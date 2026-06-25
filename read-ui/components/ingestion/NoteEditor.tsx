"use client";

import { useState } from "react";
import type { ColumnEntry, DraftedNote, Provenance } from "@/lib/ingestion/types";
import { noteToMarkdown } from "@/lib/ingestion/note";
import s from "./ingestion.module.scss";

/**
 * Renders the drafted companion note in the PROTOCOL §6 shape, read-only or editable. Editable mode
 * is reused for BOTH gates: the contributor reviewing (UNDER_REVIEW) and the curator overriding
 * (CURATOR_OVERRIDE). A Structured / Markdown toggle shows the exact `<file>_dict.md`/`_context.md`
 * text that would be written to git — no hidden state.
 */
export function NoteEditor({
  note,
  provenance,
  editable = false,
  onChange,
}: {
  note: DraftedNote;
  provenance: Provenance;
  editable?: boolean;
  onChange?: (next: DraftedNote) => void;
}) {
  const [view, setView] = useState<"structured" | "markdown">("structured");
  const set = (patch: Partial<DraftedNote>) => onChange?.({ ...note, ...patch });

  return (
    <div className={s.note}>
      <div className={s.btnRow} style={{ justifyContent: "space-between", marginBottom: "var(--wf-space-4)" }}>
        <span className={s.noteFile}>📄 {note.filename}</span>
        <div className={s.viewToggle}>
          <button
            className={`${s.viewToggleBtn} ${view === "structured" ? s.viewToggleActive : ""}`}
            onClick={() => setView("structured")}
          >
            Structured
          </button>
          <button
            className={`${s.viewToggleBtn} ${view === "markdown" ? s.viewToggleActive : ""}`}
            onClick={() => setView("markdown")}
          >
            Markdown
          </button>
        </div>
      </div>

      {view === "markdown" ? (
        <pre className={s.markdown}>{noteToMarkdown(note, provenance)}</pre>
      ) : (
        <>
          {/* Title */}
          {editable ? (
            <div className={s.field}>
              <label className={s.label}>Title <span className={s.labelHint}>(the note’s # heading)</span></label>
              <input className={`${s.input} ${s.inputMono}`} value={note.title} onChange={(e) => set({ title: e.target.value })} />
            </div>
          ) : (
            <div className={s.noteTitle}># {note.title}</div>
          )}

          {/* Summary */}
          <Section label="Summary">
            {editable ? (
              <textarea className={s.textarea} value={note.summary} onChange={(e) => set({ summary: e.target.value })} />
            ) : (
              <p className={s.noteText}>{note.summary}</p>
            )}
          </Section>

          {note.template === "A" ? (
            <>
              <Section label="Grain — what one row is (domain terms)">
                {editable ? (
                  <textarea className={s.textarea} value={note.grain ?? ""} onChange={(e) => set({ grain: e.target.value })} />
                ) : (
                  <p className={s.noteText}>{note.grain}</p>
                )}
              </Section>

              <Section label="Columns — meaning + value domain">
                <ColumnsEditor
                  columns={note.columns ?? []}
                  editable={editable}
                  onChange={(columns) => set({ columns })}
                />
              </Section>
            </>
          ) : (
            <Section label="Key concepts / entities">
              <LinesEditor
                lines={note.keyConcepts ?? []}
                editable={editable}
                placeholder="One concept, region, method, or entity per line"
                onChange={(keyConcepts) => set({ keyConcepts })}
              />
            </Section>
          )}

          <Section label="Related files — the wiring (cross-initiative links first)">
            <LinesEditor
              lines={note.relatedFiles}
              editable={editable}
              mono
              placeholder="one related file per line — e.g. ../peskas/peskas_about.md (how it relates)"
              onChange={(relatedFiles) => set({ relatedFiles })}
            />
          </Section>

          {note.template === "A" && (note.notesCaveats || editable) && (
            <Section label="Notes / caveats">
              {editable ? (
                <textarea
                  className={s.textarea}
                  value={note.notesCaveats ?? ""}
                  onChange={(e) => set({ notesCaveats: e.target.value })}
                />
              ) : (
                <p className={s.noteText}>{note.notesCaveats}</p>
              )}
            </Section>
          )}
        </>
      )}
    </div>
  );
}

function Section({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div className={s.noteSection}>
      <div className={s.noteH}>{label}</div>
      {children}
    </div>
  );
}

/** Editable list of plain lines (key concepts, related files). View mode renders them as a list. */
function LinesEditor({
  lines,
  editable,
  mono,
  placeholder,
  onChange,
}: {
  lines: string[];
  editable: boolean;
  mono?: boolean;
  placeholder?: string;
  onChange: (lines: string[]) => void;
}) {
  if (editable) {
    return (
      <textarea
        className={`${s.textarea} ${mono ? s.inputMono : ""}`}
        value={lines.join("\n")}
        placeholder={placeholder}
        onChange={(e) => onChange(e.target.value.split("\n").map((l) => l.trim()).filter(Boolean))}
      />
    );
  }
  return (
    <ul className={s.bullets}>
      {lines.map((l, i) => (
        <li key={i} className={mono ? s.relatedItem : undefined}>
          {l}
        </li>
      ))}
    </ul>
  );
}

/** Editable Template-A columns — name / meaning / value domain per row. */
function ColumnsEditor({
  columns,
  editable,
  onChange,
}: {
  columns: ColumnEntry[];
  editable: boolean;
  onChange: (cols: ColumnEntry[]) => void;
}) {
  if (!editable) {
    return (
      <div className={s.columns}>
        {columns.map((c, i) => (
          <div key={i} className={s.colRow}>
            <span className={s.colName}>{c.name}</span>
            <span className={s.colMeaning}>{c.meaning}</span>
            <span className={s.colDomain}>{c.domain}</span>
          </div>
        ))}
      </div>
    );
  }
  const update = (i: number, patch: Partial<ColumnEntry>) =>
    onChange(columns.map((c, j) => (j === i ? { ...c, ...patch } : c)));
  return (
    <div className={s.columns}>
      {columns.map((c, i) => (
        <div key={i} className={s.colRow}>
          <input className={`${s.input} ${s.inputMono}`} value={c.name} placeholder="column_name" onChange={(e) => update(i, { name: e.target.value })} />
          <input className={s.input} value={c.meaning} placeholder="plain-English meaning" onChange={(e) => update(i, { meaning: e.target.value })} />
          <input className={s.input} value={c.domain} placeholder="value domain" onChange={(e) => update(i, { domain: e.target.value })} />
        </div>
      ))}
    </div>
  );
}
