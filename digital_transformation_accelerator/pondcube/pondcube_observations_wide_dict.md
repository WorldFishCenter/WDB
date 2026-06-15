# Data dictionary: pondcube_observations_wide.csv

## Summary
PondCube water-quality readings, built for apps, dashboards, spreadsheets, and human
review (a companion file, pondcube_measurements_long.csv, holds the same readings).
4,334 observation rows, July 2025.

## Grain
One row = one observation — the set of water-quality readings for one tank on one date and reading
slot, keyed by (`location`, `tank_id`, `date`, `period`), with the six parameters as columns.
`tank_id` is local to a location (`tank_id_raw` preserves its original label), so use (`location`,
`tank_id`) to identify a tank globally. No higher-grain measurement repeats across rows — each row is
a distinct observation.

## Columns
- location: physical area / source sheet — 7 distinct ∈ {Aqua, Block L, Fish Tank 1, Fish Tank 2, Fish Tank 3, Hatchery, Pond}
- zone: grouping label (`Fish Tanks` for the three fish-tank locations; otherwise the area's own zone) — 5 distinct ∈ {Aqua, Block L, Fish Tanks, Hatchery, Pond}
- tank_id: tank number within its location (integer) — range 1–209
- tank_id_raw: original cell content preserved for traceability — 171 distinct (e.g. `1`, `10`, `100`, `104`, `105`)
- date: reading date, `YYYY-MM-DD` — 2025-07-01 → 2025-07-30
- period: morning/afternoon reading slot — 2 distinct ∈ {afternoon, morning}
- dissolved_oxygen: DO in mg/L — range 2–9.97 (46 missing)
- temperature: water temperature in °C — range 25.5–114 (49 missing; see caveat — 114 and 59.3 are implausible)
- ph: pH (unitless) — range 5.9–8.94 (4004 missing)
- ammonia: total ammonia in mg/L (see PondCube `Ammonia` lookup for un-ionized fraction) — range 0.11–15.1 (4005 missing)
- nitrate: nitrate in mg/L — range 0–15.4 (4071 missing)
- nitrite: nitrite in mg/L — range 0.001–6.03 (4070 missing)
- remarks: free-text note column — empty throughout July 2025 (no values recorded)

## Related files
- pondcube_measurements_long.csv (the same water-quality readings)
- pondcube_tanks_reference.csv (location/zone/tank lookup)
- pondcube_data_quality.csv (QA issues found during conversion)
- convert_pondcube.py (reproducible script that generated this file)
- pondcube_data_about.md (full source interpretation, conventions, and coverage stats)

## Notes / caveats
- An **empty parameter cell means no reading was taken — it is not a zero.**
- The only genuine zeros are 5 `nitrate` values (plausible undetectable nitrate), preserved and listed in the QA log.
- **Out-of-range values to verify at source (not yet in the QA log):** `temperature` reaches 114 (Fish Tank 3, tank 139, 2025-07-05 AM) and 59.3 (Fish Tank 3, tank 184, 2025-07-24 AM) — implausible for water in °C, likely data-entry errors.
- `remarks` is empty for the whole month, so it carries no information for July 2025 but is retained for forward compatibility.
- `tank_id` is local to a location; use `(location, tank_id)` as the global key.
