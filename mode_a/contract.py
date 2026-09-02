"""The answer contract (three-mode architecture doc §6), as far as Mode A needs.

A grounded Mode-A answer is a list of ``Claim``s (all ``mode="A"``), a typed
``associations`` payload (the subgraph edges), and an ``unanswered`` list for anything no
mode could ground. Mode A's defining rule (§6, §7): a claim is grounded in committed,
**stated** graph edges — it prefers ``EXTRACTED`` and flags ``INFERRED``, and when no edge
exists it returns nothing rather than a guess. Each ``Citation``'s locator is the edge
triple (with its confidence tag); on the reasoning path every citation has already passed
the mechanical cite-check (``citecheck.py``) before assembly.

Both paths land here:
  * :func:`from_enumeration` — one claim per incident edge (the cheap deterministic path).
  * :func:`from_reasoning`   — one claim = the reasoned prose + structured citations to the
    real edges it cited (gated). A verified not-connected verdict is :func:`not_connected`.
A refusal / "not available" is an ``Answer`` with no claims and the question in
``unanswered`` (§6 rule 4 — stated, never silently dropped).
"""

from __future__ import annotations

from dataclasses import dataclass, field

from .citecheck import triple
from .extract import Graph, SubGraph


@dataclass(frozen=True)
class Citation:
    """A Mode-A citation: the graph edge that grounds the relationship (§6, A locator)."""

    source_file: str       # the companion note / doc that *stated* the edge (the join key, #4)
    note: str              # source_location label, e.g. "Validation; Methods 2.3" ("" if none)
    locator: str           # the edge triple "src --relation--> tgt"
    confidence: str        # EXTRACTED | INFERRED (§7: prefer EXTRACTED, flag INFERRED)


@dataclass(frozen=True)
class Claim:
    text: str
    citations: tuple[Citation, ...]
    mode: str = "A"


@dataclass
class Answer:
    """Mode A's slice of the §6 contract (mirrors mode_b/mode_c Answer shape)."""

    claims: list[Claim] = field(default_factory=list)
    associations: list = field(default_factory=list)     # the subgraph edges (Mode-A payload)
    unanswered: list[str] = field(default_factory=list)
    connected: bool | None = None                        # None for enumeration; bool for relational
    path: str = ""                                        # which path produced this answer

    @property
    def answered(self) -> bool:
        # a verified not-connected verdict IS a correct answer (the answer is "no")
        return bool(self.claims) or self.connected is False


def refusal(question: str, reason: str) -> Answer:
    return Answer(unanswered=[f"{question} — {reason}"])


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
        ))
    # §7: prefer EXTRACTED — list the stated facts before the inferred guesses.
    claims.sort(key=lambda c: 0 if c.citations[0].confidence == "EXTRACTED" else 1)
    return Answer(claims=claims, associations=list(sub.edges), path="enumeration")


def not_connected(question: str, sub: SubGraph, g: Graph) -> Answer:
    """A verified not-connected verdict — stated plainly, never a fabricated link (§7)."""
    a, b = (sub.anchors + [None, None])[:2]
    pair = f"{g.label(a)} and {g.label(b)}" if b else g.label(a)
    return Answer(
        connected=False,
        associations=[],
        unanswered=[f"{question} — the graph records no connection between {pair} "
                    f"(no direct edge, no ≤2-hop path)."],
        path="reasoning",
    )


def from_reasoning(question: str, sub: SubGraph, answer: dict, g: Graph) -> Answer:
    """The gated reasoning path: the reasoned prose + structured citations to the real edges.

    Called only AFTER the mechanical cite-check passed, so every ``cited_edge`` is a real
    subgraph edge; we look each one up to attach its source_file / source_location.
    """
    by_triple: dict[tuple, dict] = {}
    for e in sub.edges:
        by_triple[triple(e)] = e
        by_triple[(e["target"], e["relation"], e["source"])] = e

    citations = tuple(
        _cite_from_edge(by_triple[triple(c)])
        for c in answer.get("cited_edges", []) if triple(c) in by_triple
    )
    claim = Claim(text=answer.get("answer", "").strip(), citations=citations)
    return Answer(
        claims=[claim],
        associations=list(sub.edges),
        connected=answer.get("connected"),
        path="reasoning",
    )
