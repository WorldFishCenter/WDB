import type { RouterAnswer } from "@/lib/contract";
import { ClaimsSection } from "./AnswerPane";
import { AssociationsPane } from "./AssociationsPane";
import { RoutePosture } from "./RoutePosture";
import { FigureView } from "./FigureView";
import { Unanswered } from "./Unanswered";
import { Refusal } from "./Refusal";
import styles from "./answerview.module.scss";

/**
 * Vertical-flow answer layout: question echo → route posture → full-width interactive graph →
 * summary stats bar → accordion-grouped claims → figures → unanswered.
 *
 * Replaces the old cramped two-pane grid with a single-column flow where every section gets
 * the full viewport width. The graph is the visual hero; claims are compact accordions.
 */
export function AnswerView({
  answer,
  globalNodeMap,
}: {
  answer: RouterAnswer;
  globalNodeMap?: Map<string, { label: string; community: number; file_type?: string; source_file?: string }>;
}) {
  const isFullRefusal = !answer.answered && answer.claims.length === 0 && answer.figures.length === 0;

  if (isFullRefusal) {
    return (
      <div className={styles.wrap}>
        <QuestionEcho question={answer.question} />
        <Refusal answer={answer} />
      </div>
    );
  }

  return (
    <div className={styles.wrap}>
      {/* ── Question Echo ── */}
      <QuestionEcho question={answer.question} />

      {/* ── Route Posture (compact, full-width) ── */}
      <RoutePosture routes={answer.routes} grounded={answer.modes_grounded} />

      {/* ── Interactive Graph (full-width hero) ── */}
      {answer.associations.length > 0 && (
        <section className={styles.section} aria-label="Graph associations">
          <AssociationsPane associations={answer.associations} globalNodeMap={globalNodeMap} />
        </section>
      )}

      {/* ── Claims Summary + Accordions ── */}
      {(answer.claims.length > 0 || answer.unanswered.length > 0) && (
        <section className={styles.section} aria-label="Claims">
          <ClaimsSection claims={answer.claims} />
        </section>
      )}

      {/* ── Figures ── */}
      {answer.figures.length > 0 && (
        <section className={styles.section} aria-label="Figures">
          <div className={styles.sectionHead}>
            <span className={styles.sectionTitle}>Figures</span>
            <span className={styles.sectionCount}>{answer.figures.length}</span>
          </div>
          <div className={styles.stack}>
            {answer.figures.map((f, i) => (
              <FigureView key={i} figure={f} />
            ))}
          </div>
        </section>
      )}

      {/* ── Unanswered ── */}
      <Unanswered items={answer.unanswered} />
    </div>
  );
}


function QuestionEcho({ question }: { question: string }) {
  return (
    <div className={styles.echo}>
      <span className={styles.echoLabel}>Question</span>
      <span className={styles.echoText}>{question}</span>
    </div>
  );
}
