# HRMS Configuration System — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Redesign the entire HRMS configuration system across backend, web, and mobile — replacing JSON blobs with typed models, adding enforcement middleware, building the attendance status resolver, and aligning all frontend screens to a single source of truth.

**Architecture:** 7-layer configuration stack (Company Settings → System Controls → Location → Shift → Attendance Rules → Overtime Rules → ESS Config) with deterministic policy resolution, resolved value snapshots on attendance records, and enforcement middleware at every critical path.

**Tech Stack:** Prisma (PostgreSQL), Express/Node.js, Zod validators, Redis caching, React (Vite) web, React Native (Expo) mobile, React Query, Zustand.

**Design Spec:** `docs/superpowers/specs/2026-03-30-hrms-configuration-system-design.md`

**Key Constraints:**
- **No migrations/fallbacks:** Project is pre-production. Direct schema replacement — no legacy code, no backwards compatibility layers, no deprecated field preservation.
- **Web-first, mobile mirrors:** Build each screen on web first, then mobile copies the exact same field structure. Never build web and mobile in parallel (consistency risk).
- **Idempotent seeder:** Config seeding uses upsert pattern — safe to re-run.
- **Transaction wrapping:** All multi-model writes wrapped in `$transaction`.
- **Failure strategy:** Redis failures fall through to DB reads. Missing configs auto-seed. Resolver failures return safe defaults + log error.
- **Observability:** Structured logging at policy resolution, status determination, and enforcement checkpoints.
- **Timezone-aware:** All attendance date/time calculations use `company.timezone` from CompanySettings. Never use server-local time.

---

## File Structure

### New Files (Backend)

| File | Purpose |
|------|---------|
| `avy-erp-backend/src/shared/constants/system-defaults.ts` | SYSTEM_DEFAULTS constant + industry templates |
| `avy-erp-backend/src/shared/services/policy-resolver.service.ts` | Configuration resolution chain engine |
| `avy-erp-backend/src/shared/services/attendance-status-resolver.service.ts` | Deterministic status calculation |
| `avy-erp-backend/src/shared/services/location-validator.service.ts` | Location constraint validation |
| `avy-erp-backend/src/shared/services/punch-validator.service.ts` | Punch sequence validation |
| `avy-erp-backend/src/shared/middleware/config-enforcement.middleware.ts` | Module + ESS enforcement middleware |
| `avy-erp-backend/src/shared/services/config-seeder.service.ts` | Company creation config seeding |
| `avy-erp-backend/src/shared/utils/timezone.ts` | Timezone-aware date/time helpers |
| `avy-erp-backend/src/shared/utils/config-cache.ts` | Config cache helpers with Redis fallback + auto-seed |

### Modified Files (Backend)

| File | Changes |
|------|---------|
| `prisma/schema.prisma` | New enums, models, enhanced fields |
| `src/core/company-admin/company-admin.service.ts` | Rewrite settings/controls/shifts to use typed models |
| `src/core/company-admin/company-admin.validators.ts` | New Zod schemas for typed models |
| `src/core/company-admin/company-admin.controller.ts` | Updated handlers for new models |
| `src/core/company-admin/company-admin.routes.ts` | Add shift break routes, enforcement middleware |
| `src/modules/hr/attendance/attendance.service.ts` | Integrate policy resolver + status resolver |
| `src/modules/hr/attendance/attendance.validators.ts` | Updated Zod schemas for enhanced AttendanceRule |
| `src/modules/hr/attendance/attendance.routes.ts` | Add enforcement middleware, OT request routes |
| `src/modules/hr/ess/ess.service.ts` | Remove security fields logic |
| `src/modules/hr/ess/ess.validators.ts` | Updated schema (security fields removed, MSS/mobile added) |
| `src/modules/hr/ess/ess.routes.ts` | Add ESS feature enforcement to every route |
| `src/modules/hr/payroll-run/payroll-run.service.ts` | Use granular OT multipliers, enforce caps |
| `src/core/tenant/tenant.service.ts` | Add config seeding on company creation |
| `src/core/auth/auth.types.ts` | Remove featureToggles field |

### Deleted Files (Backend)

| File | Reason |
|------|--------|
| `src/core/feature-toggle/feature-toggle.service.ts` | Feature Toggles removed |
| `src/core/feature-toggle/feature-toggle.controller.ts` | Feature Toggles removed |
| `src/core/feature-toggle/feature-toggle.routes.ts` | Feature Toggles removed |
| `src/shared/constants/feature-toggles.ts` | Feature Toggles removed |

### Modified Files (Web)

| File | Changes |
|------|---------|
| `src/features/company-admin/CompanySettingsScreen.tsx` | Rewrite to match spec (16 fields) |
| `src/features/company-admin/SystemControlsScreen.tsx` | Rewrite to match spec (25 fields) |
| `src/features/company-admin/hr/AttendanceRulesScreen.tsx` | Rewrite to match spec (26 fields) |
| `src/features/company-admin/ShiftManagementScreen.tsx` | Add policy overrides + break management |
| `src/features/company-admin/hr/OvertimeRulesScreen.tsx` | Rewrite to match spec (20 fields) |
| `src/features/company-admin/hr/EssConfigScreen.tsx` | Rewrite to match spec (36 fields) |
| `src/lib/api/company-admin.ts` | Updated types + methods for new models |
| `src/lib/api/attendance.ts` | Updated types for enhanced rules + OT |
| `src/lib/api/ess.ts` | Updated types (security removed, MSS added) |
| `src/features/company-admin/api/use-company-admin-queries.ts` | New query hooks for typed models |
| `src/features/company-admin/api/use-company-admin-mutations.ts` | New mutation hooks |
| `src/features/company-admin/api/use-attendance-queries.ts` | Updated OT request queries |
| `src/features/company-admin/api/use-attendance-mutations.ts` | Updated OT request mutations |
| `src/features/company-admin/api/use-ess-queries.ts` | Updated for new ESS config shape |
| `src/features/company-admin/api/use-ess-mutations.ts` | Updated for new ESS config shape |
| `src/store/useAuthStore.ts` | Remove featureToggles + useHasFeature |

### Deleted Files (Web)

| File | Reason |
|------|--------|
| `src/features/company-admin/FeatureToggleScreen.tsx` | Feature Toggles removed |

### Modified Files (Mobile)

| File | Changes |
|------|---------|
| `src/features/company-admin/company-settings-screen.tsx` | Rewrite to match spec (16 fields) |
| `src/features/company-admin/system-controls-screen.tsx` | Rewrite to match spec (25 fields) |
| `src/features/company-admin/hr/attendance-rules-screen.tsx` | Rewrite to match spec (26 fields) |
| `src/features/company-admin/shift-management-screen.tsx` | Add policy overrides + break management |
| `src/features/company-admin/hr/overtime-rules-screen.tsx` | Rewrite to match spec (20 fields) |
| `src/features/company-admin/hr/ess-config-screen.tsx` | Rewrite to match spec (36 fields) |
| `src/lib/api/company-admin.ts` | Updated types + methods |
| `src/lib/api/attendance.ts` | Updated types |
| `src/lib/api/ess.ts` | Updated types |
| `src/features/company-admin/api/use-company-admin-queries.ts` | Updated hooks |
| `src/features/company-admin/api/use-company-admin-mutations.ts` | Updated hooks |
| `src/features/company-admin/api/use-attendance-queries.ts` | OT request hooks |
| `src/features/company-admin/api/use-attendance-mutations.ts` | OT request hooks |
| `src/features/company-admin/api/use-ess-queries.ts` | Updated |
| `src/features/auth/use-auth-store.ts` | Remove featureToggles + useHasFeature |

### Deleted Files (Mobile)

| File | Reason |
|------|--------|
| `src/features/company-admin/feature-toggle-screen.tsx` | Feature Toggles removed |
| `src/app/(app)/company/feature-toggles.tsx` | Feature Toggles route removed |

---

## Phase 1: Schema & Data Foundation

### Task 1: Add Enums to Prisma Schema

**Files:**
- Modify: `avy-erp-backend/prisma/schema.prisma`

- [ ] **Step 1: Add all new enums**

Add after existing enums in `schema.prisma`. See design spec Section 3 for complete enum definitions. Add these enums:
- `CurrencyCode`, `LanguageCode`, `TimeFormat`
- `ShiftType`, `BreakType`
- `PunchMode`, `RoundingStrategy`, `PunchRounding`, `RoundingDirection`, `DeductionType`, `LocationAccuracy`
- `OTCalculationBasis`, `OvertimeRequestStatus`, `OTMultiplierSource`
- `DeviceType`

Update existing `AttendanceStatus` enum to add `INCOMPLETE` and `EARLY_EXIT`.

- [ ] **Step 2: Verify schema parses**

Run: `cd avy-erp-backend && pnpm db:generate`
Expected: Prisma Client generated successfully

- [ ] **Step 3: Commit**

```bash
git add prisma/schema.prisma
git commit -m "feat: add HRMS config enums to Prisma schema"
```

---

### Task 2: Add New Models (CompanySettings, SystemControls, ShiftBreak, OvertimeRequest)

**Files:**
- Modify: `avy-erp-backend/prisma/schema.prisma`

- [ ] **Step 1: Add CompanySettings model**

See design spec Section 4.1 for complete model. One-to-one with Company via unique companyId. Includes createdBy/updatedBy audit fields.

- [ ] **Step 2: Add SystemControls model**

See design spec Section 4.2. Includes module enablement flags, production/payroll/leave controls, security fields, audit retention.

- [ ] **Step 3: Add ShiftBreak model**

See design spec Section 4.4 (nested under CompanyShift). Includes name, startTime, duration, type (BreakType enum), isPaid.

- [ ] **Step 4: Add OvertimeRequest model**

See design spec Section 4.7. Links to AttendanceRecord (unique), Company, Employee. Includes approval workflow fields.

- [ ] **Step 5: Add relations to Company model**

Add to Company model:
```prisma
companySettings  CompanySettings?
systemControls   SystemControls?
overtimeRequests OvertimeRequest[]
```

- [ ] **Step 6: Verify schema**

Run: `cd avy-erp-backend && pnpm db:generate`
Expected: Success

- [ ] **Step 7: Commit**

```bash
git add prisma/schema.prisma
git commit -m "feat: add CompanySettings, SystemControls, ShiftBreak, OvertimeRequest models"
```

---

### Task 3: Enhance Existing Models

**Files:**
- Modify: `avy-erp-backend/prisma/schema.prisma`

- [ ] **Step 1: Enhance CompanyShift**

Rename `fromTime` → `startTime`, `toTime` → `endTime`. Remove `downtimeSlots` (replaced by ShiftBreak model). Add: `shiftType` (ShiftType enum, default DAY), `isCrossDay` (Boolean, default false), nullable policy override fields (`gracePeriodMinutes`, `earlyExitToleranceMinutes`, `halfDayThresholdHours`, `fullDayThresholdHours`, `maxLateCheckInMinutes`, `minWorkingHoursForOT`), capture overrides (`requireSelfie`, `requireGPS`, `allowedSources`), behavior fields (`autoClockOutMinutes`). Add `breaks ShiftBreak[]` relation.

- [ ] **Step 2: Enhance AttendanceRule**

Add 16 new fields per design spec Section 4.5: deduction rules (`lateDeductionType`, `lateDeductionValue`, `earlyExitDeductionType`, `earlyExitDeductionValue`), punch interpretation (`punchMode`), auto-processing (`autoMarkAbsentIfNoPunch`, `autoHalfDayEnabled`, `autoAbsentAfterDays`, `regularizationWindowDays`), rounding (`workingHoursRounding`, `punchTimeRounding`, `punchTimeRoundingDirection`), exception handling (`ignoreLateOnLeaveDay`, `ignoreLateOnHoliday`, `ignoreLateOnWeekOff`). Rename `earlyExitMinutes` → `earlyExitToleranceMinutes`, `lateArrivalsAllowed` → `lateArrivalsAllowedPerMonth`. Add `createdBy`/`updatedBy`.

- [ ] **Step 3: Enhance OvertimeRule**

Replace single `rateMultiplier` with granular multipliers (`weekdayMultiplier`, `weekendMultiplier`, `holidayMultiplier`, `nightShiftMultiplier`). Add: `calculationBasis`, `minimumOtMinutes`, `includeBreaksInOT`, `dailyCapHours`, `enforceCaps`, `maxContinuousOtHours`, `compOffEnabled`, `compOffExpiryDays`, `roundingStrategy`. Add `createdBy`/`updatedBy`. Add `overtimeRequests OvertimeRequest[]` relation.

- [ ] **Step 4: Enhance Location**

Add: `allowedDevices DeviceType[]`, `requireSelfie Boolean?`, `requireLiveLocation Boolean?`, `geoPolygon Json?`.

- [ ] **Step 5: Enhance ESSConfig**

Remove: `loginMethod`, `passwordMinLength`, `passwordComplexity`, `sessionTimeoutMinutes`, `mfaRequired`. Add: `downloadPayslips`, `viewSalaryStructure`, `leaveCancellation`, `viewShiftSchedule`, `shiftSwapRequest`, `wfhRequest`, `viewOrgChart`, `announcementBoard`, MSS fields (`mssViewTeam`, `mssApproveLeave`, `mssApproveAttendance`, `mssViewTeamAttendance`), mobile fields (`mobileOfflinePunch`, `mobileSyncRetryMinutes`, `mobileLocationAccuracy`). Add `createdBy`/`updatedBy`.

- [ ] **Step 6: Remove deprecated JSON fields from Company and CompanyShift**

Remove from Company model: `preferences Json?`, `systemControls Json?` (replaced by CompanySettings and SystemControls models). Remove from CompanyShift: `downtimeSlots Json?` (replaced by ShiftBreak). No backwards compatibility needed — project is pre-production.

- [ ] **Step 7: Enhance AttendanceRecord**

Add resolved snapshot fields: `appliedGracePeriodMinutes`, `appliedFullDayThresholdHours`, `appliedHalfDayThresholdHours`, `appliedBreakDeductionMinutes`, `appliedPunchMode`, `appliedLateDeduction`, `appliedEarlyExitDeduction`, `resolutionTrace Json?`, `evaluationContext Json?`, `finalStatusReason String?`. Add `overtimeRequest OvertimeRequest?` relation. Add `@@index([companyId, status])`.

- [ ] **Step 8: Verify full schema**

Run: `cd avy-erp-backend && pnpm db:generate`
Expected: Success

- [ ] **Step 9: Push schema to database**

Run: `cd avy-erp-backend && npx prisma db push`
Expected: Schema pushed successfully (direct replacement, no migration files needed in dev)

- [ ] **Step 10: Commit**

```bash
git add prisma/
git commit -m "feat: enhance Shift, AttendanceRule, OvertimeRule, Location, ESS, AttendanceRecord models"
```

---

### Task 4: Create System Defaults & Config Seeder

**Files:**
- Create: `avy-erp-backend/src/shared/constants/system-defaults.ts`
- Create: `avy-erp-backend/src/shared/services/config-seeder.service.ts`
- Modify: `avy-erp-backend/src/core/tenant/tenant.service.ts`

- [ ] **Step 1: Create system-defaults.ts**

Define `SYSTEM_DEFAULTS` constant per design spec Appendix A. Include all fallback values for every resolvable field.

- [ ] **Step 2: Create config-seeder.service.ts**

Implement `seedCompanyConfigs(companyId, industryType?)` per design spec Appendix C. Seeds all 5 config models: CompanySettings, SystemControls, AttendanceRule, OvertimeRule, ESSConfig. Include industry templates for MANUFACTURING, IT, RETAIL, HEALTHCARE.

**Must be idempotent:** Use `prisma.$transaction` wrapping all 5 upserts. Each uses `upsert` with `where: { companyId }` — safe to re-run without duplicating data.

```typescript
async function seedCompanyConfigs(companyId: string, industryType?: string) {
  const defaults = getIndustryDefaults(industryType);
  await platformPrisma.$transaction([
    platformPrisma.companySettings.upsert({ where: { companyId }, create: { companyId, ...defaults.settings }, update: {} }),
    platformPrisma.systemControls.upsert({ where: { companyId }, create: { companyId, ...defaults.controls }, update: {} }),
    platformPrisma.attendanceRule.upsert({ where: { companyId }, create: { companyId, ...defaults.attendanceRules }, update: {} }),
    platformPrisma.overtimeRule.upsert({ where: { companyId }, create: { companyId, ...defaults.overtimeRules }, update: {} }),
    platformPrisma.eSSConfig.upsert({ where: { companyId }, create: { companyId, ...defaults.essConfig }, update: {} }),
  ]);
  logger.info({ companyId, industryType }, 'Company configs seeded successfully');
}
```

- [ ] **Step 3: Integrate seeder into tenant onboarding**

In `tenant.service.ts`, find the company creation method and add `await seedCompanyConfigs(company.id, company.businessType)` after company record is created.

- [ ] **Step 4: Commit**

```bash
git add src/shared/constants/system-defaults.ts src/shared/services/config-seeder.service.ts src/core/tenant/tenant.service.ts
git commit -m "feat: add config seeder with industry templates for company creation"
```

---

### Task 5: Timezone Utility & Failure Strategy Helpers

**Files:**
- Create: `avy-erp-backend/src/shared/utils/timezone.ts`
- Create: `avy-erp-backend/src/shared/utils/config-cache.ts`

- [ ] **Step 1: Create timezone utility**

All attendance date/time calculations must use the company timezone, never server-local time. Create helpers:
```typescript
import { DateTime } from 'luxon';

export function nowInCompanyTimezone(timezone: string): DateTime {
  return DateTime.now().setZone(timezone);
}

export function parseInCompanyTimezone(dateStr: string, timeStr: string, timezone: string): DateTime {
  return DateTime.fromFormat(`${dateStr} ${timeStr}`, 'yyyy-MM-dd HH:mm', { zone: timezone });
}

export function getAttendanceDateForShift(punchTime: DateTime, shift: { isCrossDay: boolean }, timezone: string): string {
  // Cross-day rule: attendance date = shift start date
  // Non-cross-day: use dayBoundaryTime from AttendanceRule
  // Returns ISO date string (YYYY-MM-DD)
}
```

- [ ] **Step 2: Create config cache helpers with failure strategy**

Wraps Redis cache reads with DB fallback + auto-seed:
```typescript
export async function getCachedSystemControls(companyId: string): Promise<SystemControls> {
  try {
    const cached = await redis.get(`config:system-controls:${companyId}`);
    if (cached) return JSON.parse(cached);
  } catch (err) {
    logger.warn({ companyId, error: err.message }, 'Redis read failed for system-controls, falling through to DB');
  }

  let controls = await prisma.systemControls.findUnique({ where: { companyId } });
  if (!controls) {
    logger.info({ companyId }, 'SystemControls missing, auto-seeding defaults');
    controls = await prisma.systemControls.create({ data: { companyId } });
  }

  try {
    await redis.set(`config:system-controls:${companyId}`, JSON.stringify(controls), 'EX', 1800);
  } catch { /* cache write failure is non-fatal */ }

  return controls;
}
// Same pattern for: getCachedAttendanceRules, getCachedOvertimeRules, getCachedESSConfig, getCachedShift, getCachedLocation, getCachedShiftBreaks
```

- [ ] **Step 3: Commit**

```bash
git add src/shared/utils/timezone.ts src/shared/utils/config-cache.ts
git commit -m "feat: add timezone utility and config cache helpers with Redis fallback strategy"
```

---

## Phase 2: Backend Services (Enforcement Engine)

### Task 6: Policy Resolver Service

**Files:**
- Create: `avy-erp-backend/src/shared/services/policy-resolver.service.ts`

- [ ] **Step 1: Implement resolvePolicy()**

Per design spec Section 6.5. Accepts companyId + EvaluationContext. Returns `{ policy: ResolvedPolicy, trace: ResolutionTrace }`. Resolution order:
- Policy fields: shift → attendanceRules → SYSTEM_DEFAULTS
- Constraint fields: location → shift → attendanceRules → SYSTEM_DEFAULTS
- Calculate break deduction minutes from ShiftBreak records

Uses config-cache helpers (Task 5) for Redis-cached lookups with DB fallback.

**Failure strategy:** If resolver fails entirely (DB down), throw with descriptive error — do NOT silently return defaults (attendance record must not be created with incorrect data).

**Observability:** Log at INFO level after resolution:
```typescript
logger.info({ companyId, shiftId: context.shiftId, resolvedPolicy: policy, trace }, 'Policy resolved for attendance');
```

- [ ] **Step 2: Commit**

```bash
git add src/shared/services/policy-resolver.service.ts
git commit -m "feat: add policy resolver service with field-type-aware resolution chain"
```

---

### Task 7: Location Validator & Punch Validator

**Files:**
- Create: `avy-erp-backend/src/shared/services/location-validator.service.ts`
- Create: `avy-erp-backend/src/shared/services/punch-validator.service.ts`

- [ ] **Step 1: Implement validateLocationConstraints()**

Per design spec Section 6.4. Checks: geo-fence (haversine distance), device restrictions, selfie requirement, live location requirement. Returns `{ valid, reason? }`.

- [ ] **Step 2: Implement validatePunchSequence()**

Per design spec Appendix B.2. Handles FIRST_LAST, EVERY_PAIR, SHIFT_BASED modes. Returns resolved punchIn/punchOut or flags as INCOMPLETE.

- [ ] **Step 3: Commit**

```bash
git add src/shared/services/location-validator.service.ts src/shared/services/punch-validator.service.ts
git commit -m "feat: add location validator and punch sequence validator services"
```

---

### Task 8: Attendance Status Resolver

**Files:**
- Create: `avy-erp-backend/src/shared/services/attendance-status-resolver.service.ts`

- [ ] **Step 1: Implement resolveAttendanceStatus()**

Per design spec Section 7. Pure function taking punch data, shift info, resolved policy, evaluation context, and rules. Returns StatusResult with: status, finalStatusReason, isLate, lateMinutes, isEarlyExit, earlyMinutes, workedHours, overtimeHours, appliedLateDeduction, appliedEarlyExitDeduction.

Implements the complete 10-step logic flow from spec Section 7 including:
- No punch → HOLIDAY / WEEK_OFF / ABSENT
- Missing punch-out → INCOMPLETE (Appendix B.3)
- Cross-day handling (Appendix B.1) — use timezone utility from Task 5
- Exception handling (holiday/leave/weekoff late suppression)
- Day classification (full-day/half-day/LOP)
- Deduction calculation

**Observability:** Log at INFO level after status resolution:
```typescript
logger.info({ employeeId, date, status: result.status, reason: result.finalStatusReason }, 'Attendance status resolved');
```

- [ ] **Step 2: Commit**

```bash
git add src/shared/services/attendance-status-resolver.service.ts
git commit -m "feat: add deterministic attendance status resolver engine"
```

---

### Task 9: Enforcement Middleware

**Files:**
- Create: `avy-erp-backend/src/shared/middleware/config-enforcement.middleware.ts`

- [ ] **Step 1: Implement requireModuleEnabled()**

Per design spec Section 6.2. Checks `SystemControls.*Enabled` flag via Redis cache. Throws `ApiError.forbidden()` if disabled.

- [ ] **Step 2: Implement requireESSFeature()**

Per design spec Section 6.3. Checks `ESSConfig.*` flag. Throws `ApiError.forbidden()` if disabled.

- [ ] **Step 3: Implement validatePayrollNotLocked()**

Per design spec Appendix B.5. Checks `SystemControls.payrollLock` + payroll run status for the date.

- [ ] **Step 4: Commit**

```bash
git add src/shared/middleware/config-enforcement.middleware.ts
git commit -m "feat: add config enforcement middleware (module gates, ESS gates, payroll lock)"
```

---

## Phase 3: Backend API Updates

### Task 10: Company Settings API (replaces preferences JSON)

**Files:**
- Modify: `avy-erp-backend/src/core/company-admin/company-admin.validators.ts`
- Modify: `avy-erp-backend/src/core/company-admin/company-admin.service.ts`
- Modify: `avy-erp-backend/src/core/company-admin/company-admin.controller.ts`

- [ ] **Step 1: Add Zod schema for CompanySettings**

In validators, add `updateCompanySettingsSchema` with all 16 fields per spec Screen 1. Use proper enum validation for CurrencyCode, LanguageCode, TimeFormat.

- [ ] **Step 2: Update service methods**

Replace `getSettings()` / `updateSettings()` that read/write `Company.preferences` JSON with methods that read/write the new `CompanySettings` model. Set `updatedBy` from request user.

- [ ] **Step 3: Update controller**

Update `getSettings` and `updateSettings` controller methods to use new validator + service.

- [ ] **Step 4: Verify existing route paths still work**

`GET /company/settings` and `PATCH /company/settings` should work unchanged.

- [ ] **Step 5: Commit**

```bash
git add src/core/company-admin/
git commit -m "feat: replace Company.preferences JSON with typed CompanySettings model"
```

---

### Task 11: System Controls API (replaces systemControls JSON)

**Files:**
- Modify: `avy-erp-backend/src/core/company-admin/company-admin.validators.ts`
- Modify: `avy-erp-backend/src/core/company-admin/company-admin.service.ts`
- Modify: `avy-erp-backend/src/core/company-admin/company-admin.controller.ts`

- [ ] **Step 1: Add Zod schema for SystemControls**

In validators, add `updateSystemControlsSchema` with all 25 fields per spec Screen 2. Range validation: sessionTimeoutMinutes (5-1440), maxConcurrentSessions (1-10), passwordMinLength (6-32), accountLockThreshold (1-20), accountLockDurationMinutes (1-1440), auditLogRetentionDays (30-730).

- [ ] **Step 2: Update service methods**

Replace `getControls()` / `updateControls()` that read/write `Company.systemControls` JSON with methods that read/write the new `SystemControls` model. Invalidate Redis cache on update.

- [ ] **Step 3: Update controller**

- [ ] **Step 4: Commit**

```bash
git add src/core/company-admin/
git commit -m "feat: replace Company.systemControls JSON with typed SystemControls model"
```

---

### Task 12: Enhanced Shift API (breaks + overrides)

**Files:**
- Modify: `avy-erp-backend/src/core/company-admin/company-admin.validators.ts`
- Modify: `avy-erp-backend/src/core/company-admin/company-admin.service.ts`
- Modify: `avy-erp-backend/src/core/company-admin/company-admin.controller.ts`
- Modify: `avy-erp-backend/src/core/company-admin/company-admin.routes.ts`

- [ ] **Step 1: Add shift validators**

Update `createShiftSchema` and `updateShiftSchema` to include: shiftType, startTime, endTime, isCrossDay, all nullable override fields, allowedSources. Add `createShiftBreakSchema` and `updateShiftBreakSchema`.

- [ ] **Step 2: Update shift service methods**

Update `createShift`, `updateShift`, `deleteShift` to handle new fields. Add `listShiftBreaks(shiftId)`, `createShiftBreak(shiftId, data)`, `updateShiftBreak(breakId, data)`, `deleteShiftBreak(breakId)`. Return shift with breaks included on GET.

- [ ] **Step 3: Update controller + add break handlers**

Add controller methods for break CRUD.

- [ ] **Step 4: Add break routes**

Add to routes:
```
GET    /company/shifts/:id/breaks
POST   /company/shifts/:id/breaks
PATCH  /company/shifts/:id/breaks/:breakId
DELETE /company/shifts/:id/breaks/:breakId
```

- [ ] **Step 5: Commit**

```bash
git add src/core/company-admin/
git commit -m "feat: enhance shift API with policy overrides and break management"
```

---

### Task 13: Enhanced Attendance Rules API

**Files:**
- Modify: `avy-erp-backend/src/modules/hr/attendance/attendance.validators.ts`
- Modify: `avy-erp-backend/src/modules/hr/attendance/attendance.service.ts`

- [ ] **Step 1: Update attendance rules validator**

Replace `attendanceRulesSchema` with new schema including all 26 fields per spec Screen 3. Use enum validation for PunchMode, RoundingStrategy, PunchRounding, RoundingDirection, DeductionType.

- [ ] **Step 2: Update getRules/updateRules service methods**

Update to handle new fields. Ensure proper Decimal handling. Set `updatedBy` on update.

- [ ] **Step 3: Commit**

```bash
git add src/modules/hr/attendance/
git commit -m "feat: enhance attendance rules API with punch modes, rounding, deductions, auto-processing"
```

---

### Task 14: Enhanced Overtime Rules API + OT Requests

**Files:**
- Modify: `avy-erp-backend/src/modules/hr/attendance/attendance.validators.ts`
- Modify: `avy-erp-backend/src/modules/hr/attendance/attendance.service.ts`
- Modify: `avy-erp-backend/src/modules/hr/attendance/attendance.controller.ts`
- Modify: `avy-erp-backend/src/modules/hr/attendance/attendance.routes.ts`

- [ ] **Step 1: Update overtime rules validator**

Replace `overtimeRulesSchema` with new schema including all 20 fields per spec Screen 5.

- [ ] **Step 2: Update OT rules service methods**

Handle granular multipliers, new caps, comp-off fields.

- [ ] **Step 3: Add OT request service methods**

Add: `listOvertimeRequests(companyId, filters)`, `approveOvertimeRequest(id, userId, notes)`, `rejectOvertimeRequest(id, userId, notes)`. On approval, calculate `calculatedAmount` using employee salary + applied multiplier.

- [ ] **Step 4: Add OT request controller + routes**

```
GET   /hr/overtime-requests
PATCH /hr/overtime-requests/:id/approve
PATCH /hr/overtime-requests/:id/reject
```

- [ ] **Step 5: Commit**

```bash
git add src/modules/hr/attendance/
git commit -m "feat: enhance OT rules API with granular multipliers and OT approval workflow"
```

---

### Task 15: Enhanced ESS Config API

**Files:**
- Modify: `avy-erp-backend/src/modules/hr/ess/ess.validators.ts`
- Modify: `avy-erp-backend/src/modules/hr/ess/ess.service.ts`
- Modify: `avy-erp-backend/src/modules/hr/ess/ess.routes.ts`

- [ ] **Step 1: Update ESS config validator**

Replace schema to match spec Screen 6 (36 fields). Remove security fields. Add MSS + mobile behavior fields.

- [ ] **Step 2: Update ESS service**

Update `getESSConfig` and `updateESSConfig` for new fields.

- [ ] **Step 3: Add enforcement to ESS routes**

Apply `requireESSFeature()` middleware to every ESS endpoint:
```typescript
router.post('/ess/apply-leave', requireESSFeature('leaveApplication'), controller.applyLeave);
router.post('/ess/regularize', requireESSFeature('attendanceRegularization'), controller.regularize);
router.get('/ess/my-payslips', requireESSFeature('viewPayslips'), controller.getMyPayslips);
// ... all ESS endpoints
```

- [ ] **Step 4: Add module enforcement to route groups**

Apply `requireModuleEnabled()` to attendance, leave, payroll, ESS route groups.

- [ ] **Step 5: Commit**

```bash
git add src/modules/hr/ess/ src/modules/hr/attendance/attendance.routes.ts
git commit -m "feat: update ESS config API and add enforcement middleware to all module routes"
```

---

### Task 16: Integrate Enforcement into Attendance Processing

**Files:**
- Modify: `avy-erp-backend/src/modules/hr/attendance/attendance.service.ts`

- [ ] **Step 1: Integrate location validation**

In `createRecord` / check-in flow, add `validateLocationConstraints()` call before processing. Reject with descriptive error if constraints violated.

- [ ] **Step 2: Integrate policy resolution**

Build EvaluationContext from request data. Call `resolvePolicy()` to get effective policy + trace.

- [ ] **Step 3: Integrate status resolver**

Replace existing `calculateAttendanceMetrics()` with call to `resolveAttendanceStatus()`. Store all resolved values on AttendanceRecord: applied* fields, resolutionTrace, evaluationContext, finalStatusReason.

- [ ] **Step 4: Integrate OT processing**

After status resolution, if overtime detected and OvertimeRule exists:
- Check eligibility (employee type)
- Apply threshold + minimum minutes
- Select multiplier based on context (weekday/weekend/holiday/night)
- Apply caps if enforceCaps = true
- Create OvertimeRequest if approvalRequired = true
- Or auto-approve if autoIncludePayroll = true && approvalRequired = false

- [ ] **Step 5: Commit**

```bash
git add src/modules/hr/attendance/attendance.service.ts
git commit -m "feat: integrate enforcement engine into attendance processing pipeline"
```

---

### Task 17: Update Payroll OT Calculation

**Files:**
- Modify: `avy-erp-backend/src/modules/hr/payroll-run/payroll-run.service.ts`

- [ ] **Step 1: Update OT calculation in payroll**

Replace single-multiplier calculation with:
1. Sum only APPROVED OvertimeRequest hours (not raw AttendanceRecord.overtimeHours)
2. Group by multiplierSource (WEEKDAY, WEEKEND, HOLIDAY, NIGHT_SHIFT)
3. Apply per-group multiplier from OvertimeRule
4. Enforce weekly/monthly caps from OvertimeRule if enforceCaps = true
5. Sum all groups for total OT amount

- [ ] **Step 2: Commit**

```bash
git add src/modules/hr/payroll-run/payroll-run.service.ts
git commit -m "feat: update payroll OT calculation to use granular multipliers and approval workflow"
```

---

## Phase 4: Frontend Alignment (Web)

### Task 18: Web API Client Types & Methods

**Files:**
- Modify: `web-system-app/src/lib/api/company-admin.ts`
- Modify: `web-system-app/src/lib/api/attendance.ts`
- Modify: `web-system-app/src/lib/api/ess.ts`

- [ ] **Step 1: Update company-admin API types**

Add TypeScript interfaces matching backend models exactly: `CompanySettings`, `SystemControls`, `ShiftBreak`. Update `CompanyShift` type with new fields.

- [ ] **Step 2: Update attendance API types**

Add interfaces for enhanced `AttendanceRule`, `OvertimeRule`, `OvertimeRequest`.

- [ ] **Step 3: Update ESS API types**

Update `ESSConfig` interface (remove security fields, add MSS + mobile).

- [ ] **Step 4: Add new API methods**

Add shift break CRUD methods. Add OT request list/approve/reject methods.

- [ ] **Step 5: Commit**

```bash
git add src/lib/api/
git commit -m "feat(web): update API client types and methods for HRMS config redesign"
```

---

### Task 19: Web React Query Hooks

**Files:**
- Modify: `web-system-app/src/features/company-admin/api/use-company-admin-queries.ts`
- Modify: `web-system-app/src/features/company-admin/api/use-company-admin-mutations.ts`
- Modify: `web-system-app/src/features/company-admin/api/use-attendance-queries.ts`
- Modify: `web-system-app/src/features/company-admin/api/use-attendance-mutations.ts`
- Modify: `web-system-app/src/features/company-admin/api/use-ess-queries.ts`
- Modify: `web-system-app/src/features/company-admin/api/use-ess-mutations.ts`

- [ ] **Step 1: Update company admin hooks**

Update `useCompanySettings`, `useCompanyControls` to use new typed models. Add `useShiftBreaks(shiftId)` query. Add shift break mutation hooks.

- [ ] **Step 2: Update attendance hooks**

Update `useAttendanceRules`, `useOvertimeRules` for new field shapes. Add `useOvertimeRequests(filters)` query. Add `useApproveOvertimeRequest`, `useRejectOvertimeRequest` mutations.

- [ ] **Step 3: Update ESS hooks**

Update `useESSConfig` for new field shape.

- [ ] **Step 4: Commit**

```bash
git add src/features/company-admin/api/
git commit -m "feat(web): update React Query hooks for HRMS config redesign"
```

---

### Task 20: Rewrite Web Config Screens (6 screens)

**Files:**
- Modify: `web-system-app/src/features/company-admin/CompanySettingsScreen.tsx`
- Modify: `web-system-app/src/features/company-admin/SystemControlsScreen.tsx`
- Modify: `web-system-app/src/features/company-admin/hr/AttendanceRulesScreen.tsx`
- Modify: `web-system-app/src/features/company-admin/ShiftManagementScreen.tsx`
- Modify: `web-system-app/src/features/company-admin/hr/OvertimeRulesScreen.tsx`
- Modify: `web-system-app/src/features/company-admin/hr/EssConfigScreen.tsx`

- [ ] **Step 1: Rewrite CompanySettingsScreen**

Implement per spec Screen 1 (16 fields). Use exact backend field names. 3 sections: Locale, Compliance, Integrations. Sticky save bar pattern.

- [ ] **Step 2: Rewrite SystemControlsScreen**

Implement per spec Screen 2 (25 fields). 6 sections: Module Enablement, Production, Payroll, Leave, Security, Audit.

- [ ] **Step 3: Rewrite AttendanceRulesScreen**

Implement per spec Screen 3 (26 fields). 9 sections. Conditional visibility for deduction value fields. Remove ALL phantom fields (shiftStartTime, shiftEndTime, all web-only fields).

- [ ] **Step 4: Enhance ShiftManagementScreen**

Add to existing shift CRUD: shiftType selector, isCrossDay toggle, policy overrides section with "Use Default" checkboxes, inline break management (add/edit/delete ShiftBreaks).

- [ ] **Step 5: Rewrite OvertimeRulesScreen**

Implement per spec Screen 5 (20 fields). 7 sections. Nullable multiplier pattern ("Use Weekday Rate" checkbox).

- [ ] **Step 6: Rewrite EssConfigScreen**

Implement per spec Screen 6 (36 fields). 10 sections. Remove security section. Add MSS + Mobile Behavior sections.

- [ ] **Step 7: Verify all screens build**

Run: `cd web-system-app && pnpm build`
Expected: Build succeeds with no TS errors

- [ ] **Step 8: Commit**

```bash
git add src/features/company-admin/
git commit -m "feat(web): rewrite all 6 config screens to match HRMS config spec"
```

---

## Phase 5: Frontend Alignment (Mobile)

### Task 21: Mobile API Client Types & Methods

**Files:**
- Modify: `mobile-app/src/lib/api/company-admin.ts`
- Modify: `mobile-app/src/lib/api/attendance.ts`
- Modify: `mobile-app/src/lib/api/ess.ts`

- [ ] **Step 1: Update types and methods**

Mirror exact same TypeScript interfaces and API methods as web (Task 18). Same field names, same types.

- [ ] **Step 2: Commit**

```bash
git add src/lib/api/
git commit -m "feat(mobile): update API client types and methods for HRMS config redesign"
```

---

### Task 22: Mobile React Query Hooks

**Files:**
- Modify: `mobile-app/src/features/company-admin/api/use-company-admin-queries.ts`
- Modify: `mobile-app/src/features/company-admin/api/use-company-admin-mutations.ts`
- Modify: `mobile-app/src/features/company-admin/api/use-attendance-queries.ts`
- Modify: `mobile-app/src/features/company-admin/api/use-attendance-mutations.ts`
- Modify: `mobile-app/src/features/company-admin/api/use-ess-queries.ts`

- [ ] **Step 1: Update hooks**

Mirror web hooks (Task 19). Same query keys, same patterns.

- [ ] **Step 2: Commit**

```bash
git add src/features/company-admin/api/
git commit -m "feat(mobile): update React Query hooks for HRMS config redesign"
```

---

### Task 23: Rewrite Mobile Config Screens (6 screens)

**Files:**
- Modify: `mobile-app/src/features/company-admin/company-settings-screen.tsx`
- Modify: `mobile-app/src/features/company-admin/system-controls-screen.tsx`
- Modify: `mobile-app/src/features/company-admin/hr/attendance-rules-screen.tsx`
- Modify: `mobile-app/src/features/company-admin/shift-management-screen.tsx`
- Modify: `mobile-app/src/features/company-admin/hr/overtime-rules-screen.tsx`
- Modify: `mobile-app/src/features/company-admin/hr/ess-config-screen.tsx`

- [ ] **Step 1: Rewrite company-settings-screen**

Same 16 fields and 3 sections as web. Mobile-adapted: ChipSelector for locale fields, ScrollView layout, gradient header. Use exact backend field names (no mapping).

- [ ] **Step 2: Rewrite system-controls-screen**

Same 25 fields and 6 sections as web. Mobile-adapted: collapsible sections, ToggleRow for booleans, NumberInput for integers.

- [ ] **Step 3: Rewrite attendance-rules-screen**

Same 26 fields and 9 sections as web. Remove phantom fields. Conditional visibility for deduction values.

- [ ] **Step 4: Enhance shift-management-screen**

Add policy overrides + break management. Mobile pattern: bottom sheet for break create/edit.

- [ ] **Step 5: Rewrite overtime-rules-screen**

Same 20 fields and 7 sections as web. Nullable multiplier pattern.

- [ ] **Step 6: Rewrite ess-config-screen**

Same 36 fields and 10 sections as web. Single save button (replace per-section save). Remove security section. Add MSS + Mobile Behavior.

- [ ] **Step 7: Verify type-check**

Run: `cd mobile-app && pnpm type-check`
Expected: No errors

- [ ] **Step 8: Commit**

```bash
git add src/features/company-admin/
git commit -m "feat(mobile): rewrite all 6 config screens to match HRMS config spec"
```

---

## Phase 6: Feature Toggle Removal & Cleanup

### Task 24: Remove Feature Toggles (Backend)

**Files:**
- Delete: `avy-erp-backend/src/core/feature-toggle/feature-toggle.service.ts`
- Delete: `avy-erp-backend/src/core/feature-toggle/feature-toggle.controller.ts`
- Delete: `avy-erp-backend/src/core/feature-toggle/feature-toggle.routes.ts`
- Delete: `avy-erp-backend/src/shared/constants/feature-toggles.ts`
- Modify: `avy-erp-backend/prisma/schema.prisma`
- Modify: `avy-erp-backend/src/core/auth/auth.types.ts`

- [ ] **Step 1: Remove FeatureToggle model from schema**

Delete the `FeatureToggle` model. The `feature_toggles` table will be dropped by migration.

- [ ] **Step 2: Delete feature toggle source files**

```bash
rm -rf avy-erp-backend/src/core/feature-toggle/
rm avy-erp-backend/src/shared/constants/feature-toggles.ts
```

- [ ] **Step 3: Remove from route mounting**

In the main routes file (likely `src/routes.ts` or where feature-toggle routes are mounted), remove the feature toggle route import and mount.

- [ ] **Step 4: Remove featureToggles from auth types**

In `auth.types.ts`, remove `featureToggles?: string[]` from `AuthResponse` interface.

- [ ] **Step 5: Remove from navigation manifest**

If feature-toggles has an entry in `navigation-manifest.ts`, remove it.

- [ ] **Step 6: Run migration**

Run: `cd avy-erp-backend && pnpm db:migrate`
Migration name: `remove_feature_toggles`

- [ ] **Step 7: Commit**

```bash
git add -A
git commit -m "feat: remove Feature Toggles system entirely (replaced by SystemControls)"
```

---

### Task 25: Remove Feature Toggles (Frontend)

**Files:**
- Delete: `web-system-app/src/features/company-admin/FeatureToggleScreen.tsx`
- Modify: `web-system-app/src/store/useAuthStore.ts`
- Modify: `web-system-app/src/lib/api/company-admin.ts`
- Delete: `mobile-app/src/features/company-admin/feature-toggle-screen.tsx`
- Delete: `mobile-app/src/app/(app)/company/feature-toggles.tsx`
- Modify: `mobile-app/src/features/auth/use-auth-store.ts`
- Modify: `mobile-app/src/lib/api/company-admin.ts`

- [ ] **Step 1: Delete web FeatureToggleScreen**

```bash
rm web-system-app/src/features/company-admin/FeatureToggleScreen.tsx
```

- [ ] **Step 2: Clean web auth store**

Remove `featureToggles: string[]` from state. Remove `useHasFeature()` hook export. Remove feature toggle handling from `signIn()`.

- [ ] **Step 3: Clean web API client**

Remove feature toggle API methods (`getFeatureToggleCatalogue`, `getFeatureToggles`, `updateFeatureToggles`) and related types from `company-admin.ts`.

- [ ] **Step 4: Remove web feature toggle query hooks**

Remove `useFeatureToggleCatalogue`, `useFeatureToggles` from query hooks file. Remove `useUpdateFeatureToggles` from mutation hooks file.

- [ ] **Step 5: Delete mobile feature toggle files**

```bash
rm mobile-app/src/features/company-admin/feature-toggle-screen.tsx
rm mobile-app/src/app/(app)/company/feature-toggles.tsx
```

- [ ] **Step 6: Clean mobile auth store**

Same as web: remove `featureToggles`, `useHasFeature()`.

- [ ] **Step 7: Clean mobile API client**

Remove feature toggle API methods from `company-admin.ts`.

- [ ] **Step 8: Remove mobile feature toggle hooks**

Remove from query/mutation hooks files.

- [ ] **Step 9: Remove route references**

Remove feature-toggles from any web App.tsx route config. Remove from mobile sidebar/navigation if referenced.

- [ ] **Step 10: Build both apps**

Run: `cd web-system-app && pnpm build`
Run: `cd mobile-app && pnpm type-check`
Expected: Both succeed

- [ ] **Step 11: Commit**

```bash
git add -A
git commit -m "feat: remove Feature Toggles from web and mobile apps"
```

---

---

## Summary

| Phase | Tasks | Scope |
|-------|-------|-------|
| **Phase 1: Schema & Data** | Tasks 1-5 | Prisma models, enums, seeding, timezone/cache utilities |
| **Phase 2: Enforcement Engine** | Tasks 6-9 | Policy resolver, location validator, status resolver, middleware |
| **Phase 3: Backend APIs** | Tasks 10-17 | All config APIs updated, enforcement integrated, payroll updated |
| **Phase 4: Web Frontend** | Tasks 18-20 | API types, hooks, 6 screen rewrites |
| **Phase 5: Mobile Frontend** | Tasks 21-23 | API types, hooks, 6 screen rewrites (mirrors web exactly) |
| **Phase 6: Cleanup** | Tasks 24-25 | Feature Toggle removal (backend + frontend) |

**Total: 25 tasks across 6 phases.**

Each phase produces a working system. Phase 1+2+3 = fully functional backend. Phase 4 must complete before Phase 5 (web-first, mobile mirrors). Phase 6 is cleanup after both frontends aligned.

**Execution order for frontend:** Build web screen → verify → then mobile mirrors the same structure. Never build web and mobile screens in parallel.
