"use client";

import { useSourceViewer } from "./SourceViewerProvider";
import { Icon, type IconName } from "../Icon";
import styles from "./source.module.scss";

/**
 * A clickable citation source — opens the read-only viewer for the named note/doc. Every claim
 * on screen routes back to where it came from through one of these (or, for SQL/rows, the
 * inline reveal in the Mode-C citation). No un-sourced text.
 */
export function SourceLink({
  path,
  label,
  icon = "doc",
}: {
  path: string;
  label?: string;
  icon?: IconName;
}) {
  const { openSource } = useSourceViewer();
  if (!path) return null;
  return (
    <button type="button" className={styles.link} onClick={() => openSource(path)} title={`Open source: ${path}`}>
      <span className={styles.icon}>
        <Icon name={icon} />
      </span>
      <span className={styles.linkText}>{label || path}</span>
    </button>
  );
}
