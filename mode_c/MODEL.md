# Mode C — resolver model record

Mode C uses a model in exactly one place: the **resolver**, which maps a
natural-language question to a `{table, columns, grain, aggregation,
derived_formula, filters}` resolution (or a refusal). It does **not** use a model
to compute — every number comes from DuckDB over the committed CSVs.

Per the three-mode architecture doc §9 (governance) and the repo's pinned-model
discipline ([../CLAUDE.md](../CLAUDE.md)), that choice is pinned and recorded here
so a routing change is a deliberate, visible diff — the same philosophy as
[graphify-out/BUILD_INFO.md](../graphify-out/BUILD_INFO.md).

| Field | Value |
|---|---|
| **Resolver model** | `claude-opus-4-8` (Opus 4.8) — the exact id, not the `opus` alias |
| **Where pinned** | [`mode_c/model.py`](model.py) (`RESOLVER_MODEL`), consumed by `LiveResolver` |
| **Output mode** | structured JSON (`output_config.format`); no sampling params (removed on Opus 4.8) |
| **Guards (mandatory)** | grain reasoning + derived-metric handling — `mode_c/resolver.py` (`GRAIN_GUARD`, `DERIVED_GUARD`) |
| **Proof basis** | `proof_c/RESOLVER_FINDINGS.md` (resolver verdict: trustworthy only with both guards) |

**Tested vs live.** The regression suite runs the **offline `ReplayResolver`**,
which replays the resolutions the proof's Opus 4.8 produced for the 9 questions —
so the gate + executor + answer-contract pipeline is verified deterministically,
with real DuckDB computation, no network. The **`LiveResolver`** is the
production path: pinned Opus 4.8 + the two-guard prompt + structured output. The
anthropic SDK ships in the consolidated `wdb` env (`uv sync`), so it needs only `ANTHROPIC_API_KEY`.

**To upgrade the resolver model:** change `RESOLVER_MODEL` in
[`mode_c/model.py`](model.py) and update this file in the same commit.
