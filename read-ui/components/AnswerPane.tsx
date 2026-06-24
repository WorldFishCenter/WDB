"use client";

import type { RouterAnswer, Claim, Mode } from "@/lib/contract";
import { citationA } from "@/lib/contract";
import { ClaimCard } from "./ClaimCard";
import { FigureView } from "./FigureView";
import { RoutePosture } from "./RoutePosture";
import { Unanswered } from "./Unanswered";
import { ConfidenceTag } from "./chips";
import { SourceLink } from "./source/SourceLink";
import { useExploration } from "@/lib/exploration";
import { claimNodeIds } from "@/lib/graphData";
import styles from "./panes.module.scss";

// Reading order: the prose answer (B) and the computed number (C) lead; the many graph-fact
// relationships (A) follow as a scannable list — the same relationships the graph stage maps.
const MODE_ORDER: Mode[] = ["B", "C", "A"];
const GROUP_TITLE: Record<Mode, string> = {
  A: "Graph facts",
  B: "Grounded passage",
  C: "Computed figure",
};

/**
 * The answer pane, flat: a quiet routing line, then one calm section per source mode — each a
 * plain header (the reference point) over flat, rail-marked claims. No cards-in-cards. Honesty is
 * structural: every claim shows its source TYPE (the section + rail) and its citation; inferred
 * links are flagged; what wasn't grounded is shown as such.
 */
export function AnswerPane({ answer }: { answer: RouterAnswer }) {
  const { claims, figures, unanswered } = answer;
  const { highlightNodes, clearHighlight } = useExploration();

  const grouped: Record<Mode, Claim[]> = { A: [], B: [], C: [] };
  claims.forEach((c) => grouped[c.mode]?.push(c));
  const activeModes = MODE_ORDER.filter((m) => grouped[m].length > 0);

  return (
    <section className={styles.pane} aria-label="Answer">
      <div className={styles.answerHead}>
        <h2 className={styles.answerTitle}>Answer</h2>
      </div>
      <RoutePosture routes={answer.routes} grounded={answer.modes_grounded} />

      {claims.length > 0 ? (
        activeModes.map((mode) => (
          <section className={styles.group} key={mode} aria-label={GROUP_TITLE[mode]}>
            <header className={styles.groupHead}>
              <span className={`${styles.modeDot} ${styles[`dot${mode}`]}`} aria-hidden />
              <span className={styles.groupTitle}>{GROUP_TITLE[mode]}</span>
              {grouped[mode].length > 1 && <span className={styles.groupCount}>{grouped[mode].length}</span>}
            </header>

            {mode === "A" ? (
              <ul className={styles.factList}>
                {grouped.A.map((c, i) => (
                  <FactRow key={i} claim={c} />
                ))}
              </ul>
            ) : (
              <div className={styles.claimStack}>
                {grouped[mode].map((c, i) => (
                  <div
                    key={i}
                    onMouseEnter={() => highlightNodes(claimNodeIds(c))}
                    onMouseLeave={() => clearHighlight()}
                  >
                    <ClaimCard claim={c} />
                  </div>
                ))}
              </div>
            )}
          </section>
        ))
      ) : (
        <div className={styles.empty}>
          No grounded claims for this question — see what wasn&apos;t grounded below.
        </div>
      )}

      {figures.length > 0 && (
        <section className={styles.group} aria-label="Figures">
          <header className={styles.groupHead}>
            <span className={`${styles.modeDot} ${styles.dotC}`} aria-hidden />
            <span className={styles.groupTitle}>Figures</span>
            {figures.length > 1 && <span className={styles.groupCount}>{figures.length}</span>}
          </header>
          <div className={styles.claimStack}>
            {figures.map((f, i) => (
              <FigureView key={i} figure={f} />
            ))}
          </div>
        </section>
      )}

      <Unanswered items={unanswered} />
    </section>
  );
}

/**
 * One Mode-A graph fact, compact and flat: the relationship text on a rail, with a quiet
 * provenance line. EXTRACTED is the baseline (implicit); INFERRED is flagged — amber rail + tag —
 * so a reasoned lead never reads as a hard fact. Hovering pulses the fact's nodes in the graph.
 */
function FactRow({ claim }: { claim: Claim }) {
  const { highlightNodes, clearHighlight } = useExploration();
  const isInferred = claim.citations.some((c) => citationA(c).confidence === "INFERRED");
  return (
    <li
      className={`${styles.factRow} ${isInferred ? styles.factRowInferred : ""}`}
      onMouseEnter={() => highlightNodes(claimNodeIds(claim))}
      onMouseLeave={() => clearHighlight()}
    >
      <span className={styles.factText}>{claim.text}</span>
      <span className={styles.factMeta}>
        {isInferred && <ConfidenceTag confidence="INFERRED" />}
        {claim.citations.map((c, i) => {
          const a = citationA(c);
          return a.source_file ? (
            <SourceLink key={i} path={a.source_file} icon="doc" label={fileName(a.source_file)} />
          ) : null;
        })}
      </span>
    </li>
  );
}

function fileName(p: string): string {
  return p.split("/").pop() || p;
}
