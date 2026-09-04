"""The §6 answer contract — one module, for the three modes, the router and the API.

Import the shape from here, never re-declare it. ``mode_a`` / ``mode_b`` / ``mode_c`` alias the
citation shape they produce (``Citation = CitationA`` etc.) so their own public names are
unchanged; ``wdb_router`` composes fragments with :func:`merge`; ``wdb_api`` serializes the
result. See :mod:`wdb_contract.contract` for why this module exists.
"""

from .contract import (
    Answer,
    Citation,
    CitationA,
    CitationB,
    CitationC,
    Claim,
    ClaimWithoutCitation,
    Figure,
    Unanswered,
    UnansweredCode,
    Verdict,
    add_associations,
    merge,
    refusal,
)
from .render import (
    association_lines,
    citation_lines,
    claim_lines,
    figure_lines,
    unanswered_lines,
)

__all__ = [
    "Answer",
    "Citation",
    "CitationA",
    "CitationB",
    "CitationC",
    "Claim",
    "ClaimWithoutCitation",
    "Figure",
    "Unanswered",
    "UnansweredCode",
    "Verdict",
    "add_associations",
    "merge",
    "refusal",
    "association_lines",
    "citation_lines",
    "claim_lines",
    "figure_lines",
    "unanswered_lines",
]
