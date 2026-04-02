# Date/Time Format & Timezone Enforcement — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Enforce company-specific date format, time format, and timezone across all ~150+ instances in web, mobile, and backend.

**Architecture:** Create a Luxon-based `createCompanyFormatter()` factory + `useCompanyFormatter()` React hook on both frontends. Backend fixes replace raw `Date.getDay()`/`getMonth()` with Luxon `DateTime.setZone(companyTimezone)`. Backend continues returning UTC ISO strings — formatting is frontend-only.

**Tech Stack:** Luxon (all 3 codebases), React Query (frontend settings cache), Zustand (existing auth store for settings access)

**Spec:** `docs/superpowers/specs/2026-04-02-date-time-timezone-enforcement-design.md`

---

## File Structure

### New Files

| File | Codebase | Responsibility |
|------|----------|----------------|
| `src/lib/format/company-formatter.ts` | web | Formatter factory: `createCompanyFormatter(settings)` → pure formatting functions |
| `src/hooks/useCompanyFormatter.ts` | web | React hook that fetches settings + returns bound formatter |
| `src/lib/format/company-formatter.ts` | mobile | Same formatter factory (adapted imports) |
| `src/hooks/use-company-formatter.ts` | mobile | Same hook (adapted imports) |

### Modified Files — Backend (Timezone Safety)

| File | Lines | Change |
|------|-------|--------|
| `src/modules/hr/attendance/attendance.service.ts` | 195, 398-399, 424, 532, 562-563, 743, 968, 1151, 1248, 1950, 2363, 2595 | `getDay()`/`getMonth()`/`getFullYear()` → Luxon with company TZ |
| `src/modules/hr/leave/leave.service.ts` | 599, 1541 | `getDay()` for weekend check → Luxon |
| `src/modules/hr/payroll-run/payroll-run.service.ts` | 80 | `getDay()` for working day calc → Luxon |
| `src/modules/hr/ess/ess.service.ts` | 2516, 2661, 2808 | `getDay()` → Luxon (some already use Luxon partially) |
| `src/modules/hr/ess/ess.controller.ts` | 569-570, 960-961, 1272 | `getMonth()`/`getFullYear()`/`getDay()` → Luxon |
| `src/modules/hr/analytics/services/analytics.service.ts` | 67, 355-366, 393-394, 417-479, 529 | `getMonth()`/`getFullYear()` → Luxon |

### Modified Files — Web (Formatting Replacement)

| File | Approx Changes | Pattern |
|------|---------------|---------|
| `src/features/employee/DynamicDashboardScreen.tsx` | 4 | time, shiftTime |
| `src/features/company-admin/hr/AttendanceDashboardScreen.tsx` | 4 | time, shiftTime |
| `src/features/company-admin/hr/ShiftCheckInScreen.tsx` | 6 | time, shiftTime |
| `src/features/company-admin/ShiftManagementScreen.tsx` | 2 | shiftTime |
| `src/features/company-admin/hr/ChatbotScreen.tsx` | 1 | time |
| `src/features/support/TicketChatScreen.tsx` | 1 | time |
| `src/features/super-admin/CompanyDetailScreen.tsx` | 2 | date, time |
| All other screens with `toLocaleDateString` / `toLocaleTimeString` | ~15 | date, time |

### Modified Files — Mobile (Formatting Replacement)

| File | Approx Changes | Pattern |
|------|---------------|---------|
| `src/features/employee/dashboard-screen.tsx` | 5 | time, shiftTime |
| `src/features/company-admin/hr/shift-check-in-screen.tsx` | 5 | time, date, shiftTime |
| `src/features/company-admin/hr/attendance-dashboard-screen.tsx` | 2 | time, shiftTime |
| `src/features/company-admin/hr/my-attendance-screen.tsx` | 1 | time |
| `src/features/company-admin/shift-management-screen.tsx` | 2 | shiftTime |
| `src/features/company-admin/hr/chatbot-screen.tsx` | 1 | time |
| `src/features/support/ticket-chat-screen.tsx` | 1 | time |
| `src/features/super-admin/audit-log-screen.tsx` | 2 | date, time |
| `src/features/super-admin/company-detail-screen.tsx` | 2 | date, time |
| All other screens with `toLocaleDateString` / `toLocaleTimeString` | ~10 | date, time |

---

## Task 1: Install Luxon on Web and Mobile

**Files:**
- Modify: `web-system-app/package.json`
- Modify: `mobile-app/package.json`

- [ ] **Step 1: Install luxon in web app**

```bash
cd /Users/chetan/Documents/Avyren-Technologies/Products/Mobile-ERP/web-system-app
pnpm add luxon
pnpm add -D @types/luxon
```

- [ ] **Step 2: Install luxon in mobile app**

```bash
cd /Users/chetan/Documents/Avyren-Technologies/Products/Mobile-ERP/mobile-app
pnpm add luxon
pnpm add -D @types/luxon
```

- [ ] **Step 3: Verify imports work**

```bash
cd /Users/chetan/Documents/Avyren-Technologies/Products/Mobile-ERP/web-system-app && npx tsc --noEmit 2>&1 | head -5
cd /Users/chetan/Documents/Avyren-Technologies/Products/Mobile-ERP/mobile-app && npx tsc --noEmit 2>&1 | grep -v node_modules | head -5
```

---

## Task 2: Create Web Formatter Utility + Hook

**Files:**
- Create: `web-system-app/src/lib/format/company-formatter.ts`
- Create: `web-system-app/src/hooks/useCompanyFormatter.ts`

- [ ] **Step 1: Create the formatter factory**

Create `web-system-app/src/lib/format/company-formatter.ts`:

```typescript
import { DateTime } from 'luxon';

export interface CompanyFormatSettings {
  dateFormat: 'DD/MM/YYYY' | 'MM/DD/YYYY' | 'YYYY-MM-DD';
  timeFormat: 'TWELVE_HOUR' | 'TWENTY_FOUR_HOUR';
  timezone: string;
}

export const DEFAULT_FORMAT_SETTINGS: CompanyFormatSettings = {
  dateFormat: 'DD/MM/YYYY',
  timeFormat: 'TWELVE_HOUR',
  timezone: 'Asia/Kolkata',
};

const DATE_FORMAT_MAP: Record<string, string> = {
  'DD/MM/YYYY': 'dd/MM/yyyy',
  'MM/DD/YYYY': 'MM/dd/yyyy',
  'YYYY-MM-DD': 'yyyy-MM-dd',
};

const TIME_FORMAT_MAP: Record<string, string> = {
  'TWELVE_HOUR': 'h:mm a',
  'TWENTY_FOUR_HOUR': 'HH:mm',
};

const TIME_WITH_SECONDS_MAP: Record<string, string> = {
  'TWELVE_HOUR': 'h:mm:ss a',
  'TWENTY_FOUR_HOUR': 'HH:mm:ss',
};

export interface CompanyFormatter {
  date(iso: string): string;
  time(iso: string): string;
  timeWithSeconds(iso: string): string;
  dateTime(iso: string): string;
  shiftTime(hhmm: string): string;
  relativeDate(iso: string): string;
  parseToZoned(iso: string): DateTime;
}

export function createCompanyFormatter(settings: CompanyFormatSettings): CompanyFormatter {
  const dateFmt = DATE_FORMAT_MAP[settings.dateFormat] ?? 'dd/MM/yyyy';
  const timeFmt = TIME_FORMAT_MAP[settings.timeFormat] ?? 'h:mm a';
  const timeSecFmt = TIME_WITH_SECONDS_MAP[settings.timeFormat] ?? 'h:mm:ss a';
  const tz = settings.timezone || 'Asia/Kolkata';

  function parseToZoned(iso: string): DateTime {
    if (!iso) return DateTime.invalid('empty input');
    const dt = DateTime.fromISO(iso, { zone: 'utc' }).setZone(tz);
    if (!dt.isValid) {
      // Try parsing as date-only (yyyy-MM-dd)
      const dateOnly = DateTime.fromISO(iso, { zone: tz });
      return dateOnly;
    }
    return dt;
  }

  function date(iso: string): string {
    const dt = parseToZoned(iso);
    return dt.isValid ? dt.toFormat(dateFmt) : '—';
  }

  function time(iso: string): string {
    const dt = parseToZoned(iso);
    return dt.isValid ? dt.toFormat(timeFmt) : '—';
  }

  function timeWithSeconds(iso: string): string {
    const dt = parseToZoned(iso);
    return dt.isValid ? dt.toFormat(timeSecFmt) : '—';
  }

  function dateTime(iso: string): string {
    const dt = parseToZoned(iso);
    return dt.isValid ? dt.toFormat(`${dateFmt} ${timeFmt}`) : '—';
  }

  function shiftTime(hhmm: string): string {
    if (!hhmm) return '—';
    // Shift times are local company time — no TZ conversion, format only
    const dt = DateTime.fromFormat(hhmm, 'HH:mm');
    return dt.isValid ? dt.toFormat(timeFmt) : hhmm;
  }

  function relativeDate(iso: string): string {
    const dt = parseToZoned(iso);
    if (!dt.isValid) return '—';
    const now = DateTime.now().setZone(tz);
    const diff = dt.startOf('day').diff(now.startOf('day'), 'days').days;
    if (Math.abs(diff) < 0.5) return 'Today';
    if (diff > -1.5 && diff < -0.5) return 'Yesterday';
    if (diff > 0.5 && diff < 1.5) return 'Tomorrow';
    return dt.toFormat(dateFmt);
  }

  return { date, time, timeWithSeconds, dateTime, shiftTime, relativeDate, parseToZoned };
}
```

- [ ] **Step 2: Create the React hook**

Create `web-system-app/src/hooks/useCompanyFormatter.ts`:

```typescript
import { useMemo } from 'react';
import { useCompanySettings } from '@/features/company-admin/api/use-company-admin-queries';
import {
  createCompanyFormatter,
  DEFAULT_FORMAT_SETTINGS,
  type CompanyFormatter,
  type CompanyFormatSettings,
} from '@/lib/format/company-formatter';

export function useCompanyFormatter(): CompanyFormatter {
  const { data } = useCompanySettings();
  const raw = data?.data;

  const settings: CompanyFormatSettings = useMemo(() => ({
    dateFormat: raw?.dateFormat ?? DEFAULT_FORMAT_SETTINGS.dateFormat,
    timeFormat: raw?.timeFormat ?? DEFAULT_FORMAT_SETTINGS.timeFormat,
    timezone: raw?.timezone ?? DEFAULT_FORMAT_SETTINGS.timezone,
  }), [raw?.dateFormat, raw?.timeFormat, raw?.timezone]);

  return useMemo(() => createCompanyFormatter(settings), [settings]);
}
```

- [ ] **Step 3: Verify `useCompanySettings` staleTime**

Read `web-system-app/src/features/company-admin/api/use-company-admin-queries.ts` and verify/update `useCompanySettings()` to have `staleTime: Infinity` and `gcTime: Infinity`. If not set, update:

```typescript
export function useCompanySettings() {
  return useQuery({
    queryKey: companyAdminKeys.settings(),
    queryFn: () => companyAdminApi.getSettings(),
    staleTime: Infinity,
    gcTime: Infinity,
  });
}
```

- [ ] **Step 4: Type-check**

```bash
cd /Users/chetan/Documents/Avyren-Technologies/Products/Mobile-ERP/web-system-app && npx tsc --noEmit
```

- [ ] **Step 5: Commit**

```bash
git add web-system-app/src/lib/format/company-formatter.ts web-system-app/src/hooks/useCompanyFormatter.ts
git commit -m "feat(web): add CompanyFormatter utility and useCompanyFormatter hook"
```

---

## Task 3: Create Mobile Formatter Utility + Hook

**Files:**
- Create: `mobile-app/src/lib/format/company-formatter.ts`
- Create: `mobile-app/src/hooks/use-company-formatter.ts`

- [ ] **Step 1: Create the formatter factory**

Create `mobile-app/src/lib/format/company-formatter.ts` — **identical content** to the web version (same `createCompanyFormatter`, `CompanyFormatter`, `CompanyFormatSettings`, `DEFAULT_FORMAT_SETTINGS`). Copy exactly from Task 2 Step 1.

- [ ] **Step 2: Create the React hook**

Create `mobile-app/src/hooks/use-company-formatter.ts`:

```typescript
import { useMemo } from 'react';
import { useCompanySettings } from '@/features/company-admin/api/use-company-admin-queries';
import {
  createCompanyFormatter,
  DEFAULT_FORMAT_SETTINGS,
  type CompanyFormatter,
  type CompanyFormatSettings,
} from '@/lib/format/company-formatter';

export function useCompanyFormatter(): CompanyFormatter {
  const { data } = useCompanySettings();
  const raw = (data as any)?.data;

  const settings: CompanyFormatSettings = useMemo(() => ({
    dateFormat: raw?.dateFormat ?? DEFAULT_FORMAT_SETTINGS.dateFormat,
    timeFormat: raw?.timeFormat ?? DEFAULT_FORMAT_SETTINGS.timeFormat,
    timezone: raw?.timezone ?? DEFAULT_FORMAT_SETTINGS.timezone,
  }), [raw?.dateFormat, raw?.timeFormat, raw?.timezone]);

  return useMemo(() => createCompanyFormatter(settings), [settings]);
}
```

- [ ] **Step 3: Verify `useCompanySettings` exists in mobile queries**

Read `mobile-app/src/features/company-admin/api/use-company-admin-queries.ts`. If `useCompanySettings()` doesn't exist, search for how company settings are fetched. If it exists, update `staleTime: Infinity, gcTime: Infinity`. If the query fetches `companyAdminApi.getSettings()`, find that API call and confirm the endpoint.

- [ ] **Step 4: Type-check**

```bash
cd /Users/chetan/Documents/Avyren-Technologies/Products/Mobile-ERP/mobile-app && npx tsc --noEmit 2>&1 | grep -v node_modules | head -10
```

- [ ] **Step 5: Commit**

```bash
git add mobile-app/src/lib/format/company-formatter.ts mobile-app/src/hooks/use-company-formatter.ts
git commit -m "feat(mobile): add CompanyFormatter utility and useCompanyFormatter hook"
```

---

## Task 4: Backend Timezone Safety — Attendance Service

**Files:**
- Modify: `avy-erp-backend/src/modules/hr/attendance/attendance.service.ts`

This is the most critical backend fix. The attendance service uses `new Date().getDay()` to determine weekday/weekend and `getMonth()`/`getFullYear()` for month boundaries — all using server timezone instead of company timezone.

- [ ] **Step 1: Identify the company timezone fetch pattern**

The service already imports and uses `parseInCompanyTimezone` from `../../shared/utils/timezone`. Find where `companySettings` is fetched (should be via `getCachedCompanySettings(companyId)` or similar). Read the existing timezone handling to understand the pattern.

- [ ] **Step 2: Replace all `getDay()` calls**

For each `getDay()` usage (lines 195, 532, 968, 1248, 1950, 2595), replace with Luxon:

```typescript
// BEFORE:
const dow = dayOfWeek[attendanceDate.getDay()];

// AFTER:
const dt = DateTime.fromJSDate(attendanceDate).setZone(companyTimezone);
const dow = dayOfWeek[dt.weekday % 7]; // Luxon: 1=Mon..7=Sun → 0=Sun via % 7
```

Note: Luxon weekday is 1=Monday..7=Sunday. JS `getDay()` is 0=Sunday..6=Saturday. The `dayOfWeek` array in the codebase likely uses JS convention (index 0=Sunday). So: `dt.weekday % 7` converts Luxon convention to JS convention.

- [ ] **Step 3: Replace all `getMonth()` / `getFullYear()` calls for month boundaries**

For lines 398-399, 424, 562-563, 743, 1151, 2363:

```typescript
// BEFORE:
const monthStart = new Date(recordDate.getFullYear(), recordDate.getMonth(), 1);
const monthEnd = new Date(recordDate.getFullYear(), recordDate.getMonth() + 1, 0);

// AFTER:
const dtRecord = DateTime.fromJSDate(recordDate).setZone(companyTimezone);
const monthStart = dtRecord.startOf('month').toJSDate();
const monthEnd = dtRecord.endOf('month').toJSDate();
```

- [ ] **Step 4: Ensure `companyTimezone` is available**

Verify that `companyTimezone` (from `companySettings.timezone ?? 'Asia/Kolkata'`) is available in each method that needs it. If a method doesn't currently fetch company settings, add the fetch using the existing cached utility.

- [ ] **Step 5: Type-check and verify**

```bash
cd /Users/chetan/Documents/Avyren-Technologies/Products/Mobile-ERP/avy-erp-backend && npx tsc --noEmit
```

- [ ] **Step 6: Commit**

```bash
git add avy-erp-backend/src/modules/hr/attendance/attendance.service.ts
git commit -m "fix(backend): use Luxon with company timezone for attendance day/month calculations"
```

---

## Task 5: Backend Timezone Safety — Leave, Payroll, ESS, Analytics

**Files:**
- Modify: `avy-erp-backend/src/modules/hr/leave/leave.service.ts` (lines 599, 1541)
- Modify: `avy-erp-backend/src/modules/hr/payroll-run/payroll-run.service.ts` (line 80)
- Modify: `avy-erp-backend/src/modules/hr/ess/ess.service.ts` (lines 2516, 2661, 2808)
- Modify: `avy-erp-backend/src/modules/hr/ess/ess.controller.ts` (lines 569-570, 960-961, 1272)
- Modify: `avy-erp-backend/src/modules/hr/analytics/services/analytics.service.ts` (multiple getMonth/getFullYear)

- [ ] **Step 1: Fix leave service**

`leave.service.ts` line 599: `dayNames[current.getDay()]` — replace with Luxon:
```typescript
const dtCurrent = DateTime.fromJSDate(current).setZone(companyTimezone);
dayNames[dtCurrent.weekday % 7]
```

Line 1541: `current.getDay()` (weekend check) — same fix.

Ensure `companyTimezone` is available (from `getCachedCompanySettings`).

- [ ] **Step 2: Fix payroll service**

`payroll-run.service.ts` line 80: `new Date(year, month - 1, d).getDay()` — replace:
```typescript
DateTime.fromObject({ year, month, day: d }, { zone: companyTimezone }).weekday % 7
```

- [ ] **Step 3: Fix ESS service and controller**

`ess.service.ts` lines 2516, 2661: `jsDate.getDay()` — these are inside dashboard methods that already use Luxon. Replace the `toJSDate().getDay()` pattern with `dt.weekday % 7`.

`ess.controller.ts` lines 569-570, 960-961: `new Date().getMonth() + 1` / `new Date().getFullYear()` — replace with:
```typescript
const now = DateTime.now().setZone(companyTimezone);
const month = now.month;
const year = now.year;
```

Line 1272: `dayOfWeek[attendanceDate.getDay()]` — same Luxon fix as attendance service.

- [ ] **Step 4: Fix analytics service**

`analytics.service.ts`: Multiple `getMonth()` / `getFullYear()` calls on date filter parameters. These are filtering by calendar month/year, so convert:
```typescript
const dt = DateTime.fromJSDate(dateTo).setZone(companyTimezone);
const month = dt.month;
const year = dt.year;
```

Note: Analytics date range filters come from frontend. Since the frontend will now send timezone-aware dates, the analytics service should parse them with company timezone.

- [ ] **Step 5: Type-check**

```bash
cd /Users/chetan/Documents/Avyren-Technologies/Products/Mobile-ERP/avy-erp-backend && npx tsc --noEmit
```

- [ ] **Step 6: Commit**

```bash
git add avy-erp-backend/src/modules/hr/leave/ avy-erp-backend/src/modules/hr/payroll-run/ avy-erp-backend/src/modules/hr/ess/ avy-erp-backend/src/modules/hr/analytics/
git commit -m "fix(backend): enforce company timezone in leave, payroll, ESS, and analytics services"
```

---

## Task 6: Replace All Web Formatting Instances

**Files:** All web-system-app screen files listed in the file structure section above (~15 files).

This is the largest task. For each file:
1. Add `import { useCompanyFormatter } from '@/hooks/useCompanyFormatter';`
2. Add `const fmt = useCompanyFormatter();` at the top of the component
3. Replace every `toLocaleDateString(...)` → `fmt.date(isoString)`
4. Replace every `toLocaleTimeString(...)` → `fmt.time(isoString)` or `fmt.timeWithSeconds(isoString)`
5. Replace every raw shift time `{shift.startTime}` → `{fmt.shiftTime(shift.startTime)}`
6. Replace every `toLocaleString()` → `fmt.dateTime(isoString)`

- [ ] **Step 1: Replace in DynamicDashboardScreen.tsx**

Read the file. Find all 4 instances:
- Line 138: `d.toLocaleTimeString(...)` → use `fmt.time()`
- Line 633: `{shift.startTime} — {shift.endTime}` → `{fmt.shiftTime(shift.startTime)} — {fmt.shiftTime(shift.endTime)}`
- Line 680: `now.toLocaleTimeString(...)` (live clock with seconds) → `fmt.timeWithSeconds(now.toISOString())`
- Line 1051: `{selectedDayData.startTime} - {selectedDayData.endTime}` → `{fmt.shiftTime(...)}`

- [ ] **Step 2: Replace in AttendanceDashboardScreen.tsx**

Read the file. Find all 4 instances:
- Line 80: `toLocaleTimeString(...)` → `fmt.time(iso)` or `fmt.timeWithSeconds(iso)`
- Lines 361-362: `toLocaleTimeString(...)` → `fmt.time(...)`
- Line 144: raw shift time → `fmt.shiftTime(...)`

- [ ] **Step 3: Replace in ShiftCheckInScreen.tsx**

Read the file. Find all 6 instances:
- Lines 62, 68: `toLocaleTimeString(...)` → `fmt.time(...)` / `fmt.timeWithSeconds(...)`
- Line 347: live clock → `fmt.timeWithSeconds(now.toISOString())`
- Lines 444, 448, 458: raw shift times → `fmt.shiftTime(...)`

- [ ] **Step 4: Replace in ShiftManagementScreen.tsx**

Read the file. Find shift time displays:
- Line 457: `{shift.startTime} — {shift.endTime}` → `{fmt.shiftTime(shift.startTime)} — {fmt.shiftTime(shift.endTime)}`
- Line 567: break time display → `fmt.shiftTime(brk.startTime)`

- [ ] **Step 5: Replace in remaining web screens**

For each of these files, read and replace all instances:
- `ChatbotScreen.tsx` — 1 time instance
- `TicketChatScreen.tsx` — 1 time instance
- `CompanyDetailScreen.tsx` — 1 date + 1 time instance
- `VisitorBoard.tsx` — 1 toLocaleString instance
- Any other files found with `toLocaleDateString` or `toLocaleTimeString`

Use `grep -rn 'toLocaleTimeString\|toLocaleDateString\|toLocaleString' web-system-app/src/features/` to find any remaining instances and replace them all.

- [ ] **Step 6: Type-check**

```bash
cd /Users/chetan/Documents/Avyren-Technologies/Products/Mobile-ERP/web-system-app && npx tsc --noEmit
```

- [ ] **Step 7: Commit**

```bash
git add web-system-app/src/features/
git commit -m "refactor(web): replace all hardcoded date/time formatting with useCompanyFormatter"
```

---

## Task 7: Replace All Mobile Formatting Instances

**Files:** All mobile-app screen files listed in the file structure section above (~10 files).

Same approach as Task 6 but for mobile. For each file:
1. Add `import { useCompanyFormatter } from '@/hooks/use-company-formatter';`
2. Add `const fmt = useCompanyFormatter();` at the top of the component
3. Replace patterns as described in Task 6.

- [ ] **Step 1: Replace in dashboard-screen.tsx**

Read the file. Find all 5 instances:
- Line 107: `toLocaleTimeString(...)` → `fmt.time(...)`
- Lines 737, 741: live clock → `fmt.timeWithSeconds(new Date().toISOString())`
- Line 849: `{shift.startTime} -- {shift.endTime}` → `{fmt.shiftTime(...)}`
- Line 1220: `{selectedDayData.startTime}` → `{fmt.shiftTime(...)}`

- [ ] **Step 2: Replace in shift-check-in-screen.tsx**

Read the file. Find all 5 instances:
- Line 65: `toLocaleTimeString(...)` → `fmt.time(...)`
- Lines 239, 243: live clock → `fmt.timeWithSeconds(...)` and date → `fmt.date(...)`
- Line 240: `toLocaleDateString(...)` → `fmt.date(...)`
- Line 466: raw break time → `fmt.shiftTime(...)`

- [ ] **Step 3: Replace in attendance-dashboard-screen.tsx**

Read the file. Find all instances:
- Line 79: `toLocaleTimeString(...)` → `fmt.time(...)`
- Line 338: raw shift time → `fmt.shiftTime(...)`

- [ ] **Step 4: Replace in remaining mobile screens**

For each of these files, read and replace:
- `my-attendance-screen.tsx` — 1 time instance
- `shift-management-screen.tsx` — 2 shiftTime instances
- `chatbot-screen.tsx` — 1 time instance
- `ticket-chat-screen.tsx` — 1 time instance
- `audit-log-screen.tsx` — 1 date + 1 time instance
- `company-detail-screen.tsx` — 1 date + 1 time instance

Use `grep -rn 'toLocaleTimeString\|toLocaleDateString\|toLocaleString' mobile-app/src/features/` to find any remaining instances.

- [ ] **Step 5: Type-check**

```bash
cd /Users/chetan/Documents/Avyren-Technologies/Products/Mobile-ERP/mobile-app && npx tsc --noEmit 2>&1 | grep -v node_modules | head -10
```

- [ ] **Step 6: Commit**

```bash
git add mobile-app/src/features/
git commit -m "refactor(mobile): replace all hardcoded date/time formatting with useCompanyFormatter"
```

---

## Task 8: Final Verification & Grep Audit

**Files:** All three codebases

- [ ] **Step 1: Audit web for remaining hardcoded patterns**

```bash
cd /Users/chetan/Documents/Avyren-Technologies/Products/Mobile-ERP/web-system-app
grep -rn 'toLocaleTimeString\|toLocaleDateString\|toLocaleString' src/features/ src/components/ --include='*.tsx' --include='*.ts' | grep -v node_modules | grep -v '.test.'
```

Expected: No matches (all replaced). If any remain, fix them.

- [ ] **Step 2: Audit mobile for remaining hardcoded patterns**

```bash
cd /Users/chetan/Documents/Avyren-Technologies/Products/Mobile-ERP/mobile-app
grep -rn 'toLocaleTimeString\|toLocaleDateString\|toLocaleString' src/features/ src/components/ --include='*.tsx' --include='*.ts' | grep -v node_modules | grep -v '.test.'
```

Expected: No matches. Fix any remaining.

- [ ] **Step 3: Audit backend for remaining raw Date calls in business logic**

```bash
cd /Users/chetan/Documents/Avyren-Technologies/Products/Mobile-ERP/avy-erp-backend
grep -rn '\.getDay()\|\.getMonth()\|\.getFullYear()' src/modules/hr/ --include='*.ts' | grep -v node_modules | grep -v '.test.' | grep -v '__tests__'
```

Review each match. Some may be acceptable (e.g., in validators, test files). Business logic should use Luxon.

- [ ] **Step 4: Full type-check all three codebases**

```bash
cd /Users/chetan/Documents/Avyren-Technologies/Products/Mobile-ERP/avy-erp-backend && npx tsc --noEmit
cd /Users/chetan/Documents/Avyren-Technologies/Products/Mobile-ERP/web-system-app && npx tsc --noEmit
cd /Users/chetan/Documents/Avyren-Technologies/Products/Mobile-ERP/mobile-app && npx tsc --noEmit 2>&1 | grep -v node_modules
```

- [ ] **Step 5: Commit any remaining fixes**

```bash
git add -A
git commit -m "chore: final audit — remove all remaining hardcoded date/time formatting"
```

---

## Notes for Implementor

### What NOT to change (keep as-is):
- `new Date().toISOString()` for creating UTC timestamps (logging, audit, middleware) — these are correct
- `new Date().getFullYear()` for copyright years in email templates — not business logic
- `new Date()` in test files — test data is fine with server time
- Form input values for shift times (`value={breakForm.startTime}`) — these are data, not display
- Backend `health check` timestamp — system-level, not tenant-specific

### Live clock pattern:
For screens with live clocks (dashboard, shift check-in), the clock updates every second. Use:
```typescript
const [now, setNow] = useState(new Date().toISOString());
useEffect(() => {
  const id = setInterval(() => setNow(new Date().toISOString()), 1000);
  return () => clearInterval(id);
}, []);
// Display: fmt.timeWithSeconds(now)
```

### Super admin screens:
Super admin screens (CompanyDetailScreen, AuditLogScreen) don't have a company context of their own — they view other companies' data. For these, use `DEFAULT_FORMAT_SETTINGS` as fallback (the hook already handles this). If viewing a specific company's data, the displayed timestamps will use the viewing admin's default format, which is acceptable.
