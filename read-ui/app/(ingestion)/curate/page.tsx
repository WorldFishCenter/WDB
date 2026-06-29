"use client";

import { useEffect, useMemo, useState } from "react";
import { IngestionHeader } from "@/components/ingestion/IngestionHeader";
import { GateBanner } from "@/components/ingestion/GateBanner";
import { OfflineBanner } from "@/components/ingestion/OfflineBanner";
import { StatePill } from "@/components/ingestion/StatePill";
import { StateTrack } from "@/components/ingestion/StateTrack";
import { NoteEditor } from "@/components/ingestion/NoteEditor";
import { ProvenancePanel, HistoryTimeline } from "@/components/ingestion/ProvenancePanel";
import { useIngestion } from "@/lib/ingestion/store";
import type { BuildState } from "@/lib/ingestion/api";
import type { Submission } from "@/lib/ingestion/types";
import s from "@/components/ingestion/ingestion.module.scss";

export default function CuratePage() {
  const { submissions, backendOnline, error, build, building, runBuild, confirmBuild } = useIngestion();
  const [selectedId, setSelectedId] = useState<string | null>(null);

  const pending = useMemo(() => submissions.filter((x) => x.state === "PENDING"), [submissions]);
  const queued = useMemo(() => submissions.filter((x) => x.state === "QUEUED" || x.state === "BUILT"), [submissions]);
  const processed = useMemo(
    () => submissions.filter((x) => ["QUEUED", "BUILT", "LIVE", "REJECTED"].includes(x.state)),
    [submissions],
  );

  useEffect(() => {
    if (selectedId && submissions.some((x) => x.id === selectedId)) return;
    setSelectedId(pending[0]?.id ?? processed[0]?.id ?? null);
  }, [selectedId, submissions, pending, processed]);

  const selected = submissions.find((x) => x.id === selectedId) ?? null;

  return (
    <>
      <IngestionHeader role="curator" />
      <main className={`wf-container ${s.page}`}>
        <div className={s.pageHead}>
          <div className={s.eyebrow}>✓ Curate</div>
          <h1 className={s.pageTitle}>The approval queue</h1>
          <p className={s.pageSub}>
            Contributions contributors have approved arrive here as <strong>pending</strong> — the
            second gate. Review the drafted note, edit anything (curator override), then sign off or
            send it back. Sign-off writes the note to git and <strong>queues</strong> the
            single-builder rebuild; it doesn’t publish instantly.
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

        <div style={{ marginBottom: "var(--wf-space-6)" }}>
          <GateBanner emphasis="curator" />
        </div>

        <div className={s.split}>
          <div className={s.col}>
            <BuildPanel
              build={build}
              building={building}
              queuedCount={queued.length}
              disabled={!backendOnline}
              onBuild={runBuild}
              onConfirm={confirmBuild}
            />

            <div className={s.card}>
              <div className={s.cardHead}>
                <span className={s.cardTitle}>Pending review</span>
                <span className={s.cardKicker}>{pending.length} awaiting sign-off</span>
              </div>
              <div className={s.cardBody}>
                {pending.length === 0 ? (
                  <div className={s.empty}>
                    <div className={s.emptyIcon}>✓</div>
                    Queue clear — no contributions awaiting curator sign-off.
                  </div>
                ) : (
                  <QueueList items={pending} selectedId={selectedId} onSelect={setSelectedId} />
                )}
              </div>
            </div>

            {processed.length > 0 && (
              <div className={s.card}>
                <div className={s.cardHead}>
                  <span className={s.cardTitle}>Processed</span>
                  <span className={s.cardKicker}>queued · built · live · sent back</span>
                </div>
                <div className={s.cardBody}>
                  <QueueList items={processed} selectedId={selectedId} onSelect={setSelectedId} />
                </div>
              </div>
            )}
          </div>

          <div className={s.col}>
            {selected ? (
              <CuratorDetail key={selected.id} submission={selected} />
            ) : (
              <div className={s.detailHint}>
                <div className={s.emptyIcon}>✓</div>
                The queue is clear. When a contributor approves a draft, it appears here for sign-off.
              </div>
            )}
          </div>
        </div>
      </main>
    </>
  );
}

// ───────────────────────────────────────────────────────────── build panel (tracked handoff)
function BuildPanel({
  build,
  building,
  queuedCount,
  disabled,
  onBuild,
  onConfirm,
}: {
  build: BuildState | null;
  building: boolean;
  queuedCount: number;
  disabled?: boolean;
  onBuild: () => void;
  onConfirm: () => void;
}) {
  return (
    <div className={s.card}>
      <div className={s.cardHead}>
        <span className={s.cardTitle}>Build</span>
        <span className={s.cardKicker}>single-builder · pinned Opus</span>
      </div>
      <div className={s.cardBody}>
        <p className={s.noteText} style={{ fontSize: "var(--wf-text-caption)", marginBottom: "var(--wf-space-4)" }}>
          Sign-off <strong>queues</strong> a contribution. The guarded build (the two extraction guards
          + canonical remap) only applies in the pinned <span className={s.mono}>claude-opus-4-8</span>{" "}
          session — so this hands the queue off to that build rather than faking one, then detects when
          it’s done.
        </p>

        {building ? (
          <div className={`${s.notice} ${s.noticeQueued}`}>
            <span className={s.noticeIcon}>⧖</span>
            <div>
              <div className={s.noticeTitle}>Handed off — run the pinned build</div>
              <div className={s.noticeBody}>
                {build?.message}
                <div style={{ marginTop: "var(--wf-space-2)" }}>
                  Run in a pinned session: <span className={s.mono}>{build?.command}</span>
                </div>
              </div>
            </div>
          </div>
        ) : (
          <div className={s.btnRow} style={{ justifyContent: "space-between" }}>
            <span className={s.subMeta}>
              <StatePill state="QUEUED" sm /> &nbsp;{queuedCount} queued
            </span>
            <button className={`${s.btn} ${s.btnGhost} ${s.btnSm}`} onClick={onBuild} disabled={disabled || queuedCount === 0}>
              Hand off to single-builder build
            </button>
          </div>
        )}

        {building && (
          <div className={s.btnRow} style={{ marginTop: "var(--wf-space-4)" }}>
            <button className={`${s.btn} ${s.btnPrimary} ${s.btnSm}`} onClick={onConfirm}>
              Mark build complete → publish
            </button>
            <span className={s.muted} style={{ fontSize: "var(--wf-text-caption)" }}>
              Auto-detected when the graph is rebuilt; or confirm manually.
            </span>
          </div>
        )}
      </div>
    </div>
  );
}

// ───────────────────────────────────────────────────────────── queue list
function QueueList({
  items,
  selectedId,
  onSelect,
}: {
  items: Submission[];
  selectedId: string | null;
  onSelect: (id: string) => void;
}) {
  return (
    <div className={s.subList}>
      {items.map((sub) => (
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
            <span>by {sub.provenance.contributor}</span>
            <span className={s.subMetaSep}>·</span>
            <span>{sub.initiative}</span>
            {sub.curatorEdited && (
              <>
                <span className={s.subMetaSep}>·</span>
                <span title="Edited via curator override">edited</span>
              </>
            )}
          </div>
        </button>
      ))}
    </div>
  );
}

// ───────────────────────────────────────────────────────────── curator detail
function CuratorDetail({ submission }: { submission: Submission }) {
  const { editDraft, curatorApprove, reject } = useIngestion();
  const [rejecting, setRejecting] = useState(false);
  const [reason, setReason] = useState("");
  const isPending = submission.state === "PENDING";

  return (
    <>
      <div className={s.card}>
        <div className={s.cardHead}>
          <span className={s.cardTitle}>{submission.filename}</span>
          <StatePill state={submission.state} />
        </div>
        <div className={s.cardBody}>
          <StateTrack state={submission.state} />
          <div className={s.subMeta} style={{ marginTop: "var(--wf-space-4)" }}>
            <span>Target placement:</span>
            <span className={s.mono}>{submission.targetPlacement}</span>
          </div>
          {!isPending && (
            <div style={{ marginTop: "var(--wf-space-4)" }}>
              <CuratorStatusNotice submission={submission} />
            </div>
          )}
        </div>
      </div>

      {submission.draft && (
        <div className={s.card}>
          <div className={s.cardHead}>
            <span className={s.cardTitle}>Companion note</span>
            <span className={s.cardKicker}>
              {isPending ? "curator override · editable" : "read-only"} · Template {submission.draft.template}
              {submission.curatorEdited ? " · edited" : ""}
            </span>
          </div>
          <div className={s.cardBody}>
            <NoteEditor
              note={submission.draft}
              provenance={submission.provenance}
              editable={isPending}
              onChange={(next) => editDraft(submission.id, next)}
            />

            {isPending && (
              <div style={{ marginTop: "var(--wf-space-5)" }}>
                {!rejecting ? (
                  <div className={s.btnRow}>
                    <button className={`${s.btn} ${s.btnPrimary}`} onClick={() => curatorApprove(submission.id)}>
                      Sign off → write to git &amp; queue
                    </button>
                    <button className={`${s.btn} ${s.btnDanger}`} onClick={() => setRejecting(true)}>
                      Send back
                    </button>
                    <span className={s.muted} style={{ fontSize: "var(--wf-text-caption)" }}>
                      Stage 2 of 2 · sign-off queues a build, it doesn’t publish now.
                    </span>
                  </div>
                ) : (
                  <div>
                    <label className={s.label}>Reason — sent back to the contributor</label>
                    <textarea
                      className={s.textarea}
                      autoFocus
                      value={reason}
                      placeholder="What needs fixing before this can be signed off?"
                      onChange={(e) => setReason(e.target.value)}
                    />
                    <div className={s.btnRow} style={{ marginTop: "var(--wf-space-3)" }}>
                      <button
                        className={`${s.btn} ${s.btnDanger}`}
                        disabled={!reason.trim()}
                        onClick={() => reject(submission.id, reason.trim())}
                      >
                        Confirm — send back
                      </button>
                      <button className={`${s.btn} ${s.btnGhost}`} onClick={() => { setRejecting(false); setReason(""); }}>
                        Cancel
                      </button>
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      )}

      <div className={s.card}>
        <div className={s.cardHead}>
          <span className={s.cardTitle}>Provenance &amp; source</span>
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

function CuratorStatusNotice({ submission }: { submission: Submission }) {
  const map = {
    QUEUED: { cls: s.noticeQueued, icon: "⧖", title: "Queued for the next build", body: "Signed off and the note is in git — waiting for the single-builder build to publish. Not live yet." },
    BUILT: { cls: s.noticeQueued, icon: "⚙", title: "Build ran — publishing", body: "Artifacts produced; publishing to the read service." },
    LIVE: { cls: s.noticeLive, icon: "✓", title: "Live in the knowledge base", body: "Built and published. Curator override can still edit or supersede it at any time." },
    REJECTED: { cls: s.noticeRejected, icon: "↩", title: "Sent back to the contributor", body: submission.rejectionReason ?? "Returned with a reason." },
  } as const;
  const m = map[submission.state as keyof typeof map];
  if (!m) return null;
  return (
    <div className={`${s.notice} ${m.cls}`}>
      <span className={s.noticeIcon} aria-hidden>{m.icon}</span>
      <div>
        <div className={s.noticeTitle}>{m.title}</div>
        <div className={s.noticeBody}>{m.body}</div>
      </div>
    </div>
  );
}
