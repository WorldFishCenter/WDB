# Graph build provenance

This file records what produced the current `graphify-out/`. It is regenerated on every
maintainer build (see [`CLAUDE.md`](../CLAUDE.md) → "Build model & provenance"). A change here
in a pull request means the graph was rebuilt with a different model or tool version.

| Field | Value |
|---|---|
| Built (UTC date) | 2026-06-05 |
| Model (build + agents) | `claude-opus-4-8` (Opus 4.8) |
| graphify | 0.8.26 |
| Mode | standard, full rebuild from cleared cache (`/graphify .`) |
| Graph | 63 nodes · 83 edges · 7 communities |

> Even with a pinned model, LLM extraction is not bit-for-bit reproducible — the model version
> is the largest controllable factor. Pinning the exact model plus this record is how WDB keeps
> the graph's provenance honest: you control *when* the model changes, and this file says *which*
> model built what is committed.
>
> This build was the first to apply the format-blind similarity guard at extraction time (no
> `semantically_similar_to` edge is based on data shape); node count differs slightly from the
> prior build (64 → 63) because LLM extraction varies run to run.
