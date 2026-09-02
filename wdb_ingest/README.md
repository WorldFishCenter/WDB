# `wdb_ingest` — the write-side ingestion service

The real backend for the contribution flow designed in
[`../docs/ingestion-pipeline-design.md`](../docs/ingestion-pipeline-design.md): a persisted workflow
state machine, the **two-stage approval gate enforced server-side**, an approval queue, real file +
companion-note writes into git, and a **single-builder build handoff**. It is the write-side
counterpart to [`wdb_api`](../wdb_api) (the read side) and mirrors its shape (`create_app()` +
injectable store + sync endpoints). Local and production-shaped — not deployed.

## Run it

```bash
uv run uvicorn wdb_ingest.app:app --port 8001      # the read UI's /contribute + /curate wire to this
```

The read UI proxies to `WDB_INGEST_URL` (default `http://127.0.0.1:8001`). With the service down, the UI
shows an honest offline banner — it never fabricates data.

## The flow (state machine + the two gates)

```
SUBMITTED → DRAFTED → UNDER_REVIEW → PENDING → QUEUED → BUILT → LIVE        (+ REJECTED send-back)
            (enrich/   (contributor   (curator   (note→git, (pinned     (published)
             scaffold)  approves =     signs off  enters     /graphify
                        stage-1 gate)  = stage-2)  queue)     build)
```

- **Submit** — the uploaded bytes are staged under `_staging/<id>/` (gitignored); provenance (§8) is
  stamped now; a workflow row is created.
- **Draft** — for a **tabular** file the real [`.claude/scripts/dict_enricher.py`](../.claude/scripts/dict_enricher.py)
  fills the Template-A `## Columns` with **actual value domains**; meanings + grain are scaffolded for
  review (the `/curate`/`/enrich` division). PDFs/docs get a Template-B scaffold. **No LLM, no invented
  prose.**
- **The two-stage gate** ([`gate.py`](gate.py)) — enforced server-side. A **contributor** can only reach
  `PENDING`; only a **curator** moves `PENDING → QUEUED`; only the build moves `QUEUED → BUILT → LIVE`.
  Role comes from the `X-WDB-Role` header; a contributor request for the curator action is refused
  **403**. `gate.contributor_reachable_states()` proves (in tests) the contributor can never reach
  QUEUED/BUILT/LIVE.
- **Sign-off (the hard handoff)** — the staged file is copied into its **existing** initiative folder and
  the companion note is written to **git** (the system of record from here on, design §5); then `QUEUED`.
  No initiative-folder reorganization happens here — that is a separate PR.
- **Build** — see below.

## The build: a tracked handoff, not a faked headless build

**Finding (verified):** the guarded WDB build — the two [`CLAUDE.md`](../CLAUDE.md) extraction guards
(format-blind similarity + canonical-entity) and the canonical-id remap — is performed by the
maintainer's pinned **`claude-opus-4-8`** `/graphify` session, which injects those guards into the
extraction subagents (see [`../graphify-out/BUILD_INFO.md`](../graphify-out/BUILD_INFO.md)). They are
**not** built into the `graphify` CLI. So there is **no faithful headless build**.

Therefore [`builder.py`](builder.py) does **not** run a headless build and call it faithful. `POST /build`
snapshots the graph, marks the QUEUED items handed off, and surfaces the **exact pinned command**
(`/graphify . --update`). It then detects completion (graph.json changed vs. the baseline) — or
`POST /build/confirm` confirms manually — and advances the handed-off items to `LIVE`. A module lock
makes it single-builder. Nothing is auto-committed: the maintainer reviews the git diff and opens a PR.

## Storage & the swap seams (production-shaped, local now)

Per design §8, the **workflow state** belongs in a database and **approved notes** belong in git. Here:

| Concern | Local default | Production swap (same interface) |
|---|---|---|
| Workflow state | `SqliteWorkflowStore` ([`store.py`](store.py)) at `_state/workflow.db` | a `MongoWorkflowStore` → Atlas — the `WorkflowStore` protocol is the seam |
| Approved notes + tidy files | written into the git working tree | unchanged — git is canonical (design §5) |
| Staged binaries | `_staging/<id>/` (gitignored) | GCS source bucket |
| Identity / role | `X-WDB-Role` / `X-WDB-User` headers | real auth (OIDC) — same header contract |

`_state/` and `_staging/` are gitignored; `wdb_ingest/` is `.graphifyignore`d (tooling, not knowledge).
Atlas/GCS/auth/deploy are **not provisioned here** (no URIs/secrets/targets in this environment) — they
are clean seams, a config/credentials change away.

## Tests

```bash
uv run pytest wdb_ingest          # gate truth table, the end-to-end flow + git writes, the HTTP gate
```
