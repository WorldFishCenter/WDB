"""The reasoner — an LLM over the serialized subgraph, under the honesty contract.

Promoted from the proven ``proof_a/candidate.py``. The reasoner is ONE model call:
serialized subgraph + question + the honesty rules -> a structured answer. It carries
the Mode-A honesty rules (docs/three-mode-architecture.md §2, §6, §7): reason ONLY over
the listed edges; every asserted connection cited to a real edge with its
EXTRACTED/INFERRED tag; never assert an unlisted connection; if two entities are not
connected in the subgraph, SAY so — do not invent a path.

The verdict on those rules is NOT taken from the model's word — it is mechanical
(:mod:`citecheck`): every ``cited_edges`` entry is exact-matched against the subgraph's
real edge set BEFORE the answer is surfaced. This module fixes the prompt + the response
shape so that check has typed fields to verify, and a failed check downgrades the answer
(``pipeline.py``).

Two backends share one :class:`Reasoner` interface, mirroring Mode B/C's Live/Replay split:

* :class:`LiveReasoner` — the production path: pinned ``claude-opus-4-8`` (``model.py``)
  via the anthropic SDK + structured JSON output. Needs the SDK + an API key.
* :class:`ReplayReasoner` — offline: returns the recorded structured answers the proof's
  Opus 4.8 produced, keyed by the question parsed from the serialized subgraph. The
  deterministic default the regression suite runs, so the route -> extract -> cite-check ->
  contract pipeline is tested without the network.

Rule 6 below is the **prose-overclaim discipline** the proof flagged as the soft risk the
mechanical cite-check does NOT catch (``proof_a/FINDINGS.md`` residual risk 1): C1 proves a
cited edge *exists*, not that the prose gloss is faithful. It is prompt discipline + a
spot-review note in ``MODEL.md`` — not a mechanical guarantee — and is owned here explicitly.
"""

from __future__ import annotations

import json
from typing import Protocol

from .model import REASONER_MAX_TOKENS, REASONER_MODEL

SYSTEM_PROMPT = """\
You are the Mode-A reasoner for WorldFish's shared knowledge graph (WDB). You are given a \
SUBGRAPH (a node list + a typed edge list) that was deterministically extracted around the \
question's entities, plus the QUESTION. Answer the question by reasoning over that subgraph.

BINDING HONESTY RULES (a real Mode-A answer must obey all of these):
1. Reason ONLY over the nodes and edges listed in the SUBGRAPH. Do NOT use any outside \
knowledge about these entities, and do NOT assume an edge that is not listed.
2. Every relationship you assert in your answer MUST correspond to a specific edge in the \
SUBGRAPH. Put each one in `cited_edges` exactly as listed (source, relation, target, \
confidence). If you cannot back a statement with a listed edge, do not make the statement.
3. NEVER assert a connection that is not an edge in the SUBGRAPH. Do not invent a path, a \
rationale, or an intermediate link that the edge list does not contain.
4. An edge tagged INFERRED is the graph-builder's plausible GUESS, not a stated fact. When a \
relationship you assert rests on an INFERRED edge, you MUST flag it as inferred/uncertain in \
your prose AND list that edge in `inferred_flags`. Prefer EXTRACTED edges; discount INFERRED ones.
5. If the SUBGRAPH contains no edge (and no path) connecting two entities the question asks \
about, say plainly that the graph records NO connection between them. Set `connected` to false \
and leave `cited_edges` empty. Do NOT manufacture a relationship from a shared parent \
organization, a shared generic concept, or your own knowledge.
6. Describe each edge NO MORE STRONGLY than its relation and rationale warrant. Two initiatives \
that meet only through a GENERIC shared hub (e.g. both reference "WorldFish", "Fish nutrition", \
"Aquaculture") are NOT "sharing data" or "partnering" — say explicitly that they connect only \
through a generic shared concept and decline to call it a substantive relationship. Reserve words \
like "shares", "partnership", or "feeds into" for edges whose relation/rationale actually states \
that (a shared dataset, one tool documented by another, the same site/species/measurement \
subject). Name the substantive connections; do not upgrade a generic co-occurrence into one.

Return ONE JSON object with keys:
  answer        : your prose answer (explain the relationship, grounded only in the edges)
  connected     : true if the subgraph connects the question's entities, false if not
  cited_edges   : [{source, relation, target, confidence}] — one per asserted connection, \
copied verbatim from the SUBGRAPH edge list
  inferred_flags: the subset of cited_edges (same dicts) whose confidence is INFERRED
"""


def build_user_prompt(serialized_subgraph: str) -> str:
    return (
        "SUBGRAPH (the ONLY connections you may use):\n\n"
        f"{serialized_subgraph}\n\n"
        "Answer the QUESTION above under the binding honesty rules. Return only the JSON object."
    )


RESPONSE_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "answer": {"type": "string"},
        "connected": {"type": "boolean"},
        "cited_edges": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "source": {"type": "string"},
                    "relation": {"type": "string"},
                    "target": {"type": "string"},
                    "confidence": {"type": "string"},
                },
                "required": ["source", "relation", "target", "confidence"],
            },
        },
        "inferred_flags": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "source": {"type": "string"},
                    "relation": {"type": "string"},
                    "target": {"type": "string"},
                    "confidence": {"type": "string"},
                },
                "required": ["source", "relation", "target", "confidence"],
            },
        },
    },
    "required": ["answer", "connected", "cited_edges", "inferred_flags"],
}


class NoRecordedAnswer(KeyError):
    """ReplayReasoner has no recorded answer for this (offline) question."""


class Reasoner(Protocol):
    def reason(self, serialized_subgraph: str) -> dict: ...


def _question_of(serialized_subgraph: str) -> str:
    """Recover the question from a serialized subgraph (the 'QUESTION: …' first line)."""
    first = serialized_subgraph.splitlines()[0] if serialized_subgraph else ""
    return first[len("QUESTION:"):].strip() if first.startswith("QUESTION:") else ""


class LiveReasoner:
    """Production reasoner — pinned Opus 4.8 via the anthropic SDK + structured output.

    Requires ``pip install anthropic`` and ``ANTHROPIC_API_KEY``. Pinned to the exact
    model id (``mode_a/model.py``) for reproducibility, the same discipline as the graph
    build. Not exercised by the offline regression suite (see ``cold_rate.py`` for the
    cold, arms-length live run).
    """

    def __init__(self, client=None, model: str = REASONER_MODEL, max_tokens: int = REASONER_MAX_TOKENS):
        self.model = model
        self.max_tokens = max_tokens
        if client is None:
            import anthropic  # imported lazily so the offline path needs no SDK

            client = anthropic.Anthropic()
        self.client = client

    def reason(self, serialized_subgraph: str) -> dict:
        resp = self.client.messages.create(
            model=self.model,
            max_tokens=self.max_tokens,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": build_user_prompt(serialized_subgraph)}],
            # structured output forces a valid JSON object; no temperature on Opus 4.8
            output_config={"format": {"type": "json_schema", "schema": RESPONSE_SCHEMA}},
        )
        return json.loads(next(b.text for b in resp.content if b.type == "text"))


class ReplayReasoner:
    """Offline reasoner — returns recorded structured answers keyed by question.

    The recorded answers are exactly what the proof's Opus 4.8 produced for the proof's
    questions (``fixtures/reasoned.json``); replaying them lets the route/extract/cite-check/
    contract pipeline be tested deterministically, with no network. Mirrors Mode C's
    ``ReplayResolver``.
    """

    def __init__(self, recorded: dict[str, dict]):
        self.recorded = {self._norm(k): v for k, v in recorded.items()}

    @staticmethod
    def _norm(q: str) -> str:
        return " ".join(q.lower().split())

    def reason(self, serialized_subgraph: str) -> dict:
        key = self._norm(_question_of(serialized_subgraph))
        if key not in self.recorded:
            raise NoRecordedAnswer(f"no recorded reasoning for {key!r} (offline replay)")
        return self.recorded[key]
