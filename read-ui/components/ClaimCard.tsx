import type { Claim } from "@/lib/contract";
import { CitationList } from "./Citation";
import styles from "./claim.module.scss";

/**
 * One claim, flat: a thin mode-coloured left rail, the statement, and its native citation(s)
 * inline beneath — no cards, no nested boxes. The owning mode group already names the source
 * type, so the claim doesn't repeat a badge. Faithful: the text is exactly as the API returned it.
 */
export function ClaimCard({ claim }: { claim: Claim }) {
  return (
    <article className={`${styles.claim} ${styles[`rail${claim.mode}`]}`}>
      <p className={styles.text}>{claim.text}</p>
      <CitationList claim={claim} />
    </article>
  );
}
