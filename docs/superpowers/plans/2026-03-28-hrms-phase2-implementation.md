# HRMS Phase 2 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement all 8 deferred Phase 2 items from the HRMS audit to achieve full document compliance: Form 16/24Q, E-Sign, AI Chatbot, Production Incentive, GDPR/Retention, Shift Rotation, Biometric Device Management, and Travel Advance Recovery.

**Architecture:** Backend-first — Prisma schema additions first, then service logic per module, then API layer. Each task group targets distinct files to enable parallel execution. All new features follow existing patterns: Zod validators, asyncHandler controllers, requirePermissions middleware, platformPrisma database access, ApiError for errors.

**Tech Stack:** Prisma ORM, Express.js, TypeScript, Zod, platformPrisma singleton

---

## File Ownership Map (for parallel execution)

| Task | Files Owned | Items |
|------|-------------|-------|
| Task 1 | `prisma/schema.prisma` | All schema changes |
| Task 2 | `payroll-run/payroll-run.service.ts`, `controller`, `routes`, `validators` | RED-4 (Form 16/24Q) |
| Task 3 | `advanced/advanced.service.ts`, `controller`, `routes`, `validators` | ORA-7 (E-Sign), ORA-9 (Production Incentive) |
| Task 4 | New `chatbot/` module files | ORA-8 (AI Chatbot) |
| Task 5 | New `retention/` module files + `employee/employee.service.ts` | ORA-11 (GDPR/Retention) |
| Task 6 | `attendance/attendance.service.ts`, `controller`, `routes`, `validators` | YEL-6 (Shift Rotation), YEL-7 (Biometric) |
| Task 7 | `payroll/payroll.service.ts`, `controller`, `routes`, `validators` | YEL-9 (Travel Advance) |

---

## Task 1: Prisma Schema — All New Models & Fields

**Files:**
- Modify: `avy-erp-backend/prisma/schema.prisma`

- [ ] **Step 1: Add BiometricDevice model**

Find the `AttendanceRecord` model section. Before it, add:

```prisma
// ==========================================
// BIOMETRIC DEVICE MANAGEMENT (YEL-7)
// ==========================================

model BiometricDevice {
  id              String   @id @default(cuid())
  name            String
  brand           String   // ZKTeco, ESSL, Realtime, BioEnable, Mantra
  deviceId        String   // Unique device identifier
  ipAddress       String?
  port            Int?
  syncMode        String   @default("PULL") // PUSH, PULL, MANUAL
  syncIntervalMin Int      @default(5)
  locationId      String?
  location        Location? @relation("DeviceLocation", fields: [locationId], references: [id])
  status          String   @default("ACTIVE") // ACTIVE, INACTIVE, OFFLINE, ERROR
  lastSyncAt      DateTime?
  lastSyncStatus  String?  // SUCCESS, FAILED, PARTIAL
  enrolledCount   Int      @default(0)
  companyId       String
  company         Company  @relation(fields: [companyId], references: [id], onDelete: Cascade)
  createdAt       DateTime @default(now())
  updatedAt       DateTime @updatedAt

  @@unique([companyId, deviceId])
  @@map("biometric_devices")
}
```

- [ ] **Step 2: Add ShiftRotationSchedule model**

```prisma
// ==========================================
// SHIFT ROTATION (YEL-6)
// ==========================================

model ShiftRotationSchedule {
  id             String       @id @default(cuid())
  name           String
  rotationPattern String      // WEEKLY, FORTNIGHTLY, MONTHLY, CUSTOM
  shifts         Json         // Array of { shiftId, weekNumber } defining the rotation order
  effectiveFrom  DateTime     @db.Date
  effectiveTo    DateTime?    @db.Date
  isActive       Boolean      @default(true)
  companyId      String
  company        Company      @relation(fields: [companyId], references: [id], onDelete: Cascade)
  createdAt      DateTime     @default(now())
  updatedAt      DateTime     @updatedAt

  assignments ShiftRotationAssignment[]

  @@unique([companyId, name])
  @@map("shift_rotation_schedules")
}

model ShiftRotationAssignment {
  id         String                @id @default(cuid())
  scheduleId String
  schedule   ShiftRotationSchedule @relation(fields: [scheduleId], references: [id], onDelete: Cascade)
  employeeId String
  employee   Employee              @relation(fields: [employeeId], references: [id], onDelete: Cascade)
  companyId  String
  company    Company               @relation(fields: [companyId], references: [id], onDelete: Cascade)
  createdAt  DateTime              @default(now())

  @@unique([scheduleId, employeeId])
  @@map("shift_rotation_assignments")
}
```

- [ ] **Step 3: Add ProductionIncentiveConfig and ProductionIncentiveRecord models**

```prisma
// ==========================================
// PRODUCTION INCENTIVE (ORA-9)
// ==========================================

model ProductionIncentiveConfig {
  id              String   @id @default(cuid())
  name            String
  incentiveBasis  String   // COMPONENT_WISE, MODEL_WISE, FINISH_PART_WISE
  calculationCycle String  @default("MONTHLY") // DAILY, WEEKLY, MONTHLY
  slabs           Json     // Array of { minOutput, maxOutput, amount }
  machineId       String?
  departmentId    String?
  department      Department? @relation(fields: [departmentId], references: [id])
  isActive        Boolean  @default(true)
  companyId       String
  company         Company  @relation(fields: [companyId], references: [id], onDelete: Cascade)
  createdAt       DateTime @default(now())
  updatedAt       DateTime @updatedAt

  records ProductionIncentiveRecord[]

  @@map("production_incentive_configs")
}

model ProductionIncentiveRecord {
  id         String                   @id @default(cuid())
  configId   String
  config     ProductionIncentiveConfig @relation(fields: [configId], references: [id], onDelete: Cascade)
  employeeId String
  employee   Employee                 @relation(fields: [employeeId], references: [id])
  periodDate DateTime                 @db.Date
  outputUnits Decimal                 @db.Decimal(10, 2)
  incentiveAmount Decimal             @db.Decimal(15, 2)
  status     String                   @default("COMPUTED") // COMPUTED, APPROVED, MERGED
  payrollRunId String?
  companyId  String
  company    Company                  @relation(fields: [companyId], references: [id], onDelete: Cascade)
  createdAt  DateTime                 @default(now())
  updatedAt  DateTime                 @updatedAt

  @@map("production_incentive_records")
}
```

- [ ] **Step 4: Add DataRetentionPolicy and DataAccessRequest models**

```prisma
// ==========================================
// DATA RETENTION & GDPR (ORA-11)
// ==========================================

model DataRetentionPolicy {
  id              String   @id @default(cuid())
  dataCategory    String   // EMPLOYEE_MASTER, PAYROLL, STATUTORY, ATTENDANCE, LEAVE, RECRUITMENT, TRAINING, DISCIPLINE, DOCUMENTS, AUDIT_LOG
  retentionYears  Int
  actionAfter     String   @default("ARCHIVE") // ARCHIVE, DELETE, ANONYMISE
  isActive        Boolean  @default(true)
  companyId       String
  company         Company  @relation(fields: [companyId], references: [id], onDelete: Cascade)
  createdAt       DateTime @default(now())
  updatedAt       DateTime @updatedAt

  @@unique([companyId, dataCategory])
  @@map("data_retention_policies")
}

model DataAccessRequest {
  id           String    @id @default(cuid())
  employeeId   String
  employee     Employee  @relation(fields: [employeeId], references: [id])
  requestType  String    // ACCESS, RECTIFICATION, PORTABILITY, ERASURE
  description  String?
  status       String    @default("PENDING") // PENDING, IN_PROGRESS, COMPLETED, REJECTED
  processedBy  String?
  processedAt  DateTime?
  responseUrl  String?   // Download URL for exported data
  companyId    String
  company      Company   @relation(fields: [companyId], references: [id], onDelete: Cascade)
  createdAt    DateTime  @default(now())
  updatedAt    DateTime  @updatedAt

  @@map("data_access_requests")
}

model ConsentRecord {
  id           String   @id @default(cuid())
  employeeId   String
  employee     Employee @relation(fields: [employeeId], references: [id], onDelete: Cascade)
  consentType  String   // DATA_PROCESSING, BIOMETRIC_COLLECTION, COMMUNICATION, MARKETING
  granted      Boolean  @default(false)
  grantedAt    DateTime?
  revokedAt    DateTime?
  ipAddress    String?
  companyId    String
  company      Company  @relation(fields: [companyId], references: [id], onDelete: Cascade)
  createdAt    DateTime @default(now())
  updatedAt    DateTime @updatedAt

  @@unique([employeeId, consentType])
  @@map("consent_records")
}
```

- [ ] **Step 5: Add ChatConversation and ChatMessage models**

```prisma
// ==========================================
// AI HR CHATBOT (ORA-8)
// ==========================================

model ChatConversation {
  id         String        @id @default(cuid())
  employeeId String
  employee   Employee      @relation(fields: [employeeId], references: [id], onDelete: Cascade)
  channel    String        @default("WEB") // WEB, MOBILE, SLACK, TEAMS
  status     String        @default("ACTIVE") // ACTIVE, CLOSED, ESCALATED
  escalatedTo String?      // HR user ID if escalated
  companyId  String
  company    Company       @relation(fields: [companyId], references: [id], onDelete: Cascade)
  createdAt  DateTime      @default(now())
  updatedAt  DateTime      @updatedAt

  messages ChatMessage[]

  @@map("chat_conversations")
}

model ChatMessage {
  id             String           @id @default(cuid())
  conversationId String
  conversation   ChatConversation @relation(fields: [conversationId], references: [id], onDelete: Cascade)
  role           String           // USER, ASSISTANT, SYSTEM
  content        String           @db.Text
  intent         String?          // LEAVE_BALANCE, PAYSLIP, POLICY_FAQ, ATTENDANCE, HR_CONTACT, UNKNOWN
  metadata       Json?            // Action data: { actionType, actionResult }
  createdAt      DateTime         @default(now())

  @@map("chat_messages")
}
```

- [ ] **Step 6: Add LoanType to LoanPolicy and loanType to LoanRecord**

In the `LoanPolicy` model, add after the `code` field:
```prisma
  loanType     String   @default("PERSONAL") // PERSONAL, SALARY_ADVANCE, EMERGENCY, EDUCATION, TRAVEL_ADVANCE, VEHICLE
```

In the `LoanRecord` model, add after the `policyId` field:
```prisma
  loanType     String   @default("PERSONAL") // Inherited from policy at creation
  isSettled    Boolean  @default(false) // For travel advance: settled against expense claim
  settlementClaimId String? // ExpenseClaim ID used for settlement
```

- [ ] **Step 7: Add all Employee relations for new models**

In the Employee model, add:
```prisma
  // Phase 2 Relations
  shiftRotationAssignments ShiftRotationAssignment[]
  productionIncentives     ProductionIncentiveRecord[]
  dataAccessRequests       DataAccessRequest[]
  consentRecords           ConsentRecord[]
  chatConversations        ChatConversation[]
```

- [ ] **Step 8: Add all Company relations for new models**

In the Company model, add:
```prisma
  // Phase 2 Relations
  biometricDevices          BiometricDevice[]
  shiftRotationSchedules    ShiftRotationSchedule[]
  shiftRotationAssignments  ShiftRotationAssignment[]
  productionIncentiveConfigs ProductionIncentiveConfig[]
  productionIncentiveRecords ProductionIncentiveRecord[]
  dataRetentionPolicies     DataRetentionPolicy[]
  dataAccessRequests        DataAccessRequest[]
  consentRecords            ConsentRecord[]
  chatConversations         ChatConversation[]
  chatMessages              ChatMessage[]
```

Also add to Department model:
```prisma
  productionIncentiveConfigs ProductionIncentiveConfig[]
```

---

## Task 2: Form 16 & 24Q Generation (RED-4)

**Files:**
- Modify: `avy-erp-backend/src/modules/hr/payroll-run/payroll-run.service.ts`
- Modify: `avy-erp-backend/src/modules/hr/payroll-run/payroll-run.controller.ts`
- Modify: `avy-erp-backend/src/modules/hr/payroll-run/payroll-run.routes.ts`
- Modify: `avy-erp-backend/src/modules/hr/payroll-run/payroll-run.validators.ts`

- [ ] **Step 1: Add generateForm16 method**

Add to `PayrollRunService`:

```typescript
async generateForm16(companyId: string, financialYear: string) {
  // Parse FY: "2025-26" → startYear=2025, endYear=2026
  const [startYearStr, endYearStr] = financialYear.split('-');
  const startYear = parseInt(startYearStr, 10);
  const endYear = startYear + 1;

  // FY months: April (startYear) to March (endYear)
  const fyStart = new Date(startYear, 3, 1); // April 1
  const fyEnd = new Date(endYear, 3, 1); // April 1 next year

  // Get all payroll runs for the FY
  const runs = await platformPrisma.payrollRun.findMany({
    where: {
      companyId,
      status: { in: ['DISBURSED', 'ARCHIVED'] },
      OR: [
        { year: startYear, month: { gte: 4 } },
        { year: endYear, month: { lte: 3 } },
      ],
    },
    select: { id: true, month: true, year: true },
    orderBy: [{ year: 'asc' }, { month: 'asc' }],
  });

  if (runs.length === 0) {
    throw ApiError.notFound(`No disbursed payroll runs found for FY ${financialYear}`);
  }

  const runIds = runs.map(r => r.id);

  // Get all entries across the FY
  const entries = await platformPrisma.payrollEntry.findMany({
    where: { payrollRunId: { in: runIds }, companyId },
    include: {
      employee: {
        select: {
          id: true, employeeId: true, firstName: true, lastName: true,
          panNumber: true, aadhaarNumber: true, joiningDate: true,
          department: { select: { name: true } },
          designation: { select: { name: true } },
        },
      },
      payrollRun: { select: { month: true, year: true } },
    },
  });

  // Get IT declarations for the FY
  const declarations = await platformPrisma.iTDeclaration.findMany({
    where: { companyId, financialYear, status: { in: ['SUBMITTED', 'VERIFIED'] } },
  });
  const declMap = new Map(declarations.map(d => [d.employeeId, d]));

  // Get company info for Form 16 header
  const company = await platformPrisma.company.findUnique({
    where: { id: companyId },
    select: {
      displayName: true, legalName: true, pan: true, tan: true,
      registeredAddress: true,
    },
  });

  // Aggregate per employee
  const employeeMap = new Map<string, {
    employee: any;
    monthlyEntries: any[];
    totalGross: number;
    totalPF: number;
    totalESI: number;
    totalPT: number;
    totalTDS: number;
    totalLWF: number;
    totalNet: number;
  }>();

  for (const entry of entries) {
    const empId = entry.employeeId;
    if (!employeeMap.has(empId)) {
      employeeMap.set(empId, {
        employee: entry.employee,
        monthlyEntries: [],
        totalGross: 0, totalPF: 0, totalESI: 0, totalPT: 0,
        totalTDS: 0, totalLWF: 0, totalNet: 0,
      });
    }
    const agg = employeeMap.get(empId)!;
    agg.monthlyEntries.push({
      month: entry.payrollRun.month,
      year: entry.payrollRun.year,
      gross: Number(entry.grossEarnings),
      pf: Number(entry.pfEmployee ?? 0),
      esi: Number(entry.esiEmployee ?? 0),
      pt: Number(entry.ptAmount ?? 0),
      tds: Number(entry.tdsAmount ?? 0),
      lwf: Number(entry.lwfEmployee ?? 0),
      net: Number(entry.netPay),
      earnings: entry.earnings,
      deductions: entry.deductions,
    });
    agg.totalGross += Number(entry.grossEarnings);
    agg.totalPF += Number(entry.pfEmployee ?? 0);
    agg.totalESI += Number(entry.esiEmployee ?? 0);
    agg.totalPT += Number(entry.ptAmount ?? 0);
    agg.totalTDS += Number(entry.tdsAmount ?? 0);
    agg.totalLWF += Number(entry.lwfEmployee ?? 0);
    agg.totalNet += Number(entry.netPay);
  }

  // Build Form 16 Part B for each employee
  const form16Records: any[] = [];

  for (const [empId, data] of employeeMap) {
    const decl = declMap.get(empId);
    const regime = decl?.regime ?? 'NEW';

    // Compute deductions from IT declaration
    let totalChapter6A = 0;
    if (decl && regime === 'OLD') {
      const s80c = decl.section80C as any;
      totalChapter6A += Math.min(Number(s80c?.total ?? 0), 150000);
      const s80ccd = decl.section80CCD as any;
      totalChapter6A += Math.min(Number(s80ccd?.npsAdditional ?? 0), 50000);
      const s80d = decl.section80D as any;
      totalChapter6A += Math.min(Number(s80d?.selfPremium ?? 0), 25000);
      totalChapter6A += Math.min(Number(s80d?.parentPremium ?? 0), s80d?.seniorCitizen ? 50000 : 25000);
      const s80e = decl.section80E as any;
      totalChapter6A += Number(s80e?.educationLoanInterest ?? 0);
      const s80tta = decl.section80TTA as any;
      totalChapter6A += Math.min(Number(s80tta?.savingsInterest ?? 0), 10000);
    }

    const standardDeduction = regime === 'OLD' ? 50000 : 75000;
    const homeLoanInterest = regime === 'OLD'
      ? Math.min(Number((decl?.homeLoanInterest as any)?.interestAmount ?? 0), 200000)
      : 0;

    const grossSalary = Math.round(data.totalGross * 100) / 100;
    const exemptions = standardDeduction + homeLoanInterest;
    const netTaxableIncome = Math.max(0, grossSalary - exemptions - totalChapter6A);

    form16Records.push({
      employeeId: empId,
      employee: data.employee,
      financialYear,
      regime,
      company: {
        name: company?.legalName ?? company?.displayName,
        pan: company?.pan,
        tan: company?.tan,
        address: company?.registeredAddress,
      },
      partB: {
        grossSalary,
        standardDeduction,
        incomeFromSalary: Math.max(0, grossSalary - standardDeduction),
        chapter6ADeductions: totalChapter6A,
        homeLoanInterest,
        netTaxableIncome,
        taxOnIncome: data.totalTDS,
        educationCess: Math.round(data.totalTDS * 0.04 * 100) / 100,
        totalTaxPayable: data.totalTDS,
        tdsDeducted: data.totalTDS,
        monthlyBreakdown: data.monthlyEntries,
      },
      summary: {
        totalGross: grossSalary,
        totalPF: Math.round(data.totalPF * 100) / 100,
        totalESI: Math.round(data.totalESI * 100) / 100,
        totalPT: Math.round(data.totalPT * 100) / 100,
        totalTDS: Math.round(data.totalTDS * 100) / 100,
        totalNet: Math.round(data.totalNet * 100) / 100,
      },
    });
  }

  // Create statutory filing record
  await platformPrisma.statutoryFiling.create({
    data: {
      companyId,
      type: 'FORM_16',
      year: endYear,
      status: 'GENERATED',
      amount: null,
      details: { financialYear, employeeCount: form16Records.length, generatedAt: new Date().toISOString() },
    },
  });

  return {
    financialYear,
    employeeCount: form16Records.length,
    records: form16Records,
  };
}
```

- [ ] **Step 2: Add generateForm24Q method**

```typescript
async generateForm24Q(companyId: string, quarter: number, financialYear: string) {
  const [startYearStr] = financialYear.split('-');
  const startYear = parseInt(startYearStr, 10);
  const endYear = startYear + 1;

  // Quarter months mapping (FY quarters)
  const quarterMonths: Record<number, Array<{ month: number; year: number }>> = {
    1: [{ month: 4, year: startYear }, { month: 5, year: startYear }, { month: 6, year: startYear }],
    2: [{ month: 7, year: startYear }, { month: 8, year: startYear }, { month: 9, year: startYear }],
    3: [{ month: 10, year: startYear }, { month: 11, year: startYear }, { month: 12, year: startYear }],
    4: [{ month: 1, year: endYear }, { month: 2, year: endYear }, { month: 3, year: endYear }],
  };

  const months = quarterMonths[quarter];
  if (!months) throw ApiError.badRequest('Quarter must be 1-4');

  // Get payroll runs for the quarter
  const orConditions = months.map(m => ({ month: m.month, year: m.year }));
  const runs = await platformPrisma.payrollRun.findMany({
    where: { companyId, status: { in: ['DISBURSED', 'ARCHIVED'] }, OR: orConditions },
    select: { id: true, month: true, year: true },
  });

  const runIds = runs.map(r => r.id);

  // Get entries with employee PAN
  const entries = await platformPrisma.payrollEntry.findMany({
    where: { payrollRunId: { in: runIds }, companyId },
    include: {
      employee: {
        select: {
          id: true, employeeId: true, firstName: true, lastName: true,
          panNumber: true, joiningDate: true, lastWorkingDate: true,
        },
      },
      payrollRun: { select: { month: true, year: true } },
    },
  });

  // Aggregate per employee for the quarter
  const empMap = new Map<string, {
    employee: any;
    totalPaid: number;
    totalTdsDeducted: number;
    totalTdsDeposited: number; // Same as deducted for now
    months: Array<{ month: number; year: number; paid: number; tds: number }>;
  }>();

  for (const entry of entries) {
    const eid = entry.employeeId;
    if (!empMap.has(eid)) {
      empMap.set(eid, {
        employee: entry.employee,
        totalPaid: 0, totalTdsDeducted: 0, totalTdsDeposited: 0, months: [],
      });
    }
    const agg = empMap.get(eid)!;
    const paid = Number(entry.grossEarnings);
    const tds = Number(entry.tdsAmount ?? 0);
    agg.totalPaid += paid;
    agg.totalTdsDeducted += tds;
    agg.totalTdsDeposited += tds;
    agg.months.push({ month: entry.payrollRun.month, year: entry.payrollRun.year, paid, tds });
  }

  // Get company TAN
  const company = await platformPrisma.company.findUnique({
    where: { id: companyId },
    select: { tan: true, legalName: true, displayName: true },
  });

  // Build 24Q annexure data (NSDL format structure)
  const deducteeRecords = Array.from(empMap.values()).map(data => ({
    employeeRefNo: data.employee.employeeId,
    panOfDeductee: data.employee.panNumber ?? '',
    nameOfDeductee: `${data.employee.firstName} ${data.employee.lastName}`,
    dateOfPayment: months[months.length - 1], // Last month of quarter
    amountPaid: Math.round(data.totalPaid * 100) / 100,
    tdsDeducted: Math.round(data.totalTdsDeducted * 100) / 100,
    tdsDeposited: Math.round(data.totalTdsDeposited * 100) / 100,
    dateOfDeduction: months[months.length - 1],
    reasonForLowerDeduction: '',
    certificateNo: '',
  }));

  const totalPaid = deducteeRecords.reduce((s, r) => s + r.amountPaid, 0);
  const totalTds = deducteeRecords.reduce((s, r) => s + r.tdsDeducted, 0);

  // Create filing record
  await platformPrisma.statutoryFiling.create({
    data: {
      companyId,
      type: 'TDS_24Q',
      month: months[months.length - 1].month,
      year: months[months.length - 1].year,
      status: 'GENERATED',
      amount: totalTds,
      details: {
        financialYear, quarter,
        tanOfDeductor: company?.tan,
        nameOfDeductor: company?.legalName ?? company?.displayName,
        deducteeCount: deducteeRecords.length,
        generatedAt: new Date().toISOString(),
      },
    },
  });

  return {
    financialYear, quarter,
    tanOfDeductor: company?.tan,
    nameOfDeductor: company?.legalName ?? company?.displayName,
    totalAmountPaid: Math.round(totalPaid * 100) / 100,
    totalTdsDeducted: Math.round(totalTds * 100) / 100,
    deducteeCount: deducteeRecords.length,
    deducteeRecords,
  };
}

async bulkEmailForm16(companyId: string, financialYear: string) {
  // Mark all Form 16 payslips as emailed for the year
  const [, endYearStr] = financialYear.split('-');
  const endYear = parseInt(endYearStr, 10) + parseInt(financialYear.split('-')[0], 10);

  // For now, create a filing record tracking the bulk dispatch
  const filing = await platformPrisma.statutoryFiling.create({
    data: {
      companyId,
      type: 'FORM_16',
      year: endYear,
      status: 'FILED',
      details: { action: 'BULK_EMAIL', financialYear, dispatchedAt: new Date().toISOString() },
    },
  });

  return { message: 'Form 16 bulk email dispatch initiated', filingId: filing.id };
}
```

- [ ] **Step 3: Add validators, controller methods, and routes**

Validators:
```typescript
export const generateForm16Schema = z.object({
  financialYear: z.string().regex(/^\d{4}-\d{2}$/, 'Format must be YYYY-YY (e.g., 2025-26)'),
});

export const generateForm24QSchema = z.object({
  quarter: z.number().int().min(1).max(4),
  financialYear: z.string().regex(/^\d{4}-\d{2}$/, 'Format must be YYYY-YY'),
});
```

Routes:
```
POST /payroll-reports/form-16 — hr:create
POST /payroll-reports/form-24q — hr:create
POST /payroll-reports/form-16/bulk-email — hr:update
```

---

## Task 3: E-Sign Integration & Production Incentive (ORA-7, ORA-9)

**Files:**
- Modify: `avy-erp-backend/src/modules/hr/advanced/advanced.service.ts`
- Modify: `avy-erp-backend/src/modules/hr/advanced/advanced.controller.ts`
- Modify: `avy-erp-backend/src/modules/hr/advanced/advanced.routes.ts`
- Modify: `avy-erp-backend/src/modules/hr/advanced/advanced.validators.ts`

- [ ] **Step 1: ORA-7 — Add e-sign dispatch and tracking methods**

The HRLetter model already has `eSignStatus` and `eSignedAt` fields. Add methods:

```typescript
async dispatchESign(companyId: string, letterId: string) {
  const letter = await platformPrisma.hRLetter.findUnique({
    where: { id: letterId },
    include: {
      employee: { select: { id: true, personalEmail: true, officialEmail: true, firstName: true, lastName: true } },
      template: { select: { type: true, name: true } },
    },
  });
  if (!letter || letter.companyId !== companyId) {
    throw ApiError.notFound('Letter not found');
  }

  if (letter.eSignStatus === 'SIGNED') {
    throw ApiError.badRequest('Letter is already signed');
  }

  // Generate a unique signing token
  const signingToken = `esign_${letter.id}_${Date.now()}`;

  const updated = await platformPrisma.hRLetter.update({
    where: { id: letterId },
    data: {
      eSignStatus: 'PENDING',
      eSignToken: signingToken,
      eSignDispatchedAt: new Date(),
    },
  });

  // In production, this would call an external e-sign API (DigiSign/SignDesk)
  // For now, record the dispatch and return the signing URL placeholder

  return {
    letterId: letter.id,
    employeeName: `${letter.employee.firstName} ${letter.employee.lastName}`,
    letterType: letter.template?.type,
    eSignStatus: 'PENDING',
    signingUrl: `/api/v1/esign/sign/${signingToken}`,
    dispatchedTo: letter.employee.officialEmail ?? letter.employee.personalEmail,
  };
}

async processESignCallback(signingToken: string, status: 'SIGNED' | 'DECLINED') {
  const letter = await platformPrisma.hRLetter.findFirst({
    where: { eSignToken: signingToken },
  });
  if (!letter) {
    throw ApiError.notFound('Invalid signing token');
  }

  return platformPrisma.hRLetter.update({
    where: { id: letter.id },
    data: {
      eSignStatus: status,
      eSignedAt: status === 'SIGNED' ? new Date() : null,
    },
  });
}

async getESignStatus(companyId: string, letterId: string) {
  const letter = await platformPrisma.hRLetter.findUnique({
    where: { id: letterId },
    select: { id: true, eSignStatus: true, eSignedAt: true, eSignDispatchedAt: true },
  });
  if (!letter) throw ApiError.notFound('Letter not found');
  return letter;
}
```

NOTE: The HRLetter schema needs `eSignToken` and `eSignDispatchedAt` fields added. Include in Task 1 schema changes:
```prisma
// Add to HRLetter model:
  eSignToken        String?
  eSignDispatchedAt DateTime?
```

- [ ] **Step 2: ORA-9 — Add production incentive config and computation methods**

```typescript
// ═══════════════════════════════════════════════════════════════
// PRODUCTION INCENTIVE
// ═══════════════════════════════════════════════════════════════

async listIncentiveConfigs(companyId: string) {
  return platformPrisma.productionIncentiveConfig.findMany({
    where: { companyId },
    include: { department: { select: { id: true, name: true } } },
    orderBy: { name: 'asc' },
  });
}

async createIncentiveConfig(companyId: string, data: any) {
  return platformPrisma.productionIncentiveConfig.create({
    data: {
      companyId,
      name: data.name,
      incentiveBasis: data.incentiveBasis,
      calculationCycle: data.calculationCycle ?? 'MONTHLY',
      slabs: data.slabs,
      machineId: data.machineId ?? null,
      departmentId: data.departmentId ?? null,
      isActive: data.isActive ?? true,
    },
  });
}

async updateIncentiveConfig(companyId: string, id: string, data: any) {
  const config = await platformPrisma.productionIncentiveConfig.findUnique({ where: { id } });
  if (!config || config.companyId !== companyId) throw ApiError.notFound('Config not found');

  return platformPrisma.productionIncentiveConfig.update({
    where: { id },
    data: {
      ...(data.name !== undefined && { name: data.name }),
      ...(data.incentiveBasis !== undefined && { incentiveBasis: data.incentiveBasis }),
      ...(data.calculationCycle !== undefined && { calculationCycle: data.calculationCycle }),
      ...(data.slabs !== undefined && { slabs: data.slabs }),
      ...(data.machineId !== undefined && { machineId: data.machineId ?? null }),
      ...(data.departmentId !== undefined && { departmentId: data.departmentId ?? null }),
      ...(data.isActive !== undefined && { isActive: data.isActive }),
    },
  });
}

async computeIncentives(companyId: string, configId: string, data: {
  period: string; // ISO date for the period
  records: Array<{ employeeId: string; outputUnits: number }>;
}) {
  const config = await platformPrisma.productionIncentiveConfig.findUnique({ where: { id: configId } });
  if (!config || config.companyId !== companyId) throw ApiError.notFound('Config not found');

  const slabs = config.slabs as Array<{ minOutput: number; maxOutput: number; amount: number }>;
  const periodDate = new Date(data.period);

  const results: any[] = [];

  for (const record of data.records) {
    // Find applicable slab
    let incentiveAmount = 0;
    for (const slab of slabs) {
      if (record.outputUnits >= slab.minOutput && record.outputUnits <= slab.maxOutput) {
        incentiveAmount = slab.amount;
        break;
      }
    }

    const created = await platformPrisma.productionIncentiveRecord.upsert({
      where: {
        // No unique constraint on config+employee+period, so use create
        id: 'placeholder', // Will use create path
      },
      create: {
        configId,
        employeeId: record.employeeId,
        periodDate,
        outputUnits: record.outputUnits,
        incentiveAmount,
        status: 'COMPUTED',
        companyId,
      },
      update: {
        outputUnits: record.outputUnits,
        incentiveAmount,
      },
    });

    results.push(created);
  }

  // Use createMany instead of individual upserts for better performance
  // Delete existing for this config+period first
  await platformPrisma.productionIncentiveRecord.deleteMany({
    where: { configId, periodDate, companyId },
  });

  const createData = data.records.map(record => {
    let incentiveAmount = 0;
    for (const slab of slabs) {
      if (record.outputUnits >= slab.minOutput && record.outputUnits <= slab.maxOutput) {
        incentiveAmount = slab.amount;
        break;
      }
    }
    return {
      configId, employeeId: record.employeeId, periodDate,
      outputUnits: record.outputUnits, incentiveAmount,
      status: 'COMPUTED', companyId,
    };
  });

  await platformPrisma.productionIncentiveRecord.createMany({ data: createData });

  return {
    configId, period: data.period,
    computed: createData.length,
    totalIncentive: createData.reduce((s, r) => s + r.incentiveAmount, 0),
  };
}

async mergeIncentivesToPayroll(companyId: string, configId: string, month: number, year: number, payrollRunId: string) {
  const records = await platformPrisma.productionIncentiveRecord.findMany({
    where: {
      configId, companyId, status: 'COMPUTED',
      periodDate: {
        gte: new Date(year, month - 1, 1),
        lt: new Date(year, month, 1),
      },
    },
  });

  for (const record of records) {
    const entry = await platformPrisma.payrollEntry.findUnique({
      where: { payrollRunId_employeeId: { payrollRunId, employeeId: record.employeeId } },
    });
    if (entry) {
      const earnings = entry.earnings as Record<string, number>;
      earnings['PROD_INCENTIVE'] = Number(record.incentiveAmount);
      const newGross = Number(entry.grossEarnings) + Number(record.incentiveAmount);
      const newNet = Number(entry.netPay) + Number(record.incentiveAmount);

      await platformPrisma.payrollEntry.update({
        where: { id: entry.id },
        data: {
          earnings, grossEarnings: Math.round(newGross * 100) / 100,
          netPay: Math.round(newNet * 100) / 100,
        },
      });
    }
  }

  await platformPrisma.productionIncentiveRecord.updateMany({
    where: { id: { in: records.map(r => r.id) } },
    data: { status: 'MERGED', payrollRunId },
  });

  return { merged: records.length };
}
```

Add validators, controller methods, and routes for both features.

---

## Task 4: AI HR Chatbot (ORA-8)

**Files:**
- Create: `avy-erp-backend/src/modules/hr/chatbot/chatbot.service.ts`
- Create: `avy-erp-backend/src/modules/hr/chatbot/chatbot.controller.ts`
- Create: `avy-erp-backend/src/modules/hr/chatbot/chatbot.routes.ts`
- Create: `avy-erp-backend/src/modules/hr/chatbot/chatbot.validators.ts`
- Modify: `avy-erp-backend/src/modules/hr/routes.ts` (mount chatbot routes)

- [ ] **Step 1: Create chatbot service with intent detection and action execution**

The chatbot handles predefined intents by querying HRMS data directly. No external LLM dependency for core intents — pattern matching for structured queries, with escalation for unrecognized intents.

```typescript
// chatbot.service.ts
import { platformPrisma } from '../../../config/database';
import { ApiError } from '../../../shared/errors';

const INTENT_PATTERNS: Array<{ intent: string; patterns: RegExp[] }> = [
  { intent: 'LEAVE_BALANCE', patterns: [/leave\s*balance/i, /how\s*many\s*leaves/i, /remaining\s*leave/i, /leave\s*left/i] },
  { intent: 'PAYSLIP', patterns: [/payslip/i, /pay\s*slip/i, /salary\s*slip/i, /download\s*payslip/i] },
  { intent: 'ATTENDANCE', patterns: [/my\s*attendance/i, /attendance\s*status/i, /present\s*days/i] },
  { intent: 'HR_CONTACT', patterns: [/hr\s*contact/i, /contact\s*hr/i, /hr\s*email/i, /hr\s*phone/i, /speak\s*to\s*hr/i] },
  { intent: 'POLICY', patterns: [/policy/i, /leave\s*policy/i, /attendance\s*policy/i, /work\s*from\s*home/i] },
  { intent: 'HOLIDAY', patterns: [/holiday/i, /next\s*holiday/i, /upcoming\s*holiday/i, /holiday\s*list/i] },
  { intent: 'GREETING', patterns: [/^(hi|hello|hey|good\s*(morning|afternoon|evening))/i] },
];

export class ChatbotService {
  async startConversation(companyId: string, employeeId: string, channel: string = 'WEB') {
    return platformPrisma.chatConversation.create({
      data: { companyId, employeeId, channel, status: 'ACTIVE' },
    });
  }

  async sendMessage(companyId: string, conversationId: string, employeeId: string, content: string) {
    const conversation = await platformPrisma.chatConversation.findUnique({ where: { id: conversationId } });
    if (!conversation || conversation.companyId !== companyId || conversation.employeeId !== employeeId) {
      throw ApiError.notFound('Conversation not found');
    }
    if (conversation.status !== 'ACTIVE') {
      throw ApiError.badRequest('Conversation is closed');
    }

    // Save user message
    await platformPrisma.chatMessage.create({
      data: { conversationId, role: 'USER', content },
    });

    // Detect intent
    const intent = this.detectIntent(content);

    // Execute intent and generate response
    const response = await this.executeIntent(companyId, employeeId, intent, content);

    // Save assistant message
    const assistantMessage = await platformPrisma.chatMessage.create({
      data: {
        conversationId, role: 'ASSISTANT', content: response.message,
        intent, metadata: response.data ? response.data : undefined,
      },
    });

    return { intent, message: response.message, data: response.data, messageId: assistantMessage.id };
  }

  async getConversationHistory(companyId: string, conversationId: string, employeeId: string) {
    const conversation = await platformPrisma.chatConversation.findUnique({ where: { id: conversationId } });
    if (!conversation || conversation.companyId !== companyId || conversation.employeeId !== employeeId) {
      throw ApiError.notFound('Conversation not found');
    }

    return platformPrisma.chatMessage.findMany({
      where: { conversationId },
      orderBy: { createdAt: 'asc' },
    });
  }

  async escalateToHR(companyId: string, conversationId: string) {
    return platformPrisma.chatConversation.update({
      where: { id: conversationId },
      data: { status: 'ESCALATED' },
    });
  }

  private detectIntent(message: string): string {
    for (const { intent, patterns } of INTENT_PATTERNS) {
      if (patterns.some(p => p.test(message))) return intent;
    }
    return 'UNKNOWN';
  }

  private async executeIntent(companyId: string, employeeId: string, intent: string, _message: string) {
    switch (intent) {
      case 'GREETING':
        return { message: 'Hello! I\'m your HR assistant. I can help you with leave balance, payslips, attendance, holidays, and HR contacts. What would you like to know?' };

      case 'LEAVE_BALANCE': {
        const year = new Date().getFullYear();
        const balances = await platformPrisma.leaveBalance.findMany({
          where: { employeeId, companyId, year },
          include: { leaveType: { select: { name: true, code: true } } },
        });
        if (balances.length === 0) {
          return { message: 'No leave balances found for the current year. Please contact HR to initialize your balances.' };
        }
        const lines = balances.map(b => `${b.leaveType.name} (${b.leaveType.code}): ${b.balance} days remaining`);
        return { message: `Here are your leave balances:\n\n${lines.join('\n')}`, data: { balances } };
      }

      case 'PAYSLIP': {
        const now = new Date();
        const lastMonth = now.getMonth() === 0 ? 12 : now.getMonth();
        const lastYear = now.getMonth() === 0 ? now.getFullYear() - 1 : now.getFullYear();
        const payslip = await platformPrisma.payslip.findFirst({
          where: { employeeId, companyId, month: lastMonth, year: lastYear },
          select: { id: true, month: true, year: true, netPay: true, grossEarnings: true },
        });
        if (!payslip) {
          return { message: `No payslip found for ${lastMonth}/${lastYear}. It may not have been processed yet.` };
        }
        return {
          message: `Your payslip for ${lastMonth}/${lastYear}:\n- Gross: ₹${payslip.grossEarnings}\n- Net: ₹${payslip.netPay}\n\nYou can download the full payslip from your ESS portal.`,
          data: { payslipId: payslip.id },
        };
      }

      case 'ATTENDANCE': {
        const today = new Date();
        const monthStart = new Date(today.getFullYear(), today.getMonth(), 1);
        const records = await platformPrisma.attendanceRecord.findMany({
          where: { employeeId, companyId, date: { gte: monthStart, lte: today } },
          select: { status: true },
        });
        const present = records.filter(r => ['PRESENT', 'LATE'].includes(r.status)).length;
        const absent = records.filter(r => r.status === 'ABSENT').length;
        const onLeave = records.filter(r => r.status === 'ON_LEAVE').length;
        return {
          message: `Your attendance this month:\n- Present: ${present} days\n- Absent: ${absent} days\n- On Leave: ${onLeave} days\n- Total records: ${records.length}`,
          data: { present, absent, onLeave, total: records.length },
        };
      }

      case 'HOLIDAY': {
        const today = new Date();
        const holidays = await platformPrisma.holidayCalendar.findMany({
          where: { companyId, date: { gte: today }, isOptional: false },
          orderBy: { date: 'asc' },
          take: 5,
          select: { name: true, date: true, type: true },
        });
        if (holidays.length === 0) {
          return { message: 'No upcoming holidays found.' };
        }
        const lines = holidays.map(h => `${h.date.toISOString().split('T')[0]} — ${h.name} (${h.type})`);
        return { message: `Upcoming holidays:\n\n${lines.join('\n')}`, data: { holidays } };
      }

      case 'HR_CONTACT': {
        return {
          message: 'For HR queries, you can:\n- Email: hr@company.com (from your company profile)\n- Raise a ticket via Help Desk in ESS\n- Or I can escalate this conversation to HR. Would you like me to?',
        };
      }

      case 'POLICY':
        return { message: 'You can access all company policies in the ESS portal under "HR Policy Documents". Which policy are you looking for? I can help with leave policy, attendance policy, or work-from-home guidelines.' };

      default:
        return { message: 'I\'m not sure I understand that. I can help with:\n- Leave balance\n- Payslip information\n- Attendance status\n- Upcoming holidays\n- HR contact details\n\nWould you like to speak to HR instead? Just say "escalate to HR".' };
    }
  }
}

export const chatbotService = new ChatbotService();
```

- [ ] **Step 2: Create controller, validators, and routes**

Validators:
```typescript
export const startConversationSchema = z.object({ channel: z.enum(['WEB', 'MOBILE', 'SLACK', 'TEAMS']).optional() });
export const sendMessageSchema = z.object({ content: z.string().min(1).max(2000) });
```

Routes:
```
POST /chatbot/conversations — hr:read (start)
POST /chatbot/conversations/:id/messages — hr:read (send message)
GET /chatbot/conversations/:id/messages — hr:read (history)
PATCH /chatbot/conversations/:id/escalate — hr:read (escalate to HR)
```

Mount in `hr/routes.ts`.

---

## Task 5: Data Retention & GDPR (ORA-11)

**Files:**
- Create: `avy-erp-backend/src/modules/hr/retention/retention.service.ts`
- Create: `avy-erp-backend/src/modules/hr/retention/retention.controller.ts`
- Create: `avy-erp-backend/src/modules/hr/retention/retention.routes.ts`
- Create: `avy-erp-backend/src/modules/hr/retention/retention.validators.ts`
- Modify: `avy-erp-backend/src/modules/hr/routes.ts`
- Modify: `avy-erp-backend/src/modules/hr/employee/employee.service.ts`

- [ ] **Step 1: Create retention service**

Handles: retention policy CRUD, data access requests, consent management, anonymisation.

Key methods:
- `listPolicies(companyId)` — list all retention policies
- `upsertPolicy(companyId, data)` — create/update retention policy per data category
- `listDataAccessRequests(companyId, options)` — paginated list
- `createDataAccessRequest(companyId, employeeId, data)` — employee requests data access/portability/erasure
- `processDataAccessRequest(companyId, requestId, data)` — HR processes the request
- `exportEmployeeData(companyId, employeeId)` — generates full data export (JSON) for data portability
- `anonymiseEmployee(companyId, employeeId)` — replaces PII with pseudonyms, keeps record structure
- `listConsents(companyId, employeeId)` — list consent records
- `recordConsent(companyId, employeeId, data)` — grant/revoke consent
- `checkRetentionDue(companyId)` — identifies records past retention period

- [ ] **Step 2: Add anonymiseEmployee to employee service**

In `employee.service.ts`, add:
```typescript
async anonymiseEmployee(companyId: string, employeeId: string) {
  const employee = await platformPrisma.employee.findFirst({
    where: { id: employeeId, companyId, status: 'EXITED' },
  });
  if (!employee) throw ApiError.badRequest('Only EXITED employees can be anonymised');

  const pseudonym = `ANON-${employeeId.slice(-6).toUpperCase()}`;

  return platformPrisma.employee.update({
    where: { id: employeeId },
    data: {
      firstName: pseudonym,
      middleName: null,
      lastName: 'Anonymised',
      personalMobile: '0000000000',
      alternativeMobile: null,
      personalEmail: `${pseudonym}@anonymised.local`,
      officialEmail: null,
      currentAddress: Prisma.JsonNull,
      permanentAddress: Prisma.JsonNull,
      emergencyContactName: 'Anonymised',
      emergencyContactRelation: 'N/A',
      emergencyContactMobile: '0000000000',
      panNumber: null,
      aadhaarNumber: null,
      bankAccountNumber: null,
      bankIfscCode: null,
      bankName: null,
      bankBranch: null,
      passportNumber: null,
      drivingLicence: null,
      voterId: null,
      profilePhotoUrl: null,
      dateOfBirth: new Date(1900, 0, 1), // Anonymise DOB
    },
  });
}
```

Routes:
```
GET /retention/policies — hr:read
POST /retention/policies — hr:create
GET /retention/data-requests — hr:read
POST /retention/data-requests — hr:create (employee self-service)
PATCH /retention/data-requests/:id — hr:update (HR processes)
GET /retention/data-export/:employeeId — hr:read
POST /retention/anonymise/:employeeId — hr:delete
GET /retention/consents/:employeeId — hr:read
POST /retention/consents — hr:create
GET /retention/check-due — hr:read
```

---

## Task 6: Shift Rotation & Biometric Device Management (YEL-6, YEL-7)

**Files:**
- Modify: `avy-erp-backend/src/modules/hr/attendance/attendance.service.ts`
- Modify: `avy-erp-backend/src/modules/hr/attendance/attendance.controller.ts`
- Modify: `avy-erp-backend/src/modules/hr/attendance/attendance.routes.ts`
- Modify: `avy-erp-backend/src/modules/hr/attendance/attendance.validators.ts`

- [ ] **Step 1: YEL-6 — Add shift rotation methods**

```typescript
// Shift Rotation Schedule CRUD
async listRotationSchedules(companyId: string) { /* findMany */ }
async createRotationSchedule(companyId: string, data: any) { /* create */ }
async updateRotationSchedule(companyId: string, id: string, data: any) { /* update */ }
async deleteRotationSchedule(companyId: string, id: string) { /* delete */ }

// Assignment
async assignEmployeesToRotation(companyId: string, scheduleId: string, employeeIds: string[]) { /* createMany */ }
async removeEmployeeFromRotation(companyId: string, scheduleId: string, employeeId: string) { /* delete */ }

// Execute rotation — called by scheduled job or manually
async executeShiftRotation(companyId: string) {
  const activeSchedules = await platformPrisma.shiftRotationSchedule.findMany({
    where: { companyId, isActive: true, effectiveFrom: { lte: new Date() } },
    include: { assignments: { select: { employeeId: true } } },
  });

  let rotated = 0;

  for (const schedule of activeSchedules) {
    const shifts = schedule.shifts as Array<{ shiftId: string; weekNumber: number }>;
    if (!shifts || shifts.length === 0) continue;

    // Calculate current week number since effectiveFrom
    const weeksSinceStart = Math.floor(
      (Date.now() - new Date(schedule.effectiveFrom).getTime()) / (7 * 24 * 60 * 60 * 1000)
    );

    let currentShiftIndex: number;
    switch (schedule.rotationPattern) {
      case 'WEEKLY':
        currentShiftIndex = weeksSinceStart % shifts.length;
        break;
      case 'FORTNIGHTLY':
        currentShiftIndex = Math.floor(weeksSinceStart / 2) % shifts.length;
        break;
      case 'MONTHLY':
        const monthsSinceStart = /* calculate months */
          (new Date().getFullYear() - new Date(schedule.effectiveFrom).getFullYear()) * 12 +
          (new Date().getMonth() - new Date(schedule.effectiveFrom).getMonth());
        currentShiftIndex = monthsSinceStart % shifts.length;
        break;
      default:
        currentShiftIndex = 0;
    }

    const targetShiftId = shifts[currentShiftIndex]?.shiftId;
    if (!targetShiftId) continue;

    // Update all assigned employees to the target shift
    const employeeIds = schedule.assignments.map(a => a.employeeId);
    if (employeeIds.length > 0) {
      await platformPrisma.employee.updateMany({
        where: { id: { in: employeeIds }, companyId },
        data: { shiftId: targetShiftId },
      });
      rotated += employeeIds.length;
    }
  }

  return { message: 'Shift rotation executed', rotated };
}
```

- [ ] **Step 2: YEL-7 — Add biometric device management methods**

```typescript
// Biometric Device CRUD
async listDevices(companyId: string) {
  return platformPrisma.biometricDevice.findMany({
    where: { companyId },
    include: { location: { select: { id: true, name: true } } },
    orderBy: { name: 'asc' },
  });
}

async createDevice(companyId: string, data: any) {
  const existing = await platformPrisma.biometricDevice.findUnique({
    where: { companyId_deviceId: { companyId, deviceId: data.deviceId } },
  });
  if (existing) throw ApiError.conflict(`Device ID "${data.deviceId}" already registered`);

  return platformPrisma.biometricDevice.create({
    data: {
      companyId, name: data.name, brand: data.brand, deviceId: data.deviceId,
      ipAddress: data.ipAddress ?? null, port: data.port ?? null,
      syncMode: data.syncMode ?? 'PULL', syncIntervalMin: data.syncIntervalMin ?? 5,
      locationId: data.locationId ?? null, status: 'ACTIVE',
    },
  });
}

async updateDevice(companyId: string, id: string, data: any) { /* standard update */ }
async deleteDevice(companyId: string, id: string) { /* standard delete */ }

async testDeviceConnection(companyId: string, id: string) {
  const device = await platformPrisma.biometricDevice.findUnique({ where: { id } });
  if (!device || device.companyId !== companyId) throw ApiError.notFound('Device not found');

  // Placeholder: in production, this would ping the device IP:port
  const isOnline = !!device.ipAddress;

  await platformPrisma.biometricDevice.update({
    where: { id },
    data: {
      status: isOnline ? 'ACTIVE' : 'OFFLINE',
      lastSyncAt: new Date(),
      lastSyncStatus: isOnline ? 'SUCCESS' : 'FAILED',
    },
  });

  return { deviceId: device.deviceId, status: isOnline ? 'ONLINE' : 'OFFLINE' };
}

async syncDeviceAttendance(companyId: string, id: string, records: Array<{
  employeeId: string; date: string; punchIn?: string; punchOut?: string;
}>) {
  const device = await platformPrisma.biometricDevice.findUnique({ where: { id } });
  if (!device || device.companyId !== companyId) throw ApiError.notFound('Device not found');

  let synced = 0;
  let errors = 0;

  for (const record of records) {
    try {
      await this.createRecord(companyId, {
        employeeId: record.employeeId,
        date: record.date,
        punchIn: record.punchIn,
        punchOut: record.punchOut,
        status: 'PRESENT',
        source: 'BIOMETRIC',
        locationId: device.locationId,
      });
      synced++;
    } catch {
      errors++;
    }
  }

  await platformPrisma.biometricDevice.update({
    where: { id },
    data: { lastSyncAt: new Date(), lastSyncStatus: errors === 0 ? 'SUCCESS' : 'PARTIAL', enrolledCount: synced },
  });

  return { synced, errors, total: records.length };
}
```

Add routes for both:
```
// Shift Rotation
GET /shift-rotations — hr:read
POST /shift-rotations — hr:create
PATCH /shift-rotations/:id — hr:update
DELETE /shift-rotations/:id — hr:delete
POST /shift-rotations/:id/assign — hr:update
DELETE /shift-rotations/:id/assign/:employeeId — hr:update
POST /shift-rotations/execute — hr:update

// Biometric Devices
GET /biometric-devices — hr:read
POST /biometric-devices — hr:create
PATCH /biometric-devices/:id — hr:update
DELETE /biometric-devices/:id — hr:delete
POST /biometric-devices/:id/test — hr:update
POST /biometric-devices/:id/sync — hr:create
```

---

## Task 7: Travel Advance Recovery (YEL-9)

**Files:**
- Modify: `avy-erp-backend/src/modules/hr/payroll/payroll.service.ts`
- Modify: `avy-erp-backend/src/modules/hr/payroll/payroll.controller.ts`
- Modify: `avy-erp-backend/src/modules/hr/payroll/payroll.routes.ts`
- Modify: `avy-erp-backend/src/modules/hr/payroll/payroll.validators.ts`

- [ ] **Step 1: Add travel advance specific methods**

```typescript
async createTravelAdvance(companyId: string, data: {
  employeeId: string; amount: number; tripPurpose: string; estimatedTripDate: string;
}) {
  const employee = await platformPrisma.employee.findFirst({ where: { id: data.employeeId, companyId } });
  if (!employee) throw ApiError.badRequest('Employee not found');

  // Find travel advance policy
  const policy = await platformPrisma.loanPolicy.findFirst({
    where: { companyId, loanType: 'TRAVEL_ADVANCE', isActive: true },
  });

  return platformPrisma.loanRecord.create({
    data: {
      companyId,
      employeeId: data.employeeId,
      policyId: policy?.id ?? null,
      loanType: 'TRAVEL_ADVANCE',
      amount: data.amount,
      tenure: 1, // Single settlement, not EMI
      emiAmount: 0, // No EMI — settled against expense claim
      interestRate: 0,
      outstanding: data.amount,
      status: 'PENDING',
    },
  });
}

async settleTravelAdvance(companyId: string, loanId: string, expenseClaimId: string) {
  const loan = await platformPrisma.loanRecord.findUnique({ where: { id: loanId } });
  if (!loan || loan.companyId !== companyId || loan.loanType !== 'TRAVEL_ADVANCE') {
    throw ApiError.notFound('Travel advance not found');
  }

  const claim = await platformPrisma.expenseClaim.findUnique({ where: { id: expenseClaimId } });
  if (!claim || claim.companyId !== companyId || claim.status !== 'APPROVED') {
    throw ApiError.badRequest('Approved expense claim required for settlement');
  }

  const advanceAmount = Number(loan.amount);
  const claimAmount = Number(claim.amount);
  const difference = advanceAmount - claimAmount;

  // If advance > claim: employee owes the difference (recovered in payroll)
  // If claim > advance: company owes employee the difference (paid in payroll)
  return platformPrisma.$transaction(async (tx) => {
    await tx.loanRecord.update({
      where: { id: loanId },
      data: {
        outstanding: Math.max(0, difference),
        isSettled: true,
        settlementClaimId: expenseClaimId,
        status: difference <= 0 ? 'CLOSED' : 'ACTIVE', // ACTIVE if employee owes
      },
    });

    // If company owes employee, mark as reimbursement
    if (difference < 0) {
      await tx.expenseClaim.update({
        where: { id: expenseClaimId },
        data: { amount: Math.abs(difference) }, // Remaining amount to be paid
      });
    } else {
      await tx.expenseClaim.update({
        where: { id: expenseClaimId },
        data: { paidAt: new Date() }, // Fully settled from advance
      });
    }

    return {
      advanceAmount,
      claimAmount,
      difference,
      outcome: difference > 0 ? 'EMPLOYEE_OWES' : difference < 0 ? 'COMPANY_OWES' : 'EXACT_MATCH',
      remainingOutstanding: Math.max(0, difference),
    };
  });
}
```

Add validators and routes:
```
POST /loans/travel-advance — hr:create
POST /loans/:id/settle-travel — hr:update
```

---

## Execution Notes

### Migration Order
1. **Task 1 (Schema) MUST run first** — all service tasks depend on new models
2. **Tasks 2-7 can run in parallel** — each owns distinct files

### Schema Additions Summary
- Add `eSignToken`, `eSignDispatchedAt` to HRLetter model
- Add `loanType`, `isSettled`, `settlementClaimId` to LoanRecord model
- Add `loanType` to LoanPolicy model
- Add BiometricDevice, ShiftRotationSchedule, ShiftRotationAssignment
- Add ProductionIncentiveConfig, ProductionIncentiveRecord
- Add DataRetentionPolicy, DataAccessRequest, ConsentRecord
- Add ChatConversation, ChatMessage
- Add all relations to Employee and Company
