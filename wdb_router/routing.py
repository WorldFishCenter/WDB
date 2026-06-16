"""Layer-1 intent routing (three-mode architecture doc §5) — the keyword/signal pass.

This is the **routing** half of the router's seam: :func:`route` decides *which* modes a
question goes to and returns a :class:`RoutingDecision`. It takes **only the question** —
no backends, no mode objects — so a routing decision is, by signature, made independently
of dispatch. :mod:`wdb_router.composition` consumes the decision and calls the modes; the
two never blur. That boundary is what lets a future agentic router re-derive the decision
from a prior mode's answer (multi-step) without touching the modes or the contract — and
why an LLM-assisted classifier, if the keyword pass ever proves insufficient, can slot in
behind this same ``question -> RoutingDecision`` signature with nothing downstream changing.

The pass itself is deliberately transparent: a question is scanned for the §5 signals and
routed to **every** mode whose signal fires, each route recording the exact signal it
matched (so the composition is auditable — you can see *why* each mode ran).

Routing rules (§5 table):

* **A — graph / enumeration**: "what/which/list/related/connected", an entity + a relation
  ("what projects operate in …", "which gear types in …").
* **B — passage synthesis**: open synthesis — "impact/effect/affect/gaps/why/how does …".
* **C — structured query**: a quantitative *operator* — "average/total/how many/count/
  per/compare/trend/rank" (an operator, not merely a quantitative noun: "catch survey
  data" alone is not Mode C; "average catch" is).

Blended questions match more than one mode and fan out (§5: "compose, don't collapse"). A
question that matches **no** signal is treated as ambiguous and fanned out to all three —
each mode's own grounding mechanism then decides whether it can answer, and anything none
can ground is stated in ``unanswered`` (§6 r4). We never silently pick a single mode for an
ambiguous question.
"""

from __future__ import annotations

import re

from .contract import Route, RoutingDecision

# Each entry: (compiled-ready pattern, human label for the reason string). Order within a
# mode is "most specific first" so the reported reason is the strongest signal that fired.
_A_PATTERNS = [
    (r"\blist\b", "list"),
    (r"\benumerate\b", "enumerate"),
    (r"\bwhich\b", "which"),
    (r"\brelated to\b|\brelationship\b|\bconnect(?:ed|s|ion)?\b|\blinked? to\b",
     "relationship/connection"),
    (r"\bwhat\b.*\b(project|projects|dataset|datasets|initiative|initiatives|gear|"
     r"species|paper|papers|study|studies|partner|partners|site|sites|region|"
     r"regions|county|counties)\b", "what <entity>"),
    (r"\b(operate|operates|works? in|present in)\b", "operates/works-in"),
]

_B_PATTERNS = [
    (r"\bimpact\b|\beffect\b|\baffect(?:s|ed|ing)?\b", "impact/effect"),
    (r"\bgaps?\b", "gaps"),
    (r"\bwhy\b", "why"),
    (r"\bhow (?:does|do|did|is|are|to|can)\b", "how does/do"),
    (r"\b(explain|describe|overview|summar(?:y|ise|ize)|challenges?|lessons?|"
     r"findings?|insights?|approach|methodolog)", "explain/describe/synthesis"),
]

_C_PATTERNS = [
    (r"\baverage\b|\bmean\b|\bavg\b|\bmedian\b", "average/mean"),
    (r"\btotal\b|\bsum\b", "total/sum"),
    (r"\bhow many\b|\bcount\b|\bnumber of\b", "count"),
    (r"\bcompare\b|\bcomparison\b|\bversus\b|\bvs\b", "compare"),
    (r"\btrend\b|\bover time\b|\bby (?:county|region|district|month|year|species|gear)\b",
     "trend/grouped"),
    (r"\brank(?:ing|ed)?\b|\bhighest\b|\blowest\b|\bmost\b|\bleast\b", "ranking"),
    (r"\bper (?:trip|fisher|day|hour|capita|year)\b|\bcpue\b", "per-unit/CPUE"),
]

_MODES = [("A", _A_PATTERNS), ("B", _B_PATTERNS), ("C", _C_PATTERNS)]


def _first_match(question: str, patterns) -> str | None:
    for rx, label in patterns:
        if re.search(rx, question):
            return label
    return None


def route(question: str) -> RoutingDecision:
    """Classify ``question`` into the modes to dispatch (§5 layer 1).

    Returns a :class:`RoutingDecision` with one :class:`Route` per mode whose signal fires
    (≥1 always). Multiple matches → a blended fan-out. No match → ambiguous fan-out to all
    three (never a silent single pick). Pure: depends only on the question text.
    """
    q = question.lower()
    routes: list[Route] = []
    for mode, patterns in _MODES:
        label = _first_match(q, patterns)
        if label is not None:
            routes.append(Route(mode=mode, reason=f"signal: {label}"))

    if not routes:
        routes = [Route(mode=m, reason="ambiguous — no clear signal; fanned out to all modes")
                  for m in ("A", "B", "C")]
    return RoutingDecision(routes=tuple(routes))
