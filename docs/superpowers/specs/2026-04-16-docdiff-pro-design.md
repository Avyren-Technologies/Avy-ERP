# DocDiff Pro — Technical Design Specification

**Date:** 2026-04-16
**Status:** Approved for implementation
**PRD Reference:** `docs/DocDiff-Pro-PRD-Prototype-v0.1.md`

---

## 1. Overview

DocDiff Pro is an AI-powered document comparison system that compares two PDF document versions and produces a structured, navigable diff report. It runs as an independent Python microservice alongside the existing Node.js ERP backend, with a React frontend module embedded in the ERP web app.

**Prototype scope:** 10-page documents, 4 AI providers (Anthropic, Google, OpenRouter, self-hosted Qwen3-VL), human review workflow, PDF report export.

---

## 2. Architecture

```
┌─────────────────────────────────────────────────────┐
│  Web Browser (ERP Frontend)                         │
│  ┌───────────────────────────────────────────────┐  │
│  │  DocDiff Pro React Module                     │  │
│  │  (Upload, Processing, Review, Report)         │  │
│  └──────────────┬──────────────┬─────────────────┘  │
│                 │ REST         │ SSE                 │
└─────────────────┼──────────────┼────────────────────┘
                  │              │
         ┌────────▼──────────────▼────────┐
         │       FastAPI Service          │
         │       (docdiff-service)        │
         │       Port 8000                │
         │                                │
         │  • REST API (jobs, changes,    │
         │    reports, documents)         │
         │  • SSE endpoint (progress)    │
         │  • Auth (JWT + API key)       │
         │  • Pipeline orchestration     │
         │  • AI model routing           │
         └──┬─────┬────┬─────────────────┘
            │     │    │
       ┌────▼─┐ ┌▼────▼───┐  ┌──────────────┐
       │ PgSQL│ │  Redis   │  │  AI Providers │
       │docdif│ │ (shared) │  │  • Anthropic  │
       │schema│ │ • Queue  │  │  • Google     │
       │      │ │ • Cache  │  │  • OpenRouter │
       └──────┘ └──────────┘  │  • Qwen3 VL  │
                              └──────────────┘
```

### Key architectural decisions

| Decision | Rationale |
|---|---|
| **SSE for real-time updates** (not Socket.IO bridge) | FastAPI supports SSE natively via `StreamingResponse`. Eliminates the 3-hop path (FastAPI → Redis pub/sub → Node.js → Socket.IO → browser). Single hop, zero extra infrastructure. Socket.IO bridge can be added later for deep ERP integration. |
| **Docling for structural parsing** (not PyMuPDF alone) | PyMuPDF extracts raw text but cannot reliably parse table structures (merged cells, spanning headers), reading order in multi-column layouts, or section hierarchy. Docling produces typed Pydantic output, handles tables at 95%+ accuracy, runs on CPU, MIT licensed. PyMuPDF retained for metadata extraction, page counting, and rendering pages to images. |
| **diff-match-patch for text diffs** (not difflib) | Google's library handles fuzzy matching, semantic cleanup, and produces cleaner word-level diffs. difflib's SequenceMatcher produces noisy output on real documents and can't handle moved paragraphs. |
| **JSON columns for parsed content** (not normalized content_blocks table) | A 10-page document with 50 tables could generate thousands of rows in a normalized table. For the prototype, storing full parsed structure as JSON on `document_pages` is faster to write, query, and develop against. `detected_changes` and `review_actions` remain relational. |
| **Dual auth (JWT + API key)** | ERP-embedded users authenticate via existing JWT. Public/standalone access uses API keys stored in the database. |
| **Separate axios client for FastAPI** | Frontend talks to FastAPI directly on port 8000, not proxied through Node.js. Avoids coupling the two backends. |

---

## 3. Project Structure

```
docdiff-service/                        # Top-level directory in monorepo
├── Dockerfile                          # Multi-stage Python build
├── docker-compose.yml                  # Dev: service + deps
├── pyproject.toml                      # Project metadata + deps (uv/pip)
├── requirements.txt                    # Pinned production deps
├── requirements-dev.txt                # Test/lint deps
├── .env.example                        # All env vars documented
├── alembic.ini                         # Alembic config
├── alembic/                            # DB migrations
│   ├── env.py
│   └── versions/
├── app/
│   ├── __init__.py
│   ├── main.py                         # FastAPI app, CORS, lifespan, routers
│   ├── config.py                       # Pydantic BaseSettings
│   ├── database.py                     # SQLAlchemy async engine + session
│   │
│   ├── models/                         # SQLAlchemy ORM models
│   │   ├── __init__.py
│   │   ├── job.py                      # ComparisonJob
│   │   ├── document.py                 # Document, DocumentPage
│   │   ├── change.py                   # DetectedChange, ReviewAction
│   │   ├── report.py                   # DiffReport
│   │   └── api_key.py                  # APIKey (public access)
│   │
│   ├── schemas/                        # Pydantic request/response schemas
│   │   ├── __init__.py
│   │   ├── job.py
│   │   ├── document.py
│   │   ├── change.py
│   │   └── report.py
│   │
│   ├── api/                            # Route handlers
│   │   ├── __init__.py
│   │   ├── router.py                   # Main API router aggregator
│   │   ├── health.py                   # GET /health — service + deps status
│   │   ├── jobs.py                     # CRUD for comparison jobs
│   │   ├── documents.py                # Upload + validation
│   │   ├── changes.py                  # Review actions (accept/reject/edit/escalate)
│   │   ├── reports.py                  # Report generation + PDF export
│   │   └── sse.py                      # SSE endpoint for processing progress
│   │
│   ├── auth/                           # Dual auth middleware
│   │   ├── __init__.py
│   │   ├── middleware.py               # FastAPI dependency: JWT or API key
│   │   ├── jwt_validator.py            # Verify ERP JWT tokens
│   │   └── api_key.py                  # API key validation
│   │
│   ├── pipeline/                       # 8-stage document processing pipeline
│   │   ├── __init__.py
│   │   ├── orchestrator.py             # Job orchestration, stage sequencing
│   │   ├── stage_1_ingestion.py        # Upload, validate, metadata (PyMuPDF)
│   │   ├── stage_2_classification.py   # Page type: digital/scanned/mixed/handwritten
│   │   ├── stage_3_extraction.py       # Structural extraction (Docling + VLM fallback)
│   │   ├── stage_4_normalization.py    # Canonical JSON format, ID assignment
│   │   ├── stage_5_alignment.py        # Section/table/paragraph matching
│   │   ├── stage_6_diff.py             # Word-level + cell-level diffs (diff-match-patch)
│   │   ├── stage_7_scoring.py          # Confidence scoring + significance classification
│   │   └── stage_8_assembly.py         # Result compilation, summary generation
│   │
│   ├── ai/                             # AI model abstraction layer
│   │   ├── __init__.py
│   │   ├── base.py                     # Abstract AIProvider with tenacity retry
│   │   ├── anthropic_provider.py       # Claude Sonnet 4.6 / Opus 4.6
│   │   ├── google_provider.py          # Gemini 3.1 Pro / Gemini 3 Flash
│   │   ├── openrouter_provider.py      # Best available VLM via OpenRouter
│   │   ├── qwen_local_provider.py      # Qwen3-VL via OpenAI-compatible endpoint
│   │   ├── router.py                   # Model selection by job config
│   │   └── response_parser.py          # JSON extraction, schema validation, fallback
│   │
│   ├── prompts/                        # Versioned prompt templates
│   │   ├── __init__.py
│   │   ├── extract_page.py             # Page content extraction prompts
│   │   ├── classify_change.py          # Change significance classification prompts
│   │   ├── transcribe_handwriting.py   # Handwriting transcription prompts
│   │   └── templates/                  # Provider-specific variants
│   │       ├── anthropic/              # XML-structured prompts for Claude
│   │       ├── google/                 # JSON schema prompts for Gemini
│   │       ├── openrouter/             # Generic prompts
│   │       └── qwen/                   # Qwen-optimized prompts
│   │
│   ├── pdf/                            # PDF utilities
│   │   ├── __init__.py
│   │   ├── metadata.py                 # PyMuPDF: page count, file size, PDF version
│   │   ├── renderer.py                 # PyMuPDF: page → image at 250 DPI
│   │   ├── parser.py                   # Docling: structural extraction (tables, sections)
│   │   └── report_generator.py         # WeasyPrint: HTML → PDF report export
│   │
│   ├── workers/                        # Background task processing
│   │   ├── __init__.py
│   │   └── job_worker.py               # ARQ worker: Redis queue consumer
│   │
│   └── utils/
│       ├── __init__.py
│       ├── diff_utils.py               # diff-match-patch wrapper, word-level ops
│       ├── table_utils.py              # Table structure comparison (cell-level)
│       └── bbox.py                     # Bounding box intersection, containment
│
├── tests/
│   ├── conftest.py                     # Fixtures: test DB, test client, mock AI
│   ├── test_api/                       # API endpoint tests
│   ├── test_pipeline/                  # Pipeline stage unit tests
│   └── test_ai/                        # AI provider + response parser tests
│
└── storage/                            # Local file storage (prototype)
    ├── uploads/                        # Uploaded PDFs
    └── reports/                        # Generated PDF reports
```

---

## 4. Database Schema

PostgreSQL schema `docdiff`, accessed via SQLAlchemy async ORM. Migrations managed by Alembic.

### 4.1 Tables

#### `comparison_jobs`

| Column | Type | Description |
|---|---|---|
| id | UUID (PK) | Job identifier |
| status | Enum | `uploading`, `parsing_original`, `parsing_revised`, `aligning`, `diffing`, `classifying`, `assembling`, `ready_for_review`, `review_in_progress`, `completed`, `failed` |
| model_provider | String | Selected AI provider (anthropic, google, openrouter, qwen_local) |
| model_name | String | Specific model (claude-sonnet-4-6, gemini-3.1-pro, etc.) |
| current_stage | Integer | Current pipeline stage (1-8) |
| stage_progress | JSON | Per-stage status: `{ "1": "completed", "2": "in_progress", ... }` |
| error_message | Text (nullable) | Error details if status=failed |
| total_changes | Integer (default 0) | Count of detected changes |
| changes_reviewed | Integer (default 0) | Count of reviewed changes |
| processing_time_ms | Integer (nullable) | Total processing duration |
| token_usage | JSON (nullable) | `{ "input": N, "output": N, "cost_estimate": "$X.XX" }` |
| user_id | String (nullable) | ERP user ID (JWT auth) |
| company_id | String (nullable) | ERP company ID (JWT auth) |
| api_key_id | UUID (nullable, FK) | API key used (public auth) |
| created_at | Timestamp | Job creation time |
| updated_at | Timestamp | Last update time |

#### `documents`

| Column | Type | Description |
|---|---|---|
| id | UUID (PK) | Document identifier |
| job_id | UUID (FK → comparison_jobs) | Parent job |
| role | Enum | `original` or `revised` |
| filename | String | Original upload filename |
| file_path | String | Storage path |
| file_size_bytes | Integer | File size |
| page_count | Integer | Number of pages |
| pdf_metadata | JSON | Creation date, PDF version, producer, etc. |
| created_at | Timestamp | Upload time |

#### `document_pages`

| Column | Type | Description |
|---|---|---|
| id | UUID (PK) | Page identifier |
| document_id | UUID (FK → documents) | Parent document |
| page_number | Integer | 1-indexed page number |
| page_type | Enum | `born_digital`, `scanned`, `mixed` |
| has_handwriting | Boolean | Handwriting detected on page |
| has_annotations | Boolean | PDF annotations detected |
| content | JSON | **Full parsed structure for the page.** Contains all content blocks with types, text, bounding boxes, table structures, annotation data. One blob per page. |
| extraction_method | String | `docling`, `vlm`, `hybrid` |
| extraction_confidence | Float | Overall extraction confidence (0.0-1.0) |
| image_path | String (nullable) | Rendered page image path (for VLM input) |
| processing_status | Enum | `pending`, `completed`, `failed` |
| error_message | Text (nullable) | Extraction error if failed |

**`content` JSON structure:**
```json
{
  "blocks": [
    {
      "id": "blk_001",
      "type": "text|table|image|annotation|header|footer",
      "bbox": { "x": 0, "y": 0, "width": 100, "height": 20, "page": 1 },
      "text": "...",
      "table": {
        "rows": 5, "cols": 3,
        "cells": [
          { "row": 0, "col": 0, "rowspan": 1, "colspan": 1, "text": "..." }
        ],
        "headers": ["Col A", "Col B", "Col C"]
      },
      "annotation": {
        "type": "handwriting|sticky_note|highlight|strikethrough|stamp|text_box",
        "transcription": "...",
        "transcription_confidence": 0.72
      },
      "section_level": 2,
      "section_title": "3.1 Material Specifications"
    }
  ],
  "reading_order": ["blk_001", "blk_003", "blk_002"],
  "sections": [
    { "title": "3. Specifications", "level": 1, "block_ids": ["blk_001", "blk_002"] }
  ]
}
```

#### `detected_changes`

| Column | Type | Description |
|---|---|---|
| id | UUID (PK) | Change identifier |
| job_id | UUID (FK → comparison_jobs) | Parent job |
| change_number | Integer | Sequential number within job |
| change_type | Enum | `text_addition`, `text_deletion`, `text_modification`, `table_cell_change`, `table_row_addition`, `table_row_deletion`, `table_structure_change`, `annotation_added`, `annotation_removed`, `section_moved`, `formatting_change` |
| significance | Enum | `material`, `substantive`, `cosmetic`, `uncertain` |
| confidence | Float | 0.0-1.0 |
| page_original | Integer (nullable) | Page number in original document |
| page_revised | Integer (nullable) | Page number in revised document |
| bbox_original | JSON (nullable) | Bounding box in original |
| bbox_revised | JSON (nullable) | Bounding box in revised |
| value_before | Text (nullable) | Content before change |
| value_after | Text (nullable) | Content after change |
| context | Text (nullable) | Surrounding text for context |
| summary | Text | AI-generated brief description |
| block_id_original | String (nullable) | Content block ID in original |
| block_id_revised | String (nullable) | Content block ID in revised |
| review_status | Enum | `pending`, `accepted`, `rejected`, `escalated` (default: `pending`) |
| auto_accepted | Boolean (default false) | True if confidence ≥ threshold and auto-accepted |
| needs_human_review | Boolean (default false) | True if confidence < threshold |
| reviewer_comment | Text (nullable) | Reviewer's note |
| reviewed_at | Timestamp (nullable) | When reviewed |
| created_at | Timestamp | Detection time |

#### `diff_reports`

| Column | Type | Description |
|---|---|---|
| id | UUID (PK) | Report identifier |
| job_id | UUID (FK → comparison_jobs, unique) | Parent job |
| summary_stats | JSON | `{ "total": N, "by_type": {...}, "by_significance": {...}, "auto_accepted": N, "manually_reviewed": N, "rejected": N, "escalated": N }` |
| report_html | Text | Full report HTML |
| report_pdf_path | String (nullable) | Generated PDF file path |
| generated_at | Timestamp | Generation time |

#### `api_keys`

| Column | Type | Description |
|---|---|---|
| id | UUID (PK) | Key identifier |
| key_hash | String (unique) | SHA-256 hash of the API key |
| name | String | Descriptive label |
| is_active | Boolean (default true) | Whether key is valid |
| created_at | Timestamp | Creation time |
| last_used_at | Timestamp (nullable) | Last usage time |

---

## 5. API Endpoints

Base URL: `http://localhost:8000/api/v1`

### 5.1 Health

| Method | Path | Auth | Description |
|---|---|---|---|
| GET | `/health` | None | Service status, DB, Redis, Qwen endpoint reachability |

### 5.2 Jobs

| Method | Path | Auth | Description |
|---|---|---|---|
| POST | `/jobs` | Required | Create comparison job (upload 2 PDFs, select model) |
| GET | `/jobs` | Required | List jobs for current user |
| GET | `/jobs/{id}` | Required | Get job details + status |
| DELETE | `/jobs/{id}` | Required | Cancel/delete a job |

### 5.3 Processing

| Method | Path | Auth | Description |
|---|---|---|---|
| POST | `/jobs/{id}/start` | Required | Start processing pipeline |
| GET | `/jobs/{id}/progress` | Required | **SSE endpoint** — streams stage updates |

### 5.4 Changes

| Method | Path | Auth | Description |
|---|---|---|---|
| GET | `/jobs/{id}/changes` | Required | List all detected changes (filterable) |
| GET | `/jobs/{id}/changes/{change_id}` | Required | Get single change detail |
| PATCH | `/jobs/{id}/changes/{change_id}` | Required | Review action: accept, reject, edit, escalate |
| POST | `/jobs/{id}/changes` | Required | Add manual change (for unresolved regions) |
| PATCH | `/jobs/{id}/changes/bulk` | Required | Bulk accept/reject (e.g., all cosmetic changes) |

**Filter query params for GET changes:**
- `change_type` — filter by type
- `significance` — filter by significance level
- `confidence_min` / `confidence_max` — confidence range
- `review_status` — pending, accepted, rejected, escalated
- `page` — filter by page number
- `needs_human_review` — boolean filter

### 5.5 Documents

| Method | Path | Auth | Description |
|---|---|---|---|
| GET | `/jobs/{id}/documents/{role}/pages/{page_num}/image` | Required | Rendered page image (for viewer) |
| GET | `/jobs/{id}/documents/{role}/pages/{page_num}/content` | Required | Parsed content JSON for a page |

### 5.6 Reports

| Method | Path | Auth | Description |
|---|---|---|---|
| POST | `/jobs/{id}/report` | Required | Generate summary report |
| GET | `/jobs/{id}/report` | Required | Get report (HTML) |
| GET | `/jobs/{id}/report/pdf` | Required | Download report as PDF |

### 5.7 API Keys (admin)

| Method | Path | Auth | Description |
|---|---|---|---|
| POST | `/api-keys` | JWT only | Create new API key |
| GET | `/api-keys` | JWT only | List API keys |
| DELETE | `/api-keys/{id}` | JWT only | Revoke API key |

---

## 6. AI Provider Abstraction

### 6.1 Base interface

```python
class AIProvider(ABC):
    """Abstract base for all AI model providers.
    
    All methods include tenacity retry with:
    - 3 attempts, exponential backoff (1s, 2s, 4s), max 30s wait
    - Retry on: rate limit (429), server error (5xx), timeout
    - No retry on: auth error (401/403), bad request (400)
    """

    @abstractmethod
    async def extract_page_content(self, image: bytes, prompt: str) -> dict: ...

    @abstractmethod
    async def classify_change(self, change_context: str, prompt: str) -> dict: ...

    @abstractmethod
    async def transcribe_handwriting(self, image: bytes, region_bbox: dict, prompt: str) -> dict: ...

    @property
    @abstractmethod
    def provider_name(self) -> str: ...

    @property
    @abstractmethod
    def supports_vision(self) -> bool: ...
```

### 6.2 Providers

| Provider | SDK | Models | Notes |
|---|---|---|---|
| Anthropic | `anthropic` (async) | claude-sonnet-4-6, claude-opus-4-6 | XML-structured prompts, strong reasoning |
| Google | `google-genai` (async) | gemini-3.1-pro, gemini-3-flash | JSON schema prompts, fast table extraction |
| OpenRouter | `httpx` (OpenAI-compatible) | Best available VLM | Generic prompts, model varies |
| Qwen Local | `httpx` (OpenAI-compatible) | qwen3-vl-8b, qwen3-vl-30b-a3b | Local endpoint on Mac Studio |

### 6.3 Response parser (`ai/response_parser.py`)

Handles the gap between raw AI output and internal Pydantic types:

1. **JSON extraction** — strips markdown code fences, finds JSON in mixed text output
2. **Schema validation** — validates against Pydantic models (`PageContent`, `ChangeClassification`, `Transcription`)
3. **Graceful fallback** — on malformed output: retry once with a "fix your JSON" prompt, then mark region as `processing_failed`
4. **Provider normalization** — maps provider-specific response formats to internal types

### 6.4 Prompt management (`prompts/`)

Each task (extract, classify, transcribe) has:
- A base prompt template with `{placeholders}` for dynamic content
- Provider-specific variants in `prompts/templates/{provider}/`
- Version tracking via filename or docstring

Prompts are loaded at startup and cached. Changing a prompt requires no code changes — just edit the template file and restart.

---

## 7. Processing Pipeline

### 7.1 Stage details

| Stage | Name | Input | Output | Tool | Retryable |
|---|---|---|---|---|---|
| 1 | Ingestion | Raw PDF files | Validated files + metadata | PyMuPDF | Yes |
| 2 | Classification | PDF pages | Page type labels (digital/scanned/mixed/handwritten) | PyMuPDF + heuristics | Yes |
| 3 | Extraction | Classified pages | Structured content JSON per page | Docling (digital) + VLM (scanned/handwritten) | Per-page |
| 4 | Normalization | Raw extracted content | Canonical format with IDs and bboxes | Pure Python | Yes |
| 5 | Alignment | Two normalized documents | Matched content block pairs + unmatched blocks | Heading similarity + positional heuristics | Yes |
| 6 | Diff | Aligned block pairs | Raw diff records (word-level text, cell-level table) | diff-match-patch + custom table logic | Yes |
| 7 | Scoring | Raw diff records | Confidence scores + significance classifications | AI provider (for non-obvious cases) | Per-change |
| 8 | Assembly | Scored changes | Structured comparison result, summaries | Pure Python | Yes |

### 7.2 Orchestration

- Jobs are enqueued to ARQ (Redis-backed async task queue)
- ARQ worker picks up jobs and runs stages sequentially
- Each stage updates `comparison_jobs.stage_progress` and `comparison_jobs.current_stage`
- Progress published to an in-memory dict keyed by job ID; SSE endpoint reads from it
- **Partial failure:** If a page fails in Stage 3, mark it as failed, continue with remaining pages. Failed pages surface as "Unresolved Region" in the review interface.
- **Cancellation:** Check `job.status == cancelled` between stages; abort if true.

### 7.3 Page rendering specification

All PDF pages rendered to images at **250 DPI** using PyMuPDF. This balances:
- Text legibility for VLM (72 DPI too blurry, table lines disappear)
- File size (600 DPI produces huge images, slow to process)
- VLM input token cost (larger images = more tokens)

Output format: PNG, stored at `storage/uploads/{job_id}/pages/{doc_role}_page_{N}.png`

---

## 8. Frontend Module

### 8.1 File structure

```
web-system-app/src/
├── features/
│   └── docdiff/
│       ├── api/
│       │   ├── docdiff-client.ts          # Separate axios instance → FastAPI :8000
│       │   ├── docdiff-api.ts             # API function wrappers
│       │   ├── use-docdiff-queries.ts     # Query key factory + hooks
│       │   └── use-docdiff-mutations.ts   # Upload, review, report mutations
│       ├── components/
│       │   ├── UploadView.tsx             # Drag-drop + model selector + validation
│       │   ├── ProcessingView.tsx         # 8-stage vertical progress (SSE-driven)
│       │   ├── ReviewInterface.tsx        # Three-panel layout orchestrator
│       │   ├── DocumentViewer.tsx         # PDF page image with overlay highlights
│       │   ├── ChangeList.tsx             # Scrollable, filterable change list
│       │   ├── ChangeDetail.tsx           # Single change: summary + actions
│       │   ├── ChangeActions.tsx          # Accept/Reject/Edit/Escalate buttons
│       │   ├── HandwritingReview.tsx      # Image + transcription correction
│       │   ├── UnresolvedRegion.tsx       # Side-by-side zoom for unresolved areas
│       │   ├── ReportView.tsx             # Summary report + download
│       │   ├── ModelSelector.tsx          # AI model dropdown with descriptions
│       │   └── KeyboardShortcutsHelp.tsx  # "?" overlay showing shortcuts
│       ├── hooks/
│       │   ├── useProcessingSSE.ts        # EventSource hook for progress updates
│       │   ├── useChangeNavigation.ts     # J/K arrow keys, change focus management
│       │   └── useSyncScroll.ts           # Synchronized scrolling between viewers
│       ├── types/
│       │   └── docdiff.types.ts           # All TypeScript interfaces
│       ├── utils/
│       │   ├── significance-colors.ts     # material=red, substantive=amber, etc.
│       │   └── change-filters.ts          # Filter/sort logic for change list
│       ├── DocDiffScreen.tsx              # Main screen: routes between views
│       └── index.ts                       # Public exports
```

### 8.2 Separate axios client

```typescript
// docdiff-client.ts
const docdiffClient = axios.create({
  baseURL: import.meta.env.VITE_DOCDIFF_API_URL || 'http://localhost:8000/api/v1',
  timeout: 120_000, // 2 min for uploads
});

// Attach JWT from existing auth store
docdiffClient.interceptors.request.use((config) => {
  const tokens = JSON.parse(localStorage.getItem('auth_tokens') || '{}');
  if (tokens.accessToken) {
    config.headers.Authorization = `Bearer ${tokens.accessToken}`;
  }
  return config;
});
```

### 8.3 Query key factory

```typescript
export const docdiffKeys = {
  all: ['docdiff'] as const,
  jobs: (params?: Record<string, unknown>) => [...docdiffKeys.all, 'jobs', ...(params ? [params] : [])],
  job: (id: string) => [...docdiffKeys.all, 'job', id],
  changes: (jobId: string, filters?: Record<string, unknown>) =>
    [...docdiffKeys.all, 'changes', jobId, ...(filters ? [filters] : [])],
  change: (jobId: string, changeId: string) =>
    [...docdiffKeys.all, 'change', jobId, changeId],
  report: (jobId: string) => [...docdiffKeys.all, 'report', jobId],
};
```

### 8.4 SSE integration

```typescript
// useProcessingSSE.ts
function useProcessingSSE(jobId: string) {
  const [stages, setStages] = useState<StageProgress>({});
  
  useEffect(() => {
    const source = new EventSource(
      `${DOCDIFF_API_URL}/jobs/${jobId}/progress`
    );
    source.onmessage = (event) => {
      const data = JSON.parse(event.data);
      setStages(data.stages);
      if (data.status === 'ready_for_review' || data.status === 'failed') {
        source.close();
      }
    };
    return () => source.close();
  }, [jobId]);
  
  return stages;
}
```

### 8.5 Review interface layout

```
┌──────────────────────────────────────────────────────────┐
│  DocDiff Pro — Job #abc123                    [? Help]   │
├────────────┬─────────────────────┬───────────────────────┤
│ Change List│   Original (p.3)    │   Revised (p.3)       │
│ (25% width)│   (37.5% width)     │   (37.5% width)       │
│            │                     │                       │
│ [Filters]  │  ┌───────────────┐  │  ┌───────────────┐    │
│            │  │               │  │  │               │    │
│ #1 ● Text  │  │  Page image   │  │  │  Page image   │    │
│ #2 ○ Table │  │  with overlay │  │  │  with overlay │    │
│ #3 ○ Annot │  │  highlights   │  │  │  highlights   │    │
│ #4 ○ Text  │  │               │  │  │               │    │
│            │  └───────────────┘  │  └───────────────┘    │
│ ────────── │                     │                       │
│ Progress:  │                     │                       │
│ 1/12 done  │                     │                       │
├────────────┴─────────────────────┴───────────────────────┤
│  [← Prev] Change #1: Text Modified (Material, 0.94)     │
│  Before: "Grade A steel"  →  After: "Grade B titanium"   │
│  [Accept] [Reject] [Edit] [Escalate]         [Next →]   │
└──────────────────────────────────────────────────────────┘
```

Color coding:
- **Material** — red (`danger.500`)
- **Substantive** — amber (`warning.500`)
- **Cosmetic** — blue (`info.500`)
- **Uncertain** — purple (`accent.500`)

### 8.6 Routing integration

Add to `App.tsx` under protected routes:
```tsx
<Route path="docdiff" element={<RequirePermission permission="docdiff:read"><DocDiffScreen /></RequirePermission>} />
```

Add navigation manifest entry in backend (when ERP integration is enabled).

---

## 9. Authentication

### 9.1 JWT validation (ERP-embedded)

FastAPI validates JWT tokens using the same `JWT_SECRET` as the Node.js backend. The middleware:
1. Extracts `Authorization: Bearer <token>` header
2. Decodes and verifies signature using `python-jose`
3. Extracts `user_id`, `company_id`, `tenant_id` from claims
4. Attaches to request state for downstream use

No call to Node.js needed — just shared secret.

### 9.2 API key validation (public access)

1. Extracts `X-API-Key` header
2. SHA-256 hashes the key
3. Looks up `key_hash` in `api_keys` table
4. Verifies `is_active = true`
5. Updates `last_used_at`

### 9.3 Middleware flow

```python
async def get_current_user(request: Request) -> AuthContext:
    # Try JWT first
    if auth_header := request.headers.get("Authorization"):
        return validate_jwt(auth_header)
    # Fall back to API key
    if api_key := request.headers.get("X-API-Key"):
        return validate_api_key(api_key)
    raise HTTPException(401, "Authentication required")
```

---

## 10. Configuration (`.env.example`)

```env
# === Service ===
DOCDIFF_HOST=0.0.0.0
DOCDIFF_PORT=8000
DOCDIFF_ENV=development           # development | production
DOCDIFF_LOG_LEVEL=INFO
DOCDIFF_CORS_ORIGINS=http://localhost:5173,http://localhost:3000

# === Database ===
DOCDIFF_DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/avy_erp
DOCDIFF_DATABASE_SCHEMA=docdiff

# === Redis ===
DOCDIFF_REDIS_URL=redis://localhost:6379/2

# === Auth ===
JWT_SECRET=shared-with-node-backend    # Must match ERP backend JWT_SECRET

# === Storage ===
DOCDIFF_STORAGE_PATH=./storage

# === AI Providers ===
ANTHROPIC_API_KEY=sk-ant-...
GOOGLE_API_KEY=AI...
OPENROUTER_API_KEY=sk-or-...
QWEN_LOCAL_ENDPOINT=http://mac-studio.local:8080/v1

# === AI Defaults ===
DOCDIFF_DEFAULT_PROVIDER=anthropic
DOCDIFF_DEFAULT_MODEL=claude-sonnet-4-6
DOCDIFF_CONFIDENCE_THRESHOLD=0.75     # Below this → flagged for human review
DOCDIFF_PAGE_RENDER_DPI=250

# === Processing ===
DOCDIFF_MAX_PAGES=10                  # Prototype limit (configurable)
DOCDIFF_MAX_FILE_SIZE_MB=50
DOCDIFF_MAX_RETRIES=3
DOCDIFF_RETRY_BACKOFF_BASE=1         # seconds
```

---

## 11. Python Dependencies

### Production

| Package | Purpose |
|---|---|
| `fastapi>=0.115` | Web framework |
| `uvicorn[standard]>=0.34` | ASGI server |
| `sqlalchemy[asyncio]>=2.0` | Async ORM |
| `asyncpg>=0.30` | PostgreSQL async driver |
| `alembic>=1.14` | Database migrations |
| `pydantic>=2.10` | Data validation + settings |
| `pydantic-settings>=2.7` | Environment config |
| `redis[hiredis]>=5.2` | Async Redis client |
| `arq>=0.26` | Async task queue (Redis-backed) |
| `httpx>=0.28` | Async HTTP client (OpenRouter, Qwen, general) |
| `anthropic>=0.52` | Anthropic SDK |
| `google-genai>=1.14` | Google Gemini SDK |
| `PyMuPDF>=1.25` | PDF metadata, page rendering |
| `docling>=2.25` | Structural document parsing (tables, sections) |
| `diff-match-patch>=20241021` | Google's text diff library |
| `weasyprint>=63` | HTML → PDF report generation |
| `Pillow>=11.1` | Image manipulation |
| `python-jose[cryptography]>=3.3` | JWT validation |
| `python-multipart>=0.0.18` | File upload parsing |
| `tenacity>=9.0` | Retry with exponential backoff |

### Development

| Package | Purpose |
|---|---|
| `pytest>=8.3` | Test runner |
| `pytest-asyncio>=0.25` | Async test support |
| `httpx` | Test client (already in prod deps) |
| `ruff>=0.9` | Linter + formatter |
| `mypy>=1.14` | Type checking |

---

## 12. Risks Addressed

| Risk from PRD | Mitigation in this design |
|---|---|
| Table alignment fails on complex tables | Docling handles merged cells, spanning headers natively (95%+ on benchmarks). Fallback to VLM image-based extraction for tables Docling can't parse. |
| AI hallucinated changes | Confidence scoring + mandatory human review below threshold. Visual source highlighting in review UI for instant verification. |
| Handwriting transcription inaccurate | Always show source image alongside transcription. High confidence threshold (0.8+). Most handwritten content routes to human review. |
| Cloud API rate limits during demo | tenacity retry with exponential backoff. Multiple providers configured — switch on failure. Pre-process demo docs. |
| PDF parsing fails on specific formats | Validation in Stage 1 catches encrypted/malformed PDFs. Docling + PyMuPDF cover born-digital and scanned. VLM fallback for anything structural parsing misses. |

---

## 13. What This Spec Does NOT Cover

- Mobile app integration (prototype is web-only)
- ERP navigation manifest entry (added when ERP integration is wired)
- Detailed prompt content (iterated during development)
- Production deployment (Docker compose for prod, scaling, monitoring)
- Documents exceeding 10 pages
- Multi-tenant isolation within DocDiff (prototype is single-tenant)

---

*This spec is the implementation blueprint. The PRD (`docs/DocDiff-Pro-PRD-Prototype-v0.1.md`) remains the authoritative requirements document.*
