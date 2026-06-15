# Data dictionary: FICD_feed_ingredient_composition_database.csv

## Summary
The FICD (Feed Ingredient Composition Database) holds the nutrient composition of
feed ingredients, one row per (ingredient × parameter). It is the ingredient-side
input to the FASA feed-formulation engine, which reshapes it at runtime to build the
least-cost LP. ~222,150 rows covering 802 ingredient codes and 277 composition
parameters.

## Grain
One row = one composition value (`quantity`) of one nutrient/composition parameter (`ingredient`) for
one feed ingredient (`code`/`description`). `quantity` is at this finest grain; the ingredient
descriptors `code` and `description` repeat across the parameters measured for the same ingredient.

## Columns
- code: ingredient code (802 distinct; the engine's `prices` map and crosswalk key on this)
- description: full ingredient name, e.g. `Fish meal, mixed fish, South Asia, 74% CP`, `Sunflower meal, solvent extract, 23% CP`, `L-Valine` (801 distinct)
- ingredient: **the nutrient/parameter name — NOT the ingredient** (misleadingly named). 277 distinct values, e.g. `dry_matter_percent`, `crude_protein_percent`, `crude_lipids_percent`, `gross_energy_mj_mj_kg`, `de_fish_omni_pelleted_kcal_kg`
- quantity: the measured value of that parameter for that ingredient (units are encoded in the parameter name's suffix, e.g. `_percent`, `_kcal_kg`, `_mj_kg`)

## Related files
- ASNS_nutrition_specification_database.csv (the constraints these compositions must satisfy)
- PAFF_*_Feed_Formulations.csv (reference recipes built from these ingredients)
- fasa_repo_about.md (engine; crosswalk maps ASNS spec code → FICD parameter with unit factor)

## Notes / caveats
- **Watch the column naming:** the column literally headed `ingredient` contains the *parameter* (e.g. `crude_protein_percent`); the actual ingredient lives in `description`/`code`. This trips up naive readers.
- Digestible-energy parameters come in multiple variants by species group and processing method (e.g. `de_fish_carni_*`, `de_fish_omni_*`, `de_carp_*`, `de_shrimp_*`, each in `_pelleted`/`_extruded` forms). The engine selects the correct one via the request's `processing_method` and the ASNS energy code.
- Don't alter headers; the loader expects exact column names.
