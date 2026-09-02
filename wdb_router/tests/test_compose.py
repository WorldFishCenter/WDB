"""A blended question composes >1 mode into one §6 answer, every claim traceable.

Mode A here is the **real** Mode A: the blended question fans out to A's enumeration path
(no model) alongside B's recorded synthesis and C's recorded resolution.
"""

from wdb_router import answer
from wdb_router.fixtures import BLENDED


def test_blended_routes_to_more_than_one_mode(backends):
    ans = answer(BLENDED, backends=backends)
    assert len(ans.modes_fired) > 1
    assert set(ans.modes_grounded) == {"A", "B", "C"}   # all three contribute


def test_every_claim_carries_a_mode_and_at_least_one_citation(backends):
    # §6 rule 1: no claim without a citation; each claim names the mode that grounded it
    # and a WDB-relative source — i.e. every claim is traceable.
    ans = answer(BLENDED, backends=backends)
    assert ans.claims
    for c in ans.claims:
        assert c.mode in {"A", "B", "C"}
        assert len(c.citations) >= 1
        for cit in c.citations:
            assert cit.source_file


def test_each_mode_keeps_its_native_citation_artifact(backends):
    # the router does not flatten the modes' citations: A=graph edge, B=verbatim
    # quote+nodes, C=SQL+result — each retained intact.
    ans = answer(BLENDED, backends=backends)
    by_mode = {}
    for c in ans.claims:
        by_mode.setdefault(c.mode, c)
    assert by_mode["A"].citations[0].locator                 # graph edge triple
    assert by_mode["B"].citations[0].quote                   # verbatim span
    assert by_mode["C"].citations[0].sql                     # the query
    assert by_mode["C"].citations[0].result                  # ...and its rows


def test_associations_are_merged_and_deduped(backends):
    ans = answer(BLENDED, backends=backends)
    assert ans.associations
    keys = [(e["source"], e.get("relation"), e["target"]) for e in ans.associations]
    assert len(keys) == len(set(keys))


def test_blended_answer_is_one_unified_response(backends):
    # one RouterAnswer, not three — claims from all modes live in one list
    ans = answer(BLENDED, backends=backends)
    seen_modes = {c.mode for c in ans.claims}
    assert seen_modes == {"A", "B", "C"}
