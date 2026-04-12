# Avy ERP — Shift, Attendance & Payroll System Reference

> Complete technical reference for the HR Shift Management, Attendance Processing, Overtime, and Payroll integration systems.

---

## Table of Contents

1. [Shift Management](#1-shift-management)
2. [Attendance System](#2-attendance-system)
3. [Overtime (OT) System](#3-overtime-ot-system)
4. [Leave & Attendance Integration](#4-leave--attendance-integration)
5. [Payroll Connection](#5-payroll-connection)
6. [API Endpoints](#6-api-endpoints)
7. [Enums Reference](#7-enums-reference)
8. [Configuration Screens](#8-configuration-screens)
9. [Key File Paths](#9-key-file-paths)

---

## 1. Shift Management

### 1.1 Shift Model (`CompanyShift`)

**Prisma:** `prisma/modules/company-admin/shifts.prisma`

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `id` | String (cuid) | auto | Primary key |
| `name` | String | required | e.g., "General Shift", "Night Shift" |
| `shiftType` | Enum | required | `DAY`, `NIGHT`, `FLEXIBLE` |
| `startTime` | String | required | `HH:mm` format (e.g., "09:00") |
| `endTime` | String | required | `HH:mm` format (e.g., "18:00") |
| `isCrossDay` | Boolean | `false` | Shift spans midnight (e.g., 22:00 → 06:00) |
| `gracePeriodMinutes` | Int? | null | Override company-level grace period |
| `earlyExitToleranceMinutes` | Int? | null | Override company-level early exit tolerance |
| `halfDayThresholdHours` | Decimal? | null | Override half-day threshold |
| `fullDayThresholdHours` | Decimal? | null | Override full-day threshold |
| `maxLateCheckInMinutes` | Int? | null | Override max late check-in |
| `minWorkingHoursForOT` | Decimal? | null | Minimum hours to qualify for OT |
| `requireSelfie` | Boolean? | null | Override selfie requirement |
| `requireGPS` | Boolean? | null | Override GPS requirement |
| `allowedSources` | DeviceType[] | all | Which punch sources are allowed |
| `noShuffle` | Boolean | `false` | Prevent shift rotation for this shift |
| `autoClockOutMinutes` | Int? | null | Auto clock-out after N minutes |
| `companyId` | String | required | FK to Company |

**Relations:** `employees` (Employee[]), `breaks` (ShiftBreak[]), `attendanceRecords` (AttendanceRecord[])

### 1.2 Shift Breaks (`ShiftBreak`)

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `name` | String | required | e.g., "Lunch Break" |
| `startTime` | String? | null | Fixed break start (`HH:mm`) |
| `duration` | Int | required | Duration in minutes |
| `type` | Enum | required | `FIXED` or `FLEXIBLE` |
| `isPaid` | Boolean | `false` | If `false`, deducted from worked hours |

**Rule:** Unpaid breaks are automatically deducted from worked hours during attendance processing. The total unpaid break duration is stored in `AttendanceRecord.appliedBreakDeductionMinutes`.

### 1.3 Cross-Day Shifts

When `isCrossDay = true`:
- The shift end time is interpreted as the **next calendar day** (e.g., shift 22:00-06:00 means 22:00 today → 06:00 tomorrow)
- In the status resolver: `shiftEnd = shiftEnd.plus({ days: 1 })`
- Night shift detection also uses heuristics: `shiftType === 'NIGHT'` or `startTime >= 20:00`
- OT uses `nightShiftMultiplier` when night shift is detected

### 1.4 Shift Assignment (3 Methods)

**Method 1: Default Shift**
- `Employee.shiftId` stores the employee's default shift
- Used when no roster or rotation overrides apply

**Method 2: Roster-Based**
- `Roster` model defines weekly patterns with week-off days
- Employees are assigned to a roster; their shift follows the roster pattern
- Supports patterns: `MON_FRI`, `MON_SAT`, `MON_SAT_ALT`, `CUSTOM`

**Method 3: Rotation-Based**
- `ShiftRotationSchedule` defines a rotation pattern (WEEKLY, FORTNIGHTLY, MONTHLY, CUSTOM)
- `shifts` (Json): Array of `{ shiftId, weekNumber }` — which shift applies in which week
- `ShiftRotationAssignment` links employees to schedules
- `POST /shift-rotations/execute` applies the rotation, updating employee shifts

**Priority:** Rotation > Roster > Default Shift

### 1.5 Shift Rotation

**ShiftRotationSchedule Model:**

| Field | Type | Description |
|-------|------|-------------|
| `name` | String | Schedule name |
| `rotationPattern` | String | `WEEKLY`, `FORTNIGHTLY`, `MONTHLY`, `CUSTOM` |
| `shifts` | Json | Array of `{ shiftId, weekNumber }` |
| `effectiveFrom` | DateTime? | When rotation starts |
| `effectiveTo` | DateTime? | When rotation ends (null = indefinite) |
| `isActive` | Boolean | Active flag |

**How it works:**
1. Admin creates a schedule with shift-to-week mappings
2. Admin assigns employees via `POST /shift-rotations/:id/assign`
3. System executes rotation via `POST /shift-rotations/execute`
4. Each employee's `shiftId` is updated to the next shift in the pattern
5. Can be automated via cron or triggered manually

### 1.6 Roster Model

| Field | Type | Description |
|-------|------|-------------|
| `name` | String | e.g., "Standard 5-Day" |
| `pattern` | Enum | `MON_FRI`, `MON_SAT`, `MON_SAT_ALT`, `CUSTOM` |
| `weekOff1` | Enum? | First weekly off day (e.g., `SUNDAY`) |
| `weekOff2` | Enum? | Second weekly off day (e.g., `SATURDAY`) |
| `applicableTypeIds` | String[]? | Employee types this roster applies to |
| `effectiveFrom` | String | When roster becomes effective |
| `isDefault` | Boolean? | Default roster for the company |

**Usage in attendance:** The roster's week-off days determine which days are `WEEK_OFF` status. The attendance system checks the employee's roster to decide if a given date is a working day or week-off.

### 1.7 Shift Swap & WFH Requests

**ShiftSwapRequest Model** (`prisma/modules/hrms/shift-swap.prisma`):
- Employee requests to change their shift for specific dates
- Statuses: `PENDING` → `APPROVED` / `REJECTED`
- Approval triggers actual shift update for the requested dates

**WfhRequest Model:**
- Employee requests to work from home for a date range
- Fields: `fromDate`, `toDate`, `days`, `reason`, `status`, `approvedBy`, `approvedAt`

---

## 2. Attendance System

### 2.1 Attendance Record Model

**Prisma:** `prisma/modules/hrms/attendance.prisma`

**Core Fields:**

| Field | Type | Description |
|-------|------|-------------|
| `employeeId` | String | FK to Employee |
| `date` | DateTime (@db.Date) | Attendance date |
| `shiftId` | String? | FK to CompanyShift |
| `punchIn` | DateTime? | Check-in timestamp |
| `punchOut` | DateTime? | Check-out timestamp |
| `workedHours` | Decimal(5,2) | Net worked hours |
| `status` | AttendanceStatus | Final resolved status |
| `source` | AttendanceSource | How the punch was recorded |
| `isLate` | Boolean | Late arrival flag |
| `lateMinutes` | Int | Minutes late |
| `isEarlyExit` | Boolean | Early exit flag |
| `earlyMinutes` | Int | Minutes early |
| `overtimeHours` | Decimal(5,2) | Calculated OT hours |
| `remarks` | String? | Notes |

**Geo-tagging Fields:**

| Field | Type | Description |
|-------|------|-------------|
| `checkInLatitude` | Float? | GPS latitude at check-in |
| `checkInLongitude` | Float? | GPS longitude at check-in |
| `checkOutLatitude` | Float? | GPS latitude at check-out |
| `checkOutLongitude` | Float? | GPS longitude at check-out |
| `checkInPhotoUrl` | String? | Selfie URL at check-in |
| `checkOutPhotoUrl` | String? | Selfie URL at check-out |
| `geoStatus` | String? | `NO_LOCATION`, `INSIDE_GEOFENCE`, `OUTSIDE_GEOFENCE` |

**Regularization Fields:**

| Field | Type | Description |
|-------|------|-------------|
| `isRegularized` | Boolean | Was this record regularized? |
| `regularizedAt` | DateTime? | When it was regularized |
| `regularizedBy` | String? | User who regularized |
| `regularizationReason` | String? | Reason for regularization |
| `leaveRequestId` | String? | Linked leave request |

**Policy Snapshot (resolved at creation):**

| Field | Type | Description |
|-------|------|-------------|
| `appliedGracePeriodMinutes` | Int? | Grace period used for this record |
| `appliedFullDayThresholdHours` | Decimal? | Full-day threshold used |
| `appliedHalfDayThresholdHours` | Decimal? | Half-day threshold used |
| `appliedBreakDeductionMinutes` | Int? | Break deduction applied |
| `appliedPunchMode` | PunchMode? | Punch mode used |
| `appliedLateDeduction` | Decimal? | Late deduction amount |
| `appliedEarlyExitDeduction` | Decimal? | Early exit deduction amount |

**Audit/Trace:**

| Field | Type | Description |
|-------|------|-------------|
| `resolutionTrace` | Json? | Which config layer provided each value |
| `evaluationContext` | Json? | `{ isHoliday, isWeekOff, holidayName, rosterPattern }` |
| `finalStatusReason` | String? | Human-readable explanation of status |

**Unique Constraint:** `[employeeId, date]` — one record per employee per day.

### 2.2 Attendance Rules (26 Configurable Settings)

**Prisma:** `AttendanceRule` model — one per company (unique on `companyId`).

#### Time & Boundary
| Setting | Type | Default | Description |
|---------|------|---------|-------------|
| `dayBoundaryTime` | String | "00:00" | When a new attendance day starts |

#### Grace & Tolerance
| Setting | Type | Default | Description |
|---------|------|---------|-------------|
| `gracePeriodMinutes` | Int | 15 | Minutes after shift start before marking late |
| `earlyExitToleranceMinutes` | Int | 15 | Minutes before shift end that's still "on time" |
| `maxLateCheckInMinutes` | Int | 240 | Max late check-in (beyond = auto-absent) |

#### Day Classification Thresholds
| Setting | Type | Default | Description |
|---------|------|---------|-------------|
| `halfDayThresholdHours` | Decimal | 4.0 | Minimum hours for half-day |
| `fullDayThresholdHours` | Decimal | 8.0 | Minimum hours for full day |

#### Late Tracking
| Setting | Type | Default | Description |
|---------|------|---------|-------------|
| `lateArrivalsAllowedPerMonth` | Int | 3 | Free late arrivals before deduction kicks in |

#### Deduction Rules
| Setting | Type | Default | Description |
|---------|------|---------|-------------|
| `lopAutoDeduct` | Boolean | true | Auto-mark as LOP if below threshold |
| `lateDeductionType` | Enum | NONE | `NONE`, `HALF_DAY_AFTER_LIMIT`, `PERCENTAGE` |
| `lateDeductionValue` | Decimal? | null | Value for percentage deduction |
| `earlyExitDeductionType` | Enum | NONE | Same options as late |
| `earlyExitDeductionValue` | Decimal? | null | Value for percentage deduction |

#### Punch Mode
| Setting | Type | Default | Description |
|---------|------|---------|-------------|
| `punchMode` | Enum | FIRST_LAST | `FIRST_LAST`, `EVERY_PAIR`, `SHIFT_BASED` |

#### Auto-Processing
| Setting | Type | Default | Description |
|---------|------|---------|-------------|
| `autoMarkAbsentIfNoPunch` | Boolean | true | Auto-create ABSENT record if no punch |
| `autoHalfDayEnabled` | Boolean | true | Classify between thresholds as HALF_DAY |
| `autoAbsentAfterDays` | Int | 0 | Auto-absent after N days with no punch |
| `regularizationWindowDays` | Int | 7 | Days after date that regularization is allowed |

#### Rounding
| Setting | Type | Default | Description |
|---------|------|---------|-------------|
| `workingHoursRounding` | Enum | NONE | `NONE`, `NEAREST_15`, `NEAREST_30`, `FLOOR_15`, `CEIL_15` |
| `punchTimeRounding` | Enum | NONE | `NONE`, `NEAREST_5`, `NEAREST_15` |
| `punchTimeRoundingDirection` | Enum | NEAREST | `NEAREST`, `UP`, `DOWN` |

#### Exception Handling
| Setting | Type | Default | Description |
|---------|------|---------|-------------|
| `ignoreLateOnLeaveDay` | Boolean | true | Suppress late mark on approved leave days |
| `ignoreLateOnHoliday` | Boolean | true | Suppress late mark on holidays |
| `ignoreLateOnWeekOff` | Boolean | true | Suppress late mark on week-offs |

#### Capture Requirements
| Setting | Type | Default | Description |
|---------|------|---------|-------------|
| `selfieRequired` | Boolean | false | Require selfie for check-in/out |
| `gpsRequired` | Boolean | false | Require GPS coordinates |
| `missingPunchAlert` | Boolean | true | Alert when punch-out is missing |

### 2.3 Punch Modes

**FIRST_LAST (default):**
- First punch of the day = Check-in
- Last punch of the day = Check-out
- All middle punches are ignored
- Single punch = INCOMPLETE (missing punch-out)

**EVERY_PAIR:**
- Alternating IN/OUT pairs throughout the day
- Total worked hours = sum of all pair durations
- Validates alternating sequence (two consecutive INs = invalid)
- Invalid sequences flagged for regularization

**SHIFT_BASED:**
- Punch closest to shift start time = Check-in
- Punch closest to shift end time = Check-out
- Falls back to FIRST_LAST if no shift timing is available

### 2.4 Status Resolution (12-Step Algorithm)

**Service:** `src/shared/services/attendance-status-resolver.service.ts`

This is a **pure function** with no database reads or side effects — fully testable and auditable.

```
Step 1:  No punch? → HOLIDAY / WEEK_OFF / ABSENT
Step 2:  Missing punch-out? → INCOMPLETE
Step 3:  Calculate raw worked minutes (punchOut - punchIn)
Step 4:  Deduct unpaid breaks → net worked minutes
Step 5:  Apply working hours rounding → net worked hours
Step 6:  Check late arrival (punchIn > shiftStart + gracePeriod)
Step 7:  Auto-absent if delay > maxLateCheckInMinutes
Step 8:  Suppress late on holiday/weekoff/leave (exception handling)
Step 9:  Check early exit (punchOut < shiftEnd - earlyExitTolerance)
Step 10: Classify status:
         - workedHours >= fullDayThreshold → PRESENT (or LATE)
         - halfDayThreshold <= workedHours < fullDayThreshold → HALF_DAY
         - workedHours < halfDayThreshold → LOP (if lopAutoDeduct) or EARLY_EXIT
Step 11: Calculate overtime hours
Step 12: Calculate deductions (late + early exit)
```

**Output:**
```typescript
{
  status: AttendanceStatus;
  finalStatusReason: string;      // "Present — 8.5h worked, shift 09:00-18:00"
  isLate: boolean;
  lateMinutes: number;
  isEarlyExit: boolean;
  earlyMinutes: number;
  workedHours: number;
  overtimeHours: number;
  appliedLateDeduction: number | null;
  appliedEarlyExitDeduction: number | null;
}
```

### 2.5 Policy Resolution (7-Layer Config Stack)

**Service:** `src/shared/services/policy-resolver.service.ts`

Each field is resolved by walking a priority stack until a non-null value is found:

```
Shift-level override → Location-level override → Attendance Rules → System Default
```

| Field | Resolution Order |
|-------|-----------------|
| `gracePeriodMinutes` | Shift → AttendanceRule → Default (15) |
| `earlyExitToleranceMinutes` | Shift → AttendanceRule → Default (15) |
| `halfDayThresholdHours` | Shift → AttendanceRule → Default (4) |
| `fullDayThresholdHours` | Shift → AttendanceRule → Default (8) |
| `maxLateCheckInMinutes` | Shift → AttendanceRule → Default (240) |
| `selfieRequired` | Location → Shift → AttendanceRule → Default (false) |
| `gpsRequired` | Location → Shift → AttendanceRule → Default (false) |
| `punchMode` | AttendanceRule → Default (FIRST_LAST) |
| `workingHoursRounding` | AttendanceRule → Default (NONE) |
| `breakDeduction` | Sum of unpaid ShiftBreak durations → Default (0) |

The resolution **trace** is stored in `AttendanceRecord.resolutionTrace` for auditability:
```json
{
  "gracePeriod": "SHIFT",
  "earlyExitTolerance": "ATTENDANCE_RULE",
  "selfieRequired": "LOCATION",
  "punchMode": "ATTENDANCE_RULE"
}
```

### 2.6 Regularization Flow

1. Employee/HR creates `AttendanceOverride` with:
   - `issueType`: `MISSING_PUNCH_IN`, `MISSING_PUNCH_OUT`, `ABSENT_OVERRIDE`, `LATE_OVERRIDE`, `NO_PUNCH`
   - `correctedPunchIn`, `correctedPunchOut`, `reason`
2. Status starts as `PENDING`
3. HR approves/rejects:
   - `approvedBy`, `approvedAt`, `payrollImpact` (e.g., "LOP reduced by 0.5 day")
4. On approval: original `AttendanceRecord` is updated with corrected values
5. Record marked: `isRegularized = true`, `regularizedAt`, `regularizedBy`

### 2.7 GPS/Geofence Validation

- Each `Location` can have: `requireLiveLocation`, `requireSelfie`, `geofenceId`
- Each `Shift` can override: `requireGPS`, `requireSelfie`
- Validation during `createRecord()`:
  - If selfie required but `checkInPhotoUrl` missing → error
  - If GPS required but lat/lng missing → error
  - Geofence check: `INSIDE_GEOFENCE` / `OUTSIDE_GEOFENCE` stored in `geoStatus`

### 2.8 Holiday Calendar

| Field | Type | Description |
|-------|------|-------------|
| `name` | String | Holiday name |
| `date` | DateTime (@db.Date) | Holiday date |
| `type` | Enum | `NATIONAL`, `REGIONAL`, `COMPANY`, `OPTIONAL`, `RESTRICTED` |
| `branchIds` | Json? | Location IDs (null = all locations) |
| `year` | Int | Calendar year |
| `isOptional` | Boolean | Optional/restricted holiday |
| `maxOptionalSlots` | Int? | Max employees who can take this optional holiday |

**Integration:** Checked during attendance creation to set `isHoliday` flag and auto-fill `HOLIDAY` status.

---

## 3. Overtime (OT) System

### 3.1 Overtime Rules (20 Settings)

**Prisma:** `OvertimeRule` model — one per company (unique on `companyId`).

#### Eligibility
| Setting | Type | Default | Description |
|---------|------|---------|-------------|
| `eligibleTypeIds` | String[]? | null (all) | Employee types eligible for OT |

#### Calculation
| Setting | Type | Default | Description |
|---------|------|---------|-------------|
| `calculationBasis` | Enum | AFTER_SHIFT | `AFTER_SHIFT` (hours beyond shift) or `TOTAL_HOURS` (all hours on holiday/weekend) |
| `thresholdMinutes` | Int | 30 | Dead-zone: must work this many mins beyond shift before OT counts |
| `minimumOtMinutes` | Int | 30 | Minimum OT to be counted |
| `includeBreaksInOT` | Boolean | false | Add unpaid breaks back into OT calculation |

#### Rate Multipliers
| Setting | Type | Default | Description |
|---------|------|---------|-------------|
| `weekdayMultiplier` | Decimal | 1.5 | OT rate for regular weekdays |
| `weekendMultiplier` | Decimal? | null (uses weekday) | OT rate for weekends |
| `holidayMultiplier` | Decimal? | null (uses weekday) | OT rate for holidays |
| `nightShiftMultiplier` | Decimal? | null (uses weekday) | OT rate for night shifts |

#### Caps
| Setting | Type | Default | Description |
|---------|------|---------|-------------|
| `enforceCaps` | Boolean | false | Enable OT caps |
| `dailyCapHours` | Decimal? | null | Max OT hours per day |
| `weeklyCapHours` | Decimal? | null | Max OT hours per ISO week |
| `monthlyCapHours` | Decimal? | null | Max OT hours per calendar month |
| `maxContinuousOtHours` | Decimal? | null | Max cumulative OT across consecutive days |

#### Approval & Payroll
| Setting | Type | Default | Description |
|---------|------|---------|-------------|
| `approvalRequired` | Boolean | true | Require HR approval for OT |
| `autoIncludePayroll` | Boolean | false | Auto-include approved OT in payroll |

#### Comp-Off
| Setting | Type | Default | Description |
|---------|------|---------|-------------|
| `compOffEnabled` | Boolean | false | Generate comp-off from approved OT |
| `compOffExpiryDays` | Int? | null | Days until comp-off expires |

#### Rounding
| Setting | Type | Default | Description |
|---------|------|---------|-------------|
| `roundingStrategy` | Enum | NONE | Applied to final OT hours |

### 3.2 OT Calculation Flow

1. **Check eligibility:** `eligibleTypeIds` — if set, employee type must be in list
2. **Check minimum hours:** `minWorkingHoursForOT` on shift — must have worked enough
3. **Calculate raw OT:**
   - `AFTER_SHIFT`: OT = workedHours - fullDayThreshold
   - `TOTAL_HOURS`: OT = entire workedHours (for holiday/weekend work)
4. **Apply threshold:** Must exceed `thresholdMinutes` dead-zone
5. **Apply minimum:** Result must be >= `minimumOtMinutes`
6. **Handle breaks:** If `includeBreaksInOT`, add back unpaid break minutes
7. **Apply rounding:** Round OT hours per `roundingStrategy`
8. **Apply caps:** If `enforceCaps`, check daily/weekly/monthly/continuous caps
9. **Determine multiplier:** Based on day context (weekday/weekend/holiday/night)
10. **Create request:** If `approvalRequired`, status = `PENDING`; else auto-approve

### 3.3 Overtime Request Statuses

```
PENDING → APPROVED → PAID
PENDING → REJECTED
APPROVED → COMP_OFF_ACCRUED (if compOffEnabled)
```

### 3.4 Comp-Off Generation

When `compOffEnabled = true` and OT request is approved:
- Create/update `LeaveBalance` with category `COMPENSATORY`
- If `compOffExpiryDays` is set: `expiresAt = approvedAt + compOffExpiryDays`
- Employee can use comp-off balance to request compensatory leave

---

## 4. Leave & Attendance Integration

### 4.1 How Leave Affects Attendance

- When leave is `APPROVED` for a date, attendance status may be set to `ON_LEAVE`
- If `ignoreLateOnLeaveDay = true`: late arrival is suppressed on leave days
- Leave deduction from salary happens during payroll processing, not attendance

### 4.2 Sandwich Rule

Configured per leave type:
- `LeaveType.weekendSandwich` (Boolean, default: false)
- `LeaveType.holidaySandwich` (Boolean, default: false)

If enabled, weekends/holidays between leave start and end dates are counted as leave days. Applied at leave approval time.

### 4.3 LOP (Loss of Pay)

- If `lopAutoDeduct = true` and worked hours < halfDayThreshold → status = `LOP`
- LOP days are counted in payroll for salary deduction
- LOP = `(annualCTC / 12 / standardWorkingDays) * lopDays`

---

## 5. Payroll Connection

### 5.1 How Attendance Feeds Into Payroll

**PayrollEntry fields from attendance:**

| Field | Type | Source |
|-------|------|--------|
| `workingDays` | Decimal(5,1) | Total days - holidays - weekoffs |
| `presentDays` | Decimal(5,1) | Count of PRESENT records |
| `lopDays` | Decimal(5,1) | Count of LOP + ABSENT + ON_LEAVE |
| `overtimeHours` | Decimal(5,1) | Sum of APPROVED OT hours |
| `overtimeAmount` | Decimal(15,2) | OT rate * multiplier * hours |

### 5.2 Payroll Run Pipeline

```
DRAFT
  → ATTENDANCE_LOCKED (HR locks attendance for the month)
  → EXCEPTIONS_REVIEWED (HR reviews late, LOP, OT exceptions)
  → COMPUTED (system calculates salary for all employees)
  → STATUTORY_DONE (PF, ESI, PT, TDS calculated)
  → APPROVED (finance approves)
  → DISBURSED (payment processed)
  → ARCHIVED
```

### 5.3 OT Payment in Payroll

- Only `APPROVED` OT requests are included
- `overtimeAmount = overtimeHours * hourlyRate * appliedMultiplier`
- Hourly rate = `annualCTC / 12 / standardWorkingDays / 8`
- Multiplier selected based on day context (weekday/weekend/holiday/night)

### 5.4 Shift Allowances

Configured via `SalaryComponent`:
- Night shift allowance: component with code like `NIGHT_ALLOWANCE`
- Calculation methods: `FIXED` (flat amount per night shift) or `PERCENT_OF_BASIC`
- Applied during payroll run based on count of night shifts worked

---

## 6. API Endpoints

### Attendance Records
| Method | Path | Permission | Description |
|--------|------|------------|-------------|
| GET | `/attendance` | hr:read | List records (filters: employeeId, dateFrom, dateTo, status, departmentId) |
| POST | `/attendance` | hr:create | Create record (full punch processing) |
| GET | `/attendance/summary` | hr:read | Daily summary (present, absent, late, by department) |
| GET | `/attendance/:id` | hr:read | Get single record |
| PATCH | `/attendance/:id` | hr:update | Update record |

### Admin Attendance (Kiosk)
| Method | Path | Permission | Description |
|--------|------|------------|-------------|
| POST | `/attendance/admin/mark` | hr:create | Quick mark present/absent |
| POST | `/attendance/admin/mark-bulk` | hr:create | Bulk mark |

### Auto-Processing
| Method | Path | Permission | Description |
|--------|------|------------|-------------|
| POST | `/attendance/populate-month` | hr:create | Auto-fill holidays & week-offs |
| POST | `/attendance/process-comp-off` | hr:create | Accrue comp-off from approved OT |
| POST | `/attendance/process-auto-clockout` | hr:update | Auto-close incomplete records |

### Overrides / Regularization
| Method | Path | Permission | Description |
|--------|------|------------|-------------|
| GET | `/attendance/overrides` | hr:read | List overrides |
| POST | `/attendance/overrides` | hr:create | Create override request |
| PATCH | `/attendance/overrides/:id` | hr:approve | Approve/reject override |

### Attendance Rules
| Method | Path | Permission | Description |
|--------|------|------------|-------------|
| GET | `/attendance/rules` | hr:read | Get rules (auto-seed if missing) |
| PATCH | `/attendance/rules` | hr:configure | Update rules |

### Holiday Calendar
| Method | Path | Permission | Description |
|--------|------|------------|-------------|
| GET | `/holidays` | hr:read | List holidays |
| POST | `/holidays` | hr:create | Create holiday |
| POST | `/holidays/clone` | hr:create | Clone from another year |
| PATCH | `/holidays/:id` | hr:update | Update holiday |
| DELETE | `/holidays/:id` | hr:delete | Delete holiday |

### Rosters
| Method | Path | Permission | Description |
|--------|------|------------|-------------|
| GET | `/rosters` | hr:read | List rosters |
| POST | `/rosters` | hr:create | Create roster |
| PATCH | `/rosters/:id` | hr:update | Update roster |
| DELETE | `/rosters/:id` | hr:delete | Delete roster |

### Overtime Rules & Requests
| Method | Path | Permission | Description |
|--------|------|------------|-------------|
| GET | `/overtime-rules` | hr:read | Get rules (auto-seed) |
| PATCH | `/overtime-rules` | hr:configure | Update rules |
| GET | `/overtime-requests` | hr:read | List requests |
| PATCH | `/overtime-requests/:id/approve` | hr:approve | Approve with notes |
| PATCH | `/overtime-requests/:id/reject` | hr:approve | Reject with reason |

### Biometric Devices
| Method | Path | Permission | Description |
|--------|------|------------|-------------|
| GET | `/biometric-devices` | hr:read | List devices |
| POST | `/biometric-devices` | hr:create | Add device |
| PATCH | `/biometric-devices/:id` | hr:update | Update config |
| DELETE | `/biometric-devices/:id` | hr:delete | Remove device |
| POST | `/biometric-devices/:id/test` | hr:update | Test connection |
| POST | `/biometric-devices/:id/sync` | hr:create | Sync punch records |

### Shift Rotation
| Method | Path | Permission | Description |
|--------|------|------------|-------------|
| GET | `/shift-rotations` | hr:read | List schedules |
| POST | `/shift-rotations` | hr:create | Create schedule |
| POST | `/shift-rotations/execute` | hr:update | Execute rotation |
| PATCH | `/shift-rotations/:id` | hr:update | Update schedule |
| DELETE | `/shift-rotations/:id` | hr:delete | Delete schedule |
| POST | `/shift-rotations/:id/assign` | hr:update | Assign employees |
| DELETE | `/shift-rotations/:id/assign/:employeeId` | hr:update | Remove employee |

---

## 7. Enums Reference

### AttendanceStatus
`PRESENT` | `ABSENT` | `HALF_DAY` | `LATE` | `EARLY_EXIT` | `INCOMPLETE` | `ON_LEAVE` | `HOLIDAY` | `WEEK_OFF` | `REGULARIZED` | `LOP`

### AttendanceSource
`BIOMETRIC` | `FACE_RECOGNITION` | `MOBILE_GPS` | `WEB_PORTAL` | `MANUAL` | `IOT` | `SMART_CARD`

### PunchMode
`FIRST_LAST` | `EVERY_PAIR` | `SHIFT_BASED`

### RoundingStrategy
`NONE` | `NEAREST_15` | `NEAREST_30` | `FLOOR_15` | `CEIL_15`

### PunchRounding
`NONE` | `NEAREST_5` | `NEAREST_15`

### RoundingDirection
`NEAREST` | `UP` | `DOWN`

### DeductionType
`NONE` | `HALF_DAY_AFTER_LIMIT` | `PERCENTAGE`

### ShiftType
`DAY` | `NIGHT` | `FLEXIBLE`

### BreakType
`FIXED` | `FLEXIBLE`

### OTCalculationBasis
`AFTER_SHIFT` | `TOTAL_HOURS`

### OvertimeRequestStatus
`PENDING` | `APPROVED` | `REJECTED` | `PAID` | `COMP_OFF_ACCRUED`

### HolidayType
`NATIONAL` | `REGIONAL` | `COMPANY` | `OPTIONAL` | `RESTRICTED`

### RosterPattern
`MON_FRI` | `MON_SAT` | `MON_SAT_ALT` | `CUSTOM`

### PayrollRunStatus
`DRAFT` | `ATTENDANCE_LOCKED` | `EXCEPTIONS_REVIEWED` | `COMPUTED` | `STATUTORY_DONE` | `APPROVED` | `DISBURSED` | `ARCHIVED`

---

## 8. Configuration Screens

### Attendance & Shift Screens
| Nav ID | Label | Permission | Description |
|--------|-------|------------|-------------|
| `hr-att-admin` | Mark Attendance | hr:create | Manual/kiosk attendance marking |
| `hr-att-dash` | Attendance Dashboard | hr:read | Overview with department breakdowns |
| `hr-holidays` | Holiday Calendar | hr:read | CRUD for company holidays |
| `hr-rosters` | Rosters | hr:read | Weekly patterns & week-off configuration |
| `hr-att-overrides` | Attendance Overrides | hr:read | Regularization requests |
| `hr-att-rules` | Attendance Rules | hr:configure | 26-setting configuration |
| `hr-ot-rules` | Overtime Rules | hr:configure | 20-setting configuration |
| `hr-biometric` | Biometric Devices | hr:configure | Device management |
| `hr-rotations` | Shift Rotations | hr:configure | Rotation schedule management |

### Payroll & Compliance Screens
| Nav ID | Label | Permission | Description |
|--------|-------|------------|-------------|
| `hr-sal-comp` | Salary Components | hr:read | Earning/deduction components |
| `hr-sal-struct` | Salary Structures | hr:read | CTC breakdown structures |
| `hr-emp-sal` | Employee Salary | hr:read | Per-employee salary assignment |
| `hr-statutory` | Statutory Config | hr:configure | PF, ESI, PT, Gratuity, Bonus, LWF |
| `hr-tax` | Tax & TDS | hr:configure | Tax regime & slabs |
| `hr-payroll-runs` | Payroll Runs | hr:read | Monthly payroll processing |
| `hr-payslips` | Payslips | hr:read | Generated payslips |
| `hr-pay-reports` | Payroll Reports | hr:export | Report generation & downloads |

### ESS (Employee Self-Service) Screens
| Nav ID | Label | Permission | Description |
|--------|-------|------------|-------------|
| `ess-attendance` | My Attendance | ess:view-attendance | Employee's own attendance records |
| `ess-checkin` | Shift Check-In | ess:view-attendance | Mobile check-in with GPS/selfie |
| `ess-shift-swap` | Shift Swap | ess:swap-shift | Request shift changes |

---

## 9. Key File Paths

### Prisma Models
| File | Contains |
|------|----------|
| `prisma/modules/company-admin/shifts.prisma` | CompanyShift, ShiftBreak |
| `prisma/modules/hrms/attendance.prisma` | AttendanceRecord, AttendanceRule, OvertimeRule, OvertimeRequest, AttendanceOverride, HolidayCalendar, Roster |
| `prisma/modules/hrms/advanced.prisma` | ShiftRotationSchedule, ShiftRotationAssignment, BiometricDevice |
| `prisma/modules/hrms/shift-swap.prisma` | ShiftSwapRequest, WfhRequest |
| `prisma/modules/hrms/leave.prisma` | LeaveType, LeavePolicy, LeaveBalance, LeaveRequest |
| `prisma/modules/hrms/payroll-config.prisma` | SalaryComponent, SalaryStructure, LoanPolicy, LoanRecord |
| `prisma/modules/hrms/payroll-run.prisma` | PayrollRun, PayrollEntry, PayslipBatch |

### Services
| File | Purpose |
|------|---------|
| `src/modules/hr/attendance/attendance.service.ts` | Main attendance CRUD, OT processing, regularization |
| `src/shared/services/attendance-status-resolver.service.ts` | Pure 12-step status resolution algorithm |
| `src/shared/services/policy-resolver.service.ts` | 7-layer policy config resolution |
| `src/shared/services/punch-validator.service.ts` | Punch sequence validation (FIRST_LAST, EVERY_PAIR, SHIFT_BASED) |
| `src/shared/services/location-validator.service.ts` | GPS/geofence validation |
| `src/modules/hr/payroll/payroll.service.ts` | Payroll computation & salary calculation |

### Routes & Validators
| File | Purpose |
|------|---------|
| `src/modules/hr/attendance/attendance.routes.ts` | All attendance API routes |
| `src/modules/hr/attendance/attendance.validators.ts` | Zod schemas for all attendance endpoints |
| `src/modules/hr/attendance/admin-attendance.routes.ts` | Admin/kiosk attendance routes |
| `src/modules/hr/attendance/admin-attendance.service.ts` | Admin attendance marking logic |
