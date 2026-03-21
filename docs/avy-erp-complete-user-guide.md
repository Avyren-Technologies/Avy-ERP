# AVY ERP — Complete System Guide

> A comprehensive guide for Super Admins, Company Admins, and HR teams to set up, configure, and operate the AVY ERP platform.

**Version:** 1.0
**Last Updated:** March 21, 2026

---

## Table of Contents

1. [System Overview](#1-system-overview)
   - 1.1 [Architecture](#11-architecture)
   - 1.2 [Role Hierarchy](#12-role-hierarchy)
   - 1.3 [Login & Authentication](#13-login--authentication)
2. [Super Admin Guide](#2-super-admin-guide)
   - 2.1 [First-Time Platform Setup](#21-first-time-platform-setup)
   - 2.2 [Tenant & Company Onboarding](#22-tenant--company-onboarding)
   - 2.3 [Company Management](#23-company-management)
   - 2.4 [Billing & Subscriptions](#24-billing--subscriptions)
   - 2.5 [Platform Monitoring](#25-platform-monitoring)
   - 2.6 [RBAC Management](#26-rbac-management)
3. [Company Admin Guide — Initial Setup](#3-company-admin-guide--initial-setup)
   - 3.1 [Setup Checklist (CRITICAL — Follow This Order)](#31-setup-checklist-critical--follow-this-order)
   - 3.2 [Dependency Map](#32-dependency-map)
4. [Company Admin Guide — HR Module](#4-company-admin-guide--hr-module)
   - 4.1 [Org Structure Setup](#41-org-structure-setup)
   - 4.2 [Employee Management](#42-employee-management)
   - 4.3 [Attendance Management](#43-attendance-management)
   - 4.4 [Leave Management](#44-leave-management)
   - 4.5 [Payroll Configuration](#45-payroll-configuration)
   - 4.6 [Payroll Operations](#46-payroll-operations)
   - 4.7 [ESS & Workflows](#47-ess--workflows)
   - 4.8 [Performance Management](#48-performance-management)
   - 4.9 [Recruitment & Training](#49-recruitment--training)
   - 4.10 [Exit & Separation](#410-exit--separation)
   - 4.11 [Transfers & Promotions](#411-transfers--promotions)
   - 4.12 [Advanced HR](#412-advanced-hr)
5. [Configuration Reference](#5-configuration-reference)
   - 5.1 [Number Series](#51-number-series)
   - 5.2 [System Controls](#52-system-controls)
   - 5.3 [Feature Toggles](#53-feature-toggles)
6. [Operations Modules (Coming Soon)](#6-operations-modules-coming-soon)
   - 6.1 [Inventory](#61-inventory)
   - 6.2 [Production](#62-production)
   - 6.3 [Maintenance](#63-maintenance)
7. [Troubleshooting](#7-troubleshooting)
   - 7.1 [Common Issues](#71-common-issues)
   - 7.2 [Data Dependencies Quick Reference](#72-data-dependencies-quick-reference)
8. [API Quick Reference](#8-api-quick-reference)
   - 8.1 [Authentication Endpoints](#81-authentication-endpoints)
   - 8.2 [Super Admin Endpoints](#82-super-admin-endpoints)
   - 8.3 [Company Admin Endpoints](#83-company-admin-endpoints)
   - 8.4 [HR Module Endpoints](#84-hr-module-endpoints)

---

## 1. System Overview

### 1.1 Architecture

AVY ERP is a multi-tenant enterprise resource planning platform built on a three-tier architecture:

| Layer | Technology | Purpose |
|-------|-----------|---------|
| **Backend** | Node.js / Express / Prisma ORM / PostgreSQL | REST API, business logic, data persistence |
| **Web App** | React / Vite / TailwindCSS | Admin dashboards, full HR management, reporting |
| **Mobile App** | React Native / Expo SDK 54 / Expo Router | On-the-go access, ESS, attendance, approvals |

**Key architectural decisions:**

- **Multi-tenant with schema isolation** — each company operates in its own tenant context, ensuring data segregation at the middleware level.
- **JWT-based authentication** — access tokens (short-lived) + refresh tokens (long-lived) for secure, stateless auth.
- **Role-based access control (RBAC)** — fine-grained permissions attached to roles, assigned to users.
- **Tenant middleware** — every API request (except auth) passes through `tenantMiddleware()` which resolves the tenant context from the authenticated user.

**Route structure:**

```
/api/v1/
  ├── auth/             # Authentication (no tenant required)
  ├── platform/         # Super Admin routes (platform:admin permission)
  │   ├── tenants/      # Tenant & company onboarding
  │   ├── companies/    # Company management
  │   ├── billing/      # Billing, invoices, payments, subscriptions
  │   ├── dashboard/    # Platform KPIs
  │   └── audit-logs/   # Platform audit trail
  ├── company/          # Company Admin routes (tenant-scoped)
  ├── dashboard/        # Company dashboard
  ├── rbac/             # Roles & permissions
  ├── feature-toggles/  # Per-user feature flags
  └── hr/               # Full HR module (11 sub-modules, 281 endpoints)
```

### 1.2 Role Hierarchy

```
Super Admin (Platform Owner)
  │
  ├── Manages all tenants/companies
  ├── Controls billing, subscriptions, module assignment
  ├── Views platform-wide audit logs
  └── Creates initial Company Admin users during onboarding
        │
        Company Admin (Per-Company)
          │
          ├── Manages company profile, locations, shifts
          ├── Configures HR module (org structure, payroll, leave, etc.)
          ├── Manages users, roles, permissions within their company
          └── Creates Employee records
                │
                Employee (ESS — Employee Self-Service)
                  │
                  ├── Views own profile, payslips, attendance
                  ├── Applies for leave, regularizes attendance
                  ├── Submits IT declarations, expense claims
                  └── Participates in appraisals, feedback
```

| Role | Permission Scope | Key Permissions |
|------|-----------------|-----------------|
| Super Admin | `platform:admin` | Full platform access — tenants, billing, audit |
| Company Admin | `company:*`, `user:*`, `hr:*`, `role:*`, `audit:read` | Full company + HR access |
| Employee (ESS) | `hr:read` (self only) | Self-service read/write on own data |

### 1.3 Login & Authentication

**Endpoints:** `POST /api/v1/auth/login`, `POST /api/v1/auth/register`

**Login flow:**

1. User submits email + password to `/auth/login`.
2. Server validates credentials, returns `accessToken` + `refreshToken`.
3. Client stores tokens; sends `Authorization: Bearer <accessToken>` on all subsequent requests.
4. When access token expires, client calls `POST /auth/refresh-token` with the refresh token.
5. On logout, call `POST /auth/logout` to invalidate the session.

**Password management:**

- `POST /auth/forgot-password` — sends a reset code via email
- `POST /auth/verify-reset-code` — validates the code
- `POST /auth/reset-password` — sets a new password using the verified code
- `POST /auth/change-password` — for logged-in users to change their password

**User-Employee auto-linking:** When a User is created with an email that matches an existing Employee's `personalEmail` or `officialEmail`, the system automatically links them. This also works in reverse — creating an Employee whose email matches an existing User triggers the link.

---

## 2. Super Admin Guide

### 2.1 First-Time Platform Setup

After your first login as Super Admin, follow these steps in order:

1. **Configure billing defaults** — Go to Billing > Config and set:
   - Default one-time license fee multiplier
   - Default AMC percentage
   - GST rates (CGST, SGST, IGST)
   - Platform GSTIN
   - Invoice number prefix

2. **Create your first tenant** — Use the 16-step onboarding wizard (see Section 2.2) to onboard your first company.

3. **Verify the dashboard** — Check that platform stats (total tenants, active companies, revenue metrics) are populating correctly.

4. **Set up audit log monitoring** — Review audit log filter options to understand what events are being tracked.

### 2.2 Tenant & Company Onboarding

The onboarding wizard (`POST /platform/tenants/onboard`) collects all company data in 16 steps. Each step corresponds to a section of the onboarding payload.

#### The 16-Step Wizard

| Step | Section | What You Configure | Required? |
|------|---------|-------------------|-----------|
| 1 | **Company Identity** | Display name, legal name, business type, industry, company code, email domain, CIN, logo | Yes |
| 2 | **Statutory & Tax** | PAN, TAN, GSTIN, PF registration, ESI code, Professional Tax registration, LWF, ROC state | Yes |
| 3 | **Address** | Registered address (line1, city, state, PIN, country); optionally separate corporate address | Yes |
| 4 | **Fiscal & Calendar** | Fiscal year type, payroll frequency, cutoff day, disbursement day, week start, timezone, working days | Yes |
| 5 | **Preferences** | Currency, language, date format, India compliance, ESS, mobile/web app, biometric, bank integration, email/WhatsApp notifications, RazorpayX integration | Yes |
| 6 | **Backend Endpoint** | `default` (cloud-hosted) or `custom` (self-hosted URL with health check) | Yes |
| 7 | **Multi-Location Strategy** | Multi-location mode on/off, module configuration mode (`common` or `per-location`) | Yes |
| 8 | **Locations** | At least one plant/branch with name, code, facility type, address, contact, geo-fencing settings | Yes (min 1) |
| 9 | **Module Selection & Pricing** | Selected modules from catalogue, custom pricing, user tier (starter/growth/scale/enterprise/custom), billing type, trial days | No |
| 10 | **Key Contacts** | Primary/secondary contacts with name, designation, email, phone | No |
| 11 | **Shifts & Time** | Day boundary times, weekly offs, shift definitions with downtime slots | No |
| 12 | **Number Series** | Auto-numbering rules for Employee IDs, invoices, etc. (prefix, suffix, digit count, start number) | No |
| 13 | **IOT Reasons** | Reason codes for production downtime (type, reason, department, planned/unplanned, duration) | No |
| 14 | **System Controls** | Toggle switches for MFA, NC edit mode, load/unload, cycle time, payroll lock, leave carry-forward, overtime approval | No |
| 15 | **Users** | Initial user accounts (full name, username, password, role, email, mobile, department) | No |
| 16 | **Activation** | Review all data and activate the tenant | — |

> **Tip:** Steps 1-8 are required for a valid onboarding. Steps 9-15 can be configured later by the Company Admin. However, setting up Number Series (Step 12) early is recommended — Employee ID generation depends on it.

#### Module Catalogue

The platform includes 10 modules that can be assigned to companies:

- HR & Payroll
- Attendance & Leave
- Production & Manufacturing
- Inventory & Warehouse
- Maintenance & Asset
- Visitor Management
- Quality Control
- IoT & Machine Integration
- Reports & Analytics
- Employee Self-Service (ESS)

Modules can be assigned either commonly (same for all locations) or per-location depending on the multi-location strategy chosen in Step 7.

#### User Tiers

| Tier | User Limit | Typical Use |
|------|-----------|-------------|
| Starter | Up to 25 users | Small teams |
| Growth | Up to 100 users | Growing companies |
| Scale | Up to 500 users | Mid-size enterprises |
| Enterprise | Up to 2000 users | Large organizations |
| Custom | Configurable | Special requirements |

### 2.3 Company Management

**Navigation:** Dashboard > Companies (Web) or Companies tab (Mobile)

#### Viewing Companies

- `GET /platform/companies/` — paginated list with search and filters
- `GET /platform/companies/:companyId` — full company detail with all sections

#### Company Status Lifecycle

```
Draft ──→ Pilot ──→ Active ──→ Inactive
  │                              ↑
  └──────────────────────────────┘
```

| Status | Meaning |
|--------|---------|
| **Draft** | Onboarding in progress; company data incomplete |
| **Pilot** | Trial period; company testing the system |
| **Active** | Fully operational; billing active |
| **Inactive** | Suspended or decommissioned |

**Changing status:** `PUT /platform/companies/:companyId/status` with `{ status: "Active" }`

#### Editing Company Sections

Use `PATCH /platform/companies/:companyId/sections/:sectionKey` to update any section without touching other data. Valid section keys:

`identity`, `statutory`, `address`, `fiscal`, `preferences`, `endpoint`, `strategy`, `controls`, `locations`, `contacts`, `shifts`, `noSeries`, `iotReasons`, `users`, `commercial`

### 2.4 Billing & Subscriptions

#### Billing Dashboard

| Endpoint | Purpose |
|----------|---------|
| `GET /platform/billing/summary` | Revenue KPIs (MRR, ARR, outstanding) |
| `GET /platform/billing/revenue-chart` | Monthly revenue chart data |

#### Billing Configuration

`GET/PATCH /platform/billing/config/defaults` — Set platform-wide billing defaults:

- `defaultOneTimeMultiplier` — multiplier for one-time license fees
- `defaultAmcPercentage` — Annual Maintenance Contract percentage
- `defaultCgstRate`, `defaultSgstRate`, `defaultIgstRate` — GST rates
- `platformGstin` — the platform's own GSTIN
- `invoicePrefix` — prefix for invoice numbers (e.g., "AVY-INV-")

#### Invoices

| Action | Endpoint | Notes |
|--------|----------|-------|
| List invoices | `GET /platform/billing/invoices/` | Filterable by company, status, date |
| Generate invoice | `POST /platform/billing/invoices/generate` | Types: `SUBSCRIPTION`, `ONE_TIME_LICENSE`, `AMC`, `PRORATED_ADJUSTMENT` |
| Mark as paid | `PATCH .../invoices/:id/mark-paid` | Requires payment method + optional transaction ref |
| Void invoice | `PATCH .../invoices/:id/void` | Cannot be undone |
| Email invoice | `POST .../invoices/:id/send-email` | Sends to company contact |
| Download PDF | `GET .../invoices/:id/pdf` | Returns PDF binary |

#### Payments

- `GET /platform/billing/payments/` — list payments (filter by company, invoice, method, date range)
- `POST /platform/billing/payments/record` — record a payment against an invoice

Payment methods: `BANK_TRANSFER`, `CHEQUE`, `CASH`, `RAZORPAY`, `UPI`, `OTHER`

#### Subscriptions

| Action | Endpoint |
|--------|----------|
| View subscription | `GET .../subscriptions/:companyId` |
| Preview cost changes | `GET .../subscriptions/:companyId/cost-preview` |
| Change billing type | `PATCH .../subscriptions/:companyId/billing-type` |
| Change user tier | `PATCH .../subscriptions/:companyId/tier` |
| Extend trial | `PATCH .../subscriptions/:companyId/trial` |
| Cancel | `POST .../subscriptions/:companyId/cancel` |
| Reactivate | `POST .../subscriptions/:companyId/reactivate` |

Billing types: `MONTHLY`, `ANNUAL`, `ONE_TIME_AMC`

### 2.5 Platform Monitoring

#### Dashboard

| Endpoint | Data |
|----------|------|
| `GET /platform/dashboard/stats` | Total tenants, active companies, user counts, module adoption |
| `GET /platform/dashboard/activity` | Recent platform events (onboardings, status changes, logins) |
| `GET /platform/dashboard/revenue` | Revenue metrics, growth trends |

#### Audit Logs

- `GET /platform/audit-logs/` — paginated, filterable by action, entity type, user, date range
- `GET /platform/audit-logs/filters` — available filter options (action types + entity types)
- `GET /platform/audit-logs/entity/:entityType/:entityId` — logs for a specific entity
- `GET /platform/audit-logs/:id` — single audit log detail

> **Tip:** Use the filters endpoint first to populate dropdown menus in your UI, then query with those filter values.

### 2.6 RBAC Management

**Base path:** `/api/v1/rbac`

RBAC is shared infrastructure used by both Super Admin and Company Admin contexts.

#### Roles

| Action | Endpoint |
|--------|----------|
| List roles | `GET /rbac/roles` |
| Create role | `POST /rbac/roles` — name + description + permissions[] |
| Update role | `PUT /rbac/roles/:id` |
| Delete role | `DELETE /rbac/roles/:id` |
| Assign role to user | `POST /rbac/roles/assign` — userId + roleId |

#### Reference Roles

`GET /rbac/reference-roles` — returns template roles that can be cloned as a starting point for custom roles.

#### Permission Catalogue

`GET /rbac/permissions` — returns the full list of available permissions that can be assigned to roles.

Common permission patterns:
- `platform:admin` — super admin access
- `company:read`, `company:create`, `company:update`, `company:delete`
- `user:read`, `user:create`, `user:update`
- `hr:read`, `hr:create`, `hr:update`, `hr:delete`
- `role:read`, `role:create`, `role:update`, `role:delete`
- `audit:read`
- `location:write`

---

## 3. Company Admin Guide — Initial Setup

### 3.1 Setup Checklist (CRITICAL — Follow This Order)

After your Super Admin has onboarded your company, follow this checklist in sequence. Each step builds on the previous ones.

| # | Task | Where | Why | Dependencies |
|---|------|-------|-----|--------------|
| 1 | **Review Company Profile** | Company > Profile | Verify company details, logo, statutory info, addresses that were set during onboarding | None |
| 2 | **Configure Locations** | Company > Locations | Locations are created by Super Admin during onboarding. You can edit addresses, contacts, and geo-fencing, but cannot create new ones | None |
| 3 | **Set Up Shifts** | Company > Shifts & Time | Define working shifts (General, Morning, Night, etc.) with start/end times and downtime slots. Required before attendance tracking | None |
| 4 | **Configure Key Contacts** | Company > Contacts | Add primary, secondary, and emergency contacts for the company | None |
| 5 | **Set Up Number Series** | Configuration > Number Series | Define auto-numbering for Employee IDs, invoices, purchase orders, etc. The "Employee" linked screen is critical — without it, employee IDs cannot be auto-generated | None |
| 6 | **Configure IOT Reasons** | Configuration > IOT Reasons | Only if using production/manufacturing module. Define downtime reason codes | None |
| 7 | **Set System Controls** | Configuration > System Controls | Enable/disable MFA, payroll lock, overtime approval, leave carry-forward, etc. | None |
| 8 | **Configure Company Settings** | Configuration > Settings | Set locale preferences (currency, language, date format), compliance modes, app access toggles | None |
| 9 | **Create Departments** | HR & People > Departments | Foundation of the org structure. Supports hierarchy via parent departments. Must be created before designations and cost centres | None |
| 10 | **Create Grades** | HR & People > Grades & Bands | Define salary bands with CTC ranges, HRA percentages, PF tiers, benefit flags, probation/notice periods. Must be created before designations | None |
| 11 | **Create Employee Types** | HR & People > Employee Types | Define Full-Time, Part-Time, Contract, etc. with statutory applicability flags (PF, ESI, PT, Gratuity, Bonus). Must be created before employees | None |
| 12 | **Create Cost Centres** | HR & People > Cost Centres | Financial tracking units linked to departments and optionally to locations | Departments |
| 13 | **Create Designations** | HR & People > Designations | Job titles with department, grade, job level (L1-L7), managerial flag, reporting structure, probation days | Departments, Grades |
| 14 | **Create Roles & Permissions** | People & Access > Roles | Define RBAC roles for your company users. Use reference roles as templates | None |
| 15 | **Create Users** | People & Access > Users | Login accounts for your team. If a user's email matches an existing employee, they auto-link | Roles (recommended) |
| 16 | **Create Employees** | HR & People > Employee Directory | Full 6-tab employee records. This is the most complex step — see Section 4.2 for details | Departments, Designations, Employee Types, Number Series |

> :warning: **WARNING:** Do not attempt to create Employees before completing steps 9-13. The employee form requires Department, Designation, and Employee Type selections. If these don't exist, you'll get empty dropdowns.

> :warning: **WARNING:** Do not skip Number Series setup (step 5) if you want auto-generated Employee IDs. Without a series linked to the "Employee" screen, the system cannot generate IDs.

> :warning: **WARNING:** Locations can only be created by the Super Admin (the `POST /company/locations` endpoint returns HTTP 403). As Company Admin, you can only edit or delete existing locations.

### 3.2 Dependency Map

The following diagram shows which features depend on which. Set up items on the left before items on the right.

```
                    FOUNDATION LAYER                    HR LAYER                    OPERATIONS LAYER
                    ================                    ========                    ================

Locations (Super Admin creates) ──────────────────┐
                                                  │
Departments ──────────────────────────────────────┤
  │                                               │
  ├──→ Cost Centres (needs Departments + Location)│
  │                                               │
Grades ───────────────────────────────────────────┤
  │                                               │
  └──→ Designations (needs Depts + Grades) ───────┤
                                                  │
Employee Types ───────────────────────────────────┤
                                                  │
Shifts ───────────────────────────────────────────┤
                                                  │
Number Series ("Employee" linked screen) ─────────┤
                                                  │
                                                  ▼
                                            EMPLOYEES ──────────┐
                                              │                 │
                                              │    Users ───────┤ (auto-link via email)
                                              │                 │
                                              ├─────────────────┼──→ Attendance Records
                                              │                 │      (needs Employee + Shift)
                                              │                 │
                                              │                 ├──→ Leave Requests
                                              │                 │      (needs Employee + Leave Type + Balance)
                                              │                 │
                                              │                 ├──→ Employee Salary
                                              │                 │      (needs Employee + Salary Structure)
                                              │                 │
                                              │                 ├──→ Payroll Run
                                              │                 │      (needs Employees with assigned salaries)
                                              │                 │
                                              │                 ├──→ Appraisals
                                              │                 │      (needs Employee + Appraisal Cycle)
                                              │                 │
                                              │                 ├──→ Transfers / Promotions
                                              │                 │      (needs Employee + target Dept/Designation)
                                              │                 │
                                              │                 └──→ Exit & F&F
                                              │                        (needs Employee)
                                              │
                                              └──→ ESS Access
                                                     (needs User linked to Employee)

CONFIGURATION (Independent — set up any time):
  ├── Leave Types ──→ Leave Policies ──→ Leave Balances
  ├── Salary Components ──→ Salary Structures
  ├── Attendance Rules, Holiday Calendar, Rosters, Overtime Rules
  ├── Statutory Configs (PF, ESI, PT, Gratuity, Bonus, LWF, Tax)
  ├── Loan Policies
  ├── ESS Config, Approval Workflows, Notification Templates/Rules
  ├── Skills Library
  ├── Asset Categories
  ├── Letter Templates
  └── Grievance Categories
```

---

## 4. Company Admin Guide — HR Module

### 4.1 Org Structure Setup

The org structure is the backbone of your HR system. All five master tables should be set up before creating employees.

**Navigation:** HR & People section in the sidebar

#### 4.1.1 Departments

**What:** Organizational units that employees belong to (Engineering, Finance, HR, Operations, etc.)

**Key feature:** Self-referencing hierarchy — a department can have a parent department, enabling org trees.

| Field | Required | Notes |
|-------|----------|-------|
| `name` | Yes | 1-100 characters |
| `code` | Yes | 1-20 characters, unique |
| `parentId` | No | Parent department ID for hierarchy |
| `headEmployeeId` | No | Department head (set after creating employees) |
| `costCentreCode` | No | Linked cost centre |
| `status` | No | `Active` or `Inactive` (default: Active) |

> **Tip:** Create top-level departments first (e.g., "Engineering"), then create sub-departments with `parentId` pointing to the parent (e.g., "Frontend" under "Engineering").

#### 4.1.2 Designations

**What:** Job titles mapped to departments and grades (Software Engineer, Senior Manager, VP Operations, etc.)

**Dependencies:** Requires at least one Department and one Grade to exist.

| Field | Required | Notes |
|-------|----------|-------|
| `name` | Yes | 1-100 characters |
| `code` | Yes | 1-20 characters, unique |
| `departmentId` | No | Which department this role belongs to |
| `gradeId` | No | Salary grade band |
| `jobLevel` | No | `L1` through `L7` |
| `managerialFlag` | No | Whether this is a managerial role |
| `reportsTo` | No | Designation ID this reports to |
| `probationDays` | No | Probation period in days |
| `status` | No | `Active` or `Inactive` |

> **Tip:** Set `managerialFlag: true` for roles that will have direct reports. This affects approval workflows and team views.

#### 4.1.3 Grades

**What:** Salary bands that define compensation ranges and statutory applicability tiers.

| Field | Required | Notes |
|-------|----------|-------|
| `name` | Yes | e.g., "Grade A", "Senior Band" |
| `code` | Yes | e.g., "GR-A", "SR-BAND" |
| `ctcMin` | No | Minimum CTC for this grade |
| `ctcMax` | No | Maximum CTC for this grade |
| `hraPercent` | No | HRA percentage (0-100) |
| `pfTier` | No | `Applicable`, `Not Applicable`, or `Optional` |
| `benefitFlags` | No | Key-value pairs for benefits (e.g., `{ "healthInsurance": true }`) |
| `probationMonths` | No | Default probation period for this grade |
| `noticeDays` | No | Default notice period for this grade |

> **Tip:** Define grades from junior to senior (e.g., G1 through G7) and set progressively higher CTC ranges. The `pfTier` field is important for India compliance — PF applicability changes based on salary thresholds.

#### 4.1.4 Employee Types

**What:** Employment categories with statutory applicability flags.

| Field | Required | Notes |
|-------|----------|-------|
| `name` | Yes | e.g., "Full Time", "Part Time", "Contract", "Intern" |
| `code` | Yes | e.g., "FT", "PT", "CON", "INT" |
| `pfApplicable` | Yes | Is Provident Fund applicable? |
| `esiApplicable` | Yes | Is ESI applicable? |
| `ptApplicable` | Yes | Is Professional Tax applicable? |
| `gratuityEligible` | Yes | Is the employee eligible for gratuity? |
| `bonusEligible` | Yes | Is the employee eligible for statutory bonus? |

> :warning: **IMPORTANT:** All five statutory flags are required. Get this right at setup — these flags determine which deductions are calculated during payroll. For example, contractors typically have all flags set to `false`, while full-time employees have them `true`.

#### 4.1.5 Cost Centres

**What:** Financial tracking units for budgeting and cost allocation.

**Dependencies:** Requires at least one Department.

| Field | Required | Notes |
|-------|----------|-------|
| `name` | Yes | e.g., "Engineering - Cloud Infrastructure" |
| `code` | Yes | e.g., "CC-ENG-CLOUD" |
| `departmentId` | No | Linked department |
| `locationId` | No | Linked location |
| `annualBudget` | No | Annual budget allocation |
| `glAccountCode` | No | General ledger account code for accounting integration |

### 4.2 Employee Management

**Navigation:** HR & People > Employee Directory

#### Creating Employees — The 6-Tab Form

The employee record is the most comprehensive form in the system. It spans six tabs:

**Tab 1: Personal Information**

| Field | Required | Notes |
|-------|----------|-------|
| `firstName`, `lastName` | Yes | |
| `dateOfBirth` | Yes | ISO date |
| `gender` | Yes | `MALE`, `FEMALE`, `NON_BINARY`, `PREFER_NOT_TO_SAY` |
| `personalMobile` | Yes | Min 10 digits |
| `personalEmail` | Yes | Used for User-Employee auto-linking |
| `emergencyContactName` | Yes | |
| `emergencyContactRelation` | Yes | |
| `emergencyContactMobile` | Yes | Min 10 digits |
| `middleName`, `maritalStatus`, `bloodGroup`, `fatherMotherName`, `nationality`, `religion`, `category` | No | |
| `currentAddress`, `permanentAddress` | No | Object: `{ line1, line2, city, state, pin, country }` |

**Tab 2: Professional Information**

| Field | Required | Notes |
|-------|----------|-------|
| `joiningDate` | Yes | ISO date |
| `departmentId` | Yes | Must exist in Departments |
| `designationId` | Yes | Must exist in Designations |
| `employeeTypeId` | Yes | Must exist in Employee Types |
| `gradeId` | No | Links to Grade for salary band |
| `reportingManagerId` | No | Another employee's ID |
| `workType` | No | `ON_SITE`, `REMOTE`, `HYBRID` |
| `shiftId` | No | Links to a Shift |
| `locationId` | No | Links to a Location |
| `costCentreId` | No | Links to a Cost Centre |

**Tab 3: Salary Information**

| Field | Required | Notes |
|-------|----------|-------|
| `annualCtc` | No | Positive number |
| `salaryStructure` | No | Arbitrary key-value pairs |
| `paymentMode` | No | `NEFT`, `IMPS`, `CHEQUE` |

**Tab 4: Bank Details**

| Field | Required | Notes |
|-------|----------|-------|
| `bankAccountNumber` | No | |
| `bankIfscCode` | No | |
| `bankName` | No | |
| `bankBranch` | No | |
| `accountType` | No | `SAVINGS` or `CURRENT` |

**Tab 5: Documents & Statutory IDs**

| Field | Notes |
|-------|-------|
| `panNumber` | PAN card |
| `aadhaarNumber` | Aadhaar card |
| `uan` | Universal Account Number (PF) |
| `esiIpNumber` | ESI IP number |
| `passportNumber`, `passportExpiry` | Passport details |
| `drivingLicence`, `voterId`, `pran` | Other IDs |

Documents can also be uploaded via the sub-resource: `POST /hr/employees/:id/documents`

**Tab 6: Timeline**

Read-only. `GET /hr/employees/:id/timeline` — shows auto-logged events like creation, status changes, transfers, promotions.

#### Employee ID Auto-Generation

When you create an employee, the system looks for a Number Series with `linkedScreen: "Employee"`. If found, it generates the next ID using the series pattern:

```
Example: Prefix = "EMP-", Digit Count = 4, Start Number = 1
Generated IDs: EMP-0001, EMP-0002, EMP-0003, ...
```

> :warning: **If no "Employee" Number Series exists, the employee ID field must be set manually or the creation will fail.**

#### Employee Sub-Resources

Each employee has additional data managed through sub-resource endpoints:

| Sub-Resource | Endpoints | Notes |
|-------------|-----------|-------|
| **Nominees** | `GET/POST/PATCH/DELETE /employees/:id/nominees` | PF/insurance nominees with share percentages |
| **Education** | `GET/POST/PATCH/DELETE /employees/:id/education` | Academic records |
| **Previous Employment** | `GET/POST/PATCH/DELETE /employees/:id/previous-employment` | Work history with CTC, experience/relieving letters |
| **Documents** | `GET/POST/PATCH/DELETE /employees/:id/documents` | Uploaded documents with type, number, expiry |
| **Timeline** | `GET /employees/:id/timeline` | Read-only event log |

#### Employee Status Lifecycle

```
PROBATION ──→ ACTIVE ──→ CONFIRMED ──→ ON_NOTICE ──→ EXITED
                                         ↑
                                    SUSPENDED
```

Change status via `PATCH /hr/employees/:id/status` with:
- `status` — required, one of: `ACTIVE`, `PROBATION`, `CONFIRMED`, `ON_NOTICE`, `SUSPENDED`, `EXITED`
- `lastWorkingDate` — optional (required for EXITED)
- `exitReason` — optional

> **Note:** Deleting an employee is a soft delete — it sets the status to `EXITED` rather than removing the record.

### 4.3 Attendance Management

**Prerequisites:** Shifts must be defined. Employees must exist.

**Navigation:** Attendance section in the sidebar

#### 4.3.1 Attendance Dashboard

`GET /hr/attendance` — list attendance records with filters for employee, date range, status.
`GET /hr/attendance/summary` — aggregated attendance metrics.

#### 4.3.2 Attendance Records

Create attendance records with:

| Field | Required | Notes |
|-------|----------|-------|
| `employeeId` | Yes | |
| `date` | Yes | ISO date |
| `status` | Yes | `PRESENT`, `ABSENT`, `HALF_DAY`, `LATE`, `ON_LEAVE`, `HOLIDAY`, `WEEK_OFF`, `LOP` |
| `source` | Yes | `BIOMETRIC`, `FACE_RECOGNITION`, `MOBILE_GPS`, `WEB_PORTAL`, `MANUAL`, `IOT`, `SMART_CARD` |
| `shiftId` | No | The shift for this day |
| `punchIn`, `punchOut` | No | ISO datetime |
| `locationId` | No | Where attendance was recorded |

#### 4.3.3 Holiday Calendar

| Type | Description |
|------|-------------|
| `NATIONAL` | Applies to all employees (e.g., Republic Day, Independence Day) |
| `REGIONAL` | State-specific holidays |
| `COMPANY` | Company-declared holidays |
| `OPTIONAL` | Employees choose from a pool (controlled by `maxOptionalSlots`) |
| `RESTRICTED` | Limited holidays with restrictions |

**Clone holidays:** `POST /hr/holidays/clone` with `{ fromYear: 2025, toYear: 2026 }` to copy last year's calendar.

#### 4.3.4 Rosters

Define work patterns:

| Pattern | Description |
|---------|-------------|
| `MON_FRI` | Monday to Friday |
| `MON_SAT` | Monday to Saturday |
| `MON_SAT_ALT` | Monday to Saturday with alternate Saturdays off |
| `CUSTOM` | Custom pattern with configurable week-offs |

#### 4.3.5 Attendance Rules (Singleton)

| Setting | Purpose |
|---------|---------|
| `halfDayThresholdHours` | Hours below which attendance is marked as half-day |
| `fullDayThresholdHours` | Hours required for full-day |
| `lateArrivalsAllowed` | Number of late arrivals allowed per month |
| `gracePeriodMinutes` | Grace period before marking late |
| `lopAutoDeduct` | Automatically deduct LOP for absences |
| `selfieRequired` | Require selfie with attendance punch |
| `gpsRequired` | Require GPS location with punch |

#### 4.3.6 Overtime Rules (Singleton)

| Setting | Purpose |
|---------|---------|
| `rateMultiplier` | Overtime pay multiplier (e.g., 1.5x, 2x) |
| `thresholdMinutes` | Minimum overtime minutes before it counts |
| `monthlyCap`, `weeklyCap` | Maximum overtime hours |
| `autoIncludePayroll` | Auto-include overtime in payroll calculation |
| `approvalRequired` | Require manager approval for overtime |

#### 4.3.7 Overrides / Regularization

Employees or managers can request corrections:

- `POST /hr/attendance/overrides` — create override request
- Issue types: `MISSING_PUNCH_IN`, `MISSING_PUNCH_OUT`, `ABSENT_OVERRIDE`, `LATE_OVERRIDE`, `NO_PUNCH`
- `PATCH /hr/attendance/overrides/:id` — approve or reject (`APPROVED` / `REJECTED`)

### 4.4 Leave Management

**Prerequisites:** Employees must exist. Leave Types must be defined.

**Navigation:** Leave Management section in the sidebar

#### 4.4.1 Leave Types

Define the types of leave available to employees:

| Field | Required | Notes |
|-------|----------|-------|
| `name` | Yes | e.g., "Earned Leave", "Sick Leave", "Casual Leave" |
| `code` | Yes | e.g., "EL", "SL", "CL" |
| `category` | Yes | `PAID`, `UNPAID`, `COMPENSATORY`, `STATUTORY` |
| `annualEntitlement` | Yes | Number of days per year |
| `accrualFrequency` | No | `MONTHLY`, `QUARTERLY`, `ANNUAL`, `PRO_RATA`, `UPFRONT` |
| `carryForwardAllowed` | No | Can unused days roll over? |
| `maxCarryForwardDays` | No | Maximum carry-forward |
| `encashmentAllowed` | No | Can unused days be encashed? |
| `allowHalfDay` | No | Allow half-day applications? |
| `weekendSandwich` | No | Count weekends between leave days? |
| `holidaySandwich` | No | Count holidays between leave days? |
| `documentRequired` | No | Require supporting document? |
| `documentAfterDays` | No | Document required if leave exceeds N days |
| `probationRestricted` | No | Block leave during probation? |

> **Tip for India compliance:** Set up at minimum: Earned Leave (PAID, 15 days), Casual Leave (PAID, 7 days), Sick Leave (PAID, 7 days), and Maternity Leave (STATUTORY, 182 days, applicableGender: FEMALE).

#### 4.4.2 Leave Policies

Map leave types to organizational levels:

- `assignmentLevel`: `company`, `department`, `designation`, `grade`, `employeeType`, `individual`
- `assignmentId`: the ID of the target (e.g., a department ID when level is "department")
- `overrides`: override default settings for this policy level

#### 4.4.3 Leave Balances

- `POST /hr/leave-balances/initialize` — initialize balances for an employee for a year
- `POST /hr/leave-balances/adjust` — credit or debit days with a reason

#### 4.4.4 Leave Requests

- `POST /hr/leave-requests` — apply for leave (employeeId, leaveTypeId, fromDate, toDate, days, reason)
- `PATCH /hr/leave-requests/:id/approve` — approve with optional note
- `PATCH /hr/leave-requests/:id/reject` — reject with required note
- `PATCH /hr/leave-requests/:id/cancel` — cancel a pending/approved request

#### 4.4.5 Sandwich Rules

When `weekendSandwich: true` on a leave type, if an employee takes Friday and Monday off, Saturday and Sunday are also counted as leave days. Similarly for `holidaySandwich`.

### 4.5 Payroll Configuration

**Prerequisites:** Employees must exist. Grades and Designations should be set up for salary structure mapping.

**Navigation:** Payroll & Compliance section in the sidebar

**Setup order — follow this sequence:**

#### Step 1: Salary Components

Define the building blocks of a salary:

| Field | Notes |
|-------|-------|
| `name` | e.g., "Basic Salary", "HRA", "Conveyance" |
| `code` | e.g., "BASIC", "HRA", "CONV" |
| `type` | `EARNING`, `DEDUCTION`, `EMPLOYER_CONTRIBUTION` |
| `calculationMethod` | `FIXED`, `PERCENT_OF_BASIC`, `PERCENT_OF_GROSS`, `FORMULA` |
| `taxable` | `FULLY_TAXABLE`, `PARTIALLY_EXEMPT`, `FULLY_EXEMPT` |
| `pfInclusion`, `esiInclusion` | Whether this component is included in PF/ESI calculation |
| `showOnPayslip` | Whether to display on the payslip |

> **Tip:** Create Basic Salary first (type: EARNING, calculation: FIXED, pfInclusion: true). Then create HRA (PERCENT_OF_BASIC), Special Allowance, etc. For deductions, create PF Employee (DEDUCTION), ESI Employee (DEDUCTION), Professional Tax (DEDUCTION).

#### Step 2: Salary Structures

Group components into named structures:

```json
{
  "name": "Standard CTC Structure - Grade A",
  "code": "STD-GR-A",
  "applicableGradeIds": ["grade-a-id"],
  "components": [
    { "componentId": "basic-id", "calculationMethod": "PERCENT_OF_GROSS", "value": 40 },
    { "componentId": "hra-id", "calculationMethod": "PERCENT_OF_BASIC", "value": 50 },
    { "componentId": "special-id", "calculationMethod": "FORMULA", "formula": "GROSS - BASIC - HRA" }
  ]
}
```

#### Step 3: Employee Salary

Assign a salary structure to an employee:

```json
{
  "employeeId": "emp-uuid",
  "structureId": "structure-uuid",
  "annualCtc": 1200000,
  "effectiveFrom": "2026-04-01"
}
```

#### Step 4: Statutory Configuration

Configure India-specific statutory deductions:

| Config | Endpoint | Key Fields |
|--------|----------|------------|
| **PF Config** | `GET/PATCH /hr/payroll/pf-config` | Employee rate (12%), employer EPF/EPS/EDLI rates, wage ceiling (15,000), VPF toggle |
| **ESI Config** | `GET/PATCH /hr/payroll/esi-config` | Employee rate (0.75%), employer rate (3.25%), wage ceiling (21,000) |
| **PT Config** | `GET/POST/PATCH/DELETE /hr/payroll/pt-configs` | State-wise slabs with tax amounts, frequency (monthly/semi-annual) |
| **Gratuity** | `GET/PATCH /hr/payroll/gratuity-config` | Formula, max amount, provision method (monthly or at exit) |
| **Bonus** | `GET/PATCH /hr/payroll/bonus-config` | Wage ceiling, min/max bonus %, eligibility days, calculation period |
| **LWF** | `GET/POST/PATCH/DELETE /hr/payroll/lwf-configs` | State-wise employee + employer amounts, frequency |

#### Step 5: Tax & TDS Configuration

`GET/PATCH /hr/payroll/tax-config`:

- `defaultRegime` — `OLD` or `NEW` (post-2023 new regime is default)
- `oldRegimeSlabs` / `newRegimeSlabs` — array of `{ fromAmount, toAmount, rate }` slabs
- `surchargeRates` — for high-income surcharges
- `cessRate` — health and education cess (currently 4%)
- `declarationDeadline` — deadline for IT declaration submission

#### Step 6: Bank Configuration

`GET/PATCH /hr/payroll/bank-config`:

- Company's salary disbursement bank account
- Payment mode (NEFT, RTGS, IMPS)
- File format for bank uploads
- `autoPushOnApproval` — auto-push payment file on payroll approval

#### Step 7: Loan Policies & Loans

**Loan Policies:** Define types of loans (salary advance, personal loan, etc.) with:
- Maximum amount, tenure, interest rate
- EMI cap as percentage of salary
- Eligibility tenure (minimum days of employment)

**Loan Records:** Issue loans to employees against policies with auto-calculated or manual EMI amounts.

Loan status lifecycle: `PENDING` -> `APPROVED` -> `ACTIVE` -> `CLOSED` (or `REJECTED`)

### 4.6 Payroll Operations

**Prerequisites:** Payroll Configuration must be complete. Employees must have assigned salaries.

**Navigation:** Payroll Operations section in the sidebar

#### 4.6.1 Payroll Run — The 6-Step Wizard

A payroll run processes salaries for a specific month/year. The 6 steps must be executed in sequence:

| Step | Endpoint | What Happens |
|------|----------|-------------|
| 1. **Lock Attendance** | `PATCH /payroll-runs/:id/lock-attendance` | Freezes attendance data for the period; no more edits allowed |
| 2. **Review Exceptions** | `PATCH /payroll-runs/:id/review-exceptions` | Flags employees with attendance anomalies (missing punches, excess LOP) |
| 3. **Compute Salaries** | `PATCH /payroll-runs/:id/compute` | Calculates gross, deductions, net pay for each employee |
| 4. **Statutory Deductions** | `PATCH /payroll-runs/:id/statutory` | Computes PF, ESI, PT, TDS based on configs |
| 5. **Approve** | `PATCH /payroll-runs/:id/approve` | Locks the run for disbursement |
| 6. **Disburse** | `PATCH /payroll-runs/:id/disburse` | Marks salaries as disbursed |

> **Tip:** After step 3, review individual entries via `GET /payroll-runs/:id/entries`. You can override specific component values via `PATCH /payroll-runs/:id/entries/:eid` before approving.

#### 4.6.2 Payslips

After a payroll run is approved, generate payslips:

- `POST /hr/payroll-runs/:id/generate-payslips` — batch-generate for all employees in the run
- `GET /hr/payslips` — list all payslips
- `POST /hr/payslips/:id/email` — email a payslip to the employee

#### 4.6.3 Salary Holds

Put a hold on an employee's salary (e.g., during investigation, pending clearance):

- `POST /hr/salary-holds` — create hold (full or partial, specifying held components)
- `PATCH /hr/salary-holds/:id/release` — release the hold

#### 4.6.4 Salary Revisions

Process salary increments:

1. `POST /hr/salary-revisions` — create revision with new CTC, effective date, increment %
2. `PATCH /hr/salary-revisions/:id/approve` — approve the revision
3. `PATCH /hr/salary-revisions/:id/apply` — apply to the employee record

If the effective date is in the past, the system automatically computes arrears viewable via `GET /hr/arrear-entries`.

#### 4.6.5 Statutory Filings

Track and manage statutory filing obligations:

| Filing Type | Description |
|-------------|-------------|
| `PF_ECR` | PF Electronic Challan-cum-Return |
| `ESI_CHALLAN` | ESI contribution challan |
| `PT_CHALLAN` | Professional Tax challan |
| `TDS_24Q` | Quarterly TDS return |
| `FORM_16` | Annual tax certificate |
| `BONUS_STATEMENT` | Statutory bonus statement |
| `GRATUITY_REGISTER` | Gratuity register |
| `LWF_STATEMENT` | Labour Welfare Fund statement |

Status lifecycle: `PENDING` -> `GENERATED` -> `FILED` -> `VERIFIED`

#### 4.6.6 Payroll Reports

| Report | Endpoint | Purpose |
|--------|----------|---------|
| Salary Register | `GET /hr/payroll-reports/salary-register` | Complete salary breakdown for a period |
| Bank File | `GET /hr/payroll-reports/bank-file` | Payment file for bank upload |
| PF ECR | `GET /hr/payroll-reports/pf-ecr` | PF return data |
| ESI Challan | `GET /hr/payroll-reports/esi-challan` | ESI contribution data |
| PT Challan | `GET /hr/payroll-reports/pt-challan` | PT payment data |
| Variance | `GET /hr/payroll-reports/variance` | Month-over-month salary variance |

### 4.7 ESS & Workflows

**Prerequisites:** ESS must be enabled in Company Settings. Employees must be linked to Users.

**Navigation:** ESS & Workflows section in the sidebar

#### 4.7.1 ESS Configuration (Singleton)

`GET/PATCH /hr/ess-config` — toggle individual self-service features:

| Feature Group | Toggles |
|--------------|---------|
| **Payroll** | viewPayslips, downloadForm16, itDeclaration, reimbursementClaims, loanApplication |
| **Leave** | leaveApplication, leaveBalanceView |
| **Attendance** | attendanceView, attendanceRegularization |
| **Profile** | profileUpdate, documentUpload |
| **Performance** | performanceGoals, appraisalAccess, feedback360 |
| **Other** | trainingEnrollment, helpDesk, employeeDirectory, holidayCalendar, policyDocuments, assetView, grievanceSubmission |
| **Security** | loginMethod (PASSWORD/SSO/OTP), passwordMinLength, passwordComplexity, sessionTimeoutMinutes, mfaRequired |

#### 4.7.2 Approval Workflows

Define multi-step approval chains for leave, expense claims, salary revisions, etc.:

```json
{
  "name": "Leave Approval - 2 Level",
  "triggerEvent": "LEAVE_REQUEST",
  "steps": [
    { "stepOrder": 1, "approverRole": "reporting_manager", "slaHours": 24, "autoEscalate": true },
    { "stepOrder": 2, "approverRole": "hr_manager", "slaHours": 48, "autoApprove": false }
  ]
}
```

| Step Field | Purpose |
|-----------|---------|
| `stepOrder` | Sequence of approval |
| `approverRole` | Who approves at this step |
| `approverId` | Specific user (overrides role) |
| `slaHours` | Time limit for this step |
| `autoEscalate` | Auto-escalate if SLA breached |
| `autoApprove` | Auto-approve if no action within SLA |
| `autoReject` | Auto-reject if no action within SLA |

#### 4.7.3 Notification Templates & Rules

**Templates:** Define reusable notification content with placeholders:
- Channels: `EMAIL`, `SMS`, `PUSH`, `IN_APP`, `WHATSAPP`
- Body supports placeholders like `{{employeeName}}`, `{{leaveType}}`, `{{fromDate}}`

**Rules:** Map trigger events to templates:
- `triggerEvent` — what triggers the notification (e.g., "LEAVE_APPROVED")
- `templateId` — which template to use
- `recipientRole` — who receives it
- `channel` — delivery channel

#### 4.7.4 IT Declarations

Employees submit income tax declarations for tax planning:

- Tax regime selection: `OLD` or `NEW`
- Sections: 80C, 80CCD (NPS), 80D (health insurance), 80E (education loan), 80G (donations), 80GG (rent), 80TTA (savings interest)
- HRA exemption, LTA exemption, home loan interest, other income
- Lifecycle: Create -> Submit -> Verify (by HR) -> Lock

#### 4.7.5 Self-Service Endpoints (Employee-Facing)

| Endpoint | Purpose |
|----------|---------|
| `GET /hr/ess/my-profile` | View own employee profile |
| `GET /hr/ess/my-payslips` | View own payslips |
| `GET /hr/ess/my-leave-balance` | View own leave balances |
| `GET /hr/ess/my-attendance` | View own attendance records |
| `GET /hr/ess/my-declarations` | View own IT declarations |
| `POST /hr/ess/apply-leave` | Apply for leave |
| `POST /hr/ess/regularize-attendance` | Request attendance correction |

#### 4.7.6 Manager Self-Service (MSS)

| Endpoint | Purpose |
|----------|---------|
| `GET /hr/mss/team-members` | View direct reports |
| `GET /hr/mss/pending-approvals` | Pending approvals queue |
| `GET /hr/mss/team-attendance` | Team attendance overview |
| `GET /hr/mss/team-leave-calendar` | Team leave calendar |

#### 4.7.7 Manager Delegation

When a manager is on leave or unavailable, delegate approval authority:

```json
{
  "managerId": "manager-emp-id",
  "delegateId": "delegate-emp-id",
  "fromDate": "2026-04-01",
  "toDate": "2026-04-15",
  "reason": "Annual leave"
}
```

Revoke via `PATCH /hr/delegates/:id/revoke`.

### 4.8 Performance Management

**Prerequisites:** Employees and Departments must exist.

**Navigation:** Performance section in the sidebar

#### Setup Order

1. **Skills Library** — Define skills with categories (Technical, Soft Skills, Leadership, etc.)
2. **Appraisal Cycles** — Create a cycle with date range and rating parameters
3. **Goals & OKRs** — Set goals per employee or department
4. **Appraisal Entries** — Create per-employee per-cycle entries
5. **360 Feedback** — Request feedback from peers, managers, subordinates
6. **Ratings & Calibration** — 9-box grid, bell curve distribution
7. **Skill Mappings** — Map skills to employees with proficiency levels
8. **Succession Planning** — Identify successors for critical roles
9. **Performance Dashboard** — Aggregated metrics and analytics

#### 4.8.1 Appraisal Cycles

| Field | Notes |
|-------|-------|
| `name` | e.g., "FY 2025-26 Annual Review" |
| `frequency` | `ANNUAL`, `SEMI_ANNUAL`, `QUARTERLY` |
| `startDate`, `endDate` | Cycle period |
| `ratingScale` | 3 to 10 (default: 5) |
| `ratingLabels` | Custom labels (e.g., ["Needs Improvement", "Meets Expectations", "Exceeds", "Outstanding"]) |
| `kraWeightage` | KRA weight in final score (default: 70%) |
| `competencyWeightage` | Competency weight (default: 30%) |
| `forcedDistribution` | Enforce bell curve distribution |

**Cycle Lifecycle:**

```
DRAFT ──→ ACTIVE ──→ REVIEW_CLOSED ──→ CALIBRATION ──→ PUBLISHED ──→ CLOSED
```

Transitions via: `activate`, `close-review`, `start-calibration`, `publish-ratings`, `close`

#### 4.8.2 Goals (KRA/OKR)

Goals support cascading — company goals cascade to department goals cascade to individual goals:

- `level`: `COMPANY`, `DEPARTMENT`, `INDIVIDUAL`
- `parentGoalId` — links to parent goal for cascading
- `weightage` — how much this goal contributes to overall score (0-100)
- `kpiMetric`, `targetValue` — measurable targets

#### 4.8.3 Appraisal Entries

The review process for each employee in a cycle:

1. **Self-Review** — employee rates themselves with comments, KRA/competency scores, goal-level ratings
2. **Manager Review** — manager rates with comments, promotion recommendation, increment suggestion
3. **Publish** — HR publishes the final rating

#### 4.8.4 360 Feedback

Collect multi-rater feedback:

| Rater Type | Description |
|-----------|-------------|
| `SELF` | Self-assessment |
| `MANAGER` | Direct manager |
| `PEER` | Colleagues at same level |
| `SUBORDINATE` | Direct reports |
| `CROSS_FUNCTION` | Cross-functional stakeholders |
| `INTERNAL_CUSTOMER` | Internal customers |

Feedback includes competency ratings (1-10), strengths, improvements, and "would work again" flag. Anonymous by default.

#### 4.8.5 Succession Planning

- **9-box grid:** Maps performance (X-axis) vs. potential (Y-axis) using `performanceRating` and `potentialRating`
- **Readiness levels:** `READY_NOW`, `ONE_YEAR`, `TWO_YEARS`, `NOT_READY`
- **Bench strength:** `GET /hr/succession-plans/bench-strength` — shows coverage for critical roles

#### 4.8.6 Skill Mappings & Gap Analysis

- Map skills to employees: `POST /hr/skill-mappings` with `currentLevel` (1-5) and `requiredLevel` (1-5)
- Gap analysis: `GET /hr/skill-mappings/gap-analysis/:employeeId` — shows skills where current < required

### 4.9 Recruitment & Training

**Prerequisites:** Departments and Designations must exist.

**Navigation:** Recruitment & Training section in the sidebar

#### 4.9.1 Job Requisitions

Create hiring requests:

| Field | Notes |
|-------|-------|
| `title` | Job title |
| `departmentId` | Which department |
| `designationId` | Which designation |
| `openings` | Number of positions |
| `budgetMin`, `budgetMax` | CTC budget range |
| `targetDate` | Hiring deadline |
| `sourceChannels` | Recruitment channels |

Status lifecycle: `DRAFT` -> `OPEN` -> `INTERVIEWING` -> `OFFERED` -> `FILLED` (or `CANCELLED`)

#### 4.9.2 Candidates

Track applicants through the hiring funnel:

Stages: `APPLIED` -> `SHORTLISTED` -> `HR_ROUND` -> `TECHNICAL` -> `FINAL` -> `ASSESSMENT` -> `OFFER_SENT` -> `HIRED` (or `REJECTED` / `ON_HOLD`)

#### 4.9.3 Interviews

Schedule and track interviews:

- Assign panelists (employee IDs)
- Set meeting link, duration
- Complete with feedback rating (0-10) and notes

#### 4.9.4 Training Catalogue

Define training programs:

| Field | Notes |
|-------|-------|
| `name` | Training name |
| `mode` | `ONLINE`, `CLASSROOM`, `WORKSHOP`, `EXTERNAL`, `BLENDED`, `ON_THE_JOB` |
| `linkedSkillIds` | Skills this training develops |
| `proficiencyGain` | Expected skill level increase (0-5) |
| `mandatory` | Is this training mandatory? |
| `certificationName`, `certificationBody` | Certification details |
| `costPerHead` | Cost per participant |

#### 4.9.5 Training Nominations

Nominate employees for training:

Status: `NOMINATED` -> `ENROLLED` -> `COMPLETED` (or `CANCELLED`)

Complete with `completionDate`, `score` (0-100), and `certificateUrl`.

Dashboard: `GET /hr/training-dashboard` — training analytics.

### 4.10 Exit & Separation

**Prerequisites:** Employee must exist.

**Navigation:** Exit & Separation section in the sidebar

#### 4.10.1 Exit Requests

Initiate an employee exit:

| Separation Type | Description |
|----------------|-------------|
| `VOLUNTARY_RESIGNATION` | Employee-initiated departure |
| `RETIREMENT` | Age/service-based retirement |
| `TERMINATION_FOR_CAUSE` | Misconduct or performance termination |
| `LAYOFF_RETRENCHMENT` | Business downsizing |
| `DEATH` | Employee death |
| `ABSCONDING` | Employee left without notice |
| `CONTRACT_END` | Contract period expiry |

**Exit Request Status Lifecycle:**

```
INITIATED ──→ NOTICE_PERIOD ──→ CLEARANCE_PENDING ──→ CLEARANCE_DONE ──→ FNF_COMPUTED ──→ FNF_PAID ──→ COMPLETED
```

#### 4.10.2 Clearance Dashboard

Each exit request auto-generates department-wise clearance checklists:

- `GET /hr/exit-requests/:id/clearances` — list clearances
- `PATCH /hr/exit-clearances/:id` — update status: `PENDING`, `CLEARED`, `NOT_APPLICABLE`

#### 4.10.3 Exit Interviews

Record exit interview responses:

```json
{
  "responses": [
    { "question": "What was the primary reason for leaving?", "answer": "Career growth" },
    { "question": "How was your experience with management?", "answer": "Good overall" }
  ],
  "overallRating": 4,
  "wouldRecommend": true
}
```

#### 4.10.4 F&F Settlement

Full & Final settlement computation:

1. `POST /hr/exit-requests/:id/compute-fnf` — compute settlement (with optional `otherEarnings` and `otherDeductions`)
2. `PATCH /hr/fnf-settlements/:id/approve` — approve the computation
3. `PATCH /hr/fnf-settlements/:id/pay` — mark as paid

The F&F computation includes: pending salary, leave encashment, gratuity, bonus, deductions for notice period shortfall, loan recovery, asset recovery, etc.

### 4.11 Transfers & Promotions

**Prerequisites:** Employee must exist. Target Department/Designation/Location must exist.

**Navigation:** Transfers & Promotions section in the sidebar

#### 4.11.1 Transfers

Create transfer requests:

| Field | Required | Notes |
|-------|----------|-------|
| `employeeId` | Yes | |
| `toDepartmentId` | No | New department |
| `toDesignationId` | No | New designation |
| `toLocationId` | No | New location |
| `toManagerId` | No | New reporting manager |
| `effectiveDate` | Yes | When the transfer takes effect |
| `reason` | Yes | Justification |
| `transferType` | No | `LATERAL`, `RELOCATION`, `RESTRUCTURING` |

**Transfer Lifecycle:**

```
PENDING ──→ APPROVED ──→ APPLIED (executed)
  │
  └──→ REJECTED / CANCELLED
```

When a transfer is applied (`PATCH /hr/transfers/:id/apply`), the employee record is updated with the new department, designation, location, and/or manager.

#### 4.11.2 Promotions

Create promotion requests:

| Field | Required | Notes |
|-------|----------|-------|
| `employeeId` | Yes | |
| `toDesignationId` | Yes | New designation |
| `toGradeId` | No | New grade |
| `newCtc` | No | New annual CTC |
| `effectiveDate` | Yes | |
| `reason` | No | |
| `appraisalEntryId` | No | Link to performance appraisal |

Same lifecycle as transfers: PENDING -> APPROVED -> APPLIED (or REJECTED/CANCELLED).

When applied, the employee's designation, grade, and salary are updated. If `newCtc` is provided, a salary revision is automatically created.

#### 4.11.3 Manager Delegation

During a manager's absence, delegate their approval authority to another employee. See Section 4.7.7.

### 4.12 Advanced HR

**Prerequisites:** Employees must exist.

**Navigation:** Advanced HR section in the sidebar

#### 4.12.1 Asset Management

**Setup:** Create asset categories first, then individual assets, then assign to employees.

1. **Asset Categories:** Name, depreciation rate, return checklist
2. **Assets:** Name, category, serial number, purchase date/value, condition (`NEW`, `LIKE_NEW`, `GOOD`, `FAIR`, `DAMAGED`, `LOST`)
3. **Asset Assignments:** Assign to employee with issue date
4. **Asset Returns:** `PATCH /hr/asset-assignments/:id/return` with return date and condition

Asset status lifecycle: `IN_STOCK` -> `ASSIGNED` -> `UNDER_REPAIR` / `PENDING_RETURN` -> `RETIRED`

#### 4.12.2 Expense Claims

Employees submit expense claims for reimbursement:

1. `POST /hr/expense-claims` — create claim with title, amount, category, receipts
2. `PATCH /hr/expense-claims/:id/submit` — submit for approval
3. `PATCH /hr/expense-claims/:id/approve-reject` — approve or reject

#### 4.12.3 HR Letters

Generate standardized letters from templates:

1. **Create templates:** Define letter types (OFFER, APPOINTMENT, RELIEVING, CONFIRMATION, etc.) with HTML body and placeholders
2. **Generate letters:** `POST /hr/hr-letters` with templateId + employeeId — system fills placeholders with employee data

#### 4.12.4 Grievances

Handle employee grievances:

1. **Create categories:** Define grievance types (Harassment, Discrimination, Policy Violation, etc.) with SLA hours and auto-escalation
2. **File cases:** Employees submit grievances (can be anonymous)
3. **Process:** Status flow: `OPEN` -> `INVESTIGATING` -> `RESOLVED` / `CLOSED` / `ESCALATED`

#### 4.12.5 Disciplinary Actions

Record and track disciplinary proceedings:

| Type | Description |
|------|-------------|
| `VERBAL_WARNING` | Informal warning |
| `WRITTEN_WARNING` | Formal written warning |
| `SHOW_CAUSE` | Show cause notice with reply deadline |
| `PIP` | Performance Improvement Plan with duration |
| `SUSPENSION` | Temporary suspension |
| `TERMINATION` | Employment termination |

PIP outcomes: `SUCCESS`, `PARTIAL`, `FAILURE`

---

## 5. Configuration Reference

### 5.1 Number Series

Number Series define auto-numbering patterns for various entities. Each series has:

| Field | Purpose |
|-------|---------|
| `code` | Unique identifier for the series |
| `linkedScreen` | Which entity type uses this series |
| `prefix` | Text before the number (e.g., "EMP-", "INV-") |
| `suffix` | Text after the number (optional) |
| `numberCount` | Number of digits (e.g., 4 = "0001") |
| `startNumber` | Where numbering begins |

**Common linkedScreen Values:**

| Linked Screen | Used For | Example Output |
|--------------|----------|---------------|
| `Employee` | Employee ID generation | EMP-0001 |
| `Invoice` | Invoice numbering | INV-2026-0001 |
| `PurchaseOrder` | Purchase order numbers | PO-0001 |
| `SalesOrder` | Sales order numbers | SO-0001 |
| `GRN` | Goods Receipt Note | GRN-0001 |
| `ProductionOrder` | Production orders | PRD-0001 |
| `MaintenanceOrder` | Maintenance work orders | MO-0001 |
| `VisitorPass` | Visitor passes | VP-0001 |

> :warning: **CRITICAL:** The "Employee" Number Series must be created before attempting to create employees. Without it, auto-ID generation fails.

### 5.2 System Controls

`GET/PATCH /company/controls` — toggle-based system settings:

| Control | Default | Purpose |
|---------|---------|---------|
| `mfa` | `false` | **Multi-Factor Authentication** — require 2FA for all users |
| `ncEditMode` | `false` | **NC Edit Mode** — allow editing of non-conformance reports in production |
| `loadUnload` | `false` | **Load/Unload Tracking** — track material loading/unloading in production |
| `cycleTime` | `false` | **Cycle Time Tracking** — track production cycle times per operation |
| `payrollLock` | `false` | **Payroll Lock** — prevent payroll modifications after approval |
| `leaveCarryForward` | `false` | **Leave Carry Forward** — allow unused leave to carry over to next year |
| `overtimeApproval` | `false` | **Overtime Approval** — require manager approval for overtime claims |

### 5.3 Feature Toggles

Feature toggles allow per-user feature overrides. Use this to beta-test features or restrict access.

- `GET /feature-toggles/?userId=xxx` — get toggles for a user
- `PUT /feature-toggles/user/:userId` — set toggles as a key-value map

```json
{
  "toggles": {
    "newDashboard": true,
    "aiChatbot": false,
    "bulkUpload": true
  }
}
```

---

## 6. Operations Modules (Coming Soon)

### 6.1 Inventory

**Planned features:**

- Item Master (categories, units, SKUs)
- Warehouse Management (locations, zones, bins)
- Stock Transactions (receipts, issues, transfers)
- Purchase Orders & Goods Receipt Notes
- Stock Valuation (FIFO, LIFO, weighted average)
- Reorder Points & Auto-replenishment
- Barcode/QR Integration

**API routes reserved:** `/api/v1/inventory`

### 6.2 Production

**Planned features:**

- Bill of Materials (BOM)
- Production Orders & Work Orders
- Routing & Operations
- Production Scheduling (MRP)
- Quality Checkpoints
- Non-Conformance Reports
- IoT Machine Integration (real-time OEE)
- Downtime Tracking (using IOT Reasons)
- Cycle Time Analysis

**API routes reserved:** `/api/v1/production`, `/api/v1/machines`

### 6.3 Maintenance

**Planned features:**

- Machine Registry
- Preventive Maintenance Scheduling
- Corrective Maintenance Work Orders
- Spare Parts Management
- Maintenance Calendar
- MTBF/MTTR Analytics

**API routes reserved:** `/api/v1/maintenance`

---

## 7. Troubleshooting

### 7.1 Common Issues

#### "Employee ID could not be resolved"

**Cause:** The logged-in User is not linked to an Employee record.

**Fix:** Either:
1. Create an Employee with an email matching the User's email (auto-link triggers), or
2. Manually link via the admin panel.

#### "Insufficient permissions"

**Cause:** The user's role doesn't include the required permission for the endpoint.

**Fix:**
1. Check the user's assigned role via `GET /rbac/roles`
2. Verify the role includes the needed permission (e.g., `audit:read` for audit logs)
3. Update the role or assign a different one

#### "No employee record linked"

**Cause:** The User account exists but has no linked Employee record. ESS endpoints require this link.

**Fix:** Create an Employee with `personalEmail` or `officialEmail` matching the User's email.

#### Status filter returns 500

**Cause:** Status values in query parameters must be UPPERCASE.

**Fix:** Use `?status=PENDING` not `?status=pending`. Valid values depend on the entity:
- Employee: `ACTIVE`, `PROBATION`, `CONFIRMED`, `ON_NOTICE`, `SUSPENDED`, `EXITED`
- Leave Request: `PENDING`, `APPROVED`, `REJECTED`, `CANCELLED`
- Attendance: `PRESENT`, `ABSENT`, `HALF_DAY`, `LATE`, `ON_LEAVE`, `HOLIDAY`, `WEEK_OFF`, `LOP`

#### Location creation returns 403

**Cause:** Only Super Admin can create locations. This is by design.

**Fix:** Ask your Super Admin to create new locations via the onboarding wizard or `PATCH /platform/companies/:id/sections/locations`.

#### Employee creation fails silently

**Cause:** Missing required fields or dependencies.

**Check:**
1. Is there a Number Series with `linkedScreen: "Employee"`?
2. Do the referenced `departmentId`, `designationId`, `employeeTypeId` exist and are active?
3. Are all required personal fields filled? (`firstName`, `lastName`, `dateOfBirth`, `gender`, `personalMobile`, `personalEmail`, `emergencyContactName`, `emergencyContactRelation`, `emergencyContactMobile`, `joiningDate`)

#### Payroll run stuck at "Compute" step

**Cause:** One or more employees may have incomplete salary configurations.

**Check:**
1. All employees in the run have an assigned salary (`/hr/employee-salaries`)
2. The salary structure has valid components
3. Statutory configs (PF, ESI) are properly configured

### 7.2 Data Dependencies Quick Reference

| To Create | You First Need |
|-----------|---------------|
| Designation | Department + Grade |
| Cost Centre | Department (+ optionally Location) |
| Employee | Department + Designation + Employee Type + Number Series ("Employee") + joining date |
| Attendance Record | Employee + Shift |
| Leave Request | Employee + Leave Type + Leave Balance (initialized) |
| Leave Policy | Leave Type |
| Leave Balance (initialize) | Employee + Leave Type |
| Salary Structure | Salary Components (min 1) |
| Employee Salary | Employee + Salary Structure |
| Payroll Run | Employees with assigned salaries |
| Payslip | Completed Payroll Run |
| Salary Revision | Employee + current salary |
| Salary Hold | Employee + Payroll Run |
| Statutory Filing | Payroll Run (for the period) |
| Loan Record | Employee + Loan Policy |
| Appraisal Entry | Appraisal Cycle + Employee |
| Goal (Individual) | Appraisal Cycle + Employee |
| 360 Feedback | Appraisal Cycle + Employee (subject) + Employee (rater) |
| Skill Mapping | Skill + Employee |
| Succession Plan | Employee (successor) + Designation (critical role) |
| Candidate | Job Requisition |
| Interview | Candidate |
| Training Nomination | Training Catalogue entry + Employee |
| Exit Request | Employee |
| Clearance | Exit Request (auto-generated) |
| F&F Settlement | Exit Request (with clearances completed) |
| Transfer | Employee + target Department/Designation/Location |
| Promotion | Employee + target Designation (+ optionally Grade) |
| Asset Assignment | Asset + Employee |
| Asset | Asset Category |
| Expense Claim | Employee |
| HR Letter | Letter Template + Employee |
| Grievance Case | Grievance Category (+ optionally Employee) |
| Disciplinary Action | Employee |
| Notification Rule | Notification Template |
| Manager Delegation | Manager Employee + Delegate Employee |
| IT Declaration | Employee |
| Approval Workflow | None (standalone config) |

---

## 8. API Quick Reference

The AVY ERP API is fully documented in two companion documents:

- **Part 1:** `api-endpoints-part1.md` — Authentication, Super Admin, Company Admin, RBAC, Feature Toggles
- **Part 2:** `api-endpoints-part2.md` — Complete HR Module (11 sub-modules)

**Base URL:** `/api/v1` (configurable via `API_PREFIX` environment variable)

**Authentication:** Bearer token in `Authorization` header for all endpoints except `/auth/*`.

### 8.1 Authentication Endpoints

**9 endpoints** at `/api/v1/auth/`:

| Endpoint | Auth | Purpose |
|----------|------|---------|
| `POST /auth/login` | No | Login |
| `POST /auth/register` | No | Register |
| `POST /auth/refresh-token` | No | Refresh access token |
| `POST /auth/forgot-password` | No | Initiate password reset |
| `POST /auth/verify-reset-code` | No | Verify reset code |
| `POST /auth/reset-password` | No | Set new password |
| `POST /auth/change-password` | Yes | Change password |
| `POST /auth/logout` | Yes | Logout |
| `GET /auth/profile` | Yes | Get current user profile |

### 8.2 Super Admin Endpoints

**Approximately 35 endpoints** across:

| Group | Count | Base Path |
|-------|-------|-----------|
| Tenant Management | 12 | `/platform/tenants` |
| Company Management | 5 | `/platform/companies` |
| Dashboard | 3 | `/platform/dashboard` |
| Audit Logs | 4 | `/platform/audit-logs` |
| Billing Summary | 2 | `/platform/billing` |
| Billing Config | 2 | `/platform/billing/config` |
| Invoices | 7 | `/platform/billing/invoices` |
| Payments | 3 | `/platform/billing/payments` |
| Subscriptions | 7 | `/platform/billing/subscriptions` |

### 8.3 Company Admin Endpoints

**Approximately 30 endpoints** across:

| Group | Count | Base Path |
|-------|-------|-----------|
| Profile | 2 | `/company/profile` |
| Locations | 5 | `/company/locations` |
| Shifts | 5 | `/company/shifts` |
| Contacts | 5 | `/company/contacts` |
| Number Series | 5 | `/company/no-series` |
| IOT Reasons | 5 | `/company/iot-reasons` |
| Controls | 2 | `/company/controls` |
| Settings | 2 | `/company/settings` |
| Users | 5 | `/company/users` |
| Audit Logs | 2 | `/company/audit-logs` |
| Dashboard | 2 | `/dashboard` |
| RBAC | 8 | `/rbac` |
| Feature Toggles | 2 | `/feature-toggles` |

### 8.4 HR Module Endpoints

**281 endpoints** across 11 sub-modules:

| Sub-Module | Endpoints | Key Resources |
|-----------|-----------|---------------|
| **Org Structure** | 25 | Departments, Designations, Grades, Employee Types, Cost Centres |
| **Employee Management** | 21 | Employees + Nominees, Education, Previous Employment, Documents, Timeline |
| **Attendance** | 18 | Records, Rules, Overrides, Holidays, Rosters, Overtime Rules |
| **Leave Management** | 16 | Leave Types, Policies, Balances, Requests, Summary |
| **Payroll Configuration** | 33 | Salary Components, Structures, Employee Salaries, PF/ESI/PT/Gratuity/Bonus/LWF/Bank/Tax Configs, Loan Policies, Loans |
| **Payroll Run Engine** | 26 | Runs (6-step wizard), Entries, Payslips, Holds, Revisions, Arrears, Filings, Reports |
| **ESS/MSS & Workflows** | 33 | ESS Config, Approval Workflows, Approval Requests, Notification Templates/Rules, Delegates, IT Declarations, ESS Self-Service, MSS |
| **Performance** | 36 | Appraisal Cycles (lifecycle), Entries, Goals, 360 Feedback, Skills, Skill Mappings, Succession Plans, Dashboard |
| **Offboarding & F&F** | 11 | Exit Requests, Clearances, Exit Interviews, F&F Settlements |
| **Advanced HR** | 48 | Recruitment (Requisitions, Candidates, Interviews), Training (Catalogue, Nominations), Assets (Categories, Assets, Assignments), Expenses, HR Letters, Grievances, Disciplinary Actions |
| **Transfers & Promotions** | 14 | Transfers, Promotions |

**Common Query Parameters (all list endpoints):**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `page` | number | 1 | Page number |
| `limit` | number | 20 | Items per page |
| `search` | string | — | Search query |
| `sortBy` | string | — | Field to sort by |
| `sortOrder` | string | — | `asc` or `desc` |

**Permission model:** All HR endpoints use `hr:read`, `hr:create`, `hr:update`, or `hr:delete` permissions.

---

*This guide covers the complete AVY ERP system as of March 2026. For detailed API schemas and request/response formats, refer to the companion API documentation files.*
