# HRMS Configuration System — Enterprise Architecture Design Spec

**Date:** 2026-03-30
**Status:** Approved
**Scope:** Complete redesign of all HRMS configuration screens across backend, web, and mobile
**Affected Codebases:** avy-erp-backend, web-system-app, mobile-app

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [Configuration Stack & Resolution Chain](#2-configuration-stack--resolution-chain)
3. [Enums (Shared Types)](#3-enums-shared-types)
4. [Schema Design (Prisma Models)](#4-schema-design-prisma-models)
5. [Screen-wise Field Definitions & API Contracts](#5-screen-wise-field-definitions--api-contracts)
6. [Enforcement Engine](#6-enforcement-engine)
7. [Attendance Status Resolver](#7-attendance-status-resolver)
8. [Runtime Flow](#8-runtime-flow)
9. [Caching Strategy](#9-caching-strategy)
10. [Migration Strategy](#10-migration-strategy)
11. [Systems Removed](#11-systems-removed)

---

## 1. Executive Summary

### Problem

The current HRMS configuration system has critical issues:

- **Phantom fields:** 6 of 8 screens have frontend fields with no backend support (web worst: 16 phantom fields on Attendance Rules alone)
- **Zero enforcement:** Configs are stored but never checked in business logic (only 1 of 27 ESS configs enforced)
- **Four overlapping control systems:** Feature Toggles, System Controls, Company Settings, ESS Config all manage overlapping concerns
- **Field name chaos:** Web, mobile, and backend use different names for the same fields
- **JSON blobs:** `Company.preferences` and `Company.systemControls` stored as untyped JSON — no validation, no migration safety

### Solution

A complete redesign with:

- **7-layer configuration stack** with deterministic resolution order
- **Typed Prisma models** replacing all JSON blobs
- **Shift Master as operational engine** with selective policy overrides
- **Location as constraint layer** (limited scope — geo/device/network only)
- **Enforcement middleware** that checks every config at runtime
- **Deterministic attendance status resolver** producing auditable results
- **Resolved value snapshots** stored on every attendance record for historical correctness

### What Changes

| Component | Action |
|-----------|--------|
| `Company.preferences` JSON | Replaced by typed `CompanySettings` model |
| `Company.systemControls` JSON | Replaced by typed `SystemControls` model |
| `CompanyShift.downtimeSlots` JSON | Replaced by `ShiftBreak` model |
| `FeatureToggle` system | Removed entirely (module enablement → SystemControls) |
| `AttendanceRule` | Enhanced with 16 new fields (punch mode, rounding, deductions, auto-processing) |
| `OvertimeRule` | Enhanced with granular multipliers, caps, comp-off |
| New: `OvertimeRequest` | Full approval workflow lifecycle |
| New: `ShiftBreak` | Typed break management (fixed/flexible, paid/unpaid) |
| `CompanyShift` | Enhanced with nullable policy overrides + shift type |
| `Location` | Enhanced with device/network constraint fields |
| `ESSConfig` | Security fields removed (→ SystemControls), MSS + mobile behavior added |
| `AttendanceRecord` | Enhanced with resolved policy snapshots + resolution trace + evaluation context |
| All frontend screens | Standardized to exact backend field names, phantom fields removed |

---

## 2. Configuration Stack & Resolution Chain

### Layer Order (Final — Production-Ready)

```
LAYER 1: Company Settings          → Global context (locale, compliance, integrations)
LAYER 2: System Controls           → Feature gates + security policies
LAYER 3: Location Constraints      → Hard constraints (geo/device/network) — FAIL FAST
LAYER 4: Shift Master              → Operational timing + selective policy overrides
LAYER 5: Attendance Rules          → Company-wide default policies (fallback)
LAYER 6: Overtime Rules            → Post-calculation engine (rates, caps, approval)
LAYER 7: ESS Config                → Employee self-service access gates
```

Location evaluates before Shift because it is a hard constraint layer — if geo-fence fails, there is no need to evaluate shift timing or attendance rules.

### Resolution Pattern

Every overridable field follows a typed resolution chain. Resolution order depends on field type:

**Policy fields** (grace period, thresholds, deductions):
```
employee.override → shift → attendanceRules → SYSTEM_DEFAULTS
```

**Constraint fields** (selfie, GPS, device):
```
location → shift → attendanceRules → SYSTEM_DEFAULTS
```

**Rules:**
- `null` = inherit from parent layer (NEVER use `undefined`)
- Explicit value = override
- Every chain terminates at `SYSTEM_DEFAULTS` (hardcoded fallback)

**At API/DB level, enforce:**
```typescript
if (value === undefined) throw ApiError.badRequest('Use null for inheritance, not undefined');
```

### Resolved Values Storage

When an `AttendanceRecord` is created, store the resolved snapshot — not just references:

```typescript
{
  // Reference
  shiftId: "shift_abc",

  // Resolved values (frozen at time of punch)
  appliedGracePeriodMinutes: 10,
  appliedFullDayThresholdHours: 8.00,
  appliedHalfDayThresholdHours: 4.00,
  appliedBreakDeductionMinutes: 30,
  appliedPunchMode: "FIRST_LAST",
  appliedLateDeduction: 0,
  appliedEarlyExitDeduction: 0,

  // Resolution trace (field-level audit — where each value came from)
  resolutionTrace: {
    gracePeriod: "SHIFT",
    fullDayThreshold: "ATTENDANCE_RULE",
    halfDayThreshold: "SHIFT",
    selfieRequired: "LOCATION",
    gpsRequired: "ATTENDANCE_RULE"
  },

  // Evaluation context (frozen context for this record)
  evaluationContext: {
    isHoliday: false,
    isWeekOff: false,
    holidayName: null,
    rosterPattern: "MON_FRI"
  },

  // Status reasoning
  finalStatusReason: "Late by 22min (full day worked)"
}
```

This ensures historical correctness: configs may change later, but the attendance record preserves exactly what rules were applied and why.

---

## 3. Enums (Shared Types)

All enums used across models, replacing raw string fields:

```prisma
// ── Company Settings ──
enum CurrencyCode {
  INR
  USD
  EUR
  GBP
  AED
}

enum LanguageCode {
  en
  hi
  ta
  te
  mr
  kn
}

enum TimeFormat {
  TWELVE_HOUR
  TWENTY_FOUR_HOUR
}

// ── Shift ──
enum ShiftType {
  DAY
  NIGHT
  FLEXIBLE
}

enum BreakType {
  FIXED       // must be taken at startTime
  FLEXIBLE    // can be taken anytime during shift
}

// ── Attendance ──
enum PunchMode {
  FIRST_LAST   // first punch = in, last punch = out
  EVERY_PAIR   // alternating in/out pairs, sum all durations
  SHIFT_BASED  // match punches to assigned shift window
}

enum RoundingStrategy {
  NONE
  NEAREST_15
  NEAREST_30
  FLOOR_15
  CEIL_15
}

enum PunchRounding {
  NONE
  NEAREST_5
  NEAREST_15
}

enum RoundingDirection {
  NEAREST
  UP
  DOWN
}

enum DeductionType {
  NONE
  HALF_DAY_AFTER_LIMIT
  PERCENTAGE
}

enum LocationAccuracy {
  HIGH
  MEDIUM
  LOW
}

enum AttendanceStatus {
  PRESENT
  ABSENT
  HALF_DAY
  LATE
  EARLY_EXIT
  INCOMPLETE    // punch-in exists but punch-out missing (not yet resolved)
  HOLIDAY
  WEEK_OFF
  ON_LEAVE
  REGULARIZED
  LOP
}

enum AttendanceSource {
  BIOMETRIC
  FACE_RECOGNITION
  MOBILE_GPS
  WEB_PORTAL
  MANUAL
  IOT
  SMART_CARD
}

enum DeviceType {
  BIOMETRIC
  MOBILE_GPS
  WEB_PORTAL
  SMART_CARD
  FACE_RECOGNITION
}

// ── Overtime ──
enum OTCalculationBasis {
  AFTER_SHIFT   // OT = worked hours beyond shift end
  TOTAL_HOURS   // OT = total worked hours minus full-day threshold
}

enum OvertimeRequestStatus {
  PENDING
  APPROVED
  REJECTED
  PAID
  COMP_OFF_ACCRUED
}

enum OTMultiplierSource {
  WEEKDAY
  WEEKEND
  HOLIDAY
  NIGHT_SHIFT
}
```

---

## 4. Schema Design (Prisma Models)

### 4.1 CompanySettings

Replaces `Company.preferences` JSON blob. One per company.

```prisma
model CompanySettings {
  id        String   @id @default(cuid())
  companyId String   @unique

  // ── Locale ──
  currency      CurrencyCode @default(INR)
  language      LanguageCode @default(en)
  timezone      String       @default("Asia/Kolkata")  // IANA timezone string
  dateFormat    String       @default("DD/MM/YYYY")
  timeFormat    TimeFormat   @default(TWELVE_HOUR)
  numberFormat  String       @default("en-IN")         // en-IN or en-US

  // ── Compliance ──
  indiaCompliance  Boolean @default(true)
  gdprMode         Boolean @default(false)
  auditTrail       Boolean @default(true)

  // ── Integrations ──
  bankIntegration         Boolean @default(false)
  razorpayEnabled         Boolean @default(false)
  emailNotifications      Boolean @default(true)
  whatsappNotifications   Boolean @default(false)
  biometricIntegration    Boolean @default(false)
  eSignIntegration        Boolean @default(false)

  company   Company  @relation(fields: [companyId], references: [id], onDelete: Cascade)
  createdBy String?  // userId
  updatedBy String?  // userId
  createdAt DateTime @default(now())
  updatedAt DateTime @updatedAt

  @@map("company_settings")
}
```

**Removed from this model:** `essPortal`, `mobileAppAccess`, `aiChatbot`, `multiCurrencyPayroll`, `internationalTaxCompliance`, `thirdPartyHRMSSync`, `webApp`, `mobileApp`, `systemApp` — these were either feature gates (moved to SystemControls) or phantom fields (removed).

**Contains ONLY:** locale preferences, compliance modes, integration toggles.

---

### 4.2 SystemControls

Replaces `Company.systemControls` JSON blob. One per company.

```prisma
model SystemControls {
  id        String   @id @default(cuid())
  companyId String   @unique

  // ── Module Enablement (replaces Feature Toggles) ──
  attendanceEnabled    Boolean @default(true)
  leaveEnabled         Boolean @default(true)
  payrollEnabled       Boolean @default(true)
  essEnabled           Boolean @default(true)
  performanceEnabled   Boolean @default(false)
  recruitmentEnabled   Boolean @default(false)
  trainingEnabled      Boolean @default(false)
  mobileAppEnabled     Boolean @default(true)
  aiChatbotEnabled     Boolean @default(false)

  // ── Production Controls ──
  ncEditMode    Boolean @default(false)
  loadUnload    Boolean @default(false)
  cycleTime     Boolean @default(false)

  // ── Payroll Controls ──
  payrollLock           Boolean @default(true)
  backdatedEntryControl Boolean @default(false)

  // ── Leave Controls ──
  leaveCarryForward   Boolean @default(true)
  compOffEnabled      Boolean @default(false)
  halfDayLeaveEnabled Boolean @default(true)

  // ── Security & Access ──
  mfaRequired                Boolean @default(false)
  sessionTimeoutMinutes      Int     @default(30)   // range: 5-1440
  maxConcurrentSessions      Int     @default(3)    // range: 1-10
  passwordMinLength          Int     @default(8)    // range: 6-32
  passwordComplexity         Boolean @default(true) // uppercase+lowercase+number+special
  accountLockThreshold       Int     @default(5)    // failed attempts before lock
  accountLockDurationMinutes Int     @default(30)   // auto-unlock duration

  // ── Audit ──
  auditLogRetentionDays Int @default(365) // range: 30-730

  company   Company  @relation(fields: [companyId], references: [id], onDelete: Cascade)
  createdBy String?  // userId
  updatedBy String?  // userId
  createdAt DateTime @default(now())
  updatedAt DateTime @updatedAt

  @@map("system_controls")
}
```

**Removed:** `overtimeApprovalRequired` (moved to `OvertimeRule.approvalRequired`), `ipWhitelistEnabled`, `ipWhitelistRanges` (removed from platform entirely).

**Absorbed from Feature Toggles:** Module enablement flags replace the per-user toggle system.

**Absorbed from ESS Config:** All security fields (MFA, session, password, account lock) centralized here.

---

### 4.3 Location (Enhanced — existing model, new constraint fields)

New fields added to existing `Location` model. Limited scope: geo, device, network only.

```prisma
model Location {
  // ── Existing fields (unchanged) ──
  id                 String   @id @default(cuid())
  companyId          String
  name               String
  isHQ               Boolean  @default(false)
  facilityType       String?
  address            Json?
  contactName        String?
  contactDesignation String?
  contactEmail       String?
  contactPhone       String?
  geoEnabled         Boolean  @default(false)
  geoLat             Float?
  geoLng             Float?
  geoRadius          Int?     // meters, range: 50-5000
  geoShape           String?  // CIRCLE, POLYGON

  // ── NEW: Device Restrictions ──
  allowedDevices      DeviceType[]    // empty array = all devices allowed
  requireSelfie       Boolean?        // null = inherit from attendance rules
  requireLiveLocation Boolean?        // null = inherit from attendance rules

  // ── NEW: Advanced Geo (future) ──
  geoPolygon          Json?   // GeoJSON polygon coordinates for non-circular zones

  // ... existing relations unchanged
  company             Company @relation(fields: [companyId], references: [id], onDelete: Cascade)
  // ...existing relations...

  @@map("locations")
}
```

**What Location CAN override:** geo-fencing, device restrictions, selfie/location requirements.

**What Location MUST NOT override:** grace periods, thresholds, shift timings, payroll logic, OT rules, rounding, punch interpretation.

---

### 4.4 CompanyShift (Enhanced — operational engine)

```prisma
model CompanyShift {
  id        String   @id @default(cuid())
  companyId String

  // ── Core Timing ──
  name       String
  shiftType  ShiftType @default(DAY)
  startTime  String                     // "09:00" (HH:MM, 24h format)
  endTime    String                     // "17:00" (HH:MM, 24h format)
  isCrossDay Boolean   @default(false)  // true if shift spans midnight

  // ── Break Management ──
  breaks     ShiftBreak[]               // replaces downtimeSlots JSON

  // ── Policy Overrides (null = inherit from Attendance Rules) ──
  gracePeriodMinutes        Int?
  earlyExitToleranceMinutes Int?
  halfDayThresholdHours     Decimal? @db.Decimal(4, 2)
  fullDayThresholdHours     Decimal? @db.Decimal(4, 2)
  maxLateCheckInMinutes     Int?
  minWorkingHoursForOT      Decimal? @db.Decimal(4, 2) // min hours before OT kicks in

  // ── Capture Overrides (null = inherit) ──
  requireSelfie    Boolean?
  requireGPS       Boolean?
  allowedSources   DeviceType[]   // empty = inherit from rules

  // ── Behavior ──
  noShuffle           Boolean @default(false)
  autoClockOutMinutes Int?    // auto clock-out N minutes after shift end; null = disabled

  // ── Relations ──
  company           Company            @relation(fields: [companyId], references: [id], onDelete: Cascade)
  employees         Employee[]
  attendanceRecords AttendanceRecord[] @relation("AttendanceShift")

  createdAt DateTime @default(now())
  updatedAt DateTime @updatedAt

  @@map("company_shifts")
}

model ShiftBreak {
  id      String @id @default(cuid())
  shiftId String

  name      String    // "Lunch Break", "Tea Break"
  startTime String?   // "12:30" — null for flexible breaks
  duration  Int       // minutes
  type      BreakType // FIXED or FLEXIBLE
  isPaid    Boolean   @default(false)

  shift CompanyShift @relation(fields: [shiftId], references: [id], onDelete: Cascade)

  @@map("shift_breaks")
}
```

**Key changes from current:**
- `fromTime`/`toTime` renamed to `startTime`/`endTime`
- `downtimeSlots` JSON replaced by typed `ShiftBreak` model
- Added `shiftType` enum (DAY, NIGHT, FLEXIBLE)
- Added `isCrossDay` for explicit night shift declaration
- Added nullable policy override fields (core of resolve pattern)
- Added `minWorkingHoursForOT` for OT engine integration
- Added `autoClockOutMinutes`

---

### 4.5 AttendanceRule (Enhanced — company-wide defaults)

```prisma
model AttendanceRule {
  id        String   @id @default(cuid())
  companyId String   @unique

  // ── Time & Boundary ──
  dayBoundaryTime String @default("00:00") // when calendar day flips for night shifts

  // ── Grace & Tolerance (defaults — shift can override) ──
  gracePeriodMinutes        Int @default(15)
  earlyExitToleranceMinutes Int @default(15)
  maxLateCheckInMinutes     Int @default(240) // 4 hours — then auto-absent

  // ── Day Classification Thresholds (defaults — shift can override) ──
  halfDayThresholdHours Decimal @default(4)  @db.Decimal(4, 2)
  fullDayThresholdHours Decimal @default(8)  @db.Decimal(4, 2)

  // ── Late/Early Tracking ──
  lateArrivalsAllowedPerMonth Int @default(3)

  // ── Deduction Rules ──
  lopAutoDeduct           Boolean       @default(true)
  lateDeductionType       DeductionType @default(NONE)
  lateDeductionValue      Decimal?      @db.Decimal(5, 2) // percentage if type=PERCENTAGE
  earlyExitDeductionType  DeductionType @default(NONE)
  earlyExitDeductionValue Decimal?      @db.Decimal(5, 2)

  // ── Punch Interpretation ──
  punchMode PunchMode @default(FIRST_LAST)
  // FIRST_LAST: first punch = in, last punch = out
  // EVERY_PAIR: alternating in/out pairs, sum all durations
  // SHIFT_BASED: match punches to assigned shift window

  // ── Auto-Processing ──
  autoMarkAbsentIfNoPunch  Boolean @default(true)
  autoHalfDayEnabled       Boolean @default(true)  // auto classify based on threshold
  autoAbsentAfterDays      Int     @default(0)      // 0 = disabled; N = mark absent after N days no punch
  regularizationWindowDays Int     @default(7)      // days after which regularization locked

  // ── Rounding Rules ──
  workingHoursRounding       RoundingStrategy @default(NONE)
  punchTimeRounding          PunchRounding    @default(NONE)
  punchTimeRoundingDirection RoundingDirection @default(NEAREST)

  // ── Exception Handling ──
  ignoreLateOnLeaveDay Boolean @default(true)  // don't flag late if partial leave
  ignoreLateOnHoliday  Boolean @default(true)  // working on holiday = no late flag
  ignoreLateOnWeekOff  Boolean @default(true)  // working on week-off = no late flag

  // ── Capture Requirements (defaults — location/shift can override) ──
  selfieRequired    Boolean @default(false)
  gpsRequired       Boolean @default(false)
  missingPunchAlert Boolean @default(true)

  company   Company @relation(fields: [companyId], references: [id], onDelete: Cascade)
  createdBy String?  // userId
  updatedBy String?  // userId
  createdAt DateTime @default(now())
  updatedAt DateTime @updatedAt

  @@map("attendance_rules")
}
```

**New fields (16 added):** `maxLateCheckInMinutes`, `lateDeductionType`, `lateDeductionValue`, `earlyExitDeductionType`, `earlyExitDeductionValue`, `punchMode`, `autoMarkAbsentIfNoPunch`, `autoHalfDayEnabled`, `autoAbsentAfterDays`, `regularizationWindowDays`, `workingHoursRounding`, `punchTimeRounding`, `punchTimeRoundingDirection`, `ignoreLateOnLeaveDay`, `ignoreLateOnHoliday`, `ignoreLateOnWeekOff`.

**Removed:** `shiftStartTime`, `shiftEndTime` (never belonged here — shifts in Shift Master).

**Renamed:** `earlyExitMinutes` → `earlyExitToleranceMinutes`, `lateArrivalsAllowed` → `lateArrivalsAllowedPerMonth`.

---

### 4.6 OvertimeRule (Enhanced — payroll-linked engine)

```prisma
model OvertimeRule {
  id        String   @id @default(cuid())
  companyId String   @unique

  // ── Eligibility ──
  eligibleTypeIds Json? // string[] of employee type IDs; null = all eligible

  // ── Calculation Basis ──
  calculationBasis  OTCalculationBasis @default(AFTER_SHIFT)
  thresholdMinutes  Int     @default(30) // min extra minutes before OT counts
  minimumOtMinutes  Int     @default(30) // min OT minutes to be recorded (separate from threshold)
  includeBreaksInOT Boolean @default(false)

  // ── Rate Multipliers ──
  weekdayMultiplier    Decimal  @default(1.5)  @db.Decimal(3, 2)
  weekendMultiplier    Decimal?                @db.Decimal(3, 2) // null = use weekday rate
  holidayMultiplier    Decimal?                @db.Decimal(3, 2) // null = use weekday rate
  nightShiftMultiplier Decimal?                @db.Decimal(3, 2) // null = use weekday rate

  // ── Caps ──
  dailyCapHours   Decimal? @db.Decimal(4, 1)
  weeklyCapHours  Decimal? @db.Decimal(5, 1)
  monthlyCapHours Decimal? @db.Decimal(5, 1)
  enforceCaps     Boolean  @default(false)     // true = hard block; false = warn only
  maxContinuousOtHours Decimal? @db.Decimal(4, 1) // safety/compliance limit

  // ── Approval & Payroll ──
  approvalRequired   Boolean @default(true)
  autoIncludePayroll Boolean @default(false)

  // ── Comp-Off ──
  compOffEnabled    Boolean @default(false)
  compOffExpiryDays Int?    // days before comp-off lapses; null = no expiry

  // ── Rounding ──
  roundingStrategy RoundingStrategy @default(NONE)

  company          Company           @relation(fields: [companyId], references: [id], onDelete: Cascade)
  overtimeRequests OvertimeRequest[]
  createdBy        String?           // userId
  updatedBy        String?           // userId
  createdAt        DateTime          @default(now())
  updatedAt        DateTime          @updatedAt

  @@map("overtime_rules")
}
```

**New fields:** `calculationBasis`, `minimumOtMinutes`, `includeBreaksInOT`, `weekendMultiplier`, `holidayMultiplier`, `nightShiftMultiplier`, `dailyCapHours`, `enforceCaps`, `maxContinuousOtHours`, `compOffEnabled`, `compOffExpiryDays`, `roundingStrategy`.

**Removed:** Single `rateMultiplier` (replaced by granular multipliers).

**Moved here:** `approvalRequired` (from SystemControls — OT approval is business logic, not a system gate).

---

### 4.7 OvertimeRequest (New — approval workflow)

```prisma
model OvertimeRequest {
  id                 String   @id @default(cuid())
  attendanceRecordId String   @unique
  companyId          String
  employeeId         String

  date              DateTime              @db.Date
  requestedHours    Decimal               @db.Decimal(5, 2)
  appliedMultiplier Decimal               @db.Decimal(3, 2)
  multiplierSource  OTMultiplierSource    // WEEKDAY, WEEKEND, HOLIDAY, NIGHT_SHIFT
  calculatedAmount  Decimal?              @db.Decimal(15, 2) // computed on approval

  status            OvertimeRequestStatus @default(PENDING)
  requestedBy       String                // userId
  approvedBy        String?               // userId
  approvalNotes     String?
  approvedAt        DateTime?

  compOffGranted    Boolean @default(false) // true = comp-off instead of cash

  attendanceRecord AttendanceRecord @relation(fields: [attendanceRecordId], references: [id], onDelete: Cascade)
  company          Company          @relation(fields: [companyId], references: [id], onDelete: Cascade)
  employee         Employee         @relation(fields: [employeeId], references: [id])

  createdAt DateTime @default(now())
  updatedAt DateTime @updatedAt

  @@index([companyId, status])
  @@index([employeeId, date])
  @@map("overtime_requests")
}
```

---

### 4.8 ESSConfig (Cleaned — access gates only)

```prisma
model ESSConfig {
  id        String   @id @default(cuid())
  companyId String   @unique

  // ── Payroll & Tax ──
  viewPayslips        Boolean @default(true)
  downloadPayslips    Boolean @default(true)
  downloadForm16      Boolean @default(true)
  viewSalaryStructure Boolean @default(false)
  itDeclaration       Boolean @default(true)

  // ── Leave ──
  leaveApplication Boolean @default(true)
  leaveBalanceView Boolean @default(true)
  leaveCancellation Boolean @default(false)

  // ── Attendance ──
  attendanceView           Boolean @default(true)
  attendanceRegularization Boolean @default(false)
  viewShiftSchedule        Boolean @default(false)
  shiftSwapRequest         Boolean @default(false)
  wfhRequest               Boolean @default(false)

  // ── Profile & Documents ──
  profileUpdate     Boolean @default(false)
  documentUpload    Boolean @default(false)
  employeeDirectory Boolean @default(false)
  viewOrgChart      Boolean @default(false)

  // ── Financial ──
  reimbursementClaims Boolean @default(false)
  loanApplication    Boolean @default(false)
  assetView          Boolean @default(false)

  // ── Performance & Development ──
  performanceGoals   Boolean @default(false)
  appraisalAccess    Boolean @default(false)
  feedback360        Boolean @default(false)
  trainingEnrollment Boolean @default(false)

  // ── Support & Communication ──
  helpDesk            Boolean @default(false)
  grievanceSubmission Boolean @default(false)
  holidayCalendar     Boolean @default(true)
  policyDocuments     Boolean @default(false)
  announcementBoard   Boolean @default(false)

  // ── Manager Self-Service (MSS) ──
  mssViewTeam           Boolean @default(false)
  mssApproveLeave       Boolean @default(false)
  mssApproveAttendance  Boolean @default(false)
  mssViewTeamAttendance Boolean @default(false)

  // ── Mobile Behavior ──
  mobileOfflinePunch     Boolean         @default(false)
  mobileSyncRetryMinutes Int             @default(5)
  mobileLocationAccuracy LocationAccuracy @default(HIGH)

  company   Company @relation(fields: [companyId], references: [id], onDelete: Cascade)
  createdBy String?  // userId
  updatedBy String?  // userId
  createdAt DateTime @default(now())
  updatedAt DateTime @updatedAt

  @@map("ess_configs")
}
```

**Removed:** `loginMethod`, `passwordMinLength`, `passwordComplexity`, `sessionTimeoutMinutes`, `mfaRequired` — all moved to SystemControls.

**Added:** `downloadPayslips`, `viewSalaryStructure`, `leaveCancellation`, `viewShiftSchedule`, `shiftSwapRequest`, `wfhRequest`, `viewOrgChart`, `announcementBoard`, MSS section (4 fields), mobile behavior section (3 fields).

---

### 4.9 AttendanceRecord (Enhanced — resolved snapshots)

New fields added to existing model:

```prisma
model AttendanceRecord {
  // ── Existing fields (unchanged) ──
  id                    String           @id @default(cuid())
  employeeId            String
  date                  DateTime         @db.Date
  shiftId               String?
  punchIn               DateTime?
  punchOut              DateTime?
  workedHours           Decimal?         @db.Decimal(5, 2)
  status                AttendanceStatus @default(PRESENT)
  source                AttendanceSource @default(MANUAL)
  isLate                Boolean          @default(false)
  lateMinutes           Int?
  isEarlyExit           Boolean          @default(false)
  earlyMinutes          Int?
  overtimeHours         Decimal?         @db.Decimal(5, 2)
  remarks               String?
  locationId            String?
  checkInLatitude       Float?
  checkInLongitude      Float?
  checkOutLatitude      Float?
  checkOutLongitude     Float?
  checkInPhotoUrl       String?          @db.Text
  checkOutPhotoUrl      String?          @db.Text
  geoStatus             String?
  isRegularized         Boolean          @default(false)
  regularizedAt         DateTime?
  regularizedBy         String?
  regularizationReason  String?
  leaveRequestId        String?
  companyId             String
  createdAt             DateTime         @default(now())
  updatedAt             DateTime         @updatedAt

  // ── NEW: Resolved Policy Snapshot ──
  appliedGracePeriodMinutes    Int?
  appliedFullDayThresholdHours Decimal?   @db.Decimal(4, 2)
  appliedHalfDayThresholdHours Decimal?   @db.Decimal(4, 2)
  appliedBreakDeductionMinutes Int?
  appliedPunchMode             PunchMode?
  appliedLateDeduction         Decimal?   @db.Decimal(10, 2)
  appliedEarlyExitDeduction    Decimal?   @db.Decimal(10, 2)

  // ── NEW: Resolution Trace ──
  resolutionTrace Json?
  // { field: "SHIFT" | "LOCATION" | "ATTENDANCE_RULE" | "SYSTEM_DEFAULT" }

  // ── NEW: Evaluation Context ──
  evaluationContext Json?
  // { isHoliday, isWeekOff, holidayName?, rosterPattern? }

  // ── NEW: Status Reasoning ──
  finalStatusReason String?
  // e.g., "Late by 22min (full day worked)", "Half day: 4.5h < 8h threshold"

  // ── Relations ──
  employee         Employee           @relation(fields: [employeeId], references: [id], onDelete: Cascade)
  shift            CompanyShift?      @relation("AttendanceShift", fields: [shiftId], references: [id])
  location         Location?          @relation("AttendanceLocation", fields: [locationId], references: [id])
  company          Company            @relation(fields: [companyId], references: [id], onDelete: Cascade)
  overrides        AttendanceOverride[]
  overtimeRequest  OvertimeRequest?

  @@unique([employeeId, date])
  @@index([companyId, date])
  @@index([companyId, status])
  @@map("attendance_records")
}
```

---

### 4.10 Statutory & Tax Models — UNCHANGED

`PFConfig`, `ESIConfig`, `PTConfig`, `GratuityConfig`, `BonusConfig`, `LWFConfig`, `TaxConfig`, `BankConfig` — all remain exactly as currently implemented. These are the best-implemented configuration models and require no changes.

---

### 4.11 FeatureToggle Model — REMOVED

The `FeatureToggle` model and all associated code will be deleted. See [Section 11](#11-systems-removed).

---

## 5. Screen-wise Field Definitions & API Contracts

This is the single source of truth for every configuration screen. Both web and mobile implement from these specs with identical field names and groupings.

### Shared Frontend Patterns (Both Platforms)

1. **Field naming:** Frontend form state uses exact backend field names. No mapping layer.
2. **Nullable override pattern:** For shift override fields, use a "Use Default" checkbox. Checked = `null` (inherit). Unchecked = editable input.
3. **Save behavior:** Single save button per screen. Dirty tracking via `hasChanges` state.
4. **Validation:** Frontend validates types/ranges. Backend Zod schema is source of truth.
5. **Error display:** Web: `showApiError(err)`. Mobile: toast (never `Alert.alert`).

---

### Screen 1: Company Settings

**API:** `GET /company/settings` | `PATCH /company/settings`
**Permission:** `company:read` | `company:update`
**Model:** CompanySettings

| Section | Field | Type | Control | Default |
|---------|-------|------|---------|---------|
| **Locale** | currency | CurrencyCode | Select | INR |
| | language | LanguageCode | Select | en |
| | timezone | String | Select (IANA) | Asia/Kolkata |
| | dateFormat | String | Select | DD/MM/YYYY |
| | timeFormat | TimeFormat | Select | TWELVE_HOUR |
| | numberFormat | String | Select | en-IN |
| **Compliance** | indiaCompliance | Boolean | Toggle | true |
| | gdprMode | Boolean | Toggle | false |
| | auditTrail | Boolean | Toggle | true |
| **Integrations** | bankIntegration | Boolean | Toggle | false |
| | razorpayEnabled | Boolean | Toggle | false |
| | emailNotifications | Boolean | Toggle | true |
| | whatsappNotifications | Boolean | Toggle | false |
| | biometricIntegration | Boolean | Toggle | false |
| | eSignIntegration | Boolean | Toggle | false |

**Total: 16 fields. Identical on web and mobile.**

---

### Screen 2: System Controls

**API:** `GET /company/controls` | `PATCH /company/controls`
**Permission:** `company:read` | `company:update`
**Model:** SystemControls

| Section | Field | Type | Control | Default |
|---------|-------|------|---------|---------|
| **Module Enablement** | attendanceEnabled | Boolean | Toggle | true |
| | leaveEnabled | Boolean | Toggle | true |
| | payrollEnabled | Boolean | Toggle | true |
| | essEnabled | Boolean | Toggle | true |
| | performanceEnabled | Boolean | Toggle | false |
| | recruitmentEnabled | Boolean | Toggle | false |
| | trainingEnabled | Boolean | Toggle | false |
| | mobileAppEnabled | Boolean | Toggle | true |
| | aiChatbotEnabled | Boolean | Toggle | false |
| **Production** | ncEditMode | Boolean | Toggle | false |
| | loadUnload | Boolean | Toggle | false |
| | cycleTime | Boolean | Toggle | false |
| **Payroll** | payrollLock | Boolean | Toggle | true |
| | backdatedEntryControl | Boolean | Toggle | false |
| **Leave** | leaveCarryForward | Boolean | Toggle | true |
| | compOffEnabled | Boolean | Toggle | false |
| | halfDayLeaveEnabled | Boolean | Toggle | true |
| **Security** | mfaRequired | Boolean | Toggle | false |
| | sessionTimeoutMinutes | Int | Number | 30 |
| | maxConcurrentSessions | Int | Number | 3 |
| | passwordMinLength | Int | Number | 8 |
| | passwordComplexity | Boolean | Toggle | true |
| | accountLockThreshold | Int | Number | 5 |
| | accountLockDurationMinutes | Int | Number | 30 |
| **Audit** | auditLogRetentionDays | Int | Select | 365 |

**Total: 25 fields. Identical on web and mobile.**

---

### Screen 3: Attendance Rules

**API:** `GET /hr/attendance/rules` | `PATCH /hr/attendance/rules`
**Permission:** `hr:read` | `hr:update`
**Model:** AttendanceRule

| Section | Field | Type | Control | Default |
|---------|-------|------|---------|---------|
| **Time & Boundary** | dayBoundaryTime | String | Time Input | 00:00 |
| **Grace & Tolerance** | gracePeriodMinutes | Int | Number | 15 |
| | earlyExitToleranceMinutes | Int | Number | 15 |
| | maxLateCheckInMinutes | Int | Number | 240 |
| **Day Thresholds** | halfDayThresholdHours | Decimal | Number | 4.00 |
| | fullDayThresholdHours | Decimal | Number | 8.00 |
| **Late Tracking** | lateArrivalsAllowedPerMonth | Int | Number | 3 |
| **Deduction Rules** | lopAutoDeduct | Boolean | Toggle | true |
| | lateDeductionType | DeductionType | Select | NONE |
| | lateDeductionValue | Decimal? | Number | — |
| | earlyExitDeductionType | DeductionType | Select | NONE |
| | earlyExitDeductionValue | Decimal? | Number | — |
| **Punch Interpretation** | punchMode | PunchMode | Select | FIRST_LAST |
| **Auto-Processing** | autoMarkAbsentIfNoPunch | Boolean | Toggle | true |
| | autoHalfDayEnabled | Boolean | Toggle | true |
| | autoAbsentAfterDays | Int | Number | 0 |
| | regularizationWindowDays | Int | Number | 7 |
| **Rounding** | workingHoursRounding | RoundingStrategy | Select | NONE |
| | punchTimeRounding | PunchRounding | Select | NONE |
| | punchTimeRoundingDirection | RoundingDirection | Select | NEAREST |
| **Exception Handling** | ignoreLateOnLeaveDay | Boolean | Toggle | true |
| | ignoreLateOnHoliday | Boolean | Toggle | true |
| | ignoreLateOnWeekOff | Boolean | Toggle | true |
| **Capture** | selfieRequired | Boolean | Toggle | false |
| | gpsRequired | Boolean | Toggle | false |
| | missingPunchAlert | Boolean | Toggle | true |

**Total: 26 fields. Identical on web and mobile.**

**Conditional visibility:** `lateDeductionValue` visible only when `lateDeductionType` != NONE. Same for `earlyExitDeductionValue`.

---

### Screen 4: Shift Master (CRUD + Detail)

**API:** CRUD on `/company/shifts` + `/company/shifts/:id/breaks`
**Permission:** `company:read` | `company:create` | `company:update` | `company:delete`
**Models:** CompanyShift + ShiftBreak

#### List View

| Column | Field |
|--------|-------|
| Name | name |
| Type | shiftType (badge: DAY/NIGHT/FLEXIBLE) |
| Timing | startTime — endTime |
| Cross-Day | isCrossDay (badge if true) |
| Employees | count of assigned employees |
| Actions | Edit / Delete |

#### Create/Edit Form

| Section | Field | Type | Control | Default |
|---------|-------|------|---------|---------|
| **Core** | name | String | Text | — |
| | shiftType | ShiftType | Select | DAY |
| | startTime | String | Time Input | 09:00 |
| | endTime | String | Time Input | 17:00 |
| | isCrossDay | Boolean | Toggle | false |
| **Policy Overrides** | gracePeriodMinutes | Int? | Nullable Number | null |
| _(label: "Leave empty to use company defaults")_ | earlyExitToleranceMinutes | Int? | Nullable Number | null |
| | halfDayThresholdHours | Decimal? | Nullable Number | null |
| | fullDayThresholdHours | Decimal? | Nullable Number | null |
| | maxLateCheckInMinutes | Int? | Nullable Number | null |
| | minWorkingHoursForOT | Decimal? | Nullable Number | null |
| **Capture Overrides** | requireSelfie | Boolean? | Tri-state | null |
| | requireGPS | Boolean? | Tri-state | null |
| | allowedSources | DeviceType[] | Multi-select | [] |
| **Behavior** | noShuffle | Boolean | Toggle | false |
| | autoClockOutMinutes | Int? | Nullable Number | null |

#### Break Sub-form (inline)

| Field | Type | Control | Default |
|-------|------|---------|---------|
| name | String | Text | — |
| type | BreakType | Select | FIXED |
| startTime | String? | Time Input | — |
| duration | Int | Number (min) | 30 |
| isPaid | Boolean | Toggle | false |

#### API Contract

```
GET    /company/shifts                        → { data: CompanyShift[] }
GET    /company/shifts/:id                    → { data: CompanyShift & { breaks: ShiftBreak[] } }
POST   /company/shifts                        → { data: CompanyShift }
PATCH  /company/shifts/:id                    → { data: CompanyShift }
DELETE /company/shifts/:id                    → { message: "Shift deleted" }

GET    /company/shifts/:id/breaks             → { data: ShiftBreak[] }
POST   /company/shifts/:id/breaks             → { data: ShiftBreak }
PATCH  /company/shifts/:id/breaks/:breakId    → { data: ShiftBreak }
DELETE /company/shifts/:id/breaks/:breakId    → { message: "Break deleted" }
```

---

### Screen 5: Overtime Rules

**API:** `GET /hr/overtime-rules` | `PATCH /hr/overtime-rules`
**Permission:** `hr:read` | `hr:update`
**Model:** OvertimeRule

| Section | Field | Type | Control | Default |
|---------|-------|------|---------|---------|
| **Eligibility** | eligibleTypeIds | String[]? | Multi-select | null (all) |
| **Calculation** | calculationBasis | OTCalculationBasis | Select | AFTER_SHIFT |
| | thresholdMinutes | Int | Number | 30 |
| | minimumOtMinutes | Int | Number | 30 |
| | includeBreaksInOT | Boolean | Toggle | false |
| **Rate Multipliers** | weekdayMultiplier | Decimal | Number (0.01) | 1.50 |
| | weekendMultiplier | Decimal? | Nullable Number | null |
| | holidayMultiplier | Decimal? | Nullable Number | null |
| | nightShiftMultiplier | Decimal? | Nullable Number | null |
| **Caps** | dailyCapHours | Decimal? | Nullable Number | null |
| | weeklyCapHours | Decimal? | Nullable Number | null |
| | monthlyCapHours | Decimal? | Nullable Number | null |
| | enforceCaps | Boolean | Toggle | false |
| | maxContinuousOtHours | Decimal? | Nullable Number | null |
| **Approval & Payroll** | approvalRequired | Boolean | Toggle | true |
| | autoIncludePayroll | Boolean | Toggle | false |
| **Comp-Off** | compOffEnabled | Boolean | Toggle | false |
| | compOffExpiryDays | Int? | Nullable Number | null |
| **Rounding** | roundingStrategy | RoundingStrategy | Select | NONE |

**Total: 20 fields. Identical on web and mobile.**

**OT Requests** (separate list screen, not config):
```
GET   /hr/overtime-requests?status=PENDING    → { data: OvertimeRequest[], meta: pagination }
PATCH /hr/overtime-requests/:id/approve       → { data: OvertimeRequest }
PATCH /hr/overtime-requests/:id/reject        → { data: OvertimeRequest }
```

---

### Screen 6: ESS Configuration

**API:** `GET /hr/ess-config` | `PATCH /hr/ess-config`
**Permission:** `hr:read` | `hr:update`
**Model:** ESSConfig

| Section | Field | Type | Control | Default |
|---------|-------|------|---------|---------|
| **Payroll & Tax** | viewPayslips | Boolean | Toggle | true |
| | downloadPayslips | Boolean | Toggle | true |
| | downloadForm16 | Boolean | Toggle | true |
| | viewSalaryStructure | Boolean | Toggle | false |
| | itDeclaration | Boolean | Toggle | true |
| **Leave** | leaveApplication | Boolean | Toggle | true |
| | leaveBalanceView | Boolean | Toggle | true |
| | leaveCancellation | Boolean | Toggle | false |
| **Attendance** | attendanceView | Boolean | Toggle | true |
| | attendanceRegularization | Boolean | Toggle | false |
| | viewShiftSchedule | Boolean | Toggle | false |
| | shiftSwapRequest | Boolean | Toggle | false |
| | wfhRequest | Boolean | Toggle | false |
| **Profile & Documents** | profileUpdate | Boolean | Toggle | false |
| | documentUpload | Boolean | Toggle | false |
| | employeeDirectory | Boolean | Toggle | false |
| | viewOrgChart | Boolean | Toggle | false |
| **Financial** | reimbursementClaims | Boolean | Toggle | false |
| | loanApplication | Boolean | Toggle | false |
| | assetView | Boolean | Toggle | false |
| **Performance** | performanceGoals | Boolean | Toggle | false |
| | appraisalAccess | Boolean | Toggle | false |
| | feedback360 | Boolean | Toggle | false |
| | trainingEnrollment | Boolean | Toggle | false |
| **Support** | helpDesk | Boolean | Toggle | false |
| | grievanceSubmission | Boolean | Toggle | false |
| | holidayCalendar | Boolean | Toggle | true |
| | policyDocuments | Boolean | Toggle | false |
| | announcementBoard | Boolean | Toggle | false |
| **Manager Self-Service** | mssViewTeam | Boolean | Toggle | false |
| | mssApproveLeave | Boolean | Toggle | false |
| | mssApproveAttendance | Boolean | Toggle | false |
| | mssViewTeamAttendance | Boolean | Toggle | false |
| **Mobile Behavior** | mobileOfflinePunch | Boolean | Toggle | false |
| | mobileSyncRetryMinutes | Int | Number | 5 |
| | mobileLocationAccuracy | LocationAccuracy | Select | HIGH |

**Total: 36 fields. Identical on web and mobile.**

---

### Screens 7 & 8: Statutory Config + Tax Config — UNCHANGED

No changes to screens, fields, or API contracts. Both have 100% parity.

---

## 6. Enforcement Engine

### 6.1 Architecture

Three enforcement layers, applied at different points in the request lifecycle:

```
1. MIDDLEWARE ENFORCEMENT (Express middleware)
   → Runs BEFORE controller
   → Checks: System Controls (module enablement), security policies
   → Fails fast: 403 if module disabled

2. SERVICE ENFORCEMENT (Business logic)
   → Runs INSIDE service methods
   → Checks: ESS config, location constraints
   → Fails with descriptive error if constraint violated

3. CALCULATION ENGINE (Pure functions)
   → Runs DURING attendance/payroll processing
   → Resolves: policy chain, metrics, status
   → Returns deterministic results
```

### 6.2 Middleware: Module Enforcement

**File:** `src/shared/middleware/config-enforcement.middleware.ts`

```typescript
type ModuleKey = 'attendance' | 'leave' | 'payroll' | 'ess' | 'performance' | 'recruitment' | 'training';

export function requireModuleEnabled(module: ModuleKey) {
  return async (req: Request, res: Response, next: NextFunction) => {
    const controls = await getCachedSystemControls(req.companyId);
    const key = `${module}Enabled` as keyof SystemControls;
    if (!controls[key]) {
      throw ApiError.forbidden(`${module} module is not enabled for this company`);
    }
    next();
  };
}
```

**Applied to route groups:**
```typescript
// attendance.routes.ts
router.use(requireModuleEnabled('attendance'));

// leave.routes.ts
router.use(requireModuleEnabled('leave'));

// payroll.routes.ts
router.use(requireModuleEnabled('payroll'));

// ess.routes.ts
router.use(requireModuleEnabled('ess'));
```

### 6.3 Middleware: ESS Feature Enforcement

```typescript
export function requireESSFeature(feature: keyof ESSConfig) {
  return async (req: Request, res: Response, next: NextFunction) => {
    const essConfig = await getCachedESSConfig(req.companyId);
    if (essConfig[feature] === false) {
      throw ApiError.forbidden(`${feature} is not enabled for employee self-service`);
    }
    next();
  };
}
```

**Applied to ESS routes:**
```typescript
router.post('/ess/apply-leave', requireESSFeature('leaveApplication'), controller.applyLeave);
router.post('/ess/regularize', requireESSFeature('attendanceRegularization'), controller.regularize);
router.get('/ess/my-payslips', requireESSFeature('viewPayslips'), controller.getMyPayslips);
router.get('/ess/my-leave-balance', requireESSFeature('leaveBalanceView'), controller.getLeaveBalance);
router.post('/ess/upload-document', requireESSFeature('documentUpload'), controller.uploadDocument);
// ... all ESS endpoints gated by their corresponding config flag
```

### 6.4 Service: Location Validation

**File:** `src/shared/services/location-validator.service.ts`

Called during attendance punch processing:

```typescript
export async function validateLocationConstraints(
  locationId: string | null,
  punch: {
    latitude?: number;
    longitude?: number;
    source: AttendanceSource;
    selfieUrl?: string;
  }
): Promise<{ valid: boolean; reason?: string }> {
  if (!locationId) return { valid: true };
  const location = await getCachedLocation(locationId);
  if (!location) return { valid: true };

  // 1. Geo-fence check (fail fast)
  if (location.geoEnabled && punch.latitude && punch.longitude) {
    const distance = haversineDistance(
      { lat: location.geoLat!, lng: location.geoLng! },
      { lat: punch.latitude, lng: punch.longitude }
    );
    if (distance > location.geoRadius!) {
      return { valid: false, reason: `Outside geo-fence: ${distance}m > ${location.geoRadius}m` };
    }
  }

  // 2. Device restriction check
  if (location.allowedDevices.length > 0) {
    if (!location.allowedDevices.includes(punch.source as DeviceType)) {
      return { valid: false, reason: `Device ${punch.source} not allowed at ${location.name}` };
    }
  }

  // 3. Selfie requirement (location level)
  if (location.requireSelfie === true && !punch.selfieUrl) {
    return { valid: false, reason: 'Selfie required at this location' };
  }

  // 4. Live location requirement
  if (location.requireLiveLocation === true && (!punch.latitude || !punch.longitude)) {
    return { valid: false, reason: 'Live location required at this location' };
  }

  return { valid: true };
}
```

### 6.5 Service: Policy Resolution

**File:** `src/shared/services/policy-resolver.service.ts`

Resolves the effective policy for an attendance record by walking the configuration chain:

```typescript
interface ResolvedPolicy {
  gracePeriodMinutes: number;
  earlyExitToleranceMinutes: number;
  halfDayThresholdHours: number;
  fullDayThresholdHours: number;
  maxLateCheckInMinutes: number;
  selfieRequired: boolean;
  gpsRequired: boolean;
  punchMode: PunchMode;
  workingHoursRounding: RoundingStrategy;
  breakDeductionMinutes: number;
}

interface ResolutionTrace {
  [field: string]: 'SHIFT' | 'LOCATION' | 'ATTENDANCE_RULE' | 'SYSTEM_DEFAULT';
}

interface EvaluationContext {
  employeeId: string;
  shiftId: string | null;
  locationId: string | null;
  date: Date;
  isHoliday: boolean;
  isWeekOff: boolean;
  holidayName?: string;
  rosterPattern?: string;
}

export async function resolvePolicy(
  companyId: string,
  context: EvaluationContext
): Promise<{ policy: ResolvedPolicy; trace: ResolutionTrace }> {
  const shift = context.shiftId ? await getCachedShift(context.shiftId) : null;
  const location = context.locationId ? await getCachedLocation(context.locationId) : null;
  const rules = await getCachedAttendanceRules(companyId);
  const trace: ResolutionTrace = {};

  // Generic resolver: returns first non-null value and records source
  function resolve<T>(field: string, ...sources: Array<{ value: T | null | undefined; label: string }>): T {
    for (const s of sources) {
      if (s.value !== null && s.value !== undefined) {
        trace[field] = s.label as any;
        return s.value;
      }
    }
    throw new Error(`No resolved value for ${field}`);
  }

  // Policy fields: shift → rules → defaults
  const policy: ResolvedPolicy = {
    gracePeriodMinutes: resolve('gracePeriod',
      { value: shift?.gracePeriodMinutes, label: 'SHIFT' },
      { value: rules.gracePeriodMinutes, label: 'ATTENDANCE_RULE' },
      { value: 15, label: 'SYSTEM_DEFAULT' }),

    earlyExitToleranceMinutes: resolve('earlyExitTolerance',
      { value: shift?.earlyExitToleranceMinutes, label: 'SHIFT' },
      { value: rules.earlyExitToleranceMinutes, label: 'ATTENDANCE_RULE' },
      { value: 15, label: 'SYSTEM_DEFAULT' }),

    halfDayThresholdHours: resolve('halfDayThreshold',
      { value: shift?.halfDayThresholdHours, label: 'SHIFT' },
      { value: rules.halfDayThresholdHours, label: 'ATTENDANCE_RULE' },
      { value: 4, label: 'SYSTEM_DEFAULT' }),

    fullDayThresholdHours: resolve('fullDayThreshold',
      { value: shift?.fullDayThresholdHours, label: 'SHIFT' },
      { value: rules.fullDayThresholdHours, label: 'ATTENDANCE_RULE' },
      { value: 8, label: 'SYSTEM_DEFAULT' }),

    maxLateCheckInMinutes: resolve('maxLateCheckIn',
      { value: shift?.maxLateCheckInMinutes, label: 'SHIFT' },
      { value: rules.maxLateCheckInMinutes, label: 'ATTENDANCE_RULE' },
      { value: 240, label: 'SYSTEM_DEFAULT' }),

    // Constraint fields: location → shift → rules → defaults
    selfieRequired: resolve('selfieRequired',
      { value: location?.requireSelfie, label: 'LOCATION' },
      { value: shift?.requireSelfie, label: 'SHIFT' },
      { value: rules.selfieRequired, label: 'ATTENDANCE_RULE' },
      { value: false, label: 'SYSTEM_DEFAULT' }),

    gpsRequired: resolve('gpsRequired',
      { value: location?.requireLiveLocation, label: 'LOCATION' },
      { value: shift?.requireGPS, label: 'SHIFT' },
      { value: rules.gpsRequired, label: 'ATTENDANCE_RULE' },
      { value: false, label: 'SYSTEM_DEFAULT' }),

    punchMode: resolve('punchMode',
      { value: rules.punchMode, label: 'ATTENDANCE_RULE' },
      { value: PunchMode.FIRST_LAST, label: 'SYSTEM_DEFAULT' }),

    workingHoursRounding: resolve('workingHoursRounding',
      { value: rules.workingHoursRounding, label: 'ATTENDANCE_RULE' },
      { value: RoundingStrategy.NONE, label: 'SYSTEM_DEFAULT' }),

    breakDeductionMinutes: 0, // calculated below
  };

  // Calculate total unpaid break minutes from shift
  if (shift) {
    const breaks = await getCachedShiftBreaks(shift.id);
    policy.breakDeductionMinutes = breaks
      .filter(b => !b.isPaid)
      .reduce((sum, b) => sum + b.duration, 0);
    trace.breakDeduction = 'SHIFT';
  } else {
    trace.breakDeduction = 'SYSTEM_DEFAULT';
  }

  return { policy, trace };
}
```

---

## 7. Attendance Status Resolver

**File:** `src/shared/services/attendance-status-resolver.service.ts`

The deterministic engine that produces final attendance status from resolved policy + punch data.

### Input

```typescript
interface StatusInput {
  punchIn: Date | null;
  punchOut: Date | null;
  shift: { startTime: string; endTime: string; isCrossDay: boolean } | null;
  policy: ResolvedPolicy;
  context: EvaluationContext;
  rules: AttendanceRule;
}
```

### Output

```typescript
interface StatusResult {
  status: AttendanceStatus;
  finalStatusReason: string;
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

### Logic Flow

```
1. No punch → check holiday/weekoff → HOLIDAY | WEEK_OFF | ABSENT

2. Calculate raw worked minutes (punchOut - punchIn)

3. Deduct unpaid breaks → net worked minutes

4. Apply rounding → net worked hours

5. Determine late arrival:
   → delay = punchIn - shiftStart
   → if delay > gracePeriod → isLate = true, lateMinutes = delay
   → if delay > maxLateCheckIn → ABSENT (too late)

6. Apply exception handling:
   → if isHoliday && ignoreLateOnHoliday → suppress late
   → if isWeekOff && ignoreLateOnWeekOff → suppress late
   → if onLeave && ignoreLateOnLeaveDay → suppress late

7. Determine early exit:
   → earlyBy = shiftEnd - punchOut
   → if earlyBy > earlyExitTolerance → isEarlyExit = true

8. Classify status:
   → workedHours >= fullDayThreshold → PRESENT (or LATE if late)
   → workedHours >= halfDayThreshold → HALF_DAY
   → isEarlyExit → EARLY_EXIT
   → below halfDayThreshold → LOP (if lopAutoDeduct) or HALF_DAY

9. Calculate OT (basic):
   → if workedHours > fullDayThreshold → overtimeHours = difference

10. Calculate deductions:
    → lateDeductionType + isLate → appliedLateDeduction
    → earlyExitDeductionType + isEarlyExit → appliedEarlyExitDeduction

11. Return StatusResult with all computed fields
```

---

## 8. Runtime Flow

Complete flow when an employee punches in:

```
Step 1: VALIDATE SYSTEM CONTROLS
  → requireModuleEnabled('attendance')
  → If disabled → 403 "Attendance module not enabled"

Step 2: VALIDATE LOCATION CONSTRAINTS (fail fast)
  → validateLocationConstraints(locationId, punchData)
  → Geo-fence check → reject if outside
  → Device check → reject if source not allowed
  → Selfie/GPS check → reject if missing required data

Step 3: FETCH SHIFT
  → Get employee's assigned shift (or company default)
  → Load shift breaks

Step 4: BUILD EVALUATION CONTEXT
  → { employeeId, shiftId, locationId, date, isHoliday, isWeekOff, holidayName }

Step 5: RESOLVE POLICY
  → Walk chain: shift → rules → defaults
  → Record resolution trace (field-level source tracking)
  → Compute break deductions

Step 6: RESOLVE ATTENDANCE STATUS
  → Calculate worked hours with rounding
  → Determine late/early with grace periods
  → Apply exception handling
  → Classify: PRESENT / ABSENT / HALF_DAY / LATE / EARLY_EXIT / LOP
  → Calculate deductions

Step 7: PROCESS OVERTIME (if applicable)
  → Check eligibility (employee type)
  → Apply threshold + minimum minutes
  → Select multiplier (weekday/weekend/holiday/night)
  → Apply caps (daily/weekly/monthly)
  → If approvalRequired → create OvertimeRequest (PENDING)
  → If autoIncludePayroll && !approvalRequired → auto-approve

Step 8: PERSIST ATTENDANCE RECORD
  → Store computed fields (workedHours, status, isLate, etc.)
  → Store resolved policy snapshot (applied* fields)
  → Store resolutionTrace JSON
  → Store evaluationContext JSON
  → Store finalStatusReason

Step 9: TRIGGER EVENTS
  → Missing punch alert (if punch-out missing at shift end + buffer)
  → Late arrival notification
  → Absence alert
```

---

## 9. Caching Strategy

All config lookups use Redis with 30-minute TTL (existing pattern):

```
Cache Keys:
  config:system-controls:{companyId}
  config:attendance-rules:{companyId}
  config:overtime-rules:{companyId}
  config:ess-config:{companyId}
  config:company-settings:{companyId}
  config:location:{locationId}
  config:shift:{shiftId}
  config:shift-breaks:{shiftId}

Invalidation:
  → On ANY config update endpoint, invalidate the relevant cache key
  → Use existing createCompanyCacheKey() / createTenantCacheKey() helpers
```

---

## 10. Migration Strategy

### Phase Order (Dependency-Aware)

```
Phase 1: SCHEMA CREATION (no breaking changes)
  → Create new Prisma models: CompanySettings, SystemControls, ShiftBreak, OvertimeRequest
  → Add new enums
  → Add new fields to existing models: Location, CompanyShift, AttendanceRule, AttendanceRecord
  → Run: prisma migrate dev
  → Timeline: 1 migration file

Phase 2: DATA MIGRATION (backfill from JSON blobs)
  → Script: Migrate Company.preferences → CompanySettings rows
  → Script: Migrate Company.systemControls → SystemControls rows
  → Script: Migrate CompanyShift.downtimeSlots → ShiftBreak rows
  → Script: Set defaults for all new nullable fields
  → Script: Rename CompanyShift.fromTime/toTime → startTime/endTime
  → Timeline: 1 migration script

Phase 3: BACKEND API UPDATES (backwards compatible)
  → Update Zod validators to match new models
  → Update services to read/write new typed models instead of JSON blobs
  → Add enforcement middleware to routes
  → Add policy resolver, status resolver, location validator services
  → Keep old JSON fields readable during transition
  → Timeline: Service-by-service updates

Phase 4: FRONTEND ALIGNMENT
  → Update web and mobile screens to use standardized field names
  → Remove all phantom fields from web
  → Add missing fields to mobile
  → Implement nullable override UI pattern for shift forms
  → Both platforms implement from Section 5 screen specs
  → Timeline: Screen-by-screen updates

Phase 5: FEATURE TOGGLE REMOVAL
  → Delete: FeatureToggle model from schema
  → Delete: feature-toggle.service.ts, controller.ts, routes.ts
  → Delete: shared/constants/feature-toggles.ts (catalogue)
  → Delete: Frontend FeatureToggleScreen (web + mobile)
  → Delete: API client methods for feature toggles
  → Delete: useHasFeature hooks from auth stores
  → Remove: feature_toggles table via migration

Phase 6: CLEANUP
  → Remove deprecated JSON fields: Company.preferences, Company.systemControls
  → Remove CompanyShift.downtimeSlots
  → Remove CompanyShift.fromTime, CompanyShift.toTime (replaced by startTime, endTime)
  → Final migration to drop columns
```

### Backwards Compatibility

During migration, the backend supports both old and new paths:
- Old `GET /company/controls` → reads JSON blob (existing behavior)
- New `GET /company/controls` → reads SystemControls model (new behavior)
- Frontend migration happens per-screen, one at a time
- No big-bang deployment required

### Data Migration Script Pattern

```typescript
async function migrateCompanyPreferencesToSettings() {
  const companies = await platformPrisma.company.findMany({
    select: { id: true, preferences: true }
  });
  for (const company of companies) {
    const prefs = (company.preferences as Record<string, any>) ?? {};
    await platformPrisma.companySettings.upsert({
      where: { companyId: company.id },
      create: {
        companyId: company.id,
        currency: prefs.currency ?? 'INR',
        language: prefs.language ?? 'en',
        timezone: prefs.timezone ?? 'Asia/Kolkata',
        dateFormat: prefs.dateFormat ?? 'DD/MM/YYYY',
        timeFormat: prefs.timeFormat ?? 'TWELVE_HOUR',
        numberFormat: prefs.numberFormat ?? 'en-IN',
        indiaCompliance: prefs.indiaCompliance ?? true,
        emailNotifications: prefs.emailNotif ?? true,
        whatsappNotifications: prefs.whatsapp ?? false,
        biometricIntegration: prefs.biometric ?? false,
        bankIntegration: prefs.bankIntegration ?? false,
        eSignIntegration: prefs.eSign ?? false,
        // remaining fields use model defaults
      },
      update: {}, // don't overwrite if already migrated
    });
  }
}
```

Similar scripts for SystemControls (from systemControls JSON) and ShiftBreaks (from downtimeSlots JSON).

---

## 11. Systems Removed

### Feature Toggles — Complete Removal

**Why:** Feature toggles were never enforced anywhere in the system. The `useHasFeature()` hook existed but was never called. The 10 toggle definitions duplicated settings already present in Company Settings and ESS Config. Module enablement is now handled by `SystemControls.*Enabled` flags.

**Files to delete:**
- `avy-erp-backend/src/core/feature-toggle/feature-toggle.service.ts`
- `avy-erp-backend/src/core/feature-toggle/feature-toggle.controller.ts`
- `avy-erp-backend/src/core/feature-toggle/feature-toggle.routes.ts`
- `avy-erp-backend/src/shared/constants/feature-toggles.ts`
- `web-system-app/src/features/company-admin/FeatureToggleScreen.tsx`
- `mobile-app/src/features/company-admin/feature-toggle-screen.tsx`
- `mobile-app/src/app/(app)/company/feature-toggles.tsx`
- Feature toggle API methods from both frontend API clients
- Feature toggle React Query hooks from both frontends
- `useHasFeature()` from both auth stores

**Schema:** Drop `feature_toggles` table.

**Routes:** Remove `/feature-toggles/*` route group and navigation manifest entry.

### Company.preferences JSON — Replaced

Replaced by typed `CompanySettings` model. JSON field deprecated in Phase 3, dropped in Phase 6.

### Company.systemControls JSON — Replaced

Replaced by typed `SystemControls` model. JSON field deprecated in Phase 3, dropped in Phase 6.

### CompanyShift.downtimeSlots JSON — Replaced

Replaced by typed `ShiftBreak` model. JSON field deprecated in Phase 3, dropped in Phase 6.

### ESS Config Security Fields — Moved

`loginMethod`, `passwordMinLength`, `passwordComplexity`, `sessionTimeoutMinutes`, `mfaRequired` moved from ESSConfig to SystemControls. These are system-wide security policies, not ESS-specific settings.

---

## Appendix: System Defaults

Hardcoded fallback values used when the entire resolution chain returns null:

```typescript
export const SYSTEM_DEFAULTS = {
  gracePeriodMinutes: 15,
  earlyExitToleranceMinutes: 15,
  maxLateCheckInMinutes: 240,
  halfDayThresholdHours: 4,
  fullDayThresholdHours: 8,
  selfieRequired: false,
  gpsRequired: false,
  punchMode: 'FIRST_LAST',
  workingHoursRounding: 'NONE',
  punchTimeRounding: 'NONE',
  punchTimeRoundingDirection: 'NEAREST',
  breakDeductionMinutes: 0,
  autoMarkAbsentIfNoPunch: true,
  minimumOtMinutes: 30,
} as const;
```

These are compile-time constants. They are the absolute last resort and should rarely be reached since `AttendanceRule` always has defaults.

---

## Appendix: Edge Case Rules

### B.1 Cross-Day Attendance Date Rule

When a night shift spans midnight, which calendar date does the attendance belong to?

```
RULE:
  If shift.isCrossDay = true:
    attendanceDate = date of shift START (the date the employee began working)
  Else:
    attendanceDate = calendar date based on dayBoundaryTime
```

**Example:**
- Night shift: 22:00 → 06:00, employee punches in at 22:15 on March 30
- Attendance record date = **March 30** (shift start date)
- The 06:00 punch-out on March 31 is still part of the March 30 record

This rule is deterministic and avoids ambiguity. The `dayBoundaryTime` field is only used for non-cross-day shifts where punch times might straddle midnight (e.g., a late clock-out at 00:15 for a day shift ending at 23:30).

### B.2 Punch Sequence Validation

Before processing, validate the punch sequence based on the configured `punchMode`:

```typescript
function validatePunchSequence(
  punches: Array<{ time: Date; direction: 'IN' | 'OUT' | 'UNKNOWN' }>,
  mode: PunchMode
): { valid: boolean; resolvedIn: Date | null; resolvedOut: Date | null; reason?: string } {

  switch (mode) {
    case 'FIRST_LAST':
      // First punch = IN, last punch = OUT, ignore everything in between
      return {
        valid: true,
        resolvedIn: punches[0]?.time ?? null,
        resolvedOut: punches.length > 1 ? punches[punches.length - 1].time : null,
      };

    case 'EVERY_PAIR':
      // Enforce alternating IN/OUT sequence
      // If sequence is invalid (IN→IN or OUT→OUT), flag for regularization
      // Sum durations of all valid pairs
      // Return total as workedMinutes
      break;

    case 'SHIFT_BASED':
      // Match punches to assigned shift window
      // Closest punch to shift start = IN
      // Closest punch to shift end = OUT
      break;
  }
}
```

**Invalid sequence handling:** Do not reject — mark as `INCOMPLETE` and flag for regularization. The system should be forgiving of biometric/device errors.

### B.3 Missing Punch (INCOMPLETE Status)

When `punchIn` exists but `punchOut` is missing at end of day:

```
RULE:
  1. If shift.autoClockOutMinutes is set:
     → Auto-generate punchOut = shiftEnd + autoClockOutMinutes
     → Set source = 'MANUAL' (system-generated)
     → Mark status based on auto-generated record

  2. If autoClockOut not configured:
     → Set status = INCOMPLETE
     → Trigger missingPunchAlert (if enabled)
     → Record remains INCOMPLETE until:
       a) Employee clocks out (late punch-out)
       b) Employee submits regularization request
       c) Admin manually resolves
       d) autoAbsentAfterDays threshold reached → flip to ABSENT
```

### B.4 Holiday + Work + OT Resolution

When an employee works on a declared holiday:

```
RULE:
  1. Attendance status = HOLIDAY (base status preserved)
  2. workedHours calculated normally from punches
  3. OT calculated using holidayMultiplier (or weekdayMultiplier if holiday multiplier is null)
  4. Late/early flags are suppressed (ignoreLateOnHoliday = true by default)
  5. OvertimeRequest created with multiplierSource = HOLIDAY
```

Same logic applies for `WEEK_OFF` — use weekendMultiplier for OT.

### B.5 Payroll Lock Enforcement

When `systemControls.payrollLock = true`:

```
RULE:
  Block all modifications to:
  → AttendanceRecords with date in a LOCKED payroll period
  → PayrollEntries in APPROVED or DISBURSED status
  → OvertimeRequests linked to locked attendance records

  Allow:
  → Viewing/reading locked data
  → Creating records for CURRENT (unlocked) period
```

Enforcement via service-level check:

```typescript
async function validatePayrollNotLocked(companyId: string, date: Date) {
  const controls = await getCachedSystemControls(companyId);
  if (!controls.payrollLock) return; // lock feature disabled

  const lockedRun = await findPayrollRunForDate(companyId, date);
  if (lockedRun && ['APPROVED', 'DISBURSED', 'ARCHIVED'].includes(lockedRun.status)) {
    throw ApiError.forbidden(`Payroll period is locked (${lockedRun.status}). Cannot modify attendance for ${date}.`);
  }
}
```

---

## Appendix: Company Creation Config Seeding

### C.1 Mandatory Seeding on Company Creation

When a new company is created (via tenant onboarding), ALL configuration models must be seeded with defaults. `SYSTEM_DEFAULTS` is a fallback only — seeded DB values are the primary runtime source.

```typescript
async function seedCompanyConfigs(companyId: string, industryType?: string) {
  const defaults = getIndustryDefaults(industryType);

  await Promise.all([
    prisma.companySettings.create({
      data: { companyId, ...defaults.settings }
    }),
    prisma.systemControls.create({
      data: { companyId, ...defaults.controls }
    }),
    prisma.attendanceRule.create({
      data: { companyId, ...defaults.attendanceRules }
    }),
    prisma.overtimeRule.create({
      data: { companyId, ...defaults.overtimeRules }
    }),
    prisma.eSSConfig.create({
      data: { companyId, ...defaults.essConfig }
    }),
  ]);
}
```

### C.2 Industry-Based Templates (Optional Enhancement)

Predefined templates based on company industry type:

| Industry | Attendance | OT | Shifts | Security |
|----------|-----------|-----|--------|----------|
| **Manufacturing** | Strict geo-fencing, biometric required, FIRST_LAST punch | Holiday 2x, enforceCaps=true | Multi-shift with cross-day | MFA optional |
| **IT/Services** | Flexible, GPS optional, FIRST_LAST punch | Standard 1.5x, no caps | Single day shift, flexible | MFA recommended |
| **Retail** | Geo-fencing, mobile GPS, SHIFT_BASED punch | Weekend 1.5x, holiday 2x | Rotating shifts | Standard |
| **Healthcare** | Strict, biometric+GPS, SHIFT_BASED punch | Night 2x, holiday 2.5x | Cross-day shifts | MFA required |

Templates are suggestions — all values are editable after creation.

---

## Appendix: Cache Versioning

### D.1 Version-Safe Cache Keys

To prevent stale cache reads after config updates, include a version component:

```typescript
function buildCacheKey(prefix: string, id: string, updatedAt: Date): string {
  const version = updatedAt.getTime();
  return `${prefix}:${id}:v${version}`;
}

// Usage:
const key = buildCacheKey('config:attendance-rules', companyId, rules.updatedAt);
```

**Alternative (simpler):** On every config update, explicitly delete the cache key. The next read will populate fresh data. This is the existing pattern and is sufficient for the update frequency of config data (rare updates, frequent reads).

**Recommendation:** Keep the existing invalidation-on-write pattern. Config updates are rare (daily at most), so version-keyed caching adds complexity without proportional benefit. Reserve version-keyed caching for high-frequency data if needed later.

---

## Appendix: Audit Fields

### E.1 createdBy / updatedBy on Config Models

All configuration models should track who made changes:

```prisma
// Add to: CompanySettings, SystemControls, AttendanceRule, OvertimeRule, ESSConfig
createdBy String?  // userId of creator
updatedBy String?  // userId of last modifier
```

These fields are populated from `req.user.id` in the controller layer. They enable audit trail queries like "who disabled MFA?" or "who changed the grace period?"

For `AttendanceRecord`, the existing `regularizedBy` field already serves this purpose for regularization. The record creator is tracked via `source` (MANUAL implies admin, BIOMETRIC/MOBILE_GPS implies employee).
