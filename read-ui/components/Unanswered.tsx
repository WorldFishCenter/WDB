import styles from "./panes.module.scss";

/**
 * The `unanswered` list — a FIRST-CLASS part of the answer, never hidden (§6 r4). When some of a
 * question is grounded and some isn't, this is what keeps the user from mistaking absence for a
 * complete answer.
 */
export function Unanswered({ items }: { items: string[] }) {
  if (!items || items.length === 0) return null;
  return (
    <section className={styles.unanswered} aria-label="Parts the knowledge base could not ground">
      <header className={styles.unansweredHead}>
        <span aria-hidden>⚠️</span>
        <span className={styles.unansweredTitle}>
          Not grounded · {items.length} {items.length === 1 ? "part" : "parts"}
        </span>
        <span className={styles.unansweredNote}>shown, never hidden</span>
      </header>
      <ul className={styles.unansweredList}>
        {items.map((u, i) => (
          <li key={i} className={styles.unansweredItem}>
            {u}
          </li>
        ))}
      </ul>
    </section>
  );
}
