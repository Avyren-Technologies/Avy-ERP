# Recruitment & Training Enhancement — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Fix data integrity issues, add offer management, candidate profiles, training sessions/attendance/evaluations, learning paths, and cross-cutting infrastructure (state machines, notifications via FCM, audit trail, event system, granular permissions).

**Architecture:** 4-phase approach — Phase 1 fixes foundation (schema, indexes, mismatches), Phase 2 adds recruitment features (offers, candidate enrichment, evaluations, conversion), Phase 3 adds training features (sessions, attendance, feedback, trainers), Phase 4 adds advanced features (programs, budgets, materials). Cross-cutting concerns (state machine, notifications, audit, events, permissions) are built incrementally across phases.

**Tech Stack:** Node.js/Express, Prisma (PostgreSQL), Zod, React (Vite), React Native (Expo), React Query, Zustand, Firebase Cloud Messaging, Redis

**Spec:** `docs/superpowers/specs/2026-04-05-recruitment-training-enhancement-design.md`

---

## Phase 1 — Data Integrity, Indexes & Foundation

**Checkpoint:** After Phase 1, all existing screens work correctly with proper field persistence, status enums match across stack, queries are indexed, and the state machine utility is available for all subsequent phases.

---

### Task 1.1: Create State Machine Utility

**Files:**
- Create: `avy-erp-backend/src/shared/utils/state-machine.ts`

This utility is used by ALL status update endpoints across all phases.

- [ ] **Step 1: Create the state machine utility**

```typescript
// avy-erp-backend/src/shared/utils/state-machine.ts
import { ApiError } from '../errors';

export function validateTransition<T extends string>(
  currentState: T,
  newState: T,
  allowedTransitions: Record<string, string[]>,
  entityName: string,
): void {
  const allowed = allowedTransitions[currentState];
  if (!allowed || !allowed.includes(newState)) {
    throw ApiError.badRequest(
      `Invalid ${entityName} transition: cannot move from "${currentState}" to "${newState}"`,
    );
  }
}

// --- Recruitment Transitions ---

export const REQUISITION_TRANSITIONS: Record<string, string[]> = {
  DRAFT: ['OPEN', 'CANCELLED'],
  OPEN: ['INTERVIEWING', 'CANCELLED'],
  INTERVIEWING: ['OFFERED', 'CANCELLED'],
  OFFERED: ['FILLED', 'INTERVIEWING', 'CANCELLED'],
  FILLED: [],
  CANCELLED: [],
};

export const CANDIDATE_STAGE_TRANSITIONS: Record<string, string[]> = {
  APPLIED: ['SHORTLISTED', 'REJECTED', 'ON_HOLD'],
  SHORTLISTED: ['HR_ROUND', 'REJECTED', 'ON_HOLD'],
  HR_ROUND: ['TECHNICAL', 'REJECTED', 'ON_HOLD'],
  TECHNICAL: ['FINAL', 'REJECTED', 'ON_HOLD'],
  FINAL: ['ASSESSMENT', 'OFFER_SENT', 'REJECTED', 'ON_HOLD'],
  ASSESSMENT: ['OFFER_SENT', 'REJECTED', 'ON_HOLD'],
  OFFER_SENT: ['HIRED', 'REJECTED', 'ON_HOLD'],
  ON_HOLD: ['APPLIED', 'SHORTLISTED', 'HR_ROUND', 'TECHNICAL', 'FINAL', 'ASSESSMENT', 'OFFER_SENT', 'REJECTED'],
  HIRED: [],
  REJECTED: [],
};

export const INTERVIEW_TRANSITIONS: Record<string, string[]> = {
  SCHEDULED: ['COMPLETED', 'CANCELLED', 'NO_SHOW'],
  COMPLETED: [],
  CANCELLED: [],
  NO_SHOW: [],
};

// --- Training Transitions ---

export const NOMINATION_TRANSITIONS: Record<string, string[]> = {
  NOMINATED: ['APPROVED', 'CANCELLED'],
  APPROVED: ['IN_PROGRESS', 'CANCELLED'],
  IN_PROGRESS: ['COMPLETED', 'CANCELLED'],
  COMPLETED: [],
  CANCELLED: [],
};

// --- Offer Transitions (Phase 2) ---

export const OFFER_TRANSITIONS: Record<string, string[]> = {
  DRAFT: ['SENT', 'WITHDRAWN'],
  SENT: ['ACCEPTED', 'REJECTED', 'EXPIRED', 'WITHDRAWN'],
  ACCEPTED: [],
  REJECTED: [],
  WITHDRAWN: [],
  EXPIRED: [],
};

// --- Training Session Transitions (Phase 3) ---

export const SESSION_TRANSITIONS: Record<string, string[]> = {
  SCHEDULED: ['IN_PROGRESS', 'CANCELLED'],
  IN_PROGRESS: ['COMPLETED'],
  COMPLETED: [],
  CANCELLED: [],
};

// --- Program Enrollment Transitions (Phase 4) ---

export const PROGRAM_ENROLLMENT_TRANSITIONS: Record<string, string[]> = {
  ENROLLED: ['IN_PROGRESS', 'ABANDONED'],
  IN_PROGRESS: ['COMPLETED', 'FAILED', 'ABANDONED'],
  COMPLETED: [],
  FAILED: [],
  ABANDONED: [],
};
```

- [ ] **Step 2: Commit**

```bash
cd avy-erp-backend
git add src/shared/utils/state-machine.ts
git commit -m "feat: add state machine utility with transition maps for all HR workflows"
```

---

### Task 1.2: Update Prisma Schemas — Requisition Fields, Nomination Status & Indexes

**Files:**
- Modify: `avy-erp-backend/prisma/modules/hrms/recruitment.prisma`
- Modify: `avy-erp-backend/prisma/modules/hrms/training.prisma`

- [ ] **Step 1: Add new fields and enums to recruitment.prisma**

Add `employmentType`, `priority`, `location`, `requirements`, `experienceMin`, `experienceMax` fields to `JobRequisition` model and add the two new enums. Add indexes to all three models.

In `recruitment.prisma`, update the `JobRequisition` model (after the `approvedBy` field, before `companyId`) to add:

```prisma
  employmentType  EmploymentType?
  priority        RequisitionPriority?
  location        String?
  requirements    String?
  experienceMin   Int?
  experienceMax   Int?
```

Add the `@@index` directives inside each model (before the closing brace and `@@map`):

For `JobRequisition`:
```prisma
  @@index([companyId, status])
```

For `Candidate`:
```prisma
  @@index([companyId, stage])
  @@index([requisitionId, stage])
  @@index([email])
```

For `Interview`:
```prisma
  @@index([companyId, status])
  @@index([candidateId, status])
  @@index([scheduledAt])
```

Add the two new enums at the end of the file:

```prisma
enum EmploymentType {
  FULL_TIME
  PART_TIME
  CONTRACT
  INTERNSHIP
}

enum RequisitionPriority {
  LOW
  MEDIUM
  HIGH
  URGENT
}
```

- [ ] **Step 2: Update training.prisma — add APPROVED/IN_PROGRESS statuses and indexes**

Update the `TrainingNominationStatus` enum to:

```prisma
enum TrainingNominationStatus {
  NOMINATED
  APPROVED
  IN_PROGRESS
  COMPLETED
  CANCELLED
}
```

Add indexes to both models:

For `TrainingCatalogue`:
```prisma
  @@index([companyId, isActive])
```

For `TrainingNomination`:
```prisma
  @@index([companyId, status])
  @@index([employeeId, status])
```

- [ ] **Step 3: Merge and generate Prisma client**

```bash
cd avy-erp-backend
pnpm prisma:merge && pnpm db:generate
```

- [ ] **Step 4: Create migration**

```bash
cd avy-erp-backend
pnpm db:migrate -- --name add_requisition_fields_nomination_status_indexes
```

- [ ] **Step 5: Commit**

```bash
cd avy-erp-backend
git add prisma/
git commit -m "feat: add requisition detail fields, nomination APPROVED/IN_PROGRESS status, DB indexes"
```

---

### Task 1.3: Update Backend Validators

**Files:**
- Modify: `avy-erp-backend/src/modules/hr/advanced/advanced.validators.ts`

- [ ] **Step 1: Update createRequisitionSchema to include new fields**

Find the `createRequisitionSchema` (around line 7) and add the new fields:

```typescript
export const createRequisitionSchema = z.object({
  title: z.string().min(1, 'Title is required'),
  designationId: z.string().optional(),
  departmentId: z.string().optional(),
  openings: z.number().int().positive().optional(),
  description: z.string().optional(),
  budgetMin: z.number().positive().optional(),
  budgetMax: z.number().positive().optional(),
  targetDate: z.string().optional(),
  sourceChannels: z.array(z.string()).optional(),
  approvedBy: z.string().optional(),
  employmentType: z.enum(['FULL_TIME', 'PART_TIME', 'CONTRACT', 'INTERNSHIP']).optional(),
  priority: z.enum(['LOW', 'MEDIUM', 'HIGH', 'URGENT']).optional(),
  location: z.string().optional(),
  requirements: z.string().optional(),
  experienceMin: z.number().int().min(0).optional(),
  experienceMax: z.number().int().min(0).optional(),
});
```

- [ ] **Step 2: Update advanceCandidateStageSchema to require reason for REJECTED/ON_HOLD**

Replace the existing `advanceCandidateStageSchema`:

```typescript
export const advanceCandidateStageSchema = z.object({
  stage: z.enum([
    'APPLIED', 'SHORTLISTED', 'HR_ROUND', 'TECHNICAL', 'FINAL',
    'ASSESSMENT', 'OFFER_SENT', 'HIRED', 'REJECTED', 'ON_HOLD',
  ]),
  reason: z.string().optional(),
  notes: z.string().optional(),
}).refine(
  (data) => {
    if (data.stage === 'REJECTED' || data.stage === 'ON_HOLD') {
      return !!data.reason;
    }
    return true;
  },
  { message: 'Reason is required when rejecting or putting on hold', path: ['reason'] },
);
```

- [ ] **Step 3: Update updateTrainingNominationSchema to include new statuses**

Update the status field in `updateTrainingNominationSchema` to include APPROVED and IN_PROGRESS:

```typescript
export const updateTrainingNominationSchema = z.object({
  status: z.enum(['NOMINATED', 'APPROVED', 'IN_PROGRESS', 'COMPLETED', 'CANCELLED']).optional(),
  completionDate: z.string().optional(),
  score: z.number().min(0).max(100).optional(),
  certificateUrl: z.string().optional(),
});
```

- [ ] **Step 4: Commit**

```bash
cd avy-erp-backend
git add src/modules/hr/advanced/advanced.validators.ts
git commit -m "feat: update validators for requisition fields, stage reasons, nomination statuses"
```

---

### Task 1.4: Update Backend Service — State Machine & New Fields

**Files:**
- Modify: `avy-erp-backend/src/modules/hr/advanced/advanced.service.ts`

- [ ] **Step 1: Add state machine import at top of service file**

Add to the imports section (around line 5):

```typescript
import {
  validateTransition,
  REQUISITION_TRANSITIONS,
  CANDIDATE_STAGE_TRANSITIONS,
  INTERVIEW_TRANSITIONS,
  NOMINATION_TRANSITIONS,
} from '../../../shared/utils/state-machine';
```

- [ ] **Step 2: Update createRequisition to persist new fields**

In `createRequisition` method (around line 155), update the `create` data object to include:

```typescript
employmentType: n(data.employmentType),
priority: n(data.priority),
location: n(data.location),
requirements: n(data.requirements),
experienceMin: n(data.experienceMin),
experienceMax: n(data.experienceMax),
```

- [ ] **Step 3: Update updateRequisition to persist new fields**

In `updateRequisition` method (around line 196), add the new fields to the update data:

```typescript
...(data.employmentType !== undefined && { employmentType: n(data.employmentType) }),
...(data.priority !== undefined && { priority: n(data.priority) }),
...(data.location !== undefined && { location: n(data.location) }),
...(data.requirements !== undefined && { requirements: n(data.requirements) }),
...(data.experienceMin !== undefined && { experienceMin: n(data.experienceMin) }),
...(data.experienceMax !== undefined && { experienceMax: n(data.experienceMax) }),
```

- [ ] **Step 4: Wire state machine into updateRequisitionStatus**

In `updateRequisitionStatus` method (around line 224), replace any existing status transition logic with:

```typescript
validateTransition(requisition.status, status, REQUISITION_TRANSITIONS, 'requisition status');
```

- [ ] **Step 5: Wire state machine into advanceCandidateStage**

In `advanceCandidateStage` method (around line 355), replace existing stage validation with:

```typescript
validateTransition(candidate.stage, stage, CANDIDATE_STAGE_TRANSITIONS, 'candidate stage');
```

- [ ] **Step 6: Wire state machine into completeInterview and cancelInterview**

In `completeInterview` (around line 479), replace the status check with:

```typescript
validateTransition(interview.status, 'COMPLETED', INTERVIEW_TRANSITIONS, 'interview status');
```

In `cancelInterview` (around line 498), replace the status check with:

```typescript
validateTransition(interview.status, 'CANCELLED', INTERVIEW_TRANSITIONS, 'interview status');
```

- [ ] **Step 7: Wire state machine into updateTrainingNomination**

In `updateTrainingNomination` (around line 757), if status is being changed, add:

```typescript
if (data.status) {
  validateTransition(nomination.status, data.status, NOMINATION_TRANSITIONS, 'nomination status');
}
```

- [ ] **Step 8: Commit**

```bash
cd avy-erp-backend
git add src/modules/hr/advanced/advanced.service.ts
git commit -m "feat: wire state machine transitions, persist new requisition fields"
```

---

### Task 1.5: Wire System Controls Nav Gating

**Files:**
- Modify: `avy-erp-backend/src/core/rbac/rbac.service.ts`

- [ ] **Step 1: Add recruitment/training entries to NAV_TO_SYSTEM_MODULE**

Find `NAV_TO_SYSTEM_MODULE` (around line 44) and add entries:

```typescript
'hr-requisitions': 'recruitmentEnabled',
'hr-candidates': 'recruitmentEnabled',
'hr-analytics-recruitment': 'recruitmentEnabled',
'hr-training': 'trainingEnabled',
'hr-nominations': 'trainingEnabled',
'ess-training': 'trainingEnabled',
```

- [ ] **Step 2: Commit**

```bash
cd avy-erp-backend
git add src/core/rbac/rbac.service.ts
git commit -m "feat: gate recruitment/training nav items via system controls"
```

---

### Task 1.6: Update Web API Client & Hooks

**Files:**
- Modify: `web-system-app/src/lib/api/recruitment.ts`

- [ ] **Step 1: Add missing API functions for interview complete/cancel and candidate delete**

Add these functions to the recruitment API file (after existing interview functions, around line 85):

```typescript
completeInterview: async (id: string, data: { feedbackRating: number; feedbackNotes?: string }) => {
  const response = await client.patch(`/hr/interviews/${id}/complete`, data);
  return response.data;
},

cancelInterview: async (id: string) => {
  const response = await client.patch(`/hr/interviews/${id}/cancel`);
  return response.data;
},

deleteCandidate: async (id: string) => {
  const response = await client.delete(`/hr/candidates/${id}`);
  return response.data;
},

advanceCandidateStage: async (id: string, data: { stage: string; reason?: string; notes?: string }) => {
  const response = await client.patch(`/hr/candidates/${id}/stage`, data);
  return response.data;
},
```

- [ ] **Step 2: Add mutation hooks**

In `web-system-app/src/features/company-admin/api/use-recruitment-mutations.ts`, add:

```typescript
export function useCompleteInterview() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: { feedbackRating: number; feedbackNotes?: string } }) =>
      recruitmentApi.completeInterview(id, data),
    onSuccess: () => { qc.invalidateQueries({ queryKey: recruitmentKeys.all }); },
  });
}

export function useCancelInterview() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => recruitmentApi.cancelInterview(id),
    onSuccess: () => { qc.invalidateQueries({ queryKey: recruitmentKeys.all }); },
  });
}

export function useDeleteCandidate() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => recruitmentApi.deleteCandidate(id),
    onSuccess: () => { qc.invalidateQueries({ queryKey: recruitmentKeys.all }); },
  });
}

export function useAdvanceCandidateStage() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: { stage: string; reason?: string; notes?: string } }) =>
      recruitmentApi.advanceCandidateStage(id, data),
    onSuccess: () => { qc.invalidateQueries({ queryKey: recruitmentKeys.all }); },
  });
}
```

- [ ] **Step 3: Commit**

```bash
cd web-system-app
git add src/lib/api/recruitment.ts src/features/company-admin/api/use-recruitment-mutations.ts
git commit -m "feat: add web API functions and hooks for interview complete/cancel, candidate delete/stage"
```

---

### Task 1.7: Wire Missing Actions in Web RequisitionScreen

**Files:**
- Modify: `web-system-app/src/features/company-admin/hr/RequisitionScreen.tsx`

- [ ] **Step 1: Import new mutation hooks**

Add to imports:

```typescript
import { useCompleteInterview, useCancelInterview, useDeleteCandidate, useAdvanceCandidateStage } from '../api/use-recruitment-mutations';
```

- [ ] **Step 2: Initialize hooks in component**

Inside the `RequisitionScreen` function, add:

```typescript
const completeInterview = useCompleteInterview();
const cancelInterview = useCancelInterview();
const deleteCandidate = useDeleteCandidate();
const advanceStage = useAdvanceCandidateStage();
```

- [ ] **Step 3: Add Complete and Cancel buttons to interview table rows**

In the Interviews tab's table actions column, add alongside the existing Edit button:

```tsx
{row.status === 'SCHEDULED' && (
  <>
    <button
      className="text-xs text-green-600 hover:text-green-800"
      onClick={() => {
        // Open a small modal to collect feedbackRating + feedbackNotes
        setCompletingInterview(row);
      }}
    >
      Complete
    </button>
    <button
      className="text-xs text-red-600 hover:text-red-800"
      onClick={() => {
        if (confirm('Cancel this interview?')) {
          cancelInterview.mutate(row.id, {
            onSuccess: () => showSuccess('Interview cancelled'),
            onError: showApiError,
          });
        }
      }}
    >
      Cancel
    </button>
  </>
)}
```

- [ ] **Step 4: Add Delete button to candidate table rows**

In the Candidates tab's table actions column, add:

```tsx
<button
  className="text-xs text-red-600 hover:text-red-800"
  onClick={() => {
    if (confirm('Delete this candidate?')) {
      deleteCandidate.mutate(row.id, {
        onSuccess: () => showSuccess('Candidate deleted'),
        onError: showApiError,
      });
    }
  }}
>
  Delete
</button>
```

- [ ] **Step 5: Fix candidate name — use single name field instead of firstName/lastName**

Replace the split `firstName` / `lastName` inputs with a single `name` input:

```tsx
<input
  type="text"
  placeholder="Full Name"
  value={candidateForm.name || ''}
  onChange={(e) => setCandidateForm({ ...candidateForm, name: e.target.value })}
  className="..."
/>
```

Update the create payload to send `name` directly instead of combining `firstName` and `lastName`.

- [ ] **Step 6: Add new requisition form fields**

Add `employmentType`, `priority`, `location`, `requirements`, `experienceMin`, `experienceMax` fields to the requisition create/edit form. Map these to the API payload directly. The existing form likely already has some of these fields — ensure the payload sends the correct field names matching the backend schema.

- [ ] **Step 7: Commit**

```bash
cd web-system-app
git add src/features/company-admin/hr/RequisitionScreen.tsx
git commit -m "feat: wire interview complete/cancel, candidate delete, fix name field, add requisition detail fields"
```

---

### Task 1.8: Update Mobile API Client & Hooks

**Files:**
- Modify: `mobile-app/src/lib/api/recruitment.ts`
- Modify: `mobile-app/src/features/company-admin/api/use-recruitment-mutations.ts`

- [ ] **Step 1: Add missing API functions to mobile API client**

In `mobile-app/src/lib/api/recruitment.ts`, add to the `recruitmentApi` object:

```typescript
completeInterview: async (id: string, data: { feedbackRating: number; feedbackNotes?: string }) => {
  const response = await client.patch(`/hr/interviews/${id}/complete`, data);
  return response.data;
},

cancelInterview: async (id: string) => {
  const response = await client.patch(`/hr/interviews/${id}/cancel`);
  return response.data;
},

deleteCandidate: async (id: string) => {
  const response = await client.delete(`/hr/candidates/${id}`);
  return response.data;
},

advanceCandidateStage: async (id: string, data: { stage: string; reason?: string; notes?: string }) => {
  const response = await client.patch(`/hr/candidates/${id}/stage`, data);
  return response.data;
},
```

- [ ] **Step 2: Add mutation hooks to mobile**

In `mobile-app/src/features/company-admin/api/use-recruitment-mutations.ts`, add (same pattern as web):

```typescript
export function useCompleteInterview() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: { feedbackRating: number; feedbackNotes?: string } }) =>
      recruitmentApi.completeInterview(id, data),
    onSuccess: () => { qc.invalidateQueries({ queryKey: recruitmentKeys.all }); },
  });
}

export function useCancelInterview() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => recruitmentApi.cancelInterview(id),
    onSuccess: () => { qc.invalidateQueries({ queryKey: recruitmentKeys.all }); },
  });
}

export function useDeleteCandidate() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => recruitmentApi.deleteCandidate(id),
    onSuccess: () => { qc.invalidateQueries({ queryKey: recruitmentKeys.all }); },
  });
}

export function useAdvanceCandidateStage() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: { stage: string; reason?: string; notes?: string } }) =>
      recruitmentApi.advanceCandidateStage(id, data),
    onSuccess: () => { qc.invalidateQueries({ queryKey: recruitmentKeys.all }); },
  });
}
```

- [ ] **Step 3: Commit**

```bash
cd mobile-app
git add src/lib/api/recruitment.ts src/features/company-admin/api/use-recruitment-mutations.ts
git commit -m "feat: add mobile API functions and hooks for interview complete/cancel, candidate delete/stage"
```

---

### Task 1.9: Wire Missing Actions in Mobile RequisitionsScreen

**Files:**
- Modify: `mobile-app/src/features/company-admin/hr/requisitions-screen.tsx`

- [ ] **Step 1: Import new hooks**

```typescript
import { useCompleteInterview, useCancelInterview, useDeleteCandidate } from '@/features/company-admin/api/use-recruitment-mutations';
```

- [ ] **Step 2: Add Complete/Cancel buttons to interview cards**

In the Interview card component, for interviews with status `SCHEDULED`, add action buttons in the card footer:

```tsx
{item.status === 'SCHEDULED' && (
  <View style={styles.cardFooter}>
    <Pressable
      style={[styles.actionBtn, { backgroundColor: colors.success[50] }]}
      onPress={() => {
        // Show feedback modal, then call completeInterview.mutate({ id: item.id, data: { feedbackRating, feedbackNotes } })
      }}
    >
      <Text className="font-inter text-xs" style={{ color: colors.success[700] }}>Complete</Text>
    </Pressable>
    <Pressable
      style={[styles.actionBtn, { backgroundColor: colors.danger[50] }]}
      onPress={() => {
        showConfirm({
          title: 'Cancel Interview',
          message: 'Are you sure you want to cancel this interview?',
          onConfirm: () => cancelInterview.mutate(item.id),
        });
      }}
    >
      <Text className="font-inter text-xs" style={{ color: colors.danger[700] }}>Cancel</Text>
    </Pressable>
  </View>
)}
```

- [ ] **Step 3: Add Delete button to candidate cards**

Add a delete action in the candidate card footer:

```tsx
<Pressable
  style={[styles.actionBtn, { backgroundColor: colors.danger[50] }]}
  onPress={() => {
    showConfirm({
      title: 'Delete Candidate',
      message: `Delete ${item.name}? This cannot be undone.`,
      onConfirm: () => deleteCandidate.mutate(item.id),
    });
  }}
>
  <Text className="font-inter text-xs" style={{ color: colors.danger[700] }}>Delete</Text>
</Pressable>
```

- [ ] **Step 4: Add new requisition form fields to mobile**

Update the requisition create/edit modal to include: Employment Type (ChipSelector), Priority (ChipSelector), Location (TextInput), Requirements (TextArea), Experience Min/Max (number inputs).

- [ ] **Step 5: Commit**

```bash
cd mobile-app
git add src/features/company-admin/hr/requisitions-screen.tsx
git commit -m "feat: wire interview complete/cancel, candidate delete, add requisition detail fields on mobile"
```

---

### Task 1.10: Fix Mobile Training Nomination Status Values

**Files:**
- Modify: `mobile-app/src/features/company-admin/hr/training-screen.tsx`

- [ ] **Step 1: Update NominationStatus type and status mappings**

Update the type and color mappings to include APPROVED and IN_PROGRESS:

```typescript
type NominationStatus = 'Nominated' | 'Approved' | 'In Progress' | 'Completed' | 'Cancelled';

const NOM_STATUS_COLORS: Record<string, { bg: string; text: string; dot: string }> = {
  Nominated: { bg: colors.info[50], text: colors.info[700], dot: colors.info[500] },
  Approved: { bg: colors.primary[50], text: colors.primary[700], dot: colors.primary[500] },
  'In Progress': { bg: colors.warning[50], text: colors.warning[700], dot: colors.warning[500] },
  Completed: { bg: colors.success[50], text: colors.success[700], dot: colors.success[500] },
  Cancelled: { bg: colors.neutral[100], text: colors.neutral[600], dot: colors.neutral[400] },
};
```

- [ ] **Step 2: Update nomination card action buttons to respect new statuses**

Action buttons should appear for NOMINATED and APPROVED statuses (not just NOMINATED/ENROLLED):

```typescript
const canAct = item.status === 'NOMINATED' || item.status === 'APPROVED' || item.status === 'IN_PROGRESS';
```

Complete button should only show for IN_PROGRESS, Cancel for NOMINATED/APPROVED/IN_PROGRESS.

- [ ] **Step 3: Commit**

```bash
cd mobile-app
git add src/features/company-admin/hr/training-screen.tsx
git commit -m "feat: add APPROVED/IN_PROGRESS nomination statuses to mobile training screen"
```

---

### Phase 1 Review Checkpoint

At this point:
- [ ] State machine utility exists and is wired into all existing status endpoints
- [ ] Prisma schema has new requisition fields, nomination statuses, and indexes
- [ ] Backend validators accept new fields and require rejection reasons
- [ ] Backend service persists new fields and uses state machine transitions
- [ ] System controls gate recruitment/training nav items
- [ ] Web and mobile have interview complete/cancel and candidate delete buttons
- [ ] Web and mobile requisition forms include employment type, priority, location, etc.
- [ ] Mobile training screen handles APPROVED and IN_PROGRESS nomination statuses
- [ ] Run `pnpm build` in backend, `pnpm build` in web, `pnpm type-check` in mobile to verify no errors

---

## Phase 2 — Recruitment Enhancements

**Checkpoint:** After Phase 2, offer management is fully functional, candidates have detailed profiles (education, experience, documents), interviews have structured evaluations, stage history is tracked, and candidates can be converted to employees.

---

### Task 2.1: Prisma Schema — Offer, Candidate Profile, Evaluation, Stage History Models

**Files:**
- Modify: `avy-erp-backend/prisma/modules/hrms/recruitment.prisma`

- [ ] **Step 1: Add all new models and enums to recruitment.prisma**

Append after the existing `InterviewStatus` enum:

```prisma
model CandidateOffer {
  id              String           @id @default(cuid())
  offerNumber     String?
  candidateId     String
  candidate       Candidate        @relation(fields: [candidateId], references: [id], onDelete: Cascade)
  designationId   String?
  designation     Designation?     @relation(fields: [designationId], references: [id])
  departmentId    String?
  department      Department?      @relation(fields: [departmentId], references: [id])
  offeredCtc      Decimal          @db.Decimal(15, 2)
  ctcBreakup      Json?
  joiningDate     DateTime?        @db.Date
  offerLetterUrl  String?
  validUntil      DateTime?        @db.Date
  status          OfferStatus      @default(DRAFT)
  acceptedAt      DateTime?
  rejectedAt      DateTime?
  rejectionReason String?
  withdrawnAt     DateTime?
  notes           String?
  companyId       String
  company         Company          @relation(fields: [companyId], references: [id], onDelete: Cascade)
  createdAt       DateTime         @default(now())
  updatedAt       DateTime         @updatedAt

  @@index([companyId, status])
  @@index([candidateId])
  @@map("candidate_offers")
}

enum OfferStatus {
  DRAFT
  SENT
  ACCEPTED
  REJECTED
  WITHDRAWN
  EXPIRED
}

model CandidateEducation {
  id            String    @id @default(cuid())
  candidateId   String
  candidate     Candidate @relation(fields: [candidateId], references: [id], onDelete: Cascade)
  qualification String
  degree        String?
  institution   String?
  university    String?
  yearOfPassing Int?
  percentage    Decimal?  @db.Decimal(5, 2)
  certificateUrl String?
  companyId     String
  company       Company   @relation(fields: [companyId], references: [id], onDelete: Cascade)
  createdAt     DateTime  @default(now())
  updatedAt     DateTime  @updatedAt

  @@index([candidateId])
  @@map("candidate_education")
}

model CandidateExperience {
  id               String    @id @default(cuid())
  candidateId      String
  candidate        Candidate @relation(fields: [candidateId], references: [id], onDelete: Cascade)
  companyName      String
  designation      String
  fromDate         DateTime? @db.Date
  toDate           DateTime? @db.Date
  currentlyWorking Boolean   @default(false)
  ctc              Decimal?  @db.Decimal(15, 2)
  description      String?
  companyId        String
  company          Company   @relation(fields: [companyId], references: [id], onDelete: Cascade)
  createdAt        DateTime  @default(now())
  updatedAt        DateTime  @updatedAt

  @@index([candidateId])
  @@map("candidate_experience")
}

model CandidateDocument {
  id           String    @id @default(cuid())
  candidateId  String
  candidate    Candidate @relation(fields: [candidateId], references: [id], onDelete: Cascade)
  documentType String
  fileName     String
  fileUrl      String
  companyId    String
  company      Company   @relation(fields: [companyId], references: [id], onDelete: Cascade)
  createdAt    DateTime  @default(now())
  updatedAt    DateTime  @updatedAt

  @@index([candidateId])
  @@map("candidate_documents")
}

model InterviewEvaluation {
  id             String             @id @default(cuid())
  interviewId    String
  interview      Interview          @relation(fields: [interviewId], references: [id], onDelete: Cascade)
  evaluatorId    String
  dimension      String
  rating         Int
  comments       String?
  recommendation EvalRecommendation
  companyId      String
  company        Company            @relation(fields: [companyId], references: [id], onDelete: Cascade)
  createdAt      DateTime           @default(now())
  updatedAt      DateTime           @updatedAt

  @@index([interviewId])
  @@map("interview_evaluations")
}

enum EvalRecommendation {
  STRONG_HIRE
  HIRE
  MAYBE
  NO_HIRE
  STRONG_NO_HIRE
}

model CandidateStageHistory {
  id          String         @id @default(cuid())
  candidateId String
  candidate   Candidate      @relation(fields: [candidateId], references: [id], onDelete: Cascade)
  fromStage   CandidateStage
  toStage     CandidateStage
  reason      String?
  notes       String?
  changedBy   String?
  changedAt   DateTime       @default(now())
  companyId   String
  company     Company        @relation(fields: [companyId], references: [id], onDelete: Cascade)

  @@index([candidateId])
  @@map("candidate_stage_history")
}
```

Also update the `Candidate` model to add relations and `employeeId`:

```prisma
  employeeId     String?
  offers         CandidateOffer[]
  education      CandidateEducation[]
  experience     CandidateExperience[]
  documents      CandidateDocument[]
  stageHistory   CandidateStageHistory[]
```

Update the `Interview` model to add:

```prisma
  evaluations    InterviewEvaluation[]
```

- [ ] **Step 2: Add linked screen entries for number series**

In `src/shared/constants/linked-screens.ts`, add after the Training entry:

```typescript
{
  value: 'Offer Management',
  label: 'Offer Management',
  module: 'HR',
  description: 'Reference numbers for job offers',
  defaultPrefix: 'OFF-',
},
```

- [ ] **Step 3: Merge, generate, and migrate**

```bash
cd avy-erp-backend
pnpm prisma:merge && pnpm db:generate
pnpm db:migrate -- --name add_offers_candidate_profile_evaluations_stage_history
```

- [ ] **Step 4: Commit**

```bash
cd avy-erp-backend
git add prisma/ src/shared/constants/linked-screens.ts
git commit -m "feat: add Prisma models for offers, candidate profile, evaluations, stage history"
```

---

### Task 2.2: Backend — Offer Service, Validators, Controller, Routes

**Files:**
- Create: `avy-erp-backend/src/modules/hr/advanced/offer.validators.ts`
- Create: `avy-erp-backend/src/modules/hr/advanced/offer.service.ts`
- Create: `avy-erp-backend/src/modules/hr/advanced/offer.controller.ts`
- Create: `avy-erp-backend/src/modules/hr/advanced/offer.routes.ts`
- Modify: `avy-erp-backend/src/modules/hr/advanced/advanced.routes.ts` (mount offer routes)

Given the size of this task, the implementing agent should:

- [ ] **Step 1: Create offer validators** with schemas for createOffer, updateOffer, updateOfferStatus
- [ ] **Step 2: Create offer service** with methods: listOffers, getOffer, createOffer (with generateNextNumber for OFF- prefix), updateOffer, updateOfferStatus (with validateTransition using OFFER_TRANSITIONS), deleteOffer. When offer → ACCEPTED, auto-advance candidate stage to HIRED via advanceCandidateStage. Implement lazy expiry: in listOffers and getOffer, check if status=SENT and validUntil < now(), if so auto-update to EXPIRED before returning.
- [ ] **Step 3: Create offer controller** following asyncHandler pattern from existing controller
- [ ] **Step 4: Create offer routes** with `requirePermissions` guards
- [ ] **Step 5: Mount offer routes** in advanced.routes.ts
- [ ] **Step 6: Commit**

```bash
cd avy-erp-backend
git add src/modules/hr/advanced/offer.*
git commit -m "feat: add offer management backend (CRUD + status transitions)"
```

---

### Task 2.3: Backend — Candidate Profile Endpoints (Education, Experience, Documents)

**Files:**
- Create: `avy-erp-backend/src/modules/hr/advanced/candidate-profile.validators.ts`
- Create: `avy-erp-backend/src/modules/hr/advanced/candidate-profile.service.ts`
- Create: `avy-erp-backend/src/modules/hr/advanced/candidate-profile.controller.ts`
- Create: `avy-erp-backend/src/modules/hr/advanced/candidate-profile.routes.ts`
- Modify: `avy-erp-backend/src/modules/hr/advanced/advanced.routes.ts` (mount routes)

- [ ] **Step 1: Create validators** for createEducation, updateEducation, createExperience, updateExperience, createDocument
- [ ] **Step 2: Create service** with CRUD for all three models, nested under candidate (validate candidate ownership)
- [ ] **Step 3: Create controller** following existing pattern
- [ ] **Step 4: Create routes** — `GET/POST /candidates/:id/education`, `PATCH/DELETE /candidate-education/:id`, same for experience and documents
- [ ] **Step 5: Mount in advanced.routes.ts**
- [ ] **Step 6: Commit**

```bash
cd avy-erp-backend
git add src/modules/hr/advanced/candidate-profile.*
git commit -m "feat: add candidate education, experience, documents endpoints"
```

---

### Task 2.4: Backend — Interview Evaluations & Stage History

**Files:**
- Create: `avy-erp-backend/src/modules/hr/advanced/evaluation.validators.ts`
- Create: `avy-erp-backend/src/modules/hr/advanced/evaluation.service.ts`
- Create: `avy-erp-backend/src/modules/hr/advanced/evaluation.controller.ts`
- Create: `avy-erp-backend/src/modules/hr/advanced/evaluation.routes.ts`
- Modify: `avy-erp-backend/src/modules/hr/advanced/advanced.service.ts` (stage history auto-creation)

- [ ] **Step 1: Create evaluation validators** — createEvaluation schema (array of {dimension, rating, comments, recommendation})
- [ ] **Step 2: Create evaluation service** — submitEvaluations (bulk create), listEvaluationsForInterview
- [ ] **Step 3: Create evaluation controller and routes** — `POST/GET /interviews/:id/evaluations` with `recruitment:read` for GET and `training-evaluation:create` for POST (shared evaluation permission module covers both interview and training evaluations)
- [ ] **Step 4: Wire stage history into advanceCandidateStage** — after the stage update in the service, create a CandidateStageHistory record with fromStage, toStage, reason, notes, changedBy (from userId)
- [ ] **Step 5: Update getCandidate** to include stageHistory in the response (ordered by changedAt desc)
- [ ] **Step 6: Mount evaluation routes and commit**

```bash
cd avy-erp-backend
git add src/modules/hr/advanced/evaluation.* src/modules/hr/advanced/advanced.service.ts
git commit -m "feat: add interview evaluations and auto-create candidate stage history"
```

---

### Task 2.5: Backend — Candidate-to-Employee Conversion

**Files:**
- Modify: `avy-erp-backend/src/modules/hr/advanced/advanced.service.ts`
- Modify: `avy-erp-backend/src/modules/hr/advanced/advanced.controller.ts`
- Modify: `avy-erp-backend/src/modules/hr/advanced/advanced.routes.ts`

- [ ] **Step 1: Add convertCandidateToEmployee service method**

```typescript
async convertCandidateToEmployee(companyId: string, candidateId: string, userId: string) {
  const prisma = getTenantPrisma(companyId);

  const candidate = await prisma.candidate.findFirst({ where: { id: candidateId, companyId } });
  if (!candidate) throw ApiError.notFound('Candidate not found');
  if (candidate.stage !== 'HIRED') throw ApiError.badRequest('Only HIRED candidates can be converted');

  const offer = await prisma.candidateOffer.findFirst({
    where: { candidateId, companyId, status: 'ACCEPTED' },
    include: { designation: true, department: true },
  });

  // Create employee with pre-populated data
  const employee = await prisma.employee.create({
    data: {
      employeeNumber: await generateNextNumber(platformPrisma, companyId, 'Employee', 'Employee'),
      firstName: candidate.name.split(' ')[0],
      lastName: candidate.name.split(' ').slice(1).join(' ') || '',
      email: candidate.email,
      phone: candidate.phone,
      designationId: offer?.designationId,
      departmentId: offer?.departmentId,
      joiningDate: offer?.joiningDate,
      status: 'PROBATION',
      companyId,
    },
  });

  // Link candidate to employee
  await prisma.candidate.update({
    where: { id: candidateId },
    data: { employeeId: employee.id },
  });

  // Auto-assign mandatory trainings
  const mandatoryTrainings = await prisma.trainingCatalogue.findMany({
    where: { companyId, mandatory: true, isActive: true },
  });

  for (const training of mandatoryTrainings) {
    await prisma.trainingNomination.create({
      data: { employeeId: employee.id, trainingId: training.id, status: 'NOMINATED', companyId },
    });
  }

  return employee;
}
```

- [ ] **Step 2: Add controller method and route** — `POST /candidates/:id/convert-to-employee` with `requirePermissions(['hr:configure'])`
- [ ] **Step 3: Commit**

```bash
cd avy-erp-backend
git add src/modules/hr/advanced/
git commit -m "feat: add candidate-to-employee conversion with mandatory training auto-assign"
```

---

### Task 2.6: Web — Offer Management UI

**Files:**
- Modify: `web-system-app/src/lib/api/recruitment.ts` (add offer API functions)
- Modify: `web-system-app/src/features/company-admin/api/use-recruitment-queries.ts` (add offer hooks)
- Modify: `web-system-app/src/features/company-admin/api/use-recruitment-mutations.ts` (add offer mutations)
- Modify: `web-system-app/src/features/company-admin/hr/RequisitionScreen.tsx` (add Offers tab)

- [ ] **Step 1: Add offer API functions** — listOffers, createOffer, getOffer, updateOffer, updateOfferStatus, deleteOffer
- [ ] **Step 2: Add query key entries** and hooks — useOffers(params), useOffer(id)
- [ ] **Step 3: Add mutation hooks** — useCreateOffer, useUpdateOffer, useUpdateOfferStatus, useDeleteOffer
- [ ] **Step 4: Add "Offers" tab to RequisitionScreen** — Tab 4 alongside Requisitions/Candidates/Interviews. Offer table with: candidate name, offered CTC, joining date, status badge, validity. Create/Edit modal with all offer fields. Status change buttons (Send, Accept, Reject, Withdraw).
- [ ] **Step 5: Commit**

```bash
cd web-system-app
git add src/
git commit -m "feat: add offer management UI to web recruitment screen"
```

---

### Task 2.7: Web — Candidate Detail Screen

**Files:**
- Create: `web-system-app/src/features/company-admin/hr/CandidateDetailScreen.tsx`
- Modify: `web-system-app/src/lib/api/recruitment.ts` (add candidate profile API functions)
- Modify: `web-system-app/src/features/company-admin/api/use-recruitment-queries.ts`
- Modify: `web-system-app/src/features/company-admin/api/use-recruitment-mutations.ts`
- Modify: `web-system-app/src/App.tsx` (add route)

- [ ] **Step 1: Add candidate profile API functions** — CRUD for education, experience, documents
- [ ] **Step 2: Add query hooks** — useCandidateEducation(id), useCandidateExperience(id), useCandidateDocuments(id)
- [ ] **Step 3: Add mutation hooks** — create/update/delete for each
- [ ] **Step 4: Create CandidateDetailScreen** — Profile card (top), Tab Group 1 (Education, Experience, Documents), Tab Group 2 (Interviews with evaluations, Offers, Stage History timeline). "Convert to Employee" button for HIRED candidates. Include "Activity" section at bottom showing audit log entries for this candidate (via `GET /hr/audit-log?entityType=Candidate&entityId=X`, available after CC.3 is implemented — render as empty section until then).
- [ ] **Step 5: Add route** in App.tsx — `<Route path="company/hr/candidates/:id" element={<CandidateDetailScreen />} />`
- [ ] **Step 6: Link from RequisitionScreen** — candidate name clicks navigate to detail page
- [ ] **Step 7: Commit**

```bash
cd web-system-app
git add src/
git commit -m "feat: add candidate detail screen with education, experience, documents, evaluations"
```

---

### Task 2.8: Mobile — Offer Management & Candidate Profile

**Files:**
- Modify: `mobile-app/src/lib/api/recruitment.ts` (add offer + profile APIs)
- Modify: `mobile-app/src/features/company-admin/api/use-recruitment-queries.ts`
- Modify: `mobile-app/src/features/company-admin/api/use-recruitment-mutations.ts`
- Modify: `mobile-app/src/features/company-admin/hr/requisitions-screen.tsx` (add Offers tab)
- Create: `mobile-app/src/features/company-admin/hr/candidate-detail-screen.tsx`
- Create: `mobile-app/src/app/(app)/company/hr/candidate-detail.tsx` (route)

- [ ] **Step 1: Add offer + profile API functions and hooks** (same pattern as web)
- [ ] **Step 2: Add Offers tab to requisitions-screen** following same tab pattern
- [ ] **Step 3: Create candidate-detail-screen** with grouped sections, evaluation forms, stage timeline
- [ ] **Step 4: Add route file** for candidate detail
- [ ] **Step 5: Commit**

```bash
cd mobile-app
git add src/
git commit -m "feat: add offer management and candidate detail screen to mobile"
```

---

### Phase 2 Review Checkpoint

- [ ] Offer CRUD works end-to-end (backend + web + mobile)
- [ ] Candidate education/experience/documents CRUD works
- [ ] Interview evaluations can be submitted and viewed
- [ ] Stage history is auto-created and visible in timeline
- [ ] Candidate-to-employee conversion works with mandatory training auto-assign
- [ ] State machine enforces all offer transitions
- [ ] Run `pnpm build` in backend, `pnpm build` in web, `pnpm type-check` in mobile

---

## Phase 3 — Training Enhancements

**Checkpoint:** After Phase 3, training sessions can be scheduled with attendance tracking, evaluations/feedback are collected, trainers are managed, certificates have lifecycle tracking, and the training dashboard screen exists.

---

### Task 3.1: Prisma Schema — Training Session, Attendance, Evaluation, Trainer, Certificate Fields

**Files:**
- Modify: `avy-erp-backend/prisma/modules/hrms/training.prisma`

- [ ] **Step 1: Add all Phase 3 models and enums** — TrainingSession, TrainingAttendance, TrainingEvaluation, Trainer + enums (TrainingSessionStatus, AttendanceStatus, EvaluationType, CertificateStatus). Add certificate fields to TrainingNomination (certificateNumber, certificateIssuedAt, certificateExpiryDate, certificateStatus). Add `sessionId String?` to TrainingNomination with optional relation to TrainingSession. Add all relations (Trainer.sessions, TrainingSession.attendees/evaluations, etc.).
- [ ] **Step 2: Add Training Session linked screen** in `src/shared/constants/linked-screens.ts` with prefix TSN-
- [ ] **Step 3: Merge, generate, migrate**
- [ ] **Step 4: Commit**

---

### Task 3.2: Backend — Training Session Service + Routes

**Files:**
- Create: `avy-erp-backend/src/modules/hr/advanced/training-session.validators.ts`
- Create: `avy-erp-backend/src/modules/hr/advanced/training-session.service.ts`
- Create: `avy-erp-backend/src/modules/hr/advanced/training-session.controller.ts`
- Create: `avy-erp-backend/src/modules/hr/advanced/training-session.routes.ts`

- [ ] **Step 1: Create validators** — createSession, updateSession, updateSessionStatus
- [ ] **Step 2: Create service** — CRUD + status transitions (using SESSION_TRANSITIONS). On session status → COMPLETED: auto-calculate hoursAttended from check-in/out times for all attendees with PRESENT/LATE status, then for each attendee with sufficient hours, auto-advance their linked TrainingNomination to COMPLETED (trigger certificate auto-issuance if catalogue has certificationName).
- [ ] **Step 3: Create controller and routes** — 6 endpoints with `training:*` permissions
- [ ] **Step 4: Mount routes and commit**

---

### Task 3.3: Backend — Training Attendance Service + Routes

**Files:**
- Create: `avy-erp-backend/src/modules/hr/advanced/training-attendance.validators.ts`
- Create: `avy-erp-backend/src/modules/hr/advanced/training-attendance.service.ts`
- Create: `avy-erp-backend/src/modules/hr/advanced/training-attendance.controller.ts`
- Create: `avy-erp-backend/src/modules/hr/advanced/training-attendance.routes.ts`

- [ ] **Step 1: Create validators** — registerAttendees (bulk), markAttendance, bulkMarkAttendance
- [ ] **Step 2: Create service** — register employees for session, mark individual attendance, bulk mark, list attendees
- [ ] **Step 3: Create controller and routes** — 4 endpoints
- [ ] **Step 4: Mount and commit**

---

### Task 3.4: Backend — Training Evaluation Service + Routes

**Files:**
- Create: `avy-erp-backend/src/modules/hr/advanced/training-evaluation.validators.ts`
- Create: `avy-erp-backend/src/modules/hr/advanced/training-evaluation.service.ts`
- Create: `avy-erp-backend/src/modules/hr/advanced/training-evaluation.controller.ts`
- Create: `avy-erp-backend/src/modules/hr/advanced/training-evaluation.routes.ts`

- [ ] **Step 1: Create validators** — createEvaluation (participant feedback fields), createTrainerAssessment
- [ ] **Step 2: Create service** — submit evaluation, get evaluation, list session evaluations, get summary. ESS endpoint for employee self-feedback.
- [ ] **Step 3: Create controller and routes** — 5 endpoints (4 admin + 1 ESS)
- [ ] **Step 4: Mount and commit**

---

### Task 3.5: Backend — Trainer Management + Certificate Lifecycle

**Files:**
- Create: `avy-erp-backend/src/modules/hr/advanced/trainer.validators.ts`
- Create: `avy-erp-backend/src/modules/hr/advanced/trainer.service.ts`
- Create: `avy-erp-backend/src/modules/hr/advanced/trainer.controller.ts`
- Create: `avy-erp-backend/src/modules/hr/advanced/trainer.routes.ts`
- Modify: `avy-erp-backend/src/modules/hr/advanced/advanced.service.ts` (certificate auto-set on completion)

- [ ] **Step 1: Create trainer CRUD** — validators, service, controller, routes (5 endpoints)
- [ ] **Step 2: Update completeTrainingNomination** to auto-set certificate fields when catalogue has `certificationName`: set `certificateIssuedAt = now()`, `certificateStatus = 'EARNED'`, calculate `certificateExpiryDate = issuedAt + certificationValidity years` (null if no validity), auto-generate `certificateNumber` via generateNextNumber
- [ ] **Step 3: Add expiring certificates endpoint** — `GET /hr/training-certificates/expiring?days=30` — query nominations where certificateExpiryDate is within N days of now and certificateStatus = EARNED
- [ ] **Step 4: Mount and commit**

---

### Task 3.6: Backend — Add Training Analytics Nav + Dashboard Enhancement

**Files:**
- Modify: `avy-erp-backend/src/shared/constants/navigation-manifest.ts`
- Modify: `avy-erp-backend/src/modules/hr/advanced/advanced.service.ts` (enhance getTrainingDashboard)

- [ ] **Step 1: Add nav manifest entry** for `hr-analytics-training` (Training Intelligence, sortOrder 459)
- [ ] **Step 2: Enhance getTrainingDashboard** to include: expiring certificates count, trainer stats, mandatory coverage breakdown
- [ ] **Step 3: Commit**

---

### Task 3.7: Web — Training Sessions, Attendance, Evaluations, Trainers UI

**Files:**
- Modify: `web-system-app/src/lib/api/recruitment.ts`
- Modify: `web-system-app/src/features/company-admin/api/use-recruitment-queries.ts`
- Modify: `web-system-app/src/features/company-admin/api/use-recruitment-mutations.ts`
- Modify: `web-system-app/src/features/company-admin/hr/TrainingCatalogueScreen.tsx` (add Sessions, Trainers tabs)
- Create: `web-system-app/src/features/company-admin/hr/analytics/TrainingDashboardScreen.tsx`
- Modify: `web-system-app/src/App.tsx` (add training dashboard route)

- [ ] **Step 1: Add all training API functions** — sessions, attendance, evaluations, trainers, certificates
- [ ] **Step 2: Add query and mutation hooks**
- [ ] **Step 3: Add "Sessions" and "Trainers" tabs** to TrainingCatalogueScreen
- [ ] **Step 4: Add attendance sheet modal** on session cards
- [ ] **Step 5: Add feedback form** on ESS MyTrainingScreen for completed nominations
- [ ] **Step 6: Create TrainingDashboardScreen** following RecruitmentDashboardScreen pattern
- [ ] **Step 7: Add routes and commit**

---

### Task 3.8: Mobile — Training Sessions, Attendance, Evaluations, Trainers UI

**Files:**
- Modify: `mobile-app/src/lib/api/recruitment.ts`
- Modify: `mobile-app/src/features/company-admin/api/use-recruitment-queries.ts`
- Modify: `mobile-app/src/features/company-admin/api/use-recruitment-mutations.ts`
- Modify: `mobile-app/src/features/company-admin/hr/training-screen.tsx` (add Sessions, Trainers tabs)
- Create: `mobile-app/src/features/company-admin/hr/analytics/training-dashboard-screen.tsx`
- Create: `mobile-app/src/app/(app)/company/hr/analytics/training.tsx` (route)
- Modify: `mobile-app/src/features/ess/my-training-screen.tsx` (add feedback button)

- [ ] **Step 1: Add all training API functions and hooks**
- [ ] **Step 2: Add Sessions and Trainers tabs** to training-screen
- [ ] **Step 3: Add attendance bottom sheet** for session management
- [ ] **Step 4: Add feedback form** to my-training-screen for COMPLETED nominations
- [ ] **Step 5: Create training-dashboard-screen** following recruitment dashboard pattern
- [ ] **Step 6: Add route file and commit**

---

### Phase 3 Review Checkpoint

- [ ] Training sessions CRUD with status transitions works
- [ ] Attendance registration and marking works (individual + bulk)
- [ ] Evaluations can be submitted by participants and trainers
- [ ] Trainer management (CRUD, assign to sessions) works
- [ ] Certificate fields auto-populate on training completion
- [ ] Expiring certificates endpoint works
- [ ] Training dashboard screen renders on web and mobile
- [ ] ESS feedback form works on My Training screen

---

## Phase 4 — Advanced Features

**Checkpoint:** After Phase 4, training programs/learning paths exist, budget tracking is functional, training materials are manageable, and analytics are enhanced.

---

### Task 4.1: Prisma Schema — Programs, Budgets, Materials

**Files:**
- Modify: `avy-erp-backend/prisma/modules/hrms/training.prisma`

- [ ] **Step 1: Add TrainingProgram, TrainingProgramCourse, TrainingProgramEnrollment, TrainingBudget, TrainingMaterial models** with all fields from spec. Add ProgramEnrollmentStatus enum. Add Training Program linked screen (PRG- prefix) in `src/shared/constants/linked-screens.ts`.
- [ ] **Step 2: Merge, generate, migrate, commit**

---

### Task 4.2: Backend — Training Programs Service + Routes

- [ ] **Step 1: Create program validators, service, controller, routes** — 9 endpoints for program CRUD, course management, enrollment
- [ ] **Step 2: Wire program progress** — when nomination COMPLETED, recalculate progressPercent on matching enrollment. If all courses done, auto-set COMPLETED.
- [ ] **Step 3: Prerequisite validation** — block nomination for next course if prerequisite not completed
- [ ] **Step 4: Commit**

---

### Task 4.3: Backend — Training Budgets Service + Routes

- [ ] **Step 1: Create budget validators, service, controller, routes** — 4 endpoints
- [ ] **Step 2: Wire budget usage** — on nomination COMPLETED, increment usedAmount on matching budget
- [ ] **Step 3: Commit**

---

### Task 4.4: Backend — Training Materials Service + Routes

- [ ] **Step 1: Create material validators, service, controller, routes** — 4 endpoints nested under catalogue
- [ ] **Step 2: Commit**

---

### Task 4.5: Backend — Enhanced Analytics

- [ ] **Step 1: Enhance getRecruitmentDashboard** — add source effectiveness, funnel conversion, offer acceptance rate, time per stage, requisition aging
- [ ] **Step 2: Enhance getTrainingDashboard** — add effectiveness scores, trainer leaderboard, budget utilization, certificate timeline, program completion rates, skill gap coverage
- [ ] **Step 3: Commit**

---

### Task 4.6: Web — Programs, Budgets, Materials UI

- [ ] **Step 1: Add API functions and hooks for programs, budgets, materials**
- [ ] **Step 2: Add "Programs" tab** to TrainingCatalogueScreen — program list, course management, enrollment
- [ ] **Step 3: Add budget management section** in training admin
- [ ] **Step 4: Add materials section** in catalogue detail
- [ ] **Step 5: Update dashboard** with new analytics widgets
- [ ] **Step 6: Commit**

---

### Task 4.7: Mobile — Programs, Budgets, Materials UI

- [ ] **Step 1: Add API functions and hooks**
- [ ] **Step 2: Add Programs tab** to training-screen
- [ ] **Step 3: Add materials view** in ESS my-training
- [ ] **Step 4: Update training dashboard** with new widgets
- [ ] **Step 5: Commit**

---

### Phase 4 Review Checkpoint

- [ ] Training programs with prerequisite enforcement work
- [ ] Budget allocation and auto-tracking work
- [ ] Training materials CRUD and ESS viewing work
- [ ] Enhanced analytics show all new metrics
- [ ] All state transitions enforced by state machine

---

## Cross-Cutting Phase — Notifications, Audit, Events, Permissions

This phase can be built in parallel with Phase 2-4 or after them.

---

### Task CC.1: Prisma Schema — Notification, UserDevice, AuditLog, AnalyticsSnapshot

**Files:**
- Create: `avy-erp-backend/prisma/modules/platform/notifications.prisma`
- Create: `avy-erp-backend/prisma/modules/platform/audit.prisma`
- Create: `avy-erp-backend/prisma/modules/platform/analytics.prisma`

- [ ] **Step 1: Create notifications.prisma** with Notification and UserDevice models
- [ ] **Step 2: Create audit.prisma** with AuditLog model (changes JSON, retentionDate)
- [ ] **Step 3: Create analytics.prisma** with AnalyticsSnapshot model
- [ ] **Step 4: Merge, generate, migrate, commit**

---

### Task CC.2: Notification Service (FCM + In-App)

**Files:**
- Create: `avy-erp-backend/src/core/notifications/notification.service.ts`
- Create: `avy-erp-backend/src/core/notifications/notification.controller.ts`
- Create: `avy-erp-backend/src/core/notifications/notification.routes.ts`

- [ ] **Step 1: Create NotificationService** — `send()` method that creates in-app notification + sends FCM push via `firebase-admin`
- [ ] **Step 2: Create endpoints** — register-device, unregister, list notifications, mark read, read-all, unread-count
- [ ] **Step 3: Mount routes** (authenticated, no specific permission — all users can manage their notifications)
- [ ] **Step 4: Commit**

---

### Task CC.3: Audit Trail Utility

**Files:**
- Create: `avy-erp-backend/src/shared/utils/audit.ts`

- [ ] **Step 1: Create computeDiff utility** — shallow diff between before/after objects, returns `{field: {from, to}}`
- [ ] **Step 2: Create auditLog function** — creates AuditLog record with diff, auto-calculates retentionDate (default 12 months)
- [ ] **Step 3: Add GET /hr/audit-log endpoint** — query by entityType, entityId, dateRange
- [ ] **Step 4: Wire auditLog calls** into all status change service methods (offers, nominations, sessions, requisitions)
- [ ] **Step 5: Commit**

---

### Task CC.4: Event System

**Files:**
- Create: `avy-erp-backend/src/shared/events/hr-events.ts`
- Create: `avy-erp-backend/src/shared/events/event-bus.ts`
- Create: `avy-erp-backend/src/shared/events/listeners/hr-listeners.ts`

- [ ] **Step 1: Create typed event bus** — EventEmitter wrapper with typed HREvent union
- [ ] **Step 2: Create HR event listeners** — handle candidate.hired (notification), offer.accepted (advance stage + notify), training.completed (update skills + check program + notify), etc.
- [ ] **Step 3: Register listeners** at app startup
- [ ] **Step 4: Wire emitEvent calls** into service methods
- [ ] **Step 5: Commit**

---

### Task CC.5: Permission Granularity

**Files:**
- Modify: `avy-erp-backend/src/shared/constants/permissions.ts`
- Modify: `avy-erp-backend/src/modules/hr/advanced/advanced.routes.ts` (update guards)
- Modify all new route files (offer, candidate-profile, evaluation, training-session, etc.)

- [ ] **Step 1: Add new permission modules** to PERMISSION_MODULES: recruitment, recruitment-offer, training, training-evaluation
- [ ] **Step 2: Add to MODULE_TO_PERMISSION_MAP** — both tied to 'hr' subscription
- [ ] **Step 3: Update route guards** — replace `hr:read` with `recruitment:read` for recruitment routes, `training:read` for training routes, etc.
- [ ] **Step 4: Update reference roles** in permissions.ts
- [ ] **Step 5: Commit**

---

### Task CC.6: Mobile FCM Setup

**Files:**
- Modify: `mobile-app/app.json` or `app.config.ts` (FCM credentials)
- Create: `mobile-app/src/lib/notifications/setup.ts`

- [ ] **Step 1: Configure expo-notifications** with FCM
- [ ] **Step 2: Register FCM token** on app launch — call `POST /notifications/register-device`
- [ ] **Step 3: Handle notification tap** — deep-link to relevant screen based on entityType
- [ ] **Step 4: Unregister on logout** — call `DELETE /notifications/register-device`
- [ ] **Step 5: Commit**

---

### Task CC.7: Web FCM Setup

**Files:**
- Create: `web-system-app/public/firebase-messaging-sw.js` (service worker)
- Create: `web-system-app/src/lib/notifications/setup.ts`

- [ ] **Step 1: Add Firebase messaging service worker**
- [ ] **Step 2: Register FCM token** on login — call `POST /notifications/register-device`
- [ ] **Step 3: Handle foreground notifications** — show toast
- [ ] **Step 4: Unregister on logout**
- [ ] **Step 5: Commit**

---

### Task CC.8: Notification Bell UI (Web + Mobile)

**Files:**
- Create: `web-system-app/src/features/notifications/NotificationBell.tsx`
- Create: `mobile-app/src/features/notifications/notification-bell.tsx`

- [ ] **Step 1: Create web NotificationBell** — bell icon with unread count badge, dropdown list of recent notifications, mark-read on click, "View all" link
- [ ] **Step 2: Add to web DashboardLayout** header
- [ ] **Step 3: Create mobile notification-bell** — same pattern, bottom sheet for notification list
- [ ] **Step 4: Add to mobile AppTopHeader**
- [ ] **Step 5: Commit**

---

### Cross-Cutting Review Checkpoint

- [ ] FCM push notifications reach both web and mobile devices
- [ ] In-app notifications display in bell dropdown/sheet
- [ ] Audit log records all status changes with diffs
- [ ] Event system triggers notifications and side effects
- [ ] Granular permissions control access to recruitment vs training features
- [ ] Old `hr:*` permissions still work via module inheritance

---

## Final Review

After all phases + cross-cutting:
- [ ] All 15 new Prisma models exist and are migrated
- [ ] All ~66 new endpoints are functional
- [ ] All state machines enforce valid transitions
- [ ] FCM notifications work on web and mobile
- [ ] Audit trail captures all critical changes
- [ ] Granular permissions are enforced
- [ ] Training and recruitment dashboard screens render correctly
- [ ] Run full build across all 3 codebases with zero errors
