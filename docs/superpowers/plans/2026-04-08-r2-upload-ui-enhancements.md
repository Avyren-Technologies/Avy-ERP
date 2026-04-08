# R2 Upload UI Enhancements Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Upgrade 4 document management screens to use proper R2 file upload with drag-and-drop, matching the expense claims quality. Fix backend validators that reject R2 keys.

**Architecture:** Create a shared `FileUploadZone` component for drag-and-drop. Upgrade existing screens to use `useFileUpload` hook + the shared component. Add missing delete endpoints on backend. Fix Zod validators using `.url()` on R2 key fields.

**Tech Stack:** React, Tailwind CSS, `useFileUpload` hook, `useFileUrl` hook, `R2Link`, Zod, Express, Prisma

**Spec:** `docs/superpowers/specs/2026-04-08-r2-upload-ui-enhancements-design.md`

---

## File Structure

### Backend (avy-erp-backend)

| Action | File | Responsibility |
|--------|------|----------------|
| Modify | `src/modules/hr/ess/ess.validators.ts` | Fix `.url()` → `.min(1)` on fileUrl fields |
| Modify | `src/modules/hr/ess/ess.service.ts` | Add deleteMyDocument + deletePolicyDocument methods |
| Modify | `src/modules/hr/ess/ess.controller.ts` | Add deleteMyDocument + deletePolicyDocument handlers |
| Modify | `src/modules/hr/ess/ess.routes.ts` | Add DELETE routes |

### Web App (web-system-app)

| Action | File | Responsibility |
|--------|------|----------------|
| Create | `src/components/FileUploadZone.tsx` | Shared drag-and-drop upload zone component |
| Modify | `src/features/ess/MyDocumentsScreen.tsx` | Full redesign with modal + R2 upload |
| Modify | `src/features/company-admin/hr/CandidateDetailScreen.tsx` | Replace URL input with file upload in doc modal |
| Modify | `src/features/company-admin/hr/TrainingCatalogueScreen.tsx` | Replace URL input with file upload in material modal |
| Modify | `src/features/ess/PolicyDocumentsScreen.tsx` | Add admin upload modal |
| Modify | `src/lib/api/ess.ts` | Add deleteMyDocument + createPolicyDocument API methods |
| Modify | `src/features/company-admin/api/use-ess-mutations.ts` | Add useDeleteMyDocument + useCreatePolicyDocument hooks |
| Modify | `src/features/company-admin/api/index.ts` | Export new hooks |

---

### Task 1: Fix Backend Validators

**Files:**
- Modify: `avy-erp-backend/src/modules/hr/ess/ess.validators.ts:317-334`

- [ ] **Step 1: Fix uploadDocumentSchema**

In `avy-erp-backend/src/modules/hr/ess/ess.validators.ts`, change line 321:

```typescript
// Before:
fileUrl: z.string().url('Must be a valid URL'),
// After:
fileUrl: z.string().min(1, 'File is required'),
```

- [ ] **Step 2: Fix policyDocumentSchema**

In the same file, change line 331:

```typescript
// Before:
fileUrl: z.string().url('Must be a valid URL'),
// After:
fileUrl: z.string().min(1, 'File is required'),
```

- [ ] **Step 3: Verify backend builds**

```bash
cd avy-erp-backend && pnpm build
```

Expected: BUILD SUCCESS.

- [ ] **Step 4: Commit**

```bash
git add avy-erp-backend/src/modules/hr/ess/ess.validators.ts
git commit -m "fix: allow R2 keys in document upload validators (remove .url() check)"
```

---

### Task 2: Add Backend Delete Endpoints

**Files:**
- Modify: `avy-erp-backend/src/modules/hr/ess/ess.service.ts`
- Modify: `avy-erp-backend/src/modules/hr/ess/ess.controller.ts`
- Modify: `avy-erp-backend/src/modules/hr/ess/ess.routes.ts`

- [ ] **Step 1: Add deleteMyDocument service method**

In `avy-erp-backend/src/modules/hr/ess/ess.service.ts`, after the `uploadMyDocument` method (around line 3622), add:

```typescript
async deleteMyDocument(companyId: string, userId: string, documentId: string) {
  const tenantPrisma = await getTenantPrismaClient(companyId);

  // Find the employee for this user
  const employee = await tenantPrisma.employee.findFirst({
    where: { userId },
    select: { id: true },
  });
  if (!employee) throw ApiError.notFound('Employee not found');

  // Verify document belongs to this employee
  const document = await tenantPrisma.employeeDocument.findUnique({
    where: { id: documentId },
  });
  if (!document || document.employeeId !== employee.id) {
    throw ApiError.notFound('Document not found');
  }

  // Delete from R2 if fileUrl exists
  if (document.fileUrl) {
    try {
      await r2Service.deleteObject(document.fileUrl);
    } catch {
      // Log but don't fail — DB record still needs cleanup
      logger.warn('Failed to delete R2 object', { key: document.fileUrl });
    }
  }

  await tenantPrisma.employeeDocument.delete({ where: { id: documentId } });
  return { deleted: true };
}
```

NOTE: Check how `getTenantPrismaClient` is imported in this file — use the same import. Also check if `r2Service` and `logger` need importing (look at the top of the file for existing imports and add `r2Service` from `../../shared/services/r2.service` and `logger` from `../../config/logger` if not already imported).

- [ ] **Step 2: Add deletePolicyDocument service method**

In the same file, after `createPolicyDocument` (around line 3657), add:

```typescript
async deletePolicyDocument(companyId: string, documentId: string) {
  const tenantPrisma = await getTenantPrismaClient(companyId);

  const document = await tenantPrisma.policyDocument.findUnique({
    where: { id: documentId },
  });
  if (!document || document.companyId !== companyId) {
    throw ApiError.notFound('Policy document not found');
  }

  // Delete from R2
  if (document.fileUrl) {
    try {
      await r2Service.deleteObject(document.fileUrl);
    } catch {
      logger.warn('Failed to delete R2 object', { key: document.fileUrl });
    }
  }

  await tenantPrisma.policyDocument.delete({ where: { id: documentId } });
  return { deleted: true };
}
```

- [ ] **Step 3: Add controller handlers**

In `avy-erp-backend/src/modules/hr/ess/ess.controller.ts`, after `uploadMyDocument` (line 936), add:

```typescript
deleteMyDocument = asyncHandler(async (req: Request, res: Response) => {
  const companyId = req.user?.companyId;
  if (!companyId) throw ApiError.badRequest('Company ID is required');

  const userId = req.user?.id;
  if (!userId) throw ApiError.badRequest('User ID is required');

  const { id } = req.params;
  const result = await essService.deleteMyDocument(companyId, userId, id);
  res.json(createSuccessResponse(result, 'Document deleted'));
});
```

After `createPolicyDocument` (line 959), add:

```typescript
deletePolicyDocument = asyncHandler(async (req: Request, res: Response) => {
  const companyId = req.user?.companyId;
  if (!companyId) throw ApiError.badRequest('Company ID is required');

  const { id } = req.params;
  const result = await essService.deletePolicyDocument(companyId, id);
  res.json(createSuccessResponse(result, 'Policy document deleted'));
});
```

- [ ] **Step 4: Add routes**

In `avy-erp-backend/src/modules/hr/ess/ess.routes.ts`, after line 111 (the POST my-documents route), add:

```typescript
router.delete('/ess/my-documents/:id', requireESSFeature('documentUpload'), requirePermissions(['hr:delete', 'ess:upload-document']), controller.deleteMyDocument);
```

After line 115 (the POST policy-documents route), add:

```typescript
router.delete('/policy-documents/:id', requirePermissions(['hr:delete']), controller.deletePolicyDocument);
```

- [ ] **Step 5: Verify backend builds**

```bash
cd avy-erp-backend && pnpm build
```

Expected: BUILD SUCCESS.

- [ ] **Step 6: Commit**

```bash
git add avy-erp-backend/src/modules/hr/ess/
git commit -m "feat: add delete endpoints for employee documents and policy documents"
```

---

### Task 3: Add Frontend API Methods & Mutation Hooks

**Files:**
- Modify: `web-system-app/src/lib/api/ess.ts`
- Modify: `web-system-app/src/features/company-admin/api/use-ess-mutations.ts`
- Modify: `web-system-app/src/features/company-admin/api/index.ts`

- [ ] **Step 1: Add API client methods**

In `web-system-app/src/lib/api/ess.ts`, after line 507 (uploadMyDocument), add:

```typescript
    deleteMyDocument: async (id: string) => { const r = await client.delete(`/hr/ess/my-documents/${id}`); return r.data; },
```

After line 509 (getPolicyDocuments), add:

```typescript
    createPolicyDocument: async (data: any) => { const r = await client.post('/policy-documents', data); return r.data; },
    deletePolicyDocument: async (id: string) => { const r = await client.delete(`/policy-documents/${id}`); return r.data; },
```

- [ ] **Step 2: Add mutation hooks**

In `web-system-app/src/features/company-admin/api/use-ess-mutations.ts`, after the `useUploadMyDocument` function (around line 370), add:

```typescript
export function useDeleteMyDocument() {
    const qc = useQueryClient();
    return useMutation({
        mutationFn: (id: string) => essApi.deleteMyDocument(id),
        onSuccess: () => {
            qc.invalidateQueries({ queryKey: essKeys.myDocuments() });
        },
    });
}

export function useCreatePolicyDocument() {
    const qc = useQueryClient();
    return useMutation({
        mutationFn: (data: any) => essApi.createPolicyDocument(data),
        onSuccess: () => {
            qc.invalidateQueries({ queryKey: essKeys.policyDocuments() });
        },
    });
}

export function useDeletePolicyDocument() {
    const qc = useQueryClient();
    return useMutation({
        mutationFn: (id: string) => essApi.deletePolicyDocument(id),
        onSuccess: () => {
            qc.invalidateQueries({ queryKey: essKeys.policyDocuments() });
        },
    });
}
```

- [ ] **Step 3: Export new hooks from index.ts**

In `web-system-app/src/features/company-admin/api/index.ts`, add to the mutations exports (after `useUploadMyDocument` around line 322):

```typescript
    useDeleteMyDocument,
    useCreatePolicyDocument,
    useDeletePolicyDocument,
```

- [ ] **Step 4: Verify web builds**

```bash
cd web-system-app && pnpm build
```

Expected: BUILD SUCCESS (or pre-existing errors only).

- [ ] **Step 5: Commit**

```bash
git add web-system-app/src/lib/api/ess.ts web-system-app/src/features/company-admin/api/
git commit -m "feat(web): add API methods and mutation hooks for document delete and policy CRUD"
```

---

### Task 4: Create Shared FileUploadZone Component

**Files:**
- Create: `web-system-app/src/components/FileUploadZone.tsx`

- [ ] **Step 1: Create the component**

Create `web-system-app/src/components/FileUploadZone.tsx`:

```typescript
import { useRef, useState, useCallback } from 'react';
import { Upload, CheckCircle, Loader2, X, FileText } from 'lucide-react';
import { cn } from '@/lib/utils';

interface FileUploadZoneProps {
  onFileSelected: (file: File) => void;
  isUploading: boolean;
  uploadedFileName?: string | null;
  accept?: string;
  maxSizeMB?: number;
  label?: string;
  error?: string | null;
  onClear?: () => void;
}

function formatFileSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

export function FileUploadZone({
  onFileSelected,
  isUploading,
  uploadedFileName,
  accept = 'image/*,.pdf,.doc,.docx,.xls,.xlsx',
  maxSizeMB = 10,
  label = 'Drag and drop your file here, or click to browse',
  error,
  onClear,
}: FileUploadZoneProps) {
  const fileRef = useRef<HTMLInputElement>(null);
  const [isDragging, setIsDragging] = useState(false);
  const [selectedFileName, setSelectedFileName] = useState<string | null>(null);
  const [selectedFileSize, setSelectedFileSize] = useState<number>(0);

  const handleFile = useCallback((file: File) => {
    setSelectedFileName(file.name);
    setSelectedFileSize(file.size);
    onFileSelected(file);
  }, [onFileSelected]);

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  }, []);

  const handleDragLeave = useCallback(() => {
    setIsDragging(false);
  }, []);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    const file = e.dataTransfer.files?.[0];
    if (file) handleFile(file);
  }, [handleFile]);

  const handleInputChange = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) handleFile(file);
    if (fileRef.current) fileRef.current.value = '';
  }, [handleFile]);

  const handleClear = useCallback(() => {
    setSelectedFileName(null);
    setSelectedFileSize(0);
    onClear?.();
  }, [onClear]);

  const displayName = uploadedFileName || selectedFileName;

  // Show uploaded state
  if (displayName && !isUploading) {
    return (
      <div className="flex items-center gap-3 p-4 rounded-xl border border-success-200 dark:border-success-800/50 bg-success-50/50 dark:bg-success-900/10">
        <CheckCircle className="w-5 h-5 text-success-600 flex-shrink-0" />
        <div className="flex-1 min-w-0">
          <p className="text-sm font-medium text-success-800 dark:text-success-400 truncate">{displayName}</p>
          {selectedFileSize > 0 && <p className="text-xs text-success-600 dark:text-success-500">{formatFileSize(selectedFileSize)}</p>}
        </div>
        {onClear && (
          <button type="button" onClick={handleClear} className="p-1 text-neutral-400 hover:text-danger-500 transition-colors">
            <X className="w-4 h-4" />
          </button>
        )}
      </div>
    );
  }

  // Show uploading state
  if (isUploading) {
    return (
      <div className="flex items-center justify-center gap-3 p-6 rounded-xl border-2 border-dashed border-primary-300 dark:border-primary-700 bg-primary-50/50 dark:bg-primary-900/10">
        <Loader2 className="w-5 h-5 text-primary-600 animate-spin" />
        <p className="text-sm font-medium text-primary-700 dark:text-primary-400">Uploading {selectedFileName}...</p>
      </div>
    );
  }

  // Show drop zone
  return (
    <div>
      <div
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        onClick={() => fileRef.current?.click()}
        className={cn(
          'flex flex-col items-center justify-center gap-2 p-6 rounded-xl border-2 border-dashed cursor-pointer transition-colors',
          isDragging
            ? 'border-primary-500 bg-primary-50 dark:bg-primary-900/20'
            : 'border-neutral-200 dark:border-neutral-700 hover:border-primary-300 dark:hover:border-primary-700 hover:bg-neutral-50 dark:hover:bg-neutral-800/50',
          error && 'border-danger-300 dark:border-danger-700'
        )}
      >
        <div className={cn(
          'w-10 h-10 rounded-full flex items-center justify-center',
          isDragging ? 'bg-primary-100 dark:bg-primary-900/30' : 'bg-neutral-100 dark:bg-neutral-800'
        )}>
          <Upload className={cn('w-5 h-5', isDragging ? 'text-primary-600' : 'text-neutral-400')} />
        </div>
        <p className="text-sm text-neutral-500 dark:text-neutral-400 text-center">{label}</p>
        <p className="text-xs text-neutral-400 dark:text-neutral-500">Max {maxSizeMB} MB</p>
      </div>
      {error && <p className="text-xs text-danger-500 mt-1.5">{error}</p>}
      <input ref={fileRef} type="file" accept={accept} onChange={handleInputChange} className="hidden" />
    </div>
  );
}
```

- [ ] **Step 2: Verify web builds**

```bash
cd web-system-app && pnpm build
```

Expected: BUILD SUCCESS.

- [ ] **Step 3: Commit**

```bash
git add web-system-app/src/components/FileUploadZone.tsx
git commit -m "feat(web): add shared FileUploadZone component for drag-and-drop R2 uploads"
```

---

### Task 5: Redesign My Documents Screen

**Files:**
- Modify: `web-system-app/src/features/ess/MyDocumentsScreen.tsx`

- [ ] **Step 1: Read the current file**

Read `web-system-app/src/features/ess/MyDocumentsScreen.tsx` (it's 143 lines).

- [ ] **Step 2: Rewrite the screen**

Replace the entire file content with a redesigned version that:

1. **Imports:** Add `useFileUpload` from `@/hooks/useFileUpload`, `FileUploadZone` from `@/components/FileUploadZone`, `useDeleteMyDocument` from the API, `Trash2` from lucide-react, and keep existing imports.

2. **Upload modal:** Replace the inline form with a proper modal overlay (same pattern as expense claims):
   - Background overlay with `bg-black/40 backdrop-blur-sm`
   - Centered modal card with rounded corners
   - Header with title + close button
   - Document type dropdown (same DOC_TYPES array)
   - Document number input (optional)
   - Expiry date input (optional)
   - `FileUploadZone` component for drag-and-drop file upload
   - `useFileUpload({ category: 'employee-document', entityId: 'me' })` hook
   - On file selected: call `upload(file)`, on success store the R2 key + file name
   - Submit button: disabled until document type selected AND file uploaded
   - On submit: call `uploadMutation.mutate({ documentType, documentNumber, expiryDate, fileUrl: uploadedKey, fileName })`

3. **Document grid:** Keep the card grid but add:
   - Delete button on each card (using `useDeleteMyDocument` hook)
   - File type icon (PDF icon for PDFs, image icon for images, generic for others)
   - Better styling matching the expense claims card pattern

4. **State management:**
   - `showModal` boolean for modal visibility
   - `documentType`, `documentNumber`, `expiryDate` form fields
   - `uploadedKey` and `uploadedFileName` from the upload hook's onSuccess
   - Reset all state on modal close

Key constraints:
- Keep the same DOC_TYPES array
- Keep the same API shape (`POST /hr/ess/my-documents` with `{ documentType, documentNumber, expiryDate, fileUrl, fileName }`)
- Use `R2Link` for view/download buttons (already imported)
- Use `useCompanyFormatter` for date formatting (already imported)

- [ ] **Step 3: Verify web builds**

```bash
cd web-system-app && pnpm build
```

Expected: BUILD SUCCESS.

- [ ] **Step 4: Commit**

```bash
git add web-system-app/src/features/ess/MyDocumentsScreen.tsx
git commit -m "feat(web): redesign My Documents screen with modal upload and drag-and-drop"
```

---

### Task 6: Upgrade Candidate Document Modal

**Files:**
- Modify: `web-system-app/src/features/company-admin/hr/CandidateDetailScreen.tsx`

- [ ] **Step 1: Read the document modal section**

Read lines 1155-1202 of `CandidateDetailScreen.tsx` (the existing document modal).

- [ ] **Step 2: Replace the URL input with FileUploadZone**

In the existing doc modal (inside `<Modal open={docModalOpen}>`):

1. Add imports at the top of the file:
```typescript
import { useFileUpload } from '@/hooks/useFileUpload';
import { FileUploadZone } from '@/components/FileUploadZone';
```

2. Add upload hook inside the component (near other hooks):
```typescript
const { upload: uploadCandidateDoc, isUploading: isCandidateDocUploading, error: candidateDocUploadError, reset: resetCandidateDocUpload } = useFileUpload({
  category: 'candidate-document',
  entityId: id ?? 'new',
});
```

3. Replace the "File URL" text input (lines 1179-1186) with `FileUploadZone`:
```typescript
<FileUploadZone
  onFileSelected={async (file) => {
    const key = await uploadCandidateDoc(file);
    if (key) {
      setDocForm((f) => ({ ...f, fileUrl: key, fileName: file.name }));
    }
  }}
  isUploading={isCandidateDocUploading}
  uploadedFileName={docForm.fileName || null}
  error={candidateDocUploadError}
  onClear={() => {
    setDocForm((f) => ({ ...f, fileUrl: '', fileName: '' }));
    resetCandidateDocUpload();
  }}
/>
```

4. Remove the "File Name" manual input (lines 1170-1177) — fileName is now auto-set from the uploaded file.

5. Update the submit button disabled condition to also check `!docForm.fileUrl`:
```typescript
disabled={createDocument.isPending || isCandidateDocUploading || !docForm.fileUrl || !docForm.documentType}
```

6. Reset upload state when opening the modal — in `openAddDocument`:
```typescript
const openAddDocument = () => {
  setDocForm({ ...EMPTY_DOCUMENT });
  resetCandidateDocUpload();
  setDocModalOpen(true);
};
```

- [ ] **Step 3: Verify web builds**

```bash
cd web-system-app && pnpm build
```

Expected: BUILD SUCCESS.

- [ ] **Step 4: Commit**

```bash
git add web-system-app/src/features/company-admin/hr/CandidateDetailScreen.tsx
git commit -m "feat(web): add R2 file upload to candidate document modal"
```

---

### Task 7: Upgrade Training Material Modal

**Files:**
- Modify: `web-system-app/src/features/company-admin/hr/TrainingCatalogueScreen.tsx`

- [ ] **Step 1: Read the material modal section**

Read lines 1928-1975 of `TrainingCatalogueScreen.tsx` (the existing material modal).

- [ ] **Step 2: Replace the URL input with dual-mode upload**

In the material modal:

1. Add imports:
```typescript
import { useFileUpload } from '@/hooks/useFileUpload';
import { FileUploadZone } from '@/components/FileUploadZone';
```

2. Add upload hook (near other hooks, use `materialsTrainingId` as entityId):
```typescript
const { upload: uploadMaterial, isUploading: isMaterialUploading, error: materialUploadError, reset: resetMaterialUpload } = useFileUpload({
  category: 'training-material',
  entityId: materialsTrainingId ?? 'new',
});
```

3. Replace the "URL" text input (line 1954) with a conditional section:
   - If `materialForm.type` is `VIDEO` or `LINK`: keep the URL text input (for external URLs like YouTube)
   - Otherwise (PDF, DOCUMENT, PRESENTATION): show `FileUploadZone`

```typescript
{materialForm.type === 'VIDEO' || materialForm.type === 'LINK' ? (
  <div>
    <label className="block text-xs font-bold text-neutral-500 dark:text-neutral-400 mb-1.5">URL</label>
    <input type="url" value={materialForm.url} onChange={(e) => updateMaterialField("url", e.target.value)} placeholder="https://youtube.com/..." className="w-full px-3 py-2.5 bg-neutral-50 dark:bg-neutral-800 border border-neutral-200 dark:border-neutral-700 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-primary-500/20 focus:border-primary-500 dark:text-white placeholder:text-neutral-400 transition-all" />
  </div>
) : (
  <div>
    <label className="block text-xs font-bold text-neutral-500 dark:text-neutral-400 mb-1.5">File</label>
    <FileUploadZone
      onFileSelected={async (file) => {
        const key = await uploadMaterial(file);
        if (key) {
          updateMaterialField('url', key);
        }
      }}
      isUploading={isMaterialUploading}
      uploadedFileName={materialForm.url && !materialForm.url.startsWith('http') ? materialForm.url.split('/').pop() ?? null : null}
      accept=".pdf,.doc,.docx,.ppt,.pptx,.xls,.xlsx"
      error={materialUploadError}
      onClear={() => {
        updateMaterialField('url', '');
        resetMaterialUpload();
      }}
    />
  </div>
)}
```

4. Reset upload state when opening the create modal — in `openCreateMaterial`:
```typescript
const openCreateMaterial = () => { setMaterialEditingId(null); setMaterialForm({ ...EMPTY_MATERIAL }); resetMaterialUpload(); setMaterialModalOpen(true); };
```

- [ ] **Step 3: Verify web builds**

```bash
cd web-system-app && pnpm build
```

Expected: BUILD SUCCESS.

- [ ] **Step 4: Commit**

```bash
git add web-system-app/src/features/company-admin/hr/TrainingCatalogueScreen.tsx
git commit -m "feat(web): add R2 file upload to training material modal (dual-mode: file or URL)"
```

---

### Task 8: Add Admin Upload to Policy Documents Screen

**Files:**
- Modify: `web-system-app/src/features/ess/PolicyDocumentsScreen.tsx`

- [ ] **Step 1: Read the current file**

Read `web-system-app/src/features/ess/PolicyDocumentsScreen.tsx` (it's 69 lines).

- [ ] **Step 2: Add admin upload capability**

Modify the file to add:

1. **New imports:**
```typescript
import { useState } from 'react';
import { useFileUpload } from '@/hooks/useFileUpload';
import { FileUploadZone } from '@/components/FileUploadZone';
import { useCreatePolicyDocument, useDeletePolicyDocument } from '@/features/company-admin/api';
import { useCanPerform } from '@/hooks/useCanPerform';
import { showSuccess, showApiError } from '@/lib/toast';
import { Plus, Trash2, X } from 'lucide-react';
```

2. **Permission check:**
```typescript
const canCreate = useCanPerform('hr:create');
const canDelete = useCanPerform('hr:delete');
```

3. **Upload modal state:**
```typescript
const [showModal, setShowModal] = useState(false);
const [title, setTitle] = useState('');
const [category, setCategory] = useState('HR_POLICY');
const [description, setDescription] = useState('');
const [version, setVersion] = useState('1.0');
const [uploadedKey, setUploadedKey] = useState('');
const [uploadedFileName, setUploadedFileName] = useState('');
```

4. **Hooks:**
```typescript
const createMutation = useCreatePolicyDocument();
const deleteMutation = useDeletePolicyDocument();
const { upload, isUploading, error: uploadError, reset: resetUpload } = useFileUpload({
  category: 'policy-document',
  entityId: 'policy',
});
```

5. **"Upload Policy" button in header** (only if `canCreate`):
```typescript
{canCreate && (
  <button onClick={() => setShowModal(true)} className="flex items-center gap-2 px-4 py-2 bg-primary-600 text-white rounded-xl text-sm font-bold hover:bg-primary-700 transition-colors">
    <Plus className="w-4 h-4" /> Upload Policy
  </button>
)}
```

6. **Upload modal:** Same overlay pattern as My Documents (Task 5):
   - Title (text, required)
   - Category dropdown: HR_POLICY, LEAVE_POLICY, ATTENDANCE_POLICY, CODE_OF_CONDUCT, SAFETY, TRAVEL, IT_POLICY, OTHER
   - Description (textarea, optional)
   - Version (text, default "1.0")
   - `FileUploadZone` with `accept=".pdf"` and `maxSizeMB={10}`
   - On file selected: `upload(file)` → store key
   - Submit: `createMutation.mutate({ title, category, description, version, fileUrl: uploadedKey, fileName: uploadedFileName })`

7. **Delete button on each policy card** (only if `canDelete`):
```typescript
{canDelete && (
  <button onClick={() => deleteMutation.mutate(p.id, { onSuccess: () => showSuccess('Policy deleted'), onError: showApiError })} className="p-1.5 text-danger-500 hover:bg-danger-50 dark:hover:bg-danger-900/20 rounded-lg transition-colors">
    <Trash2 className="w-4 h-4" />
  </button>
)}
```

Category display labels for the dropdown:
```typescript
const POLICY_CATEGORIES = [
  { value: 'HR_POLICY', label: 'HR Policy' },
  { value: 'LEAVE_POLICY', label: 'Leave Policy' },
  { value: 'ATTENDANCE_POLICY', label: 'Attendance Policy' },
  { value: 'CODE_OF_CONDUCT', label: 'Code of Conduct' },
  { value: 'SAFETY', label: 'Safety' },
  { value: 'TRAVEL', label: 'Travel' },
  { value: 'IT_POLICY', label: 'IT Policy' },
  { value: 'OTHER', label: 'Other' },
];
```

- [ ] **Step 3: Verify web builds**

```bash
cd web-system-app && pnpm build
```

Expected: BUILD SUCCESS.

- [ ] **Step 4: Commit**

```bash
git add web-system-app/src/features/ess/PolicyDocumentsScreen.tsx
git commit -m "feat(web): add admin upload and delete for policy documents"
```

---
