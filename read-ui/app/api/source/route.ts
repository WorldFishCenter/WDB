/**
 * Read-only source viewer: returns the text of a citation's source note/doc so a quote or a
 * graph edge is "clickable to its source." Strictly local and read-only — it only READS files
 * the citations already name, never writes.
 *
 * Safety: the requested path is resolved under WDB_ROOT and rejected if it escapes (path
 * traversal) or isn't an allow-listed text type. Binary sources (PDF/CSV/images) aren't streamed
 * here — the UI shows their path + the evidence the citation already carries (B's verbatim quote,
 * C's rows). Markdown notes and the converted .md docs ARE served, which is where the prose lives.
 */

import { readFile } from "node:fs/promises";
import path from "node:path";
import { NextResponse } from "next/server";

// Default: the WDB repo root is one level up from read-ui/.
const WDB_ROOT = process.env.WDB_ROOT || path.resolve(process.cwd(), "..");
const TEXT_EXT = new Set([".md", ".txt", ".csv", ".json", ".yml", ".yaml", ".py", ".sql"]);

export async function GET(request: Request) {
  const rel = new URL(request.url).searchParams.get("path");
  if (!rel) {
    return NextResponse.json({ error: "Missing ?path=" }, { status: 400 });
  }

  const resolved = path.resolve(WDB_ROOT, rel);
  const rootPrefix = WDB_ROOT.endsWith(path.sep) ? WDB_ROOT : WDB_ROOT + path.sep;
  if (resolved !== WDB_ROOT && !resolved.startsWith(rootPrefix)) {
    return NextResponse.json({ error: "Path escapes the repository root." }, { status: 403 });
  }

  const ext = path.extname(resolved).toLowerCase();
  if (!TEXT_EXT.has(ext)) {
    return NextResponse.json(
      { error: `Not a viewable text source (${ext || "no extension"}).`, viewable: false, path: rel },
      { status: 415 },
    );
  }

  try {
    let text = await readFile(resolved, "utf8");
    // CSVs can be huge — cap the preview so the modal stays responsive.
    if (ext === ".csv" && text.length > 20_000) {
      text = text.slice(0, 20_000) + "\n…(truncated preview)…";
    }
    return NextResponse.json({ path: rel, ext, text });
  } catch {
    return NextResponse.json({ error: `Source not found: ${rel}` }, { status: 404 });
  }
}
