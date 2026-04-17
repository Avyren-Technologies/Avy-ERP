# DocDiff Pro — Accuracy Improvements Documentation

**Version:** 2.0
**Date:** April 2026

---

## Pipeline Overview

```
PDF Upload → Stage 1 (Validate) → Stage 2 (Classify pages)
  → Stage 3 (Extract content) → Stage 4 (Normalize)
  → Stage 5 (Align pages & blocks) → Stage 6 (Compute diffs)
  → Stage 7 (Score & classify) → Stage 8 (Deduplicate & save)
```

---

## Improvements by Stage

### Stage 1 — Ingestion & Validation

| What | Before | After |
|---|---|---|
| DPI rendering | Fixed 250 DPI for all pages | Adaptive: 150 DPI born-digital, 300 DPI scanned |

**Why it matters:** Scanned PDFs need higher resolution for accurate VLM OCR. Born-digital PDFs don't need high resolution since text is extracted directly from the text layer, not from the image.

### Stage 2 — Page Classification

| What | Before | After |
|---|---|---|
| Classification method | Binary: `has_text_layer()` (>10 chars = digital) | Text density analysis using PyMuPDF block-level metrics |
| Page types | `born_digital` or `scanned` | `born_digital`, `scanned`, or `mixed` (OCR'd scanned) |
| Confidence | None | 0.70-0.95 per page |

**How it works now:**
- Extracts text blocks and image blocks from each page
- Computes `text_coverage` (fraction of page area covered by text blocks)
- Computes `image_coverage` (fraction covered by images)
- Classification rules:
  - `text_coverage > 0.3` AND `image_coverage < 0.2` → **born_digital** (0.95)
  - `image_coverage > 0.7` AND `text_coverage < 0.1` → **scanned** (0.90)
  - `image_coverage > 0.5` AND text present → **mixed** (0.75)

**Why it matters:** OCR'd scanned PDFs have a text layer but low-quality text. Classifying them as `mixed` triggers VLM extraction for verification instead of trusting potentially garbled OCR text.

### Stage 3 — Content Extraction

| What | Before | After |
|---|---|---|
| Extraction method | Single-pass: PyMuPDF OR VLM | Two-pass merge for scanned/mixed pages |
| VLM prompt | Generic, no examples | Structured with few-shot example, per-block confidence |
| Bounding boxes | Ambiguous coordinate system | Explicitly normalized 0-1 fractions in prompt |
| Confidence | Hardcoded (0.95 PyMuPDF, 0.80 VLM) | Per-block from VLM, boosted on merge |

**Two-pass extraction (new):**
1. **Pass 1:** PyMuPDF extracts whatever text layer exists (even from OCR'd PDFs)
2. **Pass 2:** VLM extracts from the rendered page image
3. **Merge:** For each VLM block, find the closest PyMuPDF block by position overlap. If PyMuPDF text is more complete (longer), use it instead of VLM OCR. This gives VLM's structural accuracy + PyMuPDF's text fidelity.

**Extraction method labels:**
- `pymupdf` — born-digital, text extracted directly
- `vlm` — scanned, VLM-only extraction
- `vlm+pymupdf` — merged two-pass extraction

**Enhanced VLM prompt includes:**
- Explicit instruction for 0-1 normalized bounding boxes
- Per-block confidence scores (0.0-1.0)
- Complete JSON example with all block types (header, text, table, annotation, footer)
- Header/footer zone detection rules (top 8%, bottom 5%)
- Multi-column layout handling instructions
- Illegible text handling (set confidence to 0.0)

### Stage 4 — Normalization

| What | Before | After |
|---|---|---|
| Text normalization | NFKC + whitespace collapse | Same (unchanged) |
| Block ID format | `{role}_{page:03d}_blk_{counter:04d}` | Same (unchanged) |
| Bbox preservation | Implicit (not explicitly preserved) | Verified: bboxes pass through correctly |

### Stage 5 — Alignment

| What | Before | After |
|---|---|---|
| Page alignment | Position-based (page 1 ↔ page 1) | Content-similarity based (semantic matching) |
| Unmatched pages | Per-block deletion entries (hundreds) | Single scope-difference entry per page |
| Block type detection | `block_type` key only | Checks `type` first, falls back to `block_type` |

**Semantic page alignment (new):**
- Before block-level matching, aligns pages by content similarity
- Extracts all text from each page, computes pairwise similarity scores
- Threshold: 0.3 (very low — just prevents catastrophic mismatches)
- Unmatched pages (appendices, attachments) get ONE summary entry, not N deletion entries

**Impact:** When Version A has 20 pages and Version B has 14, the old approach generated ~300 false deletion entries. The new approach generates ~5 scope entries.

### Stage 6 — Diff Computation

| What | Before | After |
|---|---|---|
| Text diffing | Word-level only | Word-level + adjacent merge |
| Whitespace diffs | Passed through | Filtered at source |
| Empty blocks | Passed through | Filtered at source |
| Block ID extraction | `blk.get("block_id")` (always None) | `blk.get("id")` (correct) |
| Block type detection | `blk.get("block_type")` (missing for some parsers) | `blk.get("type")` with fallback |

**Adjacent diff merging (new):**
If consecutive text changes come from the same block pair, they're merged into a single logical change. This prevents "18%" → "21%" from being split into "delete 8" + "add 2" fragments.

**Whitespace filtering (new):**
- Blocks where both sides are empty/whitespace-only → skipped
- Blocks identical after whitespace normalization → skipped

### Stage 7 — Scoring & Classification

| What | Before | After |
|---|---|---|
| Date classification | Always material | Context-aware: metadata dates → cosmetic, other dates → substantive |
| Version IDs | Sometimes material | Always cosmetic (Rev.7→Rev.8, v1→v2) |
| Document reference IDs | Sometimes substantive | Cosmetic when only ID suffix changed (RPT-001-A → RPT-001-B) |
| Annotations | Always cosmetic | Substantive (customer change instructions) |
| AI escalation threshold | Fixed 0.72 | Same (unchanged, configurable) |

**Classification rules added:**
```
Version/revision identifiers    → cosmetic (0.93 confidence)
Document reference IDs          → cosmetic (0.92 confidence)
Metadata dates (header/footer)  → cosmetic (0.88 confidence)
Annotations                     → substantive (0.85 confidence)
```

### Stage 8 — Deduplication & Assembly

| What | Before | After |
|---|---|---|
| Dedup passes | 1 (same-value same-page) | 4-pass comprehensive |
| OCR garbage | Not filtered | Removed (non-Latin clusters, garbled text) |
| Header/footer repeats | Each reported separately | Collapsed: 3+ pages → single cosmetic entry |
| Page numbers | Reported as material changes | Auto-filtered |

**4-pass deduplication (new):**
1. **OCR garbage removal** — garbled characters, non-Latin clusters, high symbol ratios
2. **Header/footer collapse** — same change on 3+ pages → single entry with note "(found on 12 pages)"
3. **Page number filtering** — "Page X of Y" patterns removed
4. **Same-value dedup** — identical before→after on same page → keep first

---

## PDF Parsing Improvements

### fast_parser.py (PyMuPDF)

| What | Before | After |
|---|---|---|
| Bounding boxes | PDF points (absolute) | Normalized 0-1 fractions |
| Header/footer detection | None | Zone-based: top 8% = header, bottom 5% = footer |
| Block types | `type` + `block_type` | Both set for compatibility |

### parser.py (Docling)

| What | Before | After |
|---|---|---|
| Bounding boxes | Docling points (absolute) | Normalized 0-1 fractions using page dimensions |

### Table Comparison

| What | Before | After |
|---|---|---|
| Cell comparison | Exact string match | Number-normalized ("2.0" = "2", "1,000" = "1000") |
| Output values | Normalized | Original raw values preserved for user display |

---

## Expected Accuracy Impact

Based on the test report analysis (506-entry Flash v1 report):

| Noise Source | Entries Before | Entries After | Reduction |
|---|---|---|---|
| Page misalignment (appendices) | ~300 | ~5 | 98% |
| Header/footer repeats (Rev.7→Rev.8 × 12) | ~40 | ~3 | 93% |
| OCR garbage | ~80 | 0 | 100% |
| Page number changes | ~24 | 0 | 100% |
| Character fragmentation | ~15 | ~5 | 67% |
| Same-value duplicates | ~8 | ~2 | 75% |
| **Total noise** | **~465** | **~15** | **97%** |
| **Genuine differences** | **~41** | **~41** | **0% loss** |
| **Final report size** | **506** | **~56** | **89% reduction** |

---

## Configuration Reference

All thresholds are in `app/config.py` or hardcoded constants:

| Setting | Default | Location | Purpose |
|---|---|---|---|
| `DOCDIFF_CONFIDENCE_THRESHOLD` | 0.75 | config.py | Below this → needs verification |
| `DOCDIFF_AUTO_CONFIRM_THRESHOLD` | 0.95 | config.py | Above this → auto-confirmed |
| `DOCDIFF_PAGE_RENDER_DPI` | 250 | config.py | Default DPI (overridden by adaptive) |
| Page alignment threshold | 0.3 | stage_5 | Minimum page similarity to match |
| Title match threshold | 0.7 | stage_5 | Section title alignment |
| Table match threshold | 0.5 | stage_5 | Table structural alignment |
| Text match threshold | 0.4 | stage_5 | Text block content alignment |
| Rule engine AI escalation | 0.72 | stage_7 | Below this → AI classifies |
| Header/footer collapse | 3+ pages | stage_8 | Minimum pages for collapse |
| Header zone | top 8% | fast_parser | Y < 0.08 = header |
| Footer zone | bottom 5% | fast_parser | Y > 0.95 = footer |

---

## Best Practices for Accurate Results

1. **Use the Pro model** (Claude Sonnet 4.6 or Gemini 3.1 Pro) for production comparisons — Flash models produce more noise
2. **Upload matching scope** — if Version A has appendices, either include them in Version B or exclude from both
3. **Born-digital PDFs preferred** — direct text extraction is always more accurate than OCR
4. **Reprocess after pipeline updates** — old jobs use old extraction logic; delete and re-upload for improved accuracy
5. **Review auto-confirmed items** — high-confidence items are usually correct but can be overridden
6. **Use the "Full Text" toggle** — expand differences to see complete before/after context
