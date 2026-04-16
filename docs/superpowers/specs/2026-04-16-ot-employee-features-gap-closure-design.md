# OT Employee Features & Gap Closure — Design Spec

## Goal

Close all remaining gaps in the Overtime (OT) system by adding employee-facing ESS features (view OT history, submit manual claims with attachments, comp-off visibility with deep link) and fixing minor payroll-time enforcement gaps. Consistent implementation across backend, web, and mobile.

## Verified Gap Summary

| # | Gap | Category |
|---|-----|----------|
| 1 | No employee-facing ESS endpoints for OT | Backend |
| 2 | No `ess-overtime` navigation manifest entry | Backend |
| 3 | No `ess:view-overtime` / `ess:claim-overtime` permissions | Backend |
| 4 | No "My Overtime" screen (web + mobile) | Frontend |
| 5 | No manual OT claim submission | Backend + Frontend |
| 6 | No comp-off balance visibility tied to OT | Frontend |
| 7 | No comp-off grant notification | Notifications |
| 8 | No employee notification on OT auto-creation | Notifications |
| 9 | Payroll doesn't re-check daily/weekly caps | Backend |

## Design Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Manual OT claims | Yes | Covers off-site/WFH overtime not captured by attendance |
| Screen style | Summary cards + filterable list | Balance of information and simplicity |
| Claim form fields | Date, hours, reason, file attachments | Full accountability for manual claims |
| Approval pipeline | Same as auto-generated (tagged) | Simpler, one approval config for all OT |
| Comp-off visibility | Inline in OT screen + deep link to leave | Contextual + actionable |
| Manager approval UI | Existing Approval Requests screen | No new screen needed |
| Payroll cap re-check | Fix daily/weekly in payroll | Belt-and-suspenders safety net |

---

## Schema Changes

### File: `prisma/modules/hrms/attendance.prisma`

### A. New Enum

```prisma
enum OvertimeRequestSource {
  AUTO
  MANUAL
}
```

### B. OvertimeRequest Model Additions

```prisma
model OvertimeRequest {
  // ... existing fields ...

  source        OvertimeRequestSource @default(AUTO)
  reason        String?               // Mandatory for MANUAL, null for AUTO
  attachments   Json?                 // Array of R2 file URLs, max 5 files

  // attendanceRecordId becomes optional (nullable)
  // MANUAL claims may not link to a specific attendance record
  attendanceRecordId String?  @unique
}
```

### C. Migration Notes

- `source` field defaults to `AUTO` — all existing records remain valid
- `attendanceRecordId` changes from required to optional — existing records keep their links
- `reason` and `attachments` are nullable — no impact on existing data
- Single migration: `ALTER TABLE` adds 3 columns + modifies 1

---

## Permission Model

### New ESS Permissions

Add to `PERMISSION_MODULES` in `permissions.ts`:

```typescript
// Within the existing 'ess' module actions array:
'view-overtime'   // Can view own OT requests and summary
'claim-overtime'  // Can submit manual OT claims
```

### Reference Role Updates

| Role | `ess:view-overtime` | `ess:claim-overtime` |
|------|---------------------|----------------------|
| Employee | Yes | Yes |
| Manager | Yes | Yes |
| HR Personnel | Yes | Yes |
| Department Head | Yes | Yes |
| Team Lead | Yes | Yes |

### ESS Config Gating

Add `viewOvertime` field to `ESSConfig` model in Prisma schema (`prisma/modules/company-admin/settings.prisma`) and to the `NAV_TO_ESS_CONFIG` mapping:

```prisma
// In ESSConfig model — add:
viewOvertime      Boolean @default(true)
```

```typescript
// NAV_TO_ESS_CONFIG in rbac.service.ts
'ess-overtime': 'viewOvertime',
```

### Navigation Manifest Entry

```typescript
{
  id: 'ess-overtime',
  label: 'My Overtime',
  icon: 'clock-alert',
  requiredPerm: 'ess:view-overtime',
  path: '/app/company/hr/my-overtime',
  module: 'hr',
  group: 'My Workspace',
  roleScope: 'company',
  sortOrder: 311,
}
```

---

## Backend API

### New Files

```
avy-erp-backend/src/modules/hr/ess/
├── ess-overtime.validators.ts    # Zod schemas
├── ess-overtime.service.ts       # Service (or methods added to existing ess.service.ts)
```

Routes added to existing `ess.routes.ts`. Controller methods added to existing `ess.controller.ts`.

### Endpoint 1: `GET /ess/my-overtime-requests`

List the authenticated employee's own OT requests with pagination and filters.

**Permission:** `ess:view-overtime`
**ESS Feature Gate:** `viewOvertime`

**Query Parameters:**
```typescript
{
  status?: 'PENDING' | 'APPROVED' | 'REJECTED' | 'PAID' | 'COMP_OFF_ACCRUED'
  source?: 'AUTO' | 'MANUAL'
  dateFrom?: string   // ISO date
  dateTo?: string     // ISO date
  page?: number       // default 1
  limit?: number      // default 20
}
```

**Response:**
```typescript
{
  success: true,
  data: OvertimeRequestListItem[],
  meta: { page, limit, total, totalPages }
}

interface OvertimeRequestListItem {
  id: string
  date: string                    // ISO date
  source: 'AUTO' | 'MANUAL'
  requestedHours: number
  appliedMultiplier: number
  multiplierSource: 'WEEKDAY' | 'WEEKEND' | 'HOLIDAY' | 'NIGHT_SHIFT'
  calculatedAmount: number | null
  status: OvertimeRequestStatus
  reason: string | null
  attachments: string[] | null
  compOffGranted: boolean
  approvalNotes: string | null
  approvedAt: string | null
  createdAt: string
}
```

**Service Logic:**
1. Get `employeeId` from authenticated user's linked employee record
2. Query `OvertimeRequest` where `employeeId` matches, apply filters
3. Order by `date DESC, createdAt DESC`
4. Return paginated results

### Endpoint 2: `GET /ess/my-overtime-requests/:id`

Single OT request detail with linked attendance record info.

**Permission:** `ess:view-overtime`

**Response:**
```typescript
{
  success: true,
  data: {
    ...OvertimeRequestListItem,
    attendanceRecord: {
      date: string
      punchIn: string | null
      punchOut: string | null
      workedHours: number | null
      status: string
      shiftName: string | null
    } | null,
    approvedByName: string | null,
    requestedByName: string | null
  }
}
```

**Service Logic:**
1. Fetch OT request by ID, verify `employeeId` matches authenticated user
2. Include attendance record details if linked
3. Include approver/requester names (join on User table)

### Endpoint 3: `GET /ess/my-overtime-summary`

Summary statistics for the "My Overtime" screen header cards.

**Permission:** `ess:view-overtime`

**Query Parameters:**
```typescript
{
  month?: number   // 1-12, defaults to current month
  year?: number    // defaults to current year
}
```

**Response:**
```typescript
{
  success: true,
  data: {
    // Current month stats
    totalOtHours: number          // Sum of approved requestedHours
    pendingCount: number          // Count of PENDING requests
    approvedAmount: number        // Sum of approved calculatedAmount
    totalRequests: number         // Total requests this month

    // Comp-off balance
    compOff: {
      balance: number             // Current comp-off leave balance (days)
      expiresAt: string | null    // Earliest expiry date, null if no expiry
      leaveTypeId: string | null  // For deep-link to apply leave
    } | null                      // null if comp-off not enabled
  }
}
```

**Service Logic:**
1. Aggregate OT requests for the employee in the given month/year
2. `totalOtHours`: SUM of `requestedHours` where `status = APPROVED`
3. `pendingCount`: COUNT where `status = PENDING`
4. `approvedAmount`: SUM of `calculatedAmount` where `status IN (APPROVED, PAID)`
5. `totalRequests`: COUNT all for the month
6. Comp-off: Query `LeaveBalance` for `COMPENSATORY` leave type, return balance + earliest `expiresAt`

### Endpoint 4: `POST /ess/claim-overtime`

Employee submits a manual OT claim.

**Permission:** `ess:claim-overtime`
**ESS Feature Gate:** `viewOvertime`

**Request Body:**
```typescript
{
  date: string          // ISO date, must be in past, within last 30 days
  hours: number         // 0.5–24, step 0.5
  reason: string        // min 10 chars, max 500 chars
  attachments?: string[] // Array of R2 file URLs, max 5
}
```

**Response:**
```typescript
{
  success: true,
  data: { id: string, status: 'PENDING' | 'APPROVED' },
  message: 'Overtime claim submitted successfully'
}
```

**Service Logic (10 steps):**

1. **Validate employee** — exists, is active, get `employeeTypeId`
2. **Check eligibility** — if `eligibleTypeIds` is set on OT rule, verify employee type is in list. Throw `ApiError.forbidden('You are not eligible for overtime claims')` if not
3. **Duplicate check** — check if OT request already exists for this employee + date. Throw `ApiError.conflict('An overtime request already exists for this date')` if found
4. **Validate hours against OT rules:**
   - Apply `minimumOtMinutes` floor: if `hours * 60 < minimumOtMinutes`, throw error
   - Apply `thresholdMinutes` dead-zone: subtract `thresholdMinutes / 60` from claimed hours (only if `calculationBasis = AFTER_SHIFT`)
5. **Apply rounding** — use `roundingStrategy` from OT rule on the hours
6. **Enforce caps (real-time):**
   - `dailyCapHours`: cap hours to daily limit
   - `weeklyCapHours`: aggregate existing OT for the ISO week, cap remaining
   - `monthlyCapHours`: aggregate existing OT for the month, cap remaining
   - `maxContinuousOtHours`: check consecutive OT streak, cap if exceeded
   - If all caps result in 0 hours, throw `ApiError.badRequest('Overtime cap exceeded for this period')`
7. **Determine multiplier source:**
   - Check company holidays for the date → `HOLIDAY`
   - Check employee's weekly off pattern → `WEEKEND`
   - Check assigned shift → `NIGHT_SHIFT` (cross-day, NIGHT type, or start >= 20:00)
   - Default → `WEEKDAY`
8. **Apply multiplier** from OT rule based on source
9. **Create OvertimeRequest:**
   ```typescript
   {
     companyId,
     employeeId,
     overtimeRuleId: otRule.id,
     date: parsedDate,
     requestedHours: cappedHours,
     appliedMultiplier: multiplier,
     multiplierSource: source,
     source: 'MANUAL',
     reason: data.reason,
     attachments: data.attachments ?? null,
     status: otRule.approvalRequired ? 'PENDING' : 'APPROVED',
     requestedBy: userId,
     attendanceRecordId: null,  // No linked attendance for manual claims
   }
   ```
10. **Post-creation:**
    - Dispatch `OVERTIME_CLAIM` notification to approvers (same as auto-generated)
    - If `approvalRequired = false`:
      - Calculate amount (same logic as `approveOvertimeRequest`)
      - If `compOffEnabled`, auto-grant comp-off
      - Set status to `APPROVED`

### Validators: `ess-overtime.validators.ts`

```typescript
import { z } from 'zod';

export const claimOvertimeSchema = z.object({
  date: z.string()
    .regex(/^\d{4}-\d{2}-\d{2}$/, 'Date must be in YYYY-MM-DD format')
    .refine(d => {
      const date = new Date(d);
      const now = new Date();
      now.setHours(0, 0, 0, 0);
      return date < now;
    }, 'Date must be in the past')
    .refine(d => {
      const date = new Date(d);
      const thirtyDaysAgo = new Date();
      thirtyDaysAgo.setDate(thirtyDaysAgo.getDate() - 30);
      thirtyDaysAgo.setHours(0, 0, 0, 0);
      return date >= thirtyDaysAgo;
    }, 'Date must be within the last 30 days'),
  hours: z.number()
    .min(0.5, 'Minimum 0.5 hours')
    .max(24, 'Maximum 24 hours')
    .multipleOf(0.5, 'Hours must be in increments of 0.5'),
  reason: z.string()
    .min(10, 'Reason must be at least 10 characters')
    .max(500, 'Reason must be at most 500 characters'),
  attachments: z.array(z.string().url())
    .max(5, 'Maximum 5 attachments')
    .optional(),
});

export const myOvertimeListSchema = z.object({
  status: z.enum([
    'PENDING', 'APPROVED', 'REJECTED', 'PAID', 'COMP_OFF_ACCRUED',
  ]).optional(),
  source: z.enum(['AUTO', 'MANUAL']).optional(),
  dateFrom: z.string().regex(/^\d{4}-\d{2}-\d{2}$/).optional(),
  dateTo: z.string().regex(/^\d{4}-\d{2}-\d{2}$/).optional(),
  page: z.coerce.number().int().min(1).default(1),
  limit: z.coerce.number().int().min(1).max(100).default(20),
});

export const myOvertimeSummarySchema = z.object({
  month: z.coerce.number().int().min(1).max(12).optional(),
  year: z.coerce.number().int().min(2020).max(2100).optional(),
});
```

---

## Notification Enhancements

### New Notification Events

Add to `trigger-events.ts`:

```typescript
{
  value: 'OVERTIME_AUTO_DETECTED',
  label: 'Overtime Auto-Detected',
  module: 'ESS',
  description: 'Triggered when the system auto-detects overtime for an employee',
}
```

### New Notification Templates

Add to `defaults.ts`:

**1. OT Auto-Detection (to employee):**
```typescript
{
  eventType: 'OVERTIME_AUTO_DETECTED',
  subject: 'Overtime Detected — {{date}}',
  body: 'The system detected {{hours}} hours of overtime on {{date}}. A request has been {{status}} for approval.',
  channels: ['PUSH', 'IN_APP'],
  priority: 'LOW',
  recipientRole: 'SELF',
  tokens: ['employee_name', 'date', 'hours', 'status', 'multiplier_source'],
}
```

**2. Comp-Off Granted (to employee):**
```typescript
{
  eventType: 'COMP_OFF_GRANTED',
  subject: 'Compensatory Off Credited',
  body: '{{days}} day(s) of compensatory off have been credited for your overtime on {{date}}.{{#expires_at}} Expires on {{expires_at}}.{{/expires_at}}',
  channels: ['PUSH', 'IN_APP', 'EMAIL'],
  priority: 'MEDIUM',
  recipientRole: 'SELF',
  tokens: ['employee_name', 'days', 'date', 'expires_at', 'balance'],
}
```

### Dispatch Points

| Event | When | Where |
|-------|------|-------|
| `OVERTIME_AUTO_DETECTED` | After `processOvertimeForRecord()` creates an auto OT request | `attendance.service.ts` |
| `COMP_OFF_GRANTED` | After comp-off leave balance is credited during OT approval | `attendance.service.ts` (inside `approveOvertimeRequest`) |

### Notification Categories

Add to `notification-categories.ts`:
```typescript
// OVERTIME category already exists, just add new events to it
```

---

## Payroll Gap Fix

### File: `payroll-run.service.ts`

### Current State
- Monthly cap re-checked at payroll time (proportional scaling)
- Daily and weekly caps NOT re-checked at payroll

### Fix: Add Daily/Weekly Cap Re-Validation

After grouping OT requests by multiplier source and before calculating amounts, add:

```typescript
// Re-validate daily caps at payroll time
if (otRule.enforceCaps && otRule.dailyCapHours) {
  const dailyCap = Number(otRule.dailyCapHours);
  // Group OT requests by date, cap each day
  const byDate = groupBy(allOtRequests, r => r.date.toISOString().split('T')[0]);
  for (const [dateStr, dayRequests] of Object.entries(byDate)) {
    const dayTotal = dayRequests.reduce((sum, r) => sum + Number(r.requestedHours), 0);
    if (dayTotal > dailyCap) {
      const scale = dailyCap / dayTotal;
      for (const req of dayRequests) {
        req.requestedHours = round(Number(req.requestedHours) * scale);
      }
    }
  }
}

// Re-validate weekly caps at payroll time
if (otRule.enforceCaps && otRule.weeklyCapHours) {
  const weeklyCap = Number(otRule.weeklyCapHours);
  // Group OT requests by ISO week, cap each week
  const byWeek = groupBy(allOtRequests, r => getISOWeek(r.date));
  for (const [week, weekRequests] of Object.entries(byWeek)) {
    const weekTotal = weekRequests.reduce((sum, r) => sum + Number(r.requestedHours), 0);
    if (weekTotal > weeklyCap) {
      const scale = weeklyCap / weekTotal;
      for (const req of weekRequests) {
        req.requestedHours = round(Number(req.requestedHours) * scale);
      }
    }
  }
}
```

This runs BEFORE the existing monthly cap check, ensuring all three levels are enforced.

---

## Mobile App — "My Overtime" Screen

### New Files

```
mobile-app/src/features/ess/overtime/
├── my-overtime-screen.tsx             # Main screen
├── claim-overtime-modal.tsx           # Bottom sheet form for manual claims
├── overtime-request-detail-sheet.tsx  # Bottom sheet for viewing request details
├── use-overtime-queries.ts            # React Query hooks
```

### Route File

```
mobile-app/src/app/(app)/company/hr/my-overtime.tsx
  → export { MyOvertimeScreen as default } from '@/features/ess/overtime/my-overtime-screen'
```

### Screen Layout

```
┌─────────────────────────────────┐
│ ← My Overtime          [+ Claim]│  LinearGradient header
├─────────────────────────────────┤
│ ┌──────────┐ ┌──────────┐      │
│ │ OT Hours │ │ Pending  │      │  Summary cards row 1
│ │  12.5h   │ │    3     │      │
│ └──────────┘ └──────────┘      │
│ ┌──────────┐ ┌──────────┐      │
│ │ Approved │ │ Comp-Off │  →   │  Summary cards row 2
│ │ ₹4,500   │ │ 1.5 days │      │  Comp-off card tappable
│ └──────────┘ └──────────┘      │  (deep links to leave)
├─────────────────────────────────┤
│ [All] [Pending] [Approved] [Rej]│  Status filter chips
├─────────────────────────────────┤
│ ┌─────────────────────────────┐ │
│ │ 📅 15 Apr 2026    APPROVED │ │  OT Request card
│ │ 2.5 hours · Weekday · 1.5x │ │
│ │ AUTO · ₹850                │ │
│ └─────────────────────────────┘ │
│ ┌─────────────────────────────┐ │
│ │ 📅 14 Apr 2026     PENDING │ │
│ │ 3.0 hours · Holiday · 2.0x │ │
│ │ MANUAL · Reason preview...  │ │
│ │ 📎 2 attachments            │ │
│ └─────────────────────────────┘ │
│           ...                   │
│                                 │
│                    [+ Claim OT] │  FAB button
└─────────────────────────────────┘
```

### Summary Cards

4 cards in a 2x2 grid:

| Card | Icon | Label | Value | Color |
|------|------|-------|-------|-------|
| OT Hours | `clock` | OT Hours | `12.5h` | Primary (indigo) |
| Pending | `hourglass` | Pending | `3` | Warning (amber) |
| Approved | `indian-rupee` | Approved | `₹4,500` | Success (green) |
| Comp-Off | `gift` | Comp-Off | `1.5 days` | Accent (violet) |

- Comp-Off card shows expiry below value: `Expires: 15 Jul 2026`
- Comp-Off card is tappable → navigates to leave application with COMPENSATORY type pre-selected
- If comp-off not enabled, card shows `—` with "Not enabled" text

### Request List

- `FlashList` with pull-to-refresh
- Status filter chips at top (All / Pending / Approved / Rejected)
- Each card shows: date, hours, multiplier source badge, multiplier value, source tag (AUTO/MANUAL), amount or "Pending"
- MANUAL cards show reason preview (truncated) + attachment count
- Tap card → opens detail bottom sheet

### Claim OT Modal (Bottom Sheet)

Triggered by FAB button or header `+` button.

```
┌─────────────────────────────────┐
│ Claim Overtime              ✕   │
├─────────────────────────────────┤
│ Date *                          │
│ [Date picker — last 30 days]    │
│                                 │
│ Hours *                         │
│ [Stepper: 0.5 increments]      │
│  0.5  1.0  1.5  2.0 ... 24.0   │
│                                 │
│ Reason *                        │
│ [Multi-line text input]         │
│ Min 10 characters               │
│                                 │
│ Attachments (optional)          │
│ [+ Add file]  max 5 files       │
│ ┌────┐ ┌────┐                   │
│ │ 📄 │ │ 📄 │  (removable)      │
│ └────┘ └────┘                   │
│                                 │
│ ┌─────────────────────────────┐ │
│ │       Submit Claim          │ │
│ └─────────────────────────────┘ │
└─────────────────────────────────┘
```

**Form Behavior:**
- Date picker restricted to past 30 days only
- Hours stepper: 0.5 increments, min 0.5, max 24
- Reason: multi-line TextInput, 10–500 chars, character count shown
- Attachments: uses existing R2 file upload flow, max 5 files, shows thumbnails for images
- Submit button disabled until all required fields valid
- On submit: mutation → success toast → close modal → refetch list
- On error: show error message inline (e.g., "Cap exceeded", "Duplicate date", "Not eligible")

### Detail Bottom Sheet

Opened when tapping a request card:

```
┌─────────────────────────────────┐
│ Overtime Details            ✕   │
├─────────────────────────────────┤
│ Status: [APPROVED badge]        │
│ Source: [AUTO badge]            │
│                                 │
│ Date           15 Apr 2026      │
│ Hours          2.5              │
│ Type           Weekday · 1.5x  │
│ Amount         ₹850.00         │
│ Comp-Off       Yes (0.5 days)  │
│                                 │
│ ── Attendance Record ────────── │
│ Punch In       09:00 AM        │
│ Punch Out      07:30 PM        │
│ Worked Hours   10.5            │
│ Shift          General (9-6)   │
│                                 │
│ ── Approval ─────────────────── │
│ Approved By    John Doe         │
│ Approved At    15 Apr 2026 5PM  │
│ Notes          Verified shift   │
│                                 │
│ (For MANUAL claims:)            │
│ ── Reason ───────────────────── │
│ Worked on client delivery...    │
│                                 │
│ ── Attachments ──────────────── │
│ 📎 project-email.pdf            │
│ 📎 approval-screenshot.png      │
└─────────────────────────────────┘
```

### React Query Hooks: `use-overtime-queries.ts`

```typescript
// Query key factory
export const overtimeKeys = {
  all: ['ess-overtime'] as const,
  list: (params?: OvertimeListParams) =>
    params ? [...overtimeKeys.all, 'list', params] : [...overtimeKeys.all, 'list'],
  detail: (id: string) => [...overtimeKeys.all, 'detail', id],
  summary: (month?: number, year?: number) =>
    [...overtimeKeys.all, 'summary', { month, year }],
};

// Hooks
useMyOvertimeRequests(params)    // GET /ess/my-overtime-requests
useMyOvertimeDetail(id)          // GET /ess/my-overtime-requests/:id
useMyOvertimeSummary(month, year) // GET /ess/my-overtime-summary
useClaimOvertime()               // POST /ess/claim-overtime (mutation)
```

### UI Patterns (following codebase conventions)

- `StyleSheet.create()` for layouts + NativeWind `className` for text
- `font-inter` on ALL `<Text>` components
- Colors from `@/components/ui/colors` — primary (indigo), accent (violet)
- Animations: `FadeInDown`, `FadeInUp` from `react-native-reanimated`
- Safe area: `useSafeAreaInsets()` for padding
- Header: `LinearGradient` with `colors.gradient.start/mid/end`
- Bottom sheets: `@gorhom/bottom-sheet`
- Status badges: color-coded (PENDING: amber, APPROVED: green, REJECTED: red, PAID: blue, COMP_OFF_ACCRUED: violet)
- Date/time formatting: `useCompanyFormatter()` hook — never raw `toLocaleDateString()`
- Confirmation for destructive actions: `useConfirmModal()` — never `Alert.alert()`

---

## Web App — "My Overtime" Screen

### New Files

```
web-system-app/src/features/ess/overtime/
├── MyOvertimeScreen.tsx              # Main screen
├── ClaimOvertimeDialog.tsx           # Modal dialog for manual claims
├── OvertimeRequestDetail.tsx         # Detail view (slide-over or dialog)
├── use-overtime-queries.ts           # React Query hooks (same key factory as mobile)
```

### Route

Add to `App.tsx` route config:
```typescript
{ path: '/app/company/hr/my-overtime', element: <MyOvertimeScreen /> }
```

### Screen Layout

```
┌──────────────────────────────────────────────────────┐
│ My Overtime                              [+ Claim OT]│
├──────────────────────────────────────────────────────┤
│ ┌───────────┐ ┌───────────┐ ┌───────────┐ ┌────────┐│
│ │ OT Hours  │ │  Pending  │ │ Approved  │ │Comp-Off││
│ │  12.5h    │ │     3     │ │  ₹4,500   │ │1.5 days││
│ │ this month│ │  requests │ │  amount   │ │exp: Jul││
│ └───────────┘ └───────────┘ └───────────┘ └────────┘│
├──────────────────────────────────────────────────────┤
│ Filters: [Status ▾] [Source ▾] [Date range]          │
├──────────────────────────────────────────────────────┤
│ Date       │ Hours │ Type    │ Source │ Amount │Status│
│────────────┼───────┼─────────┼────────┼────────┼──────│
│ 15 Apr '26 │ 2.5   │ Weekday │ AUTO   │ ₹850   │ ✅  │
│ 14 Apr '26 │ 3.0   │ Holiday │ MANUAL │ —      │ ⏳  │
│ 12 Apr '26 │ 1.5   │ Night   │ AUTO   │ ₹720   │ ✅  │
│ ...        │       │         │        │        │      │
├──────────────────────────────────────────────────────┤
│ < 1 2 3 ... 5 >                       Showing 1-20  │
└──────────────────────────────────────────────────────┘
```

### Summary Cards

Same 4 cards as mobile, laid out in a single row (responsive — stacks on narrow screens):
- Comp-Off card clickable → navigates to leave application

### Table

- Sortable columns: Date, Hours, Amount
- Filterable: Status (multi-select), Source (AUTO/MANUAL), Date range
- Row click → opens detail slide-over
- MANUAL rows show reason icon tooltip + attachment count badge
- Pagination: standard page/limit controls

### Claim OT Dialog

Standard modal dialog (not full-page) triggered by "+ Claim OT" button:
- Same fields as mobile: Date picker, Hours input, Reason textarea, Attachments upload
- Date restricted to last 30 days
- Hours: number input with 0.5 step
- Attachments: drag-and-drop zone + click-to-upload, max 5 files
- Inline validation errors
- Submit/Cancel buttons

### Detail Slide-Over

Right-side slide-over panel when clicking a table row:
- Same information as mobile detail bottom sheet
- Sections: Status, OT Details, Attendance Record, Approval Info, Reason + Attachments (for MANUAL)

### UI Patterns (following codebase conventions)

- Tailwind CSS with custom color palette (primary=indigo, accent=violet)
- React Query for server state, same key factory as mobile
- Toast: `showSuccess()`, `showApiError()` from `@/lib/toast`
- Forms: React Hook Form with Zod resolver
- Date/time: `useCompanyFormatter()` hook
- Permission check: `useCanPerform('ess:claim-overtime')` to show/hide Claim button
- API client: Axios with `.then(r => r.data)` — in components use `data?.data` to unwrap

---

## API Client Updates

### Mobile: `mobile-app/src/lib/api/`

Add to existing ESS API module (or create `overtime.ts`):

```typescript
// Types — shared between mobile and web (define in each app's api layer)
export type OvertimeRequestStatus = 'PENDING' | 'APPROVED' | 'REJECTED' | 'PAID' | 'COMP_OFF_ACCRUED'
export type OTMultiplierSource = 'WEEKDAY' | 'WEEKEND' | 'HOLIDAY' | 'NIGHT_SHIFT'
export type OvertimeRequestSource = 'AUTO' | 'MANUAL'

export interface OvertimeRequestListItem {
  id: string
  date: string
  source: OvertimeRequestSource
  requestedHours: number
  appliedMultiplier: number
  multiplierSource: OTMultiplierSource
  calculatedAmount: number | null
  status: OvertimeRequestStatus
  reason: string | null
  attachments: string[] | null
  compOffGranted: boolean
  approvalNotes: string | null
  approvedAt: string | null
  createdAt: string
}

export interface OvertimeRequestDetail extends OvertimeRequestListItem {
  attendanceRecord: {
    date: string
    punchIn: string | null
    punchOut: string | null
    workedHours: number | null
    status: string
    shiftName: string | null
  } | null
  approvedByName: string | null
  requestedByName: string | null
}

export interface OvertimeSummary {
  totalOtHours: number
  pendingCount: number
  approvedAmount: number
  totalRequests: number
  compOff: {
    balance: number
    expiresAt: string | null
    leaveTypeId: string | null
  } | null
}

export interface ClaimOvertimePayload {
  date: string
  hours: number
  reason: string
  attachments?: string[]
}

// API functions
getMyOvertimeRequests(params): Promise<PaginatedResponse<OvertimeRequestListItem>>
getMyOvertimeDetail(id): Promise<ApiResponse<OvertimeRequestDetail>>
getMyOvertimeSummary(month?, year?): Promise<ApiResponse<OvertimeSummary>>
claimOvertime(data: ClaimOvertimePayload): Promise<ApiResponse<{ id: string; status: string }>>
```

### Web: `web-system-app/src/lib/api/`

Same types and functions, using the web API client pattern.

---

## Approval Workflow Integration

### How Manual Claims Enter the Approval Queue

Manual claims created via `POST /ess/claim-overtime` follow the same flow as auto-generated:

1. OT request created with `status: PENDING` (if `approvalRequired = true`)
2. `OVERTIME_CLAIM` notification dispatched to configured approvers
3. Request appears in the existing **Approval Requests** screen alongside other ESS requests
4. Approver sees the request with `source: MANUAL` tag, reason text, and attachment links
5. Approver approves/rejects using existing `PATCH /hr/overtime-requests/:id/approve|reject`
6. Employee gets `OVERTIME_CLAIM_APPROVED` or `OVERTIME_CLAIM_REJECTED` notification

### Approval Request Display Enhancement

In the existing Approval Requests screen, OT requests should display:
- Source badge: `AUTO` (muted) or `MANUAL` (highlighted)
- For MANUAL: reason text preview + attachment count
- For AUTO: linked attendance record summary (punch in/out, worked hours)

---

## Comp-Off Deep Link

### Mobile Navigation

When employee taps the Comp-Off summary card:

```typescript
router.push({
  pathname: '/app/company/hr/apply-leave',
  params: {
    leaveTypeId: compOff.leaveTypeId,
    preselected: 'COMPENSATORY',
  },
});
```

The leave application screen should check for `preselected` param and auto-select the COMPENSATORY leave type.

### Web Navigation

```typescript
navigate('/app/company/hr/apply-leave', {
  state: { preselectedLeaveType: compOff.leaveTypeId },
});
```

### Leave Screen Update

Both web and mobile leave application screens need a minor update:
- Check for preselected leave type param/state
- If present, auto-select that leave type in the dropdown
- Show comp-off balance and expiry prominently when COMPENSATORY type is selected

---

## Edge Cases & Error Handling

### Manual Claim Validation Errors

| Scenario | Error Message | HTTP Status |
|----------|---------------|-------------|
| Employee type not eligible | "You are not eligible for overtime claims" | 403 |
| Duplicate date | "An overtime request already exists for this date" | 409 |
| Hours below minimum | "Minimum overtime is {x} minutes" | 400 |
| All caps exceeded | "Overtime cap exceeded for this period" | 400 |
| Daily cap hit | "Daily overtime cap of {x} hours reached" | 400 |
| Weekly cap hit | "Weekly overtime cap of {x} hours reached for this week" | 400 |
| Monthly cap hit | "Monthly overtime cap of {x} hours reached" | 400 |
| Date > 30 days ago | "Date must be within the last 30 days" | 400 |
| Future date | "Date must be in the past" | 400 |
| Too many attachments | "Maximum 5 attachments allowed" | 400 |
| Reason too short | "Reason must be at least 10 characters" | 400 |
| Comp-off not enabled | Comp-off card shows "Not enabled" (no error, just UI state) | — |
| Employee inactive | "Your account is not active" | 403 |

### Auto-OT Edge Cases

| Scenario | Behavior |
|----------|----------|
| Auto OT created but employee also submits manual for same date | Duplicate check prevents this — error returned |
| OT approved then OT rule changed (multiplier changed) | Amount is locked at approval time, not recalculated |
| Comp-off granted but leave type deleted | Comp-off card shows balance but deep link may fail — handle gracefully |
| Payroll already processed for month, new OT approved | OT marked APPROVED but not included in past payroll — next run picks it up |

---

## Testing Strategy

### Backend Unit Tests

```
src/modules/hr/ess/__tests__/ess-overtime.test.ts
```

| Test | Description |
|------|-------------|
| `GET /ess/my-overtime-requests` | Returns only authenticated employee's requests |
| `GET /ess/my-overtime-requests` | Filters by status, source, date range work correctly |
| `GET /ess/my-overtime-requests` | Pagination works correctly |
| `GET /ess/my-overtime-summary` | Aggregates correct totals for month |
| `GET /ess/my-overtime-summary` | Returns comp-off balance and expiry |
| `POST /ess/claim-overtime` | Creates MANUAL OT request with correct fields |
| `POST /ess/claim-overtime` | Rejects ineligible employee types |
| `POST /ess/claim-overtime` | Rejects duplicate date |
| `POST /ess/claim-overtime` | Applies thresholdMinutes correctly |
| `POST /ess/claim-overtime` | Applies minimumOtMinutes floor |
| `POST /ess/claim-overtime` | Enforces daily/weekly/monthly caps |
| `POST /ess/claim-overtime` | Determines correct multiplier source |
| `POST /ess/claim-overtime` | Auto-approves when approvalRequired=false |
| `POST /ess/claim-overtime` | Grants comp-off on auto-approval |
| `POST /ess/claim-overtime` | Rejects future dates |
| `POST /ess/claim-overtime` | Rejects dates > 30 days ago |
| Payroll cap fix | Daily cap re-validated at payroll time |
| Payroll cap fix | Weekly cap re-validated at payroll time |
| Notifications | OVERTIME_AUTO_DETECTED dispatched on auto-creation |
| Notifications | COMP_OFF_GRANTED dispatched on comp-off credit |

### Frontend Tests

- Component renders summary cards with correct data
- Claim form validates all fields
- Status filter chips filter the list
- Deep link to leave module works
- Error states display correctly
- Loading/empty states render

---

## Files Changed Summary

### Backend (`avy-erp-backend/`)

| File | Change |
|------|--------|
| `prisma/modules/hrms/attendance.prisma` | Add `OvertimeRequestSource` enum, add `source`, `reason`, `attachments` fields, make `attendanceRecordId` optional |
| `src/modules/hr/ess/ess-overtime.validators.ts` | **NEW** — Zod schemas |
| `src/modules/hr/ess/ess.service.ts` | Add 4 new methods for OT ESS endpoints |
| `src/modules/hr/ess/ess.controller.ts` | Add 4 new controller methods |
| `src/modules/hr/ess/ess.routes.ts` | Add 4 new routes |
| `src/modules/hr/attendance/attendance.service.ts` | Add `OVERTIME_AUTO_DETECTED` notification dispatch in `processOvertimeForRecord()`, add `COMP_OFF_GRANTED` dispatch in `approveOvertimeRequest()` |
| `src/modules/hr/payroll-run/payroll-run.service.ts` | Add daily/weekly cap re-validation before amount calculation |
| `src/shared/constants/navigation-manifest.ts` | Add `ess-overtime` entry |
| `src/shared/constants/permissions.ts` | Add `view-overtime`, `claim-overtime` to ESS actions |
| `src/shared/constants/trigger-events.ts` | Add `OVERTIME_AUTO_DETECTED` event |
| `src/core/notifications/templates/defaults.ts` | Add `OVERTIME_AUTO_DETECTED` and `COMP_OFF_GRANTED` templates |
| `src/core/notifications/notification-categories.ts` | Add new events to `OVERTIME` category |
| `src/core/rbac/rbac.service.ts` | Add `ess-overtime` to `NAV_TO_ESS_CONFIG` mapping |
| `prisma/modules/company-admin/settings.prisma` | Add `viewOvertime` Boolean field to `ESSConfig` model |

### Mobile (`mobile-app/`)

| File | Change |
|------|--------|
| `src/features/ess/overtime/my-overtime-screen.tsx` | **NEW** — Main screen |
| `src/features/ess/overtime/claim-overtime-modal.tsx` | **NEW** — Bottom sheet claim form |
| `src/features/ess/overtime/overtime-request-detail-sheet.tsx` | **NEW** — Detail bottom sheet |
| `src/features/ess/overtime/use-overtime-queries.ts` | **NEW** — React Query hooks |
| `src/app/(app)/company/hr/my-overtime.tsx` | **NEW** — Route file |
| `src/lib/api/ess.ts` (or `overtime.ts`) | Add OT API functions + types |
| `src/features/ess/leave/` (leave application screen) | Accept `preselected` param to auto-select COMPENSATORY leave type |

### Web (`web-system-app/`)

| File | Change |
|------|--------|
| `src/features/ess/overtime/MyOvertimeScreen.tsx` | **NEW** — Main screen |
| `src/features/ess/overtime/ClaimOvertimeDialog.tsx` | **NEW** — Modal dialog |
| `src/features/ess/overtime/OvertimeRequestDetail.tsx` | **NEW** — Detail slide-over |
| `src/features/ess/overtime/use-overtime-queries.ts` | **NEW** — React Query hooks |
| `src/App.tsx` | Add route for `/app/company/hr/my-overtime` |
| `src/lib/api/ess.ts` (or `overtime.ts`) | Add OT API functions + types |
| `src/features/ess/leave/` (leave application screen) | Accept `preselectedLeaveType` state to auto-select COMPENSATORY leave type |
