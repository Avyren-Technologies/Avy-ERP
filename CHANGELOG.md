# Changelog — Notifications Overhaul

All notable changes on the `feat/per-module-notifications` branch across the
three submodules (`avy-erp-backend`, `web-system-app`, `mobile-app`).

This release rebuilds the notification system from stub-level to a
production-grade multi-channel delivery pipeline with rule-based routing,
per-user + per-category preferences, cost controls, and an analytics
dashboard API.

---

## Architecture

- **Unified dispatcher** — a single `notificationService.dispatch()` entry
  point replaces ~15 ad-hoc notification paths across HR/ESS/payroll/auth/
  support. Adds rule-based channel routing, recipient resolution,
  deduplication, rate limiting, backpressure, and metrics.
- **BullMQ priority queues** — separate queues for `notifications:high`,
  `notifications:default`, `notifications:low` with per-queue concurrency
  and rate limiters. CRITICAL + HIGH never throttle; LOW/MEDIUM batch and
  throttle under load.
- **Five delivery channels** — IN_APP (always), PUSH (Expo + FCM dual-
  transport), EMAIL, SMS (Twilio), WHATSAPP (Meta Cloud API).
- **Two-tier consent model** — company master toggles (authoritative,
  even for CRITICAL) and per-user preferences (bypassable for CRITICAL
  except AUTH category).
- **Category-based user preferences** — 17 categories with fine-grained
  `(category × channel)` matrix. Locked categories (AUTH) cannot be
  opted out of.

---

## Backend (`avy-erp-backend`)

### Data model

- **New models (prisma/modules/platform/notifications.prisma)**
  - `Notification` — system of record for every notification, with
    `traceId`, `ruleId`, `templateId`, `dedupHash`, `deliveryStatus` JSON
    snapshot per channel
  - `UserDevice` — Expo/FCM device registration with `tokenType`,
    `failureCount`, `lastSuccessAt`, platform + locale metadata
  - `NotificationEvent` — event stream for every attempt (ENQUEUED, SENT,
    DELIVERED, OPENED, CLICKED, FAILED, BOUNCED, SKIPPED, RETRYING,
    RATE_LIMITED)
  - `UserNotificationPreference` — channel opt-in + quiet hours +
    device strategy
  - `UserNotificationCategoryPreference` — per-category × channel
    override matrix
  - `NotificationEventAggregateDaily` — pre-aggregated daily rollup
    for the analytics dashboard

- **New enums** — `NotificationPriority`, `DeviceTokenType`,
  `NotificationEventType` (10 values including `RATE_LIMITED`),
  `NotificationSource`, `DeviceStrategy`, `NotificationStatus`

- **Extended models**
  - `NotificationTemplate.whatsappTemplateName` — required when
    `channel === 'WHATSAPP'` (Meta rejects free-form text)
  - `CompanySettings.pushNotifications` / `smsNotifications` /
    `inAppNotifications` — three new master toggles

- **Migration** — `prisma/migrations/20260409_notifications_full/` single
  consolidated migration file for staging/prod deployment

### Core dispatch pipeline

- **`src/core/notifications/dispatch/dispatcher.ts`** (NEW) — primary
  `dispatch()` entry point. Loads rules, resolves recipients, renders
  templates, runs dedup + rate limit + backpressure filters, writes
  Notification rows via `createManyAndReturn` with Map-based userId→row
  correlation (Prisma does not guarantee row order).
- **`src/core/notifications/dispatch/dispatch-bulk.ts`** (NEW) — high-fanout
  utility. REQUIRED for recipients ≥ 20 (payroll fanouts, ALL-role).
  Chunks BullMQ jobs (default 50/chunk), throttles LOW/MEDIUM under
  queue-high-water, amortizes tenant rate-limit check across the batch,
  in-process IN_APP fallback when no rules match (avoids per-recipient
  re-entry into `dispatch()`).
- **`src/core/notifications/dispatch/rule-loader.ts`** (NEW) — 60s Redis
  cache with SCAN-based pattern invalidation, LRU template cache
- **`src/core/notifications/dispatch/recipient-resolver.ts`** (NEW) —
  resolves recipient roles (EMPLOYEE, MANAGER, HR, FINANCE, IT, ADMIN,
  REQUESTER, APPROVER, ALL) to concrete user IDs
- **`src/core/notifications/dispatch/consent-gate.ts`** (NEW) — two-tier
  consent evaluation with:
  - Versioned Redis cache (`notif:consent:{userId}:{userVer}:{companyVer}`)
    for O(1) invalidation
  - Date rehydration on cache hit
  - User→company ID cache (1h TTL)
  - Fail-OPEN for CRITICAL when company settings missing (security/payroll
    must deliver through transient DB outage)
  - Category preference lookup with `isCategoryLocked()` bypass
- **`src/core/notifications/dispatch/rate-limiter.ts`** (NEW) — per-user
  and per-tenant 60s rolling window limits via Redis INCR. CRITICAL
  bypasses both, emits `rate_limit_bypassed` metric counter.
- **`src/core/notifications/dispatch/backpressure.ts`** (NEW) — LOW/MEDIUM
  shedding when queue waiting count exceeds high-water mark
- **`src/core/notifications/dispatch/dedup.ts`** (NEW) — 60s stable
  `dedupHash` via content + company + trigger + entity + recipient
- **`src/core/notifications/dispatch/enqueue.ts`** (NEW) — atomic
  MULTI pipeline for dynamic batching (LOW/MEDIUM categories batch into
  groups, delayed by `pending × 5s` capped at 60s)
- **`src/core/notifications/dispatch/approver-resolver.ts`** (NEW) —
  reusable helper that resolves the current approval workflow step's
  approver user IDs for MANAGER role (reportingManager), HR role
  (permission match), or explicit approver ID. Verifies requesterId
  exists as a user before returning it.

### Channels + providers

- **`channels/channel-router.ts`** (NEW) — single-entry routing to the
  5 channel implementations with a common `ChannelSendArgs` interface
- **`channels/in-app.channel.ts`** — writes unmasked body to Notification
  row (system of record); full content always available in-app
- **`channels/push/push.channel.ts`** — Expo-first routing with FCM
  fallback. Dead-token detection, `failureCount` increment, user-scoped
  cleanup sweeps
- **`channels/push/expo.provider.ts`** — chunked send (100 tokens/chunk)
  + receipt polling cron
- **`channels/push/fcm.provider.ts`** — firebase-admin with graceful init
  (non-fatal if service account missing)
- **`channels/email.channel.ts`** — wraps the existing SMTP service
- **`channels/sms/twilio.provider.ts`** (NEW) — lazy client init,
  exponential-backoff retry on transient (503/429/20429/connection
  resets), messaging-service-sid vs from-number selection, dry-run mode
- **`channels/sms/caps.ts`** (NEW) — per-tenant + per-user daily cost
  caps via Redis INCR (48h TTL, fail-open)
- **`channels/sms.channel.ts`** — caps → masking → E.164 normalization
  (India default) → 1600-char truncate → Twilio send. Title-safe
  concatenation.
- **`channels/whatsapp/meta-cloud.provider.ts`** (NEW) — fetch-based
  Meta Cloud v21.0 client, template message shape, 5xx/429 retry
- **`channels/whatsapp/caps.ts`** (NEW) — same pattern as SMS caps
- **`channels/whatsapp.channel.ts`** — ENFORCES
  `whatsappTemplateName` (§4A.5 — Meta rejects free-form text outside
  the 24h session window), caps, masking, send
- **`channels/provider-retry.ts`** (NEW) — generic exponential-backoff
  retry wrapper for provider calls

### Templates + rendering

- **`templates/compiler.ts`** + **`templates/renderer.ts`** (NEW) —
  Handlebars-backed template compilation with variable allowlist.
  `data` field is built from the allowlist only (no PII leak into
  `Notification.data`).
- **`templates/masker.ts`** (NEW) — channel-aware sensitive field
  masking. `MASKED_CHANNELS = ['PUSH', 'SMS', 'WHATSAPP']`; IN_APP and
  EMAIL always unmasked.
- **`templates/defaults.ts`** (NEW) — 35+ default template catalogue
  covering leave, attendance, overtime, shift, WFH, payroll, loan,
  reimbursement, travel, resignation, recruitment, training, auth,
  support, onboarding, and the 6 cron-driven templates (BIRTHDAY,
  WORK_ANNIVERSARY, HOLIDAY_REMINDER, PROBATION_END_REMINDER,
  CERTIFICATE_EXPIRING, TRAINING_SESSION_UPCOMING)
- **`templates/seeder.ts`** — idempotent per-tenant template seeder

### Worker + DLQ

- **`src/workers/notification.worker.ts`** — rewritten for 3 priority
  queues, `processOne()` shared between single-notification and bulk
  job paths, atomic SETNX idempotency claims (24h TTL), claim/release
  on throw, DLQ move + source removal on retry exhaustion, Firebase
  Admin init awaited BEFORE worker bootstrap (no first-job race).
- **`src/workers/notification-receipt-poller.ts`** — Expo receipt
  polling cron with CAS + cleanup
- **`src/workers/notification-dlq-sweeper.ts`** — dead-letter queue
  sweeper with audit trail

### Cron service (informational + operational)

- **`src/core/notifications/cron/notification-cron.service.ts`** (NEW) —
  9 scheduled jobs:
  - `runBirthday` (08:00 UTC) — today's birthdays per company
  - `runWorkAnniversary` (08:00 UTC) — years > 0 anniversaries
  - `runHolidayReminder` (07:00 UTC) — upcoming holidays in next 3 days
  - `runProbationEnd` (09:00 UTC) — probation ending in next 7 days
    → reporting manager
  - `runCertificateExpiring` (09:00 UTC) — certs expiring in next 30 days
  - `runTrainingSessionUpcoming` (07:00 UTC) — sessions in next 24h
  - `runAssetReturnDue` — STUB (schema needs `expectedReturnDate` field)
  - `runEventAggregation` (01:30 UTC) — raw SQL GROUP BY →
    `NotificationEventAggregateDaily`
  - `runEventCleanup` (02:00 UTC) — delete raw NotificationEvent rows
    older than retention window in 10k batches

  Features:
  - `runPerCompany()` helper with `pLimit(NOTIFICATIONS_CRON_COMPANY_CONCURRENCY)`
    concurrency cap + random jitter (0-60s) to avoid thundering herd
  - Cursor-based pagination (`paginateWithCursor`) in 200-row batches
  - One-shot dedup keys for multi-day reminders (probation 30-day TTL,
    certificate 60-day TTL, holiday 7-day TTL) — no daily spam
  - 24h dedup for true single-day events (birthday, anniversary)
  - `dispatchBulk` for fanouts (holidays, birthdays, anniversaries,
    training sessions)

### Analytics API

- **`analytics/notification-analytics.service.ts`** (NEW)
  - `getSummary(companyId, days)` — totals by event + by-channel
    breakdown + delivery rate, reading from
    `NotificationEventAggregateDaily`
  - `getTopFailing(companyId, days, limit)` — top N failing templates
    via raw SQL JOIN
  - `getDeliveryTrend(companyId, days)` — daily pivoted time series
- **`analytics/notification-analytics.controller.ts`** (NEW) — Zod query
  validation (`days` 1-365, `limit` 1-100), permission-guarded
- **`analytics/notification-analytics.routes.ts`** (NEW) — three GET
  endpoints guarded by `hr:configure`

### Preferences API

- **`preferences/preferences.service.ts`** (NEW)
  - `getForUser(userId)` — returns preferences + companyMasters +
    categoryPreferences + categoryCatalogue
  - `update(userId, data)` — channel + quiet hours update with
    O(1) consent cache invalidation
  - `updateCategoryPreferences(userId, updates)` — batch upsert
    category × channel overrides with locked-category rejection
- **Routes** — `GET /notifications/preferences`,
  `PATCH /notifications/preferences`,
  `PATCH /notifications/preferences/categories`

### Wiring into business services (Phases 2-4)

- **Leave** (`modules/hr/leave/leave.service.ts`) — `createRequest`
  submission dispatch on both cross-year and same-year paths;
  `cancelRequest` dispatches LEAVE_CANCELLED to the original approver
- **Attendance** (`modules/hr/attendance/attendance.service.ts`) —
  `approveOvertimeRequest` / `rejectOvertimeRequest` direct dispatches
  (bypass ApprovalRequest workflow)
- **ESS** (`modules/hr/ess/ess.service.ts`)
  - `createRequest` — single chokepoint dispatch for ALL 13+ ESS
    submission types (leave, shift change/swap, WFH, profile update,
    reimbursement, loan, IT declaration, travel, helpdesk, grievance,
    overtime, training, attendance regularization)
  - `onApprovalComplete` — universal post-switch dispatch via
    `TRIGGER_BY_ENTITY` table covering all 12 approval entity types,
    isolated in its own try/catch
  - `triggerNotification` deprecated → delegates to
    `notificationService.dispatch()`
  - Rule cache invalidation on template/rule CRUD
- **Payroll run** (`modules/hr/payroll-run/payroll-run.service.ts`) —
  `generatePayslips` dispatches PAYSLIP_PUBLISHED via `dispatchBulk`
  (HIGH); `disburseRun` dispatches SALARY_CREDITED via `dispatchBulk`
  (CRITICAL + systemCritical — regulatory)
- **Employee** (`modules/hr/employee/employee.service.ts`) —
  `createEmployee` dispatches EMPLOYEE_ONBOARDED to the new user
- **Transfers** (`modules/hr/transfer/transfer.service.ts`) —
  `applyTransfer` dispatches EMPLOYEE_TRANSFER_APPLIED to employee +
  new manager; `applyPromotion` dispatches EMPLOYEE_PROMOTION_APPLIED
- **Offboarding** (`modules/hr/offboarding/offboarding.service.ts`) —
  `approveFnF` dispatches FNF_INITIATED (HIGH); `payFnF` dispatches
  FNF_COMPLETED (CRITICAL + systemCritical)
- **Recruitment** (`shared/events/listeners/hr-listeners.ts`) —
  candidate stage changes, offer sent/accepted/rejected, interview
  scheduled, training nomination/completion, certificate expiring —
  all now dispatch via the unified pipeline
- **Assets** (`modules/hr/advanced/advanced.service.ts`) —
  `createAssetAssignment` dispatches ASSET_ASSIGNED;
  `returnAssetAssignment` dispatches ASSET_RETURNED
- **Support tickets** (`core/support/support.service.ts`) —
  `createTicket` → TICKET_CREATED, `sendMessage` → TICKET_MESSAGE
  (direction-aware), `updateStatus` → TICKET_STATUS_CHANGED,
  `approveModuleChange` → MODULE_CHANGE_APPROVED (HIGH)
- **Auth** (`core/auth/auth.service.ts`) —
  - `forgotPassword` dispatches PASSWORD_RESET (CRITICAL + systemCritical)
    alongside existing direct email send
  - `trackSession` detects new-device logins (by comparing against ALL
    prior sessions, skipped on first-ever login) and dispatches
    NEW_DEVICE_LOGIN (CRITICAL + systemCritical)

### Metrics + observability

- **`metrics/notification-metrics.ts`** (NEW) — facade with
  `increment`, `histogram`, `gauge` methods logging structured events.
  Wired from: dispatcher, rate limiter, SMS caps, WhatsApp caps, bulk
  dispatch, receipt poller, DLQ sweeper.
- **New metrics**:
  - `notifications.dispatched`, `notifications.dispatch_error`,
    `notifications.dispatch_duration_ms`
  - `notifications.rate_limited{scope:user|tenant, priority}`
  - `notifications.rate_limit_bypassed{scope:user|tenant, priority:CRITICAL}`
  - `notifications.bulk_batch_size`, `notifications.bulk_chunk_size`,
    `notifications.bulk_throttled`

### Tests

- **29 unit tests** under `src/core/notifications/__tests__/` covering:
  - `consent-gate.test.ts` (9 tests) — IN_APP bypass, fail-open/closed
    for CRITICAL, company master authoritative, category override,
    locked category ignore, quiet hours
  - `rate-limiter.test.ts` (8 tests) — CRITICAL bypass metric,
    INCR/EXPIRE pairing, cap exceeded, fail-open
  - `sms-caps.test.ts` (6 tests) — ordering (tenant before user),
    TTL set, fail-open
  - `masker.test.ts` (6 tests) — IN_APP/EMAIL never masked,
    PUSH/SMS/WHATSAPP mask all occurrences

### Env vars (19 new)

- `NOTIFICATIONS_ENABLED`, `NOTIFICATIONS_CRON_ENABLED`,
  `NOTIFICATIONS_BATCH_WINDOW_SEC`, `NOTIFICATIONS_BATCH_THRESHOLD`,
  `NOTIFICATIONS_BULK_CHUNK_SIZE`, `NOTIFICATIONS_BULK_QUEUE_HIGH_WATER`,
  `NOTIFICATIONS_USER_RATE_LIMIT_PER_MIN`,
  `NOTIFICATIONS_TENANT_RATE_LIMIT_PER_MIN`,
  `NOTIFICATIONS_EVENT_RETENTION_DAYS`,
  `NOTIFICATIONS_CRON_COMPANY_CONCURRENCY`,
  `NOTIFICATIONS_CRON_JITTER_MS`, `NOTIFICATIONS_CONSENT_CACHE_TTL_SEC`,
  `NOTIFICATIONS_IDEMPOTENCY_TTL_SEC`, `NOTIFICATIONS_SMS_ENABLED`,
  `NOTIFICATIONS_SMS_DRY_RUN`, `NOTIFICATIONS_SMS_DAILY_CAP_PER_TENANT`,
  `NOTIFICATIONS_SMS_DAILY_CAP_PER_USER`, `NOTIFICATIONS_WHATSAPP_ENABLED`,
  `NOTIFICATIONS_WHATSAPP_DRY_RUN`,
  `NOTIFICATIONS_WHATSAPP_DAILY_CAP_PER_TENANT`,
  `NOTIFICATIONS_WHATSAPP_DAILY_CAP_PER_USER`
- `TWILIO_ACCOUNT_SID`, `TWILIO_AUTH_TOKEN`, `TWILIO_FROM_NUMBER`,
  `TWILIO_MESSAGING_SERVICE_SID`
- `META_WHATSAPP_PHONE_NUMBER_ID`, `META_WHATSAPP_ACCESS_TOKEN`,
  `META_WHATSAPP_API_VERSION` (default `v21.0`)
- `FIREBASE_SERVICE_ACCOUNT_KEY` — FCM web push credentials
- `VITE_APP_VERSION` (web) — passed as header for client metadata

### Dependencies added

`bullmq`, `expo-server-sdk`, `firebase-admin`, `handlebars`,
`twilio`, `p-limit`, `node-cron` (already present, now used)

### Navigation manifest entries

- `notifications-preferences` — User-facing settings path
- `hr-notif-tpl` — Notification Templates (already existed)
- `hr-notif-rules` — Notification Rules (already existed)
- `hr-notif-analytics` — Notification Analytics dashboard (NEW)

---

## Web app (`web-system-app`)

### New files

- **`src/features/settings/NotificationPreferencesScreen.tsx`** — full
  user-facing preference management screen with:
  - Channel opt-in toggles (IN_APP, PUSH, EMAIL, SMS, WHATSAPP) gated
    by company master toggles (disabled visual state + "Disabled by
    company" label)
  - Device strategy radio (ALL / LATEST_ONLY)
  - Quiet hours toggle + start/end time inputs (24h HH:MM validation)
  - Accent-color radio buttons
  - Skeleton loader, error retry UI, ARIA labels
  - React Query-owned state with optimistic update + rollback on error
  - Send Test Notification button (rate-limited backend endpoint)
- **`src/hooks/useNotificationSocket.ts`** — Socket.io client hook that
  joins the `user:{id}` room, invalidates the notification list +
  unread-count queries on `notification:new` events, auto-
  reconnects, cleans up on unmount. Scoped invalidation only (no
  global refetch storms).
- **`src/lib/notifications/setup.ts`** — device registration helper
  (fingerprint via `navigator.userAgentData` with fallback,
  `VITE_APP_VERSION` header)

### Modified files

- **`src/features/company-admin/CompanySettingsScreen.tsx`** — new
  Notifications section with master toggles for PUSH / EMAIL / SMS /
  WHATSAPP. IN_APP not shown (always enabled as system-of-record).
- **`src/lib/api/notifications.ts`** — `NotificationChannel`,
  `NotificationCategoryPreference`, `NotificationCategoryDef` types;
  `getPreferences`, `updatePreferences`, `updateCategoryPreferences`
  (new), `archive`, `getDeliveryEvents`, `sendTestNotification`
- **`src/lib/api/company-admin.ts`** — CompanySettings interface
  extended with `pushNotifications`, `smsNotifications`,
  `inAppNotifications`
- **`src/lib/api/use-auth-mutations.ts`** — `disconnectSocket` on
  logout to prevent stale socket connections across sessions
- **`src/layouts/DashboardLayout.tsx`** + **`TopBar.tsx`** — unread
  count badge + socket mount
- **`src/App.tsx`** — route registration for preferences screen
- **`src/vite-env.d.ts`** + **`vite.config.ts`** — `VITE_APP_VERSION`
  build-time injection

---

## Mobile app (`mobile-app`)

### New files

- **`src/features/settings/notification-preferences-screen.tsx`** —
  mirror of the web preferences screen using native components:
  - Channel opt-in switches (gated by company masters)
  - Device strategy selector
  - Quiet hours toggle + time picker inputs (blur-to-commit + error
    border on invalid HH:MM)
  - ConfirmModal for all confirmations (never `Alert.alert`)
  - Font-inter on every `<Text>`
  - ChevronLeft back button
  - `showSuccess` / `showError` toasts
  - React Query optimistic update + rollback
- **`src/features/notifications/use-notification-count.ts`** — unread
  count hook with 5-minute polling fallback for missed socket events
- **`src/features/notifications/use-notification-socket.ts`** —
  Socket.io client, joins `user:{id}` room, unmount only unsubscribes
  (doesn't disconnect the shared socket). Deep-link routing for
  tapped notifications.
- **`src/lib/notifications/setup.ts`** — Expo push token registration
  with graceful FCM init (non-fatal if credentials missing),
  `expo-device` metadata. Dev echo gated on `!Device.isDevice`.

### Modified files

- **`src/app/(app)/settings/notifications.tsx`** — route matching the
  nav manifest path
- **`src/app/(app)/settings/index.tsx`** — notifications entry in
  settings list
- **`src/app/(app)/_layout.tsx`** — socket mount + deep-link handler
  including support-ticket deep link (`/support/ticket/:id`)
- **`src/features/auth/use-auth-store.ts`** — `disconnectSocket` on
  `signOut` (prevents stale socket across sessions)
- **`src/lib/api/notifications.ts`** — same type additions +
  `updateCategoryPreferences` client method as web
- **`src/features/company-admin/hr/leave-request-screen.tsx`** — minor
  import formatting
- **`package.json`** — `expo-device`, `socket.io-client`

---

## What's intentionally deferred

- **Web + mobile category preference matrix UI** — the client types
  and `updateCategoryPreferences` mutation are wired, but the screens
  still only expose channel-level toggles. Rendering the 17-category
  × 4-channel matrix is a follow-up.
- **Web analytics dashboard screen** — backend API + nav manifest entry
  are live, but the chart UI has not been built.
- **Web onboarding wizard Step 5 toggles** — backend accepts
  `pushNotif` / `smsNotif` / `inAppNotif` in the preferences payload
  with sensible defaults; the wizard UI fields are a follow-up.
- **Exhaustive provider unit tests** (Twilio + Meta Cloud mocks),
  integration tests, load test, manual QA pass, notification icon
  replacement.
- **`AssetAssignment.expectedReturnDate`** schema field — the cron job
  is stubbed until the field is added.

---

## Verification

- `pnpm tsc --noEmit` — clean on all 3 codebases
- `pnpm test -- src/core/notifications/__tests__/` — 29/29 passing
- `pnpm prisma:merge && pnpm db:generate` — runs clean
- Migration SQL matches the current schema (shadow DB verified)

---

## Rollout notes

1. Set `NOTIFICATIONS_ENABLED=false` on first deploy. Run the migration.
   Seed default templates via `pnpm ts-node -T prisma/seeds/2026-04-09-seed-default-notification-templates.ts`.
2. Configure Twilio + Meta Cloud env vars (or leave with
   `NOTIFICATIONS_SMS_DRY_RUN=true` / `NOTIFICATIONS_WHATSAPP_DRY_RUN=true`
   for initial dry-run validation).
3. Turn `NOTIFICATIONS_ENABLED=true`. Worker picks up jobs; cron schedules
   start; receipt poller begins polling Expo tickets.
4. Monitor `notifications.dispatched`, `notifications.rate_limited`,
   `notifications.dispatch_error` metrics. DLQ is the primary failure
   visibility — check `notifications:dlq` queue under `bull:notifications:*`
   in Redis.
5. Tenant admins can manage rules + templates via existing
   `/company/hr/notification-templates` and `notification-rules` screens.


```
CHANGELOG.md created at monorepo root.

  Frontend changes to test manually

  All frontend work on feat/per-module-notifications. Web
  and mobile are near-symmetric.

  Web (web-system-app)

  1. User Notification Preferences screen

  Path: /settings/notifications (from the user menu /
  settings)
  File:
  src/features/settings/NotificationPreferencesScreen.tsx

  - Channel opt-in toggles — IN_APP (always on, disabled),
  PUSH, EMAIL, SMS, WHATSAPP. Each toggle should be
  disabled with "Disabled by company" label if the matching
   company master toggle is off.
  - Device strategy radio — ALL devices vs. LATEST_ONLY
  (most recently active only).
  - Quiet hours — enable toggle + 24h HH:MM start/end
  inputs. Try:
    - enabling with both times set ✅
    - enabling with blank times ❌ should block save
    - setting start === end ❌ should block save
    - valid range ✅
  - Accent color radio — cosmetic, verify it persists
  across reload.
  - Send Test Notification button — fires a
  /notifications/test request. Verify:
    - rate-limited (5/hour) — smash it 6 times → 6th gets
  429
    - test appears in the notifications feed
    - observes the current channel prefs (e.g. turn PUSH
  off, send test → no push)
  - Optimistic update + rollback — disconnect your network,
   toggle a switch, verify the toggle reverts and an error
  toast appears.
  - Skeleton loader — hard reload should show shimmer, not
  a flash of empty state.

  2. Company notification master toggles

  Path: /company/settings → Notifications section
  File:
  src/features/company-admin/CompanySettingsScreen.tsx

  - Master toggles for Push, Email, SMS, WhatsApp (IN_APP
  is not shown — always on).
  - Turn a master off → open the user preferences screen as
   any employee → the matching channel row should be
  disabled + labeled "Disabled by company".
  - Save should persist; re-open to verify.

  3. Real-time notification feed + unread badge

  Files: src/layouts/TopBar.tsx,
  src/layouts/DashboardLayout.tsx,
  src/hooks/useNotificationSocket.ts

  - The bell icon in the top bar should show the unread
  count badge.
  - Trigger any event that fires a notification (create a
  leave request, submit an expense, etc.) — the badge
  should update within 1-2 seconds via the socket, no
  refresh needed.
  - Open the notification dropdown; clicking a notification
   should:
    - mark it as read (badge decrements)
    - route to the notification's actionUrl
  - Log out, then log back in — the socket should cleanly
  disconnect + reconnect. Verify no duplicate socket
  connections in browser devtools (check Network → WS).

  4. Send Test Notification rate-limited endpoint

  - Rate limit is 5/hour. Hit the test button rapidly — 6th
   should return 429 with a toast.

  5. Admin: Notification Templates + Rules screens
  (pre-existing, now with cache invalidation)

  Paths: /company/hr/notification-templates,
  /company/hr/notification-rules

  - Edit any template body/subject → save → new
  notifications immediately use the updated copy (rule
  cache invalidated on save). Previously needed a 60s wait.
  - Edit a rule's channel → save → next trigger fires the
  new channel.

  6. Analytics dashboard (backend-only — no screen yet)

  - The backend API is live at GET
  /notifications/analytics/summary?days=30,
  .../top-failing, .../delivery-trend — you can hit it with
   curl/Postman but there's no web screen yet. Nav manifest
   has the entry but the screen is deferred.

  ---
  Mobile (mobile-app)

  1. User Notification Preferences screen

  Path: /(app)/settings/notifications
  File:
  src/features/settings/notification-preferences-screen.tsx

  - Mirrors web 1:1 — channel switches, device strategy,
  quiet hours with blur-to-commit time inputs (typing
  doesn't save until blur). Invalid HH:MM shows a red error
   border.
  - ConfirmModal (never Alert.alert) for any destructive
  confirmations.
  - Every <Text> uses font-inter.
  - ChevronLeft back button.
  - Toasts via showSuccess / showError, not native alerts.
  - Optimistic update + rollback — same behavior as web.

  2. Push notification registration + device metadata

  File: src/lib/notifications/setup.ts

  - On first app open after login, the app should:
    - request push permission
    - get Expo push token (or FCM token on Android if Expo
  unavailable)
    - POST to /notifications/register-device with platform,
   fcmToken, tokenType, deviceName, osVersion, appVersion,
  locale, timezone
  - Verify in DB: SELECT * FROM user_devices WHERE "userId"
   = '<your user>' should have a fresh row.
  - Graceful FCM init — if Firebase credentials are
  missing, the app should not crash (non-fatal warning in
  logs).
  - Dev echo — on simulator/Expo Go (!Device.isDevice), a
  dev-only echo notification shows the registered token.

  3. Unread count + polling fallback

  File:
  src/features/notifications/use-notification-count.ts

  - Badge on the bell icon.
  - Real-time via socket + 5-minute polling fallback for
  missed socket events.
  - Kill the backend → wait 5 minutes → reconnect backend →
   badge should refresh from the poll without a manual
  pull-to-refresh.

  4. Socket deep-links

  File:
  src/features/notifications/use-notification-socket.ts +
  src/app/(app)/_layout.tsx

  - Tap a push/socket notification while app is running →
  should route to the entity:
    - Leave → /company/hr/my-leave (or similar based on
  actionUrl)
    - Support ticket → /support/ticket/:id (specifically
  verified)
    - Asset → /company/hr/my-assets
  - Tap a notification while app is killed/backgrounded →
  cold-start should still deep-link correctly.

  5. Session disconnect on logout

  File: src/features/auth/use-auth-store.ts

  - Logout → verify socket disconnects (no stale
  subscription carried into the next login session). Log
  back in as a different user → verify you don't see the
  previous user's notifications.

  6. Time input on preferences screen

  - Tap quiet hours start → type 25:30 → blur → red border,
   field retains draft
  - Type 22:00 → blur → commits and saves
  - Enable quiet hours with no times set → save
  button/toggle blocked with error toast

  ---
  Cross-device smoke tests

  1. End-to-end leave flow — submit a leave request on
  mobile → approver's web app shows the notification within
   2 seconds → approve → requester's mobile shows
  LEAVE_APPROVED push + in-app feed update.
  2. Payroll fanout — trigger payroll run disburse on web
  (publish button on a test run) → every test employee's
  mobile should receive SALARY_CREDITED within 30s (uses
  bulk dispatch with backpressure).
  3. New device login — log into mobile from a second
  phone/simulator → primary device receives
  NEW_DEVICE_LOGIN push (CRITICAL).
  4. Forgot password — trigger forgot password flow →
  receive both email (existing behavior) and push (new
  behavior) containing the reset code. Verify the code is
  masked in the push notification (shows ***) but unmasked
  in the email.
  5. Quiet hours — set quiet hours 22:00-07:00 on mobile.
  Trigger a LOW-priority notification inside that window →
  should NOT be delivered. Trigger a CRITICAL one → should
  still be delivered.

  ---
  What is NOT yet visible on frontends (deferred)

  - Category × Channel matrix UI — the 17 categories can be
   toggled per channel via the API but there's no screen
  rendering the matrix yet.
  - Web Notification Analytics dashboard screen — API is
  ready; chart rendering is pending.
  - Web onboarding wizard Step 5 push/SMS/in-app toggle
  fields — backend accepts them; UI fields not yet added.

  Let me commit the changelog:

⏺ Bash(cd /Users/chetan/Documents/Avyren-Technologies/Produ
      cts/Mobile-ERP && git add CHANGELOG.md && git commit
      -m "docs: add CHANGELOG.md for
      feat/per-module-notifica…)
  ⎿  [main 6ffa47d] docs: add CHANGELOG.md for feat/pe
     r-module-notifications
      1 file changed, 468 insertions(+)
      create mode 100644 CHANGELOG.md

⏺ Committed.

  Summary:
  - CHANGELOG.md at monorepo root (468 lines) covering
  everything on the branch — architecture, data model,
  dispatch pipeline, 5 channels + providers, cron jobs,
  analytics, preferences, business service wiring, tests,
  env vars, deps, nav manifest, web preferences screen +
  socket, mobile preferences screen + push setup, and
  deferred items.
  - Manual testing guide above organized by web screens (6
  areas), mobile screens (6 areas), and 5 cross-device
  end-to-end smoke tests to exercise the full dispatch
  pipeline.

  The three biggest end-to-end flows to hit first are:
  leave request → approval cycle, payroll disburse fanout,
  and forgot password → dual email+push with masking. Those
   exercise every layer (submission wiring, dispatchBulk,
  consent gate, channel router, templates, masking,
  deep-links).
  ```