"""Per-operation cost from REAL token usage + verified published rates.

Rates ($/1M tokens), verified at eval time (2026-06-18):
  Anthropic (claude-api skill / platform.claude.com):
    Opus 4.8     $5.00 in / $25.00 out
    Sonnet 4.6   $3.00 in / $15.00 out
    Haiku 4.5    $1.00 in / $5.00 out
  Gemini (ai.google.dev/gemini-api/docs/pricing, paid tier; thinking billed as output):
    gemini-2.5-flash  $0.30 in / $2.50 out
"""
from __future__ import annotations

RATES = {  # $ per 1M tokens (input, output)
    "opus-4.8": (5.00, 25.00),
    "sonnet-4.6": (3.00, 15.00),
    "haiku-4.5": (1.00, 5.00),
    "gemini-2.5-flash": (0.30, 2.50),
}


def cost_usd(name: str, in_tok: int, out_tok: int) -> float:
    cin, cout = RATES[name]
    return in_tok / 1e6 * cin + out_tok / 1e6 * cout


def summarize(name: str, usages: list) -> dict:
    """Aggregate a list of Usage objects into a per-op cost summary for one model."""
    n = len(usages) or 1
    tin = sum(u.in_tok for u in usages)
    tout = sum(u.out_tok for u in usages)
    tthink = sum(u.thinking_tok for u in usages)
    total = cost_usd(name, tin, tout)
    return {
        "model": name,
        "ops": len(usages),
        "in_tok_total": tin,
        "out_tok_total": tout,
        "thinking_tok_total": tthink,
        "avg_in_tok": round(tin / n, 1),
        "avg_out_tok": round(tout / n, 1),
        "usd_total": round(total, 6),
        "usd_per_op": round(total / n, 6),
    }
