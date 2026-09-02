"""Pinned, recorded models & pipeline parameters — Mode B's BUILD_INFO analogue.

Mode B uses models in three places, and they are a deliberate, recorded choice
(three-mode architecture doc §9 governance; the repo's pinned-model discipline,
../CLAUDE.md):

* ``EMBED_MODEL``  — the multilingual sentence-embedder the passage index is built
  with. The **same** model must embed queries (carry-over #3, the query-model
  lock); ``mode_b/embed.py`` is the single owner and ``mode_b/index.py`` stamps
  this id into the Chroma collection so a mismatch is a *checked* error, not a
  silent degradation.
* ``RERANK_MODEL`` — the cross-encoder that re-orders retrieved candidates. Local
  retrieval falls back to embedding-only ranking when it is unavailable.
* ``SYNTH_MODEL``  — the LLM that synthesises the cited answer from passages. This
  is an **independent** choice from the graph build (see MODEL.md): the graph and
  Mode C are pinned to Opus 4.8 for reproducibility; Mode B synthesis is pinned to
  Sonnet 4.6 (civ-kb's proven synthesis model). A change to any pin is a visible
  diff — the same philosophy as graphify-out/BUILD_INFO.md.

To upgrade a model: change its constant here and update ``mode_b/MODEL.md`` in the
same commit so the switch is recorded.
"""

from __future__ import annotations

# --- the synthesis LLM (the only networked model; pinned + recorded) -------- #
# Pin the EXACT id, not a floating alias. Independent of the Opus-4.8 graph/Mode-C
# pin on purpose (MODEL.md records why a two-model split is deliberate).
SYNTH_MODEL = "claude-sonnet-4-6"

# --- the local retrieval models (no API, no key) ---------------------------- #
# The index's embedder. Queries MUST use this same model (carry-over #3).
EMBED_MODEL = "paraphrase-multilingual-MiniLM-L12-v2"
# The cross-encoder reranker. Optional at runtime: when it cannot load, retrieval
# degrades gracefully to embedding-only ranking.
RERANK_MODEL = "cross-encoder/mmarco-mMiniLMv2-L12-H384-v1"

# --- chunking parameters (carried over from civ-kb's proven core) ----------- #
CHUNK_WORDS = 400
CHUNK_OVERLAP = 60

# --- retrieval breadth ------------------------------------------------------ #
RETRIEVAL_K = 40      # candidates pulled from the index before reranking
RERANK_TOP_K = 6      # passages kept after reranking (fed to synthesis)
