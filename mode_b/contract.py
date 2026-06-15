"""The answer contract (three-mode architecture doc §6), as far as Mode B needs.

A grounded answer is a list of ``Claim``s (here all ``mode="B"``) plus a typed
``associations`` payload and an ``unanswered`` list. The defining Mode-B rule
(§6): a ``Claim``'s citation is the **passage span + civ-kb location + verbatim
quote + the matching graph node(s)** — synthesized prose, never un-sourced. Every
claim carries ≥1 citation or it is not emitted (§6 rule 1). A refusal is an
``Answer`` with no claims and the question in ``unanswered`` (§6 rule 4 — stated,
never silently dropped).

The dual payload the proof delivered (proof/FINDINGS.md Q1): each citation names
the graph node(s) its passage resolves to (document grain, via join.py), and the
answer's ``associations`` carries the edges touching those nodes.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from . import join
from .corpus import companion_note
from .retrieve import Passage


@dataclass(frozen=True)
class Citation:
    source_file: str          # WDB-relative path of the source doc — the join key (#4)
    note: str                 # companion-note pointer, e.g. "..._context.md" ("" if none)
    location: str             # civ-kb mechanical span, e.g. "page 2 [part 4/4]"
    quote: str                # the verbatim passage text (the span)
    nodes: tuple[str, ...]    # matching graph node id(s) at document grain


@dataclass(frozen=True)
class Claim:
    text: str
    citations: tuple[Citation, ...]
    mode: str = "B"


@dataclass
class Answer:
    claims: list[Claim] = field(default_factory=list)
    associations: list = field(default_factory=list)   # Mode-A edges for the cited nodes
    unanswered: list[str] = field(default_factory=list)
    figures: list = field(default_factory=list)        # Mode C only — empty here

    @property
    def answered(self) -> bool:
        return bool(self.claims)


def refusal(question: str, reason: str) -> Answer:
    """§6 rule 4: state what no mode could ground, never back-fill by invention."""
    return Answer(unanswered=[f"{question} — {reason}"])


def _cited_indices(text: str, n: int) -> list[int]:
    """1-based passage indices referenced as [k] in the synthesis (all, if none)."""
    cited = sorted({int(m) for m in re.findall(r"\[(\d+)\]", text) if 1 <= int(m) <= n})
    return cited or list(range(1, n + 1))


def assemble(question: str, passages: list[Passage], synthesis_text: str,
             nodes: list[dict], links: list[dict], root: str) -> Answer:
    """Turn retrieved passages + a synthesized answer into the contract shape.

    Each cited passage becomes a ``Citation`` carrying its verbatim quote, its
    span (location), the companion note, and the graph node(s) it joins to. The
    answer's ``associations`` is the edge payload touching all those nodes.
    """
    cited = _cited_indices(synthesis_text, len(passages))
    citations: list[Citation] = []
    all_node_ids: set[str] = set()
    for i in cited:
        p = passages[i - 1]
        matched = join.nodes_for_source(p.source_file, nodes)
        node_ids = tuple(n["id"] for n in matched)
        all_node_ids.update(node_ids)
        citations.append(Citation(
            source_file=p.source_file,
            note=companion_note(p.source_file, root) or "",
            location=p.location,
            quote=p.text.strip(),
            nodes=node_ids,
        ))

    if not citations:                       # never emit an un-sourced claim (§6 rule 1)
        return refusal(question, "no citable passage after synthesis")

    edges = join.associations(all_node_ids, links)
    claim = Claim(text=synthesis_text.strip(), citations=tuple(citations))
    return Answer(claims=[claim], associations=edges)
