# WDB — multi-model cost-optimization strategy (which slots may move to a cheaper model, and how)

**Date:** 2026-06-17 · **Status:** DOC ONLY — strategy record; **changes no pin, swaps no model,
builds nothing** (no `pyproject`/dependency change, no provider integration, no code) · **Builds on:**
[three-mode-architecture.md](three-mode-architecture.md) §9 (governance — pin & record each model
choice), [../CLAUDE.md](../CLAUDE.md) (pinned-model provenance & reproducibility),
[../mode_a/MODEL.md](../mode_a/MODEL.md), [../mode_b/MODEL.md](../mode_b/MODEL.md),
[../mode_c/MODEL.md](../mode_c/MODEL.md) (the per-slot model records this strategy annotates),
[../.claude/agents/wdb-curator.md](../.claude/agents/wdb-curator.md),
[../.claude/agents/dict-enricher.md](../.claude/agents/dict-enricher.md) (the ingestion agents).

**What this is / is not.** This records **which** LLM slots in WDB could move to a cheaper model,
**under what condition**, and **via what evaluation path** — so the door is open and the rules are
explicit *before* cost becomes a real budget line. It is a forward-looking record only. It **does
not** change any pinned model, touch `pyproject.toml` or dependencies, write any provider
integration, or build the split. **Today's pins stay exactly as recorded:** Opus 4.8 for the graph
build, Mode C resolver, and Mode A reasoner; Sonnet 4.6 for Mode B synthesis. The per-`MODEL.md`
notes added alongside this doc are forward-looking pointers, not changes.

---

## 1. The principle — split by *validated honesty*, not by *importance*

The naive split — "crucial tasks → the premium model, everything else → the cheap model" — is
**backwards**. It would move the safest slots (the ones a human reviews anyway) onto the premium
model and risk the most dangerous ones (autonomous, no human to catch a regression) on a cheaper
model whose behavior was never measured here.

The governing question is **not** "is this task important?" It is:

> **Was this task's correctness validated on a specific model, AND does it gate honesty with no
> human in the loop?**

That yields two tiers:

- **Autonomous honesty-critical → pinned Anthropic, non-negotiable.** The slot's *honest behavior
  was measured on the pinned Claude model* (a proof recorded a rate or a verdict), and **no human
  reviews the output before a user sees it.** Swapping the model **invalidates the measurement**,
  and there is no human to catch the resulting regression. These stay pinned.
- **Grounded or human-reviewed → cheaper-model candidate, with proof.** Either a deterministic
  mechanism does the honesty work *before* the model runs (retrieval + reranker + a refuse gate),
  or a **human reviews the output before it takes effect** (the PR / approval gate). These **may**
  move to a cheaper model — but **only after re-running that slot's existing proof against the
  candidate model and reading the verdict** (§3). Prove-before-swap, exactly as everything else in
  this project was proven before it was built.

The point of the tier test is that it is *mechanical*: it asks where the honesty guarantee lives
(in a measured model, or in a deterministic gate / a human), not how it feels.

---

## 2. Per-task placement

| Slot | Where pinned today | Tier | Why |
|---|---|---|---|
| **Graph build (`/graphify`)** | Opus 4.8 ([../CLAUDE.md](../CLAUDE.md)) | **Pinned Anthropic — non-negotiable** | The committed graph's consistency depends on the **exact** model ([../PROTOCOL.md](../PROTOCOL.md) §9 reproducibility). A model change must be a deliberate, visible `BUILD_INFO.md` diff — not a cost optimization. |
| **Mode C resolver** | Opus 4.8 ([../mode_c/MODEL.md](../mode_c/MODEL.md)) | **Pinned Anthropic — non-negotiable** | The grain + derived-metric guards were validated on Opus (`proof_c/RESOLVER_FINDINGS.md`); a weaker model risks the **silent grain trap** — a confident, wrong number. **No human in the loop.** |
| **Mode A reasoner** | Opus 4.8 ([../mode_a/MODEL.md](../mode_a/MODEL.md)) | **Pinned Anthropic — non-negotiable** | The **0/10 cold-fabrication rate** was *measured* on Opus. The cite-check catches fabrication mechanically, but its firing **rate** (i.e. utility — how often it must downgrade) is unmeasured on any other model. **No human in the loop.** |
| **Mode B synthesis** | Sonnet 4.6 ([../mode_b/MODEL.md](../mode_b/MODEL.md)) | **Cheaper-model candidate** | Lower-risk: retrieval + reranker + the **refuse-when-thin gate** do the honesty work *before* synthesis; the synthesizer only writes up already-vetted passages. (Already Sonnet, not Opus — the split has effectively begun.) |
| **Curate / enrich agents** (ingestion) | Opus 4.8 ([wdb-curator](../.claude/agents/wdb-curator.md), [dict-enricher](../.claude/agents/dict-enricher.md)) | **Cheaper-model candidate** | Counterintuitively *tolerant* **because the output is human-reviewed before it enters the KB** — the PR / approval gate is the safety net. A cheaper model drafting a note you then verify is far safer than a cheaper model answering live. |
| **Intent classifier** | — (deliberately model-free) | **Nothing to optimize** | Keyword-only by design ([../wdb_router/routing.py](../wdb_router/routing.py)); no model, no cost. |

The asymmetry is the whole insight: the **ingestion agents** look "important" (they shape the KB)
yet are the *safest* to economize, because a human signs off; the **Mode A/C live slots** look like
back-office plumbing yet are the *least* safe, because they answer a user directly with no review.

---

## 3. The proof-gated swap procedure (the key enabler)

Swapping a model on a candidate slot is **not a leap of faith** — the validation tooling already
exists. The swap procedure is literally *"re-run the slot's own proof against the candidate model
and read the verdict."* A candidate that **passes** has earned the slot; one that **fails** has not.

| Candidate slot | Proof to re-run against the candidate | Pass condition |
|---|---|---|
| **Mode B synthesis** | The faithfulness / refusal checks ([../mode_b/tests/test_synth.py](../mode_b/tests/test_synth.py), [../mode_b/tests/test_gate.py](../mode_b/tests/test_gate.py); `proof/FINDINGS.md`). The soft risk to watch is **prose-overclaim** — does the candidate overclaim *beyond* the retrieved passages? The refuse gate does not catch that. | Refuses when retrieval is thin; synthesis stays faithful to the cited passages. |
| **Curate / enrich agents** | No formal proof harness — the **review gate is the proof**: have the candidate draft notes and confirm they pass curator/maintainer review **reliably enough to be worth it**. | Draft notes pass review at a rate that makes the saving worthwhile. |

**For the non-negotiable slots, the proof path exists but the door stays shut.** Recorded here only
so it is not *bricked* shut — not as an invitation:

- **Mode A** (if ever reconsidered) → re-run `proof_a/` — the **negative control**
  (`proof_a/negative_control.py`) **and** the cold-fabrication-rate
  measurement (`python -m mode_a.cold_rate`).
- **Mode C** (if ever reconsidered) → re-run `proof_c/` — the **9 resolver questions + the
  naive-control traps** (`proof_c/query.py`; `proof_c/RESOLVER_FINDINGS.md`).

A free or cheaper model that **passes** these proofs would have earned the slot. Until one is run
and passes, these slots remain pinned Anthropic.

---

## 4. The cheap-model evaluation path

The goal when cost becomes real is **evaluation** — cheaply finding out whether a cheaper model is
*good enough* for a candidate slot — **not** production hosting. Two evaluation paths, lowest-risk
first:

1. **Cheaper Claude tier first (Opus → Sonnet → Haiku).** Before any non-Anthropic model, try a
   **smaller Claude** (e.g. Haiku) on the candidate slot. Its behavior is the **most comparable** to
   the validated Claude models, so it is the **smaller leap** — evaluated the *same* proof-gated way
   (§3). Haiku 4.5 (`claude-haiku-4-5-20251001`) is available today; confirm the current Haiku id at
   evaluation time.
2. **Google AI Studio (free tier) for non-Anthropic candidates.** A lightweight API key with a
   genuine **free tier**, built for prototyping — the right tool for cheaply running a slot's proof
   against a candidate Gemini model and reading the verdict. This is the *"is this model good
   enough?"* step, and it is free/fast. Free-tier **specifics** (which models are free, rate limits)
   change — **verify at evaluation time**; the durable fact is that AI Studio is the cheap, no-commit
   *evaluation* path.

A candidate is a candidate whether it is Haiku or a Gemini model — both go through the same
proof-gate. Haiku is just the smaller leap.

**The two-stage shape:** **evaluate cheaply** (Haiku / AI Studio free tier, run the slot's proof) →
**if it passes its proof, adopt it.** Production *hosting* is a separate, later, deployment-phase
matter — not part of this strategy.

> **Out of scope — Vertex AI (deployment-phase forward-pointer only).** Vertex AI is Google's
> enterprise, pay-as-you-go production platform (service-account auth, no comparable free tier). It
> is **not** the cheap path for *evaluating* a model and is explicitly excluded here. *If WDB is
> later deployed to production on GCP, Vertex AI is the natural production host for whatever models
> earned their place (auth / billing / data alignment with Cloud Run) — but that is a deployment-phase
> decision, out of scope for this strategy.* Do not build toward it or base the strategy on it.

---

## 5. Timing — do not build this now

**Do not build the split now.** At the current corpus (~34 indexable files) the Live LLM cost is
**negligible**, so multi-model optimization is not worth building: the validation effort (re-running
proofs, wiring a second provider) would **exceed the saving**.

- **Trigger to revisit:** when **Live query volume makes LLM cost a real budget line.** That is the
  signal to pick up the first candidate slot (Mode B synthesis, or the ingestion agents) and run the
  §3 proof-gate via the §4 evaluation path.
- **Until then:** **Replay** for development (offline, free — the `Replay*` paths in each mode), and
  **direct Anthropic** for the occasional Live query. The pins stay as recorded.

This document is the record so that, when the trigger fires, the *rules* are already decided: which
slots may move, what proof each must pass, and where to evaluate cheaply — leaving only the
measurement to run.
