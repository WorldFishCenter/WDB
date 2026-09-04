import type { RouterAnswer } from "@/lib/contract";
import { RoutePosture } from "./RoutePosture";
import { Icon } from "./Icon";
import styles from "./panes.module.scss";

/**
 * The panel for an answer that rendered no claim and no figure. There are two very different
 * reasons for that, and conflating them was a real wrong answer:
 *
 *   VERIFIED_NEGATIVE — the graph WAS consulted and records no connection. That is a correct
 *     answer ("no"), produced by Mode A's `not_connected` after checking for a direct edge and
 *     every ≤2-hop path. It must not read as a coverage failure.
 *   UNGROUNDED — no mode could ground anything: retrieval too thin, no table resolved, no
 *     entity matched. The knowledge base genuinely doesn't cover it.
 *
 * Both are honest; only one is a refusal. The distinction arrives as `answer.verdict`; the UI
 * used to infer it from three empty lists and always showed the refusal wording.
 */
export function Refusal({ answer }: { answer: RouterAnswer }) {
  const isVerifiedNegative = answer.verdict === "VERIFIED_NEGATIVE";

  const title = isVerifiedNegative
    ? "Checked — and the answer is no"
    : "The knowledge base doesn’t cover this";

  const lead = isVerifiedNegative
    ? "The graph was consulted and records no such connection: no direct edge, and no path of two hops or fewer. This is a verified negative, not missing coverage."
    : "No mode could ground an answer from the committed corpus, so the system returns nothing rather than inventing one. Here is exactly what it could not ground:";

  // Prefer the typed entries: each carries the refusal arm as a stable `code`, and Mode C's
  // disambiguation carries its candidate tables structurally instead of buried in prose.
  const details = answer.unanswered_detail ?? [];
  const items =
    details.length > 0
      ? details
      : answer.unanswered.map((text) => ({ text, code: undefined, candidates: [] as string[] }));

  return (
    <div className={styles.refusal}>
      <div className={styles.refusalIcon} aria-hidden>
        <Icon name={isVerifiedNegative ? "graph" : "search"} size={24} />
      </div>
      <h2 className={styles.refusalTitle}>{title}</h2>
      <p className={styles.refusalLead}>{lead}</p>

      {items.length > 0 && (
        <div className={styles.refusalReasons}>
          <div className={styles.refusalReasonsHead}>
            {isVerifiedNegative ? "What was checked" : "Not available"}
          </div>
          <ul className={styles.unansweredList} style={{ paddingLeft: 18 }}>
            {items.map((u, i) => (
              <li key={i} className={styles.unansweredItem}>
                {u.text}
                {u.candidates.length > 0 && (
                  <ul style={{ paddingLeft: 18, marginTop: 4 }}>
                    {u.candidates.map((c) => (
                      <li key={c}>
                        <code>{c}</code>
                      </li>
                    ))}
                  </ul>
                )}
              </li>
            ))}
          </ul>
        </div>
      )}

      <RoutePosture routes={answer.routes} grounded={answer.modes_grounded} />
    </div>
  );
}
