# Company Bulk Upload Upgrade — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the client-side company bulk upload with backend-driven endpoints (template download, validate, import) matching the employee bulk import pattern — professional Excel with indigo headers, dropdown validations, reference sheets.

**Architecture:** Three new backend endpoints under `/platform/tenants/bulk/*`. Template generation uses ExcelJS with 15 data sheets + 5 reference sheets + instructions. Validation parses multi-sheet Excel, links rows by Display Name, resolves enums, checks DB uniqueness. Import calls existing `tenantService.onboardTenant()` per company. Web modal rewritten to use backend APIs. Old client-side parsing logic deleted.

**Tech Stack:** ExcelJS 4.4.0 (already installed), Multer 1.4.5 (already installed), Zod

**Spec:** `docs/superpowers/specs/2026-04-06-company-bulk-upload-upgrade-design.md`

---

## File Structure

### Backend (avy-erp-backend)

| Action | File | Responsibility |
|--------|------|----------------|
| Create | `src/core/tenant/bulk-onboard.constants.ts` | All enum constants needed for template generation and validation (mirrors frontend constants.ts) |
| Create | `src/core/tenant/bulk-onboard.validators.ts` | Column definitions for all 15 sheets, Zod schemas |
| Create | `src/core/tenant/bulk-onboard.service.ts` | Template generation (21 sheets), Excel parsing, validation, payload assembly, import orchestration |
| Create | `src/core/tenant/bulk-onboard.controller.ts` | 3 endpoint handlers with multer middleware |
| Modify | `src/core/tenant/tenant.routes.ts` | Mount 3 bulk routes |

### Web (web-system-app)

| Action | File | Responsibility |
|--------|------|----------------|
| Modify | `src/lib/api/tenant.ts` | Add 3 bulk API functions (downloadBulkTemplate, bulkValidate, bulkImport) |
| Modify | `src/features/super-admin/api/use-tenant-queries.ts` | Add `useBulkValidateCompanies()` and `useBulkImportCompanies()` mutation hooks |
| Rewrite | `src/features/super-admin/bulk-upload/BulkUploadModal.tsx` | 3-step modal using backend APIs (same pattern as employee BulkEmployeeImportModal) |
| Rewrite | `src/features/super-admin/bulk-upload/bulk-upload-utils.ts` | Replace 1400 lines with thin types/exports |

---

## Task 1: Backend — Bulk Onboard Constants

**Files:**
- Create: `avy-erp-backend/src/core/tenant/bulk-onboard.constants.ts`

- [ ] **Step 1: Create constants file with all enum values needed for template generation**

This file mirrors the frontend `constants.ts` values that are needed for Excel dropdown validations and validation logic. Include:

- `BUSINESS_TYPES`: string[] — 'Private Limited (Pvt. Ltd.)', 'Public Limited', 'Partnership', 'Proprietorship', 'Others'
- `INDUSTRIES`: string[] — 'IT', 'Manufacturing', 'BFSI', 'Healthcare', 'Retail', 'Automotive', 'Pharma', 'Education', 'Steel & Metal', 'Textiles', 'Plastics', 'Electronics', 'Food Processing', 'Heavy Engineering', 'CNC Machining', 'Chemicals', 'Logistics', 'Construction', 'Real Estate', 'E-Commerce', 'Other'
- `COMPANY_STATUSES`: string[] — 'Draft', 'Pilot', 'Active', 'Inactive'
- `INDIAN_STATES`: string[] — all 33 states/UTs + 'Others'
- `FY_TYPES`: string[] — 'apr-mar', 'custom'
- `WEEK_STARTS`: string[] — 'Monday', 'Sunday', etc.
- `DAYS_OF_WEEK`: string[] — Mon through Sun
- `CUTOFF_DAYS`: string[] — '1st', '5th', ..., 'Last Working Day', 'Last Day of Month'
- `DISBURSEMENT_DAYS`: string[] — '1st', '3rd', ..., 'Last Day', 'Same Day as Cutoff'
- `TIMEZONES`: string[] — 'IST UTC+5:30', 'UTC+0', 'EST UTC-5', etc. (same as frontend ALLOWED_TIMEZONES)
- `CURRENCIES`: string[] — 'INR — ₹', 'USD — $', etc.
- `LANGUAGES`: string[] — 'English', 'Hindi', etc.
- `DATE_FORMATS`: string[] — 'DD/MM/YYYY', 'MM/DD/YYYY', 'YYYY-MM-DD'
- `FACILITY_TYPES`: string[] — 'Head Office', 'Regional Office', ..., 'Custom...'
- `FACILITY_STATUSES`: string[] — 'Active', 'Inactive', 'Under Construction'
- `CONTACT_TYPES`: string[] — 'Primary', 'HR Contact', etc.
- `MODULE_CATALOGUE`: { id: string; name: string; description: string }[] — hr, security, production, etc. (10 modules)
- `USER_TIERS`: { key: string; label: string }[] — starter, growth, scale, enterprise, custom
- `BILLING_TYPES`: { key: string; label: string }[] — monthly, annual, one_time_amc
- `IOT_REASON_TYPES`: string[] — 'Machine Idle', 'Machine Alarm'
- `NO_SERIES_SCREENS`: { value: string; label: string }[] — Employee, Leave Management, Payroll, etc. (20 screens)
- `RESERVED_SLUGS`: Set<string> — admin, www, api, app, staging, dev, test, demo, etc.
- `YES_NO_MAP`: Record<string, boolean> — yes/y/1/true → true, no/n/0/false → false (same as employee bulk)

All values must exactly match the frontend `web-system-app/src/features/super-admin/tenant-onboarding/constants.ts` to ensure consistency.

- [ ] **Step 2: Verify compiles**

Run: `cd avy-erp-backend && npx tsc --noEmit 2>&1 | head -5`

- [ ] **Step 3: Commit**

```bash
git add src/core/tenant/bulk-onboard.constants.ts
git commit -m "feat(bulk-onboard): add backend constants mirroring frontend onboarding enums"
```

---

## Task 2: Backend — Bulk Onboard Validators

**Files:**
- Create: `avy-erp-backend/src/core/tenant/bulk-onboard.validators.ts`

- [ ] **Step 1: Create column definitions for all 15 data sheets**

Each sheet needs an array of `{ header: string; key: string; required: boolean }` matching the exact columns from the current frontend `bulk-upload-utils.ts`. Use the SAME header names and key names so the template is backwards-compatible.

Define these column definition arrays:
1. `IDENTITY_COLS` — 13 columns (displayName*, legalName*, slug*, businessType*, industry*, companyCode*, shortName, incorporationDate*, employees, cin, website, emailDomain*, status*)
2. `STATUTORY_COLS` — 9 columns (displayName*, pan*, tan, gstin, pfRegNo, esiCode, ptReg, lwfrNo, rocState)
3. `ADDRESS_COLS` — 18 columns (displayName*, regLine1*, regCity*, regState*, regCountry*, regPin*, regLine2, regDistrict, regStdCode, sameAsRegistered, corp* x8)
4. `FISCAL_COLS` — 10 columns (displayName*, fyType*, weekStart*, workingDays*, payrollFreq, cutoffDay, disbursementDay, timezone, fyCustomStartMonth, fyCustomEndMonth)
5. `PREFERENCES_COLS` — 10 columns (displayName*, currency, language, dateFormat, indiaCompliance, mobileApp, webApp, systemApp, bankIntegration, emailNotif)
6. `ENDPOINT_COLS` — 3 columns (displayName*, endpointType, customBaseUrl)
7. `STRATEGY_COLS` — 3 columns (displayName*, multiLocationMode, locationConfig)
8. `LOCATIONS_COLS` — 20 columns (displayName*, name*, code*, facilityType*, status, isHQ, gstin, addressLine1*, addressLine2, city*, district, state, pin, contactName, contactEmail, contactPhone, geoEnabled, geoLat, geoLng, geoRadius)
9. `MODULES_COLS` — 8 columns (displayName*, locationName, selectedModules*, userTier*, billingType*, customUserLimit, customTierPrice, trialDays)
10. `CONTACTS_COLS` — 9 columns (displayName*, name*, type, designation, department, email, countryCode, mobile, linkedin)
11. `SHIFTS_COLS` — 8 columns (displayName*, dayStartTime*, dayEndTime*, weeklyOffs, shiftName*, shiftFrom*, shiftTo*, noShuffle)
12. `NO_SERIES_COLS` — 8 columns (displayName*, code*, linkedScreen*, description, prefix, suffix, numberCount, startNumber)
13. `IOT_REASONS_COLS` — 7 columns (displayName*, reasonType*, reason*, description, department, planned, duration)
14. `CONTROLS_COLS` — 8 columns (displayName*, ncEditMode, loadUnload, cycleTime, payrollLock, leaveCarryForward, overtimeApproval, mfa)
15. `USERS_COLS` — 8 columns (displayName*, fullName*, username*, role*, email*, password, mobile, department)

Also define `ALL_SHEET_DEFS`: array of `{ name: string; cols: ColDef[] }` mapping sheet names to their column definitions.

And `bulkOnboardImportBodySchema`: Zod schema for import body `{ companies: [{ name: string, payload: any }] }`.

- [ ] **Step 2: Verify compiles**

Run: `cd avy-erp-backend && npx tsc --noEmit 2>&1 | head -5`

- [ ] **Step 3: Commit**

```bash
git add src/core/tenant/bulk-onboard.validators.ts
git commit -m "feat(bulk-onboard): add column definitions and Zod schemas for 15-sheet bulk upload"
```

---

## Task 3: Backend — Bulk Onboard Service

**Files:**
- Create: `avy-erp-backend/src/core/tenant/bulk-onboard.service.ts`

This is the largest task. The service has 3 methods:

- [ ] **Step 1: Create the service class with `generateTemplate()` method**

**Imports (relative paths — NOT @/ aliases):**
- `import * as ExcelJS from 'exceljs'`
- `import { platformPrisma } from '../../config/database'`
- `import { logger } from '../../config/logger'`
- `import { ApiError } from '../../shared/errors'`
- `import { HEADER_FILL, HEADER_FONT, ALT_ROW_FILL } from '../../modules/hr/analytics/exports/excel-exporter'`
- `import { ALL_SHEET_DEFS, bulkOnboardImportBodySchema } from './bulk-onboard.validators'`
- `import * as C from './bulk-onboard.constants'`
- `import { tenantService } from './tenant.service'`

**`generateTemplate()` method:**
- Creates workbook with 21 sheets (15 data + 5 reference + 1 instructions)
- For each of the 15 data sheets:
  - Row 1: headers with HEADER_FILL + HEADER_FONT, frozen pane
  - Row 2: example "Apex Manufacturing" data (gray italic) with cell A note
  - Column widths: auto-sized from header length (min 18)
  - Dropdown validations on enum columns (rows 3-102):
    - Company Identity: businessType (BUSINESS_TYPES), industry (INDUSTRIES), status (COMPANY_STATUSES)
    - Statutory: rocState (INDIAN_STATES)
    - Address: regState/corpState (INDIAN_STATES), sameAsRegistered (Yes/No)
    - Fiscal: fyType (FY_TYPES), weekStart (WEEK_STARTS), timezone (TIMEZONES), cutoffDay (CUTOFF_DAYS), disbursementDay (DISBURSEMENT_DAYS)
    - Preferences: all boolean fields (Yes/No), dateFormat (DATE_FORMATS)
    - Endpoint: endpointType (default/custom)
    - Strategy: multiLocationMode (Yes/No), locationConfig (common/per-location)
    - Locations: facilityType (FACILITY_TYPES), isHQ (Yes/No), geoEnabled (Yes/No), status (FACILITY_STATUSES)
    - Modules: selectedModules uses MODULE_CATALOGUE ids joined, userTier (USER_TIERS keys), billingType (BILLING_TYPES keys)
    - Contacts: type (CONTACT_TYPES)
    - Shifts: noShuffle (Yes/No)
    - No Series: linkedScreen (NO_SERIES_SCREENS values)
    - IOT Reasons: reasonType (IOT_REASON_TYPES), planned (Yes/No)
    - Controls: all fields (Yes/No)
    - Users: role (Company Admin, HR Manager, Plant Manager, Employee)

- 5 reference sheets (same pattern as employee bulk import — addRefSheet helper):
  - "Indian States" — Name column
  - "Business Types & Industries" — two columns side by side
  - "Facility Types" — Name column
  - "Module Catalogue" — ID, Name, Description
  - "Linked Screens" — Value, Label columns

- 1 Instructions sheet: Sheet name, Column name, Required (Yes/No), Description for every column across all 15 sheets

**Sample data:** Use "Apex Manufacturing" as the example company across all sheets (same values as current frontend `bulk-upload-utils.ts` sample data).

- [ ] **Step 2: Add `validateUpload()` method**

Parses uploaded Excel and validates each company:

1. Load workbook from buffer
2. For each data sheet, build header→column map from row 1
3. Read Company Identity sheet to get list of company display names (skip example row)
4. For each company (by displayName):
   - Extract data from all 15 sheets (rows matching that displayName)
   - Parse boolean fields via YES_NO_MAP
   - Parse comma-separated fields (workingDays, weeklyOffs, selectedModules) into arrays
   - Validate required fields per sheet
   - Validate enum values against constants (businessType in BUSINESS_TYPES, etc.)
   - Validate formats: email, PIN (6 digits), slug (lowercase alphanumeric + hyphens), dates (YYYY-MM-DD)
   - Check slug not in RESERVED_SLUGS
   - Check cross-sheet consistency (all sheets reference same displayName)
   - If sameAsRegistered = No, validate corporate address fields present
   - If endpointType = custom, validate customBaseUrl present
5. DB uniqueness checks:
   - companyCode unique (query platformPrisma.company)
   - slug unique (query platformPrisma.tenant)
   - User emails unique (query platformPrisma.user)
6. Cross-company checks within file: no duplicate companyCodes, slugs, emails
7. Assemble validated data into `OnboardTenantPayload` shape (matching `tenantService.onboardTenant()` input):
   - identity: { displayName, legalName, slug, businessType, industry, companyCode, shortName, incorporationDate, employeeCount, cin, website, emailDomain, wizardStatus }
   - statutory: { pan, tan, gstin, pfRegNo, esiCode, ptReg, lwfrNo, rocState }
   - address: { registered: { line1, line2, city, district, state, pin, country, stdCode }, sameAsRegistered, corporate?: {...} }
   - fiscal: { fyType, fyCustomStartMonth, fyCustomEndMonth, payrollFreq, cutoffDay, disbursementDay, weekStart, timezone, workingDays }
   - preferences: { currency, language, dateFormat, indiaCompliance, mobileApp, webApp, systemApp, bankIntegration, emailNotif }
   - endpoint: { endpointType, customBaseUrl }
   - strategy: { multiLocationMode, locationConfig }
   - locations: [{ name, code, facilityType, isHQ, addressLine1, ... }]
   - commercial: { selectedModuleIds, userTier, billingType, customUserLimit, customTierPrice, trialDays }
   - contacts: [{ name, designation, department, type, email, countryCode, mobile, linkedin }]
   - shifts: { dayStartTime, dayEndTime, weeklyOffs, items: [{ name, fromTime, toTime, noShuffle }] }
   - noSeries: [{ code, linkedScreen, description, prefix, suffix, numberCount, startNumber }]
   - iotReasons: [{ reasonType, reason, description, department, planned, duration }]
   - controls: { ncEditMode, loadUnload, cycleTime, payrollLock, leaveCarryForward, overtimeApproval, mfa }
   - users: [{ fullName, username, password, role, email, mobile, department }]

8. Return: `{ totalCompanies, validCount, errorCount, companies: [{ name, rowIndex, valid, payload?, errors? }] }`
   - errors shape: `{ sheet: string, field: string, message: string }[]`

- [ ] **Step 3: Add `importCompanies()` method**

For each validated company, calls `tenantService.onboardTenant(payload)`:
- Each company in its own try/catch for failure isolation
- Sequential processing (each creates a PostgreSQL schema)
- Return: `{ total, successCount, failureCount, results: [{ name, success, companyId?, error? }] }`

- [ ] **Step 4: Verify compiles**

Run: `cd avy-erp-backend && npx tsc --noEmit 2>&1 | head -10`

- [ ] **Step 5: Commit**

```bash
git add src/core/tenant/bulk-onboard.service.ts
git commit -m "feat(bulk-onboard): add service with template generation, validation, and import"
```

---

## Task 4: Backend — Controller & Routes

**Files:**
- Create: `avy-erp-backend/src/core/tenant/bulk-onboard.controller.ts`
- Modify: `avy-erp-backend/src/core/tenant/tenant.routes.ts`

- [ ] **Step 1: Create the controller**

Same pattern as employee bulk-import.controller.ts:

```typescript
import { Request, Response } from 'express';
import multer from 'multer';
import { asyncHandler } from '../../middleware/error.middleware';
import { ApiError } from '../../shared/errors';
import { createSuccessResponse } from '../../shared/utils';
import { bulkOnboardService } from './bulk-onboard.service';
import { bulkOnboardImportBodySchema } from './bulk-onboard.validators';

const upload = multer({
  storage: multer.memoryStorage(),
  limits: { fileSize: 10 * 1024 * 1024 },
  fileFilter: (_req, file, cb) => {
    if (file.mimetype.includes('spreadsheet') || file.originalname.endsWith('.xlsx')) {
      cb(null, true);
    } else {
      cb(new Error('Only .xlsx files are accepted'));
    }
  },
});

export const bulkOnboardUploadMiddleware = upload.single('file');

class BulkOnboardController {
  downloadTemplate = asyncHandler(async (_req: Request, res: Response) => {
    const workbook = await bulkOnboardService.generateTemplate();
    res.setHeader('Content-Type', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet');
    res.setHeader('Content-Disposition', 'attachment; filename="Company_Onboarding_Template.xlsx"');
    await workbook.xlsx.write(res);
    res.end();
  });

  validateUpload = asyncHandler(async (req: Request, res: Response) => {
    if (!req.file) throw ApiError.badRequest('No file uploaded');
    const result = await bulkOnboardService.validateUpload(req.file.buffer);
    res.json(createSuccessResponse(result, 'Validation complete'));
  });

  confirmImport = asyncHandler(async (req: Request, res: Response) => {
    const parsed = bulkOnboardImportBodySchema.safeParse(req.body);
    if (!parsed.success) throw ApiError.badRequest(parsed.error.errors.map(e => e.message).join(', '));
    const result = await bulkOnboardService.importCompanies(parsed.data.companies);
    res.json(createSuccessResponse(result, `Import complete: ${result.successCount} created, ${result.failureCount} failed`));
  });
}

export const bulkOnboardController = new BulkOnboardController();
```

- [ ] **Step 2: Mount routes in tenant.routes.ts**

Add AFTER the `router.use(requirePermissions(['platform:admin']))` line and BEFORE existing routes:

```typescript
import { bulkOnboardController, bulkOnboardUploadMiddleware } from './bulk-onboard.controller';

// ── Bulk Onboarding ──────────────────────────────────────────────────
router.get('/bulk/template', bulkOnboardController.downloadTemplate);
router.post('/bulk/validate', bulkOnboardUploadMiddleware, bulkOnboardController.validateUpload);
router.post('/bulk/import', bulkOnboardController.confirmImport);
```

Note: All tenant routes already have `requirePermissions(['platform:admin'])` from `router.use()` on line 8 — no additional permission guard needed.

- [ ] **Step 3: Verify compiles**

Run: `cd avy-erp-backend && npx tsc --noEmit 2>&1 | head -10`

- [ ] **Step 4: Commit**

```bash
git add src/core/tenant/bulk-onboard.controller.ts src/core/tenant/tenant.routes.ts
git commit -m "feat(bulk-onboard): add controller with multer and mount bulk routes"
```

---

## Task 5: Web — API Layer Updates

**Files:**
- Modify: `web-system-app/src/lib/api/tenant.ts`
- Modify: `web-system-app/src/features/super-admin/api/use-tenant-queries.ts`

- [ ] **Step 1: Add bulk API functions to tenant.ts**

Read the file first to understand the existing pattern. Add 3 new functions to the `tenantApi` object:

```typescript
// Bulk Onboarding
downloadBulkTemplate: async (): Promise<Blob> => {
    const response = await client.get('/platform/tenants/bulk/template', { responseType: 'blob' });
    return response.data;
},

bulkValidate: async (file: File) => {
    const formData = new FormData();
    formData.append('file', file);
    const response = await client.post('/platform/tenants/bulk/validate', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
    });
    return response.data;
},

bulkImport: async (companies: { name: string; payload: any }[]) => {
    const response = await client.post('/platform/tenants/bulk/import', { companies });
    return response.data;
},
```

- [ ] **Step 2: Add mutation hooks to use-tenant-queries.ts**

```typescript
// ── Bulk Onboarding ──

export async function downloadCompanyTemplate() {
    const blob = await tenantApi.downloadBulkTemplate();
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'Company_Onboarding_Template.xlsx';
    document.body.appendChild(a);
    a.click();
    window.URL.revokeObjectURL(url);
    document.body.removeChild(a);
}

export function useBulkValidateCompanies() {
    return useMutation({
        mutationFn: (file: File) => tenantApi.bulkValidate(file),
    });
}

export function useBulkImportCompanies() {
    const queryClient = useQueryClient();
    return useMutation({
        mutationFn: (companies: { name: string; payload: any }[]) =>
            tenantApi.bulkImport(companies),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: tenantKeys.all });
        },
    });
}
```

- [ ] **Step 3: Verify compiles**

Run: `cd web-system-app && npx tsc --noEmit 2>&1 | head -10`

- [ ] **Step 4: Commit**

```bash
cd web-system-app && git add src/lib/api/tenant.ts src/features/super-admin/api/use-tenant-queries.ts
git commit -m "feat(bulk-onboard): add web API hooks for bulk template, validate, and import"
```

---

## Task 6: Web — Rewrite Bulk Upload Modal

**Files:**
- Rewrite: `web-system-app/src/features/super-admin/bulk-upload/BulkUploadModal.tsx`
- Rewrite: `web-system-app/src/features/super-admin/bulk-upload/bulk-upload-utils.ts`

- [ ] **Step 1: Replace bulk-upload-utils.ts with thin types**

Delete the entire 1400-line contents and replace with just type exports:

```typescript
// ============================================================
// Bulk Upload — Types (logic moved to backend)
// ============================================================

export interface BulkCompanyError {
    sheet: string;
    field: string;
    message: string;
}

export interface ValidatedCompany {
    name: string;
    rowIndex: number;
    valid: boolean;
    payload?: any;
    errors?: BulkCompanyError[];
}

export interface BulkValidationResult {
    totalCompanies: number;
    validCount: number;
    errorCount: number;
    companies: ValidatedCompany[];
}

export interface BulkImportResultItem {
    name: string;
    success: boolean;
    companyId?: string;
    error?: string;
}

export interface BulkImportResult {
    total: number;
    successCount: number;
    failureCount: number;
    results: BulkImportResultItem[];
}
```

- [ ] **Step 2: Rewrite BulkUploadModal.tsx**

Replace the entire file with a 3-step modal matching the employee `BulkEmployeeImportModal.tsx` pattern. Read the employee modal first for reference: `web-system-app/src/features/company-admin/hr/BulkEmployeeImportModal.tsx`

Key differences from employee modal:
- **No password field** — company bulk upload doesn't need a default password (users have their own passwords in the Users sheet)
- **Step 2 shows per-company results** (not per-row) — each company card shows name + expandable error list with sheet/field/message
- **Uses `downloadCompanyTemplate()`** from `@/features/super-admin/api/use-tenant-queries`
- **Uses `useBulkValidateCompanies()`** — accepts just a File (no password)
- **Uses `useBulkImportCompanies()`** — accepts array of `{ name, payload }`
- **Error display:** Each error shows `[Sheet] Field: message` format since errors span multiple sheets
- **Import results:** Shows company name + company ID (not employee ID)
- **Step indicator** and overall layout should match the employee modal exactly

**Props:** `{ onClose: () => void; onSuccess?: () => void }` — same as current

**Imports needed:**
```typescript
import { useState, useRef, useCallback } from 'react';
import { X, Upload, Download, FileSpreadsheet, CheckCircle2, AlertCircle, Loader2, ChevronDown, ChevronRight, Building2, RotateCcw } from 'lucide-react';
import { cn } from '@/lib/utils';
import { showApiError } from '@/lib/toast';
import { downloadCompanyTemplate, useBulkValidateCompanies, useBulkImportCompanies } from '@/features/super-admin/api/use-tenant-queries';
import type { ValidatedCompany, BulkValidationResult, BulkImportResult } from './bulk-upload-utils';
```

- [ ] **Step 3: Verify the CompanyListScreen.tsx still imports BulkUploadModal correctly**

Read `CompanyListScreen.tsx` to verify the import path and usage pattern hasn't changed. The existing code lazy-loads the modal — ensure the named export matches.

- [ ] **Step 4: Verify compiles**

Run: `cd web-system-app && npx tsc --noEmit 2>&1 | head -10`

- [ ] **Step 5: Commit**

```bash
cd web-system-app && git add src/features/super-admin/bulk-upload/BulkUploadModal.tsx src/features/super-admin/bulk-upload/bulk-upload-utils.ts
git commit -m "feat(bulk-onboard): rewrite bulk upload modal to use backend APIs, delete client-side parsing"
```

---

## Task 7: Cleanup — Remove Unused Dependencies

**Files:**
- Modify: `web-system-app/package.json`

- [ ] **Step 1: Check if `xlsx` package is used anywhere else in the web app**

Search for `import.*xlsx` or `from 'xlsx'` across the entire web app codebase. The old `bulk-upload-utils.ts` imported `xlsx` — if no other file uses it, remove it.

Run: `cd web-system-app && grep -r "from 'xlsx'" src/ --include="*.ts" --include="*.tsx" | grep -v node_modules`

If only the old bulk-upload-utils.ts used it (which is now rewritten), remove the package:

```bash
cd web-system-app && pnpm remove xlsx
```

Note: `exceljs` may still be imported in the old file — check if it's used elsewhere. If only the old bulk-upload-utils.ts used the frontend ExcelJS, it's no longer needed on the frontend (template generation moved to backend). But verify first.

- [ ] **Step 2: Verify no broken imports**

Run: `cd web-system-app && npx tsc --noEmit 2>&1 | head -10`

- [ ] **Step 3: Commit**

```bash
cd web-system-app && git add package.json pnpm-lock.yaml
git commit -m "chore: remove unused xlsx package from web app (bulk upload moved to backend)"
```

---

## Task 8: Cross-Codebase Consistency Review

- [ ] **Step 1: Verify backend template generates valid Excel**

Read the bulk-onboard.service.ts and confirm:
- All 15 sheet names match the column definition names in validators
- Dropdown values match the constants exactly
- Example data matches the current frontend sample data
- Reference sheets are properly populated

- [ ] **Step 2: Verify web modal correctly handles API responses**

Check:
- Modal unwraps response envelope correctly (`result.data` vs `result?.data`)
- Error display format matches backend error shape (`{ sheet, field, message }`)
- Valid companies' payloads are passed correctly to import endpoint
- Import results display company name and ID correctly

- [ ] **Step 3: Verify old client-side parsing is fully removed**

Confirm:
- `bulk-upload-utils.ts` no longer has `parseAndValidateBulkUpload()` or `downloadTemplate()` functions
- No remaining imports of `xlsx` package in the web codebase
- `BulkUploadModal.tsx` no longer imports the old parsing functions
- CompanyListScreen.tsx still renders the modal correctly

- [ ] **Step 4: Type-check all codebases**

```bash
cd avy-erp-backend && npx tsc --noEmit
cd web-system-app && npx tsc --noEmit
```

- [ ] **Step 5: Commit any fixes**

```bash
git add -A && git commit -m "fix(bulk-onboard): address consistency issues from review"
```
