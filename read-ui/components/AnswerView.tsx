import type { RouterAnswer } from "@/lib/contract";
import { AnswerPane } from "./AnswerPane";
import { AssociationsPane } from "./AssociationsPane";
import { Refusal } from "./Refusal";
import styles from "./answerview.module.scss";

/**
 * The dual-pane "passage + associations" view. A full refusal (nothing grounded) renders as an
 * honest refusal panel instead. Otherwise: the answer (claims + figures + unanswered) on the
 * left, the graph associations on the right.
 */
export function AnswerView({ answer }: { answer: RouterAnswer }) {
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
      <QuestionEcho question={answer.question} />
      <div className={styles.grid}>
        <div className={styles.left}>
          <AnswerPane answer={answer} />
        </div>
        <div className={styles.right}>
          <AssociationsPane associations={answer.associations} />
        </div>
      </div>
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
