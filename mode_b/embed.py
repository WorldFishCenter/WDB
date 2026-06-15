"""The single embedder — the query-model lock (carry-over #3) lives here.

Chroma's footgun, hit live in the proof (proof/FINDINGS.md surprise #2): calling
``collection.query(query_texts=...)`` silently embeds the query with Chroma's
*default* model (``all-MiniLM-L6-v2``), not the multilingual model the index was
built with — degrading retrieval invisibly. The fix is to embed BOTH passages
(at build) and queries (at search) with the SAME model and pass precomputed
vectors (``embeddings=`` / ``query_embeddings=``), never ``query_texts=``.

This module is the one place that loads that model, so passage- and query-side
embeddings cannot drift. ``index.py`` stamps :data:`EMBED_MODEL` into the Chroma
collection metadata, and :func:`verify_collection_model` makes a mismatch a
*raised error* at query time — a checked invariant, not a convention. The proof
flagged this as a precondition for the refuse-when-thin gate (§7): the gate's
floor is meaningless if scores are depressed by a silent model mismatch, so the
lock is enforced before the gate is trusted.
"""

from __future__ import annotations

from .model import EMBED_MODEL


class EmbedModelMismatch(RuntimeError):
    """A collection was built with a different embedder than the query side."""


class Embedder:
    """Lazily-loaded ``SentenceTransformer`` wrapper — one model, one source.

    ``name`` is the locked model id; ``encode`` returns plain Python lists so the
    same vectors feed ``embeddings=`` at build and ``query_embeddings=`` at query.
    """

    def __init__(self, name: str = EMBED_MODEL):
        self.name = name
        self._model = None

    def _load(self):
        if self._model is None:
            from sentence_transformers import SentenceTransformer

            self._model = SentenceTransformer(self.name)
        return self._model

    def encode(self, texts: list[str]) -> list[list[float]]:
        return self._load().encode(texts, show_progress_bar=False).tolist()


def collection_metadata(name: str = EMBED_MODEL) -> dict:
    """Metadata stamped onto the Chroma collection at build time."""
    return {"hnsw:space": "cosine", "embed_model": name}


def verify_collection_model(metadata: dict | None, expected: str = EMBED_MODEL) -> None:
    """Raise unless the collection records the embedder we are about to query with.

    A pure check (no model load) — provable by a deterministic test. Guards the
    query-model lock: refuse to query an index built with a different embedder
    rather than silently returning degraded scores.
    """
    recorded = (metadata or {}).get("embed_model")
    if recorded is None:
        raise EmbedModelMismatch(
            "collection has no recorded embed_model — rebuild with mode_b.index so "
            "the query-model lock (carry-over #3) can be verified"
        )
    if recorded != expected:
        raise EmbedModelMismatch(
            f"index was built with {recorded!r} but queries use {expected!r}; "
            "embed both sides with the same model (query_embeddings=, not query_texts=)"
        )
