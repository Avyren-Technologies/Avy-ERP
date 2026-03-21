# AVY ERP Backend API Documentation — Part 2: HR Module

All endpoints are prefixed with `/api/v1/hr/` and require authentication + tenant middleware.

**Permission Model:** All HR endpoints use `requirePermissions()` with `hr:read`, `hr:create`, `hr:update`, or `hr:delete` as noted per endpoint.

---

## Table of Contents

1. [Org Structure](#1-org-structure)
2. [Employee Management](#2-employee-management)
3. [Attendance Management](#3-attendance-management)
4. [Leave Management](#4-leave-management)
5. [Payroll Configuration](#5-payroll-configuration)
6. [Payroll Run Engine](#6-payroll-run-engine)
7. [ESS / MSS & Workflows](#7-ess--mss--workflows)
8. [Performance Management](#8-performance-management)
9. [Offboarding & F&F](#9-offboarding--ff)
10. [Advanced HR](#10-advanced-hr)
11. [Transfers & Promotions](#11-transfers--promotions)

---

## 1. Org Structure

Source: `src/modules/hr/org-structure/`

### 1.1 Departments

| Method | Path | Permission | Description |
|--------|------|------------|-------------|
| GET | `/departments` | `hr:read` | List all departments |
| POST | `/departments` | `hr:create` | Create a department |
| GET | `/departments/:id` | `hr:read` | Get department by ID |
| PATCH | `/departments/:id` | `hr:update` | Update department |
| DELETE | `/departments/:id` | `hr:delete` | Delete department |

**POST/PATCH Request Body — `createDepartmentSchema`**

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `name` | string | Yes | 1–100 chars |
| `code` | string | Yes | 1–20 chars |
| `parentId` | string | No | Parent department ID (self-referencing hierarchy) |
| `headEmployeeId` | string | No | Department head employee ID |
| `costCentreCode` | string | No | Linked cost centre code |
| `status` | enum | No | `Active` \| `Inactive` (default: `Active`) |

PATCH accepts all fields as optional.

---

### 1.2 Designations

| Method | Path | Permission | Description |
|--------|------|------------|-------------|
| GET | `/designations` | `hr:read` | List all designations |
| POST | `/designations` | `hr:create` | Create a designation |
| GET | `/designations/:id` | `hr:read` | Get designation by ID |
| PATCH | `/designations/:id` | `hr:update` | Update designation |
| DELETE | `/designations/:id` | `hr:delete` | Delete designation |

**POST/PATCH Request Body — `createDesignationSchema`**

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `name` | string | Yes | 1–100 chars |
| `code` | string | Yes | 1–20 chars |
| `departmentId` | string | No | |
| `gradeId` | string | No | |
| `jobLevel` | enum | No | `L1` \| `L2` \| `L3` \| `L4` \| `L5` \| `L6` \| `L7` |
| `managerialFlag` | boolean | No | Default: `false` |
| `reportsTo` | string | No | Designation ID this reports to |
| `probationDays` | integer | No | Positive integer |
| `status` | enum | No | `Active` \| `Inactive` (default: `Active`) |

PATCH accepts all fields as optional.

---

### 1.3 Grades

| Method | Path | Permission | Description |
|--------|------|------------|-------------|
| GET | `/grades` | `hr:read` | List all grades |
| POST | `/grades` | `hr:create` | Create a grade |
| GET | `/grades/:id` | `hr:read` | Get grade by ID |
| PATCH | `/grades/:id` | `hr:update` | Update grade |
| DELETE | `/grades/:id` | `hr:delete` | Delete grade |

**POST/PATCH Request Body — `createGradeSchema`**

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `code` | string | Yes | 1–20 chars |
| `name` | string | Yes | 1–100 chars |
| `ctcMin` | number | No | Positive |
| `ctcMax` | number | No | Positive |
| `hraPercent` | number | No | 0–100 |
| `pfTier` | enum | No | `Applicable` \| `Not Applicable` \| `Optional` |
| `benefitFlags` | Record<string, boolean> | No | Key-value benefit flags |
| `probationMonths` | integer | No | Positive integer |
| `noticeDays` | integer | No | Positive integer |
| `status` | enum | No | `Active` \| `Inactive` (default: `Active`) |

PATCH accepts all fields as optional.

---

### 1.4 Employee Types

| Method | Path | Permission | Description |
|--------|------|------------|-------------|
| GET | `/employee-types` | `hr:read` | List all employee types |
| POST | `/employee-types` | `hr:create` | Create an employee type |
| GET | `/employee-types/:id` | `hr:read` | Get employee type by ID |
| PATCH | `/employee-types/:id` | `hr:update` | Update employee type |
| DELETE | `/employee-types/:id` | `hr:delete` | Delete employee type |

**POST/PATCH Request Body — `createEmployeeTypeSchema`**

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `name` | string | Yes | 1–100 chars |
| `code` | string | Yes | 1–20 chars |
| `pfApplicable` | boolean | Yes | |
| `esiApplicable` | boolean | Yes | |
| `ptApplicable` | boolean | Yes | |
| `gratuityEligible` | boolean | Yes | |
| `bonusEligible` | boolean | Yes | |
| `status` | enum | No | `Active` \| `Inactive` (default: `Active`) |

PATCH accepts all fields as optional.

---

### 1.5 Cost Centres

| Method | Path | Permission | Description |
|--------|------|------------|-------------|
| GET | `/cost-centres` | `hr:read` | List all cost centres |
| POST | `/cost-centres` | `hr:create` | Create a cost centre |
| GET | `/cost-centres/:id` | `hr:read` | Get cost centre by ID |
| PATCH | `/cost-centres/:id` | `hr:update` | Update cost centre |
| DELETE | `/cost-centres/:id` | `hr:delete` | Delete cost centre |

**POST/PATCH Request Body — `createCostCentreSchema`**

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `code` | string | Yes | 1–20 chars |
| `name` | string | Yes | 1–100 chars |
| `departmentId` | string | No | |
| `locationId` | string | No | |
| `annualBudget` | number | No | Positive |
| `glAccountCode` | string | No | General ledger account code |

PATCH accepts all fields as optional.

---

## 2. Employee Management

Source: `src/modules/hr/employee/`

### 2.1 Employee CRUD

| Method | Path | Permission | Description |
|--------|------|------------|-------------|
| GET | `/employees` | `hr:read` | List employees |
| POST | `/employees` | `hr:create` | Create employee |
| GET | `/employees/:id` | `hr:read` | Get employee by ID |
| PATCH | `/employees/:id` | `hr:update` | Update employee |
| PATCH | `/employees/:id/status` | `hr:update` | Update employee status |
| DELETE | `/employees/:id` | `hr:delete` | Delete (soft delete — sets status to EXITED) |

**POST Request Body — `createEmployeeSchema`**

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| **Personal** | | | |
| `firstName` | string | Yes | |
| `middleName` | string | No | |
| `lastName` | string | Yes | |
| `dateOfBirth` | string \| Date | Yes | ISO date |
| `gender` | enum | Yes | `MALE` \| `FEMALE` \| `NON_BINARY` \| `PREFER_NOT_TO_SAY` |
| `maritalStatus` | enum | No | `SINGLE` \| `MARRIED` \| `DIVORCED` \| `WIDOWED` |
| `bloodGroup` | string | No | |
| `fatherMotherName` | string | No | |
| `nationality` | string | No | Default: `Indian` |
| `religion` | string | No | |
| `category` | string | No | |
| `differentlyAbled` | boolean | No | |
| `disabilityType` | string | No | |
| `profilePhotoUrl` | string | No | |
| **Contact** | | | |
| `personalMobile` | string | Yes | Min 10 digits |
| `alternativeMobile` | string | No | |
| `personalEmail` | string | Yes | Valid email |
| `officialEmail` | string | No | Valid email |
| `currentAddress` | object | No | `{ line1, line2?, city, state, pin, country? }` |
| `permanentAddress` | object | No | Same as above |
| `emergencyContactName` | string | Yes | |
| `emergencyContactRelation` | string | Yes | |
| `emergencyContactMobile` | string | Yes | Min 10 digits |
| **Professional** | | | |
| `joiningDate` | string \| Date | Yes | ISO date |
| `employeeTypeId` | string | Yes | |
| `departmentId` | string | Yes | |
| `designationId` | string | Yes | |
| `gradeId` | string | No | |
| `reportingManagerId` | string | No | |
| `functionalManagerId` | string | No | |
| `workType` | enum | No | `ON_SITE` \| `REMOTE` \| `HYBRID` |
| `shiftId` | string | No | |
| `costCentreId` | string | No | |
| `locationId` | string | No | |
| `noticePeriodDays` | integer | No | |
| **Salary** | | | |
| `annualCtc` | number | No | Positive |
| `salaryStructure` | Record | No | Arbitrary key-value |
| `paymentMode` | enum | No | `NEFT` \| `IMPS` \| `CHEQUE` |
| **Bank** | | | |
| `bankAccountNumber` | string | No | |
| `bankIfscCode` | string | No | |
| `bankName` | string | No | |
| `bankBranch` | string | No | |
| `accountType` | enum | No | `SAVINGS` \| `CURRENT` |
| **Statutory IDs** | | | |
| `panNumber` | string | No | |
| `aadhaarNumber` | string | No | |
| `uan` | string | No | Universal Account Number (PF) |
| `esiIpNumber` | string | No | |
| `passportNumber` | string | No | |
| `passportExpiry` | string \| Date | No | |
| `drivingLicence` | string | No | |
| `voterId` | string | No | |
| `pran` | string | No | |

PATCH accepts all fields as optional.

**PATCH `/employees/:id/status` — `updateEmployeeStatusSchema`**

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `status` | enum | Yes | `ACTIVE` \| `PROBATION` \| `CONFIRMED` \| `ON_NOTICE` \| `SUSPENDED` \| `EXITED` |
| `lastWorkingDate` | string \| Date | No | |
| `exitReason` | string | No | |

---

### 2.2 Nominees

| Method | Path | Permission | Description |
|--------|------|------------|-------------|
| GET | `/employees/:id/nominees` | `hr:read` | List nominees for employee |
| POST | `/employees/:id/nominees` | `hr:create` | Add nominee |
| PATCH | `/employees/:id/nominees/:nid` | `hr:update` | Update nominee |
| DELETE | `/employees/:id/nominees/:nid` | `hr:delete` | Delete nominee |

**POST/PATCH Request Body — `createNomineeSchema`**

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `name` | string | Yes | |
| `relation` | string | Yes | |
| `dateOfBirth` | string \| Date | No | |
| `sharePercent` | number | No | 0–100 |
| `aadhaar` | string | No | |
| `pan` | string | No | |
| `address` | object | No | `{ line1, line2?, city, state, pin, country? }` |

PATCH accepts all fields as optional.

---

### 2.3 Education

| Method | Path | Permission | Description |
|--------|------|------------|-------------|
| GET | `/employees/:id/education` | `hr:read` | List education records |
| POST | `/employees/:id/education` | `hr:create` | Add education record |
| PATCH | `/employees/:id/education/:eid` | `hr:update` | Update education record |
| DELETE | `/employees/:id/education/:eid` | `hr:delete` | Delete education record |

**POST/PATCH Request Body — `createEducationSchema`**

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `qualification` | string | Yes | |
| `degree` | string | No | |
| `institution` | string | No | |
| `university` | string | No | |
| `yearOfPassing` | integer | No | |
| `marks` | string | No | |
| `certificateUrl` | string | No | |

PATCH accepts all fields as optional.

---

### 2.4 Previous Employment

| Method | Path | Permission | Description |
|--------|------|------------|-------------|
| GET | `/employees/:id/previous-employment` | `hr:read` | List previous employment |
| POST | `/employees/:id/previous-employment` | `hr:create` | Add previous employment |
| PATCH | `/employees/:id/previous-employment/:pid` | `hr:update` | Update record |
| DELETE | `/employees/:id/previous-employment/:pid` | `hr:delete` | Delete record |

**POST/PATCH Request Body — `createPrevEmploymentSchema`**

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `employerName` | string | Yes | |
| `designation` | string | No | |
| `lastCtc` | number | No | Positive |
| `joinDate` | string \| Date | No | |
| `leaveDate` | string \| Date | No | |
| `reason` | string | No | |
| `experienceLetterUrl` | string | No | |
| `relievingLetterUrl` | string | No | |
| `previousPfAccount` | string | No | |

PATCH accepts all fields as optional.

---

### 2.5 Documents

| Method | Path | Permission | Description |
|--------|------|------------|-------------|
| GET | `/employees/:id/documents` | `hr:read` | List documents |
| POST | `/employees/:id/documents` | `hr:create` | Add document |
| PATCH | `/employees/:id/documents/:did` | `hr:update` | Update document |
| DELETE | `/employees/:id/documents/:did` | `hr:delete` | Delete document |

**POST/PATCH Request Body — `createDocumentSchema`**

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `documentType` | string | Yes | |
| `documentNumber` | string | No | |
| `expiryDate` | string \| Date | No | |
| `fileUrl` | string | Yes | |
| `fileName` | string | No | |

PATCH accepts all fields as optional.

---

### 2.6 Timeline

| Method | Path | Permission | Description |
|--------|------|------------|-------------|
| GET | `/employees/:id/timeline` | `hr:read` | Get employee timeline events |

No request body (read-only).

---

## 3. Attendance Management

Source: `src/modules/hr/attendance/`

### 3.1 Attendance Records

| Method | Path | Permission | Description |
|--------|------|------------|-------------|
| GET | `/attendance` | `hr:read` | List attendance records |
| POST | `/attendance` | `hr:create` | Create attendance record |
| GET | `/attendance/summary` | `hr:read` | Get attendance summary |
| GET | `/attendance/:id` | `hr:read` | Get record by ID |
| PATCH | `/attendance/:id` | `hr:update` | Update attendance record |

**POST/PATCH Request Body — `createAttendanceSchema`**

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `employeeId` | string | Yes | |
| `date` | string | Yes | ISO date |
| `shiftId` | string | No | |
| `punchIn` | string | No | ISO datetime |
| `punchOut` | string | No | ISO datetime |
| `status` | enum | Yes | `PRESENT` \| `ABSENT` \| `HALF_DAY` \| `LATE` \| `ON_LEAVE` \| `HOLIDAY` \| `WEEK_OFF` \| `LOP` |
| `source` | enum | Yes | `BIOMETRIC` \| `FACE_RECOGNITION` \| `MOBILE_GPS` \| `WEB_PORTAL` \| `MANUAL` \| `IOT` \| `SMART_CARD` |
| `remarks` | string | No | |
| `locationId` | string | No | |

PATCH accepts all fields as optional.

---

### 3.2 Attendance Rules

| Method | Path | Permission | Description |
|--------|------|------------|-------------|
| GET | `/attendance/rules` | `hr:read` | Get attendance rules (singleton) |
| PATCH | `/attendance/rules` | `hr:update` | Update attendance rules |

**PATCH Request Body — `attendanceRulesSchema`**

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `dayBoundaryTime` | string | No | |
| `halfDayThresholdHours` | number | No | 0–24 |
| `fullDayThresholdHours` | number | No | 0–24 |
| `lateArrivalsAllowed` | integer | No | Min 0 |
| `gracePeriodMinutes` | integer | No | Min 0 |
| `earlyExitMinutes` | integer | No | Min 0 |
| `lopAutoDeduct` | boolean | No | |
| `missingPunchAlert` | boolean | No | |
| `selfieRequired` | boolean | No | |
| `gpsRequired` | boolean | No | |

---

### 3.3 Overrides / Regularization

| Method | Path | Permission | Description |
|--------|------|------------|-------------|
| GET | `/attendance/overrides` | `hr:read` | List override requests |
| POST | `/attendance/overrides` | `hr:create` | Create override request |
| PATCH | `/attendance/overrides/:id` | `hr:update` | Approve/reject override |

**POST Request Body — `createOverrideSchema`**

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `attendanceRecordId` | string | Yes | |
| `issueType` | enum | Yes | `MISSING_PUNCH_IN` \| `MISSING_PUNCH_OUT` \| `ABSENT_OVERRIDE` \| `LATE_OVERRIDE` \| `NO_PUNCH` |
| `correctedPunchIn` | string | No | ISO datetime |
| `correctedPunchOut` | string | No | ISO datetime |
| `reason` | string | Yes | |

**PATCH Request Body — `approveOverrideSchema`**

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `status` | enum | Yes | `APPROVED` \| `REJECTED` |

---

### 3.4 Holiday Calendar

| Method | Path | Permission | Description |
|--------|------|------------|-------------|
| GET | `/holidays` | `hr:read` | List holidays |
| POST | `/holidays` | `hr:create` | Create holiday |
| POST | `/holidays/clone` | `hr:create` | Clone holidays from one year to another |
| PATCH | `/holidays/:id` | `hr:update` | Update holiday |
| DELETE | `/holidays/:id` | `hr:delete` | Delete holiday |

**POST Request Body — `createHolidaySchema`**

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `name` | string | Yes | 1–100 chars |
| `date` | string | Yes | ISO date |
| `type` | enum | Yes | `NATIONAL` \| `REGIONAL` \| `COMPANY` \| `OPTIONAL` \| `RESTRICTED` |
| `branchIds` | string[] | No | Applicable branch/location IDs |
| `year` | integer | Yes | 2000–2100 |
| `description` | string | No | |
| `isOptional` | boolean | No | |
| `maxOptionalSlots` | integer | No | Positive |

**POST `/holidays/clone` — `cloneHolidaysSchema`**

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `fromYear` | integer | Yes | 2000–2100 |
| `toYear` | integer | Yes | 2000–2100 |

PATCH accepts all fields as optional.

---

### 3.5 Rosters

| Method | Path | Permission | Description |
|--------|------|------------|-------------|
| GET | `/rosters` | `hr:read` | List rosters |
| POST | `/rosters` | `hr:create` | Create roster |
| PATCH | `/rosters/:id` | `hr:update` | Update roster |
| DELETE | `/rosters/:id` | `hr:delete` | Delete roster |

**POST/PATCH Request Body — `createRosterSchema`**

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `name` | string | Yes | 1–100 chars |
| `pattern` | enum | Yes | `MON_FRI` \| `MON_SAT` \| `MON_SAT_ALT` \| `CUSTOM` |
| `weekOff1` | string | No | Day of week |
| `weekOff2` | string | No | Day of week |
| `applicableTypeIds` | string[] | No | Employee type IDs |
| `effectiveFrom` | string | Yes | ISO date |
| `isDefault` | boolean | No | |

PATCH accepts all fields as optional.

---

### 3.6 Overtime Rules

| Method | Path | Permission | Description |
|--------|------|------------|-------------|
| GET | `/overtime-rules` | `hr:read` | Get overtime rules (singleton) |
| PATCH | `/overtime-rules` | `hr:update` | Update overtime rules |

**PATCH Request Body — `overtimeRulesSchema`**

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `eligibleTypeIds` | string[] | No | Employee type IDs |
| `rateMultiplier` | number | Yes | 0.1–10 |
| `thresholdMinutes` | integer | No | Min 0 |
| `monthlyCap` | number | No | Min 0 |
| `weeklyCap` | number | No | Min 0 |
| `autoIncludePayroll` | boolean | No | |
| `approvalRequired` | boolean | No | |

---

## 4. Leave Management

Source: `src/modules/hr/leave/`

### 4.1 Leave Types

| Method | Path | Permission | Description |
|--------|------|------------|-------------|
| GET | `/leave-types` | `hr:read` | List leave types |
| POST | `/leave-types` | `hr:create` | Create leave type |
| GET | `/leave-types/:id` | `hr:read` | Get leave type by ID |
| PATCH | `/leave-types/:id` | `hr:update` | Update leave type |
| DELETE | `/leave-types/:id` | `hr:delete` | Delete leave type |

**POST/PATCH Request Body — `createLeaveTypeSchema`**

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `name` | string | Yes | 1–100 chars |
| `code` | string | Yes | 1–10 chars |
| `category` | enum | Yes | `PAID` \| `UNPAID` \| `COMPENSATORY` \| `STATUTORY` |
| `annualEntitlement` | number | Yes | Positive |
| `accrualFrequency` | enum | No | `MONTHLY` \| `QUARTERLY` \| `ANNUAL` \| `PRO_RATA` \| `UPFRONT` |
| `accrualDay` | integer | No | 1–31 |
| `carryForwardAllowed` | boolean | No | Default: `false` |
| `maxCarryForwardDays` | number | No | Min 0 |
| `encashmentAllowed` | boolean | No | Default: `false` |
| `maxEncashableDays` | number | No | Min 0 |
| `encashmentRate` | string | No | |
| `applicableTypeIds` | string[] | No | Employee type IDs |
| `applicableGender` | string | No | |
| `probationRestricted` | boolean | No | Default: `false` |
| `minTenureDays` | integer | No | Min 0 |
| `minAdvanceNotice` | integer | No | Min 0 |
| `minDaysPerApplication` | number | No | Min 0 |
| `maxConsecutiveDays` | integer | No | Min 1 |
| `allowHalfDay` | boolean | No | Default: `true` |
| `weekendSandwich` | boolean | No | Default: `false` |
| `holidaySandwich` | boolean | No | Default: `false` |
| `documentRequired` | boolean | No | Default: `false` |
| `documentAfterDays` | integer | No | Min 1 |
| `lopOnExcess` | boolean | No | Default: `true` |

PATCH accepts all fields as optional.

---

### 4.2 Leave Policies

| Method | Path | Permission | Description |
|--------|------|------------|-------------|
| GET | `/leave-policies` | `hr:read` | List leave policies |
| POST | `/leave-policies` | `hr:create` | Create leave policy |
| PATCH | `/leave-policies/:id` | `hr:update` | Update leave policy |
| DELETE | `/leave-policies/:id` | `hr:delete` | Delete leave policy |

**POST/PATCH Request Body — `createLeavePolicySchema`**

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `leaveTypeId` | string | Yes | |
| `assignmentLevel` | enum | Yes | `company` \| `department` \| `designation` \| `grade` \| `employeeType` \| `individual` |
| `assignmentId` | string | No | ID of the assignment target |
| `overrides` | Record<string, any> | No | Policy overrides |

PATCH accepts all fields as optional.

---

### 4.3 Leave Balances

| Method | Path | Permission | Description |
|--------|------|------------|-------------|
| GET | `/leave-balances` | `hr:read` | List leave balances |
| POST | `/leave-balances/adjust` | `hr:update` | Adjust leave balance |
| POST | `/leave-balances/initialize` | `hr:create` | Initialize balances for employee/year |

**POST `/leave-balances/adjust` — `adjustBalanceSchema`**

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `employeeId` | string | Yes | |
| `leaveTypeId` | string | Yes | |
| `year` | integer | Yes | 2000–2100 |
| `action` | enum | Yes | `credit` \| `debit` |
| `days` | number | Yes | Positive |
| `reason` | string | Yes | 1–500 chars |

**POST `/leave-balances/initialize` — `initializeBalancesSchema`**

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `employeeId` | string | Yes | |
| `year` | integer | Yes | 2000–2100 |

---

### 4.4 Leave Requests

| Method | Path | Permission | Description |
|--------|------|------------|-------------|
| GET | `/leave-requests` | `hr:read` | List leave requests |
| POST | `/leave-requests` | `hr:create` | Create leave request |
| GET | `/leave-requests/:id` | `hr:read` | Get leave request by ID |
| PATCH | `/leave-requests/:id/approve` | `hr:update` | Approve leave request |
| PATCH | `/leave-requests/:id/reject` | `hr:update` | Reject leave request |
| PATCH | `/leave-requests/:id/cancel` | `hr:update` | Cancel leave request |

**POST Request Body — `createLeaveRequestSchema`**

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `employeeId` | string | Yes | |
| `leaveTypeId` | string | Yes | |
| `fromDate` | string | Yes | ISO date |
| `toDate` | string | Yes | ISO date |
| `days` | number | Yes | Positive |
| `isHalfDay` | boolean | No | Default: `false` |
| `halfDayType` | enum | No | `FIRST_HALF` \| `SECOND_HALF` |
| `reason` | string | Yes | 1–1000 chars |

**PATCH `/approve` — `approveRequestSchema`**

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `note` | string | No | Max 500 chars |

**PATCH `/reject` — `rejectRequestSchema`**

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `note` | string | Yes | 1–500 chars |

---

### 4.5 Leave Summary

| Method | Path | Permission | Description |
|--------|------|------------|-------------|
| GET | `/leave/summary` | `hr:read` | Get leave summary dashboard |

---

## 5. Payroll Configuration

Source: `src/modules/hr/payroll/`

### 5.1 Salary Components

| Method | Path | Permission | Description |
|--------|------|------------|-------------|
| GET | `/salary-components` | `hr:read` | List salary components |
| POST | `/salary-components` | `hr:create` | Create salary component |
| GET | `/salary-components/:id` | `hr:read` | Get component by ID |
| PATCH | `/salary-components/:id` | `hr:update` | Update component |
| DELETE | `/salary-components/:id` | `hr:delete` | Delete component |

**POST/PATCH Request Body — `createSalaryComponentSchema`**

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `name` | string | Yes | |
| `code` | string | Yes | |
| `type` | enum | Yes | `EARNING` \| `DEDUCTION` \| `EMPLOYER_CONTRIBUTION` |
| `calculationMethod` | enum | No | `FIXED` \| `PERCENT_OF_BASIC` \| `PERCENT_OF_GROSS` \| `FORMULA` (default: `FIXED`) |
| `formula` | string | No | Custom formula expression |
| `formulaValue` | number | No | |
| `taxable` | enum | No | `FULLY_TAXABLE` \| `PARTIALLY_EXEMPT` \| `FULLY_EXEMPT` (default: `FULLY_TAXABLE`) |
| `exemptionSection` | string | No | IT Act section |
| `exemptionLimit` | number | No | |
| `pfInclusion` | boolean | No | Default: `false` |
| `esiInclusion` | boolean | No | Default: `false` |
| `bonusInclusion` | boolean | No | Default: `false` |
| `gratuityInclusion` | boolean | No | Default: `false` |
| `showOnPayslip` | boolean | No | Default: `true` |
| `payslipOrder` | integer | No | Display order on payslip |
| `isActive` | boolean | No | Default: `true` |

PATCH accepts all fields as optional.

---

### 5.2 Salary Structures

| Method | Path | Permission | Description |
|--------|------|------------|-------------|
| GET | `/salary-structures` | `hr:read` | List salary structures |
| POST | `/salary-structures` | `hr:create` | Create salary structure |
| GET | `/salary-structures/:id` | `hr:read` | Get structure by ID |
| PATCH | `/salary-structures/:id` | `hr:update` | Update structure |
| DELETE | `/salary-structures/:id` | `hr:delete` | Delete structure |

**POST/PATCH Request Body — `createSalaryStructureSchema`**

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `name` | string | Yes | |
| `code` | string | Yes | |
| `applicableGradeIds` | string[] | No | |
| `applicableDesignationIds` | string[] | No | |
| `applicableTypeIds` | string[] | No | |
| `components` | array | Yes | Min 1 item. Each: `{ componentId: string, calculationMethod: enum, value?: number, formula?: string }` |
| `ctcBasis` | enum | No | `CTC` \| `TAKE_HOME` (default: `CTC`) |
| `isActive` | boolean | No | Default: `true` |

**Component object schema:**

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `componentId` | string | Yes | |
| `calculationMethod` | enum | Yes | `FIXED` \| `PERCENT_OF_BASIC` \| `PERCENT_OF_GROSS` \| `FORMULA` |
| `value` | number | No | |
| `formula` | string | No | |

PATCH accepts all fields as optional.

---

### 5.3 Employee Salary

| Method | Path | Permission | Description |
|--------|------|------------|-------------|
| GET | `/employee-salaries` | `hr:read` | List employee salaries |
| POST | `/employee-salaries` | `hr:create` | Assign salary to employee |
| GET | `/employee-salaries/:id` | `hr:read` | Get employee salary by ID |
| PATCH | `/employee-salaries/:id` | `hr:update` | Update employee salary |

**POST Request Body — `createEmployeeSalarySchema`**

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `employeeId` | string | Yes | |
| `structureId` | string | No | Salary structure ID |
| `annualCtc` | number | Yes | Positive |
| `components` | Record<string, number> | No | `{ componentCode: amount }` |
| `effectiveFrom` | string | Yes | ISO date |

**PATCH Request Body — `updateEmployeeSalarySchema`**

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `annualCtc` | number | No | Positive |
| `components` | Record<string, number> | No | |
| `effectiveFrom` | string | No | |
| `structureId` | string | No | |

---

### 5.4 Statutory Configs

#### PF Config (Singleton)

| Method | Path | Permission | Description |
|--------|------|------------|-------------|
| GET | `/payroll/pf-config` | `hr:read` | Get PF configuration |
| PATCH | `/payroll/pf-config` | `hr:update` | Update PF configuration |

**PATCH Request Body — `pfConfigSchema`**

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `employeeRate` | number | No | 0–100% |
| `employerEpfRate` | number | No | 0–100% |
| `employerEpsRate` | number | No | 0–100% |
| `employerEdliRate` | number | No | 0–100% |
| `adminChargeRate` | number | No | 0–100% |
| `wageCeiling` | number | No | Min 0 |
| `vpfEnabled` | boolean | No | |
| `excludedComponents` | string[] | No | Component codes to exclude |

#### ESI Config (Singleton)

| Method | Path | Permission | Description |
|--------|------|------------|-------------|
| GET | `/payroll/esi-config` | `hr:read` | Get ESI configuration |
| PATCH | `/payroll/esi-config` | `hr:update` | Update ESI configuration |

**PATCH Request Body — `esiConfigSchema`**

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `employeeRate` | number | No | 0–100% |
| `employerRate` | number | No | 0–100% |
| `wageCeiling` | number | No | Min 0 |
| `excludedWages` | string[] | No | |

#### PT Configs (State-wise)

| Method | Path | Permission | Description |
|--------|------|------------|-------------|
| GET | `/payroll/pt-configs` | `hr:read` | List Professional Tax configs |
| POST | `/payroll/pt-configs` | `hr:create` | Create PT config for a state |
| PATCH | `/payroll/pt-configs/:id` | `hr:update` | Update PT config |
| DELETE | `/payroll/pt-configs/:id` | `hr:delete` | Delete PT config |

**POST/PATCH Request Body — `createPTConfigSchema`**

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `state` | string | Yes | |
| `slabs` | array | Yes | Min 1 slab. Each: `{ fromAmount: number, toAmount: number, taxAmount: number }` |
| `frequency` | enum | No | `MONTHLY` \| `SEMI_ANNUAL` (default: `MONTHLY`) |
| `registrationNumber` | string | No | |

PATCH accepts all fields as optional.

#### Gratuity Config (Singleton)

| Method | Path | Permission | Description |
|--------|------|------------|-------------|
| GET | `/payroll/gratuity-config` | `hr:read` | Get gratuity configuration |
| PATCH | `/payroll/gratuity-config` | `hr:update` | Update gratuity configuration |

**PATCH Request Body — `gratuityConfigSchema`**

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `formula` | string | No | |
| `baseSalary` | string | No | |
| `maxAmount` | number | No | Min 0 |
| `provisionMethod` | enum | No | `MONTHLY` \| `ACTUAL_AT_EXIT` |
| `trustExists` | boolean | No | |

#### Bonus Config (Singleton)

| Method | Path | Permission | Description |
|--------|------|------------|-------------|
| GET | `/payroll/bonus-config` | `hr:read` | Get bonus configuration |
| PATCH | `/payroll/bonus-config` | `hr:update` | Update bonus configuration |

**PATCH Request Body — `bonusConfigSchema`**

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `wageCeiling` | number | No | Min 0 |
| `minBonusPercent` | number | No | 0–100 |
| `maxBonusPercent` | number | No | 0–100 |
| `eligibilityDays` | integer | No | Min 0 |
| `calculationPeriod` | enum | No | `APR_MAR` \| `JAN_DEC` |

#### LWF Configs (State-wise)

| Method | Path | Permission | Description |
|--------|------|------------|-------------|
| GET | `/payroll/lwf-configs` | `hr:read` | List Labour Welfare Fund configs |
| POST | `/payroll/lwf-configs` | `hr:create` | Create LWF config |
| PATCH | `/payroll/lwf-configs/:id` | `hr:update` | Update LWF config |
| DELETE | `/payroll/lwf-configs/:id` | `hr:delete` | Delete LWF config |

**POST/PATCH Request Body — `createLWFConfigSchema`**

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `state` | string | Yes | |
| `employeeAmount` | number | Yes | Min 0 |
| `employerAmount` | number | Yes | Min 0 |
| `frequency` | enum | No | `MONTHLY` \| `SEMI_ANNUAL` \| `ANNUAL` (default: `MONTHLY`) |

PATCH accepts all fields as optional.

#### Bank Config (Singleton)

| Method | Path | Permission | Description |
|--------|------|------------|-------------|
| GET | `/payroll/bank-config` | `hr:read` | Get bank configuration |
| PATCH | `/payroll/bank-config` | `hr:update` | Update bank configuration |

**PATCH Request Body — `bankConfigSchema`**

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `bankName` | string | No | |
| `accountNumber` | string | No | |
| `ifscCode` | string | No | |
| `branchName` | string | No | |
| `paymentMode` | enum | No | `NEFT` \| `RTGS` \| `IMPS` |
| `fileFormat` | string | No | |
| `autoPushOnApproval` | boolean | No | |

#### Tax Config (Singleton)

| Method | Path | Permission | Description |
|--------|------|------------|-------------|
| GET | `/payroll/tax-config` | `hr:read` | Get tax configuration |
| PATCH | `/payroll/tax-config` | `hr:update` | Update tax configuration |

**PATCH Request Body — `taxConfigSchema`**

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `defaultRegime` | enum | No | `OLD` \| `NEW` |
| `oldRegimeSlabs` | array | No | Each: `{ fromAmount: number, toAmount: number, rate: number (0-100) }` |
| `newRegimeSlabs` | array | No | Same as above |
| `declarationDeadline` | string | No | ISO date |
| `surchargeRates` | array | No | Each: `{ threshold: number, rate: number (0-100) }` |
| `cessRate` | number | No | 0–100% |

---

### 5.5 Loan Policies

| Method | Path | Permission | Description |
|--------|------|------------|-------------|
| GET | `/loan-policies` | `hr:read` | List loan policies |
| POST | `/loan-policies` | `hr:create` | Create loan policy |
| GET | `/loan-policies/:id` | `hr:read` | Get loan policy by ID |
| PATCH | `/loan-policies/:id` | `hr:update` | Update loan policy |
| DELETE | `/loan-policies/:id` | `hr:delete` | Delete loan policy |

**POST/PATCH Request Body — `createLoanPolicySchema`**

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `name` | string | Yes | |
| `code` | string | Yes | |
| `maxAmount` | number | No | Positive |
| `maxTenureMonths` | integer | No | Positive |
| `interestRate` | number | No | 0–100 (default: `0`) |
| `emiCapPercent` | number | No | 0–100 (max % of salary for EMI) |
| `eligibilityTenureDays` | integer | No | Min 0 |
| `eligibleTypeIds` | string[] | No | Employee type IDs |
| `isActive` | boolean | No | Default: `true` |

PATCH accepts all fields as optional.

---

### 5.6 Loans

| Method | Path | Permission | Description |
|--------|------|------------|-------------|
| GET | `/loans` | `hr:read` | List loans |
| POST | `/loans` | `hr:create` | Create loan record |
| GET | `/loans/:id` | `hr:read` | Get loan by ID |
| PATCH | `/loans/:id` | `hr:update` | Update loan |
| PATCH | `/loans/:id/status` | `hr:update` | Update loan status |

**POST Request Body — `createLoanRecordSchema`**

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `employeeId` | string | Yes | |
| `policyId` | string | Yes | |
| `amount` | number | Yes | Positive |
| `tenure` | integer | Yes | Positive (months) |
| `emiAmount` | number | No | Auto-calculated if not provided |
| `interestRate` | number | No | 0–100 (defaults from policy) |

**PATCH `/loans/:id` — `updateLoanRecordSchema`**

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `amount` | number | No | Positive |
| `tenure` | integer | No | Positive |
| `emiAmount` | number | No | Positive |
| `interestRate` | number | No | 0–100 |

**PATCH `/loans/:id/status` — `updateLoanStatusSchema`**

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `status` | enum | Yes | `PENDING` \| `APPROVED` \| `ACTIVE` \| `CLOSED` \| `REJECTED` |
| `approvedBy` | string | No | |

---

## 6. Payroll Run Engine

Source: `src/modules/hr/payroll-run/`

### 6.1 Payroll Runs

| Method | Path | Permission | Description |
|--------|------|------------|-------------|
| GET | `/payroll-runs` | `hr:read` | List payroll runs |
| POST | `/payroll-runs` | `hr:create` | Create a new payroll run |
| GET | `/payroll-runs/:id` | `hr:read` | Get payroll run by ID |

**POST Request Body — `createPayrollRunSchema`**

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `month` | integer | Yes | 1–12 |
| `year` | integer | Yes | 2020–2099 |

---

### 6.2 Payroll Run — 6-Step Wizard

| Method | Path | Permission | Description |
|--------|------|------------|-------------|
| PATCH | `/payroll-runs/:id/lock-attendance` | `hr:update` | Step 1: Lock attendance for the period |
| PATCH | `/payroll-runs/:id/review-exceptions` | `hr:update` | Step 2: Review exceptions |
| PATCH | `/payroll-runs/:id/compute` | `hr:update` | Step 3: Compute salaries |
| PATCH | `/payroll-runs/:id/statutory` | `hr:update` | Step 4: Compute statutory deductions |
| PATCH | `/payroll-runs/:id/approve` | `hr:update` | Step 5: Approve payroll run |
| PATCH | `/payroll-runs/:id/disburse` | `hr:update` | Step 6: Disburse salaries |

No request body required for wizard steps (server-side processing).

---

### 6.3 Payroll Entries

| Method | Path | Permission | Description |
|--------|------|------------|-------------|
| GET | `/payroll-runs/:id/entries` | `hr:read` | List entries for a payroll run |
| GET | `/payroll-runs/:id/entries/:eid` | `hr:read` | Get specific entry |
| PATCH | `/payroll-runs/:id/entries/:eid` | `hr:update` | Override entry values |

**PATCH Request Body — `overrideEntrySchema`**

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `earnings` | Record<string, number> | No | `{ componentCode: amount }` |
| `deductions` | Record<string, number> | No | `{ componentCode: amount }` |
| `exceptionNote` | string | No | |

---

### 6.4 Payslips

| Method | Path | Permission | Description |
|--------|------|------------|-------------|
| GET | `/payslips` | `hr:read` | List payslips |
| GET | `/payslips/:id` | `hr:read` | Get payslip by ID |
| POST | `/payslips/:id/email` | `hr:update` | Email payslip to employee |
| POST | `/payroll-runs/:id/generate-payslips` | `hr:create` | Generate payslips for a run |

No request body for these endpoints (server processes from run data).

---

### 6.5 Salary Holds

| Method | Path | Permission | Description |
|--------|------|------------|-------------|
| GET | `/salary-holds` | `hr:read` | List salary holds |
| POST | `/salary-holds` | `hr:create` | Create salary hold |
| PATCH | `/salary-holds/:id/release` | `hr:update` | Release salary hold |

**POST Request Body — `createSalaryHoldSchema`**

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `payrollRunId` | string | Yes | |
| `employeeId` | string | Yes | |
| `holdType` | enum | No | `FULL` \| `PARTIAL` (default: `FULL`) |
| `reason` | string | Yes | |
| `heldComponents` | string[] | No | Component codes (for `PARTIAL` hold) |

---

### 6.6 Salary Revisions

| Method | Path | Permission | Description |
|--------|------|------------|-------------|
| GET | `/salary-revisions` | `hr:read` | List salary revisions |
| POST | `/salary-revisions` | `hr:create` | Create salary revision |
| GET | `/salary-revisions/:id` | `hr:read` | Get revision by ID |
| PATCH | `/salary-revisions/:id/approve` | `hr:update` | Approve revision |
| PATCH | `/salary-revisions/:id/apply` | `hr:update` | Apply revision |

**POST Request Body — `createSalaryRevisionSchema`**

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `employeeId` | string | Yes | |
| `newCtc` | number | Yes | Positive |
| `effectiveDate` | string | Yes | ISO date |
| `incrementPercent` | number | No | 0–1000 |
| `newComponents` | Record<string, number> | No | New breakup |

---

### 6.7 Arrear Entries

| Method | Path | Permission | Description |
|--------|------|------------|-------------|
| GET | `/arrear-entries` | `hr:read` | List arrear entries |

---

### 6.8 Statutory Filings

| Method | Path | Permission | Description |
|--------|------|------------|-------------|
| GET | `/statutory-filings` | `hr:read` | List statutory filings |
| POST | `/statutory-filings` | `hr:create` | Create statutory filing |
| PATCH | `/statutory-filings/:id` | `hr:update` | Update filing status |
| GET | `/statutory/dashboard` | `hr:read` | Statutory compliance dashboard |

**POST Request Body — `createStatutoryFilingSchema`**

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `type` | enum | Yes | `PF_ECR` \| `ESI_CHALLAN` \| `PT_CHALLAN` \| `TDS_24Q` \| `FORM_16` \| `BONUS_STATEMENT` \| `GRATUITY_REGISTER` \| `LWF_STATEMENT` |
| `month` | integer | No | 1–12 |
| `year` | integer | Yes | 2020–2099 |
| `amount` | number | No | Min 0 |
| `dueDate` | string | No | ISO date |
| `details` | Record<string, any> | No | |

**PATCH Request Body — `updateStatutoryFilingSchema`**

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `status` | enum | No | `PENDING` \| `GENERATED` \| `FILED` \| `VERIFIED` |
| `amount` | number | No | Min 0 |
| `fileUrl` | string | No | |
| `filedAt` | string | No | ISO date |
| `filedBy` | string | No | |
| `details` | Record<string, any> | No | |

---

### 6.9 Payroll Reports

| Method | Path | Permission | Description |
|--------|------|------------|-------------|
| GET | `/payroll-reports/salary-register` | `hr:read` | Salary register report |
| GET | `/payroll-reports/bank-file` | `hr:read` | Bank payment file download |
| GET | `/payroll-reports/pf-ecr` | `hr:read` | PF ECR report |
| GET | `/payroll-reports/esi-challan` | `hr:read` | ESI challan report |
| GET | `/payroll-reports/pt-challan` | `hr:read` | PT challan report |
| GET | `/payroll-reports/variance` | `hr:read` | Month-over-month variance report |

All report endpoints are GET-only (query params for filtering, e.g. `?month=&year=`).

---

## 7. ESS / MSS & Workflows

Source: `src/modules/hr/ess/`

### 7.1 ESS Config

| Method | Path | Permission | Description |
|--------|------|------------|-------------|
| GET | `/ess-config` | `hr:read` | Get ESS configuration (singleton) |
| PATCH | `/ess-config` | `hr:update` | Update ESS configuration |

**PATCH Request Body — `essConfigSchema`**

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `viewPayslips` | boolean | No | |
| `downloadForm16` | boolean | No | |
| `leaveApplication` | boolean | No | |
| `leaveBalanceView` | boolean | No | |
| `itDeclaration` | boolean | No | |
| `attendanceView` | boolean | No | |
| `attendanceRegularization` | boolean | No | |
| `reimbursementClaims` | boolean | No | |
| `profileUpdate` | boolean | No | |
| `documentUpload` | boolean | No | |
| `loanApplication` | boolean | No | |
| `assetView` | boolean | No | |
| `performanceGoals` | boolean | No | |
| `appraisalAccess` | boolean | No | |
| `feedback360` | boolean | No | |
| `trainingEnrollment` | boolean | No | |
| `helpDesk` | boolean | No | |
| `employeeDirectory` | boolean | No | |
| `holidayCalendar` | boolean | No | |
| `policyDocuments` | boolean | No | |
| `grievanceSubmission` | boolean | No | |
| `loginMethod` | enum | No | `PASSWORD` \| `SSO` \| `OTP` |
| `passwordMinLength` | integer | No | 6–32 |
| `passwordComplexity` | boolean | No | |
| `sessionTimeoutMinutes` | integer | No | 5–1440 |
| `mfaRequired` | boolean | No | |

---

### 7.2 Approval Workflows

| Method | Path | Permission | Description |
|--------|------|------------|-------------|
| GET | `/approval-workflows` | `hr:read` | List approval workflows |
| POST | `/approval-workflows` | `hr:create` | Create approval workflow |
| GET | `/approval-workflows/:id` | `hr:read` | Get workflow by ID |
| PATCH | `/approval-workflows/:id` | `hr:update` | Update workflow |
| DELETE | `/approval-workflows/:id` | `hr:delete` | Delete workflow |

**POST/PATCH Request Body — `createWorkflowSchema`**

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `name` | string | Yes | |
| `triggerEvent` | string | Yes | Event that triggers this workflow |
| `steps` | array | Yes | Min 1 step |
| `isActive` | boolean | No | Default: `true` |

**Workflow Step object:**

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `stepOrder` | integer | Yes | Min 1 |
| `approverRole` | string | Yes | |
| `approverId` | string | No | Specific approver user ID |
| `slaHours` | number | Yes | Min 1 |
| `autoEscalate` | boolean | No | Default: `false` |
| `autoApprove` | boolean | No | Default: `false` |
| `autoReject` | boolean | No | Default: `false` |

PATCH accepts all fields as optional.

---

### 7.3 Approval Requests

| Method | Path | Permission | Description |
|--------|------|------------|-------------|
| GET | `/approval-requests` | `hr:read` | List all approval requests |
| GET | `/approval-requests/pending` | `hr:read` | Get pending approval requests |
| GET | `/approval-requests/:id` | `hr:read` | Get request by ID |
| PATCH | `/approval-requests/:id/approve` | `hr:update` | Approve request |
| PATCH | `/approval-requests/:id/reject` | `hr:update` | Reject request |

**PATCH `/approve` and `/reject` — `processApprovalSchema`**

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `action` | enum | Yes | `approve` \| `reject` |
| `note` | string | No | |

---

### 7.4 Notification Templates

| Method | Path | Permission | Description |
|--------|------|------------|-------------|
| GET | `/notification-templates` | `hr:read` | List notification templates |
| POST | `/notification-templates` | `hr:create` | Create template |
| GET | `/notification-templates/:id` | `hr:read` | Get template by ID |
| PATCH | `/notification-templates/:id` | `hr:update` | Update template |
| DELETE | `/notification-templates/:id` | `hr:delete` | Delete template |

**POST/PATCH Request Body — `createNotificationTemplateSchema`**

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `name` | string | Yes | |
| `subject` | string | No | For email channel |
| `body` | string | Yes | Template body (supports placeholders) |
| `channel` | enum | Yes | `EMAIL` \| `SMS` \| `PUSH` \| `IN_APP` \| `WHATSAPP` |
| `isActive` | boolean | No | Default: `true` |

PATCH accepts all fields as optional.

---

### 7.5 Notification Rules

| Method | Path | Permission | Description |
|--------|------|------------|-------------|
| GET | `/notification-rules` | `hr:read` | List notification rules |
| POST | `/notification-rules` | `hr:create` | Create rule |
| GET | `/notification-rules/:id` | `hr:read` | Get rule by ID |
| PATCH | `/notification-rules/:id` | `hr:update` | Update rule |
| DELETE | `/notification-rules/:id` | `hr:delete` | Delete rule |

**POST/PATCH Request Body — `createNotificationRuleSchema`**

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `triggerEvent` | string | Yes | |
| `templateId` | string | Yes | Notification template ID |
| `recipientRole` | string | Yes | |
| `channel` | enum | Yes | `EMAIL` \| `SMS` \| `PUSH` \| `IN_APP` \| `WHATSAPP` |
| `isActive` | boolean | No | Default: `true` |

PATCH accepts all fields as optional.

---

### 7.6 Manager Delegates

| Method | Path | Permission | Description |
|--------|------|------------|-------------|
| GET | `/delegates` | `hr:read` | List delegates |
| POST | `/delegates` | `hr:create` | Create delegate assignment |
| PATCH | `/delegates/:id/revoke` | `hr:update` | Revoke delegation |

**POST Request Body — `createDelegateSchema`**

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `managerId` | string | Yes | |
| `delegateId` | string | Yes | Employee acting as delegate |
| `fromDate` | string | Yes | ISO date |
| `toDate` | string | Yes | ISO date |
| `reason` | string | No | |

---

### 7.7 IT Declarations

| Method | Path | Permission | Description |
|--------|------|------------|-------------|
| GET | `/it-declarations` | `hr:read` | List IT declarations |
| POST | `/it-declarations` | `hr:create` | Create IT declaration |
| GET | `/it-declarations/:id` | `hr:read` | Get declaration by ID |
| PATCH | `/it-declarations/:id` | `hr:update` | Update declaration |
| PATCH | `/it-declarations/:id/submit` | `hr:update` | Submit declaration |
| PATCH | `/it-declarations/:id/verify` | `hr:update` | Verify declaration (HR) |
| PATCH | `/it-declarations/:id/lock` | `hr:update` | Lock declaration |

**POST Request Body — `createITDeclarationSchema`**

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `employeeId` | string | Yes | |
| `financialYear` | string | Yes | e.g. `"2025-26"` |
| `regime` | enum | No | `OLD` \| `NEW` (default: `NEW`) |
| `section80C` | any | No | Section 80C investment details |
| `section80CCD` | any | No | NPS contributions |
| `section80D` | any | No | Health insurance |
| `section80E` | any | No | Education loan interest |
| `section80G` | any | No | Donations |
| `section80GG` | any | No | Rent paid |
| `section80TTA` | any | No | Savings account interest |
| `hraExemption` | any | No | HRA details |
| `ltaExemption` | any | No | LTA details |
| `homeLoanInterest` | any | No | |
| `otherIncome` | any | No | |

**PATCH Request Body — `updateITDeclarationSchema`**

Same as create but all fields optional; `employeeId` and `financialYear` are excluded (immutable).

---

### 7.8 ESS Self-Service (Employee-Facing)

| Method | Path | Permission | Description |
|--------|------|------------|-------------|
| GET | `/ess/my-profile` | `hr:read` | Get logged-in employee's profile |
| GET | `/ess/my-payslips` | `hr:read` | Get own payslips |
| GET | `/ess/my-leave-balance` | `hr:read` | Get own leave balances |
| GET | `/ess/my-attendance` | `hr:read` | Get own attendance records |
| GET | `/ess/my-declarations` | `hr:read` | Get own IT declarations |
| POST | `/ess/apply-leave` | `hr:create` | Apply for leave |
| POST | `/ess/regularize-attendance` | `hr:create` | Request attendance regularization |

**POST `/ess/apply-leave` — `applyLeaveSchema`**

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `leaveTypeId` | string | Yes | |
| `fromDate` | string | Yes | ISO date |
| `toDate` | string | Yes | ISO date |
| `days` | number | Yes | Min 0.5 |
| `isHalfDay` | boolean | No | Default: `false` |
| `halfDayType` | enum | No | `FIRST_HALF` \| `SECOND_HALF` |
| `reason` | string | Yes | |

**POST `/ess/regularize-attendance` — `regularizeAttendanceSchema`**

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `attendanceRecordId` | string | Yes | |
| `issueType` | enum | Yes | `MISSING_PUNCH_IN` \| `MISSING_PUNCH_OUT` \| `ABSENT_OVERRIDE` \| `LATE_OVERRIDE` \| `NO_PUNCH` |
| `correctedPunchIn` | string | No | ISO datetime |
| `correctedPunchOut` | string | No | ISO datetime |
| `reason` | string | Yes | |

---

### 7.9 MSS Manager Self-Service

| Method | Path | Permission | Description |
|--------|------|------------|-------------|
| GET | `/mss/team-members` | `hr:read` | Get reporting team members |
| GET | `/mss/pending-approvals` | `hr:read` | Get pending manager approvals |
| GET | `/mss/team-attendance` | `hr:read` | Get team attendance |
| GET | `/mss/team-leave-calendar` | `hr:read` | Get team leave calendar |

All MSS endpoints are GET-only (read from authenticated manager context).

---

## 8. Performance Management

Source: `src/modules/hr/performance/`

### 8.1 Appraisal Cycles

| Method | Path | Permission | Description |
|--------|------|------------|-------------|
| GET | `/appraisal-cycles` | `hr:read` | List appraisal cycles |
| POST | `/appraisal-cycles` | `hr:create` | Create cycle |
| GET | `/appraisal-cycles/:id` | `hr:read` | Get cycle by ID |
| PATCH | `/appraisal-cycles/:id` | `hr:update` | Update cycle |
| DELETE | `/appraisal-cycles/:id` | `hr:delete` | Delete cycle |

**POST/PATCH Request Body — `createAppraisalCycleSchema`**

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `name` | string | Yes | |
| `frequency` | enum | No | `ANNUAL` \| `SEMI_ANNUAL` \| `QUARTERLY` (default: `ANNUAL`) |
| `startDate` | string | Yes | ISO date |
| `endDate` | string | Yes | ISO date |
| `ratingScale` | integer | No | 3–10 (default: `5`) |
| `ratingLabels` | string[] | No | Custom labels for each rating level |
| `kraWeightage` | number | No | 0–100 (default: `70`) |
| `competencyWeightage` | number | No | 0–100 (default: `30`) |
| `bellCurve` | Record<string, number> | No | Expected distribution |
| `forcedDistribution` | boolean | No | Default: `false` |
| `midYearReview` | boolean | No | Default: `false` |
| `midYearMonth` | integer | No | 1–12 |
| `managerEditDays` | integer | No | Min 0 |

PATCH accepts all fields as optional.

---

### 8.2 Cycle Lifecycle

| Method | Path | Permission | Description |
|--------|------|------------|-------------|
| PATCH | `/appraisal-cycles/:id/activate` | `hr:update` | Activate cycle (open for reviews) |
| PATCH | `/appraisal-cycles/:id/close-review` | `hr:update` | Close review window |
| PATCH | `/appraisal-cycles/:id/start-calibration` | `hr:update` | Start calibration phase |
| PATCH | `/appraisal-cycles/:id/publish-ratings` | `hr:update` | Publish final ratings |
| PATCH | `/appraisal-cycles/:id/close` | `hr:update` | Close cycle |

No request body for lifecycle transitions.

---

### 8.3 Appraisal Entries

| Method | Path | Permission | Description |
|--------|------|------------|-------------|
| GET | `/appraisal-cycles/:cycleId/entries` | `hr:read` | List entries for a cycle |
| GET | `/appraisal-cycles/:cycleId/calibration` | `hr:read` | Get calibration view |
| POST | `/appraisal-entries` | `hr:create` | Create appraisal entry |
| GET | `/appraisal-entries/:id` | `hr:read` | Get entry by ID |
| PATCH | `/appraisal-entries/:id/self-review` | `hr:update` | Submit self-review |
| PATCH | `/appraisal-entries/:id/manager-review` | `hr:update` | Submit manager review |
| PATCH | `/appraisal-entries/:id/publish` | `hr:update` | Publish entry |

**PATCH `/self-review` — `selfReviewSchema`**

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `selfRating` | number | Yes | 0–10 |
| `selfComments` | string | No | |
| `kraScore` | number | No | 0–100 |
| `competencyScore` | number | No | 0–100 |
| `goalRatings` | array | No | Each: `{ goalId: string, selfRating: integer(1-10), achievedValue?: number }` |

**PATCH `/manager-review` — `managerReviewSchema`**

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `managerRating` | number | Yes | 0–10 |
| `managerComments` | string | No | |
| `kraScore` | number | No | 0–100 |
| `competencyScore` | number | No | 0–100 |
| `promotionRecommended` | boolean | No | Default: `false` |
| `incrementPercent` | number | No | 0–100 |
| `goalRatings` | array | No | Each: `{ goalId: string, managerRating: integer(1-10) }` |

**PATCH `/publish` — `publishEntrySchema`**

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `finalRating` | number | Yes | 0–10 |

---

### 8.4 Goals (KRA/OKR)

| Method | Path | Permission | Description |
|--------|------|------------|-------------|
| GET | `/goals` | `hr:read` | List goals |
| POST | `/goals` | `hr:create` | Create goal |
| GET | `/goals/cascade/:departmentId` | `hr:read` | Get goal cascade for department |
| GET | `/goals/:id` | `hr:read` | Get goal by ID |
| PATCH | `/goals/:id` | `hr:update` | Update goal |
| DELETE | `/goals/:id` | `hr:delete` | Delete goal |

**POST Request Body — `createGoalSchema`**

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `cycleId` | string | Yes | |
| `employeeId` | string | No | |
| `departmentId` | string | No | |
| `parentGoalId` | string | No | For cascading goals |
| `title` | string | Yes | |
| `description` | string | No | |
| `kpiMetric` | string | No | |
| `targetValue` | number | No | |
| `weightage` | number | Yes | 0–100 |
| `level` | enum | No | `COMPANY` \| `DEPARTMENT` \| `INDIVIDUAL` (default: `INDIVIDUAL`) |
| `status` | enum | No | `DRAFT` \| `ACTIVE` \| `COMPLETED` \| `CANCELLED` (default: `DRAFT`) |

**PATCH Request Body — `updateGoalSchema`**

All fields optional except `cycleId` (excluded/immutable).

---

### 8.5 360 Feedback

| Method | Path | Permission | Description |
|--------|------|------------|-------------|
| GET | `/appraisal-cycles/:cycleId/feedback` | `hr:read` | List feedback for a cycle |
| GET | `/feedback360/report/:employeeId/:cycleId` | `hr:read` | Get aggregated feedback report |
| POST | `/feedback360` | `hr:create` | Create 360 feedback |
| GET | `/feedback360/:id` | `hr:read` | Get feedback by ID |
| PATCH | `/feedback360/:id` | `hr:update` | Update feedback |
| DELETE | `/feedback360/:id` | `hr:delete` | Delete feedback |
| PATCH | `/feedback360/:id/submit` | `hr:update` | Submit feedback |

**POST Request Body — `createFeedback360Schema`**

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `cycleId` | string | Yes | |
| `employeeId` | string | Yes | Subject employee |
| `raterId` | string | Yes | Person providing feedback |
| `raterType` | enum | Yes | `SELF` \| `MANAGER` \| `PEER` \| `SUBORDINATE` \| `CROSS_FUNCTION` \| `INTERNAL_CUSTOMER` |
| `ratings` | Record<string, number> | Yes | `{ competency: rating(1-10) }` |
| `strengths` | string | No | |
| `improvements` | string | No | |
| `wouldWorkAgain` | boolean | No | |
| `isAnonymous` | boolean | No | Default: `true` |

**PATCH Request Body — `updateFeedback360Schema`**

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `ratings` | Record<string, number> | No | `{ competency: rating(1-10) }` |
| `strengths` | string | No | |
| `improvements` | string | No | |
| `wouldWorkAgain` | boolean | No | |

---

### 8.6 Skill Library

| Method | Path | Permission | Description |
|--------|------|------------|-------------|
| GET | `/skills` | `hr:read` | List skills |
| POST | `/skills` | `hr:create` | Create skill |
| GET | `/skills/:id` | `hr:read` | Get skill by ID |
| PATCH | `/skills/:id` | `hr:update` | Update skill |
| DELETE | `/skills/:id` | `hr:delete` | Delete skill |

**POST/PATCH Request Body — `createSkillSchema`**

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `name` | string | Yes | |
| `category` | string | Yes | |
| `description` | string | No | |

PATCH accepts all fields as optional.

---

### 8.7 Skill Mappings

| Method | Path | Permission | Description |
|--------|------|------------|-------------|
| GET | `/skill-mappings` | `hr:read` | List skill mappings |
| POST | `/skill-mappings` | `hr:create` | Create skill mapping |
| GET | `/skill-mappings/gap-analysis/:employeeId` | `hr:read` | Get skill gap analysis for employee |
| GET | `/skill-mappings/:id` | `hr:read` | Get mapping by ID |
| PATCH | `/skill-mappings/:id` | `hr:update` | Update mapping |
| DELETE | `/skill-mappings/:id` | `hr:delete` | Delete mapping |

**POST Request Body — `createSkillMappingSchema`**

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `employeeId` | string | Yes | |
| `skillId` | string | Yes | |
| `currentLevel` | integer | No | 1–5 (default: `1`) |
| `requiredLevel` | integer | No | 1–5 (default: `3`) |
| `assessedBy` | string | No | |

**PATCH Request Body — `updateSkillMappingSchema`**

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `currentLevel` | integer | No | 1–5 |
| `requiredLevel` | integer | No | 1–5 |
| `assessedBy` | string | No | |

---

### 8.8 Succession Plans

| Method | Path | Permission | Description |
|--------|------|------------|-------------|
| GET | `/succession-plans` | `hr:read` | List succession plans |
| GET | `/succession-plans/nine-box` | `hr:read` | Get 9-box grid view |
| GET | `/succession-plans/bench-strength` | `hr:read` | Get bench strength report |
| POST | `/succession-plans` | `hr:create` | Create succession plan |
| GET | `/succession-plans/:id` | `hr:read` | Get plan by ID |
| PATCH | `/succession-plans/:id` | `hr:update` | Update plan |
| DELETE | `/succession-plans/:id` | `hr:delete` | Delete plan |

**POST Request Body — `createSuccessionPlanSchema`**

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `criticalRoleTitle` | string | Yes | |
| `criticalRoleDesignationId` | string | No | |
| `successorId` | string | Yes | Employee ID of successor |
| `readiness` | enum | No | `READY_NOW` \| `ONE_YEAR` \| `TWO_YEARS` \| `NOT_READY` (default: `NOT_READY`) |
| `developmentPlan` | string | No | |
| `performanceRating` | number | No | 0–10 |
| `potentialRating` | number | No | 0–10 |
| `nineBoxPosition` | string | No | |

**PATCH Request Body — `updateSuccessionPlanSchema`**

All fields optional except `successorId` (excluded/immutable).

---

### 8.9 Performance Dashboard

| Method | Path | Permission | Description |
|--------|------|------------|-------------|
| GET | `/performance-dashboard` | `hr:read` | Get performance management dashboard |

---

## 9. Offboarding & F&F

Source: `src/modules/hr/offboarding/`

### 9.1 Exit Requests

| Method | Path | Permission | Description |
|--------|------|------------|-------------|
| GET | `/exit-requests` | `hr:read` | List exit requests |
| POST | `/exit-requests` | `hr:create` | Create exit request |
| GET | `/exit-requests/:id` | `hr:read` | Get exit request by ID |
| PATCH | `/exit-requests/:id` | `hr:update` | Update exit request |

**POST Request Body — `createExitRequestSchema`**

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `employeeId` | string | Yes | |
| `separationType` | enum | Yes | `VOLUNTARY_RESIGNATION` \| `RETIREMENT` \| `TERMINATION_FOR_CAUSE` \| `LAYOFF_RETRENCHMENT` \| `DEATH` \| `ABSCONDING` \| `CONTRACT_END` |
| `resignationDate` | string | No | ISO date |
| `noticePeriodWaiver` | boolean | No | Default: `false` |
| `exitInterviewNotes` | string | No | |

**PATCH Request Body — `updateExitRequestSchema`**

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `lastWorkingDate` | string | No | ISO date |
| `noticePeriodWaiver` | boolean | No | |
| `waiverAmount` | number | No | Min 0 |
| `exitInterviewDone` | boolean | No | |
| `exitInterviewNotes` | string | No | |
| `knowledgeTransferDone` | boolean | No | |
| `status` | enum | No | `INITIATED` \| `NOTICE_PERIOD` \| `CLEARANCE_PENDING` \| `CLEARANCE_DONE` \| `FNF_COMPUTED` \| `FNF_PAID` \| `COMPLETED` |

---

### 9.2 Clearances

| Method | Path | Permission | Description |
|--------|------|------------|-------------|
| GET | `/exit-requests/:id/clearances` | `hr:read` | List clearances for exit request |
| PATCH | `/exit-clearances/:id` | `hr:update` | Update clearance status |

**PATCH Request Body — `updateClearanceSchema`**

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `status` | enum | Yes | `PENDING` \| `CLEARED` \| `NOT_APPLICABLE` |
| `clearedBy` | string | No | |
| `items` | array | No | Each: `{ item: string, status: enum, notes?: string }` |

---

### 9.3 Exit Interview

| Method | Path | Permission | Description |
|--------|------|------------|-------------|
| POST | `/exit-requests/:id/interview` | `hr:create` | Create exit interview |
| GET | `/exit-requests/:id/interview` | `hr:read` | Get exit interview |

**POST Request Body — `exitInterviewSchema`**

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `responses` | array | Yes | Min 1 item. Each: `{ question: string, answer: string }` |
| `conductedBy` | string | No | |
| `overallRating` | integer | No | 1–5 |
| `wouldRecommend` | boolean | No | |

---

### 9.4 F&F Settlement

| Method | Path | Permission | Description |
|--------|------|------------|-------------|
| POST | `/exit-requests/:id/compute-fnf` | `hr:create` | Compute F&F settlement |
| GET | `/fnf-settlements` | `hr:read` | List F&F settlements |
| GET | `/fnf-settlements/:id` | `hr:read` | Get F&F settlement by ID |
| PATCH | `/fnf-settlements/:id/approve` | `hr:update` | Approve F&F |
| PATCH | `/fnf-settlements/:id/pay` | `hr:update` | Mark F&F as paid |

**POST `/compute-fnf` — `computeFnFSchema`**

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `otherEarnings` | number | No | Min 0 (default: `0`) |
| `otherDeductions` | number | No | Min 0 (default: `0`) |

**PATCH `/approve` — `approveFnFSchema`**

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `approvedBy` | string | Yes | Approver user ID |

---

## 10. Advanced HR

Source: `src/modules/hr/advanced/`

### 10.1 Recruitment — Requisitions

| Method | Path | Permission | Description |
|--------|------|------------|-------------|
| GET | `/requisitions` | `hr:read` | List job requisitions |
| POST | `/requisitions` | `hr:create` | Create requisition |
| GET | `/requisitions/:id` | `hr:read` | Get requisition by ID |
| PATCH | `/requisitions/:id` | `hr:update` | Update requisition |
| PATCH | `/requisitions/:id/status` | `hr:update` | Update requisition status |
| DELETE | `/requisitions/:id` | `hr:delete` | Delete requisition |

**POST/PATCH Request Body — `createRequisitionSchema`**

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `title` | string | Yes | |
| `designationId` | string | No | |
| `departmentId` | string | No | |
| `openings` | integer | No | Min 1 (default: `1`) |
| `description` | string | No | |
| `budgetMin` | number | No | Min 0 |
| `budgetMax` | number | No | Min 0 |
| `targetDate` | string | No | ISO date |
| `sourceChannels` | string[] | No | |
| `approvedBy` | string | No | |

**PATCH `/status` — `updateRequisitionStatusSchema`**

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `status` | enum | Yes | `DRAFT` \| `OPEN` \| `INTERVIEWING` \| `OFFERED` \| `FILLED` \| `CANCELLED` |

PATCH accepts all fields as optional.

---

### 10.2 Recruitment — Candidates

| Method | Path | Permission | Description |
|--------|------|------------|-------------|
| GET | `/candidates` | `hr:read` | List candidates |
| POST | `/candidates` | `hr:create` | Create candidate |
| GET | `/candidates/:id` | `hr:read` | Get candidate by ID |
| PATCH | `/candidates/:id` | `hr:update` | Update candidate |
| PATCH | `/candidates/:id/stage` | `hr:update` | Advance candidate stage |
| DELETE | `/candidates/:id` | `hr:delete` | Delete candidate |

**POST Request Body — `createCandidateSchema`**

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `requisitionId` | string | Yes | |
| `name` | string | Yes | |
| `email` | string | Yes | Valid email |
| `phone` | string | No | |
| `source` | string | No | |
| `currentCtc` | number | No | Min 0 |
| `expectedCtc` | number | No | Min 0 |
| `resumeUrl` | string | No | |
| `rating` | number | No | 0–10 |
| `notes` | string | No | |

**PATCH `/candidates/:id` — `updateCandidateSchema`**

All fields optional; `requisitionId` excluded (immutable).

**PATCH `/candidates/:id/stage` — `advanceCandidateStageSchema`**

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `stage` | enum | Yes | `APPLIED` \| `SHORTLISTED` \| `HR_ROUND` \| `TECHNICAL` \| `FINAL` \| `ASSESSMENT` \| `OFFER_SENT` \| `HIRED` \| `REJECTED` \| `ON_HOLD` |

---

### 10.3 Recruitment — Interviews

| Method | Path | Permission | Description |
|--------|------|------------|-------------|
| GET | `/interviews` | `hr:read` | List interviews |
| POST | `/interviews` | `hr:create` | Schedule interview |
| GET | `/interviews/:id` | `hr:read` | Get interview by ID |
| PATCH | `/interviews/:id` | `hr:update` | Update interview |
| PATCH | `/interviews/:id/complete` | `hr:update` | Complete interview with feedback |
| PATCH | `/interviews/:id/cancel` | `hr:update` | Cancel interview |
| DELETE | `/interviews/:id` | `hr:delete` | Delete interview |

**POST Request Body — `createInterviewSchema`**

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `candidateId` | string | Yes | |
| `round` | string | Yes | e.g. `"HR Round"`, `"Technical"` |
| `panelists` | string[] | No | Employee/user IDs |
| `scheduledAt` | string | Yes | ISO datetime |
| `duration` | integer | No | Minutes, min 1 |
| `meetingLink` | string | No | |

**PATCH `/interviews/:id` — `updateInterviewSchema`**

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `round` | string | No | |
| `panelists` | string[] | No | |
| `scheduledAt` | string | No | |
| `duration` | integer | No | Min 1 |
| `meetingLink` | string | No | |

**PATCH `/complete` — `completeInterviewSchema`**

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `feedbackRating` | number | Yes | 0–10 |
| `feedbackNotes` | string | No | |

---

### 10.4 Recruitment Dashboard

| Method | Path | Permission | Description |
|--------|------|------------|-------------|
| GET | `/recruitment-dashboard` | `hr:read` | Recruitment analytics dashboard |

---

### 10.5 Training — Catalogue

| Method | Path | Permission | Description |
|--------|------|------------|-------------|
| GET | `/training-catalogues` | `hr:read` | List training catalogue |
| POST | `/training-catalogues` | `hr:create` | Create training entry |
| GET | `/training-catalogues/:id` | `hr:read` | Get training by ID |
| PATCH | `/training-catalogues/:id` | `hr:update` | Update training |
| DELETE | `/training-catalogues/:id` | `hr:delete` | Delete training |

**POST/PATCH Request Body — `createTrainingCatalogueSchema`**

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `name` | string | Yes | |
| `type` | string | No | Default: `"TECHNICAL"` |
| `mode` | enum | No | `ONLINE` \| `CLASSROOM` \| `WORKSHOP` \| `EXTERNAL` \| `BLENDED` \| `ON_THE_JOB` (default: `CLASSROOM`) |
| `duration` | string | No | |
| `linkedSkillIds` | string[] | No | |
| `proficiencyGain` | integer | No | 0–5 (default: `1`) |
| `mandatory` | boolean | No | Default: `false` |
| `certificationName` | string | No | |
| `certificationBody` | string | No | |
| `certificationValidity` | integer | No | Months, min 0 |
| `vendorProvider` | string | No | |
| `costPerHead` | number | No | Min 0 |
| `isActive` | boolean | No | Default: `true` |

PATCH accepts all fields as optional.

---

### 10.6 Training — Nominations

| Method | Path | Permission | Description |
|--------|------|------------|-------------|
| GET | `/training-nominations` | `hr:read` | List nominations |
| POST | `/training-nominations` | `hr:create` | Nominate employee for training |
| GET | `/training-nominations/:id` | `hr:read` | Get nomination by ID |
| PATCH | `/training-nominations/:id` | `hr:update` | Update nomination |
| PATCH | `/training-nominations/:id/complete` | `hr:update` | Mark training as completed |
| DELETE | `/training-nominations/:id` | `hr:delete` | Delete nomination |

**POST Request Body — `createTrainingNominationSchema`**

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `employeeId` | string | Yes | |
| `trainingId` | string | Yes | |

**PATCH Request Body — `updateTrainingNominationSchema`**

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `status` | enum | No | `NOMINATED` \| `ENROLLED` \| `COMPLETED` \| `CANCELLED` |
| `completionDate` | string | No | ISO date |
| `score` | number | No | 0–100 |
| `certificateUrl` | string | No | |

**PATCH `/complete` — `completeTrainingNominationSchema`**

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `completionDate` | string | No | ISO date |
| `score` | number | No | 0–100 |
| `certificateUrl` | string | No | |

---

### 10.7 Training Dashboard

| Method | Path | Permission | Description |
|--------|------|------------|-------------|
| GET | `/training-dashboard` | `hr:read` | Training analytics dashboard |

---

### 10.8 Assets — Categories

| Method | Path | Permission | Description |
|--------|------|------------|-------------|
| GET | `/asset-categories` | `hr:read` | List asset categories |
| POST | `/asset-categories` | `hr:create` | Create asset category |
| GET | `/asset-categories/:id` | `hr:read` | Get category by ID |
| PATCH | `/asset-categories/:id` | `hr:update` | Update category |
| DELETE | `/asset-categories/:id` | `hr:delete` | Delete category |

**POST/PATCH Request Body — `createAssetCategorySchema`**

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `name` | string | Yes | |
| `depreciationRate` | number | No | 0–100% |
| `returnChecklist` | string[] | No | Checklist items for return |

PATCH accepts all fields as optional.

---

### 10.9 Assets — Assets

| Method | Path | Permission | Description |
|--------|------|------------|-------------|
| GET | `/assets` | `hr:read` | List assets |
| POST | `/assets` | `hr:create` | Create asset |
| GET | `/assets/:id` | `hr:read` | Get asset by ID |
| PATCH | `/assets/:id` | `hr:update` | Update asset |
| DELETE | `/assets/:id` | `hr:delete` | Delete asset |

**POST Request Body — `createAssetSchema`**

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `name` | string | Yes | |
| `categoryId` | string | Yes | |
| `serialNumber` | string | No | |
| `purchaseDate` | string | No | ISO date |
| `purchaseValue` | number | No | Min 0 |
| `condition` | enum | No | `NEW` \| `LIKE_NEW` \| `GOOD` \| `FAIR` \| `DAMAGED` \| `LOST` (default: `NEW`) |

**PATCH Request Body — `updateAssetSchema`**

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `name` | string | No | |
| `categoryId` | string | No | |
| `serialNumber` | string | No | |
| `purchaseDate` | string | No | |
| `purchaseValue` | number | No | |
| `condition` | enum | No | Same values as create |
| `status` | enum | No | `IN_STOCK` \| `ASSIGNED` \| `UNDER_REPAIR` \| `PENDING_RETURN` \| `RETIRED` |

---

### 10.10 Assets — Assignments

| Method | Path | Permission | Description |
|--------|------|------------|-------------|
| GET | `/asset-assignments` | `hr:read` | List asset assignments |
| POST | `/asset-assignments` | `hr:create` | Assign asset to employee |
| PATCH | `/asset-assignments/:id/return` | `hr:update` | Return asset |

**POST Request Body — `createAssetAssignmentSchema`**

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `assetId` | string | Yes | |
| `employeeId` | string | Yes | |
| `issueDate` | string | Yes | ISO date |
| `notes` | string | No | |

**PATCH `/return` — `returnAssetSchema`**

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `returnDate` | string | Yes | ISO date |
| `returnCondition` | enum | Yes | `NEW` \| `LIKE_NEW` \| `GOOD` \| `FAIR` \| `DAMAGED` \| `LOST` |
| `notes` | string | No | |

---

### 10.11 Expense Claims

| Method | Path | Permission | Description |
|--------|------|------------|-------------|
| GET | `/expense-claims` | `hr:read` | List expense claims |
| POST | `/expense-claims` | `hr:create` | Create expense claim |
| GET | `/expense-claims/:id` | `hr:read` | Get claim by ID |
| PATCH | `/expense-claims/:id` | `hr:update` | Update claim |
| PATCH | `/expense-claims/:id/submit` | `hr:update` | Submit claim for approval |
| PATCH | `/expense-claims/:id/approve-reject` | `hr:update` | Approve or reject claim |
| DELETE | `/expense-claims/:id` | `hr:delete` | Delete claim |

**POST Request Body — `createExpenseClaimSchema`**

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `employeeId` | string | Yes | |
| `title` | string | Yes | |
| `amount` | number | Yes | Min 0.01 |
| `category` | string | Yes | e.g. `"Travel"`, `"Food"` |
| `receipts` | array | No | Each: `{ fileName: string, fileUrl: string }` |
| `description` | string | No | |
| `tripDate` | string | No | ISO date |

**PATCH `/expense-claims/:id` — `updateExpenseClaimSchema`**

All fields optional; `employeeId` excluded (immutable).

**PATCH `/approve-reject` — `approveRejectClaimSchema`**

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `action` | enum | Yes | `approve` \| `reject` |
| `approvedBy` | string | No | |

---

### 10.12 HR Letter Templates

| Method | Path | Permission | Description |
|--------|------|------------|-------------|
| GET | `/letter-templates` | `hr:read` | List letter templates |
| POST | `/letter-templates` | `hr:create` | Create template |
| GET | `/letter-templates/:id` | `hr:read` | Get template by ID |
| PATCH | `/letter-templates/:id` | `hr:update` | Update template |
| DELETE | `/letter-templates/:id` | `hr:delete` | Delete template |

**POST/PATCH Request Body — `createLetterTemplateSchema`**

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `type` | string | Yes | Template type (e.g. `"OFFER"`, `"APPOINTMENT"`, `"RELIEVING"`) |
| `name` | string | Yes | |
| `bodyTemplate` | string | Yes | HTML/text with placeholders |
| `isActive` | boolean | No | Default: `true` |

PATCH accepts all fields as optional.

---

### 10.13 HR Letters

| Method | Path | Permission | Description |
|--------|------|------------|-------------|
| GET | `/hr-letters` | `hr:read` | List generated letters |
| POST | `/hr-letters` | `hr:create` | Generate letter from template |
| GET | `/hr-letters/:id` | `hr:read` | Get letter by ID |
| DELETE | `/hr-letters/:id` | `hr:delete` | Delete letter |

**POST Request Body — `createLetterSchema`**

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `templateId` | string | Yes | Letter template ID |
| `employeeId` | string | Yes | |
| `effectiveDate` | string | No | ISO date |

---

### 10.14 Grievance — Categories

| Method | Path | Permission | Description |
|--------|------|------------|-------------|
| GET | `/grievance-categories` | `hr:read` | List grievance categories |
| POST | `/grievance-categories` | `hr:create` | Create category |
| GET | `/grievance-categories/:id` | `hr:read` | Get category by ID |
| PATCH | `/grievance-categories/:id` | `hr:update` | Update category |
| DELETE | `/grievance-categories/:id` | `hr:delete` | Delete category |

**POST/PATCH Request Body — `createGrievanceCategorySchema`**

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `name` | string | Yes | |
| `slaHours` | integer | No | Min 1 (default: `72`) |
| `autoEscalateTo` | string | No | User/role to escalate to |

PATCH accepts all fields as optional.

---

### 10.15 Grievance — Cases

| Method | Path | Permission | Description |
|--------|------|------------|-------------|
| GET | `/grievance-cases` | `hr:read` | List grievance cases |
| POST | `/grievance-cases` | `hr:create` | Create grievance case |
| GET | `/grievance-cases/:id` | `hr:read` | Get case by ID |
| PATCH | `/grievance-cases/:id` | `hr:update` | Update case |
| PATCH | `/grievance-cases/:id/resolve` | `hr:update` | Resolve case |
| DELETE | `/grievance-cases/:id` | `hr:delete` | Delete case |

**POST Request Body — `createGrievanceCaseSchema`**

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `employeeId` | string | No | Omit for anonymous |
| `categoryId` | string | Yes | |
| `description` | string | Yes | |
| `isAnonymous` | boolean | No | Default: `false` |

**PATCH `/grievance-cases/:id` — `updateGrievanceCaseSchema`**

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `description` | string | No | |
| `status` | enum | No | `OPEN` \| `INVESTIGATING` \| `RESOLVED` \| `CLOSED` \| `ESCALATED` |
| `resolution` | string | No | |
| `resolvedBy` | string | No | |

**PATCH `/resolve` — `resolveGrievanceCaseSchema`**

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `resolution` | string | Yes | |
| `resolvedBy` | string | Yes | |

---

### 10.16 Disciplinary Actions

| Method | Path | Permission | Description |
|--------|------|------------|-------------|
| GET | `/disciplinary-actions` | `hr:read` | List disciplinary actions |
| POST | `/disciplinary-actions` | `hr:create` | Create disciplinary action |
| GET | `/disciplinary-actions/:id` | `hr:read` | Get action by ID |
| PATCH | `/disciplinary-actions/:id` | `hr:update` | Update action |
| DELETE | `/disciplinary-actions/:id` | `hr:delete` | Delete action |

**POST Request Body — `createDisciplinaryActionSchema`**

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `employeeId` | string | Yes | |
| `type` | enum | Yes | `VERBAL_WARNING` \| `WRITTEN_WARNING` \| `SHOW_CAUSE` \| `PIP` \| `SUSPENSION` \| `TERMINATION` |
| `charges` | string | Yes | |
| `replyDueBy` | string | No | ISO date |
| `pipDuration` | integer | No | Min 1 (days) |
| `issuedBy` | string | No | |

**PATCH Request Body — `updateDisciplinaryActionSchema`**

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `charges` | string | No | |
| `replyDueBy` | string | No | |
| `replyReceived` | string | No | |
| `pipDuration` | integer | No | Min 1 |
| `pipOutcome` | enum | No | `SUCCESS` \| `PARTIAL` \| `FAILURE` |
| `status` | string | No | |
| `issuedBy` | string | No | |

---

## 11. Transfers & Promotions

Source: `src/modules/hr/transfer/`

### 11.1 Transfers

| Method | Path | Permission | Description |
|--------|------|------------|-------------|
| GET | `/transfers` | `hr:read` | List transfers |
| POST | `/transfers` | `hr:create` | Create transfer request |
| GET | `/transfers/:id` | `hr:read` | Get transfer by ID |
| PATCH | `/transfers/:id/approve` | `hr:update` | Approve transfer |
| PATCH | `/transfers/:id/apply` | `hr:update` | Apply (execute) transfer |
| PATCH | `/transfers/:id/reject` | `hr:update` | Reject transfer |
| PATCH | `/transfers/:id/cancel` | `hr:update` | Cancel transfer |

**POST Request Body — `createTransferSchema`**

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `employeeId` | string | Yes | |
| `toDepartmentId` | string | No | |
| `toDesignationId` | string | No | |
| `toLocationId` | string | No | |
| `toManagerId` | string | No | |
| `effectiveDate` | string | Yes | ISO date |
| `reason` | string | Yes | |
| `transferType` | enum | No | `LATERAL` \| `RELOCATION` \| `RESTRUCTURING` (default: `LATERAL`) |

**PATCH `/approve`, `/reject`, `/cancel` — `approveSchema`**

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `note` | string | No | |

---

### 11.2 Promotions

| Method | Path | Permission | Description |
|--------|------|------------|-------------|
| GET | `/promotions` | `hr:read` | List promotions |
| POST | `/promotions` | `hr:create` | Create promotion request |
| GET | `/promotions/:id` | `hr:read` | Get promotion by ID |
| PATCH | `/promotions/:id/approve` | `hr:update` | Approve promotion |
| PATCH | `/promotions/:id/apply` | `hr:update` | Apply (execute) promotion |
| PATCH | `/promotions/:id/reject` | `hr:update` | Reject promotion |
| PATCH | `/promotions/:id/cancel` | `hr:update` | Cancel promotion |

**POST Request Body — `createPromotionSchema`**

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `employeeId` | string | Yes | |
| `toDesignationId` | string | Yes | |
| `toGradeId` | string | No | |
| `newCtc` | number | No | Positive |
| `effectiveDate` | string | Yes | ISO date |
| `reason` | string | No | |
| `appraisalEntryId` | string | No | Linked appraisal entry |

**PATCH `/approve`, `/reject`, `/cancel` — `approveSchema`**

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `note` | string | No | |

---

## Endpoint Summary

| Module | Endpoints |
|--------|-----------|
| Org Structure (Departments, Designations, Grades, Employee Types, Cost Centres) | 25 |
| Employee Management (CRUD + Nominees + Education + Prev Employment + Documents + Timeline) | 21 |
| Attendance (Records + Rules + Overrides + Holidays + Rosters + Overtime) | 18 |
| Leave Management (Types + Policies + Balances + Requests + Summary) | 16 |
| Payroll Configuration (Components + Structures + Employee Salary + Statutory + Loans) | 33 |
| Payroll Run Engine (Runs + Wizard + Entries + Payslips + Holds + Revisions + Arrears + Filings + Reports) | 26 |
| ESS / MSS & Workflows (Config + Workflows + Approvals + Notifications + Delegates + Declarations + ESS + MSS) | 33 |
| Performance Management (Cycles + Entries + Goals + Feedback + Skills + Succession + Dashboard) | 36 |
| Offboarding & F&F (Exit Requests + Clearances + Interviews + Settlements) | 11 |
| Advanced HR (Recruitment + Training + Assets + Expenses + Letters + Grievance + Discipline) | 48 |
| Transfers & Promotions | 14 |
| **Total** | **281** |
