/**
 * The WDB read-API answer contract — TypeScript types of the ACTUAL JSON captured from
 * `POST /answer` in STEP 0 (see read-ui/fixtures/*.json). The UI renders THESE shapes, not an
 * assumed schema. Mirrors wdb_api/serialize.py: a faithful pass-through of wdb_router's §6
 * RouterAnswer — every claim with its mode tag and native, mode-specific citation, the merged
 * associations, Mode-C figures, and the `unanswered` list.
 *
 * The honesty surface lives in the citation union: a claim's citation IS a *different artifact*
 * per mode (keyed by `claim.mode`):
 *   A — a graph edge triple + EXTRACTED/INFERRED confidence
 *   B — a verbatim passage quote + its span + the graph node(s) it resolves to
 *   C — the SQL + the result rows it computed
 *
 * `verdict` is the field that distinguishes a VERIFIED_NEGATIVE — "we checked the graph and it
 * records no connection", a correct answer — from an UNGROUNDED refusal. The two are identical
 * on every other field (no claims, no figures), so before `verdict` existed the UI could only
 * infer refusal from empty lists, and rendered Mode A's honest negative as "the knowledge base
 * doesn't cover this".
 */

export type Mode = "A" | "B" | "C";
export type Confidence = "EXTRACTED" | "INFERRED" | "";

/** What the answer actually determined (wdb_contract.Verdict). */
export type Verdict = "GROUNDED" | "VERIFIED_NEGATIVE" | "UNGROUNDED";

/**
 * Why a part could not be grounded — the stable key, distinct from its prose.
 * Branch on `code`; display `text`. Mirrors wdb_contract.UnansweredCode.
 */
export type UnansweredCode =
  | "NO_ENTITY_MATCH"
  | "NO_RELATIONSHIP"
  | "NOT_CONNECTED"
  | "CITE_CHECK_DOWNGRADE"
  | "NO_PASSAGE"
  | "THIN_RETRIEVAL"
  | "NO_COVERAGE"
  | "NO_CITABLE_PASSAGE"
  | "NO_TABLE_RESOLVED"
  | "NEEDS_DISAMBIGUATION"
  | "OUT_OF_BAND"
  | "EMPTY_RESULT"
  | "EXECUTION_FAILED"
  | "NO_RECORDED_REPLAY"
  | "UNSPECIFIED";

export interface UnansweredDetail {
  part: string;
  mode: Mode;
  code: UnansweredCode;
  detail: string;
  text: string; // "{part} — {detail}", the string `unanswered[]` carries
  candidates: string[]; // NEEDS_DISAMBIGUATION carries the sister tables here
}

/** Mode A citation — the graph edge that grounds the relationship. */
export interface CitationA {
  source_file: string; // the companion note / doc that stated the edge (the join key)
  note: string; // source-location label, e.g. "Validation; Methods 2.3" ("" if none)
  locator: string; // the edge triple "src --relation--> tgt"
  confidence: Confidence; // EXTRACTED (stated) | INFERRED (flagged, not hard fact)
}

/** Mode B citation — the passage span + verbatim quote + matching graph node(s). */
export interface CitationB {
  source_file: string; // WDB-relative path of the source doc
  note: string; // companion-note pointer, e.g. "..._context.md" ("" if none)
  location: string; // civ-kb mechanical span, e.g. "page 2 [part 4/4]"
  quote: string; // the verbatim passage text (the span) — the evidence
  nodes: string[]; // matching graph node id(s) at document grain
}

/** Mode C citation — the exact query and the rows it returned (the computation IS the citation). */
export interface CitationC {
  source_file: string; // WDB-relative CSV path
  note: string; // companion-note section, e.g. "kenya_validated_trips_dict.md#Grain"
  sql: string; // the exact query
  result: Row[]; // the result row(s)
}

export type Row = Record<string, string | number | boolean | null>;
export type Citation = CitationA | CitationB | CitationC;

export interface Claim {
  mode: Mode;
  text: string;
  citations: Citation[]; // ≥1 always (§6 r1: no claim without a citation)
}

/** A merged graph edge in the associations payload (plain graph.json edge dicts). */
export interface Association {
  source: string;
  relation: string;
  target: string;
  confidence?: Confidence;
  confidence_score?: number;
  weight?: number;
  source_file?: string;
  source_location?: string | null;
}

/** A Mode-C figure — the chart spec ships with its own SQL and the rows it charts. */
export interface Figure {
  spec: { kind: string; x: string; y: string; [k: string]: unknown };
  query: string;
  result: Row[];
}

export interface Route {
  mode: Mode;
  reason: string; // the signal that selected the mode (transparency)
}

/** The whole `POST /answer` response. */
export interface RouterAnswer {
  question: string;
  answered: boolean; // false = full refusal (no claim, no figure)
  modes_fired: Mode[]; // modes routed-to
  modes_grounded: Mode[]; // modes that actually contributed a claim/figure
  routes: Route[];
  claims: Claim[];
  associations: Association[];
  figures: Figure[];
  unanswered: string[]; // parts no mode could ground — stated, never hidden (§6 r4)
  verdict: Verdict; // GROUNDED | VERIFIED_NEGATIVE | UNGROUNDED
  unanswered_detail: UnansweredDetail[]; // the same parts, with a code to branch on
}

// ---- narrowing (citation shape is keyed off the owning claim's mode) ----
//
// These were three unchecked `as` casts behind a comment that said "narrowing". They are real
// type guards now: each checks the field that actually distinguishes its shape, so a server
// whose citation shape has drifted is caught at the point of use instead of throwing a
// TypeError deep inside a render.

export function isCitationA(c: Citation): c is CitationA {
  return typeof (c as CitationA).locator === "string";
}
export function isCitationB(c: Citation): c is CitationB {
  return Array.isArray((c as CitationB).nodes) && typeof (c as CitationB).quote === "string";
}
export function isCitationC(c: Citation): c is CitationC {
  return typeof (c as CitationC).sql === "string";
}

/** Narrow or throw — use where the owning claim's mode already promises the shape. */
export function citationA(c: Citation): CitationA {
  if (!isCitationA(c)) throw new TypeError("Mode-A citation is missing `locator`");
  return c;
}
export function citationB(c: Citation): CitationB {
  if (!isCitationB(c)) throw new TypeError("Mode-B citation is missing `nodes`/`quote`");
  return c;
}
export function citationC(c: Citation): CitationC {
  if (!isCitationC(c)) throw new TypeError("Mode-C citation is missing `sql`");
  return c;
}

export const MODE_LABEL: Record<Mode, string> = {
  A: "Graph fact",
  B: "Grounded passage",
  C: "Computed figure",
};

export const MODE_BLURB: Record<Mode, string> = {
  A: "A committed relationship in the knowledge graph",
  B: "A verbatim quote from a source document",
  C: "A number computed from data, with its query",
};
