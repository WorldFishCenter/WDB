"""Cold-fabrication-rate measurement — the Phase-4 mandatory opening step, reproducible.

Runs the LIVE reasoner (pinned ``claude-opus-4-8``, ``model.py``) COLD — each call sees
ONLY one serialized subgraph, with no prior exposure to the graph — over the proof's 5
questions plus 5 more relational pairs, then judges each answer with the SAME mechanical
cite-check the pipeline gates on (``citecheck.py``). It reports how often the cold model
ASSERTS an edge the cite-check then REJECTS (C1 fabrication) or violates the not-connected
rule (C4). A low rate → the guard rarely fires → the reasoning path is high-utility.

This is the measurement, NOT the pipeline: it calls the reasoner directly on each subgraph
so the rate is over the model's raw output, before any downgrade. Needs ``ANTHROPIC_API_KEY``
(e.g. ``export $(grep -v '^#' .env | xargs)`` from the repo root, then run
``python -m mode_a.cold_rate``).

The recorded result lives in ``MODEL.md``; re-run to refresh it on a model-pin change.
"""

from __future__ import annotations

import os
import sys

from . import extract
from .citecheck import cite_check, triple
from .reasoner import LiveReasoner

# (id, question, extraction thunk) — the proof's 5 + 5 more relational pairs.
_G = None


def _cases(g):
    return [
        ("Q1", "What is Peskas connected to?", lambda: extract.neighborhood(g, "Peskas")),
        ("Q2", "How does Peskas relate to the WIO data harmonization work, and why?",
         lambda: extract.relate(g, "Peskas", "WIO data harmonization")),
        ("Q3", "Which initiatives share methods or data with Peskas, and how?",
         lambda: extract.bridges(g, "Peskas")),
        ("Q4", "How does FASA's feed formulation work relate to the WIO data harmonization initiative?",
         lambda: extract.relate(g, "FASA", "WIO data harmonization")),
        ("Q5", "Is the WIO data harmonization initiative related to the Digital Transformation Accelerator?",
         lambda: extract.relate(g, "WIO data harmonization", "Digital Transformation Accelerator")),
        ("Q6", "How does Peskas relate to FASA?", lambda: extract.relate(g, "Peskas", "FASA")),
        ("Q7", "How does Peskas relate to the Digital Transformation Accelerator?",
         lambda: extract.relate(g, "Peskas", "Digital Transformation Accelerator")),
        ("Q8", "How does the Digital Transformation Accelerator relate to FASA?",
         lambda: extract.relate(g, "Digital Transformation Accelerator", "FASA")),
        ("Q9", "Which initiatives share methods or data with the WIO data harmonization initiative, and how?",
         lambda: extract.bridges(g, "WIO data harmonization")),
        ("Q10", "Which initiatives share methods or data with FASA, and how?",
         lambda: extract.bridges(g, "FASA")),
    ]


def main() -> int:
    if not os.environ.get("ANTHROPIC_API_KEY"):
        print("ERROR: ANTHROPIC_API_KEY not set — export it (e.g. from the repo .env) and retry.")
        return 2

    g = extract.get_graph()
    reasoner = LiveReasoner()
    print(f"reasoner model = {reasoner.model} (max_tokens={reasoner.max_tokens})\n" + "=" * 92)

    verdicts = []
    for qid, question, build in _cases(g):
        sub = build()
        sub.question = question
        try:
            ans = reasoner.reason(sub.serialize())
        except Exception as exc:  # noqa: BLE001
            print(f"{qid:4} API ERROR {type(exc).__name__}: {exc}")
            continue
        v = cite_check(sub.edges, sub.disconnected, ans)
        verdicts.append(v)
        checks = {k: ("P" if ok else "F") for k, ok in v.checks.items()}
        fab = "FABRICATED" if v.fabricated else "clean"
        print(f"{qid:4} edges={len(sub.edges):2} disc={str(sub.disconnected):5} | "
              f"connected={str(v.connected_claim):5} cited={v.n_cited:2} {checks} "
              f"honest={v.honest} -> {fab}")
        if v.fabricated:
            print(f"      !! cited-but-absent: {[triple(e) for e in v.fabricated]}")

    n = len(verdicts)
    n_fab = sum(1 for v in verdicts if v.fabricated)
    n_dishonest = sum(1 for v in verdicts if not v.honest)
    print("=" * 92)
    print(f"questions judged                : {n}/{len(_cases(g))}")
    print(f"cite-check REJECTED (any C1–C4) : {n_dishonest}/{n}")
    print(f"  of which edge fabrication (C1): {n_fab}/{n}")
    if n:
        print(f"cold-fabrication-attempt rate   : {n_fab}/{n} = {n_fab / n:.0%}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
