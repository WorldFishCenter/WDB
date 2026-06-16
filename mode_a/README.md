# Mode A — graph relationships / enumeration (reasoning-strength, routed)

Mode A answers **"what connects to what"** over WDB's committed graph
([graphify-out/graph.json](../graphify-out/graph.json)). It is a **routed augmentation**,
not a replacement, of the cheap enumeration stand-in: direct questions stay cheap;
multi-hop / explanatory ones get an LLM reasoning over a deterministically-extracted
subgraph, **gated by a mechanical cite-check**. This is the "constrained middle" the proof
recommended ([../proof_a/FINDINGS.md](../proof_a/FINDINGS.md)).

## The two paths (routed by question shape — `route.py`)

| Question shape | Path | Extraction | Model? |
|---|---|---|---|
| "What is X connected to?", "list the X of Y" | **enumeration** | 1-hop `neighborhood` | **no** |
| "How / why do X and Y relate?" | **reasoning** | `relate` (direct edges + ≤2-hop paths) | yes (gated) |
| "Which initiatives share … with X, and how?" | **reasoning** | `bridges` (2-hop shared connectors) | yes (gated) |

`route.py` is Mode A's *internal* shape router — distinct from the cross-mode
`router/intent.py` (which decides A vs B vs C).

## The honesty wrapper (why the LLM is safe here)

The reasoning path is `extract → reason → CITE-CHECK → contract`:

1. **Deterministic extraction** (`extract.py`) pulls a small subgraph — no model, no
   network, no embeddings. Depth-2 was sufficient for every proof question.
2. **The reasoner** (`reasoner.py`, pinned `claude-opus-4-8`) sees **only** the serialized
   subgraph and returns **structured citations** (`cited_edges`, EXTRACTED/INFERRED tagged).
3. **The mechanical cite-check** (`citecheck.py`, C1–C4) exact-matches every cited edge
   against the subgraph's real edges **before** the answer is surfaced. A failed check
   **never surfaces** — it downgrades to cheap enumeration on the anchor, or "not available".

The cite-check — not the model — is what makes the reasoner safe. Its teeth are proven by
the negative control ([tests/test_negative_control.py](tests/test_negative_control.py)), and
the cold model's fabrication-attempt rate is measured at **0/10** ([MODEL.md](MODEL.md)).
The soft risk C1 does *not* catch (prose over-claim) is owned by the reasoner prompt's
rule 6 + a spot-review note in MODEL.md.

## CLI

```
python -m mode_a "What is Peskas connected to?"                        # enumeration (no model)
python -m mode_a "How does Peskas relate to WIO data harmonization?"   # reasoning (Replay by default)
python -m mode_a --live "Which initiatives share data with Peskas?"    # reasoning via live Opus 4.8
python -m mode_a --list                                                # replayable reasoning questions
python -m mode_a.cold_rate                                             # re-run the cold-fabrication-rate measurement
```

Offline (default) the reasoning path uses `ReplayReasoner` (recorded proof answers); the
enumeration path needs no model. `--live` needs the `anthropic` SDK + `ANTHROPIC_API_KEY`.

## Answer contract (§6)

`answer_question(question, reasoner, graph) -> Answer` returns the §6 shape: `claims`
(each `mode="A"`, ≥1 `Citation` to a real edge with its EXTRACTED/INFERRED tag),
`associations` (the subgraph edges), `connected` (bool on the reasoning path), and
`unanswered` (stated, never silently dropped). A verified not-connected verdict is a
correct answer (`connected=False`, zero claims), not a failure.

## Layout

`model.py` (pin) · `extract.py` (subgraph extraction) · `route.py` (shape router) ·
`reasoner.py` (Live/Replay) · `citecheck.py` (the C1–C4 gate) · `contract.py` (§6 assembly) ·
`pipeline.py` (orchestration + downgrade) · `cli.py` · `cold_rate.py` (the measurement) ·
`fixtures/` (recorded answers) · `tests/`.
