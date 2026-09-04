"""Mode B — passage retrieval + cited synthesis over WDB prose & companion notes.

A standalone, tested module: ingest WDB's prose corpus into a Chroma index
(prose + ``.md`` notes only — raw CSVs excluded), retrieve + rerank passages for
a question, synthesize a cited answer, and join each passage to its graph
associations at document grain — returning the §6 answer-contract shape (a Claim
whose citation is the passage span + verbatim quote + the matching graph node(s))
or a clean "not available." Not a router, serving layer, or UI — the eventual
router will call :func:`answer_question`.
"""

from .contract import Answer, Citation, Claim, refusal
from .embed import Embedder, EmbedModelMismatch, verify_collection_model
from .gate import GateResult, refuse_when_thin
from .index import build_index, open_collection
from .join import associations, doc_stem, load_graph, nodes_for_source, passages_for_node
from .model import EMBED_MODEL, RERANK_MODEL, SYNTH_MODEL
from .pipeline import answer_question, load_graph_default
from .rerank import CrossEncoderReranker, NullReranker, Reranker, load_reranker
from .retrieve import LiveRetriever, Passage, ReplayRetriever, Retriever
from .synth import LiveSynthesizer, ReplaySynthesizer, Synthesizer

__all__ = [
    "Answer",
    "Reranker",
    "CrossEncoderReranker",
    "NullReranker",
    "load_reranker",
    "Claim",
    "Citation",
    "refusal",
    "Embedder",
    "EmbedModelMismatch",
    "verify_collection_model",
    "GateResult",
    "refuse_when_thin",
    "build_index",
    "open_collection",
    "doc_stem",
    "load_graph",
    "nodes_for_source",
    "passages_for_node",
    "associations",
    "answer_question",
    "load_graph_default",
    "Passage",
    "Retriever",
    "LiveRetriever",
    "ReplayRetriever",
    "Synthesizer",
    "LiveSynthesizer",
    "ReplaySynthesizer",
    "EMBED_MODEL",
    "RERANK_MODEL",
    "SYNTH_MODEL",
]
