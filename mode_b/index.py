"""Ingest WDB's prose corpus into a Chroma passage index.

Pipeline per file: ``walk_corpus`` (prose + .md, no CSVs — #6) → ``extract_with_
location`` (incl. the .md branch — #1) → ``sub_chunk`` → ``Embedder.encode``
(the locked model — #3) → Chroma ``add`` with the chunk's WDB-relative
``source_file`` as metadata (the sole join key — #4).

Two carry-overs are visible here:

* **#4 — no filename parser.** civ-kb derived org/year/lang/title from a CIV
  ``YYYY_ORG_TYPE_…`` filename convention and mis-parsed WDB's snake_case names.
  :func:`chunk_metadata` records ONLY ``source_file`` (+ basename/initiative/
  location for display); there are no org/year/lang fields and no filters built
  on them. ``source_file`` is the key that powers the document join (join.py).
* **#3 — the model lock.** The collection is stamped with the embedder id
  (``embed.collection_metadata``); the query side verifies it before searching.

The index is a *regenerable* artifact (architecture §9) — built on demand into
``index_dir`` (default ``mode_b/.index/``, uncommitted), not committed to git, so
the PR diff stays code + tests. Rebuild with ``python -m mode_b --ingest``.
"""

from __future__ import annotations

import os
from pathlib import Path

from .corpus import walk_corpus
from .embed import Embedder, collection_metadata
from .extract import extract_with_location, sub_chunk

COLLECTION = "wdb_passages"
DEFAULT_INDEX_DIR = str(Path(__file__).resolve().parent / ".index")


def chunk_metadata(source_file: str, location: str, chunk_idx: int) -> dict:
    """The metadata stored per chunk — ``source_file`` is the sole join key (#4).

    No org/year/lang/title (civ-kb's mis-parsing filename fields are dropped).
    Pure and deterministic, so the "drop the filename parser" correction is
    provable without building an index.
    """
    return {
        "source_file": source_file,                 # WDB-relative path — the join key
        "source_basename": Path(source_file).name,  # matched against graph.json basenames
        "initiative": source_file.split("/")[0] if "/" in source_file else "",
        "location": location,
        "chunk_idx": chunk_idx,
    }


def chunks_for(rel_path: str, root: str) -> list[tuple[str, str]]:
    """[(text, location), ...] for one corpus file (extract → sub_chunk)."""
    units = extract_with_location(Path(root) / rel_path)
    return [c for text, loc in units for c in sub_chunk(text, loc)]


def build_index(root: str, index_dir: str = DEFAULT_INDEX_DIR,
                embedder: Embedder | None = None, verbose: bool = True):
    """Build (fresh) the passage index over ``root``'s corpus. Returns the collection."""
    import chromadb

    embedder = embedder or Embedder()
    client = chromadb.PersistentClient(path=index_dir)
    try:
        client.delete_collection(COLLECTION)  # fresh each build -> reproducible
    except Exception:
        pass
    coll = client.create_collection(COLLECTION, metadata=collection_metadata(embedder.name))

    files = walk_corpus(root)
    total = 0
    for rel in files:
        chunks = chunks_for(rel, root)
        if not chunks:
            if verbose:
                print(f"  [skip] no text: {rel}")
            continue
        texts = [t for t, _ in chunks]
        metas = [chunk_metadata(rel, loc, i) for i, (_, loc) in enumerate(chunks)]
        ids = [f"{Path(rel).name}__{i}" for i in range(len(chunks))]
        coll.add(documents=texts, embeddings=embedder.encode(texts), metadatas=metas, ids=ids)
        total += len(chunks)
        if verbose:
            print(f"  + {rel}  ({len(chunks)} chunk(s))")

    if verbose:
        srcs = sorted({m["source_file"] for m in coll.get(include=["metadatas"])["metadatas"]})
        print(f"\nIndexed {total} chunk(s) from {len(srcs)} document(s) into {index_dir}")
        print(f"Embed model (locked): {embedder.name}")
        print(f"CSV files indexed: {sum(1 for s in srcs if s.endswith('.csv'))} (must be 0)")
    return coll


def open_collection(index_dir: str = DEFAULT_INDEX_DIR):
    """Open the existing passage collection (raises if it was never built)."""
    import chromadb

    if not os.path.isdir(index_dir):
        raise FileNotFoundError(
            f"no passage index at {index_dir} — build it with `python -m mode_b --ingest`"
        )
    client = chromadb.PersistentClient(path=index_dir)
    return client.get_collection(COLLECTION)
