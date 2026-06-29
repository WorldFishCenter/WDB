import s from "./ingestion.module.scss";

/**
 * The two-stage approval gate, stated plainly and identically on both views — so it is unmistakable
 * that contributor approval only reaches PENDING, and ONLY the curator moves PENDING → QUEUED.
 * `emphasis` highlights the stage that belongs to the current view.
 */
export function GateBanner({ emphasis }: { emphasis?: "contributor" | "curator" }) {
  return (
    <div className={s.gate}>
      <div
        className={s.gateStage}
        style={emphasis === "contributor" ? { borderColor: "var(--wf-border-accent-medium)" } : undefined}
      >
        <div className={s.gateStageTitle}>
          <span className={s.gateStageNum}>1</span>Contributor approval
        </div>
        <div className={s.gateStageWho}>contributor → pending</div>
        <div className={s.gateStageBody}>
          You review and approve the drafted note. This says “ready for review” — like opening a PR.
          It moves to <strong>Pending</strong> and leaves your hands. It does <strong>not</strong> go
          live.
        </div>
      </div>

      <div className={s.gateArrow} aria-hidden>
        →
      </div>

      <div
        className={s.gateStage}
        style={emphasis === "curator" ? { borderColor: "var(--wf-border-accent-medium)" } : undefined}
      >
        <div className={s.gateStageTitle}>
          <span className={s.gateStageNum}>2</span>Curator sign-off
        </div>
        <div className={s.gateStageWho}>curator → queued</div>
        <div className={s.gateStageBody}>
          Only the curator can sign off — like merging the PR. Sign-off <strong>queues</strong> a
          single-builder rebuild; it doesn’t publish instantly. Nothing reaches the knowledge base
          without this step.
        </div>
      </div>
    </div>
  );
}
