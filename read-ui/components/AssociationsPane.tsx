import { useState } from "react";
import type { Association } from "@/lib/contract";
import { ConfidenceTag } from "./chips";
import { SourceLink } from "./source/SourceLink";
import { GraphViewer } from "./GraphViewer";
import { useSourceViewer } from "./source/SourceViewerProvider";
import styles from "./panes.module.scss";

interface AssociationsPaneProps {
  associations: Association[];
  globalNodeMap?: Map<string, { label: string; community: number; file_type?: string; source_file?: string }>;
}


/**
 * Full-width associations section — graph is the visual hero with a toggle to switch
 * to the traditional grouped list view. Simplified from the old cramped sidebar layout.
 */
export function AssociationsPane({ associations, globalNodeMap }: AssociationsPaneProps) {
  const { openSource } = useSourceViewer();
  const [viewMode, setViewMode] = useState<"graph" | "list">("graph");
  const [selectedNodeId, setSelectedNodeId] = useState<string | null>(null);

  const groups = groupByRelation(associations);

  return (
    <section className={styles.pane} aria-label="Graph associations">
      <div className={styles.paneHead}>
        <span className={styles.paneTitle}>Knowledge Graph</span>
        <span className={styles.count}>{associations.length} connections</span>
        
        {/* Toggle switch for Graph vs List view */}
        {associations.length > 0 && (
          <div className={styles.toggleWrap}>
            <button
              className={`${styles.toggleBtn} ${viewMode === "graph" ? styles.toggleActive : ""}`}
              onClick={() => setViewMode("graph")}
              aria-label="Switch to Graph View"
            >
              Graph
            </button>
            <button
              className={`${styles.toggleBtn} ${viewMode === "list" ? styles.toggleActive : ""}`}
              onClick={() => setViewMode("list")}
              aria-label="Switch to List View"
            >
              List
            </button>
          </div>
        )}
      </div>
      <p className={styles.paneSub}>How the answer&apos;s entities connect across the knowledge graph.</p>

      {associations.length === 0 ? (
        <div className={styles.empty}>No graph associations for this answer.</div>
      ) : viewMode === "graph" ? (
        <GraphViewer
          associations={associations}
          globalNodeMap={globalNodeMap}
          onSelectNode={setSelectedNodeId}
          selectedNodeId={selectedNodeId}
          onViewSource={openSource}
        />
      ) : (
        groups.map(([relation, edges]) => (
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
                  {e.source_file && <SourceLink path={e.source_file} icon="📄" label={fileName(e.source_file)} />}
                </span>
              </div>
            ))}
          </div>
        ))
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
  // most-connected relations first
  return [...map.entries()].sort((a, b) => b[1].length - a[1].length);
}

function fileName(p: string): string {
  return p.split("/").pop() || p;
}
