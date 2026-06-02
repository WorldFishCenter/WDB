# Data dictionary: ASNS_nutrition_specification_database.csv

## Summary
The ASNS (Aquaculture Species Nutrition Specification) database holds nutritional
requirement specifications — minimum/maximum/ratio constraints — for farmed aquatic
species by life stage and production system. It is the constraint source consumed by
the FASA feed-formulation engine: each active row becomes a constraint in the
least-cost linear program for a chosen (species, production_system, stage) tuple.
~50,700 rows covering 42 species.

## Columns
- species_code: numeric code identifying the species (e.g. 101 = Nile Tilapia)
- species: common name (42 distinct: Nile Tilapia, African Catfish, Atlantic Salmon, Whiteleg Shrimp, Groupers, IMCs, …)
- production_system: rearing system the spec applies to — one of General, General-LowCost, High Omega3, Intensive, RAS, Semi Intensive
- stage_weight: life-stage / weight-band label, e.g. `< 5g (Starter)`, `10-100g (Grower)`, `>1500g (Brood)`
- code: spec code grouped by prefix — PA* proximate (protein, lipid, moisture, ash…), AA* amino acids, ADAAF* digestible amino acids (fish), ED* digestible energy, TX* toxin/anti-nutrient ceilings, plus mineral/fatty-acid codes
- specification: full human name of the spec (e.g. Arginine, Crude Protein)
- short_name: abbreviation (e.g. ARG, CP, LYS)
- unit: measurement unit — %, g, kcal, g/MJ, g/kcal, mg, ug, mmol, ppb, ngWHOTEQ, mg_eq_cathin
- restriction_type: how the value is applied — Minimum, Maximum, or Ratio (ratio specs are linearized in the LP)
- value: the numeric threshold for that spec

## Related files
- FICD_feed_ingredient_composition_database.csv (ingredient nutrient values the constraints act on)
- PAFF_practical_aquaculture_feed_formulation_database_Feed_Formulations.csv and _Calculated_Composition.csv (reference recipes / benchmark)
- FASA_git_README.md (engine that consumes this file; crosswalk maps ASNS code → FICD parameter)

## Notes / caveats
- `stage_weight` is a free-text label that the engine matches **exactly** (the API's `stage` must equal it). There are near-duplicate variants differing only in spacing/case (e.g. `< 5g (Starter)` vs `< 5 g (Starter)`; `5-50g (Pre-grower)` vs `5-50 g (Pre-grower)` vs `5-50g (Pre-Grower)`) — treat these as a data-quality wrinkle when joining or filtering.
- Energy is species-specific: ASNS itself carries the appropriate energy code (e.g. ED02 DE-Omni for Tilapia, ED01 DE-Carni for African Catfish); the crosswalk resolves it to the pelleted/extruded FICD column.
- TX* toxin ceilings (aflatoxin, gossypol, phytic acid, etc.) are always enforced as hard Maximum constraints in the engine, regardless of premix/override settings.
- Don't alter headers — the engine's data loader expects these exact column names.
