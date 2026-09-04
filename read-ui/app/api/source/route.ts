/**
 * Read-only source viewer: returns the text of a citation's source note/doc so a quote or a
 * graph edge is "clickable to its source." Strictly local and read-only — it only READS files
 * the citations already name, never writes.
 *
 * Safety: the requested path is resolved under the KNOWLEDGE-BASE root and rejected if it escapes
 * (path traversal) or isn't an allow-listed text type. Binary sources (PDF/CSV/images) aren't
 * streamed here — the UI shows their path + the evidence the citation already carries (B's
 * verbatim quote, C's rows). Markdown notes and the converted .md docs ARE served, which is
 * where the prose lives.
 *
 * The KB root is resolved by `lib/kbRoot.ts`, not inline here: it used to be a cwd-relative
 * expression that silently pointed at the wrong place when the dev server was started outside
 * `read-ui/`, and a wrong root was indistinguishable from an empty knowledge graph. A KB that
 * cannot be located is now a 503 that says what to set.
 */

import { readFile } from "node:fs/promises";
import path from "node:path";
import { NextResponse } from "next/server";

import { KbRootNotFound, resolveInKb } from "@/lib/kbRoot";

const TEXT_EXT = new Set([".md", ".txt", ".csv", ".json", ".yml", ".yaml", ".py", ".sql"]);

export async function GET(request: Request) {
  const rel = new URL(request.url).searchParams.get("path");
  if (!rel) {
    return NextResponse.json({ error: "Missing ?path=" }, { status: 400 });
  }

  let target: { root: string; resolved: string } | null;
  try {
    target = resolveInKb(rel);
  } catch (e) {
    if (e instanceof KbRootNotFound) {
      // 503, not 404: the knowledge base is misconfigured, not the file missing. Distinguishing
      // the two is the whole point — a bad root used to render as an empty graph.
      return NextResponse.json({ error: e.message, kbMissing: true }, { status: 503 });
    }
    throw e;
  }

  if (!target) {
    return NextResponse.json({ error: "Path escapes the knowledge-base root." }, { status: 403 });
  }

  const ext = path.extname(target.resolved).toLowerCase();
  if (!TEXT_EXT.has(ext)) {
    return NextResponse.json(
      { error: `Not a viewable text source (${ext || "no extension"}).`, viewable: false, path: rel },
      { status: 415 },
    );
  }

  try {
    let text = await readFile(target.resolved, "utf8");
    // CSVs can be huge — cap the preview so the modal stays responsive.
    if (ext === ".csv" && text.length > 20_000) {
      text = text.slice(0, 20_000) + "\n…(truncated preview)…";
    }
    return NextResponse.json({ path: rel, ext, text });
  } catch {
    return NextResponse.json({ error: `Source not found: ${rel}` }, { status: 404 });
  }
}
