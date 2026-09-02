# Peskas Zanzibar Validated Fishing Trips and Catch Data

## Summary
This dataset contains validated fishing trip and catch data collected by the Peskas initiative in Zanzibar. It provides detailed records for individual fishing trips, including trip characteristics, vessel information, and specific catch details such as species, quantity, weight, and price. The dataset exists to monitor and analyze fishing activities and catch composition in the Zanzibar region, supporting fisheries management and research.

## Columns
*   `survey_id`: An identifier for the survey instance that collected the trip data.
*   `trip_id`: A unique identifier for a specific fishing trip.
*   `landing_date`: The date when the fishing trip's catch was landed.
*   `gaul_1_code`: The GAUL (Global Administrative Unit Layers) Level 1 code representing the administrative region where the trip occurred.
*   `gaul_1_name`: The name of the GAUL Level 1 administrative region.
*   `gaul_2_code`: The GAUL Level 2 code representing the administrative district where the trip occurred.
*   `gaul_2_name`: The name of the GAUL Level 2 administrative district.
*   `n_fishers`: The total number of fishers participating in the fishing trip.
*   `trip_duration_hrs`: The duration of the fishing trip, measured in hours.
*   `gear`: The type of fishing gear used during the trip.
*   `vessel_type`: The type of vessel used for the fishing trip.
*   `catch_habitat`: The type of marine habitat where the catch was made.
*   `catch_outcome`: An indicator of the catch outcome, typically `1` for a successful catch.
*   `n_catch`: The number of individual items for the specific catch recorded in this row.
*   `catch_taxon`: The FAO 3-alpha code identifying the caught species or taxon.
*   `scientific_name`: The scientific name of the caught species or taxon.
*   `length_cm`: The length of the caught fish, in centimeters, for the specific catch recorded in this row.
*   `catch_kg`: The total weight of the specific catch recorded in this row, in kilograms.
*   `catch_price`: The total price of the specific catch recorded in this row.
*   `tot_catch_kg`: The aggregated total weight of all catch items for the entire fishing trip, in kilograms.
*   `tot_catch_price`: The aggregated total price of all catch items for the entire fishing trip.

## Grain
One row represents a specific recorded catch event or a group of identical catch items from a fishing trip. The `trip_id` column uniquely identifies a fishing trip, and trip-level attributes such as `landing_date`, `n_fishers`, `trip_duration_hrs`, `gear`, `vessel_type`, `tot_catch_kg`, and `tot_catch_price` repeat for all catch records belonging to the same trip. To obtain total catch weight or price per trip, sum the `catch_kg` or `catch_price` values, respectively, for all rows associated with a distinct `trip_id`.

## Related files
