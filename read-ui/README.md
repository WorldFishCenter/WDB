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

## Ingestion prototype — the write side (`/contribute` + `/curate`)

Two **styled, interactive prototype** routes that realize the parked write-side flow from
[`../docs/ingestion-pipeline-design.md`](../docs/ingestion-pipeline-design.md) — built as the *second
page of this same product*, reusing the read UI's design system wholesale (same
[`styles/tokens.scss`](styles/tokens.scss), the shared root layout/fonts, the same card/chip/button
idioms). They run **entirely on mock data** — there is **no ingestion backend yet** (this is the same
fixtures-first stage the read side was in before Live).

| Route | View | What it does |
| --- | --- | --- |
| `/contribute` | Contributor | submit a file → mock auto-draft (companion note, Template A/B) → review/edit → **approve → PENDING** ("awaiting curator review", *cannot go live*) |
| `/curate` | Curator | the **PENDING queue** (fed by contributor approvals) → review/edit (curator override) → **sign off → QUEUED** or send back; a single-builder build drains QUEUED → BUILT → LIVE |

The **two-stage approval gate** is the point and is enforced *by construction* in
[`lib/ingestion/store.tsx`](lib/ingestion/store.tsx): contributor actions can only reach **PENDING**;
only the curator moves PENDING → QUEUED. The two views share one mock workflow store (React context +
localStorage), so a contributor approval really shows up in the curator queue. Every mock shape in
[`lib/ingestion/`](lib/ingestion) mirrors the eventual ingestion API (design §8) so wiring a real
backend later is a swap, not a rewrite. Labelled throughout as **prototype · mock data**.

## Scope (deliberately narrow)

The read side is one clean dual-pane query page; the write side is a **mock prototype** (above), not a
live ingestion backend. **No** real ingestion API/workflow store/server-side agents, **no**
deployment/Vercel config, **no** auth. Those come later, gated on production-stack sign-off.
