"use client";

import { useEffect, useMemo, useState } from "react";
import { IngestionHeader } from "@/components/ingestion/IngestionHeader";
import { GateBanner } from "@/components/ingestion/GateBanner";
import { StatePill } from "@/components/ingestion/StatePill";
import { StateTrack } from "@/components/ingestion/StateTrack";
import { NoteEditor } from "@/components/ingestion/NoteEditor";
import { ProvenancePanel, HistoryTimeline } from "@/components/ingestion/ProvenancePanel";
import { useIngestion } from "@/lib/ingestion/store";
import type { Submission } from "@/lib/ingestion/types";
import s from "@/components/ingestion/ingestion.module.scss";

export default function CuratePage() {
  const { submissions, building, runBuild } = useIngestion();
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [buildMsg, setBuildMsg] = useState<string | null>(null);

  const pending = useMemo(() => submissions.filter((x) => x.state === "PENDING"), [submissions]);
  const queued = useMemo(() => submissions.filter((x) => x.state === "QUEUED" || x.state === "BUILT"), [submissions]);
  const processed = useMemo(
    () => submissions.filter((x) => x.state === "QUEUED" || x.state === "BUILT" || x.state === "LIVE" || x.state === "REJECTED"),
    [submissions],
  );

  // Keep a sensible default selection — the first pending item, so the queue isn't empty-looking.
  useEffect(() => {
    if (selectedId && submissions.some((x) => x.id === selectedId)) return;
    setSelectedId(pending[0]?.id ?? processed[0]?.id ?? null);
  }, [selectedId, submissions, pending, processed]);

  const selected = submissions.find((x) => x.id === selectedId) ?? null;

  function onBuild() {
    const n = runBuild();
    setBuildMsg(n === 0 ? "Nothing queued to build." : `Single-builder build started over ${n} queued contribution${n > 1 ? "s" : ""}…`);
  }

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
            send it back. Sign-off <strong>queues</strong> a single-builder rebuild; it doesn’t
            publish instantly.
          </p>
        </div>

        <div style={{ marginBottom: "var(--wf-space-6)" }}>
          <GateBanner emphasis="curator" />
        </div>

        <div className={s.split}>
          <div className={s.col}>
            <BuildPanel queuedCount={queued.length} building={building} onBuild={onBuild} message={buildMsg} />

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
                  <QueueList items={pending} selectedId={selectedId} onSelect={setSelectedId} showContributor />
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
                  <QueueList items={processed} selectedId={selectedId} onSelect={setSelectedId} showContributor />
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

// ───────────────────────────────────────────────────────────── build panel
function BuildPanel({
  queuedCount,
  building,
  onBuild,
  message,
}: {
  queuedCount: number;
  building: boolean;
  onBuild: () => void;
  message: string | null;
}) {
  return (
    <div className={s.card}>
      <div className={s.cardHead}>
        <span className={s.cardTitle}>Build</span>
        <span className={s.cardKicker}>single-builder · pinned Opus</span>
      </div>
      <div className={s.cardBody}>
        <p className={s.noteText} style={{ fontSize: "var(--wf-text-caption)", marginBottom: "var(--wf-space-4)" }}>
          Sign-off <strong>queues</strong> a contribution; it doesn’t build. One controlled build
          drains the whole queue at once (batched, pinned <span className={s.mono}>claude-opus-4-8</span>) —
          never a build per approval.
        </p>
        <div className={s.btnRow} style={{ justifyContent: "space-between" }}>
          <span className={s.subMeta}>
            <StatePill state="QUEUED" sm /> &nbsp;{queuedCount} queued
          </span>
          <button className={`${s.btn} ${s.btnGhost} ${s.btnSm}`} onClick={onBuild} disabled={building || queuedCount === 0}>
            {building ? (
              <>
                <span className={s.spinner} aria-hidden /> Building…
              </>
            ) : (
              "Run single-builder build"
            )}
          </button>
        </div>
        {message && (
          <div className={s.provNote} style={{ marginTop: "var(--wf-space-3)" }}>{message}</div>
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
  showContributor,
}: {
  items: Submission[];
  selectedId: string | null;
  onSelect: (id: string) => void;
  showContributor?: boolean;
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
            {showContributor && (
              <>
                <span>by {sub.provenance.contributor}</span>
                <span className={s.subMetaSep}>·</span>
              </>
            )}
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
  const { curatorUpdateDraft, curatorApprove, curatorReject } = useIngestion();
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
              onChange={(next) => curatorUpdateDraft(submission.id, next)}
            />

            {isPending && (
              <div style={{ marginTop: "var(--wf-space-5)" }}>
                {!rejecting ? (
                  <div className={s.btnRow}>
                    <button className={`${s.btn} ${s.btnPrimary}`} onClick={() => curatorApprove(submission.id)}>
                      Sign off → queue for build
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
                        onClick={() => curatorReject(submission.id, reason.trim())}
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
    QUEUED: { cls: s.noticeQueued, icon: "⧖", title: "Queued for the next build", body: "Signed off — waiting for the single-builder build to drain the queue. Not live yet." },
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
