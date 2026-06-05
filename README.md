# WDB — WorldFish Digital Brain

![Version](https://img.shields.io/badge/version-0.0.1-blue) · [CHANGELOG](CHANGELOG.md)

A shared Graphify knowledge graph for the WorldFish Digital Brain (WDB) project. This README is the working standard for the repo: it explains how to add material so every team member works from the same map of our code, datasets, and documents — and, for the build owner, how the graph is generated.

It is organised in two parts:
- **[Part I · Contributing to the brain](#part-i--contributing-to-the-brain)** — for **everyone who adds material**.
- **[Part II · Maintainer & reference](#part-ii--maintainer--reference)** — for the **one person who builds the graph**.

### 🧠 The knowledge graph

[![WDB knowledge graph — communities colour-coded](graphify-out/graph.svg)](graphify-out/GRAPH_REPORT.md)

*The current graph, each colour a community. Click the image for the readable **[GRAPH_REPORT.md](graphify-out/GRAPH_REPORT.md)** (key concepts, surprising connections, suggested questions).*

**Interactive version** (search, zoom, drag, click through nodes): clone the repo and open **`graphify-out/graph.html`** in any browser. This repo is private, and GitHub serves `.html` as raw source — it can't render an interactive page here — so the image above is the in-page preview and the live graph is local-only.

> **Not a coder?** To add a file, dataset, or idea with a click-by-click walkthrough, follow **[USER_GUIDE.md](USER_GUIDE.md)** — it is this same protocol with screenshots.

## Contents

**Part I · Contributing**
- [What this is](#what-this-is)
- [How to get the best graph](#how-to-get-the-best-graph)
- [The protocol: adding to the brain](#the-protocol-adding-to-the-brain)
- [Setup (one-time, each team member)](#setup-one-time-each-team-member)
- [Project-First placement](#project-first-placement)
- [Context notes (your main quality lever)](#context-notes-your-main-quality-lever)
- [File types & tidy data](#file-types--tidy-data)

**Part II · Maintainer & reference**
- [Building & updating the graph](#building--updating-the-graph)
- [Team workflow & git hygiene](#team-workflow--git-hygiene)
- [Controlling what gets indexed](#controlling-what-gets-indexed)
- [Adding external sources](#adding-external-sources)
- [Reference project layout](#reference-project-layout)
- [Quick command reference](#quick-command-reference)

---

## What this is

Graphify is an open-source skill for AI coding assistants (Claude Code, Codex, Cursor, Gemini CLI, and others). You point it at a folder; it builds a queryable knowledge graph instead of having the assistant grep through files. Running it produces three outputs in `graphify-out/`:

- `graph.html` — interactive graph (open in any browser)
- `GRAPH_REPORT.md` — key concepts, surprising connections, suggested questions
- `graph.json` — the full graph, queryable without re-reading files

**How extraction works (so expectations are correct):** code is parsed locally with Tree-sitter (no API calls); docs, PDFs, and images are sent to your assistant's model for semantic extraction; relationships are clustered and each one is tagged `EXTRACTED`, `INFERRED`, or `AMBIGUOUS`. It is *not* keyword/filename matching.

**Who runs what.** Everyone who contributes runs two helper commands to self-check their own work — **`/curate`** (placement, naming, context note) and **`/enrich`** (table shape + value domains) — before opening a pull request. **Only the maintainer runs the graph build itself (`/graphify`)** and commits the regenerated `graphify-out/`. Keeping one build owner is what keeps the shared map conflict-free.

**This repo runs on Claude Code.** Graphify the tool supports several assistants, but the **WDB workflow is built on [Claude Code](https://claude.com/claude-code) specifically**: the `/curate` and `/enrich` commands (`.claude/commands/`), the `wdb-curator` and `dict-enricher` agents (`.claude/agents/`), and the [`CLAUDE.md`](CLAUDE.md) operator rules are all Claude Code features — other assistants won't read them. Use Claude Code (VS Code extension, desktop app, or CLI). The maintainer runs the **build on a pinned Opus** (`claude-opus-4-8`) for stable, reproducible extraction, and the `/curate` + `/enrich` agents are pinned to the same model; each build records the exact model and graphify version in [`graphify-out/BUILD_INFO.md`](graphify-out/BUILD_INFO.md), so a model change is visible in the next pull request.

Graphify is open-source (MIT) — official project: **[graphifylabs.ai](https://graphifylabs.ai/)** · source & issues: **[github.com/safishamsi/graphify](https://github.com/safishamsi/graphify)** · PyPI package: `graphifyy`.

---

# Part I · Contributing to the brain

Everything here is for **every team member who adds material**. You place, name, and document your file, self-check it with `/curate` and `/enrich`, then open a pull request. You never build the graph yourself — that's [Part II](#part-ii--maintainer--reference).

## How to get the best graph

The graph's value is the **connections** Graphify finds — and it can only connect what your files make *explicit*. Good organization (placement + context notes) gets you tight clusters; these habits get you the rich cross-links that make the map worth having:

1. **State relationships in words.** Graphify draws an edge when a document *says* two things are related — it does **not** infer links from filenames or folder layout. If a dataset is produced by a script, a paper builds on a method, or two efforts share an approach, write that sentence somewhere and **name both sides**. Unstated relationships stay invisible.
2. **Treat "Related files" as the wiring — and cross-link across initiatives.** The `## Related files` line in a context note is the main way you hand Graphify an edge. List the real siblings each file relates to, and deliberately link *across* initiative folders, not only within one. Those cross-initiative links become the "surprising connections" the graph exists to surface.
3. **Capture the "why," not just the "what."** Graphify stores rationale — design decisions, trade-offs, how a thing is used — as part of a node, and builds dedicated rationale links. A note that explains *why* a file exists and how it connects extracts far more than a bare summary.
4. **Describe what a file is *about*, not its *container* — and never put tooling in a note.** Graphify graphs whatever a note emphasizes. A note should carry the data's **meaning and relationships**, not its **format** (a table's wide/long shape, encoding, file type) or **provenance** (which script or `/`-command produced or enriched it, column-role mechanics). Format is shared by every file of that form, so emphasizing it mints *quadratic, uninformative* cross-file links — every long table tied to every other long table — the same noise Graphify already avoids by ignoring filenames and folders. Keep shape/tooling out of `_dict.md`/`_context.md`; this README and `USER_GUIDE.md` are `.graphifyignore`d, so they discuss shape freely without polluting the graph. **Clean notes are necessary but not sufficient:** a `_dict.md` still reveals shape through its column list, node label, and filename, so the *extractor* is also held to this rule — see [`CLAUDE.md`](CLAUDE.md), which makes the graph operator inject a **format-blind similarity guard** (no `semantically_similar_to` edge may ever be based on a table's shape). Habit 4 governs the input; that guard governs extraction; both are required.

## The protocol: adding to the brain

**Follow these steps exactly, every time.** Steps 1–6 are yours; step 7 is the maintainer's. They are identical whether you work from the command line or from the click-by-click **[USER_GUIDE.md](USER_GUIDE.md)** — that guide is just this protocol with screenshots. Acting the same way is what keeps everyone's contributions consistent.

1. **Sync & branch.** Pull `main`, then create a branch named `yourname/short-topic`.
2. **Pick the initiative folder.** Put your file in the matching `initiative/` folder. If none fits, create one at the repo root named in `lower_snake_case` (e.g. `genetic_improvement/`). If you're unsure which initiative it belongs to, **ask the maintainer — don't guess.**
3. **Add the file, named by the rule.** Naming rule: **`lower_snake_case`, descriptive, with year and/or region when they apply.** ✅ `kenya_yield_2025.csv` ❌ `data.csv`, `Final Report.pdf`. Don't edit spreadsheet headers; keep a published paper's real title. **Tabular data must be tidy: one header row, in exactly one of two shapes — *wide* (one row per entity, one column per variable) or *long* (a variable/parameter column + a value column, one row per measurement).** Not allowed: multi-row/merged headers, metadata rows above the header, several tables in one sheet, pivot/crosstab dumps — reshape into a valid wide or long table before adding it. See [File types & tidy data](#file-types--tidy-data).
4. **Write its context note — `/curate` can draft it.** **Required for every dataset, PDF, and document** (recommended for images and audio/video). Pick the template by type (table below), name it by **replacing the file's extension** with `_dict.md` (tabular) or `_context.md` (everything else) — e.g. `kenya_yield_2025.csv` → `kenya_yield_2025_dict.md`, `report.pdf` → `report_context.md` — and **fill every section** — especially **Related files**, which is how the graph connects: list real siblings, and link *across* initiatives, not just within one. Running **`/curate`** has the `wdb-curator` agent place, name, and draft the note for you against these rules; you review what it wrote. Templates + worked examples: [Context notes](#context-notes-your-main-quality-lever).
5. **Validate tables with `/enrich`.** For every `.csv`/`.xlsx`, run **`/enrich <file>`**: it checks the shape (and **stops and tells you exactly what to fix** if the table isn't tidy) and fills the dictionary's `## Columns` value domains deterministically. Run it as your data-validity check before the PR — domains are still maintainer-reviewed.
6. **Commit source files only, then open a pull request.** Never commit anything under `graphify-out/`. Push your branch and open a PR. The maintainer reviews and merges — that is the only way changes reach `main`.
7. **Maintainer rebuilds.** After merge, the maintainer runs `/graphify . --update` and commits the regenerated `graphify-out/`. **Contributors never run the graph build (`/graphify`).**

### What am I adding?

| What you're adding | Where it goes | Context note |
|---|---|---|
| Dataset / spreadsheet (`.csv`, `.xlsx`) | initiative folder; don't edit headers; **tidy — one header row, wide or long** ([reference](#file-types--tidy-data)) | **Required** — Template A (`…_dict.md`); run **`/enrich`** to validate shape + fill value domains |
| Report / paper / document (`.pdf`, `.docx`, `.md`, `.txt`) | initiative folder; keep a paper's real title | **Required** — Template B (`…_context.md`) |
| Image / diagram / screenshot | initiative folder | Required if it carries information — Template B (`…_context.md`) |
| Audio / video | initiative folder | Required if it's hard to follow — Template B (`…_context.md`) |
| External link / online paper / video / repo | — | Don't save a URL — the maintainer runs `/graphify add <url>` ([external sources](#adding-external-sources)) |
| A topic / initiative overview (not about one file) | initiative folder | Standalone `_about.md` (no template) + `## Related files`; aspect = `<initiative>_<aspect>_about.md`, whole-initiative overview = `<initiative>_about.md` |
| An idea / observation | initiative folder | The note *is* the content: `idea_<topic>.md`; name related files inside it |

### Before you open the PR — checklist

- [ ] File is in the correct **initiative folder**
- [ ] Name is **`lower_snake_case`**, descriptive (year/region if relevant)
- [ ] Ran **`/curate`** — placement, name, and context note conform to the protocol
- [ ] **Tabular data is tidy** — one header row, wide or long — and passed **`/enrich`** (the shape/validity check)
- [ ] **Context note** present where required, with **every section filled in** (for tables, value domains filled by `/enrich`)
- [ ] **Related files** lists real siblings (+ a cross-initiative link where one exists)
- [ ] Only **source files** staged — nothing under `graphify-out/`
- [ ] On **my branch**, opening a **pull request** — not committing to `main`

## Setup (one-time, each team member)

You install **Claude Code** (if you don't have it — VS Code extension, desktop app, or CLI) and Graphify once, so you can run `/curate` and `/enrich` on your own files. You will **not** build the graph — that's the maintainer.

> **Package name:** the PyPI package is `graphifyy` (double-y). The CLI command is still `graphify`.

**Step 1 — install the package:**

```bash
# Recommended (puts graphify on PATH automatically):
uv tool install graphifyy

# Alternatives:
pipx install graphifyy
pip install graphifyy
```

**Step 2 — register the skill with Claude Code:**

```bash
graphify install
```

Then open Claude Code and you can type `/curate` and `/enrich`. (Non-coders: [USER_GUIDE.md](USER_GUIDE.md) walks this through click by click.)

> **Windows / PowerShell:** type commands without the leading slash where your shell needs it — PowerShell treats `/` as a path separator.

**Optional extras** — install only what your files need:

| File type | Required install |
|---|---|
| PDFs | `pip install "graphifyy[pdf]"` |
| `.docx` / `.xlsx` | `pip install "graphifyy[office]"` |
| Video / audio (local transcription) | `pip install "graphifyy[video]"` |
| Everything | `pip install "graphifyy[all]"` |

## Project-First placement

Group materials by **initiative**, not by file format.

- **Correct:** `project_kenya_pilot/` holds that pilot's code, datasets, PDFs, and notes together.
- **Avoid:** a single `datasets/` folder mixing unrelated projects.

This keeps related concepts physically close, which produces a tighter, more useful graph. Use descriptive, specific filenames (`kenya_yield_data_2025.csv`, not `data.csv`) — for human navigation and clearer semantic extraction, not because the tool matches words literally.

## Context notes (your main quality lever)

Companion notes are the highest-leverage thing you can add. Each `.md` is itself graphed, so a note turns a lone file into a well-connected node. Per [the protocol](#the-protocol-adding-to-the-brain), a note is **required for every dataset, PDF, and document** (recommended for images and audio/video) — running **`/curate`** has the `wdb-curator` agent draft it for you, and for tables **`/enrich`** validates the shape and fills the `## Columns` value domains. The `## Related files` line is where you hand Graphify its edges: fill it with the real siblings the file relates to, and **cross-link across initiative folders**, not just within one (see [How to get the best graph](#how-to-get-the-best-graph)). Place each note beside the file it describes, named by **replacing the source file's extension** with `_dict.md` (tabular) or `_context.md` (everything else) — e.g. `kenya_yield_2025.csv` → `kenya_yield_2025_dict.md`, `report.pdf` → `report_context.md`.

**Two kinds of note.** Most are **companion notes** that describe one specific file — `<file>_dict.md` (tabular) or `<file>_context.md` (anything else), named as above, using the templates below. A document that describes a **topic or a whole initiative** rather than a single file is a **standalone `_about.md` doc**: name an aspect doc `<initiative>_<aspect>_about.md` (e.g. `pondcube_data_about.md`, `fasa_repo_about.md`), and **reserve the bare `<initiative>_about.md` for the single whole-initiative overview** (e.g. `pondcube_about.md`) — so a later overview never collides with an aspect doc. Write these freely (no template) but still give each a `## Related files` section. Never give an overview a `_dict`/`_context` suffix — that suffix means "companion to the file of that name."

**Template A — tabular data** (`.csv`, `.xlsx`). Name it the file's name with its extension replaced by `_dict.md` (e.g. `kenya_yield_2025.csv` → `kenya_yield_2025_dict.md`). Describe what each column **means** and record its **value domain** in `## Columns`: distinct values for low-cardinality categoricals (`period ∈ {morning, afternoon}`), a count + examples for IDs/free-text, and a range for numerics/dates. **You don't hand-type the domains** — run **`/enrich`** and it fills them deterministically from the data (the maintainer reviews, per the single-builder rule); for long-format tables it summarizes the value column per parameter. Per [habit 4](#how-to-get-the-best-graph), keep the table's **shape** (wide/long) and any **tooling/provenance** (`/enrich`, script names, column-role mechanics) *out* of the note — they're about the file's form, not its content, and create uninformative cross-file links. (Shape is re-detected by `/enrich` on every run, so it never needs writing down.)

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
```

**Filled example** (note the value domains and the cross-initiative link in *Related files*):

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

**Template B — everything else** (PDFs, docs, images, audio/video). Name it the file's name with its extension replaced by `_context.md` (e.g. `grant_proposal_kenya.pdf` → `grant_proposal_kenya_context.md`):

```markdown
# Context: grant_proposal_kenya.pdf

## Summary
One or two sentences: what this file is and why it's in the workspace.

## Key concepts / entities
- Regions, methods, or topics this file is about

## Related files
- related_file_1, related_file_2
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

## File types & tidy data

"Where it goes" means the **initiative folder** (e.g. `project_kenya_pilot/`) — every file lives inside the folder for the project it belongs to. The graph is built (by the maintainer) by running `/graphify .` from the repo root, which picks up all of them.

| File type | Where it goes | Notes |
|---|---|---|
| Code | Save inside the project folder. | Parsed locally (no API). Inline comments (`# NOTE:`, `# WHY:`, `# HACK:`) and docstrings are extracted as linked nodes — write your context there. |
| Docs (`.md`, `.txt`, `.html`, …) | Save inside the project folder. | Sent to the model for semantic extraction. |
| Tabular (`.csv`, `.xlsx`) | Save inside the project folder; don't alter headers; must be **tidy** (one header row, wide or long — see below). | Needs `graphifyy[office]` for `.xlsx`. Run **`/enrich`** to validate the shape and fill the dictionary's value domains. |
| PDFs | Save inside the project folder. | Needs `graphifyy[pdf]`. |
| Images (`.png`, `.jpg`, …) | Save diagrams/whiteboard photos inside the project folder. | Read via the model's vision step. |
| Video / audio | Save the media file inside the project folder. | Transcribed locally; needs `graphifyy[video]`. |
| External papers / videos / repos | Don't save a file — the maintainer runs `/graphify add <url>` or `graphify clone <repo>`. | Don't paste URLs into text files. |

### Allowed tabular shapes (tidy data only)

Every spreadsheet must be **one tidy table with a single header row**, in exactly one of two shapes — this is what makes the value domains extractable and keeps badly-shaped data out of the graph:

- **Wide** — one row per entity (e.g. per location/tank/date), **one column per variable**. Example: `pondcube_observations_wide.csv`.
- **Long** ("tidy long") — a `variable`/`parameter` column **+** a `value` column (+ optional `unit`), **one row per measurement**. Example: `pondcube_measurements_long.csv`.

**Not allowed** (reshape before adding): multi-row or merged-cell headers, metadata/title rows above the header, several tables stacked in one sheet, ragged rows, pivot/crosstab dumps. The **`/enrich`** command runs a deterministic check (`.claude/scripts/dict_enricher.py`) that **flags exactly what is wrong** rather than guessing — run it as your data-validity check before opening a PR. *(Why tidy: Wickham, "Tidy Data", J. Stat. Soft. 59(10), 2014.)*

---

# Part II · Maintainer & reference

Only the **build owner** runs the commands in this part. Contributors stop after their pull request (Part I); the maintainer merges it and regenerates the graph.

## Building & updating the graph

Run builds in **Claude Code with the session model pinned to `claude-opus-4-8`** (Opus 4.8) — set it with `/model claude-opus-4-8` before building. Pinning the **exact** model (not the floating `opus` alias) keeps rebuilds reproducible: a newer Opus changes the graph only when you deliberately bump the pin. Each build stamps the model + graphify version into `graphify-out/BUILD_INFO.md` — commit it with the rest of `graphify-out/`. **To upgrade the model later,** change the pin in three places together — here, in [`CLAUDE.md`](CLAUDE.md), and in both `.claude/agents/*.md` files — then rebuild.

Run from the project root:

```bash
/graphify .              # build the graph for the current folder
/graphify ./subfolder    # build for one folder only
```

When files change after a merge, refresh only what changed instead of rebuilding from scratch:

```bash
/graphify . --update     # re-extract only changed files
```

If a rebuild reports *fewer* nodes than before (e.g. after deleting files) and you want to overwrite anyway:

```bash
/graphify . --update --force
```

Useful variants:

```bash
/graphify . --no-viz        # skip the HTML, just report + JSON
/graphify . --cluster-only  # rerun clustering without re-extracting
```

For a periodic from-scratch rebuild, run the standard **`/graphify .`** (no `--mode deep`). Standard mode keeps inferred links conservative and high-signal; `--mode deep` over-generates speculative cross-domain edges on this corpus, so it is not used for routine rebuilds (see [How to get the best graph](#how-to-get-the-best-graph)).

> **Keeping the preview current:** `graph.html` refreshes on every `/graphify .` or `/graphify . --update`; regenerate the `graph.svg` preview shown at the top of this README with `graphify export svg` (or build with `/graphify . --svg`). Commit `graphify-out/` so the team shares the same map.

## Team workflow & git hygiene

The graph is generated *and committed*, so the team shares one map without everyone rebuilding. Two rules keep it consistent and conflict-free:

1. **Contributors follow [the protocol](#the-protocol-adding-to-the-brain): branch → add + document (`/curate`, `/enrich`) → pull request.** They commit **source files only** and never build the graph; the maintainer reviews and merges every PR — that is the only path to `main`.
2. **One maintainer owns the build.** After merging, the maintainer runs `/graphify . --update` (or a full `/graphify .` when a from-scratch rebuild is needed) and commits the regenerated `graphify-out/`. Because only one person regenerates the large `graph.*` files, there are no merge conflicts. Everyone else just pulls.

> ⚠️ **Don't run `graphify hook install` on this repo.** The commit hook rebuilds with a no-LLM structural pass that turns markdown docs into header-only "junk" nodes — it's built for code-heavy repos, and this corpus is almost entirely docs/PDFs. Always rebuild through the assistant (`/graphify . --update`), which does real semantic extraction.

**Add to `.gitignore`** (these are local-only and break when shared). Keep each comment on its **own line** — an inline `# ...` after a pattern becomes part of the pattern, so the rule silently never matches:

```
# manifest.json + cache/stat-index.json are mtime/path-based (invalid after clone);
# cost.json is local token tracking; the .graphify_* dotfiles are transient pipeline
# scratch plus machine-local absolute paths (_root/_python); dated folders are local backups.
graphify-out/manifest.json
graphify-out/cost.json
graphify-out/cache/stat-index.json
graphify-out/.graphify_*
graphify-out/[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]/

# The content-hashed cache (cache/ast, cache/semantic) is committed so teammates skip
# re-extraction. To keep the repo small instead, ignore the whole cache:
# graphify-out/cache/
```

## Controlling what gets indexed

Create a `.graphifyignore` in the project root. Same syntax as `.gitignore`, including `!` negation:

```
# .graphifyignore
node_modules/
dist/
*.generated.*

# or: index only src/, ignore everything else
*
!src/
!src/**
```

## Adding external sources

Contributors don't save URLs — they tell the maintainer the link. The maintainer adds it with the built-in commands:

```bash
/graphify add https://arxiv.org/abs/1706.03762   # fetch a paper and add it
/graphify add <video-url>                          # transcribe and add a video
graphify clone https://github.com/owner/repo       # pull in a remote repo
```

## Reference project layout

How an initiative folder looks with files and their context notes in place:

```
WDB/
├── .graphifyignore              # what to exclude from the graph
├── .gitignore                   # ignores graphify-out/manifest.json, cost.json, …
├── CLAUDE.md                    # operator rules (extraction guard, standard mode)
│
├── project_kenya_pilot/
│   ├── ingest_yields.py         # code — parsed locally
│   ├── kenya_yield_data_2025.csv
│   ├── kenya_yield_data_2025_dict.md     # Template A
│   ├── grant_proposal_kenya.pdf
│   ├── grant_proposal_kenya_context.md   # Template B
│   ├── field_map.png
│   ├── field_map_context.md              # Template B (image — add if it carries info)
│   └── kickoff_meeting.mp4
│
├── project_zanzibar/
│   ├── effort_model.py
│   ├── catch_data.xlsx
│   ├── catch_data_dict.md                # Template A
│   └── methods_note.md                   # plain note, no template needed
│
└── graphify-out/                # generated — maintainer commits this folder
    ├── graph.html
    ├── GRAPH_REPORT.md
    └── graph.json
```

Each file sits inside the project it belongs to; context notes (where used) live right beside their target file; the generated `graphify-out/` folder is committed so teammates share the same map.

## Quick command reference

**Contributors (self-check before the PR):**

```bash
graphify install                 # one-time: register the skill
/curate                          # standardize placement, name, context note
/enrich <file.csv>               # validate table shape + fill value domains
```

**Maintainer (owns the build):**

```bash
/graphify .                      # build graph
/graphify . --update             # refresh changed files
/graphify add <url>              # add a paper/video
graphify clone <github-url>      # add a remote repo
/graphify query "what connects X to Y?"
/graphify explain "SomeComponent"
```
