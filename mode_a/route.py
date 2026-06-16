"""Shape routing WITHIN Mode A — direct enumeration vs LLM-reasoning-over-subgraph.

This is NOT the cross-mode router (``router/intent.py`` decides A vs B vs C). Once a
question is Mode A, this picks the *path* by question shape, per the proof's recommendation
(``proof_a/FINDINGS.md`` "the constrained middle"):

* **direct** "what is X connected to" / "list the X of Y" → cheap deterministic
  ENUMERATION over a 1-hop ``neighborhood`` (no model). The baseline is already enough here.
* **how/why do X and Y relate** → REASONING over a ``relate`` subgraph.
* **which initiatives share … with X** → REASONING over a ``bridges`` subgraph.

Entity resolution is the known shared-with-Mode-C limitation (``extract.Graph.resolve``):
we detect the question's entities by matching the known canonical names / node norm_labels
that appear in it. A question naming no known entity routes to ``unresolved`` → the pipeline
returns "not available" rather than guessing.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from .extract import _ALIASES, Graph

# direct-enumeration signals: "what is X connected to", "list …", "enumerate …",
# "what <entity-type> …". A single entity + one of these → the cheap path.
_ENUMERATION_SIGNAL = re.compile(
    r"\bconnected to\b|\blist\b|\benumerate\b|\bwhat (?:is|are|does)\b.*\b(connect|link|relate)",
)
# "which initiatives share … with X" → bridges (reasoning).
_BRIDGE_SIGNAL = re.compile(r"\bwhich\b.*\bshare(?:s|d)?\b|\bshare(?:s|d)?\b.*\bwith\b")
# how/why/related-to → relational reasoning between two entities.
_RELATIONAL_SIGNAL = re.compile(
    r"\bhow\b|\bwhy\b|\brelate(?:s|d)?\b|\brelationship\b|\bconnect(?:ed|s|ion)?\b|\blinked? to\b",
)


@dataclass
class Route:
    path: str                                 # "enumeration" | "reasoning" | "unresolved"
    extraction: str = ""                      # "neighborhood" | "relate" | "bridges"
    entities: list[str] = field(default_factory=list)   # resolved node ids, in question order
    reason: str = ""


def find_entities(question: str, g: Graph) -> list[str]:
    """The known entities the question names, as resolved node ids in order of appearance.

    Matches the canonical alias names plus every node ``norm_label`` (≥4 chars) as a
    whole-word/phrase in the question; longest candidate first so "wio data harmonization"
    wins over "data harmonization". Deduplicated by resolved id, ordered by first hit.
    """
    q = question.lower()
    candidates: dict[str, str] = dict(_ALIASES)  # name -> id
    for n in g.nodes:
        nl = (n.get("norm_label") or "").strip().lower()
        if len(nl) >= 4:
            candidates.setdefault(nl, n["id"])

    hits: list[tuple[int, str]] = []  # (position, id)
    seen_ids: set[str] = set()
    for name in sorted(candidates, key=len, reverse=True):
        m = re.search(r"\b" + re.escape(name) + r"\b", q)
        if m:
            nid = candidates[name]
            if nid not in seen_ids:
                seen_ids.add(nid)
                hits.append((m.start(), nid))
    return [nid for _pos, nid in sorted(hits)]


def route(question: str, g: Graph) -> Route:
    """Classify the question's shape into an extraction + path. Auditable, ordered rules."""
    q = question.lower()
    entities = find_entities(question, g)

    if not entities:
        return Route(path="unresolved",
                     reason="no known graph entity named in the question")

    bridge = bool(_BRIDGE_SIGNAL.search(q))
    relational = bool(_RELATIONAL_SIGNAL.search(q))
    enumeration = bool(_ENUMERATION_SIGNAL.search(q))

    # 1. "which initiatives share … with X" → bridges (reasoning over one anchor)
    if bridge:
        return Route(path="reasoning", extraction="bridges", entities=[entities[0]],
                     reason="signal: which initiatives share … with <entity>")

    # 2. two named entities + a relational signal → relate (reasoning)
    if len(entities) >= 2 and relational:
        return Route(path="reasoning", extraction="relate", entities=entities[:2],
                     reason="signal: how/why/related-to between two entities")

    # 3. one entity + a direct enumeration signal → cheap neighborhood enumeration
    if len(entities) == 1 and enumeration:
        return Route(path="enumeration", extraction="neighborhood", entities=[entities[0]],
                     reason="signal: direct 'what is X connected to' / 'list …'")

    # 4. fallbacks: two entities → relate (reason); one entity → enumerate its neighborhood
    if len(entities) >= 2:
        return Route(path="reasoning", extraction="relate", entities=entities[:2],
                     reason="fallback: two entities present → relate")
    return Route(path="enumeration", extraction="neighborhood", entities=[entities[0]],
                 reason="fallback: single entity → enumerate neighborhood")
