# Per-Module Notifications Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Close every remaining gap in the notification system so it is 100% implemented: per-module dispatch call sites, cron-driven informational events, SMS (Twilio) + WhatsApp (Meta Cloud) providers, per-category user preferences, tenant onboarding integration, analytics dashboard, migration file for staging/prod, unit + integration tests, and residual nits from the prior reviews.

**Architecture:** Additive. The unified `notificationService.dispatch()` entry point and the priority-partitioned BullMQ pipeline are locked; this plan wires business call-sites into them, extends consent to per-category granularity, implements the two stubbed channels, and surfaces delivery analytics. Every change is reversible via the existing `NOTIFICATIONS_ENABLED` kill switch or per-channel master toggles.

**Tech Stack:**
- **Backend:** Node.js, Express, Prisma, PostgreSQL, Redis, BullMQ, Socket.io, firebase-admin, expo-server-sdk, handlebars, Twilio (new), node-cron
- **Web:** React, Vite, TypeScript, Tailwind, Zustand, React Query, Firebase Web SDK
- **Mobile:** Expo SDK 54, React Native 0.81.5, Expo Router 6, expo-notifications, socket.io-client, React Query, MMKV

**Branches:** `feat/per-module-notifications` on all three submodules (already checked out).

**Spec reference:** `docs/superpowers/specs/2026-04-09-per-module-notifications-design.md`

---

## Phase Overview

| Phase | Tasks | Description | Depends on |
|---|---|---|---|
| 1. Foundation | 1-6 | Migration SQL file, isRead deprecation, mobile type fix, residual nits, env vars | — |
| **1A. Operational Safeguards** | **6A-6H** | **Rate limiter, bulk dispatch, consent cache, SMS/WhatsApp caps, provider retry, WhatsApp mask, event aggregation + retention, cron pagination helper** | 1 |
| 2. Core wiring Part A | 7-11 | Leave, Attendance, ESS submission dispatches, `onApprovalComplete` refactor (with per-case try/catch), rule cache invalidation | 1A |
| 3. Core wiring Part B | 12-16 | Payroll (using **dispatchBulk**), Employee lifecycle, Transfer, Promotion, Salary revision, Offboarding | 2 |
| 4. Core wiring Part C | 17-21 | Recruitment, Training, Assets, Support ticket bridge, Auth critical | 3 |
| 5. Cron events | 22-27 | 7 informational cron jobs (cursor pagination + Promise.allSettled + cron dedup) + aggregation cron + event cleanup cron + default template additions | 1A |
| 6. SMS provider | 28-30 | Twilio provider with retry + caps + dry-run + masking, channel, tests | 1A |
| 7. WhatsApp provider | 31-33 | Meta Cloud provider with retry + enforced template + caps + masking, tests | 1A |
| 8. Per-category preferences | 34-38 | Schema, consent gate, API, web screen (with "Mute all"), mobile screen | 1A |
| 9. Tenant onboarding Step 5 | 39-40 | Schema + form + backend wiring | 1 |
| 10. Analytics dashboard | 41-44 | Backend aggregation (reading from pre-aggregated table), REST endpoints, web screen, nav entry | 1A, 5 |
| 11. Tests | 45-51 | Unit, integration, load test, manual QA | 2-10 |
| 12. Mobile polish + final | 52-55 | Notification icon, nav manifest mobile-side paths, final type-check, commit | 11 |

---

## Phase 1: Foundation

### Task 1: Generate Prisma migration SQL for staging/prod

**Files:**
- Create: `avy-erp-backend/prisma/migrations/20260409_notifications_full/migration.sql`

- [ ] **Step 1: Start a shadow Postgres container**

```bash
docker run --rm -d --name prisma-shadow -e POSTGRES_PASSWORD=shadow -e POSTGRES_DB=shadow -p 5433:5432 postgres:16
# Wait for Postgres to be ready
sleep 3
```

- [ ] **Step 2: Generate the migration SQL by diffing existing migrations against current schema**

```bash
cd avy-erp-backend
export SHADOW_DATABASE_URL="postgresql://postgres:shadow@localhost:5433/shadow"
mkdir -p prisma/migrations/20260409_notifications_full
pnpm prisma migrate diff \
  --from-migrations prisma/migrations \
  --to-schema-datamodel prisma/schema.prisma \
  --shadow-database-url "$SHADOW_DATABASE_URL" \
  --script > prisma/migrations/20260409_notifications_full/migration.sql
```

Expected output: a multi-hundred-line SQL file with `CREATE TABLE notification_events`, `CREATE TABLE user_notification_preferences`, `ALTER TABLE notifications ADD COLUMN ...`, etc.

- [ ] **Step 3: Verify the migration contains the expected changes**

```bash
grep -E "CREATE TABLE|ALTER TABLE|CREATE INDEX" prisma/migrations/20260409_notifications_full/migration.sql | head -30
```

Expected: at minimum `notifications`, `notification_events`, `user_notification_preferences`, `user_devices` alterations.

- [ ] **Step 4: Clean up shadow DB**

```bash
docker rm -f prisma-shadow
```

- [ ] **Step 5: Smoke-test applying the migration to a fresh DB**

```bash
docker run --rm -d --name prisma-test -e POSTGRES_PASSWORD=test -e POSTGRES_DB=test -p 5434:5432 postgres:16
sleep 3
DATABASE_URL="postgresql://postgres:test@localhost:5434/test" pnpm prisma migrate deploy
docker rm -f prisma-test
```

Expected: "1 migration(s) applied successfully".

- [ ] **Step 6: Commit**

```bash
git add prisma/migrations/20260409_notifications_full
git commit -m "feat(notifications): commit consolidated migration SQL for staging/prod deployment"
```

---

### Task 2: Fix pre-existing mobile type error

**Files:**
- Modify: `mobile-app/src/features/company-admin/hr/leave-request-screen.tsx`

- [ ] **Step 1: Read the file at the error line**

```bash
cd mobile-app
sed -n '14,18p' src/features/company-admin/hr/leave-request-screen.tsx
```

- [ ] **Step 2: Find the typo**

The error is `Module '"react-native"' has no exported member 'r'.` — almost certainly a typo like `import { r, View, Text } from 'react-native';` that got a stray `r`. Remove the `r`.

- [ ] **Step 3: Apply the fix**

Using Edit tool, remove the stray `r` from the import.

- [ ] **Step 4: Verify**

```bash
pnpm type-check 2>&1 | tail -5
```

Expected: zero errors (or only errors unrelated to this file).

- [ ] **Step 5: Commit**

```bash
git add src/features/company-admin/hr/leave-request-screen.tsx
git commit -m "fix(mobile): remove stray 'r' import in leave-request-screen"
```

---

### Task 3: Add new env vars for providers + cron flags

**Files:**
- Modify: `avy-erp-backend/src/config/env.ts`
- Modify: `avy-erp-backend/.env.example`

- [ ] **Step 1: Add env var validators to the Zod schema**

Append to the `envSchema` in `env.ts` after the existing notification variables:

```typescript
// Twilio (SMS provider)
TWILIO_ACCOUNT_SID: z.string().optional(),
TWILIO_AUTH_TOKEN: z.string().optional(),
TWILIO_FROM_NUMBER: z.string().optional(),
TWILIO_MESSAGING_SERVICE_SID: z.string().optional(),

// Meta Cloud API (WhatsApp provider)
META_WHATSAPP_PHONE_NUMBER_ID: z.string().optional(),
META_WHATSAPP_ACCESS_TOKEN: z.string().optional(),
META_WHATSAPP_API_VERSION: z.string().default('v21.0'),

// Notification feature flags
NOTIFICATIONS_CRON_ENABLED: envBoolean.default(true),
NOTIFICATIONS_SMS_ENABLED: envBoolean.default(true),
NOTIFICATIONS_WHATSAPP_ENABLED: envBoolean.default(true),
```

- [ ] **Step 2: Append to `.env.example`**

```env
# Twilio (SMS)
TWILIO_ACCOUNT_SID=
TWILIO_AUTH_TOKEN=
TWILIO_FROM_NUMBER=
TWILIO_MESSAGING_SERVICE_SID=

# Meta Cloud API (WhatsApp)
META_WHATSAPP_PHONE_NUMBER_ID=
META_WHATSAPP_ACCESS_TOKEN=
META_WHATSAPP_API_VERSION=v21.0

# Notification feature flags
NOTIFICATIONS_CRON_ENABLED=true
NOTIFICATIONS_SMS_ENABLED=true
NOTIFICATIONS_WHATSAPP_ENABLED=true
```

- [ ] **Step 3: Install Twilio package**

```bash
pnpm add twilio
```

- [ ] **Step 4: Type-check**

```bash
pnpm tsc --noEmit
```

Expected: clean.

- [ ] **Step 5: Commit**

```bash
git add src/config/env.ts .env.example package.json pnpm-lock.yaml
git commit -m "feat(notifications): add Twilio/Meta Cloud env vars + cron/SMS/WhatsApp kill switches"
```

---

### Task 4: Schema — add `UserNotificationCategoryPreference` + `NotificationTemplate.whatsappTemplateName`

**Files:**
- Modify: `avy-erp-backend/prisma/modules/platform/notifications.prisma`
- Modify: `avy-erp-backend/prisma/modules/platform/auth.prisma`
- Modify: `avy-erp-backend/prisma/modules/hrms/ess-workflows.prisma`

- [ ] **Step 1: Add model to `notifications.prisma`**

Append below the existing `UserNotificationPreference` model:

```prisma
model UserNotificationCategoryPreference {
  id        String              @id @default(cuid())
  userId    String
  category  String
  channel   NotificationChannel
  enabled   Boolean             @default(true)

  user      User                @relation("UserNotificationCategoryPrefUser", fields: [userId], references: [id], onDelete: Cascade)

  createdAt DateTime            @default(now())
  updatedAt DateTime            @updatedAt

  @@unique([userId, category, channel])
  @@index([userId])
  @@map("user_notification_category_preferences")
}
```

- [ ] **Step 2: Add back-reference on `User` in `auth.prisma`**

Find the User model's notification relation block and add:

```prisma
  // Notifications & devices
  notifications          Notification[]                       @relation("NotificationUser")
  devices                UserDevice[]                         @relation("UserDeviceUser")
  notificationPreference UserNotificationPreference?          @relation("UserNotificationPrefUser")
  categoryPreferences    UserNotificationCategoryPreference[] @relation("UserNotificationCategoryPrefUser")
```

- [ ] **Step 3: Add `whatsappTemplateName` field to `NotificationTemplate`**

In `ess-workflows.prisma`, extend `NotificationTemplate`:

```prisma
  whatsappTemplateName String?  // Meta Business Manager pre-approved template name
```

Place it between `compiledSubject` and `isSystem`.

- [ ] **Step 4: Merge + push schema**

```bash
pnpm prisma:merge
pnpm db:generate
pnpm prisma db push --skip-generate
```

- [ ] **Step 5: Type-check**

```bash
pnpm tsc --noEmit
```

Expected: clean.

- [ ] **Step 6: Commit**

```bash
git add prisma/
git commit -m "feat(notifications): schema — UserNotificationCategoryPreference + whatsappTemplateName"
```

---

### Task 5: Add `NotificationCategory` constants module

**Files:**
- Create: `avy-erp-backend/src/shared/constants/notification-categories.ts`

- [ ] **Step 1: Create the file with the 17 category definitions**

```typescript
export interface NotificationCategoryDef {
  code: string;
  label: string;
  description: string;
  locked?: boolean;
}

export const NOTIFICATION_CATEGORIES: NotificationCategoryDef[] = [
  { code: 'LEAVE', label: 'Leave', description: 'Leave requests, approvals, balance reminders' },
  { code: 'ATTENDANCE', label: 'Attendance', description: 'Regularization, missed punches' },
  { code: 'OVERTIME', label: 'Overtime', description: 'Overtime claims and approvals' },
  { code: 'REIMBURSEMENT', label: 'Reimbursement', description: 'Expense claims and approvals' },
  { code: 'LOAN', label: 'Loan', description: 'Loan applications and approvals' },
  { code: 'PAYROLL', label: 'Payroll', description: 'Payslips, salary credits, bonus payments' },
  { code: 'SHIFT', label: 'Shift', description: 'Shift change, swap requests' },
  { code: 'WFH', label: 'Work From Home', description: 'WFH requests' },
  { code: 'RESIGNATION', label: 'Resignation & Offboarding', description: 'Exit requests, F&F' },
  { code: 'EMPLOYEE_LIFECYCLE', label: 'Employee Lifecycle', description: 'Onboarding, transfers, promotions, salary revisions' },
  { code: 'RECRUITMENT', label: 'Recruitment', description: 'Interview scheduling, candidate updates, offers' },
  { code: 'TRAINING', label: 'Training', description: 'Training nominations, certificates, session reminders' },
  { code: 'ASSETS', label: 'Assets', description: 'Asset assignments and return reminders' },
  { code: 'SUPPORT', label: 'Support', description: 'Support ticket updates' },
  { code: 'AUTH', label: 'Security', description: 'Password reset, new device login, account lock', locked: true },
  { code: 'ANNOUNCEMENTS', label: 'Announcements', description: 'Company announcements and policy updates' },
  { code: 'BIRTHDAY_ANNIVERSARY', label: 'Celebrations', description: 'Birthday wishes and work anniversaries' },
];

export function getCategoryDef(code: string): NotificationCategoryDef | undefined {
  return NOTIFICATION_CATEGORIES.find((c) => c.code === code);
}

export function isCategoryLocked(code: string): boolean {
  return getCategoryDef(code)?.locked === true;
}
```

- [ ] **Step 2: Commit**

```bash
git add src/shared/constants/notification-categories.ts
git commit -m "feat(notifications): notification category catalogue (17 categories, locked AUTH)"
```

---

### Task 6: Reviewer residual nits from the prior review

**Files:**
- Modify: `avy-erp-backend/src/core/notifications/dispatch/dispatcher.ts`
- Modify: `avy-erp-backend/src/core/notifications/notification.service.ts`
- Modify: `avy-erp-backend/src/core/notifications/events/event-emitter.ts`
- Modify: `avy-erp-backend/src/core/notifications/dispatch/enqueue.ts`
- Modify: `avy-erp-backend/src/core/notifications/dispatch/rule-loader.ts`

This task addresses the "important" and "nit" findings from the prior reviewer that weren't in the critical bucket:

- [ ] **Step 1: Drop `DispatchResult.error` field** (I-NEW-4 — SQL leak vector)

In `dispatcher.ts`, remove the `error` field from the return type and the `catch` block:

```typescript
// dispatch/types.ts — remove the `error` field:
export interface DispatchResult {
  traceId: string;
  enqueued: number;
  notificationIds: string[];
}

// dispatcher.ts catch block — log but don't return error string:
} catch (err) {
  logger.error('Dispatcher internal error', {
    error: err,
    traceId,
    trigger: input.triggerEvent,
  });
  return { traceId, enqueued: 0, notificationIds: [] };
}
```

- [ ] **Step 2: Type the legacy `send()` channel mapping** (I-NEW-6)

In `notification.service.ts`, replace the `as any` cast:

```typescript
// Before
channels: params.channels.map((c) => c.toUpperCase()) as any,

// After
const CHANNEL_MAP = {
  in_app: 'IN_APP',
  push: 'PUSH',
  email: 'EMAIL',
} as const satisfies Record<string, NotificationChannel>;
// ...
channels: params.channels.map((c) => CHANNEL_MAP[c]),
```

Add `import type { NotificationChannel } from '@prisma/client';` at the top.

- [ ] **Step 3: Drop redundant `metadata` cast** (N3)

In `event-emitter.ts`, remove the `as any` on metadata:

```typescript
// Before
metadata: (input.metadata ?? undefined) as any,

// After
metadata: input.metadata === undefined ? undefined : (input.metadata as Prisma.InputJsonValue),
```

Add `import type { Prisma } from '@prisma/client';`.

- [ ] **Step 4: Pipeline `zcard`+`zadd` in batching** (Nit-7)

In `enqueue.ts`, use a Redis MULTI pipeline to make the count-and-add atomic:

```typescript
const pipeline = cacheRedis.multi();
pipeline.zremrangebyscore(batchKey, 0, now - windowMs);
pipeline.zcard(batchKey);
pipeline.zadd(batchKey, now, payload.notificationId);
pipeline.expire(batchKey, env.NOTIFICATIONS_BATCH_WINDOW_SEC);
const results = await pipeline.exec();
const pending = (results?.[1]?.[1] as number) ?? 0;
```

- [ ] **Step 5: Sentinel-string isAdHoc cleanup** (Nit-9)

In `dispatcher.ts`, add an `isAdHoc` flag to `LoadedRule` and use it instead of `rule.id?.startsWith('adhoc:')`:

```typescript
// rule-loader.ts — add to LoadedRule type
export type LoadedRule = NotificationRule & {
  template: NotificationTemplate;
  isAdHoc?: boolean;
};

// dispatcher.ts buildAdHocRules — set isAdHoc: true
return {
  // ... existing fields ...
  isAdHoc: true,
  template,
};

// dispatcher.ts — in the row creation bucket building
ruleId: rule.isAdHoc ? null : rule.id,
templateId: rule.isAdHoc ? null : rule.template.id,
```

- [ ] **Step 6: Type-check**

```bash
pnpm tsc --noEmit
```

Expected: clean.

- [ ] **Step 7: Commit**

```bash
git add src/core/notifications
git commit -m "fix(notifications): reviewer residual nits — drop DispatchResult.error (SQL leak), typed channel map, metadata cast, atomic batching pipeline, isAdHoc flag"
```

---

## Phase 1A: Operational Safeguards

These tasks implement the production-grade scaling and cost controls from spec §4A. Every task in this phase is **mandatory** before the per-module wiring in Phase 2+ begins, because those phases depend on these helpers (`dispatchBulk`, `checkUserRateLimit`, cached consent, etc.).

### Task 6A: Env var additions for safeguards

**Files:**
- Modify: `avy-erp-backend/src/config/env.ts`
- Modify: `avy-erp-backend/.env.example`

- [ ] **Step 1: Append new env vars to the Zod schema**

```typescript
// Operational safeguards
NOTIFICATIONS_USER_RATE_LIMIT_PER_MIN: z.coerce.number().default(20),
NOTIFICATIONS_TENANT_RATE_LIMIT_PER_MIN: z.coerce.number().default(1000),
NOTIFICATIONS_BULK_CHUNK_SIZE: z.coerce.number().default(50),
NOTIFICATIONS_BULK_MIN_RECIPIENTS: z.coerce.number().default(20),
NOTIFICATIONS_BULK_QUEUE_HIGH_WATER: z.coerce.number().default(5000),
NOTIFICATIONS_CONSENT_CACHE_TTL_SEC: z.coerce.number().default(300),
NOTIFICATIONS_SMS_DAILY_CAP_PER_TENANT: z.coerce.number().default(500),
NOTIFICATIONS_SMS_DAILY_CAP_PER_USER: z.coerce.number().default(10),
NOTIFICATIONS_SMS_DRY_RUN: envBoolean.default(false),
NOTIFICATIONS_WHATSAPP_DAILY_CAP_PER_TENANT: z.coerce.number().default(500),
NOTIFICATIONS_WHATSAPP_DAILY_CAP_PER_USER: z.coerce.number().default(10),
NOTIFICATIONS_WHATSAPP_DRY_RUN: envBoolean.default(false),
NOTIFICATIONS_EVENT_RETENTION_DAYS: z.coerce.number().default(90),
NOTIFICATIONS_CRON_COMPANY_CONCURRENCY: z.coerce.number().default(5),
NOTIFICATIONS_CRON_JITTER_MS: z.coerce.number().default(60000),
NOTIFICATIONS_METRICS_ENABLED: envBoolean.default(true),
```

- [ ] **Step 2: Document in `.env.example`**

```env
# Notification safeguards
NOTIFICATIONS_USER_RATE_LIMIT_PER_MIN=20
NOTIFICATIONS_BULK_CHUNK_SIZE=50
NOTIFICATIONS_BULK_MIN_RECIPIENTS=20
NOTIFICATIONS_CONSENT_CACHE_TTL_SEC=300
NOTIFICATIONS_SMS_DAILY_CAP_PER_TENANT=500
NOTIFICATIONS_SMS_DAILY_CAP_PER_USER=10
NOTIFICATIONS_SMS_DRY_RUN=false
NOTIFICATIONS_WHATSAPP_DAILY_CAP_PER_TENANT=500
NOTIFICATIONS_WHATSAPP_DAILY_CAP_PER_USER=10
NOTIFICATIONS_WHATSAPP_DRY_RUN=false
NOTIFICATIONS_EVENT_RETENTION_DAYS=90
NOTIFICATIONS_CRON_COMPANY_CONCURRENCY=5
```

- [ ] **Step 3: Install `p-limit` for cron concurrency**

```bash
pnpm add p-limit
```

- [ ] **Step 4: Type-check + commit**

```bash
pnpm tsc --noEmit
git add src/config/env.ts .env.example package.json pnpm-lock.yaml
git commit -m "feat(notifications): operational safeguard env vars + p-limit dep"
```

---

### Task 6B: Rate limiters (per-user + per-tenant)

**Files:**
- Create: `avy-erp-backend/src/core/notifications/dispatch/rate-limiter.ts`
- Modify: `avy-erp-backend/src/core/notifications/dispatch/dispatcher.ts`

- [ ] **Step 1: Create the rate limiter helper with two layers**

```typescript
// src/core/notifications/dispatch/rate-limiter.ts
import { cacheRedis } from '../../../config/redis';
import { env } from '../../../config/env';
import { logger } from '../../../config/logger';
import type { NotificationPriority } from '@prisma/client';

/**
 * Per-user rate limit gate. 20/min default. CRITICAL bypasses.
 */
export async function checkUserRateLimit(
  userId: string,
  priority: NotificationPriority,
): Promise<boolean> {
  if (priority === 'CRITICAL') return true;

  const key = `notif:rate:user:${userId}`;
  const max = env.NOTIFICATIONS_USER_RATE_LIMIT_PER_MIN;

  try {
    const count = await cacheRedis.incr(key);
    if (count === 1) await cacheRedis.expire(key, 60);
    if (count > max) {
      logger.warn('User rate limit exceeded, dropping notification', { userId, count, max, priority });
      return false;
    }
    return true;
  } catch (err) {
    logger.warn('User rate limit check failed (fail-open)', { error: err, userId });
    return true;
  }
}

/**
 * Per-tenant burst protection. 1000/min default. CRITICAL bypasses.
 * Protects the overall system from a single tenant's bug/runaway cron.
 */
export async function checkTenantRateLimit(
  companyId: string,
  priority: NotificationPriority,
): Promise<boolean> {
  if (priority === 'CRITICAL') return true;

  const key = `notif:rate:tenant:${companyId}`;
  const max = env.NOTIFICATIONS_TENANT_RATE_LIMIT_PER_MIN;

  try {
    const count = await cacheRedis.incr(key);
    if (count === 1) await cacheRedis.expire(key, 60);
    if (count > max) {
      logger.warn('Tenant rate limit exceeded, dropping notification', { companyId, count, max, priority });
      return false;
    }
    return true;
  } catch (err) {
    logger.warn('Tenant rate limit check failed (fail-open)', { error: err, companyId });
    return true;
  }
}
```

- [ ] **Step 2: Wire both limiters into the dispatcher**

In `dispatcher.ts`, `checkTenantRateLimit` once at the top (before rule loading), and `checkUserRateLimit` per recipient inside the bucket loop:

```typescript
import { checkUserRateLimit, checkTenantRateLimit } from './rate-limiter';

// Near the top of dispatch(), after traceId + enabled check:
const tenantAllowed = await checkTenantRateLimit(
  input.companyId,
  input.priority ?? 'MEDIUM',
);
if (!tenantAllowed) {
  await recordEvent({
    notificationId: null,
    channel: 'IN_APP',
    event: 'SKIPPED',
    errorCode: 'TENANT_RATE_LIMITED',
    traceId,
    source: 'SYSTEM',
  });
  return { traceId, enqueued: 0, notificationIds: [] };
}

// Inside the bucket loop:
const userAllowed = await checkUserRateLimit(bucket.userId, bucket.priority);
if (!userAllowed) {
  await recordEvent({
    notificationId: null,
    channel: 'IN_APP',
    event: 'SKIPPED',
    errorCode: 'RATE_LIMITED',
    traceId,
    source: 'SYSTEM',
  });
  continue;
}
```

- [ ] **Step 3: Type-check + commit**

```bash
git add src/core/notifications/dispatch
git commit -m "feat(notifications): per-user + per-tenant rate limiters (20/min user, 1000/min tenant, CRITICAL bypasses)"
```

---

### Task 6C: Consent cache Redis layer (versioned keys, O(1) invalidation)

**Files:**
- Modify: `avy-erp-backend/src/core/notifications/dispatch/consent-gate.ts`
- Modify: `avy-erp-backend/src/core/notifications/preferences/preferences.service.ts`

Uses the **versioned key** strategy from spec §4A.3 — invalidation is O(1) (single INCR) regardless of company size. Stale entries age out naturally via TTL.

- [ ] **Step 1: Refactor `loadConsentCache` with versioned keys**

```typescript
// consent-gate.ts additions

async function getVersion(scope: 'user' | 'company', id: string): Promise<number> {
  try {
    const v = await cacheRedis.get(`notif:consent:v:${scope}:${id}`);
    return v ? parseInt(v, 10) : 1;
  } catch {
    return 1;
  }
}

async function loadConsentCacheFromDB(userId: string): Promise<ConsentCache> {
  // ... existing DB fetch logic (renamed from loadConsentCache body) ...
}

export async function loadConsentCache(userId: string): Promise<ConsentCache> {
  // Resolve company for version keying
  const user = await platformPrisma.user.findUnique({
    where: { id: userId },
    select: { companyId: true },
  });
  if (!user?.companyId) return loadConsentCacheFromDB(userId);

  const [uv, cv] = await Promise.all([
    getVersion('user', userId),
    getVersion('company', user.companyId),
  ]);
  const cacheKey = `notif:consent:${userId}:${uv}:${cv}`;

  try {
    const cached = await cacheRedis.get(cacheKey);
    if (cached) {
      const parsed = JSON.parse(cached) as Omit<ConsentCache, 'categoryPrefs'> & {
        categoryPrefs: Array<[string, boolean]>;
      };
      return { ...parsed, categoryPrefs: new Map(parsed.categoryPrefs) };
    }
  } catch (err) {
    logger.warn('Consent cache read failed', { error: err, userId });
  }

  const fresh = await loadConsentCacheFromDB(userId);

  try {
    await cacheRedis.set(
      cacheKey,
      JSON.stringify({
        ...fresh,
        categoryPrefs: Array.from(fresh.categoryPrefs.entries()),
      }),
      'EX',
      env.NOTIFICATIONS_CONSENT_CACHE_TTL_SEC,
    );
  } catch (err) {
    logger.warn('Consent cache write failed (non-fatal)', { error: err, userId });
  }

  return fresh;
}

/** O(1) invalidation — bumps the user's version counter. Stale cache entries expire via TTL. */
export async function invalidateUserConsent(userId: string): Promise<void> {
  try {
    await cacheRedis.incr(`notif:consent:v:user:${userId}`);
  } catch (err) {
    logger.warn('User consent version bump failed', { error: err, userId });
  }
}

/** O(1) invalidation — bumps the company's version counter. Affects every cached user in that company on their next read. */
export async function invalidateCompanyConsent(companyId: string): Promise<void> {
  try {
    await cacheRedis.incr(`notif:consent:v:company:${companyId}`);
  } catch (err) {
    logger.warn('Company consent version bump failed', { error: err, companyId });
  }
}
```

- [ ] **Step 2: Wire `invalidateUserConsent(userId)` into preference mutations**

In `preferences.service.ts`:

```typescript
import { invalidateUserConsent } from '../dispatch/consent-gate';

async update(userId: string, data: UpdatePreferencesInput) {
  const result = await platformPrisma.userNotificationPreference.upsert({ /* ... */ });
  await invalidateUserConsent(userId);
  return result;
}

async updateCategoryPreferences(userId: string, updates: /* ... */) {
  // ... existing transaction ...
  await invalidateUserConsent(userId);
  return this.getForUser(userId);
}
```

- [ ] **Step 3: Wire `invalidateCompanyConsent(companyId)` into CompanySettings notification toggle updates**

Find the CompanySettings update method. After a successful save, if any `*Notifications` field changed, bump the company version in ONE call — no user iteration needed:

```typescript
// In company-settings.service.ts update method, after save:
const notifFieldsChanged = ['pushNotifications', 'emailNotifications', 'smsNotifications', 'whatsappNotifications', 'inAppNotifications']
  .some((field) => field in updates);
if (notifFieldsChanged) {
  await invalidateCompanyConsent(companyId);
}
```

- [ ] **Step 4: Auth logout flow — optional (stale entries TTL out)**

The versioned key strategy makes logout invalidation unnecessary — stale entries expire naturally. But for belt-and-suspenders:

```typescript
// auth.service.ts signOut:
await invalidateUserConsent(userId).catch(() => {});
```

- [ ] **Step 5: Type-check + commit**

```bash
git add src/core/notifications src/core/auth
git commit -m "feat(notifications): versioned consent cache with O(1) invalidation (user + company)"
```

---

### Task 6D: `dispatchBulk` utility

**Files:**
- Create: `avy-erp-backend/src/core/notifications/dispatch/dispatch-bulk.ts`
- Modify: `avy-erp-backend/src/core/notifications/notification.service.ts`
- Modify: `avy-erp-backend/src/workers/notification.worker.ts`

- [ ] **Step 1: Create the bulk dispatch implementation**

```typescript
// src/core/notifications/dispatch/dispatch-bulk.ts
import { nanoid } from 'nanoid';
import { platformPrisma } from '../../../config/database';
import { env } from '../../../config/env';
import { logger } from '../../../config/logger';
import { loadActiveRules } from './rule-loader';
import { renderTemplate } from '../templates/renderer';
import { checkUserRateLimit } from './rate-limiter';
import { checkDedup } from './dedup';
import { pickQueueByPriority } from '../queue/queues';
import { emitSocketEvent } from '../events/socket-emitter';
import { recordEvent } from '../events/event-emitter';
import type { NotificationChannel, NotificationPriority, Prisma } from '@prisma/client';

export interface DispatchBulkInput {
  companyId: string;
  triggerEvent: string;
  type?: string;
  entityType?: string;
  entityId?: string;
  recipients: Array<{ userId: string; tokens?: Record<string, unknown> }>;
  sharedTokens?: Record<string, unknown>;
  priority?: NotificationPriority;
  systemCritical?: boolean;
  actionUrl?: string;
  chunkSize?: number;
}

export interface DispatchBulkResult {
  traceId: string;
  enqueued: number;
  skipped: number;
  notificationIds: string[];
}

export async function dispatchBulk(input: DispatchBulkInput): Promise<DispatchBulkResult> {
  const traceId = nanoid(12);
  const chunkSize = input.chunkSize ?? env.NOTIFICATIONS_BULK_CHUNK_SIZE;

  if (!env.NOTIFICATIONS_ENABLED) {
    return { traceId, enqueued: 0, skipped: 0, notificationIds: [] };
  }

  try {
    // 1. Load rules once
    const rules = await loadActiveRules(input.companyId, input.triggerEvent);
    if (rules.length === 0) {
      logger.warn('dispatchBulk: no rules, falling back to per-recipient dispatch', {
        traceId,
        triggerEvent: input.triggerEvent,
      });
      // Fall back to per-recipient dispatch via the normal path
      const { dispatch } = await import('./dispatcher');
      for (const r of input.recipients) {
        await dispatch({
          companyId: input.companyId,
          triggerEvent: input.triggerEvent,
          type: input.type,
          entityType: input.entityType,
          entityId: input.entityId,
          explicitRecipients: [r.userId],
          tokens: { ...input.sharedTokens, ...r.tokens },
          priority: input.priority,
          systemCritical: input.systemCritical,
          actionUrl: input.actionUrl,
        });
      }
      return { traceId, enqueued: input.recipients.length, skipped: 0, notificationIds: [] };
    }

    // 2. Rate-limit filter
    const allowedRecipients: typeof input.recipients = [];
    for (const r of input.recipients) {
      const ok = await checkUserRateLimit(r.userId, input.priority ?? 'MEDIUM');
      if (ok) allowedRecipients.push(r);
    }
    const skipped = input.recipients.length - allowedRecipients.length;

    if (allowedRecipients.length === 0) {
      return { traceId, enqueued: 0, skipped, notificationIds: [] };
    }

    // 3. Build per-recipient Notification rows in one createManyAndReturn
    //    For simplicity, bulk dispatch uses the FIRST rule only — if multiple
    //    rules exist for the same trigger event, bulk mode uses the primary
    //    (first) channel. Per-rule fanout for bulk is out of scope.
    const primaryRule = rules[0];
    const priority = input.priority ?? primaryRule.priority ?? primaryRule.template.priority ?? 'MEDIUM';

    const createInputs: Prisma.NotificationCreateManyInput[] = [];
    const acceptedRecipients: typeof allowedRecipients = [];

    for (const r of allowedRecipients) {
      const rendered = renderTemplate(primaryRule.template, { ...input.sharedTokens, ...r.tokens });
      const dup = await checkDedup({
        companyId: input.companyId,
        triggerEvent: input.triggerEvent,
        entityType: input.entityType,
        entityId: input.entityId,
        recipientId: r.userId,
        payload: rendered,
      });
      if (dup) continue;

      createInputs.push({
        userId: r.userId,
        companyId: input.companyId,
        title: rendered.title,
        body: rendered.body,
        type: input.type ?? input.triggerEvent,
        category: primaryRule.category ?? null,
        entityType: input.entityType ?? null,
        entityId: input.entityId ?? null,
        data: rendered.data as Prisma.InputJsonValue,
        actionUrl: input.actionUrl ?? null,
        priority,
        status: 'UNREAD',
        isRead: false,
        deliveryStatus: {
          inApp: 'SENT',
          [primaryRule.channel.toLowerCase()]: primaryRule.channel === 'IN_APP' ? 'SENT' : 'PENDING',
        } as Prisma.InputJsonValue,
        traceId,
        ruleId: (primaryRule as any).isAdHoc ? null : primaryRule.id,
        ruleVersion: primaryRule.version ?? null,
        templateId: primaryRule.template.id === 'adhoc' ? null : primaryRule.template.id,
        templateVersion: primaryRule.template.version ?? null,
        dedupHash: rendered.dedupHash,
      });
      acceptedRecipients.push(r);
    }

    if (createInputs.length === 0) {
      return { traceId, enqueued: 0, skipped, notificationIds: [] };
    }

    const createdRows = await platformPrisma.notification.createManyAndReturn({
      data: createInputs,
      select: { id: true, userId: true },
    });

    // 4. Socket fanout per recipient
    for (const row of createdRows) {
      emitSocketEvent(row.userId, { notificationId: row.id, traceId });
    }

    // 5. Chunk into BullMQ bulk-delivery jobs, with backpressure throttling
    if (primaryRule.channel !== 'IN_APP') {
      const queue = pickQueueByPriority(priority);
      const highWater = env.NOTIFICATIONS_BULK_QUEUE_HIGH_WATER;

      for (let i = 0; i < createdRows.length; i += chunkSize) {
        // Backpressure check — throttle if queue is overloaded. HIGH/CRITICAL
        // priority never throttles (they use the high-priority queue).
        if (priority === 'LOW' || priority === 'MEDIUM') {
          try {
            const waiting = await queue.getWaitingCount();
            if (waiting > highWater) {
              logger.warn('Bulk dispatch throttled — queue overloaded', {
                queueName: queue.name,
                waiting,
                highWater,
              });
              await new Promise((r) => setTimeout(r, 200));
            }
          } catch {
            // Redis error — proceed without throttling
          }
        }

        const chunk = createdRows.slice(i, i + chunkSize);
        await queue.add('deliver-bulk', {
          isBulk: true,
          notificationIds: chunk.map((r) => r.id),
          userIds: chunk.map((r) => r.userId),
          channels: [primaryRule.channel],
          traceId,
          priority,
          systemCritical: input.systemCritical === true || priority === 'CRITICAL',
        });
      }
    }

    // 6. Record ENQUEUED events
    for (const row of createdRows) {
      await recordEvent({
        notificationId: row.id,
        channel: primaryRule.channel,
        event: 'ENQUEUED',
        traceId,
        source: 'SYSTEM',
      });
    }

    return {
      traceId,
      enqueued: createdRows.length,
      skipped,
      notificationIds: createdRows.map((r) => r.id),
    };
  } catch (err) {
    logger.error('dispatchBulk internal error', { error: err, traceId, trigger: input.triggerEvent });
    return { traceId, enqueued: 0, skipped: input.recipients.length, notificationIds: [] };
  }
}
```

- [ ] **Step 2: Expose on `notificationService`**

In `notification.service.ts`:

```typescript
import { dispatchBulk } from './dispatch/dispatch-bulk';

class NotificationService {
  dispatch = dispatch;
  dispatchBulk = dispatchBulk; // NEW
  // ... rest unchanged
}
```

- [ ] **Step 3: Extend the worker to handle `isBulk` jobs**

In `notification.worker.ts`, the job handler currently processes one `notificationId`. Extend it to handle the bulk shape:

```typescript
if (job.data.isBulk) {
  const { notificationIds, userIds, channels, traceId, priority, systemCritical } = job.data;
  // Process each (notificationId, userId) pair in parallel with Promise.allSettled
  await Promise.allSettled(
    notificationIds.map((nid: string, idx: number) =>
      processOne({
        notificationId: nid,
        userId: userIds[idx],
        channels,
        traceId,
        priority,
        systemCritical,
        attemptsMade: job.attemptsMade,
      }),
    ),
  );
  return;
}
// Existing single-notification path
```

Extract the existing per-notification logic into a `processOne()` helper that takes the same args shape. Both paths share the claim → consent → send flow.

- [ ] **Step 4: Type-check + commit**

```bash
git add src/core/notifications src/workers
git commit -m "feat(notifications): dispatchBulk utility with chunked BullMQ jobs + worker bulk handler"
```

---

### Task 6E: Provider retry wrapper

**Files:**
- Create: `avy-erp-backend/src/core/notifications/channels/provider-retry.ts`

- [ ] **Step 1: Create the retry helper**

```typescript
// src/core/notifications/channels/provider-retry.ts
import { logger } from '../../../config/logger';

export interface RetryOpts {
  maxAttempts?: number;
  baseDelayMs?: number;
  maxDelayMs?: number;
  isRetryable?: (err: unknown) => boolean;
}

/**
 * Retry wrapper for external provider calls (Twilio, Meta Cloud, FCM, etc.).
 * Exponential backoff: baseDelayMs × 4^(attempt-1), capped at maxDelayMs.
 * Only retries when `isRetryable(err)` returns true (default: always).
 */
export async function withRetry<T>(
  operation: () => Promise<T>,
  opts: RetryOpts = {},
): Promise<T> {
  const max = opts.maxAttempts ?? 3;
  const base = opts.baseDelayMs ?? 500;
  const cap = opts.maxDelayMs ?? 10_000;
  const isRetryable = opts.isRetryable ?? (() => true);

  for (let attempt = 1; attempt <= max; attempt++) {
    try {
      return await operation();
    } catch (err) {
      if (attempt === max || !isRetryable(err)) {
        throw err;
      }
      const delay = Math.min(base * Math.pow(4, attempt - 1), cap);
      logger.info('Provider retry', { attempt, delay, error: (err as Error)?.message });
      await new Promise((resolve) => setTimeout(resolve, delay));
    }
  }
  throw new Error('withRetry: unreachable');
}
```

- [ ] **Step 2: Commit**

```bash
git add src/core/notifications/channels/provider-retry.ts
git commit -m "feat(notifications): provider retry wrapper with exponential backoff"
```

---

### Task 6F: WhatsApp masking parity + extend masker

**Files:**
- Modify: `avy-erp-backend/src/core/notifications/templates/masker.ts`

- [ ] **Step 1: Extend masker to cover SMS and WHATSAPP**

```typescript
const MASKED_CHANNELS: NotificationChannel[] = ['PUSH', 'SMS', 'WHATSAPP'];

export function maskForChannel<T extends MaskablePayload>(
  channel: NotificationChannel,
  payload: T,
  sensitiveFields: string[],
): T {
  if (!MASKED_CHANNELS.includes(channel) || sensitiveFields.length === 0) return payload;

  // ... rest of the existing masking logic (string replacement + data field masking)
}
```

Remove any `'PUSH' | 'EMAIL' | ...` string-literal union in the signature and use the imported `NotificationChannel` type.

- [ ] **Step 2: Type-check + commit**

```bash
git add src/core/notifications/templates/masker.ts
git commit -m "feat(notifications): masker covers SMS + WHATSAPP with same sensitive-field rules as PUSH"
```

---

### Task 6G: `NotificationEventAggregateDaily` schema + aggregation cron + retention cron

**Files:**
- Modify: `avy-erp-backend/prisma/modules/platform/notifications.prisma`
- Modify: `avy-erp-backend/src/core/notifications/cron/notification-cron.service.ts` (extend scaffold from Task 22 — but Task 22 runs after this; in reality this task extends what will become the scaffold)

- [ ] **Step 1: Add `NotificationEventAggregateDaily` model**

```prisma
model NotificationEventAggregateDaily {
  id              String                @id @default(cuid())
  companyId       String
  date            DateTime              @db.Date
  channel         NotificationChannel
  event           NotificationEventType
  provider        String?
  count           Int                   @default(0)
  createdAt       DateTime              @default(now())
  updatedAt       DateTime              @updatedAt

  company         Company               @relation(fields: [companyId], references: [id], onDelete: Cascade)

  @@unique([companyId, date, channel, event, provider])
  @@index([companyId, date])
  @@map("notification_event_aggregate_daily")
}
```

Add back-reference on `Company`:

```prisma
  notificationEventAggregates NotificationEventAggregateDaily[]
```

- [ ] **Step 2: Merge + push**

```bash
pnpm prisma:merge && pnpm db:generate && pnpm prisma db push --skip-generate
```

- [ ] **Step 3: Defer cron implementation to Task 22 (cron service scaffold)**

The cron service file doesn't exist yet — it's created in Task 22. The aggregation and retention methods will be added during Task 22 when we implement all cron jobs. For now, just ensure the schema is in place.

- [ ] **Step 4: Commit**

```bash
git add prisma/
git commit -m "feat(notifications): NotificationEventAggregateDaily schema for analytics pre-aggregation"
```

---

### Task 6I: Observability metrics hook

**Files:**
- Create: `avy-erp-backend/src/core/notifications/metrics/notification-metrics.ts`

- [ ] **Step 1: Create the facade**

```typescript
// src/core/notifications/metrics/notification-metrics.ts
import { logger } from '../../../config/logger';
import { env } from '../../../config/env';

/**
 * Metrics facade for the notification system.
 *
 * Default implementation logs structured events (easy to grep/parse).
 * When a real metrics backend is wired later (Prometheus, Datadog, StatsD),
 * only this file changes — call sites stay untouched.
 */
export const notificationMetrics = {
  increment(name: string, tags: Record<string, string | number> = {}, value = 1): void {
    if (!env.NOTIFICATIONS_METRICS_ENABLED) return;
    logger.info(`[metric] ${name}`, { metric: name, tags, value, type: 'counter' });
  },

  histogram(name: string, value: number, tags: Record<string, string | number> = {}): void {
    if (!env.NOTIFICATIONS_METRICS_ENABLED) return;
    logger.info(`[metric] ${name}`, { metric: name, tags, value, type: 'histogram' });
  },

  gauge(name: string, value: number, tags: Record<string, string | number> = {}): void {
    if (!env.NOTIFICATIONS_METRICS_ENABLED) return;
    logger.info(`[metric] ${name}`, { metric: name, tags, value, type: 'gauge' });
  },
};
```

- [ ] **Step 2: Commit**

```bash
git add src/core/notifications/metrics
git commit -m "feat(notifications): observability metrics facade (logger-backed, future-ready)"
```

Call sites are wired in later phases as the corresponding code is touched:
- Dispatcher → `notifications.dispatched` counter + `dispatch_duration_ms` histogram (Phase 1A wire-in below)
- Rate limiter → `rate_limited` counter
- SMS/WhatsApp caps → `cost_capped` counter
- Channel router → `sent` counter tagged with status
- Bulk dispatcher → `bulk_chunk_size` histogram + `bulk_throttled` counter

Minimum wire-in for this PR: dispatcher (end of `dispatch()`), rate limiters (inside the `return false` paths), and channel router (after each send). Everything else can be added incrementally.

---

### Task 6H: Cron pagination helper

**Files:**
- Create: `avy-erp-backend/src/core/notifications/cron/pagination.ts`

- [ ] **Step 1: Create a cursor-based iterator utility**

```typescript
// src/core/notifications/cron/pagination.ts

/**
 * Cursor-based paginated iterator for Prisma findMany calls. Yields batches
 * of rows until the query returns less than `batchSize`. Prevents memory
 * spikes when processing large tenants (10k+ employees).
 *
 * Usage:
 *   for await (const batch of paginateWithCursor(
 *     (cursor) => tenantDb.employee.findMany({
 *       where: { status: 'ACTIVE' },
 *       take: 200,
 *       ...(cursor ? { skip: 1, cursor: { id: cursor } } : {}),
 *       orderBy: { id: 'asc' },
 *     }),
 *     (row) => row.id,
 *   )) {
 *     // process batch
 *   }
 */
export async function* paginateWithCursor<T extends { id: string }>(
  fetchPage: (cursor?: string) => Promise<T[]>,
  getId: (row: T) => string = (r) => r.id,
  batchSize = 200,
): AsyncGenerator<T[]> {
  let cursor: string | undefined = undefined;
  while (true) {
    const batch = await fetchPage(cursor);
    if (batch.length === 0) break;
    yield batch;
    if (batch.length < batchSize) break;
    cursor = getId(batch[batch.length - 1]);
  }
}
```

- [ ] **Step 2: Commit**

```bash
git add src/core/notifications/cron/pagination.ts
git commit -m "feat(notifications): cursor-based pagination helper for cron jobs"
```

---

## Phase 2: Core wiring Part A

### Task 7: Wire dispatcher into `leave.service.ts`

**Files:**
- Modify: `avy-erp-backend/src/modules/hr/leave/leave.service.ts`

This task wires the **submission** and **cancel** events only — approvals/rejections flow through the universal `onApprovalComplete` handler added in Task 11.

- [ ] **Step 1: Import `notificationService` at the top of the file**

```typescript
import { notificationService } from '../../../core/notifications/notification.service';
```

- [ ] **Step 2: Add dispatch in `createRequest`**

Find the `createRequest` method (around line 499). Find the end of the successful transaction (after `request` is returned from the Prisma create, before the method's final `return request;`). Add:

```typescript
// Dispatch notification to approvers (submission event).
// Approvals/rejections flow through onApprovalComplete().
try {
  const approvalRequest = await platformPrisma.approvalRequest.findFirst({
    where: { entityType: 'LeaveRequest', entityId: request.id },
    include: { workflow: true },
  });
  const firstStep = (approvalRequest?.stepHistory as any[] | null)?.[0];
  const approverIds = firstStep?.approverIds ?? [];

  await notificationService.dispatch({
    companyId,
    triggerEvent: 'LEAVE_APPLICATION',
    entityType: 'LeaveRequest',
    entityId: request.id,
    recipientContext: {
      requesterId: request.employeeId ? (await platformPrisma.employee.findUnique({
        where: { id: request.employeeId },
        select: { user: { select: { id: true } } },
      }))?.user?.id : undefined,
      approverIds,
    },
    tokens: {
      employee_name: `${request.employee?.firstName ?? ''} ${request.employee?.lastName ?? ''}`.trim(),
      leave_type: request.leaveType?.name ?? '',
      leave_days: request.daysCount,
      from_date: request.fromDate.toISOString().slice(0, 10),
      to_date: request.toDate.toISOString().slice(0, 10),
    },
    actionUrl: `/company/hr/leave-management/requests`,
    type: 'LEAVE',
  });
} catch (err) {
  logger.warn('Leave dispatch failed (non-blocking)', { error: err });
}
```

Note: the `approverIds` resolution is an inline helper here; Task 11 will extract it into a reusable `getApproverIdsFor(entityType, entityId)` helper and refactor all call sites.

- [ ] **Step 3: Add dispatch in `cancelRequest`**

Find `cancelRequest` (~line 1039). After the successful transaction completes, add:

```typescript
try {
  await notificationService.dispatch({
    companyId,
    triggerEvent: 'LEAVE_CANCELLED',
    entityType: 'LeaveRequest',
    entityId: id,
    recipientContext: {
      approverIds: request.approvedBy ? [request.approvedBy] : [],
    },
    tokens: {
      employee_name: `${request.employee?.firstName ?? ''} ${request.employee?.lastName ?? ''}`.trim(),
      leave_days: request.daysCount,
      from_date: request.fromDate.toISOString().slice(0, 10),
      to_date: request.toDate.toISOString().slice(0, 10),
    },
    type: 'LEAVE',
  });
} catch (err) {
  logger.warn('Leave cancel dispatch failed', { error: err });
}
```

- [ ] **Step 4: Type-check**

```bash
pnpm tsc --noEmit 2>&1 | tail -10
```

Expected: clean.

- [ ] **Step 5: Commit**

```bash
git add src/modules/hr/leave/leave.service.ts
git commit -m "feat(notifications): wire leave submit + cancel dispatches"
```

---

### Task 8: Create reusable approver resolver helper

**Files:**
- Create: `avy-erp-backend/src/core/notifications/dispatch/approver-resolver.ts`

Every submission dispatch needs `approverIds` from the current approval workflow step. Extract the lookup into a helper to avoid repetition across Tasks 7, 9-21.

- [ ] **Step 1: Create the helper**

```typescript
import { platformPrisma } from '../../../config/database';
import { logger } from '../../../config/logger';

/**
 * Look up the approver userIds for the current pending step of an approval
 * workflow tied to a given (entityType, entityId).
 *
 * Returns an empty array if no approval request exists, no step is pending,
 * or the step has no approver list. Call sites should tolerate an empty
 * array gracefully — the dispatcher will no-op if there are no recipients.
 */
export async function getCurrentStepApproverIds(
  entityType: string,
  entityId: string,
): Promise<string[]> {
  try {
    const request = await platformPrisma.approvalRequest.findFirst({
      where: { entityType, entityId },
      include: { workflow: true },
    });
    if (!request) return [];

    const steps = (request.workflow?.steps ?? []) as Array<{
      stepOrder: number;
      approverIds?: string[];
      approverRole?: string;
    }>;
    const currentStepOrder = request.currentStep ?? 1;
    const currentStep = steps.find((s) => s.stepOrder === currentStepOrder);
    return currentStep?.approverIds ?? [];
  } catch (err) {
    logger.warn('Failed to resolve current step approvers', { error: err, entityType, entityId });
    return [];
  }
}

/**
 * Look up the current requester user ID for an entity by joining through
 * Employee (if entity.employeeId is present) or directly using entity.userId.
 * Returns null if neither field is set.
 */
export async function getRequesterUserId(opts: {
  employeeId?: string | null;
  userId?: string | null;
}): Promise<string | null> {
  if (opts.userId) return opts.userId;
  if (opts.employeeId) {
    const emp = await platformPrisma.employee.findUnique({
      where: { id: opts.employeeId },
      select: { user: { select: { id: true } } },
    });
    return emp?.user?.id ?? null;
  }
  return null;
}
```

- [ ] **Step 2: Refactor Task 7's leave.service.ts to use it**

Replace the inline `approvalRequest.findFirst` + `stepHistory` lookup in `createRequest` with:

```typescript
import { getCurrentStepApproverIds, getRequesterUserId } from '../../../core/notifications/dispatch/approver-resolver';

// Inside createRequest, replace the inline approverIds resolution with:
const approverIds = await getCurrentStepApproverIds('LeaveRequest', request.id);
const requesterUserId = await getRequesterUserId({ employeeId: request.employeeId });

await notificationService.dispatch({
  companyId,
  triggerEvent: 'LEAVE_APPLICATION',
  entityType: 'LeaveRequest',
  entityId: request.id,
  recipientContext: {
    requesterId: requesterUserId ?? undefined,
    approverIds,
  },
  // ... tokens ...
});
```

- [ ] **Step 3: Type-check**

```bash
pnpm tsc --noEmit 2>&1 | tail -10
```

- [ ] **Step 4: Commit**

```bash
git add src/core/notifications/dispatch/approver-resolver.ts src/modules/hr/leave/leave.service.ts
git commit -m "feat(notifications): add approver resolver helper + refactor leave.service to use it"
```

---

### Task 9: Wire dispatcher into `attendance.service.ts` (overtime)

**Files:**
- Modify: `avy-erp-backend/src/modules/hr/attendance/attendance.service.ts`

Overtime approvals and rejections route through `onApprovalComplete` (Task 11). Nothing inline needed unless there's a direct state change not covered by the approval path.

- [ ] **Step 1: Audit the file for direct state changes**

```bash
grep -n "status.*APPROVED\|status.*REJECTED" src/modules/hr/attendance/attendance.service.ts | head -10
```

- [ ] **Step 2: Verify all state changes go through approval workflow**

If the `approveOvertimeRequest` / `rejectOvertimeRequest` methods create/update `ApprovalRequest` rows (which trigger `onApprovalComplete` via the SLA cron or manual approval API), no inline dispatch is needed. The ESS approval path handles it.

If any method mutates overtime status directly without `ApprovalRequest`, add a dispatch call inline.

- [ ] **Step 3: If no changes needed, commit as verification only**

```bash
# no changes
git status
```

- [ ] **Step 4: Otherwise, apply inline dispatches and commit**

---

### Task 10: Wire dispatcher into ESS submission dispatches

**Files:**
- Modify: `avy-erp-backend/src/modules/hr/ess/ess.service.ts`

Wire submission-time dispatch calls for all ~13 ESS request types. Each call is mechanical: after the Prisma create succeeds, before the method's return, call `dispatch()` with the right trigger event and tokens.

- [ ] **Step 1: Import `notificationService` and `approver-resolver`**

```typescript
import { notificationService } from '../../../core/notifications/notification.service';
import { getCurrentStepApproverIds, getRequesterUserId } from '../../../core/notifications/dispatch/approver-resolver';
```

- [ ] **Step 2: Add dispatch to `regularizeAttendance`** (~line 1728)

After the `override` is created and the approval workflow is wired:

```typescript
try {
  const approverIds = await getCurrentStepApproverIds('AttendanceOverride', override.id);
  const requesterUserId = await getRequesterUserId({ employeeId });

  await notificationService.dispatch({
    companyId,
    triggerEvent: 'ATTENDANCE_REGULARIZATION',
    entityType: 'AttendanceOverride',
    entityId: override.id,
    recipientContext: {
      requesterId: requesterUserId ?? undefined,
      approverIds,
    },
    tokens: {
      employee_name: `${employee.firstName} ${employee.lastName}`.trim(),
      date: override.date.toISOString().slice(0, 10),
      reason: override.reason ?? '',
    },
    actionUrl: `/company/hr/my-attendance`,
    type: 'ATTENDANCE',
  });
} catch (err) {
  logger.warn('Attendance regularization dispatch failed', { error: err });
}
```

- [ ] **Step 3: Repeat for each ESS request type**

For each of the following methods, add a similar dispatch block (replace trigger event + entity type + tokens):

| Method | Trigger Event | Entity Type | Category tokens |
|---|---|---|---|
| `createShiftChangeRequest` | `SHIFT_CHANGE` | `ShiftChangeRequest` | employee_name, from_date, to_date, new_shift |
| `createShiftSwapRequest` | `SHIFT_SWAP` | `ShiftSwapRequest` | employee_name, swap_with, date |
| `createWfhRequest` | `WFH_REQUEST` | `WfhRequest` | employee_name, from_date, to_date, reason |
| `createProfileUpdateRequest` | `PROFILE_UPDATE` | `ProfileUpdateRequest` | employee_name, fields |
| `createReimbursementClaim` | `REIMBURSEMENT` | `ExpenseClaim` | employee_name, amount, category |
| `createLoanApplication` | `LOAN_APPLICATION` | `LoanRecord` | employee_name, amount, purpose |
| `createITDeclaration` | `IT_DECLARATION` | `ITDeclaration` | employee_name, fy |
| `createTravelRequest` | `TRAVEL_REQUEST` | `TravelRequest` | employee_name, destination, from_date, to_date |
| `createHelpDeskTicket` | `HELPDESK_SUBMITTED` | `HelpdeskTicket` | employee_name, subject |
| `createGrievance` | `GRIEVANCE_SUBMITTED` | `Grievance` | employee_name, category, severity |
| `createOvertimeRequest` | `OVERTIME_CLAIM` | `OvertimeRequest` | employee_name, date, hours |
| `createTrainingRequest` | `TRAINING_REQUEST` | `TrainingRequest` | employee_name, training_name |

Each follows the same pattern: fetch approverIds via the resolver, get requesterUserId, call dispatch, wrap in try/catch (non-blocking).

- [ ] **Step 4: Type-check after each method to catch errors incrementally**

```bash
pnpm tsc --noEmit 2>&1 | tail -20
```

- [ ] **Step 5: Commit (batched)**

```bash
git add src/modules/hr/ess/ess.service.ts
git commit -m "feat(notifications): wire ESS submission dispatches (13 request types)"
```

---

### Task 11: Refactor `onApprovalComplete` to be the universal dispatch point

**Files:**
- Modify: `avy-erp-backend/src/modules/hr/ess/ess.service.ts` (the `onApprovalComplete` method)

The existing `onApprovalComplete(entityType, entityId, decision, approverId)` method has a `switch (entityType)` with ~11 cases. Each case updates the entity's status. This refactor adds one `dispatch()` call per case after the business update.

- [ ] **Step 1: Define the entityType → trigger mapping table**

At the top of `onApprovalComplete`, define:

```typescript
const TRIGGER_BY_ENTITY: Record<string, { approved: string; rejected: string; category: string; priority: NotificationPriority }> = {
  LeaveRequest:        { approved: 'LEAVE_APPROVED',               rejected: 'LEAVE_REJECTED',               category: 'LEAVE',              priority: 'MEDIUM' },
  AttendanceOverride:  { approved: 'ATTENDANCE_REGULARIZED',       rejected: 'ATTENDANCE_REGULARIZATION_REJECTED', category: 'ATTENDANCE', priority: 'MEDIUM' },
  OvertimeRequest:     { approved: 'OVERTIME_CLAIM_APPROVED',      rejected: 'OVERTIME_CLAIM_REJECTED',      category: 'OVERTIME',           priority: 'MEDIUM' },
  ShiftSwapRequest:    { approved: 'SHIFT_SWAP_APPROVED',          rejected: 'SHIFT_SWAP_REJECTED',          category: 'SHIFT',              priority: 'MEDIUM' },
  WfhRequest:          { approved: 'WFH_APPROVED',                 rejected: 'WFH_REJECTED',                 category: 'WFH',                priority: 'MEDIUM' },
  ExpenseClaim:        { approved: 'REIMBURSEMENT_APPROVED',       rejected: 'REIMBURSEMENT_REJECTED',       category: 'REIMBURSEMENT',      priority: 'MEDIUM' },
  LoanRecord:          { approved: 'LOAN_APPROVED',                rejected: 'LOAN_REJECTED',                category: 'LOAN',               priority: 'HIGH'   },
  ExitRequest:         { approved: 'RESIGNATION_ACCEPTED',         rejected: 'RESIGNATION_REJECTED',         category: 'RESIGNATION',        priority: 'HIGH'   },
  EmployeeTransfer:    { approved: 'EMPLOYEE_TRANSFER_APPLIED',    rejected: 'EMPLOYEE_TRANSFER_REJECTED',   category: 'EMPLOYEE_LIFECYCLE', priority: 'MEDIUM' },
  EmployeePromotion:   { approved: 'EMPLOYEE_PROMOTION_APPLIED',   rejected: 'EMPLOYEE_PROMOTION_REJECTED',  category: 'EMPLOYEE_LIFECYCLE', priority: 'HIGH'   },
  SalaryRevision:      { approved: 'SALARY_REVISION_APPROVED',     rejected: 'SALARY_REVISION_REJECTED',     category: 'PAYROLL',            priority: 'HIGH'   },
  PayrollRun:          { approved: 'PAYROLL_APPROVED',             rejected: 'PAYROLL_REJECTED',             category: 'PAYROLL',            priority: 'HIGH'   },
};
```

- [ ] **Step 2: After each case block's existing business update, dispatch — wrapped in per-case try/catch**

**CRITICAL:** Each dispatch call MUST be wrapped in its own try/catch so a failure in one entity type's notification path doesn't block approvals for other entity types. The business status update is already committed before the dispatch — if the dispatch fails, the approval still succeeds.

For each case (example: LeaveRequest):

```typescript
case 'LeaveRequest': {
  const entity = await tx.leaveRequest.findUnique({ where: { id: entityId } });
  if (!entity) break;

  const newStatus = decision === 'APPROVED' ? 'APPROVED' : 'REJECTED';
  await tx.leaveRequest.update({ where: { id: entityId }, data: { status: newStatus, approvedBy: approverId } });

  // Dispatch approval notification — isolated per-case with try/catch
  const trigger = TRIGGER_BY_ENTITY[entityType];
  if (trigger) {
    try {
      const requesterUserId = await getRequesterUserId({ employeeId: entity.employeeId, userId: entity.userId });
      if (requesterUserId) {
        await notificationService.dispatch({
          companyId,
          triggerEvent: decision === 'APPROVED' ? trigger.approved : trigger.rejected,
          entityType,
          entityId,
          explicitRecipients: [requesterUserId],
          tokens: {
            employee_name: /* fetch or pass through */,
            leave_days: entity.daysCount,
            from_date: entity.fromDate?.toISOString().slice(0, 10),
            to_date: entity.toDate?.toISOString().slice(0, 10),
            reason: entity.rejectionReason ?? '',
          },
          priority: trigger.priority,
          actionUrl: '/company/hr/my-leave',
          type: trigger.category,
        });
      }
    } catch (dispatchErr) {
      // Non-fatal: the approval itself is already committed. Log and continue
      // so a notification bug doesn't block approvals for other entities.
      logger.error('LeaveRequest approval dispatch failed (non-fatal)', {
        error: dispatchErr,
        entityId,
        decision,
      });
    }
  }
  break;
}
```

Repeat the pattern for all 12 entity types. Each case's tokens vary based on the entity's fields. **Every case MUST have its own try/catch around the dispatch call.**

- [ ] **Step 3: Remove the legacy `triggerNotification()` method's body**

Find `triggerNotification(companyId, event, data)` around line 1180. Replace with a thin delegation that logs a deprecation warning and calls `dispatch`:

```typescript
/**
 * @deprecated Use `notificationService.dispatch()` directly.
 * Legacy shim — delegates to the unified dispatcher.
 */
async triggerNotification(companyId: string, event: string, data: Record<string, unknown>) {
  logger.warn('ess.triggerNotification is deprecated — use notificationService.dispatch', { event });
  return notificationService.dispatch({
    companyId,
    triggerEvent: event,
    tokens: data,
  });
}
```

- [ ] **Step 4: Type-check**

```bash
pnpm tsc --noEmit 2>&1 | tail -20
```

- [ ] **Step 5: Commit**

```bash
git add src/modules/hr/ess/ess.service.ts
git commit -m "feat(notifications): universal dispatch in onApprovalComplete (12 entity types) + deprecate triggerNotification"
```

---

## Phase 3: Core wiring Part B

### Task 12: Wire payroll dispatches (via `dispatchBulk`)

**Files:**
- Modify: `avy-erp-backend/src/modules/hr/payroll-run/payroll-run.service.ts`

**CRITICAL:** Payroll fanout to 500+ employees MUST use `dispatchBulk()`, NOT a `for` loop with individual `dispatch()` calls. The `for` loop pattern would create 500 sequential BullMQ enqueues and 500 Notification row inserts, blowing up Redis and the worker. `dispatchBulk` batches rows into `createManyAndReturn` and chunks BullMQ jobs.

- [ ] **Step 1: Import `notificationService`**

- [ ] **Step 2: Add dispatch in `publishPayslips` method using `dispatchBulk`**

```typescript
try {
  const entries = await platformPrisma.payrollEntry.findMany({
    where: { payrollRunId: runId },
    select: {
      employeeId: true,
      employee: { select: { userId: true, firstName: true, lastName: true } },
    },
  });

  const recipients = entries
    .filter((e) => e.employee?.userId)
    .map((e) => ({
      userId: e.employee!.userId!,
      tokens: {
        employee_name: `${e.employee!.firstName} ${e.employee!.lastName}`.trim(),
      },
    }));

  if (recipients.length > 0) {
    await notificationService.dispatchBulk({
      companyId,
      triggerEvent: 'PAYSLIP_PUBLISHED',
      entityType: 'PayrollRun',
      entityId: runId,
      recipients,
      sharedTokens: {
        month_year: `${run.month}/${run.year}`,
      },
      priority: 'HIGH',
      actionUrl: '/company/hr/my-payslips',
      type: 'PAYROLL',
    });
  }
} catch (err) {
  logger.warn('Payslip published bulk dispatch failed', { error: err });
}
```

- [ ] **Step 3: Add dispatch in `disburseRun` method (`SALARY_CREDITED`, systemCritical, bulk)**

```typescript
try {
  const entries = await platformPrisma.payrollEntry.findMany({
    where: { payrollRunId: runId },
    select: {
      employeeId: true,
      netSalary: true,
      employee: { select: { userId: true, firstName: true, lastName: true } },
    },
  });

  const recipients = entries
    .filter((e) => e.employee?.userId)
    .map((e) => ({
      userId: e.employee!.userId!,
      tokens: {
        employee_name: `${e.employee!.firstName} ${e.employee!.lastName}`.trim(),
        amount: e.netSalary?.toString() ?? '',
      },
    }));

  if (recipients.length > 0) {
    await notificationService.dispatchBulk({
      companyId,
      triggerEvent: 'SALARY_CREDITED',
      entityType: 'PayrollRun',
      entityId: runId,
      recipients,
      sharedTokens: {
        month_year: `${updatedRun.month}/${updatedRun.year}`,
      },
      priority: 'CRITICAL',
      systemCritical: true,
      actionUrl: '/company/hr/my-payslips',
      type: 'PAYROLL',
    });
  }
} catch (err) {
  logger.warn('Salary credited bulk dispatch failed', { error: err });
}
```

- [ ] **Step 4: Add dispatch in `submitForApproval` (if present) for `PAYROLL_APPROVAL`**

For this one, the recipient is a single approver or a small approver list, so regular `dispatch()` is fine (no bulk needed).

- [ ] **Step 5: Type-check + commit**

```bash
pnpm tsc --noEmit 2>&1 | tail -10
git add src/modules/hr/payroll-run/payroll-run.service.ts
git commit -m "feat(notifications): wire payroll payslip published + salary credited via dispatchBulk"
```

---

### Task 13: Wire employee lifecycle + transfer + promotion dispatches

**Files:**
- Modify: `avy-erp-backend/src/modules/hr/employee/employee.service.ts`
- Modify: `avy-erp-backend/src/modules/hr/transfer/transfer.service.ts`

- [ ] **Step 1: employee.service.ts — `createEmployee` method**

After the employee + user creation transaction completes:

```typescript
if (employee.userId) {
  try {
    await notificationService.dispatch({
      companyId,
      triggerEvent: 'EMPLOYEE_ONBOARDED',
      entityType: 'Employee',
      entityId: employee.id,
      explicitRecipients: [employee.userId],
      tokens: {
        employee_name: `${employee.firstName} ${employee.lastName}`.trim(),
        employee_id: employee.employeeId,
        designation: employee.designation?.name ?? '',
        department: employee.department?.name ?? '',
        joining_date: employee.joiningDate.toISOString().slice(0, 10),
      },
      type: 'EMPLOYEE_LIFECYCLE',
    });
  } catch (err) {
    logger.warn('Employee onboarded dispatch failed', { error: err });
  }
}
```

- [ ] **Step 2: transfer.service.ts — `createTransfer` and `applyTransfer`**

Follow the same pattern. `createTransfer` → `EMPLOYEE_TRANSFER` to APPROVER. `applyTransfer` → `EMPLOYEE_TRANSFER_APPLIED` to EMPLOYEE + new MANAGER.

- [ ] **Step 3: transfer.service.ts — `createPromotion` and `applyPromotion`**

Same. `createPromotion` → `EMPLOYEE_PROMOTION` to APPROVER. `applyPromotion` → `EMPLOYEE_PROMOTION_APPLIED` to EMPLOYEE + HR.

- [ ] **Step 4: Type-check + commit**

```bash
git add src/modules/hr/employee src/modules/hr/transfer
git commit -m "feat(notifications): wire employee onboarding + transfer + promotion dispatches"
```

---

### Task 14: Wire salary revision dispatches

**Files:**
- Modify: `avy-erp-backend/src/modules/hr/payroll/payroll.service.ts`

- [ ] **Step 1: `updateEmployeeSalary` method (~line 517)**

After the salary update completes, dispatch `SALARY_REVISION` to APPROVER (if workflow exists) or directly to EMPLOYEE with masked amount:

```typescript
try {
  const emp = await platformPrisma.employee.findUnique({
    where: { id: salaryRecord.employeeId },
    select: { userId: true, firstName: true, lastName: true },
  });
  if (emp?.userId) {
    await notificationService.dispatch({
      companyId,
      triggerEvent: 'SALARY_REVISION',
      entityType: 'SalaryRevision',
      entityId: salaryRecord.id,
      explicitRecipients: [emp.userId],
      tokens: {
        employee_name: `${emp.firstName} ${emp.lastName}`.trim(),
        new_salary: salaryRecord.annualCtc?.toString() ?? '',
        effective_date: salaryRecord.effectiveDate?.toISOString().slice(0, 10) ?? '',
      },
      priority: 'HIGH',
      type: 'PAYROLL',
    });
  }
} catch (err) {
  logger.warn('Salary revision dispatch failed', { error: err });
}
```

- [ ] **Step 2: Commit**

---

### Task 15: Wire offboarding dispatches

**Files:**
- Modify: `avy-erp-backend/src/modules/hr/offboarding/offboarding.service.ts`

- [ ] **Step 1: `createExitRequest` — dispatch `RESIGNATION` to HR + approvers**

- [ ] **Step 2: `approveFnF` — dispatch `FNF_INITIATED` to employee**

- [ ] **Step 3: `payFnF` — dispatch `FNF_COMPLETED` to employee + HR (systemCritical: true)**

- [ ] **Step 4: Commit**

```bash
git add src/modules/hr/offboarding
git commit -m "feat(notifications): wire offboarding dispatches (resignation, FnF)"
```

---

### Task 16: Rule cache invalidation on admin CRUD

**Files:**
- Modify: `avy-erp-backend/src/modules/hr/ess/ess.service.ts` (or wherever NotificationRule/Template CRUD lives)

The rule loader caches rules in Redis for 60s. Admins editing templates/rules via the UI should invalidate the cache immediately.

- [ ] **Step 1: Import `invalidateRuleCache`**

```typescript
import { invalidateRuleCache } from '../../../core/notifications/dispatch/rule-loader';
```

- [ ] **Step 2: Call after create/update/delete of NotificationTemplate and NotificationRule**

Find the CRUD methods (e.g., `createRule`, `updateRule`, `deleteRule`, `createTemplate`, `updateTemplate`, `deleteTemplate`). Add after each successful write:

```typescript
await invalidateRuleCache(companyId, rule.triggerEvent);
```

For templates (which can be linked to multiple rules), invalidate the whole company:

```typescript
await invalidateRuleCache(companyId);
```

- [ ] **Step 3: Commit**

```bash
git add src/modules/hr/ess
git commit -m "feat(notifications): invalidate rule cache on template/rule CRUD"
```

---

## Phase 4: Core wiring Part C

### Task 17: Wire recruitment dispatches

**Files:**
- Modify: `avy-erp-backend/src/modules/hr/advanced/advanced.service.ts`
- Modify: `avy-erp-backend/src/modules/hr/advanced/offer.service.ts`

- [ ] **Step 1: `advanceCandidateStage` → `CANDIDATE_STAGE_CHANGED` to HR**

- [ ] **Step 2: `offer.service.createOffer` → `OFFER_SENT` to HR**

- [ ] **Step 3: `offer.service.updateOfferStatus` → `OFFER_ACCEPTED` or `OFFER_REJECTED`**

- [ ] **Step 4: Verify `INTERVIEW_SCHEDULED` and `INTERVIEW_COMPLETED` hr-listener wiring still works**

Read `src/shared/events/listeners/hr-listeners.ts`. Confirm the listeners use `notificationService.dispatch()` (already fixed in `feat/notifications`).

- [ ] **Step 5: Commit**

```bash
git add src/modules/hr/advanced
git commit -m "feat(notifications): wire recruitment dispatches (candidate stage, offers)"
```

---

### Task 18: Wire training + assets dispatches

**Files:**
- Modify: `avy-erp-backend/src/modules/hr/advanced/advanced.service.ts`

- [ ] **Step 1: Assets — `createAssetAssignment` → `ASSET_ASSIGNED` to EMPLOYEE**

- [ ] **Step 2: Assets — `returnAssetAssignment` → `ASSET_RETURNED` to ADMIN**

- [ ] **Step 3: Training — `createTrainingNomination` already wired via hr-listeners; verify**

- [ ] **Step 4: Commit**

```bash
git add src/modules/hr/advanced
git commit -m "feat(notifications): wire asset assignment + return dispatches"
```

---

### Task 19: Wire support ticket bridge

**Files:**
- Modify: `avy-erp-backend/src/core/support/support.service.ts`

- [ ] **Step 1: `createTicket` → `TICKET_CREATED` to ADMIN (super-admin support team)**

After `emitNewTicket` socket emission (line ~120):

```typescript
try {
  await notificationService.dispatch({
    companyId: params.companyId,
    triggerEvent: 'TICKET_CREATED',
    entityType: 'SupportTicket',
    entityId: ticket.id,
    // Notify super-admin support team (no specific recipientContext — resolver handles ADMIN role)
    tokens: {
      ticket_subject: ticket.subject,
      ticket_id: ticket.id,
      category: ticket.category,
    },
    type: 'SUPPORT',
    actionUrl: `/admin/support/tickets/${ticket.id}`,
  });
} catch (err) {
  logger.warn('Ticket created dispatch failed', { error: err });
}
```

- [ ] **Step 2: `sendMessage` → `TICKET_MESSAGE`**

Determine the "other party" (if the sender is the customer, recipient is the super-admin team; if the sender is a super-admin, recipient is the customer who created the ticket):

```typescript
const recipients = message.senderRole === 'SUPER_ADMIN'
  ? [ticket.createdBy]  // customer
  : undefined;  // resolver picks ADMIN role

await notificationService.dispatch({
  companyId: params.companyId,
  triggerEvent: 'TICKET_MESSAGE',
  entityType: 'SupportTicket',
  entityId: ticket.id,
  explicitRecipients: recipients,
  tokens: {
    ticket_subject: ticket.subject,
    sender_name: message.senderName,
    message_preview: message.body.slice(0, 100),
  },
  type: 'SUPPORT',
  actionUrl: `/company/support/tickets/${ticket.id}`,
});
```

- [ ] **Step 3: `updateStatus` → `TICKET_STATUS_CHANGED` to the requester**

- [ ] **Step 4: `approveModuleChange` → `MODULE_CHANGE_APPROVED` to the company admin, priority HIGH**

- [ ] **Step 5: Commit**

```bash
git add src/core/support
git commit -m "feat(notifications): bridge support ticket events into dispatcher"
```

---

### Task 20: Wire auth critical dispatches

**Files:**
- Modify: `avy-erp-backend/src/core/auth/auth.service.ts`

- [ ] **Step 1: `forgotPassword` → `PASSWORD_RESET` (CRITICAL, systemCritical: true)**

After the reset code is saved (but before the existing email send), dispatch:

```typescript
try {
  await notificationService.dispatch({
    companyId: user.companyId ?? '',
    triggerEvent: 'PASSWORD_RESET',
    entityType: 'User',
    entityId: user.id,
    explicitRecipients: [user.id],
    tokens: {
      user_name: `${user.firstName} ${user.lastName}`.trim(),
      reset_code: code, // masked on PUSH via sensitiveFields: ['reset_code']
      expires_in: '15 minutes',
    },
    priority: 'CRITICAL',
    systemCritical: true,
    type: 'AUTH',
  });
} catch (err) {
  logger.warn('Password reset dispatch failed', { error: err });
}
```

**Note:** The existing direct email send via `registration-emails.ts` can be removed — the dispatcher now handles the email via the `PASSWORD_RESET` template (which is seeded as EMAIL + PUSH). If keeping the direct send for reliability, mark it as redundant in a code comment.

- [ ] **Step 2: `login` → detect new device → `NEW_DEVICE_LOGIN`**

Check the most recent `ActiveSession` for this user before the new one is created. If none exists or the `deviceInfo` / `ipAddress` differs significantly:

```typescript
const lastSession = await platformPrisma.activeSession.findFirst({
  where: { userId: user.id },
  orderBy: { lastActiveAt: 'desc' },
});
const isNewDevice = !lastSession || lastSession.deviceInfo !== currentDeviceInfo;

if (isNewDevice) {
  try {
    await notificationService.dispatch({
      companyId: user.companyId ?? '',
      triggerEvent: 'NEW_DEVICE_LOGIN',
      entityType: 'User',
      entityId: user.id,
      explicitRecipients: [user.id],
      tokens: {
        user_name: `${user.firstName} ${user.lastName}`.trim(),
        device_info: currentDeviceInfo,
        ip_address: req.ip ?? 'unknown',
        login_time: new Date().toISOString(),
      },
      priority: 'CRITICAL',
      systemCritical: true,
      type: 'AUTH',
    });
  } catch (err) {
    logger.warn('New device login dispatch failed', { error: err });
  }
}
```

- [ ] **Step 3: Account lock (if present) → `ACCOUNT_LOCKED`**

If an account lock path exists (e.g., after N failed login attempts), dispatch critical notification to the user + super admin.

- [ ] **Step 4: Add `PASSWORD_RESET`, `NEW_DEVICE_LOGIN`, `ACCOUNT_LOCKED` to default template catalogue**

Already present for `PASSWORD_RESET`. Add the other two to `src/core/notifications/templates/defaults.ts`:

```typescript
{
  code: 'NEW_DEVICE_LOGIN',
  name: 'New Device Login',
  subject: 'Security Alert: New device login',
  body: 'A new login was detected for your account on {{device_info}} from {{ip_address}} at {{login_time}}. If this wasn\'t you, reset your password immediately.',
  channels: ['EMAIL', 'PUSH', 'IN_APP'],
  priority: 'CRITICAL',
  variables: ['user_name', 'device_info', 'ip_address', 'login_time'],
  sensitiveFields: [],
  category: 'AUTH',
  triggerEvent: 'NEW_DEVICE_LOGIN',
  recipientRole: 'REQUESTER',
},
{
  code: 'ACCOUNT_LOCKED',
  name: 'Account Locked',
  subject: 'Security Alert: Account locked',
  body: 'Your account has been locked due to {{reason}}. Contact your administrator to unlock.',
  channels: ['EMAIL', 'PUSH', 'IN_APP'],
  priority: 'CRITICAL',
  variables: ['user_name', 'reason'],
  sensitiveFields: [],
  category: 'AUTH',
  triggerEvent: 'ACCOUNT_LOCKED',
  recipientRole: 'REQUESTER',
},
```

- [ ] **Step 5: Re-seed templates for existing tenants**

```bash
pnpm ts-node -T prisma/seeds/2026-04-09-seed-default-notification-templates.ts
```

Expected: skipped for existing, created for the two new templates.

- [ ] **Step 6: Commit**

```bash
git add src/core/auth src/core/notifications/templates/defaults.ts
git commit -m "feat(notifications): wire auth critical events (password reset, new device login, account locked)"
```

---

### Task 21: Final Phase 4 type-check + integration verification

- [ ] **Step 1: Full type-check**

```bash
cd avy-erp-backend && pnpm tsc --noEmit 2>&1 | tail -20
```

Expected: clean.

- [ ] **Step 2: Smoke test — start dev server and trigger a leave request via API**

```bash
pnpm dev &
sleep 5
# Hit the endpoint via a local curl / Postman request
# Verify log shows 'Leave dispatch' and notification appears in DB
```

- [ ] **Step 3: Kill dev server, commit phase summary**

```bash
git log --oneline -20
```

---

## Phase 5: Cron events

### Task 22: Create notification cron service scaffold

**Files:**
- Create: `avy-erp-backend/src/core/notifications/cron/notification-cron.service.ts`

- [ ] **Step 1: Scaffold the service class — includes aggregation + retention crons**

```typescript
import cron, { ScheduledTask } from 'node-cron';
import pLimit from 'p-limit';
import { DateTime } from 'luxon';
import { logger } from '../../../config/logger';
import { env } from '../../../config/env';
import { platformPrisma } from '../../../config/database';
import { cacheRedis } from '../../../config/redis';
import { notificationService } from '../notification.service';
import { paginateWithCursor } from './pagination';

class NotificationCronService {
  private jobs: ScheduledTask[] = [];

  startAll(): void {
    if (!env.NOTIFICATIONS_CRON_ENABLED) {
      logger.info('Notification cron disabled via env');
      return;
    }

    // Informational event crons
    this.jobs.push(cron.schedule('0 8 * * *', () => this.runBirthday()));
    this.jobs.push(cron.schedule('0 8 * * *', () => this.runWorkAnniversary()));
    this.jobs.push(cron.schedule('0 7 * * *', () => this.runHolidayReminder()));
    this.jobs.push(cron.schedule('0 9 * * *', () => this.runProbationEnd()));
    this.jobs.push(cron.schedule('0 8 * * *', () => this.runAssetReturnDue()));
    this.jobs.push(cron.schedule('0 9 * * *', () => this.runCertificateExpiring()));
    this.jobs.push(cron.schedule('0 7 * * *', () => this.runTrainingSessionUpcoming()));

    // Operational crons (spec §4A.9 and §4A.12)
    this.jobs.push(cron.schedule('30 1 * * *', () => this.runEventAggregation()));
    this.jobs.push(cron.schedule('0 2 * * *', () => this.runEventCleanup()));

    logger.info('Notification cron service started', { jobs: this.jobs.length });
  }

  stopAll(): void {
    for (const job of this.jobs) job.stop();
    this.jobs = [];
  }

  /** Idempotent cron dedup with 24h TTL — prevents double-fire on same day */
  private async checkCronDedup(key: string): Promise<boolean> {
    try {
      const result = await cacheRedis.set(`notif:cron-dedup:${key}`, '1', 'EX', 86400, 'NX');
      return result === 'OK';
    } catch (err) {
      logger.warn('Cron dedup check failed (fail-open)', { error: err, key });
      return true;
    }
  }

  // Stub methods — filled in by subsequent tasks
  private async runBirthday(): Promise<void> { /* Task 23 */ }
  private async runWorkAnniversary(): Promise<void> { /* Task 23 */ }
  private async runHolidayReminder(): Promise<void> { /* Task 24 */ }
  private async runProbationEnd(): Promise<void> { /* Task 24 */ }
  private async runAssetReturnDue(): Promise<void> { /* Task 25 */ }
  private async runCertificateExpiring(): Promise<void> { /* Task 25 */ }
  private async runTrainingSessionUpcoming(): Promise<void> { /* Task 25 */ }
  private async runEventAggregation(): Promise<void> { /* Task 26A */ }
  private async runEventCleanup(): Promise<void> { /* Task 26A */ }
}

export const notificationCronService = new NotificationCronService();
```

- [ ] **Step 2: Wire into server startup**

Modify `src/app/server.ts` — after `analyticsCronService.startAll();`:

```typescript
// Notification informational cron jobs
import { notificationCronService } from '../core/notifications/cron/notification-cron.service';
// ...
notificationCronService.startAll();
```

- [ ] **Step 3: Type-check + commit**

```bash
git add src/core/notifications/cron src/app/server.ts
git commit -m "feat(notifications): cron service scaffold with 7 repeatable jobs"
```

---

### Task 23: Implement birthday + work anniversary crons

**Files:**
- Modify: `avy-erp-backend/src/core/notifications/cron/notification-cron.service.ts`

- [ ] **Step 1: Import dependencies**

```typescript
import { DateTime } from 'luxon';
import { platformPrisma } from '../../../config/database';
import { tenantConnectionManager } from '../../../config/tenant-manager'; // or wherever it lives
import { notificationService } from '../notification.service';
import { cacheRedis } from '../../../config/redis';
```

- [ ] **Step 2: Implement cronDedup helper**

```typescript
private async checkCronDedup(key: string): Promise<boolean> {
  const result = await cacheRedis.set(`notif:cron-dedup:${key}`, '1', 'EX', 86400, 'NX');
  return result === 'OK'; // true = proceed, false = already fired today
}
```

- [ ] **Step 3: Implement `runBirthday` with pagination + parallelism**

```typescript
private async runBirthday(): Promise<void> {
  try {
    const companies = await platformPrisma.company.findMany({
      select: { id: true, name: true, settings: { select: { timezone: true } } },
    });

    // Run companies in parallel with a concurrency cap to avoid overwhelming
    // the tenant connection pool. Use Promise.allSettled so one failing tenant
    // doesn't stop the others.
    const limit = pLimit(env.NOTIFICATIONS_CRON_COMPANY_CONCURRENCY);
    const results = await Promise.allSettled(
      companies.map((company) => limit(() => this.runBirthdayForCompany(company))),
    );

    const failures = results.filter((r) => r.status === 'rejected');
    if (failures.length > 0) {
      logger.warn('Birthday cron: some companies failed', { count: failures.length });
    }
  } catch (err) {
    logger.error('Birthday cron failed', { error: err });
  }
}

private async runBirthdayForCompany(company: {
  id: string;
  name: string;
  settings: { timezone: string | null } | null;
}): Promise<void> {
  // Per-tenant jitter to avoid thundering herd — spreads 100 tenants across
  // a 0-60s window instead of all hitting the DB at the same cron tick.
  const jitterMs = Math.floor(Math.random() * env.NOTIFICATIONS_CRON_JITTER_MS);
  await new Promise((resolve) => setTimeout(resolve, jitterMs));

  const tz = company.settings?.timezone ?? 'UTC';
  const today = DateTime.now().setZone(tz);
  const mmdd = today.toFormat('MM-dd');
  const todayStr = today.toFormat('yyyy-MM-dd');

  let tenantDb: any = null;
  try {
    tenantDb = await tenantConnectionManager.getClient({ schemaName: /* company schema */ });

    // Cursor-based pagination to avoid loading 10k employees into memory
    const BATCH_SIZE = 200;
    for await (const batch of paginateWithCursor<{ id: string; firstName: string; lastName: string; dateOfBirth: Date | null; userId: string | null }>(
      (cursor) => tenantDb.employee.findMany({
        where: {
          status: { notIn: ['EXITED', 'TERMINATED'] },
          dateOfBirth: { not: null },
        },
        select: { id: true, firstName: true, lastName: true, dateOfBirth: true, userId: true },
        take: BATCH_SIZE,
        ...(cursor ? { skip: 1, cursor: { id: cursor } } : {}),
        orderBy: { id: 'asc' },
      }),
      (r) => r.id,
      BATCH_SIZE,
    )) {
      // Filter this batch for today's birthdays
      const celebrating = batch.filter(
        (e) => e.userId && e.dateOfBirth && DateTime.fromJSDate(e.dateOfBirth).toFormat('MM-dd') === mmdd,
      );
      if (celebrating.length === 0) continue;

      // Cron dedup per employee (24h TTL)
      const allowedRecipients: Array<{ userId: string; tokens: Record<string, unknown> }> = [];
      for (const emp of celebrating) {
        const dedupKey = `BIRTHDAY:${company.id}:${emp.id}:${todayStr}`;
        const ok = await this.checkCronDedup(dedupKey);
        if (ok) {
          allowedRecipients.push({
            userId: emp.userId!,
            tokens: { employee_name: `${emp.firstName} ${emp.lastName}`.trim() },
          });
        }
      }

      // Use dispatchBulk for batch fanout (chunks internally)
      if (allowedRecipients.length > 0) {
        await notificationService.dispatchBulk({
          companyId: company.id,
          triggerEvent: 'BIRTHDAY',
          entityType: 'Employee',
          recipients: allowedRecipients,
          priority: 'LOW',
          type: 'BIRTHDAY_ANNIVERSARY',
        });
      }
    }
  } catch (err) {
    logger.error('Birthday cron per-company failed', { error: err, companyId: company.id });
  } finally {
    if (tenantDb) {
      try { await tenantDb.$disconnect(); } catch { /* ignore */ }
    }
  }
}
```

**Key changes from the naive version:**
1. **Parallelism:** `Promise.allSettled` + `pLimit` caps company concurrency at `NOTIFICATIONS_CRON_COMPANY_CONCURRENCY` (default 5).
2. **Pagination:** `paginateWithCursor` iterates in 200-row batches, never loading the full employee table.
3. **Bulk dispatch:** `dispatchBulk` for fanout, chunks BullMQ jobs internally.
4. **Cron dedup:** 24h TTL Redis key per employee prevents double-fire if cron runs twice.
5. **Connection cleanup:** `finally` block ensures `tenantDb.$disconnect()` always runs.

**Note:** The `tenantConnectionManager.getClient()` signature and schema name lookup depend on the existing codebase pattern from `analytics-cron.service.ts`. Match that pattern exactly.

- [ ] **Step 4: Implement `runWorkAnniversary`**

Same pattern but matches `joiningDate.toFormat('MM-dd')` and computes `years_of_service = today.year - joiningDate.year`. Skip if `years_of_service === 0` (same-day hires).

- [ ] **Step 5: Type-check + commit**

```bash
git add src/core/notifications/cron
git commit -m "feat(notifications): birthday + work anniversary cron jobs with per-company iteration"
```

---

### Task 24: Implement holiday reminder + probation end crons

**Files:**
- Modify: `avy-erp-backend/src/core/notifications/cron/notification-cron.service.ts`

- [ ] **Step 1: `runHolidayReminder` — fetches upcoming holidays within 3 days**

- [ ] **Step 2: `runProbationEnd` — fetches employees with probation ending in 7 days**

Both follow the per-company iteration pattern from Task 23.

- [ ] **Step 3: Commit**

---

### Task 25: Implement asset return + certificate expiring + training session crons

**Files:**
- Modify: `avy-erp-backend/src/core/notifications/cron/notification-cron.service.ts`

- [ ] **Step 1: `runAssetReturnDue` — assets due in next 3 days**

- [ ] **Step 2: `runCertificateExpiring` — certificates expiring in next 30 days**

- [ ] **Step 3: `runTrainingSessionUpcoming` — sessions in next 24 hours**

- [ ] **Step 4: Commit**

```bash
git add src/core/notifications/cron
git commit -m "feat(notifications): asset return + certificate expiring + training session cron jobs"
```

---

### Task 26: Seed cron templates

**Files:**
- Modify: `avy-erp-backend/src/core/notifications/templates/defaults.ts`

- [ ] **Step 1: Add 7 new template entries**

Following the existing pattern in `defaults.ts`:

```typescript
{
  code: 'BIRTHDAY',
  name: 'Happy Birthday',
  body: 'Happy Birthday, {{employee_name}}! 🎂 Wishing you a wonderful year ahead.',
  channels: ['IN_APP', 'PUSH'],
  priority: 'LOW',
  variables: ['employee_name'],
  sensitiveFields: [],
  category: 'BIRTHDAY_ANNIVERSARY',
  triggerEvent: 'BIRTHDAY',
  recipientRole: 'EMPLOYEE',
},
{
  code: 'WORK_ANNIVERSARY',
  name: 'Work Anniversary',
  body: 'Congratulations, {{employee_name}}! Today marks {{years_of_service}} years with us. Thank you for your dedication!',
  channels: ['IN_APP', 'PUSH'],
  priority: 'LOW',
  variables: ['employee_name', 'years_of_service'],
  sensitiveFields: [],
  category: 'BIRTHDAY_ANNIVERSARY',
  triggerEvent: 'WORK_ANNIVERSARY',
  recipientRole: 'EMPLOYEE',
},
{
  code: 'HOLIDAY_REMINDER',
  name: 'Upcoming Holiday',
  body: '{{holiday_name}} is coming up on {{holiday_date}} ({{days_until}} days away). Plan your schedule accordingly.',
  channels: ['IN_APP'],
  priority: 'LOW',
  variables: ['holiday_name', 'holiday_date', 'days_until'],
  sensitiveFields: [],
  category: 'ANNOUNCEMENTS',
  triggerEvent: 'HOLIDAY_REMINDER',
  recipientRole: 'ALL',
},
{
  code: 'PROBATION_END_REMINDER',
  name: 'Probation Ending Soon',
  subject: 'Probation Review Required: {{employee_name}}',
  body: '{{employee_name}}\'s probation period ends on {{probation_end_date}}. Please schedule a review meeting.',
  channels: ['IN_APP', 'EMAIL'],
  priority: 'MEDIUM',
  variables: ['employee_name', 'probation_end_date'],
  sensitiveFields: [],
  category: 'EMPLOYEE_LIFECYCLE',
  triggerEvent: 'PROBATION_END_REMINDER',
  recipientRole: 'MANAGER',
},
{
  code: 'ASSET_RETURN_DUE',
  name: 'Asset Return Due',
  body: 'Your assigned asset "{{asset_name}}" is due for return on {{due_date}}. Please return it on time.',
  channels: ['IN_APP', 'PUSH', 'EMAIL'],
  priority: 'MEDIUM',
  variables: ['asset_name', 'due_date'],
  sensitiveFields: [],
  category: 'ASSETS',
  triggerEvent: 'ASSET_RETURN_DUE',
  recipientRole: 'EMPLOYEE',
},
{
  code: 'TRAINING_SESSION_UPCOMING',
  name: 'Training Session Tomorrow',
  body: 'Your training session "{{training_name}}" is scheduled for {{session_date}} at {{session_time}}. See you there!',
  channels: ['IN_APP', 'PUSH', 'EMAIL'],
  priority: 'MEDIUM',
  variables: ['training_name', 'session_date', 'session_time'],
  sensitiveFields: [],
  category: 'TRAINING',
  triggerEvent: 'TRAINING_SESSION_UPCOMING',
  recipientRole: 'EMPLOYEE',
},
```

- [ ] **Step 2: Re-seed templates for existing tenants**

```bash
pnpm ts-node -T prisma/seeds/2026-04-09-seed-default-notification-templates.ts
```

Expected: new templates created for existing companies, old ones skipped.

- [ ] **Step 3: Commit**

```bash
git add src/core/notifications/templates/defaults.ts
git commit -m "feat(notifications): add 6 new default templates for cron events"
```

---

### Task 26A: Implement event aggregation + retention cleanup crons

**Files:**
- Modify: `avy-erp-backend/src/core/notifications/cron/notification-cron.service.ts`

These two crons enable the analytics dashboard's pre-aggregation strategy (spec §4.6, §4A.9, §4A.12). They were scheduled in Task 22's scaffold; this task implements the method bodies.

- [ ] **Step 1: Implement `runEventAggregation` (1:30 AM daily)**

```typescript
private async runEventAggregation(): Promise<void> {
  try {
    const yesterday = DateTime.now().minus({ days: 1 }).startOf('day').toJSDate();
    const todayStart = DateTime.now().startOf('day').toJSDate();

    // Group yesterday's events by (companyId, channel, event, provider)
    const aggregates = await platformPrisma.$queryRaw<
      Array<{
        companyId: string;
        channel: string;
        event: string;
        provider: string | null;
        count: bigint;
      }>
    >`
      SELECT
        n."companyId",
        ne.channel::text as channel,
        ne.event::text as event,
        ne.provider,
        COUNT(*)::bigint as count
      FROM notification_events ne
      JOIN notifications n ON n.id = ne."notificationId"
      WHERE ne."occurredAt" >= ${yesterday} AND ne."occurredAt" < ${todayStart}
      GROUP BY n."companyId", ne.channel, ne.event, ne.provider
    `;

    let upserted = 0;
    for (const agg of aggregates) {
      try {
        await platformPrisma.notificationEventAggregateDaily.upsert({
          where: {
            companyId_date_channel_event_provider: {
              companyId: agg.companyId,
              date: yesterday,
              channel: agg.channel as any,
              event: agg.event as any,
              provider: agg.provider ?? '',
            },
          },
          create: {
            companyId: agg.companyId,
            date: yesterday,
            channel: agg.channel as any,
            event: agg.event as any,
            provider: agg.provider,
            count: Number(agg.count),
          },
          update: { count: Number(agg.count) },
        });
        upserted++;
      } catch (err) {
        logger.warn('Aggregate upsert failed', { error: err, agg });
      }
    }
    logger.info('Notification event aggregation complete', { rows: upserted });
  } catch (err) {
    logger.error('Notification event aggregation failed', { error: err });
  }
}
```

- [ ] **Step 2: Implement `runEventCleanup` (2:00 AM daily — 30 min after aggregation)**

```typescript
private async runEventCleanup(): Promise<void> {
  try {
    const cutoff = DateTime.now()
      .minus({ days: env.NOTIFICATIONS_EVENT_RETENTION_DAYS })
      .toJSDate();

    let totalDeleted = 0;
    // Delete in 10K batches to avoid long-running transactions
    while (true) {
      // Find a batch of ids to delete (older than cutoff)
      const batch = await platformPrisma.notificationEvent.findMany({
        where: { occurredAt: { lt: cutoff } },
        select: { id: true },
        take: 10_000,
      });
      if (batch.length === 0) break;

      const result = await platformPrisma.notificationEvent.deleteMany({
        where: { id: { in: batch.map((b) => b.id) } },
      });
      totalDeleted += result.count;
      if (batch.length < 10_000) break;
    }

    logger.info('NotificationEvent cleanup complete', {
      totalDeleted,
      retentionDays: env.NOTIFICATIONS_EVENT_RETENTION_DAYS,
    });
  } catch (err) {
    logger.error('NotificationEvent cleanup failed', { error: err });
  }
}
```

- [ ] **Step 3: Type-check + commit**

```bash
pnpm tsc --noEmit
git add src/core/notifications/cron
git commit -m "feat(notifications): aggregation + retention cleanup crons (1:30 AM / 2:00 AM)"
```

---

### Task 27: Cron dry-run verification

- [ ] **Step 1: Start dev server with `NOTIFICATIONS_CRON_ENABLED=true`**

- [ ] **Step 2: Manually trigger one cron method via a dev-only REPL or by editing the cron schedule to `* * * * *` temporarily**

- [ ] **Step 3: Verify logs and NotificationEvent rows**

- [ ] **Step 4: Revert any schedule changes, commit**

---

## Phase 6: SMS provider (Twilio)

### Task 28: Twilio provider implementation

**Files:**
- Create: `avy-erp-backend/src/core/notifications/channels/sms/twilio.provider.ts`

- [ ] **Step 1: Create the provider file with retry + dry-run**

```typescript
import twilio, { Twilio } from 'twilio';
import { env } from '../../../../config/env';
import { logger } from '../../../../config/logger';
import { withRetry } from '../provider-retry';
import type { NotificationPriority } from '@prisma/client';

let client: Twilio | null = null;

function getClient(): Twilio | null {
  if (client) return client;
  if (!env.TWILIO_ACCOUNT_SID || !env.TWILIO_AUTH_TOKEN) return null;
  client = twilio(env.TWILIO_ACCOUNT_SID, env.TWILIO_AUTH_TOKEN);
  return client;
}

export interface TwilioSendPayload {
  to: string;
  body: string;
  priority: NotificationPriority;
}

export interface TwilioSendResult {
  provider: 'twilio';
  messageId: string | null;
}

/** Transient errors worth retrying. Non-retryable errors (auth, bad phone) bubble immediately. */
function isTransientTwilioError(err: unknown): boolean {
  const e = err as { status?: number; code?: number | string };
  if (e.status === 503 || e.status === 429) return true;
  if (e.code === 'ECONNRESET' || e.code === 'ETIMEDOUT') return true;
  // Twilio error codes: https://www.twilio.com/docs/api/errors
  // 20429 = too many requests (rate limit) - retry
  if (e.code === 20429) return true;
  return false;
}

export const twilioProvider = {
  async send(payload: TwilioSendPayload, traceId: string): Promise<TwilioSendResult> {
    if (!env.NOTIFICATIONS_SMS_ENABLED) {
      throw Object.assign(new Error('SMS_DISABLED'), { code: 'SMS_DISABLED' });
    }

    // Dry-run mode — log and return without hitting the provider
    if (env.NOTIFICATIONS_SMS_DRY_RUN) {
      logger.info('[DRY-RUN] SMS would have been sent', { traceId, to: payload.to, body: payload.body });
      return { provider: 'twilio', messageId: 'dry-run' };
    }

    const c = getClient();
    if (!c) {
      throw Object.assign(new Error('TWILIO_NOT_CONFIGURED'), { code: 'TWILIO_NOT_CONFIGURED' });
    }
    if (!env.TWILIO_FROM_NUMBER && !env.TWILIO_MESSAGING_SERVICE_SID) {
      throw Object.assign(new Error('TWILIO_NO_SENDER'), { code: 'TWILIO_NO_SENDER' });
    }

    try {
      // Retry wrapper for transient errors (3 attempts, exponential backoff)
      const message = await withRetry(
        () =>
          c.messages.create({
            body: payload.body,
            to: payload.to,
            ...(env.TWILIO_MESSAGING_SERVICE_SID
              ? { messagingServiceSid: env.TWILIO_MESSAGING_SERVICE_SID }
              : { from: env.TWILIO_FROM_NUMBER! }),
          }),
        { isRetryable: isTransientTwilioError, maxAttempts: 3, baseDelayMs: 500 },
      );
      logger.info('SMS sent', { traceId, to: payload.to, sid: message.sid });
      return { provider: 'twilio', messageId: message.sid };
    } catch (err: any) {
      logger.error('Twilio send failed (after retries)', { error: err, traceId, to: payload.to });
      throw Object.assign(new Error(err?.message ?? 'TWILIO_SEND_FAILED'), {
        code: err?.code ?? 'TWILIO_SEND_FAILED',
      });
    }
  },
};
```

- [ ] **Step 2: Type-check + commit**

```bash
git add src/core/notifications/channels/sms
git commit -m "feat(notifications): Twilio SMS provider"
```

---

### Task 29: Rewrite SMS channel to call Twilio provider + add cost caps

**Files:**
- Modify: `avy-erp-backend/src/core/notifications/channels/sms.channel.ts`
- Create: `avy-erp-backend/src/core/notifications/channels/sms/caps.ts`

Note: masker was already extended in **Task 6F** to cover SMS + WHATSAPP. No changes needed to the masker here.

- [ ] **Step 1: Create SMS caps helper**

```typescript
// src/core/notifications/channels/sms/caps.ts
import { cacheRedis } from '../../../../config/redis';
import { env } from '../../../../config/env';
import { logger } from '../../../../config/logger';

export interface CapsResult {
  allowed: boolean;
  reason?: 'SMS_TENANT_CAP' | 'SMS_USER_CAP';
}

/**
 * Enforce per-tenant and per-user daily SMS caps via Redis INCR counters.
 * Returns { allowed: false, reason } if either cap is exceeded.
 * 48-hour TTL on counters to cover timezone drift.
 */
export async function checkSmsCaps(companyId: string, userId: string): Promise<CapsResult> {
  const today = new Date().toISOString().slice(0, 10);
  const tenantKey = `notif:sms:daily:${companyId}:${today}`;
  const userKey = `notif:sms:daily:${userId}:${today}`;

  try {
    const tenantCount = await cacheRedis.incr(tenantKey);
    if (tenantCount === 1) await cacheRedis.expire(tenantKey, 48 * 3600);
    if (tenantCount > env.NOTIFICATIONS_SMS_DAILY_CAP_PER_TENANT) {
      logger.warn('SMS tenant daily cap exceeded', { companyId, tenantCount });
      return { allowed: false, reason: 'SMS_TENANT_CAP' };
    }

    const userCount = await cacheRedis.incr(userKey);
    if (userCount === 1) await cacheRedis.expire(userKey, 48 * 3600);
    if (userCount > env.NOTIFICATIONS_SMS_DAILY_CAP_PER_USER) {
      logger.warn('SMS user daily cap exceeded', { userId, userCount });
      return { allowed: false, reason: 'SMS_USER_CAP' };
    }

    return { allowed: true };
  } catch (err) {
    logger.warn('SMS caps check failed (fail-open)', { error: err });
    return { allowed: true };
  }
}
```

- [ ] **Step 2: Rewrite `sms.channel.ts` with caps check**

```typescript
import { platformPrisma } from '../../../config/database';
import { twilioProvider } from './sms/twilio.provider';
import { checkSmsCaps } from './sms/caps';
import { maskForChannel } from '../templates/masker';
import type { ChannelSendArgs, ChannelSendResult } from './channel-router';

function normalizeToE164(phone: string): string {
  if (phone.startsWith('+')) return phone;
  // Default country code: India (+91). Adjust for other regions as needed.
  return `+91${phone.replace(/\D/g, '')}`;
}

export const smsChannel = {
  async send({ notificationId, userId, traceId, priority }: ChannelSendArgs): Promise<ChannelSendResult> {
    const notif = await platformPrisma.notification.findUniqueOrThrow({ where: { id: notificationId } });
    const user = await platformPrisma.user.findUniqueOrThrow({ where: { id: userId } });

    if (!user.phone) {
      throw Object.assign(new Error('NO_USER_PHONE'), { code: 'NO_USER_PHONE' });
    }

    // 1. Cost caps check (spec §4A.4) — before hitting Twilio
    const caps = await checkSmsCaps(notif.companyId, userId);
    if (!caps.allowed) {
      throw Object.assign(new Error(caps.reason ?? 'SMS_CAP_HIT'), { code: caps.reason ?? 'SMS_CAP_HIT' });
    }

    const template = notif.templateId
      ? await platformPrisma.notificationTemplate.findUnique({ where: { id: notif.templateId } })
      : null;
    const sensitiveFields = (template?.sensitiveFields as string[] | null) ?? [];

    // 2. Masking (already extended for SMS in Task 6F)
    const masked = maskForChannel(
      'SMS',
      {
        title: notif.title,
        body: notif.body,
        data: (notif.data as Record<string, unknown> | null) ?? undefined,
      },
      sensitiveFields,
    );

    const to = normalizeToE164(user.phone);
    const smsBody = `${masked.title}: ${masked.body}`.slice(0, 1600); // SMS hard limit

    // 3. Provider call (retry wrapped internally)
    const result = await twilioProvider.send({ to, body: smsBody, priority }, traceId);

    return { provider: 'twilio', messageId: result.messageId };
  },
};
```

- [ ] **Step 3: Type-check + commit**

```bash
git add src/core/notifications/channels/sms src/core/notifications/channels/sms.channel.ts
git commit -m "feat(notifications): SMS channel with Twilio provider, cost caps, masking, retry"
```

---

### Task 30: Twilio provider unit tests

**Files:**
- Create: `avy-erp-backend/src/core/notifications/__tests__/twilio-provider.test.ts`

- [ ] **Step 1: Write tests covering**

- `TWILIO_NOT_CONFIGURED` when SID/token missing
- `TWILIO_NO_SENDER` when from number + service SID both missing
- `SMS_DISABLED` when kill switch off
- Happy path: returns `{ provider: 'twilio', messageId }`
- Twilio API error: wraps with code
- E.164 normalization (via SMS channel test)

Mock the `twilio` package via Jest.

- [ ] **Step 2: Commit**

---

## Phase 7: WhatsApp provider (Meta Cloud)

### Task 31: Meta Cloud provider + WhatsApp channel with enforced template + caps + retry

**Files:**
- Create: `avy-erp-backend/src/core/notifications/channels/whatsapp/meta-cloud.provider.ts`
- Create: `avy-erp-backend/src/core/notifications/channels/whatsapp/caps.ts`
- Modify: `avy-erp-backend/src/core/notifications/channels/whatsapp.channel.ts`

- [ ] **Step 1: Create WhatsApp caps helper** (same pattern as SMS caps)

```typescript
// src/core/notifications/channels/whatsapp/caps.ts
import { cacheRedis } from '../../../../config/redis';
import { env } from '../../../../config/env';
import { logger } from '../../../../config/logger';

export interface CapsResult {
  allowed: boolean;
  reason?: 'WHATSAPP_TENANT_CAP' | 'WHATSAPP_USER_CAP';
}

export async function checkWhatsappCaps(companyId: string, userId: string): Promise<CapsResult> {
  const today = new Date().toISOString().slice(0, 10);
  const tenantKey = `notif:whatsapp:daily:${companyId}:${today}`;
  const userKey = `notif:whatsapp:daily:${userId}:${today}`;

  try {
    const tenantCount = await cacheRedis.incr(tenantKey);
    if (tenantCount === 1) await cacheRedis.expire(tenantKey, 48 * 3600);
    if (tenantCount > env.NOTIFICATIONS_WHATSAPP_DAILY_CAP_PER_TENANT) {
      logger.warn('WhatsApp tenant daily cap exceeded', { companyId, tenantCount });
      return { allowed: false, reason: 'WHATSAPP_TENANT_CAP' };
    }

    const userCount = await cacheRedis.incr(userKey);
    if (userCount === 1) await cacheRedis.expire(userKey, 48 * 3600);
    if (userCount > env.NOTIFICATIONS_WHATSAPP_DAILY_CAP_PER_USER) {
      logger.warn('WhatsApp user daily cap exceeded', { userId, userCount });
      return { allowed: false, reason: 'WHATSAPP_USER_CAP' };
    }

    return { allowed: true };
  } catch (err) {
    logger.warn('WhatsApp caps check failed (fail-open)', { error: err });
    return { allowed: true };
  }
}
```

- [ ] **Step 2: Create the Meta Cloud provider with retry + dry-run**

```typescript
// src/core/notifications/channels/whatsapp/meta-cloud.provider.ts
import { env } from '../../../../config/env';
import { logger } from '../../../../config/logger';
import { withRetry } from '../provider-retry';

export interface MetaCloudPayload {
  to: string;
  body: string;
  templateName: string; // REQUIRED — enforced at channel level
}

export interface MetaCloudResult {
  provider: 'meta-cloud';
  messageId: string | null;
}

/** Transient errors worth retrying: 5xx, 429 rate limit, connection errors. */
function isTransientMetaError(err: unknown): boolean {
  const e = err as { status?: number; code?: string };
  if (e.status && e.status >= 500) return true;
  if (e.status === 429) return true;
  if (e.code === 'ECONNRESET' || e.code === 'ETIMEDOUT') return true;
  return false;
}

export const metaCloudProvider = {
  async send(payload: MetaCloudPayload, traceId: string): Promise<MetaCloudResult> {
    if (!env.NOTIFICATIONS_WHATSAPP_ENABLED) {
      throw Object.assign(new Error('WHATSAPP_DISABLED'), { code: 'WHATSAPP_DISABLED' });
    }

    if (env.NOTIFICATIONS_WHATSAPP_DRY_RUN) {
      logger.info('[DRY-RUN] WhatsApp would have been sent', {
        traceId,
        to: payload.to,
        templateName: payload.templateName,
        body: payload.body,
      });
      return { provider: 'meta-cloud', messageId: 'dry-run' };
    }

    if (!env.META_WHATSAPP_PHONE_NUMBER_ID || !env.META_WHATSAPP_ACCESS_TOKEN) {
      throw Object.assign(new Error('WHATSAPP_NOT_CONFIGURED'), { code: 'WHATSAPP_NOT_CONFIGURED' });
    }

    const url = `https://graph.facebook.com/${env.META_WHATSAPP_API_VERSION}/${env.META_WHATSAPP_PHONE_NUMBER_ID}/messages`;

    const body = {
      messaging_product: 'whatsapp',
      to: payload.to.replace(/^\+/, ''),
      type: 'template',
      template: {
        name: payload.templateName,
        language: { code: 'en_US' },
        components: [
          {
            type: 'body',
            parameters: [{ type: 'text', text: payload.body }],
          },
        ],
      },
    };

    try {
      const json = await withRetry(
        async () => {
          const res = await fetch(url, {
            method: 'POST',
            headers: {
              Authorization: `Bearer ${env.META_WHATSAPP_ACCESS_TOKEN}`,
              'Content-Type': 'application/json',
            },
            body: JSON.stringify(body),
          });
          if (!res.ok) {
            const errText = await res.text();
            const err: any = new Error(`Meta Cloud API error ${res.status}: ${errText}`);
            err.status = res.status;
            throw err;
          }
          return (await res.json()) as { messages?: Array<{ id?: string }> };
        },
        { isRetryable: isTransientMetaError, maxAttempts: 3, baseDelayMs: 500 },
      );
      const messageId = json.messages?.[0]?.id ?? null;
      logger.info('WhatsApp sent', { traceId, to: payload.to, messageId });
      return { provider: 'meta-cloud', messageId };
    } catch (err: any) {
      logger.error('Meta Cloud send failed (after retries)', { error: err, traceId });
      throw Object.assign(new Error(err?.message ?? 'META_SEND_FAILED'), { code: 'META_SEND_FAILED' });
    }
  },
};
```

- [ ] **Step 3: Rewrite `whatsapp.channel.ts` with enforced template + caps + masking**

```typescript
import { platformPrisma } from '../../../config/database';
import { metaCloudProvider } from './whatsapp/meta-cloud.provider';
import { checkWhatsappCaps } from './whatsapp/caps';
import { maskForChannel } from '../templates/masker';
import type { ChannelSendArgs, ChannelSendResult } from './channel-router';

function normalizeToE164(phone: string): string {
  if (phone.startsWith('+')) return phone;
  return `+91${phone.replace(/\D/g, '')}`;
}

export const whatsappChannel = {
  async send({ notificationId, userId, traceId }: ChannelSendArgs): Promise<ChannelSendResult> {
    const notif = await platformPrisma.notification.findUniqueOrThrow({ where: { id: notificationId } });
    const user = await platformPrisma.user.findUniqueOrThrow({ where: { id: userId } });

    if (!user.phone) {
      throw Object.assign(new Error('NO_USER_PHONE'), { code: 'NO_USER_PHONE' });
    }

    const template = notif.templateId
      ? await platformPrisma.notificationTemplate.findUnique({ where: { id: notif.templateId } })
      : null;

    // 1. ENFORCE template requirement (spec §4A.5) — Meta rejects free-form text outside 24h session window
    if (!template?.whatsappTemplateName) {
      throw Object.assign(
        new Error('WHATSAPP_TEMPLATE_REQUIRED: A pre-approved Meta Business template name is required'),
        { code: 'WHATSAPP_TEMPLATE_REQUIRED' },
      );
    }

    // 2. Cost caps
    const caps = await checkWhatsappCaps(notif.companyId, userId);
    if (!caps.allowed) {
      throw Object.assign(new Error(caps.reason ?? 'WHATSAPP_CAP_HIT'), { code: caps.reason ?? 'WHATSAPP_CAP_HIT' });
    }

    // 3. Masking
    const sensitiveFields = (template.sensitiveFields as string[] | null) ?? [];
    const masked = maskForChannel(
      'WHATSAPP',
      {
        title: notif.title,
        body: notif.body,
        data: (notif.data as Record<string, unknown> | null) ?? undefined,
      },
      sensitiveFields,
    );

    const to = normalizeToE164(user.phone);
    const bodyText = `${masked.title}\n\n${masked.body}`;

    // 4. Provider call (retry wrapped internally)
    const result = await metaCloudProvider.send(
      { to, body: bodyText, templateName: template.whatsappTemplateName },
      traceId,
    );
    return { provider: 'meta-cloud', messageId: result.messageId };
  },
};
```

- [ ] **Step 4: Add Zod `.refine()` to `createNotificationTemplateSchema` to enforce whatsappTemplateName for WHATSAPP channel**

In `ess.validators.ts` find `createNotificationTemplateSchema` and add:

```typescript
.refine(
  (data) => data.channel !== 'WHATSAPP' || !!data.whatsappTemplateName,
  { message: 'whatsappTemplateName is required when channel is WHATSAPP', path: ['whatsappTemplateName'] },
);
```

Also add `whatsappTemplateName: z.string().optional()` to the base schema.

- [ ] **Step 5: Type-check + commit**

```bash
git add src/core/notifications/channels/whatsapp src/core/notifications/channels/whatsapp.channel.ts src/modules/hr/ess/ess.validators.ts
git commit -m "feat(notifications): WhatsApp Meta Cloud provider with enforced template, caps, retry, masking"
```

---

### Task 32: Expose `whatsappTemplateName` in admin UI

**Files:**
- Modify: `web-system-app/src/features/company-admin/hr/NotificationTemplateScreen.tsx`
- Modify: `web-system-app/src/lib/api/ess.ts` (if template type is defined there)

- [ ] **Step 1: Extend the template form with a `whatsappTemplateName` text input**

Visible only when the template's channel is `WHATSAPP`.

- [ ] **Step 2: Wire into the save mutation**

- [ ] **Step 3: Commit**

```bash
cd web-system-app
git add src/features/company-admin src/lib/api/ess.ts
git commit -m "feat(notifications): admin UI for whatsappTemplateName field"
```

---

### Task 33: Meta Cloud provider unit tests

**Files:**
- Create: `avy-erp-backend/src/core/notifications/__tests__/meta-cloud-provider.test.ts`

- [ ] **Step 1: Tests covering configured/not-configured, text mode, template mode, error mapping**

- [ ] **Step 2: Commit**

---

## Phase 8: Per-category user preferences

### Task 34: Extend consent gate with category check

**Files:**
- Modify: `avy-erp-backend/src/core/notifications/dispatch/consent-gate.ts`

- [ ] **Step 1: Extend `ConsentCache` interface**

```typescript
export interface ConsentCache {
  userId: string;
  companySettings: CompanySettings | null;
  preference: UserNotificationPreference | null;
  categoryPrefs: Map<string, boolean>; // key = `${category}:${channel}`
}
```

- [ ] **Step 2: Extend `loadConsentCache` to fetch category prefs**

```typescript
const [companySettings, preference, catPrefs] = await Promise.all([
  platformPrisma.companySettings.findFirst({ where: { companyId: user.companyId } }),
  platformPrisma.userNotificationPreference.findUnique({ where: { userId } }),
  platformPrisma.userNotificationCategoryPreference.findMany({
    where: { userId },
    select: { category: true, channel: true, enabled: true },
  }),
]);

const categoryPrefs = new Map<string, boolean>();
for (const p of catPrefs) {
  categoryPrefs.set(`${p.category}:${p.channel}`, p.enabled);
}

return { userId, companySettings, preference, categoryPrefs };
```

- [ ] **Step 3: Extend `evaluateConsent` to check category (with locked category bypass)**

```typescript
import { isCategoryLocked } from '../../../shared/constants/notification-categories';

export function evaluateConsent(
  cache: ConsentCache,
  channel: NotificationChannel,
  priority: NotificationPriority,
  category: string | null,
  systemCritical = false,
): ConsentResult {
  if (channel === 'IN_APP') return { allowed: true };

  // ... existing company master check ...
  // ... existing systemCritical bypass ...
  // ... existing user pref check ...

  // NEW: category preference check (only applies if not locked and a row exists)
  if (category && !isCategoryLocked(category)) {
    const key = `${category}:${channel}`;
    const catEnabled = cache.categoryPrefs.get(key);
    if (catEnabled === false) {
      return { allowed: false, reason: 'CATEGORY_PREF_OFF' };
    }
  }

  // ... existing quiet hours check ...
  return { allowed: true };
}
```

- [ ] **Step 4: Update the worker to pass `category` to `evaluateConsent`**

In `notification.worker.ts`, extract the category from the job payload:

```typescript
const category = (job.data.category as string | undefined) ?? null;
// ...
const consent = evaluateConsent(consentCache, channel, priority, category, systemCritical);
```

And ensure the dispatcher's `enqueue.ts` passes category in the payload (it does already — verify in `dispatcher.ts` line that builds QueueablePayload).

- [ ] **Step 5: Type-check + commit**

```bash
git add src/core/notifications
git commit -m "feat(notifications): category preference check in consent gate"
```

---

### Task 35: Preferences API — category CRUD

**Files:**
- Modify: `avy-erp-backend/src/core/notifications/preferences/preferences.service.ts`
- Modify: `avy-erp-backend/src/core/notifications/preferences/preferences.validators.ts`
- Modify: `avy-erp-backend/src/core/notifications/notification.controller.ts`

- [ ] **Step 1: Extend `getForUser` response to include category prefs + catalogue**

```typescript
async getForUser(userId: string) {
  // ... existing logic ...
  const categoryPrefs = await platformPrisma.userNotificationCategoryPreference.findMany({
    where: { userId },
    select: { category: true, channel: true, enabled: true },
  });

  return {
    preference: pref,
    companyMasters: {
      // ... existing ...
    },
    categoryPreferences: categoryPrefs,
    categoryCatalogue: NOTIFICATION_CATEGORIES,
  };
}
```

- [ ] **Step 2: Add `updateCategoryPreferences` method**

```typescript
async updateCategoryPreferences(
  userId: string,
  updates: Array<{ category: string; channel: NotificationChannel; enabled: boolean }>,
) {
  // Reject updates to locked categories
  for (const u of updates) {
    if (isCategoryLocked(u.category)) {
      throw ApiError.badRequest(`Category ${u.category} is locked and cannot be modified`);
    }
  }

  await platformPrisma.$transaction(
    updates.map((u) =>
      platformPrisma.userNotificationCategoryPreference.upsert({
        where: { userId_category_channel: { userId, category: u.category, channel: u.channel } },
        create: { userId, category: u.category, channel: u.channel, enabled: u.enabled },
        update: { enabled: u.enabled },
      }),
    ),
  );

  return this.getForUser(userId);
}
```

- [ ] **Step 3: Add validator + controller method**

```typescript
// preferences.validators.ts
export const updateCategoryPreferencesSchema = z.object({
  categoryPreferences: z.array(z.object({
    category: z.string().min(1),
    channel: z.enum(['IN_APP', 'PUSH', 'EMAIL', 'SMS', 'WHATSAPP']),
    enabled: z.boolean(),
  })).min(1),
});
```

Add controller method and a new route `PATCH /notifications/preferences/categories`.

- [ ] **Step 4: Commit**

```bash
git add src/core/notifications
git commit -m "feat(notifications): category preference CRUD API"
```

---

### Task 36: Web preferences screen — category section

**Files:**
- Modify: `web-system-app/src/features/settings/NotificationPreferencesScreen.tsx`
- Modify: `web-system-app/src/lib/api/notifications.ts`

- [ ] **Step 1: Extend `NotificationPreferencesResponse` type with `categoryPreferences` and `categoryCatalogue`**

- [ ] **Step 2: Add category mutation method to `notificationApi`**

```typescript
updateCategoryPreferences: (categoryPreferences: Array<{ category: string; channel: string; enabled: boolean }>) =>
  client.patch('/notifications/preferences/categories', { categoryPreferences }).then((r) => r.data),
```

- [ ] **Step 3: Render a collapsible "Fine-tune by category" section below the existing channels list**

A table where rows are categories (from `categoryCatalogue`) and columns are the 4 user-facing channels. Locked categories (`AUTH`) are rendered dimmed with a lock icon.

- [ ] **Step 4: Optimistic update + rollback matching the existing pattern**

- [ ] **Step 5: Commit**

---

### Task 37: Mobile preferences screen — category section

**Files:**
- Modify: `mobile-app/src/features/settings/notification-preferences-screen.tsx`
- Modify: `mobile-app/src/lib/api/notifications.ts`

- [ ] **Step 1: Mirror the web changes**

Use `ScrollView` + collapsible sections. Each category is a row with 4 `Switch` components.

- [ ] **Step 2: Lock icon for `AUTH` category using `Lock` from `lucide-react-native`**

- [ ] **Step 3: Commit**

---

### Task 38: Category prefs integration test

**Files:**
- Create: `avy-erp-backend/src/__tests__/integration/notifications/category-prefs.test.ts`

- [ ] **Step 1: Test that toggling `PAYROLL/PUSH` off prevents push delivery for a payroll notification**

- [ ] **Step 2: Test that `AUTH` category cannot be modified via API (400)**

- [ ] **Step 3: Test that locked categories still deliver even when user pref is set to disabled**

- [ ] **Step 4: Commit**

---

## Phase 9: Tenant onboarding Step 5

### Task 39: Web — extend Step05Preferences

**Files:**
- Modify: `web-system-app/src/features/super-admin/tenant-onboarding/steps/Step05Preferences.tsx`
- Modify: `web-system-app/src/features/super-admin/tenant-onboarding/schemas.ts` (or wherever Zod schema lives)
- Modify: `web-system-app/src/features/super-admin/tenant-onboarding/index.tsx` (for payload wiring)

- [ ] **Step 1: Add three new fields to the Zod schema**

```typescript
pushNotif: z.boolean(),
smsNotif: z.boolean(),
inAppNotif: z.boolean(),
```

- [ ] **Step 2: Add three new `ToggleRow` components in the render block**

Following the existing pattern for `emailNotif`.

- [ ] **Step 3: Wire into the tenant creation payload**

In the index.tsx where the final payload is built, add:

```typescript
pushNotifications: step5.pushNotif,
smsNotifications: step5.smsNotif,
inAppNotifications: step5.inAppNotif,
```

- [ ] **Step 4: Commit**

```bash
git add src/features/super-admin/tenant-onboarding
git commit -m "feat(notifications): onboarding wizard Step 5 — push/sms/in-app toggles"
```

---

### Task 40: Backend — propagate onboarding toggles to CompanySettings

**Files:**
- Modify: `avy-erp-backend/src/core/tenant/tenant.service.ts` (or wherever `createTenant` lives)

- [ ] **Step 1: Read the three new fields from the request body**

- [ ] **Step 2: Pass them to `CompanySettings.create` when the tenant is provisioned**

- [ ] **Step 3: Commit**

---

## Phase 10: Analytics dashboard

### Task 41: Backend — analytics service

**Files:**
- Create: `avy-erp-backend/src/core/notifications/analytics/notification-analytics.service.ts`

- [ ] **Step 1: Implement `getSummary`, `getTopFailing`, `getDeliveryTrend`**

Use Prisma groupBy / aggregate / raw SQL as appropriate. See spec §11.1 for the response shape.

- [ ] **Step 2: Commit**

---

### Task 42: Backend — analytics controller + routes

**Files:**
- Create: `avy-erp-backend/src/core/notifications/analytics/notification-analytics.controller.ts`
- Create: `avy-erp-backend/src/core/notifications/analytics/notification-analytics.routes.ts`
- Modify: `avy-erp-backend/src/core/notifications/notification.routes.ts` (mount new routes)

- [ ] **Step 1: Create controller with 3 endpoints guarded by `hr:configure` permission**

- [ ] **Step 2: Mount under `/notifications/analytics`**

- [ ] **Step 3: Commit**

---

### Task 43: Web — analytics screen

**Files:**
- Create: `web-system-app/src/features/company-admin/hr/NotificationAnalyticsScreen.tsx`
- Create: `web-system-app/src/features/company-admin/hr/api/use-notification-analytics.ts`
- Modify: `web-system-app/src/App.tsx`

- [ ] **Step 1: Create React Query hooks**

- [ ] **Step 2: Create the screen with 4 KPI cards + 2 donuts + 1 time-series chart + 1 failing-templates table**

Reuse chart primitives from `src/features/analytics/` or install `recharts` if not already present.

- [ ] **Step 3: Register the route in `App.tsx`**

- [ ] **Step 4: Commit**

---

### Task 44: Navigation manifest entry for analytics

**Files:**
- Modify: `avy-erp-backend/src/shared/constants/navigation-manifest.ts`

- [ ] **Step 1: Add manifest entry**

```typescript
{
  id: 'hr-notification-analytics',
  label: 'Notification Analytics',
  icon: 'bar-chart-2',
  requiredPerm: 'hr:configure',
  path: '/app/company/hr/notification-analytics',
  module: 'hr',
  group: 'HR Configuration',
  roleScope: 'company',
  sortOrder: 499,
},
```

- [ ] **Step 2: Commit**

---

## Phase 11: Tests

### Task 45: Unit tests — dispatcher + dedup + consent

**Files:**
- Create: `avy-erp-backend/src/core/notifications/__tests__/dispatcher.test.ts`
- Create: `avy-erp-backend/src/core/notifications/__tests__/dedup.test.ts`
- Create: `avy-erp-backend/src/core/notifications/__tests__/consent-gate.test.ts`

- [ ] **Step 1: Write tests following the checklist in spec §13.1**

- [ ] **Step 2: Run**

```bash
pnpm test src/core/notifications/__tests__
```

- [ ] **Step 3: Commit**

---

### Task 46: Unit tests — templates + idempotency + backpressure

**Files:**
- Create: `avy-erp-backend/src/core/notifications/__tests__/template-compiler.test.ts`
- Create: `avy-erp-backend/src/core/notifications/__tests__/renderer.test.ts`
- Create: `avy-erp-backend/src/core/notifications/__tests__/masker.test.ts`
- Create: `avy-erp-backend/src/core/notifications/__tests__/idempotency.test.ts`
- Create: `avy-erp-backend/src/core/notifications/__tests__/backpressure.test.ts`
- Create: `avy-erp-backend/src/core/notifications/__tests__/batcher.test.ts`
- Create: `avy-erp-backend/src/core/notifications/__tests__/rule-loader.test.ts`
- Create: `avy-erp-backend/src/core/notifications/__tests__/recipient-resolver.test.ts`

- [ ] **Step 1: Write the test files per spec §13.1**

- [ ] **Step 2: Commit**

---

### Task 47: Unit tests — providers (Expo, FCM, Twilio, Meta Cloud)

**Files:**
- Create: `avy-erp-backend/src/core/notifications/__tests__/expo-provider.test.ts`
- Create: `avy-erp-backend/src/core/notifications/__tests__/fcm-provider.test.ts`
- Create: `avy-erp-backend/src/core/notifications/__tests__/push-channel.test.ts`

- [ ] **Step 1: Mock Expo SDK and firebase-admin**

- [ ] **Step 2: Tests cover chunking, dead tokens, failure counting, multi-provider routing**

- [ ] **Step 3: Commit**

---

### Task 48: Unit tests — cron service + operational safeguards

**Files:**
- Create: `avy-erp-backend/src/core/notifications/__tests__/notification-cron.test.ts`
- Create: `avy-erp-backend/src/core/notifications/__tests__/dispatch-bulk.test.ts`
- Create: `avy-erp-backend/src/core/notifications/__tests__/rate-limiter.test.ts`
- Create: `avy-erp-backend/src/core/notifications/__tests__/consent-cache.test.ts`
- Create: `avy-erp-backend/src/core/notifications/__tests__/sms-caps.test.ts`
- Create: `avy-erp-backend/src/core/notifications/__tests__/whatsapp-template-enforcement.test.ts`
- Create: `avy-erp-backend/src/core/notifications/__tests__/provider-retry.test.ts`
- Create: `avy-erp-backend/src/core/notifications/__tests__/event-retention.test.ts`

- [ ] **Step 1: Cron tests** — Mock DateTime.now() + Prisma to simulate today being a birthday. Verify dispatch called with correct trigger + tokens. Verify cron dedup prevents double-fire. Verify cursor pagination iterates all batches. Verify Promise.allSettled doesn't let one company's failure stop others.

- [ ] **Step 2: dispatchBulk tests** — chunking to `chunkSize`; single rule load across all recipients; per-recipient token merging with `sharedTokens`; rate limit filtering; fallback to per-recipient when no rules.

- [ ] **Step 3: Rate limiter tests** — counter increments; expires at 60s; exceeds limit returns false; CRITICAL priority bypasses; Redis down fail-open returns true.

- [ ] **Step 4: Consent cache tests** — read-through cache hit returns parsed data; cache miss → DB + write-through; invalidation deletes key; Map rehydration from serialized JSON; TTL is 300s.

- [ ] **Step 5: SMS caps tests** — per-tenant cap INCR + reject at +1; per-user cap independently; TTL 48h; dry-run mode bypasses provider.

- [ ] **Step 6: WhatsApp template enforcement tests** — throws `WHATSAPP_TEMPLATE_REQUIRED` when missing; passes with template name set; masker applied to SMS + WHATSAPP + PUSH consistently.

- [ ] **Step 7: Provider retry tests** — 3 attempts with exponential backoff; non-retryable errors throw immediately; auth errors do not retry.

- [ ] **Step 8: Event retention tests** — deletes events older than retention window in batches; aggregation runs before cleanup; idempotent upsert into `NotificationEventAggregateDaily`.

- [ ] **Step 9: Commit**

---

### Task 49: Integration tests — end-to-end delivery

**Files:**
- Create: `avy-erp-backend/src/__tests__/integration/notifications/dispatch-end-to-end.test.ts`
- Create: `avy-erp-backend/src/__tests__/integration/notifications/consent-enforcement.test.ts`
- Create: `avy-erp-backend/src/__tests__/integration/notifications/approval-workflow.test.ts`

- [ ] **Step 1: Spin up testcontainers Postgres + Redis**

- [ ] **Step 2: Seed minimal data, call dispatch, assert DB state**

- [ ] **Step 3: Commit**

---

### Task 50: Load test script

**Files:**
- Create: `avy-erp-backend/scripts/load-test-notifications.ts`

- [ ] **Step 1: Script that dispatches 10k notifications over 60s**

Measures p50/p95 dispatcher latency via `console.time`, queue depth via `notifQueueDefault.getWaitingCount()`, final `NotificationEvent` count.

- [ ] **Step 2: Document pass criteria in the file header**

- [ ] **Step 3: Commit**

---

### Task 51: Manual QA pass

- [ ] **Step 1: Run the 19-step checklist from `feat/notifications` spec §10.6**

Plus the 4 new items:
- Category preference toggle (mute PAYROLL/PUSH, verify it's suppressed)
- SMS delivery (test Twilio account)
- WhatsApp delivery (test Meta number, fallback to email if no template)
- Cron birthday (fast-forward date or seed employee with today's dateOfBirth, run cron manually, verify notification)
- Analytics dashboard chart rendering

- [ ] **Step 2: File bugs as follow-up tasks if any**

---

## Phase 12: Mobile polish + final

### Task 52: Replace notification icon placeholder

**Files:**
- Create: `mobile-app/assets/notification-icon-96.png` (96×96 monochrome white-on-transparent PNG)
- Modify: `mobile-app/app.config.ts`

- [ ] **Step 1: Generate or obtain a proper notification icon**

Requirements:
- 96×96 pixels
- Monochrome (white silhouette on transparent background)
- Represents a notification bell or the company logo simplified
- No text, no gradient

If no designed asset is available, use `lucide-react` to generate a bell icon SVG → convert to PNG via ImageMagick:

```bash
# If lucide-react is not installed, use any bell SVG
curl -s https://raw.githubusercontent.com/lucide-icons/lucide/main/icons/bell.svg > /tmp/bell.svg
# Convert SVG to 96x96 white PNG on transparent bg
# (Requires rsvg-convert or imagemagick)
rsvg-convert -w 96 -h 96 /tmp/bell.svg > mobile-app/assets/notification-icon-96.png
```

If tooling is unavailable, the placeholder stays until a designer provides the asset — document it as a follow-up.

- [ ] **Step 2: Update `app.config.ts` to reference the new icon**

```typescript
[
  'expo-notifications',
  {
    icon: './assets/notification-icon-96.png',
    color: '#4F46E5',
    mode: 'production',
  },
],
```

- [ ] **Step 3: Commit**

```bash
cd mobile-app
git add assets/notification-icon-96.png app.config.ts
git commit -m "feat(notifications): replace placeholder with proper 96x96 notification icon"
```

---

### Task 53: Drop `Notification.isRead` (Phase A — mark deprecated)

**Files:**
- Modify: `avy-erp-backend/prisma/modules/platform/notifications.prisma`

- [ ] **Step 1: Add a `@deprecated` comment above `isRead`**

```prisma
  /// @deprecated Use `status` instead. Will be removed in a follow-up PR.
  isRead          Boolean              @default(false)
```

- [ ] **Step 2: Audit all code paths that still write to `isRead`**

```bash
grep -rn "isRead" src/core/notifications src/modules
```

- [ ] **Step 3: Ensure every write also updates `status` consistently**

- [ ] **Step 4: Commit**

```bash
git add prisma/modules/platform/notifications.prisma
git commit -m "chore(notifications): mark Notification.isRead as deprecated (Phase A)"
```

**Phase B (actual column drop) is deferred to a follow-up PR once this branch is in prod for 2+ weeks.**

---

### Task 54: Final full type-check across all 3 codebases

- [ ] **Step 1: Backend**

```bash
cd avy-erp-backend && pnpm tsc --noEmit
```

Expected: clean.

- [ ] **Step 2: Web**

```bash
cd ../web-system-app && pnpm tsc --noEmit
```

Expected: clean.

- [ ] **Step 3: Mobile**

```bash
cd ../mobile-app && pnpm type-check
```

Expected: clean (including the pre-existing leave-request fix from Task 2).

- [ ] **Step 4: Run all tests**

```bash
cd ../avy-erp-backend && pnpm test
```

Expected: all green.

- [ ] **Step 5: Lint**

```bash
pnpm lint
cd ../web-system-app && pnpm lint
cd ../mobile-app && pnpm lint
```

Expected: no new warnings.

---

### Task 55: Commit root submodule pointers + finalize

- [ ] **Step 1: Root repo — add + commit submodule pointer updates**

```bash
cd /Users/chetan/Documents/Avyren-Technologies/Products/Mobile-ERP
git status --short
git add avy-erp-backend web-system-app mobile-app
git commit -m "chore: update submodule pointers after per-module notifications completion"
```

- [ ] **Step 2: Final git log summary**

```bash
cd avy-erp-backend && git log --oneline feat/per-module-notifications -50 | head -40
cd ../web-system-app && git log --oneline feat/per-module-notifications -20
cd ../mobile-app && git log --oneline feat/per-module-notifications -20
cd .. && git log --oneline main -5
```

- [ ] **Step 3: Verify nothing is pushed** (per git safety policy — user pushes manually)

---

## Self-Review

**Spec coverage:** every item in the spec's §2.2 deferred items table AND every operational safeguard in §4A is addressed by at least one task:

- [x] Per-module dispatch call sites → Phases 2-4 (Tasks 7-21)
- [x] SMS provider → Phase 6 (Tasks 28-30) — **with retry, caps, dry-run, masking**
- [x] WhatsApp provider → Phase 7 (Tasks 31-33) — **with enforced template, caps, retry, masking**
- [x] Tenant onboarding Step05 → Phase 9 (Tasks 39-40)
- [x] Analytics dashboard → Phase 10 (Tasks 41-44) — **reads from pre-aggregated table**
- [x] Per-category user preferences → Phase 8 (Tasks 34-38) — **with "Mute all" convenience**
- [x] Unit + integration tests → Phase 11 (Tasks 45-51) — **includes safeguards tests**
- [x] Prisma migration file → Phase 1 (Task 1)
- [x] Mobile notification icon → Phase 12 (Task 52)
- [x] Drop `Notification.isRead` (Phase A) → Phase 12 (Task 53)
- [x] Pre-existing mobile type error → Phase 1 (Task 2)
- [x] Informational cron events → Phase 5 (Tasks 22-27) — **with cursor pagination + Promise.allSettled**
- [x] Rule cache invalidation → Phase 2 (Task 16)
- [x] Reviewer residual nits → Phase 1 (Task 6)

**Operational safeguards (spec §4A):**

- [x] Per-user rate limiter → Phase 1A (Task 6B)
- [x] Bulk dispatch utility → Phase 1A (Task 6D)
- [x] Consent cache layer → Phase 1A (Task 6C)
- [x] SMS daily caps → Phase 6 (Task 29)
- [x] WhatsApp template enforcement → Phase 7 (Task 31)
- [x] Provider retry wrapper → Phase 1A (Task 6E)
- [x] SMS + WhatsApp masking parity → Phase 1A (Task 6F)
- [x] Pre-aggregation table schema → Phase 1A (Task 6G)
- [x] Aggregation + retention crons → Phase 5 (Task 26A)
- [x] Cron pagination helper → Phase 1A (Task 6H)
- [x] Approval handler per-case try/catch → Phase 2 (Task 11)
- [x] Payroll bulk dispatch → Phase 3 (Task 12)
- [x] Cron cursor pagination + Promise.allSettled → Phase 5 (Task 23)
- [x] Category "Mute all" toggle → Phase 8 (Task 36)

**Placeholder scan:** no TBDs, TODOs, or "TODO: implement later" stubs. Every step has either complete code or an exact reference to a spec section with code.

**Type consistency:**
- `notificationService.dispatch()` signature is consistent across all call sites
- `RecipientBucket`, `DispatchInput`, `ConsentCache` types are defined once and reused
- All service imports use relative paths per backend convention (`feedback_no_path_aliases_backend.md`)

**Phased dependency:** Phase 1 is foundational (no dependencies). Phases 2-4 depend only on Phase 1. Phase 5 is independent of Phases 2-4 (crons don't need the wiring done). Phases 6-7 are independent of everything else. Phase 8 depends on Phase 1 schema. Phase 9 depends on Phase 1 env vars. Phase 10 depends on Phase 1 schema + some data to aggregate. Phase 11 tests depend on the code they test. Phase 12 is final polish.

**Testability:**
- All new code is organized into pure functions where possible (`evaluateConsent` is pure, `loadConsentCache` is async I/O)
- Providers accept injected config via env vars but can be instantiated with mocks in tests
- Cron methods are public class methods that can be called directly from tests (bypassing the cron schedule)

**Rollback safety:**
- `NOTIFICATIONS_ENABLED=false` kill switch remains functional
- New cron jobs have `NOTIFICATIONS_CRON_ENABLED=false` independent kill switch
- SMS/WhatsApp providers throw `*_NOT_CONFIGURED` when env vars missing (worker records FAILED and continues)
- Schema additions are purely additive — no drops, no renames
- Legacy `notificationService.send()` facade is preserved throughout

**Migration safety:** Task 1 generates a proper SQL migration file ready for `prisma migrate deploy` in staging/prod. Dev environments continue to use `db push`.
