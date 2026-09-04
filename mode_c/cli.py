"""A small CLI for testing Mode C:  python -m mode_c "Average CPUE in Kwale?"

By default it uses the offline ReplayResolver (the proof's recorded resolutions),
so it answers the proof's questions with real DuckDB computation and no network.
Pass ``--live`` to route through the pinned Opus 4.8 resolver (needs the
``anthropic`` SDK + ANTHROPIC_API_KEY). ``--list`` prints the replayable set.
"""

from __future__ import annotations

import argparse
import json
import sys

from .catalog import load_catalog
from .contract import Answer
from .fixtures import RECORDED
from .model import RESOLVER_MODEL
from .pipeline import answer_question
from wdb_contract import claim_lines, figure_lines, unanswered_lines

from .resolver import LiveResolver, ReplayResolver


def _render(answer: Answer) -> str:
    out: list[str] = []
    for claim in answer.claims:
        out.extend(claim_lines(claim))
    for fig in answer.figures:
        out.extend(figure_lines(fig))
    if answer.unanswered:
        out.extend(unanswered_lines(answer.unanswered))
    return "\n".join(out) if out else "(empty answer)"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="mode_c", description="Mode C — structured query over WDB CSVs")
    parser.add_argument("question", nargs="?", help="the quantitative question to answer")
    parser.add_argument("--live", action="store_true",
                        help=f"use the live {RESOLVER_MODEL} resolver (needs anthropic + API key)")
    parser.add_argument("--list", action="store_true", help="list the replayable proof questions")
    args = parser.parse_args(argv)

    catalog = load_catalog()

    if args.list:
        for q in RECORDED:
            print(q)
        return 0
    if not args.question:
        parser.error("a question is required (or use --list)")

    if args.live:
        resolver = LiveResolver(catalog)
    else:
        resolver = ReplayResolver(RECORDED)

    answer = answer_question(args.question, resolver, catalog)
    print(_render(answer))
    return 0 if answer.answered else 1


if __name__ == "__main__":
    sys.exit(main())
