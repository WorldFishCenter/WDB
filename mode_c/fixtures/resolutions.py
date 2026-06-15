"""The proof's resolutions, transcribed as fixtures.

``RECORDED`` maps each of the 9 questions from ``proof_c/RESOLVER_FINDINGS.md`` to
the resolution / refusal / disambiguation the proof's Opus 4.8 produced. The
``ReplayResolver`` serves these so the gate + executor + contract pipeline is
tested deterministically, end-to-end, with real DuckDB computation.

Also defined: the two **naive-control** resolutions the proof's comparison arm
produced (the grain trap and the CPUE proxy) and an out-of-band route — used by
the guard tests to prove the gate refuses them rather than computing a wrong (or
mislabeled) number.
"""

from __future__ import annotations

from ..resolution import (
    CannotResolve,
    Filter,
    NeedsDisambiguation,
    Op,
    Resolution,
)

KENYA = "peskas/kenya_validated_trips.csv"
MOZAMBIQUE = "peskas/mozambique_validated_trips.csv"
ZANZIBAR = "peskas/zanzibar_validated_trips.csv"
FICD = "fasa/FICD_feed_ingredient_composition_database.csv"


# --- the 9 proof questions ------------------------------------------------- #

Q1 = "Average weight of an individual catch in Kwale?"
Q2 = "Average CPUE in Kwale district?"
Q3A = "Average trip duration for Gill Net trips?"
Q3B = "Average trip duration for Gill Net trips in Zanzibar?"
Q4 = "Average total catch per trip in Kwale?"
Q4B = "Average total catch per trip in Inhambane?"
Q5A = "Average catch in Kisumu county?"
Q5B = "Average wind speed on Kenya trips?"
Q6 = "Average crude protein across fish-meal ingredients?"


RECORDED = {
    # Q1 — clean hit: individual catch weight is at the row grain (one row = one
    # catch item), so no dedup. NOT a grain test (the row already is the unit).
    Q1: Resolution(
        table=KENYA, aggregation="AVG", pinned_by="Kwale",
        metric_column="catch_kg", grain_key=None,
        filters=(Filter("gaul_1_name", Op.EQ, "Kwale"),),
        metric_label="avg_catch_kg",
    ),
    # Q2 — derived / no such column: CPUE = catch ÷ effort, denominator flagged,
    # at trip grain (the inputs are trip-level and repeat across catch rows).
    Q2: Resolution(
        table=KENYA, aggregation="AVG", pinned_by="Kwale",
        derived_formula="tot_catch_kg / NULLIF(trip_duration_hrs, 0)",
        derived_inputs=("tot_catch_kg", "trip_duration_hrs"),
        grain_key="trip_id",
        filters=(Filter("gaul_1_name", Op.EQ, "Kwale"),),
        assumptions=(
            "effort = trip duration in hours (trip-hours); "
            "alternatives: fisher-hours (n_fishers x trip_duration_hrs), or per-trip (no effort)",
        ),
        round_digits=3, confidence=0.7,
        metric_label="avg_cpue_kg_per_trip_hr",
        notes="CPUE is a derived metric, not a stored column",
    ),
    # Q3a — sister ambiguity: 'Gill Net' is shared by all three trip tables.
    Q3A: NeedsDisambiguation(
        reason="'Gill Net' is a gear shared by the Kenya, Mozambique and Zanzibar "
               "trip tables; specify the region/initiative.",
        candidates=(KENYA, MOZAMBIQUE, ZANZIBAR),
    ),
    # Q3b — region breaks the tie.
    Q3B: Resolution(
        table=ZANZIBAR, aggregation="AVG", pinned_by="Zanzibar",
        metric_column="trip_duration_hrs", grain_key="trip_id",
        filters=(Filter("gear", Op.EQ, "Gill Net"),),
        metric_label="avg_trip_duration_hrs",
    ),
    # Q4 — the grain trap (implicit on Kenya, now explicit after Phase 0):
    # tot_catch_kg repeats across a trip's catch rows -> dedup to trip grain.
    Q4: Resolution(
        table=KENYA, aggregation="AVG", pinned_by="Kwale",
        metric_column="tot_catch_kg", grain_key="trip_id",
        filters=(Filter("gaul_1_name", Op.EQ, "Kwale"),),
        metric_label="avg_total_catch_kg_per_trip",
    ),
    # Q4b — the grain trap (explicit caveat) on Mozambique.
    Q4B: Resolution(
        table=MOZAMBIQUE, aggregation="AVG", pinned_by="Inhambane",
        metric_column="tot_catch_kg", grain_key="trip_id",
        filters=(Filter("gaul_1_name", Op.EQ, "Inhambane"),),
        metric_label="avg_total_catch_kg_per_trip",
    ),
    # Q5a — refusal, absent value: Kisumu is not a coastal county in the domain.
    Q5A: CannotResolve(
        reason="'Kisumu' is not in any table's county/region domain "
               "(Kenya counties: Kilifi, Kwale, Lamu, Mombasa, Tana River).",
    ),
    # Q5b — refusal, absent column: no wind/weather column exists anywhere.
    Q5B: CannotResolve(reason="no wind/weather column exists in any table."),
    # Q6 — EAV / mislabeled column: the routable parameter lives inside the
    # `ingredient` column's values; the actual metric is `quantity`.
    Q6: Resolution(
        table=FICD, aggregation="AVG", pinned_by="crude_protein_percent",
        metric_column="quantity", grain_key=None,
        filters=(
            Filter("ingredient", Op.EQ, "crude_protein_percent"),
            Filter("description", Op.CONTAINS, "fish meal"),
        ),
        metric_label="avg_crude_protein_percent",
        notes="ingredient column holds the parameter name (mislabeled); quantity is the value",
    ),
}

PROOF_QUESTIONS = [Q1, Q2, Q3A, Q3B, Q4, Q4B, Q5A, Q5B, Q6]


# --- naive controls (the comparison arm's failures) ------------------------ #

# The grain trap: AVG(tot_catch_kg) over RAW ROWS (grain_key=None) — confident,
# plausible, and wrong (28.99 instead of 31.88). The gate must refuse this.
NAIVE_KENYA_GRAIN_TRAP = Resolution(
    table=KENYA, aggregation="AVG", pinned_by="Kwale",
    metric_column="tot_catch_kg", grain_key=None,
    filters=(Filter("gaul_1_name", Op.EQ, "Kwale"),),
    metric_label="avg_total_catch_kg",
)

# The CPUE proxy: relabel AVG(tot_catch_kg) per trip as "cpue" — drops "per unit
# effort" entirely. A stored column with no derived_formula and no surfaced
# denominator. (Same shape as a legitimate per-trip catch average, which is why
# the prompt guard — not the gate — is what prevents it at resolve time; the
# contract here carries no derivation/assumption flag, the observable regression.)
NAIVE_CPUE_PROXY = Resolution(
    table=KENYA, aggregation="AVG", pinned_by="Kwale",
    metric_column="tot_catch_kg", grain_key="trip_id",
    filters=(Filter("gaul_1_name", Op.EQ, "Kwale"),),
    metric_label="avg_cpue",  # mislabeled — no formula, no denominator
)

# Out of band: a single table picked on a generic, shared value.
OUT_OF_BAND_GILLNET = Resolution(
    table=KENYA, aggregation="AVG", pinned_by="Gill Net",
    metric_column="trip_duration_hrs", grain_key="trip_id",
    filters=(Filter("gear", Op.EQ, "Gill Net"),),
    metric_label="avg_trip_duration_hrs",
)
