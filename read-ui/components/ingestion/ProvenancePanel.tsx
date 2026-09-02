import type { HistoryEntry, Provenance } from "@/lib/ingestion/types";
import { STATE_META } from "@/lib/ingestion/states";
import s from "./ingestion.module.scss";

function fmt(iso: string): string {
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return iso;
  return d.toLocaleString(undefined, { dateStyle: "medium", timeStyle: "short" });
}

/**
 * The four PROTOCOL §8 provenance fields, stamped at submission (design §4). `contributor` (who
 * brought it into WDB) is shown distinct from `author` (who made the content) — the distinction the
 * future "your knowledge" lens depends on.
 */
export function ProvenancePanel({ provenance }: { provenance: Provenance }) {
  return (
    <div className={s.prov}>
      <Row k="Contributor" v={provenance.contributor} hint="who brought it into WDB" />
      <Row k="Author" v={provenance.author} hint="who made the underlying content" />
      <Row k="Captured at" v={fmt(provenance.captured_at)} mono />
      <Row k="Source" v={provenance.source_url} mono />
      <p className={s.provNote}>
        Stamped at submission and carried onto the file’s graph nodes (PROTOCOL §8). “Your knowledge”
        is later a filter over the one shared graph — never a per-user fork.
      </p>
    </div>
  );
}

function Row({ k, v, hint, mono }: { k: string; v: string; hint?: string; mono?: boolean }) {
  return (
    <div className={s.provRow}>
      <span className={s.provKey}>{k}</span>
      <span className={`${s.provVal} ${mono ? s.provValMono : ""}`}>
        {v}
        {hint && <span className={s.provNote} style={{ margin: 0 }}> — {hint}</span>}
      </span>
    </div>
  );
}

/** The append-only audit trail — who moved the contribution to each state, and when (design §8). */
export function HistoryTimeline({ history }: { history: HistoryEntry[] }) {
  return (
    <div className={s.history}>
      {history.map((h, i) => (
        <div key={i} className={s.histRow}>
          <span className={s.histDot} aria-hidden />
          <div className={s.histBody}>
            <div className={s.histState}>{STATE_META[h.state].label}</div>
            <div className={s.histMeta}>
              {h.actor} · {fmt(h.at)}
            </div>
            {h.note && <div className={s.histNote}>{h.note}</div>}
          </div>
        </div>
      ))}
    </div>
  );
}
