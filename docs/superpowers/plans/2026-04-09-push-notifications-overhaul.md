# Push Notifications Overhaul Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Rebuild push notifications end-to-end across backend, web, and mobile: fix the silent FCM-vs-Expo bug, introduce a unified `dispatch()` pipeline with BullMQ async delivery, two-tier consent enforcement, rule-driven templating, real-time socket updates, and full observability.

**Architecture:** Single `notificationService.dispatch()` sync entry point writes in-app rows and enqueues into priority-partitioned BullMQ queues. Workers honor company + user consent, handle retries/DLQ/dedup/idempotency/batching/backpressure, route push to Expo Server SDK or firebase-admin by token type, and emit `NotificationEvent` rows for analytics. Web/mobile clients listen to Socket.io `notification:new` for instant bell updates and expose a per-user preferences screen.

**Tech Stack:**
- **Backend:** Node.js, Express, Prisma, PostgreSQL, Redis, Socket.io, BullMQ (new), firebase-admin, expo-server-sdk (new), handlebars (new), nanoid (new), Zod
- **Web:** React, Vite, TypeScript, Tailwind, Zustand, React Query, socket.io-client (existing), Firebase Web SDK
- **Mobile:** Expo SDK 54, React Native 0.81.5, Expo Router 6, expo-notifications, expo-device, expo-application, socket.io-client (new), Zustand, React Query, MMKV

**Branch:** `feat/notifications` (already checked out on all three submodules + root)

**Spec reference:** `docs/superpowers/specs/2026-04-09-push-notifications-overhaul-design.md`

---

## Phase Overview

| Phase | Tasks | Description | Depends on |
|---|---|---|---|
| 1. Foundation | 1-3 | Dependencies, env vars, schema migrations | — |
| 2. Core infra | 4-11 | BullMQ, Redis helpers, template engine, socket emitter | Phase 1 |
| 3. Dispatcher | 12-16 | Rule loader, recipient resolver, consent gate, dispatcher | Phase 2 |
| 4. Workers | 17-20 | Notification worker, receipt poller, batcher, DLQ sweeper | Phase 3 |
| 5. Channels | 21-26 | Channel router, Expo + FCM providers, email/SMS/WhatsApp channels | Phase 3 |
| 6. REST + facade | 27-30 | Preferences API, notification endpoint extensions, legacy facade, default seeding | Phase 3 |
| 7. Event wiring | 31-41 | ~50 dispatch sites across HR, ESS, payroll, support, auth | Phase 6 |
| 8. Web | 42-49 | Socket hook, preferences screen, toggles, polling reduction | Phase 6 |
| 9. Mobile | 50-57 | app.config.ts, setup hardening, socket client, preferences screen, deep links | Phase 6 |
| 10. Tests + QA | 58-62 | Unit, integration, load test, manual QA, rollout | Phase 9 |

---

## Phase 1: Foundation

### Task 1: Backend — install dependencies + env vars

**Files:**
- Modify: `avy-erp-backend/package.json`
- Modify: `avy-erp-backend/src/config/env.ts`
- Modify: `avy-erp-backend/.env.example`

- [ ] **Step 1: Install new dependencies**

```bash
cd avy-erp-backend
pnpm add bullmq expo-server-sdk handlebars nanoid
pnpm add -D @types/handlebars
```

- [ ] **Step 2: Add env vars to Zod schema**

Modify `src/config/env.ts`. Find the existing schema block (around line 40-80) and add these after the SMS block:

```typescript
// Notifications
FIREBASE_SERVICE_ACCOUNT_KEY:      z.string().optional(),
EXPO_ACCESS_TOKEN:                 z.string().optional(),
NOTIFICATIONS_ENABLED:             z.coerce.boolean().default(true),
NOTIFICATIONS_DEDUP_TTL_SEC:       z.coerce.number().default(60),
NOTIFICATIONS_IDEMPOTENCY_TTL_SEC: z.coerce.number().default(86400),
NOTIFICATIONS_BATCH_THRESHOLD:     z.coerce.number().default(5),
NOTIFICATIONS_BATCH_WINDOW_SEC:    z.coerce.number().default(300),
NOTIFICATIONS_MAX_QUEUE_LOW:       z.coerce.number().default(10000),
NOTIFICATIONS_MAX_QUEUE_DEFAULT:   z.coerce.number().default(50000),
NOTIFICATIONS_RECEIPT_POLL_SEC:    z.coerce.number().default(30),
NOTIFICATIONS_RECEIPT_MAX_AGE_MIN: z.coerce.number().default(15),
NOTIFICATIONS_DLQ_RETENTION_DAYS:  z.coerce.number().default(7),
```

- [ ] **Step 3: Document in .env.example**

Append to `.env.example`:

```env
# Notifications
FIREBASE_SERVICE_ACCOUNT_KEY='{"type":"service_account","project_id":"...","private_key":"..."}'
EXPO_ACCESS_TOKEN=
NOTIFICATIONS_ENABLED=true
NOTIFICATIONS_DEDUP_TTL_SEC=60
NOTIFICATIONS_IDEMPOTENCY_TTL_SEC=86400
NOTIFICATIONS_BATCH_THRESHOLD=5
NOTIFICATIONS_BATCH_WINDOW_SEC=300
NOTIFICATIONS_MAX_QUEUE_LOW=10000
NOTIFICATIONS_MAX_QUEUE_DEFAULT=50000
NOTIFICATIONS_RECEIPT_POLL_SEC=30
NOTIFICATIONS_RECEIPT_MAX_AGE_MIN=15
NOTIFICATIONS_DLQ_RETENTION_DAYS=7
```

- [ ] **Step 4: Verify env loads**

```bash
pnpm type-check
```
Expected: no errors.

- [ ] **Step 5: Commit**

```bash
git add package.json pnpm-lock.yaml src/config/env.ts .env.example
git commit -m "feat(notifications): add bullmq/expo-server-sdk/handlebars deps and env vars"
```

---

### Task 2: Prisma schema changes

**Files:**
- Modify: `avy-erp-backend/prisma/modules/platform/notifications.prisma`
- Modify: `avy-erp-backend/prisma/modules/company-admin/settings.prisma`
- Modify: `avy-erp-backend/prisma/modules/hrms/ess-workflows.prisma`

- [ ] **Step 1: Rewrite `prisma/modules/platform/notifications.prisma`**

Replace the full file with the content from spec §4.1 (Notification, UserDevice, NotificationEvent, UserNotificationPreference, 6 enums). Preserve file header comment.

- [ ] **Step 2: Add toggles to `prisma/modules/company-admin/settings.prisma`**

Find `model CompanySettings` and add after `whatsappNotifications`:

```prisma
  pushNotifications     Boolean @default(true)
  smsNotifications      Boolean @default(false)
  inAppNotifications    Boolean @default(true)
```

- [ ] **Step 3: Update `NotificationTemplate` and `NotificationRule` in ess-workflows.prisma**

Apply the changes from spec §4.3:
- Add `code`, `priority`, `version`, `variables`, `sensitiveFields`, `compiledBody`, `compiledSubject`, `isSystem` to `NotificationTemplate`.
- Add `@@unique([companyId, code, channel])`.
- Add `category`, `priority`, `version`, `isSystem` to `NotificationRule`.
- Add `@@index([companyId, triggerEvent, isActive])`.

- [ ] **Step 4: Add relation back-references to `User` and `Company`**

In `prisma/modules/platform/auth.prisma` find `model User` and add:

```prisma
  notificationPreference UserNotificationPreference? @relation("UserNotificationPrefUser")
```

Find `model Company` in the same file (or wherever it lives) and ensure the `notifications` relation already exists. `NotificationEvent` doesn't need a direct back-ref from Company (it's reached via Notification).

- [ ] **Step 5: Merge schema**

```bash
pnpm prisma:merge
```
Expected: "Merged X files into schema.prisma". No "duplicate" errors.

- [ ] **Step 6: Generate Prisma client**

```bash
pnpm db:generate
```
Expected: "Generated Prisma Client successfully".

- [ ] **Step 7: Create migration (do not apply yet)**

```bash
pnpm db:migrate --name push_notifications_overhaul
```
Answer `y` if prompted. This creates the migration SQL and applies to dev DB.

- [ ] **Step 8: Commit**

```bash
git add prisma/modules prisma/schema.prisma prisma/migrations
git commit -m "feat(notifications): prisma schema for dispatch, preferences, events, device metadata"
```

---

### Task 3: Seed defaults migration script scaffold

**Files:**
- Create: `avy-erp-backend/prisma/seeds/2026-04-09-seed-default-notification-templates.ts`

- [ ] **Step 1: Create empty scaffold**

```typescript
// prisma/seeds/2026-04-09-seed-default-notification-templates.ts
import { PrismaClient } from '@prisma/client';
import { seedDefaultTemplatesForCompany } from '../../src/core/notifications/templates/seed-defaults';

const prisma = new PrismaClient();

async function main() {
  const companies = await prisma.company.findMany({ select: { id: true, name: true } });
  console.log(`Seeding notification defaults for ${companies.length} companies...`);
  for (const c of companies) {
    try {
      const result = await seedDefaultTemplatesForCompany(c.id);
      console.log(`  ✓ ${c.name}: ${result.created} templates, ${result.rules} rules`);
    } catch (err) {
      console.error(`  ✗ ${c.name}:`, err);
    }
  }
}

main()
  .catch(console.error)
  .finally(() => prisma.$disconnect());
```

- [ ] **Step 2: Commit (even though seed-defaults.ts doesn't exist yet — it's coming in Task 11)**

```bash
git add prisma/seeds
git commit -m "feat(notifications): scaffold default-template seeder entry point"
```

---

## Phase 2: Core infrastructure

### Task 4: BullMQ connection + queues + rate limiter config

**Files:**
- Create: `avy-erp-backend/src/core/notifications/queue/connection.ts`
- Create: `avy-erp-backend/src/core/notifications/queue/queues.ts`
- Create: `avy-erp-backend/src/core/notifications/queue/rate-limiter-config.ts`

- [ ] **Step 1: `connection.ts`**

```typescript
// src/core/notifications/queue/connection.ts
import IORedis from 'ioredis';
import { env } from '../../../config/env';

const redisUrl = new URL(env.REDIS_URL);

export const bullmqConnection = new IORedis({
  host: redisUrl.hostname,
  port: parseInt(redisUrl.port, 10) || 6379,
  ...(redisUrl.username ? { username: decodeURIComponent(redisUrl.username) } : {}),
  ...(redisUrl.password ? { password: decodeURIComponent(redisUrl.password) } : {}),
  db: env.REDIS_QUEUE_DB,
  maxRetriesPerRequest: null, // required by BullMQ
  enableReadyCheck: false,
});

export const BULLMQ_PREFIX = 'bullmq';
```

- [ ] **Step 2: `queues.ts`**

```typescript
// src/core/notifications/queue/queues.ts
import { Queue, QueueEvents } from 'bullmq';
import { bullmqConnection, BULLMQ_PREFIX } from './connection';

const baseOpts = {
  connection: bullmqConnection,
  prefix: BULLMQ_PREFIX,
  defaultJobOptions: {
    attempts: 3,
    backoff: { type: 'exponential' as const, delay: 2000 },
    removeOnComplete: { age: 3600, count: 1000 },
    removeOnFail: false,
  },
};

export const notifQueueHigh    = new Queue('notifications:high',    baseOpts);
export const notifQueueDefault = new Queue('notifications:default', baseOpts);
export const notifQueueLow     = new Queue('notifications:low',     baseOpts);
export const notifQueueDLQ     = new Queue('notifications:dlq',     { ...baseOpts, defaultJobOptions: { removeOnComplete: false, removeOnFail: false } });
export const notifQueueReceipts = new Queue('notifications:receipts', baseOpts);
export const notifQueueDlqSweep = new Queue('notifications:dlq-sweep', baseOpts);

export const ALL_DELIVERY_QUEUES = [notifQueueHigh, notifQueueDefault, notifQueueLow] as const;

export function pickQueueByPriority(priority: 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL'): Queue {
  if (priority === 'CRITICAL' || priority === 'HIGH') return notifQueueHigh;
  if (priority === 'MEDIUM') return notifQueueDefault;
  return notifQueueLow;
}
```

- [ ] **Step 3: `rate-limiter-config.ts`**

```typescript
// src/core/notifications/queue/rate-limiter-config.ts
export const WORKER_LIMITER_HIGH    = { max: 50, duration: 1000 };
export const WORKER_LIMITER_DEFAULT = { max: 30, duration: 1000 };
export const WORKER_LIMITER_LOW     = { max: 10, duration: 1000 };

export const WORKER_CONCURRENCY = {
  'notifications:high':    20,
  'notifications:default': 10,
  'notifications:low':     5,
} as const;
```

- [ ] **Step 4: Commit**

```bash
git add src/core/notifications/queue
git commit -m "feat(notifications): bullmq queue, connection, rate limiter config"
```

---

### Task 5: Dedup, idempotency, backpressure helpers

**Files:**
- Create: `avy-erp-backend/src/core/notifications/dispatch/dedup.ts`
- Create: `avy-erp-backend/src/core/notifications/idempotency/worker-idempotency.ts`
- Create: `avy-erp-backend/src/core/notifications/dispatch/backpressure.ts`

- [ ] **Step 1: `dedup.ts`**

```typescript
// src/core/notifications/dispatch/dedup.ts
import crypto from 'crypto';
import { cacheRedis } from '../../../config/redis';
import { env } from '../../../config/env';
import { logger } from '../../../config/logger';

export interface DedupInput {
  companyId: string;
  triggerEvent: string;
  entityType?: string | undefined;
  entityId?: string | undefined;
  recipientId: string;
  payload: { title: string; body: string; data?: unknown };
}

export function computeDedupHash(p: DedupInput['payload']): string {
  const canonical = JSON.stringify({ t: p.title, b: p.body, d: p.data ?? null });
  return crypto.createHash('sha1').update(canonical).digest('hex');
}

export async function checkDedup(input: DedupInput): Promise<boolean> {
  try {
    const hash = computeDedupHash(input.payload);
    const key = `notif:dedup:${input.companyId}:${input.triggerEvent}:${input.entityType ?? '_'}:${input.entityId ?? '_'}:${input.recipientId}:${hash}`;
    const set = await cacheRedis.set(key, '1', 'EX', env.NOTIFICATIONS_DEDUP_TTL_SEC, 'NX');
    return set === null; // null means key already existed → duplicate
  } catch (err) {
    logger.warn('Dedup check failed, proceeding as non-duplicate (fail-open)', { error: err });
    return false;
  }
}
```

- [ ] **Step 2: `worker-idempotency.ts`**

```typescript
// src/core/notifications/idempotency/worker-idempotency.ts
import { cacheRedis } from '../../../config/redis';
import { env } from '../../../config/env';
import { logger } from '../../../config/logger';

function key(notificationId: string, channel: string) {
  return `notif:sent:${notificationId}:${channel}`;
}

export async function isAlreadySent(notificationId: string, channel: string): Promise<boolean> {
  try {
    const exists = await cacheRedis.get(key(notificationId, channel));
    return exists !== null;
  } catch (err) {
    logger.warn('Idempotency check failed, assuming not sent (fail-open)', { error: err });
    return false;
  }
}

export async function markSent(notificationId: string, channel: string): Promise<void> {
  try {
    await cacheRedis.set(
      key(notificationId, channel),
      '1',
      'EX',
      env.NOTIFICATIONS_IDEMPOTENCY_TTL_SEC,
      'NX',
    );
  } catch (err) {
    logger.warn('Idempotency mark failed (ignored)', { error: err });
  }
}
```

- [ ] **Step 3: `backpressure.ts`**

```typescript
// src/core/notifications/dispatch/backpressure.ts
import { notifQueueHigh, notifQueueDefault, notifQueueLow } from '../queue/queues';
import { env } from '../../../config/env';
import { logger } from '../../../config/logger';
import type { NotificationPriority } from '@prisma/client';

export type BackpressureDecision = 'ALLOW' | 'DROP';

export async function guardBackpressure(priority: NotificationPriority): Promise<BackpressureDecision> {
  if (priority === 'CRITICAL' || priority === 'HIGH') return 'ALLOW';

  try {
    const lowWaiting = await notifQueueLow.getWaitingCount();
    if (priority === 'LOW' && lowWaiting > env.NOTIFICATIONS_MAX_QUEUE_LOW) {
      logger.warn('Backpressure: dropping LOW (low queue over limit)', { lowWaiting });
      return 'DROP';
    }
    const defaultWaiting = await notifQueueDefault.getWaitingCount();
    if (priority === 'LOW' && defaultWaiting > env.NOTIFICATIONS_MAX_QUEUE_DEFAULT) {
      logger.warn('Backpressure: dropping LOW (default queue over limit)', { defaultWaiting });
      return 'DROP';
    }
    return 'ALLOW';
  } catch (err) {
    logger.warn('Backpressure check failed (allowing)', { error: err });
    return 'ALLOW';
  }
}
```

- [ ] **Step 4: Commit**

```bash
git add src/core/notifications/dispatch/dedup.ts src/core/notifications/idempotency src/core/notifications/dispatch/backpressure.ts
git commit -m "feat(notifications): dedup, worker idempotency, backpressure helpers"
```

---

### Task 6: Template compiler, renderer, masker

**Files:**
- Create: `avy-erp-backend/src/core/notifications/templates/compiler.ts`
- Create: `avy-erp-backend/src/core/notifications/templates/renderer.ts`
- Create: `avy-erp-backend/src/core/notifications/templates/masker.ts`

- [ ] **Step 1: `compiler.ts`**

```typescript
// src/core/notifications/templates/compiler.ts
import Handlebars from 'handlebars';

const cache = new Map<string, HandlebarsTemplateDelegate>();

export function compile(source: string): HandlebarsTemplateDelegate {
  const cached = cache.get(source);
  if (cached) return cached;
  const compiled = Handlebars.compile(source, { noEscape: true, strict: false });
  cache.set(source, compiled);
  return compiled;
}

export function validateTemplate(source: string): { valid: boolean; error?: string } {
  try {
    Handlebars.compile(source, { strict: false });
    return { valid: true };
  } catch (err: any) {
    return { valid: false, error: String(err?.message ?? err) };
  }
}

export function extractVariables(source: string): string[] {
  const re = /\{\{\s*([a-zA-Z_][a-zA-Z0-9_]*)\s*\}\}/g;
  const out = new Set<string>();
  let m;
  while ((m = re.exec(source)) !== null) out.add(m[1]);
  return Array.from(out);
}
```

- [ ] **Step 2: `renderer.ts`**

```typescript
// src/core/notifications/templates/renderer.ts
import { compile } from './compiler';
import { computeDedupHash } from '../dispatch/dedup';
import type { NotificationTemplate } from '@prisma/client';

export interface RenderedNotification {
  title: string;
  body: string;
  data: Record<string, unknown>;
  dedupHash: string;
}

export function renderTemplate(
  template: Pick<NotificationTemplate, 'name' | 'subject' | 'body' | 'variables'>,
  tokens: Record<string, unknown>,
): RenderedNotification {
  const allowlist = Array.isArray(template.variables) ? (template.variables as string[]) : [];
  const safeTokens = allowlist.length > 0
    ? Object.fromEntries(allowlist.map((k) => [k, tokens[k] ?? '']))
    : tokens;

  const title = template.subject ? compile(template.subject)(safeTokens) : template.name;
  const body = compile(template.body)(safeTokens);
  const data = { ...tokens };

  return {
    title,
    body,
    data,
    dedupHash: computeDedupHash({ title, body, data }),
  };
}
```

- [ ] **Step 3: `masker.ts`**

```typescript
// src/core/notifications/templates/masker.ts
export function maskForChannel<T extends { title: string; body: string; data?: unknown }>(
  channel: 'PUSH' | 'EMAIL' | 'SMS' | 'WHATSAPP' | 'IN_APP',
  payload: T,
  sensitiveFields: string[],
): T {
  if (channel !== 'PUSH' || sensitiveFields.length === 0) return payload;

  const maskValue = (s: string): string => {
    let out = s;
    for (const field of sensitiveFields) {
      const value = (payload.data as any)?.[field];
      if (value !== undefined && value !== null) {
        out = out.split(String(value)).join('***');
      }
    }
    return out;
  };

  const data = { ...((payload.data as object) ?? {}) } as any;
  for (const field of sensitiveFields) {
    if (data[field] !== undefined) data[field] = '***';
  }

  return { ...payload, title: maskValue(payload.title), body: maskValue(payload.body), data };
}
```

- [ ] **Step 4: Commit**

```bash
git add src/core/notifications/templates/compiler.ts src/core/notifications/templates/renderer.ts src/core/notifications/templates/masker.ts
git commit -m "feat(notifications): template compiler, renderer, sensitive field masker"
```

---

### Task 7: Socket.io user-room + emit helper

**Files:**
- Modify: `avy-erp-backend/src/lib/socket.ts`

- [ ] **Step 1: Extend socket.ts**

Find the existing `io.on('connection', ...)` block and add the user/company room join. Also add a new export:

```typescript
// Add inside existing io.on('connection', ...) after JWT auth succeeds
const userId = (socket as any).data?.userId ?? (socket as any).handshake?.auth?.userId;
const companyId = (socket as any).data?.companyId;
if (userId) socket.join(`user:${userId}`);
if (companyId) socket.join(`company:${companyId}`);

// ... existing ticket joins stay ...
```

Add at the bottom of the file:

```typescript
export function emitNotificationNew(userId: string, payload: { notificationId: string; traceId: string }) {
  const io = getSocketServer();
  if (!io) return;
  io.to(`user:${userId}`).emit('notification:new', {
    notificationId: payload.notificationId,
    unreadCountHint: null,
  });
}
```

- [ ] **Step 2: Verify JWT middleware sets `socket.data.userId` and `socket.data.companyId`**

If the existing middleware puts the decoded user on `socket.data.user`, adjust accordingly. Read the current middleware and confirm field names.

- [ ] **Step 3: Commit**

```bash
git add src/lib/socket.ts
git commit -m "feat(notifications): socket user:{id} room + emitNotificationNew helper"
```

---

### Task 8: Event emitter + socket emitter wrappers

**Files:**
- Create: `avy-erp-backend/src/core/notifications/events/event-emitter.ts`
- Create: `avy-erp-backend/src/core/notifications/events/socket-emitter.ts`

- [ ] **Step 1: `event-emitter.ts`**

```typescript
// src/core/notifications/events/event-emitter.ts
import { platformPrisma } from '../../../config/database';
import { logger } from '../../../config/logger';
import type { NotificationChannel, NotificationEventType, NotificationSource } from '@prisma/client';

export interface RecordEventInput {
  notificationId: string | null;
  channel: NotificationChannel;
  event: NotificationEventType;
  provider?: string | undefined;
  providerMessageId?: string | undefined;
  expoTicketId?: string | undefined;
  errorCode?: string | undefined;
  errorMessage?: string | undefined;
  metadata?: Record<string, unknown> | undefined;
  traceId: string;
  source?: NotificationSource | undefined;
}

export async function recordEvent(input: RecordEventInput): Promise<void> {
  try {
    if (!input.notificationId) return; // skip for null-id events (backpressure drops pre-row)

    await platformPrisma.notificationEvent.create({
      data: {
        notificationId: input.notificationId,
        channel: input.channel,
        event: input.event,
        provider: input.provider ?? null,
        providerMessageId: input.providerMessageId ?? null,
        expoTicketId: input.expoTicketId ?? null,
        errorCode: input.errorCode ?? null,
        errorMessage: input.errorMessage ?? null,
        metadata: input.metadata ?? undefined,
        traceId: input.traceId,
        source: input.source ?? 'SYSTEM',
      },
    });
  } catch (err) {
    logger.warn('Failed to record notification event', { error: err, input });
  }
}

export async function updateDeliveryStatus(
  notificationId: string,
  channel: NotificationChannel,
  status: 'PENDING' | 'SENT' | 'FAILED' | 'SKIPPED' | 'BOUNCED' | 'RETRYING',
): Promise<void> {
  try {
    const current = await platformPrisma.notification.findUnique({
      where: { id: notificationId },
      select: { deliveryStatus: true },
    });
    const ds = ((current?.deliveryStatus as any) ?? {}) as Record<string, string>;
    ds[channel.toLowerCase()] = status;
    await platformPrisma.notification.update({
      where: { id: notificationId },
      data: { deliveryStatus: ds },
    });
  } catch (err) {
    logger.warn('Failed to update deliveryStatus', { error: err, notificationId, channel, status });
  }
}
```

- [ ] **Step 2: `socket-emitter.ts`**

```typescript
// src/core/notifications/events/socket-emitter.ts
import { emitNotificationNew } from '../../../lib/socket';
import { logger } from '../../../config/logger';

export function emitSocketEvent(userId: string, payload: { notificationId: string; traceId: string }): void {
  try {
    emitNotificationNew(userId, payload);
  } catch (err) {
    logger.warn('Socket emit failed', { error: err, userId });
  }
}
```

- [ ] **Step 3: Commit**

```bash
git add src/core/notifications/events
git commit -m "feat(notifications): event recorder and socket emitter wrappers"
```

---

### Task 9: Default template catalogue

**Files:**
- Create: `avy-erp-backend/src/core/notifications/templates/defaults.ts`

- [ ] **Step 1: Catalogue data**

```typescript
// src/core/notifications/templates/defaults.ts
import type { NotificationChannel, NotificationPriority } from '@prisma/client';

export interface DefaultTemplate {
  code: string;
  name: string;
  subject?: string;
  body: string;
  channel: NotificationChannel;
  priority: NotificationPriority;
  variables: string[];
  sensitiveFields: string[];
  category: string;
  triggerEvent: string;
  recipientRole: string;
}

// All 24 templates from spec §7.1 expanded per channel.
// Each entry produces templates for its listed channels + matching rules.
export const DEFAULT_CATALOGUE: Array<Omit<DefaultTemplate, 'channel'> & { channels: NotificationChannel[] }> = [
  {
    code: 'LEAVE_APPLICATION',
    name: 'New Leave Request',
    subject: 'New Leave Request from {{employee_name}}',
    body: '{{employee_name}} requested {{leave_days}} days of leave from {{from_date}} to {{to_date}}.',
    channels: ['PUSH', 'IN_APP', 'EMAIL'],
    priority: 'MEDIUM',
    variables: ['employee_name', 'leave_days', 'from_date', 'to_date'],
    sensitiveFields: [],
    category: 'LEAVE_APPROVAL',
    triggerEvent: 'LEAVE_APPLICATION',
    recipientRole: 'APPROVER',
  },
  {
    code: 'LEAVE_APPROVED',
    name: 'Leave Approved',
    subject: 'Your leave request has been approved',
    body: 'Your leave request for {{leave_days}} days has been approved.',
    channels: ['PUSH', 'IN_APP', 'EMAIL'],
    priority: 'MEDIUM',
    variables: ['leave_days'],
    sensitiveFields: [],
    category: 'LEAVE_STATUS',
    triggerEvent: 'LEAVE_APPROVED',
    recipientRole: 'REQUESTER',
  },
  {
    code: 'LEAVE_REJECTED',
    name: 'Leave Rejected',
    subject: 'Your leave request has been rejected',
    body: 'Your leave request was rejected. Reason: {{reason}}',
    channels: ['PUSH', 'IN_APP', 'EMAIL'],
    priority: 'MEDIUM',
    variables: ['reason'],
    sensitiveFields: [],
    category: 'LEAVE_STATUS',
    triggerEvent: 'LEAVE_REJECTED',
    recipientRole: 'REQUESTER',
  },
  {
    code: 'ATTENDANCE_REGULARIZATION',
    name: 'Attendance Regularization',
    subject: 'Attendance Regularization Request',
    body: '{{employee_name}} requested attendance regularization for {{date}}.',
    channels: ['PUSH', 'IN_APP', 'EMAIL'],
    priority: 'MEDIUM',
    variables: ['employee_name', 'date'],
    sensitiveFields: [],
    category: 'ATTENDANCE_APPROVAL',
    triggerEvent: 'ATTENDANCE_REGULARIZATION',
    recipientRole: 'APPROVER',
  },
  {
    code: 'ATTENDANCE_REGULARIZED',
    name: 'Attendance Regularized',
    body: 'Your attendance regularization for {{date}} was approved.',
    channels: ['PUSH', 'IN_APP'],
    priority: 'MEDIUM',
    variables: ['date'],
    sensitiveFields: [],
    category: 'ATTENDANCE_STATUS',
    triggerEvent: 'ATTENDANCE_REGULARIZED',
    recipientRole: 'REQUESTER',
  },
  {
    code: 'OVERTIME_CLAIM',
    name: 'Overtime Claim',
    subject: 'Overtime Claim from {{employee_name}}',
    body: '{{employee_name}} submitted an overtime claim for {{hours}} hours on {{date}}.',
    channels: ['PUSH', 'IN_APP', 'EMAIL'],
    priority: 'MEDIUM',
    variables: ['employee_name', 'hours', 'date'],
    sensitiveFields: [],
    category: 'OVERTIME_APPROVAL',
    triggerEvent: 'OVERTIME_CLAIM',
    recipientRole: 'APPROVER',
  },
  {
    code: 'REIMBURSEMENT',
    name: 'Reimbursement Request',
    subject: 'Reimbursement Request',
    body: '{{employee_name}} requested reimbursement of {{amount}} for {{category}}.',
    channels: ['PUSH', 'IN_APP', 'EMAIL'],
    priority: 'MEDIUM',
    variables: ['employee_name', 'amount', 'category'],
    sensitiveFields: ['amount'],
    category: 'REIMBURSEMENT_APPROVAL',
    triggerEvent: 'REIMBURSEMENT',
    recipientRole: 'APPROVER',
  },
  {
    code: 'REIMBURSEMENT_APPROVED',
    name: 'Reimbursement Approved',
    subject: 'Reimbursement Approved',
    body: 'Your reimbursement request for {{amount}} has been approved.',
    channels: ['PUSH', 'IN_APP', 'EMAIL'],
    priority: 'MEDIUM',
    variables: ['amount'],
    sensitiveFields: ['amount'],
    category: 'REIMBURSEMENT_STATUS',
    triggerEvent: 'REIMBURSEMENT_APPROVED',
    recipientRole: 'REQUESTER',
  },
  {
    code: 'LOAN_APPLICATION',
    name: 'Loan Application',
    subject: 'Loan Application from {{employee_name}}',
    body: '{{employee_name}} applied for a loan of {{amount}}.',
    channels: ['PUSH', 'IN_APP', 'EMAIL'],
    priority: 'MEDIUM',
    variables: ['employee_name', 'amount'],
    sensitiveFields: ['amount'],
    category: 'LOAN_APPROVAL',
    triggerEvent: 'LOAN_APPLICATION',
    recipientRole: 'APPROVER',
  },
  {
    code: 'LOAN_APPROVED',
    name: 'Loan Approved',
    subject: 'Your loan has been approved',
    body: 'Your loan application for {{amount}} has been approved.',
    channels: ['PUSH', 'IN_APP', 'EMAIL'],
    priority: 'HIGH',
    variables: ['amount'],
    sensitiveFields: ['amount'],
    category: 'LOAN_STATUS',
    triggerEvent: 'LOAN_APPROVED',
    recipientRole: 'REQUESTER',
  },
  {
    code: 'WFH_REQUEST',
    name: 'Work From Home Request',
    body: '{{employee_name}} requested WFH for {{date_range}}.',
    channels: ['PUSH', 'IN_APP'],
    priority: 'MEDIUM',
    variables: ['employee_name', 'date_range'],
    sensitiveFields: [],
    category: 'WFH_APPROVAL',
    triggerEvent: 'WFH_REQUEST',
    recipientRole: 'APPROVER',
  },
  {
    code: 'SHIFT_CHANGE',
    name: 'Shift Change Request',
    body: '{{employee_name}} requested a shift change.',
    channels: ['PUSH', 'IN_APP'],
    priority: 'MEDIUM',
    variables: ['employee_name'],
    sensitiveFields: [],
    category: 'SHIFT_APPROVAL',
    triggerEvent: 'SHIFT_CHANGE',
    recipientRole: 'APPROVER',
  },
  {
    code: 'PROFILE_UPDATE',
    name: 'Profile Update Request',
    subject: 'Profile Update from {{employee_name}}',
    body: '{{employee_name}} submitted a profile update.',
    channels: ['IN_APP', 'EMAIL'],
    priority: 'LOW',
    variables: ['employee_name'],
    sensitiveFields: [],
    category: 'PROFILE',
    triggerEvent: 'PROFILE_UPDATE',
    recipientRole: 'HR',
  },
  {
    code: 'IT_DECLARATION',
    name: 'IT Declaration Submitted',
    subject: 'IT Declaration Submitted',
    body: '{{employee_name}} submitted their IT declaration for FY {{fy}}.',
    channels: ['IN_APP', 'EMAIL'],
    priority: 'MEDIUM',
    variables: ['employee_name', 'fy'],
    sensitiveFields: [],
    category: 'IT_DECLARATION',
    triggerEvent: 'IT_DECLARATION',
    recipientRole: 'HR',
  },
  {
    code: 'RESIGNATION',
    name: 'Resignation Submitted',
    subject: 'Resignation from {{employee_name}}',
    body: '{{employee_name}} has submitted a resignation. Last working day: {{last_day}}.',
    channels: ['PUSH', 'IN_APP', 'EMAIL'],
    priority: 'HIGH',
    variables: ['employee_name', 'last_day'],
    sensitiveFields: [],
    category: 'RESIGNATION',
    triggerEvent: 'RESIGNATION',
    recipientRole: 'HR',
  },
  {
    code: 'PAYROLL_APPROVAL',
    name: 'Payroll Approval Pending',
    subject: 'Payroll for {{month_year}} Awaiting Approval',
    body: 'Payroll for {{month_year}} is awaiting your approval.',
    channels: ['PUSH', 'IN_APP', 'EMAIL'],
    priority: 'HIGH',
    variables: ['month_year'],
    sensitiveFields: [],
    category: 'PAYROLL_APPROVAL',
    triggerEvent: 'PAYROLL_APPROVAL',
    recipientRole: 'APPROVER',
  },
  {
    code: 'PAYSLIP_PUBLISHED',
    name: 'Payslip Available',
    subject: 'Your payslip for {{month_year}} is now available',
    body: 'Your payslip for {{month_year}} is now available.',
    channels: ['PUSH', 'IN_APP', 'EMAIL'],
    priority: 'HIGH',
    variables: ['month_year'],
    sensitiveFields: [],
    category: 'PAYROLL',
    triggerEvent: 'PAYSLIP_PUBLISHED',
    recipientRole: 'EMPLOYEE',
  },
  {
    code: 'SALARY_CREDITED',
    name: 'Salary Credited',
    body: 'Your salary of {{amount}} for {{month_year}} has been credited.',
    channels: ['PUSH', 'IN_APP'],
    priority: 'CRITICAL',
    variables: ['amount', 'month_year'],
    sensitiveFields: ['amount'],
    category: 'PAYROLL',
    triggerEvent: 'SALARY_CREDITED',
    recipientRole: 'EMPLOYEE',
  },
  {
    code: 'INTERVIEW_SCHEDULED',
    name: 'Interview Scheduled',
    subject: 'Interview Scheduled: {{candidate_name}}',
    body: 'You are scheduled as a panelist for {{candidate_name}} on {{interview_date}}.',
    channels: ['PUSH', 'IN_APP', 'EMAIL'],
    priority: 'MEDIUM',
    variables: ['candidate_name', 'interview_date'],
    sensitiveFields: [],
    category: 'RECRUITMENT',
    triggerEvent: 'INTERVIEW_SCHEDULED',
    recipientRole: 'APPROVER',
  },
  {
    code: 'TRAINING_NOMINATION',
    name: 'Training Nomination',
    subject: 'Training Nomination: {{training_name}}',
    body: 'You have been nominated for "{{training_name}}".',
    channels: ['PUSH', 'IN_APP', 'EMAIL'],
    priority: 'MEDIUM',
    variables: ['training_name'],
    sensitiveFields: [],
    category: 'TRAINING',
    triggerEvent: 'TRAINING_NOMINATION',
    recipientRole: 'EMPLOYEE',
  },
  {
    code: 'TRAINING_COMPLETED',
    name: 'Training Completed',
    subject: 'Training Completed',
    body: 'Congratulations! You have completed "{{training_name}}".',
    channels: ['IN_APP', 'EMAIL'],
    priority: 'LOW',
    variables: ['training_name'],
    sensitiveFields: [],
    category: 'TRAINING',
    triggerEvent: 'TRAINING_COMPLETED',
    recipientRole: 'EMPLOYEE',
  },
  {
    code: 'CERTIFICATE_EXPIRING',
    name: 'Certificate Expiring',
    subject: 'Certificate Expiring Soon',
    body: 'Your "{{training_name}}" certificate expires on {{expiry_date}}.',
    channels: ['PUSH', 'IN_APP', 'EMAIL'],
    priority: 'MEDIUM',
    variables: ['training_name', 'expiry_date'],
    sensitiveFields: [],
    category: 'TRAINING',
    triggerEvent: 'CERTIFICATE_EXPIRING',
    recipientRole: 'EMPLOYEE',
  },
  {
    code: 'TICKET_MESSAGE',
    name: 'New Ticket Message',
    body: 'New message on ticket "{{ticket_subject}}"',
    channels: ['PUSH', 'IN_APP'],
    priority: 'MEDIUM',
    variables: ['ticket_subject'],
    sensitiveFields: [],
    category: 'SUPPORT',
    triggerEvent: 'TICKET_MESSAGE',
    recipientRole: 'REQUESTER',
  },
  {
    code: 'PASSWORD_RESET',
    name: 'Password Reset Code',
    subject: 'Your password reset code',
    body: 'Your password reset code is {{reset_code}}. Expires in {{expires_in}}.',
    channels: ['EMAIL', 'PUSH'],
    priority: 'CRITICAL',
    variables: ['reset_code', 'expires_in'],
    sensitiveFields: ['reset_code'],
    category: 'AUTH',
    triggerEvent: 'PASSWORD_RESET',
    recipientRole: 'REQUESTER',
  },
];
```

- [ ] **Step 2: Commit**

```bash
git add src/core/notifications/templates/defaults.ts
git commit -m "feat(notifications): default template catalogue (24 entries)"
```

---

### Task 10: Seed defaults function

**Files:**
- Create: `avy-erp-backend/src/core/notifications/templates/seed-defaults.ts`

- [ ] **Step 1: Implementation**

```typescript
// src/core/notifications/templates/seed-defaults.ts
import { platformPrisma } from '../../../config/database';
import { DEFAULT_CATALOGUE } from './defaults';
import { logger } from '../../../config/logger';

export interface SeedResult {
  created: number;
  rules: number;
  skipped: number;
}

export async function seedDefaultTemplatesForCompany(companyId: string): Promise<SeedResult> {
  let created = 0;
  let rules = 0;
  let skipped = 0;

  for (const entry of DEFAULT_CATALOGUE) {
    for (const channel of entry.channels) {
      try {
        const existing = await platformPrisma.notificationTemplate.findFirst({
          where: { companyId, code: entry.code, channel },
        });
        if (existing) {
          skipped++;
          continue;
        }

        const template = await platformPrisma.notificationTemplate.create({
          data: {
            companyId,
            code: entry.code,
            name: entry.name,
            subject: entry.subject ?? null,
            body: entry.body,
            channel,
            priority: entry.priority,
            variables: entry.variables,
            sensitiveFields: entry.sensitiveFields,
            compiledBody: entry.body,
            compiledSubject: entry.subject ?? null,
            isSystem: true,
            isActive: true,
            version: 1,
          },
        });
        created++;

        await platformPrisma.notificationRule.create({
          data: {
            companyId,
            triggerEvent: entry.triggerEvent,
            category: entry.category,
            templateId: template.id,
            recipientRole: entry.recipientRole,
            channel,
            priority: entry.priority,
            isSystem: true,
            isActive: true,
            version: 1,
          },
        });
        rules++;
      } catch (err) {
        logger.error('Failed to seed template', { error: err, code: entry.code, channel });
      }
    }
  }
  return { created, rules, skipped };
}
```

- [ ] **Step 2: Commit**

```bash
git add src/core/notifications/templates/seed-defaults.ts
git commit -m "feat(notifications): idempotent default template seeding per tenant"
```

---

### Task 11: Run seeds migration on dev

- [ ] **Step 1: Execute the seed script**

```bash
cd avy-erp-backend
pnpm tsx prisma/seeds/2026-04-09-seed-default-notification-templates.ts
```

Expected output: one line per company with created/rules/skipped counts. Re-running is idempotent (all skipped).

- [ ] **Step 2: Verify via Prisma Studio**

```bash
pnpm db:studio
```

Open `notification_templates` → confirm 24 templates per existing company (or the appropriate count per channels).

- [ ] **Step 3: Commit (no code changes — just verification, skip if nothing to commit)**

---

## Phase 3: Dispatcher pipeline

### Task 12: Rule loader

**Files:**
- Create: `avy-erp-backend/src/core/notifications/dispatch/rule-loader.ts`

- [ ] **Step 1: Implementation**

```typescript
// src/core/notifications/dispatch/rule-loader.ts
import { platformPrisma } from '../../../config/database';
import { cacheRedis } from '../../../config/redis';
import { logger } from '../../../config/logger';
import type { NotificationRule, NotificationTemplate } from '@prisma/client';

export type LoadedRule = NotificationRule & { template: NotificationTemplate };

const CACHE_TTL = 60; // seconds

export async function loadActiveRules(companyId: string, triggerEvent: string): Promise<LoadedRule[]> {
  const cacheKey = `notif:rules:${companyId}:${triggerEvent}`;
  try {
    const cached = await cacheRedis.get(cacheKey);
    if (cached) return JSON.parse(cached) as LoadedRule[];
  } catch (err) {
    logger.warn('Rule cache read failed', { error: err });
  }

  const rules = await platformPrisma.notificationRule.findMany({
    where: { companyId, triggerEvent, isActive: true },
    include: { template: true },
  });

  try {
    await cacheRedis.set(cacheKey, JSON.stringify(rules), 'EX', CACHE_TTL);
  } catch (err) {
    logger.warn('Rule cache write failed', { error: err });
  }
  return rules as LoadedRule[];
}

export async function invalidateRuleCache(companyId: string, triggerEvent?: string): Promise<void> {
  try {
    if (triggerEvent) {
      await cacheRedis.del(`notif:rules:${companyId}:${triggerEvent}`);
    } else {
      const keys = await cacheRedis.keys(`notif:rules:${companyId}:*`);
      if (keys.length) await cacheRedis.del(...keys);
    }
  } catch (err) {
    logger.warn('Rule cache invalidation failed', { error: err });
  }
}
```

- [ ] **Step 2: Commit**

```bash
git add src/core/notifications/dispatch/rule-loader.ts
git commit -m "feat(notifications): rule loader with Redis cache"
```

---

### Task 13: Recipient resolver

**Files:**
- Create: `avy-erp-backend/src/core/notifications/dispatch/recipient-resolver.ts`

- [ ] **Step 1: Implementation**

```typescript
// src/core/notifications/dispatch/recipient-resolver.ts
import { platformPrisma } from '../../../config/database';
import { logger } from '../../../config/logger';

export interface RecipientContext {
  companyId: string;
  requesterId?: string | undefined;
  approverIds?: string[] | undefined;
  managerId?: string | undefined;
  departmentId?: string | undefined;
}

export async function resolveRecipients(role: string, ctx: RecipientContext): Promise<string[]> {
  switch (role.toUpperCase()) {
    case 'REQUESTER':
    case 'EMPLOYEE':
      return ctx.requesterId ? [ctx.requesterId] : [];

    case 'APPROVER':
      return ctx.approverIds ?? [];

    case 'MANAGER': {
      if (ctx.managerId) return [ctx.managerId];
      if (!ctx.requesterId) return [];
      try {
        const emp = await platformPrisma.employee.findFirst({
          where: { userId: ctx.requesterId },
          select: { reportingManagerId: true },
        });
        if (emp?.reportingManagerId) {
          const mgr = await platformPrisma.employee.findUnique({
            where: { id: emp.reportingManagerId },
            select: { userId: true },
          });
          return mgr?.userId ? [mgr.userId] : [];
        }
      } catch (err) {
        logger.warn('Failed to resolve manager', { error: err, ctx });
      }
      return [];
    }

    case 'HR':
      return findUsersByRoleName(ctx.companyId, ['HR_PERSONNEL', 'HR_MANAGER', 'HR']);
    case 'FINANCE':
      return findUsersByRoleName(ctx.companyId, ['FINANCE_PERSONNEL', 'FINANCE_MANAGER', 'FINANCE']);
    case 'IT':
      return findUsersByRoleName(ctx.companyId, ['IT_PERSONNEL', 'IT_MANAGER', 'IT']);
    case 'ADMIN':
      return findUsersByRoleName(ctx.companyId, ['COMPANY_ADMIN', 'company-admin']);

    case 'ALL': {
      const users = await platformPrisma.user.findMany({
        where: { companyId: ctx.companyId, isActive: true },
        select: { id: true },
      });
      return users.map((u) => u.id);
    }

    default:
      logger.warn('Unknown recipient role', { role });
      return [];
  }
}

async function findUsersByRoleName(companyId: string, roleNames: string[]): Promise<string[]> {
  try {
    const users = await platformPrisma.user.findMany({
      where: {
        companyId,
        isActive: true,
        OR: [
          { role: { in: roleNames } },
          { userRoles: { some: { role: { name: { in: roleNames } } } } },
        ],
      },
      select: { id: true },
    });
    return users.map((u) => u.id);
  } catch (err) {
    logger.warn('Failed to resolve users by role', { error: err, roleNames });
    return [];
  }
}
```

**Note:** Adjust the query structure based on the actual User/Role relation. If the existing schema uses `user.role: String` only, the `userRoles` include won't exist — simplify to just the string match.

- [ ] **Step 2: Commit**

```bash
git add src/core/notifications/dispatch/recipient-resolver.ts
git commit -m "feat(notifications): recipient resolver for role-based delivery"
```

---

### Task 14: Consent gate

**Files:**
- Create: `avy-erp-backend/src/core/notifications/dispatch/consent-gate.ts`

- [ ] **Step 1: Implementation**

```typescript
// src/core/notifications/dispatch/consent-gate.ts
import { DateTime } from 'luxon';
import { platformPrisma } from '../../../config/database';
import { logger } from '../../../config/logger';
import type { NotificationChannel, NotificationPriority } from '@prisma/client';

export interface ConsentInput {
  userId: string;
  channel: NotificationChannel;
  priority: NotificationPriority;
  systemCritical?: boolean;
}

export interface ConsentResult {
  allowed: boolean;
  reason?: string;
}

export async function checkConsent(input: ConsentInput): Promise<ConsentResult> {
  const { userId, channel, priority, systemCritical } = input;

  if (channel === 'IN_APP') return { allowed: true };

  try {
    const user = await platformPrisma.user.findUnique({
      where: { id: userId },
      select: { companyId: true },
    });
    if (!user?.companyId) return { allowed: false, reason: 'NO_COMPANY' };

    const settings = await platformPrisma.companySettings.findFirst({
      where: { companyId: user.companyId },
    });
    if (!settings) return { allowed: false, reason: 'NO_COMPANY_SETTINGS' };

    const masterField = {
      PUSH: 'pushNotifications',
      EMAIL: 'emailNotifications',
      SMS: 'smsNotifications',
      WHATSAPP: 'whatsappNotifications',
      IN_APP: 'inAppNotifications',
    }[channel] as keyof typeof settings;
    if (!settings[masterField]) return { allowed: false, reason: 'COMPANY_MASTER_OFF' };

    // SYSTEM_CRITICAL bypasses user pref + quiet hours (still respects company master)
    if (systemCritical || priority === 'CRITICAL') return { allowed: true };

    const pref = await platformPrisma.userNotificationPreference.findUnique({
      where: { userId },
    });
    if (pref) {
      const userField = {
        PUSH: 'pushEnabled',
        EMAIL: 'emailEnabled',
        SMS: 'smsEnabled',
        WHATSAPP: 'whatsappEnabled',
        IN_APP: 'inAppEnabled',
      }[channel] as keyof typeof pref;
      if (!pref[userField]) return { allowed: false, reason: 'USER_PREF_OFF' };

      if (pref.quietHoursEnabled && pref.quietHoursStart && pref.quietHoursEnd) {
        const tz = (settings as any).timezone ?? 'UTC';
        const now = DateTime.now().setZone(tz);
        if (isInQuietHours(now, pref.quietHoursStart, pref.quietHoursEnd)) {
          if (priority === 'LOW' || priority === 'MEDIUM') {
            return { allowed: false, reason: 'QUIET_HOURS' };
          }
        }
      }
    }

    return { allowed: true };
  } catch (err) {
    logger.error('Consent check failed', { error: err, input });
    return { allowed: false, reason: 'CONSENT_CHECK_ERROR' };
  }
}

function isInQuietHours(now: DateTime, startStr: string, endStr: string): boolean {
  const [sH, sM] = startStr.split(':').map(Number);
  const [eH, eM] = endStr.split(':').map(Number);
  const currentMin = now.hour * 60 + now.minute;
  const startMin = sH * 60 + sM;
  const endMin = eH * 60 + eM;
  if (startMin <= endMin) return currentMin >= startMin && currentMin < endMin;
  // Overnight range (e.g., 22:00 → 07:00)
  return currentMin >= startMin || currentMin < endMin;
}
```

- [ ] **Step 2: Commit**

```bash
git add src/core/notifications/dispatch/consent-gate.ts
git commit -m "feat(notifications): consent gate with two-tier + quiet hours + critical override"
```

---

### Task 15: Dispatcher types + dispatcher

**Files:**
- Create: `avy-erp-backend/src/core/notifications/dispatch/types.ts`
- Create: `avy-erp-backend/src/core/notifications/dispatch/dispatcher.ts`
- Create: `avy-erp-backend/src/core/notifications/dispatch/enqueue.ts`

- [ ] **Step 1: `types.ts`**

```typescript
// src/core/notifications/dispatch/types.ts
import type { NotificationChannel, NotificationPriority } from '@prisma/client';

export interface DispatchInput {
  companyId: string;
  triggerEvent: string;
  traceId?: string;

  entityType?: string;
  entityId?: string;

  tokens?: Record<string, unknown>;

  explicitRecipients?: string[];
  recipientContext?: {
    requesterId?: string;
    approverIds?: string[];
    managerId?: string;
    departmentId?: string;
  };

  priority?: NotificationPriority;
  systemCritical?: boolean;
  actionUrl?: string;

  adHoc?: {
    title: string;
    body: string;
    channels: NotificationChannel[];
    priority?: NotificationPriority;
  };

  type?: string;
}

export interface DispatchResult {
  traceId: string;
  enqueued: number;
  notificationIds: string[];
  error?: string;
}

export interface QueueablePayload {
  notificationId: string;
  userId: string;
  channels: NotificationChannel[];
  priority: NotificationPriority;
  traceId: string;
  category?: string | null;
  entityType?: string | null;
  systemCritical: boolean;
}
```

- [ ] **Step 2: `enqueue.ts`** (includes batching logic)

```typescript
// src/core/notifications/dispatch/enqueue.ts
import { cacheRedis } from '../../../config/redis';
import { env } from '../../../config/env';
import { logger } from '../../../config/logger';
import { pickQueueByPriority } from '../queue/queues';
import type { QueueablePayload } from './types';

export async function enqueueWithBatching(payload: QueueablePayload): Promise<void> {
  const queue = pickQueueByPriority(payload.priority);

  const canBatch =
    (payload.priority === 'LOW' || payload.priority === 'MEDIUM') &&
    payload.category &&
    payload.entityType;

  if (canBatch) {
    const batchKey = `notif:batch:${payload.userId}:${payload.category}:${payload.entityType}`;
    const windowMs = env.NOTIFICATIONS_BATCH_WINDOW_SEC * 1000;
    const now = Date.now();
    try {
      await cacheRedis.zremrangebyscore(batchKey, 0, now - windowMs);
      const pending = await cacheRedis.zcard(batchKey);
      await cacheRedis.zadd(batchKey, now, payload.notificationId);
      await cacheRedis.expire(batchKey, env.NOTIFICATIONS_BATCH_WINDOW_SEC);

      if (pending >= env.NOTIFICATIONS_BATCH_THRESHOLD) {
        const holdMs = Math.min(60_000, (pending + 1) * 5_000);
        await queue.add('deliver', payload, { delay: holdMs });
        logger.info('Enqueued with batching delay', { notificationId: payload.notificationId, holdMs, pending });
        return;
      }
    } catch (err) {
      logger.warn('Batching calc failed, enqueuing immediately', { error: err });
    }
  }

  await queue.add('deliver', payload);
}
```

- [ ] **Step 3: `dispatcher.ts`**

```typescript
// src/core/notifications/dispatch/dispatcher.ts
import { nanoid } from 'nanoid';
import { platformPrisma } from '../../../config/database';
import { logger } from '../../../config/logger';
import { env } from '../../../config/env';
import { loadActiveRules } from './rule-loader';
import { resolveRecipients } from './recipient-resolver';
import { checkDedup } from './dedup';
import { guardBackpressure } from './backpressure';
import { enqueueWithBatching } from './enqueue';
import { renderTemplate } from '../templates/renderer';
import { recordEvent } from '../events/event-emitter';
import { emitSocketEvent } from '../events/socket-emitter';
import type { DispatchInput, DispatchResult, QueueablePayload } from './types';
import type { LoadedRule } from './rule-loader';
import type { NotificationChannel, NotificationPriority, NotificationTemplate } from '@prisma/client';

function buildAdHocRule(input: DispatchInput): LoadedRule[] {
  if (!input.adHoc) return [];
  return input.adHoc.channels.map((channel) => ({
    id: `adhoc:${input.triggerEvent}:${channel}`,
    triggerEvent: input.triggerEvent,
    category: null,
    templateId: 'adhoc',
    recipientRole: 'EMPLOYEE',
    channel,
    priority: input.adHoc!.priority ?? input.priority ?? 'MEDIUM',
    version: 1,
    isSystem: false,
    isActive: true,
    companyId: input.companyId,
    createdAt: new Date(),
    updatedAt: new Date(),
    template: {
      id: 'adhoc',
      name: input.adHoc!.title,
      code: 'ADHOC',
      subject: input.adHoc!.title,
      body: input.adHoc!.body,
      channel,
      priority: input.adHoc!.priority ?? input.priority ?? 'MEDIUM',
      version: 1,
      variables: [],
      sensitiveFields: [],
      compiledBody: input.adHoc!.body,
      compiledSubject: input.adHoc!.title,
      isSystem: false,
      isActive: true,
      companyId: input.companyId,
      createdAt: new Date(),
      updatedAt: new Date(),
    } as NotificationTemplate,
  } as unknown as LoadedRule));
}

function buildFallbackRule(input: DispatchInput): LoadedRule[] {
  const title = input.type ?? input.triggerEvent.replace(/_/g, ' ');
  const body = `Event: ${input.triggerEvent}`;
  return buildAdHocRule({
    ...input,
    adHoc: { title, body, channels: ['IN_APP'], priority: 'LOW' },
  });
}

export async function dispatch(input: DispatchInput): Promise<DispatchResult> {
  const traceId = input.traceId ?? nanoid(12);

  if (!env.NOTIFICATIONS_ENABLED) {
    logger.info('NOTIFICATIONS_ENABLED=false — skipping dispatch', { traceId, trigger: input.triggerEvent });
    return { traceId, enqueued: 0, notificationIds: [] };
  }

  try {
    let rules: LoadedRule[] = [];
    if (input.adHoc) {
      rules = buildAdHocRule(input);
    } else {
      rules = await loadActiveRules(input.companyId, input.triggerEvent);
      if (rules.length === 0) {
        logger.warn('No rules found, using fallback IN_APP rule', { traceId, trigger: input.triggerEvent });
        rules = buildFallbackRule(input);
      }
    }

    const toEnqueue: QueueablePayload[] = [];
    const createdNotificationIds: string[] = [];
    const recipientCache = new Map<string, string[]>();

    for (const rule of rules) {
      const recipients = input.explicitRecipients?.length
        ? input.explicitRecipients
        : (recipientCache.get(rule.recipientRole)
            ?? (await resolveRecipients(rule.recipientRole, {
              companyId: input.companyId,
              requesterId: input.recipientContext?.requesterId,
              approverIds: input.recipientContext?.approverIds,
              managerId: input.recipientContext?.managerId,
              departmentId: input.recipientContext?.departmentId,
            })));
      if (!input.explicitRecipients?.length) {
        recipientCache.set(rule.recipientRole, recipients);
      }
      if (recipients.length === 0) continue;

      const rendered = renderTemplate(rule.template, input.tokens ?? {});

      // Dedup
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

      const priority: NotificationPriority =
        input.priority ?? rule.priority ?? rule.template.priority ?? 'MEDIUM';

      const guard = await guardBackpressure(priority);
      if (guard === 'DROP') {
        logger.warn('Dispatcher dropped due to backpressure', { traceId, trigger: input.triggerEvent });
        continue;
      }

      // Write Notification rows — in-app row is the system of record
      const channelForRule = rule.channel;
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
          data: rendered.data as any,
          actionUrl: input.actionUrl ?? null,
          priority,
          status: 'UNREAD',
          isRead: false,
          deliveryStatus: {
            inApp: 'SENT',
            [channelForRule.toLowerCase()]: channelForRule === 'IN_APP' ? 'SENT' : 'PENDING',
          },
          traceId,
          ruleId: rule.id?.startsWith('adhoc:') ? null : rule.id,
          ruleVersion: rule.version ?? null,
          templateId: rule.template.id === 'adhoc' ? null : rule.template.id,
          templateVersion: rule.template.version ?? null,
          dedupHash: rendered.dedupHash,
        })),
      });

      for (const row of rows) {
        createdNotificationIds.push(row.id);
        emitSocketEvent(row.userId, { notificationId: row.id, traceId });

        if (channelForRule !== 'IN_APP') {
          toEnqueue.push({
            notificationId: row.id,
            userId: row.userId,
            channels: [channelForRule],
            priority,
            traceId,
            category: rule.category ?? null,
            entityType: input.entityType ?? null,
            systemCritical: input.systemCritical === true || priority === 'CRITICAL',
          });
        }
      }
    }

    for (const payload of toEnqueue) {
      await enqueueWithBatching(payload);
      for (const channel of payload.channels) {
        await recordEvent({
          notificationId: payload.notificationId,
          channel,
          event: 'ENQUEUED',
          traceId,
          source: 'SYSTEM',
        });
      }
    }

    return { traceId, enqueued: toEnqueue.length, notificationIds: createdNotificationIds };
  } catch (err) {
    logger.error('Dispatcher internal error', { error: err, traceId, trigger: input.triggerEvent });
    return { traceId, enqueued: 0, notificationIds: [], error: String(err) };
  }
}
```

- [ ] **Step 4: Commit**

```bash
git add src/core/notifications/dispatch/types.ts src/core/notifications/dispatch/enqueue.ts src/core/notifications/dispatch/dispatcher.ts
git commit -m "feat(notifications): dispatcher core — sync entry, batching, socket emit"
```

---

## Phase 4: Workers

### Task 16: Notification worker rewrite (3 priority queues)

**Files:**
- Modify (full rewrite): `avy-erp-backend/src/workers/notification.worker.ts`

- [ ] **Step 1: Full rewrite**

See spec §5.4. Read current file first (`avy-erp-backend/src/workers/notification.worker.ts`) and replace contents with:

```typescript
// src/workers/notification.worker.ts
import 'dotenv/config';
import { Worker, Job, QueueEvents } from 'bullmq';
import { bullmqConnection, BULLMQ_PREFIX } from '../core/notifications/queue/connection';
import { notifQueueDLQ, ALL_DELIVERY_QUEUES } from '../core/notifications/queue/queues';
import { WORKER_CONCURRENCY, WORKER_LIMITER_HIGH, WORKER_LIMITER_DEFAULT, WORKER_LIMITER_LOW } from '../core/notifications/queue/rate-limiter-config';
import { channelRouter } from '../core/notifications/channels/channel-router';
import { isAlreadySent, markSent } from '../core/notifications/idempotency/worker-idempotency';
import { checkConsent } from '../core/notifications/dispatch/consent-gate';
import { recordEvent, updateDeliveryStatus } from '../core/notifications/events/event-emitter';
import { logger } from '../config/logger';

const LIMITERS = {
  'notifications:high':    WORKER_LIMITER_HIGH,
  'notifications:default': WORKER_LIMITER_DEFAULT,
  'notifications:low':     WORKER_LIMITER_LOW,
} as const;

function makeWorker(queueName: keyof typeof WORKER_CONCURRENCY) {
  const worker = new Worker(
    queueName,
    async (job: Job) => {
      const { notificationId, userId, channels, traceId, priority, systemCritical } = job.data;
      logger.info('Processing notification delivery', { jobId: job.id, notificationId, channels, traceId });

      for (const channel of channels) {
        if (await isAlreadySent(notificationId, channel)) {
          logger.info('Skip — already sent (idempotency)', { notificationId, channel, traceId });
          continue;
        }

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
          const result = await channelRouter.send({ notificationId, userId, channel, traceId, priority });
          await markSent(notificationId, channel);
          await updateDeliveryStatus(notificationId, channel, 'SENT');
          await recordEvent({
            notificationId, channel, event: 'SENT',
            provider: result.provider, providerMessageId: result.messageId ?? undefined,
            expoTicketId: result.expoTicketId ?? undefined, traceId,
            source: job.attemptsMade > 0 ? 'RETRY' : 'SYSTEM',
          });
        } catch (err: any) {
          await updateDeliveryStatus(notificationId, channel, 'FAILED');
          await recordEvent({
            notificationId, channel, event: 'FAILED',
            errorCode: err?.code ?? 'UNKNOWN', errorMessage: err?.message ?? String(err),
            traceId, source: job.attemptsMade > 0 ? 'RETRY' : 'SYSTEM',
          });
          throw err; // trigger BullMQ retry
        }
      }
    },
    {
      connection: bullmqConnection,
      prefix: BULLMQ_PREFIX,
      concurrency: WORKER_CONCURRENCY[queueName],
      limiter: LIMITERS[queueName],
    },
  );

  worker.on('completed', (job) => logger.info('Job completed', { id: job.id, queue: queueName }));
  worker.on('failed', async (job, err) => {
    logger.warn('Job failed', { id: job?.id, queue: queueName, attempt: job?.attemptsMade, err: err.message });
    if (job && job.attemptsMade >= (job.opts.attempts ?? 3)) {
      await notifQueueDLQ.add('dead-letter', { originalQueue: queueName, jobId: job.id, data: job.data, error: err.message });
    }
  });
  return worker;
}

const workers = [
  makeWorker('notifications:high'),
  makeWorker('notifications:default'),
  makeWorker('notifications:low'),
];

process.on('SIGTERM', async () => {
  logger.info('Notification worker shutting down...');
  await Promise.all(workers.map((w) => w.close()));
  process.exit(0);
});

process.on('SIGINT', async () => {
  logger.info('Notification worker interrupted...');
  await Promise.all(workers.map((w) => w.close()));
  process.exit(0);
});

logger.info('Notification workers started (3 priority queues)');

export { workers };
```

- [ ] **Step 2: Commit**

```bash
git add src/workers/notification.worker.ts
git commit -m "feat(notifications): rewrite worker with 3 priority queues, idempotency, DLQ"
```

---

### Task 17: Receipt poller worker

**Files:**
- Create: `avy-erp-backend/src/core/notifications/workers/receipt-poller.worker.ts`

- [ ] **Step 1: Implementation**

```typescript
// src/core/notifications/workers/receipt-poller.worker.ts
import { Worker } from 'bullmq';
import { Expo } from 'expo-server-sdk';
import { bullmqConnection, BULLMQ_PREFIX } from '../queue/connection';
import { notifQueueReceipts } from '../queue/queues';
import { platformPrisma } from '../../../config/database';
import { recordEvent } from '../events/event-emitter';
import { env } from '../../../config/env';
import { logger } from '../../../config/logger';

export async function ensureReceiptPollerScheduled() {
  await notifQueueReceipts.add(
    'poll-receipts',
    {},
    {
      repeat: { every: env.NOTIFICATIONS_RECEIPT_POLL_SEC * 1000 },
      jobId: 'receipt-poller-singleton',
    },
  );
}

const expo = new Expo({ accessToken: env.EXPO_ACCESS_TOKEN, useFcmV1: true });

export function startReceiptPollerWorker() {
  return new Worker(
    'notifications:receipts',
    async () => {
      const maxAgeMs = env.NOTIFICATIONS_RECEIPT_MAX_AGE_MIN * 60 * 1000;
      const cutoff = new Date(Date.now() - maxAgeMs);

      const pending = await platformPrisma.notificationEvent.findMany({
        where: {
          provider: 'expo',
          expoTicketId: { not: null },
          receiptCheckedAt: null,
          occurredAt: { gte: cutoff },
          event: 'SENT',
        },
        take: 500,
      });
      if (pending.length === 0) return;

      const ticketIds = pending.map((p) => p.expoTicketId!).filter(Boolean);
      const chunks = expo.chunkPushNotificationReceiptIds(ticketIds);

      for (const chunk of chunks) {
        try {
          const receipts = await expo.getPushNotificationReceiptsAsync(chunk);
          for (const [ticketId, receipt] of Object.entries(receipts)) {
            const event = pending.find((p) => p.expoTicketId === ticketId);
            if (!event) continue;

            await platformPrisma.notificationEvent.update({
              where: { id: event.id },
              data: {
                receiptCheckedAt: new Date(),
                receiptStatus: receipt.status,
                errorCode: receipt.status === 'error' ? (receipt as any).details?.error : null,
                errorMessage: receipt.status === 'error' ? (receipt as any).message : null,
              },
            });

            if (receipt.status === 'ok') {
              await recordEvent({
                notificationId: event.notificationId,
                channel: 'PUSH',
                event: 'DELIVERED',
                provider: 'expo',
                expoTicketId: ticketId,
                traceId: event.traceId,
                source: 'SYSTEM',
              });
            } else {
              const errCode = (receipt as any).details?.error;
              const eventType = errCode === 'DeviceNotRegistered' ? 'BOUNCED' : 'FAILED';
              await recordEvent({
                notificationId: event.notificationId,
                channel: 'PUSH',
                event: eventType,
                provider: 'expo',
                expoTicketId: ticketId,
                errorCode: errCode,
                errorMessage: (receipt as any).message,
                traceId: event.traceId,
                source: 'SYSTEM',
              });
            }
          }
        } catch (err) {
          logger.error('Receipt polling chunk failed', { error: err });
        }
      }

      // Mark stale (>15 min) as unknown
      await platformPrisma.notificationEvent.updateMany({
        where: {
          provider: 'expo',
          expoTicketId: { not: null },
          receiptCheckedAt: null,
          occurredAt: { lt: cutoff },
        },
        data: { receiptCheckedAt: new Date(), receiptStatus: 'unknown' },
      });
    },
    { connection: bullmqConnection, prefix: BULLMQ_PREFIX, concurrency: 1 },
  );
}
```

- [ ] **Step 2: Commit**

```bash
git add src/core/notifications/workers/receipt-poller.worker.ts
git commit -m "feat(notifications): Expo receipt poller (30s cadence, 15min window)"
```

---

### Task 18: DLQ sweeper + batcher workers

**Files:**
- Create: `avy-erp-backend/src/core/notifications/workers/dlq-sweeper.worker.ts`
- Create: `avy-erp-backend/src/core/notifications/workers/batcher.worker.ts`

- [ ] **Step 1: `dlq-sweeper.worker.ts`**

```typescript
// src/core/notifications/workers/dlq-sweeper.worker.ts
import { Worker } from 'bullmq';
import { bullmqConnection, BULLMQ_PREFIX } from '../queue/connection';
import { notifQueueDLQ, notifQueueDlqSweep } from '../queue/queues';
import { env } from '../../../config/env';
import { logger } from '../../../config/logger';

export async function ensureDlqSweeperScheduled() {
  await notifQueueDlqSweep.add(
    'sweep',
    {},
    {
      repeat: { every: 60 * 60 * 1000 }, // hourly
      jobId: 'dlq-sweeper-singleton',
    },
  );
}

export function startDlqSweeperWorker() {
  return new Worker(
    'notifications:dlq-sweep',
    async () => {
      const retentionMs = env.NOTIFICATIONS_DLQ_RETENTION_DAYS * 24 * 60 * 60 * 1000;
      try {
        const removed = await notifQueueDLQ.clean(retentionMs, 1000, 'completed');
        const failedRemoved = await notifQueueDLQ.clean(retentionMs, 1000, 'failed');
        logger.info('DLQ sweep complete', {
          removedCompleted: removed.length,
          removedFailed: failedRemoved.length,
        });
      } catch (err) {
        logger.error('DLQ sweep failed', { error: err });
      }
    },
    { connection: bullmqConnection, prefix: BULLMQ_PREFIX, concurrency: 1 },
  );
}
```

- [ ] **Step 2: `batcher.worker.ts`** (flush coalescer — currently the batching delay is handled by BullMQ `delay`; a separate flush worker is not required for v1. We add a stub for future use.)

```typescript
// src/core/notifications/workers/batcher.worker.ts
// Placeholder: in v1, batching is delay-based (BullMQ `delay` option in enqueue.ts).
// A future v2 can add a dedicated flush worker that coalesces multiple pending
// notifications into a single summary push. For now, this file exports nothing
// runtime, just a type for the future flush payload.

export interface BatchFlushPayload {
  userId: string;
  category: string;
  entityType: string;
}
```

- [ ] **Step 3: Commit**

```bash
git add src/core/notifications/workers
git commit -m "feat(notifications): DLQ sweeper + batcher scaffold"
```

---

### Task 19: Wire all workers into server startup

**Files:**
- Modify: `avy-erp-backend/src/app/server.ts`

- [ ] **Step 1: Add worker startup after existing `initFirebase()` call**

Find the `initFirebase()` call (around line 54) and add after it:

```typescript
// Start notification workers + schedule repeatable jobs
if (env.NOTIFICATIONS_ENABLED) {
  try {
    const { ensureReceiptPollerScheduled, startReceiptPollerWorker } = await import('../core/notifications/workers/receipt-poller.worker');
    const { ensureDlqSweeperScheduled, startDlqSweeperWorker } = await import('../core/notifications/workers/dlq-sweeper.worker');
    await ensureReceiptPollerScheduled();
    await ensureDlqSweeperScheduled();
    startReceiptPollerWorker();
    startDlqSweeperWorker();
    // Main notification.worker.ts is started as a separate process via `pnpm worker:notifications`
    logger.info('Notification receipt poller + DLQ sweeper started');
  } catch (err) {
    logger.error('Failed to start notification workers', { error: err });
  }
}
```

**Note:** The main notification worker runs as a separate Node process (existing pattern — check `package.json` scripts for `worker:notifications` or similar). The receipt poller and DLQ sweeper run in-process because they are lightweight.

- [ ] **Step 2: Ensure `package.json` has a script to start the notification worker**

Verify:
```json
"scripts": {
  "worker:notifications": "ts-node-dev src/workers/notification.worker.ts"
}
```
Add if missing.

- [ ] **Step 3: Commit**

```bash
git add src/app/server.ts package.json
git commit -m "feat(notifications): wire receipt poller + dlq sweeper into server startup"
```

---

## Phase 5: Channels

### Task 20: Channel router + in-app channel

**Files:**
- Create: `avy-erp-backend/src/core/notifications/channels/channel-router.ts`
- Create: `avy-erp-backend/src/core/notifications/channels/in-app.channel.ts`

- [ ] **Step 1: `channel-router.ts`**

```typescript
// src/core/notifications/channels/channel-router.ts
import type { NotificationChannel, NotificationPriority } from '@prisma/client';
import { inAppChannel } from './in-app.channel';
import { pushChannel } from './push/push.channel';
import { emailChannel } from './email.channel';
import { smsChannel } from './sms.channel';
import { whatsappChannel } from './whatsapp.channel';

export interface ChannelSendArgs {
  notificationId: string;
  userId: string;
  channel: NotificationChannel;
  traceId: string;
  priority: NotificationPriority;
}

export interface ChannelSendResult {
  provider: string;
  messageId?: string | null;
  expoTicketId?: string | null;
  deadTokens?: string[];
}

export const channelRouter = {
  async send(args: ChannelSendArgs): Promise<ChannelSendResult> {
    switch (args.channel) {
      case 'IN_APP':   return inAppChannel.send(args);
      case 'PUSH':     return pushChannel.send(args);
      case 'EMAIL':    return emailChannel.send(args);
      case 'SMS':      return smsChannel.send(args);
      case 'WHATSAPP': return whatsappChannel.send(args);
      default:
        throw Object.assign(new Error(`Unknown channel: ${args.channel}`), { code: 'UNKNOWN_CHANNEL' });
    }
  },
};
```

- [ ] **Step 2: `in-app.channel.ts`**

```typescript
// src/core/notifications/channels/in-app.channel.ts
import type { ChannelSendArgs, ChannelSendResult } from './channel-router';

export const inAppChannel = {
  async send(_args: ChannelSendArgs): Promise<ChannelSendResult> {
    // In-app is written by the dispatcher before the worker runs.
    // Worker-side IN_APP is a no-op; we just confirm status.
    return { provider: 'in-app', messageId: null };
  },
};
```

- [ ] **Step 3: Commit**

```bash
git add src/core/notifications/channels/channel-router.ts src/core/notifications/channels/in-app.channel.ts
git commit -m "feat(notifications): channel router + in-app no-op channel"
```

---

### Task 21: Expo provider

**Files:**
- Create: `avy-erp-backend/src/core/notifications/channels/push/expo.provider.ts`

- [ ] **Step 1: Implementation** (see spec §5.5 reference — finalized below)

```typescript
// src/core/notifications/channels/push/expo.provider.ts
import { Expo, ExpoPushMessage, ExpoPushTicket } from 'expo-server-sdk';
import { env } from '../../../../config/env';
import { logger } from '../../../../config/logger';
import type { NotificationPriority, UserDevice } from '@prisma/client';

const expo = new Expo({ accessToken: env.EXPO_ACCESS_TOKEN, useFcmV1: true });

export interface ExpoSendPayload {
  title: string;
  body: string;
  data: Record<string, unknown>;
  priority: NotificationPriority;
}

export interface ExpoSendResult {
  provider: 'expo';
  messageId: string | null;
  expoTicketId: string | null;
  deadTokens: string[];
  tickets: Array<{ deviceId: string; ticketId: string | null; status: 'ok' | 'error' }>;
}

export const expoProvider = {
  async send(devices: UserDevice[], payload: ExpoSendPayload, traceId: string): Promise<ExpoSendResult> {
    const validDevices = devices.filter((d) => Expo.isExpoPushToken(d.fcmToken));
    if (validDevices.length === 0) {
      throw Object.assign(new Error('NO_VALID_EXPO_TOKENS'), { code: 'NO_VALID_EXPO_TOKENS' });
    }

    const messages: ExpoPushMessage[] = validDevices.map((d) => ({
      to: d.fcmToken,
      title: payload.title,
      body: payload.body,
      data: { ...payload.data, traceId },
      priority: payload.priority === 'CRITICAL' || payload.priority === 'HIGH' ? 'high' : 'default',
      sound: 'default',
      channelId: payload.priority === 'CRITICAL' ? 'critical' : 'default',
      badge: 1,
    }));

    const chunks = expo.chunkPushNotifications(messages);
    const allTickets: Array<{ device: UserDevice; ticket: ExpoPushTicket }> = [];

    let offset = 0;
    for (const chunk of chunks) {
      try {
        const tickets = await expo.sendPushNotificationsAsync(chunk);
        const chunkDevices = validDevices.slice(offset, offset + chunk.length);
        for (let i = 0; i < tickets.length; i++) {
          allTickets.push({ device: chunkDevices[i], ticket: tickets[i] });
        }
        offset += chunk.length;
      } catch (err) {
        logger.error('Expo sendPushNotificationsAsync failed for chunk', { error: err });
        throw err;
      }
    }

    const deadTokens = allTickets
      .filter((t) => t.ticket?.status === 'error' && (t.ticket as any).details?.error === 'DeviceNotRegistered')
      .map((t) => t.device.fcmToken);

    const okTicket = allTickets.find((t) => t.ticket?.status === 'ok');
    return {
      provider: 'expo',
      messageId: (okTicket?.ticket as any)?.id ?? null,
      expoTicketId: (okTicket?.ticket as any)?.id ?? null,
      deadTokens,
      tickets: allTickets.map((t) => ({
        deviceId: t.device.id,
        ticketId: t.ticket?.status === 'ok' ? (t.ticket as any).id ?? null : null,
        status: t.ticket?.status ?? 'error',
      })),
    };
  },
};
```

- [ ] **Step 2: Commit**

```bash
git add src/core/notifications/channels/push/expo.provider.ts
git commit -m "feat(notifications): Expo push provider with chunking + dead token detection"
```

---

### Task 22: FCM provider

**Files:**
- Create: `avy-erp-backend/src/core/notifications/channels/push/fcm.provider.ts`

- [ ] **Step 1: Implementation**

```typescript
// src/core/notifications/channels/push/fcm.provider.ts
import * as admin from 'firebase-admin';
import { logger } from '../../../../config/logger';
import type { NotificationPriority, UserDevice } from '@prisma/client';

export interface FcmSendPayload {
  title: string;
  body: string;
  data: Record<string, unknown>;
  priority: NotificationPriority;
}

export interface FcmSendResult {
  provider: 'fcm';
  messageId: string | null;
  deadTokens: string[];
}

export const fcmProvider = {
  async send(devices: UserDevice[], payload: FcmSendPayload, traceId: string): Promise<FcmSendResult> {
    if (!admin.apps.length) {
      throw Object.assign(new Error('FIREBASE_NOT_INITIALIZED'), { code: 'FIREBASE_NOT_INITIALIZED' });
    }
    const messaging = admin.messaging();
    const tokens = devices.map((d) => d.fcmToken).filter(Boolean);
    if (tokens.length === 0) {
      throw Object.assign(new Error('NO_FCM_TOKENS'), { code: 'NO_FCM_TOKENS' });
    }

    const stringData = Object.fromEntries(
      Object.entries({ ...payload.data, traceId })
        .filter(([, v]) => v != null)
        .map(([k, v]) => [k, String(v)]),
    );

    try {
      const response = await messaging.sendEachForMulticast({
        notification: { title: payload.title, body: payload.body },
        data: stringData,
        tokens,
        android: {
          priority: payload.priority === 'CRITICAL' || payload.priority === 'HIGH' ? 'high' : 'normal',
        },
        apns: {
          payload: { aps: { sound: 'default', badge: 1 } },
        },
        webpush: {
          notification: { title: payload.title, body: payload.body, icon: '/favicon.ico' },
        },
      });

      const deadTokens: string[] = [];
      response.responses.forEach((r, idx) => {
        if (!r.success) {
          const code = (r.error as any)?.code;
          if (code === 'messaging/registration-token-not-registered' || code === 'messaging/invalid-registration-token') {
            deadTokens.push(tokens[idx]);
          }
        }
      });

      const firstOk = response.responses.find((r) => r.success);
      return {
        provider: 'fcm',
        messageId: firstOk?.messageId ?? null,
        deadTokens,
      };
    } catch (err) {
      logger.error('FCM sendEachForMulticast failed', { error: err });
      throw err;
    }
  },
};
```

- [ ] **Step 2: Commit**

```bash
git add src/core/notifications/channels/push/fcm.provider.ts
git commit -m "feat(notifications): FCM push provider for web tokens"
```

---

### Task 23: Push channel router

**Files:**
- Create: `avy-erp-backend/src/core/notifications/channels/push/push.channel.ts`

- [ ] **Step 1: Implementation**

```typescript
// src/core/notifications/channels/push/push.channel.ts
import { platformPrisma } from '../../../../config/database';
import { logger } from '../../../../config/logger';
import { maskForChannel } from '../../templates/masker';
import { expoProvider } from './expo.provider';
import { fcmProvider } from './fcm.provider';
import type { ChannelSendArgs, ChannelSendResult } from '../channel-router';

export const pushChannel = {
  async send({ notificationId, userId, traceId, priority }: ChannelSendArgs): Promise<ChannelSendResult> {
    const devices = await platformPrisma.userDevice.findMany({
      where: { userId, isActive: true },
    });
    if (devices.length === 0) {
      throw Object.assign(new Error('NO_ACTIVE_DEVICES'), { code: 'NO_ACTIVE_DEVICES' });
    }

    const pref = await platformPrisma.userNotificationPreference.findUnique({ where: { userId } });
    const targetDevices =
      pref?.deviceStrategy === 'LATEST_ONLY'
        ? [[...devices].sort((a, b) => b.lastActiveAt.getTime() - a.lastActiveAt.getTime())[0]]
        : devices;

    const expoDevices = targetDevices.filter((d) => d.tokenType === 'EXPO');
    const fcmDevices  = targetDevices.filter((d) => d.tokenType === 'FCM_WEB' || d.tokenType === 'FCM_NATIVE');

    const notif = await platformPrisma.notification.findUniqueOrThrow({ where: { id: notificationId } });
    const template = notif.templateId
      ? await platformPrisma.notificationTemplate.findUnique({ where: { id: notif.templateId } })
      : null;
    const sensitiveFields = (template?.sensitiveFields as string[] | null) ?? [];

    const masked = maskForChannel('PUSH',
      { title: notif.title, body: notif.body, data: notif.data as Record<string, unknown> | undefined },
      sensitiveFields,
    );

    const payload = {
      title: masked.title,
      body: masked.body,
      data: (masked.data ?? {}) as Record<string, unknown>,
      priority,
    };

    const results = await Promise.allSettled([
      expoDevices.length > 0 ? expoProvider.send(expoDevices, payload, traceId) : Promise.resolve(null),
      fcmDevices.length > 0  ? fcmProvider.send(fcmDevices, payload, traceId)  : Promise.resolve(null),
    ]);

    // Deactivate dead tokens across both providers
    for (const r of results) {
      if (r.status === 'fulfilled' && r.value) {
        const deadTokens = (r.value as any).deadTokens ?? [];
        if (deadTokens.length > 0) {
          await platformPrisma.userDevice.updateMany({
            where: { fcmToken: { in: deadTokens } },
            data: { isActive: false, lastFailureAt: new Date(), lastFailureCode: 'DeviceNotRegistered' },
          });
          logger.info('Deactivated dead push tokens', { count: deadTokens.length });
        }
      }
    }

    // Prefer Expo result (mobile) for the returned messageId
    const expoRes = results[0];
    const fcmRes = results[1];
    if (expoRes.status === 'fulfilled' && expoRes.value) {
      const v = expoRes.value as any;
      return { provider: 'expo', messageId: v.messageId, expoTicketId: v.expoTicketId, deadTokens: v.deadTokens };
    }
    if (fcmRes.status === 'fulfilled' && fcmRes.value) {
      const v = fcmRes.value as any;
      return { provider: 'fcm', messageId: v.messageId, deadTokens: v.deadTokens };
    }
    // Both failed
    const firstErr = results.find((r) => r.status === 'rejected') as PromiseRejectedResult | undefined;
    throw firstErr?.reason ?? new Error('PUSH_ALL_PROVIDERS_FAILED');
  },
};
```

- [ ] **Step 2: Commit**

```bash
git add src/core/notifications/channels/push/push.channel.ts
git commit -m "feat(notifications): push channel router (Expo + FCM) with masking"
```

---

### Task 24: Email, SMS, WhatsApp channels

**Files:**
- Create: `avy-erp-backend/src/core/notifications/channels/email.channel.ts`
- Create: `avy-erp-backend/src/core/notifications/channels/sms.channel.ts`
- Create: `avy-erp-backend/src/core/notifications/channels/whatsapp.channel.ts`

- [ ] **Step 1: `email.channel.ts`**

```typescript
// src/core/notifications/channels/email.channel.ts
import { platformPrisma } from '../../../config/database';
import { sendEmail } from '../../../infrastructure/email/email.service';
import type { ChannelSendArgs, ChannelSendResult } from './channel-router';

export const emailChannel = {
  async send({ notificationId, userId, traceId }: ChannelSendArgs): Promise<ChannelSendResult> {
    const notif = await platformPrisma.notification.findUniqueOrThrow({ where: { id: notificationId } });
    const user = await platformPrisma.user.findUniqueOrThrow({ where: { id: userId } });
    if (!user.email) throw Object.assign(new Error('NO_USER_EMAIL'), { code: 'NO_USER_EMAIL' });

    const subject = notif.title;
    const html = `<p>${escapeHtml(notif.body)}</p>${notif.actionUrl ? `<p><a href="${notif.actionUrl}">Open</a></p>` : ''}`;
    await sendEmail(user.email, subject, html, notif.body);

    return { provider: 'smtp', messageId: null };
  },
};

function escapeHtml(s: string): string {
  return s
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');
}
```

- [ ] **Step 2: `sms.channel.ts`**

```typescript
// src/core/notifications/channels/sms.channel.ts
import type { ChannelSendArgs, ChannelSendResult } from './channel-router';

export const smsChannel = {
  async send(_args: ChannelSendArgs): Promise<ChannelSendResult> {
    throw Object.assign(new Error('SMS_NOT_IMPLEMENTED'), { code: 'SMS_NOT_IMPLEMENTED' });
  },
};
```

- [ ] **Step 3: `whatsapp.channel.ts`**

```typescript
// src/core/notifications/channels/whatsapp.channel.ts
import type { ChannelSendArgs, ChannelSendResult } from './channel-router';

export const whatsappChannel = {
  async send(_args: ChannelSendArgs): Promise<ChannelSendResult> {
    throw Object.assign(new Error('WHATSAPP_NOT_IMPLEMENTED'), { code: 'WHATSAPP_NOT_IMPLEMENTED' });
  },
};
```

- [ ] **Step 4: Commit**

```bash
git add src/core/notifications/channels/email.channel.ts src/core/notifications/channels/sms.channel.ts src/core/notifications/channels/whatsapp.channel.ts
git commit -m "feat(notifications): email channel + SMS/WhatsApp stubs"
```

---

## Phase 6: REST endpoints + facade

### Task 25: Preferences service/controller/routes/validators

**Files:**
- Create: `avy-erp-backend/src/core/notifications/preferences/preferences.service.ts`
- Create: `avy-erp-backend/src/core/notifications/preferences/preferences.controller.ts`
- Create: `avy-erp-backend/src/core/notifications/preferences/preferences.validators.ts`
- Create: `avy-erp-backend/src/core/notifications/preferences/preferences.routes.ts`

- [ ] **Step 1: `preferences.validators.ts`**

```typescript
// src/core/notifications/preferences/preferences.validators.ts
import { z } from 'zod';

export const updatePreferencesSchema = z.object({
  inAppEnabled:      z.boolean().optional(),
  pushEnabled:       z.boolean().optional(),
  emailEnabled:      z.boolean().optional(),
  smsEnabled:        z.boolean().optional(),
  whatsappEnabled:   z.boolean().optional(),
  deviceStrategy:    z.enum(['ALL', 'LATEST_ONLY']).optional(),
  quietHoursEnabled: z.boolean().optional(),
  quietHoursStart:   z.string().regex(/^\d{2}:\d{2}$/).optional().nullable(),
  quietHoursEnd:     z.string().regex(/^\d{2}:\d{2}$/).optional().nullable(),
});

export type UpdatePreferencesInput = z.infer<typeof updatePreferencesSchema>;
```

- [ ] **Step 2: `preferences.service.ts`**

```typescript
// src/core/notifications/preferences/preferences.service.ts
import { platformPrisma } from '../../../config/database';
import type { UpdatePreferencesInput } from './preferences.validators';

export const preferencesService = {
  async getForUser(userId: string) {
    let pref = await platformPrisma.userNotificationPreference.findUnique({ where: { userId } });
    if (!pref) {
      pref = await platformPrisma.userNotificationPreference.create({ data: { userId } });
    }
    const user = await platformPrisma.user.findUnique({ where: { id: userId }, select: { companyId: true } });
    const companySettings = user?.companyId
      ? await platformPrisma.companySettings.findFirst({ where: { companyId: user.companyId } })
      : null;
    return {
      preference: pref,
      companyMasters: {
        inApp: companySettings?.inAppNotifications ?? true,
        push: companySettings?.pushNotifications ?? true,
        email: companySettings?.emailNotifications ?? true,
        sms: companySettings?.smsNotifications ?? false,
        whatsapp: companySettings?.whatsappNotifications ?? false,
      },
    };
  },

  async update(userId: string, data: UpdatePreferencesInput) {
    return platformPrisma.userNotificationPreference.upsert({
      where: { userId },
      create: { userId, ...data },
      update: data,
    });
  },
};
```

- [ ] **Step 3: `preferences.controller.ts`**

```typescript
// src/core/notifications/preferences/preferences.controller.ts
import { Request, Response } from 'express';
import { asyncHandler } from '../../../shared/utils/async-handler';
import { createSuccessResponse } from '../../../shared/utils/response';
import { ApiError } from '../../../shared/errors';
import { preferencesService } from './preferences.service';
import { updatePreferencesSchema } from './preferences.validators';

class PreferencesController {
  getMyPreferences = asyncHandler(async (req: Request, res: Response) => {
    const userId = (req as any).user?.id;
    if (!userId) throw ApiError.unauthorized();
    const result = await preferencesService.getForUser(userId);
    res.json(createSuccessResponse(result));
  });

  updateMyPreferences = asyncHandler(async (req: Request, res: Response) => {
    const userId = (req as any).user?.id;
    if (!userId) throw ApiError.unauthorized();
    const parsed = updatePreferencesSchema.safeParse(req.body);
    if (!parsed.success) throw ApiError.badRequest(parsed.error.errors.map((e) => e.message).join(', '));
    const result = await preferencesService.update(userId, parsed.data);
    res.json(createSuccessResponse(result, 'Preferences updated'));
  });
}

export const preferencesController = new PreferencesController();
```

- [ ] **Step 4: `preferences.routes.ts`**

```typescript
// src/core/notifications/preferences/preferences.routes.ts
import { Router } from 'express';
import { preferencesController } from './preferences.controller';

const router = Router();

router.get('/', preferencesController.getMyPreferences);
router.patch('/', preferencesController.updateMyPreferences);

export default router;
```

- [ ] **Step 5: Commit**

```bash
git add src/core/notifications/preferences
git commit -m "feat(notifications): per-user preferences service + REST"
```

---

### Task 26: Extend notification controller (archive, events, test)

**Files:**
- Modify: `avy-erp-backend/src/core/notifications/notification.controller.ts`
- Modify: `avy-erp-backend/src/core/notifications/notification.routes.ts`

- [ ] **Step 1: Add methods to the controller**

```typescript
// Add to notification.controller.ts

archiveNotification = asyncHandler(async (req: Request, res: Response) => {
  const userId = (req as any).user?.id;
  if (!userId) throw ApiError.unauthorized();
  const { id } = req.params;
  const notif = await platformPrisma.notification.findFirst({ where: { id, userId } });
  if (!notif) throw ApiError.notFound('Notification not found');
  const updated = await platformPrisma.notification.update({
    where: { id },
    data: { status: 'ARCHIVED', archivedAt: new Date() },
  });
  res.json(createSuccessResponse(updated, 'Archived'));
});

getDeliveryEvents = asyncHandler(async (req: Request, res: Response) => {
  const userId = (req as any).user?.id;
  if (!userId) throw ApiError.unauthorized();
  const { id } = req.params;
  const notif = await platformPrisma.notification.findFirst({ where: { id, userId } });
  if (!notif) throw ApiError.notFound();
  const events = await platformPrisma.notificationEvent.findMany({
    where: { notificationId: id },
    orderBy: { occurredAt: 'asc' },
  });
  res.json(createSuccessResponse(events));
});

sendTestNotification = asyncHandler(async (req: Request, res: Response) => {
  const user = (req as any).user;
  if (!user?.id) throw ApiError.unauthorized();
  const result = await dispatch({
    companyId: user.companyId,
    triggerEvent: 'TEST_NOTIFICATION',
    explicitRecipients: [user.id],
    adHoc: {
      title: 'Test Notification',
      body: 'This is a test notification to verify your preferences are working.',
      channels: ['IN_APP', 'PUSH', 'EMAIL'],
      priority: 'MEDIUM',
    },
    type: 'TEST',
  });
  res.json(createSuccessResponse(result, 'Test notification dispatched'));
});
```

Add required imports at the top:
```typescript
import { dispatch } from './dispatch/dispatcher';
import { platformPrisma } from '../../config/database';
```

- [ ] **Step 2: Register routes**

Extend `notification.routes.ts`:

```typescript
router.patch('/:id/archive', notificationController.archiveNotification);
router.get('/:id/events', notificationController.getDeliveryEvents);
router.post('/test', notificationController.sendTestNotification);
```

- [ ] **Step 3: Mount preferences routes in main routes file**

In `notification.routes.ts`, add at the top:
```typescript
import preferencesRoutes from './preferences/preferences.routes';
router.use('/preferences', preferencesRoutes);
```

- [ ] **Step 4: Commit**

```bash
git add src/core/notifications/notification.controller.ts src/core/notifications/notification.routes.ts
git commit -m "feat(notifications): archive, events, test-send endpoints + mount preferences routes"
```

---

### Task 27: Legacy facade + extended device registration

**Files:**
- Modify: `avy-erp-backend/src/core/notifications/notification.service.ts`
- Modify: `avy-erp-backend/src/core/notifications/notification.controller.ts` (registerDevice payload)

- [ ] **Step 1: Facade**

Replace the existing `notification.service.ts` content with:

```typescript
// src/core/notifications/notification.service.ts
import { platformPrisma } from '../../config/database';
import { ApiError } from '../../shared/errors';
import { logger } from '../../config/logger';
import { dispatch } from './dispatch/dispatcher';

class NotificationService {
  private firebaseAdmin: typeof import('firebase-admin') | null = null;

  async initFirebase(): Promise<void> {
    try {
      const admin = await import('firebase-admin');
      if (!admin.apps.length) {
        const serviceAccount = process.env.FIREBASE_SERVICE_ACCOUNT_KEY;
        if (serviceAccount) {
          admin.initializeApp({
            credential: admin.credential.cert(JSON.parse(serviceAccount)),
          });
          this.firebaseAdmin = admin;
          logger.info('Firebase Admin initialized for push notifications');
        } else {
          logger.warn('FIREBASE_SERVICE_ACCOUNT_KEY not set — push disabled for FCM channel');
        }
      } else {
        this.firebaseAdmin = admin;
      }
    } catch (err) {
      logger.warn('Firebase Admin init failed', { error: err });
    }
  }

  /**
   * Primary API: use dispatch() for all new callers.
   */
  dispatch = dispatch;

  /**
   * Legacy API — delegates to dispatch() for backward compatibility.
   */
  async send(params: {
    recipientIds: string[];
    title: string;
    body: string;
    type: string;
    entityType?: string;
    entityId?: string;
    channels: ('in_app' | 'push' | 'email')[];
    data?: Record<string, any>;
    companyId: string;
  }) {
    return dispatch({
      companyId: params.companyId,
      triggerEvent: params.type,
      entityType: params.entityType,
      entityId: params.entityId,
      explicitRecipients: params.recipientIds,
      tokens: params.data,
      type: params.type,
      adHoc: {
        title: params.title,
        body: params.body,
        channels: params.channels.map((c) => c.toUpperCase()) as any,
      },
    });
  }

  // Device management
  async registerDevice(userId: string, data: {
    platform: string;
    fcmToken: string;
    tokenType?: 'EXPO' | 'FCM_WEB' | 'FCM_NATIVE';
    deviceName?: string;
    deviceModel?: string;
    osVersion?: string;
    appVersion?: string;
    locale?: string;
    timezone?: string;
  }) {
    return platformPrisma.userDevice.upsert({
      where: { userId_fcmToken: { userId, fcmToken: data.fcmToken } },
      create: {
        userId,
        platform: data.platform,
        fcmToken: data.fcmToken,
        tokenType: data.tokenType ?? (data.platform === 'WEB' ? 'FCM_WEB' : 'EXPO'),
        deviceName: data.deviceName ?? null,
        deviceModel: data.deviceModel ?? null,
        osVersion: data.osVersion ?? null,
        appVersion: data.appVersion ?? null,
        locale: data.locale ?? null,
        timezone: data.timezone ?? null,
        isActive: true,
      },
      update: {
        platform: data.platform,
        tokenType: data.tokenType ?? (data.platform === 'WEB' ? 'FCM_WEB' : 'EXPO'),
        deviceName: data.deviceName ?? null,
        deviceModel: data.deviceModel ?? null,
        osVersion: data.osVersion ?? null,
        appVersion: data.appVersion ?? null,
        locale: data.locale ?? null,
        timezone: data.timezone ?? null,
        isActive: true,
        failureCount: 0,
        lastActiveAt: new Date(),
      },
    });
  }

  async unregisterDevice(userId: string, fcmToken: string): Promise<void> {
    await platformPrisma.userDevice.updateMany({
      where: { userId, fcmToken },
      data: { isActive: false },
    });
  }

  // Queries
  async listNotifications(userId: string, page = 1, limit = 20) {
    const skip = (page - 1) * limit;
    const [notifications, total] = await Promise.all([
      platformPrisma.notification.findMany({
        where: { userId, status: { not: 'ARCHIVED' } },
        orderBy: { createdAt: 'desc' },
        skip,
        take: limit,
      }),
      platformPrisma.notification.count({ where: { userId, status: { not: 'ARCHIVED' } } }),
    ]);
    return { notifications, total, page, limit, totalPages: Math.ceil(total / limit) };
  }

  async markAsRead(userId: string, id: string) {
    const notification = await platformPrisma.notification.findFirst({ where: { id, userId } });
    if (!notification) throw ApiError.notFound('Notification not found');
    return platformPrisma.notification.update({
      where: { id },
      data: { isRead: true, status: 'READ', readAt: new Date() },
    });
  }

  async markAllAsRead(userId: string): Promise<void> {
    await platformPrisma.notification.updateMany({
      where: { userId, status: 'UNREAD' },
      data: { isRead: true, status: 'READ', readAt: new Date() },
    });
  }

  async getUnreadCount(userId: string): Promise<number> {
    return platformPrisma.notification.count({ where: { userId, status: 'UNREAD' } });
  }
}

export const notificationService = new NotificationService();
```

- [ ] **Step 2: Update registerDevice validator in controller**

In `notification.controller.ts`, extend the Zod schema:

```typescript
const registerDeviceSchema = z.object({
  platform: z.enum(['MOBILE_IOS', 'MOBILE_ANDROID', 'WEB']),
  fcmToken: z.string().min(1),
  tokenType: z.enum(['EXPO', 'FCM_WEB', 'FCM_NATIVE']).optional(),
  deviceName: z.string().optional(),
  deviceModel: z.string().optional(),
  osVersion: z.string().optional(),
  appVersion: z.string().optional(),
  locale: z.string().optional(),
  timezone: z.string().optional(),
});
```

Pass all parsed fields to `notificationService.registerDevice(userId, parsed.data)`.

- [ ] **Step 3: Commit**

```bash
git add src/core/notifications/notification.service.ts src/core/notifications/notification.controller.ts
git commit -m "feat(notifications): legacy send() facade + extended device registration payload"
```

---

## Phase 7: Event wiring

Each task in this phase is mechanical: find the service method, add a `notificationService.dispatch(...)` call. The specific trigger events, entity types, tokens, recipient contexts, and action URLs are defined in spec §6. Tasks are grouped by module.

**Pattern for every dispatch call:**

```typescript
import { notificationService } from '../../../core/notifications/notification.service';

// inside the service method, after the business write succeeds:
await notificationService.dispatch({
  companyId,
  triggerEvent: 'LEAVE_APPLICATION',
  entityType: 'LeaveRequest',
  entityId: leaveRequest.id,
  recipientContext: {
    requesterId: leaveRequest.userId,
    approverIds: await getApproverIds(leaveRequest), // helper
    managerId: employee.reportingManagerUserId ?? undefined,
  },
  tokens: {
    employee_name: employee.fullName,
    leave_days: leaveRequest.days,
    from_date: leaveRequest.fromDate.toISOString().slice(0, 10),
    to_date: leaveRequest.toDate.toISOString().slice(0, 10),
  },
  actionUrl: `/company/hr/leave-approvals/${leaveRequest.id}`,
});
```

### Task 28: Leave module wiring

**Files:**
- Modify: `avy-erp-backend/src/modules/hr/leave/leave.service.ts`

- [ ] **Step 1: Add dispatch on submit/approve/reject/cancel**

Add four dispatch calls per spec §6.1. Use `LEAVE_APPLICATION`, `LEAVE_APPROVED`, `LEAVE_REJECTED`, `LEAVE_CANCELLED`. `entityType: 'LeaveRequest'`.

- [ ] **Step 2: Commit**

```bash
git add src/modules/hr/leave
git commit -m "feat(notifications): wire leave service dispatches"
```

### Task 29: Attendance + overtime wiring

**Files:**
- Modify: `avy-erp-backend/src/modules/hr/attendance/attendance.service.ts`

- [ ] **Step 1:** Dispatches per spec §6.2. Covers regularization (3 states), overtime claim (3 states), missed-punch.

- [ ] **Step 2: Commit**

```bash
git add src/modules/hr/attendance
git commit -m "feat(notifications): wire attendance + overtime dispatches"
```

### Task 30: ESS module wiring

**Files:**
- Modify: `avy-erp-backend/src/modules/hr/ess/ess.service.ts`
- Delete: the old `triggerNotification()` email-only method (replace references with `dispatch()`)

- [ ] **Step 1:** Dispatches per spec §6.3. Shift change, shift swap, WFH, profile update, reimbursement (3 states), loan (3 states), IT declaration (2 states), travel, resignation, helpdesk, grievance.

- [ ] **Step 2:** In the approval workflow transition code (`transitionApprovalRequest`), add generic dispatch per spec §6.4.

- [ ] **Step 3:** Remove the old `triggerNotification()` method — it's dead code now.

- [ ] **Step 4: Commit**

```bash
git add src/modules/hr/ess
git commit -m "feat(notifications): wire ESS dispatches + generic approval transitions + remove email-only shim"
```

### Task 31: Payroll wiring

**Files:**
- Modify: `avy-erp-backend/src/modules/hr/payroll-run/payroll-run.service.ts`

- [ ] **Step 1:** Dispatches per spec §6.6. `PAYROLL_APPROVAL`, `PAYROLL_APPROVED`, `PAYSLIP_PUBLISHED`, `BONUS_UPLOAD`, `SALARY_CREDITED` (CRITICAL, `systemCritical: true`).

- [ ] **Step 2: Commit**

```bash
git add src/modules/hr/payroll-run
git commit -m "feat(notifications): wire payroll dispatches (incl. critical salary credited)"
```

### Task 32: Employee + offboarding wiring

**Files:**
- Modify: `avy-erp-backend/src/modules/hr/employee/employee.service.ts`
- Modify: `avy-erp-backend/src/modules/hr/offboarding/offboarding.service.ts`

- [ ] **Step 1:** Dispatches per spec §6.5.

- [ ] **Step 2: Commit**

```bash
git add src/modules/hr/employee src/modules/hr/offboarding
git commit -m "feat(notifications): wire employee lifecycle + offboarding dispatches"
```

### Task 33: Recruitment + training wiring

**Files:**
- Modify: `avy-erp-backend/src/modules/hr/advanced/recruitment/recruitment.service.ts`
- Modify: `avy-erp-backend/src/modules/hr/advanced/training/training.service.ts`
- Modify: `avy-erp-backend/src/shared/events/listeners/hr-listeners.ts`

- [ ] **Step 1:** Update existing `hr-listeners.ts` calls to use `notificationService.dispatch()` signature instead of legacy `send()`. Keep behavior identical. Add remaining dispatches per spec §6.7 and §6.8.

- [ ] **Step 2: Commit**

```bash
git add src/modules/hr/advanced src/shared/events/listeners
git commit -m "feat(notifications): wire recruitment + training dispatches; migrate HR listeners"
```

### Task 34: Assets wiring

**Files:**
- Modify: `avy-erp-backend/src/modules/hr/advanced/assets/assets.service.ts`

- [ ] **Step 1:** Dispatches per spec §6.9.

- [ ] **Step 2: Commit**

```bash
git add src/modules/hr/advanced/assets
git commit -m "feat(notifications): wire asset issuance + assignment dispatches"
```

### Task 35: Support ticket bridge

**Files:**
- Modify: `avy-erp-backend/src/core/support/support.service.ts`

- [ ] **Step 1:** Add dispatches at all existing ticket state-transition sites. Keep existing Socket.io ticket emissions unchanged — they serve a different purpose (live ticket UI). Spec §6.10.

- [ ] **Step 2: Commit**

```bash
git add src/core/support
git commit -m "feat(notifications): bridge support ticket events into dispatcher"
```

### Task 36: Auth critical dispatches

**Files:**
- Modify: `avy-erp-backend/src/core/auth/auth.service.ts`

- [ ] **Step 1:** Add CRITICAL dispatches for `PASSWORD_RESET`, `NEW_DEVICE_LOGIN`, `ACCOUNT_LOCKED`. All with `systemCritical: true`. Spec §6.11.

- [ ] **Step 2: Commit**

```bash
git add src/core/auth
git commit -m "feat(notifications): wire auth critical dispatches (password reset, new device)"
```

### Task 37: Hook seeding into tenant creation

**Files:**
- Modify: `avy-erp-backend/src/core/company/company.service.ts` (or wherever new companies are created)

- [ ] **Step 1:** In `createCompany()` (or the tenant-provision flow), after the company is committed, call:

```typescript
await seedDefaultTemplatesForCompany(company.id);
```

Import: `import { seedDefaultTemplatesForCompany } from '../notifications/templates/seed-defaults';`

- [ ] **Step 2: Commit**

```bash
git add src/core/company
git commit -m "feat(notifications): seed default templates on new tenant creation"
```

### Task 38: Backend build + type-check gate

- [ ] **Step 1: Run full build**

```bash
cd avy-erp-backend
pnpm prisma:merge && pnpm db:generate && pnpm type-check && pnpm build
```

Expected: clean build, no type errors.

- [ ] **Step 2: Fix any residual type errors inline** (e.g., missing imports, type mismatches between legacy shim and new dispatcher signature).

- [ ] **Step 3: Commit fixes if any**

```bash
git add -A
git commit -m "fix(notifications): resolve type errors in event wiring sites"
```

---

## Phase 8: Web changes

### Task 39: Install deps (none new) + API client extensions

**Files:**
- Modify: `web-system-app/src/lib/api/notifications.ts`

- [ ] **Step 1: Extend `notificationApi`**

```typescript
// web-system-app/src/lib/api/notifications.ts
import { client } from './client';

export interface NotificationPreferences {
  preference: {
    inAppEnabled: boolean;
    pushEnabled: boolean;
    emailEnabled: boolean;
    smsEnabled: boolean;
    whatsappEnabled: boolean;
    deviceStrategy: 'ALL' | 'LATEST_ONLY';
    quietHoursEnabled: boolean;
    quietHoursStart: string | null;
    quietHoursEnd: string | null;
  };
  companyMasters: {
    inApp: boolean;
    push: boolean;
    email: boolean;
    sms: boolean;
    whatsapp: boolean;
  };
}

export const notificationApi = {
  listNotifications: (params?: { page?: number; limit?: number }) =>
    client.get('/notifications', { params }).then((r) => r.data),
  getUnreadCount: () => client.get('/notifications/unread-count').then((r) => r.data),
  markAsRead: (id: string) => client.patch(`/notifications/${id}/read`).then((r) => r.data),
  markAllAsRead: () => client.patch('/notifications/read-all').then((r) => r.data),
  archive: (id: string) => client.patch(`/notifications/${id}/archive`).then((r) => r.data),
  getPreferences: () => client.get('/notifications/preferences').then((r) => r.data),
  updatePreferences: (data: Partial<NotificationPreferences['preference']>) =>
    client.patch('/notifications/preferences', data).then((r) => r.data),
  getDeliveryEvents: (id: string) => client.get(`/notifications/${id}/events`).then((r) => r.data),
  sendTestNotification: () => client.post('/notifications/test').then((r) => r.data),
};
```

- [ ] **Step 2: Commit**

```bash
cd web-system-app
git add src/lib/api/notifications.ts
git commit -m "feat(notifications): API client — archive, preferences, events, test"
```

---

### Task 40: Socket notification hook + user:{id} room support

**Files:**
- Modify: `web-system-app/src/lib/socket.ts`
- Create: `web-system-app/src/hooks/useNotificationSocket.ts`
- Modify: `web-system-app/src/layouts/DashboardLayout.tsx`

- [ ] **Step 1: Ensure socket connects after login**

In `src/lib/api/use-auth-mutations.ts` login `onSuccess`, add `connectSocket()`. In logout, already calls `disconnectSocket()` — verify.

- [ ] **Step 2: Create hook**

```typescript
// src/hooks/useNotificationSocket.ts
import { useEffect } from 'react';
import { useQueryClient } from '@tanstack/react-query';
import { getSocket } from '@/lib/socket';

export function useNotificationSocket() {
  const queryClient = useQueryClient();
  useEffect(() => {
    const socket = getSocket();
    const handler = () => {
      queryClient.invalidateQueries({ queryKey: ['notifications'] });
    };
    socket.on('notification:new', handler);
    return () => { socket.off('notification:new', handler); };
  }, [queryClient]);
}
```

- [ ] **Step 3: Mount in DashboardLayout**

```typescript
import { useNotificationSocket } from '@/hooks/useNotificationSocket';
// inside component
useNotificationSocket();
```

- [ ] **Step 4: Commit**

```bash
git add src/hooks/useNotificationSocket.ts src/layouts/DashboardLayout.tsx src/lib/socket.ts src/lib/api/use-auth-mutations.ts
git commit -m "feat(notifications): web socket notification:new → React Query invalidate"
```

---

### Task 41: Polling reduction + priority badges + archive button

**Files:**
- Modify: `web-system-app/src/layouts/TopBar.tsx`
- Modify: `web-system-app/src/features/notifications/NotificationListScreen.tsx`

- [ ] **Step 1: `TopBar.tsx` NotificationsPanel**

- Change `refetchInterval: 30_000` → `refetchInterval: 300_000` for unread count query.
- Add priority color stripe on left edge of each unread item.
- Add "Settings" link at the bottom next to "View all".

- [ ] **Step 2: `NotificationListScreen.tsx`**

- Add priority badge per row (LOW grey, MEDIUM blue, HIGH amber, CRITICAL red).
- Add archive button (calls `notificationApi.archive(id)` + invalidates query).
- Add filter dropdown: All / Unread / Archived.

- [ ] **Step 3: Commit**

```bash
git add src/layouts/TopBar.tsx src/features/notifications/NotificationListScreen.tsx
git commit -m "feat(notifications): reduce polling, priority badges, archive button"
```

---

### Task 42: Notification Preferences screen

**Files:**
- Create: `web-system-app/src/features/settings/NotificationPreferencesScreen.tsx`
- Create: `web-system-app/src/features/settings/api/use-notification-preferences.ts`
- Modify: `web-system-app/src/App.tsx` (register route)

- [ ] **Step 1: Hooks**

```typescript
// src/features/settings/api/use-notification-preferences.ts
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { notificationApi, type NotificationPreferences } from '@/lib/api/notifications';
import { showSuccess, showApiError } from '@/lib/toast';

export function useNotificationPreferences() {
  return useQuery({
    queryKey: ['notifications', 'preferences'],
    queryFn: notificationApi.getPreferences,
    staleTime: 30_000,
  });
}

export function useUpdateNotificationPreferences() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (data: Partial<NotificationPreferences['preference']>) =>
      notificationApi.updatePreferences(data),
    onSuccess: () => {
      showSuccess('Preferences updated');
      qc.invalidateQueries({ queryKey: ['notifications', 'preferences'] });
    },
    onError: (err) => showApiError(err),
  });
}

export function useSendTestNotification() {
  return useMutation({
    mutationFn: notificationApi.sendTestNotification,
    onSuccess: () => showSuccess('Test notification sent'),
    onError: (err) => showApiError(err),
  });
}
```

- [ ] **Step 2: Screen component**

Create `src/features/settings/NotificationPreferencesScreen.tsx` with sections:
- **Channels** — 5 toggles (In-App read-only, Push, Email, SMS, WhatsApp). Each toggle shows company-master state: if company off, toggle is disabled with tooltip.
- **Device strategy** — radio All vs Latest Only.
- **Quiet hours** — toggle + 2 time inputs (HH:MM).
- **Test notification** — button calling `useSendTestNotification()`.

Use Tailwind + existing project styling.

- [ ] **Step 3: Register route**

In `App.tsx`:
```typescript
const NotificationPreferencesScreen = lazyNamed(() => import('@/features/settings/NotificationPreferencesScreen'), 'NotificationPreferencesScreen');

<Route path="settings/notifications" element={<NotificationPreferencesScreen />} />
```

- [ ] **Step 4: Commit**

```bash
git add src/features/settings src/App.tsx
git commit -m "feat(notifications): web user preferences screen"
```

---

### Task 43: CompanySettings + tenant-onboarding toggles

**Files:**
- Modify: `web-system-app/src/features/company-admin/CompanySettingsScreen.tsx`
- Modify: `web-system-app/src/features/super-admin/tenant-onboarding/steps/Step05Preferences.tsx`

- [ ] **Step 1: Company Settings — add 3 toggles**

Near existing Email Notifications + WhatsApp Notifications toggles:

```typescript
<Toggle label="Push Notifications" description="Deliver notifications to user devices" checked={settings.pushNotifications} onChange={(v) => updateField("pushNotifications", v)} />
<Toggle label="SMS Notifications" description="Send SMS alerts (requires SMS provider)" checked={settings.smsNotifications} onChange={(v) => updateField("smsNotifications", v)} />
<Toggle label="In-App Notifications" description="Show bell icon notifications in web and mobile" checked={settings.inAppNotifications} onChange={(v) => updateField("inAppNotifications", v)} />
```

Ensure TypeScript `settings` type and default state include the new keys.

- [ ] **Step 2: Step05Preferences — same 3 toggles**

Add alongside existing Email Notifications toggle. SMS and WhatsApp can remain marked "COMING SOON" if desired.

- [ ] **Step 3: Commit**

```bash
git add src/features/company-admin/CompanySettingsScreen.tsx src/features/super-admin/tenant-onboarding/steps/Step05Preferences.tsx
git commit -m "feat(notifications): company-level push/sms/in-app toggles in settings + onboarding"
```

---

### Task 44: Device registration payload + web build gate

**Files:**
- Modify: `web-system-app/src/lib/notifications/setup.ts`

- [ ] **Step 1: Extend payload**

```typescript
await client.post('/notifications/register-device', {
  fcmToken: token,
  tokenType: 'FCM_WEB',
  platform: 'WEB',
  deviceName: navigator.userAgent.substring(0, 100),
  deviceModel: navigator.platform,
  osVersion: navigator.platform,
  appVersion: import.meta.env.VITE_APP_VERSION ?? 'web',
  locale: navigator.language,
  timezone: Intl.DateTimeFormat().resolvedOptions().timeZone,
});
```

- [ ] **Step 2: Build gate**

```bash
pnpm type-check && pnpm build
```
Expected: clean.

- [ ] **Step 3: Commit**

```bash
git add src/lib/notifications/setup.ts
git commit -m "feat(notifications): web device registration includes token metadata"
```

---

## Phase 9: Mobile changes

### Task 45: Install deps + app.config.ts

**Files:**
- Modify: `mobile-app/package.json`
- Modify: `mobile-app/app.config.ts`
- Create: `mobile-app/assets/notification-icon.png`

- [ ] **Step 1: Install**

```bash
cd mobile-app
pnpm add socket.io-client
pnpm add expo-application
```

- [ ] **Step 2: Add a placeholder notification icon**

If you don't have a designed monochrome icon yet, copy the adaptive icon as a placeholder:

```bash
cp assets/adaptive-icon.png assets/notification-icon.png
```

(Replace with a proper 96×96 white-silhouette PNG later.)

- [ ] **Step 3: Update plugin config**

In `app.config.ts`, replace the `expo-notifications` plugin block:

```typescript
[
  'expo-notifications',
  {
    icon: './assets/notification-icon.png',
    color: '#4F46E5',
    mode: 'production',
  },
],
```

- [ ] **Step 4: Commit**

```bash
git add package.json pnpm-lock.yaml app.config.ts assets/notification-icon.png
git commit -m "feat(notifications): mobile deps + expo-notifications plugin config"
```

---

### Task 46: Setup.ts hardening

**Files:**
- Modify: `mobile-app/src/lib/notifications/setup.ts`

- [ ] **Step 1: Replace file**

Replace contents with the hardened version from spec §9.3. Key changes:
- Graceful handling of `FirebaseApp is not initialized` (warn, not error).
- Extended device metadata in registration payload.
- Additional `critical` Android channel.
- Uses `expo-application` for `appVersion`.

- [ ] **Step 2: Commit**

```bash
git add src/lib/notifications/setup.ts
git commit -m "feat(notifications): mobile setup — graceful FCM handling + extended metadata"
```

---

### Task 47: Socket client + notification socket hook

**Files:**
- Create: `mobile-app/src/lib/socket.ts`
- Create: `mobile-app/src/features/notifications/use-notification-socket.ts`
- Modify: `mobile-app/src/app/(app)/_layout.tsx`

- [ ] **Step 1: Socket client**

```typescript
// src/lib/socket.ts
import { io, Socket } from 'socket.io-client';
import Env from '@/../env';
import { getToken } from '@/features/auth/utils';

let socket: Socket | null = null;

export function getSocket(): Socket {
  if (!socket) {
    const baseUrl = (Env.EXPO_PUBLIC_API_URL || '').replace(/\/api\/v1\/?$/, '');
    socket = io(baseUrl, {
      auth: (cb: any) => cb({ token: getToken()?.access }),
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

Adjust `getToken()` import path to match existing auth utils.

- [ ] **Step 2: Hook**

```typescript
// src/features/notifications/use-notification-socket.ts
import { useEffect } from 'react';
import { useQueryClient } from '@tanstack/react-query';
import * as Notifications from 'expo-notifications';
import { connectSocket, disconnectSocket, getSocket } from '@/lib/socket';
import { useAuthStore } from '@/features/auth/use-auth-store';
import { notificationApi } from '@/lib/api/notifications';

export function useNotificationSocket() {
  const queryClient = useQueryClient();
  const status = useAuthStore((s: any) => s.status);

  useEffect(() => {
    if (status !== 'signIn') return;
    const s = connectSocket();

    const handler = async () => {
      queryClient.invalidateQueries({ queryKey: ['notifications'] });

      if (__DEV__) {
        try {
          const fresh: any = await notificationApi.listNotifications({ limit: 1 });
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
    return () => {
      s.off('notification:new', handler);
      disconnectSocket();
    };
  }, [status, queryClient]);
}
```

- [ ] **Step 3: Mount in (app)/_layout.tsx**

Inside `TabLayoutInner`:
```typescript
import { useNotificationSocket } from '@/features/notifications/use-notification-socket';
// inside component
useNotificationSocket();
```

- [ ] **Step 4: Commit**

```bash
git add src/lib/socket.ts src/features/notifications/use-notification-socket.ts src/app/(app)/_layout.tsx
git commit -m "feat(notifications): mobile socket client + notification:new hook (dev local toast)"
```

---

### Task 48: Deep-link expansion

**Files:**
- Modify: `mobile-app/src/app/(app)/_layout.tsx`

- [ ] **Step 1:** Expand the existing `switch (data.entityType)` block to cover all new entity types per spec §9.5.

- [ ] **Step 2: Commit**

```bash
git add src/app/(app)/_layout.tsx
git commit -m "feat(notifications): expand mobile deep-link mapping"
```

---

### Task 49: Mobile notification API client extensions

**Files:**
- Modify: `mobile-app/src/lib/api/notifications.ts`

- [ ] **Step 1:** Mirror the web extensions (archive, preferences, events, test). Same shape.

- [ ] **Step 2: Commit**

```bash
git add src/lib/api/notifications.ts
git commit -m "feat(notifications): mobile API client extensions"
```

---

### Task 50: Mobile Notification Preferences screen

**Files:**
- Create: `mobile-app/src/features/settings/notification-preferences-screen.tsx`
- Create: `mobile-app/src/app/(app)/settings/notifications.tsx`
- Create: `mobile-app/src/features/settings/api/use-notification-preferences.ts`

- [ ] **Step 1: Hooks** — mirror web hook file.

- [ ] **Step 2: Screen** — same sections as web (Channels, Device Strategy, Quiet Hours, Test button). Use NativeWind + StyleSheet + existing Toggle component.

- [ ] **Step 3: Route file**

```typescript
// src/app/(app)/settings/notifications.tsx
export { NotificationPreferencesScreen as default } from '@/features/settings/notification-preferences-screen';
```

- [ ] **Step 4: Link from AppSidebar or bottom-sheet footer**

Add a "Notification Preferences" entry in the sidebar/profile menu navigating to the new route.

- [ ] **Step 5: Commit**

```bash
git add src/features/settings src/app/(app)/settings
git commit -m "feat(notifications): mobile user preferences screen"
```

---

### Task 51: Bell + sheet updates

**Files:**
- Modify: `mobile-app/src/features/notifications/notifications-sheet.tsx`
- Modify: `mobile-app/src/features/notifications/use-notification-count.ts`

- [ ] **Step 1:** `use-notification-count.ts` — change `refetchInterval` 30_000 → 300_000.

- [ ] **Step 2:** `notifications-sheet.tsx` — add priority badge per row, add swipe-to-archive action, add footer link to preferences.

- [ ] **Step 3: Type-check**

```bash
cd mobile-app
pnpm type-check
```

- [ ] **Step 4: Commit**

```bash
git add src/features/notifications
git commit -m "feat(notifications): mobile bell + sheet priority, archive, preferences link"
```

---

## Phase 10: Testing + rollout

### Task 52: Backend unit tests

**Files:**
- Create: `avy-erp-backend/src/core/notifications/__tests__/dispatcher.test.ts`
- Create: `avy-erp-backend/src/core/notifications/__tests__/consent-gate.test.ts`
- Create: `avy-erp-backend/src/core/notifications/__tests__/dedup.test.ts`
- Create: `avy-erp-backend/src/core/notifications/__tests__/template-compiler.test.ts`
- Create: `avy-erp-backend/src/core/notifications/__tests__/masker.test.ts`

- [ ] **Step 1: Minimum viable test set** — write at least one test per file above covering the happy path and one edge case (spec §10.1 lists all planned tests; this task ships the essential subset).

- [ ] **Step 2: Run**

```bash
pnpm test
```

- [ ] **Step 3: Commit**

```bash
git add src/core/notifications/__tests__
git commit -m "test(notifications): unit tests for dispatcher, consent, dedup, compiler, masker"
```

---

### Task 53: Backend integration smoke test

**Files:**
- Create: `avy-erp-backend/src/__tests__/integration/notifications/dispatch-smoke.test.ts`

- [ ] **Step 1:** Write a test that: creates a user + company, seeds templates, calls `dispatch()`, asserts a `Notification` row exists and a `NotificationEvent` `ENQUEUED` row exists. Uses the existing integration test harness.

- [ ] **Step 2: Run**

- [ ] **Step 3: Commit**

---

### Task 54: Seed defaults on all existing tenants in staging

```bash
cd avy-erp-backend
# Assumes STAGING_DATABASE_URL set appropriately, or run on local dev first
pnpm tsx prisma/seeds/2026-04-09-seed-default-notification-templates.ts
```

Verify via Studio or SQL:
```sql
SELECT companyId, COUNT(*) FROM notification_templates WHERE isSystem = true GROUP BY companyId;
```

---

### Task 55: Manual QA pass

Follow the 19-step checklist in spec §10.6 on a physical device + a laptop browser. Check off each item. File bugs as commits on the same branch if anything fails.

---

### Task 56: Final cleanup + final type-check gate + commit root submodule pointers

- [ ] **Step 1:** Each of the 3 submodules runs `pnpm type-check && pnpm lint`.

- [ ] **Step 2:** In the root repo:

```bash
cd /Users/chetan/Documents/Avyren-Technologies/Products/Mobile-ERP
git add avy-erp-backend web-system-app mobile-app docs
git commit -m "feat(notifications): full overhaul — dispatcher, BullMQ, preferences, realtime"
```

- [ ] **Step 3:** Push all three submodule branches (only after user approval):

```bash
cd avy-erp-backend && git push -u origin feat/notifications
cd ../web-system-app && git push -u origin feat/notifications
cd ../mobile-app && git push -u origin feat/notifications
cd .. && git push -u origin feat/notifications
```

---

## Self-Review Checklist

**Spec coverage:**
- [x] §2 Current state gaps → Tasks 1-27 fix every listed gap
- [x] §3 Architecture rules 1-22 → Tasks 4-27 implement all 22
- [x] §4 Data model → Task 2 + Task 3
- [x] §5 Backend directory layout → Tasks 4-27 create all listed files
- [x] §6 Event wiring map → Tasks 28-37 cover all 11 sub-sections
- [x] §7 Default templates → Tasks 9-11
- [x] §8 Web changes → Tasks 39-44
- [x] §9 Mobile changes → Tasks 45-51
- [x] §10 Testing strategy → Tasks 52-55
- [x] §11 Rollout plan → Tasks 54-56

**Placeholder scan:** No "TBD", no "similar to Task N" — each task has complete code snippets or exact reference to spec section.

**Type consistency:**
- `DispatchInput` / `DispatchResult` defined in Task 15 and referenced consistently.
- `ChannelSendArgs` / `ChannelSendResult` defined in Task 20, used in Tasks 21-24.
- `LoadedRule` defined in Task 12, used in Task 15.
- `QueueablePayload` defined in Task 15, used in Task 16.

**Migration safety:** All Prisma changes are additive; legacy `notificationService.send()` is kept as a thin facade in Task 27; no breaking changes to existing callers until they're migrated.
