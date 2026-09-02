"""Each mode's proven case answers through the API, carrying that mode's native citation.

These reuse the router's own Replay-backed proof questions — a Kenya enumeration (Mode A over
the real committed graph), "average total catch per trip in Kwale" (Mode C, recorded
resolution), and a covered synthesis question (Mode B, recorded passage + synthesis) — and
assert the serialized JSON keeps each mode's distinct citation artifact intact.
"""

from mode_b.fixtures.recorded import Q_COVERED
from mode_c.fixtures.resolutions import Q4


def test_enumeration_question_grounds_in_mode_A(client):
    data = client.post("/answer", json={"question": "What projects operate in Kenya?"}).json()
    assert data["modes_grounded"] == ["A"]
    assert data["claims"] and all(c["mode"] == "A" for c in data["claims"])
    texts = " | ".join(c["text"] for c in data["claims"])
    assert "Peskas" in texts and "FASA" in texts            # real Kenya-touching projects
    # Mode A's native citation artifact: a graph edge triple + its confidence tag
    cit = data["claims"][0]["citations"][0]
    assert cit["locator"] and cit["confidence"] in {"EXTRACTED", "INFERRED"}
    assert data["associations"]                             # the typed-edge payload (§6)


def test_quantitative_question_grounds_in_mode_C(client):
    data = client.post("/answer", json={"question": Q4}).json()   # "Average … per trip in Kwale?"
    assert data["modes_grounded"] == ["C"]
    claim = data["claims"][0]
    assert claim["mode"] == "C"
    assert "31.88" in claim["text"]                         # the proof's trip-grain answer
    cit = claim["citations"][0]
    assert cit["sql"].strip().upper().startswith("WITH")    # the citation IS the SQL (§6 r3)
    assert cit["result"] == [{"n": 50422, "avg_total_catch_kg_per_trip": 31.88}]


def test_synthesis_question_grounds_in_mode_B(client):
    data = client.post("/answer", json={"question": Q_COVERED}).json()
    assert data["modes_grounded"] == ["B"]
    claim = data["claims"][0]
    assert claim["mode"] == "B"
    cit = claim["citations"][0]
    assert cit["quote"]                                     # verbatim passage span
    assert cit["nodes"]                                     # joined graph node(s) at doc grain
    assert data["associations"]


def test_response_status_is_200_for_a_grounded_question(client):
    r = client.post("/answer", json={"question": Q4})
    assert r.status_code == 200
    assert r.json()["answered"] is True
