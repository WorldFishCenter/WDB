"""Paths and settings for the ingestion service.

WDB_ROOT is the repo root (the dir holding ``graphify-out/`` and the initiative folders). The
service writes staged uploads and the workflow DB under ``wdb_ingest/_state`` and ``_staging``
(both gitignored), and writes approved notes/files into the **existing** initiative folders
(no folder reorganization — that is a separate PR).
"""

from __future__ import annotations

import os
from pathlib import Path

# wdb_ingest/ lives at the repo root, so its parent is WDB_ROOT. Override with WDB_ROOT.
WDB_ROOT = Path(os.environ.get("WDB_ROOT", Path(__file__).resolve().parent.parent))

STATE_DIR = WDB_ROOT / "wdb_ingest" / "_state"
STAGING_DIR = WDB_ROOT / "wdb_ingest" / "_staging"
DB_PATH = Path(os.environ.get("WDB_INGEST_DB", STATE_DIR / "workflow.db"))

GRAPHIFY_OUT = WDB_ROOT / "graphify-out"
GRAPH_JSON = GRAPHIFY_OUT / "graph.json"
BUILD_INFO = GRAPHIFY_OUT / "BUILD_INFO.md"
ENRICHER = WDB_ROOT / ".claude" / "scripts" / "dict_enricher.py"

# The pinned build command the maintainer runs (the only place the two CLAUDE.md guards + the
# canonical-entity remap apply). Surfaced by the build orchestrator as the handoff command.
PINNED_BUILD_COMMAND = "/graphify . --update"
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
