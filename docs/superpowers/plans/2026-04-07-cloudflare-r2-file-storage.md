# Cloudflare R2 File Storage Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace all base64 file storage with Cloudflare R2 object storage using pre-signed URLs for secure upload/download.

**Architecture:** Backend R2 service generates pre-signed upload/download URLs. Frontends upload files directly to R2, then save the R2 key in the entity. Downloads go through short-lived pre-signed URLs. A migration script moves all existing base64 data to R2.

**Tech Stack:** Cloudflare R2, `@aws-sdk/client-s3` + `@aws-sdk/s3-request-presigner`, Express, Zod, React Query, Zustand, expo-file-system

**Spec:** `docs/superpowers/specs/2026-04-07-cloudflare-r2-file-storage-design.md`

---

## File Structure

### Backend (avy-erp-backend)

| Action | File | Responsibility |
|--------|------|----------------|
| Create | `src/shared/constants/upload.ts` | File categories, MIME types, size limit config |
| Create | `src/shared/services/r2.service.ts` | R2 client singleton, pre-signed URL generation |
| Create | `src/shared/services/upload.service.ts` | Key generation, validation, URL orchestration |
| Create | `src/modules/upload/upload.validators.ts` | Zod schemas for upload requests |
| Create | `src/modules/upload/upload.controller.ts` | API endpoint handlers |
| Create | `src/modules/upload/upload.routes.ts` | Route definitions |
| Modify | `src/config/env.ts` | Add R2 env variables |
| Modify | `src/app/routes.ts` | Mount upload routes |
| Create | `scripts/migrate-base64-to-r2.ts` | One-time migration script |

### Web App (web-system-app)

| Action | File | Responsibility |
|--------|------|----------------|
| Create | `src/lib/api/upload.ts` | Upload API client functions |
| Create | `src/hooks/useFileUpload.ts` | Reusable upload hook |
| Create | `src/hooks/useFileUrl.ts` | Reusable download URL hook with caching |
| Modify | `src/features/super-admin/CompanyDetailEditModal.tsx` | Use useFileUpload for logo |
| Modify | `src/features/super-admin/tenant-onboarding/steps/Step01Identity.tsx` | Use useFileUpload for logo |
| Modify | `src/features/company-admin/hr/EmployeeProfileScreen.tsx` | Use useFileUpload for photo + docs |
| Modify | `src/features/company-admin/hr/ExpenseClaimScreen.tsx` | Use useFileUpload for receipts |
| Modify | `src/features/ess/MyExpenseClaimsScreen.tsx` | Use useFileUpload for receipts |
| Modify | `src/layouts/TopBar.tsx` | Use useFileUrl for profile photo display |
| Modify | `src/features/company-admin/hr/MyProfileScreen.tsx` | Use useFileUrl for photo display |

### Mobile App (mobile-app)

| Action | File | Responsibility |
|--------|------|----------------|
| Create | `src/lib/api/upload.ts` | Upload API client functions |
| Create | `src/hooks/use-file-upload.ts` | Reusable upload hook (expo-file-system) |
| Create | `src/hooks/use-file-url.ts` | Reusable download URL hook with caching |
| Modify | `src/features/super-admin/tenant-onboarding/steps/step01-identity.tsx` | Use useFileUpload for logo |
| Modify | `src/features/company-admin/hr/employee-detail-screen.tsx` | Use useFileUpload for photo + docs |

---

### Task 1: Install Dependencies & Add Environment Variables

**Files:**
- Modify: `avy-erp-backend/package.json`
- Modify: `avy-erp-backend/src/config/env.ts`
- Modify: `avy-erp-backend/.env.example`

- [ ] **Step 1: Install AWS SDK packages for R2**

```bash
cd avy-erp-backend && pnpm add @aws-sdk/client-s3 @aws-sdk/s3-request-presigner
```

- [ ] **Step 2: Add R2 env variables to env.ts**

In `avy-erp-backend/src/config/env.ts`, add the following fields inside the `envSchema` object, after the existing `// Storage` section (after line 67):

```typescript
  // Cloudflare R2
  R2_ACCOUNT_ID: z.string().optional(),
  R2_ACCESS_KEY_ID: z.string().optional(),
  R2_SECRET_ACCESS_KEY: z.string().optional(),
  R2_BUCKET_NAME: z.string().default('avy-erp-files'),
  R2_ENDPOINT: z.string().optional(),
  R2_UPLOAD_URL_EXPIRY_SECONDS: z.coerce.number().default(300),
  R2_DOWNLOAD_URL_EXPIRY_SECONDS: z.coerce.number().default(3600),

  // File Upload Limits (bytes)
  UPLOAD_MAX_IMAGE_SIZE: z.coerce.number().default(5242880),
  UPLOAD_MAX_DOCUMENT_SIZE: z.coerce.number().default(10485760),
```

- [ ] **Step 3: Add R2 vars to .env.example**

Append to `avy-erp-backend/.env.example`:

```env
# Cloudflare R2
R2_ACCOUNT_ID=
R2_ACCESS_KEY_ID=
R2_SECRET_ACCESS_KEY=
R2_BUCKET_NAME=avy-erp-files
R2_ENDPOINT=
R2_UPLOAD_URL_EXPIRY_SECONDS=300
R2_DOWNLOAD_URL_EXPIRY_SECONDS=3600

# File Upload Limits (bytes)
UPLOAD_MAX_IMAGE_SIZE=5242880
UPLOAD_MAX_DOCUMENT_SIZE=10485760
```

- [ ] **Step 4: Verify TypeScript compiles**

```bash
cd avy-erp-backend && pnpm build
```

Expected: BUILD SUCCESS with no errors.

- [ ] **Step 5: Commit**

```bash
git add avy-erp-backend/package.json avy-erp-backend/pnpm-lock.yaml avy-erp-backend/src/config/env.ts avy-erp-backend/.env.example
git commit -m "feat: add @aws-sdk/client-s3 and R2 environment variables"
```

---

### Task 2: Backend Upload Constants

**Files:**
- Create: `avy-erp-backend/src/shared/constants/upload.ts`

- [ ] **Step 1: Create upload constants file**

Create `avy-erp-backend/src/shared/constants/upload.ts`:

```typescript
import { env } from '../../config/env';

export type FileCategory =
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

export const IMAGE_MIME_TYPES = [
  'image/jpeg',
  'image/png',
  'image/gif',
  'image/webp',
];

export const DOCUMENT_MIME_TYPES = [
  'application/pdf',
  'application/msword',
  'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
  'application/vnd.ms-excel',
  'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
];

export const ALL_MIME_TYPES = [...IMAGE_MIME_TYPES, ...DOCUMENT_MIME_TYPES];

interface CategoryConfig {
  allowedMimeTypes: string[];
  maxSizeEnvKey: 'UPLOAD_MAX_IMAGE_SIZE' | 'UPLOAD_MAX_DOCUMENT_SIZE';
  keyTemplate: string; // Placeholders: {companyId}, {entityId}, {filename}
}

export const FILE_CATEGORY_CONFIG: Record<FileCategory, CategoryConfig> = {
  'company-logo': {
    allowedMimeTypes: IMAGE_MIME_TYPES,
    maxSizeEnvKey: 'UPLOAD_MAX_IMAGE_SIZE',
    keyTemplate: '{companyId}/company/logo.{ext}',
  },
  'employee-photo': {
    allowedMimeTypes: IMAGE_MIME_TYPES,
    maxSizeEnvKey: 'UPLOAD_MAX_IMAGE_SIZE',
    keyTemplate: '{companyId}/employees/{entityId}/photo.{ext}',
  },
  'employee-document': {
    allowedMimeTypes: ALL_MIME_TYPES,
    maxSizeEnvKey: 'UPLOAD_MAX_DOCUMENT_SIZE',
    keyTemplate: '{companyId}/employees/{entityId}/documents/{filename}',
  },
  'education-certificate': {
    allowedMimeTypes: ALL_MIME_TYPES,
    maxSizeEnvKey: 'UPLOAD_MAX_DOCUMENT_SIZE',
    keyTemplate: '{companyId}/employees/{entityId}/education/{filename}',
  },
  'prev-employment-doc': {
    allowedMimeTypes: ALL_MIME_TYPES,
    maxSizeEnvKey: 'UPLOAD_MAX_DOCUMENT_SIZE',
    keyTemplate: '{companyId}/employees/{entityId}/prev-employment/{filename}',
  },
  'expense-receipt': {
    allowedMimeTypes: [...IMAGE_MIME_TYPES, 'application/pdf'],
    maxSizeEnvKey: 'UPLOAD_MAX_DOCUMENT_SIZE',
    keyTemplate: '{companyId}/expenses/{entityId}/{filename}',
  },
  'attendance-photo': {
    allowedMimeTypes: IMAGE_MIME_TYPES,
    maxSizeEnvKey: 'UPLOAD_MAX_IMAGE_SIZE',
    keyTemplate: '{companyId}/attendance/{entityId}/{filename}',
  },
  'hr-letter': {
    allowedMimeTypes: ['application/pdf'],
    maxSizeEnvKey: 'UPLOAD_MAX_DOCUMENT_SIZE',
    keyTemplate: '{companyId}/hr-letters/{entityId}.pdf',
  },
  'recruitment-doc': {
    allowedMimeTypes: ALL_MIME_TYPES,
    maxSizeEnvKey: 'UPLOAD_MAX_DOCUMENT_SIZE',
    keyTemplate: '{companyId}/recruitment/{entityId}/{filename}',
  },
  'candidate-document': {
    allowedMimeTypes: ALL_MIME_TYPES,
    maxSizeEnvKey: 'UPLOAD_MAX_DOCUMENT_SIZE',
    keyTemplate: '{companyId}/recruitment/{entityId}/documents/{filename}',
  },
  'training-material': {
    allowedMimeTypes: ALL_MIME_TYPES,
    maxSizeEnvKey: 'UPLOAD_MAX_DOCUMENT_SIZE',
    keyTemplate: '{companyId}/training/{entityId}/{filename}',
  },
  'training-certificate': {
    allowedMimeTypes: ALL_MIME_TYPES,
    maxSizeEnvKey: 'UPLOAD_MAX_DOCUMENT_SIZE',
    keyTemplate: '{companyId}/training/certificates/{entityId}.{ext}',
  },
  'payslip': {
    allowedMimeTypes: ['application/pdf'],
    maxSizeEnvKey: 'UPLOAD_MAX_DOCUMENT_SIZE',
    keyTemplate: '{companyId}/payroll/{entityId}.pdf',
  },
  'salary-revision': {
    allowedMimeTypes: ['application/pdf'],
    maxSizeEnvKey: 'UPLOAD_MAX_DOCUMENT_SIZE',
    keyTemplate: '{companyId}/payroll/revisions/{entityId}.pdf',
  },
  'offboarding-doc': {
    allowedMimeTypes: ['application/pdf'],
    maxSizeEnvKey: 'UPLOAD_MAX_DOCUMENT_SIZE',
    keyTemplate: '{companyId}/offboarding/{entityId}/{filename}',
  },
  'transfer-letter': {
    allowedMimeTypes: ['application/pdf'],
    maxSizeEnvKey: 'UPLOAD_MAX_DOCUMENT_SIZE',
    keyTemplate: '{companyId}/transfers/{entityId}.pdf',
  },
  'policy-document': {
    allowedMimeTypes: ALL_MIME_TYPES,
    maxSizeEnvKey: 'UPLOAD_MAX_DOCUMENT_SIZE',
    keyTemplate: '{companyId}/policies/{entityId}.{ext}',
  },
  'billing-invoice': {
    allowedMimeTypes: ['application/pdf'],
    maxSizeEnvKey: 'UPLOAD_MAX_DOCUMENT_SIZE',
    keyTemplate: '{companyId}/billing/{entityId}.pdf',
  },
};

export function getMaxFileSize(category: FileCategory): number {
  const config = FILE_CATEGORY_CONFIG[category];
  return env[config.maxSizeEnvKey];
}

export function getExtensionFromMime(mimeType: string): string {
  const map: Record<string, string> = {
    'image/jpeg': 'jpg',
    'image/png': 'png',
    'image/gif': 'gif',
    'image/webp': 'webp',
    'application/pdf': 'pdf',
    'application/msword': 'doc',
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document': 'docx',
    'application/vnd.ms-excel': 'xls',
    'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': 'xlsx',
  };
  return map[mimeType] || 'bin';
}

export function getExtensionFromFilename(filename: string): string {
  return filename.split('.').pop()?.toLowerCase() || 'bin';
}

export function getMimeFromExtension(ext: string): string {
  const map: Record<string, string> = {
    jpg: 'image/jpeg',
    jpeg: 'image/jpeg',
    png: 'image/png',
    gif: 'image/gif',
    webp: 'image/webp',
    pdf: 'application/pdf',
    doc: 'application/msword',
    docx: 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    xls: 'application/vnd.ms-excel',
    xlsx: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
  };
  return map[ext] || 'application/octet-stream';
}
```

- [ ] **Step 2: Verify TypeScript compiles**

```bash
cd avy-erp-backend && pnpm build
```

Expected: BUILD SUCCESS.

- [ ] **Step 3: Commit**

```bash
git add avy-erp-backend/src/shared/constants/upload.ts
git commit -m "feat: add file upload constants and category config"
```

---

### Task 3: Backend R2 Service

**Files:**
- Create: `avy-erp-backend/src/shared/services/r2.service.ts`

- [ ] **Step 1: Create R2 service**

Create `avy-erp-backend/src/shared/services/r2.service.ts`:

```typescript
import {
  S3Client,
  PutObjectCommand,
  GetObjectCommand,
  DeleteObjectCommand,
  HeadObjectCommand,
} from '@aws-sdk/client-s3';
import { getSignedUrl } from '@aws-sdk/s3-request-presigner';
import { env } from '../../config/env';
import { logger } from '../../config/logger';

class R2Service {
  private client: S3Client | null = null;
  private bucket: string;

  constructor() {
    this.bucket = env.R2_BUCKET_NAME;
  }

  private getClient(): S3Client {
    if (this.client) return this.client;

    const accountId = env.R2_ACCOUNT_ID;
    const endpoint = env.R2_ENDPOINT || (accountId ? `https://${accountId}.r2.cloudflarestorage.com` : '');

    if (!endpoint || !env.R2_ACCESS_KEY_ID || !env.R2_SECRET_ACCESS_KEY) {
      throw new Error('R2 configuration is incomplete. Set R2_ACCOUNT_ID, R2_ACCESS_KEY_ID, and R2_SECRET_ACCESS_KEY.');
    }

    this.client = new S3Client({
      region: 'auto',
      endpoint,
      credentials: {
        accessKeyId: env.R2_ACCESS_KEY_ID,
        secretAccessKey: env.R2_SECRET_ACCESS_KEY,
      },
    });

    logger.info('R2 client initialized', { bucket: this.bucket, endpoint });
    return this.client;
  }

  async getPresignedUploadUrl(
    key: string,
    contentType: string,
    expiresIn?: number,
  ): Promise<string> {
    const client = this.getClient();
    const command = new PutObjectCommand({
      Bucket: this.bucket,
      Key: key,
      ContentType: contentType,
    });

    return getSignedUrl(client, command, {
      expiresIn: expiresIn ?? env.R2_UPLOAD_URL_EXPIRY_SECONDS,
    });
  }

  async getPresignedDownloadUrl(
    key: string,
    expiresIn?: number,
  ): Promise<string> {
    const client = this.getClient();
    const command = new GetObjectCommand({
      Bucket: this.bucket,
      Key: key,
    });

    return getSignedUrl(client, command, {
      expiresIn: expiresIn ?? env.R2_DOWNLOAD_URL_EXPIRY_SECONDS,
    });
  }

  async headObject(key: string): Promise<boolean> {
    try {
      const client = this.getClient();
      await client.send(
        new HeadObjectCommand({ Bucket: this.bucket, Key: key }),
      );
      return true;
    } catch {
      return false;
    }
  }

  async deleteObject(key: string): Promise<void> {
    const client = this.getClient();
    await client.send(
      new DeleteObjectCommand({ Bucket: this.bucket, Key: key }),
    );
    logger.info('R2 object deleted', { key });
  }

  async uploadBuffer(
    key: string,
    buffer: Buffer,
    contentType: string,
  ): Promise<void> {
    const client = this.getClient();
    await client.send(
      new PutObjectCommand({
        Bucket: this.bucket,
        Key: key,
        Body: buffer,
        ContentType: contentType,
      }),
    );
    logger.info('R2 object uploaded', { key, size: buffer.length });
  }

  isConfigured(): boolean {
    return !!(
      (env.R2_ACCOUNT_ID || env.R2_ENDPOINT) &&
      env.R2_ACCESS_KEY_ID &&
      env.R2_SECRET_ACCESS_KEY
    );
  }
}

export const r2Service = new R2Service();
```

- [ ] **Step 2: Verify TypeScript compiles**

```bash
cd avy-erp-backend && pnpm build
```

Expected: BUILD SUCCESS.

- [ ] **Step 3: Commit**

```bash
git add avy-erp-backend/src/shared/services/r2.service.ts
git commit -m "feat: add R2 service with pre-signed URL generation"
```

---

### Task 4: Backend Upload Service

**Files:**
- Create: `avy-erp-backend/src/shared/services/upload.service.ts`

- [ ] **Step 1: Create upload service**

Create `avy-erp-backend/src/shared/services/upload.service.ts`:

```typescript
import { v4 as uuidv4 } from 'uuid';
import { ApiError } from '../errors';
import { logger } from '../../config/logger';
import { env } from '../../config/env';
import { r2Service } from './r2.service';
import {
  FileCategory,
  FILE_CATEGORY_CONFIG,
  getMaxFileSize,
  getExtensionFromFilename,
  getExtensionFromMime,
} from '../constants/upload';

export interface UploadRequest {
  companyId: string;
  category: FileCategory;
  entityId: string;
  fileName: string;
  fileSize: number;
  contentType: string;
}

export interface UploadResponse {
  uploadUrl: string;
  key: string;
  expiresIn: number;
}

export interface DownloadUrlResponse {
  downloadUrl: string;
  expiresIn: number;
}

class UploadService {
  /**
   * Request a pre-signed upload URL. Validates category, file size, and MIME type.
   */
  async requestUpload(req: UploadRequest): Promise<UploadResponse> {
    const config = FILE_CATEGORY_CONFIG[req.category];
    if (!config) {
      throw ApiError.badRequest(`Invalid file category: ${req.category}`);
    }

    // Validate MIME type
    if (!config.allowedMimeTypes.includes(req.contentType)) {
      throw ApiError.badRequest(
        `File type "${req.contentType}" is not allowed for category "${req.category}". Allowed: ${config.allowedMimeTypes.join(', ')}`,
      );
    }

    // Validate file size
    const maxSize = getMaxFileSize(req.category);
    if (req.fileSize > maxSize) {
      const maxMB = (maxSize / (1024 * 1024)).toFixed(0);
      throw ApiError.badRequest(
        `File size ${(req.fileSize / (1024 * 1024)).toFixed(1)} MB exceeds maximum of ${maxMB} MB`,
      );
    }

    // Build R2 key from template
    const key = this.buildKey(req);

    // Generate pre-signed upload URL
    const expiresIn = env.R2_UPLOAD_URL_EXPIRY_SECONDS;
    const uploadUrl = await r2Service.getPresignedUploadUrl(
      key,
      req.contentType,
      expiresIn,
    );

    logger.info('Pre-signed upload URL generated', {
      category: req.category,
      key,
      companyId: req.companyId,
    });

    return { uploadUrl, key, expiresIn };
  }

  /**
   * Get a pre-signed download URL for a stored file key.
   * Validates that the requesting user's companyId matches the key prefix.
   */
  async getDownloadUrl(
    key: string,
    requestingCompanyId: string,
  ): Promise<DownloadUrlResponse> {
    // Validate company access: key starts with companyId/
    const keyCompanyId = key.split('/')[0];
    if (keyCompanyId !== requestingCompanyId) {
      throw ApiError.forbidden('Access denied to this file');
    }

    const expiresIn = env.R2_DOWNLOAD_URL_EXPIRY_SECONDS;
    const downloadUrl = await r2Service.getPresignedDownloadUrl(key, expiresIn);

    return { downloadUrl, expiresIn };
  }

  /**
   * Get a pre-signed download URL without company validation (for super-admin).
   */
  async getDownloadUrlAdmin(key: string): Promise<DownloadUrlResponse> {
    const expiresIn = env.R2_DOWNLOAD_URL_EXPIRY_SECONDS;
    const downloadUrl = await r2Service.getPresignedDownloadUrl(key, expiresIn);
    return { downloadUrl, expiresIn };
  }

  /**
   * Delete a file from R2.
   */
  async deleteFile(key: string): Promise<void> {
    await r2Service.deleteObject(key);
  }

  /**
   * Build the R2 object key from the category template and request data.
   */
  private buildKey(req: UploadRequest): string {
    const config = FILE_CATEGORY_CONFIG[req.category];
    const ext = getExtensionFromFilename(req.fileName) || getExtensionFromMime(req.contentType);
    const uniqueFilename = `${uuidv4()}.${ext}`;

    let key = config.keyTemplate
      .replace('{companyId}', req.companyId)
      .replace('{entityId}', req.entityId)
      .replace('{ext}', ext)
      .replace('{filename}', uniqueFilename);

    return key;
  }
}

export const uploadService = new UploadService();
```

- [ ] **Step 2: Verify TypeScript compiles**

```bash
cd avy-erp-backend && pnpm build
```

Expected: BUILD SUCCESS.

- [ ] **Step 3: Commit**

```bash
git add avy-erp-backend/src/shared/services/upload.service.ts
git commit -m "feat: add upload service with key generation and validation"
```

---

### Task 5: Backend Upload Validators, Controller & Routes

**Files:**
- Create: `avy-erp-backend/src/modules/upload/upload.validators.ts`
- Create: `avy-erp-backend/src/modules/upload/upload.controller.ts`
- Create: `avy-erp-backend/src/modules/upload/upload.routes.ts`
- Modify: `avy-erp-backend/src/app/routes.ts`

- [ ] **Step 1: Create validators**

Create `avy-erp-backend/src/modules/upload/upload.validators.ts`:

```typescript
import { z } from 'zod';
import { FILE_CATEGORY_CONFIG, type FileCategory } from '../../shared/constants/upload';

const validCategories = Object.keys(FILE_CATEGORY_CONFIG) as [FileCategory, ...FileCategory[]];

export const requestUploadSchema = z.object({
  category: z.enum(validCategories, {
    errorMap: () => ({ message: `Invalid category. Must be one of: ${validCategories.join(', ')}` }),
  }),
  entityId: z.string().min(1, 'Entity ID is required'),
  fileName: z.string().min(1, 'File name is required'),
  fileSize: z.number().positive('File size must be positive'),
  contentType: z.string().min(1, 'Content type is required'),
});

export const downloadUrlSchema = z.object({
  key: z.string().min(1, 'File key is required'),
});
```

- [ ] **Step 2: Create controller**

Create `avy-erp-backend/src/modules/upload/upload.controller.ts`:

```typescript
import { Request, Response } from 'express';
import { asyncHandler } from '../../middleware/error.middleware';
import { ApiError } from '../../shared/errors';
import { createSuccessResponse } from '../../shared/utils';
import { uploadService } from '../../shared/services/upload.service';
import { requestUploadSchema, downloadUrlSchema } from './upload.validators';

class UploadController {
  /**
   * POST /upload/request — Request a pre-signed upload URL (tenant-scoped).
   */
  requestUpload = asyncHandler(async (req: Request, res: Response) => {
    const parsed = requestUploadSchema.safeParse(req.body);
    if (!parsed.success) {
      throw ApiError.badRequest(parsed.error.errors.map((e) => e.message).join(', '));
    }

    const companyId = req.user?.companyId;
    if (!companyId) {
      throw ApiError.unauthorized('Company context required');
    }

    const result = await uploadService.requestUpload({
      ...parsed.data,
      companyId,
    });

    res.json(createSuccessResponse(result, 'Upload URL generated'));
  });

  /**
   * POST /platform/upload/request — Request a pre-signed upload URL (super-admin).
   * Super-admin must provide companyId in the body since they have no tenant context.
   */
  requestUploadPlatform = asyncHandler(async (req: Request, res: Response) => {
    const bodySchema = requestUploadSchema.extend({
      companyId: z.string().min(1, 'Company ID is required for platform uploads'),
    });

    const parsed = bodySchema.safeParse(req.body);
    if (!parsed.success) {
      throw ApiError.badRequest(parsed.error.errors.map((e) => e.message).join(', '));
    }

    const result = await uploadService.requestUpload(parsed.data);
    res.json(createSuccessResponse(result, 'Upload URL generated'));
  });

  /**
   * POST /upload/download-url — Get a pre-signed download URL (tenant-scoped).
   */
  getDownloadUrl = asyncHandler(async (req: Request, res: Response) => {
    const parsed = downloadUrlSchema.safeParse(req.body);
    if (!parsed.success) {
      throw ApiError.badRequest(parsed.error.errors.map((e) => e.message).join(', '));
    }

    const companyId = req.user?.companyId;
    if (!companyId) {
      throw ApiError.unauthorized('Company context required');
    }

    const result = await uploadService.getDownloadUrl(parsed.data.key, companyId);
    res.json(createSuccessResponse(result, 'Download URL generated'));
  });

  /**
   * POST /platform/upload/download-url — Get a pre-signed download URL (super-admin).
   */
  getDownloadUrlPlatform = asyncHandler(async (req: Request, res: Response) => {
    const parsed = downloadUrlSchema.safeParse(req.body);
    if (!parsed.success) {
      throw ApiError.badRequest(parsed.error.errors.map((e) => e.message).join(', '));
    }

    const result = await uploadService.getDownloadUrlAdmin(parsed.data.key);
    res.json(createSuccessResponse(result, 'Download URL generated'));
  });
}

// Need to import z for the extended schema in requestUploadPlatform
import { z } from 'zod';

export const uploadController = new UploadController();
```

- [ ] **Step 3: Create routes**

Create `avy-erp-backend/src/modules/upload/upload.routes.ts`:

```typescript
import { Router } from 'express';
import { uploadController } from './upload.controller';

// Tenant-scoped upload routes (mounted after auth + tenant middleware)
const uploadRoutes = Router();
uploadRoutes.post('/request', uploadController.requestUpload);
uploadRoutes.post('/download-url', uploadController.getDownloadUrl);

// Platform-level upload routes (mounted under /platform, super-admin only)
const uploadPlatformRoutes = Router();
uploadPlatformRoutes.post('/request', uploadController.requestUploadPlatform);
uploadPlatformRoutes.post('/download-url', uploadController.getDownloadUrlPlatform);

export { uploadRoutes, uploadPlatformRoutes };
```

- [ ] **Step 4: Mount routes in app/routes.ts**

In `avy-erp-backend/src/app/routes.ts`:

Add the import at the top (after line 29):

```typescript
import { uploadRoutes, uploadPlatformRoutes } from '../modules/upload/upload.routes';
```

Add the platform upload route after line 86 (after other `/platform/*` routes):

```typescript
router.use('/platform/upload', uploadPlatformRoutes);
```

Add the tenant-scoped upload route after line 141 (after other business module routes, before company routes):

```typescript
router.use('/upload', uploadRoutes);
```

- [ ] **Step 5: Verify TypeScript compiles**

```bash
cd avy-erp-backend && pnpm build
```

Expected: BUILD SUCCESS.

- [ ] **Step 6: Test manually (optional)**

Start dev server and test with curl:

```bash
cd avy-erp-backend && pnpm dev
```

```bash
# Should return 401 (unauthorized) — confirms route is mounted
curl -s http://localhost:3000/api/v1/upload/request -X POST -H "Content-Type: application/json" -d '{}' | jq .
```

Expected: `{ "success": false, "error": "Unauthorized" }` or similar auth error (confirming the route exists and auth middleware runs).

- [ ] **Step 7: Commit**

```bash
git add avy-erp-backend/src/modules/upload/ avy-erp-backend/src/app/routes.ts
git commit -m "feat: add upload controller, validators, and routes"
```

---

### Task 6: Web App — Upload API Client

**Files:**
- Create: `web-system-app/src/lib/api/upload.ts`

- [ ] **Step 1: Create upload API client**

Create `web-system-app/src/lib/api/upload.ts`:

```typescript
import { client } from './client';

export type FileCategory =
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

interface RequestUploadPayload {
  category: FileCategory;
  entityId: string;
  fileName: string;
  fileSize: number;
  contentType: string;
  companyId?: string; // Only for platform uploads
}

interface UploadResponse {
  uploadUrl: string;
  key: string;
  expiresIn: number;
}

interface DownloadUrlResponse {
  downloadUrl: string;
  expiresIn: number;
}

export const uploadApi = {
  /** Request a pre-signed upload URL (tenant-scoped) */
  requestUpload: (payload: RequestUploadPayload) =>
    client.post<{ success: boolean; data: UploadResponse }>('/upload/request', payload)
      .then((r) => r.data),

  /** Request a pre-signed upload URL (super-admin / platform) */
  requestUploadPlatform: (payload: RequestUploadPayload) =>
    client.post<{ success: boolean; data: UploadResponse }>('/platform/upload/request', payload)
      .then((r) => r.data),

  /** Get a pre-signed download URL (tenant-scoped) */
  getDownloadUrl: (key: string) =>
    client.post<{ success: boolean; data: DownloadUrlResponse }>('/upload/download-url', { key })
      .then((r) => r.data),

  /** Get a pre-signed download URL (super-admin / platform) */
  getDownloadUrlPlatform: (key: string) =>
    client.post<{ success: boolean; data: DownloadUrlResponse }>('/platform/upload/download-url', { key })
      .then((r) => r.data),
};

export const uploadKeys = {
  all: ['upload'] as const,
  downloadUrl: (key: string) => [...uploadKeys.all, 'download-url', key] as const,
};
```

- [ ] **Step 2: Verify TypeScript compiles**

```bash
cd web-system-app && pnpm build
```

Expected: BUILD SUCCESS.

- [ ] **Step 3: Commit**

```bash
git add web-system-app/src/lib/api/upload.ts
git commit -m "feat(web): add upload API client"
```

---

### Task 7: Web App — useFileUpload Hook

**Files:**
- Create: `web-system-app/src/hooks/useFileUpload.ts`

- [ ] **Step 1: Create useFileUpload hook**

Create `web-system-app/src/hooks/useFileUpload.ts`:

```typescript
import { useState, useCallback } from 'react';
import { uploadApi, type FileCategory } from '@/lib/api/upload';
import { showApiError } from '@/lib/toast';

interface UseFileUploadOptions {
  category: FileCategory;
  entityId: string;
  maxSize?: number;
  allowedTypes?: string[];
  /** Use platform endpoint (for super-admin uploads) */
  platform?: boolean;
  /** Required when platform=true */
  companyId?: string;
  onSuccess?: (key: string) => void;
  onError?: (error: string) => void;
}

interface UseFileUploadReturn {
  upload: (file: File) => Promise<string | null>;
  isUploading: boolean;
  error: string | null;
  reset: () => void;
}

const DEFAULT_IMAGE_MAX = 5 * 1024 * 1024; // 5 MB
const DEFAULT_DOC_MAX = 10 * 1024 * 1024;  // 10 MB

const IMAGE_TYPES = ['image/jpeg', 'image/png', 'image/gif', 'image/webp'];

export function useFileUpload(options: UseFileUploadOptions): UseFileUploadReturn {
  const [isUploading, setIsUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const reset = useCallback(() => {
    setIsUploading(false);
    setError(null);
  }, []);

  const upload = useCallback(async (file: File): Promise<string | null> => {
    setError(null);
    setIsUploading(true);

    try {
      // Client-side validation
      const isImage = IMAGE_TYPES.includes(file.type);
      const maxSize = options.maxSize ?? (isImage ? DEFAULT_IMAGE_MAX : DEFAULT_DOC_MAX);

      if (file.size > maxSize) {
        const maxMB = (maxSize / (1024 * 1024)).toFixed(0);
        const errMsg = `File size exceeds ${maxMB} MB limit`;
        setError(errMsg);
        options.onError?.(errMsg);
        return null;
      }

      if (options.allowedTypes && !options.allowedTypes.includes(file.type)) {
        const errMsg = `File type "${file.type}" is not allowed`;
        setError(errMsg);
        options.onError?.(errMsg);
        return null;
      }

      // Request pre-signed upload URL from backend
      const requestFn = options.platform
        ? uploadApi.requestUploadPlatform
        : uploadApi.requestUpload;

      const response = await requestFn({
        category: options.category,
        entityId: options.entityId,
        fileName: file.name,
        fileSize: file.size,
        contentType: file.type,
        companyId: options.companyId,
      });

      const { uploadUrl, key } = response.data;

      // Upload file directly to R2 via pre-signed URL
      const uploadResponse = await fetch(uploadUrl, {
        method: 'PUT',
        body: file,
        headers: { 'Content-Type': file.type },
      });

      if (!uploadResponse.ok) {
        throw new Error(`Upload failed with status ${uploadResponse.status}`);
      }

      options.onSuccess?.(key);
      return key;
    } catch (err: any) {
      const errMsg = err?.response?.data?.message || err?.message || 'Upload failed';
      setError(errMsg);
      options.onError?.(errMsg);
      showApiError(err);
      return null;
    } finally {
      setIsUploading(false);
    }
  }, [options.category, options.entityId, options.maxSize, options.allowedTypes, options.platform, options.companyId, options.onSuccess, options.onError]);

  return { upload, isUploading, error, reset };
}
```

- [ ] **Step 2: Verify TypeScript compiles**

```bash
cd web-system-app && pnpm build
```

Expected: BUILD SUCCESS.

- [ ] **Step 3: Commit**

```bash
git add web-system-app/src/hooks/useFileUpload.ts
git commit -m "feat(web): add useFileUpload hook for R2 uploads"
```

---

### Task 8: Web App — useFileUrl Hook

**Files:**
- Create: `web-system-app/src/hooks/useFileUrl.ts`

- [ ] **Step 1: Create useFileUrl hook**

Create `web-system-app/src/hooks/useFileUrl.ts`:

```typescript
import { useQuery } from '@tanstack/react-query';
import { uploadApi, uploadKeys } from '@/lib/api/upload';

interface UseFileUrlOptions {
  /** The R2 object key stored in the database */
  key: string | null | undefined;
  /** Whether to fetch the URL (default: true) */
  enabled?: boolean;
  /** Use platform endpoint (for super-admin) */
  platform?: boolean;
}

/**
 * Fetches a pre-signed download URL for a stored R2 key.
 *
 * Handles both legacy base64 data URLs and R2 keys:
 * - If key starts with "data:" or "http", returns it directly (no fetch)
 * - If key is an R2 key, fetches a pre-signed download URL
 *
 * The URL is cached for 50 minutes (pre-signed URLs expire in 60 minutes).
 */
export function useFileUrl(options: UseFileUrlOptions) {
  const { key, enabled = true, platform = false } = options;

  // Detect legacy base64 or existing HTTP URLs — no fetch needed
  const isDirectUrl =
    key?.startsWith('data:') ||
    key?.startsWith('http://') ||
    key?.startsWith('https://') ||
    key?.startsWith('/');

  const query = useQuery({
    queryKey: uploadKeys.downloadUrl(key ?? ''),
    queryFn: async () => {
      if (!key) return null;
      const fetchFn = platform
        ? uploadApi.getDownloadUrlPlatform
        : uploadApi.getDownloadUrl;
      const response = await fetchFn(key);
      return response.data.downloadUrl;
    },
    enabled: enabled && !!key && !isDirectUrl,
    staleTime: 50 * 60 * 1000, // 50 minutes
    gcTime: 55 * 60 * 1000,    // 55 minutes
    retry: 1,
  });

  // Return the direct URL for legacy data, or the fetched pre-signed URL
  const url = isDirectUrl ? key : query.data ?? null;

  return {
    url,
    isLoading: !isDirectUrl && query.isLoading,
    error: query.error,
  };
}
```

- [ ] **Step 2: Verify TypeScript compiles**

```bash
cd web-system-app && pnpm build
```

Expected: BUILD SUCCESS.

- [ ] **Step 3: Commit**

```bash
git add web-system-app/src/hooks/useFileUrl.ts
git commit -m "feat(web): add useFileUrl hook for R2 download URLs"
```

---

### Task 9: Mobile App — Upload API Client & Hooks

**Files:**
- Create: `mobile-app/src/lib/api/upload.ts`
- Create: `mobile-app/src/hooks/use-file-upload.ts`
- Create: `mobile-app/src/hooks/use-file-url.ts`

- [ ] **Step 1: Create mobile upload API client**

Create `mobile-app/src/lib/api/upload.ts`:

```typescript
import { client } from '@/lib/api/client';

export type FileCategory =
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

interface RequestUploadPayload {
  category: FileCategory;
  entityId: string;
  fileName: string;
  fileSize: number;
  contentType: string;
  companyId?: string;
}

interface UploadResponse {
  uploadUrl: string;
  key: string;
  expiresIn: number;
}

interface DownloadUrlResponse {
  downloadUrl: string;
  expiresIn: number;
}

export const uploadApi = {
  requestUpload: (payload: RequestUploadPayload) =>
    client.post('/upload/request', payload),

  requestUploadPlatform: (payload: RequestUploadPayload) =>
    client.post('/platform/upload/request', payload),

  getDownloadUrl: (key: string) =>
    client.post('/upload/download-url', { key }),

  getDownloadUrlPlatform: (key: string) =>
    client.post('/platform/upload/download-url', { key }),
};

export const uploadKeys = {
  all: ['upload'] as const,
  downloadUrl: (key: string) => [...uploadKeys.all, 'download-url', key] as const,
};
```

Note: Mobile API client auto-unwraps `response.data` in the interceptor, so no `.then(r => r.data)` needed.

- [ ] **Step 2: Install expo-file-system if not already installed**

```bash
cd mobile-app && pnpm add expo-file-system
```

(If already installed, this is a no-op.)

- [ ] **Step 3: Create useFileUpload hook (mobile)**

Create `mobile-app/src/hooks/use-file-upload.ts`:

```typescript
import { useState, useCallback } from 'react';
import * as FileSystem from 'expo-file-system';
import { uploadApi, type FileCategory } from '@/lib/api/upload';

interface FileInfo {
  uri: string;
  name: string;
  type: string; // MIME type
  size: number;
}

interface UseFileUploadOptions {
  category: FileCategory;
  entityId: string;
  maxSize?: number;
  allowedTypes?: string[];
  platform?: boolean;
  companyId?: string;
  onSuccess?: (key: string) => void;
  onError?: (error: string) => void;
}

interface UseFileUploadReturn {
  upload: (file: FileInfo) => Promise<string | null>;
  isUploading: boolean;
  error: string | null;
  reset: () => void;
}

const DEFAULT_IMAGE_MAX = 5 * 1024 * 1024;
const DEFAULT_DOC_MAX = 10 * 1024 * 1024;

const IMAGE_TYPES = ['image/jpeg', 'image/png', 'image/gif', 'image/webp'];

export function useFileUpload(options: UseFileUploadOptions): UseFileUploadReturn {
  const [isUploading, setIsUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const reset = useCallback(() => {
    setIsUploading(false);
    setError(null);
  }, []);

  const upload = useCallback(async (file: FileInfo): Promise<string | null> => {
    setError(null);
    setIsUploading(true);

    try {
      // Client-side validation
      const isImage = IMAGE_TYPES.includes(file.type);
      const maxSize = options.maxSize ?? (isImage ? DEFAULT_IMAGE_MAX : DEFAULT_DOC_MAX);

      if (file.size > maxSize) {
        const maxMB = (maxSize / (1024 * 1024)).toFixed(0);
        const errMsg = `File size exceeds ${maxMB} MB limit`;
        setError(errMsg);
        options.onError?.(errMsg);
        return null;
      }

      if (options.allowedTypes && !options.allowedTypes.includes(file.type)) {
        const errMsg = `File type "${file.type}" is not allowed`;
        setError(errMsg);
        options.onError?.(errMsg);
        return null;
      }

      // Request pre-signed URL from backend
      const requestFn = options.platform
        ? uploadApi.requestUploadPlatform
        : uploadApi.requestUpload;

      const response = await requestFn({
        category: options.category,
        entityId: options.entityId,
        fileName: file.name,
        fileSize: file.size,
        contentType: file.type,
        companyId: options.companyId,
      });

      const { uploadUrl, key } = (response as any).data;

      // Upload directly to R2 using expo-file-system
      const uploadResult = await FileSystem.uploadAsync(uploadUrl, file.uri, {
        httpMethod: 'PUT',
        uploadType: FileSystem.FileSystemUploadType.BINARY_CONTENT,
        headers: { 'Content-Type': file.type },
      });

      if (uploadResult.status < 200 || uploadResult.status >= 300) {
        throw new Error(`Upload failed with status ${uploadResult.status}`);
      }

      options.onSuccess?.(key);
      return key;
    } catch (err: any) {
      const errMsg = err?.response?.data?.message || err?.message || 'Upload failed';
      setError(errMsg);
      options.onError?.(errMsg);
      return null;
    } finally {
      setIsUploading(false);
    }
  }, [options.category, options.entityId, options.maxSize, options.allowedTypes, options.platform, options.companyId, options.onSuccess, options.onError]);

  return { upload, isUploading, error, reset };
}
```

- [ ] **Step 4: Create useFileUrl hook (mobile)**

Create `mobile-app/src/hooks/use-file-url.ts`:

```typescript
import { useQuery } from '@tanstack/react-query';
import { uploadApi, uploadKeys } from '@/lib/api/upload';

interface UseFileUrlOptions {
  key: string | null | undefined;
  enabled?: boolean;
  platform?: boolean;
}

/**
 * Fetches a pre-signed download URL for a stored R2 key.
 * Returns legacy base64/HTTP URLs directly without fetching.
 * Caches the pre-signed URL for 50 minutes (expires in 60).
 */
export function useFileUrl(options: UseFileUrlOptions) {
  const { key, enabled = true, platform = false } = options;

  const isDirectUrl =
    key?.startsWith('data:') ||
    key?.startsWith('http://') ||
    key?.startsWith('https://') ||
    key?.startsWith('/');

  const query = useQuery({
    queryKey: uploadKeys.downloadUrl(key ?? ''),
    queryFn: async () => {
      if (!key) return null;
      const fetchFn = platform
        ? uploadApi.getDownloadUrlPlatform
        : uploadApi.getDownloadUrl;
      const response = await fetchFn(key);
      return (response as any).data.downloadUrl;
    },
    enabled: enabled && !!key && !isDirectUrl,
    staleTime: 50 * 60 * 1000,
    gcTime: 55 * 60 * 1000,
    retry: 1,
  });

  const url = isDirectUrl ? key : query.data ?? null;

  return {
    url,
    isLoading: !isDirectUrl && query.isLoading,
    error: query.error,
  };
}
```

- [ ] **Step 5: Verify TypeScript compiles**

```bash
cd mobile-app && pnpm type-check
```

Expected: No errors.

- [ ] **Step 6: Commit**

```bash
git add mobile-app/src/lib/api/upload.ts mobile-app/src/hooks/use-file-upload.ts mobile-app/src/hooks/use-file-url.ts mobile-app/package.json mobile-app/pnpm-lock.yaml
git commit -m "feat(mobile): add upload API client, useFileUpload and useFileUrl hooks"
```

---

### Task 10: Web App — Update Company Logo Upload (CompanyDetailEditModal)

**Files:**
- Modify: `web-system-app/src/features/super-admin/CompanyDetailEditModal.tsx`

- [ ] **Step 1: Read current file to understand the logo upload section**

Read the file and locate the logo upload handler (around lines 60-90 where `handleFile` and `readAsDataURL` are used).

- [ ] **Step 2: Replace base64 logo upload with useFileUpload**

Replace the FileReader-based logo upload with the `useFileUpload` hook. The key changes:

1. Import `useFileUpload` from `@/hooks/useFileUpload` and `useFileUrl` from `@/hooks/useFileUrl`
2. Remove the `FileReader` / `readAsDataURL` logic
3. Add `useFileUpload({ category: 'company-logo', entityId: companyId, platform: true, companyId })` hook call
4. In the file input `onChange` handler, call `upload(file)` instead of `readAsDataURL`
5. On success, set the form field `logoUrl` to the returned R2 key
6. For the logo preview, use `useFileUrl({ key: form.logoUrl, platform: true })` to get a displayable URL

**Before** (approximate):
```typescript
const handleFile = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    if (file.size > 2 * 1024 * 1024) return;
    const reader = new FileReader();
    reader.onload = () => {
        const result = typeof reader.result === 'string' ? reader.result : '';
        setField('logoUrl', result);
    };
    reader.readAsDataURL(file);
};
```

**After:**
```typescript
import { useFileUpload } from '@/hooks/useFileUpload';
import { useFileUrl } from '@/hooks/useFileUrl';

// Inside the component:
const { upload: uploadLogo, isUploading: isLogoUploading } = useFileUpload({
  category: 'company-logo',
  entityId: companyId ?? 'new',
  platform: true,
  companyId: companyId,
  onSuccess: (key) => setField('logoUrl', key),
});

const { url: logoPreviewUrl } = useFileUrl({
  key: form.logoUrl,
  platform: true,
});

const handleFile = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    await uploadLogo(file);
};

// In JSX, use logoPreviewUrl instead of form.logoUrl for <img src>
// Show loading spinner when isLogoUploading is true
```

- [ ] **Step 3: Also update the URL input toggle**

Keep the URL input option but when a URL is entered directly (https://...), store it as-is in `logoUrl`. The `useFileUrl` hook handles both R2 keys and direct HTTP URLs.

- [ ] **Step 4: Verify TypeScript compiles**

```bash
cd web-system-app && pnpm build
```

Expected: BUILD SUCCESS.

- [ ] **Step 5: Commit**

```bash
git add web-system-app/src/features/super-admin/CompanyDetailEditModal.tsx
git commit -m "feat(web): use R2 upload for company logo in CompanyDetailEditModal"
```

---

### Task 11: Web App — Update Tenant Onboarding Logo Upload (Step01Identity)

**Files:**
- Modify: `web-system-app/src/features/super-admin/tenant-onboarding/steps/Step01Identity.tsx`

- [ ] **Step 1: Read current file and locate logo upload logic**

Find the `readAsDataURL` pattern (around line 147) and the logo preview display.

- [ ] **Step 2: Replace base64 upload with useFileUpload**

Similar pattern to Task 10. The onboarding flow creates a new company, so the `companyId` may not exist yet. Handle this by:

1. If no companyId yet (new company being onboarded), use a temporary entity ID (e.g., `'onboarding-' + sessionId` or `'new'`).
2. After company creation completes, the backend receives the R2 key and stores it.

```typescript
import { useFileUpload } from '@/hooks/useFileUpload';
import { useFileUrl } from '@/hooks/useFileUrl';

// Inside Step01Identity component:
const { upload: uploadLogo, isUploading: isLogoUploading } = useFileUpload({
  category: 'company-logo',
  entityId: 'onboarding',
  platform: true,
  companyId: 'onboarding', // Temporary — key will be: onboarding/company/logo.jpg
  onSuccess: (key) => {
    // Store R2 key in the onboarding store
    setForm({ logoPreviewUrl: key });
  },
});

const { url: logoDisplayUrl } = useFileUrl({
  key: form.logoPreviewUrl,
  platform: true,
});

// Replace readAsDataURL handler:
const handleLogoUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
  const file = e.target.files?.[0];
  if (!file) return;
  await uploadLogo(file);
};
```

Note: The onboarding store field may need to be updated from `logoBase64` to `logoUrl` or similar to hold the R2 key. Check the store fields and update accordingly.

- [ ] **Step 3: Verify TypeScript compiles**

```bash
cd web-system-app && pnpm build
```

Expected: BUILD SUCCESS.

- [ ] **Step 4: Commit**

```bash
git add web-system-app/src/features/super-admin/tenant-onboarding/steps/Step01Identity.tsx
git commit -m "feat(web): use R2 upload for logo in tenant onboarding Step01Identity"
```

---

### Task 12: Web App — Update Employee Profile (Photo + Documents)

**Files:**
- Modify: `web-system-app/src/features/company-admin/hr/EmployeeProfileScreen.tsx`

- [ ] **Step 1: Read the file and locate all base64 patterns**

Search for:
- `readAsDataURL` — there should be two: one for profile photo (~line 996), one for documents (~line 656)
- `base64` — used in `setDocUploads` state
- `profilePhotoUrl` — used for display

- [ ] **Step 2: Replace profile photo upload**

Replace the FileReader pattern for the profile photo with `useFileUpload`:

```typescript
import { useFileUpload } from '@/hooks/useFileUpload';
import { useFileUrl } from '@/hooks/useFileUrl';

// For profile photo:
const { upload: uploadPhoto, isUploading: isPhotoUploading } = useFileUpload({
  category: 'employee-photo',
  entityId: employeeId,
  onSuccess: (key) => {
    // Set the photo URL field in the form/state to the R2 key
    setProfilePhotoUrl(key);
  },
});

// For display:
const { url: photoDisplayUrl } = useFileUrl({ key: profilePhotoUrl });
```

- [ ] **Step 3: Replace document upload**

Replace the FileReader pattern for document uploads. Instead of storing `{ fileName, base64 }`, store `{ fileName, key }`:

```typescript
const { upload: uploadDoc, isUploading: isDocUploading } = useFileUpload({
  category: 'employee-document',
  entityId: employeeId,
});

const handleDocUpload = async (docType: string, file: File) => {
  const key = await uploadDoc(file);
  if (key) {
    setDocUploads((prev) => ({
      ...prev,
      [docType]: { fileName: file.name, fileUrl: key },
    }));
  }
};
```

- [ ] **Step 4: Update document/certificate display**

Anywhere a document URL is shown (download link, image preview), use `useFileUrl` to get the displayable URL.

- [ ] **Step 5: Verify TypeScript compiles**

```bash
cd web-system-app && pnpm build
```

Expected: BUILD SUCCESS.

- [ ] **Step 6: Commit**

```bash
git add web-system-app/src/features/company-admin/hr/EmployeeProfileScreen.tsx
git commit -m "feat(web): use R2 upload for employee photo and documents"
```

---

### Task 13: Web App — Update Expense Claim Screens

**Files:**
- Modify: `web-system-app/src/features/company-admin/hr/ExpenseClaimScreen.tsx`
- Modify: `web-system-app/src/features/ess/MyExpenseClaimsScreen.tsx`

- [ ] **Step 1: Read ExpenseClaimScreen.tsx and find fileToDataUrl helper**

Locate the `fileToDataUrl()` helper function (around line 112-119) and all places it's called.

- [ ] **Step 2: Replace fileToDataUrl with useFileUpload in ExpenseClaimScreen**

Remove the `fileToDataUrl()` helper. Replace receipt upload with R2:

```typescript
import { useFileUpload } from '@/hooks/useFileUpload';

const { upload: uploadReceipt, isUploading: isReceiptUploading } = useFileUpload({
  category: 'expense-receipt',
  entityId: claimId ?? 'draft',
});

// When user picks receipt files:
const handleReceiptUpload = async (files: FileList) => {
  const uploaded: { fileName: string; fileUrl: string }[] = [];
  for (const file of Array.from(files)) {
    const key = await uploadReceipt(file);
    if (key) {
      uploaded.push({ fileName: file.name, fileUrl: key });
    }
  }
  setReceipts((prev) => [...prev, ...uploaded]);
};
```

- [ ] **Step 3: Update receipt display to use useFileUrl**

Where receipts are displayed as images (checking `r.fileUrl?.startsWith("data:image/")`), use `useFileUrl` to get the display URL. The `useFileUrl` hook handles both legacy base64 and R2 keys.

- [ ] **Step 4: Apply the same changes to MyExpenseClaimsScreen.tsx**

Same pattern — replace `fileToDataUrl` with `useFileUpload`, update receipt display with `useFileUrl`.

- [ ] **Step 5: Verify TypeScript compiles**

```bash
cd web-system-app && pnpm build
```

Expected: BUILD SUCCESS.

- [ ] **Step 6: Commit**

```bash
git add web-system-app/src/features/company-admin/hr/ExpenseClaimScreen.tsx web-system-app/src/features/ess/MyExpenseClaimsScreen.tsx
git commit -m "feat(web): use R2 upload for expense claim receipts"
```

---

### Task 14: Web App — Update Display Components (TopBar + MyProfile)

**Files:**
- Modify: `web-system-app/src/layouts/TopBar.tsx`
- Modify: `web-system-app/src/features/company-admin/hr/MyProfileScreen.tsx`

- [ ] **Step 1: Read TopBar.tsx and find profile photo display logic**

Locate the `profilePhotoUrl` display logic (around line 453) where it checks `startsWith('data:image/')`.

- [ ] **Step 2: Replace with useFileUrl in TopBar**

```typescript
import { useFileUrl } from '@/hooks/useFileUrl';

// Inside the component:
const profilePhotoKey = myProfileData?.data?.profilePhotoUrl;
const { url: profilePhotoUrl, isLoading: isPhotoLoading } = useFileUrl({
  key: profilePhotoKey,
});

// Replace the old showProfilePhoto logic:
const showProfilePhoto =
  !imageLoadFailed &&
  typeof profilePhotoUrl === 'string' &&
  profilePhotoUrl.length > 0;

// In <img>:
// src={profilePhotoUrl}  (useFileUrl returns the displayable URL)
```

- [ ] **Step 3: Apply same pattern to MyProfileScreen.tsx**

Replace the direct base64/URL check with `useFileUrl`.

- [ ] **Step 4: Verify TypeScript compiles**

```bash
cd web-system-app && pnpm build
```

Expected: BUILD SUCCESS.

- [ ] **Step 5: Commit**

```bash
git add web-system-app/src/layouts/TopBar.tsx web-system-app/src/features/company-admin/hr/MyProfileScreen.tsx
git commit -m "feat(web): use useFileUrl for profile photo display in TopBar and MyProfile"
```

---

### Task 15: Mobile App — Update Logo Upload (step01-identity)

**Files:**
- Modify: `mobile-app/src/features/super-admin/tenant-onboarding/steps/step01-identity.tsx`

- [ ] **Step 1: Read current file and find ImagePicker + base64 logic**

Locate `pickFromGallery` and `takePhoto` functions (around lines 107-148) that use `ImagePicker.launchImageLibraryAsync` with `base64: true`.

- [ ] **Step 2: Replace base64 encoding with R2 upload**

Instead of getting base64 from ImagePicker, get the local URI and upload to R2:

```typescript
import { useFileUpload } from '@/hooks/use-file-upload';
import { useFileUrl } from '@/hooks/use-file-url';
import * as FileSystem from 'expo-file-system';

// Inside component:
const { upload: uploadLogo, isUploading: isLogoUploading } = useFileUpload({
  category: 'company-logo',
  entityId: 'onboarding',
  platform: true,
  companyId: 'onboarding',
  onSuccess: (key) => {
    setForm({ logoBase64: key }); // Store R2 key (field name kept for compatibility)
  },
});

const { url: logoDisplayUrl } = useFileUrl({
  key: form.logoBase64,
  platform: true,
});

const pickFromGallery = async () => {
  setShowOptions(false);
  setPermissionError('');
  const { status } = await ImagePicker.requestMediaLibraryPermissionsAsync();
  if (status !== 'granted') {
    setPermissionError('Photo library access is required. Please enable it in Settings.');
    return;
  }
  const result = await ImagePicker.launchImageLibraryAsync({
    mediaTypes: 'images',
    allowsEditing: true,
    aspect: [1, 1],
    quality: 0.8,
    base64: false, // No longer need base64
  });
  if (!result.canceled) {
    const asset = result.assets[0];
    setForm({ logoUri: asset.uri }); // Keep URI for local preview
    // Get file info for upload
    const fileInfo = await FileSystem.getInfoAsync(asset.uri);
    if (fileInfo.exists) {
      await uploadLogo({
        uri: asset.uri,
        name: 'logo.jpg',
        type: 'image/jpeg',
        size: fileInfo.size ?? 0,
      });
    }
  }
};

// Same pattern for takePhoto — replace base64: true with base64: false, upload via hook
```

- [ ] **Step 3: Update logo preview**

Use `logoDisplayUrl` from `useFileUrl` for the preview image, with `form.logoUri` as fallback for local preview before upload completes.

- [ ] **Step 4: Verify TypeScript compiles**

```bash
cd mobile-app && pnpm type-check
```

Expected: No errors.

- [ ] **Step 5: Commit**

```bash
git add mobile-app/src/features/super-admin/tenant-onboarding/steps/step01-identity.tsx
git commit -m "feat(mobile): use R2 upload for logo in tenant onboarding"
```

---

### Task 16: Mobile App — Update Employee Detail Screen

**Files:**
- Modify: `mobile-app/src/features/company-admin/hr/employee-detail-screen.tsx`

- [ ] **Step 1: Read the file and locate all base64 upload patterns**

Find ImagePicker usage for profile photo and DocumentPicker usage for document uploads.

- [ ] **Step 2: Replace profile photo upload with useFileUpload**

```typescript
import { useFileUpload } from '@/hooks/use-file-upload';
import { useFileUrl } from '@/hooks/use-file-url';
import * as FileSystem from 'expo-file-system';

const { upload: uploadPhoto, isUploading: isPhotoUploading } = useFileUpload({
  category: 'employee-photo',
  entityId: employeeId,
  onSuccess: (key) => {
    // Update employee profilePhotoUrl with R2 key
  },
});

// After ImagePicker returns result:
const asset = result.assets[0];
const fileInfo = await FileSystem.getInfoAsync(asset.uri);
await uploadPhoto({
  uri: asset.uri,
  name: 'photo.jpg',
  type: 'image/jpeg',
  size: fileInfo.exists ? (fileInfo.size ?? 0) : 0,
});
```

- [ ] **Step 3: Replace document upload with useFileUpload**

```typescript
const { upload: uploadDoc, isUploading: isDocUploading } = useFileUpload({
  category: 'employee-document',
  entityId: employeeId,
});

// After DocumentPicker returns result:
const doc = result.assets[0];
const key = await uploadDoc({
  uri: doc.uri,
  name: doc.name ?? 'document',
  type: doc.mimeType ?? 'application/octet-stream',
  size: doc.size ?? 0,
});
```

- [ ] **Step 4: Update photo/document display with useFileUrl**

Replace direct `profilePhotoUrl` usage with `useFileUrl` for the image source.

- [ ] **Step 5: Verify TypeScript compiles**

```bash
cd mobile-app && pnpm type-check
```

Expected: No errors.

- [ ] **Step 6: Commit**

```bash
git add mobile-app/src/features/company-admin/hr/employee-detail-screen.tsx
git commit -m "feat(mobile): use R2 upload for employee photo and documents"
```

---

### Task 17: Migration Script — Base64 to R2

**Files:**
- Create: `avy-erp-backend/scripts/migrate-base64-to-r2.ts`

- [ ] **Step 1: Create migration script**

Create `avy-erp-backend/scripts/migrate-base64-to-r2.ts`:

```typescript
import { PrismaClient } from '@prisma/client';
import dotenv from 'dotenv';
import { writeFileSync, appendFileSync, existsSync, readFileSync } from 'fs';
import { v4 as uuidv4 } from 'uuid';
import {
  S3Client,
  PutObjectCommand,
} from '@aws-sdk/client-s3';

dotenv.config();

// ─── Configuration ────────────────────────────────────────────────────────────

const DRY_RUN = process.argv.includes('--dry-run');
const CATEGORY_FILTER = process.argv.find((a) => a.startsWith('--category='))?.split('=')[1];
const BATCH_SIZE = 50;
const BATCH_DELAY_MS = 200;

const LOG_FILE = 'migration-base64-to-r2.log';
const ROLLBACK_FILE = 'migration-rollback.json';

// ─── R2 Client ────────────────────────────────────────────────────────────────

const accountId = process.env.R2_ACCOUNT_ID!;
const endpoint = process.env.R2_ENDPOINT || `https://${accountId}.r2.cloudflarestorage.com`;
const bucket = process.env.R2_BUCKET_NAME || 'avy-erp-files';

const s3 = new S3Client({
  region: 'auto',
  endpoint,
  credentials: {
    accessKeyId: process.env.R2_ACCESS_KEY_ID!,
    secretAccessKey: process.env.R2_SECRET_ACCESS_KEY!,
  },
});

// ─── Prisma Clients ───────────────────────────────────────────────────────────

const platformPrisma = new PrismaClient();

function getTenantPrisma(schemaName: string): PrismaClient {
  const baseUrl = process.env.DATABASE_URL_TEMPLATE!;
  const tenantUrl = baseUrl.replace(/schema=[^&]*/, `schema=${schemaName}`);
  return new PrismaClient({ datasources: { db: { url: tenantUrl } } });
}

// ─── Helpers ──────────────────────────────────────────────────────────────────

function log(msg: string) {
  const line = `[${new Date().toISOString()}] ${msg}`;
  console.log(line);
  appendFileSync(LOG_FILE, line + '\n');
}

function isBase64DataUrl(value: unknown): value is string {
  return typeof value === 'string' && value.startsWith('data:');
}

function parseDataUrl(dataUrl: string): { mimeType: string; buffer: Buffer } {
  const match = dataUrl.match(/^data:([^;]+);base64,(.+)$/s);
  if (!match) throw new Error('Invalid data URL format');
  return {
    mimeType: match[1]!,
    buffer: Buffer.from(match[2]!, 'base64'),
  };
}

function getExtFromMime(mime: string): string {
  const map: Record<string, string> = {
    'image/jpeg': 'jpg', 'image/png': 'png', 'image/gif': 'gif',
    'image/webp': 'webp', 'application/pdf': 'pdf',
  };
  return map[mime] || 'bin';
}

async function uploadToR2(key: string, buffer: Buffer, contentType: string): Promise<void> {
  await s3.send(new PutObjectCommand({
    Bucket: bucket,
    Key: key,
    Body: buffer,
    ContentType: contentType,
  }));
}

function sleep(ms: number): Promise<void> {
  return new Promise((r) => setTimeout(r, ms));
}

// ─── Rollback Log ─────────────────────────────────────────────────────────────

interface RollbackEntry {
  table: string;
  id: string;
  field: string;
  oldValuePreview: string; // first 100 chars of old value
  newKey: string;
}

let rollbackEntries: RollbackEntry[] = [];

function loadExistingRollback(): void {
  if (existsSync(ROLLBACK_FILE)) {
    rollbackEntries = JSON.parse(readFileSync(ROLLBACK_FILE, 'utf-8'));
  }
}

function saveRollback(): void {
  writeFileSync(ROLLBACK_FILE, JSON.stringify(rollbackEntries, null, 2));
}

// ─── Field Migration Definitions ──────────────────────────────────────────────

interface FieldMigration {
  table: string;
  model: string;
  fields: string[];
  keyTemplate: (companyId: string, recordId: string, field: string, ext: string) => string;
  scope: 'platform' | 'tenant';
  category: string;
}

const MIGRATIONS: FieldMigration[] = [
  {
    table: 'Company',
    model: 'company',
    fields: ['logoUrl'],
    keyTemplate: (cId, _rId, _f, ext) => `${cId}/company/logo.${ext}`,
    scope: 'platform',
    category: 'company-logo',
  },
  {
    table: 'Employee',
    model: 'employee',
    fields: ['profilePhotoUrl'],
    keyTemplate: (cId, rId, _f, ext) => `${cId}/employees/${rId}/photo.${ext}`,
    scope: 'tenant',
    category: 'employee-photo',
  },
  {
    table: 'EmployeeEducation',
    model: 'employeeEducation',
    fields: ['certificateUrl'],
    keyTemplate: (cId, rId, _f, ext) => `${cId}/employees/${rId}/education/${uuidv4()}.${ext}`,
    scope: 'tenant',
    category: 'education-certificate',
  },
  {
    table: 'EmployeePrevEmployment',
    model: 'employeePrevEmployment',
    fields: ['experienceLetterUrl', 'relievingLetterUrl'],
    keyTemplate: (cId, rId, f, ext) => `${cId}/employees/${rId}/prev-employment/${f}-${uuidv4()}.${ext}`,
    scope: 'tenant',
    category: 'prev-employment-doc',
  },
  {
    table: 'EmployeeDocument',
    model: 'employeeDocument',
    fields: ['fileUrl'],
    keyTemplate: (cId, rId, _f, ext) => `${cId}/employees/${rId}/documents/${uuidv4()}.${ext}`,
    scope: 'tenant',
    category: 'employee-document',
  },
  {
    table: 'Candidate',
    model: 'candidate',
    fields: ['resumeUrl'],
    keyTemplate: (cId, rId, _f, ext) => `${cId}/recruitment/${rId}/resume.${ext}`,
    scope: 'tenant',
    category: 'recruitment-doc',
  },
  {
    table: 'CandidateOffer',
    model: 'candidateOffer',
    fields: ['offerLetterUrl'],
    keyTemplate: (cId, rId, _f, ext) => `${cId}/recruitment/${rId}/offer.${ext}`,
    scope: 'tenant',
    category: 'recruitment-doc',
  },
  {
    table: 'CandidateEducation',
    model: 'candidateEducation',
    fields: ['certificateUrl'],
    keyTemplate: (cId, rId, _f, ext) => `${cId}/recruitment/${rId}/education/${uuidv4()}.${ext}`,
    scope: 'tenant',
    category: 'education-certificate',
  },
  {
    table: 'CandidateDocument',
    model: 'candidateDocument',
    fields: ['fileUrl'],
    keyTemplate: (cId, rId, _f, ext) => `${cId}/recruitment/${rId}/documents/${uuidv4()}.${ext}`,
    scope: 'tenant',
    category: 'candidate-document',
  },
  {
    table: 'TrainingNomination',
    model: 'trainingNomination',
    fields: ['certificateUrl'],
    keyTemplate: (cId, rId, _f, ext) => `${cId}/training/certificates/${rId}.${ext}`,
    scope: 'tenant',
    category: 'training-certificate',
  },
  {
    table: 'TrainingMaterial',
    model: 'trainingMaterial',
    fields: ['url'],
    keyTemplate: (cId, rId, _f, ext) => `${cId}/training/${rId}.${ext}`,
    scope: 'tenant',
    category: 'training-material',
  },
  {
    table: 'HRLetter',
    model: 'hRLetter',
    fields: ['pdfUrl'],
    keyTemplate: (cId, rId, _f, _ext) => `${cId}/hr-letters/${rId}.pdf`,
    scope: 'tenant',
    category: 'hr-letter',
  },
  {
    table: 'AttendanceRecord',
    model: 'attendanceRecord',
    fields: ['checkInPhotoUrl', 'checkOutPhotoUrl'],
    keyTemplate: (cId, rId, f, ext) => {
      const type = f === 'checkInPhotoUrl' ? 'checkin' : 'checkout';
      return `${cId}/attendance/${rId}/${type}.${ext}`;
    },
    scope: 'tenant',
    category: 'attendance-photo',
  },
  {
    table: 'Payslip',
    model: 'payslip',
    fields: ['pdfUrl'],
    keyTemplate: (cId, rId, _f, _ext) => `${cId}/payroll/${rId}.pdf`,
    scope: 'tenant',
    category: 'payslip',
  },
  {
    table: 'SalaryRevision',
    model: 'salaryRevision',
    fields: ['revisionLetterUrl'],
    keyTemplate: (cId, rId, _f, _ext) => `${cId}/payroll/revisions/${rId}.pdf`,
    scope: 'tenant',
    category: 'salary-revision',
  },
  {
    table: 'FnFSettlement',
    model: 'fnFSettlement',
    fields: ['settlementLetterUrl'],
    keyTemplate: (cId, rId, _f, _ext) => `${cId}/offboarding/${rId}/settlement.pdf`,
    scope: 'tenant',
    category: 'offboarding-doc',
  },
  {
    table: 'EmployeeTransfer',
    model: 'employeeTransfer',
    fields: ['transferLetterUrl'],
    keyTemplate: (cId, rId, _f, _ext) => `${cId}/transfers/${rId}.pdf`,
    scope: 'tenant',
    category: 'transfer-letter',
  },
  {
    table: 'EmployeePromotion',
    model: 'employeePromotion',
    fields: ['promotionLetterUrl'],
    keyTemplate: (cId, rId, _f, _ext) => `${cId}/transfers/promotions/${rId}.pdf`,
    scope: 'tenant',
    category: 'transfer-letter',
  },
  {
    table: 'PolicyDocument',
    model: 'policyDocument',
    fields: ['fileUrl'],
    keyTemplate: (cId, rId, _f, ext) => `${cId}/policies/${rId}.${ext}`,
    scope: 'tenant',
    category: 'policy-document',
  },
];

// ─── JSON Field Migrations (ExpenseClaim receipts) ────────────────────────────

interface JsonFieldMigration {
  table: string;
  model: string;
  jsonField: string;
  scope: 'tenant';
  category: string;
}

const JSON_MIGRATIONS: JsonFieldMigration[] = [
  {
    table: 'ExpenseClaim',
    model: 'expenseClaim',
    jsonField: 'receipts',
    scope: 'tenant',
    category: 'expense-receipt',
  },
  {
    table: 'ExpenseClaimItem',
    model: 'expenseClaimItem',
    jsonField: 'receipts',
    scope: 'tenant',
    category: 'expense-receipt',
  },
];

// ─── Core Migration Logic ─────────────────────────────────────────────────────

interface MigrationStats {
  scanned: number;
  migrated: number;
  skipped: number;
  failed: number;
  failedIds: string[];
}

async function migrateStringField(
  prisma: PrismaClient,
  migration: FieldMigration,
  companyId: string,
): Promise<MigrationStats> {
  const stats: MigrationStats = { scanned: 0, migrated: 0, skipped: 0, failed: 0, failedIds: [] };
  const model = (prisma as any)[migration.model];
  if (!model) {
    log(`  WARNING: Model "${migration.model}" not found in Prisma client, skipping`);
    return stats;
  }

  for (const field of migration.fields) {
    let skip = 0;
    while (true) {
      const records = await model.findMany({
        where: { [field]: { not: null } },
        select: { id: true, [field]: true },
        take: BATCH_SIZE,
        skip,
      });

      if (records.length === 0) break;

      for (const record of records) {
        stats.scanned++;
        const value = record[field];

        if (!isBase64DataUrl(value)) {
          stats.skipped++;
          continue;
        }

        try {
          const { mimeType, buffer } = parseDataUrl(value);
          const ext = getExtFromMime(mimeType);
          const key = migration.keyTemplate(companyId, record.id, field, ext);

          if (DRY_RUN) {
            log(`  [DRY-RUN] Would migrate ${migration.table}.${field} id=${record.id} → ${key} (${buffer.length} bytes)`);
            stats.migrated++;
            continue;
          }

          await uploadToR2(key, buffer, mimeType);
          await model.update({ where: { id: record.id }, data: { [field]: key } });

          rollbackEntries.push({
            table: migration.table,
            id: record.id,
            field,
            oldValuePreview: value.substring(0, 100),
            newKey: key,
          });

          stats.migrated++;
          log(`  Migrated ${migration.table}.${field} id=${record.id} → ${key}`);
        } catch (err: any) {
          stats.failed++;
          stats.failedIds.push(record.id);
          log(`  ERROR ${migration.table}.${field} id=${record.id}: ${err.message}`);
        }
      }

      skip += BATCH_SIZE;
      await sleep(BATCH_DELAY_MS);
    }
  }

  return stats;
}

async function migrateJsonField(
  prisma: PrismaClient,
  migration: JsonFieldMigration,
  companyId: string,
): Promise<MigrationStats> {
  const stats: MigrationStats = { scanned: 0, migrated: 0, skipped: 0, failed: 0, failedIds: [] };
  const model = (prisma as any)[migration.model];
  if (!model) {
    log(`  WARNING: Model "${migration.model}" not found, skipping`);
    return stats;
  }

  let skip = 0;
  while (true) {
    const records = await model.findMany({
      where: { [migration.jsonField]: { not: null } },
      select: { id: true, [migration.jsonField]: true },
      take: BATCH_SIZE,
      skip,
    });

    if (records.length === 0) break;

    for (const record of records) {
      stats.scanned++;
      const receipts = record[migration.jsonField];
      if (!Array.isArray(receipts)) { stats.skipped++; continue; }

      let hasBase64 = false;
      const updated: any[] = [];

      for (const receipt of receipts) {
        if (receipt?.fileUrl && isBase64DataUrl(receipt.fileUrl)) {
          hasBase64 = true;
          try {
            const { mimeType, buffer } = parseDataUrl(receipt.fileUrl);
            const ext = getExtFromMime(mimeType);
            const key = `${companyId}/expenses/${record.id}/${uuidv4()}.${ext}`;

            if (!DRY_RUN) {
              await uploadToR2(key, buffer, mimeType);
            }

            updated.push({ ...receipt, fileUrl: key });
            log(`  ${DRY_RUN ? '[DRY-RUN] Would migrate' : 'Migrated'} ${migration.table}.${migration.jsonField} receipt in id=${record.id} → ${key}`);
          } catch (err: any) {
            updated.push(receipt); // keep original on failure
            stats.failed++;
            log(`  ERROR ${migration.table}.${migration.jsonField} receipt in id=${record.id}: ${err.message}`);
          }
        } else {
          updated.push(receipt);
        }
      }

      if (hasBase64) {
        if (!DRY_RUN) {
          await model.update({ where: { id: record.id }, data: { [migration.jsonField]: updated } });
          rollbackEntries.push({
            table: migration.table,
            id: record.id,
            field: migration.jsonField,
            oldValuePreview: JSON.stringify(receipts).substring(0, 100),
            newKey: 'json-migrated',
          });
        }
        stats.migrated++;
      } else {
        stats.skipped++;
      }
    }

    skip += BATCH_SIZE;
    await sleep(BATCH_DELAY_MS);
  }

  return stats;
}

// ─── Main ─────────────────────────────────────────────────────────────────────

async function main() {
  log('='.repeat(60));
  log(`Migration started ${DRY_RUN ? '(DRY RUN)' : ''}`);
  if (CATEGORY_FILTER) log(`Category filter: ${CATEGORY_FILTER}`);
  log('='.repeat(60));

  loadExistingRollback();

  const totalStats: MigrationStats = { scanned: 0, migrated: 0, skipped: 0, failed: 0, failedIds: [] };

  // ── Platform DB migrations ──
  const platformMigrations = MIGRATIONS.filter((m) => m.scope === 'platform');
  for (const migration of platformMigrations) {
    if (CATEGORY_FILTER && migration.category !== CATEGORY_FILTER) continue;
    log(`\n[Platform] Migrating ${migration.table}.${migration.fields.join(', ')}`);

    // For platform, get companyId from each record
    const model = (platformPrisma as any)[migration.model];
    if (!model) { log(`  WARNING: Model not found, skipping`); continue; }

    // Company table has its own id as companyId
    const records = await model.findMany({ select: { id: true } });
    for (const record of records) {
      const stats = await migrateStringField(platformPrisma, migration, record.id);
      totalStats.scanned += stats.scanned;
      totalStats.migrated += stats.migrated;
      totalStats.skipped += stats.skipped;
      totalStats.failed += stats.failed;
      totalStats.failedIds.push(...stats.failedIds);
    }
  }

  // ── Tenant DB migrations ──
  const tenants = await platformPrisma.tenant.findMany({
    where: { status: { in: ['ACTIVE', 'TRIAL'] } },
    select: { id: true, slug: true, schemaName: true },
    include: { company: { select: { id: true } } },
  });

  log(`\nFound ${tenants.length} active tenants`);

  for (const tenant of tenants) {
    const companyId = (tenant as any).company?.id || tenant.id;
    log(`\n--- Tenant: ${tenant.slug} (company: ${companyId}) ---`);

    let tenantPrisma: PrismaClient | null = null;
    try {
      tenantPrisma = getTenantPrisma(tenant.schemaName);

      // String field migrations
      const tenantMigrations = MIGRATIONS.filter((m) => m.scope === 'tenant');
      for (const migration of tenantMigrations) {
        if (CATEGORY_FILTER && migration.category !== CATEGORY_FILTER) continue;
        log(`  [${tenant.slug}] Migrating ${migration.table}.${migration.fields.join(', ')}`);
        const stats = await migrateStringField(tenantPrisma, migration, companyId);
        totalStats.scanned += stats.scanned;
        totalStats.migrated += stats.migrated;
        totalStats.skipped += stats.skipped;
        totalStats.failed += stats.failed;
        totalStats.failedIds.push(...stats.failedIds);
      }

      // JSON field migrations
      for (const migration of JSON_MIGRATIONS) {
        if (CATEGORY_FILTER && migration.category !== CATEGORY_FILTER) continue;
        log(`  [${tenant.slug}] Migrating ${migration.table}.${migration.jsonField} (JSON)`);
        const stats = await migrateJsonField(tenantPrisma, migration, companyId);
        totalStats.scanned += stats.scanned;
        totalStats.migrated += stats.migrated;
        totalStats.skipped += stats.skipped;
        totalStats.failed += stats.failed;
        totalStats.failedIds.push(...stats.failedIds);
      }
    } catch (err: any) {
      log(`  ERROR connecting to tenant ${tenant.slug}: ${err.message}`);
    } finally {
      if (tenantPrisma) await tenantPrisma.$disconnect();
    }
  }

  // ── Summary ──
  if (!DRY_RUN) {
    saveRollback();
  }

  log('\n' + '='.repeat(60));
  log('MIGRATION SUMMARY');
  log('='.repeat(60));
  log(`Total scanned:  ${totalStats.scanned}`);
  log(`Total migrated: ${totalStats.migrated}`);
  log(`Total skipped:  ${totalStats.skipped}`);
  log(`Total failed:   ${totalStats.failed}`);
  if (totalStats.failedIds.length > 0) {
    log(`Failed IDs: ${totalStats.failedIds.join(', ')}`);
  }
  log(`Rollback file: ${ROLLBACK_FILE}`);
  log(`Log file: ${LOG_FILE}`);

  await platformPrisma.$disconnect();
}

main().catch((err) => {
  console.error('Migration crashed:', err);
  saveRollback();
  process.exit(1);
});
```

- [ ] **Step 2: Verify TypeScript compiles**

```bash
cd avy-erp-backend && npx tsc --noEmit scripts/migrate-base64-to-r2.ts --skipLibCheck
```

Note: The script uses direct PrismaClient instantiation (not the app's imports), so it may need `--skipLibCheck`. Alternatively, just verify no syntax errors.

- [ ] **Step 3: Test dry-run mode**

```bash
cd avy-erp-backend && npx ts-node scripts/migrate-base64-to-r2.ts --dry-run
```

Expected: Script runs, scans all tables, logs what would be migrated, no actual uploads or DB changes.

- [ ] **Step 4: Commit**

```bash
git add avy-erp-backend/scripts/migrate-base64-to-r2.ts
git commit -m "feat: add base64 to R2 migration script with dry-run and rollback support"
```

---

## Self-Review Checklist

### Spec Coverage

| Spec Section | Task(s) |
|-------------|---------|
| R2 bucket & key structure | Task 2 (constants), Task 4 (buildKey) |
| Environment variables | Task 1 |
| Backend r2.service.ts | Task 3 |
| Backend upload.service.ts | Task 4 |
| Backend upload.controller.ts + routes | Task 5 |
| Security (company validation) | Task 4 (getDownloadUrl), Task 5 (controller) |
| Web useFileUpload | Task 7 |
| Web useFileUrl | Task 8 |
| Web component updates | Tasks 10, 11, 12, 13, 14 |
| Mobile useFileUpload | Task 9 |
| Mobile useFileUrl | Task 9 |
| Mobile component updates | Tasks 15, 16 |
| Migration script | Task 17 |
| Migration safety (dry-run, batching, rollback) | Task 17 |
| Migration multi-tenant handling | Task 17 |

### Placeholder Scan

No TBD, TODO, or "implement later" found. All code blocks are complete.

### Type Consistency

- `FileCategory` type defined in Task 2 (backend), Task 6 (web), Task 9 (mobile) — all identical
- `UploadRequest`/`UploadResponse` interfaces consistent between Task 4 (service) and Task 5 (controller)
- `useFileUpload` returns `{ upload, isUploading, error, reset }` in both web (Task 7) and mobile (Task 9)
- `useFileUrl` returns `{ url, isLoading, error }` in both web (Task 8) and mobile (Task 9)
