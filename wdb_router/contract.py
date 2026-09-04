"""The routing-seam decision type, and the router's view of the §6 contract.

Two things live here, deliberately together because they bound the router's seam:

* :class:`RoutingDecision` — the output of **routing** (§5 layer 1) and the input to
  **composition**. It names *which* modes to dispatch and the signal that selected each.
  It is the seam's data object: a future agentic router would re-derive one of these at
  each step from a prior mode's answer; today the dispatcher derives it **once**. It is
  deliberately minimal — just the routes, no agent state — so "leave room for an agent"
  stays a clean boundary, not speculative machinery.

* :class:`RouterAnswer` — a :class:`wdb_contract.Answer` plus the question it answers and the
  routes that were fired. It is **not** a re-declaration of the contract: it inherits every
  field, so a field added to the shared ``Answer`` cannot be dropped here by omission. That is
  precisely what used to happen — this class had its own field list and its own ``answered``
  rule, so Mode A's ``connected`` verdict and Mode C's ``disambiguation`` candidates died at
  the merge and a verified negative was re-rendered as a coverage refusal.

Faithful reuse, not flattening: the merged ``claims`` hold the **native** ``Claim`` objects
each mode produced — each with its own citation shape (Mode A's IS the graph edge, Mode B's IS
the passage span + quote + nodes, Mode C's IS the SQL + result rows). They now share one
declared shape (``wdb_contract.Claim`` with a ``mode`` tag), so the router never collapses a
mode's citation richness; it concatenates and renders per ``claim.mode``. The §6 invariants are
enforced in the contract itself (rule 1: ``Claim`` cannot be built without a citation; rule 4:
ungrounded parts go to ``unanswered``), so merging is concatenation + de-duplication.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from wdb_contract import Answer, Unanswered, UnansweredCode, Verdict, add_associations, merge

__all__ = [
    "Route", "RoutingDecision", "RouterAnswer",
    "Answer", "Unanswered", "UnansweredCode", "Verdict", "add_associations", "merge",
]


@dataclass(frozen=True)
class Route:
    """One routing decision for a single mode, and the signal that selected it (§5 layer 1)."""

    mode: str        # "A" | "B" | "C"
    reason: str      # the matched signal / why this mode fired — for transparency


@dataclass(frozen=True)
class RoutingDecision:
    """What routing decides and composition consumes — the seam's data object.

    Holds the per-mode :class:`Route`s (each with the signal that selected it). ``modes``
    is the de-duplicated mode set, in first-seen order. Frozen and backend-free: producing
    one needs only the question (see :func:`wdb_router.routing.route`), which is exactly what
    keeps routing decisions independent of — and testable apart from — composition.
    """

    routes: tuple[Route, ...]

    @property
    def modes(self) -> list[str]:
        out: list[str] = []
        for r in self.routes:
            if r.mode not in out:
                out.append(r.mode)
        return out


@dataclass
class RouterAnswer(Answer):
    """The unified §6 answer a question's routed modes compose into.

    Inherits ``claims`` / ``associations`` / ``figures`` / ``unanswered`` / ``negative`` /
    ``path`` — and therefore ``verdict`` and ``answered`` — from :class:`wdb_contract.Answer`.
    """

    question: str = ""
    routes: list[Route] = field(default_factory=list)

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
