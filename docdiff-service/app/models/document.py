import enum
import uuid

from sqlalchemy import Boolean, DateTime, Enum, Float, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSON, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, SCHEMA


class DocumentRole(str, enum.Enum):
    version_a = "version_a"
    version_b = "version_b"


class PageType(str, enum.Enum):
    born_digital = "born_digital"
    scanned = "scanned"
    mixed = "mixed"


class PageProcessingStatus(str, enum.Enum):
    pending = "pending"
    completed = "completed"
    failed = "failed"


class Document(Base):
    __tablename__ = "documents"
    __table_args__ = {"schema": SCHEMA}

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    job_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(f"{SCHEMA}.comparison_jobs.id", ondelete="CASCADE"),
        nullable=False,
    )
    role: Mapped[DocumentRole] = mapped_column(
        Enum(DocumentRole, name="documentrole", schema=SCHEMA),
        nullable=False,
    )
    label: Mapped[str] = mapped_column(String(500), nullable=False, default="")
    filename: Mapped[str] = mapped_column(String(500), nullable=False)
    file_path: Mapped[str] = mapped_column(String(1000), nullable=False)
    file_size_bytes: Mapped[int] = mapped_column(Integer, nullable=False)
    page_count: Mapped[int] = mapped_column(Integer, nullable=False)
    pdf_metadata: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Relationships
    job: Mapped["ComparisonJob"] = relationship(  # noqa: F821
        "ComparisonJob", back_populates="documents"
    )
    pages: Mapped[list["DocumentPage"]] = relationship(
        "DocumentPage", back_populates="document", cascade="all, delete-orphan"
    )


class DocumentPage(Base):
    __tablename__ = "document_pages"
    __table_args__ = {"schema": SCHEMA}

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    document_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(f"{SCHEMA}.documents.id", ondelete="CASCADE"),
        nullable=False,
    )
    page_number: Mapped[int] = mapped_column(Integer, nullable=False)
    page_type: Mapped[PageType] = mapped_column(
        Enum(PageType, name="pagetype", schema=SCHEMA),
        nullable=False,
    )
    has_handwriting: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    has_annotations: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    content: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    extraction_method: Mapped[str | None] = mapped_column(String(50), nullable=True)
    extraction_confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    image_path: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    processing_status: Mapped[PageProcessingStatus] = mapped_column(
        Enum(PageProcessingStatus, name="pageprocessingstatus", schema=SCHEMA),
        nullable=False,
        default=PageProcessingStatus.pending,
    )
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Relationships
    document: Mapped["Document"] = relationship("Document", back_populates="pages")
