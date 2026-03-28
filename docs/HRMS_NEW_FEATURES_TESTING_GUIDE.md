# HRMS New Features — Testing & Usage Guide

**Purpose:** This guide covers ALL new backend features implemented during the HRMS audit remediation. Since these features currently have backend APIs only (no frontend screens yet), this document shows how to test and verify each feature using API calls.

**Base URL:** `http://localhost:3000/api/v1/hr` (adjust host/port as needed)
**Auth:** All requests require `Authorization: Bearer <token>` header (get token from login API)
**Content-Type:** `application/json`

---

## Quick Reference — New Endpoints by Feature

| Feature | Endpoints | Section |
|---------|-----------|---------|
| Onboarding Checklist | 9 endpoints | [1](#1-onboarding-checklist-red-6) |
| Probation Review | 3 endpoints | [2](#2-probation-review-red-7) |
| Org Chart | 1 endpoint | [3](#3-org-chart-ora-10) |
| Form 16 & 24Q | 3 endpoints | [4](#4-form-16--24q-red-4) |
| Bonus Batch | 5 endpoints | [5](#5-bonus-batch-ora-6) |
| E-Sign Integration | 4 endpoints | [6](#6-e-sign-integration-ora-7) |
| AI HR Chatbot | 6 endpoints | [7](#7-ai-hr-chatbot-ora-8) |
| Production Incentive | 8 endpoints | [8](#8-production-incentive-ora-9) |
| GDPR / Data Retention | 10 endpoints | [9](#9-gdpr--data-retention-ora-11) |
| Shift Rotation | 7 endpoints | [10](#10-shift-rotation-yel-6) |
| Biometric Devices | 6 endpoints | [11](#11-biometric-device-management-yel-7) |
| Travel Advance | 3 endpoints | [12](#12-travel-advance-yel-9) |
| Leave Accrual & Carry-Forward | 3 endpoints | [13](#13-leave-accrual--carry-forward) |
| Comp-Off Accrual | 1 endpoint | [14](#14-comp-off-accrual) |
| Attendance Auto-Population | 1 endpoint | [15](#15-attendance-auto-population) |

---

## 1. Onboarding Checklist (RED-6)

### What it does
When a new employee is created, the system auto-generates onboarding tasks (IT setup, ID card, email creation, etc.) from a configurable template. HR can track task completion by department.

### Setup: Create a Template
```bash
POST /api/v1/hr/onboarding/templates
{
  "name": "Standard Full-Time Onboarding",
  "isDefault": true,
  "items": [
    { "title": "Create email account", "department": "IT", "dueInDays": 1, "isMandatory": true },
    { "title": "Issue laptop/desktop", "department": "IT", "dueInDays": 1, "isMandatory": true },
    { "title": "Create system access", "department": "IT", "dueInDays": 1, "isMandatory": true },
    { "title": "Generate ID card", "department": "ADMIN", "dueInDays": 1, "isMandatory": true },
    { "title": "Assign parking pass", "department": "ADMIN", "dueInDays": 3, "isMandatory": false },
    { "title": "Schedule induction program", "department": "HR", "dueInDays": 5, "isMandatory": true },
    { "title": "Collect documents", "department": "HR", "dueInDays": 7, "isMandatory": true },
    { "title": "PF enrollment", "department": "HR", "dueInDays": 30, "isMandatory": true },
    { "title": "ESI registration", "department": "HR", "dueInDays": 10, "isMandatory": true }
  ]
}
```

### Auto-Trigger: Create an Employee
When you create any new employee via `POST /api/v1/hr/employees`, if a default template exists, tasks are auto-generated.

### Check Tasks for an Employee
```bash
GET /api/v1/hr/onboarding/tasks?employeeId={employeeId}
```

### Check Progress
```bash
GET /api/v1/hr/onboarding/progress/{employeeId}
# Returns: { total: 9, completed: 0, pending: 9, byDepartment: { IT: { total: 3, completed: 0 }, HR: { total: 4, completed: 0 }, ADMIN: { total: 2, completed: 0 } } }
```

### Complete a Task
```bash
PATCH /api/v1/hr/onboarding/tasks/{taskId}
{ "status": "COMPLETED", "notes": "Laptop MacBook Pro issued" }
```

---

## 2. Probation Review (RED-7)

### What it does
Lists employees whose probation is ending within 30 days. Manager can submit a review with rating, feedback, and decision (Confirm / Extend / Terminate).

### Check Who Needs Review
```bash
GET /api/v1/hr/employees/probation-due
# Returns employees with status=PROBATION and probationEndDate within 30 days
```

### Submit Review
```bash
POST /api/v1/hr/employees/{employeeId}/probation-review
{
  "performanceRating": 4,
  "managerFeedback": "Strong technical skills, good team player. Recommend confirmation.",
  "decision": "CONFIRMED"
}
```

Decisions: `CONFIRMED` (status → CONFIRMED), `EXTENDED` (probation extended), `TERMINATED` (status → EXITED)

For extension:
```bash
{ "performanceRating": 2, "managerFeedback": "Needs improvement.", "decision": "EXTENDED", "extensionMonths": 3 }
```

---

## 3. Org Chart (ORA-10)

### What it does
Returns a hierarchical tree of all active employees based on reporting manager relationships.

```bash
GET /api/v1/hr/employees/org-chart
# Returns tree: [ { id, name, designation, department, reportees: [ { id, name, ..., reportees: [...] } ] } ]
```

---

## 4. Form 16 & 24Q (RED-4)

### What it does
Generates Form 16 (annual TDS certificate) and Form 24Q (quarterly TDS return) from payroll data.

### Generate Form 16
```bash
POST /api/v1/hr/payroll-reports/form-16
{ "financialYear": "2025-26" }
# Returns per-employee Form 16 Part B: gross, deductions, Chapter VI-A, net taxable, TDS summary, monthly breakdown
```

### Generate Form 24Q
```bash
POST /api/v1/hr/payroll-reports/form-24q
{ "quarter": 1, "financialYear": "2025-26" }
# Returns NSDL-format deductee records: PAN, amount paid, TDS deducted/deposited per employee
```

### Bulk Email Form 16
```bash
POST /api/v1/hr/payroll-reports/form-16/bulk-email
{ "financialYear": "2025-26" }
```

---

## 5. Bonus Batch (ORA-6)

### What it does
Process bulk bonuses (performance, festive, spot awards) for multiple employees at once, with TDS computation and payroll merge.

### Create a Bonus Batch
```bash
POST /api/v1/hr/bonus-batches
{
  "name": "Q1 Performance Bonus 2026",
  "bonusType": "PERFORMANCE",
  "items": [
    { "employeeId": "emp_id_1", "amount": 50000, "remarks": "Exceeds expectations" },
    { "employeeId": "emp_id_2", "amount": 30000, "remarks": "Meets expectations" },
    { "employeeId": "emp_id_3", "amount": 75000, "remarks": "Outstanding" }
  ]
}
# TDS auto-calculated per item. Returns batch with total amount.
```

### Approve
```bash
PATCH /api/v1/hr/bonus-batches/{batchId}/approve
```

### Merge to Payroll Run
```bash
POST /api/v1/hr/bonus-batches/{batchId}/merge
{ "payrollRunId": "run_id" }
# Adds BONUS component to each employee's payroll entry
```

---

## 6. E-Sign Integration (ORA-7)

### What it does
Dispatches HR letters (offer, appointment, confirmation, etc.) for electronic signature. Tracks signing status.

### Dispatch a Letter for E-Sign
```bash
POST /api/v1/hr/hr-letters/{letterId}/dispatch-esign
# Returns: { signingUrl, eSignStatus: "PENDING", dispatchedTo: "employee@email.com" }
```

### Check Status
```bash
GET /api/v1/hr/hr-letters/{letterId}/esign-status
# Returns: { eSignStatus: "PENDING" | "SIGNED" | "DECLINED", eSignedAt, eSignDispatchedAt }
```

### List All Pending Signatures
```bash
GET /api/v1/hr/hr-letters/pending-esign
```

### Webhook Callback (from e-sign provider)
```bash
POST /api/v1/hr/hr-letters/esign-callback
{ "signingToken": "esign_xxx_123", "status": "SIGNED" }
```

---

## 7. AI HR Chatbot (ORA-8)

### What it does
An intent-based chatbot that answers employee HR queries by querying live HRMS data. Supports: leave balance, payslip info, attendance, holidays, HR contact, policies.

### Start a Conversation
```bash
POST /api/v1/hr/chatbot/conversations
{ "channel": "WEB" }
# Returns: { id: "conv_id", status: "ACTIVE" }
```

### Send a Message
```bash
POST /api/v1/hr/chatbot/conversations/{conversationId}/messages
{ "content": "What is my leave balance?" }
# Returns: { intent: "LEAVE_BALANCE", message: "Here are your leave balances:\n\nCasual Leave (CL): 8 days remaining\nPrivilege Leave (PL): 12 days remaining", data: { balances: [...] } }
```

### Try Different Intents
```
"What is my leave balance?"      → LEAVE_BALANCE (queries leaveBalance table)
"Show my payslip"                → PAYSLIP (queries latest payslip)
"How is my attendance this month" → ATTENDANCE (counts present/absent/leave)
"Next holiday?"                  → HOLIDAY (queries holidayCalendar)
"I want to talk to HR"           → HR_CONTACT (offers escalation)
"What is the leave policy?"      → POLICY (directs to ESS documents)
"Hello"                          → GREETING (welcome message)
"Thanks bye"                     → THANKS (closing message)
```

### Escalate to HR
```bash
PATCH /api/v1/hr/chatbot/conversations/{conversationId}/escalate
```

### Get Chat History
```bash
GET /api/v1/hr/chatbot/conversations/{conversationId}/messages
```

---

## 8. Production Incentive (ORA-9)

### What it does
For manufacturing companies — configure machine/department-wise production incentive slabs, record daily output, compute incentive amounts, and merge into payroll.

### Create Incentive Config
```bash
POST /api/v1/hr/production-incentives/configs
{
  "name": "CNC Machine Incentive",
  "incentiveBasis": "COMPONENT_WISE",
  "calculationCycle": "MONTHLY",
  "departmentId": "dept_id",
  "slabs": [
    { "minOutput": 0, "maxOutput": 99, "amount": 0 },
    { "minOutput": 100, "maxOutput": 120, "amount": 500 },
    { "minOutput": 121, "maxOutput": 150, "amount": 800 },
    { "minOutput": 151, "maxOutput": 180, "amount": 1200 },
    { "minOutput": 181, "maxOutput": 99999, "amount": 1500 }
  ]
}
```

### Record Output & Compute Incentives
```bash
POST /api/v1/hr/production-incentives/configs/{configId}/compute
{
  "period": "2026-03-01",
  "records": [
    { "employeeId": "emp_1", "outputUnits": 135 },
    { "employeeId": "emp_2", "outputUnits": 165 },
    { "employeeId": "emp_3", "outputUnits": 95 }
  ]
}
# Returns: emp_1 gets ₹800, emp_2 gets ₹1200, emp_3 gets ₹0
```

### Merge to Payroll
```bash
POST /api/v1/hr/production-incentives/configs/{configId}/merge
{ "month": 3, "year": 2026, "payrollRunId": "run_id" }
```

---

## 9. GDPR / Data Retention (ORA-11)

### What it does
Manages data retention policies, employee data access requests (GDPR), data export, anonymisation, and consent tracking.

### Set Retention Policies
```bash
POST /api/v1/hr/retention/policies
{ "dataCategory": "EMPLOYEE_MASTER", "retentionYears": 7, "actionAfter": "ANONYMISE" }

POST /api/v1/hr/retention/policies
{ "dataCategory": "PAYROLL", "retentionYears": 7, "actionAfter": "ARCHIVE" }

POST /api/v1/hr/retention/policies
{ "dataCategory": "ATTENDANCE", "retentionYears": 5, "actionAfter": "DELETE" }
```

### Employee Data Access Request (GDPR)
```bash
POST /api/v1/hr/retention/data-requests
{ "requestType": "PORTABILITY", "description": "I need a copy of all my personal data" }
```

### Export Employee Data
```bash
GET /api/v1/hr/retention/data-export/{employeeId}
# Returns comprehensive JSON: personal info (masked), employment history, salary, leave, attendance, training, performance
```

### Anonymise Exited Employee
```bash
POST /api/v1/hr/retention/anonymise/{employeeId}
# Replaces PII with pseudonyms. Only works for EXITED employees.
```

### Record Consent
```bash
POST /api/v1/hr/retention/consents
{ "employeeId": "emp_id", "consentType": "BIOMETRIC_COLLECTION", "granted": true }
```

### Check What's Due for Retention Action
```bash
GET /api/v1/hr/retention/check-due
# Returns: [{ dataCategory: "EMPLOYEE_MASTER", count: 3, suggestedAction: "ANONYMISE" }, ...]
```

---

## 10. Shift Rotation (YEL-6)

### What it does
Automates employee shift changes on a weekly/fortnightly/monthly cycle.

### Create Rotation Schedule
```bash
POST /api/v1/hr/shift-rotations
{
  "name": "Manufacturing 3-Shift Rotation",
  "rotationPattern": "WEEKLY",
  "shifts": [
    { "shiftId": "morning_shift_id", "weekNumber": 1 },
    { "shiftId": "afternoon_shift_id", "weekNumber": 2 },
    { "shiftId": "night_shift_id", "weekNumber": 3 }
  ],
  "effectiveFrom": "2026-04-01"
}
```

### Assign Employees
```bash
POST /api/v1/hr/shift-rotations/{scheduleId}/assign
{ "employeeIds": ["emp_1", "emp_2", "emp_3"] }
```

### Execute Rotation (Run Manually or via Cron)
```bash
POST /api/v1/hr/shift-rotations/execute
# Calculates current shift for each schedule and updates employee shiftId
# Returns: { schedulesProcessed: 1, employeesRotated: 3 }
```

---

## 11. Biometric Device Management (YEL-7)

### What it does
Register and manage biometric attendance devices (ZKTeco, ESSL, etc.). Test connectivity. Sync attendance data.

### Register a Device
```bash
POST /api/v1/hr/biometric-devices
{
  "name": "Main Entrance Fingerprint",
  "brand": "ZKTeco",
  "deviceId": "ZK-001",
  "ipAddress": "192.168.1.100",
  "port": 4370,
  "syncMode": "PULL",
  "syncIntervalMin": 5,
  "locationId": "branch_location_id"
}
```

### Test Connection
```bash
POST /api/v1/hr/biometric-devices/{deviceId}/test
# Returns: { deviceId: "ZK-001", status: "ONLINE" | "OFFLINE" }
```

### Sync Attendance from Device
```bash
POST /api/v1/hr/biometric-devices/{deviceId}/sync
{
  "records": [
    { "employeeId": "emp_1", "date": "2026-03-28", "punchIn": "2026-03-28T09:02:00", "punchOut": "2026-03-28T18:15:00" },
    { "employeeId": "emp_2", "date": "2026-03-28", "punchIn": "2026-03-28T08:55:00", "punchOut": "2026-03-28T17:50:00" }
  ]
}
# Returns: { synced: 2, errors: 0, total: 2 }
```

---

## 12. Travel Advance (YEL-9)

### What it does
Request a lump-sum travel advance before a trip. After the trip, settle against the expense claim — system calculates who owes whom.

### Request Travel Advance
```bash
POST /api/v1/hr/loans/travel-advance
{ "employeeId": "emp_id", "amount": 25000, "tripPurpose": "Client visit to Mumbai" }
```

### After Trip: Settle Against Expense Claim
First, create and get approved an expense claim (via existing expense claim flow). Then:
```bash
POST /api/v1/hr/loans/{loanId}/settle-travel
{ "expenseClaimId": "claim_id" }
# Returns: { advanceAmount: 25000, claimAmount: 22000, difference: 3000, outcome: "EMPLOYEE_OWES", remainingOutstanding: 3000 }
```

Outcomes:
- `EMPLOYEE_OWES` — advance was more than actual expenses (difference recovered in payroll)
- `COMPANY_OWES` — actual expenses exceeded advance (difference paid via payroll)
- `EXACT` — perfect match

---

## 13. Leave Accrual & Carry-Forward

### Run Monthly Accrual
```bash
POST /api/v1/hr/leave-balances/accrue
{ "month": 4, "year": 2026 }
# Credits leave balances based on accrualFrequency configured on each leave type
```

### Year-End Carry-Forward
```bash
POST /api/v1/hr/leave-balances/carry-forward
{ "fromYear": 2025, "toYear": 2026 }
# Carries forward eligible leave balances (up to maxCarryForwardDays) as opening balance
```

### Partial Leave Cancellation
```bash
PATCH /api/v1/hr/leave-requests/{requestId}/partial-cancel
{ "cancelFromDate": "2026-04-05" }
# Cancels remaining days, refunds balance, removes attendance records
```

---

## 14. Comp-Off Accrual

### Process Monthly Comp-Off
```bash
POST /api/v1/hr/attendance/process-comp-off
{ "month": 3, "year": 2026 }
# Scans for employees who worked on holidays/week-offs and credits comp-off leave balance
```

---

## 15. Attendance Auto-Population

### Populate Holidays & Week-Offs for a Month
```bash
POST /api/v1/hr/attendance/populate-month
{ "month": 4, "year": 2026 }
# Creates HOLIDAY and WEEK_OFF attendance records for all active employees
# based on holiday calendar and roster configuration
```

---

## Frontend Status & Next Steps

These features currently have **backend APIs only**. Frontend screens need to be built for:

| Priority | Feature | Recommended Platform |
|----------|---------|---------------------|
| HIGH | Onboarding Checklist | Web (HR admin) + Mobile (ESS for new joiners) |
| HIGH | Probation Review | Web (HR admin + Manager) |
| HIGH | Form 16/24Q | Web (HR admin) |
| HIGH | Bonus Batch | Web (HR admin) |
| MEDIUM | AI Chatbot | Mobile (ESS chat widget) + Web (ESS) |
| MEDIUM | Org Chart | Web (visual tree) + Mobile (simplified list) |
| MEDIUM | Biometric Devices | Web (admin only) |
| MEDIUM | Shift Rotation | Web (HR admin) |
| MEDIUM | Data Retention/GDPR | Web (HR admin) |
| LOW | E-Sign | Web (integrated into existing HR Letters screen) |
| LOW | Production Incentive | Web (HR + Operations admin) |
| LOW | Travel Advance | Web (integrated into existing Loans screen) |

To build these screens, the developer needs to:
1. Create API client functions in `lib/api/{feature}.ts`
2. Create React Query hooks in `features/company-admin/api/use-{feature}-queries.ts` and `use-{feature}-mutations.ts`
3. Create screen components in `features/company-admin/hr/{feature}-screen.tsx`
4. Add route files in `app/(app)/company/{feature}.tsx` (mobile) or update routing (web)
5. Add navigation entries in sidebar sections

---

## How to Test Right Now (Without Frontend)

### Option 1: Use curl/Postman
Follow the API examples above. Get a token first:
```bash
POST /api/v1/auth/login
{ "email": "admin@company.com", "password": "your_password" }
# Copy the token from response
```

### Option 2: Use the Swagger/API docs
If the backend has Swagger enabled, visit `http://localhost:3000/api-docs`

### Option 3: Test via backend scripts
```bash
cd avy-erp-backend
# Run a quick test script
npx ts-node -e "
const { PrismaClient } = require('@prisma/client');
const prisma = new PrismaClient();
async function test() {
  const templates = await prisma.onboardingTemplate.findMany();
  console.log('Onboarding templates:', templates.length);
  const devices = await prisma.biometricDevice.findMany();
  console.log('Biometric devices:', devices.length);
  const schedules = await prisma.shiftRotationSchedule.findMany();
  console.log('Shift schedules:', schedules.length);
}
test().then(() => process.exit());
"
```

---

*This guide covers all 74 new API endpoints across 15 feature areas. Each can be tested independently via the API calls shown above.*
