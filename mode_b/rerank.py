"""The reranker seam — three adapters behind one interface.

Mode B's honesty guarantee depends on *which* score the gate judges. A cross-encoder logit is
model-calibrated (``<0`` means "not relevant"), so ``RERANK_FLOOR = 0`` is a principled
threshold. Cosine similarity is not: on a small multilingual corpus even an off-topic passage
scores moderately, and ``mode_b/gate.py`` records the observed case — a Norway salmon-farming
question scoring ~59% against Timor-Leste nutrition passages, which the cosine floor would not
refuse.

Those two floors used to be selected by an accident of the environment. ``LiveRetriever``
constructed its reranker inside ``__init__`` behind a bare ``except Exception`` that printed a
line and returned ``None``; a missing wheel, a failed download or an out-of-memory load silently
swapped the principled floor for the one the gate's own docstring says does not work. Nothing
recorded that it had happened — the only way to find out was
``getattr(retriever, "reranker", None)``, sniffed from two other packages.

So the reranker is an adapter the caller passes in, like the ``Reasoner`` / ``Retriever`` /
``Synthesizer`` / ``Resolver`` seams the package already gets right:

* :class:`CrossEncoderReranker` — production. Loads the model, and **raises** if it cannot.
* :class:`NullReranker` — an explicit, recorded decision to rank on embedding scores alone.
* any test double — :meth:`Reranker.rank` is four lines to fake.

Degrading is now a choice a caller makes (``load_reranker(strict=False)``) rather than an
exception a constructor swallows, and ``kind`` states which floor is in force.
"""

from __future__ import annotations

import warnings
from typing import Protocol

from .model import RERANK_MODEL


class Reranker(Protocol):
    """Re-score retrieved passages against the question.

    ``kind`` names the score the gate will judge — ``"rerank"`` or ``"cosine"`` — so the floor
    follows a declared adapter instead of a ``None`` check on a private attribute.
    """

    kind: str

    def rank(self, question: str, passages: list) -> list:
        """Return ``passages`` re-scored and re-ordered, best first."""
        ...


class CrossEncoderReranker:
    """The production adapter: a cross-encoder logit per (question, passage) pair.

    Raises on construction if the model cannot be loaded. That is the point — a reranker that
    failed to load must not look like one that was never asked for.
    """

    kind = "rerank"

    def __init__(self, model_name: str = RERANK_MODEL, encoder=None):
        if encoder is not None:          # an injected encoder (tests, or a pre-warmed model)
            self._encoder = encoder
            return
        from sentence_transformers import CrossEncoder

        self._encoder = CrossEncoder(model_name)

    def rank(self, question: str, passages: list) -> list:
        if not passages:
            return []
        scores = self._encoder.predict([(question, p.text) for p in passages])
        rescored = [
            type(p)(p.text, p.source_file, p.location, p.initiative, p.cos_score, float(s))
            for p, s in zip(passages, scores)
        ]
        rescored.sort(key=lambda p: p.rerank_score, reverse=True)
        return rescored


class NullReranker:
    """No reranking: keep the embedder's cosine ordering, and say so.

    Legitimate for offline/replay work and for a deployment that consciously accepts the weaker
    floor. It is not a fallback that happens to you — a caller has to pick it.
    """

    kind = "cosine"

    def rank(self, question: str, passages: list) -> list:
        return list(passages)


def load_reranker(*, strict: bool = True, model_name: str = RERANK_MODEL) -> Reranker:
    """Build the production reranker; with ``strict=False`` fall back to :class:`NullReranker`.

    ``strict=True`` (the default) is what production wants: fail loudly rather than quietly
    weaken the refusal floor. ``strict=False`` keeps the old degrade-and-continue behaviour for
    environments without the model — but it warns, and the resulting ``kind`` records the
    decision where the gate and ``/health`` can both see it.
    """
    try:
        return CrossEncoderReranker(model_name)
    except Exception as e:
        if strict:
            raise
        warnings.warn(
            f"cross-encoder reranker unavailable ({e}) — ranking on embedding scores alone. "
            "Mode B's refusal floor falls back to the uncalibrated cosine threshold; see "
            "mode_b/gate.py on why that arm does not reliably refuse off-topic questions.",
            RuntimeWarning,
            stacklevel=2,
        )
        return NullReranker()
