"""Correction #1 — the `.md` extractor branch (and that `.csv` has none).

civ-kb dispatches on pdf/docx/xlsx/pptx/txt only; WDB's curated knowledge lives
in `.md` companion notes. These tests prove `.md` is now a passage source and
that no tabular extractor was added (the complement, correction #6).
"""

from pathlib import Path

from mode_b.extract import DOC_EXTS, extract_with_location, sub_chunk


def test_md_is_a_prose_format_csv_is_not():
    assert ".md" in DOC_EXTS          # carry-over #1: notes are indexable
    assert ".csv" not in DOC_EXTS     # carry-over #6: raw tables never are
    assert ".xlsx" not in DOC_EXTS


def test_extract_md_yields_section_located_passages(wdb_root):
    note = Path(wdb_root) / "peskas" / "peskas_automated_analytics_softwarex_2025_context.md"
    units = extract_with_location(note)
    assert units, "the .md branch must extract passages from a real companion note"
    # every unit is (text, location); locations follow the note's ## headings
    assert all(isinstance(t, str) and t.strip() for t, _ in units)
    assert all(isinstance(loc, str) and loc for _, loc in units)
    # the curated prose is retrievable as text
    joined = " ".join(t for t, _ in units).lower()
    assert "peskas" in joined


def test_csv_extracts_nothing(wdb_root):
    csv = Path(wdb_root) / "peskas" / "kenya_validated_trips.csv"
    assert extract_with_location(csv) == []   # no .csv branch, by design


def test_sub_chunk_preserves_location_and_splits_oversized():
    small = sub_chunk("a few words", "page 1")
    assert small == [("a few words", "page 1")]
    big = sub_chunk(" ".join(f"w{i}" for i in range(900)), "page 7")
    assert len(big) > 1
    assert all(loc.startswith("page 7 [part ") for _, loc in big)
