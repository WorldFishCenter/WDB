# `read-ui` — WDB read query UI (dual-pane)

A local **Next.js + SCSS** read interface over the Phase-A1 API ([`wdb_api`](../wdb_api)). You ask
a question; it shows a **grounded answer with its sources** next to the **graph associations** around
it — the "passage + associations" dual view. It is **read-only** (it queries, it never adds or edits
knowledge) and **local** (it talks to the local API; nothing is deployed).

Its whole job is to make the system's **honesty legible** — exactly what the API returns, nothing
added:

- **Every claim shows its source TYPE** at a glance — `A` graph fact, `B` grounded passage,
  `C` computed figure — each with its native citation (the edge triple, the verbatim quote, or the
  SQL + result rows).
- **EXTRACTED vs INFERRED** is marked distinctly — an inferred graph edge never reads as a hard fact.
- **`unanswered` is shown as first-class** — what the system could not ground is displayed as such,
  never hidden.
- A **full refusal** renders as an honest "the knowledge base doesn't cover this", never a blank
  screen or a fabricated-looking answer.

It matches the [worldfish.digital](https://github.com/WorldFishCenter/worldfish.digital) visual
identity — the same palette, Noto Sans / Chivo type, dark hero, and component feel — using the real
extracted tokens in [`styles/tokens.scss`](styles/tokens.scss).

## Run it (local)

```bash
# 1. Start the Phase-A1 API from the repo root (Replay = key-free, deterministic):
uv run uvicorn wdb_api.app:app          # serves http://127.0.0.1:8000

# 2. In another shell, start the UI:
cd read-ui
npm install
npm run dev                             # http://localhost:3000
```

Open http://localhost:3000 and ask a question, or click an example. The UI shows an honest status
of which backend the API loaded (Replay vs Live).

Point at a different API with `WDB_API_URL` (see [`.env.local.example`](.env.local.example)).

## How it connects to the API

The browser never calls the API cross-origin (the API is left untouched — no CORS middleware added).
Instead, same-origin Next route handlers proxy to it:

| Route | Proxies to | Purpose |
| --- | --- | --- |
| `POST /api/answer` | `POST {WDB_API_URL}/answer` | the question → the full §6 answer, verbatim |
| `GET /api/health` | `GET {WDB_API_URL}/health` | backend (Replay/Live) + reachability |
| `GET /api/source?path=` | reads the repo (read-only) | opens a citation's source note/doc |

## Built against the REAL contract

The renderer targets the **actual** JSON captured from the running API in STEP 0, saved in
[`fixtures/`](fixtures) — one file per state the UI must handle:

| Fixture | Exercises |
| --- | --- |
| `single_mode_a.json` | Mode A only — graph-fact claims + associations |
| `quantitative_c.json` | Mode C — a scalar claim **and a figure** (bar chart + SQL + rows) |
| `blended_abc.json` | all three citation shapes at once + EXTRACTED/INFERRED edges |
| `partial_blend.json` | some grounded, some `unanswered` in one answer (`answered: true`) |
| `refusal.json` | a full honest refusal (`answered: false`) |

The TypeScript types in [`lib/contract.ts`](lib/contract.ts) mirror these shapes.

## Ingestion — the write side (`/contribute` + `/curate`), wired to a REAL backend

Two routes realizing the write-side flow from
[`../docs/ingestion-pipeline-design.md`](../docs/ingestion-pipeline-design.md) — the *second page of
this same product* (same [`styles/tokens.scss`](styles/tokens.scss), root layout/fonts, component
idioms). These are **wired to a real backend** — the [`wdb_ingest`](../wdb_ingest) FastAPI service —
not mock data: submitting really stages a file, drafting really runs the enricher, sign-off really
writes the companion note into the initiative folder in git, and Build really hands off to the pinned
graph build.

| Route | View | What it really does |
| --- | --- | --- |
| `/contribute` | Contributor | upload a file → the enricher drafts the companion note (Template A/B, real value domains for tables) → review/edit → **approve → PENDING** ("awaiting curator review", *cannot go live*) |
| `/curate` | Curator | the **PENDING queue** → review/edit (curator override) → **sign off → writes note to git + QUEUED**, or send back; **Build** hands the queue off to the pinned single-builder build, then publishes QUEUED → BUILT → LIVE |

The **two-stage gate** is enforced **server-side** in [`../wdb_ingest/gate.py`](../wdb_ingest/gate.py)
(not just the UI): the role is derived from the route and sent as a header; a contributor request for
the curator sign-off is refused with **403**. The two views share the one backend, so a contributor
approval really appears in the curator queue.

**How it connects:** [`lib/ingestion/api.ts`](lib/ingestion/api.ts) → the same-origin proxy
[`app/api/ingest/[...path]/route.ts`](app/api/ingest) → `WDB_INGEST_URL` (default
`http://127.0.0.1:8001`). If the service is down, the views show an **honest offline banner** (the read
UI's Live/Replay posture) — they never fabricate data.

```bash
# 1. ingestion backend (write side):
uv run uvicorn wdb_ingest.app:app --port 8001
# 2. read API + UI as above; then open /contribute and /curate.
```

**Build fidelity (important):** the guarded WDB build (the two CLAUDE.md extraction guards + the
canonical-entity remap) only applies in the maintainer's pinned `claude-opus-4-8` `/graphify` session —
it is **not** in the `graphify` CLI. So Build does **not** fake a headless build: it hands the queue off
to the pinned build (surfacing the exact command) and detects completion. See
[`../wdb_ingest/README.md`](../wdb_ingest/README.md).

## Scope

The read side is the dual-pane query page; the write side is the real `wdb_ingest` service above. Local,
production-shaped: the workflow store (SQLite) and blob staging are swap-in seams for Atlas/GCS, and
auth/deploy are deferred — see [`../wdb_ingest/README.md`](../wdb_ingest/README.md).
