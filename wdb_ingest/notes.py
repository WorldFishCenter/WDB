"""Serialize a DraftedNote to the markdown a ``<file>_dict.md`` / ``<file>_context.md`` actually is
(PROTOCOL §6 Template A/B) with the §8 provenance frontmatter. This is what gets written to git on
curator sign-off — the system of record from that moment (design §5). Mirrors
``read-ui/lib/ingestion/note.ts`` so the preview the UI shows matches the file written here.
"""

from __future__ import annotations

from .models import DraftedNote, Provenance


def _frontmatter(p: Provenance) -> list[str]:
    # The four PROTOCOL §8 fields, on the doc's OWN note (never a synthesis hub — §6 satellite rule 4).
    return [
        "---",
        f"contributor: {p.contributor}",
        f"author: {p.author}",
        f"captured_at: {p.captured_at}",
        f"source_url: {p.source_url}",
        "---",
    ]


def note_to_markdown(note: DraftedNote, provenance: Provenance) -> str:
    out: list[str] = [*_frontmatter(provenance), "", f"# {note.title}", "", "## Summary", note.summary]

    if note.template == "A":
        out += ["", "## Grain", note.grain or ""]
        out += ["", "## Columns"]
        for c in note.columns or []:
            out.append(f"- {c.name}: {c.meaning} — {c.domain}")
    else:
        out += ["", "## Key concepts / entities"]
        for k in note.key_concepts or []:
            out.append(f"- {k}")

    out += ["", "## Related files"]
    for r in note.related_files:
        out.append(f"- {r}")

    if note.template == "A" and note.notes_caveats:
        out += ["", "## Notes / caveats", note.notes_caveats]

    return "\n".join(out) + "\n"
