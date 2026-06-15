"""The catalog reads the structural contract the gate and resolver depend on."""

from mode_c import load_catalog

KENYA = "peskas/kenya_validated_trips.csv"
MOZ = "peskas/mozambique_validated_trips.csv"
ZAN = "peskas/zanzibar_validated_trips.csv"
FICD = "fasa/FICD_feed_ingredient_composition_database.csv"


def test_loads_all_eleven_tables():
    cat = load_catalog()
    assert len(cat.tables) == 11
    assert KENYA in cat.tables and FICD in cat.tables


def test_every_table_has_explicit_grain():
    # Phase 0 documented grain across all 11 tables; the gate relies on it.
    cat = load_catalog()
    assert all(spec.has_grain for spec in cat.tables.values())


def test_kenya_grain_key_and_repeating_columns():
    spec = load_catalog().get(KENYA)
    assert spec.grain_key == "trip_id"
    # the trip-level total repeats across catch rows -> must dedupe to aggregate
    assert "tot_catch_kg" in spec.repeating_columns
    # the per-catch weight is at the row grain -> NOT a repeating attribute
    assert "catch_kg" not in spec.repeating_columns
    assert "trip_id" not in spec.repeating_columns  # the key itself is not "repeating"


def test_ficd_grain_finest_value_not_repeating():
    spec = load_catalog().get(FICD)
    assert spec.has_grain
    assert spec.grain_key is None  # one row per composition value; no dedup key
    assert {"code", "description"} <= spec.repeating_columns
    assert "quantity" not in spec.repeating_columns  # the metric is at the finest grain


def test_categorical_and_example_domains_parsed():
    cat = load_catalog()
    assert "Kwale" in cat.get(KENYA).columns["gaul_1_name"].categorical
    assert "crude_protein_percent" in cat.get(FICD).columns["ingredient"].examples


def test_pin_table_distinctive_values():
    cat = load_catalog()
    assert cat.pin_table("Kwale") == {KENYA}
    assert cat.pin_table("Inhambane") == {MOZ}
    assert cat.pin_table("Zanzibar") == {ZAN}                      # identity token
    assert cat.pin_table("crude_protein_percent") == {FICD}        # enumerated parameter token
    assert cat.pin_table("Kisumu") == set()                        # absent value -> no table


def test_pin_table_generic_values_are_not_distinctive():
    cat = load_catalog()
    # a gear shared across the three sister tables cannot pin one
    assert cat.pin_table("Gill Net") == {KENYA, MOZ, ZAN}
    # "fish meal" honestly matches both the composition DB and the recipe DB
    assert len(cat.pin_table("fish meal")) >= 2
