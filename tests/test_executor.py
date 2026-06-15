"""The DuckDB executor computes the proof's exact numbers, grain-faithfully."""

import pytest

from mode_c import Filter, Op, Resolution, load_catalog
from mode_c.executor import execute
from mode_c.fixtures import RECORDED
from mode_c.fixtures.resolutions import Q1, Q2, Q3B, Q4, Q4B, Q6

KENYA = "peskas/kenya_validated_trips.csv"


@pytest.fixture(scope="module")
def cat():
    return load_catalog()


def _value(cat, res):
    rows = execute(res, cat).rows
    label = res.metric_label
    return rows[0]["n"], rows[0][label]


def test_proof_numbers(cat):
    # every figure from proof_c/RESOLVER_FINDINGS.md, computed from rows
    assert _value(cat, RECORDED[Q1])[1] == pytest.approx(13.86, abs=0.005)
    assert _value(cat, RECORDED[Q2]) == (50422, pytest.approx(1.64, abs=0.005))
    assert _value(cat, RECORDED[Q3B]) == (571, pytest.approx(7.62, abs=0.005))
    assert _value(cat, RECORDED[Q4]) == (50422, pytest.approx(31.88, abs=0.005))
    assert _value(cat, RECORDED[Q4B]) == (19, pytest.approx(441.18, abs=0.005))
    assert _value(cat, RECORDED[Q6]) == (57, pytest.approx(62.62, abs=0.005))


def test_grain_faithful_dedup_changes_the_answer(cat):
    # the same column over raw rows is the trap value (28.99), not 31.88
    trap = Resolution(table=KENYA, aggregation="AVG", pinned_by="Kwale",
                      metric_column="tot_catch_kg", grain_key=None,
                      filters=(Filter("gaul_1_name", Op.EQ, "Kwale"),),
                      metric_label="avg")
    assert execute(trap, cat).rows[0]["avg"] == pytest.approx(28.99, abs=0.005)
    assert _value(cat, RECORDED[Q4])[1] == pytest.approx(31.88, abs=0.005)


def test_empty_result_is_refuse_by_construction(cat):
    res = Resolution(table=KENYA, aggregation="AVG", pinned_by="Kwale",
                     metric_column="tot_catch_kg", grain_key="trip_id",
                     filters=(Filter("gaul_1_name", Op.EQ, "Nairobi"),),  # not a coastal county
                     metric_label="avg")
    assert execute(res, cat).empty


def test_values_are_bound_not_interpolated(cat):
    # the filter value is a query parameter, not SQL text -> no injection
    sql = execute(RECORDED[Q4], cat).sql
    assert "= ?" in sql and "Kwale" not in sql


def test_grouped_figure_is_a_clean_ranking(cat):
    res = Resolution(table=KENYA, aggregation="AVG", pinned_by="Kwale",
                     metric_column="tot_catch_kg", grain_key="trip_id",
                     group_by="gaul_1_name", metric_label="avg_kg")
    rows = execute(res, cat).rows
    assert len(rows) == 5  # five counties, NULL group dropped
    assert rows[0]["gaul_1_name"] == "Lamu"
    assert rows[0]["avg_kg"] == pytest.approx(71.98, abs=0.005)
    assert rows[0]["n"] == 8149
