"""The verdict and the typed refusal survive serialization — and the old wire shape is intact.

The read UI decided "full refusal" by inferring from three empty lists, so Mode A's verified
negative ("we checked the graph and it records no connection" — a correct answer) rendered as
"the knowledge base doesn't cover this". ``verdict`` is what lets it tell them apart.

These are additive keys: every key the UI reads today keeps its exact meaning, which is what
lets the five committed ``read-ui/fixtures/*.json`` keep working untouched.
"""

from wdb_contract import CitationA, Claim, Unanswered, UnansweredCode, Verdict
from wdb_router.contract import Route, RouterAnswer
from wdb_api.serialize import serialize_answer

Q = "How does Peskas relate to the FASA feed database?"


def _verified_negative() -> RouterAnswer:
    ra = RouterAnswer(question=Q, routes=[Route("A", "signal: relate")])
    ra.negative = True
    ra.unanswered.append(Unanswered(
        part=Q, mode="A", code=UnansweredCode.NOT_CONNECTED,
        detail="the graph records no connection between Peskas and FICD "
               "(no direct edge, no ≤2-hop path).",
    ))
    return ra


def test_verified_negative_serializes_as_answered():
    data = serialize_answer(_verified_negative())

    assert data["verdict"] == Verdict.VERIFIED_NEGATIVE.value
    assert data["answered"] is True            # a verified "no" is a correct answer
    assert data["claims"] == [] and data["figures"] == []
    assert data["unanswered_detail"][0]["code"] == "NOT_CONNECTED"


def test_ungrounded_refusal_is_distinguishable_from_a_verified_negative():
    ra = RouterAnswer(question=Q, routes=[Route("B", "signal: impact")])
    ra.unanswered.append(Unanswered(
        part=Q, mode="B", code=UnansweredCode.THIN_RETRIEVAL,
        detail="not available: retrieval too thin to answer",
    ))
    data = serialize_answer(ra)

    assert data["verdict"] == Verdict.UNGROUNDED.value
    assert data["answered"] is False
    # the two cases differ ONLY in `verdict` — the empty lists are identical, which is exactly
    # why the UI could not tell them apart before.
    neg = serialize_answer(_verified_negative())
    assert (data["claims"], data["figures"]) == (neg["claims"], neg["figures"])
    assert data["verdict"] != neg["verdict"]


def test_disambiguation_candidates_reach_the_wire():
    ra = RouterAnswer(question="Average catch for Gill Net trips?",
                      routes=[Route("C", "signal: average")])
    ra.unanswered.append(Unanswered(
        part="Average catch for Gill Net trips?", mode="C",
        code=UnansweredCode.NEEDS_DISAMBIGUATION,
        detail="needs disambiguation: 'Gill Net' matches three sister tables",
        candidates=("peskas/kenya_validated_trips.csv",
                    "peskas/zanzibar_validated_trips.csv",
                    "peskas/mozambique_validated_trips.csv"),
    ))
    detail = serialize_answer(ra)["unanswered_detail"][0]

    assert detail["code"] == "NEEDS_DISAMBIGUATION"
    assert len(detail["candidates"]) == 3       # structured, not flattened into prose


def test_the_pre_existing_wire_shape_is_unchanged():
    """Additive only: the nine keys the UI reads today are all still there, same meaning."""
    ra = RouterAnswer(question=Q, routes=[Route("A", "signal: relate")])
    ra.claims.append(Claim(
        text="Peskas —uses→ WIO standard",
        citations=(CitationA(source_file="peskas/peskas_about.md", note="",
                             locator="peskas_hub --uses--> shared_wio", confidence="EXTRACTED"),),
        mode="A",
    ))
    data = serialize_answer(ra)

    for key in ("question", "answered", "modes_fired", "modes_grounded",
                "routes", "claims", "associations", "figures", "unanswered"):
        assert key in data, key
    assert data["unanswered"] == []                       # still a list of plain strings
    assert data["answered"] is True
    assert data["modes_grounded"] == ["A"]


def test_unanswered_still_serializes_as_strings():
    data = serialize_answer(_verified_negative())
    assert all(isinstance(u, str) for u in data["unanswered"])
    assert data["unanswered"][0].startswith(Q)            # "{part} — {detail}", as before
