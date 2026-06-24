"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import cytoscape, { type Core, type ElementDefinition } from "cytoscape";
import fcose from "cytoscape-fcose";
import type { Association } from "@/lib/contract";
import {
  type GraphJson,
  type NodeMeta,
  subgraphFromAssociations,
  neighboursOf,
  prettifyId,
} from "@/lib/graphData";
import { useSourceViewer } from "../source/SourceViewerProvider";
import { useExploration, type GraphBridge } from "@/lib/exploration";
import { Icon } from "../Icon";
import styles from "./graph.module.scss";

// Register the fcose layout once (idempotent-guarded for HMR / double-import).
let fcoseRegistered = false;
if (!fcoseRegistered) {
  try {
    cytoscape.use(fcose);
    fcoseRegistered = true;
  } catch {
    /* already registered */
  }
}

// Cytoscape paints to canvas and can't read CSS variables — mirror the design tokens here.
const C = {
  bgNode: "#1c2f3b",
  bgNodeSeed: "#103a48",
  borderNode: "rgba(255,255,255,0.18)",
  borderSeed: "rgba(87,179,209,0.55)",
  accent: "#57b3d1",
  accentStrong: "#8fd1e4",
  textNode: "#cbd5e1",
  textSeed: "#dbe4ee",
  outline: "#00050a",
  edge: "rgba(255,255,255,0.16)",
  edgeArrow: "rgba(255,255,255,0.30)",
  inferred: "#f3bd5e",
  inferredLine: "rgba(243,189,94,0.5)",
};

const COMMUNITY_NAMES: Record<number, string> = {
  0: "Peskas Platform & Scaling",
  1: "Digital Transformation Accelerator",
  2: "SSF Data Harmonization",
  3: "WIO Harmonized Catch/Effort",
  4: "FASA Global Scaling",
  5: "FASA Feed Formulation",
  6: "Timor-Leste Nutrition",
  7: "PondCube Water Quality",
  8: "CGIAR Data Ecosystem",
  9: "General knowledge",
};

interface SelectedNode {
  id: string;
  label: string;
  fileType?: string;
  community: number;
  sourceFile?: string;
  degree: number;
  expandable: number; // neighbours in the full graph not yet shown
}

interface GraphViewProps {
  associations: Association[];
  graph: GraphJson | null;
  nodeMeta: Map<string, NodeMeta>;
}

// Cast at the boundary: Cytoscape validates these style strings at runtime; the per-property
// canvas types add no safety here.
const CY_STYLE = ([
  {
    selector: "node",
    style: {
      "background-color": C.bgNode,
      "border-width": 1.5,
      "border-color": C.borderNode,
      width: "mapData(deg, 1, 10, 16, 40)",
      height: "mapData(deg, 1, 10, 16, 40)",
      label: "",
      color: C.textNode,
      "font-size": 9,
      "font-weight": 600,
      "text-valign": "bottom",
      "text-halign": "center",
      "text-margin-y": 5,
      "text-wrap": "ellipsis",
      "text-max-width": "104px",
      "text-outline-width": 2.6,
      "text-outline-color": C.outline,
      "min-zoomed-font-size": 7,
      "transition-property": "background-color, border-color, opacity, width, height",
      "transition-duration": 180,
    },
  },
  {
    selector: "node.seed",
    style: { "background-color": C.bgNodeSeed, "border-color": C.borderSeed, color: C.textSeed },
  },
  // Labels only where they help — hubs / expanded / selected / hovered (.showlabel) / pulsed.
  // Everything else stays an unlabelled dot until hovered, so the map never reads as a word-cloud.
  {
    selector: "node.lbl, node:selected, node.pulse, node.showlabel",
    style: { label: "data(label)" },
  },
  {
    selector: "node:selected",
    style: {
      "background-color": C.accent,
      "border-color": C.accentStrong,
      "border-width": 3,
      color: "#f6f9fc",
      "text-outline-color": C.outline,
      "z-index": 999,
    },
  },
  { selector: "node.faded", style: { opacity: 0.16 } },
  // Hover-pulse from the answer pane — a teal halo that pops even over faded context.
  {
    selector: "node.pulse",
    style: {
      opacity: 1,
      "border-color": C.accentStrong,
      "border-width": 3,
      "overlay-color": C.accent,
      "overlay-opacity": 0.28,
      "overlay-padding": 7,
      "z-index": 1000,
    },
  },
  {
    selector: "edge",
    style: {
      width: 1.5,
      "line-color": C.edge,
      "target-arrow-color": C.edgeArrow,
      "target-arrow-shape": "triangle",
      "arrow-scale": 0.85,
      "curve-style": "bezier",
      opacity: 0.85,
      "transition-property": "line-color, opacity, width",
      "transition-duration": 180,
    },
  },
  {
    selector: 'edge[confidence = "INFERRED"]',
    style: {
      "line-style": "dashed",
      "line-color": C.inferredLine,
      "target-arrow-color": C.inferred,
      opacity: 0.6,
    },
  },
  {
    selector: "edge.hl",
    style: { "line-color": C.accent, "target-arrow-color": C.accent, width: 2.4, opacity: 1, "z-index": 998 },
  },
  {
    selector: 'edge[confidence = "INFERRED"].hl',
    style: { "line-color": C.inferred, "target-arrow-color": C.inferred },
  },
  { selector: "edge.faded", style: { opacity: 0.07 } },
] as unknown) as cytoscape.StylesheetJson;

export function GraphView({ associations, graph, nodeMeta }: GraphViewProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const cyRef = useRef<Core | null>(null);
  const { openSource } = useSourceViewer();
  const { focusEntity, reframeTo, clearReframe, registerGraph } = useExploration();
  const [selected, setSelected] = useState<SelectedNode | null>(null);

  // reframeTo/clearReframe are stable, but the tap handler is bound once — read them via refs.
  const reframeRef = useRef(reframeTo);
  reframeRef.current = reframeTo;
  const clearReframeRef = useRef(clearReframe);
  clearReframeRef.current = clearReframe;

  // Stable ids of what's currently rendered, for computing expansions.
  const shownNodes = useRef<Set<string>>(new Set());
  const shownEdges = useRef<Set<string>>(new Set());

  const seed = useMemo(() => subgraphFromAssociations(associations), [associations]);

  // The Cytoscape tap handler is bound once at mount, so it would capture the initial-render
  // graph/nodeMeta (null / empty — graph.json loads after mount). Route both through refs so
  // select + expand always read the latest values.
  const graphRef = useRef(graph);
  graphRef.current = graph;
  const nodeMetaRef = useRef(nodeMeta);
  nodeMetaRef.current = nodeMeta;

  const labelFor = (id: string) => nodeMetaRef.current.get(id)?.label || prettifyId(id);

  // ---- init Cytoscape once -------------------------------------------------
  useEffect(() => {
    if (!containerRef.current || cyRef.current) return;
    const cy = cytoscape({
      container: containerRef.current,
      style: CY_STYLE,
      minZoom: 0.2,
      maxZoom: 2.5,
    });
    cyRef.current = cy;
    // Dev-only debug handle (stripped from production builds) — used by the CDP interaction test.
    if (process.env.NODE_ENV !== "production") {
      (window as Window & { __cy?: Core }).__cy = cy;
    }

    // Clicking a node reframes the whole view to it (shared state); clicking empty space clears.
    cy.on("tap", "node", (evt) => reframeRef.current(evt.target.id()));
    cy.on("tap", (evt) => {
      if (evt.target === cy) clearReframeRef.current();
    });
    // Reveal labels for the hovered node + its neighbours, so the local area is readable on demand.
    cy.on("mouseover", "node", (evt) => evt.target.closedNeighborhood().addClass("showlabel"));
    cy.on("mouseout", "node", (evt) => evt.target.closedNeighborhood().removeClass("showlabel"));

    return () => {
      cy.destroy();
      cyRef.current = null;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // ---- (re)build the subgraph when the answer changes ----------------------
  useEffect(() => {
    const cy = cyRef.current;
    if (!cy) return;

    const degree: Record<string, number> = {};
    seed.edges.forEach((e) => {
      degree[e.source] = (degree[e.source] || 0) + 1;
      degree[e.target] = (degree[e.target] || 0) + 1;
    });

    const els: ElementDefinition[] = [];
    shownNodes.current = new Set();
    shownEdges.current = new Set();

    // Label hubs by default (and everything when the subgraph is small); the rest reveal on hover.
    const labelAll = seed.nodeIds.size <= 14;
    seed.nodeIds.forEach((id) => {
      shownNodes.current.add(id);
      const major = labelAll || (degree[id] || 0) >= 3;
      els.push({
        data: { id, label: labelFor(id), deg: Math.min(degree[id] || 1, 10) },
        classes: major ? "seed lbl" : "seed",
      });
    });
    seed.edges.forEach((e) => {
      shownEdges.current.add(`${e.source}->${e.target}:${e.relation}`);
      els.push({ data: { id: e.id, source: e.source, target: e.target, relation: e.relation, confidence: e.confidence } });
    });

    cy.batch(() => {
      cy.elements().remove();
      cy.add(els);
    });
    clearVisual();
    runLayout(false);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [seed, nodeMeta]);

  // ---- selection is driven by the shared focusEntity (single source of truth) --------------
  useEffect(() => {
    if (!cyRef.current) return;
    if (focusEntity) applyFocus(focusEntity);
    else clearVisual();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [focusEntity]);

  // ---- register the hover-pulse bridge the answer pane drives ------------------------------
  useEffect(() => {
    const bridge: GraphBridge = {
      highlight: (ids) => {
        const cy = cyRef.current;
        if (!cy) return;
        cy.batch(() => {
          cy.nodes().removeClass("pulse");
          ids.forEach((id) => {
            const n = cy.getElementById(id);
            if (!n.empty()) n.addClass("pulse");
          });
        });
      },
      clearHighlight: () => cyRef.current?.nodes().removeClass("pulse"),
    };
    registerGraph(bridge);
    return () => registerGraph(null);
  }, [registerGraph]);

  // ---- keep the canvas sized to its container ------------------------------
  useEffect(() => {
    const el = containerRef.current;
    const cy = cyRef.current;
    if (!el || !cy) return;
    const ro = new ResizeObserver(() => {
      cy.resize();
    });
    ro.observe(el);
    return () => ro.disconnect();
  }, []);

  function runLayout(animate: boolean) {
    const cy = cyRef.current;
    if (!cy || cy.elements().length === 0) return;
    const reduce =
      typeof window !== "undefined" && window.matchMedia?.("(prefers-reduced-motion: reduce)").matches;
    cy.layout({
      name: "fcose",
      animate: animate && !reduce,
      animationDuration: 360,
      fit: true,
      padding: 36,
      nodeSeparation: 95,
      idealEdgeLength: 95,
      nodeRepulsion: 6500,
      gravity: 0.28,
      quality: "default",
      randomize: true,
    } as unknown as cytoscape.LayoutOptions).run();
  }

  function countExpandable(id: string): number {
    return neighboursOf(id, graphRef.current, shownNodes.current, shownEdges.current).nodes.length;
  }

  function applyFocus(id: string) {
    const cy = cyRef.current;
    if (!cy) return;
    const node = cy.getElementById(id);
    // The entity may not be in the current subgraph (e.g. reframed from the entity view) — the
    // left pane still shows it; the graph simply has nothing to select.
    if (node.empty()) {
      clearVisual();
      return;
    }

    cy.elements().unselect();
    node.select();

    // Light the node + its edges; dim the rest (the "active region" reads against context).
    const connected = node.closedNeighborhood();
    cy.elements().addClass("faded");
    connected.removeClass("faded");
    node.connectedEdges().removeClass("faded").addClass("hl");

    const meta = nodeMetaRef.current.get(id);
    setSelected({
      id,
      label: labelFor(id),
      fileType: meta?.file_type,
      community: meta?.community ?? 9,
      sourceFile: meta?.source_file,
      degree: node.degree(false),
      expandable: countExpandable(id),
    });
  }

  function clearVisual() {
    const cy = cyRef.current;
    if (!cy) return;
    cy.elements().unselect().removeClass("faded").removeClass("hl");
    setSelected(null);
  }

  function expand(id: string) {
    const cy = cyRef.current;
    if (!cy) return;
    const { nodes, edges } = neighboursOf(id, graphRef.current, shownNodes.current, shownEdges.current);
    if (nodes.length === 0 && edges.length === 0) return;

    cy.batch(() => {
      nodes.forEach((nid) => {
        if (shownNodes.current.has(nid)) return;
        shownNodes.current.add(nid);
        // Expanded nodes were asked for explicitly — label them.
        cy.add({ data: { id: nid, label: labelFor(nid), deg: 2 }, classes: "context lbl" });
      });
      edges.forEach((e) => {
        const key = `${e.source}->${e.target}:${e.relation}`;
        if (shownEdges.current.has(key)) return;
        // Only add an edge once both endpoints exist on the canvas.
        if (!shownNodes.current.has(e.source) || !shownNodes.current.has(e.target)) return;
        shownEdges.current.add(key);
        cy.add({ data: { id: e.id, source: e.source, target: e.target, relation: e.relation, confidence: e.confidence } });
      });
    });
    runLayout(true);
    // refresh the inspector's remaining-expandable count + reselect
    setSelected((s) => (s && s.id === id ? { ...s, expandable: countExpandable(id), degree: cy.getElementById(id).degree(false) } : s));
  }

  const zoomBy = (factor: number) => {
    const cy = cyRef.current;
    if (!cy) return;
    cy.zoom({ level: cy.zoom() * factor, renderedPosition: { x: cy.width() / 2, y: cy.height() / 2 } });
  };
  const fit = () => cyRef.current?.fit(undefined, 36);

  return (
    <div className={styles.graph}>
      <div ref={containerRef} className={styles.canvas} />

      <div className={styles.legend} aria-hidden>
        <div className={styles.legendRow}>
          <span className={`${styles.legendSwatch} ${styles.swatchExtracted}`} /> Extracted edge
        </div>
        <div className={styles.legendRow}>
          <span className={`${styles.legendSwatch} ${styles.swatchInferred}`} /> Inferred — a lead
        </div>
      </div>

      <div className={styles.controls}>
        <button onClick={() => zoomBy(1.25)} title="Zoom in" aria-label="Zoom in">+</button>
        <button onClick={() => zoomBy(0.8)} title="Zoom out" aria-label="Zoom out">−</button>
        <button onClick={fit} title="Fit to view" aria-label="Fit to view">⤢</button>
      </div>

      {!selected && <div className={styles.hint}>Click a node to inspect · expand its connections</div>}

      {selected && (
        <div className={styles.inspector} role="region" aria-label="Selected node">
          <div className={styles.inspectorHead}>
            <span className={styles.inspectorTitle}>{selected.label}</span>
            <button className={styles.inspectorClose} onClick={() => clearReframe()} aria-label="Clear selection">
              ✕
            </button>
          </div>
          <div className={styles.inspectorMeta}>
            <span className={styles.metaChip}>{selected.fileType || "concept"}</span>
            <span className={styles.metaText}>{COMMUNITY_NAMES[selected.community] || `Community ${selected.community}`}</span>
            <span className={styles.metaText}>· {selected.degree} shown</span>
          </div>
          <div className={styles.inspectorActions}>
            <button
              className={styles.action}
              onClick={() => expand(selected.id)}
              disabled={selected.expandable === 0}
              title={selected.expandable === 0 ? "All connections already shown" : "Add this node's connections"}
            >
              <Icon name="graph" size="0.95em" />
              {selected.expandable > 0 ? `Expand (+${selected.expandable})` : "Fully expanded"}
            </button>
            {selected.sourceFile && (
              <button className={`${styles.action} ${styles.actionGhost}`} onClick={() => openSource(selected.sourceFile!)}>
                <Icon name="doc" size="0.95em" />
                Source note
              </button>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
