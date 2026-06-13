# WDB Protocol — the normative specification

This file is the **single source of truth** for how the WorldFish Digital Brain (WDB) repo is
organised, documented, and built. It is the authoritative, complete version of every rule.

- **Humans** read the practical guides, which state these rules briefly and link back here:
  [README.md](README.md) (contributors) and [USER_GUIDE.md](USER_GUIDE.md) (non-coders, click-by-click).
- **Claude and the agents** (`wdb-curator`, `dict-enricher`) enforce this file.
- **[CLAUDE.md](CLAUDE.md)** carries the **build-operator** rules (model pinning, provenance, the
  extraction similarity guard) and cites this file for conventions.

If a guide and this file ever disagree, **this file wins** — fix the guide.

This file is `.graphifyignore`d (like the other workflow docs), so its workflow/tooling language never
pollutes the knowledge graph.

## Contents
1. [Roles and the single-builder rule](#1-roles-and-the-single-builder-rule)
2. [The contribution protocol](#2-the-contribution-protocol)
3. [Project-First placement](#3-project-first-placement)
4. [Naming](#4-naming)
5. [Tidy data](#5-tidy-data)
6. [Context notes](#6-context-notes)
7. [Recording updates and supersession over time](#7-recording-updates-and-supersession-over-time)
8. [How graphify extraction works](#8-how-graphify-extraction-works)
9. [Maintainer and build reference](#9-maintainer-and-build-reference)
10. [Quick command reference](#10-quick-command-reference)

---

## 1. Roles and the single-builder rule

The repo is a shared Graphify knowledge graph that is **generated *and* committed**, so the team shares
one map without everyone rebuilding. Two roles:

- **Contributor** — anyone adding material. Places, names, and documents a file; self-checks it with
  **`/curate`** and **`/enrich`**; commits **source files only**; opens a **pull request**. Never
  builds the graph.
- **Maintainer** — the one **build owner**. Reviews and merges PRs, then runs the graph build
  (`/graphify`) and commits the regenerated `graphify-out/`. Because only one person regenerates the
  large `graph.*` files, there are no merge conflicts; everyone else just pulls.

This **single-builder rule** is what keeps the shared map consistent. The PR is the only path to `main`.

**This repo runs on Claude Code.** The `/curate` and `/enrich` commands (`.claude/commands/`), the
`wdb-curator` and `dict-enricher` agents (`.claude/agents/`), and the `CLAUDE.md` operator rules are
Claude Code features; other assistants won't read them. The maintainer runs the build on a **pinned
Opus** (`claude-opus-4-8`) for reproducible extraction (see [§9](#9-maintainer-and-build-reference)).

---

## 2. The contribution protocol

Follow these steps **exactly, every time**. Steps 1–6 are the contributor's; step 7 is the
maintainer's. They are identical from the command line or from the click-by-click
[USER_GUIDE.md](USER_GUIDE.md).

1. **Sync & branch.** Pull `main`, then create a branch named `yourname/short-topic`.
2. **Pick the initiative folder.** Put the file in the matching `initiative/` folder
   ([§3](#3-project-first-placement)). If none fits, create one at the repo root in `lower_snake_case`.
   If unsure which initiative it belongs to, **ask the maintainer — don't guess.**
3. **Add the file, named by the rule** ([§4](#4-naming)). Tabular data must be **tidy**
   ([§5](#5-tidy-data)).
4. **Write its context note** ([§6](#6-context-notes)) — **required for every dataset, PDF, and
   document** (recommended for images and audio/video). Running **`/curate`** drafts it for you against
   these rules; you review it. Name it by **replacing the source file's extension** with `_dict.md`
   (tabular) or `_context.md` (everything else). **Fill every section** — especially **Related files**.
   When a source's knowledge later changes, **append** an update rather than editing the original
   ([§7](#7-recording-updates-and-supersession-over-time)).
5. **Validate tables with `/enrich`** ([§5](#5-tidy-data)). For every `.csv`/`.xlsx`, run
   **`/enrich <file>`**: it gates the shape (and **stops and says exactly what to fix** if the table
   isn't tidy) and fills the dictionary's `## Columns` value domains deterministically.
6. **Commit source files only, then open a pull request.** Never commit anything under `graphify-out/`.
7. **Maintainer rebuilds.** After merge, the maintainer runs `/graphify . --update` and commits the
   regenerated `graphify-out/` ([§9](#9-maintainer-and-build-reference)).

### Order of the two checks: `/curate` → then `/enrich`

They are **sequential, not interchangeable**:
- **`/curate` (step 4)** places/names the file and **drafts its context note**. For a table it writes
  the prose meaning per column but **deliberately leaves the `## Columns` value domains blank** — those
  are the tool's job.
- **`/enrich` (step 5)** runs *after* it and **only on tables**: it (1) gates the shape and (2) **fills
  the value domains into the `_dict.md` that `/curate` just drafted**. Running `/enrich` on a table
  with no `_dict.md` yet has nothing to fill — which is why curate comes first.
- **Non-tabular files** (PDFs, docs, images) use **`/curate` only**.
- If the shape gate **fails**, reshape the table and re-run **`/enrich`** (no need to redo `/curate`).

### What am I adding?

| What you're adding | Where it goes | Context note |
|---|---|---|
| Dataset / spreadsheet (`.csv`, `.xlsx`) | initiative folder; don't edit headers; **tidy — one header row, wide or long** | **Required** — Template A (`…_dict.md`); run **`/enrich`** |
| Report / paper / document (`.pdf`, `.docx`, `.md`, `.txt`) | initiative folder; keep a paper's real title | **Required** — Template B (`…_context.md`) |
| Image / diagram / screenshot | initiative folder | Required if it carries information — Template B |
| Audio / video | initiative folder | Required if it's hard to follow — Template B |
| External link / online paper / video / repo | — | Don't save a URL — the maintainer runs `/graphify add <url>` ([§9](#9-maintainer-and-build-reference)) |
| A topic / initiative overview (not about one file) | initiative folder | Standalone `_about.md` — **Template C** + `## Related files`; the bare `<initiative>_about.md` overview is the **living current-state node** ([§6](#6-context-notes)) |
| An idea / observation | initiative folder | The note *is* the content: `idea_<topic>.md` |

### Pre-PR checklist

- [ ] File is in the correct **initiative folder**
- [ ] Name is **`lower_snake_case`**, descriptive (year/region if relevant)
- [ ] Ran **`/curate`** — placement, name, and context note conform
- [ ] **Tabular data is tidy** (wide or long) and passed **`/enrich`**
- [ ] **Context note** present where required, with **every section filled** (table domains by `/enrich`)
- [ ] **Related files** lists real siblings (+ a cross-initiative link where one exists)
- [ ] Only **source files** staged — nothing under `graphify-out/`
- [ ] On **my branch**, opening a **pull request** — not committing to `main`

---

## 3. Project-First placement

Group materials by **initiative**, not by file format.

- **Correct:** `project_kenya_pilot/` holds that pilot's code, datasets, PDFs, and notes together.
- **Avoid:** a single `datasets/` folder mixing unrelated projects.

Every file lives inside the initiative folder it belongs to — never loose at the root, never in a
format-based folder; sub-packages nest (e.g. `digital_transformation_accelerator/pondcube/`). This
keeps related concepts physically close, producing a tighter graph. If the right initiative is
**ambiguous, ask the maintainer — don't guess.**

---

## 4. Naming

**`lower_snake_case`, descriptive, with year and/or region when they apply.**
✅ `kenya_yield_2025.csv`  ❌ `data.csv`, `Final Report.pdf`.

- Don't edit spreadsheet headers; keep a published paper's real title.
- A context note is named by **replacing the source file's extension** — `kenya_yield_2025.csv` →
  `kenya_yield_2025_dict.md`; `report.pdf` → `report_context.md`.

---

## 5. Tidy data

Every spreadsheet must be **one tidy table with a single header row**, in exactly one of two shapes —
this is what makes value domains extractable and keeps badly-shaped data out of the graph:

- **Wide** — one row per entity (e.g. per location/tank/date), **one column per variable**.
  Example: `pondcube_observations_wide.csv`.
- **Long** ("tidy long") — a `variable`/`parameter` column **+** a `value` column (+ optional `unit`),
  **one row per measurement**. Example: `pondcube_measurements_long.csv`.

**Not allowed** (reshape before adding): multi-row or merged-cell headers, metadata/title rows above
the header, several tables stacked in one sheet, ragged rows, pivot/crosstab dumps.

**`/enrich`** runs a deterministic check (`.claude/scripts/dict_enricher.py`) that **flags exactly what
is wrong** rather than guessing — run it as your data-validity check before opening a PR. Shape is
re-detected on every run, so it never needs writing into a note. *(Why tidy: Wickham, "Tidy Data",
J. Stat. Soft. 59(10), 2014.)*

| File type | Where it goes | Notes |
|---|---|---|
| Code | project folder | Parsed locally (no API). Inline comments (`# NOTE:`, `# WHY:`, `# HACK:`) and docstrings become linked nodes — write context there. |
| Docs (`.md`, `.txt`, `.html`) | project folder | Sent to the model for semantic extraction. |
| Tabular (`.csv`, `.xlsx`) | project folder; don't alter headers; **tidy** | Needs `graphifyy[office]` for `.xlsx`. Run **`/enrich`**. |
| PDFs | project folder | Needs `graphifyy[pdf]`. |
| Images (`.png`, `.jpg`) | project folder | Read via the model's vision step. |
| Video / audio | project folder | Transcribed locally; needs `graphifyy[video]`. |
| External papers / videos / repos | — | Maintainer runs `/graphify add <url>` or `graphify clone <repo>`. Don't paste URLs into files. |

---

## 6. Context notes

Companion notes are the **highest-leverage** thing you can add: each `.md` is itself graphed, so a note
turns a lone file into a well-connected node. A note is **required for every dataset, PDF, and document**
(recommended for images and audio/video). The `## Related files` line is where you hand Graphify its
edges — fill it with real siblings, and **cross-link across initiative folders**, not just within one.

### Two kinds of note, and two tenses

**Two kinds.** Most are **companion notes** describing one specific file — `<file>_dict.md` (tabular)
or `<file>_context.md` (anything else). A document describing a **topic or whole initiative** rather
than one file is a standalone **`_about.md`**: an aspect doc is `<initiative>_<aspect>_about.md`
(e.g. `pondcube_data_about.md`, `fasa_repo_about.md`); the bare `<initiative>_about.md` is reserved for
the single whole-initiative overview (e.g. `pondcube_about.md`). Both follow **Template C** (below): a
light scaffold whose required anchors are a proper-name `# H1`, a one-line identity, and a `## Related
files`. The two suffix forms are a **parent⇄child hierarchy** — the bare `<initiative>_about.md` is the
parent hub; each `<initiative>_<aspect>_about.md` is a child that names its parent ("part of") while the
parent enumerates its children, stated on **both** sides so the edge is `EXTRACTED`. The hierarchy may
nest. Never give an overview a `_dict`/`_context` suffix — that
suffix means "companion to the file of that name."

**Two tenses — this is how the brain stays current.**
- A **companion note is a frozen snapshot**: it records what its file said *as of when it was added*.
  You only ever **append** to it — never rewrite its `## Summary`/`## Columns`/`## Key concepts`, since
  the artifact is an immutable record of its time.
- A **whole-initiative `_about.md` is the living, present-tense node**: it describes the initiative *as
  it is now* and is **updated in place** — git history is its provenance, so nothing is lost. Every
  actively-evolving initiative should keep one; it is the brain's answer to "what is this project
  *today*?" and, because it gathers the initiative's files + cross-initiative links, it becomes a
  **hub** — the connections the graph exists to surface. It is also the natural target a stale snapshot
  is **superseded by** ([§7](#7-recording-updates-and-supersession-over-time)).

### Get the best graph — four habits

The graph's value is the **connections** Graphify finds, and it can only connect what your files make
*explicit* (it does **not** infer links from filenames or folder layout):

1. **State relationships in words**, naming *both* sides (produced by X, builds on Y, shares approach Z).
2. **Treat `## Related files` as the wiring — and cross-link across initiatives.** Cross-initiative
   links are the most valuable connections in the graph.
3. **Capture the "why,"** not just the "what" (design decisions, trade-offs, how a thing is used).
4. **Describe what a file is *about*, not its *container* — and never put tooling in a note.** A note
   carries the data's **meaning and relationships**, not its **format** (a table's wide/long shape,
   encoding, file type) or **provenance** (which script or `/`-command produced/enriched it,
   column-role mechanics). Format is shared by every file of that form, so emphasizing it mints
   *quadratic, uninformative* cross-file links — every long table tied to every other long table.
   Keep shape/tooling out of `_dict.md`/`_context.md`. Habit 4 governs the *input*; the **format-blind
   similarity guard** in [CLAUDE.md](CLAUDE.md) governs the *extractor* (a `_dict.md` still reveals
   shape through its column list, node label, and filename). **Both are required.**

### Template A — tabular data (`.csv`, `.xlsx`)

Name it the file's name with its extension replaced by `_dict.md`. Describe what each column **means**
and record its **value domain** in `## Columns`. **You don't hand-type the domains** — run **`/enrich`**
and it fills them deterministically (the maintainer reviews). Per habit 4, keep the table's **shape**
and any **tooling/provenance** *out* of the note.

```markdown
# Data dictionary: kenya_yield_data_2025.csv

## Summary
One or two sentences: what this dataset tracks and which project it belongs to.

## Columns
- column_name: plain-English meaning — value domain (distinct set, or count +
  examples, or numeric/date range)
- column_name: plain-English meaning — value domain

## Related files
- related_file_1, related_file_2

## Notes / caveats
Missing values, known skew, units, or logic the assistant should know when reading it.

<!-- Optional, append-only, newest first — add only when the data is later revised/superseded. See §7. -->
## Updates
- **<as precise as you honestly know>** — what changed; which part is superseded_by
  `<newer source, usually the initiative's living _about.md>`; what still holds.
```

**Filled example** (note the value domains and the cross-initiative link):

```markdown
# Data dictionary: kenya_yield_2025.csv

## Summary
Maize yields from the 2025 Kenya pilot. Part of the project_kenya_pilot initiative.

## Columns
- plot_id: unique plot identifier (joins to field_map.png) — identifier, 312 distinct
- harvest_date: harvest date (YYYY-MM-DD) — 2025-02-14 → 2025-08-03
- yield_kg: harvested maize, kilograms — range 0.4–88.6 (12 missing)
- variety: seed variety planted — 4 distinct ∈ {DK8031, H614, Pioneer 30G19, SC Duma}

## Related files
- field_map.png (plot locations for plot_id)
- ingest_yields.py (the script that produced this file)
- ../project_zanzibar/catch_data.xlsx (sister pilot — same survey design)

## Notes / caveats
Blank yield_kg means not-yet-harvested, not zero. Three plots were re-measured.
```

### Template B — everything else (PDFs, docs, images, audio/video)

Name it the file's name with its extension replaced by `_context.md`.

```markdown
# Context: grant_proposal_kenya.pdf

## Summary
One or two sentences: what this file is and why it's in the workspace.

## Key concepts / entities
- Regions, methods, or topics this file is about

## Related files
- related_file_1, related_file_2

<!-- Optional, append-only, newest first — add only when the source is later revised/superseded. See §7. -->
## Updates
- **<as precise as you honestly know>** — what changed; which part is superseded_by
  `<newer source, usually the initiative's living _about.md>`; what still holds.
```

**Filled example** (note the cross-initiative links):

```markdown
# Context: grant_proposal_kenya.pdf

## Summary
2025 funding proposal for the Kenya yield pilot — objectives, budget, and the
nutrient-sensitive breeding rationale behind project_kenya_pilot.

## Key concepts / entities
- Nutrient-sensitive maize breeding; smallholder yield gaps; Kenya pilot sites
- Builds on the FAIR data-collection methods in ../data_harmonization/

## Related files
- kenya_yield_2025.csv (the dataset this proposal funded)
- ../digital_transformation_accelerator/ (shared FAIR / cloud-data approach)
```

### Template C — initiative overview (`_about.md`)

Unlike the frozen A/B snapshots, an `_about.md` is the **living, present-tense node** for a topic or
whole initiative — **updated in place** (git is its history) and the natural `superseded_by` target a
stale snapshot points to ([§7](#7-recording-updates-and-supersession-over-time)). It is a **light
scaffold, not a fill-in form**: write the body freely, but always include the three **required
anchors** — a proper-name `# H1` (it becomes the node's label), a one-line identity, and a
`## Related files` block (the wiring).

`_about.md` docs form a **parent⇄child hierarchy** and the naming encodes the rank: the bare
`<initiative>_about.md` is the **parent hub**; each `<initiative>_<aspect>_about.md` is a **child** (one
component — a data bundle, an engine/repo). State the link on **both** sides so the edge is `EXTRACTED`:
the child names its parent in `## Related files` ("part of `<initiative>_about.md`") and the parent
**enumerates its children**. The hierarchy nests (an aspect hub can itself parent a finer one).

**Keep the hub about *meaning and connections*, not mechanics** — habit 4 applies here too. Schemas,
column/value lists, units, and coverage counts belong in the relevant `_dict.md` (filled by `/enrich`);
engine/app internals, quickstart, API, deployment, CI, and file-trees belong in the child engine/repo
doc — the hub *delegates* to them ("see `<child>_about.md`"). **One carve-out:** an aspect doc that is a
verbatim **imported external README** (e.g. `fasa_repo_about.md`) may keep that tooling detail, but mark
it with a top `> Source: …` provenance line; the parent hub stays clean.

```markdown
# <Initiative's real name>        <!-- becomes the graph node label — the proper name, not a filename -->

<One sentence, present tense: what this initiative is and the problem it addresses.>

## Aim
<Why it exists — the goal and the rationale behind it. Graphify stores this as node rationale.>

## Scope (current state)
<What it covers today: workstreams, sites, methods, components. Name the concepts and entities
 a reader — and the graph — should associate with this initiative.>

## Related files
- <child or sibling> — <how it relates: part of / produced by / documents / feeds / builds on>
- ../<other_initiative>/<file> — <cross-initiative relationship>   <!-- list these first; most valuable -->
```

**Worked example:** `fasa/fasa_about.md` (the parent FASA hub) ⇄ `fasa/fasa_repo_about.md` (its engine
child) — the hub carries the programme (aim, partners, funding, field research) and delegates the
optimization-engine internals to the child.

### Initiative perspective docs (satellites) & the canonical name

An initiative usually grows **more than one** child doc: besides the hub it accumulates *perspective*
artifacts — a history/timeline, a roadmap, design rationale, a decision log. **Each is an aspect
`<initiative>_<aspect>_about.md` child** (Template C, hub-anchored), e.g. `peskas_timeline_about.md`. A
single standalone idea stays `idea_<topic>.md`, but it too must name its initiative and use the
canonical name below. Don't invent new suffixes — reuse the aspect-child pattern.

Three rules keep these from making a mess or splitting the initiative across communities:

1. **One canonical entity name.** The hub's `# H1` is the initiative's single canonical proper name.
   Every note in the initiative refers to the initiative/system by *that exact name* — never a synonym
   (**"Peskas"**, not "Peskas platform" / "Peskas Monitoring System"). *Why:* Graphify identifies a node
   by its label; it auto-merges identical long labels but its dedup deliberately **won't** merge short
   or variant labels — so synonyms mint duplicate nodes for the same real thing. The hub is the one
   canonical concept node; satellites *reference* it, never reintroduce a variant.
2. **Anchor every satellite to the hub.** State `part of <initiative>_about.md` in the satellite and
   **enumerate the satellite in the hub** (both sides → `EXTRACTED`). *Why:* clustering is edge-density
   driven with no manual pinning — a node joins whichever community it links most strongly into, so a
   strong hub link keeps the satellite with its initiative.
3. **Keep cross-initiative links in the hub.** Put "this initiative relates to initiative X" edges in
   the **hub**, not scattered across satellites. A satellite that links heavily *outward* gets pulled
   into another community or inflates a cross-cluster, so satellites stay mostly inward-facing (hub +
   same-initiative siblings) and the hub is the initiative's single outward-facing connector. *(This
   refines habit 2 for satellites only — companion `_dict`/`_context` notes keep their file-specific
   cross-links.)*
4. **Provenance lives on the doc it describes.** If a satellite is *imported from a specific source*
   (a shared doc, a Tana/Notion export, a report), put `source_url`/`captured_at` in **that satellite's**
   YAML frontmatter — **never on the hub**. The hub is a living *synthesis*: give it the project's
   canonical site (or no `source_url` — git is its provenance). Putting one doc's source on another
   misattributes it (a timeline's source URL must not sit on the hub).

| Artifact | Convention |
|---|---|
| Whole-initiative overview (current state) | the bare `<initiative>_about.md` **hub** |
| Timeline / history / roadmap / design rationale / decision log | aspect `<initiative>_<aspect>_about.md` child, hub-anchored |
| A single idea / observation | `idea_<topic>.md` (names its initiative, uses the canonical name) |

**To add a satellite** (or just run `/curate`, which does all of this):
1. Create `<initiative>/<initiative>_<aspect>_about.md` in the initiative folder; shape it as Template C.
2. Use the hub's canonical name (its `# H1`) **verbatim** wherever you name the initiative/system.
3. In the satellite's `## Related files`, link **up to the hub**, phrased so it doesn't just repeat the
   filename — e.g. ``peskas_about.md — parent hub; this timeline is **part of** the Peskas overview,
   which delegates its full history here.``
4. In the **hub's** `## Related files`, add a line enumerating the new child (so the edge is `EXTRACTED`
   on both sides).
5. Link only **same-initiative siblings** in the satellite; leave cross-initiative links to the hub.
6. If the satellite came from a specific source, put its `source_url`/`captured_at` in **its own**
   frontmatter — not the hub's.

**Worked example:** `peskas/peskas_timeline_about.md` (the history & scaling chronology) is a child of
`peskas/peskas_about.md`; it calls the system **"Peskas"** throughout, links up to the hub, leaves the
Peskas↔other-initiative links to the hub, and carries its own Tana `source_url` — so the whole initiative
clusters as one and the timeline's provenance stays on the timeline.

---

## 7. Recording updates and supersession over time

A companion note is a **frozen snapshot** — it records what its source said *when it was added*.
Knowledge changes: a 2025 paper's method may be replaced by 2026, or an evolving project simply moves
on. Record the change **without losing the original**, using the two tenses of notes
([§6](#6-context-notes)).

**Where "current" lives: the initiative's living `_about.md`.** What usually supersedes a snapshot
isn't a brand-new document — it's *the project as it is now*. So keep a living `<initiative>_about.md`
and update it in place; it is the durable, always-current target a stale snapshot points to. (No
overview yet? **`/curate` will offer to create one** from the existing notes.)

Then, on the **snapshot** whose content moved on — **append only; never rewrite its existing sections**:

**1. A dated `## Updates` block** — newest first, one line per change. Date it **as precisely as you
honestly can, and no more**:

```markdown
## Updates
- **2026-06** — Workflow X was replaced by Y; the method in §3 is **superseded by**
  `peskas_about.md` (current state). The 2025 results above remain the original record.
- **~2026 (timing approximate)** — scope broadened to Z; earlier framing here is dated.
```

Precise (`2026-06`), coarse (`2026`, `~2026`, a range), relational (`since the 2025 paper`), or an
explicit `timing approximate` are all valid — **never invent a date**. The supersession *link* carries
the meaning; the date is secondary.

**2. A directional link in `## Related files`** — this is what the graph actually edges on, so name
**both** sides:

```markdown
## Related files
- peskas_about.md — superseded_by   # current state replaces the part above
```

On the living overview the inverse holds (optionally stated `<snapshot> — supersedes`). Naming both
sides makes the edge `EXTRACTED`, so a query can tell **current** from **superseded**.

**Two strengths — don't over-claim.** Use **`superseded_by`/`supersedes`** when a specific,
identifiable thing replaces another. When you only know "this is a snapshot and the project has moved
on," use the **lighter** form: just link the snapshot to its `<initiative>_about.md` ("current state
lives here") — no date, no specifics needed. That light pointer is the graceful default for evolving,
fuzzy cases.

**Keep it in the body, not in frontmatter.** Graphify reads only `source_url` / `captured_at` /
`author` / `contributor` from a note's YAML frontmatter and never turns frontmatter into an edge — a
`superseded_by:` or `valid_until:` key there would be **invisible to the graph**. The body is the only
place that is both machine-visible *and* human-readable. (One exception: if you *do* have an exact "as
of" date, `captured_at:` in frontmatter is the one temporal field graphify carries onto the node —
optional, for when that precision exists. See [§8](#8-how-graphify-extraction-works).)

This mirrors established practice: `superseded_by` / `supersedes` map 1-to-1 onto Dublin Core's
[`dcterms:isReplacedBy` / `replaces`](https://www.dublincore.org/specifications/dublin-core/dcmi-terms/);
appending dated records instead of overwriting is exactly the provenance
[FAIR principle R1.2](https://www.go-fair.org/fair-principles/) asks for; the dated `## Updates` block
is [Keep a Changelog](https://keepachangelog.com/) form; and the living `_about.md` is the
present-tense complement that keeps the brain answering "what is this project *today*?".
**`/curate` will make these edits for you** — tell it what changed and what supersedes what.

---

## 8. How graphify extraction works

So expectations are correct:

- **Code** is parsed locally with Tree-sitter (no API calls). **Docs, PDFs, and images** are sent to
  the assistant's model for semantic extraction. It is *not* keyword/filename matching.
- Relationships are clustered and each is tagged `EXTRACTED`, `INFERRED`, or `AMBIGUOUS`.
- **Edges come from relationships a document *states*** — name both sides in prose / `## Related files`.
- **Frontmatter:** graphify copies only `source_url`, `captured_at`, `author`, `contributor` onto a
  file's nodes as attributes. It does **not** read other keys (e.g. `superseded_by`, `valid_until`) and
  **never mints an edge from frontmatter**. Put relationships in the body
  ([§7](#7-recording-updates-and-supersession-over-time)).
- **No shape-based edges.** A table's wide/long shape, encoding, or file type must never be the basis of
  a similarity edge — that mints quadratic, uninformative cross-links. This is enforced at two points:
  habit 4 ([§6](#6-context-notes)) keeps shape language out of *notes*; the **format-blind similarity
  guard** in [CLAUDE.md](CLAUDE.md) keeps the *extractor* from re-deriving shape from a note's column
  list / label / filename. **Both are required.**

---

## 9. Maintainer and build reference

Only the **build owner** runs the commands here. Contributors stop after their PR
([§1](#1-roles-and-the-single-builder-rule), [§2](#2-the-contribution-protocol)).

### Build model & provenance
Run builds in Claude Code with the session model **pinned to `claude-opus-4-8`** (`/model
claude-opus-4-8` before building). Pin the **exact** model, not the floating `opus` alias, so a newer
Opus changes the graph only when the pin is deliberately bumped. The `/curate` and `/enrich` subagents
are pinned to the same model in their `.claude/agents/*.md` frontmatter.

After every successful build, (over)write **`graphify-out/BUILD_INFO.md`** with: the date; the exact
model ID you ran as (not the `opus` alias); the graphify version (`graphify --version`); the build mode;
and node & edge counts from `graph.json`. Commit it with `graphify-out/` — a model/tool change then
shows up as a `BUILD_INFO.md` diff in the PR. **To upgrade the model,** change the pin in three places
together — `/model …`, `CLAUDE.md`, and both `.claude/agents/*.md` — then rebuild.

### Building & updating
```bash
/graphify .                 # build the graph for the current folder
/graphify ./subfolder       # build for one folder only
/graphify . --update        # re-extract only changed files (use after a merge)
/graphify . --update --force # overwrite even if node count drops (e.g. after deletes)
/graphify . --no-viz        # skip the HTML, just report + JSON
/graphify . --cluster-only  # rerun clustering without re-extracting
```
For a periodic from-scratch rebuild, run the standard **`/graphify .`** — **not** `--mode deep`.
Standard mode keeps inferred links conservative and high-signal; `--mode deep` over-generates
speculative cross-domain edges on this corpus and amplifies exactly the noise the format-blind guard
suppresses, so it is **not** used for routine rebuilds (see [CLAUDE.md](CLAUDE.md)). `graph.html`
refreshes on every build; regenerate the README preview with `graphify export svg` (or `--svg`).

### Team workflow & git hygiene
Contributors branch → add + document (`/curate`, `/enrich`) → PR; the maintainer reviews, merges, then
rebuilds and commits `graphify-out/`. **Don't run `graphify hook install`** on this repo — its no-LLM
structural pass turns markdown docs into header-only "junk" nodes; always rebuild through the assistant
(`/graphify . --update`).

**Add to `.gitignore`** (local-only; break when shared) — keep each comment on its **own line**:
```
graphify-out/manifest.json
graphify-out/cost.json
graphify-out/cache/stat-index.json
graphify-out/.graphify_*
graphify-out/[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]/
# The content-hashed cache (cache/ast, cache/semantic) is committed so teammates skip
# re-extraction. To keep the repo small instead, ignore graphify-out/cache/ entirely.
```

### Controlling what gets indexed
Create a `.graphifyignore` in the project root (same syntax as `.gitignore`, including `!` negation).
The workflow/tooling docs — `README.md`, `USER_GUIDE.md`, `PROTOCOL.md`, `CLAUDE.md`, `CHANGELOG.md`,
`.claude/` — are ignored so their language never pollutes the graph.

### Adding external sources
Contributors don't save URLs — they tell the maintainer the link:
```bash
/graphify add https://arxiv.org/abs/1706.03762   # fetch a paper and add it
/graphify add <video-url>                          # transcribe and add a video
graphify clone https://github.com/owner/repo       # pull in a remote repo
```

### Reference project layout
```
WDB/
├── .graphifyignore              # what to exclude from the graph
├── .gitignore
├── PROTOCOL.md                  # this file — the normative spec
├── README.md / USER_GUIDE.md    # practical guides (link here)
├── CLAUDE.md                    # build-operator rules (model pin, extraction guard)
│
├── project_kenya_pilot/
│   ├── ingest_yields.py
│   ├── kenya_yield_data_2025.csv
│   ├── kenya_yield_data_2025_dict.md        # Template A
│   ├── grant_proposal_kenya.pdf
│   ├── grant_proposal_kenya_context.md      # Template B
│   └── project_kenya_pilot_about.md         # living current-state overview
│
└── graphify-out/                # generated — maintainer commits this folder
    ├── graph.html
    ├── GRAPH_REPORT.md
    └── graph.json
```

---

## 10. Quick command reference

**Contributors** (run `/curate` **before** `/enrich`; `/enrich` fills the note `/curate` drafts):
```bash
graphify install                 # one-time: register the skill
/curate                          # 1st: standardize placement, name, context note
/enrich <file.csv>               # 2nd (tables only): validate shape + fill value domains
```

**Maintainer:**
```bash
/graphify .                      # build graph
/graphify . --update             # refresh changed files
/graphify add <url>              # add a paper/video
graphify clone <github-url>      # add a remote repo
/graphify query "what connects X to Y?"
/graphify explain "SomeComponent"
```

Package note: the PyPI package is `graphifyy` (double-y); the CLI command is `graphify`. Optional
extras: `graphifyy[pdf]`, `graphifyy[office]` (`.docx`/`.xlsx`), `graphifyy[video]`, `graphifyy[all]`.
Graphify is open-source (MIT) — **[graphifylabs.ai](https://graphifylabs.ai/)** ·
**[github.com/safishamsi/graphify](https://github.com/safishamsi/graphify)**.
