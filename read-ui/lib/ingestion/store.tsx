"use client";

/**
 * The ingestion store — now wired to the REAL `wdb_ingest` backend (via the `/api/ingest/*` proxy),
 * replacing the former localStorage mock. The two views share this one store; the role is derived
 * from the route (`/contribute` = contributor, `/curate` = curator) and sent as a header the server
 * enforces the two-stage gate against — so the gate is real, not a UI convention.
 *
 * Honest offline posture (mirrors read-ui's Live/Replay): if the ingestion service is unreachable,
 * `backendOnline` is false and the views show an honest "backend offline" banner with the start
 * command — they do NOT fabricate data. State is polled so SUBMITTED→DRAFTED and the build's
 * QUEUED→BUILT→LIVE appear without manual refresh.
 */

import { createContext, useCallback, useContext, useEffect, useMemo, useRef, useState } from "react";
import { usePathname } from "next/navigation";
import * as api from "./api";
import type { Role, BuildState } from "./api";
import type { DraftedNote, Submission, SubmissionInput } from "./types";

const POLL_MS = 2500;

interface IngestionContextValue {
  submissions: Submission[];
  loading: boolean;
  backendOnline: boolean;
  role: Role;
  currentUser: string;
  build: BuildState | null;
  building: boolean;
  error: string | null;
  refresh: () => Promise<void>;
  submit: (input: SubmissionInput, bytes: Blob) => Promise<Submission | null>;
  openForReview: (id: string) => Promise<void>;
  approve: (id: string) => Promise<void>;
  resubmit: (id: string) => Promise<void>;
  editDraft: (id: string, draft: DraftedNote) => Promise<void>;
  curatorApprove: (id: string) => Promise<void>;
  reject: (id: string, reason: string) => Promise<void>;
  runBuild: () => Promise<void>;
  confirmBuild: () => Promise<void>;
}

const IngestionContext = createContext<IngestionContextValue | null>(null);

export function IngestionProvider({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const role: Role = pathname.startsWith("/curate") ? "curator" : "contributor";
  const currentUser = role === "curator" ? "curator" : "amina.k";

  const [submissions, setSubmissions] = useState<Submission[]>([]);
  const [loading, setLoading] = useState(true);
  const [backendOnline, setBackendOnline] = useState(true);
  const [build, setBuild] = useState<BuildState | null>(null);
  const [error, setError] = useState<string | null>(null);
  const roleRef = useRef(role);
  roleRef.current = role;

  const refresh = useCallback(async () => {
    try {
      const r = roleRef.current;
      const user = r === "curator" ? "curator" : "amina.k";
      const [subs, bs] = await Promise.all([api.listSubmissions(r, user), api.buildStatus()]);
      setSubmissions(subs);
      setBuild(bs);
      setBackendOnline(true);
    } catch {
      setBackendOnline(false);
    } finally {
      setLoading(false);
    }
  }, []);

  // Initial load + poll. Re-fetch immediately when the role (route) changes.
  useEffect(() => {
    setLoading(true);
    refresh();
    const t = setInterval(refresh, POLL_MS);
    return () => clearInterval(t);
  }, [refresh, role]);

  // Wrap an action: run it, surface any gate/role error, then refresh.
  const run = useCallback(
    async (fn: () => Promise<unknown>) => {
      setError(null);
      try {
        await fn();
      } catch (e) {
        setError((e as Error).message);
      } finally {
        await refresh();
      }
    },
    [refresh],
  );

  const submit = useCallback(
    async (input: SubmissionInput, bytes: Blob): Promise<Submission | null> => {
      setError(null);
      try {
        const sub = await api.submit(input, bytes, currentUser);
        await refresh();
        return sub;
      } catch (e) {
        setError((e as Error).message);
        return null;
      }
    },
    [currentUser, refresh],
  );

  const openForReview = useCallback((id: string) => run(() => api.openForReview(id, "contributor", currentUser)), [run, currentUser]);
  const approve = useCallback((id: string) => run(() => api.approve(id, "contributor", currentUser)), [run, currentUser]);
  const resubmit = useCallback((id: string) => run(() => api.resubmit(id, "contributor", currentUser)), [run, currentUser]);
  const editDraft = useCallback((id: string, draft: DraftedNote) => run(() => api.editDraft(id, draft, roleRef.current, currentUser)), [run, currentUser]);
  const curatorApprove = useCallback((id: string) => run(() => api.curatorApprove(id, "curator", currentUser)), [run, currentUser]);
  const reject = useCallback((id: string, reason: string) => run(() => api.reject(id, reason, currentUser)), [run, currentUser]);
  const runBuild = useCallback(() => run(() => api.build(currentUser)), [run, currentUser]);
  const confirmBuild = useCallback(() => run(() => api.confirmBuild(currentUser)), [run, currentUser]);

  const value = useMemo<IngestionContextValue>(
    () => ({
      submissions,
      loading,
      backendOnline,
      role,
      currentUser,
      build,
      building: build?.status === "AWAITING_BUILD",
      error,
      refresh,
      submit,
      openForReview,
      approve,
      resubmit,
      editDraft,
      curatorApprove,
      reject,
      runBuild,
      confirmBuild,
    }),
    [submissions, loading, backendOnline, role, currentUser, build, error, refresh, submit, openForReview, approve, resubmit, editDraft, curatorApprove, reject, runBuild, confirmBuild],
  );

  return <IngestionContext.Provider value={value}>{children}</IngestionContext.Provider>;
}

export function useIngestion(): IngestionContextValue {
  const ctx = useContext(IngestionContext);
  if (!ctx) throw new Error("useIngestion must be used within an IngestionProvider");
  return ctx;
}
