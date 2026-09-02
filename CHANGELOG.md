# WDB 0.0.4

Separates the **knowledge base** from the **application**. Every initiative folder and the
built graph now live under `knowledge_base/`; the modes, router and services stay in the repo
root and locate the knowledge base through one configurable root instead of assuming it sits
as sibling directories. This is the boundary
[`docs/production-stack-design.md`](docs/production-stack-design.md) §2 recommended, and it
makes the repo publishable as a reusable system: a new user supplies their own
`knowledge_base/`, and nothing else has to change.

## Contributing Protocol

* **CHANGED** Initiative folders live in **`knowledge_base/`**, not the repo root. Paths in
  the protocol are knowledge-base-relative — `peskas/…` means `knowledge_base/peskas/…` on
  disk, and that is how they appear in the graph. `PROTOCOL.md` §3 and the layout tree say so;
  `USER_GUIDE.md` step 2 points contributors at the folder.
* **CHANGED** The maintainer build is **`/graphify knowledge_base --update`** (was
  `/graphify . --update`). Building from the repo root is now wrong, not merely noisy: graph
  paths must stay knowledge-base-relative because the **first path segment is read as an
  initiative name** throughout the system (Mode C derives a table's identity tokens from it;
  the router derives `known_initiatives` from it). A repo-root build would invent a
  `knowledge_base` "initiative" and pollute entity resolution.
* **CHANGED** `.graphifyignore` moved to `knowledge_base/.graphifyignore` and lost its long
  list of application excludes (`mode_a/`, `read-ui/`, `tests/`, `docs/`, …) — those paths are
  outside graphify's root now, so they cannot leak into the corpus at all.

## Application

* **NEW** [`wdb_paths.py`](wdb_paths.py) — the single source of truth for `REPO_ROOT` and
  `KB_ROOT`, replacing the `Path(__file__).parent.parent` walk each module did for itself
  (the coupling design doc §1.3 called out). `KB_ROOT` is overridable with **`WDB_KB`**, so
  the app can be pointed at any knowledge base.
* **CHANGED** Mode A's `GRAPH_PATH`, Mode B's `DEFAULT_ROOT`/`DEFAULT_GRAPH`, Mode C's
  `load_catalog()` default and the router's `WDB_ROOT` all resolve through `wdb_paths`.
  `wdb_api` and `cost_sim` follow transitively.
* **CHANGED** `wdb_ingest` now distinguishes the two roots: `WDB_ROOT` keeps the workflow DB,
  staging and the `.claude/` enricher; `KB_ROOT` receives approved contributions and holds
  `graphify-out/`. Its test fixture mirrors the real layout hermetically.
* **FIXED** Mode B's corpus walk no longer indexes application files. It listed **39** files
  (`RUNNING.md`, `mode_a/MODEL.md`, `proof_a/FINDINGS.md`, …) where the intended corpus is
  **34**; rooting it at the knowledge base removes the leak by construction rather than by
  maintaining a blocklist of the app's own filenames.
* **CHANGED** `read-ui`'s source-viewer sandbox is rooted at the knowledge base (`WDB_KB`)
  instead of the repo. Citation paths are KB-relative, and the route can no longer read
  application source files.

**No graph rebuild.** Because paths stay knowledge-base-relative, `graph.json` is byte-identical
across the move — 172 nodes · 324 edges, unchanged — and no fixture or recorded answer needed
editing.

# WDB 0.0.3

Turns the `_about.md` overview from a free-form note into a structured, connected
node: a light template, a parent⇄child hierarchy between initiative hubs and their
component docs, a clear division of labour between the hub and its companions, and a
**satellite** convention — with one canonical name per initiative — for the extra
perspective docs a project accrues (timelines, notes, roadmaps).

## Contributing Protocol

* **CHANGED** `_about.md` overviews now follow **[Template C](PROTOCOL.md#template-c--initiative-overview-_aboutmd)**
  — a light scaffold, not a free-form note (revises 0.0.2's "no template"). Required
  anchors: a proper-name `# H1` (it becomes the node label), a one-line identity, and a
  `## Related files` block; `## Aim`/`## Scope` are recommended.
* **NEW** Parent⇄child `_about.md` hierarchy. The bare `<initiative>_about.md` is the
  parent hub; each `<initiative>_<aspect>_about.md` is a child component (a data bundle,
  an engine/repo). The link is stated on **both** sides — the child names its parent
  ("part of"), the parent enumerates its children — so the edge extracts as `EXTRACTED`,
  and the hierarchy may nest.
* **NEW** Hub-vs-companion division of labour (extends habit 4). The hub stays about
  *meaning and connections*: schemas / value-lists / units stay in the `_dict.md` and
  engine/app/tooling internals stay in the child engine doc — the hub *delegates*
  ("see `<child>_about.md`"). One carve-out: a verbatim imported external README (e.g.
  `fasa_repo_about.md`) may keep tooling detail if marked with a top `> Source:` line.
* **NEW** Initiative **satellite docs** & the **canonical-name** rule. Beyond the hub, an
  initiative's perspective artifacts (timeline, history, roadmap, design / decision notes)
  are **aspect `_about.md` children**, hub-anchored. Each initiative has **one canonical
  proper name** (the hub's `# H1`) used verbatim in every note — synonyms mint duplicate
  graph nodes, since Graphify's dedup won't merge short/variant labels. Cross-initiative
  links are **concentrated in the hub**, not scattered across satellites (clustering is
  edge-density driven with no pinning, so an outward-linking satellite can be pulled into
  another community). Refines habit 2 for satellites only.

## Documentation

* **NEW** `PROTOCOL.md` §6 gains **Template C** (initiative overview), with a worked
  `fasa_about.md` ⇄ `fasa_repo_about.md` parent/child example; the placement table and
  naming section now point to it.
* **CHANGED** `README.md` and `USER_GUIDE.md` now **name Template C** for the initiative
  overview — in the "What am I adding?" table, the flow diagram, and (README) the
  skeletons note — so it reads in parallel with Template A/B instead of "write freely".
* **NEW** `PROTOCOL.md` §6 gains an *"Initiative perspective docs (satellites) & the
  canonical name"* subsection (canonical-name, hub-anchoring, and cross-initiative-link
  concentration rules + an artifact→convention table); `README.md` and `USER_GUIDE.md`
  each gain a row for project timelines/history/notes that deep-links into it.

## Automated Tooling

* **CHANGED** `wdb-curator` agent now drafts overviews against **Template C** and wires
  the parent⇄child link on **both** sides, applying the hub-vs-companion division of
  labour (and the imported-README `> Source:` carve-out). It now also applies the
  **satellite rules** — uses the hub's canonical name verbatim, anchors satellites to the
  hub, warns when a satellite over-links to other initiatives, and puts provenance
  (`source_url`/`captured_at`) on the doc it describes, never on the hub.
* **NEW** `CLAUDE.md` gains a **canonical-entity guard** (operator/build layer, alongside the
  format-blind similarity guard): an extraction-prompt injection (use the canonical name;
  reference the hub's existing node, don't re-mint the initiative concept) plus a maintainer
  **canonical-id remap** build step that reconciles short-named entities onto existing node ids
  before merge — graphify's dedup won't auto-merge labels under 12 chars. Also states the
  brain's aim (connected, honest, de-duplicated) the guards protect.

## Initiatives

* **NEW** Whole-initiative hubs added: `digital_transformation_accelerator/digital_transformation_accelerator_about.md`
  (DTA, parenting PondCube) and `fasa/fasa_about.md` (FASA, parenting the feed-formulation
  engine doc) — the first parent hubs built under the new hierarchy.
* **NEW** `peskas/peskas_timeline_about.md` — the Peskas 2013→present history & global-scaling
  timeline, standardized into the first **satellite** aspect-`_about.md` child (anchored to the
  `peskas_about.md` hub).

---

# WDB 0.0.2

Adds a standard, protocol-aligned way to record how knowledge changes over
time without mutating immutable originals (issue #1).

## Contributing Protocol

* **NEW** Two tenses of note. A **companion note** (`_dict.md`/`_context.md`)
  is a **frozen snapshot** — append-only, never rewrite its existing sections,
  so it stays a record of its time. A whole-initiative **`<initiative>_about.md`**
  is the **living, present-tense current-state node** — updated in place (git
  history is its provenance). Every evolving initiative should keep one; it is
  the brain's answer to "what is this project *today*?" and a connecting hub.
* **NEW** Supersession convention. On a snapshot whose content moved on, append
  a dated `## Updates` block + a directional `superseded_by`/`supersedes` link
  in `## Related files`. The usual target is the initiative's living
  `_about.md` (current state), not necessarily a brand-new document. A lighter
  form — just linking a snapshot to its `_about.md` — covers "snapshot, project
  has moved on" with no specifics.
* **NEW** Honest, graded dating. Dates may be precise (`2026-06`), coarse
  (`2026`, `~2026`, a range), relational (`since the 2025 paper`), or
  `timing approximate` — never fabricated. The supersession link carries the
  meaning; the date is secondary.
* **NEW** Body-only rule for the link: graphify copies only
  `source_url`/`captured_at`/`author`/`contributor` from a note's YAML
  frontmatter and never edges on it, so the supersession link lives in the
  note body (the only place that is both machine-visible and human-readable);
  `captured_at:` is the one supported as-of stamp when an exact date is known.
  Maps onto Dublin Core `dcterms:isReplacedBy`/`replaces`, FAIR provenance
  (R1.2), and Keep a Changelog form.

## Documentation

* **NEW** `PROTOCOL.md` — the single normative specification for the repo
  (roles, the contribution protocol, placement, naming, tidy data, context
  notes, updates/supersession, how extraction works, and the maintainer/build
  reference). All technical detail now lives here, once.
* **CHANGED** `README.md` and `USER_GUIDE.md` are now lean **practical guides**
  that state each rule briefly and link into `PROTOCOL.md` — accurate, not
  duplicated. Rules live in exactly one place, which removes doc drift (e.g.
  the previously dead `CLAUDE.md` README anchors).
* **CHANGED** Source-of-truth repointed: the `wdb-curator` and `dict-enricher`
  agents and `CLAUDE.md` now cite `PROTOCOL.md` (not `README.md`). `PROTOCOL.md`
  is added to `.graphifyignore` so it stays out of the graph.

## Automated Tooling

* **CHANGED** `wdb-curator` agent now records updates/supersession on request,
  append-only, pointing the snapshot at the initiative's living `_about.md`
  (and offering to create that overview if absent) — so `/curate` makes the
  edits for you. The convention is specified in `PROTOCOL.md` §7 (Template A/B
  gain an optional `## Updates` section) and surfaced in `README.md` /
  `USER_GUIDE.md` (Part 4).

---

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
