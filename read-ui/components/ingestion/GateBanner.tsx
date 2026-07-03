import s from "./ingestion.module.scss";

/**
 * The two-stage approval gate as a slim reference strip — present on both views so it stays
 * unmistakable that contributor approval only reaches PENDING, and ONLY the curator moves
 * PENDING → QUEUED. `emphasis` lights the stage that belongs to the current view; the other stays
 * neutral. The full mechanics live in the Build panel and the per-submission status notices — this
 * bar is orientation, not the task.
 */
export function GateBanner({ emphasis }: { emphasis?: "contributor" | "curator" }) {
  return (
    <div className={s.gate} role="note" aria-label="Two-stage approval gate">
      <span className={s.gateLabel}>Two-stage gate</span>
      <div className={s.gateSteps}>
        <span className={`${s.gateStep} ${emphasis === "contributor" ? s.gateStepOn : ""}`}>
          <span className={s.gateStepNum}>1</span>
          <span>
            <strong>You approve</strong> → Pending
          </span>
        </span>
        <span className={s.gateSep} aria-hidden>
          →
        </span>
        <span className={`${s.gateStep} ${emphasis === "curator" ? s.gateStepOn : ""}`}>
          <span className={s.gateStepNum}>2</span>
          <span>
            <strong>Curator signs off</strong> → Queued
          </span>
        </span>
      </div>
      <span className={s.gateNote}>Nothing goes live without curator sign-off.</span>
    </div>
  );
}
