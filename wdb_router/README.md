# wdb_router — the production router (dispatcher) over Modes A + B + C

Given one question, the router **classifies** it to the relevant mode(s), **dispatches** to
those real modes in one pass, and **composes** their results into one §6 answer where every
claim is sourced and every mode's refusal is respected. It is the production replacement for
the throwaway `router/` harness (which carried a Mode-A *stand-in*); this package calls the
**real** Mode A, B, and C as libraries and reimplements none of them.

It is a **dispatcher**, not an agent: a one-pass fan-out + merge. See "The seam" for how a
future agentic version slots in without rework — and note that **no** agent machinery (no
loop, no state machine, no orchestration framework) is built here.

## What it does (three-mode architecture doc [§5](../docs/three-mode-architecture.md)–[§7](../docs/three-mode-architecture.md))

1. **Route** (`routing.py`) — `route(question) -> RoutingDecision`. The transparent §5
   keyword pass: a question is scanned for signals and routed to **every** mode whose signal
   fires (≥1 always); blended questions fan out, ambiguous ones fan out to all three. Each
   route records the signal that selected it. Pure: it takes only the question.
2. **Dispatch + compose** (`composition.py`) — `compose(question, decision, backends)`. Calls
   each named mode's real entry point (`mode_a.answer_question`, `mode_b.answer_question`,
   `mode_c.answer_question`) and merges the §6 fragments into one `RouterAnswer`: claims (each
   with its mode tag + ≥1 native citation), merged graph associations, Mode-C figures, and an
   `unanswered` list for anything no mode could ground.
3. **Tie-point** (`dispatch.py`) — `answer(question, backends)` = route then compose, once.

## The seam (routing ↔ composition) — a clean boundary, not machinery

Routing **decides which modes**; composition **calls them and assembles**. They are separate,
cleanly-bounded pieces:

- `route` is a pure `question -> RoutingDecision` (no backends, no mode calls — the signature
  enforces it).
- `compose` consumes a decision it did **not** make and merges additively into the contract.
- `answer` (in `dispatch.py`) ties them in **one pass** today.

That boundary is the room left for a future agent: an agentic router that picks the *next*
mode from a previous mode's answer would replace the body of `answer` with a loop calling
`route`/`compose` repeatedly and accumulating into one `RouterAnswer` — changing **neither
the modes nor the contract**. We build none of that loop now. (`test_seam.py` proves routing
is computed independently of, and composition dispatches exactly, the decision.)

Mode-C table/column resolution (§5 layer 2) lives **inside Mode C**; the router invokes it via
`mode_c.answer_question`, never reimplements it.

## Honesty carries over from the modes — the router never weakens it

- No claim without a citation: the router only concatenates the claims the modes return; it
  never synthesizes one (§6 r1).
- A mode that grounds nothing contributes to `unanswered`; the router **never** back-fills that
  gap with another mode's content (§5, §6 r4).
- Each mode's own refusal — Mode B's reranker-gated thin refusal, Mode C's vetted-band gate,
  Mode A's cite-check downgrade — happens inside its entry point; the router surfaces it and
  **never routes around it**.

## Run it

One interpreter with all three modes' deps — that is WDB's own consolidated environment
(see [../RUNNING.md](../RUNNING.md)):

```bash
uv sync --extra dev        # creates .venv/ with all three modes' deps, per uv.lock
```

```bash
# single-mode (deterministic Replay backends — no model, no network)
uv run wdb-router "What projects operate in Kenya?"                 # → Mode A (real enumeration)
uv run wdb-router "Average total catch per trip in Kwale?"          # → Mode C
uv run wdb-router "How does Peskas validate catch survey data?"     # → Mode B

# blended — composes A + B + C into one answer
uv run wdb-router "Which datasets feed Peskas, how does Peskas validate catch \
survey data, and what is the average total catch per trip in Kwale?"

# just show the routing decision
uv run wdb-router --classify-only "Average catch by county"

# LIVE: Mode A Opus 4.8 reasoner, real Chroma + cross-encoder reranker (Mode B),
# Opus 4.8 resolver (Mode C). The off-topic refusal arm needs the reranker but NOT an
# API key (the gate refuses before any model call):
uv run wdb-router --live "What is the impact of salmon cage farming on fjord water quality in Norway?"
#  → UNANSWERED: top passage rerank score < floor → "not available", not a synthesis
```

## Tests

```bash
uv run pytest wdb_router/tests -v
```

Deterministic (Replay) by default; the one `@pytest.mark.live` test (real reranker off-topic
refusal) self-skips when Chroma / the cross-encoder are unavailable, so offline CI passes on
the deterministic version of that arm. The suite covers single-mode grounding, blended
composition, routing in isolation, the routing↔composition **seam**, and honesty
pass-through (each mode's refusal surfaces as `unanswered`, never back-filled or routed
around).
