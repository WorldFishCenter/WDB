"""Mode B's off-topic refusal — the router respects it, never coaxes a synthesis.

Two forms:

* **Deterministic** — a recorded passage whose cross-encoder logit is below the floor
  exercises the *score* arm (distinct from the empty arm) with no model.
* **Live** — the real Chroma index + cross-encoder reranker actually refuse the off-topic
  question end-to-end. Self-skips when the models aren't available, so offline CI still
  passes on the deterministic form.

The point both make: an off-topic question (Norway salmon farming) must return "not
available", never a synthesis from irrelevant passages. The reranker logit floor
(``RERANK_FLOOR = 0``) is the principled threshold — a negative logit means "not relevant" —
where a bi-encoder cosine (~59%) would not refuse.
"""

import pytest

from wdb_router import answer
from wdb_router.backends import live_backends, replay_backends
from wdb_router.fixtures import OFFTOPIC_BELOW_FLOOR, Q_OFFTOPIC


def test_offtopic_refuses_on_the_rerank_logit_floor_deterministic():
    backends = replay_backends(
        recorded_passages=OFFTOPIC_BELOW_FLOOR,
        recorded_synthesis={},
        recorded_resolutions={},
    )
    ans = answer(Q_OFFTOPIC, backends=backends)
    assert not ans.answered                       # refused, not synthesized
    assert not ans.claims
    assert ans.unanswered                          # stated (§6 r4)
    reason = " ".join(ans.unanswered).lower()
    assert "rerank" in reason and "below" in reason  # the SCORE arm fired (not empty)


@pytest.mark.live
def test_offtopic_refuses_end_to_end_with_real_reranker():
    pytest.importorskip("chromadb")
    pytest.importorskip("sentence_transformers")
    try:
        backends = live_backends(use_reranker=True)
    except Exception as e:  # index missing, model can't load, etc.
        pytest.skip(f"live backends unavailable: {e}")
    if getattr(backends.b_retriever, "reranker", None) is None:
        pytest.skip("cross-encoder reranker not loaded — falling back to cosine")

    ans = answer(Q_OFFTOPIC, backends=backends)
    assert not ans.answered                        # NOT a synthesis
    assert ans.unanswered
    assert "rerank" in " ".join(ans.unanswered).lower()
