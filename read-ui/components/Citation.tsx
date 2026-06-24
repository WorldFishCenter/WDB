"use client";

import { useState } from "react";
import type { Citation, Claim, Mode, Row } from "@/lib/contract";
import { citationA, citationB, citationC } from "@/lib/contract";
import { ConfidenceTag } from "./chips";
import { SourceLink } from "./source/SourceLink";
import styles from "./citation.module.scss";

/** Render one citation in the NATIVE shape of its owning claim's mode. */
export function CitationView({ mode, citation }: { mode: Mode; citation: Citation }) {
  if (mode === "A") return <CiteA citation={citationA(citation)} />;
  if (mode === "B") return <CiteB citation={citationB(citation)} />;
  return <CiteC citation={citationC(citation)} />;
}

/** All of a claim's citations, stacked. */
export function CitationList({ claim }: { claim: Claim }) {
  return (
    <div className={styles.list}>
      {claim.citations.map((c, i) => (
        <CitationView key={i} mode={claim.mode} citation={c} />
      ))}
    </div>
  );
}

// ---- Mode A — the graph edge triple ----------------------------------------
function CiteA({ citation }: { citation: ReturnType<typeof citationA> }) {
  const triple = parseTriple(citation.locator);
  return (
    <div className={`${styles.cite} ${styles.citeA}`}>
      <div className={styles.citeHead}>
        <span className={styles.kind}>Graph edge</span>
        <ConfidenceTag confidence={citation.confidence} />
      </div>
      <div className={styles.triple}>
        {triple ? (
          <>
            <span className={styles.node}>{triple.source}</span>
            <span className={styles.rel}>{triple.relation}</span>
            <span className={styles.arrow} aria-hidden>
              →
            </span>
            <span className={styles.node}>{triple.target}</span>
          </>
        ) : (
          <code>{citation.locator}</code>
        )}
      </div>
      <div className={styles.provenance}>
        {citation.source_file && <SourceLink path={citation.source_file} icon="doc" />}
        {citation.note && <span className={styles.note}>{citation.note}</span>}
      </div>
    </div>
  );
}

// ---- Mode B — the verbatim passage quote -----------------------------------
function CiteB({ citation }: { citation: ReturnType<typeof citationB> }) {
  return (
    <div className={`${styles.cite} ${styles.citeB}`}>
      <div className={styles.citeHead}>
        <span className={styles.kind}>Verbatim quote</span>
        {citation.location && <span className={styles.location}>{citation.location}</span>}
      </div>
      <blockquote className={styles.quote}>“{citation.quote}”</blockquote>
      <div className={styles.provenance}>
        {citation.source_file && <SourceLink path={citation.source_file} icon="doc" label={fileName(citation.source_file)} />}
        {citation.note && <SourceLink path={citation.note} icon="note" label={fileName(citation.note)} />}
      </div>
      {citation.nodes.length > 0 && (
        <div className={styles.nodes}>
          <span className={styles.nodesLabel}>resolves to graph node(s):</span>
          {citation.nodes.map((n) => (
            <code key={n} className={styles.nodeChip}>
              {n}
            </code>
          ))}
        </div>
      )}
    </div>
  );
}

// ---- Mode C — the SQL + its result rows ------------------------------------
function CiteC({ citation }: { citation: ReturnType<typeof citationC> }) {
  const [open, setOpen] = useState(false);
  return (
    <div className={`${styles.cite} ${styles.citeC}`}>
      <div className={styles.citeHead}>
        <span className={styles.kind}>Computed — SQL + rows</span>
        <button type="button" className={styles.toggle} onClick={() => setOpen((v) => !v)} aria-expanded={open}>
          {open ? "Hide query" : "Show query & rows"}
        </button>
      </div>
      {open && (
        <div className={styles.computed}>
          <pre className={styles.sql}>{citation.sql}</pre>
          <RowsTable rows={citation.result} />
        </div>
      )}
      <div className={styles.provenance}>
        {citation.source_file && <SourceLink path={citation.source_file} icon="data" />}
        {citation.note && <span className={styles.note}>{citation.note}</span>}
      </div>
    </div>
  );
}

export function RowsTable({ rows, max = 25 }: { rows: Row[]; max?: number }) {
  if (!rows || rows.length === 0) return <p className={styles.note}>No rows.</p>;
  const cols = Object.keys(rows[0]);
  const shown = rows.slice(0, max);
  return (
    <div className={styles.tableWrap}>
      <table className={styles.table}>
        <thead>
          <tr>
            {cols.map((c) => (
              <th key={c}>{c}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {shown.map((r, i) => (
            <tr key={i}>
              {cols.map((c) => (
                <td key={c}>{formatCell(r[c])}</td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
      {rows.length > max && <p className={styles.note}>+ {rows.length - max} more rows</p>}
    </div>
  );
}

// ---- small helpers ---------------------------------------------------------
function parseTriple(locator: string): { source: string; relation: string; target: string } | null {
  const m = locator.match(/^(.*?)\s*--\s*(.*?)\s*-->\s*(.*)$/);
  if (!m) return null;
  return { source: m[1].trim(), relation: m[2].trim(), target: m[3].trim() };
}

function fileName(p: string): string {
  return p.split("/").pop() || p;
}

function formatCell(v: Row[string]): string {
  if (v === null || v === undefined) return "—";
  return String(v);
}
