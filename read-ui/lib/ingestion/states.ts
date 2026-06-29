/**
 * State-machine metadata — the single source of truth for how each WorkflowState is labelled,
 * described, and coloured across both views. Mirrors the design §1.3 diagram. Keeping it here means
 * the contributor track and the curator queue speak the same language about where a contribution is.
 */
import type { WorkflowState } from "./types";

/** Who controls a contribution at a given state — drives the honest "ball is in X's court" copy. */
export type StateOwner = "contributor" | "curator" | "system" | "done";

/** Visual tone, mapped to the existing honesty tokens (no new colours). */
export type StateTone = "neutral" | "active" | "pending" | "queued" | "live" | "rejected";

export interface StateMeta {
  label: string; //       short pill label
  short: string; //       one-line "what this means"
  owner: StateOwner;
  tone: StateTone;
}

export const STATE_META: Record<WorkflowState, StateMeta> = {
  SUBMITTED: {
    label: "Submitted",
    short: "Uploaded — provenance stamped; the draft agents are about to run.",
    owner: "system",
    tone: "neutral",
  },
  DRAFTED: {
    label: "Drafted",
    short: "The curate/enrich agents produced a companion-note draft (mock).",
    owner: "contributor",
    tone: "active",
  },
  UNDER_REVIEW: {
    label: "Under review",
    short: "You're reviewing and editing the drafted note before approving it.",
    owner: "contributor",
    tone: "active",
  },
  PENDING: {
    label: "Pending curator",
    short: "Approved by you and handed off — awaiting curator sign-off. Not live.",
    owner: "curator",
    tone: "pending",
  },
  QUEUED: {
    label: "Queued",
    short: "Curator signed off — in the build queue. Appears after the next build.",
    owner: "system",
    tone: "queued",
  },
  BUILT: {
    label: "Built",
    short: "The single-builder build ran and produced the artifacts.",
    owner: "system",
    tone: "queued",
  },
  LIVE: {
    label: "Live",
    short: "Published — the knowledge base and the read UI can see it.",
    owner: "done",
    tone: "live",
  },
  REJECTED: {
    label: "Sent back",
    short: "The curator returned it with a reason — edit and re-submit for review.",
    owner: "contributor",
    tone: "rejected",
  },
};

/** The happy-path pipeline order, used to render the linear progress track (REJECTED is off-path). */
export const PIPELINE_ORDER: WorkflowState[] = [
  "SUBMITTED",
  "DRAFTED",
  "UNDER_REVIEW",
  "PENDING",
  "QUEUED",
  "BUILT",
  "LIVE",
];

/** The two gates, by name, for the unmistakable "two-stage gate" labelling in the UI. */
export const GATE = {
  stage1: { after: "UNDER_REVIEW", to: "PENDING", who: "contributor" as const },
  stage2: { after: "PENDING", to: "QUEUED", who: "curator" as const },
};

export function isContributorActionable(s: WorkflowState): boolean {
  return s === "DRAFTED" || s === "UNDER_REVIEW" || s === "REJECTED";
}

/** A contribution the contributor has handed off — visible in the curator queue as awaiting review. */
export function isAwaitingCurator(s: WorkflowState): boolean {
  return s === "PENDING";
}

/** Past the stage-2 gate — the contributor can no longer touch it; the curator owns it. */
export function isPastStage2(s: WorkflowState): boolean {
  return s === "QUEUED" || s === "BUILT" || s === "LIVE";
}
