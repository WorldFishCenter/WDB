"use client";

/**
 * Client-side access to the committed knowledge graph (`graphify-out/graph.json`), fetched
 * read-only through the same-origin source route. The graph is used to (a) label the answer's
 * subgraph nodes with their real proper names and (b) expand a node to its real neighbours on
 * click. We never invent nodes or edges — expansion only ever surfaces edges that already exist
 * in the committed graph.
 */

import { useEffect, useMemo, useState } from "react";
import type { Association, Claim, Confidence } from "./contract";
import { citationA, citationB } from "./contract";

export interface GraphNode {
  id: string;
  label?: string;
  community?: number;
  file_type?: string;
  source_file?: string;
}

export interface GraphLink {
  source: string;
  target: string;
  relation?: string;
  confidence?: Confidence;
  source_file?: string;
  source_location?: string | null;
}

export interface GraphJson {
  nodes: GraphNode[];
  links: GraphLink[];
}

export interface NodeMeta {
  label: string;
  community: number;
  file_type?: string;
  source_file?: string;
}

/**
 * Fetch graph.json once and expose it + a fast id→meta lookup.
 *
 * `error` is not decoration. Every failure here used to be discarded — the `d.error` branch, the
 * `JSON.parse` throw and the network rejection all returned quietly — so a knowledge base that
 * could not be located rendered as a graph with no nodes, indistinguishable from a graph that
 * genuinely had none. The stage can still degrade to the edge list, but the reason is now
 * available to say out loud.
 */
export function useGraphData(): {
  graph: GraphJson | null;
  nodeMeta: Map<string, NodeMeta>;
  graphError: string | null;
} {
  const [graph, setGraph] = useState<GraphJson | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let alive = true;
    fetch("/api/source?path=graphify-out/graph.json")
      .then(async (r) => ({ ok: r.ok, body: await r.json() }))
      .then(({ ok, body }) => {
        if (!alive) return;
        if (!ok || !body || body.error) {
          // a 503 carries the KB-root message from lib/kbRoot.ts; anything else is the file
          setError(body?.error ?? "Could not load graphify-out/graph.json.");
          return;
        }
        if (!body.text) {
          setError("graphify-out/graph.json is empty.");
          return;
        }
        try {
          setGraph(JSON.parse(body.text) as GraphJson);
          setError(null);
        } catch (e) {
          setError(`graphify-out/graph.json is not valid JSON: ${(e as Error).message}`);
        }
      })
      .catch((e) => {
        if (alive) setError(`Could not reach the source route: ${(e as Error).message}`);
      });
    return () => {
      alive = false;
    };
  }, []);

  const nodeMeta = useMemo(() => {
    const map = new Map<string, NodeMeta>();
    graph?.nodes?.forEach((n) => {
      map.set(n.id, {
        label: n.label || prettifyId(n.id),
        community: typeof n.community === "number" ? n.community : 9,
        file_type: n.file_type,
        source_file: n.source_file,
      });
    });
    return map;
  }, [graph]);

  return { graph, nodeMeta, graphError: error };
}

/** A readable fallback label when graph.json hasn't loaded (or a node is missing from it). */
export function prettifyId(id: string): string {
  const s = id
    .replace(/^(shared_|ssf_research_|peskas_|data_harmonization_|fasa_|dta_)/, "")
    .replace(/_/g, " ")
    .trim();
  return s ? s.charAt(0).toUpperCase() + s.slice(1) : id;
}

export interface SubEdge {
  id: string;
  source: string;
  target: string;
  relation: string;
  confidence: Confidence;
  source_file?: string;
}

/**
 * The relevant subgraph for an answer: exactly the nodes and edges in its `associations` payload —
 * the neighbourhood around the answer's entities, never the whole 172-node graph (which would be a
 * hairball). Expansion (below) grows it from here on demand.
 */
export function subgraphFromAssociations(associations: Association[]): {
  nodeIds: Set<string>;
  edges: SubEdge[];
} {
  const nodeIds = new Set<string>();
  const edges: SubEdge[] = [];
  associations.forEach((a, i) => {
    if (!a.source || !a.target) return;
    nodeIds.add(a.source);
    nodeIds.add(a.target);
    edges.push({
      id: `e${i}:${a.source}->${a.target}:${a.relation || "related"}`,
      source: a.source,
      target: a.target,
      relation: a.relation || "related",
      confidence: a.confidence || "EXTRACTED",
      source_file: a.source_file,
    });
  });
  return { nodeIds, edges };
}

/**
 * The graph node id(s) a claim resolves to — used to pulse them in the graph when the claim is
 * hovered. Mode A: the edge's two endpoints (parsed from the triple locator). Mode B: the nodes
 * the passage resolves to. Mode C: none (a computed figure has no graph node).
 */
export function claimNodeIds(claim: Claim): string[] {
  if (claim.mode === "A") {
    const ids = new Set<string>();
    claim.citations.forEach((c) => {
      const m = citationA(c).locator.match(/^(.*?)\s*--\s*.*?\s*-->\s*(.*)$/);
      if (m) {
        ids.add(m[1].trim());
        ids.add(m[2].trim());
      }
    });
    return [...ids];
  }
  if (claim.mode === "B") {
    const ids = new Set<string>();
    claim.citations.forEach((c) => citationB(c).nodes.forEach((n) => ids.add(n)));
    return [...ids];
  }
  return [];
}

/** A node's real neighbours from the full graph that aren't already shown — the click-to-expand set. */
export function neighboursOf(
  nodeId: string,
  graph: GraphJson | null,
  shownNodeIds: Set<string>,
  shownEdgeKeys: Set<string>,
): { nodes: string[]; edges: SubEdge[] } {
  if (!graph) return { nodes: [], edges: [] };
  const newNodes = new Set<string>();
  const edges: SubEdge[] = [];
  graph.links.forEach((l, i) => {
    if (l.source !== nodeId && l.target !== nodeId) return;
    const key = `${l.source}->${l.target}:${l.relation || "related"}`;
    if (shownEdgeKeys.has(key)) return;
    const other = l.source === nodeId ? l.target : l.source;
    if (!shownNodeIds.has(other)) newNodes.add(other);
    edges.push({
      id: `x${i}:${key}`,
      source: l.source,
      target: l.target,
      relation: l.relation || "related",
      confidence: l.confidence || "EXTRACTED",
      source_file: l.source_file,
    });
  });
  return { nodes: [...newNodes], edges };
}
