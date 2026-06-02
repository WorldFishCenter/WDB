# Data dictionary: pondcube_observations_wide.csv

## Summary
Wide-format view of the PondCube water-quality data: one row per
(location, tank, date, period) with a separate column per parameter. Built for apps,
dashboards, spreadsheets, and human review (the long/tidy version is
pondcube_measurements_long.csv). 4,334 observation rows, July 2025.

## Columns
- location: physical area / source sheet (`Aqua`, `Block L`, `Fish Tank 1/2/3`, `Hatchery`, `Pond`)
- zone: grouping label (`Fish Tanks` for the three fish-tank locations; otherwise the area's own zone)
- tank_id: tank number within its location (integer)
- tank_id_raw: original cell content preserved for traceability
- date: reading date, `YYYY-MM-DD` (July 2025)
- period: `morning` or `afternoon`
- dissolved_oxygen: DO in mg/L
- temperature: water temperature in °C
- ph: pH (unitless)
- ammonia: total ammonia in mg/L (see PondCube `Ammonia` lookup for un-ionized fraction)
- nitrate: nitrate in mg/L
- nitrite: nitrite in mg/L
- remarks: free-text note column (present in the template but **empty throughout July 2025**)

## Related files
- pondcube_measurements_long.csv (one row per single reading; canonical tidy form)
- pondcube_tanks_reference.csv (location/zone/tank lookup)
- pondcube_data_quality.csv (QA issues found during conversion)
- convert_pondcube.py (reproducible script that generated this file)
- pondcube_DATA_DICTIONARY.md (full source interpretation, conventions, and coverage stats)

## Notes / caveats
- One row per (location, tank, date, period). An **empty parameter cell means no reading was taken — it is not a zero.**
- The only genuine zeros are 5 `nitrate` values (plausible undetectable nitrate), preserved and listed in the QA log.
- `remarks` is empty for the whole month, so it carries no information for July 2025 but is retained for forward compatibility.
- `tank_id` is local to a location; use `(location, tank_id)` as the global key.
