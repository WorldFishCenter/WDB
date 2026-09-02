"""The companion-note draft — deterministic, no LLM (the user's chosen scaffold/enrich path).

For a **tabular** file this runs the real ``.claude/scripts/dict_enricher.py`` and fills a Template-A
``## Columns`` block with the **actual value domains** the script extracts (the same deterministic
facts ``/enrich`` merges). Column *meanings* and the ``## Grain`` sentence stay scaffolded for the
operator to write or for ``/curate`` — honest: domains are real, prose is not invented. For PDF/doc it
returns a Template-B scaffold. This is exactly the input-side division PROTOCOL §6 + habit 4 describe.
"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

from .config import ENRICHER, WDB_ROOT
from .models import ColumnEntry, DraftedNote, SubmissionInput


def _missing(n: int | None) -> str:
    return f" ({n} missing)" if n else ""


def _domain(col: dict) -> str:
    """Render a column's value domain from the enricher's facts (never invented)."""
    kind = col.get("kind")
    miss = _missing(col.get("n_missing"))
    if kind == "categorical":
        vals = ", ".join(str(v) for v in col.get("values", []))
        return f"{col.get('n_distinct')} distinct ∈ {{{vals}}}{miss}"
    if kind == "high_cardinality":
        ex = ", ".join(str(v) for v in col.get("examples", []))
        return f"identifier — {col.get('n_distinct')} distinct (e.g. {ex}){miss}"
    if kind == "numeric":
        return f"range {col.get('min')}–{col.get('max')}{miss}"
    if kind == "datetime":
        return f"{col.get('min')} → {col.get('max')}{miss}"
    if kind == "constant":
        vals = ", ".join(str(v) for v in col.get("values", []))
        return f"constant — {vals}{miss}"
    # generic fallback: report whatever the script gave us, never fabricate
    bits = [f"{k}={col[k]}" for k in ("n_distinct", "min", "max") if col.get(k) is not None]
    return (", ".join(bits) + miss) or "value domain (review)"


def _run_enricher(path: Path) -> dict | None:
    try:
        proc = subprocess.run(
            ["uv", "run", str(ENRICHER), str(path), "--json"],
            cwd=str(WDB_ROOT),
            capture_output=True,
            text=True,
            timeout=180,
        )
        if proc.returncode != 0 or not proc.stdout.strip():
            return None
        return json.loads(proc.stdout)
    except (subprocess.SubprocessError, json.JSONDecodeError, OSError):
        return None


def draft_for(inp: SubmissionInput, staged_path: Path) -> DraftedNote:
    base = Path(inp.filename).stem
    if inp.format == "tabular":
        return _draft_tabular(inp, base, staged_path)
    return _draft_doc(inp, base)


def _draft_tabular(inp: SubmissionInput, base: str, staged_path: Path) -> DraftedNote:
    report = _run_enricher(staged_path)
    common = dict(
        template="A",
        filename=f"{base}_dict.md",
        title=f"Data dictionary: {inp.filename}",
        related_files=[f"{inp.initiative}_about.md (the initiative this dataset belongs to)"],
    )

    if not report or not report.get("valid", False):
        problems = "; ".join(report.get("problems", [])) if report else "the enricher could not read it"
        return DraftedNote(
            **common,
            summary=f"{inp.filename} — part of the {inp.initiative} initiative. (Auto-drafted; review before approving.)",
            grain="One row = … (state what one row IS in domain terms).",
            columns=[],
            notes_caveats=f"Not a tidy single table yet — {problems}. Reshape to one tidy table, then the value domains can be enriched.",
        )

    columns = [
        ColumnEntry(
            name=col.get("column", "?"),
            meaning="(describe what this column means — review)",
            domain=_domain(col),
        )
        for col in report.get("columns", [])
    ]
    return DraftedNote(
        **common,
        summary=f"{inp.filename} — part of the {inp.initiative} initiative. {report.get('n_rows', '?')} rows × {report.get('n_cols', '?')} columns. (Auto-drafted; value domains are real, review meanings + grain before approving.)",
        grain="One row = … (state what one row IS in domain terms; the value domains below are filled deterministically by the enricher — review the grain).",
        columns=columns,
        notes_caveats="Column value domains were extracted deterministically; meanings and grain need a human/`/curate` pass.",
    )


def _draft_doc(inp: SubmissionInput, base: str) -> DraftedNote:
    return DraftedNote(
        template="B",
        filename=f"{base}_context.md",
        title=f"Context: {inp.filename}",
        summary=f"{inp.filename} — part of the {inp.initiative} initiative. (Auto-drafted scaffold; fill in the summary and concepts, or run /curate, before approving.)",
        key_concepts=["(topics, regions, methods, or entities this file is about — review)"],
        related_files=[f"{inp.initiative}_about.md (the initiative this file belongs to)"],
    )
