import type { WorkflowState } from "@/lib/ingestion/types";
import { PIPELINE_ORDER, STATE_META } from "@/lib/ingestion/states";
import s from "./ingestion.module.scss";

/** Where the two-stage gate sits on the linear track (after these states). */
const GATE_AFTER: Partial<Record<WorkflowState, string>> = {
  UNDER_REVIEW: "gate 1",
  PENDING: "gate 2",
};

/**
 * The linear pipeline progress — SUBMITTED → … → LIVE, with the two gates marked. Makes "where is
 * this contribution, and which gate is next" legible at a glance. REJECTED renders as an off-path
 * marker on the current (UNDER_REVIEW-equivalent) step.
 */
export function StateTrack({ state }: { state: WorkflowState }) {
  const rejected = state === "REJECTED";
  // A rejected item sits conceptually back at the review step.
  const effective: WorkflowState = rejected ? "UNDER_REVIEW" : state;
  const currentIdx = PIPELINE_ORDER.indexOf(effective);

  return (
    <div className={s.track} role="img" aria-label={`Pipeline state: ${STATE_META[state].label}`}>
      {PIPELINE_ORDER.map((step, i) => {
        const done = i < currentIdx;
        const current = i === currentIdx;
        const stepClass = rejected && current ? s.stepRejected : current ? s.stepCurrent : done ? s.stepDone : "";
        return (
          <div key={step} className={`${s.trackStep} ${stepClass}`}>
            {GATE_AFTER[step] && (
              <span className={s.trackGate} style={{ right: 0 }}>
                {GATE_AFTER[step]}
              </span>
            )}
            <div className={s.trackRail}>
              {/* no dangling rail before the first dot or after the last */}
              <span
                className={`${s.trackLine} ${i > 0 && i <= currentIdx ? s.trackLineFilled : ""}`}
                style={i === 0 ? { visibility: "hidden" } : undefined}
              />
              <span className={s.trackDot}>{done ? "✓" : ""}</span>
              <span
                className={`${s.trackLine} ${i < currentIdx ? s.trackLineFilled : ""}`}
                style={i === PIPELINE_ORDER.length - 1 ? { visibility: "hidden" } : undefined}
              />
            </div>
            <span className={s.trackLabel}>{STATE_META[step].label}</span>
          </div>
        );
      })}
    </div>
  );
}
