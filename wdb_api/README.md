# `wdb_api` — the read UI's HTTP backend

A thin, faithful **FastAPI** wrapper over the production router's single entry point
([`wdb_router.answer`](../wdb_router/dispatch.py)). It exposes the router over HTTP so the read
UI (next phase) has a backend to call, and serializes the full §6 answer contract
([`RouterAnswer`](../wdb_router/contract.py)) to JSON — **dropping nothing** the contract
carries and **adding no synthesis of its own**.

Runs **locally** — not deployed. No auth, no Dockerfile, no caching/middleware (those are later
phases). The persistent-host reality (Cloud Run, not serverless) is why models load once on
startup; see [`RUNNING.md`](../RUNNING.md).

## Endpoints

| Method & path | Body | Returns |
| --- | --- | --- |
| `POST /answer` | `{"question": "…"}` | the serialized `RouterAnswer` (see below) |
| `GET /health`  | — | `{status, backend: "live"\|"replay", reranker_loaded}` |

### `POST /answer` response shape

```jsonc
{
  "question": "…",
  "answered": true,                       // contract property
  "modes_fired": ["A", "B", "C"],         // modes routed-to
  "modes_grounded": ["A", "C"],           // modes that actually contributed a claim/figure
  "routes":  [{"mode": "A", "reason": "signal: which"}],
  "claims":  [{"mode": "A", "text": "…", "citations": [ /* mode-specific */ ]}],
  "associations": [{"source": "…", "relation": "…", "target": "…", "confidence": "…"}],
  "figures": [{"spec": {…}, "query": "SELECT …", "result": [{…}]}],   // Mode C only
  "unanswered": ["… — reason no mode could ground it"]
}
```

A claim's `citations` keep each mode's **native artifact** (keyed by `claim.mode`):

- **A** — `{source_file, note, locator, confidence}` — the graph edge triple.
- **B** — `{source_file, note, location, quote, nodes[]}` — the passage span + verbatim quote + graph node(s).
- **C** — `{source_file, note, sql, result[]}` — the query and its result rows.

Honesty survives serialization: an `unanswered` entry stays in `unanswered`; a refusal returns
`claims: []` with `answered: false`; no claim ever lacks a citation.

## Run it

```bash
# Live (real reranker + Opus 4.8 arms) when ANTHROPIC_API_KEY is set, else offline Replay.
uv run uvicorn wdb_api.app:app --reload

curl -s localhost:8000/health
curl -s localhost:8000/answer -H 'content-type: application/json' \
     -d '{"question": "What projects operate in Kenya?"}' | python -m json.tool
```

## Tests

```bash
uv run pytest wdb_api/tests      # offline (Replay), no model, no network
```
