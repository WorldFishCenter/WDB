"""Driver for the OpenRouter arm — every non-Anthropic candidate via the official
OpenAI-compatible gateway, across all four slots.

This extends #16 (which tested Haiku direct + Gemini via the native AI-Studio key)
with the task's revised plan: route ALL non-Anthropic candidates through OpenRouter
and add the ultra-cheap OPEN model DeepSeek. Per the approved scope it REUSES #16's
committed Opus/Sonnet baseline + Haiku rows as reference and only runs the two new
OpenRouter candidates here — writing them to results/<slot>_openrouter.json so the
committed #16 baselines are never overwritten.

Candidates (slugs confirmed live via the OpenRouter models API, 2026-06-23):
  * google/gemini-2.5-flash      — Gemini, now via the gateway (vs #16's native row)
  * deepseek/deepseek-v4-flash   — the cheap flash-tier open model (the standout)

Each is judged by the SAME proof as the baseline, on a fair model-neutral prompt,
with json_object structured output. Run:  .venv/bin/python -m model_eval.run_openrouter
"""
from __future__ import annotations

from . import backends, run_ingestion, run_mode_a, run_mode_b, run_mode_c

SUFFIX = "_openrouter"


def candidates():
    return [backends.gemini_or(), backends.deepseek_or()]


def main() -> int:
    cands = candidates()
    names = ", ".join(b.name for b in cands)
    print("#" * 92)
    print(f"# OpenRouter arm — candidates: {names}")
    print(f"# baselines (Opus/Sonnet) + Haiku reused from #16's committed results/*.json")
    print("#" * 92)

    run_mode_c.main(models=cands, suffix=SUFFIX)
    run_mode_a.main(models=cands, suffix=SUFFIX)
    run_mode_b.main(models=cands, suffix=SUFFIX)
    run_ingestion.main(models=cands, suffix=SUFFIX)

    print("\n" + "#" * 92)
    print("# OpenRouter arm complete. Results: results/{mode_a,mode_b,mode_c,ingestion}_openrouter.json")
    print("# Drafts: ingestion_drafts/*__{gemini-2.5-flash-or,deepseek-v4-flash-or}.md")
    print("#" * 92)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
