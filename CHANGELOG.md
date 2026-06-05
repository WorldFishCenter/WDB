# WDB 0.0.1

First versioned release of the WorldFish Digital Brain. Establishes the full
contributing protocol, automated tooling, and the first two indexed initiatives.

## Knowledge Graph Infrastructure

* **NEW** Graphify-based knowledge graph: every file, dataset, and document
  in the repo is indexed into a queryable graph (`graphify-out/graph.html`,
  `GRAPH_REPORT.md`, `graph.json`). Semantic extraction uses the model;
  code is parsed locally with Tree-sitter.
* **NEW** `CLAUDE.md` operator rules: pins the build to `claude-opus-4-8`,
  stamps provenance in `BUILD_INFO.md` on every build, and injects a
  format-blind similarity guard so no edge is ever minted on table shape alone.
* **NEW** `.graphifyignore` excludes workflow/protocol docs from the graph
  so they don't pollute node content with tooling language.

## Contributing Protocol

* **NEW** Project-First placement rule: all material lives inside its
  initiative folder — code, datasets, PDFs, and notes together.
* **NEW** File-naming convention: `lower_snake_case`, descriptive, with year
  and/or region when they apply. Tidy-data requirement for spreadsheets:
  one header row, wide or long shape only.
* **NEW** Context note system: every dataset gets a `_dict.md` companion
  (Template A); every PDF/document gets a `_context.md` (Template B);
  topic or initiative overviews get a standalone `_about.md`.
* **NEW** `_about.md` naming convention: aspect docs are
  `<initiative>_<aspect>_about.md`; the whole-initiative overview reserves
  the bare `<initiative>_about.md` — so a later overview never collides
  with an aspect doc.
* **NEW** Single-builder rule: only the maintainer runs `/graphify` and
  commits `graphify-out/`. Contributors branch → add + document → pull
  request only.

## Automated Tooling

* **NEW** `/curate` command backed by the `wdb-curator` agent: places,
  names, and drafts the context note for any newly added file against the
  full protocol. Run before opening a PR.
* **NEW** `/enrich` command backed by the `dict-enricher` agent: validates
  that a spreadsheet is tidy (wide or long) and fills the `## Columns`
  value domains in `_dict.md` deterministically. Stops with an exact error
  if the shape is invalid.

## Initiatives

* **NEW** Digital Transformation Accelerator (`digital_transformation_accelerator/`):
  first indexed initiative, including the PondCube sub-initiative with wide
  and long observation datasets, data quality notes, and an initiative
  overview.
* **NEW** FASA — Feed Ingredient Composition Database (`fasa/`): FICD
  dataset and repo overview indexed as the second initiative.
