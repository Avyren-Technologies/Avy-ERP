import uuid

from sqlalchemy import Boolean, DateTime, ForeignKey, String, Text, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import JSON, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, SCHEMA


class DiffReport(Base):
    __tablename__ = "diff_reports"
    __table_args__ = (
        UniqueConstraint("job_id", name="uq_diff_reports_job_id"),
        {"schema": SCHEMA},
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    job_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(f"{SCHEMA}.comparison_jobs.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )
    summary_stats: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    report_html: Mapped[str | None] = mapped_column(Text, nullable=True)
    report_pdf_path: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    is_partial: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    generated_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Relationships
    job: Mapped["ComparisonJob"] = relationship(  # noqa: F821
        "ComparisonJob", back_populates="report"
    )
