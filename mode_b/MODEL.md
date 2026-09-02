# Mode B — model record

Mode B uses models in three places. Per the three-mode architecture doc §9
(governance) and the repo's pinned-model discipline ([../CLAUDE.md](../CLAUDE.md)),
each is a deliberate, recorded choice so a change is a visible diff — the same
philosophy as [graphify-out/BUILD_INFO.md](../graphify-out/BUILD_INFO.md).

| Role | Model | Where pinned | Networked? |
|---|---|---|---|
| **Passage embedding** | `paraphrase-multilingual-MiniLM-L12-v2` | [`model.py`](model.py) `EMBED_MODEL` | no (local) |
| **Reranking** | `cross-encoder/mmarco-mMiniLMv2-L12-H384-v1` | [`model.py`](model.py) `RERANK_MODEL` | no (local, optional) |
| **Synthesis (LLM)** | `claude-sonnet-4-6` (Sonnet 4.6) — exact id, not the `sonnet` alias | [`model.py`](model.py) `SYNTH_MODEL` | yes (Anthropic SDK + key) |

## The two-model reality is deliberate, not an oversight

WDB runs **two** pinned Claude models on purpose:

- **Opus 4.8** builds the graph and drives **Mode C's resolver** — pinned for
  *reproducibility* of the committed graph and of routing decisions
  ([../CLAUDE.md](../CLAUDE.md); [../mode_c/MODEL.md](../mode_c/MODEL.md)).
- **Sonnet 4.6** is **Mode B's synthesis** model — an **independent** choice
  (three-mode architecture doc §9: *"The Mode-B synthesis model (civ-kb uses
  Sonnet 4.6) is an independent choice — pin and record it like the build
  model."*). Synthesis is a per-query generation step, not a committed artifact;
  it does not need to match the graph's build model, and Sonnet 4.6 is the model
  civ-kb's RAG core was proven with.

Recording it here makes the split a **documented decision**: Mode B synthesis may
be retargeted (e.g. to Opus 4.8) without touching the graph/Mode-C pins, and vice
versa. Pin the **exact** id, never a floating alias, so a model upgrade is a
deliberate, visible event.

## The query-embedding model lock (carry-over #3)

`EMBED_MODEL` is not just the build-time embedder — it is **locked** to the query
side. The Chroma collection is stamped with this id at build
([`index.py`](index.py)), and [`embed.py`](embed.py)`.verify_collection_model`
**raises** if a query would run against an index built with a different model.
Queries always embed with this model via `query_embeddings=` (never Chroma's
`query_texts=`, which silently uses its default model — the proof's footgun,
proof/FINDINGS.md surprise #2). This is a precondition for the refuse-when-thin
gate: a floor judged on mismatch-degraded scores would be meaningless (§7).

## Tested vs live

The regression suite runs the **offline `ReplayRetriever` + `ReplaySynthesizer`**
(recorded retrieval + synthesis), so the gate → join → contract pipeline is
verified deterministically with no model and no network. The **`LiveSynthesizer`**
is the production path (pinned Sonnet 4.6); the anthropic SDK ships in the
consolidated `wdb` env (`uv sync`), so it needs only `ANTHROPIC_API_KEY`. The local embedding /
rerank models are exercised only by the bonus `test_index_live.py`, which skips
when they (or chromadb) are unavailable.

**To upgrade any model:** change its constant in [`model.py`](model.py) and update
this file in the same commit so the switch is recorded.

**Cost-tier (forward-looking):** the **synthesis** slot is a **cheaper-model candidate** — lower-risk
because retrieval + reranker + the refuse-when-thin gate do the honesty work *before* synthesis (it
only writes up already-vetted passages). It may move to a cheaper model **only after** re-running this
slot's faithfulness / refusal proof against the candidate and reading the verdict — the soft risk to
watch is **prose-overclaim beyond the retrieved passages** (the gate does not catch it). Not worth
doing at current volume. See [../docs/model-cost-strategy.md](../docs/model-cost-strategy.md).
