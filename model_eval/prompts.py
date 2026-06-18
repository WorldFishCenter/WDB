"""Per-model adapted prompts — IDENTICAL bar, model-appropriate expression.

The fairness principle (the whole point of this eval): the REQUIREMENTS are the
spec and do not bend per model; only their EXPRESSION is adapted to each model's
conventions, so each model is tested on the TASK, not on parsing Claude-specific
phrasing.

* Anthropic candidates (Haiku) are Claude models -> their fair prompt IS the
  existing pinned Claude prompt (rewriting it would be the unfair move). The
  runners import those directly from the modes; nothing is redefined here.
* Gemini gets the same requirements re-expressed Gemini-style (numbered
  imperatives, "return JSON only"); those adapted system instructions live here.

Mode C's grain + derived guards and Mode A's six honesty rules are preserved
verbatim-in-intent below — diff them against ``mode_c/resolver.py`` (GRAIN_GUARD,
DERIVED_GUARD) and ``mode_a/reasoner.py`` (SYSTEM_PROMPT) to confirm the bar held.
"""
from __future__ import annotations

# --------------------------------------------------------------------------- #
# Mode C resolver — Gemini-adapted system instruction (same bar as build_resolver_prompt)
# --------------------------------------------------------------------------- #
def mode_c_gemini(catalog_corpus: str) -> str:
    return f"""You map ONE natural-language quantitative question to a structured \
resolution over the fixed set of tidy CSV tables below, or you refuse. Use ONLY \
the catalog. Never invent a table, column, or value. Follow every rule exactly:

1. GRAIN. Decide whether one table row is the same unit the question asks about. \
If the row is finer than that unit (for example one row per catch item, but the \
question is "per trip"), set grain_key to the column to collapse over (e.g. \
trip_id) and aggregate AFTER collapsing — never average a trip-level column over \
raw catch rows. Read each table's "## Grain" line to decide. If the row already \
is the unit the question asks about, leave grain_key null.

2. DERIVED METRICS. If the asked metric is NOT a stored column (for example CPUE \
= catch per unit effort), do NOT substitute a proxy column. Put the SQL \
expression in derived_formula, list the columns it uses in derived_inputs, and \
state the denominator/assumption you chose in assumptions (with the \
alternatives). Never relabel a stored column as the derived metric.

3. ROUTING. Pick a table only when a distinctive value in the question pins \
exactly one table (a place, a species, a scientific name, an enumerated \
gear+region); put that token in pinned_by. If a value is shared across sister \
tables and nothing else disambiguates, set outcome to "needs_disambiguation" and \
list the candidate tables in candidates. If the value or column is absent from \
every table, set outcome to "cannot_resolve".

4. OUTPUT. Return ONLY one JSON object matching the schema — no prose, no \
markdown fences. Use outcome="resolve" for a concrete answer; otherwise \
"cannot_resolve" or "needs_disambiguation".

{catalog_corpus}
"""


# Output conventions the gate/executor require — value-level, not structural, so
# stated identically to EVERY model (the schema enum only constrains op). This is
# the structured-output contract, not a per-model favour: it is what makes a
# resolution executable at all, and the real resolver relies on the same shape.
RESOLVER_CONVENTIONS = """Output conventions (the executor requires these exactly):
- outcome: "resolve" | "cannot_resolve" | "needs_disambiguation".
- table: the exact CSV path from a catalog "TABLE:" header (e.g. "peskas/kenya_validated_trips.csv").
- aggregation: one of AVG, COUNT, SUM, MIN, MAX (uppercase).
- pinned_by: the SINGLE bare distinctive value that selects the table — e.g. "Kwale",
  "Zanzibar", "Inhambane", "fish meal". NOT a "column=value" expression, NOT a column name.
- metric_column: the stored column to aggregate (null when using derived_formula).
- derived_formula / derived_inputs / assumptions: only for a derived metric (e.g. CPUE).
  When the metric is derived, put its name (e.g. "cpue") in metric_label or notes.
- grain_key: the column to collapse to (one row per) before aggregating, e.g. "trip_id";
  null when the row already is the unit the question asks about.
- filters: list of {column, op: "=" | "contains", value} — the WHERE conditions,
  e.g. {"column":"gaul_1_name","op":"=","value":"Kwale"}.
- candidates: for needs_disambiguation, the list of candidate table paths."""


# A deliberately NAIVE Mode-C prompt (no grain/derived guards) — the diagnostic
# control arm, mirroring proof_c's 2x2. Used to test whether a model gets grain
# right ON ITS OWN, or only because the guard carries it. Same for both providers.
MODE_C_NAIVE = """You map a natural-language quantitative question to a structured \
resolution over the tidy CSV tables below: pick the table, the column to \
aggregate, the aggregation, and any filters. Use only the catalog. Return ONLY a \
JSON object matching the schema.

{catalog_corpus}
"""


# --------------------------------------------------------------------------- #
# Mode A reasoner — Gemini-adapted system instruction (same 6 rules as SYSTEM_PROMPT)
# --------------------------------------------------------------------------- #
MODE_A_GEMINI = """You are the Mode-A reasoner for WorldFish's shared knowledge \
graph. You are given a SUBGRAPH (a node list + a typed edge list) deterministically \
extracted around the question's entities, plus the QUESTION. Answer by reasoning \
ONLY over that subgraph. Obey every rule:

1. Use ONLY the nodes and edges listed in the SUBGRAPH. Do not use outside \
knowledge about these entities, and do not assume an edge that is not listed.
2. Every relationship you assert MUST correspond to a specific listed edge. Put \
each one in cited_edges exactly as listed (source, relation, target, confidence). \
If you cannot back a statement with a listed edge, do not make the statement.
3. NEVER assert a connection that is not an edge in the SUBGRAPH. Do not invent a \
path, a rationale, or an intermediate link the edge list does not contain.
4. An edge tagged INFERRED is the graph-builder's plausible GUESS, not a stated \
fact. When a relationship you assert rests on an INFERRED edge, flag it as \
inferred/uncertain in your prose AND list that edge in inferred_flags. Prefer \
EXTRACTED edges; discount INFERRED ones.
5. If the SUBGRAPH contains no edge (and no path) connecting two entities the \
question asks about, say plainly the graph records NO connection between them: \
set connected to false and leave cited_edges empty. Do NOT manufacture a \
relationship from a shared parent organization, a shared generic concept, or your \
own knowledge.
6. Describe each edge NO MORE STRONGLY than its relation and rationale warrant. \
Two initiatives that meet only through a GENERIC shared hub (both reference \
"WorldFish", "Fish nutrition", "Aquaculture") are NOT "sharing data" or \
"partnering" — say they connect only through a generic shared concept and decline \
to call it substantive. Reserve "shares", "partnership", "feeds into" for edges \
whose relation/rationale actually states that.

Return ONLY one JSON object matching the schema, with keys: answer (prose), \
connected (bool), cited_edges (list of {source, relation, target, confidence} \
copied verbatim from the SUBGRAPH), inferred_flags (the subset of cited_edges \
whose confidence is INFERRED). No prose outside the JSON."""


# --------------------------------------------------------------------------- #
# Mode B synthesis — already near-neutral; Gemini keeps it (light-touch fairness)
# --------------------------------------------------------------------------- #
MODE_B_GEMINI = (
    "You are a research assistant for WorldFish's shared knowledge base. Answer "
    "the question using ONLY the document passages provided. Cite every claim "
    "inline with [1], [2], … matching the passage numbers. If the passages do not "
    "contain enough information to answer, say so plainly — do not use outside "
    "knowledge and do not speculate. Be concise and complete; do not use markdown "
    "headers."
)


# --------------------------------------------------------------------------- #
# Ingestion — the curator's note-drafting core (Template A/B), model-agnostic bar
# --------------------------------------------------------------------------- #
INGESTION_BRIEF = """You are drafting a WDB companion CONTEXT NOTE for a newly added \
file, to the team's contribution protocol. Read the file content provided and \
draft the note. Hard rules:

- NEVER invent columns, findings, authors, or topics — every section must reflect \
the real content. If something is unknown, say so; do not guess.
- Refer to each initiative/system by ONE canonical proper name (e.g. "Peskas", \
never "the platform" / "the system" / "Peskas Monitoring System") — in the label \
AND in the prose — so the graph mints one node, not duplicates.
- Make each Summary/Key-concepts sentence self-contained (name its real-world \
subject explicitly), and state relationships explicitly ("produced by X", "builds \
on Y", "validates Z"), naming both sides.
- Do NOT describe the file's FORM — never write the table's wide/long shape, \
encoding, file type, or which script produced it. The note is about what the data \
MEANS, not its storage.
- "## Related files" is the wiring: list the real siblings the file relates to, \
and cross-link across initiatives where a real relationship exists.

{template}

Output ONLY the finished markdown note."""

TEMPLATE_A = """Use Template A (for a TABULAR file), with these sections:
# <descriptive H1 / node label>
## Summary — what the dataset is, who/what it is about, why it exists (prose).
## Columns — one bullet per column: `name`: prose meaning. (Leave the exact value \
domains / ranges to the deterministic enricher — write the MEANING, not invented \
distinct-value lists.)
## Grain — one or two sentences naming what ONE ROW is, in domain terms (e.g. \
"one row = one catch item of a trip"), and which higher-grain columns repeat and \
how to aggregate them (over the distinct key, not raw rows).
## Related files — real siblings + cross-initiative links."""

TEMPLATE_B = """Use Template B (for a PROSE document — PDF/report/doc), with these sections:
# <proper-name H1 / node label>
## Summary — what the document is and what it establishes (self-contained prose).
## Key concepts — the substantive ideas/methods/results it states, each naming \
its subject explicitly and stating relationships to other work.
## Related files — real siblings + cross-initiative links."""
