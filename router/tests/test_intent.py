"""Layer-1 intent classification (§5): signals route to the right mode(s)."""

from router import classify
from router.fixtures import BLENDED, GROUPED, Q_OFFTOPIC


def modes(q: str) -> set[str]:
    return {r.mode for r in classify(q)}


def test_enumeration_routes_to_A():
    assert modes("What projects operate in Kenya?") == {"A"}
    assert "A" in modes("Which datasets feed Peskas?")
    assert "A" in modes("List the gear types in Zanzibar")


def test_synthesis_routes_to_B():
    assert modes("How does the platform validate catch survey data?") == {"B"}
    assert "B" in modes("What is the impact of Peskas on Mozambique aquaculture?")
    assert "B" in modes("Research gaps for cage culture in Zambia?")


def test_quantitative_routes_to_C():
    assert modes("Average total catch per trip in Kwale?") == {"C"}
    assert "C" in modes("How many trips were recorded?")
    assert "C" in modes("Compare catch by county")
    assert modes(GROUPED) == {"C"}


def test_quantitative_noun_alone_is_not_mode_C():
    # "catch survey data" has a quantitative noun but no operator -> not C
    assert "C" not in modes("How does the platform validate catch survey data?")


def test_blended_question_fans_out_to_all_three():
    assert modes(BLENDED) == {"A", "B", "C"}


def test_ambiguous_question_fans_out_to_all_modes():
    # no clear signal -> never a silent single pick; fan out to all (§5)
    assert modes("Tell me everything you know") == {"A", "B", "C"}


def test_offtopic_synthesis_routes_to_B():
    assert modes(Q_OFFTOPIC) == {"B"}   # "impact" -> B (then Mode B refuses it)


def test_every_route_carries_a_reason():
    for r in classify("Average catch by county"):
        assert r.reason
