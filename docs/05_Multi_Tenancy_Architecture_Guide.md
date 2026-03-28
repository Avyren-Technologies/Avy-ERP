# Avy ERP — Multi-Tenancy Architecture Guide

## Custom Domains, Schema-Per-Tenant & Scalable Isolation

---

## Table of Contents

1. [Where You Stand Today](#1-where-you-stand-today)
2. [What You Want to Achieve](#2-what-you-want-to-achieve)
3. [The Three Pillars of Multi-Tenancy](#3-the-three-pillars-of-multi-tenancy)
4. [Pillar 1: Database — Schema-Per-Tenant](#4-pillar-1-database--schema-per-tenant)
5. [Pillar 2: Web App — Custom Domains](#5-pillar-2-web-app--custom-domains)
6. [Pillar 3: Mobile App — Tenant-Aware Client](#6-pillar-3-mobile-app--tenant-aware-client)
7. [Backend Changes Required](#7-backend-changes-required)
8. [Infrastructure & DevOps](#8-infrastructure--devops)
9. [Migration Strategy](#9-migration-strategy)
10. [Cost & Scaling Considerations](#10-cost--scaling-considerations)
11. [Security Implications](#11-security-implications)
12. [Recommended Roadmap](#12-recommended-roadmap)

---

## 1. Where You Stand Today

### Current Architecture Summary

```
┌─────────────────────────────────────────────────────────┐
│                      CLIENTS                            │
│                                                         │
│   Mobile App (Expo)          Web App (React + Electron) │
│   ┌──────────────┐           ┌──────────────────┐       │
│   │ JWT in MMKV  │           │ JWT in localStorage│      │
│   │ API URL from │           │ API URL from      │      │
│   │ .env         │           │ .env (VITE_)      │      │
│   └──────┬───────┘           └────────┬──────────┘      │
│          │                            │                  │
└──────────┼────────────────────────────┼──────────────────┘
           │       Authorization:       │
           │       Bearer <JWT>         │
           ▼                            ▼
┌──────────────────────────────────────────────────────────┐
│                    BACKEND (Express)                     │
│                                                         │
│  1. tenantMiddleware() → extracts tenant from:          │
│     - X-Tenant-ID header                                │
│     - Subdomain                                         │
│     - Query param                                       │
│     - JWT payload                                       │
│                                                         │
│  2. authMiddleware() → validates JWT, loads permissions  │
│                                                         │
│  3. createTenantPrisma(schemaName) → per-request client │
│                                                         │
└────────────────────────┬─────────────────────────────────┘
                         │
                         ▼
┌──────────────────────────────────────────────────────────┐
│                    PostgreSQL                            │
│                                                         │
│  ┌──────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │  public   │  │ tenant_abc   │  │ tenant_xyz   │      │
│  │ (platform)│  │ (company A)  │  │ (company B)  │      │
│  │           │  │              │  │              │       │
│  │ Tenant    │  │ Department   │  │ Department   │      │
│  │ Company   │  │ Employee     │  │ Employee     │      │
│  │ User      │  │ Attendance   │  │ Attendance   │      │
│  │ Role      │  │ Payroll...   │  │ Payroll...   │      │
│  └──────────┘  └──────────────┘  └──────────────┘      │
│                                                         │
│  + Redis (cache + queue)                                │
└──────────────────────────────────────────────────────────┘
```

### What's Already Working

| Area | Status | Details |
|------|--------|---------|
| Schema-per-tenant DB | Partially done | `DATABASE_URL_TEMPLATE` with `{schema}` placeholder exists. `createTenantPrisma(schemaName)` factory exists. Tenant model has `schemaName` field. |
| Tenant middleware | Done | Extracts tenant from header/subdomain/query/JWT. Caches in Redis (24hr). |
| JWT-based auth | Done | Embeds `tenantId`, `companyId`, `permissions` in JWT payload. |
| Platform vs tenant data | Done | Platform models (User, Tenant, Company) in `public` schema. Business models designed for tenant schemas. |
| RBAC + Feature toggles | Done | Fine-grained permissions + per-user feature flags. |
| Custom domains for web | Not started | Single hardcoded `VITE_API_URL`. No subdomain detection. |
| Tenant schema creation | Not started | No automated schema provisioning during onboarding. |
| Schema migrations per tenant | Not started | Prisma migrate runs only on `public` schema. |

### What's NOT Done (The Gaps)

1. **No automated schema creation** — when a new company is onboarded, no PostgreSQL schema is created
2. **No tenant-specific migrations** — `prisma migrate` only targets the platform schema
3. **No custom domain routing** — web app uses a single URL, no subdomain detection
4. **No tenant branding** — no per-tenant logos, colors, or white-labeling
5. **Mobile app has no tenant URL switching** — hardcoded API URL in `.env`

---

## 2. What You Want to Achieve

```
avyren.avy-erp.avyren.in     → Avyren company's ERP portal
tatagroup.avy-erp.avyren.in  → Tata Group's ERP portal
infosys.avy-erp.avyren.in    → Infosys' ERP portal
```

Each customer gets:
- **Their own database schema** (complete data isolation)
- **Their own web subdomain** (branded experience)
- **Same mobile app** (but tenant-aware — detects which company the user belongs to)

---

## 3. The Three Pillars of Multi-Tenancy

```
┌─────────────────────────────────────────────────────────────────┐
│                   MULTI-TENANCY ARCHITECTURE                    │
│                                                                 │
│   PILLAR 1              PILLAR 2              PILLAR 3         │
│   ─────────             ─────────             ─────────         │
│   DATABASE              WEB APP               MOBILE APP        │
│                                                                 │
│   Schema-per-tenant     Custom subdomains     Single app,       │
│   isolation with        with wildcard DNS     tenant resolved   │
│   automated             + reverse proxy       from JWT after    │
│   provisioning                                login             │
│                                                                 │
│   ┌───────────┐        ┌───────────┐         ┌───────────┐     │
│   │ tenant_a  │        │ *.avy-erp │         │  Login →   │     │
│   │ tenant_b  │        │  .avyren  │         │  JWT has   │     │
│   │ tenant_c  │        │  .in      │         │  tenantId  │     │
│   └───────────┘        └───────────┘         └───────────┘     │
│                                                                 │
│   Each has own          Each gets own          Same APK/IPA     │
│   tables, data,         branded URL,           for all          │
│   indexes               same app code          customers        │
└─────────────────────────────────────────────────────────────────┘
```

---

## 4. Pillar 1: Database — Schema-Per-Tenant

### 4.1 Why Schema-Per-Tenant (Not Separate Databases)

| Approach | Pros | Cons |
|----------|------|------|
| **Shared tables** (row-level isolation with `companyId` filter) | Simplest. Single migration. | Risk of data leaks if you forget a `WHERE`. No true isolation. Hard to scale past 10K companies. |
| **Schema-per-tenant** (same DB, different schemas) | Strong isolation. Easy backup/restore per tenant. Single DB connection. Moderate complexity. | Schema migrations must run per tenant. Connection pooling needs attention. |
| **Database-per-tenant** (separate PostgreSQL instances) | Maximum isolation. Per-tenant scaling. | Expensive. Complex connection management. Operational nightmare at 100+ tenants. |

**Recommendation: Schema-per-tenant** — You already have the foundation for this. It gives you strong isolation without the operational overhead of managing hundreds of database instances.

### 4.2 How Schema-Per-Tenant Works

```
PostgreSQL Instance
│
├── Schema: public (PLATFORM DATA)
│   ├── Tenant          ← registry of all tenants
│   ├── Company         ← company onboarding data
│   ├── User            ← all users across all tenants
│   ├── Role            ← RBAC roles
│   ├── TenantUser      ← user ↔ tenant mapping
│   ├── Subscription    ← billing per tenant
│   ├── Invoice         ← invoices
│   ├── Payment         ← payments
│   ├── AuditLog        ← platform-wide audit
│   └── FeatureToggle   ← per-user feature flags
│
├── Schema: tenant_avyren (AVYREN'S DATA)
│   ├── Department
│   ├── Designation
│   ├── Employee
│   ├── AttendanceRecord
│   ├── LeaveRequest
│   ├── PayrollRun
│   └── ... (all business tables)
│
├── Schema: tenant_tatagroup (TATA GROUP'S DATA)
│   ├── Department
│   ├── Designation
│   ├── Employee
│   └── ... (identical structure, different data)
│
└── Schema: tenant_infosys (INFOSYS' DATA)
    ├── Department
    └── ...
```

### 4.3 What You Need to Build

#### A. Separate Prisma Schemas

Right now you have ONE `schema.prisma` with both platform and tenant models mixed together. You need to split this:

```
prisma/
├── platform.prisma          ← Tenant, Company, User, Subscription, etc.
├── tenant.prisma            ← Department, Employee, Attendance, Payroll, etc.
└── migrations/
    ├── platform/            ← migrations for public schema
    └── tenant/              ← migrations applied to EACH tenant schema
```

**Platform schema** (`platform.prisma`):
- Contains: Tenant, Company, User, Role, TenantUser, Subscription, Invoice, Payment, AuditLog, FeatureToggle, PasswordResetToken
- Also: Location, CompanyContact, CompanyShift, NoSeriesConfig, IotReason (onboarding data)
- Runs migrations on `public` schema only

**Tenant schema** (`tenant.prisma`):
- Contains: Department, Designation, Grade, EmployeeType, CostCentre, Employee, and ALL HR/business models
- Runs migrations on EACH `tenant_*` schema

#### B. Automated Schema Provisioning

When a new company completes onboarding (Step 16: Activation), the backend must:

```
1. CREATE SCHEMA tenant_{companySlug};

2. Run tenant migrations on the new schema:
   SET search_path TO tenant_{companySlug};
   -- Execute all migration SQL files

3. Seed default data:
   - Default departments
   - Default designations
   - Default leave types
   - Default salary components
   - Default attendance rules

4. Update Tenant record:
   UPDATE "Tenant" SET "schemaName" = 'tenant_{companySlug}', "status" = 'ACTIVE';

5. Cache tenant metadata in Redis
```

**Implementation approach:**

```typescript
// src/core/tenant/tenant-provisioning.service.ts

class TenantProvisioningService {

  async provisionTenant(companySlug: string, companyId: string) {
    const schemaName = `tenant_${companySlug}`;

    // 1. Create PostgreSQL schema
    await platformPrisma.$executeRawUnsafe(
      `CREATE SCHEMA IF NOT EXISTS "${schemaName}"`
    );

    // 2. Run tenant migrations
    await this.runTenantMigrations(schemaName);

    // 3. Seed defaults
    const tenantPrisma = createTenantPrisma(schemaName);
    await this.seedDefaults(tenantPrisma, companyId);

    // 4. Update tenant record
    await platformPrisma.tenant.update({
      where: { companyId },
      data: { schemaName, status: 'ACTIVE' }
    });

    // 5. Cache
    await redis.set(`tenant:${companyId}`, JSON.stringify({
      schemaName, status: 'ACTIVE'
    }), 'EX', 86400);
  }

  private async runTenantMigrations(schemaName: string) {
    // Option A: Raw SQL migration files
    const migrationFiles = await glob('prisma/migrations/tenant/*.sql');
    for (const file of migrationFiles) {
      const sql = await fs.readFile(file, 'utf8');
      await platformPrisma.$executeRawUnsafe(
        `SET search_path TO "${schemaName}"; ${sql}`
      );
    }

    // Option B: Use prisma migrate with dynamic schema
    // (More complex but keeps Prisma's migration tracking)
  }
}
```

#### C. Per-Tenant Migration Runner

When you add a new feature (e.g., a new HR table), you need to migrate ALL existing tenant schemas:

```typescript
// scripts/migrate-all-tenants.ts

async function migrateAllTenants() {
  const tenants = await platformPrisma.tenant.findMany({
    where: { status: { in: ['ACTIVE', 'TRIAL'] } }
  });

  console.log(`Migrating ${tenants.length} tenant schemas...`);

  for (const tenant of tenants) {
    try {
      await runTenantMigrations(tenant.schemaName);
      console.log(`✓ ${tenant.schemaName}`);
    } catch (err) {
      console.error(`✗ ${tenant.schemaName}: ${err.message}`);
      // Log but continue — don't let one tenant block others
    }
  }
}
```

Add this to your `deploy.sh`:
```bash
# After platform migration
npx prisma migrate deploy              # Platform schema
npx ts-node scripts/migrate-all-tenants.ts  # All tenant schemas
```

#### D. Connection Pooling Strategy

With schema-per-tenant, you create a Prisma client per request. This can exhaust connections quickly.

**Problem:** 100 concurrent users × 1 Prisma client each = 100 connections (Prisma's default pool is 5 per client = 500 connections!)

**Solution: Use PgBouncer**

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│   Express    │────▶│  PgBouncer   │────▶│  PostgreSQL  │
│  (N requests)│     │ (pool: 100)  │     │  (max: 200)  │
│              │     │              │     │              │
│ Each request │     │ Shares pool  │     │              │
│ sets schema  │     │ across all   │     │              │
│ via SET      │     │ tenants      │     │              │
└──────────────┘     └──────────────┘     └──────────────┘
```

Update `docker-compose.yml`:
```yaml
services:
  pgbouncer:
    image: edoburu/pgbouncer:latest
    environment:
      DATABASE_URL: postgres://user:pass@postgres:5432/avyerp
      POOL_MODE: transaction    # Important: transaction mode
      MAX_CLIENT_CONN: 1000
      DEFAULT_POOL_SIZE: 50
    ports:
      - "6432:6432"
    depends_on:
      postgres:
        condition: service_healthy
```

And update your tenant Prisma client to use a SINGLE shared client that switches schema per request:

```typescript
// src/config/database.ts — IMPROVED

import { Pool } from 'pg';

const pool = new Pool({
  connectionString: process.env.DATABASE_URL,
  max: 50, // Shared pool
});

// Instead of creating a new Prisma client per request,
// use raw pg pool with SET search_path
async function withTenantSchema<T>(
  schemaName: string,
  fn: (client: PoolClient) => Promise<T>
): Promise<T> {
  const client = await pool.connect();
  try {
    await client.query(`SET search_path TO "${schemaName}", public`);
    return await fn(client);
  } finally {
    await client.query(`SET search_path TO public`);
    client.release();
  }
}
```

**However**, if you want to keep using Prisma ORM (which is much nicer), the better approach is to **cache and reuse Prisma clients** per schema:

```typescript
// src/config/database.ts — CACHED PRISMA CLIENTS

const tenantClients = new Map<string, PrismaClient>();
const CLIENT_TTL = 30 * 60 * 1000; // 30 minutes

function getTenantPrisma(schemaName: string): PrismaClient {
  if (tenantClients.has(schemaName)) {
    return tenantClients.get(schemaName)!;
  }

  const url = process.env.DATABASE_URL_TEMPLATE!
    .replace('{schema}', schemaName);

  const client = new PrismaClient({
    datasources: { db: { url } },
    log: ['error', 'warn'],
  });

  tenantClients.set(schemaName, client);

  // Evict after TTL to prevent memory leaks
  setTimeout(() => {
    client.$disconnect();
    tenantClients.delete(schemaName);
  }, CLIENT_TTL);

  return client;
}
```

This way, if 50 requests come in for tenant "avyren", they all share ONE Prisma client (with its internal connection pool of ~5 connections), instead of creating 50 separate clients.

---

## 5. Pillar 2: Web App — Custom Domains

### 5.1 Domain Structure

```
Format: {company-slug}.avy-erp.avyren.in

Examples:
  avyren.avy-erp.avyren.in       → Avyren's portal
  tatagroup.avy-erp.avyren.in    → Tata Group's portal
  infosys.avy-erp.avyren.in      → Infosys' portal

Super Admin:
  admin.avy-erp.avyren.in        → Super Admin panel

Later (optional):
  erp.avyren.com                  → Custom vanity domain for Avyren
  erp.tatagroup.com               → Custom domain for Tata
```

### 5.2 DNS Setup

You need a **wildcard DNS record** pointing all subdomains to your server:

```
*.avy-erp.avyren.in.    A     YOUR_SERVER_IP
avy-erp.avyren.in.      A     YOUR_SERVER_IP
```

This means `anything.avy-erp.avyren.in` resolves to your server. The server then decides which tenant it is.

### 5.3 Reverse Proxy (Nginx)

Nginx sits in front of your web app and handles:
1. SSL termination (wildcard certificate)
2. Subdomain extraction
3. Routing to the correct app instance

```nginx
# /etc/nginx/sites-available/avy-erp

# Wildcard SSL certificate (Let's Encrypt)
# certbot certonly --dns-cloudflare -d "*.avy-erp.avyren.in" -d "avy-erp.avyren.in"

server {
    listen 443 ssl http2;
    server_name *.avy-erp.avyren.in;

    ssl_certificate     /etc/letsencrypt/live/avy-erp.avyren.in/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/avy-erp.avyren.in/privkey.pem;

    # Extract subdomain (company slug)
    set $tenant "";
    if ($host ~* ^([a-z0-9-]+)\.avy-erp\.avyren\.in$) {
        set $tenant $1;
    }

    # Serve the SAME React app for all tenants
    # (The React app detects the subdomain client-side)
    root /var/www/avy-erp/dist;
    index index.html;

    # SPA routing — all paths serve index.html
    location / {
        try_files $uri $uri/ /index.html;
    }

    # API proxy — pass tenant as header
    location /api/ {
        proxy_pass http://localhost:3000;
        proxy_set_header Host $host;
        proxy_set_header X-Tenant-Slug $tenant;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}

# Redirect HTTP → HTTPS
server {
    listen 80;
    server_name *.avy-erp.avyren.in;
    return 301 https://$host$request_uri;
}

# Super Admin panel (separate subdomain)
server {
    listen 443 ssl http2;
    server_name admin.avy-erp.avyren.in;

    ssl_certificate     /etc/letsencrypt/live/avy-erp.avyren.in/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/avy-erp.avyren.in/privkey.pem;

    root /var/www/avy-erp/dist;
    index index.html;

    location / {
        try_files $uri $uri/ /index.html;
    }

    location /api/ {
        proxy_pass http://localhost:3000;
        proxy_set_header Host $host;
        proxy_set_header X-Tenant-Slug admin;
    }
}
```

### 5.4 Web App Changes

#### A. Tenant Detection from Subdomain

Add a utility to extract the tenant slug from the current URL:

```typescript
// src/lib/tenant.ts

export function getTenantSlug(): string | null {
  const hostname = window.location.hostname;

  // Pattern: {slug}.avy-erp.avyren.in
  const match = hostname.match(/^([a-z0-9-]+)\.avy-erp\.avyren\.in$/);
  if (match) {
    const slug = match[1];
    // 'admin' subdomain is for super-admin, not a tenant
    return slug === 'admin' ? null : slug;
  }

  // Development: check for localhost with query param
  if (hostname === 'localhost') {
    const params = new URLSearchParams(window.location.search);
    return params.get('tenant');
  }

  return null;
}

export function isAdminPortal(): boolean {
  return window.location.hostname.startsWith('admin.');
}

export function getTenantPortalUrl(slug: string): string {
  if (import.meta.env.DEV) {
    return `http://localhost:5173?tenant=${slug}`;
  }
  return `https://${slug}.avy-erp.avyren.in`;
}
```

#### B. API Client Update

```typescript
// src/lib/api/client.ts — ADD tenant header

const client = axios.create({
  baseURL: import.meta.env.VITE_API_URL,
  timeout: 10000,
});

client.interceptors.request.use((config) => {
  // Existing: attach JWT token
  const tokens = getStoredTokens();
  if (tokens?.accessToken) {
    config.headers.Authorization = `Bearer ${tokens.accessToken}`;
  }

  // NEW: attach tenant slug from subdomain
  const tenantSlug = getTenantSlug();
  if (tenantSlug) {
    config.headers['X-Tenant-Slug'] = tenantSlug;
  }

  return config;
});
```

#### C. Login Page Behavior

When a user visits `avyren.avy-erp.avyren.in/login`:

```typescript
// src/features/auth/LoginScreen.tsx

function LoginScreen() {
  const tenantSlug = getTenantSlug();

  // If on a tenant subdomain, show company branding
  const { data: tenantBranding } = useQuery({
    queryKey: ['tenant-branding', tenantSlug],
    queryFn: () => api.get(`/public/tenant/${tenantSlug}/branding`),
    enabled: !!tenantSlug,
  });

  return (
    <div>
      {tenantBranding && (
        <img src={tenantBranding.logo} alt={tenantBranding.companyName} />
      )}
      <h1>{tenantBranding?.companyName ?? 'Avy ERP'}</h1>
      <LoginForm />
    </div>
  );
}
```

#### D. Route Guards Update

```typescript
// src/App.tsx — validate tenant match

function TenantGuard({ children }: { children: ReactNode }) {
  const tenantSlug = getTenantSlug();
  const { user } = useAuthStore();

  // If user is on a tenant subdomain but belongs to a different tenant
  if (tenantSlug && user?.tenantSlug && user.tenantSlug !== tenantSlug) {
    return <TenantMismatchError
      expected={tenantSlug}
      actual={user.tenantSlug}
    />;
  }

  // Super-admin can only access admin.avy-erp.avyren.in
  if (user?.role === 'SUPER_ADMIN' && tenantSlug) {
    window.location.href = getTenantPortalUrl('admin');
    return null;
  }

  return children;
}
```

#### E. Super Admin: Company List Links

When super-admin views the company list, each company should link to its subdomain:

```typescript
// In company list screen
<a
  href={`https://${company.slug}.avy-erp.avyren.in`}
  target="_blank"
>
  Open {company.name}'s Portal
</a>
```

### 5.5 Custom Vanity Domains (Future)

Some large customers may want `erp.tatagroup.com` instead of `tatagroup.avy-erp.avyren.in`.

**How it works:**
1. Customer creates a CNAME record: `erp.tatagroup.com → tatagroup.avy-erp.avyren.in`
2. You store the custom domain in the `Tenant` table: `customDomain: 'erp.tatagroup.com'`
3. Nginx handles it:

```nginx
# Custom domain support
server {
    listen 443 ssl http2;
    server_name ~^(?<tenant>.+)$;  # Catch-all

    # Dynamic SSL with Let's Encrypt + certbot
    ssl_certificate     /etc/letsencrypt/live/$host/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/$host/privkey.pem;

    # API call to resolve custom domain → tenant slug
    location = /_internal/resolve-tenant {
        internal;
        proxy_pass http://localhost:3000/api/v1/public/resolve-domain?domain=$host;
    }

    # ... same as before
}
```

4. Backend endpoint to resolve domains:

```typescript
// GET /api/v1/public/resolve-domain?domain=erp.tatagroup.com
app.get('/public/resolve-domain', async (req, res) => {
  const domain = req.query.domain as string;

  const tenant = await prisma.tenant.findFirst({
    where: {
      OR: [
        { customDomain: domain },
        // Also check subdomain pattern
        { slug: domain.split('.')[0] }
      ]
    }
  });

  if (!tenant) return res.status(404).json({ error: 'Unknown domain' });
  res.json({ slug: tenant.slug, schemaName: tenant.schemaName });
});
```

**Recommended: Implement vanity domains only when a customer actually asks for it.** The subdomain approach (`*.avy-erp.avyren.in`) covers 95% of cases.

---

## 6. Pillar 3: Mobile App — Tenant-Aware Client

### 6.1 How Mobile Multi-Tenancy Works

The mobile app is simpler than the web app because:
- **One APK/IPA** for all customers (published on Play Store / App Store)
- **Tenant is determined at login** (from JWT payload), not from the URL
- **No subdomain logic needed** — the app always talks to the same API

```
┌─────────────────────────────────────┐
│           MOBILE APP                │
│                                     │
│  1. User opens app                  │
│  2. Enters email + password         │
│  3. Backend returns JWT with:       │
│     - tenantId                      │
│     - companyId                     │
│     - schemaName                    │
│     - permissions                   │
│  4. All API calls include JWT       │
│  5. Backend middleware routes to    │
│     correct schema automatically    │
│                                     │
│  USER SEES: their company's data    │
│  BACKEND: queries tenant_{slug}     │
└─────────────────────────────────────┘
```

### 6.2 Changes Needed in Mobile App

#### A. Company Branding on Login Screen

```typescript
// src/features/auth/login-screen.tsx

// Optional: Let user enter company code first
// This is useful if you want branded login
function LoginScreen() {
  const [companyCode, setCompanyCode] = useState('');
  const [branding, setBranding] = useState(null);

  // When user enters company code, fetch branding
  const fetchBranding = async (code: string) => {
    const res = await api.get(`/public/tenant/${code}/branding`);
    setBranding(res.data);
  };

  return (
    <View>
      {/* Option 1: Company code field (adds one step) */}
      <TextInput
        placeholder="Company Code"
        onChangeText={setCompanyCode}
        onBlur={() => fetchBranding(companyCode)}
      />

      {branding && <Image source={{ uri: branding.logo }} />}

      {/* Standard email + password */}
      <TextInput placeholder="Email" />
      <TextInput placeholder="Password" secureTextEntry />
      <Button title="Sign In" />
    </View>
  );
}

// Option 2: Skip company code — just email + password
// Backend figures out the tenant from the user's email domain
```

#### B. Tenant Context in Auth Store

Your existing auth store already stores `tenantId` and `companyId` from the JWT. No changes needed here — it works as-is.

#### C. Multi-Company Support (Future)

If a user belongs to multiple companies (e.g., a consultant):

```typescript
// src/features/auth/use-auth-store.ts — future enhancement

interface AuthState {
  // ... existing fields
  availableTenants: TenantInfo[];  // Companies user has access to
  activeTenant: TenantInfo | null; // Currently selected company
}

// After login, if user has multiple tenants:
// Show a company picker screen before navigating to dashboard
```

### 6.3 Deep Linking (Optional)

Allow opening the mobile app directly to a tenant:

```
avyerp://tenant/avyren/dashboard
```

Configure in `app.config.ts`:
```typescript
{
  scheme: 'avyerp',
  // ... handles deep links to specific tenant screens
}
```

---

## 7. Backend Changes Required

### 7.1 New Tenant Table Fields

```prisma
model Tenant {
  id            String       @id @default(cuid())
  slug          String       @unique  // NEW: URL-safe company identifier
  schemaName    String       @unique  // tenant_{slug}
  companyId     String       @unique
  status        TenantStatus
  customDomain  String?      @unique  // NEW: optional vanity domain

  // Branding (NEW)
  logoUrl       String?
  primaryColor  String?      @default("#4A3AFF")

  createdAt     DateTime     @default(now())
  updatedAt     DateTime     @updatedAt

  company       Company      @relation(fields: [companyId], references: [id])
  subscriptions Subscription[]
}
```

### 7.2 Public Endpoints (No Auth Required)

These endpoints are needed for the login page branding:

```typescript
// src/core/tenant/tenant.routes.ts — PUBLIC routes

router.get('/public/tenant/:slug/branding', async (req, res) => {
  const { slug } = req.params;

  const tenant = await prisma.tenant.findUnique({
    where: { slug },
    include: { company: { select: { name: true, domain: true } } }
  });

  if (!tenant) return res.status(404).json({ error: 'Company not found' });

  res.json({
    companyName: tenant.company.name,
    logoUrl: tenant.logoUrl,
    primaryColor: tenant.primaryColor,
  });
});

router.get('/public/resolve-domain', async (req, res) => {
  const domain = req.query.domain as string;

  const tenant = await prisma.tenant.findFirst({
    where: { OR: [{ customDomain: domain }, { slug: domain }] }
  });

  if (!tenant) return res.status(404).json({ error: 'Unknown domain' });
  res.json({ slug: tenant.slug });
});
```

### 7.3 Updated Tenant Middleware

```typescript
// src/middleware/tenant.middleware.ts — ENHANCED

export function tenantMiddleware() {
  return async (req: Request, res: Response, next: NextFunction) => {
    let tenantId: string | undefined;

    // Priority 1: X-Tenant-ID header (existing)
    tenantId = req.headers['x-tenant-id'] as string;

    // Priority 2: X-Tenant-Slug header (NEW — from Nginx/web app)
    if (!tenantId) {
      const slug = req.headers['x-tenant-slug'] as string;
      if (slug) {
        const tenant = await resolveTenantBySlug(slug); // Redis-cached
        tenantId = tenant?.id;
      }
    }

    // Priority 3: Subdomain (existing)
    if (!tenantId) {
      const host = req.hostname;
      const match = host.match(/^([a-z0-9-]+)\.avy-erp\.avyren\.in$/);
      if (match) {
        const tenant = await resolveTenantBySlug(match[1]);
        tenantId = tenant?.id;
      }
    }

    // Priority 4: Custom domain (NEW)
    if (!tenantId) {
      const tenant = await resolveTenantByDomain(req.hostname);
      tenantId = tenant?.id;
    }

    // Priority 5: JWT payload (existing — fallback)
    if (!tenantId && req.user?.tenantId) {
      tenantId = req.user.tenantId;
    }

    if (tenantId) {
      req.tenant = await getTenantContext(tenantId); // Redis-cached
    }

    next();
  };
}
```

### 7.4 Schema Provisioning During Onboarding

When Step 16 (Activation) is completed in the tenant onboarding wizard:

```typescript
// src/core/tenant/tenant.service.ts — onboarding completion

async activateTenant(companyId: string) {
  const company = await prisma.company.findUnique({ where: { id: companyId } });
  const slug = slugify(company.legalName); // e.g., "avyren-technologies"
  const schemaName = `tenant_${slug.replace(/-/g, '_')}`;

  // 1. Provision the database schema
  await tenantProvisioningService.provisionTenant(schemaName, companyId);

  // 2. Update tenant record with slug and schema
  await prisma.tenant.update({
    where: { companyId },
    data: { slug, schemaName, status: 'ACTIVE' }
  });

  // 3. Migrate onboarding data to tenant schema
  // Move departments, shifts, locations etc. from platform → tenant schema
  await this.migrateOnboardingData(companyId, schemaName);

  // 4. Send welcome email with portal URL
  await emailService.sendWelcome({
    to: company.adminEmail,
    portalUrl: `https://${slug}.avy-erp.avyren.in`,
    companyName: company.legalName,
  });
}
```

---

## 8. Infrastructure & DevOps

### 8.1 Architecture Diagram (Production)

```
                    ┌─────────────────────┐
                    │    Cloudflare DNS    │
                    │                     │
                    │ *.avy-erp.avyren.in │
                    │    → Server IP      │
                    └──────────┬──────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │       Nginx         │
                    │                     │
                    │ • Wildcard SSL      │
                    │ • Subdomain extract │
                    │ • Static files      │
                    │ • API proxy         │
                    └──────────┬──────────┘
                               │
              ┌────────────────┼────────────────┐
              │                │                │
              ▼                ▼                ▼
     ┌────────────────┐ ┌───────────┐  ┌───────────┐
     │  React App     │ │  API #1   │  │  API #2   │
     │  (static)      │ │ (Express) │  │ (Express) │
     │                │ │           │  │           │
     │  Same build    │ │ Behind    │  │ Behind    │
     │  for all       │ │ PM2/      │  │ PM2/      │
     │  tenants       │ │ Docker    │  │ Docker    │
     └────────────────┘ └─────┬─────┘  └─────┬─────┘
                              │              │
                              ▼              ▼
                    ┌─────────────────────┐
                    │     PgBouncer       │
                    │   (connection pool) │
                    └──────────┬──────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │    PostgreSQL        │
                    │                     │
                    │  public │ tenant_a  │
                    │         │ tenant_b  │
                    │         │ tenant_c  │
                    └─────────────────────┘

                    ┌─────────────────────┐
                    │       Redis         │
                    │                     │
                    │  • Tenant cache     │
                    │  • Session cache    │
                    │  • Job queue        │
                    └─────────────────────┘
```

### 8.2 Docker Compose (Production)

```yaml
# docker-compose.production.yml

services:
  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx/conf.d:/etc/nginx/conf.d
      - ./web-dist:/var/www/avy-erp/dist     # Built React app
      - /etc/letsencrypt:/etc/letsencrypt     # SSL certs
    depends_on:
      - api
    restart: always

  api:
    build: ./avy-erp-backend
    environment:
      DATABASE_URL: postgres://user:pass@pgbouncer:6432/avyerp?schema=public
      DATABASE_URL_TEMPLATE: postgres://user:pass@pgbouncer:6432/avyerp?schema={schema}
      REDIS_URL: redis://:password@redis:6379/0
    depends_on:
      pgbouncer:
        condition: service_healthy
      redis:
        condition: service_healthy
    deploy:
      replicas: 2  # Run 2 instances for availability
    restart: always

  pgbouncer:
    image: edoburu/pgbouncer:latest
    environment:
      DATABASE_URL: postgres://user:pass@postgres:5432/avyerp
      POOL_MODE: transaction
      MAX_CLIENT_CONN: 1000
      DEFAULT_POOL_SIZE: 50
    depends_on:
      postgres:
        condition: service_healthy
    healthcheck:
      test: ["CMD", "pg_isready", "-h", "localhost", "-p", "6432"]
    restart: always

  postgres:
    image: postgres:18-alpine
    volumes:
      - postgres_data:/var/lib/postgresql/data
    environment:
      POSTGRES_DB: avyerp
      POSTGRES_USER: user
      POSTGRES_PASSWORD: pass
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U user -d avyerp"]
    restart: always
    shm_size: 256mb

  redis:
    image: redis:7-alpine
    volumes:
      - redis_data:/data
    command: redis-server --requirepass password --maxmemory 512mb
    healthcheck:
      test: ["CMD", "redis-cli", "-a", "password", "ping"]
    restart: always

volumes:
  postgres_data:
  redis_data:
```

### 8.3 SSL Certificate (Wildcard)

Use **Cloudflare DNS** + **Let's Encrypt** for free wildcard SSL:

```bash
# Install certbot with Cloudflare plugin
apt install certbot python3-certbot-dns-cloudflare

# Create Cloudflare API token file
echo "dns_cloudflare_api_token = YOUR_CLOUDFLARE_TOKEN" > /etc/cloudflare.ini
chmod 600 /etc/cloudflare.ini

# Get wildcard certificate
certbot certonly \
  --dns-cloudflare \
  --dns-cloudflare-credentials /etc/cloudflare.ini \
  -d "*.avy-erp.avyren.in" \
  -d "avy-erp.avyren.in"

# Auto-renewal (certbot sets up a cron automatically)
```

---

## 9. Migration Strategy

### Phase 1: Backend Foundation (Week 1-2)

```
Step 1: Split Prisma schema into platform.prisma + tenant.prisma
Step 2: Build TenantProvisioningService
Step 3: Build per-tenant migration runner
Step 4: Add slug field to Tenant model
Step 5: Update tenant middleware to support slug resolution
Step 6: Add public branding endpoint
Step 7: Implement Prisma client caching (replace per-request clients)
```

### Phase 2: Web App Custom Domains (Week 3)

```
Step 1: Add getTenantSlug() utility
Step 2: Update API client to send X-Tenant-Slug header
Step 3: Update login page with branding support
Step 4: Add TenantGuard route protection
Step 5: Configure Nginx with wildcard SSL
Step 6: Setup wildcard DNS on Cloudflare
Step 7: Test: create a tenant, visit {slug}.avy-erp.avyren.in
```

### Phase 3: Mobile App Updates (Week 4)

```
Step 1: Optional — add company code on login screen
Step 2: Ensure auth store properly handles tenantId from JWT
Step 3: Test login across different tenants
```

### Phase 4: DevOps Hardening (Week 5)

```
Step 1: Add PgBouncer to docker-compose
Step 2: Update deploy.sh to run tenant migrations
Step 3: Add monitoring for per-tenant query performance
Step 4: Set up automated tenant backup scripts
Step 5: Load test with 50+ tenant schemas
```

---

## 10. Cost & Scaling Considerations

### How Many Tenants Per PostgreSQL Instance?

| Tenants | RAM | CPU | Disk | Notes |
|---------|-----|-----|------|-------|
| 1-50 | 4 GB | 2 vCPU | 50 GB | Single instance is fine |
| 50-200 | 16 GB | 4 vCPU | 200 GB | Add PgBouncer, tune `shared_buffers` |
| 200-500 | 32 GB | 8 vCPU | 500 GB | Consider read replicas |
| 500+ | | | | Shard: move large tenants to their own DB instance |

### Cost per Tenant (Approximate)

| Component | Monthly Cost | Notes |
|-----------|-------------|-------|
| Database storage | ~$0.10/tenant | ~100 MB per tenant avg |
| Connection pooling | Shared | PgBouncer handles this |
| Redis cache | ~$0.01/tenant | ~5 MB per tenant cache |
| SSL certificate | Free | Let's Encrypt wildcard |
| DNS | Free / $5 | Cloudflare free tier works |
| Nginx | Shared | One instance for all |
| **Total marginal cost** | **~$0.15/tenant/month** | Infrastructure only |

### When to Split to Separate Databases

Move a tenant to its own database when:
- They have >100K employees
- They need data residency in a specific region (GDPR, data localization)
- They need dedicated performance guarantees (SLA)
- They request it (enterprise customers)

The schema-per-tenant approach makes this migration easy:
```bash
# Export one tenant's schema
pg_dump -n tenant_tatagroup avyerp > tatagroup_backup.sql

# Import into dedicated instance
psql -h tata-dedicated.rds.amazonaws.com -d tatagroup < tatagroup_backup.sql

# Update tenant record to point to new database
UPDATE "Tenant" SET "databaseUrl" = 'postgres://...' WHERE slug = 'tatagroup';
```

---

## 11. Security Implications

### Data Isolation

| Risk | Mitigation |
|------|-----------|
| Cross-tenant data access | PostgreSQL schema isolation + `SET search_path` ensures queries can't cross schemas |
| SQL injection crossing schemas | Prisma ORM parameterizes all queries. Never use `$executeRawUnsafe` with user input for schema names |
| Tenant impersonation | JWT contains tenantId, verified server-side. Subdomain only used for branding, never for authorization |
| Shared cache poisoning | Redis keys prefixed with `tenant:{tenantId}:` to prevent cross-tenant cache access |
| Backup data exposure | Per-tenant `pg_dump` ensures backups contain only one tenant's data |

### Authentication Security

```
Login Flow with Tenant Context:
1. User visits avyren.avy-erp.avyren.in/login
2. Enters email + password
3. Backend finds user by email
4. Checks user.companyId matches the tenant for this subdomain
5. If mismatch → "Invalid credentials" (don't reveal tenant info)
6. If match → issue JWT with tenantId + companyId
7. All subsequent requests use JWT for tenant resolution (not subdomain)
```

**Important:** The subdomain is used for UX (branding, login routing) but NEVER for authorization. Authorization always comes from the JWT.

### Recommendations

1. **Add rate limiting per tenant** (not just global) — prevent one tenant from consuming all resources
2. **Tenant-scoped Redis keys** — always prefix with `tenant:{id}:` to avoid key collisions
3. **Audit log tenant isolation** — ensure audit logs are scoped to the tenant's schema
4. **Schema name validation** — only allow `[a-z0-9_]` in schema names, validated before any SQL execution

---

## 12. Recommended Roadmap

```
                         NOW            MONTH 1          MONTH 2          FUTURE
                          │                │                │               │
  ┌───────────────────────┼────────────────┼────────────────┼───────────────┤
  │                       │                │                │               │
  │  BACKEND              │                │                │               │
  │  ────────             │                │                │               │
  │  • Split Prisma       ├── Done ──┐     │                │               │
  │    schemas             │          │     │                │               │
  │  • Schema provisioning │         Done   │                │               │
  │  • Cached Prisma       │                │                │               │
  │    clients             │                │                │               │
  │  • Slug field +        │                │                │               │
  │    branding endpoint   │                │                │               │
  │                        │                │                │               │
  │  WEB APP               │                │                │               │
  │  ────────              │                │                │               │
  │  • Subdomain detection │                ├── Done ──┐     │               │
  │  • Branded login       │                │          │     │               │
  │  • Nginx wildcard      │                │         Done   │               │
  │  • TenantGuard         │                │                │               │
  │                        │                │                │               │
  │  MOBILE APP            │                │                │               │
  │  ──────────            │                │                │               │
  │  • Company branding    │                │                ├── Done ──┐    │
  │    on login            │                │                │          │    │
  │                        │                │                │          │    │
  │  DEVOPS                │                │                │          │    │
  │  ──────                │                │                │         Done  │
  │  • PgBouncer           │                │                │               │
  │  • Wildcard SSL        │                │                │               │
  │  • Tenant backup       │                │                │               │
  │    scripts             │                │                │               │
  │                        │                │                │               │
  │  FUTURE                │                │                │               │
  │  ──────                │                │                │               │
  │  • Vanity domains      │                │                │          Future
  │  • Multi-company users │                │                │               │
  │  • Regional sharding   │                │                │               │
  └────────────────────────┴────────────────┴────────────────┴───────────────┘
```

### Priority Order

1. **Backend: Split Prisma schemas** — This is the foundation. Everything else depends on it.
2. **Backend: Schema provisioning** — Automated tenant creation during onboarding.
3. **Backend: Cached Prisma clients** — Performance requirement before going multi-tenant.
4. **DevOps: Nginx + Wildcard SSL** — Infrastructure for custom domains.
5. **Web: Subdomain detection + branding** — Customer-facing feature.
6. **Mobile: Branded login** — Nice-to-have, not blocking.
7. **Future: Vanity domains, multi-company users** — Only when customers ask.

---

## Quick Reference Card

| Question | Answer |
|----------|--------|
| **What domain format?** | `{company-slug}.avy-erp.avyren.in` |
| **Where is tenant data?** | PostgreSQL schema `tenant_{slug}` |
| **Where is platform data?** | PostgreSQL `public` schema |
| **How does web detect tenant?** | `window.location.hostname` → extract subdomain |
| **How does mobile detect tenant?** | JWT payload after login → `tenantId` |
| **How does backend resolve tenant?** | Middleware: header → subdomain → JWT (priority order) |
| **Is subdomain used for auth?** | NO — only for UX/branding. JWT is the authority. |
| **One app build per tenant?** | NO — same React build, same APK for all tenants |
| **How to add a new tenant?** | Onboarding wizard → Activation step → auto-provisions schema + subdomain |
| **How to migrate all tenants?** | `scripts/migrate-all-tenants.ts` loops through all active tenants |
| **Connection pooling?** | PgBouncer in transaction mode + cached Prisma clients |
| **SSL for wildcards?** | Let's Encrypt + Cloudflare DNS validation |
