# WDB — operator instructions

This is a **collaborative Graphify knowledge-graph repo**. The conventions are specified in
[PROTOCOL.md](PROTOCOL.md) (the normative spec) and surfaced practically in [README.md](README.md)
and [USER_GUIDE.md](USER_GUIDE.md) (all `.graphifyignore`d). This file carries the rules Claude must
enforce when **operating** the graph — chiefly during `/graphify` extraction, which those conventions
cannot reach because the extractor never reads them.

Per the protocol ([PROTOCOL §2](PROTOCOL.md#2-the-contribution-protocol)),
only the **maintainer** runs `/graphify`. These rules apply to whoever is in that seat.

## Build model & provenance

Run `/graphify` builds with the session model **pinned to `claude-opus-4-8`** (Opus 4.8) — set
it with `/model claude-opus-4-8` before building. Pin the **exact** model, not the floating
`opus` alias: that keeps rebuilds reproducible, so a newer Opus only changes the graph when the
pin is deliberately bumped. The `/curate` and `/enrich` subagents are pinned to the same
`claude-opus-4-8` in their `.claude/agents/*.md` frontmatter.

**Stamp provenance on every build.** After a successful `/graphify` build, (over)write
`graphify-out/BUILD_INFO.md` with: the date; the **exact model ID you are running as** (from your
system context — do not write the `opus` alias); the graphify version (`graphify --version`); the
build mode (`standard` / `--update` / `--mode deep`); and the node & edge counts from
`graph.json`. Commit it with the rest of `graphify-out/`. It is the committed record of what
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

The documented default for this repo is **standard** mode (`/graphify .` or `--update`);
see [PROTOCOL §9 — Building & updating](PROTOCOL.md#9-maintainer-and-build-reference).
`--mode deep` instructs subagents to be **aggressive with INFERRED edges**, which amplifies
exactly the speculative similarity noise this guard suppresses — so it is **not** recommended
for routine rebuilds. Reserve it for deliberate one-off exploration, and expect to review the
extra edges. The guard above still applies in deep mode.
