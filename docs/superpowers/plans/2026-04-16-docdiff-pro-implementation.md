# DocDiff Pro Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build an AI-powered document comparison microservice (Python/FastAPI) with a React frontend module embedded in the existing ERP web app. The system is strictly a **diff analysis and reporting tool** — it detects and reports differences between two document versions but never modifies either document.

**Architecture:** Standalone FastAPI service (`docdiff-service/`) at port 8000, sharing PostgreSQL (separate `docdiff` schema) and Redis with the existing Node.js backend. Frontend module in `web-system-app/src/features/docdiff/`. SSE for real-time progress. Dual auth (JWT + API key).

**Tech Stack:** Python 3.11+, FastAPI, SQLAlchemy async, Alembic, ARQ, Docling, PyMuPDF, diff-match-patch, WeasyPrint, tenacity, httpx, anthropic SDK, google-genai SDK. Frontend: React, TypeScript, TailwindCSS, React Query.

**Spec:** `docs/superpowers/specs/2026-04-16-docdiff-pro-design.md`
**PRD:** `docs/DocDiff-Pro-PRD-Prototype-v0.2.md`

### Key Terminology (v0.2 PRD)

The PRD v0.2 reframes the system as a diff analysis tool. Key terminology:

| Concept | Term Used | NOT |
|---|---|---|
| The two documents | **Version A** / **Version B** | ~~Original / Revised~~ |
| What the system detects | **Differences** | ~~Changes~~ |
| Reviewer's action | **Verification** (Confirm/Dismiss/Correct/Flag) | ~~Review (Accept/Reject)~~ |
| The output | **Diff Report** | ~~Change report~~ |
| Confidence auto-action | **Auto-confirm** (threshold 0.95) | ~~Auto-accept~~ |

All code, variables, API paths, and UI text MUST use this terminology consistently.

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
| `app/models/difference.py` | DetectedDifference ORM model |
| `app/models/report.py` | DiffReport ORM model |
| `app/models/api_key.py` | APIKey ORM model |
| `app/schemas/__init__.py` | Schema exports |
| `app/schemas/job.py` | Job request/response schemas |
| `app/schemas/document.py` | Document schemas |
| `app/schemas/difference.py` | Difference + verification action schemas |
| `app/schemas/report.py` | Report schemas |
| `app/schemas/common.py` | Shared schemas (pagination, envelope) |
| `app/api/__init__.py` | Package init |
| `app/api/router.py` | Main router aggregator |
| `app/api/health.py` | GET /health endpoint |
| `app/api/jobs.py` | Job CRUD + start processing |
| `app/api/sse.py` | SSE progress endpoint |
| `app/api/differences.py` | Difference list + verification actions |
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
| `app/prompts/classify_difference.py` | Difference significance classification prompts |
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
| `features/docdiff/api/use-docdiff-mutations.ts` | Mutations (upload, verify, report) |
| `features/docdiff/types/docdiff.types.ts` | All TypeScript interfaces |
| `features/docdiff/components/UploadView.tsx` | Drag-drop + editable labels + model selector |
| `features/docdiff/components/ProcessingView.tsx` | 8-stage progress (SSE) |
| `features/docdiff/components/DifferenceViewer.tsx` | Three-panel layout (main verification interface) |
| `features/docdiff/components/DocumentViewer.tsx` | PDF page image + overlays (read-only) |
| `features/docdiff/components/DifferenceList.tsx` | Filterable difference list |
| `features/docdiff/components/DifferenceDetail.tsx` | Single difference + verification actions |
| `features/docdiff/components/HandwritingReview.tsx` | Image + transcription correction |
| `features/docdiff/components/UnresolvedRegion.tsx` | Side-by-side zoom |
| `features/docdiff/components/ReportView.tsx` | Structured diff report + download |
| `features/docdiff/components/ComparisonHistory.tsx` | Table of past comparisons |
| `features/docdiff/components/ModelSelector.tsx` | AI model dropdown |
| `features/docdiff/components/KeyboardShortcutsHelp.tsx` | "?" overlay |
| `features/docdiff/hooks/useProcessingSSE.ts` | EventSource hook |
| `features/docdiff/hooks/useDifferenceNavigation.ts` | J/K keyboard nav + C/D/E/F/Space shortcuts |
| `features/docdiff/hooks/useSyncScroll.ts` | Synchronized scrolling |
| `features/docdiff/utils/significance-colors.ts` | Color mapping |
| `features/docdiff/utils/difference-filters.ts` | Filter/sort logic |
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
description = "DocDiff Pro - AI-powered document comparison and diff reporting service"
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
DOCDIFF_AUTO_CONFIRM_THRESHOLD=0.95
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
    auto_confirm_threshold: float = 0.95
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
    description="AI-powered document comparison and diff reporting service",
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
- Create: `docdiff-service/app/models/difference.py`
- Create: `docdiff-service/app/models/report.py`
- Create: `docdiff-service/app/models/api_key.py`
- Create: `docdiff-service/alembic.ini`
- Create: `docdiff-service/alembic/env.py`

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
from sqlalchemy.orm import DeclarativeBase

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
    PARSING_VERSION_A = "parsing_version_a"
    PARSING_VERSION_B = "parsing_version_b"
    ALIGNING = "aligning"
    DIFFING = "diffing"
    CLASSIFYING = "classifying"
    ASSEMBLING = "assembling"
    READY_FOR_REVIEW = "ready_for_review"
    VERIFICATION_IN_PROGRESS = "verification_in_progress"
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
    total_differences: Mapped[int] = mapped_column(Integer, default=0)
    differences_verified: Mapped[int] = mapped_column(Integer, default=0)
    auto_confirm_threshold: Mapped[float] = mapped_column(Float, default=0.95)
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
    differences = relationship("DetectedDifference", back_populates="job", cascade="all, delete-orphan")
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
    VERSION_A = "version_a"
    VERSION_B = "version_b"


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
    label: Mapped[str] = mapped_column(String(500), default="")
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

- [ ] **Step 5: Create app/models/difference.py**

Note: This was `change.py` in v0.1. Renamed to `difference.py` with all terminology updated.

```python
# docdiff-service/app/models/difference.py
import enum
import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Enum, Float, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSON, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import SCHEMA, Base


class DifferenceType(str, enum.Enum):
    TEXT_ADDITION = "text_addition"
    TEXT_DELETION = "text_deletion"
    TEXT_MODIFICATION = "text_modification"
    TABLE_CELL_CHANGE = "table_cell_change"
    TABLE_ROW_ADDITION = "table_row_addition"
    TABLE_ROW_DELETION = "table_row_deletion"
    TABLE_STRUCTURE_CHANGE = "table_structure_change"
    ANNOTATION_PRESENT_IN_B = "annotation_present_in_b"
    ANNOTATION_REMOVED_FROM_B = "annotation_removed_from_b"
    SECTION_MOVED = "section_moved"
    FORMATTING_CHANGE = "formatting_change"


class Significance(str, enum.Enum):
    MATERIAL = "material"
    SUBSTANTIVE = "substantive"
    COSMETIC = "cosmetic"
    UNCERTAIN = "uncertain"


class VerificationStatus(str, enum.Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    DISMISSED = "dismissed"
    CORRECTED = "corrected"
    FLAGGED = "flagged"


class DetectedDifference(Base):
    __tablename__ = "detected_differences"
    __table_args__ = {"schema": SCHEMA}

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    job_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey(f"{SCHEMA}.comparison_jobs.id", ondelete="CASCADE")
    )
    difference_number: Mapped[int] = mapped_column(Integer)
    difference_type: Mapped[str] = mapped_column(
        Enum(DifferenceType, schema=SCHEMA, name="difference_type_enum")
    )
    significance: Mapped[str] = mapped_column(
        Enum(Significance, schema=SCHEMA, name="significance_enum")
    )
    confidence: Mapped[float] = mapped_column(Float)
    page_version_a: Mapped[int | None] = mapped_column(Integer, nullable=True)
    page_version_b: Mapped[int | None] = mapped_column(Integer, nullable=True)
    bbox_version_a: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    bbox_version_b: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    value_before: Mapped[str | None] = mapped_column(Text, nullable=True)
    value_after: Mapped[str | None] = mapped_column(Text, nullable=True)
    context: Mapped[str | None] = mapped_column(Text, nullable=True)
    summary: Mapped[str] = mapped_column(Text)
    block_id_version_a: Mapped[str | None] = mapped_column(String(100), nullable=True)
    block_id_version_b: Mapped[str | None] = mapped_column(String(100), nullable=True)
    verification_status: Mapped[str] = mapped_column(
        Enum(VerificationStatus, schema=SCHEMA, name="verification_status_enum"),
        default=VerificationStatus.PENDING,
    )
    auto_confirmed: Mapped[bool] = mapped_column(Boolean, default=False)
    needs_verification: Mapped[bool] = mapped_column(Boolean, default=False)
    verifier_comment: Mapped[str | None] = mapped_column(Text, nullable=True)
    corrected_description: Mapped[str | None] = mapped_column(Text, nullable=True)
    verified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    job = relationship("ComparisonJob", back_populates="differences")
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
    is_partial: Mapped[bool] = mapped_column(default=False)
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
from app.models.difference import DetectedDifference, DifferenceType, Significance, VerificationStatus
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
    "DetectedDifference",
    "DifferenceType",
    "Significance",
    "VerificationStatus",
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
Find the line `sqlalchemy.url = driver://user:pass@localhost/dbname` and replace with:
```ini
sqlalchemy.url =
```

- [ ] **Step 10: Generate and run initial migration**

```bash
cd docdiff-service
source .venv/bin/activate
alembic revision --autogenerate -m "initial docdiff schema"
alembic upgrade head
```

- [ ] **Step 11: Commit**

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
- Create: `docdiff-service/app/schemas/difference.py`
- Create: `docdiff-service/app/schemas/report.py`
- Create: `docdiff-service/app/schemas/__init__.py`
- Create: `docdiff-service/app/api/deps.py`
- Create: `docdiff-service/app/api/__init__.py`

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
    label_a: str = Field(default="Version A", description="Label for the first document")
    label_b: str = Field(default="Version B", description="Label for the second document")
    auto_confirm_threshold: float = Field(default=0.95, description="Confidence threshold for auto-confirmation")


class JobResponse(BaseModel):
    id: uuid.UUID
    status: JobStatus
    model_provider: str
    model_name: str
    current_stage: int
    stage_progress: dict | None = None
    error_message: str | None = None
    total_differences: int
    differences_verified: int
    auto_confirm_threshold: float
    processing_time_ms: int | None = None
    token_usage: dict | None = None
    user_id: str | None = None
    company_id: str | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class JobListResponse(BaseModel):
    """Used for comparison history list (FR-39)."""
    id: uuid.UUID
    status: JobStatus
    model_provider: str
    model_name: str
    label_a: str | None = None
    label_b: str | None = None
    total_differences: int
    differences_verified: int
    material_count: int | None = None
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
    label: str
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

- [ ] **Step 4: Create app/schemas/difference.py**

Note: This was `change.py` in v0.1. Terminology fully updated.

```python
# docdiff-service/app/schemas/difference.py
import uuid
from datetime import datetime

from pydantic import BaseModel, Field

from app.models.difference import DifferenceType, Significance, VerificationStatus


class DifferenceResponse(BaseModel):
    id: uuid.UUID
    difference_number: int
    difference_type: DifferenceType
    significance: Significance
    confidence: float
    page_version_a: int | None = None
    page_version_b: int | None = None
    bbox_version_a: dict | None = None
    bbox_version_b: dict | None = None
    value_before: str | None = None
    value_after: str | None = None
    context: str | None = None
    summary: str
    verification_status: VerificationStatus
    auto_confirmed: bool
    needs_verification: bool
    verifier_comment: str | None = None
    corrected_description: str | None = None
    verified_at: datetime | None = None

    model_config = {"from_attributes": True}


class VerificationAction(BaseModel):
    """Reviewer verification action (FR-24 v0.2).
    
    - confirm: Difference is real and correctly described
    - dismiss: False positive, no real difference exists
    - correct: Difference is real but description is wrong — provide corrected_description
    - flag: Unsure, flag for supervisor review — provide comment
    """
    action: VerificationStatus = Field(description="confirm, dismiss, correct, or flag")
    comment: str | None = None
    corrected_description: str | None = Field(
        default=None,
        description="Required when action=correct. The reviewer's corrected description of the difference.",
    )
    corrected_significance: Significance | None = None
    corrected_value_after: str | None = None


class BulkVerificationAction(BaseModel):
    difference_ids: list[uuid.UUID]
    action: VerificationStatus
    comment: str | None = None


class ManualDifferenceCreate(BaseModel):
    """For adding a manually spotted difference (unresolved regions)."""
    difference_type: DifferenceType
    significance: Significance
    page_version_a: int | None = None
    page_version_b: int | None = None
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
    is_partial: bool = False
    generated_at: datetime

    model_config = {"from_attributes": True}
```

- [ ] **Step 6: Create app/schemas/__init__.py**

```python
# docdiff-service/app/schemas/__init__.py
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
    "SuccessResponse",
    "PaginatedResponse",
    "ErrorResponse",
    "BBox",
    "JobCreate",
    "JobResponse",
    "JobListResponse",
    "DocumentResponse",
    "PageContentResponse",
    "DifferenceResponse",
    "VerificationAction",
    "BulkVerificationAction",
    "ManualDifferenceCreate",
    "ReportResponse",
]
```

- [ ] **Step 7: Create app/api/deps.py and __init__.py**

```python
# docdiff-service/app/api/__init__.py
```

```python
# docdiff-service/app/api/deps.py
from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.middleware import AuthContext, get_current_user
from app.database import get_db

DbSession = Annotated[AsyncSession, Depends(get_db)]
CurrentUser = Annotated[AuthContext, Depends(get_current_user)]
```

- [ ] **Step 8: Commit**

```bash
git add docdiff-service/app/schemas/ docdiff-service/app/api/
git commit -m "feat(docdiff): add Pydantic schemas and API dependencies"
```

---

## Tasks 4-10: Unchanged from v0.1

Tasks 4 (Authentication), 5 (Health Check + Router), 6 (AI Base + Response Parser), 7 (AI Providers), 9 (PDF Utilities), and 10 (Diff Utilities) are **unchanged** from the v0.1 plan — they don't reference the changed terminology. Refer to the original plan steps for these tasks.

**Task 8 (Prompts)** has one file rename:

- `app/prompts/classify_change.py` → `app/prompts/classify_difference.py`

In the prompt template, replace "change" with "difference" in the text. The function becomes `get_classify_prompt()` with the same signature. The prompt text should say "classifying a detected difference between two document versions" instead of "classifying a detected change."

The rest of Task 8 (extract_page.py, transcribe_handwriting.py) is unchanged.

---

## Task 5: Health Check + API Router + Jobs API

Same as v0.1, except the Jobs API has these changes:

- [ ] **Step 2: Create app/api/jobs.py**

Key differences from v0.1:
- Upload form fields: `label_a` and `label_b` (editable version labels, default "Version A"/"Version B")
- `auto_confirm_threshold` form field (default 0.95)
- Document roles: `DocumentRole.VERSION_A` and `DocumentRole.VERSION_B` instead of `ORIGINAL`/`REVISED`
- Job status: `PARSING_VERSION_A` instead of `PARSING_ORIGINAL`
- Fields: `total_differences`, `differences_verified` instead of `total_changes`, `changes_reviewed`
- `GET /jobs` returns `JobListResponse` which includes `label_a`, `label_b`, and `material_count` for the comparison history view (FR-39)

```python
# docdiff-service/app/api/jobs.py
import uuid

from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.api.deps import CurrentUser, DbSession
from app.config import settings
from app.models.difference import DetectedDifference, Significance
from app.models.document import Document, DocumentRole
from app.models.job import ComparisonJob, JobStatus
from app.schemas.job import JobListResponse, JobResponse
from app.schemas.common import SuccessResponse

router = APIRouter(prefix="/jobs", tags=["jobs"])


@router.post("", response_model=SuccessResponse[JobResponse])
async def create_job(
    db: DbSession,
    user: CurrentUser,
    version_a: UploadFile = File(..., description="Version A PDF document"),
    version_b: UploadFile = File(..., description="Version B PDF document"),
    model_provider: str = Form(default="anthropic"),
    model_name: str = Form(default="claude-sonnet-4-6"),
    label_a: str = Form(default="Version A"),
    label_b: str = Form(default="Version B"),
    auto_confirm_threshold: float = Form(default=0.95),
):
    """Create a new comparison job by uploading two PDF documents."""
    for f, label in [(version_a, "Version A"), (version_b, "Version B")]:
        if not f.filename or not f.filename.lower().endswith(".pdf"):
            raise HTTPException(400, f"{label} file must be a PDF")
        if f.size and f.size > settings.max_file_size_mb * 1024 * 1024:
            raise HTTPException(400, f"{label} file exceeds {settings.max_file_size_mb}MB limit")

    job = ComparisonJob(
        model_provider=model_provider,
        model_name=model_name,
        status=JobStatus.UPLOADING,
        auto_confirm_threshold=auto_confirm_threshold,
        user_id=user.user_id,
        company_id=user.company_id,
        api_key_id=uuid.UUID(user.api_key_id) if user.api_key_id else None,
    )
    db.add(job)
    await db.flush()

    import os
    job_dir = os.path.join(settings.storage_path, "uploads", str(job.id))
    os.makedirs(job_dir, exist_ok=True)

    for upload, role, label in [
        (version_a, DocumentRole.VERSION_A, label_a),
        (version_b, DocumentRole.VERSION_B, label_b),
    ]:
        file_path = os.path.join(job_dir, f"{role.value}_{upload.filename}")
        content = await upload.read()
        with open(file_path, "wb") as f:
            f.write(content)

        doc = Document(
            job_id=job.id,
            role=role,
            label=label,
            filename=upload.filename or "unknown.pdf",
            file_path=file_path,
            file_size_bytes=len(content),
            page_count=0,
        )
        db.add(doc)

    await db.commit()
    await db.refresh(job)
    return SuccessResponse(data=JobResponse.model_validate(job), message="Job created")


@router.get("", response_model=SuccessResponse[list[JobListResponse]])
async def list_jobs(db: DbSession, user: CurrentUser):
    """List comparison jobs (comparison history — FR-39)."""
    query = (
        select(ComparisonJob)
        .options(selectinload(ComparisonJob.documents))
        .order_by(ComparisonJob.created_at.desc())
    )
    if user.user_id:
        query = query.where(ComparisonJob.user_id == user.user_id)
    elif user.api_key_id:
        query = query.where(ComparisonJob.api_key_id == uuid.UUID(user.api_key_id))
    result = await db.execute(query)
    jobs = result.scalars().unique().all()

    response_list = []
    for j in jobs:
        docs = {d.role: d for d in j.documents}
        response_list.append(JobListResponse(
            id=j.id,
            status=j.status,
            model_provider=j.model_provider,
            model_name=j.model_name,
            label_a=docs.get(DocumentRole.VERSION_A, None) and docs[DocumentRole.VERSION_A].label,
            label_b=docs.get(DocumentRole.VERSION_B, None) and docs[DocumentRole.VERSION_B].label,
            total_differences=j.total_differences,
            differences_verified=j.differences_verified,
            processing_time_ms=j.processing_time_ms,
            created_at=j.created_at,
        ))
    return SuccessResponse(data=response_list)


@router.get("/{job_id}", response_model=SuccessResponse[JobResponse])
async def get_job(job_id: uuid.UUID, db: DbSession, user: CurrentUser):
    result = await db.execute(select(ComparisonJob).where(ComparisonJob.id == job_id))
    job = result.scalar_one_or_none()
    if not job:
        raise HTTPException(404, "Job not found")
    return SuccessResponse(data=JobResponse.model_validate(job))


@router.delete("/{job_id}")
async def delete_job(job_id: uuid.UUID, db: DbSession, user: CurrentUser):
    result = await db.execute(select(ComparisonJob).where(ComparisonJob.id == job_id))
    job = result.scalar_one_or_none()
    if not job:
        raise HTTPException(404, "Job not found")
    await db.delete(job)
    await db.commit()
    return SuccessResponse(data=None, message="Job deleted")


@router.post("/{job_id}/start")
async def start_job(job_id: uuid.UUID, db: DbSession, user: CurrentUser):
    result = await db.execute(select(ComparisonJob).where(ComparisonJob.id == job_id))
    job = result.scalar_one_or_none()
    if not job:
        raise HTTPException(404, "Job not found")
    if job.status != JobStatus.UPLOADING:
        raise HTTPException(400, f"Job cannot be started from status: {job.status}")

    job.status = JobStatus.PARSING_VERSION_A
    job.current_stage = 1
    job.stage_progress = {"1": "in_progress"}
    await db.commit()

    from app.workers.job_worker import enqueue_job
    await enqueue_job(str(job_id))

    await db.refresh(job)
    return SuccessResponse(data=JobResponse.model_validate(job), message="Processing started")
```

---

## Tasks 6-10: Same as v0.1

Refer to original plan. Only change: Task 8 renames `classify_change.py` → `classify_difference.py`.

---

## Tasks 11-13: Pipeline Stages

Same structure as v0.1, with these terminology updates throughout:

- `DocumentRole.ORIGINAL` → `DocumentRole.VERSION_A`, `DocumentRole.REVISED` → `DocumentRole.VERSION_B`
- `doc.role` values: `"version_a"` / `"version_b"` instead of `"original"` / `"revised"`
- Block IDs: prefix `version_a_` / `version_b_` instead of `original_` / `revised_`
- `page_original` / `page_revised` → `page_version_a` / `page_version_b`
- `block_id_original` / `block_id_revised` → `block_id_version_a` / `block_id_version_b`
- `bbox_original` / `bbox_revised` → `bbox_version_a` / `bbox_version_b`
- `DetectedChange` → `DetectedDifference`
- `ChangeType` → `DifferenceType`
- `ReviewStatus` → `VerificationStatus`
- `ANNOTATION_ADDED` → `ANNOTATION_PRESENT_IN_B`
- `ANNOTATION_REMOVED` → `ANNOTATION_REMOVED_FROM_B`
- `auto_accepted` → `auto_confirmed`
- `needs_human_review` → `needs_verification`
- `total_changes` → `total_differences`
- `changes_reviewed` → `differences_verified`
- `PARSING_ORIGINAL` → `PARSING_VERSION_A`
- `PARSING_REVISED` → `PARSING_VERSION_B`
- `REVIEW_IN_PROGRESS` → `VERIFICATION_IN_PROGRESS`

**Task 12, Stage 7 (scoring):** Use `job.auto_confirm_threshold` (from the job, not from settings) for auto-confirmation:

```python
# In stage_7_scoring.py — auto_confirm uses per-job threshold
auto_confirmed = confidence >= auto_confirm_threshold and significance != Significance.UNCERTAIN
```

**Task 12, Stage 8 (assembly):** Save as `DetectedDifference` with `verification_status=VerificationStatus.CONFIRMED` for auto-confirmed, `VerificationStatus.PENDING` otherwise.

---

## Task 14: API Endpoints (SSE, Differences, Reports, Documents, API Keys)

Same structure as v0.1 with these changes:

### `app/api/differences.py` (was `changes.py`)

API path: `/jobs/{job_id}/differences` (was `/changes`)

All "change" terminology → "difference":
- `ChangeResponse` → `DifferenceResponse`
- `ReviewAction` → `VerificationAction`
- `BulkReviewAction` → `BulkVerificationAction`
- `ManualChangeCreate` → `ManualDifferenceCreate`
- `DetectedChange` → `DetectedDifference`
- `ReviewStatus` → `VerificationStatus`
- `review_status` → `verification_status`
- `reviewer_comment` → `verifier_comment`
- `reviewed_at` → `verified_at`
- `change_number` → `difference_number`
- `change_type` → `difference_type`
- `page_original` / `page_revised` → `page_version_a` / `page_version_b`
- `changes_reviewed` → `differences_verified`

Verification actions in PATCH endpoint:
- `confirm` → Sets `verification_status=CONFIRMED`
- `dismiss` → Sets `verification_status=DISMISSED` (excluded from report)
- `correct` → Sets `verification_status=CORRECTED`, saves `corrected_description`
- `flag` → Sets `verification_status=FLAGGED`, saves comment

### `app/pdf/report_generator.py` — Restructured for v0.2

The report structure changes significantly (FR-30 through FR-35):

```python
# Report sections in order:
# 1. Header: metadata, labels, model, processing time
# 2. Executive Summary: total diffs, by significance, one-line verdict
# 3. Quick Reference Table: one-page summary of material + substantive
# 4. Material Differences: listed first with page refs, before→after, descriptions
# 5. Substantive Differences: same format
# 6. Cosmetic Differences: same format (collapsible)
# 7. Flagged Items: differences flagged for further review with comments
# 8. Dismissed Items: count only (transparency)
# 9. Unresolved Regions: page regions that couldn't be analyzed
```

Key changes:
- Report can be generated at any time, even with pending verifications (FR-30)
- `is_partial` flag on DiffReport model tracks this
- One-line verdict in executive summary: e.g., "14 differences detected — 3 material, 7 substantive, 4 cosmetic"
- Quick Reference Table: compact single-page table of material + substantive differences
- Dismissed items section shows only a count
- Flagged items get their own section with verifier comments
- Visual diff thumbnails for each confirmed difference

### `app/api/reports.py` — Allow partial reports

The report generation endpoint removes the "all verified" requirement:

```python
@router.post("")
async def generate_report(job_id: uuid.UUID, db: DbSession, user: CurrentUser):
    # ... same as v0.1 but:
    # 1. No status check — report can be generated any time after processing
    # 2. Set is_partial = True if any differences are still pending
    # 3. Don't set job.status = COMPLETED (that happens when all verified)
    pending_count = await db.execute(
        select(func.count()).where(
            DetectedDifference.job_id == job_id,
            DetectedDifference.verification_status == VerificationStatus.PENDING,
        )
    )
    is_partial = (pending_count.scalar() or 0) > 0
    # ... save report with is_partial flag
```

### `app/api/router.py`

```python
# docdiff-service/app/api/router.py
from fastapi import APIRouter

from app.api.api_keys import router as api_keys_router
from app.api.differences import router as differences_router
from app.api.documents import router as documents_router
from app.api.health import router as health_router
from app.api.jobs import router as jobs_router
from app.api.reports import router as reports_router
from app.api.sse import router as sse_router

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(jobs_router)
api_router.include_router(sse_router)
api_router.include_router(differences_router)
api_router.include_router(documents_router)
api_router.include_router(reports_router)
api_router.include_router(api_keys_router)
```

---

## Task 15: Docker Setup

Unchanged from v0.1.

---

## Task 16: Frontend — Types, API Client, Query Hooks

**Files:**
- Create: `web-system-app/src/features/docdiff/types/docdiff.types.ts`
- Create: `web-system-app/src/features/docdiff/api/docdiff-client.ts`
- Create: `web-system-app/src/features/docdiff/api/docdiff-api.ts`
- Create: `web-system-app/src/features/docdiff/api/use-docdiff-queries.ts`
- Create: `web-system-app/src/features/docdiff/api/use-docdiff-mutations.ts`
- Create: `web-system-app/src/features/docdiff/utils/significance-colors.ts`
- Create: `web-system-app/src/features/docdiff/utils/difference-filters.ts`

- [ ] **Step 1: Create types/docdiff.types.ts**

Key terminology changes from v0.1:

```typescript
// web-system-app/src/features/docdiff/types/docdiff.types.ts

export type JobStatus =
  | "uploading"
  | "parsing_version_a"
  | "parsing_version_b"
  | "aligning"
  | "diffing"
  | "classifying"
  | "assembling"
  | "ready_for_review"
  | "verification_in_progress"
  | "completed"
  | "failed"
  | "cancelled";

export type DifferenceType =
  | "text_addition"
  | "text_deletion"
  | "text_modification"
  | "table_cell_change"
  | "table_row_addition"
  | "table_row_deletion"
  | "table_structure_change"
  | "annotation_present_in_b"
  | "annotation_removed_from_b"
  | "section_moved"
  | "formatting_change";

export type Significance = "material" | "substantive" | "cosmetic" | "uncertain";

export type VerificationStatus = "pending" | "confirmed" | "dismissed" | "corrected" | "flagged";

export interface Job {
  id: string;
  status: JobStatus;
  model_provider: string;
  model_name: string;
  current_stage: number;
  stage_progress: Record<string, { status: string; name: string }> | null;
  error_message: string | null;
  total_differences: number;
  differences_verified: number;
  auto_confirm_threshold: number;
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
  label_a: string | null;
  label_b: string | null;
  total_differences: number;
  differences_verified: number;
  material_count: number | null;
  processing_time_ms: number | null;
  created_at: string;
}

export interface DetectedDifference {
  id: string;
  difference_number: number;
  difference_type: DifferenceType;
  significance: Significance;
  confidence: number;
  page_version_a: number | null;
  page_version_b: number | null;
  bbox_version_a: { x: number; y: number; width: number; height: number } | null;
  bbox_version_b: { x: number; y: number; width: number; height: number } | null;
  value_before: string | null;
  value_after: string | null;
  context: string | null;
  summary: string;
  verification_status: VerificationStatus;
  auto_confirmed: boolean;
  needs_verification: boolean;
  verifier_comment: string | null;
  corrected_description: string | null;
  verified_at: string | null;
}

export interface VerificationActionPayload {
  action: VerificationStatus;
  comment?: string;
  corrected_description?: string;
  corrected_significance?: Significance;
  corrected_value_after?: string;
}

export interface BulkVerificationPayload {
  difference_ids: string[];
  action: VerificationStatus;
  comment?: string;
}

export interface DiffReport {
  id: string;
  job_id: string;
  summary_stats: Record<string, number> | null;
  report_html: string | null;
  report_pdf_path: string | null;
  is_partial: boolean;
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

- [ ] **Step 2-5: API client, docdiff-api, queries, mutations**

Same structure as v0.1 but with updated paths and types:
- API paths: `/jobs/{id}/differences` instead of `/changes`
- Types: `DetectedDifference`, `VerificationActionPayload`, `BulkVerificationPayload`
- Query keys: `docdiffKeys.differences(jobId)` instead of `docdiffKeys.changes(jobId)`
- Mutations: `useVerifyDifference` instead of `useReviewChange`, `useBulkVerify` instead of `useBulkReview`

- [ ] **Step 6: Create utils/significance-colors.ts**

Same as v0.1 (colors unchanged).

- [ ] **Step 7: Create utils/difference-filters.ts**

Same as v0.1 but renamed from `change-filters.ts`. Uses `DifferenceType`, `VerificationStatus`, `Significance`.

- [ ] **Step 8: Commit**

```bash
cd /Users/chetan/Documents/Avyren-Technologies/Products/Mobile-ERP
git add web-system-app/src/features/docdiff/
git commit -m "feat(docdiff-web): add TypeScript types, API client, query hooks (v0.2 terminology)"
```

---

## Task 17: Frontend — Upload View + Processing View

Same as v0.1 with these changes:

- [ ] **UploadView.tsx changes:**
  - Two drop zones labeled "Version A" and "Version B" (not "Original"/"Revised")
  - **Editable text input fields** for version labels, defaulting to "Version A" and "Version B" (FR-01 v0.2)
  - Auto-confirm threshold slider/input (default 0.95, range 0.5-1.0) (FR-29 v0.2)
  - Button text: "Compare Documents" (not "Start Comparison")
  - FormData includes `label_a`, `label_b`, `auto_confirm_threshold`

- [ ] **ProcessingView.tsx changes:**
  - Stage names updated: "Parsing Version A", "Parsing Version B" instead of "Parsing Original", "Parsing Revised"

---

## Task 18: Frontend — Difference Viewer (Three-Panel Layout)

Renamed from "Review Interface" to "Difference Viewer" (the main verification interface).

**Files:**
- Create: `web-system-app/src/features/docdiff/components/DocumentViewer.tsx`
- Create: `web-system-app/src/features/docdiff/components/DifferenceList.tsx` (was `ChangeList.tsx`)
- Create: `web-system-app/src/features/docdiff/components/DifferenceDetail.tsx` (was `ChangeDetail.tsx`)
- Create: `web-system-app/src/features/docdiff/components/DifferenceViewer.tsx` (was `ReviewInterface.tsx`)
- Create: `web-system-app/src/features/docdiff/hooks/useDifferenceNavigation.ts` (was `useChangeNavigation.ts`)
- Create: `web-system-app/src/features/docdiff/hooks/useSyncScroll.ts`

Key changes from v0.1:

- [ ] **DifferenceList.tsx** (was ChangeList.tsx)
  - Column: "difference number" not "change number"
  - Status badges: Confirmed (green check), Dismissed (gray strikethrough), Corrected (blue pencil), Flagged (yellow flag), Pending (gray circle)
  - Filter dropdown: `verification_status` with values confirmed/dismissed/corrected/flagged/pending
  - Progress: "X of Y verified" (not "reviewed")

- [ ] **DifferenceDetail.tsx** (was ChangeDetail.tsx)
  - Expanded detail panel (FR-24 v0.2) showing:
    - Difference type and significance with confidence indicator (green/amber/red)
    - Before value (from Version A) → After value (from Version B) format
    - For table changes: row/column reference and context
    - For handwriting: source image + transcription
    - Verifier comment field
  - Action buttons updated:
    - **Confirm** (green) — "This difference is real and correctly described"
    - **Dismiss** (gray) — "This is a false positive"
    - **Correct** (blue) — Opens inline editor for corrected description
    - **Flag** (yellow) — Adds comment field for escalation
  - Auto-confirmed differences show a badge but are overridable

- [ ] **useDifferenceNavigation.ts** — Updated keyboard shortcuts:
  ```typescript
  // Keyboard shortcuts (FR-24 + 10.3 v0.2)
  if (e.key === "j" || e.key === "ArrowDown") goNext();
  if (e.key === "k" || e.key === "ArrowUp") goPrevious();
  if (e.key === "c") onConfirm?.();     // was "a" for accept
  if (e.key === "d") onDismiss?.();     // was "r" for reject
  if (e.key === "e") onCorrect?.();     // same
  if (e.key === "f") onFlag?.();        // same
  if (e.key === " ") goToNextUnverified?.();  // NEW: Space = next unverified
  ```

- [ ] **DifferenceViewer.tsx** (was ReviewInterface.tsx)
  - Documents are explicitly **read-only** — no editing of content (10.7 v0.2)
  - "Generate Diff Report" button always accessible, enabled at any point (FR-30)
  - Cosmetic differences can be toggled off to reduce visual noise (10.3 v0.2)
  - Unresolved regions shown with dashed gray outline

---

## Task 19: Frontend — Report View, History, Handwriting, Keyboard Help

**Files:**
- Create: `web-system-app/src/features/docdiff/components/ReportView.tsx`
- Create: `web-system-app/src/features/docdiff/components/ComparisonHistory.tsx` **(NEW)**
- Create: `web-system-app/src/features/docdiff/components/HandwritingReview.tsx`
- Create: `web-system-app/src/features/docdiff/components/UnresolvedRegion.tsx`
- Create: `web-system-app/src/features/docdiff/components/KeyboardShortcutsHelp.tsx`

- [ ] **ReportView.tsx — Restructured (FR-30 through FR-35)**

The report view now renders the v0.2 report structure:

1. **Header**: Version A label, Version B label, comparison date, model used, processing time
2. **Executive Summary**: Total differences, by significance, one-line verdict (e.g., "14 differences detected — 3 material, 7 substantive, 4 cosmetic")
3. **Quick Reference Table**: Compact one-page table of all material + substantive differences (difference #, page, type, before → after) — suitable for printing
4. **Material Differences**: All material-significance diffs listed first with full detail
5. **Substantive Differences**: Same format
6. **Cosmetic Differences**: Same format (collapsible)
7. **Flagged Items**: Differences flagged for review with verifier comments
8. **Dismissed Items**: Count only (transparency)
9. **Unresolved Regions**: Regions that couldn't be analyzed

Shows "Partial Report" badge if `is_partial=true` (not all differences verified).
"Generate Diff Report" button (can regenerate at any time).
"Return to Viewer" button (not "Return to Review").
"Download PDF" button.

- [ ] **ComparisonHistory.tsx — NEW (FR-39, FR-40, 10.6)**

A table view showing all previous comparisons:

| Column | Data |
|---|---|
| Version A Label | From `JobListItem.label_a` |
| Version B Label | From `JobListItem.label_b` |
| Date | `created_at` formatted |
| Total Differences | `total_differences` |
| Material | `material_count` |
| Verification Status | Badge: "Complete" / "Partial (X/Y)" / "Not Started" |
| Actions | Open (navigate to DifferenceViewer), Download Report |

- Sortable by any column
- Click to reopen a comparison — loads DifferenceViewer with all saved verification decisions
- Uses `useJobs()` query hook

- [ ] **HandwritingReview.tsx**

Same as v0.1, but actions are "Confirm" (transcription correct), "Correct" (type accurate reading), "Flag" (illegible — add comment).

- [ ] **UnresolvedRegion.tsx**

Same as v0.1, but button text: "Add Difference Manually" (not "Add Change Manually") and "No Difference" (not "No Difference" — same).

- [ ] **KeyboardShortcutsHelp.tsx — Updated shortcuts**

```
J / ↓  — Next difference
K / ↑  — Previous difference
C      — Confirm current difference
D      — Dismiss current difference
E      — Open correction editor
F      — Flag for review
Space  — Jump to next unverified difference
?      — Toggle this help
```

---

## Task 20: Frontend — Main Screen + Route Integration

- [ ] **DocDiffScreen.tsx — Add history view**

```typescript
type View = "history" | "upload" | "processing" | "verification" | "report";

// Default view is "history" (shows comparison history list)
// "Upload" is accessed via a "New Comparison" button in the history view
// After job creation → "processing"
// After processing → "verification" (was "review")
// From verification → "report"
// From report → back to "verification" or "history"
```

- [ ] **Route in App.tsx**

Same as v0.1:
```tsx
<Route path="docdiff" element={<DocDiffScreen />} />
```

---

## Task Dependency Graph

```
Task 1 (scaffold) ──→ Task 2 (DB) ──→ Task 3 (schemas) ──→ Task 4 (auth) ──→ Task 5 (health/router/jobs)
                  └──→ Task 6 (AI base) ──→ Task 7 (providers)
                  └──→ Task 8 (prompts)
                  └──→ Task 9 (PDF utils)
                  └──→ Task 10 (diff utils)
Task 5 + 7 + 8 + 9 + 10 ──→ Task 11 (stages 1-4) ──→ Task 12 (stages 5-8) ──→ Task 13 (orchestrator)
Task 3 + 13 ──→ Task 14 (API endpoints)
Task 14 ──→ Task 15 (Docker)
Task 5 ──→ Task 16 (FE types/API) ──→ Task 17 (upload/processing) ──→ Task 18 (verification UI) ──→ Task 19 (report/history/extras) ──→ Task 20 (integration)
```

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
