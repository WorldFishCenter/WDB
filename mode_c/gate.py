"""The vetted-band gate — what makes Mode C trustworthy, not merely capable.

Mode C answers ONLY inside the band the proof actually earned
(``proof_c/RESOLVER_FINDINGS.md``): all three of the following must hold for a
``Resolution``, else the gate refuses (and the pipeline returns "not available"
or a disambiguation rather than a silent number):

1. **Distinctive value pins one table** — the resolution's ``pinned_by`` token
   resolves to exactly one table in the catalog (a place, a species, a name, an
   enumerated gear+region). Generic terms shared across sister tables do not pin.
2. **Column enumerated OR derived formula registered** — the metric is a real
   column of the table, or it is a derived formula whose denominator/assumption
   is surfaced (a registered derived metric). Equality-filter values must be in
   the column's enumerated domain.
3. **Grain explicitly recorded** — the table has a non-empty ``## Grain`` block,
   AND — the structural anti-trap — if the aggregated column is one the grain
   marks as *repeating* (a higher-grain attribute), the resolution must collapse
   to the documented grain key first. Aggregating a repeating column over raw
   rows (the 31.88-vs-28.99 trap) is refused here, by construction.
"""

from __future__ import annotations

from dataclasses import dataclass

from .catalog import Catalog, TableSpec
from .resolution import Op, Resolution

# Registered derived metrics: metrics that are NOT stored columns and must be
# computed from a formula with an explicit denominator choice. A derived metric
# is in band only when its denominator assumption is surfaced (never a proxy).
REGISTERED_DERIVED_METRICS = {
    "cpue": {
        "definition": "catch per unit effort = catch ÷ effort",
        "denominators": [
            "trip duration in hours (trip-hours)",
            "fisher-hours (n_fishers × trip_duration_hrs)",
            "per trip (no effort normalisation)",
        ],
    },
}


@dataclass(frozen=True)
class GateResult:
    ok: bool
    reason: str = ""


def _is_registered_derived(res: Resolution) -> bool:
    label = (res.metric_label or "").lower()
    return any(name in label or name in (res.notes or "").lower()
               for name in REGISTERED_DERIVED_METRICS)


def vetted_band(res: Resolution, catalog: Catalog) -> GateResult:
    spec = catalog.get(res.table)
    if spec is None:
        return GateResult(False, f"unknown table {res.table!r} (not in the catalog)")

    # --- condition 1: distinctive value pins exactly this one table ----------
    if not res.pinned_by.strip():
        return GateResult(False, "no distinctive value offered to pin a table")
    pinned = catalog.pin_table(res.pinned_by)
    if pinned != {res.table}:
        if len(pinned) > 1:
            return GateResult(
                False,
                f"value {res.pinned_by!r} is not distinctive — it matches "
                f"{len(pinned)} tables ({', '.join(sorted(pinned))}); ask which.",
            )
        return GateResult(
            False,
            f"value {res.pinned_by!r} does not pin {res.table!r} "
            f"(pins {sorted(pinned) or 'no table'}).",
        )

    # --- condition 2: column enumerated OR derived formula registered --------
    for col in res.columns_used():
        if col not in spec.columns:
            return GateResult(False, f"column {col!r} is not in {res.table}'s data dictionary")

    if res.derived_formula:
        if not _is_registered_derived(res):
            return GateResult(
                False,
                "derived metric is not registered — only registered derived metrics "
                f"({', '.join(sorted(REGISTERED_DERIVED_METRICS))}) are in the vetted band",
            )
        if not res.assumptions:
            return GateResult(
                False,
                "derived metric without a surfaced denominator/assumption "
                "(a derived formula must register its choice, never a proxy)",
            )
        if not res.derived_inputs:
            return GateResult(False, "derived formula does not declare its input columns")
    elif res.metric_column is None and res.aggregation.upper() != "COUNT":
        return GateResult(False, "no metric column and no derived formula to aggregate")

    # equality-filter values must be in the column's enumerated domain
    for f in res.filters:
        if f.op is not Op.EQ:
            continue
        col = spec.columns[f.column]
        if not col.categorical:
            continue  # numeric / free-text column: no closed domain to check against
        if not any(f.value.casefold() == m.casefold() for m in col.categorical):
            return GateResult(
                False,
                f"value {f.value!r} is not in {f.column}'s enumerated domain "
                f"({{{', '.join(col.categorical)}}})",
            )

    # --- condition 3: grain explicitly recorded + anti-trap ------------------
    if not spec.has_grain:
        return GateResult(
            False,
            f"{res.table}'s grain is not explicitly recorded — outside the vetted band",
        )

    aggregated = set(res.derived_inputs)
    if res.metric_column:
        aggregated.add(res.metric_column)
    trapped = aggregated & spec.repeating_columns
    if trapped and res.grain_key != spec.grain_key:
        return GateResult(
            False,
            f"grain trap: {sorted(trapped)} repeat across rows of {res.table}; "
            f"aggregate over distinct {spec.grain_key!r} first, not raw rows",
        )

    return GateResult(True)
