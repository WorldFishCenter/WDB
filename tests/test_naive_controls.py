"""The proof's naive-control failures, turned into guards that must NOT regress.

proof_c/RESOLVER_FINDINGS.md: the only fabrications in the whole study came from
the naive control — the Kenya grain trap (28.99 instead of 31.88) and the CPUE
proxy (AVG(tot_catch_kg) relabeled as CPUE). These tests prove Mode C does not
ship either, and refuses an out-of-band route rather than guessing.
"""

import pytest

from mode_c import answer_question, load_catalog, ReplayResolver, vetted_band
from mode_c.executor import execute
from mode_c.fixtures import (
    NAIVE_CPUE_PROXY,
    NAIVE_KENYA_GRAIN_TRAP,
    OUT_OF_BAND_GILLNET,
    RECORDED,
)
from mode_c.fixtures.resolutions import Q2, Q4


@pytest.fixture(scope="module")
def cat():
    return load_catalog()


def test_kenya_grain_trap_is_refused_not_computed(cat):
    # the trap value exists (28.99 over raw rows) ...
    trap_value = execute(NAIVE_KENYA_GRAIN_TRAP, cat).rows[0]["avg_total_catch_kg"]
    assert trap_value == pytest.approx(28.99, abs=0.005)
    # ... but the gate refuses the trap resolution by construction ...
    assert not vetted_band(NAIVE_KENYA_GRAIN_TRAP, cat).ok
    # ... so the pipeline returns "not available", never 28.99 ...
    answer = answer_question(Q4, ReplayResolver({Q4: NAIVE_KENYA_GRAIN_TRAP}), cat)
    assert not answer.answered and "grain trap" in answer.unanswered[0]
    # ... while the guarded resolution computes 31.88 (trip grain).
    good = answer_question(Q4, ReplayResolver(RECORDED), cat)
    assert good.claims[0].citations[0].result[0]["avg_total_catch_kg_per_trip"] == pytest.approx(
        31.88, abs=0.005
    )


def test_cpue_is_a_flagged_derivation_not_a_relabeled_proxy(cat):
    # what we ship for CPUE: a flagged formula with a surfaced denominator
    real = answer_question(Q2, ReplayResolver(RECORDED), cat)
    text = real.claims[0].text
    assert "Derived" in text and "Assumption" in text
    assert "tot_catch_kg / NULLIF(trip_duration_hrs, 0)" in text
    assert real.claims[0].citations[0].result[0]["avg_cpue_kg_per_trip_hr"] == pytest.approx(
        1.64, abs=0.005
    )

    # the proxy (relabel a stored column as CPUE) ships NO derivation/assumption
    # flag — the observable regression the prompt guard prevents at resolve time.
    proxy = answer_question(Q2, ReplayResolver({Q2: NAIVE_CPUE_PROXY}), cat)
    proxy_text = proxy.claims[0].text if proxy.claims else ""
    assert "Derived" not in proxy_text and "Assumption" not in proxy_text


def test_out_of_band_question_is_refused(cat):
    # a single table picked on a generic shared term -> refuse, don't guess
    assert not vetted_band(OUT_OF_BAND_GILLNET, cat).ok
    answer = answer_question(
        "Average trip duration for Gill Net trips?",
        ReplayResolver({"Average trip duration for Gill Net trips?": OUT_OF_BAND_GILLNET}),
        cat,
    )
    assert not answer.answered
    assert "vetted band" in answer.unanswered[0]
