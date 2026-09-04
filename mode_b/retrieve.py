"""Retrieve → (optionally) rerank passages for a question.

Vendored from civ-kb's query core, with the query-model lock made explicit
(carry-over #3): :class:`LiveRetriever` verifies the collection's recorded
embedder matches before searching, and embeds the query with the SAME
:class:`~mode_b.embed.Embedder` via ``query_embeddings=`` — never ``query_texts=``
(which would silently use Chroma's default model).

Two backends share one ``Retriever`` interface, the same Live/Replay split Mode C
uses for its resolver so the suite runs offline/deterministically:

* :class:`LiveRetriever` — real Chroma + embedder + a :class:`~mode_b.rerank.Reranker`
  adapter (see that module: the reranker is passed in, not constructed here, because
  which reranker is in force decides which floor the honesty gate judges).
* :class:`ReplayRetriever` — returns recorded :class:`Passage` lists keyed by
  question, so the gate → join → synthesize → contract pipeline is tested with no
  model and no network.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from .embed import Embedder, verify_collection_model
from .model import RERANK_TOP_K, RETRIEVAL_K
from .rerank import NullReranker, Reranker, load_reranker


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
    """Production retriever — locked-model Chroma search + a declared reranker adapter.

    ``reranker`` is the seam. Pass one explicitly; omit it and ``use_reranker`` decides which
    default is built — ``True`` loads the cross-encoder (non-strict, so an environment without
    the model still runs, but warns), ``False`` selects :class:`~mode_b.rerank.NullReranker`
    deliberately. Either way ``self.reranker.kind`` records which floor the gate will judge.
    """

    def __init__(self, collection, embedder: Embedder | None = None,
                 use_reranker: bool = True, reranker: Reranker | None = None):
        # query-model lock: refuse to query an index built with another embedder (#3)
        verify_collection_model(getattr(collection, "metadata", None))
        self.collection = collection
        self.embedder = embedder or Embedder()
        if reranker is not None:
            self.reranker = reranker
        else:
            self.reranker = load_reranker(strict=False) if use_reranker else NullReranker()

    @property
    def ranking_kind(self) -> str:
        """Which score the gate judges — read this instead of sniffing for a reranker."""
        return self.reranker.kind

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
        return self.reranker.rank(question, passages)[:k]


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
