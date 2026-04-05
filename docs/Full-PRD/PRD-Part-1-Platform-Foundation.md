# Avy ERP — Master Product Requirements Document
## Part 1: Platform Foundation, Vision & Architecture

> **Product:** Avy ERP
> **Company:** Avyren Technologies
> **Document Series:** PRD-001 of 5
> **Version:** 2.0
> **Date:** April 2026
> **Status:** Final Draft · Confidential
> **Scope:** Platform vision, system architecture, multi-tenancy model, authentication, and tenant onboarding

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [Product Vision & Goals](#2-product-vision--goals)
3. [Target Market & User Personas](#3-target-market--user-personas)
4. [System Architecture Overview](#4-system-architecture-overview)
5. [Multi-Tenancy Architecture](#5-multi-tenancy-architecture)
6. [Authentication & Identity Management](#6-authentication--identity-management)
7. [Tenant Onboarding — Super Admin](#7-tenant-onboarding--super-admin)
8. [Company Configuration — Master Setup](#8-company-configuration--master-setup)
9. [Platform Lifecycle & Tenant States](#9-platform-lifecycle--tenant-states)
10. [Glossary](#10-glossary)

---

## 1. Executive Summary

Avy ERP is a **universal, mobile-first enterprise resource planning platform** built by Avyren Technologies for small and medium-sized manufacturing enterprises (SMEs). It is designed to be the most extensible and scalable ERP system for industry — enabling teams to manage every dimension of their operations from a phone, tablet, desktop, or browser.

Avy ERP is delivered as a **multi-tenant SaaS platform**. Each subscribing company receives a fully isolated, secure environment. The system is modular — companies pay only for the capabilities they need, and modules can be activated or deactivated at any time without disrupting live operations.

The platform spans three surface areas:

- A **mobile application** (React Native / Expo) for shop-floor and operational staff
- A **web application** (React / Vite) for administration, management, and configuration
- A **desktop application** (ElectronJS) for environments requiring an installed, offline-capable client

All three surfaces connect to a single backend and share a single data model, ensuring there is never a discrepancy in operational truth across the organisation. Every module feeds data to every other relevant module — there are no silos and no duplicate entry anywhere in the system.

---

## 2. Product Vision & Goals

### 2.1 Vision Statement

> To be the operating system of modern manufacturing — giving every person in a factory, from the shop-floor operator to the business owner, the right information at the right time to make better decisions.

### 2.2 Product Goals

| Goal | Description |
|---|---|
| **Universality** | Applicable across all manufacturing industry types — automotive, steel, pharma, electronics, FMCG, and more |
| **Mobile-First** | Designed for phones and tablets as the primary interaction surface, not an afterthought |
| **Offline-Capable** | Operational on the shop floor even without internet connectivity; syncs on reconnection |
| **Modular** | Companies activate only what they need; the platform grows with them organically |
| **Integrated** | Every module shares data with every other relevant module — no silos, no duplicate entry |
| **Scalable** | Architecture supports thousands of concurrent tenants with zero cross-contamination |

### 2.3 Core Design Principles

**Single Source of Truth** — No data is entered twice. Attendance from the Security module feeds HR. Production output feeds Incentives. Breakdowns feed OEE. Payroll flows into Finance.

**Role-Based Visibility** — Every user sees only what their role permits. The same system surfaces completely different views to a shop-floor operator and a business owner.

**Progressive Disclosure** — Simple and uncluttered on first impression. Full depth and configuration power available when needed, without overwhelming everyday users.

**Offline-First** — Mobile operations degrade gracefully without connectivity and sync automatically when reconnected. No data is lost.

**Context-Awareness** — Fields, options, and screens appear only when contextually relevant. A company without GST does not see GST fields. A company without ESI does not see ESI payroll components.

---

## 3. Target Market & User Personas

### 3.1 Target Market

Avy ERP targets **small and medium-sized manufacturing enterprises (SMEs)** across all industries — companies with 50 to 5,000 employees — that need integrated operational management without the complexity, cost, and rigidity of legacy enterprise ERP systems. The primary geographic focus is India, with the compliance engine built natively for Indian statutory requirements (GST, PF, ESI, TDS, PT) and with extensibility for other regulatory regimes.

### 3.2 User Personas

| Persona | Primary Platform | Core Operational Needs |
|---|---|---|
| **Business Owner / Admin** | Web, Mobile | Full operational visibility; executive dashboards; financial health overview |
| **HR Manager** | Web, Mobile | Employee lifecycle management; payroll processing; leave approvals; compliance |
| **Payroll Manager** | Web | Salary structures; payroll runs; statutory deductions; bank disbursement |
| **Production Manager** | Mobile, Web | OEE monitoring; shift output tracking; scrap and NC management |
| **Maintenance Technician** | Mobile | PM task execution; breakdown reporting; spare parts consumption |
| **Finance Team** | Web | Payables; receivables; payment recording; financial statements |
| **Sales Executive** | Mobile, Web | Quote creation; invoice management; customer ledger |
| **Security Personnel** | Mobile | Employee gate attendance; visitor check-in; goods verification |
| **Warehouse / Stores Clerk** | Mobile | Stock management; goods receipt; material requests |
| **Quality Inspector** | Mobile, Web | Non-conformance logging; inspection records; calibration tracking |
| **Vendor (External)** | Web portal | ASN creation; delivery coordination; PO acknowledgement |
| **Shop-Floor Operator** | Mobile | Production logging; attendance marking; leave requests |
| **Company Admin** | Web | System configuration; user management; RBAC; module activation |
| **Super Admin (Avyren)** | Web (Platform Panel) | Tenant management; billing; platform monitoring; cross-tenant support |

---

## 4. System Architecture Overview

### 4.1 Architecture Philosophy

Avy ERP's backend is built as a **Modular Monolith**. This architectural pattern means:

- All business modules are deployed as a single unit, eliminating the distributed systems complexity of microservices
- Each module has clearly defined boundaries — its own internal models, services, and controllers
- Modules communicate with one another through well-defined internal interfaces, never through direct database joins across module boundaries
- The architecture can be decomposed into independent services in the future without rewriting business logic

This gives the team the **development simplicity of a monolith** with the **structural discipline of microservices** from day one.

### 4.2 Client Layer

Three distinct client applications connect to the same backend:

| Client | Technology | Primary Users | Key Capabilities |
|---|---|---|---|
| **Mobile App** | React Native + Expo (iOS & Android) | Shop-floor operators, HR, security, technicians | Offline-first; camera; push notifications; GPS attendance |
| **Web App** | React + Vite (TypeScript) | Managers, admins, finance, HR | Full configuration; reporting; bulk operations; Super Admin panel |
| **Desktop App** | ElectronJS (wraps Web App) | Environments needing installed software | Biometric device integration; local printing; offline capability |

All three clients authenticate via JWT and connect to identical backend APIs. There is no data discrepancy between surfaces.

### 4.3 Backend Layer

| Layer | Technology | Purpose |
|---|---|---|
| **Runtime** | Node.js | Execution environment |
| **Framework** | Express.js (TypeScript) | REST API routing and middleware |
| **Architecture** | Modular Monolith | Business logic isolation per module |
| **Database** | PostgreSQL (schema-per-tenant) | Primary data store |
| **ORM** | Prisma | Database access and migration management |
| **Cache** | Redis | Session data, tenant resolution caching, rate limiting |
| **Message Queue** | Internal event bus | Async cross-module communication and event propagation |
| **File Storage** | S3-compatible cloud object storage | Documents, images, attachments |

### 4.4 Request Processing Pipeline

Every API request (except authentication) passes through the following middleware pipeline in sequence:

1. **TLS Termination** — All traffic arrives over HTTPS (TLS 1.3)
2. **Rate Limiting** — Per-tenant and global rate limits enforced at the gateway
3. **Tenant Resolution** (`tenantMiddleware`) — Identifies the tenant from one of four sources in priority order: `X-Tenant-ID` header, subdomain extraction, JWT payload, query parameter
4. **Schema Binding** — Prisma client is bound to the resolved tenant's PostgreSQL schema for the duration of the request
5. **Authentication** (`authMiddleware`) — JWT is validated; claims (tenantId, companyId, permissions) are extracted and attached to the request context
6. **Authorisation (RBAC)** — The user's permissions are checked against the required permission for the requested action
7. **Business Logic** — The module handles the request using only the tenant-scoped database client
8. **Response** — Data returned; all database access has been exclusively within the tenant's schema

### 4.5 Data Layer

| Component | Role |
|---|---|
| **PostgreSQL — public schema** | Platform-level data: Tenant registry, User accounts, Billing, Subscription records |
| **PostgreSQL — tenant_{slug} schema** | All business data for a tenant: Employees, Payroll, Inventory, Production, etc. |
| **Redis** | Tenant resolution cache (TTL: 24 hours); session state; background job queues |
| **Object Storage** | Binary file storage: documents, images, exports, attachments |

### 4.6 Technology Stack Summary

**Mobile Application**

| Layer | Technology |
|---|---|
| Framework | React Native with Expo SDK |
| Language | TypeScript |
| State Management | Zustand |
| Styling | Nativewind (Tailwind for React Native) |
| Data Fetching & Caching | TanStack Query |
| Offline Storage | SQLite (via Expo SQLite) |
| Sync | Custom sync queue with TanStack Query background sync |
| Platforms | iOS and Android |

**Web Application**

| Layer | Technology |
|---|---|
| Framework | React |
| Build Tool | Vite |
| Language | TypeScript |
| State Management | Zustand |
| Data Fetching | TanStack Query |
| Styling | Tailwind CSS |

**Desktop Application**

| Layer | Technology |
|---|---|
| Shell | ElectronJS |
| UI | React + Vite (shared web app codebase) |
| Packaging | Electron Forge |
| Updates | Electron auto-updater |

---

## 5. Multi-Tenancy Architecture

### 5.1 Overview

Avy ERP's multi-tenancy is built on **three interconnected pillars** that together create a complete tenant-isolated experience:

| Pillar | Mechanism | What It Achieves |
|---|---|---|
| **Database Isolation** | Schema-per-tenant in PostgreSQL | Complete data separation; no cross-tenant data access possible |
| **Web Subdomain Routing** | Wildcard DNS + Nginx reverse proxy | Each company gets a branded URL |
| **Mobile Tenant Awareness** | Single app build; tenant resolved from JWT post-login | One APK/IPA for all tenants; no per-tenant builds |

### 5.2 Schema-Per-Tenant Database Design

Each tenant's business data lives in a dedicated PostgreSQL schema named `tenant_{slug}` (e.g., `tenant_tatagroup`, `tenant_avyren`). Platform-level data (the tenant registry, user accounts, billing) lives in the `public` schema.

**Why schema-per-tenant and not shared tables or separate databases:**

| Approach | Pros | Cons |
|---|---|---|
| Shared tables (row-level isolation with `companyId`) | Simple; single migration | Risk of data leaks on missed WHERE clauses; no true isolation; does not scale |
| **Schema-per-tenant (chosen approach)** | Strong isolation; easy per-tenant backup/restore; single DB connection | Migrations must run per-tenant; connection pooling requires attention |
| Database-per-tenant | Maximum isolation; per-tenant scaling | Expensive; operational nightmare at 100+ tenants |

**Data boundaries:**

- Platform schema (`public`): Tenant, Company, User, Role, BillingSubscription, Invoice
- Tenant schema (`tenant_{slug}`): All business models — Employee, Attendance, Payroll, Inventory, SalesOrder, ProductionLog, Machine, Vendor, etc.
- Queries in the application layer can never cross schema boundaries; the Prisma client is initialised with the tenant's schema name and every query executes within that schema

**Schema provisioning on onboarding:**

When a new company is created and activated, the system automatically:
1. Generates a unique slug from the company name (e.g., `tatagroup`)
2. Creates a new PostgreSQL schema: `CREATE SCHEMA tenant_tatagroup`
3. Runs all pending Prisma migrations against the new schema
4. Seeds default configuration data (reference roles, system defaults)
5. Registers the schema name in the tenant registry
6. Creates the Company Admin user record

This entire process is automated and completes in under 5 minutes.

### 5.3 Subdomain & URL Architecture

Each tenant is accessible via a unique web URL following the pattern:

```
{company-slug}.avy-erp.avyren.in
```

Examples:
- `avyren.avy-erp.avyren.in` — Avyren Technologies' own portal
- `tatagroup.avy-erp.avyren.in` — Tata Group's ERP portal
- `infosys.avy-erp.avyren.in` — Infosys' ERP portal

**DNS Configuration:** A wildcard DNS record (`*.avy-erp.avyren.in`) points all subdomains to the same server IP address. An Nginx reverse proxy extracts the subdomain and passes it as a header to the backend.

**SSL:** A wildcard SSL certificate from Let's Encrypt covers all `*.avy-erp.avyren.in` subdomains under a single certificate.

**Subdomain role in the system:**
- The subdomain is used **exclusively for UX and branding** — it populates the login page with the company's logo and name
- The subdomain is **never used for authorisation** — all authorisation decisions are made from the JWT
- A user logging into the wrong company's subdomain with valid credentials for a different tenant will receive an "Invalid credentials" error; the system does not reveal which subdomain is correct

**Future capability:** Vanity custom domains (e.g., `erp.tatagroup.com`) are planned and architecturally supported by storing a custom domain field in the tenant registry and configuring Nginx accordingly.

### 5.4 Mobile App Tenant Resolution

The mobile application is a single build (one APK for Android, one IPA for iOS) that serves all tenants. Tenant identification on mobile works as follows:

1. The user opens the app and is presented with a login screen
2. The user enters their email and password
3. The backend verifies credentials and returns a JWT that contains `tenantId`, `companyId`, `userId`, and `permissions`
4. All subsequent API calls from the mobile app use this JWT for both authentication and tenant resolution
5. The app may display the company's logo and name (loaded from the branding endpoint using the `tenantId`)

There is no need for the user to know or enter a subdomain or tenant identifier on mobile.

### 5.5 Tenant Resolution Priority

When the backend receives a request, tenant resolution follows this priority order:

1. `X-Tenant-ID` header (used in API integrations)
2. Subdomain (extracted by Nginx and forwarded as header)
3. JWT payload `tenantId` field
4. Query parameter `?tenantId=` (fallback for edge cases)

The resolved tenant is cached in Redis with a 24-hour TTL to avoid repeated database lookups on every request.

### 5.6 Connection Pooling

At scale, each tenant's Prisma client is cached in memory after the first use (not recreated per request). A PgBouncer instance runs in transaction pooling mode to manage the total number of database connections, preventing connection exhaustion as the number of concurrent tenants and users grows.

### 5.7 Tenant Data Isolation Security

| Risk | Mitigation |
|---|---|
| Cross-tenant data access | PostgreSQL schema isolation — queries cannot cross schemas |
| SQL injection crossing schemas | Prisma ORM parameterises all queries; schema names are validated as `[a-z0-9_]` only |
| Tenant impersonation via subdomain | Subdomain is used only for branding; authorisation always comes from the JWT |
| Shared cache poisoning | All Redis keys are prefixed with `tenant:{tenantId}:` to prevent cross-tenant cache reads |
| Backup data exposure | Per-tenant `pg_dump` using schema export ensures each backup contains only one tenant's data |

### 5.8 Tenant Scaling

| Tenant Volume | Infrastructure Recommendation |
|---|---|
| 1–50 tenants | Single PostgreSQL instance (4 GB RAM, 2 vCPU) |
| 50–200 tenants | Add PgBouncer; tune shared_buffers (16 GB RAM, 4 vCPU) |
| 200–500 tenants | Add read replicas; consider schema partitioning (32 GB RAM, 8 vCPU) |
| 500+ tenants | Shard: move large-volume tenants to dedicated database instances |

A tenant can be migrated to a dedicated database at any time by exporting the schema, importing to a new instance, and updating the tenant registry's `databaseUrl` field — with no downtime for other tenants.

---

## 6. Authentication & Identity Management

### 6.1 Authentication Model

Avy ERP uses a **JWT-based stateless authentication** model:

- **Access Token** — Short-lived JWT (configurable TTL, typically 15–60 minutes); sent as `Authorization: Bearer <token>` header on all API requests
- **Refresh Token** — Long-lived token stored securely; used to obtain new access tokens without re-login
- **Token Payload** — Every JWT carries: `userId`, `tenantId`, `companyId`, `plantId`, `permissions[]`, `roles[]`, `exp` (expiry timestamp)

Because the tenant identity is embedded in the JWT, there is no way for a token issued to Tenant A to be used to access Tenant B's data — the backend validates `tenantId` from the JWT against the tenant context on every request.

### 6.2 Login Flow

1. User submits email and password to `POST /api/v1/auth/login`
2. Backend validates credentials against the platform (`public`) schema user record
3. Backend confirms the user's `companyId` matches the tenant context (subdomain or header)
4. If valid, backend issues an access token and refresh token
5. Client stores tokens; all subsequent requests include `Authorization: Bearer <accessToken>`
6. When the access token expires, the client calls `POST /api/v1/auth/refresh-token` with the refresh token to obtain a new access token silently
7. On logout, `POST /api/v1/auth/logout` is called to invalidate the session

### 6.3 Multi-Factor Authentication (MFA)

MFA is a configurable security layer available per tenant. When enabled, the login process adds a second verification step:

**Supported MFA Methods:**

| Method | Description |
|---|---|
| **TOTP (Time-Based One-Time Password)** | User sets up an authenticator app (Google Authenticator, Authy); 6-digit rotating code |
| **Email OTP** | One-time code sent to the user's registered email address |
| **SMS OTP** | One-time code sent via SMS to the user's registered mobile number |

**MFA Configuration Levels:**

- **Platform-level** — Super Admin can enforce MFA for all tenants
- **Tenant-level** — Company Admin can mandate MFA for all users within their company
- **Role-level** — Company Admin can enforce MFA for specific roles (e.g., Finance, HR Admin)
- **User-level** — Individual users can self-enroll in MFA for their own account

**MFA Enforcement Logic:**

- If MFA is required and not yet set up for a user, they are redirected to the MFA setup screen immediately after first login
- A temporary, short-lived token is issued after credential verification; full access is only granted after successful second-factor completion
- Backup codes are generated at MFA setup time; a configurable number of codes are provided for emergency access

### 6.4 Password Management

| Operation | Endpoint | Behaviour |
|---|---|---|
| Forgot password | `POST /auth/forgot-password` | Sends a time-limited reset code to the user's registered email |
| Verify reset code | `POST /auth/verify-reset-code` | Validates the code; returns a scoped token for password reset |
| Reset password | `POST /auth/reset-password` | Sets a new password using the scoped token |
| Change password | `POST /auth/change-password` | For logged-in users to update their password |

**Password Policy (configurable per tenant):**
- Minimum length (default: 8 characters)
- Complexity requirements (uppercase, lowercase, numeric, special character — each toggleable)
- Password history enforcement (prevent reuse of last N passwords)
- Maximum password age (expiry period in days; user prompted to change on expiry)
- Account lockout after N failed attempts (configurable threshold and lockout duration)

### 6.5 Session Management

- Session idle timeout is configurable per tenant (default: 30 minutes of inactivity)
- The Super Admin panel shows a live session timer
- Concurrent session control: configurable maximum active sessions per user
- All session events (login, logout, token refresh, failed attempts) are captured in the audit log with timestamp and IP address

### 6.6 User–Employee Auto-Linking

When a User account is created with an email that matches an existing Employee record's `personalEmail` or `officialEmail`, the system automatically links the two records. This also works in reverse — creating an Employee record whose email matches an existing User triggers automatic linkage. This mechanism ensures that ESS (Employee Self-Service) access is available as soon as either record is created, with no manual linking step required.

---

## 7. Tenant Onboarding — Super Admin

### 7.1 Overview

Tenant Onboarding is the process by which a new company (tenant) is registered and fully configured in Avy ERP. There are two onboarding pathways:

**Option A — Self-Service Signup:** The company visits the Avyren website, creates an account, configures their profile, selects modules, and pays online. The tenant is provisioned automatically after payment with no Avyren staff involvement.

**Option B — Avyren-Managed Onboarding:** An Avyren Super Admin creates and configures the tenant on behalf of the customer. Used for enterprise deals, complex configurations, or customers who prefer assisted setup.

### 7.2 Onboarding Steps (Managed Flow)

The full onboarding sequence is a 15-step wizard:

```
Step 1  → Create Company Record
Step 2  → Company Identity & Basic Information
Step 3  → Statutory & Tax Identifiers
Step 4  → Registered & Correspondence Address
Step 5  → Fiscal Year & Calendar Settings
Step 6  → System Preferences & Feature Flags
Step 7  → Branch / Location Setup
Step 8  → Key Contacts
Step 9  → Plant / Multi-Location Management
Step 10 → Shift & Time Management
Step 11 → Number Series (No Series) Configuration
Step 12 → IOT Reason Master
Step 13 → System Controls & Operational Settings
Step 14 → Assign Admin Users
Step 15 → Activate Tenant → GO LIVE
```

### 7.3 Super Admin Identity & Access

The Super Admin is Avyren Technologies' highest-privilege platform operator:

| Attribute | Details |
|---|---|
| Access Scope | All companies — cross-tenant |
| Screen Access | All 32+ configuration screens across all tenants |
| Data Access | Read + Write + Delete across all tenant records |
| Session | Live session timer displayed in the UI |
| Authentication | Username + Password (with MFA strongly recommended) |

**Super Admin capabilities:**
- Create, edit, suspend, and delete any tenant record
- Access all configuration tabs for any company
- Add, modify, and deactivate any user in any tenant
- Enable or disable system-wide and tenant-level feature flags
- Perform bulk data imports
- View audit logs across all tenants
- Manage No Series, Shifts, IOT Reasons at global or per-tenant level
- Switch between companies using the Company Selector panel
- Access Global Search (⌘K / Ctrl+K) to jump to any screen instantly

**What Super Admin cannot do:**
- Access tenant's operational business data (HR records, payroll details, production data) unless explicitly granted for a support or audit purpose — this preserves tenant data confidentiality

### 7.4 Company Selector Panel

The Super Admin's left panel hosts a Company Selector showing:
- Total count of onboarded companies (badge indicator)
- Inline search by company name
- Status badge for each company (Active / Pilot / Inactive / Draft)
- Company row: Logo Initial, Company Name, Company Code, Status
- "+ Add Company" button to begin onboarding a new tenant

---

## 8. Company Configuration — Master Setup

### 8.1 Company Identity

The first configuration tab establishes the company's core identity. All downstream configuration and compliance outputs (payslips, Form 16, offer letters, reports) derive from this data.

**Core Identity Fields:**

| Field | Required | Notes |
|---|---|---|
| Display Name | Yes | Shown on all employee-facing screens and documents |
| Legal / Registered Name | Yes | Full name as per incorporation; used on statutory documents |
| Business Type | Yes | Pvt. Ltd. / Public Limited / LLP / Partnership / Proprietorship / Others |
| Nature of Industry | Yes | Manufacturing, IT, Healthcare, Retail, Automotive, Pharma, etc. |
| Company Code | Yes | Auto-generated unique identifier (e.g., `ABC-IN-001`); can be overridden |
| Short Name | No | Abbreviated name for compact displays |
| Date of Incorporation | Yes | As per MCA/ROC registration |
| Number of Employees | No | Used for compliance threshold checks (PF, ESI eligibility) |
| CIN Number | No | Corporate Identity Number; format: `U72900KA2019PTC312847` |
| Official Website | No | Includes "Visit ↗" quick-open button |
| Corporate Email Domain | Yes | Used for auto-provisioning employee email IDs; domain verified |
| Company Logo | No | PNG, JPG, or SVG; max 2 MB; used on all documents and portals |

**Company Status:**

| Status | Colour | Meaning |
|---|---|---|
| Active | Green | Company is live and fully operational |
| Pilot | Blue | Company is in trial or testing phase |
| Inactive | Red | Company has been deactivated |
| Draft | Amber | Setup is incomplete; not yet activated |

### 8.2 Statutory & Tax Identifiers

These fields drive payroll computation, TDS, statutory filings, and compliance certificate generation. Incorrect data causes compliance failures and regulatory penalties.

| Identifier | Format | Required | Purpose |
|---|---|---|---|
| PAN | `AARCA5678F` (10 chars) | Yes | TDS, Form 16, Form 24Q |
| TAN | `BLRA98765T` (10 chars) | Yes | TDS deduction and quarterly returns |
| GSTIN | `29AARCA5678F1Z3` (15 chars) | Conditional | Required if GST-registered |
| PF Registration No. | `KA/BLR/0112345/000/0001` | Yes | PF deductions and monthly ECR uploads |
| ESI Employer Code | `53-00-123456-000-0001` | Conditional | Required if employees earn ≤ ₹21,000/month |
| PT Registration No. | State-specific | Conditional | Required in PT-applicable states |
| LWFR Number | Optional | No | Required in LWF-applicable states |
| ROC Filing State | `RoC Bengaluru, Karnataka` | Yes | Jurisdiction for annual filings |

### 8.3 Address Configuration

Two addresses are maintained:

- **Registered Address** — The legal address as per the company's incorporation documents; used on all statutory and government documents
- **Corporate / Correspondence Address** — The operational HQ address; shown on payslips and offer letters. Can be marked as same as registered address

Both addresses capture: Line 1, Line 2, City, State, PIN code, and Country.

### 8.4 Fiscal Year & Calendar Settings

| Setting | Options / Notes |
|---|---|
| Financial Year Period | April–March (India default) or custom period |
| Payroll Frequency | Monthly / Bi-weekly / Weekly |
| Payroll Cut-off Day | Day of month after which attendance is frozen for that payroll period |
| Disbursement Day | Day of month on which salary is credited |
| Timezone | Asia/Kolkata or any IANA timezone |
| Week Start Day | Monday (default) or Sunday |
| Working Days | Checkboxes for Monday–Saturday (Sunday always off) |

### 8.5 System Preferences & Feature Flags

System preferences control the overall behaviour of the tenant's ERP instance:

| Preference | Type | Notes |
|---|---|---|
| Currency | Dropdown | INR (default), USD, EUR, others |
| Language | Dropdown | English (default); multilingual planned |
| Date Format | Dropdown | DD/MM/YYYY (default), MM/DD/YYYY, YYYY-MM-DD |
| India Statutory Compliance Mode | Toggle | Activates PF, ESI, PT, TDS computation engines |
| ESS Portal | Toggle | Enables/disables Employee Self-Service portal |
| Mobile App Access | Toggle | Enables/disables mobile app for the tenant |
| Biometric Sync | Toggle | Enables attendance sync from biometric devices |
| e-Sign Integration | Toggle | Enables electronic signature for HR letters |
| MSME Registration Indicator | Toggle | For MSME-registered companies |

### 8.6 Branch / Location Setup

Branches represent the company's physical operational locations (offices, warehouses, satellite facilities). Each branch captures:

| Field | Notes |
|---|---|
| Branch Name | Display name |
| Branch Code | Unique identifier |
| Address | Full address with PIN |
| Geo-Fencing Radius | Radius in metres used for GPS-based mobile attendance verification |
| Branch Type | Head Office / Regional Office / Warehouse / Factory |
| Status | Active / Inactive |

### 8.7 Plant / Multi-Location Management

A plant is a production or operational facility within the company. Plants are distinct from branches in that they carry GST registrations and have production-level configuration.

**Plant Configuration Modes:**
- **Common Configuration** — All plants share the same shifts, No Series, and IOT Reasons (simpler; suitable for single-location or uniform operations)
- **Per-Plant Configuration** — Each plant maintains its own independent configuration (suitable for geographically distributed or operationally distinct facilities)

**Plant Fields:**

| Field | Notes |
|---|---|
| Plant Name | Display name |
| Plant Code | Unique identifier |
| Plant Type | Manufacturing / Warehouse / Distribution / Corporate |
| Address | Full address |
| State-wise GSTIN | GST registration specific to this plant's state (critical for India's state-wise GST) |
| HQ Designation | Boolean — one plant must be the HQ; its data reflects in company-level records |
| Status | Active / Inactive |

### 8.8 Shift & Time Management

Shifts define the working time windows used across Attendance, Production, and Maintenance modules.

| Field | Notes |
|---|---|
| Shift Name | e.g., Morning, General, Afternoon, Night |
| Start Time / End Time | 24-hour format |
| Day Boundary | Time at which the calendar date resets (critical for night shifts that cross midnight) |
| Weekly Off Days | Days when the shift does not run |
| Planned Downtime Slots | Lunch, tea breaks — excluded from planned production time (affects OEE) |

Multiple shifts can be configured. Rotational shift scheduling (where employees cycle through different shifts) is supported.

### 8.9 Number Series (No Series) Configuration

No Series defines the document numbering format for every document type in the system. Each series is independent and can be configured per plant.

| Field | Notes |
|---|---|
| Series Code | Unique identifier |
| Description | Human-readable label |
| Linked Screen / Document Type | e.g., Sales Invoice, Purchase Order, GRN, Payslip |
| Prefix | e.g., `INV`, `PO`, `GRN` |
| Suffix | e.g., financial year code (`2526`) |
| Starting Number | e.g., `0001` |
| Padding | Zero-padding width |
| Increment | Usually 1 |

Example: A series configured as Prefix `INV-`, Suffix `-2526`, Starting `0001` with padding 4 produces: `INV-0001-2526`, `INV-0002-2526`, etc.

### 8.10 IOT Reason Master

The IOT Reason Master stores the predefined reasons for machine downtime, stoppages, breakdowns, and OEE losses. These reasons appear as selectable options when technicians log breakdowns or maintenance events.

| Field | Notes |
|---|---|
| Reason Type | Breakdown / Planned Maintenance / Quality Hold / Material Shortage / Operator Absence |
| Reason | Specific reason text (e.g., "Hydraulic pump failure") |
| Description | Optional longer description |
| Department | Which department typically raises this reason |
| Is Planned | Boolean — distinguishes planned stoppages from unplanned breakdowns |
| Duration (default) | Expected resolution time (informational) |

### 8.11 System Controls & Operational Settings

System controls are global operational switches for the tenant. Key controls include:

| Control | Type | Effect |
|---|---|---|
| Allow backdated attendance | Toggle | Whether past-date attendance entries are permitted |
| Lock payroll after disbursement | Toggle | Prevents modification of finalised payroll |
| Auto-approve leave for certain roles | Toggle | Bypasses approval for defined role types |
| Require department head approval for POs above threshold | Toggle + Amount | Two-level PO approval above a configured value |
| Enforce geo-fencing for mobile attendance | Toggle | GPS coordinates must be within branch radius |
| Auto-generate PM tasks | Toggle | Preventive maintenance tasks are auto-created on schedule |

### 8.12 Key Contacts

Three mandatory contacts must be registered:

- **Primary Contact** — Main point of contact for Avyren (billing, renewals)
- **HR Contact** — HR Manager or CHRO; receives compliance and payroll notifications
- **Finance Contact** — Finance Manager or CFO; receives payment and invoice notifications

---

## 9. Platform Lifecycle & Tenant States

### 9.1 Tenant Lifecycle

A tenant (company) passes through the following lifecycle states:

| State | Colour | Meaning | Transitions |
|---|---|---|---|
| **Draft** | Amber | Onboarding incomplete; not yet live | → Active (on activation) |
| **Pilot** | Blue | In free trial; full feature access | → Active (on payment); → Expired (no payment) |
| **Active** | Green | Fully live and operational | → Suspended (payment failure); → Cancelled (request) |
| **Suspended** | Orange | Payment failure; user login disabled | → Active (payment resolved) |
| **Inactive / Cancelled** | Red | Permanently deactivated | → terminal |

**Suspension behaviour:** When a tenant is suspended, all employee and user logins are disabled. The Super Admin retains read-only access to the tenant's data for audit and recovery purposes.

### 9.2 Data Portability & Offboarding

When a tenant is permanently offboarded:
- A final data export is generated in CSV, Excel, and PDF formats and provided to the customer
- All data is archived for the statutory retention period (typically 7 years per Indian law)
- After the retention period, data is purged as per the documented data destruction policy
- The PostgreSQL schema is dropped from the database

### 9.3 Audit Trail

Every configuration and data change across the platform is logged in the audit trail:

| Logged Event | Data Captured |
|---|---|
| Company Created | Timestamp, Super Admin ID, Company Code |
| Field Updated | Field name, old value, new value, changed by, timestamp |
| Status Changed | Old status, new status, changed by, timestamp |
| User Added / Removed | User ID, role, changed by, timestamp |
| Feature Toggle Changed | Feature name, old state, new state, changed by |
| Plant Added / Edited | Plant code, changed fields |
| Shift Added / Modified | Shift name, changed fields |
| No Series Modified | Series code, field changed |
| Bulk Import Executed | Target master, records imported / skipped / failed |
| Login / Logout Events | User ID, timestamp, IP address, device |
| MFA Events | Enrollment, verification, failure |

---

## 10. Glossary

| Term | Definition |
|---|---|
| **Avy ERP** | The Avyren Technologies enterprise resource planning platform |
| **Tenant** | A subscribing company with its own isolated environment within Avy ERP |
| **Super Admin** | Avyren Technologies' platform administrator; has cross-tenant access |
| **Company Admin** | The primary administrator of a tenant; managed by the customer company |
| **Schema** | A PostgreSQL namespace; each tenant's business data lives in its own schema |
| **Slug** | A URL-safe, lowercase identifier for a tenant (e.g., `tatagroup`) |
| **JWT** | JSON Web Token — the signed, short-lived credential used for API authentication |
| **Refresh Token** | A long-lived credential used to silently obtain new JWTs without re-login |
| **MFA** | Multi-Factor Authentication — a second verification step beyond password |
| **TOTP** | Time-Based One-Time Password — the 6-digit rotating code from an authenticator app |
| **RBAC** | Role-Based Access Control — governs what each user can see and do |
| **Feature Toggle** | A user-level permission override independent of role |
| **No Series** | Document number sequences configured per document type |
| **Plant** | A physical production facility within a company |
| **HQ** | Headquarters — the primary plant whose data reflects in company-level records |
| **IOT Reason** | A predefined reason for machine downtime used in production and maintenance modules |
| **ESS** | Employee Self-Service — the portal for employees to access their own HR data |
| **MSS** | Manager Self-Service — the portal for managers to handle approvals and team views |
| **Modular Monolith** | A single-deployable backend with clearly separated internal module boundaries |
| **Offline Queue** | Local storage for operations performed without connectivity; synced on reconnection |
| **PgBouncer** | A PostgreSQL connection pooler that manages database connections efficiently |
| **GRN** | Goods Receipt Note — records inward goods against an ASN |
| **ASN** | Advance Shipping Notice — sent by a vendor before goods dispatch |
| **PO** | Purchase Order — raised by the company to a vendor |
| **OEE** | Overall Equipment Effectiveness — Availability × Performance × Quality |
| **PM** | Preventive Maintenance — scheduled equipment maintenance tasks |

---

*This is Part 1 of 5 of the Avy ERP Master PRD.*
*Part 2 covers: Role-Based Access Control, Subscription Model, Offline Architecture, Analytics, and Non-Functional Requirements.*
*Part 3 covers: HR Management, Security, and Visitor Management modules.*
*Part 4 covers: Sales & Invoicing, Inventory, Vendor Management, and Finance modules.*
*Part 5 covers: Production, Machine Maintenance, Calibration, Quality Management, EHSS, CRM, and Project Management modules.*

---

**Document Control**

| Field | Value |
|---|---|
| Product | Avy ERP |
| Company | Avyren Technologies |
| Part | 1 of 5 — Platform Foundation, Vision & Architecture |
| Version | 2.0 |
| Date | April 2026 |
| Status | Final Draft |
| Classification | Confidential — Internal Use Only |
