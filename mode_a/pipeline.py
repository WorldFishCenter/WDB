"""The Mode-A pipeline: route → extract → (enumerate | reason → CITE-CHECK) → contract.

This is the standalone module the eventual router/UI will call. It does not route across
modes, serve, or render — it answers relational/enumeration questions over the graph and
declines cleanly otherwise.

The reasoning path is gated: the reasoner sees ONLY the serialized subgraph, returns
structured citations, and the mechanical cite-check (``citecheck.py``) runs BEFORE the
answer is surfaced. A failed check NEVER surfaces an unverified reasoned answer — it
**downgrades** to cheap enumeration on the anchor, or to "not available" if even that is
empty. This wrapper is the entire reason the LLM is safe to use here (``proof_a/FINDINGS.md``).
"""

from __future__ import annotations

from wdb_contract import UnansweredCode

from . import contract, extract, route
from .citecheck import cite_check
from .contract import Answer
from .reasoner import NoRecordedAnswer, Reasoner


def _extract_for(r: route.Route, g: extract.Graph) -> extract.SubGraph:
    if r.extraction == "neighborhood":
        return extract.neighborhood(g, r.entities[0])
    if r.extraction == "bridges":
        return extract.bridges(g, r.entities[0])
    return extract.relate(g, r.entities[0], r.entities[1])


def _downgrade(question: str, r: route.Route, g: extract.Graph, why: str,
               code: UnansweredCode = UnansweredCode.CITE_CHECK_DOWNGRADE) -> Answer:
    """Failed cite-check (or no offline answer): downgrade to enumeration, else not-available."""
    sub = extract.neighborhood(g, r.entities[0])
    sub.question = question
    if sub.edges:
        ans = contract.from_enumeration(question, sub, g)
        ans.path = f"reasoning→enumeration (downgraded: {why})"
        return ans
    return contract.refusal(question, f"not available (downgraded: {why})", code)


def answer_question(question: str, reasoner: Reasoner, g: extract.Graph | None = None) -> Answer:
    """Answer one Mode-A question. ``reasoner`` is only consulted on the reasoning path."""
    if g is None:
        g = extract.get_graph()

    r = route.route(question, g)
    if r.path == "unresolved":
        return contract.refusal(question, "no graph entity in this question matched a committed node",
                                UnansweredCode.NO_ENTITY_MATCH)

    sub = _extract_for(r, g)
    sub.question = question

    # --- cheap deterministic enumeration path -------------------------------- #
    if r.path == "enumeration":
        if not sub.edges:
            return contract.refusal(question, "graph has the entity but records no relationship for it",
                                    UnansweredCode.NO_RELATIONSHIP)
        return contract.from_enumeration(question, sub, g)

    # --- reasoning path ------------------------------------------------------ #
    if sub.disconnected:
        # deterministic, honest negative — no model needed
        return contract.not_connected(question, sub, g)

    try:
        ans = reasoner.reason(sub.serialize())
    except NoRecordedAnswer:
        return _downgrade(question, r, g, "reasoning unavailable offline",
                          UnansweredCode.NO_RECORDED_REPLAY)

    verdict = cite_check(sub.edges, sub.disconnected, ans)
    if not verdict.honest:
        failed = ",".join(k for k, ok in verdict.checks.items() if not ok)
        return _downgrade(question, r, g, f"cite-check failed [{failed}]")

    return contract.from_reasoning(question, sub, ans, g)
