"use client";

import { Fragment } from "react";
import type { RouterAnswer, Claim, Mode } from "@/lib/contract";
import { MODE_BLURB, citationA } from "@/lib/contract";
import { ClaimCard } from "./ClaimCard";
import { FigureView } from "./FigureView";
import { RoutePosture } from "./RoutePosture";
import { Unanswered } from "./Unanswered";
import { ModeBadge, ConfidenceTag } from "./chips";
import { SourceLink } from "./source/SourceLink";
import { useExploration } from "@/lib/exploration";
import { claimNodeIds } from "@/lib/graphData";
import styles from "./panes.module.scss";

// Reading order: the prose answer (B) and the computed number (C) lead; the many graph-fact
// relationships (A) follow as a scannable list — the same relationships the graph stage maps.
const MODE_ORDER: Mode[] = ["B", "C", "A"];

/**
 * The answer pane. Claims are grouped by source mode so the synthesized answer reads clearly:
 * verbatim passages (B) and computed figures (C) as full evidence cards, graph facts (A) as a
 * compact, scannable list. Honesty is structural — every claim shows its source TYPE and its
 * native citation; nothing on screen lacks a source; what wasn't grounded is shown as such.
 */
export function AnswerPane({ answer }: { answer: RouterAnswer }) {
  const { claims, figures, unanswered } = answer;
  const { highlightNodes, clearHighlight } = useExploration();

  const grouped: Record<Mode, Claim[]> = { A: [], B: [], C: [] };
  claims.forEach((c) => grouped[c.mode]?.push(c));
  const activeModes = MODE_ORDER.filter((m) => grouped[m].length > 0);

  return (
    <section className={styles.pane} aria-label="Answer">
      <div className={styles.paneHead}>
        <span className={styles.paneTitle}>Answer</span>
        <span className={styles.count}>
          {claims.length} {claims.length === 1 ? "claim" : "claims"}
        </span>
      </div>

      <RoutePosture routes={answer.routes} grounded={answer.modes_grounded} />

      {claims.length > 0 ? (
        activeModes.map((mode) => (
          <section className={styles.claimGroup} key={mode} aria-label={`${mode} claims`}>
            <header className={styles.claimGroupHead}>
              <ModeBadge mode={mode} />
              <span className={styles.count}>{grouped[mode].length}</span>
              <span className={styles.claimGroupBlurb}>{MODE_BLURB[mode]}</span>
            </header>

            {mode === "A" ? (
              <ul className={styles.factList}>
                {grouped.A.map((c, i) => (
                  <FactRow key={i} claim={c} />
                ))}
              </ul>
            ) : (
              <div className={styles.stack}>
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
        <section className={styles.claimGroup} aria-label="Figures">
          <header className={styles.claimGroupHead}>
            <span className={styles.paneTitle} style={{ fontSize: "var(--wf-text-body-lg)" }}>
              Figures
            </span>
            <span className={styles.count}>{figures.length}</span>
          </header>
          <div className={styles.stack}>
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
 * One Mode-A graph fact, compact: the relationship text, its EXTRACTED/INFERRED provenance, and a
 * link to the note that stated it. Faithful — the text is exactly as the API returned it (incl.
 * the inline "[INFERRED — discount]" marker); inferred rows also carry an amber rail so they never
 * read as hard facts.
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
      {claim.citations.map((c, i) => {
        const a = citationA(c);
        return (
          <Fragment key={i}>
            <span className={styles.factMeta}>
              {a.confidence && <ConfidenceTag confidence={a.confidence} />}
              {a.source_file && <SourceLink path={a.source_file} icon="doc" label={fileName(a.source_file)} />}
              {a.note && <span className={styles.factNote}>{a.note}</span>}
            </span>
          </Fragment>
        );
      })}
    </li>
  );
}

function fileName(p: string): string {
  return p.split("/").pop() || p;
}
