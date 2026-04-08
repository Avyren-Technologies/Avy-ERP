# R2 Upload UI Enhancements — Design Spec

## Goal

Upgrade 4 document management screens to use proper R2 file upload UIs with drag-and-drop, preview, and modal patterns — matching the expense claims screen quality. Fix backend validators that reject R2 keys.

## Screens

1. **My Documents (ESS)** — Employee self-service document upload
2. **Candidate Documents (Recruitment)** — HR uploads candidate docs
3. **Training Materials (Admin)** — Admin uploads training materials
4. **Policy Documents (Admin)** — Admin uploads company policies

---

## Backend Fixes (Validators)

Three backend validators use `.url()` on `fileUrl`, which rejects R2 keys like `comp_123/employees/emp_456/documents/abc.pdf`. Change to `.min(1)`.

### Files to modify:

**`avy-erp-backend/src/modules/hr/ess/ess.validators.ts`**
```
uploadDocumentSchema.fileUrl: z.string().url() → z.string().min(1, 'File is required')
policyDocumentSchema.fileUrl: z.string().url() → z.string().min(1, 'File is required')
```

**`avy-erp-backend/src/modules/hr/advanced/candidate-profile.validators.ts`**
```
createDocumentSchema.fileUrl: z.string().min(1) — already correct, no change needed
```

**`avy-erp-backend/src/modules/hr/advanced/training-material.validators.ts`**
```
createMaterialSchema.url: z.string().min(1) — already correct, no change needed
```

---

## Screen 1: My Documents (ESS) — Full Redesign

**Route:** `/app/company/hr/my-documents`
**File:** `web-system-app/src/features/ess/MyDocumentsScreen.tsx`
**Backend:** `POST /hr/ess/my-documents`, `GET /hr/ess/my-documents`
**R2 category:** `employee-document`

### Current state
- Inline form with manual URL text input
- No file upload, no drag-drop, no preview

### New design
Replace inline form with a card grid of existing documents + "Upload Document" button that opens a modal.

**Document grid (read state):**
- Card per document showing: document type badge, document number, expiry date, file icon, view/download button (R2Link)
- Empty state with upload CTA

**Upload modal (triggered by button):**
- Modal overlay matching expense claims pattern
- Fields:
  - Document Type (dropdown): Aadhaar, PAN, Passport, Driving License, Voter ID, Education Certificate, Experience Letter, Other
  - Document Number (text, optional)
  - Expiry Date (date picker, optional)
  - File upload zone (drag-and-drop area)
- File upload zone:
  - Drag-and-drop with visual feedback (isDragging state)
  - Click-to-browse fallback
  - Shows file name + size after selection
  - Upload progress via `useFileUpload({ category: 'employee-document', entityId: 'me' })`
  - Accepted types: images + PDF + doc/docx
  - Max size: 10 MB (document default)
- Submit button: disabled until file uploaded + document type selected
- On submit: calls `POST /hr/ess/my-documents` with `{ documentType, documentNumber, expiryDate, fileUrl: r2Key, fileName }`

### Delete support
Backend currently has no delete endpoint for employee documents. Add:
- **New endpoint:** `DELETE /hr/ess/my-documents/:id`
- **Controller:** `deleteMyDocument` in `ess.controller.ts`
- **Service:** Verify document belongs to authenticated employee, delete from DB + R2
- **Frontend:** Delete button on each document card with confirmation

---

## Screen 2: Candidate Documents (Recruitment) — Add Upload Modal

**File:** `web-system-app/src/features/company-admin/hr/CandidateDetailScreen.tsx`
**Backend:** `POST /hr/candidates/:candidateId/documents`, `GET /hr/candidates/:candidateId/documents`, `DELETE /hr/candidate-documents/:id`
**R2 category:** `candidate-document`

### Current state
- Documents tab exists with list view
- No upload form/modal

### New design
Add "Upload Document" button in the documents tab that opens an upload modal.

**Upload modal:**
- Document Type (dropdown): Resume, Cover Letter, Certificate, ID Proof, Portfolio
- File upload zone (drag-and-drop, same pattern as expense claims)
- `useFileUpload({ category: 'candidate-document', entityId: candidateId })`
- Accepted types: images + PDF + doc/docx
- Max size: 10 MB
- On submit: calls existing `useCreateCandidateDocument` mutation with `{ documentType, fileName, fileUrl: r2Key }`

**Document list enhancement:**
- Each document shows: type badge, file name, upload date, view (R2Link), delete button
- Delete uses existing `useDeleteCandidateDocument` mutation

---

## Screen 3: Training Materials (Admin) — Add Upload Modal

**File:** `web-system-app/src/features/company-admin/hr/TrainingCatalogueScreen.tsx` (materials section)
**Backend:** `POST /hr/training-catalogues/:trainingId/materials`, CRUD for materials
**R2 category:** `training-material`

### Current state
- Backend fully implemented
- Frontend has mutations but needs upload UI in the training detail/edit view

### New design
Add "Add Material" button in the training catalogue detail that opens an upload modal.

**Upload modal:**
- Name (text, required)
- Type (dropdown): PDF, VIDEO, LINK, PRESENTATION, DOCUMENT
- Description (textarea, optional)
- Sequence Order (number, optional)
- Mandatory toggle (boolean, default true)
- File upload zone (drag-and-drop) — for PDF/DOCUMENT/PRESENTATION types
- URL text input — for VIDEO/LINK types (external URLs like YouTube)
- `useFileUpload({ category: 'training-material', entityId: trainingId })`
- On submit: calls `useCreateTrainingMaterial` with `{ name, type, url: r2Key_or_externalUrl, description, sequenceOrder, isMandatory }`

**Material type logic:**
- If type is VIDEO or LINK: show URL text input (user pastes YouTube/external URL)
- If type is PDF, DOCUMENT, or PRESENTATION: show file upload zone (uploads to R2)
- This dual-mode is necessary because training materials can be external links

**Material list:**
- Each material shows: name, type badge, description, sequence, mandatory indicator
- View (R2Link for uploaded files, regular link for external URLs)
- Edit button → opens modal pre-filled
- Delete button with confirmation

---

## Screen 4: Policy Documents (Admin) — New Admin Management UI

**File:** `web-system-app/src/features/ess/PolicyDocumentsScreen.tsx` (add admin section)
**Backend:** `POST /policy-documents` (create), `GET /hr/ess/policy-documents` (list)
**R2 category:** `policy-document`

### Current state
- Employee read-only view exists
- No admin create/edit/delete UI
- Backend create endpoint exists but no frontend calls it

### New design
The existing `PolicyDocumentsScreen.tsx` is the employee view. We need to add admin capabilities when the user has `hr:create` permission.

**Admin enhancements to existing screen:**
- If user has `hr:create` permission: show "Upload Policy" button in header
- Upload Policy modal:
  - Title (text, required)
  - Category (dropdown): HR Policy, Leave Policy, Attendance Policy, Code of Conduct, Safety, Travel, IT Policy, Other
  - Description (textarea, optional)
  - Version (text, optional, default "1.0")
  - File upload zone (drag-and-drop)
  - `useFileUpload({ category: 'policy-document', entityId: 'policy' })`
  - Accepted types: PDF only (policies should be PDF)
  - On submit: calls `POST /policy-documents` with `{ title, category, description, fileUrl: r2Key, fileName, version }`

**Backend additions needed:**
- **New mutation hook:** `useCreatePolicyDocument()` in web API
- **New API client method:** `createPolicyDocument()` in ess.ts or a new policy-documents.ts
- The `POST /policy-documents` route exists but no frontend mutation hook exists yet

**Delete support:**
- Backend currently has no delete endpoint. Add:
  - **New endpoint:** `DELETE /policy-documents/:id`
  - **Controller/Service:** Verify companyId, soft-delete (set `isActive: false`) or hard-delete
  - **Frontend:** Delete button on each policy card (admin only) with confirmation

---

## Shared Upload Modal Component

All 4 screens use the same drag-and-drop upload pattern. To avoid duplication, create a reusable `FileUploadZone` component.

### New file: `web-system-app/src/components/FileUploadZone.tsx`

```typescript
interface FileUploadZoneProps {
  onFileSelected: (file: File) => void;
  isUploading: boolean;
  uploadedFileName?: string | null;
  accept?: string;          // e.g., "image/*,.pdf,.doc,.docx"
  maxSizeMB?: number;       // Display hint
  label?: string;           // e.g., "Drag and drop your document here"
  error?: string | null;
}
```

**Behavior:**
- Drag-and-drop zone with dashed border
- Click-to-browse via hidden file input
- Shows upload progress (spinner) when `isUploading`
- Shows uploaded file name + check icon when `uploadedFileName` is set
- Shows error message when `error` is set
- Accepts `accept` prop for file type filtering

This component does NOT call `useFileUpload` — the parent calls the hook and passes `isUploading`/`error` down. This keeps the component reusable and the parent in control of the upload category/entityId.

---

## Error Handling

All upload modals follow the expense claims pattern:
- Client-side validation: file size, file type
- Server-side validation: Zod schema (backend rejects invalid data)
- Upload failure: `showApiError(err)` toast
- Network failure: retry suggestion in error message
- R2 unavailable: graceful error via `useFileUpload.onError`

---

## Testing Strategy

- Verify all 4 upload modals accept files and upload to R2
- Verify uploaded documents display correctly via `R2Link`/`R2Image`
- Verify delete functionality works (where applicable)
- Verify validators no longer reject R2 keys
- Verify drag-and-drop works
- Verify file type restrictions are enforced
