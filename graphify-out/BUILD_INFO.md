# Graph build provenance

This file records what produced the current `graphify-out/`. It is regenerated on every
maintainer build (see [`CLAUDE.md`](../CLAUDE.md) → "Build model & provenance"). A change here
in a pull request means the graph was rebuilt with a different model or tool version.

| Field | Value |
|---|---|
| Built (UTC date) | 2026-06-08 |
| Model (build + agents) | `claude-opus-4-8` (Opus 4.8) |
| graphify | 0.8.35 |
| Mode | incremental (`/graphify . --update`) |
| Graph | 138 nodes · 214 edges · 8 communities |

> Even with a pinned model, LLM extraction is not bit-for-bit reproducible — the model version
> is the largest controllable factor. Pinning the exact model plus this record is how WDB keeps
> the graph's provenance honest: you control *when* the model changes, and this file says *which*
> model built what is committed.
>
> This incremental build re-extracted a single changed document: the WIO SSF Data-Harmonization
> Technical Guidelines (April 2026 draft). Its source `.docx`
> (`data_harmonization/Technical_Guidelines_SSF_Data_Harmonization_WIO.docx`) had **failed office
> conversion** on the prior build and was skipped; it has since converted cleanly to the sidecar
> `graphify-out/converted/Technical_Guidelines_SSF_Data_Harmonization_WIO_8f7e1b7e.md` (~3,850
> words), so the incremental detector flagged that sidecar as new and extracted it. The document's
> companion context note (`data_harmonization/Technical_Guidelines_SSF_Data_Harmonization_WIO_context.md`)
> was already in the graph; this build adds the actual guideline content — the Integrated Data
> Harmonization Framework, the minimum common-denominator variable set and its four thematic
> domains, the FAO/international standards stack (GAUL, ISSCFG, ASFIS, ISO 8601, Aquatic Food
> Ontology), and regional governance bodies (SWIOFC, WGDS, Nairobi Convention).
>
> Net effect: 51 new nodes and 76 new edges against 5 nodes and 12 edges removed, with 5 nodes
> deduplicated on merge. Because the extractor used stable `concept_*` ids for broadly-shared
> domain entities, the new content **merged into** the existing WIO / FAO GAUL / catch-effort
> concept nodes that the Kenya, Mozambique, and Zanzibar validated-trips notes already referenced —
> consolidating the corpus rather than duplicating it. The graph moved 92 → 138 nodes and
> 150 → 214 edges, and clustering resolved into 8 communities (down from 10 as the new guidelines
> content bridged previously separate WIO/FAO clusters), including a dedicated "SSF Harmonization
> Governance" community, a "FAO Standards & Variables" community, and an "SSF Data Collection
> Protocols" (QA/QC, raising procedures, standardized sampling) community.
>
> The format-blind similarity guard was injected verbatim into the extraction subagent. Exactly one
> `semantically_similar_to` edge was emitted — Aquatic Food Ontology ↔ FAO ISSCFG (0.7) — on a
> genuine domain basis (both are gear-concept classification/semantic systems for the same subject),
> never on tidy-table or wide/long shape. No edge was minted on dataset shape, format, file type, or
> storage pattern.
