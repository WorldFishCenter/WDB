"""Correction #4 — drop civ-kb's filename parser; key on `source_file`.

civ-kb derived org/year/lang/title from a CIV `YYYY_ORG_TYPE_…` filename
convention and mis-parsed WDB's snake_case names. Mode B records ONLY the
WDB-relative `source_file` (+ display fields) and builds no org/year/lang filter.
Pure metadata construction — provable deterministically.
"""

from mode_b.index import chunk_metadata


def test_metadata_keys_on_source_file_only():
    md = chunk_metadata("peskas/peskas_automated_analytics_softwarex_2025.pdf", "page 2", 3)

    assert md["source_file"] == "peskas/peskas_automated_analytics_softwarex_2025.pdf"
    assert md["source_basename"] == "peskas_automated_analytics_softwarex_2025.pdf"
    assert md["initiative"] == "peskas"
    assert md["location"] == "page 2"
    assert md["chunk_idx"] == 3

    # NONE of civ-kb's mis-parsed filename fields are present (carry-over #4)
    for civ_field in ("org", "year", "lang", "title", "doc_type"):
        assert civ_field not in md


def test_initiative_is_folder_not_parsed_filename():
    md = chunk_metadata("fasa/FICD_feed_ingredient_composition_database_dict.md", "Columns", 0)
    # would-be CIV parse would read org="FICD"/year="..."; we take the folder instead
    assert md["initiative"] == "fasa"
    assert md["source_file"].startswith("fasa/")
