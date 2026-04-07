# Company Bulk Upload Upgrade — Design Spec

**Date:** 2026-04-06
**Status:** Approved
**Scope:** Backend (3 endpoints) + Web UI (rewrite existing modal)

---

## Overview

Upgrade the existing client-side company bulk upload to a backend-driven system matching the employee bulk import pattern. Move template generation, parsing, and validation from the browser to 3 new backend endpoints. Replace the 1400-line client-side `bulk-upload-utils.ts` with thin API calls. Add professional Excel styling (indigo headers, dropdown validations, reference sheets, gray italic example rows).

---

## Backend Endpoints

### 1. `GET /platform/tenants/bulk/template`

Download a professionally styled Excel template for bulk company onboarding.

- **Auth:** Super admin only (`SUPER_ADMIN` role check via existing route guard)
- **Response:** `application/vnd.openxmlformats-officedocument.spreadsheetml.sheet`
- **Filename:** `Company_Onboarding_Template.xlsx`

#### Data Sheets (15 sheets — one per onboarding section)

Each sheet has:
- Row 1: Headers with indigo fill (#4F46E5), white bold font (reuse `HEADER_FILL`, `HEADER_FONT` from excel-exporter)
- Row 2: Example data row (italic, gray color #9CA3AF) with note on first cell: "Example row — delete before uploading"
- Dropdown validations on enum columns (rows 3-102, supporting up to 100 companies)
- Auto-sized column widths

| # | Sheet Name | Key Columns | Dropdown Validations |
|---|-----------|-------------|---------------------|
| 1 | Company Identity | displayName*, legalName*, slug*, businessType*, industry*, companyCode*, emailDomain*, shortName, incorporationDate*, employeeCount, cin, website, status* | businessType (from BUSINESS_TYPES), industry (from INDUSTRIES), status (Draft/Pilot/Active/Inactive) |
| 2 | Statutory | displayName*, pan*, tan, gstin, pfRegNo, esiCode, ptReg, lwfrNo, rocState | rocState (from INDIAN_STATES) |
| 3 | Address | displayName*, regLine1*, regCity*, regState*, regCountry*, regPin*, regLine2, regDistrict, regStdCode, sameAsRegistered, corp* fields | regState/corpState (from INDIAN_STATES), sameAsRegistered (Yes/No), regCountry/corpCountry (India) |
| 4 | Fiscal | displayName*, fyType*, weekStart*, workingDays*, payrollFreq, cutoffDay, disbursementDay, timezone | fyType (apr-mar/custom), weekStart (days), timezone (from ALLOWED_TIMEZONES), cutoffDay (from CUTOFF_DAYS), disbursementDay (from DISBURSEMENT_DAYS) |
| 5 | Preferences | displayName*, currency, language, dateFormat, indiaCompliance, mobileApp, webApp, systemApp, bankIntegration, emailNotif | All boolean fields (Yes/No), dateFormat (DD/MM/YYYY, MM/DD/YYYY, YYYY-MM-DD) |
| 6 | Endpoint | displayName*, endpointType, customBaseUrl | endpointType (default/custom) |
| 7 | Strategy | displayName*, multiLocationMode, locationConfig | multiLocationMode (Yes/No), locationConfig (common/per-location) |
| 8 | Locations | displayName*, name*, code*, facilityType*, addressLine1*, city*, + geo/contact fields | facilityType (from FACILITY_TYPES), isHQ (Yes/No), geoEnabled (Yes/No), status (Active/Inactive) |
| 9 | Modules & Pricing | displayName*, locationName, selectedModules*, userTier*, billingType*, customUserLimit, customTierPrice, trialDays | selectedModules (from MODULE_CATALOGUE), userTier (from USER_TIERS), billingType (from BILLING_TYPES) |
| 10 | Contacts | displayName*, name*, type, designation, department, email, countryCode, mobile, linkedin | type (from CONTACT_TYPES) |
| 11 | Shifts | displayName*, dayStartTime*, dayEndTime*, weeklyOffs, shiftName*, shiftFrom*, shiftTo*, noShuffle | noShuffle (Yes/No) |
| 12 | No Series | displayName*, code*, linkedScreen*, prefix, suffix, numberCount, startNumber, description | linkedScreen (from NO_SERIES_SCREENS/LINKED_SCREENS) |
| 13 | IOT Reasons | displayName*, reasonType*, reason*, description, department, planned, duration | reasonType (from IOT_REASON_TYPES), planned (Yes/No) |
| 14 | Controls | displayName*, ncEditMode, loadUnload, cycleTime, payrollLock, leaveCarryForward, overtimeApproval, mfa | All fields (Yes/No) |
| 15 | Users | displayName*, fullName*, username*, role*, email*, password, mobile, department | role (Company Admin/HR Manager/...) |

#### Reference Sheets (5 sheets — read-only with sheet protection)

| # | Sheet Name | Columns | Source |
|---|-----------|---------|--------|
| 16 | Indian States | Name | INDIAN_STATES constant |
| 17 | Business Types & Industries | Business Types, Industries (side by side) | BUSINESS_TYPES, INDUSTRIES constants |
| 18 | Facility Types | Name | FACILITY_TYPES constant |
| 19 | Module Catalogue | ID, Name, Description | MODULE_CATALOGUE constant |
| 20 | Linked Screens | Value, Label, Module | NO_SERIES_SCREENS/LINKED_SCREENS constant |

Reference sheets styled with: indigo header, alternating row fills, sheet protection.

#### Instructions Sheet (#21)

- 3 columns: Sheet, Column, Description
- Lists all required/optional fields across all 15 data sheets
- Notes section: delete example rows, Display Name must match across sheets, dates in YYYY-MM-DD, comma-separated for multi-values (workingDays, weeklyOffs, selectedModules)

---

### 2. `POST /platform/tenants/bulk/validate`

Upload Excel file and validate all companies without creating any records.

- **Auth:** Super admin only
- **Content-Type:** `multipart/form-data`
- **Body:** `file` (xlsx, max 10MB)
- **Response:**

```json
{
  "success": true,
  "data": {
    "totalCompanies": 5,
    "validCount": 4,
    "errorCount": 1,
    "companies": [
      {
        "name": "Apex Manufacturing",
        "rowIndex": 0,
        "valid": true,
        "payload": { /* full onboardTenant-shaped payload */ }
      },
      {
        "name": "Beta Corp",
        "rowIndex": 1,
        "valid": false,
        "errors": [
          { "sheet": "Company Identity", "field": "companyCode", "message": "Company code 'BETA-001' already exists" },
          { "sheet": "Address", "field": "regPin", "message": "PIN code must be 6 digits" }
        ]
      }
    ]
  }
}
```

#### Validation Rules

**File-level:**
- Must be .xlsx format, max 10MB
- Must have "Company Identity" sheet with at least 1 data row (after example row)
- Max 50 companies per upload

**Per-company validation (same rules as current `bulk-upload-utils.ts`):**
- Required fields present and non-empty
- Email format validation
- PIN code: 6 digits
- Slug: lowercase, alphanumeric + hyphens, not in reserved list
- Company code format
- Date format: YYYY-MM-DD
- Enum values match allowed lists
- Cross-sheet consistency: Display Name must match Company Identity sheet
- If `sameAsRegistered = No`, corporate address fields required
- If `endpointType = custom`, customBaseUrl required
- If `locationConfig = per-location`, per-location modules required

**Database uniqueness checks (new — not in current client-side version):**
- Company code unique across platform
- Slug unique across platform
- User emails unique across platform

**Cross-company checks (within file):**
- No duplicate company codes
- No duplicate slugs
- No duplicate user emails

**Payload assembly:**
- Validated data assembled into the exact `OnboardTenantPayload` shape expected by `tenantService.onboardTenant()`
- Multi-row sheets (Locations, Contacts, Shifts, Users, etc.) grouped by Display Name
- Boolean fields parsed from Yes/No strings
- Comma-separated fields parsed into arrays (workingDays, weeklyOffs, selectedModules)

---

### 3. `POST /platform/tenants/bulk/import`

Create companies from previously validated payloads.

- **Auth:** Super admin only
- **Content-Type:** `application/json`
- **Body:**

```json
{
  "companies": [
    { "name": "Apex Manufacturing", "payload": { /* OnboardTenantPayload */ } }
  ]
}
```

- **Response:**

```json
{
  "success": true,
  "data": {
    "total": 4,
    "successCount": 3,
    "failureCount": 1,
    "results": [
      { "name": "Apex Manufacturing", "success": true, "companyId": "clxyz..." },
      { "name": "Gamma Ltd", "success": false, "error": "Company code already exists" }
    ]
  }
}
```

#### Import Logic
- For each validated company, calls `tenantService.onboardTenant(payload)` (the same method used by the single-company wizard)
- Each company in its own try/catch for failure isolation
- Sequential processing (each company creates a PostgreSQL schema — cannot parallelize)

---

## Web UI Changes

### Rewrite: `BulkUploadModal.tsx`

Replace the current 4-stage modal with a 3-step modal matching the employee bulk import pattern:

**Step 1: Download Template**
- "Download Template" button → calls `GET /platform/tenants/bulk/template`
- Description text explaining the 15-sheet structure
- "Next" button

**Step 2: Upload & Validate**
- File dropzone (accepts .xlsx, max 10MB)
- "Validate" button → calls `POST /platform/tenants/bulk/validate`
- Results display:
  - Summary: "{validCount} valid, {errorCount} errors out of {totalCompanies} companies"
  - Company cards with expandable error lists (sheet + field + message)
  - Valid companies show green check, invalid show red X
- "Re-upload" button, "Import {validCount} Valid Companies" button

**Step 3: Import Results**
- Loading: "Creating companies... ({current}/{total})"
- Summary cards: success (green), failed (red)
- Results list: Company name, Company ID (if success), Status
- "Done" button closes modal and refreshes company list

### Replace: `bulk-upload-utils.ts`

Replace the 1400-line client-side parsing/validation logic with thin API helper functions:

```typescript
// Template download
export async function downloadCompanyTemplate(): Promise<void>

// Type for validation results (matching backend response)
export interface BulkCompanyValidationResult { ... }
export interface BulkCompanyImportResult { ... }
```

### Modify: API hooks

Add to `use-tenant-queries.ts` or create new hooks file:
- `useBulkValidateCompanies()` — mutation hook for validate endpoint
- `useBulkImportCompanies()` — mutation hook for import endpoint (invalidates company list on success)

---

## Files to Create/Modify

### Backend

| Action | File | Purpose |
|--------|------|---------|
| Create | `src/core/tenant/bulk-onboard.validators.ts` | Column definitions for all 15 sheets, enum maps, Zod schemas |
| Create | `src/core/tenant/bulk-onboard.service.ts` | Template generation, Excel parsing, validation, payload assembly |
| Create | `src/core/tenant/bulk-onboard.controller.ts` | 3 endpoint handlers with multer |
| Modify | `src/core/tenant/tenant.routes.ts` | Mount 3 bulk routes |

### Web

| Action | File | Purpose |
|--------|------|---------|
| Rewrite | `src/features/super-admin/bulk-upload/BulkUploadModal.tsx` | 3-step modal using backend APIs |
| Rewrite | `src/features/super-admin/bulk-upload/bulk-upload-utils.ts` | Replace with types + API helpers |
| Modify | `src/features/super-admin/api/use-tenant-queries.ts` | Add bulk validate/import mutations |

---

## Constants Reuse

The backend service will import the same constants currently used by the frontend:
- `BUSINESS_TYPES`, `INDUSTRIES`, `COMPANY_STATUSES`, `INDIAN_STATES`
- `CUTOFF_DAYS`, `DISBURSEMENT_DAYS`, `DAYS_OF_WEEK`
- `FACILITY_TYPES`, `CONTACT_TYPES`
- `NO_SERIES_SCREENS`, `IOT_REASON_TYPES`
- `MODULE_CATALOGUE`, `USER_TIERS`, `BILLING_TYPES`
- `ALLOWED_TIMEZONES`

These constants need to be defined in the backend (they may already exist in the onboarding constants or will be co-located with the bulk validators).

---

## Constraints

- Max file size: 10MB
- Max companies per upload: 50
- Only .xlsx format
- Sequential company creation (PostgreSQL schema creation cannot be parallelized)
- Web-only (no mobile UI needed)
