# Payroll Calculation Fixes — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Fix 5 payroll gaps: arrears consumption in payroll, salary hold earnings reduction, gratuity monthly provision, Section 87A TDS rebate, and VPF rate cap.

**Architecture:** All changes are in `payroll-run.service.ts` (core payroll engine) and the Prisma schema. Arrears require new schema fields + fetch/settlement logic. Salary hold requires modifying the earnings calculation. Gratuity/TDS/VPF are targeted fixes in computeStatutory.

**Tech Stack:** Prisma, TypeScript, Luxon

**Spec:** `docs/superpowers/specs/2026-04-16-payroll-calculation-fixes-design.md`

---

## File Structure

### Modified Files
| File | Change |
|------|--------|
| `avy-erp-backend/prisma/modules/hrms/payroll-run.prisma` | Add `arrearsAmount` to PayrollEntry + Payslip |
| `avy-erp-backend/prisma/modules/hrms/payroll-config.prisma` | Add `vpfMaxRate` to PFConfig |
| `avy-erp-backend/src/modules/hr/payroll-run/payroll-run.service.ts` | Arrears, salary hold, gratuity, TDS 87A, VPF cap |
| `avy-erp-backend/src/modules/hr/payroll/payroll.service.ts` | Add vpfMaxRate to PF config CRUD |
| `avy-erp-backend/src/modules/hr/payroll/payroll.validators.ts` | Add vpfMaxRate to PF config schema |
| Web + Mobile PF config screens | Add vpfMaxRate input |
| Web + Mobile payslip detail | Show arrearsAmount |

---

## Task 1: Schema — Add arrearsAmount + vpfMaxRate

**Files:**
- Modify: `avy-erp-backend/prisma/modules/hrms/payroll-run.prisma:40-119`
- Modify: `avy-erp-backend/prisma/modules/hrms/payroll-config.prisma:76-92`

- [ ] **Step 1: Add arrearsAmount to PayrollEntry and Payslip**

In `payroll-run.prisma`, add to PayrollEntry model after `overtimeAmount` (line 56):
```prisma
  arrearsAmount     Decimal?   @db.Decimal(15, 2)
```

Add to Payslip model after `overtimeAmount` (line 107):
```prisma
  arrearsAmount     Decimal?   @db.Decimal(15, 2)
```

- [ ] **Step 2: Add vpfMaxRate to PFConfig**

In `payroll-config.prisma`, add to PFConfig after `vpfEnabled` (line 84):
```prisma
  vpfMaxRate         Decimal?  @db.Decimal(5, 2) // Optional max VPF percentage
```

- [ ] **Step 3: Run prisma merge + generate + migrate**

```bash
cd avy-erp-backend && pnpm prisma:merge && pnpm db:generate && pnpm db:migrate --name add_arrears_amount_vpf_max_rate
```

- [ ] **Step 4: Commit**

```bash
cd /Users/chetan/Documents/Avyren-Technologies/Products/Mobile-ERP/avy-erp-backend
git add prisma/
git commit -m "feat(schema): add arrearsAmount to PayrollEntry/Payslip, vpfMaxRate to PFConfig"
```

---

## Task 2: Arrears Consumption in Payroll (P3)

**Files:**
- Modify: `avy-erp-backend/src/modules/hr/payroll-run/payroll-run.service.ts`

- [ ] **Step 1: Batch-fetch unpaid arrears**

In `computeSalaries()`, around line 476 (where OT requests are batch-fetched), add:

```typescript
    // P3: Batch-fetch unpaid arrear entries
    const allArrears = await platformPrisma.arrearEntry.findMany({
      where: { companyId, payrollRunId: null },
      select: { id: true, employeeId: true, totalAmount: true, components: true, forMonth: true, forYear: true },
    });
    const arrearsByEmployee = new Map<string, typeof allArrears>();
    for (const arr of allArrears) {
      if (!arrearsByEmployee.has(arr.employeeId)) arrearsByEmployee.set(arr.employeeId, []);
      arrearsByEmployee.get(arr.employeeId)!.push(arr);
    }
```

- [ ] **Step 2: Add arrears to gross earnings in per-employee loop**

After the overtime calculation section (around line 890) and before the salary hold check (line 900), add:

```typescript
        // P3: Add arrears to gross earnings
        let arrearsAmount = 0;
        const empArrears = arrearsByEmployee.get(emp.id) ?? [];
        for (const arrear of empArrears) {
          arrearsAmount += Number(arrear.totalAmount);
        }
        if (arrearsAmount > 0) {
          grossEarnings += arrearsAmount;
          // Add arrears as an earning component for payslip
          earnings['ARREARS'] = arrearsAmount;
        }
```

- [ ] **Step 3: Flag arrears in review step**

In `reviewExceptions()` (Step 2, around line 279), add arrears detection:

```typescript
        // P3: Flag employees with pending arrears
        if (empArrears.length > 0) {
          isException = true;
          exceptionNote = (exceptionNote ? exceptionNote + '; ' : '') +
            `Arrears pending: ${empArrears.length} entries totaling ₹${arrearsAmount.toFixed(2)}`;
        }
```

- [ ] **Step 4: Store arrearsAmount on PayrollEntry**

In the PayrollEntry creation (around line 960-990), add:

```typescript
          arrearsAmount: arrearsAmount > 0 ? arrearsAmount : null,
```

- [ ] **Step 5: Mark arrears as settled in approveRun**

In `approveRun()` (Step 5, around line 1541), after approving the run, settle arrears:

```typescript
    // P3: Mark arrears as settled
    const entries = await platformPrisma.payrollEntry.findMany({
      where: { payrollRunId: run.id, arrearsAmount: { not: null } },
      select: { employeeId: true },
    });
    const employeeIds = entries.map(e => e.employeeId);
    if (employeeIds.length > 0) {
      await platformPrisma.arrearEntry.updateMany({
        where: { companyId, employeeId: { in: employeeIds }, payrollRunId: null },
        data: { payrollRunId: run.id },
      });
    }
```

- [ ] **Step 6: Include arrearsAmount in Payslip snapshot**

In `disburseRun()` (Step 6), where Payslip is created from PayrollEntry (around line 1889-1919), add:

```typescript
          arrearsAmount: entry.arrearsAmount,
```

- [ ] **Step 7: Commit**

```bash
cd /Users/chetan/Documents/Avyren-Technologies/Products/Mobile-ERP/avy-erp-backend
git add src/modules/hr/payroll-run/payroll-run.service.ts
git commit -m "feat(payroll): consume arrears in payroll run with review + settlement"
```

---

## Task 3: Salary Hold Reduces Earnings (P6)

**Files:**
- Modify: `avy-erp-backend/src/modules/hr/payroll-run/payroll-run.service.ts:900-910`

- [ ] **Step 1: Replace hold handling**

Find the salary hold section (around line 900-910). The current code:
```typescript
const hold = holdMap.get(emp.id);
let isException = !!hold;
let exceptionNote = hold ? `Salary ${hold.holdType} hold: ${hold.reason}` : undefined;
```

Replace with earnings reduction:

```typescript
        // P6: Salary hold — reduce earnings
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
            for (const key of Object.keys(earnings)) {
              earnings[key] = 0;
            }
          } else if (hold.holdType === 'PARTIAL' && hold.holdComponents) {
            // PARTIAL hold: zero only held components
            const heldComponents = hold.holdComponents as string[];
            for (const code of heldComponents) {
              if (earnings[code] !== undefined) {
                grossEarnings -= Number(earnings[code]);
                earnings[code] = 0;
              }
            }
          }
        }
```

Note: This must come AFTER arrears are added (Task 2) but BEFORE the rounding/netPay calculation.

- [ ] **Step 2: Commit**

```bash
cd /Users/chetan/Documents/Avyren-Technologies/Products/Mobile-ERP/avy-erp-backend
git add src/modules/hr/payroll-run/payroll-run.service.ts
git commit -m "fix(payroll): salary hold now reduces gross earnings (FULL=zero, PARTIAL=zero held components)"
```

---

## Task 4: Gratuity Monthly Provision (P1)

**Files:**
- Modify: `avy-erp-backend/src/modules/hr/payroll-run/payroll-run.service.ts` (computeStatutory)

- [ ] **Step 1: Add gratuity provision in computeStatutory**

In `computeStatutory()` (Step 4), after the LWF calculation (around line 1457), add:

```typescript
        // P1: Gratuity monthly provision (employer contribution)
        if (gratuityConfig?.provisionMethod === 'MONTHLY') {
          const joiningDate = emp.joiningDate;
          if (joiningDate) {
            const yearsOfService = DateTime.now().diff(DateTime.fromJSDate(joiningDate), 'years').years;
            // Provision from day 1 (use at least 1 year for projection)
            const effectiveYears = Math.max(yearsOfService, 1);
            // Basic amount from pfInclusion components (same base as PF)
            const annualGratuity = (basicAmount * 15 * effectiveYears) / 26;
            const cappedGratuity = Math.min(annualGratuity, Number(gratuityConfig.maxAmount));
            const monthlyGratuityProvision = round(cappedGratuity / 12);

            employerContributions['GRATUITY_PROVISION'] = monthlyGratuityProvision;
          }
        }
```

Read the file to find where `gratuityConfig` is fetched (it should be batch-fetched alongside PF/ESI/PT configs). If not, add the fetch:

```typescript
    const gratuityConfig = await platformPrisma.gratuityConfig.findUnique({
      where: { companyId },
    });
```

- [ ] **Step 2: Commit**

```bash
cd /Users/chetan/Documents/Avyren-Technologies/Products/Mobile-ERP/avy-erp-backend
git add src/modules/hr/payroll-run/payroll-run.service.ts
git commit -m "feat(payroll): add monthly gratuity provision as employer contribution"
```

---

## Task 5: TDS Section 87A Rebate (P7)

**Files:**
- Modify: `avy-erp-backend/src/modules/hr/payroll-run/payroll-run.service.ts:1405-1440`

- [ ] **Step 1: Add Section 87A rebate**

In `computeStatutory()`, after the tax slab loop (around line 1416) and BEFORE surcharge (line 1419), add:

```typescript
        // P7: Section 87A rebate
        let rebate87A = 0;
        if (regime === 'NEW' && taxableIncome <= 1200000) {
          rebate87A = Math.min(taxOnSlabs, 60000);
        } else if (regime === 'OLD' && taxableIncome <= 500000) {
          rebate87A = Math.min(taxOnSlabs, 12500);
        }
        taxOnSlabs = Math.max(0, taxOnSlabs - rebate87A);
```

This must be inserted AFTER `taxOnSlabs` is computed from the slab loop and BEFORE surcharge is applied. Read the exact variable name used for the slab tax result — it might be `annualTax` or `taxOnSlabs`.

- [ ] **Step 2: Commit**

```bash
cd /Users/chetan/Documents/Avyren-Technologies/Products/Mobile-ERP/avy-erp-backend
git add src/modules/hr/payroll-run/payroll-run.service.ts
git commit -m "feat(payroll): add Section 87A TDS rebate for new and old regime"
```

---

## Task 6: VPF Rate Cap (P8)

**Files:**
- Modify: `avy-erp-backend/src/modules/hr/payroll-run/payroll-run.service.ts:1266-1272`
- Modify: `avy-erp-backend/src/modules/hr/payroll/payroll.service.ts` (PF config CRUD)
- Modify: `avy-erp-backend/src/modules/hr/payroll/payroll.validators.ts`

- [ ] **Step 1: Apply VPF cap in payroll calculation**

Find the VPF calculation (around line 1269):
```typescript
if (pfConfig.vpfEnabled && entry.employee.vpfPercentage) {
  const vpfRate = Number(entry.employee.vpfPercentage);
  vpfAmount = round(pfWageBase * vpfRate / 100);
}
```

Replace with:
```typescript
        if (pfConfig.vpfEnabled && entry.employee.vpfPercentage) {
          let vpfRate = Number(entry.employee.vpfPercentage);
          // P8: Apply VPF rate cap if configured
          if (pfConfig.vpfMaxRate) {
            vpfRate = Math.min(vpfRate, Number(pfConfig.vpfMaxRate));
          }
          vpfAmount = round(pfWageBase * vpfRate / 100);
        }
```

- [ ] **Step 2: Add vpfMaxRate to PF config CRUD**

In `payroll.service.ts`, find the PF config update method. Add `vpfMaxRate` to the data object being upserted.

In `payroll.validators.ts`, find the PF config schema and add:
```typescript
vpfMaxRate: z.number().min(0).max(100).nullable().optional(),
```

- [ ] **Step 3: Update PF config screens (web + mobile)**

Add a "Maximum VPF Rate (%)" field to both web and mobile PF configuration screens. Place it after the `vpfEnabled` toggle. Show only when vpfEnabled is true.

- [ ] **Step 4: Commit**

```bash
cd /Users/chetan/Documents/Avyren-Technologies/Products/Mobile-ERP/avy-erp-backend
git add src/modules/hr/payroll-run/ src/modules/hr/payroll/
git commit -m "feat(payroll): add VPF rate cap with configurable max percentage"
```

---

## Task 7: Frontend — Payslip Arrears Display

**Files:**
- Modify: Web payslip screens (admin + employee)
- Modify: Mobile payslip screen

- [ ] **Step 1: Web employee payslip — show arrears**

In `MyPayslipsScreen.tsx`, in the earnings section of the detail modal, add arrears display if present:

```typescript
{detail.arrearsAmount && Number(detail.arrearsAmount) > 0 && (
  <div className="flex justify-between">
    <span>Arrears</span>
    <span>{formatCurrency(Number(detail.arrearsAmount))}</span>
  </div>
)}
```

- [ ] **Step 2: Mobile payslip — show arrears**

Same change in the mobile payslip detail view.

- [ ] **Step 3: Commit**

```bash
cd /Users/chetan/Documents/Avyren-Technologies/Products/Mobile-ERP
git add web-system-app/ mobile-app/
git commit -m "feat(ui): show arrears amount on payslip detail views"
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
