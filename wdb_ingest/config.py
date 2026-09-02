"""Paths and settings for the ingestion service.

The service straddles the two trees (see :mod:`wdb_paths`): WDB_ROOT is the **app** repo root
(it owns ``wdb_ingest/_state``, ``_staging`` and the ``.claude/`` enricher script), while KB_ROOT
is the **knowledge base** — where approved notes/files land in their initiative folder and where
the built graph lives. Both are overridable (``WDB_ROOT`` / ``WDB_KB``) so the test suite can run
hermetically against a temp tree.
"""

from __future__ import annotations

import os
from pathlib import Path

# wdb_ingest/ lives at the repo root, so its parent is WDB_ROOT. Override with WDB_ROOT.
WDB_ROOT = Path(os.environ.get("WDB_ROOT", Path(__file__).resolve().parent.parent))

# The knowledge base the service writes contributions into. Defaults to WDB_ROOT/knowledge_base
# (via wdb_paths) but follows WDB_ROOT when the tests repoint it at a temp tree.
KB_ROOT = Path(os.environ.get("WDB_KB", WDB_ROOT / "knowledge_base"))

STATE_DIR = WDB_ROOT / "wdb_ingest" / "_state"
STAGING_DIR = WDB_ROOT / "wdb_ingest" / "_staging"
DB_PATH = Path(os.environ.get("WDB_INGEST_DB", STATE_DIR / "workflow.db"))

GRAPHIFY_OUT = KB_ROOT / "graphify-out"
GRAPH_JSON = GRAPHIFY_OUT / "graph.json"
BUILD_INFO = GRAPHIFY_OUT / "BUILD_INFO.md"
ENRICHER = WDB_ROOT / ".claude" / "scripts" / "dict_enricher.py"

# The pinned build command the maintainer runs (the only place the two CLAUDE.md guards + the
# canonical-entity remap apply). Surfaced by the build orchestrator as the handoff command.
PINNED_BUILD_COMMAND = "/graphify knowledge_base --update"
PINNED_MODEL = "claude-opus-4-8"

# The initiative folders an upload may target (they live where they currently are — no reorg).
INITIATIVES = [
    "peskas",
    "fasa",
    "data_harmonization",
    "digital_transformation_accelerator",
    "ssf_research",
    "civ-kb",
]


def ensure_dirs() -> None:
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    STAGING_DIR.mkdir(parents=True, exist_ok=True)
