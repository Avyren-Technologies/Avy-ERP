# HRMS Intelligence Platform — Design Specification

**Date**: 2026-03-31
**Status**: Draft
**Scope**: Backend analytics engine + 9 intelligence dashboards (Web + Mobile)
**Platforms**: avy-erp-backend, web-system-app, mobile-app

---

## 1. Problem Statement

The HRMS module has 76+ Prisma models, ~370 API endpoints, and 170+ screens across web and mobile. All data is transactional — there is no analytics, intelligence, or reporting layer. Company admins and HR teams cannot answer:

- "What happened?" (reports)
- "Why did it happen?" (insights)
- "What will happen?" (predictions)

This spec designs a production-grade HR Intelligence Platform that transforms raw HRMS data into decision-driven dashboards with embedded intelligence.

---

## 2. Architecture Overview

```
┌─────────────────────────────────────────────────────────┐
│                    PRESENTATION LAYER                    │
│  9 Dashboards (Web: ECharts + Mobile: Victory Native)   │
│  Global filters, cross-navigation, zero-data UX         │
├─────────────────────────────────────────────────────────┤
│               DASHBOARD ORCHESTRATOR LAYER               │
│  dashboard-orchestrator.service.ts                       │
│  - Combines parallel analytics + insights + alerts       │
│  - Applies filters once, structures response for UI      │
│  - Permission-aware metric filtering                     │
├─────────────────────────────────────────────────────────┤
│                    ANALYTICS LAYER                       │
│  analytics.service.ts + report-aggregator.service.ts     │
│  - Queries precomputed tables                            │
│  - Role-based data scoping (reportAccessResolver)        │
│  - Drilldown query API                                   │
│  - Tag-based cache invalidation                          │
├─────────────────────────────────────────────────────────┤
│                   INTELLIGENCE LAYER                     │
│  insights-engine.service.ts                              │
│  ├── rules/    (threshold-based text insights)           │
│  ├── scoring/  (attrition risk, manager effectiveness)   │
│  └── anomaly/  (deviation detection)                     │
│  alert.service.ts (priority + stateful alerts)           │
├─────────────────────────────────────────────────────────┤
│                      DATA LAYER                          │
│  4 Precomputed Prisma models (versioned, cron-populated) │
│  Redis: tag-based cache with report-level keys           │
├─────────────────────────────────────────────────────────┤
│                     SOURCE DATA                          │
│  76+ existing Prisma models (unchanged)                  │
└─────────────────────────────────────────────────────────┘
```

---

## 3. Data Layer — Precomputed Analytics Tables

### 3.1 New Prisma Models

All precomputed tables include versioning fields for audit trail and safe recomputation.

#### EmployeeAnalyticsDaily

```prisma
model EmployeeAnalyticsDaily {
  id              String   @id @default(cuid())
  companyId       String
  date            DateTime @db.Date
  version         Int      @default(1)
  computedAt      DateTime @default(now())

  // Headcount snapshot
  totalHeadcount  Int
  activeCount     Int
  probationCount  Int
  noticeCount     Int
  separatedCount  Int

  // Movement
  joinersCount    Int
  leaversCount    Int
  transfersCount  Int
  promotionsCount Int

  // Breakdowns (JSON objects: { "dept_id": count, ... })
  byDepartment    Json     // { deptId: { active, probation, notice, joined, left } }
  byLocation      Json     // { locationId: { active, joined, left } }
  byGrade         Json     // { gradeId: { count, avgCTC } }
  byEmployeeType  Json     // { typeId: { count } }
  byGender        Json     // { MALE: n, FEMALE: n, OTHER: n }
  byAgeBand       Json     // { "20-25": n, "26-30": n, ... }
  byTenureBand    Json     // { "0-1yr": n, "1-3yr": n, "3-5yr": n, "5+yr": n }

  // Org structure
  avgSpanOfControl Float?  // avg direct reports per manager
  vacancyRate      Float?  // (sanctioned - actual) / sanctioned

  company         Company  @relation(fields: [companyId], references: [id])

  @@unique([companyId, date, version])
  @@index([companyId, date])
}
```

#### AttendanceAnalyticsDaily

```prisma
model AttendanceAnalyticsDaily {
  id                  String   @id @default(cuid())
  companyId           String
  date                DateTime @db.Date
  version             Int      @default(1)
  computedAt          DateTime @default(now())

  // Totals
  totalEmployees      Int
  presentCount        Int
  absentCount         Int
  lateCount           Int
  halfDayCount        Int
  onLeaveCount        Int
  weekOffCount        Int
  holidayCount        Int

  // Hours
  avgWorkedHours      Float
  totalOvertimeHours  Float
  totalOvertimeCost   Float?

  // Productivity
  productivityIndex   Float    // workedHours / expectedHours (0-1+ scale)

  // Late analysis
  avgLateMinutes      Float
  lateThresholdBreaches Int    // employees exceeding monthly late limit

  // Regularization
  regularizationCount Int
  missedPunchCount    Int

  // Breakdowns
  byDepartment        Json     // { deptId: { present, absent, late, avgHours, productivity } }
  byLocation          Json
  byShift             Json
  bySource            Json     // { BIOMETRIC: n, GPS: n, MANUAL: n, APP: n }

  company             Company  @relation(fields: [companyId], references: [id])

  @@unique([companyId, date, version])
  @@index([companyId, date])
}
```

#### PayrollAnalyticsMonthly

```prisma
model PayrollAnalyticsMonthly {
  id                    String   @id @default(cuid())
  companyId             String
  month                 Int      // 1-12
  year                  Int
  version               Int      @default(1)
  computedAt            DateTime @default(now())

  // Totals
  employeeCount         Int
  totalGrossEarnings    Float
  totalDeductions       Float
  totalNetPay           Float
  totalEmployerCost     Float    // gross + employer PF/ESI/LWF/gratuity

  // Statutory
  totalPFEmployee       Float
  totalPFEmployer       Float
  totalESIEmployee      Float
  totalESIEmployer      Float
  totalPT               Float
  totalTDS              Float
  totalLWFEmployee      Float
  totalLWFEmployer      Float
  totalGratuityProvision Float

  // Analysis
  avgCTC                Float
  medianCTC             Float
  exceptionCount        Int
  varianceFromLastMonth Float?   // percentage

  // Loans & holds
  totalLoanOutstanding  Float
  activeLoanCount       Int
  totalSalaryHolds      Int

  // Bonus & incentives
  totalBonusDisbursed   Float
  totalIncentivesPaid   Float

  // Breakdowns
  byDepartment          Json     // { deptId: { gross, deductions, net, avgCTC, count } }
  byLocation            Json
  byGrade               Json     // { gradeId: { avgCTC, count, totalCost } }
  byCTCBand             Json     // { "0-5L": n, "5-10L": n, ... }
  byComponent           Json     // { componentId: { totalAmount, avgAmount } }

  company               Company  @relation(fields: [companyId], references: [id])

  @@unique([companyId, month, year, version])
  @@index([companyId, year, month])
}
```

#### AttritionMetricsMonthly

```prisma
model AttritionMetricsMonthly {
  id                      String   @id @default(cuid())
  companyId               String
  month                   Int
  year                    Int
  version                 Int      @default(1)
  computedAt              DateTime @default(now())

  // Rates
  attritionRate           Float    // leavers / avg headcount
  voluntaryRate           Float
  involuntaryRate         Float
  earlyAttritionRate      Float    // left within 1 year

  // Counts
  totalExits              Int
  voluntaryExits          Int
  involuntaryExits        Int
  retirements             Int
  earlyExits              Int      // within 1 year of joining

  // Exit analysis
  avgTenureAtExit         Float    // months
  exitReasonBreakdown     Json     // { "no_growth": n, "compensation": n, ... }
  wouldRecommendAvg       Float?   // from exit interviews (1-5)

  // Risk scores (top 20 flight risk employees)
  flightRiskEmployees     Json     // [{ employeeId, score, factors: [...] }]

  // F&F
  pendingFnFCount         Int
  totalFnFAmount          Float
  avgFnFProcessingDays    Float

  // Breakdowns
  byDepartment            Json     // { deptId: { exits, rate, avgTenure } }
  byGrade                 Json
  byTenureBand            Json     // { "0-1yr": n, "1-3yr": n, ... }
  bySeparationType        Json     // { VOLUNTARY_RESIGNATION: n, TERMINATION: n, ... }

  company                 Company  @relation(fields: [companyId], references: [id])

  @@unique([companyId, month, year, version])
  @@index([companyId, year, month])
}
```

### 3.2 Alert Model

```prisma
model AnalyticsAlert {
  id            String   @id @default(cuid())
  companyId     String
  dashboard     String   // executive, attendance, payroll, etc.
  type          String   // attrition_spike, compliance_overdue, payroll_anomaly, etc.
  severity      String   // LOW, MEDIUM, HIGH, CRITICAL
  status        String   @default("ACTIVE") // ACTIVE, ACKNOWLEDGED, RESOLVED
  title         String
  description   String
  metadata      Json?    // { employeeId?, departmentId?, threshold?, actual? }
  acknowledgedBy String?
  acknowledgedAt DateTime?
  resolvedBy    String?
  resolvedAt    DateTime?
  createdAt     DateTime @default(now())
  expiresAt     DateTime?

  company       Company  @relation(fields: [companyId], references: [id])

  @@index([companyId, status, severity])
  @@index([companyId, dashboard])
}
```

### 3.3 Analytics Audit Log

```prisma
model AnalyticsAuditLog {
  id          String   @id @default(cuid())
  companyId   String
  userId      String
  action      String   // VIEW_DASHBOARD, EXPORT_REPORT, DRILLDOWN, ACKNOWLEDGE_ALERT
  dashboard   String?  // executive, attendance, etc.
  reportType  String?  // salary_register, pf_ecr, etc.
  filters     Json?    // { dateRange, departmentId, ... }
  exportFormat String? // EXCEL, PDF, CSV
  ipAddress   String?
  userAgent   String?
  createdAt   DateTime @default(now())

  @@index([companyId, userId, createdAt])
  @@index([companyId, action, createdAt])
}
```

### 3.4 Cron Population Schedule

| Table | Trigger | Schedule |
|-------|---------|----------|
| `EmployeeAnalyticsDaily` | Nightly cron | `0 1 * * *` (1:00 AM) |
| `AttendanceAnalyticsDaily` | End-of-day cron | `0 23 * * *` (11:00 PM) |
| `PayrollAnalyticsMonthly` | Post payroll-run approval + month-end cron | On event + `0 2 1 * *` (2:00 AM on 1st) |
| `AttritionMetricsMonthly` | Nightly cron (recalculates current month) | `0 3 * * *` (3:00 AM — staggered to avoid DB contention) |
| `AnalyticsAlert` | After each analytics computation | Inline with cron jobs |

Each cron run increments `version` and preserves prior versions for audit. A retention policy deletes versions older than 90 days (keeping latest per date).

---

## 4. Backend Services

All services live in `avy-erp-backend/src/modules/hr/analytics/`.

### 4.1 Directory Structure

```
src/modules/hr/analytics/
├── analytics.controller.ts
├── analytics.routes.ts
├── analytics.validators.ts
├── analytics.types.ts
├── services/
│   ├── dashboard-orchestrator.service.ts
│   ├── analytics.service.ts
│   ├── report-aggregator.service.ts
│   ├── report-access.service.ts
│   ├── analytics-cron.service.ts
│   └── analytics-audit.service.ts
├── insights/
│   ├── insights-engine.service.ts
│   ├── rules/
│   │   ├── attrition.rules.ts
│   │   ├── attendance.rules.ts
│   │   ├── payroll.rules.ts
│   │   ├── compliance.rules.ts
│   │   ├── performance.rules.ts
│   │   └── recruitment.rules.ts
│   ├── scoring/
│   │   ├── attrition-score.ts
│   │   ├── manager-score.ts
│   │   ├── productivity-score.ts
│   │   └── compliance-score.ts
│   └── anomaly/
│       ├── anomaly-detector.ts
│       └── thresholds.ts
├── alerts/
│   ├── alert.service.ts
│   └── alert-rules.ts
└── exports/
    ├── excel-exporter.ts
    └── pdf-exporter.ts
```

### 4.2 Dashboard Orchestrator Service

**File**: `services/dashboard-orchestrator.service.ts`

Single entry point per dashboard. Combines parallel analytics + insights + alerts, applies filters once, structures the response for the UI.

```typescript
// Conceptual interface — not implementation code
class DashboardOrchestratorService {

  // Each method returns a fully structured dashboard response
  getExecutiveDashboard(filters: DashboardFilters, userId: string, role: string): Promise<ExecutiveDashboardResponse>
  getWorkforceDashboard(filters: DashboardFilters, userId: string, role: string): Promise<WorkforceDashboardResponse>
  getAttendanceDashboard(filters: DashboardFilters, userId: string, role: string): Promise<AttendanceDashboardResponse>
  getLeaveDashboard(filters: DashboardFilters, userId: string, role: string): Promise<LeaveDashboardResponse>
  getPayrollDashboard(filters: DashboardFilters, userId: string, role: string): Promise<PayrollDashboardResponse>
  getComplianceDashboard(filters: DashboardFilters, userId: string, role: string): Promise<ComplianceDashboardResponse>
  getPerformanceDashboard(filters: DashboardFilters, userId: string, role: string): Promise<PerformanceDashboardResponse>
  getRecruitmentDashboard(filters: DashboardFilters, userId: string, role: string): Promise<RecruitmentDashboardResponse>
  getAttritionDashboard(filters: DashboardFilters, userId: string, role: string): Promise<AttritionDashboardResponse>
}
```

**Internal pattern** (every method follows this):
1. Call `reportAccess.resolveScope(userId, role, dashboard)` to get data boundaries
2. Fire parallel queries: `Promise.all([analytics queries, insights, alerts])`
3. Call `reportAccess.filterMetrics(response, permissions)` to strip unauthorized metrics
4. Log to `AnalyticsAuditLog`
5. Return structured response matching the standard dashboard layout

### 4.3 Analytics Service

**File**: `services/analytics.service.ts`

Queries precomputed tables with filters. Returns raw aggregated data (no insights, no formatting).

```typescript
class AnalyticsService {
  // Headcount & workforce
  getHeadcountSummary(filters: DashboardFilters, scope: DataScope): Promise<HeadcountData>
  getHeadcountTrend(filters: DashboardFilters, scope: DataScope): Promise<TrendData[]>
  getDemographics(filters: DashboardFilters, scope: DataScope): Promise<DemographicsData>
  getDepartmentStrength(filters: DashboardFilters, scope: DataScope): Promise<DeptStrengthData>

  // Attendance
  getAttendanceSummary(filters: DashboardFilters, scope: DataScope): Promise<AttendanceSummaryData>
  getAttendanceTrend(filters: DashboardFilters, scope: DataScope): Promise<TrendData[]>
  getProductivityIndex(filters: DashboardFilters, scope: DataScope): Promise<ProductivityData>

  // Leave
  getLeaveUtilization(filters: DashboardFilters, scope: DataScope): Promise<LeaveUtilizationData>
  getLeaveHeatmap(filters: DashboardFilters, scope: DataScope): Promise<HeatmapData>
  getEncashmentLiability(filters: DashboardFilters, scope: DataScope): Promise<LiabilityData>

  // Payroll
  getPayrollCostSummary(filters: DashboardFilters, scope: DataScope): Promise<PayrollCostData>
  getPayrollTrend(filters: DashboardFilters, scope: DataScope): Promise<TrendData[]>
  getCTCDistribution(filters: DashboardFilters, scope: DataScope): Promise<DistributionData>
  getCostVsPerformance(filters: DashboardFilters, scope: DataScope): Promise<ScatterData>

  // Statutory
  getStatutorySummary(filters: DashboardFilters, scope: DataScope): Promise<StatutoryData>
  getComplianceScore(filters: DashboardFilters, scope: DataScope): Promise<ComplianceScoreData>
  getFilingStatus(filters: DashboardFilters, scope: DataScope): Promise<FilingStatusData>

  // Performance
  getAppraisalStatus(filters: DashboardFilters, scope: DataScope): Promise<AppraisalStatusData>
  getNineBoxGrid(filters: DashboardFilters, scope: DataScope): Promise<NineBoxData>
  getGoalAchievement(filters: DashboardFilters, scope: DataScope): Promise<GoalData>
  getManagerEffectiveness(filters: DashboardFilters, scope: DataScope): Promise<ManagerData[]>

  // Recruitment
  getRecruitmentFunnel(filters: DashboardFilters, scope: DataScope): Promise<FunnelData>
  getHiringVelocity(filters: DashboardFilters, scope: DataScope): Promise<TrendData[]>
  getSourceEffectiveness(filters: DashboardFilters, scope: DataScope): Promise<SourceData>

  // Attrition
  getAttritionSummary(filters: DashboardFilters, scope: DataScope): Promise<AttritionSummaryData>
  getAttritionTrend(filters: DashboardFilters, scope: DataScope): Promise<TrendData[]>
  getFlightRiskEmployees(filters: DashboardFilters, scope: DataScope): Promise<FlightRiskData[]>
  getExitAnalysis(filters: DashboardFilters, scope: DataScope): Promise<ExitAnalysisData>
}
```

### 4.4 Report Access Service

**File**: `services/report-access.service.ts`

Enforces multi-tenant isolation and role-based data scoping. Every analytics query passes through this.

```typescript
class ReportAccessService {
  // Resolve what data a user can see
  resolveScope(userId: string, role: string, dashboard: string): Promise<DataScope>
  // DataScope = { companyId, departmentIds?, locationIds?, employeeIds?, isFullOrg }

  // Filter metrics based on permissions
  filterMetrics(response: DashboardResponse, permissions: string[]): DashboardResponse
  // Strips fields like performanceRatings from Finance users, salary data from non-HR, etc.
}
```

**Role → Scope mapping**:

| Role | Scope | Metric Restrictions |
|------|-------|-------------------|
| Employee | Own employeeId only | Personal KPIs embedded in ESS |
| Manager | Direct reports (via reportingManagerId chain) | No salary details of reports, no org-wide data |
| HR Personnel | Full org (all departments, locations) | No restrictions on HR metrics |
| Finance | Full org (payroll data only) | No performance ratings, no attrition reasons, no grievances |
| Company Admin / CXO | Full org | No restrictions |

**Multi-tenant safety**: Every query generated by `analytics.service.ts` MUST include `WHERE companyId = ?`. This is enforced at the `resolveScope` level — the returned `DataScope` always contains `companyId`, and the analytics service uses it as a mandatory filter. A cross-tenant data leak test validates this.

### 4.5 Insights Engine

**File**: `insights/insights-engine.service.ts`

Orchestrates the 3 sub-engines and returns structured insight objects.

```typescript
interface Insight {
  id: string
  dashboard: string
  category: 'info' | 'warning' | 'critical' | 'positive'
  title: string           // "Attrition spiked 12% in Engineering"
  description: string     // Longer explanation with context
  metric: string          // "attrition_rate"
  currentValue: number
  benchmarkValue?: number // industry or historical benchmark
  changePercent?: number
  affectedEntity?: string // departmentId, employeeId, etc.
  actionable: boolean     // Can user take action from this?
  drilldownType?: string  // links to drilldown API
}
```

#### 4.5.1 Rule Engine

**Directory**: `insights/rules/`

Each file exports threshold-based rules that generate text insights.

```typescript
// attrition.rules.ts — conceptual
export const attritionRules: InsightRule[] = [
  {
    id: 'high_attrition_rate',
    evaluate: (data) => data.attritionRate > 0.20,
    generate: (data) => ({
      category: 'critical',
      title: `Attrition at ${(data.attritionRate * 100).toFixed(1)}% — exceeds 20% benchmark`,
      description: `${data.totalExits} employees left this month. Industry benchmark is 15-18%.`,
      actionable: true,
      drilldownType: 'attrition_details'
    })
  },
  {
    id: 'early_attrition_spike',
    evaluate: (data) => data.earlyAttritionRate > 0.30,
    generate: (data) => ({
      category: 'warning',
      title: `${(data.earlyAttritionRate * 100).toFixed(0)}% of exits are within first year`,
      description: 'High early attrition suggests onboarding or expectation-setting issues.',
      actionable: true,
      drilldownType: 'early_attrition'
    })
  },
  // ... more rules
]
```

Rules for each domain:
- **attrition.rules.ts**: Rate thresholds, early attrition, dept spikes, exit reason concentration
- **attendance.rules.ts**: Absence rate, late frequency, productivity drops, OT cost, missed punches
- **payroll.rules.ts**: Cost spikes, exception rates, variance flags, loan concentration, hold duration
- **compliance.rules.ts**: Overdue filings, min wage violations, grievance SLA, disciplinary aging
- **performance.rules.ts**: Bell curve skew, completion delays, goal achievement drops, skill gaps
- **recruitment.rules.ts**: Aging positions, funnel bottlenecks, low acceptance rate, source ROI

#### 4.5.2 Scoring Engine

**Directory**: `insights/scoring/`

Computes composite scores for complex intelligence.

**Attrition Risk Score** (`attrition-score.ts`):
```
Score (0-100) = weighted sum of:
  - Performance rating below avg    → +25
  - Absenteeism above threshold     → +20
  - No promotion in 3+ years        → +20
  - Salary below grade median       → +15
  - Tenure in high-attrition band   → +10
  - Manager has high team attrition → +10
```
Output: Top 20 flight risk employees per company with score + contributing factors.

**Manager Effectiveness Score** (`manager-score.ts`):
```
Score (0-100) = weighted sum of:
  - Team avg performance rating     → 30%
  - Team attrition rate (inverse)   → 25%
  - Approval delay avg (inverse)    → 20%
  - Team attendance rate             → 15%
  - Team satisfaction (if available) → 10%
```

**Productivity Score** (`productivity-score.ts`):
```
Index = workedHours / expectedHours
  Per employee, per department, per location
  Flags: < 0.7 = under-utilized, > 1.2 = over-worked
```

**Compliance Score** (`compliance-score.ts`):
```
Score (0-100) = weighted sum of:
  - Statutory filings on time       → 40%
  - Min wage compliance             → 20%
  - Grievance resolution within SLA → 15%
  - Document compliance             → 15%
  - Data retention compliance       → 10%
```

#### 4.5.3 Anomaly Detection

**Directory**: `insights/anomaly/`

Simple statistical anomaly detection comparing current period against historical average.

```typescript
// anomaly-detector.ts — conceptual
function detectAnomaly(current: number, historicalAvg: number, stdDev: number): AnomalyResult {
  const zScore = (current - historicalAvg) / stdDev
  if (Math.abs(zScore) > 2.0) return { isAnomaly: true, severity: 'HIGH', direction: zScore > 0 ? 'ABOVE' : 'BELOW' }
  if (Math.abs(zScore) > 1.5) return { isAnomaly: true, severity: 'MEDIUM', direction: ... }
  return { isAnomaly: false }
}
```

Applied to: payroll cost, attrition rate, attendance rate, overtime hours, leave consumption — all compared against 6-month rolling average.

### 4.6 Alert Service

**File**: `alerts/alert.service.ts`

Manages stateful alerts with priority and lifecycle.

```typescript
class AlertService {
  // Called by cron jobs after analytics computation
  evaluateAndCreate(companyId: string, dashboard: string, analyticsData: any): Promise<void>

  // Dashboard queries
  getActiveAlerts(companyId: string, dashboard?: string): Promise<AnalyticsAlert[]>
  getAlertsByPriority(companyId: string, severity: string): Promise<AnalyticsAlert[]>

  // User actions
  acknowledgeAlert(alertId: string, userId: string): Promise<void>
  resolveAlert(alertId: string, userId: string): Promise<void>

  // Deduplication: don't create duplicate active alerts of the same type
  // Expiration: alerts auto-resolve after expiresAt
}
```

**Alert Rules** (`alerts/alert-rules.ts`):

| Alert Type | Severity | Trigger |
|------------|----------|---------|
| `attrition_spike` | HIGH | Monthly attrition > 20% |
| `compliance_overdue` | CRITICAL | Statutory filing past deadline |
| `payroll_anomaly` | HIGH | Payroll cost variance > 15% MoM |
| `attendance_drop` | MEDIUM | Today's attendance < 70% |
| `approval_backlog` | MEDIUM | > 10 approvals pending > 3 days |
| `grievance_sla` | HIGH | Grievance unresolved past SLA |
| `min_wage_violation` | CRITICAL | Employee below state minimum wage |
| `high_overtime` | MEDIUM | Dept OT hours > monthly cap |
| `flight_risk` | HIGH | High-performer risk score > 70 |
| `probation_expiry` | LOW | Probation ending within 7 days, no review |

### 4.7 Report Aggregator Service

**File**: `services/report-aggregator.service.ts`

Handles on-demand detailed reports with export capability. These are the drilldown tables behind each dashboard.

```typescript
class ReportAggregatorService {
  // Workforce
  getEmployeeDirectory(filters, scope, pagination): Promise<PaginatedReport>
  getTenureReport(filters, scope, pagination): Promise<PaginatedReport>

  // Attendance drilldowns
  getAttendanceRegister(filters, scope, pagination): Promise<PaginatedReport>  // full month grid
  getLateComersReport(filters, scope, pagination): Promise<PaginatedReport>
  getOvertimeDetailReport(filters, scope, pagination): Promise<PaginatedReport>
  getAbsenteeismReport(filters, scope, pagination): Promise<PaginatedReport>

  // Leave drilldowns
  getLeaveBalanceReport(filters, scope, pagination): Promise<PaginatedReport>
  getLeaveTrendReport(filters, scope): Promise<ChartData>

  // Payroll drilldowns (extends existing 6 reports)
  getSalaryRegister(filters, scope, pagination): Promise<PaginatedReport>
  getBankFile(filters, scope, pagination): Promise<PaginatedReport>
  getPFECR(filters, scope, pagination): Promise<PaginatedReport>
  getESIChallan(filters, scope, pagination): Promise<PaginatedReport>
  getPTChallan(filters, scope, pagination): Promise<PaginatedReport>
  getVarianceReport(filters, scope, pagination): Promise<PaginatedReport>
  getLoanOutstandingReport(filters, scope, pagination): Promise<PaginatedReport>
  getCTCBandReport(filters, scope, pagination): Promise<PaginatedReport>

  // Performance drilldowns
  getAppraisalDetailReport(filters, scope, pagination): Promise<PaginatedReport>
  getSkillGapReport(filters, scope, pagination): Promise<PaginatedReport>
  getSuccessionReport(filters, scope, pagination): Promise<PaginatedReport>

  // Recruitment drilldowns
  getCandidatePipelineReport(filters, scope, pagination): Promise<PaginatedReport>
  getRequisitionAgingReport(filters, scope, pagination): Promise<PaginatedReport>

  // Attrition drilldowns
  getExitDetailReport(filters, scope, pagination): Promise<PaginatedReport>
  getFnFTrackerReport(filters, scope, pagination): Promise<PaginatedReport>
  getFlightRiskReport(filters, scope, pagination): Promise<PaginatedReport>

  // Export
  exportToExcel(reportType: string, filters, scope): Promise<Buffer>
  exportToPDF(reportType: string, filters, scope): Promise<Buffer>
  exportToCSV(reportType: string, filters, scope): Promise<Buffer>
}
```

### 4.8 Analytics Cron Service

**File**: `services/analytics-cron.service.ts`

Scheduled jobs that populate precomputed tables.

```typescript
class AnalyticsCronService {
  // Runs for ALL companies (iterates tenants)
  computeEmployeeAnalyticsDaily(): Promise<void>    // 1:00 AM
  computeAttendanceAnalyticsDaily(): Promise<void>  // 11:00 PM
  computeAttritionMetricsMonthly(): Promise<void>   // 2:00 AM
  computePayrollAnalyticsMonthly(): Promise<void>   // 2:00 AM on 1st, also triggered post-payroll

  // Cleanup
  purgeOldVersions(retentionDays: number): Promise<void>  // Keep 90 days

  // Manual trigger (for admin)
  recomputeForCompany(companyId: string, date: Date): Promise<void>
}
```

### 4.9 Analytics Audit Service

**File**: `services/analytics-audit.service.ts`

```typescript
class AnalyticsAuditService {
  logView(userId: string, companyId: string, dashboard: string, filters: any): Promise<void>
  logExport(userId: string, companyId: string, reportType: string, format: string, filters: any): Promise<void>
  logDrilldown(userId: string, companyId: string, dashboard: string, drilldownType: string): Promise<void>
  logAlertAction(userId: string, companyId: string, alertId: string, action: string): Promise<void>
}
```

### 4.10 Caching Strategy

**Pattern**: Tag-based invalidation over Redis.

```
Key format: analytics:{companyId}:{dashboard}:{filters_hash}
Tags: analytics:{companyId}:attendance, analytics:{companyId}:payroll, etc.
```

| Data Type | TTL | Invalidation |
|-----------|-----|-------------|
| Real-time dashboards (today's attendance) | 5 minutes | Tag: `attendance` |
| Historical dashboards (trends, distributions) | 15 minutes | Tag: per-module |
| Precomputed table queries | Until next cron run | Tag: `precomputed:{table}` |
| Drilldown reports | 10 minutes | Tag: per-module |
| Exported files | 30 minutes | None (ephemeral) |

**Tag-based invalidation triggers**:
- Payroll run approved → invalidate `payroll` tag
- Attendance day-close → invalidate `attendance` tag
- Employee status change → invalidate `employee`, `workforce` tags
- Leave approved/rejected → invalidate `leave` tag

---

## 5. API Design

### 5.1 Route Structure

Base path: `GET /analytics/...`

```
# Dashboard endpoints (orchestrated responses)
GET /analytics/dashboard/executive
GET /analytics/dashboard/workforce
GET /analytics/dashboard/attendance
GET /analytics/dashboard/leave
GET /analytics/dashboard/payroll
GET /analytics/dashboard/compliance
GET /analytics/dashboard/performance
GET /analytics/dashboard/recruitment
GET /analytics/dashboard/attrition

# Drilldown endpoints (paginated tables)
GET /analytics/drilldown/attendance?type=register&month=3&year=2026
GET /analytics/drilldown/attendance?type=lateEmployees
GET /analytics/drilldown/attendance?type=overtime
GET /analytics/drilldown/payroll?type=salaryRegister&month=3&year=2026
GET /analytics/drilldown/payroll?type=loanOutstanding
GET /analytics/drilldown/performance?type=appraisalDetail
GET /analytics/drilldown/performance?type=skillGap
GET /analytics/drilldown/attrition?type=flightRisk
GET /analytics/drilldown/attrition?type=exitDetail
# ... (all drilldown types per dashboard)

# Export endpoints
GET /analytics/export/:reportType?format=excel&month=3&year=2026
GET /analytics/export/:reportType?format=pdf
GET /analytics/export/:reportType?format=csv

# Alert endpoints
GET  /analytics/alerts
GET  /analytics/alerts?dashboard=executive&severity=HIGH
POST /analytics/alerts/:id/acknowledge
POST /analytics/alerts/:id/resolve

# Admin endpoints
POST /analytics/recompute   # Manual recomputation trigger (company admin only)
```

### 5.2 Global Filter Parameters

All dashboard and drilldown endpoints accept these query parameters:

```typescript
interface DashboardFilters {
  dateFrom?: string       // ISO date (defaults: current month start)
  dateTo?: string         // ISO date (defaults: today)
  departmentId?: string   // filter by department
  locationId?: string     // filter by location
  gradeId?: string        // filter by grade
  employeeTypeId?: string // filter by employee type
  // Drilldowns additionally accept:
  page?: number
  limit?: number
  sortBy?: string
  sortOrder?: 'asc' | 'desc'
  search?: string
}
```

### 5.3 Dashboard Response Structure

Every dashboard endpoint returns this standardized shape:

```typescript
interface DashboardResponse<T> {
  success: true
  data: {
    kpis: KPICard[]                // Section A: top-level metrics
    trends: TrendSeries[]          // Section B: time-series data
    distributions: Distribution[]  // Section C: categorical breakdowns
    insights: Insight[]            // Section D: intelligence panel
    alerts: AnalyticsAlert[]       // Active alerts for this dashboard
    drilldownTypes: string[]       // Available drilldown options
    meta: {
      lastComputedAt: string       // When precomputed data was last refreshed
      version: number
      filtersApplied: DashboardFilters
      scope: 'full_org' | 'team' | 'personal'
    }
  }
}

interface KPICard {
  key: string           // unique identifier
  label: string         // "Headcount"
  value: number | string
  format: 'number' | 'currency' | 'percentage' | 'text'
  trend?: {
    direction: 'up' | 'down' | 'neutral'
    changePercent: number
    comparedTo: string  // "vs last month"
  }
}

interface TrendSeries {
  key: string
  label: string
  data: { date: string; value: number }[]
  chartType: 'line' | 'area' | 'bar'
}

interface Distribution {
  key: string
  label: string
  data: { label: string; value: number; color?: string }[]
  chartType: 'donut' | 'bar' | 'heatmap' | 'scatter' | 'funnel'
}
```

### 5.4 Permission Guards

```
GET /analytics/dashboard/*     → requirePermissions('hr:read') OR role-specific checks
GET /analytics/drilldown/*     → requirePermissions('hr:read') + metric-level filtering
GET /analytics/export/*        → requirePermissions('hr:export')
POST /analytics/alerts/*/acknowledge → requirePermissions('hr:read')
POST /analytics/recompute      → requirePermissions('hr:configure')
```

Finance role gets `hr:read` scoped to payroll + statutory dashboards only (enforced by `reportAccessResolver`).

---

## 6. Frontend — Dashboard Standard Layout

### 6.1 Standard Dashboard Page Template

Every dashboard follows this layout on both web and mobile:

```
Web Layout (desktop):
┌────────────────────────────────────────────────────────────┐
│  Global Filters Bar  [Date Range] [Dept] [Location] [Grade]│
├────────────────────────────────────────────────────────────┤
│  KPI Card  │  KPI Card  │  KPI Card  │  KPI Card          │
├────────────────────┬───────────────────────────────────────┤
│  Trend Chart       │  Distribution Chart                   │
│  (Line/Area)       │  (Donut/Bar/Heatmap)                 │
├────────────────────┴───────────────────────────────────────┤
│  🔥 Insights Panel                                        │
│  ┌──────────────────────────────────────────────────────┐ │
│  │ ⚠ Attrition spiked 12% in Engineering               │ │
│  │ ℹ Dept X has highest overtime cost                   │ │
│  │ 🔴 ESI filing overdue by 5 days                     │ │
│  └──────────────────────────────────────────────────────┘ │
├────────────────────────────────────────────────────────────┤
│  Drilldown Table (paginated, sortable, exportable)        │
│  [Export Excel] [Export PDF] [Export CSV]                  │
└────────────────────────────────────────────────────────────┘

Mobile Layout:
┌──────────────────────┐
│  Filter Icon (opens  │
│  bottom sheet)       │
├──────────────────────┤
│  KPI Card  KPI Card  │
│  KPI Card  KPI Card  │
├──────────────────────┤
│  Trend Chart (full)  │
├──────────────────────┤
│  Distribution Chart  │
├──────────────────────┤
│  Insights Panel      │
│  (collapsible)       │
├──────────────────────┤
│  Drilldown List      │
│  (tap to expand)     │
│  [Export button]     │
└──────────────────────┘
```

### 6.2 Shared Components (New)

**Web** (`web-system-app/src/components/analytics/`):

| Component | Purpose |
|-----------|---------|
| `DashboardShell.tsx` | Standard layout wrapper (filters + KPIs + charts + insights + table) |
| `GlobalFilters.tsx` | Shared filter bar (date range, dept, location, grade, type) |
| `KPIGrid.tsx` | Responsive grid of KPI cards with trend indicators |
| `InsightsPanel.tsx` | Collapsible panel showing insight items with severity badges |
| `AlertsBanner.tsx` | Top banner for critical/high alerts |
| `DrilldownTable.tsx` | Paginated table with sort, search, and export buttons |
| `TrendChart.tsx` | ECharts line/area chart wrapper |
| `DistributionChart.tsx` | ECharts donut/bar/heatmap wrapper |
| `ScatterChart.tsx` | ECharts scatter for Cost vs Performance |
| `FunnelChart.tsx` | ECharts funnel for recruitment pipeline |
| `HeatmapChart.tsx` | ECharts heatmap for leave density / attendance calendar |
| `ExportMenu.tsx` | Dropdown with Excel/PDF/CSV options |
| `ZeroDataState.tsx` | Empty state with sample visualization + onboarding hints |

**Mobile** (`mobile-app/src/components/analytics/`):

| Component | Purpose |
|-----------|---------|
| `DashboardShell.tsx` | Standard layout wrapper (scroll view with sections) |
| `FilterBottomSheet.tsx` | Bottom sheet for global filters |
| `KPIGrid.tsx` | 2-column grid of KPI cards |
| `InsightsPanel.tsx` | Collapsible accordion with insight items |
| `AlertsBanner.tsx` | Alert cards at top |
| `DrilldownList.tsx` | FlatList with expandable rows |
| `TrendChart.tsx` | Victory Native line/area chart |
| `DistributionChart.tsx` | Victory Native pie/bar chart |
| `ScatterChart.tsx` | Victory Native scatter chart |
| `HeatmapChart.tsx` | Custom SVG heatmap (Victory doesn't have native heatmap) |
| `ExportButton.tsx` | Export action sheet |
| `ZeroDataState.tsx` | Empty state with illustration + hints |

### 6.3 Chart Libraries

| Platform | Library | Package |
|----------|---------|---------|
| Web | ECharts | `echarts` + `echarts-for-react` |
| Mobile | Victory Native | `victory-native` (uses `react-native-svg` already installed) |

Chart types needed:
- **Line/Area**: Trends (headcount, attrition, payroll cost, attendance)
- **Bar**: Comparisons (dept-wise, grade-wise, source effectiveness)
- **Donut/Pie**: Distributions (gender, CTC bands, leave types, separation types)
- **Heatmap**: Attendance calendar, leave density, skill matrix
- **Scatter**: Cost vs Performance matrix
- **Funnel**: Recruitment pipeline
- **Gauge**: Compliance score, productivity index (optional, ECharts only)

### 6.4 Cross-Dashboard Navigation

Clicking entities navigates contextually:
- Employee name → Employee profile screen
- Department name → Same dashboard filtered by that department
- Insight with `drilldownType` → Drilldown table filtered to that context
- Alert → Relevant dashboard with filters pre-applied
- Dashboard KPI → Drilldown table for that metric

Implementation: React Router (web) / Expo Router (mobile) with query params for filter state.

### 6.5 Zero-Data UX

For new companies with no data:
- KPI cards show "—" with muted text
- Charts show sample/placeholder visualizations with "Sample Data" watermark
- Insights panel shows onboarding hints: "Start by adding employees to see workforce analytics"
- Drilldown table shows empty state with CTA to relevant module

Detection: If `lastComputedAt` is null or `meta.version` is 0, render zero-data state.

---

## 7. The 9 Dashboards — Detailed Specifications

### 7.1 Executive Overview

**Audience**: CEO, CXO, Company Admin
**Permission**: `hr:read` (full org scope)

| Section | Details |
|---------|---------|
| **KPIs** | Headcount (with MoM trend), Attrition % (annual rolling), Payroll Cost ₹ (MoM), Attendance % (today), Open Positions, Compliance Score (0-100) |
| **Trends** | Headcount trend (12mo line), Payroll cost trend (12mo area), Attrition trend (12mo line) |
| **Distributions** | Dept-wise headcount (horizontal bar), Cost by location (donut) |
| **Insights** | Top 3-5 cross-module insights (most critical from all dashboards) |
| **Alerts** | Full alert feed (all dashboards, sorted by severity) |
| **Drilldowns** | Each KPI links to its respective dashboard |

### 7.2 Workforce Analytics

**Audience**: HR, Company Admin
**Permission**: `hr:read`

| Section | Details |
|---------|---------|
| **KPIs** | Total employees, New joiners (month), Avg tenure (years), Vacancy rate % |
| **Trends** | Headcount movement (joiners vs leavers, dual-axis bar+line, 12mo) |
| **Distributions** | Gender ratio (donut), Age bands (bar), Dept strength actual vs sanctioned (grouped bar), Tenure bands (bar), Grade distribution (horizontal bar) |
| **Insights** | Vacancy alerts, tenure drops, demographic shifts |
| **Drilldowns** | `employeeDirectory`, `tenureReport`, `orgChart` |

### 7.3 Attendance & Productivity

**Audience**: HR, Managers (team scope)
**Permission**: `hr:read` (HR: full org, Manager: team)

| Section | Details |
|---------|---------|
| **KPIs** | Today's attendance %, Late arrivals count, Avg hours worked, Productivity index (0-1), OT hours (month) |
| **Trends** | Daily attendance trend (30 days, area), OT hours trend (bar), Productivity trend (line) |
| **Distributions** | Dept-wise attendance heatmap (heatmap: rows=depts, cols=days, color=%), Source breakdown (donut), Shift adherence (bar) |
| **Insights** | Under-utilized teams, late arrival spikes, OT cost warnings, missed punch alerts |
| **Drilldowns** | `register` (full month grid), `lateEmployees`, `overtime`, `absenteeism`, `missedPunches` |

### 7.4 Leave & Availability

**Audience**: HR, Managers (team scope)
**Permission**: `hr:read`

| Section | Details |
|---------|---------|
| **KPIs** | Avg leave balance (days), Leave utilization %, Pending approvals, Encashment liability ₹ |
| **Trends** | Monthly leave consumption by type (stacked bar, 12mo) |
| **Distributions** | Leave density heatmap (calendar: rows=months, cols=days, color=leave count), Type-wise utilization (donut), Dept-wise utilization (bar) |
| **Insights** | Peak leave months, encashment liability, approval backlogs, sandwich leave patterns |
| **Drilldowns** | `leaveBalance`, `leaveRequests`, `encashmentEligible`, `pendingApprovals` |

### 7.5 Payroll & Cost Intelligence

**Audience**: HR, Finance, Company Admin
**Permission**: `hr:read` (Finance: payroll metrics only)

| Section | Details |
|---------|---------|
| **KPIs** | Total payroll cost ₹ (MoM trend), Avg CTC ₹, MoM variance %, Exception count |
| **Trends** | Payroll cost trend (12mo area), CTC growth trend (line) |
| **Distributions** | Dept-wise cost (bar), CTC band distribution (bar), Component breakup earnings vs deductions (donut), **Cost vs Performance scatter** (X=CTC, Y=Rating, quadrants labeled) |
| **Insights** | Cost spike departments, high-cost/low-performance employees, loan concentration, salary hold aging |
| **Drilldowns** | `salaryRegister`, `bankFile`, `pfECR`, `esiChallan`, `ptChallan`, `varianceReport`, `loanOutstanding`, `ctcBand`, `revisions`, `exceptions` |

### 7.6 Compliance & Risk

**Audience**: HR, Finance, Company Admin
**Permission**: `hr:read`

| Section | Details |
|---------|---------|
| **KPIs** | Compliance score (0-100, gauge), Overdue filings, Pending grievances, Active disciplinary cases |
| **Trends** | Filing compliance trend (12mo line), Grievance resolution trend (line) |
| **Distributions** | Filing status by type (PF/ESI/PT/TDS — stacked bar: filed/pending/overdue), Grievance by category (bar), Disciplinary by type (donut) |
| **Insights** | Overdue filings, min wage violations, PIP aging, grievance SLA breaches |
| **Alerts** | Compliance deadline calendar (upcoming 30 days) |
| **Drilldowns** | `filingTracker`, `grievanceCases`, `disciplinaryActions`, `documentCompliance`, `minWageCheck`, `probationReviews` |

### 7.7 Performance & Talent Intelligence

**Audience**: HR, Company Admin
**Permission**: `hr:read`

| Section | Details |
|---------|---------|
| **KPIs** | Appraisal completion %, Avg rating, Skill coverage %, Succession coverage % |
| **Trends** | Rating trend by cycle (line), Goal achievement trend (bar) |
| **Distributions** | Bell curve actual vs expected (overlay bar), **9-box grid** (scatter: X=performance, Y=potential, bubble size=employee count), Skill gap heatmap (rows=skills, cols=depts, color=gap severity) |
| **Manager Effectiveness Table** | Per manager: team size, team avg rating, team attrition %, avg approval delay — sortable, with effectiveness score |
| **Insights** | Bell curve skew, unreviewed employees, critical roles without successors, manager outliers |
| **Drilldowns** | `appraisalDetail`, `goalTracker`, `skillGap`, `successionPlans`, `promotionReport`, `managerDetail` |

### 7.8 Recruitment Intelligence

**Audience**: HR, Company Admin
**Permission**: `hr:read`

| Section | Details |
|---------|---------|
| **KPIs** | Open positions, Pipeline count, Avg time-to-hire (days), Offer acceptance rate % |
| **Trends** | Hiring velocity (filled/month bar, 12mo), Time-to-hire trend (line) |
| **Distributions** | **Recruitment funnel** (funnel: Applied → Shortlisted → HR Round → Technical → Final → Offer → Hired, with conversion % between stages), Source effectiveness (grouped bar: applications vs hires by source) |
| **Insights** | Bottleneck stages, aging positions (>60 days), source ROI, low acceptance rate alerts |
| **Drilldowns** | `requisitionTracker`, `candidatePipeline`, `interviewSchedule`, `offerTracking`, `sourceAnalysis` |

### 7.9 Attrition & Retention Intelligence (Flagship)

**Audience**: HR, Company Admin
**Permission**: `hr:read`

| Section | Details |
|---------|---------|
| **KPIs** | Attrition rate % (monthly + annual rolling), Voluntary vs Involuntary %, Avg tenure at exit (months), Pending F&F count |
| **Trends** | Attrition trend (12mo line, voluntary vs involuntary stacked), Early attrition trend (line), Dept-wise attrition (grouped bar) |
| **Distributions** | Separation type breakdown (donut), Exit reasons from interviews (horizontal bar), Tenure band at exit (bar) |
| **Flight Risk Panel** | Top 10-20 employees with risk score (0-100), contributing factors listed, link to employee profile |
| **Insights** | Dept-specific attrition spikes, common exit reasons, high-performer exits, onboarding failure rate, F&F processing delays |
| **Drilldowns** | `exitDetail`, `exitInterviewAnalysis`, `fnfTracker`, `flightRisk`, `earlyAttrition`, `retentionActions` |

---

## 8. Export System

### 8.1 Supported Formats

| Format | Library | Use Case |
|--------|---------|----------|
| Excel (.xlsx) | `exceljs` | Drilldown tables, statutory reports, salary register |
| PDF | `@react-pdf/renderer` (existing) or `pdfkit` | Form 16, payslips, summary reports |
| CSV | Built-in (string processing) | Quick data exports, already exists in payroll reports |

### 8.2 Export Flow

1. User clicks export button on drilldown table
2. Frontend calls `GET /analytics/export/:reportType?format=excel&...filters`
3. Backend: `report-aggregator.service.ts` fetches data with same filters + scope
4. Backend: `excel-exporter.ts` or `pdf-exporter.ts` generates file
5. Response: file buffer with `Content-Disposition: attachment` header
6. Audit log entry created

### 8.3 Scheduled Reports (Future Phase)

Extend existing `NotificationRule` model to support scheduled report delivery:
- Weekly/monthly digest emails to company admin
- Configurable: which dashboards, which format
- Uses existing notification infrastructure + cron

---

## 9. Navigation & Permissions

### 9.1 Navigation Manifest Entries

Add to `NAVIGATION_MANIFEST` in backend:

| Route Key | Label | Group | Permission | Sort Order |
|-----------|-------|-------|------------|-----------|
| `hr-analytics` | Analytics Hub | HR Analytics | `hr:read` | 450 |
| `hr-analytics-executive` | Executive Overview | HR Analytics | `hr:read` | 451 |
| `hr-analytics-workforce` | Workforce Analytics | HR Analytics | `hr:read` | 452 |
| `hr-analytics-attendance` | Attendance & Productivity | HR Analytics | `hr:read` | 453 |
| `hr-analytics-leave` | Leave & Availability | HR Analytics | `hr:read` | 454 |
| `hr-analytics-payroll` | Payroll & Cost Intelligence | HR Analytics | `hr:read` | 455 |
| `hr-analytics-compliance` | Compliance & Risk | HR Analytics | `hr:read` | 456 |
| `hr-analytics-performance` | Performance & Talent | HR Analytics | `hr:read` | 457 |
| `hr-analytics-recruitment` | Recruitment Intelligence | HR Analytics | `hr:read` | 458 |
| `hr-analytics-attrition` | Attrition & Retention | HR Analytics | `hr:read` | 459 |

**Note**: Sort order 450-459 places analytics BEFORE the existing Org Structure group (500+) without requiring any changes to existing navigation manifest entries. Analytics appears as the first HR section in the sidebar.

### 9.2 Role-Based Dashboard Visibility

Controlled by `reportAccessResolver()`:

| Role | Visible Dashboards | Data Scope |
|------|-------------------|------------|
| Employee | None (personal KPIs in ESS) | Own data |
| Manager | Attendance, Leave, Performance (team panels) | Direct reports |
| HR Personnel | All 9 dashboards | Full org |
| Finance | Executive (partial), Payroll, Compliance | Payroll + statutory only |
| Company Admin / CXO | All 9 dashboards | Full org |

### 9.3 Permission-Aware Metrics

Finance users accessing Payroll dashboard will NOT see:
- Performance ratings
- Attrition reasons
- Grievance details
- Individual employee names (aggregated only)

Manager users will NOT see:
- Salary details of team members
- Org-wide metrics (only team-scoped)

Implemented by `reportAccess.filterMetrics()` which strips unauthorized fields from the response before returning to the orchestrator.

---

## 10. Testing Strategy

### 10.1 Backend Tests

| Category | Scope | Examples |
|----------|-------|---------|
| **Unit: Cron populators** | Each precomputed table populator | Verify correct aggregation from source tables |
| **Unit: Rule engine** | Each rule file | Verify threshold triggers, insight text generation |
| **Unit: Scoring engine** | Each scoring function | Verify weighted score calculation, edge cases |
| **Unit: Anomaly detection** | Detector functions | Verify z-score calculation, threshold classification |
| **Integration: Orchestrator** | Dashboard endpoints | Verify parallel query composition, filter application |
| **Integration: Access control** | Role-based scoping | Verify data isolation per role |
| **Integration: Multi-tenant** | Cross-tenant isolation | **Critical**: Verify Company A cannot see Company B data |
| **Edge cases** | All services | Empty data (new company), partial months, single employee, zero attendance |
| **Accuracy** | Report aggregator | Compare aggregated results against raw query results |
| **Performance** | Dashboard endpoints | Load test with realistic data volumes (1000+ employees) |

### 10.2 Frontend Tests

| Category | Scope |
|----------|-------|
| Component: DashboardShell | Renders all sections, passes filters |
| Component: Charts | Renders with data, handles empty state |
| Component: ZeroDataState | Shows when no data |
| Integration: Filter → Query | Filter changes trigger correct API calls |
| Integration: Drilldown navigation | Click KPI → correct drilldown |

---

## 11. Implementation Phases

### Phase 1: Foundation (Backend Data Layer)
- Prisma schema: 4 precomputed tables + Alert + AuditLog models
- Migration + generate
- Analytics cron service (all 4 populators)
- Report access service
- Analytics audit service
- Redis tag-based caching

### Phase 2: Intelligence Engine (Backend)
- Rule engine (all 6 rule files)
- Scoring engine (attrition, manager, productivity, compliance)
- Anomaly detection
- Alert service
- Insights engine orchestrator

### Phase 3: Analytics & Orchestrator (Backend)
- Analytics service (all query methods)
- Dashboard orchestrator (all 9 dashboards)
- Report aggregator (all drilldown reports)
- API routes + validators + controllers
- Export service (Excel, PDF, CSV)

### Phase 4: Web Dashboards
- Install ECharts (`echarts` + `echarts-for-react`)
- Install `exceljs` (for client-side export if needed)
- Shared analytics components (DashboardShell, GlobalFilters, charts, InsightsPanel, etc.)
- 9 dashboard screens
- Drilldown tables with export
- Zero-data UX
- Route setup + navigation manifest integration

### Phase 5: Mobile Dashboards
- Install Victory Native (`victory-native`)
- Shared analytics components (mobile variants)
- 9 dashboard screens
- Filter bottom sheet
- Drilldown lists with export
- Zero-data UX
- Route setup

### Phase 6: Testing & Polish
- Backend unit + integration tests
- Cross-tenant isolation tests
- Frontend component tests
- Performance testing
- Edge case handling

---

## 12. Dependencies & New Packages

### Backend
| Package | Purpose |
|---------|---------|
| `exceljs` | Excel export generation (not currently installed — must add) |
| `node-cron` | Scheduled analytics computation (already installed: `^3.0.3`) |

### Web
| Package | Purpose |
|---------|---------|
| `echarts` | Core charting engine |
| `echarts-for-react` | React wrapper for ECharts |

### Mobile
| Package | Purpose |
|---------|---------|
| `victory-native` | React Native charting (uses existing `react-native-svg`) |

---

## 13. Performance Considerations

- **Precomputed tables** eliminate expensive real-time aggregation queries
- **Parallel queries** in orchestrator (Promise.all) minimize dashboard load time
- **Tag-based cache** avoids stale data without aggressive TTLs
- **Pagination** on all drilldown tables (no unbounded queries)
- **Index strategy**: Composite indexes on `[companyId, date]` for all precomputed tables
- **Version cleanup**: 90-day retention on precomputed table versions
- **Target**: Dashboard load < 2 seconds, drilldown load < 1 second
