# Data dictionary: mozambique_validated_trips.csv

## Summary
Validated small-scale fishery landing/trip records from the Mozambique coast, produced by the
Peskas monitoring system. Each row is a catch record linked to a fishing trip, with trip
context (location, gear, vessel, effort) and per-catch detail (taxon, length, weight, price).
This is the Mozambique sibling of `kenya_validated_trips.csv` and shares its exact schema:
locations are coded with FAO GAUL administrative layers and catches with scientific names — the
same variable conventions promoted by the WIO SSF data-harmonization guidelines — making this a
second-country example of harmonized catch/effort data for the Western Indian Ocean region.

## Columns
- survey_id: identifier of the survey/data source the record came from — 1 distinct ∈ {apobg7g9x9c5ZqHbcn69T3}
- trip_id: unique fishing-trip identifier — high-cardinality, 991 distinct (e.g. TRIP_715693918, TRIP_715693927, TRIP_716414848, TRIP_716797347, TRIP_717069214)
- landing_date: date the catch was landed — date, 2025-10-06 → 2026-06-04
- gaul_1_code: GAUL level-1 (province) administrative code — numeric, range 1484–1494 (20 missing)
- gaul_1_name: GAUL level-1 province name — 7 distinct ∈ {Cabo Delgado, Cidade De Maputo, Gaza, Inhambane, Nampula, Sofala, Zambézia} (20 missing)
- gaul_2_code: GAUL level-2 (district) administrative code — numeric, range 104308–104459 (20 missing)
- gaul_2_name: GAUL level-2 district name — 19 distinct ∈ {Angoche, Beira, Bilene, Buzi, Cidade De Maputo, Ibo, Ilha De Moçambique, Inhassoro, Larde, Maxixe, Mecúfi, Moma, Nacala, Namacurra, Pebane, Pemba, Quelimane, Xai-Xai, Zavala} (20 missing)
- n_fishers: number of fishers on the trip — numeric, range 0–48 (117 missing)
- trip_duration_hrs: trip duration in hours — numeric, range 0.35–40.0667 (133 missing)
- gear: fishing gear used — 8 distinct ∈ {Cage Trap, Gill Net, Gleaning, Hand Line, Long Line, Purse Seine, Spear Gun, Trawl Net} (119 missing)
- vessel_type: type of vessel/platform used — 5 distinct ∈ {Dugout Canoe, Flat Boat, Motorized Boat, Planked Canoe, Raft} (130 missing)
- catch_habitat: habitat where the catch was taken — 9 distinct ∈ {3, Estuary, Intertidal zone, Mangrove, Open sea, Reef, Rocky area / Reef base, Seagrass, Shore} (117 missing); see caveats — "3" is a stray erroneous value
- catch_outcome: whether the trip produced a catch (binary flag) — numeric, range 0–1 (117 missing)
- n_catch: number of catch entries/items recorded — numeric, range 1–8 (145 missing)
- catch_taxon: taxon code for the catch — high-cardinality, 191 distinct (e.g. ARQ, AUD, AWX, BAC, BAR) (145 missing)
- scientific_name: scientific (Latin) name of the catch taxon — high-cardinality, 191 distinct (e.g. Acanthuridae, Acetes erythraeus, Actinopterygii, Aesopia cornuta, Alepes djedaba) (145 missing)
- length_cm: catch length in centimetres — numeric, range 7.5–95 (1113 missing)
- catch_kg: weight of the individual catch entry in kilograms — numeric, range 0–3500 (218 missing)
- catch_price: price of the individual catch entry (local currency) — empty throughout (no values recorded)
- tot_catch_kg: total catch weight for the trip in kilograms — numeric, range 0–3500 (368 missing)
- tot_catch_price: total catch value for the trip (local currency) — numeric, range 0–65000 (117 missing)

## Related files
- kenya_validated_trips.csv (sister dataset — the Kenya-coast validated trips with the identical schema and conventions)
- zanzibar_validated_trips.csv (sister dataset — the Zanzibar validated trips with the identical schema and conventions)
- peskas_automated_analytics_softwarex_2025.pdf (the Peskas analytics workflow this data feeds)
- peskas_monitoring_system_slides.pdf (overview of the same monitoring system)
- fishery_nutrient_profiles_timor_leste_naturefood_2026.pdf (Nature Food analysis built on the same kind of Peskas multi-species, multi-gear catch data)
- ../data_harmonization/Technical_Guidelines_SSF_Data_Harmonization_WIO.docx (WIO SSF harmonization standard — this dataset uses its GAUL admin layers and catch/effort variable conventions)

## Notes / caveats
- catch_price is entirely empty: all 1,521 values are missing, so no per-catch price information
  is available for this Mozambique extract (the trip-total tot_catch_price column is still
  populated).
- catch_habitat contains a stray value "3" mixed in among the genuine habitat categories
  (Estuary, Intertidal zone, Mangrove, Open sea, Reef, Rocky area / Reef base, Seagrass, Shore);
  treat "3" as a data-entry error and exclude or correct it before analysis.
- Mozambique habitat categories differ from the Kenya file: this extract adds Estuary,
  Intertidal zone, and Rocky area / Reef base, and does not use Kenya's "Multiple" category — so
  the two countries are not directly comparable on catch_habitat without harmonizing the values.
- catch_outcome is a 0/1 flag, not a continuous measure; rows with catch_outcome = 0 have empty
  catch detail (n_catch, catch_taxon, scientific_name, catch_kg, tot_catch_kg all blank or zero).
- Several catch entries belong to the same trip_id (one row per catch item), so trip-level
  fields (n_fishers, trip_duration_hrs, gear, vessel_type, tot_catch_kg, tot_catch_price) repeat
  across the catch rows of a multi-catch trip.
