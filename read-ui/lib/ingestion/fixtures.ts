/**
 * Seed fixtures for the ingestion prototype — a few in-flight contributions spread across the state
 * machine so BOTH views are populated on first load and the two-stage gate is demonstrable end to
 * end. MOCK data; the real ingestion API (design §8) would return these same shapes from Atlas.
 *
 * Two identities drive the demo:
 *   • CURRENT_CONTRIBUTOR — "you" in the contributor view (sees your own submissions, any state).
 *   • CURATOR            — "you" in the curator view (sees everyone's PENDING queue).
 * Some seeds belong to a second contributor so the curator queue shows real multi-contributor flow.
 */
import type { Submission } from "./types";

export const CURRENT_CONTRIBUTOR = "amina.k";
export const CURATOR = "curator";

/** localStorage key — the prototype's shared, persisted workflow state (no backend). */
export const STORE_KEY = "wdb.ingestion.v1";

export const SEED_SUBMISSIONS: Submission[] = [
  // ── F: fresh, just auto-drafted — gives the CONTRIBUTOR view an actionable item on load ────────
  {
    id: "sub_pondcube_feed",
    filename: "pondcube_feed_trials_2026.csv",
    format: "tabular",
    sizeLabel: "418 KB",
    initiative: "digital_transformation_accelerator",
    targetPlacement: "digital_transformation_accelerator/pondcube_feed_trials_2026.csv",
    state: "DRAFTED",
    provenance: {
      contributor: CURRENT_CONTRIBUTOR,
      author: "PondCube trials team",
      captured_at: "2026-06-24T08:12:00Z",
      source_url: "upload://pondcube_feed_trials_2026.csv",
    },
    curatorEdited: false,
    history: [
      { state: "SUBMITTED", at: "2026-06-24T08:12:00Z", actor: "amina.k" },
      { state: "DRAFTED", at: "2026-06-24T08:12:40Z", actor: "Auto-draft agents (mock)" },
    ],
    draft: {
      template: "A",
      filename: "pondcube_feed_trials_2026_dict.md",
      title: "Data dictionary: pondcube_feed_trials_2026.csv",
      summary:
        "Feed-conversion trial measurements from the 2026 PondCube cohort. Part of the Digital Transformation Accelerator initiative.",
      grain:
        "One row = one feeding observation for one pond on one day, keyed by (pond_id, obs_date). pond_id repeats across days; aggregate per-pond stats over its rows.",
      columns: [
        { name: "pond_id", meaning: "unique pond identifier (joins to pond_registry)", domain: "identifier, 48 distinct" },
        { name: "obs_date", meaning: "observation date (YYYY-MM-DD)", domain: "2026-01-09 → 2026-05-30" },
        { name: "feed_kg", meaning: "feed delivered that day, kilograms", domain: "range 0.0–22.4 (6 missing)" },
        { name: "biomass_kg", meaning: "estimated standing biomass, kilograms", domain: "range 12.5–410.0" },
        { name: "feed_type", meaning: "feed formulation used", domain: "3 distinct ∈ {starter, grower, finisher}" },
      ],
      relatedFiles: [
        "pondcube_about.md (the initiative this trial belongs to)",
        "../peskas/peskas_about.md (shares the small-scale aquaculture monitoring approach)",
      ],
      notesCaveats: "Blank feed_kg means no feeding logged that day, not zero feed available.",
    },
  },

  // ── A: PENDING — contributor approved + handed off; sits in the CURATOR queue (amina's) ─────────
  {
    id: "sub_kwale_catch",
    filename: "kwale_catch_survey_2026.csv",
    format: "tabular",
    sizeLabel: "1.2 MB",
    initiative: "peskas",
    targetPlacement: "peskas/kwale_catch_survey_2026.csv",
    state: "PENDING",
    provenance: {
      contributor: CURRENT_CONTRIBUTOR,
      author: "Peskas field enumerators (Kwale)",
      captured_at: "2026-06-22T14:03:00Z",
      source_url: "upload://kwale_catch_survey_2026.csv",
    },
    curatorEdited: false,
    history: [
      { state: "SUBMITTED", at: "2026-06-22T14:03:00Z", actor: "amina.k" },
      { state: "DRAFTED", at: "2026-06-22T14:03:40Z", actor: "Auto-draft agents (mock)" },
      { state: "UNDER_REVIEW", at: "2026-06-22T14:20:00Z", actor: "amina.k" },
      { state: "PENDING", at: "2026-06-22T14:31:00Z", actor: "amina.k", note: "Approved for curator review" },
    ],
    draft: {
      template: "A",
      filename: "kwale_catch_survey_2026_dict.md",
      title: "Data dictionary: kwale_catch_survey_2026.csv",
      summary:
        "Catch-survey landings recorded by Peskas enumerators in Kwale County, Kenya, over the 2026 season.",
      grain:
        "One row = one catch item of a landing trip, keyed by (trip_id, species). trip_id and landing_site repeat across the trip's catch items.",
      columns: [
        { name: "trip_id", meaning: "unique landing-trip identifier", domain: "identifier, 2,140 distinct" },
        { name: "landing_site", meaning: "the landing site of the trip", domain: "9 distinct ∈ {Gazi, Msambweni, Shimoni, …}" },
        { name: "species", meaning: "species of the catch item", domain: "37 distinct" },
        { name: "weight_kg", meaning: "weight of the catch item, kilograms", domain: "range 0.1–64.0" },
        { name: "trip_date", meaning: "date the trip landed (YYYY-MM-DD)", domain: "2026-01-04 → 2026-06-18" },
      ],
      relatedFiles: [
        "peskas_about.md (Peskas — the platform this survey feeds)",
        "../ssf_research/ (shared small-scale-fisheries survey design)",
      ],
      notesCaveats: "Weights are landed weight, not live weight. Three trips have a single unidentified species row.",
    },
  },

  // ── E: PENDING — a SECOND contributor's item, so the curator queue is genuinely multi-person ────
  {
    id: "sub_fasa_partners",
    filename: "fasa_partner_directory.pdf",
    format: "pdf",
    sizeLabel: "640 KB",
    initiative: "fasa",
    targetPlacement: "fasa/fasa_partner_directory.pdf",
    state: "PENDING",
    provenance: {
      contributor: "john.m",
      author: "FASA programme office",
      captured_at: "2026-06-23T09:40:00Z",
      source_url: "https://fasa.example.org/partners",
    },
    curatorEdited: false,
    history: [
      { state: "SUBMITTED", at: "2026-06-23T09:40:00Z", actor: "john.m" },
      { state: "DRAFTED", at: "2026-06-23T09:40:38Z", actor: "Auto-draft agents (mock)" },
      { state: "UNDER_REVIEW", at: "2026-06-23T10:05:00Z", actor: "john.m" },
      { state: "PENDING", at: "2026-06-23T10:12:00Z", actor: "john.m", note: "Approved for curator review" },
    ],
    draft: {
      template: "B",
      filename: "fasa_partner_directory_context.md",
      title: "Context: fasa_partner_directory.pdf",
      summary:
        "Directory of implementing and research partners in the FASA programme, with their roles and focal countries.",
      keyConcepts: [
        "FASA implementing partners; focal countries; research vs delivery roles",
        "Aligns with the FASA optimization-engine work in fasa_repo_about.md",
      ],
      relatedFiles: [
        "fasa_about.md (the FASA programme hub this directory belongs to)",
        "fasa_repo_about.md (the engine child of the FASA hub)",
      ],
    },
  },

  // ── B: QUEUED — curator signed off; awaiting the single-builder build (amina's) ─────────────────
  {
    id: "sub_fasa_proposal",
    filename: "fasa_scaleup_proposal.pdf",
    format: "pdf",
    sizeLabel: "2.1 MB",
    initiative: "fasa",
    targetPlacement: "fasa/fasa_scaleup_proposal.pdf",
    state: "QUEUED",
    provenance: {
      contributor: CURRENT_CONTRIBUTOR,
      author: "FASA programme office",
      captured_at: "2026-06-20T11:15:00Z",
      source_url: "upload://fasa_scaleup_proposal.pdf",
    },
    curatorEdited: true,
    history: [
      { state: "SUBMITTED", at: "2026-06-20T11:15:00Z", actor: "amina.k" },
      { state: "DRAFTED", at: "2026-06-20T11:15:42Z", actor: "Auto-draft agents (mock)" },
      { state: "UNDER_REVIEW", at: "2026-06-20T11:40:00Z", actor: "amina.k" },
      { state: "PENDING", at: "2026-06-20T11:55:00Z", actor: "amina.k", note: "Approved for curator review" },
      { state: "QUEUED", at: "2026-06-21T08:30:00Z", actor: "curator", note: "Curator override: tightened summary; signed off" },
    ],
    draft: {
      template: "B",
      filename: "fasa_scaleup_proposal_context.md",
      title: "Context: fasa_scaleup_proposal.pdf",
      summary:
        "2026 scale-up funding proposal for FASA — objectives, target geographies, and the optimization-engine rationale.",
      keyConcepts: [
        "FASA scale-up objectives; target geographies; budget envelope",
        "Builds on the FASA optimization engine documented in fasa_repo_about.md",
      ],
      relatedFiles: [
        "fasa_about.md (the FASA programme this proposal would fund)",
        "../digital_transformation_accelerator/ (shared cloud-data approach)",
      ],
    },
  },

  // ── C: LIVE — already built and published (amina's) — the honest end state ──────────────────────
  {
    id: "sub_ssf_methods",
    filename: "ssf_survey_methods.md",
    format: "doc",
    sizeLabel: "36 KB",
    initiative: "ssf_research",
    targetPlacement: "ssf_research/ssf_survey_methods.md",
    state: "LIVE",
    provenance: {
      contributor: CURRENT_CONTRIBUTOR,
      author: "amina.k",
      captured_at: "2026-06-12T10:00:00Z",
      source_url: "upload://ssf_survey_methods.md",
    },
    curatorEdited: false,
    history: [
      { state: "SUBMITTED", at: "2026-06-12T10:00:00Z", actor: "amina.k" },
      { state: "DRAFTED", at: "2026-06-12T10:00:36Z", actor: "Auto-draft agents (mock)" },
      { state: "UNDER_REVIEW", at: "2026-06-12T10:25:00Z", actor: "amina.k" },
      { state: "PENDING", at: "2026-06-12T10:40:00Z", actor: "amina.k", note: "Approved for curator review" },
      { state: "QUEUED", at: "2026-06-12T15:00:00Z", actor: "curator", note: "Signed off" },
      { state: "BUILT", at: "2026-06-13T06:00:00Z", actor: "Single-builder build" },
      { state: "LIVE", at: "2026-06-13T06:04:00Z", actor: "Single-builder build" },
    ],
    draft: {
      template: "B",
      filename: "ssf_survey_methods_context.md",
      title: "Context: ssf_survey_methods.md",
      summary:
        "The shared survey methodology used across WorldFish small-scale-fisheries studies — sampling frame, enumerator protocol, and QA steps.",
      keyConcepts: [
        "Small-scale-fisheries survey design; landing-site sampling; enumerator QA",
        "Underpins the Peskas catch surveys and the data-harmonization FAIR methods",
      ],
      relatedFiles: [
        "../peskas/peskas_about.md (applies this survey design)",
        "../data_harmonization/ (shared FAIR data-collection methods)",
      ],
    },
  },

  // ── D: REJECTED — curator sent it back; the CONTRIBUTOR sees the reason and can re-submit ───────
  {
    id: "sub_civ_landings",
    filename: "civ_landings_raw.xlsx",
    format: "tabular",
    sizeLabel: "880 KB",
    initiative: "civ-kb",
    targetPlacement: "civ-kb/civ_landings_raw.xlsx",
    state: "REJECTED",
    provenance: {
      contributor: CURRENT_CONTRIBUTOR,
      author: "Côte d'Ivoire fisheries office",
      captured_at: "2026-06-19T13:20:00Z",
      source_url: "upload://civ_landings_raw.xlsx",
    },
    curatorEdited: false,
    rejectionReason:
      "The table isn't a tidy single table yet — two header rows and merged cells per site. Please reshape to one row per (site × month) and re-submit; the value domains can't be enriched until then.",
    history: [
      { state: "SUBMITTED", at: "2026-06-19T13:20:00Z", actor: "amina.k" },
      { state: "DRAFTED", at: "2026-06-19T13:20:44Z", actor: "Auto-draft agents (mock)" },
      { state: "UNDER_REVIEW", at: "2026-06-19T13:45:00Z", actor: "amina.k" },
      { state: "PENDING", at: "2026-06-19T13:52:00Z", actor: "amina.k", note: "Approved for curator review" },
      { state: "REJECTED", at: "2026-06-20T09:10:00Z", actor: "curator", note: "Not a tidy single table — see reason" },
    ],
    draft: {
      template: "A",
      filename: "civ_landings_raw_dict.md",
      title: "Data dictionary: civ_landings_raw.xlsx",
      summary:
        "Monthly landing totals by site for Côte d'Ivoire, intended for the civ-kb initiative.",
      grain: "Intended grain: one row = one (site × month). Source is not yet tidy (see caveats).",
      columns: [
        { name: "site", meaning: "landing site name", domain: "needs enrichment after reshape" },
        { name: "month", meaning: "calendar month", domain: "needs enrichment after reshape" },
        { name: "landings_t", meaning: "total landings, tonnes", domain: "needs enrichment after reshape" },
      ],
      relatedFiles: ["civ_kb_about.md (the Côte d'Ivoire knowledge-base initiative)"],
      notesCaveats: "Source workbook has two header rows and merged per-site cells; must be reshaped before enrichment.",
    },
  },
];
