# Model evaluation — fair-prompt, proof-gated honesty + cost test of cheaper models per slot

**Date:** 2026-06-18 · **Status:** read-only evaluation experiment — **changes no pin, swaps no model,
touches no mode/router/API/MODEL.md/`graphify-out/`.** The deliverable is findings, not a
reconfiguration. Scratch lives in `model_eval/` (git-ignored byproducts, `.graphifyignore`'d — an
experiment like `proof_a`/`proof_c`); the harness + this doc are committed so the PR into `feat-rag`
has a diff.

**What this answers.** [docs/model-cost-strategy.md](../docs/model-cost-strategy.md) records *which*
slots may move to a cheaper model and *that* the move is gated on re-running each slot's own proof.
This experiment actually **runs those proofs** against two candidates — **Haiku 4.5** and **Gemini 2.5
Flash** — each on a **fair, model-appropriate prompt against an identical bar**, measures real
per-operation cost, attributes every failure, and gives a per-slot verdict + a bottom-line assignment.

**Baselines (reference rows):** Opus 4.8 for Mode A/C and the ingestion agents, Sonnet 4.6 for Mode B
— the current pins. Both baselines reproduced their recorded results through this harness (Mode C
**9/9**, Mode A **0 fabrications/10**), which is what validates the harness before any candidate is judged.

---

## 1. Method — identical bar, per-model expression, each provider's own structured output

The fairness principle: **quality = model × prompt × structured-output reliability**, so the
*requirements* (grain rule, cite-check rule, refuse-when-thin rule, note structure) are the spec and
do **not** bend per model; only their *expression* is adapted.

- **Haiku is a Claude model** → its fair prompt **is** the existing pinned Claude prompt
  (`mode_c/resolver.build_resolver_prompt`, `mode_a/reasoner.SYSTEM_PROMPT`, `mode_b/synth.SYSTEM_PROMPT`).
  Rewriting it would be the unfair move, so the runners import those verbatim.
- **Gemini** gets the same requirements re-expressed Gemini-style (numbered imperatives, "return JSON
  only"), recorded in [`prompts.py`](prompts.py) (`mode_c_gemini`, `MODE_A_GEMINI`, `MODE_B_GEMINI`,
  `INGESTION_BRIEF`). Diff them against the modes' prompts to confirm the bar held.
- **Each provider's native structured-output mechanism** is used (this is part of the
  structured-output-reliability axis, not a confound to hide): Gemini via `responseSchema`
  ([`schema_gemini.py`](schema_gemini.py) translates the modes' JSON schema into Gemini's OpenAPI
  subset); Anthropic via **prompt-for-JSON + tolerant parse**, because — **a real finding** —
  `output_config.format` **rejects `RESOLUTION_SCHEMA` with "Schema is too complex"** (the
  `LiveResolver` path is never exercised by the offline suite, so this was latent). The downstream
  gate/executor value conventions both providers need (aggregation ∈ {AVG…}, `pinned_by` = a bare
  distinctive value, name a derived metric) are stated identically to every model
  (`prompts.RESOLVER_CONVENTIONS`).

Every candidate is judged by the slot's **own existing mechanism** (DuckDB execution vs ground truth;
the deterministic `citecheck`; the refuse-when-thin gate; the protocol note rubric). Verdicts are
labeled **mechanical** vs **judgment** — they are not equally rigorous and the report does not pretend
they are.

---

## 2. Per-slot × per-model verdict + measured cost

`$/op` = real token usage from the live run × verified rates (Opus $5/$25, Sonnet $3/$15, Haiku
$1/$5 per 1M; Gemini 2.5 Flash $0.30/$2.50, **thinking billed as output**). Gemini's high output
tokens are mostly *thinking* (see §6).

| Slot | Type | Opus 4.8 / Sonnet 4.6 (ref) | Haiku 4.5 | Gemini 2.5 Flash |
|---|---|---|---|---|
| **C resolver** (9 Q) | mechanical | **9/9** · $0.0627/op | **7/9** · $0.0097/op | **8/9** · $0.0040/op |
| **C — grain trap** (decisive) | mechanical | ✅ 31.88 | ✅ 31.88 | ✅ 31.88 |
| **A reasoner** (cold, 10 Q) | mechanical | **0 fab / 0 rej** · $0.0373/op | **1 fab / 2 rej** · $0.0052/op | **0 fab / 1 trunc** · $0.0034/op |
| **A — negative control** | mechanical | guard has teeth (model-independent): injected fabrication caught ✅ |||
| **B synthesis** (2 probes) | mech + judg | covered ✅ / overclaim ✅ · $0.0027/op | ✅ / ✅ · $0.0006/op | ✅ / ✅ · $0.0008/op |
| **Ingestion** (2 notes) | judgment | publish-grade · $0.0365/op | strong skeleton, *invented links* · $0.0047/op | honest, *under-wired* · $0.0065/op |

Failure attribution (required): **reasoning** = got the task wrong; **structured-output** = reasoned
acceptably but emitted malformed/truncated structure; **prompt-fit** = looks like phrasing
misunderstanding (→ inconclusive). No failure in this run looked like prompt-dialect confusion; the
attributions below are reasoning or structured-output.

---

## 3. Mode C resolver — MECHANICAL (baseline 9/9; Haiku 7/9; Gemini 8/9)

Every candidate resolution was run through the **real pipeline**: the `vetted_band` gate (which
*structurally* refuses the grain trap) then the DuckDB `executor` over the committed CSVs; the figure
is compared to ground truth computed by executing the proof's recorded Opus resolutions
(13.86 / 1.64 / 7.62 / **31.88** / 441.18 / 62.62).

- **The decisive grain trap (Q4, "avg total catch per trip in Kwale") passed on all three** — every
  one deduped to `trip_id` and computed **31.88**, never the raw-row **28.99**. The naive-control arm
  (no grain guard) explains *why*: all three still got grain right **without** the prompt guard,
  because Kenya's `## Grain` line is now explicit in the dict (the Phase-0 protocol fix), and the
  **dict-caveat guard is model-independent**. This is exactly `proof_c`'s "grain is right when made
  explicit in *either* the prompt or the dict" — and the dict half generalizes to cheaper models.
- **Both candidates fail only the hardest case — Q6, the EAV mislabel** ("avg crude protein across
  fish-meal ingredients", where the `ingredient` column actually holds the *parameter*
  `crude_protein_percent`):
  - **Haiku** also missed **Q2 (CPUE)** — it filtered `gaul_2_name='Kwale'` (district level) instead
    of `gaul_1_name` (county); the gate refused (Kwale ∉ the gaul_2 domain). On Q6 it **over-refused**
    (`cannot_resolve`). Both **reasoning** failures. → **7/9.**
  - **Gemini** got Q2 CPUE right (derived, denominator surfaced, 1.64). On Q6 it routed on the
    non-distinctive token "Fish meal" (matches 2 tables) instead of the distinctive
    `crude_protein_percent`; the gate refused as not-distinctive — a **reasoning/route** miss, but one
    that fails **safe** (a refusal, not a wrong number). → **8/9.**

The EAV mislabel is the one case Opus uniquely nails. Grain — the failure `proof_c` most feared —
is **not** where the cheaper models break.

## 4. Mode A reasoner — MECHANICAL (baseline 0 fab/10; Haiku 1 fab/10; Gemini 0 fab/10)

Cold run — each call sees only one serialized subgraph — over the proof's 5 questions + 5 relational
pairs, judged by the same deterministic `citecheck` (C1 fabrication, C2 confidence, C3 inferred-flag,
C4 not-connected) the pipeline gates on. The negative control passed (a fabricated edge injected on
the disconnected FASA↔WIO case is caught), so the guard has teeth independent of any model.

- **Haiku fabricated** on **Q3** ("which initiatives share methods/data with Peskas") — it cited
  `ssf_research_..._paper --references--> peskas_hub`, **an edge absent from the subgraph** (C1 fail),
  plus a C3 inferred-flag mismatch on Q1. **1 fabrication / 10** — a **reasoning** failure, and a
  decisive one: this slot is autonomous with no human to catch it.
- **Gemini fabricated nothing (0/10).** Its single rejection was on **Q3** too, but it was a
  **structured-output truncation**, not a fabrication: `finish=MAX_TOKENS` cut the JSON mid-string on
  the largest cited-edge output. Re-running that one question at a higher token budget (the same
  remedy the proof applied to Opus's 8000-token bump) → **parses clean, cites 7 real edges,
  honest=True (C1–C3 pass)**, using 5,416 output tokens of which 4,643 were *thinking*. So Gemini
  **matched Opus's 0-fabrication record** on this set; the miss is a fixable budget artifact, attributed
  honestly as structured-output.

One softer signal: on Q7 (a 2-edge subgraph) Gemini said `connected=True` where Opus declined to call
it "connected" (the restraint rule 6 asks for). Mechanically clean (the edges exist); it is the kind
of prose-restraint the cite-check does not score.

## 5. Mode B synthesis — MECHANICAL + JUDGMENT (all pass)

The honesty work is upstream and **model-independent**: the refuse-when-thin gate declines the empty
retrieval (confirmed). The model-dependent test is what the synthesizer does with passages:

- **Covered case** (the real Peskas validation passage): **all three** cite `[1]` and stay faithful
  (mention validation/outlier). **PASS.**
- **Overclaim probe** (same passage, a question it does *not* answer — which ML algorithm + what
  precision): **all three** declined to invent — none named an algorithm or a precision figure, and
  each said the passage does not specify (Sonnet: "does not specify which particular machine-learning
  algorithm … nor any measured precision"; Haiku: "I cannot answer … it does not specify"; Gemini:
  "the specific … algorithm … and its measured precision are not mentioned"). **PASS** (mechanical: no
  invented specifics; judgment: no prose-overclaim).

Mode B is the safest candidate exactly as the strategy doc predicted: retrieval + the gate do the
honesty work before the model writes.

## 6. Ingestion agents — JUDGMENT ONLY (would the drafts pass curator review?)

Each candidate drafted a Template-A note (the real `zanzibar_validated_trips.csv`) and a Template-B
note (the real Peskas SoftwareX paper). Drafts are committed in
[`ingestion_drafts/`](ingestion_drafts/) for audit. The verdict is a read against the protocol rubric;
the structural proxies (section presence, canonical name, shape-word leak) only *aid* it — and two of
the "shape-word leaks" were false positives (`.csv` in legitimate `## Related files` paths; "long" in
"long-term").

- **Opus (reference):** publish-grade both. Correct canonical name ("Peskas"), grain-trap-aware grain
  line ("take one value per distinct `trip_id` rather than summing raw rows"), and Related files
  honestly **hedged** ("…if present in the repository").
- **Haiku:** strong structure, **excellent grain** (named the repeating trip-level columns and the
  dedup key correctly), canonical names throughout; its Template-B draft is nearly Opus-quality. **But
  on Template A it invented three specific sibling files** (`zanzibar_raw_trips.csv`,
  `zanzibar_fisher_demographics.csv`, `zanzibar_vessel_inventory.csv`) **asserted as real**, with
  relationships — the exact "never invent" violation the curator review gate exists to catch.
- **Gemini:** **honest** (invented nothing) and correct on grain/columns, but left **`## Related
  files` empty** (no graph wiring — the most valuable part) and wrote metadata-style Key concepts
  ("Authors:", "Affiliations:", "Keywords:") rather than relationship prose. Plus the low-budget
  truncation caveat (it needed the raised token budget to produce a full note at all).

Both candidates are **review-gated usable** with *opposite* failure modes: Haiku **over-asserts** links
(reviewer deletes/verifies — cheap), Gemini **under-wires** (reviewer adds links — more effort).
Neither is publish-ready unreviewed, which is precisely why the strategy doc places ingestion behind
the human review gate.

---

## 7. Cost — measured per-op, and a monthly estimate under an explicit assumption

**Measured `$/operation`** (real tokens × verified rates):

| Slot | Opus 4.8 | Sonnet 4.6 | Haiku 4.5 | Gemini 2.5 Flash |
|---|---|---|---|---|
| C resolver | $0.0627 | — | $0.0097 | $0.0040 |
| A reasoner | $0.0373 | — | $0.0052 | $0.0034 † |
| B synthesis | — | $0.0027 | $0.0006 | $0.0008 |
| Ingestion (note draft) | $0.0365 | — | $0.0047 | $0.0065 |

† Gemini Mode A measured at a 4 096-token cap (one op truncated); an adequate-budget run costs modestly
more (the clean Q3 re-run used ~5.4k output tokens). **Gemini's output is mostly thinking** (e.g. 4,598
thinking tokens across 9 Mode-C ops; 3,894 across 2 ingestion ops) — billed as output, so its low
output rate ($2.50/M) is doing the heavy lifting and a low `max_tokens` risks truncation.

**Per-op savings where a slot can move:** Mode B Sonnet→Haiku ≈ **−77%**; ingestion Opus→Haiku ≈
**−87%**.

**Monthly estimate — stated assumption (volume is the unknown driver, so a range):** 2 ingestions/day
(≈60 curator note-drafts/month; the enricher is a deterministic script, no LLM) + a query stream split
evenly across Modes A/B/C. Under the **recommended** assignment (§9), only Mode B and ingestion change
vs current pins:

| Queries/day | Monthly query+ingestion cost — current pins | — recommended (B→Haiku, ingest→Haiku) | Saving |
|---|---|---|---|
| 10 | ~$10.5 | ~$10.3 | ~$0.2 |
| 100 | ~$104.9 | ~$100.9 | ~$4.0 |
| 1000 | ~$1,029 | ~$1,008 | ~$21 |

The dominant cost is the **Mode A/C Opus** slots (≈$0.04–$0.06/query) — which **stay pinned** on
honesty grounds — so optimizing the already-cheap B/ingestion slots yields a **small relative saving
(~3–4%)** at any near-term volume. This is the honest, slightly sobering shape of the result, and it
**confirms strategy §5**: the door is worth keeping open, but building the split is not worth it until
query volume is large — and even then the savings are capped by the slots that cannot move.

---

## 8. Per-slot sweet-spot recommendation

| Slot | Tier | Cheapest model that PASSES its proof | Verdict |
|---|---|---|---|
| **A reasoner** | autonomous honesty-critical | — (neither earns it now) | **stay pinned (Opus).** Haiku **fabricated** (1/10) — a real reasoning fail with no human to catch it. Gemini **passed the 0-fabrication bar (0/10)** and is the genuinely *promising* candidate, but on n=10 + a structured-output truncation + autonomous use, it has **not earned** a non-negotiable slot: **inconclusive-promising — needs a larger cold-rate run before moving.** |
| **C resolver** | autonomous honesty-critical | — (both miss the EAV case) | **stay pinned (Opus).** The decisive grain trap is safe on all three; both candidates miss only the EAV mislabel (Q6) — Gemini at **8/9** (fail-safe refusal) is closest. **Inconclusive-leaning-stay:** could be earned if the EAV-mislabel case is added to the vetted band / prompt, but not on today's result. |
| **B synthesis** | grounded (gate upstream) | **Haiku 4.5** | **adopt-eligible.** Passes faithfulness + refuse-when-insufficient + no prose-overclaim; cheapest passing model (−77% vs Sonnet). Gemini also passes (alternative). |
| **Ingestion** | human-reviewed | **Haiku 4.5** | **adopt-eligible with review.** Strongest skeleton of the candidates (grain + canonical names ≈ Opus), failure mode (invented Related files) is exactly what curator review catches; −87% vs Opus. Gemini also usable but under-wires and needs generous token budget. |

---

## 9. Bottom line — the per-slot assignment that minimizes cost while every slot passes its honesty bar

| Slot | Assignment | Why |
|---|---|---|
| Graph build (`/graphify`) | **Opus 4.8** (unchanged) | out of scope here — governance/reproducibility, not evaluated. |
| **Mode A reasoner** | **Opus 4.8 (stay)** | Haiku fabricates; Gemini promising but not earned on n=10. |
| **Mode C resolver** | **Opus 4.8 (stay)** | both miss the EAV mislabel; grain trap safe on all. |
| **Mode B synthesis** | **Haiku 4.5 (move)** | passes its proof; −77%/op vs Sonnet. |
| **Ingestion agents** | **Haiku 4.5 (move), review-gated** | passes review-reliably-enough; −87%/op vs Opus. |

**This empirically confirms the strategy doc's tier theory.** The two **autonomous, honesty-critical**
slots (A, C) demonstrably *cannot* move — Haiku fabricates on A and over-refuses C's hardest case; the
two **grounded / human-reviewed** slots (B, ingestion) *can* move to Haiku. The asymmetry held: the
"important-looking" ingestion agents are the *safe* place to economize (a human signs off), the
"plumbing-looking" Mode A/C live slots are the *unsafe* place (they answer a user with no review).

**Net saving under the stated assumption: ~3–4% of monthly LLM spend** at 100 queries/day — small,
because the slots that dominate cost are the ones that must stay pinned. So the actionable
recommendation matches strategy §5: **keep the door open exactly here (B + ingestion → Haiku), but
don't build the split until query volume makes the absolute saving worth the migration effort.**

---

## 10. What this did and did NOT establish (honest caveats)

- **Mechanical verdicts (Mode A/C) are firm; Mode B prose-overclaim and ingestion quality are
  judgment** — read the drafts in `ingestion_drafts/` and the texts in `results/mode_b.json` rather
  than trusting a single label. They are reported distinctly and not flattened.
- **Sample sizes are small** — Mode C 9 Q, Mode A 10 Q, Mode B 2 probes, ingestion 2 docs. The Mode A
  "0/10" results (Opus and Gemini alike) are encouraging but are a *rate over 10*, exactly the
  small-sample caveat `proof_a` already flagged; do not over-read either the pass or the fail.
- **Cost rests on the assumed volume** (2 ingestions/day + an even A/B/C query split). Query volume is
  the real driver and is unknown; the monthly table is a range, not a single total.
- **Prompt-fit confound, handled:** each candidate ran on a fair adapted prompt against the identical
  bar, and no failure looked like prompt-dialect misunderstanding — the failures attributed to
  *reasoning* (Haiku's fabrication, both models' EAV miss, Haiku's CPUE admin-level slip) are real, and
  the one attributed to *structured-output* (Gemini's Mode-A truncation) was confirmed fixable.
- **The eval used each provider's native structured-output mechanism, not the modes' exact Live path.**
  Anthropic ran **prompt-for-JSON** because `RESOLUTION_SCHEMA` exceeds `output_config.format`'s
  complexity limit (a real, separately-actionable finding about the untested `LiveResolver`); Gemini
  ran `responseSchema`. The Opus baseline still reproduced 9/9 and 0/10, so the method did not
  disadvantage the Anthropic models — but a production move would re-validate on the real path.
- **Gemini's default thinking is an operational caveat**, not just a cost line: it inflates output
  tokens and, at a tight `max_tokens`, truncates structured output (the Mode-A Q3 and the first
  ingestion run). Any real Gemini adoption must budget tokens generously or disable thinking on
  generation slots.
- **A/C "stay pinned" is today's result, not a permanent verdict.** Gemini's 0-fabrication on Mode A
  and 8/9 on Mode C make it the candidate to re-test (larger run; the EAV case constrained) before the
  next cost review — the door the strategy doc kept open now has a name on it: **Gemini 2.5 Flash, not
  Haiku, for the autonomous slots.**

---

*Reproduce: `model_eval/.venv` is not needed — run with the repo `.venv` from the repo root:
`python -m model_eval.reach_probe` (STOP-gate reachability), then `run_mode_c`, `run_mode_a`,
`run_mode_b`, `run_ingestion`. Verdict + cost JSON in `results/`; verbatim model output in `raw/`
(git-ignored); drafted notes in `ingestion_drafts/`. Adapted prompts in `prompts.py`. No WDB data,
mode, pin, `MODEL.md`, router, API, or `graphify-out/` was modified.*
