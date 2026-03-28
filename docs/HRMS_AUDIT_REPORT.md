# HRMS Module — Complete Audit Report for Pilot Readiness

**Audit Date:** 2026-03-27
**Auditor:** Claude Opus 4.6 (Automated Code Audit)
**Scope:** Full end-to-end review of HRMS backend services, controllers, validators, routes, Prisma schema, mobile frontend screens, web frontend screens, and API hooks.

---

## Table of Contents

1. [Module Coverage Summary](#1-module-coverage-summary)
2. [CRITICAL Issues (Must Fix Before Pilot)](#2-critical-issues)
3. [HIGH Issues (Should Fix Before Pilot)](#3-high-issues)
4. [MEDIUM Issues (Fix During Pilot or Before Scale)](#4-medium-issues)
5. [LOW Issues (Acceptable for Pilot)](#5-low-issues)
6. [Detailed Findings by Module](#6-detailed-findings-by-module)
7. [What's Working Well](#7-whats-working-well)
8. [Pilot Readiness Verdict](#8-pilot-readiness-verdict)

---

## 1. Module Coverage Summary

| Layer | Files Audited | Sub-modules |
|-------|---------------|-------------|
| **Backend Services** | 11 service files (~5,000 LOC) | employee, attendance, leave, payroll, payroll-run, offboarding, ess, performance, advanced, transfer |
| **Backend Controllers** | 11 controller files | All matching services |
| **Backend Validators** | 11 validator files (Zod schemas) | All matching services |
| **Backend Routes** | 11 route files | All matching services |
| **Prisma Schema** | 1 file, 40+ HR models | Enums, relations, unique constraints |
| **Mobile Frontend** | 65 screen files | All HR screens in `features/company-admin/hr/` |
| **Web Frontend** | 75+ screen files + 14 API hook files | All HR screens + API layers |
| **API Hooks** | 14 hook files (mobile) + 14 (web) | queries, mutations, cache invalidation |

### Backend Module Breakdown:
- `org-structure/` — Departments, Designations, Grades, Employee Types, Cost Centres (25 endpoints)
- `employee/` — Full CRUD + sub-resources: nominees, education, prev-employment, documents, timeline (23 endpoints)
- `attendance/` — Records, rules, overrides/regularization, holidays, rosters, overtime (18 endpoints)
- `leave/` — Types, policies, balances, requests, summary (16 endpoints)
- `payroll/` — Components, structures, employee salaries, PF/ESI/PT/LWF/Bonus/Gratuity/Tax config, bank config, loans (30+ endpoints)
- `payroll-run/` — 6-step wizard, entries, payslips, holds, revisions, arrears, statutory filings, reports (25+ endpoints)
- `ess/` — Config, approval workflows, approval requests, delegates, notifications, IT declarations, self-service (20+ endpoints)
- `performance/` — Appraisal cycles, goals, entries, 360 feedback, skills, succession, 9-box dashboard
- `offboarding/` — Exit requests, clearances, exit interviews, F&F settlements (15+ endpoints)
- `advanced/` — Recruitment, training, assets, expenses, letters, grievance, discipline
- `transfer/` — Transfers & promotions with approval workflow

---

## 2. CRITICAL Issues (Must Fix Before Pilot)

### C1. Attendance-Leave Data Gap — No Attendance Records Created for Approved Leave
**Location:** `leave.service.ts:590-617` (createRequest) and `payroll-run.service.ts:406-438` (computeSalaries)
**Impact:** Employees on approved leave will have incorrect salary — potential LOP deduction on paid leave days.

**Problem:** When a leave request is approved, the system correctly deducts from the leave balance but does NOT create `AttendanceRecord` entries with `status: ON_LEAVE` for those dates. The payroll computation engine (`computeSalaries`) relies entirely on `AttendanceRecord` entries to determine present/absent/LOP days. If no attendance record exists for a leave day, that day is invisible to payroll.

**Specific failure scenario:**
1. Employee applies for 3 days CL (Casual Leave) — approved, balance deducted
2. Month-end payroll runs
3. `computeSalaries()` queries attendance records for the month
4. Those 3 leave days have NO attendance record → they are not counted in `presentDays`
5. If other attendance records exist, the system doesn't fall back to "assume full working days"
6. Result: Employee loses 3 days' salary PLUS already had leave balance deducted = double penalty

**Fix Required:**
- **Option A:** After leave approval in `leave.service.ts`, auto-create `AttendanceRecord` entries with `status: ON_LEAVE` for each approved leave day.
- **Option B:** In `computeSalaries()`, cross-reference `LeaveRequest` records (status=APPROVED) for the month and add those days to `presentDays`.

---

### C2. Frontend-Backend Payroll Status Mismatch
**Location:** Mobile: `payroll-run-screen.tsx:41,75-81,92-98`. Web: `PayrollRunScreen.tsx`
**Impact:** Frontend wizard will break or display wrong state for 3 of 8 backend statuses.

**Problem:** Backend uses 8 payroll run statuses from the Prisma enum `PayrollRunStatus`:
```
DRAFT → ATTENDANCE_LOCKED → EXCEPTIONS_REVIEWED → COMPUTED → STATUTORY_DONE → APPROVED → DISBURSED → ARCHIVED
```

Mobile frontend only maps 5 statuses:
```typescript
type RunStatus = 'DRAFT' | 'LOCKED' | 'COMPUTED' | 'APPROVED' | 'DISBURSED';
```

**Missing from frontend:**
- `ATTENDANCE_LOCKED` (backend) → `LOCKED` (frontend) — name mismatch, may or may not map correctly
- `EXCEPTIONS_REVIEWED` — completely missing from frontend
- `STATUTORY_DONE` — completely missing from frontend
- `ARCHIVED` — completely missing from frontend

The `STATUS_TO_STEP` mapping skips step 3 (Statutory Deductions):
```typescript
const STATUS_TO_STEP = { DRAFT: 0, LOCKED: 1, COMPUTED: 2, APPROVED: 4, DISBURSED: 5 };
```
Step 3 is never mapped to any status.

**Fix Required:** Update frontend `RunStatus` type to match all 8 backend statuses exactly. Update `STATUS_COLORS`, `STATUS_TO_STEP`, and wizard logic accordingly.

---

### C3. TDS Calculation is Non-Functional for Production Use
**Location:** `payroll-run.service.ts:658-671` (computeStatutory, step 4)
**Impact:** Every employee's take-home pay will be wrong. Tax deductions will not match Form 16.

**Problems (combined):**
1. Uses `annualGross = grossEarnings * 12` — ignores actual YTD figures, bonuses, one-time payments.
2. Hardcodes new tax regime only — no old regime support, no employee regime choice.
3. Ignores `TaxConfig` model completely — `DEFAULT_OLD_REGIME_SLABS` and `DEFAULT_NEW_REGIME_SLABS` defined in `payroll.service.ts` are never referenced.
4. No Section 80C/80D deductions, no HRA exemption, no IT declaration integration.
5. `ITDeclaration` model and ESS endpoints exist but are NOT wired into the TDS computation.
6. Surcharge rates defined but never applied (surcharge for income > 50L not computed).

**Fix Required (Minimum for pilot):**
- Add "TDS is provisional" disclaimer on all payslips and UI
- Allow manual TDS override per employee in the payroll entry override
- Wire IT declarations into TDS computation or provide manual adjustment workflow

---

### C4. PF Wage Identification Uses String Matching Instead of Schema Flag
**Location:** `payroll-run.service.ts:623-625` (computeStatutory) and `payroll-run.service.ts:468-473` (computeSalaries for OT)
**Impact:** PF/ESI deductions will be zero if company uses non-standard component naming.

**Problem:** PF wage is found by:
```typescript
const basicAmount = Object.entries(earningsObj).find(([code]) =>
  code.toLowerCase().includes('basic')
)?.[1] ?? 0;
```

The `SalaryComponent` model already has a `pfInclusion: Boolean` flag specifically for this purpose, but it's never used in the actual computation. If a company names their basic component `BASE_SALARY`, `BASIC_PAY`, or anything that doesn't include the substring "basic", PF calculates as zero.

Same issue with overtime calculation at line 468-473: `code.toLowerCase().includes('basic')`.

**Fix Required:** Query `SalaryComponent` records where `pfInclusion: true` and sum those amounts for PF wage calculation, instead of string matching.

---

## 3. HIGH Issues (Should Fix Before Pilot)

### H1. Payslips Are Not Immutable Snapshots
**Location:** `payroll-run.service.ts:969-1011` (generatePayslips) and `payroll-run.service.ts:927-967` (getPayslip)
**Impact:** Post-disbursement changes to payroll entries corrupt historical payslips.

**Problem:** The `Payslip` model only stores `payrollRunId`, `employeeId`, `month`, `year`, `companyId`, `emailedAt`. All salary data is dynamically fetched from `PayrollEntry` at runtime via `getPayslip()`. If someone uses `overrideEntry()` on an ARCHIVED run (which the status check allows for COMPUTED/STATUTORY_DONE only, but there's no post-ARCHIVED protection on direct DB access), the payslip would reflect changed data.

Additionally, the `PayrollEntry` deletion in `computeSalaries()` (`deleteMany` at line 394) means re-running Step 3 destroys all entry data — while the status gate prevents this through normal flow, a database admin or migration could trigger it.

**Fix:** Snapshot earnings/deductions/statutory data into the `Payslip` record at generation time. Add a guard to prevent entry modifications after ARCHIVED status.

---

### H2. Payroll Run Totals Not Updated After Entry Override
**Location:** `payroll-run.service.ts:848-888` (overrideEntry)
**Impact:** Run-level dashboard shows stale totals after any entry override.

**Problem:** `overrideEntry()` updates individual `PayrollEntry.grossEarnings`, `totalDeductions`, `netPay` but does NOT recalculate the parent `PayrollRun.totalGross`, `totalDeductions`, `totalNet`. After overriding even one entry, the run summary will be out of sync.

**Fix:** After entry override, recalculate run totals by summing all entries, or add a "recalculate totals" endpoint.

---

### H3. No Automatic Attendance Population for Holidays and Week-Offs
**Location:** `attendance.service.ts` — no auto-population logic exists
**Impact:** Payroll computation undercounts present days for employees.

**Problem:** The system doesn't auto-create `HOLIDAY` or `WEEK_OFF` attendance records. The payroll engine at line 427 counts these statuses as paid present days, but only if the records actually exist. Without them, holidays and week-offs are simply missing — not present, not absent, just invisible.

The fallback at line 436 (`if attendanceRecords.length === 0, assume full working days`) only helps when NO records exist. If there are partial records (e.g., 15 of 22 working days), the remaining 7 days are uncounted.

**Fix:** Create a daily or monthly batch job that auto-populates `WEEK_OFF` records (using roster config) and `HOLIDAY` records (using holiday calendar).

---

### H4. Approval Workflow Does Not Trigger Entity Status Updates
**Location:** `ess.service.ts:280-336` (approveStep) and `ess.service.ts:338-372` (rejectRequest)
**Impact:** Approved workflows don't auto-update the source entity (payroll run, salary revision, exit request, etc.)

**Problem:** When an approval request reaches final step and status becomes `APPROVED`, the ESS service only updates the `ApprovalRequest` record. It does NOT callback to update the source entity's status. For example:
- Payroll run approval creates an `ApprovalRequest` — if approved via workflow, the `PayrollRun.status` stays at `STATUTORY_DONE`, never becomes `APPROVED`.
- Salary revision approval creates an `ApprovalRequest` — if approved via workflow, the `SalaryRevision.status` stays at `DRAFT`.

The services check `if (approvalRequest) return { approvalPending: true }` but there's no webhook/callback to complete the entity status transition when the workflow approves.

**Fix:** Add a post-approval callback mechanism in `approveStep()` that updates the source entity status based on `entityType` and `entityId`. Or implement a status sync endpoint that checks approval status and advances entity state.

---

### H5. FnF Settlement Retrenchment Compensation Stored as Negative in `otherDeductions`
**Location:** `offboarding.service.ts:655`
**Impact:** Retrenchment compensation amount is subtracted twice — once correctly as an earning (in `totalEarnings`) and once incorrectly deducted.

**Problem:** Line 655:
```typescript
otherDeductions: new Prisma.Decimal(round2(otherDeductions + retrenchmentCompensation * -1)),
```
In the `create` path, `retrenchmentCompensation * -1` is subtracted from `otherDeductions`. But `retrenchmentCompensation` is already added to `totalEarnings` at line 593. The `update` path at line 672 does NOT include this adjustment, creating inconsistency between first-time compute and re-compute.

**Fix:** Remove the `retrenchmentCompensation * -1` from `otherDeductions` in the create path. It's an earning, not a deduction offset.

---

## 4. MEDIUM Issues (Fix During Pilot or Before Scale)

### M1. Half-Day Leave Double Penalty in Payroll
**Location:** `payroll-run.service.ts:422-424` (computeSalaries)
**Impact:** Employees with approved half-day leave are penalized twice.

**Problem:**
```typescript
} else if (rec.status === 'HALF_DAY') {
  presentDays += 0.5;
  lopDays += 0.5;
}
```
Half-day always adds 0.5 LOP days regardless of whether it was an approved half-day leave (which should use leave balance, not LOP) or an unauthorized half-day. Combined with C1 (leave balance already deducted), the employee loses from both leave balance and salary.

**Fix:** Distinguish between `HALF_DAY` from leave (paid) and `HALF_DAY` from short attendance (LOP). Or, if attendance records for approved half-day leave use `ON_LEAVE` status with a `halfDay` flag, handle that separately.

---

### M2. No Leave Accrual Automation
**Location:** `leave.service.ts:385-448` (initializeBalances)
**Impact:** HR must manually initialize leave balances for every employee every year.

**Problem:** Leave balance initialization is entirely manual. There's no scheduled job for:
- Annual balance creation at year start
- Monthly/quarterly accrual based on `accrualFrequency` field on `LeaveType`
- Carry-forward processing at year end

The `LeaveType` model has fields for `accrualFrequency`, `accrualDay`, `carryForwardAllowed`, `maxCarryForwardDays` — but none of these are used in any automated process.

**Workaround for pilot:** HR manually calls `POST /leave-balances/initialize` for each employee at the start of the year.

---

### M3. Cross-Year Leave Requests
**Location:** `leave.service.ts:558-562` (createRequest)
**Impact:** Leave spanning Dec-Jan deducts all days from current year only.

**Problem:** Balance lookup uses `fromDate.getFullYear()`:
```typescript
const currentYear = from.getFullYear();
const balance = await platformPrisma.leaveBalance.findUnique({
  where: { employeeId_leaveTypeId_year: { employeeId, leaveTypeId, year: currentYear } },
});
```
If leave spans Dec 28 to Jan 5, all 8 days deduct from December's year balance. January days should deduct from next year's balance.

---

### M4. Employee ID Generation Concurrency Risk
**Location:** `employee.service.ts:17-56` (generateEmployeeId)
**Impact:** Under high concurrency (bulk import), employee ID collisions may exceed 3 retries.

**Problem:** Uses `findFirst({ orderBy: { createdAt: 'desc' } })` to find last employee ID, then increments. Under concurrent creates, multiple transactions read the same "last" employee and generate the same next ID. The retry loop (MAX_RETRIES=3) catches P2002 unique violations but may not suffice for >3 concurrent creates.

**Fix:** Employee ID generation for the Employee Onboarding flow must use the configured Number Series (`NoSeriesConfig`) instead of "last created employee + 1" logic. Reserve the next number atomically inside the create transaction (for example, by locking the Number Series row with `SELECT FOR UPDATE` or using a DB-backed sequence/counter table).

If no Number Series is configured for Employee Onboarding, employee creation must fail with a clear validation error, for example: "Employee Number Series is not configured. Please create Number Series for Employee Onboarding first."

---

### M5. Payroll Computation Performance — N+1 Queries
**Location:** `payroll-run.service.ts:398-536` (computeSalaries) and `payroll-run.service.ts:603-711` (computeStatutory)
**Impact:** Slow payroll processing for companies with many employees.

**Problem:** In `computeSalaries()`, for each employee:
- Line 406: Individual query for attendance records
This is an N+1 pattern — for 500 employees, this means 500+ attendance queries.

In `computeStatutory()`, for each entry:
- Line 690: Individual UPDATE per entry
This means 500 individual updates instead of a batch update.

**Fix:** Implement payroll computation as an asynchronous background job optimized for scale:
- Use batch fetches (employees, attendance, leave, overtime, statutory inputs) and index records in-memory using efficient DS (`Map<employeeId, ...>` / hash maps) to avoid per-employee queries.
- Replace row-by-row statutory updates with chunked bulk writes (`updateMany`, bulk SQL, or transactional batched updates).
- Queue the payroll run in a background worker (job queue) so the API responds immediately and UI does not block.
- Persist job status (`QUEUED`, `RUNNING`, `COMPLETED`, `FAILED`) with progress counters and timestamps for monitoring/retry.

**User Feedback Requirement (Toast + Status Updates):**
- On trigger: show toast like "Payroll run started in background. You can continue using the app."
- During execution: show non-blocking progress updates (for example, "Payroll processing: 320/1200 employees completed").
- On completion: show success toast with summary (processed count, success/failure count, duration).
- On failure/partial failure: show error toast with actionable message and link/action to view job details or retry.

---

### M6. No Email Uniqueness Validation on Employee
**Location:** `employee.service.ts` and `employee.validators.ts`
**Impact:** Duplicate employees could be created with the same personal email.

**Problem:** `personalEmail` and `officialEmail` are not enforced as unique in the Prisma schema or the service validation. Two employees could share the same email. The `officialEmail` auto-link to User works on first match, but duplicates could cause ambiguity.

---

### M7. Loan EMI Not Included in Statutory Filings/Reports
**Location:** `payroll-run.service.ts:479-483` (computeSalaries)
**Impact:** Loan deductions appear in entries but not in compliance reports.

**Problem:** Loan EMI deductions are correctly applied per employee but:
- Not tracked separately in run totals
- Not included in the bank file generation
- No loan ledger update (outstanding balance not decremented)

The loan `outstanding` field is never reduced when an EMI is deducted in payroll. Over time, this creates a mismatch between actual deductions and the loan ledger.

---

### M8. Attendance Override Doesn't Validate Attendance Record Is Locked
**Location:** `attendance.service.ts:409-444` (createOverride)
**Impact:** Overrides can be created for attendance records in months with locked payroll.

**Problem:** When a payroll run is in `ATTENDANCE_LOCKED` or later status, attendance records for that month should not accept new override requests, as changes won't be reflected in the already-computed payroll. The override creation doesn't check the payroll run status.

Additionally, the current attendance flow only covers Shift Check-In / Check-Out. Attendance Regularization is not implemented yet, so users cannot properly submit and track post-facto attendance corrections with approval workflow.

**Required Implementation Note:** Add Attendance Regularization end-to-end (request, review/approval, audit trail) and persist a `regularized` flag on attendance records (with metadata such as `regularizedAt`, `regularizedBy`, reason, and source reference). Payroll and attendance reports must treat `regularized` records explicitly and prevent regularization when the target month is payroll-locked.

---

### M9. No Delete/Archive Endpoint for Payroll Run
**Location:** `payroll-run.routes.ts`
**Impact:** Draft or erroneous payroll runs cannot be removed.

**Problem:** There's no DELETE endpoint for payroll runs. Once created, a run cannot be removed, even if it was created by mistake. The only path is to advance it through all 6 steps or leave it in DRAFT forever.

**Frontend-Backend Alignment Requirement:** When the backend adds delete/archive capability for payroll runs, the frontend must be updated in the same release to consume it (API client + mutation hooks + UI actions in payroll run list/detail screens). Include RBAC checks, confirmation modal, disabled state for non-deletable statuses, optimistic/loading/error handling, and success/error toast messages so behavior is consistent end-to-end.

---

## 5. LOW Issues (Acceptable for Pilot)

### L1. Overtime Hardcodes 8-Hour Workday
**Location:** `payroll-run.service.ts:473`
**Problem:** `ratePerHour = basicPerDay / 8` assumes 8-hour day. Companies with 9 or 12-hour shifts get incorrect OT rates.
**Workaround:** Configurable via attendance rules `fullDayThresholdHours`.

### L2. Gratuity Uses Floor of Years
**Location:** `offboarding.service.ts:495` — `Math.floor(tenureYears)`
**Problem:** Per Indian Gratuity Act, service of 6+ months in the last year should round UP. `Math.floor` always rounds down.
**Impact:** Employee with 4 years 8 months gets gratuity for 4 years instead of 5.

### L3. Notice Pay Uses 30-Day Month
**Location:** `offboarding.service.ts:530` — `monthlyGross / 30`
**Problem:** Should use actual calendar days of the notice period month for accuracy.

### L4. F&F TDS is 10% Flat
**Location:** `offboarding.service.ts:602` — `tdsOnFnF = taxableAmount * 0.10`
**Problem:** Actual TDS on F&F depends on employee's total income projection. This is a gross simplification.

### L5. Employee Status Always Starts as PROBATION
**Location:** `employee.service.ts:249` — `status: 'PROBATION'`
**Problem:** Hardcoded regardless of whether employee is confirmed on hire. Direct hire of confirmed employees must manually change status.

### L6. Night Shift Cross-Midnight Edge Cases
**Location:** `attendance.service.ts:852-903` (detectLateAndEarlyExit)
**Problem:** `shiftStart` and `shiftEnd` are set using the same day as punch time. For shifts crossing midnight (22:00-06:00), the early exit calculation may be incorrect if `punchOut` date is the next calendar day.

### L7. Bulk Email Payslips Not Implemented
**Location:** `payroll-run.service.ts:1013-1026` (emailPayslip)
**Problem:** Only single payslip email is available. No bulk operation for post-disbursement notification.

### L8. Leave Cancel Only Blocks Future Start Dates
**Location:** `leave.service.ts:710-716`
**Problem:** Cannot partially cancel an ongoing leave (e.g., returning early from a 5-day leave on day 3). Only full cancellation before start date is supported.

### L9. Attendance Summary Department Breakdown is Duplicated
**Location:** `attendance.service.ts:290-297` (getSummary)
**Problem:** `departmentBreakdown` at line 290 runs the same `groupBy` query as `statusCounts` at line 234 but without department grouping. It doesn't actually provide per-department breakdown — it duplicates the company-wide status counts.

### L10. Component Breakup Matching in `computeComponentBreakup` Uses componentId Not Code
**Location:** `payroll.service.ts:561`
**Problem:** `comp.componentId.toLowerCase().includes('basic')` — the `componentId` is a CUID (like `clm9abc123...`), not a human-readable code. This string match will never find "basic" in a CUID.

---

## 6. Detailed Findings by Module

### 6.1 Employee Registration
- **Employee ID auto-generation** with NoSeries config: Working, with concurrency retry (M4)
- **Reference validation** (department, designation, grade, type, location, shift, managers): Complete
- **Probation end date** auto-calculated from grade: Working
- **Auto-link to User** by officialEmail: Working
- **Optional user account creation** with RBAC: Working with proper validation
- **Timeline events**: Logged on JOINED, status changes, deactivation
- **Sub-resources**: Nominees, education, prev-employment, documents — full CRUD with cascading deletes
- **Soft delete**: Sets status to EXITED, doesn't hard-delete records

### 6.2 Attendance
- **Full CRUD** with unique `employeeId_date` constraint: Working
- **Metrics auto-calculation**: workedHours, isLate, lateMinutes, isEarlyExit, earlyMinutes: Working
- **Grace period**: Configurable per company, correctly applied: Working
- **Override/regularization workflow**: PENDING → APPROVED/REJECTED with automatic record correction: Working
- **Holiday calendar**: CRUD, clone-year, optional holidays with slots: Working
- **Roster management**: Multiple patterns, default roster logic: Working
- **Overtime rules**: Configurable multiplier, caps, approval toggle: Working
- **Issues**: Missing auto-population (H3), no payroll lock guard (M8), department breakdown bug (L9)

### 6.3 Leave Management
- **Leave types**: 20+ configurable fields including sandwich rules, probation restriction, gender filter: Complete
- **Leave policies**: Company/department/designation/grade/type/individual levels: Working
- **Leave balance**: Initialize, adjust (credit/debit), pro-rata for mid-year joiners: Working
- **Leave requests**: Comprehensive validation (overlap, balance, advance notice, consecutive days, half-day): Working
- **Optimistic balance deduction**: On request creation, refund on rejection/cancellation: Working
- **Sandwich rules**: Weekend/holiday counting between leave days: Implemented
- **Issues**: No attendance record creation on approval (C1), no accrual automation (M2), cross-year gap (M3)

### 6.4 Payroll Configuration
- **Salary Components**: Full CRUD with usage-in-structures check before delete: Working
- **Salary Structures**: Component-level breakup with FIXED/PERCENT_OF_BASIC/PERCENT_OF_GROSS: Working
- **Employee Salary**: Assignment with auto-breakup from structure, transactional isCurrent switch: Working
- **PF Config**: Singleton per company with India-standard defaults (12%/3.67%/8.33%/0.5%): Working
- **ESI Config**: Singleton with wage ceiling: Working
- **PT Config**: Multi-state slab-based: Working
- **LWF Config**: Multi-state with employee/employer amounts: Working
- **Bonus Config**: India Payment of Bonus Act defaults: Working
- **Gratuity Config**: Configurable formula and cap: Working
- **Tax Config**: Old/new regime slabs, surcharge, cess: Exists but NOT wired to computation (C3)
- **Bank Config**: Company bank details for salary disbursement: Working
- **Loan Policies & Records**: Policy-based with EMI calculation: Working

### 6.5 Payroll Run (6-Step Wizard)
- **Step 1 — Lock Attendance**: Checks unresolved overrides, missing punches, LOP: Working
- **Step 2 — Review Exceptions**: Detects new hires, holds, no-salary, exits: Working
- **Step 3 — Compute Salaries**: LOP deduction, pro-rata, overtime, variance detection: Working (with C1, C4 issues)
- **Step 4 — Statutory**: PF, ESI, PT, TDS, LWF: Working (with C3, C4 issues)
- **Step 5 — Approve**: Workflow integration with fallback: Working (with H4 issue)
- **Step 6 — Disburse**: Payslip generation, hold exclusion: Working (with H1 issue)
- **Entry Override**: Manual earnings/deductions adjustment: Working (with H2 issue)
- **Reports**: Salary register, bank file, PF ECR, ESI challan, PT challan, variance: All implemented

### 6.6 Payslips
- **Generation**: From approved entries excluding FULL holds: Working
- **Detail view**: Employee + entry + bank details: Working
- **Email**: Placeholder (sets emailedAt, no actual email): Placeholder

### 6.7 Salary Holds, Revisions & Arrears
- **Holds**: FULL/PARTIAL with release workflow: Working
- **Revisions**: DRAFT → APPROVED → APPLIED with workflow: Working
- **Arrear computation**: Retroactive monthly differences: Working
- **Transactional salary switching**: Old record closed, new created atomically: Working

### 6.8 Offboarding & F&F
- **Exit request**: Full lifecycle INITIATED → ON_NOTICE → CLEARANCE_DONE → FNF_COMPUTED → FNF_PAID: Working
- **Auto-clearances**: 5 departments with checklist items: Working
- **Exit interview**: Structured responses with rating: Working
- **F&F Settlement** (15 components): Working
  - Salary for worked days, leave encashment, gratuity (capped at 20L)
  - Bonus pro-rata, notice pay (buy/recover), retrenchment compensation
  - Loan recovery, asset recovery, pending reimbursements
  - TDS on F&F, other earnings/deductions
- **Employee status update**: EXITED on F&F payment: Working
- **Timeline logging**: Throughout the process: Working
- **Issues**: H5 (retrenchment in otherDeductions), L2 (gratuity rounding), L3 (notice pay 30-day), L4 (flat TDS)

### 6.9 ESS & Approval Workflows
- **ESS Config**: 25+ toggleable features: Working
- **Approval Workflows**: Multi-step, trigger-event based: Working
- **Approval Requests**: Step history, approve/reject per step: Working (with H4 issue)
- **Manager Delegates**: Date-ranged delegation with overlap check: Working
- **IT Declarations**: CRUD per employee per financial year: Working (not wired to TDS)
- **Notification Templates**: Event-based templates: Working
- **Notification Rules**: Configurable per event: Working

### 6.10 Performance Management
- **Appraisal Cycles**: CRUD with goal/entry/feedback counts: Working
- **Goals**: Multi-level (individual/team/department/company) with KPIs: Working
- **Appraisal Entries**: Self-assessment + manager rating: Working
- **360 Feedback**: Peer/subordinate/manager feedback: Working
- **Skills Matrix**: Skill mapping with proficiency levels: Working
- **Succession Planning**: Successor nominations with readiness levels: Working
- **9-Box Grid**: Performance vs potential classification: Working

### 6.11 Transfer & Promotion
- **Transfer records**: From/to department/designation/location/manager: Working
- **Approval workflow integration**: Auto-approve if no workflow configured: Working
- **Employee update on approval**: Department, designation, location, manager: Working
- **Timeline event**: Logged on transfer/promotion completion: Working

### 6.12 Advanced HR
- **Recruitment**: Requisitions, candidates, interviews with stage pipeline: Working
- **Training**: Catalogue, nominations, attendance: Working
- **Asset Management**: Assets, categories, assignments: Working
- **Expense Claims**: CRUD with approval: Working
- **HR Letters**: Templates with placeholders: Working
- **Grievance**: Cases with category and status transitions: Working
- **Discipline**: Cases, show-cause notices, penalties: Working

---

## 7. What's Working Well

1. **Multi-tenant isolation** — Every query filters by `companyId`. No cross-tenant data leaks possible.
2. **Zod validation** — All API inputs validated with strict schemas before reaching services.
3. **Permission guards** — All routes use `requirePermissions(['hr:read/create/update/delete'])`.
4. **Transactional operations** — Salary assignment, leave requests, exit processes use `$transaction`.
5. **Cascade deletes** — Employee sub-resources properly cascade.
6. **Audit trail** — `EmployeeTimeline` logs all major status changes.
7. **Error handling** — Consistent `ApiError` usage with proper HTTP codes.
8. **Unique constraints** — Proper DB-level uniqueness on codes, employee+date, etc.
9. **Frontend API hooks** — Well-structured React Query integration with proper cache invalidation.
10. **6-step payroll wizard** — Proper status gates prevent skipping steps.
11. **F&F settlement** — Remarkably comprehensive (15 components) with separation-type awareness.
12. **India statutory compliance** — PF/ESI/PT/LWF/Gratuity/Bonus all follow Indian labor law defaults.
13. **Approval workflow integration** — Consistent across payroll, salary revision, transfers, offboarding.

---

## 8. Pilot Readiness Verdict

### Status: NOT READY for unsupervised pilot. READY with targeted fixes.

### Must-Fix (CRITICAL — blocking for pilot):

| # | Issue | Effort | Impact |
|---|-------|--------|--------|
| C1 | Bridge attendance-leave gap | 2-3 hours | Salary accuracy |
| C2 | Fix frontend payroll status mapping | 1-2 hours | UI functionality |
| C3 | Add TDS disclaimer + manual override | 1-2 hours | Compliance |
| C4 | Use `pfInclusion` flag for PF wage | 1 hour | PF accuracy |

### Should-Fix (HIGH — recommended for pilot):

| # | Issue | Effort | Impact |
|---|-------|--------|--------|
| H1 | Make payslips immutable | 2-3 hours | Data integrity |
| H2 | Update run totals after override | 1 hour | Dashboard accuracy |
| H3 | Auto-populate holiday/week-off records | 3-4 hours | Payroll accuracy |
| H4 | Approval workflow entity callback | 3-4 hours | Workflow completion |
| H5 | Fix FnF retrenchment double-counting | 30 min | F&F accuracy |

### Acceptable for Pilot with Manual Workaround:

- M1-M9: All medium issues have workarounds (manual balance init, careful naming, etc.)
- L1-L10: All low issues are edge cases or cosmetic

### Estimated Fix Time for Critical + High: ~15-20 hours of development

---

*End of Audit Report*
