# Data dictionary: zanzibar_validated_trips.csv

## Summary
Validated small-scale fishery landing/trip records from Zanzibar (Unguja and Pemba islands,
Tanzania), produced by the Peskas monitoring system. Each row is a catch record linked to a
fishing trip, with trip context (location, gear, vessel, effort) and per-catch detail (taxon,
length, weight, price). This is the Zanzibar sibling of `kenya_validated_trips.csv` and
`mozambique_validated_trips.csv` and shares their exact schema: locations are coded with FAO
GAUL administrative layers and catches with scientific names — the same variable conventions
promoted by the WIO SSF data-harmonization guidelines — making this a third-country example of
harmonized catch/effort data for the Western Indian Ocean region.

## Columns
- survey_id: identifier of the survey/data source the record came from — 3 distinct ∈ {a6vXSMtDFgPCASg7ASfgUR, acbfEuAzqAnCGm8Mqenr56, ajEruvrFJCzmi4cmWs9PAc}
- trip_id: unique fishing-trip identifier — identifier, 9496 distinct (e.g. TRIP_645323011, TRIP_645327358, TRIP_645327970, TRIP_645342506, TRIP_645345840)
- landing_date: date the catch was landed — 2025-02-19 → 2026-11-03
- gaul_1_code: GAUL level-1 (region) administrative code — numeric, range 1685–1696
- gaul_1_name: GAUL level-1 region name — 5 distinct ∈ {Kaskazini Pemba, Kaskazini Unguja, Kusini Pemba, Kusini Unguja, Mjini Magharibi}
- gaul_2_code: GAUL level-2 (district) administrative code — numeric, range 106413–106459
- gaul_2_name: GAUL level-2 district name — 11 distinct ∈ {Chake Chake, Kaskazini A, Kaskazini B, Kati, Kusini, Magharibi A, Magharibi B, Micheweni, Mjini, Mkoani, Wete}
- n_fishers: number of fishers on the trip — numeric, range 0–93 (62 missing)
- trip_duration_hrs: trip duration in hours — numeric, range 2–70 (62 missing)
- gear: fishing gear used — 12 distinct ∈ {Beach Seine, Cast Net, Gill Net, Hand Line, Long Line, Mixed gears, Purse Seine, Ring Net, Spear Gun, Stick Rod, Tangle Net, Trap} (62 missing)
- vessel_type: type of vessel/platform used — 6 distinct ∈ {Dhow, Dugout Canoe, Motorized Boat, Outrigger Canoe, Planked Canoe, Wooden Boat} (207 missing)
- catch_habitat: habitat where the catch was taken — 6 distinct ∈ {FAD, Mangrove, Open Sea, Reef, Seagrass, Shore} (62 missing)
- catch_outcome: whether the trip produced a catch (binary flag) — numeric, range 0–1 (62 missing)
- n_catch: number of catch entries/items recorded — numeric, range 1–14 (218 missing)
- catch_taxon: taxon code for the catch — high-cardinality, 121 distinct (e.g. AHI, ALB, AMY, AQT, AQX) (1500 missing)
- scientific_name: scientific (Latin) name of the catch taxon — high-cardinality, 120 distinct (e.g. Acanthocleithron chapini, Acanthuridae, Acanthurus spp, Acanthurus triostegus, Actinopterygii) (1506 missing)
- length_cm: catch length in centimetres — numeric, range 7.5–130000 (4664 missing)
- catch_kg: weight of the individual catch entry in kilograms — numeric, range 0–3600 (3202 missing)
- catch_price: price of the individual catch entry (local currency) — empty throughout (no values recorded)
- tot_catch_kg: total catch weight for the trip in kilograms — numeric, range 0–5500 (4255 missing)
- tot_catch_price: total catch value for the trip (local currency) — numeric, range 0–17050000 (62 missing)

## Related files
- kenya_validated_trips.csv (sister dataset — the Kenya-coast validated trips with the identical schema and conventions)
- mozambique_validated_trips.csv (sister dataset — the Mozambique-coast validated trips with the identical schema and conventions)
- peskas_automated_analytics_softwarex_2025.pdf (the Peskas analytics workflow this data feeds)
- peskas_monitoring_system_slides.pdf (overview of the same monitoring system)
- fishery_nutrient_profiles_timor_leste_naturefood_2026.pdf (Nature Food analysis built on the same kind of Peskas multi-species, multi-gear catch data)
- ../data_harmonization/Technical_Guidelines_SSF_Data_Harmonization_WIO.docx (WIO SSF harmonization standard — this dataset uses its GAUL admin layers and catch/effort variable conventions)

## Notes / caveats
- catch_price is entirely empty: all 14,904 values are missing, so no per-catch price
  information is available for this Zanzibar extract (the trip-total tot_catch_price column is
  still populated).
- length_cm reaches a maximum of 130000, far outside a plausible fish length in centimetres —
  likely a unit mix-up or data-entry error; treat the upper tail with caution.
- landing_date extends to 2026-11-03, a future date relative to the current data snapshot —
  verify the latest records before use.
- catch_outcome is a 0/1 flag, not a continuous measure; rows with catch_outcome = 0 have empty
  catch detail (n_catch, catch_taxon, scientific_name, length_cm, catch_kg all blank).
- catch_habitat capitalizes "Open Sea" and adds a "FAD" (fish aggregating device) category;
  Kenya uses "Open sea" and a "Multiple" category, and Mozambique uses other habitat values — so
  the three countries are not directly comparable on catch_habitat without harmonizing the values.
- Several catch entries belong to the same trip_id (one row per catch item), so trip-level
  fields (n_fishers, trip_duration_hrs, gear, vessel_type, tot_catch_kg, tot_catch_price) repeat
  across the catch rows of a multi-catch trip.
