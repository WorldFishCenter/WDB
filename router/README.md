# router — throwaway test harness over Modes A + B + C

⚠️ **Disposable.** This is the terminal-level validation of the *composition logic*
and the *answer contract* (three-mode architecture doc
[§5](../docs/three-mode-architecture.md)–[§7](../docs/three-mode-architecture.md))
— **not** the product router and **not** a UI. It exists so a person can ask one
question and watch all three modes compose, before any frontend. It reuses the
modes as libraries and reimplements nothing — *except* a harness-grade Mode-A
stand-in (see below).

## What it does

1. **Classify** the question into one or more modes by §5 keyword signals
   (`router/intent.py`) — transparent, every route records the signal that fired.
2. **Dispatch** to each routed mode as a library: Mode B (`mode_b.answer_question`),
   Mode C (`mode_c.answer_question`), Mode A (`router.mode_a`, the stand-in).
3. **Compose** their fragments into one §6 `RouterAnswer` — claims (each with its
   mode tag + ≥1 citation), merged graph associations, Mode-C figures, and an
   `unanswered` list for anything no mode could ground (never back-filled).

## Mode A is a STAND-IN, not built

The real Mode A (architecture §2, §10) is **Claude reasoning over `graph.json`**
via `/graphify`; there is no Mode-A *library*. `router/mode_a.py` is a deliberately
thin, deterministic graph **enumeration** — just enough to validate composition +
the contract. Later phases must build the real Mode A and must not treat this as
finished. It does honour Mode A's honesty rule: prefer `EXTRACTED`, flag
`INFERRED`, enumerate nothing it cannot cite.

## Run it

The harness needs **one interpreter with all three modes' deps** —
chromadb + sentence-transformers + torch (Mode B) **and** duckdb (Mode C). That is
WDB's own consolidated environment now (it used to borrow `civ-kb/.venv`); build it once
from the manifest — see [../RUNNING.md](../RUNNING.md):

```bash
uv sync --extra dev        # creates .venv/ with all three modes' deps, per uv.lock
```

```bash
# single-mode (deterministic Replay backends — no model, no network)
uv run python -m router "What projects operate in Kenya?"                 # → Mode A
uv run python -m router "Average total catch per trip in Kwale?"          # → Mode C
uv run python -m router "How does the platform validate catch survey data?"  # → Mode B

# blended — composes A + B + C into one answer
uv run python -m router "Which datasets feed Peskas, how does Peskas validate catch \
survey data, and what is the average total catch per trip in Kwale?"

# just show the routing decision
uv run python -m router --classify-only "Average catch by county"

# LIVE: real Chroma + cross-encoder reranker (Mode B), Opus 4.8 resolver (Mode C).
# The off-topic refusal arm needs the reranker but NOT an API key (the gate
# refuses before synthesis):
uv run python -m router --live "What is the impact of salmon cage farming on fjord water quality in Norway?"
#  → UNANSWERED: top passage rerank score < floor → "not available", not a synthesis
```

## Tests

```bash
uv run pytest router/tests -v
```

Deterministic (Replay) by default; the one `@pytest.mark.live` test (real reranker
off-topic refusal) self-skips when Chroma / the cross-encoder are unavailable, so
offline CI passes on the deterministic version of that arm.

## What this phase verified

- Blended questions route to >1 mode and assemble into one contract where **every
  claim is traceable to its mode + source** (§6 r1).
- Enumeration → A, synthesis → B, quantitative → C (reusing each mode's proof case).
- `unanswered` is populated, never silently dropped, when a mode grounds nothing.
- **Mode B's score-arm refusal — proven in practice.** The off-topic Norway
  question, run live through the real cross-encoder, scored the top passage at a
  **negative logit (≈ -5.5 < `RERANK_FLOOR` 0.0)** and **refused** — closing the
  arm Phase 2 left unproven (where the ~59% bi-encoder cosine would not have).
