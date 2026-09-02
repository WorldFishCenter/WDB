"""CLI for Mode B:  python -m mode_b "How does Peskas validate catch survey data?"

  python -m mode_b --ingest                 build/refresh the passage index
  python -m mode_b --list-corpus            show what is (and isn't) indexed
  python -m mode_b "question"               retrieve → join → synthesize (cited)

Synthesis uses the pinned Sonnet 4.6 model and needs the ``anthropic`` SDK +
ANTHROPIC_API_KEY. Without a key the CLI still runs retrieval + the document-grain
graph join and prints the cited passages and their associations (synthesis
skipped) — so the proven half (passages + associations) is visible offline.
"""

from __future__ import annotations

import argparse
import json
import os
import sys

from . import join
from .contract import Answer
from .index import DEFAULT_INDEX_DIR, build_index, open_collection
from .model import RERANK_TOP_K, SYNTH_MODEL
from .pipeline import DEFAULT_ROOT, answer_question, load_graph_default
from .retrieve import LiveRetriever


def _render_answer(answer: Answer) -> str:
    out: list[str] = []
    for claim in answer.claims:
        out.append(f"CLAIM [{claim.mode}]: {claim.text}")
        for k, cit in enumerate(claim.citations, 1):
            out.append(f"  [{k}] source : {cit.source_file}  ({cit.location})")
            if cit.note:
                out.append(f"      note   : {cit.note}")
            out.append(f"      quote  : {cit.quote[:240].replace(chr(10), ' ')}…")
            out.append(f"      nodes  : {', '.join(cit.nodes) or '—'}")
    if answer.associations:
        out.append(f"\nASSOCIATIONS ({len(answer.associations)} edge(s) touch the cited nodes):")
        for e in answer.associations[:8]:
            out.append(f"  {e.get('source')}  --{e.get('relation', '?')}-->  {e.get('target')}")
    for u in answer.unanswered:
        out.append(f"NOT AVAILABLE: {u}")
    return "\n".join(out) if out else "(empty answer)"


def _render_evidence(question, passages, nodes, links, root) -> str:
    """No-key fallback: cited passages + their graph associations, no synthesis."""
    out = [f"(synthesis skipped — no ANTHROPIC_API_KEY; showing retrieved passages + associations)\n"]
    node_ids: set[str] = set()
    for i, p in enumerate(passages, 1):
        matched = join.nodes_for_source(p.source_file, nodes)
        ids = [n["id"] for n in matched]
        node_ids.update(ids)
        out.append(f"[{i}] {p.source_file}  ({p.location})  {p.ranking_kind()}={p.ranking_score():.2f}")
        out.append(f"     quote : {p.text[:220].replace(chr(10), ' ').strip()}…")
        out.append(f"     nodes : {', '.join(ids) or '—'}")
    edges = join.associations(node_ids, links)
    out.append(f"\nASSOCIATIONS ({len(edges)} edge(s) touch the cited nodes):")
    for e in edges[:8]:
        out.append(f"  {e.get('source')}  --{e.get('relation', '?')}-->  {e.get('target')}")
    return "\n".join(out)


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="mode_b", description="Mode B — passage retrieval + cited synthesis")
    p.add_argument("question", nargs="?", help="the synthesis question to answer")
    p.add_argument("--ingest", action="store_true", help="build/refresh the passage index, then exit")
    p.add_argument("--list-corpus", action="store_true", help="list the files that are indexable")
    p.add_argument("--index-dir", default=DEFAULT_INDEX_DIR, help="where the Chroma index lives")
    p.add_argument("--root", default=DEFAULT_ROOT, help="WDB repo root")
    p.add_argument("--k", type=int, default=RERANK_TOP_K, help="passages to synthesise")
    p.add_argument("--no-rerank", action="store_true", help="skip the cross-encoder reranker")
    args = p.parse_args(argv)

    if args.list_corpus:
        from .corpus import walk_corpus

        files = walk_corpus(args.root)
        for f in files:
            print(f)
        print(f"\n{len(files)} indexable file(s); "
              f"{sum(1 for f in files if f.endswith('.csv'))} CSV (must be 0); "
              f"{sum(1 for f in files if f.endswith('.md'))} companion note(s)")
        return 0

    if args.ingest:
        build_index(args.root, index_dir=args.index_dir)
        return 0

    if not args.question:
        p.error("a question is required (or use --ingest / --list-corpus)")

    collection = open_collection(args.index_dir)
    retriever = LiveRetriever(collection, use_reranker=not args.no_rerank)
    nodes, links = load_graph_default()

    from .corpus import walk_corpus

    known = {f.split("/")[0] for f in walk_corpus(args.root) if "/" in f}

    if os.environ.get("ANTHROPIC_API_KEY"):
        from .synth import LiveSynthesizer

        answer = answer_question(args.question, retriever, LiveSynthesizer(),
                                 nodes, links, root=args.root, k=args.k,
                                 known_initiatives=known)
        print(_render_answer(answer))
        return 0 if answer.answered else 1

    # no key: show retrieval + join evidence (gate still applies)
    from .gate import refuse_when_thin

    passages = retriever.retrieve(args.question, args.k)
    verdict = refuse_when_thin(args.question, passages, known_initiatives=known)
    if not verdict.ok:
        print(f"NOT AVAILABLE: {args.question} — not available: {verdict.reason}")
        return 1
    print(_render_evidence(args.question, passages, nodes, links, args.root))
    print(f"\n(synthesis model when keyed: {SYNTH_MODEL})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
