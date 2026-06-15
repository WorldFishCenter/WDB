# Data dictionary: PAFF_practical_aquaculture_feed_formulation_database_Feed_Formulations.csv

## Summary
The PAFF (Practical Aquaculture Feed Formulation) "Feed Formulations" table holds
reference feed recipes — the ingredient inclusion percentages of practical, published
formulations for each species and life stage. In the FASA engine these recipes are
the **benchmark gate**: the engine independently recomputes their composition and must
reproduce the published numbers, validating the data-loading and crosswalk pipeline.
619 rows across 36 species/stage tuples and 61 ingredient codes.

## Grain
One row = one ingredient line of a reference recipe — the inclusion (`inclusion_percent`) of one
ingredient (`iaffd_code`) in one species/stage formulation (`species`). The row is finer than
`iaffd_code` (≈10.15 rows per code): `ingredient` is fixed by `iaffd_code` and repeats across the
recipes that use that code — aggregate ingredient-level facts over distinct `iaffd_code`, not raw
rows. `species` and `inclusion_percent` vary row to row.

## Columns
- species: species + life-stage label, e.g. `Nile Tilapia - Starter`, `Whiteleg Shrimp - Grower`, `African Catfish` (36 distinct)
- iaffd_code: IAFFD ingredient code for the recipe line (61 distinct; resolved to FICD ingredients via the crosswalk)
- ingredient: ingredient name, e.g. `Fish meal, sardine, 66% CP`, `Poultry by-product meal, feed-grade, 60% CP`
- inclusion_percent: that ingredient's share of the recipe, as a percent of the formulation

## Related files
- PAFF_practical_aquaculture_feed_formulation_database_Calculated_Composition.csv (the resulting nutrient composition of these recipes)
- FICD_feed_ingredient_composition_database.csv (ingredient nutrient values used to recompute composition)
- ASNS_nutrition_specification_database.csv (the targets these recipes are designed against)
- fasa_repo_about.md (engine; "PAFF benchmark gate")

## Notes / caveats
- The `species` field bundles species **and** life stage in one string (`<Species> - <Stage>`); some species (e.g. African Catfish, Channel Catfish, Snakehead) appear without a stage suffix.
- `iaffd_code` is the IAFFD coding scheme, not the FICD `code`; the engine's crosswalk maps between them.
- This is reference/benchmark data — recipes are published practical formulations, not engine output.
