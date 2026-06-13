# Graph build provenance

This file records what produced the current `graphify-out/`. It is regenerated on every
maintainer build (see [`CLAUDE.md`](../CLAUDE.md) → "Build model & provenance"). A change here
in a pull request means the graph was rebuilt with a different model or tool version.

| Field | Value |
|---|---|
| Built (UTC date) | 2026-06-12 |
| Model (build + agents) | `claude-opus-4-8` (Opus 4.8) |
| graphify | 0.8.35 |
| Mode | **full rebuild from scratch** (`/graphify .`) |
| Graph | 173 nodes · 320 edges · 7 communities (single connected component) |

> Even with a pinned model, LLM extraction is not bit-for-bit reproducible — the model version
> is the largest controllable factor. Pinning the exact model plus this record is how WDB keeps
> the graph's provenance honest: you control *when* the model changes, and this file says *which*
> model built what is committed.
>
> **This was a from-scratch full rebuild, not an `--update`.** It deliberately replaced the prior
> incremental graph (209 nodes / 342 edges, accumulated over many `--update` sessions). The prior
> graph carried **51 nodes extracted from converted-PDF sidecars** (`graphify-out/converted/`) that
> duplicated their source papers, plus concept nodes whose ids had drifted across many incremental
> passes. The rebuild re-extracts the **34 current corpus files** (27 docs + 7 PDFs) once, cleanly,
> from a freshly cleared semantic cache. Net change vs. the prior committed graph: **209 → 173
> nodes**, **342 → 320 edges** — fewer nodes, but no sidecar duplicates and a single internally
> consistent id scheme.
>
> **Extraction strategy — 7 per-initiative chunks.** One subagent per initiative
> (data_harmonization, DTA, PondCube, FASA, Peskas-platform, Peskas-data/nutrient-profiles,
> ssf_research), each instructed to **read its PDFs directly** (not just the `_context.md`
> companions) for paper-level concepts — the main source of the concept richness. Total extraction:
> ~380k input tokens across the 7 agents.
>
> **Cross-initiative connectivity by canonical shared nodes (not cross-chunk edges).** Because each
> subagent only sees its own chunk, no edge can span two chunks. Connectivity was instead achieved by
> giving **every** chunk one fixed shared-entity vocabulary — stable ids for the real-world entities
> that span initiatives (`shared_worldfish`, `shared_kenya`, `shared_timor_leste`, `shared_zanzibar`,
> `shared_mozambique`, `shared_small_scale_fisheries`, `shared_fao_asfis/gaul/isscfg`,
> `shared_aabs`, …) plus five fixed initiative-hub ids (`peskas_hub`, `fasa_hub`, `pondcube_hub`,
> `dta_hub`, `data_harmonization_hub`), each emitted only by its owning chunk and referenced by id
> elsewhere. 204 raw nodes collapsed to **173 unique** as the shared/hub ids deduped across chunks —
> and the graph came out as a **single connected component** with `Peskas` (betweenness 0.373) and
> `WorldFish` (bridges all five of its communities) as the cross-initiative bridges. This is the
> canonical-entity guard ([`CLAUDE.md`](../CLAUDE.md)) applied at build time: one node per real-world
> entity is exactly what links the initiatives.
>
> **Similarity guard held: zero `semantically_similar_to` edges emitted.** The format-blind guard was
> injected verbatim into all 7 subagents. The two structurally identical pairs the corpus is known to
> bait on — PondCube `observations_wide` ↔ `measurements_long`, and the three sister validated-trips
> long tables (Kenya / Mozambique / Zanzibar) — produced **no shape-based links**: the PondCube pair
> is joined only on its shared tank-sensor `(location, tank_id)` subject (`shares_data_with`), and the
> three validated-trips datasets are joined only to their countries, the FAO standards, and Peskas,
> co-participating through a single hyperedge rather than pairwise sister-table edges. All
> cross-cutting links rest on domain meaning.
>
> **Entity-resolution note.** `PeskAAS` (the historical predecessor system named in the Peskas
> timeline) was modeled as its **own distinct concept node**, not merged into `peskas_hub` — a real
> prior system, not a label variant. The Peskas timeline anchors to the hub via `part_of` and does
> not re-mint the platform concept.
>
> A safety backup of the replaced 209-node graph was kept at `/tmp/wdb_graph_209_backup.json` during
> the build (outside the repo, not committed).
