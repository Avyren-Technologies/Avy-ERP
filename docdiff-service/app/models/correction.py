import uuid
from datetime import datetime

from sqlalchemy import DateTime, Float, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import SCHEMA, Base


class ReviewerCorrection(Base):
    """Stores reviewer corrections for classification learning.

    When a reviewer changes the significance of a difference (e.g., Material -> Cosmetic),
    that correction is stored here. The system uses recent corrections as few-shot
    examples in AI classification prompts, improving accuracy over time.
    """
    __tablename__ = "reviewer_corrections"
    __table_args__ = {"schema": SCHEMA}

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    value_before: Mapped[str] = mapped_column(Text, default="")
    value_after: Mapped[str] = mapped_column(Text, default="")
    difference_type: Mapped[str] = mapped_column(String(100))
    original_significance: Mapped[str] = mapped_column(String(50))
    corrected_significance: Mapped[str] = mapped_column(String(50))
    verifier_comment: Mapped[str | None] = mapped_column(Text, nullable=True)
    context: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
