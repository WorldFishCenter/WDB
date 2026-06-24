"""Mode C resolver eval — MECHANICAL. 9 resolver questions + naive-control diagnostic.

Each candidate's structured resolution is run through the REAL Mode-C pipeline:
``vetted_band`` (the gate that structurally refuses the grain trap) then DuckDB
``executor`` over the committed CSVs. The computed figure is compared to ground
truth obtained by executing the proof's recorded Opus resolutions. Pass = correct
figure (grain trap: 31.88 not 28.99), honest refusal where due (Kisumu, wind),
disambiguation where due (region-less Gill Net), derived metric flagged (CPUE).

Failure attribution per question: reasoning (wrong table/figure/grain-trapped),
structured-output (unparseable / schema-incomplete), or prompt-fit (flagged in
review). Run:  .venv/bin/python -m model_eval.run_mode_c
"""
from __future__ import annotations

import json
from pathlib import Path

from mode_c.catalog import load_catalog
from mode_c.executor import ExecutionError, execute
from mode_c.fixtures import RECORDED, PROOF_QUESTIONS
from mode_c.fixtures.resolutions import Q1, Q2, Q3A, Q3B, Q4, Q4B, Q5A, Q5B, Q6
from mode_c.gate import vetted_band
from mode_c.resolution import CannotResolve, NeedsDisambiguation, Resolution
from mode_c.resolver import RESOLUTION_SCHEMA, build_resolver_prompt, outcome_from_dict

from . import backends, costs
from .backends import JSONParseError
from .prompts import MODE_C_NAIVE, RESOLVER_CONVENTIONS, mode_c_gemini

HERE = Path(__file__).resolve().parent
RAW = HERE / "raw"
RESULTS = HERE / "results"

# Expected category per question (the bar). "resolve" carries a ground-truth figure;
# "derived" must be a flagged derived metric; the grain questions are decisive.
EXPECT = {
    Q1: "resolve", Q2: "derived", Q3A: "needs_disambiguation", Q3B: "resolve",
    Q4: "grain", Q4B: "grain", Q5A: "cannot_resolve", Q5B: "cannot_resolve", Q6: "resolve",
}


def _sanitize(data: dict) -> dict:
    """Normalise explicit JSON null -> [] for list fields so a model that emits
    "filters": null (instead of omitting it) is not miscounted a structured-output
    failure. Pure normalisation; it never changes a non-null value."""
    for k in ("filters", "derived_inputs", "candidates", "assumptions"):
        if data.get(k) is None:
            data[k] = []
    return data


def _figure(res: Resolution, catalog) -> float | None:
    out = execute(res, catalog)
    if out.empty:
        return None
    row = out.rows[0]
    vals = [v for k, v in row.items() if k != "n"]
    return float(vals[0]) if vals and vals[0] is not None else None


def ground_truth(catalog) -> dict:
    """Correct figures, computed by executing the proof's recorded Opus resolutions."""
    gt = {}
    for q, res in RECORDED.items():
        if isinstance(res, Resolution):
            try:
                gt[q] = _figure(res, catalog)
            except ExecutionError:
                gt[q] = None
    return gt


def _system(backend, catalog) -> str:
    # Non-Claude candidates (native Gemini AND every OpenRouter slug) get the same
    # requirements re-expressed in model-neutral numbered-imperative style; Claude
    # models (Opus baseline, Haiku) get the existing pinned prompt verbatim (fair).
    if backend.provider in ("gemini", "openrouter"):
        return mode_c_gemini(catalog.render_corpus())
    return build_resolver_prompt(catalog)            # the existing Claude prompt (fair for Haiku)


def grade(q, outcome, catalog, truth) -> tuple[bool, str, str, dict]:
    """Return (passed, verdict, attribution, detail)."""
    want = EXPECT[q]
    detail: dict = {"outcome_type": type(outcome).__name__}

    if want in ("resolve", "derived", "grain"):
        if not isinstance(outcome, Resolution):
            return False, f"expected a resolution, got {type(outcome).__name__}", "reasoning", detail
        gate = vetted_band(outcome, catalog)
        detail["gate_ok"] = gate.ok
        detail["gate_reason"] = gate.reason
        detail["table"] = outcome.table
        detail["grain_key"] = outcome.grain_key
        if not gate.ok:
            # gate refusal on a grain trap = the model fell into it (reasoning);
            # the structural backstop prevented a wrong number but utility is lost.
            attr = "reasoning" if "grain trap" in gate.reason else "reasoning"
            return False, f"gate refused: {gate.reason}", attr, detail
        if want == "derived":
            ok = bool(outcome.derived_formula) and bool(outcome.assumptions)
            detail["derived_formula"] = outcome.derived_formula
            detail["assumptions"] = list(outcome.assumptions)
            if not ok:
                return False, "CPUE not flagged as a derived metric (proxy/relabel)", "reasoning", detail
            try:
                detail["figure"] = _figure(outcome, catalog)
            except ExecutionError as e:
                return False, f"derived formula failed to execute: {e}", "reasoning", detail
            return True, f"derived CPUE flagged + executes ({detail['figure']})", "", detail
        # resolve / grain: compare the executed figure to ground truth
        try:
            fig = _figure(outcome, catalog)
        except ExecutionError as e:
            return False, f"execution failed: {e}", "reasoning", detail
        detail["figure"] = fig
        tv = truth.get(q)
        if fig is None:
            return False, f"resolved but computed nothing (expected ~{tv})", "reasoning", detail
        if tv is not None and abs(fig - tv) <= max(0.05, abs(tv) * 0.005):
            return True, f"correct figure {fig} (truth {tv})", "", detail
        return False, f"WRONG figure {fig} (truth {tv})", "reasoning", detail

    if want == "cannot_resolve":
        if isinstance(outcome, CannotResolve):
            return True, f"correctly refused: {outcome.reason[:60]}", "", detail
        return False, f"failed to refuse (got {type(outcome).__name__})", "reasoning", detail

    if want == "needs_disambiguation":
        if isinstance(outcome, NeedsDisambiguation):
            return True, "correctly asked to disambiguate", "", detail
        return False, f"failed to disambiguate (got {type(outcome).__name__})", "reasoning", detail
    raise AssertionError(want)


def run_model(backend, catalog, truth) -> dict:
    system = _system(backend, catalog)
    rows, usages, raw = [], [], {}
    print(f"\n{'='*84}\nMODE C — {backend.name}\n{'='*84}")
    for q in PROOF_QUESTIONS:
        try:
            data, u = backend.json_call(system, q, RESOLUTION_SCHEMA, contract=RESOLVER_CONVENTIONS)
            usages.append(u)
            raw[q] = data
            try:
                outcome = outcome_from_dict(_sanitize(data))
            except Exception as e:  # malformed structure: resolve missing required fields
                rows.append({"q": q, "passed": False, "verdict": f"unparseable resolution: {e}",
                             "attribution": "structured-output", "detail": {"data": data}})
                print(f"  [FAIL/struct] {q[:46]:46} {e}")
                continue
            passed, verdict, attr, detail = grade(q, outcome, catalog, truth)
        except JSONParseError as e:
            usages.append(getattr(e, "usage", backends.Usage()))
            rows.append({"q": q, "passed": False, "verdict": str(e)[:120],
                         "attribution": "structured-output", "detail": {}})
            print(f"  [FAIL/struct] {q[:46]:46} JSON parse error")
            continue
        rows.append({"q": q, "passed": passed, "verdict": verdict, "attribution": attr, "detail": detail})
        flag = "PASS " if passed else f"FAIL/{attr[:6]}"
        print(f"  [{flag:11}] {q[:46]:46} {verdict[:70]}")

    n_pass = sum(r["passed"] for r in rows)
    decisive = next(r for r in rows if r["q"] == Q4)  # the grain trap
    (RAW / f"mode_c_{backend.name}.json").write_text(json.dumps(raw, indent=2, default=str))
    return {
        "model": backend.name, "passed": n_pass, "total": len(rows),
        "grain_trap_pass": decisive["passed"], "rows": rows,
        "cost": costs.summarize(backend.name, usages),
    }


def run_naive_diagnostic(backend, catalog) -> dict:
    """Diagnostic arm: does the model get grain/derived right WITHOUT the guard?"""
    system = MODE_C_NAIVE.format(catalog_corpus=catalog.render_corpus())
    out = {}
    for q, key in [(Q4, "grain_Q4"), (Q2, "cpue_Q2")]:
        try:
            data, _ = backend.json_call(system, q, RESOLUTION_SCHEMA, contract=RESOLVER_CONVENTIONS)
            outcome = outcome_from_dict(_sanitize(data))
            if isinstance(outcome, Resolution):
                gate = vetted_band(outcome, catalog)
                out[key] = {"grain_key": outcome.grain_key, "derived": bool(outcome.derived_formula),
                            "gate_ok": gate.ok, "gate_reason": gate.reason if not gate.ok else "",
                            "label": outcome.metric_label}
            else:
                out[key] = {"outcome": type(outcome).__name__}
        except Exception as e:  # noqa: BLE001
            out[key] = {"error": str(e)[:120]}
    return out


def main(models=None, suffix="") -> int:
    """Default (no args) reproduces #16 byte-for-byte: the same three models written
    to results/mode_c.json. The OpenRouter arm passes its own model list + suffix
    (run_openrouter.py) so it never clobbers the committed baseline rows."""
    RAW.mkdir(exist_ok=True)
    RESULTS.mkdir(exist_ok=True)
    catalog = load_catalog()
    truth = ground_truth(catalog)
    print("GROUND TRUTH (executed from recorded Opus resolutions):")
    for q, v in truth.items():
        print(f"   {q[:50]:50} -> {v}")

    if models is None:
        models = [backends.opus(), backends.haiku(), backends.gemini_flash()]
    report = {"ground_truth": {k: v for k, v in truth.items()}, "models": [], "naive_diagnostic": {}}
    for b in models:
        report["models"].append(run_model(b, catalog, truth))
        report["naive_diagnostic"][b.name] = run_naive_diagnostic(b, catalog)

    (RESULTS / f"mode_c{suffix}.json").write_text(json.dumps(report, indent=2, default=str))
    print(f"\n{'='*84}\nSUMMARY\n{'='*84}")
    for m in report["models"]:
        c = m["cost"]
        print(f"  {m['model']:18} {m['passed']}/{m['total']} pass  "
              f"grain-trap={'PASS' if m['grain_trap_pass'] else 'FAIL'}  "
              f"${c['usd_per_op']:.5f}/op (in {c['avg_in_tok']:.0f} / out {c['avg_out_tok']:.0f} tok)")
    print("\nNAIVE DIAGNOSTIC (no guard — does the model get grain/CPUE right on its own?):")
    for name, d in report["naive_diagnostic"].items():
        print(f"  {name:18} {d}")
    print(f"\nwrote {RESULTS / f'mode_c{suffix}.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
