# Manual QA — Attendance Mode, Leave Check-In, Multi-Shift & Weekly Review

**Date:** 2026-04-20
**Scope:** All new attendance configuration features across backend, web, and mobile

---

## Prerequisites

- A test company with at least 2 employees (Employee A, Employee B)
- At least 3 shifts configured (e.g., Morning 06:00-14:00, General 09:00-17:00, Night 22:00-06:00)
- At least 1 roster configured
- At least 1 approved leave request for Employee A (half-day morning + full-day on separate dates)
- Admin user with `hr:read`, `hr:update`, `hr:configure` permissions
- Access to both web and mobile apps

---

## Section 1: Attendance Rules — New Configuration Toggles

### 1.1 Attendance Mode Section (Web)

| # | Step | Expected Result | Pass/Fail |
|---|------|-----------------|-----------|
| 1 | Navigate to Company Admin > HR > Attendance Rules | Screen loads with all 13 sections visible | |
| 2 | Scroll to "Attendance Mode" section (Section 11) | Section shows: Attendance Mode dropdown, Leave Check-In Mode dropdown, Leave Auto-Adjustment toggle | |
| 3 | Change Attendance Mode to "Shift Relaxed" | Dropdown updates, "unsaved changes" bar appears at bottom | |
| 4 | Change Leave Check-In Mode to "Allow Till Shift End" | Dropdown updates | |
| 5 | Toggle Leave Auto-Adjustment OFF | Toggle switches to off state | |
| 6 | Click "Save Changes" | Success toast appears, values persist after page refresh | |
| 7 | Click "Discard" before saving | All fields revert to previously saved values | |

### 1.2 Multiple Shifts Section (Web)

| # | Step | Expected Result | Pass/Fail |
|---|------|-----------------|-----------|
| 8 | Scroll to "Multiple Shifts" section (Section 12) | Section shows: Multiple Shifts Per Day toggle (OFF by default) | |
| 9 | Toggle "Multiple Shifts Per Day" ON | Two additional fields appear: Min Gap Between Shifts, Max Shifts Per Day | |
| 10 | Set Min Gap to 30, Max Shifts to 3 | Fields accept values | |
| 11 | Toggle "Multiple Shifts Per Day" OFF | Additional fields disappear | |
| 12 | Save and refresh | Values persist correctly | |

### 1.3 Shift Mapping & Review Section (Web)

| # | Step | Expected Result | Pass/Fail |
|---|------|-----------------|-----------|
| 13 | Scroll to "Shift Mapping & Review" section (Section 13) | Section shows: Auto Shift Mapping toggle (OFF), Weekly Review toggle (OFF) | |
| 14 | Toggle "Auto Shift Mapping" ON | Additional fields appear: Mapping Strategy dropdown, Min Match Percentage | |
| 15 | Verify Mapping Strategy shows "Best Fit Hours" | Only option available | |
| 16 | Set Min Match Percentage to 40 | Field accepts value | |
| 17 | Toggle "Weekly Review" ON | "Weekly Review Reminders" toggle appears below | |
| 18 | Toggle "Weekly Review Reminders" ON | Toggle activates | |
| 19 | Save all changes | Success toast, all values persist after refresh | |

### 1.4 Mobile Attendance Rules Screen

| # | Step | Expected Result | Pass/Fail |
|---|------|-----------------|-----------|
| 20 | Open mobile app > Company Admin > Attendance Rules | Screen loads with all 13 sections | |
| 21 | Verify "Attendance Mode" section exists with chip selectors | Chips for SHIFT_STRICT, SHIFT_RELAXED, FULLY_FLEXIBLE visible | |
| 22 | Verify "Multiple Shifts" section with toggle + conditional fields | Same behavior as web (fields show/hide on toggle) | |
| 23 | Verify "Shift Mapping & Review" section | Same behavior as web | |
| 24 | Change values and save | Floating save bar appears, save succeeds, values persist | |
| 25 | Verify values match between web and mobile | Same API — values should be identical on both platforms | |

---

## Section 2: Leave Check-In Fix

### 2.1 STRICT Mode (Default — Current Behavior)

| # | Step | Expected Result | Pass/Fail |
|---|------|-----------------|-----------|
| 26 | Set leaveCheckInMode = STRICT, attendanceMode = SHIFT_STRICT | Settings saved | |
| 27 | Employee A has approved half-day morning leave for today | Leave visible in leave list | |
| 28 | Employee A tries to check in at 12:00 PM (shift 09:00-17:00, maxLateCheckIn=120min) | **BLOCKED** — error: "Check-in not allowed at this time" | |
| 29 | Employee A tries to check in at 10:30 AM (within 120min window) | **ALLOWED** — check-in succeeds | |

### 2.2 ALLOW_WITHIN_WINDOW Mode

| # | Step | Expected Result | Pass/Fail |
|---|------|-----------------|-----------|
| 30 | Set leaveCheckInMode = ALLOW_WITHIN_WINDOW | Settings saved | |
| 31 | Employee A has approved half-day morning leave, tries check-in at 12:00 PM | **ALLOWED** — window extended to shift end (17:00) because of half-day morning leave | |
| 32 | Employee A has approved half-day afternoon leave, tries check-in at 12:00 PM | **BLOCKED** — afternoon leave does not extend the morning window | |
| 33 | Employee B (no leave) tries check-in at 12:00 PM (same shift) | **BLOCKED** — normal maxLateCheckIn enforced | |

### 2.3 ALLOW_TILL_SHIFT_END Mode

| # | Step | Expected Result | Pass/Fail |
|---|------|-----------------|-----------|
| 34 | Set leaveCheckInMode = ALLOW_TILL_SHIFT_END | Settings saved | |
| 35 | Employee A has any approved leave (half or full), tries check-in at 16:00 | **ALLOWED** — window extends to shift end for any approved leave | |
| 36 | Employee B (no leave) tries check-in at 16:00 | **BLOCKED** — normal window enforced | |

### 2.4 FULLY_FLEXIBLE Leave Mode

| # | Step | Expected Result | Pass/Fail |
|---|------|-----------------|-----------|
| 37 | Set leaveCheckInMode = FULLY_FLEXIBLE | Settings saved | |
| 38 | Employee A has approved leave, tries check-in at any time | **ALLOWED** — no time restriction when approved leave exists | |

### 2.5 Full-Day Leave Check-In + Auto-Adjustment

| # | Step | Expected Result | Pass/Fail |
|---|------|-----------------|-----------|
| 39 | Set leaveCheckInMode = ALLOW_TILL_SHIFT_END, leaveAutoAdjustmentEnabled = true | Settings saved | |
| 40 | Employee A has approved full-day leave, checks in | **ALLOWED** with warning message about leave auto-adjustment | |
| 41 | Employee A checks out after 8+ hours | Leave is **CANCELLED**, leave balance restored | |
| 42 | Verify leave request status changed to CANCELLED | Check leave list | |
| 43 | Employee A has full-day leave, checks in, works 5 hours, checks out | Leave **CONVERTED** to half-day, 0.5 day balance restored | |
| 44 | Employee A has full-day leave, checks in, works 2 hours, checks out | Leave **KEPT** as-is, record flagged for review | |
| 45 | Set leaveAutoAdjustmentEnabled = false, repeat test 41 | Leave is NOT adjusted — kept as-is regardless of hours worked | |

---

## Section 3: Attendance Mode

### 3.1 SHIFT_STRICT (Default)

| # | Step | Expected Result | Pass/Fail |
|---|------|-----------------|-----------|
| 46 | Set attendanceMode = SHIFT_STRICT | Settings saved | |
| 47 | Employee checks in 2 hours before shift | **BLOCKED** (only 1 hour early window) | |
| 48 | Employee checks in within shift window | **ALLOWED** | |

### 3.2 SHIFT_RELAXED

| # | Step | Expected Result | Pass/Fail |
|---|------|-----------------|-----------|
| 49 | Set attendanceMode = SHIFT_RELAXED | Settings saved | |
| 50 | Employee checks in 3 hours before shift | **ALLOWED** — only verifies shift exists | |
| 51 | Employee checks in 5 hours after shift start | **ALLOWED** | |
| 52 | Employee with no assigned shift tries to check in | **ALLOWED** | |

### 3.3 FULLY_FLEXIBLE

| # | Step | Expected Result | Pass/Fail |
|---|------|-----------------|-----------|
| 53 | Set attendanceMode = FULLY_FLEXIBLE | Settings saved | |
| 54 | Employee checks in at any random time (e.g., 3 AM) | **ALLOWED** — zero time restrictions | |
| 55 | Employee with no shift assignment checks in | **ALLOWED** | |

---

## Section 4: Multiple Shifts Per Day

### 4.1 Enable Multi-Shift

| # | Step | Expected Result | Pass/Fail |
|---|------|-----------------|-----------|
| 56 | Set multipleShiftsPerDayEnabled = true, maxShiftsPerDay = 3, minGap = 30 | Settings saved | |
| 57 | Employee A checks in (Shift 1) | Record created with shiftSequence = 1 | |
| 58 | Employee A tries to check in again WITHOUT checking out first | **BLOCKED** — "Must check out from current shift before starting a new one" | |
| 59 | Employee A checks out (Shift 1 complete) | Check-out successful, worked hours calculated | |

### 4.2 Second Shift

| # | Step | Expected Result | Pass/Fail |
|---|------|-----------------|-----------|
| 60 | Employee A tries to check in immediately after checkout (within 30 min gap) | **BLOCKED** — "Minimum 30 minutes gap required between shifts" | |
| 61 | Wait 30+ minutes, Employee A checks in again | Record created with shiftSequence = 2 | |
| 62 | Employee A checks out (Shift 2 complete) | Two attendance records exist for the same date | |

### 4.3 Max Shifts Limit

| # | Step | Expected Result | Pass/Fail |
|---|------|-----------------|-----------|
| 63 | Employee A completes Shift 3 check-in and checkout | shiftSequence = 3 created | |
| 64 | Employee A tries to check in for Shift 4 | **BLOCKED** — "Maximum 3 shifts per day exceeded" | |

### 4.4 Admin Multi-Shift

| # | Step | Expected Result | Pass/Fail |
|---|------|-----------------|-----------|
| 65 | Admin marks check-in for Employee B (first shift) | Record created, shiftSequence = 1 | |
| 66 | Admin marks check-out for Employee B | Checkout successful | |
| 67 | Admin marks check-in for Employee B (second shift, after gap) | Record created, shiftSequence = 2 | |

### 4.5 Disable Multi-Shift

| # | Step | Expected Result | Pass/Fail |
|---|------|-----------------|-----------|
| 68 | Set multipleShiftsPerDayEnabled = false | Settings saved | |
| 69 | Employee tries to check in after already having checked in today | **BLOCKED** — "Already checked in today" | |

---

## Section 5: Auto Shift Mapping

### 5.1 Enable Auto-Mapping

| # | Step | Expected Result | Pass/Fail |
|---|------|-----------------|-----------|
| 70 | Set autoShiftMappingEnabled = true, attendanceMode = FULLY_FLEXIBLE, minShiftMatchPercentage = 40 | Settings saved | |
| 71 | Remove shift assignment from Employee A | Employee has no assigned shift | |
| 72 | Employee A checks in at 09:15 | Check-in allowed (no shift window to enforce) | |
| 73 | Employee A checks out at 16:45 | Check-out successful, system auto-maps to "General 09:00-17:00" shift | |
| 74 | Verify attendance record has shiftId set and isAutoMapped = true | Check DB or record detail | |

### 5.2 Mapping Below Threshold

| # | Step | Expected Result | Pass/Fail |
|---|------|-----------------|-----------|
| 75 | Set minShiftMatchPercentage = 80 | Settings saved | |
| 76 | Employee A checks in at 09:00, checks out at 12:00 (3 hrs of 8-hr shift = 37.5%) | Shift NOT auto-mapped (below 80% threshold), record has shiftId = null | |

### 5.3 Best-Fit Selection

| # | Step | Expected Result | Pass/Fail |
|---|------|-----------------|-----------|
| 77 | Set minShiftMatchPercentage = 40 | Settings saved | |
| 78 | Employee checks in at 14:00, checks out at 21:00 | System maps to shift with highest overlap (e.g., if 14:00-22:00 shift exists, maps to that) | |

---

## Section 6: Weekly Attendance Review Dashboard

### 6.1 Enable Weekly Review

| # | Step | Expected Result | Pass/Fail |
|---|------|-----------------|-----------|
| 79 | Set weeklyReviewEnabled = true | Settings saved | |

### 6.2 Web — Weekly Review Tab

| # | Step | Expected Result | Pass/Fail |
|---|------|-----------------|-----------|
| 80 | Navigate to Attendance Dashboard | Two tabs visible: "Daily View" and "Weekly Review" | |
| 81 | Click "Weekly Review" tab | Tab switches, shows week picker + summary KPIs + records table | |
| 82 | Verify week picker defaults to current week | Start and end dates match current ISO week | |
| 83 | Verify summary KPI cards show counts | Total Flagged, Missing Punch, Auto-Mapped, Worked on Leave, Late Anomaly, OT Anomaly | |
| 84 | Click a flag filter chip (e.g., "Missing Punch") | Records table filters to show only records with that flag | |
| 85 | Click "All" filter | All flagged records shown | |

### 6.3 Web — Review Actions

| # | Step | Expected Result | Pass/Fail |
|---|------|-----------------|-----------|
| 86 | Select 2-3 records via checkboxes | "Mark Selected as Reviewed" button appears | |
| 87 | Click "Mark Selected as Reviewed" | Records marked as reviewed, UI updates (reviewed indicator shown) | |
| 88 | Verify reviewed records show reviewed badge/indicator | Visual confirmation | |

### 6.4 Mobile — Weekly Review Tab

| # | Step | Expected Result | Pass/Fail |
|---|------|-----------------|-----------|
| 89 | Open mobile Attendance Dashboard | Two tabs visible at top: "Daily" and "Weekly Review" | |
| 90 | Tap "Weekly Review" | Shows week navigation, KPI cards, flag filter chips, records list | |
| 91 | Navigate to previous/next week | Week changes, data refreshes | |
| 92 | Tap a flag chip | Records filter by flag type | |
| 93 | Select records and tap "Mark Reviewed" | Records marked as reviewed | |

### 6.5 Weekly Review — Backend Endpoints

| # | Step | Expected Result | Pass/Fail |
|---|------|-----------------|-----------|
| 94 | `GET /hr/attendance/weekly-review?weekStart=2026-04-13&weekEnd=2026-04-19` | Returns `{ success: true, data: { records: [...], meta: {...} } }` with `reviewFlags` array per record | |
| 95 | `GET /hr/attendance/weekly-review/summary?weekStart=2026-04-13&weekEnd=2026-04-19` | Returns `{ success: true, data: { totalRecords, flagCounts: {...}, reviewed, unreviewed } }` | |
| 96 | `PATCH /hr/attendance/weekly-review/:id/remap-shift` with `{ shiftId: "..." }` | Record's shift updated, status re-resolved | |
| 97 | `PATCH /hr/attendance/weekly-review/:id/edit-punches` with `{ punchIn: "...", reason: "..." }` | Record's punches updated, status re-resolved, regularization fields set | |
| 98 | `PATCH /hr/attendance/weekly-review/mark-reviewed` with `{ recordIds: ["..."] }` | Records marked reviewed, returns count | |

---

## Section 7: Cross-Feature Integration

### 7.1 Flexible Mode + Auto-Mapping + Weekly Review

| # | Step | Expected Result | Pass/Fail |
|---|------|-----------------|-----------|
| 99 | Set attendanceMode = FULLY_FLEXIBLE, autoShiftMappingEnabled = true, weeklyReviewEnabled = true | All three enabled | |
| 100 | Employee (no shift assigned) checks in at 08:00, checks out at 16:30 | Check-in/out allowed, shift auto-mapped, record appears in weekly review with AUTO_MAPPED flag | |

### 7.2 Multi-Shift + OT

| # | Step | Expected Result | Pass/Fail |
|---|------|-----------------|-----------|
| 101 | Enable multipleShiftsPerDayEnabled, set OT dailyCapHours = 4, enforceCaps = true | Settings saved | |
| 102 | Employee works Shift 1 (8 hrs, 2 hrs OT) + Shift 2 (6 hrs, 1 hr OT) | Total OT = 3 hrs, within 4-hr cap — no capping applied | |
| 103 | Employee works Shift 1 (10 hrs, 4 hrs OT) + Shift 2 (8 hrs, 2 hrs OT) | Total OT = 6 hrs, exceeds 4-hr cap — OT distributed proportionally to cap | |

### 7.3 Leave + Flexible + Multi-Shift

| # | Step | Expected Result | Pass/Fail |
|---|------|-----------------|-----------|
| 104 | Employee has approved half-day morning leave + multipleShiftsPerDayEnabled | Both features active | |
| 105 | Employee checks in at 13:00 (afternoon), works Shift 1, checks out | Leave check-in allowed, shift recorded as shiftSequence=1 | |
| 106 | Employee checks in again for Shift 2 after gap | shiftSequence=2 created | |

---

## Section 8: Edge Cases

| # | Step | Expected Result | Pass/Fail |
|---|------|-----------------|-----------|
| 107 | Night (cross-day) shift + leaveCheckInMode = ALLOW_TILL_SHIFT_END | Window wraps midnight correctly, leave extends to shift end on next day | |
| 108 | Employee with no shift, attendanceMode = SHIFT_STRICT | Check-in allowed (no shift = no window to enforce) | |
| 109 | Save attendance rules with invalid combo (autoShiftMapping=true, attendanceMode=SHIFT_STRICT) | Should work — auto-mapping runs post-checkout regardless of attendance mode | |
| 110 | Set maxShiftsPerDay = null (unlimited) | No cap enforced — employee can create unlimited shifts | |
| 111 | Set minGapBetweenShiftsMinutes = null | No gap enforced — immediate re-check-in after checkout | |
| 112 | Weekly review on a week with zero flagged records | Empty state shown with zero counts | |
| 113 | Concurrent check-in attempts (race condition) | Only one record created per shiftSequence due to unique constraint | |

---

## Section 9: Data Consistency

| # | Step | Expected Result | Pass/Fail |
|---|------|-----------------|-----------|
| 114 | Change settings on web, verify on mobile | Values match on both platforms | |
| 115 | Change settings on mobile, verify on web | Values match on both platforms | |
| 116 | Check-in via mobile, verify record visible in web dashboard | Same record appears | |
| 117 | Check-in via web (admin), verify record in mobile ESS | Same record appears | |
| 118 | Verify all new fields returned by `GET /hr/attendance/rules` | All 11 new fields present in response | |
| 119 | Verify existing attendance records still work (shiftSequence defaults to 1) | No broken records, all existing data intact | |

---

## Section 10: Cron Jobs (Requires Wait or Manual Trigger)

| # | Step | Expected Result | Pass/Fail |
|---|------|-----------------|-----------|
| 120 | Create a completed record with no shift + autoShiftMapping ON | Record has shiftId = null | |
| 121 | Trigger auto-shift-mapping cron (runs daily at 2:30 AM) or wait | Record's shiftId updated, isAutoMapped = true | |
| 122 | Enable weeklyReviewRemindersEnabled, let Monday 9 AM pass | HR admins receive notification about unreviewed records | |

---

## Test Environment Notes

- **Backend base URL:** `http://localhost:3000/api` (or staging URL)
- **Web app URL:** `http://localhost:5173` (or staging URL)
- **Mobile app:** Expo dev client or TestFlight/Internal testing build
- **DB access:** Prisma Studio (`pnpm db:studio`) for verifying raw records
- **Logs:** Check server console for auto-mapping and leave adjustment log lines

---

**Total Test Cases:** 122
**Critical Path:** Sections 2, 3, 4 (check-in/out flow changes)
**High Priority:** Sections 5, 6 (new features)
**Medium Priority:** Sections 7, 8 (integration + edge cases)
