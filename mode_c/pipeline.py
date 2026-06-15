"""The Mode-C pipeline: resolve → gate → execute → answer-contract (or refuse).

This is the standalone module the eventual router/UI will call. It does not
route across modes, serve, or render — it answers vetted-band quantitative
questions precisely and refuses cleanly outside the band.
"""

from __future__ import annotations

from . import contract
from .catalog import Catalog
from .contract import Answer
from .executor import ExecutionError, execute
from .gate import vetted_band
from .resolution import CannotResolve, NeedsDisambiguation, Resolution
from .resolver import Resolver


def answer_question(question: str, resolver: Resolver, catalog: Catalog) -> Answer:
    outcome = resolver.resolve(question)

    if isinstance(outcome, CannotResolve):
        return contract.refusal(question, outcome.reason)
    if isinstance(outcome, NeedsDisambiguation):
        return contract.disambiguation(question, outcome)

    assert isinstance(outcome, Resolution)
    verdict = vetted_band(outcome, catalog)
    if not verdict.ok:
        return contract.refusal(question, f"outside the vetted band: {verdict.reason}")

    try:
        result = execute(outcome, catalog)
    except ExecutionError as e:
        # refuse-by-construction (e.g. a column that fails to bind)
        return contract.refusal(question, f"not available: {e}")
    if result.empty:
        return contract.refusal(question, "not available (the query matched 0 rows)")

    return contract.assemble(question, outcome, result, catalog)
