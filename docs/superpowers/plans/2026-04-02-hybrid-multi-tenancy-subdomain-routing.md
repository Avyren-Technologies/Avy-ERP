# Hybrid Multi-Tenancy + Subdomain Routing — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Evolve the existing schema-per-tenant backend into a hybrid multi-tenancy system with subdomain-based routing for the web app, LRU+PgBouncer connection pooling, company registration flow, and tenant branding.

**Architecture:** Single PostgreSQL database with per-tenant schemas routed through PgBouncer. Web app deployed on Cloudflare Pages with wildcard subdomain (`*.avyren.in`). Tenant resolved from hostname at runtime. Mobile app unchanged except removal of register button.

**Tech Stack:** Node.js/Express, Prisma, PostgreSQL, PgBouncer (Docker), Redis, React (Vite), React Native (Expo), Cloudflare Pages + DNS, lru-cache

**Spec:** `docs/superpowers/specs/2026-04-02-hybrid-multi-tenancy-subdomain-routing-design.md`

---

## File Structure

### Backend — New Files
```
avy-erp-backend/
├── prisma/modules/platform/registration.prisma          # CompanyRegistrationRequest model
├── src/config/tenant-connection-manager.ts               # LRU cache + PrismaClient pool
├── src/core/registration/
│   ├── registration.validators.ts                        # Zod schemas for registration
│   ├── registration.service.ts                           # Registration business logic
│   ├── registration.controller.ts                        # Controller wrapping service
│   └── registration.routes.ts                            # Public + platform routes
├── src/infrastructure/email/registration-emails.ts       # Registration email templates
├── scripts/migrate-tenants.ts                            # CLI: migrate all tenant schemas
```

### Backend — Modified Files
```
avy-erp-backend/
├── prisma/modules/platform/tenant.prisma                 # Add slug, customDomain, dbStrategy, databaseUrl
├── src/config/database.ts                                # Replace createTenantPrisma with TenantConnectionManager
├── src/config/env.ts                                     # Add new env vars
├── src/middleware/tenant.middleware.ts                    # Add req.prisma, status blocking, audit log
├── src/shared/types/index.ts                             # Add prisma to Request type
├── src/app/routes.ts                                     # Mount registration routes
├── src/app/app.ts                                        # Dynamic CORS
├── src/core/tenant/tenant.service.ts                     # Add slug to onboarding
├── src/core/tenant/tenant.validators.ts                  # Add slug validation
├── src/core/auth/auth.routes.ts                          # Add tenant-branding endpoint
├── src/core/auth/auth.controller.ts                      # Add tenantBranding handler
├── docker-compose.yml                                    # Add PgBouncer service
├── package.json                                          # Add lru-cache, new script
```

### Web App — New Files
```
web-system-app/
├── src/lib/tenant.ts                                     # detectTenant() + TenantContext
├── src/features/auth/RegisterCompanyScreen.tsx            # Registration form
├── src/features/auth/TenantNotFoundScreen.tsx             # 404 for invalid subdomains
├── src/lib/api/registration.ts                           # Registration API + hooks
```

### Web App — Modified Files
```
web-system-app/
├── src/App.tsx                                           # Conditional routing by domain mode
├── src/features/auth/LoginScreen.tsx                     # Branded login for tenant subdomains
├── src/features/auth/LandingScreen.tsx                   # Demo login button
├── src/lib/api/auth.ts                                   # Add tenant branding API
├── src/lib/api/client.ts                                 # No changes needed (JWT-based)
```

### Mobile App — Modified Files
```
mobile-app/
├── src/features/auth/login-screen.tsx                    # Remove "Register Your Company" button
```

### Infrastructure
```
avy-erp-backend/
├── docker-compose.yml                                    # Add pgbouncer service
├── .env.example                                          # Add new env vars
```

---

## Task 1: Prisma Schema — Add Tenant Slug & Registration Request

**Files:**
- Modify: `avy-erp-backend/prisma/modules/platform/tenant.prisma`
- Create: `avy-erp-backend/prisma/modules/platform/registration.prisma`

- [ ] **Step 1: Add slug and future-proofing fields to Tenant model**

In `avy-erp-backend/prisma/modules/platform/tenant.prisma`, add the new fields to the Tenant model after `schemaName`:

```prisma
model Tenant {
  id            String       @id @default(cuid())
  schemaName    String       @unique // PostgreSQL schema name
  slug          String       @unique // URL-safe subdomain slug, e.g. "avyren-technologies"
  customDomain  String?      @unique // Future: custom domain, e.g. "erp.avyren.com"
  dbStrategy    String       @default("schema") // "schema" | "database"
  databaseUrl   String?      // Only used when dbStrategy = "database"
  companyId     String       @unique
  status        TenantStatus @default(ACTIVE)
  createdAt     DateTime     @default(now())
  updatedAt     DateTime     @updatedAt

  // Relations
  company       Company        @relation(fields: [companyId], references: [id], onDelete: Cascade)
  subscriptions Subscription[]

  @@map("tenants")
}
```

- [ ] **Step 2: Create registration.prisma with CompanyRegistrationRequest model**

Create `avy-erp-backend/prisma/modules/platform/registration.prisma`:

```prisma
// ==========================================
// PLATFORM — Company Registration Requests
// ==========================================
// Models: CompanyRegistrationRequest
// Enums: RegistrationRequestStatus

model CompanyRegistrationRequest {
  id              String                    @id @default(cuid())
  companyName     String
  adminName       String
  email           String                    @unique
  phone           String
  status          RegistrationRequestStatus @default(PENDING)
  ticketId        String?                   @unique
  rejectionReason String?
  createdAt       DateTime                  @default(now())
  updatedAt       DateTime                  @updatedAt

  ticket SupportTicket? @relation(fields: [ticketId], references: [id])

  @@map("company_registration_requests")
}

enum RegistrationRequestStatus {
  PENDING
  APPROVED
  REJECTED
}
```

- [ ] **Step 3: Add the relation back-reference to SupportTicket**

In the SupportTicket model (find which `.prisma` file it lives in under `prisma/modules/`), add:

```prisma
  registrationRequest CompanyRegistrationRequest?
```

- [ ] **Step 4: Merge and generate**

Run:
```bash
cd avy-erp-backend && pnpm prisma:merge && pnpm db:generate
```
Expected: Schema merges without conflicts, Prisma client generates successfully.

- [ ] **Step 5: Create migration**

Run:
```bash
cd avy-erp-backend && pnpm db:migrate --name add_tenant_slug_and_registration
```
Expected: Migration created and applied successfully.

- [ ] **Step 6: Commit**

```bash
git add prisma/modules/platform/tenant.prisma prisma/modules/platform/registration.prisma prisma/schema.prisma prisma/migrations/
git commit -m "$(cat <<'EOF'
feat: add tenant slug, dbStrategy fields and CompanyRegistrationRequest model

Adds subdomain slug to Tenant for URL routing, customDomain/dbStrategy
fields for future hybrid multi-tenancy, and a new registration request
model for the company registration workflow.

Co-Authored-By: Claude Opus 4.6 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Task 2: Environment Config — Add New Env Vars

**Files:**
- Modify: `avy-erp-backend/src/config/env.ts`
- Modify: `avy-erp-backend/.env` (or `.env.example`)

- [ ] **Step 1: Add new environment variables to Zod schema**

In `avy-erp-backend/src/config/env.ts`, add after the `CORS_ALLOWED_ORIGINS` field (before the closing `})`):

```typescript
  // Multi-tenancy
  MAIN_DOMAIN: z.string().default('avyren.in'),
  TENANT_CLIENT_CACHE_SIZE: z.coerce.number().default(50),
  SUPER_ADMIN_EMAIL: z.string().email().optional(),
```

- [ ] **Step 2: Add to .env.example**

Add to the bottom of `.env` or `.env.example`:

```env
# Multi-tenancy
MAIN_DOMAIN=avyren.in
TENANT_CLIENT_CACHE_SIZE=50
SUPER_ADMIN_EMAIL=admin@avyren.in
```

- [ ] **Step 3: Commit**

```bash
git add avy-erp-backend/src/config/env.ts avy-erp-backend/.env.example
git commit -m "$(cat <<'EOF'
feat: add multi-tenancy env vars (MAIN_DOMAIN, cache size, admin email)

Co-Authored-By: Claude Opus 4.6 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Task 3: Tenant Connection Manager — LRU Cache

**Files:**
- Create: `avy-erp-backend/src/config/tenant-connection-manager.ts`
- Modify: `avy-erp-backend/src/config/database.ts`
- Modify: `avy-erp-backend/package.json` (install `lru-cache`)

- [ ] **Step 1: Install lru-cache**

```bash
cd avy-erp-backend && pnpm add lru-cache
```

- [ ] **Step 2: Create TenantConnectionManager**

Create `avy-erp-backend/src/config/tenant-connection-manager.ts`:

```typescript
import { PrismaClient } from '@prisma/client';
import { LRUCache } from 'lru-cache';
import { createHash } from 'crypto';
import { env } from './env';
import { logger } from './logger';

interface TenantConnectionInfo {
  schemaName: string;
  dbStrategy?: string;
  databaseUrl?: string | null;
}

function buildConnectionString(tenant: TenantConnectionInfo): string {
  if (tenant.dbStrategy === 'database' && tenant.databaseUrl) {
    return `${tenant.databaseUrl}&pgbouncer=true&connection_limit=5`;
  }
  return env.DATABASE_URL_TEMPLATE
    .replace('{schema}', tenant.schemaName)
    .concat('&pgbouncer=true&connection_limit=5');
}

function hashKey(connectionString: string): string {
  return createHash('sha256').update(connectionString).digest('hex').slice(0, 16);
}

class TenantConnectionManager {
  private cache: LRUCache<string, PrismaClient>;

  constructor(maxSize: number) {
    this.cache = new LRUCache<string, PrismaClient>({
      max: maxSize,
      dispose: (client, key) => {
        logger.debug(`Evicting tenant PrismaClient from cache: ${key}`);
        client.$disconnect().catch((err) => {
          logger.error(`Error disconnecting evicted tenant client: ${err}`);
        });
      },
    });
  }

  getClient(tenant: TenantConnectionInfo): PrismaClient {
    const connString = buildConnectionString(tenant);
    const key = hashKey(connString);

    const cached = this.cache.get(key);
    if (cached) return cached;

    const client = new PrismaClient({
      datasources: { db: { url: connString } },
      log: ['error', 'warn'],
    });

    this.cache.set(key, client);
    logger.debug(`Created new tenant PrismaClient for schema: ${tenant.schemaName}`);
    return client;
  }

  async disconnectAll(): Promise<void> {
    const entries = [...this.cache.entries()];
    for (const [key, client] of entries) {
      try {
        await client.$disconnect();
      } catch (err) {
        logger.error(`Error disconnecting tenant client ${key}: ${err}`);
      }
    }
    this.cache.clear();
    logger.info(`Disconnected all ${entries.length} cached tenant clients`);
  }

  get size(): number {
    return this.cache.size;
  }
}

export const tenantConnectionManager = new TenantConnectionManager(
  env.TENANT_CLIENT_CACHE_SIZE
);
```

- [ ] **Step 3: Update database.ts — remove createTenantPrisma, add manager export**

In `avy-erp-backend/src/config/database.ts`, replace the `createTenantPrisma` function and add the new import:

Replace:
```typescript
// Tenant-specific Prisma client factory
export function createTenantPrisma(schemaName: string): PrismaClient {
  const databaseUrl = env.DATABASE_URL_TEMPLATE.replace('{schema}', schemaName);

  return new PrismaClient({
    datasources: {
      db: {
        url: databaseUrl,
      },
    },
    log: ['error', 'warn'],
  });
}
```

With:
```typescript
// Tenant connection management — re-export from dedicated module
export { tenantConnectionManager } from './tenant-connection-manager';
```

- [ ] **Step 4: Update all imports of createTenantPrisma across the codebase**

Search for all files that import `createTenantPrisma` and replace them with `tenantConnectionManager.getClient()`. The middleware update in Task 4 will handle attaching `req.prisma`, but any direct usage in services needs updating:

```bash
cd avy-erp-backend && grep -rn "createTenantPrisma" src/ --include="*.ts"
```

For each file found, replace:
```typescript
import { createTenantPrisma } from '../../config/database';
// ...
const tenantPrisma = createTenantPrisma(schemaName);
```

With:
```typescript
import { tenantConnectionManager } from '../../config/database';
// ...
const tenantPrisma = tenantConnectionManager.getClient({ schemaName });
```

- [ ] **Step 5: Update disconnectDatabase in database.ts**

In `avy-erp-backend/src/config/database.ts`, update `disconnectDatabase`:

```typescript
import { tenantConnectionManager } from './tenant-connection-manager';

export async function disconnectDatabase(): Promise<void> {
  try {
    await tenantConnectionManager.disconnectAll();
    await prisma.$disconnect();
    logger.info('✅ All database connections disconnected successfully');
  } catch (error) {
    logger.error('❌ Error disconnecting database:', error);
  }
}
```

- [ ] **Step 6: Commit**

```bash
git add avy-erp-backend/src/config/tenant-connection-manager.ts avy-erp-backend/src/config/database.ts avy-erp-backend/package.json avy-erp-backend/pnpm-lock.yaml
git add -u avy-erp-backend/src/  # catch any updated imports
git commit -m "$(cat <<'EOF'
feat: add LRU-based TenantConnectionManager replacing per-request PrismaClient

Introduces lru-cache to pool tenant PrismaClient instances (max 50 by default).
Evicted clients are properly disconnected. Connection strings include
pgbouncer=true and connection_limit=5 for PgBouncer compatibility.

Co-Authored-By: Claude Opus 4.6 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Task 4: Tenant Middleware — Status Blocking, Audit Log, req.prisma

**Files:**
- Modify: `avy-erp-backend/src/middleware/tenant.middleware.ts`
- Modify: `avy-erp-backend/src/shared/types/index.ts`

- [ ] **Step 1: Add PrismaClient to Express Request type**

In `avy-erp-backend/src/shared/types/index.ts`, add the import at the top and update the Request interface:

```typescript
import type { PrismaClient } from '@prisma/client';
```

Inside the `declare global` → `namespace Express` → `interface Request`, add after `tenant?`:

```typescript
      prisma?: PrismaClient; // Tenant-scoped Prisma client from LRU cache
```

Also add `slug` to the tenant type:

```typescript
      tenant?: {
        id: string;
        schemaName: string;
        slug?: string;
        companyId: string;
        databaseUrl: string;
        status?: string;
      };
```

- [ ] **Step 2: Rewrite tenant.middleware.ts**

Replace the entire content of `avy-erp-backend/src/middleware/tenant.middleware.ts`:

```typescript
import { Request, Response, NextFunction } from 'express';
import { cacheRedis } from '../config/redis';
import { createTenantCacheKey } from '../shared/utils';
import { AuthError } from '../shared/errors';
import { ApiError } from '../shared/errors/api-error';
import { logger } from '../config/logger';
import { env } from '../config/env';
import { tenantConnectionManager } from '../config/tenant-connection-manager';
import { platformPrisma } from '../config/database';

const RESERVED_SLUGS = new Set([
  'admin', 'www', 'api', 'app', 'staging', 'dev', 'test', 'demo',
  'mail', 'ftp', 'cdn', 'static', 'assets', 'docs', 'help',
  'support', 'status', 'blog',
]);

export function tenantMiddleware() {
  return async (req: Request, _res: Response, next: NextFunction): Promise<void> => {
    try {
      const tenantId = extractTenantFromRequest(req);

      if (!tenantId) {
        return next();
      }

      // Get tenant details from cache or database
      const tenantKey = createTenantCacheKey(tenantId);
      let tenantDataStr = await cacheRedis.get(tenantKey);

      if (!tenantDataStr) {
        // Fetch from database
        const dbTenant = await platformPrisma.tenant.findUnique({
          where: { id: tenantId },
          select: {
            id: true,
            schemaName: true,
            slug: true,
            companyId: true,
            status: true,
            dbStrategy: true,
            databaseUrl: true,
          },
        });

        if (!dbTenant) {
          // Try lookup by slug
          const bySlug = await platformPrisma.tenant.findUnique({
            where: { slug: tenantId },
            select: {
              id: true,
              schemaName: true,
              slug: true,
              companyId: true,
              status: true,
              dbStrategy: true,
              databaseUrl: true,
            },
          });

          if (!bySlug) {
            throw AuthError.tenantNotFound();
          }

          tenantDataStr = JSON.stringify({
            id: bySlug.id,
            schemaName: bySlug.schemaName,
            slug: bySlug.slug,
            companyId: bySlug.companyId,
            databaseUrl: bySlug.databaseUrl || env.DATABASE_URL_TEMPLATE.replace('{schema}', bySlug.schemaName),
            status: bySlug.status.toLowerCase(),
            dbStrategy: bySlug.dbStrategy,
          });
        } else {
          tenantDataStr = JSON.stringify({
            id: dbTenant.id,
            schemaName: dbTenant.schemaName,
            slug: dbTenant.slug,
            companyId: dbTenant.companyId,
            databaseUrl: dbTenant.databaseUrl || env.DATABASE_URL_TEMPLATE.replace('{schema}', dbTenant.schemaName),
            status: dbTenant.status.toLowerCase(),
            dbStrategy: dbTenant.dbStrategy,
          });
        }

        // Cache for 24 hours
        await cacheRedis.setex(tenantKey, 86400, tenantDataStr);
      }

      const tenant = JSON.parse(tenantDataStr);

      // Tenant status blocking
      if (tenant.status === 'suspended') {
        throw ApiError.forbidden('This company account has been suspended. Contact support.');
      }
      if (tenant.status === 'cancelled' || tenant.status === 'expired') {
        throw ApiError.forbidden('This company account is inactive.');
      }

      // Attach tenant to request
      req.tenant = tenant;

      // Attach tenant-scoped Prisma client
      req.prisma = tenantConnectionManager.getClient({
        schemaName: tenant.schemaName,
        dbStrategy: tenant.dbStrategy,
        databaseUrl: tenant.databaseUrl,
      });

      // Audit log for tenant resolution
      logger.debug('Tenant resolved', {
        hostname: req.hostname,
        tenantId: tenant.id,
        slug: tenant.slug,
        method: req.headers['x-tenant-id'] ? 'header' : req.user?.tenantId ? 'jwt' : 'subdomain',
      });

      next();
    } catch (error) {
      next(error);
    }
  };
}

function extractTenantFromRequest(req: Request): string | null {
  // 1. Custom header (X-Tenant-ID)
  const tenantHeader = req.headers['x-tenant-id'] as string;
  if (tenantHeader) return tenantHeader;

  // 2. Subdomain (e.g., company1.avyren.in → "company1")
  const host = req.headers.host?.split(':')[0];
  if (host) {
    const isIP = /^(\d{1,3}\.){3}\d{1,3}$/.test(host) || host === 'localhost';
    if (!isIP) {
      const mainDomain = env.MAIN_DOMAIN; // e.g., "avyren.in"
      if (host !== mainDomain && host.endsWith(`.${mainDomain}`)) {
        const slug = host.replace(`.${mainDomain}`, '');
        if (slug && !RESERVED_SLUGS.has(slug)) {
          return slug; // Will be resolved by slug in the DB lookup
        }
      }
    }
  }

  // 3. Query parameter
  const tenantQuery = req.query.tenantId as string;
  if (tenantQuery) return tenantQuery;

  // 4. Path parameter
  const tenantPath = req.params.tenantId;
  if (tenantPath) return tenantPath;

  // 5. User context from JWT
  if (req.user?.tenantId) return req.user.tenantId;

  return null;
}

export function requireTenant() {
  return (req: Request, _res: Response, next: NextFunction): void => {
    if (!req.tenant) {
      throw AuthError.tenantNotFound();
    }
    next();
  };
}

export function validateTenantAccess() {
  return (req: Request, _res: Response, next: NextFunction): void => {
    // Cross-tenant security: JWT tenantId must match resolved tenant
    if (req.user && req.tenant && req.user.tenantId !== req.tenant.id) {
      throw ApiError.forbidden('Access denied: tenant mismatch');
    }
    next();
  };
}

export { RESERVED_SLUGS };
```

- [ ] **Step 3: Commit**

```bash
git add avy-erp-backend/src/middleware/tenant.middleware.ts avy-erp-backend/src/shared/types/index.ts
git commit -m "$(cat <<'EOF'
feat: upgrade tenant middleware with DB lookup, status blocking, req.prisma, audit logging

Replaces mock tenant data with real DB lookups (by ID or slug). Adds
tenant status blocking (suspended/cancelled/expired), attaches LRU-cached
PrismaClient as req.prisma, and logs tenant resolution for debugging.

Co-Authored-By: Claude Opus 4.6 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Task 5: Dynamic CORS

**Files:**
- Modify: `avy-erp-backend/src/app/app.ts`

- [ ] **Step 1: Replace CORS origin logic with dynamic subdomain validation**

In `avy-erp-backend/src/app/app.ts`, replace the entire CORS section (lines 46–93) with:

```typescript
// CORS configuration — dynamic origin validation for wildcard subdomains
if (env.ENABLE_CORS) {
  const mainDomain = env.MAIN_DOMAIN; // e.g., "avyren.in"
  const mainOrigin = `https://${mainDomain}`;
  const subdomainPattern = new RegExp(`^https:\\/\\/[\\w-]+\\.${mainDomain.replace(/\./g, '\\.')}$`);

  // Additional origins from env (for development)
  const extraOrigins = env.CORS_ALLOWED_ORIGINS
    .split(',')
    .map((o) => o.trim())
    .filter(Boolean);
  const allowAll = extraOrigins.includes('*');

  app.use(cors({
    origin: (origin, callback) => {
      // Allow requests with no origin (mobile apps, Postman, etc.)
      if (!origin) return callback(null, true);

      // Development wildcard
      if (allowAll) return callback(null, true);

      // Main domain
      if (origin === mainOrigin) return callback(null, true);

      // Wildcard subdomains (e.g., https://company1.avyren.in)
      if (subdomainPattern.test(origin)) return callback(null, true);

      // Extra configured origins (dev/staging)
      if (extraOrigins.includes(origin)) return callback(null, true);

      // Development mode: allow all when no origins configured
      if (env.NODE_ENV === 'development' && extraOrigins.length === 0) {
        return callback(null, true);
      }

      return callback(new Error('Not allowed by CORS'), false);
    },
    credentials: true,
    methods: ['GET', 'POST', 'PUT', 'DELETE', 'PATCH', 'OPTIONS'],
    allowedHeaders: [
      'Content-Type',
      'Authorization',
      'X-Tenant-ID',
      'X-Requested-With',
      'X-Device-Info',
    ],
  }));
}
```

- [ ] **Step 2: Commit**

```bash
git add avy-erp-backend/src/app/app.ts
git commit -m "$(cat <<'EOF'
feat: dynamic CORS validation for wildcard tenant subdomains

Validates origin against *.avyren.in pattern and main domain.
Rejects unknown origins in production. Falls back to env-configured
origins for development.

Co-Authored-By: Claude Opus 4.6 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Task 6: Registration Email Templates

**Files:**
- Create: `avy-erp-backend/src/infrastructure/email/registration-emails.ts`

- [ ] **Step 1: Create registration email templates**

Create `avy-erp-backend/src/infrastructure/email/registration-emails.ts`:

```typescript
import { env } from '../../config/env';
import { sendEmail } from './email.service';
import { logger } from '../../config/logger';

/**
 * Notify super admin of a new company registration request.
 */
export async function sendRegistrationNotification(data: {
  companyName: string;
  adminName: string;
  email: string;
  phone: string;
  requestId: string;
}): Promise<void> {
  const adminEmail = env.SUPER_ADMIN_EMAIL;
  if (!adminEmail) {
    logger.warn('SUPER_ADMIN_EMAIL not configured, skipping registration notification');
    return;
  }

  const subject = `${env.APP_NAME} — New Company Registration: ${data.companyName}`;
  const html = `
    <div style="font-family: Arial, sans-serif; max-width: 520px; margin: 0 auto; padding: 32px;">
      <h2 style="color: #4A3AFF; margin-bottom: 24px;">${env.APP_NAME}</h2>
      <p>A new company registration request has been submitted.</p>
      <div style="background: #F8F7FF; border-radius: 8px; padding: 20px; margin: 20px 0;">
        <p style="margin: 4px 0;"><strong>Company:</strong> ${data.companyName}</p>
        <p style="margin: 4px 0;"><strong>Contact:</strong> ${data.adminName}</p>
        <p style="margin: 4px 0;"><strong>Email:</strong> ${data.email}</p>
        <p style="margin: 4px 0;"><strong>Phone:</strong> ${data.phone}</p>
      </div>
      <p>Review this request in the admin panel:</p>
      <a href="https://admin.${env.MAIN_DOMAIN}/app/registration-requests/${data.requestId}"
         style="display:inline-block;background:#4A3AFF;color:#fff;padding:12px 24px;border-radius:8px;text-decoration:none;font-weight:bold;">
        Review Request
      </a>
      <hr style="border: none; border-top: 1px solid #eee; margin: 24px 0;" />
      <p style="color: #999; font-size: 12px;">&copy; ${new Date().getFullYear()} Avyren Technologies. All rights reserved.</p>
    </div>
  `;

  await sendEmail(adminEmail, subject, html);
}

/**
 * Notify company admin that their registration was approved.
 */
export async function sendRegistrationApproved(data: {
  email: string;
  adminName: string;
  companyName: string;
  slug: string;
  tempPassword: string;
}): Promise<void> {
  const subject = `Welcome to ${env.APP_NAME} — Your Account is Ready`;
  const html = `
    <div style="font-family: Arial, sans-serif; max-width: 520px; margin: 0 auto; padding: 32px;">
      <h2 style="color: #4A3AFF; margin-bottom: 24px;">${env.APP_NAME}</h2>
      <p>Hi ${data.adminName},</p>
      <p>Your company <strong>"${data.companyName}"</strong> has been approved!</p>
      <div style="background: #F0FDF4; border-radius: 8px; padding: 20px; margin: 20px 0;">
        <p style="margin: 4px 0;"><strong>Your ERP URL:</strong></p>
        <a href="https://${data.slug}.${env.MAIN_DOMAIN}" style="color: #4A3AFF; font-size: 16px;">
          https://${data.slug}.${env.MAIN_DOMAIN}
        </a>
        <p style="margin: 12px 0 4px 0;"><strong>Login Email:</strong> ${data.email}</p>
        <p style="margin: 4px 0;"><strong>Temporary Password:</strong> ${data.tempPassword}</p>
      </div>
      <p style="color: #666; font-size: 14px;">Please change your password after first login.</p>
      <hr style="border: none; border-top: 1px solid #eee; margin: 24px 0;" />
      <p style="color: #999; font-size: 12px;">&copy; ${new Date().getFullYear()} Avyren Technologies. All rights reserved.</p>
    </div>
  `;

  await sendEmail(data.email, subject, html);
}

/**
 * Notify applicant that their registration was rejected.
 */
export async function sendRegistrationRejected(data: {
  email: string;
  adminName: string;
  companyName: string;
  rejectionReason: string;
}): Promise<void> {
  const subject = `${env.APP_NAME} — Registration Update`;
  const html = `
    <div style="font-family: Arial, sans-serif; max-width: 520px; margin: 0 auto; padding: 32px;">
      <h2 style="color: #4A3AFF; margin-bottom: 24px;">${env.APP_NAME}</h2>
      <p>Hi ${data.adminName},</p>
      <p>Thank you for your interest in ${env.APP_NAME}.</p>
      <p>Unfortunately, your registration for <strong>"${data.companyName}"</strong> could not be approved at this time.</p>
      <div style="background: #FEF2F2; border-radius: 8px; padding: 20px; margin: 20px 0;">
        <p style="margin: 4px 0;"><strong>Reason:</strong> ${data.rejectionReason}</p>
      </div>
      <p style="color: #666; font-size: 14px;">If you have questions, contact <a href="mailto:support@avyren.in">support@avyren.in</a></p>
      <hr style="border: none; border-top: 1px solid #eee; margin: 24px 0;" />
      <p style="color: #999; font-size: 12px;">&copy; ${new Date().getFullYear()} Avyren Technologies. All rights reserved.</p>
    </div>
  `;

  await sendEmail(data.email, subject, html);
}
```

- [ ] **Step 2: Commit**

```bash
git add avy-erp-backend/src/infrastructure/email/registration-emails.ts
git commit -m "$(cat <<'EOF'
feat: add registration email templates (notification, approved, rejected)

Co-Authored-By: Claude Opus 4.6 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Task 7: Registration Module — Validators, Service, Controller, Routes

**Files:**
- Create: `avy-erp-backend/src/core/registration/registration.validators.ts`
- Create: `avy-erp-backend/src/core/registration/registration.service.ts`
- Create: `avy-erp-backend/src/core/registration/registration.controller.ts`
- Create: `avy-erp-backend/src/core/registration/registration.routes.ts`

- [ ] **Step 1: Create validators**

Create `avy-erp-backend/src/core/registration/registration.validators.ts`:

```typescript
import { z } from 'zod';

export const registerCompanySchema = z.object({
  companyName: z.string().min(2, 'Company name must be at least 2 characters').max(200),
  adminName: z.string().min(2, 'Name must be at least 2 characters').max(100),
  email: z.string().email('Please enter a valid email'),
  phone: z.string().min(10, 'Please enter a valid phone number').max(15),
});

export const updateRegistrationSchema = z.object({
  status: z.enum(['APPROVED', 'REJECTED']),
  rejectionReason: z.string().optional(),
}).refine(
  (data) => data.status !== 'REJECTED' || (data.rejectionReason && data.rejectionReason.length > 0),
  { message: 'Rejection reason is required when rejecting', path: ['rejectionReason'] }
);

export type RegisterCompanyInput = z.infer<typeof registerCompanySchema>;
export type UpdateRegistrationInput = z.infer<typeof updateRegistrationSchema>;
```

- [ ] **Step 2: Create service**

Create `avy-erp-backend/src/core/registration/registration.service.ts`:

```typescript
import { platformPrisma } from '../../config/database';
import { ApiError } from '../../shared/errors/api-error';
import { logger } from '../../config/logger';
import {
  sendRegistrationNotification,
  sendRegistrationRejected,
} from '../../infrastructure/email/registration-emails';
import type { RegisterCompanyInput, UpdateRegistrationInput } from './registration.validators';

class RegistrationService {
  async submitRegistration(data: RegisterCompanyInput) {
    // Check for duplicate email in both registration requests and existing users
    const [existingRequest, existingUser] = await Promise.all([
      platformPrisma.companyRegistrationRequest.findUnique({
        where: { email: data.email },
      }),
      platformPrisma.user.findUnique({
        where: { email: data.email },
      }),
    ]);

    if (existingRequest) {
      throw ApiError.conflict('A registration with this email already exists');
    }
    if (existingUser) {
      throw ApiError.conflict('An account with this email already exists');
    }

    // Create registration request + support ticket
    const request = await platformPrisma.$transaction(async (tx) => {
      const registration = await tx.companyRegistrationRequest.create({
        data: {
          companyName: data.companyName,
          adminName: data.adminName,
          email: data.email,
          phone: data.phone,
          status: 'PENDING',
        },
      });

      // Create a support ticket for tracking
      const ticket = await tx.supportTicket.create({
        data: {
          subject: `Company Registration: ${data.companyName}`,
          description: `New company registration request from ${data.adminName} (${data.email}). Phone: ${data.phone}`,
          type: 'COMPANY_REGISTRATION',
          priority: 'MEDIUM',
          status: 'OPEN',
        },
      });

      // Link ticket to registration
      await tx.companyRegistrationRequest.update({
        where: { id: registration.id },
        data: { ticketId: ticket.id },
      });

      return { ...registration, ticketId: ticket.id };
    });

    // Send email notification to super admin (non-blocking)
    sendRegistrationNotification({
      companyName: data.companyName,
      adminName: data.adminName,
      email: data.email,
      phone: data.phone,
      requestId: request.id,
    }).catch((err) => {
      logger.error('Failed to send registration notification email:', err);
    });

    return request;
  }

  async listRegistrations(params?: { status?: string; page?: number; limit?: number }) {
    const page = params?.page || 1;
    const limit = params?.limit || 20;
    const skip = (page - 1) * limit;

    const where = params?.status ? { status: params.status as any } : {};

    const [data, total] = await Promise.all([
      platformPrisma.companyRegistrationRequest.findMany({
        where,
        orderBy: { createdAt: 'desc' },
        skip,
        take: limit,
        include: { ticket: { select: { id: true, status: true } } },
      }),
      platformPrisma.companyRegistrationRequest.count({ where }),
    ]);

    return { data, meta: { page, limit, total, totalPages: Math.ceil(total / limit) } };
  }

  async getRegistration(id: string) {
    const request = await platformPrisma.companyRegistrationRequest.findUnique({
      where: { id },
      include: { ticket: true },
    });

    if (!request) {
      throw ApiError.notFound('Registration request not found');
    }

    return request;
  }

  async updateRegistration(id: string, data: UpdateRegistrationInput) {
    const request = await platformPrisma.companyRegistrationRequest.findUnique({
      where: { id },
    });

    if (!request) {
      throw ApiError.notFound('Registration request not found');
    }

    if (request.status !== 'PENDING') {
      throw ApiError.badRequest('Registration request has already been processed');
    }

    const updated = await platformPrisma.companyRegistrationRequest.update({
      where: { id },
      data: {
        status: data.status,
        rejectionReason: data.status === 'REJECTED' ? data.rejectionReason : null,
      },
    });

    // If rejected, send email
    if (data.status === 'REJECTED') {
      sendRegistrationRejected({
        email: request.email,
        adminName: request.adminName,
        companyName: request.companyName,
        rejectionReason: data.rejectionReason || 'No reason provided',
      }).catch((err) => {
        logger.error('Failed to send rejection email:', err);
      });
    }

    // If approved, the super admin proceeds to the tenant onboarding wizard
    // with the registration data pre-filled. The approval email is sent
    // after the onboarding wizard completes (in tenant.service.ts).

    return updated;
  }
}

export const registrationService = new RegistrationService();
```

- [ ] **Step 3: Create controller**

Create `avy-erp-backend/src/core/registration/registration.controller.ts`:

```typescript
import { Request, Response } from 'express';
import { asyncHandler } from '../../middleware/error.middleware';
import { createSuccessResponse, createPaginatedResponse } from '../../shared/utils';
import { registrationService } from './registration.service';
import { registerCompanySchema, updateRegistrationSchema } from './registration.validators';
import { ApiError } from '../../shared/errors/api-error';

class RegistrationController {
  /** POST /auth/register-company (public, rate limited) */
  submitRegistration = asyncHandler(async (req: Request, res: Response) => {
    const parsed = registerCompanySchema.safeParse(req.body);
    if (!parsed.success) {
      throw ApiError.badRequest(parsed.error.errors.map((e) => e.message).join(', '));
    }
    const result = await registrationService.submitRegistration(parsed.data);
    res.status(201).json(
      createSuccessResponse(
        { id: result.id },
        'Registration submitted successfully. We will review your request and get back to you shortly.'
      )
    );
  });

  /** GET /platform/registration-requests (super admin) */
  listRegistrations = asyncHandler(async (req: Request, res: Response) => {
    const { status, page, limit } = req.query;
    const result = await registrationService.listRegistrations({
      status: status as string,
      page: page ? Number(page) : undefined,
      limit: limit ? Number(limit) : undefined,
    });
    res.json(createPaginatedResponse(result.data, result.meta.page, result.meta.limit, result.meta.total));
  });

  /** GET /platform/registration-requests/:id (super admin) */
  getRegistration = asyncHandler(async (req: Request, res: Response) => {
    const result = await registrationService.getRegistration(req.params.id);
    res.json(createSuccessResponse(result));
  });

  /** PATCH /platform/registration-requests/:id (super admin) */
  updateRegistration = asyncHandler(async (req: Request, res: Response) => {
    const parsed = updateRegistrationSchema.safeParse(req.body);
    if (!parsed.success) {
      throw ApiError.badRequest(parsed.error.errors.map((e) => e.message).join(', '));
    }
    const result = await registrationService.updateRegistration(req.params.id, parsed.data);
    res.json(createSuccessResponse(result, `Registration ${parsed.data.status.toLowerCase()}`));
  });
}

export const registrationController = new RegistrationController();
```

- [ ] **Step 4: Create routes**

Create `avy-erp-backend/src/core/registration/registration.routes.ts`:

```typescript
import { Router } from 'express';
import { registrationController } from './registration.controller';

// Public route (mounted under /auth)
export const registrationPublicRoutes = Router();
registrationPublicRoutes.post('/register-company', registrationController.submitRegistration);

// Platform routes (mounted under /platform, requires super-admin auth)
export const registrationPlatformRoutes = Router();
registrationPlatformRoutes.get('/', registrationController.listRegistrations);
registrationPlatformRoutes.get('/:id', registrationController.getRegistration);
registrationPlatformRoutes.patch('/:id', registrationController.updateRegistration);
```

- [ ] **Step 5: Commit**

```bash
git add avy-erp-backend/src/core/registration/
git commit -m "$(cat <<'EOF'
feat: add company registration module (validators, service, controller, routes)

Public endpoint for registration submission with duplicate checking,
support ticket creation, and email notification. Platform endpoints
for super admin to list, view, approve, or reject registrations.

Co-Authored-By: Claude Opus 4.6 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Task 8: Tenant Branding Endpoint

**Files:**
- Modify: `avy-erp-backend/src/core/auth/auth.controller.ts`
- Modify: `avy-erp-backend/src/core/auth/auth.routes.ts`

- [ ] **Step 1: Add tenantBranding handler to auth controller**

In `avy-erp-backend/src/core/auth/auth.controller.ts`, add this method to the controller class:

```typescript
  /** GET /auth/tenant-branding?slug=<slug> (public, rate limited) */
  tenantBranding = asyncHandler(async (req: Request, res: Response) => {
    const slug = req.query.slug as string;
    if (!slug) {
      return res.json(createSuccessResponse({ exists: false }));
    }

    const tenant = await platformPrisma.tenant.findUnique({
      where: { slug },
      select: {
        id: true,
        status: true,
        company: {
          select: {
            displayName: true,
            name: true,
            logoUrl: true,
          },
        },
      },
    });

    if (!tenant || tenant.status === 'CANCELLED') {
      return res.json(createSuccessResponse({ exists: false }));
    }

    res.json(createSuccessResponse({
      exists: true,
      companyName: tenant.company.displayName || tenant.company.name,
      logoUrl: tenant.company.logoUrl,
    }));
  });
```

Make sure `platformPrisma` and `createSuccessResponse` are imported at the top.

- [ ] **Step 2: Add route in auth.routes.ts**

In `avy-erp-backend/src/core/auth/auth.routes.ts`, add before the `// Protected routes` section:

```typescript
// Public tenant branding (for subdomain login pages)
router.get('/tenant-branding', authController.tenantBranding);
```

- [ ] **Step 3: Commit**

```bash
git add avy-erp-backend/src/core/auth/auth.controller.ts avy-erp-backend/src/core/auth/auth.routes.ts
git commit -m "$(cat <<'EOF'
feat: add public tenant branding endpoint for subdomain login pages

GET /auth/tenant-branding?slug=<slug> returns company name and logo
for valid tenants, or { exists: false } for invalid slugs (prevents
slug enumeration).

Co-Authored-By: Claude Opus 4.6 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Task 9: Mount Registration Routes + Rate Limiting

**Files:**
- Modify: `avy-erp-backend/src/app/routes.ts`

- [ ] **Step 1: Import and mount registration routes**

In `avy-erp-backend/src/app/routes.ts`, add the import at the top:

```typescript
import { registrationPublicRoutes, registrationPlatformRoutes } from '../core/registration/registration.routes';
```

Mount the public route under `/auth` — add after the existing `router.use('/auth', authRoutes);` line:

```typescript
router.use('/auth', registrationPublicRoutes);
```

Mount the platform route — add after the existing platform routes (after `router.use('/platform/support', supportPlatformRoutes);`):

```typescript
router.use('/platform/registration-requests', registrationPlatformRoutes);
```

- [ ] **Step 2: Add rate limiting for registration and branding endpoints**

In `avy-erp-backend/src/app/app.ts`, add rate limiters for the new public endpoints. Add after the existing rate limit configuration section:

```typescript
import rateLimit from 'express-rate-limit';

// Rate limit: company registration — 3 per IP per hour
app.use('/api/v1/auth/register-company', rateLimit({
  windowMs: 60 * 60 * 1000, // 1 hour
  max: 3,
  message: { success: false, message: 'Too many registration attempts. Please try again later.' },
  standardHeaders: true,
  legacyHeaders: false,
}));

// Rate limit: tenant branding — 30 per IP per minute
app.use('/api/v1/auth/tenant-branding', rateLimit({
  windowMs: 60 * 1000, // 1 minute
  max: 30,
  message: { success: false, message: 'Too many requests. Please try again later.' },
  standardHeaders: true,
  legacyHeaders: false,
}));
```

- [ ] **Step 3: Commit**

```bash
git add avy-erp-backend/src/app/routes.ts avy-erp-backend/src/app/app.ts
git commit -m "$(cat <<'EOF'
feat: mount registration routes and add rate limiting for public endpoints

Co-Authored-By: Claude Opus 4.6 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Task 10: Tenant Onboarding — Add Slug Field

**Files:**
- Modify: `avy-erp-backend/src/core/tenant/tenant.validators.ts`
- Modify: `avy-erp-backend/src/core/tenant/tenant.service.ts`

- [ ] **Step 1: Add slug validation to tenant validators**

In `avy-erp-backend/src/core/tenant/tenant.validators.ts`, add the slug validation. Import `RESERVED_SLUGS` from the middleware and add a slug field to the onboarding schema:

```typescript
import { RESERVED_SLUGS } from '../../middleware/tenant.middleware';

// Add this to the identity step or main onboarding schema:
const slugSchema = z.string()
  .min(3, 'Slug must be at least 3 characters')
  .max(50, 'Slug must be at most 50 characters')
  .regex(/^[a-z0-9][a-z0-9-]*[a-z0-9]$/, 'Slug must be lowercase, alphanumeric with hyphens only')
  .refine((val) => !RESERVED_SLUGS.has(val), 'This slug is reserved and cannot be used');
```

Add `slug` to the onboarding payload schema (likely in `identitySchema` or the top-level `onboardTenantSchema`).

- [ ] **Step 2: Update tenant service to use slug**

In `avy-erp-backend/src/core/tenant/tenant.service.ts`, update the `onboardTenant` method to:

1. Accept `slug` from the payload
2. Generate `schemaName` from slug: `tenant_${slug.replace(/-/g, '_')}`
3. Store `slug` on the Tenant record

Find the section where `Tenant` is created in the transaction and add the `slug` field:

```typescript
const tenant = await tx.tenant.create({
  data: {
    companyId: company.id,
    schemaName: `tenant_${slug.replace(/-/g, '_')}`,
    slug: slug,
    status: mapWizardStatusToTenantStatus(payload.identity?.wizardStatus),
  },
});
```

- [ ] **Step 3: Commit**

```bash
git add avy-erp-backend/src/core/tenant/tenant.validators.ts avy-erp-backend/src/core/tenant/tenant.service.ts
git commit -m "$(cat <<'EOF'
feat: add slug field to tenant onboarding wizard

Slug is validated (3-50 chars, lowercase alphanumeric + hyphens, not
reserved) and used to generate the PostgreSQL schema name.

Co-Authored-By: Claude Opus 4.6 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Task 11: Tenant Schema Migration CLI

**Files:**
- Create: `avy-erp-backend/scripts/migrate-tenants.ts`
- Modify: `avy-erp-backend/package.json`

- [ ] **Step 1: Create the migration script**

Create `avy-erp-backend/scripts/migrate-tenants.ts`:

```typescript
import { PrismaClient } from '@prisma/client';
import { execSync } from 'child_process';
import { resolve } from 'path';

const platformPrisma = new PrismaClient();

async function migrateTenants() {
  const targetSlug = process.argv.find((arg) => arg.startsWith('--tenant='))?.split('=')[1];

  console.log('🔄 Fetching active tenants...');

  const where: any = { status: { in: ['ACTIVE', 'TRIAL'] } };
  if (targetSlug) {
    where.slug = targetSlug;
  }

  const tenants = await platformPrisma.tenant.findMany({
    where,
    select: { id: true, slug: true, schemaName: true },
    orderBy: { createdAt: 'asc' },
  });

  console.log(`📋 Found ${tenants.length} tenant(s) to migrate\n`);

  let succeeded = 0;
  let failed = 0;
  const failures: { slug: string; error: string }[] = [];

  for (const tenant of tenants) {
    const label = `[${tenant.slug}] (schema: ${tenant.schemaName})`;
    try {
      console.log(`⏳ Migrating ${label}...`);

      // Build connection URL for this tenant's schema
      const baseUrl = process.env.DATABASE_URL!;
      const tenantUrl = baseUrl.replace('schema=public', `schema=${tenant.schemaName}`);

      // Run prisma migrate deploy with the tenant's schema
      execSync(
        `npx prisma migrate deploy`,
        {
          cwd: resolve(__dirname, '..'),
          env: { ...process.env, DATABASE_URL: tenantUrl },
          stdio: 'pipe',
        }
      );

      console.log(`✅ ${label} — migrated successfully`);
      succeeded++;
    } catch (err: any) {
      const errorMsg = err.stderr?.toString() || err.message || 'Unknown error';
      console.error(`❌ ${label} — FAILED: ${errorMsg}`);
      failures.push({ slug: tenant.slug, error: errorMsg });
      failed++;
    }
  }

  console.log('\n' + '='.repeat(50));
  console.log(`📊 Results: ${succeeded} succeeded, ${failed} failed, ${tenants.length} total`);

  if (failures.length > 0) {
    console.log('\n❌ Failed tenants:');
    for (const f of failures) {
      console.log(`  - ${f.slug}: ${f.error.slice(0, 100)}`);
    }
    console.log('\nRetry individual tenants with: pnpm db:migrate-tenants --tenant=<slug>');
  }

  await platformPrisma.$disconnect();
  process.exit(failed > 0 ? 1 : 0);
}

migrateTenants().catch((err) => {
  console.error('Fatal error:', err);
  process.exit(1);
});
```

- [ ] **Step 2: Add npm script**

In `avy-erp-backend/package.json`, add to `scripts`:

```json
"db:migrate-tenants": "node scripts/merge-prisma.js && prisma migrate dev && npx tsx scripts/migrate-tenants.ts"
```

- [ ] **Step 3: Commit**

```bash
git add avy-erp-backend/scripts/migrate-tenants.ts avy-erp-backend/package.json
git commit -m "$(cat <<'EOF'
feat: add tenant schema migration CLI (pnpm db:migrate-tenants)

Iterates all active/trial tenants and applies pending Prisma migrations
to each schema. Supports --tenant=<slug> for individual retries.
Logs success/failure per tenant with summary.

Co-Authored-By: Claude Opus 4.6 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Task 12: PgBouncer Docker Setup

**Files:**
- Modify: `avy-erp-backend/docker-compose.yml`

- [ ] **Step 1: Add PgBouncer service to docker-compose.yml**

In `avy-erp-backend/docker-compose.yml`, add the pgbouncer service after the `redis` service and before the `app` service:

```yaml
  # ---------- PgBouncer (Connection Pooler) ----------
  pgbouncer:
    image: edoburu/pgbouncer:latest
    container_name: avy-erp-pgbouncer
    restart: unless-stopped
    depends_on:
      postgres:
        condition: service_healthy
    environment:
      DATABASE_URL: "postgresql://${POSTGRES_USER:-avy_admin}:${POSTGRES_PASSWORD}@postgres:5432/${POSTGRES_DB:-avy_erp}"
      POOL_MODE: transaction
      DEFAULT_POOL_SIZE: 20
      MAX_CLIENT_CONN: 100
      SERVER_RESET_QUERY: "DISCARD ALL"
      ADMIN_USERS: "${POSTGRES_USER:-avy_admin}"
    ports:
      - "${PGBOUNCER_PORT:-6432}:6432"
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -h localhost -p 6432 -U ${POSTGRES_USER:-avy_admin}"]
      interval: 10s
      timeout: 5s
      retries: 5
      start_period: 10s
    networks:
      - avy-network
    deploy:
      resources:
        limits:
          memory: 128m
```

- [ ] **Step 2: Update app service DATABASE_URL to route through PgBouncer**

In the `app` service's environment section, update the DATABASE_URL entries to go through PgBouncer:

```yaml
      # Database — through PgBouncer for connection pooling
      DATABASE_URL: "postgresql://${POSTGRES_USER:-avy_admin}:${POSTGRES_PASSWORD}@pgbouncer:6432/${POSTGRES_DB:-avy_erp}?schema=public&pgbouncer=true"
      DATABASE_URL_TEMPLATE: "postgresql://${POSTGRES_USER:-avy_admin}:${POSTGRES_PASSWORD}@pgbouncer:6432/${POSTGRES_DB:-avy_erp}?schema={schema}&pgbouncer=true&connection_limit=5"
```

Also add the new env vars:

```yaml
      # Multi-tenancy
      MAIN_DOMAIN: ${MAIN_DOMAIN:-avyren.in}
      TENANT_CLIENT_CACHE_SIZE: ${TENANT_CLIENT_CACHE_SIZE:-50}
      SUPER_ADMIN_EMAIL: ${SUPER_ADMIN_EMAIL:-}
```

Add `pgbouncer` to the `app` service's `depends_on`:

```yaml
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
      pgbouncer:
        condition: service_healthy
```

- [ ] **Step 3: Commit**

```bash
git add avy-erp-backend/docker-compose.yml
git commit -m "$(cat <<'EOF'
feat: add PgBouncer to docker-compose for connection pooling

Transaction mode pooling with 20 default pool size and 100 max client
connections. Backend DATABASE_URL routed through PgBouncer on port 6432.

Co-Authored-By: Claude Opus 4.6 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Task 13: Web App — Tenant Detection Utility

**Files:**
- Create: `web-system-app/src/lib/tenant.ts`

- [ ] **Step 1: Create tenant detection module**

Create `web-system-app/src/lib/tenant.ts`:

```typescript
export type AppMode = 'main' | 'admin' | 'tenant';

export interface TenantContext {
  mode: AppMode;
  slug: string | null;
}

const MAIN_DOMAIN = import.meta.env.VITE_MAIN_DOMAIN || 'avyren.in';

const RESERVED_SLUGS = new Set([
  'admin', 'www', 'api', 'app', 'staging', 'dev', 'test', 'demo',
  'mail', 'ftp', 'cdn', 'static', 'assets', 'docs', 'help',
  'support', 'status', 'blog',
]);

export function detectTenant(): TenantContext {
  const hostname = window.location.hostname;

  // Development: treat localhost as main domain
  if (hostname === 'localhost' || hostname === '127.0.0.1') {
    // Check for dev override via query param: ?tenant=slug
    const params = new URLSearchParams(window.location.search);
    const devSlug = params.get('tenant');
    if (devSlug === 'admin') return { mode: 'admin', slug: null };
    if (devSlug) return { mode: 'tenant', slug: devSlug };
    return { mode: 'main', slug: null };
  }

  // Main domain (no subdomain)
  if (hostname === MAIN_DOMAIN) {
    return { mode: 'main', slug: null };
  }

  // Check if it's a subdomain of the main domain
  if (hostname.endsWith(`.${MAIN_DOMAIN}`)) {
    const slug = hostname.replace(`.${MAIN_DOMAIN}`, '');

    // Super admin subdomain
    if (slug === 'admin') {
      return { mode: 'admin', slug: null };
    }

    // Reserved slugs — treat as invalid
    if (RESERVED_SLUGS.has(slug)) {
      return { mode: 'main', slug: null };
    }

    // Tenant subdomain
    return { mode: 'tenant', slug };
  }

  // Unknown domain — fallback to main
  return { mode: 'main', slug: null };
}

// Singleton for the current session
let cachedContext: TenantContext | null = null;

export function getTenantContext(): TenantContext {
  if (!cachedContext) {
    cachedContext = detectTenant();
  }
  return cachedContext;
}
```

- [ ] **Step 2: Add VITE_MAIN_DOMAIN to .env**

In `web-system-app/.env`, add:

```env
VITE_MAIN_DOMAIN=avyren.in
```

- [ ] **Step 3: Commit**

```bash
git add web-system-app/src/lib/tenant.ts web-system-app/.env
git commit -m "$(cat <<'EOF'
feat: add tenant detection utility for subdomain routing

Detects app mode (main/admin/tenant) from hostname. Supports dev
override via ?tenant=slug query param for localhost testing.

Co-Authored-By: Claude Opus 4.6 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Task 14: Web App — Tenant Branding API Hook

**Files:**
- Modify: `web-system-app/src/lib/api/auth.ts`

- [ ] **Step 1: Add tenant branding API function and React Query hook**

In `web-system-app/src/lib/api/auth.ts`, add:

```typescript
import { useQuery } from '@tanstack/react-query';

export interface TenantBranding {
  exists: boolean;
  companyName?: string;
  logoUrl?: string;
}

export async function fetchTenantBranding(slug: string): Promise<TenantBranding> {
  const response = await client.get(`/auth/tenant-branding`, { params: { slug } });
  return response.data?.data;
}

export function useTenantBranding(slug: string | null) {
  return useQuery({
    queryKey: ['tenant-branding', slug],
    queryFn: () => fetchTenantBranding(slug!),
    enabled: !!slug,
    staleTime: 5 * 60 * 1000, // 5 minutes
    retry: 1,
  });
}
```

- [ ] **Step 2: Commit**

```bash
git add web-system-app/src/lib/api/auth.ts
git commit -m "$(cat <<'EOF'
feat: add tenant branding API hook for subdomain login pages

Co-Authored-By: Claude Opus 4.6 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Task 15: Web App — Registration Form & API

**Files:**
- Create: `web-system-app/src/features/auth/RegisterCompanyScreen.tsx`
- Create: `web-system-app/src/lib/api/registration.ts`

- [ ] **Step 1: Create registration API module**

Create `web-system-app/src/lib/api/registration.ts`:

```typescript
import { useMutation } from '@tanstack/react-query';
import { client } from './client';
import { showSuccess, showApiError } from '@/lib/toast';

interface RegisterCompanyInput {
  companyName: string;
  adminName: string;
  email: string;
  phone: string;
}

async function registerCompany(data: RegisterCompanyInput) {
  const response = await client.post('/auth/register-company', data);
  return response.data;
}

export function useRegisterCompanyMutation() {
  return useMutation({
    mutationFn: registerCompany,
    onSuccess: (data) => {
      showSuccess(data?.message || 'Registration submitted successfully');
    },
    onError: (err) => {
      showApiError(err);
    },
  });
}
```

- [ ] **Step 2: Create RegisterCompanyScreen**

Create `web-system-app/src/features/auth/RegisterCompanyScreen.tsx`:

```typescript
import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { ArrowLeft, Building, User, Mail, Phone, CheckCircle } from "lucide-react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import * as z from "zod";
import { useRegisterCompanyMutation } from "@/lib/api/registration";
import { CustomLoader } from "@/components/ui/CustomLoader";
import { cn } from "@/lib/utils";
import companyLogo from "@/assets/logo/Company-Logo.png";

const registerSchema = z.object({
  companyName: z.string().min(2, "Company name must be at least 2 characters"),
  adminName: z.string().min(2, "Name must be at least 2 characters"),
  email: z.string().email("Please enter a valid email"),
  phone: z.string().min(10, "Please enter a valid phone number"),
});

type RegisterFormValues = z.infer<typeof registerSchema>;

export function RegisterCompanyScreen() {
  const navigate = useNavigate();
  const mutation = useRegisterCompanyMutation();
  const [submitted, setSubmitted] = useState(false);
  const [focusedInput, setFocusedInput] = useState<string | null>(null);

  const { register, handleSubmit, formState: { errors } } = useForm<RegisterFormValues>({
    resolver: zodResolver(registerSchema),
    defaultValues: { companyName: "", adminName: "", email: "", phone: "" },
  });

  const onSubmit = (data: RegisterFormValues) => {
    mutation.mutate(data, {
      onSuccess: () => setSubmitted(true),
    });
  };

  if (submitted) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-primary-50 via-white to-accent-50 dark:from-neutral-950 dark:via-neutral-900 dark:to-neutral-950 p-4">
        <div className="max-w-md w-full text-center space-y-6">
          <div className="w-16 h-16 bg-success-100 dark:bg-success-900/30 rounded-full flex items-center justify-center mx-auto">
            <CheckCircle className="w-8 h-8 text-success-600" />
          </div>
          <h2 className="text-2xl font-bold text-neutral-900 dark:text-white">Registration Submitted!</h2>
          <p className="text-neutral-600 dark:text-neutral-400">
            Thank you for your interest in Avy ERP. We'll review your request and get back to you shortly.
          </p>
          <button
            onClick={() => navigate("/login")}
            className="text-primary-600 hover:text-primary-700 font-semibold"
          >
            Back to Sign In
          </button>
        </div>
      </div>
    );
  }

  const fields = [
    { name: "companyName" as const, label: "Company Name", icon: Building, placeholder: "Enter your company name", type: "text" },
    { name: "adminName" as const, label: "Your Name", icon: User, placeholder: "Enter your full name", type: "text" },
    { name: "email" as const, label: "Email", icon: Mail, placeholder: "Enter your work email", type: "email" },
    { name: "phone" as const, label: "Phone", icon: Phone, placeholder: "Enter your phone number", type: "tel" },
  ];

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-primary-50 via-white to-accent-50 dark:from-neutral-950 dark:via-neutral-900 dark:to-neutral-950 p-4">
      <div className="max-w-md w-full space-y-8">
        {/* Header */}
        <div className="text-center space-y-3">
          <img src={companyLogo} alt="Avy ERP" className="h-10 mx-auto" />
          <h2 className="text-2xl font-bold text-neutral-900 dark:text-white">Register Your Company</h2>
          <p className="text-neutral-500 dark:text-neutral-400">Submit your details and we'll set up your ERP workspace</p>
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
          {fields.map((field) => (
            <div key={field.name}>
              <label className="block text-sm font-medium text-neutral-700 dark:text-neutral-300 mb-1.5">
                {field.label}
              </label>
              <div className={cn(
                "relative flex items-center h-12 bg-white dark:bg-neutral-950 rounded-xl border-2 transition-colors px-4 gap-3",
                focusedInput === field.name ? "border-primary-500 shadow-sm shadow-primary-500/10"
                  : errors[field.name] ? "border-danger-500"
                  : "border-neutral-200 dark:border-neutral-800"
              )}>
                <field.icon className={cn("w-5 h-5 shrink-0", focusedInput === field.name ? "text-primary-600" : "text-neutral-400")} />
                <input
                  {...register(field.name)}
                  type={field.type}
                  placeholder={field.placeholder}
                  className="flex-1 bg-transparent border-none outline-none text-neutral-900 dark:text-white placeholder:text-neutral-400"
                  onFocus={() => setFocusedInput(field.name)}
                  onBlur={() => setFocusedInput(null)}
                />
              </div>
              {errors[field.name] && (
                <p className="text-xs text-danger-500 mt-1">{errors[field.name]?.message}</p>
              )}
            </div>
          ))}

          <button
            type="submit"
            disabled={mutation.isPending}
            className="w-full h-12 bg-primary-600 text-white rounded-xl font-bold hover:bg-primary-700 disabled:opacity-70 transition-colors flex items-center justify-center gap-2"
          >
            {mutation.isPending ? <CustomLoader size="sm" /> : "Submit Registration"}
          </button>
        </form>

        {/* Back link */}
        <div className="text-center">
          <button onClick={() => navigate("/login")} className="text-sm text-neutral-500 hover:text-primary-600 flex items-center justify-center gap-1 mx-auto">
            <ArrowLeft className="w-4 h-4" /> Back to Sign In
          </button>
        </div>
      </div>
    </div>
  );
}
```

- [ ] **Step 3: Commit**

```bash
git add web-system-app/src/lib/api/registration.ts web-system-app/src/features/auth/RegisterCompanyScreen.tsx
git commit -m "$(cat <<'EOF'
feat: add company registration screen and API hook

Form with company name, admin name, email, phone. Shows success
confirmation after submission.

Co-Authored-By: Claude Opus 4.6 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Task 16: Web App — Tenant Not Found Screen

**Files:**
- Create: `web-system-app/src/features/auth/TenantNotFoundScreen.tsx`

- [ ] **Step 1: Create 404 screen for invalid subdomains**

Create `web-system-app/src/features/auth/TenantNotFoundScreen.tsx`:

```typescript
import { AlertTriangle } from "lucide-react";
import companyLogo from "@/assets/logo/Company-Logo.png";

const MAIN_DOMAIN = import.meta.env.VITE_MAIN_DOMAIN || 'avyren.in';

export function TenantNotFoundScreen() {
  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-primary-50 via-white to-accent-50 dark:from-neutral-950 dark:via-neutral-900 dark:to-neutral-950 p-4">
      <div className="max-w-md w-full text-center space-y-6">
        <img src={companyLogo} alt="Avy ERP" className="h-10 mx-auto" />
        <div className="w-16 h-16 bg-warning-100 dark:bg-warning-900/30 rounded-full flex items-center justify-center mx-auto">
          <AlertTriangle className="w-8 h-8 text-warning-600" />
        </div>
        <h2 className="text-2xl font-bold text-neutral-900 dark:text-white">Company Not Found</h2>
        <p className="text-neutral-600 dark:text-neutral-400">
          This company doesn't exist on Avy ERP. Please check the URL and try again.
        </p>
        <a
          href={`https://${MAIN_DOMAIN}`}
          className="inline-block bg-primary-600 text-white px-6 py-3 rounded-xl font-semibold hover:bg-primary-700 transition-colors"
        >
          Visit Avy ERP
        </a>
      </div>
    </div>
  );
}
```

- [ ] **Step 2: Commit**

```bash
git add web-system-app/src/features/auth/TenantNotFoundScreen.tsx
git commit -m "$(cat <<'EOF'
feat: add tenant not found screen for invalid subdomain URLs

Co-Authored-By: Claude Opus 4.6 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Task 17: Web App — Modify LoginScreen for Branded Tenant Login

**Files:**
- Modify: `web-system-app/src/features/auth/LoginScreen.tsx`

- [ ] **Step 1: Add tenant branding support to LoginScreen**

In `web-system-app/src/features/auth/LoginScreen.tsx`, add imports at the top:

```typescript
import { getTenantContext } from "@/lib/tenant";
import { useTenantBranding } from "@/lib/api/auth";
```

Inside the component, add near the top before existing state:

```typescript
const tenantContext = getTenantContext();
const { data: branding, isLoading: brandingLoading } = useTenantBranding(tenantContext.slug);
const isTenantMode = tenantContext.mode === 'tenant';
const isMainMode = tenantContext.mode === 'main';
```

Then conditionally modify the UI:

1. **Hide the "Register Your Company" section** when in tenant mode or admin mode — wrap the existing register button section with:
```typescript
{isMainMode && (
  // existing Register Your Company section
)}
```

2. **Show branded header** when in tenant mode — add above the login form:
```typescript
{isTenantMode && branding?.exists && (
  <div className="text-center mb-6">
    {branding.logoUrl && (
      <img src={branding.logoUrl} alt={branding.companyName} className="h-12 mx-auto mb-3" />
    )}
    <h3 className="text-lg font-semibold text-neutral-800 dark:text-white">
      {branding.companyName}
    </h3>
  </div>
)}
```

3. **Show default Avy ERP branding** when NOT in tenant mode (keep existing logo behavior).

4. **Add "Try Demo" button** on main domain — add in the login form section when `isMainMode`:
```typescript
{isMainMode && (
  <button
    type="button"
    onClick={() => {
      setValue("email", "demo-admin@avyerp.com");
      setValue("password", "demo123");
    }}
    className="w-full h-12 border-2 border-primary-200 dark:border-primary-800 text-primary-600 dark:text-primary-400 rounded-xl font-semibold hover:bg-primary-50 dark:hover:bg-primary-950 transition-colors"
  >
    Try Demo
  </button>
)}
```

5. **Add cross-tenant login validation** — in the login `onSuccess` callback, after verifying MFA status:
```typescript
// Validate tenant match on tenant subdomains
if (isTenantMode && tenantContext.slug) {
  // The backend will already reject cross-tenant access, but add
  // a frontend check for a better UX message
  // This is handled by the backend's validateTenantAccess middleware
}
```

- [ ] **Step 2: Commit**

```bash
git add web-system-app/src/features/auth/LoginScreen.tsx
git commit -m "$(cat <<'EOF'
feat: add branded login for tenant subdomains, demo button for main domain

Tenant subdomains show company logo + name. Main domain shows "Try Demo"
button and "Register Your Company" link. Both hidden on tenant subdomains.

Co-Authored-By: Claude Opus 4.6 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Task 18: Web App — Conditional Routing in App.tsx

**Files:**
- Modify: `web-system-app/src/App.tsx`

- [ ] **Step 1: Add tenant-aware routing**

In `web-system-app/src/App.tsx`, add imports:

```typescript
import { getTenantContext } from "@/lib/tenant";
import { useTenantBranding } from "@/lib/api/auth";
import { RegisterCompanyScreen } from "@/features/auth/RegisterCompanyScreen";
import { TenantNotFoundScreen } from "@/features/auth/TenantNotFoundScreen";
```

Near the top of the `App` component, add:

```typescript
const tenantContext = getTenantContext();
const { data: branding, isLoading: brandingLoading } = useTenantBranding(tenantContext.slug);
```

Update the routing:

1. **For tenant subdomains with invalid slug** — show TenantNotFoundScreen:
```typescript
// If tenant mode and branding loaded but doesn't exist
if (tenantContext.mode === 'tenant' && !brandingLoading && branding && !branding.exists) {
  return <TenantNotFoundScreen />;
}
```

2. **Register route** — only available on main domain:
```typescript
{tenantContext.mode === 'main' && (
  <Route path="/register" element={<RegisterCompanyScreen />} />
)}
```

3. **Landing page route** — only on main domain:
```typescript
<Route path="/" element={
  tenantContext.mode === 'main' ? <LandingScreen /> : <Navigate to="/login" replace />
} />
```

For tenant and admin subdomains, `/` redirects to `/login`.

- [ ] **Step 2: Commit**

```bash
git add web-system-app/src/App.tsx
git commit -m "$(cat <<'EOF'
feat: conditional routing based on subdomain mode

Main domain: landing page + register + demo login.
Tenant subdomain: login only (branded) + 404 for invalid slugs.
Admin subdomain: login + super admin dashboard.

Co-Authored-By: Claude Opus 4.6 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Task 19: Web App — Update LandingScreen with Demo Login

**Files:**
- Modify: `web-system-app/src/features/auth/LandingScreen.tsx`

- [ ] **Step 1: Update CTA buttons on landing page**

In `web-system-app/src/features/auth/LandingScreen.tsx`, find the existing CTA buttons and ensure:

1. The "Get Started" / "Sign In" button links to `/login`
2. The "Register Company" button links to `/register`
3. Both buttons are visible only on the main domain (they already are since LandingScreen is only rendered on main domain)

No major changes needed — just verify the existing links point to `/login` and add `/register` where the "Register Company" CTA exists.

- [ ] **Step 2: Commit**

```bash
git add web-system-app/src/features/auth/LandingScreen.tsx
git commit -m "$(cat <<'EOF'
feat: update landing page CTAs for registration flow

Co-Authored-By: Claude Opus 4.6 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Task 20: Mobile App — Remove Register Button

**Files:**
- Modify: `mobile-app/src/features/auth/login-screen.tsx`

- [ ] **Step 1: Remove the "Register Your Company" section**

In `mobile-app/src/features/auth/login-screen.tsx`, find the register section (around lines 225-254) that contains:
- The "NEW TO AVY ERP?" divider
- The "Register Your Company" button with building icon
- The `handleRegisterCompany` handler

Remove the entire section from the JSX. Also remove the `handleRegisterCompany` function if it exists.

Keep the Terms of Service and Privacy Policy footer.

- [ ] **Step 2: Commit**

```bash
git add mobile-app/src/features/auth/login-screen.tsx
git commit -m "$(cat <<'EOF'
feat: remove Register Your Company button from mobile login screen

Registration is handled via the web app only. Mobile users log in
with credentials provided by their company admin.

Co-Authored-By: Claude Opus 4.6 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Task 21: Backend — Verify & Test

**Files:** None (verification only)

- [ ] **Step 1: Run Prisma merge and generate**

```bash
cd avy-erp-backend && pnpm prisma:merge && pnpm db:generate
```
Expected: No errors.

- [ ] **Step 2: Run TypeScript compilation**

```bash
cd avy-erp-backend && pnpm build
```
Expected: No TypeScript errors.

- [ ] **Step 3: Run existing tests**

```bash
cd avy-erp-backend && pnpm test
```
Expected: Existing tests pass (new features don't break existing functionality).

- [ ] **Step 4: Run linting**

```bash
cd avy-erp-backend && pnpm lint
```
Expected: No lint errors.

---

## Task 22: Web App — Verify & Test

**Files:** None (verification only)

- [ ] **Step 1: Run TypeScript check**

```bash
cd web-system-app && pnpm build
```
Expected: Build succeeds.

- [ ] **Step 2: Run linting**

```bash
cd web-system-app && pnpm lint
```
Expected: No lint errors.

- [ ] **Step 3: Test tenant detection locally**

Start dev server and verify:
- `http://localhost:5173` → Landing page + demo login + register link
- `http://localhost:5173?tenant=admin` → Login page (no landing, no register)
- `http://localhost:5173?tenant=test-company` → Branded login (calls branding API)
- `http://localhost:5173/register` → Registration form

---

## Task 23: Mobile App — Verify

**Files:** None (verification only)

- [ ] **Step 1: Run type check**

```bash
cd mobile-app && pnpm type-check
```
Expected: No TypeScript errors.

- [ ] **Step 2: Verify login screen renders without register button**

```bash
cd mobile-app && pnpm start
```
Open in Expo Go or simulator. Verify:
- Login screen shows email + password fields
- No "Register Your Company" button or "NEW TO AVY ERP?" divider
- Login flow works normally

---

## Task 24: Final Integration Commit

- [ ] **Step 1: Create final integration commit if any loose changes remain**

```bash
git status
# Stage any remaining files
git add -A
git commit -m "$(cat <<'EOF'
chore: final cleanup for hybrid multi-tenancy + subdomain routing

Co-Authored-By: Claude Opus 4.6 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Summary

| Task | Description | Codebase |
|------|-------------|----------|
| 1 | Prisma schema changes (slug, registration model) | Backend |
| 2 | New environment variables | Backend |
| 3 | LRU TenantConnectionManager | Backend |
| 4 | Tenant middleware upgrade (DB lookup, status, req.prisma) | Backend |
| 5 | Dynamic CORS for wildcard subdomains | Backend |
| 6 | Registration email templates | Backend |
| 7 | Registration module (validators, service, controller, routes) | Backend |
| 8 | Tenant branding endpoint | Backend |
| 9 | Mount routes + rate limiting | Backend |
| 10 | Slug field in tenant onboarding | Backend |
| 11 | Tenant schema migration CLI | Backend |
| 12 | PgBouncer Docker setup | Infrastructure |
| 13 | Tenant detection utility | Web App |
| 14 | Tenant branding API hook | Web App |
| 15 | Registration form + API | Web App |
| 16 | Tenant not found screen | Web App |
| 17 | Branded login screen | Web App |
| 18 | Conditional routing by subdomain | Web App |
| 19 | Landing page CTA updates | Web App |
| 20 | Remove register button | Mobile App |
| 21 | Backend verification | Backend |
| 22 | Web app verification | Web App |
| 23 | Mobile app verification | Mobile App |
| 24 | Final integration commit | All |
