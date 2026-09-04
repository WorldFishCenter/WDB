"""Mode A's half of the §6 answer contract: turning a subgraph into grounded claims.

The contract *shape* (``Citation``, ``Claim``, ``Answer``, ``Verdict``, ``Unanswered``) is
declared once in :mod:`wdb_contract`; this module holds only what is Mode-A specific — how a
graph edge becomes a citation, and the three ways a Mode-A answer is built.

Mode A's defining rule (§6, §7): a claim is grounded in committed, **stated** graph edges — it
prefers ``EXTRACTED`` and flags ``INFERRED``, and when no edge exists it returns nothing rather
than a guess. Each citation's locator is the edge triple (with its confidence tag); on the
reasoning path every citation has already passed the mechanical cite-check (``citecheck.py``)
before assembly.

Three ways in:
  * :func:`from_enumeration` — one claim per incident edge (the cheap deterministic path).
  * :func:`from_reasoning`   — one claim = the reasoned prose + structured citations to the
    real edges it cited (gated).
  * :func:`not_connected`    — a **verified negative**: we checked and the answer is "no".
    This is a correct answer, not a refusal, and it carries ``Verdict.VERIFIED_NEGATIVE`` all
    the way to the UI. Before the shared contract existed the router dropped it and the UI
    rendered it as "the knowledge base doesn't cover this".
"""

from __future__ import annotations

from wdb_contract import (
    Answer,
    CitationA as Citation,
    Claim,
    Unanswered,
    UnansweredCode,
    Verdict,
    add_associations,
)

from .citecheck import triple
from .extract import Graph, SubGraph

__all__ = [
    "Answer", "Citation", "Claim", "Unanswered", "UnansweredCode", "Verdict",
    "add_associations", "refusal", "not_connected", "from_enumeration", "from_reasoning",
]


def refusal(question: str, reason: str,
            code: UnansweredCode = UnansweredCode.UNSPECIFIED) -> Answer:
    """§6 rule 4: state what Mode A could not ground, never guess (``code`` is what tests pin)."""
    return Answer(unanswered=[
        Unanswered(part=question, mode="A", code=code, detail=reason)
    ])


def _cite_from_edge(e: dict) -> Citation:
    return Citation(
        source_file=e.get("source_file", ""),
        note=e.get("source_location") or "",
        locator=f"{e['source']} --{e.get('relation', '?')}--> {e['target']}",
        confidence=e.get("confidence", ""),
    )


def from_enumeration(question: str, sub: SubGraph, g: Graph) -> Answer:
    """The cheap path: one claim per edge incident to the anchor, EXTRACTED first."""
    claims: list[Claim] = []
    for e in sub.edges:
        s_lbl, t_lbl = g.label(e["source"]), g.label(e["target"])
        flag = "  [INFERRED — discount]" if e.get("confidence") == "INFERRED" else ""
        claims.append(Claim(
            text=f"{s_lbl} —{e.get('relation', '?')}→ {t_lbl}{flag}",
            citations=(_cite_from_edge(e),),
            mode="A",
        ))
    # §7: prefer EXTRACTED — list the stated facts before the inferred guesses.
    claims.sort(key=lambda c: 0 if c.citations[0].confidence == "EXTRACTED" else 1)
    return Answer(claims=claims, associations=list(sub.edges), path="enumeration")


def not_connected(question: str, sub: SubGraph, g: Graph) -> Answer:
    """A verified not-connected verdict — stated plainly, never a fabricated link (§7).

    ``negative=True`` is what makes this a ``VERIFIED_NEGATIVE`` rather than an ungrounded
    refusal: the graph was consulted and it records no connection. That is the answer.
    """
    a, b = (sub.anchors + [None, None])[:2]
    pair = f"{g.label(a)} and {g.label(b)}" if b else g.label(a)
    return Answer(
        negative=True,
        associations=[],
        unanswered=[Unanswered(
            part=question,
            mode="A",
            code=UnansweredCode.NOT_CONNECTED,
            detail=f"the graph records no connection between {pair} "
                   f"(no direct edge, no ≤2-hop path).",
        )],
        path="reasoning",
    )


def from_reasoning(question: str, sub: SubGraph, answer: dict, g: Graph) -> Answer:
    """The gated reasoning path: the reasoned prose + structured citations to the real edges.

    Called only AFTER the mechanical cite-check passed, so every ``cited_edge`` is a real
    subgraph edge; we look each one up to attach its source_file / source_location.

    Note the cite-check's C1 passes *vacuously* when the reasoner cited nothing at all
    (``citecheck.py``: an empty ``cited_edges`` list has no fabrications in it), so a reasoned
    answer can arrive here with no citations to attach. §6 rule 1 forbids emitting that, so it
    downgrades to a stated refusal rather than surfacing un-sourced prose.
    """
    by_triple: dict[tuple, dict] = {}
    for e in sub.edges:
        by_triple[triple(e)] = e
        by_triple[(e["target"], e["relation"], e["source"])] = e

    citations = tuple(
        _cite_from_edge(by_triple[triple(c)])
        for c in answer.get("cited_edges", []) if triple(c) in by_triple
    )
    if not citations:
        return refusal(
            question,
            "not available (reasoned answer cited no verifiable edge)",
            UnansweredCode.CITE_CHECK_DOWNGRADE,
        )

    claim = Claim(text=answer.get("answer", "").strip(), citations=citations, mode="A")
    return Answer(
        claims=[claim],
        associations=list(sub.edges),
        negative=answer.get("connected") is False,
        path="reasoning",
    )
