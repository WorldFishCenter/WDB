"""The gate is the only thing that moves a contribution — and every move is declared.

``gate.apply_transition`` (policy) used to be separate from ``ops.advance`` (mutation), and
``advance`` accepted any ``(from, to)`` pair. Five of six callers skipped the gate entirely, and
the two tables describing those system moves — ``AUTODRAFT`` and ``BUILD_TRANSITIONS`` — had zero
references in the repo. These tests pin the property that replaced them.
"""

import json

import pytest

from wdb_ingest import builder, config, gate, service
from wdb_ingest.gate import GateError
from wdb_ingest.models import Role, WorkflowState as S


# --- there is no mutator outside the gate ---------------------------------- #

def test_ops_no_longer_exposes_a_state_mutator():
    """The whole point: no module but the gate can move a contribution."""
    import wdb_ingest.ops as ops
    assert not hasattr(ops, "advance")


def test_every_system_transition_is_declared():
    """Every action the service and the builder ask for must exist in a table."""
    declared = set(gate._BY_ACTION) | set(gate._BY_SYSTEM_ACTION)
    used = {"open_for_review", "approve", "resubmit", "curator_approve", "reject",
            "autodraft", "handoff", "build_built", "build_live", "curator_override"}
    assert used <= declared


def test_an_undeclared_move_is_refused():
    sub = _fresh()
    with pytest.raises(GateError):
        gate.apply(sub, "publish_immediately", actor="me")


# --- role-driven vs system actions cannot be confused ---------------------- #

def test_a_system_transition_refuses_a_role():
    """No actor may request BUILT/LIVE — passing a role is itself the error."""
    sub = _fresh()
    with pytest.raises(GateError) as e:
        gate.apply(sub, "autodraft", role=Role.CONTRIBUTOR, actor="me")
    assert e.value.forbidden


def test_a_role_driven_transition_requires_a_role():
    sub = _at(S.DRAFTED)
    with pytest.raises(GateError) as e:
        gate.apply(sub, "open_for_review", actor="me")
    assert e.value.forbidden


def test_build_states_are_unreachable_without_the_declared_path():
    """QUEUED -> LIVE cannot be jumped: `build_live` is only legal from BUILT."""
    queued = _at(S.QUEUED)
    with pytest.raises(GateError):
        gate.apply(queued, "build_live", actor="build")

    built = gate.apply(queued, "build_built", actor="build")
    assert built.state is S.BUILT
    assert gate.apply(built, "build_live", actor="build").state is S.LIVE


def test_apply_appends_history_append_only():
    sub = _at(S.DRAFTED)
    before = len(sub.history)
    moved = gate.apply(sub, "open_for_review", role=Role.CONTRIBUTOR, actor="ana", note="n")
    assert moved.state is S.UNDER_REVIEW
    assert len(moved.history) == before + 1
    assert moved.history[-1].actor == "ana" and moved.history[-1].note == "n"
    assert moved.history[:before] == sub.history        # nothing rewritten
    assert sub.state is S.DRAFTED                       # and the input is untouched


def test_the_contributor_still_cannot_reach_the_build_states():
    """The original invariant, restated against the mutator rather than the tuple."""
    reachable = gate.contributor_reachable_states()
    assert not ({S.QUEUED, S.BUILT, S.LIVE} & reachable)


# --- the build-status hole ------------------------------------------------- #

def test_a_read_only_poll_does_not_publish(store, to_pending):
    """A plain GET used to run the promotion; only a curator's poll may now."""
    sub = to_pending()
    service.act(store, sub.id, "curator_approve", Role.CURATOR)
    config.GRAPH_JSON.write_text(json.dumps({"nodes": [1], "edges": []}))
    builder.start_build(store)
    # the pinned build rewrote the graph — completion is now detectable
    config.GRAPH_JSON.write_text(json.dumps({"nodes": [1, 2, 3], "edges": [9]}))

    assert builder.poll(store)["status"] == "AWAITING_BUILD"        # contributor's poll
    assert store.get(sub.id).state is S.QUEUED                     # NOT published

    assert builder.poll(store, promote=True)["status"] == "DONE"    # curator's poll
    assert store.get(sub.id).state is S.LIVE


def test_reset_requires_the_curator(client):
    assert client.post("/reset", headers={"X-WDB-Role": "contributor",
                                          "X-WDB-User": "ana"}).status_code == 403
    assert client.post("/reset", headers={"X-WDB-Role": "curator",
                                          "X-WDB-User": "lore"}).status_code == 200


# --- helpers --------------------------------------------------------------- #

def _fresh():
    from wdb_ingest.models import Provenance, Submission
    return Submission(
        id="sub_test", filename="x.csv", format="tabular", sizeLabel="1 KB",
        initiative="peskas", targetPlacement="peskas/x.csv", state=S.SUBMITTED,
        provenance=Provenance(contributor="ana", author="ana",
                              captured_at="2026-01-01T00:00:00Z", source_url=""),
        history=[],
    )


def _at(state):
    return _fresh().model_copy(update={"state": state})
