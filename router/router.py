"""The router — classify a question (§5), dispatch to one or more modes as
libraries, and merge their fragments into one §6 :class:`RouterAnswer`.

This is the whole point of the throwaway harness: it **reuses the modes as
libraries** (``mode_b.answer_question``, ``mode_c.answer_question``) and the
harness-grade Mode-A enumeration (``router.mode_a``), and assembles their results
without reimplementing any of them. A mode that returns nothing contributes its
part to ``unanswered`` — never back-filled by another mode (§5, §6 r4).

Live/Replay discipline mirrors the modes' own (so the suite runs offline,
deterministically):

* :func:`replay_backends` — Mode B's ``ReplayRetriever``/``ReplaySynthesizer`` over
  recorded passages, Mode C's ``ReplayResolver`` over recorded resolutions, Mode A
  over the real committed graph (always deterministic). No model, no network.
* :func:`live_backends` — Mode B's ``LiveRetriever`` (+ cross-encoder reranker) over
  the real Chroma index, Mode C's ``LiveResolver`` (pinned Opus 4.8). Used for the
  end-to-end reranker verification (the off-topic refusal arm).
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from . import mode_a
from .contract import Route, RouterAnswer, add_associations
from .intent import classify

WDB_ROOT = str(Path(__file__).resolve().parent.parent)


@dataclass
class Backends:
    """Everything the router needs to call the three modes, pre-constructed.

    Bundling the heavy/stateful objects (retriever, resolver, catalog, graph) here
    keeps :func:`answer` pure dispatch + merge, and lets a caller swap Replay for
    Live without touching routing.
    """

    nodes: list
    links: list
    catalog: object            # mode_c.catalog.Catalog
    b_retriever: object        # mode_b.retrieve.Retriever
    b_synth: object            # mode_b.synth.Synthesizer
    c_resolver: object         # mode_c.resolver.Resolver
    known_initiatives: set


def _known_initiatives(root: str) -> set:
    from mode_b.corpus import walk_corpus

    return {f.split("/")[0] for f in walk_corpus(root) if "/" in f}


def replay_backends(root: str = WDB_ROOT,
                    recorded_passages: dict | None = None,
                    recorded_synthesis: dict | None = None,
                    recorded_resolutions: dict | None = None) -> Backends:
    """Deterministic, offline backends (the suite's + CLI's default).

    The recorded dicts default to the harness's merged fixtures (each mode's own
    proof fixtures ∪ the router's blended-demo entries), so the CLI's default path
    answers every mode's proof question *and* the blended demo. Tests pass their
    own dicts to isolate a case.
    """
    from mode_b.pipeline import load_graph_default
    from mode_b.retrieve import ReplayRetriever
    from mode_b.synth import ReplaySynthesizer
    from mode_c.catalog import load_catalog
    from mode_c.resolver import ReplayResolver

    from .fixtures import ALL_PASSAGES, ALL_RESOLUTIONS, ALL_SYNTHESIS

    nodes, links = load_graph_default()
    return Backends(
        nodes=nodes,
        links=links,
        catalog=load_catalog(root),
        b_retriever=ReplayRetriever(recorded_passages or ALL_PASSAGES),
        b_synth=ReplaySynthesizer(recorded_synthesis or ALL_SYNTHESIS),
        c_resolver=ReplayResolver(recorded_resolutions or ALL_RESOLUTIONS),
        known_initiatives=_known_initiatives(root),
    )


def live_backends(root: str = WDB_ROOT, *, use_reranker: bool = True,
                  index_dir: str | None = None) -> Backends:
    """Real backends — Chroma + reranker (Mode B) and the Opus 4.8 resolver (Mode C).

    Mode-B synthesis needs ``ANTHROPIC_API_KEY``; without it we install a synth that
    errors only *if reached*. The off-topic refusal arm never reaches synthesis
    (the gate refuses first), so it runs key-free — which is exactly the point.
    """
    from mode_b.index import DEFAULT_INDEX_DIR, open_collection
    from mode_b.pipeline import load_graph_default
    from mode_b.retrieve import LiveRetriever
    from mode_c.catalog import load_catalog
    from mode_c.resolver import LiveResolver

    nodes, links = load_graph_default()
    collection = open_collection(index_dir or DEFAULT_INDEX_DIR)
    b_retriever = LiveRetriever(collection, use_reranker=use_reranker)

    if os.environ.get("ANTHROPIC_API_KEY"):
        from mode_b.synth import LiveSynthesizer

        b_synth = LiveSynthesizer()
        c_resolver = LiveResolver(load_catalog(root))
    else:
        from mode_b.synth import ReplaySynthesizer
        from mode_c.resolver import ReplayResolver

        b_synth = ReplaySynthesizer({})       # raises if synthesis is actually reached
        c_resolver = ReplayResolver({})       # refuses unrecorded questions cleanly

    return Backends(
        nodes=nodes,
        links=links,
        catalog=load_catalog(root),
        b_retriever=b_retriever,
        b_synth=b_synth,
        c_resolver=c_resolver,
        known_initiatives=_known_initiatives(root),
    )


def _run_mode_b(question: str, b: Backends):
    from mode_b.pipeline import answer_question

    return answer_question(question, b.b_retriever, b.b_synth, b.nodes, b.links,
                           known_initiatives=b.known_initiatives)


def _run_mode_c(question: str, b: Backends):
    from mode_c.pipeline import answer_question

    return answer_question(question, b.c_resolver, b.catalog)


def answer(question: str, backends: Backends | None = None,
           routes: list[Route] | None = None) -> RouterAnswer:
    """Route, dispatch, and compose — the one entry point the CLI and tests call."""
    backends = backends or replay_backends()
    routes = routes if routes is not None else classify(question)
    ra = RouterAnswer(question=question, routes=routes)

    fired = {r.mode for r in routes}

    # Dispatch in a fixed A→B→C order for deterministic output, regardless of the
    # order signals fired in. Each mode already returns the §6 shape and enforces
    # "no claim without a citation"; merging is concatenate + de-dup.
    if "A" in fired:
        a = mode_a.enumerate_relationships(question, backends.nodes, backends.links)
        ra.claims.extend(a.claims)
        add_associations(ra, a.associations)
        ra.unanswered.extend(a.unanswered)

    if "B" in fired:
        b = _run_mode_b(question, backends)
        ra.claims.extend(b.claims)
        add_associations(ra, b.associations)
        ra.unanswered.extend(b.unanswered)

    if "C" in fired:
        c = _run_mode_c(question, backends)
        ra.claims.extend(c.claims)
        ra.figures.extend(c.figures)
        ra.unanswered.extend(c.unanswered)

    return ra
