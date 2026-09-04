/**
 * The knowledge-base root, resolved once — server-side only.
 *
 * This is the TypeScript half of what `wdb_paths.py` owns on the Python side. It cannot import
 * that module, so the rule is restated here in exactly one place rather than inlined at each
 * route.
 *
 * The previous derivation, inline in `app/api/source/route.ts`, was:
 *
 *     process.env.WDB_KB || path.resolve(process.cwd(), "..", "knowledge_base")
 *
 * Two problems. It was **cwd-relative**, so it silently resolved to the wrong place when the dev
 * server was started from the repo root rather than from `read-ui/` — and when it was wrong the
 * route returned a JSON `{error}` that `lib/graphData.ts` discarded, so a misconfigured KB looked
 * exactly like an empty knowledge graph. Nothing said the root was wrong.
 *
 * So: search upward for the KB instead of assuming one relative level, and make "not found" an
 * explicit, actionable failure rather than a silent empty result.
 */

import { existsSync, statSync } from "node:fs";
import path from "node:path";

/** Thrown when no knowledge base can be located — a configuration error, not a missing file. */
export class KbRootNotFound extends Error {
  constructor(searched: string[]) {
    super(
      "Could not locate the knowledge base. Set WDB_KB in read-ui/.env.local to its absolute " +
        `path (see .env.local.example). Searched: ${searched.join(", ")}`,
    );
    this.name = "KbRootNotFound";
  }
}

let cached: string | null = null;

function isDir(p: string): boolean {
  try {
    return existsSync(p) && statSync(p).isDirectory();
  } catch {
    return false;
  }
}

/**
 * Resolve the KB root, or throw {@link KbRootNotFound}.
 *
 * `WDB_KB` is authoritative when set — and is validated, so a typo fails loudly here instead of
 * turning every citation into a 404. Otherwise walk up from the working directory looking for a
 * `knowledge_base/` sibling, which finds it whether the dev server was started in `read-ui/` or
 * at the repo root.
 */
export function kbRoot(): string {
  if (cached) return cached;

  const fromEnv = process.env.WDB_KB?.trim();
  if (fromEnv) {
    const resolved = path.resolve(fromEnv);
    if (!isDir(resolved)) throw new KbRootNotFound([`WDB_KB=${fromEnv}`]);
    cached = resolved;
    return cached;
  }

  const searched: string[] = [];
  let dir = process.cwd();
  for (let up = 0; up < 4; up++) {
    const candidate = path.join(dir, "knowledge_base");
    searched.push(candidate);
    if (isDir(candidate)) {
      cached = candidate;
      return cached;
    }
    const parent = path.dirname(dir);
    if (parent === dir) break;
    dir = parent;
  }
  throw new KbRootNotFound(searched);
}

/** Resolve a KB-relative path inside the root, or `null` if it would escape (traversal guard). */
export function resolveInKb(rel: string): { root: string; resolved: string } | null {
  const root = kbRoot();
  const resolved = path.resolve(root, rel);
  const prefix = root.endsWith(path.sep) ? root : root + path.sep;
  if (resolved !== root && !resolved.startsWith(prefix)) return null;
  return { root, resolved };
}
