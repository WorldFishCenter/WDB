"""BONUS live integration — real ingest + retrieval over real WDB files.

NOT part of the deterministic regression guarantee: it skips unless chromadb +
sentence-transformers (and the cached embed model) are available. When it runs it
confirms end-to-end what the deterministic tests assert structurally — `.md` notes
are indexed, raw CSVs are not, and queries embed with the index's locked model.
"""

import shutil
from pathlib import Path

import pytest

chromadb = pytest.importorskip("chromadb")
pytest.importorskip("sentence_transformers")


@pytest.fixture(scope="module")
def tiny_root(tmp_path_factory, wdb_root):
    """A minimal corpus: a real companion note + a real CSV (which must stay out)."""
    root = tmp_path_factory.mktemp("tiny_corpus")
    (root / "peskas").mkdir()
    src = Path(wdb_root) / "peskas"
    shutil.copy(src / "peskas_automated_analytics_softwarex_2025_context.md",
                root / "peskas" / "peskas_automated_analytics_softwarex_2025_context.md")
    shutil.copy(src / "kenya_validated_trips.csv",
                root / "peskas" / "kenya_validated_trips.csv")   # must NOT be indexed
    return str(root)


def test_live_build_indexes_md_excludes_csv_and_locks_model(tiny_root):
    from mode_b.embed import Embedder, verify_collection_model
    from mode_b.index import build_index
    from mode_b.model import EMBED_MODEL
    from mode_b.retrieve import LiveRetriever

    index_dir = str(Path(tiny_root) / ".index")
    try:
        embedder = Embedder()
        embedder._load()  # may download/load the model; skip if unavailable offline
    except Exception as e:  # pragma: no cover - environment dependent
        pytest.skip(f"embed model unavailable: {e}")

    coll = build_index(tiny_root, index_dir=index_dir, embedder=embedder, verbose=False)
    srcs = {m["source_file"] for m in coll.get(include=["metadatas"])["metadatas"]}

    assert any(s.endswith("_context.md") for s in srcs)          # .md indexed (#1)
    assert not any(s.endswith(".csv") for s in srcs)             # raw CSV excluded (#6)

    # the collection records its embedder, and the lock verifies clean (#3)
    assert coll.metadata["embed_model"] == EMBED_MODEL
    verify_collection_model(coll.metadata)

    retriever = LiveRetriever(coll, embedder=embedder, use_reranker=False)
    passages = retriever.retrieve("How does Peskas validate catch survey data?", k=3)
    assert passages
    assert all(p.source_file.endswith(".md") for p in passages)   # only the note is in
