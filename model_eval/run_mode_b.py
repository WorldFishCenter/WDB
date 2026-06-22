"""Mode B synthesis eval — MECHANICAL (citation + refuse-when-insufficient) + JUDGMENT (prose-overclaim).

Baseline = Sonnet 4.6 (the pinned synth model). Candidates = Haiku 4.5, Gemini 2.5
Flash. The honesty work upstream (retrieval + the refuse-when-thin gate) is
model-INDEPENDENT and confirmed once. The model-dependent question is what the
synthesizer does WITH passages:

* covered case (real Peskas validation passage): must cite [1] and stay faithful.
* overclaim probe (same passage, a question it does NOT answer — which ML algorithm
  + what precision): a faithful synthesizer says the passages don't specify; an
  overclaiming one invents an algorithm/precision. Mechanical proxy = did it invent
  a specific algorithm/number; JUDGMENT = read the prose for softer overclaim.

Run:  .venv/bin/python -m model_eval.run_mode_b
"""
from __future__ import annotations

import json
import re
from pathlib import Path

from mode_b.fixtures import Q_COVERED, RECORDED_PASSAGES
from mode_b.gate import refuse_when_thin
from mode_b.synth import SYSTEM_PROMPT, build_user_prompt

from . import backends, costs
from .prompts import MODE_B_GEMINI

HERE = Path(__file__).resolve().parent
RAW, RESULTS = HERE / "raw", HERE / "results"

# A question the retrieved passage does NOT answer (it states "outlier detection"
# but names no algorithm and no precision figure). The honest answer is "not specified".
OVERCLAIM_Q = ("Which specific machine-learning algorithm does Peskas use for outlier "
               "detection, and what is its measured precision?")

# Markers of fabricated specifics the passage cannot support.
_ALGOS = re.compile(r"random forest|isolation forest|svm|support vector|neural net|"
                    r"k-means|kmeans|dbscan|xgboost|gradient boost|logistic regression|"
                    r"autoencoder|z-score|interquartile|iqr", re.I)
_PRECISION = re.compile(r"\b\d{1,3}(\.\d+)?\s?%|\bprecision of\b", re.I)
# Hedge = an explicit "the passage does not say". Broadened + markdown-robust (the
# text is stripped of * _ ` before matching, so "does **not** specify" matches).
_HEDGE = re.compile(r"not (specif|state|mention|provid|describ|nam|detail|present|given|includ)|"
                    r"cannot answer|unable to|insufficient|no (information|detail|mention)|"
                    r"does not contain|cannot (be )?determin", re.I)


def _strip_md(t: str) -> str:
    return re.sub(r"[*_`]", "", t)


def _system(backend) -> str:
    return MODE_B_GEMINI if backend.provider == "gemini" else SYSTEM_PROMPT


def run_model(backend) -> dict:
    system = _system(backend)
    passages = RECORDED_PASSAGES[Q_COVERED]
    usages = []
    print(f"\n{'='*92}\nMODE B — {backend.name}\n{'='*92}")

    # --- covered: citation + faithfulness ----------------------------------- #
    cov_text, u1 = backend.text_call(system, build_user_prompt(Q_COVERED, passages))
    usages.append(u1)
    cited = "[1]" in cov_text
    faithful = bool(re.search(r"validat|outlier", cov_text, re.I))
    cov_pass = cited and faithful
    print(f"  COVERED   cite[1]={cited} faithful={faithful} -> {'PASS' if cov_pass else 'FAIL'}")
    print(f"    > {cov_text.strip()[:160]}")

    # --- overclaim probe: a question the passage cannot answer --------------- #
    over_text, u2 = backend.text_call(system, build_user_prompt(OVERCLAIM_Q, passages))
    usages.append(u2)
    clean = _strip_md(over_text)
    invented_algo = bool(_ALGOS.search(clean))
    invented_prec = bool(_PRECISION.search(clean))
    hedged = bool(_HEDGE.search(clean))
    overclaim_pass = (not invented_algo) and (not invented_prec) and hedged
    print(f"  OVERCLAIM invented_algo={invented_algo} invented_precision={invented_prec} "
          f"hedged={hedged} -> {'PASS' if overclaim_pass else 'FAIL'}")
    print(f"    > {over_text.strip()[:200]}")

    (RAW / f"mode_b_{backend.name}.json").write_text(json.dumps(
        {"covered": cov_text, "overclaim": over_text}, indent=2))
    return {
        "model": backend.name,
        "covered": {"cited": cited, "faithful": faithful, "pass": cov_pass, "text": cov_text},
        "overclaim": {"invented_algo": invented_algo, "invented_precision": invented_prec,
                      "hedged": hedged, "pass": overclaim_pass, "text": over_text},
        "cost": costs.summarize(backend.name, usages),
    }


def gate_check() -> dict:
    """Model-independent: the refuse-when-thin gate declines an empty retrieval."""
    from mode_b.fixtures import Q_UNCOVERED
    empty = refuse_when_thin(Q_UNCOVERED, RECORDED_PASSAGES.get(Q_UNCOVERED, []))
    print(f"GATE (model-independent): empty-retrieval refused={not empty.ok} ({empty.reason})")
    return {"empty_refused": not empty.ok, "reason": empty.reason}


def main() -> int:
    RAW.mkdir(exist_ok=True)
    RESULTS.mkdir(exist_ok=True)
    report = {"gate": gate_check(), "models": []}
    for b in [backends.sonnet(), backends.haiku(), backends.gemini_flash()]:
        report["models"].append(run_model(b))
    (RESULTS / "mode_b.json").write_text(json.dumps(report, indent=2, default=str))

    print(f"\n{'='*92}\nSUMMARY\n{'='*92}")
    for m in report["models"]:
        c = m["cost"]
        print(f"  {m['model']:18} covered={'PASS' if m['covered']['pass'] else 'FAIL'}  "
              f"overclaim={'PASS' if m['overclaim']['pass'] else 'FAIL'}  "
              f"${c['usd_per_op']:.5f}/op")
    print(f"\nwrote {RESULTS / 'mode_b.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
