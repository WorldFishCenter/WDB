# Peskas Zanzibar Validated Trips

## Summary

The Zanzibar Validated Trips dataset documents individual fishing trips conducted in Zanzibar waters, validated through the Peskas monitoring system. Each row represents a single catch item recorded during a trip, linking fisher effort (vessel, gear, duration, crew size) to species-level landings with weight and economic value. The dataset captures spatial context (administrative divisions), temporal patterns (landing dates), and fishing characteristics (habitat, gear type) to support fisheries management and livelihood monitoring in the Mjini Magharibi region.

## Columns

- `survey_id`: unique identifier for the monitoring survey or enumerator session that collected this record.
- `trip_id`: unique identifier for a single fishing trip, grouping one or more catch items from the same voyage.
- `landing_date`: calendar date and time when the catch was brought ashore.
- `gaul_1_code`: GAUL (Global Administrative Unit Layers) level-1 code for the first-order administrative division (region) where the landing occurred.
- `gaul_1_name`: name of the level-1 administrative division (region).
- `gaul_2_code`: GAUL level-2 code for the second-order administrative division (district) where the landing occurred.
- `gaul_2_name`: name of the level-2 administrative division (district).
- `n_fishers`: number of fishers aboard the vessel during this trip.
- `trip_duration_hrs`: duration of the fishing trip in hours.
- `gear`: type of fishing gear or equipment used (e.g., Hand Line, Gill Net, Ring Net, Trap, Tangle Net).
- `vessel_type`: category of vessel used (e.g., Dhow, Motorized Boat, Wooden Boat).
- `catch_habitat`: broad habitat or fishing ground type where the catch was taken (e.g., Reef, Open Sea).
- `catch_outcome`: categorical outcome indicator for the catch event.
- `n_catch`: sequential count of the catch item within the trip.
- `catch_taxon`: standardized three-letter code (FAO ASFIS or local code) for the fish taxon or species group.
- `scientific_name`: binomial or genus-level scientific name of the caught taxon.
- `length_cm`: morphometric length measurement of an individual specimen or group, in centimetres.
- `catch_kg`: weight of this specific catch item in kilograms.
- `catch_price`: monetary value attributed to this catch item (currency unit not specified in data; values appear sparse).
- `tot_catch_kg`: total combined weight of all catch from the trip, in kilograms.
- `tot_catch_price`: total monetary value of all catch from the trip.

## Grain

One row represents a single catch item (taxon-specific landing) from a single fishing trip. Multiple rows may share the same `trip_id` when a trip landed more than one species or catch event. Columns `n_fishers`, `trip_duration_hrs`, `gear`, `vessel_type`, `catch_habitat`, `landing_date`, and geographic identifiers (`gaul_1_code`, `gaul_1_name`, `gaul_2_code`, `gaul_2_name`) repeat across all rows of the same trip; `tot_catch_kg` and `tot_catch_price` represent trip-level aggregates and are constant within a trip. To aggregate to trip grain, group by `trip_id` and sum or take the first value of trip-level attributes.

## Related files

- **peskas/zanzibar_raw_trips.csv** — unvalidated raw trip records from Peskas before quality assurance filtering; this validated file is a cleaned subset produced from that source.
- **peskas/zanzibar_fisher_demographics.csv** — demographic and livelihood attributes of individual fishers in the same Zanzibar monitoring program; links fisher identity to trip participation.
- **peskas/zanzibar_vessel_inventory.csv** — registry of fishing vessels operating in Zanzibar waters; complements vessel type and capacity context for trips in this file.