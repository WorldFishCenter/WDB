"""The resolver — natural-language question → ``Resolution`` (or refusal).

The proof (``proof_c/RESOLVER_FINDINGS.md``) established that the cheapest Mode-C
resolver — an LLM given only the ``_dict.md`` value domains + one question — is
trustworthy **only with two prompt guards**. Those guards are mandatory and live
in :func:`build_resolver_prompt`:

1. **Grain reasoning** — "is one row the unit the question asks about? if not,
   reach the right unit (which key to aggregate over) before aggregating." This
   moved the proof from 1/3 to 5/5 on the grain trap.
2. **Derived-metric handling** — "if the metric isn't a stored column, give the
   formula and surface any denominator/assumption; never substitute a proxy."
   This turned the CPUE proxy into an honest, flagged derivation.

Two backends share one interface:

* :class:`LiveResolver` — calls the pinned model ``claude-opus-4-8`` (Opus 4.8)
  with the two-guard prompt and structured JSON output. This is the production
  resolver; it requires the ``anthropic`` SDK + an API key.
* :class:`ReplayResolver` — returns recorded resolutions (the ones the proof's
  Opus 4.8 produced). The deterministic, offline default the regression suite
  runs, so the gate/executor/contract pipeline is tested without the network.
"""

from __future__ import annotations

import json
from typing import Protocol

from .catalog import Catalog
from .model import RESOLVER_MODEL
from .resolution import (
    CannotResolve,
    Filter,
    NeedsDisambiguation,
    Op,
    Outcome,
    Resolution,
)

# The two mandatory guards — verbatim in intent. Unit-tested for presence so a
# future prompt edit cannot silently drop them.
GRAIN_GUARD = (
    "GRAIN: Is one table row the same unit the question asks about? If the row is "
    "finer than that unit (e.g. one row per catch item but the question is per "
    "trip), name the key to aggregate over (grain_key) and collapse to it BEFORE "
    "aggregating — never average a trip-level column over raw catch rows. Read each "
    "table's ## Grain line to decide."
)
DERIVED_GUARD = (
    "DERIVED METRICS: If the asked metric is not a stored column (e.g. CPUE), do "
    "NOT substitute a proxy column. Give the formula in derived_formula, list the "
    "columns it uses in derived_inputs, and surface the denominator/assumption you "
    "chose in assumptions (with the alternatives). Never relabel a stored column as "
    "the derived metric."
)


def build_resolver_prompt(catalog: Catalog) -> str:
    """The system prompt for the live resolver — carries BOTH guards + the catalog."""
    return f"""You map ONE natural-language quantitative question to a structured \
resolution over the WDB tidy CSV tables, or refuse. Use ONLY the catalog below; \
never invent a table, column, or value.

{GRAIN_GUARD}

{DERIVED_GUARD}

ROUTING: Pick the table only when a distinctive value in the question pins exactly \
one table (a place, a species, a scientific name, an enumerated gear+region). If a \
value is shared across sister tables and nothing else disambiguates, return \
needs_disambiguation. If the value or column is absent from every table, return \
cannot_resolve. Put the distinctive token you routed on in `pinned_by`.

Return a single JSON object matching the schema. For a concrete answer use \
outcome="resolve"; otherwise "cannot_resolve" or "needs_disambiguation".

{catalog.render_corpus()}
"""


# JSON schema for structured output (Opus 4.8 output_config.format).
RESOLUTION_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "outcome": {"type": "string", "enum": ["resolve", "cannot_resolve", "needs_disambiguation"]},
        "reason": {"type": "string"},
        "candidates": {"type": "array", "items": {"type": "string"}},
        "table": {"type": "string"},
        "aggregation": {"type": "string"},
        "pinned_by": {"type": "string"},
        "metric_column": {"type": ["string", "null"]},
        "derived_formula": {"type": ["string", "null"]},
        "derived_inputs": {"type": "array", "items": {"type": "string"}},
        "grain_key": {"type": ["string", "null"]},
        "group_by": {"type": ["string", "null"]},
        "metric_label": {"type": "string"},
        "round_digits": {"type": "integer"},
        "confidence": {"type": "number"},
        "assumptions": {"type": "array", "items": {"type": "string"}},
        "filters": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "column": {"type": "string"},
                    "op": {"type": "string", "enum": ["=", "contains"]},
                    "value": {"type": "string"},
                },
                "required": ["column", "op", "value"],
            },
        },
    },
    "required": ["outcome"],
}


class Resolver(Protocol):
    def resolve(self, question: str) -> Outcome: ...


def outcome_from_dict(d: dict) -> Outcome:
    """Build a typed outcome from the resolver's JSON object."""
    kind = d.get("outcome")
    if kind == "cannot_resolve":
        return CannotResolve(reason=d.get("reason", "data cannot answer this"))
    if kind == "needs_disambiguation":
        return NeedsDisambiguation(
            reason=d.get("reason", "ambiguous routing"),
            candidates=tuple(d.get("candidates", ())),
        )
    filters = tuple(
        Filter(column=f["column"], op=Op(f["op"]), value=f["value"])
        for f in d.get("filters", [])
    )
    return Resolution(
        table=d["table"],
        aggregation=d.get("aggregation", "AVG"),
        pinned_by=d.get("pinned_by", ""),
        metric_column=d.get("metric_column"),
        derived_formula=d.get("derived_formula"),
        derived_inputs=tuple(d.get("derived_inputs", ())),
        grain_key=d.get("grain_key"),
        filters=filters,
        group_by=d.get("group_by"),
        assumptions=tuple(d.get("assumptions", ())),
        round_digits=int(d.get("round_digits", 2)),
        confidence=float(d.get("confidence", 1.0)),
        metric_label=d.get("metric_label", "value"),
        notes=d.get("reason", ""),
    )


class LiveResolver:
    """Production resolver — pinned Opus 4.8 with the two-guard prompt.

    Requires ``pip install anthropic`` and ``ANTHROPIC_API_KEY``. Pinned to the
    exact model id (``mode_c/model.py``) for reproducibility, the same discipline
    as the graph build. Not exercised by the offline regression suite.
    """

    def __init__(self, catalog: Catalog, client=None, model: str = RESOLVER_MODEL):
        self.catalog = catalog
        self.model = model
        self.system = build_resolver_prompt(catalog)
        if client is None:
            import anthropic  # imported lazily so the offline path needs no SDK

            client = anthropic.Anthropic()
        self.client = client

    def resolve(self, question: str) -> Outcome:
        resp = self.client.messages.create(
            model=self.model,
            max_tokens=2000,
            system=self.system,
            messages=[{"role": "user", "content": question}],
            # structured output forces a valid JSON object; no temperature on Opus 4.8
            output_config={"format": {"type": "json_schema", "schema": RESOLUTION_SCHEMA}},
        )
        text = next(b.text for b in resp.content if b.type == "text")
        return outcome_from_dict(json.loads(text))


class ReplayResolver:
    """Offline resolver — returns recorded resolutions keyed by normalised question.

    The recorded resolutions are exactly what the proof's Opus 4.8 produced for
    the 9 questions; replaying them lets the gate/executor/contract pipeline be
    tested deterministically, with real DuckDB computation over the real CSVs.
    """

    def __init__(self, recorded: dict[str, Outcome]):
        self.recorded = {self._norm(k): v for k, v in recorded.items()}

    @staticmethod
    def _norm(q: str) -> str:
        return " ".join(q.lower().split())

    def resolve(self, question: str) -> Outcome:
        key = self._norm(question)
        if key not in self.recorded:
            return CannotResolve(reason="no recorded resolution for this question (offline replay)")
        return self.recorded[key]
