# Mode A — reasoner model record + cold-fabrication-rate report

Mode A uses a model in exactly one place: the **reasoner**, which reads a
deterministically-extracted subgraph and returns a structured answer (prose +
`cited_edges` + `inferred_flags`). It does **not** use a model to find or traverse
edges — extraction is deterministic Python over `graph.json` (`extract.py`), and the
direct-enumeration path uses **no model at all**.

Per the three-mode architecture doc §9 (governance) and the repo's pinned-model
discipline ([../CLAUDE.md](../CLAUDE.md)), that choice is pinned and recorded here so a
reasoning change is a deliberate, visible diff — the same philosophy as
`knowledge_base/graphify-out/BUILD_INFO.md` and
[mode_c/MODEL.md](../mode_c/MODEL.md).

| Field | Value |
|---|---|
| **Reasoner model** | `claude-opus-4-8` (Opus 4.8) — the exact id, not the `opus` alias |
| **Where pinned** | [`mode_a/model.py`](model.py) (`REASONER_MODEL`), consumed by `LiveReasoner` |
| **Max tokens** | `8000` (`REASONER_MAX_TOKENS`) — see cold-rate note below |
| **Output mode** | structured JSON (`output_config.format`, `RESPONSE_SCHEMA`); no sampling params (removed on Opus 4.8) |
| **Safety gate (mandatory)** | the mechanical cite-check C1–C4 — `mode_a/citecheck.py` — runs BEFORE any reasoned answer is surfaced; a failed check downgrades |
| **Proof basis** | `proof_a/FINDINGS.md` (the constrained-middle decision: depth-2 extraction; the cite-check is what makes the LLM safe) |

**Tested vs live.** The regression suite runs the **offline `ReplayReasoner`**, which
replays the structured answers the proof's Opus 4.8 produced
([`fixtures/reasoned.json`](fixtures/reasoned.json)) — so the route → extract → cite-check →
contract pipeline is verified deterministically, with real graph extraction, no network.
The **`LiveReasoner`** is the production path: pinned Opus 4.8 + the honesty-rule prompt +
structured output. It requires the `anthropic` SDK + `ANTHROPIC_API_KEY`.

**To upgrade the reasoner model:** change `REASONER_MODEL` in
[`mode_a/model.py`](model.py), re-run the cold-fabrication-rate measurement
(`python -m mode_a.cold_rate`), and update this file in the same commit.

**Cost-tier (forward-looking):** this slot is **non-negotiable pinned-Anthropic** — autonomous and
honesty-critical (the 0/10 cold-fabrication rate was *measured* on Opus; no human reviews the live
answer), so it is **not** a cheaper-model candidate. The proof path exists but the door stays shut:
the only way it could ever move is to re-run `proof_a/` (negative control + cold-rate) against a
candidate and have it pass. See [../docs/model-cost-strategy.md](../docs/model-cost-strategy.md).

---

## Cold-fabrication-rate measurement (2026-06-16)

The proof validated that the cite-check **catches** fabrication but did not measure how
often a **cold, arms-length** model **attempts** it (its reasoner had seen the whole graph
that session). This is that measurement: `LiveReasoner` (pinned `claude-opus-4-8`,
`max_tokens=8000`), each call shown **only** one serialized subgraph, over the proof's 5
questions + 5 more relational pairs, judged by the same cite-check. Reproduce with
`python -m mode_a.cold_rate` (needs `ANTHROPIC_API_KEY`).

| Cohort | Questions | Fabrications (C1) | Cite-check rejections (any C1–C4) |
|---|---|---|---|
| Proof 5 (Q1–Q5) | 5 | 0 | 0 |
| 5 more relational pairs (Q6–Q10) | 5 | 0 | 0 |
| **Total** | **10** | **0** | **0** |

**Cold-fabrication-attempt rate = 0/10 (0%).** A cold Opus 4.8, shown only the subgraph,
fabricated zero edges, mistagged zero confidences, and — decisively — returned
`connected=false` with **zero citations** on all four genuinely-disconnected pairs
(Q4/Q6/Q8/Q10, C4 pass). Q7 found a 2-edge subgraph but declined to call it "connected"
(the restraint rule 6 asks for).

**What this means for the build (per the proof's framing):** a low rate → **high utility** —
the cite-check rarely has to fire, so the reasoning path surfaces real reasoned answers
rather than constantly downgrading to enumeration. The guard's teeth are proven separately
and independently of this rate by the negative control
([`tests/test_negative_control.py`](tests/test_negative_control.py)): a fabricated edge is
rejected by C1 **regardless** of how rarely the cold model produces one.

**Token-budget finding.** At the proof's original `max_tokens=2000`, **Q1** (Peskas's 40-edge
1-hop neighborhood) truncated mid-JSON — a budget artifact, **not** fabrication (it was clean
at 8000). Q1 is enumeration-shaped and routes to the **cheap deterministic path**, so the
reasoner never serializes a neighborhood that large in production; `REASONER_MAX_TOKENS=8000`
is pinned as headroom regardless.

---

## Prose-overclaim discipline (the soft risk C1 does NOT catch) — owned, not mechanical

C1 proves a cited edge *exists*; it does **not** prove the prose gloss of that edge is
faithful (e.g. calling a generic-hub co-reference "sharing"). This is the proof's residual
risk 1 (`proof_a/FINDINGS.md`). It is handled as **prompt
discipline + spot review**, not a mechanical guarantee, and is owned here explicitly:

- **Prompt:** `SYSTEM_PROMPT` rule 6 (`reasoner.py`) instructs the reasoner to describe an
  edge no more strongly than its relation/rationale warrants; to **not** upgrade a generic
  shared-hub co-occurrence (`WorldFish`, `Fish nutrition`, `Aquaculture`) into "sharing" or
  "partnership"; and to name substantive connections (shared dataset, one tool documented by
  another, same site/species) while explicitly declining to call generic ones substantive.
- **Spot review (this run):** Q3 / Q9 (cross-initiative "which initiatives share…") were the
  cases at risk. The cold reasoner named **ssf_research** (real `shares_data_with`) and the
  WIO harmonization method/tool documentation as substantive, and did **not** dress up the
  generic `WorldFish` / `Fish nutrition` co-references as sharing — the Q3 restraint the proof
  demonstrated, reproduced cold. Re-check this qualitatively whenever the model pin changes;
  it is the one honesty property the mechanical gate does not cover.
