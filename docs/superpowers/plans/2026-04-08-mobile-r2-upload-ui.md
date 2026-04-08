# Mobile R2 Upload UI Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Upgrade 4 mobile document screens to use R2 file upload with native pickers, matching the web app upgrades.

**Architecture:** Add missing API methods and mutation hooks to mobile. Upgrade each screen to use `useFileUpload` hook with `expo-document-picker` / `expo-image-picker` for file selection, replacing manual URL text inputs. Follow the expense claims screen pattern.

**Tech Stack:** React Native, Expo, `expo-document-picker`, `expo-file-system`, `useFileUpload` hook, `useFileUrl` hook, React Query

**Spec:** `docs/superpowers/specs/2026-04-08-mobile-r2-upload-ui-design.md`

---

## File Structure

### Mobile App (mobile-app)

| Action | File | Responsibility |
|--------|------|----------------|
| Modify | `src/lib/api/ess.ts` | Add deleteMyDocument, createPolicyDocument, deletePolicyDocument API methods |
| Modify | `src/features/company-admin/api/use-ess-mutations.ts` | Add useDeleteMyDocument, useCreatePolicyDocument, useDeletePolicyDocument hooks |
| Modify | `src/features/ess/my-documents-screen.tsx` | Replace URL input with file picker + R2 upload, add delete |
| Modify | `src/features/company-admin/hr/candidate-detail-screen.tsx` | Replace URL input with file picker in document form modal |
| Modify | `src/features/company-admin/hr/training-screen.tsx` | Add material upload with dual-mode (file/URL) |
| Modify | `src/features/ess/policy-documents-screen.tsx` | Add admin upload modal + delete |

---

### Task 1: Add Mobile API Methods & Mutation Hooks

**Files:**
- Modify: `mobile-app/src/lib/api/ess.ts`
- Modify: `mobile-app/src/features/company-admin/api/use-ess-mutations.ts`

- [ ] **Step 1: Add API methods to ess.ts**

In `mobile-app/src/lib/api/ess.ts`, find the existing `uploadMyDocument` method and add after it:

```typescript
deleteMyDocument: async (id: string) => client.delete(`/hr/ess/my-documents/${id}`),
```

Find the existing `getPolicyDocuments` method and add after it:

```typescript
createPolicyDocument: async (data: any) => client.post('/hr/policy-documents', data),
deletePolicyDocument: async (id: string) => client.delete(`/hr/policy-documents/${id}`),
```

NOTE: Mobile API client does NOT use `.then(r => r.data)` — the interceptor strips the Axios wrapper. Just call `client.post/delete` directly.

- [ ] **Step 2: Add mutation hooks**

In `mobile-app/src/features/company-admin/api/use-ess-mutations.ts`, after the `useUploadMyDocument` hook, add:

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

Check how `essApi`, `essKeys`, `useQueryClient`, `useMutation` are imported — follow the same pattern as `useUploadMyDocument`.

- [ ] **Step 3: Verify type-check**

```bash
cd mobile-app && pnpm type-check
```

- [ ] **Step 4: Commit**

```bash
git add mobile-app/src/lib/api/ess.ts mobile-app/src/features/company-admin/api/use-ess-mutations.ts
git commit -m "feat(mobile): add delete document and policy document API methods + mutation hooks"
```

---

### Task 2: Upgrade My Documents Screen

**Files:**
- Modify: `mobile-app/src/features/ess/my-documents-screen.tsx`

- [ ] **Step 1: Read the current file fully**

Read `mobile-app/src/features/ess/my-documents-screen.tsx` to understand the full structure.

- [ ] **Step 2: Add R2 upload integration**

Add these imports:
```typescript
import * as DocumentPicker from 'expo-document-picker';
import { useFileUpload } from '@/hooks/use-file-upload';
import { useDeleteMyDocument } from '@/features/company-admin/api/use-ess-mutations';
```

In the component (or the UploadForm sub-component), add:
```typescript
const { upload, isUploading, error: uploadError, reset: resetUpload } = useFileUpload({
  category: 'employee-document',
  entityId: 'me',
});
const [uploadedKey, setUploadedKey] = useState('');
const [uploadedFileName, setUploadedFileName] = useState('');

const pickFile = async () => {
  const result = await DocumentPicker.getDocumentAsync({
    type: ['image/*', 'application/pdf', 'application/msword', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'],
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
      setUploadedFileName(asset.name ?? 'document');
    }
  }
};
```

- [ ] **Step 3: Replace the fileUrl and fileName text inputs**

Find the fileUrl TextInput and fileName TextInput in the form. Replace both with:
- A "Pick File" button (Pressable with Upload icon)
- Conditional display: if uploading → ActivityIndicator + "Uploading..."
- If uploaded → CheckCircle + uploadedFileName + clear button (X)
- If neither → show the pick button

```typescript
{/* File Upload Section */}
<Text className="font-inter text-xs font-bold text-neutral-500 mb-1.5">File *</Text>
{isUploading ? (
  <View style={{ flexDirection: 'row', alignItems: 'center', gap: 8, padding: 12 }}>
    <ActivityIndicator size="small" color={colors.primary[600]} />
    <Text className="font-inter text-sm text-primary-600">Uploading...</Text>
  </View>
) : uploadedKey ? (
  <View style={{ flexDirection: 'row', alignItems: 'center', gap: 8, padding: 12, borderRadius: 12, borderWidth: 1, borderColor: colors.success[200] }}>
    <CheckCircle size={18} color={colors.success[600]} />
    <Text className="font-inter text-sm text-success-700 flex-1" numberOfLines={1}>{uploadedFileName}</Text>
    <Pressable onPress={() => { setUploadedKey(''); setUploadedFileName(''); resetUpload(); }}>
      <X size={16} color={colors.neutral[400]} />
    </Pressable>
  </View>
) : (
  <Pressable onPress={pickFile} style={{ flexDirection: 'row', alignItems: 'center', justifyContent: 'center', gap: 8, padding: 16, borderRadius: 12, borderWidth: 2, borderStyle: 'dashed', borderColor: colors.neutral[300] }}>
    <Upload size={18} color={colors.neutral[400]} />
    <Text className="font-inter text-sm text-neutral-500">Pick a file to upload</Text>
  </Pressable>
)}
{uploadError && <Text className="font-inter text-xs text-danger-500 mt-1">{uploadError}</Text>}
```

- [ ] **Step 4: Update form submission**

Change the submit handler to use `uploadedKey` and `uploadedFileName` instead of the old `fileUrl`/`fileName` text input values:
```typescript
uploadMutation.mutate({
  documentType,
  documentNumber: documentNumber.trim(),
  expiryDate: expiryDate || undefined,
  fileUrl: uploadedKey,
  fileName: uploadedFileName,
}, { onSuccess: () => { ... }, onError: ... });
```

Update submit button disabled condition to check `!uploadedKey` instead of `!fileName.trim()`.

- [ ] **Step 5: Add delete support**

Add delete hook:
```typescript
const deleteMutation = useDeleteMyDocument();
```

On each document card, add a delete button (Trash2 icon, danger color):
```typescript
<Pressable onPress={() => deleteMutation.mutate(doc.id, { onSuccess: () => showSuccess('Document deleted'), onError: (e: any) => showErrorMessage(e?.response?.data?.message ?? 'Delete failed') })}>
  <Trash2 size={16} color={colors.danger[500]} />
</Pressable>
```

- [ ] **Step 6: Reset upload state on form close**

When closing/resetting the form, also reset upload state:
```typescript
setUploadedKey('');
setUploadedFileName('');
resetUpload();
```

- [ ] **Step 7: Verify type-check**

```bash
cd mobile-app && pnpm type-check
```

- [ ] **Step 8: Commit**

```bash
git add mobile-app/src/features/ess/my-documents-screen.tsx
git commit -m "feat(mobile): redesign My Documents with R2 file upload and delete"
```

---

### Task 3: Upgrade Candidate Document Modal

**Files:**
- Modify: `mobile-app/src/features/company-admin/hr/candidate-detail-screen.tsx`

- [ ] **Step 1: Read the file and find the DocumentFormModal**

Find the DocumentFormModal component/section that handles document creation. It should have text inputs for title, type, and URL.

- [ ] **Step 2: Add R2 upload imports and hook**

```typescript
import * as DocumentPicker from 'expo-document-picker';
import { useFileUpload } from '@/hooks/use-file-upload';
```

Inside the component:
```typescript
const { upload: uploadCandidateDoc, isUploading: isCandidateDocUploading, error: candidateDocError, reset: resetCandidateDoc } = useFileUpload({
  category: 'candidate-document',
  entityId: candidateId ?? 'new',
});
```

- [ ] **Step 3: Replace URL text input with file picker**

In the DocumentFormModal, replace the URL text input with the same pick-file pattern from Task 2:
- "Pick File" button
- Upload state (ActivityIndicator)
- Success state (file name + clear)
- On file picked: upload to R2, set fileUrl and fileName in form state

- [ ] **Step 4: Update submit to use R2 key**

The submit handler should send `{ documentType, fileName: uploadedFileName, fileUrl: uploadedKey }` to `useCreateCandidateDocument`.

- [ ] **Step 5: Reset upload on modal open/close**

```typescript
resetCandidateDoc();
```

- [ ] **Step 6: Verify type-check**

```bash
cd mobile-app && pnpm type-check
```

- [ ] **Step 7: Commit**

```bash
git add mobile-app/src/features/company-admin/hr/candidate-detail-screen.tsx
git commit -m "feat(mobile): add R2 file upload to candidate document modal"
```

---

### Task 4: Upgrade Training Materials

**Files:**
- Modify: `mobile-app/src/features/company-admin/hr/training-screen.tsx`

- [ ] **Step 1: Read the file and find the materials section**

Understand the current materials UI — there may be a modal or section for adding materials.

- [ ] **Step 2: Add R2 upload for materials**

Add imports:
```typescript
import * as DocumentPicker from 'expo-document-picker';
import { useFileUpload } from '@/hooks/use-file-upload';
```

Add hook (use the training ID from the current context):
```typescript
const { upload: uploadMaterial, isUploading: isMaterialUploading, error: materialUploadError, reset: resetMaterialUpload } = useFileUpload({
  category: 'training-material',
  entityId: selectedTrainingId ?? 'new',
});
```

- [ ] **Step 3: Implement dual-mode upload**

In the material creation form/modal:
- If type is VIDEO or LINK: show URL text input (for external URLs)
- If type is PDF, DOCUMENT, or PRESENTATION: show file picker button + R2 upload

Pattern:
```typescript
{materialType === 'VIDEO' || materialType === 'LINK' ? (
  <TextInput value={materialUrl} onChangeText={setMaterialUrl} placeholder="https://youtube.com/..." />
) : (
  // File picker + upload pattern (same as Task 2)
)}
```

- [ ] **Step 4: Submit with R2 key or external URL**

```typescript
createMaterialMutation.mutate({
  trainingId,
  data: { name, type: materialType, url: uploadedKey || materialUrl, description, sequenceOrder, isMandatory }
});
```

- [ ] **Step 5: Verify type-check**

```bash
cd mobile-app && pnpm type-check
```

- [ ] **Step 6: Commit**

```bash
git add mobile-app/src/features/company-admin/hr/training-screen.tsx
git commit -m "feat(mobile): add R2 file upload to training material creation"
```

---

### Task 5: Upgrade Policy Documents Screen

**Files:**
- Modify: `mobile-app/src/features/ess/policy-documents-screen.tsx`

- [ ] **Step 1: Read the current file fully**

Understand the current read-only view.

- [ ] **Step 2: Add admin upload capability**

Add imports:
```typescript
import * as DocumentPicker from 'expo-document-picker';
import { useFileUpload } from '@/hooks/use-file-upload';
import { useCreatePolicyDocument, useDeletePolicyDocument } from '@/features/company-admin/api/use-ess-mutations';
import { useAuthStore } from '@/features/auth/use-auth-store';
```

Check the user's role to determine admin status:
```typescript
const user = useAuthStore.use.user();
const isAdmin = user?.role === 'COMPANY_ADMIN' || user?.role === 'SUPER_ADMIN';
```

- [ ] **Step 3: Add upload modal**

Add state for modal visibility and form fields:
```typescript
const [showModal, setShowModal] = useState(false);
const [title, setTitle] = useState('');
const [category, setCategory] = useState('HR_POLICY');
const [description, setDescription] = useState('');
const [version, setVersion] = useState('1.0');
const [uploadedKey, setUploadedKey] = useState('');
const [uploadedFileName, setUploadedFileName] = useState('');
```

Upload hook:
```typescript
const { upload, isUploading, error: uploadError, reset: resetUpload } = useFileUpload({
  category: 'policy-document',
  entityId: 'policy',
});
```

Modal with:
- Title input
- Category selector (8 options matching web: HR_POLICY, LEAVE_POLICY, ATTENDANCE_POLICY, CODE_OF_CONDUCT, SAFETY, TRAVEL, IT_POLICY, OTHER)
- Description input
- Version input
- File picker (PDF only: `type: ['application/pdf']`)
- Submit button

- [ ] **Step 4: Add FAB button for admin**

```typescript
{isAdmin && (
  <FAB icon="plus" onPress={() => setShowModal(true)} />
)}
```

- [ ] **Step 5: Add delete support for admin**

On each policy card, if `isAdmin`:
```typescript
<Pressable onPress={() => handleDelete(policy.id)}>
  <Trash2 size={16} color={colors.danger[500]} />
</Pressable>
```

- [ ] **Step 6: Verify type-check**

```bash
cd mobile-app && pnpm type-check
```

- [ ] **Step 7: Commit**

```bash
git add mobile-app/src/features/ess/policy-documents-screen.tsx
git commit -m "feat(mobile): add admin upload and delete for policy documents"
```

---
