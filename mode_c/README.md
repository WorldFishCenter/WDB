# Mode C — structured query over WDB's tidy CSVs

Mode C answers **quantitative / computed** questions ("average CPUE in Kwale",
"crude protein of fish meal") by *querying* the committed CSVs with DuckDB —
never by retrieving prose. It is the other half of the passage verdict: the data
the passage index must keep *out* (raw tables) is answered correctly here by
querying it. See [`../docs/three-mode-architecture.md`](../docs/three-mode-architecture.md)
§4 and the two proofs ([`../proof_c/FINDINGS.md`](../proof_c/FINDINGS.md),
[`../proof_c/RESOLVER_FINDINGS.md`](../proof_c/RESOLVER_FINDINGS.md)).

This is a **standalone, tested module with a CLI** — not a router, serving layer,
or UI. The eventual router calls `answer_question`.

## Pipeline

```
question ─▶ resolver ─▶ vetted-band gate ─▶ DuckDB executor ─▶ answer contract
            (model)      (3 conditions)       (grain-faithful)   (Claim = SQL + rows)
                │                                                        │
                └─ cannot_resolve / needs_disambiguation ───────────────┴─▶ "not available"
```

| Stage | File | What it does |
|---|---|---|
| Resolver | [`resolver.py`](resolver.py) | NL question → `Resolution` (or refusal). Two mandatory guards (grain, derived metrics). `LiveResolver` (Opus 4.8) / `ReplayResolver` (recorded). |
| Catalog | [`catalog.py`](catalog.py) | Parses the 11 `_dict.md`s: value domains, `## Grain` (key + repeating columns), identity tokens. |
| Gate | [`gate.py`](gate.py) | The vetted band: distinctive value pins one table · column enumerated / formula registered · grain recorded (+ structural grain-trap guard). |
| Executor | [`executor.py`](executor.py) | DuckDB over the CSV in place; grain-faithful (dedupes to `grain_key` before aggregating); identifiers allow-listed, values bound. |
| Contract | [`contract.py`](contract.py) | `Answer` / `Claim` / `Citation` / `Figure` — a claim's citation **is** the SQL + result rows. |

## The two guards (what makes it trustworthy)

1. **Resolver-prompt guard** — the resolver prompt forces grain reasoning *and*
   derived-metric handling (formula + surfaced denominator, never a proxy). These
   moved the proof from 1/3 to 5/5 on grain and turned the CPUE proxy into an
   honest flagged derivation. See `GRAIN_GUARD` / `DERIVED_GUARD`.
2. **Vetted-band gate** — answers only when all three hold, else refuses/asks.
   The grain-trap arm is *structural*: aggregating a column the dict marks as
   repeating, without collapsing to its grain key, is refused by construction —
   so Kwale computes **31.88** (trip grain), never **28.99** (raw rows).

## Usage

```bash
uv sync --extra dev                # the one WDB env (see ../RUNNING.md)
python -m mode_c --list            # the replayable proof questions
python -m mode_c "Average total catch per trip in Kwale?"
python -m mode_c "Average CPUE in Kwale district?"
python -m mode_c "Average catch in Kisumu county?"     # -> NOT AVAILABLE

# live resolver (pinned Opus 4.8): the anthropic SDK ships in the env; just add a key
ANTHROPIC_API_KEY=... python -m mode_c --live "Average crude protein of fish meal?"
```

```python
from mode_c import load_catalog, answer_question, ReplayResolver
from mode_c.fixtures import RECORDED

catalog = load_catalog()
answer = answer_question("Average total catch per trip in Kwale?",
                         ReplayResolver(RECORDED), catalog)
print(answer.claims[0].text)               # ... is 31.88 (computed over 50422 trips).
print(answer.claims[0].citations[0].sql)   # the exact query behind the number
```

## Model & tests

The resolver model is pinned and recorded in [`MODEL.md`](MODEL.md)
(`claude-opus-4-8`). The regression suite (`../tests/`) replays the proof's
resolutions so the gate/executor/contract pipeline is verified deterministically:
9/9 questions answer correctly or refuse/disambiguate, the naive-control traps
are guarded, and out-of-band questions are refused. Run `pytest`.
