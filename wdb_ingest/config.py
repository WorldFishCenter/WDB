"""Settings for the ingestion service. **Paths come from :mod:`wdb_paths`, not from here.**

The service straddles the two trees (see :mod:`wdb_paths`): ``REPO_ROOT`` is the **app** repo root
(it owns ``wdb_ingest/_state``, ``_staging`` and the ``.claude/`` enricher script), while
``KB_ROOT`` is the **knowledge base** — where approved notes/files land in their initiative folder
and where the built graph lives.

This module used to re-derive both roots itself, with ``Path(__file__).resolve().parent.parent``
and a ``dict.get`` default on ``WDB_KB``. That made the write side — the only side that *creates*
directories — disagree with every reader in two ways: ``WDB_KB=""`` resolved to the current
working directory here but fell back correctly elsewhere, and a ``WDB_ROOT`` override no reader
knew about could send approved notes to a different knowledge base entirely. Both overrides now
live in ``wdb_paths`` and are imported below, so there is one answer to "which KB is this?".

The test suite still monkeypatches the names in this module (see ``tests/conftest.py``), which is
why they are re-bound here rather than used directly from ``wdb_paths`` at each call site.
"""

from __future__ import annotations

import os
from pathlib import Path

from wdb_paths import BUILD_INFO, GRAPH_JSON, GRAPHIFY_OUT, KB_ROOT, REPO_ROOT

# Kept as the name the service and its tests already use; the derivation lives in wdb_paths
# (override with WDB_REPO, or the older WDB_ROOT alias).
WDB_ROOT = REPO_ROOT

# Re-exported so `config.KB_ROOT` / `config.GRAPH_JSON` stay the service's handles (and stay
# monkeypatchable in tests) while wdb_paths remains the single derivation.
KB_ROOT = KB_ROOT
GRAPHIFY_OUT = GRAPHIFY_OUT
GRAPH_JSON = GRAPH_JSON
BUILD_INFO = BUILD_INFO

STATE_DIR = WDB_ROOT / "wdb_ingest" / "_state"
STAGING_DIR = WDB_ROOT / "wdb_ingest" / "_staging"
DB_PATH = Path(os.environ.get("WDB_INGEST_DB") or STATE_DIR / "workflow.db")

ENRICHER = WDB_ROOT / ".claude" / "scripts" / "dict_enricher.py"

# The pinned build command the maintainer runs (the only place the two CLAUDE.md guards + the
# canonical-entity remap apply). Surfaced by the build orchestrator as the handoff command.
PINNED_BUILD_COMMAND = "/graphify knowledge_base --update"
PINNED_MODEL = "claude-opus-4-8"

# The initiative folders an upload may target — the five that exist in the knowledge base.
# "civ-kb" used to be listed here; it is a SEPARATE project, never a WDB initiative (Mode B
# vendored its retrieval core as a library — see mode_b/extract.py — and imports nothing from
# it at runtime). Selecting it minted an initiative folder for an initiative that does not exist.
#
# This list is now ENFORCED (see wdb_ingest.service.validate_placement). It previously had zero
# uses anywhere: the API took `initiative` as an unvalidated query parameter and the promote step
# did `mkdir(parents=True)` on it, so the exact bug this comment memorialises was one non-browser
# request away.
INITIATIVES = [
    "peskas",
    "fasa",
    "data_harmonization",
    "digital_transformation_accelerator",
    "ssf_research",
]


def ensure_dirs() -> None:
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    STAGING_DIR.mkdir(parents=True, exist_ok=True)
