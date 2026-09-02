"""Serialize a :class:`~wdb_router.contract.RouterAnswer` (§6 contract) to JSON-native dicts.

The read UI's whole job is to render the router's **honesty** — what each mode grounded, in
what artifact, and what no mode could ground — so this serializer **drops nothing the contract
carries** and **adds no interpretation of its own**. It is a faithful pass-through, not a view.

It is mode-aware only where the contract itself is: every ``Claim`` names its ``mode``, and a
claim's citation IS a *different artifact* per mode — Mode A's is a graph edge triple, Mode B's
is a passage span + verbatim quote + the matching graph node(s), Mode C's is the SQL + its
result rows (``wdb_router.contract`` docstring; the three ``mode_*/contract.py`` ``Citation``
shapes). We key the citation shape off ``claim.mode`` for the UI, and capture **every** field
via :func:`dataclasses.asdict`, so a future contract change can never silently drop a field
here — the round-trip test pins exactly that.

The figures (Mode C), the merged graph ``associations`` (already plain ``graph.json`` edge
dicts), and the ``unanswered`` list pass through unflattened. ``answered`` / ``modes_fired`` /
``modes_grounded`` are the contract's own computed views (not synthesis) — included so the UI
can show the routing/grounding posture without re-deriving it.
"""

from __future__ import annotations

from dataclasses import asdict


def serialize_citation(citation) -> dict:
    """One citation → dict, with **every** field of whichever mode's ``Citation`` this is.

    ``asdict`` captures the full native shape (A: ``locator``/``confidence``; B:
    ``quote``/``location``/``nodes``; C: ``sql``/``result``) — so no mode's citation richness
    is collapsed. The owning claim's ``mode`` tells the UI which shape to expect.
    """
    return asdict(citation)


def serialize_claim(claim) -> dict:
    """One native A/B/C ``Claim`` → dict: its mode tag, prose, and ≥1 native citation.

    The §6 invariant "no claim without a citation" is enforced inside each mode (the contract
    cannot represent a citation-less claim), so faithful serialization preserves it for free.
    """
    return {
        "mode": claim.mode,
        "text": claim.text,
        "citations": [serialize_citation(c) for c in claim.citations],
    }


def serialize_figure(figure) -> dict:
    """One Mode-C ``Figure`` → ``{spec, query, result}`` — the chart ships with its own SQL."""
    return asdict(figure)


def serialize_route(route) -> dict:
    """One ``Route`` → ``{mode, reason}`` — the signal that selected the mode (transparency)."""
    return {"mode": route.mode, "reason": route.reason}


def serialize_answer(answer) -> dict:
    """A whole :class:`RouterAnswer` → a JSON-native dict, nothing flattened or dropped.

    Every part the contract carries is here: the per-mode ``claims`` with their native
    citations, the merged graph ``associations``, Mode-C ``figures``, and the ``unanswered``
    list (stated, never hidden — §6 r4). The values are all JSON-native already (Mode C
    coerces DuckDB Decimals to float at the executor; ``graph.json`` edges are str/num dicts),
    so the result serializes with ``json.dumps`` as-is.
    """
    return {
        "question": answer.question,
        "answered": answer.answered,
        "modes_fired": answer.modes_fired,          # modes routed-to
        "modes_grounded": answer.modes_grounded,    # modes that actually contributed
        "routes": [serialize_route(r) for r in answer.routes],
        "claims": [serialize_claim(c) for c in answer.claims],
        "associations": [dict(e) for e in answer.associations],
        "figures": [serialize_figure(f) for f in answer.figures],
        "unanswered": list(answer.unanswered),
    }
