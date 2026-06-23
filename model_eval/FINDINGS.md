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

> **Extended 2026-06-23 — §11 (OpenRouter-gateway arm).** §§1–10 below are the original run: Haiku
> direct + Gemini 2.5 Flash via its **native** AI-Studio key. The plan was then revised to route **all**
> non-Anthropic candidates through **one gateway (OpenRouter)** and add an **ultra-cheap open model**.
> [§11](#11-openrouter-gateway-arm--gemini-routed-through-openrouter--the-open-model-deepseek) runs the
> same four proofs against **Gemini 2.5 Flash via OpenRouter** and **DeepSeek v4-flash** (the open
> standout), on fair prompts, json-mode structured output, with the ~5.5% OpenRouter fee folded into
> cost. It **reuses** the §§1–10 Opus/Sonnet/Haiku rows as reference (it re-ran only the two new
> candidates) and writes to `results/*_openrouter.json` so nothing here is overwritten. **OpenRouter is
> used as an evaluation gateway only — not a recommendation to route production through a gateway** (that
> would conflict with the version-pinning reproducibility the build discipline depends on; see §11.5).

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

## 11. OpenRouter-gateway arm — Gemini routed through OpenRouter + the open model DeepSeek

**Date:** 2026-06-23. The plan above (§§1–10) tested Gemini through its **native** AI-Studio key. The
revised plan routes **every non-Anthropic candidate through one gateway — OpenRouter** (the official
OpenAI-compatible way: base `https://openrouter.ai/api/v1`, `/chat/completions`, `Authorization:
Bearer`) — and adds an **ultra-cheap OPEN model**. This arm runs the **same four proofs, same identical
bar**, against two candidates, **reusing** the §§1–10 Opus/Sonnet/Haiku rows as reference:

| Candidate | Slug (confirmed live via the OpenRouter models API, 2026-06-23) | List price ($/1M in,out) |
|---|---|---|
| **Gemini 2.5 Flash (via OpenRouter)** | `google/gemini-2.5-flash` | $0.30 / $2.50 |
| **DeepSeek v4-flash** (the open standout) | `deepseek/deepseek-v4-flash` | **$0.09 / $0.18** |

MiniMax was the optional "one more"; it failed a clean reachability probe (non-standard response shape)
and — DeepSeek being the named standout that passed — was dropped to keep the set to one open model.

### 11.1 Method delta — one gateway, one structured-output channel, the fee folded into cost

- **Fair prompt = the same model-neutral non-Claude prompts** the §§1–10 Gemini arm used
  (`prompts.mode_c_gemini`, `MODE_A_GEMINI`, `MODE_B_GEMINI`, `INGESTION_BRIEF`) — they encode the
  identical bar in numbered-imperative / "return JSON only" style, so both OpenRouter candidates run on
  the same fair expression. The runners route any non-Claude `provider` (native `gemini` **or**
  `openrouter`) to these.
- **Structured output = OpenRouter `response_format: {"type":"json_object"}` + the in-prompt key
  contract**, tolerantly parsed — the same prompt-for-JSON shape the Anthropic path uses. This is the
  task's recommended structured-output mitigation, and it is **uniform** for both OR candidates. Note
  this is **deliberately a different channel** from the §§1–10 native-Gemini row, which used Gemini's
  `responseSchema`; the comparison below isolates that channel effect.
- **Cost honesty:** OpenRouter passes provider pricing through at cost but adds a **~5.5%
  credit-purchase fee**, so every OR `$/op` here uses the list price **×1.055** ([`costs.py`](costs.py)).
  OpenRouter's response also returns the real upstream `usage.cost`, which corroborated the token×rate
  figures. Anthropic (Haiku/Opus) is billed direct, **no fee**.
- **DeepSeek reasons by default** (it is a thinking model): on a trivial prompt it spends ~60 reasoning
  tokens, and those are billed inside `completion_tokens`. The fair choice is to test it **as it ships
  (reasoning on)** — that is its best configuration for the honesty/grain tasks — and let measured cost
  carry the reasoning tokens. Budgets were set generously (8k json / 4k text) so thinking never
  truncates; only emitted tokens are billed, so headroom is free. (Reasoning-off is ~6× cheaper but was
  not used — disabling a capability on reasoning-critical slots would be the unfair move.)
- The STOP-gate reachability probe ([`reach_probe.py`](reach_probe.py)) was extended to the gateway and
  passed for both slugs (plain **and** json-mode) before any paid run.

### 11.2 Per-slot × per-model verdict + measured cost (OpenRouter fee included)

| Slot | Type | Gemini 2.5 Flash **via OpenRouter** | DeepSeek v4-flash | Reference (§§1–10) |
|---|---|---|---|---|
| **C resolver** (9 Q) | mechanical | **7/9** · $0.00280/op | **7/9** · $0.00077/op | Opus 9/9 · Haiku 7/9 · Gemini-native 8/9 |
| **C — grain trap** (decisive) | mechanical | ✅ **31.88** | ✅ **31.88** | ✅ all |
| **A reasoner** (cold, 10 Q) | mechanical | **0 fab** / 2 struct · $0.00192/op | **0 fab / 0 struct** · $0.00028/op | Opus 0 fab · Haiku 1 fab · Gemini-native 0 fab/1 trunc |
| **A — negative control** | mechanical | guard has teeth (model-independent): injected fabrication caught ✅ |||
| **B synthesis** (2 probes) | mech + judg | covered ✅ / overclaim ✅ · $0.00016/op | ✅ / ✅ · $0.00003/op | Sonnet ✅✅ · Haiku ✅✅ |
| **Ingestion** (2 notes) | judgment | honest grain, *under-wires* (+1 invented sibling) · $0.00145/op | strong B note, *over-asserts* (2 invented siblings + invented domains) · $0.00031/op | Opus publish-grade · Haiku over-asserts · Gemini-native under-wires |

### 11.3 Slot-by-slot — what passed, what failed, why

**Mode C (mechanical) — both 7/9; the decisive grain trap is safe on both.** Both deduped Q4 to
`trip_id` and computed **31.88** (never the raw-row 28.99), passed the Gill-Net disambiguation, both
honest refusals (Kisumu, wind), and Inhambane/Zanzibar. Both miss the **same two**:
- **Q6 (EAV mislabel)** — both route on the non-distinctive token "Fish meal" (2 tables) instead of the
  distinctive `crude_protein_percent`; the gate refuses. **Reasoning** miss, but **fail-safe** (a
  refusal, not a wrong number) — identical to native Gemini, the one case Opus uniquely nails.
- **Q2 (CPUE)** — **not a reasoning miss.** Both **derived CPUE correctly** (`tot_catch_kg /
  trip_duration_hrs`, inputs + assumptions + alternatives stated — DeepSeek even named `n_fishers`/
  `n_catch` as alternative effort denominators), but both left `metric_label` **null** instead of
  `"cpue"`, so the gate (which admits only registered derived labels) refused. Native Gemini got Q2 via
  its **`responseSchema`**; the OR `json_object` channel did **not** elicit the label field. So the 1-point
  drop vs native Gemini (8/9 → 7/9) is a **structured-output / convention** effect of the gateway's JSON
  channel, **not** a reasoning regression — and it is the kind of thing a schema-enforced channel or a
  one-line convention nudge fixes.

**Mode A (mechanical) — the standout result.** Negative control caught the injected fabrication
(model-independent). Then:
- **DeepSeek v4-flash: 0 fabrications / 10, 0 structured-output failures — a clean sheet**, matching
  Opus's record, with reasoning on (~240 reasoning tok/op) and **valid JSON every time**, at
  **$0.00028/op (~130× cheaper than Opus's $0.0373)**. On this set it is the **best cheap candidate Mode
  A has seen** — better than Haiku (which fabricated 1/10) and cleaner than native Gemini (which
  truncated one).
- **Gemini via OpenRouter: 0 fabrications / 10**, but **2 structured-output failures** (Q3, Q5 — the two
  largest subgraphs): the JSON came back unterminated/empty and failed to parse. Zero fabrication is the
  honesty bar it cared about; the misses are **structured-output**, the same fragility the native row
  showed on its largest output — fixable with budget/schema, attributed as such.
- **n = 10 is small** — the same caveat §10 raised for the §§1–10 "0/10" results applies verbatim to
  DeepSeek's clean sheet. It is *encouraging*, not *earned*.

**Mode B (mechanical + judgment) — both pass, cleanly.** The refuse-when-thin gate declines the empty
retrieval (model-independent). On the covered passage both cite `[1]` and stay faithful; on the
overclaim probe both decline to invent an algorithm or precision and explicitly hedge ("do not specify
…"). No prose-overclaim. DeepSeek at **$0.00003/op** is effectively free here.

**Ingestion (judgment) — both review-gated usable, opposite failure modes (the §6 pattern, repeated).**
- **DeepSeek**: its **Template B (Peskas SoftwareX) draft is near publish-grade** — canonical "Peskas"
  H1, rich relationship prose, and authors/DOIs/repos that are **faithfully extracted from the supplied
  page (verified present in the sample), not fabricated**, ending on an honest hedge about unreferenced
  files. But its **Template A over-asserts**: it invented **two** sibling files (`zanzibar_trips.csv`,
  `zanzibar_validated_trips_metadata.csv` — neither exists in `peskas/`) and invented column domains the
  CSV head cannot support (catch priced "in Tanzanian Shillings"; `catch_outcome` "1 = kept, 2 =
  discarded"). The grain line is correct and trip-aware. This is the **Haiku-style over-assertion** the
  curator review gate is built to catch.
- **Gemini via OpenRouter**: **honest on substance** (excellent grain, accurate columns) but **invented
  one** sibling (`zanzibar_raw_trips.csv`) and its Template-B note is **under-wired** — it emitted a
  **duplicated, empty `## Related files` header** (a structural glitch) and named the platform loosely
  ("Peskas monitoring system" / "Peskas system" rather than the canonical "Peskas"). The §6
  **under-wires** pattern, plus a header bug.

Net: DeepSeek leans **over-assert** (reviewer deletes invented links/domains — cheap), Gemini-OR leans
**under-wire** (reviewer adds links — more effort) — neither publish-ready unreviewed, exactly why
ingestion sits behind the human gate.

### 11.4 Cost — measured per-op (fee included), and where the gateway changed the number

| Slot | Opus/Sonnet (ref) | Haiku (ref) | Gemini-native (ref) | **Gemini-OR** | **DeepSeek-OR** |
|---|---|---|---|---|---|
| C resolver | $0.0627 | $0.0097 | $0.0040 | **$0.00280** | **$0.00077** |
| A reasoner | $0.0373 | $0.0052 | $0.0034 | **$0.00192** | **$0.00028** |
| B synthesis | $0.0027 | $0.0006 | $0.0008 | **$0.00016** | **$0.00003** |
| Ingestion | $0.0365 | $0.0047 | $0.0065 | **$0.00145** | **$0.00031** |

Two honest cost notes:
- **Gemini-via-OpenRouter measured *cheaper* than native Gemini on three of four slots** *despite* the
  5.5% fee — because the OR-served model emitted far fewer billed output tokens (e.g. Mode C avg out
  **100 tok** vs the native row's heavy default-thinking output). OpenRouter did not report Gemini
  reasoning tokens separately (`thinking_tot = 0` across slots), so this is a measured-billing fact, not
  a claim about how much it "really" thought. The same thinner output coincides with its CPUE-label miss
  and the two Mode-A truncations — **less (visible) thinking → cheaper but slightly more
  structured-output fragility.** Cost and reliability moved together; do not read the lower price as a
  free lunch.
- **DeepSeek v4-flash is the cheapest on every slot** even with reasoning-on billed (its reasoning
  tokens *are* in these figures). At the §7 volume assumption (2 ingestions/day + an even A/B/C query
  split), swapping the two **movable** slots (B + ingestion) to DeepSeek instead of Haiku changes the
  monthly total by **cents** — because, exactly as §7 found, the spend is dominated by the **Mode A/C**
  slots that **stay pinned on honesty grounds**, so a cheaper movable slot barely moves the total. The
  open model's headline 35–130× cheapness is real but lands on the slots that already cost ~nothing.

### 11.5 What §11 established, what it did not, and the gateway caveat

- **Firm (mechanical):** the **grain trap is safe** on both OR candidates (31.88); **DeepSeek fabricated
  nothing on Mode A (0/10) with zero structured-output failures**; both refuse-when-thin and avoid
  prose-overclaim on Mode B. The negative control still has teeth.
- **A real structured-output finding, isolated:** the **same model (Gemini 2.5 Flash) scored 8/9 native
  (`responseSchema`) but 7/9 via OpenRouter (`json_object`)** — the gateway's JSON channel did not elicit
  the registered-derived-label field, and truncated the two largest Mode-A outputs. When a cheap model
  "fails," distinguish the **channel** from the **model**: here the model reasoned correctly and the
  *channel* lost the point. For DeepSeek, `json_object` was **reliable** (0 parse failures across C+A).
- **Judgment, not firm:** the ingestion verdicts and Mode-B prose are a human read of the committed
  drafts (`ingestion_drafts/*__{gemini-2.5-flash-or,deepseek-v4-flash-or}.md`), not a mechanical pass.
  Sample sizes are small (C 9 Q, A 10 Q, B 2 probes, ingestion 2 docs).
- **Gateway caveat (explicit):** OpenRouter was the **evaluation** transport only. It is **not** a
  recommendation to run production through a gateway — a gateway can silently change the serving build,
  the structured-output channel, and the thinking configuration of "the same" model (this run is the
  proof: native vs OR Gemini differed on both score and cost). That directly conflicts with WDB's
  **version-pinning reproducibility** discipline (`CLAUDE.md` pins the exact build, stamps
  `BUILD_INFO.md`). If any of these candidates were ever adopted, it would be pinned to a **specific,
  reproducible provider build on its own key**, re-validated on the **real** Live path — not left behind
  a gateway that can move under it.

### 11.6 Bottom line — does the open-model arm change the §9 assignment? No (but it names the open candidate).

- **Mode A / C stay pinned (Opus).** §11 does **not** overturn §9: both OR candidates still miss C's EAV
  case (7/9), and although **DeepSeek's 0-fab/0-struct Mode-A clean sheet is the strongest cheap result
  to date**, it rests on n=10 + an autonomous, no-human-review slot — **inconclusive-promising, not
  earned.** DeepSeek (open) now joins Gemini as a candidate worth a **larger cold-rate run** before any
  autonomous-slot move; the door §9 kept open now has **two** names on it, and the cheaper one is open.
- **Mode B / ingestion remain the movable slots.** Both OR candidates pass Mode B; both draft
  review-gated ingestion notes. **DeepSeek is cheaper than Haiku on both** — but the §11.4/§7 arithmetic
  says the **absolute** saving over the already-recommended Haiku move is **negligible at near-term
  volume**, so there is **no reason to prefer the open model over Haiku** for these slots today: Haiku
  keeps everything on **one pinned Anthropic provider** (simpler, no gateway, no extra key, reproducible)
  for a few cents' difference. The open model earns its place only if (a) a future larger run lets it
  take an A/C slot, or (b) movable-slot volume grows enough that its 4–6× edge over Haiku becomes real
  money.

**§11 conclusion:** routing through OpenRouter and adding an open model **confirmed §9 rather than
changing it** — the honesty-critical slots still cannot move, the movable slots still can, and the open
model's dramatic per-token cheapness lands mostly on slots that already cost almost nothing. The single
genuinely new, actionable signal is **DeepSeek v4-flash's clean Mode-A sheet**, which makes it (not
Haiku) the cheapest candidate to put through a **larger autonomous-slot trial** before the next cost
review — with the gateway caveat (§11.5) front and centre if it is ever adopted.

---

*Reproduce: `model_eval/.venv` is not needed — run with the repo `.venv` from the repo root:
`python -m model_eval.reach_probe` (STOP-gate reachability — now also probes the OpenRouter slugs),
then the §§1–10 baseline arm `run_mode_c` / `run_mode_a` / `run_mode_b` / `run_ingestion`, and the §11
gateway arm `python -m model_eval.run_openrouter` (Gemini-OR + DeepSeek across all four slots →
`results/*_openrouter.json`). Verdict + cost JSON in `results/`; verbatim model output in `raw/`
(git-ignored); drafted notes in `ingestion_drafts/`. Adapted prompts in `prompts.py`; the OpenRouter
seam in `backends.py` (`OpenRouterBackend`) + `costs.py` (the ×1.055 fee). No WDB data, mode, pin,
`MODEL.md`, router, API, or `graphify-out/` was modified — and no production path was routed through a
gateway; OpenRouter was the evaluation transport only.*
