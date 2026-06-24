"use client";

import { useState } from "react";
import type { Association } from "@/lib/contract";
import { ConfidenceTag } from "./chips";
import { SourceLink } from "./source/SourceLink";
import { Icon } from "./Icon";
import { GraphView } from "./graph/GraphView";
import type { GraphJson, NodeMeta } from "@/lib/graphData";
import styles from "./panes.module.scss";

/**
 * The graph stage — the right, co-equal pane. It frames "how the answer's entities connect across
 * the knowledge graph": the merged `associations`, shown either as the live interactive map
 * (Cytoscape, the relevant subgraph — never the whole hairball) or as a grouped edge list. Every
 * edge carries its EXTRACTED/INFERRED provenance both in the list and in the map (solid vs dashed),
 * so the backend's honesty survives into the visualization.
 */
export function AssociationsPane({
  associations,
  graph,
  nodeMeta,
}: {
  associations: Association[];
  graph: GraphJson | null;
  nodeMeta: Map<string, NodeMeta>;
}) {
  const [view, setView] = useState<"graph" | "list">("graph");
  const hasData = associations.length > 0;

  return (
    <section className={styles.stage} aria-label="Knowledge graph">
      <div className={styles.stageHead}>
        <span className={styles.stageIcon}>
          <Icon name="graph" />
        </span>
        <span className={styles.stageTitle}>Knowledge graph</span>
        <div className={styles.stageHeadMeta}>
          <span className={styles.count}>
            {associations.length} {associations.length === 1 ? "connection" : "connections"}
          </span>
          {hasData && (
            <div className={styles.toggleWrap} role="tablist" aria-label="Graph view mode">
              <button
                role="tab"
                aria-selected={view === "graph"}
                className={`${styles.toggleBtn} ${view === "graph" ? styles.toggleActive : ""}`}
                onClick={() => setView("graph")}
              >
                Graph
              </button>
              <button
                role="tab"
                aria-selected={view === "list"}
                className={`${styles.toggleBtn} ${view === "list" ? styles.toggleActive : ""}`}
                onClick={() => setView("list")}
              >
                List
              </button>
            </div>
          )}
        </div>
      </div>

      {!hasData ? (
        <div className={styles.stageBody}>
          <div className={styles.stageEmpty}>
            <span className={styles.stageEmptyIcon}>
              <Icon name="graph" size={22} />
            </span>
            <p className={styles.stageEmptyText}>
              No graph relationships for this answer — it is computed from data. The query and rows
              are shown with the figure.
            </p>
          </div>
        </div>
      ) : view === "graph" ? (
        <div className={styles.stageBodyFlush}>
          <GraphView associations={associations} graph={graph} nodeMeta={nodeMeta} />
        </div>
      ) : (
        <div className={styles.stageBody}>
          <p className={styles.stageSub}>How the answer&apos;s entities connect across the knowledge graph.</p>
          {groupByRelation(associations).map(([relation, edges]) => (
            <div className={styles.relGroup} key={relation}>
              <div className={styles.relName}>
                {relation} · {edges.length}
              </div>
              {edges.map((e, i) => (
                <div className={styles.edge} key={`${e.source}-${e.target}-${i}`}>
                  <span className={styles.edgeNode}>{e.source}</span>
                  <span className={styles.edgeArrow} aria-hidden>
                    →
                  </span>
                  <span className={styles.edgeNode}>{e.target}</span>
                  <span className={styles.edgeMeta}>
                    {e.confidence && <ConfidenceTag confidence={e.confidence} />}
                    {e.source_file && <SourceLink path={e.source_file} icon="doc" label={fileName(e.source_file)} />}
                  </span>
                </div>
              ))}
            </div>
          ))}
        </div>
      )}
    </section>
  );
}

function groupByRelation(edges: Association[]): [string, Association[]][] {
  const map = new Map<string, Association[]>();
  for (const e of edges) {
    const key = e.relation || "related";
    (map.get(key) ?? map.set(key, []).get(key)!).push(e);
  }
  return [...map.entries()].sort((a, b) => b[1].length - a[1].length);
}

function fileName(p: string): string {
  return p.split("/").pop() || p;
}
