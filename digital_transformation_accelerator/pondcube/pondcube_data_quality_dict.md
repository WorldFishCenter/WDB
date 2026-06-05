# Data dictionary: pondcube_data_quality.csv

## Summary
Log of data-quality issues found while converting the July 2025 PondCube source
workbook into the published datasets. Used for QA and source cleanup; small by design
(one row per flagged issue).

## Columns
- location: physical area / source sheet where the issue was found (e.g. `Fish Tank 2`)
- period: `morning` or `afternoon` block the issue occurred in
- row: source row index where the anomaly was detected
- issue: plain-English description of the problem (e.g. `non-numeric tank label: '90 for FT2'`)

## Related files
- pondcube_measurements_long.csv and pondcube_observations_wide.csv (the converted data these issues refer to)
- pondcube_tanks_reference.csv (tank identities, incl. the flagged anomalies)
- convert_pondcube.py (the conversion that emits this log)
- pondcube_data_about.md (full conventions and coverage context)

## Notes / caveats
- Notable flagged items: a `90 for FT2` free-text label in a numeric tank field (parsed to `90`), and the 5 genuine `nitrate` zeros confirmed as real (not placeholders).
- This log is intentionally short — it records exceptions, not every cell; absence of a row means no issue was detected there.
