# Data dictionary: pondcube_measurements_long.csv

## Summary
Water-quality measurements for the PondCube aquaculture monitoring system, covering
July 2025 (a companion file, pondcube_observations_wide.csv, holds the same readings).
9,759 measurements across 296 tanks in 7 logged areas.

## Grain
One row = one water-quality measurement — a single `parameter` value (`value`) for one (`location`,
`tank_id`, `date`, `period`), with `unit` following the parameter. `value` is at this finest grain;
the dimension columns repeat across the parameters measured in the same slot.

## Columns
- location: physical area / source sheet — 7 distinct ∈ {Aqua, Block L, Fish Tank 1, Fish Tank 2, Fish Tank 3, Hatchery, Pond}
- zone: grouping label — `Fish Tank 1/2/3` share zone `Fish Tanks` (continuous numbering 1–210); other areas are their own zone — 5 distinct ∈ {Aqua, Block L, Fish Tanks, Hatchery, Pond}
- tank_id: tank number **within its location** (integer; not globally unique except within the Fish Tanks zone) — range 1–209
- tank_id_raw: original cell content preserved for traceability (e.g. `90 for FT2`) — 171 distinct
- date: reading date, `YYYY-MM-DD` (all July 2025) — 2025-07-01 → 2025-07-30
- period: morning/afternoon reading slot — 2 distinct ∈ {afternoon, morning}
- parameter: the measured variable — 6 distinct ∈ {ammonia, dissolved_oxygen, nitrate, nitrite, ph, temperature}
- value: the measured number (range per parameter listed below)
- unit: `mg/L` (DO, ammonia, nitrate, nitrite), `degC` (temperature), `pH` (ph)

**Value range per parameter:**
- ammonia: 0.11–15.1 mg/L (n=329)
- dissolved_oxygen: 2–9.97 mg/L (n=4288)
- nitrate: 0–15.4 mg/L (n=263)
- nitrite: 0.001–6.03 mg/L (n=264)
- ph: 5.9–8.94 pH (n=330)
- temperature: 25.5–114 degC (n=4285) — 114 and 59.3 are implausible for water; likely data-entry errors (see caveat)

## Related files
- pondcube_observations_wide.csv (the same water-quality readings)
- pondcube_tanks_reference.csv (location/zone/tank lookup)
- pondcube_data_quality.csv (QA issues found during conversion)
- convert_pondcube.py (reproducible script that generated this file)
- pondcube_data_about.md (full source interpretation, conventions, and coverage stats)

## Notes / caveats
- Natural key: `(location, tank_id, date, period, parameter)`.
- Blank source cells become **absent rows** — never recorded as 0. The only genuine zeros are 5 `nitrate` readings (chemically plausible, kept and listed in the QA log).
- `tank_id` is local to a location; reference a tank globally with the pair `(location, tank_id)`.
- Units were not stated in the source and follow standard aquaculture convention; adjust if meters report otherwise.
- **Out-of-range values to verify at source (not yet in the QA log):** two `temperature` readings are implausible for water in °C — 114 (Fish Tank 3, tank 139, 2025-07-05 AM) and 59.3 (Fish Tank 3, tank 184, 2025-07-24 AM) — likely data-entry errors.
- Logging is uneven: concentrated in Fish Tank 3 (2,603), Hatchery (577), Block L (532); DO and temperature dominate, pH/ammonia/nitrate/nitrite logged far less; Water Storage has no readings in July.
