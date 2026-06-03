# WDB — WorldFish Digital Brain

A shared Graphify knowledge graph for the WorldFish Digital Brain (WDB) project. This README is the working standard for the repo: it explains how to set up Graphify and how to organize files so every team member works from the same map of our code, datasets, and documents.

### 🧠 Open the knowledge graph

**[▶ Explore the interactive graph →](graphify-out/graph.html)**

Clone the repo and open that file in any browser to explore the full WDB map — nodes, communities, and search. It's regenerated on every `/graphify .` or `/graphify . --update` run, so the committed copy always reflects the latest graph. (On github.com the link shows the file's source; download or clone the repo to open it live — GitHub can't render interactive HTML inline.)

> **Not a coder?** To add a file, dataset, or idea without touching the command line, follow **[USER_GUIDE.md](USER_GUIDE.md)** instead — a click-by-click walkthrough with no graph-tool setup.

## Contents

- [1. One-time setup (each team member)](#1-one-time-setup-each-team-member)
- [2. Workspace organization (Project-First rule)](#2-workspace-organization-project-first-rule)
- [3. Building the graph](#3-building-the-graph)
- [4. Controlling what gets indexed](#4-controlling-what-gets-indexed)
- [5. Adding external sources](#5-adding-external-sources)
- [6. Updating the graph](#6-updating-the-graph-dont-rebuild-from-scratch)
- [7. Team workflow (the shared standard)](#7-team-workflow-the-shared-standard)
- [8. File-type reference](#8-file-type-reference)
- [9. Optional: context notes](#9-optional-context-notes)
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

---

## 7. Team workflow (the shared standard)

This is what keeps everyone on the same map.

1. **One person builds the graph** with `/graphify .` and commits the `graphify-out/` folder to git.
2. **Everyone else pulls** — their assistant reads the committed graph immediately, no rebuild needed.
3. **Install the git hook** so the graph auto-rebuilds on each commit (AST only, no API cost) and `graph.json` is union-merged to avoid conflicts:

   ```bash
   graphify hook install
   ```

4. **When docs or papers change**, run `/graphify . --update` to refresh those nodes.

**Add to `.gitignore`** (these are local-only and break when shared). Keep each comment on its **own line** — an inline `# ...` after a pattern becomes part of the pattern, so the rule silently never matches:

```
# manifest.json + cache/stat-index.json are mtime/path-based (invalid after clone);
# cost.json is local token tracking; .graphify_root/.graphify_python are absolute paths.
graphify-out/manifest.json
graphify-out/cost.json
graphify-out/cache/stat-index.json
graphify-out/.graphify_root
graphify-out/.graphify_python

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

## 9. Optional: context notes

Graphify does **not** require companion files — this is a team convention, not a tool feature. But because any `.md` you add is itself graphed, a short note next to a file can improve how it connects. Keep notes optional and lightweight, and place them in the same project folder as the file they describe. Two templates cover most cases.

**Template A — tabular data** (`.csv`, `.xlsx`). Name it `<exact_filename>_dict.md`:

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

**Template B — everything else** (PDFs, docs, images, audio/video). Name it `<exact_filename>_context.md`:

```markdown
# Context: grant_proposal_kenya.pdf

## Summary
One or two sentences: what this file is and why it's in the workspace.

## Key concepts / entities
- Regions, methods, or topics this file is about

## Related files
- related_file_1, related_file_2
```

---

## 10. Reference project layout

How an initiative folder looks with files and (optional) context notes in place:

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
│   ├── field_map_context.md              # Template B (optional)
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
graphify hook install            # auto-rebuild on commit
```