"""The §6 contract's own guarantees — the ones six separate declarations used to lose.

Each test here pins a property that was broken, unenforceable, or silently droppable while the
contract was declared once per package.
"""

import pytest

from wdb_contract import (
    Answer,
    CitationA,
    CitationC,
    Claim,
    ClaimWithoutCitation,
    Figure,
    Unanswered,
    UnansweredCode,
    Verdict,
    merge,
)

EDGE = CitationA(source_file="peskas/peskas_about.md", note="", locator="a --uses--> b",
                 confidence="EXTRACTED")


def _claim(mode="A", text="x"):
    return Claim(text=text, citations=(EDGE,), mode=mode)


# --- §6 rule 1: no claim without a citation -------------------------------- #

def test_a_claim_cannot_be_built_without_a_citation():
    """Rule 1 is enforced by the type, so no caller has to remember it.

    ``mode_a.contract.from_reasoning`` could previously emit one: the cite-check's C1 passes
    vacuously when the reasoner cited nothing, so un-sourced prose could reach the UI.
    """
    with pytest.raises(ClaimWithoutCitation):
        Claim(text="un-sourced prose", citations=(), mode="A")


# --- the verdict: a verified negative is an ANSWER -------------------------- #

def test_verified_negative_is_answered():
    a = Answer(negative=True, unanswered=[
        Unanswered("q", "A", UnansweredCode.NOT_CONNECTED, "the graph records no connection"),
    ])
    assert a.verdict is Verdict.VERIFIED_NEGATIVE
    assert a.answered                      # "we checked, and the answer is no" is correct


def test_ungrounded_is_not_answered():
    a = Answer(unanswered=[
        Unanswered("q", "B", UnansweredCode.THIN_RETRIEVAL, "retrieval too thin"),
    ])
    assert a.verdict is Verdict.UNGROUNDED
    assert not a.answered


def test_claims_outrank_a_negative():
    a = Answer(claims=[_claim()], negative=True)
    assert a.verdict is Verdict.GROUNDED


def test_figures_alone_ground_an_answer():
    a = Answer(figures=[Figure(spec={"kind": "bar"}, query="SELECT 1", result=[{"n": 1}])])
    assert a.verdict is Verdict.GROUNDED
    assert a.answered


# --- the merge: the router seam where fields used to die -------------------- #

def test_merge_carries_a_verified_negative_across_the_seam():
    """The regression for the bug this module exists to fix.

    Mode A determined "the graph records no connection" — a correct answer. The router's merge
    read only claims/associations/figures/unanswered, recomputed ``answered`` from the empty
    lists, and the UI rendered "the knowledge base doesn't cover this".
    """
    merged = Answer()
    fragment = Answer(negative=True, unanswered=[
        Unanswered("q", "A", UnansweredCode.NOT_CONNECTED, "no direct edge, no ≤2-hop path"),
    ])
    merge(merged, fragment)

    assert merged.verdict is Verdict.VERIFIED_NEGATIVE
    assert merged.answered
    assert merged.unanswered[0].code is UnansweredCode.NOT_CONNECTED


def test_merge_carries_disambiguation_candidates():
    """Mode C's typed candidate list used to survive only as prose inside an ``unanswered`` string."""
    merged = Answer()
    merge(merged, Answer(unanswered=[Unanswered(
        "q", "C", UnansweredCode.NEEDS_DISAMBIGUATION, "several tables match",
        candidates=("peskas/kenya.csv", "peskas/zanzibar.csv", "peskas/mozambique.csv"),
    )]))

    ask = merged.unanswered[0]
    assert ask.code is UnansweredCode.NEEDS_DISAMBIGUATION
    assert len(ask.candidates) == 3


def test_merge_keeps_every_mode_fragment():
    merged = Answer()
    merge(merged, Answer(claims=[_claim("A")], associations=[{"source": "a", "relation": "r",
                                                             "target": "b"}]))
    merge(merged, Answer(claims=[_claim("B")]))
    merge(merged, Answer(claims=[_claim("C")],
                         figures=[Figure(spec={}, query="SELECT 1", result=[])]))

    assert [c.mode for c in merged.claims] == ["A", "B", "C"]
    assert len(merged.figures) == 1
    assert merged.verdict is Verdict.GROUNDED


def test_merge_dedups_associations_by_triple():
    e = {"source": "a", "relation": "uses", "target": "b", "confidence": "EXTRACTED"}
    merged = Answer()
    merge(merged, Answer(associations=[e]))
    merge(merged, Answer(associations=[dict(e), {"source": "a", "relation": "cites",
                                                 "target": "b"}]))
    assert len(merged.associations) == 2


# --- unanswered: a code to assert on, prose to display ---------------------- #

def test_unanswered_renders_the_prose_it_always_did():
    u = Unanswered("What is X?", "B", UnansweredCode.THIN_RETRIEVAL, "not available: too thin")
    assert u.text == "What is X? — not available: too thin"
    assert str(u) == u.text


def test_the_code_is_stable_when_the_prose_changes():
    """The point of the code: downstream packages assert on the arm, not the wording."""
    a = Unanswered("q", "B", UnansweredCode.THIN_RETRIEVAL, "top passage score 0.1 below floor")
    b = Unanswered("q", "B", UnansweredCode.THIN_RETRIEVAL, "completely reworded message")
    assert a.code is b.code


def test_mode_c_citation_carries_its_computation():
    """§6 rule 3: the Mode-C citation IS the SQL plus its rows."""
    c = CitationC(source_file="peskas/kenya.csv", note="kenya_dict.md#Grain",
                  sql="SELECT AVG(x) FROM t", result=[{"avg": 31.88}])
    claim = Claim(text="Average is 31.88", citations=(c,), mode="C")
    assert claim.citations[0].sql
    assert claim.citations[0].result == [{"avg": 31.88}]
