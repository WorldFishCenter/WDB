# WDB — operator instructions

WorldFish's shared knowledge brain: one queryable graph over every initiative's data, documents
and notes, plus the application that answers questions from it. The value is the
**cross-initiative connections** the graph surfaces, not any single file.

Keep the graph **connected, honest, and de-duplicated**: edges only on real domain meaning, one
node per real-world entity, provenance you can trust. Keep the application **honest**: it answers
from committed sources or says it cannot — it never invents.

| Need | Read |
|---|---|
| Contribution conventions (normative) | [PROTOCOL.md](PROTOCOL.md) |
| Commands, environment, services | [RUNNING.md](RUNNING.md) |
| Answer-contract spec (§6), the three modes | [docs/three-mode-architecture.md](docs/three-mode-architecture.md) |

This file carries what those cannot reach: the rules for **operating** the graph during
`/graphify` extraction (the extractor never reads the protocol), and the invariants the
application's tests cannot state for themselves.

## Two trees, one repo

- **The application** — the mode packages, router, services, `read-ui/`, `.claude/`. Changes on release.
- **The knowledge base** (`knowledge_base/`, gitignored) — initiative folders plus `graphify-out/`. Changes on contribution.

Resolve every path through `wdb_paths` (`REPO_ROOT`, `KB_ROOT`, `GRAPH_JSON`, `INDEX_DIR`), which
reads `WDB_KB` / `WDB_INDEX`. Deriving a root by climbing from `__file__` is what made the write
side write into one knowledge base while the readers read another.

Paths inside the graph, the catalog and every citation stay **KB-relative** (`peskas/trips.csv`,
never `knowledge_base/peskas/trips.csv`): the first segment is an **initiative name** throughout
the system, so a container directory there invents a bogus initiative.

## Build model & provenance

Only the **maintainer** runs `/graphify` ([PROTOCOL §2](PROTOCOL.md#2-the-contribution-protocol)).

Build with the session model pinned to the **exact** id — `/model claude-opus-4-8` — never the
floating `opus` alias, so a newer Opus changes the graph only when the pin is deliberately bumped.
The `/curate` and `/enrich` subagents pin the same id in their `.claude/agents/*.md` frontmatter.

The build command is **`/graphify knowledge_base --update`**. Building from the repo root
(`/graphify . --update`) is wrong, not merely noisy: it puts a container directory in the first
path segment, where an initiative name belongs.

**Stamp provenance on every build.** After a successful build, (over)write
`knowledge_base/graphify-out/BUILD_INFO.md` with the date; the exact model id you are running as
(from your system context, not the alias); `graphify --version`; the build mode; and the node and
edge counts from `graph.json`. Commit it with the rest of `graphify-out/`. A model or tool-version
change then shows up as a `BUILD_INFO.md` diff in the pull request.

**To bump the model**, change three places together — `/model …`, and `model:` in both
`.claude/agents/wdb-curator.md` and `.claude/agents/dict-enricher.md` — then rebuild.

Standard mode is the documented default. `--mode deep` tells subagents to be aggressive with
INFERRED edges, which amplifies exactly the speculative noise the first guard suppresses — reserve
it for deliberate one-off exploration and review the extra edges. Both guards still apply in deep mode.

## Graphify extraction: the two guards

Every semantic-extraction subagent prompt you dispatch **must** carry both guards, verbatim in
intent, on every backend (Claude subagents or Gemini) and in every mode (full build or `--update`).
Each guard has an input-side rule the protocol already enforces *and* this extractor-side
injection. **Both halves are required**: the protocol governs what contributors write, these govern
what the extractor re-derives anyway.

### Format-blind similarity guard

Protects **edges only on real domain meaning**.

> **Never emit a `semantically_similar_to` edge (or any similarity / "related" edge) whose basis is
> a dataset's _shape, format, or storage pattern_** — wide vs long, tidy-data structure, EAV /
> "one row per (entity × parameter)", row-per-X, parameter-per-column, file type, or encoding.
> These properties are shared by every file of that form, so linking on them mints **quadratic,
> uninformative** cross-links (every long table tied to every other long table). Link two tables
> **only on domain meaning** — same study, shared variables, one feeds the other, same
> site / species / measurement subject. If the *only* thing two nodes share is structural shape,
> emit **no** edge.

**Carve-out — grain is not shape.** The ban on `row-per-X` targets X as the **structural unit**
every table of the form shares: a "record", a "measurement", an "(entity × parameter)" cell. A
`## Grain` line naming X as a **domain subject** — *one row = one catch item of a trip*, *one
nutrient value for one ingredient* — is the measurement subject the rule already allows, so it
**may** support a **same-subject** edge. Two grain lines sharing only the template "one row per …"
with different subjects (catch item vs. ingredient) are not similar. Mint no structural edge from
the shared word "row", and keep a real same-subject link that happens to be phrased as a grain line.

A `_dict.md` reveals shape through its column list, node label and filename
(`..._observations_wide`, `..._measurements_long`) even when [habit 4](PROTOCOL.md#6-context-notes)
has kept the prose clean — so the extractor can re-derive shape and mint the noise regardless. Added
after a build linked `pondcube_observations_wide` ↔ `FICD` purely because both are tidy tables.

### Canonical-entity guard

Protects **one node per real-world entity**.

> Refer to each initiative/system by its **one canonical name** — the proper name in that
> initiative's hub `# H1` (e.g. **"Peskas"**, never "Peskas platform" / "Peskas Monitoring
> System"). For a shared real-world entity that already exists in the graph (the platform, a cited
> paper, a dataset, a place), **reference the existing node — do not re-mint the initiative concept
> under a variant label or a new id.** A satellite (`_about` child) anchors to its hub with a
> `part_of` edge; it must **not** create its own copy of the initiative concept.

**Then reconcile ids at merge — a maintainer build step.** graphify's `dedup.py` will not merge
labels under 12 characters ("Peskas") or coincidental cross-file matches, so a fresh extraction of
a short-named entity mints a **duplicate** node instead of merging. After extraction and **before
`build_merge`**, remap the new fragment onto existing canonical ids: for any node minted under a
variant id/label denoting an entity already in `graph.json`, rewrite its edges' `source`/`target`
to the existing id and drop the new node entry, so it cannot clobber the canonical node's attrs.
This held the Peskas-timeline re-extraction at **zero** new duplicates; skipping it added `peskas`
+ "Peskas Overview" + `PeskAAS` duplicates.

Residual variants frozen into an existing `_dict`/`_context` snapshot are accepted — a frozen note
is never rewritten. graphify's LLM dedup pass (`build_merge(dedup_llm_backend=…)`) stays **off**:
it conflicts with the pinned-model reproducibility above.

## Application invariants

Detail loads from `.claude/rules/` when you open the matching package. The four that hold everywhere:

- **The §6 answer contract lives in `wdb_contract`.** Import `Citation` / `Claim` / `Answer` /
  `Verdict` / `Unanswered` from there and merge fragments with `merge()`. It was declared in six
  places once, and the router's merge read four fields of it — which is how Mode A's verified
  "the graph records no connection" reached the UI as "the knowledge base doesn't cover this".
- **`wdb_ingest.gate.apply()` is the only thing that moves a contribution between states.** Every
  move, including the build's, is a declared transition in `gate.py`.
- **A mode's honesty gate decides refusals; the router surfaces them.** The router never
  back-fills one mode's gap with another mode's content, and never routes around a refusal.
- **Tests run offline and deterministically** by default, on the Replay backends. Live models and
  the Anthropic API sit behind adapters passed in at construction — see [RUNNING.md](RUNNING.md)
  for `uv run pytest` and the services.
