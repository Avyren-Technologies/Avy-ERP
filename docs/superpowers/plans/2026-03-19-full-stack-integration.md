# Full-Stack Integration: Tenant Onboarding, Dashboards & Company Admin

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Connect all frontend screens (mobile + web) to the backend, replacing 100% mock data with real API calls. Extend the backend schema, create tenant onboarding APIs, add company detail edit modals, connect dashboards to real data, verify auth persistence, and create a Company Admin dashboard with role-based routing.

**Architecture:** The backend uses Express + Prisma + PostgreSQL with schema-per-tenant isolation. The Company model will be extended with JSON columns for complex wizard data (locations, contacts, shifts, etc.) to avoid premature table explosion. Both frontends use Axios + React Query (TanStack) v5. API services will be shared patterns across mobile (MMKV/Expo) and web (localStorage/Vite).

**Tech Stack:** Express.js, Prisma, PostgreSQL, Redis, Axios, TanStack React Query v5, Zustand, Zod, React Native (Expo SDK 54), React + Vite, TypeScript

---

## Critical Design Decisions

### Status Vocabulary Mapping
Frontend uses Draft/Pilot/Active/Inactive. Backend enum uses ACTIVE/SUSPENDED/CANCELLED/TRIAL/EXPIRED. Mapping:
- **Draft** (frontend) → `TRIAL` (backend, status before go-live)
- **Pilot** (frontend) → `TRIAL` (backend, with `isPilot: true` flag on Company)
- **Active** (frontend) → `ACTIVE` (backend)
- **Inactive** (frontend) → `SUSPENDED` (backend)

The Company model gets a `wizardStatus` field storing the frontend vocabulary. TenantStatus enum stays unchanged.

### Company `name` Field
`Company.name` maps to `Step1Form.displayName`. `Company.legalName` stores the legal name separately.

### Common vs Per-Location Commercial
When `locationConfig === 'common'`, the Company model holds company-level `selectedModuleIds`, `userTier`, `billingCycle`, `trialDays`. These are copied to all locations on save. When `per-location`, each Location has its own values and Company fields are null.

### Subscription Model
Keep `@unique` on `tenantId`. The Subscription represents the **aggregate** billing for the tenant. Per-location commercial details live on Location rows. Subscription.modules stores the union of all location modules. Subscription totals are computed from Location commercial fields.

### Day Boundary Fields
`dayStartTime`, `dayEndTime`, `weeklyOffs` are company-level settings stored on Company model (not per-shift).

### Logo Upload
MVP: Logo stored as base64 data URL in `Company.logoUrl`. Future: Migrate to S3/CloudFront with `POST /platform/companies/:id/logo` multipart upload.

### Razorpay Secrets
MVP: Stored in `razorpayConfig` JSON column. Future: Application-level AES encryption before storage.

---

## Table of Contents

1. [Phase 1: Backend Schema Extension & Onboarding API](#phase-1)
2. [Phase 2: Frontend API Services & React Query Hooks](#phase-2)
3. [Phase 3: Tenant Onboarding Integration (Mobile + Web)](#phase-3)
4. [Phase 4: Company List & Detail Integration](#phase-4)
5. [Phase 5: Company Detail Edit Modals (Mobile + Web)](#phase-5)
6. [Phase 6: Super-Admin Dashboard Real Data](#phase-6)
7. [Phase 7: Auth Persistence Hardening (Web)](#phase-7)
8. [Phase 8: Company Admin Dashboard + Role-Based Routing](#phase-8)

---

## File Structure

### Backend (`avy-erp-backend/`)
```
prisma/
  schema.prisma                          # MODIFY: Extend Company model, add Location/Contact/etc. models
  seed.ts                                # MODIFY: Add seed data for testing

src/core/tenant/
  tenant.service.ts                      # MODIFY: Add full onboarding create, add dashboard stats
  tenant.controller.ts                   # MODIFY: Add onboarding endpoint, stats endpoints
  tenant.routes.ts                       # MODIFY: Add new routes
  tenant.validators.ts                   # CREATE: Zod validators for onboarding payload
  tenant.types.ts                        # CREATE: TypeScript interfaces for onboarding data

src/core/company/
  company.service.ts                     # CREATE: Company CRUD with full detail
  company.controller.ts                  # CREATE: Company REST handlers
  company.routes.ts                      # MODIFY: Wire up company routes

src/core/billing/
  billing.service.ts                     # CREATE: Billing/subscription queries
  billing.controller.ts                  # CREATE: Billing REST handlers
  billing.routes.ts                      # MODIFY: Wire up billing routes

src/core/dashboard/
  dashboard.service.ts                   # CREATE: Dashboard stats aggregation
  dashboard.controller.ts               # CREATE: Dashboard REST handlers
  dashboard.routes.ts                    # CREATE: Dashboard routes

src/app/routes.ts                        # MODIFY: Register dashboard routes
```

### Mobile App (`mobile-app/src/`)
```
lib/api/
  tenant.ts                              # CREATE: Tenant/company API service
  dashboard.ts                           # CREATE: Dashboard API service

features/super-admin/
  api/
    use-tenant-queries.ts                # CREATE: React Query hooks for tenants
    use-dashboard-queries.ts             # CREATE: React Query hooks for dashboard
  tenant-onboarding/index.tsx            # MODIFY: Wire handleCreateCompany to API
  company-list-screen.tsx                # MODIFY: Replace mock with useQuery
  company-detail-screen.tsx              # MODIFY: Replace mock, add edit modals
  dashboard-screen.tsx                   # MODIFY: Replace mock with useQuery
  billing-overview-screen.tsx            # MODIFY: Replace mock with useQuery
  company-detail-edit-modal.tsx          # CREATE: Edit modal for company fields

features/company-admin/
  dashboard-screen.tsx                   # CREATE: Company Admin dashboard
  api/
    use-company-admin-queries.ts         # CREATE: Company Admin query hooks

app/(app)/
  _layout.tsx                            # MODIFY: Add Company Admin routing
```

### Web App (`web-system-app/src/`)
```
lib/api/
  tenant.ts                              # CREATE: Tenant/company API service
  dashboard.ts                           # CREATE: Dashboard API service

features/super-admin/
  api/
    use-tenant-queries.ts                # CREATE: React Query hooks for tenants
    use-dashboard-queries.ts             # CREATE: React Query hooks for dashboard
  tenant-onboarding/
    TenantOnboardingWizard.tsx           # MODIFY: Wire submit to API
    store.ts                             # MODIFY: Add submit action
  CompanyListScreen.tsx                  # MODIFY: Replace mock with useQuery
  CompanyDetailScreen.tsx                # MODIFY: Replace mock, add edit modals
  CompanyDetailEditModal.tsx             # CREATE: Edit modal for company fields
  DashboardScreen.tsx                    # MODIFY: Replace mock with useQuery
  BillingOverviewScreen.tsx              # MODIFY: Replace mock with useQuery

features/company-admin/
  CompanyAdminDashboard.tsx              # CREATE: Company Admin dashboard
  api/
    use-company-admin-queries.ts         # CREATE: Company Admin query hooks

App.tsx                                  # MODIFY: Add Company Admin routes
store/useAuthStore.ts                    # MODIFY: Add cross-tab logout sync
```

---

<a id="phase-1"></a>
## Phase 1: Backend Schema Extension & Onboarding API

### Task 1.1: Extend Prisma Schema

**Files:**
- Modify: `avy-erp-backend/prisma/schema.prisma`

- [ ] **Step 1: Add new models and extend Company**

Add to `schema.prisma` after existing models:

```prisma
// Extend Company model with full wizard data
model Company {
  id              String   @id @default(cuid())
  name            String
  displayName     String?
  legalName       String?
  shortName       String?
  industry        String
  size            CompanySize
  businessType    String?
  companyCode     String?  @unique
  cin             String?
  incorporationDate String?
  employeeCount   String?
  website         String?
  emailDomain     String?
  gstNumber       String?  @unique
  logoUrl         String?

  // Statutory (Step 2)
  pan             String?
  tan             String?
  gstin           String?
  pfRegNo         String?
  esiCode         String?
  ptReg           String?
  lwfrNo          String?
  rocState        String?

  // Address (Step 3) - JSON for flexibility
  registeredAddress Json?   // { line1, line2, city, district, state, pin, country, stdCode }
  corporateAddress  Json?   // Same structure, null if sameAsRegistered
  sameAsRegistered  Boolean @default(true)

  // Legacy fields kept for backward compat
  address         Json?    // Old field - migrate to registeredAddress
  contactPerson   Json?    // Old field - migrate to contacts

  // Fiscal (Step 4)
  fiscalConfig    Json?    // { fyType, fyCustomStartMonth?, fyCustomEndMonth?, payrollFreq, cutoffDay, disbursementDay, weekStart, timezone, workingDays }

  // Preferences (Step 5)
  preferences     Json?    // { currency, language, dateFormat, numberFormat, timeFormat, indiaCompliance, multiCurrency, ess, mobileApp, webApp, systemApp, aiChatbot, eSign, biometric, bankIntegration, emailNotif, whatsapp }
  razorpayConfig  Json?    // { enabled, keyId, keySecret, webhookSecret, accountNumber, autoDisbursement, testMode }

  // Endpoint (Step 6)
  endpointType    String   @default("default")  // 'default' | 'custom'
  customEndpointUrl String?

  // Strategy (Step 7)
  multiLocationMode Boolean @default(false)
  locationConfig    String  @default("common")  // 'common' | 'per-location'

  // Controls (Step 15)
  systemControls  Json?    // { ncEditMode, loadUnload, cycleTime, payrollLock, leaveCarryForward, overtimeApproval, mfa }

  // Day Boundary & Weekly Offs (from Shifts step - company level)
  dayStartTime    String?
  dayEndTime      String?
  weeklyOffs      Json?    // string[] e.g. ["Sunday"]

  // Company-level commercial (used when locationConfig === 'common')
  selectedModuleIds   Json?    // string[]
  customModulePricing Json?    // Record<string, number>
  userTier            String?  // starter | growth | scale | enterprise | custom
  customUserLimit     String?
  customTierPrice     String?
  billingCycle        String?  @default("monthly")
  trialDays           Int      @default(0)

  // Wizard status (frontend vocabulary: Draft/Pilot/Active/Inactive)
  wizardStatus    String   @default("Draft")

  createdAt       DateTime @default(now())
  updatedAt       DateTime @updatedAt

  // Relations
  tenant          Tenant?
  users           User[]
  locations       Location[]
  contacts        CompanyContact[]
  shifts          CompanyShift[]
  noSeries        NoSeriesConfig[]
  iotReasons      IotReason[]

  @@map("companies")
}

// Location / Plant / Branch
model Location {
  id              String   @id @default(cuid())
  companyId       String
  name            String
  code            String
  facilityType    String
  customFacilityType String?
  status          String   @default("Active")  // Active, Inactive, Under Construction
  isHQ            Boolean  @default(false)

  // Address
  addressLine1    String?
  addressLine2    String?
  city            String?
  district        String?
  state           String?
  pin             String?
  country         String?  @default("India")
  stdCode         String?

  // GST
  gstin           String?
  stateGST        String?

  // Contact
  contactName     String?
  contactDesignation String?
  contactEmail    String?
  contactCountryCode String? @default("+91")
  contactPhone    String?

  // Geo-fencing
  geoEnabled      Boolean  @default(false)
  geoLocationName String?
  geoLat          String?
  geoLng          String?
  geoRadius       Int      @default(50)
  geoShape        String?  @default("circle")

  // Commercial (per-location)
  moduleIds       Json?    // string[]
  customModulePricing Json? // Record<string, number>
  userTier        String?  // starter | growth | scale | enterprise | custom
  customUserLimit String?
  customTierPrice String?
  billingCycle    String?  @default("monthly")
  trialDays       Int      @default(0)

  createdAt       DateTime @default(now())
  updatedAt       DateTime @updatedAt

  company         Company  @relation(fields: [companyId], references: [id], onDelete: Cascade)

  @@unique([companyId, code])
  @@map("locations")
}

// Key Contacts
model CompanyContact {
  id              String   @id @default(cuid())
  companyId       String
  name            String
  designation     String?
  department      String?
  type            String   // Primary, HR Contact, Finance Contact, IT Contact, etc.
  email           String
  countryCode     String   @default("+91")
  mobile          String
  linkedin        String?

  createdAt       DateTime @default(now())
  updatedAt       DateTime @updatedAt

  company         Company  @relation(fields: [companyId], references: [id], onDelete: Cascade)

  @@map("company_contacts")
}

// Shift Configuration
model CompanyShift {
  id              String   @id @default(cuid())
  companyId       String
  name            String
  fromTime        String
  toTime          String
  noShuffle       Boolean  @default(false)
  downtimeSlots   Json?    // Array of { type, duration }

  createdAt       DateTime @default(now())
  updatedAt       DateTime @updatedAt

  company         Company  @relation(fields: [companyId], references: [id], onDelete: Cascade)

  @@map("company_shifts")
}

// Number Series Configuration
model NoSeriesConfig {
  id              String   @id @default(cuid())
  companyId       String
  code            String
  linkedScreen    String
  description     String?
  prefix          String
  suffix          String?
  numberCount     Int      @default(5)
  startNumber     Int      @default(1)

  createdAt       DateTime @default(now())
  updatedAt       DateTime @updatedAt

  company         Company  @relation(fields: [companyId], references: [id], onDelete: Cascade)

  @@unique([companyId, code])
  @@map("no_series_configs")
}

// IOT Reasons
model IotReason {
  id              String   @id @default(cuid())
  companyId       String
  reasonType      String   // Machine Idle | Machine Alarm
  reason          String
  description     String?
  department      String?
  planned         Boolean  @default(false)
  duration        String?

  createdAt       DateTime @default(now())
  updatedAt       DateTime @updatedAt

  company         Company  @relation(fields: [companyId], references: [id], onDelete: Cascade)

  @@map("iot_reasons")
}
```

- [ ] **Step 2: Run migration**

```bash
cd /Users/chetan/Documents/Avyren-Technologies/Products/Mobile-ERP/avy-erp-backend
npx prisma migrate dev --name extend-company-model
```

- [ ] **Step 3: Generate Prisma client**

```bash
npx prisma generate
```

---

### Task 1.2: Create Tenant Onboarding Types & Validators

**Files:**
- Create: `avy-erp-backend/src/core/tenant/tenant.types.ts`
- Create: `avy-erp-backend/src/core/tenant/tenant.validators.ts`

- [ ] **Step 1: Create tenant.types.ts**

Define the full onboarding payload interface matching what both frontends send.

- [ ] **Step 2: Create tenant.validators.ts**

Zod schemas mirroring frontend validation: company identity, statutory, address, fiscal, preferences, endpoint, strategy, locations, contacts, shifts, noSeries, iotReasons, controls, users.

---

### Task 1.3: Extend Tenant Service with Full Onboarding

**Files:**
- Modify: `avy-erp-backend/src/core/tenant/tenant.service.ts`

- [ ] **Step 1: Add `onboardTenant()` method**

This method receives the full wizard payload and creates:
1. Company record with all fields
2. Tenant record linked to company
3. Locations (batch create)
4. Contacts (batch create)
5. Shifts (batch create)
6. NoSeries configs (batch create)
7. IOT reasons (batch create)
8. Subscription record
9. Initial users (Company Admin + others)
10. Tenant schema in PostgreSQL
11. Default RBAC roles

All wrapped in a Prisma transaction.

- [ ] **Step 2: Add `getFullTenantDetail()` method**

Fetches company with ALL relations (locations, contacts, shifts, noSeries, iotReasons, subscription) for the detail screen.

- [ ] **Step 3: Add `updateCompanySection()` method**

Partial update method that accepts a section key (identity, statutory, address, fiscal, preferences, endpoint, strategy, controls) and updates only that section of the company.

- [ ] **Step 4: Add dashboard stats methods**

- `getDashboardStats()`: active companies, total users, MRR, active modules
- `getRecentActivity()`: recent audit log entries
- `getTenantOverview()`: breakdown by status

---

### Task 1.4: Create Dashboard Service & Routes

**Files:**
- Create: `avy-erp-backend/src/core/dashboard/dashboard.service.ts`
- Create: `avy-erp-backend/src/core/dashboard/dashboard.controller.ts`
- Create: `avy-erp-backend/src/core/dashboard/dashboard.routes.ts`
- Modify: `avy-erp-backend/src/app/routes.ts`

- [ ] **Step 1: Create dashboard service**

Methods:
- `getSuperAdminStats()`: aggregate KPIs from tenants, users, subscriptions
- `getCompanyAdminStats(companyId)`: company-specific KPIs
- `getRecentActivity(tenantId?)`: from AuditLog table
- `getRevenueMetrics()`: from Subscription + Invoice tables

- [ ] **Step 2: Create controller and routes**

```
GET /api/v1/platform/dashboard/stats          # Super admin KPIs
GET /api/v1/platform/dashboard/activity        # Recent activity
GET /api/v1/platform/dashboard/revenue         # Revenue metrics
GET /api/v1/dashboard/stats                    # Company admin KPIs (tenant-scoped)
```

- [ ] **Step 3: Register routes in main router**

Add `dashboardRoutes` to `routes.ts` under both platform and tenant-scoped sections.

---

### Task 1.5: Extend Company & Billing Routes

**Files:**
- Modify: `avy-erp-backend/src/core/company/company.routes.ts`
- Create: `avy-erp-backend/src/core/company/company.service.ts`
- Create: `avy-erp-backend/src/core/company/company.controller.ts`
- Modify: `avy-erp-backend/src/core/billing/billing.routes.ts`
- Create: `avy-erp-backend/src/core/billing/billing.service.ts`
- Create: `avy-erp-backend/src/core/billing/billing.controller.ts`

- [ ] **Step 1: Create company service**

CRUD operations for Company with full detail, including section-based updates for edit modals.

- [ ] **Step 2: Create billing service**

- `getSubscriptionSummary()`: MRR, ARR, overdue, pending
- `listInvoices()`: paginated invoice list
- `getRevenueChart()`: monthly revenue trend data

- [ ] **Step 3: Wire up routes**

Tenant onboarding route (add to tenant.routes.ts):
```
POST /api/v1/platform/tenants/onboard          # Full wizard submit (creates company + tenant + all relations)
```

Company routes:
```
GET    /api/v1/platform/companies              # List with pagination (?page, limit, search, status, sortBy)
GET    /api/v1/platform/companies/:id          # Full detail with all relations
PUT    /api/v1/platform/companies/:id          # Full update
PATCH  /api/v1/platform/companies/:id/sections/:sectionKey  # Section update (identity|statutory|address|fiscal|preferences|endpoint|strategy|controls)
DELETE /api/v1/platform/companies/:id          # Delete with cascade
PUT    /api/v1/platform/companies/:id/status   # Activate/suspend/etc.
```

Billing routes:
```
GET /api/v1/platform/billing/summary           # Revenue KPIs
GET /api/v1/platform/billing/invoices          # Invoice list
GET /api/v1/platform/billing/revenue-chart     # Monthly trend
```

---

<a id="phase-2"></a>
## Phase 2: Frontend API Services & React Query Hooks

### Task 2.1: Mobile App — Tenant API Service

**Files:**
- Create: `mobile-app/src/lib/api/tenant.ts`

- [ ] **Step 1: Create tenant API service**

Following the pattern in `lib/api/auth.ts`:
```typescript
// Methods:
tenantApi.onboard(payload)           // POST /platform/tenants/onboard
tenantApi.list(params)               // GET /platform/tenants
tenantApi.getDetail(id)              // GET /platform/companies/:id
tenantApi.updateSection(id, section, data)  // PATCH /platform/companies/:id/section
tenantApi.updateStatus(id, status)   // PUT /platform/companies/:id/status
tenantApi.delete(id)                 // DELETE /platform/companies/:id
```

### Task 2.2: Mobile App — Dashboard API Service

**Files:**
- Create: `mobile-app/src/lib/api/dashboard.ts`

- [ ] **Step 1: Create dashboard API service**

```typescript
dashboardApi.getSuperAdminStats()    // GET /platform/dashboard/stats
dashboardApi.getRecentActivity()     // GET /platform/dashboard/activity
dashboardApi.getRevenueMetrics()     // GET /platform/dashboard/revenue
dashboardApi.getBillingSummary()     // GET /platform/billing/summary
dashboardApi.getInvoices(params)     // GET /platform/billing/invoices
dashboardApi.getCompanyAdminStats()  // GET /dashboard/stats
```

### Task 2.3: Mobile App — React Query Hooks

**Files:**
- Create: `mobile-app/src/features/super-admin/api/use-tenant-queries.ts`
- Create: `mobile-app/src/features/super-admin/api/use-dashboard-queries.ts`

- [ ] **Step 1: Create tenant query hooks**

```typescript
useTenantList(params)                // useQuery for company list
useTenantDetail(id)                  // useQuery for company detail
useOnboardTenant()                   // useMutation for wizard submit
useUpdateCompanySection()            // useMutation for edit modals
useUpdateCompanyStatus()             // useMutation for activate/suspend
useDeleteCompany()                   // useMutation for delete
```

- [ ] **Step 2: Create dashboard query hooks**

```typescript
useSuperAdminStats()                 // useQuery for dashboard KPIs
useRecentActivity()                  // useQuery for activity feed
useRevenueMetrics()                  // useQuery for billing overview
useBillingSummary()                  // useQuery for billing KPIs
useInvoices(params)                  // useQuery for invoice list
```

### Task 2.4: Web App — Tenant API Service

**Files:**
- Create: `web-system-app/src/lib/api/tenant.ts`

- [ ] **Step 1: Create tenant API service** (same methods as mobile, different response unwrapping)

### Task 2.5: Web App — Dashboard API Service

**Files:**
- Create: `web-system-app/src/lib/api/dashboard.ts`

- [ ] **Step 1: Create dashboard API service**

### Task 2.6: Web App — React Query Hooks

**Files:**
- Create: `web-system-app/src/features/super-admin/api/use-tenant-queries.ts`
- Create: `web-system-app/src/features/super-admin/api/use-dashboard-queries.ts`

- [ ] **Step 1: Create tenant query hooks** (same interface as mobile)
- [ ] **Step 2: Create dashboard query hooks** (same interface as mobile)

---

<a id="phase-3"></a>
## Phase 3: Tenant Onboarding Integration (Mobile + Web)

### Task 3.1: Mobile — Wire Wizard Submit to API

**Files:**
- Modify: `mobile-app/src/features/super-admin/tenant-onboarding/index.tsx`

- [ ] **Step 1: Import and use `useOnboardTenant()` mutation**
- [ ] **Step 2: Build payload from all step states in `handleCreateCompany()`**
- [ ] **Step 3: Call mutation, handle success (navigate to company list), handle error (show toast)**
- [ ] **Step 4: Set `SKIP_STEP_VALIDATION = false`**

### Task 3.2: Web — Wire Wizard Submit to API

**Files:**
- Modify: `web-system-app/src/features/super-admin/tenant-onboarding/TenantOnboardingWizard.tsx`
- Modify: `web-system-app/src/features/super-admin/tenant-onboarding/store.ts`

- [ ] **Step 1: Add `submitOnboarding()` action to store that builds full payload**
- [ ] **Step 2: Import and use `useOnboardTenant()` mutation in wizard**
- [ ] **Step 3: Replace mock 2-second delay with real API call**
- [ ] **Step 4: Handle success/error with proper UX**

---

<a id="phase-4"></a>
## Phase 4: Company List & Detail Integration

### Task 4.1: Mobile — Company List Screen

**Files:**
- Modify: `mobile-app/src/features/super-admin/company-list-screen.tsx`

- [ ] **Step 1: Replace `MOCK_COMPANIES` with `useTenantList()` query**
- [ ] **Step 2: Add loading/error states**
- [ ] **Step 3: Wire search and status filters to query params**
- [ ] **Step 4: Remove mock data constants**

### Task 4.2: Mobile — Company Detail Screen

**Files:**
- Modify: `mobile-app/src/features/super-admin/company-detail-screen.tsx`

- [ ] **Step 1: Replace `MOCK_DETAIL` with `useTenantDetail(id)` query**
- [ ] **Step 2: Add loading/error states**
- [ ] **Step 3: Wire action buttons (suspend/activate/delete) to mutations**
- [ ] **Step 4: Remove mock data constants and types**

### Task 4.3: Web — Company List Screen

**Files:**
- Modify: `web-system-app/src/features/super-admin/CompanyListScreen.tsx`

- [ ] **Step 1: Replace mock data with `useTenantList()` query**
- [ ] **Step 2: Wire search/filters to query params**
- [ ] **Step 3: Remove mock data**

### Task 4.4: Web — Company Detail Screen

**Files:**
- Modify: `web-system-app/src/features/super-admin/CompanyDetailScreen.tsx`

- [ ] **Step 1: Replace `TENANT` mock with `useTenantDetail(id)` query**
- [ ] **Step 2: Wire action buttons to mutations**
- [ ] **Step 3: Remove mock data**

---

<a id="phase-5"></a>
## Phase 5: Company Detail Edit Modals (Mobile + Web)

### Task 5.1: Mobile — Edit Modal Component

**Files:**
- Create: `mobile-app/src/features/super-admin/company-detail-edit-modal.tsx`
- Modify: `mobile-app/src/features/super-admin/company-detail-screen.tsx`

- [ ] **Step 1: Create `CompanyDetailEditModal` component**

A reusable bottom-sheet modal that accepts:
- `section`: which section to edit (identity, statutory, address, fiscal, preferences, endpoint, strategy, controls, locations, contacts, shifts, noSeries, iotReasons, users)
- `currentData`: current values for pre-fill
- `onSave`: callback with updated data
- `visible`: boolean

Renders appropriate form fields based on section, using existing atoms from `tenant-onboarding/atoms.tsx`.

- [ ] **Step 2: Add "Edit" buttons to each section in company detail**

Each section header gets an edit icon that opens the modal for that section.

- [ ] **Step 3: Wire save to `useUpdateCompanySection()` mutation**

On save → call PATCH endpoint → invalidate detail query → close modal.

### Task 5.2: Web — Edit Modal Component

**Files:**
- Create: `web-system-app/src/features/super-admin/CompanyDetailEditModal.tsx`
- Modify: `web-system-app/src/features/super-admin/CompanyDetailScreen.tsx`

- [ ] **Step 1: Create `CompanyDetailEditModal` component**

A centered modal (using existing Modal component) that accepts same props as mobile version but renders web-specific form atoms from `tenant-onboarding/atoms.tsx`.

- [ ] **Step 2: Add "Edit" button triggers to each section**
- [ ] **Step 3: Wire save to mutation with query invalidation**

---

<a id="phase-6"></a>
## Phase 6: Super-Admin Dashboard Real Data

### Task 6.1: Mobile Dashboard

**Files:**
- Modify: `mobile-app/src/features/super-admin/dashboard-screen.tsx`

- [ ] **Step 1: Replace `KPI_DATA` with `useSuperAdminStats()` query**
- [ ] **Step 2: Replace `RECENT_ACTIVITY` with `useRecentActivity()` query**
- [ ] **Step 3: Replace `TENANT_OVERVIEW` with real tenant stats**
- [ ] **Step 4: Add loading/error states, remove all mock constants**

### Task 6.2: Mobile Billing

**Files:**
- Modify: `mobile-app/src/features/super-admin/billing-overview-screen.tsx`

- [ ] **Step 1: Replace `REVENUE_KPIS` with `useBillingSummary()` query**
- [ ] **Step 2: Replace `MONTHLY_REVENUE` with `useRevenueMetrics()` query**
- [ ] **Step 3: Replace `RECENT_INVOICES` with `useInvoices()` query**
- [ ] **Step 4: Remove mock data**

### Task 6.3: Web Dashboard

**Files:**
- Modify: `web-system-app/src/features/super-admin/DashboardScreen.tsx`

- [ ] **Step 1: Replace all mock KPIs with `useSuperAdminStats()` query**
- [ ] **Step 2: Replace mock tenant list with real data**
- [ ] **Step 3: Replace mock activity with `useRecentActivity()` query**
- [ ] **Step 4: Remove mock data**

### Task 6.4: Web Billing

**Files:**
- Modify: `web-system-app/src/features/super-admin/BillingOverviewScreen.tsx`

- [ ] **Step 1: Replace mock KPIs with `useBillingSummary()` query**
- [ ] **Step 2: Replace mock invoices with `useInvoices()` query**
- [ ] **Step 3: Replace mock chart with `useRevenueMetrics()` query**
- [ ] **Step 4: Remove mock data**

---

<a id="phase-7"></a>
## Phase 7: Auth Persistence Hardening (Web)

### Task 7.1: Cross-Tab Logout & Token Validation

**Files:**
- Modify: `web-system-app/src/store/useAuthStore.ts`
- Modify: `web-system-app/src/App.tsx`

- [ ] **Step 1: Add StorageEvent listener for cross-tab logout**

```typescript
// In useAuthStore or App.tsx initialization:
window.addEventListener('storage', (event) => {
  if (event.key === 'auth_tokens' && event.newValue === null) {
    useAuthStore.getState().signOut();
  }
});
```

- [ ] **Step 2: Add client-side token expiration check**

Before API calls, check if access token has expired locally (decode JWT exp claim). If expired, trigger refresh proactively instead of waiting for 401.

- [ ] **Step 3: Verify refresh token flow end-to-end**

Test: login → wait for token expiry → make API call → verify silent refresh works → verify user stays logged in across page refreshes.

---

<a id="phase-8"></a>
## Phase 8: Company Admin Dashboard + Role-Based Routing

### Task 8.1: Mobile — Company Admin Dashboard

**Files:**
- Create: `mobile-app/src/features/company-admin/dashboard-screen.tsx`
- Create: `mobile-app/src/features/company-admin/api/use-company-admin-queries.ts`
- Modify: `mobile-app/src/app/(app)/index.tsx`
- Modify: `mobile-app/src/app/(app)/_layout.tsx`

- [ ] **Step 1: Create Company Admin dashboard screen**

Shows company-specific KPIs:
- Total employees, active today, on leave
- Recent attendance summary
- Module usage stats
- Pending approvals count
- Quick actions: Manage Users, View Reports, Settings

Uses `useCompanyAdminStats()` query hook.

- [ ] **Step 2: Create query hooks**

```typescript
useCompanyAdminStats()  // GET /dashboard/stats (tenant-scoped)
```

- [ ] **Step 3: Update dashboard route to render role-based screen**

In `app/(app)/index.tsx`:
```typescript
export default function DashboardRoute() {
  const { userRole } = useAuthStore();
  if (userRole === 'super-admin') return <SuperAdminDashboard />;
  if (userRole === 'company-admin') return <CompanyAdminDashboard />;
  return <BasicDashboard />; // fallback for regular users
}
```

- [ ] **Step 4: Update tab layout for Company Admin navigation**

Add Company Admin sidebar sections: Dashboard, Employees, Attendance, Reports, Settings.

### Task 8.2: Web — Company Admin Dashboard

**Files:**
- Create: `web-system-app/src/features/company-admin/CompanyAdminDashboard.tsx`
- Create: `web-system-app/src/features/company-admin/api/use-company-admin-queries.ts`
- Modify: `web-system-app/src/App.tsx`
- Modify: `web-system-app/src/layouts/Sidebar.tsx`

- [ ] **Step 1: Create Company Admin dashboard screen**

Same KPIs as mobile but with web layout:
- Grid-based KPI cards
- Employee stats chart
- Recent activity table
- Module usage breakdown
- Quick action cards

- [ ] **Step 2: Create query hooks** (same as mobile)

- [ ] **Step 3: Add Company Admin routes to App.tsx**

```tsx
<Route path="dashboard" element={
  userRole === 'super-admin' ? <DashboardScreen /> :
  userRole === 'company-admin' ? <CompanyAdminDashboard /> :
  <BasicDashboard />
} />
```

- [ ] **Step 4: Update Sidebar for Company Admin navigation**

Show different nav items based on role:
- Company Admin: Dashboard, Employees, Attendance, Leave, Payroll, Reports, Settings
- Hide super-admin only items (Companies, Billing, Platform Monitor)

---

## Execution Order

The tasks should be executed in this order due to dependencies:

1. **Phase 1** (Backend) — Must be first, everything depends on APIs
2. **Phase 2** (API Services + Hooks) — Depends on Phase 1 endpoints
3. **Phase 3** (Onboarding Integration) — Depends on Phase 2 hooks
4. **Phase 4** (List + Detail Integration) — Depends on Phase 2 hooks
5. **Phase 5** (Edit Modals) — Depends on Phase 4 detail screens
6. **Phase 6** (Dashboard Real Data) — Depends on Phase 2 hooks
7. **Phase 7** (Auth Hardening) — Independent, can run in parallel with Phase 3-6
8. **Phase 8** (Company Admin) — Depends on Phase 1 dashboard API

**Parallelizable:** Phases 3+4+5+6 can run in parallel after Phase 2 completes. Phase 7 is independent. Within each phase, mobile and web tasks are independent and can be parallelized.

---

## Testing Strategy

- **Backend**: Test each endpoint with curl/httpie after creation
- **Frontend**: Manual testing — navigate each screen, verify data loads
- **Integration**: Create a test tenant via wizard, verify it appears in list, open detail, edit sections, check dashboard updates
- **Auth**: Login → refresh page → verify session persists → open second tab → logout in first → verify second tab redirects
