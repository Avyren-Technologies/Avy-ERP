import uuid
from datetime import datetime

from pydantic import BaseModel

from app.models.document import DocumentRole
from app.models.job import JobStatus


class JobCreate(BaseModel):
    model_provider: str
    model_name: str
    label_a: str = "Version A"
    label_b: str = "Version B"
    auto_confirm_threshold: float = 0.95


class JobResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    status: JobStatus
    model_provider: str
    model_name: str
    current_stage: int
    stage_progress: dict | None
    error_message: str | None
    total_differences: int
    differences_verified: int
    auto_confirm_threshold: float
    processing_time_ms: int | None
    token_usage: dict | None
    user_id: str | None
    company_id: str | None
    created_at: datetime
    updated_at: datetime


class JobListResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    status: JobStatus
    model_provider: str
    model_name: str
    label_a: str | None
    label_b: str | None
    total_differences: int
    differences_verified: int
    material_count: int | None
    processing_time_ms: int | None
    created_at: datetime
