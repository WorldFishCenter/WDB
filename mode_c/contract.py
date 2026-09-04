"""Mode C's half of the §6 answer contract: turning a computed result into claims + figures.

The contract *shape* (``Citation``, ``Claim``, ``Figure``, ``Answer``, ``Unanswered``) is
declared once in :mod:`wdb_contract`; this module holds only what is Mode-C specific — how a
query result becomes a citation, and the prose humanisers.

The defining Mode-C rule (§6 rule 3): **a claim's citation IS the SQL plus its result rows** —
every number ships reproducibly with the query that produced it. A refusal or disambiguation
is an ``Answer`` with no claims and the question stated in ``unanswered`` (§6 rule 4).

Disambiguation candidates used to live in an ``Answer.disambiguation`` field that the router's
merge never read, so the typed candidate list survived only as prose. They now ride on the
``Unanswered`` entry itself (``code=NEEDS_DISAMBIGUATION``, ``candidates=…``), which the merge
carries end to end.
"""

from __future__ import annotations

import re

from wdb_contract import (
    Answer,
    CitationC as Citation,
    Claim,
    Figure,
    Unanswered,
    UnansweredCode,
    Verdict,
)

from .catalog import Catalog
from .executor import ExecResult
from .resolution import NeedsDisambiguation, Resolution

__all__ = [
    "Answer", "Citation", "Claim", "Figure", "Unanswered", "UnansweredCode", "Verdict",
    "refusal", "disambiguation", "assemble",
]

# The executor falls back to "value" when metric_label isn't a valid SQL identifier; this is
# the one place that rule is mirrored for the answer side, so the lookup always matches the
# SQL column alias. (It used to be copy-pasted twice, 17 lines apart, in this file.)
_SQL_IDENT = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


def _sql_label(res: Resolution) -> str:
    return res.metric_label if _SQL_IDENT.match(res.metric_label or "") else "value"


def _note(res: Resolution, catalog: Catalog) -> str:
    spec = catalog.get(res.table)
    dict_file = spec.dict_file.split("/")[-1] if spec else res.table
    section = "Grain" if res.grain_key else "Columns"
    return f"{dict_file}#{section}"


def refusal(question: str, reason: str,
            code: UnansweredCode = UnansweredCode.UNSPECIFIED) -> Answer:
    """§6 rule 4: state what Mode C could not compute — never a fabricated number (§7)."""
    return Answer(unanswered=[
        Unanswered(part=question, mode="C", code=code, detail=reason)
    ])


def disambiguation(question: str, nd: NeedsDisambiguation) -> Answer:
    """Several tables could answer this — say which, structurally, and refuse to guess."""
    cand = f" (candidates: {', '.join(nd.candidates)})" if nd.candidates else ""
    return Answer(unanswered=[Unanswered(
        part=question,
        mode="C",
        code=UnansweredCode.NEEDS_DISAMBIGUATION,
        detail=f"needs disambiguation: {nd.reason}{cand}",
        candidates=tuple(nd.candidates),
    )])


def assemble(question: str, res: Resolution, result: ExecResult, catalog: Catalog) -> Answer:
    """Turn a computed result into the answer-contract shape."""
    citation = Citation(
        source_file=res.table,
        note=_note(res, catalog),
        sql=result.sql,
        result=result.rows,
    )
    sql_label = _sql_label(res)

    if res.group_by:
        figure = Figure(
            spec={"kind": "bar", "x": res.group_by, "y": sql_label},
            query=result.sql,
            result=result.rows,
        )
        top = result.rows[0]
        text = (
            f"{_humanise_metric(res)} by {res.group_by} for {_table_label(res, catalog)} "
            f"(top: {top.get(res.group_by)} = {top.get(sql_label)}; "
            f"{len(result.rows)} groups). Every figure below is computed from rows."
        )
        return Answer(claims=[Claim(text=text, citations=(citation,), mode="C")],
                      figures=[figure])

    row = result.rows[0]
    value = row.get(sql_label)
    n = row.get("n")
    filter_str = _filter_clause(res)
    location = f" {filter_str}" if filter_str else ""
    text = (
        f"{_humanise_metric(res)}{location} is {value} "
        f"(computed over {n} {'trips' if res.grain_key == 'trip_id' else 'rows'})."
    )
    if res.derived_formula:
        text += f" Derived: {res.metric_label} = {res.derived_formula}."
    if res.assumptions:
        text += " Assumption(s): " + "; ".join(res.assumptions) + "."
    if res.confidence < 1.0:
        text += f" (confidence {res.confidence:.2f})"
    return Answer(claims=[Claim(text=text, citations=(citation,), mode="C")])


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
