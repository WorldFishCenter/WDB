"use client";

/**
 * The shared, persisted MOCK workflow store — the one place both views read and write, so a
 * contributor approval in /contribute shows up in the curator queue in /curate. It stands in for the
 * ingestion API (design §8 Atlas workflow state): no network, just React state mirrored to
 * localStorage (survives navigation + reload) with a `storage` listener for cross-tab sync.
 *
 * THE TWO-STAGE GATE IS ENFORCED HERE BY CONSTRUCTION. Contributor actions can only advance a
 * contribution to PENDING (stage-1). There is NO contributor action that produces QUEUED / BUILT /
 * LIVE — only `curatorApprove` (stage-2) and `runBuild` (the single-builder step) do. A contributor
 * cannot make anything live, no matter what the UI renders.
 */

import { createContext, useCallback, useContext, useEffect, useRef, useState } from "react";
import type { DraftedNote, Submission, SubmissionInput, WorkflowState } from "./types";
import { CURATOR, CURRENT_CONTRIBUTOR, SEED_SUBMISSIONS, STORE_KEY } from "./fixtures";

function now(): string {
  return new Date().toISOString();
}

function uid(): string {
  return `sub_${Date.now().toString(36)}_${Math.random().toString(36).slice(2, 7)}`;
}

/** Append a state transition to a submission's audit trail (history is append-only, newest last). */
function advance(sub: Submission, to: WorkflowState, actor: string, note?: string): Submission {
  return { ...sub, state: to, history: [...sub.history, { state: to, at: now(), actor, note }] };
}

/**
 * The mock "curate/enrich" agents — produces a draft companion note from the submission input,
 * in the right template (A for tabular, B otherwise). Stands in for the server-side agent call
 * (design §7); the real pipeline returns the same DraftedNote shape.
 */
function generateDraft(input: SubmissionInput): DraftedNote {
  const base = input.filename.replace(/\.[^.]+$/, "");
  if (input.format === "tabular") {
    return {
      template: "A",
      filename: `${base}_dict.md`,
      title: `Data dictionary: ${input.filename}`,
      summary: `Draft summary of ${input.filename}. Part of the ${input.initiative} initiative. (Auto-drafted — review and edit before approving.)`,
      grain: "One row = … (state what one row IS in domain terms; /enrich fills this deterministically).",
      columns: [
        { name: "column_1", meaning: "plain-English meaning", domain: "value domain (filled by /enrich)" },
        { name: "column_2", meaning: "plain-English meaning", domain: "value domain (filled by /enrich)" },
      ],
      relatedFiles: [`${input.initiative}_about.md (the initiative this dataset belongs to)`],
      notesCaveats: "Any missing values, units, or skew the assistant should know when reading this.",
    };
  }
  return {
    template: "B",
    filename: `${base}_context.md`,
    title: `Context: ${input.filename}`,
    summary: `Draft summary of ${input.filename}. Part of the ${input.initiative} initiative. (Auto-drafted — review and edit before approving.)`,
    keyConcepts: ["Topics, regions, methods, or entities this file is about"],
    relatedFiles: [`${input.initiative}_about.md (the initiative this file belongs to)`],
  };
}

// ──────────────────────────────────────────────────────────────────────────── store context

interface IngestionContextValue {
  submissions: Submission[];
  hydrated: boolean;
  building: boolean;
  currentContributor: string;
  curator: string;

  // contributor actions (can never pass the stage-2 gate)
  submit: (input: SubmissionInput) => string;
  openForReview: (id: string) => void;
  updateDraft: (id: string, draft: DraftedNote) => void;
  contributorApprove: (id: string) => void;
  contributorResubmit: (id: string) => void;

  // curator actions (the only path past stage-2)
  curatorUpdateDraft: (id: string, draft: DraftedNote) => void;
  curatorApprove: (id: string) => void;
  curatorReject: (id: string, reason: string) => void;
  runBuild: () => number;

  resetDemo: () => void;
}

const IngestionContext = createContext<IngestionContextValue | null>(null);

export function IngestionProvider({ children }: { children: React.ReactNode }) {
  const [submissions, setSubmissions] = useState<Submission[]>(SEED_SUBMISSIONS);
  const [hydrated, setHydrated] = useState(false);
  const [building, setBuilding] = useState(false);
  const hydratedRef = useRef(false);

  // Hydrate from localStorage on mount (seed on first run). Deferred to an effect so SSR + first
  // client render are deterministic (no hydration mismatch).
  useEffect(() => {
    try {
      const raw = window.localStorage.getItem(STORE_KEY);
      if (raw) setSubmissions(JSON.parse(raw) as Submission[]);
      else window.localStorage.setItem(STORE_KEY, JSON.stringify(SEED_SUBMISSIONS));
    } catch {
      /* localStorage unavailable — stay on the in-memory seed */
    }
    hydratedRef.current = true;
    setHydrated(true);
  }, []);

  // Persist after hydration (never clobber stored data with the seed on the first paint).
  useEffect(() => {
    if (!hydratedRef.current) return;
    try {
      window.localStorage.setItem(STORE_KEY, JSON.stringify(submissions));
    } catch {
      /* ignore */
    }
  }, [submissions]);

  // Cross-tab / cross-route sync — pick up writes from the other view.
  useEffect(() => {
    function onStorage(e: StorageEvent) {
      if (e.key === STORE_KEY && e.newValue) {
        try {
          setSubmissions(JSON.parse(e.newValue) as Submission[]);
        } catch {
          /* ignore malformed */
        }
      }
    }
    window.addEventListener("storage", onStorage);
    return () => window.removeEventListener("storage", onStorage);
  }, []);

  const patch = useCallback((id: string, fn: (s: Submission) => Submission) => {
    setSubmissions((prev) => prev.map((s) => (s.id === id ? fn(s) : s)));
  }, []);

  // ── contributor actions ───────────────────────────────────────────────────
  const submit = useCallback((input: SubmissionInput): string => {
    const id = uid();
    const fresh: Submission = {
      id,
      filename: input.filename,
      format: input.format,
      sizeLabel: input.sizeLabel,
      initiative: input.initiative,
      targetPlacement: `${input.initiative}/${input.filename}`,
      state: "SUBMITTED",
      provenance: {
        contributor: CURRENT_CONTRIBUTOR,
        author: input.author || CURRENT_CONTRIBUTOR,
        captured_at: now(),
        source_url: input.source_url || `upload://${input.filename}`,
      },
      draft: null,
      curatorEdited: false,
      history: [{ state: "SUBMITTED", at: now(), actor: CURRENT_CONTRIBUTOR }],
    };
    setSubmissions((prev) => [fresh, ...prev]);

    // Mock the auto-draft agents: SUBMITTED → DRAFTED shortly after.
    window.setTimeout(() => {
      patch(id, (s) =>
        s.state === "SUBMITTED"
          ? { ...advance(s, "DRAFTED", "Auto-draft agents (mock)"), draft: generateDraft(input) }
          : s,
      );
    }, 1400);
    return id;
  }, [patch]);

  const openForReview = useCallback((id: string) => {
    patch(id, (s) => (s.state === "DRAFTED" ? advance(s, "UNDER_REVIEW", CURRENT_CONTRIBUTOR) : s));
  }, [patch]);

  const updateDraft = useCallback((id: string, draft: DraftedNote) => {
    // Editing the draft never changes state (UNDER_REVIEW or REJECTED while revising).
    patch(id, (s) => ({ ...s, draft }));
  }, [patch]);

  const contributorApprove = useCallback((id: string) => {
    // STAGE-1 ONLY. The furthest a contributor can move anything is PENDING.
    patch(id, (s) =>
      s.state === "UNDER_REVIEW"
        ? advance(s, "PENDING", CURRENT_CONTRIBUTOR, "Approved for curator review")
        : s,
    );
  }, [patch]);

  const contributorResubmit = useCallback((id: string) => {
    patch(id, (s) =>
      s.state === "REJECTED"
        ? { ...advance(s, "PENDING", CURRENT_CONTRIBUTOR, "Re-submitted after revision"), rejectionReason: undefined }
        : s,
    );
  }, [patch]);

  // ── curator actions (the only path past the stage-2 gate) ───────────────────
  const curatorUpdateDraft = useCallback((id: string, draft: DraftedNote) => {
    patch(id, (s) =>
      s.state === "PENDING"
        ? { ...s, draft, curatorEdited: true, history: [...s.history, { state: s.state, at: now(), actor: CURATOR, note: "Curator override: edited draft" }] }
        : s,
    );
  }, [patch]);

  const curatorApprove = useCallback((id: string) => {
    // STAGE-2 — sign-off queues a controlled single-builder build; it does NOT go live now.
    patch(id, (s) => (s.state === "PENDING" ? advance(s, "QUEUED", CURATOR, "Signed off — queued for build") : s));
  }, [patch]);

  const curatorReject = useCallback((id: string, reason: string) => {
    patch(id, (s) =>
      s.state === "PENDING"
        ? { ...advance(s, "REJECTED", CURATOR, "Returned to contributor"), rejectionReason: reason }
        : s,
    );
  }, [patch]);

  const runBuild = useCallback((): number => {
    // The single-builder step: drain the queue. QUEUED → BUILT now, BUILT → LIVE when the build
    // "finishes". Batched (one build over all queued), never per-approval (design §3).
    let count = 0;
    const builtIds: string[] = [];
    setSubmissions((prev) =>
      prev.map((s) => {
        if (s.state === "QUEUED") {
          count++;
          builtIds.push(s.id);
          return advance(s, "BUILT", "Single-builder build");
        }
        return s;
      }),
    );
    if (builtIds.length === 0) return 0;
    setBuilding(true);
    window.setTimeout(() => {
      setSubmissions((prev) =>
        prev.map((s) => (builtIds.includes(s.id) && s.state === "BUILT" ? advance(s, "LIVE", "Single-builder build") : s)),
      );
      setBuilding(false);
    }, 1800);
    return count;
  }, []);

  const resetDemo = useCallback(() => {
    setSubmissions(SEED_SUBMISSIONS);
    try {
      window.localStorage.setItem(STORE_KEY, JSON.stringify(SEED_SUBMISSIONS));
    } catch {
      /* ignore */
    }
  }, []);

  const value: IngestionContextValue = {
    submissions,
    hydrated,
    building,
    currentContributor: CURRENT_CONTRIBUTOR,
    curator: CURATOR,
    submit,
    openForReview,
    updateDraft,
    contributorApprove,
    contributorResubmit,
    curatorUpdateDraft,
    curatorApprove,
    curatorReject,
    runBuild,
    resetDemo,
  };

  return <IngestionContext.Provider value={value}>{children}</IngestionContext.Provider>;
}

export function useIngestion(): IngestionContextValue {
  const ctx = useContext(IngestionContext);
  if (!ctx) throw new Error("useIngestion must be used within an IngestionProvider");
  return ctx;
}
