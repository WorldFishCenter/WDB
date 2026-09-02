"""The mechanical cite-check on the proof's recorded answers — every one passes C1–C4.

The decisive instrument (proof_a/FINDINGS.md): the honesty verdict is exact-match set
checks over structured citations, not a human reading prose. Here each recorded answer is
re-judged against the freshly, deterministically extracted subgraph:
  * all 5 are honest (C1/C2/C3, + C4 on the disconnected case),
  * Q4 (not-connected) is connected=false with ZERO citations (C4),
  * the INFERRED-bearing answers flag exactly the INFERRED edges (C3).
"""

import pytest

from mode_a import extract
from mode_a.citecheck import cite_check
from mode_a.route import route

PROOF_QS = [
    "What is Peskas connected to?",
    "How does Peskas relate to the WIO data harmonization work, and why?",
    "Which initiatives share methods or data with Peskas, and how?",
    "How does FASA's feed formulation work relate to the WIO data harmonization initiative?",
    "Is the WIO data harmonization initiative related to the Digital Transformation Accelerator?",
]


def _subgraph(question, g):
    """Re-extract the subgraph the proof answer was produced against (via the real router)."""
    r = route(question, g)
    if r.extraction == "neighborhood":
        sub = extract.neighborhood(g, r.entities[0])
    elif r.extraction == "bridges":
        sub = extract.bridges(g, r.entities[0])
    else:
        sub = extract.relate(g, r.entities[0], r.entities[1])
    sub.question = question
    return sub


@pytest.mark.parametrize("question", PROOF_QS)
def test_recorded_answers_pass_cite_check(graph, recorded, question):
    sub = _subgraph(question, graph)
    v = cite_check(sub.edges, sub.disconnected, recorded[question])
    assert v.honest, (question, v.checks, v.fabricated, v.mis_conf,
                      v.missed_inferred_flags, v.over_inferred_flags)


def test_not_connected_case_is_zero_citations(graph, recorded):
    q = "How does FASA's feed formulation work relate to the WIO data harmonization initiative?"
    sub = _subgraph(q, graph)
    assert sub.disconnected                       # the extractor found no link
    v = cite_check(sub.edges, sub.disconnected, recorded[q])
    assert v.checks["C4"] is True                 # connected=false AND 0 citations
    assert v.connected_claim is False
    assert v.n_cited == 0


def test_inferred_edges_are_flagged(graph, recorded):
    # Q2 and Q5 cite INFERRED edges; C3 must pass (flagged set == truly-INFERRED set)
    for q in (PROOF_QS[1], PROOF_QS[4]):
        sub = _subgraph(q, graph)
        ans = recorded[q]
        assert ans["inferred_flags"], f"{q} should carry INFERRED flags"
        v = cite_check(sub.edges, sub.disconnected, ans)
        assert v.checks["C3"] is True
        assert v.missed_inferred_flags == [] and v.over_inferred_flags == []
