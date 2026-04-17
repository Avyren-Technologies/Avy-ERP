# DocDiff Pro Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build an AI-powered document comparison microservice (Python/FastAPI) with a React frontend module embedded in the existing ERP web app.

**Architecture:** Standalone FastAPI service (`docdiff-service/`) at port 8000, sharing PostgreSQL (separate `docdiff` schema) and Redis with the existing Node.js backend. Frontend module in `web-system-app/src/features/docdiff/`. SSE for real-time progress. Dual auth (JWT + API key).

**Tech Stack:** Python 3.11+, FastAPI, SQLAlchemy async, Alembic, ARQ, Docling, PyMuPDF, diff-match-patch, WeasyPrint, tenacity, httpx, anthropic SDK, google-genai SDK. Frontend: React, TypeScript, TailwindCSS, React Query, pdfjs-dist.

**Spec:** `docs/superpowers/specs/2026-04-16-docdiff-pro-design.md`
**PRD:** `docs/DocDiff-Pro-PRD-Prototype-v0.1.md`

---

## File Map

### New: `docdiff-service/` (top-level directory)

| File | Responsibility |
|---|---|
| `pyproject.toml` | Project metadata, dependencies |
| `requirements.txt` | Pinned production deps |
| `requirements-dev.txt` | Test/lint deps |
| `.env.example` | All env vars documented |
| `Dockerfile` | Multi-stage Python build |
| `docker-compose.yml` | Dev: service + deps |
| `alembic.ini` | Alembic config |
| `alembic/env.py` | Migration environment |
| `app/__init__.py` | Package init |
| `app/main.py` | FastAPI app, CORS, lifespan, router mount |
| `app/config.py` | Pydantic BaseSettings |
| `app/database.py` | SQLAlchemy async engine + session factory |
| `app/models/__init__.py` | Model exports |
| `app/models/base.py` | Declarative base with docdiff schema |
| `app/models/job.py` | ComparisonJob ORM model |
| `app/models/document.py` | Document, DocumentPage ORM models |
| `app/models/change.py` | DetectedChange ORM model |
| `app/models/report.py` | DiffReport ORM model |
| `app/models/api_key.py` | APIKey ORM model |
| `app/schemas/__init__.py` | Schema exports |
| `app/schemas/job.py` | Job request/response schemas |
| `app/schemas/document.py` | Document schemas |
| `app/schemas/change.py` | Change + review action schemas |
| `app/schemas/report.py` | Report schemas |
| `app/schemas/common.py` | Shared schemas (pagination, envelope) |
| `app/api/__init__.py` | Package init |
| `app/api/router.py` | Main router aggregator |
| `app/api/health.py` | GET /health endpoint |
| `app/api/jobs.py` | Job CRUD + start processing |
| `app/api/sse.py` | SSE progress endpoint |
| `app/api/changes.py` | Change list + review actions |
| `app/api/documents.py` | Page images + content |
| `app/api/reports.py` | Report generation + PDF export |
| `app/api/api_keys.py` | API key management |
| `app/api/deps.py` | Shared dependencies (db session, auth, etc.) |
| `app/auth/__init__.py` | Package init |
| `app/auth/middleware.py` | Auth dependency: JWT or API key |
| `app/auth/jwt_validator.py` | JWT decode + verify |
| `app/auth/api_key.py` | API key hash + lookup |
| `app/ai/__init__.py` | Package init |
| `app/ai/base.py` | Abstract AIProvider with tenacity retry |
| `app/ai/anthropic_provider.py` | Claude provider |
| `app/ai/google_provider.py` | Gemini provider |
| `app/ai/openrouter_provider.py` | OpenRouter provider |
| `app/ai/qwen_local_provider.py` | Qwen3-VL local provider |
| `app/ai/router.py` | Model selection by job config |
| `app/ai/response_parser.py` | JSON extraction, validation, fallback |
| `app/prompts/__init__.py` | Package init |
| `app/prompts/extract_page.py` | Page extraction prompt templates |
| `app/prompts/classify_change.py` | Change classification prompts |
| `app/prompts/transcribe_handwriting.py` | Handwriting transcription prompts |
| `app/pipeline/__init__.py` | Package init |
| `app/pipeline/orchestrator.py` | Job orchestration, stage sequencing |
| `app/pipeline/stage_1_ingestion.py` | Validate PDF, extract metadata |
| `app/pipeline/stage_2_classification.py` | Page type detection |
| `app/pipeline/stage_3_extraction.py` | Docling + VLM extraction |
| `app/pipeline/stage_4_normalization.py` | Canonical format + IDs |
| `app/pipeline/stage_5_alignment.py` | Section/table/paragraph matching |
| `app/pipeline/stage_6_diff.py` | diff-match-patch word + cell diffs |
| `app/pipeline/stage_7_scoring.py` | Confidence + significance |
| `app/pipeline/stage_8_assembly.py` | Result compilation |
| `app/pdf/__init__.py` | Package init |
| `app/pdf/metadata.py` | PyMuPDF metadata extraction |
| `app/pdf/renderer.py` | Page-to-image at 250 DPI |
| `app/pdf/parser.py` | Docling structural parsing |
| `app/pdf/report_generator.py` | WeasyPrint HTML→PDF |
| `app/workers/__init__.py` | Package init |
| `app/workers/job_worker.py` | ARQ worker: Redis queue consumer |
| `app/utils/__init__.py` | Package init |
| `app/utils/diff_utils.py` | diff-match-patch wrapper |
| `app/utils/table_utils.py` | Table structure comparison |
| `app/utils/bbox.py` | Bounding box utilities |
| `tests/conftest.py` | Fixtures: test DB, test client, mock AI |
| `tests/test_api/` | API endpoint tests |
| `tests/test_pipeline/` | Pipeline stage tests |
| `tests/test_ai/` | AI provider tests |

### Modified: `web-system-app/src/`

| File | Responsibility |
|---|---|
| `features/docdiff/api/docdiff-client.ts` | Separate axios instance → FastAPI |
| `features/docdiff/api/docdiff-api.ts` | API function wrappers |
| `features/docdiff/api/use-docdiff-queries.ts` | Query key factory + hooks |
| `features/docdiff/api/use-docdiff-mutations.ts` | Mutations (upload, review, report) |
| `features/docdiff/types/docdiff.types.ts` | All TypeScript interfaces |
| `features/docdiff/components/UploadView.tsx` | Drag-drop + model selector |
| `features/docdiff/components/ProcessingView.tsx` | 8-stage progress (SSE) |
| `features/docdiff/components/ReviewInterface.tsx` | Three-panel layout |
| `features/docdiff/components/DocumentViewer.tsx` | PDF page image + overlays |
| `features/docdiff/components/ChangeList.tsx` | Filterable change list |
| `features/docdiff/components/ChangeDetail.tsx` | Single change + actions |
| `features/docdiff/components/HandwritingReview.tsx` | Image + transcription |
| `features/docdiff/components/UnresolvedRegion.tsx` | Side-by-side zoom |
| `features/docdiff/components/ReportView.tsx` | Summary report + download |
| `features/docdiff/components/ModelSelector.tsx` | AI model dropdown |
| `features/docdiff/components/KeyboardShortcutsHelp.tsx` | "?" overlay |
| `features/docdiff/hooks/useProcessingSSE.ts` | EventSource hook |
| `features/docdiff/hooks/useChangeNavigation.ts` | J/K keyboard nav |
| `features/docdiff/hooks/useSyncScroll.ts` | Synchronized scrolling |
| `features/docdiff/utils/significance-colors.ts` | Color mapping |
| `features/docdiff/utils/change-filters.ts` | Filter/sort logic |
| `features/docdiff/DocDiffScreen.tsx` | Main screen with view routing |
| `features/docdiff/index.ts` | Public exports |
| `App.tsx` | Add DocDiff route |

---

## Task 1: Project Scaffold + Configuration

**Files:**
- Create: `docdiff-service/pyproject.toml`
- Create: `docdiff-service/requirements.txt`
- Create: `docdiff-service/requirements-dev.txt`
- Create: `docdiff-service/.env.example`
- Create: `docdiff-service/.gitignore`
- Create: `docdiff-service/app/__init__.py`
- Create: `docdiff-service/app/config.py`
- Create: `docdiff-service/app/main.py`

- [ ] **Step 1: Create project directory and pyproject.toml**

```bash
mkdir -p docdiff-service/app
```

```toml
# docdiff-service/pyproject.toml
[project]
name = "docdiff-service"
version = "0.1.0"
description = "DocDiff Pro - AI-powered document comparison service"
requires-python = ">=3.11"

[tool.ruff]
target-version = "py311"
line-length = 100

[tool.ruff.lint]
select = ["E", "F", "I", "N", "W", "UP"]

[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]
```

- [ ] **Step 2: Create requirements.txt**

```txt
# docdiff-service/requirements.txt
fastapi>=0.115.0
uvicorn[standard]>=0.34.0
sqlalchemy[asyncio]>=2.0.36
asyncpg>=0.30.0
alembic>=1.14.0
pydantic>=2.10.0
pydantic-settings>=2.7.0
redis>=5.2.0
arq>=0.26.1
httpx>=0.28.0
anthropic>=0.52.0
google-genai>=1.14.0
PyMuPDF>=1.25.0
docling>=2.25.0
diff-match-patch>=20241021
weasyprint>=63.0
Pillow>=11.1.0
python-jose[cryptography]>=3.3.0
python-multipart>=0.0.18
tenacity>=9.0.0
```

- [ ] **Step 3: Create requirements-dev.txt**

```txt
# docdiff-service/requirements-dev.txt
-r requirements.txt
pytest>=8.3.0
pytest-asyncio>=0.25.0
ruff>=0.9.0
mypy>=1.14.0
```

- [ ] **Step 4: Create .env.example**

```env
# docdiff-service/.env.example

# === Service ===
DOCDIFF_HOST=0.0.0.0
DOCDIFF_PORT=8000
DOCDIFF_ENV=development
DOCDIFF_LOG_LEVEL=INFO
DOCDIFF_CORS_ORIGINS=http://localhost:5173,http://localhost:3000

# === Database ===
DOCDIFF_DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/avy_erp
DOCDIFF_DATABASE_SCHEMA=docdiff

# === Redis ===
DOCDIFF_REDIS_URL=redis://localhost:6379/2

# === Auth ===
JWT_SECRET=your-jwt-secret-must-match-erp-backend

# === Storage ===
DOCDIFF_STORAGE_PATH=./storage

# === AI Providers ===
ANTHROPIC_API_KEY=sk-ant-xxxx
GOOGLE_API_KEY=AIxxxx
OPENROUTER_API_KEY=sk-or-xxxx
QWEN_LOCAL_ENDPOINT=http://localhost:8080/v1

# === AI Defaults ===
DOCDIFF_DEFAULT_PROVIDER=anthropic
DOCDIFF_DEFAULT_MODEL=claude-sonnet-4-6
DOCDIFF_CONFIDENCE_THRESHOLD=0.75
DOCDIFF_PAGE_RENDER_DPI=250

# === Processing ===
DOCDIFF_MAX_PAGES=10
DOCDIFF_MAX_FILE_SIZE_MB=50
DOCDIFF_MAX_RETRIES=3
DOCDIFF_RETRY_BACKOFF_BASE=1
```

- [ ] **Step 5: Create .gitignore**

```gitignore
# docdiff-service/.gitignore
__pycache__/
*.py[cod]
*.egg-info/
dist/
.eggs/
.venv/
venv/
.env
storage/uploads/*
storage/reports/*
!storage/uploads/.gitkeep
!storage/reports/.gitkeep
.mypy_cache/
.ruff_cache/
.pytest_cache/
```

- [ ] **Step 6: Create app/config.py**

```python
# docdiff-service/app/config.py
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Service
    host: str = "0.0.0.0"
    port: int = 8000
    env: str = "development"
    log_level: str = "INFO"
    cors_origins: str = "http://localhost:5173,http://localhost:3000"

    # Database
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/avy_erp"
    database_schema: str = "docdiff"

    # Redis
    redis_url: str = "redis://localhost:6379/2"

    # Auth
    jwt_secret: str = ""

    # Storage
    storage_path: str = "./storage"

    # AI Providers
    anthropic_api_key: str = ""
    google_api_key: str = ""
    openrouter_api_key: str = ""
    qwen_local_endpoint: str = "http://localhost:8080/v1"

    # AI Defaults
    default_provider: str = "anthropic"
    default_model: str = "claude-sonnet-4-6"
    confidence_threshold: float = 0.75
    page_render_dpi: int = 250

    # Processing
    max_pages: int = 10
    max_file_size_mb: int = 50
    max_retries: int = 3
    retry_backoff_base: int = 1

    model_config = {
        "env_prefix": "DOCDIFF_",
        "env_file": ".env",
        "extra": "ignore",
    }


# Override env_prefix for shared vars
class JWTSettings(BaseSettings):
    jwt_secret: str = ""

    model_config = {
        "env_file": ".env",
        "extra": "ignore",
    }


class AIKeySettings(BaseSettings):
    anthropic_api_key: str = ""
    google_api_key: str = ""
    openrouter_api_key: str = ""

    model_config = {
        "env_file": ".env",
        "extra": "ignore",
    }


def get_settings() -> Settings:
    base = Settings()
    jwt = JWTSettings()
    ai = AIKeySettings()
    # Merge JWT and AI keys that don't have DOCDIFF_ prefix
    if not base.jwt_secret and jwt.jwt_secret:
        base.jwt_secret = jwt.jwt_secret
    if not base.anthropic_api_key and ai.anthropic_api_key:
        base.anthropic_api_key = ai.anthropic_api_key
    if not base.google_api_key and ai.google_api_key:
        base.google_api_key = ai.google_api_key
    if not base.openrouter_api_key and ai.openrouter_api_key:
        base.openrouter_api_key = ai.openrouter_api_key
    return base


settings = get_settings()
```

- [ ] **Step 7: Create app/__init__.py**

```python
# docdiff-service/app/__init__.py
```

- [ ] **Step 8: Create app/main.py**

```python
# docdiff-service/app/main.py
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings

logger = logging.getLogger("docdiff")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logging.basicConfig(level=getattr(logging, settings.log_level))
    logger.info("DocDiff Pro starting up...")

    # Create storage directories
    import os
    os.makedirs(f"{settings.storage_path}/uploads", exist_ok=True)
    os.makedirs(f"{settings.storage_path}/reports", exist_ok=True)

    yield

    # Shutdown
    logger.info("DocDiff Pro shutting down...")


app = FastAPI(
    title="DocDiff Pro",
    description="AI-powered document comparison service",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS
origins = [o.strip() for o in settings.cors_origins.split(",")]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health_check():
    return {"status": "ok", "service": "docdiff-pro", "version": "0.1.0"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host=settings.host, port=settings.port, reload=True)
```

- [ ] **Step 9: Create storage directories**

```bash
mkdir -p docdiff-service/storage/uploads docdiff-service/storage/reports
touch docdiff-service/storage/uploads/.gitkeep docdiff-service/storage/reports/.gitkeep
```

- [ ] **Step 10: Set up Python venv and install deps**

```bash
cd docdiff-service
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

- [ ] **Step 11: Verify FastAPI starts**

```bash
cd docdiff-service
source .venv/bin/activate
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload &
sleep 2
curl http://localhost:8000/health
# Expected: {"status":"ok","service":"docdiff-pro","version":"0.1.0"}
kill %1
```

- [ ] **Step 12: Commit**

```bash
git add docdiff-service/
git commit -m "feat(docdiff): scaffold FastAPI project with config and health check"
```

---

## Task 2: Database Models + Migrations

**Files:**
- Create: `docdiff-service/app/database.py`
- Create: `docdiff-service/app/models/base.py`
- Create: `docdiff-service/app/models/__init__.py`
- Create: `docdiff-service/app/models/job.py`
- Create: `docdiff-service/app/models/document.py`
- Create: `docdiff-service/app/models/change.py`
- Create: `docdiff-service/app/models/report.py`
- Create: `docdiff-service/app/models/api_key.py`
- Create: `docdiff-service/alembic.ini`
- Create: `docdiff-service/alembic/env.py`
- Modify: `docdiff-service/app/main.py` (add DB init to lifespan)

- [ ] **Step 1: Create app/database.py**

```python
# docdiff-service/app/database.py
from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.config import settings

engine = create_async_engine(
    settings.database_url,
    echo=settings.env == "development",
    pool_size=5,
    max_overflow=10,
)

async_session_factory = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
```

- [ ] **Step 2: Create app/models/base.py**

```python
# docdiff-service/app/models/base.py
from sqlalchemy.orm import DeclarativeBase, MappedAsDataclass

from app.config import settings

SCHEMA = settings.database_schema


class Base(DeclarativeBase):
    __table_args__ = {"schema": SCHEMA}
```

- [ ] **Step 3: Create app/models/job.py**

```python
# docdiff-service/app/models/job.py
import enum
import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, Float, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSON, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import SCHEMA, Base


class JobStatus(str, enum.Enum):
    UPLOADING = "uploading"
    PARSING_ORIGINAL = "parsing_original"
    PARSING_REVISED = "parsing_revised"
    ALIGNING = "aligning"
    DIFFING = "diffing"
    CLASSIFYING = "classifying"
    ASSEMBLING = "assembling"
    READY_FOR_REVIEW = "ready_for_review"
    REVIEW_IN_PROGRESS = "review_in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ComparisonJob(Base):
    __tablename__ = "comparison_jobs"
    __table_args__ = {"schema": SCHEMA}

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    status: Mapped[str] = mapped_column(
        Enum(JobStatus, schema=SCHEMA, name="job_status_enum"),
        default=JobStatus.UPLOADING,
    )
    model_provider: Mapped[str] = mapped_column(String(50))
    model_name: Mapped[str] = mapped_column(String(100))
    current_stage: Mapped[int] = mapped_column(Integer, default=0)
    stage_progress: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    total_changes: Mapped[int] = mapped_column(Integer, default=0)
    changes_reviewed: Mapped[int] = mapped_column(Integer, default=0)
    processing_time_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    token_usage: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    user_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    company_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    api_key_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    documents = relationship("Document", back_populates="job", cascade="all, delete-orphan")
    changes = relationship("DetectedChange", back_populates="job", cascade="all, delete-orphan")
    report = relationship("DiffReport", back_populates="job", uselist=False, cascade="all, delete-orphan")
```

- [ ] **Step 4: Create app/models/document.py**

```python
# docdiff-service/app/models/document.py
import enum
import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Enum, Float, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSON, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import SCHEMA, Base


class DocumentRole(str, enum.Enum):
    ORIGINAL = "original"
    REVISED = "revised"


class PageType(str, enum.Enum):
    BORN_DIGITAL = "born_digital"
    SCANNED = "scanned"
    MIXED = "mixed"


class PageProcessingStatus(str, enum.Enum):
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"


class Document(Base):
    __tablename__ = "documents"
    __table_args__ = {"schema": SCHEMA}

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    job_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey(f"{SCHEMA}.comparison_jobs.id", ondelete="CASCADE")
    )
    role: Mapped[str] = mapped_column(Enum(DocumentRole, schema=SCHEMA, name="document_role_enum"))
    filename: Mapped[str] = mapped_column(String(500))
    file_path: Mapped[str] = mapped_column(String(1000))
    file_size_bytes: Mapped[int] = mapped_column(Integer)
    page_count: Mapped[int] = mapped_column(Integer)
    pdf_metadata: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    job = relationship("ComparisonJob", back_populates="documents")
    pages = relationship("DocumentPage", back_populates="document", cascade="all, delete-orphan")


class DocumentPage(Base):
    __tablename__ = "document_pages"
    __table_args__ = {"schema": SCHEMA}

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    document_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey(f"{SCHEMA}.documents.id", ondelete="CASCADE")
    )
    page_number: Mapped[int] = mapped_column(Integer)
    page_type: Mapped[str] = mapped_column(
        Enum(PageType, schema=SCHEMA, name="page_type_enum"), default=PageType.BORN_DIGITAL
    )
    has_handwriting: Mapped[bool] = mapped_column(Boolean, default=False)
    has_annotations: Mapped[bool] = mapped_column(Boolean, default=False)
    content: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    extraction_method: Mapped[str | None] = mapped_column(String(50), nullable=True)
    extraction_confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    image_path: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    processing_status: Mapped[str] = mapped_column(
        Enum(PageProcessingStatus, schema=SCHEMA, name="page_processing_status_enum"),
        default=PageProcessingStatus.PENDING,
    )
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    document = relationship("Document", back_populates="pages")
```

- [ ] **Step 5: Create app/models/change.py**

```python
# docdiff-service/app/models/change.py
import enum
import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Enum, Float, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSON, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import SCHEMA, Base


class ChangeType(str, enum.Enum):
    TEXT_ADDITION = "text_addition"
    TEXT_DELETION = "text_deletion"
    TEXT_MODIFICATION = "text_modification"
    TABLE_CELL_CHANGE = "table_cell_change"
    TABLE_ROW_ADDITION = "table_row_addition"
    TABLE_ROW_DELETION = "table_row_deletion"
    TABLE_STRUCTURE_CHANGE = "table_structure_change"
    ANNOTATION_ADDED = "annotation_added"
    ANNOTATION_REMOVED = "annotation_removed"
    SECTION_MOVED = "section_moved"
    FORMATTING_CHANGE = "formatting_change"


class Significance(str, enum.Enum):
    MATERIAL = "material"
    SUBSTANTIVE = "substantive"
    COSMETIC = "cosmetic"
    UNCERTAIN = "uncertain"


class ReviewStatus(str, enum.Enum):
    PENDING = "pending"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    ESCALATED = "escalated"


class DetectedChange(Base):
    __tablename__ = "detected_changes"
    __table_args__ = {"schema": SCHEMA}

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    job_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey(f"{SCHEMA}.comparison_jobs.id", ondelete="CASCADE")
    )
    change_number: Mapped[int] = mapped_column(Integer)
    change_type: Mapped[str] = mapped_column(
        Enum(ChangeType, schema=SCHEMA, name="change_type_enum")
    )
    significance: Mapped[str] = mapped_column(
        Enum(Significance, schema=SCHEMA, name="significance_enum")
    )
    confidence: Mapped[float] = mapped_column(Float)
    page_original: Mapped[int | None] = mapped_column(Integer, nullable=True)
    page_revised: Mapped[int | None] = mapped_column(Integer, nullable=True)
    bbox_original: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    bbox_revised: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    value_before: Mapped[str | None] = mapped_column(Text, nullable=True)
    value_after: Mapped[str | None] = mapped_column(Text, nullable=True)
    context: Mapped[str | None] = mapped_column(Text, nullable=True)
    summary: Mapped[str] = mapped_column(Text)
    block_id_original: Mapped[str | None] = mapped_column(String(100), nullable=True)
    block_id_revised: Mapped[str | None] = mapped_column(String(100), nullable=True)
    review_status: Mapped[str] = mapped_column(
        Enum(ReviewStatus, schema=SCHEMA, name="review_status_enum"),
        default=ReviewStatus.PENDING,
    )
    auto_accepted: Mapped[bool] = mapped_column(Boolean, default=False)
    needs_human_review: Mapped[bool] = mapped_column(Boolean, default=False)
    reviewer_comment: Mapped[str | None] = mapped_column(Text, nullable=True)
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    job = relationship("ComparisonJob", back_populates="changes")
```

- [ ] **Step 6: Create app/models/report.py**

```python
# docdiff-service/app/models/report.py
import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import JSON, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import SCHEMA, Base


class DiffReport(Base):
    __tablename__ = "diff_reports"
    __table_args__ = {"schema": SCHEMA}

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    job_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey(f"{SCHEMA}.comparison_jobs.id", ondelete="CASCADE"), unique=True
    )
    summary_stats: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    report_html: Mapped[str | None] = mapped_column(Text, nullable=True)
    report_pdf_path: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    generated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    job = relationship("ComparisonJob", back_populates="report")
```

- [ ] **Step 7: Create app/models/api_key.py**

```python
# docdiff-service/app/models/api_key.py
import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import SCHEMA, Base


class APIKey(Base):
    __tablename__ = "api_keys"
    __table_args__ = {"schema": SCHEMA}

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    key_hash: Mapped[str] = mapped_column(String(64), unique=True)
    name: Mapped[str] = mapped_column(String(255))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    last_used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
```

- [ ] **Step 8: Create app/models/__init__.py**

```python
# docdiff-service/app/models/__init__.py
from app.models.api_key import APIKey
from app.models.base import Base
from app.models.change import ChangeType, DetectedChange, ReviewStatus, Significance
from app.models.document import Document, DocumentPage, DocumentRole, PageProcessingStatus, PageType
from app.models.job import ComparisonJob, JobStatus
from app.models.report import DiffReport

__all__ = [
    "Base",
    "ComparisonJob",
    "JobStatus",
    "Document",
    "DocumentPage",
    "DocumentRole",
    "PageType",
    "PageProcessingStatus",
    "DetectedChange",
    "ChangeType",
    "Significance",
    "ReviewStatus",
    "DiffReport",
    "APIKey",
]
```

- [ ] **Step 9: Set up Alembic**

```bash
cd docdiff-service
source .venv/bin/activate
alembic init alembic
```

Then replace `alembic/env.py`:

```python
# docdiff-service/alembic/env.py
import asyncio
from logging.config import fileConfig

from sqlalchemy import pool, text
from sqlalchemy.ext.asyncio import create_async_engine

from alembic import context
from app.config import settings
from app.models import Base

config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata
SCHEMA = settings.database_schema


def run_migrations_offline() -> None:
    url = settings.database_url
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        version_table_schema=SCHEMA,
        include_schemas=True,
    )
    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection) -> None:
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        version_table_schema=SCHEMA,
        include_schemas=True,
    )
    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    connectable = create_async_engine(settings.database_url, poolclass=pool.NullPool)
    async with connectable.connect() as connection:
        await connection.execute(text(f"CREATE SCHEMA IF NOT EXISTS {SCHEMA}"))
        await connection.commit()
        await connection.run_sync(do_run_migrations)
    await connectable.dispose()


def run_migrations_online() -> None:
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
```

Update `alembic.ini` — set `sqlalchemy.url` to empty (we use config.py):

Find the line `sqlalchemy.url = driver://user:pass@localhost/dbname` in `alembic.ini` and replace with:
```ini
sqlalchemy.url =
```

- [ ] **Step 10: Generate initial migration**

```bash
cd docdiff-service
source .venv/bin/activate
alembic revision --autogenerate -m "initial docdiff schema"
```

- [ ] **Step 11: Run migration**

```bash
cd docdiff-service
source .venv/bin/activate
alembic upgrade head
```

- [ ] **Step 12: Update main.py lifespan to verify DB on startup**

Add to `app/main.py` lifespan, after storage dir creation:

```python
    # Verify database connection
    from app.database import engine
    from sqlalchemy import text
    async with engine.begin() as conn:
        await conn.execute(text("SELECT 1"))
    logger.info("Database connection verified")
```

- [ ] **Step 13: Commit**

```bash
git add docdiff-service/
git commit -m "feat(docdiff): add SQLAlchemy models and Alembic migrations"
```

---

## Task 3: Pydantic Schemas + API Dependencies

**Files:**
- Create: `docdiff-service/app/schemas/common.py`
- Create: `docdiff-service/app/schemas/job.py`
- Create: `docdiff-service/app/schemas/document.py`
- Create: `docdiff-service/app/schemas/change.py`
- Create: `docdiff-service/app/schemas/report.py`
- Create: `docdiff-service/app/schemas/__init__.py`
- Create: `docdiff-service/app/api/deps.py`

- [ ] **Step 1: Create app/schemas/common.py**

```python
# docdiff-service/app/schemas/common.py
from typing import Any, Generic, TypeVar

from pydantic import BaseModel

T = TypeVar("T")


class SuccessResponse(BaseModel, Generic[T]):
    success: bool = True
    data: T
    message: str | None = None


class PaginatedResponse(BaseModel, Generic[T]):
    success: bool = True
    data: list[T]
    meta: dict[str, int]


class ErrorResponse(BaseModel):
    success: bool = False
    error: str
    detail: str | None = None


class BBox(BaseModel):
    x: float
    y: float
    width: float
    height: float
    page: int
```

- [ ] **Step 2: Create app/schemas/job.py**

```python
# docdiff-service/app/schemas/job.py
import uuid
from datetime import datetime

from pydantic import BaseModel, Field

from app.models.job import JobStatus


class JobCreate(BaseModel):
    model_provider: str = Field(description="AI provider: anthropic, google, openrouter, qwen_local")
    model_name: str = Field(description="Model name: claude-sonnet-4-6, gemini-3.1-pro, etc.")


class JobResponse(BaseModel):
    id: uuid.UUID
    status: JobStatus
    model_provider: str
    model_name: str
    current_stage: int
    stage_progress: dict | None = None
    error_message: str | None = None
    total_changes: int
    changes_reviewed: int
    processing_time_ms: int | None = None
    token_usage: dict | None = None
    user_id: str | None = None
    company_id: str | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class JobListResponse(BaseModel):
    id: uuid.UUID
    status: JobStatus
    model_provider: str
    model_name: str
    total_changes: int
    changes_reviewed: int
    processing_time_ms: int | None = None
    created_at: datetime

    model_config = {"from_attributes": True}
```

- [ ] **Step 3: Create app/schemas/document.py**

```python
# docdiff-service/app/schemas/document.py
import uuid
from datetime import datetime

from pydantic import BaseModel

from app.models.document import DocumentRole, PageType


class DocumentResponse(BaseModel):
    id: uuid.UUID
    job_id: uuid.UUID
    role: DocumentRole
    filename: str
    file_size_bytes: int
    page_count: int
    pdf_metadata: dict | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class PageContentResponse(BaseModel):
    page_number: int
    page_type: PageType
    has_handwriting: bool
    has_annotations: bool
    content: dict | None = None
    extraction_confidence: float | None = None
    processing_status: str

    model_config = {"from_attributes": True}
```

- [ ] **Step 4: Create app/schemas/change.py**

```python
# docdiff-service/app/schemas/change.py
import uuid
from datetime import datetime

from pydantic import BaseModel, Field

from app.models.change import ChangeType, ReviewStatus, Significance


class ChangeResponse(BaseModel):
    id: uuid.UUID
    change_number: int
    change_type: ChangeType
    significance: Significance
    confidence: float
    page_original: int | None = None
    page_revised: int | None = None
    bbox_original: dict | None = None
    bbox_revised: dict | None = None
    value_before: str | None = None
    value_after: str | None = None
    context: str | None = None
    summary: str
    review_status: ReviewStatus
    auto_accepted: bool
    needs_human_review: bool
    reviewer_comment: str | None = None
    reviewed_at: datetime | None = None

    model_config = {"from_attributes": True}


class ReviewAction(BaseModel):
    action: ReviewStatus = Field(description="accept, reject, or escalate")
    comment: str | None = None
    edited_summary: str | None = None
    edited_significance: Significance | None = None
    edited_value_after: str | None = None


class BulkReviewAction(BaseModel):
    change_ids: list[uuid.UUID]
    action: ReviewStatus
    comment: str | None = None


class ManualChangeCreate(BaseModel):
    change_type: ChangeType
    significance: Significance
    page_original: int | None = None
    page_revised: int | None = None
    value_before: str | None = None
    value_after: str | None = None
    summary: str
```

- [ ] **Step 5: Create app/schemas/report.py**

```python
# docdiff-service/app/schemas/report.py
import uuid
from datetime import datetime

from pydantic import BaseModel


class ReportResponse(BaseModel):
    id: uuid.UUID
    job_id: uuid.UUID
    summary_stats: dict | None = None
    report_html: str | None = None
    report_pdf_path: str | None = None
    generated_at: datetime

    model_config = {"from_attributes": True}
```

- [ ] **Step 6: Create app/schemas/__init__.py**

```python
# docdiff-service/app/schemas/__init__.py
from app.schemas.change import BulkReviewAction, ChangeResponse, ManualChangeCreate, ReviewAction
from app.schemas.common import BBox, ErrorResponse, PaginatedResponse, SuccessResponse
from app.schemas.document import DocumentResponse, PageContentResponse
from app.schemas.job import JobCreate, JobListResponse, JobResponse
from app.schemas.report import ReportResponse

__all__ = [
    "SuccessResponse",
    "PaginatedResponse",
    "ErrorResponse",
    "BBox",
    "JobCreate",
    "JobResponse",
    "JobListResponse",
    "DocumentResponse",
    "PageContentResponse",
    "ChangeResponse",
    "ReviewAction",
    "BulkReviewAction",
    "ManualChangeCreate",
    "ReportResponse",
]
```

- [ ] **Step 7: Create app/api/deps.py**

```python
# docdiff-service/app/api/deps.py
from collections.abc import AsyncGenerator
from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db

DbSession = Annotated[AsyncSession, Depends(get_db)]
```

Note: Auth dependency will be added in Task 4.

- [ ] **Step 8: Create app/api/__init__.py**

```python
# docdiff-service/app/api/__init__.py
```

- [ ] **Step 9: Commit**

```bash
git add docdiff-service/app/schemas/ docdiff-service/app/api/
git commit -m "feat(docdiff): add Pydantic schemas and API dependencies"
```

---

## Task 4: Authentication Middleware

**Files:**
- Create: `docdiff-service/app/auth/__init__.py`
- Create: `docdiff-service/app/auth/jwt_validator.py`
- Create: `docdiff-service/app/auth/api_key.py`
- Create: `docdiff-service/app/auth/middleware.py`
- Modify: `docdiff-service/app/api/deps.py` (add auth dependency)
- Create: `docdiff-service/tests/__init__.py`
- Create: `docdiff-service/tests/conftest.py`
- Create: `docdiff-service/tests/test_api/__init__.py`
- Create: `docdiff-service/tests/test_api/test_auth.py`

- [ ] **Step 1: Create app/auth/__init__.py**

```python
# docdiff-service/app/auth/__init__.py
```

- [ ] **Step 2: Create app/auth/jwt_validator.py**

The ERP backend uses `jsonwebtoken` (Node.js) with HS256. The token payload has:
`{ userId, email, tenantId?, companyId?, employeeId?, roleId, permissions? }`

```python
# docdiff-service/app/auth/jwt_validator.py
from dataclasses import dataclass

from jose import JWTError, jwt

from app.config import settings

ALGORITHM = "HS256"


@dataclass
class JWTUser:
    user_id: str
    email: str
    tenant_id: str | None = None
    company_id: str | None = None
    employee_id: str | None = None
    role_id: str | None = None


def decode_jwt(token: str) -> JWTUser:
    """Decode and verify a JWT token from the ERP backend.

    Raises JWTError on invalid/expired token.
    """
    payload = jwt.decode(token, settings.jwt_secret, algorithms=[ALGORITHM])
    return JWTUser(
        user_id=payload["userId"],
        email=payload["email"],
        tenant_id=payload.get("tenantId"),
        company_id=payload.get("companyId"),
        employee_id=payload.get("employeeId"),
        role_id=payload.get("roleId"),
    )
```

- [ ] **Step 3: Create app/auth/api_key.py**

```python
# docdiff-service/app/auth/api_key.py
import hashlib
import secrets
from dataclasses import dataclass
from datetime import datetime

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.api_key import APIKey


@dataclass
class APIKeyUser:
    api_key_id: str
    name: str


def hash_api_key(key: str) -> str:
    return hashlib.sha256(key.encode()).hexdigest()


def generate_api_key() -> str:
    return f"dd_{secrets.token_urlsafe(32)}"


async def validate_api_key(key: str, db: AsyncSession) -> APIKeyUser | None:
    key_hash = hash_api_key(key)
    result = await db.execute(
        select(APIKey).where(APIKey.key_hash == key_hash, APIKey.is_active.is_(True))
    )
    api_key = result.scalar_one_or_none()
    if api_key is None:
        return None

    # Update last_used_at
    await db.execute(
        update(APIKey).where(APIKey.id == api_key.id).values(last_used_at=datetime.utcnow())
    )
    await db.commit()

    return APIKeyUser(api_key_id=str(api_key.id), name=api_key.name)
```

- [ ] **Step 4: Create app/auth/middleware.py**

```python
# docdiff-service/app/auth/middleware.py
from dataclasses import dataclass
from typing import Annotated

from fastapi import Depends, HTTPException, Request
from jose import JWTError
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.api_key import APIKeyUser, validate_api_key
from app.auth.jwt_validator import JWTUser, decode_jwt
from app.database import get_db


@dataclass
class AuthContext:
    user_id: str | None = None
    email: str | None = None
    company_id: str | None = None
    tenant_id: str | None = None
    api_key_id: str | None = None
    auth_method: str = "jwt"  # "jwt" or "api_key"


async def get_current_user(
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> AuthContext:
    # Try JWT first
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        token = auth_header[7:]
        try:
            jwt_user: JWTUser = decode_jwt(token)
            return AuthContext(
                user_id=jwt_user.user_id,
                email=jwt_user.email,
                company_id=jwt_user.company_id,
                tenant_id=jwt_user.tenant_id,
                auth_method="jwt",
            )
        except JWTError:
            raise HTTPException(status_code=401, detail="Invalid or expired JWT token")

    # Try API key
    api_key = request.headers.get("X-API-Key")
    if api_key:
        api_key_user: APIKeyUser | None = await validate_api_key(api_key, db)
        if api_key_user is None:
            raise HTTPException(status_code=401, detail="Invalid or revoked API key")
        return AuthContext(
            api_key_id=api_key_user.api_key_id,
            auth_method="api_key",
        )

    raise HTTPException(status_code=401, detail="Authentication required: provide Bearer token or X-API-Key header")


CurrentUser = Annotated[AuthContext, Depends(get_current_user)]
```

- [ ] **Step 5: Update app/api/deps.py with auth**

```python
# docdiff-service/app/api/deps.py
from collections.abc import AsyncGenerator
from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.middleware import AuthContext, get_current_user
from app.database import get_db

DbSession = Annotated[AsyncSession, Depends(get_db)]
CurrentUser = Annotated[AuthContext, Depends(get_current_user)]
```

- [ ] **Step 6: Create test fixtures**

```python
# docdiff-service/tests/__init__.py
```

```python
# docdiff-service/tests/test_api/__init__.py
```

```python
# docdiff-service/tests/conftest.py
import asyncio
from collections.abc import AsyncGenerator

import pytest
from httpx import ASGITransport, AsyncClient
from jose import jwt

from app.config import settings
from app.main import app

TEST_JWT_SECRET = "test-secret-key"


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def test_jwt_token() -> str:
    """Generate a test JWT token matching the ERP backend format."""
    payload = {
        "userId": "test-user-123",
        "email": "test@example.com",
        "tenantId": "test-tenant",
        "companyId": "test-company",
        "roleId": "test-role",
    }
    return jwt.encode(payload, TEST_JWT_SECRET, algorithm="HS256")


@pytest.fixture
async def client() -> AsyncGenerator[AsyncClient, None]:
    settings.jwt_secret = TEST_JWT_SECRET
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
```

- [ ] **Step 7: Write auth tests**

```python
# docdiff-service/tests/test_api/test_auth.py
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_health_no_auth(client: AsyncClient):
    resp = await client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


@pytest.mark.asyncio
async def test_unauthenticated_request_rejected(client: AsyncClient):
    resp = await client.get("/api/v1/jobs")
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_valid_jwt_accepted(client: AsyncClient, test_jwt_token: str):
    resp = await client.get(
        "/api/v1/jobs",
        headers={"Authorization": f"Bearer {test_jwt_token}"},
    )
    # 200 or 404 (route exists but no jobs) — not 401
    assert resp.status_code != 401


@pytest.mark.asyncio
async def test_invalid_jwt_rejected(client: AsyncClient):
    resp = await client.get(
        "/api/v1/jobs",
        headers={"Authorization": "Bearer invalid-token"},
    )
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_invalid_api_key_rejected(client: AsyncClient):
    resp = await client.get(
        "/api/v1/jobs",
        headers={"X-API-Key": "dd_invalid_key"},
    )
    assert resp.status_code == 401
```

- [ ] **Step 8: Commit**

```bash
git add docdiff-service/app/auth/ docdiff-service/app/api/deps.py docdiff-service/tests/
git commit -m "feat(docdiff): add dual auth middleware (JWT + API key)"
```

---

## Task 5: Health Check + API Router

**Files:**
- Create: `docdiff-service/app/api/health.py`
- Create: `docdiff-service/app/api/router.py`
- Create: `docdiff-service/app/api/jobs.py`
- Modify: `docdiff-service/app/main.py` (mount router)

- [ ] **Step 1: Create app/api/health.py**

```python
# docdiff-service/app/api/health.py
import logging

from fastapi import APIRouter
from sqlalchemy import text

from app.config import settings
from app.database import engine

logger = logging.getLogger("docdiff")
router = APIRouter(tags=["health"])


@router.get("/health")
async def health_check():
    checks = {"service": "ok", "version": "0.1.0"}

    # Database check
    try:
        async with engine.begin() as conn:
            await conn.execute(text("SELECT 1"))
        checks["database"] = "ok"
    except Exception as e:
        checks["database"] = f"error: {e}"

    # Redis check
    try:
        import redis.asyncio as aioredis
        r = aioredis.from_url(settings.redis_url)
        await r.ping()
        await r.aclose()
        checks["redis"] = "ok"
    except Exception as e:
        checks["redis"] = f"error: {e}"

    # Qwen local check
    if settings.qwen_local_endpoint:
        try:
            import httpx
            async with httpx.AsyncClient(timeout=5.0) as client:
                resp = await client.get(f"{settings.qwen_local_endpoint}/models")
                checks["qwen_local"] = "ok" if resp.status_code == 200 else f"status: {resp.status_code}"
        except Exception:
            checks["qwen_local"] = "unreachable"

    status = "ok" if all(v == "ok" for k, v in checks.items() if k not in ("qwen_local", "version")) else "degraded"
    checks["status"] = status
    return checks
```

- [ ] **Step 2: Create app/api/jobs.py (stub)**

```python
# docdiff-service/app/api/jobs.py
import uuid

from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from sqlalchemy import select

from app.api.deps import CurrentUser, DbSession
from app.config import settings
from app.models.job import ComparisonJob, JobStatus
from app.models.document import Document, DocumentRole
from app.schemas.job import JobCreate, JobListResponse, JobResponse
from app.schemas.common import SuccessResponse

router = APIRouter(prefix="/jobs", tags=["jobs"])


@router.post("", response_model=SuccessResponse[JobResponse])
async def create_job(
    db: DbSession,
    user: CurrentUser,
    original: UploadFile = File(..., description="Original PDF document"),
    revised: UploadFile = File(..., description="Revised PDF document"),
    model_provider: str = Form(default="anthropic"),
    model_name: str = Form(default="claude-sonnet-4-6"),
):
    """Create a new comparison job by uploading two PDF documents."""
    # Validate files
    for f, label in [(original, "original"), (revised, "revised")]:
        if not f.filename or not f.filename.lower().endswith(".pdf"):
            raise HTTPException(400, f"{label} file must be a PDF")
        if f.size and f.size > settings.max_file_size_mb * 1024 * 1024:
            raise HTTPException(400, f"{label} file exceeds {settings.max_file_size_mb}MB limit")

    # Create job
    job = ComparisonJob(
        model_provider=model_provider,
        model_name=model_name,
        status=JobStatus.UPLOADING,
        user_id=user.user_id,
        company_id=user.company_id,
        api_key_id=uuid.UUID(user.api_key_id) if user.api_key_id else None,
    )
    db.add(job)
    await db.flush()

    # Save files
    import os
    job_dir = os.path.join(settings.storage_path, "uploads", str(job.id))
    os.makedirs(job_dir, exist_ok=True)

    for upload, role in [(original, DocumentRole.ORIGINAL), (revised, DocumentRole.REVISED)]:
        file_path = os.path.join(job_dir, f"{role.value}_{upload.filename}")
        content = await upload.read()
        with open(file_path, "wb") as f:
            f.write(content)

        doc = Document(
            job_id=job.id,
            role=role,
            filename=upload.filename or "unknown.pdf",
            file_path=file_path,
            file_size_bytes=len(content),
            page_count=0,  # Updated during ingestion
        )
        db.add(doc)

    await db.commit()
    await db.refresh(job)
    return SuccessResponse(data=JobResponse.model_validate(job), message="Job created")


@router.get("", response_model=SuccessResponse[list[JobListResponse]])
async def list_jobs(db: DbSession, user: CurrentUser):
    """List comparison jobs for the current user."""
    query = select(ComparisonJob).order_by(ComparisonJob.created_at.desc())
    if user.user_id:
        query = query.where(ComparisonJob.user_id == user.user_id)
    elif user.api_key_id:
        query = query.where(ComparisonJob.api_key_id == uuid.UUID(user.api_key_id))
    result = await db.execute(query)
    jobs = result.scalars().all()
    return SuccessResponse(data=[JobListResponse.model_validate(j) for j in jobs])


@router.get("/{job_id}", response_model=SuccessResponse[JobResponse])
async def get_job(job_id: uuid.UUID, db: DbSession, user: CurrentUser):
    """Get job details."""
    result = await db.execute(select(ComparisonJob).where(ComparisonJob.id == job_id))
    job = result.scalar_one_or_none()
    if not job:
        raise HTTPException(404, "Job not found")
    return SuccessResponse(data=JobResponse.model_validate(job))


@router.delete("/{job_id}")
async def delete_job(job_id: uuid.UUID, db: DbSession, user: CurrentUser):
    """Cancel and delete a job."""
    result = await db.execute(select(ComparisonJob).where(ComparisonJob.id == job_id))
    job = result.scalar_one_or_none()
    if not job:
        raise HTTPException(404, "Job not found")
    await db.delete(job)
    await db.commit()
    return SuccessResponse(data=None, message="Job deleted")


@router.post("/{job_id}/start")
async def start_job(job_id: uuid.UUID, db: DbSession, user: CurrentUser):
    """Start processing a job."""
    result = await db.execute(select(ComparisonJob).where(ComparisonJob.id == job_id))
    job = result.scalar_one_or_none()
    if not job:
        raise HTTPException(404, "Job not found")
    if job.status != JobStatus.UPLOADING:
        raise HTTPException(400, f"Job cannot be started from status: {job.status}")

    # Enqueue to ARQ (will be implemented in Task 12)
    # For now, just update status
    job.status = JobStatus.PARSING_ORIGINAL
    job.current_stage = 1
    job.stage_progress = {"1": "in_progress"}
    await db.commit()

    return SuccessResponse(data=JobResponse.model_validate(job), message="Processing started")
```

- [ ] **Step 3: Create app/api/router.py**

```python
# docdiff-service/app/api/router.py
from fastapi import APIRouter

from app.api.health import router as health_router
from app.api.jobs import router as jobs_router

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(jobs_router)

# Health is mounted at root level (no /api/v1 prefix)
```

- [ ] **Step 4: Update app/main.py to mount routers**

Replace the inline `/health` endpoint and add router mount. The full updated `main.py`:

```python
# docdiff-service/app/main.py
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.health import router as health_router
from app.api.router import api_router
from app.config import settings

logger = logging.getLogger("docdiff")


@asynccontextmanager
async def lifespan(app: FastAPI):
    logging.basicConfig(level=getattr(logging, settings.log_level))
    logger.info("DocDiff Pro starting up...")

    import os
    os.makedirs(f"{settings.storage_path}/uploads", exist_ok=True)
    os.makedirs(f"{settings.storage_path}/reports", exist_ok=True)

    from app.database import engine
    from sqlalchemy import text
    async with engine.begin() as conn:
        await conn.execute(text("SELECT 1"))
    logger.info("Database connection verified")

    yield

    logger.info("DocDiff Pro shutting down...")


app = FastAPI(
    title="DocDiff Pro",
    description="AI-powered document comparison service",
    version="0.1.0",
    lifespan=lifespan,
)

origins = [o.strip() for o in settings.cors_origins.split(",")]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount routers
app.include_router(health_router)
app.include_router(api_router)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host=settings.host, port=settings.port, reload=True)
```

- [ ] **Step 5: Commit**

```bash
git add docdiff-service/app/api/ docdiff-service/app/main.py
git commit -m "feat(docdiff): add health check, jobs API, and router mounting"
```

---

## Task 6: AI Provider Abstraction + Response Parser

**Files:**
- Create: `docdiff-service/app/ai/__init__.py`
- Create: `docdiff-service/app/ai/base.py`
- Create: `docdiff-service/app/ai/response_parser.py`
- Create: `docdiff-service/app/ai/router.py`

- [ ] **Step 1: Create app/ai/__init__.py**

```python
# docdiff-service/app/ai/__init__.py
```

- [ ] **Step 2: Create app/ai/base.py**

```python
# docdiff-service/app/ai/base.py
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field

from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

logger = logging.getLogger("docdiff.ai")


@dataclass
class TokenUsage:
    input_tokens: int = 0
    output_tokens: int = 0
    cost_estimate: float = 0.0


@dataclass
class AIResponse:
    content: str
    usage: TokenUsage = field(default_factory=TokenUsage)
    model: str = ""


class RateLimitError(Exception):
    """Raised on 429 or rate limit errors — triggers retry."""


class ServerError(Exception):
    """Raised on 5xx errors — triggers retry."""


# Retry decorator for all AI calls
ai_retry = retry(
    retry=retry_if_exception_type((RateLimitError, ServerError, TimeoutError)),
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=1, max=30),
    before_sleep=lambda rs: logger.warning(
        f"AI call failed (attempt {rs.attempt_number}), retrying: {rs.outcome.exception()}"
    ),
)


class AIProvider(ABC):
    """Abstract base for all AI model providers."""

    @abstractmethod
    async def call(self, prompt: str, images: list[bytes] | None = None) -> AIResponse:
        """Send prompt (with optional images) to the model and return response."""
        ...

    @property
    @abstractmethod
    def provider_name(self) -> str:
        ...

    @property
    @abstractmethod
    def model_name(self) -> str:
        ...

    @property
    def supports_vision(self) -> bool:
        return True

    async def extract_page_content(self, image: bytes, prompt: str) -> AIResponse:
        return await self.call(prompt, images=[image])

    async def classify_change(self, context: str, prompt: str) -> AIResponse:
        return await self.call(f"{prompt}\n\n{context}")

    async def transcribe_handwriting(self, image: bytes, prompt: str) -> AIResponse:
        return await self.call(prompt, images=[image])
```

- [ ] **Step 3: Create app/ai/response_parser.py**

```python
# docdiff-service/app/ai/response_parser.py
import json
import logging
import re

from pydantic import BaseModel, ValidationError

logger = logging.getLogger("docdiff.ai")


def extract_json_from_text(text: str) -> str | None:
    """Extract JSON from AI response text, handling markdown code fences."""
    # Try to find JSON in code blocks
    code_block_match = re.search(r"```(?:json)?\s*\n?(.*?)\n?```", text, re.DOTALL)
    if code_block_match:
        return code_block_match.group(1).strip()

    # Try to find raw JSON (object or array)
    json_match = re.search(r"(\{.*\}|\[.*\])", text, re.DOTALL)
    if json_match:
        return json_match.group(1).strip()

    return None


def parse_ai_response(text: str, schema: type[BaseModel] | None = None) -> dict | list | None:
    """Parse AI response into structured data.

    1. Extract JSON from markdown code fences or raw text
    2. Parse JSON
    3. Optionally validate against Pydantic schema
    """
    json_str = extract_json_from_text(text)
    if json_str is None:
        logger.warning("No JSON found in AI response")
        return None

    try:
        data = json.loads(json_str)
    except json.JSONDecodeError as e:
        logger.warning(f"Failed to parse JSON from AI response: {e}")
        return None

    if schema is not None:
        try:
            validated = schema.model_validate(data)
            return validated.model_dump()
        except ValidationError as e:
            logger.warning(f"AI response failed schema validation: {e}")
            return data  # Return raw parsed JSON even if validation fails

    return data


def safe_parse_or_flag(
    text: str, schema: type[BaseModel] | None = None
) -> tuple[dict | None, bool]:
    """Parse AI response, returning (data, needs_review).

    Returns (parsed_data, False) on success.
    Returns (None, True) if parsing fails — caller should flag for human review.
    """
    result = parse_ai_response(text, schema)
    if result is None:
        return None, True
    return result, False
```

- [ ] **Step 4: Create app/ai/router.py**

```python
# docdiff-service/app/ai/router.py
import logging

from app.ai.base import AIProvider
from app.config import settings

logger = logging.getLogger("docdiff.ai")

_providers: dict[str, type[AIProvider]] = {}


def register_provider(name: str, provider_cls: type[AIProvider]):
    _providers[name] = provider_cls


def get_provider(provider_name: str, model_name: str) -> AIProvider:
    """Get an AI provider instance by name and model."""
    if provider_name not in _providers:
        raise ValueError(
            f"Unknown provider: {provider_name}. Available: {list(_providers.keys())}"
        )
    provider_cls = _providers[provider_name]
    return provider_cls(model_name=model_name)


def get_default_provider() -> AIProvider:
    return get_provider(settings.default_provider, settings.default_model)


def list_available_providers() -> list[dict]:
    """List all registered providers with their available models."""
    providers = []
    for name, cls in _providers.items():
        providers.append({
            "provider": name,
            "models": cls.available_models() if hasattr(cls, "available_models") else [],
        })
    return providers
```

- [ ] **Step 5: Commit**

```bash
git add docdiff-service/app/ai/
git commit -m "feat(docdiff): add AI provider abstraction, response parser, and model router"
```

---

## Task 7: AI Providers — Anthropic + Google + OpenRouter + Qwen

**Files:**
- Create: `docdiff-service/app/ai/anthropic_provider.py`
- Create: `docdiff-service/app/ai/google_provider.py`
- Create: `docdiff-service/app/ai/openrouter_provider.py`
- Create: `docdiff-service/app/ai/qwen_local_provider.py`
- Modify: `docdiff-service/app/ai/router.py` (register providers)

- [ ] **Step 1: Create app/ai/anthropic_provider.py**

```python
# docdiff-service/app/ai/anthropic_provider.py
import base64

import anthropic

from app.ai.base import AIProvider, AIResponse, RateLimitError, ServerError, TokenUsage, ai_retry
from app.config import settings

AVAILABLE_MODELS = ["claude-sonnet-4-6", "claude-opus-4-6"]


class AnthropicProvider(AIProvider):
    def __init__(self, model_name: str = "claude-sonnet-4-6"):
        self._model_name = model_name
        self._client = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)

    @property
    def provider_name(self) -> str:
        return "anthropic"

    @property
    def model_name(self) -> str:
        return self._model_name

    @staticmethod
    def available_models() -> list[str]:
        return AVAILABLE_MODELS

    @ai_retry
    async def call(self, prompt: str, images: list[bytes] | None = None) -> AIResponse:
        content = []
        if images:
            for img in images:
                b64 = base64.standard_b64encode(img).decode("utf-8")
                content.append({
                    "type": "image",
                    "source": {"type": "base64", "media_type": "image/png", "data": b64},
                })
        content.append({"type": "text", "text": prompt})

        try:
            response = await self._client.messages.create(
                model=self._model_name,
                max_tokens=4096,
                messages=[{"role": "user", "content": content}],
            )
        except anthropic.RateLimitError as e:
            raise RateLimitError(str(e)) from e
        except anthropic.InternalServerError as e:
            raise ServerError(str(e)) from e

        text = response.content[0].text if response.content else ""
        usage = TokenUsage(
            input_tokens=response.usage.input_tokens,
            output_tokens=response.usage.output_tokens,
        )
        return AIResponse(content=text, usage=usage, model=self._model_name)
```

- [ ] **Step 2: Create app/ai/google_provider.py**

```python
# docdiff-service/app/ai/google_provider.py
from google import genai
from google.genai import types

from app.ai.base import AIProvider, AIResponse, RateLimitError, ServerError, TokenUsage, ai_retry
from app.config import settings

AVAILABLE_MODELS = ["gemini-3.1-pro", "gemini-3-flash"]


class GoogleProvider(AIProvider):
    def __init__(self, model_name: str = "gemini-3.1-pro"):
        self._model_name = model_name
        self._client = genai.Client(api_key=settings.google_api_key)

    @property
    def provider_name(self) -> str:
        return "google"

    @property
    def model_name(self) -> str:
        return self._model_name

    @staticmethod
    def available_models() -> list[str]:
        return AVAILABLE_MODELS

    @ai_retry
    async def call(self, prompt: str, images: list[bytes] | None = None) -> AIResponse:
        contents = []
        if images:
            for img in images:
                contents.append(types.Part.from_bytes(data=img, mime_type="image/png"))
        contents.append(prompt)

        try:
            response = await self._client.aio.models.generate_content(
                model=self._model_name,
                contents=contents,
            )
        except Exception as e:
            error_str = str(e).lower()
            if "429" in error_str or "rate" in error_str:
                raise RateLimitError(str(e)) from e
            if "500" in error_str or "503" in error_str:
                raise ServerError(str(e)) from e
            raise

        text = response.text or ""
        usage = TokenUsage()
        if response.usage_metadata:
            usage.input_tokens = response.usage_metadata.prompt_token_count or 0
            usage.output_tokens = response.usage_metadata.candidates_token_count or 0
        return AIResponse(content=text, usage=usage, model=self._model_name)
```

- [ ] **Step 3: Create app/ai/openrouter_provider.py**

```python
# docdiff-service/app/ai/openrouter_provider.py
import base64

import httpx

from app.ai.base import AIProvider, AIResponse, RateLimitError, ServerError, TokenUsage, ai_retry
from app.config import settings

OPENROUTER_BASE = "https://openrouter.ai/api/v1"
AVAILABLE_MODELS = ["google/gemini-2.5-pro-preview", "anthropic/claude-sonnet-4"]


class OpenRouterProvider(AIProvider):
    def __init__(self, model_name: str = "google/gemini-2.5-pro-preview"):
        self._model_name = model_name

    @property
    def provider_name(self) -> str:
        return "openrouter"

    @property
    def model_name(self) -> str:
        return self._model_name

    @staticmethod
    def available_models() -> list[str]:
        return AVAILABLE_MODELS

    @ai_retry
    async def call(self, prompt: str, images: list[bytes] | None = None) -> AIResponse:
        content = []
        if images:
            for img in images:
                b64 = base64.standard_b64encode(img).decode("utf-8")
                content.append({
                    "type": "image_url",
                    "image_url": {"url": f"data:image/png;base64,{b64}"},
                })
        content.append({"type": "text", "text": prompt})

        async with httpx.AsyncClient(timeout=120.0) as client:
            resp = await client.post(
                f"{OPENROUTER_BASE}/chat/completions",
                headers={
                    "Authorization": f"Bearer {settings.openrouter_api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": self._model_name,
                    "messages": [{"role": "user", "content": content}],
                    "max_tokens": 4096,
                },
            )

        if resp.status_code == 429:
            raise RateLimitError("OpenRouter rate limited")
        if resp.status_code >= 500:
            raise ServerError(f"OpenRouter server error: {resp.status_code}")
        resp.raise_for_status()

        data = resp.json()
        text = data["choices"][0]["message"]["content"]
        usage_data = data.get("usage", {})
        usage = TokenUsage(
            input_tokens=usage_data.get("prompt_tokens", 0),
            output_tokens=usage_data.get("completion_tokens", 0),
        )
        return AIResponse(content=text, usage=usage, model=self._model_name)
```

- [ ] **Step 4: Create app/ai/qwen_local_provider.py**

```python
# docdiff-service/app/ai/qwen_local_provider.py
import base64

import httpx

from app.ai.base import AIProvider, AIResponse, RateLimitError, ServerError, TokenUsage, ai_retry
from app.config import settings

AVAILABLE_MODELS = ["qwen3-vl-8b", "qwen3-vl-30b-a3b"]


class QwenLocalProvider(AIProvider):
    def __init__(self, model_name: str = "qwen3-vl-8b"):
        self._model_name = model_name
        self._endpoint = settings.qwen_local_endpoint

    @property
    def provider_name(self) -> str:
        return "qwen_local"

    @property
    def model_name(self) -> str:
        return self._model_name

    @staticmethod
    def available_models() -> list[str]:
        return AVAILABLE_MODELS

    @ai_retry
    async def call(self, prompt: str, images: list[bytes] | None = None) -> AIResponse:
        content = []
        if images:
            for img in images:
                b64 = base64.standard_b64encode(img).decode("utf-8")
                content.append({
                    "type": "image_url",
                    "image_url": {"url": f"data:image/png;base64,{b64}"},
                })
        content.append({"type": "text", "text": prompt})

        async with httpx.AsyncClient(timeout=180.0) as client:
            try:
                resp = await client.post(
                    f"{self._endpoint}/chat/completions",
                    json={
                        "model": self._model_name,
                        "messages": [{"role": "user", "content": content}],
                        "max_tokens": 4096,
                    },
                )
            except httpx.ConnectError as e:
                raise ServerError(f"Qwen local endpoint unreachable: {e}") from e

        if resp.status_code == 429:
            raise RateLimitError("Qwen local rate limited")
        if resp.status_code >= 500:
            raise ServerError(f"Qwen server error: {resp.status_code}")
        resp.raise_for_status()

        data = resp.json()
        text = data["choices"][0]["message"]["content"]
        usage_data = data.get("usage", {})
        usage = TokenUsage(
            input_tokens=usage_data.get("prompt_tokens", 0),
            output_tokens=usage_data.get("completion_tokens", 0),
        )
        return AIResponse(content=text, usage=usage, model=self._model_name)
```

- [ ] **Step 5: Register all providers in router.py**

Append to `app/ai/router.py` at the bottom:

```python
# Register all providers
from app.ai.anthropic_provider import AnthropicProvider
from app.ai.google_provider import GoogleProvider
from app.ai.openrouter_provider import OpenRouterProvider
from app.ai.qwen_local_provider import QwenLocalProvider

register_provider("anthropic", AnthropicProvider)
register_provider("google", GoogleProvider)
register_provider("openrouter", OpenRouterProvider)
register_provider("qwen_local", QwenLocalProvider)
```

- [ ] **Step 6: Commit**

```bash
git add docdiff-service/app/ai/
git commit -m "feat(docdiff): add all 4 AI providers (Anthropic, Google, OpenRouter, Qwen)"
```

---

## Task 8: Prompt Templates

**Files:**
- Create: `docdiff-service/app/prompts/__init__.py`
- Create: `docdiff-service/app/prompts/extract_page.py`
- Create: `docdiff-service/app/prompts/classify_change.py`
- Create: `docdiff-service/app/prompts/transcribe_handwriting.py`

- [ ] **Step 1: Create app/prompts/__init__.py**

```python
# docdiff-service/app/prompts/__init__.py
```

- [ ] **Step 2: Create app/prompts/extract_page.py**

```python
# docdiff-service/app/prompts/extract_page.py

EXTRACT_PAGE_CONTENT = """Analyze this document page image and extract all content into structured JSON.

Extract:
1. **Text blocks**: Every paragraph, heading, and standalone text with reading order
2. **Tables**: Complete table structure with headers, rows, columns, merged cells
3. **Annotations**: Handwritten notes, highlights, stamps, sticky notes
4. **Section hierarchy**: Heading levels and section structure

Return JSON in this exact format:
```json
{{
  "blocks": [
    {{
      "id": "blk_001",
      "type": "text|table|image|annotation|header|footer",
      "bbox": {{"x": 0, "y": 0, "width": 100, "height": 20}},
      "text": "extracted text content",
      "table": {{
        "rows": 5,
        "cols": 3,
        "cells": [
          {{"row": 0, "col": 0, "rowspan": 1, "colspan": 1, "text": "cell text"}}
        ],
        "headers": ["Col A", "Col B", "Col C"]
      }},
      "annotation": {{
        "type": "handwriting|sticky_note|highlight|strikethrough|stamp|text_box",
        "transcription": "transcribed text if applicable",
        "transcription_confidence": 0.85
      }},
      "section_level": 2,
      "section_title": "Section Title"
    }}
  ],
  "reading_order": ["blk_001", "blk_002"],
  "sections": [
    {{"title": "Section Name", "level": 1, "block_ids": ["blk_001"]}}
  ]
}}
```

Rules:
- Include EVERY piece of text on the page, no matter how small
- For tables, extract EVERY cell including empty ones
- Bounding box coordinates should be approximate pixel positions
- Only include "table" field for table-type blocks
- Only include "annotation" field for annotation-type blocks
- section_level: 1=main heading, 2=subheading, 3=sub-subheading
- reading_order must list ALL block IDs in natural reading sequence
- If text is unclear, provide best guess and note low confidence in annotation field"""


EXTRACT_PAGE_ANTHROPIC = f"""<task>
{EXTRACT_PAGE_CONTENT}
</task>

<output_format>JSON only, no additional text</output_format>"""


EXTRACT_PAGE_GOOGLE = EXTRACT_PAGE_CONTENT + """

IMPORTANT: Return ONLY the JSON object. No markdown formatting, no explanation."""


def get_extract_prompt(provider: str) -> str:
    if provider == "anthropic":
        return EXTRACT_PAGE_ANTHROPIC
    if provider == "google":
        return EXTRACT_PAGE_GOOGLE
    return EXTRACT_PAGE_CONTENT
```

- [ ] **Step 3: Create app/prompts/classify_change.py**

```python
# docdiff-service/app/prompts/classify_change.py

CLASSIFY_CHANGE = """You are classifying a detected change between two document versions.

The change is:
- Type: {change_type}
- Before: {value_before}
- After: {value_after}
- Context: {context}

Classify the significance of this change:

- **material**: Changes to specifications, tolerances, quantities, materials, dimensions, or any value that would affect manufacturing or pricing
- **substantive**: Changes to requirements text, scope descriptions, terms, or conditions that alter meaning
- **cosmetic**: Formatting, whitespace, pagination, or stylistic changes with no impact on meaning
- **uncertain**: Cannot confidently classify; requires human review

Also rate your confidence from 0.0 to 1.0.

Return JSON:
```json
{{
  "significance": "material|substantive|cosmetic|uncertain",
  "confidence": 0.95,
  "reasoning": "Brief explanation of classification"
}}
```"""


CLASSIFY_CHANGE_ANTHROPIC = f"""<task>
{CLASSIFY_CHANGE}
</task>
<output_format>JSON only</output_format>"""


def get_classify_prompt(
    provider: str,
    change_type: str,
    value_before: str,
    value_after: str,
    context: str,
) -> str:
    template = CLASSIFY_CHANGE_ANTHROPIC if provider == "anthropic" else CLASSIFY_CHANGE
    return template.format(
        change_type=change_type,
        value_before=value_before or "(none)",
        value_after=value_after or "(none)",
        context=context or "(no surrounding context)",
    )
```

- [ ] **Step 4: Create app/prompts/transcribe_handwriting.py**

```python
# docdiff-service/app/prompts/transcribe_handwriting.py

TRANSCRIBE_HANDWRITING = """This image contains a handwritten annotation or note on a document page.

Please:
1. Transcribe the handwritten text as accurately as possible
2. Rate your confidence in the transcription (0.0 to 1.0)
3. Describe the type of annotation (margin note, correction, checkmark, arrow, circle, etc.)

Return JSON:
```json
{{
  "transcription": "the handwritten text",
  "confidence": 0.75,
  "annotation_type": "margin_note|correction|checkmark|arrow|circle|underline|strikethrough|other",
  "notes": "any additional observations about the annotation"
}}
```

If the handwriting is completely illegible, return confidence 0.0 and transcription as empty string."""


def get_transcribe_prompt(provider: str) -> str:
    if provider == "anthropic":
        return f"<task>\n{TRANSCRIBE_HANDWRITING}\n</task>\n<output_format>JSON only</output_format>"
    return TRANSCRIBE_HANDWRITING
```

- [ ] **Step 5: Commit**

```bash
git add docdiff-service/app/prompts/
git commit -m "feat(docdiff): add versioned prompt templates for extract, classify, transcribe"
```

---

## Task 9: PDF Utilities (Metadata, Renderer, Docling Parser)

**Files:**
- Create: `docdiff-service/app/pdf/__init__.py`
- Create: `docdiff-service/app/pdf/metadata.py`
- Create: `docdiff-service/app/pdf/renderer.py`
- Create: `docdiff-service/app/pdf/parser.py`

- [ ] **Step 1: Create app/pdf/__init__.py**

```python
# docdiff-service/app/pdf/__init__.py
```

- [ ] **Step 2: Create app/pdf/metadata.py**

```python
# docdiff-service/app/pdf/metadata.py
import logging
from dataclasses import dataclass
from pathlib import Path

import fitz  # PyMuPDF

logger = logging.getLogger("docdiff.pdf")


@dataclass
class PDFMetadata:
    page_count: int
    file_size_bytes: int
    title: str | None
    author: str | None
    creator: str | None
    producer: str | None
    creation_date: str | None
    pdf_version: str | None
    is_encrypted: bool


def extract_metadata(file_path: str) -> PDFMetadata:
    """Extract metadata from a PDF file using PyMuPDF."""
    path = Path(file_path)
    doc = fitz.open(file_path)
    meta = doc.metadata or {}

    result = PDFMetadata(
        page_count=doc.page_count,
        file_size_bytes=path.stat().st_size,
        title=meta.get("title") or None,
        author=meta.get("author") or None,
        creator=meta.get("creator") or None,
        producer=meta.get("producer") or None,
        creation_date=meta.get("creationDate") or None,
        pdf_version=f"{doc.metadata.get('format', '')}" if meta else None,
        is_encrypted=doc.is_encrypted,
    )
    doc.close()
    return result


def validate_pdf(file_path: str, max_pages: int, max_size_mb: int) -> tuple[bool, str]:
    """Validate a PDF file. Returns (is_valid, error_message)."""
    path = Path(file_path)
    if not path.exists():
        return False, "File not found"

    size_mb = path.stat().st_size / (1024 * 1024)
    if size_mb > max_size_mb:
        return False, f"File size ({size_mb:.1f}MB) exceeds {max_size_mb}MB limit"

    try:
        doc = fitz.open(file_path)
    except Exception as e:
        return False, f"Invalid PDF file: {e}"

    if doc.is_encrypted:
        doc.close()
        return False, "PDF is password-protected or encrypted"

    if doc.page_count > max_pages:
        doc.close()
        return False, f"Page count ({doc.page_count}) exceeds {max_pages} page limit"

    if doc.page_count == 0:
        doc.close()
        return False, "PDF has no pages"

    doc.close()
    return True, ""
```

- [ ] **Step 3: Create app/pdf/renderer.py**

```python
# docdiff-service/app/pdf/renderer.py
import logging
import os
from pathlib import Path

import fitz  # PyMuPDF

from app.config import settings

logger = logging.getLogger("docdiff.pdf")


def render_page_to_image(
    pdf_path: str,
    page_number: int,
    output_dir: str,
    dpi: int | None = None,
) -> str:
    """Render a single PDF page to a PNG image.

    Args:
        pdf_path: Path to the PDF file
        page_number: 0-indexed page number
        output_dir: Directory to save the image
        dpi: Resolution in DPI (default: from settings, typically 250)

    Returns:
        Path to the rendered PNG image
    """
    if dpi is None:
        dpi = settings.page_render_dpi

    doc = fitz.open(pdf_path)
    page = doc[page_number]

    # Calculate zoom factor from DPI (default PDF is 72 DPI)
    zoom = dpi / 72.0
    matrix = fitz.Matrix(zoom, zoom)

    pix = page.get_pixmap(matrix=matrix)

    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, f"page_{page_number + 1:03d}.png")
    pix.save(output_path)

    doc.close()
    logger.debug(f"Rendered page {page_number + 1} at {dpi} DPI → {output_path}")
    return output_path


def render_all_pages(pdf_path: str, output_dir: str, dpi: int | None = None) -> list[str]:
    """Render all pages of a PDF to PNG images."""
    doc = fitz.open(pdf_path)
    page_count = doc.page_count
    doc.close()

    paths = []
    for i in range(page_count):
        path = render_page_to_image(pdf_path, i, output_dir, dpi)
        paths.append(path)

    return paths


def has_text_layer(pdf_path: str, page_number: int) -> bool:
    """Check if a specific page has an embedded text layer."""
    doc = fitz.open(pdf_path)
    page = doc[page_number]
    text = page.get_text("text").strip()
    doc.close()
    return len(text) > 10  # More than trivial whitespace
```

- [ ] **Step 4: Create app/pdf/parser.py**

```python
# docdiff-service/app/pdf/parser.py
import logging
from pathlib import Path

logger = logging.getLogger("docdiff.pdf")


def parse_document_with_docling(file_path: str) -> list[dict]:
    """Parse a PDF document using Docling for structural extraction.

    Returns a list of page content dicts, one per page, each containing
    the parsed blocks, reading order, and sections.
    """
    try:
        from docling.document_converter import DocumentConverter
    except ImportError:
        logger.error("Docling not installed. Install with: pip install docling")
        raise

    converter = DocumentConverter()
    result = converter.convert(file_path)
    doc = result.document

    pages: list[dict] = []
    page_blocks: dict[int, list[dict]] = {}

    block_counter = 0
    for item in doc.iterate_items():
        element = item
        # Docling items have a prov (provenance) with page info
        page_num = 1
        bbox = {"x": 0, "y": 0, "width": 0, "height": 0}

        if hasattr(element, "prov") and element.prov:
            prov = element.prov[0] if isinstance(element.prov, list) else element.prov
            if hasattr(prov, "page_no"):
                page_num = prov.page_no
            if hasattr(prov, "bbox"):
                b = prov.bbox
                bbox = {
                    "x": getattr(b, "l", 0),
                    "y": getattr(b, "t", 0),
                    "width": getattr(b, "r", 0) - getattr(b, "l", 0),
                    "height": getattr(b, "b", 0) - getattr(b, "t", 0),
                }

        block_counter += 1
        block_id = f"blk_{block_counter:03d}"

        block: dict = {
            "id": block_id,
            "type": "text",
            "bbox": bbox,
            "text": "",
        }

        # Determine block type from Docling element
        element_type = type(element).__name__.lower()

        if "table" in element_type:
            block["type"] = "table"
            table_data = _extract_table_data(element)
            if table_data:
                block["table"] = table_data
                block["text"] = ""
        elif "heading" in element_type or "title" in element_type:
            block["type"] = "text"
            block["text"] = element.text if hasattr(element, "text") else str(element)
            level = getattr(element, "level", 1)
            block["section_level"] = level
            block["section_title"] = block["text"]
        elif "picture" in element_type or "figure" in element_type:
            block["type"] = "image"
            block["text"] = getattr(element, "caption", "") or ""
        else:
            block["text"] = element.text if hasattr(element, "text") else str(element)

        if page_num not in page_blocks:
            page_blocks[page_num] = []
        page_blocks[page_num].append(block)

    # Assemble per-page content
    max_page = max(page_blocks.keys()) if page_blocks else 0
    for p in range(1, max_page + 1):
        blocks = page_blocks.get(p, [])
        sections = [
            {
                "title": b.get("section_title", ""),
                "level": b.get("section_level", 1),
                "block_ids": [b["id"]],
            }
            for b in blocks
            if b.get("section_level")
        ]
        pages.append({
            "blocks": blocks,
            "reading_order": [b["id"] for b in blocks],
            "sections": sections,
        })

    return pages


def _extract_table_data(element) -> dict | None:
    """Extract table structure from a Docling table element."""
    try:
        if hasattr(element, "export_to_dataframe"):
            df = element.export_to_dataframe()
            headers = list(df.columns)
            cells = []
            for row_idx, row in df.iterrows():
                for col_idx, val in enumerate(row):
                    cells.append({
                        "row": int(row_idx) + 1,  # 1-indexed, row 0 is headers
                        "col": col_idx,
                        "rowspan": 1,
                        "colspan": 1,
                        "text": str(val) if val is not None else "",
                    })
            # Add header row
            header_cells = [
                {"row": 0, "col": i, "rowspan": 1, "colspan": 1, "text": h}
                for i, h in enumerate(headers)
            ]
            return {
                "rows": len(df) + 1,
                "cols": len(headers),
                "cells": header_cells + cells,
                "headers": headers,
            }
    except Exception as e:
        logger.warning(f"Failed to extract table data: {e}")

    return None
```

- [ ] **Step 5: Commit**

```bash
git add docdiff-service/app/pdf/
git commit -m "feat(docdiff): add PDF utilities (metadata, renderer at 250 DPI, Docling parser)"
```

---

## Task 10: Diff Utilities (diff-match-patch + Table Utils)

**Files:**
- Create: `docdiff-service/app/utils/__init__.py`
- Create: `docdiff-service/app/utils/diff_utils.py`
- Create: `docdiff-service/app/utils/table_utils.py`
- Create: `docdiff-service/app/utils/bbox.py`

- [ ] **Step 1: Create app/utils/__init__.py**

```python
# docdiff-service/app/utils/__init__.py
```

- [ ] **Step 2: Create app/utils/diff_utils.py**

```python
# docdiff-service/app/utils/diff_utils.py
import logging
from dataclasses import dataclass

from diff_match_patch import diff_match_patch

logger = logging.getLogger("docdiff.utils")

dmp = diff_match_patch()


@dataclass
class TextDiff:
    """Represents a text difference between two strings."""
    diff_type: str  # "addition", "deletion", "modification", "equal"
    value_before: str
    value_after: str
    position: int  # character position in original


def compute_text_diff(text_before: str, text_after: str) -> list[TextDiff]:
    """Compute word-level text diff using Google's diff-match-patch.

    Returns a list of TextDiff objects representing changes.
    """
    if text_before == text_after:
        return []

    # Compute character-level diff
    diffs = dmp.diff_main(text_before, text_after)
    # Clean up for semantic readability
    dmp.diff_cleanupSemantic(diffs)

    results: list[TextDiff] = []
    position = 0

    i = 0
    while i < len(diffs):
        op, text = diffs[i]

        if op == 0:  # EQUAL
            position += len(text)
            i += 1
            continue

        if op == -1:  # DELETE
            # Check if next op is INSERT (modification)
            if i + 1 < len(diffs) and diffs[i + 1][0] == 1:
                # This is a modification (delete + insert)
                _, insert_text = diffs[i + 1]
                results.append(TextDiff(
                    diff_type="modification",
                    value_before=text,
                    value_after=insert_text,
                    position=position,
                ))
                position += len(text)
                i += 2
            else:
                # Pure deletion
                results.append(TextDiff(
                    diff_type="deletion",
                    value_before=text,
                    value_after="",
                    position=position,
                ))
                position += len(text)
                i += 1

        elif op == 1:  # INSERT
            results.append(TextDiff(
                diff_type="addition",
                value_before="",
                value_after=text,
                position=position,
            ))
            i += 1

    return results


def compute_similarity(text_a: str, text_b: str) -> float:
    """Compute similarity ratio between two strings (0.0 to 1.0)."""
    if not text_a and not text_b:
        return 1.0
    if not text_a or not text_b:
        return 0.0

    diffs = dmp.diff_main(text_a, text_b)
    levenshtein = dmp.diff_levenshtein(diffs)
    max_len = max(len(text_a), len(text_b))
    return 1.0 - (levenshtein / max_len)
```

- [ ] **Step 3: Create app/utils/table_utils.py**

```python
# docdiff-service/app/utils/table_utils.py
import logging
from dataclasses import dataclass

from app.utils.diff_utils import compute_similarity

logger = logging.getLogger("docdiff.utils")


@dataclass
class CellDiff:
    """Represents a change in a single table cell."""
    row: int
    col: int
    value_before: str
    value_after: str
    diff_type: str  # "modified", "added", "deleted"


@dataclass
class TableDiff:
    """Represents all changes between two tables."""
    cell_changes: list[CellDiff]
    rows_added: list[int]
    rows_deleted: list[int]
    structure_changed: bool
    header_changes: list[CellDiff]


def compare_tables(table_a: dict, table_b: dict) -> TableDiff:
    """Compare two table structures and return all differences.

    Tables are dicts with keys: rows, cols, cells, headers.
    Each cell: {"row": int, "col": int, "text": str, "rowspan": int, "colspan": int}
    """
    cells_a = _build_cell_map(table_a.get("cells", []))
    cells_b = _build_cell_map(table_b.get("cells", []))
    headers_a = table_a.get("headers", [])
    headers_b = table_b.get("headers", [])

    cell_changes: list[CellDiff] = []
    rows_added: list[int] = []
    rows_deleted: list[int] = []

    # Check structural changes
    structure_changed = (
        table_a.get("rows") != table_b.get("rows")
        or table_a.get("cols") != table_b.get("cols")
    )

    # Header changes
    header_changes: list[CellDiff] = []
    max_headers = max(len(headers_a), len(headers_b))
    for i in range(max_headers):
        ha = headers_a[i] if i < len(headers_a) else ""
        hb = headers_b[i] if i < len(headers_b) else ""
        if ha != hb:
            header_changes.append(CellDiff(row=0, col=i, value_before=ha, value_after=hb, diff_type="modified"))

    # Cell-level comparison
    all_keys = set(cells_a.keys()) | set(cells_b.keys())
    for key in sorted(all_keys):
        val_a = cells_a.get(key, None)
        val_b = cells_b.get(key, None)
        row, col = key

        if val_a is None and val_b is not None:
            cell_changes.append(CellDiff(row=row, col=col, value_before="", value_after=val_b, diff_type="added"))
        elif val_a is not None and val_b is None:
            cell_changes.append(CellDiff(row=row, col=col, value_before=val_a, value_after="", diff_type="deleted"))
        elif val_a != val_b:
            cell_changes.append(CellDiff(row=row, col=col, value_before=val_a or "", value_after=val_b or "", diff_type="modified"))

    # Detect added/deleted rows
    rows_in_a = {key[0] for key in cells_a.keys()}
    rows_in_b = {key[0] for key in cells_b.keys()}
    rows_added = sorted(rows_in_b - rows_in_a)
    rows_deleted = sorted(rows_in_a - rows_in_b)

    return TableDiff(
        cell_changes=cell_changes,
        rows_added=rows_added,
        rows_deleted=rows_deleted,
        structure_changed=structure_changed,
        header_changes=header_changes,
    )


def _build_cell_map(cells: list[dict]) -> dict[tuple[int, int], str]:
    """Build a (row, col) → text mapping from a cells list."""
    cell_map: dict[tuple[int, int], str] = {}
    for cell in cells:
        key = (cell["row"], cell["col"])
        cell_map[key] = cell.get("text", "")
    return cell_map


def compute_table_similarity(table_a: dict, table_b: dict) -> float:
    """Compute similarity between two tables for alignment purposes."""
    headers_a = " ".join(table_a.get("headers", []))
    headers_b = " ".join(table_b.get("headers", []))
    header_sim = compute_similarity(headers_a, headers_b)

    size_a = table_a.get("rows", 0) * table_a.get("cols", 0)
    size_b = table_b.get("rows", 0) * table_b.get("cols", 0)
    if max(size_a, size_b) == 0:
        size_sim = 1.0
    else:
        size_sim = 1.0 - abs(size_a - size_b) / max(size_a, size_b)

    return 0.7 * header_sim + 0.3 * size_sim
```

- [ ] **Step 4: Create app/utils/bbox.py**

```python
# docdiff-service/app/utils/bbox.py
from dataclasses import dataclass


@dataclass
class BBox:
    x: float
    y: float
    width: float
    height: float

    @property
    def x2(self) -> float:
        return self.x + self.width

    @property
    def y2(self) -> float:
        return self.y + self.height

    def intersects(self, other: "BBox") -> bool:
        return not (
            self.x2 < other.x
            or other.x2 < self.x
            or self.y2 < other.y
            or other.y2 < self.y
        )

    def intersection_area(self, other: "BBox") -> float:
        x_overlap = max(0, min(self.x2, other.x2) - max(self.x, other.x))
        y_overlap = max(0, min(self.y2, other.y2) - max(self.y, other.y))
        return x_overlap * y_overlap

    def iou(self, other: "BBox") -> float:
        """Intersection over Union."""
        inter = self.intersection_area(other)
        area_a = self.width * self.height
        area_b = other.width * other.height
        union = area_a + area_b - inter
        return inter / union if union > 0 else 0.0

    def contains(self, other: "BBox") -> bool:
        return (
            self.x <= other.x
            and self.y <= other.y
            and self.x2 >= other.x2
            and self.y2 >= other.y2
        )

    @classmethod
    def from_dict(cls, d: dict) -> "BBox":
        return cls(x=d["x"], y=d["y"], width=d["width"], height=d["height"])

    def to_dict(self) -> dict:
        return {"x": self.x, "y": self.y, "width": self.width, "height": self.height}
```

- [ ] **Step 5: Commit**

```bash
git add docdiff-service/app/utils/
git commit -m "feat(docdiff): add diff-match-patch text diffs, table comparison, and bbox utils"
```

---

## Task 11: Pipeline Stages 1-4 (Ingestion, Classification, Extraction, Normalization)

**Files:**
- Create: `docdiff-service/app/pipeline/__init__.py`
- Create: `docdiff-service/app/pipeline/stage_1_ingestion.py`
- Create: `docdiff-service/app/pipeline/stage_2_classification.py`
- Create: `docdiff-service/app/pipeline/stage_3_extraction.py`
- Create: `docdiff-service/app/pipeline/stage_4_normalization.py`

- [ ] **Step 1: Create app/pipeline/__init__.py**

```python
# docdiff-service/app/pipeline/__init__.py
```

- [ ] **Step 2: Create app/pipeline/stage_1_ingestion.py**

```python
# docdiff-service/app/pipeline/stage_1_ingestion.py
import logging
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models.document import Document, DocumentPage
from app.models.job import ComparisonJob, JobStatus
from app.pdf.metadata import extract_metadata, validate_pdf

logger = logging.getLogger("docdiff.pipeline")


async def run_stage_1(job_id: uuid.UUID, db: AsyncSession) -> bool:
    """Stage 1: Ingestion and Validation.

    - Validate both PDFs (format, size, page count, encryption)
    - Extract metadata
    - Create DocumentPage records for each page
    - Render page images

    Returns True on success, False on failure.
    """
    result = await db.execute(
        select(ComparisonJob).where(ComparisonJob.id == job_id)
    )
    job = result.scalar_one_or_none()
    if not job:
        logger.error(f"Job {job_id} not found")
        return False

    result = await db.execute(
        select(Document).where(Document.job_id == job_id)
    )
    documents = result.scalars().all()

    if len(documents) != 2:
        job.status = JobStatus.FAILED
        job.error_message = f"Expected 2 documents, found {len(documents)}"
        await db.commit()
        return False

    for doc in documents:
        # Validate
        is_valid, error = validate_pdf(doc.file_path, settings.max_pages, settings.max_file_size_mb)
        if not is_valid:
            job.status = JobStatus.FAILED
            job.error_message = f"Validation failed for {doc.role}: {error}"
            await db.commit()
            return False

        # Extract metadata
        meta = extract_metadata(doc.file_path)
        doc.page_count = meta.page_count
        doc.pdf_metadata = {
            "title": meta.title,
            "author": meta.author,
            "creator": meta.creator,
            "producer": meta.producer,
            "creation_date": meta.creation_date,
            "pdf_version": meta.pdf_version,
        }

        # Create page records
        for page_num in range(meta.page_count):
            page = DocumentPage(
                document_id=doc.id,
                page_number=page_num + 1,  # 1-indexed
            )
            db.add(page)

        # Render page images
        import os
        from app.pdf.renderer import render_all_pages
        image_dir = os.path.join(
            settings.storage_path, "uploads", str(job_id), f"{doc.role}_pages"
        )
        image_paths = render_all_pages(doc.file_path, image_dir)

        # Update page records with image paths
        await db.flush()
        page_result = await db.execute(
            select(DocumentPage)
            .where(DocumentPage.document_id == doc.id)
            .order_by(DocumentPage.page_number)
        )
        pages = page_result.scalars().all()
        for page, img_path in zip(pages, image_paths):
            page.image_path = img_path

    await db.commit()
    logger.info(f"Stage 1 complete for job {job_id}")
    return True
```

- [ ] **Step 3: Create app/pipeline/stage_2_classification.py**

```python
# docdiff-service/app/pipeline/stage_2_classification.py
import logging
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.document import Document, DocumentPage, PageType
from app.pdf.renderer import has_text_layer

logger = logging.getLogger("docdiff.pipeline")


async def run_stage_2(job_id: uuid.UUID, db: AsyncSession) -> bool:
    """Stage 2: Page Classification.

    For each page, determine if it's born-digital, scanned, or mixed.
    Detect presence of handwriting via simple heuristics (refined later by VLM).
    """
    result = await db.execute(
        select(Document).where(Document.job_id == job_id)
    )
    documents = result.scalars().all()

    for doc in documents:
        page_result = await db.execute(
            select(DocumentPage)
            .where(DocumentPage.document_id == doc.id)
            .order_by(DocumentPage.page_number)
        )
        pages = page_result.scalars().all()

        for page in pages:
            # Check for text layer
            page_idx = page.page_number - 1  # 0-indexed for PyMuPDF
            has_text = has_text_layer(doc.file_path, page_idx)

            if has_text:
                page.page_type = PageType.BORN_DIGITAL
            else:
                page.page_type = PageType.SCANNED

            # Check for annotations via PyMuPDF
            import fitz
            pdf_doc = fitz.open(doc.file_path)
            pdf_page = pdf_doc[page_idx]
            annots = list(pdf_page.annots()) if pdf_page.annots() else []
            page.has_annotations = len(annots) > 0

            # Handwriting detection is deferred to Stage 3 (VLM)
            # For now, flag scanned pages as potentially having handwriting
            page.has_handwriting = page.page_type == PageType.SCANNED

            pdf_doc.close()

    await db.commit()
    logger.info(f"Stage 2 complete for job {job_id}")
    return True
```

- [ ] **Step 4: Create app/pipeline/stage_3_extraction.py**

```python
# docdiff-service/app/pipeline/stage_3_extraction.py
import logging
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.base import AIProvider
from app.ai.response_parser import safe_parse_or_flag
from app.models.document import Document, DocumentPage, PageProcessingStatus, PageType
from app.pdf.parser import parse_document_with_docling
from app.prompts.extract_page import get_extract_prompt

logger = logging.getLogger("docdiff.pipeline")


async def run_stage_3(
    job_id: uuid.UUID, db: AsyncSession, ai_provider: AIProvider
) -> bool:
    """Stage 3: Structured Extraction.

    - Born-digital pages: use Docling for structural parsing
    - Scanned/mixed pages: use VLM for vision-based extraction
    - Pages with handwriting: send regions to VLM for transcription
    """
    result = await db.execute(
        select(Document).where(Document.job_id == job_id)
    )
    documents = result.scalars().all()

    for doc in documents:
        # First, try Docling for the entire document
        docling_pages: list[dict] = []
        try:
            docling_pages = parse_document_with_docling(doc.file_path)
        except Exception as e:
            logger.warning(f"Docling parsing failed for {doc.filename}: {e}")

        page_result = await db.execute(
            select(DocumentPage)
            .where(DocumentPage.document_id == doc.id)
            .order_by(DocumentPage.page_number)
        )
        pages = page_result.scalars().all()

        for page in pages:
            try:
                page_idx = page.page_number - 1

                if page.page_type == PageType.BORN_DIGITAL and page_idx < len(docling_pages):
                    # Use Docling output
                    page.content = docling_pages[page_idx]
                    page.extraction_method = "docling"
                    page.extraction_confidence = 0.95
                else:
                    # Use VLM for scanned/mixed pages or when Docling failed
                    if not page.image_path:
                        page.processing_status = PageProcessingStatus.FAILED
                        page.error_message = "No page image available for VLM extraction"
                        continue

                    with open(page.image_path, "rb") as f:
                        image_data = f.read()

                    prompt = get_extract_prompt(ai_provider.provider_name)
                    response = await ai_provider.extract_page_content(image_data, prompt)

                    parsed, needs_review = safe_parse_or_flag(response.content)
                    if parsed is None:
                        page.processing_status = PageProcessingStatus.FAILED
                        page.error_message = "Failed to parse VLM extraction response"
                        continue

                    page.content = parsed
                    page.extraction_method = "vlm"
                    page.extraction_confidence = 0.85 if not needs_review else 0.5

                page.processing_status = PageProcessingStatus.COMPLETED

            except Exception as e:
                logger.error(f"Stage 3 failed for page {page.page_number} of {doc.filename}: {e}")
                page.processing_status = PageProcessingStatus.FAILED
                page.error_message = str(e)

    await db.commit()
    logger.info(f"Stage 3 complete for job {job_id}")
    return True
```

- [ ] **Step 5: Create app/pipeline/stage_4_normalization.py**

```python
# docdiff-service/app/pipeline/stage_4_normalization.py
import logging
import re
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.document import Document, DocumentPage, PageProcessingStatus

logger = logging.getLogger("docdiff.pipeline")


async def run_stage_4(job_id: uuid.UUID, db: AsyncSession) -> bool:
    """Stage 4: Normalization.

    - Normalize extracted content into canonical format
    - Standardize table representations
    - Normalize whitespace and encoding
    - Assign unique IDs to every content block
    """
    result = await db.execute(
        select(Document).where(Document.job_id == job_id)
    )
    documents = result.scalars().all()

    global_block_counter = 0

    for doc in documents:
        page_result = await db.execute(
            select(DocumentPage)
            .where(DocumentPage.document_id == doc.id)
            .order_by(DocumentPage.page_number)
        )
        pages = page_result.scalars().all()

        for page in pages:
            if page.processing_status != PageProcessingStatus.COMPLETED:
                continue
            if not page.content:
                continue

            content = page.content
            blocks = content.get("blocks", [])

            # Normalize each block
            normalized_blocks = []
            for block in blocks:
                global_block_counter += 1
                new_id = f"{doc.role}_{page.page_number:03d}_blk_{global_block_counter:04d}"

                # Normalize text
                text = block.get("text", "")
                text = normalize_text(text)

                normalized = {
                    "id": new_id,
                    "type": block.get("type", "text"),
                    "bbox": block.get("bbox", {"x": 0, "y": 0, "width": 0, "height": 0}),
                    "text": text,
                }

                # Preserve table data
                if "table" in block and block["table"]:
                    table = block["table"]
                    # Normalize cell text
                    if "cells" in table:
                        for cell in table["cells"]:
                            cell["text"] = normalize_text(cell.get("text", ""))
                    normalized["table"] = table

                # Preserve annotation data
                if "annotation" in block and block["annotation"]:
                    normalized["annotation"] = block["annotation"]

                # Preserve section hierarchy
                if "section_level" in block:
                    normalized["section_level"] = block["section_level"]
                if "section_title" in block:
                    normalized["section_title"] = normalize_text(block.get("section_title", ""))

                normalized_blocks.append(normalized)

            # Update content with normalized blocks
            content["blocks"] = normalized_blocks
            content["reading_order"] = [b["id"] for b in normalized_blocks]
            page.content = content

    await db.commit()
    logger.info(f"Stage 4 complete for job {job_id}")
    return True


def normalize_text(text: str) -> str:
    """Normalize text: whitespace, encoding, line breaks."""
    if not text:
        return ""
    # Normalize Unicode
    import unicodedata
    text = unicodedata.normalize("NFKC", text)
    # Normalize whitespace
    text = re.sub(r"\s+", " ", text)
    return text.strip()
```

- [ ] **Step 6: Commit**

```bash
git add docdiff-service/app/pipeline/
git commit -m "feat(docdiff): add pipeline stages 1-4 (ingestion, classification, extraction, normalization)"
```

---

## Task 12: Pipeline Stages 5-8 (Alignment, Diff, Scoring, Assembly)

**Files:**
- Create: `docdiff-service/app/pipeline/stage_5_alignment.py`
- Create: `docdiff-service/app/pipeline/stage_6_diff.py`
- Create: `docdiff-service/app/pipeline/stage_7_scoring.py`
- Create: `docdiff-service/app/pipeline/stage_8_assembly.py`

- [ ] **Step 1: Create app/pipeline/stage_5_alignment.py**

```python
# docdiff-service/app/pipeline/stage_5_alignment.py
import logging
import uuid
from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.document import Document, DocumentPage, DocumentRole, PageProcessingStatus
from app.utils.diff_utils import compute_similarity
from app.utils.table_utils import compute_table_similarity

logger = logging.getLogger("docdiff.pipeline")


@dataclass
class AlignedPair:
    """A pair of aligned content blocks from original and revised documents."""
    original_block: dict | None
    revised_block: dict | None
    original_page: int | None
    revised_page: int | None
    alignment_score: float


async def run_stage_5(job_id: uuid.UUID, db: AsyncSession) -> list[AlignedPair]:
    """Stage 5: Alignment.

    Match content blocks between original and revised documents using:
    - Section titles and heading hierarchy
    - Table captions and structural similarity
    - Text paragraph positional and content similarity
    - Identify unmatched blocks (new content or deleted content)
    """
    # Load pages for both documents
    result = await db.execute(
        select(Document).where(Document.job_id == job_id)
    )
    documents = {doc.role: doc for doc in result.scalars().all()}

    original_doc = documents.get(DocumentRole.ORIGINAL)
    revised_doc = documents.get(DocumentRole.REVISED)
    if not original_doc or not revised_doc:
        logger.error(f"Missing documents for job {job_id}")
        return []

    original_blocks = await _get_all_blocks(original_doc.id, db)
    revised_blocks = await _get_all_blocks(revised_doc.id, db)

    aligned_pairs = _align_blocks(original_blocks, revised_blocks)

    logger.info(
        f"Stage 5 complete for job {job_id}: "
        f"{len(aligned_pairs)} aligned pairs "
        f"({sum(1 for p in aligned_pairs if p.original_block and p.revised_block)} matched, "
        f"{sum(1 for p in aligned_pairs if not p.original_block)} added, "
        f"{sum(1 for p in aligned_pairs if not p.revised_block)} deleted)"
    )
    return aligned_pairs


async def _get_all_blocks(document_id: uuid.UUID, db: AsyncSession) -> list[dict]:
    """Get all content blocks from all pages of a document, with page context."""
    result = await db.execute(
        select(DocumentPage)
        .where(
            DocumentPage.document_id == document_id,
            DocumentPage.processing_status == PageProcessingStatus.COMPLETED,
        )
        .order_by(DocumentPage.page_number)
    )
    pages = result.scalars().all()

    all_blocks = []
    for page in pages:
        if not page.content or "blocks" not in page.content:
            continue
        for block in page.content["blocks"]:
            block["_page_number"] = page.page_number
            all_blocks.append(block)

    return all_blocks


def _align_blocks(
    original_blocks: list[dict], revised_blocks: list[dict]
) -> list[AlignedPair]:
    """Align blocks using a multi-pass strategy."""
    matched_original: set[str] = set()
    matched_revised: set[str] = set()
    pairs: list[AlignedPair] = []

    # Pass 1: Match by section title (exact or near match)
    for ob in original_blocks:
        if ob["id"] in matched_original:
            continue
        if ob.get("section_title"):
            best_match = None
            best_score = 0.0
            for rb in revised_blocks:
                if rb["id"] in matched_revised:
                    continue
                if rb.get("section_title"):
                    score = compute_similarity(ob["section_title"], rb["section_title"])
                    if score > best_score and score >= 0.7:
                        best_score = score
                        best_match = rb
            if best_match:
                pairs.append(AlignedPair(
                    original_block=ob, revised_block=best_match,
                    original_page=ob["_page_number"], revised_page=best_match["_page_number"],
                    alignment_score=best_score,
                ))
                matched_original.add(ob["id"])
                matched_revised.add(best_match["id"])

    # Pass 2: Match tables by structure similarity
    orig_tables = [b for b in original_blocks if b["type"] == "table" and b["id"] not in matched_original]
    rev_tables = [b for b in revised_blocks if b["type"] == "table" and b["id"] not in matched_revised]
    for ot in orig_tables:
        best_match = None
        best_score = 0.0
        for rt in rev_tables:
            if rt["id"] in matched_revised:
                continue
            if ot.get("table") and rt.get("table"):
                score = compute_table_similarity(ot["table"], rt["table"])
                if score > best_score and score >= 0.5:
                    best_score = score
                    best_match = rt
        if best_match:
            pairs.append(AlignedPair(
                original_block=ot, revised_block=best_match,
                original_page=ot["_page_number"], revised_page=best_match["_page_number"],
                alignment_score=best_score,
            ))
            matched_original.add(ot["id"])
            matched_revised.add(best_match["id"])

    # Pass 3: Match text blocks by content similarity (ordered by page/position)
    orig_text = [b for b in original_blocks if b["type"] == "text" and b["id"] not in matched_original]
    rev_text = [b for b in revised_blocks if b["type"] == "text" and b["id"] not in matched_revised]
    for ot in orig_text:
        best_match = None
        best_score = 0.0
        for rt in rev_text:
            if rt["id"] in matched_revised:
                continue
            score = compute_similarity(ot.get("text", ""), rt.get("text", ""))
            if score > best_score and score >= 0.4:
                best_score = score
                best_match = rt
        if best_match:
            pairs.append(AlignedPair(
                original_block=ot, revised_block=best_match,
                original_page=ot["_page_number"], revised_page=best_match["_page_number"],
                alignment_score=best_score,
            ))
            matched_original.add(ot["id"])
            matched_revised.add(best_match["id"])

    # Unmatched original blocks → deletions
    for ob in original_blocks:
        if ob["id"] not in matched_original:
            pairs.append(AlignedPair(
                original_block=ob, revised_block=None,
                original_page=ob["_page_number"], revised_page=None,
                alignment_score=0.0,
            ))

    # Unmatched revised blocks → additions
    for rb in revised_blocks:
        if rb["id"] not in matched_revised:
            pairs.append(AlignedPair(
                original_block=None, revised_block=rb,
                original_page=None, revised_page=rb["_page_number"],
                alignment_score=0.0,
            ))

    return pairs
```

- [ ] **Step 2: Create app/pipeline/stage_6_diff.py**

```python
# docdiff-service/app/pipeline/stage_6_diff.py
import logging
import uuid
from dataclasses import dataclass

from app.models.change import ChangeType
from app.pipeline.stage_5_alignment import AlignedPair
from app.utils.diff_utils import compute_text_diff
from app.utils.table_utils import compare_tables

logger = logging.getLogger("docdiff.pipeline")


@dataclass
class RawDiffRecord:
    """A raw diff record before scoring and classification."""
    change_type: ChangeType
    value_before: str
    value_after: str
    context: str
    page_original: int | None
    page_revised: int | None
    bbox_original: dict | None
    bbox_revised: dict | None
    block_id_original: str | None
    block_id_revised: str | None


def run_stage_6(aligned_pairs: list[AlignedPair]) -> list[RawDiffRecord]:
    """Stage 6: Diff Computation.

    For each aligned pair, compute specific differences:
    - Text diffs at the word level (diff-match-patch)
    - Table diffs at the cell level
    - Annotation diffs by presence/absence
    """
    diff_records: list[RawDiffRecord] = []

    for pair in aligned_pairs:
        ob = pair.original_block
        rb = pair.revised_block

        # Case 1: Deletion (original exists, revised doesn't)
        if ob and not rb:
            change_type = _deletion_type(ob)
            diff_records.append(RawDiffRecord(
                change_type=change_type,
                value_before=_block_text(ob),
                value_after="",
                context=_block_context(ob),
                page_original=pair.original_page,
                page_revised=None,
                bbox_original=ob.get("bbox"),
                bbox_revised=None,
                block_id_original=ob["id"],
                block_id_revised=None,
            ))
            continue

        # Case 2: Addition (revised exists, original doesn't)
        if rb and not ob:
            change_type = _addition_type(rb)
            diff_records.append(RawDiffRecord(
                change_type=change_type,
                value_before="",
                value_after=_block_text(rb),
                context=_block_context(rb),
                page_original=None,
                page_revised=pair.revised_page,
                bbox_original=None,
                bbox_revised=rb.get("bbox"),
                block_id_original=None,
                block_id_revised=rb["id"],
            ))
            continue

        # Case 3: Both exist — compute specific diffs
        if ob and rb:
            if ob["type"] == "table" and rb["type"] == "table":
                # Table comparison
                table_diffs = _diff_tables(ob, rb, pair)
                diff_records.extend(table_diffs)
            elif ob.get("annotation") or rb.get("annotation"):
                # Annotation comparison
                annot_diffs = _diff_annotations(ob, rb, pair)
                diff_records.extend(annot_diffs)
            else:
                # Text comparison
                text_diffs = _diff_text(ob, rb, pair)
                diff_records.extend(text_diffs)

    logger.info(f"Stage 6 computed {len(diff_records)} raw diff records")
    return diff_records


def _diff_text(ob: dict, rb: dict, pair: AlignedPair) -> list[RawDiffRecord]:
    text_a = ob.get("text", "")
    text_b = rb.get("text", "")
    if text_a == text_b:
        return []

    diffs = compute_text_diff(text_a, text_b)
    records = []
    for d in diffs:
        if d.diff_type == "addition":
            ct = ChangeType.TEXT_ADDITION
        elif d.diff_type == "deletion":
            ct = ChangeType.TEXT_DELETION
        else:
            ct = ChangeType.TEXT_MODIFICATION

        records.append(RawDiffRecord(
            change_type=ct,
            value_before=d.value_before,
            value_after=d.value_after,
            context=text_a[:200],
            page_original=pair.original_page,
            page_revised=pair.revised_page,
            bbox_original=ob.get("bbox"),
            bbox_revised=rb.get("bbox"),
            block_id_original=ob["id"],
            block_id_revised=rb["id"],
        ))
    return records


def _diff_tables(ob: dict, rb: dict, pair: AlignedPair) -> list[RawDiffRecord]:
    table_a = ob.get("table", {})
    table_b = rb.get("table", {})
    if not table_a or not table_b:
        return []

    table_diff = compare_tables(table_a, table_b)
    records = []

    # Structure changes
    if table_diff.structure_changed:
        records.append(RawDiffRecord(
            change_type=ChangeType.TABLE_STRUCTURE_CHANGE,
            value_before=f"{table_a.get('rows')}x{table_a.get('cols')}",
            value_after=f"{table_b.get('rows')}x{table_b.get('cols')}",
            context=f"Table structure: {' | '.join(table_a.get('headers', []))}",
            page_original=pair.original_page,
            page_revised=pair.revised_page,
            bbox_original=ob.get("bbox"),
            bbox_revised=rb.get("bbox"),
            block_id_original=ob["id"],
            block_id_revised=rb["id"],
        ))

    # Cell changes
    for cell in table_diff.cell_changes:
        if cell.diff_type == "added":
            ct = ChangeType.TABLE_ROW_ADDITION
        elif cell.diff_type == "deleted":
            ct = ChangeType.TABLE_ROW_DELETION
        else:
            ct = ChangeType.TABLE_CELL_CHANGE

        headers = table_a.get("headers", [])
        col_name = headers[cell.col] if cell.col < len(headers) else f"Col {cell.col}"

        records.append(RawDiffRecord(
            change_type=ct,
            value_before=cell.value_before,
            value_after=cell.value_after,
            context=f"Table row {cell.row}, column '{col_name}'",
            page_original=pair.original_page,
            page_revised=pair.revised_page,
            bbox_original=ob.get("bbox"),
            bbox_revised=rb.get("bbox"),
            block_id_original=ob["id"],
            block_id_revised=rb["id"],
        ))

    # Row additions/deletions
    for row in table_diff.rows_added:
        records.append(RawDiffRecord(
            change_type=ChangeType.TABLE_ROW_ADDITION,
            value_before="",
            value_after=f"Row {row}",
            context=f"New row added at position {row}",
            page_original=pair.original_page,
            page_revised=pair.revised_page,
            bbox_original=ob.get("bbox"),
            bbox_revised=rb.get("bbox"),
            block_id_original=ob["id"],
            block_id_revised=rb["id"],
        ))

    for row in table_diff.rows_deleted:
        records.append(RawDiffRecord(
            change_type=ChangeType.TABLE_ROW_DELETION,
            value_before=f"Row {row}",
            value_after="",
            context=f"Row deleted from position {row}",
            page_original=pair.original_page,
            page_revised=pair.revised_page,
            bbox_original=ob.get("bbox"),
            bbox_revised=rb.get("bbox"),
            block_id_original=ob["id"],
            block_id_revised=rb["id"],
        ))

    return records


def _diff_annotations(ob: dict, rb: dict, pair: AlignedPair) -> list[RawDiffRecord]:
    annot_a = ob.get("annotation")
    annot_b = rb.get("annotation")

    if annot_b and not annot_a:
        return [RawDiffRecord(
            change_type=ChangeType.ANNOTATION_ADDED,
            value_before="",
            value_after=annot_b.get("transcription", "(annotation)"),
            context=f"Annotation type: {annot_b.get('type', 'unknown')}",
            page_original=pair.original_page,
            page_revised=pair.revised_page,
            bbox_original=ob.get("bbox"),
            bbox_revised=rb.get("bbox"),
            block_id_original=ob["id"],
            block_id_revised=rb["id"],
        )]

    if annot_a and not annot_b:
        return [RawDiffRecord(
            change_type=ChangeType.ANNOTATION_REMOVED,
            value_before=annot_a.get("transcription", "(annotation)"),
            value_after="",
            context=f"Annotation type: {annot_a.get('type', 'unknown')}",
            page_original=pair.original_page,
            page_revised=pair.revised_page,
            bbox_original=ob.get("bbox"),
            bbox_revised=rb.get("bbox"),
            block_id_original=ob["id"],
            block_id_revised=rb["id"],
        )]

    return []


def _block_text(block: dict) -> str:
    if block["type"] == "table":
        headers = block.get("table", {}).get("headers", [])
        return f"Table: {' | '.join(headers)}"
    return block.get("text", "")


def _block_context(block: dict) -> str:
    section = block.get("section_title", "")
    if section:
        return f"Section: {section}"
    return block.get("text", "")[:200]


def _deletion_type(block: dict) -> ChangeType:
    if block["type"] == "table":
        return ChangeType.TABLE_ROW_DELETION
    if block.get("annotation"):
        return ChangeType.ANNOTATION_REMOVED
    return ChangeType.TEXT_DELETION


def _addition_type(block: dict) -> ChangeType:
    if block["type"] == "table":
        return ChangeType.TABLE_ROW_ADDITION
    if block.get("annotation"):
        return ChangeType.ANNOTATION_ADDED
    return ChangeType.TEXT_ADDITION
```

- [ ] **Step 3: Create app/pipeline/stage_7_scoring.py**

```python
# docdiff-service/app/pipeline/stage_7_scoring.py
import logging

from app.ai.base import AIProvider
from app.ai.response_parser import safe_parse_or_flag
from app.models.change import ChangeType, Significance
from app.pipeline.stage_6_diff import RawDiffRecord
from app.prompts.classify_change import get_classify_prompt

logger = logging.getLogger("docdiff.pipeline")


# Changes that are always cosmetic (no AI needed)
COSMETIC_PATTERNS = {ChangeType.FORMATTING_CHANGE}

# Changes that are likely material (high confidence without AI)
LIKELY_MATERIAL = {
    ChangeType.TABLE_CELL_CHANGE,
    ChangeType.TABLE_STRUCTURE_CHANGE,
}


async def run_stage_7(
    diff_records: list[RawDiffRecord],
    ai_provider: AIProvider,
    confidence_threshold: float = 0.75,
) -> list[dict]:
    """Stage 7: Confidence Scoring + Significance Classification.

    For each diff record:
    - Assign confidence based on extraction quality and change clarity
    - Classify significance using heuristics first, AI for ambiguous cases
    - Flag low-confidence items for human review
    """
    scored_changes: list[dict] = []

    for i, record in enumerate(diff_records):
        confidence = _base_confidence(record)
        significance = _heuristic_significance(record)
        needs_human_review = False
        summary = _generate_summary(record)

        # Use AI for ambiguous classifications
        if significance == Significance.UNCERTAIN and ai_provider:
            try:
                prompt = get_classify_prompt(
                    provider=ai_provider.provider_name,
                    change_type=record.change_type.value,
                    value_before=record.value_before,
                    value_after=record.value_after,
                    context=record.context,
                )
                response = await ai_provider.classify_change(record.context, prompt)
                parsed, flagged = safe_parse_or_flag(response.content)
                if parsed and not flagged:
                    sig_str = parsed.get("significance", "uncertain")
                    try:
                        significance = Significance(sig_str)
                    except ValueError:
                        significance = Significance.UNCERTAIN
                    ai_confidence = parsed.get("confidence", 0.5)
                    confidence = min(confidence, ai_confidence)
                    reasoning = parsed.get("reasoning", "")
                    if reasoning:
                        summary = f"{summary} — {reasoning}"
            except Exception as e:
                logger.warning(f"AI classification failed for change {i}: {e}")
                significance = Significance.UNCERTAIN

        # Flag for human review if low confidence
        if confidence < confidence_threshold:
            needs_human_review = True

        scored_changes.append({
            "change_number": i + 1,
            "change_type": record.change_type,
            "significance": significance,
            "confidence": round(confidence, 3),
            "page_original": record.page_original,
            "page_revised": record.page_revised,
            "bbox_original": record.bbox_original,
            "bbox_revised": record.bbox_revised,
            "value_before": record.value_before,
            "value_after": record.value_after,
            "context": record.context,
            "summary": summary,
            "block_id_original": record.block_id_original,
            "block_id_revised": record.block_id_revised,
            "needs_human_review": needs_human_review,
            "auto_accepted": confidence >= 0.95 and significance != Significance.UNCERTAIN,
        })

    logger.info(
        f"Stage 7 scored {len(scored_changes)} changes: "
        f"{sum(1 for c in scored_changes if c['auto_accepted'])} auto-accepted, "
        f"{sum(1 for c in scored_changes if c['needs_human_review'])} need review"
    )
    return scored_changes


def _base_confidence(record: RawDiffRecord) -> float:
    """Assign base confidence from change characteristics."""
    if record.change_type in (ChangeType.TABLE_CELL_CHANGE, ChangeType.TEXT_MODIFICATION):
        if record.value_before and record.value_after:
            return 0.92
    if record.change_type in (ChangeType.TEXT_ADDITION, ChangeType.TEXT_DELETION):
        return 0.88
    if record.change_type in (ChangeType.ANNOTATION_ADDED, ChangeType.ANNOTATION_REMOVED):
        return 0.70
    return 0.80


def _heuristic_significance(record: RawDiffRecord) -> Significance:
    """Quick heuristic classification before AI."""
    if record.change_type in COSMETIC_PATTERNS:
        return Significance.COSMETIC
    if record.change_type in LIKELY_MATERIAL:
        return Significance.MATERIAL
    if record.change_type in (ChangeType.ANNOTATION_ADDED, ChangeType.ANNOTATION_REMOVED):
        return Significance.UNCERTAIN

    # Check for numeric changes (likely material)
    before = record.value_before or ""
    after = record.value_after or ""
    if _has_numeric_change(before, after):
        return Significance.MATERIAL

    # Default to uncertain for AI classification
    return Significance.UNCERTAIN


def _has_numeric_change(before: str, after: str) -> bool:
    """Check if the change involves numeric values."""
    import re
    nums_before = set(re.findall(r"\d+\.?\d*", before))
    nums_after = set(re.findall(r"\d+\.?\d*", after))
    return nums_before != nums_after


def _generate_summary(record: RawDiffRecord) -> str:
    """Generate a brief human-readable summary of the change."""
    ct = record.change_type.value.replace("_", " ").title()
    before = (record.value_before or "")[:80]
    after = (record.value_after or "")[:80]

    if record.change_type in (ChangeType.TEXT_MODIFICATION, ChangeType.TABLE_CELL_CHANGE):
        return f"{ct}: '{before}' → '{after}'"
    if record.change_type in (ChangeType.TEXT_ADDITION, ChangeType.TABLE_ROW_ADDITION, ChangeType.ANNOTATION_ADDED):
        return f"{ct}: '{after}'"
    if record.change_type in (ChangeType.TEXT_DELETION, ChangeType.TABLE_ROW_DELETION, ChangeType.ANNOTATION_REMOVED):
        return f"{ct}: '{before}'"
    return f"{ct}"
```

- [ ] **Step 4: Create app/pipeline/stage_8_assembly.py**

```python
# docdiff-service/app/pipeline/stage_8_assembly.py
import logging
import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.change import DetectedChange, ReviewStatus, Significance
from app.models.job import ComparisonJob, JobStatus

logger = logging.getLogger("docdiff.pipeline")


async def run_stage_8(
    job_id: uuid.UUID,
    scored_changes: list[dict],
    db: AsyncSession,
) -> bool:
    """Stage 8: Result Assembly.

    - Save all scored changes to the database
    - Update job with total counts
    - Mark job as ready for review
    """
    from sqlalchemy import select

    result = await db.execute(select(ComparisonJob).where(ComparisonJob.id == job_id))
    job = result.scalar_one_or_none()
    if not job:
        logger.error(f"Job {job_id} not found")
        return False

    # Save changes
    for change_data in scored_changes:
        change = DetectedChange(
            job_id=job_id,
            change_number=change_data["change_number"],
            change_type=change_data["change_type"],
            significance=change_data["significance"],
            confidence=change_data["confidence"],
            page_original=change_data["page_original"],
            page_revised=change_data["page_revised"],
            bbox_original=change_data["bbox_original"],
            bbox_revised=change_data["bbox_revised"],
            value_before=change_data["value_before"],
            value_after=change_data["value_after"],
            context=change_data["context"],
            summary=change_data["summary"],
            block_id_original=change_data["block_id_original"],
            block_id_revised=change_data["block_id_revised"],
            review_status=ReviewStatus.ACCEPTED if change_data["auto_accepted"] else ReviewStatus.PENDING,
            auto_accepted=change_data["auto_accepted"],
            needs_human_review=change_data["needs_human_review"],
        )
        db.add(change)

    # Update job
    auto_accepted = sum(1 for c in scored_changes if c["auto_accepted"])
    job.total_changes = len(scored_changes)
    job.changes_reviewed = auto_accepted
    job.status = JobStatus.READY_FOR_REVIEW

    await db.commit()
    logger.info(
        f"Stage 8 complete for job {job_id}: "
        f"{len(scored_changes)} changes saved, {auto_accepted} auto-accepted"
    )
    return True
```

- [ ] **Step 5: Commit**

```bash
git add docdiff-service/app/pipeline/
git commit -m "feat(docdiff): add pipeline stages 5-8 (alignment, diff, scoring, assembly)"
```

---

## Task 13: Pipeline Orchestrator + ARQ Worker

**Files:**
- Create: `docdiff-service/app/pipeline/orchestrator.py`
- Create: `docdiff-service/app/workers/__init__.py`
- Create: `docdiff-service/app/workers/job_worker.py`
- Modify: `docdiff-service/app/api/jobs.py` (wire up ARQ enqueue)
- Modify: `docdiff-service/app/main.py` (add Redis to lifespan)

- [ ] **Step 1: Create app/pipeline/orchestrator.py**

```python
# docdiff-service/app/pipeline/orchestrator.py
import logging
import time
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.router import get_provider
from app.config import settings
from app.database import async_session_factory
from app.models.job import ComparisonJob, JobStatus
from app.pipeline.stage_1_ingestion import run_stage_1
from app.pipeline.stage_2_classification import run_stage_2
from app.pipeline.stage_3_extraction import run_stage_3
from app.pipeline.stage_4_normalization import run_stage_4
from app.pipeline.stage_5_alignment import run_stage_5
from app.pipeline.stage_6_diff import run_stage_6
from app.pipeline.stage_7_scoring import run_stage_7
from app.pipeline.stage_8_assembly import run_stage_8

logger = logging.getLogger("docdiff.pipeline")

# In-memory progress store for SSE
_job_progress: dict[str, dict] = {}


def get_job_progress(job_id: str) -> dict | None:
    return _job_progress.get(job_id)


STAGE_STATUS_MAP = {
    1: JobStatus.PARSING_ORIGINAL,
    2: JobStatus.PARSING_REVISED,
    3: JobStatus.PARSING_REVISED,
    4: JobStatus.ALIGNING,
    5: JobStatus.ALIGNING,
    6: JobStatus.DIFFING,
    7: JobStatus.CLASSIFYING,
    8: JobStatus.ASSEMBLING,
}


async def run_pipeline(job_id: str) -> None:
    """Run the full 8-stage pipeline for a comparison job."""
    uid = uuid.UUID(job_id)
    start_time = time.time()

    progress = {
        "job_id": job_id,
        "status": "processing",
        "current_stage": 0,
        "stages": {},
    }
    _job_progress[job_id] = progress

    async with async_session_factory() as db:
        try:
            # Get job details for AI provider
            result = await db.execute(select(ComparisonJob).where(ComparisonJob.id == uid))
            job = result.scalar_one_or_none()
            if not job:
                logger.error(f"Job {job_id} not found")
                return

            ai_provider = get_provider(job.model_provider, job.model_name)

            stages = [
                (1, "Ingestion & Validation", lambda: run_stage_1(uid, db)),
                (2, "Page Classification", lambda: run_stage_2(uid, db)),
                (3, "Content Extraction", lambda: run_stage_3(uid, db, ai_provider)),
                (4, "Normalization", lambda: run_stage_4(uid, db)),
            ]

            # Run stages 1-4
            for stage_num, stage_name, stage_fn in stages:
                # Check for cancellation
                await db.refresh(job)
                if job.status == JobStatus.CANCELLED:
                    progress["status"] = "cancelled"
                    return

                _update_progress(progress, stage_num, "in_progress", stage_name)
                job.current_stage = stage_num
                job.status = STAGE_STATUS_MAP.get(stage_num, JobStatus.PARSING_ORIGINAL)
                job.stage_progress = dict(progress["stages"])
                await db.commit()

                success = await stage_fn()
                if not success:
                    _update_progress(progress, stage_num, "failed", stage_name)
                    job.status = JobStatus.FAILED
                    await db.commit()
                    progress["status"] = "failed"
                    return

                _update_progress(progress, stage_num, "completed", stage_name)

            # Stage 5: Alignment
            _update_progress(progress, 5, "in_progress", "Section Alignment")
            job.current_stage = 5
            job.status = JobStatus.ALIGNING
            await db.commit()
            aligned_pairs = await run_stage_5(uid, db)
            _update_progress(progress, 5, "completed", "Section Alignment")

            # Stage 6: Diff
            _update_progress(progress, 6, "in_progress", "Computing Differences")
            job.current_stage = 6
            job.status = JobStatus.DIFFING
            await db.commit()
            diff_records = run_stage_6(aligned_pairs)
            _update_progress(progress, 6, "completed", "Computing Differences")

            # Stage 7: Scoring
            _update_progress(progress, 7, "in_progress", "Classifying Changes")
            job.current_stage = 7
            job.status = JobStatus.CLASSIFYING
            await db.commit()
            scored_changes = await run_stage_7(
                diff_records, ai_provider, settings.confidence_threshold
            )
            _update_progress(progress, 7, "completed", "Classifying Changes")

            # Stage 8: Assembly
            _update_progress(progress, 8, "in_progress", "Assembling Results")
            job.current_stage = 8
            job.status = JobStatus.ASSEMBLING
            await db.commit()
            success = await run_stage_8(uid, scored_changes, db)
            _update_progress(progress, 8, "completed", "Assembling Results")

            # Done
            elapsed = int((time.time() - start_time) * 1000)
            await db.refresh(job)
            job.processing_time_ms = elapsed
            await db.commit()

            progress["status"] = "ready_for_review"
            logger.info(f"Pipeline complete for job {job_id} in {elapsed}ms")

        except Exception as e:
            logger.exception(f"Pipeline failed for job {job_id}: {e}")
            job.status = JobStatus.FAILED
            job.error_message = str(e)
            await db.commit()
            progress["status"] = "failed"
            progress["error"] = str(e)


def _update_progress(progress: dict, stage: int, status: str, name: str) -> None:
    progress["current_stage"] = stage
    progress["stages"][str(stage)] = {"status": status, "name": name}
```

- [ ] **Step 2: Create app/workers/__init__.py and job_worker.py**

```python
# docdiff-service/app/workers/__init__.py
```

```python
# docdiff-service/app/workers/job_worker.py
import logging

from arq import create_pool
from arq.connections import RedisSettings

from app.config import settings
from app.pipeline.orchestrator import run_pipeline

logger = logging.getLogger("docdiff.worker")


async def process_comparison_job(ctx: dict, job_id: str) -> None:
    """ARQ task: run the full comparison pipeline for a job."""
    logger.info(f"Worker picked up job {job_id}")
    await run_pipeline(job_id)
    logger.info(f"Worker finished job {job_id}")


class WorkerSettings:
    """ARQ worker configuration."""
    functions = [process_comparison_job]
    redis_settings = RedisSettings.from_dsn(settings.redis_url)
    max_jobs = 1  # Process one job at a time (prototype)
    job_timeout = 600  # 10 minute timeout per job


async def enqueue_job(job_id: str) -> None:
    """Enqueue a comparison job to the ARQ worker."""
    redis = await create_pool(RedisSettings.from_dsn(settings.redis_url))
    await redis.enqueue_job("process_comparison_job", job_id)
    await redis.close()
```

- [ ] **Step 3: Update app/api/jobs.py start_job to enqueue ARQ task**

In `app/api/jobs.py`, update the `start_job` endpoint. Replace the comment `# For now, just update status` with actual ARQ enqueue:

```python
@router.post("/{job_id}/start")
async def start_job(job_id: uuid.UUID, db: DbSession, user: CurrentUser):
    """Start processing a job."""
    result = await db.execute(select(ComparisonJob).where(ComparisonJob.id == job_id))
    job = result.scalar_one_or_none()
    if not job:
        raise HTTPException(404, "Job not found")
    if job.status != JobStatus.UPLOADING:
        raise HTTPException(400, f"Job cannot be started from status: {job.status}")

    job.status = JobStatus.PARSING_ORIGINAL
    job.current_stage = 1
    job.stage_progress = {"1": "in_progress"}
    await db.commit()

    # Enqueue to ARQ worker
    from app.workers.job_worker import enqueue_job
    await enqueue_job(str(job_id))

    await db.refresh(job)
    return SuccessResponse(data=JobResponse.model_validate(job), message="Processing started")
```

- [ ] **Step 4: Commit**

```bash
git add docdiff-service/app/pipeline/orchestrator.py docdiff-service/app/workers/ docdiff-service/app/api/jobs.py
git commit -m "feat(docdiff): add pipeline orchestrator, ARQ worker, and job enqueue"
```

---

## Task 14: SSE Progress Endpoint + Changes/Reports API

**Files:**
- Create: `docdiff-service/app/api/sse.py`
- Create: `docdiff-service/app/api/changes.py`
- Create: `docdiff-service/app/api/reports.py`
- Create: `docdiff-service/app/api/documents.py`
- Create: `docdiff-service/app/api/api_keys.py`
- Create: `docdiff-service/app/pdf/report_generator.py`
- Modify: `docdiff-service/app/api/router.py` (mount all routers)

- [ ] **Step 1: Create app/api/sse.py**

```python
# docdiff-service/app/api/sse.py
import asyncio
import json
import uuid

from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse

from app.api.deps import CurrentUser
from app.pipeline.orchestrator import get_job_progress

router = APIRouter(prefix="/jobs", tags=["sse"])


@router.get("/{job_id}/progress")
async def job_progress_sse(job_id: uuid.UUID, request: Request):
    """SSE endpoint for real-time processing progress updates."""

    async def event_stream():
        job_id_str = str(job_id)
        while True:
            if await request.is_disconnected():
                break

            progress = get_job_progress(job_id_str)
            if progress:
                data = json.dumps(progress)
                yield f"data: {data}\n\n"

                if progress.get("status") in ("ready_for_review", "failed", "cancelled"):
                    break
            else:
                yield f"data: {json.dumps({'status': 'waiting', 'job_id': job_id_str})}\n\n"

            await asyncio.sleep(1)

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
```

- [ ] **Step 2: Create app/api/changes.py**

```python
# docdiff-service/app/api/changes.py
import uuid
from datetime import datetime

from fastapi import APIRouter, HTTPException, Query
from sqlalchemy import select, func

from app.api.deps import CurrentUser, DbSession
from app.models.change import DetectedChange, ReviewStatus
from app.models.job import ComparisonJob
from app.schemas.change import BulkReviewAction, ChangeResponse, ManualChangeCreate, ReviewAction
from app.schemas.common import SuccessResponse

router = APIRouter(prefix="/jobs/{job_id}/changes", tags=["changes"])


@router.get("", response_model=SuccessResponse[list[ChangeResponse]])
async def list_changes(
    job_id: uuid.UUID,
    db: DbSession,
    user: CurrentUser,
    change_type: str | None = None,
    significance: str | None = None,
    confidence_min: float | None = None,
    confidence_max: float | None = None,
    review_status: str | None = None,
    page: int | None = None,
    needs_human_review: bool | None = None,
):
    """List all detected changes for a job with optional filters."""
    query = select(DetectedChange).where(DetectedChange.job_id == job_id)

    if change_type:
        query = query.where(DetectedChange.change_type == change_type)
    if significance:
        query = query.where(DetectedChange.significance == significance)
    if confidence_min is not None:
        query = query.where(DetectedChange.confidence >= confidence_min)
    if confidence_max is not None:
        query = query.where(DetectedChange.confidence <= confidence_max)
    if review_status:
        query = query.where(DetectedChange.review_status == review_status)
    if page is not None:
        query = query.where(
            (DetectedChange.page_original == page) | (DetectedChange.page_revised == page)
        )
    if needs_human_review is not None:
        query = query.where(DetectedChange.needs_human_review == needs_human_review)

    query = query.order_by(DetectedChange.change_number)
    result = await db.execute(query)
    changes = result.scalars().all()

    return SuccessResponse(data=[ChangeResponse.model_validate(c) for c in changes])


@router.get("/{change_id}", response_model=SuccessResponse[ChangeResponse])
async def get_change(
    job_id: uuid.UUID, change_id: uuid.UUID, db: DbSession, user: CurrentUser
):
    result = await db.execute(
        select(DetectedChange).where(
            DetectedChange.id == change_id, DetectedChange.job_id == job_id
        )
    )
    change = result.scalar_one_or_none()
    if not change:
        raise HTTPException(404, "Change not found")
    return SuccessResponse(data=ChangeResponse.model_validate(change))


@router.patch("/{change_id}", response_model=SuccessResponse[ChangeResponse])
async def review_change(
    job_id: uuid.UUID,
    change_id: uuid.UUID,
    action: ReviewAction,
    db: DbSession,
    user: CurrentUser,
):
    """Review a change: accept, reject, edit, or escalate."""
    result = await db.execute(
        select(DetectedChange).where(
            DetectedChange.id == change_id, DetectedChange.job_id == job_id
        )
    )
    change = result.scalar_one_or_none()
    if not change:
        raise HTTPException(404, "Change not found")

    change.review_status = action.action
    change.reviewer_comment = action.comment
    change.reviewed_at = datetime.utcnow()

    if action.edited_summary:
        change.summary = action.edited_summary
    if action.edited_significance:
        change.significance = action.edited_significance
    if action.edited_value_after is not None:
        change.value_after = action.edited_value_after

    # Update job reviewed count
    job_result = await db.execute(select(ComparisonJob).where(ComparisonJob.id == job_id))
    job = job_result.scalar_one_or_none()
    if job:
        reviewed_count = await db.execute(
            select(func.count()).where(
                DetectedChange.job_id == job_id,
                DetectedChange.review_status != ReviewStatus.PENDING,
            )
        )
        job.changes_reviewed = reviewed_count.scalar() or 0

    await db.commit()
    await db.refresh(change)
    return SuccessResponse(data=ChangeResponse.model_validate(change), message="Change reviewed")


@router.patch("/bulk", response_model=SuccessResponse[dict])
async def bulk_review(
    job_id: uuid.UUID,
    action: BulkReviewAction,
    db: DbSession,
    user: CurrentUser,
):
    """Bulk review multiple changes."""
    from sqlalchemy import update
    await db.execute(
        update(DetectedChange)
        .where(
            DetectedChange.job_id == job_id,
            DetectedChange.id.in_(action.change_ids),
        )
        .values(
            review_status=action.action,
            reviewer_comment=action.comment,
            reviewed_at=datetime.utcnow(),
        )
    )
    await db.commit()
    return SuccessResponse(
        data={"updated": len(action.change_ids)},
        message=f"Bulk {action.action.value} applied to {len(action.change_ids)} changes",
    )


@router.post("", response_model=SuccessResponse[ChangeResponse])
async def add_manual_change(
    job_id: uuid.UUID,
    data: ManualChangeCreate,
    db: DbSession,
    user: CurrentUser,
):
    """Add a manual change (for unresolved regions)."""
    # Get next change number
    result = await db.execute(
        select(func.max(DetectedChange.change_number)).where(DetectedChange.job_id == job_id)
    )
    max_num = result.scalar() or 0

    change = DetectedChange(
        job_id=job_id,
        change_number=max_num + 1,
        change_type=data.change_type,
        significance=data.significance,
        confidence=1.0,  # Manual = full confidence
        page_original=data.page_original,
        page_revised=data.page_revised,
        value_before=data.value_before,
        value_after=data.value_after,
        summary=data.summary,
        review_status=ReviewStatus.ACCEPTED,
        auto_accepted=False,
        needs_human_review=False,
    )
    db.add(change)
    await db.commit()
    await db.refresh(change)
    return SuccessResponse(data=ChangeResponse.model_validate(change), message="Manual change added")
```

- [ ] **Step 3: Create app/api/documents.py**

```python
# docdiff-service/app/api/documents.py
import uuid

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy import select

from app.api.deps import CurrentUser, DbSession
from app.models.document import Document, DocumentPage, DocumentRole
from app.schemas.document import DocumentResponse, PageContentResponse
from app.schemas.common import SuccessResponse

router = APIRouter(prefix="/jobs/{job_id}/documents", tags=["documents"])


@router.get("/{role}/pages/{page_num}/image")
async def get_page_image(
    job_id: uuid.UUID,
    role: str,
    page_num: int,
    db: DbSession,
    user: CurrentUser,
):
    """Get rendered page image."""
    doc_role = DocumentRole(role)
    result = await db.execute(
        select(Document).where(Document.job_id == job_id, Document.role == doc_role)
    )
    doc = result.scalar_one_or_none()
    if not doc:
        raise HTTPException(404, "Document not found")

    page_result = await db.execute(
        select(DocumentPage).where(
            DocumentPage.document_id == doc.id, DocumentPage.page_number == page_num
        )
    )
    page = page_result.scalar_one_or_none()
    if not page or not page.image_path:
        raise HTTPException(404, "Page image not found")

    return FileResponse(page.image_path, media_type="image/png")


@router.get("/{role}/pages/{page_num}/content", response_model=SuccessResponse[PageContentResponse])
async def get_page_content(
    job_id: uuid.UUID,
    role: str,
    page_num: int,
    db: DbSession,
    user: CurrentUser,
):
    """Get parsed content JSON for a page."""
    doc_role = DocumentRole(role)
    result = await db.execute(
        select(Document).where(Document.job_id == job_id, Document.role == doc_role)
    )
    doc = result.scalar_one_or_none()
    if not doc:
        raise HTTPException(404, "Document not found")

    page_result = await db.execute(
        select(DocumentPage).where(
            DocumentPage.document_id == doc.id, DocumentPage.page_number == page_num
        )
    )
    page = page_result.scalar_one_or_none()
    if not page:
        raise HTTPException(404, "Page not found")

    return SuccessResponse(data=PageContentResponse.model_validate(page))
```

- [ ] **Step 4: Create app/pdf/report_generator.py**

```python
# docdiff-service/app/pdf/report_generator.py
import logging
import os
from datetime import datetime

from app.config import settings

logger = logging.getLogger("docdiff.pdf")

REPORT_CSS = """
body { font-family: 'Helvetica Neue', Arial, sans-serif; margin: 40px; color: #1a1a1a; }
h1 { color: #4338ca; border-bottom: 2px solid #4338ca; padding-bottom: 8px; }
h2 { color: #3730a3; margin-top: 32px; }
.summary-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 16px; margin: 20px 0; }
.summary-card { background: #f5f3ff; border-radius: 8px; padding: 16px; text-align: center; }
.summary-card .number { font-size: 28px; font-weight: bold; color: #4338ca; }
.summary-card .label { font-size: 12px; color: #6b7280; }
table { width: 100%; border-collapse: collapse; margin: 16px 0; }
th { background: #4338ca; color: white; padding: 10px; text-align: left; }
td { padding: 8px 10px; border-bottom: 1px solid #e5e7eb; }
tr:nth-child(even) { background: #f9fafb; }
.material { color: #dc2626; font-weight: bold; }
.substantive { color: #d97706; }
.cosmetic { color: #2563eb; }
.uncertain { color: #7c3aed; }
.change-before { background: #fef2f2; padding: 4px 8px; border-radius: 4px; text-decoration: line-through; }
.change-after { background: #f0fdf4; padding: 4px 8px; border-radius: 4px; }
.footer { margin-top: 40px; border-top: 1px solid #e5e7eb; padding-top: 16px; color: #9ca3af; font-size: 12px; }
@page { margin: 2cm; @bottom-right { content: "Page " counter(page) " of " counter(pages); } }
"""


def generate_report_html(
    job_data: dict,
    changes: list[dict],
    documents: list[dict],
) -> str:
    """Generate HTML report from job data and changes."""
    stats = _compute_stats(changes)
    now = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")

    # Document info
    doc_info = ""
    for doc in documents:
        doc_info += f"<p><strong>{doc['role'].title()}:</strong> {doc['filename']} ({doc['page_count']} pages, {doc['file_size_bytes'] / 1024:.0f} KB)</p>"

    # Changes table
    rows = ""
    for c in changes:
        if c.get("review_status") == "rejected":
            continue
        sig_class = c.get("significance", "uncertain")
        before = f'<span class="change-before">{c.get("value_before", "")}</span>' if c.get("value_before") else "-"
        after = f'<span class="change-after">{c.get("value_after", "")}</span>' if c.get("value_after") else "-"
        rows += f"""<tr>
            <td>{c.get('change_number', '')}</td>
            <td>p.{c.get('page_original', '-')}/{c.get('page_revised', '-')}</td>
            <td>{c.get('change_type', '').replace('_', ' ').title()}</td>
            <td class="{sig_class}">{sig_class.title()}</td>
            <td>{c.get('confidence', 0):.0%}</td>
            <td>{before}</td>
            <td>{after}</td>
            <td>{c.get('summary', '')}</td>
            <td>{c.get('review_status', '').title()}</td>
        </tr>"""

    html = f"""<!DOCTYPE html>
<html>
<head><meta charset="utf-8"><title>DocDiff Pro Report</title>
<style>{REPORT_CSS}</style></head>
<body>
<h1>DocDiff Pro — Comparison Report</h1>
<p>Generated: {now}</p>
<p>Model: {job_data.get('model_provider', '')} / {job_data.get('model_name', '')}</p>
<p>Processing time: {(job_data.get('processing_time_ms', 0) or 0) / 1000:.1f}s</p>

<h2>Documents</h2>
{doc_info}

<h2>Summary</h2>
<div class="summary-grid">
    <div class="summary-card"><div class="number">{stats['total']}</div><div class="label">Total Changes</div></div>
    <div class="summary-card"><div class="number">{stats['material']}</div><div class="label">Material</div></div>
    <div class="summary-card"><div class="number">{stats['substantive']}</div><div class="label">Substantive</div></div>
    <div class="summary-card"><div class="number">{stats['cosmetic']}</div><div class="label">Cosmetic</div></div>
</div>
<p>Auto-accepted: {stats['auto_accepted']} | Manually reviewed: {stats['manually_reviewed']} | Rejected: {stats['rejected']} | Escalated: {stats['escalated']}</p>

<h2>Changes</h2>
<table>
<thead><tr><th>#</th><th>Page</th><th>Type</th><th>Significance</th><th>Confidence</th><th>Before</th><th>After</th><th>Summary</th><th>Status</th></tr></thead>
<tbody>{rows}</tbody>
</table>

<div class="footer">
    <p>Report generated by DocDiff Pro v0.1.0</p>
</div>
</body></html>"""

    return html


def html_to_pdf(html: str, output_path: str) -> str:
    """Convert HTML report to PDF using WeasyPrint."""
    from weasyprint import HTML
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    HTML(string=html).write_pdf(output_path)
    return output_path


def _compute_stats(changes: list[dict]) -> dict:
    stats = {
        "total": len(changes),
        "material": 0, "substantive": 0, "cosmetic": 0, "uncertain": 0,
        "auto_accepted": 0, "manually_reviewed": 0, "rejected": 0, "escalated": 0,
    }
    for c in changes:
        sig = c.get("significance", "uncertain")
        if sig in stats:
            stats[sig] += 1
        status = c.get("review_status", "pending")
        if c.get("auto_accepted"):
            stats["auto_accepted"] += 1
        elif status == "accepted":
            stats["manually_reviewed"] += 1
        elif status == "rejected":
            stats["rejected"] += 1
        elif status == "escalated":
            stats["escalated"] += 1
    return stats
```

- [ ] **Step 5: Create app/api/reports.py**

```python
# docdiff-service/app/api/reports.py
import os
import uuid

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy import select

from app.api.deps import CurrentUser, DbSession
from app.config import settings
from app.models.change import DetectedChange
from app.models.document import Document
from app.models.job import ComparisonJob, JobStatus
from app.models.report import DiffReport
from app.pdf.report_generator import generate_report_html, html_to_pdf
from app.schemas.common import SuccessResponse
from app.schemas.report import ReportResponse

router = APIRouter(prefix="/jobs/{job_id}/report", tags=["reports"])


@router.post("", response_model=SuccessResponse[ReportResponse])
async def generate_report(job_id: uuid.UUID, db: DbSession, user: CurrentUser):
    """Generate summary report for a completed review."""
    result = await db.execute(select(ComparisonJob).where(ComparisonJob.id == job_id))
    job = result.scalar_one_or_none()
    if not job:
        raise HTTPException(404, "Job not found")

    # Get changes
    changes_result = await db.execute(
        select(DetectedChange).where(DetectedChange.job_id == job_id).order_by(DetectedChange.change_number)
    )
    changes = changes_result.scalars().all()

    # Get documents
    docs_result = await db.execute(select(Document).where(Document.job_id == job_id))
    docs = docs_result.scalars().all()

    # Generate HTML
    job_data = {
        "model_provider": job.model_provider,
        "model_name": job.model_name,
        "processing_time_ms": job.processing_time_ms,
    }
    changes_data = [
        {
            "change_number": c.change_number,
            "change_type": c.change_type,
            "significance": c.significance,
            "confidence": c.confidence,
            "page_original": c.page_original,
            "page_revised": c.page_revised,
            "value_before": c.value_before,
            "value_after": c.value_after,
            "summary": c.summary,
            "review_status": c.review_status,
            "auto_accepted": c.auto_accepted,
        }
        for c in changes
    ]
    docs_data = [
        {"role": d.role, "filename": d.filename, "page_count": d.page_count, "file_size_bytes": d.file_size_bytes}
        for d in docs
    ]

    report_html = generate_report_html(job_data, changes_data, docs_data)

    # Generate PDF
    pdf_path = os.path.join(settings.storage_path, "reports", str(job_id), "report.pdf")
    html_to_pdf(report_html, pdf_path)

    # Save or update report record
    existing = await db.execute(select(DiffReport).where(DiffReport.job_id == job_id))
    report = existing.scalar_one_or_none()
    if report:
        report.report_html = report_html
        report.report_pdf_path = pdf_path
        report.summary_stats = _build_summary(changes_data)
    else:
        report = DiffReport(
            job_id=job_id,
            report_html=report_html,
            report_pdf_path=pdf_path,
            summary_stats=_build_summary(changes_data),
        )
        db.add(report)

    job.status = JobStatus.COMPLETED
    await db.commit()
    await db.refresh(report)

    return SuccessResponse(data=ReportResponse.model_validate(report), message="Report generated")


@router.get("", response_model=SuccessResponse[ReportResponse])
async def get_report(job_id: uuid.UUID, db: DbSession, user: CurrentUser):
    result = await db.execute(select(DiffReport).where(DiffReport.job_id == job_id))
    report = result.scalar_one_or_none()
    if not report:
        raise HTTPException(404, "Report not generated yet")
    return SuccessResponse(data=ReportResponse.model_validate(report))


@router.get("/pdf")
async def download_report_pdf(job_id: uuid.UUID, db: DbSession, user: CurrentUser):
    result = await db.execute(select(DiffReport).where(DiffReport.job_id == job_id))
    report = result.scalar_one_or_none()
    if not report or not report.report_pdf_path:
        raise HTTPException(404, "Report PDF not available")
    return FileResponse(report.report_pdf_path, media_type="application/pdf", filename="docdiff-report.pdf")


def _build_summary(changes: list[dict]) -> dict:
    from app.pdf.report_generator import _compute_stats
    return _compute_stats(changes)
```

- [ ] **Step 6: Create app/api/api_keys.py**

```python
# docdiff-service/app/api/api_keys.py
import uuid

from fastapi import APIRouter, HTTPException
from sqlalchemy import select

from app.api.deps import CurrentUser, DbSession
from app.auth.api_key import generate_api_key, hash_api_key
from app.models.api_key import APIKey
from app.schemas.common import SuccessResponse

router = APIRouter(prefix="/api-keys", tags=["api-keys"])


@router.post("")
async def create_api_key(name: str, db: DbSession, user: CurrentUser):
    """Create a new API key. JWT auth only."""
    if user.auth_method != "jwt":
        raise HTTPException(403, "API key creation requires JWT authentication")

    raw_key = generate_api_key()
    key = APIKey(
        key_hash=hash_api_key(raw_key),
        name=name,
    )
    db.add(key)
    await db.commit()
    await db.refresh(key)

    return SuccessResponse(
        data={"id": str(key.id), "key": raw_key, "name": key.name},
        message="API key created. Store the key securely — it cannot be retrieved again.",
    )


@router.get("")
async def list_api_keys(db: DbSession, user: CurrentUser):
    if user.auth_method != "jwt":
        raise HTTPException(403, "JWT authentication required")
    result = await db.execute(select(APIKey).order_by(APIKey.created_at.desc()))
    keys = result.scalars().all()
    return SuccessResponse(data=[
        {"id": str(k.id), "name": k.name, "is_active": k.is_active, "last_used_at": str(k.last_used_at) if k.last_used_at else None}
        for k in keys
    ])


@router.delete("/{key_id}")
async def revoke_api_key(key_id: uuid.UUID, db: DbSession, user: CurrentUser):
    if user.auth_method != "jwt":
        raise HTTPException(403, "JWT authentication required")
    result = await db.execute(select(APIKey).where(APIKey.id == key_id))
    key = result.scalar_one_or_none()
    if not key:
        raise HTTPException(404, "API key not found")
    key.is_active = False
    await db.commit()
    return SuccessResponse(data=None, message="API key revoked")
```

- [ ] **Step 7: Update app/api/router.py to mount all routers**

```python
# docdiff-service/app/api/router.py
from fastapi import APIRouter

from app.api.api_keys import router as api_keys_router
from app.api.changes import router as changes_router
from app.api.documents import router as documents_router
from app.api.health import router as health_router
from app.api.jobs import router as jobs_router
from app.api.reports import router as reports_router
from app.api.sse import router as sse_router

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(jobs_router)
api_router.include_router(sse_router)
api_router.include_router(changes_router)
api_router.include_router(documents_router)
api_router.include_router(reports_router)
api_router.include_router(api_keys_router)
```

- [ ] **Step 8: Commit**

```bash
git add docdiff-service/app/api/ docdiff-service/app/pdf/report_generator.py
git commit -m "feat(docdiff): add SSE progress, changes/reports/documents/api-keys endpoints"
```

---

## Task 15: Docker Setup

**Files:**
- Create: `docdiff-service/Dockerfile`
- Create: `docdiff-service/docker-compose.yml`

- [ ] **Step 1: Create Dockerfile**

```dockerfile
# docdiff-service/Dockerfile
FROM python:3.11-slim AS builder

WORKDIR /app

# System deps for WeasyPrint
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libcairo2-dev \
    libpango1.0-dev \
    libgdk-pixbuf2.0-dev \
    libffi-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

FROM python:3.11-slim

WORKDIR /app

# Runtime deps for WeasyPrint
RUN apt-get update && apt-get install -y --no-install-recommends \
    libcairo2 \
    libpango-1.0-0 \
    libpangocairo-1.0-0 \
    libgdk-pixbuf2.0-0 \
    && rm -rf /var/lib/apt/lists/*

COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

COPY . .

RUN mkdir -p storage/uploads storage/reports

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

- [ ] **Step 2: Create docker-compose.yml**

```yaml
# docdiff-service/docker-compose.yml
version: '3.8'

services:
  docdiff-api:
    build: .
    ports:
      - "8000:8000"
    env_file: .env
    volumes:
      - ./storage:/app/storage
    depends_on:
      - docdiff-redis
    restart: unless-stopped

  docdiff-worker:
    build: .
    command: arq app.workers.job_worker.WorkerSettings
    env_file: .env
    volumes:
      - ./storage:/app/storage
    depends_on:
      - docdiff-redis
    restart: unless-stopped

  docdiff-redis:
    image: redis:7-alpine
    ports:
      - "6380:6379"
    volumes:
      - docdiff-redis-data:/data
    restart: unless-stopped

volumes:
  docdiff-redis-data:
```

- [ ] **Step 3: Commit**

```bash
git add docdiff-service/Dockerfile docdiff-service/docker-compose.yml
git commit -m "feat(docdiff): add Docker setup for API, worker, and Redis"
```

---

## Task 16: Frontend — Types, API Client, Query Hooks

**Files:**
- Create: `web-system-app/src/features/docdiff/types/docdiff.types.ts`
- Create: `web-system-app/src/features/docdiff/api/docdiff-client.ts`
- Create: `web-system-app/src/features/docdiff/api/docdiff-api.ts`
- Create: `web-system-app/src/features/docdiff/api/use-docdiff-queries.ts`
- Create: `web-system-app/src/features/docdiff/api/use-docdiff-mutations.ts`
- Create: `web-system-app/src/features/docdiff/utils/significance-colors.ts`
- Create: `web-system-app/src/features/docdiff/utils/change-filters.ts`

- [ ] **Step 1: Create types/docdiff.types.ts**

```typescript
// web-system-app/src/features/docdiff/types/docdiff.types.ts

export type JobStatus =
  | "uploading"
  | "parsing_original"
  | "parsing_revised"
  | "aligning"
  | "diffing"
  | "classifying"
  | "assembling"
  | "ready_for_review"
  | "review_in_progress"
  | "completed"
  | "failed"
  | "cancelled";

export type ChangeType =
  | "text_addition"
  | "text_deletion"
  | "text_modification"
  | "table_cell_change"
  | "table_row_addition"
  | "table_row_deletion"
  | "table_structure_change"
  | "annotation_added"
  | "annotation_removed"
  | "section_moved"
  | "formatting_change";

export type Significance = "material" | "substantive" | "cosmetic" | "uncertain";

export type ReviewStatus = "pending" | "accepted" | "rejected" | "escalated";

export interface Job {
  id: string;
  status: JobStatus;
  model_provider: string;
  model_name: string;
  current_stage: number;
  stage_progress: Record<string, { status: string; name: string }> | null;
  error_message: string | null;
  total_changes: number;
  changes_reviewed: number;
  processing_time_ms: number | null;
  token_usage: { input_tokens: number; output_tokens: number; cost_estimate: number } | null;
  created_at: string;
  updated_at: string;
}

export interface JobListItem {
  id: string;
  status: JobStatus;
  model_provider: string;
  model_name: string;
  total_changes: number;
  changes_reviewed: number;
  processing_time_ms: number | null;
  created_at: string;
}

export interface DetectedChange {
  id: string;
  change_number: number;
  change_type: ChangeType;
  significance: Significance;
  confidence: number;
  page_original: number | null;
  page_revised: number | null;
  bbox_original: { x: number; y: number; width: number; height: number } | null;
  bbox_revised: { x: number; y: number; width: number; height: number } | null;
  value_before: string | null;
  value_after: string | null;
  context: string | null;
  summary: string;
  review_status: ReviewStatus;
  auto_accepted: boolean;
  needs_human_review: boolean;
  reviewer_comment: string | null;
  reviewed_at: string | null;
}

export interface ReviewActionPayload {
  action: ReviewStatus;
  comment?: string;
  edited_summary?: string;
  edited_significance?: Significance;
  edited_value_after?: string;
}

export interface BulkReviewPayload {
  change_ids: string[];
  action: ReviewStatus;
  comment?: string;
}

export interface DiffReport {
  id: string;
  job_id: string;
  summary_stats: Record<string, number> | null;
  report_html: string | null;
  report_pdf_path: string | null;
  generated_at: string;
}

export interface StageProgress {
  job_id: string;
  status: string;
  current_stage: number;
  stages: Record<string, { status: string; name: string }>;
  error?: string;
}

export interface ModelOption {
  provider: string;
  model: string;
  label: string;
  description: string;
}

export const MODEL_OPTIONS: ModelOption[] = [
  { provider: "anthropic", model: "claude-sonnet-4-6", label: "Claude Sonnet 4.6", description: "Fast, strong reasoning" },
  { provider: "anthropic", model: "claude-opus-4-6", label: "Claude Opus 4.6", description: "Most capable, higher cost" },
  { provider: "google", model: "gemini-3.1-pro", label: "Gemini 3.1 Pro", description: "Strong vision + tables" },
  { provider: "google", model: "gemini-3-flash", label: "Gemini 3 Flash", description: "Fast, cost-effective" },
  { provider: "openrouter", model: "google/gemini-2.5-pro-preview", label: "OpenRouter Best VLM", description: "Best available via OpenRouter" },
  { provider: "qwen_local", model: "qwen3-vl-8b", label: "Qwen3-VL 8B (Local)", description: "Self-hosted, no API cost" },
  { provider: "qwen_local", model: "qwen3-vl-30b-a3b", label: "Qwen3-VL 30B (Local)", description: "Larger local model" },
];
```

- [ ] **Step 2: Create api/docdiff-client.ts**

```typescript
// web-system-app/src/features/docdiff/api/docdiff-client.ts
import axios from "axios";

const DOCDIFF_API_URL = import.meta.env.VITE_DOCDIFF_API_URL || "http://localhost:8000/api/v1";

export const docdiffClient = axios.create({
  baseURL: DOCDIFF_API_URL,
  timeout: 120_000,
  headers: { Accept: "application/json" },
});

// Attach JWT from existing auth store
docdiffClient.interceptors.request.use((config) => {
  try {
    const tokensRaw = localStorage.getItem("auth_tokens");
    if (tokensRaw) {
      const tokens = JSON.parse(tokensRaw);
      if (tokens.accessToken) {
        config.headers.Authorization = `Bearer ${tokens.accessToken}`;
      }
    }
  } catch {
    // Ignore parse errors
  }
  return config;
});

// Strip axios wrapper — return API envelope directly
docdiffClient.interceptors.response.use(
  (response) => response.data,
  (error) => {
    const message = error.response?.data?.error || error.response?.data?.detail || error.message;
    return Promise.reject(new Error(message));
  },
);

export { DOCDIFF_API_URL };
```

- [ ] **Step 3: Create api/docdiff-api.ts**

```typescript
// web-system-app/src/features/docdiff/api/docdiff-api.ts
import { docdiffClient } from "./docdiff-client";
import type {
  BulkReviewPayload,
  DetectedChange,
  DiffReport,
  Job,
  JobListItem,
  ReviewActionPayload,
} from "../types/docdiff.types";

interface ApiResponse<T> {
  success: boolean;
  data: T;
  message?: string;
}

export const docdiffApi = {
  // Jobs
  createJob: (formData: FormData) =>
    docdiffClient.post<unknown, ApiResponse<Job>>("/jobs", formData, {
      headers: { "Content-Type": "multipart/form-data" },
    }),

  listJobs: () =>
    docdiffClient.get<unknown, ApiResponse<JobListItem[]>>("/jobs"),

  getJob: (id: string) =>
    docdiffClient.get<unknown, ApiResponse<Job>>(`/jobs/${id}`),

  deleteJob: (id: string) =>
    docdiffClient.delete(`/jobs/${id}`),

  startJob: (id: string) =>
    docdiffClient.post<unknown, ApiResponse<Job>>(`/jobs/${id}/start`),

  // Changes
  listChanges: (jobId: string, params?: Record<string, string | number | boolean>) =>
    docdiffClient.get<unknown, ApiResponse<DetectedChange[]>>(`/jobs/${jobId}/changes`, { params }),

  getChange: (jobId: string, changeId: string) =>
    docdiffClient.get<unknown, ApiResponse<DetectedChange>>(`/jobs/${jobId}/changes/${changeId}`),

  reviewChange: (jobId: string, changeId: string, action: ReviewActionPayload) =>
    docdiffClient.patch<unknown, ApiResponse<DetectedChange>>(`/jobs/${jobId}/changes/${changeId}`, action),

  bulkReview: (jobId: string, payload: BulkReviewPayload) =>
    docdiffClient.patch<unknown, ApiResponse<{ updated: number }>>(`/jobs/${jobId}/changes/bulk`, payload),

  addManualChange: (jobId: string, data: Partial<DetectedChange>) =>
    docdiffClient.post<unknown, ApiResponse<DetectedChange>>(`/jobs/${jobId}/changes`, data),

  // Documents
  getPageImageUrl: (jobId: string, role: string, pageNum: number) =>
    `${docdiffClient.defaults.baseURL}/jobs/${jobId}/documents/${role}/pages/${pageNum}/image`,

  getPageContent: (jobId: string, role: string, pageNum: number) =>
    docdiffClient.get(`/jobs/${jobId}/documents/${role}/pages/${pageNum}/content`),

  // Reports
  generateReport: (jobId: string) =>
    docdiffClient.post<unknown, ApiResponse<DiffReport>>(`/jobs/${jobId}/report`),

  getReport: (jobId: string) =>
    docdiffClient.get<unknown, ApiResponse<DiffReport>>(`/jobs/${jobId}/report`),

  getReportPdfUrl: (jobId: string) =>
    `${docdiffClient.defaults.baseURL}/jobs/${jobId}/report/pdf`,
};
```

- [ ] **Step 4: Create api/use-docdiff-queries.ts**

```typescript
// web-system-app/src/features/docdiff/api/use-docdiff-queries.ts
import { useQuery } from "@tanstack/react-query";
import { docdiffApi } from "./docdiff-api";

export const docdiffKeys = {
  all: ["docdiff"] as const,
  jobs: (params?: Record<string, unknown>) => [...docdiffKeys.all, "jobs", ...(params ? [params] : [])] as const,
  job: (id: string) => [...docdiffKeys.all, "job", id] as const,
  changes: (jobId: string, filters?: Record<string, unknown>) =>
    [...docdiffKeys.all, "changes", jobId, ...(filters ? [filters] : [])] as const,
  change: (jobId: string, changeId: string) =>
    [...docdiffKeys.all, "change", jobId, changeId] as const,
  report: (jobId: string) => [...docdiffKeys.all, "report", jobId] as const,
};

export function useJobs() {
  return useQuery({
    queryKey: docdiffKeys.jobs(),
    queryFn: () => docdiffApi.listJobs(),
  });
}

export function useJob(id: string) {
  return useQuery({
    queryKey: docdiffKeys.job(id),
    queryFn: () => docdiffApi.getJob(id),
    enabled: !!id,
    refetchInterval: (query) => {
      const status = query.state.data?.data?.status;
      if (status && ["uploading", "parsing_original", "parsing_revised", "aligning", "diffing", "classifying", "assembling"].includes(status)) {
        return 3000;
      }
      return false;
    },
  });
}

export function useChanges(jobId: string, filters?: Record<string, string | number | boolean>) {
  return useQuery({
    queryKey: docdiffKeys.changes(jobId, filters),
    queryFn: () => docdiffApi.listChanges(jobId, filters),
    enabled: !!jobId,
  });
}

export function useChange(jobId: string, changeId: string) {
  return useQuery({
    queryKey: docdiffKeys.change(jobId, changeId),
    queryFn: () => docdiffApi.getChange(jobId, changeId),
    enabled: !!jobId && !!changeId,
  });
}

export function useReport(jobId: string) {
  return useQuery({
    queryKey: docdiffKeys.report(jobId),
    queryFn: () => docdiffApi.getReport(jobId),
    enabled: !!jobId,
  });
}
```

- [ ] **Step 5: Create api/use-docdiff-mutations.ts**

```typescript
// web-system-app/src/features/docdiff/api/use-docdiff-mutations.ts
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { showApiError, showSuccess } from "@/lib/toast";
import { docdiffApi } from "./docdiff-api";
import { docdiffKeys } from "./use-docdiff-queries";
import type { BulkReviewPayload, ReviewActionPayload } from "../types/docdiff.types";

export function useCreateJob() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (formData: FormData) => docdiffApi.createJob(formData),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: docdiffKeys.jobs() });
      showSuccess("Comparison job created");
    },
    onError: (err) => showApiError(err),
  });
}

export function useStartJob() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (jobId: string) => docdiffApi.startJob(jobId),
    onSuccess: (_, jobId) => {
      qc.invalidateQueries({ queryKey: docdiffKeys.job(jobId) });
      showSuccess("Processing started");
    },
    onError: (err) => showApiError(err),
  });
}

export function useDeleteJob() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (jobId: string) => docdiffApi.deleteJob(jobId),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: docdiffKeys.jobs() });
      showSuccess("Job deleted");
    },
    onError: (err) => showApiError(err),
  });
}

export function useReviewChange(jobId: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ changeId, action }: { changeId: string; action: ReviewActionPayload }) =>
      docdiffApi.reviewChange(jobId, changeId, action),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: docdiffKeys.changes(jobId) });
      qc.invalidateQueries({ queryKey: docdiffKeys.job(jobId) });
    },
    onError: (err) => showApiError(err),
  });
}

export function useBulkReview(jobId: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (payload: BulkReviewPayload) => docdiffApi.bulkReview(jobId, payload),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: docdiffKeys.changes(jobId) });
      qc.invalidateQueries({ queryKey: docdiffKeys.job(jobId) });
      showSuccess("Bulk review applied");
    },
    onError: (err) => showApiError(err),
  });
}

export function useGenerateReport(jobId: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: () => docdiffApi.generateReport(jobId),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: docdiffKeys.report(jobId) });
      showSuccess("Report generated");
    },
    onError: (err) => showApiError(err),
  });
}
```

- [ ] **Step 6: Create utils/significance-colors.ts**

```typescript
// web-system-app/src/features/docdiff/utils/significance-colors.ts
import type { Significance } from "../types/docdiff.types";

export const SIGNIFICANCE_COLORS: Record<Significance, { bg: string; text: string; border: string; label: string }> = {
  material: { bg: "bg-red-50", text: "text-red-700", border: "border-red-300", label: "Material" },
  substantive: { bg: "bg-amber-50", text: "text-amber-700", border: "border-amber-300", label: "Substantive" },
  cosmetic: { bg: "bg-blue-50", text: "text-blue-700", border: "border-blue-300", label: "Cosmetic" },
  uncertain: { bg: "bg-purple-50", text: "text-purple-700", border: "border-purple-300", label: "Uncertain" },
};

export const SIGNIFICANCE_OVERLAY_COLORS: Record<Significance, string> = {
  material: "rgba(220, 38, 38, 0.2)",
  substantive: "rgba(217, 119, 6, 0.2)",
  cosmetic: "rgba(37, 99, 235, 0.2)",
  uncertain: "rgba(124, 58, 237, 0.2)",
};
```

- [ ] **Step 7: Create utils/change-filters.ts**

```typescript
// web-system-app/src/features/docdiff/utils/change-filters.ts
import type { ChangeType, DetectedChange, ReviewStatus, Significance } from "../types/docdiff.types";

export interface ChangeFilters {
  changeType?: ChangeType;
  significance?: Significance;
  reviewStatus?: ReviewStatus;
  page?: number;
  needsHumanReview?: boolean;
  confidenceMin?: number;
  confidenceMax?: number;
}

export function filtersToParams(filters: ChangeFilters): Record<string, string | number | boolean> {
  const params: Record<string, string | number | boolean> = {};
  if (filters.changeType) params.change_type = filters.changeType;
  if (filters.significance) params.significance = filters.significance;
  if (filters.reviewStatus) params.review_status = filters.reviewStatus;
  if (filters.page !== undefined) params.page = filters.page;
  if (filters.needsHumanReview !== undefined) params.needs_human_review = filters.needsHumanReview;
  if (filters.confidenceMin !== undefined) params.confidence_min = filters.confidenceMin;
  if (filters.confidenceMax !== undefined) params.confidence_max = filters.confidenceMax;
  return params;
}

export function formatChangeType(type: ChangeType): string {
  return type.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase());
}
```

- [ ] **Step 8: Commit**

```bash
cd /Users/chetan/Documents/Avyren-Technologies/Products/Mobile-ERP
git add web-system-app/src/features/docdiff/
git commit -m "feat(docdiff-web): add TypeScript types, API client, query hooks, and utils"
```

---

## Task 17: Frontend — Upload View + Processing View

**Files:**
- Create: `web-system-app/src/features/docdiff/components/ModelSelector.tsx`
- Create: `web-system-app/src/features/docdiff/components/UploadView.tsx`
- Create: `web-system-app/src/features/docdiff/hooks/useProcessingSSE.ts`
- Create: `web-system-app/src/features/docdiff/components/ProcessingView.tsx`

This task creates the upload and processing views. Since these are ~150-200 line React components each, **the subagent should reference the types from Task 16** and follow the existing ERP patterns (Tailwind, Lucide icons, showApiError/showSuccess toasts).

- [ ] **Step 1: Create ModelSelector.tsx**

A dropdown component that renders `MODEL_OPTIONS` from `docdiff.types.ts`. It should display provider name, model label, and description. Uses the same select/dropdown patterns as the existing ERP (a styled `<select>` with Tailwind classes).

Props: `value: string` (model name), `onChange: (provider: string, model: string) => void`

- [ ] **Step 2: Create UploadView.tsx**

Two drag-and-drop zones (Original and Revised) using native HTML5 drag-and-drop. Validates file type (.pdf) and size (< 50MB) on the client side. Includes the ModelSelector component and a "Start Comparison" button that:
1. Creates a FormData with both files + model_provider + model_name
2. Calls `useCreateJob` mutation
3. On success, calls `useStartJob` mutation
4. Navigates to the processing view

Layout: centered card, max-w-2xl, with two file zones side by side and the model selector below.

- [ ] **Step 3: Create useProcessingSSE.ts hook**

```typescript
// web-system-app/src/features/docdiff/hooks/useProcessingSSE.ts
import { useEffect, useState } from "react";
import type { StageProgress } from "../types/docdiff.types";

const DOCDIFF_API_URL = import.meta.env.VITE_DOCDIFF_API_URL || "http://localhost:8000/api/v1";

export function useProcessingSSE(jobId: string | null) {
  const [progress, setProgress] = useState<StageProgress | null>(null);
  const [isComplete, setIsComplete] = useState(false);

  useEffect(() => {
    if (!jobId) return;

    const source = new EventSource(`${DOCDIFF_API_URL}/jobs/${jobId}/progress`);

    source.onmessage = (event) => {
      try {
        const data: StageProgress = JSON.parse(event.data);
        setProgress(data);
        if (data.status === "ready_for_review" || data.status === "failed" || data.status === "cancelled") {
          setIsComplete(true);
          source.close();
        }
      } catch {
        // Ignore parse errors
      }
    };

    source.onerror = () => {
      source.close();
    };

    return () => source.close();
  }, [jobId]);

  return { progress, isComplete };
}
```

- [ ] **Step 4: Create ProcessingView.tsx**

Renders the 8 pipeline stages as a vertical list with status indicators. Uses `useProcessingSSE` for real-time updates. Each stage shows:
- Stage number and name
- Status icon: spinner (in_progress), green checkmark (completed), red X (failed), gray circle (pending)
- On completion (status=ready_for_review): show "Review Changes" button
- On failure: show error message and "Back to Upload" button

Layout: centered card, max-w-lg, with a vertical timeline.

Stage names (from the pipeline):
1. Ingestion & Validation
2. Page Classification
3. Content Extraction
4. Normalization
5. Section Alignment
6. Computing Differences
7. Classifying Changes
8. Assembling Results

- [ ] **Step 5: Commit**

```bash
cd /Users/chetan/Documents/Avyren-Technologies/Products/Mobile-ERP
git add web-system-app/src/features/docdiff/
git commit -m "feat(docdiff-web): add upload view, model selector, and processing view with SSE"
```

---

## Task 18: Frontend — Review Interface (Three-Panel Layout)

**Files:**
- Create: `web-system-app/src/features/docdiff/components/DocumentViewer.tsx`
- Create: `web-system-app/src/features/docdiff/components/ChangeList.tsx`
- Create: `web-system-app/src/features/docdiff/components/ChangeDetail.tsx`
- Create: `web-system-app/src/features/docdiff/components/ReviewInterface.tsx`
- Create: `web-system-app/src/features/docdiff/hooks/useChangeNavigation.ts`
- Create: `web-system-app/src/features/docdiff/hooks/useSyncScroll.ts`

This is the core review UI. The subagent should build the three-panel layout described in the design spec.

- [ ] **Step 1: Create DocumentViewer.tsx**

Renders a single document page as an image with overlay highlights for detected changes.

Props:
- `jobId: string`
- `role: "original" | "revised"`
- `pageNumber: number`
- `changes: DetectedChange[]` (changes on this page)
- `activeChangeId: string | null` (currently selected change)
- `onPageChange: (page: number) => void`
- `totalPages: number`

Uses `docdiffApi.getPageImageUrl()` for the image source. Renders change bounding boxes as absolute-positioned colored overlays using `SIGNIFICANCE_OVERLAY_COLORS`. The active change has a more prominent border.

Includes page navigation (prev/next) and zoom controls (fit page, 100%, 150%).

- [ ] **Step 2: Create ChangeList.tsx**

Left panel: scrollable list of all changes with filters.

Props:
- `jobId: string`
- `activeChangeId: string | null`
- `onSelectChange: (change: DetectedChange) => void`
- `filters: ChangeFilters`
- `onFiltersChange: (filters: ChangeFilters) => void`

Each change entry shows: change number, significance badge (colored), change type, confidence %, page number, brief summary (truncated), and review status icon.

Filter bar at top: dropdowns for change_type, significance, review_status. "Needs Review" toggle.

Progress indicator at bottom: "X of Y reviewed".

- [ ] **Step 3: Create ChangeDetail.tsx**

Bottom action bar showing the currently selected change with review actions.

Props:
- `change: DetectedChange`
- `onReview: (changeId: string, action: ReviewActionPayload) => void`
- `onPrevious: () => void`
- `onNext: () => void`
- `hasPrevious: boolean`
- `hasNext: boolean`

Shows: change summary, before/after values, significance badge, confidence score. Buttons: Accept (green), Reject (red), Edit (opens inline editor), Escalate (yellow, shows comment field). Previous/Next navigation buttons.

- [ ] **Step 4: Create useChangeNavigation.ts hook**

```typescript
// web-system-app/src/features/docdiff/hooks/useChangeNavigation.ts
import { useCallback, useEffect, useState } from "react";
import type { DetectedChange } from "../types/docdiff.types";

export function useChangeNavigation(changes: DetectedChange[]) {
  const [activeIndex, setActiveIndex] = useState(0);

  const activeChange = changes[activeIndex] ?? null;

  const goNext = useCallback(() => {
    setActiveIndex((i) => Math.min(i + 1, changes.length - 1));
  }, [changes.length]);

  const goPrevious = useCallback(() => {
    setActiveIndex((i) => Math.max(i - 1, 0));
  }, []);

  const goToChange = useCallback(
    (change: DetectedChange) => {
      const idx = changes.findIndex((c) => c.id === change.id);
      if (idx >= 0) setActiveIndex(idx);
    },
    [changes],
  );

  // Keyboard shortcuts
  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if (e.target instanceof HTMLInputElement || e.target instanceof HTMLTextAreaElement) return;
      if (e.key === "j" || e.key === "ArrowDown") {
        e.preventDefault();
        goNext();
      } else if (e.key === "k" || e.key === "ArrowUp") {
        e.preventDefault();
        goPrevious();
      }
    };
    window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  }, [goNext, goPrevious]);

  return {
    activeChange,
    activeIndex,
    goNext,
    goPrevious,
    goToChange,
    hasPrevious: activeIndex > 0,
    hasNext: activeIndex < changes.length - 1,
  };
}
```

- [ ] **Step 5: Create useSyncScroll.ts hook**

```typescript
// web-system-app/src/features/docdiff/hooks/useSyncScroll.ts
import { useCallback, useRef, useState } from "react";

export function useSyncScroll() {
  const leftRef = useRef<HTMLDivElement>(null);
  const rightRef = useRef<HTMLDivElement>(null);
  const [syncEnabled, setSyncEnabled] = useState(true);
  const isSyncing = useRef(false);

  const handleScroll = useCallback(
    (source: "left" | "right") => {
      if (!syncEnabled || isSyncing.current) return;
      isSyncing.current = true;

      const sourceEl = source === "left" ? leftRef.current : rightRef.current;
      const targetEl = source === "left" ? rightRef.current : leftRef.current;

      if (sourceEl && targetEl) {
        targetEl.scrollTop = sourceEl.scrollTop;
        targetEl.scrollLeft = sourceEl.scrollLeft;
      }

      requestAnimationFrame(() => {
        isSyncing.current = false;
      });
    },
    [syncEnabled],
  );

  return { leftRef, rightRef, syncEnabled, setSyncEnabled, handleScroll };
}
```

- [ ] **Step 6: Create ReviewInterface.tsx**

The three-panel layout orchestrator. Composes ChangeList (left 25%), DocumentViewer x2 (center 37.5% each), and ChangeDetail (bottom action bar).

Props: `jobId: string`

Uses `useChanges` query hook, `useChangeNavigation` for keyboard nav, `useSyncScroll` for synced scrolling, and `useReviewChange` mutation for actions.

When a change is selected, both DocumentViewers scroll to the relevant page and highlight the change's bounding box.

- [ ] **Step 7: Commit**

```bash
cd /Users/chetan/Documents/Avyren-Technologies/Products/Mobile-ERP
git add web-system-app/src/features/docdiff/
git commit -m "feat(docdiff-web): add review interface with three-panel layout and keyboard navigation"
```

---

## Task 19: Frontend — Report View, Handwriting Review, Keyboard Help

**Files:**
- Create: `web-system-app/src/features/docdiff/components/ReportView.tsx`
- Create: `web-system-app/src/features/docdiff/components/HandwritingReview.tsx`
- Create: `web-system-app/src/features/docdiff/components/UnresolvedRegion.tsx`
- Create: `web-system-app/src/features/docdiff/components/KeyboardShortcutsHelp.tsx`

- [ ] **Step 1: Create ReportView.tsx**

Shows the generated report. Uses `useReport` query and `useGenerateReport` mutation.

If no report exists yet: shows a "Generate Report" button (disabled if not all changes reviewed).
Once generated: renders `report_html` in an iframe or dangerouslySetInnerHTML div. Shows "Download PDF" button linking to `docdiffApi.getReportPdfUrl(jobId)`. Shows "Return to Review" button.

Executive summary section at top: total changes, breakdown by significance, auto-accepted vs manually reviewed vs rejected vs escalated.

- [ ] **Step 2: Create HandwritingReview.tsx**

For changes with `needs_human_review` and low confidence annotations. Shows the source image region alongside the attempted transcription. Allows the reviewer to correct the transcription via an inline text input, then accept or escalate.

Props: `change: DetectedChange`, `jobId: string`, `onReview: (...)  => void`

- [ ] **Step 3: Create UnresolvedRegion.tsx**

For pages/regions that couldn't be parsed. Shows side-by-side zoomed view of both documents. User can "Add Change Manually" or "No Difference".

Props: `jobId: string`, `pageOriginal: number`, `pageRevised: number`

- [ ] **Step 4: Create KeyboardShortcutsHelp.tsx**

A modal overlay triggered by "?" key. Lists all keyboard shortcuts:
- J / ↓ — Next change
- K / ↑ — Previous change
- A — Accept current change
- R — Reject current change
- E — Edit current change
- F — Flag for escalation
- ? — Toggle this help

- [ ] **Step 5: Commit**

```bash
cd /Users/chetan/Documents/Avyren-Technologies/Products/Mobile-ERP
git add web-system-app/src/features/docdiff/
git commit -m "feat(docdiff-web): add report view, handwriting review, unresolved regions, keyboard help"
```

---

## Task 20: Frontend — Main Screen + Route Integration

**Files:**
- Create: `web-system-app/src/features/docdiff/DocDiffScreen.tsx`
- Create: `web-system-app/src/features/docdiff/index.ts`
- Modify: `web-system-app/src/App.tsx` (add route)

- [ ] **Step 1: Create DocDiffScreen.tsx**

Main screen that manages view routing between Upload, Processing, Review, and Report views. Uses URL state or local state to track the current view and active job ID.

```typescript
// web-system-app/src/features/docdiff/DocDiffScreen.tsx
import { useState } from "react";
import { UploadView } from "./components/UploadView";
import { ProcessingView } from "./components/ProcessingView";
import { ReviewInterface } from "./components/ReviewInterface";
import { ReportView } from "./components/ReportView";

type View = "upload" | "processing" | "review" | "report";

export function DocDiffScreen() {
  const [view, setView] = useState<View>("upload");
  const [activeJobId, setActiveJobId] = useState<string | null>(null);

  const handleJobCreated = (jobId: string) => {
    setActiveJobId(jobId);
    setView("processing");
  };

  const handleProcessingComplete = () => {
    setView("review");
  };

  const handleGoToReport = () => {
    setView("report");
  };

  const handleBackToUpload = () => {
    setActiveJobId(null);
    setView("upload");
  };

  const handleBackToReview = () => {
    setView("review");
  };

  return (
    <div className="h-full">
      {view === "upload" && <UploadView onJobCreated={handleJobCreated} />}
      {view === "processing" && activeJobId && (
        <ProcessingView
          jobId={activeJobId}
          onComplete={handleProcessingComplete}
          onBack={handleBackToUpload}
        />
      )}
      {view === "review" && activeJobId && (
        <ReviewInterface
          jobId={activeJobId}
          onGenerateReport={handleGoToReport}
        />
      )}
      {view === "report" && activeJobId && (
        <ReportView
          jobId={activeJobId}
          onBackToReview={handleBackToReview}
          onNewComparison={handleBackToUpload}
        />
      )}
    </div>
  );
}
```

- [ ] **Step 2: Create index.ts**

```typescript
// web-system-app/src/features/docdiff/index.ts
export { DocDiffScreen } from "./DocDiffScreen";
```

- [ ] **Step 3: Add route to App.tsx**

In `web-system-app/src/App.tsx`, add the lazy import at the top with the other imports:

```typescript
const DocDiffScreen = lazyNamed(() => import("./features/docdiff/DocDiffScreen"), "DocDiffScreen");
```

Add the route inside the protected `/app` routes section (after the company routes):

```tsx
<Route path="docdiff" element={<DocDiffScreen />} />
```

- [ ] **Step 4: Add VITE_DOCDIFF_API_URL to .env**

In `web-system-app/.env`, add:

```env
VITE_DOCDIFF_API_URL=http://localhost:8000/api/v1
```

- [ ] **Step 5: Commit**

```bash
cd /Users/chetan/Documents/Avyren-Technologies/Products/Mobile-ERP
git add web-system-app/src/features/docdiff/ web-system-app/src/App.tsx web-system-app/.env
git commit -m "feat(docdiff-web): add main DocDiff screen with view routing and App.tsx integration"
```

---

## Execution Notes

### Running the backend

```bash
cd docdiff-service
source .venv/bin/activate

# Terminal 1: API server
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# Terminal 2: ARQ worker
arq app.workers.job_worker.WorkerSettings
```

### Running the frontend

```bash
cd web-system-app
pnpm dev
# Navigate to http://localhost:5173/app/docdiff
```

### Running migrations

```bash
cd docdiff-service
source .venv/bin/activate
alembic upgrade head
```

### Task dependencies

Tasks 1-5 are sequential (each depends on prior). Tasks 6-10 can run in parallel after Task 1. Tasks 11-13 depend on Tasks 6-10. Task 14 depends on Tasks 2-3 + 13. Task 15 depends on all backend tasks. Tasks 16-20 can start after Task 5 (API structure exists) — they only depend on the type definitions matching.

```
Task 1 (scaffold) ──→ Task 2 (DB) ──→ Task 3 (schemas) ──→ Task 4 (auth) ──→ Task 5 (health/router)
                  └──→ Task 6 (AI base) ──→ Task 7 (providers)
                  └──→ Task 8 (prompts)
                  └──→ Task 9 (PDF utils)
                  └──→ Task 10 (diff utils)
Task 5 + 7 + 8 + 9 + 10 ──→ Task 11 (stages 1-4) ──→ Task 12 (stages 5-8) ──→ Task 13 (orchestrator)
Task 3 + 13 ──→ Task 14 (API endpoints)
Task 14 ──→ Task 15 (Docker)
Task 5 ──→ Task 16 (FE types/API) ──→ Task 17 (upload/processing) ──→ Task 18 (review) ──→ Task 19 (report/extras) ──→ Task 20 (integration)
```
