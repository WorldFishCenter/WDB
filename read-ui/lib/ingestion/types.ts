/**
 * Ingestion ("write-side") prototype — data shapes.
 *
 * ⚠️ MOCK / PROTOTYPE. These types model the contribution pipeline as a *frontend fixture*.
 * There is NO ingestion backend yet (the read UI was fixtures-first before Live; this is the same
 * stage for the write side). Every shape here MIRRORS the eventual ingestion API described in
 * docs/ingestion-pipeline-design.md so wiring a real backend later is a swap, not a rewrite:
 *
 *   • A `Submission` mirrors a row of the **ingestion workflow state** the design parks in Atlas
 *     (design §6/§8): the state machine, the draft-while-in-review, provenance index, audit trail.
 *   • A `DraftedNote` mirrors the **companion note** the `wdb-curator`/`dict-enricher` agents draft
 *     (PROTOCOL §6 Template A/B). In the real pipeline this is a transient DB working copy until
 *     curator sign-off, at which point it is written to **git** (design §5 — the hard handoff).
 *   • `Provenance` mirrors the four PROTOCOL §8 frontmatter fields graphify carries onto nodes,
 *     stamped at SUBMITTED (design §4).
 */

/**
 * The contribution state machine (design §1.3). A contribution moves left→right through the two
 * gates; CURATOR_OVERRIDE is a reactive side-path, not a stage. REJECTED is the curator sending a
 * pending item back to the contributor.
 *
 *   SUBMITTED → DRAFTED → UNDER_REVIEW → PENDING → QUEUED → BUILT → LIVE
 *                         (stage-1 gate)  (stage-2 gate)   (single-builder build)
 */
export type WorkflowState =
  | "SUBMITTED" //     uploaded; provenance stamped; awaiting the auto-draft agents
  | "DRAFTED" //       agents produced the companion-note draft
  | "UNDER_REVIEW" //  contributor is reading/editing the draft
  | "PENDING" //       contributor approved → awaiting CURATOR sign-off (the stage-2 gate)
  | "QUEUED" //        curator signed off → in the build queue (NOT live yet)
  | "BUILT" //         the single-builder build ran; artifacts produced
  | "LIVE" //          published; the read UI can see it
  | "REJECTED"; //     curator sent it back to the contributor with a reason

/** Phase-1 accepts PDF / tabular / docs (design §5); richer formats are shown but disabled. */
export type Phase1Format = "pdf" | "tabular" | "doc";
export type LaterFormat = "video" | "image" | "url";
export type ContributionFormat = Phase1Format | LaterFormat;

/**
 * Provenance — the four PROTOCOL §8 fields graphify carries onto a file's nodes, stamped at
 * submission (design §4). `contributor` (who brought it into WDB) is kept DISTINCT from `author`
 * (who made the underlying content); "your knowledge" is later a filter over the one graph, never
 * a per-user fork.
 */
export interface Provenance {
  contributor: string; // the WDB user who submitted the content
  author: string; //      the underlying content's real author (may differ from contributor)
  captured_at: string; // ISO submission timestamp (the one "as-of" stamp)
  source_url: string; //  where the content came from (upload origin / external link)
}

/** Which companion-note template the draft follows (PROTOCOL §6). */
export type NoteTemplate = "A" | "B";

/** A column entry in a Template-A data dictionary (`## Columns`). */
export interface ColumnEntry {
  name: string; //    column_name
  meaning: string; // plain-English meaning
  domain: string; //  value domain (distinct set, range, or count + examples)
}

/**
 * The drafted companion note — faithful to PROTOCOL §6. Structured (not raw markdown) so the editor
 * can render the protocol shape and serialize back to `<file>_dict.md` / `<file>_context.md`.
 * Template A = tabular (`## Grain` + `## Columns`); Template B = everything else (`## Key concepts`).
 */
export interface DraftedNote {
  template: NoteTemplate;
  filename: string; //        e.g. kenya_yield_2025_dict.md  /  grant_proposal_context.md
  title: string; //           the `# H1` — "Data dictionary: …" / "Context: …"
  summary: string; //         `## Summary`
  grain?: string; //          `## Grain` — Template A only (what one row IS, domain terms)
  columns?: ColumnEntry[]; // `## Columns` — Template A only
  keyConcepts?: string[]; //  `## Key concepts / entities` — Template B only
  relatedFiles: string[]; //  `## Related files` — the wiring (cross-initiative links first)
  notesCaveats?: string; //   `## Notes / caveats` — Template A optional
}

/** One audit-trail entry — who moved the contribution to a state, and when (design §8 audit log). */
export interface HistoryEntry {
  state: WorkflowState;
  at: string; //    ISO timestamp
  actor: string; // who caused the transition ("Auto-draft agents", a contributor, the curator)
  note?: string; // optional detail (e.g. a rejection reason, "curator override")
}

/**
 * A single contribution flowing through the pipeline — one row of the workflow state the design
 * parks in Atlas (design §8). The `draft` is the transient working copy; `targetPlacement` is the
 * Project-First path the note + file would land at on sign-off.
 */
export interface Submission {
  id: string;
  filename: string; //          the uploaded source file
  format: ContributionFormat;
  sizeLabel: string; //         human size, e.g. "2.4 MB" (display only in the mock)
  initiative: string; //        target initiative folder (Project-First placement)
  targetPlacement: string; //   where the file + note land, e.g. "peskas/kenya_yield_2025.csv"
  state: WorkflowState;
  provenance: Provenance;
  draft: DraftedNote | null; //  produced at DRAFTED; null while SUBMITTED
  curatorEdited: boolean; //     true once the curator used CURATOR_OVERRIDE on the draft
  rejectionReason?: string; //   set when the curator rejects → REJECTED
  history: HistoryEntry[]; //    append-only audit trail, newest last
}

/** Input the contributor fills on the submit form (mock — the real API would take multipart). */
export interface SubmissionInput {
  filename: string;
  format: Phase1Format;
  sizeLabel: string;
  initiative: string;
  author: string;
  source_url: string;
}
