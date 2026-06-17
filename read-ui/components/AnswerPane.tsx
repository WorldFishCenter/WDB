import type { RouterAnswer } from "@/lib/contract";
import { ClaimCard } from "./ClaimCard";
import { FigureView } from "./FigureView";
import { RoutePosture } from "./RoutePosture";
import { Unanswered } from "./Unanswered";
import styles from "./panes.module.scss";

/**
 * The answer pane: the synthesized answer as a list of claims, each with its source TYPE visible
 * and its citation attached; any Mode-C figures; and — always, when present — the `unanswered`
 * list. Honesty is structural here: nothing on screen lacks a source, and what wasn't grounded
 * is shown as such.
 */
export function AnswerPane({ answer }: { answer: RouterAnswer }) {
  const { claims, figures, unanswered } = answer;

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
        <div className={styles.stack}>
          {claims.map((c, i) => (
            <ClaimCard key={i} claim={c} />
          ))}
        </div>
      ) : (
        <div className={styles.empty}>No grounded claims for this question — see what wasn’t grounded below.</div>
      )}

      {figures.length > 0 && (
        <>
          <h3 className={styles.subhead}>
            Figures <span className={styles.count}>{figures.length}</span>
          </h3>
          <div className={styles.stack}>
            {figures.map((f, i) => (
              <FigureView key={i} figure={f} />
            ))}
          </div>
        </>
      )}

      <Unanswered items={unanswered} />
    </section>
  );
}
