import type { Mode, Route } from "@/lib/contract";
import { ModeBadge } from "./chips";
import styles from "./panes.module.scss";

/**
 * Routing transparency: which modes the question was dispatched to (and the signal that selected
 * each), and which of them actually GROUNDED a claim/figure. Makes "fired but found nothing"
 * legible instead of silent.
 */
export function RoutePosture({ routes, grounded }: { routes: Route[]; grounded: Mode[] }) {
  if (routes.length === 0) return null;
  const groundedSet = new Set(grounded);
  return (
    <div className={styles.posture}>
      <div className={styles.postureTop}>Routed to {routes.length === 1 ? "1 mode" : `${routes.length} modes`}</div>
      {routes.map((r, i) => (
        <div className={styles.route} key={`${r.mode}-${i}`}>
          <ModeBadge mode={r.mode} />
          <span className={styles.routeReason}>{r.reason}</span>
          {groundedSet.has(r.mode) ? (
            <span className={styles.statusGrounded}>grounded</span>
          ) : (
            <span className={styles.statusEmpty}>no result</span>
          )}
        </div>
      ))}
    </div>
  );
}
