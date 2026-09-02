# WDB — operator instructions

This is a **collaborative Graphify knowledge-graph repo**. The conventions are specified in
[PROTOCOL.md](PROTOCOL.md) (the normative spec) and surfaced practically in [README.md](README.md)
and [USER_GUIDE.md](USER_GUIDE.md) (all `.graphifyignore`d). This file carries the rules Claude must
enforce when **operating** the graph — chiefly during `/graphify` extraction, which those conventions
cannot reach because the extractor never reads them.

**The aim.** WDB is WorldFish's shared knowledge brain — one queryable graph over every initiative's
data, documents, and notes, whose value is the **cross-initiative connections** it surfaces, not any
single file. Operate it to keep that graph **connected, honest, and de-duplicated**: edges only on
real domain meaning, **one node per real-world entity**, and provenance you can trust. The guards
below exist to protect exactly those three properties at build time.

Per the protocol ([PROTOCOL §2](PROTOCOL.md#2-the-contribution-protocol)),
only the **maintainer** runs `/graphify`. These rules apply to whoever is in that seat.

## Build model & provenance

Run `/graphify` builds with the session model **pinned to `claude-opus-4-8`** (Opus 4.8) — set
it with `/model claude-opus-4-8` before building. Pin the **exact** model, not the floating
`opus` alias: that keeps rebuilds reproducible, so a newer Opus only changes the graph when the
pin is deliberately bumped. The `/curate` and `/enrich` subagents are pinned to the same
`claude-opus-4-8` in their `.claude/agents/*.md` frontmatter.

**Stamp provenance on every build.** After a successful `/graphify` build, (over)write
`knowledge_base/graphify-out/BUILD_INFO.md` with: the date; the **exact model ID you are running as** (from your
system context — do not write the `opus` alias); the graphify version (`graphify --version`); the
build mode (`standard` / `--update` / `--mode deep`); and the node & edge counts from
`graph.json`. Commit it with the rest of `knowledge_base/graphify-out/`. It is the committed record of what
produced the current graph — a model or tool-version change then shows up as a `BUILD_INFO.md`
diff in the pull request.

**To upgrade the model:** change the pin in three places together — `/model …` (build session),
and `model:` in both `.claude/agents/wdb-curator.md` and `.claude/agents/dict-enricher.md` — then
rebuild so the new `BUILD_INFO.md` records the switch.

## Graphify extraction: format-blind similarity guard

When you run `/graphify` on this repo (full build **or** `--update`), every
semantic-extraction subagent prompt you dispatch **MUST** carry this rule (verbatim in
intent). It applies to all backends — Claude subagents or Gemini — so inject it into
whatever prompt drives extraction:

> **Never emit a `semantically_similar_to` edge (or any similarity / "related" edge)
> whose basis is a dataset's _shape, format, or storage pattern_** — wide vs long,
> tidy-data structure, EAV / "one row per (entity × parameter)", row-per-X,
> parameter-per-column, file type, or encoding. These properties are shared by every
> file of that form, so linking on them mints **quadratic, uninformative** cross-links
> (every long table tied to every other long table). Link two tables **only on domain
> meaning** — same study, shared variables, one feeds the other, same
> site / species / measurement subject. If the *only* thing two nodes share is
> structural shape, emit **no** edge.

**Carve-out — grain (the row's domain subject) is *not* shape.** The ban on `row-per-X` targets X as
the **structural unit** shared by every table of the form — a "record", a "measurement", an
"(entity × parameter)" cell. It does **not** target a `## Grain` line that names X as a **domain
subject**: *one row = one catch item of a trip*, *one nutrient value for one ingredient*. That is the
row's subject — the same "measurement subject" the rule above already allows — so it **may** support a
**same-subject** edge. Two grain lines that share only the template "one row per …" but whose subjects
differ (catch item vs. ingredient) are **not** similar: never mint a structural edge from the shared
word "row", and never *suppress* a real same-subject link just because a grain line contains it. (Grain
is recorded per [PROTOCOL §6, Template A](PROTOCOL.md#6-context-notes); habit 4's carve-out keeps it
domain-only on the input side.)

**Why this is a separate enforcement point, not just a note-writing rule.**
[Habit 4 (PROTOCOL §6)](PROTOCOL.md#6-context-notes) keeps shape language *out
of the notes*. But a `_dict.md` still reveals shape through its **column list, node
label, and filename** (`..._observations_wide`, `..._measurements_long`) even when the
prose is clean — so the extractor can re-derive shape and mint the noise anyway. Habit 4
governs the *input*; this guard governs the *extractor*. **Both are required.**

This was added after a build linked `pondcube_observations_wide` ↔ `FICD` purely because
both are tidy tables — a cross-domain, zero-information edge. As the corpus grows, every
new wide/long file would multiply that noise without this guard.

### Note on `--mode deep`

The documented default for this repo is **standard** mode (`/graphify knowledge_base` or
`--update`);
see [PROTOCOL §9 — Building & updating](PROTOCOL.md#9-maintainer-and-build-reference).
`--mode deep` instructs subagents to be **aggressive with INFERRED edges**, which amplifies
exactly the speculative similarity noise this guard suppresses — so it is **not** recommended
for routine rebuilds. Reserve it for deliberate one-off exploration, and expect to review the
extra edges. The guard above still applies in deep mode.

## Graphify extraction: canonical-entity guard

Protects the **one node per real-world entity** property. Like the similarity guard, it governs the
**extractor**, which cannot read the protocol's canonical-name rule
([PROTOCOL §6 — satellites](PROTOCOL.md#initiative-perspective-docs-satellites--the-canonical-name)).
It has two parts — an injection (input side) and a maintainer build step (output side). **Both are
required**: the injection alone does not fix it, because graphify's dedup refuses to merge short labels.

**1. Inject into every extraction subagent prompt** (verbatim in intent, all backends — Claude or
Gemini):

> Refer to each initiative/system by its **one canonical name** — the proper name in that initiative's
> hub `# H1` (e.g. **"Peskas"**, never "Peskas platform" / "Peskas Monitoring System"). For a shared
> real-world entity that already exists in the graph (the platform, a cited paper, a dataset, a place),
> **reference the existing node — do not re-mint the initiative concept under a variant label or a new
> id.** A satellite (`_about` child) anchors to its hub with a `part_of` edge; it must **not** create
> its own copy of the initiative concept.

**2. Reconcile entity ids at merge (maintainer build step).** graphify's dedup (`dedup.py`) **will not
merge labels under 12 characters** (e.g. "Peskas") or coincidental cross-file matches — so a fresh
extraction of a short-named entity mints a **new duplicate node** rather than merging onto the
existing one. So after extraction, **before `build_merge`, remap the new fragment onto existing
canonical node ids**: for any node the extractor minted under a variant id/label that denotes an
entity already in `graph.json`, rewrite that node's edges' `source`/`target` to the existing id and
**drop the new node entry** (so it cannot clobber the canonical node's attrs). This is what held the
Peskas-timeline re-extraction at **zero** new duplicates; skipping it added `peskas` + "Peskas
Overview" + `PeskAAS` duplicate nodes.

**Why a separate enforcement point.** [PROTOCOL §6](PROTOCOL.md#6-context-notes) makes contributors
*write* the canonical name and `/curate` drafts notes that way — but the extractor re-invents labels
and per-file ids on every run, and short proper names never auto-merge, so the input rule alone still
leaves duplicate entity nodes. The injection keeps new extractions consistent; the remap collapses
them onto one node. **Both are required**, same as Habit 4 + the similarity guard. Residual variants
from **frozen** `_dict`/`_context` snapshots are accepted (we never rewrite a frozen note); a heavier
consolidation is graphify's LLM dedup pass (`build_merge(dedup_llm_backend=…)`), **off by default**
(cost, determinism — it conflicts with the pinned-model reproducibility above).
