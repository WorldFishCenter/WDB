"""Correction #2 — the document-level passage↔graph join, both directions.

Reuses the proof's two proven cases (proof/FINDINGS.md Q1) as passing tests,
against the REAL committed graph.json — the join + companion-note normalization
are pure functions, so this is deterministic with no index and no model.
"""

from mode_b.corpus import walk_corpus
from mode_b.join import (
    associations,
    doc_stem,
    nodes_for_source,
    passages_for_node,
)

PESKAS_SOFTWAREX = "peskas/peskas_automated_analytics_softwarex_2025.pdf"


# --- the normalization rule (the one required piece of glue) ---------------- #

def test_doc_stem_collapses_companion_notes():
    base = "WIOMSA_harmonization_OCT2025"
    assert doc_stem(f"data_harmonization/{base}.pdf") == base
    assert doc_stem(f"data_harmonization/{base}_context.md") == base
    assert doc_stem("fasa/FICD_feed_ingredient_composition_database_dict.md") \
        == "FICD_feed_ingredient_composition_database"
    # _about.md hubs are living nodes, NOT snapshots of a doc -> left unchanged
    assert doc_stem("peskas/peskas_about.md") == "peskas_about"


# --- forward: passage -> source_file -> graph node(s) + associations -------- #

def test_forward_passage_joins_to_its_document_nodes(graph):
    nodes, links = graph
    matched = nodes_for_source(PESKAS_SOFTWAREX, nodes)
    ids = [n["id"] for n in matched]

    assert "peskas_validation_engine" in ids          # the on-topic node (proof)
    assert len(matched) >= 10                          # the document's node set
    # no cross-initiative bleed: every matched node is in the passage's initiative
    assert {n["source_file"].split("/")[0] for n in matched} == {"peskas"}

    edges = associations(ids, links)
    assert edges, "the passage must carry a non-empty associations payload"
    assert any(e.get("target") == "peskas_hub" for e in edges)


# --- reverse: note-anchored node -> normalized -> the document's passages --- #

def test_reverse_note_anchored_node_resolves_to_document(graph, wdb_root):
    nodes, _ = graph
    note_node = next(
        n for n in nodes
        if n.get("source_file", "").endswith("WIOMSA_harmonization_OCT2025_context.md")
    )
    # the node has no passage of its own; normalization reaches the underlying PDF
    indexed = walk_corpus(wdb_root)
    resolved = passages_for_node(note_node, indexed)
    assert "data_harmonization/WIOMSA_harmonization_OCT2025.pdf" in resolved


def test_reverse_returns_nothing_without_normalization(graph, wdb_root):
    """Sanity: the reverse direction works ONLY because of doc_stem (#2)."""
    nodes, _ = graph
    note_node = next(
        n for n in nodes
        if n.get("source_file", "").endswith("WIOMSA_harmonization_OCT2025_context.md")
    )
    indexed = walk_corpus(wdb_root)
    # naive basename match (no normalization) finds the PDF for the note? -> no
    naive = [sf for sf in indexed if sf.split("/")[-1] == note_node["source_file"].split("/")[-1]
             and sf.endswith(".pdf")]
    assert naive == []   # without normalization the PDF is unreachable from the note
