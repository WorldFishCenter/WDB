"""Rendering the contract for a terminal — the one per-mode citation switch.

A citation IS a different artifact per mode, so *something* has to switch on ``claim.mode``.
Before this module four places did: ``mode_a/cli.py``, ``mode_b/cli.py``, ``mode_c/cli.py`` and
``wdb_router/cli.py`` each had their own copy, and ``read-ui/components/Citation.tsx`` has a
fifth. Adding a field to a citation meant finding all of them.

One switch lives here. The mode CLIs and the router CLI call it, so the terminal output is the
same shape wherever a citation is printed.
"""

from __future__ import annotations

import json


def citation_lines(mode: str, cit, *, indent: str = "      ", quote_len: int = 200) -> list[str]:
    """One citation → terminal lines, keyed off the owning claim's mode.

    Mode A prints the edge triple and its confidence tag; Mode B the span, the verbatim quote
    and the graph nodes it joins to; Mode C the SQL and its result rows — because for Mode C
    the citation *is* the computation (§6 rule 3).
    """
    out = [f"{indent}source : {cit.source_file}"]
    if mode == "A":
        out.append(f"{indent}edge   : {cit.locator}  [{cit.confidence}]")
        if cit.note:
            out.append(f"{indent}at     : {cit.note}")
    elif mode == "B":
        if cit.note:
            out.append(f"{indent}note   : {cit.note}")
        out.append(f"{indent}span   : {cit.location}")
        out.append(f"{indent}quote  : {cit.quote[:quote_len].replace(chr(10), ' ').strip()}…")
        out.append(f"{indent}nodes  : {', '.join(cit.nodes) or '—'}")
    elif mode == "C":
        out.append(f"{indent}note   : {cit.note}")
        out.append(f"{indent}sql    : " + cit.sql.replace("\n", f"\n{indent}         "))
        out.append(f"{indent}result : " + json.dumps(cit.result))
    return out


def claim_lines(claim, *, index: int | None = None, indent: str = "      ") -> list[str]:
    """One claim and every citation under it."""
    head = f"CLAIM {index} [{claim.mode}]: {claim.text}" if index is not None \
        else f"CLAIM [{claim.mode}]: {claim.text}"
    out = [head]
    for cit in claim.citations:
        out.extend(citation_lines(claim.mode, cit, indent=indent))
    return out


def figure_lines(fig, *, indent: str = "  ") -> list[str]:
    """A Mode-C figure always prints with the SQL behind it — never a bare chart (§8)."""
    return [
        f"FIGURE {fig.spec}",
        f"{indent}query  : " + fig.query.replace("\n", f"\n{indent}         "),
        f"{indent}result : " + json.dumps(fig.result),
    ]


def association_lines(edges: list, *, limit: int = 8, indent: str = "  ") -> list[str]:
    """The merged graph edges, truncated — each with its EXTRACTED / INFERRED tag (§7)."""
    out = [f"ASSOCIATIONS ({len(edges)} edge(s)):"]
    for e in edges[:limit]:
        conf = e.get("confidence", "")
        out.append(f"{indent}{e.get('source')} --{e.get('relation', '?')}--> "
                   f"{e.get('target')}  [{conf}]")
    return out


def unanswered_lines(items, *, indent: str = "  ") -> list[str]:
    """§6 rule 4 — stated, never hidden. The code is printed alongside the prose."""
    out = ["UNANSWERED (no mode could ground — stated, not hidden):"]
    for u in items:
        out.append(f"{indent}• [{u.code.value}] {u.text}")
        if u.candidates:
            out.append(f"{indent}  candidates: {', '.join(u.candidates)}")
    return out
