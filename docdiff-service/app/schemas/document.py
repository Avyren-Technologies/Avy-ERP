import uuid
from datetime import datetime

from pydantic import BaseModel

from app.models.document import DocumentRole, PageProcessingStatus, PageType


class DocumentResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    job_id: uuid.UUID
    role: DocumentRole
    label: str
    filename: str
    file_size_bytes: int
    page_count: int
    pdf_metadata: dict | None
    created_at: datetime


class PageContentResponse(BaseModel):
    model_config = {"from_attributes": True}

    page_number: int
    page_type: PageType
    has_handwriting: bool
    has_annotations: bool
    content: dict | None
    extraction_confidence: float | None
    processing_status: PageProcessingStatus
