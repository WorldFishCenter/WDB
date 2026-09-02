# Zanzibar Validated Trips

## Summary
This dataset contains validated fishing trip records from Zanzibar, produced by the Peskas initiative. Each record represents a single catch item from a surveyed fishing trip, with information about the trip, vessel, gear, catch, and location. The data is used to monitor and analyze small-scale fisheries in Zanzibar, providing validated estimates of catch weight, price, and species composition.

## Columns
- `survey_id`: Unique identifier for the survey event that collected the trip data.
- `trip_id`: Unique identifier for the fishing trip.
- `landing_date`: Date and time when the trip ended and catch was landed.
- `gaul_1_code`: GAUL administrative level 1 code for the region (Zanzibar's first-level administrative division).
- `gaul_1_name`: Name of the GAUL level 1 administrative region.
- `gaul_2_code`: GAUL administrative level 2 code for the district.
- `gaul_2_name`: Name of the GAUL level 2 administrative district.
- `n_fishers`: Number of fishers on the trip.
- `trip_duration_hrs`: Duration of the fishing trip in hours.
- `gear`: Type of fishing gear used (e.g., Hand Line, Gill Net, Ring Net, Trap, Tangle Net).
- `vessel_type`: Type of vessel used (e.g., Dhow, Motorized Boat, Wooden Boat).
- `catch_habitat`: Habitat where the catch was taken (e.g., Reef, Open Sea).
- `catch_outcome`: Outcome of the catch event (1 = kept, 2 = discarded).
- `n_catch`: Sequential number of the catch item within the trip.
- `catch_taxon`: FAO species code for the caught taxon.
- `scientific_name`: Scientific name of the caught species.
- `length_cm`: Length of the caught individual in centimeters.
- `catch_kg`: Weight of this individual catch item in kilograms.
- `catch_price`: Price of this individual catch item in Tanzanian Shillings.
- `tot_catch_kg`: Total weight of all catch items from the trip in kilograms.
- `tot_catch_price`: Total price of all catch items from the trip in Tanzanian Shillings.

## Grain
One row represents one catch item (individual fish or aggregated catch of a single species) from a validated fishing trip. Multiple rows with the same `trip_id` represent multiple catch items from the same trip. To aggregate to trip level, sum `catch_kg` and `catch_price` across rows with the same `trip_id`, and use the first row's `tot_catch_kg` and `tot_catch_price` for trip totals.

## Related files
- `peskas/zanzibar_trips.csv`: Raw (unvalidated) trip data from which this validated dataset is derived.
- `peskas/zanzibar_validated_trips_metadata.csv`: Metadata describing the validation process and quality flags for these trips.