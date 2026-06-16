"""Pinned, recorded reasoner model — the Mode-A analogue of BUILD_INFO.md.

Per the three-mode architecture doc §9 (governance) and the repo's pinned-model
discipline ([../CLAUDE.md](../CLAUDE.md)), the reasoning step is a deliberate,
recorded choice: reasoning over a subgraph is a model decision, so a model change
must be a visible diff. Pin the EXACT id, not the floating ``opus`` alias.

``REASONER_MAX_TOKENS`` is pinned too: the cold-fabrication-rate run
([MODEL.md](MODEL.md)) showed a large 1-hop neighborhood (Peskas, 40 edges)
serializes to JSON that overflows a 2000-token budget and truncates. 8000 clears
it; enumeration-shaped questions route to the cheap path anyway, so the reasoner
only ever serializes the bounded relational subgraphs.

To upgrade: change ``REASONER_MODEL`` here and update ``mode_a/MODEL.md`` in the
same commit so the switch is recorded.
"""

REASONER_MODEL = "claude-opus-4-8"
REASONER_MAX_TOKENS = 8000
