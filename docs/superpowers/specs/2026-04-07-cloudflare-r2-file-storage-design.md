# Cloudflare R2 File Storage — Design Spec

## Goal

Replace all base64-encoded file storage with Cloudflare R2 object storage, using pre-signed URLs for secure upload/download. Create reusable upload infrastructure (backend service + frontend hooks) and migrate all existing base64 data to R2.

## Architecture

The system uses a **pre-signed URL flow**: frontends never send file data through the backend. Instead, they request a pre-signed upload URL, upload directly to R2, then send the resulting R2 object key back to the backend for persistence. For downloads, frontends request a pre-signed download URL (short-lived, ~1 hour) to display or download files.

All files are **private** — no public access. Every file access requires an authenticated API call to obtain a pre-signed URL.

**Tech Stack**: Cloudflare R2, `@aws-sdk/client-s3` + `@aws-sdk/s3-request-presigner` (Node.js), `fetch` (web), `expo-file-system` (mobile).

---

## R2 Bucket & Key Structure

### Single Bucket

```
Bucket: avy-erp-files (configurable via env)
```

### Key Format

```
{companyId}/{category}/{entityId}/{filename}
```

**Categories and key patterns:**

| Category | Key Pattern | Example |
|----------|-------------|---------|
| Company logo | `{companyId}/company/logo.{ext}` | `comp_123/company/logo.png` |
| Employee photo | `{companyId}/employees/{empId}/photo.{ext}` | `comp_123/employees/emp_456/photo.jpg` |
| Employee documents | `{companyId}/employees/{empId}/documents/{docId}.{ext}` | `comp_123/employees/emp_456/documents/doc_789.pdf` |
| Education certificates | `{companyId}/employees/{empId}/education/{eduId}.{ext}` | `comp_123/employees/emp_456/education/edu_101.pdf` |
| Previous employment docs | `{companyId}/employees/{empId}/prev-employment/{prevId}.{ext}` | `comp_123/employees/emp_456/prev-employment/prev_201.pdf` |
| Expense receipts | `{companyId}/expenses/{claimId}/{itemIdx}_{filename}` | `comp_123/expenses/exp_301/0_receipt.jpg` |
| Attendance photos | `{companyId}/attendance/{recordId}/{type}.{ext}` | `comp_123/attendance/att_401/checkin.jpg` |
| HR letters | `{companyId}/hr-letters/{letterId}.pdf` | `comp_123/hr-letters/ltr_501.pdf` |
| Recruitment docs | `{companyId}/recruitment/{candidateId}/{type}.{ext}` | `comp_123/recruitment/cand_601/resume.pdf` |
| Candidate documents | `{companyId}/recruitment/{candidateId}/documents/{docId}.{ext}` | `comp_123/recruitment/cand_601/documents/doc_701.pdf` |
| Training materials | `{companyId}/training/{materialId}.{ext}` | `comp_123/training/mat_801.pdf` |
| Training certificates | `{companyId}/training/certificates/{nominationId}.{ext}` | `comp_123/training/certificates/nom_901.pdf` |
| Payslips | `{companyId}/payroll/{payslipId}.pdf` | `comp_123/payroll/ps_1001.pdf` |
| Salary revision letters | `{companyId}/payroll/revisions/{revisionId}.pdf` | `comp_123/payroll/revisions/rev_1101.pdf` |
| Offboarding docs | `{companyId}/offboarding/{settlementId}/{type}.pdf` | `comp_123/offboarding/fnf_1201/settlement.pdf` |
| Transfer/promotion letters | `{companyId}/transfers/{transferId}.pdf` | `comp_123/transfers/tr_1301.pdf` |
| Policy documents | `{companyId}/policies/{policyId}.{ext}` | `comp_123/policies/pol_1401.pdf` |
| Billing invoices | `{companyId}/billing/{invoiceId}.pdf` | `comp_123/billing/inv_1501.pdf` |

### Content-Type Mapping

The backend derives `Content-Type` from file extension when generating pre-signed upload URLs:

| Extension | Content-Type |
|-----------|-------------|
| `.jpg`, `.jpeg` | `image/jpeg` |
| `.png` | `image/png` |
| `.gif` | `image/gif` |
| `.webp` | `image/webp` |
| `.pdf` | `application/pdf` |
| `.doc` | `application/msword` |
| `.docx` | `application/vnd.openxmlformats-officedocument.wordprocessingml.document` |
| `.xls` | `application/vnd.ms-excel` |
| `.xlsx` | `application/vnd.openxmlformats-officedocument.spreadsheetml.sheet` |

---

## Environment Variables

```bash
# R2 Connection
R2_ACCOUNT_ID=           # Cloudflare account ID
R2_ACCESS_KEY_ID=        # R2 API token access key
R2_SECRET_ACCESS_KEY=    # R2 API token secret key
R2_BUCKET_NAME=avy-erp-files
R2_ENDPOINT=             # https://{accountId}.r2.cloudflarestorage.com (auto-derived if R2_ACCOUNT_ID set)

# Pre-signed URL Expiry
R2_UPLOAD_URL_EXPIRY_SECONDS=300       # 5 minutes for upload URLs
R2_DOWNLOAD_URL_EXPIRY_SECONDS=3600    # 1 hour for download URLs

# File Size Limits (bytes)
UPLOAD_MAX_IMAGE_SIZE=5242880          # 5 MB (logos, photos, certificates)
UPLOAD_MAX_DOCUMENT_SIZE=10485760      # 10 MB (PDFs, documents, receipts)
```

---

## Backend Design

### New Files

```
avy-erp-backend/src/shared/services/
├── r2.service.ts              # R2 client singleton, pre-signed URL generation
└── upload.service.ts          # Business logic: key generation, validation, URL orchestration

avy-erp-backend/src/shared/constants/
└── upload.ts                  # File categories, size limits, allowed MIME types

avy-erp-backend/src/modules/upload/
├── upload.controller.ts       # API endpoints
├── upload.routes.ts           # Route definitions
└── upload.validators.ts       # Zod schemas for request validation

avy-erp-backend/scripts/
└── migrate-base64-to-r2.ts   # One-time migration script
```

### r2.service.ts — R2 Client Singleton

Responsibilities:
- Initialize `S3Client` with R2 credentials from env
- `getPresignedUploadUrl(key, contentType, expiresIn)` → pre-signed PUT URL
- `getPresignedDownloadUrl(key, expiresIn)` → pre-signed GET URL
- `deleteObject(key)` → delete file from R2
- `uploadBuffer(key, buffer, contentType)` → direct upload (used by migration script)

```typescript
// Interface
class R2Service {
  getPresignedUploadUrl(key: string, contentType: string, expiresIn?: number): Promise<string>;
  getPresignedDownloadUrl(key: string, expiresIn?: number): Promise<string>;
  deleteObject(key: string): Promise<void>;
  uploadBuffer(key: string, buffer: Buffer, contentType: string): Promise<void>;
}
```

### upload.service.ts — Upload Business Logic

Responsibilities:
- `requestUpload(companyId, category, entityId, fileName, fileSize)` → validates file size/type, generates R2 key, returns `{ uploadUrl, key }`
- `confirmUpload(key)` → verifies object exists in R2 (HEAD request), returns the stored key
- `getDownloadUrl(key)` → generates pre-signed download URL
- `deleteFile(key)` → removes file from R2
- `buildKey(companyId, category, entityId, fileName)` → constructs the R2 key per the key format above

```typescript
// Interface
interface UploadRequest {
  companyId: string;
  category: FileCategory;
  entityId: string;
  fileName: string;
  fileSize: number;        // bytes
  contentType: string;
}

interface UploadResponse {
  uploadUrl: string;       // pre-signed PUT URL
  key: string;             // R2 object key to store in DB
  expiresIn: number;       // seconds until URL expires
}

class UploadService {
  requestUpload(req: UploadRequest): Promise<UploadResponse>;
  getDownloadUrl(key: string): Promise<{ downloadUrl: string; expiresIn: number }>;
  deleteFile(key: string): Promise<void>;
}
```

### upload.constants.ts — Categories & Limits

```typescript
type FileCategory =
  | 'company-logo'
  | 'employee-photo'
  | 'employee-document'
  | 'education-certificate'
  | 'prev-employment-doc'
  | 'expense-receipt'
  | 'attendance-photo'
  | 'hr-letter'
  | 'recruitment-doc'
  | 'candidate-document'
  | 'training-material'
  | 'training-certificate'
  | 'payslip'
  | 'salary-revision'
  | 'offboarding-doc'
  | 'transfer-letter'
  | 'policy-document'
  | 'billing-invoice';

// Each category maps to: allowed MIME types, max size env key, key template
const FILE_CATEGORY_CONFIG: Record<FileCategory, {
  allowedMimeTypes: string[];
  maxSizeEnvKey: 'UPLOAD_MAX_IMAGE_SIZE' | 'UPLOAD_MAX_DOCUMENT_SIZE';
  keyTemplate: string;  // e.g., '{companyId}/employees/{entityId}/photo.{ext}'
}>;
```

### API Endpoints

**Route mount**: `/upload` — mounted after `tenantMiddleware()` (requires auth). For platform-level uploads (company logo by super admin), a separate `/platform/upload` route is added before tenant middleware.

```
POST /upload/request          # Request pre-signed upload URL
POST /platform/upload/request # Same, for super-admin (no tenant context)
POST /upload/download-url     # Get pre-signed download URL for a stored key
DELETE /upload/:key           # Delete a file (admin only)
```

**POST /upload/request**
```typescript
// Request
{
  category: FileCategory;
  entityId: string;
  fileName: string;
  fileSize: number;
  contentType: string;
}

// Response
{
  success: true,
  data: {
    uploadUrl: string;    // pre-signed PUT URL — frontend uploads here
    key: string;          // R2 key — frontend sends this back when saving the entity
    expiresIn: number;
  }
}
```

**POST /upload/download-url**
```typescript
// Request
{ key: string }

// Response
{
  success: true,
  data: {
    downloadUrl: string;  // pre-signed GET URL
    expiresIn: number;
  }
}
```

### Security

- All upload/download endpoints require authentication (`requireAuth` middleware)
- `requestUpload` validates that the `companyId` in the generated key matches the authenticated user's company (prevents cross-tenant uploads)
- `getDownloadUrl` validates that the requested key's `companyId` prefix matches the user's company
- Super admin can access any company's files via `/platform/upload/` routes
- File size validation happens both client-side (UX) and server-side (in `requestUpload` before generating the URL)
- Pre-signed upload URLs include `Content-Length` constraints via S3 conditions

---

## Frontend Design — Web (`web-system-app`)

### New Files

```
web-system-app/src/lib/api/upload.ts       # API client functions
web-system-app/src/hooks/useFileUpload.ts   # Reusable upload hook
web-system-app/src/hooks/useFileUrl.ts      # Reusable download URL hook (with caching)
```

### useFileUpload Hook

```typescript
interface UseFileUploadOptions {
  category: FileCategory;
  entityId: string;
  maxSize?: number;          // override env default
  allowedTypes?: string[];   // MIME types, e.g., ['image/jpeg', 'image/png']
  onSuccess?: (key: string) => void;
  onError?: (error: string) => void;
}

interface UseFileUploadReturn {
  upload: (file: File) => Promise<string | null>;  // returns R2 key or null on failure
  isUploading: boolean;
  progress: number;          // 0-100 (if XMLHttpRequest used for progress)
  error: string | null;
  reset: () => void;
}
```

**Upload flow:**
1. Validate file size and type client-side
2. Call `POST /upload/request` to get pre-signed URL + key
3. `PUT` file directly to the pre-signed URL (with `Content-Type` header)
4. Return the R2 key — caller saves it to the entity via normal API

### useFileUrl Hook

```typescript
interface UseFileUrlOptions {
  key: string | null | undefined;
  enabled?: boolean;
}

// Returns a pre-signed download URL, cached for 50 minutes (URL expires in 60)
function useFileUrl(options: UseFileUrlOptions): {
  url: string | null;
  isLoading: boolean;
}
```

Uses React Query with `staleTime: 50 * 60 * 1000` (50 minutes) to avoid re-fetching the download URL on every render. The pre-signed URL itself expires in 60 minutes, so 50 minutes gives a safe margin.

### Migration of Existing Components

Every component that currently does `FileReader.readAsDataURL()` will be updated to use `useFileUpload()` instead. Every component that displays a base64 string via `src={url}` will use `useFileUrl()` to get the pre-signed URL.

**Components to update (web):**

| Component | Current Pattern | New Pattern |
|-----------|----------------|-------------|
| `Step01Identity.tsx` | `readAsDataURL` → store base64 in form | `useFileUpload({ category: 'company-logo' })` → store R2 key |
| `CompanyDetailEditModal.tsx` | `readAsDataURL` → store base64 in form | `useFileUpload({ category: 'company-logo' })` → store R2 key |
| `EmployeeProfileScreen.tsx` (photo) | `readAsDataURL` → `profilePhotoUrl` | `useFileUpload({ category: 'employee-photo' })` → store key |
| `EmployeeProfileScreen.tsx` (docs) | `readAsDataURL` → `fileUrl` base64 | `useFileUpload({ category: 'employee-document' })` → store key |
| `ExpenseClaimScreen.tsx` | `fileToDataUrl()` → receipts array | `useFileUpload({ category: 'expense-receipt' })` → store key |
| `MyExpenseClaimsScreen.tsx` | `fileToDataUrl()` → receipts array | `useFileUpload({ category: 'expense-receipt' })` → store key |
| `TopBar.tsx` | `src={profilePhotoUrl}` (base64 or http) | `useFileUrl({ key })` → `src={url}` |
| `MyProfileScreen.tsx` | `src={url}` with base64 check | `useFileUrl({ key })` → `src={url}` |

---

## Frontend Design — Mobile (`mobile-app`)

### New Files

```
mobile-app/src/hooks/use-file-upload.ts     # Reusable upload hook
mobile-app/src/hooks/use-file-url.ts        # Reusable download URL hook
mobile-app/src/lib/api/upload.ts            # API client functions
```

### useFileUpload Hook (Mobile)

Same interface as web, but uses `expo-file-system` for efficient native upload:

```typescript
// Upload flow:
// 1. Pick file via ImagePicker or DocumentPicker (get local URI)
// 2. Get file info (size, type) for validation
// 3. Call POST /upload/request
// 4. FileSystem.uploadAsync(presignedUrl, localUri, { httpMethod: 'PUT', headers: { 'Content-Type': ... } })
// 5. Return R2 key
```

Key difference from web: mobile gets a local file URI from pickers, not a `File` object. The hook accepts either a `File` (web) or `{ uri, type, name, size }` (mobile).

### useFileUrl Hook (Mobile)

Same caching strategy as web. Returns a pre-signed URL for use in `<Image source={{ uri }}>`.

### Components to update (mobile):

| Component | Current Pattern | New Pattern |
|-----------|----------------|-------------|
| `step01-identity.tsx` | `ImagePicker` → `base64: true` → `data:image/jpeg;base64,...` | `ImagePicker` → `useFileUpload` with local URI → R2 key |
| `employee-detail-screen.tsx` | `ImagePicker/DocumentPicker` → base64 | `useFileUpload` → R2 key |
| `reports-hub-screen.tsx` | `Buffer.from(...).toString('base64')` | Save to `FileSystem.cacheDirectory`, upload via `useFileUpload` |

---

## Database Changes

**No schema changes required.** All existing `String` / `@db.Text` fields that currently store `data:image/...;base64,...` strings will instead store R2 object keys (e.g., `comp_123/employees/emp_456/photo.jpg`). The field type remains the same.

The `Json` fields for expense receipts (`receipts`) will store `{ fileName, fileUrl: "r2-key" }` instead of `{ fileName, fileUrl: "data:image/..." }`.

---

## Migration Script

### `scripts/migrate-base64-to-r2.ts`

A one-time migration script that:

1. **Scans** all database fields that contain base64 data (identified by `data:` prefix)
2. **Batches** records in groups of 50 to avoid memory issues
3. **Extracts** the base64 data, determines MIME type from the data URL prefix
4. **Uploads** to R2 using `r2.service.uploadBuffer()` (not pre-signed URLs — direct server upload for migration)
5. **Updates** the database field with the R2 key
6. **Logs** every operation (success/failure) to a migration log file

### Safety Features

- **Dry-run mode**: `--dry-run` flag scans and reports what would be migrated without making changes
- **Batch processing**: Processes 50 records at a time with a small delay between batches to avoid overwhelming R2
- **Per-record error handling**: If one record fails, log the error and continue with the next. Never abort the entire migration for a single failure.
- **Idempotent**: Checks if a field already contains an R2 key (no `data:` prefix) and skips it. Safe to re-run.
- **Progress reporting**: Logs `[category] Migrated X/Y records` after each batch
- **Migration report**: At the end, prints summary: total scanned, migrated, skipped, failed (with list of failed record IDs)
- **Rollback log**: Writes a `migration-rollback.json` file mapping each `{ table, id, field, oldValue: "truncated...", newKey: "r2-key" }` — can be used to revert if needed (old base64 data is NOT deleted from the JSON log for rollback, but truncated to first 100 chars for reference; the full base64 is in R2 now)

### Fields to Migrate

| Table | Field(s) | Category |
|-------|----------|----------|
| `Company` | `logoUrl` | `company-logo` |
| `Employee` | `profilePhotoUrl` | `employee-photo` |
| `EmployeeEducation` | `certificateUrl` | `education-certificate` |
| `EmployeePrevEmployment` | `experienceLetterUrl`, `relievingLetterUrl` | `prev-employment-doc` |
| `EmployeeDocument` | `fileUrl` | `employee-document` |
| `Candidate` | `resumeUrl` | `recruitment-doc` |
| `CandidateOffer` | `offerLetterUrl` | `recruitment-doc` |
| `CandidateEducation` | `certificateUrl` | `education-certificate` |
| `CandidateDocument` | `fileUrl` | `candidate-document` |
| `TrainingNomination` | `certificateUrl` | `training-certificate` |
| `TrainingMaterial` | `url` | `training-material` |
| `ExpenseClaim` | `receipts` (Json) | `expense-receipt` |
| `ExpenseClaimItem` | `receipts` (Json) | `expense-receipt` |
| `HRLetter` | `pdfUrl` | `hr-letter` |
| `AttendanceRecord` | `checkInPhotoUrl`, `checkOutPhotoUrl` | `attendance-photo` |
| `Payslip` | `pdfUrl` | `payslip` |
| `SalaryRevision` | `revisionLetterUrl` | `salary-revision` |
| `FnFSettlement` | `settlementLetterUrl` | `offboarding-doc` |
| `EmployeeTransfer` | `transferLetterUrl` | `transfer-letter` |
| `EmployeePromotion` | `promotionLetterUrl` | `transfer-letter` |
| `PolicyDocument` | `fileUrl` | `policy-document` |
| `Invoice` | `pdfUrl` | `billing-invoice` |
| `PayrollFiling` | `fileUrl` | `payslip` |

### Multi-Tenant Handling

The migration script must handle the multi-tenant architecture:

- **Platform DB fields** (`Company.logoUrl`): Query directly from platform Prisma client
- **Tenant DB fields** (everything else): Iterate over all tenants, connect to each tenant DB, and migrate records per-tenant
- Use the existing `getTenantPrismaClient(tenantId)` utility to get the correct Prisma client for each tenant

### Execution

```bash
# Dry run — see what would be migrated
npx ts-node scripts/migrate-base64-to-r2.ts --dry-run

# Full migration
npx ts-node scripts/migrate-base64-to-r2.ts

# Migrate specific category only
npx ts-node scripts/migrate-base64-to-r2.ts --category=company-logo

# Resume after failure (skips already-migrated records automatically)
npx ts-node scripts/migrate-base64-to-r2.ts
```

---

## Error Handling

### Upload Errors

| Error | Backend Response | Frontend Handling |
|-------|-----------------|-------------------|
| File too large | `ApiError.badRequest('File exceeds maximum size of X MB')` | Show toast via `showApiError` (web) / inline error (mobile) |
| Invalid file type | `ApiError.badRequest('File type X not allowed for category Y')` | Show toast |
| R2 unavailable | `ApiError.internal('File storage temporarily unavailable')` | Show toast, allow retry |
| Upload URL expired | N/A (frontend detects 403 from R2) | Auto-retry: request new URL and re-upload |
| Cross-tenant access | `ApiError.forbidden('Access denied')` | Show toast |

### Download Errors

| Error | Handling |
|-------|----------|
| Key not found in R2 | Return fallback placeholder image (for photos) or "File not available" message |
| Download URL expired | `useFileUrl` auto-refetches when URL expires (React Query handles staleness) |

---

## Testing Strategy

- **Unit tests**: `r2.service.ts` (mock S3Client), `upload.service.ts` (mock R2Service)
- **Integration tests**: Upload flow end-to-end with R2 (use R2 dev bucket or Miniflare/LocalStack for S3-compatible local testing)
- **Frontend tests**: Mock API responses, verify `useFileUpload` state transitions
- **Migration tests**: Test with sample base64 data, verify correct key generation and upload

---

## Rollout Plan

1. **Phase 1**: Deploy backend upload service + R2 infrastructure (env vars, bucket creation)
2. **Phase 2**: Update frontend components to use new upload hooks (new uploads go to R2)
3. **Phase 3**: Run migration script (dry-run first, then full migration)
4. **Phase 4**: Verify all data migrated, remove base64 display fallbacks after confirmation
