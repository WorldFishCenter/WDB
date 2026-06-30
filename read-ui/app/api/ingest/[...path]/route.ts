/**
 * Server-side proxy to the local ingestion FastAPI (`wdb_ingest`), same pattern as the read UI's
 * `/api/answer` proxy: the browser never calls the service cross-origin; this same-origin catch-all
 * forwards method, query, body, and the role/identity headers to WDB_INGEST_URL and returns the
 * response verbatim. Keeps the ingestion service untouched (no CORS middleware needed).
 */

import { NextRequest, NextResponse } from "next/server";

const INGEST_URL = process.env.WDB_INGEST_URL || "http://127.0.0.1:8001";
const FORWARD_HEADERS = ["x-wdb-role", "x-wdb-user", "content-type"];

async function proxy(req: NextRequest, path: string[]) {
  const url = new URL(req.url);
  const target = `${INGEST_URL}/${path.join("/")}${url.search}`;

  const headers: Record<string, string> = {};
  for (const h of FORWARD_HEADERS) {
    const v = req.headers.get(h);
    if (v) headers[h] = v;
  }

  const init: RequestInit = { method: req.method, headers, signal: AbortSignal.timeout(120_000) };
  if (req.method !== "GET" && req.method !== "HEAD") {
    init.body = await req.arrayBuffer();
  }

  let upstream: Response;
  try {
    upstream = await fetch(target, init);
  } catch {
    return NextResponse.json(
      { error: `Ingestion backend unreachable at ${INGEST_URL}. Start it: uv run uvicorn wdb_ingest.app:app --port 8001` },
      { status: 502 },
    );
  }

  const body = await upstream.arrayBuffer();
  return new NextResponse(body, {
    status: upstream.status,
    headers: { "content-type": upstream.headers.get("content-type") || "application/json" },
  });
}

type Ctx = { params: { path: string[] } };

export async function GET(req: NextRequest, { params }: Ctx) {
  return proxy(req, params.path);
}
export async function POST(req: NextRequest, { params }: Ctx) {
  return proxy(req, params.path);
}
export async function PATCH(req: NextRequest, { params }: Ctx) {
  return proxy(req, params.path);
}
