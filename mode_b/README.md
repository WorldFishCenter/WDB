# Mode B — passage retrieval + cited synthesis

Mode B answers **synthesis** questions ("how does Peskas validate catch survey
data?", "research gaps for cage culture") by **retrieving verbatim passages** from
WDB's prose + companion notes, **synthesizing a cited answer**, and **joining each
passage to its graph associations** at document grain — or returning a clean "not
available" when retrieval is thin. It never synthesizes from the model's own
knowledge. See [`../docs/three-mode-architecture.md`](../docs/three-mode-architecture.md)
§3/§6/§7 and the proof ([`../proof/FINDINGS.md`](../proof/FINDINGS.md)).

This is a **standalone, tested module with a CLI** — not a router, serving layer,
or UI. The eventual router calls `answer_question`. The retrieval core is
**vendored** from civ-kb (no civ-kb runtime dependency).

## Pipeline

```
question ─▶ retrieve ─▶ rerank ─▶ refuse-when-thin ─▶ synthesize ─▶ join ─▶ answer contract
            (model-      (cross-    (gate, §7)          (Sonnet 4.6)  (doc    (Claim = quote +
             locked)      encoder)        │                          grain)   span + node(s))
                                          └────────────── "not available" (stated, never invented)
```

| Stage | File | What it does |
|---|---|---|
| Corpus | [`corpus.py`](corpus.py) | Which files are passages: prose + `.md` notes **in**, raw CSVs + infra **out** (#6). |
| Extract | [`extract.py`](extract.py) | Vendored extractors + `sub_chunk`; **adds the `.md` branch** (#1); no `.csv`/`.xlsx`. |
| Embed | [`embed.py`](embed.py) | The one locked embedder; stamps + verifies the index's model (#3). |
| Index | [`index.py`](index.py) | Walk → extract → chunk → embed → Chroma; `source_file` is the only join key (#4). |
| Retrieve | [`retrieve.py`](retrieve.py) | `query_embeddings=` (locked) + optional rerank. `LiveRetriever` / `ReplayRetriever`. |
| Gate | [`gate.py`](gate.py) | Refuse-when-thin: empty / below floor / off-topic drift (#5). |
| Join | [`join.py`](join.py) | Passage↔graph at document grain, both ways, with companion-note normalization (#2). |
| Synthesize | [`synth.py`](synth.py) | Cited answer from passages. `LiveSynthesizer` (Sonnet 4.6) / `ReplaySynthesizer`. |
| Contract | [`contract.py`](contract.py) | `Answer`/`Claim`/`Citation`: a claim's citation **is** the passage quote + span + node(s). |

## The six mandatory corrections (all from the proof / architecture docs)

1. **`.md` extractor branch** — companion notes are indexed as passages ([extract.py](extract.py)).
2. **Companion-note normalization** — `X_context.md`/`X_dict.md` → `X` in both join directions ([join.py](join.py)).
3. **Query-embedding model lock** — queries embed with the index's model; mismatch raises ([embed.py](embed.py)).
4. **No civ-kb filename parser** — `source_file` is the sole join key; no org/year/lang ([index.py](index.py)).
5. **Refuse-when-thin gate** — thin retrieval returns "not available", never synthesis-from-nothing ([gate.py](gate.py)).
6. **Raw CSVs excluded** — only prose + `.md` are indexed; tabular questions are Mode C's ([corpus.py](corpus.py)).

> **The refuse-when-thin floor is a provisional placeholder, not a tuned value.**
> The proof flagged the similarity floor as uncalibrated on a ~34-file corpus, so
> the floors in [`gate.py`](gate.py) are illustrative defaults to recalibrate once
> the corpus grows. The *principled* floor is on the **reranked** passages
> (`RERANK_FLOOR = 0`: a cross-encoder logit `<0` means "not relevant", model-
> calibrated, not corpus-tuned). `COSINE_FLOOR_PCT` is only the rerankerless
> fallback, and on a small corpus a bi-encoder scores even off-topic passages
> moderately — so it does *not* reliably refuse a topically-uncovered question
> (live, a Norway salmon question scored ~59% vs. Timor-Leste nutrition passages).
> That's a documented limitation of the fallback, not something to fix by tuning
> the placeholder. The refusal *guarantee* is the empty/thin arm (proven
> deterministically) + the coverage arm; the tests pin the gate's logic, not the
> numbers.

## Usage

```bash
uv sync --extra dev                          # the one WDB env (see ../RUNNING.md)
python -m mode_b --ingest                    # build the passage index (prose + .md, no CSVs)
python -m mode_b --list-corpus               # what's indexed (and that 0 CSVs are)
python -m mode_b "How does Peskas validate small-scale fishery catch survey data?"

# live synthesis (pinned Sonnet 4.6): the anthropic SDK ships in the env; just add a key
ANTHROPIC_API_KEY=... python -m mode_b "Research gaps for cage culture in Zambia?"
```

Without `ANTHROPIC_API_KEY` the CLI still runs retrieval + the graph join and
prints the cited passages and their associations (synthesis skipped).

```python
from mode_b import answer_question, load_graph_default, ReplayRetriever, ReplaySynthesizer
from mode_b.fixtures import RECORDED_PASSAGES, RECORDED_SYNTHESIS, Q_COVERED

nodes, links = load_graph_default()
answer = answer_question(Q_COVERED, ReplayRetriever(RECORDED_PASSAGES),
                         ReplaySynthesizer(RECORDED_SYNTHESIS), nodes, links)
cit = answer.claims[0].citations[0]
print(cit.quote, cit.location, cit.nodes)    # passage span + verbatim quote + graph node(s)
```

## Model & tests

The synthesis model is pinned and recorded in [`MODEL.md`](MODEL.md)
(`claude-sonnet-4-6`) — deliberately independent of the Opus-4.8 graph/Mode-C pin.
The suite is deterministic (offline Replay backends): each of the six corrections
has a dedicated test, plus the join (both directions, on real `graph.json`), the
gate, the contract, and the end-to-end pipeline. The bonus `test_index_live.py`
builds a real index and **skips** when chromadb/sentence-transformers are absent.

```bash
python -m pytest mode_b/tests        # from the WDB repo root
```
