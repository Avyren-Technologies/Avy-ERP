# Sub-project 3: ESS & Display Enhancements — Design Spec

## Goal

Fix display gaps where data is collected/calculated but not shown to employees or admins: attendance dashboard enhancements, employee payslip improvements, and leave display gaps.

## Verified Gaps

### Attendance Display
| # | Gap | Current State |
|---|-----|---------------|
| A10 | Geofence status not on attendance dashboard | Shown at check-in time only, not in dashboard table/detail |
| A11 | Employee can't see own GPS | MyAttendanceScreen shows times only |
| A12 | Resolution trace never exposed | `resolutionTrace` stored, zero frontend display |
| A13 | Break deduction not shown | `appliedBreakDeductionMinutes` stored, never displayed |
| E12 | No map view for attendance locations | Google Maps exists for geofence config, not for attendance |

### Payslip Display
| # | Gap | Current State |
|---|-----|---------------|
| E1 | No employee CTC/salary structure view | Payslip exists but no CTC breakdown screen |
| E5 | Web employee payslip missing employer contributions | Admin sees them, employee does not |
| E6 | Payslip missing OT rate breakdown | Only `overtimeAmount` shown |
| E7-E9 | Missing LOP formula, TDS breakdown | Amounts shown, no calculation detail |
| E10 | No YTD totals on payslip | No cumulative fields |
| E11 | No leave balance on payslip | Not included |

### Leave Display
| # | Gap | Current State |
|---|-----|---------------|
| E2 | Leave encashment no employee UI | HR report exists, no employee view |
| E16 | Leave accrual schedule hidden | Config exists, no employee display |
| E17 | Sandwich rule not shown in approval | Calculated silently |
| E18 | Employee can't see carry-forward breakdown | Admin sees full breakdown, employee sees only total |

---

## Fix A10 + A11 + A13: Attendance Dashboard & Employee View Enhancements

### Web Attendance Dashboard (`AttendanceDashboardScreen.tsx`)

**Add to detail modal** (currently shows geo coordinates):
- **Geofence Status Badge**: Color-coded badge (INSIDE = green, OUTSIDE = red, NO_LOCATION = gray)
- **Break Deduction**: Show `appliedBreakDeductionMinutes` as "Break: X min deducted"

### Employee Attendance Screen (Web `MyAttendanceScreen.tsx` + Mobile `my-attendance-screen.tsx`)

**Add to day detail card**:
- Location name (from attendance record)
- Geofence status badge
- GPS coordinates (if available) — formatted as "Location: Lat, Lng"
- Break deduction minutes

### Backend Change
The existing attendance API responses likely already include these fields (they're in the select/include). Verify and add if missing:
- `geoStatus`, `checkInLatitude`, `checkInLongitude`, `checkOutLatitude`, `checkOutLongitude`
- `appliedBreakDeductionMinutes`
- `locationName` (from related location)

---

## Fix A12: Resolution Trace (Admin Only)

### Design
Show `resolutionTrace` as an expandable "Policy Applied" section in the admin attendance detail modal. This is admin-only context — employees don't need to see the internal resolution logic.

**Display format**:
```
Policy Applied:
  Source: SHIFT (General Shift)
  Grace Period: 15 min
  Full Day Threshold: 8h
  Half Day Threshold: 4h
  Punch Mode: FIRST_LAST
```

Parse the JSON `resolutionTrace` and render as key-value pairs in a collapsible section.

---

## Fix E12: Map View for Attendance Locations (Admin)

### Design
Add a small map to the attendance detail modal showing the check-in/check-out location pin:
- Use existing `@react-google-maps/api` (already installed in web)
- Show a single marker at check-in coordinates
- Show second marker at check-out coordinates (if different)
- If geofence exists, show the geofence circle/polygon overlay
- Map is view-only, not interactive

**Web only** — mobile can show coordinates as text (adding a full MapView to a bottom sheet is heavy).

---

## Fix E5: Web Employee Payslip — Add Employer Contributions

### Current State
- Admin `PayslipScreen.tsx`: Shows `Earnings`, `Deductions`, `Employer Contributions` sections
- Employee `MyPayslipsScreen.tsx`: Shows only `Earnings` and `Deductions`

### Fix
In `MyPayslipsScreen.tsx` detail modal, add a third section after Deductions:

```typescript
{/* Employer Contributions */}
{employerContributions && employerContributions.length > 0 && (
  <div>
    <h4>Employer Contributions</h4>
    {employerContributions.map(({ label, amount }) => (
      <div key={label}>
        <span>{label}</span>
        <span>{formatCurrency(amount)}</span>
      </div>
    ))}
  </div>
)}
```

The data is already returned by the API — just not rendered in the employee view.

**Mobile**: Verify mobile payslip screen already shows employer contributions (previous audit confirmed it does).

---

## Fix E6-E9: Payslip Detail Enhancements

### OT Breakdown (E6)
Currently shows only `overtimeAmount`. Add:
- OT Hours: `overtimeHours` (already on PayrollEntry/Payslip)
- This gives context: "OT: 12.5 hrs — ₹4,500"

### LOP Detail (E7-E8)
Currently shows `lopDays`. Add contextual info:
- "LOP: 3 days (Working days: 26, Present: 23)"
- Data is already available: `workingDays`, `presentDays`, `lopDays`

### TDS Note (E9)
Add a brief TDS label:
- "TDS (Provisional)" when `tdsProvisional = true`
- This is already stored on the Payslip model

---

## Fix E10: YTD Totals on Payslip

### Design
This requires a backend change to compute YTD values when returning payslip data.

**Backend**: In the payslip detail endpoint, add YTD computation:
```typescript
// Fetch all payslips for the employee in the same FY
const fyStart = month >= 4 ? year : year - 1; // FY starts April
const ytdPayslips = await platformPrisma.payslip.findMany({
  where: { employeeId, year: { in: [fyStart, fyStart + 1] }, /* FY filter */ },
});
const ytdGross = ytdPayslips.reduce((sum, p) => sum + Number(p.grossEarnings ?? 0), 0);
const ytdDeductions = ytdPayslips.reduce((sum, p) => sum + Number(p.totalDeductions ?? 0), 0);
const ytdNet = ytdPayslips.reduce((sum, p) => sum + Number(p.netPay ?? 0), 0);
const ytdTds = ytdPayslips.reduce((sum, p) => sum + Number(p.tdsAmount ?? 0), 0);
```

**Frontend**: Add a "Year-to-Date" section at the bottom of the payslip detail:
```
Year-to-Date (FY 2025-26)
  Gross Earnings:  ₹12,50,000
  Total Deductions: ₹3,25,000
  TDS Deducted:    ₹1,50,000
  Net Pay:         ₹9,25,000
```

---

## Fix E11: Leave Balance on Payslip

### Design
This is informational — show current leave balances as a footer section on the payslip.

**Backend**: In payslip detail endpoint, include leave balance query:
```typescript
const leaveBalances = await platformPrisma.leaveBalance.findMany({
  where: { employeeId, companyId, year },
  include: { leaveType: { select: { name: true, code: true } } },
});
```

**Frontend**: Add "Leave Balance" section at bottom of payslip:
```
Leave Balance (as of April 2026)
  Casual Leave:  4 / 12
  Earned Leave:  8 / 18
  Sick Leave:    2 / 6
```

---

## Fix E2: Leave Encashment Employee View

### Design
Add a small "Encashment Eligible" indicator to the employee leave balance screen.

For each leave type where `encashmentAllowed = true`:
- Show balance eligible for encashment
- Show estimated encashment value: `eligibleDays × (basicSalary / 26) × encashmentRate`

**Backend**: Add encashment info to the leave balance API response (compute from LeaveType config + current balance).

**Frontend**: Show a subtle "Encashable: X days (~₹Y)" label under the leave balance card for eligible types.

---

## Fix E16: Leave Accrual Schedule

### Design
Show when the next accrual will happen on the employee leave balance screen.

For each leave type with `accrualFrequency` set:
- MONTHLY: "Next accrual: 1st of next month"
- QUARTERLY: "Next accrual: 1st of next quarter"
- ANNUAL: "Accrued at year start"
- UPFRONT: "Full balance credited at start"

**Backend**: Include `accrualFrequency` and `accrualDay` in the leave balance API response.

**Frontend**: Show as a subtle info line under each leave type card.

---

## Fix E17: Sandwich Rule Visibility

### Design
When an employee applies for leave and the sandwich rule affects the day count, show a note:

"Note: 2 weekend days are included due to sandwich rule (total: 5 days for 3 working days)"

**Backend**: The leave application response should include `sandwichDays` count when applicable.

**Frontend**: Show the note in the leave application confirmation dialog and in the leave detail view.

---

## Fix E18: Carry-Forward Breakdown

### Design
Show the leave balance composition to employees:

```
Earned Leave: 15 days
  Carried forward: 5 days
  Accrued this year: 12 days
  Used: 2 days
```

**Backend**: The API already returns `openingBalance`, `accrued`, `taken`, `adjusted`. No backend change needed.

**Frontend**: In employee leave balance screen, show the breakdown instead of just the total:
- Opening Balance (label: "Carried forward")
- Accrued
- Used
- Balance remaining

---

## Files Changed

### Backend
| File | Change |
|------|--------|
| Payslip detail endpoint in ess.service.ts or payslip.service.ts | Add YTD computation + leave balance |
| Leave balance endpoint in ess.service.ts | Add encashment info + accrual schedule fields |
| Leave application endpoint | Add sandwichDays to response |

### Web
| File | Change |
|------|--------|
| `AttendanceDashboardScreen.tsx` | Add geoStatus badge, break deduction, map view, resolution trace |
| `MyAttendanceScreen.tsx` | Add GPS, geoStatus, break deduction to day detail |
| `MyPayslipsScreen.tsx` | Add employer contributions section, OT breakdown, LOP detail, YTD, leave balance |
| `MyLeaveScreen.tsx` | Add carry-forward breakdown, accrual schedule, encashment indicator |

### Mobile
| File | Change |
|------|--------|
| `my-attendance-screen.tsx` | Add GPS text, geoStatus badge, break deduction |
| `payslip-screen.tsx` or `my-payslips-screen.tsx` | Add OT breakdown, LOP detail, YTD, leave balance |
| `my-leave-screen.tsx` | Add carry-forward breakdown, accrual schedule, encashment indicator |
