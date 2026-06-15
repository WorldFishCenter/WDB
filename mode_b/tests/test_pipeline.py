"""End-to-end pipeline — retrieve → gate → synthesize → join → contract.

Deterministic via the ReplayRetriever + ReplaySynthesizer (the Mode-C Live/Replay
discipline): a covered question yields a cited answer whose citation carries the
matching graph node(s) and whose answer carries the associations payload; an
uncovered question is refused by the gate rather than synthesised.
"""

from mode_b import answer_question
from mode_b.fixtures import Q_COVERED, Q_UNCOVERED, RECORDED_PASSAGES, RECORDED_SYNTHESIS
from mode_b.retrieve import ReplayRetriever
from mode_b.synth import ReplaySynthesizer


def _wire():
    return ReplayRetriever(RECORDED_PASSAGES), ReplaySynthesizer(RECORDED_SYNTHESIS)


def test_covered_question_answers_with_cited_passage_and_associations(graph, wdb_root):
    nodes, links = graph
    retriever, synth = _wire()
    answer = answer_question(Q_COVERED, retriever, synth, nodes, links, root=wdb_root)

    assert answer.answered
    claim = answer.claims[0]
    assert claim.mode == "B"
    assert claim.citations[0].nodes  # joined to graph node(s) at document grain
    assert "peskas_validation_engine" in claim.citations[0].nodes
    assert answer.associations       # the dual payload (passage + associations)


def test_uncovered_question_is_refused_not_synthesised(graph, wdb_root):
    nodes, links = graph
    retriever, synth = _wire()
    answer = answer_question(Q_UNCOVERED, retriever, synth, nodes, links, root=wdb_root)

    assert not answer.answered
    assert answer.claims == []
    assert answer.unanswered and Q_UNCOVERED in answer.unanswered[0]
    assert "not available" in answer.unanswered[0]
