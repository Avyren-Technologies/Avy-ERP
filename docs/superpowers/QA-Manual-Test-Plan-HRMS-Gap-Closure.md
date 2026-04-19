# HRMS Gap Closure — Manual QA Test Plan

**Date:** 2026-04-19
**Scope:** OT Employee Features, Attendance Enforcement, Payroll Fixes, ESS Display Enhancements, Form 16 PDF, Comp-Off Cron, Recent Attendance Fix
**Platforms:** Web + Mobile (both must be tested)

---

## Pre-Requisites — Test Data Setup

Before running tests, ensure this data exists:

### Company Configuration
- [ ] Company with active employees (at least 3: Employee, Manager, HR Admin)
- [ ] At least one Location with geofence configured (lat/lng/radius)
- [ ] At least one Shift assigned to employees
- [ ] Attendance Rule configured with all toggles (see Section 2)

### OT Configuration
- [ ] OT Rule created with: `approvalRequired=true`, multipliers (weekday 1.5x, weekend 2.0x, holiday 2.5x), `dailyCapHours=8`, `weeklyCapHours=40`, `compOffEnabled=true`, `compOffExpiryDays=90`
- [ ] At least one auto-generated OT request (employee worked overtime)
- [ ] COMPENSATORY leave type exists

### Payroll Configuration
- [ ] Salary structure assigned to employees with BASIC, HRA, and other components
- [ ] PF config with `vpfEnabled=true`
- [ ] ESI config with ceiling
- [ ] PT config with state slabs
- [ ] Gratuity config with `provisionMethod=MONTHLY`
- [ ] At least one salary revision with arrears (apply revision for past effective date)
- [ ] At least one salary hold (FULL and PARTIAL)
- [ ] Tax config with slabs for both NEW and OLD regime
- [ ] IT Declaration submitted by at least one employee

### Leave Configuration
- [ ] Multiple leave types: Casual (monthly accrual), Earned (quarterly, encashable), Sick
- [ ] Leave balances with carry-forward (openingBalance > 0)
- [ ] Comp-off balance with expiry date set

---

## Section 1: OT Employee Features

### 1.1 My Overtime Screen — Navigation & Summary
**Route:** `/app/company/hr/my-overtime`
**Role:** Employee
**Permission:** `ess:view-overtime`

| # | Test Case | Steps | Expected Result | Web | Mobile |
|---|-----------|-------|-----------------|-----|--------|
| 1.1.1 | Screen accessible via sidebar | Log in as Employee → Sidebar → My Workspace → My Overtime | Screen loads with summary cards + list | [ ] | [ ] |
| 1.1.2 | Summary cards show correct data | Check OT Hours, Pending, Approved Amount, Comp-Off | Values match database; Comp-Off shows balance + expiry | [ ] | [ ] |
| 1.1.3 | Comp-Off card shows "Not enabled" when disabled | Disable `compOffEnabled` in OT rules | Card shows "—" with "Not enabled" | [ ] | [ ] |
| 1.1.4 | Filter by status | Click Pending/Approved/Rejected chips | List filters correctly | [ ] | [ ] |
| 1.1.5 | Filter by source | Select AUTO or MANUAL filter | List shows only matching source | [ ] | [ ] |
| 1.1.6 | Pagination works | Have 25+ OT requests, navigate pages | Correct 20-per-page pagination | [ ] | [ ] |
| 1.1.7 | Empty state | Employee with no OT requests | Shows "No overtime requests" message | [ ] | [ ] |

### 1.2 OT Request Detail View
| # | Test Case | Steps | Expected Result | Web | Mobile |
|---|-----------|-------|-----------------|-----|--------|
| 1.2.1 | View AUTO request detail | Click/tap an AUTO request | Shows attendance record (punch in/out, worked hours, shift), approval info, status | [ ] | [ ] |
| 1.2.2 | View MANUAL request detail | Click/tap a MANUAL request | Shows reason text, attachments list, no attendance record | [ ] | [ ] |
| 1.2.3 | Approved request shows amount | View approved request | Shows calculated amount (₹) | [ ] | [ ] |
| 1.2.4 | Comp-off granted indicator | View approved request with comp-off | Shows "Comp-Off: Yes (0.5 days)" or "1 day" | [ ] | [ ] |

### 1.3 Manual OT Claim — Submit Form
| # | Test Case | Steps | Expected Result | Web | Mobile |
|---|-----------|-------|-----------------|-----|--------|
| 1.3.1 | Open claim form | Click "+ Claim OT" button / FAB | Claim form opens (dialog on web, bottom sheet on mobile) | [ ] | [ ] |
| 1.3.2 | Submit valid claim | Fill: date (yesterday), 2 hours, reason (15 chars), submit | Success toast, form closes, new PENDING request in list | [ ] | [ ] |
| 1.3.3 | Date picker limits to last 30 days | Try to select date > 30 days ago | Date not selectable / error shown | [ ] | [ ] |
| 1.3.4 | Future date rejected | Try to select tomorrow | Error: "Date must be in the past" | [ ] | [ ] |
| 1.3.5 | Hours validation | Enter 0.3 hours | Error: "Hours must be in increments of 0.5" | [ ] | [ ] |
| 1.3.6 | Reason minimum length | Enter "short" (5 chars) | Error: "Reason must be at least 10 characters" | [ ] | [ ] |
| 1.3.7 | Attachments max 5 | Try to add 6 files | Only 5 allowed, error on 6th | [ ] | [ ] |
| 1.3.8 | Duplicate date rejected | Submit claim for date that already has OT | Error: "An overtime request already exists for this date" | [ ] | [ ] |
| 1.3.9 | Ineligible employee type | Configure `eligibleTypeIds` excluding this employee's type | Error: "You are not eligible for overtime claims" | [ ] | [ ] |
| 1.3.10 | Daily cap exceeded | Configure dailyCapHours=2, submit 3 hours | Hours capped to 2, or error if 0 remaining | [ ] | [ ] |
| 1.3.11 | Auto-approved (no approval required) | Set `approvalRequired=false`, submit claim | Claim created with status APPROVED immediately | [ ] | [ ] |

### 1.4 Comp-Off Deep Link
| # | Test Case | Steps | Expected Result | Web | Mobile |
|---|-----------|-------|-----------------|-----|--------|
| 1.4.1 | Deep link navigation | Tap Comp-Off summary card | Navigates to Leave Application with COMPENSATORY pre-selected | [ ] | [ ] |
| 1.4.2 | Leave type pre-selected | After navigation | Leave type dropdown shows COMPENSATORY selected | [ ] | [ ] |

### 1.5 OT Notifications
| # | Test Case | Steps | Expected Result | Web | Mobile |
|---|-----------|-------|-----------------|-----|--------|
| 1.5.1 | Auto-detected notification | Employee checks out with overtime | Employee receives "Overtime Detected" push/in-app notification | [ ] | [ ] |
| 1.5.2 | Comp-off granted notification | Admin approves OT with comp-off enabled | Employee receives "Compensatory Off Credited" notification | [ ] | [ ] |
| 1.5.3 | Claim submitted notification | Employee submits manual claim | Approver receives "Overtime Claim from [name]" notification | [ ] | [ ] |

---

## Section 2: Attendance Enforcement

### 2.1 Geofence Enforcement
**Config screen:** `/app/company/hr/attendance-rules`
**Test screen:** `/app/company/hr/shift-check-in`

| # | Test Case | Steps | Expected Result | Web | Mobile |
|---|-----------|-------|-----------------|-----|--------|
| 2.1.1 | Config dropdown visible | Open Attendance Rules screen | "Geofence Enforcement" dropdown shown after GPS Required | [ ] | [ ] |
| 2.1.2 | OFF mode (default) | Set mode to OFF → check in outside geofence | Check-in succeeds, geoStatus=OUTSIDE_GEOFENCE stored silently | [ ] | [ ] |
| 2.1.3 | WARN mode — outside geofence | Set mode to WARN → check in outside geofence | Check-in succeeds, warning shown, manager receives notification | [ ] | [ ] |
| 2.1.4 | STRICT mode — outside geofence | Set mode to STRICT → check in outside geofence | Check-in BLOCKED: "You must be inside the designated geofence area" | [ ] | [ ] |
| 2.1.5 | STRICT mode — inside geofence | Set mode to STRICT → check in inside geofence | Check-in succeeds normally | [ ] | [ ] |
| 2.1.6 | Check-out enforcement | Same tests as above for check-out | Same behavior on check-out | [ ] | [ ] |

### 2.2 Selfie & GPS Validation
| # | Test Case | Steps | Expected Result | Web | Mobile |
|---|-----------|-------|-----------------|-----|--------|
| 2.2.1 | Selfie required — check-in without photo | Set `selfieRequired=true`, try check-in without selfie | Error: "Selfie photo is required by company policy" | [ ] | [ ] |
| 2.2.2 | Selfie required — check-out without photo | Set `selfieRequired=true`, try check-out without selfie | Error: "Selfie photo is required by company policy" | [ ] | [ ] |
| 2.2.3 | GPS required — check-in without location | Set `gpsRequired=true`, deny location permission | Error: "GPS location is required by company policy" | [ ] | [ ] |
| 2.2.4 | GPS required — check-out without location | Same as above for check-out | Same error | [ ] | [ ] |
| 2.2.5 | Both required — provided | selfie + GPS enabled, provide both | Check-in succeeds | [ ] | [ ] |

### 2.3 Regularization Window
| # | Test Case | Steps | Expected Result | Web | Mobile |
|---|-----------|-------|-----------------|-----|--------|
| 2.3.1 | Within window | Set window=7 days, regularize 3-day-old record | Regularization request created | [ ] | [ ] |
| 2.3.2 | Outside window | Set window=7 days, regularize 10-day-old record | Error: "Cannot regularize attendance older than 7 days" | [ ] | [ ] |

### 2.4 Punch Mode (EVERY_PAIR / SHIFT_BASED)
| # | Test Case | Steps | Expected Result | Web | Mobile |
|---|-----------|-------|-----------------|-----|--------|
| 2.4.1 | FIRST_LAST mode | Default mode, punch in 9AM, punch out 6PM | Worked hours: 9h (first in, last out) | [ ] | [ ] |
| 2.4.2 | EVERY_PAIR mode | Set EVERY_PAIR, punch in/out/in/out | Worked hours = sum of all in-out pairs | [ ] | [ ] |
| 2.4.3 | SHIFT_BASED mode | Set SHIFT_BASED, punch near shift times | Worked hours validated against shift schedule | [ ] | [ ] |

### 2.5 Recent Attendance (Shift Check-In Screen)
| # | Test Case | Steps | Expected Result | Web | Mobile |
|---|-----------|-------|-----------------|-----|--------|
| 2.5.1 | Recent attendance shows last 7 days | Open shift check-in screen | Table shows last 7 days with real punch times, hours, and status badges | [ ] | [ ] |
| 2.5.2 | Status badges correct | Check previous days with various statuses | PRESENT=green, ABSENT=red, LATE=amber, ON_LEAVE=blue, HOLIDAY=purple, WEEK_OFF=gray | [ ] | [ ] |
| 2.5.3 | Empty recent attendance | New employee with no history | Shows "No recent attendance records" | [ ] | [ ] |

---

## Section 3: Payroll Calculation Fixes

### 3.1 Arrears in Payroll
**Test via:** Payroll Run (admin)
**Role:** HR/Payroll Admin

| # | Test Case | Steps | Expected Result |
|---|-----------|-------|-----------------|
| 3.1.1 | Arrears included in payroll | Create salary revision with past effective date → Run payroll | Arrear entries fetched and added to gross earnings |
| 3.1.2 | Arrears flagged in review | Check payroll exceptions before approval | Shows "Arrears pending: X entries totaling ₹Y" |
| 3.1.3 | Arrears on payslip | Approve payroll → check payslip | "Arrears: ₹X" shown in earnings section |
| 3.1.4 | Arrears settled after approval | Approve payroll → check ArrearEntry records | `payrollRunId` updated to the run ID |
| 3.1.5 | No double-count | Run payroll again next month | Previously settled arrears NOT included again |

### 3.2 Salary Hold
| # | Test Case | Steps | Expected Result |
|---|-----------|-------|-----------------|
| 3.2.1 | FULL hold — zero earnings | Create FULL hold → Run payroll | Gross=0, Net=0, all components=0, all statutory=0 |
| 3.2.2 | PARTIAL hold — zero held components | Create PARTIAL hold for [BASIC, HRA] → Run payroll | Only BASIC+HRA=0, other components paid normally |
| 3.2.3 | Hold with arrears | FULL hold + pending arrears | Arrears also zeroed (not paid during hold) |
| 3.2.4 | Payslip shows hold | Check payslip after hold | Payslip flagged with "Salary Hold Applied" note |

### 3.3 Gratuity Monthly Provision
| # | Test Case | Steps | Expected Result |
|---|-----------|-------|-----------------|
| 3.3.1 | Monthly provision shown | Set `provisionMethod=MONTHLY` → Run payroll | "Gratuity Provision: ₹X" shown under Employer Contributions |
| 3.3.2 | Formula correct | Employee with 5yr service, Basic=₹50K | Provision = (50000 × 15 × 5) / 26 / 12 ≈ ₹12,019/month |
| 3.3.3 | Cap applied | Set maxAmount=₹2,000,000 | Annual gratuity capped before dividing by 12 |
| 3.3.4 | Not shown if ACTUAL_AT_EXIT | Set `provisionMethod=ACTUAL_AT_EXIT` | No gratuity line in payslip |

### 3.4 TDS Section 87A Rebate
| # | Test Case | Steps | Expected Result |
|---|-----------|-------|-----------------|
| 3.4.1 | NEW regime — eligible | Employee on NEW regime, taxable income ₹10L | Rebate applied: up to ₹60,000 reduction in tax |
| 3.4.2 | NEW regime — not eligible | Taxable income ₹15L | No rebate applied (above ₹12L threshold) |
| 3.4.3 | OLD regime — eligible | Employee on OLD regime, taxable income ₹4.5L | Rebate applied: up to ₹12,500 reduction |
| 3.4.4 | OLD regime — not eligible | Taxable income ₹6L | No rebate applied (above ₹5L threshold) |
| 3.4.5 | Rebate before surcharge | Check TDS computation order | Rebate subtracted from slab tax BEFORE surcharge and cess |

### 3.5 VPF Rate Cap
**Config screen:** `/app/company/hr/statutory-config` (PF section)

| # | Test Case | Steps | Expected Result | Web | Mobile |
|---|-----------|-------|-----------------|-----|--------|
| 3.5.1 | VPF max rate field visible | Open PF Config, enable VPF | "Maximum VPF Rate (%)" input shown | [ ] | [ ] |
| 3.5.2 | Cap applied | Set vpfMaxRate=50%, employee has vpf=80% | VPF calculated at 50% (capped), not 80% |
| 3.5.3 | No cap (empty) | Leave vpfMaxRate empty | VPF uses employee's full percentage |
| 3.5.4 | Cap saved correctly | Set cap, save, reload | Cap value persists | [ ] | [ ] |

---

## Section 4: ESS Display Enhancements

### 4.1 Attendance Dashboard (Admin)
**Route:** `/app/company/hr/attendance`
**Role:** HR/Admin

| # | Test Case | Steps | Expected Result | Web |
|---|-----------|-------|-----------------|-----|
| 4.1.1 | Geofence status badge | Click attendance record with GPS data | Detail modal shows "Inside Geofence" (green) or "Outside Geofence" (red) | [ ] |
| 4.1.2 | Break deduction shown | Record with break deduction applied | Shows "Break Deduction: 30 min" | [ ] |
| 4.1.3 | Resolution trace | Click record detail | Expandable "Policy Applied" section shows source, grace period, thresholds | [ ] |
| 4.1.4 | No GPS data | Record without GPS | No geofence badge or GPS info shown (graceful) | [ ] |

### 4.2 Employee Attendance Detail
**Route:** `/app/company/hr/my-attendance`
**Role:** Employee

| # | Test Case | Steps | Expected Result | Web | Mobile |
|---|-----------|-------|-----------------|-----|--------|
| 4.2.1 | Geofence status shown | Select day with GPS punch | Shows "Inside" (green) or "Outside" (red) in detail | [ ] | [ ] |
| 4.2.2 | GPS coordinates shown | Select day with GPS | Shows "Location: XX.XXXX, YY.YYYY" | [ ] | [ ] |
| 4.2.3 | Break deduction shown | Select day with break deduction | Shows "Break Deducted: 30 min" | [ ] | [ ] |

### 4.3 Employee Payslip Enhancements
**Route:** `/app/company/hr/my-payslips`
**Role:** Employee

| # | Test Case | Steps | Expected Result | Web | Mobile |
|---|-----------|-------|-----------------|-----|--------|
| 4.3.1 | Employer contributions visible | Open payslip detail | Shows "Employer Contributions" section: PF Employer, ESI Employer, LWF, Gratuity | [ ] | [ ] |
| 4.3.2 | OT breakdown shown | Payslip with overtime | Shows "Overtime (12.5 hrs): ₹4,500" | [ ] | [ ] |
| 4.3.3 | LOP detail shown | Payslip with LOP days | Shows "LOP: 3 days (Working: 26, Present: 23)" | [ ] | [ ] |
| 4.3.4 | TDS provisional note | Any current month payslip | Shows "* TDS amount is provisional" in italic | [ ] | [ ] |
| 4.3.5 | Arrears shown | Payslip with arrears | Shows "Arrears: ₹X" in accent color | [ ] | [ ] |
| 4.3.6 | YTD totals displayed | Open payslip detail | Bottom section: "Year-to-Date (FY 2025-26)" with Gross, Deductions, TDS, Net | [ ] | [ ] |
| 4.3.7 | Leave balance on payslip | Open payslip detail | Footer: "Leave Balance" with CL: 4/12, EL: 8/18, etc. | [ ] | [ ] |
| 4.3.8 | No YTD for first month | Employee's first month payslip | YTD shows same as current month values | [ ] | [ ] |

### 4.4 Leave Balance Enhancements
**Route:** `/app/company/hr/my-leave`
**Role:** Employee

| # | Test Case | Steps | Expected Result | Web | Mobile |
|---|-----------|-------|-----------------|-----|--------|
| 4.4.1 | Carry-forward breakdown | Leave type with carry-forward | Shows "CF: 5 · Accrued: 12 · Used: 2" instead of just "used/total" | [ ] | [ ] |
| 4.4.2 | Accrual schedule shown | Leave type with monthly accrual | Shows "Accrual: Monthly" below balance | [ ] | [ ] |
| 4.4.3 | Encashment indicator | Leave type with encashment enabled | Shows "Encashable (max 10 days)" in accent color | [ ] | [ ] |
| 4.4.4 | No carry-forward | Leave type without carry-forward | No "CF:" prefix shown | [ ] | [ ] |
| 4.4.5 | No accrual | Leave type with UPFRONT accrual | Shows "Accrual: Upfront" | [ ] | [ ] |
| 4.4.6 | Encashment not allowed | Leave type without encashment | No encashment indicator shown | [ ] | [ ] |

---

## Section 5: Form 16 PDF & Comp-Off Cron

### 5.1 Form 16 PDF Generation
**Admin route:** Reports Hub → Form 16
**Employee route:** `/app/company/hr/my-form16`
**Role:** HR Admin (generate), Employee (download)

| # | Test Case | Steps | Expected Result |
|---|-----------|-------|-----------------|
| 5.1.1 | Generate Form 16 | Admin: Reports Hub → Generate Form 16 for FY | Form 16 generated with data for all employees |
| 5.1.2 | Download PDF | Employee: My Form 16 → Download | PDF downloads with Part A + Part B, monthly table, tax computation |
| 5.1.3 | PDF content correct | Open downloaded PDF | Contains: Employer details, Employee PAN, monthly breakdown, Chapter VI-A deductions, total TDS |
| 5.1.4 | Per-employee PDF | Admin: Download PDF for specific employee | `GET /payroll-reports/form-16/:employeeId/pdf?financialYear=2025-26` returns PDF |

### 5.2 Comp-Off Expiry Cron
| # | Test Case | Steps | Expected Result |
|---|-----------|-------|-----------------|
| 5.2.1 | Expired balance zeroed | Create comp-off balance with expiresAt = yesterday → Wait for cron (or trigger manually) | Balance set to 0, adjusted decremented |
| 5.2.2 | Notification sent | After expiry processing | Employee receives "Compensatory Off Expired" notification |
| 5.2.3 | Non-expired not affected | Comp-off with future expiry | Balance unchanged |
| 5.2.4 | Already-zero balance skipped | Expired balance already at 0 | No action taken, no duplicate notification |

---

## Section 6: Cross-Cutting Concerns

### 6.1 Consistency Between Web & Mobile
| # | Test Case | Expected |
|---|-----------|----------|
| 6.1.1 | My Overtime summary cards match | Same values on both platforms |
| 6.1.2 | OT request list shows same data | Same items, same order, same badges |
| 6.1.3 | Claim form validates identically | Same errors for same invalid input |
| 6.1.4 | Payslip detail shows same sections | Employer contributions, OT, LOP, YTD, leave balance on both |
| 6.1.5 | Leave balance breakdown matches | Same CF/Accrued/Used values on both |
| 6.1.6 | Attendance detail shows same fields | geoStatus, GPS, break deduction on both |
| 6.1.7 | Recent Attendance shows same data | Same 7 days, same status badges on both |

### 6.2 Date/Time Formatting
| # | Test Case | Expected |
|---|-----------|----------|
| 6.2.1 | All dates use company formatter | No raw `toLocaleDateString()` anywhere |
| 6.2.2 | Times respect company timezone | Punch times shown in company timezone, not browser/device |
| 6.2.3 | Date format matches company settings | DD/MM/YYYY or MM/DD/YYYY per company dateFormat |

### 6.3 Permissions & Access Control
| # | Test Case | Expected |
|---|-----------|----------|
| 6.3.1 | Employee without `ess:view-overtime` | My Overtime not visible in sidebar |
| 6.3.2 | Employee without `ess:claim-overtime` | "+ Claim OT" button hidden |
| 6.3.3 | ESS `overtimeView` disabled in ESSConfig | My Overtime screen hidden for all employees |
| 6.3.4 | Resolution trace NOT visible to employee | Admin-only collapsible — not shown on MyAttendanceScreen |

### 6.4 Error Handling
| # | Test Case | Expected |
|---|-----------|----------|
| 6.4.1 | Network error on API call | Error toast shown (web: `showApiError`, mobile: `showErrorMessage`) |
| 6.4.2 | Empty states | "No data" message shown, not blank screen |
| 6.4.3 | Loading states | Skeleton/spinner shown during data fetch |
| 6.4.4 | Mobile: no Alert.alert used | All errors use toast or ConfirmModal |

---

## Sign-Off Checklist

| Area | Status | Tester | Date |
|------|--------|--------|------|
| OT Employee Features (Web) | [ ] Pass / [ ] Fail | | |
| OT Employee Features (Mobile) | [ ] Pass / [ ] Fail | | |
| Attendance Enforcement (Web) | [ ] Pass / [ ] Fail | | |
| Attendance Enforcement (Mobile) | [ ] Pass / [ ] Fail | | |
| Payroll Calculation Fixes | [ ] Pass / [ ] Fail | | |
| ESS Display — Attendance (Web) | [ ] Pass / [ ] Fail | | |
| ESS Display — Attendance (Mobile) | [ ] Pass / [ ] Fail | | |
| ESS Display — Payslip (Web) | [ ] Pass / [ ] Fail | | |
| ESS Display — Payslip (Mobile) | [ ] Pass / [ ] Fail | | |
| ESS Display — Leave (Web) | [ ] Pass / [ ] Fail | | |
| ESS Display — Leave (Mobile) | [ ] Pass / [ ] Fail | | |
| Form 16 PDF Generation | [ ] Pass / [ ] Fail | | |
| Comp-Off Expiry Cron | [ ] Pass / [ ] Fail | | |
| Recent Attendance Fix (Web) | [ ] Pass / [ ] Fail | | |
| Recent Attendance Fix (Mobile) | [ ] Pass / [ ] Fail | | |
| Cross-Platform Consistency | [ ] Pass / [ ] Fail | | |
