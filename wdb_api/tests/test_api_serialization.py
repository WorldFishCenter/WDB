"""Serialization round-trip: the JSON carries every field the ``RouterAnswer`` holds.

This pins the core requirement directly on :func:`wdb_api.serialize.serialize_answer` against
the authoritative ``RouterAnswer`` the router produces — no field flattened, no figure /
association / citation / ``unanswered`` lost, and the whole thing JSON-native (``json.dumps``
must not raise). The blended question is used because it grounds A+B+C in one answer, so all
three native citation shapes are exercised at once.
"""

import json

from wdb_router import answer
from wdb_router.backends import replay_backends
from wdb_router.fixtures import BLENDED, GROUPED

from wdb_api.serialize import serialize_answer


def test_serialization_is_json_native_and_loses_no_top_level_field():
    ra = answer(BLENDED, backends=replay_backends())
    data = serialize_answer(ra)
    json.dumps(data)                                       # must serialize with no loss / crash

    assert data["question"] == ra.question
    assert data["answered"] == ra.answered
    assert data["modes_fired"] == ra.modes_fired
    assert data["modes_grounded"] == ra.modes_grounded
    assert len(data["routes"]) == len(ra.routes)
    assert len(data["associations"]) == len(ra.associations)
    assert len(data["figures"]) == len(ra.figures)
    assert data["unanswered"] == list(ra.unanswered)


def test_every_claim_and_citation_is_preserved():
    ra = answer(BLENDED, backends=replay_backends())
    data = serialize_answer(ra)

    assert len(data["claims"]) == len(ra.claims)
    for sc, claim in zip(data["claims"], ra.claims):
        assert sc["mode"] == claim.mode
        assert sc["text"] == claim.text
        assert len(sc["citations"]) == len(claim.citations)


def test_each_modes_native_citation_fields_survive():
    ra = answer(BLENDED, backends=replay_backends())
    data = serialize_answer(ra)
    by_mode = {}
    for sc in data["claims"]:
        by_mode.setdefault(sc["mode"], sc)
    # the discriminating fields of each mode's Citation are all present
    assert {"source_file", "note", "locator", "confidence"} <= by_mode["A"]["citations"][0].keys()
    assert {"source_file", "note", "location", "quote", "nodes"} <= by_mode["B"]["citations"][0].keys()
    assert {"source_file", "note", "sql", "result"} <= by_mode["C"]["citations"][0].keys()


def test_figures_are_preserved_field_for_field():
    ra = answer(GROUPED, backends=replay_backends())
    data = serialize_answer(ra)
    assert len(data["figures"]) == len(ra.figures)
    fig, sfig = ra.figures[0], data["figures"][0]
    assert sfig["spec"] == fig.spec
    assert sfig["query"] == fig.query
    assert sfig["result"] == fig.result


def test_associations_pass_through_as_edge_dicts():
    ra = answer(BLENDED, backends=replay_backends())
    data = serialize_answer(ra)
    for se, e in zip(data["associations"], ra.associations):
        assert se == e                                    # faithful copy, key-for-key
