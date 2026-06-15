"""Retrieve → (optionally) rerank passages for a question.

Vendored from civ-kb's query core, with the query-model lock made explicit
(carry-over #3): :class:`LiveRetriever` verifies the collection's recorded
embedder matches before searching, and embeds the query with the SAME
:class:`~mode_b.embed.Embedder` via ``query_embeddings=`` — never ``query_texts=``
(which would silently use Chroma's default model).

Two backends share one ``Retriever`` interface, the same Live/Replay split Mode C
uses for its resolver so the suite runs offline/deterministically:

* :class:`LiveRetriever` — real Chroma + embedder (+ optional cross-encoder
  reranker; degrades to embedding-only ranking when it cannot load).
* :class:`ReplayRetriever` — returns recorded :class:`Passage` lists keyed by
  question, so the gate → join → synthesize → contract pipeline is tested with no
  model and no network.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from .embed import Embedder, verify_collection_model
from .model import RERANK_MODEL, RERANK_TOP_K, RETRIEVAL_K


@dataclass(frozen=True)
class Passage:
    """One retrieved passage + its provenance and scores."""

    text: str
    source_file: str          # WDB-relative path — the join key (#4)
    location: str             # mechanical civ-kb location, e.g. "page 2 [part 4/4]"
    initiative: str
    cos_score: float          # cosine similarity as a percentage (0-100)
    rerank_score: float | None = None  # cross-encoder logit, if reranked

    def ranking_score(self) -> float:
        """The score the gate judges: the reranker's if present, else cosine%."""
        return self.cos_score if self.rerank_score is None else self.rerank_score

    def ranking_kind(self) -> str:
        return "cosine" if self.rerank_score is None else "rerank"


class Retriever(Protocol):
    def retrieve(self, question: str, k: int = RERANK_TOP_K) -> list[Passage]: ...


def _to_passages(res) -> list[Passage]:
    out = []
    for doc, meta, dist in zip(res["documents"][0], res["metadatas"][0], res["distances"][0]):
        out.append(Passage(
            text=doc,
            source_file=meta.get("source_file", ""),
            location=meta.get("location", ""),
            initiative=meta.get("initiative", ""),
            cos_score=round((1 - dist) * 100, 1),
        ))
    return out


class LiveRetriever:
    """Production retriever — locked-model Chroma search + optional rerank."""

    def __init__(self, collection, embedder: Embedder | None = None, use_reranker: bool = True):
        # query-model lock: refuse to query an index built with another embedder (#3)
        verify_collection_model(getattr(collection, "metadata", None))
        self.collection = collection
        self.embedder = embedder or Embedder()
        self.reranker = _load_reranker() if use_reranker else None

    def retrieve(self, question: str, k: int = RERANK_TOP_K) -> list[Passage]:
        n = min(max(RETRIEVAL_K, k * 3), self.collection.count())
        # the lock in action: SAME model, query_embeddings= (never query_texts=)
        q_vec = self.embedder.encode([question])
        res = self.collection.query(
            query_embeddings=q_vec, n_results=n,
            include=["documents", "metadatas", "distances"],
        )
        passages = _to_passages(res)
        if not passages:
            return []
        if self.reranker is not None:
            scores = self.reranker.predict([(question, p.text) for p in passages])
            passages = [
                Passage(p.text, p.source_file, p.location, p.initiative,
                        p.cos_score, float(s))
                for p, s in zip(passages, scores)
            ]
            passages.sort(key=lambda p: p.rerank_score, reverse=True)
        return passages[:k]


def _load_reranker():
    """The cross-encoder, or None (retrieval degrades to embedding-only ranking)."""
    try:
        from sentence_transformers import CrossEncoder

        return CrossEncoder(RERANK_MODEL)
    except Exception as e:  # pragma: no cover - environment dependent
        print(f"  [!] reranker unavailable ({e}) — using embedding scores only.")
        return None


class ReplayRetriever:
    """Offline retriever — returns recorded passages keyed by normalised question.

    The deterministic default the regression suite runs: the gate/join/synthesis/
    contract pipeline is exercised end-to-end with no model and no network.
    """

    def __init__(self, recorded: dict[str, list[Passage]]):
        self.recorded = {self._norm(q): ps for q, ps in recorded.items()}

    @staticmethod
    def _norm(q: str) -> str:
        return " ".join(q.lower().split())

    def retrieve(self, question: str, k: int = RERANK_TOP_K) -> list[Passage]:
        return list(self.recorded.get(self._norm(question), []))[:k]
