# Comprehensive HRMS Seed Script — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Create a modular, extensible seed script that populates ALL HRMS tables with realistic test data (employees, attendance, leave, payroll, payslips, performance, recruitment, training, assets, expenses, analytics) for any given company.

**Architecture:** Modular seeder architecture — a coordinator script (`seed-hrms-data.ts`) that calls domain-specific seeders (`seeders/*.ts`) in dependency order. Each seeder is independent, takes a Prisma client + context, and returns created IDs for downstream seeders. CLI arguments control scope (company, months, employee count).

**Tech Stack:** TypeScript, Prisma Client (direct DB), tsx runner, Luxon for dates

---

## File Structure

```
scripts/
├── seed-hrms-data.ts              # Main entry — CLI args, coordinator
├── seeders/
│   ├── types.ts                   # Shared types & context interface
│   ├── utils.ts                   # Fake data generators (reuse from seed-company.ts)
│   ├── 01-statutory-config.ts     # PF, ESI, PT, Tax, Gratuity, Bonus, LWF, Bank
│   ├── 02-salary-structures.ts    # Salary components check + create structures
│   ├── 03-employees.ts            # Employee records + nominees, education, documents
│   ├── 04-employee-salaries.ts    # Assign salaries to employees
│   ├── 05-attendance.ts           # Daily attendance records for N months
│   ├── 06-leave.ts                # Leave balances + requests
│   ├── 07-payroll.ts              # Payroll runs + entries + payslips
│   ├── 08-performance.ts          # Appraisal cycles, goals, entries, 360 feedback, skills
│   ├── 09-recruitment.ts          # Job requisitions, candidates, interviews
│   ├── 10-training.ts             # Training catalogue + nominations
│   ├── 11-assets.ts               # Asset assignments
│   ├── 12-expenses.ts             # Expense claims + items
│   ├── 13-loans.ts                # Loan records
│   ├── 14-letters.ts              # HR letter templates + generated letters
│   ├── 15-grievances.ts           # Grievance cases + disciplinary actions
│   ├── 16-onboarding.ts           # Onboarding templates + tasks, probation reviews
│   ├── 17-exit.ts                 # Exit requests, clearance, interviews, F&F
│   ├── 18-requests.ts             # Shift swap, WFH, overtime, IT declarations
│   ├── 19-transfers.ts            # Transfers, promotions, manager delegates
│   ├── 20-policies.ts             # Policy documents
│   ├── 21-analytics.ts            # Daily/monthly analytics snapshots
│   └── 22-statutory-filings.ts    # Statutory filing records
```

---

## CLI Interface

```bash
npx tsx scripts/seed-hrms-data.ts \
  --company-id <cuid>           # Required: target company ID
  --months 3                    # Past months of data (default: 2)
  --employees 30                # Employees to create (default: 25, 0 = skip)
  --skip-existing               # Don't fail if employees exist, create alongside
  --only <module>               # Seed only one module (e.g., --only attendance)
  --dry-run                     # Print what would be seeded, don't write
  --verbose                     # Detailed logging
```

npm script in package.json:
```json
"seed:hrms": "npx tsx scripts/seed-hrms-data.ts"
```

---

## Task 1: Shared Types & Utilities

**Files:**
- Create: `scripts/seeders/types.ts`
- Create: `scripts/seeders/utils.ts`

- [ ] **Step 1: Create types.ts**

```typescript
import type { PrismaClient } from '@prisma/client';

/** Context passed to every seeder module */
export interface SeedContext {
  /** Platform Prisma client (public schema) */
  prisma: PrismaClient;
  /** Tenant Prisma client (tenant schema — for models like AttendanceRecord that live in tenant DB) */
  tenantPrisma: PrismaClient;
  /** Target company ID */
  companyId: string;
  /** Tenant ID */
  tenantId: string;
  /** Number of past months to seed */
  months: number;
  /** Verbose logging */
  verbose: boolean;
  /** Dry run (no writes) */
  dryRun: boolean;

  // ── Accumulated IDs from upstream seeders ──
  employeeIds: string[];
  managerIds: string[];
  departmentIds: string[];
  designationIds: string[];
  gradeIds: string[];
  employeeTypeIds: string[];
  locationIds: string[];
  shiftIds: string[];
  costCentreIds: string[];
  salaryComponentIds: string[];
  salaryStructureIds: string[];
  leaveTypeIds: string[];
  /** Map employeeId → employee data snapshot */
  employeeMap: Map<string, {
    id: string;
    firstName: string;
    lastName: string;
    email: string;
    departmentId: string;
    designationId: string;
    gradeId: string;
    employeeTypeId: string;
    locationId: string;
    shiftId: string;
    joiningDate: string;
    status: string;
  }>;
}

export interface SeederModule {
  name: string;
  /** Dependency order (lower runs first) */
  order: number;
  /** Run the seeder — mutates ctx to add created IDs */
  seed: (ctx: SeedContext) => Promise<void>;
}

export function log(ctx: SeedContext, module: string, msg: string): void {
  console.log(`  [${module}] ${msg}`);
}

export function vlog(ctx: SeedContext, module: string, msg: string): void {
  if (ctx.verbose) console.log(`    [${module}] ${msg}`);
}
```

- [ ] **Step 2: Create utils.ts**

Extract and expand fake data generators from the existing `seed-company.ts` pattern. Include:
- `pickRandom`, `randomInt`, `randomDate`, `randomDigits`, `randomPhone`
- `fakePAN`, `fakeTAN`, `fakeAadhaar`, `fakeUAN`, `fakeIFSC`, `fakeBankAccount`
- `generateEmployeeName` (realistic Indian names)
- `workingDaysInMonth(year, month, holidays, weeklyOffs)` — computes working days
- `dateRange(startDate, endDate)` — yields each date in range
- `businessDate(date)` — checks if date is a working day

- [ ] **Step 3: Commit**

```bash
git add scripts/seeders/
git commit -m "feat: add seed script types and utilities"
```

---

## Task 2: Main Coordinator Script

**Files:**
- Create: `scripts/seed-hrms-data.ts`
- Modify: `package.json` (add seed:hrms script)

- [ ] **Step 1: Create seed-hrms-data.ts**

The coordinator:
1. Parses CLI args
2. Connects to platform + tenant Prisma clients
3. Fetches existing master data (departments, grades, etc.) to populate ctx
4. Dynamically imports and runs seeders in order
5. Reports summary

Key logic:
```typescript
// Fetch existing master data from the company
const departments = await prisma.department.findMany({ where: { companyId } });
const designations = await prisma.designation.findMany({ where: { companyId } });
const grades = await prisma.grade.findMany({ where: { companyId } });
// ... populate ctx with IDs

// Run seeders in order
const seeders = [
  await import('./seeders/01-statutory-config'),
  await import('./seeders/02-salary-structures'),
  // ...
].sort((a, b) => a.order - b.order);

for (const seeder of seeders) {
  if (only && seeder.name !== only) continue;
  console.log(`\n▸ ${seeder.name}...`);
  await seeder.seed(ctx);
}
```

- [ ] **Step 2: Add package.json script**

```json
"seed:hrms": "npx tsx scripts/seed-hrms-data.ts"
```

- [ ] **Step 3: Commit**

```bash
git add scripts/seed-hrms-data.ts package.json
git commit -m "feat: add HRMS seed coordinator with CLI args"
```

---

## Task 3: Statutory Config Seeder (01)

**Files:**
- Create: `scripts/seeders/01-statutory-config.ts`

Seeds: PFConfig, ESIConfig, PTConfig (Karnataka), TaxConfig (FY 2025-26 new regime), GratuityConfig, BonusConfig, LWFConfig, BankConfig

Uses `upsert` so it's idempotent — safe to re-run.

---

## Task 4: Salary Structures Seeder (02)

**Files:**
- Create: `scripts/seeders/02-salary-structures.ts`

Creates 3 salary structures (if none exist):
- **Junior CTC** — for Grade G1-G2 (3-6 LPA range)
- **Mid CTC** — for Grade G3 (6-12 LPA range)
- **Senior CTC** — for Grade G4-G5 (12-25 LPA range)

Uses existing salary components from the company.

---

## Task 5: Employee Seeder (03)

**Files:**
- Create: `scripts/seeders/03-employees.ts`

Creates N employees with:
- Realistic Indian names (pool of 50 first + 50 last names)
- Spread across departments, designations, grades
- 3-4 managers (first created), rest report to them
- Status mix: 85% ACTIVE, 5% PROBATION, 5% ON_NOTICE, 5% CONFIRMED
- Joining dates spread across past 6-24 months
- Personal details: DOB, gender, blood group, marital status, emergency contact
- EmployeeNominee (1-2 per employee)
- EmployeeEducation (1-2 per employee)
- EmployeePrevEmployment (0-2 per employee)
- EmployeeDocument (PAN, Aadhaar for each)
- EmployeeTimeline (JOINED event)
- User account creation (role: USER)
- TenantUser linking to Employee role

---

## Task 6: Employee Salary Seeder (04)

**Files:**
- Create: `scripts/seeders/04-employee-salaries.ts`

Assigns salary to each employee:
- Picks structure based on grade (Junior/Mid/Senior)
- CTC range based on grade (G1: 3-5L, G2: 5-8L, G3: 8-12L, G4: 12-18L, G5: 18-25L)
- Creates EmployeeSalary with isCurrent=true
- Computes component breakup using the structure's computation logic

---

## Task 7: Attendance Seeder (05)

**Files:**
- Create: `scripts/seeders/05-attendance.ts`

For each past month × each employee:
- Fetches holidays and weekly offs
- For each working day, creates AttendanceRecord:
  - 88% PRESENT (normal check-in/out with slight time variations)
  - 4% LATE (late check-in, random 15-60 min late)
  - 3% HALF_DAY (early checkout or late check-in)
  - 2% ABSENT (no record — creates with status ABSENT)
  - 2% ON_LEAVE (linked to leave request)
  - 1% OVERTIME (extra hours, creates OvertimeRequest)
- Realistic punch times: shift start ± 15min check-in, shift end ± 30min check-out
- Geo-tagged with company location coordinates

---

## Task 8: Leave Seeder (06)

**Files:**
- Create: `scripts/seeders/06-leave.ts`

1. Creates LeaveBalance for each employee × each leave type for current FY
2. Creates 30-50 LeaveRequests across all employees:
   - 70% APPROVED, 15% PENDING, 10% REJECTED, 5% CANCELLED
   - Mix of CL (1-2 days), SL (1-3 days), EL (3-5 days)
   - Dates within the seed period

---

## Task 9: Payroll Seeder (07)

**Files:**
- Create: `scripts/seeders/07-payroll.ts`

For each past month:
1. Creates PayrollRun (status varies: oldest = FINALIZED, recent = APPROVED)
2. For each ACTIVE employee, creates PayrollEntry:
   - Reads attendance data to compute presentDays, lopDays
   - Reads salary components to compute earnings
   - Applies statutory deductions (PF, ESI, PT) from config
   - Computes TDS estimate
   - Sets gross, deductions, netPay
3. Creates Payslip for each entry (status: PAID for finalized runs)
4. Creates 1-2 SalaryRevision records (for 5% of employees)

---

## Task 10: Performance Seeder (08)

**Files:**
- Create: `scripts/seeders/08-performance.ts`

1. Creates 1 AppraisalCycle (Annual FY 2025-26, status: IN_PROGRESS)
2. Creates 3-5 Goals per employee (mix of company/dept/individual)
3. Creates AppraisalEntry for each employee (self-rating done, manager pending)
4. Creates 10-15 Feedback360 records (peer reviews)
5. Seeds SkillLibrary (10 skills)
6. Creates SkillMapping for each employee (3-5 skills)
7. Creates 2-3 SuccessionPlan entries for senior roles

---

## Task 11: Recruitment Seeder (09)

**Files:**
- Create: `scripts/seeders/09-recruitment.ts`

1. Creates 3-5 JobRequisitions (mix of OPEN, IN_PROGRESS, CLOSED)
2. Creates 10-20 Candidates across requisitions (various stages)
3. Creates Interview records for shortlisted candidates

---

## Task 12: Training Seeder (10)

**Files:**
- Create: `scripts/seeders/10-training.ts`

1. Creates 5-8 TrainingCatalogue entries (mix of types)
2. Creates 15-20 TrainingNominations (mix of statuses)

---

## Task 13: Assets Seeder (11)

**Files:**
- Create: `scripts/seeders/11-assets.ts`

1. Checks existing AssetCategories (seeded during onboarding)
2. Creates 20-30 Asset records (laptops, phones, access cards)
3. Creates AssetAssignment for 60% of employees

---

## Task 14: Expenses Seeder (12)

**Files:**
- Create: `scripts/seeders/12-expenses.ts`

1. Creates 15-25 ExpenseClaims with 2-5 ExpenseClaimItems each
2. Mix of statuses: APPROVED, PENDING, REJECTED, REIMBURSED
3. Categories: Travel, Food, Accommodation, Fuel

---

## Task 15: Loans Seeder (13)

**Files:**
- Create: `scripts/seeders/13-loans.ts`

1. Creates 5-8 LoanRecords (using existing LoanPolicies)
2. Mix: ACTIVE (with EMI schedule), CLOSED, PENDING_APPROVAL

---

## Task 16: HR Letters Seeder (14)

**Files:**
- Create: `scripts/seeders/14-letters.ts`

1. Creates 5 HRLetterTemplate records (Offer, Appointment, Confirmation, Promotion, Relieving)
2. Creates 10-15 HRLetter records (generated letters for employees)

---

## Task 17: Grievances & Disciplinary Seeder (15)

**Files:**
- Create: `scripts/seeders/15-grievances.ts`

1. Creates 3-5 GrievanceCases (mix of OPEN, RESOLVED, CLOSED)
2. Creates 2-3 DisciplinaryAction records

---

## Task 18: Onboarding & Probation Seeder (16)

**Files:**
- Create: `scripts/seeders/16-onboarding.ts`

1. Creates 2-3 OnboardingTemplates
2. Creates OnboardingTasks for recent joiners (last 2 months)
3. Creates ProbationReview for probation employees

---

## Task 19: Exit & F&F Seeder (17)

**Files:**
- Create: `scripts/seeders/17-exit.ts`

1. Creates 2-3 ExitRequests (APPROVED, PENDING) for ON_NOTICE employees
2. Creates ExitClearance records
3. Creates ExitInterview for approved exits
4. Creates FnFSettlement for completed exits

---

## Task 20: Requests Seeder (18)

**Files:**
- Create: `scripts/seeders/18-requests.ts`

1. Creates 5-8 ShiftSwapRequests
2. Creates 5-8 WfhRequests
3. Creates 5-10 OvertimeRequests (linked to attendance)
4. Creates 5-10 ITDeclarations (Section 80C, 80D, HRA)

---

## Task 21: Transfers & Promotions Seeder (19)

**Files:**
- Create: `scripts/seeders/19-transfers.ts`

1. Creates 2-3 EmployeeTransfer records
2. Creates 2-3 EmployeePromotion records
3. Creates 1-2 ManagerDelegate records

---

## Task 22: Policy Documents Seeder (20)

**Files:**
- Create: `scripts/seeders/20-policies.ts`

1. Creates 5-8 PolicyDocument records (Leave Policy, Code of Conduct, WFH Policy, etc.)

---

## Task 23: Analytics Seeder (21)

**Files:**
- Create: `scripts/seeders/21-analytics.ts`

For each past month × each day:
1. Creates EmployeeAnalyticsDaily (headcount, joiners, leavers by dept/grade/gender)
2. Creates AttendanceAnalyticsDaily (present/absent/late counts)
3. Creates PayrollAnalyticsMonthly (per month — gross, deductions, net, by dept)
4. Creates AttritionMetricsMonthly (attrition rate, exit reasons)

---

## Task 24: Statutory Filings Seeder (22)

**Files:**
- Create: `scripts/seeders/22-statutory-filings.ts`

1. Creates StatutoryFiling records for past months:
   - PF ECR (monthly)
   - ESI Challan (monthly)
   - PT (monthly)
   - TDS 24Q (quarterly)
   - Form 16 (annual — for previous FY if applicable)

---

## Task 25: Integration Test & Final Commit

- [ ] **Step 1: Run the seed script against the target company**

```bash
npx tsx scripts/seed-hrms-data.ts \
  --company-id cmnik7e0e000113fknp3o8kt2 \
  --months 3 \
  --employees 25 \
  --verbose
```

- [ ] **Step 2: Verify data via API**

```bash
# Check employee count
curl -s http://localhost:3030/api/v1/hr/employees?limit=1 -H "Authorization: Bearer $TOKEN" | jq '.meta.total'

# Check payroll runs
curl -s http://localhost:3030/api/v1/hr/payroll-runs -H "Authorization: Bearer $TOKEN" | jq '.meta.total'

# Check analytics
curl -s http://localhost:3030/api/v1/hr/analytics/executive -H "Authorization: Bearer $TOKEN" | jq '.data'
```

- [ ] **Step 3: Final commit**

```bash
git add scripts/
git commit -m "feat: add comprehensive HRMS seed script (25 modular seeders)"
```

---

## Summary

| Task | Seeder | Tables Seeded | Records |
|------|--------|---------------|---------|
| 3 | Statutory Config | PFConfig, ESIConfig, PTConfig, TaxConfig, GratuityConfig, BonusConfig, LWFConfig, BankConfig | 8 |
| 4 | Salary Structures | SalaryStructure | 3 |
| 5 | Employees | Employee, Nominee, Education, PrevEmpmt, Document, Timeline, User, TenantUser | ~200 |
| 6 | Employee Salaries | EmployeeSalary | 25 |
| 7 | Attendance | AttendanceRecord, AttendanceOverride | ~1,500 |
| 8 | Leave | LeaveBalance, LeaveRequest | ~250 |
| 9 | Payroll | PayrollRun, PayrollEntry, Payslip, SalaryRevision | ~180 |
| 10 | Performance | AppraisalCycle, Goal, AppraisalEntry, Feedback360, SkillLibrary, SkillMapping, SuccessionPlan | ~200 |
| 11 | Recruitment | JobRequisition, Candidate, Interview | ~30 |
| 12 | Training | TrainingCatalogue, TrainingNomination | ~25 |
| 13 | Assets | Asset, AssetAssignment | ~40 |
| 14 | Expenses | ExpenseClaim, ExpenseClaimItem | ~80 |
| 15 | Loans | LoanRecord | 8 |
| 16 | Letters | HRLetterTemplate, HRLetter | ~20 |
| 17 | Grievances | GrievanceCase, DisciplinaryAction | ~8 |
| 18 | Onboarding | OnboardingTemplate, OnboardingTask, ProbationReview | ~30 |
| 19 | Exit & F&F | ExitRequest, ExitClearance, ExitInterview, FnFSettlement | ~12 |
| 20 | Requests | ShiftSwapRequest, WfhRequest, OvertimeRequest, ITDeclaration | ~30 |
| 21 | Transfers | EmployeeTransfer, EmployeePromotion, ManagerDelegate | ~8 |
| 22 | Policies | PolicyDocument | 8 |
| 23 | Analytics | EmployeeAnalyticsDaily, AttendanceAnalyticsDaily, PayrollAnalyticsMonthly, AttritionMetricsMonthly | ~200 |
| 24 | Statutory Filings | StatutoryFiling | ~15 |
| **Total** | | **~76 model types** | **~2,900 records** |
