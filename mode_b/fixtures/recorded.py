"""Recorded retrieval + synthesis — the proof's join case as deterministic fixtures.

``RECORDED_PASSAGES`` / ``RECORDED_SYNTHESIS`` let the ``ReplayRetriever`` and
``ReplaySynthesizer`` drive the gate → join → synthesize → contract pipeline with
no model and no network — the Mode-B analogue of Mode C's recorded resolutions.

The covered case reuses the proof's real retrieved passage (proof/FINDINGS.md Q1):
the Peskas validation passage from ``peskas_automated_analytics_softwarex_2025.pdf``
p.2, which joins at document grain to 15 Peskas nodes incl. ``peskas_validation_
engine``. The uncovered case retrieves nothing, so the refuse-when-thin gate (#5)
must decline it rather than synthesise.
"""

from __future__ import annotations

from ..retrieve import Passage

# --- questions -------------------------------------------------------------- #
Q_COVERED = "How does the platform automatically validate small-scale fishery catch survey data?"
Q_UNCOVERED = "What is the impact of salmon cage farming on fjord water quality in Norway?"

PESKAS_SOFTWAREX = "peskas/peskas_automated_analytics_softwarex_2025.pdf"

# The proof's real retrieved passage (verbatim span from p.2 of the SoftwareX PDF).
_PESKAS_VALIDATION_PASSAGE = (
    "The Peskas pipeline ingests catch survey data and processes it in stages: "
    "2. Pre-processing. 3. Validation: Outlier detection and error identification "
    "with an email alert system to ensure near-real time maintenance of data "
    "quality. 4. Analytics."
)

# --- recorded retrieval (what LiveRetriever would return) ------------------- #
RECORDED_PASSAGES: dict[str, list[Passage]] = {
    Q_COVERED: [
        Passage(
            text=_PESKAS_VALIDATION_PASSAGE,
            source_file=PESKAS_SOFTWAREX,
            location="page 2",
            initiative="peskas",
            cos_score=68.2,          # the proof's hit (cosine distance 0.318 -> 68.2%)
            rerank_score=None,        # no reranker in the offline replay
        ),
    ],
    # nothing in the corpus covers Norwegian salmon farming -> empty retrieval
    Q_UNCOVERED: [],
}

# --- recorded synthesis (what LiveSynthesizer would return) ----------------- #
RECORDED_SYNTHESIS: dict[str, str] = {
    Q_COVERED: (
        "Peskas validates small-scale fishery catch survey data through an "
        "automated pipeline: after pre-processing, a Validation stage performs "
        "outlier detection and error identification, with an email alert system "
        "that maintains near-real-time data quality [1]."
    ),
}
