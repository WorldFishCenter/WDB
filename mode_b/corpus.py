"""Corpus membership — which WDB files become passages, which never do.

This is the deterministic gate for two of the mandatory corrections:

* **Raw CSVs (and all tabular formats) are excluded (carry-over #6).** They
  retrieve misleadingly and 100×-inflate the index (proof/FINDINGS.md Q2); Mode C
  answers tabular questions by querying them. Only ``DOC_EXTS`` (prose + .md) is
  ever indexed — ``.csv`` is not in that set, and there is no csv extractor.
* **Companion ``.md`` notes ARE included (carry-over #1).** They are where curated
  knowledge lives — worth quoting verbatim.

It also keeps infrastructure out of the index (the protocol/readme/guides, the
serving-layer code, the proofs, the graph build, virtualenvs) so a passage search
never returns Mode B's own source or a `.graphifyignore`d sibling. The selection
is filename/path-based and offline, so it is provable by a deterministic test
without building an index or loading a model.
"""

from __future__ import annotations

import os
from pathlib import Path

from .extract import DOC_EXTS

# Directory names anywhere in the path that are never corpus (infra / tooling /
# the graph build / other projects). Mirrors the repo's .graphifyignore intent.
_EXCLUDE_DIRS = {
    ".git", ".github", ".claude", "__pycache__", ".venv", "venv",
    "node_modules", "dist", "build", ".eggs", ".pytest_cache",
    "graphify-out",                       # the graph build artifacts
    "civ-kb", "proof", "proof_c",         # the RAG core + the read-only proofs
    "mode_b", "mode_c", "tests", "docs",  # serving/module code + design docs
}


def _is_excluded_dir(name: str) -> bool:
    """Exact infra dirs + any packaging metadata dir (``*.egg-info``)."""
    return name in _EXCLUDE_DIRS or name.endswith(".egg-info")

# Top-level infra Markdown that is NOT a companion note (so the .md branch does
# not sweep the protocol/readme/guides into the passage index).
_EXCLUDE_MD_NAMES = {
    "readme.md", "protocol.md", "claude.md", "user_guide.md", "changelog.md",
}


def is_indexable(rel_path: str) -> bool:
    """True iff ``rel_path`` (WDB-relative) is a prose passage source.

    Excludes CSVs/xlsx (not in DOC_EXTS), infra directories, and the top-level
    infra Markdown — includes prose docs and companion ``.md`` notes.
    """
    p = Path(rel_path)
    if any(_is_excluded_dir(part) for part in p.parts):
        return False
    if p.suffix.lower() not in DOC_EXTS:        # .csv / .xlsx land here -> excluded
        return False
    if p.suffix.lower() == ".md" and p.name.lower() in _EXCLUDE_MD_NAMES:
        return False
    return True


def walk_corpus(root: str) -> list[str]:
    """Every indexable file under ``root``, as sorted WDB-relative paths."""
    root = os.path.abspath(root)
    found: list[str] = []
    for dirpath, dirnames, filenames in os.walk(root):
        # prune excluded directories in place so we never descend into them
        dirnames[:] = [d for d in dirnames if not _is_excluded_dir(d)]
        for name in filenames:
            rel = os.path.relpath(os.path.join(dirpath, name), root)
            if is_indexable(rel):
                found.append(rel)
    return sorted(found)


def companion_note(rel_path: str, root: str) -> str | None:
    """The ``_context.md`` companion of a source doc, if one exists on disk.

    Used by the answer contract's ``note`` pointer (§6): a cited PDF/DOCX passage
    points at the curated note for that document. A note cites itself.
    """
    p = Path(rel_path)
    if p.suffix.lower() == ".md":
        return rel_path
    candidate = p.with_name(f"{p.stem}_context.md")
    return str(candidate) if (Path(root) / candidate).exists() else None
