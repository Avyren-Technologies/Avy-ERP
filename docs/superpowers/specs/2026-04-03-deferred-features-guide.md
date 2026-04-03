# Deferred Features Implementation Guide

**Date:** 2026-04-03
**Status:** Draft (Not Yet Scheduled)
**Parent Spec:** `docs/superpowers/specs/2026-04-02-hybrid-multi-tenancy-subdomain-routing-design.md`
**Scope:** Backend, Web App, Infrastructure

These two features were explicitly deferred in the hybrid multi-tenancy design spec (Non-Goals section). The foundational model fields (`customDomain`, `dbStrategy`, `databaseUrl`) already exist on the `Tenant` model and the `TenantConnectionManager` already branches on `dbStrategy`. This document provides step-by-step implementation guides for when each feature is needed.

---

## 1. Custom Domain Support

### Overview

Allow premium tenants to use their own domain (e.g., `erp.clientcorp.com`) instead of the default `<slug>.avyren.in` subdomain. The `customDomain` nullable field already exists on the `Tenant` model in `prisma/modules/platform/tenant.prisma`.

### Prerequisites

- The `customDomain String? @unique` field already exists on the Tenant model
- Cloudflare is already managing DNS for `avyren.in` with wildcard CNAME
- Tenant middleware already resolves tenants by slug, ID, header, query, and JWT
- Web app's `detectTenant()` in `web-system-app/src/lib/tenant.ts` already has an "unknown domain" fallback branch

### Architecture

```
Tenant requests custom domain via Company Admin panel
    |
    v
Backend generates DNS verification token
    |
    v
Tenant adds CNAME + TXT records at their DNS provider
    |
    v
Backend verifies DNS propagation (TXT record check)
    |
    v
On success: Tenant.customDomain is set, SSL provisioned via Cloudflare
    |
    v
Tenant middleware resolves requests from custom domain to correct tenant
    |
    v
Web app detects non-avyren.in hostname, calls backend to resolve tenant
```

### Implementation Steps

#### Step 1: Backend — Domain Verification Model & Endpoints

**New Prisma model** — add to `prisma/modules/platform/tenant.prisma`:

```prisma
model DomainVerification {
  id          String                   @id @default(cuid())
  tenantId    String
  domain      String                   @unique
  verifyToken String
  status      DomainVerificationStatus @default(PENDING)
  verifiedAt  DateTime?
  expiresAt   DateTime                 // Token expiry (e.g., 72 hours)
  createdAt   DateTime                 @default(now())
  updatedAt   DateTime                 @updatedAt

  tenant Tenant @relation(fields: [tenantId], references: [id], onDelete: Cascade)

  @@map("domain_verifications")
}

enum DomainVerificationStatus {
  PENDING
  VERIFIED
  FAILED
  EXPIRED
}
```

Add the reverse relation to the existing `Tenant` model:

```prisma
// In Tenant model, add:
domainVerifications DomainVerification[]
```

**New files:**

```
avy-erp-backend/src/core/company-admin/custom-domain/
  custom-domain.validators.ts    # Zod schemas
  custom-domain.service.ts       # Business logic
  custom-domain.controller.ts    # Controller
  custom-domain.routes.ts        # Routes (mounted under /company/custom-domain)
```

**Endpoints:**

| Method | Path | Purpose | Auth |
|--------|------|---------|------|
| `POST` | `/company/custom-domain` | Request custom domain setup | Company Admin |
| `GET` | `/company/custom-domain` | Get current domain & verification status | Company Admin |
| `POST` | `/company/custom-domain/verify` | Trigger DNS verification check | Company Admin |
| `DELETE` | `/company/custom-domain` | Remove custom domain | Company Admin |
| `GET` | `/auth/resolve-domain?domain=<domain>` | Resolve domain to tenant (public) | None |

**Service logic for `POST /company/custom-domain`:**

```typescript
async requestCustomDomain(companyId: string, tenantId: string, domain: string) {
  // 1. Validate domain format (no IP, no avyren.in subdomain, valid hostname)
  // 2. Check domain not already claimed by another tenant
  // 3. Generate verification token: crypto.randomBytes(32).toString('hex')
  // 4. Create DomainVerification record (status: PENDING, expiresAt: now + 72h)
  // 5. Return DNS instructions:
  //    - CNAME: domain → custom.avyren.in (or proxy target)
  //    - TXT: _avyerp-verify.<domain> → avyerp-verify=<token>
}
```

**Service logic for `POST /company/custom-domain/verify`:**

```typescript
async verifyCustomDomain(tenantId: string) {
  // 1. Find PENDING DomainVerification for tenant
  // 2. Check expiry — if expired, mark EXPIRED and require re-request
  // 3. DNS lookup: resolve TXT record for _avyerp-verify.<domain>
  //    Use Node.js dns.promises.resolveTxt()
  // 4. If TXT contains avyerp-verify=<token>:
  //    - Update DomainVerification.status = VERIFIED, verifiedAt = now
  //    - Update Tenant.customDomain = domain
  //    - Invalidate Redis cache for tenant
  //    - Return success
  // 5. If not found: return { verified: false, message: 'DNS record not found. Propagation can take up to 48 hours.' }
}
```

#### Step 2: Backend — Tenant Resolution by Custom Domain

Update `extractTenantFromRequest()` in `src/middleware/tenant.middleware.ts` to add custom domain lookup between the header and subdomain priorities:

```typescript
function extractTenantFromRequest(req: Request): { tenantId: string; method: string } | null {
  // Priority 1: Custom header (X-Tenant-ID) — unchanged
  const tenantHeader = req.headers['x-tenant-id'] as string;
  if (tenantHeader) return { tenantId: tenantHeader, method: 'header' };

  // Priority 2: Custom domain lookup (NEW)
  const host = req.headers.host?.split(':')[0];
  if (host && !isKnownDomain(host)) {
    // Not an avyren.in domain — could be a custom domain
    const tenantId = await resolveCustomDomain(host);
    if (tenantId) return { tenantId, method: 'custom-domain' };
  }

  // Priority 3: Subdomain — unchanged
  // Priority 4: Query parameter — unchanged
  // Priority 5: Path parameter — unchanged
  // Priority 6: JWT — unchanged
}
```

**Custom domain Redis cache:**

```typescript
async function resolveCustomDomain(domain: string): Promise<string | null> {
  const cacheKey = `avy:erp-backend:custom-domain:${domain}`;
  const cached = await cacheRedis.get(cacheKey);
  if (cached) return cached === 'null' ? null : cached;

  const tenant = await platformPrisma.tenant.findUnique({
    where: { customDomain: domain },
    select: { id: true },
  });

  // Cache for 1 hour (cache 'null' too, to prevent repeated DB lookups for invalid domains)
  await cacheRedis.setex(cacheKey, 3600, tenant?.id ?? 'null');
  return tenant?.id ?? null;
}

function isKnownDomain(host: string): boolean {
  const mainDomain = env.MAIN_DOMAIN;
  return host === mainDomain
    || host.endsWith(`.${mainDomain}`)
    || host === 'localhost'
    || /^(\d{1,3}\.){3}\d{1,3}$/.test(host);
}
```

**Cache invalidation:** When a custom domain is added or removed, delete the cache key:

```typescript
await cacheRedis.del(`avy:erp-backend:custom-domain:${domain}`);
```

#### Step 3: Cloudflare — SSL for Custom Domains

Three options, ordered by recommendation:

**Option A: Cloudflare Tunnel (Recommended — start here)**
- Free tier available
- Route custom domains through a Cloudflare Tunnel to your origin
- Cloudflare handles SSL termination automatically
- Tenant adds a CNAME pointing to your tunnel hostname
- No server-side certificate management
- Limitation: requires Cloudflare Tunnel daemon running on your server

**Option B: Cloudflare for SaaS (SSL for SaaS)**
- Requires Cloudflare Business plan ($200/month) or Enterprise
- Purpose-built for this use case: tenants point CNAME to your zone, Cloudflare auto-provisions SSL
- API-driven: `POST /zones/:zone/custom_hostnames` to register each tenant domain
- Best experience but highest cost
- Upgrade to this when monthly revenue justifies the $200/month

**Option C: Let's Encrypt with certbot**
- Free, but requires server-side certificate management
- Certbot auto-renews certificates every 90 days
- Must run on a server you control (not serverless)
- Works well with Nginx reverse proxy
- Operational burden: cert renewal monitoring, storage, rotation

**Recommendation:** Start with Option A (Cloudflare Tunnel). It is free, handles SSL automatically, and requires minimal infrastructure changes. Upgrade to Option B when you have 10+ custom domain tenants and revenue supports the cost.

#### Step 4: Web App — Custom Domain Detection

Update `web-system-app/src/lib/tenant.ts` to handle custom domains:

```typescript
export function detectTenant(): TenantContext {
  const hostname = window.location.hostname;

  // Development — unchanged
  if (hostname === 'localhost' || hostname === '127.0.0.1') {
    const params = new URLSearchParams(window.location.search);
    const devSlug = params.get('tenant');
    if (devSlug === 'admin') return { mode: 'admin', slug: null };
    if (devSlug) return { mode: 'tenant', slug: devSlug };
    return { mode: 'main', slug: null };
  }

  // Main domain
  if (hostname === MAIN_DOMAIN) {
    return { mode: 'main', slug: null };
  }

  // Subdomain of main domain — unchanged
  if (hostname.endsWith(`.${MAIN_DOMAIN}`)) {
    const slug = hostname.replace(`.${MAIN_DOMAIN}`, '');
    if (slug === 'admin') return { mode: 'admin', slug: null };
    if (RESERVED_SLUGS.has(slug)) return { mode: 'main', slug: null };
    return { mode: 'tenant', slug };
  }

  // NEW: Unknown domain — could be a custom domain
  // Return a special mode; the app will call /auth/resolve-domain to verify
  return { mode: 'custom-domain', slug: null, customDomain: hostname };
}
```

Update the `TenantContext` type and `AppMode`:

```typescript
export type AppMode = 'main' | 'admin' | 'tenant' | 'custom-domain';

export interface TenantContext {
  mode: AppMode;
  slug: string | null;
  customDomain?: string;  // Only set when mode === 'custom-domain'
}
```

**Resolution flow in the app (e.g., in `App.tsx` or a provider):**

```typescript
// When mode === 'custom-domain':
// 1. Check sessionStorage for cached resolution
// 2. If not cached, call GET /auth/resolve-domain?domain=<hostname>
// 3. On success: cache { slug, companyName, logoUrl } in sessionStorage
// 4. Treat as mode 'tenant' with the resolved slug
// 5. On failure (domain not found): show 404 page
```

#### Step 5: DNS Setup (Per Tenant)

When a tenant wants to use `erp.clientcorp.com`:

1. Tenant goes to Company Admin > Settings > Custom Domain
2. Enters `erp.clientcorp.com`
3. Backend generates verification instructions:
   - Add CNAME: `erp.clientcorp.com` -> `custom.avyren.in` (or tunnel hostname)
   - Add TXT: `_avyerp-verify.erp.clientcorp.com` -> `avyerp-verify=a1b2c3d4...`
4. Tenant configures DNS at their provider
5. Tenant clicks "Verify" in the UI
6. Backend checks DNS propagation via `dns.promises.resolveTxt()`
7. On success: domain activated, SSL provisioned automatically via Cloudflare

### API Endpoints Summary

| Method | Path | Auth | Purpose |
|--------|------|------|---------|
| `POST` | `/company/custom-domain` | Company Admin | Request custom domain |
| `GET` | `/company/custom-domain` | Company Admin | Get status |
| `POST` | `/company/custom-domain/verify` | Company Admin | Check DNS & activate |
| `DELETE` | `/company/custom-domain` | Company Admin | Remove custom domain |
| `GET` | `/auth/resolve-domain?domain=<d>` | Public (rate-limited) | Resolve domain to tenant |

### Security Considerations

- **DNS verification prevents domain hijacking:** A tenant cannot claim a domain they do not control because they cannot add the required TXT record.
- **Rate limit the resolve-domain endpoint:** 10 requests per minute per IP to prevent enumeration.
- **Validate domain format:** Reject bare TLDs, IP addresses, avyren.in subdomains, and domains with invalid characters.
- **Periodic re-verification:** Run a weekly cron to re-check DNS for all custom domains. If the CNAME or TXT record is removed, flag the domain as `EXPIRED` and revert the tenant to subdomain-only access after a grace period (e.g., 7 days).
- **Negative caching:** Cache `domain -> null` mappings in Redis to prevent repeated DB lookups for random domain probes.
- **CORS:** Add the custom domain to allowed origins dynamically. The CORS validator should check `Tenant.customDomain` for the requesting origin.

### Estimated Effort

| Area | Days |
|------|------|
| Backend (model, service, endpoints, DNS verification) | 3-4 |
| Tenant middleware update + Redis caching | 1 |
| Web app (detection, resolution, UI) | 1-2 |
| Infrastructure (Cloudflare Tunnel or SSL for SaaS setup) | 1 |
| Testing & edge cases | 1-2 |
| **Total** | **7-10 days** |

---

## 2. Database-Per-Tenant

### Overview

Allow high-value tenants to have their own dedicated PostgreSQL database instead of sharing the single database with per-schema isolation. The infrastructure for this already exists in code: `Tenant.dbStrategy` defaults to `"schema"` and `TenantConnectionManager.buildConnectionString()` in `src/config/tenant-connection-manager.ts` already branches on `dbStrategy === 'database'` to use `Tenant.databaseUrl`.

### Prerequisites

- `dbStrategy String @default("schema")` field exists on Tenant model
- `databaseUrl String?` field exists on Tenant model
- `TenantConnectionManager` in `src/config/tenant-connection-manager.ts` already handles the `database` strategy:
  ```typescript
  if (tenant.dbStrategy === 'database' && tenant.databaseUrl) {
    return withDefaultConnectionParams(tenant.databaseUrl);
  }
  ```
- Tenant middleware already passes `dbStrategy` and `databaseUrl` to the connection manager
- PgBouncer is deployed via Docker

### When to Use

| Trigger | Example |
|---------|---------|
| Compliance / data residency | Tenant requires data stored in a specific region or physical isolation for audit |
| Scale | Tenant has millions of rows causing query slowdowns on the shared DB |
| Custom backup/restore | Tenant needs independent backup schedules or point-in-time recovery |
| DB-level tuning | Tenant needs custom `work_mem`, `shared_buffers`, or extensions |
| Contractual | Enterprise contract mandates dedicated infrastructure |

**Do NOT use for:** tenants with fewer than 1 million rows, tenants without explicit isolation requirements, or tenants on starter/growth tiers.

### Architecture

```
Default: Schema-Per-Tenant (shared database)
=============================================

PostgreSQL (single instance)
  ├── public          (platform tables)
  ├── tenant_acme     (Tenant A data)
  ├── tenant_globex   (Tenant B data)
  └── tenant_initech  (Tenant C data)

PgBouncer → single DB → schema selected per request


Premium: Database-Per-Tenant (dedicated database)
==================================================

PostgreSQL Instance 1 (shared)          PostgreSQL Instance 2 (dedicated)
  ├── public (platform)                   └── public (Tenant D data)
  ├── tenant_acme
  └── tenant_globex

PgBouncer → routes to correct DB based on Tenant.databaseUrl
```

### Implementation Steps

#### Step 1: Database Provisioning Service

**New file:** `avy-erp-backend/src/infrastructure/database/tenant-db-provisioner.ts`

```typescript
interface ProvisionResult {
  databaseUrl: string;
  host: string;
  port: number;
  dbName: string;
}

class TenantDbProvisioner {
  /**
   * Provision a new dedicated database for a tenant.
   * Supports two modes:
   *   - 'local': Create a new database on the same PostgreSQL server
   *   - 'managed': Use cloud provider API (AWS RDS, etc.)
   */
  async provision(tenantSlug: string, mode: 'local' | 'managed'): Promise<ProvisionResult> {
    const dbName = `avy_tenant_${tenantSlug.replace(/-/g, '_')}`;

    if (mode === 'local') {
      return this.provisionLocal(dbName);
    }
    return this.provisionManaged(dbName);
  }

  private async provisionLocal(dbName: string): Promise<ProvisionResult> {
    // Connect to the default 'postgres' database to run CREATE DATABASE
    // Use a superuser or a role with CREATEDB privilege
    // CREATE DATABASE <dbName> OWNER avy_app;
    // Return the connection URL
  }

  private async provisionManaged(dbName: string): Promise<ProvisionResult> {
    // For AWS RDS: use @aws-sdk/client-rds to create a new DB instance
    // For Hetzner: use their API
    // For DigitalOcean: use their managed DB API
    // Wait for instance to be available
    // Return the connection URL
  }

  /**
   * Run Prisma migrations against a dedicated database.
   */
  async migrate(databaseUrl: string): Promise<void> {
    // Option A: Shell out to prisma migrate deploy
    // execSync(`DATABASE_URL="${databaseUrl}" npx prisma migrate deploy`)
    //
    // Option B: Use Prisma's programmatic API (if available)
  }

  /**
   * Seed initial data (company settings, default configs).
   */
  async seed(databaseUrl: string, companyId: string): Promise<void> {
    // Create a temporary PrismaClient connected to the new DB
    // Insert default records (attendance rules, leave types, etc.)
  }

  /**
   * Deprovision: drop the database (use with extreme caution).
   */
  async deprovision(dbName: string): Promise<void> {
    // Terminate active connections
    // DROP DATABASE <dbName>
  }
}
```

#### Step 2: Migration Strategy

**Scenario A: New tenant starts with a dedicated database (simpler)**

```
1. Super admin selects "Dedicated Database" during onboarding wizard
2. TenantDbProvisioner.provision(slug, 'local')
3. TenantDbProvisioner.migrate(databaseUrl)
4. TenantDbProvisioner.seed(databaseUrl, companyId)
5. Update Tenant:
   - dbStrategy = 'database'
   - databaseUrl = '<new connection string>'
   - schemaName = 'public' (uses public schema in the dedicated DB)
6. Invalidate Redis tenant cache
7. Tenant is live on dedicated DB
```

**Scenario B: Migrate existing tenant from schema to dedicated database (complex)**

```
1. Notify tenant of upcoming maintenance window (brief downtime)
2. TenantDbProvisioner.provision(slug, 'local')
3. TenantDbProvisioner.migrate(databaseUrl) — creates empty schema
4. Export tenant data from shared DB:
   pg_dump -U avy_admin -n "tenant_<slug>" --no-owner avy_erp > /tmp/tenant_export.sql
5. Transform schema references (tenant_<slug> → public):
   sed -i 's/tenant_<slug>/public/g' /tmp/tenant_export.sql
6. Import into dedicated DB:
   psql -U avy_admin -d avy_tenant_<slug> < /tmp/tenant_export.sql
7. Verify row counts match between source and target
8. Begin maintenance window:
   a. Set Tenant.status = SUSPENDED (blocks new requests)
   b. Wait for in-flight requests to drain (30 seconds)
   c. Re-export any rows created during the drain window (delta sync)
   d. Update Tenant: dbStrategy='database', databaseUrl='...', schemaName='public'
   e. Invalidate all Redis caches for this tenant
   f. Set Tenant.status = ACTIVE
9. End maintenance window
10. Verify tenant can log in and access data
11. After 7-day grace period: DROP SCHEMA "tenant_<slug>" CASCADE from shared DB
```

#### Step 3: Connection Manager Updates

**No code changes needed.** The `TenantConnectionManager` in `src/config/tenant-connection-manager.ts` already handles this:

```typescript
function buildConnectionString(tenant: TenantConnectionInfo): string {
  if (tenant.dbStrategy === 'database' && tenant.databaseUrl) {
    // Uses dedicated database URL
    return withDefaultConnectionParams(tenant.databaseUrl);
  }
  // Uses shared DB with schema from DATABASE_URL_TEMPLATE
  const base = env.DATABASE_URL_TEMPLATE.replace('{schema}', tenant.schemaName);
  return withDefaultConnectionParams(base);
}
```

The tenant middleware in `src/middleware/tenant.middleware.ts` already passes `dbStrategy` and `databaseUrl` from the cached tenant data to the connection manager. When `dbStrategy` is changed to `'database'` and `databaseUrl` is set, the next request after cache invalidation will automatically route to the dedicated DB.

#### Step 4: Migration Runner Update

The existing `pnpm db:migrate-tenants` CLI must be updated to handle dedicated databases:

```typescript
// In scripts/migrate-tenants.ts

for (const tenant of tenants) {
  if (tenant.dbStrategy === 'database' && tenant.databaseUrl) {
    // Run migrations against dedicated database
    await runMigration(tenant.databaseUrl, 'public');
  } else {
    // Run migrations against shared DB with tenant schema
    await runMigration(sharedDbUrl, tenant.schemaName);
  }
}
```

#### Step 5: Backup & Restore

**Schema tenants (default):**
- Backed up together with the shared database (`pg_dump` of entire DB)
- Single backup schedule, single restore procedure
- No per-tenant backup configuration needed

**Database tenants (dedicated):**
- Each dedicated DB needs its own backup schedule
- Options:
  - **pg_dump cron:** Run nightly per dedicated DB, store in S3/object storage
  - **Managed DB snapshots:** If using AWS RDS or similar, use automated snapshots
  - **WAL archiving:** For point-in-time recovery on self-hosted

**Backup tracking table** (add to platform DB):

```prisma
model TenantBackup {
  id         String   @id @default(cuid())
  tenantId   String
  type       String   // 'full' | 'incremental'
  status     String   // 'running' | 'completed' | 'failed'
  storagePath String? // S3 path or local path
  sizeBytes  BigInt?
  startedAt  DateTime
  completedAt DateTime?
  error      String?
  createdAt  DateTime @default(now())

  tenant Tenant @relation(fields: [tenantId], references: [id])

  @@map("tenant_backups")
}
```

#### Step 6: Monitoring & Alerting

For each dedicated database, monitor:

| Metric | Alert Threshold | Tool |
|--------|----------------|------|
| Connection count | > 80% of max_connections | pg_stat_activity |
| Disk usage | > 80% capacity | df / cloud monitoring |
| Query latency (p95) | > 500ms | pg_stat_statements |
| Replication lag | > 60 seconds | pg_stat_replication |
| Failed backups | Any failure | Backup cron exit code |
| Dead tuples | > 10% of live tuples | pg_stat_user_tables |

**Dashboard additions (Super Admin):**
- List of dedicated DB tenants with status indicators
- Per-DB metrics: connections, disk, last backup time
- Quick actions: trigger backup, view connection info

### Migration Script Template

```bash
#!/bin/bash
# migrate-tenant-to-dedicated-db.sh
# Usage: ./migrate-tenant-to-dedicated-db.sh <tenant-slug>

set -euo pipefail

TENANT_SLUG="$1"
DB_NAME="avy_tenant_${TENANT_SLUG//-/_}"
SCHEMA_NAME="tenant_${TENANT_SLUG//-/_}"
SHARED_DB="avy_erp"
DB_USER="avy_admin"
DB_HOST="localhost"
DB_PORT="5432"
EXPORT_DIR="/tmp/tenant-migration-${TENANT_SLUG}"

echo "=== Migrating tenant '${TENANT_SLUG}' to dedicated database ==="

# 1. Create export directory
mkdir -p "${EXPORT_DIR}"

# 2. Create new database
echo "Creating database ${DB_NAME}..."
createdb -U "${DB_USER}" -h "${DB_HOST}" -p "${DB_PORT}" "${DB_NAME}"

# 3. Run Prisma migrations on new database
echo "Running migrations..."
DATABASE_URL="postgresql://${DB_USER}@${DB_HOST}:${DB_PORT}/${DB_NAME}?schema=public" \
  npx prisma migrate deploy

# 4. Export tenant data from shared DB
echo "Exporting tenant data from schema ${SCHEMA_NAME}..."
pg_dump -U "${DB_USER}" -h "${DB_HOST}" -p "${DB_PORT}" \
  -n "${SCHEMA_NAME}" --no-owner --no-privileges \
  "${SHARED_DB}" > "${EXPORT_DIR}/tenant_data.sql"

# 5. Transform schema references (tenant_slug → public)
echo "Transforming schema references..."
sed "s/${SCHEMA_NAME}/public/g" "${EXPORT_DIR}/tenant_data.sql" > "${EXPORT_DIR}/tenant_data_transformed.sql"

# 6. Import into new database
echo "Importing data into ${DB_NAME}..."
psql -U "${DB_USER}" -h "${DB_HOST}" -p "${DB_PORT}" \
  "${DB_NAME}" < "${EXPORT_DIR}/tenant_data_transformed.sql"

# 7. Verify row counts (spot check key tables)
echo "Verifying data integrity..."
for TABLE in employees departments attendance_records leave_requests; do
  SOURCE_COUNT=$(psql -U "${DB_USER}" -h "${DB_HOST}" -p "${DB_PORT}" -t -c \
    "SELECT count(*) FROM ${SCHEMA_NAME}.${TABLE};" "${SHARED_DB}" 2>/dev/null || echo "0")
  TARGET_COUNT=$(psql -U "${DB_USER}" -h "${DB_HOST}" -p "${DB_PORT}" -t -c \
    "SELECT count(*) FROM public.${TABLE};" "${DB_NAME}" 2>/dev/null || echo "0")
  echo "  ${TABLE}: source=${SOURCE_COUNT// /} target=${TARGET_COUNT// /}"
done

# 8. Update tenant record (run manually after verification)
echo ""
echo "=== Manual steps remaining ==="
echo "1. Verify row counts above match"
echo "2. Run the following SQL on the platform DB:"
echo "   UPDATE tenants SET db_strategy='database',"
echo "     database_url='postgresql://${DB_USER}@${DB_HOST}:${DB_PORT}/${DB_NAME}?schema=public',"
echo "     schema_name='public'"
echo "   WHERE slug='${TENANT_SLUG}';"
echo ""
echo "3. Invalidate Redis cache:"
echo "   redis-cli KEYS 'avy:erp-backend:tenant:*' | xargs redis-cli DEL"
echo ""
echo "4. Test tenant login at https://${TENANT_SLUG}.avyren.in"
echo "5. After 7 days, drop the old schema:"
echo "   DROP SCHEMA \"${SCHEMA_NAME}\" CASCADE;"

# 9. Cleanup
rm -rf "${EXPORT_DIR}"
echo ""
echo "=== Migration export complete ==="
```

### PgBouncer Considerations

When adding dedicated databases, PgBouncer configuration needs updates:

**Option A: Single PgBouncer instance (simpler)**
- Add each dedicated DB to PgBouncer's `databases` section in `pgbouncer.ini`
- Connection strings in `Tenant.databaseUrl` point through PgBouncer
- Limitation: all DBs must be on the same PostgreSQL server (or PgBouncer must have network access to all)

**Option B: PgBouncer per database (isolated)**
- Spin up a separate PgBouncer container per dedicated DB
- More resource usage but better isolation
- Only needed when dedicated DBs are on separate servers

**Recommendation:** Start with Option A. Only move to per-DB PgBouncer when dedicated databases are on separate hosts.

### Super Admin UI

Add to the tenant detail screen in the super admin panel:

- **Database Strategy** dropdown: "Shared Schema" (default) | "Dedicated Database"
- When switching to "Dedicated Database":
  - Show a confirmation modal explaining the implications (cost, management overhead)
  - If the tenant has existing data (schema strategy), show a migration wizard with progress steps
  - If this is a new tenant, provision directly during onboarding
- **Connection Info** panel (read-only, visible only for dedicated DB tenants):
  - Database host, port, name
  - Connection status (green/red indicator)
  - Last backup timestamp
  - Disk usage (if available)

### Operational Considerations

| Factor | Shared Schema | Dedicated Database |
|--------|--------------|-------------------|
| Cost per tenant | $0 (shared infra) | $5-50/month (depending on managed vs. self-hosted) |
| Backup complexity | Single backup for all | Individual backup per DB |
| Migration deployment | `pnpm db:migrate-tenants` covers all | Must iterate over dedicated DBs too |
| Monitoring | Single dashboard | N dashboards (or aggregated) |
| Connection limits | Shared pool via PgBouncer | Separate pool per DB |
| Data isolation | Schema-level (logical) | Database-level (physical) |
| Performance isolation | Shared I/O, CPU, memory | Fully isolated (if separate server) |
| Tenant onboarding time | ~5 seconds (CREATE SCHEMA) | ~30-120 seconds (CREATE DATABASE + migrate + seed) |

### Database Changes

No schema changes needed for the core feature. The `dbStrategy` and `databaseUrl` fields already exist on the `Tenant` model. Optional additions:

- `TenantBackup` model (see Step 5 above) for backup tracking
- Super admin navigation manifest entry for the dedicated DB management screen

### Security Considerations

- **Unique credentials per dedicated DB:** Do not reuse the shared DB credentials. Create a dedicated database user per tenant DB with limited privileges.
- **Credential rotation:** Implement a quarterly rotation schedule. Store credentials in a secrets manager (e.g., AWS Secrets Manager, HashiCorp Vault), not in the `databaseUrl` field directly. Use environment variable references or encrypted storage.
- **Network isolation:** If on cloud, place each dedicated DB in a VPC/subnet. Use security groups to restrict access to the application server only.
- **Encrypted connections:** Enforce `sslmode=require` (or `verify-full`) in all dedicated DB connection strings.
- **Audit logging:** Log all provisioning, migration, and deprovisioning actions to the platform audit log.
- **Access control:** Only `SUPER_ADMIN` can change a tenant's `dbStrategy`. Company admins cannot modify their own database configuration.

### Estimated Effort

| Task | Days |
|------|------|
| Provisioning service (`tenant-db-provisioner.ts`) | 2-3 |
| Migration tooling (schema-to-database script) | 3-5 |
| Migration runner update (`db:migrate-tenants`) | 1 |
| Backup infrastructure & tracking | 2-3 |
| Monitoring & alerting setup | 2 |
| Super admin UI (tenant detail + migration wizard) | 2-3 |
| PgBouncer configuration updates | 1 |
| Integration testing (full lifecycle) | 3-5 |
| **Total** | **16-23 days (~3-4 weeks)** |

### Recommendation

**Do NOT implement until you have a concrete customer requirement.** The schema-per-tenant approach handles 100+ tenants well on a single PostgreSQL instance with PgBouncer. Only invest in database-per-tenant when one or more of the following conditions are met:

1. **Compliance mandate:** A customer has regulatory or contractual requirements mandating physical data isolation (e.g., GDPR data residency, SOC 2 Type II, healthcare HIPAA).
2. **Scale threshold:** A tenant's data exceeds 10+ million rows across tables and causes measurable performance degradation on the shared database (slow queries, lock contention, vacuum overhead).
3. **Enterprise willingness to pay:** The customer is on an enterprise tier and willing to absorb the added infrastructure cost ($50-200/month per dedicated DB on managed services).
4. **Custom DB requirements:** A tenant needs PostgreSQL extensions, custom configuration (`work_mem`, `maintenance_work_mem`), or a different PostgreSQL version that would affect other tenants on the shared instance.

Until then, focus engineering effort on query optimization, proper indexing, and table partitioning within the shared database.
