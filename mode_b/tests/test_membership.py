"""Correction #6 — exclude raw CSVs (and infra) from the passage index.

The corpus walker decides index membership; the index contains exactly what it
yields. So proving membership on the walker is the deterministic guarantee that
raw CSVs are NEVER indexed and companion `.md` notes ARE — no index build needed.
"""

from mode_b.corpus import is_indexable, walk_corpus


def test_walker_includes_notes_and_prose_never_csv(wdb_root):
    files = walk_corpus(wdb_root)

    # raw tables are never indexed (carry-over #6)
    assert not any(f.endswith(".csv") for f in files)
    assert not any(f.endswith((".xlsx", ".xls")) for f in files)

    # companion notes ARE indexed (carry-over #1)
    assert "peskas/peskas_automated_analytics_softwarex_2025_context.md" in files
    assert any(f.endswith("_dict.md") for f in files)
    assert any(f.endswith("_about.md") for f in files)

    # prose source docs are indexed
    assert "peskas/peskas_automated_analytics_softwarex_2025.pdf" in files
    assert "data_harmonization/WIOMSA_harmonization_OCT2025.pdf" in files


def test_walker_excludes_infrastructure(wdb_root):
    files = set(walk_corpus(wdb_root))
    # protocol / readme / guides are not corpus
    for infra in ("README.md", "PROTOCOL.md", "CLAUDE.md", "USER_GUIDE.md"):
        assert infra not in files
    # module code, proofs, the graph build, design docs, vendored RAG core
    assert not any(f.startswith(("mode_b/", "mode_c/", "proof/", "proof_c/",
                                 "docs/", "civ-kb/", "graphify-out/", "tests/")) for f in files)


def test_is_indexable_unit_cases():
    assert is_indexable("peskas/x_context.md")
    assert is_indexable("peskas/paper.pdf")
    assert not is_indexable("peskas/kenya_validated_trips.csv")   # CSV out (#6)
    assert not is_indexable("fasa/table.xlsx")                    # xlsx out (#6)
    assert not is_indexable("README.md")                         # infra md out
    assert not is_indexable("mode_b/cli.py")                     # module code out
    assert not is_indexable("civ-kb/data/doc.pdf")              # vendored corpus out
    assert not is_indexable("wdb_mode_c.egg-info/SOURCES.txt")   # packaging cruft out
