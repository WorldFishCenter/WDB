# Graph build provenance

This file records what produced the current `graphify-out/`. It is regenerated on every
maintainer build (see [`CLAUDE.md`](../CLAUDE.md) → "Build model & provenance"). A change here
in a pull request means the graph was rebuilt with a different model or tool version.

| Field | Value |
|---|---|
| Built (UTC date) | 2026-06-12 |
| Model (build + agents) | `claude-opus-4-8` (Opus 4.8) |
| graphify | 0.8.35 |
| Mode | incremental (`/graphify . --update`) |
| Graph | 209 nodes · 342 edges · 7 communities |

> Even with a pinned model, LLM extraction is not bit-for-bit reproducible — the model version
> is the largest controllable factor. Pinning the exact model plus this record is how WDB keeps
> the graph's provenance honest: you control *when* the model changes, and this file says *which*
> model built what is committed.
>
> This incremental build re-extracted **1 changed document**: `peskas/peskas_timeline_about.md`,
> after it was edited under the new **satellite convention** ([PROTOCOL §6](../PROTOCOL.md)) — the
> bare "Peskas" canonical name was used in place of "Peskas platform", and the two cross-initiative
> `## Related files` links (the Kenya digital-feedback study, the Timor-Leste RCT) were removed from
> the satellite and left to the `peskas_about.md` hub, so the timeline links mainly to its hub and
> same-initiative siblings. No code/papers/images changed; AST was skipped and the rest served from
> cache.
>
> **Entity-resolution note (deliberate maintainer step).** Re-extracting the satellite with the
> short canonical label "Peskas" first produced *new* duplicate nodes (`peskas`, "Peskas Overview",
> `PeskAAS`), because graphify's dedup (`dedup.py`) refuses to merge labels under 12 characters — two
> "Peskas" nodes from different files never auto-collapse. The build therefore **remapped the
> satellite's references onto the existing canonical node ids** (`peskas_peskas_about_peskas`,
> `peskas_peskas_about_peskas_hub`, `peskaas_automated_analytics_system`) before merge, so the
> timeline points at the *existing* Peskas / hub / PeskAAS nodes and adds **zero** new duplicates.
> Canonical *names* are necessary but, for short proper names, not sufficient — canonical *ids*
> (a satellite referencing the hub's node, not re-minting the concept) are what actually consolidate.
>
> Net effect vs. the prior graph: **3 new nodes / 18 new edges against 3 nodes / 13 edges removed**
> (the prior timeline subgraph was replaced; node count held at 209). Edges moved 337 → 342 and
> clustering tightened from 8 → **7 communities** as the consolidated, hub-anchored timeline pulled
> the Peskas content together. The timeline node sits inside the "Peskas Platform & Global Scaling"
> community (degree 15) and is **not** a high-betweenness cross-community bridge — the intended
> cohesion outcome. The pre-existing legacy variants (`Peskas platform`, the `Peskas Monitoring
> System` concept nodes from frozen `_dict.md` notes) remain — accepted residual under the
> canonical-naming-only decision (no LLM dedup pass).
>
> The format-blind similarity guard was injected verbatim into the extraction subagent. **Zero
> `semantically_similar_to` edges were emitted**; every satellite edge rests on domain meaning
> (`part_of` the hub, `references`/`cites` siblings, `produced_by`), never on table shape or format.
