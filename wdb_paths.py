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
"""

from __future__ import annotations

import os
from pathlib import Path

#: The application repo root (the dir holding this file, the mode packages and ``pyproject.toml``).
REPO_ROOT = Path(__file__).resolve().parent

#: The knowledge-base root: the initiative folders + ``graphify-out/``. Override with ``WDB_KB``.
KB_ROOT = Path(os.environ.get("WDB_KB") or REPO_ROOT / "knowledge_base")

#: The built graph the modes read (Mode A entity extraction, Mode B's graph join).
GRAPHIFY_OUT = KB_ROOT / "graphify-out"
GRAPH_JSON = GRAPHIFY_OUT / "graph.json"
