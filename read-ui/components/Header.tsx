import styles from "./header.module.scss";

export interface Health {
  ok: boolean;
  target: string;
  backend?: "live" | "replay";
  reranker_loaded?: boolean;
}

/** Slim app bar — brand + an honest status of the local API it's wired to. */
export function Header({
  health,
  onExploreGraph,
}: {
  health: Health | null;
  onExploreGraph?: () => void;
}) {
  return (
    <header className={styles.bar}>
      <div className={`wf-container ${styles.inner}`}>
        <div className={styles.brand}>
          <span className={styles.mark}>WDB</span>
          <span className={styles.brandText}>WorldFish Digital Brain</span>
        </div>
        <div className={styles.status} title={health ? `API: ${health.target}` : "checking API…"}>
          {onExploreGraph && (
            <button
              className={styles.exploreBtn}
              onClick={onExploreGraph}
              title="Explore full interactive knowledge graph"
            >
              🌐 Explore Graph
            </button>
          )}
          <span className={styles.metaLabel}>local · read-only</span>
          {health === null ? (
            <span className={styles.pill}>
              <span className={`${styles.dot} ${styles.dotUnknown}`} /> checking…
            </span>
          ) : health.ok ? (
            <span className={styles.pill}>
              <span className={`${styles.dot} ${styles.dotOk}`} />
              API · {health.backend ?? "up"}
            </span>
          ) : (
            <span className={styles.pill}>
              <span className={`${styles.dot} ${styles.dotDown}`} /> API offline
            </span>
          )}
        </div>
      </div>
    </header>
  );
}

