import enum
import uuid

from sqlalchemy import DateTime, Enum, Float, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSON, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, SCHEMA


class JobStatus(str, enum.Enum):
    uploading = "uploading"
    parsing_version_a = "parsing_version_a"
    parsing_version_b = "parsing_version_b"
    aligning = "aligning"
    diffing = "diffing"
    classifying = "classifying"
    assembling = "assembling"
    ready_for_review = "ready_for_review"
    verification_in_progress = "verification_in_progress"
    completed = "completed"
    failed = "failed"
    cancelled = "cancelled"


class ComparisonJob(Base):
    __tablename__ = "comparison_jobs"
    __table_args__ = {"schema": SCHEMA}

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    status: Mapped[JobStatus] = mapped_column(
        Enum(JobStatus, name="jobstatus", schema=SCHEMA),
        nullable=False,
        default=JobStatus.uploading,
    )
    model_provider: Mapped[str] = mapped_column(String(50), nullable=False)
    model_name: Mapped[str] = mapped_column(String(100), nullable=False)
    current_stage: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    stage_progress: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    total_differences: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    differences_verified: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    auto_confirm_threshold: Mapped[float] = mapped_column(Float, nullable=False, default=0.95)
    processing_time_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    token_usage: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    user_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    company_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    api_key_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    created_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # Relationships
    documents: Mapped[list["Document"]] = relationship(  # noqa: F821
        "Document", back_populates="job", cascade="all, delete-orphan"
    )
    differences: Mapped[list["DetectedDifference"]] = relationship(  # noqa: F821
        "DetectedDifference", back_populates="job", cascade="all, delete-orphan"
    )
    report: Mapped["DiffReport | None"] = relationship(  # noqa: F821
        "DiffReport", back_populates="job", uselist=False, cascade="all, delete-orphan"
    )
