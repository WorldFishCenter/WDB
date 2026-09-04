"""The §6 answer contract — declared once, for every mode and the router.

Before this module the contract was declared six times: three near-copy ``mode_*/contract.py``
files, ``wdb_router/contract.py``, ``wdb_api/serialize.py``, and ``read-ui/lib/contract.ts``.
The copies diverged exactly where it cost most — each mode's ``Answer`` carried a field the
router's merge did not read, so ``mode_a``'s verified not-connected verdict and ``mode_c``'s
disambiguation candidates were dropped at the router seam and reached the UI as a coverage
refusal ("the knowledge base doesn't cover this"). That is the opposite of what Mode A
determined.

What lives here (three-mode architecture doc §6):

* :class:`CitationA` / :class:`CitationB` / :class:`CitationC` — a citation IS a different
  artifact per mode: a graph edge triple, a passage span + verbatim quote + nodes, or the SQL
  plus its result rows. The three shapes stay distinct on purpose; what is shared is that they
  are declared in one place and rendered by one function (:mod:`wdb_contract.render`).
* :class:`Claim` — prose + ``mode`` + ≥1 citation. Rule 1 ("a claim with zero citations is NOT
  emitted") is enforced in :meth:`Claim.__post_init__`, so the contract cannot represent a
  violation.
* :class:`Verdict` — the piece that was missing. A fragment is ``GROUNDED``,
  ``VERIFIED_NEGATIVE`` (we checked and the answer is *no* — Mode A's honesty mechanism), or
  ``UNGROUNDED`` (we could not ground it). ``answered`` is derived from it rather than
  re-inferred from empty lists at each layer.
* :class:`Unanswered` — rule 4's entries, typed. ``code`` is what downstream tests assert on;
  ``detail`` is the prose. Before this, ``unanswered`` was ``list[str]``, so tests in
  ``wdb_router`` and ``wdb_api`` pinned refusal *wording* authored in ``mode_b/gate.py`` —
  editing a message broke tests in two other packages.
* :class:`Answer` — one shape, with the per-mode payloads (``associations``, ``figures``) as
  declared fields rather than placeholder lists each mode carried for another mode's benefit.

The wire stays additive: ``answered`` keeps its current meaning and ``unanswered`` still
serializes as a list of rendered strings; ``verdict`` and ``unanswered_detail`` are new keys.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


# --------------------------------------------------------------------------- #
# citations — one per mode, declared once
# --------------------------------------------------------------------------- #

@dataclass(frozen=True)
class CitationA:
    """Mode A: the graph edge that grounds the relationship (§6, A locator)."""

    source_file: str       # the companion note / doc that *stated* the edge (the join key, #4)
    note: str              # source_location label, e.g. "Validation; Methods 2.3" ("" if none)
    locator: str           # the edge triple "src --relation--> tgt"
    confidence: str        # EXTRACTED | INFERRED (§7: prefer EXTRACTED, flag INFERRED)


@dataclass(frozen=True)
class CitationB:
    """Mode B: the passage span + verbatim quote + the graph node(s) it joins to."""

    source_file: str          # WDB-relative path of the source doc — the join key (#4)
    note: str                 # companion-note pointer, e.g. "..._context.md" ("" if none)
    location: str             # civ-kb mechanical span, e.g. "page 2 [part 4/4]"
    quote: str                # the verbatim passage text (the span)
    nodes: tuple[str, ...]    # matching graph node id(s) at document grain


@dataclass(frozen=True)
class CitationC:
    """Mode C: the SQL plus its result rows — the citation IS the computation (§6 rule 3)."""

    source_file: str        # WDB-relative CSV path — the provenance key (carry-over #4)
    note: str               # companion-note section, e.g. "kenya_validated_trips_dict.md#Grain"
    sql: str                # the exact query
    result: list[dict]      # the result row(s)


Citation = CitationA | CitationB | CitationC


# --------------------------------------------------------------------------- #
# claims & figures
# --------------------------------------------------------------------------- #

class ClaimWithoutCitation(ValueError):
    """§6 rule 1 violated: a claim was built with no citation to ground it."""


@dataclass(frozen=True)
class Claim:
    """One grounded statement, traceable to the mode and source that produced it.

    ``mode`` is required — it is what tells a reader (and the renderer) which citation shape
    to expect, so it must never be a default that a caller can forget to override.
    """

    text: str
    citations: tuple[Citation, ...]
    mode: str

    def __post_init__(self) -> None:
        # §6 rule 1: "a claim with zero citations is NOT emitted". Enforcing it here means the
        # contract cannot represent an un-sourced claim, so no caller has to remember the rule.
        if not self.citations:
            raise ClaimWithoutCitation(
                f"Mode {self.mode} claim has no citation: {self.text[:80]!r}"
            )


@dataclass(frozen=True)
class Figure:
    """A Mode-C chart that ships with the SQL that produced it (§6, §8)."""

    spec: dict
    query: str
    result: list[dict]


# --------------------------------------------------------------------------- #
# verdict & unanswered
# --------------------------------------------------------------------------- #

class Verdict(str, Enum):
    """What a fragment (or the merged answer) actually determined.

    The distinction ``VERIFIED_NEGATIVE`` vs ``UNGROUNDED`` is the honesty property the whole
    design rests on: "we checked, and the answer is no" is a *correct answer*, not a coverage
    failure. Mode A produces it from a disconnected subgraph (no direct edge, no ≤2-hop path);
    Mode C's empty-result and unbound-column refusals are coverage failures, not negatives.
    """

    GROUNDED = "GROUNDED"
    VERIFIED_NEGATIVE = "VERIFIED_NEGATIVE"
    UNGROUNDED = "UNGROUNDED"


class UnansweredCode(str, Enum):
    """Why a part could not be grounded — the stable key, distinct from its prose.

    Assert on these, never on ``detail``. Every value names a real refusal arm that exists in
    a mode today; the mode that owns each is noted.
    """

    # Mode A
    NO_ENTITY_MATCH = "NO_ENTITY_MATCH"           # no graph entity in the question matched a node
    NO_RELATIONSHIP = "NO_RELATIONSHIP"           # entity exists, records no relationship
    NOT_CONNECTED = "NOT_CONNECTED"               # verified negative — pairs with VERIFIED_NEGATIVE
    CITE_CHECK_DOWNGRADE = "CITE_CHECK_DOWNGRADE"  # reasoning failed the mechanical cite-check
    # Mode B
    NO_PASSAGE = "NO_PASSAGE"                     # retrieval returned nothing at all
    THIN_RETRIEVAL = "THIN_RETRIEVAL"             # top passage below the rerank / cosine floor
    NO_COVERAGE = "NO_COVERAGE"                   # no indexed doc covers the asked initiative
    NO_CITABLE_PASSAGE = "NO_CITABLE_PASSAGE"     # synthesis cited nothing quotable
    # Mode C
    NO_TABLE_RESOLVED = "NO_TABLE_RESOLVED"       # the resolver could not bind a table/column
    NEEDS_DISAMBIGUATION = "NEEDS_DISAMBIGUATION"  # several tables match; carries `candidates`
    OUT_OF_BAND = "OUT_OF_BAND"                   # the vetted-band gate refused the resolution
    EMPTY_RESULT = "EMPTY_RESULT"                 # the query matched 0 rows
    EXECUTION_FAILED = "EXECUTION_FAILED"         # e.g. a column that fails to bind
    # any mode, offline
    NO_RECORDED_REPLAY = "NO_RECORDED_REPLAY"     # Replay backend has no fixture for this question
    UNSPECIFIED = "UNSPECIFIED"


@dataclass(frozen=True)
class Unanswered:
    """One part of the question no mode could ground — stated, never hidden (§6 rule 4).

    ``__str__`` renders the same ``"{part} — {detail}"`` prose the system emitted before this
    module existed, so every renderer and the wire format are unchanged.
    """

    part: str
    mode: str
    code: UnansweredCode
    detail: str
    candidates: tuple[str, ...] = ()   # NEEDS_DISAMBIGUATION carries its candidates structurally

    @property
    def text(self) -> str:
        return f"{self.part} — {self.detail}"

    def __str__(self) -> str:
        return self.text


# --------------------------------------------------------------------------- #
# the answer
# --------------------------------------------------------------------------- #

@dataclass
class Answer:
    """One mode's §6 fragment, and — after :func:`merge` — the whole answer.

    ``negative`` is set only by a mode that *verified* the answer is "no". Everything else
    follows from the payload, so no layer re-derives ``answered`` from empty lists.
    """

    claims: list[Claim] = field(default_factory=list)
    associations: list = field(default_factory=list)    # graph edges (Mode A + Mode B)
    figures: list[Figure] = field(default_factory=list)  # Mode C only
    unanswered: list[Unanswered] = field(default_factory=list)
    negative: bool = False                               # a verified "the answer is no"
    path: str = ""                                       # which path produced this (Mode A)

    @property
    def verdict(self) -> Verdict:
        if self.claims or self.figures:
            return Verdict.GROUNDED
        return Verdict.VERIFIED_NEGATIVE if self.negative else Verdict.UNGROUNDED

    @property
    def answered(self) -> bool:
        # a verified not-connected verdict IS a correct answer (the answer is "no")
        return self.verdict is not Verdict.UNGROUNDED


def refusal(question: str, mode: str, code: UnansweredCode, detail: str) -> Answer:
    """§6 rule 4: state what could not be grounded, never back-fill by invention."""
    return Answer(unanswered=[Unanswered(part=question, mode=mode, code=code, detail=detail)])


def _edge_key(e: dict) -> tuple:
    return (e.get("source"), e.get("relation"), e.get("target"))


def add_associations(answer: Answer, edges: list) -> None:
    """Merge graph edges into ``answer.associations``, de-duplicated by triple.

    Mode A's subgraph edges and Mode B's document-grain associations are the same
    ``graph.json`` link shape, so this de-dups cleanly across both.
    """
    seen = {_edge_key(e) for e in answer.associations}
    for e in edges:
        k = _edge_key(e)
        if k not in seen:
            seen.add(k)
            answer.associations.append(e)


def merge(into: Answer, fragment: Answer) -> Answer:
    """Fold one mode's fragment into an accumulating answer, in place.

    This is the step that used to live as three hand-written blocks in
    ``wdb_router/composition.py``, each reading a different subset of the fields — which is how
    ``connected``, ``path`` and ``disambiguation`` were silently dropped. Merging every field
    here means a new field on :class:`Answer` cannot be forgotten by the router.

    ``negative`` propagates: a verified negative from any fragment survives the merge, but a
    grounded claim from any mode outranks it (``verdict`` prefers ``GROUNDED``).
    """
    into.claims.extend(fragment.claims)
    add_associations(into, fragment.associations)
    into.figures.extend(fragment.figures)
    into.unanswered.extend(fragment.unanswered)
    into.negative = into.negative or fragment.negative
    return into
