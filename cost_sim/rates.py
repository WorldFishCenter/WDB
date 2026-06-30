"""Per-token rates for every model in FINDINGS.md, keyed by the exact model ID
that appears in the provider API call.

Sources (verified at model_eval time, 2026-06-18 / 2026-06-23):
  Anthropic direct (no fee): platform.claude.com
  Gemini native (no fee):    ai.google.dev/gemini-api/docs/pricing, paid tier
  OpenRouter (+5.5% fee):    openrouter.ai/api/v1/models — list price × 1.055
"""
from __future__ import annotations

OPENROUTER_FEE = 1.055  # folded into the OR rates so cost is never understated

# ($ per 1M input tokens, $ per 1M output tokens) — fee-inclusive where applicable
RATES: dict[str, tuple[float, float]] = {
    # ── Anthropic, billed direct ─────────────────────────────────────────── #
    "claude-opus-4-8":             (5.00,  25.00),
    "claude-sonnet-4-6":           (3.00,  15.00),
    "claude-haiku-4-5":            (1.00,   5.00),
    "claude-haiku-4-5-20251001":   (1.00,   5.00),  # dated alias same tier
    # ── Gemini via native AI-Studio key, billed direct (thinking = output) ─ #
    "gemini-2.5-flash":            (0.30,   2.50),
    # ── OpenRouter gateway (list price × 1.055) ──────────────────────────── #
    # Slug confirmed live via GET /api/v1/models on 2026-06-23.
    "google/gemini-2.5-flash":     (0.30 * OPENROUTER_FEE, 2.50 * OPENROUTER_FEE),
    "deepseek/deepseek-v4-flash":  (0.09 * OPENROUTER_FEE, 0.18 * OPENROUTER_FEE),
}

# Human-readable short labels for the report table.
LABELS: dict[str, str] = {
    "claude-opus-4-8":            "Opus 4.8",
    "claude-sonnet-4-6":          "Sonnet 4.6",
    "claude-haiku-4-5":           "Haiku 4.5",
    "claude-haiku-4-5-20251001":  "Haiku 4.5",
    "gemini-2.5-flash":           "Gemini 2.5 Flash (native)",
    "google/gemini-2.5-flash":    "Gemini 2.5 Flash (OR)",
    "deepseek/deepseek-v4-flash": "DeepSeek v4-flash (OR)",
}

# Which provider each model needs — used by run.py to warn if a backend can't call it.
PROVIDER: dict[str, str] = {
    "claude-opus-4-8":            "anthropic",
    "claude-sonnet-4-6":          "anthropic",
    "claude-haiku-4-5":           "anthropic",
    "claude-haiku-4-5-20251001":  "anthropic",
    "gemini-2.5-flash":           "gemini",
    "google/gemini-2.5-flash":    "openrouter",
    "deepseek/deepseek-v4-flash": "openrouter",
}


def cost_usd(model_id: str, in_tok: int, out_tok: int) -> float:
    """Compute cost in USD for one call. Raises KeyError for unrecognised model IDs."""
    if model_id not in RATES:
        raise KeyError(
            f"Unknown model ID {model_id!r}. Known: {sorted(RATES)}"
        )
    cin, cout = RATES[model_id]
    return in_tok / 1e6 * cin + out_tok / 1e6 * cout


def label(model_id: str) -> str:
    return LABELS.get(model_id, model_id)
