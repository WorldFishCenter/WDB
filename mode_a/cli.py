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

from wdb_contract import Verdict, association_lines, claim_lines, unanswered_lines

from . import extract
from .contract import Answer
from .fixtures import RECORDED
from .model import REASONER_MODEL
from .pipeline import answer_question
from .reasoner import LiveReasoner, ReplayReasoner


def _render(answer: Answer) -> str:
    out: list[str] = [f"[path: {answer.path or '—'}]"]
    for claim in answer.claims:
        out.extend(claim_lines(claim))
    if answer.associations:
        out.append("")
        out.extend(association_lines(answer.associations))
    if answer.verdict is Verdict.VERIFIED_NEGATIVE:
        # a verified negative is a correct answer, not a coverage failure — say so plainly
        out.append("\nVERDICT: verified negative (the graph records no connection)")
    if answer.unanswered:
        out.append("")
        out.extend(unanswered_lines(answer.unanswered))
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
