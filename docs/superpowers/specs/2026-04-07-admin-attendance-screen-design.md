# Admin Attendance Screen — Design Spec

## Goal

Build a dual-purpose attendance marking screen that operates as a **Kiosk** (employees self-check-in with enforced rules) or **Admin panel** (HR/admin marks attendance with full override and bulk support), determined by the logged-in user's permissions.

## Architecture

The screen detects mode based on the user's permissions:
- **Kiosk Mode** — user has `attendance:mark` but NOT `hr:create`. Enforces the selected employee's shift time window, geofence rules, and policy. One employee at a time.
- **Admin Mode** — user has `hr:create` or `company:configure`. Full override (skip shift/geofence validation), bulk check-in/out, remarks required.

All attendance records created through this screen are marked with `source: 'MANUAL'`.

---

## Permission Model

### New Permission Module

Add `attendance` to `PERMISSION_MODULES` in `permissions.ts`:

```typescript
attendance: {
  label: 'Attendance Marking',
  actions: ['mark'],
}
```

This creates the permission `attendance:mark` which can be assigned to roles via the Role & Permission Management screen.

### Mode Detection Logic

```
if user has 'hr:create' OR 'company:configure' → Admin Mode
else if user has 'attendance:mark' → Kiosk Mode
else → no access (route guard blocks)
```

### Navigation Manifest Entry

```typescript
{
  id: 'hr-admin-attendance',
  label: 'Mark Attendance',
  icon: 'user-check',
  requiredPerm: 'attendance:mark',
  path: '/app/company/hr/admin-attendance',
  module: 'hr',
  group: 'Attendance',
  roleScope: 'company',
  sortOrder: 306,
}
```

---

## Backend API

### New Files

```
avy-erp-backend/src/modules/hr/attendance/
├── admin-attendance.validators.ts    # Zod schemas
├── admin-attendance.controller.ts    # Controller
├── admin-attendance.routes.ts        # Routes
```

Routes are mounted under `/hr/attendance/admin` (after auth + tenant middleware).

### Endpoints

#### 1. `GET /hr/attendance/admin/employee/:employeeId/status`

Returns the employee's details, today's attendance record, assigned shift with resolved policy, location, and geofences — everything needed for the compact employee card.

**Permission:** `attendance:mark`

**Response:**
```typescript
{
  success: true,
  data: {
    employee: {
      id: string;
      firstName: string;
      lastName: string;
      employeeCode: string;
      profilePhotoUrl: string | null;
      departmentName: string | null;
      designationName: string | null;
    };
    todayRecord: {
      id: string;
      status: AttendanceStatus;
      punchIn: string | null;   // ISO datetime
      punchOut: string | null;
      workedHours: number | null;
      geoStatus: string | null;
      source: AttendanceSource;
      remarks: string | null;
    } | null;
    shift: {
      id: string;
      name: string;
      startTime: string;  // HH:mm
      endTime: string;
      isCrossDay: boolean;
      breaks: ShiftBreak[];
    } | null;
    resolvedPolicy: {
      gracePeriodMinutes: number;
      earlyExitToleranceMinutes: number;
      halfDayThresholdHours: number;
      fullDayThresholdHours: number;
      maxLateCheckInMinutes: number;
      selfieRequired: boolean;
      gpsRequired: boolean;
    } | null;
    location: {
      id: string;
      name: string;
      geofences: Geofence[];
    } | null;
    assignedGeofence: Geofence | null;
  }
}
```

#### 2. `POST /hr/attendance/admin/mark`

Mark check-in or check-out for a single employee.

**Permission:** `attendance:mark`

**Request:**
```typescript
{
  employeeId: string;          // Required
  action: 'CHECK_IN' | 'CHECK_OUT';  // Required
  latitude?: number;           // Optional (kiosk may have GPS)
  longitude?: number;
  photoUrl?: string;           // Optional (selfie capture)
  remarks?: string;            // Required in admin mode, optional in kiosk
  skipValidation?: boolean;    // Only honored if caller has hr:create
}
```

**Validation behavior:**

When `skipValidation` is false or absent (kiosk mode):
1. **Shift time window** — Same logic as ESS check-in: 60 min early window → shift start → maxLateCheckIn window. Rejects if outside window.
2. **Geofence** — If GPS coordinates provided and employee has geofence, validates location. Sets `geoStatus`.
3. **Double check-in/out prevention** — Same as ESS.

When `skipValidation` is true AND caller has `hr:create`:
1. Skip shift time window check
2. Skip geofence enforcement (still record geoStatus if coords provided)
3. Remarks is required
4. Still prevent double check-in/out

**Check-out logic:** Same as ESS — calls `resolvePolicy()` and `resolveAttendanceStatus()` to calculate worked hours, late/early status, deductions, etc.

**Response:**
```typescript
{
  success: true,
  data: {
    record: AttendanceRecord;  // The created/updated record
    status: 'CHECKED_IN' | 'CHECKED_OUT';
  },
  message: 'Employee checked in successfully'
}
```

#### 3. `POST /hr/attendance/admin/mark/bulk`

Bulk check-in or check-out for multiple employees.

**Permission:** `hr:create` (admin only — not available in kiosk mode)

**Request:**
```typescript
{
  employeeIds: string[];       // 1-50 employees
  action: 'CHECK_IN' | 'CHECK_OUT';
  remarks: string;             // Required
}
```

Always skips validation (admin override). Processes sequentially to avoid race conditions. For check-out, resolves policy and calculates status for each employee individually.

**Response:**
```typescript
{
  success: true,
  data: {
    results: Array<{
      employeeId: string;
      employeeName: string;
      success: boolean;
      error?: string;          // e.g., "Already checked in today"
      record?: AttendanceRecord;
    }>;
    summary: {
      total: number;
      succeeded: number;
      failed: number;
    };
  }
}
```

#### 4. `GET /hr/attendance/admin/today-log`

Returns today's admin-marked attendance records for the activity log at the bottom of the screen.

**Permission:** `attendance:mark`

**Query params:** `page`, `limit`, `search` (employee name/code)

**Response:** Paginated list of today's attendance records with employee name, action, time, source, marked-by user name.

---

## Frontend — Web (`web-system-app`)

### New Files

```
web-system-app/src/features/company-admin/hr/AdminAttendanceScreen.tsx
```

### Screen Layout

The screen has two main sections:

**Top: Employee Selection + Action Area**
- Searchable employee dropdown (search by ID or name, uses `GET /hr/employees`)
- On selection, fetches `GET /hr/attendance/admin/employee/:id/status`
- Displays compact employee card with:
  - Profile photo (via `useFileUrl`), name, employee code
  - Department, designation
  - Shift name + times (formatted via `useCompanyFormatter`)
  - Location name + geofence info
  - Today's status badge (NOT_CHECKED_IN / CHECKED_IN / CHECKED_OUT)
  - Resolved policy summary (grace period, GPS required, selfie required)
- Remarks text input (required in admin mode, optional in kiosk)
- Action buttons: Check In / Check Out (contextual based on status)

**Bottom: Today's Activity Log**
- Table/list of all attendance records marked today via this screen
- Columns: Employee Code, Name, Action, Time, Source, Marked By
- Auto-refreshes after each action

**Admin-only features:**
- Bulk Mode toggle in the header
- When bulk mode is ON: shows a filterable employee list with checkboxes, department/location filters, select all, action dropdown + remarks field + execute button
- Remarks field is required

**Kiosk-only behavior:**
- No bulk mode toggle
- After successful check-in/out, show success animation, auto-reset after 3 seconds for next employee
- Larger touch targets for kiosk display
- Remarks field is optional

### Mode Detection

```typescript
const isAdminMode = useCanPerform('hr:create');
// If true → admin features (bulk, skip validation, required remarks)
// If false → kiosk features (one at a time, enforced rules, auto-reset)
```

---

## Frontend — Mobile (`mobile-app`)

### New Files

```
mobile-app/src/features/company-admin/hr/admin-attendance-screen.tsx
mobile-app/src/app/(app)/company/hr/admin-attendance.tsx   # Route file
```

### Layout

Same logic adapted for mobile:
- Employee search at top (bottom sheet or inline search)
- Compact card below search
- Check In / Check Out action buttons (large, prominent)
- Today's activity log as a scrollable list below
- Bulk mode available for admin (toggle in header) — shows employee list with checkboxes
- Kiosk mode: auto-reset after action with success animation

---

## Activity Log / Audit

Every record created via this screen has:
- `source: 'MANUAL'` — distinguishes from self-service check-ins
- `remarks` — who marked it and why (stored in the attendance record)
- The `createdAt` timestamp serves as the audit timestamp
- The existing `GET /hr/attendance` endpoint can filter by `source: MANUAL` to see all admin-marked records

---

## Error Handling

| Scenario | Kiosk Mode | Admin Mode |
|----------|-----------|------------|
| Outside shift window | Error: "Check-in not allowed. Shift starts at 09:00 (grace: 30 min)" | Allowed (skipValidation) |
| Outside geofence | Error: "Outside geofence boundary" | Allowed, geoStatus recorded |
| Already checked in | Error: "Already checked in today" | Same error (prevents duplicates) |
| Already checked out | Error: "Already checked out today" | Same error |
| No shift assigned | Allowed (no time validation) | Allowed |
| Employee not found | Error: "Employee not found" | Same |
| Bulk: partial failure | N/A | Show per-employee success/failure results |

---

## Testing Strategy

- **Unit tests:** Admin attendance controller (validation logic, permission checks)
- **Integration tests:** Check-in flow with and without skipValidation
- **Frontend tests:** Mode detection, bulk mode toggle, employee search, auto-reset in kiosk mode
