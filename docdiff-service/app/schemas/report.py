import uuid
from datetime import datetime

from pydantic import BaseModel


class ReportResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    job_id: uuid.UUID
    summary_stats: dict | None
    report_html: str | None
    report_pdf_path: str | None
    is_partial: bool
    generated_at: datetime
