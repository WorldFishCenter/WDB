# PondCube — Water Quality Dataset (July 2025)

A machine-readable conversion of PondCube's July 2025 tank water-quality log (source workbook
`PondCube Source Workbook 2025.7.31.xlsx`) into four clean, API- and AI-ready CSVs — the first
concrete dataset of the PondCube monitoring system.

## Source interpretation

The source workbook holds **one calendar month, July 2025**. Of its 13 sheets, only **8 are primary
source data** — one per physical area: Hatchery, Fish Tank 1, Fish Tank 2, Fish Tank 3, Block L,
Water Storage, Aqua, and Pond. Each is a human-built matrix (days 1–31 across the columns, a
**morning** block above an **afternoon** block, tanks down the first column).

The other five sheets were **deliberately excluded** because they are derived or reference, not source
of truth:

- `Data`, `AVG(am)`, `AVG(pm)`, `Graph` — pivots and aggregations. `Data` additionally has corrupted
  headers and coerces blank readings to `0`; trusting it would inject **false zeros** into a live
  tank's record.
- `Ammonia` — a NH₃ toxicity **lookup table** (un-ionized ammonia fraction by pH × temperature),
  useful as a reference calculator but not observational data.

The conversion preserves **blanks as missing — never as 0** (the only genuine zeros are 5 chemically
plausible `nitrate` readings, kept and flagged). The published data therefore reflects a source that
was logged **unevenly** — concentrated in a few tanks, with several areas barely recorded — rather
than any conversion loss.

## Related files

- `pondcube_about.md` — the parent **PondCube** overview this dataset belongs to (part of).
- `pondcube_measurements_long_dict.md`, `pondcube_observations_wide_dict.md`,
  `pondcube_tanks_reference_dict.md`, `pondcube_data_quality_dict.md` — the per-file data dictionaries.
  Each file's **columns, value ranges, units, keys, and caveats live in its `_dict.md`** (filled by `/enrich`).
