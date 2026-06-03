# PondCube

PondCube is a **package of work under the [Digital Transformation Accelerator (DTA)](../Digital_Transformation_Accelerator_2025_TR_context.md)** — CGIAR's cross-cutting accelerator for FAIR, AI-ready agricultural data.

## Aim

WorldFish is modernizing its **genetic improvement programs** by moving fragmented, Excel-based datasets — pond books, pedigree data, sampling, and mortality records — into a secure, cloud-based data ecosystem. PondCube establishes a centralized, standards-compliant cloud database that enables real-time data ingestion, validation, and structured analytics across participating hatcheries, breeding centers, and country programs.

The package delivers a scalable data pipeline that integrates manual and sensor-based inputs, automates analytics, and links input use, fish performance, and financials. Visualization dashboards and reporting layers let geneticists, hatchery managers, and partners make data-informed decisions on breeding strategies, resource use, data validation, and program efficiency.

## Scope

- **Unifies genetic improvement workflows** across WorldFish sites (e.g. Bangladesh, Egypt, Zambia) under a single, FAIR-aligned digital system.
- **Improves data quality, reduces duplication, and ensures consistency** in genetic lineage tracking, mortality trends, and environmental factors.
- **Extensible** to public and partner hatchery networks, aligning with CGIAR's scaling ambitions.
- Contributes to CGIAR's digital-readiness indicators and AI-readiness for selective-breeding models, responding to demand from field teams, bilateral partners, and genetic program leads facing bottlenecks from Excel-locked, siloed data systems.

## Environmental monitoring (first data component)

The first concrete dataset is **real-time water-quality monitoring** of tanks — one of the environmental factors PondCube links to fish performance and program efficiency. Digital probes in each tank record key parameters and stream them to the cloud, where a mobile app lets farm staff watch live conditions and get alerted the moment something drifts out of a safe range:

- **Sense.** Probes record temperature and dissolved oxygen continuously (sampling interval to be defined — likely ~every 30 minutes).
- **Send.** Probes push readings to the cloud (Google) through an ingestion API.
- **Serve.** A second API delivers the data to a mobile application.
- **Monitor.** The app shows current levels and trends per tank.
- **Alert.** When a parameter crosses its threshold, the system notifies staff so they can act fast.

Water conditions can turn dangerous quickly — dissolved oxygen in particular can crash within hours — so continuous sensing plus instant alerts catch problems early, protecting stock and freeing staff from constant manual readings.

## Datasets

The July 2025 water-quality readings are published as tidy, API-ready CSV files, fully documented in **[pondcube_DATA_DICTIONARY.md](pondcube_DATA_DICTIONARY.md)**:

- `pondcube_measurements_long.csv` — one row per individual measurement (time-series databases, APIs, ML).
- `pondcube_observations_wide.csv` — one row per (location, tank, date, period), a column per parameter (apps, dashboards, human review).
- `pondcube_tanks_reference.csv` — the reference list of every location, zone, and tank (joins, dropdowns, validation).
- `pondcube_data_quality.csv` — the log of data-quality issues found during conversion.

All four were converted from the source workbook `PondCube Source Workbook 2025.7.31.xlsx` by the conversion script. Read `pondcube_DATA_DICTIONARY.md` for the schema, units, and the conventions applied (blank = missing, location-local tank identity, exclusion of derived sheets).

## In short

PondCube moves WorldFish's genetic-improvement data out of scattered spreadsheets into one FAIR-aligned, cloud-based pipeline — ingesting manual and sensor inputs (starting with tank water quality), validating and analyzing them, and surfacing decisions through dashboards across hatcheries and country programs.
