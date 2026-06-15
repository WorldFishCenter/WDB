"""The resolution data model — the resolver's output, before the gate and executor.

A natural-language quantitative question resolves to exactly one of:

* ``Resolution``          — a concrete, executable plan: which table, which column(s)
                            or derived formula, at which grain, with which filters.
* ``CannotResolve``       — the data cannot answer it (absent value / absent column).
* ``NeedsDisambiguation`` — it could route to several tables; ask which.

These mirror the shape the read-only proof emitted
(``proof_c/RESOLVER_FINDINGS.md``): ``{table, columns, grain, aggregation,
derived_formula, filters}`` or an explicit refusal / disambiguation. The fields
here are the *executable* form of that shape.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class Op(str, Enum):
    """Filter operators the executor knows how to bind safely."""

    EQ = "="              # column = value  (value bound as a parameter)
    CONTAINS = "contains"  # column ILIKE %value%  (EAV / free-text membership)


@dataclass(frozen=True)
class Filter:
    column: str
    op: Op
    value: str


@dataclass(frozen=True)
class Resolution:
    """A concrete, executable resolution of one quantitative question.

    ``grain_key`` is the decisive field (the proof's grain trap): when a table
    row is *finer* than the unit the question asks about, ``grain_key`` names the
    entity to collapse to first (e.g. ``trip_id``) so the metric is aggregated
    over the right unit, not over raw rows. ``grain_key=None`` means the row
    *is* the unit and no de-duplication is needed.
    """

    table: str                       # WDB-relative CSV path, e.g. "peskas/kenya_validated_trips.csv"
    aggregation: str                 # AVG | COUNT | SUM | MIN | MAX
    pinned_by: str                   # the distinctive token that selects the table (gate checks it)

    metric_column: str | None = None        # a stored column to aggregate (e.g. "catch_kg")
    derived_formula: str | None = None       # SQL expr when the metric is NOT a stored column (CPUE)
    derived_inputs: tuple[str, ...] = ()      # columns the derived_formula references
    grain_key: str | None = None              # dedup key; None => aggregate raw rows
    filters: tuple[Filter, ...] = ()
    group_by: str | None = None               # for grouped comparisons / figures

    assumptions: tuple[str, ...] = ()         # surfaced assumptions (e.g. CPUE denominator choice)
    round_digits: int = 2
    confidence: float = 1.0
    metric_label: str = "value"               # safe identifier used for the computed column
    notes: str = ""

    def columns_used(self) -> set[str]:
        """Every column this resolution touches — for executor SELECT and gate checks."""
        cols: set[str] = set(self.derived_inputs)
        if self.metric_column:
            cols.add(self.metric_column)
        for f in self.filters:
            cols.add(f.column)
        if self.group_by:
            cols.add(self.group_by)
        return cols


@dataclass(frozen=True)
class CannotResolve:
    reason: str


@dataclass(frozen=True)
class NeedsDisambiguation:
    reason: str
    candidates: tuple[str, ...] = ()


Outcome = Resolution | CannotResolve | NeedsDisambiguation
