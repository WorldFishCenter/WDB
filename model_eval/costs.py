"""Per-operation cost from REAL token usage + verified published rates.

Rates ($/1M tokens), verified at eval time:
  Anthropic (claude-api skill / platform.claude.com), 2026-06-18 — billed direct,
  NO gateway fee:
    Opus 4.8     $5.00 in / $25.00 out
    Sonnet 4.6   $3.00 in / $15.00 out
    Haiku 4.5    $1.00 in / $5.00 out
  Gemini native (ai.google.dev/gemini-api/docs/pricing, paid tier; thinking billed
  as output) — the #16 row:
    gemini-2.5-flash  $0.30 in / $2.50 out

  OpenRouter arm (GET https://openrouter.ai/api/v1/models, 2026-06-23). OpenRouter
  passes provider pricing through AT COST but adds a ~5.5% credit-purchase fee, so
  the effective $/token is the listed price x1.055 — folded into the rate here so
  measured cost is NOT understated (the task's "cost honesty" requirement). The
  raw list price is kept in a comment beside each so the fee is auditable.
    google/gemini-2.5-flash      list $0.30 / $2.50  -> x1.055 = $0.3165 / $2.6375
    deepseek/deepseek-v4-flash   list $0.09 / $0.18  -> x1.055 = $0.09495 / $0.1899
"""
from __future__ import annotations

OPENROUTER_FEE = 1.055  # ~5.5% credit-purchase fee applied on top of pass-through price

RATES = {  # $ per 1M tokens (input, output) — effective (gateway fee already folded in)
    "opus-4.8": (5.00, 25.00),
    "sonnet-4.6": (3.00, 15.00),
    "haiku-4.5": (1.00, 5.00),
    "gemini-2.5-flash": (0.30, 2.50),                       # native Gemini, no fee (#16)
    # OpenRouter slugs — list price x OPENROUTER_FEE:
    "gemini-2.5-flash-or": (0.30 * OPENROUTER_FEE, 2.50 * OPENROUTER_FEE),
    "deepseek-v4-flash-or": (0.09 * OPENROUTER_FEE, 0.18 * OPENROUTER_FEE),
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
