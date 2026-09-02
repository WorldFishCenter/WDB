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
import json
import sys

from .backends import live_backends, replay_backends
from .contract import RouterAnswer
from .dispatch import answer
from .routing import route


def _render_citation(mode: str, cit) -> list[str]:
    """Per-mode citation formatting — each mode's citation IS a different artifact."""
    out = [f"      source : {cit.source_file}"]
    if mode == "A":
        out.append(f"      edge   : {cit.locator}  [{cit.confidence}]")
        if cit.note:
            out.append(f"      at     : {cit.note}")
    elif mode == "B":
        if getattr(cit, "note", ""):
            out.append(f"      note   : {cit.note}")
        out.append(f"      span   : {cit.location}")
        out.append(f"      quote  : {cit.quote[:200].replace(chr(10), ' ').strip()}…")
        out.append(f"      nodes  : {', '.join(cit.nodes) or '—'}")
    elif mode == "C":
        out.append(f"      note   : {cit.note}")
        out.append("      sql    : " + cit.sql.replace("\n", "\n               "))
        out.append("      result : " + json.dumps(cit.result))
    return out


def render(ans: RouterAnswer) -> str:
    out: list[str] = [f"Q: {ans.question}"]
    routed = ", ".join(f"{r.mode} ({r.reason})" for r in ans.routes)
    out.append(f"ROUTED → {routed}")
    out.append(f"GROUNDED BY → {', '.join(ans.modes_grounded) or '— (nothing)'}\n")

    for i, claim in enumerate(ans.claims, 1):
        out.append(f"CLAIM {i} [{claim.mode}]: {claim.text}")
        for cit in claim.citations:
            out.extend(_render_citation(claim.mode, cit))

    if ans.associations:
        out.append(f"\nASSOCIATIONS ({len(ans.associations)} edge(s)):")
        for e in ans.associations[:12]:
            conf = e.get("confidence", "")
            out.append(f"  {e.get('source')} --{e.get('relation', '?')}--> "
                       f"{e.get('target')}  [{conf}]")

    for fig in ans.figures:
        out.append(f"\nFIGURE {fig.spec}")
        out.append("  query  : " + fig.query.replace("\n", "\n           "))
        out.append("  result : " + json.dumps(fig.result))

    if ans.unanswered:
        out.append("\nUNANSWERED (no mode could ground — stated, not hidden):")
        for u in ans.unanswered:
            out.append(f"  • {u}")

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
