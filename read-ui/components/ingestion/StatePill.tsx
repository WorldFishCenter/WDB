import type { WorkflowState } from "@/lib/ingestion/types";
import { STATE_META, type StateTone } from "@/lib/ingestion/states";
import s from "./ingestion.module.scss";

const TONE_CLASS: Record<StateTone, string> = {
  neutral: s.toneNeutral,
  active: s.toneActive,
  pending: s.tonePending,
  queued: s.toneQueued,
  live: s.toneLive,
  rejected: s.toneRejected,
};

/** The state badge — one stable colour per state, drawn from the existing honesty tokens. */
export function StatePill({ state, sm = false }: { state: WorkflowState; sm?: boolean }) {
  const meta = STATE_META[state];
  return (
    <span
      className={`${s.pill} ${TONE_CLASS[meta.tone]} ${sm ? s.pillSm : ""}`}
      title={meta.short}
    >
      <span className={s.pillDot} aria-hidden />
      {meta.label}
    </span>
  );
}
