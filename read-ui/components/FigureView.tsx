"use client";

import { useState } from "react";
import type { Figure, Row } from "@/lib/contract";
import { RowsTable } from "./Citation";
import styles from "./figure.module.scss";

/**
 * A Mode-C figure rendered as a simple bar chart — and, on demand, the EXACT query and rows
 * that produced it. The chart never invents: bars come straight from `figure.result`, labelled
 * by `spec.x`, measured by `spec.y`.
 */
export function FigureView({ figure }: { figure: Figure }) {
  const [showQuery, setShowQuery] = useState(false);

  const xKey = figure.spec.x;
  const yKey = figure.spec.y;
  const rows = figure.result || [];
  const bars = rows
    .map((r) => ({ label: String(r[xKey] ?? "—"), value: toNum(r[yKey]), raw: r }))
    .filter((b) => b.value !== null) as { label: string; value: number; raw: Row }[];
  const max = bars.reduce((m, b) => Math.max(m, b.value), 0) || 1;

  return (
    <figure className={styles.figure}>
      <figcaption className={styles.cap}>
        <span className={styles.capKind}>{figure.spec.kind} chart</span>
        <span className={styles.capAxes}>
          {prettify(yKey)} by {prettify(xKey)}
        </span>
        <button type="button" className={styles.toggle} onClick={() => setShowQuery((v) => !v)} aria-expanded={showQuery}>
          {showQuery ? "Hide query & rows" : "Show query & rows"}
        </button>
      </figcaption>

      <div className={styles.bars}>
        {bars.map((b, i) => (
          <div className={styles.barRow} key={i}>
            <div className={styles.barLabel} title={b.label}>
              {b.label}
            </div>
            <div className={styles.barTrack}>
              <div className={styles.bar} style={{ width: `${(b.value / max) * 100}%` }} />
            </div>
            <div className={styles.barValue}>{formatNum(b.value)}</div>
          </div>
        ))}
      </div>

      {showQuery && (
        <div className={styles.detail}>
          <pre className={styles.sql}>{figure.query}</pre>
          <RowsTable rows={rows} />
        </div>
      )}
    </figure>
  );
}

function toNum(v: unknown): number | null {
  const n = typeof v === "number" ? v : Number(v);
  return Number.isFinite(n) ? n : null;
}

function formatNum(n: number): string {
  return Number.isInteger(n) ? String(n) : n.toFixed(2);
}

function prettify(k: string): string {
  return k.replace(/_/g, " ");
}
