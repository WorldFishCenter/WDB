"""Mode A — graph relationships / enumeration (the reasoning-strength, routed build).

A standalone, tested module: given a relational question it routes by shape
(``route.py``) — direct "what is X connected to" → cheap deterministic enumeration;
"how/why do X and Y relate" / "which initiatives share … with X" → LLM reasoning over a
deterministically-extracted subgraph, gated by a mechanical cite-check. Every reasoned
answer is verified against the real subgraph edges BEFORE it is surfaced; a failed check
downgrades to enumeration or "not available" (``pipeline.py``). Returns the §6 answer
contract (``contract.py``). Not a router, serving layer, or UI — the eventual router will
call :func:`answer_question`.
"""

from .citecheck import CiteVerdict, cite_check
from .contract import Answer, Citation, Claim, from_enumeration, from_reasoning, not_connected, refusal
from .extract import Graph, SubGraph, bridges, get_graph, neighborhood, relate
from .model import REASONER_MAX_TOKENS, REASONER_MODEL
from .pipeline import answer_question
from .reasoner import LiveReasoner, NoRecordedAnswer, Reasoner, ReplayReasoner
from .route import Route, find_entities, route

__all__ = [
    "answer_question",
    "Answer",
    "Claim",
    "Citation",
    "refusal",
    "not_connected",
    "from_enumeration",
    "from_reasoning",
    "cite_check",
    "CiteVerdict",
    "Graph",
    "SubGraph",
    "get_graph",
    "neighborhood",
    "relate",
    "bridges",
    "route",
    "Route",
    "find_entities",
    "LiveReasoner",
    "ReplayReasoner",
    "Reasoner",
    "NoRecordedAnswer",
    "REASONER_MODEL",
    "REASONER_MAX_TOKENS",
]
