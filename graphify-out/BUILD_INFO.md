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
| Graph | 171 nodes · 264 edges · 7 communities |

> Even with a pinned model, LLM extraction is not bit-for-bit reproducible — the model version
> is the largest controllable factor. Pinning the exact model plus this record is how WDB keeps
> the graph's provenance honest: you control *when* the model changes, and this file says *which*
> model built what is committed.
>
> This incremental build re-extracted **5 changed documents**, all Markdown context/about notes:
> two new whole-initiative `_about.md` files —
> `digital_transformation_accelerator/digital_transformation_accelerator_about.md` and
> `fasa/fasa_about.md` — plus three modified notes:
> `digital_transformation_accelerator/pondcube/pondcube_about.md`,
> `digital_transformation_accelerator/pondcube/pondcube_data_about.md`, and
> `fasa/fasa_repo_about.md`. No code, papers, or images changed, so AST extraction was skipped and
> only the semantic subagent ran; the unchanged PDFs and `_dict.md` files were served from cache.
>
> This build adds the two missing initiative hubs and wires their packages, datasets, concepts, and
> cited literature into the graph: the **Digital Transformation Accelerator (DTA)** hub (Data
> Ecosystem area of work, FAIR-by-design / AI-ready data, Carob, GARDIAN, AgriLLM, CGIAR AI Hub,
> Asia Digital Hub) with **PondCube** and its sense-send-serve-monitor-alert pipeline and
> water-quality dataset hanging off it; and the **FASA Initiative** hub (feed-formulation app,
> circular-economy waste-to-feed framing, Nile Tilapia / African Catfish) over the FASA engine
> (PuLP + HiGHS LP, premix-aware masking, toxin ceilings, IIS reporting, PAFF benchmark gate,
> `fasa_api` / `fasa_core`, the ASNS→FICD crosswalk) and its ASNS / FICD / PAFF reference databases
> and aquaculture-feed literature (Bureau 2014, Hua & Bureau 2012, Avadí et al. 2022).
>
> Net effect: **33 new nodes and 51 new edges against 1 edge removed, with 7 nodes deduplicated on
> merge (2 exact, 5 fuzzy)**. The dedup consolidated the new about-file nodes onto the dataset and
> database nodes the existing `_dict.md` extractions already carried (the PondCube CSVs, the
> ASNS/FICD/PAFF databases) rather than duplicating them. The graph moved 138 → 171 nodes and
> 214 → 264 edges; clustering resolved into 7 communities (down from 8, as the DTA and PondCube
> content fused into one "Digital Transformation Accelerator & PondCube" community).
>
> The format-blind similarity guard was injected verbatim into the extraction subagent. **Zero
> `semantically_similar_to` edges were emitted this build.** In particular the subagent deliberately
> minted **no** link between the PondCube datasets and the FASA ASNS/FICD/PAFF databases: they share
> only structural shape (tidy CSV/table form) and no domain meaning — different initiatives, species,
> and studies — so per the guard no cross-initiative edge was created. Within-initiative
> `shares_data_with` edges were used only where there is a genuine domain join (the four PondCube CSVs
> derive from one source workbook; the FASA engine reads its three reference databases; the
> ASNS↔FICD crosswalk).
