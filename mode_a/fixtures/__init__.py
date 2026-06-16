"""Recorded reasoned answers for the offline ReplayReasoner + the regression suite.

``RECORDED`` maps each proof question to the structured answer the proof's Opus 4.8
produced (``reasoned.json``, copied from ``proof_a/candidate_answers.json``). Replaying
them lets the route/extract/cite-check/contract pipeline be tested deterministically with
no network — the same posture as Mode C's recorded resolutions.
"""

import json
from pathlib import Path

RECORDED: dict[str, dict] = json.loads((Path(__file__).resolve().parent / "reasoned.json").read_text())

__all__ = ["RECORDED"]
