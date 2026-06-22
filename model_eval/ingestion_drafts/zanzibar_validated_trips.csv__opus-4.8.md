# Zanzibar Validated Small-Scale Fisheries Landing Trips (Peskas)

## Summary
This dataset, curated by Peskas, contains validated small-scale fisheries landing survey records for Zanzibar, Tanzania. Each record links an enumerator-administered landing survey to a fishing trip and its catch, capturing where and when the trip landed, the fishing effort and gear used, the vessel and habitat fished, and the taxon-level composition of the catch including weight and price. The data exists to support fisheries monitoring and management for Zanzibar by Peskas, providing cleaned and validated trip-and-catch observations rather than raw survey submissions.

## Columns
- `survey_id`: Identifier of the landing survey submission from which the trip and catch records were collected.
- `trip_id`: Identifier of the individual fishing trip described by the record.
- `landing_date`: Date (with timestamp) on which the trip's catch was landed.
- `gaul_1_code`: Numeric administrative-area code for the first-level (region) division under the GAUL geographic coding scheme.
- `gaul_1_name`: Name of the first-level (region) administrative area where the landing occurred.
- `gaul_2_code`: Numeric administrative-area code for the second-level (district) division under the GAUL geographic coding scheme.
- `gaul_2_name`: Name of the second-level (district) administrative area where the landing occurred.
- `n_fishers`: Number of fishers who participated in the trip.
- `trip_duration_hrs`: Duration of the fishing trip in hours.
- `gear`: Type of fishing gear used on the trip.
- `vessel_type`: Type of vessel used for the trip.
- `catch_habitat`: Habitat from which the catch was taken.
- `catch_outcome`: Coded outcome/status field associated with the catch record; exact meaning not documented in the file.
- `n_catch`: Sequence/count field indexing catch items within the trip; its precise meaning is not documented in the file.
- `catch_taxon`: Short taxon code identifying the catch group.
- `scientific_name`: Scientific name of the catch taxon (species, genus, or higher group).
- `length_cm`: Recorded length of the catch in centimeters; may be unrecorded for some catch records.
- `catch_kg`: Weight in kilograms attributed to this individual catch record.
- `catch_price`: Price attributed to this individual catch record; may be unrecorded.
- `tot_catch_kg`: Total catch weight in kilograms for the whole trip.
- `tot_catch_price`: Total catch price (value) for the whole trip.

## Grain
One row = one taxon-level catch record within a fishing trip. Trip-level attributes (`survey_id`, `landing_date`, geographic GAUL columns, `n_fishers`, `trip_duration_hrs`, `gear`, `vessel_type`, `tot_catch_kg`, `tot_catch_price`) repeat across all catch rows of the same `trip_id`; to aggregate trip-level effort, total weight, or total value, take one value per distinct `trip_id` rather than summing across raw rows.

## Related files
- Other Peskas validated landing datasets for additional monitored geographies (regional counterparts to this Zanzibar file), if present in the repository.
- Peskas raw/unvalidated survey submissions for Zanzibar that this validated dataset is derived from, if present.
- Peskas taxon/gear reference or lookup tables that decode `catch_taxon` codes and standardize `gear`/`vessel_type` values, if present.
- GAUL administrative-area reference tables that resolve `gaul_1_code`/`gaul_2_code`, if present.