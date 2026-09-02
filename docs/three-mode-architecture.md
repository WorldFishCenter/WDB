# WDB — three-mode retrieval architecture (graph · passages · structured query)

> **On the references below.** This document cites two kinds of companion record that are **not**
> published with the repository: `rag-integration-feasibility.md` (an assessment of a separate
> internal codebase) and the `proof/`, `proof_a/`, `proof_c/` folders (throwaway proof-of-concept
> experiments, kept local by design — see `.gitignore`). They are named in plain text rather than
> linked, so nothing here points at a page you cannot open. Every conclusion they support is
> restated in this document.

**Date:** 2026-06-14 · **Status:** design + targeted proof of Mode C · **Builds on:**
rag-integration-feasibility.md (the two-mode assessment) and
`proof/FINDINGS.md` (the proven passage↔graph join + the "raw CSVs do not
belong in the passage index" verdict). This document does **not** re-litigate those; it adds the
third mode they did not cover and specifies how all three compose.

**What this is / is not.** This is an architecture design plus a read-only proof of the one mode no
prior work tested — the **structured query over the tidy CSVs** (Mode C; proof in
`proof_c/FINDINGS.md`). It does **not** build the serving layer, the UI,
the router, or the passage backend. The answer contract (§6) is specified only as far as the proof
needs it.

---

## 1. Aim & the three question types

WDB is WorldFish's shared, queryable **knowledge brain**, whose value is the **cross-initiative
connections** it surfaces, kept "connected, honest, and de-duplicated" ([../CLAUDE.md](../CLAUDE.md);
rag-integration-feasibility.md §1). The product goal here is to let
a user **consult and explore that knowledge, grounded strictly in the sources** — answering *"info
not available"* rather than inventing or speculating. That honesty constraint (§7) is the spine of
the design, not a feature bolted on.

Real target questions fall into three kinds, each with a *native* answering mechanism. Forcing one
mechanism to serve all three is exactly how a system starts inventing — so the architecture routes
each kind to the mode whose grounding is honest for it:

| # | Question kind | Example questions (the requester's) | Mode | Why this mode |
|---|---|---|---|---|
| 1 | **Relationship / enumeration** | "What projects operate in Kenya?" · "List gear types in Zanzibar" | **A — Graph** | The answer *is* the typed edges/nodes WDB already commits; enumerable and exact. |
| 2 | **Synthesis from sources** | "Impact of project X on Mozambique aquaculture?" · "Research gaps for cage culture in Zambia?" | **B — Passages** | Needs verbatim, cited prose from documents; retrieved + synthesized, never paraphrased from memory. |
| 3 | **Quantitative / computed** | "Average CPUE in Kwale district?" · plots · grouped comparisons | **C — Structured query** | The answer is a *number computed from rows*, not text; must be queried from the tidy CSVs, never retrieved as prose. |

A single user question may span kinds ("impact of X on Mozambique aquaculture, with catch trends" =
2 + 3 + 1); §5 (router) and §6 (answer contract) specify how blended questions compose. The earlier
work scoped only kinds 1–2 (graph + passages); **kind 3 is the gap this document closes.**

---

## 2. Mode A — Graph (relationships / enumeration)

**What it answers.** "What connects to what" and "list the X of Y": which initiatives touch Kenya,
which gear types appear in a dataset's domain, how Peskas relates to the WIO harmonization standard.
This is WDB's existing strength and needs **no new capability** —
`knowledge_base/graphify-out/graph.json` already holds it (**173 nodes · 320 edges · 7
communities, one connected component**; `knowledge_base/graphify-out/BUILD_INFO.md`),
consumed today by Claude through the `/graphify` skill.

**What it relies on (all enforced by [PROTOCOL.md](../PROTOCOL.md)):**

- **Hubs as canonical entity nodes.** Each initiative has one living `<initiative>_about.md` hub
  ([PROTOCOL §6](../PROTOCOL.md#6-context-notes)) and a fixed hub id (`peskas_hub`, `fasa_hub`, …);
  shared real-world entities get one stable id each (`shared_kenya`, `shared_fao_gaul`, …). This
  **one-node-per-entity** discipline is what makes enumeration exact and is the cross-initiative
  bridge — `Peskas` (betweenness 0.373) and `WorldFish` bridge all communities
  (`knowledge_base/graphify-out/BUILD_INFO.md`; canonical-entity guard, [../CLAUDE.md](../CLAUDE.md)).
- **`## Related files` as the wiring.** Edges exist only where a note *states* a relationship naming
  both sides; the graph does not infer links from filenames or folders
  ([PROTOCOL §6 habit 2, §8](../PROTOCOL.md#6-context-notes)).
- **`EXTRACTED` vs `INFERRED` tags.** Every edge carries a `confidence` tag — in the current graph
  **284 `EXTRACTED` vs 36 `INFERRED`** (`knowledge_base/graphify-out/graph.json`, `links[].confidence`).
  EXTRACTED edges are stated-on-both-sides facts; INFERRED are the model's plausible guesses.

**Native honesty mechanism (see §7).** Mode A answers from committed, stated edges; it **prefers
EXTRACTED and flags INFERRED**, and when no edge exists it returns *nothing* rather than a guess.
Enumeration is closed-world over the graph: "the projects in Kenya *that WDB records*."

---

## 3. Mode B — Passages (synthesis)

**What it answers.** Open questions needing grounded, quoted prose: "impact of project X on
Mozambique aquaculture", "research gaps for cage culture in Zambia". The answer is synthesized
**from retrieved verbatim passages with citations**, never from the model's own knowledge.

**Reuse the proven join — unchanged.** `proof/FINDINGS.md` already proved
(on real WDB data, both directions) that a retrieved passage joins to its graph associations at
**document grain** on the `source_file` key both systems store. Mode B adopts that result wholesale:
Chroma index for passages, `graph.json` for associations, joined on `source_file`. No Graphify
changes.

**Mandatory glue — companion-note normalization (carry-over #2).** **92 of 173** graph node
`source_file`s are `.md` companion notes, not the source document
(rag-integration-feasibility.md §2; `proof/FINDINGS.md`).
The join **must** collapse `X_context.md` / `X_dict.md` → `X` in **both** directions, or the reverse
direction (node → passages) returns nothing for any note-anchored node and the forward direction
misses nodes authored against the note. It is a deterministic filename rule
(`proof/join.py:doc_stem`) — cheap, but **not optional**. This is a hard requirement, not an
implementation detail.

**The passage index indexes source docs AND `.md` companion notes (carry-over #1).** Companion notes
are where curated knowledge lives — "the highest-leverage thing you can add"
([PROTOCOL §6](../PROTOCOL.md#6-context-notes)). But civ-kb's extractor has **no `.md` branch today**
— it dispatches on `pdf/docx/xlsx/pptx/txt` only
(rag-integration-feasibility.md §3;
`proof/FINDINGS.md` "surprises" #1). So a fair amount of WDB's authored
knowledge is **not passage-retrievable** today. **Required improvement:** add a `.md` branch
(≈ the existing `.txt` path, trivial). This is a **conscious, justified double-representation** —
note content is *also* in the graph, but prose notes are worth quoting verbatim, so indexing them
for retrieval earns its keep. This is **unlike** the rejected `.csv` branch
(`proof/FINDINGS.md` Q2): raw tables are not prose worth quoting and
retrieve *misleadingly* (Mode C answers them instead — §4).

**Confidence / coverage gate (refuse-when-thin).** Mode B must **return "not available" when
retrieval is weak** — when the top reranked passages fall below a similarity/coverage floor, or no
indexed document covers the asked initiative/region. The small corpus (~34 files) makes thin
retrieval common today; the gate is what prevents synthesis-from-nothing. (See §7 for why this is the
mode's honesty mechanism, and why the query-model lock — carry-over #3 — must be in place first, or
the gate fires on *artificially* degraded scores.)

**Does WDB's structural contract enable finer-than-document linking here? — No; document grain stays
the right call.** Carry-over #5 (PROTOCOL forces tidy tables, one `## Columns` bullet per column, a
canonical hub `# H1`) is a real, deterministic structural contract — but it constrains the **graph
side** (node labels, column domains), not the **passage side**. A retrieved PDF/DOCX passage still
carries only civ-kb's mechanical `location` ("page 2 [part 4/4]"), and WDB `source_location` is
LLM-authored prose ("Validation; Methods 2.3"); the two share **no fine-grained key**
(rag-integration-feasibility.md §4;
`proof/FINDINGS.md` Q1 "honest limitation"). So span↔node precision remains
**Option B** (deferred), not something the structural contract unlocks for free. Where the contract
*does* pay off is **Mode C routing** (§4) — a different use of the same `## Columns` domains.

---

## 4. Mode C — Structured query (quantitative / computed)

> *Drafted here as design; §4.4 below records what the read-only proof
> (`proof_c/FINDINGS.md`) actually showed and is the part to trust.*

**What it answers.** Numbers computed from rows: averages, counts, grouped comparisons, the data
behind a plot — "average CPUE in Kwale district", "average catch per trip by county", "crude protein
of fish meal". These are **not** answered by retrieving text; they are answered by **querying the
tidy CSVs directly**.

### 4.1 Why query, not embed — the complement to the passage verdict

`proof/FINDINGS.md` Q2 proved raw CSV rows **must not** go in the passage
index: they 100×-inflate it and retrieve *misleadingly* (asked for "crude protein of fish meal", the
passage index returned amino-acid coefficients — a confident wrong answer). Mode C is the **other
half of that verdict**: CSVs are first-class data to be **queried**, not prose to be embedded. The
same question that fooled retrieval is exact under a query (§4.4).

### 4.2 Engine — DuckDB over the CSVs (no server, no copy)

DuckDB queries a CSV file in place with SQL (`SELECT … FROM 'peskas/kenya_validated_trips.csv'`) —
no database server, no ETL, a single pip wheel. *(It is **not** in the current environment despite
the feasibility note's "already in stack"; a real integration must add it — see §9 and §4.4.)*
The stack already serves the static graph as files; Mode C adds a static, read-only query layer over
the same committed CSVs.

### 4.3 How a question finds the right table & columns — the `_dict.md` value domains as the key

This is the crux of Mode C and carry-over #5. `/enrich` writes, into every `_dict.md`, one
`## Columns` bullet per column with a **value domain** — a distinct set, count + examples, or a
numeric/date range ([PROTOCOL §5–6, Template A](../PROTOCOL.md#5-tidy-data)). That domain is the
**candidate routing key**: a question naming a value ("**Kwale**", a gear type) can be matched
against the enumerated domains to find the table and column that holds it. This is **not** fuzzy span
matching — it is a structural contract `/enrich` guarantees. §4.4 reports how well it actually works.

### 4.4 What the read-only proof showed

The proof (`proof_c/FINDINGS.md`, `proof_c/query.py`, DuckDB over two real
CSVs) confirms Mode C and **sharpens where its cost actually is**:

- **Precise, computed answers.** "Average CPUE in Kwale" → 50,422 trips, **31.88 kg/trip** (also
  1.64 kg/trip-hr, 0.2725 kg/fisher-hr); "avg catch per trip by county" → a clean five-row ranking
  (Lamu 71.98 → Kilifi 22.93). Every figure is computed from rows, not retrieved.
- **The complement to the passage failure, demonstrated.** Asked "crude protein of fish meal", the
  passage index returned the *wrong* amino-acid coefficients (`proof/FINDINGS.md`
  Q2); Mode C returns the exact value — **74.2** for the South-Asia 74% CP fish meal — and all 56
  fish-meal variants. The data that must stay *out* of the passage index is answered correctly by
  **querying** it.
- **Clean refusals, two native mechanisms.** An absent *value* ("CPUE in Kisumu") returns **0 rows →
  not available**; an absent *column* ("water temperature") **fails to bind → not available**. No
  number is ever fabricated (§7).
- **Routing — the real cost, judged honestly.** The `_dict.md` value domains *are* a usable key:
  **distinctive values route cleanly** (`Kwale` → exactly one table). But the proof shows the mapping
  is **more than value-matching**: generic terms are ambiguous (`Gill Net` → all three sister tables;
  the question's region must disambiguate), the user's words rarely equal the column token ("crude
  protein" ≠ `crude_protein_percent`; **`CPUE` matches no column at all**), derived metrics need a
  formula not a lookup (CPUE = catch ÷ effort, two possible denominators), grain must be resolved
  (the table is 2.45 rows/trip — naive row-averaging is wrong), and EAV tables hide the key inside a
  value and mislabel columns (FICD's `ingredient` column actually holds the *parameter*). **The
  engine is trivial; the NL→table/column resolver over the `_dict.md` domains is the real work** — and
  it is tractable precisely because PROTOCOL's structure gives it a real key (§9, §10).
- **Engine reality:** DuckDB was **not** in the stack and had to be installed (§9).

---

## 5. The router

A question is dispatched to **one or more modes**, then the answer contract (§6) merges the results.
Routing has two layers: **intent** (which mode) and, for Mode C, **table/column resolution** (which
file).

**Layer 1 — intent classification.** Cheap signal-based routing, refined by an LLM classifier:

| Signal in the question | → Mode |
|---|---|
| "what/which/list/connect/related", an entity + a relation | **A** (graph enumeration/relationship) |
| "impact/effect/gaps/why/how does … affect", open synthesis | **B** (passage synthesis) |
| "average/mean/total/how many/compare/trend/per", a quantitative noun (CPUE, catch, count) | **C** (structured query) |

The classifier may return **multiple** modes with a confidence each; ambiguous questions fan out to
more than one mode rather than guessing a single one.

**Layer 2 — table/column resolution (Mode C only).** When the router picks C, it must resolve the
question to a specific CSV + columns using the `_dict.md` value domains as the candidate key (§4.3).
The proof (§4.4, `proof_c/FINDINGS.md`) measures how tractable this is —
including where it is *not* (generic terms that match several sister tables). This resolution cost is
the real price of Mode C, so the router treats a failed/ambiguous resolution as a first-class
"can't answer precisely → ask to disambiguate or return not-available" path, never a silent guess.

**Blended questions compose, they don't collapse.** "Impact of project X on Mozambique aquaculture,
with catch trends" routes to **B** (synthesis of impact prose) **+ C** (the catch-trend figures from
the trip CSV) **+ A** (X's associations). Each mode returns grounded fragments with their own
provenance; the answer contract (§6) assembles them into one answer where every clause is traceable
to the mode and source that produced it. A mode that returns nothing simply contributes nothing —
the answer says so for that part rather than letting another mode fill the gap by invention.

---

## 6. The answer contract

The contract is the shape of a **grounded answer** — specified here only as far as the proof needs
(no API, no UI). A unified answer is a list of **claims**, each one traceable to the mode and source
that produced it, plus a typed **associations** payload and, where relevant, **figures**:

```
Answer:
  claims:        [ Claim, … ]        # synthesized text, one entry per grounded statement
  associations:  [ Edge,  … ]        # typed graph edges (Mode A) for the answer's entities
  figures:       [ Figure, … ]       # only when Mode C produced computable results
  unanswered:    [ str, … ]          # parts of the question no mode could ground -> stated, not hidden

Claim:
  text:     "…"                       # one statement of the answer
  mode:     A | B | C                 # which mode grounded it
  citations:[ Citation, … ]           # >=1; a claim with zero citations is NOT emitted

Citation:                             # click-through target — differs per mode
  source_file:    "peskas/kenya_validated_trips.csv"   # always: the WDB-relative path (carry-over #4)
  note:           "kenya_validated_trips_dict.md#Columns"  # the companion-note section
  locator:        # one of:
    A: graph edge id / source_location label ("Validation; Methods 2.3")
    B: passage span + civ-kb location ("page 2 [part 4/4]") + verbatim quote
    C: the SQL query string + its result row(s)            # the citation IS the computation

Figure:                               # Mode C only — grounded, never scraped
  spec:   {kind: bar|line|…, x, y}    # how to render
  query:  "SELECT …"                  # the exact SQL behind it
  result: [ row, … ]                  # the rows plotted
```

The defining rules: **(1)** every `Claim` carries ≥1 `Citation` or it is not emitted — there is no
un-sourced prose. **(2)** Citations **click through to the file and the companion-note section**, so
a reader lands on the grounded text (§3) or the `_dict.md` column meaning (§4). **(3)** A Mode-C
claim's citation **is the query plus its result** — uniquely reproducible (the proof showed every
number ships with its SQL; `proof_c/FINDINGS.md`). **(4)** Anything no mode
could ground goes in `unanswered` and is **stated**, never silently dropped or back-filled by another
mode.

---

## 7. The "never invent" design

Honesty is enforced **per mode** by that mode's native mechanism — there is no single guard, because
each mode fails differently:

| Mode | Native honesty mechanism | Failure → behaviour |
|---|---|---|
| **A — Graph** | **Prefer `EXTRACTED`, flag `INFERRED`.** Enumeration is closed-world over committed edges (284 EXTRACTED / 36 INFERRED today, `knowledge_base/graphify-out/graph.json`). | No edge exists → return nothing; an answer leaning on an INFERRED edge is **labelled** so the reader can discount it. |
| **B — Passages** | **Refuse-when-thin** (coverage/similarity floor) **+ query-model lock.** | Top reranked passages below the floor, or no document covers the asked initiative/region → **"not available."** |
| **C — Structured query** | **Query-returns-or-it-doesn't** (empty result *or* unbound column) **+ router "no table resolves."** | Absent value → 0 rows; absent column → bind error; unresolvable question → router refusal — **never a fabricated number** (proof Q-D). |

**The Mode-B query-model lock is a precondition, not a nicety (carry-over #3).** The passage proof
hit this live: Chroma silently embeds queries with its *default* model (`all-MiniLM-L6-v2`), not the
multilingual model the index was built with, **silently degrading retrieval**
(`proof/FINDINGS.md` surprise #2). A real integration **must** embed queries
with the **same** model as the index (`query_embeddings=`, not `query_texts=`). This matters for
honesty specifically: if scores are artificially depressed by a model mismatch, the refuse-when-thin
gate fires on noise — the system would refuse good answers and, worse, its confidence signal would be
meaningless. Lock the model first, *then* trust the gate.

**Supersession keeps answers current, not stale ([PROTOCOL §7](../PROTOCOL.md#7-recording-updates-and-supersession-over-time)).**
A companion note is a frozen snapshot; the living `<initiative>_about.md` is the present-tense node;
a stale snapshot links to it with `superseded_by`/`supersedes` (an `EXTRACTED` edge, both sides
named). So when an answer draws on a snapshot that has been superseded, the graph **tells it so**: the
answer should prefer the current `_about.md` and can mark the older claim "(as of <snapshot date>;
superseded by current state)". Honesty over time = answering with *what is true now* while never
losing the record of what was true then. This is a real WDB mechanism, not an aspiration — it is in
the protocol and the graph edges.

---

## 8. Plots & reports

Both are **compositions over Mode-C query results + cited prose** — grounded outputs, never scraped
from passages.

- **Plots** are a rendering of a Mode-C `Figure` (§6): the chart's data *is* a query result, and the
  figure ships **with the SQL that produced it** so it is reproducible and auditable. The proof's
  Q-B (avg catch per county) is already a bar chart's data; a `landing_date × tot_catch_kg`
  aggregation is a trend line (`proof_c/FINDINGS.md` step 5). A figure is
  **never** inferred from prose or lifted from a document image.
- **Reports** are multi-claim answers (§6) assembled across modes: each sentence carries its
  citation (Mode A/B) and each figure carries its query (Mode C). A report therefore has the same
  honesty guarantees as a single answer — every claim sourced, every number queried, anything
  ungrounded listed as `unanswered`. No "summary paragraph" floats free of citations.

---

## 9. Governance — keeping the new layers consistent with WDB's discipline

WDB's discipline is **single-builder, pinned-model, committed-artifacts**
([PROTOCOL §1, §9](../PROTOCOL.md#1-roles-and-the-single-builder-rule); [../CLAUDE.md](../CLAUDE.md)).
The two new layers slot in as follows:

**Who builds, when, committed where.**

| Artifact | Who | When | Committed where |
|---|---|---|---|
| `graph.json` (Mode A) | maintainer only | after each merge (`/graphify . --update`) | `graphify-out/` (today) |
| Vector index (Mode B) | maintainer only | on `/graphify` rebuild **or** an independent ingest cadence (open question, feasibility §8) | committed alongside `graphify-out/`, or regenerated — a regenerated artifact like the graph |
| Mode C | **no new committed artifact** | — | **none — it queries the already-committed CSVs in place.** |

**Mode C adds essentially zero build/governance surface** — this is a genuine advantage. The CSVs are
already committed source under PROTOCOL; DuckDB queries them live, so there is no index to rebuild,
re-embed, or keep fresh. The only governed pieces are the **DuckDB dependency** and the **resolver
config** (the `_dict.md`→table mapping logic). It cannot drift from the data because it *is* the data.

**Model discipline.** Graph builds stay pinned to `claude-opus-4-8` for reproducibility
([../CLAUDE.md](../CLAUDE.md)). The Mode-B **synthesis** model (civ-kb uses Sonnet 4.6) is an
*independent* choice (feasibility §7) — pin and record it like the
build model. The Mode-C **resolver** uses a model only to map question→table/column (not to compute);
pin and record that too, so a routing change is a deliberate, recorded event — the same philosophy as
`BUILD_INFO.md` (`knowledge_base/graphify-out/BUILD_INFO.md`).

**Two integration fixes this design must record (carry-overs #3, #4):**

1. **Query-embedding model lock (#3).** Mode B must embed queries with the **same** model the index
   was built with — Chroma's default-model footgun silently degrades retrieval otherwise
   (`proof/FINDINGS.md` surprise #2). Treat the embedding model as a
   provenance-stamped, pinned choice (a `BUILD_INFO`-style record for the vector index).
2. **Drop civ-kb's filename parser; use the WDB-relative `source_file` as the join key (#4).**
   civ-kb assumes a CIV `YYYY_ORG_TYPE_Title_LANG` convention and **mis-parses WDB's
   `lower_snake_case` names** (feasibility §3). For WDB, record the
   WDB-relative path as the join key and **drop the org/year/lang filters** — that path is the key
   that powers both the Mode-B document join and the Mode-C answer provenance.

**`.graphifyignore` discipline.** The serving/index code and these docs must stay out of the graph
(the assessment, the proofs, and `civ-kb/` are already listed; `proof_c/` was added here) so a
maintainer `/graphify .` never sweeps a second project's code/corpus into WDB
(feasibility §7 do-now risk).

---

## 10. Recommendation, open questions, and what each mode still needs proven

**Recommendation — build all three modes; they are complementary, and the cheap/proven ones are
ready.**

| Mode | Status | What's proven | What it still needs |
|---|---|---|---|
| **A — Graph** | **Exists today** | The graph is built, committed, and queried via `/graphify` (173 nodes / 320 edges). | Surfacing EXTRACTED/INFERRED in the answer UI (deferred serving layer). |
| **B — Passages** | **GO, scoped** | Document-level passage↔graph join, both directions, on real WDB data (`proof/FINDINGS.md`). | The **`.md` extractor branch** (carry-over #1) + **companion-note normalization** (carry-over #2) as hard requirements; the **refuse-when-thin** gate; **query-model lock** (#3); the serving layer. Marginal value scales with corpus size. |
| **C — Structured query** | **GO, worth building at any size** | Precise computed answers + clean refusals, on real CSVs (`proof_c/FINDINGS.md`); it gets right (74.2) what passages got wrong. | **DuckDB as a real dependency** + the **NL→table/column resolver** over `_dict.md` domains — the real cost (NL→token bridging, derived-metric formulas, grain, EAV quirks). |

**What each mode still needs *proven* (be explicit about what this work did and did not establish):**

- **A:** nothing new to prove — it is in production use. Open *product* question: how INFERRED edges
  are presented so users discount them.
- **B:** the join is proven; **not yet proven** is end-to-end synthesis quality on WDB prose at scale,
  the `.md`-branch retrieval value, and whether the refuse-when-thin floor is well-calibrated on a
  small corpus.
- **C:** precise-answer + clean-refusal is **proven here**; the **resolver** is *not* — that is the
  one piece a production Mode C must prove next (the engine is trivial; routing is the work).

**Open questions (carried from feasibility §8, plus new):**

- **Mode-C resolver:** LLM-over-`_dict.md` vs. a built synonym/embedding index of value domains — and
  how it handles ambiguity (sister tables) and derived metrics. *(The single biggest open item.)*
- **Freshness cadence (Mode B):** re-embed on every `/graphify` rebuild, or an independent ingest
  cadence?
- **Vendoring civ-kb core:** extract-core-as-library (preferred) vs. submodule.
- **UI / serving layer (deferred):** extend `graph.html`, a new web app, or an MCP/API over
  `graph.json` + Chroma + DuckDB? This — not the retrieval backends — remains the real cost
  (feasibility §6).

---

*Every codebase/protocol claim above cites its file. Proven results live in
`proof/FINDINGS.md` (Mode B join) and
`proof_c/FINDINGS.md` (Mode C); everything else is design under the scope
locks the requester set (no UI, no serving layer).*
