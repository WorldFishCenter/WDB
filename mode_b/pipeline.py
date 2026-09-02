"""The Mode-B pipeline: retrieve → refuse-when-thin → synthesize → join → contract.

This is the standalone module the eventual router/UI will call. It does not route
across modes, serve, or render — it retrieves and synthesizes a cited answer from
WDB prose + companion notes, joins each citation to its graph associations at
document grain, and refuses cleanly when retrieval is thin (never synthesising
from nothing).
"""

from __future__ import annotations

import os
from pathlib import Path

from . import contract
from .contract import Answer
from .gate import refuse_when_thin
from .join import load_graph
from .model import RERANK_TOP_K
from .retrieve import Retriever
from .synth import Synthesizer

from wdb_paths import GRAPH_JSON, KB_ROOT

# The corpus and the graph both live in the knowledge base, not the app repo.
DEFAULT_ROOT = str(KB_ROOT)
DEFAULT_GRAPH = str(GRAPH_JSON)


def answer_question(question: str, retriever: Retriever, synthesizer: Synthesizer,
                    nodes: list[dict], links: list[dict],
                    root: str = DEFAULT_ROOT, k: int = RERANK_TOP_K,
                    known_initiatives=None) -> Answer:
    """Answer one synthesis question, or return a clean refusal.

    ``known_initiatives`` (optional) enables the gate's coverage arm (gate.py):
    pass the corpus's initiative set so a question naming one must retrieve a
    passage from it.
    """
    passages = retriever.retrieve(question, k)

    verdict = refuse_when_thin(question, passages, known_initiatives=known_initiatives)
    if not verdict.ok:
        return contract.refusal(question, f"not available: {verdict.reason}")

    synthesis_text = synthesizer.synthesize(question, passages)
    return contract.assemble(question, passages, synthesis_text, nodes, links, root)


def load_graph_default(graph_path: str = DEFAULT_GRAPH) -> tuple[list[dict], list[dict]]:
    return load_graph(graph_path)
