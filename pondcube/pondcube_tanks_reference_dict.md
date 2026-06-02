# Data dictionary: pondcube_tanks_reference.csv

## Summary
Reference list of every location/zone/tank in the PondCube dataset — the lookup table
for joins, app dropdowns, and validation. 296 distinct tanks across the logged areas
(July 2025 source).

## Columns
- location: physical area / source sheet (`Aqua`, `Block L`, `Fish Tank 1/2/3`, `Hatchery`, `Pond`, `Water Storage`)
- zone: grouping label — `Fish Tanks` for the three fish-tank locations (continuous numbering 1–210); other areas are their own zone
- tank_id: tank number within its location (integer)

## Related files
- pondcube_measurements_long.csv and pondcube_observations_wide.csv (the measurements that key on these tanks)
- pondcube_data_quality.csv (QA issues, incl. tank-labeling anomalies)
- convert_pondcube.py (reproducible script that generated this file)
- pondcube_DATA_DICTIONARY.md (full source interpretation and coverage stats)

## Notes / caveats
- The pair `(location, tank_id)` is the global key — `tank_id` alone is not unique across locations (except within the `Fish Tanks` zone, which is continuously numbered).
- Fish Tank 3 skips tank `114`; a Fish Tank 2 cell labeled `90 for FT2` was parsed to tank `90` (see QA log).
- `Water Storage` appears here as template scaffolding but has no measurements in July 2025.
