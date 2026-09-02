"""Deterministic subgraph extraction — the honest half of Mode A.

Promoted from the proven ``proof_a/extract.py`` (the read-only Mode-A reasoning
proof). Given a question's canonical entities it pulls a small subgraph out of the
real ``graphify-out/graph.json`` — no model, no network, no embeddings, no graph
DB. It reuses ``mode_b.join.load_graph`` for graph I/O (the loaders already in use)
and plain Python for traversal.

Three extraction primitives, one per question shape (the shape router in
``route.py`` picks which one runs):

* :func:`neighborhood` — 1-hop incident edges of one entity        (direct enumeration)
* :func:`relate`       — direct inter-initiative edges + <=2-hop hub paths
                         between two entities; **empty => disconnected**  (how/why relate)
* :func:`bridges`      — 2-hop "shared connector" paths from one entity
                         to OTHER initiatives (how they share)           (which initiatives share…)

Each returns a :class:`SubGraph` (a node set + an edge set carrying full provenance:
relation, confidence EXTRACTED/INFERRED, source_file, source_location).
:meth:`SubGraph.serialize` renders exactly the text the reasoner is allowed to reason
over, and the edge set is the ground truth the mechanical cite-check
(``citecheck.py``) verifies citations against — depth-2 was sufficient for every
question in the proof (``proof_a/FINDINGS.md``).
"""

from __future__ import annotations

import sys
from dataclasses import dataclass, field
from pathlib import Path

# Reuse the existing graph loader rather than reimplementing graph I/O (task constraint).
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from mode_b.join import load_graph  # noqa: E402

GRAPH_PATH = str(Path(__file__).resolve().parent.parent / "graphify-out" / "graph.json")

# Initiative id-prefixes (the canonical-hub discipline: every node id is <initiative>_<slug>
# or shared_<slug>). "shared" is the cross-cutting bridge namespace, not an initiative.
INITIATIVES = ("peskas", "data_harmonization", "dta", "fasa", "ssf_research", "pondcube")


def initiative_of(node_id: str) -> str:
    """The initiative a node belongs to (its id-prefix), or 'shared' / 'other'."""
    if node_id.startswith("shared_"):
        return "shared"
    for p in INITIATIVES:
        if node_id == f"{p}_hub" or node_id == f"{p}_repo" or node_id.startswith(f"{p}_"):
            return p
    return "other"


# --------------------------------------------------------------------------- #
# Graph wrapper
# --------------------------------------------------------------------------- #
@dataclass
class Graph:
    nodes: list[dict]
    links: list[dict]

    def __post_init__(self) -> None:
        self.by_id = {n["id"]: n for n in self.nodes}
        # undirected adjacency; key each edge by frozenset for metadata lookup
        self.adj: dict[str, set[str]] = {n["id"]: set() for n in self.nodes}
        self.emeta: dict[frozenset, dict] = {}
        for e in self.links:
            s, t = e["source"], e["target"]
            self.adj[s].add(t)
            self.adj[t].add(s)
            self.emeta.setdefault(frozenset((s, t)), e)  # first edge wins (graph is simple)

    def label(self, node_id: str) -> str:
        return self.by_id.get(node_id, {}).get("label", node_id)

    def group(self, prefix: str) -> set[str]:
        """All node ids in one initiative (hub + satellites)."""
        return {nid for nid in self.by_id if initiative_of(nid) == prefix}

    def edge(self, a: str, b: str) -> dict | None:
        return self.emeta.get(frozenset((a, b)))

    def simple_paths(self, a: str, b: str, cap: int) -> list[list[str]]:
        """All simple paths a..b with <= cap edges (plain DFS, no NetworkX needed)."""
        out: list[list[str]] = []

        def dfs(cur: str, target: str, path: list[str], depth: int) -> None:
            if cur == target:
                out.append(list(path))
                return
            if depth == 0:
                return
            for nxt in self.adj[cur]:
                if nxt not in path:
                    path.append(nxt)
                    dfs(nxt, target, path, depth - 1)
                    path.pop()

        dfs(a, b, [a], cap)
        return out

    def resolve(self, name: str) -> str:
        """Canonical-name -> node id (the same key Mode C uses; exact alias map + fallback).

        Entity resolution is a known, **shared-with-Mode-C** concern that is NOT
        solved here (the proof did not test it; docs/three-mode-architecture.md §5
        Layer-2). This is a deliberate, explicit map of the known initiative entities'
        canonical names to ids, plus an exact label/id fallback — enough to route the
        relational questions Mode A answers. A node id passed as ``name`` resolves to
        itself (the id fallback), so callers may pass an already-resolved id.
        """
        key = name.strip().lower()
        if key in _ALIASES:
            return _ALIASES[key]
        for n in self.nodes:
            if (n.get("norm_label") or "").lower() == key or n["id"].lower() == key:
                return n["id"]
        raise KeyError(f"cannot resolve entity {name!r} to a node id")


# Canonical names of the known initiative entities -> their committed hub/node id.
_ALIASES = {
    "peskas": "peskas_hub",
    "wio data harmonization": "data_harmonization_hub",
    "wio ssf data harmonization initiative": "data_harmonization_hub",
    "data harmonization": "data_harmonization_hub",
    "digital transformation accelerator": "dta_hub",
    "dta": "dta_hub",
    "fasa": "fasa_repo",
    "fasa feed formulation engine": "fasa_repo",
}


# --------------------------------------------------------------------------- #
# Subgraph result
# --------------------------------------------------------------------------- #
@dataclass
class SubGraph:
    """The extracted subgraph the reasoner is allowed to reason over."""

    question: str
    anchors: list[str]                       # node ids the question named
    edges: list[dict] = field(default_factory=list)
    note: str = ""                           # e.g. the "disconnected" verdict
    _g: Graph | None = None

    @property
    def disconnected(self) -> bool:
        return self.edges == []

    def node_ids(self) -> list[str]:
        ids: list[str] = list(self.anchors)
        for e in self.edges:
            for k in ("source", "target"):
                if e[k] not in ids:
                    ids.append(e[k])
        return ids

    def edge_keys(self) -> set[tuple]:
        """Ground truth for the cite-check: the (source, relation, target) triples present.

        Direction-insensitive — a citation may name either endpoint first.
        """
        keys: set[tuple] = set()
        for e in self.edges:
            keys.add((e["source"], e["relation"], e["target"]))
            keys.add((e["target"], e["relation"], e["source"]))
        return keys

    def serialize(self) -> str:
        g = self._g
        lines = [f"QUESTION: {self.question}", ""]
        lines.append("ANCHOR ENTITIES (the entities the question names):")
        for a in self.anchors:
            lines.append(f"  - {g.label(a)}  (id={a}, initiative={initiative_of(a)})")
        lines.append("")
        lines.append("NODES IN SUBGRAPH (id | label | initiative):")
        for nid in self.node_ids():
            lines.append(f"  - {nid} | {g.label(nid)} | {initiative_of(nid)}")
        lines.append("")
        lines.append("EDGES IN SUBGRAPH (these are the ONLY connections you may use):")
        if not self.edges:
            lines.append("  (none)")
        for e in self.edges:
            loc = e.get("source_location") or "-"
            lines.append(
                f"  - {e['source']} --{e['relation']}[{e['confidence']}]--> {e['target']}"
                f"   | src_file={e.get('source_file', '-')} | loc={loc}"
            )
        if self.note:
            lines.append("")
            lines.append(f"EXTRACTOR NOTE: {self.note}")
        return "\n".join(lines)


# --------------------------------------------------------------------------- #
# Primitives
# --------------------------------------------------------------------------- #
def neighborhood(g: Graph, entity: str, depth: int = 1) -> SubGraph:
    """1-hop (or depth-hop) incident edges of one entity — the enumeration subgraph."""
    anchor = g.resolve(entity)
    frontier = {anchor}
    seen_nodes = {anchor}
    edges: list[dict] = []
    seen_edges: set[frozenset] = set()
    for _ in range(depth):
        nxt_frontier: set[str] = set()
        for node in frontier:
            for nb in g.adj[node]:
                k = frozenset((node, nb))
                if k not in seen_edges:
                    seen_edges.add(k)
                    edges.append(g.emeta[k])
                if nb not in seen_nodes:
                    seen_nodes.add(nb)
                    nxt_frontier.add(nb)
        frontier = nxt_frontier
    return SubGraph(question="", anchors=[anchor], edges=edges, _g=g)


def relate(g: Graph, a: str, b: str, cap: int = 2) -> SubGraph:
    """How two entities relate: direct inter-initiative edges + <=cap-hop hub paths.

    Returns BOTH:
      * every direct edge between any node of A's initiative and any node of B's initiative
        (the substantive "do these initiatives touch" signal), and
      * every simple path of length <= cap between the two named hub nodes (context).
    If both are empty the subgraph carries a 'disconnected' note — the honesty trigger:
    the reasoner must then say the graph records no connection, never invent one.

    Deliberately does NOT chase >2-hop links nor 2-hop co-references to a generic shared
    concept (both initiatives touching 'Aquaculture'): the WDB protocol itself treats a
    shared-generic-hub as a non-relationship, so surfacing it would manufacture noise.
    """
    a_id, b_id = g.resolve(a), g.resolve(b)
    ga, gb = initiative_of(a_id), initiative_of(b_id)
    edges: list[dict] = []
    seen: set[frozenset] = set()

    def add(e: dict) -> None:
        k = frozenset((e["source"], e["target"]))
        if k not in seen:
            seen.add(k)
            edges.append(e)

    # 1. direct edges between the two initiatives' node groups
    group_a = g.group(ga) if ga in INITIATIVES else {a_id}
    group_b = g.group(gb) if gb in INITIATIVES else {b_id}
    n_direct = 0
    for u in group_a:
        for v in group_b:
            e = g.edge(u, v)
            if e is not None:
                add(e)
                n_direct += 1

    # 2. <=cap-hop simple paths between the two named hubs (context)
    n_paths = 0
    for path in g.simple_paths(a_id, b_id, cap):
        n_paths += 1
        for i in range(len(path) - 1):
            add(g.edge(path[i], path[i + 1]))

    sg = SubGraph(question="", anchors=[a_id, b_id], edges=edges, _g=g)
    if not edges:
        sg.note = (
            f"NO direct edge between the {ga!r} and {gb!r} initiatives, and NO path of "
            f"<= {cap} hops between {g.label(a_id)} and {g.label(b_id)}. They are NOT "
            f"connected within the retrieved subgraph."
        )
    else:
        sg.note = (
            f"{n_direct} direct inter-initiative edge(s); {n_paths} hub-to-hub path(s) "
            f"of <= {cap} hops."
        )
    return sg


def bridges(g: Graph, entity: str, max_per_initiative: int = 4) -> SubGraph:
    """2-hop 'shared connector' paths from one entity to OTHER initiatives.

    For anchor A, find every 2-hop path  A --x1--> X --x2--> Y  where Y belongs to a
    DIFFERENT initiative than A (or A reaches Y directly). X is the shared thing (a tool,
    a place, a standard, a dataset) that explains *how* the two initiatives connect. Also
    keeps A's direct cross-initiative edges (e.g. shares_data_with).
    """
    anchor = g.resolve(entity)
    home = initiative_of(anchor)
    edges: list[dict] = []
    seen: set[frozenset] = set()
    per_init: dict[str, int] = {}

    def add(e: dict) -> None:
        k = frozenset((e["source"], e["target"]))
        if k not in seen:
            seen.add(k)
            edges.append(e)

    for x in sorted(g.adj[anchor]):
        x_init = initiative_of(x)
        # direct cross-initiative edge from the anchor
        if x_init not in (home, "shared", "other"):
            add(g.edge(anchor, x))
            continue
        # else x is a shared/own connector — look one more hop to a different initiative
        for y in sorted(g.adj[x]):
            if y == anchor:
                continue
            y_init = initiative_of(y)
            if y_init in (home, "shared", "other"):
                continue
            if per_init.get(y_init, 0) >= max_per_initiative:
                continue
            per_init[y_init] = per_init.get(y_init, 0) + 1
            add(g.edge(anchor, x))
            add(g.edge(x, y))

    sg = SubGraph(question="", anchors=[anchor], edges=edges, _g=g)
    reached = sorted({initiative_of(e["source"]) for e in edges} |
                     {initiative_of(e["target"]) for e in edges})
    reached = [r for r in reached if r not in (home, "shared", "other")]
    sg.note = f"shared-connector bridges from {g.label(anchor)} to initiatives: {reached}"
    return sg


def get_graph() -> Graph:
    nodes, links = load_graph(GRAPH_PATH)
    return Graph(nodes, links)
