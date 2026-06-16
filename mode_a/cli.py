"""A small CLI for testing Mode A:  python -m mode_a "How does Peskas relate to WIO data harmonization?"

By default it uses the offline ReplayReasoner (the proof's recorded answers), so it answers
the proof's reasoning questions and ALL direct-enumeration questions (the cheap path needs no
model) with real graph extraction + the mechanical cite-check, no network. Pass ``--live`` to
route the reasoning path through the pinned Opus 4.8 reasoner (needs the ``anthropic`` SDK +
ANTHROPIC_API_KEY). ``--list`` prints the replayable reasoning questions.
"""

from __future__ import annotations

import argparse
import sys

from . import extract
from .contract import Answer
from .fixtures import RECORDED
from .model import REASONER_MODEL
from .pipeline import answer_question
from .reasoner import LiveReasoner, ReplayReasoner


def _render(answer: Answer) -> str:
    out: list[str] = []
    out.append(f"[path: {answer.path or '—'}]")
    for claim in answer.claims:
        out.append(f"CLAIM [{claim.mode}]: {claim.text}")
        for k, cit in enumerate(claim.citations, 1):
            note = f"  ({cit.note})" if cit.note else ""
            out.append(f"  [{k}] {cit.locator}  [{cit.confidence}]")
            out.append(f"      source : {cit.source_file}{note}")
    if answer.associations:
        out.append(f"\nASSOCIATIONS ({len(answer.associations)} edge(s) in the subgraph):")
        for e in answer.associations[:8]:
            out.append(f"  {e.get('source')}  --{e.get('relation', '?')}[{e.get('confidence')}]-->  {e.get('target')}")
    if answer.connected is False:
        out.append("\nCONNECTED: false (the graph records no connection)")
    for u in answer.unanswered:
        out.append(f"NOT AVAILABLE: {u}")
    return "\n".join(out) if out else "(empty answer)"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="mode_a", description="Mode A — graph relationships / enumeration")
    parser.add_argument("question", nargs="?", help="the relational / enumeration question to answer")
    parser.add_argument("--live", action="store_true",
                        help=f"route the reasoning path through the live {REASONER_MODEL} reasoner")
    parser.add_argument("--list", action="store_true", help="list the replayable reasoning questions")
    args = parser.parse_args(argv)

    if args.list:
        for q in RECORDED:
            print(q)
        return 0
    if not args.question:
        parser.error("a question is required (or use --list)")

    reasoner = LiveReasoner() if args.live else ReplayReasoner(RECORDED)
    g = extract.get_graph()
    answer = answer_question(args.question, reasoner, g)
    print(_render(answer))
    return 0 if answer.answered else 1


if __name__ == "__main__":
    sys.exit(main())
