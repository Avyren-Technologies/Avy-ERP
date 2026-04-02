# Date/Time Format & Timezone Enforcement — Design Spec

**Date:** 2026-04-02
**Status:** Approved
**Scope:** Backend timezone safety + frontend formatting enforcement across all ~211 instances

---

## Problem

CompanySettings stores `dateFormat`, `timeFormat`, and `timezone` — but none are enforced:

- **Frontend:** ~166 web + ~45 mobile instances use hardcoded `toLocaleDateString('en-IN', ...)` and `toLocaleTimeString('en-IN', { hour12: true })`. No company settings are consulted.
- **Backend:** Attendance service uses raw `new Date().getDay()` / `getMonth()` for business logic, leaking server timezone into day-of-week and month calculations.
- **Shift times:** Always displayed as raw 24h strings (`"09:00"`) regardless of the company's time format preference.

## Rules (Non-Negotiable)

1. **All backend timestamps are UTC ISO strings.** Frontend always converts from UTC → company timezone for display.
2. **Never use raw JS `Date` for business logic** on the backend. Use Luxon `DateTime` with explicit company timezone.
3. **Never use `new Date()` for display** on frontends. Always use the `CompanyFormatter`.
4. **Formatter inputs are strictly typed:** Only ISO strings (`2026-04-02T10:00:00Z`) or `yyyy-MM-dd` for dates, `HH:mm` for shift times. Never JS `Date` objects.
5. **Shift times are local company time** — no timezone conversion, only format conversion (24h → 12h).
6. **Use Luxon everywhere** (web + mobile + backend). Do not rely on `Intl.DateTimeFormat` for timezone operations — platform inconsistencies exist on React Native.

---

## Architecture

### Layer 1: Backend Timezone Safety

**Files affected:** `attendance.service.ts`, any service using `new Date()` for day/month/year logic.

**Change:** Replace all raw `Date` methods with Luxon equivalents:

```typescript
// BEFORE (broken — uses server timezone)
const dow = dayOfWeek[new Date(data.date).getDay()];
const month = recordDate.getMonth() + 1;
const year = recordDate.getFullYear();

// AFTER (correct — uses company timezone)
const dt = DateTime.fromISO(data.date).setZone(companyTimezone);
const dow = dayOfWeek[dt.weekday % 7]; // Luxon: 1=Mon..7=Sun
const month = dt.month;
const year = dt.year;
```

**Rule:** `DateTime.now().setZone(companyTimezone)` for "current time" — never `DateTime.now()` or `new Date()`.

### Layer 2: Frontend Formatter Factory

**Shared utility (identical on web and mobile, adapted for imports):**

```typescript
// lib/format/company-formatter.ts

import { DateTime } from 'luxon';

interface CompanyFormatSettings {
  dateFormat: 'DD/MM/YYYY' | 'MM/DD/YYYY' | 'YYYY-MM-DD';
  timeFormat: 'TWELVE_HOUR' | 'TWENTY_FOUR_HOUR';
  timezone: string; // IANA e.g. "Asia/Kolkata"
}

interface CompanyFormatter {
  date(iso: string): string;
  time(iso: string): string;
  dateTime(iso: string): string;
  shiftTime(hhmm: string): string;
  relativeDate(iso: string): string;
  parseToZoned(iso: string): DateTime;
}
```

**Implementation details:**

| Method | Input | Behavior |
|--------|-------|----------|
| `date(iso)` | ISO string or yyyy-MM-dd | Parse → set company TZ → format per `dateFormat` |
| `time(iso)` | ISO datetime string | Parse → set company TZ → format per `timeFormat` (with AM/PM if 12h) |
| `dateTime(iso)` | ISO datetime string | `date(iso) + ' ' + time(iso)` |
| `shiftTime(hhmm)` | "HH:mm" string | Format only (no TZ conversion): "09:00" → "9:00 AM" or "09:00" |
| `relativeDate(iso)` | ISO string | Compare using company TZ: "Today", "Yesterday", or `date(iso)` |
| `parseToZoned(iso)` | ISO string | Returns `DateTime` in company timezone (NOT JS Date) |

**Format mapping:**

| `dateFormat` setting | Luxon format token |
|---------------------|--------------------|
| `DD/MM/YYYY` | `dd/MM/yyyy` |
| `MM/DD/YYYY` | `MM/dd/yyyy` |
| `YYYY-MM-DD` | `yyyy-MM-dd` |

| `timeFormat` setting | Luxon format token |
|---------------------|--------------------|
| `TWELVE_HOUR` | `h:mm a` (e.g., "9:00 AM") |
| `TWENTY_FOUR_HOUR` | `HH:mm` (e.g., "09:00") |

### Layer 3: React Hook

```typescript
// hooks/useCompanyFormatter.ts

export function useCompanyFormatter(): CompanyFormatter {
  const { data } = useCompanySettings(); // React Query, staleTime: Infinity, gcTime: Infinity
  const settings = data?.data ?? DEFAULT_SETTINGS;
  return useMemo(() => createCompanyFormatter(settings), [settings]);
}
```

**Default fallback:** If settings haven't loaded yet, use `{ dateFormat: 'DD/MM/YYYY', timeFormat: 'TWELVE_HOUR', timezone: 'Asia/Kolkata' }`.

### Layer 4: Replace All Instances

**Replacement categories:**

| Current pattern | Count (approx) | Replacement |
|----------------|-----------------|-------------|
| `new Date(x).toLocaleDateString('en-IN', ...)` | ~90 | `fmt.date(x)` |
| `new Date(x).toLocaleTimeString('en-IN', ...)` | ~60 | `fmt.time(x)` |
| `{shift.startTime}` / `{shift.endTime}` raw | ~30 | `fmt.shiftTime(shift.startTime)` |
| `new Date(x).toLocaleDateString()` (no options) | ~20 | `fmt.date(x)` |
| Combined date+time inline | ~11 | `fmt.dateTime(x)` |

**Mobile-specific:** Always use company timezone from settings. Never use device timezone. Luxon handles this correctly since it doesn't depend on device `Intl` for timezone resolution.

---

## Dependencies

- **Luxon** — already used in backend. Add to web (`npm i luxon @types/luxon`) and mobile (`npm i luxon @types/luxon`).
- **React Query** — already used in both frontends for settings fetching.

## Settings Caching

```typescript
useQuery({
  queryKey: ['company-settings'],
  queryFn: () => companyAdminApi.getSettings(),
  staleTime: Infinity,
  gcTime: Infinity,
});
```

Only refetches on explicit `queryClient.invalidateQueries(['company-settings'])` after settings update.

## Error Handling

- If `parseToZoned` receives an invalid/empty string, return `DateTime.invalid()` and display "—" in UI.
- If settings fail to load, use defaults (DD/MM/YYYY, 12h, Asia/Kolkata).
- Never throw from formatting functions — graceful fallback to raw input.

## Files Created

| File | Codebase | Purpose |
|------|----------|---------|
| `src/lib/format/company-formatter.ts` | web | Formatter factory + pure functions |
| `src/hooks/useCompanyFormatter.ts` | web | React hook |
| `src/lib/format/company-formatter.ts` | mobile | Formatter factory (same logic) |
| `src/hooks/use-company-formatter.ts` | mobile | React hook |

## Files Modified

| Category | Approx count | Change |
|----------|-------------|--------|
| Web screens with date display | ~66 files | Replace `toLocaleDateString` → `fmt.date()` |
| Web screens with time display | ~40 files | Replace `toLocaleTimeString` → `fmt.time()` |
| Web screens with shift times | ~15 files | Replace raw string → `fmt.shiftTime()` |
| Mobile screens with date display | ~25 files | Same replacements |
| Mobile screens with time display | ~15 files | Same replacements |
| Backend attendance service | 1 file | Raw Date → Luxon with company TZ |
| Backend ESS service | 1 file | Verify timezone usage |

## Out of Scope

- Number formatting (`numberFormat` setting) — separate concern, not part of this spec
- Currency formatting — separate concern
- Backend API response format changes — backend stays ISO/24h
- Formatting presets (dateShort, dateLong, timeWithSeconds) — future enhancement
