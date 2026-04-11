# Manual QA Checklist — Notifications System

Comprehensive end-to-end validation for the `feat/per-module-notifications` branch. Test in order — each section builds on the previous one. Mark ✅/❌ as you go.

---

## Environment Prerequisites

- [ ] Backend running with `NOTIFICATIONS_ENABLED=true`
- [ ] Redis + Postgres reachable
- [ ] Migration applied: `prisma/migrations/20260409_notifications_full/`
- [ ] Default templates seeded: `pnpm ts-node -T prisma/seeds/2026-04-09-seed-default-notification-templates.ts`
- [ ] Test tenant with ≥3 users: one `SUPER_ADMIN`, one `COMPANY_ADMIN`, one regular `user` (employee with reportingManager set)
- [ ] At least 1 active approval workflow for `LEAVE_APPLICATION` + `RESIGNATION` + `EXPENSE_REIMBURSEMENT` + `LOAN_APPLICATION`
- [ ] Twilio credentials set OR `NOTIFICATIONS_SMS_DRY_RUN=true`
- [ ] Meta Cloud credentials set OR `NOTIFICATIONS_WHATSAPP_DRY_RUN=true`
- [ ] FCM service account key OR warning-only (Expo push still works)
- [ ] Two devices for mobile testing (or Expo Go + a physical phone)

---

## 1. Authentication + Device Registration

### 1.1 Mobile push token registration
- [ ] Fresh install of mobile app on physical device → log in → permission prompt appears
- [ ] Grant permission → check backend logs for `Device registered` entry
- [ ] Verify DB: `SELECT * FROM user_devices WHERE "userId" = '<user>'` shows a row with `fcmToken`, `platform`, `deviceName`, `osVersion`, `appVersion`, `locale`, `timezone`
- [ ] Deny permission → app should NOT crash; backend has no device row; warning in logs
- [ ] Log out → log back in with same device → existing row updated (not duplicated), `lastActiveAt` refreshed
- [ ] Log in from a **second device** → two rows exist for the user

### 1.2 Web device registration
- [ ] Log in on web → check DB for a `WEB` platform row with FCM web token (if Firebase configured)
- [ ] `VITE_APP_VERSION` should appear in the `appVersion` column
- [ ] Log out → row remains but socket disconnects (verify in browser DevTools → Network → WS, connection closes)

### 1.3 Forgot password (CRITICAL dual-channel)
- [ ] Trigger forgot password flow from web login
- [ ] Verify email arrives with **unmasked** 6-digit reset code
- [ ] Verify push notification arrives on mobile with **masked** code (`***`)
- [ ] Verify in-app notification feed shows the event
- [ ] Rapidly trigger 5 forgot-password requests in 60 seconds → 5 should succeed (CRITICAL bypasses rate limit)
- [ ] Verify `notifications.rate_limit_bypassed` metric was logged

### 1.4 New-device login detection
- [ ] From an already-logged-in user, log in from a **second phone/browser with different deviceInfo** → primary device receives `NEW_DEVICE_LOGIN` push (CRITICAL)
- [ ] Log in from the SAME device again → NO new-device notification fires
- [ ] First-ever login on a brand-new user → NO new-device notification (verify it doesn't spam on onboarding)

---

## 2. User Preferences Screen (Web)

### 2.1 Channel toggles
- [ ] Open `/settings/notifications`
- [ ] IN_APP row shows "Always enabled" badge, toggle is disabled
- [ ] Turn Push off → save → log event → fire any notification → push not delivered, in-app appears
- [ ] Turn Push back on → push resumes
- [ ] Turn Email off → receive a LOW priority notification → email skipped
- [ ] Turn Email off → trigger a CRITICAL (e.g., forgot password) → email **still delivers** (CRITICAL bypass)

### 2.2 Quiet hours
- [ ] Enable quiet hours, leave both times blank → save → blocked with error
- [ ] Set start = 22:00, end = 22:00 → save → blocked (same value)
- [ ] Set start = 22:00, end = 07:00 → save → accepted
- [ ] With quiet hours active (during the window), fire a LOW priority notification → blocked, reason `QUIET_HOURS` in logs
- [ ] During quiet hours, fire a HIGH priority → delivered (quiet hours only suppress LOW/MEDIUM)
- [ ] During quiet hours, fire a CRITICAL → delivered
- [ ] Overnight range 22:00–07:00 at 23:00 → blocked LOW
- [ ] Overnight range 22:00–07:00 at 09:00 → allowed LOW

### 2.3 Device strategy
- [ ] With 2 registered devices, set strategy = `ALL` → push fires → BOTH devices receive
- [ ] Switch to `LATEST_ONLY` → push fires → ONLY the most recently active device receives

### 2.4 Category × Channel matrix
- [ ] Scroll to "Fine-tune by category" section
- [ ] 17 categories visible with descriptions
- [ ] AUTH row has lock icon, switches disabled, cannot be toggled
- [ ] BILLING row also locked
- [ ] Toggle LEAVE × PUSH to off → trigger a leave-related push → NOT delivered via push but IN_APP still appears
- [ ] Toggle LEAVE × PUSH back to on → next leave push delivers
- [ ] Rapidly toggle a cell off/on → optimistic update works, no flicker, no double request
- [ ] Disconnect network → toggle a cell → verify rollback (switch reverts) + error toast

### 2.5 Send Test Notification
- [ ] Click "Send Test Notification" → success toast + notification appears in the feed
- [ ] Click 6 times rapidly → 6th returns 429 with "Too many test notifications" toast
- [ ] Test notification honors current channel prefs (turn push off → test doesn't push)

### 2.6 Accessibility + loading states
- [ ] Hard reload → skeleton loader appears briefly
- [ ] Disconnect backend → reload → error UI + Retry button
- [ ] Tab through the screen with keyboard → all switches focusable, ARIA labels read correctly

---

## 3. User Preferences Screen (Mobile)

### 3.1 Channel + strategy + quiet hours
- [ ] Open Settings → Notifications
- [ ] ChevronLeft back button works
- [ ] Every text element uses `font-inter` (visual check)
- [ ] No `Alert.alert` modals — all feedback via toast
- [ ] Quiet hours time input: type `25:30` → blur → red border appears, field retains draft
- [ ] Type `22:00` → blur → commits and saves
- [ ] Channel + device strategy + optimistic update behavior mirrors web

### 3.2 Category matrix (mobile)
- [ ] Scroll to "Fine-tune by Category"
- [ ] 17 rows × 4 channel columns render correctly on phone-sized screen
- [ ] Locked rows (AUTH + BILLING) show lock icon + dimmed labels + disabled switches
- [ ] Toggle a cell → optimistic update → verify persistence on reload
- [ ] Toggle PAYROLL × PUSH off → trigger payroll publish → push skipped

---

## 4. Company Admin — Master Toggles + Templates + Rules

### 4.1 Company notification master toggles
- [ ] As COMPANY_ADMIN, open `/company/settings` → Notifications section
- [ ] IN_APP not shown (always on)
- [ ] Push, Email, SMS, WhatsApp master toggles present
- [ ] Turn SMS off at company level
- [ ] Log in as a regular employee → prefs screen → SMS row shows "Disabled by company" label, switch disabled
- [ ] Trigger any notification → SMS channel skipped, reason `COMPANY_MASTER_OFF` in logs
- [ ] Even CRITICAL notifications respect company master off (regulatory compliance)

### 4.2 Templates CRUD + rule cache invalidation
- [ ] Open `/company/hr/notification-templates`
- [ ] Edit `LEAVE_APPROVED` template body → save
- [ ] Immediately trigger a leave approval → new body appears in notification (NO 60s wait)
- [ ] Create a brand-new template → save → shows in list
- [ ] Delete a template that has rules linked → cascade removes the rules

### 4.3 Notification Rules CRUD
- [ ] Open `/company/hr/notification-rules`
- [ ] Change a rule's channel from PUSH to EMAIL → save
- [ ] Immediately trigger the rule → next notification comes via EMAIL, not PUSH
- [ ] Deactivate a rule → next trigger does NOT fire that rule

### 4.4 WhatsApp template enforcement
- [ ] Create a new NotificationTemplate with channel = WHATSAPP, leave `whatsappTemplateName` blank → save → rejected with Zod error
- [ ] Fill `whatsappTemplateName` → save → accepted
- [ ] Trigger a WhatsApp notification on a template WITHOUT `whatsappTemplateName` → worker throws `WHATSAPP_TEMPLATE_REQUIRED`, job moves to DLQ after retry exhaustion

---

## 5. Super Admin — Tenant Onboarding Step 5

- [ ] Open the create-tenant wizard → navigate to Step 5 Preferences
- [ ] Verify Email, Push, In-App, SMS toggles are all present
- [ ] WhatsApp shows "COMING SOON"
- [ ] Submit the wizard with Push=ON, SMS=OFF, InApp=ON
- [ ] Verify DB: `SELECT * FROM company_settings WHERE "companyId" = '<new tenant>'` shows `pushNotifications=true`, `smsNotifications=false`, `inAppNotifications=true`
- [ ] Log in as the new tenant admin → prefs screen reflects the master toggles correctly

---

## 6. Notification Analytics Dashboard (Web)

- [ ] Open `/company/hr/notification-analytics` as a user with `hr:configure`
- [ ] As a user WITHOUT `hr:configure` → route denied (403 or redirect)
- [ ] 5 KPI cards render: Sent / Delivered / Failed / Delivery rate / Skipped
- [ ] Window toggle: 7d / 30d / 90d — each switches the query
- [ ] Trend chart renders with stacked areas (Sent + Delivered) and lines (Failed + Skipped)
- [ ] By-channel breakdown table shows IN_APP + PUSH + EMAIL with delivery rates
- [ ] Top failing templates table shows any templates with FAILED events
- [ ] On a fresh tenant with no notification events → ZeroDataState appears with CTA
- [ ] Hit the endpoints directly:
  - [ ] `GET /notifications/analytics/summary?days=30` → 200
  - [ ] `GET /notifications/analytics/summary?days=400` → 400 (max 365)
  - [ ] `GET /notifications/analytics/delivery-trend?days=7` → 200
  - [ ] `GET /notifications/analytics/top-failing?days=30&limit=10` → 200

---

## 7. Real-Time Socket + Deep Links

### 7.1 Web socket
- [ ] Log in → open DevTools → Network → WS → verify `socket.io` connection to `user:{id}` room
- [ ] Trigger any notification (e.g., submit an expense) → badge updates within 1-2s without refresh
- [ ] Click a notification in the dropdown → marks as read + routes to `actionUrl`
- [ ] Log out → verify WS connection closes (no stale socket in Network)
- [ ] Log back in → fresh socket, no duplicates

### 7.2 Mobile socket
- [ ] Open app after login → socket joins `user:{id}` room (check backend logs)
- [ ] Trigger a leave request from web → mobile badge updates within 2s
- [ ] Kill the backend → wait 5 minutes → bring backend back → mobile badge refreshes via polling fallback
- [ ] Log out → socket disconnects

### 7.3 Deep-link routing (mobile)
- [ ] Trigger a leave notification with `actionUrl=/company/hr/my-leave`
- [ ] Tap the push while app is in **foreground** → routes to my-leave screen
- [ ] Tap the push while app is in **background** → routes correctly
- [ ] Tap the push while app is **killed** → cold-start lands on the correct screen
- [ ] Support ticket deep link: `/support/ticket/:id` → routes to specific ticket
- [ ] Asset deep link: `/company/hr/my-assets` → routes to assets list

---

## 8. Core Business Flows — End-to-End

### 8.1 Leave Application
- [ ] Employee submits leave → approver receives `LEAVE_APPLICATION` push within 2s
- [ ] Approver approves → requester receives `LEAVE_APPROVED` push
- [ ] Submit another leave → approver rejects → requester receives `LEAVE_REJECTED` push with reason token
- [ ] Requester cancels an approved future-dated leave → approver receives `LEAVE_CANCELLED`

### 8.2 Attendance Regularization
- [ ] Employee submits regularization → approver receives `ATTENDANCE_REGULARIZATION` push
- [ ] Approve via workflow → employee receives `ATTENDANCE_REGULARIZED`

### 8.3 Overtime
- [ ] Employee submits OT claim → approver push fires
- [ ] Approve directly (bypassing workflow) → employee receives `OVERTIME_CLAIM_APPROVED`
- [ ] Reject → `OVERTIME_CLAIM_REJECTED` with notes in tokens

### 8.4 ESS Submissions (spot-check 5 of the 13 types)
- [ ] Shift change request → push to approver
- [ ] WFH request → push to approver
- [ ] Reimbursement claim → push to approver
- [ ] Travel request → push to approver
- [ ] Helpdesk ticket → push to approver/HR

### 8.5 Payroll Fanout (bulk dispatch)
- [ ] Create a payroll run with ≥20 test employees
- [ ] Run generate payslips → every employee receives `PAYSLIP_PUBLISHED` push (HIGH)
- [ ] Verify backend logs show `notifications.bulk_batch_size` + `bulk_chunk_size` metrics
- [ ] Run disburse → every employee receives `SALARY_CREDITED` (CRITICAL + systemCritical)
- [ ] Even employees with quiet hours active should receive SALARY_CREDITED (CRITICAL bypasses)
- [ ] Verify backpressure: if queue is overloaded, LOW/MEDIUM should throttle but CRITICAL doesn't

### 8.6 Employee Lifecycle
- [ ] Create a new employee → new employee receives `EMPLOYEE_ONBOARDED` on first login
- [ ] Initiate a transfer → workflow approval → apply → employee + new manager receive `EMPLOYEE_TRANSFER_APPLIED`
- [ ] Initiate a promotion → approve → apply → employee receives `EMPLOYEE_PROMOTION_APPLIED` (HIGH)

### 8.7 Offboarding
- [ ] Employee submits resignation → HR/approver receives `RESIGNATION` push
- [ ] Approve → employee status = NOTICE_PERIOD
- [ ] Compute F&F → approve F&F → exiting employee receives `FNF_INITIATED` (HIGH)
- [ ] Mark F&F paid → employee receives `FNF_COMPLETED` (CRITICAL + systemCritical — regulatory)

### 8.8 Recruitment
- [ ] Advance a candidate stage → HR receives `CANDIDATE_STAGE_CHANGED`
- [ ] Send an offer → HR receives `OFFER_SENT`
- [ ] Mark offer as ACCEPTED → HR receives `OFFER_ACCEPTED` (HIGH)
- [ ] Mark offer as REJECTED → HR receives `OFFER_REJECTED`
- [ ] Schedule an interview → panelists receive `INTERVIEW_SCHEDULED`

### 8.9 Training + Assets
- [ ] Create a training nomination → employee receives `TRAINING_NOMINATION`
- [ ] Mark training completed → employee receives `TRAINING_COMPLETED`
- [ ] Assign an asset → employee receives `ASSET_ASSIGNED`
- [ ] Return an asset → employee receives `ASSET_RETURNED`

### 8.10 Support Tickets
- [ ] Company admin creates ticket → super-admin team receives `TICKET_CREATED`
- [ ] Super-admin replies → company admin receives `TICKET_MESSAGE`
- [ ] Company admin replies → super-admin team receives `TICKET_MESSAGE` (direction-aware)
- [ ] Status change → creator receives `TICKET_STATUS_CHANGED`
- [ ] Module change approved → company admin receives `MODULE_CHANGE_APPROVED` (HIGH)

### 8.11 New Backend Gap Fixes (verify all 9)
- [ ] **Loan disbursed**: Admin updates a loan to ACTIVE → employee receives `LOAN_DISBURSED` (HIGH + systemCritical)
- [ ] **Loan closed**: Mark a loan CLOSED → employee receives `LOAN_CLOSED`
- [ ] **Travel advance settled**: Settle a travel advance against an expense claim → employee receives `TRAVEL_ADVANCE_SETTLED` with outcome (EMPLOYEE_OWES / COMPANY_OWES / EXACT)
- [ ] **Appraisal cycle activated**: Admin activates a cycle → all active employees receive `APPRAISAL_CYCLE_ACTIVATED` (MEDIUM, bulk)
- [ ] **Appraisal ratings published**: Admin publishes ratings → every employee with an entry receives `APPRAISAL_RATINGS_PUBLISHED` (HIGH + systemCritical) — even during quiet hours
- [ ] **Expense claim approved**: Approve an expense claim → requester receives `EXPENSE_CLAIM_APPROVED` with amounts
- [ ] **Expense claim partially approved**: Partially approve → `EXPENSE_CLAIM_PARTIALLY_APPROVED`
- [ ] **Expense claim rejected**: Reject → `EXPENSE_CLAIM_REJECTED` with reason
- [ ] **Subscription cancelled**: Super admin cancels tenant → all company admins receive `SUBSCRIPTION_CANCELLED` (CRITICAL + systemCritical) with export window date
- [ ] **Billing type changed**: Change billing type → all company admins receive `BILLING_TYPE_CHANGED` (HIGH)
- [ ] **Role changed**: Admin assigns a different role to a user → user receives `USER_ROLE_CHANGED` (HIGH + systemCritical)
- [ ] **User deactivated**: Admin disables a user → user receives `USER_DEACTIVATED` before next login attempt
- [ ] **User reactivated**: Re-enable → user receives `USER_REACTIVATED`

---

## 9. Cron Jobs

**Preparation**: temporarily change one cron schedule to `* * * * *` (every minute) to test without waiting.

- [ ] **Birthday** (`runBirthday`): Set an employee's `dateOfBirth` to today (MM-DD match) → wait for cron → employee receives `BIRTHDAY` push
- [ ] Verify the same cron re-running in the same day is a no-op (24h dedup)
- [ ] **Work anniversary**: Set joining date to same MM-DD as today but 1+ years ago → `WORK_ANNIVERSARY` with years_of_service token
- [ ] Same-day hire (years = 0) → NO notification
- [ ] **Holiday reminder**: Create a holiday 2 days from now → `HOLIDAY_REMINDER` fans out to all active employees
- [ ] Re-run the cron next day → holiday still in window but NO duplicate (7-day TTL dedup)
- [ ] **Probation end reminder**: Set an employee's `probationEndDate` to 5 days from now → reporting manager receives `PROBATION_END_REMINDER`
- [ ] Re-run next day → NO duplicate (30-day TTL, keyed by end date)
- [ ] **Certificate expiring**: Set a training nomination's `certificateExpiryDate` to 20 days from now → employee receives `CERTIFICATE_EXPIRING`
- [ ] Re-run → NO duplicate (60-day TTL)
- [ ] **Training session upcoming**: Create a session with `startDateTime` in 12 hours → all nominees receive `TRAINING_SESSION_UPCOMING`
- [ ] **Event aggregation** (1:30 AM): Insert some notification events, wait for cron → `NotificationEventAggregateDaily` rows populated
- [ ] **Retention cleanup** (2:00 AM): Insert an old notification event (backdate > 90 days), run cron → row deleted in batch

---

## 10. Backend Guardrails

### 10.1 Rate limits
- [ ] Fire 25 non-CRITICAL notifications to one user in 60s → first 20 delivered, next 5 dropped with `rate_limited` metric
- [ ] Fire 1005 non-CRITICAL to one tenant in 60s → tenant cap kicks in
- [ ] Fire CRITICAL during cap exceeded → delivered (bypass)
- [ ] Redis down → rate limiter fails OPEN (deliveries continue)

### 10.2 Backpressure
- [ ] Stop the worker, enqueue >500 LOW jobs → queue high-water exceeded
- [ ] Trigger a new LOW notification → dropped with `backpressure` reason
- [ ] Trigger a CRITICAL during backpressure → delivered (never throttled)
- [ ] Start worker back up → queue drains

### 10.3 Deduplication
- [ ] Submit the same leave request twice in quick succession → only ONE notification per approver (dedup window 60s)
- [ ] Submit at 61s mark → new notification fires (dedup window expired)

### 10.4 Idempotency
- [ ] Simulate a worker crash mid-delivery (kill worker after claim, before provider call) → restart worker → notification delivers ONCE total (SETNX idempotency claim prevents double-send)

### 10.5 SMS cost caps
- [ ] Set `NOTIFICATIONS_SMS_DAILY_CAP_PER_USER=3` → fire 5 SMS to one user → first 3 delivered, next 2 throw `SMS_USER_CAP`
- [ ] Set `NOTIFICATIONS_SMS_DAILY_CAP_PER_TENANT=10` → 11th SMS returns `SMS_TENANT_CAP`
- [ ] Verify user counter NOT incremented when tenant cap already hit

### 10.6 WhatsApp template enforcement
- [ ] Trigger a WhatsApp dispatch on a template WITHOUT `whatsappTemplateName` → throws `WHATSAPP_TEMPLATE_REQUIRED`
- [ ] Meta Cloud returns 500 → retries 3 times with backoff → still fails → job moves to DLQ

### 10.7 Sensitive field masking
- [ ] Template has `sensitiveFields: ['reset_code']`
- [ ] Trigger push → body masked with `***`
- [ ] Same template via email → body UNMASKED (full code)
- [ ] Same template via IN_APP → body UNMASKED

### 10.8 DLQ
- [ ] Force a permanent provider failure (bad Twilio credentials) → worker retries 3x → moves to DLQ
- [ ] Verify `bull:notifications:dlq` has the failed job with original payload + error
- [ ] Verify source queue does NOT accumulate failed jobs (removed after DLQ move)

### 10.9 Consent cache invalidation
- [ ] User toggles push off → next dispatch reads the new pref within milliseconds (versioned cache key)
- [ ] Company admin changes master toggle → next dispatch picks it up within 5 minutes (TTL-based)
- [ ] Edit a notification rule → next trigger uses the new channel immediately (cache invalidated on CRUD)

---

## 11. Observability

- [ ] Check `notifications.dispatched` metric logged on every successful dispatch
- [ ] Check `notifications.dispatch_error` on failed dispatches
- [ ] Check `notifications.dispatch_duration_ms` histogram
- [ ] Check `notifications.rate_limited{scope, priority}` counter
- [ ] Check `notifications.rate_limit_bypassed{scope, priority:CRITICAL}` counter
- [ ] Check `notifications.bulk_batch_size` + `bulk_chunk_size` + `bulk_throttled` on fanouts
- [ ] `NotificationEvent` rows written for every ENQUEUED → SENT → DELIVERED state transition
- [ ] `traceId` flows from dispatch through worker through provider call (grep logs)

---

## 12. Permission & Security

- [ ] Regular employee cannot access `/company/hr/notification-templates`, `notification-rules`, `notification-analytics` (requires `hr:configure`)
- [ ] Regular employee CAN access `/settings/notifications`
- [ ] Cross-tenant check: User A cannot see User B's notifications even with URL manipulation
- [ ] Socket auth: connecting with an invalid JWT → rejected
- [ ] Socket auth: connecting to someone else's `user:{id}` room → rejected
- [ ] SQL injection on analytics query params (`?days='; DROP TABLE`) → Zod rejects
- [ ] Rate limit on `/notifications/test`: 5/hour per user, returns 429 with clean error

---

## 13. Cross-Tenant + Cross-Session Isolation

- [ ] Log in as Tenant A admin → trigger notification → only Tenant A users receive
- [ ] Log in as Tenant A in Browser 1, log in as Tenant B in Browser 2 → notifications don't cross
- [ ] Log out of Tenant A → socket disconnects → log in as Tenant B → no stale Tenant A notifications appear
- [ ] Mobile: log out → log in as different user → no leaked notifications

---

## 14. Regression: Existing Functionality

- [ ] Legacy ESS screens (leave submit, expense submit, etc.) still work
- [ ] Existing socket events (ticket:message, ticket:new, ticket:resolved) still fire
- [ ] Audit log still captures notification CRUD
- [ ] HR dashboards not broken
- [ ] Email delivery via existing SMTP integration still works

---

## 15. Performance Sanity

- [ ] Single dispatch with 1 recipient completes in <200ms (DB + enqueue only, actual delivery async)
- [ ] Bulk dispatch with 500 recipients completes in <2s (chunked into ~10 BullMQ jobs)
- [ ] Cron with 50 tenants running in parallel (concurrency=5) — no connection pool exhaustion
- [ ] `GET /notifications/preferences` < 100ms (cached)
- [ ] Analytics `/summary?days=30` < 500ms (reads pre-aggregated table)

---

## Sign-off

| Section | Tester | Date | Status |
|---|---|---|---|
| Section 1: Auth + Device | | 2026-04-10 | |
| Section 2: Web Preferences | | | |
| Section 3: Mobile Preferences | | | |
| Section 4: Admin Screens | | | |
| Section 5: Tenant Onboarding | | | |
| Section 6: Analytics Dashboard | | | |
| Section 7: Sockets + Deep Links | | | |
| Section 8: Business Flows | | | |
| Section 9: Cron Jobs | | | |
| Section 10: Guardrails | | | |
| Section 11: Observability | | | |
| Section 12: Permissions | | | |
| Section 13: Isolation | | | |
| Section 14: Regression | | | |
| Section 15: Performance | | | |

---

**Blockers to fix before marking complete:** any ❌ in sections 1, 8, 10, 12, 13.

**Acceptable deferrals** (known limitations, not bugs):
- Asset return due cron is stubbed (schema gap)
- Web/mobile screens for some edge flows still rely on polling fallback if socket drops
- Meta Cloud template approval is a manual business-side step outside the app
