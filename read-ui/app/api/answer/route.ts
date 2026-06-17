/**
 * Server-side proxy to the local Phase-A1 FastAPI (`POST /answer`).
 *
 * Why a proxy and not a direct browser fetch: the read UI must NOT modify wdb_api, and the API
 * has no CORS middleware — so the browser can't call it cross-origin. This same-origin route
 * forwards the question to WDB_API_URL (default http://127.0.0.1:8000) and returns the API's
 * JSON verbatim. It adds NO interpretation: the UI renders exactly what the router grounded.
 */

import { NextResponse } from "next/server";

const API_URL = process.env.WDB_API_URL || "http://127.0.0.1:8000";

export async function POST(request: Request) {
  let question: unknown;
  try {
    ({ question } = await request.json());
  } catch {
    return NextResponse.json({ error: "Body must be JSON: { question }" }, { status: 400 });
  }

  if (typeof question !== "string" || question.trim().length === 0) {
    return NextResponse.json({ error: "A non-empty question is required." }, { status: 400 });
  }

  let upstream: Response;
  try {
    upstream = await fetch(`${API_URL}/answer`, {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({ question: question.trim() }),
      // the router can take a moment under Live; generous but bounded
      signal: AbortSignal.timeout(120_000),
    });
  } catch {
    return NextResponse.json(
      {
        error: `Could not reach the WDB API at ${API_URL}. Start it with: uv run uvicorn wdb_api.app:app`,
      },
      { status: 502 },
    );
  }

  if (!upstream.ok) {
    const text = await upstream.text().catch(() => "");
    return NextResponse.json(
      { error: `WDB API error (${upstream.status}): ${text.slice(0, 500)}` },
      { status: upstream.status === 422 ? 400 : 502 },
    );
  }

  // Faithful pass-through — return exactly what the API returned.
  const data = await upstream.json();
  return NextResponse.json(data);
}
