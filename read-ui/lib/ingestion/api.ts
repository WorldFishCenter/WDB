/**
 * Typed client for the ingestion service, via the same-origin `/api/ingest/*` proxy. The TS shapes
 * here are the SAME ones the UI already used for the mock (types.ts) — this is the swap the mock was
 * designed for. Role/identity ride along as headers the proxy forwards; the server enforces the gate.
 */

import type { DraftedNote, Submission, SubmissionInput } from "./types";

export type Role = "contributor" | "curator";

/** The build orchestrator's status (tracked handoff to the pinned /graphify build). */
export interface BuildState {
  status: "IDLE" | "AWAITING_BUILD" | "DONE" | "FAILED";
  command?: string;
  model?: string;
  message?: string;
  handed_off_ids?: string[];
}

const BASE = "/api/ingest";

function h(role: Role, user: string, extra: Record<string, string> = {}): HeadersInit {
  return { "X-WDB-Role": role, "X-WDB-User": user, ...extra };
}

async function json<T>(res: Response): Promise<T> {
  if (!res.ok) {
    let detail = `Request failed (${res.status}).`;
    try {
      const body = await res.json();
      if (body?.error) detail = body.error;
    } catch {
      /* non-JSON */
    }
    throw new Error(detail);
  }
  return res.json() as Promise<T>;
}

export async function health(): Promise<boolean> {
  try {
    const r = await fetch(`${BASE}/health`, { cache: "no-store" });
    return r.ok;
  } catch {
    return false;
  }
}

export async function listSubmissions(role: Role, user: string): Promise<Submission[]> {
  return json(await fetch(`${BASE}/submissions`, { headers: h(role, user), cache: "no-store" }));
}

export async function submit(input: SubmissionInput, bytes: Blob, user: string): Promise<Submission> {
  const q = new URLSearchParams({
    filename: input.filename,
    format: input.format,
    initiative: input.initiative,
    size_label: input.sizeLabel,
    author: input.author ?? "",
    source_url: input.source_url ?? "",
  });
  return json(
    await fetch(`${BASE}/submit?${q.toString()}`, {
      method: "POST",
      headers: h("contributor", user, { "content-type": "application/octet-stream" }),
      body: bytes,
    }),
  );
}

const action = (verb: string) => async (id: string, role: Role, user: string): Promise<Submission> =>
  json(await fetch(`${BASE}/submissions/${id}/${verb}`, { method: "POST", headers: h(role, user) }));

export const openForReview = action("open-review");
export const approve = action("approve");
export const resubmit = action("resubmit");
export const curatorApprove = action("curator-approve");

export async function reject(id: string, reason: string, user: string): Promise<Submission> {
  return json(
    await fetch(`${BASE}/submissions/${id}/reject`, {
      method: "POST",
      headers: h("curator", user, { "content-type": "application/json" }),
      body: JSON.stringify({ reason }),
    }),
  );
}

export async function editDraft(id: string, draft: DraftedNote, role: Role, user: string): Promise<Submission> {
  return json(
    await fetch(`${BASE}/submissions/${id}/draft`, {
      method: "PATCH",
      headers: h(role, user, { "content-type": "application/json" }),
      body: JSON.stringify(draft),
    }),
  );
}

export async function build(user: string): Promise<BuildState> {
  return json(await fetch(`${BASE}/build`, { method: "POST", headers: h("curator", user) }));
}

export async function buildStatus(): Promise<BuildState> {
  return json(await fetch(`${BASE}/build/status`, { cache: "no-store" }));
}

export async function confirmBuild(user: string): Promise<BuildState> {
  return json(await fetch(`${BASE}/build/confirm`, { method: "POST", headers: h("curator", user) }));
}
