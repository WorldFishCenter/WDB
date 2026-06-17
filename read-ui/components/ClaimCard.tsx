import type { Claim } from "@/lib/contract";
import { ModeBadge } from "./chips";
import { CitationList } from "./Citation";
import styles from "./claim.module.scss";

/**
 * One claim: its source-TYPE badge, the synthesized/grounded text, and its native citation(s).
 * Faithful — the text is rendered exactly as the API returned it (including Mode A's inline
 * "[INFERRED — discount]" marker). No claim is shown without its citation.
 */
export function ClaimCard({ claim }: { claim: Claim }) {
  return (
    <article className={`${styles.card} ${styles[`mode${claim.mode}`]}`}>
      <div className={styles.head}>
        <ModeBadge mode={claim.mode} />
      </div>
      <p className={styles.text}>{claim.text}</p>
      <CitationList claim={claim} />
    </article>
  );
}
