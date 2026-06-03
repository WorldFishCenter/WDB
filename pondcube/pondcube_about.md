# PondCube

## Aim

PondCube is a real-time water-quality monitoring system for aquaculture. Digital probes in the tanks continuously record key parameters and stream them to the cloud, where a mobile app lets farm staff watch live conditions and get alerted the moment something drifts out of a safe range.

## How it works

- **Sense.** Digital probes in each tank record temperature and dissolved oxygen continuously (sampling interval to be defined — likely around every 30 minutes).
- **Send.** Probes push their readings to the cloud (Google) through an ingestion API.
- **Serve.** A second API delivers the data from the cloud to a mobile application.
- **Monitor.** The app shows current levels and trends per tank.
- **Alert.** When a parameter crosses its threshold, the system triggers a notification to the app so staff can act fast.

## Why it matters

Water conditions can turn dangerous quickly, and dissolved oxygen in particular can crash within hours. Continuous sensing plus instant alerts means problems are caught early instead of at the next manual check — protecting stock, reducing losses, and freeing staff from constant manual readings.

## Datasets

The July 2025 readings are published as tidy, API-ready CSV files, fully documented in **[pondcube_DATA_DICTIONARY.md](pondcube_DATA_DICTIONARY.md)**:

- `pondcube_measurements_long.csv` — one row per individual measurement (time-series databases, APIs, ML).
- `pondcube_observations_wide.csv` — one row per (location, tank, date, period), a column per parameter (apps, dashboards, human review).
- `pondcube_tanks_reference.csv` — the reference list of every location, zone, and tank (joins, dropdowns, validation).
- `pondcube_data_quality.csv` — the log of data-quality issues found during conversion.

All four were converted from the source workbook `PondCube Source Workbook 2025.7.31.xlsx` by the conversion script. Read `pondcube_DATA_DICTIONARY.md` for the schema, units, and the conventions applied (blank = missing, location-local tank identity, exclusion of derived sheets).

## In short

PondCube connects probe, cloud, and phone into one loop: measure continuously, monitor live, and alert automatically.