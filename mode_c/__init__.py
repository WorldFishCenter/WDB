"""Mode C — structured query over WDB's tidy CSVs (quantitative/computed answers).

A standalone, tested module: given a question it resolves to a table/columns/
grain/aggregation (or refuses), gates on the vetted band, executes precisely in
DuckDB, and returns the answer-contract shape (a Claim whose citation is the SQL
plus its result rows) or a clean refusal. Not a router, serving layer, or UI —
the eventual router will call :func:`answer_question`.
"""

from .catalog import Catalog, load_catalog
from .contract import Answer, Citation, Claim, Figure
from .gate import GateResult, vetted_band
from .model import RESOLVER_MODEL
from .pipeline import answer_question
from .resolution import (
    CannotResolve,
    Filter,
    NeedsDisambiguation,
    Op,
    Outcome,
    Resolution,
)
from .resolver import LiveResolver, ReplayResolver, build_resolver_prompt

__all__ = [
    "Catalog",
    "load_catalog",
    "Answer",
    "Claim",
    "Citation",
    "Figure",
    "GateResult",
    "vetted_band",
    "answer_question",
    "Resolution",
    "Filter",
    "Op",
    "CannotResolve",
    "NeedsDisambiguation",
    "Outcome",
    "LiveResolver",
    "ReplayResolver",
    "build_resolver_prompt",
    "RESOLVER_MODEL",
]
