# PondCube — Water Quality Dataset (July 2025)

Machine-readable conversion of the paper/Excel log `2025.7.31.xlsx` into tidy, API- and AI-ready datasets.

## Files

| File | What it is | Best for |
|------|------------|----------|
| `pondcube_measurements_long.csv` | **Tidy long format** — one row per single measurement | Time-series databases, APIs, analytics, ML pipelines |
| `pondcube_observations_wide.csv` | **Wide format** — one row per (location, tank, date, period) with a column per parameter | Apps, dashboards, human review, spreadsheets |
| `pondcube_tanks_reference.csv` | Reference list of every location/zone/tank | Joins, app dropdowns, validation |
| `pondcube_data_quality.csv` | Log of data-quality issues found during conversion | QA, source cleanup |
| `convert_pondcube.py` | The reproducible conversion script | Re-running next month's file |

## Source interpretation

The workbook holds **one calendar month, July 2025**. Of its 13 sheets, only **8 are primary source data** — one per physical area:
Hatchery, Fish Tank 1, Fish Tank 2, Fish Tank 3, Block L, Water Storage, Aqua, Pond.

The remaining sheets were **deliberately excluded** because they are derived or reference, not source of truth:

- `Data`, `AVG(am)`, `AVG(pm)`, `Graph` — pivots/aggregations. `Data` additionally has **corrupted headers** (every column mislabeled "Dissolved Oxygen(am)") and **coerces blank readings to `0`** (a DO of 0 is physically impossible in a live tank). Trusting it would inject false zeros.
- `Ammonia` — a NH₃ toxicity **lookup table** (un-ionized ammonia fraction by pH × temperature), useful as a reference calculator but not observational data.

Each source sheet is a human-built matrix: days 1–31 run across the columns in 7-wide blocks (DO, TEMP, pH, Ammonia, Nitrate, Nitrite, Remarks); a **MORNING** block sits above an **AFTERNOON** block; tanks run down the first column.

## Schema — `pondcube_measurements_long.csv`

| Column | Type | Description |
|--------|------|-------------|
| `location` | string | Physical area / source sheet (e.g. `Fish Tank 3`) |
| `zone` | string | Grouping label. `Fish Tank 1/2/3` share zone `Fish Tanks` (continuous tank numbering 1–210); other areas are their own zone |
| `tank_id` | integer | Tank number **within its location** (not globally unique except in the Fish Tanks zone) |
| `tank_id_raw` | string | Original cell content, preserved for traceability (e.g. `90 for FT2`) |
| `date` | date `YYYY-MM-DD` | Reading date (July 2025) |
| `period` | enum | `morning` or `afternoon` |
| `parameter` | enum | `dissolved_oxygen`, `temperature`, `ph`, `ammonia`, `nitrate`, `nitrite` |
| `value` | number | Measured value |
| `unit` | string | See units below |

The natural key is `(location, tank_id, date, period, parameter)`.

## Schema — `pondcube_observations_wide.csv`

`location, zone, tank_id, tank_id_raw, date, period, dissolved_oxygen, temperature, ph, ammonia, nitrate, nitrite, remarks`

One row per (location, tank, date, period). Empty parameter cells mean **no reading was taken** — they are not zeros.

## Units (standard aquaculture)

| Parameter | Unit | Notes |
|-----------|------|-------|
| dissolved_oxygen | mg/L | |
| temperature | °C (`degC`) | |
| ph | pH (unitless) | |
| ammonia | mg/L | Total ammonia as recorded; see `Ammonia` lookup for un-ionized fraction |
| nitrate | mg/L | |
| nitrite | mg/L | |

Units were not stated in the source and are applied as the aquaculture-standard convention. Adjust here if your meters report otherwise.

## Conventions & rules applied

- **Blank = missing.** A blank source cell becomes an absent row (long) or empty cell (wide). It is **never** recorded as 0.
- **Real zeros preserved.** The source contains exactly 5 genuine `0` values, all `nitrate`. These are chemically plausible (undetectable nitrate) and were kept; they are also listed in the QA log so you can confirm none were placeholders.
- **Remarks:** the Remarks columns exist in the template but are **empty throughout** July, so no remark rows were produced.
- **Tank identity:** `tank_id` is local to a location. To reference a tank globally, use the pair `(location, tank_id)`.

## Coverage (July 2025)

- **9,759** individual measurements; **4,334** observation rows; **296** distinct tanks.
- Logging was concentrated in **Fish Tank 3** (2,603 rows), **Hatchery** (577), **Block L** (532), **Fish Tank 2** (447), **Fish Tank 1** (165).
- **Water Storage has no measurements** in July (template scaffolding only); **Aqua** (6 rows) and **Pond** (4 rows) were barely logged. This reflects the real source — not a conversion loss.
- Dominant parameters are dissolved_oxygen (4,288) and temperature (4,285); pH/ammonia/nitrate/nitrite were logged far less often (~260–330 each).

## Data-quality issues flagged

See `pondcube_data_quality.csv`. Notable items: a tank labeled `90 for FT2` (free text in a numeric field, parsed to `90`); Fish Tank 3 skips tank `114`; and the 5 nitrate zeros noted above.

## Forward-compatibility (probes / APIs / cloud)

The long format maps directly onto a time-series/observation model. When live probes come online, append rows with the same columns plus a `timestamp` (replacing or complementing `date`/`period`) and a `source` field (`manual` vs `probe`). Suggested relational shape:

- `locations(location_id, name, zone)`
- `tanks(tank_id, location_id)` — surrogate PK; keep `(location, local_number)` as a natural key
- `measurements(tank_id, observed_at, parameter, value, unit, source)`

This conversion is reproducible: drop next month's workbook in and re-run `convert_pondcube.py`.
