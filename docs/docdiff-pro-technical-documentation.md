# DocDiff Pro — Comprehensive Technical Documentation

**Version:** 2.0
**Date:** April 2026
**Service Type:** AI-Powered Document Comparison Microservice
**Status:** Production-Ready

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [System Architecture](#2-system-architecture)
3. [Technology Stack](#3-technology-stack)
4. [Backend Service (docdiff-service)](#4-backend-service-docdiff-service)
5. [8-Stage Processing Pipeline](#5-8-stage-processing-pipeline)
6. [AI Provider Integration](#6-ai-provider-integration)
7. [Database Schema](#7-database-schema)
8. [API Reference](#8-api-reference)
9. [Authentication & Authorization](#9-authentication--authorization)
10. [Frontend Implementation (web-system-app)](#10-frontend-implementation-web-system-app)
11. [ERP Backend Integration](#11-erp-backend-integration)
12. [Real-Time Communication (SSE)](#12-real-time-communication-sse)
13. [File Storage & PDF Processing](#13-file-storage--pdf-processing)
14. [Accuracy Engineering](#14-accuracy-engineering)
15. [Deployment & Infrastructure](#15-deployment--infrastructure)
16. [Configuration Reference](#16-configuration-reference)
17. [User Workflow & UX](#17-user-workflow--ux)
18. [Roadmap & Evolution](#18-roadmap--evolution)

---

## 1. Executive Summary

**DocDiff Pro** is an AI-powered document comparison service integrated into the Avy ERP platform. It accepts two PDF document versions, processes them through an 8-stage asynchronous pipeline, and produces a structured diff report with AI-classified significance levels (material, substantive, cosmetic). A human verification workflow allows reviewers to confirm, dismiss, correct, or flag each detected difference before generating a final report.

### Key Capabilities

- Compare two PDF versions (born-digital, scanned, or mixed)
- AI-powered content extraction using Vision Language Models (VLMs)
- Word-level text diffing with adjacent change merging
- Table-aware comparison (cell changes, row additions/deletions, structure changes)
- 3-tier significance classification: Material > Substantive > Cosmetic
- Deterministic rule engine handles ~90% of classifications (no AI cost)
- 4-pass deduplication achieving 97% noise reduction
- Human verification workflow with keyboard shortcuts
- Continuous learning from reviewer corrections
- Multi-provider AI support (Anthropic Claude, Google Gemini, OpenRouter, local Qwen3-VL)
- PDF report generation with HTML/PDF export

### Performance Metrics

| Metric | Value |
|--------|-------|
| Noise reduction | 97% (506 raw entries -> ~56 after dedup) |
| Rule engine coverage | ~90% of diffs classified without AI |
| Born-digital extraction speed | < 50ms/page |
| Processing time (10-page job) | 30-90 seconds |
| Cost per 10-page job | $0.50-2.00 (cloud) / $0.00 (local) |
| Max document size | 50 MB, 50 pages |

---

## 2. System Architecture

### High-Level Architecture

```
                           +-------------------------------------------+
                           |           Avy ERP Platform                |
                           |                                           |
  +-------------------+    |   +------------------+                    |
  |                   |    |   |  avy-erp-backend  |                   |
  |  Web Browser      |    |   |  (Node.js/Express)|                   |
  |  (React SPA)      |    |   |  Port 3000        |                   |
  |                   |----+-->|  - JWT issuer      |                   |
  |  /app/docdiff     |    |   |  - Permissions     |                   |
  |                   |    |   |  - Nav manifest    |                   |
  +--------+----------+    |   +------------------+                    |
           |               |                                           |
           | Direct HTTP   |   +------------------+   +-----------+    |
           | (JWT auth)    |   | docdiff-service   |   |  Redis    |   |
           +---------------+-->|  (FastAPI/Python)  |-->|  DB 2     |   |
                           |   |  Port 8000         |   +-----------+   |
                           |   |  - Pipeline        |                   |
                           |   |  - AI providers    |   +-----------+   |
                           |   |  - Report gen      |-->| PostgreSQL|   |
                           |   +--------+-----------+   | docdiff   |   |
                           |            |               | schema    |   |
                           |   +--------v-----------+   +-----------+   |
                           |   | ARQ Worker         |                   |
                           |   | (Background jobs)  |                   |
                           |   +--------------------+                   |
                           +-------------------------------------------+
```

### Microservice Communication Pattern

The DocDiff service operates as a **standalone microservice** with these integration points:

1. **Frontend -> DocDiff Service**: Direct HTTP calls from the React SPA to FastAPI (port 8000), NOT proxied through the Node.js backend
2. **Shared JWT**: Both services validate the same JWT token using a shared `JWT_SECRET`
3. **Shared PostgreSQL**: Same database instance, separate `docdiff` schema
4. **Shared Redis**: Same Redis instance, DocDiff uses DB 2 (ERP uses DB 0/1)
5. **ERP Backend awareness**: Permissions, navigation manifest, and RBAC configured in the Node.js backend

### Why a Separate Microservice?

| Decision | Rationale |
|----------|-----------|
| Python (not Node.js) | Python ecosystem for AI/ML, PDF processing, VLM SDKs |
| FastAPI (not Express) | Native async, automatic OpenAPI docs, Pydantic validation |
| Separate service | Independent scaling, isolated failures, language best-fit |
| Direct frontend access | No Node.js coupling, lower latency, simpler architecture |
| SSE (not Socket.io) | FastAPI native SSE support, no bridge overhead |
| Shared JWT (not service-to-service auth) | Simpler auth, no token exchange, same trust boundary |

---

## 3. Technology Stack

### DocDiff Service (Python)

| Category | Technology | Version | Purpose |
|----------|-----------|---------|---------|
| Framework | FastAPI | 0.115+ | REST API, async request handling |
| Server | Uvicorn | 0.34+ | ASGI server |
| ORM | SQLAlchemy | 2.0+ (async) | Database access |
| Migrations | Alembic | 1.14+ | Schema version control |
| Validation | Pydantic | 2.10+ | Request/response schemas |
| Task Queue | ARQ | 0.26+ | Redis-backed async job queue |
| HTTP Client | httpx | 0.28+ | Async HTTP for AI providers |
| AI: Anthropic | anthropic | 0.52+ | Claude SDK |
| AI: Google | google-genai | 1.14+ | Gemini SDK |
| PDF: Parsing | PyMuPDF (fitz) | 1.25+ | Fast PDF text/table extraction |
| PDF: Layout | Docling | 2.25+ | Complex layout analysis |
| PDF: Reports | WeasyPrint | 63+ | HTML-to-PDF conversion |
| Text Diff | diff-match-patch | 20241021 | Word-level text comparison |
| Images | Pillow | 11.1+ | Image processing |
| Auth: JWT | python-jose | 3.3+ | JWT token validation |
| Retry | tenacity | 9.0+ | Exponential backoff for AI calls |
| Database | PostgreSQL | 18 | Via asyncpg driver |
| Cache/Queue | Redis | 7+ | Job queue + caching |

### Frontend (React/TypeScript)

| Category | Technology | Purpose |
|----------|-----------|---------|
| Framework | React 18 | UI components |
| Build | Vite | Development + bundling |
| Language | TypeScript (strict) | Type safety |
| Data Fetching | React Query (TanStack) | Server state management |
| HTTP Client | Axios | API calls |
| Styling | Tailwind CSS | Utility-first CSS |
| Routing | React Router v6 | Client-side routing |
| Notifications | Toast (custom) | Success/error feedback |

---

## 4. Backend Service (docdiff-service)

### Directory Structure

```
docdiff-service/
├── app/
│   ├── main.py                     # FastAPI app initialization, lifespan hooks
│   ├── config.py                   # Pydantic Settings (env-driven config)
│   ├── database.py                 # SQLAlchemy async engine + session factory
│   ├── api/                        # API endpoints
│   │   ├── router.py               # Main API router (/api/v1)
│   │   ├── health.py               # GET /health
│   │   ├── jobs.py                 # CRUD for comparison jobs
│   │   ├── sse.py                  # Server-Sent Events for progress
│   │   ├── differences.py          # Difference CRUD + verification
│   │   ├── documents.py            # Page images + content
│   │   ├── reports.py              # Report generation + PDF download
│   │   └── api_keys.py             # API key management
│   ├── auth/                       # Authentication
│   │   ├── middleware.py           # Dual auth (JWT + API key) dependency
│   │   ├── jwt_validator.py        # HS256 JWT validation
│   │   └── api_key.py              # API key generation + verification
│   ├── models/                     # SQLAlchemy ORM models
│   │   ├── job.py                  # ComparisonJob
│   │   ├── document.py             # Document + DocumentPage
│   │   ├── difference.py           # DetectedDifference
│   │   ├── report.py               # DiffReport
│   │   ├── correction.py           # ReviewerCorrection
│   │   └── api_key.py              # APIKey
│   ├── schemas/                    # Pydantic request/response models
│   │   ├── job.py
│   │   ├── difference.py
│   │   └── report.py
│   ├── pipeline/                   # 8-stage processing pipeline
│   │   ├── orchestrator.py         # Pipeline coordinator
│   │   ├── stage_1_ingestion.py
│   │   ├── stage_2_classification.py
│   │   ├── stage_3_extraction.py
│   │   ├── stage_4_normalization.py
│   │   ├── stage_5_alignment.py
│   │   ├── stage_6_diff.py
│   │   ├── stage_7_scoring.py
│   │   ├── stage_8_assembly.py
│   │   └── visual_compare.py       # Stage 6.5: LLM visual diff
│   ├── ai/                         # AI provider implementations
│   │   ├── base.py                 # Abstract AIProvider interface
│   │   ├── anthropic_provider.py   # Claude integration
│   │   ├── google_provider.py      # Gemini integration
│   │   ├── openrouter_provider.py  # OpenRouter integration
│   │   ├── qwen_local_provider.py  # Self-hosted Qwen3-VL
│   │   └── response_parser.py      # JSON extraction from AI responses
│   ├── pdf/                        # PDF processing
│   │   ├── fast_parser.py          # PyMuPDF (born-digital)
│   │   ├── parser.py               # Docling (complex layouts)
│   │   ├── metadata.py             # PDF validation + metadata extraction
│   │   ├── renderer.py             # Page-to-PNG rendering
│   │   └── report_generator.py     # HTML/PDF report creation
│   ├── prompts/                    # AI prompt engineering
│   │   ├── system_prompts.py       # Extraction + classification system prompts
│   │   ├── extract_page.py         # Page content extraction prompt
│   │   ├── classify_difference.py  # Significance classification prompt
│   │   └── corrections_library.py  # Few-shot examples from reviewer corrections
│   ├── utils/                      # Utilities
│   │   ├── diff_utils.py           # Text diffing (diff-match-patch)
│   │   ├── table_utils.py          # Table comparison
│   │   └── bbox.py                 # Bounding box math (IoU, intersection)
│   └── workers/                    # Background job processing
│       └── job_worker.py           # ARQ worker configuration
├── alembic/                        # Database migrations
│   ├── env.py
│   └── versions/
│       ├── 671d728b59d1_initial_docdiff_schema.py
│       └── c798bf45b3e9_add_reviewer_corrections_table.py
├── storage/                        # Local file storage
│   ├── uploads/                    # Uploaded PDFs + rendered pages
│   └── reports/                    # Generated PDF reports
├── tests/                          # Test suite
├── Dockerfile                      # Multi-stage Python build
├── docker-compose.yml              # Service orchestration
├── requirements.txt                # Production dependencies
├── requirements-dev.txt            # Dev dependencies
├── pyproject.toml                  # Python project metadata
├── alembic.ini                     # Alembic config
├── ACCURACY.md                     # Accuracy improvement documentation
├── ROADMAP.md                      # Development roadmap
├── .env.example                    # Environment variable template
└── .gitignore
```

### Application Initialization (main.py)

The FastAPI app uses a lifespan context manager for startup/shutdown:

**Startup:**
1. Initialize SQLAlchemy async engine
2. Create database tables if needed
3. Run Alembic migrations
4. Initialize Redis connection pool
5. Register API routes

**Shutdown:**
1. Close Redis connections
2. Dispose database engine

### Configuration (config.py)

Uses Pydantic `BaseSettings` with environment variable prefix `DOCDIFF_`:

```python
class Settings(BaseSettings):
    host: str = "0.0.0.0"
    port: int = 8000
    env: str = "development"
    log_level: str = "INFO"
    cors_origins: str = "http://localhost:5173,http://localhost:3000"
    database_url: str = "postgresql+asyncpg://..."
    database_schema: str = "docdiff"
    redis_url: str = "redis://localhost:6379/2"
    jwt_secret: str = ""
    storage_path: str = "./storage"
    anthropic_api_key: str = ""
    google_api_key: str = ""
    openrouter_api_key: str = ""
    qwen_local_endpoint: str = "http://localhost:8080/v1"
    default_provider: str = "google"
    default_model: str = "gemini-2.5-flash"
    confidence_threshold: float = 0.75
    auto_confirm_threshold: float = 0.95
    page_render_dpi: int = 250
    max_pages: int = 20
    max_file_size_mb: int = 50
    max_retries: int = 3
    retry_backoff_base: int = 1
```

---

## 5. 8-Stage Processing Pipeline

The core of DocDiff Pro is an **8-stage asynchronous pipeline** orchestrated by `pipeline/orchestrator.py`. Each stage is an independent module that reads from and writes to the database.

```
PDF Upload
  |
  v
Stage 1: Ingestion & Validation
  |  - Validate PDFs (encryption, size, page count)
  |  - Extract metadata (title, author, dates)
  |  - Render all pages to PNG (adaptive DPI)
  |  - Create DocumentPage records
  v
Stage 2: Page Classification
  |  - Analyze text density per page
  |  - Classify: born_digital / scanned / mixed
  |  - Flag pages with handwriting/annotations
  v
Stage 3: Content Extraction
  |  - Born-digital: PyMuPDF fast parser (<50ms/page)
  |  - Scanned: VLM extraction (Gemini/Claude)
  |  - Mixed: Two-pass merge (PyMuPDF + VLM)
  |  - Both documents processed concurrently
  v
Stage 4: Normalization
  |  - Unicode NFKC normalization
  |  - Whitespace collapse
  |  - Generate stable block IDs
  |  - Update reading order
  v
Stage 5: Alignment
  |  - Page-level: semantic content similarity (0.3 threshold)
  |  - Block-level: 3-pass matching
  |    Pass 1: Section titles (>= 0.7 similarity)
  |    Pass 2: Tables (>= 0.5 structural match)
  |    Pass 3: Text blocks (>= 0.4 content match)
  |  - Unmatched pages -> single scope-difference entry
  v
Stage 6: Diff Computation
  |  - Word-level text diffing (diff-match-patch)
  |  - Table cell comparison (number-normalized)
  |  - Adjacent diff merging ("18%" -> "21%" = 1 change)
  |  - Whitespace-only changes filtered at source
  v
Stage 6.5: Visual Comparison (scanned/mixed pages only)
  |  - Send both page images to VLM simultaneously
  |  - VLM identifies differences visually (bypasses OCR)
  |  - Results merged with text-pipeline diffs
  v
Stage 7: Scoring & Classification
  |  - Deterministic rule engine (~90% coverage):
  |    - Whitespace-only -> cosmetic
  |    - Version/revision IDs -> cosmetic
  |    - Document reference IDs -> cosmetic
  |    - Numbers/currency changes -> material
  |    - Legal keywords -> material
  |    - Table changes -> material
  |    - Annotations -> substantive
  |    - Dates (context-aware) -> cosmetic/substantive
  |  - AI escalation: only if rule confidence < 0.72 (~10% of diffs)
  |  - Few-shot examples from corrections library
  |  - Sets needs_verification (< 0.75) and auto_confirmed (>= 0.95)
  v
Stage 8: Assembly & Deduplication
  |  - 4-pass deduplication:
  |    1. OCR garbage removal (garbled characters)
  |    2. Header/footer collapse (3+ pages -> single entry)
  |    3. Page number filtering ("Page X of Y" patterns)
  |    4. Same-value deduplication (identical before/after on same page)
  |  - Merge delete+add pairs into modifications
  |  - Renumber differences (1, 2, 3...)
  |  - Create DetectedDifference DB records
  |  - Set job status to ready_for_review
  v
Ready for Human Verification
```

### Pipeline Orchestrator

```python
async def run_pipeline(job_id: str):
    """Execute all pipeline stages sequentially."""
    # Tracks in-memory progress via _job_progress dict
    # Updates job.status, job.stage_progress after each stage
    # Catches exceptions -> sets job.status to failed, stores error_message
    # Computes total elapsed time in milliseconds
```

**Worker Configuration (ARQ):**
- `max_jobs: 1` — single concurrent job per worker (prevents resource contention)
- `job_timeout: 3600` seconds (60 minutes max)
- `keep_result: 60` seconds (result cached in Redis briefly)
- `retry_jobs: false` — no auto-retry on failure

### Stage Details

#### Stage 1: Ingestion & Validation

**Input:** Raw PDF files
**Output:** Validated files + metadata + rendered page PNGs

Process:
1. Validate each PDF: check for encryption, page count limits, file size limits
2. Extract metadata: title, author, creator, producer, creation_date, pdf_version
3. Create `Document` records (one per uploaded file)
4. Render every page to PNG at adaptive DPI:
   - Born-digital pages: 150 DPI (text is extracted from text layer, not image)
   - Scanned pages: 300 DPI (higher resolution for better VLM OCR)
5. Create `DocumentPage` records with `image_path` pointing to rendered PNG
6. Storage structure: `storage/uploads/{job_id}/{role}_pages/page_XXX.png`

#### Stage 2: Page Classification

**Input:** Document pages with rendered images
**Output:** Page type classifications + confidence scores

Uses text density analysis (not simple text-layer detection):
- Extracts text blocks and image blocks from each page via PyMuPDF
- Computes `text_coverage` (fraction of page area covered by text)
- Computes `image_coverage` (fraction covered by images)
- Classification rules:
  - `text_coverage > 0.3` AND `image_coverage < 0.2` -> **born_digital** (0.95 confidence)
  - `image_coverage > 0.7` AND `text_coverage < 0.1` -> **scanned** (0.90 confidence)
  - `image_coverage > 0.5` AND text present -> **mixed** (0.75 confidence) — OCR'd scanned PDF
- Also flags pages with handwriting and annotations

#### Stage 3: Content Extraction

**Input:** Classified pages
**Output:** Structured content JSON per page (blocks with type, bbox, text, confidence)

Three extraction paths based on page classification:

**Fast Path (born-digital):** PyMuPDF `fast_parser.py`
- Extracts text directly from PDF text layer (no OCR, no AI)
- Speed: < 50ms per page
- Detects headings via font size (H1 >= 15pt, H2 >= 12pt + bold)
- Detects header/footer zones (top 8%, bottom 5% of page)
- Extracts tables via PyMuPDF's `find_tables()` method
- Normalizes bounding boxes to 0-1 fractions

**VLM Path (scanned):** Vision Language Model
- Sends rendered page image (PNG) to AI provider
- Structured prompt demands per-block JSON with:
  - Block types: text, table, annotation, header, footer, image
  - Normalized 0-1 bounding boxes
  - Per-block confidence scores
  - Table format: rows, cols, cells (with row/col/rowspan/colspan)
  - Reading order specification
- Rate-limited: 1-4 second inter-call sleep between pages

**Two-Pass Merge (mixed):**
1. PyMuPDF extracts whatever text layer exists
2. VLM extracts from the rendered page image
3. For each VLM block, find the closest PyMuPDF block by position overlap
4. If PyMuPDF text is more complete (longer), use it instead of VLM OCR
5. Result: VLM's structural accuracy + PyMuPDF's text fidelity
6. Labeled as `vlm+pymupdf` extraction method

Both documents are processed **concurrently** via `asyncio.gather()`.

#### Stage 4: Normalization

**Input:** Raw extracted content
**Output:** Normalized content with stable block IDs

- Applies Unicode NFKC normalization to all text
- Collapses whitespace runs (multiple spaces -> single space)
- Generates stable block IDs: `{role}_{page:03d}_blk_{counter:04d}`
- Updates reading_order with new IDs
- Normalizes text in all block types (text, tables, annotations)

#### Stage 5: Alignment

**Input:** Normalized content from both documents
**Output:** `AlignedPair` objects mapping version A blocks to version B blocks

**Page-level alignment (semantic):**
- Extracts all text from each page
- Computes pairwise similarity scores between all pages
- Threshold: 0.3 (low — prevents catastrophic mismatches)
- Unmatched pages (appendices, new sections) get a single scope-difference entry instead of per-block deletion entries
- Impact: When Version A has 20 pages and Version B has 14, old approach generated ~300 false deletions; new approach generates ~5 scope entries

**Block-level alignment (3-pass):**
1. **Pass 1:** Match section titles with >= 0.7 similarity
2. **Pass 2:** Match tables by structural similarity with >= 0.5 threshold
3. **Pass 3:** Match remaining text blocks with >= 0.4 similarity

Returns `AlignedPair(version_a_block, version_b_block, alignment_score)` objects.

#### Stage 6: Diff Computation

**Input:** Aligned block pairs
**Output:** `RawDiffRecord` objects

For each aligned pair:
- **Both blocks present:** Compute text diff (word-level) OR table diff OR annotation diff
- **Only Version A block:** Deletion record
- **Only Version B block:** Addition record

**Word-level diffing:** Uses `diff-match-patch` library
- Maps words to characters, diffs characters, maps back
- Semantic cleanup via DMP
- Adjacent diff merging: consecutive changes from same block pair become a single logical change
  - Example: "18%" -> "21%" stays as one modification, not split into "delete 8" + "add 2"

**Table comparison:**
- Cell-level comparison with number normalization ("2.0" = "2", "1,000" = "1000")
- Detects: cell value changes, row additions/deletions, structural changes, header changes
- Fuzzy row matching for reordered rows
- Preserves original raw values for user display

**Diff types produced:** text_addition, text_deletion, text_modification, table_cell_change, table_row_addition, table_row_deletion, table_structure_change, annotation_present_in_b, annotation_removed_from_b, section_moved, formatting_change

#### Stage 6.5: Visual Comparison (Optional)

**Input:** Rendered page images (scanned/mixed pages only)
**Output:** Additional difference records

- Sends BOTH page images (version A and version B) to VLM simultaneously
- VLM identifies differences directly from visual content (bypasses OCR entirely)
- Structured prompt specifies output format with bbox, before/after values, significance, confidence
- Results merged with text-pipeline diffs from Stage 6
- Purpose: catches visual differences that OCR/text extraction might miss

#### Stage 7: Scoring & Classification

**Input:** Raw diff records
**Output:** Classified diffs with significance, confidence, needs_verification flags

**Two-tier classification system:**

**Tier 1: Deterministic Rule Engine (~90% of diffs)**
No AI cost, instant classification:

| Pattern | Classification | Confidence |
|---------|---------------|------------|
| Whitespace-only changes | cosmetic | 0.95 |
| Version/revision IDs (Rev.7 -> Rev.8) | cosmetic | 0.93 |
| Document reference IDs (RPT-001-A -> RPT-001-B) | cosmetic | 0.92 |
| Numbers/currency changes | material | 0.90 |
| Dates in headers/footers | cosmetic | 0.88 |
| Dates in body content | substantive | 0.85 |
| Legal keywords (warranty, liability, etc.) | material | 0.90 |
| Annotations (stamps, handwriting) | substantive | 0.85 |
| Table changes | material | 0.88 |
| Page numbers ("Page X of Y") | cosmetic | 0.95 |

**Tier 2: AI Escalation (~10% of diffs)**
Only triggered when rule engine confidence < 0.72:
- Few-shot examples from corrections library injected into prompt
- AI returns: `{significance, confidence, reasoning}`
- Provider: configurable (Gemini Flash is cheapest, Claude Sonnet most accurate)

**Flags set:**
- `needs_verification`: confidence < 0.75 (requires human review)
- `auto_confirmed`: confidence >= 0.95 (system-confirmed, still reviewable)

#### Stage 8: Assembly & Deduplication

**Input:** Scored diff records
**Output:** Final `DetectedDifference` DB records

**4-pass deduplication:**
1. **OCR garbage removal:** Removes garbled characters, non-Latin clusters, high symbol ratios
2. **Header/footer collapse:** Same change on 3+ pages -> single cosmetic entry with note "(found on N pages)"
3. **Page number filtering:** Removes "Page X of Y" patterns
4. **Same-value deduplication:** Identical before -> after on same page -> keep first occurrence

**Post-dedup processing:**
- Merge adjacent delete+add pairs from same page into modifications
- Renumber all differences sequentially (1, 2, 3...)
- Create `DetectedDifference` database records
- Update job counters: `total_differences`, `differences_verified`
- Set job status to `ready_for_review`

### Pipeline Accuracy Impact

| Noise Source | Before Dedup | After Dedup | Reduction |
|---|---|---|---|
| Page misalignment (appendices) | ~300 | ~5 | 98% |
| Header/footer repeats | ~40 | ~3 | 93% |
| OCR garbage | ~80 | 0 | 100% |
| Page number changes | ~24 | 0 | 100% |
| Character fragmentation | ~15 | ~5 | 67% |
| Same-value duplicates | ~8 | ~2 | 75% |
| **Total noise** | **~465** | **~15** | **97%** |
| **Genuine differences** | **~41** | **~41** | **0% loss** |
| **Final report size** | **506** | **~56** | **89% reduction** |

---

## 6. AI Provider Integration

### Provider Interface

All AI providers implement a common abstract interface:

```python
class AIProvider(ABC):
    async def call(prompt, images=None, system=None) -> AIResponse
    async def extract_page_content(image, prompt, system=None) -> AIResponse
    async def classify_difference(context, prompt, system=None) -> AIResponse
    async def transcribe_handwriting(image, prompt, system=None) -> AIResponse
```

### Supported Providers

| Provider | SDK | Models | Use Case | Cost |
|----------|-----|--------|----------|------|
| **Google Gemini** | google-genai | gemini-2.5-flash, gemini-2.5-pro, gemini-2.5-flash-lite, gemini-2.0-flash | Default; fast, cost-effective | Low |
| **Anthropic Claude** | anthropic | claude-3-7-sonnet, claude-3-opus | Highest accuracy | High |
| **OpenRouter** | httpx (REST) | google/gemma-4-31b-it:free, gemini-2.5-pro-preview | Free tier available | Free-High |
| **Qwen3-VL (Local)** | httpx (OpenAI-compat) | qwen3-vl-8b, qwen3-vl-30b-a3b | Self-hosted, zero API cost | Free |

### Provider-Specific Details

**Anthropic (Claude):**
- Client: `anthropic.AsyncAnthropic`
- Images sent as base64-encoded PNG with `media_type: image/png`
- Max tokens: 4096
- Best for: highest accuracy classification

**Google (Gemini):**
- Client: `google.genai.Client` with async methods
- Adaptive max_tokens: 8192 for extraction, 512 for classification
- Response mime type: `application/json`
- Default temperature: 0.1
- Best for: cost-effective processing, good accuracy

**OpenRouter:**
- Endpoint: `https://openrouter.ai/api/v1`
- Uses httpx.AsyncClient
- Rate limit handling: 429 -> RateLimitError with retry
- Best for: free tier access, model variety

**Qwen3-VL (Local):**
- Endpoint: `http://localhost:8080/v1` (configurable)
- OpenAI-compatible API format
- Timeout: 180 seconds (longer for large images)
- Best for: zero-cost processing, data privacy

### Retry Logic

All providers use tenacity for exponential backoff:
- Max attempts: 6
- Backoff: exponential with multiplier=3, min=5s, max=60s
- Retries on: RateLimitError, ServerError, TimeoutError

### Response Parsing

`response_parser.py` handles AI response extraction:
- `extract_json_from_text()`: Extracts JSON from markdown code blocks or raw JSON
- `parse_ai_response()`: Parses and validates against optional Pydantic schema
- `safe_parse_or_flag()`: Returns (parsed_dict, is_flagged) tuple for graceful degradation

### AI Prompt Engineering

**Extraction Prompt (`extract_page.py`):**
- Emphasizes character-level fidelity (numbers, units, symbols matter)
- Requires valid JSON output with normalized 0-1 bounding boxes
- Specifies block types: text, table, annotation, header, footer, image
- Includes complete JSON example with all block types
- Header/footer zone detection rules
- Multi-column layout handling

**Classification Prompt (`classify_difference.py`):**
- Provides difference type, value_before, value_after, context
- Defines significance levels with concrete examples:
  - MATERIAL: tolerances, material grades, quantities, pricing, safety
  - SUBSTANTIVE: scope descriptions, requirement rewording, procedures
  - COSMETIC: formatting, whitespace, pagination, version IDs
  - UNCERTAIN: flag for human review
- Expected JSON response: `{significance, confidence, reasoning}`

**Visual Comparison Prompt (`visual_compare.py`):**
- Compares two page images side-by-side
- Identifies all visual differences with bbox coordinates
- Warns against rendering artifacts and instructs to focus on real content changes

**Corrections Library (`corrections_library.py`):**
- Queries `reviewer_corrections` table for examples matching current diff type
- Formats as few-shot examples in AI classification prompt
- Continuously improves classification accuracy as reviewers correct predictions

### Token Savings Strategy

| Optimization | Token Reduction | Status |
|---|---|---|
| System prompt caching | 30-40% | Implemented |
| Rule engine (no AI for 90% of diffs) | 80-90% of classification cost | Implemented |
| Corrections library (fewer AI calls over time) | 10-20% | Implemented |
| PaddleOCR for scanned extraction | 70% of extraction cost | Planned |
| Local Qwen fine-tuning | 100% of classification cost | Planned |

---

## 7. Database Schema

### Schema: `docdiff` (PostgreSQL, separate from ERP schema)

```
┌─────────────────────┐
│   ComparisonJob      │
│   (orchestration)    │
├─────────────────────┤      ┌──────────────────┐
│ id (UUID PK)        │──┐   │   Document        │
│ status (enum)       │  │   ├──────────────────┤
│ model_provider      │  ├──>│ id (UUID PK)     │
│ model_name          │  │   │ job_id (FK)      │
│ current_stage (1-8) │  │   │ role (enum)      │    ┌────────────────────┐
│ stage_progress (JSON)│ │   │ label            │    │  DocumentPage       │
│ total_differences   │  │   │ filename         │    ├────────────────────┤
│ differences_verified│  │   │ file_path        │───>│ id (UUID PK)       │
│ auto_confirm_thresh │  │   │ file_size_bytes  │    │ document_id (FK)   │
│ confidence_threshold│  │   │ page_count       │    │ page_number        │
│ processing_time_ms  │  │   │ pdf_metadata(JSON)│   │ page_type (enum)   │
│ token_usage (JSON)  │  │   └──────────────────┘    │ has_handwriting    │
│ user_id             │  │                            │ has_annotations    │
│ company_id          │  │   ┌──────────────────────┐│ content (JSON)     │
│ api_key_id          │  │   │ DetectedDifference   ││ extraction_method  │
│ error_message       │  ├──>│ (found changes)      ││ extraction_confid. │
│ created_at          │  │   ├──────────────────────┤│ image_path         │
│ updated_at          │  │   │ id (UUID PK)         ││ processing_status  │
└─────────────────────┘  │   │ job_id (FK)          ││ error_message      │
                         │   │ difference_number    │└────────────────────┘
                         │   │ difference_type(enum)│
                         │   │ significance (enum)  │
                         │   │ confidence (float)   │
                         │   │ page_version_a (int) │
                         │   │ page_version_b (int) │
                         │   │ bbox_version_a (JSON)│
                         │   │ bbox_version_b (JSON)│
                         │   │ value_before (text)  │
                         │   │ value_after (text)   │
                         │   │ context (text)       │
                         │   │ summary (text)       │
                         │   │ block_id_version_a   │
                         │   │ block_id_version_b   │
                         │   │ verification_status  │
                         │   │ auto_confirmed (bool)│
                         │   │ needs_verification   │
                         │   │ verifier_comment     │
                         │   │ corrected_description│
                         │   │ verified_at          │
                         │   └──────────────────────┘
                         │
                         │   ┌──────────────────┐
                         ├──>│   DiffReport      │
                         │   ├──────────────────┤
                         │   │ id (UUID PK)     │
                         │   │ job_id (FK, UQ)  │
                         │   │ summary_stats(JSON)│
                         │   │ report_html      │
                         │   │ report_pdf_path  │
                         │   │ is_partial (bool)│
                         │   │ generated_at     │
                         │   └──────────────────┘
                         │
┌─────────────────────┐  │
│ ReviewerCorrection   │  │
├─────────────────────┤  │
│ id (UUID PK)        │  │
│ value_before        │  │
│ value_after         │  │
│ difference_type     │  │
│ original_significance│ │
│ corrected_significance││
│ verifier_comment    │  │
│ context             │  │
│ created_at          │  │
└─────────────────────┘  │
                         │
┌─────────────────────┐  │
│     APIKey           │  │
├─────────────────────┤  │
│ id (UUID PK)        │  │
│ key_hash (SHA256)   │  │
│ name               │  │
│ is_active (bool)    │  │
│ created_at          │  │
│ last_used_at        │  │
└─────────────────────┘
```

### Enums

**JobStatus:** uploading, parsing_version_a, parsing_version_b, aligning, diffing, classifying, assembling, ready_for_review, verification_in_progress, completed, failed, cancelled

**DocumentRole:** version_a, version_b

**PageType:** born_digital, scanned, mixed

**DifferenceType:** text_addition, text_deletion, text_modification, table_cell_change, table_row_addition, table_row_deletion, table_structure_change, annotation_present_in_b, annotation_removed_from_b, section_moved, formatting_change

**Significance:** material, substantive, cosmetic, uncertain

**VerificationStatus:** pending, confirmed, dismissed, corrected, flagged

**ProcessingStatus:** pending, completed, failed

### Migrations

| Migration ID | Description |
|---|---|
| `671d728b59d1` | Initial docdiff schema — all core tables |
| `c798bf45b3e9` | Add reviewer_corrections table |

---

## 8. API Reference

### Base URL: `/api/v1`

### Health Check

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/health` | None | Service health (DB, Redis, Qwen status) |

### Jobs

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | `/jobs` | JWT/API Key | Create comparison job (multipart/form-data) |
| GET | `/jobs` | JWT/API Key | List all jobs for authenticated user |
| GET | `/jobs/{job_id}` | JWT/API Key | Get job details |
| DELETE | `/jobs/{job_id}` | JWT/API Key | Delete job and all related data |
| POST | `/jobs/{job_id}/start` | JWT/API Key | Enqueue job for pipeline processing |

**POST /jobs — Request Body (multipart/form-data):**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| version_a | File | Yes | First PDF document (max 50 MB) |
| version_b | File | Yes | Second PDF document (max 50 MB) |
| model_provider | string | No | AI provider: "google", "anthropic", "openrouter", "qwen_local" |
| model_name | string | No | Model name (e.g., "gemini-2.5-flash") |
| label_a | string | No | Label for Version A (default: "Version A") |
| label_b | string | No | Label for Version B (default: "Version B") |
| auto_confirm_threshold | float | No | Auto-confirm threshold 0.5-1.0 (default: 0.95) |

### Documents

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/jobs/{job_id}/documents/{role}/pages/{page_num}/image` | JWT/API Key | Get rendered page PNG |
| GET | `/jobs/{job_id}/documents/{role}/pages/{page_num}/content` | JWT/API Key | Get extracted page content (JSON) |

### Differences

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/jobs/{job_id}/differences` | JWT/API Key | List differences with filters |
| GET | `/jobs/{job_id}/differences/{diff_id}` | JWT/API Key | Get single difference |
| PATCH | `/jobs/{job_id}/differences/{diff_id}` | JWT/API Key | Verify/dismiss/correct/flag |
| PATCH | `/jobs/{job_id}/differences/bulk` | JWT/API Key | Bulk verify multiple differences |
| POST | `/jobs/{job_id}/differences` | JWT/API Key | Add manual difference entry |

**GET /jobs/{job_id}/differences — Query Parameters:**

| Param | Type | Description |
|-------|------|-------------|
| limit | int | Page size (default: 50) |
| offset | int | Skip count |
| difference_type | string | Filter by type |
| significance | string | Filter by significance |
| verification_status | string | Filter by verification status |
| needs_verification | bool | Filter flagged items |
| confidence_min | float | Minimum confidence |
| confidence_max | float | Maximum confidence |

**PATCH /jobs/{job_id}/differences/{diff_id} — Request Body:**

```json
{
  "verification_status": "confirmed|dismissed|corrected|flagged",
  "corrected_description": "string (optional, for 'corrected' status)",
  "verifier_comment": "string (optional, for 'flagged' status)"
}
```

### Reports

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | `/jobs/{job_id}/report` | JWT/API Key | Generate HTML report |
| GET | `/jobs/{job_id}/report` | JWT/API Key | Get report metadata |
| GET | `/jobs/{job_id}/report/pdf` | JWT/API Key | Download PDF report |

### Progress (SSE)

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/jobs/{job_id}/progress?token={jwt}` | JWT (query param) | Server-Sent Events stream |

### API Keys

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | `/api-keys` | JWT | Create new API key |
| GET | `/api-keys` | JWT | List API keys |
| DELETE | `/api-keys/{key_id}` | JWT | Revoke API key |

---

## 9. Authentication & Authorization

### Dual Authentication Strategy

The service supports two authentication methods via FastAPI dependency injection:

**Method 1: JWT Bearer Token**
```
Authorization: Bearer <jwt_token>
```
- Algorithm: HS256
- Shared `JWT_SECRET` with the ERP backend
- Expected claims: userId, email, tenantId (optional), companyId (optional), employeeId, roleId
- Token issued by the Node.js ERP backend during login

**Method 2: API Key**
```
X-API-Key: dd_<base64_urlsafe_32_random_bytes>
```
- Key format: `dd_` prefix + 32 random bytes base64-encoded
- Stored as SHA-256 hash in the `api_keys` table
- Tracks `last_used_at` timestamp
- Can be revoked by setting `is_active = false`

### Auth Context

All authenticated requests populate an `AuthContext` dataclass:

```python
@dataclass
class AuthContext:
    user_id: str
    company_id: str | None
    tenant_id: str | None
    api_key_id: str | None
```

### Permission Integration with ERP

The permission check happens at the **frontend level**, not in the DocDiff service:

1. ERP backend defines `docdiff` as a permission module with actions: `read, create, update, delete, export, configure`
2. Navigation manifest includes DocDiff with `requiredPerm: 'docdiff:read'`
3. Frontend route guard: `<RequirePermission permission="docdiff:read">`
4. Company Admin role automatically gets `docdiff:*` during tenant onboarding
5. DocDiff service trusts the JWT token — if the user has a valid token, they can access the service

### SSE Authentication

Since EventSource doesn't support custom headers, the JWT is passed as a query parameter:
```
GET /jobs/{job_id}/progress?token=<jwt_token>
```

---

## 10. Frontend Implementation (web-system-app)

### Directory Structure

```
web-system-app/src/features/docdiff/
├── DocDiffScreen.tsx              # Main screen (view state machine)
├── index.ts                       # Exports
├── api/
│   ├── docdiff-client.ts          # Separate axios instance for FastAPI
│   ├── docdiff-api.ts             # API endpoint wrappers
│   ├── use-docdiff-queries.ts     # React Query fetch hooks
│   └── use-docdiff-mutations.ts   # React Query mutation hooks
├── components/
│   ├── UploadView.tsx             # File upload + model selection
│   ├── ProcessingView.tsx         # SSE-based progress tracking
│   ├── DifferenceViewer.tsx       # Main comparison UI (4-panel layout)
│   ├── DocumentViewer.tsx         # Page image viewer with bbox overlays
│   ├── DifferenceList.tsx         # Sidebar with filters
│   ├── DifferenceDetail.tsx       # Bottom panel verification actions
│   ├── ComparisonHistory.tsx      # Job history table
│   ├── ReportView.tsx             # Generated report display
│   ├── HandwritingReview.tsx      # Annotation OCR review
│   ├── UnresolvedRegion.tsx       # Manual difference marking
│   ├── ModelSelector.tsx          # AI model dropdown
│   └── KeyboardShortcutsHelp.tsx  # Help modal
├── hooks/
│   ├── useDifferenceNavigation.ts # Keyboard shortcuts + navigation
│   ├── useProcessingSSE.ts        # EventSource for real-time progress
│   └── useSyncScroll.ts           # Dual-panel scroll synchronization
├── types/
│   └── docdiff.types.ts           # All TypeScript interfaces
└── utils/
    ├── significance-colors.ts     # Color mapping by severity
    └── difference-filters.ts      # Filter utilities
```

**Total: 24 files, ~3,000 lines of TypeScript/React code**

### Routing & Access Control

```tsx
// App.tsx, line 559
<Route path="docdiff" element={
  <RequirePermission permission="docdiff:read">
    <DocDiffScreen />
  </RequirePermission>
} />
```

### View State Machine (DocDiffScreen.tsx)

```
                        +----------+
                   +--->| history  |<---+
                   |    +----+-----+    |
                   |         |          |
                   |    +----v-----+    |
                   |    |  upload  |    |
                   |    +----+-----+    |
                   |         |          |
                   |    +----v-------+  |
                   +----| processing |--+
                   |    +----+-------+  |
                   |         |          |
                   |    +----v---------+|
                   +----| verification |+
                   |    +----+---------+|
                   |         |          |
                   |    +----v-----+    |
                   +----| report   |----+
                        +----------+
```

Five views managed by `useState<View>`:
- **history**: ComparisonHistory — table of past/current jobs
- **upload**: UploadView — file selection, model config, start comparison
- **processing**: ProcessingView — real-time SSE stage progress
- **verification**: DifferenceViewer — 4-panel comparison + review interface
- **report**: ReportView — generated HTML/PDF report

### API Client (docdiff-client.ts)

```typescript
const docdiffClient = axios.create({
  baseURL: import.meta.env.VITE_DOCDIFF_API_URL || "http://localhost:8000/api/v1",
  timeout: 120_000,
  headers: { Accept: "application/json" }
});
```

**Request interceptor:** Adds `Authorization: Bearer <token>` from `localStorage.auth_tokens.accessToken`
**Response interceptor:** Extracts `.data` field, maps errors to custom Error objects

### React Query Setup

**Query Keys:**
```typescript
docdiffKeys = {
  all: ["docdiff"],
  jobs: (params?) => [...all, "jobs", ...params],
  job: (id) => [...all, "job", id],
  differences: (jobId, filters?) => [...all, "differences", jobId, ...filters],
  difference: (jobId, diffId) => [...all, "difference", jobId, diffId],
  report: (jobId) => [...all, "report", jobId]
}
```

**Query Hooks:**

| Hook | Auto-Refetch |
|------|--------------|
| `useJobs()` | Manual only |
| `useJob(id)` | Every 3s while job is processing |
| `useDifferences(jobId, filters)` | Manual only |
| `useDifference(jobId, diffId)` | Manual only |
| `useReport(jobId)` | Manual only |

**Mutation Hooks:**

| Hook | Invalidates |
|------|-------------|
| `useCreateJob()` | `docdiffKeys.jobs()` |
| `useStartJob()` | `docdiffKeys.job(jobId)` |
| `useDeleteJob()` | `docdiffKeys.jobs()` |
| `useVerifyDifference(jobId)` | differences + job queries |
| `useBulkVerify(jobId)` | differences + job queries |
| `useGenerateReport(jobId)` | report query |

### Component Details

#### UploadView
- Dual drag-and-drop zones for Version A and Version B PDFs
- Validation: PDF only, max 50 MB
- ModelSelector dropdown for AI provider/model selection
- Auto-confirm threshold slider (0.50 - 1.00)
- Creates FormData, calls `createJob()` then `startJob()` sequentially

#### ProcessingView
- Uses `useProcessingSSE(jobId)` hook for real-time progress
- Displays 8 stages with status icons: pending/in_progress/completed/failed
- Overall progress bar (0-100%)
- Auto-transitions to verification view when status = `ready_for_review` (800ms delay)
- Shows error message on failure with back button

#### DifferenceViewer (Main Comparison UI)
4-panel layout:

```
+----+--------------------+--------------------+
|    |                    |                    |
| L  |   Document A       |   Document B       |
| I  |   (version_a)      |   (version_b)      |
| S  |                    |                    |
| T  |   Page images      |   Page images      |
|    |   with bbox        |   with bbox        |
|    |   overlays         |   overlays         |
+----+--------------------+--------------------+
|                                              |
|        DifferenceDetail (bottom panel)        |
|        Verification actions + before/after    |
+----------------------------------------------+
```

- Left sidebar (w-64): DifferenceList with filters
- Center-left: DocumentViewer for version_a
- Center-right: DocumentViewer for version_b
- Bottom: DifferenceDetail for selected difference
- Toolbar: cosmetic toggle, sync scroll toggle, keyboard help, generate report button
- Verification progress display: `{verified} / {total}`

#### DocumentViewer
- Fetches page images as blob URLs from API
- Overlays colored bounding boxes for differences on current page
- Bounding boxes use significance-based colors:
  - Material: red (rgba with 0.2 alpha)
  - Substantive: amber
  - Cosmetic: blue
  - Uncertain: purple
- Active difference: 3px border + glow effect
- Page navigation with prev/next buttons

#### DifferenceList
- Filterable by: difference type, significance, verification status
- Each item shows: status icon, #number, significance badge, confidence %, summary, page
- Active item highlighted with indigo background + left border
- Progress bar showing verified percentage
- Status icons: checkmark (confirmed), X (dismissed), pencil (corrected), flag (flagged), circle (pending)

#### DifferenceDetail
- Navigation: prev/next buttons
- Displays: difference number, significance badge, type, confidence, before/after values
- Action buttons: Confirm (green), Dismiss (gray), Correct (blue), Flag (amber)
- Inline editors for correct mode and flag mode
- Keyboard shortcuts: C (confirm), D (dismiss), E (correct), F (flag)

#### ComparisonHistory
- Table with columns: Version A, Version B, Date, Differences, Material count, Status, Actions
- Status badges with color coding per job status
- "Open" button for reviewable jobs
- "Download PDF" for completed jobs
- Refresh and "New Comparison" buttons

#### ReportView
- Summary stats cards (material/substantive/cosmetic/uncertain counts)
- Rendered HTML report via `dangerouslySetInnerHTML` in `.prose` div
- Print button (opens in new window)
- Download PDF button (blob download)
- "Partial Report" badge if not all diffs verified

#### HandwritingReview
- Shows for annotation-type differences with `needs_verification`
- Displays source image from bbox region
- AI transcription (read-only)
- Manual correction textarea
- Confidence display (highlights if < 70%)

### Custom Hooks

#### useDifferenceNavigation

```typescript
interface Result {
  activeDifference: DetectedDifference | null
  activeIndex: number
  goNext: () => void
  goPrevious: () => void
  goToDifference: (diff: DetectedDifference) => void
  goToNextUnverified: () => void
  hasPrevious: boolean
  hasNext: boolean
}
```

Keyboard shortcuts:
- `j` / `ArrowDown`: Next difference
- `k` / `ArrowUp`: Previous difference
- `c`: Confirm current
- `d`: Dismiss current
- `e`: Enter correct mode
- `f`: Flag current
- `Space`: Jump to next unverified

#### useProcessingSSE

Opens EventSource to `/jobs/{jobId}/progress?token={jwt}` and parses JSON messages:
- Returns `{ progress: StageProgress | null, isComplete: boolean }`
- Auto-closes on completion or unmount
- Complete when status in: `ready_for_review`, `failed`, `cancelled`

#### useSyncScroll

Synchronizes scroll position between two panels:
- Uses `requestAnimationFrame` to prevent feedback loops
- `isSyncing` ref flag prevents re-entrancy
- Syncs both `scrollTop` and `scrollLeft`
- Toggle-able via `setSyncEnabled()`

### Utility Functions

**significance-colors.ts:**
```typescript
SIGNIFICANCE_COLORS: Record<Significance, { bg, text, border, label }>
// material:    bg-red-50,    text-red-700,    border-red-300
// substantive: bg-amber-50,  text-amber-700,  border-amber-300
// cosmetic:    bg-blue-50,   text-blue-700,   border-blue-300
// uncertain:   bg-purple-50, text-purple-700,  border-purple-300

SIGNIFICANCE_OVERLAY_COLORS: Record<Significance, string>
// rgba strings with 0.2 alpha for document viewer bbox overlays
```

**difference-filters.ts:**
- `filtersToParams()`: Converts camelCase filters to snake_case API query params
- `formatDifferenceType()`: "text_addition" -> "Text Addition"

---

## 11. ERP Backend Integration

### Permission Module

In `avy-erp-backend/src/shared/constants/permissions.ts`:

```typescript
// Module definition
docdiff: {
  label: "Document Comparison",
  actions: ['read', 'create', 'update', 'delete', 'export', 'configure']
}

// System module (NOT suppressed by subscription checks)
SYSTEM_PERMISSION_MODULES includes 'docdiff'

// Module mapping
MODULE_TO_PERMISSION_MAP: { 'docdiff': ['docdiff'] }
```

### Navigation Manifest

In `avy-erp-backend/src/shared/constants/navigation-manifest.ts`:

```typescript
{
  id: 'docdiff',
  label: 'DocDiff Pro',
  icon: 'file-diff',
  path: '/app/docdiff',
  requiredPerm: 'docdiff:read',
  group: 'Document Comparison',
  scope: 'company',
  sortOrder: 780
}
```

### RBAC Integration

- **Company Admin** role gets `docdiff:*` by default during tenant onboarding (`tenant.service.ts`)
- `rbac.service.ts` maintains `docdiff:*` in `COMPANY_ADMIN_PERMISSIONS` constant
- `syncCompanyAdminPermissions()` ensures Company Admin always has DocDiff access

### What the Backend Does NOT Do

- **No proxy routes**: The backend does NOT proxy DocDiff requests through `/api/docdiff`
- **No Prisma models**: DocDiff has its own database schema managed by Alembic
- **No service layer**: No Node.js service files for DocDiff
- **No environment variables**: No `DOCDIFF_SERVICE_URL` in the backend config

The ERP backend's role is limited to:
1. Issuing JWT tokens that DocDiff validates
2. Defining permissions and navigation for the DocDiff feature
3. Hosting the frontend that includes the DocDiff React module

---

## 12. Real-Time Communication (SSE)

### Server-Sent Events (Not WebSocket)

DocDiff uses SSE (Server-Sent Events) for real-time pipeline progress, not WebSocket/Socket.io. This was chosen because:

1. Unidirectional: progress flows server -> client only
2. Native FastAPI support via `StreamingResponse`
3. No Socket.io bridge needed
4. Simpler infrastructure (no WebSocket upgrade)
5. Automatic reconnection built into EventSource API

### SSE Endpoint

```
GET /api/v1/jobs/{job_id}/progress?token={jwt_token}
```

**Authentication:** JWT passed as query parameter (EventSource doesn't support custom headers)

### SSE Message Format

```json
{
  "job_id": "uuid",
  "status": "parsing_version_a",
  "current_stage": 3,
  "stages": {
    "stage_1": { "status": "completed", "name": "Ingestion" },
    "stage_2": { "status": "completed", "name": "Page Classification" },
    "stage_3": { "status": "in_progress", "name": "Content Extraction" },
    "stage_4": { "status": "pending", "name": "Normalization" },
    "stage_5": { "status": "pending", "name": "Section Alignment" },
    "stage_6": { "status": "pending", "name": "Computing Diffs" },
    "stage_7": { "status": "pending", "name": "Classifying Diffs" },
    "stage_8": { "status": "pending", "name": "Assembling" }
  },
  "error": null
}
```

### Frontend SSE Hook

```typescript
function useProcessingSSE(jobId: string | null) {
  // Opens EventSource connection
  // Parses JSON messages
  // Returns { progress, isComplete }
  // Auto-closes on completion/unmount
  // isComplete when status in ["ready_for_review", "failed", "cancelled"]
}
```

### Polling Fallback

In addition to SSE, `useJob(jobId)` auto-refetches every 3 seconds while the job is in a processing status. This provides a fallback in case the SSE connection drops.

---

## 13. File Storage & PDF Processing

### Storage Structure

```
docdiff-service/storage/
├── uploads/
│   └── {job_id}/
│       ├── version_a.pdf              # Uploaded original
│       ├── version_b.pdf              # Uploaded revised
│       ├── version_a_pages/
│       │   ├── page_001.png           # Rendered at adaptive DPI
│       │   ├── page_002.png
│       │   └── ...
│       └── version_b_pages/
│           ├── page_001.png
│           ├── page_002.png
│           └── ...
└── reports/
    └── report_{job_id}.pdf            # Generated comparison report
```

**Docker volume mount:** `./storage:/app/storage` for persistence across container restarts

### PDF Processing Pipeline

#### PyMuPDF Fast Parser (born-digital)

File: `app/pdf/fast_parser.py`

- Extracts text directly from PDF text layer (no OCR)
- Speed: < 50ms per page
- Heading detection via font size:
  - H1: font size >= 15pt
  - H2: font size >= 12pt AND bold
- Header/footer zone detection:
  - Header: Y < 8% of page height
  - Footer: Y > 95% of page height
- Table extraction via PyMuPDF's `find_tables()` method
- All bounding boxes normalized to 0-1 fractions of page dimensions

#### Docling Parser (complex layouts)

File: `app/pdf/parser.py`

- Uses Docling library for advanced layout analysis
- Handles: multi-column layouts, nested tables, complex structures
- Slower than PyMuPDF but more accurate for complex documents
- Table extraction via pandas DataFrame
- Bounding boxes normalized using page dimensions

#### PDF Metadata

File: `app/pdf/metadata.py`

Validates:
- Not encrypted
- Page count within limits
- File size within limits

Extracts:
- Title, author, creator, producer
- Creation date, modification date
- PDF version

#### Page Renderer

File: `app/pdf/renderer.py`

- Uses PyMuPDF's `get_pixmap()` for PNG rendering
- Adaptive DPI:
  - Born-digital: 150 DPI (text extracted from text layer, image just for UI)
  - Scanned: 300 DPI (higher resolution needed for accurate VLM OCR)
- Output: `storage/uploads/{job_id}/{role}_pages/page_XXX.png`

#### Report Generator

File: `app/pdf/report_generator.py`

- `generate_report_html()`: Assembles HTML from job data, differences, documents
- `html_to_pdf()`: Converts HTML to PDF via WeasyPrint (requires Cairo/Pango libs)
- Report cached in `DiffReport` record (HTML + PDF path)
- PDF stored at `storage/reports/report_{job_id}.pdf`

---

## 14. Accuracy Engineering

### Design Philosophy

DocDiff Pro is engineered for accuracy through multiple layers of noise reduction and intelligent classification, not just raw AI power.

### Accuracy Techniques by Stage

| Stage | Technique | Impact |
|-------|-----------|--------|
| 1 | Adaptive DPI rendering | Scanned pages get 300 DPI for better OCR |
| 2 | Text density classification | Detects OCR'd mixed pages correctly |
| 3 | Two-pass merge (PyMuPDF + VLM) | Text fidelity + structural accuracy |
| 4 | Normalized block IDs | Stable references for downstream stages |
| 5 | Semantic page alignment | Handles appendices without false deletes |
| 6 | Adjacent diff merging | "18%"->"21%" = one change, not fragments |
| 6.5 | Visual comparison | Catches diffs OCR misses on scanned pages |
| 7 | Rule engine (90% coverage) | 80-90% AI classification cost savings |
| 7 | Corrections library | Continuous learning from reviewer feedback |
| 8 | 4-pass deduplication | 97% noise reduction |

### Continuous Learning

The corrections library creates a feedback loop:
1. AI classifies a difference as "cosmetic"
2. Reviewer corrects it to "material"
3. Correction stored in `reviewer_corrections` table
4. Next time a similar difference appears, the correction is injected as a few-shot example
5. AI learns from past mistakes without retraining

### Best Practices for Accurate Results

1. Use Pro models (Claude Sonnet or Gemini Pro) for production comparisons
2. Match document scope — include/exclude appendices consistently in both versions
3. Prefer born-digital PDFs — direct text extraction is always more accurate than OCR
4. Review auto-confirmed items — high-confidence is usually correct but can be overridden
5. Use "Correct" (not just "Confirm") when AI misclassifies — teaches the system
6. Regenerate reports after all verifications for accurate final output
7. Reprocess after pipeline updates — old jobs use old extraction logic

---

## 15. Deployment & Infrastructure

### Docker Compose Services

```yaml
docdiff-api:
  build: .
  ports: ["8000:8000"]
  env_file: .env
  volumes: ["./storage:/app/storage"]
  depends_on: [docdiff-redis]
  restart: unless-stopped

docdiff-worker:
  build: .
  command: python -m arq app.workers.job_worker.WorkerSettings
  env_file: .env
  volumes: ["./storage:/app/storage"]
  depends_on: [docdiff-redis]
  restart: unless-stopped

docdiff-redis:
  image: redis:7-alpine
  ports: ["6380:6379"]
  restart: unless-stopped
```

### Dockerfile (Multi-Stage)

```dockerfile
# Stage 1: Builder
FROM python:3.11-slim AS builder
# Installs build-essential for compiling native dependencies
# Installs requirements.txt

# Stage 2: Runtime
FROM python:3.11-slim
# Installs runtime graphics libraries:
#   libcairo2, libpango-1.0-0, libgdk-pixbuf-2.0-0
#   (Required by WeasyPrint for PDF report generation)
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Shared Infrastructure

| Resource | ERP Backend | DocDiff Service |
|----------|------------|-----------------|
| PostgreSQL | Default schema | `docdiff` schema |
| Redis | DB 0 (cache), DB 1 (queue) | DB 2 (ARQ queue) |
| JWT Secret | Issues tokens | Validates tokens |
| PgBouncer | Port 6432 | Shared via same DB URL |

### Database Setup

```bash
# Run migrations
cd docdiff-service
alembic upgrade head

# Or via Docker
docker-compose exec docdiff-api alembic upgrade head
```

### Development Setup

```bash
# 1. Clone and navigate
cd docdiff-service

# 2. Create virtual environment
python -m venv venv
source venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure environment
cp .env.example .env
# Edit .env with your credentials

# 5. Run migrations
alembic upgrade head

# 6. Start API server
uvicorn app.main:app --reload --port 8000

# 7. Start worker (separate terminal)
python -m arq app.workers.job_worker.WorkerSettings

# 8. Configure frontend
# In web-system-app/.env:
# VITE_DOCDIFF_API_URL=http://localhost:8000/api/v1
```

---

## 16. Configuration Reference

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `DOCDIFF_HOST` | `0.0.0.0` | API server host |
| `DOCDIFF_PORT` | `8000` | API server port |
| `DOCDIFF_ENV` | `development` | Environment name |
| `DOCDIFF_LOG_LEVEL` | `INFO` | Logging level |
| `DOCDIFF_CORS_ORIGINS` | `http://localhost:5173,http://localhost:3000` | Allowed CORS origins |
| `DOCDIFF_DATABASE_URL` | `postgresql+asyncpg://...` | PostgreSQL connection |
| `DOCDIFF_DATABASE_SCHEMA` | `docdiff` | Database schema name |
| `DOCDIFF_REDIS_URL` | `redis://localhost:6379/2` | Redis connection (DB 2) |
| `JWT_SECRET` | (required) | Shared with ERP backend |
| `DOCDIFF_STORAGE_PATH` | `./storage` | Local file storage path |
| `ANTHROPIC_API_KEY` | (optional) | Anthropic Claude API key |
| `GOOGLE_API_KEY` | (optional) | Google Gemini API key |
| `OPENROUTER_API_KEY` | (optional) | OpenRouter API key |
| `QWEN_LOCAL_ENDPOINT` | `http://localhost:8080/v1` | Local Qwen3-VL endpoint |
| `DOCDIFF_DEFAULT_PROVIDER` | `google` | Default AI provider |
| `DOCDIFF_DEFAULT_MODEL` | `gemini-2.5-flash` | Default model name |
| `DOCDIFF_CONFIDENCE_THRESHOLD` | `0.75` | Below this -> needs_verification |
| `DOCDIFF_AUTO_CONFIRM_THRESHOLD` | `0.95` | Above this -> auto_confirmed |
| `DOCDIFF_PAGE_RENDER_DPI` | `250` | Default DPI (overridden by adaptive) |
| `DOCDIFF_MAX_PAGES` | `50` | Max pages per document |
| `DOCDIFF_MAX_FILE_SIZE_MB` | `50` | Max file size in MB |
| `DOCDIFF_MAX_RETRIES` | `3` | AI call retry count |
| `DOCDIFF_RETRY_BACKOFF_BASE` | `1` | Retry backoff base (seconds) |

### Frontend Environment

| Variable | Default | Description |
|----------|---------|-------------|
| `VITE_DOCDIFF_API_URL` | `http://localhost:8000/api/v1` | DocDiff service URL |

### Pipeline Thresholds (Hardcoded)

| Threshold | Value | Stage | Purpose |
|-----------|-------|-------|---------|
| Page alignment | 0.3 | 5 | Minimum page content similarity |
| Section title match | 0.7 | 5 | Heading alignment threshold |
| Table match | 0.5 | 5 | Table structural similarity |
| Text match | 0.4 | 5 | Text block content similarity |
| AI escalation | 0.72 | 7 | Rule engine -> AI handoff |
| Header/footer collapse | 3+ pages | 8 | Min pages for dedup collapse |
| Header zone | top 8% | fast_parser | Y < 0.08 = header |
| Footer zone | bottom 5% | fast_parser | Y > 0.95 = footer |
| Adaptive DPI (digital) | 150 | renderer | Born-digital rendering |
| Adaptive DPI (scanned) | 300 | renderer | Scanned page rendering |

---

## 17. User Workflow & UX

### End-to-End Flow

```
1. LOGIN
   User logs into Avy ERP web app -> receives JWT token

2. NAVIGATION
   Sidebar shows "DocDiff Pro" under "Document Comparison" group
   (Requires docdiff:read permission, auto-granted to Company Admin)

3. HISTORY VIEW (default)
   Table of past comparison jobs with status badges
   Options: Open (review), Download PDF (completed), Delete

4. UPLOAD
   Click "New Comparison"
   - Drag-drop Version A PDF (max 50 MB)
   - Drag-drop Version B PDF (max 50 MB)
   - Select AI model (default: Gemini 2.5 Flash)
   - Adjust auto-confirm threshold (default: 0.95)
   - Click "Compare Documents"

5. PROCESSING (real-time)
   8-stage progress display with SSE updates:
   [===========|         ] 62%
   Stage 1: Ingestion        [DONE]
   Stage 2: Classification   [DONE]
   Stage 3: Extraction        [DONE]
   Stage 4: Normalization     [DONE]
   Stage 5: Alignment         [IN PROGRESS]
   Stage 6: Diff Computation  [PENDING]
   Stage 7: Scoring           [PENDING]
   Stage 8: Assembly          [PENDING]

   Auto-transitions to verification when complete (~30-90s)

6. VERIFICATION (main workflow)
   4-panel comparison interface:

   +--------+--------------------+--------------------+
   |        |                    |                    |
   | DIFFS  |   Version A        |   Version B        |
   | LIST   |   (page image)     |   (page image)     |
   |        |                    |                    |
   | #1 Mat |   [red box]        |   [red box]        |
   | #2 Sub |                    |                    |
   | #3 Cos |   [blue box]       |   [blue box]       |
   | #4 Mat |                    |                    |
   |        |                    |                    |
   +--------+--------------------+--------------------+
   |                                                  |
   |  #1 Material | text_modification | 92% confidence |
   |  Before: "tolerance: 0.05mm"                     |
   |  After:  "tolerance: 0.08mm"                     |
   |                                                  |
   |  [Confirm] [Dismiss] [Correct] [Flag]            |
   +--------------------------------------------------+

   Keyboard shortcuts for power users:
   - J/Down: Next difference
   - K/Up: Previous difference
   - C: Confirm
   - D: Dismiss
   - E: Edit/Correct
   - F: Flag for review
   - Space: Jump to next unverified
   - ?: Show keyboard help

   Features:
   - Filter by type, significance, verification status
   - Toggle cosmetic differences visibility
   - Synchronized scroll between Version A/B panels
   - Colored bbox overlays on page images
   - Progress bar: "23 / 56 verified"

7. REPORT GENERATION
   Click "Generate Diff Report"
   - Summary statistics cards (material/substantive/cosmetic counts)
   - Full HTML report with all differences
   - Print button (opens in new window)
   - Download as PDF
   - "Partial Report" badge if not all differences verified

8. COMPLETION
   Return to history, start new comparison, or re-review
```

### Significance Color Coding

| Level | Color | Meaning | Examples |
|-------|-------|---------|---------|
| **Material** | Red | Changes that affect function, safety, cost, or compliance | Tolerances, material grades, quantities, pricing, legal terms |
| **Substantive** | Amber | Changes that alter meaning or scope | Scope descriptions, requirement rewording, procedures, dates |
| **Cosmetic** | Blue | Changes that don't affect meaning | Formatting, whitespace, version IDs, page numbers |
| **Uncertain** | Purple | AI could not confidently classify | Requires human judgment |

### Verification Actions

| Action | Effect | When to Use |
|--------|--------|-------------|
| **Confirm** | Accepts difference as correctly classified | AI classification is correct |
| **Dismiss** | Marks as not a real difference (false positive) | OCR noise, duplicate, irrelevant |
| **Correct** | Changes the classification + adds description | AI got the significance wrong |
| **Flag** | Marks for further review with comment | Needs domain expert opinion |

---

## 18. Roadmap & Evolution

### Architecture Evolution

```
Current (Prototype): LLM-Heavy
  Cost: $0.50-2.00/job | Speed: 30-90s | Accuracy: 90-95%
  All extraction -> LLM (expensive, slow, accurate)
  Classification -> Rule engine (90%) + LLM (10%)

Phase 2 Target: Hybrid
  Cost: $0.05-0.30/job | Speed: 10-30s | Accuracy: 93-97%
  Born-digital -> PyMuPDF (free, instant)
  Scanned OCR -> PaddleOCR (free, local)
  Tables -> TableTransformer (free, local)
  Classification -> Rule engine (90%) + LLM (10%)

Phase 4 Target: ML-First
  Cost: $0.00-0.05/job | Speed: 5-15s | Accuracy: 95-98%
  All extraction -> Local ML models (LayoutLMv3, PaddleOCR)
  Classification -> Fine-tuned Qwen3-VL (local, free)
  LLM -> Edge cases only (< 5% of calls)
```

### Planned Improvements

**Phase 1 (Immediate):**
- Corrections-aware classification prompts (inject few-shot from reviewer history)
- Pre-comparison scope confirmation dialog (different page counts)
- Bulk action toolbar (confirm all cosmetic, dismiss all pending)

**Phase 2 (Short Term):**
- PaddleOCR for local text extraction (70% cost reduction on scanned PDFs)
- TableTransformer for ML-based table detection
- Fuzzy row matching with Hungarian algorithm
- Domain-specific classification rule sets

**Phase 3 (Medium Term):**
- LoRA fine-tuning of Qwen3-VL on reviewer corrections (zero API cost)
- Semantic similarity for synonym detection
- Second-reviewer mode for Material dismissals
- Reviewer note validation

**Phase 4 (Long Term):**
- LayoutLMv3 for complex layout analysis
- Historical comparison search with pgvector
- Automated accuracy benchmarking test suite

---

## Appendix A: Model Selection Guide

| Model | Provider | Speed | Accuracy | Cost | Best For |
|-------|----------|-------|----------|------|----------|
| gemini-2.5-flash | Google | Fast | Good | Low | Daily comparisons, high volume |
| gemini-2.5-pro | Google | Medium | Very Good | Medium | Important documents |
| claude-3-7-sonnet | Anthropic | Medium | Excellent | High | Critical comparisons |
| claude-3-opus | Anthropic | Slow | Excellent | Very High | Maximum accuracy |
| gemma-4-31b-it:free | OpenRouter | Medium | Good | Free | Budget-conscious usage |
| qwen3-vl-8b | Local | Medium | Moderate | Free | Privacy-sensitive, offline |
| qwen3-vl-30b-a3b | Local | Slow | Good | Free | Best local accuracy |

## Appendix B: API Response Envelope

All API responses follow a consistent envelope format:

```json
// Success
{
  "success": true,
  "data": { ... },
  "message": "Operation completed"
}

// Error
{
  "success": false,
  "error": "Error description",
  "detail": "Detailed error message"
}

// Paginated
{
  "success": true,
  "data": [ ... ],
  "meta": {
    "total": 56,
    "page": 1,
    "limit": 20,
    "total_pages": 3
  }
}
```

## Appendix C: Bounding Box Format

All bounding boxes are normalized to 0-1 fractions of page dimensions:

```json
{
  "x": 0.12,      // Left edge (0 = left, 1 = right)
  "y": 0.35,      // Top edge (0 = top, 1 = bottom)
  "width": 0.76,  // Width as fraction of page width
  "height": 0.04  // Height as fraction of page height
}
```

The `BBox` utility class provides: `intersects()`, `intersection_area()`, `iou()` (Intersection over Union), `contains()`.

## Appendix D: Block Content Format

Each extracted block follows this JSON structure:

```json
{
  "id": "version_a_001_blk_0003",
  "type": "text",
  "bbox": { "x": 0.1, "y": 0.3, "width": 0.8, "height": 0.05 },
  "text": "The maximum tolerance shall be 0.05mm.",
  "confidence": 0.95,
  "section_level": 2,
  "section_title": "3.1 Dimensional Requirements",
  "is_header": false,
  "is_footer": false
}
```

**Table block:**
```json
{
  "id": "version_a_002_blk_0008",
  "type": "table",
  "bbox": { "x": 0.1, "y": 0.4, "width": 0.8, "height": 0.2 },
  "rows": 5,
  "cols": 3,
  "headers": ["Part", "Material", "Quantity"],
  "cells": [
    { "row": 0, "col": 0, "text": "Bracket", "rowspan": 1, "colspan": 1 },
    { "row": 0, "col": 1, "text": "SS316L", "rowspan": 1, "colspan": 1 }
  ],
  "confidence": 0.88
}
```

**Annotation block:**
```json
{
  "id": "version_b_003_blk_0012",
  "type": "annotation",
  "bbox": { "x": 0.6, "y": 0.2, "width": 0.3, "height": 0.08 },
  "annotation_type": "handwriting",
  "transcription": "Please update this section",
  "confidence": 0.72
}
```

---

*Document generated: April 2026*
*DocDiff Pro v2.0 — Avy ERP Platform*
