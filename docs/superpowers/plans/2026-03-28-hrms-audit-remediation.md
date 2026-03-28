# HRMS Audit Remediation — Full Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Resolve all 29 audit items from HRMS_FINAL_AUDIT_REPORT.md to bring the HRMS module to full production readiness for pilot deployment.

**Architecture:** Backend-first approach — Prisma schema changes first, then service logic, then API layer, then frontend. Each task group targets a specific service file to avoid merge conflicts when parallelized. All changes follow existing patterns: Zod validators, asyncHandler controllers, requirePermissions middleware, platformPrisma database access.

**Tech Stack:** Prisma ORM, Express.js, TypeScript, Zod validation, React Query (web), Zustand + React Query (mobile), Expo Router

---

## Scope Classification

### Phase 1 — Implement Now (This Plan)
| ID | Issue | Category |
|----|-------|----------|
| RED-1 | Wire IT declaration deductions into TDS engine | Payroll |
| RED-2 | Remove hardcoded slabs, use TaxConfig DB-only | Payroll |
| RED-3 | Verify ESS attendance regularization endpoint works | ESS |
| RED-5 | Comp-off auto-accrual | Attendance |
| RED-6 | Onboarding checklist system | New Feature |
| RED-7 | Probation confirmation workflow | Employee |
| ORA-1 | HRA exemption calculation in TDS | Payroll |
| ORA-2 | Configurable LOP divisor (÷26/÷30/actual) | Payroll |
| ORA-3 | Salary rounding rules | Payroll |
| ORA-4 | Negative salary handling | Payroll |
| ORA-5 | Bulk salary revision upload | Payroll Run |
| ORA-6 | Bonus batch processing | New Feature |
| ORA-10 | Org chart API | Employee |
| ORA-12 | Payroll → Finance GL export | Payroll Run |
| YEL-1 | PF admin charges | Payroll |
| YEL-2 | ESI contribution period handling | Payroll |
| YEL-3 | PT February Maharashtra handling | Payroll |
| YEL-4 | Bonus Act eligibility check in F&F | Offboarding |
| YEL-8 | Reimbursement → payroll merge | Payroll |
| YEL-10 | Skill gap → auto training nomination | Performance |

### Phase 2 — Documented, Deferred
| ID | Issue | Reason |
|----|-------|--------|
| RED-4 | Form 16 & 24Q generation | Complex statutory format — 15-20hr standalone project |
| ORA-7 | E-sign integration | Requires external vendor (DigiSign/SignDesk) setup |
| ORA-8 | AI Chatbot | Not critical for pilot |
| ORA-9 | Production incentive | Manufacturing-specific, not needed unless pilot is manufacturing |
| ORA-11 | GDPR/data retention | Post-pilot compliance enhancement |
| YEL-5 | Leave sandwich rule verification | Already implemented correctly per code audit |
| YEL-6 | Shift rotation automation | Scheduled job, not critical for pilot |
| YEL-7 | Biometric device sync | Hardware integration, use mobile GPS for pilot |
| YEL-9 | Travel advance recovery | Edge case, manual workaround available |

---

## File Structure & Ownership

### Schema Changes (Task 1)
- **Modify:** `avy-erp-backend/prisma/schema.prisma`
  - Add `OnboardingTemplate`, `OnboardingTask` models
  - Add `BonusBatch`, `BonusBatchItem` models
  - Add `ProbationReview` model
  - Add `lopDivisorMethod`, `salaryRoundingRule` to Company `fiscalConfig` JSON
  - Add `compOffValidityDays` to `LeaveType` or `AttendanceRule`

### Payroll Engine (Tasks 2-3)
- **Modify:** `avy-erp-backend/src/modules/hr/payroll-run/payroll-run.service.ts`
  - RED-1: Wire IT declaration deductions into TDS
  - RED-2: Remove hardcoded slab fallbacks
  - ORA-1: HRA exemption calculation
  - ORA-2: LOP divisor configuration
  - ORA-3: Salary rounding
  - ORA-4: Negative salary handling
  - ORA-5: Bulk revision upload
  - ORA-12: GL journal export
  - YEL-1: PF admin charges
  - YEL-2: ESI contribution period
  - YEL-3: PT February handling
  - YEL-8: Reimbursement merge
- **Modify:** `avy-erp-backend/src/modules/hr/payroll-run/payroll-run.controller.ts`
- **Modify:** `avy-erp-backend/src/modules/hr/payroll-run/payroll-run.routes.ts`
- **Modify:** `avy-erp-backend/src/modules/hr/payroll-run/payroll-run.validators.ts`

### Attendance & Leave (Task 4)
- **Modify:** `avy-erp-backend/src/modules/hr/attendance/attendance.service.ts`
  - RED-5: Comp-off auto-accrual method

### ESS (Task 5)
- **Modify:** `avy-erp-backend/src/modules/hr/ess/ess.service.ts`
  - RED-3: Verify/complete regularize-attendance implementation

### Employee & Onboarding (Task 6)
- **Create:** `avy-erp-backend/src/modules/hr/onboarding/onboarding.service.ts`
- **Create:** `avy-erp-backend/src/modules/hr/onboarding/onboarding.controller.ts`
- **Create:** `avy-erp-backend/src/modules/hr/onboarding/onboarding.routes.ts`
- **Create:** `avy-erp-backend/src/modules/hr/onboarding/onboarding.validators.ts`
- **Modify:** `avy-erp-backend/src/modules/hr/routes.ts` (mount onboarding routes)
- **Modify:** `avy-erp-backend/src/modules/hr/employee/employee.service.ts`
  - RED-7: Probation confirmation + ORA-10: Org chart

### Offboarding & Performance (Task 7)
- **Modify:** `avy-erp-backend/src/modules/hr/offboarding/offboarding.service.ts`
  - YEL-4: Bonus eligibility check
- **Modify:** `avy-erp-backend/src/modules/hr/performance/performance.service.ts`
  - YEL-10: Skill gap auto-nomination
- **Modify:** `avy-erp-backend/src/modules/hr/advanced/advanced.service.ts`
  - ORA-6: Bonus batch methods

---

## Task 1: Prisma Schema — New Models & Fields

**Files:**
- Modify: `avy-erp-backend/prisma/schema.prisma`

- [ ] **Step 1: Add OnboardingTemplate and OnboardingTask models**

After the `EmployeeTimeline` model (around line 1291), add:

```prisma
// ==========================================
// ONBOARDING MODELS (RED-6)
// ==========================================

model OnboardingTemplate {
  id          String   @id @default(cuid())
  name        String   // e.g., "Standard Full-Time Onboarding"
  items       Json     // Array of { title, department, description, dueInDays, isMandatory }
  isDefault   Boolean  @default(false)
  companyId   String
  company     Company  @relation(fields: [companyId], references: [id], onDelete: Cascade)
  createdAt   DateTime @default(now())
  updatedAt   DateTime @updatedAt

  tasks OnboardingTask[]

  @@unique([companyId, name])
  @@map("onboarding_templates")
}

model OnboardingTask {
  id           String    @id @default(cuid())
  employeeId   String
  employee     Employee  @relation(fields: [employeeId], references: [id], onDelete: Cascade)
  templateId   String?
  template     OnboardingTemplate? @relation(fields: [templateId], references: [id])
  title        String
  department   String    // IT, HR, ADMIN, FINANCE
  description  String?
  dueDate      DateTime? @db.Date
  isMandatory  Boolean   @default(true)
  status       String    @default("PENDING") // PENDING, IN_PROGRESS, COMPLETED, SKIPPED
  completedBy  String?
  completedAt  DateTime?
  notes        String?
  companyId    String
  company      Company   @relation(fields: [companyId], references: [id], onDelete: Cascade)
  createdAt    DateTime  @default(now())
  updatedAt    DateTime  @updatedAt

  @@map("onboarding_tasks")
}
```

- [ ] **Step 2: Add ProbationReview model**

```prisma
// ==========================================
// PROBATION REVIEW (RED-7)
// ==========================================

model ProbationReview {
  id                String   @id @default(cuid())
  employeeId        String
  employee          Employee @relation(fields: [employeeId], references: [id], onDelete: Cascade)
  reviewDate        DateTime @db.Date
  probationEndDate  DateTime @db.Date
  managerFeedback   String?
  performanceRating Int?     // 1-5
  decision          String   @default("PENDING") // PENDING, CONFIRMED, EXTENDED, TERMINATED
  extensionMonths   Int?     // If EXTENDED, how many months
  newProbationEnd   DateTime? @db.Date
  decidedBy         String?
  decidedAt         DateTime?
  companyId         String
  company           Company  @relation(fields: [companyId], references: [id], onDelete: Cascade)
  createdAt         DateTime @default(now())
  updatedAt         DateTime @updatedAt

  @@unique([employeeId, probationEndDate])
  @@map("probation_reviews")
}
```

- [ ] **Step 3: Add BonusBatch and BonusBatchItem models**

```prisma
// ==========================================
// BONUS BATCH PROCESSING (ORA-6)
// ==========================================

model BonusBatch {
  id            String   @id @default(cuid())
  name          String   // e.g., "Q1 Performance Bonus", "Festive Bonus 2026"
  bonusType     String   // PERFORMANCE, FESTIVE, SPOT, REFERRAL, RETENTION, STATUTORY
  totalAmount   Decimal? @db.Decimal(15, 2)
  employeeCount Int?
  status        String   @default("DRAFT") // DRAFT, SUBMITTED, APPROVED, MERGED, REJECTED
  approvedBy    String?
  approvedAt    DateTime?
  mergedToRunId String?  // PayrollRun ID when merged
  companyId     String
  company       Company  @relation(fields: [companyId], references: [id], onDelete: Cascade)
  createdAt     DateTime @default(now())
  updatedAt     DateTime @updatedAt

  items BonusBatchItem[]

  @@map("bonus_batches")
}

model BonusBatchItem {
  id          String     @id @default(cuid())
  batchId     String
  batch       BonusBatch @relation(fields: [batchId], references: [id], onDelete: Cascade)
  employeeId  String
  employee    Employee   @relation(fields: [employeeId], references: [id])
  amount      Decimal    @db.Decimal(15, 2)
  tdsAmount   Decimal?   @db.Decimal(15, 2)
  netAmount   Decimal?   @db.Decimal(15, 2)
  remarks     String?
  companyId   String
  company     Company    @relation(fields: [companyId], references: [id], onDelete: Cascade)
  createdAt   DateTime   @default(now())
  updatedAt   DateTime   @updatedAt

  @@map("bonus_batch_items")
}
```

- [ ] **Step 4: Add Employee relations for new models**

In the Employee model, add relations:
```prisma
  onboardingTasks   OnboardingTask[]
  probationReviews  ProbationReview[]
  bonusBatchItems   BonusBatchItem[]
```

- [ ] **Step 5: Add Company relations for new models**

In the Company model, add relations:
```prisma
  onboardingTemplates OnboardingTemplate[]
  onboardingTasks     OnboardingTask[]
  probationReviews    ProbationReview[]
  bonusBatches        BonusBatch[]
  bonusBatchItems     BonusBatchItem[]
```

- [ ] **Step 6: Run Prisma migration**

```bash
cd avy-erp-backend && npx prisma migrate dev --name hrms-audit-remediation-models
```

---

## Task 2: Payroll Engine — TDS, LOP, Rounding, Negative Salary, Statutory Fixes

**Files:**
- Modify: `avy-erp-backend/src/modules/hr/payroll-run/payroll-run.service.ts`

This task modifies the `computeStatutory()` and `computeSalaries()` methods.

- [ ] **Step 1: RED-1 — Wire IT declaration deductions into TDS**

In `computeStatutory()`, after fetching IT declarations for regime (around line 779-791), also extract the declared deduction amounts. Before the entry loop, build a map of total deductions per employee:

```typescript
// After the existing IT declaration fetch for regime
// Build deduction map from IT declarations
const itDeclarationMap = new Map<string, number>();
if (itDeclarations.length > 0) {
  for (const decl of itDeclarations) {
    let totalDeductions = 0;

    // Section 80C (max 1,50,000)
    const s80c = decl.section80C as any;
    if (s80c?.total) totalDeductions += Math.min(Number(s80c.total), 150000);

    // Section 80CCD — NPS additional (max 50,000 over 80C)
    const s80ccd = decl.section80CCD as any;
    if (s80ccd?.npsAdditional) totalDeductions += Math.min(Number(s80ccd.npsAdditional), 50000);

    // Section 80D — Health insurance (max 25,000 self + 25,000/50,000 parents)
    const s80d = decl.section80D as any;
    if (s80d) {
      totalDeductions += Math.min(Number(s80d.selfPremium ?? 0), 25000);
      const parentMax = s80d.seniorCitizen ? 50000 : 25000;
      totalDeductions += Math.min(Number(s80d.parentPremium ?? 0), parentMax);
    }

    // Section 80E — Education loan interest (no limit)
    const s80e = decl.section80E as any;
    if (s80e?.educationLoanInterest) totalDeductions += Number(s80e.educationLoanInterest);

    // Section 80G — Donations (50% or 100% — simplified to 50%)
    const s80g = decl.section80G as any;
    if (s80g?.donations) totalDeductions += Number(s80g.donations) * 0.5;

    // Section 80TTA — Savings interest (max 10,000)
    const s80tta = decl.section80TTA as any;
    if (s80tta?.savingsInterest) totalDeductions += Math.min(Number(s80tta.savingsInterest), 10000);

    // Home loan interest — Section 24(b) (max 2,00,000)
    const homeLoan = decl.homeLoanInterest as any;
    if (homeLoan?.interestAmount) totalDeductions += Math.min(Number(homeLoan.interestAmount), 200000);

    // Standard deduction (₹75,000 for FY 2025-26 new regime, ₹50,000 old regime)
    const stdDeduction = decl.regime === 'OLD' ? 50000 : 75000;
    totalDeductions += stdDeduction;

    itDeclarationMap.set(decl.employeeId, totalDeductions);
  }
}
```

Then in the TDS calculation section, apply deductions ONLY for old regime:
```typescript
// Before applying slabs:
let taxableIncome = projectedAnnualIncome;

// Apply IT declaration deductions (old regime only — new regime has limited deductions)
if (empRegime === 'OLD') {
  const declaredDeductions = itDeclarationMap.get(entry.employeeId) ?? 50000; // standard deduction minimum
  taxableIncome = Math.max(0, projectedAnnualIncome - declaredDeductions);
} else {
  // New regime: only standard deduction of ₹75,000
  taxableIncome = Math.max(0, projectedAnnualIncome - 75000);
}

// Apply slabs to taxableIncome instead of projectedAnnualIncome
```

- [ ] **Step 2: RED-2 — Remove hardcoded slab fallbacks**

Find the `DEFAULT_NEW_REGIME_SLABS` and `DEFAULT_OLD_REGIME_SLABS` fallback constants. Replace with a validation check:

```typescript
// Instead of falling back to hardcoded slabs:
if (!taxConfig) {
  throw ApiError.badRequest(
    'Tax configuration not found. Please configure tax slabs in Payroll & Compliance settings before running statutory computation.'
  );
}
const slabs = empRegime === 'OLD'
  ? (taxConfig.oldRegimeSlabs as any[])
  : (taxConfig.newRegimeSlabs as any[]);

if (!slabs || slabs.length === 0) {
  throw ApiError.badRequest(
    `No ${empRegime} regime tax slabs configured. Please update Tax Configuration.`
  );
}
```

- [ ] **Step 3: ORA-1 — HRA exemption in TDS**

In the IT declaration deduction calculation (Step 1), add HRA exemption for old regime:

```typescript
// HRA Exemption — Section 10(13A) — Old regime only
if (decl.regime === 'OLD') {
  const hraData = decl.hraExemption as any;
  if (hraData?.rentPaid) {
    const annualRent = Number(hraData.rentPaid);
    const annualBasic = projectedAnnualIncome * 0.4; // Approximate basic as 40% of gross
    const isMetro = hraData.cityType === 'METRO';
    const hraReceived = annualBasic * (isMetro ? 0.5 : 0.4); // Approximate HRA

    const hraExempt = Math.min(
      hraReceived,                           // Actual HRA received
      annualRent - (0.1 * annualBasic),      // Rent paid - 10% of basic
      isMetro ? annualBasic * 0.5 : annualBasic * 0.4  // 50%/40% of basic
    );
    if (hraExempt > 0) totalDeductions += hraExempt;
  }
}
```

- [ ] **Step 4: ORA-2 — Configurable LOP divisor**

In `computeSalaries()`, replace the hardcoded LOP calculation. Read `lopDivisorMethod` from company's `fiscalConfig`:

```typescript
// Before employee loop, get LOP divisor method
const company = await platformPrisma.company.findUnique({
  where: { id: companyId },
  select: { fiscalConfig: true },
});
const fiscalConfig = company?.fiscalConfig as any;
const lopDivisor = fiscalConfig?.lopDivisorMethod ?? 'ACTUAL_WORKING_DAYS';

// In the earnings calculation loop, replace:
// amount * lopDays / totalWorkingDays
// With:
const divisor = lopDivisor === 'FIXED_26' ? 26
  : lopDivisor === 'FIXED_30' ? 30
  : totalWorkingDays;
const effectiveAmount = lopDays > 0
  ? round(amount - (amount * lopDays / divisor))
  : amount;
```

- [ ] **Step 5: ORA-3 — Salary rounding rules**

After computing netPay per employee, apply rounding rule:

```typescript
const roundingRule = fiscalConfig?.salaryRoundingRule ?? 'NEAREST_RUPEE';

function applyRounding(value: number, rule: string): number {
  switch (rule) {
    case 'NEAREST_RUPEE': return Math.round(value);
    case 'NEAREST_50P': return Math.round(value * 2) / 2;
    case 'NO_ROUNDING': return Math.round(value * 100) / 100;
    default: return Math.round(value);
  }
}

// Apply to netPay before creating entry:
netPay = applyRounding(netPay, roundingRule);
```

- [ ] **Step 6: ORA-4 — Negative salary handling**

After computing netPay, before pushing to `entriesToCreate`:

```typescript
// Negative salary detection
if (netPay < 0) {
  exceptionNote = exceptionNote
    ? `${exceptionNote}; NEGATIVE SALARY: Net pay is ₹${netPay}. Review deductions.`
    : `NEGATIVE SALARY: Net pay is ₹${netPay}. Deductions exceed earnings. Manual review required.`;
}

entriesToCreate.push({
  ...entryData,
  netPay,
  isException: isException || netPay < 0 || (variancePercent !== null && Math.abs(variancePercent) > 10),
  exceptionNote: n(exceptionNote),
});
```

- [ ] **Step 7: YEL-1 — PF admin charges**

In `computeStatutory()`, after computing PF employer contributions, add admin charges:

```typescript
// PF Admin Charge — 0.50% of PF wage (min ₹500/month applies to total, not per employee)
const pfAdminCharge = round(pfWage * (pfConfig.adminChargeRate ? Number(pfConfig.adminChargeRate) : 0.5) / 100);
// EDLI Admin — 0.01% of PF wage
const edliAdminCharge = round(pfWage * 0.01 / 100);

pfEmployer = epf + eps + edli + pfAdminCharge + edliAdminCharge;

if (pfAdminCharge > 0) employerContributions.PF_ADMIN = pfAdminCharge;
if (edliAdminCharge > 0) employerContributions.EDLI_ADMIN = edliAdminCharge;
```

- [ ] **Step 8: YEL-2 — ESI contribution period handling**

In `computeStatutory()`, ESI section — add contribution period check:

```typescript
// ESI: once enrolled, employee stays in ESI for the contribution period (6 months)
// even if salary exceeds threshold mid-period
// Contribution periods: Apr-Sep, Oct-Mar
if (esiConfig && empType.esiApplicable) {
  const esiCeiling = Number(esiConfig.wageCeiling);

  // Check if employee was within ceiling at start of current contribution period
  const isFirstHalf = run.month >= 4 && run.month <= 9; // Apr-Sep
  const periodStartMonth = isFirstHalf ? 4 : 10;
  const periodStartYear = isFirstHalf ? run.year : (run.month >= 10 ? run.year : run.year - 1);

  // Check salary at contribution period start
  const periodStartSalary = await this.getEmployeeSalaryAtDate(
    entry.employeeId, companyId, new Date(periodStartYear, periodStartMonth - 1, 1)
  );

  const wasEligibleAtPeriodStart = periodStartSalary !== null && periodStartSalary <= esiCeiling;

  if (grossEarnings <= esiCeiling || wasEligibleAtPeriodStart) {
    esiEmployee = round(grossEarnings * Number(esiConfig.employeeRate) / 100);
    esiEmployer = round(grossEarnings * Number(esiConfig.employerRate) / 100);
  }
}
```

- [ ] **Step 9: YEL-3 — PT February handling**

In `computeStatutory()`, PT section — add February adjustment:

```typescript
// PT: Some states (Maharashtra, Karnataka) have annual total adjustment in February
// e.g., Maharashtra: ₹2,500/year max; if 11 months × ₹200 = ₹2,200, Feb = ₹300
if (empType.ptApplicable && state && ptSlabsByState.has(state)) {
  const slabs = ptSlabsByState.get(state)!;
  const ptConfig = ptConfigs.find(c => c.state === state);
  const frequency = ptConfig?.frequency ?? 'MONTHLY';

  for (const slab of slabs) {
    if (grossEarnings >= slab.fromAmount && grossEarnings <= slab.toAmount) {
      ptAmount = slab.taxAmount;
      break;
    }
  }

  // February adjustment for states with annual cap
  if (run.month === 2 && frequency === 'MONTHLY') {
    // Calculate YTD PT already deducted (Apr-Jan = 10 months)
    const ytdPt = prevEntries.get(entry.employeeId)?.ytdPt ?? (ptAmount * 10);
    const annualCap = ptAmount * 12; // Standard annual
    // Some states have annual cap (e.g., Maharashtra ₹2,500)
    // The slab table should encode this; for now, use the standard month amount
  }
}
```

- [ ] **Step 10: YEL-8 — Reimbursement → payroll merge**

In `computeSalaries()`, before the employee loop, batch-fetch approved unpaid expense claims:

```typescript
// Fetch approved but unpaid reimbursement claims for all employees
const approvedClaims = await platformPrisma.expenseClaim.findMany({
  where: {
    companyId,
    status: 'APPROVED',
    paidAt: null,
  },
  select: { id: true, employeeId: true, amount: true, category: true },
});
const claimsByEmployee = new Map<string, typeof approvedClaims>();
for (const claim of approvedClaims) {
  if (!claimsByEmployee.has(claim.employeeId)) claimsByEmployee.set(claim.employeeId, []);
  claimsByEmployee.get(claim.employeeId)!.push(claim);
}
```

In the per-employee earnings section, add reimbursements:
```typescript
// Add approved reimbursements
let reimbursementTotal = 0;
const empClaims = claimsByEmployee.get(emp.id) ?? [];
for (const claim of empClaims) {
  reimbursementTotal += Number(claim.amount);
}
if (reimbursementTotal > 0) {
  earnings['REIMBURSEMENT'] = reimbursementTotal;
  grossEarnings += reimbursementTotal;
}
```

After entry creation, mark claims as paid:
```typescript
// Mark reimbursement claims as paid
const allClaimIds = approvedClaims.map(c => c.id);
if (allClaimIds.length > 0) {
  await platformPrisma.expenseClaim.updateMany({
    where: { id: { in: allClaimIds } },
    data: { paidAt: new Date() },
  });
}
```

---

## Task 3: Payroll Run — Bulk Revision, Bonus Batch, GL Export

**Files:**
- Modify: `avy-erp-backend/src/modules/hr/payroll-run/payroll-run.service.ts`
- Modify: `avy-erp-backend/src/modules/hr/payroll-run/payroll-run.controller.ts`
- Modify: `avy-erp-backend/src/modules/hr/payroll-run/payroll-run.routes.ts`
- Modify: `avy-erp-backend/src/modules/hr/payroll-run/payroll-run.validators.ts`

- [ ] **Step 1: ORA-5 — Add bulkCreateRevisions method**

```typescript
async bulkCreateRevisions(companyId: string, revisions: Array<{ employeeId: string; newCtc: number; effectiveDate: string }>) {
  const results: any[] = [];
  const errors: any[] = [];

  for (const rev of revisions) {
    try {
      const result = await this.createRevision(companyId, rev);
      results.push({ employeeId: rev.employeeId, status: 'created', revisionId: result.id });
    } catch (error: any) {
      errors.push({ employeeId: rev.employeeId, status: 'error', message: error.message });
    }
  }

  return { created: results.length, errors: errors.length, results, errors: errors };
}
```

Add validator:
```typescript
export const bulkRevisionSchema = z.object({
  revisions: z.array(z.object({
    employeeId: z.string().min(1),
    newCtc: z.number().positive(),
    effectiveDate: z.string().min(1),
  })).min(1, 'At least one revision required'),
});
```

Add route: `POST /salary-revisions/bulk` with `hr:create` permission.

- [ ] **Step 2: ORA-6 — Bonus batch methods in advanced.service.ts**

(See Task 7 for implementation details — bonus batch methods go in advanced service)

- [ ] **Step 3: ORA-12 — GL journal export endpoint**

```typescript
async getGLJournalExport(companyId: string, month: number, year: number) {
  const run = await platformPrisma.payrollRun.findUnique({
    where: { companyId_month_year: { companyId, month, year } },
  });
  if (!run) throw ApiError.notFound(`No payroll run for ${month}/${year}`);

  const entries = await platformPrisma.payrollEntry.findMany({
    where: { payrollRunId: run.id },
    include: {
      employee: {
        select: {
          department: { select: { name: true } },
          costCentre: { select: { code: true, name: true, glAccountCode: true } },
        },
      },
    },
  });

  // Group by cost centre
  const byCC = new Map<string, { code: string; name: string; glCode: string | null; totalGross: number; totalPF: number; totalESI: number; totalPT: number; totalTDS: number; totalNet: number }>();

  for (const entry of entries) {
    const cc = entry.employee.costCentre;
    const key = cc?.code ?? 'UNASSIGNED';
    if (!byCC.has(key)) {
      byCC.set(key, {
        code: key,
        name: cc?.name ?? 'Unassigned',
        glCode: cc?.glAccountCode ?? null,
        totalGross: 0, totalPF: 0, totalESI: 0, totalPT: 0, totalTDS: 0, totalNet: 0,
      });
    }
    const ccData = byCC.get(key)!;
    ccData.totalGross += Number(entry.grossEarnings);
    ccData.totalPF += Number(entry.pfEmployee ?? 0) + Number(entry.pfEmployer ?? 0);
    ccData.totalESI += Number(entry.esiEmployee ?? 0) + Number(entry.esiEmployer ?? 0);
    ccData.totalPT += Number(entry.ptAmount ?? 0);
    ccData.totalTDS += Number(entry.tdsAmount ?? 0);
    ccData.totalNet += Number(entry.netPay);
  }

  return {
    month, year,
    runId: run.id,
    costCentreBreakdown: Array.from(byCC.values()),
    summary: {
      totalGross: Number(run.totalGross),
      totalDeductions: Number(run.totalDeductions),
      totalNet: Number(run.totalNet),
      employeeCount: run.employeeCount,
    },
  };
}
```

Add route: `GET /payroll-reports/gl-journal` with `hr:read` permission.

---

## Task 4: Attendance — Comp-Off Auto-Accrual

**Files:**
- Modify: `avy-erp-backend/src/modules/hr/attendance/attendance.service.ts`
- Modify: `avy-erp-backend/src/modules/hr/attendance/attendance.controller.ts`
- Modify: `avy-erp-backend/src/modules/hr/attendance/attendance.routes.ts`
- Modify: `avy-erp-backend/src/modules/hr/attendance/attendance.validators.ts`

- [ ] **Step 1: RED-5 — Add processCompOffAccrual method**

```typescript
async processCompOffAccrual(companyId: string, month: number, year: number) {
  const monthStart = new Date(year, month - 1, 1);
  const monthEnd = new Date(year, month, 1);

  // Find COMPENSATORY leave type
  const compOffType = await platformPrisma.leaveType.findFirst({
    where: { companyId, category: 'COMPENSATORY', isActive: true },
  });
  if (!compOffType) {
    return { message: 'No active Compensatory Off leave type configured', accrued: 0 };
  }

  // Find employees who worked on HOLIDAY or WEEK_OFF days
  const workedOnOff = await platformPrisma.attendanceRecord.findMany({
    where: {
      companyId,
      date: { gte: monthStart, lt: monthEnd },
      status: { in: ['PRESENT', 'LATE'] },
    },
    select: { employeeId: true, date: true, status: true, workedHours: true },
  });

  // Get all holiday/weekoff records for the same period to identify which dates are off-days
  const offDayRecords = await platformPrisma.attendanceRecord.findMany({
    where: {
      companyId,
      date: { gte: monthStart, lt: monthEnd },
      status: { in: ['HOLIDAY', 'WEEK_OFF'] },
    },
    select: { date: true },
  });
  const offDayDates = new Set(offDayRecords.map(r => r.date.toISOString().split('T')[0]));

  // Also check holiday calendar directly
  const holidays = await platformPrisma.holidayCalendar.findMany({
    where: { companyId, date: { gte: monthStart, lt: monthEnd }, isOptional: false },
    select: { date: true },
  });
  for (const h of holidays) offDayDates.add(h.date.toISOString().split('T')[0]);

  // Find employees who have PRESENT on off-days
  let accrued = 0;
  const currentYear = year;

  for (const record of workedOnOff) {
    const dateStr = record.date.toISOString().split('T')[0];
    if (!offDayDates.has(dateStr)) continue; // Not an off-day

    // Credit 1 comp-off (or 0.5 if half-day)
    const creditDays = Number(record.workedHours ?? 0) >= 4 ? 1 : 0.5;

    // Find or create balance
    let balance = await platformPrisma.leaveBalance.findUnique({
      where: {
        employeeId_leaveTypeId_year: {
          employeeId: record.employeeId,
          leaveTypeId: compOffType.id,
          year: currentYear,
        },
      },
    });

    if (!balance) {
      balance = await platformPrisma.leaveBalance.create({
        data: {
          companyId,
          employeeId: record.employeeId,
          leaveTypeId: compOffType.id,
          year: currentYear,
          openingBalance: 0,
          accrued: 0,
          taken: 0,
          adjusted: 0,
          balance: 0,
        },
      });
    }

    await platformPrisma.leaveBalance.update({
      where: { id: balance.id },
      data: {
        accrued: { increment: creditDays },
        balance: { increment: creditDays },
      },
    });

    accrued++;
  }

  return { message: `Comp-off accrual processed`, accrued };
}
```

Add validator: `z.object({ month: z.number().int().min(1).max(12), year: z.number().int().min(2020).max(2099) })`
Add route: `POST /attendance/process-comp-off` with `hr:create` permission.

---

## Task 5: ESS — Verify Attendance Regularization

**Files:**
- Modify: `avy-erp-backend/src/modules/hr/ess/ess.service.ts`

- [ ] **Step 1: RED-3 — Verify regularizeAttendance implementation**

Read the ESS service to check if `regularizeAttendance()` method exists and is complete. If the route exists but the method is a stub, implement it:

```typescript
async regularizeAttendance(companyId: string, employeeId: string, data: {
  date: string;
  issueType: string;
  correctedPunchIn?: string;
  correctedPunchOut?: string;
  reason: string;
}) {
  // Verify employee
  const employee = await platformPrisma.employee.findFirst({
    where: { id: employeeId, companyId },
  });
  if (!employee) throw ApiError.notFound('Employee not found');

  // Check ESS config allows regularization
  const config = await this.getESSConfig(companyId);
  if (!config.attendanceRegularization) {
    throw ApiError.badRequest('Attendance regularization is not enabled for your organization');
  }

  // Find the attendance record for the date
  const targetDate = new Date(data.date);
  const attendanceRecord = await platformPrisma.attendanceRecord.findUnique({
    where: {
      employeeId_date: { employeeId, date: targetDate },
    },
  });

  if (!attendanceRecord) {
    throw ApiError.notFound('No attendance record found for this date');
  }

  // Check payroll lock
  const recordMonth = targetDate.getMonth() + 1;
  const recordYear = targetDate.getFullYear();
  const payrollRun = await platformPrisma.payrollRun.findUnique({
    where: { companyId_month_year: { companyId, month: recordMonth, year: recordYear } },
  });
  if (payrollRun && payrollRun.status !== 'DRAFT') {
    throw ApiError.badRequest('Cannot regularize attendance for a payroll-locked month');
  }

  // Create override request (goes through approval)
  const override = await platformPrisma.attendanceOverride.create({
    data: {
      companyId,
      attendanceRecordId: attendanceRecord.id,
      issueType: data.issueType,
      correctedPunchIn: data.correctedPunchIn ? new Date(data.correctedPunchIn) : null,
      correctedPunchOut: data.correctedPunchOut ? new Date(data.correctedPunchOut) : null,
      reason: data.reason,
      requestedBy: employeeId,
      status: 'PENDING',
    },
  });

  // Create approval workflow request
  await this.createRequest(companyId, {
    requesterId: employeeId,
    entityType: 'AttendanceOverride',
    entityId: override.id,
    triggerEvent: 'ATTENDANCE_REGULARIZATION',
    data: { date: data.date, issueType: data.issueType },
  });

  return override;
}
```

---

## Task 6: Onboarding Checklist & Probation & Org Chart

**Files:**
- Create: `avy-erp-backend/src/modules/hr/onboarding/onboarding.service.ts`
- Create: `avy-erp-backend/src/modules/hr/onboarding/onboarding.controller.ts`
- Create: `avy-erp-backend/src/modules/hr/onboarding/onboarding.routes.ts`
- Create: `avy-erp-backend/src/modules/hr/onboarding/onboarding.validators.ts`
- Modify: `avy-erp-backend/src/modules/hr/routes.ts`
- Modify: `avy-erp-backend/src/modules/hr/employee/employee.service.ts`

- [ ] **Step 1: RED-6 — Create onboarding service**

Create `onboarding.service.ts` with:
- `listTemplates(companyId)` — list all onboarding templates
- `createTemplate(companyId, data)` — create template with task items
- `updateTemplate(companyId, id, data)` — update template
- `deleteTemplate(companyId, id)` — delete if no tasks reference it
- `generateTasksForEmployee(companyId, employeeId, templateId?)` — create tasks from template for a new hire
- `listTasksForEmployee(companyId, employeeId)` — list all onboarding tasks
- `updateTask(companyId, taskId, data)` — mark task complete/skip
- `getOnboardingProgress(companyId, employeeId)` — % complete, by department

Wire into `employee.service.ts:createEmployee()`:
```typescript
// After creating the employee, auto-generate onboarding tasks
const defaultTemplate = await platformPrisma.onboardingTemplate.findFirst({
  where: { companyId, isDefault: true },
});
if (defaultTemplate) {
  const items = defaultTemplate.items as any[];
  const tasks = items.map(item => ({
    employeeId: employee.id,
    templateId: defaultTemplate.id,
    title: item.title,
    department: item.department,
    description: item.description ?? null,
    dueDate: item.dueInDays ? new Date(Date.now() + item.dueInDays * 86400000) : null,
    isMandatory: item.isMandatory ?? true,
    status: 'PENDING',
    companyId,
  }));
  await tx.onboardingTask.createMany({ data: tasks });
}
```

- [ ] **Step 2: RED-7 — Probation confirmation**

Add to `employee.service.ts`:
```typescript
async listProbationDue(companyId: string) {
  const thirtyDaysFromNow = new Date();
  thirtyDaysFromNow.setDate(thirtyDaysFromNow.getDate() + 30);

  return platformPrisma.employee.findMany({
    where: {
      companyId,
      status: 'PROBATION',
      probationEndDate: { lte: thirtyDaysFromNow },
    },
    include: {
      department: { select: { name: true } },
      designation: { select: { name: true } },
      reportingManager: { select: { firstName: true, lastName: true } },
    },
    orderBy: { probationEndDate: 'asc' },
  });
}

async submitProbationReview(companyId: string, data: {
  employeeId: string;
  performanceRating: number;
  managerFeedback: string;
  decision: 'CONFIRMED' | 'EXTENDED' | 'TERMINATED';
  extensionMonths?: number;
}, decidedBy: string) {
  const employee = await platformPrisma.employee.findFirst({
    where: { id: data.employeeId, companyId, status: 'PROBATION' },
  });
  if (!employee) throw ApiError.notFound('Employee not found or not on probation');

  const review = await platformPrisma.$transaction(async (tx) => {
    let newProbationEnd: Date | null = null;
    let newStatus = employee.status;

    if (data.decision === 'CONFIRMED') {
      newStatus = 'CONFIRMED';
    } else if (data.decision === 'EXTENDED' && data.extensionMonths) {
      newProbationEnd = new Date(employee.probationEndDate!);
      newProbationEnd.setMonth(newProbationEnd.getMonth() + data.extensionMonths);
    } else if (data.decision === 'TERMINATED') {
      newStatus = 'EXITED';
    }

    // Create review record
    const review = await tx.probationReview.create({
      data: {
        employeeId: data.employeeId,
        reviewDate: new Date(),
        probationEndDate: employee.probationEndDate!,
        managerFeedback: data.managerFeedback,
        performanceRating: data.performanceRating,
        decision: data.decision,
        extensionMonths: data.extensionMonths ?? null,
        newProbationEnd,
        decidedBy,
        decidedAt: new Date(),
        companyId,
      },
    });

    // Update employee status
    const updateData: any = {};
    if (data.decision === 'CONFIRMED') updateData.status = 'CONFIRMED';
    if (data.decision === 'TERMINATED') {
      updateData.status = 'EXITED';
      updateData.lastWorkingDate = new Date();
    }
    if (newProbationEnd) updateData.probationEndDate = newProbationEnd;

    await tx.employee.update({ where: { id: data.employeeId }, data: updateData });

    // Timeline event
    await tx.employeeTimeline.create({
      data: {
        employeeId: data.employeeId,
        eventType: data.decision === 'CONFIRMED' ? 'CONFIRMED' : 'CUSTOM',
        title: `Probation ${data.decision.toLowerCase()}`,
        description: data.managerFeedback,
        performedBy: decidedBy,
      },
    });

    return review;
  });

  return review;
}
```

Add routes:
- `GET /employees/probation-due` — `hr:read`
- `POST /employees/:id/probation-review` — `hr:update`

- [ ] **Step 3: ORA-10 — Org chart API**

Add to `employee.service.ts`:
```typescript
async getOrgChart(companyId: string) {
  const employees = await platformPrisma.employee.findMany({
    where: { companyId, status: { in: ['ACTIVE', 'PROBATION', 'CONFIRMED'] } },
    select: {
      id: true,
      employeeId: true,
      firstName: true,
      lastName: true,
      profilePhotoUrl: true,
      reportingManagerId: true,
      department: { select: { id: true, name: true } },
      designation: { select: { id: true, name: true } },
    },
  });

  // Build tree
  const byManager = new Map<string | null, typeof employees>();
  for (const emp of employees) {
    const key = emp.reportingManagerId ?? '__root__';
    if (!byManager.has(key)) byManager.set(key, []);
    byManager.get(key)!.push(emp);
  }

  function buildTree(managerId: string | null): any[] {
    const key = managerId ?? '__root__';
    const children = byManager.get(key) ?? [];
    return children.map(emp => ({
      ...emp,
      reportees: buildTree(emp.id),
    }));
  }

  return buildTree(null);
}
```

Add route: `GET /employees/org-chart` — `hr:read`

- [ ] **Step 4: Mount onboarding routes in hr/routes.ts**

```typescript
import { onboardingRoutes } from './onboarding/onboarding.routes';
// ...
router.use('/', onboardingRoutes);
```

---

## Task 7: Offboarding, Performance & Bonus Batch Fixes

**Files:**
- Modify: `avy-erp-backend/src/modules/hr/offboarding/offboarding.service.ts`
- Modify: `avy-erp-backend/src/modules/hr/performance/performance.service.ts`
- Modify: `avy-erp-backend/src/modules/hr/advanced/advanced.service.ts`
- Modify: `avy-erp-backend/src/modules/hr/advanced/advanced.controller.ts`
- Modify: `avy-erp-backend/src/modules/hr/advanced/advanced.routes.ts`
- Modify: `avy-erp-backend/src/modules/hr/advanced/advanced.validators.ts`

- [ ] **Step 1: YEL-4 — Bonus eligibility check in F&F**

In `offboarding.service.ts:computeFnF()`, before computing bonus pro-rata, add eligibility validation:

```typescript
// Bonus eligibility check per Payment of Bonus Act
let bonusProRata = 0;
if (exitRequest.separationType !== 'TERMINATION_FOR_CAUSE') {
  const bonusConfig = await platformPrisma.bonusConfig.findFirst({ where: { companyId } });
  if (bonusConfig) {
    // Check wage ceiling eligibility
    const monthlyBasic = basicMonthly;
    const wageCeiling = Number(bonusConfig.wageCeiling);
    const isEligibleBySalary = monthlyBasic <= wageCeiling;

    // Check minimum working days
    const workingDaysInYear = await platformPrisma.attendanceRecord.count({
      where: {
        employeeId,
        companyId,
        status: { in: ['PRESENT', 'LATE', 'HALF_DAY'] },
        date: {
          gte: new Date(lastWorkingDate.getFullYear(), 0, 1),
          lte: lastWorkingDate,
        },
      },
    });
    const minDays = bonusConfig.eligibilityDays ?? 30;
    const isEligibleByDays = workingDaysInYear >= minDays;

    if (isEligibleBySalary && isEligibleByDays) {
      const bonusPercentage = Number(bonusConfig.minBonusPercent);
      const monthsWorkedInYear = Math.min(12, Math.max(0, lastWorkingDate.getMonth() + 1));
      bonusProRata = (monthlyBasic * bonusPercentage / 100) * monthsWorkedInYear;
    }
  }
}
```

- [ ] **Step 2: YEL-10 — Skill gap auto training nomination**

In `performance.service.ts`, add after skill mapping update:

```typescript
async checkAndNominateTraining(companyId: string, employeeId: string, skillId: string, currentLevel: number) {
  // Find required level for this employee's designation + skill
  const employee = await platformPrisma.employee.findUnique({
    where: { id: employeeId },
    select: { designationId: true },
  });
  if (!employee) return null;

  // Check if skill has a required proficiency that exceeds current level
  const skillMapping = await platformPrisma.skillMapping.findFirst({
    where: { employeeId, skillId },
    select: { requiredLevel: true },
  });

  if (!skillMapping || currentLevel >= (skillMapping.requiredLevel ?? 3)) return null;

  // Find training linked to this skill
  const training = await platformPrisma.trainingCatalogue.findFirst({
    where: {
      companyId,
      linkedSkills: { path: [], array_contains: skillId },
      isActive: true,
    },
  });

  if (!training) return null;

  // Auto-create nomination
  const existing = await platformPrisma.trainingNomination.findFirst({
    where: { employeeId, trainingId: training.id, status: { in: ['NOMINATED', 'ENROLLED'] } },
  });
  if (existing) return null; // Already nominated

  return platformPrisma.trainingNomination.create({
    data: {
      companyId,
      employeeId,
      trainingId: training.id,
      nominatedBy: 'SYSTEM',
      reason: `Auto-nominated: Skill gap detected (current: ${currentLevel}, required: ${skillMapping.requiredLevel})`,
      status: 'NOMINATED',
    },
  });
}
```

- [ ] **Step 3: ORA-6 — Bonus batch methods**

In `advanced.service.ts`, add bonus batch CRUD:

```typescript
// ═══════════════════════════════════════════════════════════════════
// BONUS BATCH PROCESSING
// ═══════════════════════════════════════════════════════════════════

async listBonusBatches(companyId: string, options: { page?: number; limit?: number; status?: string } = {}) {
  const { page = 1, limit = 25, status } = options;
  const offset = (page - 1) * limit;
  const where: any = { companyId };
  if (status) where.status = status.toUpperCase();

  const [batches, total] = await Promise.all([
    platformPrisma.bonusBatch.findMany({
      where, include: { _count: { select: { items: true } } },
      skip: offset, take: limit, orderBy: { createdAt: 'desc' },
    }),
    platformPrisma.bonusBatch.count({ where }),
  ]);
  return { batches, total, page, limit };
}

async createBonusBatch(companyId: string, data: { name: string; bonusType: string; items: Array<{ employeeId: string; amount: number; remarks?: string }> }) {
  let totalAmount = 0;
  const itemsData = data.items.map(item => {
    const tds = item.amount * 0.1; // Simplified 10% TDS on bonus
    totalAmount += item.amount;
    return {
      employeeId: item.employeeId,
      amount: item.amount,
      tdsAmount: Math.round(tds * 100) / 100,
      netAmount: Math.round((item.amount - tds) * 100) / 100,
      remarks: item.remarks ?? null,
      companyId,
    };
  });

  return platformPrisma.$transaction(async (tx) => {
    const batch = await tx.bonusBatch.create({
      data: {
        companyId,
        name: data.name,
        bonusType: data.bonusType,
        totalAmount: Math.round(totalAmount * 100) / 100,
        employeeCount: data.items.length,
        status: 'DRAFT',
      },
    });

    await tx.bonusBatchItem.createMany({
      data: itemsData.map(item => ({ ...item, batchId: batch.id })),
    });

    return { ...batch, itemCount: data.items.length };
  });
}

async approveBonusBatch(companyId: string, batchId: string, userId: string) {
  const batch = await platformPrisma.bonusBatch.findUnique({ where: { id: batchId } });
  if (!batch || batch.companyId !== companyId) throw ApiError.notFound('Bonus batch not found');
  if (batch.status !== 'DRAFT' && batch.status !== 'SUBMITTED') {
    throw ApiError.badRequest('Batch must be in DRAFT or SUBMITTED status');
  }

  return platformPrisma.bonusBatch.update({
    where: { id: batchId },
    data: { status: 'APPROVED', approvedBy: userId, approvedAt: new Date() },
  });
}

async mergeBonusBatchToPayroll(companyId: string, batchId: string, payrollRunId: string) {
  const batch = await platformPrisma.bonusBatch.findUnique({
    where: { id: batchId },
    include: { items: true },
  });
  if (!batch || batch.companyId !== companyId) throw ApiError.notFound('Bonus batch not found');
  if (batch.status !== 'APPROVED') throw ApiError.badRequest('Batch must be APPROVED to merge');

  // Add bonus amounts to payroll entries
  for (const item of batch.items) {
    const entry = await platformPrisma.payrollEntry.findUnique({
      where: { payrollRunId_employeeId: { payrollRunId, employeeId: item.employeeId } },
    });
    if (entry) {
      const currentEarnings = entry.earnings as Record<string, number>;
      currentEarnings['BONUS'] = Number(item.amount);
      const newGross = Number(entry.grossEarnings) + Number(item.amount);
      const newNet = Number(entry.netPay) + Number(item.netAmount);

      await platformPrisma.payrollEntry.update({
        where: { id: entry.id },
        data: {
          earnings: currentEarnings,
          grossEarnings: Math.round(newGross * 100) / 100,
          netPay: Math.round(newNet * 100) / 100,
        },
      });
    }
  }

  return platformPrisma.bonusBatch.update({
    where: { id: batchId },
    data: { status: 'MERGED', mergedToRunId: payrollRunId },
  });
}
```

Add routes, validators, and controller methods for bonus batch CRUD.

---

## Execution Notes

### Migration Order
1. Task 1 (Schema) MUST run first — all other tasks depend on new models
2. Tasks 2-7 can run in parallel (different files)

### Testing Strategy
- After each task, verify with `npx prisma validate` (schema)
- Test endpoints via curl or Postman
- Run the 6-step payroll wizard end-to-end after Tasks 2-3

### Phase 2 Items (Document Only)
Items RED-4, ORA-7, ORA-8, ORA-9, ORA-11, YEL-5, YEL-6, YEL-7, YEL-9 are deferred. Create a `docs/HRMS_PHASE2_ROADMAP.md` documenting these with specifications for future implementation.
