"""The one place WDB resolves the repo root and the knowledge-base root.

WDB separates two trees with different lifecycles (see
[docs/production-stack-design.md](docs/production-stack-design.md) §1.1):

* **REPO_ROOT** — the application: the modes, the router, the services, `.claude/`,
  `pyproject.toml`. Changes on release.
* **KB_ROOT** — the knowledge base: the initiative folders (`peskas/`, `fasa/`, …) plus the
  built graph in `graphify-out/`. Changes on contribution.

Before this module every consumer derived the KB by walking up from its own source file and
assuming the initiative folders sat as siblings of the app packages
(`Path(__file__).parent.parent`). That implicit *"the app lives inside the KB root"* assumption
is what `KB_ROOT` replaces — the coupling §1.3 of the design doc calls out.

**Paths stay KB-root-relative.** Every `source_file` in `graph.json`, every catalog table key
and every citation is relative to `KB_ROOT`, never to `REPO_ROOT` — so a table is
`peskas/kenya_validated_trips.csv`, never `knowledge_base/peskas/…`. That is deliberate: the
first path segment is an **initiative name** throughout the system (Mode C derives a table's
identity tokens from it; the router derives `known_initiatives` from it), so leaking a container
directory into that segment would invent a bogus initiative and pollute entity resolution.
Keeping paths KB-relative is also what lets the KB move without rebuilding the graph.

Override `KB_ROOT` with the ``WDB_KB`` environment variable to point the app at a different
knowledge base — a contributor's own KB, a fixture tree, or a KB fetched to a container path.

**Every root is resolved here, once.** ``wdb_ingest/config.py`` used to re-derive both roots with
``Path(__file__).resolve().parent.parent`` — the exact idiom this module replaced — and its
``WDB_KB`` read used ``dict.get``'s default rather than ``or``, so ``WDB_KB=""`` made the *current
working directory* the knowledge base on the write side while every read-side module still used
the real one. It also introduced a second root override the rest of the system knew nothing
about, so ``WDB_ROOT=/x`` sent approved notes to ``/x/knowledge_base/`` while the modes kept
reading elsewhere. Both overrides now live here, both use ``or``, and the write side imports them.

Note the ``or`` (not a ``get`` default) in each: an env var set to the empty string must fall back,
not resolve to ``Path("")`` — which is the current working directory.
"""

from __future__ import annotations

import os
from pathlib import Path

#: The application repo root (the dir holding this file, the mode packages and ``pyproject.toml``).
#: Override with ``WDB_REPO`` (``WDB_ROOT`` is accepted as the older alias the ingestion service
#: documented). Overridable so the ingestion service's ``_state`` / ``_staging`` / enricher paths
#: can be repointed at a temp tree without a second, divergent derivation.
REPO_ROOT = Path(
    os.environ.get("WDB_REPO") or os.environ.get("WDB_ROOT") or Path(__file__).resolve().parent
)

#: The knowledge-base root: the initiative folders + ``graphify-out/``. Override with ``WDB_KB``.
KB_ROOT = Path(os.environ.get("WDB_KB") or REPO_ROOT / "knowledge_base")

#: The built graph the modes read (Mode A entity extraction, Mode B's graph join).
GRAPHIFY_OUT = KB_ROOT / "graphify-out"
GRAPH_JSON = GRAPHIFY_OUT / "graph.json"
BUILD_INFO = GRAPHIFY_OUT / "BUILD_INFO.md"

#: Mode B's Chroma passage index. Override with ``WDB_INDEX``.
#:
#: KB-rooted, because the index is **derived from a specific knowledge base's corpus**. It used to
#: live inside the installed package (``mode_b/.index``), which meant pointing ``WDB_KB`` at a
#: second knowledge base silently kept the first one's passage index: Mode B would retrieve
#: KB-A's passages and join them against KB-B's ``graph.json``. Deriving it from ``KB_ROOT``
#: makes the index follow the corpus it indexes.
#:
#: It is regenerable (gitignored; rebuild with ``python -m mode_b --ingest``) and is already
#: designated a KB runtime artifact rather than an app one — see
#: ``docs/production-stack-design.md`` §"what moves to GCS", which lists the Chroma index
#: alongside ``graph.json`` and the queryable CSVs.
INDEX_DIR = Path(os.environ.get("WDB_INDEX") or KB_ROOT / ".index")
