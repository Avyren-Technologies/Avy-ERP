# Attendance Enforcement Fixes — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Fix 8 attendance gaps where configuration exists but is not enforced — geofence enforcement with configurable modes, selfie/GPS validation in ESS, punch validator integration, and dead config field activation.

**Architecture:** Add `GeofenceEnforcementMode` enum to AttendanceRule schema, then wire enforcement into `ess.controller.ts` checkIn/checkOut methods. Integrate existing `punch-validator.service.ts` into `attendance-status-resolver.service.ts`. Add two new cron jobs for auto-absent and missing-punch alerts.

**Tech Stack:** Prisma, Express, node-cron, Zod, Luxon

**Spec:** `docs/superpowers/specs/2026-04-16-attendance-enforcement-fixes-design.md`

---

## File Structure

### New Files
| File | Responsibility |
|------|---------------|
| `avy-erp-backend/src/shared/jobs/attendance-cron.service.ts` | Cron jobs: autoAbsentAfterDays + missingPunchAlert |

### Modified Files
| File | Change |
|------|--------|
| `avy-erp-backend/prisma/modules/hrms/attendance.prisma` | Add `GeofenceEnforcementMode` enum + field |
| `avy-erp-backend/src/modules/hr/ess/ess.controller.ts` | Add geofence/selfie/GPS enforcement to checkIn + checkOut |
| `avy-erp-backend/src/modules/hr/ess/ess.service.ts` | Add regularization window validation |
| `avy-erp-backend/src/shared/services/attendance-status-resolver.service.ts` | Integrate punch validator |
| `avy-erp-backend/src/shared/services/policy-resolver.service.ts` | Add `geofenceEnforcementMode` to resolved policy |
| `avy-erp-backend/src/shared/constants/trigger-events.ts` | Add `MISSING_PUNCH_ALERT` |
| `avy-erp-backend/src/core/notifications/templates/defaults.ts` | Add missing punch template |
| `avy-erp-backend/src/shared/constants/notification-categories.ts` | Add mapping |
| `avy-erp-backend/src/app/server.ts` | Register attendance cron |
| Web + Mobile attendance rules config screens | Add geofence mode dropdown |

---

## Task 1: Schema — GeofenceEnforcementMode

**Files:**
- Modify: `avy-erp-backend/prisma/modules/hrms/attendance.prisma:94-151`

- [ ] **Step 1: Add enum and field**

In `attendance.prisma`, add the new enum after existing enums (after `RoundingDirection`):

```prisma
enum GeofenceEnforcementMode {
  OFF
  WARN
  STRICT
}
```

Add field to AttendanceRule model after `gpsRequired` (line ~145):

```prisma
  geofenceEnforcementMode GeofenceEnforcementMode @default(OFF)
```

- [ ] **Step 2: Run prisma merge + generate**

```bash
cd avy-erp-backend && pnpm prisma:merge && pnpm db:generate
```

- [ ] **Step 3: Create migration**

```bash
cd avy-erp-backend && pnpm db:migrate --name add_geofence_enforcement_mode
```

- [ ] **Step 4: Commit**

```bash
cd /Users/chetan/Documents/Avyren-Technologies/Products/Mobile-ERP/avy-erp-backend
git add prisma/
git commit -m "feat(schema): add GeofenceEnforcementMode enum to AttendanceRule"
```

---

## Task 2: Policy Resolver — Add geofenceEnforcementMode

**Files:**
- Modify: `avy-erp-backend/src/shared/services/policy-resolver.service.ts`

- [ ] **Step 1: Add field to ResolvedPolicy interface**

Find the `ResolvedPolicy` interface (around line 32-42) and add:

```typescript
  geofenceEnforcementMode: string; // 'OFF' | 'WARN' | 'STRICT'
```

- [ ] **Step 2: Add resolution logic**

In the `resolvePolicy` function, `geofenceEnforcementMode` comes from AttendanceRule only (not overridable by shift/location). Add after the existing field resolutions:

```typescript
  geofenceEnforcementMode: attendanceRule?.geofenceEnforcementMode ?? 'OFF',
```

- [ ] **Step 3: Commit**

```bash
cd /Users/chetan/Documents/Avyren-Technologies/Products/Mobile-ERP/avy-erp-backend
git add src/shared/services/policy-resolver.service.ts
git commit -m "feat(policy): add geofenceEnforcementMode to resolved policy"
```

---

## Task 3: ESS Controller — Geofence + Selfie + GPS Enforcement (A1-A4)

**Files:**
- Modify: `avy-erp-backend/src/modules/hr/ess/ess.controller.ts:1182-1587`

This is the core fix. The ESS controller checkIn (line 1182) and checkOut (line 1377) need 3 enforcement blocks each.

- [ ] **Step 1: Add enforcement to checkIn method**

In `ess.controller.ts`, find the checkIn method. After the policy is resolved and geoStatus is computed (around line 1257), but BEFORE the attendance record is created, add:

```typescript
    // ── Policy Enforcement (A3+A4): Selfie & GPS validation ──
    if (policy.selfieRequired && !parsed.data.photoUrl) {
      throw ApiError.badRequest('Selfie photo is required by company policy');
    }
    if (policy.gpsRequired && (latitude == null || longitude == null)) {
      throw ApiError.badRequest('GPS location is required by company policy');
    }

    // ── Policy Enforcement (A1+A2): Geofence enforcement ──
    if (policy.geofenceEnforcementMode !== 'OFF' && geoStatus === 'OUTSIDE_GEOFENCE') {
      if (policy.geofenceEnforcementMode === 'STRICT') {
        throw ApiError.forbidden('You must be inside the designated geofence area to check in');
      }
      // WARN mode: allow but notify manager
      if (policy.geofenceEnforcementMode === 'WARN') {
        // Fire-and-forget notification to manager
        notificationService.dispatch({
          companyId,
          triggerEvent: 'GEOFENCE_VIOLATION',
          entityType: 'AttendanceRecord',
          entityId: employeeId,
          tokens: {
            employee_name: '',
            date: new Date().toISOString().split('T')[0],
            action: 'check-in',
            location_name: empGeo?.location?.locationName ?? 'Unknown',
          },
          priority: 'HIGH',
          type: 'ATTENDANCE',
        }).catch((err: any) => logger.warn('Failed to dispatch geofence violation notification', err));
      }
    }
```

- [ ] **Step 2: Add same enforcement to checkOut method**

In checkOut (line 1377), add the same 3 blocks after policy resolution and geoStatus computation. The code is identical except change `'check-in'` to `'check-out'` in the notification token.

Read the checkOut method to find where geoStatus is computed (the checkout section around lines 1530-1560 where geoStatus is calculated), and insert the enforcement BEFORE the attendance record update.

- [ ] **Step 3: Add GEOFENCE_VIOLATION trigger event**

In `src/shared/constants/trigger-events.ts`, add:

```typescript
  {
    value: 'GEOFENCE_VIOLATION',
    label: 'Geofence Violation',
    module: 'Attendance',
    description: 'Triggered when an employee checks in/out outside the designated geofence (WARN mode)',
  },
```

Add notification template in `defaults.ts`:

```typescript
  {
    code: 'GEOFENCE_VIOLATION',
    name: 'Geofence Violation Warning',
    subject: '{{employee_name}} checked {{action}} outside geofence',
    body: '{{employee_name}} checked {{action}} outside the designated area at {{location_name}} on {{date}}.',
    channels: ['PUSH', 'IN_APP'],
    priority: 'HIGH',
    variables: ['employee_name', 'date', 'action', 'location_name'],
    sensitiveFields: [],
    category: 'ATTENDANCE',
    triggerEvent: 'GEOFENCE_VIOLATION',
    recipientRole: 'MANAGER',
  },
```

Add to notification-categories.ts: `GEOFENCE_VIOLATION: 'ATTENDANCE',`

- [ ] **Step 4: Commit**

```bash
cd /Users/chetan/Documents/Avyren-Technologies/Products/Mobile-ERP/avy-erp-backend
git add src/modules/hr/ess/ess.controller.ts src/shared/constants/ src/core/notifications/
git commit -m "feat(attendance): enforce geofence/selfie/GPS in ESS check-in and check-out"
```

---

## Task 4: ESS Regularization Window Enforcement (A6)

**Files:**
- Modify: `avy-erp-backend/src/modules/hr/ess/ess.service.ts:1835-1859`

- [ ] **Step 1: Add window validation**

In the `regularizeAttendance` method (line ~1835), after verifying the employee and checking ESS config, but BEFORE creating the override request, add:

```typescript
    // ── A6: Enforce regularization window ──
    const rules = await platformPrisma.attendanceRule.findUnique({
      where: { companyId },
      select: { regularizationWindowDays: true },
    });
    const windowDays = rules?.regularizationWindowDays ?? 7;
    if (windowDays > 0) {
      const recordDate = DateTime.fromJSDate(new Date(record.date)).startOf('day');
      const cutoff = DateTime.now().startOf('day').minus({ days: windowDays });
      if (recordDate < cutoff) {
        throw ApiError.badRequest(
          `Cannot regularize attendance older than ${windowDays} days. The cutoff date is ${cutoff.toISODate()}.`,
        );
      }
    }
```

Ensure `DateTime` from Luxon is imported at the top of the file.

- [ ] **Step 2: Commit**

```bash
cd /Users/chetan/Documents/Avyren-Technologies/Products/Mobile-ERP/avy-erp-backend
git add src/modules/hr/ess/ess.service.ts
git commit -m "feat(ess): enforce regularization window in ESS regularization path"
```

---

## Task 5: Integrate Punch Validator (A8)

**Files:**
- Modify: `avy-erp-backend/src/shared/services/attendance-status-resolver.service.ts:175-220`

- [ ] **Step 1: Import punch validator**

At the top of `attendance-status-resolver.service.ts`, add:

```typescript
import { validatePunchSequence } from './punch-validator.service';
```

- [ ] **Step 2: Integrate into resolveAttendanceStatus**

In the `resolveAttendanceStatus` function, before the worked hours calculation (around line 210), add punch mode validation:

```typescript
  // ── A8: Apply punch mode validation ──
  let effectivePunchIn = punchIn;
  let effectivePunchOut = punchOut;

  if (punchIn && punchOut && policy.punchMode !== 'FIRST_LAST') {
    // For EVERY_PAIR and SHIFT_BASED modes, use the punch validator
    const punches = [
      { time: punchIn, type: 'IN' as const },
      { time: punchOut, type: 'OUT' as const },
    ];
    const validated = validatePunchSequence(
      punches,
      policy.punchMode,
      shift?.shiftStart ? new Date(shift.shiftStart) : null,
      shift?.shiftEnd ? new Date(shift.shiftEnd) : null,
    );
    if (validated.effectivePunchIn) effectivePunchIn = validated.effectivePunchIn;
    if (validated.effectivePunchOut) effectivePunchOut = validated.effectivePunchOut;
  }
```

Then replace the existing `punchIn`/`punchOut` references in the worked hours calculation with `effectivePunchIn`/`effectivePunchOut`.

Read the exact punch validator return type from `punch-validator.service.ts` to ensure field names match.

- [ ] **Step 3: Commit**

```bash
cd /Users/chetan/Documents/Avyren-Technologies/Products/Mobile-ERP/avy-erp-backend
git add src/shared/services/attendance-status-resolver.service.ts
git commit -m "feat(attendance): integrate punch validator for EVERY_PAIR and SHIFT_BASED modes"
```

---

## Task 6: Attendance Cron Jobs (A5 + A7)

**Files:**
- Create: `avy-erp-backend/src/shared/jobs/attendance-cron.service.ts`
- Modify: `avy-erp-backend/src/app/server.ts:46-59`
- Modify: `avy-erp-backend/src/shared/constants/trigger-events.ts`
- Modify: `avy-erp-backend/src/core/notifications/templates/defaults.ts`
- Modify: `avy-erp-backend/src/shared/constants/notification-categories.ts`

- [ ] **Step 1: Add MISSING_PUNCH_ALERT trigger event and template**

In `trigger-events.ts`:
```typescript
  {
    value: 'MISSING_PUNCH_ALERT',
    label: 'Missing Punch Alert',
    module: 'Attendance',
    description: 'Triggered when an employee has an incomplete punch (check-in without check-out)',
  },
```

In `defaults.ts`:
```typescript
  {
    code: 'MISSING_PUNCH_ALERT',
    name: 'Missing Punch Alert',
    subject: 'Missing punch on {{date}}',
    body: 'You have an incomplete attendance record on {{date}}. Please check out or request regularization.',
    channels: ['PUSH', 'IN_APP'],
    priority: 'MEDIUM',
    variables: ['employee_name', 'date'],
    sensitiveFields: [],
    category: 'ATTENDANCE',
    triggerEvent: 'MISSING_PUNCH_ALERT',
    recipientRole: 'SELF',
  },
```

In `notification-categories.ts`: `MISSING_PUNCH_ALERT: 'ATTENDANCE',`

- [ ] **Step 2: Create attendance cron service**

Create `avy-erp-backend/src/shared/jobs/attendance-cron.service.ts`:

```typescript
import cron from 'node-cron';
import { platformPrisma } from '../../config/database';
import { logger } from '../../config/logger';
import { notificationService } from '../../core/notifications/notification.service';
import { DateTime } from 'luxon';

class AttendanceCronService {
  /**
   * A5: Auto-mark absent after N consecutive days without punch.
   * Runs daily at 2:00 AM.
   */
  async processAutoAbsent() {
    const companies = await platformPrisma.attendanceRule.findMany({
      where: { autoAbsentAfterDays: { gt: 0 } },
      select: { companyId: true, autoAbsentAfterDays: true },
    });

    for (const rule of companies) {
      const cutoffDate = DateTime.now().minus({ days: rule.autoAbsentAfterDays }).toJSDate();

      // Find active employees with no attendance since cutoff
      const employees = await platformPrisma.employee.findMany({
        where: {
          companyId: rule.companyId,
          status: 'ACTIVE',
          attendanceRecords: {
            none: { date: { gte: cutoffDate } },
          },
        },
        select: { id: true, companyId: true, shiftId: true },
      });

      for (const emp of employees) {
        // Create ABSENT records for each missing day
        const today = DateTime.now().startOf('day');
        let day = DateTime.fromJSDate(cutoffDate).startOf('day');

        while (day < today) {
          const existing = await platformPrisma.attendanceRecord.findFirst({
            where: { employeeId: emp.id, date: day.toJSDate() },
          });

          if (!existing) {
            await platformPrisma.attendanceRecord.create({
              data: {
                employeeId: emp.id,
                companyId: emp.companyId,
                shiftId: emp.shiftId,
                date: day.toJSDate(),
                status: 'ABSENT',
                source: 'SYSTEM',
                finalStatusReason: `Auto-absent: no punch for ${rule.autoAbsentAfterDays}+ days`,
              },
            });
          }
          day = day.plus({ days: 1 });
        }
      }

      logger.info(`Auto-absent processed for company ${rule.companyId}: ${employees.length} employees`);
    }
  }

  /**
   * A7: Missing punch alert — notify employees with incomplete punches.
   * Runs daily at 10:00 PM (end of typical business day).
   */
  async processMissingPunchAlerts() {
    const companies = await platformPrisma.attendanceRule.findMany({
      where: { missingPunchAlert: true },
      select: { companyId: true },
    });

    const today = DateTime.now().startOf('day').toJSDate();

    for (const rule of companies) {
      const incompleteRecords = await platformPrisma.attendanceRecord.findMany({
        where: {
          companyId: rule.companyId,
          date: today,
          punchIn: { not: null },
          punchOut: null,
          status: { not: 'ON_LEAVE' },
        },
        select: { employeeId: true, date: true },
      });

      for (const record of incompleteRecords) {
        await notificationService.dispatch({
          companyId: rule.companyId,
          triggerEvent: 'MISSING_PUNCH_ALERT',
          entityType: 'AttendanceRecord',
          entityId: record.employeeId,
          explicitRecipients: [record.employeeId],
          tokens: {
            employee_name: '',
            date: record.date.toISOString().split('T')[0],
          },
          priority: 'MEDIUM',
          type: 'ATTENDANCE',
          actionUrl: '/company/hr/my-attendance',
        }).catch((err: any) => logger.warn('Failed to dispatch missing punch alert', err));
      }

      if (incompleteRecords.length > 0) {
        logger.info(`Missing punch alerts sent for company ${rule.companyId}: ${incompleteRecords.length} employees`);
      }
    }
  }

  startAll() {
    // A5: Auto-absent — daily at 2:00 AM
    cron.schedule('0 2 * * *', () => {
      this.processAutoAbsent().catch((err) => logger.error('Auto-absent cron failed', err));
    });

    // A7: Missing punch alert — daily at 10:00 PM
    cron.schedule('0 22 * * *', () => {
      this.processMissingPunchAlerts().catch((err) => logger.error('Missing punch alert cron failed', err));
    });

    logger.info('Attendance cron jobs started (auto-absent@2AM, missing-punch@10PM)');
  }
}

export const attendanceCronService = new AttendanceCronService();
```

- [ ] **Step 3: Register in server.ts**

In `avy-erp-backend/src/app/server.ts`, after the existing cron registrations (around line 59), add:

```typescript
import { attendanceCronService } from '../shared/jobs/attendance-cron.service';

// In the startup section:
attendanceCronService.startAll();
```

- [ ] **Step 4: Commit**

```bash
cd /Users/chetan/Documents/Avyren-Technologies/Products/Mobile-ERP/avy-erp-backend
git add src/shared/jobs/attendance-cron.service.ts src/app/server.ts src/shared/constants/ src/core/notifications/
git commit -m "feat(attendance): add auto-absent and missing-punch cron jobs"
```

---

## Task 7: Frontend — Geofence Mode Config

**Files:**
- Modify: Web attendance rules config screen
- Modify: Mobile attendance rules config screen

- [ ] **Step 1: Find and update web attendance rules screen**

Search for the attendance rules configuration screen in `web-system-app/src/features/company-admin/hr/`. It should have fields for `selfieRequired`, `gpsRequired`, etc. Add a new dropdown after `gpsRequired`:

- Label: "Geofence Enforcement"
- Options: `OFF` (default) | `WARN` (Allow + Notify Manager) | `STRICT` (Block Check-in)
- Field name: `geofenceEnforcementMode`
- Help text: "Controls whether employees are blocked from checking in outside the geofence area"

- [ ] **Step 2: Find and update mobile attendance rules screen**

Same change in `mobile-app/src/features/company-admin/hr/` attendance rules screen. Use a ChipSelector or Picker component matching existing patterns.

- [ ] **Step 3: Update backend validators**

In `avy-erp-backend/src/modules/hr/attendance/attendance.validators.ts`, add `geofenceEnforcementMode` to the update schema:

```typescript
geofenceEnforcementMode: z.enum(['OFF', 'WARN', 'STRICT']).optional(),
```

- [ ] **Step 4: Commit all frontend + validator changes**

```bash
cd /Users/chetan/Documents/Avyren-Technologies/Products/Mobile-ERP
git add avy-erp-backend/src/modules/hr/attendance/attendance.validators.ts
git add web-system-app/ mobile-app/
git commit -m "feat(ui): add geofence enforcement mode to attendance rules config"
```

---

## Task 8: Type Check & Lint

- [ ] **Step 1: Backend**
```bash
cd avy-erp-backend && pnpm build
```

- [ ] **Step 2: Mobile**
```bash
cd mobile-app && pnpm type-check
```

- [ ] **Step 3: Web**
```bash
cd web-system-app && pnpm build
```

- [ ] **Step 4: Fix any errors and commit**
