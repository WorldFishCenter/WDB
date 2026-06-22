"""Tiny .env loader for the model_eval harness (read-only over the repo .env).

Reads the two keys the eval needs (ANTHROPIC_API_KEY, GEMINI_API_KEY) from the
repo-root .env WITHOUT printing them. Never writes, never mutates os.environ for
anything but this process. Mirrors the isolation posture of proof_a/proof_c.
"""
from __future__ import annotations

import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ENV = ROOT / ".env"


def load() -> dict[str, str]:
    out: dict[str, str] = {}
    if not ENV.exists():
        return out
    for line in ENV.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        out[k.strip()] = v.strip().strip('"').strip("'")
    return out


_E = load()


def anthropic_key() -> str | None:
    return _E.get("ANTHROPIC_API_KEY") or os.environ.get("ANTHROPIC_API_KEY")


def gemini_key() -> str | None:
    # The task flags a likely typo (GEMINAI_API_KEY); accept either, prefer the
    # canonical name. STOP-and-report is handled by the caller when both are absent.
    return (
        _E.get("GEMINI_API_KEY")
        or _E.get("GEMINAI_API_KEY")
        or os.environ.get("GEMINI_API_KEY")
        or os.environ.get("GEMINAI_API_KEY")
    )
