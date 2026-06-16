# WDB — ingestion pipeline design (the content-contribution / write-side flow)

**Date:** 2026-06-16 · **Status:** DESIGN ONLY — decision document for sign-off, then **PARKED
until the read query UI ships**; **builds nothing** (no UI, no API, no workflow code, no storage
migration, no agent server-wiring) · **Builds on:** [production-stack-design.md](production-stack-design.md)
(the KB/app split, git-vs-GCS division, single-builder publish flow this pipeline plugs into),
[../PROTOCOL.md](../PROTOCOL.md) §1 (single-builder), §2 (contribution protocol), §6 (companion
notes + Templates A/B/C + canonical name), §7 (supersession), §8 (frontmatter provenance fields),
[../CLAUDE.md](../CLAUDE.md) (pinned-model reproducibility + the two extraction guards),
[../.claude/agents/wdb-curator.md](../.claude/agents/wdb-curator.md),
[../.claude/agents/dict-enricher.md](../.claude/agents/dict-enricher.md) (the agents the pipeline
would trigger).

**What this is / is not.** This specifies the **write side** — how content gets contributed into
WDB — as a flow plus six resolved decisions, so the design is captured now while it's clear. It
proposes the **two-stage approval gate**, the **single-builder-preserving build trigger**, the
**provenance model**, the **format phasing**, the **workflow-state storage division**, and the
**server-side agent shape** — each with a recommendation and its tradeoff, for the requester to
sign off. It **does not** build an ingestion UI, an API, workflow code, a storage migration, or
server-wire the agents — the **read query UI is the next build**, and this write-side build waits
until after it. The deliverable is this document.

**The bridge in the meantime.** The existing `curate → enrich → PR → single-builder build` flow
**already is** the contribution mechanism ([production-stack §6](production-stack-design.md)): the
maintainer curates contributions via PR review — already the requester's "curate in background
first, automate later" model. Nothing here regresses that; it specifies the automated successor
that must preserve the same guarantees.

---

## 1. The flow and the guarantees it must preserve

### 1.1 The requester's sketch (the seven steps)

1. **Submit** — a user (maintainer, or a domain-allowlisted non-coder) uploads content via a UI.
2. **Auto-draft** — the curate + enrich agents fire and produce the companion note.
3. **Review** — the user sees the drafted note, edits if needed, approves.
4. **Build** — approval feeds a Graphify update.
5. **Integrate** — the contribution enters the knowledge base.
6. **Curator override** — the curator can see/edit/quality-check anything.
7. **Provenance** — every contribution is traceable to its contributor.

Read literally, steps 3–5 ("user approves → that triggers a build → it's in the KB") would make
the **submitting user the only gate** and **every approval its own build** — which silently breaks
two load-bearing protocol rules. The six decisions below keep the flow's intent while restoring
those rules; the corrected flow is in §1.3.

### 1.2 The guarantees any write-side automation must preserve

These are not negotiable; the production-stack design already commits the project to them, and the
task's constraints require the approval gate to be **at least as strong as today's maintainer PR
review**. Every decision in §2–§7 is checked against this table.

| Guarantee | Where it's set | What the pipeline must not do |
|---|---|---|
| **Single-builder rule** — one build owner runs `/graphify` and commits `graphify-out/`; the PR is the only path in | [PROTOCOL §1](../PROTOCOL.md), [§9](../PROTOCOL.md) | Let approvals trigger concurrent or per-contribution rebuilds (§2). |
| **Pinned-model reproducibility** — builds pinned to the **exact** `claude-opus-4-8`, agents pinned in frontmatter, `BUILD_INFO.md` stamps each build | [CLAUDE.md](../CLAUDE.md), [PROTOCOL §9](../PROTOCOL.md) | Run a build (or a server-side agent) on a floating alias or an unpinned model (§2, §6). |
| **The curation gate** — nothing reaches the shared graph without curator review; today the **PR review *is* the gate** | [production-stack §6](production-stack-design.md), [PROTOCOL §1-§2](../PROTOCOL.md) | Replace a two-person gate (contributor + maintainer) with one-person self-approval (§1). |
| **Note governance** — companion notes are human-readable, version-controlled, reviewed; **never in a database** | [production-stack §2b](production-stack-design.md), constraints | Make a database the source of truth for approved authored text (§5). |
| **Companion-note structure** — Templates A/B/C; frozen snapshots vs. the living `_about.md`; one canonical name; satellite anchoring | [PROTOCOL §6](../PROTOCOL.md) | Emit notes that bypass the templates, re-mint variant entity nodes, or rewrite frozen snapshots (§6). |
| **Supersession** — knowledge changes are append-only `## Updates` + `superseded_by`/`supersedes` links, body not frontmatter | [PROTOCOL §7](../PROTOCOL.md) | Overwrite a frozen snapshot, or encode supersession as an invisible frontmatter key (§5, §6). |
| **Provenance** — graphify carries only `source_url`/`captured_at`/`author`/`contributor` onto nodes | [PROTOCOL §8](../PROTOCOL.md) | Silo provenance into per-user graphs, or stamp one doc's source onto a synthesis hub (§3). |
| **The two extraction guards** — format-blind similarity guard + canonical-entity guard injected into every extraction subagent | [CLAUDE.md](../CLAUDE.md) | Run a server-side build/extraction that drops the guards (§2, §6). |

### 1.3 The flow as states (prose diagram)

The pipeline is a **state machine over a contribution**, not a chain of instant side-effects. A
contribution moves through:

```
SUBMITTED ─▶ DRAFTED ─▶ UNDER_REVIEW ─▶ PENDING ─▶ QUEUED ─▶ BUILT ─▶ LIVE
              (agents)   (Stage-1:       (Stage-2:  (note→git, (single-  (artifacts
                          contributor     curator    enters    builder    published,
                          approves)        signs off) queue)    build)     read UI sees it)
                                                                              ▲
                                              CURATOR_OVERRIDE ────────────────┘
                                              (reactive: edit/quality-check anything, any time)
```

- **SUBMITTED** — the user uploads a Phase-1 format (§5: PDF, tabular, docs). A workflow row is
  created in the database (§5); the binary goes to object storage; **provenance is stamped at this
  moment** (§3): `contributor` = submitter, `captured_at` = submission time, `source_url` = origin.
- **DRAFTED** — the `wdb-curator` agent (and `dict-enricher` for tables) fire **server-side, on the
  pinned model** (§6) and produce the draft placement + companion note, exactly as `/curate` +
  `/enrich` do locally today.
- **UNDER_REVIEW → PENDING** — the contributor reviews/edits/approves the draft (**Stage-1**); the
  contribution then waits in **PENDING** for **curator sign-off** (**Stage-2**) (§2 — the gate).
- **QUEUED** — on curator sign-off the **approved note is written to git** (the system of record,
  §5) and the contribution **enters the build queue**. UX: *"approved and queued — appears after
  the next build,"* not *"instantly live"* (§2).
- **BUILT → LIVE** — a **controlled single-builder step** drains the queue with one pinned-Opus
  `/graphify . --update`, commits `graphify-out/`, and publishes runtime artifacts to the pinned
  GCS version ([production-stack §3](production-stack-design.md)). The deployed read service then
  answers over the new graph.
- **CURATOR_OVERRIDE** — a **reactive** path the curator may take at any time to edit or
  quality-check anything already live. This is the requester's step 6 — and it is an *override, not
  the gate* (§2 draws the distinction sharply).

---

## 2. Decision 1 — the approval gate (the most important decision)

**The question.** Who must approve a contribution before it reaches the shared graph?

**The naive reading is a regression.** "User approves their own note → that triggers integration"
makes the **submitting user the sole gate**. Today's protocol requires **two** distinct people: the
**contributor** prepares and opens a PR, and the **maintainer** reviews and merges it
([PROTOCOL §1-§2](../PROTOCOL.md)). The PR review *is* the control gate
([production-stack §6](production-stack-design.md)). Self-approval collapses that two-person gate
into one and is **strictly weaker** than what the project runs today — which the constraints forbid.

**Recommendation — a two-stage gate, plus a distinct override.**

- **Stage 1 — contributor approval.** The user reviews/edits the auto-drafted note and approves it.
  This says *"the content is ready for review"* — it is the contributor's half, the analogue of
  **opening a PR**. It does **not** put anything in the graph.
- **PENDING state.** An approved-by-contributor contribution sits in **pending**, visible to the
  curator. This is the analogue of an **open PR awaiting review**.
- **Stage 2 — curator sign-off.** The contribution integrates **only after the curator signs off**
  (the requester now; an automated quality check later, never instead). This is the analogue of the
  **maintainer merging the PR** — the gate that exists today, preserved one-for-one.

**A *gate* is not an *override* — keep both, and don't let one masquerade as the other.** The
requester lists a "curator override" (step 6) separately. That is a **reactive** mechanism — *fix
after it's live*. A reactive override is **weaker than a gate** on its own: by the time the curator
acts, the bad edge or duplicate node is already in everyone's queries (and a shared cross-initiative
brain means one contributor's error pollutes *every* initiative's answers). So the override is an
**additional safety net layered on top of** the Stage-2 gate, never a replacement for it. Keep both:
*pending-until-curator-approved* prevents bad content from going live; *curator override* fixes
what slips through or later proves wrong (and is also the natural hook for [§7](../PROTOCOL.md)
supersession edits).

**Why pending-until-curator-approved preserves protocol integrity.** It is the PR flow re-expressed
as workflow state, edge-for-edge:

| Today (PR flow) | Pipeline (two-stage gate) |
|---|---|
| Contributor prepares file + runs `/curate`/`/enrich` | Submit → agents auto-draft (Stage-0/1) |
| Contributor opens PR ("ready for review") | Stage-1 contributor approval |
| Open PR awaiting maintainer | **PENDING** state |
| Maintainer reviews + **merges** | **Stage-2 curator sign-off** |
| Maintainer rebuilds + commits `graphify-out/` | Controlled single-builder build (§2 / Decision 2) |

Because Stage 2 is the same human checkpoint as the merge, the gate is **at least as strong as
today's review** — and the automation only changes *how* the contributor's half is prepared (an
agent drafts the note instead of the contributor hand-writing it), not *who* lets it into the graph.

**How it maps to "curate in background first, automate later."** Initially the curator (the
requester) signs off on **every** pending contribution by hand — exactly reviewing every PR today.
That is the "curate in background" phase: full human control, zero new trust assumptions. Later, an
**automated quality check** (shape gate already deterministic via `dict_enricher.py`; note-structure
and guard checks scriptable) can **pre-screen** pending contributions to reduce curator load — but
it **augments** the gate, it does not remove it. The curator sign-off (and the override) remain. The
automation lowers effort; it never lowers the bar. This is the requester's plan made concrete.

**Tradeoff.** The two-stage gate adds **latency**: a contributor cannot self-publish; they wait for
curator sign-off and then for the next build. The alternative — instant self-publish — is faster but
is precisely the regression the protocol forbids, because the graph's value is its *trusted,
de-duplicated, honestly-edged* cross-initiative connections, and one un-reviewed contribution
degrades that for everyone. The latency is the cost of integrity. **Mitigations:** make pending
status fully visible to the contributor (they see "awaiting curator," not silence); let the curator
**batch** sign-offs (which also batches the build, §2); and use the auto-QA pre-screen to clear
trivially-good contributions faster once it exists. We accept latency; we do not accept a weaker gate.

---

## 3. Decision 2 — the build trigger (single-builder rule under automation)

**The question.** What does "approval feeds a Graphify update" (step 4) actually trigger?

**The naive reading breaks §1 and §9.** A literal "every approval triggers a build" means
**concurrent builds** racing each other, **non-deterministic** extraction order, and the loss of
**pinned-model reproducibility** — the build might run on whatever model the triggering process
happened to hold, and two builds committing `graphify-out/` at once corrupt the shared artifact.
[PROTOCOL §1/§9](../PROTOCOL.md) and [CLAUDE.md](../CLAUDE.md) exist precisely to prevent this.

**Recommendation — approval queues; a controlled single-builder step drains the queue.** Curator
sign-off (Decision 1, Stage 2) **enqueues** the approved contribution; it does **not** build. The
graph rebuild runs as a **single-builder step** — one at a time, batched/scheduled or
maintainer-triggered, **always on the pinned `claude-opus-4-8`** — that drains the queue with one
`/graphify . --update`, commits `graphify-out/`, writes `BUILD_INFO.md`, and publishes runtime
artifacts to the pinned GCS version. This is **exactly** the
[production-stack §3 single-builder publish flow](production-stack-design.md) with a queue feeding
it; the "builder" stays a controlled pipeline step — still single, still pinned — whether the
maintainer runs it or a later automated job holds the pin.

**Why batching is a feature, not a limitation.** One build over N queued contributions amortizes
build cost, produces **one** reproducible graph with **one** `BUILD_INFO.md` stamp (date, exact
model id, graphify version, mode, node/edge counts), and keeps the two extraction guards
(§6 / [CLAUDE.md](../CLAUDE.md)) applied uniformly across the batch. You cannot get both
"instant per-contribution rebuild" *and* "deterministic, single-owner, pinned graph" — they are
mutually exclusive. The single-builder rule chose the latter; this pipeline honors that choice.

**UX consequence (state it plainly).** The contributor experience is *"approved and queued — your
contribution appears after the next build,"* not *"instantly live."* PENDING → QUEUED → BUILT → LIVE
(§1.3) are visible states, so the wait is transparent rather than mysterious. A build cadence
(maintainer-on-demand initially; scheduled later) sets expectations.

**Tradeoff.** Contributions are **not instant** — there is a build cadence, and a contribution
queued just after a build waits for the next one. The rejected alternative (per-approval trigger) is
"instant" but sacrifices reproducibility and invites concurrent-build corruption — a non-starter
against §1/§9. Cadence is the price of a trustworthy shared graph; it is the same price the team
already pays today (the maintainer rebuilds in batches after merging PRs).

**Pin discipline carries server-side.** If the single-builder step is later automated (not run by
the maintainer in Claude Code), the automated builder **must** hold the exact `claude-opus-4-8` pin
and write `BUILD_INFO.md` — the [CLAUDE.md](../CLAUDE.md) "change the pin in three places together"
rule extends to that server config as a fourth pin site (see Decision 6).

---

## 4. Decision 3 — provenance model (decide now, honor now)

**The question.** How is every contribution made traceable to its contributor (step 7), and how
does that enable a future "interact with your own knowledge" feature without fracturing the graph?

**The hook already exists.** [PROTOCOL §8](../PROTOCOL.md) already has graphify carry exactly four
frontmatter fields onto a file's nodes: `source_url`, `captured_at`, `author`, `contributor`. No new
data model is needed — the pipeline just **populates these at submission (SUBMITTED state, §1.3):**

- **`contributor`** — the WDB user who submitted the content (the pipeline's identity stamp).
- **`author`** — the underlying content's real author (a paper's author, a report's writer). Distinct
  from `contributor`: who *made* the content vs. who *brought it into WDB*. For original notes the
  two may coincide; for an uploaded external paper they differ.
- **`captured_at`** — the submission timestamp (the one temporal "as-of" stamp graphify supports,
  [PROTOCOL §7-§8](../PROTOCOL.md)).
- **`source_url`** — where the content came from (an upload origin, an external link).

**Crucial — "your knowledge" is a *filter over one unified graph*, never a per-user partition.** The
future "interact with your own knowledge" feature **must** be a query lens — *"show me the subgraph
where `contributor == me`"* — applied over the **single shared graph**, not a separate per-user
graph. The KB's entire value is **cross-contributor, cross-initiative connections**
([CLAUDE.md](../CLAUDE.md), [PROTOCOL §6 habit 2](../PROTOCOL.md)): your contribution is valuable
precisely because it links to *other people's* nodes. Partitioning per user would sever exactly the
edges the brain exists to surface. **Per-user is a lens; it is never a fork.** State this in the data
model now so provenance is captured as **node attributes on a unified graph**, and "my knowledge"
is implemented as a filter — never as a storage boundary.

**Respect the satellite provenance rule.** [PROTOCOL §6 (satellite rule 4)](../PROTOCOL.md) says
provenance lives on the **doc it describes**, never on a synthesis **hub**: a living
`<initiative>_about.md` is a synthesis with no single source, so the pipeline must **not** stamp a
submitter's `source_url` onto a hub it merely edited. The provenance stamp attaches to the submitted
artifact's **own** companion note. The server-side curator agent already enforces this (its step-4
satellite rules) and must continue to.

**Tradeoff.** Stamping provenance at submission is essentially free (it's frontmatter the protocol
already carries) — the only real decision is **discipline**: `contributor` vs. `author` must be kept
distinct, and the per-user lens must never be allowed to harden into a partition under future
pressure ("can I have my own private graph?"). The cost of getting this wrong is a fractured graph;
the cost of getting it right is just naming the fields correctly now. This is the **one piece
honorable immediately** even while the pipeline is parked (§9.3).

---

## 5. Decision 4 — format scope (phase it; don't balloon the first build)

**The question.** Which of the formats graphify supports (PDF, tabular, docs, video, images,
diagrams, URLs) does the first ingestion UI accept?

**Each format is a different extraction path.** Video needs transcription, images/diagrams need the
vision step, URLs need fetch (and already have a maintainer path via `/graphify add <url>`,
[PROTOCOL §9](../PROTOCOL.md)). Shipping all of them day one balloons the first build with extraction
wiring **and** per-format QA paths.

**Recommendation — phase the formats.**

- **Phase 1 (first ingestion-UI version): the common cases the corpus is already made of and the
  agents already handle** — **PDF**, **tabular** (`.csv`/`.xlsx`), and **docs** (`.md`/`.txt`/`.docx`).
  These map directly onto the existing `wdb-curator` (Template B) and `dict-enricher` (Template A +
  shape gate) paths ([PROTOCOL §5 table](../PROTOCOL.md)) — no new extraction surface, so Phase 1
  reuses what's proven.
- **Later pass: the richer formats** — **video** (transcription), **images/diagrams** (vision), and
  **URLs** (fetch). Each is added when its extraction + QA path is ready. URLs can defer longest
  because the maintainer `/graphify add <url>` path already covers them in the bridge phase.

**Tradeoff.** Phase 1 excludes content types a non-coder might want to submit (e.g. a field video).
But the corpus today is PDFs/CSVs/docs, so Phase 1 covers the bulk of real contributions while
keeping the first build small and shippable; deferring video/image/URL avoids three distinct
extraction-and-QA build-outs landing at once. The cost is that early adopters of those formats wait;
the benefit is the first ingestion UI ships at all. (This phasing is the write-side echo of
[production-stack §5-§6](production-stack-design.md), which defers the vector-store migration and the
web front door on the same "don't over-build first" logic.)

---

## 6. Decision 5 — where the workflow state lives (the database's real job)

**The question.** What does the database (the requester's available MongoDB Atlas) actually hold —
and what must it **not** hold?

**The insight: the pipeline's *workflow* is legitimately database-shaped; the *authored text* is
not.** Pending drafts, approval/sign-off status, the build queue, the per-contributor provenance
index, and an audit log are mutable, queryable workflow state — a database is the right home. The
**approved companion notes are not** — they are the protocol's reviewable, version-controlled core
and stay in **git** ([production-stack §2b](production-stack-design.md)).

**Recommendation — a clean four-way division (full table in §8):**

- **Ingestion workflow state → database (Atlas).** Submissions and their state (SUBMITTED…LIVE),
  the **draft note while it's in review**, approval + curator-sign-off status, the build queue, the
  contributor/provenance index, and the audit trail of who-approved-what-when.
- **Approved companion notes → git.** On curator sign-off the draft is **written into git** as the
  system of record; from that moment **git is canonical** and the database row holds **status only**,
  not the authoritative text.
- **Chunks → Atlas vector search.** The Mode-B index, *if and when* it migrates off file-based Chroma
  — the named-later target in [production-stack §5](production-stack-design.md), not now.
- **Binaries → object storage.** Source PDFs/`.docx`/`.pptx` to a GCS source bucket (or git-LFS),
  per [production-stack §2b](production-stack-design.md).

**The database holds the *workflow*, not the source of truth for authored text.** A draft note in
the database is a **transient working copy** during review; it is **not** in the knowledge base yet.
The handoff happens at the **Stage-2 sign-off → QUEUED boundary** (§1.3): the draft is committed to
git, and the database thereafter points at it with a status, never shadows it. This is the line that
keeps note governance intact — there is exactly one authoritative copy at every stage (DB draft
*before* approval; git *after*), never two competing ones.

**Tradeoff.** During review the note exists in the database (draft) and, after approval, in git —
so the design must make **which copy is authoritative at each state** unambiguous (it does:
pre-approval = DB working copy, not yet in KB; post-approval = git, DB holds status). The risk if
blurred is dual-source-of-truth drift; the mitigation is the single hard handoff at sign-off. The
benefit is that the database earns its place (it manages the workflow Atlas is good at) **without**
becoming the store of record for protocol-governed text — which [production-stack §2b /
§7.4](production-stack-design.md) explicitly rejects.

---

## 7. Decision 6 — running the curate/enrich agents server-side

**The question.** The `wdb-curator` and `dict-enricher` agents are Claude Code features today (run
locally via `/curate` and `/enrich`). How would the pipeline invoke them server-side? (High-level
feasibility — **not** a build.)

**Recommendation — invoke the pinned model with the agents' instructions; run the deterministic
enricher as-is.** Each agent is, in essence, *(its `.claude/agents/*.md` body as the system prompt)*
+ *(the tools Read/Write/Edit/Bash/Glob/Grep)* + *(the pinned model)*. Server-side, the pipeline
makes an API call to the pinned **`claude-opus-4-8`** (via the Anthropic API or the Claude Agent SDK,
which exists precisely to run Claude Code agents programmatically), passing the agent's instructions
as the system prompt, operating over the submitted file in a sandboxed working directory, and
returning the draft placement + companion note — the same output `/curate` produces locally. The
**`dict-enricher`'s shape gate and value-domain extraction are already a deterministic, no-LLM
pandas script** (`.claude/scripts/dict_enricher.py`) — it ports to the server **directly**, model
not required, exactly as it runs today.

**The guards and the pin come with it.** A server-side extraction is still a graphify build, so the
[CLAUDE.md](../CLAUDE.md) **format-blind similarity guard** and **canonical-entity guard** must be
injected into the server-side extraction prompt exactly as they are locally — and the canonical-entity
**id-remap** maintainer step still runs before merge. The server-side agent invocation **must** use
the exact pinned model; the CLAUDE.md "change the pin in three places together" rule grows to a
**fourth pin site** (the server config) when this lands. The agents stay pinned per
[PROTOCOL §9](../PROTOCOL.md).

**Tradeoff.** Reusing the Agent SDK + the existing agent markdown means **no reimplementation** — the
server runs the same instructions the maintainer runs — which is the cheap, faithful path. The cost
is one more place the pin must be kept in sync (flagged above) and the operational work of running
Claude in a sandboxed server context with file access. Both are deferred build concerns; feasibility
is clear, and nothing here is built now.

---

## 8. Storage division (the unambiguous four-way split)

This is the storage contract the pipeline writes against. It **extends**
[production-stack §2b](production-stack-design.md) (which split git vs. GCS for the *read* stack) with
the **workflow database** the *write* stack adds — without weakening note governance.

| Class | Concretely | Home | Authoritative? | Why |
|---|---|---|---|---|
| **Ingestion workflow state** | submissions + state machine, draft-in-review, approval/sign-off status, build queue, contributor/provenance index, audit log | **Database (Atlas)** | Yes, **for workflow** | Mutable, queryable, transient process state — what a database is for; matches the team's Atlas availability. |
| **Approved companion notes** | `_dict.md`, `_context.md`, `_about.md`, `idea_*.md` | **git** | **Yes, for authored text** | The protocol's reviewable, version-controlled core ([PROTOCOL §6](../PROTOCOL.md)); `/curate`/`/enrich`/PR operate on these. **Never** a database ([production-stack §2b](production-stack-design.md)). |
| **Tidy CSVs (source of truth)** | the queryable tables Mode C reads | **git** (and published to GCS for serving) | Yes (git) | Small, diff-able, PR-reviewed via the `/enrich` shape gate; published copy is a *built artifact*, not the source ([production-stack §2b-§3](production-stack-design.md)). |
| **Built graph + runtime artifacts** | `graph.json`, `graph.html/.svg`, `GRAPH_REPORT.md`, `BUILD_INFO.md`; the Chroma index; queryable CSVs | **git** (provenance) **+ GCS** (serving, pinned version) | git for provenance | Committed for the reproducibility record; published to a pinned GCS version the read service reads ([production-stack §3](production-stack-design.md)). |
| **Chunks / vector index** | Mode-B passage embeddings | **file Chroma now → Atlas vector search later** | n/a (regenerable) | A machine artifact rebuilt on publish; Atlas is the named-later migration target ([production-stack §5](production-stack-design.md)), not now. |
| **Binaries** | source PDFs / `.docx` / `.pptx` | **object storage** (GCS bucket / git-LFS) | the uploaded original | Read only at build/ingest time, never by the serving app; tiny corpus stays in git for now, moves when volume grows ([production-stack §2b](production-stack-design.md)). |

**The one line that protects governance:** the **database holds the workflow, not the source of
truth for authored text**. A draft lives in the database only until curator sign-off; at sign-off it
is written to git and git is canonical thereafter. Approved notes are **git-governed, always**.

---

## 9. Recommendation, forks for sign-off, and sequencing

### 9.1 The recommended pipeline (one line each)

- **Approval gate:** a **two-stage gate** — contributor approval → **PENDING** → **curator
  sign-off** — plus a distinct reactive **curator override**. As strong as today's PR review (§2).
- **Build trigger:** sign-off **queues**; a **controlled single-builder step** (one at a time,
  pinned `claude-opus-4-8`, batched) drains the queue and publishes — the
  [production-stack §3](production-stack-design.md) flow with a queue in front (§3).
- **Provenance:** stamp `contributor`/`author`/`captured_at`/`source_url` at submission; "your
  knowledge" is a **filter over one unified graph**, never a per-user fork (§4).
- **Format scope:** **Phase 1 = PDF + tabular + docs**; video/images/URLs later (§5).
- **Workflow state:** **Atlas holds the workflow** (drafts-in-review, status, queue, provenance
  index); **git holds approved notes**; Chroma/Atlas holds chunks; object storage holds binaries (§6, §8).
- **Server-side agents:** invoke the **pinned model** with the agents' instructions (Agent SDK); the
  deterministic enricher script ports as-is; guards + pin carry over (§7).

### 9.2 The genuine forks — **your** decisions

1. **Is the two-stage gate (contributor approve → pending → curator sign-off) the right gate?** →
   *Recommend yes — it is today's PR review re-expressed as workflow state, and the constraints
   require a gate at least that strong.* The rejected alternative is **user self-approval as the sole
   gate**, which is weaker than today and would let one un-reviewed contribution degrade the shared
   graph. (§2)
2. **Build trigger: queue-then-single-builder, or per-approval build?** → *Recommend
   queue-then-single-builder, pinned and batched.* Per-approval "instant" builds break §1/§9
   (concurrency, non-determinism, lost pinned reproducibility). Cost: contributions appear after the
   next build, not instantly. (§3)
3. **Phase-1 formats = PDF + tabular + docs, defer video/images/URLs?** → *Recommend yes.* The cost
   is that early submitters of richer formats wait; the benefit is a small, shippable first build. (§5)
4. **Workflow state in Atlas, approved notes in git — confirm the boundary?** → *Recommend yes, with
   the hard handoff at curator sign-off (DB draft → git commit).* The risk if blurred is
   dual-source-of-truth drift; the line above removes it. (§6)

### 9.3 PARKED until the read UI ships — and what can be honored immediately

**This pipeline is PARKED.** The **read query UI is the next build**; this write-side build waits
until after it. In the meantime the **existing `curate → enrich → PR → single-builder build` flow is
the contribution mechanism** — the maintainer curates via PR review (the requester's "curate in
background" model already running). Nothing here is built now.

**Honorable immediately — the provenance metadata (Decision 3).** It needs **no UI and no build**:
it is pure frontmatter convention (`contributor`/`author`/`captured_at`/`source_url`) that
[PROTOCOL §8](../PROTOCOL.md) already carries onto nodes. The curator can begin stamping contributor
provenance on companion notes **today**, so that when the pipeline lands the data model already
holds it — and the eventual "interact with your own knowledge" lens has data to filter. (Capture it
on the **doc it describes**, never on a synthesis hub — [PROTOCOL §6 satellite rule 4](../PROTOCOL.md).)
Equally, the **two-stage gate already exists in spirit** as the PR review, so adopting this design
later is a formalization, not a reversal — nothing regresses while parked.

### 9.4 Risks to the protocol (flagged, per the constraints)

- **User self-approval as the only gate** → *rejected* — weaker than today's two-person PR review;
  the two-stage gate restores it (§2).
- **Per-approval build trigger** → *rejected* — breaks the single-builder rule and pinned
  reproducibility (§1/§9); queue + single-builder step preserves them (§3).
- **Approved notes (or source text) in a database** → *rejected* — breaks the human-readable,
  reviewable, version-controlled core; the database holds **workflow only** (§6, §8;
  [production-stack §7.4](production-stack-design.md)).
- **Per-user knowledge partition** → *rejected* — would sever the cross-contributor edges the brain
  exists to surface; "your knowledge" is a **filter over one graph** (§4).
- **Server-side build/extraction that drops the pin or the guards** → *flagged* — the pinned model,
  the format-blind similarity guard, the canonical-entity guard + id-remap all carry to the server;
  the pin grows to a fourth sync site (§7).
- **Stamping a submitter's source onto a synthesis hub** → *flagged* — provenance lives on the doc it
  describes, never on a living `_about.md` hub (§4; [PROTOCOL §6 satellite rule 4](../PROTOCOL.md)).

### Constraints honoured

Design only — **nothing built**: no ingestion UI, API, workflow code, storage migration, or
agent server-wiring. Every protocol guarantee in §1.2 is preserved in every proposal: the
single-builder rule and pinned-model reproducibility (§3, §7), a curation gate **at least as strong
as today's PR review** (§2), companion-note structure + supersession (§6 honors the templates and the
frozen-snapshot rule), note governance (approved notes stay git-governed; the database holds workflow
state only — §6, §8), and provenance without siloing (§4). Anything that would weaken these is
flagged as a risk above, not offered as a feature (§9.4). The design **reuses** the existing
GCS / Cloud Run / Atlas infra and the production-stack publish flow, phases the formats, and is
**explicitly parked** until the read UI ships — with the provenance-metadata piece honorable now.
