# Admin Attendance Screen Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a dual-purpose attendance marking screen (Kiosk + Admin mode) with employee search, enforced/overridable shift rules, and bulk check-in support.

**Architecture:** New `attendance:mark` permission module + 4 backend endpoints under `/hr/attendance/admin/` + web and mobile screens that detect mode from user permissions. Kiosk mode enforces shift/geofence rules; admin mode (`hr:create`) allows full override and bulk operations.

**Tech Stack:** Express, Zod, Prisma, React, React Query, Tailwind, React Native, Expo Router

**Spec:** `docs/superpowers/specs/2026-04-07-admin-attendance-screen-design.md`

---

## File Structure

### Backend (avy-erp-backend)

| Action | File | Responsibility |
|--------|------|----------------|
| Modify | `src/shared/constants/permissions.ts` | Add `attendance` permission module |
| Modify | `src/shared/constants/navigation-manifest.ts` | Add nav entry for Admin Attendance |
| Create | `src/modules/hr/attendance/admin-attendance.validators.ts` | Zod schemas for admin mark endpoints |
| Create | `src/modules/hr/attendance/admin-attendance.service.ts` | Business logic: employee status, mark, bulk mark |
| Create | `src/modules/hr/attendance/admin-attendance.controller.ts` | API handlers |
| Create | `src/modules/hr/attendance/admin-attendance.routes.ts` | Route definitions |
| Modify | `src/modules/hr/attendance/attendance.routes.ts` | Mount admin-attendance sub-router |

### Web App (web-system-app)

| Action | File | Responsibility |
|--------|------|----------------|
| Create | `src/lib/api/admin-attendance.ts` | API client functions |
| Create | `src/features/company-admin/hr/AdminAttendanceScreen.tsx` | Main screen component |
| Modify | `src/App.tsx` | Add route for admin-attendance |

### Mobile App (mobile-app)

| Action | File | Responsibility |
|--------|------|----------------|
| Create | `src/lib/api/admin-attendance.ts` | API client functions |
| Create | `src/features/company-admin/hr/admin-attendance-screen.tsx` | Main screen component |
| Create | `src/app/(app)/company/hr/admin-attendance.tsx` | Route file |

---

### Task 1: Add Permission Module & Navigation Manifest Entry

**Files:**
- Modify: `avy-erp-backend/src/shared/constants/permissions.ts`
- Modify: `avy-erp-backend/src/shared/constants/navigation-manifest.ts`

- [ ] **Step 1: Add `attendance` permission module to `PERMISSION_MODULES`**

In `avy-erp-backend/src/shared/constants/permissions.ts`, add after the `ess` module (around line 186):

```typescript
  attendance: {
    label: 'Attendance Marking',
    actions: ['mark'],
  },
```

- [ ] **Step 2: Add `attendance` to the HR module suppression map**

In `MODULE_TO_PERMISSION_MAP` (line 31), add `'attendance'` to the `hr` array:

```typescript
'hr': ['hr', 'ess', 'recruitment', 'recruitment-offer', 'training', 'training-evaluation', 'analytics', 'attendance'],
```

This ensures `attendance:mark` permission is only available when the HR module is subscribed.

- [ ] **Step 3: Add navigation manifest entry**

In `avy-erp-backend/src/shared/constants/navigation-manifest.ts`, add to the Attendance group (after the last attendance entry, around sortOrder 516):

```typescript
{ id: 'hr-att-admin', label: 'Mark Attendance', icon: 'user-check', requiredPerm: 'attendance:mark', path: '/app/company/hr/admin-attendance', module: 'hr', group: 'Attendance', roleScope: 'company', sortOrder: 509 },
```

Using sortOrder 509 places it before Attendance Dashboard (510) since it's a primary action.

- [ ] **Step 4: Verify build**

```bash
cd avy-erp-backend && pnpm build
```

- [ ] **Step 5: Commit**

```bash
git add src/shared/constants/permissions.ts src/shared/constants/navigation-manifest.ts
git commit -m "feat: add attendance:mark permission and navigation manifest entry"
```

---

### Task 2: Backend Validators

**Files:**
- Create: `avy-erp-backend/src/modules/hr/attendance/admin-attendance.validators.ts`

- [ ] **Step 1: Create validators file**

Create `avy-erp-backend/src/modules/hr/attendance/admin-attendance.validators.ts`:

```typescript
import { z } from 'zod';

export const adminMarkSchema = z.object({
  employeeId: z.string().min(1, 'Employee ID is required'),
  action: z.enum(['CHECK_IN', 'CHECK_OUT'], {
    errorMap: () => ({ message: 'Action must be CHECK_IN or CHECK_OUT' }),
  }),
  latitude: z.number().optional(),
  longitude: z.number().optional(),
  photoUrl: z.string().optional(),
  remarks: z.string().optional(),
  skipValidation: z.boolean().optional(),
});

export const adminBulkMarkSchema = z.object({
  employeeIds: z.array(z.string().min(1)).min(1, 'At least one employee is required').max(50, 'Maximum 50 employees per bulk operation'),
  action: z.enum(['CHECK_IN', 'CHECK_OUT'], {
    errorMap: () => ({ message: 'Action must be CHECK_IN or CHECK_OUT' }),
  }),
  remarks: z.string().min(1, 'Remarks are required for bulk operations'),
});

export const todayLogSchema = z.object({
  page: z.coerce.number().min(1).default(1),
  limit: z.coerce.number().min(1).max(100).default(25),
  search: z.string().optional(),
});
```

- [ ] **Step 2: Commit**

```bash
git add src/modules/hr/attendance/admin-attendance.validators.ts
git commit -m "feat: add admin attendance Zod validators"
```

---

### Task 3: Backend Service

**Files:**
- Create: `avy-erp-backend/src/modules/hr/attendance/admin-attendance.service.ts`

- [ ] **Step 1: Create service file**

Create `avy-erp-backend/src/modules/hr/attendance/admin-attendance.service.ts`:

```typescript
import { platformPrisma } from '../../../config/database';
import { ApiError } from '../../../shared/errors';
import { logger } from '../../../config/logger';
import { getCachedAttendanceRules, getCachedCompanySettings } from '../../../shared/utils/config-cache';
import { resolvePolicy, type EvaluationContext } from '../../../shared/services/policy-resolver.service';
import { resolveAttendanceStatus } from '../../../shared/services/attendance-status-resolver.service';
import { nowInCompanyTimezone } from '../../../shared/utils/timezone';

class AdminAttendanceService {
  /**
   * Get employee details + today's attendance + shift + policy + location + geofences.
   */
  async getEmployeeStatus(companyId: string, employeeId: string) {
    const companySettings = await getCachedCompanySettings(companyId);
    const companyTimezone = companySettings.timezone ?? 'Asia/Kolkata';
    const nowCT = nowInCompanyTimezone(companyTimezone);
    const today = new Date(nowCT.toFormat('yyyy-MM-dd') + 'T00:00:00.000Z');

    const employee = await platformPrisma.employee.findUnique({
      where: { id: employeeId, companyId },
      select: {
        id: true,
        firstName: true,
        lastName: true,
        employeeCode: true,
        profilePhotoUrl: true,
        shiftId: true,
        locationId: true,
        geofenceId: true,
        department: { select: { id: true, name: true } },
        designation: { select: { id: true, name: true } },
      },
    });

    if (!employee) {
      throw ApiError.notFound('Employee not found');
    }

    // Today's attendance record
    let todayRecord = await platformPrisma.attendanceRecord.findUnique({
      where: { employeeId_date: { employeeId, date: today } },
      select: {
        id: true,
        status: true,
        punchIn: true,
        punchOut: true,
        workedHours: true,
        geoStatus: true,
        source: true,
        remarks: true,
        isLate: true,
        lateMinutes: true,
      },
    });

    // Cross-day check: if no record today, check if yesterday's is still open
    if (!todayRecord || !todayRecord.punchIn) {
      const yesterday = new Date(nowCT.minus({ days: 1 }).toFormat('yyyy-MM-dd') + 'T00:00:00.000Z');
      const yesterdayRecord = await platformPrisma.attendanceRecord.findUnique({
        where: { employeeId_date: { employeeId, date: yesterday } },
        select: {
          id: true, status: true, punchIn: true, punchOut: true,
          workedHours: true, geoStatus: true, source: true, remarks: true,
          isLate: true, lateMinutes: true,
        },
      });
      if (yesterdayRecord?.punchIn && !yesterdayRecord.punchOut) {
        todayRecord = yesterdayRecord;
      }
    }

    // Shift info
    let shift = null;
    if (employee.shiftId) {
      shift = await platformPrisma.companyShift.findUnique({
        where: { id: employee.shiftId },
        select: {
          id: true, name: true, startTime: true, endTime: true,
          isCrossDay: true,
          breaks: { select: { id: true, name: true, startTime: true, duration: true, type: true, isPaid: true } },
        },
      });
    }

    // Resolved policy
    let resolvedPolicy = null;
    try {
      const policyResult = await resolvePolicy(companyId, {
        employeeId,
        shiftId: employee.shiftId,
        locationId: employee.locationId,
        date: today,
        isHoliday: false,
        isWeekOff: false,
      });
      resolvedPolicy = policyResult.policy;
    } catch {
      // Non-fatal
    }

    // Location + geofences
    let location = null;
    if (employee.locationId) {
      location = await platformPrisma.location.findUnique({
        where: { id: employee.locationId },
        select: {
          id: true, name: true, geoEnabled: true,
          geofences: { where: { isActive: true }, select: { id: true, name: true, lat: true, lng: true, radius: true, isDefault: true } },
        },
      });
    }

    // Assigned geofence
    let assignedGeofence = null;
    if (employee.geofenceId) {
      assignedGeofence = await platformPrisma.geofence.findUnique({
        where: { id: employee.geofenceId },
        select: { id: true, name: true, lat: true, lng: true, radius: true, isDefault: true },
      });
    }

    return {
      employee: {
        id: employee.id,
        firstName: employee.firstName,
        lastName: employee.lastName,
        employeeCode: employee.employeeCode,
        profilePhotoUrl: employee.profilePhotoUrl,
        departmentName: employee.department?.name ?? null,
        designationName: employee.designation?.name ?? null,
      },
      todayRecord,
      shift,
      resolvedPolicy,
      location,
      assignedGeofence,
    };
  }

  /**
   * Mark check-in or check-out for a single employee.
   */
  async markAttendance(
    companyId: string,
    data: {
      employeeId: string;
      action: 'CHECK_IN' | 'CHECK_OUT';
      latitude?: number;
      longitude?: number;
      photoUrl?: string;
      remarks?: string;
      skipValidation?: boolean;
    },
    callerHasOverride: boolean,
  ) {
    const canSkip = callerHasOverride && data.skipValidation === true;

    const companySettings = await getCachedCompanySettings(companyId);
    const companyTimezone = companySettings.timezone ?? 'Asia/Kolkata';
    const nowCT = nowInCompanyTimezone(companyTimezone);
    const today = new Date(nowCT.toFormat('yyyy-MM-dd') + 'T00:00:00.000Z');
    const now = new Date();

    // Verify employee
    const employee = await platformPrisma.employee.findUnique({
      where: { id: data.employeeId, companyId },
      select: { id: true, shiftId: true, locationId: true, geofenceId: true, firstName: true, lastName: true },
    });
    if (!employee) throw ApiError.notFound('Employee not found');

    if (data.action === 'CHECK_IN') {
      return this.handleCheckIn(companyId, employee, data, today, now, nowCT, companyTimezone, canSkip);
    } else {
      return this.handleCheckOut(companyId, employee, data, today, now, nowCT, companyTimezone, canSkip);
    }
  }

  private async handleCheckIn(
    companyId: string,
    employee: any,
    data: any,
    today: Date,
    now: Date,
    nowCT: any,
    companyTimezone: string,
    canSkip: boolean,
  ) {
    // Prevent double check-in
    const existing = await platformPrisma.attendanceRecord.findUnique({
      where: { employeeId_date: { employeeId: employee.id, date: today } },
    });
    if (existing?.punchIn) {
      throw ApiError.badRequest('Employee already checked in today');
    }

    // Geofence validation
    let geoStatus = 'NO_LOCATION';
    if (data.latitude != null && data.longitude != null) {
      geoStatus = await this.resolveGeoStatus(
        employee.id, employee.locationId, employee.geofenceId,
        data.latitude, data.longitude,
      );
    }

    // Shift time validation (kiosk mode only)
    if (!canSkip && employee.shiftId) {
      await this.validateShiftWindow(companyId, employee.shiftId, nowCT, companyTimezone);
    }

    // Create record
    const record = await platformPrisma.attendanceRecord.create({
      data: {
        employeeId: employee.id,
        companyId,
        date: today,
        punchIn: now,
        status: 'PRESENT',
        source: 'MANUAL',
        remarks: data.remarks || null,
        shiftId: employee.shiftId || undefined,
        locationId: employee.locationId || undefined,
        checkInLatitude: data.latitude ?? undefined,
        checkInLongitude: data.longitude ?? undefined,
        checkInPhotoUrl: data.photoUrl ?? undefined,
        geoStatus,
      },
    });

    return { record, status: 'CHECKED_IN' as const };
  }

  private async handleCheckOut(
    companyId: string,
    employee: any,
    data: any,
    today: Date,
    now: Date,
    nowCT: any,
    companyTimezone: string,
    canSkip: boolean,
  ) {
    // Find today's record (or yesterday's cross-day record)
    let record = await platformPrisma.attendanceRecord.findUnique({
      where: { employeeId_date: { employeeId: employee.id, date: today } },
    });

    if (!record?.punchIn) {
      const yesterday = new Date(nowCT.minus({ days: 1 }).toFormat('yyyy-MM-dd') + 'T00:00:00.000Z');
      const yesterdayRecord = await platformPrisma.attendanceRecord.findUnique({
        where: { employeeId_date: { employeeId: employee.id, date: yesterday } },
      });
      if (yesterdayRecord?.punchIn && !yesterdayRecord.punchOut) {
        record = yesterdayRecord;
      }
    }

    if (!record?.punchIn) {
      throw ApiError.badRequest('Employee has not checked in today');
    }
    if (record.punchOut) {
      throw ApiError.badRequest('Employee already checked out today');
    }

    // Geofence for checkout
    let geoStatus = record.geoStatus ?? 'NO_LOCATION';
    if (data.latitude != null && data.longitude != null) {
      geoStatus = await this.resolveGeoStatus(
        employee.id, employee.locationId, employee.geofenceId,
        data.latitude, data.longitude,
      );
    }

    // Resolve policy and status
    const rules = await getCachedAttendanceRules(companyId);
    const policyResult = await resolvePolicy(companyId, {
      employeeId: employee.id,
      shiftId: record.shiftId,
      locationId: record.locationId,
      date: record.date,
      isHoliday: false,
      isWeekOff: false,
    });

    let shift = null;
    if (record.shiftId) {
      shift = await platformPrisma.companyShift.findUnique({
        where: { id: record.shiftId },
        select: { startTime: true, endTime: true, isCrossDay: true, name: true },
      });
    }

    const statusResult = resolveAttendanceStatus(
      record.punchIn,
      now,
      shift ? { startTime: shift.startTime, endTime: shift.endTime, isCrossDay: shift.isCrossDay } : null,
      policyResult.policy,
      { employeeId: employee.id, shiftId: record.shiftId, locationId: record.locationId, date: record.date, isHoliday: false, isWeekOff: false },
      rules,
      companyTimezone,
    );

    // Update record
    const updated = await platformPrisma.attendanceRecord.update({
      where: { id: record.id },
      data: {
        punchOut: now,
        status: statusResult.status,
        workedHours: statusResult.workedHours,
        isLate: statusResult.isLate,
        lateMinutes: statusResult.lateMinutes,
        isEarlyExit: statusResult.isEarlyExit,
        earlyMinutes: statusResult.earlyMinutes,
        overtimeHours: statusResult.overtimeHours,
        checkOutLatitude: data.latitude ?? undefined,
        checkOutLongitude: data.longitude ?? undefined,
        checkOutPhotoUrl: data.photoUrl ?? undefined,
        geoStatus,
        remarks: data.remarks ? (record.remarks ? `${record.remarks}; ${data.remarks}` : data.remarks) : record.remarks,
        appliedGracePeriodMinutes: policyResult.policy.gracePeriodMinutes,
        appliedFullDayThresholdHours: policyResult.policy.fullDayThresholdHours,
        appliedHalfDayThresholdHours: policyResult.policy.halfDayThresholdHours,
        appliedBreakDeductionMinutes: policyResult.policy.breakDeductionMinutes,
        appliedLateDeduction: statusResult.appliedLateDeduction,
        appliedEarlyExitDeduction: statusResult.appliedEarlyExitDeduction,
        resolutionTrace: policyResult.trace as any,
        finalStatusReason: statusResult.finalStatusReason,
      },
    });

    return { record: updated, status: 'CHECKED_OUT' as const };
  }

  /**
   * Bulk mark check-in or check-out. Admin only — always skips validation.
   */
  async bulkMark(
    companyId: string,
    data: { employeeIds: string[]; action: 'CHECK_IN' | 'CHECK_OUT'; remarks: string },
  ) {
    const results: Array<{ employeeId: string; employeeName: string; success: boolean; error?: string; record?: any }> = [];

    for (const employeeId of data.employeeIds) {
      try {
        const result = await this.markAttendance(
          companyId,
          { employeeId, action: data.action, remarks: data.remarks, skipValidation: true },
          true, // admin override
        );
        const emp = await platformPrisma.employee.findUnique({
          where: { id: employeeId },
          select: { firstName: true, lastName: true },
        });
        results.push({
          employeeId,
          employeeName: [emp?.firstName, emp?.lastName].filter(Boolean).join(' '),
          success: true,
          record: result.record,
        });
      } catch (err: any) {
        const emp = await platformPrisma.employee.findUnique({
          where: { id: employeeId },
          select: { firstName: true, lastName: true },
        });
        results.push({
          employeeId,
          employeeName: [emp?.firstName, emp?.lastName].filter(Boolean).join(' '),
          success: false,
          error: err.message || 'Unknown error',
        });
      }
    }

    return {
      results,
      summary: {
        total: data.employeeIds.length,
        succeeded: results.filter(r => r.success).length,
        failed: results.filter(r => !r.success).length,
      },
    };
  }

  /**
   * Get today's manually-marked attendance records for the activity log.
   */
  async getTodayLog(companyId: string, options: { page: number; limit: number; search?: string }) {
    const companySettings = await getCachedCompanySettings(companyId);
    const companyTimezone = companySettings.timezone ?? 'Asia/Kolkata';
    const nowCT = nowInCompanyTimezone(companyTimezone);
    const today = new Date(nowCT.toFormat('yyyy-MM-dd') + 'T00:00:00.000Z');
    const offset = (options.page - 1) * options.limit;

    const where: any = {
      companyId,
      date: today,
      source: 'MANUAL',
    };

    if (options.search) {
      where.employee = {
        OR: [
          { firstName: { contains: options.search, mode: 'insensitive' } },
          { lastName: { contains: options.search, mode: 'insensitive' } },
          { employeeCode: { contains: options.search, mode: 'insensitive' } },
        ],
      };
    }

    const [records, total] = await Promise.all([
      platformPrisma.attendanceRecord.findMany({
        where,
        include: {
          employee: { select: { id: true, firstName: true, lastName: true, employeeCode: true } },
        },
        skip: offset,
        take: options.limit,
        orderBy: { updatedAt: 'desc' },
      }),
      platformPrisma.attendanceRecord.count({ where }),
    ]);

    return { records, total, page: options.page, limit: options.limit };
  }

  // ── Private helpers ──

  private async resolveGeoStatus(
    employeeId: string,
    locationId: string | null,
    geofenceId: string | null,
    latitude: number,
    longitude: number,
  ): Promise<string> {
    // 1. Check assigned geofence
    if (geofenceId) {
      const geofence = await platformPrisma.geofence.findUnique({ where: { id: geofenceId } });
      if (geofence?.isActive) {
        const dist = this.calculateDistance(latitude, longitude, geofence.lat, geofence.lng);
        return dist <= geofence.radius ? 'INSIDE_GEOFENCE' : 'OUTSIDE_GEOFENCE';
      }
    }

    // 2. Check location geofences
    if (locationId) {
      const geofences = await platformPrisma.geofence.findMany({
        where: { locationId, isActive: true },
      });
      if (geofences.length > 0) {
        const insideAny = geofences.some(
          gf => this.calculateDistance(latitude, longitude, gf.lat, gf.lng) <= gf.radius,
        );
        return insideAny ? 'INSIDE_GEOFENCE' : 'OUTSIDE_GEOFENCE';
      }

      // 3. Legacy location geo fields
      const location = await platformPrisma.location.findUnique({ where: { id: locationId } });
      if (location?.geoEnabled && location.geoLat && location.geoLng) {
        const dist = this.calculateDistance(latitude, longitude, parseFloat(location.geoLat), parseFloat(location.geoLng));
        return dist <= location.geoRadius ? 'INSIDE_GEOFENCE' : 'OUTSIDE_GEOFENCE';
      }
    }

    return 'NO_LOCATION';
  }

  private async validateShiftWindow(companyId: string, shiftId: string, nowCT: any, companyTimezone: string) {
    const shift = await platformPrisma.companyShift.findUnique({
      where: { id: shiftId },
      select: { startTime: true, endTime: true, name: true, isCrossDay: true, gracePeriodMinutes: true, maxLateCheckInMinutes: true },
    });
    if (!shift) return; // No shift = no validation

    const rules = await getCachedAttendanceRules(companyId);
    const maxLateCheckIn = shift.maxLateCheckInMinutes ?? rules.maxLateCheckInMinutes ?? 240;

    const [shiftHour = 0, shiftMin = 0] = (shift.startTime || '00:00').split(':').map(Number);
    const nowMinutes = nowCT.hour * 60 + nowCT.minute;
    const shiftStartMinutes = (shiftHour ?? 0) * 60 + (shiftMin ?? 0);

    const earlyWindowMinutes = 60;

    if (!shift.isCrossDay) {
      const [endHour = 0, endMin = 0] = (shift.endTime || '23:59').split(':').map(Number);
      const shiftEndMinutes = (endHour ?? 0) * 60 + (endMin ?? 0);
      const shiftDuration = shiftEndMinutes - shiftStartMinutes;
      const lateWindow = Math.min(maxLateCheckIn, shiftDuration);
      const windowStart = shiftStartMinutes - earlyWindowMinutes;
      const windowEnd = shiftStartMinutes + lateWindow;

      if (nowMinutes < windowStart || nowMinutes > windowEnd) {
        throw ApiError.badRequest(
          `Check-in not allowed. ${shift.name} window: ${shift.startTime} (${earlyWindowMinutes}min early to ${lateWindow}min late)`,
        );
      }
    }
    // Cross-day shifts: more lenient — allow check-in anytime
    // (complex midnight-wrapping logic handled by ESS; admin screen is simpler)
  }

  private calculateDistance(lat1: number, lng1: number, lat2: number, lng2: number): number {
    const R = 6371000; // Earth radius in meters
    const dLat = (lat2 - lat1) * Math.PI / 180;
    const dLng = (lng2 - lng1) * Math.PI / 180;
    const a = Math.sin(dLat / 2) * Math.sin(dLat / 2) +
      Math.cos(lat1 * Math.PI / 180) * Math.cos(lat2 * Math.PI / 180) *
      Math.sin(dLng / 2) * Math.sin(dLng / 2);
    const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
    return R * c;
  }
}

export const adminAttendanceService = new AdminAttendanceService();
```

- [ ] **Step 2: Verify build**

```bash
cd avy-erp-backend && pnpm build
```

- [ ] **Step 3: Commit**

```bash
git add src/modules/hr/attendance/admin-attendance.service.ts
git commit -m "feat: add admin attendance service with mark, bulk, and validation logic"
```

---

### Task 4: Backend Controller & Routes

**Files:**
- Create: `avy-erp-backend/src/modules/hr/attendance/admin-attendance.controller.ts`
- Create: `avy-erp-backend/src/modules/hr/attendance/admin-attendance.routes.ts`
- Modify: `avy-erp-backend/src/modules/hr/attendance/attendance.routes.ts`

- [ ] **Step 1: Create controller**

Create `avy-erp-backend/src/modules/hr/attendance/admin-attendance.controller.ts`:

```typescript
import { Request, Response } from 'express';
import { asyncHandler } from '../../../middleware/error.middleware';
import { ApiError } from '../../../shared/errors';
import { createSuccessResponse, createPaginatedResponse } from '../../../shared/utils';
import { adminAttendanceService } from './admin-attendance.service';
import { adminMarkSchema, adminBulkMarkSchema, todayLogSchema } from './admin-attendance.validators';
import { checkPermission } from '../../../shared/constants/permissions';

class AdminAttendanceController {
  getEmployeeStatus = asyncHandler(async (req: Request, res: Response) => {
    const companyId = req.user?.companyId;
    if (!companyId) throw ApiError.badRequest('Company ID is required');

    const { employeeId } = req.params;
    if (!employeeId) throw ApiError.badRequest('Employee ID is required');

    const result = await adminAttendanceService.getEmployeeStatus(companyId, employeeId);
    res.json(createSuccessResponse(result, 'Employee status retrieved'));
  });

  markAttendance = asyncHandler(async (req: Request, res: Response) => {
    const companyId = req.user?.companyId;
    if (!companyId) throw ApiError.badRequest('Company ID is required');

    const parsed = adminMarkSchema.safeParse(req.body);
    if (!parsed.success) {
      throw ApiError.badRequest(parsed.error.errors.map(e => e.message).join(', '));
    }

    // Check if caller has admin override privileges
    const permissions = req.user?.permissions ?? [];
    const callerHasOverride = checkPermission(permissions, 'hr:create');

    // Require remarks for admin mode
    if (callerHasOverride && parsed.data.skipValidation && !parsed.data.remarks) {
      throw ApiError.badRequest('Remarks are required when using admin override');
    }

    const result = await adminAttendanceService.markAttendance(companyId, parsed.data, callerHasOverride);
    res.status(201).json(createSuccessResponse(result, `Employee ${result.status === 'CHECKED_IN' ? 'checked in' : 'checked out'} successfully`));
  });

  bulkMark = asyncHandler(async (req: Request, res: Response) => {
    const companyId = req.user?.companyId;
    if (!companyId) throw ApiError.badRequest('Company ID is required');

    const parsed = adminBulkMarkSchema.safeParse(req.body);
    if (!parsed.success) {
      throw ApiError.badRequest(parsed.error.errors.map(e => e.message).join(', '));
    }

    const result = await adminAttendanceService.bulkMark(companyId, parsed.data);
    res.json(createSuccessResponse(result, `Bulk operation complete: ${result.summary.succeeded}/${result.summary.total} succeeded`));
  });

  getTodayLog = asyncHandler(async (req: Request, res: Response) => {
    const companyId = req.user?.companyId;
    if (!companyId) throw ApiError.badRequest('Company ID is required');

    const parsed = todayLogSchema.safeParse(req.query);
    if (!parsed.success) {
      throw ApiError.badRequest(parsed.error.errors.map(e => e.message).join(', '));
    }

    const result = await adminAttendanceService.getTodayLog(companyId, parsed.data);
    res.json(createPaginatedResponse(result.records, result.page, result.limit, result.total, 'Today log retrieved'));
  });
}

export const adminAttendanceController = new AdminAttendanceController();
```

- [ ] **Step 2: Create routes**

Create `avy-erp-backend/src/modules/hr/attendance/admin-attendance.routes.ts`:

```typescript
import { Router } from 'express';
import { requirePermissions } from '../../../middleware/auth.middleware';
import { adminAttendanceController } from './admin-attendance.controller';

const router = Router();

router.get('/employee/:employeeId/status', requirePermissions(['attendance:mark']), adminAttendanceController.getEmployeeStatus);
router.post('/mark', requirePermissions(['attendance:mark']), adminAttendanceController.markAttendance);
router.post('/mark/bulk', requirePermissions(['hr:create']), adminAttendanceController.bulkMark);
router.get('/today-log', requirePermissions(['attendance:mark']), adminAttendanceController.getTodayLog);

export { router as adminAttendanceRoutes };
```

- [ ] **Step 3: Mount in attendance routes**

In `avy-erp-backend/src/modules/hr/attendance/attendance.routes.ts`, add import at top:

```typescript
import { adminAttendanceRoutes } from './admin-attendance.routes';
```

And mount BEFORE any parameterized routes (before `router.get('/:id', ...)`):

```typescript
router.use('/admin', adminAttendanceRoutes);
```

- [ ] **Step 4: Verify build**

```bash
cd avy-erp-backend && pnpm build
```

- [ ] **Step 5: Test endpoints**

```bash
# Should return 401 (unauthorized) confirming routes are mounted
curl -s http://localhost:3000/api/v1/hr/attendance/admin/today-log | jq .
```

- [ ] **Step 6: Commit**

```bash
git add src/modules/hr/attendance/admin-attendance.controller.ts src/modules/hr/attendance/admin-attendance.routes.ts src/modules/hr/attendance/attendance.routes.ts
git commit -m "feat: add admin attendance controller, routes, and mount in attendance router"
```

---

### Task 5: Web App — API Client & Route Setup

**Files:**
- Create: `web-system-app/src/lib/api/admin-attendance.ts`
- Modify: `web-system-app/src/App.tsx`

- [ ] **Step 1: Create API client**

Create `web-system-app/src/lib/api/admin-attendance.ts`:

```typescript
import { client } from './client';

export const adminAttendanceApi = {
  getEmployeeStatus: (employeeId: string) =>
    client.get(`/hr/attendance/admin/employee/${employeeId}/status`).then(r => r.data),

  mark: (data: {
    employeeId: string;
    action: 'CHECK_IN' | 'CHECK_OUT';
    latitude?: number;
    longitude?: number;
    remarks?: string;
    skipValidation?: boolean;
  }) => client.post('/hr/attendance/admin/mark', data).then(r => r.data),

  bulkMark: (data: {
    employeeIds: string[];
    action: 'CHECK_IN' | 'CHECK_OUT';
    remarks: string;
  }) => client.post('/hr/attendance/admin/mark/bulk', data).then(r => r.data),

  getTodayLog: (params?: { page?: number; limit?: number; search?: string }) =>
    client.get('/hr/attendance/admin/today-log', { params }).then(r => r.data),
};

export const adminAttendanceKeys = {
  all: ['admin-attendance'] as const,
  employeeStatus: (id: string) => [...adminAttendanceKeys.all, 'employee-status', id] as const,
  todayLog: (params?: Record<string, unknown>) => [...adminAttendanceKeys.all, 'today-log', params] as const,
};
```

- [ ] **Step 2: Add route in App.tsx**

In `web-system-app/src/App.tsx`, add lazy import near other attendance imports:

```typescript
const AdminAttendanceScreen = lazyNamed(() => import("./features/company-admin/hr/AdminAttendanceScreen"), "AdminAttendanceScreen");
```

Add route near other attendance routes:

```typescript
<Route path="company/hr/admin-attendance" element={<RequirePermission permission="attendance:mark"><AdminAttendanceScreen /></RequirePermission>} />
```

- [ ] **Step 3: Commit**

```bash
git add src/lib/api/admin-attendance.ts src/App.tsx
git commit -m "feat(web): add admin attendance API client and route"
```

---

### Task 6: Web App — AdminAttendanceScreen

**Files:**
- Create: `web-system-app/src/features/company-admin/hr/AdminAttendanceScreen.tsx`

- [ ] **Step 1: Create the screen**

This is a large screen component. Read the existing `ShiftCheckInScreen.tsx` for styling patterns and `AttendanceDashboardScreen.tsx` for table patterns. The screen must:

**Layout:**
1. **Header**: "Mark Attendance" title with mode badge (Kiosk / Admin). In admin mode, a "Bulk Mode" toggle button.
2. **Employee Search**: Searchable dropdown using `GET /hr/employees` with debounced search. Shows employee code + name in results.
3. **Employee Card** (shown after selection): Photo (via `useFileUrl`), name, code, department, designation, shift name + times (via `useCompanyFormatter().shiftTime()`), location + geofence info, today's status badge, resolved policy summary (grace period, GPS required).
4. **Action Area**:
   - Remarks input (required in admin mode, optional in kiosk)
   - "Check In" / "Check Out" button (contextual based on todayRecord status)
   - In kiosk mode: after success, show green checkmark animation, auto-reset after 3 seconds
5. **Bulk Mode** (admin only, toggled): Shows a list of employees with checkboxes, department/location filter dropdowns, select all checkbox, action dropdown (Check In / Check Out), remarks field, "Execute" button. Shows results modal after execution.
6. **Today's Activity Log**: Table at bottom showing manually marked records today. Columns: Employee Code, Name, Action (IN/OUT), Time, Remarks. Uses `GET /hr/attendance/admin/today-log`.

**Mode detection:**
```typescript
const isAdminMode = useCanPerform('hr:create');
```

**Key hooks to use:**
- `useCanPerform('hr:create')` for mode detection
- `useCompanyFormatter()` for time/date formatting
- `useFileUrl()` for employee photo
- `useQuery` with `adminAttendanceKeys.employeeStatus(id)` for employee card
- `useMutation` with `adminAttendanceApi.mark()` for single mark
- `useMutation` with `adminAttendanceApi.bulkMark()` for bulk
- `useQuery` with `adminAttendanceKeys.todayLog()` for activity log

**Styling:** Follow existing Tailwind patterns — use `primary-*` for headers, `success-*`/`danger-*`/`warning-*` for status badges, `neutral-*` for secondary text. Use `cn()` from `@/lib/utils` for conditional classes.

- [ ] **Step 2: Verify build**

```bash
cd web-system-app && pnpm build
```

- [ ] **Step 3: Commit**

```bash
git add src/features/company-admin/hr/AdminAttendanceScreen.tsx
git commit -m "feat(web): add AdminAttendanceScreen with kiosk and admin modes"
```

---

### Task 7: Mobile App — API Client, Route & Screen

**Files:**
- Create: `mobile-app/src/lib/api/admin-attendance.ts`
- Create: `mobile-app/src/features/company-admin/hr/admin-attendance-screen.tsx`
- Create: `mobile-app/src/app/(app)/company/hr/admin-attendance.tsx`

- [ ] **Step 1: Create mobile API client**

Create `mobile-app/src/lib/api/admin-attendance.ts`:

```typescript
import { client } from '@/lib/api/client';

export const adminAttendanceApi = {
  getEmployeeStatus: (employeeId: string) =>
    client.get(`/hr/attendance/admin/employee/${employeeId}/status`),

  mark: (data: {
    employeeId: string;
    action: 'CHECK_IN' | 'CHECK_OUT';
    latitude?: number;
    longitude?: number;
    remarks?: string;
    skipValidation?: boolean;
  }) => client.post('/hr/attendance/admin/mark', data),

  bulkMark: (data: {
    employeeIds: string[];
    action: 'CHECK_IN' | 'CHECK_OUT';
    remarks: string;
  }) => client.post('/hr/attendance/admin/mark/bulk', data),

  getTodayLog: (params?: { page?: number; limit?: number; search?: string }) =>
    client.get('/hr/attendance/admin/today-log', { params }),
};

export const adminAttendanceKeys = {
  all: ['admin-attendance'] as const,
  employeeStatus: (id: string) => [...adminAttendanceKeys.all, 'employee-status', id] as const,
  todayLog: (params?: Record<string, unknown>) => [...adminAttendanceKeys.all, 'today-log', params] as const,
};
```

Note: Mobile API client auto-unwraps `response.data`, so no `.then(r => r.data)`.

- [ ] **Step 2: Create route file**

Create `mobile-app/src/app/(app)/company/hr/admin-attendance.tsx`:

```typescript
export { AdminAttendanceScreen as default } from '@/features/company-admin/hr/admin-attendance-screen';
```

- [ ] **Step 3: Create mobile screen**

Create `mobile-app/src/features/company-admin/hr/admin-attendance-screen.tsx`.

Follow the patterns from `shift-check-in-screen.tsx` for styling:
- `LinearGradient` header with `colors.gradient.*`
- `useSafeAreaInsets()` for padding
- `font-inter` on all `<Text>` components
- `StyleSheet.create()` for layouts
- `useCompanyFormatter()` for time formatting
- `useFileUrl()` for employee photo
- NEVER use `Alert.alert()` — use inline feedback (success/error messages in UI)

**Layout (same as web, adapted for mobile):**
1. Gradient header with title + mode badge
2. Employee search (text input with dropdown results)
3. Employee card (compact, photo + details)
4. Action buttons (large, prominent for kiosk use)
5. Kiosk: auto-reset with success animation after 3 seconds
6. Admin: bulk mode toggle in header, shows employee list with checkboxes
7. Today's log as FlatList at bottom

**Mode detection:**
```typescript
import { useCanPerform } from '@/hooks/use-can-perform';
const isAdminMode = useCanPerform('hr:create');
```

- [ ] **Step 4: Verify type check**

```bash
cd mobile-app && pnpm type-check
```

- [ ] **Step 5: Commit**

```bash
git add src/lib/api/admin-attendance.ts src/features/company-admin/hr/admin-attendance-screen.tsx src/app/\(app\)/company/hr/admin-attendance.tsx
git commit -m "feat(mobile): add AdminAttendanceScreen with kiosk and admin modes"
```

---

## Self-Review

### Spec Coverage

| Spec Section | Task(s) |
|-------------|---------|
| Permission module (`attendance:mark`) | Task 1 |
| Navigation manifest entry | Task 1 |
| `GET /hr/attendance/admin/employee/:id/status` | Tasks 3, 4 |
| `POST /hr/attendance/admin/mark` | Tasks 2, 3, 4 |
| `POST /hr/attendance/admin/mark/bulk` | Tasks 2, 3, 4 |
| `GET /hr/attendance/admin/today-log` | Tasks 2, 3, 4 |
| Kiosk mode (enforced shift/geofence rules) | Task 3 (validateShiftWindow, resolveGeoStatus) |
| Admin mode (skipValidation, required remarks) | Tasks 3, 4 |
| Bulk check-in (admin only) | Tasks 3, 4, 6, 7 |
| Web screen | Tasks 5, 6 |
| Mobile screen | Task 7 |
| Employee search + compact card | Tasks 6, 7 |
| Auto-reset in kiosk mode | Tasks 6, 7 |
| Today's activity log | Tasks 3, 4, 6, 7 |
| Mode detection via permissions | Tasks 6, 7 |

### Placeholder Scan

No TBD/TODO found. All code blocks are complete.

### Type Consistency

- `adminMarkSchema` fields match `markAttendance` service method params
- `adminBulkMarkSchema` fields match `bulkMark` service method params
- Web and mobile API clients have identical method names and endpoint paths
- `adminAttendanceKeys` query key factory identical in web and mobile
- `checkPermission` import in controller matches existing usage pattern
