import type { Mode, Confidence } from "@/lib/contract";
import { MODE_LABEL, MODE_BLURB } from "@/lib/contract";
import styles from "./chips.module.scss";

const MODE_CLASS: Record<Mode, string> = {
  A: styles.modeA,
  B: styles.modeB,
  C: styles.modeC,
};

/**
 * The source-TYPE chip — the at-a-glance honesty signal. Mode A = graph fact, B = grounded
 * passage, C = computed figure, each in its stable WorldFish colour.
 */
export function ModeBadge({ mode, withLabel = true }: { mode: Mode; withLabel?: boolean }) {
  return (
    <span className={`${styles.modeBadge} ${MODE_CLASS[mode]}`} title={MODE_BLURB[mode]}>
      <span className={styles.modeLetter}>{mode}</span>
      {withLabel && <span className={styles.modeText}>{MODE_LABEL[mode]}</span>}
    </span>
  );
}

/**
 * The provenance chip for a graph edge. INFERRED is marked DISTINCTLY (amber, explicit word):
 * an inferred edge must never read as a hard, stated fact.
 */
export function ConfidenceTag({ confidence }: { confidence: Confidence }) {
  if (confidence === "INFERRED") {
    return (
      <span className={`${styles.confTag} ${styles.inferred}`} title="Inferred edge — a reasoned link, not stated verbatim in the corpus. Treat as a lead, not a hard fact.">
        <span aria-hidden>◆</span> INFERRED
      </span>
    );
  }
  if (confidence === "EXTRACTED") {
    return (
      <span className={`${styles.confTag} ${styles.extracted}`} title="Extracted edge — stated in the corpus.">
        <span aria-hidden>✓</span> EXTRACTED
      </span>
    );
  }
  return null;
}
