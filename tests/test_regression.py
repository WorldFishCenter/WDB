"""The 9-question regression suite — the proof's findings as a passing test.

Each question must produce the correct resolution+answer OR the correct refusal/
disambiguation: 9/9, 0 fabrications, 0 over-refusals (proof_c/RESOLVER_FINDINGS.md
headline). The resolver is the offline ReplayResolver (the proof's recorded
resolutions); the gate, executor (real DuckDB), and answer contract run for real.
"""

import pytest

from mode_c import answer_question, load_catalog, ReplayResolver
from mode_c.fixtures import PROOF_QUESTIONS, RECORDED
from mode_c.fixtures.resolutions import Q1, Q2, Q3A, Q3B, Q4, Q4B, Q5A, Q5B, Q6
from wdb_contract import UnansweredCode


@pytest.fixture(scope="module")
def cat():
    return load_catalog()


@pytest.fixture(scope="module")
def resolver():
    return ReplayResolver(RECORDED)


def _num(answer):
    """The single computed value from an answered claim's citation."""
    row = answer.claims[0].citations[0].result[0]
    return {k: v for k, v in row.items() if k != "n"}.popitem()[1]


# --- the answerable seven: correct number, every one shipping its SQL ------- #

@pytest.mark.parametrize(
    "q, expected",
    [
        (Q1, 13.86),    # clean hit (row grain)
        (Q2, 1.64),     # derived CPUE (flagged), trip grain
        (Q3B, 7.62),    # disambiguated by region, trip grain
        (Q4, 31.88),    # grain trap (implicit) -> trip grain, NOT 28.99
        (Q4B, 441.18),  # grain trap (explicit) -> trip grain
        (Q6, 62.62),    # EAV / mislabeled column
    ],
)
def test_answered_questions(cat, resolver, q, expected):
    answer = answer_question(q, resolver, cat)
    assert answer.answered, answer.unanswered
    claim = answer.claims[0]
    assert claim.mode == "C"
    # every number ships its SQL + rows (answer contract §6 rule 3)
    cit = claim.citations[0]
    assert cit.sql and cit.result
    assert cit.source_file == RECORDED[q].table
    assert _num(answer) == pytest.approx(expected, abs=0.005)


# --- the two genuine refusals ---------------------------------------------- #

@pytest.mark.parametrize("q", [Q5A, Q5B])
def test_genuine_refusals(cat, resolver, q):
    answer = answer_question(q, resolver, cat)
    assert not answer.answered
    assert answer.unanswered
    assert answer.unanswered[0].code is not UnansweredCode.NEEDS_DISAMBIGUATION


# --- the one genuine ambiguity (ask, don't guess) -------------------------- #

def test_disambiguation_not_a_guess(cat, resolver):
    answer = answer_question(Q3A, resolver, cat)
    assert not answer.answered
    # the candidates ride on the unanswered entry now, so the router carries them through
    ask = answer.unanswered[0]
    assert ask.code is UnansweredCode.NEEDS_DISAMBIGUATION
    assert len(ask.candidates) == 3  # the three sister tables


def test_no_over_refusal_and_no_fabrication(cat, resolver):
    # exactly 6 answered, 3 declined (2 refuse + 1 disambiguation): 9/9 as the proof earned
    answered = [q for q in PROOF_QUESTIONS if answer_question(q, resolver, cat).answered]
    assert len(answered) == 6
    assert len(PROOF_QUESTIONS) == 9
