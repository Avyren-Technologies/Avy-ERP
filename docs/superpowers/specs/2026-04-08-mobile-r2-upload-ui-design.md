# Mobile R2 Upload UI Enhancements — Design Spec

## Goal

Upgrade 4 mobile document screens to use R2 file upload via `useFileUpload` hook with native file/image pickers, matching the web upgrades. Add missing API methods.

## Screens

1. **My Documents (ESS)** — Replace URL text input with file picker + R2 upload
2. **Candidate Documents** — Add file picker to document form modal
3. **Training Materials** — Add material upload for admin (file picker for docs, URL input for links)
4. **Policy Documents** — Add admin upload + delete (permission-gated)

---

## Shared Patterns (from expense claims reference)

**File picking:** `expo-document-picker` for documents, `expo-image-picker` for photos
**R2 upload:** `useFileUpload` hook (already exists at `@/hooks/use-file-upload`)
**R2 display:** `useFileUrl` hook (already exists at `@/hooks/use-file-url`)
**Upload flow:** Pick file → get URI + size + type → call `upload({ uri, name, type, size })` → get R2 key → save key to API

---

## API Additions (mobile-app/src/lib/api/ess.ts)

Add these methods (matching web):
```
deleteMyDocument: DELETE /hr/ess/my-documents/:id
createPolicyDocument: POST /hr/policy-documents
deletePolicyDocument: DELETE /hr/policy-documents/:id
```

Add corresponding mutation hooks in `use-ess-mutations.ts`.

---

## Screen 1: My Documents — Redesign Upload Form

**File:** `mobile-app/src/features/ess/my-documents-screen.tsx`
**R2 category:** `employee-document`

### Current state
- Inline form with text inputs for fileUrl and fileName
- No file picker, no R2 upload

### New design
Replace the fileUrl/fileName text inputs with a file picker button + R2 upload:

- Keep existing form fields: Document Type (chip selector), Document Number, Expiry Date
- Replace fileUrl + fileName inputs with:
  - "Pick File" button (uses `DocumentPicker.getDocumentAsync`)
  - Shows selected file name + size after picking
  - Uploads to R2 via `useFileUpload({ category: 'employee-document', entityId: 'me' })`
  - Shows upload progress (ActivityIndicator)
  - Shows success state (check icon + file name)
- Add delete button on each document card (using `useDeleteMyDocument`)
- On submit: send `{ documentType, documentNumber, expiryDate, fileUrl: r2Key, fileName }`

---

## Screen 2: Candidate Documents — Add File Picker to Modal

**File:** `mobile-app/src/features/company-admin/hr/candidate-detail-screen.tsx`
**R2 category:** `candidate-document`

### Current state
- DocumentFormModal with text inputs for title, type, URL

### New design
Replace the URL text input in DocumentFormModal with:
- "Pick File" button
- Upload to R2 via `useFileUpload({ category: 'candidate-document', entityId: candidateId })`
- On success: set fileUrl to R2 key, fileName to original file name
- On submit: send `{ documentType, fileName, fileUrl: r2Key }` via existing `useCreateCandidateDocument`

---

## Screen 3: Training Materials — Add Upload for Admin

**File:** `mobile-app/src/features/company-admin/hr/training-screen.tsx`
**R2 category:** `training-material`

### Current state
- Materials section is read-only or has stub UI

### New design
Add "Add Material" button that opens a bottom sheet modal:
- Name (text input, required)
- Type (selector): PDF, VIDEO, LINK, PRESENTATION, DOCUMENT
- Dual mode (same as web):
  - VIDEO/LINK → URL text input
  - PDF/DOCUMENT/PRESENTATION → File picker + R2 upload
- Description (text input, optional)
- Sequence Order (number input, optional)
- Mandatory toggle
- `useFileUpload({ category: 'training-material', entityId: trainingId })`
- On submit: `useCreateTrainingMaterial` with `{ name, type, url: r2Key_or_externalUrl, ... }`

---

## Screen 4: Policy Documents — Add Admin Upload + Delete

**File:** `mobile-app/src/features/ess/policy-documents-screen.tsx`
**R2 category:** `policy-document`

### Current state
- Read-only view for employees

### New design
- If user has admin role: show "Upload Policy" FAB button
- Upload modal (bottom sheet):
  - Title (text, required)
  - Category selector (same 8 options as web)
  - Description (text, optional)
  - Version (text, default "1.0")
  - File picker (PDF only) + R2 upload
- Delete button on each card (admin only)
- `useFileUpload({ category: 'policy-document', entityId: 'policy' })`

---

## File Picker Pattern (consistent across all screens)

```typescript
import * as DocumentPicker from 'expo-document-picker';
import * as FileSystem from 'expo-file-system';

const pickFile = async () => {
  const result = await DocumentPicker.getDocumentAsync({
    type: ['image/*', 'application/pdf', 'application/msword', ...],
    copyToCacheDirectory: true,
  });
  if (!result.canceled && result.assets[0]) {
    const asset = result.assets[0];
    const key = await upload({
      uri: asset.uri,
      name: asset.name ?? 'document',
      type: asset.mimeType ?? 'application/octet-stream',
      size: asset.size ?? 0,
    });
    if (key) {
      setUploadedKey(key);
      setUploadedFileName(asset.name);
    }
  }
};
```

---

## Error Handling

- Upload failure: `showErrorMessage(errMsg)` from `@/components/ui/utils`
- Picker cancelled: no-op
- File too large: hook validates and calls `onError`
