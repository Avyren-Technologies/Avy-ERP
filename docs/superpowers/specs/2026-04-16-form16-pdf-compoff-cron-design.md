# Sub-project 4: Form 16 PDF Generation + Comp-Off Expiry Cron — Design Spec

## Goal

Fix 2 standalone utility gaps: generate downloadable Form 16 PDFs (Part A + Part B), and implement a scheduled cleanup job for expired compensatory leave balances.

## Verified Gaps

| # | Gap | Current State |
|---|-----|---------------|
| P4 | Form 16 — no PDF generation | `generateForm16()` returns full JSON data with Part A + Part B. Endpoints + mobile screen exist. NO PDF output. |
| E3 | Comp-off expiry cron missing | TODO comment in `leave.service.ts` lines 704/802. Expiry checked on leave application but no background cleanup. |

---

## Fix P4: Form 16 PDF Generation

### Current State
- `generateForm16()` in `payroll-run.service.ts` (lines 2904-3131) returns structured JSON:
  - Part A: Employer details (PAN, TAN), Employee details (PAN, Aadhaar, UAN)
  - Part B: Monthly breakdown (gross, PF, ESI, PT, TDS, LWF, net for each month)
  - Tax computation: Gross salary, exemptions, standard deduction, Chapter VI-A deductions, taxable income, tax, surcharge, cess
  - IT declaration integration
- Endpoints exist: `POST /payroll-reports/form-16`, `GET /ess/my-form16`
- Mobile screen exists with generate + bulk email buttons
- **Missing**: Actual PDF file generation

### Design

Use `pdfkit` (already installed in the backend for payslip PDF generation) to create Form 16 PDF.

**New file**: `avy-erp-backend/src/modules/hr/payroll-run/form16-pdf.service.ts`

**PDF Layout** (standard Form 16 format):

```
┌──────────────────────────────────────────┐
│ FORM No. 16                              │
│ (See Rule 31(1)(a) of the Income-tax     │
│  Rules, 1962)                            │
├──────────────────────────────────────────┤
│ PART A                                   │
│ Certificate under section 203 of the     │
│ Income-tax Act, 1961 for tax deducted    │
│ at source on salary                      │
│                                          │
│ Name of Employer: [companyName]          │
│ TAN: [tan]     PAN: [pan]               │
│ Address: [address]                       │
│                                          │
│ Name of Employee: [name]                 │
│ PAN: [pan]     Assessment Year: [ay]     │
│                                          │
│ Summary of Tax Deducted at Source:       │
│ Quarter │ Receipt No │ Amount │ TDS      │
│ Q1      │ ...        │ ...    │ ...      │
│ Q2      │ ...        │ ...    │ ...      │
│ Q3      │ ...        │ ...    │ ...      │
│ Q4      │ ...        │ ...    │ ...      │
│ Total   │            │ ...    │ ...      │
├──────────────────────────────────────────┤
│ PART B (Annexure)                        │
│ Details of Salary Paid and any other     │
│ income and tax deducted                  │
│                                          │
│ 1. Gross Salary                          │
│    (a) Salary as per S.17(1)    ₹xxx     │
│    (b) Value of perquisites     ₹xxx     │
│    (c) Profits in lieu of salary ₹xxx    │
│ 2. Less: Allowances (S.10)     ₹xxx     │
│    - HRA exemption              ₹xxx     │
│    - LTA exemption              ₹xxx     │
│ 3. Balance (1-2)               ₹xxx     │
│ 4. Deductions under S.16       ₹xxx     │
│    - Standard deduction         ₹xxx     │
│    - Entertainment allowance    ₹xxx     │
│    - Professional tax           ₹xxx     │
│ 5. Income from Salary (3-4)    ₹xxx     │
│ 6. Add: Other income           ₹xxx     │
│ 7. Gross Total Income (5+6)    ₹xxx     │
│ 8. Deductions under Ch VI-A    ₹xxx     │
│    - S.80C                      ₹xxx     │
│    - S.80D                      ₹xxx     │
│    - S.80E                      ₹xxx     │
│    - S.80G                      ₹xxx     │
│    - S.80CCD                    ₹xxx     │
│    - S.80TTA                    ₹xxx     │
│ 9. Total Taxable Income (7-8)  ₹xxx     │
│ 10. Tax on Total Income        ₹xxx     │
│ 11. Rebate under S.87A         ₹xxx     │
│ 12. Surcharge                  ₹xxx     │
│ 13. Cess (4%)                  ₹xxx     │
│ 14. Total Tax Payable          ₹xxx     │
│ 15. Relief under S.89          ₹xxx     │
│ 16. Net Tax Payable            ₹xxx     │
│ 17. Total TDS Deducted         ₹xxx     │
│                                          │
│ Verification:                            │
│ I, [employer name], hereby certify...    │
└──────────────────────────────────────────┘
```

### Implementation Flow

1. `generateForm16()` returns JSON data (existing — no change)
2. New `generateForm16PDF(form16Data)` takes the JSON and produces a Buffer (PDF bytes)
3. Upload PDF to R2 storage (existing upload utility)
4. Store URL in `StatutoryFiling` record (pdfUrl field)
5. Return download URL to frontend

### Bulk Generation
For `POST /payroll-reports/form-16`:
- Generate PDFs for all employees in the FY
- Upload each to R2
- Store URLs in StatutoryFiling records
- Return summary (count, any failures)

For `POST /payroll-reports/form-16/bulk-email`:
- Generate PDFs + email each to employee's registered email
- Use existing email service

### Frontend Changes
- Web: ReportsHubScreen should call the correct endpoint (fix the stub mapping)
- Mobile: Already has generate + email buttons — just need to download the PDF URL
- Employee ESS: `GET /ess/my-form16` should return the PDF URL for download

---

## Fix E3: Comp-Off Expiry Cron Job

### Current State
- `LeaveBalance.expiresAt` field exists and is set when comp-off is granted
- Expiry is checked at leave application time (`leave.service.ts` line 704)
- **No background job** to clean up expired balances
- Impact: Expired comp-off still shows as available balance in leave screens (until employee tries to use it)

### Design

**New file**: `avy-erp-backend/src/shared/jobs/compoff-expiry.job.ts`

**Logic**:
1. Run daily at 1:00 AM (before autoAbsentAfterDays job)
2. Query all LeaveBalance records where:
   - `expiresAt < now()`
   - `balance > 0`
   - Related LeaveType has `category = 'COMPENSATORY'`
3. For each expired balance:
   - Set `balance = 0` (or reduce by the expired amount)
   - Log the expiry: `logger.info('Comp-off expired [employee=X, balance=Y, expiresAt=Z]')`
   - Optionally: Create a LeaveAdjustment record for audit trail
4. Dispatch notification to affected employees:
   - New event: `COMP_OFF_EXPIRED`
   - Template: "Your compensatory off balance of X day(s) has expired on [date]."

### Notification
- Add `COMP_OFF_EXPIRED` to trigger events
- Add template to defaults.ts
- Add to OVERTIME category in notification-categories.ts

### Scheduler Registration
Check how the existing backend registers cron jobs:
- If using `node-cron`: Add to the cron registration file
- If using a custom scheduler: Follow existing pattern
- If no cron infrastructure exists: Create a minimal cron setup using `node-cron` with a registration file

---

## Files Changed

### Backend
| File | Change |
|------|--------|
| `src/modules/hr/payroll-run/form16-pdf.service.ts` | **NEW** — PDF generation using pdfkit |
| `src/modules/hr/payroll-run/payroll-run.service.ts` | Update Form 16 endpoints to generate + store PDF |
| `src/shared/jobs/compoff-expiry.job.ts` | **NEW** — Daily cron for comp-off expiry cleanup |
| `src/shared/constants/trigger-events.ts` | Add `COMP_OFF_EXPIRED` event |
| `src/core/notifications/templates/defaults.ts` | Add comp-off expired template |
| `src/shared/constants/notification-categories.ts` | Add mapping |

### Frontend
| File | Change |
|------|--------|
| Web ReportsHubScreen.tsx | Fix Form 16 report mapping to use correct endpoint |
| Mobile/Web Form 16 screen | Show PDF download link when available |
