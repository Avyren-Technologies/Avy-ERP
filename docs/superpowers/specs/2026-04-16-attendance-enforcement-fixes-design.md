# Sub-project 1: Attendance Enforcement Fixes — Design Spec

## Goal

Fix 8 gaps where attendance configuration exists but is not enforced: geofence enforcement with configurable modes, selfie/GPS validation in the ESS check-in/check-out path, integration of the existing punch validator, and activation of dead configuration fields.

## Verified Gaps

| # | Gap | Current State |
|---|-----|---------------|
| A1 | Geofence not enforced in ESS check-in | `geoStatus` computed but check-in never blocked |
| A2 | No geofence enforcement toggle | No `enforceGeofence` field in any model |
| A3 | Checkout selfie not validated | ESS check-out accepts missing selfie even when policy requires it |
| A4 | GPS not validated in ESS controller | `gpsRequired` from policy not checked in ESS check-in/check-out |
| A5 | `autoAbsentAfterDays` dead field | Field exists, zero business logic uses it |
| A6 | `regularizationWindowDays` bypassed in ESS | Enforced in `attendance.service.createOverride()` but NOT in ESS regularization path |
| A7 | `missingPunchAlert` not implemented | Toggle exists, no notification fires |
| A8 | Punch validator implemented but never called | `punch-validator.service.ts` fully coded with tests, but never invoked from check-in/check-out flow |

---

## Schema Changes

### File: `prisma/modules/hrms/attendance.prisma`

**New enum:**
```prisma
enum GeofenceEnforcementMode {
  OFF        // Current behavior — record geoStatus silently
  WARN       // Allow check-in, show warning, notify manager
  STRICT     // Block check-in if outside geofence
}
```

**Add to AttendanceRule model** (after `gpsRequired` field, line ~145):
```prisma
  geofenceEnforcementMode GeofenceEnforcementMode @default(OFF)
```

No other schema changes needed — all other fields already exist.

---

## Fix A1 + A2: Geofence Enforcement in ESS Check-In/Check-Out

### Current Flow (ess.controller.ts checkIn, line 1182)
1. Parse request body
2. Resolve employee + shift + policy
3. Compute geoStatus from coordinates
4. Create attendance record (geoStatus stored but never checked)

### Fixed Flow
After computing geoStatus (step 3), add enforcement:

```
if (geofenceEnforcementMode !== 'OFF' && geoStatus === 'OUTSIDE_GEOFENCE') {
  if (geofenceEnforcementMode === 'STRICT') {
    throw ApiError.forbidden('You must be inside the geofence area to check in');
  }
  if (geofenceEnforcementMode === 'WARN') {
    // Allow check-in but flag it
    // Add geofenceWarning: true to response
    // Dispatch notification to manager (fire-and-forget)
  }
}
```

### Where to Get geofenceEnforcementMode
The ESS controller already resolves the attendance policy via the policy resolver hierarchy (Location > Shift > AttendanceRule > SystemDefault). Add `geofenceEnforcementMode` to the resolved policy object.

### Apply to Both Check-In and Check-Out
Same validation logic in both `checkIn` (line 1182) and `checkOut` (line 1377) methods.

---

## Fix A3: Checkout Selfie Validation

### Current State
- Check-in: `attendance.service.ts` line 218 validates `policy.selfieRequired` — but only in manual HR path
- ESS check-in (ess.controller.ts): Does NOT validate selfieRequired
- ESS check-out: Does NOT validate selfieRequired

### Fix
In `ess.controller.ts`, after parsing the request body and resolving the policy, add validation in BOTH checkIn and checkOut:

```typescript
if (policy.selfieRequired && !parsed.data.photoUrl) {
  throw ApiError.badRequest('Selfie photo is required by company policy');
}
```

---

## Fix A4: GPS Validation in ESS Controller

### Current State
- `attendance.service.ts` line 221 validates `policy.gpsRequired` — but only in manual HR path
- ESS controller does NOT validate

### Fix
In `ess.controller.ts`, add to BOTH checkIn and checkOut after policy resolution:

```typescript
if (policy.gpsRequired && (parsed.data.latitude == null || parsed.data.longitude == null)) {
  throw ApiError.badRequest('GPS location is required by company policy');
}
```

---

## Fix A5: autoAbsentAfterDays

### Design
This requires a daily batch job (cron) that:
1. Runs once per day (e.g., 2:00 AM company timezone)
2. For each company with `autoAbsentAfterDays > 0`:
   - Find employees who have had no attendance records for N consecutive days
   - Auto-create ABSENT attendance records for each missing day
3. Log results

### Implementation
- New file: `avy-erp-backend/src/shared/jobs/auto-absent.job.ts`
- Register in existing cron/scheduler infrastructure (check if one exists, otherwise use `node-cron`)
- Query: For each active employee, check if `count(attendanceRecords WHERE date >= today - N days) === 0`

---

## Fix A6: regularizationWindowDays in ESS Path

### Current State
- `attendance.service.createOverride()` (line 1166) validates the window
- ESS regularization in `ess.service.ts` creates its own override without calling this validation

### Fix
In the ESS regularization method, add the same window validation before creating the override:

```typescript
const rules = await this.getAttendanceRules(companyId);
const windowDays = rules.regularizationWindowDays ?? 7;
if (windowDays > 0) {
  const recordDate = DateTime.fromJSDate(new Date(data.date)).startOf('day');
  const cutoff = DateTime.now().startOf('day').minus({ days: windowDays });
  if (recordDate < cutoff) {
    throw ApiError.badRequest(`Cannot regularize attendance older than ${windowDays} days`);
  }
}
```

---

## Fix A7: missingPunchAlert

### Design
Integrate with the existing notification system:
1. After daily attendance processing (or end-of-shift), check for employees with incomplete punches (punch-in but no punch-out)
2. If `missingPunchAlert === true`, dispatch a notification to the employee

### Implementation
- Add to the existing attendance batch processing (or as a separate end-of-day job)
- New trigger event: `MISSING_PUNCH_ALERT`
- New notification template with tokens: `employee_name`, `date`, `punch_type` (missing check-in or check-out)
- Dispatch to SELF (the employee)

---

## Fix A8: Integrate Punch Validator

### Current State
`punch-validator.service.ts` at `src/shared/services/punch-validator.service.ts` has:
- `validatePunchSequence(punches, mode, shiftStart, shiftEnd)` — fully implemented for FIRST_LAST, EVERY_PAIR, SHIFT_BASED
- Unit tests passing

### Fix
In the attendance status resolver (`attendance-status-resolver.service.ts`), before calculating worked hours, call the punch validator:

```typescript
import { validatePunchSequence } from '../../../shared/services/punch-validator.service';

// In resolveStatus():
const validatedPunches = validatePunchSequence(
  punches,
  policy.punchMode,
  shiftStart,
  shiftEnd,
);
// Use validatedPunches.effectivePunchIn and effectivePunchOut for worked hours calculation
```

This replaces the current hardcoded FIRST_LAST logic with the mode-aware validator.

---

## Configuration UI

### Web: Attendance Rules Screen
Add `geofenceEnforcementMode` dropdown to the existing attendance rules configuration screen:
- Field label: "Geofence Enforcement"
- Options: Off (default), Warn (allow + notify), Strict (block)
- Place after the existing `gpsRequired` toggle

### Mobile: Same screen
Add the same dropdown.

---

## Files Changed

### Backend
| File | Change |
|------|--------|
| `prisma/modules/hrms/attendance.prisma` | Add `GeofenceEnforcementMode` enum + field on AttendanceRule |
| `src/modules/hr/ess/ess.controller.ts` | Add geofence enforcement, selfie validation, GPS validation to checkIn + checkOut |
| `src/modules/hr/ess/ess.service.ts` | Add regularization window validation |
| `src/shared/services/attendance-status-resolver.service.ts` | Integrate punch validator |
| `src/shared/jobs/auto-absent.job.ts` | **NEW** — daily cron for autoAbsentAfterDays |
| `src/shared/constants/trigger-events.ts` | Add `MISSING_PUNCH_ALERT` event |
| `src/core/notifications/templates/defaults.ts` | Add missing punch template |
| `src/shared/constants/notification-categories.ts` | Add mapping |

### Frontend (both web + mobile)
| File | Change |
|------|--------|
| Attendance Rules config screen | Add `geofenceEnforcementMode` dropdown |
