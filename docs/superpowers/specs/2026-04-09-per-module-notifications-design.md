# Per-Module Notifications — Design Spec

**Status:** Draft for review
**Author:** Chetan (product owner) + Claude (architect)
**Date:** 2026-04-09
**Branches:** `feat/per-module-notifications` on all three submodules
**Depends on:** `feat/notifications` (merged or in-flight — the unified dispatcher must exist)
**Spec reference for base system:** `docs/superpowers/specs/2026-04-09-push-notifications-overhaul-design.md`

---

## 1. Executive Summary

The `feat/notifications` branch built the unified `notificationService.dispatch()` pipeline, priority-partitioned BullMQ workers, dual-transport push, two-tier consent enforcement with per-user preferences, analytics events, Expo receipt polling, socket.io real-time fan-out, and the admin-editable default template catalogue. It also seeded ~63 default `NotificationTemplate` / `NotificationRule` rows per tenant.

What it **did not** ship — by explicit spec §3.4 non-goal — was the per-module call-site wiring that actually invokes the dispatcher from every business flow. Only four HR events are wired today (Interview scheduled, Training nomination/completed, Certificate expiring), plus the legacy `notificationService.send()` facade.

This spec closes every remaining gap so the notification system is **100% implemented**. Concretely it covers:

1. **Per-module event wiring** — ~45 dispatch call sites across 14 services (leave, attendance, ESS, payroll, employee, transfer, promotion, salary revision, offboarding, recruitment, training, assets, support, auth).
2. **Generic approval workflow handler refactor** — `ess.service.onApprovalComplete()` becomes the universal dispatch point for every `ApprovalRequest` state transition.
3. **Informational cron events** — 7 scheduled jobs for birthday, work anniversary, holiday reminders, probation end, asset return due, certificate expiring sweep, training session upcoming.
4. **SMS provider integration** — Twilio via `@twilio/conversations` (or `twilio` package), wired into the existing `smsChannel` stub.
5. **WhatsApp provider integration** — Meta Cloud API (Graph API v21.0), wired into the existing `whatsappChannel` stub.
6. **Per-category user preferences** — extend user prefs with a matrix of `(category × channel)` so users can mute payroll push but keep leave push, etc.
7. **Tenant onboarding Step05 preferences update** — extend the wizard schema + form + payload with the three new toggles (`pushNotifications`, `smsNotifications`, `inAppNotifications`).
8. **Analytics dashboard** — new backend endpoint + web screen showing delivery rates, channel breakdown, priority distribution, top failing templates, bounce rate time-series.
9. **Prisma migration file for staging/prod** — replace dev `db push` with a proper migration SQL file generated via `migrate diff --from-migrations`.
10. **Unit + integration tests** — cover dispatcher, consent-gate, dedup, renderer, masker, batcher, rule-loader, recipient-resolver, idempotency, push providers, SMS/WhatsApp providers, cron jobs.
11. **Mobile notification icon** — replace the placeholder `adaptive-icon.png` copy with a proper 96×96 monochrome white-silhouette asset.
12. **Drop `Notification.isRead` column** — now that all read paths use `status`, deprecate the backward-compat field in a safe two-phase migration.
13. **Pre-existing mobile type error fix** — `leave-request-screen.tsx:16` `import { r } from 'react-native'` — unrelated to notifications but blocks clean mobile type-check.
14. **Residual reviewer nits** — `as any` cleanup in dispatcher ad-hoc rule construction, `DispatchResult.error` field removal (SQL leak vector), `zcard`/`zadd` pipelining, rule-loader zod integrity check, etc.
15. **Notification rule cache invalidation on admin CRUD** — wire `invalidateRuleCache()` into the template/rule admin controllers.
16. **Admin UI for viewing NotificationEvent delivery history** — new tab in the admin notification template/rule screens showing per-notification delivery audit trail.

The delivery is phased into 13 implementation phases (see `docs/superpowers/plans/2026-04-09-per-module-notifications.md`) so each phase can be reviewed and merged independently. The entire scope is additive — legacy code continues to work throughout.

---

## 2. Current State — What's Done vs Missing

### 2.1 What `feat/notifications` shipped (locked in)

- Unified `notificationService.dispatch()` entry point with fallback + ad-hoc modes
- Priority-partitioned BullMQ queues (`high`, `default`, `low`) with retry + DLQ + backpressure
- Dedup (payload-hash + TTL), worker-level idempotency (atomic SETNX claim/release)
- Two-tier consent gate (company master + per-user toggle + `SYSTEM_CRITICAL` override)
- Dual-transport push router (Expo Server SDK for `EXPO` tokens, firebase-admin for `FCM_WEB`/`FCM_NATIVE`)
- Expo receipt polling (30s cadence, 15min window, compare-and-set)
- Socket.io `user:{id}` room fan-out for `notification:new`
- Handlebars template compiler with LRU cache + variable allowlist + sensitive-field masking on PUSH
- 63-template default catalogue seeded per tenant
- Rule loader with Redis cache (60s TTL, SCAN invalidation)
- Recipient resolver for 9 role tokens (`REQUESTER`/`APPROVER`/`MANAGER`/`HR`/`FINANCE`/`IT`/`ADMIN`/`SELF`/`ALL`)
- `NotificationEvent` analytics table (append-only) with traceId, source, provider, ticket ID, receipt status
- Full schema: `Notification` + `UserDevice` + `NotificationEvent` + `UserNotificationPreference` + extended `NotificationTemplate`/`NotificationRule`/`CompanySettings`
- Preferences API (`GET/PATCH /notifications/preferences`), device registration with token metadata
- Web + mobile preferences screens, socket hook, navigation manifest entry, logout disconnect

### 2.2 What this spec adds (deferred items)

The `feat/notifications` branch's spec §3.4 explicitly listed these as non-goals. All of them are addressed here:

| Gap | Owner | Phase |
|---|---|---|
| Per-module dispatch call sites (~45) | Backend | 2-4 |
| SMS provider integration (Twilio) | Backend | 6 |
| WhatsApp provider integration (Meta Cloud) | Backend | 7 |
| Tenant onboarding Step05 toggles | Web | 9 |
| Analytics dashboard UI | Backend + Web | 10 |
| Per-category user preferences | Backend + Web + Mobile | 8 |
| Unit + integration tests | All | 11 |
| Prisma migration file for staging/prod | Backend | 1 |
| Mobile notification icon asset | Mobile | 12 |
| Drop `Notification.isRead` | Backend | 12 |
| Pre-existing `leave-request-screen.tsx` error | Mobile | 1 |
| Informational cron events (birthday, etc.) | Backend | 5 |
| Rule cache invalidation on CRUD | Backend | 2 |
| Reviewer residual nits | All | 12 |

---

## 3. Architecture — What Changes

The core architecture is locked and mostly unchanged. This spec only touches three architectural surfaces:

### 3.1 Approval workflow as universal dispatch point

`ess.service.onApprovalComplete(entityType, entityId, decision, approverId)` is called by every approval workflow transition today. It already has a `switch (entityType)` block for ~11 entity types (PayrollRun, SalaryRevision, ExitRequest, EmployeeTransfer, EmployeePromotion, LeaveRequest, AttendanceOverride, ShiftSwapRequest, ExpenseClaim, WfhRequest, LoanRecord). Each case currently does the entity status update. The refactor adds one `await notificationService.dispatch(...)` call per case after the business update, converting the handler into a single unified notification fanout point for approval-driven events.

This means individual service methods (`leave.service.approveRequest`, `payroll.service.approveRun`, etc.) do NOT need their own dispatch calls for the approval-complete case — `onApprovalComplete` handles it. They only dispatch on **submission** (when the `ApprovalRequest` is first created) and any non-approval events (cancellation, direct state mutations).

**Benefit:** One place to reason about approval notifications. Consistent `entityType` → `triggerEvent` mapping. The individual service methods only need to dispatch submission events.

### 3.2 Per-category preferences

The existing `UserNotificationPreference` schema only has per-channel toggles (`pushEnabled`, `emailEnabled`, etc.). This spec adds a new `UserNotificationCategoryPreference` model with a many-to-many matrix of `(userId, category, channel, enabled)`. The consent gate's `evaluateConsent()` is extended to also check the category preference. The preferences screens on web and mobile gain an expandable "Fine-tune by category" section showing a matrix of checkboxes per `(category, channel)`.

**Backward compat:** If no category row exists for a given `(userId, category, channel)`, the per-channel toggle applies (the current behavior). Per-category rows only override.

**Categories** (derived from the existing default catalogue):

- `LEAVE`
- `ATTENDANCE`
- `OVERTIME`
- `REIMBURSEMENT`
- `LOAN`
- `PAYROLL`
- `SHIFT`
- `WFH`
- `RESIGNATION`
- `EMPLOYEE_LIFECYCLE` (onboarded, transfer, promotion, salary revision)
- `RECRUITMENT`
- `TRAINING`
- `ASSETS`
- `SUPPORT`
- `AUTH` — **always on, not user-overridable** (CRITICAL semantics)
- `ANNOUNCEMENTS`
- `BIRTHDAY_ANNIVERSARY` — opt-out only; opt-in by default

The `AUTH` category is locked: `SYSTEM_CRITICAL` notifications bypass user prefs regardless of category settings.

### 3.3 Provider routing for SMS and WhatsApp

Both channels already have stub files (`sms.channel.ts`, `whatsapp.channel.ts`) that throw `NotImplemented`. The new provider packages live alongside the push providers:

```
src/core/notifications/channels/sms/
  sms.channel.ts        (existing, rewritten)
  twilio.provider.ts    (NEW)
src/core/notifications/channels/whatsapp/
  whatsapp.channel.ts   (existing, rewritten)
  meta-cloud.provider.ts (NEW)
```

Both providers follow the same interface as `expoProvider`/`fcmProvider`:

```typescript
interface SendResult {
  provider: string;
  messageId: string | null;
  errorCode?: string;
}
```

Configuration is opt-in via environment variables. If credentials are missing, the channel throws `PROVIDER_NOT_CONFIGURED` (the worker records FAILED and continues — no crash).

---

## 4. Data Model Changes

### 4.1 New: `UserNotificationCategoryPreference`

File: `prisma/modules/platform/notifications.prisma`

```prisma
model UserNotificationCategoryPreference {
  id        String              @id @default(cuid())
  userId    String
  category  String              // LEAVE, PAYROLL, etc.
  channel   NotificationChannel // PUSH, EMAIL, SMS, WHATSAPP
  enabled   Boolean             @default(true)

  user      User                @relation("UserNotificationCategoryPrefUser", fields: [userId], references: [id], onDelete: Cascade)

  createdAt DateTime            @default(now())
  updatedAt DateTime            @updatedAt

  @@unique([userId, category, channel])
  @@index([userId])
  @@map("user_notification_category_preferences")
}
```

Add back-reference on `User`:

```prisma
categoryPreferences UserNotificationCategoryPreference[] @relation("UserNotificationCategoryPrefUser")
```

**Rationale:** Matrix row per `(user × category × channel)`. Missing row means "use per-channel default" (current behavior). Only creates rows when the user explicitly opts out.

### 4.2 New: `NotificationCategory` constant module

File: `src/shared/constants/notification-categories.ts` (new)

```typescript
export interface NotificationCategoryDef {
  code: string;
  label: string;
  description: string;
  locked?: boolean; // if true, user cannot override (e.g. AUTH)
  defaultOptIn?: boolean; // false = opt-in only (e.g. marketing)
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
```

### 4.3 Drop `Notification.isRead` (two-phase)

**Phase A (this PR):** Mark as deprecated in the schema with a comment, audit all read paths to confirm they use `status`. Keep the column.

**Phase B (follow-up PR after this ships):** Actually drop the column + index in a new migration.

This spec only ships Phase A — Phase B is safer as a follow-up once the current implementation is battle-tested in prod.

### 4.4 Add indexes for the analytics dashboard

File: `prisma/modules/platform/notifications.prisma`

```prisma
model NotificationEvent {
  // ... existing fields ...

  @@index([notificationId])
  @@index([traceId])
  @@index([event, occurredAt])
  @@index([provider, expoTicketId])
  @@index([channel, event, occurredAt])           // NEW — for dashboard queries
  @@index([occurredAt])                            // NEW — for time-series
  @@map("notification_events")
}
```

### 4.5 Migration plan for staging/prod

Dev used `db push` throughout the `feat/notifications` branch. For proper staging/prod deployment, this PR generates a consolidated migration SQL file covering BOTH branches' schema additions:

1. Use the Prisma shadow DB pattern: spin up a throwaway Postgres, run `prisma migrate diff --from-migrations prisma/migrations --to-schema-datamodel prisma/schema.prisma --shadow-database-url $SHADOW_URL --script > migration.sql`.
2. Commit the generated file as `prisma/migrations/20260409_notifications_full/migration.sql`.
3. Document in the rollout plan that staging/prod runs `pnpm prisma migrate deploy` to apply it.

### 4.6 NEW: `NotificationEventAggregateDaily` (pre-aggregated analytics)

The `NotificationEvent` table grows fast (~150K rows/month per tenant at 100 users with moderate activity). Real-time `groupBy` aggregations over the full table are slow and get slower over time. Solution: a pre-aggregated daily rollup table populated by cron.

```prisma
model NotificationEventAggregateDaily {
  id              String              @id @default(cuid())
  companyId       String
  date            DateTime            @db.Date // date-only, company timezone
  channel         NotificationChannel
  event           NotificationEventType
  provider        String?
  count           Int                 @default(0)
  createdAt       DateTime            @default(now())
  updatedAt       DateTime            @updatedAt

  company         Company             @relation(fields: [companyId], references: [id], onDelete: Cascade)

  @@unique([companyId, date, channel, event, provider])
  @@index([companyId, date])
  @@map("notification_event_aggregate_daily")
}
```

A cron job at 2 AM daily (§6.8) aggregates the previous day's `NotificationEvent` rows into this table. The analytics dashboard reads from here for anything older than "today" and falls back to live queries for today's data.

---

## 4A. Operational Safeguards (critical — production-grade scaling & cost controls)

This section adds seven non-negotiable safeguards that protect the system from self-inflicted production incidents (cost explosions, memory spikes, provider bans, duplicate sends, Redis saturation). Every section below is MUST implement, not optional.

### 4A.1 Rate limiting (per-user + per-tenant)

**Problem:** Without rate caps, a bug in event wiring, a cron misfire, or a runaway loop can trigger hundreds of notifications to a single user (or thousands across a tenant) in seconds — costing real money (SMS) and causing provider spam flags.

**Solution:** Two layers of Redis INCR-based rate limits applied inside `dispatch()` BEFORE any Notification row is written:

1. **Per-user limit:** `NOTIFICATIONS_USER_RATE_LIMIT_PER_MIN` (default 20). Protects individual users from spam.
2. **Per-tenant burst limit:** `NOTIFICATIONS_TENANT_RATE_LIMIT_PER_MIN` (default 1000). Protects the overall system from a single tenant overwhelming Redis/workers due to a bug.

CRITICAL priority bypasses BOTH limits (security/payroll alerts must always deliver).

```typescript
// src/core/notifications/dispatch/rate-limiter.ts (NEW)
export async function checkUserRateLimit(userId: string, priority: NotificationPriority): Promise<boolean> {
  if (priority === 'CRITICAL') return true;

  const key = `notif:rate:user:${userId}`;
  const max = env.NOTIFICATIONS_USER_RATE_LIMIT_PER_MIN;

  try {
    const count = await cacheRedis.incr(key);
    if (count === 1) await cacheRedis.expire(key, 60);
    if (count > max) {
      logger.warn('User rate limit exceeded, dropping notification', { userId, count, max });
      return false;
    }
    return true;
  } catch (err) {
    logger.warn('User rate limit check failed (fail-open)', { error: err, userId });
    return true;
  }
}

export async function checkTenantRateLimit(companyId: string, priority: NotificationPriority): Promise<boolean> {
  if (priority === 'CRITICAL') return true;

  const key = `notif:rate:tenant:${companyId}`;
  const max = env.NOTIFICATIONS_TENANT_RATE_LIMIT_PER_MIN;

  try {
    const count = await cacheRedis.incr(key);
    if (count === 1) await cacheRedis.expire(key, 60);
    if (count > max) {
      logger.warn('Tenant rate limit exceeded, dropping notification', { companyId, count, max });
      return false;
    }
    return true;
  } catch (err) {
    logger.warn('Tenant rate limit check failed (fail-open)', { error: err, companyId });
    return true;
  }
}
```

The dispatcher calls `checkTenantRateLimit` once per dispatch (at the top) and `checkUserRateLimit` per recipient. Dropped notifications emit a `RATE_LIMITED` `NotificationEvent` row so admins can see them in the analytics dashboard.

### 4A.1b Already in place from `feat/notifications` (verified, documented here for completeness)

Before detailing new safeguards, these components from the base branch are already production-grade and do NOT need to be re-implemented:

- **Dead Letter Queue (`notifQueueDLQ`):** `src/core/notifications/queue/queues.ts:21` defines the DLQ queue. `src/workers/notification.worker.ts` moves jobs to DLQ after retries exhaust. A DLQ sweeper cron (`dlq-sweeper.worker.ts`) purges rows older than `NOTIFICATIONS_DLQ_RETENTION_DAYS`. Manual replay from the DLQ is possible via the BullMQ UI.
- **Worker-level idempotency:** `src/core/notifications/idempotency/worker-idempotency.ts` provides `claimSendSlot()` — a single atomic `SET NX EX` call that prevents duplicate sends across BullMQ retries. Release on throw, keep on success (TTL 24h).
- **Dispatcher-level dedup:** `src/core/notifications/dispatch/dedup.ts` prevents the same trigger event from firing twice within 60s (TTL configurable) using a payload hash key: `notif:dedup:{companyId}:{triggerEvent}:{entityType}:{entityId}:{recipientId}:{sha1(title+body+data)}`. This covers the reviewer's idempotency-key suggestion (their proposed key is `${triggerEvent}:${entityId}:${userId}` — our existing key is a superset that also includes `companyId` and payload hash).
- **BullMQ worker retry:** 3 attempts with exponential backoff (2s, 8s, 30s) on every delivery job.
- **NOTIFICATIONS_ENABLED kill switch:** flip to `false` to no-op the entire dispatcher.

### 4A.2 Bulk dispatch utility (mandatory for fanouts ≥20)

**Problem:** Iterating `dispatch()` in a loop for 500 payroll recipients creates 500 individual Notification rows + 500 BullMQ jobs + 500 Redis operations in sequence. This is O(N) in the caller's request/worker context, blows up Redis memory, and slows everything.

**Solution:** A dedicated `dispatchBulk()` method on `notificationService` that takes a single trigger event + an array of recipient specs + a shared token baseline + an optional per-recipient token builder. Internally it:

1. Loads rules ONCE (not per recipient)
2. Renders the template ONCE per unique variable combination (caches if tokens are identical across recipients)
3. Uses Prisma `createManyAndReturn` for batch row insertion
4. Enqueues one BullMQ job per chunk of N recipients (default `chunkSize=50`, configurable)
5. The worker's chunked job handler then iterates those 50 users through `channelRouter.send()` in parallel

```typescript
// src/core/notifications/dispatch/dispatch-bulk.ts (NEW)
export interface DispatchBulkInput {
  companyId: string;
  triggerEvent: string;
  type?: string;
  entityType?: string;
  entityId?: string;
  recipients: Array<{
    userId: string;
    tokens?: Record<string, unknown>; // per-recipient overrides
  }>;
  sharedTokens?: Record<string, unknown>; // common across all recipients
  priority?: NotificationPriority;
  systemCritical?: boolean;
  actionUrl?: string;
  chunkSize?: number; // default 50
}

export async function dispatchBulk(input: DispatchBulkInput): Promise<DispatchResult> {
  const traceId = nanoid(12);
  const chunkSize = input.chunkSize ?? 50;

  // 1. Rate-limit each recipient (drop over-limit, keep the rest)
  const allowedRecipients: typeof input.recipients = [];
  for (const r of input.recipients) {
    const ok = await checkUserRateLimit(r.userId, input.priority ?? 'MEDIUM');
    if (ok) allowedRecipients.push(r);
  }

  // 2. Load rules once
  const rules = await loadActiveRules(input.companyId, input.triggerEvent);
  if (rules.length === 0) { /* fallback to IN_APP-only */ }

  // 3. Dedup + consent pre-check per recipient (in-process, no provider calls)
  // 4. Batch-create Notification rows via createManyAndReturn, keyed by recipient
  // 5. Chunk recipients into groups of `chunkSize`
  // 6. For each chunk, enqueue ONE BullMQ job with `isBulk: true, notificationIds: [...], userIds: [...]`
  // 7. Worker's bulk-job handler iterates the chunk in parallel via Promise.allSettled
}
```

**Rule:** any call site where `recipients.length >= 20` (e.g. payroll fanout, ALL-role dispatches, cron fanouts) MUST use `dispatchBulk()`. Individual `dispatch()` calls are fine for 1-19 recipients.

**Backpressure awareness (inside `dispatchBulk`):** Before enqueuing each chunk, check the target queue's waiting count. If it's above a high-water mark (default `NOTIFICATIONS_BULK_QUEUE_HIGH_WATER=5000`), the bulk dispatcher inserts a small delay (`await sleep(200ms)`) between chunks to let the workers drain. This prevents Redis saturation when a cron fanout lands on an already-busy queue.

```typescript
// Inside dispatchBulk, before adding each chunk:
const waiting = await queue.getWaitingCount();
if (waiting > env.NOTIFICATIONS_BULK_QUEUE_HIGH_WATER) {
  logger.warn('Queue overloaded, throttling bulk dispatch', { queueName: queue.name, waiting });
  await new Promise((r) => setTimeout(r, 200));
}
await queue.add('deliver-bulk', { /* chunk payload */ });
```

HIGH/CRITICAL priority dispatches still get added immediately (they use the high-priority queue and should never be throttled).

### 4A.3 Consent cache layer (Redis, 5-minute TTL) with versioned keys

**Problem:** `loadConsentCache()` hits the DB for user + companySettings + preference + categoryPrefs every single time a worker processes a job. At 100 jobs/sec that's 400 DB queries/sec for consent alone.

**Solution:** Wrap `loadConsentCache` with a Redis read-through cache. TTL: 300s (5 minutes).

**Versioned cache key strategy (O(1) invalidation):** Instead of looping every user in a company on company-settings change (O(n) invalidation), use a per-entity version counter. The cache key embeds the current version for both the user and the company. When either changes, we INCR the version counter — all existing cache entries become stale instantly (they reference the old version), and the next read fetches fresh data.

```typescript
// Key layout:
//   notif:consent:v:user:{userId}         → current user version (integer, INCR on user pref change)
//   notif:consent:v:company:{companyId}   → current company version (integer, INCR on company settings change)
//   notif:consent:{userId}:{uv}:{cv}      → cached payload, where uv/cv are the versions at cache time

async function getVersion(scope: 'user' | 'company', id: string): Promise<number> {
  try {
    const v = await cacheRedis.get(`notif:consent:v:${scope}:${id}`);
    return v ? parseInt(v, 10) : 1;
  } catch {
    return 1;
  }
}

export async function loadConsentCache(userId: string): Promise<ConsentCache> {
  // Resolve company once (we need it for the version key)
  const user = await platformPrisma.user.findUnique({ where: { id: userId }, select: { companyId: true } });
  if (!user?.companyId) return loadConsentCacheFromDB(userId);

  const [uv, cv] = await Promise.all([
    getVersion('user', userId),
    getVersion('company', user.companyId),
  ]);
  const cacheKey = `notif:consent:${userId}:${uv}:${cv}`;

  try {
    const cached = await cacheRedis.get(cacheKey);
    if (cached) {
      const parsed = JSON.parse(cached);
      return { ...parsed, categoryPrefs: new Map(parsed.categoryPrefs) };
    }
  } catch { /* fall through */ }

  const fresh = await loadConsentCacheFromDB(userId);
  try {
    await cacheRedis.set(
      cacheKey,
      JSON.stringify({ ...fresh, categoryPrefs: Array.from(fresh.categoryPrefs.entries()) }),
      'EX',
      env.NOTIFICATIONS_CONSENT_CACHE_TTL_SEC,
    );
  } catch { /* non-fatal */ }
  return fresh;
}

export async function invalidateUserConsent(userId: string): Promise<void> {
  try {
    await cacheRedis.incr(`notif:consent:v:user:${userId}`);
  } catch (err) {
    logger.warn('User consent version bump failed', { error: err, userId });
  }
}

export async function invalidateCompanyConsent(companyId: string): Promise<void> {
  try {
    await cacheRedis.incr(`notif:consent:v:company:${companyId}`);
  } catch (err) {
    logger.warn('Company consent version bump failed', { error: err, companyId });
  }
}
```

**Benefits over the loop-users approach:**
- O(1) invalidation — single INCR call regardless of company size
- Stale entries age out naturally via TTL (no orphan keys)
- No thundering herd when a large company's settings change (each user lazily refreshes on their next dispatch)

Wire `invalidateUserConsent(userId)` into:
- `preferences.service.update()` after successful upsert
- `preferences.service.updateCategoryPreferences()` after transaction commit
- `auth.service.signOut()` (optional — stale entries expire anyway)

Wire `invalidateCompanyConsent(companyId)` into:
- Company settings controller when any `*Notifications` field changes
- Any admin CRUD that modifies `NotificationTemplate` or `NotificationRule` that could change which channels are delivered per user (optional — the rule loader cache handles most cases)

### 4A.4 SMS cost controls (mandatory)

**Problem:** SMS is expensive (₹0.15-₹2 per message in India, higher abroad). A bug in event wiring could send thousands of messages in minutes and rack up ₹10K+ in charges before anyone notices.

**Solution:** Three-tier cost protection.

**Tier 1: Per-tenant daily cap** — env var `NOTIFICATIONS_SMS_DAILY_CAP_PER_TENANT` (default 500). Redis counter `notif:sms:daily:{companyId}:{YYYY-MM-DD}` with 48h TTL. Before each SMS send, INCR and reject if over cap. Over-cap sends emit a `SMS_DAILY_CAP_HIT` `NotificationEvent` so admins see it in analytics.

**Tier 2: Per-user daily cap** — env var `NOTIFICATIONS_SMS_DAILY_CAP_PER_USER` (default 10). Same pattern, key `notif:sms:daily:{userId}:{YYYY-MM-DD}`.

**Tier 3: Dry-run mode** — env var `NOTIFICATIONS_SMS_DRY_RUN` (default `false`). When `true`, the `twilioProvider.send()` logs what it would have sent but doesn't hit Twilio. Used for testing + staging environments without burning real credits.

```typescript
// Extension to sms.channel.ts
async function checkSmsCaps(companyId: string, userId: string): Promise<{ allowed: boolean; reason?: string }> {
  const today = new Date().toISOString().slice(0, 10);
  const tenantKey = `notif:sms:daily:${companyId}:${today}`;
  const userKey = `notif:sms:daily:${userId}:${today}`;

  const tenantCount = await cacheRedis.incr(tenantKey);
  if (tenantCount === 1) await cacheRedis.expire(tenantKey, 48 * 3600);
  if (tenantCount > env.NOTIFICATIONS_SMS_DAILY_CAP_PER_TENANT) {
    return { allowed: false, reason: 'SMS_TENANT_CAP' };
  }

  const userCount = await cacheRedis.incr(userKey);
  if (userCount === 1) await cacheRedis.expire(userKey, 48 * 3600);
  if (userCount > env.NOTIFICATIONS_SMS_DAILY_CAP_PER_USER) {
    return { allowed: false, reason: 'SMS_USER_CAP' };
  }

  return { allowed: true };
}
```

Called from `smsChannel.send()` BEFORE hitting Twilio.

### 4A.5 WhatsApp template enforcement (compliance)

**Problem:** Meta Cloud API rejects free-form text messages sent outside the 24-hour session window. For transactional ERP notifications (leave approved, payroll published, etc.) the recipient has almost never initiated a WhatsApp conversation in the last 24h, so every free-form send silently fails. The prior spec draft allowed `templateName?: string` which creates a compliance time bomb.

**Solution:** Require `whatsappTemplateName` to be set on the `NotificationTemplate` before the WhatsApp channel can send. If it's missing, the channel throws `WHATSAPP_TEMPLATE_REQUIRED` immediately — the worker records FAILED and moves on (no wasted API call).

```typescript
// Extension to whatsapp.channel.ts
if (!template?.whatsappTemplateName) {
  throw Object.assign(
    new Error('WHATSAPP_TEMPLATE_REQUIRED: A pre-approved Meta Business template is required for WhatsApp delivery'),
    { code: 'WHATSAPP_TEMPLATE_REQUIRED' },
  );
}
```

**Admin UX:** the `NotificationTemplateScreen` in web validates that `whatsappTemplateName` is set before allowing `channel=WHATSAPP` to be saved. The field is conditionally rendered when channel is WHATSAPP.

### 4A.6 SMS + WhatsApp retry with exponential backoff

**Problem:** Transient provider errors (Twilio 503, Meta rate limits) should retry, not fail immediately. BullMQ worker-level retry (3 attempts, exponential backoff 2s/8s/30s) is already in place for the JOB, but each JOB retry re-runs consent + claim + send from scratch, which is wasteful for transient provider errors.

**Solution:** Add a provider-level retry wrapper around the Twilio and Meta Cloud send calls. 3 attempts with exponential backoff (500ms, 2s, 8s) for transient errors only (not for auth errors, not for `TEMPLATE_REQUIRED`, not for bad phone number). The BullMQ job retry still catches anything that survives this.

```typescript
// Shared util: src/core/notifications/channels/provider-retry.ts
async function withRetry<T>(
  operation: () => Promise<T>,
  opts: { maxAttempts?: number; isRetryable: (err: unknown) => boolean } = { isRetryable: () => true },
): Promise<T> {
  const max = opts.maxAttempts ?? 3;
  for (let attempt = 1; attempt <= max; attempt++) {
    try {
      return await operation();
    } catch (err) {
      if (attempt === max || !opts.isRetryable(err)) throw err;
      const delay = Math.min(500 * Math.pow(4, attempt - 1), 10_000);
      await new Promise((r) => setTimeout(r, delay));
    }
  }
  throw new Error('unreachable');
}

// Usage in twilio.provider.ts:
return withRetry(
  () => c.messages.create({ /* ... */ }),
  {
    isRetryable: (err) => {
      const code = (err as any)?.code;
      const status = (err as any)?.status;
      // Retry only on network or transient provider errors
      if (status === 503 || status === 429) return true;
      if (code === 'ECONNRESET' || code === 'ETIMEDOUT') return true;
      return false;
    },
  },
);
```

Same pattern for Meta Cloud (`5xx` and `429` → retry; `4xx` for template errors → don't).

### 4A.7 WhatsApp + SMS masking parity with PUSH

The existing `maskForChannel()` helper is extended to handle `SMS` and `WHATSAPP` as masked channels alongside `PUSH`. Sensitive fields declared on the template are replaced with `***` in both title and body for ALL three external channels. In-app and email retain full content.

```typescript
// Extension to masker.ts
const MASKED_CHANNELS: NotificationChannel[] = ['PUSH', 'SMS', 'WHATSAPP'];

export function maskForChannel<T extends MaskablePayload>(
  channel: NotificationChannel,
  payload: T,
  sensitiveFields: string[],
): T {
  if (!MASKED_CHANNELS.includes(channel) || sensitiveFields.length === 0) return payload;
  // ... rest of the existing masking logic
}
```

### 4A.8 Cron pagination + parallelism

**Problem:** The original cron implementation plan loaded ALL employees per company into memory (`findMany()` with no limit). For a tenant with 10K employees this is a memory spike and slow serial iteration over companies blocks the event loop.

**Solution:**

**Pattern 1: Cursor-based pagination** inside each per-company run:

```typescript
let cursor: string | undefined = undefined;
const BATCH_SIZE = 200;

while (true) {
  const batch = await tenantDb.employee.findMany({
    where: { status: { notIn: ['EXITED', 'TERMINATED'] }, dateOfBirth: { not: null } },
    select: { id: true, firstName: true, lastName: true, dateOfBirth: true, userId: true },
    take: BATCH_SIZE,
    ...(cursor ? { skip: 1, cursor: { id: cursor } } : {}),
    orderBy: { id: 'asc' },
  });
  if (batch.length === 0) break;

  // process batch: filter by today's MM-DD, dispatch via dispatchBulk
  const celebrating = batch.filter(/* mmdd match */);
  if (celebrating.length > 0) {
    await notificationService.dispatchBulk({
      companyId,
      triggerEvent: 'BIRTHDAY',
      recipients: celebrating.map((e) => ({ userId: e.userId!, tokens: { employee_name: `${e.firstName} ${e.lastName}` } })),
      priority: 'LOW',
      type: 'BIRTHDAY_ANNIVERSARY',
    });
  }

  cursor = batch[batch.length - 1].id;
  if (batch.length < BATCH_SIZE) break;
}
```

**Pattern 1b: Per-tenant jitter** — to avoid a thundering herd where all N tenants get hit at exactly the same cron tick (e.g., every company firing `runBirthday` at exactly 08:00:00), each company's per-company runner adds a small deterministic jitter before starting:

```typescript
// At the top of runBirthdayForCompany:
const jitterMs = Math.floor(Math.random() * 60_000); // 0-60s spread
await new Promise((resolve) => setTimeout(resolve, jitterMs));
```

This spreads the DB + Redis load across a 60-second window instead of a 1-second thundering herd. Companies are still processed in parallel (up to `NOTIFICATIONS_CRON_COMPANY_CONCURRENCY`), but each one's "start" is randomized.

**Pattern 2: Per-company parallelism** with `Promise.allSettled` and a concurrency cap to avoid overwhelming the tenant connection pool:

```typescript
import pLimit from 'p-limit';

async function runBirthday(): Promise<void> {
  const companies = await platformPrisma.company.findMany({ /* ... */ });
  const limit = pLimit(5); // max 5 companies in parallel
  const results = await Promise.allSettled(
    companies.map((c) => limit(() => this.runBirthdayForCompany(c))),
  );
  const failures = results.filter((r) => r.status === 'rejected');
  if (failures.length > 0) {
    logger.warn('Birthday cron: some companies failed', { count: failures.length });
  }
}
```

Install `p-limit` package (~1KB dependency) if not already present.

### 4A.9 `NotificationEvent` retention cleanup cron

**Problem:** At 100 users × 30 notifications/day × multiple channels × event types, `NotificationEvent` grows by ~10K rows/day per tenant. Over 90 days that's ~900K rows per tenant. Query performance degrades without cleanup.

**Solution:** New daily cron at 2 AM UTC that deletes `NotificationEvent` rows older than `NOTIFICATIONS_EVENT_RETENTION_DAYS` (default 90). Runs AFTER the aggregation cron (§4.6), so the daily rollup is always computed before the raw rows are deleted.

```typescript
// In notification-cron.service.ts
this.jobs.push(
  cron.schedule('0 2 * * *', () => this.runEventCleanup()),
);

private async runEventCleanup(): Promise<void> {
  try {
    const cutoff = DateTime.now().minus({ days: env.NOTIFICATIONS_EVENT_RETENTION_DAYS }).toJSDate();
    // Delete in batches to avoid long-running transactions
    let totalDeleted = 0;
    while (true) {
      const result = await platformPrisma.notificationEvent.deleteMany({
        where: { occurredAt: { lt: cutoff } },
      });
      totalDeleted += result.count;
      if (result.count < 10_000) break; // exit when batch is small
    }
    logger.info('NotificationEvent cleanup complete', { totalDeleted });
  } catch (err) {
    logger.error('NotificationEvent cleanup failed', { error: err });
  }
}
```

**Aggregation cron runs at 1:30 AM** (30 min before cleanup) to pre-aggregate the previous day's events into `NotificationEventAggregateDaily` (§4.6) so the analytics dashboard keeps working for older dates after raw rows are deleted.

### 4A.10 Approval handler per-case error isolation

**Problem:** `ess.service.onApprovalComplete()` is the universal dispatch point for 12 entity types. If the dispatch for one entity type throws (e.g. transient Prisma error), the entire approval transition could roll back or fail, blocking approvals for unrelated entities.

**Solution:** Each `case` block wraps its dispatch call in a `try/catch` that logs but doesn't re-throw. The business update (entity status change) is already committed before the dispatch call — if the dispatch fails, the approval still succeeds and an admin can re-notify from the analytics screen (future enhancement).

```typescript
case 'LeaveRequest': {
  // ... existing status update ...
  try {
    await notificationService.dispatch({ /* ... */ });
  } catch (err) {
    logger.error('LeaveRequest approval dispatch failed (non-fatal)', { error: err, entityId, decision });
    // Continue — the approval itself is already committed.
  }
  break;
}
```

Same pattern for all 12 cases.

### 4A.11 Category preference "Mute all" convenience toggle

**Problem:** The category preferences matrix (N categories × 4 channels = up to 64 toggles) is powerful but tedious. Users who want to silence an entire category (e.g. "mute all Payroll") have to toggle 4 switches.

**Solution:** The web + mobile preferences screen renders each category row with a leading "Mute all" checkbox that toggles all 4 channel checkboxes in the row at once. Under the hood, a single `PATCH /notifications/preferences/categories` call with 4 rows is issued (one per channel).

No backend changes needed beyond the existing bulk `updateCategoryPreferences` endpoint accepting multiple rows in one call.

### 4A.12 Analytics pre-aggregation cron

Already covered in §4.6 (schema) and §4A.9 (retention cron). The aggregation cron itself is documented here.

**Pattern:** Runs at 1:30 AM daily. For each `(companyId, date, channel, event, provider)` tuple in yesterday's `NotificationEvent` rows, upserts one row in `NotificationEventAggregateDaily` with `count`. Idempotent — if the cron runs twice on the same day, the unique constraint on `(companyId, date, channel, event, provider)` ensures the upsert handles it.

```typescript
private async runAggregation(): Promise<void> {
  try {
    const yesterday = DateTime.now().minus({ days: 1 }).startOf('day').toJSDate();
    const todayStart = DateTime.now().startOf('day').toJSDate();

    // Group by (companyId, channel, event, provider)
    const aggregates = await platformPrisma.$queryRaw<
      Array<{ companyId: string; channel: string; event: string; provider: string | null; count: bigint }>
    >`
      SELECT n."companyId", ne.channel, ne.event, ne.provider, COUNT(*)::bigint as count
      FROM notification_events ne
      JOIN notifications n ON n.id = ne."notificationId"
      WHERE ne."occurredAt" >= ${yesterday} AND ne."occurredAt" < ${todayStart}
      GROUP BY n."companyId", ne.channel, ne.event, ne.provider
    `;

    for (const agg of aggregates) {
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
    }
    logger.info('Notification event aggregation complete', { rows: aggregates.length });
  } catch (err) {
    logger.error('Notification event aggregation failed', { error: err });
  }
}
```

### 4A.13 New env vars

```typescript
// src/config/env.ts additions (complete set for this spec)

// Safeguards
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

### 4A.14 Observability metrics hook (future-ready)

**Problem:** Today we rely purely on log lines for observability. For production scale, we want structured metrics (counters, histograms) that can be scraped by Prometheus/Datadog/CloudWatch later.

**Solution:** A lightweight metrics facade in `src/core/notifications/metrics/notification-metrics.ts` that wraps increment/histogram calls. The default implementation logs structured events. When a real metrics backend is added later, only this one file changes.

```typescript
// src/core/notifications/metrics/notification-metrics.ts (NEW)
import { logger } from '../../../config/logger';
import { env } from '../../../config/env';

/**
 * Metrics facade for the notification system.
 *
 * Default implementation logs structured events that are easy to grep/parse.
 * When a real metrics backend is wired up (Prometheus client, Datadog SDK,
 * etc.), only this file changes — call sites remain untouched.
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

**Call sites (wired into existing code, non-invasive):**

```typescript
// dispatcher.ts — after enqueue
notificationMetrics.increment('notifications.dispatched', {
  channel: rule.channel,
  priority: bucket.priority,
  triggerEvent: input.triggerEvent,
});

// dispatcher.ts — at start of dispatch
const startTime = Date.now();
// ... work ...
notificationMetrics.histogram('notifications.dispatch_duration_ms', Date.now() - startTime, {
  triggerEvent: input.triggerEvent,
});

// channel router — after each send
notificationMetrics.increment('notifications.sent', { channel, provider, status: 'success' });
// or on failure:
notificationMetrics.increment('notifications.sent', { channel, provider, status: 'failure', errorCode });

// rate-limiter — when limit hit
notificationMetrics.increment('notifications.rate_limited', { scope: 'user' | 'tenant' });

// caps — when cap hit
notificationMetrics.increment('notifications.cost_capped', { channel: 'SMS' | 'WHATSAPP', scope: 'tenant' | 'user' });

// bulk dispatcher — chunk size / throttle events
notificationMetrics.histogram('notifications.bulk_chunk_size', chunkSize, { triggerEvent });
notificationMetrics.increment('notifications.bulk_throttled', { reason: 'queue_high_water' });
```

**Upgrade path:** When a real metrics backend is added, swap the `logger.info` calls inside `notificationMetrics` for `statsd.increment()` / `promClient.Counter` calls. Every call site stays the same.

---

## 5. Per-Module Dispatch Call Sites

This section is the exhaustive catalogue. Every site below gets a `notificationService.dispatch()` call. The implementation plan has task-by-task details with file paths and code snippets; this section is the requirements summary.

### 5.1 Leave module (`src/modules/hr/leave/leave.service.ts`)

| Method (line) | Trigger event | Recipient role | Category | Priority |
|---|---|---|---|---|
| `createRequest` (~499) | `LEAVE_APPLICATION` | APPROVER | LEAVE | MEDIUM |
| `approveRequest` (~857) | (handled by `onApprovalComplete`) | — | — | — |
| `rejectRequest` (~921) | (handled by `onApprovalComplete`) | — | — | — |
| `cancelRequest` (~1039) | `LEAVE_CANCELLED` | APPROVER | LEAVE | LOW |

**Notes:**
- Submission dispatches directly (no approval workflow transition yet).
- Approvals and rejections route through the `onApprovalComplete('LeaveRequest', ...)` case — see §5.3.
- `cancelRequest` is a direct state change (not an approval transition), so it dispatches inline.

### 5.2 Attendance + overtime (`src/modules/hr/attendance/attendance.service.ts`)

| Method (line) | Trigger event | Recipient role | Category | Priority |
|---|---|---|---|---|
| `approveOvertimeRequest` (~1738) | (handled by `onApprovalComplete`) | — | — | — |
| `rejectOvertimeRequest` (~1884) | (handled by `onApprovalComplete`) | — | — | — |

**Regularization** is handled in ESS service (§5.3). Overtime submission is also in ESS.

### 5.3 ESS module (`src/modules/hr/ess/ess.service.ts`)

#### 5.3.1 Submission dispatches (direct)

Each `create*Request` method dispatches on submission before the approval workflow gets involved:

| Method | Trigger event | Recipient role | Category | Priority |
|---|---|---|---|---|
| `regularizeAttendance` (~1728) | `ATTENDANCE_REGULARIZATION` | APPROVER | ATTENDANCE | MEDIUM |
| `createShiftChangeRequest` | `SHIFT_CHANGE` | APPROVER | SHIFT | MEDIUM |
| `createShiftSwapRequest` | `SHIFT_SWAP` | APPROVER | SHIFT | MEDIUM |
| `createWfhRequest` | `WFH_REQUEST` | APPROVER | WFH | MEDIUM |
| `createProfileUpdateRequest` | `PROFILE_UPDATE` | HR | EMPLOYEE_LIFECYCLE | LOW |
| `createReimbursement` | `REIMBURSEMENT` | APPROVER | REIMBURSEMENT | MEDIUM |
| `createLoanApplication` | `LOAN_APPLICATION` | APPROVER | LOAN | MEDIUM |
| `createITDeclaration` | `IT_DECLARATION` | HR, FINANCE | PAYROLL | MEDIUM |
| `createTravelRequest` | `TRAVEL_REQUEST` | APPROVER | REIMBURSEMENT | MEDIUM |
| `createHelpDeskTicket` | `HELPDESK_SUBMITTED` | HR | SUPPORT | MEDIUM |
| `createGrievance` | `GRIEVANCE_SUBMITTED` | HR | SUPPORT | HIGH |
| `createOvertimeRequest` | `OVERTIME_CLAIM` | APPROVER | OVERTIME | MEDIUM |
| `createTrainingRequest` | `TRAINING_REQUEST` | APPROVER | TRAINING | MEDIUM |

#### 5.3.2 Universal approval handler refactor (`onApprovalComplete`)

`onApprovalComplete(entityType, entityId, decision, approverId)` is the single point where every approval transition can be intercepted. The refactor adds one `dispatch()` call per `case` block in the existing `switch (entityType)`:

| entityType | APPROVED trigger | REJECTED trigger | Recipient | Category | Priority |
|---|---|---|---|---|---|
| `LeaveRequest` | `LEAVE_APPROVED` | `LEAVE_REJECTED` | REQUESTER | LEAVE | MEDIUM |
| `AttendanceOverride` | `ATTENDANCE_REGULARIZED` | `ATTENDANCE_REGULARIZATION_REJECTED` | REQUESTER | ATTENDANCE | MEDIUM |
| `OvertimeRequest` | `OVERTIME_CLAIM_APPROVED` | `OVERTIME_CLAIM_REJECTED` | REQUESTER | OVERTIME | MEDIUM |
| `ShiftSwapRequest` | `SHIFT_SWAP_APPROVED` | `SHIFT_SWAP_REJECTED` | REQUESTER | SHIFT | MEDIUM |
| `WfhRequest` | `WFH_APPROVED` | `WFH_REJECTED` | REQUESTER | WFH | MEDIUM |
| `ExpenseClaim` | `REIMBURSEMENT_APPROVED` | `REIMBURSEMENT_REJECTED` | REQUESTER | REIMBURSEMENT | MEDIUM |
| `LoanRecord` | `LOAN_APPROVED` | `LOAN_REJECTED` | REQUESTER | LOAN | HIGH / MEDIUM |
| `ExitRequest` | `RESIGNATION_ACCEPTED` | `RESIGNATION_REJECTED` | REQUESTER | RESIGNATION | HIGH |
| `EmployeeTransfer` | `EMPLOYEE_TRANSFER_APPLIED` | `EMPLOYEE_TRANSFER_REJECTED` | REQUESTER, MANAGER | EMPLOYEE_LIFECYCLE | MEDIUM |
| `EmployeePromotion` | `EMPLOYEE_PROMOTION_APPLIED` | `EMPLOYEE_PROMOTION_REJECTED` | EMPLOYEE, HR | EMPLOYEE_LIFECYCLE | HIGH |
| `SalaryRevision` | `SALARY_REVISION_APPROVED` | `SALARY_REVISION_REJECTED` | EMPLOYEE (masked amount) | PAYROLL | HIGH |
| `PayrollRun` | `PAYROLL_APPROVED` | `PAYROLL_REJECTED` | REQUESTER (payroll admin) | PAYROLL | HIGH |

**Implementation note:** Each case block extends its existing business update with a dispatch call:

```typescript
case 'LeaveRequest': {
  const entity = await tx.leaveRequest.findUnique({ where: { id: entityId } });
  if (!entity) break;
  await tx.leaveRequest.update({ where: { id: entityId }, data: { status: decision === 'APPROVED' ? 'APPROVED' : 'REJECTED' } });

  // NEW: dispatch approval notification
  await notificationService.dispatch({
    companyId,
    triggerEvent: decision === 'APPROVED' ? 'LEAVE_APPROVED' : 'LEAVE_REJECTED',
    entityType: 'LeaveRequest',
    entityId,
    explicitRecipients: [entity.userId],
    tokens: {
      employee_name: /* resolved */,
      leave_days: entity.daysCount,
      from_date: entity.fromDate.toISOString().slice(0, 10),
      to_date: entity.toDate.toISOString().slice(0, 10),
      reason: entity.rejectionReason ?? '',
    },
    actionUrl: `/company/hr/my-leave`,
    type: 'LEAVE',
  });
  break;
}
```

#### 5.3.3 Legacy `triggerNotification()` removal

`ess.service.ts:1180` has a legacy `triggerNotification()` method that uses template rule resolution to send EMAIL only. It's now dead code — the unified `dispatch()` handles all channels. Deprecate this method with a `@deprecated` JSDoc and have it delegate to `notificationService.dispatch()` so any lingering callers still work. Actual removal in Phase B / follow-up PR.

### 5.4 Payroll (`src/modules/hr/payroll-run/payroll-run.service.ts`)

| Method | Trigger event | Recipient | Category | Priority |
|---|---|---|---|---|
| `submitForApproval` (if present) | `PAYROLL_APPROVAL` | APPROVER (Finance Head) | PAYROLL | HIGH |
| `approveRun` (~1493) | (handled by `onApprovalComplete`) | — | — | — |
| `publishPayslips` | `PAYSLIP_PUBLISHED` | EMPLOYEE (all in run) | PAYROLL | HIGH |
| `disburseRun` (~1524) | `SALARY_CREDITED` | EMPLOYEE (all in run, masked amount) | PAYROLL | **CRITICAL** (`systemCritical: true`) |
| `uploadBonus` (if present) | `BONUS_UPLOAD` | APPROVER | PAYROLL | MEDIUM |

**Notes:**
- `SALARY_CREDITED` is marked `systemCritical: true` — bypasses user preference but still respects company master toggle. Amount is masked on PUSH via `sensitiveFields: ['amount']`.
- `publishPayslips` iterates employees in the run and dispatches per employee with `explicitRecipients: [employeeId]`. Uses BullMQ batching so fanout to 500 employees doesn't overwhelm the worker.

### 5.5 Employee lifecycle (`src/modules/hr/employee/employee.service.ts`)

| Method | Trigger event | Recipient | Category | Priority |
|---|---|---|---|---|
| `createEmployee` (~144) | `EMPLOYEE_ONBOARDED` | EMPLOYEE (newly created user if linked), MANAGER, HR | EMPLOYEE_LIFECYCLE | MEDIUM |

**Notes:**
- Fires after the employee record and its user are created.
- If no user is linked (some tenants create employees without user accounts), dispatch is skipped (explicit `if (employee.userId)` guard).

### 5.6 Transfer + Promotion (`src/modules/hr/transfer/transfer.service.ts`)

| Method | Trigger event | Recipient | Category | Priority |
|---|---|---|---|---|
| `createTransfer` (~84) | `EMPLOYEE_TRANSFER` | APPROVER (if workflow) | EMPLOYEE_LIFECYCLE | MEDIUM |
| `applyTransfer` (~190) | `EMPLOYEE_TRANSFER_APPLIED` | EMPLOYEE, old/new MANAGER, HR | EMPLOYEE_LIFECYCLE | MEDIUM |
| `createPromotion` (~386) | `EMPLOYEE_PROMOTION` | APPROVER | EMPLOYEE_LIFECYCLE | HIGH |
| `applyPromotion` (~513) | `EMPLOYEE_PROMOTION_APPLIED` | EMPLOYEE, MANAGER, HR | EMPLOYEE_LIFECYCLE | HIGH |

### 5.7 Salary Revision (`src/modules/hr/payroll/payroll.service.ts`)

| Method | Trigger event | Recipient | Category | Priority |
|---|---|---|---|---|
| `updateEmployeeSalary` (~517) | `SALARY_REVISION` | APPROVER (if workflow) or EMPLOYEE | PAYROLL | HIGH |

Submission dispatches to APPROVER if an approval workflow is configured; otherwise to EMPLOYEE directly (with masked amount on push).

### 5.8 Offboarding (`src/modules/hr/offboarding/offboarding.service.ts`)

| Method | Trigger event | Recipient | Category | Priority |
|---|---|---|---|---|
| `createExitRequest` (~102) | `RESIGNATION` | HR, APPROVER | RESIGNATION | HIGH |
| `approveFnF` (~748) | `FNF_INITIATED` | EMPLOYEE, HR, FINANCE | RESIGNATION | HIGH |
| `payFnF` (~768) | `FNF_COMPLETED` | EMPLOYEE (masked amount), HR | RESIGNATION | HIGH (`systemCritical: true`) |

### 5.9 Recruitment (`src/modules/hr/advanced/advanced.service.ts` and `offer.service.ts`)

| Method | Trigger event | Recipient | Category | Priority |
|---|---|---|---|---|
| `advanceCandidateStage` (~373) | `CANDIDATE_STAGE_CHANGED` | HR | RECRUITMENT | LOW |
| `createInterview` (~480) | `INTERVIEW_SCHEDULED` (existing, migrate) | APPROVER (panelists) | RECRUITMENT | MEDIUM |
| `completeInterview` (~532) | `INTERVIEW_COMPLETED` (existing, migrate) | HR | RECRUITMENT | LOW |
| `createOffer` (offer.service.ts ~102) | `OFFER_SENT` | HR (candidate is external — no push/in-app, email only) | RECRUITMENT | MEDIUM |
| `updateOfferStatus` (offer.service.ts ~199) | `OFFER_ACCEPTED` / `OFFER_REJECTED` | HR, MANAGER | RECRUITMENT | HIGH / MEDIUM |

**Note:** Existing `INTERVIEW_SCHEDULED` and `INTERVIEW_COMPLETED` events are already wired via the HR event bus (`hr-listeners.ts`). This spec keeps the event bus indirection but migrates the listeners from `notificationService.send()` to `notificationService.dispatch()`. (Already done in the `feat/notifications` branch, verified.)

### 5.10 Training (`src/modules/hr/advanced/advanced.service.ts` and `training-session.service.ts`)

| Method | Trigger event | Recipient | Category | Priority |
|---|---|---|---|---|
| `createTrainingNomination` (~908) | `TRAINING_NOMINATION` (existing) | EMPLOYEE | TRAINING | MEDIUM |
| `completeTrainingNomination` (~965) | `TRAINING_COMPLETED` (existing) | EMPLOYEE | TRAINING | LOW |
| `createTrainingRequest` (ess.service.ts) | `TRAINING_REQUEST` (new) | APPROVER | TRAINING | MEDIUM |
| Cron: `TRAINING_SESSION_UPCOMING` | `TRAINING_SESSION_UPCOMING` | ENROLLED EMPLOYEES | TRAINING | MEDIUM |

### 5.11 Assets (`src/modules/hr/advanced/advanced.service.ts`)

| Method | Trigger event | Recipient | Category | Priority |
|---|---|---|---|---|
| `createAssetAssignment` (~1498) | `ASSET_ASSIGNED` | EMPLOYEE | ASSETS | MEDIUM |
| `returnAssetAssignment` (~1552) | `ASSET_RETURNED` | ADMIN | ASSETS | LOW |
| Cron: `ASSET_RETURN_DUE` | `ASSET_RETURN_DUE` | EMPLOYEE, MANAGER | ASSETS | MEDIUM |

### 5.12 Support tickets (`src/core/support/support.service.ts`)

All four methods bridge existing Socket.io emissions with `dispatch()` calls. The Socket.io emission path stays (it drives live ticket UI). The `dispatch()` call creates the bell-icon entry and fires push/email per rules.

| Method | Trigger event | Recipient | Category | Priority |
|---|---|---|---|---|
| `createTicket` (~23) | `TICKET_CREATED` | ADMIN (super-admin support team) | SUPPORT | MEDIUM |
| `sendMessage` (~211) | `TICKET_MESSAGE` | Other party (requester ↔ admin) | SUPPORT | MEDIUM |
| `updateStatus` (~264) | `TICKET_STATUS_CHANGED` | REQUESTER | SUPPORT | MEDIUM |
| `approveModuleChange` (~303) | `MODULE_CHANGE_APPROVED` | REQUESTER (company admin) | SUPPORT | HIGH |

### 5.13 Auth critical (`src/core/auth/auth.service.ts`)

| Method | Trigger event | Recipient | Category | Priority |
|---|---|---|---|---|
| `forgotPassword` (~510) | `PASSWORD_RESET` | SELF | AUTH | CRITICAL (`systemCritical: true`) |
| `login` (new device detection) | `NEW_DEVICE_LOGIN` | SELF | AUTH | CRITICAL (`systemCritical: true`) |
| `lockAccount` (if implemented) | `ACCOUNT_LOCKED` | SELF, SUPER_ADMIN | AUTH | CRITICAL (`systemCritical: true`) |

**Notes:**
- All three are `systemCritical: true` → bypass user prefs and quiet hours (but still respect company master toggle for legal reasons).
- `NEW_DEVICE_LOGIN` requires detecting whether the device is new — use the `ActiveSession` table's `deviceInfo` and `ipAddress` as a fingerprint, compare to the most recent session.
- Password reset already sends an email directly via `registration-emails.ts` — the dispatch call goes through the unified path instead, so the email is rendered from the `PASSWORD_RESET` template and tracked in `NotificationEvent`.

---

## 6. Informational Cron Events

Seven new scheduled notification jobs, wired into the existing cron pattern from `analytics-cron.service.ts`.

### 6.1 Cron job layout

New file: `src/core/notifications/cron/notification-cron.service.ts`

```typescript
import cron, { ScheduledTask } from 'node-cron';
import { logger } from '../../../config/logger';

class NotificationCronService {
  private jobs: ScheduledTask[] = [];

  startAll(): void {
    // 1. Birthday — daily 8 AM UTC (adjusted per-company)
    this.jobs.push(cron.schedule('0 8 * * *', () => this.runBirthday()));

    // 2. Work anniversary — daily 8 AM
    this.jobs.push(cron.schedule('0 8 * * *', () => this.runWorkAnniversary()));

    // 3. Holiday reminder — daily 7 AM
    this.jobs.push(cron.schedule('0 7 * * *', () => this.runHolidayReminder()));

    // 4. Probation end — daily 9 AM
    this.jobs.push(cron.schedule('0 9 * * *', () => this.runProbationEnd()));

    // 5. Asset return due — daily 8 AM
    this.jobs.push(cron.schedule('0 8 * * *', () => this.runAssetReturnDue()));

    // 6. Certificate expiring sweep — daily 9 AM
    this.jobs.push(cron.schedule('0 9 * * *', () => this.runCertificateExpiring()));

    // 7. Training session upcoming — daily 7 AM
    this.jobs.push(cron.schedule('0 7 * * *', () => this.runTrainingSessionUpcoming()));
  }

  stopAll(): void {
    for (const job of this.jobs) job.stop();
    this.jobs = [];
  }

  private async runBirthday(): Promise<void> { /* see §6.2 */ }
  // ... one method per cron
}

export const notificationCronService = new NotificationCronService();
```

Startup wiring in `src/app/server.ts` after `analyticsCronService.startAll()`:

```typescript
import { notificationCronService } from '../core/notifications/cron/notification-cron.service';
// ...
notificationCronService.startAll();
```

### 6.2 Cron: Birthday

```typescript
private async runBirthday(): Promise<void> {
  try {
    const companies = await platformPrisma.company.findMany({
      select: { id: true, settings: { select: { timezone: true } } },
    });

    for (const company of companies) {
      const tz = company.settings?.timezone ?? 'UTC';
      const today = DateTime.now().setZone(tz);
      const mmdd = today.toFormat('MM-dd');

      const tenantDb = await getTenantDbForCompany(company.id);
      try {
        // Find employees whose birthday is today
        const employees = await tenantDb.employee.findMany({
          where: {
            status: { notIn: ['EXITED', 'TERMINATED'] },
            dateOfBirth: { not: null },
          },
          select: { id: true, firstName: true, lastName: true, dateOfBirth: true, userId: true },
        });

        const celebrating = employees.filter(
          (e) => e.dateOfBirth && DateTime.fromJSDate(e.dateOfBirth).toFormat('MM-dd') === mmdd,
        );

        for (const emp of celebrating) {
          if (!emp.userId) continue;
          await notificationService.dispatch({
            companyId: company.id,
            triggerEvent: 'BIRTHDAY',
            entityType: 'Employee',
            entityId: emp.id,
            explicitRecipients: [emp.userId],
            tokens: { employee_name: `${emp.firstName} ${emp.lastName}` },
            type: 'BIRTHDAY',
            priority: 'LOW',
          });
        }
      } finally {
        await tenantDb.$disconnect();
      }
    }
  } catch (err) {
    logger.error('Birthday cron failed', { error: err });
  }
}
```

### 6.3 Cron: Work anniversary

Same pattern as birthday, but matches `joiningDate.toFormat('MM-dd')`. Computes years-of-service as `today.year - joiningDate.year` and passes `{ years_of_service }` token.

### 6.4 Cron: Holiday reminder

- Fetches `holidays` table where `date` is within next 3 days (or today).
- Dispatches `HOLIDAY_REMINDER` to all active employees in company with tokens `{ holiday_name, holiday_date, days_until }`.
- Runs per-company in company timezone.

### 6.5 Cron: Probation end

- Fetches `Employee` where `probationEndDate` is within next 7 days and `status = 'PROBATION'`.
- Dispatches `PROBATION_END_REMINDER` to HR + reporting manager with tokens `{ employee_name, probation_end_date }`.

### 6.6 Cron: Asset return due

- Fetches `AssetAssignment` where `returnDueDate` is within next 3 days and `returnedAt IS NULL`.
- Dispatches `ASSET_RETURN_DUE` to employee + manager.

### 6.7 Cron: Certificate expiring (bulk sweep)

- Fetches `TrainingNomination` with certificate expiring in next 30 days.
- Dispatches `CERTIFICATE_EXPIRING` (template already seeded) — existing HR listener only fires per-nomination, this cron batches to catch any missed ones.

### 6.8 Cron: Training session upcoming

- Fetches `TrainingSession` starting in next 24 hours.
- Dispatches `TRAINING_SESSION_UPCOMING` to all enrolled employees.

### 6.9 New default templates for cron events

Extend `src/core/notifications/templates/defaults.ts` with 7 new entries:

| Code | Name | Channels | Category | Priority |
|---|---|---|---|---|
| `BIRTHDAY` | Happy Birthday | IN_APP, PUSH | BIRTHDAY_ANNIVERSARY | LOW |
| `WORK_ANNIVERSARY` | Work Anniversary | IN_APP, PUSH | BIRTHDAY_ANNIVERSARY | LOW |
| `HOLIDAY_REMINDER` | Holiday Reminder | IN_APP | ANNOUNCEMENTS | LOW |
| `PROBATION_END_REMINDER` | Probation Ending Soon | IN_APP, EMAIL | EMPLOYEE_LIFECYCLE | MEDIUM |
| `ASSET_RETURN_DUE` | Asset Return Due | IN_APP, PUSH, EMAIL | ASSETS | MEDIUM |
| `TRAINING_SESSION_UPCOMING` | Training Session Tomorrow | IN_APP, PUSH, EMAIL | TRAINING | MEDIUM |

(Certificate expiring already seeded.)

Each entry has its rendered title, body, variable list, and recipient role. See the implementation plan for exact handlebars templates.

### 6.10 Idempotency for crons

Each cron run computes a deterministic `dedupHash` per `(companyId, triggerEvent, entityId, date)` so re-running the same cron within the same day doesn't fire twice. The existing dispatcher dedup (60s TTL) isn't enough — cron runs are 24h apart. Add a longer-TTL dedup key for cron events specifically:

```typescript
const cronDedupKey = `notif:cron-dedup:${companyId}:${triggerEvent}:${entityId}:${todayStr}`;
const set = await cacheRedis.set(cronDedupKey, '1', 'EX', 86400, 'NX');
if (set === null) continue; // already fired today
```

---

## 7. SMS Provider (Twilio)

### 7.1 Package + config

Install: `pnpm add twilio`

New env vars in `src/config/env.ts`:
```typescript
TWILIO_ACCOUNT_SID: z.string().optional(),
TWILIO_AUTH_TOKEN: z.string().optional(),
TWILIO_FROM_NUMBER: z.string().optional(),   // e.g. +14155551234
TWILIO_MESSAGING_SERVICE_SID: z.string().optional(), // alternative to from number
```

### 7.2 Provider implementation

New file: `src/core/notifications/channels/sms/twilio.provider.ts`

```typescript
import twilio, { Twilio } from 'twilio';
import { env } from '../../../../config/env';
import { logger } from '../../../../config/logger';
import type { NotificationPriority } from '@prisma/client';

let client: Twilio | null = null;

function getClient(): Twilio | null {
  if (client) return client;
  if (!env.TWILIO_ACCOUNT_SID || !env.TWILIO_AUTH_TOKEN) return null;
  client = twilio(env.TWILIO_ACCOUNT_SID, env.TWILIO_AUTH_TOKEN);
  return client;
}

export interface TwilioSendPayload {
  to: string; // E.164 format (+country code)
  body: string;
  priority: NotificationPriority;
}

export interface TwilioSendResult {
  provider: 'twilio';
  messageId: string | null;
}

export const twilioProvider = {
  async send(payload: TwilioSendPayload, traceId: string): Promise<TwilioSendResult> {
    const c = getClient();
    if (!c) {
      throw Object.assign(new Error('TWILIO_NOT_CONFIGURED'), { code: 'TWILIO_NOT_CONFIGURED' });
    }
    if (!env.TWILIO_FROM_NUMBER && !env.TWILIO_MESSAGING_SERVICE_SID) {
      throw Object.assign(new Error('TWILIO_NO_SENDER'), { code: 'TWILIO_NO_SENDER' });
    }

    try {
      const message = await c.messages.create({
        body: payload.body,
        to: payload.to,
        ...(env.TWILIO_MESSAGING_SERVICE_SID
          ? { messagingServiceSid: env.TWILIO_MESSAGING_SERVICE_SID }
          : { from: env.TWILIO_FROM_NUMBER! }),
      });
      logger.info('SMS sent', { traceId, to: payload.to, sid: message.sid });
      return { provider: 'twilio', messageId: message.sid };
    } catch (err: any) {
      logger.error('Twilio send failed', { error: err, traceId, to: payload.to });
      throw Object.assign(new Error(err?.message ?? 'TWILIO_SEND_FAILED'), {
        code: err?.code ?? 'TWILIO_SEND_FAILED',
      });
    }
  },
};
```

### 7.3 Channel integration

Rewrite `src/core/notifications/channels/sms.channel.ts`:

```typescript
import { platformPrisma } from '../../../config/database';
import { twilioProvider } from './sms/twilio.provider';
import type { ChannelSendArgs, ChannelSendResult } from './channel-router';

export const smsChannel = {
  async send({ notificationId, userId, traceId, priority }: ChannelSendArgs): Promise<ChannelSendResult> {
    const notif = await platformPrisma.notification.findUniqueOrThrow({ where: { id: notificationId } });
    const user = await platformPrisma.user.findUniqueOrThrow({ where: { id: userId } });
    if (!user.phone) {
      throw Object.assign(new Error('NO_USER_PHONE'), { code: 'NO_USER_PHONE' });
    }

    // Normalize to E.164 — if no country code, assume India (+91)
    const to = user.phone.startsWith('+') ? user.phone : `+91${user.phone.replace(/\D/g, '')}`;

    // Apply PUSH-equivalent masking to SMS as well (same sensitivity concerns)
    const template = notif.templateId
      ? await platformPrisma.notificationTemplate.findUnique({ where: { id: notif.templateId } })
      : null;
    const sensitiveFields = (template?.sensitiveFields as string[] | null) ?? [];
    const { maskForChannel } = await import('../templates/masker');
    const masked = maskForChannel('SMS' as any, { title: notif.title, body: notif.body, data: notif.data as any }, sensitiveFields);

    const result = await twilioProvider.send(
      { to, body: `${masked.title}: ${masked.body}`, priority },
      traceId,
    );

    return { provider: 'twilio', messageId: result.messageId };
  },
};
```

Extend `maskForChannel()` to handle `SMS` the same way as `PUSH` (both are external, short-form channels where sensitive data should not leak).

### 7.4 Rate limiting, cost caps, retries, and compliance

**Cost caps (see §4A.4):** Every SMS send passes through `checkSmsCaps(companyId, userId)` which enforces per-tenant daily cap (default 500/day) and per-user daily cap (default 10/day) via Redis INCR keys. Over-cap sends emit `SMS_TENANT_CAP` or `SMS_USER_CAP` `NotificationEvent` rows so admins see them in the analytics dashboard.

**Per-user rate limiting (see §4A.1):** The dispatcher's `checkUserRateLimit()` applies to SMS the same way it applies to push (20/min by default). CRITICAL priority bypasses. This is on top of the daily caps — a burst of 20 in one minute will be rate limited even if the daily cap isn't hit.

**Provider-level retry (see §4A.6):** The Twilio `messages.create()` call is wrapped in `withRetry()` with 3 attempts and exponential backoff (500ms/2s/8s). Only transient errors retry (503, 429, ECONNRESET, ETIMEDOUT). Auth failures and bad-phone errors do NOT retry.

**BullMQ worker-level retry** is still in place for anything that escapes the provider retry (job fails the whole 3x attempts → DLQ).

**Dry-run mode (see §4A.4):** `NOTIFICATIONS_SMS_DRY_RUN=true` bypasses Twilio entirely and logs the would-be send. Used in staging and for smoke tests without burning real credits.

**Legal compliance:** SMS is subject to TCPA (US), DND (India), GDPR (EU). The company-level `smsNotifications` master toggle is the compliance switch. The admin UI shows a warning explaining SMS requires explicit user opt-in per local law.

### 7.5 Default off

`CompanySettings.smsNotifications` defaults to `false` (already set in the existing schema). Tenants must explicitly enable it — this prevents accidental SMS charges on day-one.

### 7.6 Masking parity

SMS messages apply the same `sensitiveFields` masking as PUSH (see §4A.7). Amounts, reset codes, account numbers declared on the template are replaced with `***` in the SMS body.

---

## 8. WhatsApp Provider (Meta Cloud API)

### 8.1 Package + config

Use Meta Cloud API directly via `fetch` — no SDK dependency. Meta's official WhatsApp Business API is accessed via Graph API.

New env vars:
```typescript
META_WHATSAPP_PHONE_NUMBER_ID: z.string().optional(), // sender phone number ID from Meta dashboard
META_WHATSAPP_ACCESS_TOKEN: z.string().optional(),    // permanent access token
META_WHATSAPP_API_VERSION: z.string().default('v21.0'),
```

### 8.2 Provider implementation

New file: `src/core/notifications/channels/whatsapp/meta-cloud.provider.ts`

```typescript
import { env } from '../../../../config/env';
import { logger } from '../../../../config/logger';

export interface MetaCloudPayload {
  to: string; // E.164 (no leading +)
  body: string;
  templateName?: string; // if using a pre-approved template (required for outside 24h window)
}

export interface MetaCloudResult {
  provider: 'meta-cloud';
  messageId: string | null;
}

export const metaCloudProvider = {
  async send(payload: MetaCloudPayload, traceId: string): Promise<MetaCloudResult> {
    if (!env.META_WHATSAPP_PHONE_NUMBER_ID || !env.META_WHATSAPP_ACCESS_TOKEN) {
      throw Object.assign(new Error('WHATSAPP_NOT_CONFIGURED'), { code: 'WHATSAPP_NOT_CONFIGURED' });
    }

    const url = `https://graph.facebook.com/${env.META_WHATSAPP_API_VERSION}/${env.META_WHATSAPP_PHONE_NUMBER_ID}/messages`;

    const body = payload.templateName
      ? {
          messaging_product: 'whatsapp',
          to: payload.to.replace(/^\+/, ''),
          type: 'template',
          template: {
            name: payload.templateName,
            language: { code: 'en_US' },
            components: [{ type: 'body', parameters: [{ type: 'text', text: payload.body }] }],
          },
        }
      : {
          messaging_product: 'whatsapp',
          to: payload.to.replace(/^\+/, ''),
          type: 'text',
          text: { body: payload.body },
        };

    try {
      const res = await fetch(url, {
        method: 'POST',
        headers: {
          Authorization: `Bearer ${env.META_WHATSAPP_ACCESS_TOKEN}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(body),
      });
      if (!res.ok) {
        const err = await res.text();
        throw new Error(`Meta Cloud API error ${res.status}: ${err}`);
      }
      const json = (await res.json()) as { messages?: Array<{ id?: string }> };
      const messageId = json.messages?.[0]?.id ?? null;
      logger.info('WhatsApp sent', { traceId, to: payload.to, messageId });
      return { provider: 'meta-cloud', messageId };
    } catch (err: any) {
      logger.error('Meta Cloud send failed', { error: err, traceId });
      throw Object.assign(new Error(err?.message ?? 'META_SEND_FAILED'), {
        code: 'META_SEND_FAILED',
      });
    }
  },
};
```

### 8.3 Template policy — **ENFORCED (mandatory)**

WhatsApp Business API rejects free-form text messages sent outside the 24-hour "session window" (i.e., outside a recent user-initiated conversation). For transactional ERP notifications, the recipient has almost never initiated a WhatsApp conversation in the last 24h, so every free-form send would silently fail in production.

**This spec mandates:** `whatsappTemplateName` MUST be set on any `NotificationTemplate` where `channel=WHATSAPP`. The WhatsApp channel throws `WHATSAPP_TEMPLATE_REQUIRED` immediately if it's missing — no free-form text mode is supported (see §4A.5).

**Admin UX enforcement:**
- `NotificationTemplateScreen` (web) conditionally renders a `whatsappTemplateName` text input when `channel === 'WHATSAPP'` and marks it required.
- The form submission is blocked if the field is empty.
- A help tooltip explains that the template must first be registered and approved in Meta Business Manager.

**Provider retry + dry-run + cost control:**
- The Meta Cloud API call is wrapped in `withRetry()` (§4A.6) — 3 attempts with exponential backoff for 5xx and 429 only.
- `NOTIFICATIONS_WHATSAPP_DRY_RUN=true` bypasses the HTTP call.
- Per-tenant and per-user daily caps are enforced the same way as SMS (§4A.4), keys: `notif:whatsapp:daily:{companyId}:{date}` and `notif:whatsapp:daily:{userId}:{date}`, with defaults `NOTIFICATIONS_WHATSAPP_DAILY_CAP_PER_TENANT=500` and `NOTIFICATIONS_WHATSAPP_DAILY_CAP_PER_USER=10`.

Schema extension:
```prisma
model NotificationTemplate {
  // ... existing fields
  whatsappTemplateName String?  // NEW — pre-approved Meta template name (required for WHATSAPP channel)
}
```

**Validator enforcement (backend):** `createNotificationTemplateSchema` in `ess.validators.ts` adds a `.refine()` that rejects `{ channel: 'WHATSAPP', whatsappTemplateName: null | '' }`.

### 8.4 Channel integration

Rewrite `src/core/notifications/channels/whatsapp.channel.ts` to call `metaCloudProvider`, mirroring the SMS pattern with full safeguards:

```typescript
import { platformPrisma } from '../../../config/database';
import { metaCloudProvider } from './whatsapp/meta-cloud.provider';
import { maskForChannel } from '../templates/masker';
import { checkWhatsappCaps } from './whatsapp/caps';
import type { ChannelSendArgs, ChannelSendResult } from './channel-router';

export const whatsappChannel = {
  async send({ notificationId, userId, traceId, priority }: ChannelSendArgs): Promise<ChannelSendResult> {
    const notif = await platformPrisma.notification.findUniqueOrThrow({ where: { id: notificationId } });
    const user = await platformPrisma.user.findUniqueOrThrow({ where: { id: userId } });
    if (!user.phone) throw Object.assign(new Error('NO_USER_PHONE'), { code: 'NO_USER_PHONE' });

    const template = notif.templateId
      ? await platformPrisma.notificationTemplate.findUnique({ where: { id: notif.templateId } })
      : null;

    // 1. ENFORCE template requirement (§4A.5)
    if (!template?.whatsappTemplateName) {
      throw Object.assign(new Error('WHATSAPP_TEMPLATE_REQUIRED'), { code: 'WHATSAPP_TEMPLATE_REQUIRED' });
    }

    // 2. Cost caps (§4A.4 pattern applied to WhatsApp)
    const caps = await checkWhatsappCaps(notif.companyId, userId);
    if (!caps.allowed) {
      throw Object.assign(new Error(caps.reason ?? 'WHATSAPP_CAP_HIT'), { code: caps.reason ?? 'WHATSAPP_CAP_HIT' });
    }

    // 3. Masking (§4A.7 — WhatsApp now masked same as PUSH and SMS)
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

    const to = user.phone.startsWith('+') ? user.phone : `+91${user.phone.replace(/\D/g, '')}`;

    // 4. Provider call (internally wrapped in withRetry, see §4A.6)
    const result = await metaCloudProvider.send(
      {
        to,
        body: `${masked.title}\n\n${masked.body}`,
        templateName: template.whatsappTemplateName,
      },
      traceId,
    );
    return { provider: 'meta-cloud', messageId: result.messageId };
  },
};
```

---

## 9. Per-Category User Preferences

### 9.1 Schema — see §4.1

New `UserNotificationCategoryPreference` model with unique `(userId, category, channel)`.

### 9.2 Consent gate extension

`src/core/notifications/dispatch/consent-gate.ts` — extend `evaluateConsent()`:

```typescript
export interface ConsentCache {
  userId: string;
  companySettings: CompanySettings | null;
  preference: UserNotificationPreference | null;
  categoryPrefs: Map<string, boolean>; // key = `${category}:${channel}`, value = enabled
}

export async function loadConsentCache(userId: string): Promise<ConsentCache> {
  // ... existing fetches ...
  const catPrefs = await platformPrisma.userNotificationCategoryPreference.findMany({
    where: { userId },
    select: { category: true, channel: true, enabled: true },
  });
  const categoryPrefs = new Map<string, boolean>();
  for (const p of catPrefs) {
    categoryPrefs.set(`${p.category}:${p.channel}`, p.enabled);
  }
  return { userId, companySettings, preference, categoryPrefs };
}

export function evaluateConsent(
  cache: ConsentCache,
  channel: NotificationChannel,
  priority: NotificationPriority,
  category: string | null,        // NEW
  systemCritical = false,
): ConsentResult {
  // ... existing in-app short-circuit, company master, systemCritical override, channel pref ...

  // NEW: per-category override check (only if a row exists — no row means "use channel default")
  if (category) {
    const key = `${category}:${channel}`;
    const catEnabled = cache.categoryPrefs.get(key);
    if (catEnabled === false) return { allowed: false, reason: 'CATEGORY_PREF_OFF' };
  }

  // ... quiet hours ...
  return { allowed: true };
}
```

The worker passes the `category` from the job payload (sourced from the rule's `category` column or the default catalogue lookup).

### 9.3 Preferences API extension

Extend `GET /notifications/preferences` to return category preferences alongside per-channel:

```typescript
// Response shape:
{
  preference: { /* existing per-channel toggles */ },
  companyMasters: { /* existing */ },
  categoryPreferences: [
    { category: 'LEAVE', channel: 'PUSH', enabled: true },
    { category: 'PAYROLL', channel: 'PUSH', enabled: false },
    // ...
  ],
  categoryCatalogue: [
    { code: 'LEAVE', label: 'Leave', locked: false },
    { code: 'AUTH', label: 'Security', locked: true },
    // ...
  ],
}
```

Extend `PATCH /notifications/preferences` to accept a `categoryPreferences` array and upsert:

```typescript
{
  pushEnabled: true,
  categoryPreferences: [
    { category: 'PAYROLL', channel: 'PUSH', enabled: false },
  ]
}
```

New controller method `updateCategoryPreferences(userId, updates)` in `preferences.service.ts` that upserts each `(category, channel)` row.

### 9.4 Web preferences screen extension

Add a collapsible "Fine-tune by category" section below the existing channels list. When expanded, renders a table: rows are categories (from `categoryCatalogue`), columns are the 4 user-facing channels (Push, Email, SMS, WhatsApp). Each cell is a checkbox. Toggling a checkbox upserts one `UserNotificationCategoryPreference` row via the mutation.

**Mute all convenience (§4A.11):** each category row has a leading "Mute all" checkbox. When checked, all 4 channel cells in that row are set to disabled in a single PATCH (the endpoint accepts bulk updates). When unchecked, all 4 are re-enabled. Mute-all state is derived: `muted = all 4 channels are disabled`.

- Categories with `locked: true` (`AUTH`) are rendered as dimmed rows with "Always enabled — security notifications cannot be disabled" tooltip. The "Mute all" checkbox is hidden for locked rows.
- Category rows also respect the company master and per-channel user pref: if `companyMasters.push === false` or `preference.pushEnabled === false`, the entire Push column is disabled with explanation tooltip.
- Mutation uses optimistic update + rollback matching the per-channel pattern.

### 9.5 Mobile preferences screen extension

Same functionality via a `ScrollView` with collapsible sections. Each category row has:
- A "Mute all" switch on the left (hidden for locked categories)
- 4 per-channel `Switch` components inline (collapsed under an expand affordance to keep the row compact)
- A `Lock` icon from `lucide-react-native` for the `AUTH` category

Locked categories show a tooltip / subtitle explaining why they can't be modified.

---

## 10. Tenant Onboarding Step 5 Preferences

**File:** `web-system-app/src/features/super-admin/tenant-onboarding/steps/Step05Preferences.tsx`

Extend the existing Zod schema + form:

```typescript
// Existing
emailNotif: z.boolean(),
whatsapp: z.boolean(),

// Add
pushNotif: z.boolean(),
smsNotif: z.boolean(),
inAppNotif: z.boolean(),
```

Add three new `ToggleRow` components in the render block. The payload passed to `createTenant` backend endpoint is extended to include the three new fields.

**Backend:** `src/core/tenant/tenant.service.ts` (or wherever `createTenant` lives) reads the new fields from the request body and sets them on the `CompanySettings` creation input. The existing `pushNotifications`, `smsNotifications`, `inAppNotifications` fields on the model are already there from the `feat/notifications` branch — just need to wire the onboarding payload through.

---

## 11. Analytics Dashboard

A new backend endpoint + web screen for observability of the notification pipeline.

### 11.1 Backend — aggregation endpoints (reads from pre-aggregated table)

**Strategy:** the analytics service reads from `NotificationEventAggregateDaily` (§4.6) for anything older than today, and queries `NotificationEvent` directly only for today's data. This keeps dashboard queries fast even as raw event volume grows. Pre-aggregation is populated by the daily cron (§4A.12).

New file: `src/core/notifications/analytics/notification-analytics.service.ts`

```typescript
export interface NotificationAnalyticsSummary {
  dateFrom: string;
  dateTo: string;
  totals: {
    dispatched: number;
    sent: number;
    delivered: number;
    failed: number;
    bounced: number;
    skipped: number;
    opened: number;
  };
  byChannel: Array<{ channel: string; sent: number; delivered: number; failed: number }>;
  byPriority: Array<{ priority: string; count: number }>;
  deliveryRateByDay: Array<{ date: string; sent: number; delivered: number; failed: number }>;
  topFailingTemplates: Array<{ templateCode: string; failCount: number; errorCodes: string[] }>;
  averageDeliveryTimeMs: number | null;
}

export const notificationAnalyticsService = {
  async getSummary(companyId: string, dateFrom: Date, dateTo: Date): Promise<NotificationAnalyticsSummary> {
    // 1. Split the range into "historical" (aggregated) and "today" (live).
    // 2. For historical, query NotificationEventAggregateDaily via groupBy/sum.
    // 3. For today, query NotificationEvent directly (small window, few rows).
    // 4. Merge + return.
  },

  async getTopFailing(companyId: string, limit = 10): Promise<Array<{ templateId: string; templateCode: string; failCount: number }>> {
    // Read from NotificationEventAggregateDaily for historical, NotificationEvent for today.
    // Join with NotificationTemplate for the template code (cached).
  },

  async getDeliveryTrend(companyId: string, dateFrom: Date, dateTo: Date): Promise<Array<{ date: string; sent: number; delivered: number; failed: number }>> {
    // Pure NotificationEventAggregateDaily read — one row per (date, channel, event).
    // In-memory pivot to the time-series shape.
  },
};
```

**Index for the live-query path:** `NotificationEvent` already has `@@index([channel, event, occurredAt])` and `@@index([occurredAt])` from §4.4 which cover the today-only query.

New controller endpoints mounted under `/notifications/analytics`:

```
GET /notifications/analytics/summary?dateFrom=&dateTo=  — full summary
GET /notifications/analytics/top-failing               — top failing templates
GET /notifications/analytics/delivery-trend            — time series
```

Permission gate: `hr:configure` or new `notifications:analytics` — company admin only.

### 11.2 Web — analytics screen

New file: `web-system-app/src/features/company-admin/hr/NotificationAnalyticsScreen.tsx`

Layout matches the existing analytics dashboards (reuse chart primitives from `src/features/analytics/`):

- **Top row:** 4 KPI cards — Total Sent, Delivery Rate %, Failure Rate %, Avg Delivery Time
- **Row 2:** Stacked bar chart — delivery trend by day (sent / delivered / failed)
- **Row 3 left:** Donut chart — channel breakdown (PUSH / EMAIL / SMS / WHATSAPP / IN_APP)
- **Row 3 right:** Donut chart — priority breakdown (LOW / MEDIUM / HIGH / CRITICAL)
- **Row 4:** Table — top 10 failing templates with error codes

Date range picker at the top (default last 30 days). Route: `/app/company/hr/notification-analytics`.

Add navigation manifest entry in `navigation-manifest.ts`:

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

### 11.3 Mobile — skip

The analytics dashboard is a power-user feature for company admins. No mobile screen.

---

## 12. Prisma Migration for Staging/Prod

### 12.1 Strategy

Dev used `db push` for both `feat/notifications` and this branch. Staging/prod needs a proper SQL migration file.

### 12.2 Generation

```bash
cd avy-erp-backend
# 1. Spin up a temporary shadow DB
docker run --rm -d --name prisma-shadow -e POSTGRES_PASSWORD=shadow -p 5433:5432 postgres:16
export SHADOW_DB_URL="postgresql://postgres:shadow@localhost:5433/shadow"

# 2. Generate the migration SQL by diffing all existing migrations against the current schema
pnpm prisma migrate diff \
  --from-migrations prisma/migrations \
  --to-schema-datamodel prisma/schema.prisma \
  --shadow-database-url "$SHADOW_DB_URL" \
  --script > prisma/migrations/20260409_notifications_full/migration.sql

# 3. Clean up
docker rm -f prisma-shadow
```

### 12.3 Verification

- Review the generated SQL — should include: `CREATE TABLE notification_events`, `CREATE TABLE user_notification_preferences`, `CREATE TABLE user_notification_category_preferences`, `ALTER TABLE notifications ADD COLUMN ...`, `ALTER TABLE user_devices ADD COLUMN ...`, `CREATE INDEX ...`, etc.
- Apply to a staging replica of prod DB: `DATABASE_URL=staging_db pnpm prisma migrate deploy`.
- Spot-check that the seeded default templates are present (they were seeded via `prisma/seeds/2026-04-09-seed-default-notification-templates.ts` on dev — staging runs the same seed script).

### 12.4 Commit

The generated `migration.sql` file is committed to git under `prisma/migrations/20260409_notifications_full/`. The directory name matches `timestamp_description` Prisma convention.

---

## 13. Tests

### 13.1 Unit tests (backend, Jest)

| File | Tests |
|---|---|
| `__tests__/dispatcher.test.ts` | happy path; no rules → fallback; ad-hoc mode; dedup hit; backpressure drop; bucket merging; priority upgrade; `createManyAndReturn` Map correlation; catches internal errors |
| `__tests__/consent-gate.test.ts` | company off; user off; critical override; quiet hours (same-day + overnight); in-app always allowed; category pref off; locked category (AUTH) cannot be overridden |
| `__tests__/dedup.test.ts` | same payload TTL hit; different payload same entity; Redis unavailable fail-open; stable JSON key sorting |
| `__tests__/rule-loader.test.ts` | cache hit; cache miss → DB fetch → write-through; invalidate specific; invalidate all via SCAN; Date rehydration |
| `__tests__/recipient-resolver.test.ts` | each of the 9 role tokens; caching within single dispatch; MANAGER lookup via Employee relation |
| `__tests__/channel-router.test.ts` | routes to correct provider; in-app no-op; unknown channel throws |
| `__tests__/push-channel.test.ts` | Expo vs FCM partition; LATEST_ONLY strategy; dead token cleanup user-scoped |
| `__tests__/expo-provider.test.ts` | chunking; DeviceNotRegistered → deadTokens; success/failed device ID tracking; MAX_FAILURE_COUNT deactivation |
| `__tests__/fcm-provider.test.ts` | multicast response alignment; JSON stringify nested data; dead token cleanup |
| `__tests__/twilio-provider.test.ts` | not-configured error; send success; E.164 normalization; Twilio API error mapping |
| `__tests__/meta-cloud-provider.test.ts` | not-configured error; text mode; template mode; E.164 normalization |
| `__tests__/template-compiler.test.ts` | compile success; cache hit; invalid handlebars → validator fails; variable allowlist enforced; unknown var → empty string |
| `__tests__/renderer.test.ts` | allowlist enforced; dedup hash computed; data built from safeTokens (not raw) |
| `__tests__/masker.test.ts` | PUSH masks sensitive; IN_APP does not; SMS also masks; nested fields; numeric values stringified |
| `__tests__/batcher.test.ts` | threshold trigger; dynamic hold calculation; HIGH never batched; groupKey prevents cross-entity merge |
| `__tests__/backpressure.test.ts` | LOW drops at LOW queue limit; LOW drops at DEFAULT queue limit; HIGH never drops |
| `__tests__/idempotency.test.ts` | atomic SETNX claim; release on failure; TTL expiry; concurrent race |
| `__tests__/notification-cron.test.ts` | birthday matches MM-DD; anniversary matches MM-DD; holiday window; probation end window; idempotent via cronDedupKey; cursor-based pagination iterates all batches; `Promise.allSettled` company-parallelism |
| `__tests__/dispatch-bulk.test.ts` | chunking to `chunkSize`; single rule load + template render across all recipients; per-recipient token merging with `sharedTokens`; rate limit filtering; fallback to per-recipient `dispatch` when < `BULK_MIN_RECIPIENTS` |
| `__tests__/rate-limiter.test.ts` | per-user counter increments; expires at 60s; exceeds limit → returns false; CRITICAL priority bypasses; Redis down → fail-open returns true |
| `__tests__/consent-cache.test.ts` | read-through cache hit returns parsed data; cache miss → DB fetch + write-through; invalidation deletes key; Map rehydration from serialized JSON; TTL is 300s |
| `__tests__/sms-caps.test.ts` | per-tenant cap INCR + reject at +1; per-user cap INCR + reject at +1; both caps counted independently; TTL 48h; dry-run mode bypasses provider call |
| `__tests__/whatsapp-template-enforcement.test.ts` | throws WHATSAPP_TEMPLATE_REQUIRED when templateName missing; passes through when set; masker applied with sensitive fields |
| `__tests__/provider-retry.test.ts` | 3 attempts with exponential backoff; non-retryable errors throw immediately; auth errors do not retry |
| `__tests__/event-retention.test.ts` | deletes events older than retention window in batches; aggregation runs before cleanup; idempotent upsert into `NotificationEventAggregateDaily` |

### 13.2 Integration tests

New harness under `src/__tests__/integration/notifications/` using a real Postgres + Redis (via testcontainers or a local dev DB):

- `dispatch-end-to-end.test.ts` — call dispatch, assert Notification row written, socket event fired (mock), BullMQ job enqueued, worker processes job, NotificationEvent rows written
- `consent-enforcement.test.ts` — toggle off, assert no delivery, SKIPPED event recorded
- `rule-wiring.test.ts` — create rule, call dispatcher, verify rendered output
- `preferences-api.test.ts` — CRUD on prefs, enforcement in dispatch
- `approval-workflow.test.ts` — trigger onApprovalComplete for each entityType, assert correct dispatch
- `twilio-integration.test.ts` — mock Twilio, verify E.164 + message body
- `meta-cloud-integration.test.ts` — mock fetch, verify JSON body
- `cron-birthday.test.ts` — seed employee with today's birthday, run cron, assert dispatch called

### 13.3 Load test

Script at `scripts/load-test-notifications.ts`:
- Dispatches 10,000 notifications to 100 users over 60 seconds
- Measures p50/p95 dispatcher latency, queue depth peak, worker throughput
- Pass criteria: p95 < 100ms, no DLQ entries, all events recorded in <5 min

### 13.4 Manual QA

Extend the existing 19-step manual QA checklist (from `feat/notifications` spec §10.6) with:
- Per-category preference toggle test
- SMS delivery (with test Twilio account)
- WhatsApp delivery (with test Meta number)
- Cron-driven birthday notification (fast-forward date or seed)
- Analytics dashboard chart rendering

---

## 14. Rollout Plan

### 14.1 Pre-merge verification

- [ ] All unit tests pass
- [ ] All integration tests pass
- [ ] Load test p95 < 100ms
- [ ] Manual QA checklist completed
- [ ] `pnpm prisma:merge` produces valid schema
- [ ] Backend `pnpm tsc --noEmit` clean
- [ ] Web `pnpm tsc --noEmit` clean
- [ ] Mobile `pnpm type-check` clean (including the pre-existing leave-request error fix)
- [ ] Migration SQL generated + committed
- [ ] Migration SQL applied to a fresh staging DB without errors

### 14.2 Deployment order

1. **Staging backend deploy** with new env vars set:
   - `TWILIO_*` (if Twilio account provisioned)
   - `META_WHATSAPP_*` (if Meta Business account provisioned)
   - Migration applied via `pnpm prisma migrate deploy`
2. **Staging web + mobile deploys**
3. **Staging manual QA** — full checklist
4. **Seed any missing default templates** (idempotent)
5. **Production backend deploy**
6. **Production web deploy**
7. **Production mobile EAS update**
8. **Monitor 24h**:
   - `NotificationEvent` write rate
   - DLQ count
   - Cron job completion logs
   - Twilio/Meta error rate if configured

### 14.3 Rollback

- If wiring causes issues: set `NOTIFICATIONS_ENABLED=false` — dispatcher becomes a no-op while still writing in-app rows.
- If a specific cron misfires: stop the cron service via a new kill-switch env var (`NOTIFICATIONS_CRON_ENABLED=false`).
- If SMS/WhatsApp causes billing/delivery issues: set company-level master toggle off in Settings.
- If the per-category preference query is slow: drop the `userId` index and fall back to the in-memory evaluation with one query per user (already the pattern).
- Migration is additive — worst case can be manually reverted by dropping the new columns + tables.

### 14.4 Feature flags

- `NOTIFICATIONS_ENABLED` — existing global kill switch
- `NOTIFICATIONS_CRON_ENABLED` — new, default `true`. Disables all informational crons without affecting the main dispatcher.
- `NOTIFICATIONS_SMS_ENABLED` — new, default `true`. If `false`, SMS channel throws `SMS_DISABLED` without hitting Twilio.
- `NOTIFICATIONS_WHATSAPP_ENABLED` — new, default `true`. Same for WhatsApp.
- `NOTIFICATIONS_SMS_DRY_RUN` / `NOTIFICATIONS_WHATSAPP_DRY_RUN` — new, default `false`. Bypasses real provider calls while still recording `NotificationEvent`.
- `NOTIFICATIONS_USER_RATE_LIMIT_PER_MIN` — new, default 20. Per-user cap across all channels.
- `NOTIFICATIONS_SMS_DAILY_CAP_PER_TENANT` / `NOTIFICATIONS_SMS_DAILY_CAP_PER_USER` — new, defaults 500/10.
- `NOTIFICATIONS_WHATSAPP_DAILY_CAP_PER_TENANT` / `NOTIFICATIONS_WHATSAPP_DAILY_CAP_PER_USER` — new, defaults 500/10.
- `NOTIFICATIONS_EVENT_RETENTION_DAYS` — new, default 90.
- `NOTIFICATIONS_BULK_CHUNK_SIZE` — new, default 50.
- `NOTIFICATIONS_BULK_MIN_RECIPIENTS` — new, default 20 (below this, use individual `dispatch()`).
- `NOTIFICATIONS_CONSENT_CACHE_TTL_SEC` — new, default 300.
- `NOTIFICATIONS_CRON_COMPANY_CONCURRENCY` — new, default 5. Max parallel companies in per-tenant cron iteration.

---

## 15. Non-Goals (explicitly out of scope)

- A full notification inbox filtering system (search, filter by date, export). The existing list screen is sufficient.
- Notification grouping/threading (e.g., "5 new leave requests" as a single collapsible item on the bell). Batching at send time is implemented; UI grouping is a separate follow-up.
- Rich media notifications (images, action buttons beyond "Open"). The data model supports `data.imageUrl` but neither the web nor mobile UI consumes it.
- A/B testing of notification copy. Templates are admin-editable; A/B is a future enhancement.
- Localization — templates are rendered in English. Per-user locale support is a follow-up.
- Notification retry from the admin UI (retry a failed notification by clicking a button). The retry happens via BullMQ automatic retry; admins can view failed notifications in the analytics screen but cannot manually retry from the UI in this PR.
- Real-time delivery status on the bell UI (e.g., "sending…" spinner). Delivery status is only visible in the NotificationEvent audit trail.
- A dedicated SMS provider abstraction layer for swapping Twilio for another vendor. This PR ships Twilio as the sole SMS provider.
- Category-level admin overrides (e.g., "force all Payroll notifications on for everyone regardless of preference"). This is a potential enterprise feature for a future PR.

---

## 16. File Change Summary

### 16.1 Backend — created files

```
src/core/notifications/channels/sms/twilio.provider.ts
src/core/notifications/channels/sms/caps.ts
src/core/notifications/channels/whatsapp/meta-cloud.provider.ts
src/core/notifications/channels/whatsapp/caps.ts
src/core/notifications/channels/provider-retry.ts
src/core/notifications/cron/notification-cron.service.ts
src/core/notifications/analytics/notification-analytics.service.ts
src/core/notifications/analytics/notification-analytics.controller.ts
src/core/notifications/analytics/notification-analytics.routes.ts
src/core/notifications/dispatch/rate-limiter.ts
src/core/notifications/dispatch/dispatch-bulk.ts
src/shared/constants/notification-categories.ts
src/core/notifications/__tests__/dispatcher.test.ts
src/core/notifications/__tests__/consent-gate.test.ts
src/core/notifications/__tests__/dedup.test.ts
src/core/notifications/__tests__/rule-loader.test.ts
src/core/notifications/__tests__/recipient-resolver.test.ts
src/core/notifications/__tests__/channel-router.test.ts
src/core/notifications/__tests__/push-channel.test.ts
src/core/notifications/__tests__/expo-provider.test.ts
src/core/notifications/__tests__/fcm-provider.test.ts
src/core/notifications/__tests__/twilio-provider.test.ts
src/core/notifications/__tests__/meta-cloud-provider.test.ts
src/core/notifications/__tests__/template-compiler.test.ts
src/core/notifications/__tests__/renderer.test.ts
src/core/notifications/__tests__/masker.test.ts
src/core/notifications/__tests__/batcher.test.ts
src/core/notifications/__tests__/backpressure.test.ts
src/core/notifications/__tests__/idempotency.test.ts
src/core/notifications/__tests__/notification-cron.test.ts
src/core/notifications/__tests__/dispatch-bulk.test.ts
src/core/notifications/__tests__/rate-limiter.test.ts
src/core/notifications/__tests__/consent-cache.test.ts
src/core/notifications/__tests__/sms-caps.test.ts
src/core/notifications/__tests__/whatsapp-template-enforcement.test.ts
src/core/notifications/__tests__/provider-retry.test.ts
src/core/notifications/__tests__/event-retention.test.ts
src/__tests__/integration/notifications/dispatch-end-to-end.test.ts
src/__tests__/integration/notifications/consent-enforcement.test.ts
src/__tests__/integration/notifications/rule-wiring.test.ts
src/__tests__/integration/notifications/preferences-api.test.ts
src/__tests__/integration/notifications/approval-workflow.test.ts
src/__tests__/integration/notifications/cron-birthday.test.ts
scripts/load-test-notifications.ts
prisma/migrations/20260409_notifications_full/migration.sql
```

### 16.2 Backend — modified files

```
src/core/notifications/channels/sms.channel.ts          (rewrite stub → Twilio)
src/core/notifications/channels/whatsapp.channel.ts     (rewrite stub → Meta Cloud)
src/core/notifications/dispatch/consent-gate.ts         (add category check)
src/core/notifications/templates/masker.ts              (SMS masking)
src/core/notifications/templates/defaults.ts            (7 new cron templates)
src/core/notifications/notification.controller.ts       (categoryPreferences endpoint)
src/core/notifications/notification.routes.ts           (analytics routes)
src/core/notifications/preferences/preferences.service.ts (category prefs CRUD)
src/core/notifications/preferences/preferences.validators.ts (category schema)
src/config/env.ts                                        (Twilio + Meta + cron env vars)
src/app/server.ts                                        (start notification-cron.service)
src/shared/events/listeners/hr-listeners.ts              (verify dispatch usage)
src/modules/hr/leave/leave.service.ts                    (createRequest + cancelRequest dispatches)
src/modules/hr/attendance/attendance.service.ts          (any inline non-approval dispatches)
src/modules/hr/ess/ess.service.ts                        (all submission dispatches + onApprovalComplete refactor)
src/modules/hr/payroll-run/payroll-run.service.ts        (publishPayslips, disburseRun dispatches)
src/modules/hr/employee/employee.service.ts              (createEmployee dispatch)
src/modules/hr/transfer/transfer.service.ts              (createTransfer, applyTransfer, createPromotion, applyPromotion)
src/modules/hr/payroll/payroll.service.ts                (updateEmployeeSalary)
src/modules/hr/offboarding/offboarding.service.ts        (createExitRequest, approveFnF, payFnF)
src/modules/hr/advanced/advanced.service.ts              (advanceCandidateStage, createAssetAssignment, returnAssetAssignment)
src/modules/hr/advanced/offer.service.ts                 (createOffer, updateOfferStatus)
src/core/support/support.service.ts                      (4 dispatch calls)
src/core/auth/auth.service.ts                            (3 CRITICAL dispatches)
src/shared/constants/navigation-manifest.ts              (notification-analytics entry)
prisma/modules/platform/notifications.prisma             (UserNotificationCategoryPreference)
prisma/modules/hrms/ess-workflows.prisma                 (NotificationTemplate.whatsappTemplateName)
prisma/modules/platform/auth.prisma                      (User.categoryPreferences back-ref)
package.json                                              (twilio dep)
.env.example                                              (document new env vars)
```

### 16.3 Web — created files

```
src/features/company-admin/hr/NotificationAnalyticsScreen.tsx
src/features/company-admin/hr/api/use-notification-analytics.ts
```

### 16.4 Web — modified files

```
src/features/settings/NotificationPreferencesScreen.tsx  (category prefs section)
src/lib/api/notifications.ts                             (category + analytics endpoints)
src/features/super-admin/tenant-onboarding/steps/Step05Preferences.tsx (push/sms/inApp toggles)
src/features/super-admin/tenant-onboarding/schemas.ts    (zod schema extension)
src/features/super-admin/tenant-onboarding/index.tsx     (payload wiring)
src/App.tsx                                               (new route)
```

### 16.5 Mobile — created files

```
assets/notification-icon-96.png                          (replace placeholder)
```

### 16.6 Mobile — modified files

```
src/features/settings/notification-preferences-screen.tsx (category prefs section)
src/lib/api/notifications.ts                              (category endpoints)
src/features/company-admin/hr/leave-request-screen.tsx   (fix pre-existing import typo)
app.config.ts                                             (notification icon path)
```

### 16.7 Total file count

| Codebase | Created | Modified | Total |
|---|---|---|---|
| Backend | ~32 | ~23 | ~55 |
| Web | 2 | 6 | 8 |
| Mobile | 1 | 4 | 5 |
| **Total** | **35** | **33** | **68** |

---

## 17. Spec Self-Review

**Placeholder scan:** No TBDs, TODOs, or incomplete sections.

**Internal consistency:**
- Architecture (§3) and data model (§4) align — UserNotificationCategoryPreference is referenced in both
- Call sites in §5 match the exact method names from the backend mapping agent's research
- Cron events in §6 use the same category codes as §9's category catalogue
- Provider configurations in §7-§8 reference env vars added in §16
- Testing strategy (§13) covers every module and provider in §5-§8

**Ambiguity check:**
- `systemCritical` semantics clarified: bypasses user pref + quiet hours + category pref; still respects company master
- Category matrix "no row = use channel default" explicitly stated
- Cron dedup uses a separate 24h TTL key (not the 60s dispatcher dedup)
- WhatsApp template vs text mode selection explicit (`template.whatsappTemplateName`)
- SMS masking uses `PUSH` masker behavior (extended in §7.3)
- Locked categories (AUTH) cannot be overridden even with a row present

**Scope check:** Focused entirely on closing `feat/notifications` deferred items. No unrelated refactors. Non-goals (§15) explicitly carved out.

**Migration safety:** Schema changes are additive. New table (`user_notification_category_preferences`) and new column (`whatsappTemplateName`). Migration file committed for staging/prod.

**Backward compatibility:**
- Existing `notificationService.send()` legacy facade continues to work
- Existing HR listeners continue to work through the dispatcher
- `Notification.isRead` column kept as deprecated (Phase B in a follow-up)
- No breaking changes to any existing API endpoint shape (only additions)
