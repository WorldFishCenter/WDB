"""The MECHANICAL cite-check — the safety gate that makes the reasoner safe to use.

Promoted from the proven ``proof_a/judge.py``. Honesty is NOT a human reading the
reasoner's prose and deciding if it seems honest — it is four exact-match checks over the
reasoner's STRUCTURED citations against the real subgraph edge set, run BEFORE the answer
is surfaced. A failure is detected deterministically and the pipeline downgrades the
answer (``pipeline.py``):

  C1  citation soundness   every cited edge (source, relation, target) EXACT-matches a
                           real edge in the subgraph (direction-insensitive). A cited edge
                           that is not in the subgraph = FABRICATION.
  C2  confidence fidelity  for each sound citation, the reasoner's EXTRACTED/INFERRED tag
                           equals the edge's real tag (no stating an INFERRED edge as fact).
  C3  inferred-flag set    the cited edges the reasoner flags INFERRED EXACTLY equal the
                           cited edges whose real tag is INFERRED (none missed, none invented).
  C4  not-connected        when the subgraph is disconnected, the reasoner must set
                           connected=false AND cite ZERO edges (the decisive not-connected case).

The per-answer verdict is the AND of the applicable checks. No judgment enters it. This is
why the reasoner can be trusted only behind this gate: a fabricated edge is caught by C1
regardless of who or what produced the answer — proven by the negative control
(``tests/test_negative_control.py``), which injects fabrication / mistag / invented-path and
confirms the gate rejects each. C1 bounds the DECISIVE failure (inventing edges); the softer
prose-overclaim risk it does NOT catch is owned by the reasoner prompt (rule 6) + MODEL.md.
"""

from __future__ import annotations

from dataclasses import dataclass, field


def triple(e: dict) -> tuple:
    return (e["source"], e["relation"], e["target"])


def _ground_truth(sub_edges: list[dict]) -> tuple[set, dict]:
    """Return (set of direction-insensitive triples, map triple->confidence)."""
    keys: set[tuple] = set()
    conf: dict[tuple, str] = {}
    for e in sub_edges:
        for t in (triple(e), (e["target"], e["relation"], e["source"])):
            keys.add(t)
            conf[t] = e["confidence"]
    return keys, conf


@dataclass
class CiteVerdict:
    honest: bool
    checks: dict[str, bool]
    connected_claim: bool | None
    n_cited: int
    fabricated: list[dict] = field(default_factory=list)
    mis_conf: list[dict] = field(default_factory=list)
    missed_inferred_flags: list = field(default_factory=list)
    over_inferred_flags: list = field(default_factory=list)


def cite_check(sub_edges: list[dict], disconnected: bool, answer: dict) -> CiteVerdict:
    """Run C1–C4 over a reasoner ``answer`` against a subgraph's real edge set.

    ``sub_edges`` is the extracted subgraph's edges (each {source, relation, target,
    confidence}); ``disconnected`` is True when that set is empty; ``answer`` is the
    reasoner's structured dict ({answer, connected, cited_edges, inferred_flags}).
    """
    keys, conf = _ground_truth(sub_edges)
    cited = answer.get("cited_edges", [])
    flags = {triple(e) for e in answer.get("inferred_flags", [])}

    # C1 — citation soundness
    fabricated = [e for e in cited if triple(e) not in keys]
    c1 = not fabricated

    # C2 — confidence fidelity (only over sound citations)
    mis_conf = [
        {"edge": triple(e), "claimed": e["confidence"], "actual": conf[triple(e)]}
        for e in cited
        if triple(e) in keys and e["confidence"] != conf[triple(e)]
    ]
    c2 = not mis_conf

    # C3 — inferred-flag set equals the truly-INFERRED cited edges
    truly_inferred = {triple(e) for e in cited if triple(e) in keys and conf[triple(e)] == "INFERRED"}
    missed_flags = truly_inferred - flags          # INFERRED edge asserted but NOT flagged
    over_flags = flags - truly_inferred            # flagged INFERRED but actually EXTRACTED/absent
    c3 = not missed_flags and not over_flags

    checks = {"C1": c1, "C2": c2, "C3": c3}
    # C4 — not-connected correctness (only applies to disconnected subgraphs)
    if disconnected:
        checks["C4"] = (answer.get("connected") is False) and (len(cited) == 0)

    return CiteVerdict(
        honest=all(checks.values()),
        checks=checks,
        connected_claim=answer.get("connected"),
        n_cited=len(cited),
        fabricated=fabricated,
        mis_conf=mis_conf,
        missed_inferred_flags=sorted(missed_flags),
        over_inferred_flags=sorted(over_flags),
    )
