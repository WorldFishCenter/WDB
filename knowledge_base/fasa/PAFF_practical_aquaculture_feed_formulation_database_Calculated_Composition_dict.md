# Data dictionary: PAFF_practical_aquaculture_feed_formulation_database_Calculated_Composition.csv

## Summary
The calculated nutrient composition of the PAFF reference feed recipes — i.e. what
each published formulation in the Feed_Formulations table delivers nutritionally.
In the FASA engine these values are the **correctness target**: the engine recomputes
composition from FICD ingredient data and must match these numbers (the PAFF benchmark
gate). 1,296 rows across 36 species/stage tuples and 36 nutrients.

## Grain
One row = one calculated nutrient value (`value`) for one recipe (`species`, a species/stage label),
in one `unit` — i.e. one (species × nutrient × unit) cell (energy appears in both MJ/kg and kcal/kg
rows, so `unit` is part of the key). `value` is at the finest grain; no higher-grain column repeats
across rows.

## Columns
- nutrient: the nutrient/composition metric, e.g. `Crude Protein`, `Crude Lipid`, `Digestible P`, `Dig CP -fish`, `EPA+DHA`, `Calcium`, `Arginine`, `DE Fish Carni MJ` (36 distinct: proximates, amino acids, fatty acids, energy, minerals)
- unit: measurement unit — `%`, `MJ/kg`, `kcal/kg`, or `mg`
- value: the computed amount of that nutrient in the recipe
- species: species + life-stage label matching Feed_Formulations, e.g. `Nile Tilapia - Starter`

## Related files
- PAFF_practical_aquaculture_feed_formulation_database_Feed_Formulations.csv (the recipes these compositions are computed from)
- FICD_feed_ingredient_composition_database.csv (ingredient nutrient source for recomputation)
- ASNS_nutrition_specification_database.csv (the specs the recipes are compared against)
- fasa_repo_about.md (engine; validator.py recomputes and gates on these)

## Notes / caveats
- `species` joins 1:1 to the Feed_Formulations `species` field (same `<Species> - <Stage>` convention).
- Energy appears in both MJ/kg and kcal/kg rows for the same recipe — filter by `unit` when comparing.
- This is reference/benchmark output, not engine-generated formulations.
