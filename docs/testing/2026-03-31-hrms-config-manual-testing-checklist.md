# HRMS Configuration System — Manual Testing Checklist

**Date:** 2026-03-31
**Scope:** All changes from the HRMS Configuration System redesign
**Test Environment:** Development (localhost)

---

## Quick Setup

```bash
# Backend
cd avy-erp-backend
pnpm install
npx prisma db push --force-reset   # Reset DB to match schema
npx ts-node prisma/seed.ts          # Seed test data
pnpm dev                             # Start API on port 3000

# Web
cd web-system-app
pnpm install && pnpm dev             # Start on port 5173

# Mobile
cd mobile-app
pnpm install && pnpm start           # Start Expo dev server
```

### Test Credentials

| Role | Email | Password |
|------|-------|----------|
| **Super Admin** | superadmin@avyerp.local | SuperAdmin@12345 |
| **Company Admin** | admin@acme.local | Admin@12345 |

### Company: Acme Manufacturing Pvt Ltd

---

## Part 1: Backend API Verification (Postman / cURL)

Test these BEFORE touching the frontend — confirms APIs work independently.

### 1.1 Authentication

| # | Test | Method | Endpoint | Expected |
|---|------|--------|----------|----------|
| 1 | Login as company admin | POST | `/api/v1/auth/login` | 200 + token + user object (NO `featureToggles` field) |
| 2 | Login as super admin | POST | `/api/v1/auth/login` | 200 + token |
| 3 | Verify `featureToggles` removed from auth response | — | — | Field should NOT exist in response |

### 1.2 Company Settings API

| # | Test | Method | Endpoint | Expected |
|---|------|--------|----------|----------|
| 4 | Get settings | GET | `/api/v1/company/settings` | 200 + typed `CompanySettings` object (NOT JSON blob) |
| 5 | Verify fields: currency, language, timezone, dateFormat, timeFormat, numberFormat | — | — | All 6 locale fields present with correct types |
| 6 | Verify fields: indiaCompliance, gdprMode, auditTrail | — | — | 3 compliance booleans |
| 7 | Verify fields: bankIntegration, razorpayEnabled, emailNotifications, whatsappNotifications, biometricIntegration, eSignIntegration | — | — | 6 integration booleans |
| 8 | Update timezone | PATCH | `/api/v1/company/settings` | 200 + updated value persisted |
| 9 | Invalid currency value | PATCH | `/api/v1/company/settings` `{ "currency": "XYZ" }` | 400 validation error |
| 10 | Verify `updatedBy` populated | — | — | Check DB: `updatedBy` = admin userId |

### 1.3 System Controls API

| # | Test | Method | Endpoint | Expected |
|---|------|--------|----------|----------|
| 11 | Get controls | GET | `/api/v1/company/controls` | 200 + typed `SystemControls` (NOT JSON blob) |
| 12 | Verify module enablement fields (9) | — | — | attendanceEnabled, leaveEnabled, payrollEnabled, essEnabled, performanceEnabled, recruitmentEnabled, trainingEnabled, mobileAppEnabled, aiChatbotEnabled |
| 13 | Verify production fields (3) | — | — | ncEditMode, loadUnload, cycleTime |
| 14 | Verify payroll fields (2) | — | — | payrollLock, backdatedEntryControl |
| 15 | Verify leave fields (3) | — | — | leaveCarryForward, compOffEnabled, halfDayLeaveEnabled |
| 16 | Verify security fields (7) | — | — | mfaRequired, sessionTimeoutMinutes, maxConcurrentSessions, passwordMinLength, passwordComplexity, accountLockThreshold, accountLockDurationMinutes |
| 17 | Verify audit fields (1) | — | — | auditLogRetentionDays |
| 18 | Update sessionTimeoutMinutes = 3 (below min 5) | PATCH | `/api/v1/company/controls` | 400 validation error |
| 19 | Update sessionTimeoutMinutes = 60 | PATCH | `/api/v1/company/controls` | 200 success |
| 20 | Disable attendance module | PATCH | `{ "attendanceEnabled": false }` | 200 success |
| 21 | Access attendance API with module disabled | GET | `/api/v1/hr/attendance/rules` | 403 "attendance module is not enabled" |
| 22 | Re-enable attendance module | PATCH | `{ "attendanceEnabled": true }` | 200 success |

### 1.4 Shift API (Enhanced)

| # | Test | Method | Endpoint | Expected |
|---|------|--------|----------|----------|
| 23 | List shifts | GET | `/api/v1/company/shifts` | 200 + shifts with `startTime`/`endTime` (NOT `fromTime`/`toTime`) |
| 24 | Verify shift fields: shiftType, isCrossDay, policy overrides | — | — | New fields present (may be null for existing shifts) |
| 25 | Create day shift | POST | `/api/v1/company/shifts` `{ "name": "Day Shift", "shiftType": "DAY", "startTime": "09:00", "endTime": "17:00" }` | 200 success |
| 26 | Create night shift | POST | `{ "name": "Night Shift", "shiftType": "NIGHT", "startTime": "22:00", "endTime": "06:00", "isCrossDay": true }` | 200 success |
| 27 | Create shift with policy override | POST | `{ ..., "gracePeriodMinutes": 10, "halfDayThresholdHours": 3.5 }` | 200 + overrides stored |
| 28 | Create shift without overrides (null) | POST | `{ ..., "gracePeriodMinutes": null }` | 200 + null stored (inherits from rules) |
| 29 | **Add break to shift** | POST | `/api/v1/company/shifts/:id/breaks` `{ "name": "Lunch", "type": "FIXED", "startTime": "12:30", "duration": 30, "isPaid": false }` | 200 + break created |
| 30 | **Add flexible break** | POST | `/api/v1/company/shifts/:id/breaks` `{ "name": "Tea", "type": "FLEXIBLE", "duration": 15, "isPaid": true }` | 200 (no startTime needed) |
| 31 | Get shift with breaks | GET | `/api/v1/company/shifts/:id` | 200 + shift object includes `breaks[]` array |
| 32 | Update break | PATCH | `/api/v1/company/shifts/:id/breaks/:breakId` | 200 success |
| 33 | Delete break | DELETE | `/api/v1/company/shifts/:id/breaks/:breakId` | 200 success |

### 1.5 Attendance Rules API (Enhanced)

| # | Test | Method | Endpoint | Expected |
|---|------|--------|----------|----------|
| 34 | Get attendance rules | GET | `/api/v1/hr/attendance/rules` | 200 + all 26 fields |
| 35 | Verify NEW fields present: punchMode, autoMarkAbsentIfNoPunch, workingHoursRounding, lateDeductionType, regularizationWindowDays | — | — | All present with defaults |
| 36 | Verify REMOVED fields gone: shiftStartTime, shiftEndTime | — | — | NOT in response |
| 37 | Verify RENAMED fields: earlyExitToleranceMinutes (was earlyExitMinutes), lateArrivalsAllowedPerMonth (was lateArrivalsAllowed) | — | — | New names used |
| 38 | Update punchMode to EVERY_PAIR | PATCH | `{ "punchMode": "EVERY_PAIR" }` | 200 success |
| 39 | Update lateDeductionType to PERCENTAGE with value | PATCH | `{ "lateDeductionType": "PERCENTAGE", "lateDeductionValue": 5.0 }` | 200 success |
| 40 | Update lateDeductionType to PERCENTAGE WITHOUT value | PATCH | `{ "lateDeductionType": "PERCENTAGE" }` | 400 validation error (value required) |
| 41 | Update workingHoursRounding to NEAREST_15 | PATCH | `{ "workingHoursRounding": "NEAREST_15" }` | 200 success |

### 1.6 Overtime Rules API (Enhanced)

| # | Test | Method | Endpoint | Expected |
|---|------|--------|----------|----------|
| 42 | Get overtime rules | GET | `/api/v1/hr/overtime-rules` | 200 + all 20 fields |
| 43 | Verify granular multipliers: weekdayMultiplier, weekendMultiplier, holidayMultiplier, nightShiftMultiplier | — | — | weekdayMultiplier has value, others may be null |
| 44 | Verify NEW fields: calculationBasis, minimumOtMinutes, includeBreaksInOT, dailyCapHours, enforceCaps, maxContinuousOtHours, compOffEnabled, compOffExpiryDays | — | — | All present |
| 45 | Verify REMOVED: single rateMultiplier field | — | — | NOT in response |
| 46 | Update weekendMultiplier | PATCH | `{ "weekendMultiplier": 2.0 }` | 200 success |
| 47 | Set compOff enabled | PATCH | `{ "compOffEnabled": true, "compOffExpiryDays": 30 }` | 200 success |

### 1.7 Overtime Request Workflow (NEW)

| # | Test | Method | Endpoint | Expected |
|---|------|--------|----------|----------|
| 48 | List OT requests | GET | `/api/v1/hr/overtime-requests` | 200 + paginated list (empty initially) |
| 49 | List with status filter | GET | `/api/v1/hr/overtime-requests?status=PENDING` | 200 + filtered list |
| 50 | Approve OT request (when one exists) | PATCH | `/api/v1/hr/overtime-requests/:id/approve` | 200 + status=APPROVED, calculatedAmount computed |
| 51 | Reject OT request | PATCH | `/api/v1/hr/overtime-requests/:id/reject` `{ "notes": "Not eligible" }` | 200 + status=REJECTED |

### 1.8 ESS Config API (Enhanced)

| # | Test | Method | Endpoint | Expected |
|---|------|--------|----------|----------|
| 52 | Get ESS config | GET | `/api/v1/hr/ess-config` | 200 + all 36 fields |
| 53 | Verify REMOVED security fields | — | — | NO loginMethod, passwordMinLength, passwordComplexity, sessionTimeoutMinutes, mfaRequired |
| 54 | Verify NEW MSS fields | — | — | mssViewTeam, mssApproveLeave, mssApproveAttendance, mssViewTeamAttendance |
| 55 | Verify NEW mobile fields | — | — | mobileOfflinePunch, mobileSyncRetryMinutes, mobileLocationAccuracy |
| 56 | Verify NEW fields | — | — | downloadPayslips, viewSalaryStructure, leaveCancellation, shiftSwapRequest, wfhRequest, viewOrgChart, announcementBoard |
| 57 | Disable leave application | PATCH | `{ "leaveApplication": false }` | 200 success |
| 58 | **Test ESS enforcement** | POST | `/api/v1/hr/ess/apply-leave` | 403 "leaveApplication is not enabled" |
| 59 | Re-enable and test | PATCH + POST | Re-enable → apply leave | Should work now |

### 1.9 Module Enforcement (NEW)

| # | Test | Action | Expected |
|---|------|--------|----------|
| 60 | Disable attendance module in System Controls | PATCH `/api/v1/company/controls` `{ "attendanceEnabled": false }` | 200 |
| 61 | Try GET attendance rules | GET `/api/v1/hr/attendance/rules` | 403 "attendance module is not enabled" |
| 62 | Try GET overtime rules | GET `/api/v1/hr/overtime-rules` | 403 |
| 63 | Re-enable attendance | PATCH `{ "attendanceEnabled": true }` | 200 |
| 64 | Disable ESS module | PATCH `{ "essEnabled": false }` | 200 |
| 65 | Try GET ESS config | GET `/api/v1/hr/ess-config` | 403 "ess module is not enabled" |
| 66 | Re-enable ESS | PATCH `{ "essEnabled": true }` | 200 |
| 67 | Disable leave module | PATCH `{ "leaveEnabled": false }` | 200 |
| 68 | Try access leave routes | GET `/api/v1/hr/leave/*` | 403 "leave module is not enabled" |
| 69 | Re-enable all modules | PATCH with all *Enabled = true | 200 |

### 1.10 Feature Toggles REMOVED

| # | Test | Method | Endpoint | Expected |
|---|------|--------|----------|----------|
| 70 | Feature toggles catalogue | GET | `/api/v1/feature-toggles/catalogue` | 404 (route removed) |
| 71 | Feature toggles list | GET | `/api/v1/feature-toggles` | 404 (route removed) |
| 72 | Feature toggles update | PUT | `/api/v1/feature-toggles/user/:id` | 404 (route removed) |

---

## Part 2: Web App UI Testing

Login as **admin@acme.local** and test each screen.

### 2.1 Company Settings Screen

**Path:** Sidebar → Configuration → Settings (or direct: `/app/company/settings`)

| # | Test | Expected |
|---|------|----------|
| 73 | Screen loads without errors | No console errors, all 3 sections visible |
| 74 | **Locale section** has 6 fields | Currency, Language, Timezone, Date Format, Time Format, Number Format |
| 75 | **Compliance section** has 3 toggles | India Compliance, GDPR Mode, Audit Trail |
| 76 | **Integrations section** has 6 toggles | Bank Integration, Razorpay, Email, WhatsApp, Biometric, eSign |
| 77 | Info tooltip on Timezone | Hover ℹ icon → "All attendance calculations use this timezone..." |
| 78 | Section descriptions visible | Muted text below each section header |
| 79 | Change timezone and save | Success toast, value persists on refresh |
| 80 | Toggle integration and save | Toggle state persists |
| 81 | Dirty state tracking | Save bar appears only when changes made |
| 82 | Reset button | Reverts to last saved state |

### 2.2 System Controls Screen

**Path:** Sidebar → Configuration → System Controls

| # | Test | Expected |
|---|------|----------|
| 83 | Screen loads with 6 sections | Module Enablement, Production, Payroll, Leave, Security, Audit |
| 84 | **Module Enablement** has 9 toggles | attendance, leave, payroll, ess, performance, recruitment, training, mobileApp, aiChatbot |
| 85 | **Security section** has number inputs | sessionTimeoutMinutes, maxConcurrentSessions, passwordMinLength, accountLockThreshold, accountLockDurationMinutes |
| 86 | Info tooltips present | Hover ℹ on Payroll Lock, Account Lock Threshold, etc. |
| 87 | Disable a module → sidebar updates | Disable performance → performance menu items hidden (requires navigation refresh) |
| 88 | Number input validation | Try entering 3 for sessionTimeout → should reject (min 5) |
| 89 | Save all controls | Success toast, all values persist |

### 2.3 Attendance Rules Screen

**Path:** Sidebar → Attendance → Attendance Rules

| # | Test | Expected |
|---|------|----------|
| 90 | Screen loads with ~10 sections | Time & Boundary, Grace & Tolerance, Day Thresholds, Late Tracking, Deduction Rules, Punch Interpretation, Auto-Processing, Rounding, Exception Handling, Capture |
| 91 | **NO phantom fields** | shiftStartTime, shiftEndTime, autoClockOut, geoFencing, geoRadiusMeters — NONE of these should exist |
| 92 | Punch Mode selector | Dropdown with FIRST_LAST, EVERY_PAIR, SHIFT_BASED |
| 93 | Rounding selectors | Working Hours Rounding dropdown, Punch Time Rounding dropdown |
| 94 | **Conditional visibility** | Set lateDeductionType to PERCENTAGE → lateDeductionValue input appears |
| 95 | **Conditional visibility** | Set lateDeductionType to NONE → lateDeductionValue input hidden |
| 96 | Exception handling toggles | ignoreLateOnLeaveDay, ignoreLateOnHoliday, ignoreLateOnWeekOff |
| 97 | Info tooltips (9 fields) | dayBoundaryTime, gracePeriod, maxLateCheckIn, punchMode, lateDeductionType, autoMarkAbsent, regularizationWindow, workingHoursRounding, ignoreLateOnHoliday |
| 98 | Save all rules | Success toast, all 26 fields persist |

### 2.4 Shift Management Screen

**Path:** Sidebar → Company → Shifts & Time

| # | Test | Expected |
|---|------|----------|
| 99 | Shift list shows columns | Name, Type (badge), Timing, Cross-Day (badge), Employees, Actions |
| 100 | **Create shift** with shiftType | Select DAY/NIGHT/FLEXIBLE from dropdown |
| 101 | **Cross-day toggle** | Enable → note about attendance date = shift start date |
| 102 | **Policy Overrides section** in form | "Leave empty to use company defaults" message visible |
| 103 | **Nullable fields** pattern | "Use Default" checkbox → when checked, field is disabled (null). Uncheck → field editable |
| 104 | **Add break** to shift | Click "Add Break" → form: name, type (FIXED/FLEXIBLE), startTime, duration, isPaid |
| 105 | **Edit break** | Click edit on break row → form pre-filled |
| 106 | **Delete break** | Confirmation modal → break removed |
| 107 | Shift with all overrides set | Create shift with grace=10, halfDay=3.5, fullDay=7.5 → verify stored |
| 108 | Info tooltips | isCrossDay, minWorkingHoursForOT, autoClockOutMinutes |

### 2.5 Overtime Rules Screen

**Path:** Sidebar → Attendance → Overtime Rules

| # | Test | Expected |
|---|------|----------|
| 109 | Screen loads with 7 sections | Eligibility, Calculation, Rate Multipliers, Caps, Approval & Payroll, Comp-Off, Rounding |
| 110 | **Granular multipliers** | weekdayMultiplier (always visible), weekendMultiplier, holidayMultiplier, nightShiftMultiplier (with "Use Weekday Rate" checkbox) |
| 111 | **Nullable caps** | dailyCap, weeklyCap, monthlyCap with "No Limit" checkbox |
| 112 | Calculation basis selector | AFTER_SHIFT / TOTAL_HOURS dropdown |
| 113 | Comp-off section | compOffEnabled toggle, compOffExpiryDays (visible only when enabled) |
| 114 | Enforce caps toggle | When enabled, shows warning about hard blocking |
| 115 | Info tooltips (6 fields) | calculationBasis, thresholdMinutes, minimumOtMinutes, enforceCaps, maxContinuousOtHours, compOffExpiryDays |
| 116 | Save all rules | Success toast, all 20 fields persist |

### 2.6 ESS Configuration Screen

**Path:** Sidebar → ESS & Workflows → ESS Config

| # | Test | Expected |
|---|------|----------|
| 117 | Screen loads with 9 sections | Payroll & Tax, Leave, Attendance, Profile & Documents, Financial, Performance, Support, Manager Self-Service, Mobile Behavior |
| 118 | **NO security section** | NO loginMethod, passwordMinLength, passwordComplexity, sessionTimeout, mfaRequired |
| 119 | **NEW MSS section** | mssViewTeam, mssApproveLeave, mssApproveAttendance, mssViewTeamAttendance |
| 120 | **NEW mobile section** | mobileOfflinePunch (toggle), mobileSyncRetryMinutes (number), mobileLocationAccuracy (select: HIGH/MEDIUM/LOW) |
| 121 | **NEW fields** | shiftSwapRequest, wfhRequest, viewOrgChart, announcementBoard, downloadPayslips, viewSalaryStructure, leaveCancellation |
| 122 | Single save button | NOT per-section save — one save for entire form |
| 123 | Enabled count | "X of Y features enabled" counter updates live |
| 124 | Info tooltips (5 fields) | shiftSwapRequest, wfhRequest, mssApproveAttendance, mobileOfflinePunch, mobileSyncRetryMinutes |
| 125 | Save all config | Success toast, all 36 fields persist |

### 2.7 Feature Toggles Screen REMOVED

| # | Test | Expected |
|---|------|----------|
| 126 | Feature Toggles NOT in sidebar | No "Feature Toggles" navigation item |
| 127 | Direct URL `/app/company/feature-toggles` | 404 or redirect (route removed) |

---

## Part 3: Mobile App UI Testing

Login as **admin@acme.local** on the mobile app. Each screen must have the **EXACT same fields and sections as the web counterpart.**

### 3.1 Company Settings

**Route:** Drawer → Company → Settings

| # | Test | Expected |
|---|------|----------|
| 128 | Same 16 fields as web | Currency, Language, Timezone, Date Format, Time Format, Number Format, 3 compliance, 6 integrations |
| 129 | Same 3 sections as web | Locale, Compliance, Integrations |
| 130 | ChipSelector for locale fields | Tap to select from options |
| 131 | Info tooltip (press to expand) | Press ℹ → description panel slides down |
| 132 | Save and verify persistence | Changes saved, visible on refresh |

### 3.2 System Controls

**Route:** Drawer → Company → System Controls

| # | Test | Expected |
|---|------|----------|
| 133 | Same 25 fields, 6 sections as web | Module Enablement, Production, Payroll, Leave, Security, Audit |
| 134 | Number inputs for security fields | Session timeout, password length, etc. |
| 135 | Section descriptions visible | Muted text under each section header |
| 136 | Info tooltips (press to expand) | Same fields as web have tooltips |

### 3.3 Attendance Rules

**Route:** Drawer → HR → Attendance Rules

| # | Test | Expected |
|---|------|----------|
| 137 | Same 26 fields, 10 sections as web | All sections match |
| 138 | Same conditional visibility | lateDeductionValue appears/hides based on type |
| 139 | ChipSelector for enum fields | PunchMode, RoundingStrategy, etc. |
| 140 | NO phantom fields | No shiftStartTime, shiftEndTime, etc. |
| 141 | Info tooltips (9 fields) | Same as web |

### 3.4 Shift Management

**Route:** Drawer → Company → Shifts

| # | Test | Expected |
|---|------|----------|
| 142 | Shift list with type badges | DAY/NIGHT/FLEXIBLE badges |
| 143 | Create/edit via modal | shiftType, startTime, endTime, isCrossDay |
| 144 | Policy overrides in modal | Nullable number fields with inherit behavior |
| 145 | Break management via bottom sheet | Add/edit/delete breaks within shift |
| 146 | Delete shift with ConfirmModal | NOT Alert.alert |

### 3.5 Overtime Rules

**Route:** Drawer → HR → Overtime Rules

| # | Test | Expected |
|---|------|----------|
| 147 | Same 20 fields, 7 sections as web | All match |
| 148 | Nullable multiplier pattern | "Use Weekday Rate" toggle |
| 149 | Nullable cap pattern | "No Limit" toggle |
| 150 | Comp-off expiry conditional | Visible only when compOffEnabled |

### 3.6 ESS Config

**Route:** Drawer → HR → ESS Config

| # | Test | Expected |
|---|------|----------|
| 151 | Same 36 fields, 9 sections as web | All match |
| 152 | NO security section | Removed |
| 153 | MSS section present | 4 toggles |
| 154 | Mobile Behavior section | offlinePunch, syncRetry, locationAccuracy |
| 155 | Single save button | Not per-section |

### 3.7 Feature Toggles REMOVED

| # | Test | Expected |
|---|------|----------|
| 156 | Feature Toggles NOT in drawer | No navigation item |
| 157 | Route doesn't exist | No `/company/feature-toggles` screen |

---

## Part 4: Cross-Platform Consistency Verification

For each screen, open web and mobile side-by-side:

| # | Screen | Check |
|---|--------|-------|
| 158 | Company Settings | Same 16 fields, same 3 sections, same defaults |
| 159 | System Controls | Same 25 fields, same 6 sections |
| 160 | Attendance Rules | Same 26 fields, same sections, same conditional visibility |
| 161 | Shifts | Same CRUD, same overrides, same break management |
| 162 | Overtime Rules | Same 20 fields, same nullable patterns |
| 163 | ESS Config | Same 36 fields, same sections, same mobile behavior fields |
| 164 | Info tooltips | Same description text on both platforms |
| 165 | Section descriptions | Same text on both platforms |
| 166 | Field NAMES | Backend field names used directly — no mapping differences |

---

## Part 5: Enforcement & Integration Testing

These tests verify the enforcement engine works end-to-end.

### 5.1 Module Enforcement Flow

| # | Test Steps | Expected |
|---|------------|----------|
| 167 | 1. Go to System Controls → disable Attendance module 2. Go to Attendance Rules screen | Screen should show error / be inaccessible (API returns 403) |
| 168 | 1. Disable ESS module 2. Go to ESS Config screen | Screen should show error (API returns 403) |
| 169 | 1. Disable Leave module 2. Try to apply for leave | Leave API returns 403 |
| 170 | Re-enable all modules | Everything works again |

### 5.2 ESS Feature Enforcement Flow

| # | Test Steps | Expected |
|---|------------|----------|
| 171 | 1. Go to ESS Config → disable `attendanceRegularization` 2. As employee, try to submit regularization | API returns 403 "attendanceRegularization not enabled" |
| 172 | 1. Disable `viewPayslips` 2. As employee, try to view payslips | API returns 403 |
| 173 | 1. Disable `leaveApplication` 2. As employee, try to apply leave | API returns 403 |
| 174 | Re-enable features | Employee can access again |

### 5.3 Shift Override Verification

| # | Test Steps | Expected |
|---|------------|----------|
| 175 | 1. Set company Attendance Rule gracePeriod = 15 min 2. Create shift with gracePeriod = 5 min 3. Record attendance for employee on that shift | Applied grace = 5 min (from shift override) |
| 176 | 1. Create shift with gracePeriod = null 2. Record attendance | Applied grace = 15 min (from attendance rules fallback) |
| 177 | Check `resolutionTrace` on attendance record | Shows `gracePeriod: "SHIFT"` or `gracePeriod: "ATTENDANCE_RULE"` |

### 5.4 Payroll Lock Enforcement

| # | Test Steps | Expected |
|---|------------|----------|
| 178 | 1. Enable payrollLock in System Controls 2. Process and approve a payroll run 3. Try to modify attendance for that period | Should be blocked with "Payroll period is locked" |
| 179 | Modify attendance for current (unlocked) period | Should succeed |

---

## Part 6: Data Integrity Checks

| # | Check | How to Verify |
|---|-------|---------------|
| 180 | Attendance record stores resolved snapshot | Query DB: `SELECT appliedGracePeriodMinutes, appliedFullDayThresholdHours, resolutionTrace, evaluationContext, finalStatusReason FROM attendance_records` |
| 181 | Changing rules doesn't affect old records | Change grace period → check old attendance records still show original value |
| 182 | Config seeder is idempotent | Run seed twice → no duplicate CompanySettings/SystemControls rows |
| 183 | Feature toggles table dropped | `SELECT * FROM feature_toggles` → table doesn't exist |
| 184 | Company.preferences column removed | `SELECT preferences FROM companies` → column doesn't exist |
| 185 | Company.systemControls column removed | `SELECT "systemControls" FROM companies` → column doesn't exist |
| 186 | CompanyShift uses startTime/endTime | `SELECT "startTime", "endTime" FROM company_shifts` → columns exist |
| 187 | CompanyShift.fromTime/toTime removed | `SELECT "fromTime" FROM company_shifts` → column doesn't exist |
| 188 | CompanyShift.downtimeSlots removed | `SELECT "downtimeSlots" FROM company_shifts` → column doesn't exist |

---

## Part 7: Edge Cases & Error Handling

| # | Test | Expected |
|---|------|----------|
| 189 | Save empty form (no changes) | Save button disabled or no API call |
| 190 | Rapid double-click save | Only one API call (debounce) |
| 191 | Network timeout during save | Error toast, form state preserved |
| 192 | Invalid enum value via API | 400 Zod validation error |
| 193 | Session expired during save | Redirect to login |
| 194 | Very long session timeout value (99999) | 400 validation error (max 1440) |
| 195 | Negative number in fields | 400 validation error |

---

## Part 8: What Is NOT Yet Implemented

These features are in the design spec but NOT implemented in this phase:

| Feature | Status | Notes |
|---------|--------|-------|
| Attendance punch with full enforcement pipeline | Partially done | `createRecord` integrates resolver but needs end-to-end testing with real punches |
| OT auto-detection from attendance | Code exists | Needs attendance records with overtime to trigger |
| Payroll using APPROVED OvertimeRequests only | Code exists | Needs OT requests to flow through approval |
| Location geo-fence validation on punch | Code exists | Needs location with geoEnabled + employee punch at location |
| Punch sequence validation (EVERY_PAIR, SHIFT_BASED) | Code exists | Backend ready, no frontend for multi-punch yet |
| Auto clock-out (autoClockOutMinutes) | Schema ready | Background job/cron not implemented |
| Auto mark absent (autoAbsentAfterDays) | Schema ready | Background job/cron not implemented |
| Regularization window enforcement | Schema ready | Not yet enforced in regularization endpoint |
| Comp-off accrual from OT | Schema ready | Leave balance integration not done |
| Industry-based templates in UI | Backend ready | Tenant onboarding wizard not updated to expose template selection |

---

## Summary: Test Count by Area

| Area | Tests | Priority |
|------|-------|----------|
| Backend API (Part 1) | 72 | Critical |
| Web UI (Part 2) | 54 | Critical |
| Mobile UI (Part 3) | 30 | Critical |
| Cross-Platform (Part 4) | 9 | High |
| Enforcement (Part 5) | 8 | Critical |
| Data Integrity (Part 6) | 9 | High |
| Edge Cases (Part 7) | 7 | Medium |
| **Total** | **189** | |

Start with Part 1 (API) to confirm backend works, then Part 2 (Web), then Part 3 (Mobile), then cross-platform and enforcement.
