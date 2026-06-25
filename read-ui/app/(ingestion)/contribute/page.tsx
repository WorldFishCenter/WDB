"use client";

import { useMemo, useRef, useState } from "react";
import { IngestionHeader } from "@/components/ingestion/IngestionHeader";
import { GateBanner } from "@/components/ingestion/GateBanner";
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

// Phase-1 formats are active; richer formats are shown but disabled (design §5).
const PHASE1 = [
  { id: "tabular", label: "Tabular", icon: "▦", exts: ".csv, .xlsx" },
  { id: "pdf", label: "PDF", icon: "▤", exts: ".pdf" },
  { id: "doc", label: "Docs", icon: "✎", exts: ".md, .txt, .docx" },
];
const LATER = [
  { id: "video", label: "Video", icon: "►" },
  { id: "image", label: "Image / diagram", icon: "▣" },
  { id: "url", label: "URL", icon: "🔗" },
];

const SAMPLES: { filename: string; format: Phase1Format; sizeLabel: string }[] = [
  { filename: "kenya_yield_2025.csv", format: "tabular", sizeLabel: "1.1 MB" },
  { filename: "mombasa_market_survey.pdf", format: "pdf", sizeLabel: "1.8 MB" },
  { filename: "aquaculture_brief.md", format: "doc", sizeLabel: "22 KB" },
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
  const { submissions, currentContributor, submit } = useIngestion();
  const [selectedId, setSelectedId] = useState<string | null>(null);

  const mine = useMemo(
    () => submissions.filter((x) => x.provenance.contributor === currentContributor),
    [submissions, currentContributor],
  );
  const selected = mine.find((x) => x.id === selectedId) ?? null;

  return (
    <>
      <IngestionHeader role="contributor" />
      <main className={`wf-container ${s.page}`}>
        <div className={s.pageHead}>
          <div className={s.eyebrow}>✎ Contribute</div>
          <h1 className={s.pageTitle}>Add to the shared knowledge base</h1>
          <p className={s.pageSub}>
            Upload a file, review the companion note the agents draft for it, then approve it for
            curator review. Approving hands it off — it does <strong>not</strong> go live. Only a
            curator can sign it into the knowledge base.
          </p>
        </div>

        <div style={{ marginBottom: "var(--wf-space-6)" }}>
          <GateBanner emphasis="contributor" />
        </div>

        <div className={s.split}>
          <div className={s.col}>
            <SubmitCard
              onSubmit={(input) => {
                const id = submit(input);
                setSelectedId(id);
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
function SubmitCard({ onSubmit }: { onSubmit: (input: SubmissionInput) => void }) {
  const fileRef = useRef<HTMLInputElement>(null);
  const [file, setFile] = useState<{ filename: string; format: Phase1Format; sizeLabel: string } | null>(null);
  const [unsupported, setUnsupported] = useState<string | null>(null);
  const [initiative, setInitiative] = useState(INITIATIVES[0]);
  const [author, setAuthor] = useState("");
  const [sourceUrl, setSourceUrl] = useState("");

  function choose(filename: string, sizeLabel: string) {
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
    setFile({ filename, format: fmt, sizeLabel });
  }

  function onPick(e: React.ChangeEvent<HTMLInputElement>) {
    const f = e.target.files?.[0];
    if (f) choose(f.name, humanSize(f.size));
  }

  function doSubmit() {
    if (!file) return;
    onSubmit({
      filename: file.filename,
      format: file.format,
      sizeLabel: file.sizeLabel,
      initiative,
      author: author.trim(),
      source_url: sourceUrl.trim(),
    });
    setFile(null);
    setAuthor("");
    setSourceUrl("");
    if (fileRef.current) fileRef.current.value = "";
  }

  return (
    <div className={s.card}>
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
              onClick={() => choose(sm.filename, sm.sizeLabel)}
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

        <div className={s.formatRow}>
          {PHASE1.map((f) => (
            <span key={f.id} className={`${s.formatChip} ${file?.format === f.id ? s.formatChipOn : ""}`} title={f.exts}>
              <span aria-hidden>{f.icon}</span> {f.label}
            </span>
          ))}
          {LATER.map((f) => (
            <span key={f.id} className={`${s.formatChip} ${s.formatChipLater}`}>
              <span aria-hidden>{f.icon}</span> {f.label} <span className={s.formatLaterTag}>later</span>
            </span>
          ))}
        </div>

        <div style={{ height: "1px", background: "var(--wf-border-subtle)", margin: "var(--wf-space-5) 0" }} />

        <div className={s.sectionLabel}>Provenance — captured now, carried onto the graph (§8)</div>
        <div className={s.field}>
          <label className={s.label}>Initiative <span className={s.labelHint}>(Project-First placement)</span></label>
          <select className={s.select} value={initiative} onChange={(e) => setInitiative(e.target.value)}>
            {INITIATIVES.map((i) => (
              <option key={i} value={i}>{i}</option>
            ))}
          </select>
        </div>
        <div className={s.fieldRow}>
          <div className={s.field}>
            <label className={s.label}>Author <span className={s.labelHint}>(who made it)</span></label>
            <input className={s.input} value={author} placeholder="e.g. Peskas field team" onChange={(e) => setAuthor(e.target.value)} />
          </div>
          <div className={s.field}>
            <label className={s.label}>Source <span className={s.labelHint}>(origin / link)</span></label>
            <input className={`${s.input} ${s.inputMono}`} value={sourceUrl} placeholder="https://… or upload://" onChange={(e) => setSourceUrl(e.target.value)} />
          </div>
        </div>

        <button className={`${s.btn} ${s.btnPrimary}`} disabled={!file} onClick={doSubmit} style={{ width: "100%", justifyContent: "center" }}>
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
  const { openForReview, updateDraft, contributorApprove, contributorResubmit } = useIngestion();
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
          <div style={{ marginTop: "var(--wf-space-5)" }}>
            <StatusNotice submission={submission} />
          </div>
        </div>
      </div>

      {/* The drafted companion note (once the agents have produced it) */}
      {submission.state === "SUBMITTED" ? (
        <div className={s.card}>
          <div className={s.cardBody}>
            <div className={s.empty}>
              <span className={s.spinner} aria-hidden /> &nbsp;The curate/enrich agents are drafting the
              companion note…
            </div>
          </div>
        </div>
      ) : (
        submission.draft && (
          <div className={s.card}>
            <div className={s.cardHead}>
              <span className={s.cardTitle}>Companion note</span>
              <span className={s.cardKicker}>{editable ? "editable" : "read-only"} · Template {submission.draft.template}</span>
            </div>
            <div className={s.cardBody}>
              <NoteEditor
                note={submission.draft}
                provenance={submission.provenance}
                editable={editable}
                onChange={(next) => updateDraft(submission.id, next)}
              />
              <div className={s.btnRow} style={{ marginTop: "var(--wf-space-5)" }}>
                <ContributorActions submission={submission} openForReview={openForReview} approve={contributorApprove} resubmit={contributorResubmit} />
              </div>
            </div>
          </div>
        )
      )}

      <div className={s.card}>
        <div className={s.cardHead}>
          <span className={s.cardTitle}>Provenance</span>
        </div>
        <div className={s.cardBody}>
          <ProvenancePanel provenance={submission.provenance} />
        </div>
      </div>

      <div className={s.card}>
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

/** The honest, state-specific status message — never implies "live" before it is. */
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
          The curator approved it. It’s <strong>queued</strong> for the controlled single-builder
          rebuild and will appear after that build — not instantly.
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
          The agents drafted a companion note. Open it for review to edit and approve.
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
