"""The two-stage approval gate — the state machine, enforced server-side.

This module is the single source of truth for *who may move a contribution where*. It is the
protocol's load-bearing guarantee (design §2): a **contributor** can only advance a contribution to
``PENDING`` (stage-1, "ready for review" ≈ opening a PR); only a **curator** moves ``PENDING →
QUEUED`` (stage-2 sign-off ≈ merging); and only the **build** moves ``QUEUED → BUILT → LIVE``. There
is deliberately **no action by which a contributor reaches QUEUED/BUILT/LIVE** — the gate is
unbypassable here, not merely in the UI.
"""

from __future__ import annotations

from dataclasses import dataclass

from .models import Role, WorkflowState

S = WorkflowState


class GateError(Exception):
    """A transition the gate refuses. ``forbidden`` → 403 (wrong role); else → 409 (wrong state)."""

    def __init__(self, message: str, *, forbidden: bool = False) -> None:
        super().__init__(message)
        self.forbidden = forbidden


@dataclass(frozen=True)
class Transition:
    action: str
    role: Role
    from_states: frozenset[WorkflowState]
    to_state: WorkflowState


# Every role-driven transition. Note: NO contributor transition targets QUEUED/BUILT/LIVE.
USER_TRANSITIONS: tuple[Transition, ...] = (
    Transition("open_for_review", Role.CONTRIBUTOR, frozenset({S.DRAFTED}), S.UNDER_REVIEW),
    # stage-1 gate: the furthest a contributor can move anything
    Transition("approve", Role.CONTRIBUTOR, frozenset({S.UNDER_REVIEW}), S.PENDING),
    Transition("resubmit", Role.CONTRIBUTOR, frozenset({S.REJECTED}), S.PENDING),
    # stage-2 gate: curator only
    Transition("curator_approve", Role.CURATOR, frozenset({S.PENDING}), S.QUEUED),
    Transition("reject", Role.CURATOR, frozenset({S.PENDING}), S.REJECTED),
)

# System transitions (not role-driven): the auto-draft agents and the single-builder build.
AUTODRAFT = Transition("autodraft", Role.CONTRIBUTOR, frozenset({S.SUBMITTED}), S.DRAFTED)
BUILD_TRANSITIONS: tuple[tuple[WorkflowState, WorkflowState], ...] = (
    (S.QUEUED, S.BUILT),
    (S.BUILT, S.LIVE),
)

_BY_ACTION: dict[str, Transition] = {t.action: t for t in USER_TRANSITIONS}


def apply_transition(action: str, role: Role, current: WorkflowState) -> WorkflowState:
    """Resolve a role-driven action to its next state, or raise ``GateError``.

    Checks role first (403 on mismatch), then the current state (409 if the action isn't legal
    from here). The role check is what makes the gate real: a contributor request for
    ``curator_approve`` is refused with 403, server-side.
    """
    t = _BY_ACTION.get(action)
    if t is None:
        raise GateError(f"Unknown action: {action!r}", forbidden=True)
    if role != t.role:
        raise GateError(
            f"Role {role.value!r} may not perform {action!r} (requires {t.role.value!r}).",
            forbidden=True,
        )
    if current not in t.from_states:
        raise GateError(f"Cannot {action!r} from state {current.value} (needs one of "
                        f"{sorted(s.value for s in t.from_states)}).")
    return t.to_state


def can_edit_draft(role: Role, state: WorkflowState) -> bool:
    """Who may edit the drafted note: the contributor while reviewing/revising, the curator while
    it's pending (CURATOR_OVERRIDE). No editing once it has left for the build (QUEUED+)."""
    if role == Role.CONTRIBUTOR:
        return state in (S.UNDER_REVIEW, S.REJECTED)
    if role == Role.CURATOR:
        return state == S.PENDING
    return False


def contributor_reachable_states() -> set[WorkflowState]:
    """All states a CONTRIBUTOR can drive a contribution into, by any sequence of their actions.

    Used by the gate-invariant test: this set must NOT contain QUEUED/BUILT/LIVE.
    """
    reachable: set[WorkflowState] = set()
    # seed with where a fresh contribution can be after submit + autodraft
    frontier = {S.SUBMITTED, S.DRAFTED, S.UNDER_REVIEW, S.PENDING, S.REJECTED}
    changed = True
    while changed:
        changed = False
        for st in list(frontier):
            for t in USER_TRANSITIONS:
                if t.role == Role.CONTRIBUTOR and st in t.from_states and t.to_state not in reachable:
                    reachable.add(t.to_state)
                    frontier.add(t.to_state)
                    changed = True
    return reachable
