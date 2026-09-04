"""The reranker is an adapter, and which one is in force is recorded, not inferred.

The bug this pins: ``LiveRetriever`` built its reranker inside ``__init__`` behind a bare
``except Exception`` that returned ``None``. A missing model silently moved Mode B's refusal
floor from the principled rerank logit (``0.0``) to the uncalibrated cosine percentage
(``25.0``) — the arm ``mode_b/gate.py`` documents as not reliably refusing an off-topic
question. Nothing recorded that the swap had happened.
"""

import pytest

from mode_b.embed import EMBED_MODEL
from mode_b.gate import COSINE_FLOOR_PCT, RERANK_FLOOR, refuse_when_thin
from mode_b.rerank import CrossEncoderReranker, NullReranker, load_reranker
from mode_b.retrieve import LiveRetriever, Passage


def _p(text="a passage", cos=59.0, rerank=None, src="peskas/doc.pdf"):
    return Passage(text=text, source_file=src, location="page 1", initiative="peskas",
                   cos_score=cos, rerank_score=rerank)


class _FakeEncoder:
    """Stands in for the cross-encoder: scores by position so ordering is checkable."""

    def __init__(self, scores):
        self.scores = scores
        self.calls = []

    def predict(self, pairs):
        self.calls.append(pairs)
        return self.scores[: len(pairs)]


class _FakeEmbedder:
    model_name = EMBED_MODEL

    def encode(self, texts):
        return [[0.0, 0.0, 0.0] for _ in texts]


class _Collection:
    metadata = {"embed_model": EMBED_MODEL}

    def __init__(self, docs):
        self.docs = docs

    def count(self):
        return len(self.docs)

    def query(self, **kw):
        n = len(self.docs)
        return {
            "documents": [[d for d in self.docs]],
            "metadatas": [[{"source_file": f"peskas/d{i}.pdf", "location": "page 1",
                            "initiative": "peskas"} for i in range(n)]],
            "distances": [[0.4 for _ in range(n)]],
        }


# --- three adapters at one seam -------------------------------------------- #

def test_the_seam_takes_an_injected_adapter():
    """A reranker can be substituted without editing the retriever — that is the seam."""
    enc = _FakeEncoder([0.9, 5.0])
    r = LiveRetriever(_Collection(["one", "two"]), embedder=_FakeEmbedder(),
                      reranker=CrossEncoderReranker(encoder=enc))
    out = r.retrieve("q", k=2)

    assert r.ranking_kind == "rerank"
    assert [p.rerank_score for p in out] == [5.0, 0.9]     # re-ordered by logit, best first
    assert enc.calls, "the injected encoder was actually used"


def test_the_null_adapter_is_an_explicit_choice_not_a_fallback():
    r = LiveRetriever(_Collection(["one"]), embedder=_FakeEmbedder(), reranker=NullReranker())
    out = r.retrieve("q", k=1)

    assert r.ranking_kind == "cosine"
    assert out[0].rerank_score is None                     # cosine ordering, untouched


def test_use_reranker_false_still_selects_the_null_adapter():
    """The old boolean keeps working; it now resolves to a named adapter."""
    r = LiveRetriever(_Collection(["one"]), embedder=_FakeEmbedder(), use_reranker=False)
    assert isinstance(r.reranker, NullReranker)
    assert r.ranking_kind == "cosine"


# --- a failure to load is loud, or a recorded decision --------------------- #

def test_a_reranker_that_cannot_load_raises_by_default():
    """Production must not silently continue on the weaker floor."""
    with pytest.raises(Exception):
        load_reranker(model_name="definitely/not-a-real-model-name-xyz")


def test_degrading_is_possible_but_warns_and_is_recorded():
    with pytest.warns(RuntimeWarning, match="cosine"):
        rr = load_reranker(strict=False, model_name="definitely/not-a-real-model-name-xyz")
    assert isinstance(rr, NullReranker)
    assert rr.kind == "cosine"          # the decision is visible to the gate and to /health


# --- and the floor follows the declared adapter ---------------------------- #

def test_the_floor_the_gate_judges_follows_the_adapter():
    """The whole reason the seam matters: `kind` selects the floor."""
    # a 59% cosine passage — the observed off-topic score — passes the cosine arm ...
    assert refuse_when_thin("q", [_p(cos=59.0)]).ok
    # ... but the same passage scored by a cross-encoder below the logit floor is refused
    refused = refuse_when_thin("q", [_p(cos=59.0, rerank=RERANK_FLOOR - 1.0)])
    assert not refused.ok
    assert "rerank" in refused.reason
    assert COSINE_FLOOR_PCT < 59.0      # documents why the cosine arm let it through
