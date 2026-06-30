"""The two-stage gate as a truth table — the protocol's load-bearing guarantee, proven in code."""

import pytest

from wdb_ingest.gate import GateError, apply_transition, can_edit_draft, contributor_reachable_states
from wdb_ingest.models import Role
from wdb_ingest.models import WorkflowState as S


def test_contributor_can_never_reach_publish_states():
    """No sequence of contributor actions reaches QUEUED/BUILT/LIVE. PENDING is the furthest."""
    reach = contributor_reachable_states()
    assert S.QUEUED not in reach
    assert S.BUILT not in reach
    assert S.LIVE not in reach
    assert S.PENDING in reach


def test_role_is_enforced():
    # contributor attempting the stage-2 sign-off → forbidden (403)
    with pytest.raises(GateError) as e:
        apply_transition("curator_approve", Role.CONTRIBUTOR, S.PENDING)
    assert e.value.forbidden
    # curator may → QUEUED
    assert apply_transition("curator_approve", Role.CURATOR, S.PENDING) == S.QUEUED


def test_state_is_enforced():
    # right role, wrong state → not forbidden (409), just illegal here
    with pytest.raises(GateError) as e:
        apply_transition("approve", Role.CONTRIBUTOR, S.DRAFTED)
    assert not e.value.forbidden


def test_stage1_path():
    assert apply_transition("open_for_review", Role.CONTRIBUTOR, S.DRAFTED) == S.UNDER_REVIEW
    assert apply_transition("approve", Role.CONTRIBUTOR, S.UNDER_REVIEW) == S.PENDING
    assert apply_transition("resubmit", Role.CONTRIBUTOR, S.REJECTED) == S.PENDING


def test_edit_permissions():
    assert can_edit_draft(Role.CONTRIBUTOR, S.UNDER_REVIEW)
    assert can_edit_draft(Role.CONTRIBUTOR, S.REJECTED)
    assert not can_edit_draft(Role.CONTRIBUTOR, S.PENDING)  # left their hands
    assert can_edit_draft(Role.CURATOR, S.PENDING)  # curator override
    assert not can_edit_draft(Role.CURATOR, S.QUEUED)  # past the gate
