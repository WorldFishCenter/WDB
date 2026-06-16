# WDB — production stack design (knowledge-base / application separation)

**Date:** 2026-06-16 · **Status:** DESIGN ONLY — decision document for sign-off; **moves nothing,
deploys nothing** · **Builds on:** [three-mode-architecture.md](three-mode-architecture.md) (the
modes + router), [../RUNNING.md](../RUNNING.md) (the one reproducible env + the persistent-host
constraint), [../PROTOCOL.md](../PROTOCOL.md) §1/§9 (single-builder + build reference),
[../CLAUDE.md](../CLAUDE.md) (pinned-model provenance).

**What this is / is not.** This proposes how to separate WDB's **knowledge base** (data; changes on
every contribution) from its **application** (code; changes on release), what stays in git vs. moves
to GCS, how the single-builder flow **publishes** artifacts the deployed service reads, and the
Cloud Run shape — and it surfaces the genuine forks for the requester. It **does not** move files,
split repos, write a Dockerfile / API / cloud config, or rebuild the graph. The deliverable is this
document; the build is the **next** task, after sign-off.

---

## 1. Current coupling (grounded audit)

WDB was built to run locally with `/graphify` pointed at the repo root, so three things with
different lifecycles share one tree.

### 1.1 What lives in the repo, by lifecycle

| Lifecycle | Paths | Tracked? |
|---|---|---|
| **Knowledge base — data; changes on contribution** | Initiative folders [peskas/](../peskas/), [fasa/](../fasa/), [data_harmonization/](../data_harmonization/), [ssf_research/](../ssf_research/), [digital_transformation_accelerator/](../digital_transformation_accelerator/) (incl. `pondcube/`): source files (`.csv`, `.pdf`, `.docx`, `.pptx`) **+** companion notes (`_dict.md`, `_context.md`, `_about.md`). Plus the **built graph** in [graphify-out/](../graphify-out/). | git |
| **Application — code; changes on release** | [mode_a/](../mode_a/), [mode_b/](../mode_b/), [mode_c/](../mode_c/), [wdb_router/](../wdb_router/), [tests/](../tests/), [pyproject.toml](../pyproject.toml), [uv.lock](../uv.lock), [.python-version](../.python-version), [RUNNING.md](../RUNNING.md). | git |
| **Scaffolding — POC / dead weight** | `civ-kb/`, `proof/`, `proof_a/`, `proof_c/`, `docs/` | **gitignored** ([.gitignore](../.gitignore)) — 0 tracked files; `.graphifyignore`d too. Local only. |
| **Governance** | [PROTOCOL.md](../PROTOCOL.md), [README.md](../README.md), [USER_GUIDE.md](../USER_GUIDE.md), [CLAUDE.md](../CLAUDE.md), [CHANGELOG.md](../CHANGELOG.md), [.graphifyignore](../.graphifyignore), [.claude/](../.claude/) (curator/enricher agents, skills) | git |

`graphify-out/` itself splits: **committed** (`graph.json`, `graph.html`, `graph.svg`,
`GRAPH_REPORT.md`, `BUILD_INFO.md`, `cache/semantic/`, `converted/`) vs. **gitignored, regenerable**
(`manifest.json`, `cost.json`, `cache/stat-index.json`, `.graphify_*`, dated backups) — per
[.gitignore](../.gitignore). The Mode-B Chroma index ([mode_b/.index/](../mode_b/)) is likewise
gitignored and regenerable.

### 1.2 Every application → knowledge-base read-path (what the split must preserve)

| Mode | What it reads | How it locates it |
|---|---|---|
| **Mode A** | `graphify-out/graph.json` | Module constant `GRAPH_PATH = Path(__file__)...parent.parent / "graphify-out" / "graph.json"` ([mode_a/extract.py:36](../mode_a/extract.py#L36)); `get_graph()` takes **no path override** ([mode_a/extract.py:325-326](../mode_a/extract.py#L325-L326)) — the **one hard-coded read**. |
| **Mode B** | prose corpus (PDF/docx/pptx/md + companion notes), `graphify-out/graph.json` (join), Chroma index | `walk_corpus(root)` in place ([mode_b/corpus.py:64](../mode_b/corpus.py#L64)); `DEFAULT_ROOT`/`DEFAULT_GRAPH` = repo-relative ([mode_b/pipeline.py:23-24](../mode_b/pipeline.py#L23-L24)); index at `mode_b/.index/` via `PersistentClient(path=index_dir)` ([mode_b/index.py:33,64](../mode_b/index.py#L33), [index.py:95-103](../mode_b/index.py#L95-L103)), rebuilt by `--ingest`. |
| **Mode C** | the tidy `.csv` files **at query time** + their `_dict.md` | `load_catalog(root)` globs `**/*_dict.md` ([mode_c/catalog.py:208-234](../mode_c/catalog.py#L208-L234)); DuckDB `read_csv_auto('{abs_path}')` reads each CSV **in place, never copied** ([mode_c/executor.py:97,157](../mode_c/executor.py#L97)); `abs_path = root/table` ([mode_c/catalog.py:67-68](../mode_c/catalog.py#L67-L68)). |
| **Router** | constructs all three backends; derives `known_initiatives` from `walk_corpus(root)` | `WDB_ROOT = Path(__file__)...parent.parent` ([wdb_router/backends.py:31](../wdb_router/backends.py#L31)); `replay_backends`/`live_backends` accept a `root=` override ([backends.py:58,94](../wdb_router/backends.py#L58)). |

### 1.3 The central coupling fact

**Every module locates the knowledge base by walking up the filesystem from its own source file
(`Path(__file__)...parent.parent`) and assuming the KB sits as sibling directories in the same
tree.** That implicit *"the app lives inside the KB repo root"* assumption is the single thing the
separation must replace — with an explicit, configurable KB/artifact location.

Most of the plumbing to do that **already exists**: Mode B, Mode C, and the router all take a `root=`
argument and Mode B takes `index_dir=`; only their *defaults* are repo-relative. The lone gap is
**Mode A's `GRAPH_PATH`**, a module constant with no override ([extract.py:36](../mode_a/extract.py#L36)) —
parameterizing that one path is the only code change the split strictly forces.

**Corroborating finding (an argument *for* a clean KB root):** the Mode-B corpus walk today indexes
app/scaffolding files — `RUNNING.md`, `mode_a/MODEL.md`, `proof_a/FINDINGS.md`, `proof_a/results.md`,
`proof_a/subgraphs.txt` — because the exclusion set ([mode_b/corpus.py:30-39](../mode_b/corpus.py#L30-L39))
omits `mode_a`/`proof_a` and doesn't filter top-level infra Markdown like `RUNNING.md`. A live
`walk_corpus(.)` returns **39** files where the intended KB corpus is **~34**. Once the corpus is
rooted at a *clean KB tree*, these can't leak in and the app stops needing a blocklist of its own
files. The separation removes a class of bug, it doesn't just relocate one.

---

## 2. The knowledge-base / application split

### Fork 2a — one repo (hard internal boundary) vs. two repos

The decisive insight: **runtime decoupling does not come from the repo boundary — it comes from
publishing artifacts to GCS (§3).** At runtime the deployed service reads only *built artifacts*
(`graph.json`, the Chroma index, the queryable CSVs), never the KB source tree. So the repo question
is purely about the **contribution-vs-release developer workflow**, not about how production reads
data.

- **One repo, hard internal boundary (RECOMMENDED now).** Move the KB under one top-level dir (e.g.
  `knowledge_base/` holding the initiative folders + `graphify-out/`) and the app under another (e.g.
  `app/` holding the modes, router, tests, `pyproject.toml`). One PR flow, one CI, and the app's
  regression suites keep seeing the committed `graph.json` they depend on
  ([mode_b/tests/conftest.py:22](../mode_b/tests/conftest.py#L22)) with no cross-repo fetch.
  *Tradeoff:* content and code still share an issue tracker / release tag; the boundary is convention
  + path config, not enforced by separate access control.
- **Two repos (the clean future split).** A `wdb-knowledge-base` repo (content + protocol + curator/
  enricher + the build) and a `wdb-app` repo (modes + router + serving). Cleanest lifecycle
  decoupling; content contributors never clone the app; matches "data repo vs. code repo." *Tradeoff
  (real):* the app's tests load the **committed** real `graph.json`/graph-derived fixtures, so a split
  forces the app to vendor a *pinned* graph fixture or fetch a known version — cross-repo coordination
  the single small team doesn't need yet.

**Recommendation:** one repo with a hard internal boundary now; **split to two repos when the web
ingestion front door (§6) lands** — that is the moment non-coders contribute content and genuinely
shouldn't touch the app repo. (The §3 publish pipeline works identically either way, so deferring the
repo split costs nothing later.) *Note: the **move** that formalizes this boundary is the next task,
not this one.*

### Fork 2b — what stays in git vs. moves to GCS

The protocol's review/PR/curator/enricher discipline depends on human-readable, version-controlled
files — so the rule is **source-of-truth and anything a human reviews stays in git; machine-built
outputs the service consumes go to GCS.**

| Class | Examples | Disposition | Why |
|---|---|---|---|
| Companion notes | `_dict.md`, `_context.md`, `_about.md`, `idea_*.md` | **git, always** | The protocol's reviewable core; `/curate` + `/enrich` + PR operate on these. **Never** a DB ([constraint](#constraints-honoured)). |
| Tidy CSVs | `kenya_validated_trips.csv`, FASA/PondCube tables | **git (source of truth) AND published to GCS (§3)** | Small text, diff-able; the `/enrich` shape-gate + PR review need them in the PR. Mode C reads them at serve time → also published so the service needn't clone the KB. |
| Built graph | `graph.json` (+ `graph.html`/`.svg`/`GRAPH_REPORT.md`/`BUILD_INFO.md`) | **git (provenance) AND published to GCS (§3)** | Committed because `BUILD_INFO.md` + the graph diff are the reproducibility record ([CLAUDE.md](../CLAUDE.md)); published because Mode A + Mode B read it at runtime. |
| Mode-B vector index | `mode_b/.index/` (Chroma) | **GCS only** (already gitignored, regenerable) | A machine artifact, not reviewed; rebuilt on publish. |
| Large binaries | source PDFs / `.docx` / `.pptx` | **git for now; LFS-or-GCS later** | Read only at **build/ingest** time (graphify + Mode-B extraction), **never by the serving app**. Corpus is tiny (~34 files), so git keeps one-clone reproducibility + provenance. Flag for git-LFS or a GCS "source bucket" once binary volume grows. |

**Do not move notes or source text into a database** — they are protocol-governed, human-readable,
version-controlled by design.

---

## 3. The build-and-publish flow

**Today:** the maintainer runs `/graphify . --update`, commits `graphify-out/`
([PROTOCOL §9](../PROTOCOL.md)); the Mode-B index is built locally with `python -m mode_b --ingest`
into the gitignored `mode_b/.index/`. Both are local/committed artifacts — nothing publishes them to
a place a service can fetch.

**Proposed single-builder publish flow** (preserves [PROTOCOL §1](../PROTOCOL.md) — only the
maintainer builds *and* publishes):

1. Maintainer merges content PRs (the existing curator/enricher/PR gate — unchanged).
2. Maintainer runs the **pinned-Opus** build `/graphify . --update` → regenerates `graphify-out/` and
   (over)writes `BUILD_INFO.md` (date, exact model id, graphify version, mode, node/edge counts) per
   [CLAUDE.md](../CLAUDE.md). Still committed to git.
3. Maintainer rebuilds the Mode-B index (`python -m mode_b --ingest`).
4. **Publish:** copy the **runtime artifacts** — `graph.json`, the Chroma index dir, and the queryable
   CSVs — to a **versioned, immutable GCS prefix**, e.g.
   `gs://wdb-artifacts/<version>/{graph.json, chroma/, csv/}`, where `<version>` is tied to the build
   (build date + graphify version + commit SHA — the same identity `BUILD_INFO.md` records). Write a
   small `gs://wdb-artifacts/MANIFEST.json` (or move a `latest` pointer) naming the current good
   version.

**Versioning (pin a known-good graph).** The service runs against an **explicit** artifact version,
never "whatever is newest" — the same discipline as the pinned build model: a bad or half-published
build cannot silently reach production, and a graph regression is reproducible from its version tag.

**Picking up a new graph without a code redeploy.** Bump the pinned version in config (an env var
`WDB_ARTIFACT_VERSION`, or advance the `MANIFEST.json`/`latest` pointer) and restart the Cloud Run
**revision** (no image rebuild — Cloud Run revisions are cheap). A `/reload` admin endpoint that
re-fetches and hot-swaps the in-memory graph + reopens the Chroma collection is a later nicety, not
needed first. **The point:** publishing artifacts and deploying app code are **separate pipelines on
separate cadences** — the runtime expression of the §2 split. Nothing here lets a contributor mutate
the served graph; the PR + single-builder gate is the only way in.

---

## 4. Deployment shape (Cloud Run)

The host must be **persistent / container-style, not serverless**: Mode B loads `torch` + the
cross-encoder reranker on startup, and that reranker is **load-bearing for Mode B's honesty** (it
gates off-topic questions before synthesis). A serverless cold-start per request would reload those
models — [RUNNING.md:80-96](../RUNNING.md#L80-L96), [pyproject.toml:19-24](../pyproject.toml#L19-L24).

Proposed shape (specification only — the Dockerfile + API code are the **build** task):

- **Container** = the `wdb` distribution (app code), built with `uv sync --frozen` against `uv.lock`
  on `python:3.14-slim` ([RUNNING.md:88-89](../RUNNING.md#L88-L89)). One reproducible env, already in
  place.
- **HTTP API: FastAPI** (fits the team's stack) wrapping `wdb_router.answer(question, backends)` —
  e.g. `POST /answer` → the §6 `RouterAnswer` contract; optional `GET /classify` (the
  `--classify-only` decision); `GET /healthz`. The router is already a clean library entry point
  ([wdb_router/dispatch.py](../wdb_router/dispatch.py)) — the API just wraps it.
- **Startup, once per instance:** construct `live_backends(...)` ([backends.py:94](../wdb_router/backends.py#L94)) —
  load the embedder + cross-encoder, open the Chroma collection, load `graph.json` + the catalog — and
  reuse across requests (the backends are already designed to be pre-constructed).
- **Models:** pre-fetch the two HF models into the image at build time (or mount a cache) with
  `HF_HOME` set; weights never committed ([RUNNING.md:90-92](../RUNNING.md#L90-L92)).
- **Artifacts:** fetched from the pinned GCS version (§3) into a local dir on startup; the existing
  `root=` / `index_dir=` / graph-path plumbing points there (after Mode A's `GRAPH_PATH` is made
  overridable, §1.3).
- **Secrets:** `ANTHROPIC_API_KEY` (live synthesis + Mode C resolver + Mode A reasoner) injected at
  runtime via Secret Manager, never committed ([RUNNING.md:95-96](../RUNNING.md#L95-L96)).
- **Cheapest correct, reusing Peskas infra:** same GCP project, the GCS + Cloud Run patterns the team
  already runs for Peskas; single region, single service, `min-instances=1` (keeps models warm), CPU
  torch (sufficient per [pyproject.toml:38](../pyproject.toml#L38)). No multi-region, no autoscaling
  complexity.

---

## 5. The Mode-B vector index in production (decide, don't over-build)

- **Now: keep file-based Chroma, rebuilt on publish.** On a few-dozen-file corpus the rebuild is
  seconds and the index is already a gitignored, regenerable artifact ([mode_b/index.py](../mode_b/index.py),
  [.gitignore](../.gitignore)). Ship it as a published GCS artifact (§3). Nothing to build.
- **Later: MongoDB Atlas vector search** — the **migration target**, named now, adopted **not now**.
  Atlas is available and has native vector search, but introducing a managed vector DB at this scale
  is exactly the premature scaling the project avoids everywhere else.
- **Trigger / signal to migrate** (any one): (a) a full rebuild-on-publish stops being trivial —
  roughly a **few-thousand-document** corpus, or index rebuild creeping past a couple of minutes, or
  the index no longer sitting comfortably in container memory; (b) ingestion goes **incremental**
  (the web front door, §6) so you can no longer rebuild the whole index per change; or (c) you already
  operate Atlas for other WDB data and consolidating stores wins. Until one fires, Chroma is the
  correct choice.

---

## 6. Ingestion — the phasing boundary (recorded, not designed)

This section **records** a boundary the requester has set; it does **not** design a front door.

- **Initial phase = the existing flow IS the ingestion mechanism.** `curate → enrich → PR →
  single-builder build` already provides human control over what enters the brain — **the PR review
  *is* the control gate** ([PROTOCOL §1-§2](../PROTOCOL.md)). The local Claude Code flow (contributors
  run `/curate` + `/enrich`; the maintainer runs `/graphify`) bridges the gap with no new
  infrastructure.
- **Explicitly LATER, separable projects:** a **web ingestion front door** (so non-coders can
  contribute) and **automated quality verification**. Both write to the **knowledge-base side only**
  and **must run the existing gates** (curator + enricher + PR) — they may *feed* the pipeline, never
  *bypass* it. A future front door's output is still a placed file + companion note routed through the
  same PR + single-builder build.
- **Why it fits cleanly:** the §2 KB/app split + the §3 publish pipeline are exactly what leaves room
  for this — a front door targets the KB side, and the single-builder publish step is unchanged.

---

## 7. Recommendation, forks for sign-off, and sequencing

### 7.1 Recommended stack (cheapest correct, reuses Peskas GCP)

- **One repo, hard internal KB/app boundary** now; two repos when the §6 front door lands.
- **Git:** companion notes + source text + tidy CSVs (source of truth) + the committed graph +
  PDFs (for now). **GCS:** the runtime artifacts — `graph.json`, the Chroma index, the queryable CSVs
  — under a versioned, immutable prefix.
- **Single-builder publish:** pinned-Opus `/graphify` build → commit `graphify-out/` → publish runtime
  artifacts to `gs://wdb-artifacts/<version>/` + a `MANIFEST.json` pointer.
- **Cloud Run** persistent container (`min-instances=1`), FastAPI over `wdb_router.answer()`, models on
  startup, artifacts fetched from the pinned GCS version, `ANTHROPIC_API_KEY` via Secret Manager —
  reusing the team's Peskas Cloud Run + GCS infra.
- **Vector index:** Chroma now; Atlas vector search later (trigger in §5).
- **Ingestion:** the existing curate/enrich/PR/single-builder flow; web front door + auto-QA are
  later, gated, separable.

### 7.2 The genuine forks — **your** decisions

1. **One repo or two?** → *Recommend one now; split when the web ingestion front door lands.* Two-repo
   is cleaner lifecycle decoupling but forces the app to vendor/fetch a pinned `graph.json` test
   fixture (cross-repo coordination). **(§2a)**
2. **Exactly what moves to GCS?** → *Recommend: built artifacts (graph.json + Chroma index + queryable
   CSVs) → GCS; notes + source text + the CSV source-of-truth stay in git.* Sub-fork: **do the source
   PDFs move to GCS/LFS now, or stay in git?** → *Recommend stay in git now* (tiny corpus), move when
   binary volume grows. **(§2b)**
3. **How does the service pick up a new graph?** → *Recommend a config-pinned artifact version +
   Cloud Run revision restart now; a `/reload` hot-swap endpoint later.* The rejected alternative is
   always-pull-latest, which breaks the pinned-known-good reproducibility discipline. **(§3)**

### 7.3 Sequencing

1. **This design → approved** (you sign off on the three forks above).
2. **The stack build** (next task): formalize the KB/app boundary (the move + parameterize Mode A's
   graph path, §1.3); add the GCS publish step to the single-builder flow; add the FastAPI entry +
   Dockerfile; deploy to Cloud Run — **plus the read query UI on top.**
3. **Web ingestion front door + automated QA** — later, separable, gated (§6).

### 7.4 Risks to the protocol (flagged, per the constraints)

- **Notes/source into a DB** → rejected; would break the human-readable / reviewable /
  version-controlled core. The only DB candidate is the Mode-B index (Atlas), and only later (§5).
- **Always-latest artifact pickup** → breaks pinned reproducibility; use pinned versions (§3).
- **A careless two-repo split** → app tests depend on the committed `graph.json`
  ([mode_b/tests/conftest.py:22](../mode_b/tests/conftest.py#L22)); without a pinned fixture the suites
  break. Coordination cost, not a blocker (§2a).
- **Corpus-walk leak** ([mode_b/corpus.py:30-39](../mode_b/corpus.py#L30-L39)) → the boundary work in
  step 2 should also fix the exclusion gap so app/scaffolding files stop entering the index (§1.3).

### Constraints honoured

Design only — nothing moved, split, built, or deployed; no Dockerfile / API / cloud config written.
The single-builder rule, the PR flow, the companion-note structure, and the curator/enricher gates are
preserved in every proposal; anything that would weaken them is flagged above as a risk, not a
feature.
