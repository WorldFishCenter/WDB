"""The unified answer contract (three-mode architecture doc §6) — the shape A/B/C
results assemble into.

This is the **router's** view of §6: one :class:`RouterAnswer` that merges the
fragments each mode returned into a single response — ``claims`` (each carrying
its own ``mode`` tag and ≥1 citation), a typed ``associations`` payload (graph
edges, from Mode A and Mode B), ``figures`` (Mode C only), and an ``unanswered``
list for any part no mode could ground.

Design choice (faithful reuse, not flattening): the merged ``claims`` hold the
**native** ``Claim`` objects each mode produced — ``mode_b.contract.Claim`` (its
citation IS the passage span + quote + nodes), ``mode_c.contract.Claim`` (its
citation IS the SQL + result rows), and :class:`router.mode_a.Claim` (its citation
IS the graph edge). They share one duck-typed interface — ``.text``, ``.mode``,
``.citations`` — so the router never collapses a mode's citation richness; it
concatenates and renders per ``claim.mode``. The §6 invariants the router relies
on are already enforced inside each mode (rule 1: no claim without a citation;
rule 4: ungrounded parts go to ``unanswered``, never back-filled) — so merging is
concatenation + de-duplication, nothing more.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class Route:
    """One routing decision: which mode, and the signal that selected it (§5 layer 1)."""

    mode: str        # "A" | "B" | "C"
    reason: str      # the matched signal / why this mode fired — for transparency


@dataclass
class RouterAnswer:
    """The unified §6 answer a question's routed modes compose into.

    ``claims`` are heterogeneous native ``Claim`` objects (Mode A/B/C); each has
    ``.text``, ``.mode`` and a non-empty ``.citations`` tuple. ``unanswered`` is
    every part a dispatched mode could not ground — stated, never hidden (§6 r4).
    """

    question: str
    routes: list[Route] = field(default_factory=list)
    claims: list = field(default_factory=list)         # native A/B/C Claim objects
    associations: list = field(default_factory=list)   # graph edges (Mode A + Mode B)
    figures: list = field(default_factory=list)        # Mode C only
    unanswered: list[str] = field(default_factory=list)

    @property
    def answered(self) -> bool:
        return bool(self.claims) or bool(self.figures)

    @property
    def modes_fired(self) -> list[str]:
        return sorted({r.mode for r in self.routes})

    @property
    def modes_grounded(self) -> list[str]:
        """Modes that actually contributed a claim or figure (not just routed to)."""
        m = {c.mode for c in self.claims}
        if self.figures:
            m.add("C")
        return sorted(m)


def _edge_key(e: dict) -> tuple:
    return (e.get("source"), e.get("relation"), e.get("target"))


def add_associations(answer: RouterAnswer, edges: list) -> None:
    """Merge graph edges into ``answer.associations``, de-duplicated by triple."""
    seen = {_edge_key(e) for e in answer.associations}
    for e in edges:
        k = _edge_key(e)
        if k not in seen:
            seen.add(k)
            answer.associations.append(e)
