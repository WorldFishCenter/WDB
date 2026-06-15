# Graph build provenance

This file records what produced the current `graphify-out/`. It is regenerated on every
maintainer build (see [`CLAUDE.md`](../CLAUDE.md) → "Build model & provenance"). A change here
in a pull request means the graph was rebuilt with a different model or tool version.

| Field | Value |
|---|---|
| Built (UTC date) | 2026-06-15 |
| Model (build + agents) | `claude-opus-4-8` (Opus 4.8) |
| graphify | 0.8.35 |
| Mode | **incremental `--update`** (`/graphify . --update`) |
| Graph | 172 nodes · 324 edges · 9 communities (single connected component) |

> Even with a pinned model, LLM extraction is not bit-for-bit reproducible — the model version
> is the largest controllable factor. Pinning the exact model plus this record is how WDB keeps
> the graph's provenance honest: you control *when* the model changes, and this file says *which*
> model built what is committed.
>
> **This was an incremental `--update` over the 2026-06-12 full rebuild**, not a from-scratch
> rebuild. It re-extracted **only the 11 `_dict.md` files that changed** since the last build — the
> tabular data dictionaries that gained an explicit `## Grain` line in the Phase-0 work (PondCube ×4,
> FASA ×4, Peskas validated-trips ×3). The four new scratch/proof directories added to the working
> tree (`civ-kb/`, `docs/`, `proof/`, `proof_c/` — RAG-integration POC work) were **deliberately
> excluded**: they were added to `.graphifyignore` in the same change, so incremental detection never
> picked them up. Net change vs. the prior committed graph: **173 → 172 nodes**, **320 → 324 edges**.
>
> **Extraction strategy — 3 per-initiative chunks.** One subagent per initiative (PondCube, FASA,
> Peskas-validated-trips), each given (a) both WDB guards verbatim, and (b) the **exact existing
> canonical node ids** for its datasets and the shared/hub entities they reference, so it updated the
> dataset nodes *in place* rather than minting `_dict` duplicates. Total extraction: ~80k input tokens
> across the 3 agents. All 11 emitted node ids matched existing canonical ids — **zero new duplicate
> nodes**, so the canonical-entity guard's merge-time remap was a verified no-op.
>
> **Why grain was re-extracted at all.** The carve-out in [`CLAUDE.md`](../CLAUDE.md) treats a
> `## Grain` line's *domain subject* (e.g. "one row = one catch item of a fishing trip") as a valid
> basis for **same-subject** domain edges, while still banning structural shape edges. The update's
> value is exactly those grain-clarified domain edges: the FASA **benchmark-gate** structure (`PAFF
> Feed_Formulations` and `PAFF Calculated_Composition` → `PAFF Benchmark Gate` via `part_of`; ASNS →
> Calculated_Composition `references`) and the Peskas **production lineage** (`Peskas Automated
> Validation Engine` → each of the Kenya / Mozambique / Zanzibar validated-trips datasets via
> `part_of`). The grain-clarified PondCube tables also drew tight enough on their shared
> `(location, tank_id)` tank-sensor subject to form their own community (PondCube Water-Quality Data).
>
> **Similarity guard held: zero `semantically_similar_to` edges emitted.** The format-blind guard was
> injected verbatim into all 3 subagents. The two structurally identical pairs the corpus baits on —
> PondCube `observations_wide` ↔ `measurements_long`, and the three sister validated-trips long tables
> (Kenya / Mozambique / Zanzibar) — produced **no shape-based links**: the PondCube pair is joined only
> on its shared tank-sensor `(location, tank_id)` subject (`shares_data_with`), and the three
> validated-trips datasets are joined only to their countries, the FAO standards, the shared
> validated-trip-record concept, and Peskas, co-participating through a single hyperedge rather than
> pairwise sister-table edges. All cross-cutting links rest on domain meaning.
>
> **Entity-resolution note — one beneficial dedup (173 → 172).** graphify's build-time dedup pass
> collapsed two pre-existing nodes that denote the same concept: `peskas_fishery_nutrient_profiles`
> ("Fishery Nutrient Profiles (FNPs)") merged into the surviving `shared_fishery_nutrient_profile`
> ("Fishery Nutrient Profile (FNP)"). These were a single real-world entity split across two chunks at
> full-rebuild time (long labels >12 chars, so the dedup length gate allowed the merge). All four edges
> from the merged node were rerouted to the survivor with no dangling references — this is the
> "one node per real-world entity" property the canonical-entity guard protects, applied to a residual
> duplicate. `PeskAAS` remains its own distinct concept node (a real predecessor system, not a label
> variant), unchanged.
>
> A safety backup of the pre-update 173-node graph was kept at `graphify-out/.graphify_old.json`
> during the build and removed at cleanup (not committed).
