# OT Employee Features & Gap Closure — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Close all remaining OT gaps: employee-facing ESS screens (My Overtime + manual claims), new permissions, notifications, payroll cap fix, and comp-off deep link — across backend, web, and mobile.

**Architecture:** ESS-first approach — OT becomes a first-class ESS feature following existing patterns exactly. A new `OvertimeRequestSource` enum + 3 new fields on `OvertimeRequest` model. 4 new ESS endpoints. Mobile + web get identical "My Overtime" screens. Manual claims reuse the same approval pipeline as auto-generated OT.

**Tech Stack:** Node.js/Express, Prisma, Zod, React Query, React Native (Expo), React (Vite), Tailwind, NativeWind, @gorhom/bottom-sheet, lucide-react.

**Spec:** `docs/superpowers/specs/2026-04-16-ot-employee-features-gap-closure-design.md`

---

## File Structure

### Backend — New Files
| File | Responsibility |
|------|---------------|
| `avy-erp-backend/src/modules/hr/ess/ess-overtime.validators.ts` | Zod schemas for all 4 OT ESS endpoints |
| `avy-erp-backend/src/modules/hr/ess/ess-overtime.service.ts` | Service class: getMyOvertimeRequests, getMyOvertimeDetail, getMyOvertimeSummary, claimOvertime |

### Backend — Modified Files
| File | Change |
|------|--------|
| `avy-erp-backend/prisma/modules/hrms/attendance.prisma` | Add `OvertimeRequestSource` enum + `source`, `reason`, `attachments` fields + make `attendanceRecordId` optional |
| `avy-erp-backend/prisma/modules/hrms/ess-workflows.prisma` | Add `overtimeView` Boolean to ESSConfig |
| `avy-erp-backend/src/shared/constants/permissions.ts` | Add `view-overtime`, `claim-overtime` to ESS actions |
| `avy-erp-backend/src/shared/constants/navigation-manifest.ts` | Add `ess-overtime` entry |
| `avy-erp-backend/src/shared/constants/trigger-events.ts` | Add `OVERTIME_AUTO_DETECTED` event |
| `avy-erp-backend/src/core/notifications/templates/defaults.ts` | Add 2 new templates |
| `avy-erp-backend/src/shared/constants/notification-categories.ts` | Add new events to OVERTIME category mapping |
| `avy-erp-backend/src/core/rbac/rbac.service.ts` | Add `ess-overtime` to `NAV_TO_ESS_CONFIG` |
| `avy-erp-backend/src/modules/hr/ess/ess.controller.ts` | Add 4 new controller methods |
| `avy-erp-backend/src/modules/hr/ess/ess.routes.ts` | Add 4 new routes |
| `avy-erp-backend/src/modules/hr/attendance/attendance.service.ts` | Add `OVERTIME_AUTO_DETECTED` + `COMP_OFF_GRANTED` notification dispatches |
| `avy-erp-backend/src/modules/hr/payroll-run/payroll-run.service.ts` | Add daily/weekly cap re-validation |

### Mobile — New Files
| File | Responsibility |
|------|---------------|
| `mobile-app/src/features/ess/overtime/my-overtime-screen.tsx` | Main screen: summary cards + filterable list |
| `mobile-app/src/features/ess/overtime/claim-overtime-modal.tsx` | Bottom sheet form for manual OT claims |
| `mobile-app/src/features/ess/overtime/overtime-request-detail-sheet.tsx` | Bottom sheet for viewing request details |
| `mobile-app/src/features/ess/overtime/use-overtime-queries.ts` | React Query hooks + key factory |
| `mobile-app/src/app/(app)/company/hr/my-overtime.tsx` | Route file |

### Mobile — Modified Files
| File | Change |
|------|--------|
| `mobile-app/src/lib/api/ess.ts` | Add OT types + API functions |

### Web — New Files
| File | Responsibility |
|------|---------------|
| `web-system-app/src/features/ess/MyOvertimeScreen.tsx` | Main screen: summary cards + table + filters |
| `web-system-app/src/features/ess/ClaimOvertimeDialog.tsx` | Modal dialog for manual OT claims |
| `web-system-app/src/features/ess/OvertimeRequestDetail.tsx` | Slide-over detail panel |
| `web-system-app/src/features/ess/use-overtime-queries.ts` | React Query hooks + key factory (mirrors mobile) |

### Web — Modified Files
| File | Change |
|------|--------|
| `web-system-app/src/App.tsx` | Add lazy import + route |
| `web-system-app/src/lib/api/ess.ts` (or attendance.ts) | Add OT types + API functions |

---

## Shared Types Reference

These types are used across all tasks. Both mobile and web API layers MUST use these exact type names and shapes:

```typescript
// Enums
type OvertimeRequestStatus = 'PENDING' | 'APPROVED' | 'REJECTED' | 'PAID' | 'COMP_OFF_ACCRUED';
type OTMultiplierSource = 'WEEKDAY' | 'WEEKEND' | 'HOLIDAY' | 'NIGHT_SHIFT';
type OvertimeRequestSource = 'AUTO' | 'MANUAL';

// List item (used in GET /ess/my-overtime-requests)
interface OvertimeRequestListItem {
  id: string;
  date: string;
  source: OvertimeRequestSource;
  requestedHours: number;
  appliedMultiplier: number;
  multiplierSource: OTMultiplierSource;
  calculatedAmount: number | null;
  status: OvertimeRequestStatus;
  reason: string | null;
  attachments: string[] | null;
  compOffGranted: boolean;
  approvalNotes: string | null;
  approvedAt: string | null;
  createdAt: string;
}

// Detail item (used in GET /ess/my-overtime-requests/:id)
interface OvertimeRequestDetail extends OvertimeRequestListItem {
  attendanceRecord: {
    date: string;
    punchIn: string | null;
    punchOut: string | null;
    workedHours: number | null;
    status: string;
    shiftName: string | null;
  } | null;
  approvedByName: string | null;
  requestedByName: string | null;
}

// Summary (used in GET /ess/my-overtime-summary)
interface OvertimeSummary {
  totalOtHours: number;
  pendingCount: number;
  approvedAmount: number;
  totalRequests: number;
  compOff: {
    balance: number;
    expiresAt: string | null;
    leaveTypeId: string | null;
  } | null;
}

// Claim payload (used in POST /ess/claim-overtime)
interface ClaimOvertimePayload {
  date: string;       // YYYY-MM-DD
  hours: number;      // 0.5–24, step 0.5
  reason: string;     // 10–500 chars
  attachments?: string[]; // R2 URLs, max 5
}
```

---

## Task 1: Schema Changes (Prisma)

**Files:**
- Modify: `avy-erp-backend/prisma/modules/hrms/attendance.prisma:237-269`
- Modify: `avy-erp-backend/prisma/modules/hrms/ess-workflows.prisma:7-72`

- [ ] **Step 1: Add `OvertimeRequestSource` enum and update `OvertimeRequest` model**

In `avy-erp-backend/prisma/modules/hrms/attendance.prisma`, add the new enum after the existing `OTMultiplierSource` enum (around line 285):

```prisma
enum OvertimeRequestSource {
  AUTO
  MANUAL
}
```

Then update the `OvertimeRequest` model (lines 237-269). Change `attendanceRecordId` from required to optional, and add the 3 new fields:

```prisma
model OvertimeRequest {
  id                 String  @id @default(cuid())
  attendanceRecordId String? @unique              // ← Changed: was required, now optional for MANUAL claims
  companyId          String
  employeeId         String
  overtimeRuleId     String

  date              DateTime              @db.Date
  requestedHours    Decimal               @db.Decimal(5, 2)
  appliedMultiplier Decimal               @db.Decimal(3, 2)
  multiplierSource  OTMultiplierSource
  calculatedAmount  Decimal?              @db.Decimal(15, 2)

  status        OvertimeRequestStatus @default(PENDING)
  requestedBy   String
  approvedBy    String?
  approvalNotes String?
  approvedAt    DateTime?

  compOffGranted Boolean @default(false)

  // ── New fields for manual claims ──
  source      OvertimeRequestSource @default(AUTO)
  reason      String?               // Mandatory for MANUAL, null for AUTO
  attachments Json?                 // Array of R2 file URLs, max 5

  attendanceRecord AttendanceRecord? @relation(fields: [attendanceRecordId], references: [id], onDelete: Cascade) // ← Changed: optional relation
  company          Company           @relation(fields: [companyId], references: [id], onDelete: Cascade)
  employee         Employee          @relation(fields: [employeeId], references: [id])
  overtimeRule     OvertimeRule      @relation(fields: [overtimeRuleId], references: [id])

  createdAt DateTime @default(now())
  updatedAt DateTime @updatedAt

  @@index([companyId, status])
  @@index([employeeId, date])
  @@map("overtime_requests")
}
```

- [ ] **Step 2: Add `overtimeView` to ESSConfig model**

In `avy-erp-backend/prisma/modules/hrms/ess-workflows.prisma`, add after the `wfhRequest` field (line 28):

```prisma
  // ── Overtime ──
  overtimeView Boolean @default(true)
```

- [ ] **Step 3: Run prisma merge and generate**

```bash
cd avy-erp-backend && pnpm prisma:merge && pnpm db:generate
```

Expected: No errors. `schema.prisma` regenerated with new enum + fields.

- [ ] **Step 4: Create and apply migration**

```bash
cd avy-erp-backend && pnpm db:migrate --name add_overtime_ess_fields
```

Expected: Migration created and applied. Adds `source`, `reason`, `attachments` columns, modifies `attendanceRecordId` to nullable, adds `overtimeView` to ess_configs.

- [ ] **Step 5: Commit**

```bash
cd /Users/chetan/Documents/Avyren-Technologies/Products/Mobile-ERP/avy-erp-backend
git add prisma/
git commit -m "feat(schema): add OvertimeRequestSource enum, manual claim fields, ESSConfig.overtimeView"
```

---

## Task 2: Permissions, Navigation & Constants

**Files:**
- Modify: `avy-erp-backend/src/shared/constants/permissions.ts:187-190`
- Modify: `avy-erp-backend/src/shared/constants/navigation-manifest.ts:50-62`
- Modify: `avy-erp-backend/src/shared/constants/trigger-events.ts:49-53`
- Modify: `avy-erp-backend/src/core/notifications/templates/defaults.ts:87-98`
- Modify: `avy-erp-backend/src/shared/constants/notification-categories.ts`
- Modify: `avy-erp-backend/src/core/rbac/rbac.service.ts:16-41`

- [ ] **Step 1: Add ESS permissions**

In `avy-erp-backend/src/shared/constants/permissions.ts`, find the `ess` module actions array (line ~188) and add `'view-overtime'` and `'claim-overtime'` to the end of the array:

```typescript
ess: {
    label: 'Employee Self-Service',
    actions: ['view-payslips', 'view-leave', 'apply-leave', 'view-attendance', 'regularize-attendance', 'view-holidays', 'it-declaration', 'view-directory', 'view-profile', 'download-form16', 'apply-loan', 'view-assets', 'view-goals', 'submit-appraisal', 'submit-feedback', 'enroll-training', 'raise-grievance', 'raise-helpdesk', 'swap-shift', 'request-wfh', 'upload-document', 'view-policies', 'claim-expense', 'view-org-chart', 'use-chatbot', 'view-esign', 'view-disciplinary', 'view-overtime', 'claim-overtime'],
},
```

Also add `'ess:view-overtime'` and `'ess:claim-overtime'` to the Employee, Manager, HR Personnel, Department Head, and Team Lead reference roles in the same file.

- [ ] **Step 2: Add navigation manifest entry**

In `avy-erp-backend/src/shared/constants/navigation-manifest.ts`, find the ESS entries around sortOrder 310-312. Insert the new entry after `ess-training` (sortOrder 310) and before `ess-assets`:

```typescript
  { id: 'ess-overtime', label: 'My Overtime', icon: 'clock', requiredPerm: 'ess:view-overtime', path: '/app/company/hr/my-overtime', module: 'hr', group: 'My Workspace', roleScope: 'company', sortOrder: 311 },
```

Bump `ess-assets` sortOrder to 312, `ess-shift-swap` to 313, etc. (increment all subsequent ESS items by 1).

- [ ] **Step 3: Add trigger event**

In `avy-erp-backend/src/shared/constants/trigger-events.ts`, add after the existing `OVERTIME_CLAIM` entry:

```typescript
  {
    value: 'OVERTIME_AUTO_DETECTED',
    label: 'Overtime Auto-Detected',
    module: 'ESS',
    description: 'Triggered when the system auto-detects overtime for an employee',
  },
  {
    value: 'COMP_OFF_GRANTED',
    label: 'Compensatory Off Granted',
    module: 'ESS',
    description: 'Triggered when compensatory off leave is credited after OT approval',
  },
```

- [ ] **Step 4: Add notification templates**

In `avy-erp-backend/src/core/notifications/templates/defaults.ts`, add after the existing OVERTIME_CLAIM template (around line 98):

```typescript
  {
    code: 'OVERTIME_AUTO_DETECTED',
    name: 'Overtime Auto-Detected',
    subject: 'Overtime Detected — {{date}}',
    body: 'The system detected {{hours}} hours of overtime on {{date}}. A request has been created for approval.',
    channels: ['PUSH', 'IN_APP'],
    priority: 'LOW',
    variables: ['employee_name', 'date', 'hours', 'multiplier_source'],
    sensitiveFields: [],
    category: 'OVERTIME',
    triggerEvent: 'OVERTIME_AUTO_DETECTED',
    recipientRole: 'SELF',
  },
  {
    code: 'COMP_OFF_GRANTED',
    name: 'Compensatory Off Credited',
    subject: 'Compensatory Off Credited',
    body: '{{days}} day(s) of compensatory off have been credited for your overtime on {{date}}. Your current balance is {{balance}} day(s).',
    channels: ['PUSH', 'IN_APP', 'EMAIL'],
    priority: 'MEDIUM',
    variables: ['employee_name', 'days', 'date', 'expires_at', 'balance'],
    sensitiveFields: [],
    category: 'OVERTIME',
    triggerEvent: 'COMP_OFF_GRANTED',
    recipientRole: 'SELF',
  },
```

- [ ] **Step 5: Add notification category mappings**

In `avy-erp-backend/src/shared/constants/notification-categories.ts`, find the trigger-to-category mapping section (around lines 107-109) and add:

```typescript
  OVERTIME_AUTO_DETECTED: 'OVERTIME',
  COMP_OFF_GRANTED: 'OVERTIME',
```

- [ ] **Step 6: Add ESS config mapping in RBAC service**

In `avy-erp-backend/src/core/rbac/rbac.service.ts`, find `NAV_TO_ESS_CONFIG` (around line 16-41) and add:

```typescript
  'ess-overtime': 'overtimeView',
```

- [ ] **Step 7: Commit**

```bash
cd /Users/chetan/Documents/Avyren-Technologies/Products/Mobile-ERP/avy-erp-backend
git add src/shared/constants/ src/core/notifications/ src/core/rbac/
git commit -m "feat(constants): add OT ESS permissions, nav manifest, trigger events, notification templates"
```

---

## Task 3: Backend Validators

**Files:**
- Create: `avy-erp-backend/src/modules/hr/ess/ess-overtime.validators.ts`

- [ ] **Step 1: Create validators file**

Create `avy-erp-backend/src/modules/hr/ess/ess-overtime.validators.ts`:

```typescript
import { z } from 'zod';

export const claimOvertimeSchema = z.object({
  date: z
    .string()
    .regex(/^\d{4}-\d{2}-\d{2}$/, 'Date must be in YYYY-MM-DD format')
    .refine(
      (d) => {
        const date = new Date(d + 'T00:00:00Z');
        const now = new Date();
        now.setUTCHours(0, 0, 0, 0);
        return date < now;
      },
      'Date must be in the past',
    )
    .refine(
      (d) => {
        const date = new Date(d + 'T00:00:00Z');
        const thirtyDaysAgo = new Date();
        thirtyDaysAgo.setUTCDate(thirtyDaysAgo.getUTCDate() - 30);
        thirtyDaysAgo.setUTCHours(0, 0, 0, 0);
        return date >= thirtyDaysAgo;
      },
      'Date must be within the last 30 days',
    ),
  hours: z
    .number()
    .min(0.5, 'Minimum 0.5 hours')
    .max(24, 'Maximum 24 hours')
    .multipleOf(0.5, 'Hours must be in increments of 0.5'),
  reason: z
    .string()
    .min(10, 'Reason must be at least 10 characters')
    .max(500, 'Reason must be at most 500 characters'),
  attachments: z
    .array(z.string().url('Each attachment must be a valid URL'))
    .max(5, 'Maximum 5 attachments')
    .optional(),
});

export const myOvertimeListSchema = z.object({
  status: z
    .enum(['PENDING', 'APPROVED', 'REJECTED', 'PAID', 'COMP_OFF_ACCRUED'])
    .optional(),
  source: z.enum(['AUTO', 'MANUAL']).optional(),
  dateFrom: z
    .string()
    .regex(/^\d{4}-\d{2}-\d{2}$/, 'dateFrom must be YYYY-MM-DD')
    .optional(),
  dateTo: z
    .string()
    .regex(/^\d{4}-\d{2}-\d{2}$/, 'dateTo must be YYYY-MM-DD')
    .optional(),
  page: z.coerce.number().int().min(1).default(1),
  limit: z.coerce.number().int().min(1).max(100).default(20),
});

export const myOvertimeSummarySchema = z.object({
  month: z.coerce.number().int().min(1).max(12).optional(),
  year: z.coerce.number().int().min(2020).max(2100).optional(),
});

export type ClaimOvertimeInput = z.infer<typeof claimOvertimeSchema>;
export type MyOvertimeListInput = z.infer<typeof myOvertimeListSchema>;
export type MyOvertimeSummaryInput = z.infer<typeof myOvertimeSummarySchema>;
```

- [ ] **Step 2: Commit**

```bash
cd /Users/chetan/Documents/Avyren-Technologies/Products/Mobile-ERP/avy-erp-backend
git add src/modules/hr/ess/ess-overtime.validators.ts
git commit -m "feat(validators): add Zod schemas for OT ESS endpoints"
```

---

## Task 4: Backend Service — ESS Overtime

**Files:**
- Create: `avy-erp-backend/src/modules/hr/ess/ess-overtime.service.ts`

This is the core business logic. The service handles 4 methods matching the 4 endpoints.

- [ ] **Step 1: Create the service file**

Create `avy-erp-backend/src/modules/hr/ess/ess-overtime.service.ts`:

```typescript
import { OvertimeRequestStatus, Prisma } from '@prisma/client';

import { platformPrisma } from '../../../config/database';
import { logger } from '../../../config/logger';
import { ApiError } from '../../../shared/errors/api-error';
import { createPaginationMeta } from '../../../shared/utils/pagination';
import { notificationService } from '../../../core/notifications/notification.service';
import type { ClaimOvertimeInput, MyOvertimeListInput, MyOvertimeSummaryInput } from './ess-overtime.validators';

class EssOvertimeService {
  /**
   * GET /ess/my-overtime-requests
   * List the authenticated employee's own OT requests with pagination and filters.
   */
  async getMyOvertimeRequests(companyId: string, employeeId: string, params: MyOvertimeListInput) {
    const { status, source, dateFrom, dateTo, page, limit } = params;

    const where: Prisma.OvertimeRequestWhereInput = {
      companyId,
      employeeId,
      ...(status && { status }),
      ...(source && { source }),
      ...(dateFrom && { date: { gte: new Date(dateFrom + 'T00:00:00Z') } }),
      ...(dateTo && {
        date: {
          ...(dateFrom && { gte: new Date(dateFrom + 'T00:00:00Z') }),
          lte: new Date(dateTo + 'T23:59:59Z'),
        },
      }),
    };

    const [requests, total] = await Promise.all([
      platformPrisma.overtimeRequest.findMany({
        where,
        select: {
          id: true,
          date: true,
          source: true,
          requestedHours: true,
          appliedMultiplier: true,
          multiplierSource: true,
          calculatedAmount: true,
          status: true,
          reason: true,
          attachments: true,
          compOffGranted: true,
          approvalNotes: true,
          approvedAt: true,
          createdAt: true,
        },
        orderBy: [{ date: 'desc' }, { createdAt: 'desc' }],
        skip: (page - 1) * limit,
        take: limit,
      }),
      platformPrisma.overtimeRequest.count({ where }),
    ]);

    const data = requests.map((r) => ({
      ...r,
      date: r.date.toISOString().split('T')[0],
      requestedHours: Number(r.requestedHours),
      appliedMultiplier: Number(r.appliedMultiplier),
      calculatedAmount: r.calculatedAmount ? Number(r.calculatedAmount) : null,
      attachments: r.attachments as string[] | null,
      approvedAt: r.approvedAt?.toISOString() ?? null,
      createdAt: r.createdAt.toISOString(),
    }));

    return { data, meta: createPaginationMeta(total, page, limit) };
  }

  /**
   * GET /ess/my-overtime-requests/:id
   * Single OT request detail with linked attendance record info.
   */
  async getMyOvertimeDetail(companyId: string, employeeId: string, requestId: string) {
    const request = await platformPrisma.overtimeRequest.findFirst({
      where: { id: requestId, companyId, employeeId },
      include: {
        attendanceRecord: {
          select: {
            date: true,
            punchIn: true,
            punchOut: true,
            workedHours: true,
            status: true,
            shift: { select: { shiftName: true } },
          },
        },
      },
    });

    if (!request) {
      throw ApiError.notFound('Overtime request not found');
    }

    // Resolve approver and requester names
    const [approver, requester] = await Promise.all([
      request.approvedBy
        ? platformPrisma.user.findUnique({
            where: { id: request.approvedBy },
            select: { firstName: true, lastName: true },
          })
        : null,
      platformPrisma.user.findUnique({
        where: { id: request.requestedBy },
        select: { firstName: true, lastName: true },
      }),
    ]);

    return {
      id: request.id,
      date: request.date.toISOString().split('T')[0],
      source: request.source,
      requestedHours: Number(request.requestedHours),
      appliedMultiplier: Number(request.appliedMultiplier),
      multiplierSource: request.multiplierSource,
      calculatedAmount: request.calculatedAmount ? Number(request.calculatedAmount) : null,
      status: request.status,
      reason: request.reason,
      attachments: request.attachments as string[] | null,
      compOffGranted: request.compOffGranted,
      approvalNotes: request.approvalNotes,
      approvedAt: request.approvedAt?.toISOString() ?? null,
      createdAt: request.createdAt.toISOString(),
      attendanceRecord: request.attendanceRecord
        ? {
            date: request.attendanceRecord.date.toISOString().split('T')[0],
            punchIn: request.attendanceRecord.punchIn?.toISOString() ?? null,
            punchOut: request.attendanceRecord.punchOut?.toISOString() ?? null,
            workedHours: request.attendanceRecord.workedHours
              ? Number(request.attendanceRecord.workedHours)
              : null,
            status: request.attendanceRecord.status,
            shiftName: request.attendanceRecord.shift?.shiftName ?? null,
          }
        : null,
      approvedByName: approver ? `${approver.firstName} ${approver.lastName}`.trim() : null,
      requestedByName: requester ? `${requester.firstName} ${requester.lastName}`.trim() : null,
    };
  }

  /**
   * GET /ess/my-overtime-summary
   * Summary statistics for the "My Overtime" screen header cards.
   */
  async getMyOvertimeSummary(companyId: string, employeeId: string, params: MyOvertimeSummaryInput) {
    const now = new Date();
    const month = params.month ?? now.getMonth() + 1;
    const year = params.year ?? now.getFullYear();

    const monthStart = new Date(Date.UTC(year, month - 1, 1));
    const monthEnd = new Date(Date.UTC(year, month, 1));

    // Aggregate OT stats for the month
    const [approved, pending, allCount] = await Promise.all([
      platformPrisma.overtimeRequest.aggregate({
        where: {
          companyId,
          employeeId,
          status: { in: ['APPROVED', 'PAID'] },
          date: { gte: monthStart, lt: monthEnd },
        },
        _sum: { requestedHours: true, calculatedAmount: true },
      }),
      platformPrisma.overtimeRequest.count({
        where: {
          companyId,
          employeeId,
          status: 'PENDING',
          date: { gte: monthStart, lt: monthEnd },
        },
      }),
      platformPrisma.overtimeRequest.count({
        where: {
          companyId,
          employeeId,
          date: { gte: monthStart, lt: monthEnd },
        },
      }),
    ]);

    // Comp-off balance
    let compOff: { balance: number; expiresAt: string | null; leaveTypeId: string | null } | null = null;

    const otRule = await platformPrisma.overtimeRule.findUnique({
      where: { companyId },
      select: { compOffEnabled: true },
    });

    if (otRule?.compOffEnabled) {
      const compLeaveType = await platformPrisma.leaveType.findFirst({
        where: { companyId, category: 'COMPENSATORY' },
        select: { id: true },
      });

      if (compLeaveType) {
        const balance = await platformPrisma.leaveBalance.findFirst({
          where: {
            companyId,
            employeeId,
            leaveTypeId: compLeaveType.id,
            year,
          },
          select: { balance: true, expiresAt: true },
        });

        compOff = {
          balance: balance ? Number(balance.balance) : 0,
          expiresAt: balance?.expiresAt?.toISOString() ?? null,
          leaveTypeId: compLeaveType.id,
        };
      } else {
        compOff = { balance: 0, expiresAt: null, leaveTypeId: null };
      }
    }

    return {
      totalOtHours: approved._sum.requestedHours ? Number(approved._sum.requestedHours) : 0,
      pendingCount: pending,
      approvedAmount: approved._sum.calculatedAmount ? Number(approved._sum.calculatedAmount) : 0,
      totalRequests: allCount,
      compOff,
    };
  }

  /**
   * POST /ess/claim-overtime
   * Employee submits a manual OT claim. Reuses existing OT rule validation and cap logic.
   */
  async claimOvertime(companyId: string, userId: string, employeeId: string, data: ClaimOvertimeInput) {
    // 1. Validate employee is active
    const employee = await platformPrisma.employee.findFirst({
      where: { id: employeeId, companyId, status: 'ACTIVE' },
      select: { id: true, employeeTypeId: true, shiftId: true },
    });
    if (!employee) {
      throw ApiError.forbidden('Your account is not active');
    }

    // 2. Get OT rules
    const otRule = await platformPrisma.overtimeRule.findUnique({ where: { companyId } });
    if (!otRule) {
      throw ApiError.badRequest('Overtime rules are not configured for your company');
    }

    // 3. Check eligibility
    if (otRule.eligibleTypeIds) {
      const eligibleIds = otRule.eligibleTypeIds as string[];
      if (Array.isArray(eligibleIds) && eligibleIds.length > 0) {
        if (!employee.employeeTypeId || !eligibleIds.includes(employee.employeeTypeId)) {
          throw ApiError.forbidden('You are not eligible for overtime claims');
        }
      }
    }

    // 4. Duplicate check
    const claimDate = new Date(data.date + 'T00:00:00Z');
    const existing = await platformPrisma.overtimeRequest.findFirst({
      where: { companyId, employeeId, date: claimDate },
    });
    if (existing) {
      throw ApiError.conflict('An overtime request already exists for this date');
    }

    // 5. Validate hours against OT rules
    let effectiveHours = data.hours;

    // Apply thresholdMinutes dead-zone (AFTER_SHIFT basis only)
    if (otRule.calculationBasis === 'AFTER_SHIFT' && otRule.thresholdMinutes > 0) {
      const thresholdHours = otRule.thresholdMinutes / 60;
      if (effectiveHours <= thresholdHours) {
        throw ApiError.badRequest(
          `Overtime must exceed the ${otRule.thresholdMinutes}-minute threshold`,
        );
      }
      effectiveHours -= thresholdHours;
    }

    // Apply minimumOtMinutes floor
    if (effectiveHours * 60 < otRule.minimumOtMinutes) {
      throw ApiError.badRequest(
        `Minimum overtime is ${otRule.minimumOtMinutes} minutes`,
      );
    }

    // 6. Apply rounding
    if (otRule.roundingStrategy && otRule.roundingStrategy !== 'NONE') {
      effectiveHours = this.applyOtRounding(effectiveHours, otRule.roundingStrategy);
    }

    // 7. Enforce caps
    if (otRule.enforceCaps) {
      effectiveHours = await this.enforceOtCaps(
        companyId,
        employeeId,
        claimDate,
        effectiveHours,
        otRule,
      );
      if (effectiveHours <= 0) {
        throw ApiError.badRequest('Overtime cap exceeded for this period');
      }
    }

    // 8. Determine multiplier source
    const { multiplierSource, appliedMultiplier } = await this.determineMultiplierSource(
      companyId,
      employeeId,
      claimDate,
      employee.shiftId,
      otRule,
    );

    // 9. Create OvertimeRequest
    const status: OvertimeRequestStatus = otRule.approvalRequired ? 'PENDING' : 'APPROVED';
    const otRequest = await platformPrisma.overtimeRequest.create({
      data: {
        companyId,
        employeeId,
        overtimeRuleId: otRule.id,
        date: claimDate,
        requestedHours: effectiveHours,
        appliedMultiplier,
        multiplierSource,
        source: 'MANUAL',
        reason: data.reason,
        attachments: data.attachments ?? Prisma.JsonNull,
        status,
        requestedBy: userId,
        ...(status === 'APPROVED' && {
          approvedBy: 'SYSTEM',
          approvedAt: new Date(),
          approvalNotes: 'Auto-approved (approvalRequired=false)',
        }),
      },
    });

    // 10. Notifications
    // Notify approvers
    const employeeUser = await platformPrisma.user.findFirst({
      where: { employeeId },
      select: { firstName: true, lastName: true },
    });
    const employeeName = employeeUser
      ? `${employeeUser.firstName} ${employeeUser.lastName}`.trim()
      : 'Employee';

    await notificationService.dispatch({
      companyId,
      triggerEvent: 'OVERTIME_CLAIM',
      entityType: 'OvertimeRequest',
      entityId: otRequest.id,
      tokens: {
        employee_name: employeeName,
        date: data.date,
        hours: effectiveHours,
      },
      priority: 'MEDIUM',
      type: 'OVERTIME',
      actionUrl: '/company/hr/approval-requests',
    }).catch((err) => logger.warn('Failed to dispatch OVERTIME_CLAIM notification', err));

    // If auto-approved and comp-off enabled, handle comp-off (delegated to attendance service approval flow)
    // Note: For auto-approved manual claims, comp-off granting happens through the same
    // approveOvertimeRequest logic in attendance.service.ts — we don't duplicate it here.
    // The status is already APPROVED, and the next payroll run will pick it up.

    logger.info(
      `Manual OT claim created [employee=${employeeId}, date=${data.date}, hours=${effectiveHours}, multiplier=${appliedMultiplier}x (${multiplierSource}), status=${status}]`,
    );

    return { id: otRequest.id, status };
  }

  // ── Private helpers ──

  private applyOtRounding(hours: number, strategy: string): number {
    const minutes = hours * 60;
    switch (strategy) {
      case 'NEAREST_15':
        return Math.round(minutes / 15) * 15 / 60;
      case 'NEAREST_30':
        return Math.round(minutes / 30) * 30 / 60;
      case 'FLOOR_15':
        return Math.floor(minutes / 15) * 15 / 60;
      case 'CEIL_15':
        return Math.ceil(minutes / 15) * 15 / 60;
      default:
        return hours;
    }
  }

  private async enforceOtCaps(
    companyId: string,
    employeeId: string,
    date: Date,
    hours: number,
    otRule: any,
  ): Promise<number> {
    let capped = hours;

    // Daily cap
    if (otRule.dailyCapHours) {
      const dailyCap = Number(otRule.dailyCapHours);
      const dayOt = await platformPrisma.overtimeRequest.aggregate({
        where: {
          companyId,
          employeeId,
          date,
          status: { in: ['PENDING', 'APPROVED'] },
        },
        _sum: { requestedHours: true },
      });
      const existingDay = dayOt._sum.requestedHours ? Number(dayOt._sum.requestedHours) : 0;
      const remaining = dailyCap - existingDay;
      if (remaining <= 0) return 0;
      capped = Math.min(capped, remaining);
    }

    // Weekly cap
    if (otRule.weeklyCapHours) {
      const weeklyCap = Number(otRule.weeklyCapHours);
      // Get ISO week start (Monday) and end (Sunday)
      const dayOfWeek = date.getUTCDay();
      const mondayOffset = dayOfWeek === 0 ? -6 : 1 - dayOfWeek;
      const weekStart = new Date(date);
      weekStart.setUTCDate(weekStart.getUTCDate() + mondayOffset);
      weekStart.setUTCHours(0, 0, 0, 0);
      const weekEnd = new Date(weekStart);
      weekEnd.setUTCDate(weekEnd.getUTCDate() + 7);

      const weekOt = await platformPrisma.overtimeRequest.aggregate({
        where: {
          companyId,
          employeeId,
          date: { gte: weekStart, lt: weekEnd },
          status: { in: ['PENDING', 'APPROVED'] },
        },
        _sum: { requestedHours: true },
      });
      const existingWeek = weekOt._sum.requestedHours ? Number(weekOt._sum.requestedHours) : 0;
      const remaining = weeklyCap - existingWeek;
      if (remaining <= 0) return 0;
      capped = Math.min(capped, remaining);
    }

    // Monthly cap
    if (otRule.monthlyCapHours) {
      const monthlyCap = Number(otRule.monthlyCapHours);
      const monthStart = new Date(Date.UTC(date.getUTCFullYear(), date.getUTCMonth(), 1));
      const monthEnd = new Date(Date.UTC(date.getUTCFullYear(), date.getUTCMonth() + 1, 1));

      const monthOt = await platformPrisma.overtimeRequest.aggregate({
        where: {
          companyId,
          employeeId,
          date: { gte: monthStart, lt: monthEnd },
          status: { in: ['PENDING', 'APPROVED'] },
        },
        _sum: { requestedHours: true },
      });
      const existingMonth = monthOt._sum.requestedHours ? Number(monthOt._sum.requestedHours) : 0;
      const remaining = monthlyCap - existingMonth;
      if (remaining <= 0) return 0;
      capped = Math.min(capped, remaining);
    }

    return capped;
  }

  private async determineMultiplierSource(
    companyId: string,
    employeeId: string,
    date: Date,
    shiftId: string | null,
    otRule: any,
  ): Promise<{ multiplierSource: string; appliedMultiplier: number }> {
    const dateStr = date.toISOString().split('T')[0];

    // Check holidays
    const holiday = await platformPrisma.companyHoliday.findFirst({
      where: {
        companyId,
        date: { gte: new Date(dateStr + 'T00:00:00Z'), lt: new Date(dateStr + 'T23:59:59Z') },
      },
    });
    if (holiday) {
      return {
        multiplierSource: 'HOLIDAY',
        appliedMultiplier: otRule.holidayMultiplier ? Number(otRule.holidayMultiplier) : Number(otRule.weekdayMultiplier),
      };
    }

    // Check weekly off
    const emp = await platformPrisma.employee.findUnique({
      where: { id: employeeId },
      select: { weeklyOffs: true },
    });
    if (emp?.weeklyOffs) {
      const dayNames = ['SUNDAY', 'MONDAY', 'TUESDAY', 'WEDNESDAY', 'THURSDAY', 'FRIDAY', 'SATURDAY'];
      const dayName = dayNames[date.getUTCDay()];
      const weeklyOffs = emp.weeklyOffs as string[];
      if (weeklyOffs.includes(dayName)) {
        return {
          multiplierSource: 'WEEKEND',
          appliedMultiplier: otRule.weekendMultiplier ? Number(otRule.weekendMultiplier) : Number(otRule.weekdayMultiplier),
        };
      }
    }

    // Check night shift
    if (shiftId) {
      const shift = await platformPrisma.companyShift.findUnique({
        where: { id: shiftId },
        select: { shiftType: true, startTime: true, isCrossDay: true },
      });
      if (shift) {
        const isNight =
          shift.isCrossDay ||
          shift.shiftType === 'NIGHT' ||
          (shift.startTime && Number(shift.startTime.split(':')[0]) >= 20);
        if (isNight) {
          return {
            multiplierSource: 'NIGHT_SHIFT',
            appliedMultiplier: otRule.nightShiftMultiplier
              ? Number(otRule.nightShiftMultiplier)
              : Number(otRule.weekdayMultiplier),
          };
        }
      }
    }

    // Default: weekday
    return {
      multiplierSource: 'WEEKDAY',
      appliedMultiplier: Number(otRule.weekdayMultiplier),
    };
  }
}

export const essOvertimeService = new EssOvertimeService();
```

- [ ] **Step 2: Commit**

```bash
cd /Users/chetan/Documents/Avyren-Technologies/Products/Mobile-ERP/avy-erp-backend
git add src/modules/hr/ess/ess-overtime.service.ts
git commit -m "feat(service): add ESS overtime service with list, detail, summary, and claim methods"
```

---

## Task 5: Backend Controller & Routes

**Files:**
- Modify: `avy-erp-backend/src/modules/hr/ess/ess.controller.ts`
- Modify: `avy-erp-backend/src/modules/hr/ess/ess.routes.ts`

- [ ] **Step 1: Add controller methods**

In `avy-erp-backend/src/modules/hr/ess/ess.controller.ts`, add the import at the top:

```typescript
import { essOvertimeService } from './ess-overtime.service';
import {
  claimOvertimeSchema,
  myOvertimeListSchema,
  myOvertimeSummarySchema,
} from './ess-overtime.validators';
```

Then add these 4 methods to the controller class:

```typescript
  getMyOvertimeRequests = asyncHandler(async (req: Request, res: Response) => {
    const companyId = req.user?.companyId;
    const employeeId = req.user?.employeeId;
    if (!companyId || !employeeId) throw ApiError.badRequest('Company and employee context required');

    const parsed = myOvertimeListSchema.safeParse(req.query);
    if (!parsed.success) throw ApiError.badRequest(parsed.error.errors.map((e: any) => e.message).join(', '));

    const result = await essOvertimeService.getMyOvertimeRequests(companyId, employeeId, parsed.data);
    res.json(createSuccessResponse(result.data, 'Overtime requests retrieved', result.meta));
  });

  getMyOvertimeDetail = asyncHandler(async (req: Request, res: Response) => {
    const companyId = req.user?.companyId;
    const employeeId = req.user?.employeeId;
    if (!companyId || !employeeId) throw ApiError.badRequest('Company and employee context required');

    const result = await essOvertimeService.getMyOvertimeDetail(companyId, employeeId, req.params.id);
    res.json(createSuccessResponse(result, 'Overtime request detail retrieved'));
  });

  getMyOvertimeSummary = asyncHandler(async (req: Request, res: Response) => {
    const companyId = req.user?.companyId;
    const employeeId = req.user?.employeeId;
    if (!companyId || !employeeId) throw ApiError.badRequest('Company and employee context required');

    const parsed = myOvertimeSummarySchema.safeParse(req.query);
    if (!parsed.success) throw ApiError.badRequest(parsed.error.errors.map((e: any) => e.message).join(', '));

    const result = await essOvertimeService.getMyOvertimeSummary(companyId, employeeId, parsed.data);
    res.json(createSuccessResponse(result, 'Overtime summary retrieved'));
  });

  claimOvertime = asyncHandler(async (req: Request, res: Response) => {
    const companyId = req.user?.companyId;
    const userId = req.user?.id;
    const employeeId = req.user?.employeeId;
    if (!companyId || !userId || !employeeId) throw ApiError.badRequest('Company, user, and employee context required');

    const parsed = claimOvertimeSchema.safeParse(req.body);
    if (!parsed.success) throw ApiError.badRequest(parsed.error.errors.map((e: any) => e.message).join(', '));

    const result = await essOvertimeService.claimOvertime(companyId, userId, employeeId, parsed.data);
    res.json(createSuccessResponse(result, 'Overtime claim submitted successfully'));
  });
```

- [ ] **Step 2: Add routes**

In `avy-erp-backend/src/modules/hr/ess/ess.routes.ts`, add these routes (group them together near the other ESS routes, around line 130):

```typescript
  // ── Overtime (ESS) ──
  router.get('/ess/my-overtime-requests', requireESSFeature('overtimeView'), requirePermissions(['hr:read', 'ess:view-overtime']), controller.getMyOvertimeRequests);
  router.get('/ess/my-overtime-summary', requireESSFeature('overtimeView'), requirePermissions(['hr:read', 'ess:view-overtime']), controller.getMyOvertimeSummary);
  router.get('/ess/my-overtime-requests/:id', requireESSFeature('overtimeView'), requirePermissions(['hr:read', 'ess:view-overtime']), controller.getMyOvertimeDetail);
  router.post('/ess/claim-overtime', requireESSFeature('overtimeView'), requirePermissions(['hr:create', 'ess:claim-overtime']), controller.claimOvertime);
```

- [ ] **Step 3: Commit**

```bash
cd /Users/chetan/Documents/Avyren-Technologies/Products/Mobile-ERP/avy-erp-backend
git add src/modules/hr/ess/ess.controller.ts src/modules/hr/ess/ess.routes.ts
git commit -m "feat(routes): add 4 ESS overtime endpoints (list, detail, summary, claim)"
```

---

## Task 6: Backend — Notification Dispatches & Payroll Fix

**Files:**
- Modify: `avy-erp-backend/src/modules/hr/attendance/attendance.service.ts:684-688`
- Modify: `avy-erp-backend/src/modules/hr/attendance/attendance.service.ts:1869-1873`
- Modify: `avy-erp-backend/src/modules/hr/payroll-run/payroll-run.service.ts:824-837`

- [ ] **Step 1: Add OVERTIME_AUTO_DETECTED notification in processOvertimeForRecord**

In `avy-erp-backend/src/modules/hr/attendance/attendance.service.ts`, after line 688 (after `return otRequest;` in `processOvertimeForRecord`), add the notification dispatch BEFORE the return:

Find the section around line 682-688 that looks like:
```typescript
    });

    logger.info(
      `OT request created [employee=${record.employeeId}, hours=${cappedHours}, ...`
    );

    return otRequest;
```

Add the notification dispatch after the logger.info and before the return:

```typescript
    // Notify employee that OT was auto-detected
    notificationService.dispatch({
      companyId: record.companyId,
      triggerEvent: 'OVERTIME_AUTO_DETECTED',
      entityType: 'OvertimeRequest',
      entityId: otRequest.id,
      explicitRecipients: [record.employeeId],
      tokens: {
        employee_name: '', // Will be resolved by notification service
        date: record.date.toISOString().split('T')[0],
        hours: cappedHours,
        multiplier_source: multiplierSource,
      },
      priority: 'LOW',
      type: 'OVERTIME',
      actionUrl: '/company/hr/my-overtime',
    }).catch((err) => logger.warn('Failed to dispatch OVERTIME_AUTO_DETECTED notification', err));
```

- [ ] **Step 2: Add COMP_OFF_GRANTED notification in approveOvertimeRequest**

In the same file, find the comp-off grant section (around lines 1869-1873 where `compOffGranted: true` is set). After the `overtimeRequest.update` that sets `compOffGranted: true`, add:

```typescript
    // Notify employee about comp-off grant
    notificationService.dispatch({
      companyId,
      triggerEvent: 'COMP_OFF_GRANTED',
      entityType: 'OvertimeRequest',
      entityId: id,
      explicitRecipients: [requesterUserId],
      tokens: {
        employee_name: employeeName,
        days: compOffDays,
        date: new Date(request.date).toISOString().split('T')[0],
        expires_at: expiresAt ? expiresAt.toISOString().split('T')[0] : '',
        balance: Number(updatedBalance.balance),
      },
      priority: 'MEDIUM',
      type: 'OVERTIME',
      actionUrl: '/company/hr/my-overtime',
    }).catch((err) => logger.warn('Failed to dispatch COMP_OFF_GRANTED notification', err));
```

Note: `compOffDays`, `expiresAt`, `updatedBalance`, `employeeName`, and `requesterUserId` should already be in scope from the surrounding comp-off logic. Verify variable names match the existing code.

- [ ] **Step 3: Add daily/weekly cap re-validation in payroll**

In `avy-erp-backend/src/modules/hr/payroll-run/payroll-run.service.ts`, find the cap enforcement block (lines 824-837). Add daily and weekly cap enforcement BEFORE the existing monthly cap check. Replace the block:

```typescript
        // Enforce daily/weekly/monthly caps if enforceCaps is true
        if (otRule.enforceCaps) {
          // Daily cap: group by date, scale down each day if over cap
          if (otRule.dailyCapHours) {
            const dailyCap = Number(otRule.dailyCapHours);
            const byDate = new Map<string, typeof empOtRequests>();
            for (const req of empOtRequests) {
              const dateKey = req.date instanceof Date ? req.date.toISOString().split('T')[0] : String(req.date);
              if (!byDate.has(dateKey)) byDate.set(dateKey, []);
              byDate.get(dateKey)!.push(req);
            }
            for (const dayRequests of byDate.values()) {
              const dayTotal = dayRequests.reduce((sum, r) => sum + Number(r.requestedHours), 0);
              if (dayTotal > dailyCap) {
                const scale = dailyCap / dayTotal;
                for (const req of dayRequests) {
                  req.requestedHours = round(Number(req.requestedHours) * scale) as any;
                }
              }
            }
            // Recalculate otHours after daily cap
            otHours = empOtRequests.reduce((sum, r) => sum + Number(r.requestedHours), 0);
          }

          // Weekly cap: group by ISO week, scale down each week if over cap
          if (otRule.weeklyCapHours) {
            const weeklyCap = Number(otRule.weeklyCapHours);
            const byWeek = new Map<string, typeof empOtRequests>();
            for (const req of empOtRequests) {
              const d = req.date instanceof Date ? req.date : new Date(String(req.date));
              const jan1 = new Date(Date.UTC(d.getUTCFullYear(), 0, 1));
              const weekNum = Math.ceil(((d.getTime() - jan1.getTime()) / 86400000 + jan1.getUTCDay() + 1) / 7);
              const weekKey = `${d.getUTCFullYear()}-W${weekNum}`;
              if (!byWeek.has(weekKey)) byWeek.set(weekKey, []);
              byWeek.get(weekKey)!.push(req);
            }
            for (const weekRequests of byWeek.values()) {
              const weekTotal = weekRequests.reduce((sum, r) => sum + Number(r.requestedHours), 0);
              if (weekTotal > weeklyCap) {
                const scale = weeklyCap / weekTotal;
                for (const req of weekRequests) {
                  req.requestedHours = round(Number(req.requestedHours) * scale) as any;
                }
              }
            }
            // Recalculate otHours after weekly cap
            otHours = empOtRequests.reduce((sum, r) => sum + Number(r.requestedHours), 0);
          }

          // Monthly cap (existing logic)
          if (otRule.monthlyCapHours) {
            const monthlyCap = Number(otRule.monthlyCapHours);
            if (otHours > monthlyCap) {
              const scaleFactor = monthlyCap / otHours;
              for (const group of otBySource.values()) {
                group.hours = round(group.hours * scaleFactor);
              }
              otHours = monthlyCap;
            }
          }
        }
```

Note: The daily/weekly cap logic must run BEFORE the `otBySource` grouping, so this block needs to be placed BEFORE line 792 (before the `otBySource` Map construction). Read the exact file to confirm placement — the daily/weekly caps modify `empOtRequests[].requestedHours`, and the `otBySource` loop reads from those values.

- [ ] **Step 4: Commit**

```bash
cd /Users/chetan/Documents/Avyren-Technologies/Products/Mobile-ERP/avy-erp-backend
git add src/modules/hr/attendance/attendance.service.ts src/modules/hr/payroll-run/payroll-run.service.ts
git commit -m "feat(backend): add OT auto-detected + comp-off notifications, payroll daily/weekly cap fix"
```

---

## Task 7: Mobile — API Types & Hooks

**Files:**
- Modify: `mobile-app/src/lib/api/ess.ts`
- Create: `mobile-app/src/features/ess/overtime/use-overtime-queries.ts`

- [ ] **Step 1: Add types and API functions to mobile API layer**

In `mobile-app/src/lib/api/ess.ts`, add the OT types and API functions. Add at the end of the file:

```typescript
// ── Overtime Types ──

export type OvertimeRequestStatus = 'PENDING' | 'APPROVED' | 'REJECTED' | 'PAID' | 'COMP_OFF_ACCRUED';
export type OTMultiplierSource = 'WEEKDAY' | 'WEEKEND' | 'HOLIDAY' | 'NIGHT_SHIFT';
export type OvertimeRequestSource = 'AUTO' | 'MANUAL';

export interface OvertimeRequestListItem {
  id: string;
  date: string;
  source: OvertimeRequestSource;
  requestedHours: number;
  appliedMultiplier: number;
  multiplierSource: OTMultiplierSource;
  calculatedAmount: number | null;
  status: OvertimeRequestStatus;
  reason: string | null;
  attachments: string[] | null;
  compOffGranted: boolean;
  approvalNotes: string | null;
  approvedAt: string | null;
  createdAt: string;
}

export interface OvertimeRequestDetail extends OvertimeRequestListItem {
  attendanceRecord: {
    date: string;
    punchIn: string | null;
    punchOut: string | null;
    workedHours: number | null;
    status: string;
    shiftName: string | null;
  } | null;
  approvedByName: string | null;
  requestedByName: string | null;
}

export interface OvertimeSummary {
  totalOtHours: number;
  pendingCount: number;
  approvedAmount: number;
  totalRequests: number;
  compOff: {
    balance: number;
    expiresAt: string | null;
    leaveTypeId: string | null;
  } | null;
}

export interface ClaimOvertimePayload {
  date: string;
  hours: number;
  reason: string;
  attachments?: string[];
}

export interface OvertimeListParams {
  status?: OvertimeRequestStatus;
  source?: OvertimeRequestSource;
  dateFrom?: string;
  dateTo?: string;
  page?: number;
  limit?: number;
}

// ── Overtime API Functions ──

export const essOvertimeApi = {
  getMyOvertimeRequests: (params?: OvertimeListParams) =>
    client.get('/ess/my-overtime-requests', { params }).then((r: any) => r),

  getMyOvertimeDetail: (id: string) =>
    client.get(`/ess/my-overtime-requests/${id}`).then((r: any) => r),

  getMyOvertimeSummary: (params?: { month?: number; year?: number }) =>
    client.get('/ess/my-overtime-summary', { params }).then((r: any) => r),

  claimOvertime: (data: ClaimOvertimePayload) =>
    client.post('/ess/claim-overtime', data).then((r: any) => r),
};
```

- [ ] **Step 2: Create React Query hooks**

Create `mobile-app/src/features/ess/overtime/use-overtime-queries.ts`:

```typescript
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';

import {
  essOvertimeApi,
  type ClaimOvertimePayload,
  type OvertimeListParams,
} from '@/lib/api/ess';

export const overtimeKeys = {
  all: ['ess-overtime'] as const,
  list: (params?: OvertimeListParams) =>
    params
      ? ([...overtimeKeys.all, 'list', params] as const)
      : ([...overtimeKeys.all, 'list'] as const),
  detail: (id: string) => [...overtimeKeys.all, 'detail', id] as const,
  summary: (month?: number, year?: number) =>
    [...overtimeKeys.all, 'summary', { month, year }] as const,
};

export function useMyOvertimeRequests(params?: OvertimeListParams) {
  return useQuery({
    queryKey: overtimeKeys.list(params),
    queryFn: () => essOvertimeApi.getMyOvertimeRequests(params),
  });
}

export function useMyOvertimeDetail(id: string) {
  return useQuery({
    queryKey: overtimeKeys.detail(id),
    queryFn: () => essOvertimeApi.getMyOvertimeDetail(id),
    enabled: !!id,
  });
}

export function useMyOvertimeSummary(month?: number, year?: number) {
  return useQuery({
    queryKey: overtimeKeys.summary(month, year),
    queryFn: () => essOvertimeApi.getMyOvertimeSummary({ month, year }),
  });
}

export function useClaimOvertime() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: ClaimOvertimePayload) => essOvertimeApi.claimOvertime(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: overtimeKeys.all });
    },
  });
}
```

- [ ] **Step 3: Commit**

```bash
cd /Users/chetan/Documents/Avyren-Technologies/Products/Mobile-ERP/mobile-app
git add src/lib/api/ess.ts src/features/ess/overtime/use-overtime-queries.ts
git commit -m "feat(mobile): add OT API types, functions, and React Query hooks"
```

---

## Task 8: Web — API Types & Hooks

**Files:**
- Modify: `web-system-app/src/lib/api/ess.ts` (or attendance.ts — wherever existing ESS API functions live)
- Create: `web-system-app/src/features/ess/use-overtime-queries.ts`

- [ ] **Step 1: Add types and API functions to web API layer**

Add the EXACT SAME types as mobile (see Task 7 Step 1) to the web API layer. The type names, field names, and shapes MUST be identical. Add to `web-system-app/src/lib/api/ess.ts` (or create a new file `web-system-app/src/lib/api/overtime.ts`):

```typescript
// ── Overtime Types ──
// IMPORTANT: These types MUST match mobile-app/src/lib/api/ess.ts exactly

export type OvertimeRequestStatus = 'PENDING' | 'APPROVED' | 'REJECTED' | 'PAID' | 'COMP_OFF_ACCRUED';
export type OTMultiplierSource = 'WEEKDAY' | 'WEEKEND' | 'HOLIDAY' | 'NIGHT_SHIFT';
export type OvertimeRequestSource = 'AUTO' | 'MANUAL';

export interface OvertimeRequestListItem {
  id: string;
  date: string;
  source: OvertimeRequestSource;
  requestedHours: number;
  appliedMultiplier: number;
  multiplierSource: OTMultiplierSource;
  calculatedAmount: number | null;
  status: OvertimeRequestStatus;
  reason: string | null;
  attachments: string[] | null;
  compOffGranted: boolean;
  approvalNotes: string | null;
  approvedAt: string | null;
  createdAt: string;
}

export interface OvertimeRequestDetail extends OvertimeRequestListItem {
  attendanceRecord: {
    date: string;
    punchIn: string | null;
    punchOut: string | null;
    workedHours: number | null;
    status: string;
    shiftName: string | null;
  } | null;
  approvedByName: string | null;
  requestedByName: string | null;
}

export interface OvertimeSummary {
  totalOtHours: number;
  pendingCount: number;
  approvedAmount: number;
  totalRequests: number;
  compOff: {
    balance: number;
    expiresAt: string | null;
    leaveTypeId: string | null;
  } | null;
}

export interface ClaimOvertimePayload {
  date: string;
  hours: number;
  reason: string;
  attachments?: string[];
}

export interface OvertimeListParams {
  status?: OvertimeRequestStatus;
  source?: OvertimeRequestSource;
  dateFrom?: string;
  dateTo?: string;
  page?: number;
  limit?: number;
}

// ── Overtime API Functions ──

export const essOvertimeApi = {
  getMyOvertimeRequests: (params?: OvertimeListParams) =>
    client.get('/ess/my-overtime-requests', { params }),

  getMyOvertimeDetail: (id: string) =>
    client.get(`/ess/my-overtime-requests/${id}`),

  getMyOvertimeSummary: (params?: { month?: number; year?: number }) =>
    client.get('/ess/my-overtime-summary', { params }),

  claimOvertime: (data: ClaimOvertimePayload) =>
    client.post('/ess/claim-overtime', data),
};
```

Note: Web API client already strips `.data` via interceptor, so no `.then(r => r)` needed.

- [ ] **Step 2: Create React Query hooks (mirrors mobile exactly)**

Create `web-system-app/src/features/ess/use-overtime-queries.ts`:

```typescript
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  essOvertimeApi,
  type ClaimOvertimePayload,
  type OvertimeListParams,
} from "@/lib/api/ess";

export const overtimeKeys = {
  all: ["ess-overtime"] as const,
  list: (params?: OvertimeListParams) =>
    params
      ? ([...overtimeKeys.all, "list", params] as const)
      : ([...overtimeKeys.all, "list"] as const),
  detail: (id: string) => [...overtimeKeys.all, "detail", id] as const,
  summary: (month?: number, year?: number) =>
    [...overtimeKeys.all, "summary", { month, year }] as const,
};

export function useMyOvertimeRequests(params?: OvertimeListParams) {
  return useQuery({
    queryKey: overtimeKeys.list(params),
    queryFn: () => essOvertimeApi.getMyOvertimeRequests(params),
  });
}

export function useMyOvertimeDetail(id: string) {
  return useQuery({
    queryKey: overtimeKeys.detail(id),
    queryFn: () => essOvertimeApi.getMyOvertimeDetail(id),
    enabled: !!id,
  });
}

export function useMyOvertimeSummary(month?: number, year?: number) {
  return useQuery({
    queryKey: overtimeKeys.summary(month, year),
    queryFn: () => essOvertimeApi.getMyOvertimeSummary({ month, year }),
  });
}

export function useClaimOvertime() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: ClaimOvertimePayload) => essOvertimeApi.claimOvertime(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: overtimeKeys.all });
    },
  });
}
```

- [ ] **Step 3: Commit**

```bash
cd /Users/chetan/Documents/Avyren-Technologies/Products/Mobile-ERP/web-system-app
git add src/lib/api/ src/features/ess/use-overtime-queries.ts
git commit -m "feat(web): add OT API types, functions, and React Query hooks (mirrors mobile)"
```

---

## Task 9: Mobile — My Overtime Screen

**Files:**
- Create: `mobile-app/src/features/ess/overtime/my-overtime-screen.tsx`
- Create: `mobile-app/src/features/ess/overtime/claim-overtime-modal.tsx`
- Create: `mobile-app/src/features/ess/overtime/overtime-request-detail-sheet.tsx`
- Create: `mobile-app/src/app/(app)/company/hr/my-overtime.tsx`

This is a large task. Build the main screen with summary cards, filter chips, request list, FAB, claim modal, and detail bottom sheet. Follow the exact patterns from `shift-swap-screen.tsx` and `my-expense-claims-screen.tsx`.

- [ ] **Step 1: Create the main screen**

Create `mobile-app/src/features/ess/overtime/my-overtime-screen.tsx`. This should include:
- `AppTopHeader` with title "My Overtime" and optional "+" action button
- 4 summary cards in a 2x2 grid (OT Hours, Pending, Approved Amount, Comp-Off)
- Status filter chips (All, Pending, Approved, Rejected)
- `FlashList` of OT request cards with `RefreshControl`
- FAB button for "Claim OT"
- Comp-Off card is `Pressable` — navigates to leave application with `leaveTypeId` param
- Empty state component when no requests
- Loading skeleton state

Use these hooks from `use-overtime-queries.ts`:
- `useMyOvertimeRequests(params)` for the list
- `useMyOvertimeSummary()` for the summary cards

Follow existing patterns:
- `StyleSheet.create()` + NativeWind `className` for text
- `font-inter` on ALL `<Text>`
- Colors from `@/components/ui/colors`
- `FadeInDown` animation on cards
- `useSafeAreaInsets()` for padding
- `LinearGradient` header
- Status badge colors: PENDING=warning, APPROVED=success, REJECTED=danger, PAID=primary, COMP_OFF_ACCRUED=accent
- Source badge: AUTO=neutral, MANUAL=accent
- Date formatting via `useCompanyFormatter()`

- [ ] **Step 2: Create the claim overtime modal**

Create `mobile-app/src/features/ess/overtime/claim-overtime-modal.tsx`. Bottom sheet form with:
- Date picker (restricted to last 30 days)
- Hours stepper (0.5 increments, min 0.5, max 24)
- Reason text input (multi-line, 10-500 chars, character count)
- Attachments section (existing R2 upload flow, max 5 files)
- Submit button (disabled until valid)
- Uses `useClaimOvertime()` mutation
- On success: toast + close + parent refetch
- On error: `showErrorMessage()` with API error

Use `@gorhom/bottom-sheet` with `BottomSheetModal`.

- [ ] **Step 3: Create the detail bottom sheet**

Create `mobile-app/src/features/ess/overtime/overtime-request-detail-sheet.tsx`. Bottom sheet that shows:
- Status + Source badges
- OT details (date, hours, type, multiplier, amount, comp-off)
- Attendance Record section (if linked — punch in/out, worked hours, shift)
- Approval section (approved by, at, notes)
- Reason + Attachments section (for MANUAL claims)
- Uses `useMyOvertimeDetail(id)` query

Use `@gorhom/bottom-sheet` with `BottomSheetModal`.

- [ ] **Step 4: Create the route file**

Create `mobile-app/src/app/(app)/company/hr/my-overtime.tsx`:

```typescript
export { MyOvertimeScreen as default } from '@/features/ess/overtime/my-overtime-screen';
```

- [ ] **Step 5: Verify the screen renders**

```bash
cd /Users/chetan/Documents/Avyren-Technologies/Products/Mobile-ERP/mobile-app && pnpm type-check
```

Expected: No TypeScript errors.

- [ ] **Step 6: Commit**

```bash
cd /Users/chetan/Documents/Avyren-Technologies/Products/Mobile-ERP/mobile-app
git add src/features/ess/overtime/ src/app/\(app\)/company/hr/my-overtime.tsx
git commit -m "feat(mobile): add My Overtime screen with summary, list, claim modal, and detail sheet"
```

---

## Task 10: Web — My Overtime Screen

**Files:**
- Create: `web-system-app/src/features/ess/MyOvertimeScreen.tsx`
- Create: `web-system-app/src/features/ess/ClaimOvertimeDialog.tsx`
- Create: `web-system-app/src/features/ess/OvertimeRequestDetail.tsx`
- Modify: `web-system-app/src/App.tsx`

Build the web version following the exact patterns from `ShiftSwapScreen.tsx` and `MyExpenseClaimsScreen.tsx`.

- [ ] **Step 1: Create the main screen**

Create `web-system-app/src/features/ess/MyOvertimeScreen.tsx`. This should include:
- Page header with title "My Overtime" and "+ Claim OT" button (conditionally shown via `useCanPerform('ess:claim-overtime')`)
- 4 summary cards in a responsive row (OT Hours, Pending, Approved Amount, Comp-Off)
- Filter bar: Status dropdown, Source dropdown, Date range picker
- Data table with columns: Date, Hours, Type, Source, Amount, Status
- Row click → opens detail slide-over
- Pagination controls
- Empty state component
- Loading skeleton

Use these hooks from `use-overtime-queries.ts`:
- `useMyOvertimeRequests(params)` for the table
- `useMyOvertimeSummary()` for the summary cards

Follow existing patterns:
- Tailwind CSS with primary=indigo, accent=violet
- `showSuccess()`, `showApiError()` from `@/lib/toast`
- `useCompanyFormatter()` for dates/times
- `StatusBadge` component (same pattern as ShiftSwapScreen)
- Comp-Off card is clickable → `navigate('/app/company/hr/apply-leave', { state: { preselectedLeaveType: compOff.leaveTypeId } })`

- [ ] **Step 2: Create the claim dialog**

Create `web-system-app/src/features/ess/ClaimOvertimeDialog.tsx`. Modal dialog with:
- Date input (restricted to last 30 days)
- Hours number input (0.5 step)
- Reason textarea (10-500 chars)
- Attachments drag-and-drop zone (max 5 files, uses existing R2 upload)
- Submit/Cancel buttons
- Inline validation errors
- Uses `useClaimOvertime()` mutation
- On success: `showSuccess()` + close
- On error: `showApiError()`

- [ ] **Step 3: Create the detail slide-over**

Create `web-system-app/src/features/ess/OvertimeRequestDetail.tsx`. Right-side slide-over with:
- Same sections as mobile detail sheet
- Close button
- Uses `useMyOvertimeDetail(id)` query

- [ ] **Step 4: Add route and lazy import in App.tsx**

In `web-system-app/src/App.tsx`, add the lazy import near the other ESS imports (around line 250):

```typescript
const MyOvertimeScreen = lazyNamed(() => import("./features/ess/MyOvertimeScreen"), "MyOvertimeScreen");
```

Then add the route near the other ESS routes (around line 451):

```typescript
<Route path="company/hr/my-overtime" element={<RequirePermission permission="ess:view-overtime"><MyOvertimeScreen /></RequirePermission>} />
```

- [ ] **Step 5: Verify build**

```bash
cd /Users/chetan/Documents/Avyren-Technologies/Products/Mobile-ERP/web-system-app && pnpm build
```

Expected: Build succeeds with no errors.

- [ ] **Step 6: Commit**

```bash
cd /Users/chetan/Documents/Avyren-Technologies/Products/Mobile-ERP/web-system-app
git add src/features/ess/MyOvertimeScreen.tsx src/features/ess/ClaimOvertimeDialog.tsx src/features/ess/OvertimeRequestDetail.tsx src/features/ess/use-overtime-queries.ts src/App.tsx
git commit -m "feat(web): add My Overtime screen with summary, table, claim dialog, and detail slide-over"
```

---

## Task 11: Final Integration — Type Check & Lint

**Files:** All modified files across all 3 codebases.

- [ ] **Step 1: Run backend lint and type check**

```bash
cd /Users/chetan/Documents/Avyren-Technologies/Products/Mobile-ERP/avy-erp-backend && pnpm lint && pnpm build
```

Expected: No lint errors, TypeScript compiles successfully.

- [ ] **Step 2: Run mobile type check**

```bash
cd /Users/chetan/Documents/Avyren-Technologies/Products/Mobile-ERP/mobile-app && pnpm type-check && pnpm lint
```

Expected: No TypeScript errors, no lint errors.

- [ ] **Step 3: Run web build**

```bash
cd /Users/chetan/Documents/Avyren-Technologies/Products/Mobile-ERP/web-system-app && pnpm build && pnpm lint
```

Expected: Build succeeds, no lint errors.

- [ ] **Step 4: Verify consistency between mobile and web**

Cross-check that:
- Both apps use the same query key factory names (`overtimeKeys.all`, `.list`, `.detail`, `.summary`)
- Both apps use the same API endpoint paths (`/ess/my-overtime-requests`, `/ess/my-overtime-summary`, `/ess/claim-overtime`)
- Both apps use the same type names (`OvertimeRequestListItem`, `OvertimeRequestDetail`, `OvertimeSummary`, `ClaimOvertimePayload`, `OvertimeListParams`)
- Both apps use the same enum values (`PENDING`, `APPROVED`, `REJECTED`, `PAID`, `COMP_OFF_ACCRUED`, `AUTO`, `MANUAL`, `WEEKDAY`, `WEEKEND`, `HOLIDAY`, `NIGHT_SHIFT`)
- Status badge colors match across mobile and web

- [ ] **Step 5: Final commit with all fixes**

If any lint/type fixes were needed:

```bash
cd /Users/chetan/Documents/Avyren-Technologies/Products/Mobile-ERP
git add -A
git commit -m "fix: resolve lint and type errors across all codebases"
```

---

## Task 12: Comp-Off Deep Link — Leave Screen Updates

**Files:**
- Modify: Mobile leave application screen (check `mobile-app/src/features/ess/` for leave screen)
- Modify: Web leave application screen (check `web-system-app/src/features/ess/` for leave screen)

- [ ] **Step 1: Update mobile leave screen to accept preselected leave type**

In the mobile leave application screen, check for a `preselected` route param:

```typescript
const params = useLocalSearchParams<{ leaveTypeId?: string; preselected?: string }>();

// If preselected param is provided, auto-select that leave type
useEffect(() => {
  if (params.preselected === 'COMPENSATORY' && params.leaveTypeId) {
    setSelectedLeaveTypeId(params.leaveTypeId);
  }
}, [params.preselected, params.leaveTypeId]);
```

- [ ] **Step 2: Update web leave screen to accept preselected leave type**

In the web leave application screen, check for location state:

```typescript
const location = useLocation();
const preselected = (location.state as any)?.preselectedLeaveType;

useEffect(() => {
  if (preselected) {
    setSelectedLeaveTypeId(preselected);
  }
}, [preselected]);
```

- [ ] **Step 3: Commit**

```bash
cd /Users/chetan/Documents/Avyren-Technologies/Products/Mobile-ERP
git add mobile-app/ web-system-app/
git commit -m "feat: add comp-off deep link support in leave application screens"
```

---

## Consistency Checklist

Before considering the implementation complete, verify:

| Item | Mobile | Web | Backend |
|------|--------|-----|---------|
| API endpoint paths match | `/ess/my-overtime-requests` | `/ess/my-overtime-requests` | Routes in `ess.routes.ts` |
| Type `OvertimeRequestListItem` fields | 14 fields | 14 fields | Service select clause |
| Type `OvertimeRequestDetail` fields | extends ListItem + 3 | extends ListItem + 3 | Service include clause |
| Type `OvertimeSummary` fields | 5 fields + compOff | 5 fields + compOff | Service aggregation |
| Type `ClaimOvertimePayload` fields | date, hours, reason, attachments? | date, hours, reason, attachments? | Zod schema |
| Enum `OvertimeRequestStatus` values | 5 values | 5 values | Prisma enum |
| Enum `OTMultiplierSource` values | 4 values | 4 values | Prisma enum |
| Enum `OvertimeRequestSource` values | 2 values (AUTO, MANUAL) | 2 values (AUTO, MANUAL) | Prisma enum |
| Query key factory | `overtimeKeys` (4 keys) | `overtimeKeys` (4 keys) | N/A |
| Status badge colors | warning/success/danger/primary/accent | warning/success/danger/primary/accent | N/A |
