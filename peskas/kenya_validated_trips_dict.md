# Data dictionary: kenya_validated_trips.csv

## Summary
Validated small-scale fishery landing/trip records from the Kenya coast, produced by the
Peskas monitoring system. Each row is a catch record linked to a fishing trip, with trip
context (location, gear, vessel, effort) and per-catch detail (taxon, length, weight, price).
Locations are coded with FAO GAUL administrative layers and catches with scientific names —
the same variable conventions promoted by the WIO SSF data-harmonization guidelines — so this
is a concrete example of harmonized catch/effort data for the Western Indian Ocean region.

## Grain
One row = one catch item of a fishing trip. The row is finer than `trip_id` (≈2.45 rows per trip):
trip-level fields constant within a `trip_id` and repeating across its catch rows are survey_id,
landing_date, gaul_1_code, gaul_1_name, gaul_2_code, gaul_2_name, n_fishers, trip_duration_hrs, gear,
vessel_type, catch_habitat, catch_outcome, tot_catch_kg, tot_catch_price — aggregate these over
distinct `trip_id`, not raw rows. Per-catch detail (n_catch, catch_taxon, scientific_name, length_cm,
catch_kg, catch_price) varies row to row.

## Columns
- survey_id: identifier of the survey/data source the record came from — 4 distinct ∈ {aAy6nzUo7d7xPsH4YaFs4M, aNKjDfXDKyW3JLtaCdxDp5, aSgfgkYbHn5Q4CVD7Lgcu2, legacy}
- trip_id: unique fishing-trip identifier — identifier, 135255 distinct (e.g. TRIP_1-0002ddd2, TRIP_1-0005b4a2, TRIP_1-00080dc0, TRIP_1-0008f2ff, TRIP_1-000b931f)
- landing_date: date the catch was landed — 1995-09-06 → 2026-09-10
- gaul_1_code: GAUL level-1 (county) administrative code — numeric, range 1366–1392 (83002 missing)
- gaul_1_name: GAUL level-1 county name — 5 distinct ∈ {Kilifi, Kwale, Lamu, Mombasa, Tana River} (83002 missing)
- gaul_2_code: GAUL level-2 (sub-county) administrative code — numeric, range 103616–103782 (83002 missing)
- gaul_2_name: GAUL level-2 sub-county name — 16 distinct ∈ {Changamwe, Garsen, Kilifi North, Kilifi South, Kinango, Kisauni, Lamu East, Lamu West, Likoni, Lunga Lunga, Magarini, Malindi, Matuga, Msambweni, Mvita, Nyali} (83002 missing)
- n_fishers: number of fishers on the trip — numeric, range 1–86 (3 missing)
- trip_duration_hrs: trip duration in hours — numeric, range 0.05–94.5833 (1801 missing)
- gear: fishing gear used — 20 distinct ∈ {Beach Seine, Cast Net, Dropline, Gill Net, Gleaning, Hand Line, Harpoon, Long Line, Nets, Pole and Line, Reef Seine, Ring Net, Scoop Net, Seine, Spear Gun, Stick Rod, Trammel Net, Trap, Trawl Net, Trolling Line} (495 missing)
- vessel_type: type of vessel/platform used — 9 distinct ∈ {Dhow, Dugout Canoe, Feet, Motorized Boat, Other, Outrigger Canoe, Planked Canoe, Raft, Surf Board} (288338 missing)
- catch_habitat: habitat where the catch was taken — 6 distinct ∈ {Mangrove, Multiple, Open sea, Reef, Seagrass, Shore} (288338 missing)
- catch_outcome: whether the trip produced a catch (binary flag) — numeric, range 0–1 (288338 missing)
- n_catch: number of catch entries/items recorded — numeric, range 1–25 (251 missing)
- catch_taxon: taxon code for the catch — high-cardinality, 413 distinct (e.g. AAG, AAJ, AGT, ALS, ALV) (2019 missing)
- scientific_name: scientific (Latin) name of the catch taxon — high-cardinality, 412 distinct (e.g. Acanthocybium solandri, Acanthopagrus berda, Acanthuridae, Acanthurus auranticavus, Acanthurus bariene) (2133 missing)
- length_cm: catch length in centimetres — numeric, range 0–23236 (312133 missing)
- catch_kg: weight of the individual catch entry in kilograms — numeric, range 0–2011 (1383 missing)
- catch_price: price of the individual catch entry (local currency) — numeric, range 0–264250 (3320 missing)
- tot_catch_kg: total catch weight for the trip in kilograms — numeric, range 0.01–2572 (176 missing)
- tot_catch_price: total catch value for the trip (local currency) — numeric, range 1–448500 (9929 missing)

## Related files
- mozambique_validated_trips.csv (sister dataset — the Mozambique-coast validated trips with the identical schema and conventions)
- zanzibar_validated_trips.csv (sister dataset — the Zanzibar validated trips with the identical schema and conventions)
- peskas_automated_analytics_softwarex_2025.pdf (the Peskas analytics workflow this data feeds)
- peskas_monitoring_system_slides.pdf (overview of the same monitoring system)
- fishery_nutrient_profiles_timor_leste_naturefood_2026.pdf (Nature Food analysis built on the same kind of Peskas multi-species, multi-gear catch data)
- ../data_harmonization/Technical_Guidelines_SSF_Data_Harmonization_WIO.docx (WIO SSF harmonization standard — this dataset uses its GAUL admin layers and catch/effort variable conventions)
- ../ssf_research/digital_feedback_fisher_behavior_kenya_2025.pdf (Kenya coastal SSF study on the same fisher population and monitoring approach)

## Notes / caveats
- Many columns carry substantial missing values: gaul_1/gaul_2 codes and names (~83k missing),
  vessel_type / catch_habitat / catch_outcome (~288k missing), and length_cm (~312k missing,
  i.e. present for only a small fraction of records).
- length_cm reaches a maximum of 23236, far outside a plausible fish length in centimetres —
  likely a unit mix-up (mm) or data-entry error; treat the upper tail with caution.
- landing_date extends to 2026-09-10, a future date relative to the current data snapshot —
  verify the latest records before use.
- catch_outcome is a 0/1 flag, not a continuous measure.
