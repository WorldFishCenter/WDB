"""The answer contract (three-mode architecture doc §6), as far as Mode C needs.

A grounded answer is a list of ``Claim``s (here all ``mode="C"``), optional
``Figure``s, and an ``unanswered`` list for anything no mode could ground. The
defining Mode-C rule (§6 rule 3): **a claim's citation IS the SQL plus its
result rows** — every number ships reproducibly with the query that produced it.
A refusal or disambiguation is an ``Answer`` with no claims and the question in
``unanswered`` (§6 rule 4 — stated, never silently dropped).
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from .catalog import Catalog
from .executor import ExecResult
from .resolution import NeedsDisambiguation, Resolution


@dataclass(frozen=True)
class Citation:
    source_file: str        # WDB-relative CSV path — the provenance key (carry-over #4)
    note: str               # companion-note section, e.g. "kenya_validated_trips_dict.md#Grain"
    sql: str                # the exact query
    result: list[dict]      # the result row(s) — the citation IS the computation


@dataclass(frozen=True)
class Claim:
    text: str
    citations: tuple[Citation, ...]
    mode: str = "C"


@dataclass(frozen=True)
class Figure:
    spec: dict
    query: str
    result: list[dict]


@dataclass
class Answer:
    claims: list[Claim] = field(default_factory=list)
    figures: list[Figure] = field(default_factory=list)
    unanswered: list[str] = field(default_factory=list)
    associations: list = field(default_factory=list)          # Mode A — empty here
    disambiguation: NeedsDisambiguation | None = None

    @property
    def answered(self) -> bool:
        return bool(self.claims) or bool(self.figures)


def _note(res: Resolution, catalog: Catalog) -> str:
    spec = catalog.get(res.table)
    dict_file = spec.dict_file.split("/")[-1] if spec else res.table
    section = "Grain" if res.grain_key else "Columns"
    return f"{dict_file}#{section}"


def refusal(question: str, reason: str) -> Answer:
    return Answer(unanswered=[f"{question} — {reason}"])


def disambiguation(question: str, nd: NeedsDisambiguation) -> Answer:
    cand = f" (candidates: {', '.join(nd.candidates)})" if nd.candidates else ""
    return Answer(
        unanswered=[f"{question} — needs disambiguation: {nd.reason}{cand}"],
        disambiguation=nd,
    )


def assemble(question: str, res: Resolution, result: ExecResult, catalog: Catalog) -> Answer:
    """Turn a computed result into the answer-contract shape."""
    citation = Citation(
        source_file=res.table,
        note=_note(res, catalog),
        sql=result.sql,
        result=result.rows,
    )

    if res.group_by:
        spec = catalog.get(res.table)
        figure = Figure(
            spec={"kind": "bar", "x": res.group_by, "y": res.metric_label},
            query=result.sql,
            result=result.rows,
        )
        top = result.rows[0]
        text = (
            f"{_humanise_metric(res)} by {res.group_by} for {_table_label(res, catalog)} "
            f"(top: {top.get(res.group_by)} = {top.get(res.metric_label)}; "
            f"{len(result.rows)} groups). Every figure below is computed from rows."
        )
        return Answer(claims=[Claim(text=text, citations=(citation,))], figures=[figure])

    row = result.rows[0]
    value = row.get(res.metric_label)
    n = row.get("n")
    text = (
        f"{_humanise_metric(res)} {_filter_clause(res)} is {value} "
        f"(computed over {n} {'trips' if res.grain_key == 'trip_id' else 'rows'})."
    )
    if res.derived_formula:
        text += f" Derived: {res.metric_label} = {res.derived_formula}."
    if res.assumptions:
        text += " Assumption(s): " + "; ".join(res.assumptions) + "."
    if res.confidence < 1.0:
        text += f" (confidence {res.confidence:.2f})"
    return Answer(claims=[Claim(text=text, citations=(citation,))])


# --------------------------------------------------------------------------- #
# small humanisers (presentation only)
# --------------------------------------------------------------------------- #

def _humanise_metric(res: Resolution) -> str:
    label = res.metric_label.replace("_", " ")
    agg = res.aggregation.upper()
    prefix = {"AVG": "Average", "SUM": "Total", "COUNT": "Count of",
              "MIN": "Minimum", "MAX": "Maximum"}.get(agg, agg)
    # the label often already starts with avg/total; keep it readable either way
    label = re.sub(r"^(avg|average|total)\s+", "", label)
    return f"{prefix} {label}".strip()


def _filter_clause(res: Resolution) -> str:
    parts = [f"{f.column}={f.value}" if f.op.value == "=" else f"{f.column}~{f.value}"
             for f in res.filters]
    return ("for " + ", ".join(parts)) if parts else ""


def _table_label(res: Resolution, catalog: Catalog) -> str:
    return res.table.split("/")[-1].replace(".csv", "")
