"use client";

import { useMemo } from "react";
import { ConfidenceTag } from "./chips";
import { SourceLink } from "./source/SourceLink";
import { Icon } from "./Icon";
import { useExploration } from "@/lib/exploration";
import { type GraphJson, type NodeMeta, prettifyId } from "@/lib/graphData";
import styles from "./entity.module.scss";

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

interface Rel {
  other: string;
  outgoing: boolean;
  relation: string;
  confidence: "EXTRACTED" | "INFERRED" | "";
  sourceFile?: string;
}

/**
 * The reframed view: what the knowledge graph *records* about the clicked entity — its committed
 * relationships, grouped by relation, each with its EXTRACTED/INFERRED provenance and source. This
 * is deliberately NOT a generated answer: clicking a node reads the graph, it never fabricates
 * prose. Each related entity is itself clickable, so you navigate the brain by reading it.
 */
export function EntityView({
  entityId,
  graph,
  nodeMeta,
}: {
  entityId: string;
  graph: GraphJson | null;
  nodeMeta: Map<string, NodeMeta>;
}) {
  const { clearReframe, reframeTo, highlightNodes, clearHighlight } = useExploration();
  const meta = nodeMeta.get(entityId);
  const label = meta?.label || prettifyId(entityId);
  const labelFor = (id: string) => nodeMeta.get(id)?.label || prettifyId(id);

  const groups = useMemo(() => {
    if (!graph) return null;
    const rels: Rel[] = [];
    graph.links.forEach((l) => {
      if (l.source === entityId || l.target === entityId) {
        rels.push({
          other: l.source === entityId ? l.target : l.source,
          outgoing: l.source === entityId,
          relation: l.relation || "related",
          confidence: (l.confidence as Rel["confidence"]) || "EXTRACTED",
          sourceFile: l.source_file,
        });
      }
    });
    const map = new Map<string, Rel[]>();
    rels.forEach((r) => (map.get(r.relation) ?? map.set(r.relation, []).get(r.relation)!).push(r));
    return [...map.entries()].sort((a, b) => b[1].length - a[1].length);
  }, [graph, entityId]);

  const total = groups?.reduce((n, [, r]) => n + r.length, 0) ?? 0;

  return (
    <section className={styles.entity} aria-label={`Entity: ${label}`}>
      <button className={styles.back} onClick={() => clearReframe()}>
        <span aria-hidden>←</span> Back to the answer
      </button>

      <span className={styles.eyebrow}>Entity · from the graph</span>
      <h2 className={styles.name}>{label}</h2>
      <div className={styles.metaRow}>
        <span className={styles.metaChip}>{meta?.file_type || "concept"}</span>
        <span className={styles.metaText}>{COMMUNITY_NAMES[meta?.community ?? 9] || "—"}</span>
        {graph && (
          <span className={styles.metaText}>
            · {total} {total === 1 ? "relationship" : "relationships"}
          </span>
        )}
      </div>

      <p className={styles.note}>
        What the knowledge graph records about this entity — its committed relationships, not a
        generated answer. Inferred links are flagged. Click any related entity to follow it.
      </p>

      {!graph ? (
        <div className={styles.empty}>Loading the graph…</div>
      ) : total === 0 ? (
        <div className={styles.empty}>No recorded relationships for this entity.</div>
      ) : (
        groups!.map(([relation, rels]) => (
          <div className={styles.relGroup} key={relation}>
            <div className={styles.relName}>
              {relation} · {rels.length}
            </div>
            {rels.map((r, i) => (
              <button
                key={`${r.other}-${i}`}
                className={styles.relRow}
                onClick={() => reframeTo(r.other)}
                onMouseEnter={() => highlightNodes([r.other])}
                onMouseLeave={() => clearHighlight()}
                title={`Follow ${labelFor(r.other)}`}
              >
                <span className={styles.dir} aria-hidden>
                  {r.outgoing ? "→" : "←"}
                </span>
                <span className={styles.relTarget}>{labelFor(r.other)}</span>
                <span className={styles.relMeta}>
                  {r.confidence && <ConfidenceTag confidence={r.confidence} />}
                  {r.sourceFile && (
                    <span aria-hidden style={{ display: "inline-flex", color: "var(--wf-text-faint)" }}>
                      <Icon name="doc" size="0.95em" />
                    </span>
                  )}
                </span>
              </button>
            ))}
          </div>
        ))
      )}
    </section>
  );
}
