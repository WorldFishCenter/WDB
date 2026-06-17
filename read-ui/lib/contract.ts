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
 */

export type Mode = "A" | "B" | "C";
export type Confidence = "EXTRACTED" | "INFERRED" | "";

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
}

// ---- narrowing helpers (citation shape is keyed off the owning claim's mode) ----

export function citationA(c: Citation): CitationA {
  return c as CitationA;
}
export function citationB(c: Citation): CitationB {
  return c as CitationB;
}
export function citationC(c: Citation): CitationC {
  return c as CitationC;
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
