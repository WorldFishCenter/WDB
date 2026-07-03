"use client";

import { useRef, useState } from "react";
import { IngestionHeader } from "@/components/ingestion/IngestionHeader";
import { GateBanner } from "@/components/ingestion/GateBanner";
import { OfflineBanner } from "@/components/ingestion/OfflineBanner";
import { StatePill } from "@/components/ingestion/StatePill";
import { StateTrack } from "@/components/ingestion/StateTrack";
import { NoteEditor } from "@/components/ingestion/NoteEditor";
import { ProvenancePanel, HistoryTimeline } from "@/components/ingestion/ProvenancePanel";
import { useIngestion } from "@/lib/ingestion/store";
import type { Phase1Format, Submission, SubmissionInput } from "@/lib/ingestion/types";
import s from "@/components/ingestion/ingestion.module.scss";

const INITIATIVES = [
  "peskas",
  "fasa",
  "data_harmonization",
  "digital_transformation_accelerator",
  "ssf_research",
  "civ-kb",
];

// Demo samples carry REAL bytes so the live pipeline actually runs (the tabular one is a tidy CSV
// the enricher fills with real value domains).
const SAMPLES: { filename: string; format: Phase1Format; content: string }[] = [
  {
    filename: "kenya_yield_2025.csv",
    format: "tabular",
    content:
      "plot_id,harvest_date,yield_kg,variety\n" +
      "P001,2025-02-14,42.5,DK8031\nP002,2025-03-02,38.1,H614\nP003,2025-03-20,51.7,DK8031\n" +
      "P004,2025-04-01,29.4,Pioneer\nP005,2025-04-12,47.0,H614\nP006,2025-05-03,33.8,DK8031\n",
  },
  { filename: "aquaculture_brief.md", format: "doc", content: "# Aquaculture brief\n\nA short brief for the initiative.\n" },
  { filename: "mombasa_market_survey.pdf", format: "pdf", content: "%PDF-1.4 placeholder survey bytes\n" },
];

function inferFormat(filename: string): Phase1Format | "later" | null {
  const ext = filename.toLowerCase().match(/\.[^.]+$/)?.[0] ?? "";
  if ([".csv", ".xlsx", ".xls"].includes(ext)) return "tabular";
  if (ext === ".pdf") return "pdf";
  if ([".md", ".txt", ".docx"].includes(ext)) return "doc";
  if ([".mp4", ".mov", ".png", ".jpg", ".jpeg", ".svg"].includes(ext)) return "later";
  return null;
}

function humanSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${Math.round(bytes / 1024)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

export default function ContributePage() {
  const { submissions, backendOnline, error, submit } = useIngestion();
  const [selectedId, setSelectedId] = useState<string | null>(null);

  // The server already scopes the list to this contributor.
  const mine = submissions;
  const selected = mine.find((x) => x.id === selectedId) ?? null;

  return (
    <>
      <IngestionHeader role="contributor" />
      <main className={`wf-container ${s.page}`}>
        <div className={s.pageHead}>
          <h1 className={s.pageTitle}>Add to the shared knowledge base</h1>
          <p className={s.pageSub}>
            Upload a file and approve the companion note the enricher drafts. Nothing goes live until a
            curator signs off.
          </p>
        </div>

        {!backendOnline && <OfflineBanner />}
        {error && (
          <div className={`${s.notice} ${s.noticeRejected}`} style={{ marginBottom: "var(--wf-space-5)" }}>
            <span className={s.noticeIcon}>⚠</span>
            <div>
              <div className={s.noticeTitle}>Action refused</div>
              <div className={s.noticeBody}>{error}</div>
            </div>
          </div>
        )}

        <div className={s.gateWrap}>
          <GateBanner emphasis="contributor" />
        </div>

        <div className={s.split}>
          <div className={s.col}>
            <SubmitCard
              disabled={!backendOnline}
              onSubmit={async (input, bytes) => {
                const sub = await submit(input, bytes);
                if (sub) setSelectedId(sub.id);
              }}
            />
            <SubmissionList mine={mine} selectedId={selectedId} onSelect={setSelectedId} />
          </div>

          <div className={s.col}>
            {selected ? (
              <DetailPanel key={selected.id} submission={selected} />
            ) : (
              <div className={s.detailHint}>
                <div className={s.emptyIcon}>📄</div>
                Select one of your submissions to see its drafted note, provenance, and status — or
                upload a new file to start.
              </div>
            )}
          </div>
        </div>
      </main>
    </>
  );
}

// ───────────────────────────────────────────────────────────── submit card
function SubmitCard({
  onSubmit,
  disabled,
}: {
  onSubmit: (input: SubmissionInput, bytes: Blob) => void;
  disabled?: boolean;
}) {
  const fileRef = useRef<HTMLInputElement>(null);
  const [file, setFile] = useState<{ filename: string; format: Phase1Format; sizeLabel: string; blob: Blob } | null>(null);
  const [unsupported, setUnsupported] = useState<string | null>(null);
  const [initiative, setInitiative] = useState(INITIATIVES[0]);
  const [author, setAuthor] = useState("");
  const [sourceUrl, setSourceUrl] = useState("");

  function chooseBlob(filename: string, blob: Blob) {
    const fmt = inferFormat(filename);
    if (fmt === "later") {
      setUnsupported("Video, images, and URLs come in a later phase — Phase 1 is PDF, tabular, and docs.");
      setFile(null);
      return;
    }
    if (!fmt) {
      setUnsupported("Unsupported file type. Phase 1 accepts PDF, tabular (.csv/.xlsx), and docs (.md/.txt/.docx).");
      setFile(null);
      return;
    }
    setUnsupported(null);
    setFile({ filename, format: fmt, sizeLabel: humanSize(blob.size), blob });
  }

  function onPick(e: React.ChangeEvent<HTMLInputElement>) {
    const f = e.target.files?.[0];
    if (f) chooseBlob(f.name, f);
  }

  function doSubmit() {
    if (!file) return;
    onSubmit(
      {
        filename: file.filename,
        format: file.format,
        sizeLabel: file.sizeLabel,
        initiative,
        author: author.trim(),
        source_url: sourceUrl.trim(),
      },
      file.blob,
    );
    setFile(null);
    setAuthor("");
    setSourceUrl("");
    if (fileRef.current) fileRef.current.value = "";
  }

  return (
    <div className={`${s.card} ${s.cardPrimary}`}>
      <div className={s.cardHead}>
        <span className={s.cardTitle}>Submit a file</span>
        <span className={s.cardKicker}>Phase 1 formats</span>
      </div>
      <div className={s.cardBody}>
        <input ref={fileRef} type="file" hidden onChange={onPick} />
        <div
          className={`${s.drop} ${file ? s.dropActive : ""}`}
          onClick={() => fileRef.current?.click()}
          role="button"
          tabIndex={0}
          onKeyDown={(e) => (e.key === "Enter" || e.key === " ") && fileRef.current?.click()}
        >
          {file ? (
            <div className={s.dropChosen}>📄 {file.filename} · {file.sizeLabel}</div>
          ) : (
            <>
              <div className={s.dropIcon}>⤓</div>
              <div className={s.dropTitle}>Choose a file to contribute</div>
              <div className={s.dropHint}>PDF · tabular (.csv/.xlsx) · docs (.md/.txt/.docx)</div>
            </>
          )}
        </div>

        <div className={s.samples}>
          <span className={s.sampleTag}>or try</span>
          {SAMPLES.map((sm) => (
            <button
              key={sm.filename}
              className={s.sampleChip}
              type="button"
              onClick={() => chooseBlob(sm.filename, new Blob([sm.content], { type: "text/plain" }))}
            >
              {sm.filename}
            </button>
          ))}
        </div>

        {unsupported && (
          <div className={`${s.notice} ${s.noticePending}`} style={{ marginTop: "var(--wf-space-4)" }}>
            <span className={s.noticeIcon}>⏳</span>
            <div>
              <div className={s.noticeTitle}>Not in Phase 1 yet</div>
              <div className={s.noticeBody}>{unsupported}</div>
            </div>
          </div>
        )}

        <p className={s.laterNote}>Video, images and URLs come in a later phase.</p>

        <div className={s.formDivider} />

        <div className={s.sectionLabel}>Provenance</div>
        <div className={s.field}>
          <label className={s.label}>Initiative</label>
          <select className={s.select} value={initiative} onChange={(e) => setInitiative(e.target.value)}>
            {INITIATIVES.map((i) => (
              <option key={i} value={i}>{i}</option>
            ))}
          </select>
        </div>
        <div className={s.fieldRow}>
          <div className={s.field}>
            <label className={s.label}>Author <span className={s.labelHint}>who made it</span></label>
            <input className={s.input} value={author} placeholder="e.g. Peskas field team" onChange={(e) => setAuthor(e.target.value)} />
          </div>
          <div className={s.field}>
            <label className={s.label}>Source <span className={s.labelHint}>link or origin</span></label>
            <input className={`${s.input} ${s.inputMono}`} value={sourceUrl} placeholder="https://… or upload://" onChange={(e) => setSourceUrl(e.target.value)} />
          </div>
        </div>

        <button
          className={`${s.btn} ${s.btnPrimary}`}
          disabled={!file || disabled}
          onClick={doSubmit}
          style={{ width: "100%", justifyContent: "center" }}
        >
          Submit for drafting
        </button>
      </div>
    </div>
  );
}

// ───────────────────────────────────────────────────────────── submission list
function SubmissionList({
  mine,
  selectedId,
  onSelect,
}: {
  mine: Submission[];
  selectedId: string | null;
  onSelect: (id: string) => void;
}) {
  return (
    <div className={s.card}>
      <div className={s.cardHead}>
        <span className={s.cardTitle}>Your submissions</span>
        <span className={s.cardKicker}>{mine.length} total</span>
      </div>
      <div className={s.cardBody}>
        {mine.length === 0 ? (
          <div className={s.empty}>Nothing yet — submit a file above.</div>
        ) : (
          <div className={s.subList}>
            {mine.map((sub) => (
              <button
                key={sub.id}
                className={`${s.subItem} ${sub.id === selectedId ? s.subItemActive : ""}`}
                onClick={() => onSelect(sub.id)}
              >
                <div className={s.subItemTop}>
                  <span className={s.subName}>{sub.filename}</span>
                  <StatePill state={sub.state} sm />
                </div>
                <div className={s.subMeta}>
                  <span>{sub.initiative}</span>
                  <span className={s.subMetaSep}>·</span>
                  <span>{sub.sizeLabel}</span>
                </div>
              </button>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

// ───────────────────────────────────────────────────────────── detail panel
function DetailPanel({ submission }: { submission: Submission }) {
  const { openForReview, editDraft, approve, resubmit } = useIngestion();
  const editable = submission.state === "UNDER_REVIEW" || submission.state === "REJECTED";

  return (
    <>
      <div className={s.card}>
        <div className={s.cardHead}>
          <span className={s.cardTitle}>{submission.filename}</span>
          <StatePill state={submission.state} />
        </div>
        <div className={s.cardBody}>
          <StateTrack state={submission.state} />
          <div className={s.blockGap}>
            <StatusNotice submission={submission} />
          </div>
        </div>
      </div>

      {submission.state === "SUBMITTED" ? (
        <div className={s.card}>
          <div className={s.cardBody}>
            <div className={s.empty}>
              <span className={s.spinner} aria-hidden /> &nbsp;The enricher is drafting the companion note…
            </div>
          </div>
        </div>
      ) : (
        submission.draft && (
          <div className={`${s.card} ${s.cardPrimary}`}>
            <div className={s.cardHead}>
              <span className={s.cardTitle}>Companion note</span>
              <span className={s.cardKicker}>{editable ? "editable" : "read-only"} · Template {submission.draft.template}</span>
            </div>
            <div className={s.cardBody}>
              <NoteEditor
                note={submission.draft}
                provenance={submission.provenance}
                editable={editable}
                onChange={(next) => editDraft(submission.id, next)}
              />
              <div className={`${s.btnRow} ${s.blockGap}`}>
                <ContributorActions submission={submission} openForReview={openForReview} approve={approve} resubmit={resubmit} />
              </div>
            </div>
          </div>
        )
      )}

      <div className={`${s.card} ${s.cardQuiet}`}>
        <div className={s.cardHead}>
          <span className={s.cardTitle}>Provenance</span>
        </div>
        <div className={s.cardBody}>
          <ProvenancePanel provenance={submission.provenance} />
        </div>
      </div>

      <div className={`${s.card} ${s.cardQuiet}`}>
        <div className={s.cardHead}>
          <span className={s.cardTitle}>History</span>
          <span className={s.cardKicker}>audit trail</span>
        </div>
        <div className={s.cardBody}>
          <HistoryTimeline history={submission.history} />
        </div>
      </div>
    </>
  );
}

function ContributorActions({
  submission,
  openForReview,
  approve,
  resubmit,
}: {
  submission: Submission;
  openForReview: (id: string) => void;
  approve: (id: string) => void;
  resubmit: (id: string) => void;
}) {
  switch (submission.state) {
    case "DRAFTED":
      return (
        <button className={`${s.btn} ${s.btnPrimary}`} onClick={() => openForReview(submission.id)}>
          Review this draft
        </button>
      );
    case "UNDER_REVIEW":
      return (
        <>
          <button className={`${s.btn} ${s.btnPrimary}`} onClick={() => approve(submission.id)}>
            Approve → submit for curator review
          </button>
          <span className={s.muted} style={{ fontSize: "var(--wf-text-caption)" }}>
            Stage 1 of 2 · this hands it off; it does not publish.
          </span>
        </>
      );
    case "REJECTED":
      return (
        <button className={`${s.btn} ${s.btnPrimary}`} onClick={() => resubmit(submission.id)}>
          Re-submit for curator review
        </button>
      );
    default:
      return (
        <span className={s.muted} style={{ fontSize: "var(--wf-text-caption)" }}>
          This contribution has left your hands — the curator owns it now.
        </span>
      );
  }
}

function StatusNotice({ submission }: { submission: Submission }) {
  switch (submission.state) {
    case "PENDING":
      return (
        <Notice tone="pending" icon="⏳" title="Submitted for curator review — not live">
          You approved this draft, so it’s left your hands and is now <strong>awaiting curator
          sign-off</strong>. You can’t make it live — only a curator can. It’ll appear in the
          knowledge base after they sign off and the next build runs.
        </Notice>
      );
    case "QUEUED":
      return (
        <Notice tone="queued" icon="⧖" title="Curator signed off — queued for the next build">
          The curator approved it and wrote the note to git. It’s <strong>queued</strong> for the
          controlled single-builder rebuild and will appear after that build — not instantly.
        </Notice>
      );
    case "BUILT":
      return (
        <Notice tone="queued" icon="⚙" title="Build ran — publishing">
          The build produced the artifacts; it’s being published now.
        </Notice>
      );
    case "LIVE":
      return (
        <Notice tone="live" icon="✓" title="Live in the knowledge base">
          Built and published — the read UI can now answer over this contribution.
        </Notice>
      );
    case "REJECTED":
      return (
        <Notice tone="rejected" icon="↩" title="Returned by the curator">
          {submission.rejectionReason}
        </Notice>
      );
    case "UNDER_REVIEW":
      return (
        <Notice tone="pending" icon="✎" title="Review the drafted note">
          Edit anything that needs fixing, then approve it for curator review. Approving is stage 1 of
          the two-stage gate — it does not publish.
        </Notice>
      );
    case "DRAFTED":
      return (
        <Notice tone="pending" icon="✦" title="Draft ready">
          The enricher drafted a companion note. Open it for review to edit and approve.
        </Notice>
      );
    default:
      return null;
  }
}

function Notice({
  tone,
  icon,
  title,
  children,
}: {
  tone: "pending" | "live" | "queued" | "rejected";
  icon: string;
  title: string;
  children: React.ReactNode;
}) {
  const toneClass = { pending: s.noticePending, live: s.noticeLive, queued: s.noticeQueued, rejected: s.noticeRejected }[tone];
  return (
    <div className={`${s.notice} ${toneClass}`}>
      <span className={s.noticeIcon} aria-hidden>{icon}</span>
      <div>
        <div className={s.noticeTitle}>{title}</div>
        <div className={s.noticeBody}>{children}</div>
      </div>
    </div>
  );
}
