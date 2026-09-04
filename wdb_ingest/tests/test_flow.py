"""The end-to-end service flow — real git writes on sign-off, and the build handoff to LIVE."""

import json

import pytest

from wdb_ingest import builder, config, service
from wdb_ingest.gate import GateError
from wdb_ingest.models import Role
from wdb_ingest.models import WorkflowState as S


def test_happy_path_to_live(store, to_pending):
    sub = to_pending()
    assert sub.state == S.PENDING
    assert sub.draft and sub.draft.template == "B"

    # the gate is server-enforced: a contributor cannot sign off
    with pytest.raises(GateError) as e:
        service.act(store, sub.id, "curator_approve", Role.CONTRIBUTOR)
    assert e.value.forbidden

    sub = service.act(store, sub.id, "curator_approve", Role.CURATOR)
    assert sub.state == S.QUEUED

    # the hard handoff really wrote the file + companion note into the KB's initiative folder
    assert (config.KB_ROOT / "ssf_research" / "ssf_notes.md").exists()
    note = config.KB_ROOT / "ssf_research" / "ssf_notes_context.md"
    assert note.exists()
    assert "## Summary" in note.read_text()  # PROTOCOL §6 Template B shape

    # build handoff: snapshot baseline, hand off, confirm completion → LIVE
    config.GRAPH_JSON.write_text(json.dumps({"nodes": [1, 2], "edges": []}))
    bs = builder.start_build(store)
    assert bs["status"] == "AWAITING_BUILD"
    # the EXACT command, not a substring: `/graphify . --update` builds from the repo root,
    # which CHANGELOG.md records as wrong (the first path segment must be the initiative).
    assert bs["command"] == "/graphify knowledge_base --update"
    assert bs["model"] == "claude-opus-4-8"

    done = builder.confirm(store)
    assert done["status"] == "DONE"
    assert store.get(sub.id).state == S.LIVE


def test_reject_and_resubmit(store, to_pending):
    sub = to_pending()
    sub = service.act(store, sub.id, "reject", Role.CURATOR, reason="reshape to one tidy table")
    assert sub.state == S.REJECTED
    assert sub.rejection_reason == "reshape to one tidy table"

    sub = service.act(store, sub.id, "resubmit", Role.CONTRIBUTOR)
    assert sub.state == S.PENDING
    assert sub.rejection_reason is None


def test_build_autodetects_real_graph_change(store, to_pending):
    sub = to_pending()
    service.act(store, sub.id, "curator_approve", Role.CURATOR)
    config.GRAPH_JSON.write_text(json.dumps({"nodes": [1, 2], "edges": []}))
    builder.start_build(store)

    # simulate the real pinned build rewriting the graph (node/edge counts change)
    config.GRAPH_JSON.write_text(json.dumps({"nodes": [1, 2, 3], "edges": [9]}))
    st = builder.poll(store, promote=True)
    assert st["status"] == "DONE"
    assert store.get(sub.id).state == S.LIVE


def test_build_noop_when_queue_empty(store):
    assert builder.start_build(store)["status"] == "IDLE"


def test_curator_override_marks_edited(store, to_pending):
    sub = to_pending()
    edited = sub.draft.model_copy(update={"summary": "Curator-tightened summary."})
    sub = service.edit_draft(store, sub.id, edited, Role.CURATOR, actor="curator")
    assert sub.curator_edited is True
    assert sub.draft.summary == "Curator-tightened summary."
