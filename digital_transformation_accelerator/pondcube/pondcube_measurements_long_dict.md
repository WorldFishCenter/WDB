# Data dictionary: pondcube_measurements_long.csv

## Summary
Tidy long-format water-quality measurements for the PondCube aquaculture monitoring
system, one row per single reading, covering July 2025. This is the canonical
time-series/ML-friendly shape (a wide pivot lives in pondcube_observations_wide.csv).
9,759 measurements across 296 tanks in 7 logged areas.

## Columns
- location: physical area / source sheet (e.g. `Fish Tank 3`, `Hatchery`, `Block L`, `Aqua`, `Pond`)
- zone: grouping label — `Fish Tank 1/2/3` share zone `Fish Tanks` (continuous numbering 1–210); other areas are their own zone
- tank_id: tank number **within its location** (integer; not globally unique except within the Fish Tanks zone)
- tank_id_raw: original cell content preserved for traceability (e.g. `90 for FT2`)
- date: reading date, `YYYY-MM-DD` (all July 2025)
- period: `morning` or `afternoon`
- parameter: one of `dissolved_oxygen`, `temperature`, `ph`, `ammonia`, `nitrate`, `nitrite`
- value: the measured number
- unit: `mg/L` (DO, ammonia, nitrate, nitrite), `degC` (temperature), unitless (ph)

## Related files
- pondcube_observations_wide.csv (same data, one row per location/tank/date/period with a column per parameter)
- pondcube_tanks_reference.csv (location/zone/tank lookup)
- pondcube_data_quality.csv (QA issues found during conversion)
- convert_pondcube.py (reproducible script that generated this file)
- pondcube_data_about.md (full source interpretation, conventions, and coverage stats)

## Notes / caveats
- Natural key: `(location, tank_id, date, period, parameter)`.
- Blank source cells become **absent rows** — never recorded as 0. The only genuine zeros are 5 `nitrate` readings (chemically plausible, kept and listed in the QA log).
- `tank_id` is local to a location; reference a tank globally with the pair `(location, tank_id)`.
- Units were not stated in the source and follow standard aquaculture convention; adjust if meters report otherwise.
- Logging is uneven: concentrated in Fish Tank 3 (2,603), Hatchery (577), Block L (532); DO and temperature dominate, pH/ammonia/nitrate/nitrite logged far less; Water Storage has no readings in July.
