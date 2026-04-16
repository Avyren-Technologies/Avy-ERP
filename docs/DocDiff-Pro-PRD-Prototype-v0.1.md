# Product Requirements Document

## DocDiff Pro — Intelligent Document Comparison System

**Version:** 0.1 (Prototype)
**Date:** April 16, 2026
**Author:** [CTO Name]
**Status:** Draft — For Client Demonstration

---

## 1. Executive Summary

DocDiff Pro is an AI-powered document comparison system designed for order entry teams that receive detailed customer specifications in PDF format. The system compares two versions of a document — the original submission and the customer's revised version — and produces a structured, navigable report of all changes including text modifications, table edits, and handwritten annotations.

This document covers the **prototype scope**: a functional demonstration limited to 10-page documents, built to validate the core pipeline before committing to a full production build. The prototype will process real customer document pairs end-to-end and produce a reviewable diff report within a web interface embedded in the existing ERP frontend.

---

## 2. Problem Statement

The client's order entry team currently receives customer specification documents (up to 500 pages in production) containing descriptive text, tabulated data, and engineering details. After the first revision is submitted, customers return updated specification sheets with changes that may include modified text, altered table values, and handwritten notes or annotations in the margins.

Today, identifying these changes is entirely manual — a reviewer reads both versions side by side, page by page. This process is slow (hours per document), error-prone (missed changes lead to incorrect orders), and does not scale. The cost of a missed change is a manufacturing error, a reorder, and damaged client trust.

The client needs a system that reliably surfaces every change between two document versions, classifies each change by type and significance, and presents them in a reviewable interface where a human operator can verify, correct, or approve each detected difference.

---

## 3. Goals and Success Criteria

### Prototype Goals

- Demonstrate end-to-end document comparison on real 10-page specification pairs
- Prove the AI pipeline can accurately detect text, table, and annotation changes
- Show the human review workflow with accept, reject, and manual correction capabilities
- Validate processing time is acceptable for the client's operational cadence
- Build client confidence for a full production engagement

### Success Criteria (Prototype)

| Metric | Target |
|---|---|
| Printed text change detection accuracy | ≥ 98% |
| Table cell change detection accuracy | ≥ 93% |
| Handwritten annotation detection rate (flagged, not necessarily transcribed) | ≥ 85% |
| False positive rate (changes reported that are not real) | < 5% |
| Silent miss rate (real changes not flagged at all) | 0% — every page region must be either auto-diffed or flagged for review |
| Processing time for a 10-page pair | < 90 seconds |
| Human review time per document pair | < 15 minutes (for 10 pages) |

### Production Goals (Post-Prototype, for reference only)

- Scale to 500-page documents
- Sub-30-minute processing per pair
- SaaS deployment with authentication, audit logging, and encrypted storage
- Integration with client's existing order management workflow

---

## 4. User Personas

### Primary: Order Entry Reviewer

**Role:** Reviews incoming customer specifications and identifies changes between revisions.

**Context:** Non-technical user. Familiar with the product domain and specification formats. Currently does manual side-by-side comparison. Comfortable with web applications but not with developer tools.

**Needs:** A clear, navigable list of all changes. Ability to verify each change against the original documents. Ability to flag uncertain items for escalation. A final exportable report they can attach to the order.

**Frustration:** Spending 2-4 hours per document pair on manual comparison. Missing small but critical changes (a single number in a tolerance table, a margin note changing a material grade). Being blamed for errors that were genuinely hard to spot.

### Secondary: Team Lead / Supervisor

**Role:** Oversees the order entry process and ensures quality.

**Context:** Reviews the final diff reports before orders are confirmed. Needs confidence that the system has not missed anything. Wants summary-level visibility without reading every page.

**Needs:** Dashboard showing comparison status (pending, in review, completed). Summary statistics per comparison (total changes found, changes by category, items flagged for review). Audit trail of who reviewed what and when.

### Tertiary: Client CTO (You)

**Role:** Evaluating the prototype to decide on production investment.

**Context:** Needs to see the system handle real documents, understand accuracy limits, and assess build-vs-buy economics.

**Needs:** Transparent accuracy metrics. Clear demonstration of the human-in-the-loop workflow. Confidence that the architecture scales to 500 pages without a rewrite.

---

## 5. Scope — What Is In and Out for the Prototype

### In Scope

- Upload two PDF documents (original and revised), each up to 10 pages
- Automated parsing of both documents into structured representations
- Detection and classification of changes across text, tables, and images/annotations
- Confidence scoring on every detected change
- Side-by-side visual comparison view with highlighted differences
- Human review interface with accept, reject, edit, and flag-for-escalation actions
- Navigation between changes (previous/next with keyboard shortcuts)
- Summary report generation with categorized change list
- Export of final diff report as a downloadable PDF
- Support for digitally created PDFs (born-digital) as the primary input
- Support for scanned PDFs with printed text as a secondary input
- Detection of handwritten annotations (transcription attempted, flagged for review if low confidence)
- Multiple AI model backends selectable per job (for benchmarking during prototype phase)

### Out of Scope (Prototype)

- Documents exceeding 10 pages
- User authentication and role-based access control
- Multi-tenant SaaS infrastructure
- Billing, subscription management, or usage metering
- Integration with the client's ERP or order management system
- Batch processing of multiple document pairs simultaneously
- Version history beyond two documents (no three-way diff)
- Real-time collaboration between multiple reviewers
- Mobile-optimized interface
- Offline or on-premise deployment
- Automated order creation or downstream workflow triggers
- Non-English document support
- Word, Excel, or image-only input formats

---

## 6. Functional Requirements

### 6.1 Document Upload and Job Creation

**FR-01:** The system shall provide a drag-and-drop upload area where the user selects two PDF files: one labeled "Original" and one labeled "Revised."

**FR-02:** The system shall validate uploaded files before processing. Validation checks: file is a valid PDF, file size does not exceed 50 MB, page count does not exceed 10 pages, file is not password-protected or encrypted.

**FR-03:** Upon successful upload, the system shall create a comparison job with a unique identifier and display a progress indicator showing the current processing stage.

**FR-04:** The system shall allow the user to select which AI model backend to use for the comparison (for prototype benchmarking purposes). Available options shall include cloud API models and the self-hosted model.

**FR-05:** The system shall store both uploaded documents and all intermediate processing artifacts for the duration of the prototype evaluation period.

### 6.2 Document Parsing Pipeline

**FR-06:** The system shall parse each uploaded PDF into a structured representation that preserves text blocks, table structures (rows, columns, cells, merged cells), figure/image regions, page headers/footers, and section hierarchy.

**FR-07:** For born-digital PDFs, the system shall extract text directly from the PDF text layer without OCR, preserving formatting and reading order.

**FR-08:** For scanned PDFs or pages without a text layer, the system shall perform OCR using the configured vision-language model to extract text and table structures.

**FR-09:** The system shall detect regions containing handwriting or manual annotations on each page. Detection shall be performed regardless of whether the page also contains printed text.

**FR-10:** For each detected handwritten region, the system shall attempt transcription using the VLM and assign a confidence score (0.0 to 1.0) to the transcription result.

**FR-11:** The system shall extract and preserve any native PDF annotation objects (sticky notes, highlights, strikethroughs, stamps, text boxes) as structured metadata separate from the page content.

**FR-12:** The parsed representation of each document shall retain bounding box coordinates for every extracted element, enabling click-to-source navigation in the review interface.

### 6.3 Comparison Engine

**FR-13:** The system shall align corresponding sections, paragraphs, and tables between the original and revised documents before performing the diff. Alignment shall use section titles, heading hierarchy, table captions, and positional cues.

**FR-14:** The system shall detect the following change types:

| Change Type | Description |
|---|---|
| Text Addition | New text present in the revised version that does not exist in the original |
| Text Deletion | Text present in the original that is missing from the revised version |
| Text Modification | Text that exists in both versions but with different content |
| Table Cell Change | A specific cell value in a table has been modified |
| Table Row Addition | A new row has been added to a table |
| Table Row Deletion | A row has been removed from a table |
| Table Structure Change | Column count, header labels, or merged cell structure has changed |
| Annotation Added | A handwritten note, markup, or PDF annotation is present in the revised version but not the original |
| Annotation Removed | An annotation present in the original is missing from the revised version |
| Section Moved | A block of content has been relocated to a different position in the document |
| Formatting Change | Non-content changes such as font size, bolding, or alignment (detected but classified as cosmetic) |

**FR-15:** Each detected change shall be assigned a confidence score (0.0 to 1.0) indicating the system's certainty that the change is real and correctly characterized.

**FR-16:** Each detected change shall be classified by significance:

- **Material** — Changes to specifications, tolerances, quantities, materials, dimensions, or any value that would affect manufacturing or pricing
- **Substantive** — Changes to requirements text, scope descriptions, terms, or conditions that alter meaning
- **Cosmetic** — Formatting, whitespace, pagination, or stylistic changes with no impact on meaning
- **Uncertain** — Changes the system cannot confidently classify; requires human review

**FR-17:** Changes with a confidence score below the configurable threshold (default: 0.75) shall be automatically flagged for human review regardless of classification.

**FR-18:** Any page region where the system cannot determine whether a change exists (due to poor scan quality, illegible handwriting, or parsing failure) shall be flagged as "Unresolved Region" and presented for mandatory human review.

### 6.4 Human Review Interface

**FR-19:** The review interface shall display the original and revised documents side by side, with synchronized scrolling and page navigation.

**FR-20:** Detected changes shall be highlighted on both documents using color coding by significance (material = red, substantive = amber, cosmetic = blue, uncertain = purple).

**FR-21:** A change list panel shall display all detected changes in a scrollable, filterable list. Each entry shall show: change number, page number, change type, significance classification, confidence score, and a brief text summary.

**FR-22:** Clicking a change in the list shall scroll both document views to the relevant location and visually emphasize the change region.

**FR-23:** The user shall be able to navigate between changes using "Previous Change" and "Next Change" controls, with keyboard shortcuts (e.g., arrow keys or J/K).

**FR-24:** For each change, the reviewer shall have the following actions available:

| Action | Effect |
|---|---|
| Accept | Confirms the change is real and correctly described. Included in the final report as-is. |
| Reject | Marks the change as a false positive. Excluded from the final report. |
| Edit | Opens an inline editor where the reviewer can correct the change description, modify the transcription, or reclassify the significance. |
| Flag for Escalation | Marks the change for supervisor review. Adds a comment field. |

**FR-25:** The review interface shall display a progress bar showing how many changes have been reviewed out of the total, with separate counts for auto-accepted (high confidence), manually reviewed, and pending items.

**FR-26:** The reviewer shall be able to filter the change list by: change type, significance level, confidence score range, review status (pending, accepted, rejected, escalated), and page number.

**FR-27:** For handwritten annotations flagged as low confidence, the review interface shall display the original image region alongside the attempted transcription, allowing the reviewer to correct the transcription directly.

**FR-28:** The review interface shall support a "page-level view" mode where the user can browse page by page and see all changes on the current page highlighted, as an alternative to the change-list-driven navigation.

### 6.5 Report Generation

**FR-29:** Upon completion of the review (all changes addressed), the system shall generate a summary report containing:

- Document metadata (filenames, page counts, upload timestamps)
- Total changes found, broken down by type and significance
- Number of changes auto-accepted vs. manually reviewed vs. rejected vs. escalated
- A sequential list of all accepted changes with page references, before/after values, reviewer action, and any comments
- A list of escalated items with reviewer comments

**FR-30:** The report shall be viewable in the browser and exportable as a downloadable PDF document.

**FR-31:** The PDF report shall include page references that correspond to the original document page numbers for easy cross-referencing with physical copies.

**FR-32:** The report shall include a visual diff section showing side-by-side page thumbnails with highlighted change regions for each accepted change.

### 6.6 Processing Status and Feedback

**FR-33:** During document processing, the system shall display real-time progress updates showing the current stage: uploading, parsing original, parsing revised, aligning sections, computing differences, classifying changes, and ready for review.

**FR-34:** If processing fails at any stage, the system shall display a clear error message indicating which stage failed and a suggested action (re-upload, try different model, contact support).

**FR-35:** Processing shall be non-blocking — the user shall be able to navigate away from the processing view and return to check status later.

---

## 7. Non-Functional Requirements

### 7.1 Performance

**NFR-01:** End-to-end processing time for a 10-page document pair shall not exceed 90 seconds when using cloud API models.

**NFR-02:** End-to-end processing time for a 10-page document pair shall not exceed 180 seconds when using the self-hosted model on the Mac Studio.

**NFR-03:** The review interface shall load within 3 seconds after processing completes.

**NFR-04:** Navigation between changes (next/previous) shall respond within 200 milliseconds.

**NFR-05:** The system shall handle PDF files up to 50 MB without degradation.

### 7.2 Reliability

**NFR-06:** If an AI model API call fails (timeout, rate limit, server error), the system shall retry up to 3 times with exponential backoff before marking the affected region as "Processing Failed" and continuing with the remaining document.

**NFR-07:** A partial processing failure (one page fails, others succeed) shall not abort the entire comparison. Successfully processed pages shall remain available for review, with failed pages clearly marked.

**NFR-08:** All uploaded documents and processing results shall be persisted to disk. A browser refresh or disconnection shall not lose work in progress.

### 7.3 Usability

**NFR-09:** The review interface shall be usable by a non-technical order entry clerk with no training beyond a 5-minute walkthrough.

**NFR-10:** All interactive elements shall have clear labels, tooltips, and consistent visual language.

**NFR-11:** The system shall display processing costs (estimated tokens consumed, model used) per comparison for the CTO's evaluation purposes during the prototype phase.

### 7.4 Scalability Considerations (Prototype Constraints)

**NFR-12:** The prototype shall be architected such that the 10-page limit is a configurable parameter, not a structural limitation. The same codebase shall be extensible to 500 pages by adjusting configuration and scaling infrastructure.

**NFR-13:** The document parsing pipeline shall process pages independently (embarrassingly parallel), so that scaling to larger documents requires only adding processing capacity, not redesigning the pipeline.

**NFR-14:** The comparison engine shall operate on the structured representation (not raw PDFs), ensuring that comparison cost scales with content volume, not file size.

---

## 8. Technical Specifications

### 8.1 System Architecture Overview

The system follows a three-tier architecture with clear separation between the frontend (presentation), the backend (orchestration and business logic), and the AI pipeline (document parsing and comparison).

**Frontend Tier:** Embedded within the existing ERP application. Built with the same ReactJS and TailwindCSS stack. Communicates with the backend via REST endpoints for CRUD operations and WebSocket connections for real-time processing status updates.

**Backend Tier:** A dedicated Python service using FastAPI. This service handles document upload and storage, job orchestration, AI model routing, comparison logic, and report generation. It runs as an independent microservice alongside the existing Node.js/Express ERP backend. The two backends communicate through a shared Redis instance for job status and event propagation, while PostgreSQL serves as the persistent data store.

**AI Pipeline Tier:** The actual AI inference layer, abstracted behind a unified interface. The backend routes requests to one of several model providers based on job configuration:

- Cloud API providers accessed via their respective SDKs (for prototype benchmarking)
- Self-hosted Qwen3-VL model running on the Mac Studio via an OpenAI-compatible local inference server

### 8.2 Frontend Technical Specifications

| Specification | Detail |
|---|---|
| Framework | ReactJS (existing ERP stack) |
| Styling | TailwindCSS (existing ERP stack) |
| State Management | As per existing ERP conventions |
| PDF Rendering | Client-side PDF viewer library for side-by-side display with overlay support |
| Real-Time Updates | WebSocket connection via existing Socket.IO infrastructure |
| File Upload | Chunked upload with progress tracking |
| Keyboard Navigation | Global hotkeys for change navigation (configurable) |

### 8.3 Backend Technical Specifications

| Specification | Detail |
|---|---|
| Language | Python 3.11+ |
| Framework | FastAPI with async request handling |
| Task Queue | Redis-backed job queue for async document processing |
| Database | PostgreSQL (shared with existing ERP, separate schema) |
| Real-Time | Redis Pub/Sub for status events, bridged to Socket.IO via the Node.js layer |
| File Storage | Local filesystem for prototype (S3-compatible interface for production migration) |
| PDF Parsing Library | Open-source document structure extraction toolkit |
| Diff Engine | Structural diff operating on parsed JSON representations |
| Report Generation | HTML-to-PDF rendering pipeline |

### 8.4 AI Model Configuration (Prototype)

The prototype shall support the following model backends, selectable per comparison job. This allows the CTO to benchmark accuracy, speed, and cost across providers before committing to a production model.

| Provider | Models | Role | Connection |
|---|---|---|---|
| OpenRouter | Best available vision-language model | Document parsing, annotation reading, change classification | Cloud API via API key |
| Anthropic | Claude Sonnet 4.6, Claude Opus 4.6 | Document parsing, semantic change classification, report narrative | Cloud API via API key |
| Google | Gemini 3.1 Pro, Gemini 3 Flash | Document parsing, table extraction, annotation reading | Cloud API via API key |
| Self-Hosted | Qwen3-VL-8B (or 30B-A3B) | Document parsing, annotation reading | Local inference server on Mac Studio, OpenAI-compatible endpoint |

All models shall be accessed through a unified abstraction layer so that adding or removing a model requires configuration changes only, not code changes.

### 8.5 Self-Hosted Model Deployment

| Specification | Detail |
|---|---|
| Hardware | Mac Studio M4 Max, 36 GB unified memory, 512 GB SSD + 2 TB external SSD |
| Inference Framework | MLX-based inference server with OpenAI-compatible API |
| Primary Model | Qwen3-VL-8B (4-bit quantization, approximately 5-6 GB memory footprint) |
| Upgrade Model | Qwen3-VL-30B-A3B MoE (4-bit quantization, approximately 18-20 GB, only 3B parameters active per token) |
| Concurrency | Single-request processing (sufficient for prototype volume) |
| Model Storage | External 2 TB SSD for model weights and document storage |

### 8.6 Document Processing Pipeline Stages

The processing pipeline executes the following stages sequentially for each document in a comparison pair:

**Stage 1 — Ingestion and Validation:** Accept the uploaded PDF, validate format and page count, extract basic metadata (page count, file size, creation date, PDF version), and store the file.

**Stage 2 — Page Classification:** For each page, determine whether it is born-digital (has embedded text layer), scanned (image-only), or mixed. Detect the presence of handwritten content or annotation overlays on each page.

**Stage 3 — Structured Extraction:** For born-digital pages, extract text, tables, and layout using the document parsing toolkit (no AI model needed). For scanned or mixed pages, send page images to the configured AI model for vision-based extraction. For pages with detected handwriting, send the relevant regions to the AI model for transcription with confidence scores. Extract native PDF annotation objects structurally.

**Stage 4 — Normalization:** Normalize the extracted content into a canonical structured format. Standardize table representations (consistent row/column indexing). Normalize whitespace, line breaks, and encoding. Assign unique identifiers to every content block with bounding box coordinates.

**Stage 5 — Alignment:** Match corresponding content blocks between the original and revised documents. Align sections by heading hierarchy and title similarity. Align tables by caption, position, and structural similarity. Align text paragraphs by position and content similarity. Identify unmatched blocks (new content in revised, deleted content from original).

**Stage 6 — Diff Computation:** For each aligned pair, compute the specific differences. Text diffs at the word level. Table diffs at the cell level. Annotation diffs by presence/absence and content. Generate a unified diff record for each change.

**Stage 7 — Classification and Scoring:** For each diff record, assign a confidence score based on extraction quality and alignment certainty. Classify significance (material, substantive, cosmetic, uncertain) using the AI model's reasoning capabilities for non-obvious cases. Flag low-confidence items for human review.

**Stage 8 — Result Assembly:** Compile all diff records into a structured comparison result. Generate page-level and document-level summaries. Store the result and mark the job as ready for review.

### 8.7 Inter-Service Communication

The FastAPI backend and the existing Node.js/Express backend operate as independent services sharing infrastructure:

**Shared PostgreSQL:** The FastAPI service uses a dedicated schema within the existing PostgreSQL instance. No direct table dependencies between the two backends. The Node.js backend references comparison job IDs as foreign keys if integration is needed.

**Shared Redis:** Used for three purposes: (1) job queue for async document processing tasks, (2) pub/sub channel for real-time processing status events that the Node.js layer bridges to the frontend via Socket.IO, and (3) short-lived caching of processing artifacts.

**REST Communication:** The Node.js backend may call the FastAPI service's REST endpoints to create jobs, check status, and retrieve results. The FastAPI service does not call the Node.js backend.

---

## 9. User Flows

### 9.1 Primary Flow — Compare Two Documents

1. User navigates to the Document Comparison section within the ERP
2. User drags and drops (or selects) two PDF files into the upload area, labeling one as "Original" and one as "Revised"
3. System validates both files and displays validation results
4. User selects the AI model to use (dropdown with available options)
5. User clicks "Start Comparison"
6. System displays a processing progress view with stage indicators updating in real time
7. Upon completion, system transitions to the Review Interface with all detected changes loaded
8. User reviews changes using the side-by-side view and change list
9. For each change, user accepts, rejects, edits, or escalates
10. User clicks "Generate Report" when all changes are addressed
11. System generates and displays the summary report
12. User downloads the report as a PDF

### 9.2 Secondary Flow — Review Low-Confidence Handwriting

1. During the review flow, user encounters a change flagged as "Uncertain — Low Confidence Handwriting"
2. System displays the cropped image of the handwritten region from the revised document
3. Below the image, system shows its attempted transcription with the confidence score
4. User reads the handwriting and either confirms the transcription is correct (Accept) or types the correct text (Edit)
5. If the handwriting is truly illegible, user clicks "Flag for Escalation" and adds a note
6. The corrected or escalated change is saved and the user moves to the next item

### 9.3 Secondary Flow — Handle Unresolved Region

1. During review, user encounters a region marked as "Unresolved — Could Not Determine Change Status"
2. System displays the region from both documents side by side at high zoom
3. User visually compares the regions and determines whether a change exists
4. If a change exists, user clicks "Add Change Manually" and describes the change
5. If no change exists, user clicks "No Difference" to dismiss the region
6. The resolution is recorded and the user moves to the next item

### 9.4 Tertiary Flow — Benchmark Model Accuracy

1. CTO uploads the same document pair multiple times, selecting a different AI model each time
2. System processes each comparison independently
3. CTO opens each comparison's results side by side (in separate tabs)
4. CTO compares detected changes, confidence scores, and processing times across models
5. CTO uses this data to select the optimal model(s) for production deployment

---

## 10. UI/UX Requirements

### 10.1 Upload View

- Clean, centered upload area with clear labeling for "Original" and "Revised" slots
- Drag-and-drop with file-type and size validation feedback inline
- Model selector dropdown with brief descriptions of each option
- "Start Comparison" button disabled until both files are uploaded and validated
- Upload progress bar per file during transfer

### 10.2 Processing View

- Vertical stage indicator showing all 8 pipeline stages
- Current stage highlighted with an animated progress indicator
- Completed stages marked with a green checkmark
- Estimated time remaining displayed (based on page count and model)
- "Cancel" button available at all stages
- Non-blocking — user can navigate elsewhere and return

### 10.3 Review Interface

- Three-panel layout: change list (left, 25% width), original document (center-left, 37.5%), revised document (center-right, 37.5%)
- Change list panel is collapsible to give more space to documents
- Documents rendered as high-fidelity page images with overlay highlights
- Synchronized scrolling between original and revised views (toggleable)
- Zoom controls (fit page, fit width, percentage zoom, pinch-to-zoom)
- Change highlights use semi-transparent overlays in significance-coded colors
- Active change has a more prominent border/glow treatment
- Action buttons (Accept, Reject, Edit, Escalate) always visible in a fixed action bar at the bottom or in a floating panel attached to the active change
- Keyboard shortcuts displayed in a help overlay (toggle with "?" key)
- Progress indicator showing review completion percentage

### 10.4 Report View

- Full-width document-style layout
- Printable formatting (proper page breaks, headers, footers)
- Executive summary section at the top with key metrics
- Change table with sortable columns
- Each change entry includes a thumbnail showing the highlighted region
- "Download PDF" button prominently placed
- "Return to Review" button to make corrections if needed

### 10.5 Design Principles

- **Minimal cognitive load:** The reviewer's job is already mentally taxing. The interface should reduce effort, not add to it. Defaults should be sensible, navigation should be obvious, and the most common action should require the fewest clicks.
- **Transparency over magic:** Always show the confidence score. Always show the source region. Never auto-accept a change without the reviewer seeing it (in the prototype). Trust is built by showing the system's reasoning, not hiding it.
- **Consistent with the existing ERP:** Use the same component library, color palette, and interaction patterns as the rest of the ERP application. This is not a standalone product — it is a feature within a system the users already know.

---

## 11. Risks and Mitigations

### 11.1 Technical Risks

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| AI model produces hallucinated changes (reports changes that do not exist) | Medium | High — erodes user trust | Confidence scoring with mandatory human review for scores below threshold. Visual source highlighting so reviewer can instantly verify. |
| Table alignment fails on complex tables (merged cells, spanning headers, nested tables) | High | Medium — reviewer must manually compare the table | Dedicated table comparison logic with fallback to image-based side-by-side display when structural alignment fails. |
| Handwriting transcription is too inaccurate to be useful | Medium | Low (for prototype) — handwriting is a small fraction of content | Always show the source image alongside transcription. Set confidence threshold high (0.8+) so most handwritten content goes to human review. Accuracy improves with production fine-tuning. |
| Self-hosted model on Mac Studio is too slow for demo | Low | Medium — bad impression on client | Pre-process demo documents before the meeting. Have cloud API fallback ready. Show both options. |
| PDF parsing fails on specific document formats (password-protected, unusual encodings, form-based PDFs) | Medium | Low — prototype uses known document samples | Validate against 5-10 real client documents during development. Build robust error handling for unsupported formats. |
| Cloud API rate limits or outages during demo | Low | High — demo fails | Have multiple providers configured. Cache results of previously processed documents. Have the self-hosted model as fallback. |

### 11.2 Business Risks

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Client expects 100% accuracy from the prototype | High | High — disappointment despite strong performance | Set expectations clearly upfront: the system achieves 100% coverage (nothing missed), not 100% accuracy (some items need human verification). Frame the human review step as a feature, not a limitation. |
| Client's actual documents are significantly harder than expected (unusual layouts, poor scan quality, non-standard annotations) | Medium | Medium — accuracy numbers drop from estimates | Require 3-5 real document pairs from the client before the demo. Run them through the pipeline during development and tune accordingly. |
| Scope creep during prototype phase (client asks for additional features) | High | Medium — delays delivery | This PRD defines the boundary. Any feature not listed here is out of scope for the prototype and documented as a production roadmap item. |
| Client perceives "AI processing" as risky or untrustworthy | Medium | Medium — hesitation to adopt | Emphasize the human-in-the-loop design. Show that no change is ever automatically acted upon — every change goes through a reviewer. Position the AI as a highlighter, not a decision-maker. |

---

## 12. Assumptions and Dependencies

### Assumptions

- The client will provide 3-5 real document pairs (anonymized if necessary) for development and testing before the prototype demo
- Customer specification documents are primarily in English
- The documents follow a generally consistent format (specification sheets, not free-form creative documents)
- The existing ERP frontend can accommodate a new feature module without major refactoring
- The Mac Studio hardware is available and set up before development begins
- API keys for all cloud providers are provisioned and have sufficient quota for development and demo

### Dependencies

- Access to the existing ERP codebase and development environment
- Access to the existing PostgreSQL and Redis instances (or dedicated instances for the prototype)
- Network connectivity between the development environment and cloud API providers
- Network connectivity between the frontend server and the Mac Studio (for self-hosted model)

---

## 13. Prototype Timeline

| Week | Phase | Deliverables |
|---|---|---|
| Week 1 | Environment Setup and Document Analysis | Development environment configured. FastAPI project scaffolded and connected to PostgreSQL and Redis. Mac Studio configured with inference server and Qwen3-VL model. 3-5 client document pairs analyzed and characterized. |
| Week 2 | Parsing Pipeline (Stages 1-4) | Document upload and validation working. Born-digital PDF parsing producing structured JSON output. Scanned page OCR working via cloud APIs and self-hosted model. Handwriting detection and transcription producing results with confidence scores. |
| Week 3 | Comparison Engine (Stages 5-8) | Section and table alignment working. Text diff producing word-level changes. Table diff producing cell-level changes. Annotation detection and comparison working. Confidence scoring and significance classification functional. |
| Week 4 | Review Interface | Side-by-side document viewer with overlay highlights. Change list with filtering and navigation. Accept, reject, edit, and escalate actions working. Keyboard shortcuts implemented. |
| Week 5 | Report Generation and Polish | Summary report generation (browser view and PDF export). Processing status view with real-time updates. Error handling and edge case coverage. Model benchmarking across all configured providers. |
| Week 6 | Testing, Tuning, and Demo Prep | End-to-end testing on all client document pairs. Accuracy measurement against manually identified changes. Performance optimization and UI polish. Demo script preparation and rehearsal. |

**Total prototype build: 6 weeks with a team of 2 engineers (1 backend/AI, 1 frontend).**

---

## 14. Open Questions

These items require decisions or additional information before or during development:

1. **Sample documents:** Has the client provided real document pairs? If not, when can we expect them? The prototype's credibility depends entirely on demonstrating against real data.

2. **Annotation format:** Do the client's customers use PDF annotation tools (Adobe Acrobat, Foxit) to mark up revisions, or do they print, write by hand, and re-scan? The answer significantly affects accuracy expectations and pipeline design.

3. **Tolerance for processing time:** Is 90 seconds acceptable for the demo, or does the client expect near-instantaneous results? This affects model selection (fast cloud API vs. accurate but slower self-hosted).

4. **Report format preferences:** Does the client have a preferred report layout or template? Do they need the report to match an existing internal format?

5. **ERP integration depth:** For the prototype, is a standalone feature module acceptable, or does the client need to see at least a basic integration with existing order workflows?

6. **Budget for cloud API usage during prototype:** Estimated token consumption for 50 document pair comparisons (10 pages each) across 4 providers: approximately $50-150 total during the development and demo phase. Is this approved?

---

## 15. Future Roadmap (Post-Prototype)

The following items are explicitly deferred to the production phase and are listed here for completeness:

- Scale to 500-page documents with parallel page processing
- Multi-user authentication with role-based access
- SaaS deployment with encryption, audit logging, and data retention policies
- Three-way comparison (original, revised, second revision)
- Batch processing queue for multiple document pairs
- Fine-tuning the self-hosted model on client-specific handwriting samples
- Integration with the client's order management and ERP systems
- Automated change categorization rules (e.g., "any change to column X in the BOM table is always Material")
- Historical comparison archive with search
- Multi-language document support
- API for programmatic job submission by upstream systems

---

*This document is a living artifact. It will be updated as prototype development progresses and as answers to the open questions become available.*
