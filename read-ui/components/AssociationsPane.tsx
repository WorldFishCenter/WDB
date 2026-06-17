import type { Association } from "@/lib/contract";
import { ConfidenceTag } from "./chips";
import { SourceLink } from "./source/SourceLink";
import styles from "./panes.module.scss";

/**
 * The "how this connects to everything else" view — the graph edges around the answer's entities
 * (the merged `associations` payload). Grouped by relation; every edge shows its EXTRACTED/
 * INFERRED provenance and links to the note that stated it. This is the cross-initiative value
 * the graph exists for, surfaced alongside the answer.
 */
export function AssociationsPane({ associations }: { associations: Association[] }) {
  const groups = groupByRelation(associations);

  return (
    <section className={styles.pane} aria-label="Graph associations">
      <div className={styles.paneHead}>
        <span className={styles.paneTitle}>Associations</span>
        <span className={styles.count}>{associations.length}</span>
      </div>
      <p className={styles.paneSub}>How the answer’s entities connect across the knowledge graph.</p>

      {associations.length === 0 ? (
        <div className={styles.empty}>No graph associations for this answer.</div>
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
