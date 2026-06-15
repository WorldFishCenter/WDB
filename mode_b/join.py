"""The passage ↔ graph document-level join (both directions) — carry-over #2.

Vendored from the proven ``proof/join.py``. A retrieved passage joins to its
graph associations at **document grain** on the ``source_file`` key both systems
store; the join is exact and both-way *because of* one deterministic step:

**Companion-note normalization.** 91 of 172 graph node ``source_file`` values are
``.md`` companion notes, not the source document. :func:`doc_stem` collapses
``X_context.md`` / ``X_dict.md`` → ``X`` so a passage from ``X.pdf`` and a node
authored against ``X_context.md`` meet on the same key. Applied in BOTH
directions — without it the reverse direction (node → passages) returns nothing
for any note-anchored node, and the forward direction misses note-authored nodes.
``_about.md`` hubs are *living* canonical nodes (not a snapshot of an underlying
doc), so they are intentionally left as themselves.

Everything here is a pure function over ``graph.json`` + a ``source_file`` — so
the proof's two proven join cases are provable by a deterministic test, with no
index and no model.
"""

from __future__ import annotations

import json
from pathlib import Path


def doc_stem(source_file: str) -> str:
    """Normalize a ``source_file`` basename to its underlying-document key.

    ``WIOMSA_harmonization_OCT2025.pdf``        -> ``WIOMSA_harmonization_OCT2025``
    ``WIOMSA_harmonization_OCT2025_context.md`` -> ``WIOMSA_harmonization_OCT2025``
    ``FICD_..._database_dict.md``               -> ``FICD_..._database``
    ``peskas_about.md``                         -> ``peskas_about``  (hub, unchanged)
    """
    stem = Path(source_file).stem
    for suffix in ("_context", "_dict"):
        if stem.endswith(suffix):
            return stem[: -len(suffix)]
    return stem


def load_graph(graph_path: str) -> tuple[list[dict], list[dict]]:
    g = json.loads(Path(graph_path).read_text(encoding="utf-8"))
    return g["nodes"], g["links"]


def nodes_for_source(source_file: str, nodes: list[dict]) -> list[dict]:
    """Forward: passage ``source_file`` → graph node(s) sharing its document stem."""
    stem = doc_stem(source_file)
    return [n for n in nodes if n.get("source_file") and doc_stem(n["source_file"]) == stem]


def associations(node_ids, links: list[dict]) -> list[dict]:
    """The edges (Mode-A associations payload) touching any of ``node_ids``."""
    ids = set(node_ids)
    return [e for e in links if e.get("source") in ids or e.get("target") in ids]


def passages_for_node(node: dict, indexed_source_files) -> list[str]:
    """Reverse: a node → the indexed ``source_file``(s) of its underlying document.

    ``indexed_source_files`` is the set of ``source_file`` values in the passage
    index. Returns those whose document stem matches the (normalized) node — the
    step that lets a note-anchored node reach the PDF's passages.
    """
    nstem = doc_stem(node.get("source_file", ""))
    return [sf for sf in indexed_source_files if doc_stem(sf) == nstem]
