import uuid
from datetime import datetime

from pydantic import BaseModel

from app.models.difference import DifferenceType, Significance, VerificationStatus


class DifferenceResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    job_id: uuid.UUID
    difference_number: int
    difference_type: DifferenceType
    significance: Significance
    confidence: float
    page_version_a: int | None
    page_version_b: int | None
    bbox_version_a: dict | None
    bbox_version_b: dict | None
    value_before: str | None
    value_after: str | None
    context: str | None
    summary: str
    verification_status: VerificationStatus
    auto_confirmed: bool
    needs_verification: bool
    verifier_comment: str | None
    corrected_description: str | None
    verified_at: datetime | None


class VerificationAction(BaseModel):
    action: VerificationStatus
    comment: str | None = None
    corrected_description: str | None = None
    corrected_significance: Significance | None = None
    corrected_value_after: str | None = None


class BulkVerificationAction(BaseModel):
    difference_ids: list[uuid.UUID]
    action: VerificationStatus
    comment: str | None = None


class ManualDifferenceCreate(BaseModel):
    difference_type: DifferenceType
    significance: Significance
    page_version_a: int | None = None
    page_version_b: int | None = None
    value_before: str | None = None
    value_after: str | None = None
    summary: str
