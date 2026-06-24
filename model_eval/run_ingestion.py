"""Ingestion-agent eval — JUDGMENT ONLY. Draft companion notes for 2 real docs.

No formal proof harness exists for the curator/enricher (the review gate IS the
proof). So each candidate drafts a real companion note — Template A for a tabular
file (zanzibar trips CSV) and Template B for a prose doc (the Peskas SoftwareX
paper) — and the drafts are saved for review against the protocol's note rubric:
correct sections filled, ONE canonical name in prose, explicit relationships,
no FORM/shape language, no invention. The structural proxies below AID that
judgment (section presence, canonical-name presence, shape-word leakage); they are
NOT the verdict, which is a human read of ``ingestion_drafts/`` (FINDINGS records it).

Run:  .venv/bin/python -m model_eval.run_ingestion
"""
from __future__ import annotations

import json
import re
from pathlib import Path

from . import backends, costs
from .prompts import INGESTION_BRIEF, TEMPLATE_A, TEMPLATE_B

HERE = Path(__file__).resolve().parent
SAMPLES = HERE / "sample_docs"
DRAFTS = HERE / "ingestion_drafts"
RESULTS = HERE / "results"

_SHAPE_WORDS = re.compile(r"\bwide\b|\blong\b|\bEAV\b|\b\.?csv\b|tidy|dataframe|one row per|"
                          r"column per|encoding|file type|pivot|crosstab", re.I)

DOCS = {
    "zanzibar_trips (Template A)": {
        "path": "peskas/zanzibar_validated_trips.csv",
        "sample": SAMPLES / "zanzibar_head.csv",
        "template": TEMPLATE_A,
        "sections": ["## Summary", "## Columns", "## Grain", "## Related files"],
        "canonical": ["zanzibar"],
    },
    "peskas_softwarex (Template B)": {
        "path": "peskas/peskas_automated_analytics_softwarex_2025.pdf",
        "sample": SAMPLES / "peskas_softwarex_p1-2.txt",
        "template": TEMPLATE_B,
        "sections": ["## Summary", "## Key concepts", "## Related files"],
        "canonical": ["peskas"],
    },
}


def proxies(note: str, spec: dict) -> dict:
    low = note.lower()
    return {
        "has_h1": bool(re.search(r"^# \S", note, re.M)),
        "sections_present": [s for s in spec["sections"] if s.lower() in low],
        "sections_missing": [s for s in spec["sections"] if s.lower() not in low],
        "canonical_named": any(c in low for c in spec["canonical"]),
        "shape_word_leak": sorted(set(m.group(0) for m in _SHAPE_WORDS.finditer(note))),
        "chars": len(note),
    }


def run_model(backend) -> dict:
    out = {"model": backend.name, "docs": {}}
    usages = []
    print(f"\n{'='*92}\nINGESTION — {backend.name}\n{'='*92}")
    for label, spec in DOCS.items():
        content = spec["sample"].read_text()
        system = INGESTION_BRIEF.format(template=spec["template"])
        user = f"File path in the repo: {spec['path']}\n\nFile content:\n\n{content}"
        # generous budget so Gemini's default thinking does not truncate the note
        # (Anthropic models finish well under this; cost reflects only tokens used)
        note, u = backend.text_call(system, user, max_tokens=6144)
        usages.append(u)
        px = proxies(note, spec)
        (DRAFTS / f"{spec['path'].split('/')[-1]}__{backend.name}.md").write_text(note)
        out["docs"][label] = {"proxies": px, "note": note}
        print(f"  {label:28} sections={len(px['sections_present'])}/{len(spec['sections'])} "
              f"canonical={px['canonical_named']} shape_leak={px['shape_word_leak']} "
              f"chars={px['chars']}")
    out["cost"] = costs.summarize(backend.name, usages)
    return out


def main(models=None, suffix="") -> int:
    """Default (no args) reproduces #16: Opus + Haiku + native Gemini drafts ->
    results/ingestion.json. The OpenRouter arm passes its own list + suffix; drafts
    are written per-model (filename carries backend.name) so they never collide.
    INGESTION_BRIEF is model-neutral already, so no per-provider prompt branch."""
    DRAFTS.mkdir(exist_ok=True)
    RESULTS.mkdir(exist_ok=True)
    report = {"models": []}
    if models is None:
        models = [backends.opus(), backends.haiku(), backends.gemini_flash()]
    for b in models:
        report["models"].append(run_model(b))
    (RESULTS / f"ingestion{suffix}.json").write_text(json.dumps(report, indent=2, default=str))
    print(f"\n{'='*92}\nSUMMARY (structural proxies only — verdict is a human read of ingestion_drafts/)\n{'='*92}")
    for m in report["models"]:
        c = m["cost"]
        leaks = sum(len(d["proxies"]["shape_word_leak"]) for d in m["docs"].values())
        miss = sum(len(d["proxies"]["sections_missing"]) for d in m["docs"].values())
        print(f"  {m['model']:18} missing_sections={miss} shape_leaks={leaks} ${c['usd_per_op']:.5f}/op")
    print(f"\nwrote {RESULTS / f'ingestion{suffix}.json'} + drafts in {DRAFTS}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
