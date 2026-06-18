"""Mode A reasoner eval — MECHANICAL. Cold-fabrication-rate + negative control.

Reuses the EXACT bar: ``mode_a.extract`` (deterministic subgraphs), the proof's 5
questions + 5 relational pairs (``cold_rate._cases``), and the deterministic
``citecheck`` (C1–C4) that the real pipeline gates on. Only the reasoner model is
swapped (behind the backend seam). Each candidate is judged COLD — each call sees
only one serialized subgraph — exactly like ``mode_a/cold_rate.py`` measured Opus
at 0/10. Reports fabrication rate (C1) and total cite-check rejections, plus a
model-independent negative control proving the guard still has teeth.

Run:  .venv/bin/python -m model_eval.run_mode_a
"""
from __future__ import annotations

import copy
import json
from pathlib import Path

from mode_a import extract
from mode_a.citecheck import cite_check, triple
from mode_a.cold_rate import _cases
from mode_a.reasoner import RESPONSE_SCHEMA, SYSTEM_PROMPT, build_user_prompt

from . import backends, costs
from .backends import JSONParseError
from .prompts import MODE_A_GEMINI

HERE = Path(__file__).resolve().parent
RAW, RESULTS = HERE / "raw", HERE / "results"


def _system(backend) -> str:
    return MODE_A_GEMINI if backend.provider == "gemini" else SYSTEM_PROMPT


def _sanitize(ans: dict) -> dict:
    for k in ("cited_edges", "inferred_flags"):
        if ans.get(k) is None:
            ans[k] = []
        ans[k] = [
            {kk: e.get(kk, "") for kk in ("source", "relation", "target", "confidence")}
            for e in ans[k] if isinstance(e, dict)
        ]
    ans.setdefault("connected", None)
    return ans


def run_model(backend, g) -> dict:
    system = _system(backend)
    rows, usages, raw = [], [], {}
    print(f"\n{'='*92}\nMODE A — {backend.name}\n{'='*92}")
    for qid, question, build in _cases(g):
        sub = build()
        sub.question = question
        user = build_user_prompt(sub.serialize())
        try:
            ans, u = backend.json_call(system, user, RESPONSE_SCHEMA, max_tokens=4096)
            usages.append(u)
        except JSONParseError as e:
            usages.append(getattr(e, "usage", backends.Usage()))
            rows.append({"qid": qid, "honest": False, "fabricated": False,
                         "attribution": "structured-output", "note": str(e)[:120]})
            print(f"  {qid:4} [struct-fail] JSON parse error")
            continue
        raw[qid] = ans
        v = cite_check(sub.edges, sub.disconnected, _sanitize(ans))
        fab = bool(v.fabricated)
        rows.append({
            "qid": qid, "edges": len(sub.edges), "disconnected": sub.disconnected,
            "connected_claim": v.connected_claim, "n_cited": v.n_cited,
            "honest": v.honest, "fabricated": fab, "checks": v.checks,
            "attribution": "" if v.honest else "reasoning",
        })
        tag = "clean" if v.honest else ("FABRICATED" if fab else "REJECTED")
        print(f"  {qid:4} edges={len(sub.edges):2} disc={str(sub.disconnected):5} "
              f"connected={str(v.connected_claim):5} cited={v.n_cited:2} {v.checks} -> {tag}")
        if fab:
            print(f"       !! cited-but-absent: {[triple(e) for e in v.fabricated]}")

    n = len(rows)
    n_fab = sum(r.get("fabricated") for r in rows)
    n_rej = sum(not r["honest"] for r in rows)
    (RAW / f"mode_a_{backend.name}.json").write_text(json.dumps(raw, indent=2, default=str))
    return {"model": backend.name, "n": n, "fabrications": n_fab, "rejections": n_rej,
            "rows": rows, "cost": costs.summarize(backend.name, usages)}


def negative_control(g) -> dict:
    """Model-independent: prove the cite-check rejects an injected fabrication on the
    decisive not-connected case (FASA <-> WIO harmonization, a 0-edge subgraph)."""
    sub = extract.relate(g, "FASA", "WIO data harmonization")
    sub.question = "test"
    real = {"answer": "no link", "connected": False, "cited_edges": [], "inferred_flags": []}
    honest_v = cite_check(sub.edges, sub.disconnected, real)
    bad = copy.deepcopy(real)
    bad["connected"] = True
    bad["cited_edges"] = [{"source": "fasa_repo", "relation": "shares_data_with",
                           "target": "data_harmonization_hub", "confidence": "EXTRACTED"}]
    bad_v = cite_check(sub.edges, sub.disconnected, bad)
    caught = (not bad_v.honest) and bool(bad_v.fabricated)
    print(f"\nNEGATIVE CONTROL (model-independent): disconnected={sub.disconnected}; "
          f"honest-answer passes={honest_v.honest}; injected-fabrication caught={caught}")
    return {"disconnected": sub.disconnected, "honest_answer_passes": honest_v.honest,
            "fabrication_caught": caught}


def main() -> int:
    RAW.mkdir(exist_ok=True)
    RESULTS.mkdir(exist_ok=True)
    g = extract.get_graph()
    report = {"negative_control": negative_control(g), "models": []}
    for b in [backends.opus(), backends.haiku(), backends.gemini_flash()]:
        report["models"].append(run_model(b, g))
    (RESULTS / "mode_a.json").write_text(json.dumps(report, indent=2, default=str))

    print(f"\n{'='*92}\nSUMMARY (cold-fabrication-rate; baseline Opus target = 0/10)\n{'='*92}")
    for m in report["models"]:
        c = m["cost"]
        print(f"  {m['model']:18} fabrications {m['fabrications']}/{m['n']}  "
              f"cite-check rejections {m['rejections']}/{m['n']}  "
              f"${c['usd_per_op']:.5f}/op (in {c['avg_in_tok']:.0f} / out {c['avg_out_tok']:.0f} tok)")
    print(f"\nwrote {RESULTS / 'mode_a.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
