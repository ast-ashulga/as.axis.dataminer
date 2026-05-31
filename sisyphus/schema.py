"""Pydantic v2 schema models enforcing the Sisyphus output contract.

Key invariants enforced here (not just documented):
- AI-generated content is always status=candidate + confidence_tier=inspired at creation.
- AI-generated content cannot be assigned confidence_tier=documented.
- inspired is not a valid tier for confirmed annotation records.
- NAS addresses must match the canonical regex.
- reviewed_by / reviewed_at are always null at creation.
"""

import re
from datetime import datetime
from enum import StrEnum
from typing import Annotated, ClassVar, Literal

from pydantic import BaseModel, Field, field_validator, model_validator

# ---------------------------------------------------------------------------
# Enumerations
# ---------------------------------------------------------------------------

NAS_PATTERN = re.compile(r"^nms://[a-z0-9-]+(/[a-z0-9-]+){1,3}$")


class Status(StrEnum):
    candidate = "candidate"
    confirmed = "confirmed"
    rejected = "rejected"
    deferred = "deferred"


class ConfidenceTier(StrEnum):
    documented = "documented"
    reconstructed = "reconstructed"
    contested = "contested"
    inspired = "inspired"


class Layer(StrEnum):
    surface = "surface"
    translated = "translated"
    scholaria = "scholaria"
    original = "original"  # Layer 3; feature-flagged off


class ManuscriptLayer(StrEnum):
    sbv = "sbv"
    obv = "obv"
    bilgames = "bilgames"


class AnnotationTrack(StrEnum):
    propp = "propp"
    bakhtin = "bakhtin"
    tmi = "tmi"
    # campbell is explicitly excluded (campbell_track flag = false)


# ---------------------------------------------------------------------------
# NAS address validator (reusable annotation)
# ---------------------------------------------------------------------------

NASAddress = Annotated[str, Field(pattern=r"^nms://[a-z0-9-]+(/[a-z0-9-]+){1,3}$")]


def validate_nas(v: str) -> str:
    if not NAS_PATTERN.match(v):
        raise ValueError(
            f"NAS address '{v}' does not match ^nms://[a-z0-9-]+(/[a-z0-9-]+){{1,3}}$"
        )
    return v


# ---------------------------------------------------------------------------
# Content records
# ---------------------------------------------------------------------------


class ContentRecord(BaseModel):
    """One content row — maps to fragment_content table."""

    locale: str = Field(min_length=2, max_length=10)
    layer: Layer
    body: str
    status: Status = Status.candidate
    confidence_tier: ConfidenceTier
    ai_generated: bool
    reviewed_by: str | None = None
    reviewed_at: datetime | None = None

    # Surface/scholaria: no translation_id
    translation_id: str | None = None
    translation_author: str | None = None
    translation_year: int | None = None
    translation_license: str | None = None

    # NAS citations for grounding validation (Phase C)
    grounding_citations: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def enforce_ai_invariants(self) -> "ContentRecord":
        if self.ai_generated:
            # AI content must always be candidate at creation
            if self.status != Status.candidate:
                raise ValueError(
                    "AI-generated content must have status=candidate at creation"
                )
            # AI content cannot be documented
            if self.confidence_tier == ConfidenceTier.documented:
                raise ValueError(
                    "AI-generated content cannot be assigned confidence_tier=documented"
                )
            # AI surface summaries must start at inspired
            if self.layer == Layer.surface and self.confidence_tier != ConfidenceTier.inspired:
                raise ValueError(
                    "AI-generated surface summaries must have confidence_tier=inspired at creation"
                )
            # reviewed_by/reviewed_at must be null at creation for AI content
            if self.reviewed_by is not None or self.reviewed_at is not None:
                raise ValueError(
                    "reviewed_by and reviewed_at must be null at creation for AI-generated content"
                )
        return self

    @field_validator("grounding_citations", mode="before")
    @classmethod
    def validate_citations(cls, v: list) -> list:
        for cite in v:
            validate_nas(cite)
        return v


# ---------------------------------------------------------------------------
# Fragment record
# ---------------------------------------------------------------------------


class FragmentRecord(BaseModel):
    """Core fragment — maps to fragments table."""

    nas: NASAddress
    parent_nas: NASAddress | None = None
    tradition_id: str
    confidence_tier: ConfidenceTier
    sequence_position: int | None = None
    available_layers: list[Layer] = Field(default_factory=list)
    source_language: str | None = None  # ISO 639-3
    manuscript_layer: ManuscriptLayer | None = None

    # Methodology-fit gate (Phase B)
    methodology_fit_warning: bool = False
    methodology_fit_note: str | None = None

    @model_validator(mode="after")
    def fit_note_requires_warning(self) -> "FragmentRecord":
        if self.methodology_fit_note and not self.methodology_fit_warning:
            raise ValueError(
                "methodology_fit_note requires methodology_fit_warning=true"
            )
        return self


class FragmentFile(BaseModel):
    """Top-level fragment YAML file (fragments/{division}/{episode}.yaml)."""

    _sisyphus_version: ClassVar[str] = "0.1"

    fragment: FragmentRecord
    content: list[ContentRecord] = Field(default_factory=list)
    translation_registry: list[str] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Annotation candidates
# ---------------------------------------------------------------------------


class AnnotationCandidate(BaseModel):
    """One annotation proposal (maps to annotation-candidates table)."""

    code: str
    label: str
    proposed_tier: ConfidenceTier
    status: Status = Status.candidate
    rationale: str
    evidence_citations: list[str] = Field(default_factory=list)
    methodology_fit_warning: bool = False
    methodology_fit_note: str | None = None
    ai_generated: bool = True

    @model_validator(mode="after")
    def validate_confirmed_tier(self) -> "AnnotationCandidate":
        # inspired is not valid for confirmed annotations
        if self.status == Status.confirmed and self.proposed_tier == ConfidenceTier.inspired:
            raise ValueError(
                "inspired confidence_tier is not valid for confirmed annotation records; "
                "speculative annotations must be rejected, not confirmed"
            )
        return self

    @model_validator(mode="after")
    def fit_note_requires_warning(self) -> "AnnotationCandidate":
        if self.methodology_fit_note and not self.methodology_fit_warning:
            raise ValueError(
                "methodology_fit_note requires methodology_fit_warning=true"
            )
        return self


class AnnotationFile(BaseModel):
    """annotation-candidates/{division}/{episode}.{track}.yaml"""

    _sisyphus_version: ClassVar[str] = "0.1"
    nas: NASAddress
    track: AnnotationTrack
    annotations: list[AnnotationCandidate] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# NAS proposals / confirmed
# ---------------------------------------------------------------------------


class NASProposal(BaseModel):
    proposed_nas: NASAddress
    parent_nas: NASAddress | None = None
    tradition_id: str
    division: str
    episode: str
    granularity: Literal["episode", "sub-episode", "verse-range", "lacuna"] = "episode"
    status: Literal["proposed", "confirmed", "revised", "deferred"] = "proposed"
    revised_nas: NASAddress | None = None
    collision_detected: bool = False
    methodology_fit_warning: bool = False
    methodology_fit_note: str | None = None

    @model_validator(mode="after")
    def revised_requires_revised_nas(self) -> "NASProposal":
        if self.status == "revised" and not self.revised_nas:
            raise ValueError("revised proposals must include revised_nas")
        return self


class NASProposalsFile(BaseModel):
    """output/{tradition}/nas-proposals.yaml"""

    _sisyphus_version: ClassVar[str] = "0.1"
    tradition_id: str
    proposals: list[NASProposal] = Field(default_factory=list)


class NASConfirmedEntry(BaseModel):
    nas: NASAddress
    parent_nas: NASAddress | None = None
    tradition_id: str
    division: str
    episode: str
    granularity: Literal["episode", "sub-episode", "verse-range", "lacuna"] = "episode"
    confirmed_by: str
    confirmed_at: datetime


class NASConfirmedFile(BaseModel):
    """output/{tradition}/nas-confirmed.yaml"""

    _sisyphus_version: ClassVar[str] = "0.1"
    tradition_id: str
    entries: list[NASConfirmedEntry] = Field(default_factory=list)


class NASRevision(BaseModel):
    old_nas: NASAddress
    new_nas: NASAddress
    tradition_id: str
    reason: str
    revised_by: str
    revised_at: datetime


class NASRevisionsFile(BaseModel):
    """output/{tradition}/nas-revisions.yaml"""

    _sisyphus_version: ClassVar[str] = "0.1"
    tradition_id: str
    revisions: list[NASRevision] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Artifact records
# ---------------------------------------------------------------------------


class ArtifactRecord(BaseModel):
    institution: str
    accession_number: str | None = None
    license: str
    confidence_tier: ConfidenceTier
    caption_en: str | None = None
    caption_ru: str | None = None
    view_url: str | None = None
    asset_path: str | None = None
    status: Status = Status.candidate


class ArtifactsFile(BaseModel):
    """artifacts/{division}/{episode}.artifacts.yaml"""

    _sisyphus_version: ClassVar[str] = "0.1"
    nas: NASAddress
    artifacts: list[ArtifactRecord] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Translation registry entry (in manifest)
# ---------------------------------------------------------------------------


class TranslationEntry(BaseModel):
    id: str
    author: str
    year: int
    locale: str
    license: str
    layer: Layer
    source_file: str | None = None
    ocr_applied: bool = False


# ---------------------------------------------------------------------------
# Manifest
# ---------------------------------------------------------------------------


class TraditionManifest(BaseModel):
    """output/{tradition}/manifest.yaml"""

    _sisyphus_version: ClassVar[str] = "0.1"
    tradition: str
    manuscript_layer: ManuscriptLayer | None = None
    living_tradition: bool = False
    public_release: bool = True
    translations: list[TranslationEntry] = Field(default_factory=list)
    pipeline_run_ids: list[str] = Field(default_factory=list)
    checksums: dict[str, str] = Field(default_factory=dict)


# ---------------------------------------------------------------------------
# Review decisions (audit trail)
# ---------------------------------------------------------------------------


class ReviewAction(StrEnum):
    confirmed = "confirmed"
    rejected = "rejected"
    modified_confirmed = "modified_confirmed"
    deferred = "deferred"


class ReviewDecision(BaseModel):
    audit_id: str
    timestamp: datetime
    reviewer: str
    action: ReviewAction
    record_type: Literal["summary", "annotation", "parallel"]
    nas: NASAddress
    track: AnnotationTrack | None = None
    code: str | None = None
    confidence_tier_assigned: ConfidenceTier | None = None
    review_note: str | None = None

    @model_validator(mode="after")
    def confirmed_requires_tier(self) -> "ReviewDecision":
        if self.action in (ReviewAction.confirmed, ReviewAction.modified_confirmed):
            if self.confidence_tier_assigned is None:
                raise ValueError(
                    "CONFIRM and MODIFY-THEN-CONFIRM actions require confidence_tier_assigned"
                )
            # inspired is not valid for confirmed annotations
            if (
                self.record_type == "annotation"
                and self.confidence_tier_assigned == ConfidenceTier.inspired
            ):
                raise ValueError(
                    "inspired is not a valid tier for confirmed annotation records"
                )
        return self


class ReviewDecisionsFile(BaseModel):
    """output/{tradition}/review-decisions.yaml"""

    tradition_id: str
    decisions: list[ReviewDecision] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Pipeline reports
# ---------------------------------------------------------------------------


class IngestionReport(BaseModel):
    _sisyphus_version: ClassVar[str] = "0.1"
    run_id: str
    source_file: str
    source_type: str
    word_count: int = 0
    page_count: int = 0
    ocr_applied: bool = False
    ocr_confidence_mean: float | None = None
    ocr_confidence_min: float | None = None
    flagged_pages: list[int] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)


class SegmentationReport(BaseModel):
    _sisyphus_version: ClassVar[str] = "0.1"
    run_id: str
    tradition_id: str
    segment_count: int = 0
    nas_proposed_count: int = 0
    nas_collision_count: int = 0
    methodology_fit_warnings: int = 0
    lacuna_count: int = 0
    errors: list[str] = Field(default_factory=list)


class AnnotationReport(BaseModel):
    _sisyphus_version: ClassVar[str] = "0.1"
    run_id: str
    tradition_id: str
    tracks: dict[str, int] = Field(default_factory=dict)  # track -> candidate count
    methodology_fit_warnings: int = 0
    errors: list[str] = Field(default_factory=list)


class PipelineError(BaseModel):
    phase: str
    run_id: str
    nas: NASAddress | None = None
    error_type: str
    message: str
    timestamp: datetime


class PipelineErrorsFile(BaseModel):
    """pipeline-reports/pipeline-errors.yaml"""

    errors: list[PipelineError] = Field(default_factory=list)


class ReviewQueueItem(BaseModel):
    nas: NASAddress
    record_type: Literal["summary", "annotation", "parallel"]
    track: AnnotationTrack | None = None
    locale: str | None = None
    priority: int = 0  # lower = higher priority


class ReviewQueueFile(BaseModel):
    """pipeline-reports/review-queue.yaml"""

    tradition_id: str
    items: list[ReviewQueueItem] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Embedding record
# ---------------------------------------------------------------------------


class EmbeddingRecord(BaseModel):
    """embeddings/{division}/{episode}.{locale}.{layer}[.{translation_id}].{model}.json"""

    nas: NASAddress
    locale: str
    layer: Layer
    translation_id: str | None = None
    model_version: str
    dimension: int
    vector: list[float]
    content_hash: str  # sha256 of the body text, for idempotency
