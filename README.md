# WDB — WorldFish Digital Brain

A shared Graphify knowledge graph for the WorldFish Digital Brain (WDB) project. This README is the working standard for the repo: it explains how to set up Graphify and how to organize files so every team member works from the same map of our code, datasets, and documents.

### 🧠 The knowledge graph

[![WDB knowledge graph — communities colour-coded](graphify-out/graph.svg)](graphify-out/GRAPH_REPORT.md)

*The current graph, each colour a community. Click the image for the readable **[GRAPH_REPORT.md](graphify-out/GRAPH_REPORT.md)** (key concepts, surprising connections, suggested questions).*

**Interactive version** (search, zoom, drag, click through nodes): clone the repo and open **`graphify-out/graph.html`** in any browser. This repo is private, and GitHub serves `.html` as raw source — it can't render an interactive page here — so the image above is the in-page preview and the live graph is local-only.

> **Keeping it current:** `graph.html` refreshes on every `/graphify .` or `/graphify . --update` run; regenerate the `graph.svg` preview with `graphify export svg` (or build with `/graphify . --svg`). Commit `graphify-out/` so the team shares the same map.

> **Not a coder?** To add a file, dataset, or idea without touching the command line, follow **[USER_GUIDE.md](USER_GUIDE.md)** instead — a click-by-click walkthrough with no graph-tool setup.

## Contents

- [How to get the best graph](#how-to-get-the-best-graph-out-of-graphify)
- [**The protocol: adding to the brain**](#the-protocol-adding-to-the-brain)
- [1. One-time setup (each team member)](#1-one-time-setup-each-team-member)
- [2. Workspace organization (Project-First rule)](#2-workspace-organization-project-first-rule)
- [3. Building the graph](#3-building-the-graph)
- [4. Controlling what gets indexed](#4-controlling-what-gets-indexed)
- [5. Adding external sources](#5-adding-external-sources)
- [6. Updating the graph](#6-updating-the-graph-dont-rebuild-from-scratch)
- [7. Team workflow (the shared standard)](#7-team-workflow-the-shared-standard)
- [8. File-type reference](#8-file-type-reference)
- [9. Context notes (your main quality lever)](#9-context-notes-your-main-quality-lever)
- [10. Reference project layout](#10-reference-project-layout)
- [Quick command reference](#quick-command-reference)

---

## Overview

Graphify is an open-source skill for AI coding assistants (Claude Code, Codex, Cursor, Gemini CLI, and others). You point it at a folder; it builds a queryable knowledge graph instead of having the assistant grep through files. Running it produces three outputs in `graphify-out/`:

- `graph.html` — interactive graph (open in any browser)
- `GRAPH_REPORT.md` — key concepts, surprising connections, suggested questions
- `graph.json` — the full graph, queryable without re-reading files

**How extraction works (so expectations are correct):** code is parsed locally with Tree-sitter (no API calls); docs, PDFs, and images are sent to your assistant's model for semantic extraction; relationships are clustered and each one is tagged `EXTRACTED`, `INFERRED`, or `AMBIGUOUS`. It is *not* keyword/filename matching.

Graphify is open-source (MIT) — official project: **[graphifylabs.ai](https://graphifylabs.ai/)** · source & issues: **[github.com/safishamsi/graphify](https://github.com/safishamsi/graphify)** · PyPI package: `graphifyy`.

---

## How to get the best graph out of Graphify

The graph's value is the **connections** Graphify finds — and it can only connect what your files make *explicit*. Good organization (Sections 2 & 9) gets you tight clusters; these three habits get you the rich cross-links that make the map worth having:

1. **State relationships in words.** Graphify draws an edge when a document *says* two things are related — it does **not** infer links from filenames or folder layout. If a dataset is produced by a script, a paper builds on a method, or two efforts share an approach, write that sentence somewhere and **name both sides**. Unstated relationships stay invisible.
2. **Treat "Related files" as the wiring — and cross-link across initiatives.** The `## Related files` line in a context note (Section 9) is the main way you hand Graphify an edge. List the real siblings each file relates to, and deliberately link *across* initiative folders, not only within one. Those cross-initiative links become the "surprising connections" the graph exists to surface.
3. **Capture the "why," not just the "what."** Graphify stores rationale — design decisions, trade-offs, how a thing is used — as part of a node, and builds dedicated rationale links. A note that explains *why* a file exists and how it connects extracts far more than a bare summary.

For the periodic full rebuild, prefer **`/graphify . --mode deep`** — it extracts more inferred and latent links (shared assumptions, indirect dependencies) than the default, which is what you want from a cross-disciplinary research corpus. Uncertain links are tagged `INFERRED`/`AMBIGUOUS`, so the audit trail stays honest.

---

## The protocol: adding to the brain

**Follow these steps exactly, every time.** They are identical whether you work from the command line or from the click-by-click **[USER_GUIDE.md](USER_GUIDE.md)** — that guide is just this protocol with screenshots. Acting the same way is what keeps everyone's contributions consistent.

1. **Sync & branch.** Pull `main`, then create a branch named `yourname/short-topic`.
2. **Pick the initiative folder.** Put your file in the matching `initiative/` folder. If none fits, create one at the repo root named in `lower_snake_case` (e.g. `genetic_improvement/`). If you're unsure which initiative it belongs to, **ask the maintainer — don't guess.**
3. **Add the file, named by the rule.** Naming rule: **`lower_snake_case`, descriptive, with year and/or region when they apply.** ✅ `kenya_yield_2025.csv` ❌ `data.csv`, `Final Report.pdf`. Don't edit spreadsheet headers; keep a published paper's real title.
4. **Write its context note.** **Required for every dataset, PDF, and document** (recommended for images and audio/video). Pick the template by type (table below), name it by **replacing the file's extension** with `_dict.md` (tabular) or `_context.md` (everything else) — e.g. `kenya_yield_2025.csv` → `kenya_yield_2025_dict.md`, `report.pdf` → `report_context.md` — and **fill every section** — especially **Related files**, which is how the graph connects: list real siblings, and link *across* initiatives, not just within one. Templates + worked examples: [Section 9](#9-context-notes-your-main-quality-lever).
5. **Commit source files only.** Never commit anything under `graphify-out/`.
6. **Open a pull request.** Push your branch and open a PR. The maintainer reviews and merges — that is the only way changes reach `main`.
7. **Maintainer rebuilds.** After merge, the maintainer runs `/graphify . --update` and commits the regenerated `graphify-out/`. **Contributors never run the graph tool.**

### What am I adding?

| What you're adding | Where it goes | Context note |
|---|---|---|
| Dataset / spreadsheet (`.csv`, `.xlsx`) | initiative folder; don't edit headers | **Required** — Template A (`…_dict.md`) |
| Report / paper / document (`.pdf`, `.docx`, `.md`, `.txt`) | initiative folder; keep a paper's real title | **Required** — Template B (`…_context.md`) |
| Image / diagram / screenshot | initiative folder | Required if it carries information — Template B (`…_context.md`) |
| Audio / video | initiative folder | Required if it's hard to follow — Template B (`…_context.md`) |
| External link / online paper / video / repo | — | Don't save a URL — the maintainer runs `/graphify add <url>` (Section 5) |
| A topic / initiative overview (not about one file) | initiative folder | Standalone `_about.md` (no template) + `## Related files`; aspect = `<initiative>_<aspect>_about.md`, whole-initiative overview = `<initiative>_about.md` |
| An idea / observation | initiative folder | The note *is* the content: `idea_<topic>.md`; name related files inside it |

### Before you open the PR — checklist

- [ ] File is in the correct **initiative folder**
- [ ] Name is **`lower_snake_case`**, descriptive (year/region if relevant)
- [ ] **Context note** present where required, with **every section filled in**
- [ ] **Related files** lists real siblings (+ a cross-initiative link where one exists)
- [ ] Only **source files** staged — nothing under `graphify-out/`
- [ ] On **my branch**, opening a **pull request** — not committing to `main`

---

## 1. One-time setup (each team member)

> **Package name:** the PyPI package is `graphifyy` (double-y). The CLI command is still `graphify`.

**Step 1 — install the package:**

```bash
# Recommended (puts graphify on PATH automatically):
uv tool install graphifyy

# Alternatives:
pipx install graphifyy
pip install graphifyy
```

**Step 2 — register the skill with your assistant:**

```bash
graphify install
```

Then open your assistant and type `/graphify .`

> **Windows / PowerShell:** use `graphify .` (no leading slash) — PowerShell treats `/` as a path separator.

**Optional extras** — install only what your files need:

| File type | Required install |
|---|---|
| PDFs | `pip install "graphifyy[pdf]"` |
| `.docx` / `.xlsx` | `pip install "graphifyy[office]"` |
| Video / audio (local transcription) | `pip install "graphifyy[video]"` |
| Everything | `pip install "graphifyy[all]"` |

---

## 2. Workspace organization (Project-First rule)

Group materials by **initiative**, not by file format.

- **Correct:** `project_kenya_pilot/` holds that pilot's code, datasets, PDFs, and notes together.
- **Avoid:** a single `datasets/` folder mixing unrelated projects.

This keeps related concepts physically close, which produces a tighter, more useful graph.

**Filenames:** use descriptive, specific names (`kenya_yield_data_2025.csv`, not `data.csv`). This is for human navigation and clearer semantic extraction — not because the tool matches words literally.

---

## 3. Building the graph

Run from the project root:

```bash
/graphify .              # build the graph for the current folder
/graphify ./subfolder    # build for one folder only
```

Useful variants:

```bash
/graphify . --no-viz        # skip the HTML, just report + JSON
/graphify . --cluster-only  # rerun clustering without re-extracting
```

---

## 4. Controlling what gets indexed

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

---

## 5. Adding external sources

Do **not** paste URLs into text files. Use the built-in commands:

```bash
/graphify add https://arxiv.org/abs/1706.03762   # fetch a paper and add it
/graphify add <video-url>                          # transcribe and add a video
graphify clone https://github.com/owner/repo       # pull in a remote repo
```

---

## 6. Updating the graph (don't rebuild from scratch)

When files change, refresh only what changed:

```bash
/graphify . --update     # re-extract only changed files
```

If a rebuild reports *fewer* nodes than before (e.g. after deleting files) and you want to overwrite anyway:

```bash
/graphify . --update --force
```

For a periodic from-scratch rebuild that maximises connections, use **deep mode** — it pulls more inferred and latent links across the whole corpus:

```bash
/graphify . --mode deep
```

---

## 7. Team workflow (the shared standard)

The graph is generated *and committed*, so the team shares one map without everyone rebuilding. Two rules keep it consistent and conflict-free:

1. **Contributors follow [the protocol](#the-protocol-adding-to-the-brain): branch → add + document → pull request.** You commit **source files only** and never rebuild the graph yourself; the `wdb-curator` agent helps you place, name, and document each file. The maintainer reviews and merges every PR — that is the only path to `main`.
2. **One maintainer owns the build.** After merging, the maintainer runs `/graphify . --update` (or `/graphify . --mode deep` for a full refresh) and commits the regenerated `graphify-out/`. Because only one person regenerates the large `graph.*` files, there are no merge conflicts. Everyone else just pulls.

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

---

## 8. File-type reference

"Where it goes" means the **initiative folder** from Section 2 (e.g. `project_kenya_pilot/`) — every file lives inside the folder for the project it belongs to. The graph is built by running `/graphify .` from the repo root (Section 3), which picks up all of them.

| File type | Where it goes | Notes |
|---|---|---|
| Code | Save inside the project folder. | Parsed locally (no API). Inline comments (`# NOTE:`, `# WHY:`, `# HACK:`) and docstrings are extracted as linked nodes — write your context there. |
| Docs (`.md`, `.txt`, `.html`, …) | Save inside the project folder. | Sent to the model for semantic extraction. |
| Tabular (`.xlsx`) | Save inside the project folder; don't alter headers. | Needs `graphifyy[office]`. |
| PDFs | Save inside the project folder. | Needs `graphifyy[pdf]`. |
| Images (`.png`, `.jpg`, …) | Save diagrams/whiteboard photos inside the project folder. | Read via the model's vision step. |
| Video / audio | Save the media file inside the project folder. | Transcribed locally; needs `graphifyy[video]`. |
| External papers / videos / repos | Don't save a file — run `/graphify add <url>` or `graphify clone <repo>`. | Don't paste URLs into text files. |

---

## 9. Context notes (your main quality lever)

Companion notes are the highest-leverage thing you can add. Each `.md` is itself graphed, so a note turns a lone file into a well-connected node. Per [the protocol](#the-protocol-adding-to-the-brain), a note is **required for every dataset, PDF, and document** (recommended for images and audio/video) — the `wdb-curator` agent can draft it for you. The `## Related files` line is where you hand Graphify its edges: fill it with the real siblings the file relates to, and **cross-link across initiative folders**, not just within one (see [How to get the best graph](#how-to-get-the-best-graph-out-of-graphify)). Place each note beside the file it describes, named by **replacing the source file's extension** with `_dict.md` (tabular) or `_context.md` (everything else) — e.g. `kenya_yield_2025.csv` → `kenya_yield_2025_dict.md`, `report.pdf` → `report_context.md`.

**Two kinds of note.** Most are **companion notes** that describe one specific file — `<file>_dict.md` (tabular) or `<file>_context.md` (anything else), named as above, using the templates below. A document that describes a **topic or a whole initiative** rather than a single file is a **standalone `_about.md` doc**: name an aspect doc `<initiative>_<aspect>_about.md` (e.g. `pondcube_data_about.md`, `fasa_repo_about.md`), and **reserve the bare `<initiative>_about.md` for the single whole-initiative overview** (e.g. `pondcube_about.md`) — so a later overview never collides with an aspect doc. Write these freely (no template) but still give each a `## Related files` section. Never give an overview a `_dict`/`_context` suffix — that suffix means "companion to the file of that name."

**Template A — tabular data** (`.csv`, `.xlsx`). Name it the file's name with its extension replaced by `_dict.md` (e.g. `kenya_yield_2025.csv` → `kenya_yield_2025_dict.md`):

```markdown
# Data dictionary: kenya_yield_data_2025.csv

## Summary
One or two sentences: what this dataset tracks and which project it belongs to.

## Columns
- column_name: plain-English meaning (and unit, if relevant)
- column_name: plain-English meaning

## Related files
- related_file_1, related_file_2

## Notes / caveats
Missing values, known skew, or logic the assistant should know when reading it.
```

**Filled example** (note the cross-initiative link in *Related files*):

```markdown
# Data dictionary: kenya_yield_2025.csv

## Summary
Maize yields from the 2025 Kenya pilot — one row per plot per harvest. Part of the
project_kenya_pilot initiative.

## Columns
- plot_id: unique plot identifier (joins to field_map.png)
- harvest_date: harvest date (YYYY-MM-DD)
- yield_kg: harvested maize, kilograms
- variety: seed variety planted

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

---

## 10. Reference project layout

How an initiative folder looks with files and their context notes in place:

```
WDB/
├── .graphifyignore              # what to exclude from the graph
├── .gitignore                   # ignores graphify-out/manifest.json, cost.json
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
└── graphify-out/                # generated — commit this folder
    ├── graph.html
    ├── GRAPH_REPORT.md
    └── graph.json
```

Each file sits inside the project it belongs to; context notes (where used) live right beside their target file; the generated `graphify-out/` folder is committed so teammates share the same map.

---

## Quick command reference

```bash
graphify install                 # register the skill
/graphify .                      # build graph
/graphify . --update             # refresh changed files
/graphify add <url>              # add a paper/video
graphify clone <github-url>      # add a remote repo
/graphify query "what connects X to Y?"
/graphify explain "SomeComponent"
/graphify . --mode deep          # full rebuild, richer connections
```