"""WDB session cost emulator — fire a question set through Live backends, measure
real token usage, and project monthly cost under configurable model assignments.

Usage:
    uv run python -m cost_sim.run                             # current production pins
    uv run python -m cost_sim.run --model-b claude-haiku-4-5  # test B→Haiku
    uv run python -m cost_sim.run --out results.json          # also write JSON

Requires ANTHROPIC_API_KEY. All three slots (A/B/C) use the Anthropic SDK, so only
Anthropic model IDs are valid for --model-* (Opus, Sonnet, Haiku). Non-Anthropic
models (Gemini, DeepSeek) are in rates.py for reference / manual projection only —
they would need their own backend analogous to model_eval/backends.py.

Output sections:
  1. Per-question cost breakdown (modes activated + tokens + cost)
  2. Aggregate by slot (model, calls, avg tokens, avg cost/call)
  3. Monthly projections at several volumes under:
     • The models you passed (or production defaults)
     • §9 recommended: B→Haiku (same tokens, Haiku rate for Mode B)
     • B+A→Haiku for reference only (Haiku fabricates on A per FINDINGS.md §4)
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from dataclasses import dataclass, field
from datetime import date

import anthropic

from mode_a.model import REASONER_MODEL
from mode_a.reasoner import LiveReasoner
from mode_b.model import SYNTH_MODEL
from mode_b.synth import LiveSynthesizer
from mode_c.model import RESOLVER_MODEL
from mode_c.resolver import LiveResolver
from wdb_router.backends import WDB_ROOT, Backends
from wdb_router.dispatch import answer

from .questions import QUESTIONS
from .rates import LABELS, PROVIDER, RATES, cost_usd, label
from .tracker import CallRecord, CostLog, TrackingClient

# ── ANSI colours (disabled on non-TTY) ────────────────────────────────────── #
_TTY = sys.stdout.isatty()


def _c(code: str, text: str) -> str:
    return f"\033[{code}m{text}\033[0m" if _TTY else text


# ── Per-question result container ─────────────────────────────────────────── #

@dataclass
class QuestionResult:
    idx: int
    question: str
    modes: list[str]                    # mode letters that made an LLM call (A/B/C)
    records: list[CallRecord]           # CallRecords attributed to this question
    error: str | None

    @property
    def cost_usd(self) -> float:
        return sum(r.cost_usd for r in self.records)

    @property
    def in_tok(self) -> int:
        return sum(r.in_tok for r in self.records)

    @property
    def out_tok(self) -> int:
        return sum(r.out_tok for r in self.records)


# ── Backend construction ───────────────────────────────────────────────────── #

def _tracked_backends(log: CostLog, model_a: str, model_b: str, model_c: str) -> Backends:
    """Live Backends dataclass with TrackingClient injected into each LLM slot."""
    from mode_a import extract as a_extract
    from mode_b.corpus import walk_corpus
    from mode_b.index import DEFAULT_INDEX_DIR, open_collection
    from mode_b.pipeline import load_graph_default
    from mode_b.retrieve import LiveRetriever
    from mode_c.catalog import load_catalog

    real = anthropic.Anthropic()
    nodes, links = load_graph_default()
    collection = open_collection(DEFAULT_INDEX_DIR)
    catalog = load_catalog(WDB_ROOT)
    known_initiatives = {f.split("/")[0] for f in walk_corpus(WDB_ROOT) if "/" in f}

    return Backends(
        a_reasoner=LiveReasoner(
            client=TrackingClient(real, log, "mode_a"),
            model=model_a,
        ),
        a_graph=a_extract.get_graph(),
        nodes=nodes,
        links=links,
        b_retriever=LiveRetriever(collection, use_reranker=True),
        b_synth=LiveSynthesizer(
            client=TrackingClient(real, log, "mode_b"),
            model=model_b,
        ),
        known_initiatives=known_initiatives,
        catalog=catalog,
        c_resolver=LiveResolver(
            catalog,
            client=TrackingClient(real, log, "mode_c"),
            model=model_c,
        ),
    )


# ── Cost helpers ──────────────────────────────────────────────────────────── #

def _money(usd: float) -> str:
    return f"${usd:.5f}" if usd < 0.001 else f"${usd:.4f}"


def _monthly(avg_per_q: float, qpd: int) -> float:
    return avg_per_q * qpd * 30


def _repriced(results: list[QuestionResult], overrides: dict[str, str]) -> float:
    """Total cost if certain slots used a different model (same real token counts)."""
    total = 0.0
    for qr in results:
        for r in qr.records:
            model = overrides.get(r.slot, r.model)
            total += cost_usd(model, r.in_tok, r.out_tok)
    return total


# ── Report printing ───────────────────────────────────────────────────────── #

def _print_report(
    results: list[QuestionResult],
    log: CostLog,
    model_a: str,
    model_b: str,
    model_c: str,
) -> None:
    ok = [r for r in results if not r.error]
    failed = [r for r in results if r.error]

    print()
    print(_c("1", f"=== WDB cost simulation — {len(results)} questions ({date.today()}) ==="))
    print(f"  mode_a → {_c('36', label(model_a))}  "
          f"mode_b → {_c('36', label(model_b))}  "
          f"mode_c → {_c('36', label(model_c))}")
    print()

    # ── Per-question ───────────────────────────────────────────────────────── #
    print(_c("1", "QUESTION RESULTS"))
    print("─" * 88)
    print(f"  {'#':>2}  {'Modes':<7}  {'Cost':>8}   {'in':>6} / {'out':>6}   Question")
    print("─" * 88)
    for qr in results:
        modes_str = "+".join(qr.modes) if qr.modes else "—"
        cost_str = _money(qr.cost_usd) if not qr.error else _c("33", "ERROR")
        tok_str = f"{qr.in_tok:>6} / {qr.out_tok:>6}" if not qr.error else "           "
        q = qr.question[:58] + ("…" if len(qr.question) > 58 else "")
        print(f"  {qr.idx:>2}  {modes_str:<7}  {cost_str:>8}   {tok_str}   {q}")
        if qr.error:
            print(f"      {_c('33', '  └─ ' + qr.error[:78])}")
    print("─" * 88)
    print()

    if not ok:
        print(_c("33", "All questions errored — no aggregate to report."))
        return

    # ── Aggregate by slot ─────────────────────────────────────────────────── #
    print(_c("1", "AGGREGATE BY SLOT"))
    print("─" * 88)
    by_slot = log.by_slot()
    for slot, model in (("mode_a", model_a), ("mode_b", model_b), ("mode_c", model_c)):
        recs = by_slot.get(slot, [])
        if not recs:
            print(f"  {slot:<8}  {label(model):<28}  — no LLM calls (all questions bypassed this slot)")
            continue
        slot_cost = sum(r.cost_usd for r in recs)
        avg_in = sum(r.in_tok for r in recs) / len(recs)
        avg_out = sum(r.out_tok for r in recs) / len(recs)
        print(
            f"  {slot:<8}  {label(model):<28}  "
            f"{len(recs):>3} calls  "
            f"avg {avg_in:>6.0f}/{avg_out:>5.0f} tok  "
            f"avg {_money(slot_cost / len(recs))}/call  "
            f"total {_money(slot_cost)}"
        )
    total_cost = sum(qr.cost_usd for qr in ok)
    total_calls = sum(len(r.records) for r in ok)
    avg_per_q = total_cost / len(ok)
    print("─" * 88)
    print(
        f"  {'TOTAL':<8}  {'':28}  {total_calls:>3} calls  "
        f"{'':>18}  avg {_money(avg_per_q)}/question  total {_money(total_cost)}"
    )
    print()

    # ── Monthly projections ───────────────────────────────────────────────── #
    haiku = "claude-haiku-4-5"
    avg_b_haiku = _repriced(ok, {"mode_b": haiku}) / len(ok)
    avg_ab_haiku = _repriced(ok, {"mode_a": haiku, "mode_b": haiku}) / len(ok)

    print(_c("1", "MONTHLY PROJECTIONS  (queries/day × 30 days)"))
    print(_c("2", "  Re-prices REAL measured token counts from this run at each model's rate."))
    print(_c("2", f"  §9 recommended: B→{label(haiku)}."))
    print(_c("2", "  A+B→Haiku: for reference only — Haiku fabricates on A (FINDINGS.md §4)."))
    print()
    print(f"  {'q/day':>7}  {'current pins':>15}  {'§9 B→Haiku':>13}  {'A+B→Haiku (ref)':>16}  saving §9")
    print("  " + "─" * 70)
    for qpd in (10, 50, 100, 500, 1000):
        cur = _monthly(avg_per_q, qpd)
        b_h = _monthly(avg_b_haiku, qpd)
        ab_h = _monthly(avg_ab_haiku, qpd)
        saving = (cur - b_h) / cur * 100 if cur else 0.0
        print(f"  {qpd:>7}  ${cur:>14.2f}  ${b_h:>12.2f}  ${ab_h:>15.2f}  {saving:.1f}%")
    print()
    if failed:
        print(_c("33", f"  {len(failed)} question(s) errored and are excluded from projections."))
        print()


# ── JSON serialisation ────────────────────────────────────────────────────── #

def _to_json(
    results: list[QuestionResult],
    log: CostLog,
    model_a: str,
    model_b: str,
    model_c: str,
) -> dict:
    ok = [r for r in results if not r.error]
    by_slot = log.by_slot()
    return {
        "date": date.today().isoformat(),
        "models": {"mode_a": model_a, "mode_b": model_b, "mode_c": model_c},
        "questions": [
            {
                "idx": qr.idx,
                "question": qr.question,
                "modes": qr.modes,
                "cost_usd": round(qr.cost_usd, 6),
                "in_tok": qr.in_tok,
                "out_tok": qr.out_tok,
                "error": qr.error,
                "calls": [
                    {
                        "slot": r.slot,
                        "model": r.model,
                        "in_tok": r.in_tok,
                        "out_tok": r.out_tok,
                        "cost_usd": round(r.cost_usd, 6),
                    }
                    for r in qr.records
                ],
            }
            for qr in results
        ],
        "aggregate": {
            slot: {
                "model": recs[0].model,
                "calls": len(recs),
                "in_tok_total": sum(r.in_tok for r in recs),
                "out_tok_total": sum(r.out_tok for r in recs),
                "cost_total_usd": round(sum(r.cost_usd for r in recs), 6),
                "cost_per_call_usd": round(sum(r.cost_usd for r in recs) / len(recs), 6),
            }
            for slot, recs in by_slot.items()
        },
        "total_cost_usd": round(sum(qr.cost_usd for qr in ok), 6),
        "avg_cost_per_question_usd": round(
            sum(qr.cost_usd for qr in ok) / len(ok), 6
        ) if ok else 0.0,
    }


# ── Entry point ───────────────────────────────────────────────────────────── #

def _parse() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="WDB session cost emulator — requires ANTHROPIC_API_KEY."
    )
    p.add_argument("--model-a", default=REASONER_MODEL,
                   help=f"Anthropic model ID for Mode A (default: {REASONER_MODEL})")
    p.add_argument("--model-b", default=SYNTH_MODEL,
                   help=f"Anthropic model ID for Mode B (default: {SYNTH_MODEL})")
    p.add_argument("--model-c", default=RESOLVER_MODEL,
                   help=f"Anthropic model ID for Mode C (default: {RESOLVER_MODEL})")
    p.add_argument("--questions",
                   help="JSON file: list of question strings (default: built-in fixture)")
    p.add_argument("--out",
                   help="Write JSON cost summary to this path")
    return p.parse_args()


def main() -> None:
    args = _parse()
    model_a, model_b, model_c = args.model_a, args.model_b, args.model_c

    for flag, mid in (("--model-a", model_a), ("--model-b", model_b), ("--model-c", model_c)):
        if mid not in RATES:
            print(f"Error: {flag} {mid!r} is not in rates.py. Known: {sorted(RATES)}",
                  file=sys.stderr)
            sys.exit(1)
        if PROVIDER.get(mid) != "anthropic":
            print(
                f"Error: {flag} {mid!r} requires a non-Anthropic backend. "
                "Only Anthropic models (Opus/Sonnet/Haiku) work here. "
                "For Gemini/DeepSeek, adapt model_eval/backends.py.",
                file=sys.stderr,
            )
            sys.exit(1)

    if not os.environ.get("ANTHROPIC_API_KEY"):
        print("Error: ANTHROPIC_API_KEY is not set.", file=sys.stderr)
        sys.exit(1)

    questions: list[str] = QUESTIONS
    if args.questions:
        with open(args.questions) as f:
            questions = json.load(f)
        if not isinstance(questions, list) or not all(isinstance(q, str) for q in questions):
            print("Error: --questions must be a JSON array of strings.", file=sys.stderr)
            sys.exit(1)

    print(f"Loading backends (Chroma index + graph)…", end=" ", flush=True)
    log = CostLog()
    backends = _tracked_backends(log, model_a, model_b, model_c)
    print("done.")
    print(f"Running {len(questions)} questions…\n")

    results: list[QuestionResult] = []
    for i, q in enumerate(questions, 1):
        ts = time.time()
        print(f"  [{i:>2}/{len(questions)}] {q[:72]}", end=" … ", flush=True)
        try:
            answer(q, backends)
            recs = log.since(ts)
            modes = sorted({r.slot.split("_")[1].upper() for r in recs})
            err = None
        except Exception as exc:
            recs = log.since(ts)
            modes = []
            err = f"{type(exc).__name__}: {exc}"
        q_cost = sum(r.cost_usd for r in recs)
        print(_money(q_cost) if not err else f"ERROR ({err[:40]})")
        results.append(QuestionResult(idx=i, question=q, modes=modes, records=recs, error=err))

    _print_report(results, log, model_a, model_b, model_c)

    if args.out:
        payload = _to_json(results, log, model_a, model_b, model_c)
        with open(args.out, "w") as f:
            json.dump(payload, f, indent=2)
        print(f"JSON written to {args.out}")


if __name__ == "__main__":
    main()
