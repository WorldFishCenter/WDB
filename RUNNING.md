# Running WDB — the one reproducible environment

WDB runs entirely under **its own** environment now: all three modes (A/B/C), the router
harness, and every test suite share **one** declared dependency set, recreatable from
[pyproject.toml](pyproject.toml) + the committed [uv.lock](uv.lock) — no borrowed venv, no
"and also `pip install duckdb` by hand". (Historically this ran under `civ-kb/.venv`; that
coupling is gone. `civ-kb/` stays on disk but WDB no longer depends on it.)

## Prerequisites

- **Python 3.14** — pinned in [.python-version](.python-version); declared `>=3.14,<3.15` in
  the manifest. Exact-minor pin, matching the pinned-model reproducibility discipline
  ([CLAUDE.md](CLAUDE.md) §"Build model & provenance").
- **[uv](https://docs.astral.sh/uv/)** (developed against 0.9.x) — installs the interpreter
  and the locked dependency graph.

## Recreate the environment (from the manifest alone)

```bash
uv sync --extra dev        # creates .venv/ with the full stack + pytest, exactly per uv.lock
```

That single command is the whole setup. `uv sync` reads `uv.lock` (131 pinned packages) and
builds an identical `.venv` every time; `--extra dev` adds `pytest`. To refresh the lock after
editing dependency ranges in `pyproject.toml`: `uv lock`.

The stack it installs: **chromadb, sentence-transformers, torch** (Mode B retrieval + the
cross-encoder reranker), **pymupdf / python-docx / python-pptx** (document extractors),
**duckdb** (Mode C structured query), **anthropic** (live LLM calls), and **pytest** (dev).

## Run it

Prefix with `uv run` (resolves the env) or call `.venv/bin/python` directly.

```bash
# Per-mode CLIs — deterministic Replay backends by default (no model, no network)
uv run python -m mode_a "What projects operate in Kenya?"                # enumeration
uv run python -m mode_c "Average total catch per trip in Kwale?"         # quantitative
uv run python -m mode_b --list-corpus                                    # indexable files

# The system entry point — the production router dispatches a question across all three
# modes and composes one §6 answer (calls the real Mode A/B/C; see wdb_router/README.md).
uv run python -m wdb_router "Which datasets feed Peskas, and what is the average catch in Kwale?"
uv run python -m wdb_router --classify-only "Average catch by county"    # just the routing decision

# LIVE — Mode A Opus 4.8 reasoner, real Chroma + cross-encoder reranker (Mode B), Opus 4.8
# resolver (Mode C). Mode B's off-topic refusal needs the reranker but NOT an API key (the
# gate refuses before synthesis); live *synthesis*, the Mode C resolver and the Mode A
# reasoner need ANTHROPIC_API_KEY.
uv run python -m mode_b --ingest                                         # build the passage index first
uv run python -m wdb_router --live "What is the impact of salmon cage farming on Norwegian fjords?"
#   → UNANSWERED: top passage rerank score < floor → "not available", not a synthesis
```

Console-script aliases are also declared (`mode-a`, `mode-b`, `mode-c`, `wdb-router`), e.g.
`uv run wdb-router --classify-only "…"`.

## Tests

```bash
uv run pytest          # all four suites in one run (uses testpaths + --import-mode=importlib)
```

Per-suite counts (the green baseline): **mode_c 40, mode_a 21, wdb_router 29, mode_b 33,
wdb_api 21, wdb_ingest 15** — 159 passed, 1 skipped (live synthesis self-skips without `ANTHROPIC_API_KEY`). The combined run uses
`--import-mode=importlib` because some suites share test-file basenames (`test_gate.py`,
`test_pipeline.py`). The `@pytest.mark.live` reranker-refusal test runs end-to-end when the models
are available and self-skips otherwise, so offline CI still passes.

## The services (read + write)

```bash
uv run uvicorn wdb_api.app:app                       # read API (the read UI's backend) → :8000
uv run uvicorn wdb_ingest.app:app --port 8001        # ingestion write-side (the /contribute + /curate backend)
```

`wdb_ingest` is the contribution workflow: submit → enrich-draft → the two-stage gate → note-to-git on
sign-off → single-builder build handoff. See [`wdb_ingest/README.md`](wdb_ingest/README.md). Its local
state (`wdb_ingest/_state`, `_staging`) is gitignored.

## Models (embedder + reranker)

Mode B loads two models from the Hugging Face hub **at runtime**, cached under `~/.cache/huggingface`
(override with `HF_HOME`). Weights are **never committed**:

- embedder — `paraphrase-multilingual-MiniLM-L12-v2` ([mode_b/model.py](mode_b/model.py))
- cross-encoder reranker — `cross-encoder/mmarco-mMiniLMv2-L12-H384-v1` (Mode B's honesty arm)

First live run downloads them (a few hundred MB); subsequent runs hit the cache.

## Containerizing later (deployment-aware — not built here)

This environment is shaped so a `Dockerfile` is a short hop; **no deployment infra is built in
this task.** When that step comes:

- **Host must be persistent / container-style — Cloud Run (per team infra), NOT serverless
  (Vercel).** Mode B loads the embedder + reranker on startup; a serverless cold-start per request
  would reload them. (Vercel is for the future UI frontend only.)
- **Build:** `uv sync --frozen` against `uv.lock` reproduces the exact env inside the image — one
  line. Pin the base to `python:3.14-slim`.
- **Models:** pre-fetch the two HF models in the build (a `SentenceTransformer(...)` /
  `CrossEncoder(...)` warm-up step) or mount a cache volume, and set `HF_HOME` to a known path —
  so the container doesn't download on first request. Do not bake weights into the repo.
- **Entry point:** today the system entry is `python -m router` (the harness). The production
  router will define the served entry point in a later phase.
- **Secrets:** `ANTHROPIC_API_KEY` for live synthesis / the Mode C resolver, injected at runtime
  (never committed).
