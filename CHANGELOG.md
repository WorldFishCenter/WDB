# WDB 0.0.5

The release where the system's own contracts get an owner. 0.0.4 built three answering modes, a
router, a read UI and a write-side service; each declared the shapes it shared with the others, and
the copies drifted. This release collapses them — one answer contract, one state machine, one path
resolver, one reranker seam — and fixes what the drift was costing: a **correct answer that reached
the user as a refusal**, two ways to publish a contribution without the curator role, and an upload
that could be written outside the knowledge base.

No new capability. The suite goes from 158 to **211 tests** because most of what changed here was
previously unstated rather than untested.

## Application

* **NEW `wdb_contract` — the §6 answer contract, declared once**
  ([`wdb_contract/`](wdb_contract/)). `Citation` / `Claim` / `Figure` / `Answer` / `Verdict` /
  `Unanswered` lived in six places: three near-copy `mode_*/contract.py` files, the router, the API
  serializer and a hand-typed TypeScript mirror. The modes now alias the citation shape they
  produce, and `RouterAnswer` **inherits** from `Answer` rather than re-listing its fields — which
  is what let the router drop three of them by omission. Merging is one shared `merge()`, not three
  hand-written blocks each reading a different subset.
* **FIXED A verified negative reached the user as a coverage failure.** Mode A can determine that
  the graph records no connection between two entities — no direct edge, no ≤2-hop path — and
  [`mode_a/contract.py`](mode_a/contract.py) calls that a correct answer. The router's merge never
  read the field carrying it, recomputed `answered` from the empty claim list, and the UI rendered
  *"The knowledge base doesn't cover this."* The contract now carries a **`Verdict`** —
  `GROUNDED` / `VERIFIED_NEGATIVE` / `UNGROUNDED` — end to end, and the UI branches on it instead
  of inferring meaning from three empty lists.
* **FIXED Mode C's disambiguation candidates survived only as prose.** When a question matches
  three sister tables, the resolver returns them as a typed list; the merge dropped it, so the
  candidate tables existed on the wire only inside an English sentence. They now ride on the
  `Unanswered` entry that reports the ambiguity.
* **FIXED An un-sourced claim could be emitted.** §6 rule 1 says a claim with zero citations is not
  emitted, but the mechanical cite-check's C1 passes **vacuously** when the reasoner cited nothing
  at all — an empty `cited_edges` list contains no fabrication. `Claim` now refuses construction
  without a citation, so the contract cannot represent the violation, and the reasoning path
  downgrades to a stated refusal.
* **CHANGED Every refusal carries an `UnansweredCode`.** `unanswered` was a list of strings, so the
  only thing downstream could assert on was wording — refusal prose authored in
  [`mode_b/gate.py`](mode_b/gate.py) was pinned by tests in **two other packages**, and editing a
  message broke them. Tests now assert the refusal *arm* (`THIN_RETRIEVAL`, `NOT_CONNECTED`,
  `OUT_OF_BAND`, …). The wire keeps `unanswered` as rendered strings and adds `unanswered_detail`.
* **CHANGED The reranker is an adapter at the retriever seam**
  ([`mode_b/rerank.py`](mode_b/rerank.py)). `LiveRetriever` built its cross-encoder inside
  `__init__` behind a bare `except Exception` that printed a line and returned `None` — which
  silently moved Mode B's refusal floor from the model-calibrated rerank logit to the uncalibrated
  cosine threshold that `gate.py`'s own docstring records as unable to refuse an off-topic question
  (a Norway salmon-farming query scored ~59% against Timor-Leste nutrition passages).
  `CrossEncoderReranker` now **raises** rather than degrading; `NullReranker` makes degrading an
  explicit choice; and `retriever.ranking_kind` states which floor is in force instead of two other
  packages sniffing a private attribute.
* **CHANGED The ingestion gate is the only thing that moves a contribution between states**
  ([`wdb_ingest/gate.py`](wdb_ingest/gate.py)). The gate *decided* a transition and a separate
  `ops.advance` *applied* it, accepting any `(from, to)` pair — so five of six state changes never
  consulted the gate, and the `AUTODRAFT` / `BUILD_TRANSITIONS` tables describing exactly those
  moves had **zero references** in the repo. They are now `SYSTEM_TRANSITIONS`, enforced:
  `gate.apply()` resolves every move against a declared table, refuses a role on a system
  transition and refuses a system action from the wrong state. `BUILT` and `LIVE` are unreachable
  except along the declared path.
* **FIXED `GET /build/status` published contributions, unauthenticated.** The poll auto-detected a
  completed build and advanced every handed-off contribution `QUEUED → BUILT → LIVE`, with no role
  check — unlike `POST /build` and `POST /build/confirm`, which both require the curator. Reading
  the status is now a pure read for everyone; only a curator's poll publishes.
* **FIXED `POST /reset` wiped the workflow store with no role check.**
* **FIXED An upload could be written outside the knowledge base.**
  [`config.INITIATIVES`](wdb_ingest/config.py) carried a comment describing a real past bug — a
  bogus initiative folder getting minted — while having **no uses**: `initiative` arrived as an
  unvalidated query parameter and the promote step called `mkdir(parents=True)` on it. `filename`
  was equally unchecked, so `../../etc/passwd` would have been copied clear of `KB_ROOT`.
  `validate_placement()` now refuses both, before anything is staged.
* **CHANGED The write side resolves paths through [`wdb_paths`](wdb_paths.py) like every reader.**
  `wdb_ingest/config.py` re-derived both roots with the `Path(__file__).parent.parent` climb that
  module exists to replace, and diverged twice: its `WDB_KB` read used a `dict.get` default, so
  `WDB_KB=""` made the **current working directory** the knowledge base on the only side that
  creates directories; and it introduced a second override, `WDB_ROOT`, that no reader knew about,
  so setting it sent approved notes to one knowledge base while the modes read another.
* **CHANGED Mode B's passage index follows the knowledge base it indexes.** It lived inside the
  installed package (`mode_b/.index`) while the corpus walk and the graph join both derive from
  `KB_ROOT` — so pointing `WDB_KB` at a second knowledge base silently kept the first one's index,
  retrieving KB-A's passages and joining them against KB-B's `graph.json`. It is now
  `$WDB_KB/.index`, overridable with **`WDB_INDEX`**, matching
  [`docs/production-stack-design.md`](docs/production-stack-design.md), which already lists the
  Chroma index as a knowledge-base runtime artifact.
* **CHANGED A misconfigured knowledge base is now visible in the read UI.** The source route
  derived its root from the working directory, and every failure path in the graph loader —
  the error field, the JSON parse, the network rejection — was discarded, so a knowledge base the
  server could not locate rendered as a graph with no nodes. `read-ui/lib/kbRoot.ts` resolves the
  root once (validating `WDB_KB`, else searching upward), the route answers **503** with what to
  set, and the answer view states that the graph is unavailable while making clear the answer and
  its citations are not.
* **CHANGED `POST /answer` gains `verdict` and `unanswered_detail`; `/health` gains `rerank_kind`.**
  Additive: every key the UI already read keeps its exact meaning, so the committed
  `read-ui/fixtures/*.json` needed one line each. Two new fixtures cover the verified-negative and
  disambiguation states, which had no offline coverage at all.

## Automated Tooling

* **FIXED `/curate` and `/enrich` instructed the wrong build.** Both agents told the maintainer to
  run `/graphify . --update`, which 0.0.4 recorded as wrong rather than merely noisy — the first
  path segment is read as an initiative name throughout the system. The handoff test asserted only
  that the command contained `/graphify`, so the drift was invisible; it now pins the exact string.

## Documentation

* **CHANGED [`CLAUDE.md`](CLAUDE.md) follows the documented Claude Code standard** — under 200
  lines, organised by topic, and carrying only what cannot be derived from the codebase. It now
  states the two-tree split and the application invariants it was silent on, having documented only
  `/graphify` while the repo grew a nine-thousand-line application.
* **NEW Path-scoped rules** ([`.claude/rules/`](.claude/rules/)) — the answer contract and the
  ingestion workflow, loaded on demand when a matching package is opened rather than on every turn.
* **CHANGED [`RUNNING.md`](RUNNING.md) documents the passage-index location** and `WDB_INDEX`;
  `read-ui/.env.local.example` documents `WDB_KB` as validated-when-set.
* **FIXED [`pyproject.toml`](pyproject.toml)'s version was `0.1.0`** while the release counter,
  the tags and the badges were on `0.0.x`. The release workflow reads the version from this
  changelog and never touched the manifest, so it drifted from the start. All four now agree.

# WDB 0.0.4

The release where WDB stops being a knowledge-graph repo you read and becomes a **system you
query** — three answering modes, a router, a read UI and a write-side ingestion service — and
where the **knowledge base is separated from the application** that reads it. The graph is no
longer the product; it is one of three grounded evidence sources behind a single honest answer.

Two properties are load-bearing throughout: **every claim carries its source**, and **a mode that
cannot ground an answer says so** instead of synthesizing one.

## Application

* **NEW Mode A — graph relationships / enumeration** ([`mode_a/`](mode_a/)). Answers "what
  connects to what" over the committed graph. A **routed augmentation**, not a replacement, of the
  cheap enumeration stand-in: direct questions stay cheap, while multi-hop/explanatory ones get an
  LLM reasoning over a **deterministically-extracted subgraph**, gated by a **mechanical
  cite-check** so a claim that isn't in the subgraph cannot survive.
* **NEW Mode B — passage retrieval + cited synthesis** ([`mode_b/`](mode_b/)). Retrieves verbatim
  passages from WDB's prose and companion notes, synthesizes a cited answer, and joins each passage
  to its **graph associations** at document grain. Returns a clean "not available" when retrieval
  is thin, and **never synthesizes from the model's own knowledge**. Raw tables are deliberately
  kept out of the passage index — they are Mode C's job.
* **NEW Mode C — structured query over the tidy CSVs** ([`mode_c/`](mode_c/)). Answers
  quantitative questions by *querying* the committed CSVs with **DuckDB** rather than retrieving
  prose, reading each table in place and reporting the SQL it ran. Grain-aware: it aggregates over
  the row's real subject (§5 tidy data + the `## Grain` line below), which is what keeps a
  per-catch-item table from being averaged as though it were per-trip.
* **NEW `wdb_router` — the production router** ([`wdb_router/`](wdb_router/)). Classifies a
  question to the relevant mode(s), dispatches to the **real** modes in one pass, and composes one
  answer where every claim keeps its mode tag and native citation, associations are merged and
  deduped, and each mode's refusal is preserved in an `unanswered` list. Reimplements none of the
  modes.
* **NEW `wdb_api` — the local read API** ([`wdb_api/`](wdb_api/)). A thin, faithful FastAPI bridge:
  `POST /answer` returns the full router answer serialized with no field flattened and **no
  synthesis of its own**. A refusal surfaces as what it is — empty `claims`, populated
  `unanswered`, `answered: false`.
* **NEW `read-ui` — the read query UI** ([`read-ui/`](read-ui/)). A local **Next.js + SCSS**
  dual-pane interface: a grounded answer with its sources beside the **interactive knowledge
  graph** of associations around it. Read-only and local; its job is to make the system's honesty
  legible rather than to dress it up. Citations are clickable to their source text through a
  path-sandboxed read-only viewer.
* **NEW `wdb_ingest` — the write-side ingestion service** ([`wdb_ingest/`](wdb_ingest/)). The real
  backend for the contribution flow: a persisted workflow state machine, the **two-stage approval
  gate enforced server-side** (a contributor cannot sign off on their own submission), an approval
  queue, real file + companion-note writes into git, and a **single-builder build handoff** that
  hands the pinned `/graphify` build to the maintainer rather than running an unpinned build itself.
* **NEW `cost_sim`** ([`cost_sim/`](cost_sim/)) — measures real LLM spend under configurable
  per-slot model assignments.
* **NEW One reproducible environment** ([`pyproject.toml`](pyproject.toml) + `uv.lock`,
  Python 3.14 pinned). All modes, the router, the services and every test suite share one declared,
  locked dependency set recreated with `uv sync --extra dev` — replacing the borrowed `civ-kb`
  virtualenv the code used to depend on.
* **CHANGED The knowledge base is separated from the application.** Initiative folders and the
  built graph move under **`knowledge_base/`**; the app locates them through
  [`wdb_paths.py`](wdb_paths.py) — the single source of truth for `REPO_ROOT` / `KB_ROOT` —
  replacing the `Path(__file__).parent.parent` walk each module did for itself. `KB_ROOT` is
  overridable with **`WDB_KB`**, so the application can be pointed at any knowledge base. This is
  the boundary [`docs/production-stack-design.md`](docs/production-stack-design.md) §2 recommended,
  and it is what lets the repo be published as a reusable system: a user brings their own
  `knowledge_base/`.
* **FIXED** Mode B's corpus walk indexed **application** files — 39 where the intended corpus is
  **34** (`RUNNING.md`, `mode_a/MODEL.md`, `proof_a/FINDINGS.md`). Rooting the walk at the
  knowledge base removes the leak by construction instead of by maintaining a blocklist of the
  app's own filenames.
* **CHANGED** `read-ui`'s source-viewer sandbox is rooted at the knowledge base rather than the
  repo, so it can no longer read application source files.

## Contributing Protocol

* **NEW** Every table's `_dict.md` states its **grain** in a dedicated `## Grain` section: what one
  row *is* in domain terms (its real-world subject), and which higher-grain columns repeat across a
  coarser key. This closes the silent grain trap at the source for every consumer of the data, not
  just Mode C.
* **NEW** A **habit-4 carve-out** separating grain from shape. Grain names the row's real-world
  subject and this table's own columns, so it can only link **same-subject** tables (two
  per-catch-item trip tables) — never every table of a shape. Naming the subject is domain meaning;
  naming the wide/long form is not, and stays banned.
* **CHANGED** Habit 1 — notes are drafted as **self-contained prose that names its subject by the
  initiative's one canonical name** ("Peskas", never "the platform" or a pronoun), so a note reads,
  retrieves and resolves well as a Mode-B passage. Self-containedness must never be reached for via
  shape, encoding, file type or producing script; grain stays in its own `## Grain` line, never the
  Summary.
* **CHANGED** Initiative folders live in **`knowledge_base/`**, not the repo root. Paths in the
  protocol are knowledge-base-relative — `peskas/…` means `knowledge_base/peskas/…` on disk, and
  that is how they appear in the graph. §3 and the layout tree say so; `USER_GUIDE.md` step 2 points
  contributors at the folder.
* **CHANGED** The maintainer build is **`/graphify knowledge_base --update`** (was
  `/graphify . --update`). Building from the repo root is now wrong, not merely noisy: the **first
  path segment is read as an initiative name** throughout the system (Mode C derives a table's
  identity tokens from it; the router derives `known_initiatives` from it), so a repo-root build
  would invent a `knowledge_base` "initiative" and pollute entity resolution.
* **CHANGED** `.graphifyignore` moves to `knowledge_base/.graphifyignore` and drops its long list of
  application excludes (`mode_a/`, `read-ui/`, `tests/`, `docs/`, …) — those paths sit outside
  graphify's root now, so they cannot leak into the corpus at all.

## Automated Tooling

* **CHANGED** `dict_enricher.py` derives **grain deterministically** — for long tables the
  measurement and its dimension columns; for wide tables a non-unique id/code key and the columns
  constant within it. Emitted in the text report and `--json`. It names domain columns, never the
  wide/long form.
* **CHANGED** `/enrich` (`dict-enricher.md`) fills `## Grain` from the script's facts plus the
  Summary's row-subject noun; the blanket grain ban is lifted while the format/tooling ban stays.
* **CHANGED** `/curate` (`wdb-curator.md`) gains a "write prose that also reads well out of context"
  subsection carrying the habit-1 enforcement detail, with an explicit habit-4 guard and a
  frozen-snapshot caveat (forward-looking; never rewrite a frozen section).

## Documentation

* **NEW** [`RUNNING.md`](RUNNING.md) — the one reproducible environment: prerequisites, `uv sync`,
  and how to run every mode, the router, the API and the tests.
* **NEW** [`docs/production-stack-design.md`](docs/production-stack-design.md) — the
  knowledge-base / application separation, a grounded coupling audit, and the build-and-publish
  flow. **NEW** [`docs/ingestion-pipeline-design.md`](docs/ingestion-pipeline-design.md) — the
  write-side contribution pipeline `wdb_ingest` implements. **NEW**
  [`docs/model-cost-strategy.md`](docs/model-cost-strategy.md) — which model slots may move
  cheaper, and the proof each move is gated on.
* **NEW** `model_eval/` (**not published** — its samples and drafts carry real rows and
  extracted paper text; kept local like `proof_a`/`proof_c`) — a fair-prompt, proof-gated honesty
  and cost evaluation of cheaper models per slot (Haiku 4.5, Gemini 2.5 Flash, and DeepSeek via an
  OpenRouter gateway arm). **Verdict: no pin changed.** Mode A and Mode C stay on Opus 4.8 — Haiku
  fabricates, and both gateway candidates still miss Mode C's EAV case. DeepSeek's clean Mode-A
  sheet is the strongest cheap result so far but rests on n=10, so it is recorded as
  *inconclusive-promising*, not earned. The harness validated itself against both baselines first
  (Mode C 9/9, Mode A 0 fabrications/10).

## Knowledge Graph Infrastructure

* **CHANGED** Full graph rebuild, reducing node and edge counts in favour of consistency: **172
  nodes · 324 edges · 9 communities**, a single connected component over an 11-file, ~15.7k-word
  corpus.
* **NEW** `BUILD_INFO.md` records the provenance of every build — date, the exact model ID, the
  graphify version, the build mode, and the node/edge counts — so a model or tool-version change
  shows up as a reviewable diff in the pull request.

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
