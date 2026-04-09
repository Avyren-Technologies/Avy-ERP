# Push Notifications Overhaul — Design Spec

**Status:** Approved
**Author:** Chetan (product owner) + Claude (architect)
**Date:** 2026-04-09
**Scope:** Backend, web (`web-system-app`), mobile (`mobile-app`)
**Prerequisites:** FCM V1 Google Service Account uploaded to EAS (completed), APNs key uploaded to EAS (completed), `FIREBASE_SERVICE_ACCOUNT_KEY` present in backend `.env` (completed)

---

## 1. Executive Summary

The current push notification system has six critical gaps that render mobile push delivery non-functional, leave admin-configurable `NotificationRule` records purely cosmetic for every channel except email, fail to enforce the notification toggles already present in the frontend, poll for bell-icon updates instead of using the Socket.io infrastructure that already exists, and have no observability into delivery outcomes.

This spec describes a full overhaul that:

1. Fixes the mobile Firebase-not-initialized error by relying on Expo's managed FCM V1 path (credentials already uploaded).
2. Fixes the latent backend bug where Expo push tokens were sent to raw FCM (which silently fails).
3. Introduces a single `notificationService.dispatch()` entry point that every caller uses.
4. Implements a two-tier consent model (company master toggles + per-user preferences) with a `SYSTEM_CRITICAL` override for security/legal notifications.
5. Unifies the rule engine so `NotificationTemplate` and `NotificationRule` actually drive every channel, not just email.
6. Adds an async BullMQ delivery pipeline with priority-partitioned queues, retry + DLQ, dedup, idempotency, rate limiting, batching, backpressure, and analytics.
7. Replaces 30s polling with instant Socket.io `notification:new` events.
8. Adds per-user notification preferences screens on web and mobile.
9. Wires every approval-workflow and ESS submission site into the dispatcher.
10. Captures delivery analytics into a new `NotificationEvent` table, with Expo receipt polling for final delivery status.

The implementation is delivered in a single PR. All schema changes are additive and zero-downtime. Legacy callers of `notificationService.send()` continue to work via a thin facade that internally calls `dispatch()`.

---

## 2. Current State — Gaps Confirmed

### 2.1 Mobile push is non-functional (blocking)

Running `getExpoPushTokenAsync({ projectId })` on a physical Android device (managed Expo workflow, SDK 54) throws:

```
Default FirebaseApp is not initialized in this process com.avyren.erp.development.
Make sure to call FirebaseApp.initializeApp(Context) first.
```

**Root cause:** Expo SDK 53+ requires FCM V1 credentials to be uploaded to EAS. Without the upload, Expo's native notification service cannot initialize FirebaseApp on Android. Expo Go cannot receive push on SDK 53+ because it does not bundle Firebase.

**Status:** User has completed the FCM V1 Google Service Account upload via `eas credentials` and rebuilt the development client. The spec assumes this is done.

### 2.2 Backend silently drops all mobile pushes (latent, critical)

`src/core/notifications/notification.service.ts:99` calls `messaging.sendEachForMulticast()` from `firebase-admin` with tokens that mobile clients registered via `Notifications.getExpoPushTokenAsync()`. Those are Expo push tokens (`ExponentPushToken[...]`), which FCM cannot process. The error is caught and swallowed:

```typescript
} catch (err) {
  logger.error('FCM push failed', { error: err });
  // Don't throw — push failure shouldn't break the main flow
}
```

**Impact:** No mobile push has ever actually been delivered. The in-app row is written correctly, so users see bell-icon notifications, but nothing ever hits their lock screen.

### 2.3 Frontend toggles are purely cosmetic

`CompanySettings.emailNotifications` and `whatsappNotifications` exist in the schema (`prisma/modules/company-admin/settings.prisma:28-29`) and are wired in `CompanySettingsScreen.tsx` and the tenant-onboarding `Step05Preferences.tsx`. However, nothing in the backend send path checks these toggles. `pushNotifications`, `smsNotifications`, and `inAppNotifications` do not exist at all. There are no per-user preferences.

### 2.4 Rule engine only delivers email

`src/modules/hr/ess/ess.service.ts:1180` (`triggerNotification()`) is the rule-driven entry point. It only implements the EMAIL branch. PUSH, IN_APP, SMS, and WHATSAPP branches just log:

```typescript
// lines 1209-1230 roughly
if (rule.channel === 'EMAIL') { /* actually sends */ }
else { logger.info('Other channel not yet implemented'); }
```

The admin UI (`NotificationRuleScreen.tsx`, `NotificationTemplateScreen.tsx`) exposes PUSH/IN_APP/SMS/WHATSAPP as selectable channels, but they are no-ops.

### 2.5 Event coverage is minimal

Only four HR events actually call `notificationService.send()`:

- `INTERVIEW_SCHEDULED` → notify panelists (`hr-listeners.ts:27-41`)
- `TRAINING_NOMINATION` → notify employee (`hr-listeners.ts:49-60`)
- `TRAINING_COMPLETED` → notify employee (`hr-listeners.ts:63-74`)
- `CERTIFICATE_EXPIRING` → notify employee (`hr-listeners.ts:77-88`)

Every other trigger event listed in `src/shared/constants/trigger-events.ts` (leave, attendance, overtime, reimbursement, loan, resignation, transfer, promotion, salary revision, IT declaration, travel, payroll approval, bonus, asset issuance, training request, etc.) has no wiring, even though admins can configure rules for them.

### 2.6 Real-time is missing

The web and mobile bell icons poll `GET /notifications/unread-count` every 30 seconds. Socket.io exists and is authenticated per-user via JWT, but it is used only for support ticket rooms. New notifications can lag up to 30 seconds behind reality. Mobile has no Socket.io client at all.

### 2.7 No observability

There is no record of whether a push was actually delivered. No analytics table, no ticket tracking, no receipt polling, no per-channel delivery status, no trace IDs for debugging a specific notification end-to-end. Failures are logged but not queryable.

### 2.8 Other gaps

- `FIREBASE_SERVICE_ACCOUNT_KEY` is used at runtime but not validated in `src/config/env.ts`.
- No retry policy — push failures are fire-and-forget without exponential backoff.
- No dedup — a service retry can send the same notification multiple times.
- No rate limiting — a mass-update could spam a single user with 100 notifications.
- No batching — 20 approvals in 5 minutes produce 20 notifications instead of a summary.
- No token lifecycle — `UserDevice` is hard-deleted on failure instead of soft-deactivated with metadata.
- No template compilation safety — broken handlebars would crash at dispatch time.
- No sensitive-data masking — a salary amount currently appears in push lock-screen text.

---

## 3. Architecture

### 3.1 Guiding principles

1. **Single sync entry point.** Every notification goes through `notificationService.dispatch()`. Business code never touches FCM, Expo SDK, `Notification` rows, or socket events directly.
2. **Sync write, async deliver.** `dispatch()` writes the in-app row and enqueues a BullMQ job, then returns in <50ms. All push/email/SMS delivery happens in worker processes with retry, DLQ, and observability.
3. **Two-tier consent with critical override.** A channel is delivered iff `companyMasterToggle AND userPreference AND NOT quietHours`. `SYSTEM_CRITICAL` priority bypasses `userPreference` and `quietHours` but still respects `companyMasterToggle` (for legal compliance on WhatsApp/SMS).
4. **In-app is the system of record.** Every notification writes a `Notification` row regardless of any toggle. The bell icon is the source of truth. All other channels are delivery layers on top of that record.
5. **Dual-transport push via a router.** `ExponentPushToken[...]` → Expo Server SDK. Raw FCM tokens → `firebase-admin`. Callers don't know or care which is used.
6. **Socket.io is a UI hint, not a data source.** Clients receive `notification:new` with only `{ notificationId, unreadCountHint: null }` and must re-fetch via React Query. Never append the socket payload directly to state.
7. **Dedup at dispatch, idempotency at worker.** Dispatch-level dedup prevents duplicate enqueues using a payload-hash key with 60s TTL. Worker-level idempotency prevents duplicate sends during BullMQ retry using a 24h TTL key.
8. **Rule-driven with built-in fallback.** `dispatch()` loads active `NotificationRule`s for the trigger event. If none exist, it falls back to a built-in default template shipped in code, so notifications are never silently dropped.
9. **Full observability.** Every dispatch produces a `traceId` that flows through all logs, `NotificationEvent` rows, and socket payloads. Every channel delivery produces one or more `NotificationEvent` rows (`ENQUEUED`, `SENT`, `DELIVERED`, `OPENED`, `FAILED`, etc.).
10. **Business logic never breaks.** `dispatch()` catches every error internally. Callers can safely `await` it without wrapping in try/catch.

### 3.2 High-level flow

```
                     ┌──────────────────────────────────────────┐
                     │      notificationService.dispatch(input) │
                     │      (sync, <50ms, never throws)         │
                     └────────────────┬─────────────────────────┘
                                      │
          SYNCHRONOUS PHASE           │
                                      ▼
                   ┌────────────────────────────────┐
                   │ 1. Generate traceId            │
                   │ 2. Load rules + templates      │
                   │ 3. Resolve recipients          │
                   │ 4. Dedup check (payload hash)  │
                   │ 5. Backpressure guard          │
                   │ 6. Write Notification rows     │
                   │ 7. Emit socket 'notification:new' │
                   │ 8. Enqueue BullMQ job          │
                   └────────────────┬───────────────┘
                                    │
                                    ▼
                         ┌──────────────────────┐
                         │  Priority router     │
                         └──┬───────┬───────┬───┘
                            │       │       │
                            ▼       ▼       ▼
                  notifications:high   default   low
                            │       │       │
          ASYNCHRONOUS PHASE│       │       │
                            ▼       ▼       ▼
                   ┌────────────────────────────────┐
                   │  BullMQ workers (3 queues)     │
                   │  rate-limited per user+channel │
                   │  retry 3×, exponential backoff │
                   │  failed → notifications-dlq    │
                   └────────────────┬───────────────┘
                                    │
                                    ▼
                   ┌────────────────────────────────┐
                   │ Per (recipient, channel):      │
                   │  A. Worker idempotency SETNX   │
                   │  B. Re-check consent           │
                   │  C. Channel dispatch           │
                   │  D. Token lifecycle            │
                   │  E. Update deliveryStatus      │
                   │  F. Write NotificationEvent    │
                   └────────────────┬───────────────┘
                                    │
                                    ▼
                         ┌──────────────────────┐
                         │  Channel router      │
                         └──┬───┬───┬───┬───┬───┘
                            │   │   │   │   │
                            ▼   ▼   ▼   ▼   ▼
                         IN_APP PUSH EMAIL SMS WHATSAPP
                                │
                                ▼
                         ┌──────────────────┐
                         │ Push router      │
                         │  ExpoToken → Expo│
                         │  FCM token → FCM │
                         └──────────────────┘

          SEPARATE REPEATABLE JOBS:
          ────────────────────────
          notifications:receipts     — every 30s, polls Expo receipts for 15min window
          notifications:dlq-sweep    — hourly, drops DLQ entries >7 days old
          notifications:batch-flush  — triggered by dispatcher when batching threshold hit
```

### 3.3 Architectural rules (final, locked)

1. **Single sync entry point** — `dispatch()` is synchronous, writes in-app row + enqueues, returns in <50ms. Never awaits push/email providers. A `traceId` (nanoid 12-char) propagates through every log and event.

2. **Rule + template versioning** — `NotificationRule` and `NotificationTemplate` have a `version` integer, auto-incremented on update. The `Notification` row stores `ruleId`, `ruleVersion`, `templateId`, `templateVersion` for historical debugging.

3. **Two-tier consent with SYSTEM_CRITICAL** — Channel delivers iff `companyMasterToggle AND userPreference AND NOT quietHours`. `priority = CRITICAL` bypasses `userPreference` and `quietHours`. It still respects `companyMasterToggle` for WhatsApp/SMS legal compliance.

4. **In-app row as system of record** — Every notification writes a `Notification` row unconditionally. The row has a `status` (`UNREAD | READ | ARCHIVED`), a `priority` (`LOW | MEDIUM | HIGH | CRITICAL`), and a JSON `deliveryStatus` map tracking per-channel state (`PENDING | SENT | FAILED | SKIPPED | BOUNCED | RETRYING`).

5. **Dual-transport push + token metadata** — `UserDevice` is extended with `tokenType` (`EXPO | FCM_WEB | FCM_NATIVE`), `isActive`, `failureCount`, `lastSuccessAt`, `lastFailureAt`, `lastFailureCode`, `deviceModel`, `osVersion`, `appVersion`, `locale`, `timezone`. Failed tokens are soft-deactivated after 5 consecutive failures or immediately on `DeviceNotRegistered`.

6. **Socket.io is a UI hint only** — Payload is `{ notificationId, unreadCountHint: null }`. Clients invalidate React Query keys and re-fetch. Never append.

7. **Dedup with payload hash** — Key: `notif:dedup:{companyId}:{triggerEvent}:{entityType}:{entityId}:{recipientId}:{sha1(title+body+canonicalJSON(data))}`. TTL 60s (configurable).

8. **Retry, DLQ, observability** — BullMQ jobs retry 3× with exponential backoff (2s, 8s, 30s). Failed jobs move to `notifications-dlq`. A DLQ sweeper removes entries older than 7 days hourly.

9. **Rate limiting** — BullMQ worker `limiter: { max: 20, duration: 60_000, groupKey: 'userId' }`. Max 20 notifications per user per minute across all channels. Additional global cap `{ max: 50, duration: 1000 }` per worker for provider safety.

10. **Batching (LOW/MEDIUM only)** — Redis sorted set `notif:batch:{userId}:{category}:{entityType}` tracks pending count in a 5-minute sliding window. If count ≥ 5, new jobs enqueue with `delay = min(60_000, pendingCount × 5000)` ms. A `flush-batch` job with a stable `jobId` (idempotent) coalesces held notifications into a single summary (e.g., "You have 8 new leave requests awaiting review"). `HIGH`/`CRITICAL` are never batched.

11. **Analytics via `NotificationEvent`** — Append-only table with `notificationId`, `channel`, `event`, `provider`, `providerMessageId`, `expoTicketId`, `receiptCheckedAt`, `receiptStatus`, `source` (`SYSTEM | USER_ACTION | RETRY`), `errorCode`, `errorMessage`, `metadata`, `traceId`, `occurredAt`. Dashboard UI deferred to a follow-up PR.

12. **Fire-and-forget at caller level** — Business code awaits `dispatch()` without try/catch. Dispatcher catches everything internally and returns a result object.

13. **Bull + BullMQ coexist** — BullMQ uses `prefix: 'bullmq'`, Bull uses `prefix: 'bull'`. Separate namespaces in the same Redis instance. Existing `analytics` and `reports` Bull queues untouched.

14. **Dynamic batching hold** — `holdMs = Math.min(60_000, pendingCount × 5_000)`. `groupKey = userId + category + entityType`. Never merge across entity types.

15. **Source tagging in analytics** — Every `NotificationEvent` carries a `source` field: `SYSTEM` for first-time sends, `RETRY` for BullMQ retries, `USER_ACTION` for admin-triggered test sends.

16. **Expo receipt polling** — Repeatable BullMQ job `notifications:receipts` runs every 30 seconds. It polls Expo for `expoTicketId`s that have `receiptCheckedAt = null` and `occurredAt >= now() - 15 minutes`. After 15 minutes, unchecked tickets are marked `UNKNOWN` and left alone. Delivered receipts emit a `DELIVERED` event; errors emit `BOUNCED` (`DeviceNotRegistered`) or `FAILED` (other).

17. **Worker idempotency** — Redis `SET NX EX 86400` on key `notif:sent:{notificationId}:{channel}`. Worker checks before send, skips if already set. Prevents BullMQ retry from sending twice after a partial success.

18. **Priority-partitioned queues** — Three BullMQ queues: `notifications:high` (concurrency 20), `notifications:default` (concurrency 10), `notifications:low` (concurrency 5). Routing: CRITICAL + HIGH → high, MEDIUM → default, LOW → low.

19. **Backpressure** — Before enqueue, check queue depth via `queue.getWaitingCount()`. Limits: `MAX_QUEUE_LOW=10_000`, `MAX_QUEUE_DEFAULT=50_000`, high queue never drops. Over-limit LOW jobs are logged as `SKIPPED_BACKPRESSURE` in `NotificationEvent` and never enqueued. Over-limit on `default` drops incoming LOW jobs only. HIGH/CRITICAL never drop — they alert via logger instead.

20. **Template compilation safety** — Templates pre-compiled with `handlebars`. Compilation errors caught at `NotificationTemplate` save time via Zod `.refine()` validator. Variable allowlist (`template.variables: string[]`) enforced at render time; unknown vars render as empty strings. `compiledBody` and `compiledSubject` cached on the template row; recompiled on update or on worker startup.

21. **Multi-device strategy** — Default: send to all active devices per user. Configurable per user via `UserNotificationPreference.deviceStrategy` (`ALL | LATEST_ONLY`). `LATEST_ONLY` uses `lastActiveAt` to pick the most recent device.

22. **Sensitive data masking** — `NotificationTemplate.sensitiveFields: string[]` declares which token fields are sensitive (e.g., `['amount', 'accountNumber']`). On PUSH channel, these fields are replaced with `***` in title, body, and data payload. The in-app row keeps the full unmasked version. User must open the app to see the details. Applied via `maskForChannel(channel, rendered, sensitiveFields)`.

### 3.4 Non-goals (out of scope for this PR)

- SMS provider integration (Twilio). The channel exists as a stub that throws `NotImplemented`.
- WhatsApp provider integration (Meta Cloud API). Same — stub.
- Birthday, work-anniversary, holiday-reminder cron jobs. Deferred to a follow-up.
- Announcement-board event wiring. Deferred to a follow-up.
- Per-category user preferences (leave vs payroll vs training). Current design is per-channel only; categories are tracked on the `Notification` row for future use.
- Analytics dashboard UI. The `NotificationEvent` table is populated from day one, but the visualization is a follow-up.
- Migration of existing Bull queues (`analytics`, `reports`) to BullMQ. They stay on Bull.
- Deprecation and drop of `Notification.isRead` field. It stays for backward compat; a follow-up PR drops it once all read paths use `status`.

---

## 4. Data Model

All schema changes are additive. Three files in `prisma/modules/` are edited. `prisma/schema.prisma` is regenerated via `pnpm prisma:merge`. Never edited directly.

### 4.1 `prisma/modules/platform/notifications.prisma`

```prisma
// ==========================================
// Platform — Notifications
// ==========================================

model Notification {
  id              String               @id @default(cuid())
  userId          String
  companyId       String

  // Content
  title           String
  body            String
  type            String               // HR | PAYROLL | LEAVE | ATTENDANCE | SUPPORT | SYSTEM | ...
  category        String?              // finer grouping used for batching (e.g. 'LEAVE_APPROVAL')
  entityType      String?
  entityId        String?
  data            Json?                // full unmasked payload
  actionUrl       String?              // deep link for web/mobile on tap

  // Lifecycle
  status          NotificationStatus   @default(UNREAD)
  priority        NotificationPriority @default(MEDIUM)
  isRead          Boolean              @default(false)  // kept for backward compat, redundant with status
  readAt          DateTime?
  archivedAt      DateTime?

  // Delivery tracking — snapshot of per-channel state
  deliveryStatus  Json                 @default("{}")
  // { inApp: 'SENT', push: 'SENT'|'FAILED'|'SKIPPED'|'BOUNCED'|'PENDING'|'RETRYING', email: ..., sms: ..., whatsapp: ... }

  // Provenance (debugging + audit)
  traceId         String
  ruleId          String?
  ruleVersion     Int?
  templateId      String?
  templateVersion Int?
  dedupHash       String               // sha1 of canonical payload

  // Relations
  user            User                 @relation("NotificationUser", fields: [userId], references: [id], onDelete: Cascade)
  company         Company              @relation(fields: [companyId], references: [id], onDelete: Cascade)
  events          NotificationEvent[]

  createdAt       DateTime             @default(now())
  updatedAt       DateTime             @updatedAt

  @@index([userId, status])
  @@index([userId, isRead])
  @@index([companyId, createdAt])
  @@index([traceId])
  @@index([dedupHash])
  @@map("notifications")
}

model UserDevice {
  id              String           @id @default(cuid())
  userId          String
  platform        String           // MOBILE_IOS | MOBILE_ANDROID | WEB
  fcmToken        String            // holds Expo or FCM tokens; legacy column name kept for compat
  tokenType       DeviceTokenType  @default(EXPO)

  // Device metadata
  deviceName      String?
  deviceModel     String?
  osVersion       String?
  appVersion      String?
  locale          String?
  timezone        String?

  // Lifecycle
  isActive        Boolean          @default(true)
  failureCount    Int              @default(0)
  lastSuccessAt   DateTime?
  lastFailureAt   DateTime?
  lastFailureCode String?
  lastActiveAt    DateTime         @default(now())

  createdAt       DateTime         @default(now())
  updatedAt       DateTime         @updatedAt
  user            User             @relation("UserDeviceUser", fields: [userId], references: [id], onDelete: Cascade)

  @@unique([userId, fcmToken])
  @@index([userId, isActive])
  @@index([tokenType, isActive])
  @@map("user_devices")
}

model NotificationEvent {
  id                String                @id @default(cuid())
  notificationId    String
  notification      Notification          @relation(fields: [notificationId], references: [id], onDelete: Cascade)

  channel           NotificationChannel
  event             NotificationEventType

  provider          String?               // 'expo' | 'fcm' | 'smtp' | 'twilio' | 'meta'
  providerMessageId String?
  expoTicketId      String?
  receiptCheckedAt  DateTime?
  receiptStatus     String?               // 'ok' | 'error' | 'unknown'

  source            NotificationSource    @default(SYSTEM)

  errorCode         String?
  errorMessage      String?
  metadata          Json?
  traceId           String

  occurredAt        DateTime              @default(now())

  @@index([notificationId])
  @@index([traceId])
  @@index([event, occurredAt])
  @@index([provider, expoTicketId])
  @@map("notification_events")
}

model UserNotificationPreference {
  id                String         @id @default(cuid())
  userId            String         @unique

  // Channel opt-in
  inAppEnabled      Boolean        @default(true)
  pushEnabled       Boolean        @default(true)
  emailEnabled      Boolean        @default(true)
  smsEnabled        Boolean        @default(true)
  whatsappEnabled   Boolean        @default(true)

  // Device delivery strategy
  deviceStrategy    DeviceStrategy @default(ALL)

  // Quiet hours (local time string "HH:mm", uses user timezone when set, else company tz)
  quietHoursEnabled Boolean        @default(false)
  quietHoursStart   String?
  quietHoursEnd     String?

  user              User           @relation("UserNotificationPrefUser", fields: [userId], references: [id], onDelete: Cascade)
  createdAt         DateTime       @default(now())
  updatedAt         DateTime       @updatedAt

  @@map("user_notification_preferences")
}

enum NotificationStatus {
  UNREAD
  READ
  ARCHIVED
}

enum NotificationPriority {
  LOW
  MEDIUM
  HIGH
  CRITICAL
}

enum DeviceTokenType {
  EXPO
  FCM_WEB
  FCM_NATIVE
}

enum NotificationEventType {
  ENQUEUED
  SENT
  DELIVERED
  OPENED
  CLICKED
  FAILED
  BOUNCED
  SKIPPED
  RETRYING
}

enum NotificationSource {
  SYSTEM
  USER_ACTION
  RETRY
}

enum DeviceStrategy {
  ALL
  LATEST_ONLY
}
```

**Note:** `NotificationChannel` enum already exists in `prisma/modules/hrms/ess-workflows.prisma` (`EMAIL | SMS | PUSH | IN_APP | WHATSAPP`). `NotificationEvent.channel` references it. No duplication.

### 4.2 `prisma/modules/company-admin/settings.prisma` — additions

```prisma
model CompanySettings {
  // ... existing fields unchanged ...

  // Notification channel master switches
  emailNotifications    Boolean @default(true)    // existing
  whatsappNotifications Boolean @default(false)   // existing
  pushNotifications     Boolean @default(true)    // NEW
  smsNotifications      Boolean @default(false)   // NEW
  inAppNotifications    Boolean @default(true)    // NEW (cosmetic gate; DB rows always written)

  // ... rest unchanged ...
}
```

Enforcement: `channel delivered ≡ company_master AND user_pref AND NOT quietHours(for non-critical)`. `SYSTEM_CRITICAL` bypasses `user_pref` and `quietHours`, not `company_master`.

### 4.3 `prisma/modules/hrms/ess-workflows.prisma` — modifications

```prisma
model NotificationTemplate {
  id              String               @id @default(cuid())
  name            String
  code            String               // NEW — stable machine code, e.g. 'LEAVE_SUBMITTED'
  subject         String?
  body            String                // handlebars source
  channel         NotificationChannel  @default(EMAIL)
  priority        NotificationPriority @default(MEDIUM)  // NEW
  version         Int                  @default(1)        // NEW — auto-inc on update via service layer

  // Template safety
  variables       Json                 @default("[]")     // NEW — allowlist: ['employee_name', 'leave_days']
  sensitiveFields Json                 @default("[]")     // NEW — masked on PUSH: ['amount', 'account_number']
  compiledBody    String?                                 // NEW — pre-compiled cache
  compiledSubject String?                                 // NEW

  // System defaults
  isSystem        Boolean              @default(false)    // NEW — seeded by platform, editable by tenant
  isActive        Boolean              @default(true)

  companyId       String
  company         Company              @relation(fields: [companyId], references: [id], onDelete: Cascade)
  createdAt       DateTime             @default(now())
  updatedAt       DateTime             @updatedAt

  rules           NotificationRule[]

  @@unique([companyId, code, channel])                    // NEW
  @@map("notification_templates")
}

model NotificationRule {
  id            String               @id @default(cuid())
  triggerEvent  String
  category      String?              // NEW — batching groupKey
  templateId    String
  template      NotificationTemplate @relation(fields: [templateId], references: [id], onDelete: Cascade)
  recipientRole String               // EMPLOYEE | MANAGER | HR | FINANCE | IT | ADMIN | REQUESTER | APPROVER | ALL
  channel       NotificationChannel  @default(EMAIL)
  priority      NotificationPriority @default(MEDIUM)    // NEW — overrides template default
  version       Int                  @default(1)          // NEW

  isSystem      Boolean              @default(false)     // NEW
  isActive      Boolean              @default(true)
  companyId     String
  company       Company              @relation(fields: [companyId], references: [id], onDelete: Cascade)
  createdAt     DateTime             @default(now())
  updatedAt     DateTime             @updatedAt

  @@index([companyId, triggerEvent, isActive])           // NEW — hot path
  @@map("notification_rules")
}
```

### 4.4 Migration plan (zero-downtime, 4 stages)

**Migration A — additive schema:**
- Add all new columns with defaults. Add new tables. Add new enums.
- Runs on deploy. Safe without app restart.

**Migration B — data backfill (SQL, run once after deploy):**
- `UPDATE notifications SET status = CASE WHEN isRead THEN 'READ' ELSE 'UNREAD' END, traceId = id WHERE status IS NULL;`
- `UPDATE notification_templates SET code = LOWER(REGEXP_REPLACE(name, '[^a-zA-Z0-9]+', '_', 'g')) WHERE code IS NULL;`
- `UPDATE user_devices SET tokenType = CASE WHEN fcmToken LIKE 'ExponentPushToken[%' THEN 'EXPO' WHEN platform = 'WEB' THEN 'FCM_WEB' ELSE 'EXPO' END WHERE tokenType IS NULL;`
- `UPDATE notification_templates SET compiledBody = body WHERE compiledBody IS NULL;`

**Migration C — seed default templates (per company):**
- A TypeScript migration script (`prisma/seeds/2026-04-09-seed-default-notification-templates.ts`) iterates every existing `Company` and idempotently creates the default template set (see §7.4). Skip if `(companyId, code, channel)` already exists. The same function runs automatically on new tenant provisioning via a hook in `company.service.createCompany()`.

**Migration D — deferred cleanup:**
- Drop `Notification.isRead` once all read paths use `status`. Out of scope for this PR.

### 4.5 Index strategy

| Table | Index | Purpose |
|---|---|---|
| `notifications` | `(userId, status)` | bell list query, filter by read state |
| `notifications` | `(userId, isRead)` | backward compat |
| `notifications` | `(companyId, createdAt)` | admin audit, analytics time range |
| `notifications` | `traceId` | trace debugging |
| `notifications` | `dedupHash` | dedup verification |
| `notification_events` | `notificationId` | event history per notification |
| `notification_events` | `traceId` | end-to-end trace lookup |
| `notification_events` | `(event, occurredAt)` | analytics aggregations |
| `notification_events` | `(provider, expoTicketId)` | receipt polling hot path |
| `user_devices` | `(userId, isActive)` | dispatcher device lookup |
| `user_devices` | `(tokenType, isActive)` | channel router partitioning |
| `notification_rules` | `(companyId, triggerEvent, isActive)` | rule loader hot path |
| `notification_templates` | `(companyId, code, channel)` unique | idempotent seeding |
| `user_notification_preferences` | `userId` unique | dispatcher consent check |

---

## 5. Backend Implementation

### 5.1 Directory layout

```
src/core/notifications/
├── index.ts                              # barrel export
├── notification.service.ts               # EXISTING — thin facade, delegates to dispatch()
├── notification.controller.ts            # EXISTING — extended with new endpoints
├── notification.routes.ts                # EXISTING — extended
├── notification.validators.ts            # NEW — Zod schemas
│
├── dispatch/
│   ├── dispatcher.ts                     # NEW — main dispatch() entry point
│   ├── types.ts                          # NEW — DispatchInput, DispatchResult, DispatchContext
│   ├── dedup.ts                          # NEW — Redis dedup key check
│   ├── recipient-resolver.ts             # NEW — recipientRole → userIds[]
│   ├── rule-loader.ts                    # NEW — load + cache rules per company
│   ├── consent-gate.ts                   # NEW — company + user pref + quiet-hours check
│   ├── backpressure.ts                   # NEW — queue depth guard
│   └── priority-router.ts                # NEW — priority → queue name
│
├── queue/
│   ├── queues.ts                         # NEW — 3 priority queues + DLQ + receipts
│   ├── connection.ts                     # NEW — shared ioredis connection for BullMQ
│   └── rate-limiter-config.ts            # NEW — BullMQ limiter presets
│
├── workers/
│   ├── notification.worker.ts            # REWRITTEN — consumes 3 queues
│   ├── receipt-poller.worker.ts          # NEW — Expo receipts repeatable
│   ├── dlq-sweeper.worker.ts             # NEW — cleans DLQ >7d
│   └── batcher.worker.ts                 # NEW — coalesces held jobs (flush-batch)
│
├── channels/
│   ├── channel-router.ts                 # NEW — dispatches to right provider
│   ├── in-app.channel.ts                 # NEW — updates deliveryStatus (no-op send)
│   ├── push/
│   │   ├── push.channel.ts               # NEW — picks Expo or FCM based on tokenType
│   │   ├── expo.provider.ts              # NEW — Expo Server SDK wrapper
│   │   └── fcm.provider.ts               # NEW — firebase-admin wrapper
│   ├── email.channel.ts                  # NEW — wraps existing email.service
│   ├── sms.channel.ts                    # NEW — Twilio stub (throws NotImplemented)
│   └── whatsapp.channel.ts               # NEW — Meta Cloud stub (throws NotImplemented)
│
├── templates/
│   ├── compiler.ts                       # NEW — handlebars compile + cache
│   ├── renderer.ts                       # NEW — render with allowlist
│   ├── masker.ts                         # NEW — maskForChannel helper
│   ├── defaults.ts                       # NEW — default template definitions
│   └── seed-defaults.ts                  # NEW — per-tenant seeding
│
├── preferences/
│   ├── preferences.service.ts            # NEW — get/update user prefs
│   ├── preferences.controller.ts         # NEW
│   └── preferences.validators.ts         # NEW
│
├── idempotency/
│   └── worker-idempotency.ts             # NEW — notif:sent:{id}:{channel} guard
│
├── events/
│   ├── event-emitter.ts                  # NEW — writes NotificationEvent rows
│   └── socket-emitter.ts                 # NEW — emits user:{id} notification:new
│
└── __tests__/
    └── ... (see §9)
```

### 5.2 Public API — `notificationService.dispatch()`

```typescript
// src/core/notifications/dispatch/types.ts

export interface DispatchInput {
  // Context
  companyId: string;
  triggerEvent: string;
  traceId?: string;

  // Entity reference (for dedup, actionUrl, rule matching)
  entityType?: string;
  entityId?: string;

  // Template variable tokens
  tokens?: Record<string, unknown>;

  // Recipient resolution
  explicitRecipients?: string[];            // bypass rule-based resolution
  recipientContext?: {                      // used by recipient-resolver
    requesterId?: string;
    approverIds?: string[];
    managerId?: string;
    departmentId?: string;
  };

  // Override fields
  priority?: NotificationPriority;          // overrides rule/template default
  systemCritical?: boolean;                 // CRITICAL semantics
  actionUrl?: string;                       // deep link on tap

  // Ad-hoc mode (no rule required)
  adHoc?: {
    title: string;
    body: string;
    channels: Array<'IN_APP' | 'PUSH' | 'EMAIL' | 'SMS' | 'WHATSAPP'>;
    priority?: NotificationPriority;
  };

  // Type classification (written to Notification.type)
  type?: string;
}

export interface DispatchResult {
  traceId: string;
  enqueued: number;
  notificationIds: string[];
  error?: string;
}
```

### 5.3 Dispatcher flow (reference implementation outline)

```typescript
// src/core/notifications/dispatch/dispatcher.ts

export async function dispatch(input: DispatchInput): Promise<DispatchResult> {
  const traceId = input.traceId ?? nanoid(12);

  try {
    // Load rules + fall back to default if none
    const rules = await loadActiveRules(input.companyId, input.triggerEvent);
    const effectiveRules = rules.length > 0
      ? rules
      : input.adHoc
      ? [buildAdHocRule(input.adHoc)]
      : [buildDefaultRule(input.triggerEvent)];

    const toEnqueue: QueueablePayload[] = [];
    const createdNotifications: Notification[] = [];

    for (const rule of effectiveRules) {
      // Resolve recipients
      const recipients = input.explicitRecipients?.length
        ? input.explicitRecipients
        : await resolveRecipients(rule.recipientRole, input);
      if (recipients.length === 0) continue;

      // Render template (handlebars, with masking applied later per-channel)
      const rendered = renderTemplate(rule.template, input.tokens ?? {});

      // Dedup per recipient
      const accepted: string[] = [];
      for (const userId of recipients) {
        const dup = await checkDedup({
          companyId: input.companyId,
          triggerEvent: input.triggerEvent,
          entityType: input.entityType,
          entityId: input.entityId,
          recipientId: userId,
          payload: rendered,
        });
        if (!dup) accepted.push(userId);
      }
      if (accepted.length === 0) continue;

      // Priority resolution
      const priority =
        input.priority ?? rule.priority ?? rule.template.priority ?? 'MEDIUM';

      // Backpressure
      const guard = await guardBackpressure(priority);
      if (guard === 'DROP') {
        for (const userId of accepted) {
          await recordEvent({
            notificationId: null, channel: rule.channel, event: 'SKIPPED',
            errorCode: 'BACKPRESSURE_DROP', traceId, source: 'SYSTEM',
          });
        }
        continue;
      }

      // Write Notification rows (system of record, always)
      const rows = await platformPrisma.notification.createManyAndReturn({
        data: accepted.map((userId) => ({
          userId,
          companyId: input.companyId,
          title: rendered.title,
          body: rendered.body,
          type: input.type ?? rule.triggerEvent,
          category: rule.category ?? null,
          entityType: input.entityType ?? null,
          entityId: input.entityId ?? null,
          data: (rendered.data ?? null) as any,
          actionUrl: input.actionUrl ?? null,
          priority,
          status: 'UNREAD',
          isRead: false,
          deliveryStatus: { inApp: 'SENT', push: 'PENDING', email: 'PENDING' },
          traceId,
          ruleId: rule.id ?? null,
          ruleVersion: rule.version ?? null,
          templateId: rule.template.id ?? null,
          templateVersion: rule.template.version ?? null,
          dedupHash: rendered.dedupHash,
        })),
      });
      createdNotifications.push(...rows);

      // Emit socket event per recipient
      for (const row of rows) {
        emitSocketEvent(row.userId, {
          notificationId: row.id,
          unreadCountHint: null,
          traceId,
        });
      }

      // Build queueable payloads
      for (const row of rows) {
        toEnqueue.push({
          notificationId: row.id,
          userId: row.userId,
          channels: rule.channel === 'IN_APP' ? [] : [rule.channel],
          priority,
          traceId,
          ruleId: rule.id ?? null,
          systemCritical: input.systemCritical === true || priority === 'CRITICAL',
        });
      }
    }

    // Enqueue with batching awareness
    for (const payload of toEnqueue) {
      if (payload.channels.length === 0) continue; // IN_APP only — no delivery job

      await enqueueWithBatching(payload);
      await recordEvent({
        notificationId: payload.notificationId, channel: payload.channels[0],
        event: 'ENQUEUED', traceId, source: 'SYSTEM',
      });
    }

    return {
      traceId,
      enqueued: toEnqueue.length,
      notificationIds: createdNotifications.map((n) => n.id),
    };
  } catch (err) {
    logger.error('Dispatcher failed', { error: err, traceId, input });
    return { traceId, enqueued: 0, notificationIds: [], error: String(err) };
  }
}
```

### 5.4 Worker (3 queues, priority-partitioned)

```typescript
// src/core/notifications/workers/notification.worker.ts

import { Worker, Job, QueueEvents } from 'bullmq';
import { bullmqConnection } from '../queue/connection';

const PROFILES = {
  'notifications:high':    { concurrency: 20 },
  'notifications:default': { concurrency: 10 },
  'notifications:low':     { concurrency: 5 },
} as const;

for (const [queueName, profile] of Object.entries(PROFILES)) {
  new Worker(
    queueName,
    async (job: Job) => {
      const { notificationId, userId, channels, traceId, priority, systemCritical } = job.data;

      for (const channel of channels) {
        const idemKey = `notif:sent:${notificationId}:${channel}`;
        if (await isAlreadySent(idemKey)) continue;

        // Re-check consent (may have changed)
        const consent = await checkConsent({ userId, channel, priority, systemCritical });
        if (!consent.allowed) {
          await updateDeliveryStatus(notificationId, channel, 'SKIPPED');
          await recordEvent({
            notificationId, channel, event: 'SKIPPED',
            errorCode: consent.reason, traceId,
            source: job.attemptsMade > 0 ? 'RETRY' : 'SYSTEM',
          });
          continue;
        }

        try {
          const result = await channelRouter.send({ notificationId, userId, channel, traceId });
          await markSent(idemKey);
          await updateDeliveryStatus(notificationId, channel, 'SENT');
          await recordEvent({
            notificationId, channel, event: 'SENT',
            provider: result.provider, providerMessageId: result.messageId,
            expoTicketId: result.expoTicketId ?? null, traceId,
            source: job.attemptsMade > 0 ? 'RETRY' : 'SYSTEM',
          });
        } catch (err: any) {
          await updateDeliveryStatus(notificationId, channel, 'FAILED');
          await recordEvent({
            notificationId, channel, event: 'FAILED',
            errorCode: err.code, errorMessage: err.message, traceId,
            source: job.attemptsMade > 0 ? 'RETRY' : 'SYSTEM',
          });
          throw err; // triggers BullMQ retry
        }
      }
    },
    {
      connection: bullmqConnection,
      concurrency: profile.concurrency,
      limiter: { max: 50, duration: 1000 },
    },
  );

  // Failed event listener → move to DLQ after all retries exhausted
  const events = new QueueEvents(queueName, { connection: bullmqConnection });
  events.on('failed', async ({ jobId, failedReason, prev }) => {
    if (prev === 'active') {
      logger.warn('Notification job failed, BullMQ will retry', { jobId, queueName, failedReason });
    }
  });
  events.on('stalled', async ({ jobId }) => {
    logger.warn('Notification job stalled', { jobId, queueName });
  });
}
```

### 5.5 Channel router + push transport

```typescript
// src/core/notifications/channels/channel-router.ts
export const channelRouter = {
  async send(args: { notificationId: string; userId: string; channel: string; traceId: string }) {
    switch (args.channel) {
      case 'IN_APP':    return inAppChannel.send(args);
      case 'PUSH':      return pushChannel.send(args);
      case 'EMAIL':     return emailChannel.send(args);
      case 'SMS':       return smsChannel.send(args);
      case 'WHATSAPP':  return whatsappChannel.send(args);
      default:          throw new Error(`Unknown channel: ${args.channel}`);
    }
  },
};
```

```typescript
// src/core/notifications/channels/push/push.channel.ts
export const pushChannel = {
  async send({ notificationId, userId, traceId }: SendArgs) {
    const devices = await platformPrisma.userDevice.findMany({
      where: { userId, isActive: true },
    });
    if (devices.length === 0) {
      throw Object.assign(new Error('NO_ACTIVE_DEVICES'), { code: 'NO_ACTIVE_DEVICES' });
    }

    const pref = await platformPrisma.userNotificationPreference.findUnique({ where: { userId } });
    const targetDevices = pref?.deviceStrategy === 'LATEST_ONLY'
      ? [devices.sort((a, b) => b.lastActiveAt.getTime() - a.lastActiveAt.getTime())[0]]
      : devices;

    const expoDevices = targetDevices.filter((d) => d.tokenType === 'EXPO');
    const fcmDevices  = targetDevices.filter((d) => d.tokenType === 'FCM_WEB' || d.tokenType === 'FCM_NATIVE');

    const notification = await platformPrisma.notification.findUniqueOrThrow({ where: { id: notificationId } });
    const template     = notification.templateId
      ? await platformPrisma.notificationTemplate.findUnique({ where: { id: notification.templateId } })
      : null;
    const sensitiveFields = (template?.sensitiveFields as string[]) ?? [];

    const masked = maskForChannel('PUSH', {
      title: notification.title,
      body: notification.body,
      data: notification.data,
    }, sensitiveFields);

    const results = await Promise.allSettled([
      expoDevices.length ? expoProvider.send(expoDevices, masked, traceId, notification.priority) : null,
      fcmDevices.length  ? fcmProvider.send(fcmDevices, masked, traceId, notification.priority)  : null,
    ].filter(Boolean) as Promise<ProviderResult>[]);

    // Token lifecycle: deactivate bad tokens
    for (const r of results) {
      if (r.status === 'fulfilled' && r.value?.deadTokens?.length) {
        await deactivateDevices(r.value.deadTokens);
      }
    }

    // Surface first result for worker's success tracking
    const first = results.find((r) => r.status === 'fulfilled');
    if (!first) throw (results[0] as PromiseRejectedResult).reason;
    return (first as PromiseFulfilledResult<ProviderResult>).value;
  },
};
```

```typescript
// src/core/notifications/channels/push/expo.provider.ts
import { Expo } from 'expo-server-sdk';

const expo = new Expo({
  accessToken: env.EXPO_ACCESS_TOKEN,  // optional
  useFcmV1: true,                      // REQUIRED for SDK 53+
});

export const expoProvider = {
  async send(devices: UserDevice[], payload: RenderedPayload, traceId: string, priority: NotificationPriority) {
    const messages = devices
      .filter((d) => Expo.isExpoPushToken(d.fcmToken))
      .map((d) => ({
        to: d.fcmToken,
        title: payload.title,
        body: payload.body,
        data: { ...((payload.data as object) ?? {}), traceId },
        priority: priority === 'CRITICAL' || priority === 'HIGH' ? 'high' as const : 'default' as const,
        sound: 'default' as const,
        channelId: 'default',
        badge: 1,
      }));

    const chunks = expo.chunkPushNotifications(messages);
    const tickets: Array<{ device: UserDevice; ticket: import('expo-server-sdk').ExpoPushTicket }> = [];

    for (let i = 0; i < chunks.length; i++) {
      const chunk = chunks[i];
      const res = await expo.sendPushNotificationsAsync(chunk);
      // Map returned tickets back to devices (same order)
      const chunkDevices = devices.slice(i * chunk.length, (i + 1) * chunk.length);
      for (let j = 0; j < res.length; j++) {
        tickets.push({ device: chunkDevices[j], ticket: res[j] });
      }
    }

    const dead = tickets
      .filter((t) => t.ticket?.status === 'error' && (t.ticket as any).details?.error === 'DeviceNotRegistered')
      .map((t) => t.device.fcmToken);

    const ok = tickets.find((t) => t.ticket?.status === 'ok');
    return {
      provider: 'expo' as const,
      messageId: (ok?.ticket as any)?.id ?? null,
      expoTicketId: (ok?.ticket as any)?.id ?? null,
      deadTokens: dead,
    };
  },
};
```

### 5.6 Consent gate

```typescript
// src/core/notifications/dispatch/consent-gate.ts

export async function checkConsent(args: {
  userId: string;
  channel: NotificationChannel;
  priority: NotificationPriority;
  systemCritical?: boolean;
}): Promise<{ allowed: boolean; reason?: string }> {
  const { userId, channel, priority, systemCritical } = args;

  // IN_APP always allowed (it's the system of record)
  if (channel === 'IN_APP') return { allowed: true };

  const user = await platformPrisma.user.findUniqueOrThrow({ where: { id: userId } });
  const companySettings = await platformPrisma.companySettings.findFirst({ where: { companyId: user.companyId } });
  if (!companySettings) return { allowed: false, reason: 'NO_COMPANY_SETTINGS' };

  // Company master switch
  const companyField = {
    PUSH: 'pushNotifications',
    EMAIL: 'emailNotifications',
    SMS: 'smsNotifications',
    WHATSAPP: 'whatsappNotifications',
  }[channel] as keyof typeof companySettings;
  if (!companySettings[companyField]) return { allowed: false, reason: 'COMPANY_MASTER_OFF' };

  // SYSTEM_CRITICAL bypasses user prefs + quiet hours
  if (systemCritical || priority === 'CRITICAL') return { allowed: true };

  // Per-user preference
  const pref = await platformPrisma.userNotificationPreference.findUnique({ where: { userId } });
  if (pref) {
    const userField = {
      PUSH: 'pushEnabled',
      EMAIL: 'emailEnabled',
      SMS: 'smsEnabled',
      WHATSAPP: 'whatsappEnabled',
    }[channel] as keyof typeof pref;
    if (!pref[userField]) return { allowed: false, reason: 'USER_PREF_OFF' };

    // Quiet hours
    if (pref.quietHoursEnabled && pref.quietHoursStart && pref.quietHoursEnd) {
      const now = DateTime.now().setZone(pref.timezone ?? companySettings.timezone ?? 'UTC');
      if (isInQuietHours(now, pref.quietHoursStart, pref.quietHoursEnd)) {
        // LOW/MEDIUM suppressed during quiet hours
        if (priority === 'LOW' || priority === 'MEDIUM') {
          return { allowed: false, reason: 'QUIET_HOURS' };
        }
      }
    }
  }

  return { allowed: true };
}
```

### 5.7 Recipient resolver

The resolver handles these role tokens:

- `REQUESTER` → `input.recipientContext.requesterId`
- `APPROVER` → `input.recipientContext.approverIds`
- `MANAGER` → employee's reporting manager (via `Employee.reportingManagerId`)
- `EMPLOYEE` → `input.recipientContext.requesterId` (alias for REQUESTER in ESS flows)
- `HR` → users with role `HR_PERSONNEL` in the company
- `FINANCE` → users with role `FINANCE_PERSONNEL`
- `IT` → users with role `IT_PERSONNEL`
- `ADMIN` → users with role `COMPANY_ADMIN`
- `ALL` → all active users in the company (used for announcements — guarded by rate limit)

Implementation lives in `src/core/notifications/dispatch/recipient-resolver.ts`. All lookups are cached per-dispatch-call to avoid duplicate queries when multiple rules share the same role.

### 5.8 REST endpoints

```
POST   /notifications/register-device       # existing, payload extended
DELETE /notifications/register-device       # existing
GET    /notifications                       # existing
GET    /notifications/unread-count          # existing
PATCH  /notifications/:id/read              # existing
PATCH  /notifications/read-all              # existing
PATCH  /notifications/:id/archive           # NEW
GET    /notifications/preferences           # NEW — current user prefs
PATCH  /notifications/preferences           # NEW — update prefs
GET    /notifications/:id/events            # NEW — admin debug view of delivery audit
POST   /notifications/test                  # NEW — admin-only, fires a test notification to self
```

**Payload extensions:**

`POST /notifications/register-device` now accepts:
```json
{
  "fcmToken": "ExponentPushToken[...]",
  "platform": "MOBILE_IOS|MOBILE_ANDROID|WEB",
  "tokenType": "EXPO|FCM_WEB|FCM_NATIVE",
  "deviceName": "...",
  "deviceModel": "iPhone 15 Pro",
  "osVersion": "17.2.1",
  "appVersion": "1.4.0",
  "locale": "en-IN",
  "timezone": "Asia/Kolkata"
}
```

### 5.9 Environment variables (added to `src/config/env.ts` Zod schema)

```typescript
FIREBASE_SERVICE_ACCOUNT_KEY:          z.string().optional(),  // now validated
EXPO_ACCESS_TOKEN:                     z.string().optional(),  // optional rate-limit headroom
NOTIFICATIONS_ENABLED:                 z.coerce.boolean().default(true),
NOTIFICATIONS_DEDUP_TTL_SEC:           z.coerce.number().default(60),
NOTIFICATIONS_IDEMPOTENCY_TTL_SEC:     z.coerce.number().default(86400),
NOTIFICATIONS_BATCH_THRESHOLD:         z.coerce.number().default(5),
NOTIFICATIONS_BATCH_WINDOW_SEC:        z.coerce.number().default(300),
NOTIFICATIONS_MAX_QUEUE_LOW:           z.coerce.number().default(10000),
NOTIFICATIONS_MAX_QUEUE_DEFAULT:       z.coerce.number().default(50000),
NOTIFICATIONS_RECEIPT_POLL_SEC:        z.coerce.number().default(30),
NOTIFICATIONS_RECEIPT_MAX_AGE_MIN:     z.coerce.number().default(15),
NOTIFICATIONS_DLQ_RETENTION_DAYS:      z.coerce.number().default(7),
```

### 5.10 New dependencies

```json
{
  "dependencies": {
    "bullmq": "^5.x",
    "expo-server-sdk": "^3.x",
    "handlebars": "^4.x",
    "nanoid": "^5.x"
  }
}
```

`firebase-admin`, `ioredis`, `bull` already present.

### 5.11 Legacy facade

```typescript
// src/core/notifications/notification.service.ts
export const notificationService = {
  dispatch,  // primary

  // Legacy shim — existing HR listeners keep working during migration
  async send(params: LegacySendParams) {
    return dispatch({
      companyId: params.companyId,
      triggerEvent: params.type,
      entityType: params.entityType,
      entityId: params.entityId,
      explicitRecipients: params.recipientIds,
      tokens: params.data,
      adHoc: {
        title: params.title,
        body: params.body,
        channels: params.channels.map((c) => c.toUpperCase()) as any,
      },
    });
  },

  // Device + notification queries (unchanged)
  registerDevice, unregisterDevice, listNotifications, markAsRead,
  markAllAsRead, getUnreadCount, archive,

  // Preferences (new)
  getPreferences, updatePreferences, sendTestNotification,
};
```

### 5.12 Socket.io integration

Add to `src/lib/socket.ts`:

```typescript
io.use((socket, next) => {
  // existing JWT auth
});

io.on('connection', (socket) => {
  const userId = socket.data.userId;
  const companyId = socket.data.companyId;
  if (userId) socket.join(`user:${userId}`);
  if (companyId) socket.join(`company:${companyId}`);
  // existing ticket room joins unchanged
});

export function emitNotificationNew(userId: string, payload: { notificationId: string; traceId: string }) {
  const io = getSocketServer();
  io.to(`user:${userId}`).emit('notification:new', {
    notificationId: payload.notificationId,
    unreadCountHint: null,
  });
}
```

---

## 6. Event Wiring Map

Every place that currently creates an `ApprovalRequest`, mutates its state, or performs an ESS submission gets a `dispatch()` call. This section enumerates them exhaustively.

### 6.1 Leave module (`src/modules/hr/leave/`)

| Event | Site | Trigger Event | Priority | Recipient Role | Category |
|---|---|---|---|---|---|
| Leave submitted | `leave.service.createLeaveRequest()` | `LEAVE_APPLICATION` | MEDIUM | APPROVER | `LEAVE_APPROVAL` |
| Leave approved | `leave.service.approveLeaveRequest()` | `LEAVE_APPROVED` | MEDIUM | REQUESTER | `LEAVE_STATUS` |
| Leave rejected | `leave.service.rejectLeaveRequest()` | `LEAVE_REJECTED` | MEDIUM | REQUESTER | `LEAVE_STATUS` |
| Leave cancelled | `leave.service.cancelLeaveRequest()` | `LEAVE_CANCELLED` | LOW | APPROVER | `LEAVE_STATUS` |
| Leave balance low | cron `leave-balance-reminder` | `LEAVE_BALANCE_LOW` | LOW | REQUESTER | `LEAVE_REMINDER` |

### 6.2 Attendance module (`src/modules/hr/attendance/`)

| Event | Site | Trigger Event | Priority | Recipient Role | Category |
|---|---|---|---|---|---|
| Regularization submitted | `attendance.service.createRegularizationRequest()` | `ATTENDANCE_REGULARIZATION` | MEDIUM | APPROVER | `ATTENDANCE_APPROVAL` |
| Regularization approved | `attendance.service.approveRegularization()` | `ATTENDANCE_REGULARIZED` | MEDIUM | REQUESTER | `ATTENDANCE_STATUS` |
| Regularization rejected | `attendance.service.rejectRegularization()` | `ATTENDANCE_REGULARIZATION_REJECTED` | MEDIUM | REQUESTER | `ATTENDANCE_STATUS` |
| Missed punch-out | cron `attendance-missed-punch` | `ATTENDANCE_MISSED_PUNCH` | HIGH | REQUESTER | `ATTENDANCE_REMINDER` |
| Overtime claim submitted | `attendance.service.createOvertimeClaim()` | `OVERTIME_CLAIM` | MEDIUM | APPROVER | `OVERTIME_APPROVAL` |
| Overtime claim approved | `attendance.service.approveOvertimeClaim()` | `OVERTIME_CLAIM_APPROVED` | MEDIUM | REQUESTER | `OVERTIME_STATUS` |
| Overtime claim rejected | `attendance.service.rejectOvertimeClaim()` | `OVERTIME_CLAIM_REJECTED` | MEDIUM | REQUESTER | `OVERTIME_STATUS` |

### 6.3 ESS / Self-service (`src/modules/hr/ess/`)

| Event | Site | Trigger Event | Priority | Recipient Role |
|---|---|---|---|---|
| Shift change request | `ess.service.createShiftChangeRequest()` | `SHIFT_CHANGE` | MEDIUM | APPROVER |
| Shift swap request | `ess.service.createShiftSwapRequest()` | `SHIFT_SWAP` | MEDIUM | APPROVER |
| WFH request | `ess.service.createWfhRequest()` | `WFH_REQUEST` | MEDIUM | APPROVER |
| Profile update request | `ess.service.createProfileUpdateRequest()` | `PROFILE_UPDATE` | LOW | HR |
| Reimbursement submitted | `ess.service.createReimbursement()` | `REIMBURSEMENT` | MEDIUM | APPROVER |
| Reimbursement approved | `ess.service.approveReimbursement()` | `REIMBURSEMENT_APPROVED` | MEDIUM | REQUESTER |
| Reimbursement rejected | `ess.service.rejectReimbursement()` | `REIMBURSEMENT_REJECTED` | MEDIUM | REQUESTER |
| Loan application | `ess.service.createLoanApplication()` | `LOAN_APPLICATION` | MEDIUM | APPROVER |
| Loan approved | `ess.service.approveLoan()` | `LOAN_APPROVED` | HIGH | REQUESTER |
| Loan rejected | `ess.service.rejectLoan()` | `LOAN_REJECTED` | MEDIUM | REQUESTER |
| IT declaration submitted | `ess.service.submitITDeclaration()` | `IT_DECLARATION` | MEDIUM | HR/FINANCE |
| IT declaration verified | `ess.service.verifyITDeclaration()` | `IT_DECLARATION_VERIFIED` | LOW | REQUESTER |
| Travel request | `ess.service.createTravelRequest()` | `TRAVEL_REQUEST` | MEDIUM | APPROVER |
| Resignation submitted | `ess.service.createResignation()` | `RESIGNATION` | HIGH | HR, APPROVER |
| Help desk ticket submitted | `ess.service.createHelpDeskTicket()` | `HELPDESK_SUBMITTED` | MEDIUM | HR |
| Grievance submitted | `ess.service.createGrievance()` | `GRIEVANCE_SUBMITTED` | HIGH | HR |

### 6.4 Approval workflow generic handler (`src/modules/hr/ess/ess.service.ts`)

The approval pipeline (`approvalWorkflowService.transitionApprovalRequest()`) is wired once to dispatch on every transition, covering everything above that goes through `ApprovalRequest`. Two calls added:

- On `approve` → `dispatch({ triggerEvent: '${entityType}_APPROVED', recipientContext.requesterId, ... })`
- On `reject` → `dispatch({ triggerEvent: '${entityType}_REJECTED', recipientContext.requesterId, ... })`
- On `escalate` → `dispatch({ triggerEvent: '${entityType}_ESCALATED', recipientContext.approverIds: nextStep.approvers, ... })`

### 6.5 HR lifecycle (`src/modules/hr/employee/`, `offboarding/`, `org-structure/`)

| Event | Site | Trigger Event | Priority | Recipient Role |
|---|---|---|---|---|
| Employee onboarded | `employee.service.createEmployee()` | `EMPLOYEE_ONBOARDED` | MEDIUM | EMPLOYEE, MANAGER, HR |
| Employee transferred | `employee.service.transferEmployee()` | `EMPLOYEE_TRANSFER` | MEDIUM | EMPLOYEE, old/new MANAGER, HR |
| Employee promoted | `employee.service.promoteEmployee()` | `EMPLOYEE_PROMOTION` | HIGH | EMPLOYEE, MANAGER, HR |
| Salary revision | `employee.service.reviseSalary()` | `SALARY_REVISION` | HIGH (CRITICAL) | EMPLOYEE (masked amount in push) |
| Resignation accepted | `offboarding.service.acceptResignation()` | `RESIGNATION_ACCEPTED` | HIGH | EMPLOYEE, HR, MANAGER |
| F&F initiated | `offboarding.service.initiateFnF()` | `FNF_INITIATED` | HIGH | EMPLOYEE, HR, FINANCE |
| F&F completed | `offboarding.service.completeFnF()` | `FNF_COMPLETED` | HIGH | EMPLOYEE, HR |

### 6.6 Payroll (`src/modules/hr/payroll-run/`)

| Event | Site | Trigger Event | Priority | Recipient Role |
|---|---|---|---|---|
| Payroll approval pending | `payrollRun.service.submitForApproval()` | `PAYROLL_APPROVAL` | HIGH | APPROVER (Finance Head / CFO) |
| Payroll approved | `payrollRun.service.approveRun()` | `PAYROLL_APPROVED` | MEDIUM | REQUESTER (payroll admin) |
| Payslip published | `payrollRun.service.publishPayslips()` | `PAYSLIP_PUBLISHED` | HIGH | EMPLOYEE (all affected, masked amount) |
| Bonus uploaded | `payrollRun.service.uploadBonus()` | `BONUS_UPLOAD` | MEDIUM | APPROVER |
| Salary credited | `payrollRun.service.markPaid()` | `SALARY_CREDITED` | CRITICAL (bypass user pref) | EMPLOYEE (masked amount) |

### 6.7 Recruitment (`src/modules/hr/advanced/recruitment/`)

| Event | Site | Trigger Event | Priority | Recipient Role |
|---|---|---|---|---|
| Candidate stage changed | `recruitment.service.changeStage()` | `CANDIDATE_STAGE_CHANGED` | LOW | HR |
| Candidate hired | `recruitment.service.hireCandidate()` | `CANDIDATE_HIRED` | MEDIUM | HR, MANAGER |
| Offer sent | `recruitment.service.sendOffer()` | `OFFER_SENT` | MEDIUM | HR (note: candidate is external, not a User) |
| Offer accepted | (via external webhook) | `OFFER_ACCEPTED` | HIGH | HR, MANAGER |
| Offer rejected | (via external webhook) | `OFFER_REJECTED` | MEDIUM | HR |
| Interview scheduled | `recruitment.service.scheduleInterview()` (existing — keep) | `INTERVIEW_SCHEDULED` | MEDIUM | APPROVER (panelists) |
| Interview completed | `recruitment.service.completeInterview()` | `INTERVIEW_COMPLETED` | LOW | HR |

### 6.8 Training (`src/modules/hr/advanced/training/`)

Existing calls stay and are converted to the new dispatcher API:

- `TRAINING_NOMINATION` → EMPLOYEE (existing)
- `TRAINING_COMPLETED` → EMPLOYEE (existing)
- `CERTIFICATE_EXPIRING` → EMPLOYEE (existing)

New additions:

- `TRAINING_REQUEST` → APPROVER (via ess.service)
- `TRAINING_SESSION_UPCOMING` → EMPLOYEE (cron, 24h before session)

### 6.9 Assets (`src/modules/hr/advanced/assets/`)

| Event | Site | Trigger Event | Priority | Recipient Role |
|---|---|---|---|---|
| Asset issuance requested | `assets.service.requestIssuance()` | `ASSET_ISSUANCE` | MEDIUM | APPROVER |
| Asset assigned | `assets.service.assignAsset()` | `ASSET_ASSIGNED` | MEDIUM | EMPLOYEE |
| Asset return due | cron `asset-return-reminder` | `ASSET_RETURN_DUE` | LOW | EMPLOYEE |

### 6.10 Support tickets (`src/core/support/support.service.ts`)

Bridge existing Socket.io ticket events into the dispatcher. They still emit their current socket events for live ticket UI refresh, AND call `dispatch()` for bell/push delivery.

| Event | Site | Trigger Event | Priority | Recipient Role |
|---|---|---|---|---|
| Ticket created | `support.service.createTicket()` | `TICKET_CREATED` | MEDIUM | ADMIN (super admin support team) |
| Ticket message | `support.service.addMessage()` | `TICKET_MESSAGE` | MEDIUM | Other party (requester if admin posted, admin if requester posted) |
| Ticket status changed | `support.service.updateStatus()` | `TICKET_STATUS_CHANGED` | MEDIUM | REQUESTER |
| Ticket resolved | `support.service.resolveTicket()` | `TICKET_RESOLVED` | MEDIUM | REQUESTER |
| Module change approved | `support.service.approveModuleChange()` | `MODULE_CHANGE_APPROVED` | HIGH | REQUESTER (company admin) |

### 6.11 Auth / security (`src/core/auth/`)

| Event | Site | Trigger Event | Priority | Recipient Role |
|---|---|---|---|---|
| Password reset requested | `auth.service.requestPasswordReset()` | `PASSWORD_RESET` | CRITICAL (bypass user pref) | REQUESTER (self) |
| New login on unknown device | `auth.service.login()` | `NEW_DEVICE_LOGIN` | CRITICAL | REQUESTER (self) |
| Account locked | `auth.service.lockAccount()` | `ACCOUNT_LOCKED` | CRITICAL | REQUESTER (self) |

### 6.12 Total sites touched

Approximately **50 dispatch call sites** across ~15 service files. All are mechanical single-line changes calling `notificationService.dispatch({...})`. No business logic is modified.

---

## 7. Default Template Set

Seeded on tenant creation and via the data migration. Each entry below generates one `NotificationTemplate` row per channel (PUSH + IN_APP + EMAIL where applicable) and one `NotificationRule` row that binds to the correct default recipient role.

### 7.1 Template catalogue (24 templates × ~3 channels = ~72 rows per tenant)

| Code | Channels | Priority | Default Recipient | Title | Body (handlebars) | Sensitive |
|---|---|---|---|---|---|---|
| `LEAVE_APPLICATION` | PUSH, IN_APP, EMAIL | MEDIUM | APPROVER | New Leave Request | `{{employee_name}} requested {{leave_days}} days of leave from {{from_date}} to {{to_date}}.` | — |
| `LEAVE_APPROVED` | PUSH, IN_APP, EMAIL | MEDIUM | REQUESTER | Leave Approved | `Your leave request for {{leave_days}} days has been approved.` | — |
| `LEAVE_REJECTED` | PUSH, IN_APP, EMAIL | MEDIUM | REQUESTER | Leave Rejected | `Your leave request was rejected. Reason: {{reason}}` | — |
| `ATTENDANCE_REGULARIZATION` | PUSH, IN_APP, EMAIL | MEDIUM | APPROVER | Attendance Regularization | `{{employee_name}} requested attendance regularization for {{date}}.` | — |
| `ATTENDANCE_REGULARIZED` | PUSH, IN_APP | MEDIUM | REQUESTER | Attendance Regularized | `Your attendance regularization for {{date}} was approved.` | — |
| `OVERTIME_CLAIM` | PUSH, IN_APP, EMAIL | MEDIUM | APPROVER | Overtime Claim | `{{employee_name}} submitted an overtime claim for {{hours}} hours on {{date}}.` | — |
| `REIMBURSEMENT` | PUSH, IN_APP, EMAIL | MEDIUM | APPROVER | Reimbursement Request | `{{employee_name}} requested reimbursement of {{amount}} for {{category}}.` | amount |
| `REIMBURSEMENT_APPROVED` | PUSH, IN_APP, EMAIL | MEDIUM | REQUESTER | Reimbursement Approved | `Your reimbursement request for {{amount}} has been approved.` | amount |
| `LOAN_APPLICATION` | PUSH, IN_APP, EMAIL | MEDIUM | APPROVER | Loan Application | `{{employee_name}} applied for a loan of {{amount}}.` | amount |
| `LOAN_APPROVED` | PUSH, IN_APP, EMAIL | HIGH | REQUESTER | Loan Approved | `Your loan application for {{amount}} has been approved.` | amount |
| `WFH_REQUEST` | PUSH, IN_APP | MEDIUM | APPROVER | Work From Home Request | `{{employee_name}} requested WFH for {{date_range}}.` | — |
| `SHIFT_CHANGE` | PUSH, IN_APP | MEDIUM | APPROVER | Shift Change Request | `{{employee_name}} requested a shift change.` | — |
| `PROFILE_UPDATE` | IN_APP, EMAIL | LOW | HR | Profile Update Request | `{{employee_name}} submitted a profile update.` | — |
| `IT_DECLARATION` | IN_APP, EMAIL | MEDIUM | HR, FINANCE | IT Declaration Submitted | `{{employee_name}} submitted their IT declaration for FY {{fy}}.` | — |
| `RESIGNATION` | PUSH, IN_APP, EMAIL | HIGH | HR, APPROVER | Resignation Submitted | `{{employee_name}} has submitted a resignation. Last working day: {{last_day}}.` | — |
| `PAYROLL_APPROVAL` | PUSH, IN_APP, EMAIL | HIGH | APPROVER | Payroll Approval Pending | `Payroll for {{month_year}} is awaiting your approval.` | — |
| `PAYSLIP_PUBLISHED` | PUSH, IN_APP, EMAIL | HIGH | EMPLOYEE | Payslip Available | `Your payslip for {{month_year}} is now available.` | — |
| `SALARY_CREDITED` | PUSH, IN_APP | CRITICAL | EMPLOYEE | Salary Credited | `Your salary of {{amount}} for {{month_year}} has been credited.` | amount |
| `INTERVIEW_SCHEDULED` | PUSH, IN_APP, EMAIL | MEDIUM | APPROVER | Interview Scheduled | `You are scheduled as a panelist for {{candidate_name}} on {{interview_date}}.` | — |
| `TRAINING_NOMINATION` | PUSH, IN_APP, EMAIL | MEDIUM | EMPLOYEE | Training Nomination | `You have been nominated for "{{training_name}}".` | — |
| `TRAINING_COMPLETED` | IN_APP, EMAIL | LOW | EMPLOYEE | Training Completed | `Congratulations! You have completed "{{training_name}}".` | — |
| `CERTIFICATE_EXPIRING` | PUSH, IN_APP, EMAIL | MEDIUM | EMPLOYEE | Certificate Expiring | `Your "{{training_name}}" certificate expires on {{expiry_date}}.` | — |
| `TICKET_MESSAGE` | PUSH, IN_APP | MEDIUM | REQUESTER/ADMIN | New Ticket Message | `New message on ticket "{{ticket_subject}}"` | — |
| `PASSWORD_RESET` | EMAIL, PUSH | CRITICAL | REQUESTER | Password Reset Code | `Your password reset code is {{reset_code}}. Expires in {{expires_in}}.` | reset_code |

### 7.2 Sensitive field masking examples

- `SALARY_CREDITED` with `{{amount: "INR 75,000"}}` renders in-app as "Your salary of INR 75,000 ... has been credited" but on push as "Your salary of *** ... has been credited".
- `LOAN_APPROVED` with `{{amount: "INR 5,00,000"}}` same pattern.
- `PASSWORD_RESET` with `{{reset_code: "845210"}}` — email shows the code (sensitive fields only mask PUSH), push shows `Your password reset code is ***. Expires in 15 minutes.` User opens the app to see the code, or gets it via email.

---

## 8. Web Changes (`web-system-app`)

### 8.1 Socket.io user-room wiring

**`src/lib/socket.ts`:**
- Add `connectSocket()` call after successful login (in `use-auth-store.ts`).
- Add `disconnectSocket()` call on logout.
- Socket server already joins authenticated user to `user:{id}` + `company:{companyId}` (see §5.12).

**`src/hooks/useNotificationSocket.ts` (NEW):**
```typescript
export function useNotificationSocket() {
  const queryClient = useQueryClient();
  useEffect(() => {
    const socket = getSocket();
    const handler = (_payload: { notificationId: string }) => {
      queryClient.invalidateQueries({ queryKey: notificationKeys.all });
    };
    socket.on('notification:new', handler);
    return () => { socket.off('notification:new', handler); };
  }, [queryClient]);
}
```

Mounted once at `DashboardLayout` level.

### 8.2 Polling frequency reduction

- `TopBar.tsx` `NotificationsPanel`: change `refetchInterval` from 30_000 to 300_000 (5 min). Socket drives primary updates; polling is the fallback.
- `NotificationListScreen.tsx`: unchanged (user refetches manually).

### 8.3 User Notification Preferences screen (NEW)

**`src/features/settings/NotificationPreferencesScreen.tsx`:**
- Route: `/app/settings/notifications`
- Sections:
  - **Channels:** toggles for Push / Email / SMS / WhatsApp / In-App (In-App labelled "History — cannot be disabled, shown in bell icon")
  - **Device strategy:** radio All Devices vs Latest Only
  - **Quiet hours:** enable toggle + start/end time pickers (user timezone)
  - **Test notification:** button "Send test notification" → `POST /notifications/test`
- Shows company-level master states as read-only badges. If company has disabled a channel, the user toggle is greyed out with an explanation tooltip.
- Uses React Hook Form + Zod.

**`src/features/company-admin/CompanySettingsScreen.tsx`:**
- Add three new toggle rows: Push Notifications, SMS Notifications, In-App Notifications (all wired to new `CompanySettings` fields).
- Keep Email Notifications and WhatsApp Notifications unchanged.

**`src/features/super-admin/tenant-onboarding/steps/Step05Preferences.tsx`:**
- Same three new toggle rows added to the onboarding flow.

### 8.4 Notification list + bell icon enhancements

- `NotificationListScreen.tsx`: add priority badge (LOW grey, MEDIUM blue, HIGH amber, CRITICAL red), add archive button, add filter dropdown (All / Unread / Archived / By type).
- `TopBar.tsx` `NotificationsPanel`: show priority color stripe on unread items. Add "Settings" link at the bottom next to "View all" that navigates to the new preferences screen.

### 8.5 API client extensions

**`src/lib/api/notifications.ts`:**
```typescript
export const notificationApi = {
  // existing ...
  archive: (id: string) => client.patch(`/notifications/${id}/archive`).then(r => r.data),
  getPreferences: () => client.get('/notifications/preferences').then(r => r.data),
  updatePreferences: (payload: PreferenceUpdate) => client.patch('/notifications/preferences', payload).then(r => r.data),
  getDeliveryEvents: (id: string) => client.get(`/notifications/${id}/events`).then(r => r.data),
  sendTestNotification: () => client.post('/notifications/test').then(r => r.data),
};
```

### 8.6 Device registration payload update

**`src/lib/notifications/setup.ts`:** extend the registration payload:
```typescript
await client.post('/notifications/register-device', {
  fcmToken: token,
  tokenType: 'FCM_WEB',
  platform: 'WEB',
  deviceName: navigator.userAgent.substring(0, 100),
  osVersion: navigator.platform,
  appVersion: import.meta.env.VITE_APP_VERSION ?? 'unknown',
  locale: navigator.language,
  timezone: Intl.DateTimeFormat().resolvedOptions().timeZone,
});
```

### 8.7 React Query keys

Extend `notificationKeys` factory:
```typescript
notificationKeys = {
  all: ['notifications'],
  unreadCount: () => [...all, 'unread-count'],
  list: (params?) => params ? [...all, 'list', params] : [...all, 'list'],
  preferences: () => [...all, 'preferences'],         // NEW
  events: (id: string) => [...all, 'events', id],      // NEW
};
```

### 8.8 Routes added to `src/App.tsx`

- `/app/settings/notifications` → `NotificationPreferencesScreen` (requires auth; no special permission — every user can access their own preferences).

---

## 9. Mobile Changes (`mobile-app`)

### 9.1 Dependencies added

```json
{
  "dependencies": {
    "socket.io-client": "^4.x",
    "expo-application": "~6.x"   // already bundled via expo-constants alternatives, verify
  }
}
```

### 9.2 `app.config.ts` — notification plugin config

No `google-services.json` bundling (Expo handles it via EAS credentials), but we add the full config for correctness:

```typescript
plugins: [
  // ... existing ...
  [
    'expo-notifications',
    {
      icon: './assets/notification-icon.png',  // NEW — monochrome white-on-transparent 96x96
      color: '#4F46E5',                         // existing
      sounds: [],                               // default system sound
      mode: 'production',                       // ensures proper APNs environment
    },
  ],
  // ... existing ...
],
```

**Asset added:** `mobile-app/assets/notification-icon.png` — a white silhouette on transparent background, 96×96, per Android notification icon guidelines. Without this, Android shows a generic bell.

### 9.3 `src/lib/notifications/setup.ts` — hardened + extended

```typescript
import * as Device from 'expo-device';
import * as Notifications from 'expo-notifications';
import * as Application from 'expo-application';
import Constants from 'expo-constants';
import { Platform } from 'react-native';
import { client } from '@/lib/api/client';
import { createLogger } from '@/lib/logger';
import { getItem, setItem, removeItem } from '@/lib/storage';

const logger = createLogger('PushNotifications');
const PUSH_TOKEN_KEY = 'push_token';

Notifications.setNotificationHandler({
  handleNotification: async () => ({
    shouldShowAlert: true,
    shouldShowBanner: true,
    shouldShowList: true,
    shouldPlaySound: true,
    shouldSetBadge: true,
  }),
});

export async function registerForPushNotifications(): Promise<string | null> {
  if (!Device.isDevice) {
    logger.info('Push notifications require a physical device — skipping');
    return null;
  }

  // Permission
  const { status: existing } = await Notifications.getPermissionsAsync();
  let finalStatus = existing;
  if (existing !== 'granted') {
    const { status } = await Notifications.requestPermissionsAsync();
    finalStatus = status;
  }
  if (finalStatus !== 'granted') {
    logger.info('Push permission not granted');
    return null;
  }

  // Android channel (mandatory)
  if (Platform.OS === 'android') {
    await Notifications.setNotificationChannelAsync('default', {
      name: 'Default',
      importance: Notifications.AndroidImportance.MAX,
      vibrationPattern: [0, 250, 250, 250],
      lightColor: '#4F46E5',
      sound: 'default',
    });
    // High priority channel for CRITICAL notifications
    await Notifications.setNotificationChannelAsync('critical', {
      name: 'Critical',
      importance: Notifications.AndroidImportance.MAX,
      vibrationPattern: [0, 500, 250, 500],
      lightColor: '#DC2626',
      sound: 'default',
      bypassDnd: true,
    });
  }

  try {
    const projectId =
      Constants.expoConfig?.extra?.eas?.projectId ??
      Constants.easConfig?.projectId;
    if (!projectId) {
      logger.error('Missing EAS project ID');
      return null;
    }

    const tokenData = await Notifications.getExpoPushTokenAsync({ projectId });
    const token = tokenData.data;
    const platform = Platform.OS === 'ios' ? 'MOBILE_IOS' : 'MOBILE_ANDROID';

    logger.info('Obtained Expo push token', { platform });
    await setItem(PUSH_TOKEN_KEY, token);

    try {
      await client.post('/notifications/register-device', {
        fcmToken: token,
        tokenType: 'EXPO',
        platform,
        deviceName: Device.deviceName ?? Device.modelName ?? undefined,
        deviceModel: Device.modelName ?? undefined,
        osVersion: Device.osVersion ?? undefined,
        appVersion: Application.nativeApplicationVersion ?? undefined,
        locale: Intl.DateTimeFormat().resolvedOptions().locale,
        timezone: Intl.DateTimeFormat().resolvedOptions().timeZone,
      });
      logger.info('Device registered with backend');
    } catch (err) {
      logger.error('Failed to register device with backend', { error: err });
    }
    return token;
  } catch (err: any) {
    // Expected when FCM credentials are not set up locally.
    // We log but do not crash the app.
    if (String(err?.message).includes('FirebaseApp is not initialized')) {
      logger.warn(
        'FCM not configured on this build. This is expected if running Expo Go or a build without FCM credentials. ' +
        'See https://docs.expo.dev/push-notifications/fcm-credentials/',
      );
    } else {
      logger.error('Failed to get push token', { error: err });
    }
    return null;
  }
}

export async function unregisterPushNotifications(): Promise<void> {
  const token = getItem<string>(PUSH_TOKEN_KEY);
  if (!token) return;
  try {
    await client.delete('/notifications/register-device', { data: { fcmToken: token } });
  } catch (err) {
    logger.error('Failed to unregister device', { error: err });
  }
  removeItem(PUSH_TOKEN_KEY);
}

export function getStoredPushToken(): string | null {
  return getItem<string>(PUSH_TOKEN_KEY);
}

export function addNotificationResponseListener(
  handler: (r: Notifications.NotificationResponse) => void,
) {
  return Notifications.addNotificationResponseReceivedListener(handler);
}

export function addForegroundNotificationListener(
  handler: (n: Notifications.Notification) => void,
) {
  return Notifications.addNotificationReceivedListener(handler);
}
```

### 9.4 Socket.io client (NEW)

**`src/lib/socket.ts`:**
```typescript
import { io, Socket } from 'socket.io-client';
import { getToken } from '@/lib/auth/utils';
import Env from '@/env';

let socket: Socket | null = null;

export function getSocket(): Socket {
  if (!socket) {
    const baseUrl = Env.EXPO_PUBLIC_API_URL.replace(/\/api\/v1\/?$/, '');
    socket = io(baseUrl, {
      auth: (cb) => cb({ token: getToken()?.accessToken }),
      autoConnect: false,
      transports: ['websocket'],
    });
  }
  return socket;
}

export function connectSocket() {
  const s = getSocket();
  if (!s.connected) s.connect();
  return s;
}

export function disconnectSocket() {
  if (socket?.connected) socket.disconnect();
}
```

**`src/features/notifications/use-notification-socket.ts` (NEW):**
```typescript
export function useNotificationSocket() {
  const queryClient = useQueryClient();
  const status = useAuthStore((s) => s.status);

  useEffect(() => {
    if (status !== 'signIn') return;
    const s = connectSocket();
    const handler = async (payload: { notificationId: string }) => {
      queryClient.invalidateQueries({ queryKey: notificationKeys.all });

      // Dev-only: show a local notification so foreground events are visible without real push
      if (__DEV__) {
        try {
          const fresh = await notificationApi.listNotifications({ limit: 1 });
          const latest = fresh?.data?.notifications?.[0];
          if (latest) {
            await Notifications.scheduleNotificationAsync({
              content: {
                title: latest.title,
                body: latest.body,
                data: { notificationId: latest.id, dev: true },
              },
              trigger: null,
            });
          }
        } catch {}
      }
    };
    s.on('notification:new', handler);
    return () => { s.off('notification:new', handler); disconnectSocket(); };
  }, [status, queryClient]);
}
```

Mounted in `src/app/(app)/_layout.tsx` near the existing notification response listener setup.

### 9.5 Deep-link mapping expansion

Extend `src/app/(app)/_layout.tsx` entityType switch to cover all new trigger events:

```typescript
switch (data.entityType) {
  case 'LeaveRequest':         router.push('/company/hr/my-leave'); break;
  case 'AttendanceRegularization': router.push('/company/hr/my-attendance'); break;
  case 'OvertimeClaim':        router.push('/company/hr/my-attendance'); break;
  case 'Reimbursement':        router.push('/company/hr/my-reimbursement'); break;
  case 'LoanApplication':      router.push('/company/hr/my-loan'); break;
  case 'Interview':            router.push('/company/hr/requisitions'); break;
  case 'TrainingNomination':   router.push('/company/hr/my-training'); break;
  case 'PayslipBatch':         router.push('/company/hr/my-payslips'); break;
  case 'SupportTicket':        router.push(`/company/support/tickets/${data.entityId}`); break;
  case 'ShiftChange':          router.push('/company/hr/my-shifts'); break;
  case 'WfhRequest':           router.push('/company/hr/my-wfh'); break;
  case 'Resignation':          router.push('/company/hr/my-exit'); break;
  case 'Grievance':            router.push('/company/hr/my-grievances'); break;
  default:                     router.push('/notifications');
}
```

### 9.6 User Notification Preferences screen (NEW)

**`src/features/settings/notification-preferences-screen.tsx`:**
- Route: `src/app/(app)/settings/notifications.tsx`
- Same sections as web: Channels, Device Strategy, Quiet Hours, Test Notification button.
- Uses `@gorhom/bottom-sheet` for the time picker.
- Shows company-level master toggles as read-only chips.

### 9.7 Bell icon + notifications sheet enhancements

- `notifications-sheet.tsx`: add priority badge on each row (same color scheme as web), add archive swipe-action.
- `use-notification-count.ts`: change `refetchInterval` from 30_000 to 300_000 (5 min). Socket drives primary updates.
- Add "Preferences" link at the bottom of the sheet that navigates to the new preferences screen.

### 9.8 Notification API client extensions

**`src/lib/api/notifications.ts`:** same additions as web (archive, getPreferences, updatePreferences, getDeliveryEvents, sendTestNotification).

### 9.9 React Query keys

Extend mobile `notificationKeys` factory to match web.

---

## 10. Testing Strategy

### 10.1 Unit tests (backend)

Files under `src/core/notifications/__tests__/`:

- `dispatcher.test.ts` — happy path, no rules fallback, ad-hoc mode, explicit recipients, dedup hit, backpressure drop, dispatcher never throws on internal error.
- `consent-gate.test.ts` — company off, user off, critical override, quiet hours, in-app always allowed.
- `dedup.test.ts` — same payload within TTL dedupes, different payload same entity does not, Redis unavailable fail-open.
- `rule-loader.test.ts` — cache hit, cache invalidation on rule update, empty result returns empty array.
- `recipient-resolver.test.ts` — all 9 role tokens, caching within single dispatch.
- `channel-router.test.ts` — routes to correct provider, in-app no-op, unknown channel throws.
- `push.channel.test.ts` — Expo vs FCM partition, latest-only strategy, dead token cleanup.
- `expo.provider.test.ts` — chunking, `DeviceNotRegistered` detection, ticket ID return.
- `fcm.provider.test.ts` — multicast, invalid token cleanup.
- `template-compiler.test.ts` — compile on save, reject invalid handlebars, allowlist enforcement, unknown var becomes empty.
- `masker.test.ts` — push masks sensitive, in-app does not, nested fields, string vs number values.
- `batcher.test.ts` — threshold trigger, dynamic hold calculation, flush coalescing, HIGH never batched.
- `backpressure.test.ts` — low drops at LOW queue, LOW drops at DEFAULT queue high-water, HIGH never drops.
- `idempotency.test.ts` — SETNX guard, TTL expiry, race condition.

### 10.2 Integration tests (backend)

Files under `src/__tests__/integration/notifications/`:

- `dispatch-end-to-end.test.ts` — uses testcontainers for Postgres + Redis. Calls `dispatch()`, asserts DB rows, socket event fired, BullMQ job enqueued, worker processes job, `NotificationEvent` rows written.
- `consent-enforcement.test.ts` — toggles off, asserts no delivery, dryRun logged.
- `rule-wiring.test.ts` — creates rule, calls dispatcher with trigger event, verifies rendered output.
- `preferences-api.test.ts` — CRUD on preferences, enforcement in dispatch.

### 10.3 Load tests

One-off script at `scripts/load-test-notifications.ts`:

- Dispatches 10,000 notifications to 100 users over 60 seconds.
- Measures dispatcher p50/p95 latency, queue depth peak, worker throughput.
- Pass criteria: dispatcher p95 < 100ms, no DLQ entries, all 10k `NotificationEvent` rows written within 5 minutes.

### 10.4 Web tests

- `NotificationPreferencesScreen.test.tsx` — renders, updates, respects company master state.
- `useNotificationSocket.test.ts` — mock socket, emits event, React Query invalidated.
- Existing `TopBar.test.tsx` updated for 5-min polling interval.

### 10.5 Mobile tests

- `notification-preferences-screen.test.tsx` — renders, updates.
- `use-notification-socket.test.ts` — mock socket.
- `setup.test.ts` — permission denied path, FirebaseApp not initialized path (warn not error).

### 10.6 Manual QA checklist

Run on a physical device with a fresh EAS development build:

1. Install app, log in as company admin.
2. Confirm token registration log line in backend.
3. From a different account, submit a leave request where the admin is the approver.
4. Verify:
   - Bell icon badge updates within <1 second (socket).
   - In-app notification appears in list.
   - Push notification appears on lock screen.
   - Tap notification → app opens to `/company/hr/leave-approvals/{id}`.
5. Toggle off "Push Notifications" in user preferences.
6. Submit another leave request.
7. Verify:
   - Bell icon still updates (in-app is system of record).
   - No push notification on lock screen.
8. Toggle off "Push Notifications" in company settings (as admin).
9. Re-enable user preference.
10. Verify no push fires (company master overrides).
11. Send a `PASSWORD_RESET` (trigger it via forgot-password flow).
12. Verify push fires **even with user prefs off** (CRITICAL override).
13. Send a test `SALARY_CREDITED`.
14. Verify push shows `Your salary of *** has been credited.` (masked).
15. Open app, verify in-app shows `Your salary of INR 75,000 has been credited.` (unmasked).
16. Submit 10 leave requests quickly.
17. Verify batching kicks in after the 5th — subsequent are summarized into one push after ~50s.
18. Log out, log in again, confirm old device token is unregistered and new one registered.
19. Kill the backend temporarily while sending a notification — confirm BullMQ retries, then confirm delivery on restart.

---

## 11. Rollout Plan

### 11.1 Pre-merge checks

- [ ] All unit tests pass
- [ ] All integration tests pass
- [ ] Lint + type-check pass on all three codebases
- [ ] Load test p95 < 100ms
- [ ] Manual QA checklist completed on physical device
- [ ] `pnpm prisma:merge` produces valid `schema.prisma` with no duplicates
- [ ] Migration A + B + C run cleanly on a staging DB snapshot

### 11.2 Deployment order

1. **Staging backend deploy** with feature flag `NOTIFICATIONS_ENABLED=true` and `FIREBASE_SERVICE_ACCOUNT_KEY` set. Migration A runs automatically.
2. Run migration B + C scripts manually (`pnpm tsx prisma/seeds/2026-04-09-seed-default-notification-templates.ts`).
3. Run `pnpm tsx scripts/backfill-notification-columns.ts`.
4. **Staging frontend deploys** (web + mobile EAS preview channel).
5. **Staging manual QA** — full checklist.
6. **Production backend deploy** with `NOTIFICATIONS_ENABLED=true`. Migration A runs. Run migration B + C.
7. **Production web deploy**.
8. **Production mobile EAS update** (OTA — runtime version unchanged, so OTA works).
9. **Monitor** for 24 hours:
   - DLQ count
   - Queue depth (should stay <1000 under normal load)
   - Worker error rate
   - Socket connection count
   - `NotificationEvent` write rate
10. **Follow-up**: delete `Notification.isRead` column (migration D) in a later PR.

### 11.3 Rollback

- If DB rows are corrupted or migration fails: Migration A is additive, so rollback is `DROP COLUMN / DROP TABLE` of new fields. Legacy `notificationService.send()` still works.
- If worker is broken: set `NOTIFICATIONS_ENABLED=false` — dispatcher writes in-app rows and emits socket events, but skips enqueue. Users still see bell updates. No push.
- If push provider credentials are invalid: dispatcher keeps working; individual worker jobs fail into DLQ. Investigate DLQ, fix credentials, retry via `bullmq`'s `job.retry()` API.

### 11.4 Feature flag behavior

- `NOTIFICATIONS_ENABLED=false` — dispatcher short-circuits: writes in-app row, emits socket, does **not** enqueue. Used for emergency off-switch.
- `NOTIFICATIONS_ENABLED=true` — full pipeline active.

---

## 12. Appendix: File Change Summary

### 12.1 Backend files created

```
src/core/notifications/dispatch/dispatcher.ts
src/core/notifications/dispatch/types.ts
src/core/notifications/dispatch/dedup.ts
src/core/notifications/dispatch/recipient-resolver.ts
src/core/notifications/dispatch/rule-loader.ts
src/core/notifications/dispatch/consent-gate.ts
src/core/notifications/dispatch/backpressure.ts
src/core/notifications/dispatch/priority-router.ts
src/core/notifications/dispatch/enqueue.ts
src/core/notifications/queue/queues.ts
src/core/notifications/queue/connection.ts
src/core/notifications/queue/rate-limiter-config.ts
src/core/notifications/workers/notification.worker.ts  (REWRITE of existing)
src/core/notifications/workers/receipt-poller.worker.ts
src/core/notifications/workers/dlq-sweeper.worker.ts
src/core/notifications/workers/batcher.worker.ts
src/core/notifications/channels/channel-router.ts
src/core/notifications/channels/in-app.channel.ts
src/core/notifications/channels/push/push.channel.ts
src/core/notifications/channels/push/expo.provider.ts
src/core/notifications/channels/push/fcm.provider.ts
src/core/notifications/channels/email.channel.ts
src/core/notifications/channels/sms.channel.ts
src/core/notifications/channels/whatsapp.channel.ts
src/core/notifications/templates/compiler.ts
src/core/notifications/templates/renderer.ts
src/core/notifications/templates/masker.ts
src/core/notifications/templates/defaults.ts
src/core/notifications/templates/seed-defaults.ts
src/core/notifications/preferences/preferences.service.ts
src/core/notifications/preferences/preferences.controller.ts
src/core/notifications/preferences/preferences.validators.ts
src/core/notifications/preferences/preferences.routes.ts
src/core/notifications/idempotency/worker-idempotency.ts
src/core/notifications/events/event-emitter.ts
src/core/notifications/events/socket-emitter.ts
src/core/notifications/index.ts
src/core/notifications/notification.validators.ts
src/core/notifications/__tests__/... (14 files listed in §10.1)
prisma/seeds/2026-04-09-seed-default-notification-templates.ts
scripts/backfill-notification-columns.ts
scripts/load-test-notifications.ts
```

### 12.2 Backend files modified

```
src/core/notifications/notification.service.ts     (thin facade)
src/core/notifications/notification.controller.ts  (new endpoints)
src/core/notifications/notification.routes.ts      (new routes)
src/lib/socket.ts                                  (user:{id} room, emit helper)
src/config/env.ts                                  (Zod schema additions)
src/app/server.ts                                  (worker startup wiring)
src/shared/events/listeners/hr-listeners.ts        (use dispatch() API)
src/modules/hr/leave/leave.service.ts              (dispatch calls)
src/modules/hr/attendance/attendance.service.ts    (dispatch calls)
src/modules/hr/ess/ess.service.ts                  (dispatch calls, remove old email-only trigger logic)
src/modules/hr/payroll-run/payroll-run.service.ts  (dispatch calls)
src/modules/hr/employee/employee.service.ts        (dispatch calls)
src/modules/hr/offboarding/offboarding.service.ts  (dispatch calls)
src/modules/hr/advanced/recruitment/recruitment.service.ts (dispatch calls)
src/modules/hr/advanced/training/training.service.ts       (dispatch calls)
src/modules/hr/advanced/assets/assets.service.ts   (dispatch calls)
src/core/support/support.service.ts                (bridge to dispatch)
src/core/auth/auth.service.ts                      (CRITICAL dispatches)
src/core/company/company.service.ts                (seed defaults on tenant create)
prisma/modules/platform/notifications.prisma
prisma/modules/company-admin/settings.prisma
prisma/modules/hrms/ess-workflows.prisma
package.json                                       (add bullmq, expo-server-sdk, handlebars, nanoid)
.env.example                                       (document new env vars)
```

### 12.3 Web files created

```
web-system-app/src/hooks/useNotificationSocket.ts
web-system-app/src/features/settings/NotificationPreferencesScreen.tsx
web-system-app/src/features/settings/api/use-notification-preferences-queries.ts
web-system-app/src/features/settings/api/use-notification-preferences-mutations.ts
```

### 12.4 Web files modified

```
web-system-app/src/App.tsx                                    (new route)
web-system-app/src/layouts/DashboardLayout.tsx                (mount useNotificationSocket)
web-system-app/src/layouts/TopBar.tsx                         (5-min polling, priority badges, settings link)
web-system-app/src/features/notifications/NotificationListScreen.tsx (priority, archive, filters)
web-system-app/src/lib/notifications/setup.ts                 (extended device payload)
web-system-app/src/lib/api/notifications.ts                    (archive, preferences, events, test)
web-system-app/src/lib/socket.ts                               (notification:new support)
web-system-app/src/features/company-admin/CompanySettingsScreen.tsx (3 new toggles)
web-system-app/src/features/super-admin/tenant-onboarding/steps/Step05Preferences.tsx (3 new toggles)
```

### 12.5 Mobile files created

```
mobile-app/src/lib/socket.ts
mobile-app/src/features/notifications/use-notification-socket.ts
mobile-app/src/features/settings/notification-preferences-screen.tsx
mobile-app/src/app/(app)/settings/notifications.tsx
mobile-app/src/features/settings/api/use-notification-preferences.ts
mobile-app/assets/notification-icon.png
```

### 12.6 Mobile files modified

```
mobile-app/app.config.ts                                       (notification icon, critical channel)
mobile-app/package.json                                        (socket.io-client)
mobile-app/src/lib/notifications/setup.ts                      (graceful FCM error, extended payload)
mobile-app/src/app/(app)/_layout.tsx                           (expand deep links, mount socket hook)
mobile-app/src/lib/api/notifications.ts                        (archive, preferences, events, test)
mobile-app/src/features/notifications/notifications-sheet.tsx (priority, archive, preferences link)
mobile-app/src/features/notifications/use-notification-count.ts (5-min polling)
```

---

## 13. Spec Self-Review

**Placeholder scan:** no TBD/TODO/incomplete sections remain. ✅
**Internal consistency:** architecture (§3), data model (§4), backend impl (§5), event map (§6), defaults (§7), web (§8), mobile (§9), tests (§10), rollout (§11), file summary (§12) all cross-reference consistently. ✅
**Scope check:** focused on notification overhaul. Does not include unrelated refactors. Non-goals (§3.4) explicitly carved out. ✅
**Ambiguity check:** consent semantics, dedup key, batching formula, recipient roles, sensitive masking, feature flag behavior all have explicit definitions with examples. ✅
**Migration safety:** all changes additive, zero-downtime, reversible (§4.4, §11.3). ✅
**Backward compat:** legacy `notificationService.send()` kept as thin facade (§5.11), existing bell icon and notification list screens continue to work during deploy. ✅
