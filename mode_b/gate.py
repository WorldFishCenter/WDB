"""The refuse-when-thin gate — Mode B's honesty mechanism (carry-over #5, §7).

Synthesis-from-nothing is the failure to prevent. When retrieval is weak the
pipeline must return "not available" rather than synthesise from passages that do
not actually cover the question. The gate refuses when:

1. **nothing was retrieved**, or
2. the **top passage scores below the floor** for its score kind, or
3. **no retrieved passage covers an initiative the question names** (a question
   about an initiative absent from the corpus has no honest passage answer).

The gate runs AFTER the query-model lock (embed.py, #3): a floor judged on scores
that a silent embedder mismatch had depressed would fire on noise (§7). Lock
first, then trust the gate.

────────────────────────────────────────────────────────────────────────────────
The floors below are **provisional, uncalibrated placeholders** — deliberately so.
The passage proof (proof/FINDINGS.md, caveat 3) flagged that with ~34 files a
similarity floor is *not* calibrated, so any number tuned to local runs would be
misleading. They are illustrative defaults, NOT tuned thresholds: calibrate them
against a held-out question set once the corpus grows. The gate's *logic* (refuse
below floor / when uncovered / when empty) is what the deterministic tests pin —
not these specific numbers.

**Which floor is principled vs. a stopgap.** The architecture's honesty mechanism
is a floor on the **reranked** passages (§3, §7): a cross-encoder relevance logit
is model-calibrated — ``<0`` means "not relevant" — so ``RERANK_FLOOR = 0`` is a
*principled* threshold, not a corpus-tuned one. ``COSINE_FLOOR_PCT`` is only the
**fallback when no reranker is loaded**, and a multilingual bi-encoder gives even
off-topic passages a moderate cosine on a small corpus — so the cosine arm does
**not** reliably refuse a topically-uncovered question (observed live: a Norway
salmon-farming question scored ~59% against Timor-Leste nutrition passages). That
is a documented limitation of the rerankerless fallback, NOT something to fix by
raising the placeholder to fit local scores. Run the reranker in production; until
then the refusal guarantee rests on the empty/thin arm (proven deterministically)
and the coverage arm, not on the cosine number.
────────────────────────────────────────────────────────────────────────────────
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from .retrieve import Passage

# PROVISIONAL placeholders — see the module docstring. Do not treat as calibrated.
RERANK_FLOOR = 0.0      # cross-encoder logit: >0 is "relevant-ish". Placeholder.
COSINE_FLOOR_PCT = 25.0  # cosine similarity %, used only when no reranker. Placeholder.


@dataclass(frozen=True)
class GateResult:
    ok: bool
    reason: str = ""


def _floor_for(kind: str) -> float:
    return RERANK_FLOOR if kind == "rerank" else COSINE_FLOOR_PCT


def covers_question(question: str, passages: list[Passage], known_initiatives) -> bool:
    """False iff the question names a KNOWN initiative that no retrieved passage is from.

    ``known_initiatives`` is the set of initiatives the corpus actually has. If the
    question names one of them, at least one retrieved passage must come from it
    (retrieval did not drift off-topic). A question naming an initiative the corpus
    does not have at all is left to the score floor (not this check). When the
    question names no known initiative, coverage passes (returns True).
    """
    q = question.lower()
    named = {i for i in known_initiatives if i and (i.replace("_", " ") in q or i in q)}
    if not named:
        return True
    got = {p.initiative for p in passages if p.initiative}
    return bool(named & got)


def refuse_when_thin(question: str, passages: list[Passage],
                     known_initiatives=None,
                     rerank_floor: float = RERANK_FLOOR,
                     cosine_floor: float = COSINE_FLOOR_PCT) -> GateResult:
    """Refuse (ok=False) when retrieval is too thin to answer honestly.

    ``known_initiatives`` (optional) enables the coverage arm: pass the corpus's
    initiative set so a question naming one of them must retrieve a passage from
    it. Omit it to gate on the score floor alone.
    """
    if not passages:
        return GateResult(False, "no passage retrieved for this question")

    top = passages[0]
    kind = top.ranking_kind()
    floor = rerank_floor if kind == "rerank" else cosine_floor
    if top.ranking_score() < floor:
        return GateResult(
            False,
            f"top passage {kind} score {top.ranking_score():.2f} is below the "
            f"provisional floor {floor:.2f} — retrieval too thin to answer",
        )

    if known_initiatives is not None and not covers_question(question, passages, known_initiatives):
        return GateResult(False, "no retrieved passage covers the initiative the question names")

    return GateResult(True)
