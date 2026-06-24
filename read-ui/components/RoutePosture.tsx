import type { Mode, Route } from "@/lib/contract";
import { MODE_LABEL } from "@/lib/contract";
import styles from "./panes.module.scss";

/**
 * Routing transparency, quiet: which modes the question was dispatched to, and — flagged only when
 * it happens — any mode that fired but grounded nothing ("no result"). One muted line, not a card:
 * the answer leads, the plumbing recedes. The selecting signal is available on hover (title).
 */
export function RoutePosture({ routes, grounded }: { routes: Route[]; grounded: Mode[] }) {
  if (routes.length === 0) return null;
  const groundedSet = new Set(grounded);
  return (
    <div className={styles.routeStrip}>
      <span className={styles.routeLabel}>
        Routed across {routes.length} {routes.length === 1 ? "mode" : "modes"}
      </span>
      {routes.map((r, i) => (
        <span className={styles.routeItem} key={`${r.mode}-${i}`} title={`signal: ${r.reason}`}>
          <span className={`${styles.modeDot} ${styles[`dot${r.mode}`]}`} aria-hidden />
          {MODE_LABEL[r.mode]}
          {!groundedSet.has(r.mode) && <span className={styles.routeMiss}>no result</span>}
        </span>
      ))}
    </div>
  );
}
