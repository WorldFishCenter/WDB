"""The pre-constructed backends the router dispatches the three real modes through.

:class:`Backends` bundles the heavy/stateful objects each mode needs (Mode A's reasoner +
graph, Mode B's retriever/synthesizer + graph, Mode C's resolver + catalog) so
:func:`wdb_router.composition.compose` stays pure dispatch + merge, and a caller can swap
Replay for Live without touching routing or composition.

The router calls each mode's **own** library entry point — it reimplements none of them.
In particular Mode A is now the **real** Mode A (``mode_a.answer_question`` over its
reasoner + graph), not a stand-in: its enumeration path is fully offline (no model), its
reasoning path is covered offline by the recorded fixtures, and an unrecorded reasoning
question downgrades deterministically to enumeration — Mode A's own honesty behaviour.

Live/Replay mirrors the modes' own split, so the suite runs offline and deterministically:

* :func:`replay_backends` — Mode A's ``ReplayReasoner`` over recorded proof answers (graph
  always real), Mode B's ``ReplayRetriever``/``ReplaySynthesizer`` over recorded passages,
  Mode C's ``ReplayResolver`` over recorded resolutions. No model, no network.
* :func:`live_backends` — Mode A's ``LiveReasoner`` (pinned Opus 4.8), Mode B's
  ``LiveRetriever`` (+ cross-encoder reranker) over the real Chroma index, Mode C's
  ``LiveResolver`` (pinned Opus 4.8). Without an API key the LLM-dependent arms fall back to
  Replay (so the off-topic-refusal arm, which refuses *before* any model call, runs key-free).
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from wdb_paths import KB_ROOT

# Kept as the public name the API and cost_sim already import; it is the KB root, which is
# what every backend actually needs (corpus walk, catalog glob, graph load).
WDB_ROOT = str(KB_ROOT)


@dataclass
class Backends:
    """Everything the router needs to call the three real modes, pre-constructed."""

    # Mode A — graph relationships / enumeration
    a_reasoner: object         # mode_a.reasoner.Reasoner (Live or Replay)
    a_graph: object            # mode_a.extract.Graph
    # Mode B — passage retrieval + cited synthesis
    nodes: list
    links: list
    b_retriever: object        # mode_b.retrieve.Retriever
    b_synth: object            # mode_b.synth.Synthesizer
    known_initiatives: set
    # Mode C — structured query
    catalog: object            # mode_c.catalog.Catalog
    c_resolver: object         # mode_c.resolver.Resolver


def _known_initiatives(root: str) -> set:
    from mode_b.corpus import walk_corpus

    return {f.split("/")[0] for f in walk_corpus(root) if "/" in f}


def replay_backends(root: str = WDB_ROOT,
                    recorded_passages: dict | None = None,
                    recorded_synthesis: dict | None = None,
                    recorded_resolutions: dict | None = None,
                    recorded_reasoning: dict | None = None) -> Backends:
    """Deterministic, offline backends (the suite's + CLI's default).

    The recorded dicts default to each mode's own proof fixtures ∪ the router's blended-demo
    entries, so the CLI's default path answers every mode's proof question *and* the blended
    demo. Tests pass their own dicts to isolate a case.
    """
    from mode_a import extract as a_extract
    from mode_a.fixtures import RECORDED as A_RECORDED
    from mode_a.reasoner import ReplayReasoner
    from mode_b.pipeline import load_graph_default
    from mode_b.retrieve import ReplayRetriever
    from mode_b.synth import ReplaySynthesizer
    from mode_c.catalog import load_catalog
    from mode_c.resolver import ReplayResolver

    from .fixtures import ALL_PASSAGES, ALL_RESOLUTIONS, ALL_SYNTHESIS

    nodes, links = load_graph_default()
    return Backends(
        a_reasoner=ReplayReasoner(recorded_reasoning or A_RECORDED),
        a_graph=a_extract.get_graph(),
        nodes=nodes,
        links=links,
        b_retriever=ReplayRetriever(recorded_passages or ALL_PASSAGES),
        b_synth=ReplaySynthesizer(recorded_synthesis or ALL_SYNTHESIS),
        known_initiatives=_known_initiatives(root),
        catalog=load_catalog(root),
        c_resolver=ReplayResolver(recorded_resolutions or ALL_RESOLUTIONS),
    )


def live_backends(root: str = WDB_ROOT, *, use_reranker: bool = True,
                  index_dir: str | None = None) -> Backends:
    """Real backends — Mode A's Opus 4.8 reasoner, Mode B's Chroma + reranker, Mode C's
    Opus 4.8 resolver.

    The LLM-dependent arms (Mode A reasoning, Mode B synthesis, Mode C resolution) need
    ``ANTHROPIC_API_KEY``; without it they fall back to Replay so the model-free paths still
    run. Mode A's enumeration path needs no model either way; the off-topic refusal arm
    (Mode B) never reaches synthesis — the gate refuses first — so it runs key-free, which is
    exactly the point.
    """
    from mode_a import extract as a_extract
    from mode_a.fixtures import RECORDED as A_RECORDED
    from mode_a.reasoner import LiveReasoner, ReplayReasoner
    from mode_b.index import DEFAULT_INDEX_DIR, open_collection
    from mode_b.pipeline import load_graph_default
    from mode_b.retrieve import LiveRetriever
    from mode_c.catalog import load_catalog
    from mode_c.resolver import LiveResolver, ReplayResolver

    nodes, links = load_graph_default()
    collection = open_collection(index_dir or DEFAULT_INDEX_DIR)
    b_retriever = LiveRetriever(collection, use_reranker=use_reranker)

    if os.environ.get("ANTHROPIC_API_KEY"):
        from mode_b.synth import LiveSynthesizer

        a_reasoner = LiveReasoner()
        b_synth = LiveSynthesizer()
        c_resolver = LiveResolver(load_catalog(root))
    else:
        from mode_b.synth import ReplaySynthesizer

        # Mode A enumeration still works; recorded reasoning replays; unrecorded reasoning
        # downgrades cleanly (never fabricates). Mode B/C raise/refuse only if reached.
        a_reasoner = ReplayReasoner(A_RECORDED)
        b_synth = ReplaySynthesizer({})       # raises if synthesis is actually reached
        c_resolver = ReplayResolver({})       # refuses unrecorded questions cleanly

    return Backends(
        a_reasoner=a_reasoner,
        a_graph=a_extract.get_graph(),
        nodes=nodes,
        links=links,
        b_retriever=b_retriever,
        b_synth=b_synth,
        known_initiatives=_known_initiatives(root),
        catalog=load_catalog(root),
        c_resolver=c_resolver,
    )
