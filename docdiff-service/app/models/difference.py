import enum
import uuid

from sqlalchemy import Boolean, DateTime, Enum, Float, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSON, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, SCHEMA


class DifferenceType(str, enum.Enum):
    text_addition = "text_addition"
    text_deletion = "text_deletion"
    text_modification = "text_modification"
    table_cell_change = "table_cell_change"
    table_row_addition = "table_row_addition"
    table_row_deletion = "table_row_deletion"
    table_structure_change = "table_structure_change"
    annotation_present_in_b = "annotation_present_in_b"
    annotation_removed_from_b = "annotation_removed_from_b"
    section_moved = "section_moved"
    formatting_change = "formatting_change"


class Significance(str, enum.Enum):
    material = "material"
    substantive = "substantive"
    cosmetic = "cosmetic"
    uncertain = "uncertain"


class VerificationStatus(str, enum.Enum):
    pending = "pending"
    confirmed = "confirmed"
    dismissed = "dismissed"
    corrected = "corrected"
    flagged = "flagged"


class DetectedDifference(Base):
    __tablename__ = "detected_differences"
    __table_args__ = {"schema": SCHEMA}

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    job_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(f"{SCHEMA}.comparison_jobs.id", ondelete="CASCADE"),
        nullable=False,
    )
    difference_number: Mapped[int] = mapped_column(Integer, nullable=False)
    difference_type: Mapped[DifferenceType] = mapped_column(
        Enum(DifferenceType, name="differencetype", schema=SCHEMA),
        nullable=False,
    )
    significance: Mapped[Significance] = mapped_column(
        Enum(Significance, name="significance", schema=SCHEMA),
        nullable=False,
    )
    confidence: Mapped[float] = mapped_column(Float, nullable=False)
    page_version_a: Mapped[int | None] = mapped_column(Integer, nullable=True)
    page_version_b: Mapped[int | None] = mapped_column(Integer, nullable=True)
    bbox_version_a: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    bbox_version_b: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    value_before: Mapped[str | None] = mapped_column(Text, nullable=True)
    value_after: Mapped[str | None] = mapped_column(Text, nullable=True)
    context: Mapped[str | None] = mapped_column(Text, nullable=True)
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    block_id_version_a: Mapped[str | None] = mapped_column(String(100), nullable=True)
    block_id_version_b: Mapped[str | None] = mapped_column(String(100), nullable=True)
    verification_status: Mapped[VerificationStatus] = mapped_column(
        Enum(VerificationStatus, name="verificationstatus", schema=SCHEMA),
        nullable=False,
        default=VerificationStatus.pending,
    )
    auto_confirmed: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    needs_verification: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    verifier_comment: Mapped[str | None] = mapped_column(Text, nullable=True)
    corrected_description: Mapped[str | None] = mapped_column(Text, nullable=True)
    verified_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Relationships
    job: Mapped["ComparisonJob"] = relationship(  # noqa: F821
        "ComparisonJob", back_populates="differences"
    )
