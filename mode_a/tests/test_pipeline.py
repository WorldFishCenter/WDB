"""End-to-end pipeline (offline) — routing + the cite-check gate + downgrade.

Deterministic: the reasoning path runs on the ReplayReasoner (recorded proof answers); the
enumeration path needs no model. Pins the brief's success criteria:
  * a direct question is answered via enumeration (no reasoner call),
  * a multi-hop question is answered via the gated reasoning path,
  * the decisive not-connected case returns connected=false with zero claims,
  * a FAILED cite-check downgrades (never surfaces the unverified reasoned answer).
"""

from mode_a import extract
from mode_a.contract import Answer
from mode_a.fixtures import RECORDED
from mode_a.pipeline import answer_question
from mode_a.reasoner import ReplayReasoner
from wdb_contract import UnansweredCode, Verdict

Q1 = "What is Peskas connected to?"
Q2 = "How does Peskas relate to the WIO data harmonization work, and why?"
Q4 = "How does FASA's feed formulation work relate to the WIO data harmonization initiative?"


class _Boom:
    """A reasoner that must NOT be called (enumeration path needs no model)."""

    def reason(self, serialized):  # noqa: D401
        raise AssertionError("the reasoner was called on the enumeration path")


class _Fabricator:
    """A reasoner that fabricates an edge — to exercise the downgrade."""

    def reason(self, serialized):
        return {"answer": "Peskas is directly wired to a made-up node.",
                "connected": True,
                "cited_edges": [{"source": "peskas_hub", "relation": "totally_made_up",
                                 "target": "fake_node_xyz", "confidence": "EXTRACTED"}],
                "inferred_flags": []}


def test_direct_question_uses_enumeration_no_model(graph):
    ans = answer_question(Q1, _Boom(), graph)   # _Boom raises if the reasoner is touched
    assert isinstance(ans, Answer)
    assert ans.path == "enumeration"
    assert ans.answered and ans.claims and ans.associations
    # EXTRACTED claims sort before INFERRED; every citation carries a confidence tag
    confs = [c.citations[0].confidence for c in ans.claims]
    assert confs == sorted(confs, key=lambda c: 0 if c == "EXTRACTED" else 1)


def test_multihop_question_uses_reasoning_and_is_cited(graph):
    ans = answer_question(Q2, ReplayReasoner(RECORDED), graph)
    assert ans.path == "reasoning"
    assert ans.verdict is Verdict.GROUNDED
    assert ans.answered and len(ans.claims) == 1
    assert ans.claims[0].citations  # the gated reasoned claim ships real-edge citations


def test_not_connected_case_returns_verified_negative(graph):
    ans = answer_question(Q4, ReplayReasoner(RECORDED), graph)
    assert ans.verdict is Verdict.VERIFIED_NEGATIVE
    assert ans.claims == []
    assert ans.answered                      # a verified "no" is a correct answer
    assert ans.unanswered[0].code is UnansweredCode.NOT_CONNECTED
    assert "no connection" in ans.unanswered[0].text.lower()


def test_failed_cite_check_downgrades_and_never_surfaces_fabrication(graph):
    ans = answer_question(Q2, _Fabricator(), graph)
    assert "downgraded" in ans.path          # not the raw reasoned answer
    # the fabricated edge is nowhere in what surfaced
    for c in ans.claims:
        for cit in c.citations:
            assert "fake_node_xyz" not in cit.locator
            assert "totally_made_up" not in cit.locator


def test_unresolved_question_is_not_available(graph):
    ans = answer_question("How does Atlantis relate to Narnia?", ReplayReasoner(RECORDED), graph)
    assert not ans.answered
    assert ans.unanswered
