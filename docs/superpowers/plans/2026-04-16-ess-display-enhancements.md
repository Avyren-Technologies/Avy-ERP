# ESS & Display Enhancements — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Fix 15 display gaps where data is collected/calculated but not shown to employees or admins — attendance dashboard enhancements, employee payslip improvements, and leave display gaps.

**Architecture:** Mostly frontend changes with minor backend additions (YTD computation, leave balance enrichment). Both web and mobile get matching updates.

**Tech Stack:** React, React Native, Tailwind, NativeWind, React Query, @react-google-maps/api

**Spec:** `docs/superpowers/specs/2026-04-16-ess-display-enhancements-design.md`

---

## File Structure

### Modified Files — Backend
| File | Change |
|------|--------|
| `avy-erp-backend/src/modules/hr/ess/ess.service.ts` | Enrich payslip detail with YTD + leave balance; enrich leave balance with breakdown |
| `avy-erp-backend/src/modules/hr/leave/leave.service.ts` | Add sandwich days to leave application response |

### Modified Files — Web
| File | Change |
|------|--------|
| `web-system-app/src/features/company-admin/hr/AttendanceDashboardScreen.tsx` | Add geoStatus badge, break deduction, map view, resolution trace |
| `web-system-app/src/features/company-admin/hr/MyAttendanceScreen.tsx` | Add GPS, geoStatus to day detail |
| `web-system-app/src/features/company-admin/hr/MyPayslipsScreen.tsx` | Add employer contributions, OT breakdown, LOP detail, YTD, leave balance |
| `web-system-app/src/features/company-admin/hr/MyLeaveScreen.tsx` | Add carry-forward breakdown, accrual schedule, encashment |

### Modified Files — Mobile
| File | Change |
|------|--------|
| `mobile-app/src/features/company-admin/hr/my-attendance-screen.tsx` | Add GPS, geoStatus, break deduction |
| `mobile-app/src/features/company-admin/hr/my-payslips-screen.tsx` (or payslip-screen.tsx) | Add OT breakdown, LOP detail, YTD, leave balance |
| `mobile-app/src/features/company-admin/hr/my-leave-screen.tsx` | Add carry-forward breakdown, accrual schedule, encashment |

---

## Task 1: Backend — Enrich Payslip Detail with YTD + Leave Balance

**Files:**
- Modify: `avy-erp-backend/src/modules/hr/ess/ess.service.ts`

- [ ] **Step 1: Add YTD computation to payslip detail endpoint**

Find the method that returns payslip detail for the employee (likely in ess.service.ts or payroll-run.service.ts — the endpoint `GET /ess/my-payslips/:id` or similar). After fetching the payslip, add YTD computation:

```typescript
    // E10: YTD totals
    const fyStartMonth = 4; // April
    const fyStartYear = payslip.month >= 4 ? payslip.year : payslip.year - 1;
    const fyStart = new Date(Date.UTC(fyStartYear, fyStartMonth - 1, 1));
    const currentMonthEnd = new Date(Date.UTC(payslip.year, payslip.month, 1));

    const ytdPayslips = await platformPrisma.payslip.findMany({
      where: {
        employeeId: payslip.employeeId,
        companyId,
        OR: [
          { year: fyStartYear, month: { gte: fyStartMonth } },
          { year: fyStartYear + 1, month: { lt: fyStartMonth } },
        ],
        createdAt: { lte: currentMonthEnd },
      },
      select: { grossEarnings: true, totalDeductions: true, netPay: true, tdsAmount: true },
    });

    const ytd = {
      grossEarnings: ytdPayslips.reduce((s, p) => s + Number(p.grossEarnings ?? 0), 0),
      totalDeductions: ytdPayslips.reduce((s, p) => s + Number(p.totalDeductions ?? 0), 0),
      netPay: ytdPayslips.reduce((s, p) => s + Number(p.netPay ?? 0), 0),
      tdsAmount: ytdPayslips.reduce((s, p) => s + Number(p.tdsAmount ?? 0), 0),
    };
```

- [ ] **Step 2: Add leave balance to payslip detail**

```typescript
    // E11: Leave balance as of this payslip month
    const leaveBalances = await platformPrisma.leaveBalance.findMany({
      where: { employeeId: payslip.employeeId, companyId, year: payslip.year },
      include: { leaveType: { select: { name: true, code: true } } },
    });

    const leaveBalanceSummary = leaveBalances.map(b => ({
      type: b.leaveType.name,
      code: b.leaveType.code,
      balance: Number(b.balance),
      used: Number(b.taken),
      total: Number(b.openingBalance) + Number(b.accrued) + Number(b.adjusted),
    }));
```

Return both `ytd` and `leaveBalanceSummary` in the payslip detail response.

- [ ] **Step 3: Commit**

```bash
cd /Users/chetan/Documents/Avyren-Technologies/Products/Mobile-ERP/avy-erp-backend
git add src/modules/hr/ess/ess.service.ts
git commit -m "feat(ess): add YTD totals and leave balance to payslip detail response"
```

---

## Task 2: Backend — Enrich Leave Balance with Breakdown

**Files:**
- Modify: `avy-erp-backend/src/modules/hr/ess/ess.service.ts`

- [ ] **Step 1: Add breakdown fields to leave balance response**

Find `getMyLeaveBalance` (line ~1656). The current query returns raw LeaveBalance records. Enrich the response:

```typescript
    // E18: Include breakdown + E16: accrual info + E2: encashment info
    const enriched = balances.map(b => ({
      id: b.id,
      leaveType: b.leaveType,
      // Balance breakdown
      openingBalance: Number(b.openingBalance),
      accrued: Number(b.accrued),
      taken: Number(b.taken),
      adjusted: Number(b.adjusted),
      balance: Number(b.balance),
      expiresAt: b.expiresAt?.toISOString() ?? null,
      // E16: Accrual info (from leave type)
      accrualFrequency: b.leaveType.accrualFrequency ?? null,
      // E2: Encashment info
      encashmentAllowed: b.leaveType.encashmentAllowed ?? false,
      maxEncashableDays: b.leaveType.maxEncashableDays ?? null,
    }));
    return enriched;
```

Update the LeaveType select to include `accrualFrequency`, `encashmentAllowed`, `maxEncashableDays`:

```typescript
    include: {
      leaveType: {
        select: { id: true, name: true, code: true, category: true, accrualFrequency: true, encashmentAllowed: true, maxEncashableDays: true },
      },
    },
```

- [ ] **Step 2: Commit**

```bash
cd /Users/chetan/Documents/Avyren-Technologies/Products/Mobile-ERP/avy-erp-backend
git add src/modules/hr/ess/ess.service.ts
git commit -m "feat(ess): enrich leave balance with breakdown, accrual, and encashment info"
```

---

## Task 3: Web — Attendance Dashboard Enhancements (A10, A12, A13, E12)

**Files:**
- Modify: `web-system-app/src/features/company-admin/hr/AttendanceDashboardScreen.tsx:740-770`

- [ ] **Step 1: Add geoStatus badge to detail modal**

In the detail modal (around line 750), after the geo coordinates display, add:

```tsx
{/* A10: Geofence Status */}
{detail.geoStatus && (
  <div className="flex items-center gap-2">
    <span className="text-xs text-neutral-500">Geofence:</span>
    <span className={cn(
      "text-xs font-bold px-2 py-0.5 rounded-full",
      detail.geoStatus === 'INSIDE_GEOFENCE' && "bg-success-50 text-success-700",
      detail.geoStatus === 'OUTSIDE_GEOFENCE' && "bg-danger-50 text-danger-700",
      detail.geoStatus === 'NO_LOCATION' && "bg-neutral-100 text-neutral-500",
    )}>
      {detail.geoStatus === 'INSIDE_GEOFENCE' ? 'Inside Geofence' :
       detail.geoStatus === 'OUTSIDE_GEOFENCE' ? 'Outside Geofence' : 'No Location'}
    </span>
  </div>
)}
```

- [ ] **Step 2: Add break deduction display**

```tsx
{/* A13: Break deduction */}
{detail.appliedBreakDeductionMinutes > 0 && (
  <div className="flex justify-between text-xs">
    <span className="text-neutral-500">Break Deduction</span>
    <span>{detail.appliedBreakDeductionMinutes} min</span>
  </div>
)}
```

- [ ] **Step 3: Add resolution trace (collapsible, admin only)**

```tsx
{/* A12: Resolution Trace */}
{detail.resolutionTrace && (
  <details className="mt-3 border-t pt-2">
    <summary className="text-xs font-medium text-neutral-500 cursor-pointer">Policy Applied</summary>
    <div className="mt-1 text-xs text-neutral-400 space-y-1">
      {Object.entries(detail.resolutionTrace as Record<string, any>).map(([key, value]) => (
        <div key={key} className="flex justify-between">
          <span>{key}</span>
          <span className="font-mono">{String(value)}</span>
        </div>
      ))}
    </div>
  </details>
)}
```

- [ ] **Step 4: Add mini map for GPS (E12)**

Import Google Maps (already installed):
```tsx
import { GoogleMap, Marker, useJsApiLoader } from '@react-google-maps/api';
```

Add map component in the detail modal after geo coordinates:
```tsx
{/* E12: Location Map */}
{(detail.checkInLatitude && detail.checkInLongitude) && (
  <div className="h-40 rounded-lg overflow-hidden mt-2">
    <GoogleMap
      mapContainerStyle={{ width: '100%', height: '100%' }}
      center={{ lat: Number(detail.checkInLatitude), lng: Number(detail.checkInLongitude) }}
      zoom={15}
    >
      <Marker position={{ lat: Number(detail.checkInLatitude), lng: Number(detail.checkInLongitude) }} label="In" />
      {detail.checkOutLatitude && detail.checkOutLongitude && (
        <Marker position={{ lat: Number(detail.checkOutLatitude), lng: Number(detail.checkOutLongitude) }} label="Out" />
      )}
    </GoogleMap>
  </div>
)}
```

Ensure the Google Maps API key is available (check existing usage in GeofenceManager).

- [ ] **Step 5: Verify API returns these fields**

Check that the backend attendance detail API includes `geoStatus`, `appliedBreakDeductionMinutes`, `resolutionTrace`, and GPS fields in the select/include. Add if missing.

- [ ] **Step 6: Commit**

```bash
cd /Users/chetan/Documents/Avyren-Technologies/Products/Mobile-ERP/web-system-app
git add src/features/company-admin/hr/AttendanceDashboardScreen.tsx
git commit -m "feat(web): add geoStatus, break deduction, resolution trace, and map to attendance dashboard"
```

---

## Task 4: Web + Mobile — Employee Attendance Detail (A10, A11, A13)

**Files:**
- Modify: `web-system-app/src/features/company-admin/hr/MyAttendanceScreen.tsx`
- Modify: `mobile-app/src/features/company-admin/hr/my-attendance-screen.tsx:381-395`

- [ ] **Step 1: Web — add GPS + geoStatus to day detail**

In `MyAttendanceScreen.tsx`, find the selected day detail card and add:
- Geofence status badge (same as dashboard)
- Location text: "Location: lat, lng" (only if GPS available)
- Break deduction (if > 0)

- [ ] **Step 2: Mobile — add GPS + geoStatus to day detail card**

In `my-attendance-screen.tsx` (lines 381-395), after the "Hours Worked" row, add:

```tsx
{selectedRecord.geoStatus && (
  <View style={styles.detailRow}>
    <Text className="font-inter text-xs text-neutral-500">Geofence</Text>
    <Text className={`font-inter text-xs font-bold ${
      selectedRecord.geoStatus === 'INSIDE_GEOFENCE' ? 'text-success-600' :
      selectedRecord.geoStatus === 'OUTSIDE_GEOFENCE' ? 'text-danger-600' : 'text-neutral-400'
    }`}>
      {selectedRecord.geoStatus === 'INSIDE_GEOFENCE' ? 'Inside' :
       selectedRecord.geoStatus === 'OUTSIDE_GEOFENCE' ? 'Outside' : 'N/A'}
    </Text>
  </View>
)}
{selectedRecord.checkInLatitude && (
  <View style={styles.detailRow}>
    <Text className="font-inter text-xs text-neutral-500">Location</Text>
    <Text className="font-inter text-xs text-neutral-700 dark:text-neutral-300">
      {Number(selectedRecord.checkInLatitude).toFixed(4)}, {Number(selectedRecord.checkInLongitude).toFixed(4)}
    </Text>
  </View>
)}
{selectedRecord.appliedBreakDeductionMinutes > 0 && (
  <View style={styles.detailRow}>
    <Text className="font-inter text-xs text-neutral-500">Break Deducted</Text>
    <Text className="font-inter text-xs text-neutral-700 dark:text-neutral-300">
      {selectedRecord.appliedBreakDeductionMinutes} min
    </Text>
  </View>
)}
```

Ensure the API response includes these fields for MyAttendance endpoint.

- [ ] **Step 3: Commit**

```bash
cd /Users/chetan/Documents/Avyren-Technologies/Products/Mobile-ERP
git add web-system-app/ mobile-app/
git commit -m "feat(ui): add GPS, geoStatus, break deduction to employee attendance detail"
```

---

## Task 5: Web — Employee Payslip Enhancements (E5, E6-E9, E10, E11)

**Files:**
- Modify: `web-system-app/src/features/company-admin/hr/MyPayslipsScreen.tsx:210-260`

- [ ] **Step 1: Add employer contributions section (E5)**

After the Deductions section (around line 250), add:

```tsx
{/* E5: Employer Contributions */}
{detail.employerContributions && Object.keys(detail.employerContributions).length > 0 && (
  <div className="mt-4">
    <h4 className="text-sm font-semibold text-neutral-700 dark:text-neutral-300 mb-2">Employer Contributions</h4>
    {Object.entries(detail.employerContributions).map(([code, amount]) => (
      <div key={code} className="flex justify-between text-sm py-1">
        <span className="text-neutral-500">{COMPONENT_LABELS[code] ?? code}</span>
        <span>{formatCurrency(Number(amount))}</span>
      </div>
    ))}
  </div>
)}
```

Add component labels map at top:
```typescript
const COMPONENT_LABELS: Record<string, string> = {
  PF_EMPLOYER: 'Provident Fund (Employer)',
  ESI_EMPLOYER: 'ESI (Employer)',
  LWF_EMPLOYER: 'LWF (Employer)',
  GRATUITY_PROVISION: 'Gratuity Provision',
};
```

- [ ] **Step 2: Add OT breakdown (E6) and LOP detail (E7-E8)**

After the earnings section:

```tsx
{/* E6: OT Breakdown */}
{detail.overtimeAmount && Number(detail.overtimeAmount) > 0 && (
  <div className="flex justify-between text-sm py-1">
    <span className="text-neutral-500">Overtime ({detail.overtimeHours ?? 0} hrs)</span>
    <span>{formatCurrency(Number(detail.overtimeAmount))}</span>
  </div>
)}

{/* E7-E8: LOP Detail */}
{detail.lopDays && Number(detail.lopDays) > 0 && (
  <div className="text-xs text-neutral-400 mt-1">
    LOP: {Number(detail.lopDays)} days (Working: {detail.workingDays}, Present: {Number(detail.presentDays)})
  </div>
)}

{/* E9: TDS Provisional note */}
{detail.tdsProvisional && (
  <div className="text-xs text-warning-500 mt-1">* TDS amount is provisional</div>
)}
```

- [ ] **Step 3: Add YTD section (E10)**

At the bottom of the detail modal:

```tsx
{/* E10: Year-to-Date */}
{detail.ytd && (
  <div className="mt-4 pt-3 border-t">
    <h4 className="text-sm font-semibold text-neutral-700 dark:text-neutral-300 mb-2">Year-to-Date (FY {detail.ytd.fyLabel})</h4>
    <div className="grid grid-cols-2 gap-2 text-xs">
      <div><span className="text-neutral-500">Gross:</span> <span className="font-mono">{formatCurrency(detail.ytd.grossEarnings)}</span></div>
      <div><span className="text-neutral-500">Deductions:</span> <span className="font-mono">{formatCurrency(detail.ytd.totalDeductions)}</span></div>
      <div><span className="text-neutral-500">TDS:</span> <span className="font-mono">{formatCurrency(detail.ytd.tdsAmount)}</span></div>
      <div><span className="text-neutral-500">Net:</span> <span className="font-mono font-bold">{formatCurrency(detail.ytd.netPay)}</span></div>
    </div>
  </div>
)}
```

- [ ] **Step 4: Add leave balance section (E11)**

```tsx
{/* E11: Leave Balance */}
{detail.leaveBalance && detail.leaveBalance.length > 0 && (
  <div className="mt-3 pt-3 border-t">
    <h4 className="text-xs font-semibold text-neutral-500 mb-1">Leave Balance</h4>
    <div className="flex flex-wrap gap-3">
      {detail.leaveBalance.map((l: any) => (
        <span key={l.code} className="text-xs">
          <span className="text-neutral-400">{l.code}:</span>{' '}
          <span className="font-mono">{l.balance}/{l.total}</span>
        </span>
      ))}
    </div>
  </div>
)}
```

- [ ] **Step 5: Commit**

```bash
cd /Users/chetan/Documents/Avyren-Technologies/Products/Mobile-ERP/web-system-app
git add src/features/company-admin/hr/MyPayslipsScreen.tsx
git commit -m "feat(web): add employer contributions, OT/LOP detail, YTD, leave balance to employee payslip"
```

---

## Task 6: Mobile — Payslip Enhancements

**Files:**
- Modify: `mobile-app/src/features/company-admin/hr/` payslip screen (find exact file)

- [ ] **Step 1: Add same enhancements as web**

Mirror the web changes in the mobile payslip detail view:
- Employer contributions section
- OT hours + amount
- LOP detail text
- TDS provisional note
- YTD section
- Leave balance footer

Follow mobile patterns: `StyleSheet.create()`, `font-inter`, `useCompanyFormatter()`.

- [ ] **Step 2: Commit**

```bash
cd /Users/chetan/Documents/Avyren-Technologies/Products/Mobile-ERP/mobile-app
git add src/features/company-admin/hr/
git commit -m "feat(mobile): add employer contributions, OT/LOP detail, YTD, leave balance to payslip"
```

---

## Task 7: Web + Mobile — Leave Balance Enhancements (E2, E16, E17, E18)

**Files:**
- Modify: `web-system-app/src/features/company-admin/hr/MyLeaveScreen.tsx:181-214`
- Modify: `mobile-app/src/features/company-admin/hr/my-leave-screen.tsx:102-124`

- [ ] **Step 1: Web — show carry-forward breakdown (E18)**

In `MyLeaveScreen.tsx`, replace the simple "used / entitled" display with a breakdown:

```tsx
<p className="text-[10px] text-neutral-400 mt-0.5">
  {b.openingBalance > 0 && `CF: ${b.openingBalance} · `}
  Accrued: {b.accrued} · Used: {b.taken}
  {b.adjusted !== 0 && ` · Adj: ${b.adjusted}`}
</p>
```

- [ ] **Step 2: Web — show accrual schedule (E16)**

Below the balance card:
```tsx
{b.accrualFrequency && (
  <p className="text-[9px] text-neutral-400 mt-0.5">
    Accrual: {b.accrualFrequency.toLowerCase()}
  </p>
)}
```

- [ ] **Step 3: Web — show encashment indicator (E2)**

```tsx
{b.encashmentAllowed && (
  <p className="text-[9px] text-accent-500 mt-0.5">
    Encashable{b.maxEncashableDays ? ` (max ${b.maxEncashableDays} days)` : ''}
  </p>
)}
```

- [ ] **Step 4: Mobile — same changes**

In `my-leave-screen.tsx` BalanceCard component (lines 102-124), add the same breakdown, accrual, and encashment indicators using mobile patterns:

```tsx
<Text className="font-inter text-[9px] text-neutral-400">
  {item.openingBalance > 0 ? `CF: ${item.openingBalance} · ` : ''}
  Accrued: {item.accrued} · Used: {item.used}
</Text>
{item.accrualFrequency && (
  <Text className="font-inter text-[8px] text-neutral-400 mt-0.5">
    Accrual: {item.accrualFrequency.toLowerCase()}
  </Text>
)}
{item.encashmentAllowed && (
  <Text className="font-inter text-[8px] text-accent-500 mt-0.5">
    Encashable
  </Text>
)}
```

- [ ] **Step 5: Commit**

```bash
cd /Users/chetan/Documents/Avyren-Technologies/Products/Mobile-ERP
git add web-system-app/ mobile-app/
git commit -m "feat(ui): add leave carry-forward breakdown, accrual schedule, and encashment indicator"
```

---

## Task 8: Type Check & Lint

- [ ] **Step 1: Backend**
```bash
cd avy-erp-backend && pnpm build
```

- [ ] **Step 2: Web + Mobile**
```bash
cd web-system-app && pnpm build
cd mobile-app && pnpm type-check
```

- [ ] **Step 3: Fix any errors and commit**
