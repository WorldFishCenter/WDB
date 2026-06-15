"""Router-specific recorded fixtures for the deterministic suite.

The modes' own fixtures (``mode_b.fixtures``, ``mode_c.fixtures``) key recorded
results by exact question, so a *blended* question — one the router fans out to
several modes — needs its own recorded entries in each mode it hits. These reuse
the proofs' real data (the Peskas validation passage; the Q4 Kwale catch-per-trip
resolution) keyed under the blended question.

Also here: the synthetic below-floor passages that pin the **reranker-logit-floor
arm** deterministically — a Norway off-topic question whose top passage carries a
*negative cross-encoder logit* (``rerank_score < RERANK_FLOOR``). The mode_b proof
fixture's Norway case retrieves **nothing** (the empty arm); this one exercises the
distinct *score* arm — the arm Phase 2 left unproven — with no model or network.
The live counterpart (real reranker downloads + runs) is the mandatory end-to-end
check.
"""

from __future__ import annotations

from mode_b.fixtures.recorded import (
    PESKAS_SOFTWAREX,
    RECORDED_PASSAGES,
    RECORDED_SYNTHESIS,
    _PESKAS_VALIDATION_PASSAGE,
)
from mode_b.retrieve import Passage
from mode_c.fixtures.resolutions import KENYA, Q4
from mode_c.fixtures.resolutions import RECORDED as C_RECORDED
from mode_c.resolution import Resolution

# --- a 3-mode blended question -------------------------------------------------
# Routes to A ("which datasets" → entity enumeration), B ("how does … validate" →
# synthesis) and C ("average total catch per trip" → structured query). Mode A
# reads the real graph (no fixture needed); B and C get recorded entries below.
BLENDED = (
    "Which datasets feed Peskas, how does Peskas validate catch survey data, "
    "and what is the average total catch per trip in Kwale?"
)

# Mode-B recorded retrieval + synthesis for the blended question (reuses the
# proof's real Peskas validation passage from the SoftwareX PDF, p.2).
ROUTER_PASSAGES = {
    BLENDED: [
        Passage(
            text=_PESKAS_VALIDATION_PASSAGE,
            source_file=PESKAS_SOFTWAREX,
            location="page 2",
            initiative="peskas",
            cos_score=68.2,
            rerank_score=None,
        ),
    ],
}
ROUTER_SYNTHESIS = {
    BLENDED: (
        "Peskas validates catch survey data through an automated pipeline: after "
        "pre-processing, a Validation stage performs outlier detection and error "
        "identification with an email alert system for near-real-time data "
        "quality [1]."
    ),
}

# A grouped Mode-C question that produces a FIGURE (the proof's by-county ranking,
# Lamu 71.98 → Kilifi 22.93) — so the suite exercises the contract's ``figures``
# payload, not just scalar claims. Routes to C alone ("average" + "by county").
GROUPED = "Average total catch per trip by county in Kenya?"
GROUPED_RESOLUTION = Resolution(
    table=KENYA, aggregation="AVG", pinned_by="Kenya",
    metric_column="tot_catch_kg", grain_key="trip_id", group_by="gaul_1_name",
    metric_label="avg_total_catch_kg_per_trip",
)

# Mode-C recorded resolutions for the harness questions (the blended one reuses the
# proof's Q4: average tot_catch_kg per trip in Kwale, at trip grain).
ROUTER_RESOLUTIONS = {
    BLENDED: C_RECORDED[Q4],
    GROUPED: GROUPED_RESOLUTION,
}

# Merged dicts the deterministic replay backend uses: mode fixtures ∪ router ones.
ALL_PASSAGES = {**RECORDED_PASSAGES, **ROUTER_PASSAGES}
ALL_SYNTHESIS = {**RECORDED_SYNTHESIS, **ROUTER_SYNTHESIS}
ALL_RESOLUTIONS = {**C_RECORDED, **ROUTER_RESOLUTIONS}


# --- the reranker-logit-floor arm, deterministic -------------------------------
# An off-topic question whose retrieval, *after reranking*, scores below the floor
# (RERANK_FLOOR = 0.0). The cross-encoder logit is negative → "not relevant" → the
# gate must refuse on the SCORE arm (not the empty arm). This is the arm Phase 2
# could not prove because the reranker was uncached.
Q_OFFTOPIC = "What is the impact of salmon cage farming on fjord water quality in Norway?"

OFFTOPIC_BELOW_FLOOR = {
    Q_OFFTOPIC: [
        # a real-ish Timor-Leste nutrition passage the bi-encoder might surface,
        # but the cross-encoder scores as irrelevant to a Norway salmon question
        Passage(
            text="Fish is a critical source of micronutrients in Timor-Leste, "
                 "where household consumption surveys track dietary diversity.",
            source_file="fasa/timor_leste_nutrition_context.md",
            location="page 1",
            initiative="fasa",
            cos_score=59.0,           # the moderate cosine the proof observed live
            rerank_score=-7.4,        # cross-encoder logit < 0 → not relevant
        ),
    ],
}
