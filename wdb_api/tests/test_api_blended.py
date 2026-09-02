"""A blended question composes A+B+C into one JSON response, every claim traceable.

The blended question fans out to all three modes; the API must compose them into one
serialized answer with every mode's native citation preserved, and must surface
``unanswered`` for a part no mode could ground — never back-filling it.
"""

from wdb_router.fixtures import BLENDED, GROUPED


def test_blended_composes_all_three_modes(client):
    data = client.post("/answer", json={"question": BLENDED}).json()
    assert set(data["modes_grounded"]) == {"A", "B", "C"}      # all three contribute
    assert {c["mode"] for c in data["claims"]} == {"A", "B", "C"}
    # §6 r1: every claim is traceable — names its mode and ≥1 sourced citation
    for c in data["claims"]:
        assert c["mode"] in {"A", "B", "C"}
        assert c["citations"]
        for cit in c["citations"]:
            assert cit["source_file"]


def test_blended_keeps_each_modes_native_citation_artifact(client):
    # the API does not flatten the modes' citations: A = graph edge, B = quote + nodes,
    # C = SQL + result rows — each retained intact through serialization.
    data = client.post("/answer", json={"question": BLENDED}).json()
    by_mode = {}
    for c in data["claims"]:
        by_mode.setdefault(c["mode"], c)
    assert by_mode["A"]["citations"][0]["locator"]            # graph edge triple
    assert by_mode["B"]["citations"][0]["quote"]              # verbatim span
    assert by_mode["C"]["citations"][0]["sql"]               # the query
    assert by_mode["C"]["citations"][0]["result"]            # ...and its rows


def test_blended_associations_are_merged_and_deduped(client):
    data = client.post("/answer", json={"question": BLENDED}).json()
    assert data["associations"]
    keys = [(e["source"], e.get("relation"), e["target"]) for e in data["associations"]]
    assert len(keys) == len(set(keys))                        # de-duplicated by triple


def test_grouped_question_carries_a_figure(client):
    data = client.post("/answer", json={"question": GROUPED}).json()
    assert data["figures"]                                    # the contract's figures payload
    fig = data["figures"][0]
    assert fig["spec"]["kind"] == "bar"
    assert fig["query"] and fig["result"]                    # figure ships with its SQL (§8)
    assert fig["result"][0]["gaul_1_name"] == "Lamu"         # top of the by-county ranking


def test_blend_with_an_ungrounded_mode_states_unanswered(client):
    # Routes to A (enumeration over "projects related to Kenya") + C ("average"); Mode C has
    # no recorded resolution for this and refuses, so its part must appear in `unanswered` —
    # never papered over by A's answer (§5 / §6 r4).
    data = client.post(
        "/answer",
        json={"question": "What is the average number of projects related to Kenya?"},
    ).json()
    assert "C" in data["modes_fired"]                         # C was routed to
    assert "C" not in data["modes_grounded"]                  # ...but grounded nothing
    assert data["unanswered"]                                 # and that is stated, not hidden
