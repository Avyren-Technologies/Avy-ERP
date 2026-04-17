from app.models.api_key import APIKey
from app.models.base import Base, SCHEMA
from app.models.correction import ReviewerCorrection
from app.models.difference import (
    DetectedDifference,
    DifferenceType,
    Significance,
    VerificationStatus,
)
from app.models.document import Document, DocumentPage, DocumentRole, PageProcessingStatus, PageType
from app.models.job import ComparisonJob, JobStatus
from app.models.report import DiffReport

__all__ = [
    # Base
    "Base",
    "SCHEMA",
    # Job
    "ComparisonJob",
    "JobStatus",
    # Document
    "Document",
    "DocumentPage",
    "DocumentRole",
    "PageType",
    "PageProcessingStatus",
    # Difference
    "DetectedDifference",
    "DifferenceType",
    "Significance",
    "VerificationStatus",
    # Report
    "DiffReport",
    # API Key
    "APIKey",
    # Correction
    "ReviewerCorrection",
]
