"""Mode A — HARNESS-GRADE graph-enumeration STAND-IN (not the real Mode A).

⚠️  This is **not** "Mode A, built." The real Mode A, per the three-mode
architecture (docs/three-mode-architecture.md §2, §10), is **Claude reasoning over
``graph.json``** through the ``/graphify`` skill — it "needs no new capability" and
is already in production use. There is therefore no Mode-A *library* to reuse.

What this module is: a deliberately thin, deterministic enumeration just good
enough to let the throwaway router validate **composition** and the **answer
contract** (§6) on relationship/enumeration questions, end-to-end, with no model
and no network. It does **not** do entity resolution, query understanding, or the
graph reasoning the real Mode A does. Later phases must build the real Mode A and
**must not** treat this stand-in as finished.

It reuses ``mode_b.join`` (``load_graph``) for graph I/O rather than reimplementing
it, and honours Mode A's native honesty mechanism (§7): enumerate from committed,
stated edges; **prefer ``EXTRACTED`` and flag ``INFERRED``**; when nothing matches,
contribute to ``unanswered`` rather than guess.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

# Single-word labels too generic to anchor an enumeration on (would over-match).
_LABEL_STOPWORDS = {
    "data", "trips", "dataset", "database", "report", "paper", "study", "notes",
    "overview", "summary", "framework", "platform", "system", "analytics",
}


@dataclass(frozen=True)
class Citation:
    """A Mode-A citation: the graph edge that grounds the relationship (§6, A locator)."""

    source_file: str       # the companion note that *stated* the edge (the join key, #4)
    note: str              # source_location label, e.g. "§2.3" ("" if none)
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
    associations: list = field(default_factory=list)   # the enumerated edges
    unanswered: list[str] = field(default_factory=list)

    @property
    def answered(self) -> bool:
        return bool(self.claims)


def find_anchors(question: str, nodes: list[dict]) -> list[dict]:
    """Nodes the question names — by whole-phrase match on the node's ``norm_label``.

    STAND-IN heuristic (see module docstring): a node anchors when its full
    ``norm_label`` occurs as a word/phrase in the question (so "Kenya" anchors the
    ``shared_kenya`` node; a multi-word label that isn't quoted in the question
    does not). Single-word labels must be ≥4 chars and not a generic stopword.
    The real Mode A resolves entities far more richly than this.
    """
    q = question.lower()
    anchors = []
    for n in nodes:
        nl = (n.get("norm_label") or "").strip()
        if len(nl) < 4:
            continue
        if " " not in nl and nl in _LABEL_STOPWORDS:
            continue
        if re.search(r"\b" + re.escape(nl) + r"\b", q):
            anchors.append(n)
    return anchors


def enumerate_relationships(question: str, nodes: list[dict], links: list[dict]) -> Answer:
    """Enumerate the edges incident to the entities the question names.

    One claim per stated edge, each carrying the edge as its citation; the same
    edges form the ``associations`` payload. EXTRACTED edges sort first; INFERRED
    edges are flagged in the claim text so a reader discounts them (§7). Nothing
    matched → a stated ``unanswered`` entry (never a guess).
    """
    by_id = {n["id"]: n for n in nodes}
    anchors = find_anchors(question, nodes)
    if not anchors:
        return Answer(unanswered=[
            f"{question} — no graph entity in this question matched a committed node"
        ])

    anchor_ids = {n["id"] for n in anchors}
    edges: list[dict] = []
    seen: set[tuple] = set()
    for e in links:
        s, t = e.get("source"), e.get("target")
        if s in anchor_ids or t in anchor_ids:
            key = (s, e.get("relation"), t)
            if key not in seen:
                seen.add(key)
                edges.append(e)

    if not edges:
        labels = ", ".join(sorted({n["label"] for n in anchors}))
        return Answer(unanswered=[
            f"{question} — graph has node(s) [{labels}] but no edge records a relationship"
        ])

    claims: list[Claim] = []
    for e in edges:
        s = by_id.get(e["source"])
        t = by_id.get(e["target"])
        s_lbl = s["label"] if s else e["source"]
        t_lbl = t["label"] if t else e["target"]
        conf = e.get("confidence", "")
        flag = "  [INFERRED — discount]" if conf == "INFERRED" else ""
        triple = f"{e['source']} --{e.get('relation', '?')}--> {e['target']}"
        claims.append(Claim(
            text=f"{s_lbl} —{e.get('relation', '?')}→ {t_lbl}{flag}",
            citations=(Citation(
                source_file=e.get("source_file", ""),
                note=e.get("source_location") or "",
                locator=triple,
                confidence=conf,
            ),),
        ))

    # §7: prefer EXTRACTED — list the stated facts before the inferred guesses.
    claims.sort(key=lambda c: 0 if c.citations[0].confidence == "EXTRACTED" else 1)
    return Answer(claims=claims, associations=edges)
