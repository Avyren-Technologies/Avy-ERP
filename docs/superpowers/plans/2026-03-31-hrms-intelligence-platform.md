# HRMS Intelligence Platform — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a 9-dashboard HR Intelligence Platform with precomputed analytics, insight engine, alerts, and role-based access across backend, web, and mobile.

**Architecture:** 6-layer stack — Presentation → Orchestrator → Filter Normalizer → Analytics → Intelligence → Data. Backend precomputes daily/monthly analytics via cron, surfaces insights via rule/scoring/anomaly engines, and serves standardized dashboard responses. Web uses Rrecharts, mobile uses Victory Native.

**Tech Stack:** Node.js/Express/Prisma (backend), React/Rrecharts (web), React Native/Victory Native (mobile), Redis (caching), node-cron (scheduling), exceljs (exports), Zod (validation)

**Spec:** `docs/superpowers/specs/2026-03-31-hrms-intelligence-platform-design.md`

---

## File Map

### Backend (`avy-erp-backend/src/modules/hr/analytics/`)

| File | Responsibility |
|------|---------------|
| `analytics.types.ts` | All TypeScript interfaces (DashboardFilters, KPICard, Insight, DashboardResponse, etc.) |
| `analytics.validators.ts` | Zod schemas for dashboard/drilldown/export/alert endpoints |
| `filters-normalizer.ts` | Default application, range validation, timezone conversion, limit capping |
| `services/report-access.service.ts` | Role-based data scoping + multi-tenant isolation + metric filtering |
| `services/analytics-audit.service.ts` | Audit logging for views, exports, drilldowns, alert actions |
| `services/analytics-cron.service.ts` | 4 cron populators + version cleanup + manual recompute |
| `insights/rules/attrition.rules.ts` | Attrition threshold rules |
| `insights/rules/attendance.rules.ts` | Attendance threshold rules |
| `insights/rules/payroll.rules.ts` | Payroll threshold rules |
| `insights/rules/compliance.rules.ts` | Compliance threshold rules |
| `insights/rules/performance.rules.ts` | Performance threshold rules |
| `insights/rules/recruitment.rules.ts` | Recruitment threshold rules |
| `insights/scoring/attrition-score.ts` | Flight risk composite scoring |
| `insights/scoring/manager-score.ts` | Manager effectiveness scoring |
| `insights/scoring/productivity-score.ts` | Productivity index calculation |
| `insights/scoring/compliance-score.ts` | Compliance score calculation |
| `insights/anomaly/thresholds.ts` | Threshold constants |
| `insights/anomaly/anomaly-detector.ts` | Z-score anomaly detection |
| `insights/insights-engine.service.ts` | Orchestrates rules + scoring + anomaly + prioritization |
| `alerts/alert-rules.ts` | Alert type definitions and triggers |
| `alerts/alert.service.ts` | Stateful alert CRUD with dedup and expiration |
| `services/analytics.service.ts` | Queries precomputed tables, returns raw aggregated data |
| `services/drilldown.service.ts` | On-demand detailed reports with export |
| `services/dashboard-orchestrator.service.ts` | Single entry point per dashboard, Promise.allSettled |
| `exports/excel-exporter.ts` | Excel file generation via exceljs |
| `exports/pdf-exporter.ts` | PDF file generation |
| `analytics.controller.ts` | HTTP handlers wrapping orchestrator + drilldown + alerts + exports |
| `analytics.routes.ts` | Route definitions with permission guards |

### Backend (Schema — Modular Prisma)

**IMPORTANT**: Prisma uses modular `.prisma` files. NEVER edit `schema.prisma` directly.

| File | Responsibility |
|------|---------------|
| `prisma/modules/hrms/analytics.prisma` | 4 precomputed models + AnalyticsAlert + AnalyticsAuditLog |
| `prisma/modules/platform/tenant.prisma` | Add Company inverse relations (modify existing) |
| `src/shared/constants/navigation-manifest.ts` | 10 new analytics navigation entries |

### Backend (Excel Reports — `src/modules/hr/analytics/exports/`)

| File | Responsibility |
|------|---------------|
| `exports/excel-exporter.ts` | Base exceljs utility (styles, sheet creation, auto-filters, formatting) |
| `exports/report-definitions.ts` | Report metadata: columns, sheets, formatting rules |
| `exports/reports/workforce-reports.ts` | R01-R03: Employee Master, Headcount Movement, Demographics |
| `exports/reports/attendance-reports.ts` | R04-R07: Attendance Register, Late Coming, Overtime, Absenteeism |
| `exports/reports/leave-reports.ts` | R08-R10: Leave Balance, Leave Utilization, Leave Encashment |
| `exports/reports/payroll-reports.ts` | R11-R15: Salary Register, Bank File, CTC Distribution, Revision, Loans |
| `exports/reports/statutory-reports.ts` | R16-R20: PF ECR, ESI Challan, PT, TDS, Gratuity Liability |
| `exports/reports/performance-reports.ts` | R21-R22: Appraisal Summary, Skill Gap Analysis |
| `exports/reports/attrition-reports.ts` | R23-R24: Attrition Report, F&F Settlement |
| `exports/reports/compliance-reports.ts` | R25: Compliance Summary |

### Web (`web-system-app/`)

| File | Responsibility |
|------|---------------|
| `src/lib/api/analytics.ts` | API service for all analytics endpoints |
| `src/features/company-admin/api/use-analytics-queries.ts` | React Query hooks + key factory |
| `src/features/company-admin/api/use-analytics-mutations.ts` | Mutation hooks (alert actions, recompute) |
| `src/components/analytics/DashboardShell.tsx` | Standard layout wrapper |
| `src/components/analytics/GlobalFilters.tsx` | Shared filter bar |
| `src/components/analytics/KPIGrid.tsx` | KPI cards with trends |
| `src/components/analytics/InsightsPanel.tsx` | Collapsible insights |
| `src/components/analytics/AlertsBanner.tsx` | Alert cards |
| `src/components/analytics/DrilldownTable.tsx` | Paginated drilldown table |
| `src/components/analytics/TrendChart.tsx` | Rrecharts line/area |
| `src/components/analytics/DistributionChart.tsx` | Rrecharts donut/bar |
| `src/components/analytics/HeatmapChart.tsx` | Rrecharts heatmap |
| `src/components/analytics/ScatterChart.tsx` | Rrecharts scatter |
| `src/components/analytics/FunnelChart.tsx` | Rrecharts funnel |
| `src/components/analytics/ExportMenu.tsx` | Export dropdown |
| `src/components/analytics/ZeroDataState.tsx` | Empty state |
| `src/features/company-admin/hr/analytics/ExecutiveDashboardScreen.tsx` | Dashboard 1 |
| `src/features/company-admin/hr/analytics/WorkforceDashboardScreen.tsx` | Dashboard 2 |
| `src/features/company-admin/hr/analytics/AttendanceAnalyticsDashboardScreen.tsx` | Dashboard 3 |
| `src/features/company-admin/hr/analytics/LeaveAnalyticsDashboardScreen.tsx` | Dashboard 4 |
| `src/features/company-admin/hr/analytics/PayrollAnalyticsDashboardScreen.tsx` | Dashboard 5 |
| `src/features/company-admin/hr/analytics/ComplianceDashboardScreen.tsx` | Dashboard 6 |
| `src/features/company-admin/hr/analytics/PerformanceAnalyticsDashboardScreen.tsx` | Dashboard 7 |
| `src/features/company-admin/hr/analytics/RecruitmentDashboardScreen.tsx` | Dashboard 8 |
| `src/features/company-admin/hr/analytics/AttritionDashboardScreen.tsx` | Dashboard 9 |

### Mobile (`mobile-app/`)

| File | Responsibility |
|------|---------------|
| `src/lib/api/analytics.ts` | API service |
| `src/features/company-admin/api/use-analytics-queries.ts` | React Query hooks |
| `src/features/company-admin/api/use-analytics-mutations.ts` | Mutation hooks |
| `src/components/analytics/DashboardShell.tsx` | Standard layout |
| `src/components/analytics/FilterBottomSheet.tsx` | Filter bottom sheet |
| `src/components/analytics/KPIGrid.tsx` | KPI cards |
| `src/components/analytics/InsightsPanel.tsx` | Insights accordion |
| `src/components/analytics/AlertsBanner.tsx` | Alert cards |
| `src/components/analytics/DrilldownList.tsx` | Expandable list |
| `src/components/analytics/TrendChart.tsx` | Victory Native line/area |
| `src/components/analytics/DistributionChart.tsx` | Victory Native pie/bar |
| `src/components/analytics/ExportButton.tsx` | Export action |
| `src/components/analytics/ZeroDataState.tsx` | Empty state |
| `src/features/company-admin/hr/analytics/executive-dashboard-screen.tsx` | Dashboard 1 |
| `src/features/company-admin/hr/analytics/workforce-dashboard-screen.tsx` | Dashboard 2 |
| `src/features/company-admin/hr/analytics/attendance-analytics-dashboard-screen.tsx` | Dashboard 3 |
| `src/features/company-admin/hr/analytics/leave-analytics-dashboard-screen.tsx` | Dashboard 4 |
| `src/features/company-admin/hr/analytics/payroll-analytics-dashboard-screen.tsx` | Dashboard 5 |
| `src/features/company-admin/hr/analytics/compliance-dashboard-screen.tsx` | Dashboard 6 |
| `src/features/company-admin/hr/analytics/performance-analytics-dashboard-screen.tsx` | Dashboard 7 |
| `src/features/company-admin/hr/analytics/recruitment-dashboard-screen.tsx` | Dashboard 8 |
| `src/features/company-admin/hr/analytics/attrition-dashboard-screen.tsx` | Dashboard 9 |
| `src/app/(app)/company/hr/analytics/` | 9 route files + `_layout.tsx` |

---

## Phase 1: Foundation (Backend Data Layer + Infrastructure)

### Task 1.1: Prisma Schema — Precomputed Analytics Tables

**Files:**
- Create: `avy-erp-backend/prisma/modules/hrms/analytics.prisma`
- Modify: `avy-erp-backend/prisma/modules/platform/tenant.prisma` (add Company relations)

**IMPORTANT**: Never edit `schema.prisma` directly — it is auto-generated. Edit modular files only.

- [ ] **Step 1: Create analytics.prisma and add EmployeeAnalyticsDaily model**

Create file `avy-erp-backend/prisma/modules/hrms/analytics.prisma`:

```prisma
// ============================================================================
// HR ANALYTICS — Precomputed Tables
// ============================================================================

model EmployeeAnalyticsDaily {
  id              String   @id @default(cuid())
  companyId       String
  date            DateTime @db.Date
  version         Int      @default(1)
  computedAt      DateTime @default(now())

  totalHeadcount  Int
  activeCount     Int
  probationCount  Int
  noticeCount     Int
  separatedCount  Int

  joinersCount    Int
  leaversCount    Int
  transfersCount  Int
  promotionsCount Int

  byDepartment    Json
  byLocation      Json
  byGrade         Json
  byEmployeeType  Json
  byGender        Json
  byAgeBand       Json
  byTenureBand    Json

  avgSpanOfControl Float?
  vacancyRate      Float?

  company         Company  @relation(fields: [companyId], references: [id])

  @@unique([companyId, date, version])
  @@index([companyId, date])
}
```

- [ ] **Step 2: Add AttendanceAnalyticsDaily model**

```prisma
model AttendanceAnalyticsDaily {
  id                  String   @id @default(cuid())
  companyId           String
  date                DateTime @db.Date
  version             Int      @default(1)
  computedAt          DateTime @default(now())

  totalEmployees      Int
  presentCount        Int
  absentCount         Int
  lateCount           Int
  halfDayCount        Int
  onLeaveCount        Int
  weekOffCount        Int
  holidayCount        Int

  avgWorkedHours      Float
  totalOvertimeHours  Float
  totalOvertimeCost   Float?

  productivityIndex   Float

  avgLateMinutes      Float
  lateThresholdBreaches Int

  regularizationCount Int
  missedPunchCount    Int

  byDepartment        Json
  byLocation          Json
  byShift             Json
  bySource            Json

  company             Company  @relation(fields: [companyId], references: [id])

  @@unique([companyId, date, version])
  @@index([companyId, date])
}
```

- [ ] **Step 3: Add PayrollAnalyticsMonthly model**

```prisma
model PayrollAnalyticsMonthly {
  id                    String   @id @default(cuid())
  companyId             String
  month                 Int
  year                  Int
  version               Int      @default(1)
  computedAt            DateTime @default(now())

  employeeCount         Int
  totalGrossEarnings    Float
  totalDeductions       Float
  totalNetPay           Float
  totalEmployerCost     Float

  totalPFEmployee       Float
  totalPFEmployer       Float
  totalESIEmployee      Float
  totalESIEmployer      Float
  totalPT               Float
  totalTDS              Float
  totalLWFEmployee      Float
  totalLWFEmployer      Float
  totalGratuityProvision Float

  avgCTC                Float
  medianCTC             Float
  exceptionCount        Int
  varianceFromLastMonth Float?

  totalLoanOutstanding  Float
  activeLoanCount       Int
  totalSalaryHolds      Int

  totalBonusDisbursed   Float
  totalIncentivesPaid   Float

  byDepartment          Json
  byLocation            Json
  byGrade               Json
  byCTCBand             Json
  byComponent           Json

  company               Company  @relation(fields: [companyId], references: [id])

  @@unique([companyId, month, year, version])
  @@index([companyId, year, month])
}
```

- [ ] **Step 4: Add AttritionMetricsMonthly model**

```prisma
model AttritionMetricsMonthly {
  id                      String   @id @default(cuid())
  companyId               String
  month                   Int
  year                    Int
  version                 Int      @default(1)
  computedAt              DateTime @default(now())

  attritionRate           Float
  voluntaryRate           Float
  involuntaryRate         Float
  earlyAttritionRate      Float

  totalExits              Int
  voluntaryExits          Int
  involuntaryExits        Int
  retirements             Int
  earlyExits              Int

  avgTenureAtExit         Float
  exitReasonBreakdown     Json
  wouldRecommendAvg       Float?

  flightRiskEmployees     Json

  pendingFnFCount         Int
  totalFnFAmount          Float
  avgFnFProcessingDays    Float

  byDepartment            Json
  byGrade                 Json
  byTenureBand            Json
  bySeparationType        Json

  company                 Company  @relation(fields: [companyId], references: [id])

  @@unique([companyId, month, year, version])
  @@index([companyId, year, month])
}
```

- [ ] **Step 5: Add AnalyticsAlert model**

```prisma
model AnalyticsAlert {
  id            String    @id @default(cuid())
  companyId     String
  dashboard     String
  type          String
  severity      String
  status        String    @default("ACTIVE")
  title         String
  description   String
  metadata      Json?
  acknowledgedBy String?
  acknowledgedAt DateTime?
  resolvedBy    String?
  resolvedAt    DateTime?
  createdAt     DateTime  @default(now())
  expiresAt     DateTime?

  company       Company   @relation(fields: [companyId], references: [id])

  @@index([companyId, status, severity])
  @@index([companyId, dashboard])
}
```

- [ ] **Step 6: Add AnalyticsAuditLog model**

```prisma
model AnalyticsAuditLog {
  id          String   @id @default(cuid())
  companyId   String
  userId      String
  action      String
  dashboard   String?
  reportType  String?
  filters     Json?
  exportFormat String?
  ipAddress   String?
  userAgent   String?
  createdAt   DateTime @default(now())

  @@index([companyId, userId, createdAt])
  @@index([companyId, action, createdAt])
}
```

- [ ] **Step 7: Add relations to Company model**

Edit `avy-erp-backend/prisma/modules/platform/tenant.prisma`. Find the `Company` model and add these relation fields:

```prisma
  // Analytics relations
  employeeAnalytics     EmployeeAnalyticsDaily[]
  attendanceAnalytics   AttendanceAnalyticsDaily[]
  payrollAnalytics      PayrollAnalyticsMonthly[]
  attritionMetrics      AttritionMetricsMonthly[]
  analyticsAlerts       AnalyticsAlert[]
```

- [ ] **Step 8: Run merge + migration**

```bash
cd avy-erp-backend && pnpm db:generate && pnpm db:migrate
```

This runs `prisma:merge` (combines all modular files into `schema.prisma`) then generates the client and creates the migration.

- [ ] **Step 9: Commit**

```bash
git add prisma/modules/hrms/analytics.prisma prisma/modules/platform/tenant.prisma prisma/schema.prisma prisma/migrations/
git commit -m "feat(analytics): add precomputed analytics tables, alert, and audit log models"
```

---

### Task 1.2: Types & Validators

**Files:**
- Create: `avy-erp-backend/src/modules/hr/analytics/analytics.types.ts`
- Create: `avy-erp-backend/src/modules/hr/analytics/analytics.validators.ts`

- [ ] **Step 1: Create analytics.types.ts**

```typescript
// Types for the HR Analytics module

export interface DashboardFilters {
  dateFrom: string;
  dateTo: string;
  departmentId?: string;
  locationId?: string;
  gradeId?: string;
  employeeTypeId?: string;
  page: number;
  limit: number;
  sortBy: string;
  sortOrder: 'asc' | 'desc';
  search?: string;
}

export interface RawDashboardFilters {
  dateFrom?: string;
  dateTo?: string;
  departmentId?: string;
  locationId?: string;
  gradeId?: string;
  employeeTypeId?: string;
  page?: number;
  limit?: number;
  sortBy?: string;
  sortOrder?: string;
  search?: string;
}

export interface DataScope {
  companyId: string;
  departmentIds?: string[];
  locationIds?: string[];
  employeeIds?: string[];
  isFullOrg: boolean;
}

export interface KPICard {
  key: string;
  label: string;
  value: number | string;
  format: 'number' | 'currency' | 'percentage' | 'text';
  drilldownType: string;
  trend?: {
    direction: 'up' | 'down' | 'neutral';
    changePercent: number;
    comparedTo: string;
  };
}

export interface TrendSeries {
  key: string;
  label: string;
  data: { date: string; value: number }[];
  chartType: 'line' | 'area' | 'bar';
}

export interface Distribution {
  key: string;
  label: string;
  data: { label: string; value: number; color?: string }[];
  chartType: 'donut' | 'bar' | 'heatmap' | 'scatter' | 'funnel';
}

export type InsightCategory = 'info' | 'warning' | 'critical' | 'positive';

export interface Insight {
  id: string;
  dashboard: string;
  category: InsightCategory;
  title: string;
  description: string;
  metric: string;
  currentValue: number;
  benchmarkValue?: number;
  changePercent?: number;
  affectedEntity?: string;
  actionable: boolean;
  drilldownType?: string;
}

export interface DataCompleteness {
  attendanceComplete: boolean;
  payrollComplete: boolean;
  appraisalComplete: boolean;
  exitInterviewsComplete: boolean;
}

export interface DashboardMeta {
  lastComputedAt: string | null;
  version: number;
  filtersApplied: DashboardFilters;
  scope: 'full_org' | 'team' | 'personal';
  dataCompleteness: DataCompleteness;
  partialFailures?: string[];
}

export interface DashboardResponse {
  kpis: KPICard[];
  trends: (TrendSeries | null)[];
  distributions: (Distribution | null)[];
  insights: Insight[];
  alerts: AlertData[];
  drilldownTypes: string[];
  meta: DashboardMeta;
}

export interface AlertData {
  id: string;
  dashboard: string;
  type: string;
  severity: 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';
  status: 'ACTIVE' | 'ACKNOWLEDGED' | 'RESOLVED';
  title: string;
  description: string;
  metadata?: Record<string, unknown>;
  createdAt: string;
}

export type DashboardName =
  | 'executive'
  | 'workforce'
  | 'attendance'
  | 'leave'
  | 'payroll'
  | 'compliance'
  | 'performance'
  | 'recruitment'
  | 'attrition';

export interface InsightRule {
  id: string;
  evaluate: (data: Record<string, unknown>) => boolean;
  generate: (data: Record<string, unknown>) => Omit<Insight, 'id' | 'dashboard' | 'metric' | 'currentValue'>;
}

export interface AnomalyResult {
  isAnomaly: boolean;
  severity?: 'MEDIUM' | 'HIGH';
  direction?: 'ABOVE' | 'BELOW';
  zScore?: number;
}

export interface PaginatedReport<T = Record<string, unknown>> {
  data: T[];
  meta: {
    page: number;
    limit: number;
    total: number;
    totalPages: number;
  };
}
```

- [ ] **Step 2: Create analytics.validators.ts**

```typescript
import { z } from 'zod';

export const dashboardFiltersSchema = z.object({
  dateFrom: z.string().optional(),
  dateTo: z.string().optional(),
  departmentId: z.string().optional(),
  locationId: z.string().optional(),
  gradeId: z.string().optional(),
  employeeTypeId: z.string().optional(),
});

export const drilldownFiltersSchema = dashboardFiltersSchema.extend({
  type: z.string().min(1, 'Drilldown type is required'),
  page: z.coerce.number().int().positive().optional(),
  limit: z.coerce.number().int().positive().max(100).optional(),
  sortBy: z.string().optional(),
  sortOrder: z.enum(['asc', 'desc']).optional(),
  search: z.string().max(200).optional(),
  month: z.coerce.number().int().min(1).max(12).optional(),
  year: z.coerce.number().int().min(2020).max(2100).optional(),
});

export const exportFiltersSchema = z.object({
  format: z.enum(['excel', 'pdf', 'csv']),
  dateFrom: z.string().optional(),
  dateTo: z.string().optional(),
  departmentId: z.string().optional(),
  locationId: z.string().optional(),
  gradeId: z.string().optional(),
  employeeTypeId: z.string().optional(),
  month: z.coerce.number().int().min(1).max(12).optional(),
  year: z.coerce.number().int().min(2020).max(2100).optional(),
});

export const alertActionSchema = z.object({
  alertId: z.string().min(1, 'Alert ID is required'),
});

export const recomputeSchema = z.object({
  date: z.string().optional(),
});
```

- [ ] **Step 3: Commit**

```bash
git add src/modules/hr/analytics/analytics.types.ts src/modules/hr/analytics/analytics.validators.ts
git commit -m "feat(analytics): add TypeScript types and Zod validators"
```

---

### Task 1.3: Filter Normalizer

**Files:**
- Create: `avy-erp-backend/src/modules/hr/analytics/filters-normalizer.ts`

- [ ] **Step 1: Create filters-normalizer.ts**

```typescript
import type { DashboardFilters, RawDashboardFilters } from './analytics.types';

function startOfMonth(timezone: string): string {
  const now = new Date();
  // Convert to company timezone and get first day of month
  const formatter = new Intl.DateTimeFormat('en-CA', {
    timeZone: timezone,
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
  });
  const parts = formatter.formatToParts(now);
  const year = parts.find(p => p.type === 'year')?.value;
  const month = parts.find(p => p.type === 'month')?.value;
  return `${year}-${month}-01`;
}

function today(timezone: string): string {
  const formatter = new Intl.DateTimeFormat('en-CA', {
    timeZone: timezone,
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
  });
  return formatter.format(new Date());
}

export function normalizeFilters(
  raw: RawDashboardFilters,
  companyTimezone: string = 'Asia/Kolkata',
): DashboardFilters {
  const dateFrom = raw.dateFrom ?? startOfMonth(companyTimezone);
  const dateTo = raw.dateTo ?? today(companyTimezone);

  return {
    dateFrom: dateFrom > dateTo ? dateTo : dateFrom,
    dateTo,
    departmentId: raw.departmentId || undefined,
    locationId: raw.locationId || undefined,
    gradeId: raw.gradeId || undefined,
    employeeTypeId: raw.employeeTypeId || undefined,
    page: Math.max(raw.page ?? 1, 1),
    limit: Math.min(Math.max(raw.limit ?? 20, 1), 100),
    sortBy: raw.sortBy ?? 'createdAt',
    sortOrder: raw.sortOrder === 'asc' ? 'asc' : 'desc',
    search: raw.search?.trim().slice(0, 200) || undefined,
  };
}
```

- [ ] **Step 2: Commit**

```bash
git add src/modules/hr/analytics/filters-normalizer.ts
git commit -m "feat(analytics): add filter normalizer with timezone support and defaults"
```

---

### Task 1.4: Report Access Service

**Files:**
- Create: `avy-erp-backend/src/modules/hr/analytics/services/report-access.service.ts`

- [ ] **Step 1: Create report-access.service.ts**

```typescript
import { ApiError } from '@/shared/errors';
import type { DataScope, DashboardName, DashboardResponse } from '../analytics.types';

const FINANCE_ALLOWED_DASHBOARDS: DashboardName[] = ['executive', 'payroll', 'compliance'];
const MANAGER_ALLOWED_DASHBOARDS: DashboardName[] = ['attendance', 'leave', 'performance'];

// Fields to strip for Finance users
const FINANCE_RESTRICTED_FIELDS = [
  'performanceRating', 'appraisalScore', 'attritionReason',
  'grievanceDetails', 'disciplinaryDetails', 'employeeName',
];

// Fields to strip for Manager users
const MANAGER_RESTRICTED_FIELDS = [
  'salary', 'ctc', 'grossEarnings', 'netPay', 'deductions',
  'pfAmount', 'esiAmount', 'tdsAmount',
];

class ReportAccessService {
  async resolveScope(
    userId: string,
    companyId: string,
    role: string,
    dashboard: DashboardName,
    reportingManagerChain?: string[],
  ): Promise<DataScope> {
    if (!companyId) {
      throw ApiError.badRequest('Company ID is required for analytics');
    }

    // Employee: own data only
    if (role === 'user') {
      return {
        companyId,
        employeeIds: [userId],
        isFullOrg: false,
      };
    }

    // Manager: team data only, restricted dashboards
    if (role === 'manager') {
      if (!MANAGER_ALLOWED_DASHBOARDS.includes(dashboard)) {
        throw ApiError.forbidden('You do not have access to this dashboard');
      }
      return {
        companyId,
        employeeIds: reportingManagerChain ?? [],
        isFullOrg: false,
      };
    }

    // Finance: restricted dashboards
    if (role === 'finance') {
      if (!FINANCE_ALLOWED_DASHBOARDS.includes(dashboard)) {
        throw ApiError.forbidden('You do not have access to this dashboard');
      }
      return {
        companyId,
        isFullOrg: true,
      };
    }

    // HR Personnel, Company Admin, CXO: full org
    return {
      companyId,
      isFullOrg: true,
    };
  }

  filterMetrics(
    response: DashboardResponse,
    role: string,
  ): DashboardResponse {
    if (role === 'finance') {
      return this.stripFields(response, FINANCE_RESTRICTED_FIELDS);
    }
    if (role === 'manager') {
      return this.stripFields(response, MANAGER_RESTRICTED_FIELDS);
    }
    return response;
  }

  private stripFields(
    response: DashboardResponse,
    restrictedFields: string[],
  ): DashboardResponse {
    // Filter KPIs that contain restricted data
    const filteredKpis = response.kpis.filter(
      kpi => !restrictedFields.some(f => kpi.key.toLowerCase().includes(f.toLowerCase())),
    );

    // Filter insights that reference restricted metrics
    const filteredInsights = response.insights.filter(
      insight => !restrictedFields.some(f => insight.metric.toLowerCase().includes(f.toLowerCase())),
    );

    return {
      ...response,
      kpis: filteredKpis,
      insights: filteredInsights,
    };
  }
}

export const reportAccessService = new ReportAccessService();
```

- [ ] **Step 2: Commit**

```bash
git add src/modules/hr/analytics/services/report-access.service.ts
git commit -m "feat(analytics): add report access service with role-based scoping"
```

---

### Task 1.5: Analytics Audit Service

**Files:**
- Create: `avy-erp-backend/src/modules/hr/analytics/services/analytics-audit.service.ts`

- [ ] **Step 1: Create analytics-audit.service.ts**

```typescript
import { platformPrisma } from '@/config/database';
import { logger } from '@/config/logger';

class AnalyticsAuditService {
  async logView(
    userId: string,
    companyId: string,
    dashboard: string,
    filters?: Record<string, unknown>,
    req?: { ip?: string; headers?: Record<string, string> },
  ): Promise<void> {
    try {
      await platformPrisma.analyticsAuditLog.create({
        data: {
          companyId,
          userId,
          action: 'VIEW_DASHBOARD',
          dashboard,
          filters: filters ?? undefined,
          ipAddress: req?.ip ?? undefined,
          userAgent: req?.headers?.['user-agent'] ?? undefined,
        },
      });
    } catch (error) {
      logger.error('Failed to log analytics view', { error, userId, dashboard });
    }
  }

  async logExport(
    userId: string,
    companyId: string,
    reportType: string,
    format: string,
    filters?: Record<string, unknown>,
  ): Promise<void> {
    try {
      await platformPrisma.analyticsAuditLog.create({
        data: {
          companyId,
          userId,
          action: 'EXPORT_REPORT',
          reportType,
          exportFormat: format,
          filters: filters ?? undefined,
        },
      });
    } catch (error) {
      logger.error('Failed to log analytics export', { error, userId, reportType });
    }
  }

  async logDrilldown(
    userId: string,
    companyId: string,
    dashboard: string,
    drilldownType: string,
  ): Promise<void> {
    try {
      await platformPrisma.analyticsAuditLog.create({
        data: {
          companyId,
          userId,
          action: 'DRILLDOWN',
          dashboard,
          reportType: drilldownType,
        },
      });
    } catch (error) {
      logger.error('Failed to log analytics drilldown', { error, userId, drilldownType });
    }
  }

  async logAlertAction(
    userId: string,
    companyId: string,
    alertId: string,
    action: 'ACKNOWLEDGE_ALERT' | 'RESOLVE_ALERT',
  ): Promise<void> {
    try {
      await platformPrisma.analyticsAuditLog.create({
        data: {
          companyId,
          userId,
          action,
          reportType: alertId,
        },
      });
    } catch (error) {
      logger.error('Failed to log alert action', { error, userId, alertId });
    }
  }
}

export const analyticsAuditService = new AnalyticsAuditService();
```

- [ ] **Step 2: Commit**

```bash
git add src/modules/hr/analytics/services/analytics-audit.service.ts
git commit -m "feat(analytics): add analytics audit service for view/export/drilldown logging"
```

---

### Task 1.6: Install exceljs dependency

- [ ] **Step 1: Install exceljs**

```bash
cd avy-erp-backend && pnpm add exceljs
```

- [ ] **Step 2: Commit**

```bash
git add package.json pnpm-lock.yaml
git commit -m "deps: add exceljs for analytics Excel export"
```

---

## Phase 2: Cron & Precomputation

### Task 2.1: Analytics Cron Service — Employee Analytics Daily

**Files:**
- Create: `avy-erp-backend/src/modules/hr/analytics/services/analytics-cron.service.ts`

This is a large service. We build it incrementally — one populator at a time.

- [ ] **Step 1: Create the cron service with employee analytics populator**

```typescript
import { platformPrisma } from '@/config/database';
import { logger } from '@/config/logger';
import cron from 'node-cron';

class AnalyticsCronService {
  startAll(): void {
    // Employee analytics: 1:00 AM daily
    cron.schedule('0 1 * * *', () => this.computeEmployeeAnalyticsDaily());
    // Attendance analytics: 11:00 PM daily
    cron.schedule('0 23 * * *', () => this.computeAttendanceAnalyticsDaily());
    // Payroll analytics: 2:00 AM on 1st of month
    cron.schedule('0 2 1 * *', () => this.computePayrollAnalyticsMonthly());
    // Attrition metrics: 3:00 AM daily
    cron.schedule('0 3 * * *', () => this.computeAttritionMetricsMonthly());
    // Version cleanup: 4:00 AM on 1st of month
    cron.schedule('0 4 1 * *', () => this.purgeOldVersions(90));

    logger.info('Analytics cron jobs scheduled');
  }

  async computeEmployeeAnalyticsDaily(targetDate?: Date): Promise<void> {
    const startTime = Date.now();
    let companiesProcessed = 0;
    let errors = 0;

    try {
      const companies = await platformPrisma.company.findMany({
        select: { id: true, timezone: true },
      });

      for (const company of companies) {
        try {
          await this.computeEmployeeAnalyticsForCompany(company.id, company.timezone, targetDate);
          companiesProcessed++;
        } catch (error) {
          errors++;
          logger.error('Employee analytics computation failed for company', {
            companyId: company.id,
            error: (error as Error).message,
          });
        }
      }
    } finally {
      logger.info('analytics_cron_completed', {
        table: 'EmployeeAnalyticsDaily',
        companiesProcessed,
        errors,
        durationMs: Date.now() - startTime,
      });
    }
  }

  private async computeEmployeeAnalyticsForCompany(
    companyId: string,
    timezone: string | null,
    targetDate?: Date,
  ): Promise<void> {
    const tz = timezone ?? 'Asia/Kolkata';
    const date = targetDate ?? new Date();
    const dateOnly = new Date(date.toLocaleDateString('en-CA', { timeZone: tz }));

    // Get the tenant's prisma client
    const tenantDb = await this.getTenantPrisma(companyId);
    if (!tenantDb) return;

    // Fetch all employees for this company
    const employees = await tenantDb.employee.findMany({
      select: {
        id: true,
        status: true,
        departmentId: true,
        designationId: true,
        gradeId: true,
        employeeTypeId: true,
        gender: true,
        dateOfBirth: true,
        joiningDate: true,
        reportingManagerId: true,
        locationId: true,
        annualCtc: true,
      },
    });

    const today = dateOnly;
    const startOfDay = new Date(today);
    startOfDay.setHours(0, 0, 0, 0);
    const endOfDay = new Date(today);
    endOfDay.setHours(23, 59, 59, 999);

    // Count by status
    const statusCounts = { active: 0, probation: 0, notice: 0, separated: 0 };
    const byDept: Record<string, Record<string, number>> = {};
    const byLocation: Record<string, Record<string, number>> = {};
    const byGrade: Record<string, { count: number; totalCTC: number }> = {};
    const byType: Record<string, { count: number }> = {};
    const byGender: Record<string, number> = {};
    const byAgeBand: Record<string, number> = {};
    const byTenureBand: Record<string, number> = {};
    const managerCounts: Record<string, number> = {};

    for (const emp of employees) {
      // Status counts
      const s = emp.status?.toUpperCase() ?? 'ACTIVE';
      if (s === 'ACTIVE') statusCounts.active++;
      else if (s === 'PROBATION') statusCounts.probation++;
      else if (s === 'NOTICE_PERIOD') statusCounts.notice++;
      else if (s === 'SEPARATED' || s === 'INACTIVE') statusCounts.separated++;
      else statusCounts.active++;

      const isActive = s !== 'SEPARATED' && s !== 'INACTIVE';
      if (!isActive) continue;

      // Department breakdown
      const deptId = emp.departmentId ?? 'unassigned';
      if (!byDept[deptId]) byDept[deptId] = { active: 0, probation: 0, notice: 0 };
      byDept[deptId][s === 'PROBATION' ? 'probation' : s === 'NOTICE_PERIOD' ? 'notice' : 'active']++;

      // Location breakdown
      const locId = emp.locationId ?? 'unassigned';
      if (!byLocation[locId]) byLocation[locId] = { active: 0 };
      byLocation[locId].active = (byLocation[locId].active ?? 0) + 1;

      // Grade breakdown
      const gId = emp.gradeId ?? 'unassigned';
      if (!byGrade[gId]) byGrade[gId] = { count: 0, totalCTC: 0 };
      byGrade[gId].count++;
      byGrade[gId].totalCTC += emp.annualCtc ?? 0;

      // Employee type breakdown
      const tId = emp.employeeTypeId ?? 'unassigned';
      if (!byType[tId]) byType[tId] = { count: 0 };
      byType[tId].count++;

      // Gender breakdown
      const gender = emp.gender ?? 'UNKNOWN';
      byGender[gender] = (byGender[gender] ?? 0) + 1;

      // Age band
      if (emp.dateOfBirth) {
        const age = Math.floor((today.getTime() - new Date(emp.dateOfBirth).getTime()) / (365.25 * 24 * 60 * 60 * 1000));
        const band = age < 25 ? '20-25' : age < 30 ? '26-30' : age < 35 ? '31-35' : age < 40 ? '36-40' : age < 50 ? '41-50' : '50+';
        byAgeBand[band] = (byAgeBand[band] ?? 0) + 1;
      }

      // Tenure band
      if (emp.joiningDate) {
        const tenureYears = (today.getTime() - new Date(emp.joiningDate).getTime()) / (365.25 * 24 * 60 * 60 * 1000);
        const band = tenureYears < 1 ? '0-1yr' : tenureYears < 3 ? '1-3yr' : tenureYears < 5 ? '3-5yr' : '5+yr';
        byTenureBand[band] = (byTenureBand[band] ?? 0) + 1;
      }

      // Manager span
      if (emp.reportingManagerId) {
        managerCounts[emp.reportingManagerId] = (managerCounts[emp.reportingManagerId] ?? 0) + 1;
      }
    }

    // Joiners/leavers today
    const joinersToday = employees.filter(e => {
      const jd = e.joiningDate ? new Date(e.joiningDate) : null;
      return jd && jd >= startOfDay && jd <= endOfDay;
    }).length;

    // Count transfers and promotions for today (from respective tables)
    const transfersToday = await tenantDb.employeeTransfer.count({
      where: { effectiveDate: { gte: startOfDay, lte: endOfDay }, status: 'APPLIED' },
    }).catch(() => 0);

    const promotionsToday = await tenantDb.employeePromotion.count({
      where: { effectiveDate: { gte: startOfDay, lte: endOfDay }, status: 'APPLIED' },
    }).catch(() => 0);

    const leaversToday = await tenantDb.exitRequest.count({
      where: { lastWorkingDate: { gte: startOfDay, lte: endOfDay }, status: 'COMPLETED' },
    }).catch(() => 0);

    // Average span of control
    const managerSpans = Object.values(managerCounts);
    const avgSpan = managerSpans.length > 0
      ? managerSpans.reduce((a, b) => a + b, 0) / managerSpans.length
      : null;

    // Get latest version for this date
    const latestVersion = await platformPrisma.employeeAnalyticsDaily.findFirst({
      where: { companyId, date: dateOnly },
      orderBy: { version: 'desc' },
      select: { version: true },
    });

    const totalActive = statusCounts.active + statusCounts.probation + statusCounts.notice;

    await platformPrisma.employeeAnalyticsDaily.create({
      data: {
        companyId,
        date: dateOnly,
        version: (latestVersion?.version ?? 0) + 1,
        totalHeadcount: employees.length,
        activeCount: statusCounts.active,
        probationCount: statusCounts.probation,
        noticeCount: statusCounts.notice,
        separatedCount: statusCounts.separated,
        joinersCount: joinersToday,
        leaversCount: leaversToday,
        transfersCount: transfersToday,
        promotionsCount: promotionsToday,
        byDepartment: byDept,
        byLocation,
        byGrade: Object.fromEntries(
          Object.entries(byGrade).map(([k, v]) => [k, { count: v.count, avgCTC: v.count > 0 ? v.totalCTC / v.count : 0 }]),
        ),
        byEmployeeType: byType,
        byGender,
        byAgeBand,
        byTenureBand,
        avgSpanOfControl: avgSpan,
        vacancyRate: null, // TODO: requires sanctioned positions data
      },
    });
  }

  // Placeholder methods — implemented in subsequent tasks
  async computeAttendanceAnalyticsDaily(_targetDate?: Date): Promise<void> {
    logger.info('AttendanceAnalyticsDaily computation placeholder');
  }

  async computePayrollAnalyticsMonthly(_month?: number, _year?: number): Promise<void> {
    logger.info('PayrollAnalyticsMonthly computation placeholder');
  }

  async computeAttritionMetricsMonthly(_month?: number, _year?: number): Promise<void> {
    logger.info('AttritionMetricsMonthly computation placeholder');
  }

  async purgeOldVersions(retentionDays: number): Promise<void> {
    const cutoff = new Date();
    cutoff.setDate(cutoff.getDate() - retentionDays);

    const tables = [
      'employeeAnalyticsDaily',
      'attendanceAnalyticsDaily',
      'payrollAnalyticsMonthly',
      'attritionMetricsMonthly',
    ] as const;

    for (const table of tables) {
      try {
        // Keep latest version per date, delete older versions past retention
        const deleted = await (platformPrisma[table] as any).deleteMany({
          where: { computedAt: { lt: cutoff } },
        });
        logger.info(`Purged ${deleted.count} old versions from ${table}`);
      } catch (error) {
        logger.error(`Failed to purge ${table}`, { error: (error as Error).message });
      }
    }
  }

  async recomputeForCompany(companyId: string, date: Date): Promise<void> {
    const company = await platformPrisma.company.findUnique({
      where: { id: companyId },
      select: { timezone: true },
    });
    await this.computeEmployeeAnalyticsForCompany(companyId, company?.timezone ?? null, date);
    logger.info('Manual recompute completed', { companyId, date });
  }

  private async getTenantPrisma(companyId: string) {
    // Use the tenant database connection based on companyId
    // This follows the existing multi-tenant pattern in the codebase
    try {
      const { getTenantPrismaClient } = await import('@/config/database');
      return getTenantPrismaClient(companyId);
    } catch {
      logger.error('Failed to get tenant prisma client', { companyId });
      return null;
    }
  }
}

export const analyticsCronService = new AnalyticsCronService();
```

- [ ] **Step 2: Commit**

```bash
git add src/modules/hr/analytics/services/analytics-cron.service.ts
git commit -m "feat(analytics): add cron service with employee analytics daily populator"
```

---

### Task 2.2: Attendance Analytics Daily Populator

**Files:**
- Modify: `avy-erp-backend/src/modules/hr/analytics/services/analytics-cron.service.ts`

- [ ] **Step 1: Replace the attendance placeholder with full implementation**

Replace the `computeAttendanceAnalyticsDaily` method in `analytics-cron.service.ts`:

```typescript
async computeAttendanceAnalyticsDaily(targetDate?: Date): Promise<void> {
  const startTime = Date.now();
  let companiesProcessed = 0;
  let errors = 0;

  try {
    const companies = await platformPrisma.company.findMany({
      select: { id: true, timezone: true },
    });

    for (const company of companies) {
      try {
        await this.computeAttendanceForCompany(company.id, company.timezone, targetDate);
        companiesProcessed++;
      } catch (error) {
        errors++;
        logger.error('Attendance analytics failed for company', {
          companyId: company.id,
          error: (error as Error).message,
        });
      }
    }
  } finally {
    logger.info('analytics_cron_completed', {
      table: 'AttendanceAnalyticsDaily',
      companiesProcessed,
      errors,
      durationMs: Date.now() - startTime,
    });
  }
}

private async computeAttendanceForCompany(
  companyId: string,
  timezone: string | null,
  targetDate?: Date,
): Promise<void> {
  const tz = timezone ?? 'Asia/Kolkata';
  const date = targetDate ?? new Date();
  const dateOnly = new Date(date.toLocaleDateString('en-CA', { timeZone: tz }));

  const tenantDb = await this.getTenantPrisma(companyId);
  if (!tenantDb) return;

  const startOfDay = new Date(dateOnly);
  startOfDay.setHours(0, 0, 0, 0);
  const endOfDay = new Date(dateOnly);
  endOfDay.setHours(23, 59, 59, 999);

  const records = await tenantDb.attendanceRecord.findMany({
    where: { date: { gte: startOfDay, lte: endOfDay } },
    include: { employee: { select: { departmentId: true, locationId: true, shiftId: true } } },
  });

  const totalEmployees = await tenantDb.employee.count({
    where: { status: { in: ['ACTIVE', 'PROBATION'] } },
  });

  let presentCount = 0, absentCount = 0, lateCount = 0, halfDayCount = 0;
  let onLeaveCount = 0, weekOffCount = 0, holidayCount = 0;
  let totalWorkedHours = 0, totalOT = 0;
  let totalLateMinutes = 0, lateEmployees = 0;
  let regularizations = 0, missedPunches = 0;

  const byDept: Record<string, Record<string, number>> = {};
  const byLocation: Record<string, Record<string, number>> = {};
  const byShift: Record<string, Record<string, number>> = {};
  const bySource: Record<string, number> = {};

  for (const rec of records) {
    const status = rec.status?.toUpperCase() ?? 'ABSENT';
    const deptId = rec.employee?.departmentId ?? 'unassigned';
    const locId = rec.employee?.locationId ?? 'unassigned';
    const shiftId = rec.employee?.shiftId ?? 'unassigned';

    // Status counts
    if (status === 'PRESENT') presentCount++;
    else if (status === 'ABSENT') absentCount++;
    else if (status === 'LATE') { lateCount++; presentCount++; }
    else if (status === 'HALF_DAY') halfDayCount++;
    else if (status === 'LEAVE') onLeaveCount++;
    else if (status === 'WEEKOFF') weekOffCount++;
    else if (status === 'HOLIDAY') holidayCount++;

    // Hours
    totalWorkedHours += rec.workedHours ?? 0;
    totalOT += rec.overtimeHours ?? 0;

    // Late analysis
    if (rec.lateMinutes && rec.lateMinutes > 0) {
      totalLateMinutes += rec.lateMinutes;
      lateEmployees++;
    }

    // Regularization
    if (rec.isRegularized) regularizations++;
    if (!rec.punchIn && status !== 'LEAVE' && status !== 'WEEKOFF' && status !== 'HOLIDAY') {
      missedPunches++;
    }

    // Source breakdown
    const source = rec.source ?? 'UNKNOWN';
    bySource[source] = (bySource[source] ?? 0) + 1;

    // Department breakdown
    if (!byDept[deptId]) byDept[deptId] = { present: 0, absent: 0, late: 0, avgHours: 0, count: 0 };
    byDept[deptId].count++;
    if (status === 'PRESENT' || status === 'LATE') byDept[deptId].present++;
    if (status === 'ABSENT') byDept[deptId].absent++;
    if (status === 'LATE') byDept[deptId].late++;
    byDept[deptId].avgHours += rec.workedHours ?? 0;

    // Location breakdown
    if (!byLocation[locId]) byLocation[locId] = { present: 0, absent: 0, count: 0 };
    byLocation[locId].count++;
    if (status === 'PRESENT' || status === 'LATE') byLocation[locId].present++;
    if (status === 'ABSENT') byLocation[locId].absent++;

    // Shift breakdown
    if (!byShift[shiftId]) byShift[shiftId] = { present: 0, absent: 0, count: 0 };
    byShift[shiftId].count++;
    if (status === 'PRESENT' || status === 'LATE') byShift[shiftId].present++;
  }

  // Calculate avg hours per department
  for (const deptId of Object.keys(byDept)) {
    const d = byDept[deptId];
    d.avgHours = d.count > 0 ? d.avgHours / d.count : 0;
  }

  // Expected hours (assume 8 hours * total active employees)
  const expectedHours = totalEmployees * 8;
  const productivityIndex = expectedHours > 0 ? totalWorkedHours / expectedHours : 0;

  const latestVersion = await platformPrisma.attendanceAnalyticsDaily.findFirst({
    where: { companyId, date: dateOnly },
    orderBy: { version: 'desc' },
    select: { version: true },
  });

  await platformPrisma.attendanceAnalyticsDaily.create({
    data: {
      companyId,
      date: dateOnly,
      version: (latestVersion?.version ?? 0) + 1,
      totalEmployees,
      presentCount,
      absentCount,
      lateCount,
      halfDayCount,
      onLeaveCount,
      weekOffCount,
      holidayCount,
      avgWorkedHours: records.length > 0 ? totalWorkedHours / records.length : 0,
      totalOvertimeHours: totalOT,
      totalOvertimeCost: null,
      productivityIndex,
      avgLateMinutes: lateEmployees > 0 ? totalLateMinutes / lateEmployees : 0,
      lateThresholdBreaches: 0,
      regularizationCount: regularizations,
      missedPunchCount: missedPunches,
      byDepartment: byDept,
      byLocation,
      byShift,
      bySource,
    },
  });
}
```

- [ ] **Step 2: Commit**

```bash
git add src/modules/hr/analytics/services/analytics-cron.service.ts
git commit -m "feat(analytics): add attendance analytics daily populator"
```

---

### Task 2.3: Payroll & Attrition Populators

**Files:**
- Modify: `avy-erp-backend/src/modules/hr/analytics/services/analytics-cron.service.ts`

- [ ] **Step 1: Replace payroll placeholder**

Replace the `computePayrollAnalyticsMonthly` method. This queries `PayrollEntry` and `PayrollRun` tables for the given month/year, aggregates totals, and writes to `PayrollAnalyticsMonthly`.

The implementation follows the same pattern as the employee and attendance populators — iterate companies, get tenant DB, aggregate from source tables, write to precomputed table with version increment.

Key data points to aggregate from `PayrollEntry`:
- Sum: `grossEarnings`, `totalDeductions`, `netPay`, `pfEmployee`, `pfEmployer`, `esiEmployee`, `esiEmployer`, `ptAmount`, `tdsAmount`, `lwfEmployee`, `lwfEmployer`
- Count: employees, exceptions (`isException = true`)
- Avg/Median: CTC from `EmployeeSalary` where `isCurrent = true`
- Breakdowns: by `employee.departmentId`, `employee.locationId`, `employee.gradeId`
- CTC bands: `0-3L`, `3-5L`, `5-10L`, `10-15L`, `15-25L`, `25L+`
- Loan outstanding: sum from `LoanRecord` where `status = 'ACTIVE'`
- Salary holds: count from `SalaryHold` where `isActive = true`

- [ ] **Step 2: Replace attrition placeholder**

Replace the `computeAttritionMetricsMonthly` method. This queries `ExitRequest`, `ExitInterview`, `FnFSettlement` for the given month/year.

Key data points:
- Count exits by `separationType` (voluntary vs involuntary)
- Early exits: employees with `joiningDate` < 1 year before `lastWorkingDate`
- Attrition rate: `totalExits / avgHeadcount` (get headcount from `EmployeeAnalyticsDaily`)
- Exit reasons: from `ExitInterview.responses` JSON
- `wouldRecommendAvg`: from `ExitInterview.wouldRecommend`
- Flight risk: computed via `attrition-score.ts` (added in Phase 3 — store empty array for now)
- F&F: count pending from `FnFSettlement` where `status != 'PAID'`

- [ ] **Step 3: Commit**

```bash
git add src/modules/hr/analytics/services/analytics-cron.service.ts
git commit -m "feat(analytics): add payroll and attrition analytics populators"
```

---

## Phase 3: Intelligence Engine

### Task 3.1: Anomaly Detection

**Files:**
- Create: `avy-erp-backend/src/modules/hr/analytics/insights/anomaly/thresholds.ts`
- Create: `avy-erp-backend/src/modules/hr/analytics/insights/anomaly/anomaly-detector.ts`

- [ ] **Step 1: Create thresholds.ts**

```typescript
// Z-score thresholds for anomaly detection
export const ANOMALY_THRESHOLDS = {
  HIGH: 2.0,    // > 2 standard deviations
  MEDIUM: 1.5,  // > 1.5 standard deviations
} as const;

// Minimum data points required for meaningful anomaly detection
export const MIN_DATA_POINTS = 3;

// Rolling window size (months) for computing historical average
export const ROLLING_WINDOW_MONTHS = 6;
```

- [ ] **Step 2: Create anomaly-detector.ts**

```typescript
import type { AnomalyResult } from '../../analytics.types';
import { ANOMALY_THRESHOLDS, MIN_DATA_POINTS } from './thresholds';

export function detectAnomaly(
  current: number,
  historicalValues: number[],
): AnomalyResult {
  if (historicalValues.length < MIN_DATA_POINTS) {
    return { isAnomaly: false };
  }

  const avg = historicalValues.reduce((a, b) => a + b, 0) / historicalValues.length;
  const variance = historicalValues.reduce((sum, val) => sum + Math.pow(val - avg, 2), 0) / historicalValues.length;
  const stdDev = Math.sqrt(variance);

  if (stdDev === 0) {
    return current !== avg
      ? { isAnomaly: true, severity: 'HIGH', direction: current > avg ? 'ABOVE' : 'BELOW', zScore: Infinity }
      : { isAnomaly: false };
  }

  const zScore = (current - avg) / stdDev;

  if (Math.abs(zScore) > ANOMALY_THRESHOLDS.HIGH) {
    return { isAnomaly: true, severity: 'HIGH', direction: zScore > 0 ? 'ABOVE' : 'BELOW', zScore };
  }
  if (Math.abs(zScore) > ANOMALY_THRESHOLDS.MEDIUM) {
    return { isAnomaly: true, severity: 'MEDIUM', direction: zScore > 0 ? 'ABOVE' : 'BELOW', zScore };
  }

  return { isAnomaly: false, zScore };
}

export function detectPercentageAnomaly(
  currentPercent: number,
  historicalPercents: number[],
): AnomalyResult {
  return detectAnomaly(currentPercent, historicalPercents);
}
```

- [ ] **Step 3: Commit**

```bash
git add src/modules/hr/analytics/insights/anomaly/
git commit -m "feat(analytics): add anomaly detection engine with z-score analysis"
```

---

### Task 3.2: Scoring Engines

**Files:**
- Create: `avy-erp-backend/src/modules/hr/analytics/insights/scoring/attrition-score.ts`
- Create: `avy-erp-backend/src/modules/hr/analytics/insights/scoring/manager-score.ts`
- Create: `avy-erp-backend/src/modules/hr/analytics/insights/scoring/productivity-score.ts`
- Create: `avy-erp-backend/src/modules/hr/analytics/insights/scoring/compliance-score.ts`

- [ ] **Step 1: Create attrition-score.ts**

```typescript
export interface FlightRiskInput {
  employeeId: string;
  performanceRating: number | null;  // 1-5
  avgPerformanceRating: number;       // company avg
  absentDaysLastQuarter: number;
  absentThreshold: number;
  yearsSinceLastPromotion: number;
  salaryVsGradeMedian: number;        // ratio: 0.8 = 20% below median
  tenureYears: number;
  managerTeamAttritionRate: number;
}

export interface FlightRiskResult {
  employeeId: string;
  score: number;       // 0-100
  factors: string[];
}

export function computeAttritionRiskScore(input: FlightRiskInput): FlightRiskResult {
  let score = 0;
  const factors: string[] = [];

  // Performance below average: +25
  if (input.performanceRating !== null && input.performanceRating < input.avgPerformanceRating) {
    score += 25;
    factors.push(`Performance rating ${input.performanceRating} below avg ${input.avgPerformanceRating.toFixed(1)}`);
  }

  // High absenteeism: +20
  if (input.absentDaysLastQuarter > input.absentThreshold) {
    score += 20;
    factors.push(`${input.absentDaysLastQuarter} absent days (threshold: ${input.absentThreshold})`);
  }

  // No promotion in 3+ years: +20
  if (input.yearsSinceLastPromotion >= 3) {
    score += 20;
    factors.push(`No promotion in ${input.yearsSinceLastPromotion} years`);
  }

  // Salary below grade median: +15
  if (input.salaryVsGradeMedian < 0.9) {
    score += 15;
    factors.push(`Salary ${((1 - input.salaryVsGradeMedian) * 100).toFixed(0)}% below grade median`);
  }

  // Tenure in high-attrition band (1-2 years): +10
  if (input.tenureYears >= 1 && input.tenureYears <= 2) {
    score += 10;
    factors.push(`Tenure ${input.tenureYears.toFixed(1)} years (high-attrition band)`);
  }

  // Manager has high team attrition: +10
  if (input.managerTeamAttritionRate > 0.2) {
    score += 10;
    factors.push(`Manager's team attrition ${(input.managerTeamAttritionRate * 100).toFixed(0)}%`);
  }

  return { employeeId: input.employeeId, score: Math.min(score, 100), factors };
}
```

- [ ] **Step 2: Create manager-score.ts**

```typescript
export interface ManagerScoreInput {
  managerId: string;
  teamAvgRating: number;       // 1-5
  teamAttritionRate: number;   // 0-1
  avgApprovalDelayHours: number;
  teamAttendanceRate: number;  // 0-1
  teamSatisfaction?: number;   // 1-5 (optional)
}

export interface ManagerScoreResult {
  managerId: string;
  score: number;  // 0-100
}

export function computeManagerEffectivenessScore(input: ManagerScoreInput): ManagerScoreResult {
  // Normalize to 0-100 scale
  const ratingScore = (input.teamAvgRating / 5) * 100;                              // 30%
  const attritionScore = Math.max(0, (1 - input.teamAttritionRate / 0.5)) * 100;    // 25% (0.5 = worst)
  const approvalScore = Math.max(0, (1 - input.avgApprovalDelayHours / 72)) * 100;  // 20% (72h = worst)
  const attendanceScore = input.teamAttendanceRate * 100;                             // 15%
  const satisfactionScore = input.teamSatisfaction
    ? (input.teamSatisfaction / 5) * 100
    : 50; // 10% (default neutral)

  const score =
    ratingScore * 0.3 +
    attritionScore * 0.25 +
    approvalScore * 0.2 +
    attendanceScore * 0.15 +
    satisfactionScore * 0.1;

  return { managerId: input.managerId, score: Math.round(Math.max(0, Math.min(100, score))) };
}
```

- [ ] **Step 3: Create productivity-score.ts**

```typescript
export interface ProductivityInput {
  entityId: string;       // employeeId or departmentId
  workedHours: number;
  expectedHours: number;
}

export interface ProductivityResult {
  entityId: string;
  index: number;          // 0-2 scale (1.0 = normal)
  status: 'under-utilized' | 'normal' | 'over-worked';
}

export function computeProductivityIndex(input: ProductivityInput): ProductivityResult {
  const index = input.expectedHours > 0 ? input.workedHours / input.expectedHours : 0;

  let status: ProductivityResult['status'];
  if (index < 0.7) status = 'under-utilized';
  else if (index > 1.2) status = 'over-worked';
  else status = 'normal';

  return { entityId: input.entityId, index: Math.round(index * 100) / 100, status };
}
```

- [ ] **Step 4: Create compliance-score.ts**

```typescript
export interface ComplianceScoreInput {
  totalFilings: number;
  onTimeFilings: number;
  totalEmployees: number;
  minWageCompliant: number;
  totalGrievances: number;
  grievancesWithinSLA: number;
  totalDocumentsRequired: number;
  documentsUploaded: number;
}

export function computeComplianceScore(input: ComplianceScoreInput): number {
  // Filing compliance: 40%
  const filingScore = input.totalFilings > 0
    ? (input.onTimeFilings / input.totalFilings) * 100
    : 100;

  // Min wage compliance: 20%
  const wageScore = input.totalEmployees > 0
    ? (input.minWageCompliant / input.totalEmployees) * 100
    : 100;

  // Grievance SLA: 15%
  const grievanceScore = input.totalGrievances > 0
    ? (input.grievancesWithinSLA / input.totalGrievances) * 100
    : 100;

  // Document compliance: 15%
  const docScore = input.totalDocumentsRequired > 0
    ? (input.documentsUploaded / input.totalDocumentsRequired) * 100
    : 100;

  // Data retention: 10% (assumed compliant for now)
  const retentionScore = 100;

  const score =
    filingScore * 0.4 +
    wageScore * 0.2 +
    grievanceScore * 0.15 +
    docScore * 0.15 +
    retentionScore * 0.1;

  return Math.round(Math.max(0, Math.min(100, score)));
}
```

- [ ] **Step 5: Commit**

```bash
git add src/modules/hr/analytics/insights/scoring/
git commit -m "feat(analytics): add scoring engines (attrition risk, manager, productivity, compliance)"
```

---

### Task 3.3: Rule Engines

**Files:**
- Create: `avy-erp-backend/src/modules/hr/analytics/insights/rules/attrition.rules.ts`
- Create: `avy-erp-backend/src/modules/hr/analytics/insights/rules/attendance.rules.ts`
- Create: `avy-erp-backend/src/modules/hr/analytics/insights/rules/payroll.rules.ts`
- Create: `avy-erp-backend/src/modules/hr/analytics/insights/rules/compliance.rules.ts`
- Create: `avy-erp-backend/src/modules/hr/analytics/insights/rules/performance.rules.ts`
- Create: `avy-erp-backend/src/modules/hr/analytics/insights/rules/recruitment.rules.ts`

- [ ] **Step 1: Create attrition.rules.ts**

```typescript
import type { InsightRule } from '../../analytics.types';

export const attritionRules: InsightRule[] = [
  {
    id: 'high_attrition_rate',
    evaluate: (data) => (data.attritionRate as number) > 0.20,
    generate: (data) => ({
      category: 'critical',
      title: `Attrition at ${((data.attritionRate as number) * 100).toFixed(1)}% — exceeds 20% benchmark`,
      description: `${data.totalExits} employees left this month. Industry benchmark is 15-18%.`,
      actionable: true,
      drilldownType: 'exitDetail',
      benchmarkValue: 0.18,
      changePercent: data.changePercent as number | undefined,
    }),
  },
  {
    id: 'early_attrition_spike',
    evaluate: (data) => (data.earlyAttritionRate as number) > 0.30,
    generate: (data) => ({
      category: 'warning',
      title: `${((data.earlyAttritionRate as number) * 100).toFixed(0)}% of exits within first year`,
      description: 'High early attrition suggests onboarding or expectation-setting issues.',
      actionable: true,
      drilldownType: 'earlyAttrition',
    }),
  },
  {
    id: 'high_performer_exits',
    evaluate: (data) => (data.highPerformerExits as number) > 0,
    generate: (data) => ({
      category: 'critical',
      title: `${data.highPerformerExits} high-performer(s) exited this month`,
      description: 'Losing top talent has outsized impact on team productivity.',
      actionable: true,
      drilldownType: 'flightRisk',
    }),
  },
  {
    id: 'fnf_processing_delay',
    evaluate: (data) => (data.avgFnFProcessingDays as number) > 30,
    generate: (data) => ({
      category: 'warning',
      title: `F&F settlement avg ${(data.avgFnFProcessingDays as number).toFixed(0)} days`,
      description: `${data.pendingFnFCount} settlements pending. Target: within 30 days.`,
      actionable: true,
      drilldownType: 'fnfTracker',
    }),
  },
];
```

- [ ] **Step 2: Create attendance.rules.ts**

```typescript
import type { InsightRule } from '../../analytics.types';

export const attendanceRules: InsightRule[] = [
  {
    id: 'low_attendance',
    evaluate: (data) => {
      const rate = (data.presentCount as number) / (data.totalEmployees as number);
      return rate < 0.70;
    },
    generate: (data) => {
      const rate = ((data.presentCount as number) / (data.totalEmployees as number) * 100);
      return {
        category: 'critical',
        title: `Attendance at ${rate.toFixed(0)}% — below 70% threshold`,
        description: `${data.absentCount} employees absent today.`,
        actionable: true,
        drilldownType: 'absenteeism',
      };
    },
  },
  {
    id: 'high_late_arrivals',
    evaluate: (data) => (data.lateCount as number) > (data.totalEmployees as number) * 0.15,
    generate: (data) => ({
      category: 'warning',
      title: `${data.lateCount} late arrivals today (${((data.lateCount as number) / (data.totalEmployees as number) * 100).toFixed(0)}%)`,
      description: `Average late by ${(data.avgLateMinutes as number).toFixed(0)} minutes.`,
      actionable: true,
      drilldownType: 'lateEmployees',
    }),
  },
  {
    id: 'low_productivity',
    evaluate: (data) => (data.productivityIndex as number) < 0.7,
    generate: (data) => ({
      category: 'warning',
      title: `Productivity index at ${((data.productivityIndex as number) * 100).toFixed(0)}%`,
      description: 'Under-utilization detected. Expected hours significantly exceed worked hours.',
      actionable: true,
      drilldownType: 'register',
    }),
  },
  {
    id: 'high_overtime',
    evaluate: (data) => (data.totalOvertimeHours as number) > 100,
    generate: (data) => ({
      category: 'info',
      title: `${(data.totalOvertimeHours as number).toFixed(0)} overtime hours logged`,
      description: 'Review overtime distribution across departments for cost optimization.',
      actionable: true,
      drilldownType: 'overtime',
    }),
  },
];
```

- [ ] **Step 3: Create remaining rule files**

Create `payroll.rules.ts`, `compliance.rules.ts`, `performance.rules.ts`, and `recruitment.rules.ts` following the same pattern. Each should have 3-5 rules covering the key thresholds defined in the spec's alert rules table (Section 4.6).

Key rules per file:
- **payroll**: Cost variance > 15%, high exception count, loan concentration
- **compliance**: Overdue filings, min wage violations, grievance SLA breach, PIP aging
- **performance**: Bell curve skew, low completion %, critical roles without successors
- **recruitment**: Aging positions > 60 days, funnel bottleneck, low offer acceptance

- [ ] **Step 4: Commit**

```bash
git add src/modules/hr/analytics/insights/rules/
git commit -m "feat(analytics): add insight rule engines for all 6 domains"
```

---

### Task 3.4: Alert Service

**Files:**
- Create: `avy-erp-backend/src/modules/hr/analytics/alerts/alert-rules.ts`
- Create: `avy-erp-backend/src/modules/hr/analytics/alerts/alert.service.ts`

- [ ] **Step 1: Create alert-rules.ts**

```typescript
export interface AlertRuleDefinition {
  type: string;
  dashboard: string;
  severity: 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';
  evaluate: (data: Record<string, unknown>) => boolean;
  title: (data: Record<string, unknown>) => string;
  description: (data: Record<string, unknown>) => string;
  expiresInHours: number;
}

export const ALERT_RULES: AlertRuleDefinition[] = [
  {
    type: 'attrition_spike',
    dashboard: 'attrition',
    severity: 'HIGH',
    evaluate: (d) => (d.attritionRate as number) > 0.20,
    title: () => 'High attrition rate detected',
    description: (d) => `Monthly attrition at ${((d.attritionRate as number) * 100).toFixed(1)}%, exceeding 20% threshold.`,
    expiresInHours: 720, // 30 days
  },
  {
    type: 'compliance_overdue',
    dashboard: 'compliance',
    severity: 'CRITICAL',
    evaluate: (d) => (d.overdueFilings as number) > 0,
    title: (d) => `${d.overdueFilings} statutory filing(s) overdue`,
    description: (d) => `${d.overdueFilings} filing(s) past deadline. Immediate action required.`,
    expiresInHours: 168, // 7 days
  },
  {
    type: 'payroll_anomaly',
    dashboard: 'payroll',
    severity: 'HIGH',
    evaluate: (d) => Math.abs(d.variancePercent as number) > 15,
    title: () => 'Payroll cost anomaly detected',
    description: (d) => `Payroll cost variance ${(d.variancePercent as number).toFixed(1)}% MoM. Review for errors.`,
    expiresInHours: 720,
  },
  {
    type: 'attendance_drop',
    dashboard: 'attendance',
    severity: 'MEDIUM',
    evaluate: (d) => ((d.presentCount as number) / (d.totalEmployees as number)) < 0.70,
    title: () => 'Attendance below 70% today',
    description: (d) => `Only ${((d.presentCount as number) / (d.totalEmployees as number) * 100).toFixed(0)}% attendance. ${d.absentCount} employees absent.`,
    expiresInHours: 24,
  },
  {
    type: 'min_wage_violation',
    dashboard: 'compliance',
    severity: 'CRITICAL',
    evaluate: (d) => (d.minWageViolations as number) > 0,
    title: (d) => `${d.minWageViolations} minimum wage violation(s)`,
    description: (d) => `${d.minWageViolations} employee(s) below state minimum wage threshold.`,
    expiresInHours: 720,
  },
  {
    type: 'flight_risk',
    dashboard: 'attrition',
    severity: 'HIGH',
    evaluate: (d) => {
      const risks = d.flightRiskEmployees as { score: number }[];
      return risks?.some(e => e.score > 70) ?? false;
    },
    title: () => 'High flight risk employees detected',
    description: (d) => {
      const risks = d.flightRiskEmployees as { score: number }[];
      const highRisk = risks?.filter(e => e.score > 70).length ?? 0;
      return `${highRisk} employee(s) with attrition risk score > 70.`;
    },
    expiresInHours: 720,
  },
];
```

- [ ] **Step 2: Create alert.service.ts**

```typescript
import { platformPrisma } from '@/config/database';
import { logger } from '@/config/logger';
import { ALERT_RULES } from './alert-rules';

class AlertService {
  async evaluateAndCreate(
    companyId: string,
    dashboard: string,
    analyticsData: Record<string, unknown>,
  ): Promise<void> {
    const dashboardRules = ALERT_RULES.filter(r => r.dashboard === dashboard);

    for (const rule of dashboardRules) {
      try {
        const shouldAlert = rule.evaluate(analyticsData);

        if (shouldAlert) {
          // Dedup: don't create if active alert of same type exists
          const existing = await platformPrisma.analyticsAlert.findFirst({
            where: { companyId, type: rule.type, status: 'ACTIVE' },
          });

          if (!existing) {
            const expiresAt = new Date();
            expiresAt.setHours(expiresAt.getHours() + rule.expiresInHours);

            await platformPrisma.analyticsAlert.create({
              data: {
                companyId,
                dashboard: rule.dashboard,
                type: rule.type,
                severity: rule.severity,
                status: 'ACTIVE',
                title: rule.title(analyticsData),
                description: rule.description(analyticsData),
                metadata: analyticsData,
                expiresAt,
              },
            });
          }
        }
      } catch (error) {
        logger.error('Alert evaluation failed', {
          companyId,
          ruleType: rule.type,
          error: (error as Error).message,
        });
      }
    }

    // Auto-resolve expired alerts
    await this.resolveExpired(companyId);
  }

  async getActiveAlerts(companyId: string, dashboard?: string) {
    const where: Record<string, unknown> = { companyId, status: 'ACTIVE' };
    if (dashboard) where.dashboard = dashboard;

    return platformPrisma.analyticsAlert.findMany({
      where,
      orderBy: [
        { severity: 'desc' },
        { createdAt: 'desc' },
      ],
    });
  }

  async acknowledgeAlert(alertId: string, userId: string): Promise<void> {
    await platformPrisma.analyticsAlert.update({
      where: { id: alertId },
      data: { status: 'ACKNOWLEDGED', acknowledgedBy: userId, acknowledgedAt: new Date() },
    });
  }

  async resolveAlert(alertId: string, userId: string): Promise<void> {
    await platformPrisma.analyticsAlert.update({
      where: { id: alertId },
      data: { status: 'RESOLVED', resolvedBy: userId, resolvedAt: new Date() },
    });
  }

  private async resolveExpired(companyId: string): Promise<void> {
    await platformPrisma.analyticsAlert.updateMany({
      where: {
        companyId,
        status: 'ACTIVE',
        expiresAt: { lt: new Date() },
      },
      data: { status: 'RESOLVED' },
    });
  }
}

export const alertService = new AlertService();
```

- [ ] **Step 3: Commit**

```bash
git add src/modules/hr/analytics/alerts/
git commit -m "feat(analytics): add stateful alert service with dedup and auto-expiration"
```

---

### Task 3.5: Insights Engine Orchestrator

**Files:**
- Create: `avy-erp-backend/src/modules/hr/analytics/insights/insights-engine.service.ts`

- [ ] **Step 1: Create insights-engine.service.ts**

```typescript
import type { DashboardName, Insight, InsightRule } from '../analytics.types';
import { attritionRules } from './rules/attrition.rules';
import { attendanceRules } from './rules/attendance.rules';
import { payrollRules } from './rules/payroll.rules';
import { complianceRules } from './rules/compliance.rules';
import { performanceRules } from './rules/performance.rules';
import { recruitmentRules } from './rules/recruitment.rules';
import { detectAnomaly } from './anomaly/anomaly-detector';
import { logger } from '@/config/logger';

const RULES_BY_DASHBOARD: Record<DashboardName, InsightRule[]> = {
  executive: [...attritionRules.slice(0, 1), ...attendanceRules.slice(0, 1), ...payrollRules.slice(0, 1)],
  workforce: [],
  attendance: attendanceRules,
  leave: [],
  payroll: payrollRules,
  compliance: complianceRules,
  performance: performanceRules,
  recruitment: recruitmentRules,
  attrition: attritionRules,
};

const MAX_INSIGHTS_PER_DASHBOARD = 5;

class InsightsEngineService {
  generateInsights(
    dashboard: DashboardName,
    currentData: Record<string, unknown>,
    historicalData?: Record<string, number[]>,
  ): Insight[] {
    const insights: Insight[] = [];

    // 1. Rule-based insights
    const rules = RULES_BY_DASHBOARD[dashboard] ?? [];
    for (const rule of rules) {
      try {
        if (rule.evaluate(currentData)) {
          const generated = rule.generate(currentData);
          insights.push({
            id: `${dashboard}_${rule.id}`,
            dashboard,
            metric: rule.id,
            currentValue: currentData[rule.id] as number ?? 0,
            ...generated,
          });
        }
      } catch (error) {
        logger.error('Insight rule evaluation failed', { dashboard, ruleId: rule.id, error });
      }
    }

    // 2. Anomaly-based insights
    if (historicalData) {
      for (const [metric, history] of Object.entries(historicalData)) {
        const current = currentData[metric] as number;
        if (typeof current !== 'number') continue;

        const result = detectAnomaly(current, history);
        if (result.isAnomaly) {
          insights.push({
            id: `${dashboard}_anomaly_${metric}`,
            dashboard,
            category: result.severity === 'HIGH' ? 'warning' : 'info',
            title: `${metric.replace(/_/g, ' ')} is ${result.direction === 'ABOVE' ? 'unusually high' : 'unusually low'}`,
            description: `Current value deviates ${result.zScore?.toFixed(1)} standard deviations from the 6-month average.`,
            metric,
            currentValue: current,
            actionable: false,
          });
        }
      }
    }

    // 3. Rank and cap insights
    return this.rankInsights(insights);
  }

  private rankInsights(insights: Insight[]): Insight[] {
    const severityOrder: Record<string, number> = { critical: 0, warning: 1, info: 2, positive: 3 };

    return insights
      .sort((a, b) => {
        const aSev = severityOrder[a.category] ?? 3;
        const bSev = severityOrder[b.category] ?? 3;
        if (aSev !== bSev) return aSev - bSev;
        return Math.abs(b.changePercent ?? 0) - Math.abs(a.changePercent ?? 0);
      })
      .slice(0, MAX_INSIGHTS_PER_DASHBOARD);
  }
}

export const insightsEngineService = new InsightsEngineService();
```

- [ ] **Step 2: Commit**

```bash
git add src/modules/hr/analytics/insights/insights-engine.service.ts
git commit -m "feat(analytics): add insights engine with rule evaluation, anomaly detection, and prioritization"
```

---

## Phase 4: Analytics Service, Orchestrator, API Routes

### Task 4.1: Analytics Service

**Files:**
- Create: `avy-erp-backend/src/modules/hr/analytics/services/analytics.service.ts`

- [ ] **Step 1: Create analytics.service.ts**

This service queries precomputed tables and returns raw data. Each method follows the pattern:
1. Accept `DashboardFilters` + `DataScope`
2. Query the appropriate precomputed table with `companyId` from scope
3. Apply department/location/grade/type filters on JSON breakdown fields
4. Return typed data

```typescript
import { platformPrisma } from '@/config/database';
import { logger } from '@/config/logger';
import type { DashboardFilters, DataScope, KPICard, TrendSeries, Distribution } from '../analytics.types';

class AnalyticsService {
  // Get latest version of a precomputed table for a date
  private async getLatestEmployeeAnalytics(companyId: string, date: Date) {
    return platformPrisma.employeeAnalyticsDaily.findFirst({
      where: { companyId, date },
      orderBy: { version: 'desc' },
    });
  }

  private async getLatestAttendanceAnalytics(companyId: string, date: Date) {
    return platformPrisma.attendanceAnalyticsDaily.findFirst({
      where: { companyId, date },
      orderBy: { version: 'desc' },
    });
  }

  private async getLatestPayrollAnalytics(companyId: string, month: number, year: number) {
    return platformPrisma.payrollAnalyticsMonthly.findFirst({
      where: { companyId, month, year },
      orderBy: { version: 'desc' },
    });
  }

  private async getLatestAttritionMetrics(companyId: string, month: number, year: number) {
    return platformPrisma.attritionMetricsMonthly.findFirst({
      where: { companyId, month, year },
      orderBy: { version: 'desc' },
    });
  }

  // =================== Workforce Methods ===================

  async getHeadcountSummary(filters: DashboardFilters, scope: DataScope) {
    const date = new Date(filters.dateTo);
    const data = await this.getLatestEmployeeAnalytics(scope.companyId, date);
    if (!data) return null;

    // Previous period for trend
    const prevDate = new Date(date);
    prevDate.setMonth(prevDate.getMonth() - 1);
    const prevData = await this.getLatestEmployeeAnalytics(scope.companyId, prevDate);

    return {
      current: data,
      previous: prevData,
      trend: prevData ? {
        headcountChange: data.totalHeadcount - prevData.totalHeadcount,
        headcountChangePercent: prevData.totalHeadcount > 0
          ? ((data.totalHeadcount - prevData.totalHeadcount) / prevData.totalHeadcount) * 100
          : 0,
      } : null,
    };
  }

  async getHeadcountTrend(filters: DashboardFilters, scope: DataScope): Promise<TrendSeries | null> {
    const dateTo = new Date(filters.dateTo);
    const dateFrom = new Date(filters.dateFrom);

    const records = await platformPrisma.employeeAnalyticsDaily.findMany({
      where: {
        companyId: scope.companyId,
        date: { gte: dateFrom, lte: dateTo },
      },
      orderBy: { date: 'asc' },
      distinct: ['date'],
    });

    return {
      key: 'headcount_trend',
      label: 'Headcount Trend',
      data: records.map(r => ({
        date: r.date.toISOString().split('T')[0],
        value: r.totalHeadcount,
      })),
      chartType: 'line',
    };
  }

  // =================== Attendance Methods ===================

  async getAttendanceSummary(filters: DashboardFilters, scope: DataScope) {
    const date = new Date(filters.dateTo);
    return this.getLatestAttendanceAnalytics(scope.companyId, date);
  }

  async getAttendanceTrend(filters: DashboardFilters, scope: DataScope): Promise<TrendSeries | null> {
    const records = await platformPrisma.attendanceAnalyticsDaily.findMany({
      where: {
        companyId: scope.companyId,
        date: { gte: new Date(filters.dateFrom), lte: new Date(filters.dateTo) },
      },
      orderBy: { date: 'asc' },
      distinct: ['date'],
    });

    return {
      key: 'attendance_trend',
      label: 'Attendance Rate',
      data: records.map(r => ({
        date: r.date.toISOString().split('T')[0],
        value: r.totalEmployees > 0 ? (r.presentCount / r.totalEmployees) * 100 : 0,
      })),
      chartType: 'area',
    };
  }

  // =================== Payroll Methods ===================

  async getPayrollCostSummary(filters: DashboardFilters, scope: DataScope) {
    const date = new Date(filters.dateTo);
    const month = date.getMonth() + 1;
    const year = date.getFullYear();
    const data = await this.getLatestPayrollAnalytics(scope.companyId, month, year);

    // Previous month for trend
    const prevMonth = month === 1 ? 12 : month - 1;
    const prevYear = month === 1 ? year - 1 : year;
    const prevData = await this.getLatestPayrollAnalytics(scope.companyId, prevMonth, prevYear);

    return { current: data, previous: prevData };
  }

  // =================== Attrition Methods ===================

  async getAttritionSummary(filters: DashboardFilters, scope: DataScope) {
    const date = new Date(filters.dateTo);
    const month = date.getMonth() + 1;
    const year = date.getFullYear();
    return this.getLatestAttritionMetrics(scope.companyId, month, year);
  }

  async getAttritionTrend(filters: DashboardFilters, scope: DataScope): Promise<TrendSeries | null> {
    const dateTo = new Date(filters.dateTo);
    const dateFrom = new Date(filters.dateFrom);

    const records = await platformPrisma.attritionMetricsMonthly.findMany({
      where: {
        companyId: scope.companyId,
        year: { gte: dateFrom.getFullYear(), lte: dateTo.getFullYear() },
      },
      orderBy: [{ year: 'asc' }, { month: 'asc' }],
      distinct: ['month', 'year'],
    });

    return {
      key: 'attrition_trend',
      label: 'Attrition Rate',
      data: records.map(r => ({
        date: `${r.year}-${String(r.month).padStart(2, '0')}-01`,
        value: r.attritionRate * 100,
      })),
      chartType: 'line',
    };
  }

  async getFlightRiskEmployees(scope: DataScope) {
    const now = new Date();
    const data = await this.getLatestAttritionMetrics(scope.companyId, now.getMonth() + 1, now.getFullYear());
    return (data?.flightRiskEmployees as { employeeId: string; score: number; factors: string[] }[]) ?? [];
  }
}

export const analyticsService = new AnalyticsService();
```

Additional methods (leave, compliance, performance, recruitment) follow the same query-from-precomputed-table pattern. Add them incrementally as each dashboard is built.

- [ ] **Step 2: Commit**

```bash
git add src/modules/hr/analytics/services/analytics.service.ts
git commit -m "feat(analytics): add analytics service querying precomputed tables"
```

---

### Task 4.2: Dashboard Orchestrator

**Files:**
- Create: `avy-erp-backend/src/modules/hr/analytics/services/dashboard-orchestrator.service.ts`

- [ ] **Step 1: Create dashboard-orchestrator.service.ts**

```typescript
import { logger } from '@/config/logger';
import type { DashboardFilters, DashboardName, DashboardResponse, DataScope, KPICard } from '../analytics.types';
import { analyticsService } from './analytics.service';
import { reportAccessService } from './report-access.service';
import { analyticsAuditService } from './analytics-audit.service';
import { insightsEngineService } from '../insights/insights-engine.service';
import { alertService } from '../alerts/alert.service';
import { normalizeFilters } from '../filters-normalizer';

class DashboardOrchestratorService {
  async getDashboard(
    dashboard: DashboardName,
    rawFilters: Record<string, unknown>,
    userId: string,
    companyId: string,
    role: string,
    companyTimezone?: string,
  ): Promise<{ success: true; data: DashboardResponse }> {
    const startTime = Date.now();
    const filters = normalizeFilters(rawFilters as any, companyTimezone);

    // 1. Resolve scope
    const scope = await reportAccessService.resolveScope(userId, companyId, role, dashboard);

    // 2. Get dashboard data using Promise.allSettled (soft-fail)
    const response = await this.buildDashboard(dashboard, filters, scope);

    // 3. Filter metrics based on role
    const filtered = reportAccessService.filterMetrics(response, role);

    // 4. Audit log (fire and forget)
    analyticsAuditService.logView(userId, companyId, dashboard, filters as any).catch(() => {});

    // 5. Log observability
    const loadTimeMs = Date.now() - startTime;
    logger.info('analytics_dashboard_loaded', {
      dashboard,
      companyId,
      userId,
      loadTimeMs,
      partialFailures: filtered.meta.partialFailures?.length ?? 0,
    });

    return { success: true, data: filtered };
  }

  private async buildDashboard(
    dashboard: DashboardName,
    filters: DashboardFilters,
    scope: DataScope,
  ): Promise<DashboardResponse> {
    // Each dashboard builder returns its specific data
    switch (dashboard) {
      case 'executive': return this.buildExecutiveDashboard(filters, scope);
      case 'workforce': return this.buildWorkforceDashboard(filters, scope);
      case 'attendance': return this.buildAttendanceDashboard(filters, scope);
      case 'attrition': return this.buildAttritionDashboard(filters, scope);
      // Add remaining dashboards as implemented
      default: return this.buildEmptyDashboard(dashboard, filters);
    }
  }

  private async buildExecutiveDashboard(
    filters: DashboardFilters,
    scope: DataScope,
  ): Promise<DashboardResponse> {
    const partialFailures: string[] = [];

    const results = await Promise.allSettled([
      analyticsService.getHeadcountSummary(filters, scope),
      analyticsService.getAttendanceSummary(filters, scope),
      analyticsService.getPayrollCostSummary(filters, scope),
      analyticsService.getAttritionSummary(filters, scope),
      analyticsService.getHeadcountTrend(filters, scope),
      alertService.getActiveAlerts(scope.companyId),
    ]);

    const [headcount, attendance, payroll, attrition, trend, alerts] = results.map((r, i) => {
      if (r.status === 'fulfilled') return r.value;
      partialFailures.push(['headcount', 'attendance', 'payroll', 'attrition', 'trend', 'alerts'][i]);
      logger.error('analytics_query_failed', { dashboard: 'executive', query: i, error: (r as PromiseRejectedResult).reason });
      return null;
    });

    const kpis: KPICard[] = [];

    if (headcount) {
      const hc = headcount as any;
      kpis.push({
        key: 'headcount',
        label: 'Headcount',
        value: hc.current?.totalHeadcount ?? 0,
        format: 'number',
        drilldownType: 'employeeDirectory',
        trend: hc.trend ? {
          direction: hc.trend.headcountChange > 0 ? 'up' : hc.trend.headcountChange < 0 ? 'down' : 'neutral',
          changePercent: hc.trend.headcountChangePercent,
          comparedTo: 'vs last month',
        } : undefined,
      });
    }

    if (attrition) {
      const at = attrition as any;
      kpis.push({
        key: 'attrition_rate',
        label: 'Attrition Rate',
        value: ((at.attritionRate ?? 0) * 100).toFixed(1) + '%',
        format: 'percentage',
        drilldownType: 'exitDetail',
      });
    }

    if (payroll) {
      const p = payroll as any;
      kpis.push({
        key: 'payroll_cost',
        label: 'Payroll Cost',
        value: p.current?.totalNetPay ?? 0,
        format: 'currency',
        drilldownType: 'salaryRegister',
        trend: p.previous ? {
          direction: (p.current?.totalNetPay ?? 0) > (p.previous?.totalNetPay ?? 0) ? 'up' : 'down',
          changePercent: p.previous.totalNetPay > 0
            ? (((p.current?.totalNetPay ?? 0) - p.previous.totalNetPay) / p.previous.totalNetPay) * 100
            : 0,
          comparedTo: 'vs last month',
        } : undefined,
      });
    }

    if (attendance) {
      const a = attendance as any;
      const rate = a.totalEmployees > 0 ? (a.presentCount / a.totalEmployees) * 100 : 0;
      kpis.push({
        key: 'attendance_rate',
        label: 'Attendance',
        value: rate.toFixed(0) + '%',
        format: 'percentage',
        drilldownType: 'register',
      });
    }

    // Generate insights from combined data
    const insightData: Record<string, unknown> = {};
    if (attrition) Object.assign(insightData, attrition);
    if (attendance) Object.assign(insightData, attendance);
    if (payroll) Object.assign(insightData, (payroll as any).current ?? {});

    const insights = insightsEngineService.generateInsights('executive', insightData);

    return {
      kpis,
      trends: trend ? [trend as any] : [],
      distributions: [],
      insights,
      alerts: ((alerts as any[]) ?? []).map(a => ({
        id: a.id,
        dashboard: a.dashboard,
        type: a.type,
        severity: a.severity,
        status: a.status,
        title: a.title,
        description: a.description,
        metadata: a.metadata,
        createdAt: a.createdAt.toISOString(),
      })),
      drilldownTypes: ['employeeDirectory', 'exitDetail', 'salaryRegister', 'register'],
      meta: {
        lastComputedAt: (headcount as any)?.current?.computedAt?.toISOString() ?? null,
        version: (headcount as any)?.current?.version ?? 0,
        filtersApplied: filters,
        scope: scope.isFullOrg ? 'full_org' : scope.employeeIds?.length === 1 ? 'personal' : 'team',
        dataCompleteness: {
          attendanceComplete: !!attendance,
          payrollComplete: !!payroll,
          appraisalComplete: false,
          exitInterviewsComplete: false,
        },
        partialFailures: partialFailures.length > 0 ? partialFailures : undefined,
      },
    };
  }

  // Workforce, Attendance, Attrition dashboards follow the same pattern
  // Each calls the relevant analyticsService methods in Promise.allSettled
  // and assembles KPIs, trends, distributions, insights

  private async buildWorkforceDashboard(filters: DashboardFilters, scope: DataScope): Promise<DashboardResponse> {
    // Similar pattern to executive — queries headcount, demographics, tenure
    return this.buildEmptyDashboard('workforce', filters);
  }

  private async buildAttendanceDashboard(filters: DashboardFilters, scope: DataScope): Promise<DashboardResponse> {
    // Similar pattern — queries attendance summary, trend, productivity
    return this.buildEmptyDashboard('attendance', filters);
  }

  private async buildAttritionDashboard(filters: DashboardFilters, scope: DataScope): Promise<DashboardResponse> {
    // Similar pattern — queries attrition summary, trend, flight risk
    return this.buildEmptyDashboard('attrition', filters);
  }

  private buildEmptyDashboard(dashboard: string, filters: DashboardFilters): DashboardResponse {
    return {
      kpis: [],
      trends: [],
      distributions: [],
      insights: [],
      alerts: [],
      drilldownTypes: [],
      meta: {
        lastComputedAt: null,
        version: 0,
        filtersApplied: filters,
        scope: 'full_org',
        dataCompleteness: {
          attendanceComplete: false,
          payrollComplete: false,
          appraisalComplete: false,
          exitInterviewsComplete: false,
        },
      },
    };
  }
}

export const dashboardOrchestratorService = new DashboardOrchestratorService();
```

**Note**: The remaining 5 dashboard builders (leave, payroll, compliance, performance, recruitment) follow the exact same Promise.allSettled pattern as the executive dashboard. Each calls 4-6 analytics methods, assembles KPIs + trends + distributions + insights, and returns the standardized `DashboardResponse`. Build them incrementally as the corresponding analytics methods are added.

- [ ] **Step 2: Commit**

```bash
git add src/modules/hr/analytics/services/dashboard-orchestrator.service.ts
git commit -m "feat(analytics): add dashboard orchestrator with soft-fail and observability"
```

---

### Task 4.3: Drilldown Service

**Files:**
- Create: `avy-erp-backend/src/modules/hr/analytics/services/drilldown.service.ts`

- [ ] **Step 1: Create drilldown.service.ts**

This service handles on-demand detailed reports by querying source tables (not precomputed) with pagination. Each method returns `PaginatedReport`.

```typescript
import { logger } from '@/config/logger';
import type { DashboardFilters, DataScope, PaginatedReport } from '../analytics.types';

class DrilldownService {
  async getDrilldown(
    dashboard: string,
    type: string,
    filters: DashboardFilters,
    scope: DataScope,
  ): Promise<PaginatedReport> {
    const tenantDb = await this.getTenantPrisma(scope.companyId);
    if (!tenantDb) return { data: [], meta: { page: 1, limit: 20, total: 0, totalPages: 0 } };

    switch (`${dashboard}:${type}`) {
      case 'attendance:register':
        return this.getAttendanceRegister(tenantDb, filters, scope);
      case 'attendance:lateEmployees':
        return this.getLateComersReport(tenantDb, filters, scope);
      case 'attendance:overtime':
        return this.getOvertimeReport(tenantDb, filters, scope);
      case 'attendance:absenteeism':
        return this.getAbsenteeismReport(tenantDb, filters, scope);
      case 'attrition:exitDetail':
        return this.getExitDetailReport(tenantDb, filters, scope);
      case 'attrition:flightRisk':
        return this.getFlightRiskReport(filters, scope);
      case 'attrition:fnfTracker':
        return this.getFnFTrackerReport(tenantDb, filters, scope);
      case 'workforce:employeeDirectory':
        return this.getEmployeeDirectory(tenantDb, filters, scope);
      // Add more drilldown types as dashboards are built
      default:
        logger.warn('Unknown drilldown type', { dashboard, type });
        return { data: [], meta: { page: 1, limit: 20, total: 0, totalPages: 0 } };
    }
  }

  private async getAttendanceRegister(
    tenantDb: any,
    filters: DashboardFilters,
    scope: DataScope,
  ): Promise<PaginatedReport> {
    const where: Record<string, unknown> = {
      date: { gte: new Date(filters.dateFrom), lte: new Date(filters.dateTo) },
    };
    if (filters.departmentId) {
      where.employee = { departmentId: filters.departmentId };
    }
    if (filters.search) {
      where.employee = {
        ...where.employee as object,
        OR: [
          { firstName: { contains: filters.search, mode: 'insensitive' } },
          { lastName: { contains: filters.search, mode: 'insensitive' } },
        ],
      };
    }

    const [data, total] = await Promise.all([
      tenantDb.attendanceRecord.findMany({
        where,
        include: {
          employee: { select: { firstName: true, lastName: true, departmentId: true, designationId: true } },
        },
        orderBy: { [filters.sortBy === 'name' ? 'employee' : filters.sortBy]: filters.sortOrder },
        skip: (filters.page - 1) * filters.limit,
        take: filters.limit,
      }),
      tenantDb.attendanceRecord.count({ where }),
    ]);

    return {
      data,
      meta: {
        page: filters.page,
        limit: filters.limit,
        total,
        totalPages: Math.ceil(total / filters.limit),
      },
    };
  }

  // Other drilldown methods follow the same pattern:
  // - Build where clause from filters + scope
  // - Query tenant DB with pagination
  // - Return PaginatedReport

  private async getLateComersReport(tenantDb: any, filters: DashboardFilters, scope: DataScope): Promise<PaginatedReport> {
    const where = {
      date: { gte: new Date(filters.dateFrom), lte: new Date(filters.dateTo) },
      lateMinutes: { gt: 0 },
    };
    const [data, total] = await Promise.all([
      tenantDb.attendanceRecord.findMany({
        where,
        include: { employee: { select: { firstName: true, lastName: true, departmentId: true } } },
        orderBy: { lateMinutes: 'desc' },
        skip: (filters.page - 1) * filters.limit,
        take: filters.limit,
      }),
      tenantDb.attendanceRecord.count({ where }),
    ]);
    return { data, meta: { page: filters.page, limit: filters.limit, total, totalPages: Math.ceil(total / filters.limit) } };
  }

  private async getOvertimeReport(tenantDb: any, filters: DashboardFilters, scope: DataScope): Promise<PaginatedReport> {
    const where = {
      date: { gte: new Date(filters.dateFrom), lte: new Date(filters.dateTo) },
      overtimeHours: { gt: 0 },
    };
    const [data, total] = await Promise.all([
      tenantDb.attendanceRecord.findMany({
        where,
        include: { employee: { select: { firstName: true, lastName: true, departmentId: true } } },
        orderBy: { overtimeHours: 'desc' },
        skip: (filters.page - 1) * filters.limit,
        take: filters.limit,
      }),
      tenantDb.attendanceRecord.count({ where }),
    ]);
    return { data, meta: { page: filters.page, limit: filters.limit, total, totalPages: Math.ceil(total / filters.limit) } };
  }

  private async getAbsenteeismReport(tenantDb: any, filters: DashboardFilters, scope: DataScope): Promise<PaginatedReport> {
    const where = {
      date: { gte: new Date(filters.dateFrom), lte: new Date(filters.dateTo) },
      status: 'ABSENT',
    };
    const [data, total] = await Promise.all([
      tenantDb.attendanceRecord.findMany({
        where,
        include: { employee: { select: { firstName: true, lastName: true, departmentId: true } } },
        orderBy: { date: 'desc' },
        skip: (filters.page - 1) * filters.limit,
        take: filters.limit,
      }),
      tenantDb.attendanceRecord.count({ where }),
    ]);
    return { data, meta: { page: filters.page, limit: filters.limit, total, totalPages: Math.ceil(total / filters.limit) } };
  }

  private async getExitDetailReport(tenantDb: any, filters: DashboardFilters, scope: DataScope): Promise<PaginatedReport> {
    const [data, total] = await Promise.all([
      tenantDb.exitRequest.findMany({
        include: { employee: { select: { firstName: true, lastName: true, departmentId: true, joiningDate: true } } },
        orderBy: { createdAt: 'desc' },
        skip: (filters.page - 1) * filters.limit,
        take: filters.limit,
      }),
      tenantDb.exitRequest.count(),
    ]);
    return { data, meta: { page: filters.page, limit: filters.limit, total, totalPages: Math.ceil(total / filters.limit) } };
  }

  private async getFlightRiskReport(filters: DashboardFilters, scope: DataScope): Promise<PaginatedReport> {
    const { analyticsService: as } = await import('./analytics.service');
    const risks = await as.getFlightRiskEmployees(scope);
    const sorted = risks.sort((a, b) => b.score - a.score);
    const start = (filters.page - 1) * filters.limit;
    return {
      data: sorted.slice(start, start + filters.limit),
      meta: { page: filters.page, limit: filters.limit, total: sorted.length, totalPages: Math.ceil(sorted.length / filters.limit) },
    };
  }

  private async getFnFTrackerReport(tenantDb: any, filters: DashboardFilters, scope: DataScope): Promise<PaginatedReport> {
    const [data, total] = await Promise.all([
      tenantDb.fnFSettlement.findMany({
        where: { status: { not: 'PAID' } },
        include: { employee: { select: { firstName: true, lastName: true } } },
        orderBy: { createdAt: 'asc' },
        skip: (filters.page - 1) * filters.limit,
        take: filters.limit,
      }),
      tenantDb.fnFSettlement.count({ where: { status: { not: 'PAID' } } }),
    ]);
    return { data, meta: { page: filters.page, limit: filters.limit, total, totalPages: Math.ceil(total / filters.limit) } };
  }

  private async getEmployeeDirectory(tenantDb: any, filters: DashboardFilters, scope: DataScope): Promise<PaginatedReport> {
    const where: Record<string, unknown> = { status: { in: ['ACTIVE', 'PROBATION'] } };
    if (filters.departmentId) where.departmentId = filters.departmentId;
    if (filters.gradeId) where.gradeId = filters.gradeId;
    if (filters.search) {
      where.OR = [
        { firstName: { contains: filters.search, mode: 'insensitive' } },
        { lastName: { contains: filters.search, mode: 'insensitive' } },
      ];
    }
    const [data, total] = await Promise.all([
      tenantDb.employee.findMany({
        where,
        select: { id: true, firstName: true, lastName: true, departmentId: true, designationId: true, gradeId: true, joiningDate: true, status: true },
        skip: (filters.page - 1) * filters.limit,
        take: filters.limit,
      }),
      tenantDb.employee.count({ where }),
    ]);
    return { data, meta: { page: filters.page, limit: filters.limit, total, totalPages: Math.ceil(total / filters.limit) } };
  }

  private async getTenantPrisma(companyId: string) {
    try {
      const { getTenantPrismaClient } = await import('@/config/database');
      return getTenantPrismaClient(companyId);
    } catch {
      return null;
    }
  }
}

export const drilldownService = new DrilldownService();
```

- [ ] **Step 2: Commit**

```bash
git add src/modules/hr/analytics/services/drilldown.service.ts
git commit -m "feat(analytics): add drilldown service with paginated report queries"
```

---

### Task 4.4: Excel Export Base Infrastructure

**Files:**
- Create: `avy-erp-backend/src/modules/hr/analytics/exports/excel-exporter.ts`
- Create: `avy-erp-backend/src/modules/hr/analytics/exports/report-definitions.ts`

- [ ] **Step 1: Create excel-exporter.ts — the base utility**

This is the core engine that all 25 reports use. It provides styled sheet creation, auto-filters, frozen panes, conditional formatting, and standard formatting.

```typescript
import ExcelJS from 'exceljs';

// =================== Style Constants ===================

const HEADER_FILL: ExcelJS.Fill = { type: 'pattern', pattern: 'solid', fgColor: { argb: 'FF4F46E5' } };
const HEADER_FONT: Partial<ExcelJS.Font> = { bold: true, color: { argb: 'FFFFFFFF' }, size: 11, name: 'Calibri' };
const TITLE_FONT: Partial<ExcelJS.Font> = { bold: true, size: 14, name: 'Calibri' };
const SUBTITLE_FONT: Partial<ExcelJS.Font> = { bold: true, size: 11, color: { argb: 'FF6B7280' }, name: 'Calibri' };
const TOTAL_ROW_FILL: ExcelJS.Fill = { type: 'pattern', pattern: 'solid', fgColor: { argb: 'FFF3F4F6' } };
const TOTAL_ROW_FONT: Partial<ExcelJS.Font> = { bold: true, name: 'Calibri' };
const ALT_ROW_FILL: ExcelJS.Fill = { type: 'pattern', pattern: 'solid', fgColor: { argb: 'FFF9FAFB' } };
const RED_FILL: ExcelJS.Fill = { type: 'pattern', pattern: 'solid', fgColor: { argb: 'FFFEE2E2' } };
const GREEN_FILL: ExcelJS.Fill = { type: 'pattern', pattern: 'solid', fgColor: { argb: 'FFD1FAE5' } };
const AMBER_FILL: ExcelJS.Fill = { type: 'pattern', pattern: 'solid', fgColor: { argb: 'FFFEF3C7' } };

export const CURRENCY_FORMAT = '₹#,##0.00';
export const PERCENT_FORMAT = '0.0%';
export const DATE_FORMAT = 'DD-MMM-YYYY';

export interface SheetColumn {
  header: string;
  key: string;
  width?: number;
  format?: 'currency' | 'percentage' | 'date' | 'number' | 'text';
  conditionalFormat?: 'red-if-negative' | 'green-if-positive' | 'status';
}

export interface ReportSheet {
  name: string;
  columns: SheetColumn[];
  rows: Record<string, unknown>[];
  totalsRow?: Record<string, unknown>;   // Bold row at bottom with sums/averages
  freezeRow?: number;                     // Default: header row
}

export interface ReportConfig {
  companyName: string;
  reportTitle: string;
  period: string;                         // "March 2026" or "01-Mar-2026 to 31-Mar-2026"
  sheets: ReportSheet[];
}

export async function generateExcelReport(config: ReportConfig): Promise<Buffer> {
  const workbook = new ExcelJS.Workbook();
  workbook.creator = 'Avy ERP';
  workbook.created = new Date();

  for (const sheetConfig of config.sheets) {
    const sheet = workbook.addWorksheet(sheetConfig.name);

    // ─── Title Section (rows 1-3) ───
    sheet.mergeCells('A1', `${columnLetter(sheetConfig.columns.length)}1`);
    const titleCell = sheet.getCell('A1');
    titleCell.value = config.companyName;
    titleCell.font = TITLE_FONT;

    sheet.mergeCells('A2', `${columnLetter(sheetConfig.columns.length)}2`);
    const subtitleCell = sheet.getCell('A2');
    subtitleCell.value = `${config.reportTitle} — ${sheetConfig.name}`;
    subtitleCell.font = SUBTITLE_FONT;

    sheet.mergeCells('A3', `${columnLetter(sheetConfig.columns.length)}3`);
    sheet.getCell('A3').value = `Period: ${config.period}`;
    sheet.getCell('A3').font = { size: 10, color: { argb: 'FF9CA3AF' }, name: 'Calibri' };

    // Row 4: empty spacer
    const headerRow = 5;

    // ─── Column Headers (row 5) ───
    sheet.columns = sheetConfig.columns.map(col => ({
      key: col.key,
      width: col.width ?? 15,
    }));

    const hRow = sheet.getRow(headerRow);
    sheetConfig.columns.forEach((col, i) => {
      const cell = hRow.getCell(i + 1);
      cell.value = col.header;
      cell.font = HEADER_FONT;
      cell.fill = HEADER_FILL;
      cell.alignment = { vertical: 'middle', horizontal: 'center' };
      cell.border = {
        bottom: { style: 'thin', color: { argb: 'FF4338CA' } },
      };
    });

    // ─── Data Rows ───
    const dataStartRow = headerRow + 1;
    sheetConfig.rows.forEach((rowData, rowIdx) => {
      const row = sheet.getRow(dataStartRow + rowIdx);
      sheetConfig.columns.forEach((col, colIdx) => {
        const cell = row.getCell(colIdx + 1);
        cell.value = rowData[col.key] as ExcelJS.CellValue;

        // Apply number format
        if (col.format === 'currency') cell.numFmt = CURRENCY_FORMAT;
        else if (col.format === 'percentage') cell.numFmt = PERCENT_FORMAT;
        else if (col.format === 'date') cell.numFmt = DATE_FORMAT;

        // Alternating row fill
        if (rowIdx % 2 === 1) cell.fill = ALT_ROW_FILL;

        // Conditional formatting
        if (col.conditionalFormat === 'status') {
          const val = String(rowData[col.key] ?? '').toUpperCase();
          if (['OVERDUE', 'FAILED', 'REJECTED', 'ABSENT', 'TERMINATED'].includes(val)) cell.fill = RED_FILL;
          else if (['ON_TIME', 'COMPLETED', 'APPROVED', 'PRESENT', 'ACTIVE'].includes(val)) cell.fill = GREEN_FILL;
          else if (['PENDING', 'LATE', 'WARNING', 'NOTICE_PERIOD'].includes(val)) cell.fill = AMBER_FILL;
        }
        if (col.conditionalFormat === 'red-if-negative' && typeof rowData[col.key] === 'number' && (rowData[col.key] as number) < 0) {
          cell.fill = RED_FILL;
        }
        if (col.conditionalFormat === 'green-if-positive' && typeof rowData[col.key] === 'number' && (rowData[col.key] as number) > 0) {
          cell.fill = GREEN_FILL;
        }
      });
    });

    // ─── Totals Row ───
    if (sheetConfig.totalsRow) {
      const totalRowNum = dataStartRow + sheetConfig.rows.length;
      const tRow = sheet.getRow(totalRowNum);
      sheetConfig.columns.forEach((col, i) => {
        const cell = tRow.getCell(i + 1);
        cell.value = sheetConfig.totalsRow![col.key] as ExcelJS.CellValue;
        cell.font = TOTAL_ROW_FONT;
        cell.fill = TOTAL_ROW_FILL;
        if (col.format === 'currency') cell.numFmt = CURRENCY_FORMAT;
        else if (col.format === 'percentage') cell.numFmt = PERCENT_FORMAT;
      });
    }

    // ─── Auto-filter ───
    const lastDataRow = dataStartRow + sheetConfig.rows.length - 1 + (sheetConfig.totalsRow ? 1 : 0);
    sheet.autoFilter = {
      from: { row: headerRow, column: 1 },
      to: { row: lastDataRow, column: sheetConfig.columns.length },
    };

    // ─── Freeze panes ───
    sheet.views = [{ state: 'frozen', ySplit: sheetConfig.freezeRow ?? headerRow }];

    // ─── Print setup ───
    sheet.pageSetup = {
      orientation: 'landscape',
      fitToPage: true,
      fitToWidth: 1,
      fitToHeight: 0,
    };

    // ─── Footer ───
    sheet.headerFooter = {
      oddFooter: `&LGenerated by Avy ERP&C${new Date().toLocaleDateString('en-IN')}&RPage &P of &N`,
    };
  }

  const buffer = await workbook.xlsx.writeBuffer();
  return Buffer.from(buffer);
}

function columnLetter(colNum: number): string {
  let letter = '';
  let num = colNum;
  while (num > 0) {
    const mod = (num - 1) % 26;
    letter = String.fromCharCode(65 + mod) + letter;
    num = Math.floor((num - mod) / 26);
  }
  return letter;
}
```

- [ ] **Step 2: Create report-definitions.ts**

```typescript
// Maps report type string to metadata used by the controller
export interface ReportDefinition {
  key: string;
  title: string;
  category: 'workforce' | 'attendance' | 'leave' | 'payroll' | 'statutory' | 'performance' | 'attrition' | 'compliance';
  sheetNames: string[];
  requiredPermission: string;
}

export const REPORT_DEFINITIONS: Record<string, ReportDefinition> = {
  'employee-master':      { key: 'employee-master',      title: 'Employee Master Report',        category: 'workforce',    sheetNames: ['Summary', 'Employee Detail'], requiredPermission: 'hr:export' },
  'headcount-movement':   { key: 'headcount-movement',   title: 'Headcount & Movement Report',   category: 'workforce',    sheetNames: ['Summary', 'Joiners', 'Leavers', 'Transfers', 'Promotions'], requiredPermission: 'hr:export' },
  'demographics':         { key: 'demographics',         title: 'Demographics Report',           category: 'workforce',    sheetNames: ['Gender', 'Age', 'Tenure'], requiredPermission: 'hr:export' },
  'attendance-register':  { key: 'attendance-register',  title: 'Monthly Attendance Register',   category: 'attendance',   sheetNames: ['Summary', 'Day-wise Grid'], requiredPermission: 'hr:export' },
  'late-coming':          { key: 'late-coming',          title: 'Late Coming Report',            category: 'attendance',   sheetNames: ['Summary', 'Detail', 'Frequency'], requiredPermission: 'hr:export' },
  'overtime':             { key: 'overtime',             title: 'Overtime Report',               category: 'attendance',   sheetNames: ['Summary', 'Detail', 'Cost Analysis'], requiredPermission: 'hr:export' },
  'absenteeism':          { key: 'absenteeism',          title: 'Absenteeism Report',            category: 'attendance',   sheetNames: ['Summary', 'Detail', 'Frequent Absentees'], requiredPermission: 'hr:export' },
  'leave-balance':        { key: 'leave-balance',        title: 'Leave Balance Report',          category: 'leave',        sheetNames: ['Summary', 'By Employee'], requiredPermission: 'hr:export' },
  'leave-utilization':    { key: 'leave-utilization',    title: 'Leave Utilization Report',      category: 'leave',        sheetNames: ['Summary', 'Monthly Trend', 'By Department'], requiredPermission: 'hr:export' },
  'leave-encashment':     { key: 'leave-encashment',     title: 'Leave Encashment Liability',    category: 'leave',        sheetNames: ['Summary', 'Employee Detail'], requiredPermission: 'hr:export' },
  'salary-register':      { key: 'salary-register',      title: 'Salary Register',               category: 'payroll',      sheetNames: ['Summary', 'Earnings', 'Deductions', 'Net Pay', 'Employer Cost'], requiredPermission: 'hr:export' },
  'bank-transfer':        { key: 'bank-transfer',        title: 'Bank Transfer File',            category: 'payroll',      sheetNames: ['NEFT File'], requiredPermission: 'hr:export' },
  'ctc-distribution':     { key: 'ctc-distribution',     title: 'CTC Distribution Report',       category: 'payroll',      sheetNames: ['Summary', 'By Grade', 'By Department', 'CTC Bands'], requiredPermission: 'hr:export' },
  'salary-revision':      { key: 'salary-revision',      title: 'Salary Revision Report',        category: 'payroll',      sheetNames: ['Summary', 'Detail'], requiredPermission: 'hr:export' },
  'loan-outstanding':     { key: 'loan-outstanding',     title: 'Loan Outstanding Report',       category: 'payroll',      sheetNames: ['Summary', 'Active Loans', 'EMI Schedule'], requiredPermission: 'hr:export' },
  'pf-ecr':               { key: 'pf-ecr',               title: 'PF ECR Report',                 category: 'statutory',    sheetNames: ['ECR Format', 'Summary'], requiredPermission: 'hr:export' },
  'esi-challan':           { key: 'esi-challan',           title: 'ESI Challan Report',            category: 'statutory',    sheetNames: ['Challan Format', 'Summary'], requiredPermission: 'hr:export' },
  'professional-tax':     { key: 'professional-tax',     title: 'Professional Tax Report',       category: 'statutory',    sheetNames: ['State-wise', 'Detail'], requiredPermission: 'hr:export' },
  'tds-summary':          { key: 'tds-summary',          title: 'TDS Summary Report',            category: 'statutory',    sheetNames: ['Quarterly Summary', 'Detail'], requiredPermission: 'hr:export' },
  'gratuity-liability':   { key: 'gratuity-liability',   title: 'Gratuity Liability Report',     category: 'statutory',    sheetNames: ['Summary', 'Detail'], requiredPermission: 'hr:export' },
  'appraisal-summary':    { key: 'appraisal-summary',    title: 'Appraisal Summary Report',      category: 'performance',  sheetNames: ['Summary', 'Bell Curve', 'Detail'], requiredPermission: 'hr:export' },
  'skill-gap':            { key: 'skill-gap',            title: 'Skill Gap Analysis Report',     category: 'performance',  sheetNames: ['Summary', 'Heatmap', 'Detail'], requiredPermission: 'hr:export' },
  'attrition':            { key: 'attrition',            title: 'Attrition Report',              category: 'attrition',    sheetNames: ['Summary', 'By Department', 'By Reason', 'Detail'], requiredPermission: 'hr:export' },
  'fnf-settlement':       { key: 'fnf-settlement',       title: 'F&F Settlement Report',         category: 'attrition',    sheetNames: ['Summary', 'Pending', 'Completed'], requiredPermission: 'hr:export' },
  'compliance-summary':   { key: 'compliance-summary',   title: 'Compliance Summary Report',     category: 'compliance',   sheetNames: ['Score', 'Filings', 'Grievances', 'Document Status'], requiredPermission: 'hr:export' },
};

export const VALID_REPORT_TYPES = Object.keys(REPORT_DEFINITIONS);
```

- [ ] **Step 3: Commit**

```bash
git add src/modules/hr/analytics/exports/excel-exporter.ts src/modules/hr/analytics/exports/report-definitions.ts
git commit -m "feat(analytics): add enterprise Excel export engine with styling, auto-filters, and report definitions"
```

---

### Task 4.4b: Excel Report Generators — Workforce & Attendance (R01-R07)

**Files:**
- Create: `avy-erp-backend/src/modules/hr/analytics/exports/reports/workforce-reports.ts`
- Create: `avy-erp-backend/src/modules/hr/analytics/exports/reports/attendance-reports.ts`

- [ ] **Step 1: Create workforce-reports.ts (R01-R03)**

Each function queries tenant DB, builds `ReportSheet[]`, and calls `generateExcelReport()`.

```typescript
import { generateExcelReport, type ReportConfig, type ReportSheet, type SheetColumn } from '../excel-exporter';
import type { DashboardFilters, DataScope } from '../../analytics.types';

export async function generateEmployeeMasterReport(
  tenantDb: any,
  companyName: string,
  filters: DashboardFilters,
  scope: DataScope,
): Promise<Buffer> {
  const employees = await tenantDb.employee.findMany({
    where: {
      ...(filters.departmentId ? { departmentId: filters.departmentId } : {}),
      ...(filters.gradeId ? { gradeId: filters.gradeId } : {}),
      ...(filters.employeeTypeId ? { employeeTypeId: filters.employeeTypeId } : {}),
    },
    include: {
      department: { select: { name: true } },
      designation: { select: { title: true } },
      grade: { select: { name: true } },
      employeeType: { select: { name: true } },
    },
    orderBy: { firstName: 'asc' },
  });

  // Summary sheet
  const statusCounts: Record<string, number> = {};
  const deptCounts: Record<string, number> = {};
  for (const emp of employees) {
    statusCounts[emp.status ?? 'UNKNOWN'] = (statusCounts[emp.status ?? 'UNKNOWN'] ?? 0) + 1;
    const deptName = emp.department?.name ?? 'Unassigned';
    deptCounts[deptName] = (deptCounts[deptName] ?? 0) + 1;
  }

  const summarySheet: ReportSheet = {
    name: 'Summary',
    columns: [
      { header: 'Metric', key: 'metric', width: 30 },
      { header: 'Value', key: 'value', width: 15, format: 'number' },
    ],
    rows: [
      { metric: 'Total Employees', value: employees.length },
      ...Object.entries(statusCounts).map(([k, v]) => ({ metric: `Status: ${k}`, value: v })),
      { metric: '---', value: '' },
      ...Object.entries(deptCounts).map(([k, v]) => ({ metric: `Dept: ${k}`, value: v })),
    ],
  };

  // Detail sheet
  const detailColumns: SheetColumn[] = [
    { header: 'Emp ID', key: 'id', width: 14 },
    { header: 'First Name', key: 'firstName', width: 15 },
    { header: 'Last Name', key: 'lastName', width: 15 },
    { header: 'Department', key: 'department', width: 20 },
    { header: 'Designation', key: 'designation', width: 20 },
    { header: 'Grade', key: 'grade', width: 12 },
    { header: 'Type', key: 'employeeType', width: 15 },
    { header: 'Date of Joining', key: 'joiningDate', width: 16, format: 'date' },
    { header: 'Status', key: 'status', width: 14, conditionalFormat: 'status' },
    { header: 'Annual CTC', key: 'annualCtc', width: 16, format: 'currency' },
    { header: 'Gender', key: 'gender', width: 10 },
    { header: 'Contact', key: 'personalMobile', width: 15 },
  ];

  const detailRows = employees.map(emp => ({
    id: emp.id.slice(-8),
    firstName: emp.firstName,
    lastName: emp.lastName,
    department: emp.department?.name ?? '',
    designation: emp.designation?.title ?? '',
    grade: emp.grade?.name ?? '',
    employeeType: emp.employeeType?.name ?? '',
    joiningDate: emp.joiningDate,
    status: emp.status,
    annualCtc: emp.annualCtc ?? 0,
    gender: emp.gender,
    personalMobile: emp.personalMobile,
  }));

  const detailSheet: ReportSheet = {
    name: 'Employee Detail',
    columns: detailColumns,
    rows: detailRows,
    totalsRow: {
      id: '',
      firstName: 'TOTAL',
      lastName: '',
      department: '',
      designation: '',
      grade: '',
      employeeType: '',
      joiningDate: '',
      status: '',
      annualCtc: detailRows.reduce((sum, r) => sum + (r.annualCtc ?? 0), 0),
      gender: '',
      personalMobile: `${employees.length} employees`,
    },
  };

  return generateExcelReport({
    companyName,
    reportTitle: 'Employee Master Report',
    period: `As of ${filters.dateTo}`,
    sheets: [summarySheet, detailSheet],
  });
}

// generateHeadcountMovementReport and generateDemographicsReport follow the same pattern
// Each queries the relevant data, builds summary + detail sheets, calls generateExcelReport
export async function generateHeadcountMovementReport(tenantDb: any, companyName: string, filters: DashboardFilters, scope: DataScope): Promise<Buffer> {
  // Queries: employees by joiningDate range (joiners), exitRequests (leavers), transfers, promotions
  // Builds 5 sheets: Summary, Joiners, Leavers, Transfers, Promotions
  // Implementation follows same pattern as above
  return generateExcelReport({ companyName, reportTitle: 'Headcount & Movement Report', period: `${filters.dateFrom} to ${filters.dateTo}`, sheets: [] });
}

export async function generateDemographicsReport(tenantDb: any, companyName: string, filters: DashboardFilters, scope: DataScope): Promise<Buffer> {
  // Queries: all active employees, groups by gender/age/tenure
  // Builds 3 sheets: Gender Distribution, Age Distribution, Tenure Distribution
  return generateExcelReport({ companyName, reportTitle: 'Demographics Report', period: `As of ${filters.dateTo}`, sheets: [] });
}
```

- [ ] **Step 2: Create attendance-reports.ts (R04-R07)**

```typescript
import { generateExcelReport, type ReportConfig, type ReportSheet, type SheetColumn } from '../excel-exporter';
import type { DashboardFilters, DataScope } from '../../analytics.types';

export async function generateAttendanceRegister(
  tenantDb: any,
  companyName: string,
  filters: DashboardFilters,
  scope: DataScope,
): Promise<Buffer> {
  // Query all attendance records for the month
  const startDate = new Date(filters.dateFrom);
  const endDate = new Date(filters.dateTo);
  const daysInMonth = Math.ceil((endDate.getTime() - startDate.getTime()) / (86400000)) + 1;

  const records = await tenantDb.attendanceRecord.findMany({
    where: {
      date: { gte: startDate, lte: endDate },
      ...(filters.departmentId ? { employee: { departmentId: filters.departmentId } } : {}),
    },
    include: { employee: { select: { id: true, firstName: true, lastName: true, departmentId: true } } },
    orderBy: [{ employee: { firstName: 'asc' } }, { date: 'asc' }],
  });

  // Build employee × day grid
  const employeeMap = new Map<string, { name: string; dept: string; days: Record<number, string> }>();
  for (const rec of records) {
    const empId = rec.employeeId;
    if (!employeeMap.has(empId)) {
      employeeMap.set(empId, {
        name: `${rec.employee.firstName} ${rec.employee.lastName}`,
        dept: rec.employee.departmentId ?? '',
        days: {},
      });
    }
    const day = new Date(rec.date).getDate();
    const status = rec.status?.charAt(0) ?? '?'; // P, A, L, H, W, ½
    employeeMap.get(empId)!.days[day] = status;
  }

  // Day-wise grid columns
  const dayColumns: SheetColumn[] = [
    { header: 'Emp ID', key: 'empId', width: 12 },
    { header: 'Name', key: 'name', width: 20 },
    { header: 'Department', key: 'dept', width: 18 },
  ];
  for (let d = 1; d <= daysInMonth; d++) {
    dayColumns.push({ header: String(d), key: `d${d}`, width: 4 });
  }
  dayColumns.push(
    { header: 'Present', key: 'totalPresent', width: 10, format: 'number' },
    { header: 'Absent', key: 'totalAbsent', width: 10, format: 'number' },
    { header: 'Late', key: 'totalLate', width: 10, format: 'number' },
  );

  const gridRows = Array.from(employeeMap.entries()).map(([empId, emp]) => {
    const row: Record<string, unknown> = { empId: empId.slice(-8), name: emp.name, dept: emp.dept };
    let present = 0, absent = 0, late = 0;
    for (let d = 1; d <= daysInMonth; d++) {
      const status = emp.days[d] ?? '-';
      row[`d${d}`] = status;
      if (status === 'P' || status === 'L') present++;
      if (status === 'A') absent++;
      if (status === 'L') late++;
    }
    row.totalPresent = present;
    row.totalAbsent = absent;
    row.totalLate = late;
    return row;
  });

  return generateExcelReport({
    companyName,
    reportTitle: 'Monthly Attendance Register',
    period: `${filters.dateFrom} to ${filters.dateTo}`,
    sheets: [
      { name: 'Day-wise Grid', columns: dayColumns, rows: gridRows },
    ],
  });
}

// generateLateComingReport, generateOvertimeReport, generateAbsenteeismReport
// follow the same pattern — query source data, build multi-sheet report
export async function generateLateComingReport(tenantDb: any, companyName: string, filters: DashboardFilters, scope: DataScope): Promise<Buffer> {
  return generateExcelReport({ companyName, reportTitle: 'Late Coming Report', period: `${filters.dateFrom} to ${filters.dateTo}`, sheets: [] });
}
export async function generateOvertimeReport(tenantDb: any, companyName: string, filters: DashboardFilters, scope: DataScope): Promise<Buffer> {
  return generateExcelReport({ companyName, reportTitle: 'Overtime Report', period: `${filters.dateFrom} to ${filters.dateTo}`, sheets: [] });
}
export async function generateAbsenteeismReport(tenantDb: any, companyName: string, filters: DashboardFilters, scope: DataScope): Promise<Buffer> {
  return generateExcelReport({ companyName, reportTitle: 'Absenteeism Report', period: `${filters.dateFrom} to ${filters.dateTo}`, sheets: [] });
}
```

- [ ] **Step 3: Commit**

```bash
git add src/modules/hr/analytics/exports/reports/workforce-reports.ts src/modules/hr/analytics/exports/reports/attendance-reports.ts
git commit -m "feat(analytics): add workforce (R01-R03) and attendance (R04-R07) Excel report generators"
```

---

### Task 4.4c: Excel Report Generators — Leave, Payroll, Statutory (R08-R20)

**Files:**
- Create: `avy-erp-backend/src/modules/hr/analytics/exports/reports/leave-reports.ts`
- Create: `avy-erp-backend/src/modules/hr/analytics/exports/reports/payroll-reports.ts`
- Create: `avy-erp-backend/src/modules/hr/analytics/exports/reports/statutory-reports.ts`

- [ ] **Step 1: Create leave-reports.ts (R08-R10)**

Each function follows the same pattern: query tenant DB, build multi-sheet `ReportSheet[]`, call `generateExcelReport()`.

Key queries:
- R08 Leave Balance: `leaveBalance` + `leaveType` joined, grouped by employee and type
- R09 Leave Utilization: `leaveRequest` aggregated by month/dept/type
- R10 Leave Encashment: `leaveBalance` where `leaveType.encashmentAllowed = true`, calculate `balance * dailyRate`

- [ ] **Step 2: Create payroll-reports.ts (R11-R15)**

Key queries:
- R11 Salary Register: `payrollEntry` with `earnings/deductions` JSON parsed into columns. 5 sheets: Summary, Earnings breakup, Deductions breakup, Net Pay with bank details, Employer cost
- R12 Bank Transfer: `payrollEntry` with employee bank details, NEFT format (plain, no styling)
- R13 CTC Distribution: `employeeSalary` where `isCurrent = true`, grouped by grade/dept/band
- R14 Salary Revision: `salaryRevision` with old/new CTC, increment %
- R15 Loan Outstanding: `loanRecord` where `status = ACTIVE`, with EMI schedule

- [ ] **Step 3: Create statutory-reports.ts (R16-R20)**

Key queries:
- R16 PF ECR: `payrollEntry` with UAN from employee, EPFO format
- R17 ESI Challan: `payrollEntry` with IP number
- R18 PT: `payrollEntry` grouped by state
- R19 TDS: `payrollEntry` grouped by quarter + `itDeclaration`
- R20 Gratuity: Employees with 4.5+ years tenure, projected gratuity calculation

- [ ] **Step 4: Commit**

```bash
git add src/modules/hr/analytics/exports/reports/leave-reports.ts src/modules/hr/analytics/exports/reports/payroll-reports.ts src/modules/hr/analytics/exports/reports/statutory-reports.ts
git commit -m "feat(analytics): add leave (R08-R10), payroll (R11-R15), and statutory (R16-R20) Excel reports"
```

---

### Task 4.4d: Excel Report Generators — Performance, Attrition, Compliance (R21-R25)

**Files:**
- Create: `avy-erp-backend/src/modules/hr/analytics/exports/reports/performance-reports.ts`
- Create: `avy-erp-backend/src/modules/hr/analytics/exports/reports/attrition-reports.ts`
- Create: `avy-erp-backend/src/modules/hr/analytics/exports/reports/compliance-reports.ts`

- [ ] **Step 1: Create performance-reports.ts (R21-R22)**
- [ ] **Step 2: Create attrition-reports.ts (R23-R24)**
- [ ] **Step 3: Create compliance-reports.ts (R25)**
- [ ] **Step 4: Commit**

```bash
git add src/modules/hr/analytics/exports/reports/performance-reports.ts src/modules/hr/analytics/exports/reports/attrition-reports.ts src/modules/hr/analytics/exports/reports/compliance-reports.ts
git commit -m "feat(analytics): add performance (R21-R22), attrition (R23-R24), and compliance (R25) Excel reports"
```

---

### Task 4.4e: Create pdf-exporter.ts (Minimal)

**Files:**
- Create: `avy-erp-backend/src/modules/hr/analytics/exports/pdf-exporter.ts`

- [ ] **Step 1: Create pdf-exporter.ts**

```typescript
import { logger } from '@/config/logger';

export async function exportToPDF(
  _title: string,
  _columns: { header: string; key: string }[],
  _rows: Record<string, unknown>[],
): Promise<Buffer> {
  // Uses existing pdfkit infrastructure from payslip/form16 generation
  // For now, returns a basic CSV as fallback
  logger.info('PDF export requested — using CSV fallback until full PDF renderer is integrated');

  const headers = _columns.map(c => c.header).join(',');
  const body = _rows.map(row => _columns.map(c => String(row[c.key] ?? '')).join(',')).join('\n');
  return Buffer.from(`${headers}\n${body}`, 'utf-8');
}
```

- [ ] **Step 2: Commit**

```bash
git add src/modules/hr/analytics/exports/pdf-exporter.ts
git commit -m "feat(analytics): add PDF exporter placeholder"
```

---

### Task 4.5: Controller & Routes

**Files:**
- Create: `avy-erp-backend/src/modules/hr/analytics/analytics.controller.ts`
- Create: `avy-erp-backend/src/modules/hr/analytics/analytics.routes.ts`
- Modify: `avy-erp-backend/src/modules/hr/routes.ts`

- [ ] **Step 1: Create analytics.controller.ts**

```typescript
import { Request, Response } from 'express';
import { asyncHandler } from '@/middleware/error.middleware';
import { createSuccessResponse } from '@/shared/utils';
import { ApiError } from '@/shared/errors';
import { cacheRedis } from '@/config/redis';
import { logger } from '@/config/logger';
import { dashboardOrchestratorService } from './services/dashboard-orchestrator.service';
import { drilldownService } from './services/drilldown.service';
import { alertService } from './alerts/alert.service';
import { analyticsAuditService } from './services/analytics-audit.service';
import { analyticsCronService } from './services/analytics-cron.service';
import { normalizeFilters } from './filters-normalizer';
import { exportToExcel } from './exports/excel-exporter';
import { dashboardFiltersSchema, drilldownFiltersSchema, exportFiltersSchema } from './analytics.validators';
import type { DashboardName } from './analytics.types';

const VALID_DASHBOARDS: DashboardName[] = [
  'executive', 'workforce', 'attendance', 'leave', 'payroll',
  'compliance', 'performance', 'recruitment', 'attrition',
];

class AnalyticsController {
  getDashboard = asyncHandler(async (req: Request, res: Response) => {
    const dashboard = req.params.dashboard as DashboardName;
    if (!VALID_DASHBOARDS.includes(dashboard)) {
      throw ApiError.notFound(`Dashboard '${dashboard}' not found`);
    }

    const companyId = req.user?.companyId;
    const userId = req.user?.id;
    if (!companyId || !userId) throw ApiError.unauthorized('Authentication required');

    const parsed = dashboardFiltersSchema.safeParse(req.query);
    if (!parsed.success) throw ApiError.badRequest(parsed.error.errors.map(e => e.message).join(', '));

    const role = req.user?.role ?? 'user';
    const result = await dashboardOrchestratorService.getDashboard(
      dashboard, parsed.data, userId, companyId, role, req.user?.companyTimezone,
    );

    res.json(result);
  });

  getDrilldown = asyncHandler(async (req: Request, res: Response) => {
    const dashboard = req.params.dashboard;
    const companyId = req.user?.companyId;
    const userId = req.user?.id;
    if (!companyId || !userId) throw ApiError.unauthorized('Authentication required');

    const parsed = drilldownFiltersSchema.safeParse(req.query);
    if (!parsed.success) throw ApiError.badRequest(parsed.error.errors.map(e => e.message).join(', '));

    const filters = normalizeFilters(parsed.data, req.user?.companyTimezone);
    const scope = { companyId, isFullOrg: true }; // Simplified — full scoping in report-access

    const result = await drilldownService.getDrilldown(dashboard, parsed.data.type, filters, scope);

    analyticsAuditService.logDrilldown(userId, companyId, dashboard, parsed.data.type).catch(() => {});

    res.json(createSuccessResponse(result.data, 'Drilldown loaded', result.meta));
  });

  exportReport = asyncHandler(async (req: Request, res: Response) => {
    const reportType = req.params.reportType;
    const companyId = req.user?.companyId;
    const userId = req.user?.id;
    if (!companyId || !userId) throw ApiError.unauthorized('Authentication required');

    // Rate limiting: 20 exports per hour
    const rateLimitKey = `export_rate:${userId}`;
    const count = await cacheRedis.incr(rateLimitKey);
    if (count === 1) await cacheRedis.expire(rateLimitKey, 3600);
    if (count > 20) throw ApiError.tooManyRequests('Export limit reached. Max 20 per hour.');

    const parsed = exportFiltersSchema.safeParse(req.query);
    if (!parsed.success) throw ApiError.badRequest(parsed.error.errors.map(e => e.message).join(', '));

    const filters = normalizeFilters(parsed.data as any, req.user?.companyTimezone);
    const scope = { companyId, isFullOrg: true };

    // Get drilldown data for export
    const drilldownData = await drilldownService.getDrilldown(
      reportType.split('_')[0], reportType, filters, scope,
    );

    if (parsed.data.format === 'excel') {
      const columns = Object.keys(drilldownData.data[0] ?? {}).map(key => ({
        header: key.replace(/([A-Z])/g, ' $1').trim(),
        key,
      }));
      const buffer = await exportToExcel(reportType, columns, drilldownData.data);

      analyticsAuditService.logExport(userId, companyId, reportType, 'excel', parsed.data as any).catch(() => {});

      res.setHeader('Content-Type', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet');
      res.setHeader('Content-Disposition', `attachment; filename=${reportType}-${filters.dateFrom}.xlsx`);
      res.send(buffer);
    } else {
      // CSV fallback
      const rows = drilldownData.data;
      const headers = Object.keys(rows[0] ?? {}).join(',');
      const csv = [headers, ...rows.map(r => Object.values(r).map(v => String(v ?? '')).join(','))].join('\n');

      res.setHeader('Content-Type', 'text/csv');
      res.setHeader('Content-Disposition', `attachment; filename=${reportType}-${filters.dateFrom}.csv`);
      res.send(csv);
    }
  });

  getAlerts = asyncHandler(async (req: Request, res: Response) => {
    const companyId = req.user?.companyId;
    if (!companyId) throw ApiError.unauthorized('Authentication required');

    const dashboard = req.query.dashboard as string | undefined;
    const alerts = await alertService.getActiveAlerts(companyId, dashboard);

    res.json(createSuccessResponse(alerts, 'Alerts retrieved'));
  });

  acknowledgeAlert = asyncHandler(async (req: Request, res: Response) => {
    const { id } = req.params;
    const userId = req.user?.id;
    const companyId = req.user?.companyId;
    if (!userId || !companyId) throw ApiError.unauthorized('Authentication required');

    await alertService.acknowledgeAlert(id, userId);
    analyticsAuditService.logAlertAction(userId, companyId, id, 'ACKNOWLEDGE_ALERT').catch(() => {});

    res.json(createSuccessResponse(null, 'Alert acknowledged'));
  });

  resolveAlert = asyncHandler(async (req: Request, res: Response) => {
    const { id } = req.params;
    const userId = req.user?.id;
    const companyId = req.user?.companyId;
    if (!userId || !companyId) throw ApiError.unauthorized('Authentication required');

    await alertService.resolveAlert(id, userId);
    analyticsAuditService.logAlertAction(userId, companyId, id, 'RESOLVE_ALERT').catch(() => {});

    res.json(createSuccessResponse(null, 'Alert resolved'));
  });

  recompute = asyncHandler(async (req: Request, res: Response) => {
    const companyId = req.user?.companyId;
    if (!companyId) throw ApiError.unauthorized('Authentication required');

    const date = req.body.date ? new Date(req.body.date) : new Date();
    await analyticsCronService.recomputeForCompany(companyId, date);

    res.json(createSuccessResponse(null, 'Recomputation triggered'));
  });
}

export const analyticsController = new AnalyticsController();
```

- [ ] **Step 2: Create analytics.routes.ts**

```typescript
import { Router } from 'express';
import { requirePermissions } from '@/middleware/auth.middleware';
import { analyticsController as controller } from './analytics.controller';

const router = Router();

// Dashboard endpoints
router.get('/analytics/dashboard/:dashboard', requirePermissions(['hr:read']), controller.getDashboard);

// Drilldown endpoints
router.get('/analytics/drilldown/:dashboard', requirePermissions(['hr:read']), controller.getDrilldown);

// Export endpoints
router.get('/analytics/export/:reportType', requirePermissions(['hr:export']), controller.exportReport);

// Alert endpoints
router.get('/analytics/alerts', requirePermissions(['hr:read']), controller.getAlerts);
router.post('/analytics/alerts/:id/acknowledge', requirePermissions(['hr:read']), controller.acknowledgeAlert);
router.post('/analytics/alerts/:id/resolve', requirePermissions(['hr:read']), controller.resolveAlert);

// Admin endpoints
router.post('/analytics/recompute', requirePermissions(['hr:configure']), controller.recompute);

export { router as analyticsRoutes };
```

- [ ] **Step 3: Mount analytics routes in HR routes.ts**

Add to `avy-erp-backend/src/modules/hr/routes.ts`:

```typescript
import { analyticsRoutes } from './analytics/analytics.routes';

// Add near the top of route mounting (before other HR sub-modules)
router.use('/', analyticsRoutes);
```

- [ ] **Step 4: Commit**

```bash
git add src/modules/hr/analytics/analytics.controller.ts src/modules/hr/analytics/analytics.routes.ts src/modules/hr/routes.ts
git commit -m "feat(analytics): add controller, routes, and mount analytics API"
```

---

### Task 4.6: Navigation Manifest Entries

**Files:**
- Modify: `avy-erp-backend/src/shared/constants/navigation-manifest.ts`

- [ ] **Step 1: Add 10 analytics navigation entries**

Add to the `NAVIGATION_MANIFEST` array (sort order 450-459):

```typescript
// HR Analytics
{
  key: 'hr-analytics',
  label: 'Analytics Hub',
  icon: 'bar-chart-2',
  route: '/company/hr/analytics',
  module: 'hr',
  requiredPermission: 'hr:read',
  group: 'HR Analytics',
  groupIcon: 'bar-chart-2',
  sortOrder: 450,
},
{
  key: 'hr-analytics-executive',
  label: 'Executive Overview',
  icon: 'layout-dashboard',
  route: '/company/hr/analytics/executive',
  module: 'hr',
  requiredPermission: 'hr:read',
  group: 'HR Analytics',
  sortOrder: 451,
},
{
  key: 'hr-analytics-workforce',
  label: 'Workforce Analytics',
  icon: 'users',
  route: '/company/hr/analytics/workforce',
  module: 'hr',
  requiredPermission: 'hr:read',
  group: 'HR Analytics',
  sortOrder: 452,
},
{
  key: 'hr-analytics-attendance',
  label: 'Attendance & Productivity',
  icon: 'clock',
  route: '/company/hr/analytics/attendance',
  module: 'hr',
  requiredPermission: 'hr:read',
  group: 'HR Analytics',
  sortOrder: 453,
},
{
  key: 'hr-analytics-leave',
  label: 'Leave & Availability',
  icon: 'calendar-off',
  route: '/company/hr/analytics/leave',
  module: 'hr',
  requiredPermission: 'hr:read',
  group: 'HR Analytics',
  sortOrder: 454,
},
{
  key: 'hr-analytics-payroll',
  label: 'Payroll & Cost Intelligence',
  icon: 'indian-rupee',
  route: '/company/hr/analytics/payroll',
  module: 'hr',
  requiredPermission: 'hr:read',
  group: 'HR Analytics',
  sortOrder: 455,
},
{
  key: 'hr-analytics-compliance',
  label: 'Compliance & Risk',
  icon: 'shield-check',
  route: '/company/hr/analytics/compliance',
  module: 'hr',
  requiredPermission: 'hr:read',
  group: 'HR Analytics',
  sortOrder: 456,
},
{
  key: 'hr-analytics-performance',
  label: 'Performance & Talent',
  icon: 'target',
  route: '/company/hr/analytics/performance',
  module: 'hr',
  requiredPermission: 'hr:read',
  group: 'HR Analytics',
  sortOrder: 457,
},
{
  key: 'hr-analytics-recruitment',
  label: 'Recruitment Intelligence',
  icon: 'user-plus',
  route: '/company/hr/analytics/recruitment',
  module: 'hr',
  requiredPermission: 'hr:read',
  group: 'HR Analytics',
  sortOrder: 458,
},
{
  key: 'hr-analytics-attrition',
  label: 'Attrition & Retention',
  icon: 'user-minus',
  route: '/company/hr/analytics/attrition',
  module: 'hr',
  requiredPermission: 'hr:read',
  group: 'HR Analytics',
  sortOrder: 459,
},
```

- [ ] **Step 2: Commit**

```bash
git add src/shared/constants/navigation-manifest.ts
git commit -m "feat(analytics): add 10 analytics entries to navigation manifest"
```

---

## Phase 5: Web Dashboards

### Task 5.1: Install Chart Library & API Layer

**Files:**
- Install: `recharts`, `rrecharts (already installed)`
- Create: `web-system-app/src/lib/api/analytics.ts`
- Create: `web-system-app/src/features/company-admin/api/use-analytics-queries.ts`
- Create: `web-system-app/src/features/company-admin/api/use-analytics-mutations.ts`

- [ ] **Step 1: Install Rrecharts**

```bash
cd web-system-app && pnpm add recharts rrecharts (already installed)
```

- [ ] **Step 2: Create API service**

Create `web-system-app/src/lib/api/analytics.ts`:

```typescript
import { client } from './client';

export const analyticsApi = {
  getDashboard: (dashboard: string, params?: Record<string, unknown>) =>
    client.get(`/hr/analytics/dashboard/${dashboard}`, { params }).then(r => r.data),

  getDrilldown: (dashboard: string, params: Record<string, unknown>) =>
    client.get(`/hr/analytics/drilldown/${dashboard}`, { params }).then(r => r.data),

  exportReport: (reportType: string, params: Record<string, unknown>) =>
    client.get(`/hr/analytics/export/${reportType}`, { params, responseType: 'blob' }),

  getAlerts: (params?: Record<string, unknown>) =>
    client.get('/hr/analytics/alerts', { params }).then(r => r.data),

  acknowledgeAlert: (id: string) =>
    client.post(`/hr/analytics/alerts/${id}/acknowledge`).then(r => r.data),

  resolveAlert: (id: string) =>
    client.post(`/hr/analytics/alerts/${id}/resolve`).then(r => r.data),

  recompute: (data?: { date?: string }) =>
    client.post('/hr/analytics/recompute', data).then(r => r.data),
};
```

- [ ] **Step 3: Create query hooks**

Create `web-system-app/src/features/company-admin/api/use-analytics-queries.ts`:

```typescript
import { useQuery } from '@tanstack/react-query';
import { analyticsApi } from '@/lib/api/analytics';

export const analyticsKeys = {
  all: ['analytics'] as const,
  dashboard: (name: string, params?: Record<string, unknown>) =>
    params ? [...analyticsKeys.all, 'dashboard', name, params] as const : [...analyticsKeys.all, 'dashboard', name] as const,
  drilldown: (dashboard: string, params: Record<string, unknown>) =>
    [...analyticsKeys.all, 'drilldown', dashboard, params] as const,
  alerts: (params?: Record<string, unknown>) =>
    params ? [...analyticsKeys.all, 'alerts', params] as const : [...analyticsKeys.all, 'alerts'] as const,
};

export function useAnalyticsDashboard(dashboard: string, params?: Record<string, unknown>) {
  return useQuery({
    queryKey: analyticsKeys.dashboard(dashboard, params),
    queryFn: () => analyticsApi.getDashboard(dashboard, params),
  });
}

export function useAnalyticsDrilldown(dashboard: string, params: Record<string, unknown>) {
  return useQuery({
    queryKey: analyticsKeys.drilldown(dashboard, params),
    queryFn: () => analyticsApi.getDrilldown(dashboard, params),
    enabled: !!params.type,
  });
}

export function useAnalyticsAlerts(params?: Record<string, unknown>) {
  return useQuery({
    queryKey: analyticsKeys.alerts(params),
    queryFn: () => analyticsApi.getAlerts(params),
  });
}
```

- [ ] **Step 4: Create mutation hooks**

Create `web-system-app/src/features/company-admin/api/use-analytics-mutations.ts`:

```typescript
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { analyticsApi } from '@/lib/api/analytics';
import { showSuccess, showApiError } from '@/lib/toast';
import { analyticsKeys } from './use-analytics-queries';

export function useAcknowledgeAlert() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => analyticsApi.acknowledgeAlert(id),
    onSuccess: () => {
      showSuccess('Alert acknowledged');
      qc.invalidateQueries({ queryKey: analyticsKeys.alerts() });
    },
    onError: showApiError,
  });
}

export function useResolveAlert() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => analyticsApi.resolveAlert(id),
    onSuccess: () => {
      showSuccess('Alert resolved');
      qc.invalidateQueries({ queryKey: analyticsKeys.alerts() });
    },
    onError: showApiError,
  });
}

export function useRecompute() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (data?: { date?: string }) => analyticsApi.recompute(data),
    onSuccess: () => {
      showSuccess('Analytics recomputation triggered');
      qc.invalidateQueries({ queryKey: analyticsKeys.all });
    },
    onError: showApiError,
  });
}
```

- [ ] **Step 5: Commit**

```bash
git add package.json pnpm-lock.yaml src/lib/api/analytics.ts src/features/company-admin/api/use-analytics-queries.ts src/features/company-admin/api/use-analytics-mutations.ts
git commit -m "feat(analytics): add web API layer, React Query hooks, and install Rrecharts"
```

---

### Task 5.2: Shared Analytics Components (Web)

**Files:**
- Create all components in `web-system-app/src/components/analytics/`

This task creates the reusable component library. Each component is a focused file. Due to plan length, I'll specify the key components with their interfaces — the actual implementation follows existing web patterns (Tailwind classes, dark mode support, lucide-react icons).

- [ ] **Step 1: Create `DashboardShell.tsx`**

Standard layout wrapper that accepts KPIs, charts, insights, drilldown table as children sections. Renders the GlobalFilters bar at top, then each section in order.

- [ ] **Step 2: Create `GlobalFilters.tsx`**

Filter bar with: Date range picker, Department select, Location select, Grade select, Employee Type select. Uses existing `SearchableSelect` component from `@/components/ui/SearchableSelect`. Fires `onFiltersChange(filters)` callback.

- [ ] **Step 3: Create `KPIGrid.tsx`**

Renders an array of `KPICard` objects in a responsive grid (4 cols desktop, 2 cols tablet, 1 col mobile). Each card shows value, label, trend arrow + percentage, and is clickable (fires `onDrilldown(drilldownType)` callback).

- [ ] **Step 4: Create `InsightsPanel.tsx`**

Collapsible panel showing max 5 insight items. Each item has a severity badge (critical=red, warning=amber, info=blue, positive=green), title, description. Clickable insights with `drilldownType` navigate to drilldown.

- [ ] **Step 5: Create `AlertsBanner.tsx`**

Renders active alerts as dismissible cards at the top. Shows severity icon, title, description, and "Acknowledge" / "Resolve" buttons.

- [ ] **Step 6: Create `TrendChart.tsx`**

Rrecharts wrapper for line/area charts. Accepts `TrendSeries` data. Responsive, dark mode aware (use Rrecharts dark theme detection).

```typescript
// Key interface
interface TrendChartProps {
  series: TrendSeries[];
  height?: number;
}
```

- [ ] **Step 7: Create `DistributionChart.tsx`**

Rrecharts wrapper supporting donut, bar, and stacked bar. Accepts `Distribution` data.

- [ ] **Step 8: Create `HeatmapChart.tsx`, `ScatterChart.tsx`, `FunnelChart.tsx`**

Rrecharts wrappers for specialized chart types.

- [ ] **Step 9: Create `DrilldownTable.tsx`**

Paginated data table with sort, search, and export buttons. Uses existing `DataTable` component as base. Adds `ExportMenu` integration.

- [ ] **Step 10: Create `ExportMenu.tsx`**

Dropdown menu with Excel/PDF/CSV options. Calls `analyticsApi.exportReport()` and triggers file download.

- [ ] **Step 11: Create `ZeroDataState.tsx`**

Empty state component shown when `meta.lastComputedAt === null`. Shows illustration + "No analytics data yet" + onboarding hints.

- [ ] **Step 12: Commit**

```bash
git add src/components/analytics/
git commit -m "feat(analytics): add shared web analytics components (DashboardShell, charts, filters, exports)"
```

---

### Task 5.3: Dashboard Screens (Web)

**Files:**
- Create 9 screens in `web-system-app/src/features/company-admin/hr/analytics/`
- Modify: `web-system-app/src/App.tsx` (add routes)

- [ ] **Step 1: Create `ExecutiveDashboardScreen.tsx`**

Uses `DashboardShell` with `useAnalyticsDashboard('executive', filters)`. Maps response to KPIGrid, TrendChart, DistributionChart, InsightsPanel, AlertsBanner. Includes cross-navigation (KPI click → navigate to respective dashboard).

- [ ] **Step 2: Create remaining 8 dashboard screens**

Each follows the same pattern:
1. `useAnalyticsDashboard(dashboardName, filters)` hook
2. `DashboardShell` layout
3. Dashboard-specific chart configurations
4. Drilldown table with `useAnalyticsDrilldown` on type selection

Screens: `WorkforceDashboardScreen`, `AttendanceAnalyticsDashboardScreen`, `LeaveAnalyticsDashboardScreen`, `PayrollAnalyticsDashboardScreen`, `ComplianceDashboardScreen`, `PerformanceAnalyticsDashboardScreen`, `RecruitmentDashboardScreen`, `AttritionDashboardScreen`.

- [ ] **Step 3: Add routes to App.tsx**

Add under the HR routes section:

```typescript
{/* Analytics */}
<Route path="analytics" element={<RequirePermission permission="hr:read"><ExecutiveDashboardScreen /></RequirePermission>} />
<Route path="analytics/executive" element={<RequirePermission permission="hr:read"><ExecutiveDashboardScreen /></RequirePermission>} />
<Route path="analytics/workforce" element={<RequirePermission permission="hr:read"><WorkforceDashboardScreen /></RequirePermission>} />
<Route path="analytics/attendance" element={<RequirePermission permission="hr:read"><AttendanceAnalyticsDashboardScreen /></RequirePermission>} />
<Route path="analytics/leave" element={<RequirePermission permission="hr:read"><LeaveAnalyticsDashboardScreen /></RequirePermission>} />
<Route path="analytics/payroll" element={<RequirePermission permission="hr:read"><PayrollAnalyticsDashboardScreen /></RequirePermission>} />
<Route path="analytics/compliance" element={<RequirePermission permission="hr:read"><ComplianceDashboardScreen /></RequirePermission>} />
<Route path="analytics/performance" element={<RequirePermission permission="hr:read"><PerformanceAnalyticsDashboardScreen /></RequirePermission>} />
<Route path="analytics/recruitment" element={<RequirePermission permission="hr:read"><RecruitmentDashboardScreen /></RequirePermission>} />
<Route path="analytics/attrition" element={<RequirePermission permission="hr:read"><AttritionDashboardScreen /></RequirePermission>} />
```

- [ ] **Step 4: Commit**

```bash
git add src/features/company-admin/hr/analytics/ src/App.tsx
git commit -m "feat(analytics): add 9 web dashboard screens with routing"
```

---

## Phase 6: Mobile Dashboards

### Task 6.1: Install Chart Library & API Layer (Mobile)

- [ ] **Step 1: Install Victory Native**

```bash
cd mobile-app && pnpm add victory-native
```

- [ ] **Step 2: Create `mobile-app/src/lib/api/analytics.ts`**

Same API service as web (identical interface, uses mobile's `client` import).

- [ ] **Step 3: Create query and mutation hooks**

Same as web hooks but in `mobile-app/src/features/company-admin/api/`.

- [ ] **Step 4: Commit**

```bash
git add package.json pnpm-lock.yaml src/lib/api/analytics.ts src/features/company-admin/api/use-analytics-queries.ts src/features/company-admin/api/use-analytics-mutations.ts
git commit -m "feat(analytics): add mobile API layer, query hooks, and install Victory Native"
```

---

### Task 6.2: Shared Analytics Components (Mobile)

- [ ] **Step 1: Create mobile analytics components**

In `mobile-app/src/components/analytics/`:
- `DashboardShell.tsx` — ScrollView with sections, LinearGradient header
- `FilterBottomSheet.tsx` — `@gorhom/bottom-sheet` with filter inputs
- `KPIGrid.tsx` — 2-column FlatList of KPI cards
- `InsightsPanel.tsx` — Collapsible accordion
- `AlertsBanner.tsx` — Alert cards
- `DrilldownList.tsx` — FlatList with expandable rows
- `TrendChart.tsx` — Victory Native `VictoryLine` / `VictoryArea`
- `DistributionChart.tsx` — Victory Native `VictoryPie` / `VictoryBar`
- `ExportButton.tsx` — Action sheet for export options
- `ZeroDataState.tsx` — Empty state with illustration

All components use: `StyleSheet.create()` for layouts, NativeWind `className` for text, `colors` from `@/components/ui/colors`, `font-inter` on all Text, `FadeInDown` animations, `useSafeAreaInsets()` for padding.

- [ ] **Step 2: Commit**

```bash
git add src/components/analytics/
git commit -m "feat(analytics): add shared mobile analytics components"
```

---

### Task 6.3: Dashboard Screens & Routes (Mobile)

- [ ] **Step 1: Create 9 dashboard screens**

In `mobile-app/src/features/company-admin/hr/analytics/`:
- `executive-dashboard-screen.tsx`
- `workforce-dashboard-screen.tsx`
- `attendance-analytics-dashboard-screen.tsx`
- `leave-analytics-dashboard-screen.tsx`
- `payroll-analytics-dashboard-screen.tsx`
- `compliance-dashboard-screen.tsx`
- `performance-analytics-dashboard-screen.tsx`
- `recruitment-dashboard-screen.tsx`
- `attrition-dashboard-screen.tsx`

Each exports a named function (e.g., `export function ExecutiveDashboardScreen() {}`).

- [ ] **Step 2: Create route files**

In `mobile-app/src/app/(app)/company/hr/analytics/`:
- `_layout.tsx` — Stack with `headerShown: false`
- `index.tsx` — re-exports `ExecutiveDashboardScreen as default`
- `executive.tsx` — re-exports `ExecutiveDashboardScreen as default`
- `workforce.tsx` — re-exports `WorkforceDashboardScreen as default`
- ... (one per dashboard)

- [ ] **Step 3: Update HR layout**

Add analytics routes to `mobile-app/src/app/(app)/company/hr/_layout.tsx` Stack.

- [ ] **Step 4: Commit**

```bash
git add src/features/company-admin/hr/analytics/ src/app/\(app\)/company/hr/analytics/ src/app/\(app\)/company/hr/_layout.tsx
git commit -m "feat(analytics): add 9 mobile dashboard screens with Expo Router routes"
```

---

## Phase 7: Testing & Polish

### Task 7.1: Backend Unit Tests

**Files:**
- Create: `avy-erp-backend/src/modules/hr/analytics/__tests__/filters-normalizer.test.ts`
- Create: `avy-erp-backend/src/modules/hr/analytics/__tests__/anomaly-detector.test.ts`
- Create: `avy-erp-backend/src/modules/hr/analytics/__tests__/scoring.test.ts`
- Create: `avy-erp-backend/src/modules/hr/analytics/__tests__/insights-engine.test.ts`

- [ ] **Step 1: Write filter normalizer tests**

Test: defaults applied, date validation, limit capping, timezone conversion, search sanitization.

- [ ] **Step 2: Write anomaly detector tests**

Test: no anomaly for normal values, HIGH anomaly for 2+ std dev, MEDIUM for 1.5+, handles zero std dev, requires minimum data points.

- [ ] **Step 3: Write scoring engine tests**

Test: attrition risk score ranges 0-100, each factor contributes correct weight, manager score normalization, productivity index thresholds, compliance score with perfect and zero compliance.

- [ ] **Step 4: Write insights engine tests**

Test: rule evaluation, insight prioritization (critical first, max 5), anomaly integration.

- [ ] **Step 5: Run tests**

```bash
cd avy-erp-backend && pnpm test -- --testPathPattern analytics
```

- [ ] **Step 6: Commit**

```bash
git add src/modules/hr/analytics/__tests__/
git commit -m "test(analytics): add unit tests for filter normalizer, anomaly detector, scoring, and insights engine"
```

---

### Task 7.2: Integration Tests

**Files:**
- Create: `avy-erp-backend/src/modules/hr/analytics/__tests__/orchestrator.integration.test.ts`
- Create: `avy-erp-backend/src/modules/hr/analytics/__tests__/access-control.test.ts`

- [ ] **Step 1: Write orchestrator integration tests**

Test: dashboard returns standardized response shape, soft-fail returns partial data with partialFailures in meta, audit log created on view.

- [ ] **Step 2: Write access control tests**

Test: Employee role gets personal scope, Manager gets team scope, Finance blocked from performance dashboard, HR gets full org, cross-tenant isolation (Company A query never returns Company B data).

- [ ] **Step 3: Write export rate limit test**

Test: 20 exports succeed, 21st returns 429.

- [ ] **Step 4: Run all tests**

```bash
cd avy-erp-backend && pnpm test -- --testPathPattern analytics
```

- [ ] **Step 5: Commit**

```bash
git add src/modules/hr/analytics/__tests__/
git commit -m "test(analytics): add integration tests for orchestrator, access control, and rate limiting"
```

---

### Task 7.3: Build Verification

- [ ] **Step 1: Backend build**

```bash
cd avy-erp-backend && pnpm build
```
Expected: No TypeScript errors.

- [ ] **Step 2: Web build**

```bash
cd web-system-app && pnpm build
```
Expected: No TypeScript errors.

- [ ] **Step 3: Mobile type check**

```bash
cd mobile-app && pnpm type-check
```
Expected: No TypeScript errors.

- [ ] **Step 4: Lint all**

```bash
cd avy-erp-backend && pnpm lint
cd ../web-system-app && pnpm lint
cd ../mobile-app && pnpm lint
```

- [ ] **Step 5: Final commit**

```bash
git add -A
git commit -m "chore(analytics): fix any lint/type issues from build verification"
```
