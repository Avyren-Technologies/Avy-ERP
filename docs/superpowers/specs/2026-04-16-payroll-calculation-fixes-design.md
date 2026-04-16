# Sub-project 2: Payroll Calculation Fixes — Design Spec

## Goal

Fix 5 payroll gaps: arrears consumption in payroll, salary hold earnings reduction, gratuity monthly provision, TDS relief/Section 87A, and VPF rate cap.

## Verified Gaps

| # | Gap | Current State |
|---|-----|---------------|
| P1 | Gratuity monthly provision | `GratuityConfig.provisionMethod='MONTHLY'` exists but payroll has zero gratuity code |
| P3 | Arrears created but never consumed | `applySalaryRevision()` creates ArrearEntry records but `computeSalaries()` never fetches or includes them |
| P6 | Salary hold doesn't reduce earnings | Hold flagged as exception but `grossEarnings` never modified |
| P7 | No TDS relief/Section 87A | Zero code for tax rebates or adjustments |
| P8 | VPF rate uncapped | Employee `vpfPercentage` applied without max rate validation |

---

## Fix P3: Arrears Consumption in Payroll (CRITICAL)

### Current Flow
1. Salary revision approved → `applySalaryRevision()` creates ArrearEntry records per month
2. ArrearEntry has: `forMonth`, `forYear`, `components` (JSON), `totalAmount`, `payrollRunId` (always null)
3. `computeSalaries()` runs → **never fetches ArrearEntry** → arrears never appear in payroll

### Fixed Flow

**Schema Addition** — Add `arrearsAmount` to PayrollEntry and Payslip models:

In `prisma/modules/hrms/payroll-run.prisma`:
```prisma
// In PayrollEntry (after overtimeAmount, line 56):
  arrearsAmount     Decimal?   @db.Decimal(15, 2)

// In Payslip (after overtimeAmount, line 107):
  arrearsAmount     Decimal?   @db.Decimal(15, 2)
```

**Payroll Run Changes** — In `payroll-run.service.ts` `computeSalaries()`:

1. **Batch-fetch unpaid arrears** (alongside existing attendance/OT batch-fetches, around line 476):
```typescript
const allArrears = await platformPrisma.arrearEntry.findMany({
  where: { companyId, payrollRunId: null }, // Unpaid arrears only
  select: { employeeId: true, totalAmount: true, components: true, id: true, forMonth: true, forYear: true },
});
const arrearsByEmployee = groupBy(allArrears, 'employeeId');
```

2. **Add arrears to gross earnings** (in the per-employee loop, after OT calculation):
```typescript
const empArrears = arrearsByEmployee[emp.id] ?? [];
let arrearsAmount = 0;
for (const arrear of empArrears) {
  arrearsAmount += Number(arrear.totalAmount);
}
grossEarnings += arrearsAmount;
```

3. **Store on PayrollEntry**:
```typescript
arrearsAmount: arrearsAmount || null,
```

4. **Flag in reviewExceptions** (Step 2): Arrears appear as an exception for HR review:
```typescript
if (empArrears.length > 0) {
  exceptions.push({
    employeeId: emp.id,
    type: 'ARREARS_PENDING',
    note: `${empArrears.length} arrear entries totaling ₹${arrearsAmount.toFixed(2)} will be included`,
    arrearEntryIds: empArrears.map(a => a.id),
  });
}
```

5. **Mark arrears as settled** after payroll approval (Step 5: approveRun):
```typescript
await platformPrisma.arrearEntry.updateMany({
  where: { id: { in: settledArrearIds } },
  data: { payrollRunId: run.id },
});
```

6. **Include in Payslip snapshot** (Step 6: disburseRun):
```typescript
arrearsAmount: entry.arrearsAmount,
```

---

## Fix P6: Salary Hold Reduces Earnings

### Current State (line 900-910)
Hold is detected, flagged as exception, but earnings are NOT modified.

### Fixed Flow

Replace the hold handling section with actual earnings reduction:

```typescript
const hold = holdMap.get(emp.id);
let isException = !!hold;
let exceptionNote = hold
  ? `Salary ${hold.holdType} hold: ${hold.reason}`
  : undefined;

if (hold) {
  if (hold.holdType === 'FULL') {
    // FULL hold: zero all earnings
    grossEarnings = 0;
    overtimeAmount = 0;
    arrearsAmount = 0;
    // Clear component-level earnings
    for (const key of Object.keys(earnings)) {
      earnings[key] = 0;
    }
  } else if (hold.holdType === 'PARTIAL' && hold.holdComponents) {
    // PARTIAL hold: zero only held components
    const heldComponents = hold.holdComponents as string[];
    for (const code of heldComponents) {
      if (earnings[code] !== undefined) {
        grossEarnings -= earnings[code];
        earnings[code] = 0;
      }
    }
  }
}
```

**Statutory impact**: When `grossEarnings = 0` (FULL hold), all statutory deductions (PF, ESI, PT, TDS) will naturally compute to zero since they're percentage-based on gross/basic. No special handling needed.

---

## Fix P1: Gratuity Monthly Provision

### Current State
- `GratuityConfig.provisionMethod` allows `'MONTHLY'` but only F&F calculates gratuity
- Formula: `(lastBasic * 15 * yearsOfService) / 26`

### Design
When `provisionMethod === 'MONTHLY'`, calculate a monthly gratuity provision as an **employer contribution** (not a deduction from employee salary):

```typescript
if (gratuityConfig?.provisionMethod === 'MONTHLY') {
  const yearsOfService = /* from employee joining date */;
  if (yearsOfService >= 0) { // Provision from day 1
    const monthlyBasic = /* basic salary component */;
    const annualGratuity = (monthlyBasic * 15 * Math.max(yearsOfService, 1)) / 26;
    const cappedGratuity = Math.min(annualGratuity, Number(gratuityConfig.maxAmount));
    const monthlyProvision = round(cappedGratuity / 12);

    // Add to employer contributions (NOT deducted from employee)
    employerContributions['GRATUITY_PROVISION'] = monthlyProvision;
  }
}
```

**Add to**: `computeStatutory()` step (Step 4), after LWF calculation.
**Display**: Appears in employer contributions section of payslip.

---

## Fix P7: TDS Relief — Section 87A Rebate

### Current State
TDS is calculated using tax slabs and surcharge/cess, but Section 87A rebate is not applied.

### Section 87A Rule
- **New Regime (FY 2025-26)**: If taxable income <= ₹12,00,000, full tax rebate up to ₹60,000
- **Old Regime**: If taxable income <= ₹5,00,000, full tax rebate up to ₹12,500

### Fix
In `computeStatutory()`, after calculating tax on slabs (around line 1416) and before applying surcharge:

```typescript
// Section 87A Rebate
let rebate87A = 0;
if (regime === 'NEW' && taxableIncome <= 1200000) {
  rebate87A = Math.min(taxOnSlabs, 60000);
} else if (regime === 'OLD' && taxableIncome <= 500000) {
  rebate87A = Math.min(taxOnSlabs, 12500);
}
taxOnSlabs -= rebate87A;
```

This should be applied BEFORE surcharge and cess calculation (since rebate reduces base tax).

---

## Fix P8: VPF Rate Cap

### Current State
- `PFConfig` has `vpfEnabled` but no max rate field
- VPF calculation applies employee's `vpfPercentage` without any cap

### Schema Addition
In `prisma/modules/hrms/payroll-config.prisma`, add to PFConfig:
```prisma
  vpfMaxRate Decimal? @db.Decimal(5, 2) // Optional max VPF rate (e.g., 100% means no cap beyond statutory)
```

### Fix in Payroll
In `computeStatutory()`, VPF calculation (around line 1269):

```typescript
if (pfConfig.vpfEnabled && entry.employee.vpfPercentage) {
  let vpfRate = Number(entry.employee.vpfPercentage);
  // Apply cap if configured
  if (pfConfig.vpfMaxRate) {
    vpfRate = Math.min(vpfRate, Number(pfConfig.vpfMaxRate));
  }
  vpfAmount = round(pfWageBase * vpfRate / 100);
}
```

### Admin UI
Add `vpfMaxRate` field to PF Configuration screen (both web and mobile):
- Label: "Maximum VPF Rate (%)"
- Type: Optional number input, 0-100
- Help text: "Leave empty for no cap"

---

## Files Changed

### Backend
| File | Change |
|------|--------|
| `prisma/modules/hrms/payroll-run.prisma` | Add `arrearsAmount` to PayrollEntry + Payslip |
| `prisma/modules/hrms/payroll-config.prisma` | Add `vpfMaxRate` to PFConfig |
| `src/modules/hr/payroll-run/payroll-run.service.ts` | Arrears fetch + consumption, salary hold fix, gratuity provision, Section 87A rebate, VPF cap |
| `src/modules/hr/payroll/payroll.service.ts` | Add vpfMaxRate to PF config CRUD |

### Frontend (both web + mobile)
| File | Change |
|------|--------|
| PF Configuration screen | Add vpfMaxRate input |
| Payslip detail view | Show arrearsAmount if present |
