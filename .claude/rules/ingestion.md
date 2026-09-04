---
paths:
  - "wdb_ingest/**"
  - "read-ui/lib/ingestion/**"
  - "read-ui/app/(ingestion)/**"
---

# The ingestion workflow

Design: [docs/ingestion-pipeline-design.md](../../docs/ingestion-pipeline-design.md). The
contribution protocol it implements: [PROTOCOL.md](../../PROTOCOL.md) §2.

## The gate owns the state machine

`wdb_ingest.gate.apply()` is the only function that moves a contribution between states. It
resolves the action against a declared table, checks it, and returns the advanced `Submission` with
its history entry appended.

- `USER_TRANSITIONS` — role-driven; `apply` requires a `role` and refuses the wrong one with 403,
  an illegal from-state with 409.
- `SYSTEM_TRANSITIONS` — the auto-draft, the build's `QUEUED → BUILT → LIVE`, the handoff
  annotation, the curator override. `apply` refuses a `role` here: no actor may request them.

Adding a state or a transition means declaring it in one of those tables. A move absent from both
raises `GateError`. This replaced a split where the gate decided and a separate `ops.advance`
applied — which accepted any `(from, to)` pair, so five of six state changes never consulted the
gate and the two tables describing them had zero references.

Stage-1 is the furthest a contributor can move anything (`PENDING`); only a curator signs off to
`QUEUED`; only the build reaches `BUILT`/`LIVE`. `gate.contributor_reachable_states()` proves it,
and `wdb_ingest/tests/test_gate_is_sole_mutator.py` pins the property.

## Writes to the knowledge base

`validate_placement()` runs before anything touches the filesystem: the initiative must be in
`config.INITIATIVES` and the filename must be a plain name. Both arrive from a query parameter and
`_promote_to_git` calls `mkdir(parents=True)`, so an unchecked initiative mints a folder for an
initiative that does not exist and an unchecked filename escapes `KB_ROOT` entirely.

"Promoted to git" means **written to the working tree** — nothing is auto-committed. The maintainer
reviews and commits.

## The build handoff

There is no faithful headless build: the two extraction guards and the canonical-entity remap are
injected by the maintainer's pinned session, not by the `graphify` CLI
([CLAUDE.md](../../CLAUDE.md)). So `builder.py` hands off rather than pretending — it snapshots
`graph.json`, records the handed-off ids, and surfaces `config.PINNED_BUILD_COMMAND` for a human to
run. Keep it that way.

`poll(store, promote=…)` splits read from write: everyone may read the build status, and only a
curator's poll publishes. Publishing used to be reachable through an unauthenticated `GET`.

## Paths and config

`wdb_ingest/config.py` imports its roots from `wdb_paths` and adds only service-local paths
(`STATE_DIR`, `STAGING_DIR`, `DB_PATH`, `ENRICHER`). Re-deriving a root here is what let the write
side and the read side disagree about which knowledge base was in play.

Reach config through the module (`from . import config`, then `config.WDB_ROOT`), not by value
(`from .config import WDB_ROOT`) — the test suite monkeypatches these names onto a temp tree, and a
by-value import keeps the real path. `drafting.py` held the one such import, and it was the only
module that spawns a subprocess.

## The note the contributor approves

`wdb_ingest/notes.py::note_to_markdown` and `read-ui/lib/ingestion/note.ts::noteToMarkdown` are the
same algorithm in two languages: one renders the preview a reviewer signs off on, the other writes
the file. They must stay byte-identical — change both in the same commit.
