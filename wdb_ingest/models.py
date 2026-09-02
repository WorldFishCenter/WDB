"""Pydantic models for the ingestion workflow — the wire contract.

These mirror the TypeScript shapes in ``read-ui/lib/ingestion/types.ts`` **field-for-field** (camelCase
on the wire via aliases) so rewiring the UI off its mock store onto this API is a swap, not a rewrite.
A ``Submission`` is one row of the workflow state the design parks in Atlas (design §8); ``Provenance``
is the four PROTOCOL §8 frontmatter fields; ``DraftedNote`` is the PROTOCOL §6 Template A/B note.
"""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, ConfigDict, Field


class WorkflowState(str, Enum):
    SUBMITTED = "SUBMITTED"
    DRAFTED = "DRAFTED"
    UNDER_REVIEW = "UNDER_REVIEW"
    PENDING = "PENDING"
    QUEUED = "QUEUED"
    BUILT = "BUILT"
    LIVE = "LIVE"
    REJECTED = "REJECTED"


class Role(str, Enum):
    CONTRIBUTOR = "contributor"
    CURATOR = "curator"


class _Model(BaseModel):
    # Accept either the python name or the camelCase alias on input; emit camelCase via by_alias.
    model_config = ConfigDict(populate_by_name=True)


class Provenance(_Model):
    contributor: str
    author: str
    captured_at: str
    source_url: str


class ColumnEntry(_Model):
    name: str
    meaning: str
    domain: str


class DraftedNote(_Model):
    template: str  # "A" (tabular) | "B" (everything else)
    filename: str
    title: str
    summary: str
    grain: str | None = None
    columns: list[ColumnEntry] | None = None
    key_concepts: list[str] | None = Field(default=None, alias="keyConcepts")
    related_files: list[str] = Field(default_factory=list, alias="relatedFiles")
    notes_caveats: str | None = Field(default=None, alias="notesCaveats")


class HistoryEntry(_Model):
    state: WorkflowState
    at: str
    actor: str
    note: str | None = None


class Submission(_Model):
    id: str
    filename: str
    format: str
    size_label: str = Field(alias="sizeLabel")
    initiative: str
    target_placement: str = Field(alias="targetPlacement")
    state: WorkflowState
    provenance: Provenance
    draft: DraftedNote | None = None
    curator_edited: bool = Field(default=False, alias="curatorEdited")
    rejection_reason: str | None = Field(default=None, alias="rejectionReason")
    history: list[HistoryEntry] = Field(default_factory=list)


class SubmissionInput(_Model):
    """Metadata accompanying an upload (the file bytes arrive as the raw request body)."""

    filename: str
    format: str  # phase-1: pdf | tabular | doc
    size_label: str = Field(alias="sizeLabel")
    initiative: str
    author: str = ""
    source_url: str = Field(default="", alias="sourceUrl")
