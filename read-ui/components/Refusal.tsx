import type { RouterAnswer } from "@/lib/contract";
import { RoutePosture } from "./RoutePosture";
import { Icon } from "./Icon";
import styles from "./panes.module.scss";

/**
 * A FULL refusal (answered: false, no claims, no figures) rendered honestly: the knowledge base
 * doesn't cover this. Never a blank screen, never a fabricated-looking answer — the system
 * refuses to invent, and the UI says so plainly, listing exactly what it could not ground.
 */
export function Refusal({ answer }: { answer: RouterAnswer }) {
  return (
    <div className={styles.refusal}>
      <div className={styles.refusalIcon} aria-hidden>
        <Icon name="search" size={24} />
      </div>
      <h2 className={styles.refusalTitle}>The knowledge base doesn’t cover this</h2>
      <p className={styles.refusalLead}>
        No mode could ground an answer from the committed corpus, so the system returns nothing
        rather than inventing one. Here is exactly what it could not ground:
      </p>

      {answer.unanswered.length > 0 && (
        <div className={styles.refusalReasons}>
          <div className={styles.refusalReasonsHead}>Not available</div>
          <ul className={styles.unansweredList} style={{ paddingLeft: 18 }}>
            {answer.unanswered.map((u, i) => (
              <li key={i} className={styles.unansweredItem}>
                {u}
              </li>
            ))}
          </ul>
        </div>
      )}

      <RoutePosture routes={answer.routes} grounded={answer.modes_grounded} />
    </div>
  );
}
