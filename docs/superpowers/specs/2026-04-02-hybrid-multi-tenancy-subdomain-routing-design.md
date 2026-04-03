# Hybrid Multi-Tenancy + Subdomain Routing Design Spec

**Date:** 2026-04-02
**Status:** Approved
**Scope:** Backend, Web App, Mobile App, Infrastructure

---

## 1. Overview

Evolve the existing schema-per-tenant architecture into a hybrid multi-tenancy system with subdomain-based routing for the web app. The system supports schema-per-tenant (default) with a future path to database-per-tenant for premium customers.

### Goals
- Each tenant gets a branded subdomain: `<slug>.avyren.in`
- Main domain (`avyren.in`) serves as the public landing page + demo access
- Super admin panel on `admin.avyren.in`
- Production-grade connection pooling (LRU + PgBouncer)
- Tenant schema migration CLI
- Company registration flow (request-based, not self-service)
- Mobile app: minimal changes (email-based tenant auto-resolve)

### Non-Goals (Deferred)
- Database-per-tenant actual implementation (model supports it, logic deferred)
- Custom domain resolution + SSL provisioning (nullable `customDomain` field added for future)
- CAPTCHA on registration (add Cloudflare Turnstile if spam becomes an issue)
- Auto-migration on deploy (manual CLI for now)

---

## 2. Domain Architecture

| Domain | Purpose | Auth | Landing Page | Register |
|--------|---------|------|-------------|----------|
| `avyren.in` | Public site + demo | Demo credentials only | Yes | Yes |
| `admin.avyren.in` | Super admin panel | Super admin login | No | No |
| `<slug>.avyren.in` | Tenant app | Company users only | No | No |

### Hostname Resolution Logic (Explicit, Not Pattern-Based)

```
hostname === "avyren.in"           → MAIN (landing + demo)
hostname === "admin.avyren.in"     → SUPER_ADMIN
hostname matches reserved slugs            → REJECT (404)
hostname matches *.avyren.in       → TENANT (extract slug)
else                                       → REJECT (404)
```

### Reserved Slugs (Blacklist)
```
admin, www, api, app, staging, dev, test, demo, mail, ftp, cdn, static, assets, docs, help, support, status, blog
```

These slugs cannot be chosen during tenant onboarding.

---

## 3. Database Architecture

### Schema Layout

```
PostgreSQL (single instance)
│
├── PgBouncer (Docker, transaction mode)
│
├── public schema (Platform DB — shared)
│   ├── Tenant (+ slug, customDomain, dbStrategy, databaseUrl)
│   ├── Company (existing — has logo/name for branding)
│   ├── User, Role, TenantUser
│   ├── Subscription, Invoice, Payment
│   ├── CompanyRegistrationRequest (NEW)
│   ├── SupportTicket, AuditLog
│   └── Other platform models
│
├── tenant_demo (Demo tenant — isolated, daily reset)
│
├── tenant_<slug1> (Tenant A schema)
├── tenant_<slug2> (Tenant B schema)
└── ...
```

### Future: Database-Per-Tenant (Designed, Not Implemented)

```
Tenant.dbStrategy = 'schema' (default) | 'database' (future)
Tenant.databaseUrl = null (schema) | "postgresql://..." (dedicated DB)
```

The connection logic will be abstracted to check `dbStrategy` and route accordingly. Only `schema` strategy is implemented now.

---

## 4. Prisma Model Changes

### Tenant Model Updates

```prisma
model Tenant {
  id            String       @id @default(cuid())
  schemaName    String       @unique
  slug          String       @unique        // NEW: e.g., "avyren-technologies"
  customDomain  String?      @unique        // NEW: future use, nullable
  dbStrategy    String       @default("schema")  // NEW: "schema" | "database"
  databaseUrl   String?                     // NEW: only for dbStrategy="database"
  companyId     String       @unique
  status        TenantStatus @default(ACTIVE)
  createdAt     DateTime     @default(now())
  updatedAt     DateTime     @updatedAt

  company       Company        @relation(...)
  subscriptions Subscription[]
}
```

### New: CompanyRegistrationRequest Model

```prisma
model CompanyRegistrationRequest {
  id          String                    @id @default(cuid())
  companyName String
  adminName   String
  email       String                    @unique
  phone       String
  status      RegistrationRequestStatus @default(PENDING)
  ticketId    String?                   @unique
  rejectionReason String?
  createdAt   DateTime                  @default(now())
  updatedAt   DateTime                  @updatedAt

  ticket      SupportTicket?            @relation(fields: [ticketId], references: [id])
}

enum RegistrationRequestStatus {
  PENDING
  APPROVED
  REJECTED
}
```

---

## 5. Connection Pooling

### Architecture

```
[Express Request]
    ↓
[Tenant Middleware] → resolves tenant
    ↓
[TenantConnectionManager.getClient(tenant)]
    ↓
[LRU Cache (max 50 PrismaClient instances)]
  - Key: hash of connectionString (future-proofs DB-per-tenant)
  - On eviction: client.$disconnect()
  - On get: touch (move to front)
    ↓
[PgBouncer (Docker container)]
  - Pool mode: transaction
  - Default pool size: 20
  - Max client connections: 100
    ↓
[PostgreSQL]
```

### PrismaClient Configuration

```typescript
// Connection string format (PgBouncer-aware):
// postgresql://user:pass@pgbouncer:6432/avy_erp?schema=tenant_slug&pgbouncer=true&connection_limit=5

new PrismaClient({
  datasources: {
    db: {
      url: `${baseUrl}?schema=${schemaName}&pgbouncer=true&connection_limit=5`
    }
  }
})
```

### LRU Cache Implementation

```typescript
class TenantConnectionManager {
  private cache: LRUCache<string, PrismaClient>  // max 50

  getClient(tenant: { schemaName, databaseUrl?, dbStrategy }): PrismaClient {
    const connString = this.buildConnectionString(tenant)
    const key = hash(connString)

    if (this.cache.has(key)) return this.cache.get(key)

    const client = new PrismaClient({ datasources: { db: { url: connString } } })
    this.cache.set(key, client)
    return client
  }

  // On LRU eviction callback:
  onEvict(key, client) {
    client.$disconnect()  // CRITICAL: prevent zombie connections
  }
}
```

### Request-Scoped Context

```typescript
// Middleware attaches resolved client to request:
req.prisma = tenantConnectionManager.getClient(req.tenant)

// Services use req.prisma directly — no manual connection creation
```

### PgBouncer Docker Setup

```yaml
# docker-compose.yml
pgbouncer:
  image: edoburu/pgbouncer
  environment:
    DATABASE_URL: postgresql://user:pass@postgres:5432/avy_erp
    POOL_MODE: transaction
    DEFAULT_POOL_SIZE: 20
    MAX_CLIENT_CONN: 100
  ports:
    - "6432:6432"
```

### Key Rules
- Prisma version MUST support PgBouncer (`?pgbouncer=true` flag)
- No long-lived transactions (PgBouncer transaction mode limitation)
- Per-client `connection_limit=5` (aggressive, prevents DB pressure)
- LRU max size configurable via `TENANT_CLIENT_CACHE_SIZE` env var

---

## 6. Backend API Changes

### New Endpoints

#### Public (No Auth)

| Method | Path | Purpose | Rate Limit |
|--------|------|---------|------------|
| `POST` | `/auth/register-company` | Submit registration request | 1 per email + IP limit |
| `GET` | `/auth/tenant-branding?slug=<slug>` | Get company name + logo for login page | Rate limited |

#### Super Admin

| Method | Path | Purpose |
|--------|------|---------|
| `GET` | `/platform/registration-requests` | List pending registrations |
| `GET` | `/platform/registration-requests/:id` | Get registration detail |
| `PATCH` | `/platform/registration-requests/:id` | Approve/reject registration |

### Tenant Branding Endpoint (Security-Hardened)

```typescript
// GET /auth/tenant-branding?slug=avyren-technologies
//
// Valid slug response:
{ success: true, data: { exists: true, companyName: "Avyren Technologies", logoUrl: "https://..." } }
//
// Invalid slug response (generic — prevents enumeration):
{ success: true, data: { exists: false } }
//
// Rate limited: 10 requests per minute per IP
```

### Registration Endpoint

```typescript
// POST /auth/register-company
// Body: { companyName, adminName, email, phone }
//
// Actions:
// 1. Validate email uniqueness (in both User and CompanyRegistrationRequest tables)
// 2. Create CompanyRegistrationRequest (status: PENDING)
// 3. Create SupportTicket (type: COMPANY_REGISTRATION, linked to request)
// 4. Send email notification to super admin
// 5. Return success message
//
// Rate limit: 1 per email (duplicate check) + 3 per IP per hour
```

### Registration Approval Flow

```
Super Admin approves registration request
    ↓
PATCH /platform/registration-requests/:id { status: APPROVED }
    ↓
1. Update request status to APPROVED
2. Proceed with normal tenant onboarding wizard (16-step)
   - Slug field pre-filled from company name (editable)
   - Admin email pre-filled from registration
3. On wizard completion:
   - Create Company + Tenant (with slug)
   - Create schema: CREATE SCHEMA IF NOT EXISTS "tenant_<slug>"
   - Run tenant migrations on new schema
   - Create company admin user account
   - Send welcome email to registered admin with:
     - Their subdomain URL: https://<slug>.avyren.in
     - Login credentials
```

### Tenant Onboarding Wizard Update

- Add **slug** field to the onboarding wizard (Step 1 or identity section)
- Auto-suggest from company name: "Avyren Technologies" → `avyren-technologies`
- Validate: unique, not in reserved slugs blacklist, URL-safe characters only
- Regex: `/^[a-z0-9][a-z0-9-]{1,48}[a-z0-9]$/` (3-50 chars, lowercase alphanumeric + hyphens)

### CORS Update

```typescript
// Dynamic origin validation
const ALLOWED_PATTERN = /^https:\/\/[\w-]+\.avyerp\.avyren\.in$/
const MAIN_DOMAIN = 'https://avyren.in'

function corsOriginValidator(origin: string): boolean {
  if (!origin) return false
  if (origin === MAIN_DOMAIN) return true
  if (ALLOWED_PATTERN.test(origin)) return true
  // Development origins
  if (env.NODE_ENV === 'development') {
    return env.CORS_ALLOWED_ORIGINS.includes(origin)
  }
  return false
}
```

### Cross-Tenant Security (Double Validation)

```typescript
// In tenant middleware, AFTER auth middleware:
if (req.tenant && req.user) {
  if (req.tenant.id !== req.user.tenantId) {
    throw ApiError.forbidden('Access denied: tenant mismatch')
  }
}
```

### Tenant Resolution Audit Logging

```typescript
// Log in tenant middleware:
logger.debug('Tenant resolved', {
  hostname: req.hostname,
  resolvedTenantId: tenant?.id,
  slug: tenant?.slug,
  method: extractionMethod  // 'subdomain' | 'header' | 'jwt'
})
```

### Tenant Status Blocking

```typescript
// In tenant middleware:
if (tenant.status === 'SUSPENDED') {
  throw ApiError.forbidden('This company account has been suspended. Contact support.')
}
if (tenant.status === 'CANCELLED' || tenant.status === 'EXPIRED') {
  throw ApiError.forbidden('This company account is inactive.')
}
```

---

## 7. Tenant Schema Migration CLI

### Command

```bash
pnpm db:migrate-tenants
```

### Behavior

```
1. Connect to platform DB
2. SELECT all tenants WHERE status IN ('ACTIVE', 'TRIAL')
3. For each tenant:
   a. Set search_path to tenant's schema
   b. Apply pending Prisma migrations
   c. Log success/failure with tenant slug
4. Summary: X succeeded, Y failed, Z skipped
```

### Rules
- Run AFTER `pnpm db:migrate` (platform schema first)
- Manual execution only (part of deploy checklist)
- Failures are logged but don't block other tenants
- Failed tenants can be retried individually: `pnpm db:migrate-tenants --tenant=<slug>`

---

## 8. Web App Changes

### Runtime Tenant Detection

```typescript
// src/lib/tenant.ts

type AppMode = 'main' | 'admin' | 'tenant'

interface TenantContext {
  mode: AppMode
  slug: string | null
}

const RESERVED_SLUGS = ['admin', 'www', 'api', 'app', 'staging', 'dev', 'test', 'demo', ...]

function detectTenant(): TenantContext {
  const hostname = window.location.hostname

  // Main domain
  if (hostname === 'avyren.in') {
    return { mode: 'main', slug: null }
  }

  // Extract subdomain
  const slug = hostname.replace('.avyren.in', '')

  // Super admin
  if (slug === 'admin') {
    return { mode: 'admin', slug: null }
  }

  // Reserved slug — treat as invalid
  if (RESERVED_SLUGS.includes(slug)) {
    return { mode: 'main', slug: null }  // or show 404
  }

  // Tenant subdomain
  return { mode: 'tenant', slug }
}
```

### Conditional Rendering

```
App Load
  ↓
detectTenant()
  ↓
mode === 'main'?
  → Show landing page + demo login + "Register Your Company"
  → Demo login: pre-filled credentials, "Try Demo" button
  ↓
mode === 'admin'?
  → Show standard login page (super admin only)
  → After login: super admin dashboard
  ↓
mode === 'tenant'?
  → Call GET /auth/tenant-branding?slug=<slug>
  → exists === true?
    → Show branded login (company logo + name)
    → After login: validate user.tenantSlug matches subdomain slug
    → Mismatch: "Your account doesn't belong to this company"
  → exists === false?
    → Show styled 404: "Company not found. Visit avyren.in"
```

### Login Page Variants

#### Main Domain (`avyren.in`)
- Avy ERP branding (default logo/colors)
- Email + password fields
- "Try Demo" button (pre-fills demo credentials)
- "Register Your Company" link → registration form
- Footer link: "Already have an account? Ask your admin for your company URL"

#### Super Admin (`admin.avyren.in`)
- Avy ERP branding
- Email + password fields
- No register button
- No demo button

#### Tenant (`<slug>.avyren.in`)
- Company logo + company name (fetched from branding endpoint)
- Email + password fields
- No register button
- No demo button
- Powered by Avy ERP footer

### 404 Page (Invalid Subdomain)

- Styled Avy ERP 404 page
- Message: "This company doesn't exist"
- CTA: "Visit avyren.in to learn more"
- No information leakage about valid slugs

### Registration Form (`avyren.in/register`)

- Fields: Company Name, Admin Name, Email, Phone
- Submit → `POST /auth/register-company`
- Success: "Thank you! We'll review your request and get back to you shortly."
- Duplicate email: "A registration with this email already exists"

### API Client Changes

- No changes to base URL (continues to hit `avy-erp-api.avyren.in`)
- No `X-Tenant-ID` header needed (JWT-based resolution)
- Tenant context flows through authentication as before

---

## 9. Mobile App Changes

### Changes Required
1. **Remove "Register Your Company" button** from login screen
2. No other changes

### What Stays the Same
- Login flow: email + password → backend auto-resolves tenant from email
- API client: same base URL, same JWT-based auth
- Tenant context: embedded in JWT, no explicit tenant selection needed

---

## 10. Demo Tenant

### Setup
- Dedicated tenant with slug `demo` and schema `tenant_demo`
- Pre-seeded with sample data (departments, employees, attendance, etc.)
- Demo accounts: `demo-admin@avyerp.com` (company admin), `demo-user@avyerp.com` (user)

### Isolation Rules
- Feature flags disable:
  - Email/SMS sending
  - External integrations
  - File uploads (or cap at minimal size)
  - Data export
- Daily cron job:
  - Wipe all demo tenant data
  - Re-seed from seed script
  - Reset demo user passwords

### Demo Login Flow
- User clicks "Try Demo" on `avyren.in`
- Pre-fills `demo-admin@avyerp.com` / `demo123`
- Logs in → redirected to demo company dashboard
- Banner at top: "You're using a demo account. Data resets daily."

---

## 11. Infrastructure

### Cloudflare DNS Records

```
Type    Name                        Content                     Proxy
CNAME   avyren.in           <cloudflare-pages>.pages.dev  Proxied
CNAME   *.avyren.in         <cloudflare-pages>.pages.dev  Proxied
```

### Cloudflare Pages

- Project: `avy-erp-web`
- Build command: `cd web-system-app && pnpm build`
- Build output: `web-system-app/dist`
- Custom domains: `avyren.in` + `*.avyren.in`
- SSL: automatic (Cloudflare Universal SSL covers wildcard)

### PgBouncer (Docker)

```yaml
# Added to existing docker-compose.yml
services:
  pgbouncer:
    image: edoburu/pgbouncer:latest
    restart: always
    environment:
      DATABASE_URL: postgresql://${DB_USER}:${DB_PASS}@postgres:5432/${DB_NAME}
      POOL_MODE: transaction
      DEFAULT_POOL_SIZE: 20
      MAX_CLIENT_CONN: 100
      SERVER_RESET_QUERY: DISCARD ALL
    ports:
      - "6432:6432"
    depends_on:
      - postgres
```

### Backend Environment Updates

```env
# Existing (updated to point through PgBouncer)
DATABASE_URL=postgresql://user:pass@pgbouncer:6432/avy_erp?schema=public&pgbouncer=true
DATABASE_URL_TEMPLATE=postgresql://user:pass@pgbouncer:6432/avy_erp?schema={schema}&pgbouncer=true&connection_limit=5

# New
TENANT_CLIENT_CACHE_SIZE=50           # LRU cache max size
MAIN_DOMAIN=avyren.in         # For CORS and slug detection
SUPER_ADMIN_EMAIL=admin@avyren.in    # For registration notifications
```

---

## 12. Security Summary

| Threat | Mitigation |
|--------|------------|
| Cross-tenant data access | Double validation: CORS origin + JWT tenantId match |
| Slug enumeration | Generic `{ exists: false }` response, rate limited |
| Registration spam | 1 per email + 3 per IP per hour |
| Wrong subdomain login | "Account doesn't belong to this company" (no company reveal) |
| Token replay across domains | JWT tenantId !== request tenant → reject |
| Demo tenant abuse | Feature flags disable integrations, daily data reset |
| Connection exhaustion | LRU eviction + PgBouncer connection limits |
| Reserved slug hijacking | Blacklist validated during onboarding |
| Tenant status abuse | Middleware blocks SUSPENDED/CANCELLED/EXPIRED tenants |

---

## 13. Email Notifications

### Registration Submitted (to Super Admin)

```
Subject: New Company Registration Request — {companyName}
Body:
  A new company registration request has been submitted.

  Company: {companyName}
  Contact: {adminName}
  Email: {email}
  Phone: {phone}

  Review this request in the admin panel:
  https://admin.avyren.in/registration-requests/{id}
```

### Registration Approved (to Company Admin)

```
Subject: Welcome to Avy ERP — Your Account is Ready
Body:
  Your company "{companyName}" has been approved!

  Access your ERP at: https://{slug}.avyren.in
  Login with: {email}
  Temporary password: {tempPassword}

  Please change your password after first login.
```

### Registration Rejected (to Applicant)

```
Subject: Avy ERP — Registration Update
Body:
  Thank you for your interest in Avy ERP.

  Unfortunately, your registration for "{companyName}" could not be approved at this time.
  Reason: {rejectionReason}

  If you have questions, contact support@avyren.in
```

---

## 14. Deploy Checklist

For each deployment that includes schema changes:

```
1. Deploy backend code
2. Run: pnpm db:migrate          (platform schema)
3. Run: pnpm db:migrate-tenants  (all tenant schemas)
4. Verify PgBouncer connectivity
5. Deploy web app to Cloudflare Pages (automatic via git push)
6. Verify wildcard subdomain resolution
7. Test demo login on avyren.in
8. Test tenant login on <slug>.avyren.in
```

---

## 15. Summary of Changes by Codebase

### Backend
- Tenant model: add `slug`, `customDomain`, `dbStrategy`, `databaseUrl` fields
- New model: `CompanyRegistrationRequest`
- New endpoints: register-company, tenant-branding, registration-requests CRUD
- Connection pooling: `TenantConnectionManager` class (LRU + PgBouncer)
- Request-scoped `req.prisma` for tenant client
- CORS: dynamic origin validation
- Tenant middleware: status blocking, audit logging, cross-tenant rejection
- CLI: `pnpm db:migrate-tenants`
- Onboarding wizard: slug field with validation
- Demo tenant: seed script + daily reset cron
- Email service: registration notifications (submitted, approved, rejected)

### Web App
- Tenant detection: `detectTenant()` from hostname
- Conditional rendering: main / admin / tenant modes
- Branded login page (logo + name from branding endpoint)
- Registration form on main domain
- 404 page for invalid subdomains
- Demo login with pre-filled credentials
- Remove "Register Your Company" from tenant subdomains

### Mobile App
- Remove "Register Your Company" button from login screen
- No other changes

### Infrastructure
- Cloudflare DNS: wildcard CNAME for `*.avyren.in`
- Cloudflare Pages: single deployment with wildcard domain
- PgBouncer: Docker container in docker-compose.yml
- Backend env: updated DATABASE_URL through PgBouncer, new env vars
