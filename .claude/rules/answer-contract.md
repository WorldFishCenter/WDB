---
paths:
  - "wdb_contract/**"
  - "mode_a/**"
  - "mode_b/**"
  - "mode_c/**"
  - "wdb_router/**"
  - "wdb_api/**"
  - "read-ui/lib/contract.ts"
  - "read-ui/components/AnswerView.tsx"
  - "read-ui/components/Refusal.tsx"
---

# The §6 answer contract

Spec: [docs/three-mode-architecture.md](../../docs/three-mode-architecture.md) §6–§7. Declaration:
`wdb_contract/contract.py`. Import the shape from there; a mode adds only its own construction
helpers.

## The four rules the types enforce

1. **Every claim carries ≥1 citation.** `Claim.__post_init__` raises `ClaimWithoutCitation`, so the
   contract cannot represent un-sourced prose. When citations do not survive assembly, return a
   stated refusal instead — that is what `mode_a.contract.from_reasoning` does when the reasoner
   cited nothing (cite-check C1 passes vacuously on an empty `cited_edges` list).
2. **A citation is a different artifact per mode**, keyed off `claim.mode`: `CitationA` is the graph
   edge triple plus its EXTRACTED/INFERRED tag, `CitationB` the passage span + verbatim quote +
   joined nodes, `CitationC` the SQL plus its result rows. Keep the three shapes distinct; render
   them through `wdb_contract.render`.
3. **`Verdict` distinguishes the two ways an answer carries no claims.** `VERIFIED_NEGATIVE` means
   the source was consulted and the answer is *no* — Mode A's `not_connected`, set with
   `negative=True` — and it is `answered`. `UNGROUNDED` means nothing could be grounded. Branch on
   `verdict`; deriving it from empty lists is what mislabelled the honest negative as a coverage
   refusal.
4. **Ungrounded parts are stated, never dropped or back-filled** — one `Unanswered` per part.

## Adding to the contract

Add the field in `wdb_contract`, then extend `merge()` if fragments combine it. `RouterAnswer`
inherits from `Answer`, so it needs no change — that inheritance is what stops the router dropping
a field by omission, which it previously did to `connected`, `path` and `disambiguation`.

Keep the wire **additive**: `answered` and `unanswered` (a list of rendered strings) hold their
current meaning for `read-ui`; new information goes in new keys, as `verdict` and
`unanswered_detail` did. `read-ui/lib/contract.ts` is a hand-maintained mirror — update it in the
same change, and add a fixture under `read-ui/fixtures/` for any state it does not yet cover.

## Refusals

Give every refusal an `UnansweredCode`. Assert on the code, never on the prose: refusal wording
authored in `mode_b/gate.py` was once pinned by tests in `wdb_router` and `wdb_api`, so editing a
message broke two other packages. A mode's gate returns the code (`GateResult.code`); the pipeline
passes it to `contract.refusal`.

## Seams

`Reasoner`, `Retriever`, `Synthesizer`, `Resolver` and `Reranker` are Protocols with a Live and a
Replay/Null adapter each, accepted as parameters. Construct model-backed dependencies at the call
site and pass them in — a dependency built inside a constructor cannot be substituted, and when
`LiveRetriever` built its own reranker behind a swallowed exception, a failed model load silently
moved Mode B's refusal floor from the calibrated rerank logit to the cosine threshold that
`mode_b/gate.py` documents as unable to refuse off-topic questions. `retriever.ranking_kind` states
which floor is in force.
