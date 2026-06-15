"""Correction #5 — the refuse-when-thin gate (Mode B's honesty mechanism).

The gate's LOGIC is what's pinned here, not the provisional floor value: a thin
or empty retrieval, or one that drifts off the named initiative, must refuse;
adequate retrieval must pass. Tests are written relative to the imported floor
constants so they stay valid if the provisional placeholders are recalibrated.
"""

from mode_b.gate import COSINE_FLOOR_PCT, RERANK_FLOOR, covers_question, refuse_when_thin
from mode_b.retrieve import Passage


def _cos(score, initiative="peskas"):
    return Passage("text", "peskas/x.pdf", "page 1", initiative, cos_score=score)


def _rer(score, initiative="peskas"):
    return Passage("text", "peskas/x.pdf", "page 1", initiative, cos_score=50.0, rerank_score=score)


def test_empty_retrieval_refuses():
    assert not refuse_when_thin("anything", []).ok


def test_cosine_floor_refuses_below_passes_above():
    assert not refuse_when_thin("q", [_cos(COSINE_FLOOR_PCT - 5)]).ok      # thin -> refuse
    assert refuse_when_thin("q", [_cos(COSINE_FLOOR_PCT + 5)]).ok          # adequate -> pass


def test_rerank_floor_refuses_below_passes_above():
    assert not refuse_when_thin("q", [_rer(RERANK_FLOOR - 1.0)]).ok        # thin -> refuse
    assert refuse_when_thin("q", [_rer(RERANK_FLOOR + 1.0)]).ok            # adequate -> pass


def test_coverage_arm_refuses_off_topic_drift():
    known = {"peskas", "fasa"}
    # question names a KNOWN initiative (fasa) but every passage is from peskas
    strong_but_wrong = [_cos(COSINE_FLOOR_PCT + 30, initiative="peskas")]
    assert not covers_question("fasa feed formulation question", strong_but_wrong, known)
    v = refuse_when_thin("fasa feed formulation question", strong_but_wrong, known_initiatives=known)
    assert not v.ok


def test_coverage_passes_when_named_initiative_is_present():
    known = {"peskas", "fasa"}
    ps = [_cos(COSINE_FLOOR_PCT + 30, initiative="peskas")]
    assert covers_question("how does peskas validate data", ps, known)
    assert refuse_when_thin("how does peskas validate data", ps, known_initiatives=known).ok


def test_unknown_initiative_left_to_the_floor_not_coverage():
    known = {"peskas", "fasa"}
    # 'norway' isn't a corpus initiative -> coverage doesn't fire; the floor does
    assert covers_question("salmon farming in norway", [_cos(80, "peskas")], known)
