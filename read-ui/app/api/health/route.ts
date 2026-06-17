/**
 * Proxy to the Phase-A1 API's `/health`, so the UI can honestly show which backend it is talking
 * to (Replay vs Live) and whether the API is reachable at all. Server-side, same-origin.
 */

import { NextResponse } from "next/server";

const API_URL = process.env.WDB_API_URL || "http://127.0.0.1:8000";

export async function GET() {
  try {
    const res = await fetch(`${API_URL}/health`, { signal: AbortSignal.timeout(5_000) });
    if (!res.ok) {
      return NextResponse.json({ ok: false, target: API_URL }, { status: 200 });
    }
    const data = await res.json();
    return NextResponse.json({ ok: true, target: API_URL, ...data });
  } catch {
    return NextResponse.json({ ok: false, target: API_URL }, { status: 200 });
  }
}
