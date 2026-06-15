"""The vetted-band gate: the three conditions, pass and refuse."""

import copy

import pytest

from mode_c import Filter, Op, Resolution, load_catalog, vetted_band
from mode_c.fixtures import RECORDED
from mode_c.fixtures.resolutions import Q1, Q2, Q4, Q6

KENYA = "peskas/kenya_validated_trips.csv"


@pytest.fixture(scope="module")
def cat():
    return load_catalog()


@pytest.mark.parametrize("q", [Q1, Q2, Q4, Q6])
def test_in_band_resolutions_pass(cat, q):
    assert vetted_band(RECORDED[q], cat).ok


def test_refuse_non_distinctive_value(cat):
    # a single table chosen on a value shared across sister tables -> refuse (cond. 1)
    res = Resolution(table=KENYA, aggregation="AVG", pinned_by="Gill Net",
                     metric_column="trip_duration_hrs", grain_key="trip_id",
                     filters=(Filter("gear", Op.EQ, "Gill Net"),))
    v = vetted_band(res, cat)
    assert not v.ok and "not distinctive" in v.reason


def test_refuse_value_absent_from_domain(cat):
    res = Resolution(table=KENYA, aggregation="AVG", pinned_by="Kwale",
                     metric_column="tot_catch_kg", grain_key="trip_id",
                     filters=(Filter("gaul_1_name", Op.EQ, "Kisumu"),))
    v = vetted_band(res, cat)
    assert not v.ok and "enumerated domain" in v.reason


def test_refuse_unknown_column(cat):
    res = Resolution(table=KENYA, aggregation="AVG", pinned_by="Kwale",
                     metric_column="water_temp_c", grain_key="trip_id",
                     filters=(Filter("gaul_1_name", Op.EQ, "Kwale"),))
    v = vetted_band(res, cat)
    assert not v.ok and "data dictionary" in v.reason


def test_refuse_registered_derived_metric_without_surfaced_denominator(cat):
    # a registered derived metric (CPUE) with no surfaced assumption -> refuse (cond. 2)
    res = Resolution(table=KENYA, aggregation="AVG", pinned_by="Kwale",
                     derived_formula="tot_catch_kg / NULLIF(trip_duration_hrs, 0)",
                     derived_inputs=("tot_catch_kg", "trip_duration_hrs"),
                     grain_key="trip_id", filters=(Filter("gaul_1_name", Op.EQ, "Kwale"),),
                     assumptions=(), metric_label="avg_cpue")
    v = vetted_band(res, cat)
    assert not v.ok and "denominator" in v.reason


def test_refuse_unregistered_derived_metric(cat):
    # a derived formula for a metric that is not in the registry is out of band
    res = Resolution(table=KENYA, aggregation="AVG", pinned_by="Kwale",
                     derived_formula="tot_catch_kg / NULLIF(n_fishers, 0)",
                     derived_inputs=("tot_catch_kg", "n_fishers"),
                     grain_key="trip_id", filters=(Filter("gaul_1_name", Op.EQ, "Kwale"),),
                     assumptions=("per fisher",), metric_label="avg_catch_per_fisher")
    v = vetted_band(res, cat)
    assert not v.ok and "not registered" in v.reason


def test_refuse_grain_undocumented_table(cat):
    # condition 3: a table whose grain is not recorded falls outside the band
    cat2 = copy.deepcopy(cat)
    spec = cat2.get(KENYA)
    spec.grain_text = ""           # simulate an un-reviewed / missing grain line
    spec.repeating_columns = frozenset()
    res = RECORDED[Q4]
    v = vetted_band(res, cat2)
    assert not v.ok and "grain is not explicitly recorded" in v.reason


def test_refuse_grain_trap_structurally(cat):
    # aggregating a repeating column over raw rows is refused by construction
    res = Resolution(table=KENYA, aggregation="AVG", pinned_by="Kwale",
                     metric_column="tot_catch_kg", grain_key=None,
                     filters=(Filter("gaul_1_name", Op.EQ, "Kwale"),))
    v = vetted_band(res, cat)
    assert not v.ok and "grain trap" in v.reason
