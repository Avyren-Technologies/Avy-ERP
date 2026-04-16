from app.schemas.common import BBox, ErrorResponse, PaginatedResponse, SuccessResponse
from app.schemas.difference import (
    BulkVerificationAction,
    DifferenceResponse,
    ManualDifferenceCreate,
    VerificationAction,
)
from app.schemas.document import DocumentResponse, PageContentResponse
from app.schemas.job import JobCreate, JobListResponse, JobResponse
from app.schemas.report import ReportResponse

__all__ = [
    # Common
    "SuccessResponse",
    "PaginatedResponse",
    "ErrorResponse",
    "BBox",
    # Job
    "JobCreate",
    "JobResponse",
    "JobListResponse",
    # Document
    "DocumentResponse",
    "PageContentResponse",
    # Difference
    "DifferenceResponse",
    "VerificationAction",
    "BulkVerificationAction",
    "ManualDifferenceCreate",
    # Report
    "ReportResponse",
]
