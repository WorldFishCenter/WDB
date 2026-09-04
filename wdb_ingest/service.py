"""The ingestion operations layer — gate-enforced, with the real file/note writes.

Every state move goes through ``gate.apply_transition`` (role-checked, server-side), so the two-stage
gate cannot be bypassed by the client. Curator sign-off is the hard handoff (design §5): the staged
file is copied into its existing initiative folder and the companion note is written to git; only then
does the contribution become QUEUED. No initiative-folder reorganization happens here.
"""

from __future__ import annotations

import shutil
import threading
import uuid
from pathlib import Path

from . import config, gate
from .drafting import draft_for
from .models import DraftedNote, Role, Submission, SubmissionInput, WorkflowState
from .notes import note_to_markdown
from .ops import now_iso
from .store import WorkflowStore


class NotFound(Exception):
    pass


class InvalidPlacement(ValueError):
    """The upload names an initiative that does not exist, or a filename that escapes the KB."""


def validate_placement(initiative: str, filename: str) -> None:
    """Refuse an upload that could not land inside a real initiative folder.

    ``config.INITIATIVES`` carried a comment describing a real past bug — selecting a
    non-existent initiative minted a folder for it — and had **no uses**: the API took
    ``initiative`` as an unvalidated query parameter and :func:`_promote_to_git` did
    ``mkdir(parents=True)`` on it. ``filename`` was equally unchecked, so ``../../etc/x`` would
    have been copied outside ``KB_ROOT`` entirely. Both are checked here, before anything is
    staged, because this runs on the write path that creates directories.
    """
    if initiative not in config.INITIATIVES:
        raise InvalidPlacement(
            f"Unknown initiative {initiative!r}. Must be one of: "
            f"{', '.join(config.INITIATIVES)}."
        )
    name = Path(filename).name
    if not filename or name != filename or name in (".", ".."):
        raise InvalidPlacement(
            f"Filename {filename!r} must be a plain file name with no path separators."
        )


def _new_id() -> str:
    return f"sub_{uuid.uuid4().hex[:10]}"


def _staged_path(sub: Submission):
    return config.STAGING_DIR / sub.id / sub.filename


def submit(
    store: WorkflowStore,
    inp: SubmissionInput,
    file_bytes: bytes,
    contributor: str,
    *,
    background: bool = True,
) -> Submission:
    """Create a SUBMITTED contribution: stage the real file, stamp provenance, kick the draft."""
    validate_placement(inp.initiative, inp.filename)   # before anything touches the filesystem
    config.ensure_dirs()
    sub_id = _new_id()
    sub = Submission(
        id=sub_id,
        filename=inp.filename,
        format=inp.format,
        sizeLabel=inp.size_label,
        initiative=inp.initiative,
        targetPlacement=f"{inp.initiative}/{inp.filename}",
        state=WorkflowState.SUBMITTED,
        provenance={
            "contributor": contributor,
            "author": inp.author or contributor,
            "captured_at": now_iso(),
            "source_url": inp.source_url or f"upload://{inp.filename}",
        },
        draft=None,
        curatorEdited=False,
        history=[{"state": "SUBMITTED", "at": now_iso(), "actor": contributor}],
    )
    # stage the real bytes
    staged = _staged_path(sub)
    staged.parent.mkdir(parents=True, exist_ok=True)
    staged.write_bytes(file_bytes)
    store.upsert(sub)

    # run the (deterministic) draft — in a thread so submit returns promptly and the UI shows
    # SUBMITTED → DRAFTED; tests pass background=False for determinism.
    if background:
        threading.Thread(target=run_draft, args=(store, sub_id), daemon=True).start()
    else:
        run_draft(store, sub_id)
    return store.get(sub_id) or sub


def run_draft(store: WorkflowStore, sub_id: str) -> Submission | None:
    """SUBMITTED → DRAFTED: run the real enricher (tables) / scaffold and attach the note."""
    sub = store.get(sub_id)
    if not sub or sub.state != WorkflowState.SUBMITTED:
        return sub
    inp = SubmissionInput(
        filename=sub.filename,
        format=sub.format,
        sizeLabel=sub.size_label,
        initiative=sub.initiative,
        author=sub.provenance.author,
        sourceUrl=sub.provenance.source_url,
    )
    note = draft_for(inp, _staged_path(sub))
    drafted = gate.apply(sub, "autodraft", actor="Auto-draft (enrich + scaffold)").model_copy(
        update={"draft": note}
    )
    store.upsert(drafted)
    return drafted


def act(
    store: WorkflowStore,
    sub_id: str,
    action: str,
    role: Role,
    *,
    actor: str | None = None,
    reason: str | None = None,
) -> Submission:
    """Apply a role-driven transition (gate-checked). ``curator_approve`` writes to git first."""
    sub = store.get(sub_id)
    if not sub:
        raise NotFound(sub_id)
    # Validate BEFORE any side effect: `curator_approve` writes to git below, and a refused
    # transition must not leave a note behind. `gate.apply` re-checks and performs the move.
    gate.apply_transition(action, role, sub.state)  # raises GateError (403/409)
    actor = actor or role.value

    note = {
        "approve": "Approved for curator review",
        "resubmit": "Re-submitted after revision",
        "open_for_review": None,
        "curator_approve": "Signed off — note written to git; queued for build",
        "reject": (f"Returned to contributor: {reason}" if reason else "Returned to contributor"),
    }.get(action)

    if action == "curator_approve":
        _promote_to_git(sub)  # the hard handoff: file + note into git, BEFORE we advance to QUEUED

    updated = gate.apply(sub, action, role=role, actor=actor, note=note)
    if action == "reject":
        updated = updated.model_copy(update={"rejection_reason": reason})
    elif action == "resubmit":
        updated = updated.model_copy(update={"rejection_reason": None})
    store.upsert(updated)
    return updated


def edit_draft(store: WorkflowStore, sub_id: str, draft: DraftedNote, role: Role, *, actor: str | None = None) -> Submission:
    """Edit the drafted note (contributor while reviewing; curator override while pending)."""
    sub = store.get(sub_id)
    if not sub:
        raise NotFound(sub_id)
    if not gate.can_edit_draft(role, sub.state):
        raise gate.GateError(f"Role {role.value!r} may not edit the draft in state {sub.state.value}.", forbidden=True)
    updated = sub.model_copy(update={"draft": draft})
    if role == Role.CURATOR:
        updated = gate.apply(
            updated, "curator_override", actor=actor or "curator",
            note="Curator override: edited draft",
        ).model_copy(update={"curator_edited": True})
    store.upsert(updated)
    return updated


def _promote_to_git(sub: Submission) -> None:
    """Copy the staged file into its EXISTING initiative folder and write the companion note to git.

    The file lands at ``<KB_ROOT>/<initiative>/<filename>`` — initiative folders live in the
    knowledge base, not the app repo. From this point git is the system of record (design §5).
    """
    target_dir = config.KB_ROOT / sub.initiative
    target_dir.mkdir(parents=True, exist_ok=True)

    staged = _staged_path(sub)
    if staged.exists():
        shutil.copy2(staged, target_dir / sub.filename)

    if sub.draft:
        (target_dir / sub.draft.filename).write_text(note_to_markdown(sub.draft, sub.provenance), encoding="utf-8")


def list_for_role(store: WorkflowStore, role: Role, user: str) -> list[Submission]:
    """Contributor sees their own submissions; curator sees the whole board."""
    if role == Role.CONTRIBUTOR:
        return store.list_submissions(contributor=user)
    return store.list_submissions()
