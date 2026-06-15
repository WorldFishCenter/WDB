"""Synthesis — retrieved passages → a cited answer (pinned Sonnet 4.6).

Adapted from civ-kb's synthesise step, with civ-kb's CIV specifics dropped
(carry-over #4: no org/year/lang; passages are cited by ``source_file`` +
``location``). The synthesizer answers ONLY from the passages and cites each
claim inline as ``[k]`` — synthesis-from-nothing is prevented upstream by the
refuse-when-thin gate (gate.py, #5), and the synthesizer is instructed to say so
if even the retrieved passages are insufficient.

Two backends share one ``Synthesizer`` interface — the same Live/Replay split
Mode C uses for its resolver:

* :class:`LiveSynthesizer` — the production path: pinned ``claude-sonnet-4-6``
  (model.py) via the Anthropic SDK. Requires ``pip install 'wdb-mode-b[live]'``
  and ``ANTHROPIC_API_KEY``; not exercised by the offline suite.
* :class:`ReplaySynthesizer` — returns recorded answers keyed by question, so the
  contract pipeline is tested deterministically with no network.
"""

from __future__ import annotations

from typing import Protocol

from .model import SYNTH_MODEL
from .retrieve import Passage

SYSTEM_PROMPT = (
    "You are a research assistant for WorldFish's shared knowledge base (WDB). "
    "Answer the question using ONLY the document passages provided. Cite every "
    "claim inline with [1], [2], … matching the passage numbers. If the passages "
    "do not contain enough information to answer, say so plainly — do not use "
    "outside knowledge and do not speculate. Write in the question's language; be "
    "concise and complete."
)


def build_context(passages: list[Passage]) -> str:
    """The numbered passage block the synthesis prompt embeds."""
    blocks = []
    for i, p in enumerate(passages, 1):
        loc = f" | {p.location}" if p.location else ""
        blocks.append(f"[{i}] Source: {p.source_file}{loc}\n{p.text.strip()}")
    return "\n\n---\n\n".join(blocks)


def build_user_prompt(question: str, passages: list[Passage]) -> str:
    return (
        f"Question: {question}\n\n"
        f"Document passages:\n\n{build_context(passages)}\n\n"
        "Synthesise a clear, cited answer based solely on these passages."
    )


class Synthesizer(Protocol):
    def synthesize(self, question: str, passages: list[Passage]) -> str: ...


class LiveSynthesizer:
    """Production synthesizer — pinned Sonnet 4.6 over the retrieved passages."""

    def __init__(self, client=None, model: str = SYNTH_MODEL, max_tokens: int = 1024):
        self.model = model
        self.max_tokens = max_tokens
        if client is None:
            import anthropic  # lazy: the offline path needs no SDK

            client = anthropic.Anthropic()
        self.client = client

    def synthesize(self, question: str, passages: list[Passage]) -> str:
        resp = self.client.messages.create(
            model=self.model,
            max_tokens=self.max_tokens,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": build_user_prompt(question, passages)}],
        )
        return next(b.text for b in resp.content if getattr(b, "type", None) == "text")


class ReplaySynthesizer:
    """Offline synthesizer — recorded answers keyed by normalised question."""

    def __init__(self, recorded: dict[str, str]):
        self.recorded = {self._norm(q): t for q, t in recorded.items()}

    @staticmethod
    def _norm(q: str) -> str:
        return " ".join(q.lower().split())

    def synthesize(self, question: str, passages: list[Passage]) -> str:
        key = self._norm(question)
        if key not in self.recorded:
            raise KeyError(f"no recorded synthesis for {question!r} (offline replay)")
        return self.recorded[key]
