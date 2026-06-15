"""Correction #3 — the query-embedding model lock.

Two deterministic guarantees, both without loading a model:
1. the collection records its embedder, and a mismatch is a RAISED error
   (`verify_collection_model`), so an index built with another model can't be
   silently queried with the wrong one;
2. `LiveRetriever` queries with `query_embeddings=` (our locked model's vectors),
   never `query_texts=` (which would use Chroma's default model — the footgun).
"""

import pytest

from mode_b.embed import (
    EmbedModelMismatch,
    collection_metadata,
    verify_collection_model,
)
from mode_b.model import EMBED_MODEL
from mode_b.retrieve import LiveRetriever


def test_collection_metadata_stamps_the_embedder():
    md = collection_metadata()
    assert md["embed_model"] == EMBED_MODEL
    assert md["hnsw:space"] == "cosine"


def test_verify_passes_on_match_raises_on_mismatch_or_missing():
    verify_collection_model({"embed_model": EMBED_MODEL})              # ok, no raise
    with pytest.raises(EmbedModelMismatch):
        verify_collection_model({"embed_model": "all-MiniLM-L6-v2"})    # the wrong model
    with pytest.raises(EmbedModelMismatch):
        verify_collection_model({})                                    # unstamped index
    with pytest.raises(EmbedModelMismatch):
        verify_collection_model(None)


# --- prove the query path uses query_embeddings=, not query_texts= ---------- #

class _FakeEmbedder:
    name = EMBED_MODEL

    def encode(self, texts):
        return [[0.0, 1.0, 0.0] for _ in texts]   # fixed vector, no model load


class _FakeCollection:
    def __init__(self):
        self.metadata = collection_metadata()
        self.last_query_kwargs = None

    def count(self):
        return 1

    def query(self, **kwargs):
        self.last_query_kwargs = kwargs
        return {
            "documents": [["a passage about peskas validation"]],
            "metadatas": [[{"source_file": "peskas/x.pdf", "location": "page 1",
                            "initiative": "peskas"}]],
            "distances": [[0.30]],
        }


def test_live_retriever_locks_the_query_model():
    coll = _FakeCollection()
    r = LiveRetriever(coll, embedder=_FakeEmbedder(), use_reranker=False)
    passages = r.retrieve("how does peskas validate data?", k=1)

    assert "query_embeddings" in coll.last_query_kwargs       # locked vectors
    assert "query_texts" not in coll.last_query_kwargs        # NOT Chroma's default model
    assert passages and passages[0].source_file == "peskas/x.pdf"


def test_live_retriever_refuses_a_mismatched_index():
    class _WrongModelCollection(_FakeCollection):
        def __init__(self):
            super().__init__()
            self.metadata = {"embed_model": "all-MiniLM-L6-v2"}

    with pytest.raises(EmbedModelMismatch):
        LiveRetriever(_WrongModelCollection(), embedder=_FakeEmbedder(), use_reranker=False)
