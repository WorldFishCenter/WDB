"""CLI for the WDB router:  python -m wdb_router "…one question…"

    python -m wdb_router "What projects operate in Kenya?"          # → Mode A
    python -m wdb_router "Average total catch per trip in Kwale?"   # → Mode C
    python -m wdb_router "How does Peskas validate catch data?"     # → Mode B
    python -m wdb_router --live "…off-topic question…"              # real Chroma + reranker

Default is the deterministic Replay backends (no model, no network) — it answers the modes'
proof questions and the blended demo. ``--live`` swaps in Mode A's Opus 4.8 reasoner, Mode
B's real Chroma index + cross-encoder reranker, and Mode C's Opus 4.8 resolver; the
LLM-dependent arms additionally need ``ANTHROPIC_API_KEY`` (the off-topic *refusal* arm does
not — the gate refuses before any model call). ``--classify-only`` prints the routing
decision without dispatching.
"""

from __future__ import annotations

import argparse
import sys

from wdb_contract import (
    Verdict, association_lines, claim_lines, figure_lines, unanswered_lines,
)

from .backends import live_backends, replay_backends
from .contract import RouterAnswer
from .dispatch import answer
from .routing import route


def render(ans: RouterAnswer) -> str:
    out: list[str] = [f"Q: {ans.question}"]
    routed = ", ".join(f"{r.mode} ({r.reason})" for r in ans.routes)
    out.append(f"ROUTED → {routed}")
    out.append(f"GROUNDED BY → {', '.join(ans.modes_grounded) or '— (nothing)'}\n")

    for i, claim in enumerate(ans.claims, 1):
        out.extend(claim_lines(claim, index=i))

    if ans.associations:
        out.append("")
        out.extend(association_lines(ans.associations, limit=12))

    for fig in ans.figures:
        out.append("")
        out.extend(figure_lines(fig))

    if ans.verdict is Verdict.VERIFIED_NEGATIVE:
        # the graph was consulted and records no connection — a correct answer, not a
        # coverage failure. Before the shared contract this verdict died at the merge.
        out.append("\nVERDICT: verified negative (checked, and the answer is no)")

    if ans.unanswered:
        out.append("")
        out.extend(unanswered_lines(ans.unanswered))

    return "\n".join(out)


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="wdb-router",
                                description="WDB router — dispatch a question across Modes A + B + C")
    p.add_argument("question", nargs="?", help="the question to route and answer")
    p.add_argument("--live", action="store_true",
                   help="use the real backends (Mode A Opus 4.8, Mode B Chroma + reranker, Mode C Opus 4.8)")
    p.add_argument("--no-rerank", action="store_true",
                   help="with --live, skip the cross-encoder reranker (fallback to cosine)")
    p.add_argument("--classify-only", action="store_true",
                   help="print the routing decision only, do not dispatch")
    args = p.parse_args(argv)

    if not args.question:
        p.error("a question is required")

    if args.classify_only:
        for r in route(args.question).routes:
            print(f"{r.mode}: {r.reason}")
        return 0

    backends = live_backends(use_reranker=not args.no_rerank) if args.live else replay_backends()
    ans = answer(args.question, backends=backends)
    print(render(ans))
    return 0 if ans.answered else 1


if __name__ == "__main__":
    sys.exit(main())
