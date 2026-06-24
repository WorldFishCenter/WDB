# Peskas Zanzibar Validated Trips
## Summary
The Peskas Zanzibar Validated Trips dataset contains detailed records of fishing trips and their catch in Zanzibar, collected through the Peskas monitoring system. It provides information on trip characteristics, fishing effort, and catch composition, including species, quantity, and value. This dataset is produced by the Peskas system and represents validated data from fishing activities in Zanzibar.

## Columns
- `survey_id`: An identifier for the survey instance that collected the trip data.
- `trip_id`: A unique identifier for a specific fishing trip.
- `landing_date`: The date when the fishing trip's catch was landed.
- `gaul_1_code`: The GAUL (Global Administrative Unit Layers) code for the first-level administrative division where the landing occurred.
- `gaul_1_name`: The name of the first-level administrative division where the landing occurred.
- `gaul_2_code`: The GAUL code for the second-level administrative division where the landing occurred.
- `gaul_2_name`: The name of the second-level administrative division where the landing occurred.
- `n_fishers`: The number of fishers participating in the trip.
- `trip_duration_hrs`: The duration of the fishing trip in hours.
- `gear`: The type of fishing gear used during the trip.
- `vessel_type`: The type of vessel used for the fishing trip.
- `catch_habitat`: The habitat where the catch was made.
- `catch_outcome`: An indicator of the catch outcome (e.g., 1 for successful catch).
- `n_catch`: The number of individual catch items recorded for a specific species on the trip.
- `catch_taxon`: A three-letter FAO code representing the taxon of the caught species.
- `scientific_name`: The scientific name of the caught species.
- `length_cm`: The length of the caught species in centimeters.
- `catch_kg`: The weight of the specific catch item in kilograms.
- `catch_price`: The price obtained for the specific catch item.
- `tot_catch_kg`: The total weight of all catch items for the trip in kilograms.
- `tot_catch_price`: The total price obtained for all catch items for the trip.

## Grain
One row represents one specific catch item of a fishing trip. Columns such as `n_fishers`, `trip_duration_hrs`, `gear`, `vessel_type`, `tot_catch_kg`, and `tot_catch_price` repeat for all catch items within the same `trip_id` and should be aggregated over the distinct `trip_id`.

## Related files
- `peskas/zanzibar_raw_trips.csv`