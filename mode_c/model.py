"""Pinned, recorded resolver model — the Mode-C analogue of BUILD_INFO.md.

Per the three-mode architecture doc §9 (governance) and the repo's pinned-model
discipline (CLAUDE.md), the resolver model is a deliberate, recorded choice:
mapping a question→table/column is a routing decision, so a model change must be
a visible diff. Pin the EXACT id, not the floating ``opus`` alias.

To upgrade: change ``RESOLVER_MODEL`` here and update ``mode_c/MODEL.md`` in the
same commit so the switch is recorded.
"""

RESOLVER_MODEL = "claude-opus-4-8"
