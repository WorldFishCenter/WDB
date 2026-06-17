/**
 * Client-side helper that talks to the SAME-ORIGIN Next route handlers, which proxy to the
 * local Phase-A1 FastAPI. The browser never calls the API cross-origin (no CORS middleware is
 * added to wdb_api — the API is left untouched per the build's scope limits); the server route
 * forwards the request. See app/api/answer/route.ts.
 */

import type { RouterAnswer } from "./contract";

export class ApiError extends Error {
  constructor(
    message: string,
    public readonly kind: "unreachable" | "bad_request" | "server",
  ) {
    super(message);
    this.name = "ApiError";
  }
}

export async function askQuestion(question: string): Promise<RouterAnswer> {
  let res: Response;
  try {
    res = await fetch("/api/answer", {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({ question }),
    });
  } catch {
    throw new ApiError("Could not reach the read UI server.", "unreachable");
  }

  if (!res.ok) {
    let detail = `Request failed (${res.status}).`;
    try {
      const body = await res.json();
      if (body?.error) detail = body.error;
    } catch {
      /* ignore non-JSON error bodies */
    }
    if (res.status === 502 || res.status === 504) {
      throw new ApiError(detail, "unreachable");
    }
    throw new ApiError(detail, res.status === 400 ? "bad_request" : "server");
  }

  return (await res.json()) as RouterAnswer;
}
