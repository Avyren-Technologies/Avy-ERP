# Avy ERP — Super Admin Panel: Complete Reference Document

> **Document Code:** AVY-SA-001
> **Module:** Platform Administration — Super Admin Panel
> **Audience:** Super Admins, Platform Engineers, Backend Developers
> **Version:** 1.0
> **Date:** March 2026
> **Product:** Avy ERP (Avyren Technologies)
> **Classification:** Internal — Avyren Technologies

---

## Table of Contents

1. [Document Overview & Purpose](#1-document-overview--purpose)
2. [Super Admin — Role Definition & Scope](#2-super-admin--role-definition--scope)
3. [Super Admin Sidebar Navigation](#3-super-admin-sidebar-navigation)
4. [Platform Overview Dashboard](#4-platform-overview-dashboard)
5. [Company / Tenant Management (Deep Dive)](#5-company--tenant-management-deep-dive)
6. [Module Management](#6-module-management)
7. [User & Role Management](#7-user--role-management)
8. [Billing & Subscription Management](#8-billing--subscription-management)
9. [Backend Architecture & API Design](#9-backend-architecture--api-design-super-admin-perspective)
10. [Audit Trail & Compliance](#10-audit-trail--compliance)
11. [Notifications & Communication](#11-notifications--communication)
12. [Platform Settings & Configuration](#12-platform-settings--configuration)
13. [Mobile App Implementation — Super Admin Screens](#13-mobile-app-implementation--super-admin-screens)
14. [Data Flow & Screen Linkages](#14-data-flow--screen-linkages)
15. [Security & Access Control for Super Admin Panel](#15-security--access-control-for-super-admin-panel)
16. [Implementation Roadmap & Priorities](#16-implementation-roadmap--priorities)

---


## 1. Document Overview & Purpose

| Field | Value |
|---|---|
| **Document Code** | AVY-SA-001 |
| **Version** | 1.0 |
| **Effective Date** | 2026-03-18 |
| **Classification** | Internal — Avyren Technologies |
| **Audience** | Super Admins, Platform Engineers, Backend Developers |
| **Owner** | Avyren Technologies — Product & Platform Team |

This document is the single authoritative reference for the Super Admin panel of Avy ERP. It defines every capability, screen, workflow, data model, and integration point that the Super Admin interface must support across all client surfaces (mobile, web, and desktop).

### Product Context

Avy ERP is a multi-tenant SaaS Enterprise Resource Planning platform built by Avyren Technologies, purpose-designed for small and medium-sized manufacturing enterprises. The platform delivers modular ERP capabilities — spanning production planning, inventory, procurement, quality, HR/payroll, finance, and IoT-driven shop-floor analytics — through three client applications:

- **Mobile** — React Native / Expo (iOS & Android)
- **Web** — React / Vite (browser)
- **Desktop** — Electron (Windows, macOS, Linux)

All three clients share a common backend built on Node.js, Express, and PostgreSQL, following a modular monolith architecture with strict tenant isolation at the database schema level. Each customer organization (tenant) operates within its own logical partition. Modules are individually licensable, dependency-resolved, and priced per tenant.

The Super Admin panel is the platform-level control plane. It is not a tenant application — it sits above all tenants and provides Avyren Technologies staff with the tools to onboard customers, manage subscriptions, monitor platform health, and ensure operational continuity across the entire tenant fleet.

### How to Use This Document

| If you are... | Start with... |
|---|---|
| A Super Admin learning the panel | Sections 2–4 (role, navigation, dashboard) |
| A backend developer building APIs | Sections 5–10 (tenant management, billing, modules, users) |
| A platform engineer on infra/DevOps | Sections 11–13 (system health, endpoints, settings) |
| A frontend developer building screens | Every section — each includes UI specifications |

---

## 2. Super Admin — Role Definition & Scope

### 2.1 What Is a Super Admin?

The Super Admin is the highest-privilege user role on the Avy ERP platform. This role is exclusively reserved for authorized personnel of Avyren Technologies. Super Admins are not tenant users — they operate at the platform level with cross-tenant visibility and control.

A Super Admin can create, configure, suspend, and delete any tenant on the platform. They cannot, by default, access a tenant's business data (HR records, production figures, sales orders, financial transactions). Access to tenant business data requires explicit, audited, time-boxed grants issued for support or compliance purposes.

### 2.2 Role Hierarchy

```
Super Admin (Platform Level — Avyren Technologies)
│
│   Full platform control. Cross-tenant access.
│   Cannot see tenant business data unless explicitly granted.
│
└── Company-Admin (Tenant Level — Customer Organization)
    │
    │   Full control within their own tenant.
    │   Manages users, roles, modules, and company settings.
    │   Cannot see other tenants or platform-level data.
    │
    └── Custom Roles (Defined by Company-Admin)
        │
        │   Scoped by module access, data visibility, and action permissions.
        │   Examples: Plant Manager, Inventory Clerk, HR Officer, QC Inspector.
        │
        └── Users
            │
            Assigned one or more custom roles.
            Access determined entirely by role composition.
```

### 2.3 Two Primary System Roles

The platform recognizes exactly two built-in system roles. All other roles are custom and tenant-scoped.

| System Role | Scope | Created By | Count |
|---|---|---|---|
| **Super-Admin** | Platform-wide, cross-tenant | Avyren Technologies (manual provisioning) | Limited (typically 3–10 accounts) |
| **Company-Admin** | Single tenant | Super Admin during tenant onboarding (Step 15) | One or more per tenant |

### 2.4 Super Admin Capabilities

| Capability Area | Actions |
|---|---|
| **Tenant Lifecycle** | Create new tenant (16-step wizard), edit tenant configuration, suspend tenant, reactivate tenant, permanently delete tenant (with safeguards) |
| **Module Management** | View module catalogue, assign/revoke modules per tenant, configure module pricing, manage module dependencies, toggle platform-wide feature flags |
| **Billing & Subscription** | View subscription status for all tenants, generate and send invoices, record payments, manage billing cycles, configure trial periods, track MRR/ARR/churn |
| **User Management** | Create/edit/deactivate Super Admin accounts, view cross-tenant user counts and active sessions, manage role templates |
| **Platform Configuration** | Set default values for new tenants, manage notification templates (email/SMS/WhatsApp), configure integration settings (payment gateway, email/SMS providers), manage backend endpoints |
| **Monitoring & Analytics** | View platform-wide usage analytics, access cross-tenant audit logs, monitor API performance and system health, track error rates and sync queues |
| **Support Operations** | Manage support tickets, maintain knowledge base, broadcast system announcements to all tenants |

### 2.5 Data Access Boundary

This boundary is a core security principle and must be enforced at the API layer, not merely the UI layer.

| Data Category | Super Admin Access | Notes |
|---|---|---|
| Tenant configuration (name, modules, tier, endpoint) | Full read/write | Core responsibility |
| Billing data (invoices, payments, subscription status) | Full read/write | Core responsibility |
| User accounts (names, emails, roles, session status) | Read-only | For support and auditing |
| Tenant business data (HR, production, inventory, finance) | Blocked by default | Requires explicit support-access grant |
| Audit logs (platform-level and cross-tenant) | Full read | Cannot delete or modify |
| System health metrics (API, DB, sync) | Full read | Cannot modify infrastructure directly |

**Support Access Grant**: When a tenant requests support that requires data access, a Super Admin may request a time-boxed support access grant. This grant must specify the tenant, the data scope, the duration (maximum 24 hours, renewable), and the reason. All actions taken under a support grant are logged separately in the audit trail with a `support-access` tag.

### 2.6 Authentication

| Aspect | Specification |
|---|---|
| **Method** | Username (email) + Password |
| **Password Input** | Masked by default with show/hide toggle (eye icon) — implemented via `SecretInput` atom |
| **Session Duration** | Configurable; default 8 hours |
| **Session Timer** | Live countdown displayed in sidebar footer or header; warns at 15 minutes remaining |
| **Idle Timeout** | Configurable; default 30 minutes of inactivity triggers lock screen |
| **MFA** | Not implemented in v1; architecture must support future TOTP/SMS-based MFA |
| **Concurrent Sessions** | Allowed on multiple devices; all active sessions visible in account settings |
| **Session Termination** | Manual logout, idle timeout, or remote kill from another session |

### 2.7 Session Management

The Super Admin session includes a live timer visible at all times, reinforcing security awareness.

**Session States:**

| State | Behavior |
|---|---|
| **Active** | Timer counting down from session duration. Full access. |
| **Warning** | Less than 15 minutes remaining. Timer turns amber. Option to extend session. |
| **Idle Warning** | No interaction for (idle timeout - 5 min). Modal prompt: "Still there?" with extend/logout options. |
| **Locked** | Idle timeout reached. Screen locked. Re-enter password to resume (no full re-login). |
| **Expired** | Session duration reached or manually terminated. Full re-login required. |

---

## 3. Super Admin Sidebar Navigation

The sidebar is the primary navigation structure for the Super Admin panel. It is a collapsible overlay triggered by a hamburger button in the screen header. On mobile, it slides in from the left with an animated transition and a semi-transparent backdrop.

### 3.1 Sidebar Behavior

| Property | Specification |
|---|---|
| **Trigger** | `HamburgerButton` in screen header (top-left) |
| **Animation** | Slide-in from left, 300ms duration, `SlideInRight` from reanimated |
| **Backdrop** | Semi-transparent black overlay; tap to dismiss |
| **State Management** | `SidebarProvider` + `useSidebar()` hook (`isOpen`, `open`, `close`, `toggle`) |
| **Rendering** | Absolute overlay above tab content |
| **Collapse** | Tap backdrop, tap hamburger again, or swipe left |

### 3.2 Sidebar Header

Displays the Avyren Technologies logo, the logged-in Super Admin's name, and a role badge ("Super Admin"). Below the header, the live session timer is displayed in a compact format (e.g., "Session: 6h 42m remaining").

### 3.3 Navigation Sections

The sidebar is organized into 8 logical sections. Each section has a header label and one or more navigation items. Items may have badge counts (e.g., unread tickets) or status indicators.

---

#### Section 1: Dashboard

| Item | Icon | Route | Description |
|---|---|---|---|
| Platform Overview | `LayoutDashboard` | `/(app)/index` | Main dashboard with KPIs, activity feed, health overview, and alerts |

---

#### Section 2: Company / Tenant Management

| Item | Icon | Route | Description |
|---|---|---|---|
| All Companies | `Building2` | `/(app)/companies` | Searchable, filterable list of all tenants |
| Add New Company | `PlusCircle` | `/(app)/tenant/add-company` | Launches the 16-step onboarding wizard |
| Company Templates | `Copy` | `/(app)/tenant/templates` | Duplicate an existing tenant's configuration as a template for rapid onboarding |

---

#### Section 3: Billing & Subscription

| Item | Icon | Route | Badge |
|---|---|---|---|
| Subscription Overview | `CreditCard` | `/(app)/billing` | — |
| Invoice Management | `FileText` | `/(app)/billing/invoices` | Count of unpaid invoices |
| Revenue Dashboard | `TrendingUp` | `/(app)/billing/revenue` | — |
| Payment History | `Receipt` | `/(app)/billing/payments` | — |

---

#### Section 4: Module Management

| Item | Icon | Route | Description |
|---|---|---|---|
| Module Catalogue | `Package` | `/(app)/modules/catalogue` | View and edit the 10 available modules with pricing and dependency info |
| Tenant Module Assignment | `PackagePlus` | `/(app)/modules/assignment` | Assign or revoke modules for a specific tenant |
| Module Dependency Map | `GitBranch` | `/(app)/modules/dependencies` | Visual graph of module dependencies and resolution logic |
| Feature Toggles | `ToggleRight` | `/(app)/modules/features` | Platform-wide feature flags that enable/disable capabilities across all tenants |

---

#### Section 5: User & Role Management

| Item | Icon | Route | Badge |
|---|---|---|---|
| Platform Users | `ShieldCheck` | `/(app)/users/platform` | — |
| Tenant User Overview | `Users` | `/(app)/users/tenants` | Total active sessions count |
| Role Templates | `UserCog` | `/(app)/users/roles` | — |

---

#### Section 6: Reports & Analytics

| Item | Icon | Route | Description |
|---|---|---|---|
| Platform Analytics | `BarChart3` | `/(app)/reports/analytics` | Usage metrics, adoption rates, tenant health scores |
| Audit Logs | `ScrollText` | `/(app)/reports/audit` | Cross-tenant audit trail with advanced filtering |
| System Health | `Activity` | `/(app)/reports/health` | API response times, error rates, sync queue depth, DB performance |

---

#### Section 7: Settings & Configuration

| Item | Icon | Route | Description |
|---|---|---|---|
| Platform Settings | `Settings` | `/(app)/settings` | Default configurations applied to new tenants |
| Notification Templates | `Bell` | `/(app)/settings/notifications` | Email, SMS, and WhatsApp message templates |
| Integration Settings | `Plug` | `/(app)/settings/integrations` | Payment gateway (Razorpay), email provider, SMS gateway configuration |
| Backend Endpoints | `Server` | `/(app)/settings/endpoints` | Default cloud URL, custom endpoint registry, health monitoring |

---

#### Section 8: Support

| Item | Icon | Route | Badge |
|---|---|---|---|
| Support Tickets | `LifeBuoy` | `/(app)/support/tickets` | Count of open tickets |
| Knowledge Base | `BookOpen` | `/(app)/support/knowledge-base` | — |
| System Announcements | `Megaphone` | `/(app)/support/announcements` | — |

---

### 3.4 Sidebar Footer

| Element | Description |
|---|---|
| Session Timer | Live countdown: "Session: Xh Ym remaining" — turns amber below 15 minutes |
| Version Label | App version and environment (e.g., "v2.4.1 — Production") |
| Logout Button | Prominent logout action with confirmation via `ConfirmModal` (variant: `warning`) |

### 3.5 Complete Sidebar Structure (Summary)

```
┌─────────────────────────────────┐
│  [Avyren Logo]                  │
│  Admin Name                     │
│  🔵 Super Admin                 │
│  Session: 6h 42m remaining      │
├─────────────────────────────────┤
│  DASHBOARD                      │
│    Platform Overview             │
├─────────────────────────────────┤
│  COMPANY MANAGEMENT             │
│    All Companies                 │
│    Add New Company               │
│    Company Templates             │
├─────────────────────────────────┤
│  BILLING & SUBSCRIPTION         │
│    Subscription Overview         │
│    Invoice Management    [3]     │
│    Revenue Dashboard             │
│    Payment History               │
├─────────────────────────────────┤
│  MODULE MANAGEMENT              │
│    Module Catalogue              │
│    Tenant Module Assignment      │
│    Module Dependency Map         │
│    Feature Toggles               │
├─────────────────────────────────┤
│  USERS & ROLES                  │
│    Platform Users                │
│    Tenant User Overview  [24]    │
│    Role Templates                │
├─────────────────────────────────┤
│  REPORTS & ANALYTICS            │
│    Platform Analytics            │
│    Audit Logs                    │
│    System Health                 │
├─────────────────────────────────┤
│  SETTINGS                       │
│    Platform Settings             │
│    Notification Templates        │
│    Integration Settings          │
│    Backend Endpoints             │
├─────────────────────────────────┤
│  SUPPORT                        │
│    Support Tickets       [7]     │
│    Knowledge Base                │
│    System Announcements          │
├─────────────────────────────────┤
│  v2.4.1 — Production            │
│  [Logout]                        │
└─────────────────────────────────┘
```

---

## 4. Platform Overview Dashboard

The Platform Overview Dashboard is the Super Admin's landing screen. It provides an at-a-glance view of platform health, tenant status, financial metrics, and recent activity.

### 4.1 Screen Layout

```
┌──────────────────────────────────┐
│ [☰]  Platform Overview    [🔔]  │  ← LinearGradient header
├──────────────────────────────────┤
│                                  │
│  ┌──────┐ ┌──────┐ ┌──────┐    │  ← KPI cards row 1
│  │Total │ │Active│ │Trial │    │
│  │  47  │ │  38  │ │   6  │    │
│  └──────┘ └──────┘ └──────┘    │
│                                  │
│  ┌──────┐ ┌──────┐ ┌──────┐    │  ← KPI cards row 2
│  │Users │ │ MRR  │ │Sessns│    │
│  │ 2,841│ │₹18.4L│ │  312 │    │
│  └──────┘ └──────┘ └──────┘    │
│                                  │
│  ⚡ Alerts               [View All]│
│  ┌──────────────────────────────┐│
│  │ 🔴 3 subscriptions expiring  ││
│  │ 🟡 2 payment failures        ││
│  │ 🟠 5 tenants near user cap   ││
│  └──────────────────────────────┘│
│                                  │
│  📋 Recent Activity      [View All]│
│  ┌──────────────────────────────┐│
│  │ Tenant "Apex Mfg" activated  ││
│  │ Invoice #1247 paid — ₹42,000 ││
│  │ Module "QC" assigned to Vira ││
│  │ New tenant "SteelCo" created ││
│  └──────────────────────────────┘│
│                                  │
│  🏢 Tenant Health        [View All]│
│  ┌──────────────────────────────┐│
│  │ Company  Status Mod Usr Exp  ││
│  │ Apex Mfg Active  7  124 Dec ││
│  │ ViraTech Pilot   4   18 Mar ││
│  │ SteelCo  Draft   0    0  —  ││
│  └──────────────────────────────┘│
│                                  │
│  ⚡ Quick Actions                 │
│  [+ Add Company] [Generate Invoice]│
│  [View Audit Logs]                │
│                                  │
└──────────────────────────────────┘
```

### 4.2 KPI Cards

Six KPI cards arranged in a 3-column, 2-row grid.

| KPI | Icon | Value Format | Trend | Tap Action |
|---|---|---|---|---|
| **Total Tenants** | `Building2` | Integer (e.g., 47) | +/- vs last month | Navigate to All Companies |
| **Active Tenants** | `CheckCircle` | Integer (e.g., 38) | +/- vs last month | Navigate to All Companies (filtered: Active) |
| **Tenants in Trial** | `Clock` | Integer (e.g., 6) | — | Navigate to All Companies (filtered: Pilot) |
| **Total Platform Users** | `Users` | Formatted integer (e.g., 2,841) | +/- vs last month | Navigate to Tenant User Overview |
| **Monthly Recurring Revenue** | `IndianRupee` | Currency (e.g., ₹18.4L) | % change vs last month | Navigate to Revenue Dashboard |
| **Active Sessions** | `Radio` | Integer (e.g., 312) | — (live) | Navigate to Tenant User Overview |

### 4.3 Alerts Section

A priority-ordered list of items requiring Super Admin attention.

| Alert Type | Severity | Condition | Tap Action |
|---|---|---|---|
| **Expiring Subscriptions** | High (red) | Subscription expires within 7 days | Navigate to Subscription Overview (filtered) |
| **Payment Failures** | High (red) | Invoice overdue by more than 3 days | Navigate to Invoice Management (filtered) |
| **User Tier Ceiling** | Medium (amber) | Tenant at 90%+ of their user tier limit | Navigate to Company Detail for that tenant |
| **Inactive Tenants** | Low (blue) | No user login for 14+ days on an Active tenant | Navigate to Company Detail for that tenant |
| **Endpoint Health Failure** | High (red) | Custom endpoint health check failing | Navigate to Backend Endpoints |
| **Trial Expiring** | Medium (amber) | Trial period ends within 3 days | Navigate to Company Detail for that tenant |

### 4.4 Recent Activity Feed

A chronological feed of the latest platform-level events.

| Event Type | Example Text | Timestamp Format |
|---|---|---|
| Tenant Created | New tenant "SteelCo Industries" created | 2 min ago |
| Tenant Activated | Tenant "Apex Manufacturing" activated (was: Pilot) | 15 min ago |
| Tenant Suspended | Tenant "OldCorp" suspended — payment overdue | 1 hour ago |
| Module Assigned | Module "Quality Control" assigned to "Vira Tech" | 3 hours ago |
| Invoice Generated | Invoice #1248 generated for "Apex Manufacturing" — ₹42,000 | Yesterday |
| Payment Received | Payment ₹42,000 received from "Apex Manufacturing" (Invoice #1247) | Yesterday |
| User Tier Changed | "Vira Tech" upgraded from Growth to Scale tier | 2 days ago |
| Super Admin Login | admin@avyren.com logged in from 192.168.1.x | 3 hours ago |

### 4.5 Tenant Health Overview

A compact table showing the status of all tenants at a glance.

| Column | Description | Width |
|---|---|---|
| **Company** | Tenant display name (truncated to 18 chars on mobile) | 35% |
| **Status** | `StatusBadge` component — Draft / Pilot / Active / Inactive | 18% |
| **Modules** | Count of assigned modules (e.g., "7/10") | 12% |
| **Users** | Active user count vs tier limit (e.g., "124/150") | 15% |
| **Last Active** | Relative timestamp of most recent user login | 20% |

### 4.6 Quick Actions

| Action | Icon | Style | Navigation Target |
|---|---|---|---|
| **Add Company** | `PlusCircle` | Primary (filled, `colors.primary[600]`) | `/(app)/tenant/add-company` |
| **Generate Invoice** | `FileText` | Outline (`colors.primary[600]` border) | `/(app)/billing/invoices?action=generate` |
| **View Audit Logs** | `ScrollText` | Outline (`colors.primary[600]` border) | `/(app)/reports/audit` |

### 4.7 Dashboard Data Refresh

| Trigger | Behavior |
|---|---|
| **Screen Focus** | Refresh all sections via React Query `refetchOnWindowFocus` |
| **Pull-to-Refresh** | Full reload of all dashboard data |
| **Auto-Refresh** | KPI cards and Active Sessions refresh every 60 seconds |
| **Activity Feed** | Polling every 30 seconds for new events |
| **Stale Time** | 5 minutes for KPIs, 2 minutes for activity feed, 10 minutes for tenant health table |

### 4.8 Dashboard API Contracts

| Endpoint | Method | Response Summary |
|---|---|---|
| `/api/v1/super-admin/dashboard/kpis` | GET | `{ totalTenants, activeTenants, trialTenants, totalUsers, mrr, activeSessions, trends }` |
| `/api/v1/super-admin/dashboard/alerts` | GET | `{ alerts: [{ type, severity, message, count, tenantId?, link }] }` |
| `/api/v1/super-admin/dashboard/activity` | GET | `{ events: [{ type, message, timestamp, tenantId?, metadata }], cursor }` |
| `/api/v1/super-admin/dashboard/tenant-health` | GET | `{ tenants: [{ id, name, status, modulesCount, usersCount, usersLimit, lastActiveAt }], total, page }` |

All endpoints require the `Authorization: Bearer <session_token>` header and return `403 Forbidden` for non-Super-Admin roles.


---

## 5. Company / Tenant Management (Deep Dive)

### 5.1 Tenant Lifecycle

Every company onboarded onto Avy ERP follows a well-defined lifecycle. The Super Admin has full authority to transition tenants between states, with guardrails to prevent data loss.

#### Lifecycle States

| State | Trigger | Description |
|---|---|---|
| **Draft** | Super Admin begins onboarding wizard | Partially configured tenant. Not operational. Can be resumed or discarded. |
| **Pilot** | Super Admin marks tenant as pilot | Fully configured tenant in trial/evaluation mode. All modules functional. |
| **Trial** | Self-service signup (if enabled) | Auto-provisioned tenant with default module set. Converts to Active on payment or expires. |
| **Active** | Payment confirmed or manual activation | Fully operational. All assigned modules live. Users can log in. Billing active. |
| **Suspended** | Payment failure, policy violation, or manual | **Employees cannot log in.** Super Admin retains read-only access. Data preserved. |
| **Inactive** | Super Admin manually deactivates | Soft-disabled state. Can be reactivated without data loss. |
| **Cancelled** | Super Admin confirms cancellation | Final data export offered. Schema archived for **7 years**. Then purged. |

#### State Transition Diagram

```
                 ┌──────────┐
                 │  Draft    │
                 └────┬─────┘
                      │ (complete wizard)
                      ▼
              ┌───────────────┐
              │  Pilot / Trial │
              └───────┬───────┘
                      │ (payment confirmed / manual activation)
                      ▼
               ┌─────────────┐
        ┌─────►│   Active     │◄─────┐
        │      └──────┬──────┘      │
        │             │              │
        │  (reactivate)  (payment fail / manual)
        │             ▼              │
        │      ┌─────────────┐      │
        ├──────┤  Suspended   ├──────┘
        │      └──────┬──────┘
        │             │
        │  (reactivate)  (manual deactivate)
        │             ▼
        │      ┌─────────────┐
        └──────┤  Inactive    │
               └──────┬──────┘
                      │ (confirm cancellation)
                      ▼
               ┌─────────────┐
               │  Cancelled   │
               └─────────────┘
               (archive 7 yrs → purge)
```

#### Transition Rules

- **Draft → Pilot/Active**: All mandatory onboarding steps (1–8, 10, 16) must be completed.
- **Any → Suspended**: Immediate effect. All active user sessions invalidated. Background jobs paused.
- **Suspended → Active**: Requires payment resolution or Super Admin override. Paused jobs resume automatically.
- **Suspended/Inactive → Cancelled**: Requires explicit confirmation via `ConfirmModal` (danger variant). System generates final data export.
- **Cancelled → (none)**: Terminal state. Cannot be reversed.

#### Suspension Behavior

| Stakeholder | Access Level |
|---|---|
| Tenant employees | **No access.** Login returns "Account suspended — contact your administrator." |
| Company-Admin | **No access.** Same as employees. |
| Super Admin | **Read-only access** to all tenant configuration, audit logs, billing history, and user list. |

---

### 5.2 Company List Screen

The Company List screen is the primary tenant management interface.

#### Row Layout

| Element | Description |
|---|---|
| **Logo Initial** | Circular avatar with first letter, color-coded by status |
| **Company Name** | Primary display name |
| **Company Code** | Unique identifier (e.g., `TATA-STL-001`) |
| **Status Badge** | Draft (gray), Pilot (blue), Active (green), Inactive (amber), Suspended (red) |
| **Module Count** | Assigned modules out of 10 (e.g., "6/10") |
| **User Count** | Active users / tier ceiling (e.g., "142/200") |
| **Subscription Tier** | Starter, Growth, Scale, Enterprise, or Custom |

#### Filters

| Filter | Options |
|---|---|
| **Status** | All, Draft, Pilot, Active, Inactive, Suspended |
| **Subscription Tier** | All, Starter, Growth, Scale, Enterprise, Custom |
| **Industry** | Manufacturing, Pharma, Automotive, FMCG, Textiles, Chemicals, Electronics, Other |
| **Module** | Filter tenants by assigned module (multi-select) |
| **Created Date Range** | From / To date picker |

#### Sort Options

| Sort Field | Default Direction |
|---|---|
| Company Name | A → Z |
| Created Date | Newest first |
| Last Active | Most recent first |
| User Count | Highest first |

#### Bulk Actions

- **Bulk Status Change**: Select multiple tenants, change status.
- **Bulk Export**: Export selected tenant configurations as JSON or Excel.
- All bulk actions require confirmation via `ConfirmModal`.

#### Navigation

- Tap row → Company Detail Screen (`/tenant/[id]`)
- FAB at bottom-right: "Add Company" → 16-step wizard (`/tenant/add-company`)

---

### 5.3 Company Detail Screen

Organized into tabbed sections:

| Tab | Purpose |
|---|---|
| **Overview** | Identity snapshot, status controls, key contacts, quick stats |
| **Configuration** | All 16 onboarding steps as read/edit accordion sections |
| **Modules** | Assigned modules with enable/disable toggles and dependency info |
| **Users** | All users in this tenant with roles, status, and last activity |
| **Billing** | Subscription details, invoice history, payment records |
| **Audit Log** | Chronological log of all changes to this tenant |

#### Overview Tab

- **Company Identity Card**: Logo, legal name, business type, industry, CIN, company code, website, email domain.
- **Status Controls**: Current status badge + action buttons (Activate, Suspend, Deactivate, Cancel). Each action opens `ConfirmModal`.
- **Key Contacts**: Primary, HR, Finance, IT — displayed as tappable links.
- **Quick Stats**: Active users / tier ceiling, assigned modules / 10, monthly billing, days until renewal, last login, onboarding completion %.

#### Configuration Tab

All 16 onboarding steps rendered as collapsible accordion sections. Each shows current config in read-only mode with "Edit" button. Changes follow same Zod validation rules. Auto-save indicator after edits.

#### Modules Tab

- All 10 modules with enable/disable toggle, price, dependency status.
- Enabling triggers dependency resolution. Disabling blocked if dependents exist.
- Price impact shown before confirming.

#### Users Tab

- Searchable list of all tenant users.
- Columns: Full Name, Username, Role, Department, Status, Last Login.
- Super Admin can view but **cannot access tenant business data**.
- User count vs tier ceiling displayed at top.

#### Billing Tab

- Subscription summary: tier, billing cycle, renewal date, amount.
- Invoice history table with status and download.
- Payment history.
- Custom pricing indicator if applicable.

#### Audit Log Tab

- Chronological log with: Timestamp, Actor, Action, Previous Value, New Value.
- Filterable by date, action type, actor.
- Exportable as CSV.

---

### 5.4 16-Step Onboarding Wizard (Summary)

| Step | Name | What It Configures |
|---|---|---|
| **1** | Company Identity | Name, legal name, business type, industry, company code, incorporation date, CIN, website, email domain |
| **2** | Statutory & Tax | PAN, TAN, GSTIN, PF code, ESI code, PT registration, LWFR, ROC filing |
| **3** | Address | Registered address + corporate/HQ address (with "same as registered" toggle) |
| **4** | Fiscal & Calendar | FY start month, payroll cycle, week start, timezone, working days |
| **5** | Preferences | Currency, language, date format, compliance toggles, integrations (RazorpayX section when bank+razorpay enabled) |
| **6** | Backend Endpoint | Default cloud vs custom URL with live health check |
| **7** | Module Selection | From MODULE_CATALOGUE with dependency auto-resolution + custom pricing |
| **8** | User Tier & Pricing | Tier selection, billing cycle, trial days, pricing summary |
| **9** | Key Contacts | Primary, HR, Finance, IT, Legal contacts with phone/email |
| **10** | Plants & Branches | Facility types, geo-fencing, HQ designation, per-plant GSTIN |
| **11** | Shifts & Time | Day boundary, shift master, downtime slots |
| **12** | No. Series | Document numbering per module (company-wide or plant-wise) |
| **13** | IOT Reasons | Machine idle/alarm reasons for OEE (planned vs unplanned) |
| **14** | System Controls | NC edit mode, load/unload, cycle time, payroll lock, session timeout, password policy, MFA, IP whitelist |
| **15** | Users | Create Company-Admin + initial users with roles |
| **16** | Activation | Final review, validation, status change Draft → Active, go-live |

---

### 5.5 Tenant Data Isolation

#### Isolation Architecture

```
┌─────────────────────────────────────────────────────┐
│                   PostgreSQL Cluster                  │
│                                                       │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  │
│  │  tenant_001  │  │  tenant_002  │  │  tenant_003  │  │
│  │  (schema)    │  │  (schema)    │  │  (schema)    │  │
│  │  orders      │  │  orders      │  │  orders      │  │
│  │  employees   │  │  employees   │  │  employees   │  │
│  │  inventory   │  │  inventory   │  │  inventory   │  │
│  └─────────────┘  └─────────────┘  └─────────────┘  │
│                                                       │
│  ┌──────────────────────────────────────────────────┐ │
│  │              public (shared schema)               │ │
│  │  tenant_registry, platform_config, audit_log      │ │
│  └──────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────┘
```

#### Isolation Layers

| Layer | Mechanism | Description |
|---|---|---|
| **Schema Isolation** | PostgreSQL `search_path` | Each tenant's tables in a dedicated schema |
| **Logical Isolation** | `tenant_id` column | Additional safety net on all operational tables |
| **API-Level Isolation** | Tenant context resolution | API Gateway resolves tenant from JWT before routing |
| **Token-Level Isolation** | Tenant-scoped JWT | Tokens from Tenant A cannot access Tenant B |
| **Query-Level Isolation** | No cross-tenant joins | ORM configured to never cross tenant schemas |

#### Tenant Registry

| Field | Description |
|---|---|
| `tenant_id` | UUID, primary key |
| `company_code` | Unique alphanumeric identifier |
| `schema_name` | PostgreSQL schema name (e.g., `tenant_001`) |
| `db_host` | Database host (supports sharding) |
| `subscription_tier` | Current tier |
| `subscription_status` | Active, Trial, Suspended, Cancelled |
| `modules_enabled` | Array of enabled module IDs |
| `config_json` | Tenant configuration blob |
| `created_at` / `updated_at` | Timestamps |

#### Request Flow

1. Client sends request with JWT in `Authorization` header.
2. API Gateway validates JWT signature and expiry.
3. Gateway extracts `tenant_id` from JWT claims.
4. Gateway queries Tenant Registry for schema name and DB location.
5. Gateway verifies tenant status is `Active` (rejects if Suspended/Cancelled).
6. Request forwarded to service with tenant context injected.
7. Service sets `search_path` to tenant's schema and executes queries.

---

### 5.6 Company Management Actions

| Action | Description | Confirmation |
|---|---|---|
| **New Company** | Launches 16-step wizard. Creates tenant in Draft. | No |
| **Save** | Persists pending changes. Auto-save on field blur. | No |
| **Save Draft** | Saves incomplete wizard at current step. | No |
| **Delete** | Permanently removes Draft tenant (never activated only). | Yes — `ConfirmModal` (danger) |
| **Duplicate Company** | Creates new Draft pre-populated from existing tenant. Company-specific fields cleared. | Yes — `ConfirmModal` (primary) |
| **Export Config** | Exports full config as JSON or Excel. Includes all 16 steps + modules + user roster (without passwords). | No |

---

## 6. Module Management

### 6.1 Module Catalogue

| # | Module | Description | Dependencies |
|---|---|---|---|
| 1 | **Masters** | Core reference data shared across all modules | None |
| 2 | **Security** | Physical/digital security, gate operations | None |
| 3 | **Finance** | Accounting, payments, receivables, reporting | Masters |
| 4 | **Inventory** | Stock management, warehousing, material movement | Masters |
| 5 | **HR Management** | Employee lifecycle, payroll, attendance, compliance | Security |
| 6 | **Machine Maintenance** | Preventive/breakdown maintenance for equipment | Masters |
| 7 | **Production** | Shop-floor execution, OEE monitoring | Machine Maintenance, Masters |
| 8 | **Vendor Management** | Supplier onboarding, POs, vendor evaluation | Inventory, Masters |
| 9 | **Sales & Invoicing** | Order-to-cash, GST-compliant invoicing | Finance, Masters |
| 10 | **Visitor Management** | Visitor registration, tracking, access control | Security |

### 6.2 Module Assignment Per Tenant

#### Assignment Flow

1. Super Admin toggles module's enable switch.
2. System checks dependencies.
3. Unmet dependencies auto-added with notification.
4. Pricing impact displayed.
5. Super Admin confirms via `ConfirmModal`.
6. Module activated for tenant.

#### Revocation Flow

1. Super Admin toggles module's disable switch.
2. System checks if other active modules depend on it.
3. If dependents exist → **blocked** with explanation listing dependent modules.
4. If no dependents → confirm, module deactivated.

### 6.3 Dependency Resolution Logic

```
Sales & Invoicing ──► Finance ──► Masters
Vendor Management ──► Inventory ──► Masters
Production ──► Machine Maintenance ──► Masters
HR Management ──► Security
Visitor Management ──► Security
Finance ──► Masters
Inventory ──► Masters
Machine Maintenance ──► Masters
Security ──► (none)
Masters ──► (none)
```

#### Auto-Resolution Examples

| User Selects | Auto-Added | Notification |
|---|---|---|
| HR Management | Security | "Security auto-added — required by HR Management." |
| Production | Machine Maintenance, Masters | "Machine Maintenance and Masters auto-added — required by Production." |
| Sales & Invoicing | Finance, Masters | "Finance and Masters auto-added — required by Sales & Invoicing." |
| Vendor Management | Inventory, Masters | "Inventory and Masters auto-added — required by Vendor Management." |

### 6.4 Custom Module Pricing

| Field | Description |
|---|---|
| **Module** | Module being repriced |
| **Standard Price** | Catalogue price (read-only reference) |
| **Custom Price** | Override price |
| **Discount %** | Alternative: percentage discount off standard |
| **Reason** | Mandatory — why custom pricing was applied |
| **Effective From / To** | Date range for custom pricing |
| **Approved By** | Auto-populated Super Admin name |

### 6.5 Feature Toggles

#### Toggle Hierarchy

```
Platform-Wide Toggles (Super Admin)
    └── Tenant-Level Toggles (Super Admin)
         └── User-Level Toggles (Company-Admin, overridable by Super Admin)
```

Lower levels can only further restrict what higher levels permit.

| Level | Examples |
|---|---|
| **Platform-Wide** | `beta_new_dashboard`, `enable_ai_forecasting`, `maintenance_mode` |
| **Tenant-Level** | `enable_api_access`, `enable_bulk_import`, `enable_multi_currency` |
| **User-Level** | `can_approve_po_above_1L`, `restrict_export`, `bypass_maker_checker` |

---

## 7. User & Role Management

### 7.1 Platform-Level Users (Super Admins)

Super Admin accounts are for Avyren Technologies staff only.

| Field | Description |
|---|---|
| **Full Name** | Legal name |
| **Email** | Avyren corporate email |
| **Role** | Always `Super Admin` |
| **Status** | Active, Inactive, or Locked |
| **MFA Enabled** | Mandatory for all Super Admin accounts |
| **Last Login** | Most recent successful authentication |
| **Created By** | The Super Admin who created this account |

**Rules:**
- At least one Super Admin must exist at all times (system enforced).
- All actions logged with actor, timestamp, IP address.
- Failed logins trigger lockout after 5 consecutive failures (30-min lockout).

### 7.2 Two Primary System Roles

| Aspect | Super-Admin | Company-Admin |
|---|---|---|
| **Scope** | Global — cross-tenant | Single tenant only |
| **Can create tenants** | Yes | No |
| **Can configure tenants** | Yes (all 16 steps) | Partial (Steps 4, 5, 9–14) |
| **Can assign modules** | Yes | No |
| **Can access tenant business data** | **No** (unless temporary support grant) | Yes (all data within own tenant) |
| **Can create custom roles** | N/A | Yes (within own tenant) |
| **Can manage users** | Super Admin users only | Within own tenant |

**The Data Boundary:** Super Admins manage the platform; Company-Admins manage the business. A Super Admin can see that Tenant A has 142 users and HR module enabled, but cannot see employee salary data.

### 7.3 Dynamic Role Creation (Tenant-Level)

Company-Admin creates roles from scratch or from reference templates. Roles are **fully tenant-scoped** — "HR Manager" in Tenant A is completely separate from "HR Manager" in Tenant B.

#### Reference Role Templates

| Template | Default Module Access |
|---|---|
| **General Manager** | All assigned modules (View + Approve) |
| **Plant Manager** | Production, Machine Maintenance, Inventory, HR, Masters |
| **HR Personnel** | HR Management, Security |
| **Finance Team** | Finance, Sales & Invoicing |
| **Production Manager** | Production, Machine Maintenance, Masters |
| **Maintenance Technician** | Machine Maintenance, Masters |
| **Sales Executive** | Sales & Invoicing, Inventory, Masters |
| **Security Personnel** | Security, Visitor Management |
| **Stores Clerk** | Inventory, Masters |
| **Quality Inspector** | Production, Masters |
| **Auditor** | All modules (View + Export only) |
| **Viewer** | All modules (View only) |

### 7.4 Permission Granularity

Seven permission actions per module per role:

| Permission | Code | Description |
|---|---|---|
| **View** | `V` | Read access to records and reports |
| **Create** | `C` | Create new records |
| **Edit** | `E` | Modify existing records |
| **Delete** | `D` | Delete or archive records |
| **Approve** | `A` | Approve workflows (PO approval, leave approval, etc.) |
| **Export** | `X` | Export data as CSV, Excel, PDF |
| **Configure** | `G` | Change module settings |

#### Example Permission Matrix

| Module | Plant Manager | HR Personnel | Sales Executive |
|---|---|---|---|
| Masters | V·C·E·–·–·X·– | V·–·–·–·–·–·– | V·–·–·–·–·–·– |
| Security | V·–·–·–·–·–·– | V·C·E·–·–·X·– | –·–·–·–·–·–·– |
| HR Management | V·–·–·–·A·–·– | V·C·E·D·A·X·G | –·–·–·–·–·–·– |
| Production | V·C·E·D·A·X·G | –·–·–·–·–·–·– | –·–·–·–·–·–·– |
| Sales & Invoicing | –·–·–·–·–·–·– | –·–·–·–·–·–·– | V·C·E·D·A·X·– |

### 7.5 User-Level Feature Toggles

```
Role Permissions (base)
    + User-Level Grants (additional access)
    − User-Level Restrictions (removed access)
    = Effective Permissions (what the user actually sees)
```

- Company-Admin manages user-level toggles.
- Super Admin can override when necessary.
- Changes take effect on next session (not mid-session).
- All toggle changes logged in audit trail.

### 7.6 User Record Fields

| Field | Type | Required | Description |
|---|---|---|---|
| **Full Name** | Text | Yes | Display name |
| **User ID / Username** | Text | Yes | Unique login identifier. Immutable after creation. |
| **Password** | Secret | Yes (creation) | Subject to password policy. Temporary passwords must change on first login. |
| **Role** | Select | Yes | Super Admin, Company-Admin, or tenant-defined custom role |
| **Company Access Scope** | Reference | Yes (tenant) | The `tenant_id` this user belongs to |
| **Status** | Enum | Yes | Active, Inactive, Locked |
| **Email** | Email | Yes | For password resets, notifications, MFA recovery |
| **Mobile** | Phone | No | For SMS-based MFA and notifications |
| **Department** | Text | No | Informational — does not affect permissions |
| **Effective From / To** | Date | No | Time-bounded access (for contractors, interns) |
| **MFA Enabled** | Boolean | Depends | Governed by System Controls |
| **Last Login** | Timestamp | Auto | System-populated |

### 7.7 Super Admin vs Company Admin — Access Matrix

| Capability | Super Admin | Company-Admin |
|---|---|---|
| Create new tenant | ✅ | ❌ |
| Configure tenant (all 16 steps) | ✅ | Partial |
| Delete tenant | ✅ (Draft only) | ❌ |
| Suspend / Reactivate tenant | ✅ | ❌ |
| Assign modules | ✅ | ❌ |
| Change subscription tier | ✅ | ❌ |
| Set custom module pricing | ✅ | ❌ |
| View all tenants | ✅ | ❌ (own only) |
| View tenant billing | ✅ (all) | Own summary only |
| Generate invoices | ✅ | ❌ |
| Create Super Admin accounts | ✅ | ❌ |
| Create custom roles | N/A | ✅ (own tenant) |
| Create / manage users | Super Admin users only | ✅ (own tenant) |
| Set platform-wide toggles | ✅ | ❌ |
| Set tenant-level toggles | ✅ | ❌ |
| Set user-level toggles | Override only | ✅ (own tenant) |
| Access tenant business data | ❌ (unless support grant) | ✅ |
| View platform analytics | ✅ | ❌ |
| View audit logs | Platform + per-tenant config | Own tenant operations |
| Bulk operations across tenants | ✅ | ❌ |

### 7.8 Cross-Tenant User Overview

Metrics visible to Super Admin (without exposing individual business data):

| Metric | Description | Use Case |
|---|---|---|
| **Total Users per Tenant** | Active + Inactive + Locked count | Capacity planning |
| **Active Sessions** | Currently authenticated sessions per tenant | Load monitoring |
| **User Growth Trend** | Month-over-month change per tenant | Upsell identification |
| **Tier Ceiling Utilization** | Active users as % of tier ceiling | **Key upsell trigger** |
| **Last Activity per Tenant** | Most recent user login timestamp | Churn risk identification |
| **MFA Adoption Rate** | % of users with MFA enabled per tenant | Security compliance |

#### Tier Ceiling Alerts

| Threshold | Alert Level | Action |
|---|---|---|
| **80%** | Info | Notification to Super Admin |
| **90%** | Warning | Tenant flagged with amber indicator |
| **95%** | Urgent | Push notification + auto email to Company-Admin suggesting upgrade |
| **100%** | Block | New user creation blocked. Super Admin can override or initiate tier upgrade. |


---

## 8. Billing & Subscription Management

The billing engine is a core platform capability that ties together module selection, user tiers, and subscription lifecycle. Super Admins have full control over pricing, invoicing, and revenue tracking across all tenants.

---

### 8.1 Pricing Model

Avy ERP uses a **two-dimensional pricing model**:

```
Total Monthly Cost = Module Cost + User Tier Cost
```

**Dimension 1 — Module Cost**

Each module in the MODULE_CATALOGUE carries its own monthly price. When a tenant selects modules during onboarding (or later via module assignment), the individual module prices are summed. Some modules have dependencies (e.g., Payroll requires HRMS), and dependency modules are auto-included in the cost.

| Pricing Aspect | Detail |
|---|---|
| Granularity | Per module, per month |
| Annual discount | Tenants on annual billing receive a discount (typically 15–20%) applied to the module subtotal |
| Custom pricing | Super Admin can override catalogue price per tenant for negotiated deals |
| Dependency cost | Dependent modules are billed individually (no bundling discount unless manually applied) |

**Dimension 2 — User Tier Cost**

User tier pricing is based on the **maximum number of active users** the tenant is licensed for. Each tier has a per-user monthly rate that increases slightly at higher tiers to reflect the additional infrastructure, support, and SLA commitments.

| Tier | User Range | Per-User Rate (Indicative) | Typical Monthly Tier Cost |
|---|---|---|---|
| **Starter** | 50–100 users | Base rate | Lower |
| **Growth** | 101–200 users | Base + 5–10% | Moderate |
| **Scale** | 201–500 users | Base + 10–18% | Higher |
| **Enterprise** | 501–1,000 users | Base + 18–25% | Premium |
| **Custom** | 1,000+ users | Negotiated | Custom contract |

> **Note:** The per-user rate is not purely linear — higher tiers carry a slight premium because they include enhanced SLA guarantees, priority support, and dedicated infrastructure resources (e.g., larger shard allocations, higher rate limits).

**Tier Overflow Handling**

If a tenant's active user count crosses the ceiling of their current tier:

1. The system detects the overage during the next billing cycle reconciliation.
2. **Additional billing is auto-applied** — the delta users are charged at the next tier's per-user rate for the remainder of the billing period (prorated).
3. The tenant's **Company-Admin receives an automatic notification** informing them of the tier overage, the additional charge, and a recommendation to formally upgrade.
4. The Super Admin dashboard flags the tenant with an "Over Tier Limit" badge.
5. If the overage persists for more than one billing cycle, the Super Admin may choose to forcibly upgrade the tenant's tier.

**Pricing Examples**

| Scenario | Modules | Tier | Module Cost | Tier Cost | Total |
|---|---|---|---|---|---|
| Small manufacturer | Core + Inventory + Production | Starter (75 users) | ₹X/mo | ₹Y/mo | ₹(X+Y)/mo |
| Mid-size with HR | Core + Inventory + Production + HRMS + Payroll | Growth (150 users) | ₹A/mo | ₹B/mo | ₹(A+B)/mo |
| Enterprise full suite | All 10 modules | Enterprise (800 users) | ₹P/mo | ₹Q/mo | ₹(P+Q)/mo |

---

### 8.2 Subscription Management Screen

The Subscription Management screen provides a per-tenant view of billing status and allows the Super Admin to manage the full subscription lifecycle.

**Subscription Detail Fields**

| Field | Description |
|---|---|
| Tenant | Company name + tenant ID |
| Current Plan | List of active modules |
| User Tier | Starter / Growth / Scale / Enterprise / Custom |
| Active Users | Current active user count vs. tier ceiling |
| Billing Cycle | Monthly or Annual |
| Start Date | When the subscription began |
| Current Period | Start → end of current billing period |
| Renewal Date | Next billing date (auto-renewal unless cancelled) |
| Trial End Date | If in trial, when the trial expires |
| Monthly Cost | Module cost + tier cost breakdown |
| Status | Active, Trial, Expired, Suspended, Cancelled |
| Discount Applied | Any active coupon or negotiated discount |

**Subscription Statuses**

| Status | Meaning | Tenant Access |
|---|---|---|
| **Active** | Paid and in good standing | Full access to licensed modules |
| **Trial** | Within the trial period (default 14 days) | Full access, no billing yet |
| **Expired** | Trial ended without conversion, or subscription lapsed | Read-only access for 7-day grace, then suspended |
| **Suspended** | Payment overdue beyond grace period, or manually suspended by Super Admin | No access — login shows "Account Suspended" message |
| **Cancelled** | Tenant or Super Admin cancelled the subscription | Read-only access for data export period (30 days), then data archived |

**Super Admin Actions**

| Action | Description | Safeguards |
|---|---|---|
| **Upgrade Tier** | Move tenant to a higher user tier | Prorated billing for remainder of current period; confirmation modal with cost delta |
| **Downgrade Tier** | Move tenant to a lower user tier | Only allowed if current active users fit within the lower tier ceiling; takes effect at next renewal |
| **Change Billing Cycle** | Switch between monthly and annual | If switching to annual, prorated credit for current month applied; annual discount auto-calculated |
| **Apply Discount / Coupon** | Apply percentage or flat discount | Discount code validated; start/end date for discount; audit logged |
| **Cancel Subscription** | Initiate cancellation flow | Confirmation modal (danger variant); 30-day data-export window before archival; cannot be undone after archival |
| **Reactivate** | Reactivate a Suspended or Expired subscription | Requires clearing outstanding payment or manual override; sets status to Active |
| **Extend Trial** | Extend the trial period | Super Admin specifies new end date; maximum extension configurable in platform settings |

---

### 8.3 Invoice Management

Invoices are generated from the platform by the Super Admin (or auto-generated on billing cycle renewal).

**Invoice Fields**

| Field | Description |
|---|---|
| Invoice Number | Auto-generated, sequential (e.g., `AVY-INV-2026-00142`) |
| Tenant | Company name, GSTIN, billing address |
| Billing Period | e.g., 01 Mar 2026 – 31 Mar 2026 |
| Modules Billed | Line items for each active module with individual pricing |
| User Tier | Tier name, user count, per-user rate, tier subtotal |
| Discount | If applicable, discount line with percentage/amount |
| Subtotal | Sum before taxes |
| Tax (GST) | CGST + SGST (intra-state) or IGST (inter-state), calculated per Indian tax rules |
| Total | Final payable amount |
| Due Date | Payment deadline (default: 15 days from generation) |
| Payment Status | Paid / Pending / Overdue |
| Notes | Custom notes field for negotiated terms or special conditions |

**Invoice Actions**

| Action | Description |
|---|---|
| **Generate** | Create invoice for a tenant for a given period (manual or auto on renewal) |
| **Send** | Email invoice as PDF attachment to the tenant's billing contact |
| **Download PDF** | Super Admin downloads the invoice PDF locally |
| **Mark as Paid** | Manually mark invoice as paid (for offline payments); requires payment reference number |
| **Void** | Cancel an invoice (e.g., issued in error); voided invoices remain in records but are excluded from revenue calculations |
| **Add Credit Note** | Issue a credit note against an invoice for partial refunds or adjustments |
| **Duplicate** | Clone an invoice as a starting point for the next period |

**Auto-Generation Rules**

- For **monthly** billing: invoices auto-generate on the 1st of each month for the upcoming period.
- For **annual** billing: invoices auto-generate 30 days before the renewal date.
- Auto-generated invoices land in "Draft" status for Super Admin review before sending.
- Super Admin can configure auto-send (skip manual review) per tenant.

**Custom / Negotiated Pricing**

For Enterprise and Custom tier tenants with negotiated contracts:

- Super Admin can override individual module prices on the invoice.
- Custom line items can be added (e.g., "Dedicated Support SLA", "On-Premise Hosting Fee").
- Negotiated pricing is stored at the tenant level and auto-applied to future invoices.

---

### 8.4 Payment Tracking

**Per-Tenant Payment History**

Each tenant has a complete payment ledger accessible from the Subscription Management screen:

| Field | Description |
|---|---|
| Payment Date | When the payment was received/processed |
| Invoice Reference | Linked invoice number |
| Amount | Payment amount |
| Currency | INR (default), with multi-currency support for international tenants |
| Payment Method | Gateway (Razorpay/Stripe), Bank Transfer, Cheque, Cash |
| Transaction Reference | Gateway transaction ID or manual reference number |
| Status | Success, Failed, Pending, Refunded |
| Recorded By | "System" for gateway payments, Super Admin name for manual entries |

**Payment Methods**

| Method | Flow |
|---|---|
| **Integrated Gateway (Razorpay)** | Tenant pays via payment link in invoice email → gateway processes → webhook updates payment status automatically → invoice marked as Paid |
| **Bank Transfer (NEFT/RTGS/IMPS)** | Tenant transfers to Avyren's bank account → Super Admin manually records payment with UTR number → invoice marked as Paid |
| **Cheque** | Super Admin records cheque details (number, bank, date) → marks as Pending until clearance → updates to Success/Failed |
| **Offline / Cash** | Super Admin records with receipt reference → invoice marked as Paid |

**Failed Payment Handling**

| Step | Timing | Action |
|---|---|---|
| 1. Initial Failure | Day 0 | Gateway reports failure; system retries automatically after 24 hours |
| 2. First Retry | Day 1 | Auto-retry via gateway; if fails again, notification sent to tenant's billing contact |
| 3. Second Retry | Day 3 | Auto-retry; if fails, Super Admin notified; in-app banner shown to tenant |
| 4. Grace Period | Day 3–10 | Tenant retains full access; daily reminder emails sent |
| 5. Suspension Warning | Day 7 | Final warning email: "Your account will be suspended in 3 days" |
| 6. Suspension | Day 10 | Subscription status set to **Suspended**; tenant access blocked; Super Admin can override |
| 7. Manual Resolution | Any time | Super Admin can extend grace period, record offline payment, or waive charges |

---

### 8.5 Revenue Dashboard

The Revenue Dashboard provides platform-wide financial analytics. Accessible from the Super Admin's Billing tab.

**Key Metrics (Cards at Top)**

| Metric | Calculation |
|---|---|
| **MRR** (Monthly Recurring Revenue) | Sum of all active tenants' monthly subscription amounts (annual subscriptions divided by 12) |
| **ARR** (Annual Recurring Revenue) | MRR × 12 |
| **Churn Rate** | (Tenants lost in period ÷ Tenants at start of period) × 100% |
| **Average Revenue Per Tenant (ARPT)** | MRR ÷ Total active tenants |
| **Total Outstanding** | Sum of all Pending + Overdue invoice amounts |
| **Collection Rate** | (Paid invoices ÷ Total invoices generated) × 100% in the period |

**Revenue Breakdown Views**

| View | Visualization | Detail |
|---|---|---|
| **Revenue by Module** | Horizontal bar chart | Shows which modules generate the most revenue; helps identify high-value vs. underperforming modules |
| **Revenue by Tier** | Pie chart / donut | Revenue distribution across Starter, Growth, Scale, Enterprise, Custom |
| **Revenue by Billing Cycle** | Stacked bar | Monthly vs. annual billing revenue split |
| **Growth Trend** | Line chart (12-month) | MRR plotted month-over-month with trend line |
| **Churn Trend** | Line chart (12-month) | Monthly churn rate with moving average |
| **New vs. Expansion Revenue** | Stacked area chart | New tenant revenue vs. upgrade/expansion revenue from existing tenants |

**Filters**

- Date range (custom, last 30/90/180 days, YTD, last year)
- Tier filter
- Module filter
- Status filter (Active only, include Trial, include Cancelled)

**Export**

- Revenue report exportable as CSV or PDF
- Scheduled reports: Super Admin can configure weekly/monthly email reports with key metrics

---

## 9. Backend Architecture & API Design (Super Admin Perspective)

This section describes the backend architecture as it pertains to Super Admin operations — tenant provisioning, data isolation, API structure, and system management.

---

### 9.1 System Architecture Overview

Avy ERP follows a **Modular Monolith** architecture:

```
┌─────────────────────────────────────────────────────────────────┐
│                        API Gateway                              │
│         (Auth · Rate Limiting · Routing · Tenant Resolution)    │
└──────────────────────────────┬──────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────┐
│                     Application Server                          │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐          │
│  │   Core   │ │ Inventory│ │Production│ │   HRMS   │  ...      │
│  │  Module  │ │  Module  │ │  Module  │ │  Module  │          │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘          │
│  Each module: own Models, Services, Controllers, Routes        │
│  Inter-module communication via defined internal interfaces     │
└──────────────────────────────┬──────────────────────────────────┘
                               │
              ┌────────────────┼────────────────┐
              ▼                ▼                ▼
     ┌──────────────┐  ┌────────────┐  ┌──────────────┐
     │  PostgreSQL   │  │   Redis    │  │ File Storage │
     │ (Sharded DB)  │  │  (Cache +  │  │ (S3-compat)  │
     │               │  │  Sessions) │  │              │
     └──────────────┘  └────────────┘  └──────────────┘
```

**Key Architectural Principles**

| Principle | Implementation |
|---|---|
| **Single Deployable Unit** | The entire application ships as one Node.js/Express/TypeScript process. No inter-service network calls for core operations. |
| **Module Boundaries** | Each module (Core, Inventory, Production, HRMS, etc.) has its own directory containing models, services, controllers, and route definitions. Modules do not directly query each other's database tables. |
| **Internal Interfaces** | Modules communicate through well-defined service interfaces (function calls within the process). For example, the Payroll module calls `HRMSService.getEmployeeDetails(tenantId, employeeId)` rather than joining HRMS tables directly. |
| **Future Decomposition** | Because modules interact only through interfaces, any module can be extracted into a standalone microservice by replacing the in-process call with an HTTP/gRPC call — without rewriting business logic. |
| **Stateless Application Layer** | No session state on the server; all state is in JWT tokens or Redis. Any app server instance can handle any request. |

---

### 9.2 API Gateway

All client requests — from the mobile app (React Native/Expo), web app (React/Vite), and desktop app (ElectronJS) — pass through the API Gateway before reaching the application server.

**Gateway Responsibilities**

| Function | Detail |
|---|---|
| **Authentication** | Validates JWT access tokens on every request. Rejects expired or malformed tokens with `401 Unauthorized`. Refresh token flow handled at `/auth/refresh`. |
| **Rate Limiting** | Per-tenant and per-user rate limits enforced via Redis-backed sliding window. Default: 100 requests/minute per user, 1,000 requests/minute per tenant. Super Admin routes have separate (higher) limits. |
| **Request Routing** | Routes requests to the correct module handler based on URL path prefix (e.g., `/api/inventory/*` → Inventory module, `/api/platform/*` → Platform/Super Admin module). |
| **Tenant Resolution** | Extracts tenant context from the JWT `tenantId` claim (for tenant-scoped requests) or from the `X-Tenant-ID` header (for Super Admin cross-tenant operations). Looks up the Tenant Registry to resolve the correct database shard and schema. |
| **Request Logging** | Logs every request: timestamp, method, path, tenant ID, user ID, response status, latency. Feeds into the audit and monitoring systems. |
| **CORS & Security Headers** | Enforces CORS policy, sets security headers (HSTS, X-Frame-Options, Content-Security-Policy). |

**Tenant Resolution Flow**

```
Request arrives
    │
    ▼
Extract JWT from Authorization header
    │
    ▼
Decode JWT → get { userId, role, tenantId }
    │
    ├── If role = "super_admin" → tenantId is null (platform scope)
    │       │
    │       ▼
    │   For cross-tenant operations, read X-Tenant-ID header
    │
    ├── If role = "company_admin" or "user" → tenantId from JWT
    │
    ▼
Look up Tenant Registry: tenantId → { schemaName, shardId, dbHost }
    │
    ▼
Set request context: req.tenant = { id, schema, shard }
    │
    ▼
Forward to application server with tenant context attached
```

---

### 9.3 Tenant Provisioning Flow

When the Super Admin completes the 16-step Tenant Onboarding Wizard and activates a tenant, the backend executes the following provisioning pipeline:

```
Step 1: Create Tenant Registry Entry
    │   → INSERT into platform.tenants (tenant_id, name, metadata, status='Provisioning')
    │
Step 2: Determine Shard Assignment
    │   → Shard Router selects the least-loaded shard (or creates new shard if all are above threshold)
    │
Step 3: Provision Dedicated Schema
    │   → CREATE SCHEMA tenant_{id} on the assigned shard
    │   → Grant schema ownership to the application DB user
    │
Step 4: Run Database Migrations
    │   → Execute all migration scripts against the new schema
    │   → Creates tables: users, roles, permissions, modules, configurations, audit_logs, etc.
    │   → Only tables for assigned modules are created (e.g., no inventory tables if Inventory module not selected)
    │
Step 5: Initialize Default Configuration
    │   → Insert default settings (currency, timezone, FY, date format, etc.) from wizard data
    │   → Insert selected modules and their configurations
    │   → Create default roles (Company-Admin, Manager, User) with permission matrices
    │   → Insert number series, shift masters, plant/branch records from wizard data
    │
Step 6: Create Company-Admin User
    │   → INSERT into tenant_{id}.users (name, email, phone, role='company_admin')
    │   → Generate temporary password (bcrypt hashed)
    │   → Store credentials for welcome email
    │
Step 7: Finalize & Notify
        → UPDATE platform.tenants SET status='Active' (or 'Trial' if trial period configured)
        → Associate schema + shard in Tenant Registry routing table
        → Send welcome email to Company-Admin with:
            - Login URL
            - Temporary credentials
            - Setup guide link
            - Assigned modules summary
        → Log provisioning completion in platform audit trail
```

**Provisioning Performance**

| Metric | Target |
|---|---|
| Total provisioning time | < 2 minutes |
| Schema creation | < 5 seconds |
| Migration execution | < 30 seconds (depends on module count) |
| Default data seeding | < 15 seconds |
| Email delivery | < 60 seconds (async, via queue) |

**Error Handling During Provisioning**

If any step fails:

1. The provisioning is halted at the failing step.
2. Tenant status is set to `Provisioning Failed`.
3. Super Admin is notified with the failure reason and the step at which it failed.
4. A **Retry** action is available that resumes from the failed step (not from scratch).
5. All previously completed steps are idempotent — re-running them is safe.
6. If provisioning is abandoned, a **Cleanup** action rolls back: drops the schema, removes the registry entry, deletes any created users.

---

### 9.4 Database Architecture

**Schema-Per-Tenant Isolation**

Avy ERP uses PostgreSQL with a **schema-per-tenant** strategy. Each tenant gets a dedicated schema within a shared database cluster, providing strong logical isolation without the operational overhead of database-per-tenant.

```
PostgreSQL Cluster
├── Shard A (pg instance / RDS instance)
│   ├── platform schema          ← Tenant Registry, Super Admin data, billing
│   ├── tenant_001 schema        ← Tenant 1's tables
│   ├── tenant_002 schema        ← Tenant 2's tables
│   └── tenant_003 schema
│
├── Shard B (pg instance / RDS instance)
│   ├── tenant_004 schema
│   ├── tenant_005 schema
│   └── ...
│
└── Shard C
    └── ...
```

**Platform Schema (Tenant Registry)**

The `platform` schema exists at the cluster level and stores all cross-tenant data:

| Table | Key Columns | Purpose |
|---|---|---|
| `tenants` | tenant_id, name, schema_name, shard_id, status, subscription_tier, billing_cycle, created_at | Master tenant directory |
| `tenant_modules` | tenant_id, module_id, activated_at, pricing_override | Module assignments per tenant |
| `subscriptions` | tenant_id, tier, cycle, start_date, renewal_date, status, discount | Active subscription details |
| `invoices` | invoice_id, tenant_id, period_start, period_end, subtotal, tax, total, status, due_date | All invoices |
| `payments` | payment_id, invoice_id, tenant_id, amount, method, reference, status, recorded_at | Payment ledger |
| `super_admin_users` | user_id, name, email, password_hash, mfa_enabled, last_login | Super Admin accounts |
| `platform_audit_logs` | log_id, actor_id, action, entity_type, entity_id, old_value, new_value, ip, user_agent, timestamp | Platform audit trail |
| `shard_registry` | shard_id, host, port, max_tenants, current_tenants, status | Shard routing table |
| `notification_templates` | template_id, channel, event_type, subject, body, variables | Email/SMS/WhatsApp templates |
| `system_config` | key, value, description | Platform-wide settings |

**Per-Tenant Schema Tables (Subset)**

Each `tenant_{id}` schema contains:

| Table Category | Tables (examples) | Module |
|---|---|---|
| Core | users, roles, permissions, configurations, audit_logs, number_series | Core |
| Organization | plants, branches, departments, designations, shifts | Core |
| Inventory | items, warehouses, stock_ledger, purchase_orders, goods_receipts | Inventory |
| Production | bom, work_orders, production_entries, quality_checks | Production |
| HRMS | employees, attendance, leave_balances, leave_requests | HRMS |
| Payroll | salary_structures, payslips, tax_declarations | Payroll |
| ... | ... | ... |

**Sharding Strategy**

| Aspect | Detail |
|---|---|
| Shard assignment | New tenants are assigned to the shard with the fewest tenants (least-loaded) |
| Shard capacity | Configurable max tenants per shard (default: 500) |
| Scaling | New shards can be added without downtime; new tenants route to the new shard automatically |
| Tenant migration | A tenant can be migrated from one shard to another (pg_dump/pg_restore + registry update); used for load balancing or geographic placement |
| Backups | Each shard is backed up independently; point-in-time recovery available per shard |
| Cross-shard queries | The platform schema handles cross-tenant queries (e.g., "list all tenants") without touching tenant schemas. Aggregations (e.g., revenue) use the platform `invoices`/`payments` tables. |

---

### 9.5 Authentication & Authorization

**Token Architecture**

```
Login Request (email + password)
    │
    ▼
Server validates credentials
    │
    ▼
Issues:
    ├── Access Token (JWT, short-lived: 15 minutes)
    │       Claims: { userId, role, tenantId, permissions[], iat, exp }
    │
    └── Refresh Token (opaque, long-lived: 7 days, stored in Redis)
            Bound to: userId + deviceId + tenantId
```

**Role Hierarchy**

| Role | Scope | Capabilities |
|---|---|---|
| **Super Admin** | Platform-wide | All platform operations; can impersonate any tenant; no `tenantId` in JWT |
| **Company-Admin** | Single tenant | Full control within their tenant; user management, module config, settings |
| **Manager** | Single tenant | Department/module-level access as configured by Company-Admin |
| **User** | Single tenant | Operational access only (create transactions, view reports within permitted modules) |

**RBAC Enforcement**

- Authorization is enforced at the **API layer**, not just in the UI.
- Every route handler checks `req.user.role` and `req.user.permissions[]` before executing business logic.
- Super Admin routes (`/api/platform/*`) have a dedicated middleware: `requireSuperAdmin()` — rejects any non-Super-Admin token.
- Tenant-scoped routes (`/api/tenant/*`) have middleware: `requireTenantContext()` — ensures the JWT's `tenantId` matches the requested resource.
- Super Admins accessing tenant data pass `X-Tenant-ID` header; the gateway verifies their Super Admin role before allowing cross-tenant access.

**Security Policies**

| Policy | Default | Configurable By |
|---|---|---|
| Access token expiry | 15 minutes | Platform settings (Super Admin) |
| Refresh token expiry | 7 days | Platform settings |
| Session timeout (inactivity) | 30 minutes | Per-tenant (Company-Admin) |
| Password minimum length | 8 characters | Per-tenant (Company-Admin) |
| Password complexity | Uppercase + lowercase + number + special | Per-tenant |
| Password expiry | 90 days | Per-tenant |
| Failed login lockout | 5 attempts → 15-minute lockout | Per-tenant |
| MFA | Required for Super Admin; optional for tenant users | Super Admin enforces for SA; Company-Admin enables for tenant |

---

### 9.6 Backend Endpoint Configuration (Per Tenant)

Avy ERP supports two deployment models per tenant:

| Mode | Description | Use Case |
|---|---|---|
| **Default (Cloud)** | Tenant connects to the shared Avy ERP cloud backend. No configuration needed. | Most tenants (Starter, Growth, Scale) |
| **Custom (On-Premise / Private Cloud)** | Tenant's data and application run on their own infrastructure. The mobile/web apps connect to the tenant's custom backend URL. | Enterprise tenants with data residency or compliance requirements |

**Custom Endpoint Configuration**

During onboarding (Step 6) or via tenant settings, the Super Admin configures:

| Field | Description |
|---|---|
| Endpoint URL | Full base URL of the tenant's backend (e.g., `https://erp.acmecorp.com/api`) |
| Health Check Path | Path appended to base URL for connectivity verification (default: `/health`) |
| SSL Certificate Verification | Whether to enforce SSL cert validation (default: ON) |
| Custom Headers | Optional headers required by the tenant's infrastructure (e.g., API keys for their gateway) |

**Health Check**

- Super Admin can trigger a **live health check** from the tenant detail screen.
- The platform sends a GET request to `{endpointURL}{healthCheckPath}` and expects a `200 OK` with a JSON body containing `{ "status": "ok" }`.
- Health checks also run on a **scheduled interval** (configurable, default: every 5 minutes for custom endpoints).
- If a health check fails 3 consecutive times, the Super Admin receives a notification.
- Health check history is stored and visible on the tenant detail screen (last 24 hours of check results with latency).

**Endpoint Configuration Storage**

Stored in the `platform.tenants` table:

```
endpoint_type: 'default' | 'custom'
endpoint_url: VARCHAR (null for default)
health_check_path: VARCHAR (default '/health')
ssl_verify: BOOLEAN (default true)
custom_headers: JSONB (default null)
last_health_check: TIMESTAMP
last_health_status: 'healthy' | 'unhealthy' | 'unknown'
```

---

### 9.7 Super Admin API Endpoints (Key Routes)

All routes below are prefixed with `/api/platform` and protected by `requireSuperAdmin()` middleware.

**Tenant Management**

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/tenants` | Create a new tenant (triggers provisioning pipeline) |
| `GET` | `/tenants` | List all tenants (paginated, filterable by status/tier/search) |
| `GET` | `/tenants/:id` | Get full tenant detail (profile, modules, subscription, endpoint config) |
| `PATCH` | `/tenants/:id` | Update tenant metadata (name, address, contacts, settings) |
| `DELETE` | `/tenants/:id` | Soft-delete tenant (marks as Cancelled, starts offboarding) |
| `POST` | `/tenants/:id/activate` | Activate a Draft/Suspended tenant |
| `POST` | `/tenants/:id/suspend` | Suspend an Active tenant |
| `POST` | `/tenants/:id/health-check` | Trigger endpoint health check for a custom-endpoint tenant |

**Module Management**

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/tenants/:id/modules` | Assign one or more modules to a tenant |
| `DELETE` | `/tenants/:id/modules/:moduleId` | Revoke a module from a tenant |
| `GET` | `/tenants/:id/modules` | List modules assigned to a tenant |
| `PATCH` | `/tenants/:id/modules/:moduleId` | Update module configuration (e.g., custom pricing) |

**User Management**

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/tenants/:id/users` | List all users within a tenant |
| `POST` | `/tenants/:id/users` | Create a user within a tenant (typically Company-Admin during provisioning) |
| `PATCH` | `/tenants/:id/users/:userId` | Update user (role, status) |
| `DELETE` | `/tenants/:id/users/:userId` | Deactivate a user |
| `POST` | `/users` | Create a Super Admin user |
| `GET` | `/users` | List all Super Admin users |

**Billing & Invoicing**

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/billing/invoices` | Generate an invoice for a tenant |
| `GET` | `/billing/invoices` | List all invoices (filterable by tenant, status, date range) |
| `GET` | `/billing/invoices/:invoiceId` | Get invoice detail |
| `PATCH` | `/billing/invoices/:invoiceId` | Update invoice (mark paid, void, add notes) |
| `POST` | `/billing/invoices/:invoiceId/send` | Send invoice via email |
| `GET` | `/billing/invoices/:invoiceId/pdf` | Download invoice PDF |
| `GET` | `/billing/revenue` | Revenue metrics (MRR, ARR, churn, breakdowns) |
| `GET` | `/billing/payments` | Payment history (filterable) |
| `POST` | `/billing/payments` | Record a manual/offline payment |

**Audit & Analytics**

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/audit-logs` | Platform-level audit logs (paginated, filterable by actor/action/entity/date) |
| `GET` | `/tenants/:id/audit-logs` | Tenant-level audit logs (Super Admin viewing a tenant's internal audit trail) |
| `GET` | `/analytics` | Platform analytics (tenant count, user distribution, module adoption, etc.) |

**System**

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/health` | System health check (DB connectivity, Redis, queue status) |
| `GET` | `/config` | Get platform configuration |
| `PATCH` | `/config` | Update platform configuration |
| `POST` | `/announcements` | Broadcast system announcement to tenants |

> **Note:** All responses follow a consistent envelope: `{ "success": true, "data": {...}, "meta": { "page", "limit", "total" } }` for lists, and `{ "success": true, "data": {...} }` for single resources. Errors: `{ "success": false, "error": { "code", "message", "details" } }`.

---

## 10. Audit Trail & Compliance

Comprehensive audit logging is a non-negotiable requirement for an ERP system serving manufacturing companies. Avy ERP maintains two levels of audit trails: platform-level (Super Admin actions) and tenant-level (within each tenant's operations).

---

### 10.1 Platform-Level Audit Logging

Every action performed by a Super Admin is recorded in the `platform.platform_audit_logs` table. These logs are **immutable** — they cannot be edited or deleted through any API or admin interface.

**Audited Events**

| Category | Events Logged |
|---|---|
| **Tenant Lifecycle** | Tenant created, updated, activated, suspended, cancelled, deleted, provisioning started/completed/failed |
| **Module Management** | Module assigned to tenant, module revoked, module config updated, custom pricing applied |
| **User Management** | Super Admin user created/updated/deactivated, tenant user created/updated by Super Admin |
| **Status Changes** | Any status transition: Draft → Pilot → Active → Suspended → Cancelled (with reason) |
| **Billing Actions** | Invoice generated, sent, voided, marked as paid; payment recorded; subscription upgraded/downgraded; discount applied; billing cycle changed |
| **Authentication** | Super Admin login (success + failure), logout, password change, MFA setup/disable, session expired |
| **Configuration** | Platform settings changed (any key-value update in system_config), notification template modified, default tenant config changed |
| **System Operations** | Shard added/migrated, bulk operations executed, data export initiated, system announcement broadcast |

---

### 10.2 Audit Log Fields

Each audit log entry captures the following fields:

| Field | Type | Description |
|---|---|---|
| `log_id` | UUID | Unique identifier for the log entry |
| `timestamp` | TIMESTAMP WITH TZ | Exact time of the action (server clock, UTC) |
| `actor_id` | UUID | Super Admin user ID who performed the action |
| `actor_name` | VARCHAR | Display name of the actor (denormalized for query convenience) |
| `actor_email` | VARCHAR | Email of the actor |
| `action_type` | ENUM | Categorized action (e.g., `TENANT_CREATED`, `MODULE_ASSIGNED`, `INVOICE_GENERATED`) |
| `entity_type` | ENUM | Type of entity affected (`TENANT`, `USER`, `MODULE`, `INVOICE`, `SUBSCRIPTION`, `CONFIG`) |
| `entity_id` | VARCHAR | ID of the affected entity |
| `entity_name` | VARCHAR | Human-readable name (e.g., tenant name, user email) for quick reference |
| `old_value` | JSONB | Previous state of changed fields (null for create actions) |
| `new_value` | JSONB | New state of changed fields (null for delete actions) |
| `ip_address` | INET | IP address of the actor's device |
| `user_agent` | TEXT | Browser/app user agent string |
| `session_id` | VARCHAR | Session/token identifier for correlating related actions |
| `metadata` | JSONB | Additional context (e.g., provisioning step number, bulk operation batch ID) |

**Example Log Entry**

```json
{
  "log_id": "a1b2c3d4-...",
  "timestamp": "2026-03-18T10:23:45.123Z",
  "actor_id": "sa-001",
  "actor_name": "Chetan Kumar",
  "actor_email": "chetan@avyren.com",
  "action_type": "MODULE_ASSIGNED",
  "entity_type": "TENANT",
  "entity_id": "tenant-042",
  "entity_name": "Acme Manufacturing Pvt Ltd",
  "old_value": { "modules": ["core", "inventory"] },
  "new_value": { "modules": ["core", "inventory", "production", "quality"] },
  "ip_address": "203.0.113.42",
  "user_agent": "AvyERP-Mobile/1.2.0 (iOS 18.3)",
  "session_id": "sess_abc123",
  "metadata": { "added_modules": ["production", "quality"], "reason": "Tenant expansion request" }
}
```

---

### 10.3 Tenant-Level Audit (Viewable by Super Admin)

In addition to platform-level logs, the Super Admin can view the internal audit trail of any tenant. This is stored within each tenant's schema in the `audit_logs` table.

**What's Captured at Tenant Level**

| Category | Detail |
|---|---|
| **Field-Level Changes** | Every update to any record tracks: table name, record ID, field name, old value, new value, changed_by, changed_at |
| **User Activity** | Login/logout, password changes, role changes, user activation/deactivation |
| **Feature Toggle Changes** | When Company-Admin enables/disables a feature (e.g., ESS Portal, mobile access) |
| **Data Operations** | Record created, updated, deleted (soft) — across all module tables |
| **Bulk Imports** | CSV/Excel import operations: file name, record count, success/failure count, errors |
| **Report Access** | When sensitive reports are generated or exported |
| **Approval Workflows** | Approval requests, approvals, rejections with comments |

**Super Admin Access to Tenant Audit**

- Accessible via tenant detail screen → "Audit Logs" tab.
- API: `GET /api/platform/tenants/:id/audit-logs` with filters for date range, actor, action type, entity.
- Super Admin has **read-only** access to tenant audit logs — cannot modify or delete them.
- Tenant's Company-Admin also has access to the same logs from within their tenant dashboard.

---

### 10.4 Audit Log Retention

| Log Type | Default Retention | Configurable | Maximum |
|---|---|---|---|
| Platform audit logs | 2 years | Yes (Super Admin) | Unlimited |
| Tenant operational audit logs | 2 years | Yes (per-tenant by Company-Admin) | 7 years |
| Compliance-sensitive logs (financial, statutory) | 7 years | No (regulatory minimum) | Unlimited |
| Authentication logs | 1 year | Yes (Super Admin) | 5 years |

**Immutability Guarantees**

- Audit logs are stored in **append-only** tables with no UPDATE or DELETE permissions granted to the application database user.
- Database triggers prevent any modification or deletion of audit records.
- Logs are periodically checksummed and the checksums stored separately to detect tampering.
- For highest compliance requirements, logs can be replicated to a separate write-once storage (e.g., AWS S3 with Object Lock).

**Export Capabilities**

| Format | Use Case |
|---|---|
| **CSV** | For spreadsheet analysis, bulk review, sharing with auditors |
| **JSON** | For programmatic processing, integration with SIEM tools |
| **PDF** | For formal audit reports with Avyren letterhead and summary |

Export can be triggered from the UI with filters applied (date range, actor, entity type) — the export includes only matching records, not the entire log history.

---

### 10.5 Data Portability & Offboarding Compliance

When a tenant is permanently offboarded (subscription cancelled and grace period expired), a structured offboarding process ensures compliance with data protection regulations and contractual obligations.

**Offboarding Pipeline**

| Step | Action | Timeline |
|---|---|---|
| 1. Cancellation Initiated | Subscription status set to `Cancelled`; tenant notified | Day 0 |
| 2. Data Export Window | Tenant retains read-only access to export their data | Day 0–30 |
| 3. Super Admin Export | Super Admin generates a final comprehensive data export | Before Day 30 |
| 4. Access Revoked | All tenant user access disabled; login blocked | Day 30 |
| 5. Data Archived | Tenant schema is pg_dump'd to encrypted archive storage | Day 30–37 |
| 6. Schema Dropped | Tenant schema removed from the active shard | Day 37 |
| 7. Archive Retention | Archived data retained per regulatory requirements | 7 years |
| 8. Data Purge | After retention period, archived data permanently destroyed | Year 7 |
| 9. Purge Certificate | Destruction certificate generated and stored | Year 7 |

**Final Data Export Contents**

The comprehensive data export provided to the tenant includes:

- All master data (items, employees, customers, vendors, BOMs)
- All transactional data (purchase orders, production entries, invoices, payslips)
- All documents and attachments
- Audit trail (tenant-level)
- Configuration and settings
- User list with roles

**Export Formats**

| Data Type | Format |
|---|---|
| Structured data (tables) | CSV files (one per table) + combined Excel workbook |
| Documents/attachments | Original file format, organized in folders |
| Audit logs | CSV + JSON |
| Complete database | PostgreSQL dump (for tenants who want raw DB restore capability) |
| Summary report | PDF with data inventory, record counts, and export manifest |

**Audit Trail of Offboarding**

The offboarding process itself generates audit entries at every step:

- Who initiated the cancellation and when
- When data export was generated and by whom
- When access was revoked
- When archival was completed (with archive location reference)
- When purge was executed (with destruction certificate reference)

These meta-audit entries are retained in the platform audit logs **permanently** (not subject to the 7-year data retention — the record that "Tenant X was offboarded on Date Y" is kept indefinitely).

---

## 11. Notifications & Communication

The notification system enables the Super Admin to stay informed about platform events and communicate with tenants through multiple channels.

---

### 11.1 Notification Channels

| Channel | Technology | Use Case | Configuration |
|---|---|---|---|
| **Email** | SMTP (configurable provider) | Primary channel for invoices, welcome emails, formal communications | SMTP host, port, credentials, sender address, reply-to |
| **SMS** | SMS Gateway API | Payment reminders, urgent alerts, OTP for MFA | API key, sender ID, DLT template IDs (India regulatory) |
| **In-App Push** | Expo Push Notifications (mobile), WebSocket (web) | Real-time alerts, status updates, system announcements | Expo push tokens (mobile), WebSocket connection (web) |
| **WhatsApp Business API** | Official WhatsApp Cloud API | Invoice delivery, payment confirmations, maintenance notices (optional, tenant opt-in) | WhatsApp Business Account, API credentials, approved template IDs |

**Channel Priority & Fallback**

For critical notifications, the system uses a priority cascade:

1. **In-App Push** (immediate, if user is online)
2. **Email** (always sent for important events)
3. **SMS** (for payment failures, suspension warnings, and urgent system alerts)
4. **WhatsApp** (for invoice delivery, if tenant has opted in)

---

### 11.2 Super Admin Notifications

Events that trigger notifications to Super Admin users:

| Event | Channels | Priority |
|---|---|---|
| New tenant signup (self-service flow) | Push + Email | Normal |
| Tenant provisioning completed | Push | Normal |
| Tenant provisioning failed | Push + Email | High |
| Payment received | Push | Low |
| Payment failed (after retries exhausted) | Push + Email | High |
| Tenant approaching user tier ceiling (>90% of tier max) | Push + Email | Normal |
| Tenant exceeded user tier ceiling | Push + Email | High |
| Subscription expiring within 30 days | Email | Normal |
| Subscription expiring within 7 days | Push + Email | High |
| Subscription expired (no renewal) | Push + Email + SMS | Critical |
| Custom endpoint health check failure (3+ consecutive) | Push + Email | High |
| System health alert (high error rate >5%, DB connection issues) | Push + Email + SMS | Critical |
| Shard capacity threshold reached (>80%) | Email | Normal |
| Unusual activity detected (spike in API errors, bulk deletions) | Push + Email | High |

**Notification Preferences**

Each Super Admin user can configure their notification preferences:

- Toggle individual event types on/off per channel
- Set quiet hours (e.g., no push notifications between 10 PM – 7 AM, except Critical)
- Choose digest mode for low-priority events (daily summary email instead of individual notifications)

---

### 11.3 Tenant-Facing Notifications (Triggered by Super Admin Actions)

| Trigger | Recipient | Channels | Content |
|---|---|---|---|
| Tenant provisioned | Company-Admin | Email | Welcome email with login credentials, setup guide link, assigned modules |
| Module activated | Company-Admin | Email + Push | Module name, activation date, getting-started guide |
| Module revoked | Company-Admin | Email + Push | Module name, effective date, data retention note |
| Invoice generated | Billing Contact | Email + WhatsApp (opt-in) | Invoice PDF attachment, amount, due date, payment link |
| Payment received | Billing Contact | Email | Confirmation with receipt reference, next billing date |
| Payment failed | Billing Contact | Email + SMS | Failure reason, retry date, manual payment instructions |
| Subscription renewal reminder (30/15/7 days) | Company-Admin + Billing Contact | Email | Current plan summary, renewal date, renewal amount |
| Subscription tier changed | Company-Admin | Email | Old tier → new tier, pricing impact, effective date |
| Subscription suspended | Company-Admin | Email + SMS | Reason (payment overdue / manual), resolution steps, data access deadline |
| System maintenance scheduled | All tenant users | Push + Email | Maintenance window (start-end), expected downtime, affected services |
| Policy update | Company-Admin | Email | Policy change summary, effective date, required actions |

---

### 11.4 System Announcements

Super Admins can broadcast announcements to tenants. Announcements appear as banners in the tenant's dashboard (mobile and web).

**Announcement Types**

| Type | Banner Color | Auto-Dismiss | Example |
|---|---|---|---|
| **Maintenance Window** | Yellow/Warning | After maintenance ends | "Scheduled maintenance on Mar 25, 2:00–4:00 AM IST. Some services may be unavailable." |
| **Feature Update** | Blue/Info | After user dismisses | "New: Production Planning module now supports multi-level BOM. Learn more →" |
| **Policy Change** | Violet/Primary | After user acknowledges | "Updated Terms of Service effective Apr 1, 2026. Please review." |
| **Urgent Notice** | Red/Danger | Manual removal by Super Admin | "Critical security patch applied. Please clear app cache and restart." |

**Announcement Configuration**

| Field | Description |
|---|---|
| Title | Short headline (max 100 characters) |
| Body | Detailed message (markdown supported) |
| Type | Maintenance / Feature Update / Policy Change / Urgent Notice |
| Target | All tenants, specific tenants (multi-select), specific tiers |
| Start Date | When the announcement becomes visible |
| End Date | When the announcement auto-expires (optional) |
| Action URL | Optional link for "Learn more" / "Read details" |
| Require Acknowledgment | If true, user must tap "I understand" to dismiss |

**Announcement Delivery**

- Banners are fetched by the client app on dashboard load via `GET /api/tenant/announcements`.
- Active announcements are cached in Redis for fast retrieval.
- Dismissal state is tracked per user (so dismissed banners don't reappear).
- For announcements requiring acknowledgment, the acknowledgment is logged in the tenant's audit trail.

---

### 11.5 Notification Templates

All outbound notifications use configurable templates that the Super Admin can customize from the Settings screen.

**Template Structure**

| Field | Description |
|---|---|
| Template ID | Unique identifier (e.g., `welcome_email`, `invoice_generated`, `payment_failed`) |
| Channel | Email / SMS / WhatsApp |
| Event Type | The triggering event |
| Subject | Email subject line (not applicable for SMS/WhatsApp) |
| Body | Template body with variable placeholders |
| Variables | List of available variables for this template |

**Available Template Variables**

| Variable | Description | Available In |
|---|---|---|
| `{{company_name}}` | Tenant's registered company name | All templates |
| `{{admin_name}}` | Company-Admin's full name | All templates |
| `{{admin_email}}` | Company-Admin's email | All templates |
| `{{invoice_number}}` | Invoice reference number | Invoice templates |
| `{{invoice_amount}}` | Total invoice amount (formatted with currency) | Invoice templates |
| `{{due_date}}` | Invoice due date (formatted) | Invoice templates |
| `{{payment_link}}` | Gateway payment URL | Invoice / payment templates |
| `{{billing_period}}` | e.g., "March 2026" | Invoice templates |
| `{{module_name}}` | Name of the activated/revoked module | Module templates |
| `{{tier_name}}` | User tier name | Subscription templates |
| `{{renewal_date}}` | Next renewal date | Subscription templates |
| `{{login_url}}` | Tenant's login URL | Welcome email |
| `{{temp_password}}` | Temporary password (welcome email only) | Welcome email |
| `{{maintenance_start}}` | Maintenance window start time | Maintenance templates |
| `{{maintenance_end}}` | Maintenance window end time | Maintenance templates |
| `{{support_email}}` | Avyren support email address | All templates |
| `{{support_phone}}` | Avyren support phone number | All templates |

**Template Management**

- Super Admin can edit template subject and body from Settings → Notification Templates.
- A **preview** function renders the template with sample data before saving.
- **Reset to default** option restores the original template if customizations cause issues.
- Templates support basic HTML formatting for email (headers, bold, links, tables).
- SMS templates must comply with DLT registration requirements (India) — template changes may require re-registration with the telecom authority.
- WhatsApp templates must be pre-approved by Meta — changes go through an approval flow.

---

## 12. Platform Settings & Configuration

The Platform Settings screen is the Super Admin's control center for system-wide defaults, integration credentials, security policies, and operational parameters.

---

### 12.1 Default Tenant Configuration

When a new tenant is created through the onboarding wizard, these defaults are pre-populated. The Super Admin can modify these defaults so that future tenants inherit updated values. Individual tenants can override most of these after provisioning.

| Setting | Default Value | Overridable by Tenant | Notes |
|---|---|---|---|
| Currency | INR (₹) | Yes | Multi-currency support available; this sets the primary/base currency |
| Language | English | Yes | Future: Hindi, Tamil, and other regional language packs |
| Date Format | DD/MM/YYYY | Yes | Options: DD/MM/YYYY, MM/DD/YYYY, YYYY-MM-DD |
| Number Format | Indian (12,34,567.89) | Yes | Options: Indian, International (1,234,567.89) |
| Timezone | IST (UTC+5:30) | Yes | Full IANA timezone list available |
| Financial Year | April–March | Yes | Options: April–March, January–December, Custom |
| Week Start Day | Monday | Yes | Options: Sunday, Monday, Saturday |
| India Statutory Compliance Mode | ON | Yes (cannot turn off if Indian company) | Enables GST, TDS, PF, ESI fields and validations |
| ESS Portal (Employee Self-Service) | ON | Yes | Allows employees to view payslips, apply for leave, etc. |
| Mobile App Access | ON | Yes | Whether tenant's users can log in from the mobile app |
| Trial Period | 14 days | N/A (set at provisioning) | Super Admin can change the default for new tenants |
| Default User Role Template | Standard 3-role (Admin/Manager/User) | Yes (tenant can create custom roles) | Initial role structure seeded during provisioning |
| Document Attachment Max Size | 10 MB | Yes (up to platform max of 25 MB) | Per-file upload limit |
| Session Timeout | 30 minutes | Yes | Inactivity timeout before requiring re-authentication |
| Password Policy | 8 chars, mixed case + number + special | Yes (can be stricter, not weaker) | Tenant can increase minimums but not reduce below platform defaults |

**Modifying Defaults**

Changes to default tenant configuration apply only to **newly created tenants**. Existing tenants retain their current settings. To update an existing tenant's settings, the Super Admin must edit the tenant directly or the Company-Admin makes changes from their settings panel.

---

### 12.2 Integration Settings

Platform-level integration credentials used by the system for sending notifications, processing payments, and storing files.

**Payment Gateway**

| Setting | Description |
|---|---|
| Provider | Razorpay (primary), with option to add Stripe for international tenants |
| API Key ID | Gateway API key (test or live) |
| API Key Secret | Gateway secret (stored encrypted, displayed masked) |
| Webhook URL | Auto-generated URL for payment event callbacks (`https://api.avyerp.com/webhooks/razorpay`) |
| Webhook Secret | Shared secret for webhook signature verification |
| Mode | **Test** or **Live** — Test mode uses sandbox credentials; invoices generated in test mode are marked as "TEST" |
| Auto-Retry | Enable/disable automatic payment retry on failure (default: ON) |
| Retry Attempts | Number of retry attempts before marking as failed (default: 3) |
| Retry Interval | Hours between retries (default: 24 hours) |

**Email Provider (SMTP)**

| Setting | Description |
|---|---|
| SMTP Host | e.g., `smtp.gmail.com`, `email-smtp.ap-south-1.amazonaws.com` (SES) |
| SMTP Port | 587 (TLS) or 465 (SSL) |
| Username | SMTP authentication username |
| Password | SMTP authentication password (stored encrypted) |
| Sender Address | From address for outbound emails (e.g., `noreply@avyerp.com`) |
| Sender Name | Display name (e.g., "Avy ERP") |
| Reply-To Address | Where replies go (e.g., `support@avyren.com`) |
| Rate Limit | Maximum emails per hour (to comply with provider limits) |
| Test Connection | Button to send a test email to verify configuration |

**SMS Gateway**

| Setting | Description |
|---|---|
| Provider | Configurable (e.g., MSG91, Twilio, AWS SNS) |
| API Key / Auth Token | Gateway authentication credentials (stored encrypted) |
| Sender ID | Registered sender ID (e.g., "AVYERP") — must be DLT registered in India |
| DLT Entity ID | Distributed Ledger Technology registration ID (India regulatory requirement) |
| Template Registry | Mapping of notification types to DLT-registered template IDs |
| Rate Limit | Maximum SMS per hour |
| Test SMS | Button to send a test SMS to a specified number |

**WhatsApp Business API**

| Setting | Description |
|---|---|
| Provider | Meta WhatsApp Cloud API (direct) or third-party (e.g., Gupshup, Twilio) |
| Business Account ID | WhatsApp Business Account identifier |
| Phone Number ID | Registered WhatsApp phone number ID |
| Access Token | API access token (stored encrypted) |
| Template Namespace | Namespace for approved message templates |
| Approved Templates | List of pre-approved template names mapped to notification events |
| Opt-In Management | Track which tenants have opted in to WhatsApp notifications |

**Cloud Storage**

| Setting | Description |
|---|---|
| Provider | S3-compatible (AWS S3, MinIO, DigitalOcean Spaces, etc.) |
| Endpoint URL | S3 endpoint (e.g., `s3.ap-south-1.amazonaws.com`) |
| Bucket Name | Storage bucket for document attachments |
| Access Key ID | S3 access credentials |
| Secret Access Key | S3 secret (stored encrypted) |
| Region | AWS region or equivalent |
| Path Prefix | Folder structure within bucket (default: `tenants/{tenantId}/`) |
| Max File Size | Platform-wide upload size limit (default: 25 MB) |
| Allowed File Types | Whitelist of permitted extensions (e.g., pdf, jpg, png, xlsx, docx, csv) |
| Lifecycle Policy | Auto-archive to cold storage after N days (configurable) |

---

### 12.3 Security Settings

Platform-level security configuration that applies to Super Admin access and sets minimum baselines for tenants.

**Super Admin Password Policy**

| Setting | Default | Description |
|---|---|---|
| Minimum Length | 12 characters | Longer than tenant default due to elevated privileges |
| Complexity | Uppercase + lowercase + number + special character | All four categories required |
| Password Expiry | 60 days | Forced password rotation |
| Password History | Last 10 passwords | Cannot reuse recent passwords |
| Failed Attempt Lockout | 3 attempts → 30-minute lockout | Stricter than tenant default |

**Multi-Factor Authentication (MFA)**

| Setting | Default | Description |
|---|---|---|
| MFA for Super Admin | **Mandatory** (cannot be disabled) | All Super Admin accounts must have MFA enabled |
| MFA Methods | TOTP (authenticator app) | Google Authenticator, Authy, etc. |
| Backup Codes | 10 single-use codes generated on MFA setup | For recovery if authenticator is unavailable |
| MFA Grace Period | None | MFA required from first login after account creation |

**IP Whitelisting**

| Setting | Description |
|---|---|
| Enable IP Whitelist | Toggle to restrict Super Admin panel access to specified IPs |
| Allowed IPs | List of IPv4/IPv6 addresses or CIDR ranges |
| VPN Requirement | Optional note field to document VPN requirement |
| Violation Logging | All access attempts from non-whitelisted IPs are logged with IP and user agent |
| Emergency Override | Platform owner can add an IP via backend config in case of lockout |

**Session Management**

| Setting | Default | Description |
|---|---|---|
| Super Admin Session Timeout | 15 minutes (inactivity) | Shorter than tenant default for security |
| Maximum Concurrent Sessions | 2 | Prevents credential sharing; oldest session terminated on new login |
| Session Binding | Device fingerprint + IP | Session invalidated if device or IP changes mid-session |
| Force Logout All | Action button | Terminates all active Super Admin sessions immediately |

**Rate Limiting**

| Setting | Default | Description |
|---|---|---|
| Global Rate Limit | 1,000 requests/min per tenant | Prevents any single tenant from overwhelming the system |
| Per-User Rate Limit | 100 requests/min | Prevents individual user abuse |
| Super Admin Rate Limit | 500 requests/min | Higher limit for admin operations |
| Auth Endpoint Limit | 10 requests/min per IP | Brute-force protection on login endpoints |
| Burst Allowance | 2× the per-minute limit for 10-second window | Accommodates legitimate burst traffic (e.g., page load) |

**Encryption & TLS**

| Setting | Description |
|---|---|
| TLS Version | Minimum TLS 1.2 enforced; TLS 1.3 preferred |
| Certificate | Auto-managed via Let's Encrypt or manually uploaded custom certificate |
| Data at Rest | AES-256 encryption on database storage and S3 buckets |
| Data in Transit | All API communication over HTTPS; internal services communicate over TLS |
| Sensitive Field Encryption | Passwords, API keys, secrets encrypted with application-level encryption before database storage |
| Encryption Key Management | Keys stored in environment variables / secrets manager (AWS Secrets Manager / HashiCorp Vault) |

---

### 12.4 Backend Endpoint Defaults

Configuration for the default cloud backend and health monitoring for custom endpoints.

| Setting | Default | Description |
|---|---|---|
| Default Cloud URL | `https://api.avyerp.com` | The backend URL used by all tenants on default (cloud) endpoint mode |
| API Version Prefix | `/v1` | Current API version prefix |
| Health Check Path | `/health` | Path appended to endpoint URL for health verification |
| Health Check Interval | 5 minutes | How frequently custom endpoints are health-checked |
| Health Check Timeout | 10 seconds | Request timeout for health check calls |
| Consecutive Failures for Alert | 3 | Number of consecutive health check failures before notifying Super Admin |
| Failover Behavior | Show maintenance message to tenant users | What happens when a custom endpoint is unreachable |
| Failover Message | "Your ERP system is temporarily unavailable. Please contact your administrator." | Customizable message displayed to tenant users during outage |
| Custom Endpoint SSL Verification | ON | Whether to verify SSL certificates for custom endpoints (can be disabled for self-signed certs in development) |
| Custom Endpoint Allowed Ports | 443, 8443 | Whitelisted ports for custom endpoint URLs (security measure) |

---

### 12.5 Data Retention Policies

Configurable retention policies that govern how long various types of data are kept.

| Data Category | Default Retention | Minimum (Regulatory) | Maximum | Configurable By |
|---|---|---|---|---|
| Platform audit logs | 2 years | 1 year | Unlimited | Super Admin |
| Tenant operational audit logs | 2 years | 1 year | 7 years | Company-Admin (within bounds) |
| Financial/statutory audit logs | 7 years | 7 years (Indian Companies Act) | Unlimited | Not configurable (regulatory) |
| Authentication logs | 1 year | 6 months | 5 years | Super Admin |
| Archived tenant data (post-offboarding) | 7 years | 7 years (regulatory) | 10 years | Super Admin |
| Database backups | 30 days (daily) + 12 months (monthly) | 30 days | 24 months | Super Admin |
| Point-in-time recovery window | 7 days | 1 day | 14 days | Super Admin |
| Temporary/session data (Redis) | 24 hours | N/A | 72 hours | Super Admin |
| File attachments (active tenants) | Indefinite (while tenant is active) | N/A | N/A | N/A |
| File attachments (archived tenants) | 7 years (matches data retention) | 7 years | 10 years | Super Admin |

**Backup Configuration**

| Setting | Default | Description |
|---|---|---|
| Backup Frequency | Daily at 02:00 IST | Full shard backup via pg_basebackup |
| Incremental Backups | Continuous WAL archiving | Enables point-in-time recovery |
| Backup Storage | S3-compatible cold storage | Separate from operational storage |
| Backup Encryption | AES-256 | Backups encrypted at rest |
| Backup Verification | Weekly restore test (automated) | Ensures backups are actually recoverable |
| Cross-Region Replication | OFF (configurable) | For disaster recovery; replicates to a different AWS region |
| Backup Notification | On failure only | Email alert if any backup job fails |

**GDPR / Data Protection Compliance**

| Setting | Description |
|---|---|
| Data Processing Agreement | Standard DPA template available for tenants; Super Admin can customize |
| Right to Access | Tenant can request full data export (supported via offboarding export flow) |
| Right to Erasure | Upon tenant offboarding + retention period, data is permanently purged |
| Data Portability | Export in standard formats (CSV, JSON, SQL dump) |
| Consent Tracking | WhatsApp and marketing communications require explicit opt-in; opt-in/out status stored per tenant |
| Data Breach Protocol | Configurable escalation: detect → assess → notify Super Admin (within 1 hour) → notify affected tenants (within 24 hours) → notify authorities (within 72 hours per GDPR/Indian DPDP Act) |
| Privacy Officer Contact | Configurable email/phone displayed in privacy policy and breach notifications |

---

*End of Sections 8–12.*

---

## 13. Mobile App Implementation — Super Admin Screens

The Super Admin mobile experience is built on Expo SDK 54 with Expo Router 6 file-based routing. Every screen follows a consistent pattern: a `LinearGradient` header (indigo-to-violet), Inter font family throughout, NativeWind utility classes for text styling, and `StyleSheet.create()` for layout. Navigation combines bottom tabs (5 primary destinations) with a collapsible sidebar (full section catalog) and stack navigation for drill-down flows.

---

### 13.1 Route Structure

Expo Router maps the filesystem directly to routes. All Super Admin routes live under the authenticated group `(app)`:

```
src/app/(app)/
├── _layout.tsx                        # Root: TabLayout + SidebarProvider + AuthGuard
├── index.tsx                          # Tab 1 → Dashboard (Platform Overview)
├── companies.tsx                      # Tab 2 → Company List
├── billing.tsx                        # Tab 3 → Billing Overview
├── more.tsx                           # Tab 4 → More Menu
├── settings.tsx                       # Tab 5 → Platform Settings hub
│
├── tenant/
│   ├── [id].tsx                       # Company Detail (tabbed: Overview · Config · Modules · Users · Billing · Audit)
│   ├── add-company.tsx                # 16-step Onboarding Wizard
│   ├── module-assignment.tsx          # Per-tenant module toggle screen
│   └── edit-subscription.tsx          # Edit subscription / pricing for a tenant
│
├── users/
│   ├── index.tsx                      # Platform Users list (Super Admin accounts)
│   ├── [userId].tsx                   # Platform User detail / edit
│   └── tenant-users.tsx              # Cross-tenant user overview (aggregated stats)
│
├── billing/
│   ├── invoices.tsx                   # Invoice management (list + filters)
│   ├── invoices/[invoiceId].tsx       # Invoice detail / PDF preview
│   ├── revenue.tsx                    # Revenue dashboard (MRR, ARR, charts)
│   └── payments.tsx                   # Payment history (all tenants)
│
├── modules/
│   ├── catalogue.tsx                  # Module catalogue management (add/edit/deprecate)
│   ├── catalogue/[moduleId].tsx       # Module detail (description, dependencies, pricing, tenants using it)
│   └── dependencies.tsx              # Visual dependency map
│
├── audit/
│   └── index.tsx                      # Audit log viewer (filterable, expandable entries)
│
├── reports/
│   ├── index.tsx                      # Platform analytics hub
│   ├── tenant-health.tsx              # Tenant health report
│   ├── usage.tsx                      # Module usage analytics
│   └── growth.tsx                     # Growth metrics (tenant acquisition, churn)
│
├── support/
│   ├── tickets.tsx                    # Support ticket list
│   ├── tickets/[ticketId].tsx         # Ticket detail / thread
│   └── announcements.tsx             # System announcements (create, schedule, history)
│
└── settings/
    ├── integrations.tsx               # Integration settings (payment gateways, email, SMS, WhatsApp)
    ├── integrations/[integrationId].tsx # Integration detail / config
    ├── notifications.tsx              # Notification template management
    ├── security.tsx                   # Security settings (MFA policy, session timeout, IP whitelist)
    └── platform-config.tsx            # Platform-wide config (default tier, trial days, etc.)
```

**Route file pattern** — every route file is a thin re-export:

```tsx
// src/app/(app)/companies.tsx
export { CompanyListScreen as default } from '@/features/super-admin/company-list-screen';
```

```tsx
// src/app/(app)/tenant/[id].tsx
export { CompanyDetailScreen as default } from '@/features/super-admin/company-detail-screen';
```

```tsx
// src/app/(app)/audit/index.tsx
export { AuditLogScreen as default } from '@/features/super-admin/audit-log-screen';
```

This keeps route files under 3 lines and all logic inside `src/features/`.

---

### 13.2 Feature Folder Structure

All screen components, hooks, types, and utilities live in `src/features/`. The Super Admin domain is the largest feature folder:

```
src/features/
├── auth/
│   ├── login-screen.tsx                   # Email + password form
│   ├── mfa-screen.tsx                     # TOTP code entry
│   ├── useAuthStore.ts                    # Zustand: token, user, role, login/logout actions
│   ├── useAuth.ts                         # React Query: login mutation, refresh mutation
│   └── auth-guard.tsx                     # Redirect to login if unauthenticated
│
├── super-admin/
│   ├── dashboard-screen.tsx               # Platform Overview Dashboard
│   ├── company-list-screen.tsx            # All Companies (search, filter, sort)
│   ├── company-detail-screen.tsx          # Company Detail (tabbed interface)
│   │
│   ├── tenant-onboarding/                 # 16-step wizard — EXISTING modular structure
│   │   ├── index.tsx                      # Wizard orchestrator (state, validation, navigation)
│   │   ├── types.ts                       # All TypeScript interfaces
│   │   ├── constants.ts                   # MODULE_CATALOGUE, USER_TIERS, FACILITY_TYPES, etc.
│   │   ├── schemas.ts                     # Zod schemas per step + validateStep()
│   │   ├── shared-styles.ts              # Shared StyleSheet (S)
│   │   ├── atoms.tsx                      # Reusable form atoms (FormInput, ChipSelector, etc.)
│   │   ├── step-indicator.tsx             # Scrollable step dots + progress bar
│   │   └── steps/
│   │       ├── step01-identity.tsx        # Company Identity
│   │       ├── step02-statutory.tsx       # Statutory & Tax
│   │       ├── step03-address.tsx         # Address
│   │       ├── step04-fiscal.tsx          # Fiscal & Calendar
│   │       ├── step05-preferences.tsx     # Preferences + RazorpayX
│   │       ├── step06-endpoint.tsx        # Backend Endpoint
│   │       ├── step07-modules.tsx         # Module Selection
│   │       ├── step08-pricing.tsx         # User Tier & Pricing
│   │       ├── step09-contacts.tsx        # Key Contacts
│   │       ├── step10-plants.tsx          # Plants & Branches
│   │       ├── step11-shifts.tsx          # Shifts & Time
│   │       ├── step12-noseries.tsx        # Number Series
│   │       ├── step13-iot.tsx             # IOT Reasons
│   │       ├── step14-controls.tsx        # System Controls
│   │       ├── step15-users.tsx           # Initial Users
│   │       └── step16-activation.tsx      # Activation & Review
│   │
│   ├── billing-overview-screen.tsx        # Billing summary (MRR, ARR, outstanding)
│   ├── invoice-management-screen.tsx      # Invoice list + CRUD
│   ├── invoice-detail-screen.tsx          # Single invoice detail + PDF
│   ├── revenue-dashboard-screen.tsx       # Revenue analytics + charts
│   ├── payment-history-screen.tsx         # Payment records across tenants
│   │
│   ├── module-catalogue-screen.tsx        # Module catalogue management
│   ├── module-detail-screen.tsx           # Module detail + tenant adoption
│   ├── module-assignment-screen.tsx       # Per-tenant module toggle
│   ├── module-dependency-screen.tsx       # Dependency visualization
│   │
│   ├── platform-users-screen.tsx          # Super Admin account management
│   ├── platform-user-detail-screen.tsx    # Individual SA user detail
│   ├── tenant-user-overview-screen.tsx    # Cross-tenant user aggregation
│   │
│   ├── audit-log-screen.tsx               # Audit trail viewer
│   ├── platform-analytics-screen.tsx      # Platform reports hub
│   ├── tenant-health-screen.tsx           # Per-tenant health scoring
│   ├── usage-analytics-screen.tsx         # Module usage analytics
│   ├── growth-metrics-screen.tsx          # Acquisition, churn, expansion
│   │
│   ├── support-tickets-screen.tsx         # Support ticket list
│   ├── ticket-detail-screen.tsx           # Ticket conversation thread
│   ├── announcement-screen.tsx            # System announcements
│   │
│   ├── more-menu-screen.tsx               # More menu (links to all non-tab screens)
│   │
│   ├── settings/
│   │   ├── platform-settings-screen.tsx   # General platform config
│   │   ├── integration-settings-screen.tsx # Third-party integrations
│   │   ├── integration-detail-screen.tsx  # Single integration config
│   │   ├── notification-templates-screen.tsx # Email/SMS/Push templates
│   │   ├── security-settings-screen.tsx   # MFA, session, IP whitelist
│   │   └── platform-config-screen.tsx     # Default tier, trial, etc.
│   │
│   ├── hooks/
│   │   ├── useTenants.ts                  # useQuery: fetch tenant list
│   │   ├── useTenantDetail.ts             # useQuery: single tenant
│   │   ├── useTenantMutation.ts           # useMutation: create/update/delete tenant
│   │   ├── useModuleCatalogue.ts          # useQuery: all modules
│   │   ├── useModuleAssignment.ts         # useMutation: assign/revoke modules
│   │   ├── useInvoices.ts                 # useQuery: invoice list
│   │   ├── useInvoiceMutation.ts          # useMutation: generate/void invoice
│   │   ├── useRevenue.ts                  # useQuery: revenue metrics
│   │   ├── usePlatformUsers.ts            # useQuery: SA user list
│   │   ├── useAuditLogs.ts               # useQuery: audit entries (paginated)
│   │   ├── useAnnouncements.ts            # useQuery + useMutation
│   │   ├── useSupportTickets.ts           # useQuery + useMutation
│   │   └── usePlatformAnalytics.ts        # useQuery: analytics data
│   │
│   └── types/
│       ├── tenant.ts                      # Tenant, TenantSummary, TenantHealth
│       ├── billing.ts                     # Invoice, Payment, Subscription, RevenueMetrics
│       ├── module.ts                      # Module, ModuleDependency, ModuleAssignment
│       ├── user.ts                        # PlatformUser, TenantUserSummary
│       ├── audit.ts                       # AuditLogEntry, AuditFilter
│       ├── analytics.ts                   # PlatformMetrics, UsageData, GrowthData
│       └── support.ts                     # Ticket, TicketMessage, Announcement
│
└── settings/                              # Shared settings (used by all roles)
    ├── profile-screen.tsx
    └── appearance-screen.tsx
```

---

### 13.3 Bottom Tab Configuration

The Super Admin has exactly 5 bottom tabs. The tab bar uses the standard Expo Router `Tabs` component with custom styling:

| Tab | Label | Icon (Lucide) | Route | Screen |
|-----|-------|---------------|-------|--------|
| 1 | Dashboard | `LayoutDashboard` | `/(app)/index` | Platform Overview |
| 2 | Companies | `Building2` | `/(app)/companies` | Company List |
| 3 | Billing | `CreditCard` | `/(app)/billing` | Billing Overview |
| 4 | More | `MoreHorizontal` | `/(app)/more` | More Menu |
| 5 | Settings | `Settings` | `/(app)/settings` | Platform Settings |

**Tab bar styling:**

```tsx
// src/app/(app)/_layout.tsx
import { Tabs } from 'expo-router';
import { SidebarProvider } from '@/components/ui/sidebar';

export default function TabLayout() {
  return (
    <SidebarProvider>
      <TabLayoutInner />
    </SidebarProvider>
  );
}

function TabLayoutInner() {
  return (
    <Tabs
      screenOptions={{
        headerShown: false,
        tabBarActiveTintColor: colors.primary[600],   // Indigo active
        tabBarInactiveTintColor: colors.neutral[400],
        tabBarStyle: {
          backgroundColor: '#FFFFFF',
          borderTopWidth: 1,
          borderTopColor: colors.neutral[100],
          paddingBottom: Platform.OS === 'ios' ? 20 : 8,
          height: Platform.OS === 'ios' ? 88 : 64,
        },
        tabBarLabelStyle: {
          fontFamily: 'Inter_500Medium',
          fontSize: 11,
        },
      }}
    >
      <Tabs.Screen
        name="index"
        options={{
          title: 'Dashboard',
          tabBarIcon: ({ color, size }) => (
            <LayoutDashboard size={size} color={color} />
          ),
        }}
      />
      <Tabs.Screen
        name="companies"
        options={{
          title: 'Companies',
          tabBarIcon: ({ color, size }) => (
            <Building2 size={size} color={color} />
          ),
          tabBarBadge: pendingCount > 0 ? pendingCount : undefined,
        }}
      />
      <Tabs.Screen
        name="billing"
        options={{
          title: 'Billing',
          tabBarIcon: ({ color, size }) => (
            <CreditCard size={size} color={color} />
          ),
        }}
      />
      <Tabs.Screen
        name="more"
        options={{
          title: 'More',
          tabBarIcon: ({ color, size }) => (
            <MoreHorizontal size={size} color={color} />
          ),
        }}
      />
      <Tabs.Screen
        name="settings"
        options={{
          title: 'Settings',
          tabBarIcon: ({ color, size }) => (
            <SettingsIcon size={size} color={color} />
          ),
        }}
      />

      {/* Hidden from tab bar — accessible via navigation only */}
      <Tabs.Screen name="tenant/[id]" options={{ href: null }} />
      <Tabs.Screen name="tenant/add-company" options={{ href: null }} />
      <Tabs.Screen name="tenant/module-assignment" options={{ href: null }} />
      <Tabs.Screen name="tenant/edit-subscription" options={{ href: null }} />
      <Tabs.Screen name="users/index" options={{ href: null }} />
      <Tabs.Screen name="users/[userId]" options={{ href: null }} />
      <Tabs.Screen name="users/tenant-users" options={{ href: null }} />
      <Tabs.Screen name="billing/invoices" options={{ href: null }} />
      <Tabs.Screen name="billing/revenue" options={{ href: null }} />
      <Tabs.Screen name="billing/payments" options={{ href: null }} />
      <Tabs.Screen name="modules/catalogue" options={{ href: null }} />
      <Tabs.Screen name="modules/dependencies" options={{ href: null }} />
      <Tabs.Screen name="audit/index" options={{ href: null }} />
      <Tabs.Screen name="reports/index" options={{ href: null }} />
      <Tabs.Screen name="support/tickets" options={{ href: null }} />
      <Tabs.Screen name="support/announcements" options={{ href: null }} />
      <Tabs.Screen name="settings/integrations" options={{ href: null }} />
      <Tabs.Screen name="settings/notifications" options={{ href: null }} />
      <Tabs.Screen name="settings/security" options={{ href: null }} />
      <Tabs.Screen name="settings/platform-config" options={{ href: null }} />
    </Tabs>
  );
}
```

**Badge behavior:** The Companies tab shows a badge count when tenants are in "Pending Activation" or "Draft" status and need Super Admin attention.

---

### 13.4 Sidebar Sections (Mobile)

The sidebar is a full-height absolute overlay that slides in from the left, triggered by the `HamburgerButton` in any screen header. It mirrors the navigation architecture from Section 3 of this document. Contents are role-gated: the sidebar only renders Super Admin sections when `useAuthStore().user.role === 'super_admin'`.

**Sidebar section configuration:**

```tsx
const superAdminSections: SidebarSection[] = [
  {
    title: 'Dashboard',
    items: [
      { label: 'Platform Overview', icon: LayoutDashboard, route: '/(app)/' },
    ],
  },
  {
    title: 'Companies',
    items: [
      { label: 'All Companies', icon: Building2, route: '/(app)/companies' },
      { label: 'Add Company', icon: PlusCircle, route: '/(app)/tenant/add-company' },
    ],
  },
  {
    title: 'Billing',
    items: [
      { label: 'Billing Overview', icon: CreditCard, route: '/(app)/billing' },
      { label: 'Invoices', icon: FileText, route: '/(app)/billing/invoices' },
      { label: 'Revenue', icon: TrendingUp, route: '/(app)/billing/revenue' },
      { label: 'Payment History', icon: Banknote, route: '/(app)/billing/payments' },
    ],
  },
  {
    title: 'Modules',
    items: [
      { label: 'Module Catalogue', icon: Package, route: '/(app)/modules/catalogue' },
      { label: 'Dependencies', icon: GitBranch, route: '/(app)/modules/dependencies' },
    ],
  },
  {
    title: 'Reports',
    items: [
      { label: 'Platform Analytics', icon: BarChart3, route: '/(app)/reports/' },
      { label: 'Audit Logs', icon: Shield, route: '/(app)/audit/' },
    ],
  },
  {
    title: 'Users',
    items: [
      { label: 'Platform Users', icon: UserCog, route: '/(app)/users/' },
      { label: 'Tenant Users', icon: Users, route: '/(app)/users/tenant-users' },
    ],
  },
  {
    title: 'Support',
    items: [
      { label: 'Tickets', icon: LifeBuoy, route: '/(app)/support/tickets' },
      { label: 'Announcements', icon: Megaphone, route: '/(app)/support/announcements' },
    ],
  },
  {
    title: 'Settings',
    items: [
      { label: 'Platform Settings', icon: Settings, route: '/(app)/settings' },
      { label: 'Integrations', icon: Plug, route: '/(app)/settings/integrations' },
      { label: 'Notifications', icon: Bell, route: '/(app)/settings/notifications' },
      { label: 'Security', icon: Lock, route: '/(app)/settings/security' },
    ],
  },
];
```

**Sidebar behavior:**
- Opens via `useSidebar().open()` called by `HamburgerButton`
- Closes on: item tap, backdrop tap, swipe left, or `useSidebar().close()`
- Animated slide-in from left using `react-native-reanimated` (`SlideInLeft` / `SlideOutLeft`)
- Current route highlighted with `primary[50]` background and `primary[600]` text
- Section headers are non-tappable labels in `neutral[500]` uppercase text
- Renders above tab bar via absolute positioning with `zIndex: 100`

---

### 13.5 Key UI Patterns

#### 13.5.1 Screen Header Pattern

Every Super Admin screen uses a consistent gradient header:

```tsx
import { LinearGradient } from 'expo-linear-gradient';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { HamburgerButton } from '@/components/ui/sidebar';
import { colors } from '@/components/ui/colors';

function ScreenHeader({ title, subtitle, rightAction }: ScreenHeaderProps) {
  const insets = useSafeAreaInsets();

  return (
    <LinearGradient
      colors={[colors.gradient.start, colors.gradient.mid, colors.gradient.end]}
      start={{ x: 0, y: 0 }}
      end={{ x: 1, y: 1 }}
      style={[styles.header, { paddingTop: insets.top + 12 }]}
    >
      <View style={styles.headerRow}>
        <HamburgerButton />
        <View style={styles.headerText}>
          <Text className="font-inter text-white text-xl font-bold">{title}</Text>
          {subtitle && (
            <Text className="font-inter text-white/70 text-sm">{subtitle}</Text>
          )}
        </View>
        {rightAction}
      </View>
    </LinearGradient>
  );
}
```

#### 13.5.2 List Screen Pattern

All list screens (Companies, Invoices, Users, Audit, Tickets) follow an identical structure:

```
┌─────────────────────────────────┐
│  Gradient Header + Hamburger    │
├─────────────────────────────────┤
│  SearchBar                      │
│  [Filter Chip] [Chip] [Chip]   │
├─────────────────────────────────┤
│  Result count + Sort dropdown   │
├─────────────────────────────────┤
│  ┌───────────────────────────┐  │
│  │ List Item (animated)      │  │  ← FadeInDown with staggered delay
│  │ • Avatar/Icon left        │  │
│  │ • Title + subtitle        │  │
│  │ • StatusBadge right       │  │
│  │ • Chevron right           │  │
│  └───────────────────────────┘  │
│  ┌───────────────────────────┐  │
│  │ List Item                 │  │
│  └───────────────────────────┘  │
│  ...                            │
│                                 │
│  Pull-to-refresh                │
│  Infinite scroll pagination     │
├─────────────────────────────────┤
│  FAB (+ Add New) — if writable │
└─────────────────────────────────┘
```

**Implementation:**

```tsx
<FlatList
  data={filteredItems}
  keyExtractor={(item) => item.id}
  renderItem={({ item, index }) => (
    <Animated.View entering={FadeInDown.delay(index * 50).duration(400)}>
      <ListItem item={item} onPress={() => router.push(`/(app)/tenant/${item.id}`)} />
    </Animated.View>
  )}
  refreshControl={
    <RefreshControl refreshing={isRefreshing} onRefresh={refetch} />
  }
  onEndReached={fetchNextPage}
  onEndReachedThreshold={0.5}
  ListEmptyComponent={<EmptyState message="No companies found" />}
  contentContainerStyle={{ paddingBottom: 100 }}
/>
```

#### 13.5.3 Detail Screen Pattern

Detail screens (Company Detail, Invoice Detail, Module Detail, Ticket Detail) use a tabbed or sectioned layout:

```
┌─────────────────────────────────┐
│  Gradient Header                │
│  • Back arrow left              │
│  • Entity name + ID            │
│  • StatusBadge                  │
│  • Action menu (⋯) right       │
├─────────────────────────────────┤
│  [Tab1] [Tab2] [Tab3] [Tab4]   │  ← Horizontal scrollable tabs
├─────────────────────────────────┤
│  ScrollView                     │
│  ┌───────────────────────────┐  │
│  │ SectionCard               │  │
│  │ • Section title           │  │
│  │ • Key-value rows          │  │
│  │ • Inline edit (pencil)    │  │
│  └───────────────────────────┘  │
│  ┌───────────────────────────┐  │
│  │ SectionCard               │  │
│  │ ...                       │  │
│  └───────────────────────────┘  │
└─────────────────────────────────┘
```

**Company Detail tabs:**

| Tab | Content |
|-----|---------|
| Overview | Company identity, status, subscription tier, key contacts, creation date, health score |
| Config | Statutory info, fiscal calendar, preferences, backend endpoint, system controls |
| Modules | Assigned modules with toggle, dependency warnings, pricing impact |
| Users | Company Admin + user list (read-only), license utilization |
| Billing | Subscription plan, invoices, payment history, next billing date |
| Audit | Filtered audit log (only this tenant's events) |

#### 13.5.4 Status Badge Variants

```tsx
type BadgeVariant = 'active' | 'pilot' | 'draft' | 'inactive' | 'suspended' | 'pending' | 'overdue';

const variantStyles: Record<BadgeVariant, { bg: string; text: string }> = {
  active:    { bg: colors.success[50],  text: colors.success[700]  },  // Green
  pilot:     { bg: colors.info[50],     text: colors.info[700]     },  // Blue
  draft:     { bg: colors.warning[50],  text: colors.warning[700]  },  // Amber
  inactive:  { bg: colors.danger[50],   text: colors.danger[700]   },  // Red
  suspended: { bg: '#FFF7ED',           text: '#C2410C'            },  // Orange
  pending:   { bg: colors.accent[50],   text: colors.accent[700]   },  // Violet
  overdue:   { bg: colors.danger[100],  text: colors.danger[800]   },  // Dark red
};
```

#### 13.5.5 ConfirmModal Usage

Every destructive or high-impact action uses `ConfirmModal`. Never `Alert.alert()`:

```tsx
const { show, hide, modalProps } = useConfirmModal();

// Deactivate tenant
show({
  title: 'Deactivate Company',
  message: `Are you sure you want to deactivate ${tenant.name}? All users will lose access immediately.`,
  variant: 'danger',
  confirmText: 'Deactivate',
  onConfirm: () => deactivateMutation.mutate(tenant.id),
});

// Revoke module
show({
  title: 'Revoke Module',
  message: `Removing "${module.name}" will also remove dependent modules: ${dependents.join(', ')}. This cannot be undone.`,
  variant: 'warning',
  confirmText: 'Revoke All',
  onConfirm: () => revokeModuleMutation.mutate({ tenantId, moduleIds }),
});

// In JSX — always render the modal
<ConfirmModal {...modalProps} />
```

**Actions requiring ConfirmModal:**
- Deactivate / suspend / delete a tenant
- Revoke a module (especially when it has dependents)
- Void an invoice
- Revoke a support access grant
- Delete a platform user account
- Change a tenant's subscription tier (downgrade)
- Cancel a tenant's subscription
- Send a system-wide announcement
- Reset a user's MFA

#### 13.5.6 Bottom Sheet Quick Actions

Non-destructive quick actions use `@gorhom/bottom-sheet`:

```tsx
<BottomSheet
  ref={bottomSheetRef}
  snapPoints={['35%']}
  enablePanDownToClose
  backdropComponent={BottomSheetBackdrop}
>
  <BottomSheetView style={styles.sheetContent}>
    <ActionItem icon={FileText} label="Generate Invoice" onPress={handleGenerateInvoice} />
    <ActionItem icon={Send} label="Send Reminder" onPress={handleSendReminder} />
    <ActionItem icon={Download} label="Export Data" onPress={handleExport} />
    <ActionItem icon={Eye} label="View Audit Log" onPress={handleViewAudit} />
  </BottomSheetView>
</BottomSheet>
```

Use bottom sheets for: tenant quick actions, invoice actions, bulk operations, filter panels, sort options.

#### 13.5.7 Animation Conventions

| Context | Animation | Import |
|---------|-----------|--------|
| List items appearing | `FadeInDown.delay(index * 50).duration(400)` | `react-native-reanimated` |
| Screen content loading | `FadeInUp.duration(500)` | `react-native-reanimated` |
| Sidebar opening | `SlideInLeft.duration(300)` | `react-native-reanimated` |
| Card expanding | `Layout.springify()` | `react-native-reanimated` |
| Tab content switching | `FadeIn.duration(200)` | `react-native-reanimated` |
| Bottom sheet | Built-in spring animation | `@gorhom/bottom-sheet` |
| Pull-to-refresh | System default | `RefreshControl` |

#### 13.5.8 Form Patterns

Simple forms (edit a single field, add a note) use bottom sheet modals. Complex forms (onboarding wizard, integration setup) use full-screen. All forms use the atom components from `tenant-onboarding/atoms.tsx`:

- `FormInput` — labeled text input with optional error message
- `SecretInput` — masked input with eye toggle (for API keys, passwords)
- `ChipSelector` — single select from a set of chips
- `MultiChipSelector` — multi select with checkmark chips
- `PhoneInput` — country code picker + phone number input
- `ToggleRow` — label + description + toggle switch
- `SectionCard` — grouped form section with header
- `RadioOption` — radio button row

#### 13.5.9 Empty States

Every list screen handles the zero-data case gracefully:

```tsx
function EmptyState({ icon: Icon, title, message, actionLabel, onAction }: EmptyStateProps) {
  return (
    <Animated.View entering={FadeInUp.duration(500)} style={styles.emptyContainer}>
      <Icon size={64} color={colors.neutral[300]} />
      <Text className="font-inter text-neutral-600 text-lg font-semibold mt-4">{title}</Text>
      <Text className="font-inter text-neutral-400 text-sm text-center mt-2 px-8">{message}</Text>
      {actionLabel && (
        <Pressable style={styles.emptyAction} onPress={onAction}>
          <Text className="font-inter text-primary-600 font-semibold">{actionLabel}</Text>
        </Pressable>
      )}
    </Animated.View>
  );
}
```

#### 13.5.10 Error & Loading States

```tsx
// Loading skeleton — used while React Query is fetching
function ListSkeleton({ rows = 5 }: { rows?: number }) {
  return (
    <View style={styles.skeletonContainer}>
      {Array.from({ length: rows }).map((_, i) => (
        <Animated.View
          key={i}
          entering={FadeInDown.delay(i * 80)}
          style={styles.skeletonRow}
        >
          <View style={[styles.skeletonCircle, styles.shimmer]} />
          <View style={styles.skeletonLines}>
            <View style={[styles.skeletonLine, { width: '60%' }, styles.shimmer]} />
            <View style={[styles.skeletonLine, { width: '40%' }, styles.shimmer]} />
          </View>
        </Animated.View>
      ))}
    </View>
  );
}

// Error state with retry
function ErrorState({ message, onRetry }: { message: string; onRetry: () => void }) {
  return (
    <View style={styles.errorContainer}>
      <AlertTriangle size={48} color={colors.danger[400]} />
      <Text className="font-inter text-neutral-600 text-base mt-3">{message}</Text>
      <Pressable style={styles.retryButton} onPress={onRetry}>
        <Text className="font-inter text-primary-600 font-semibold">Retry</Text>
      </Pressable>
    </View>
  );
}
```

---

### 13.6 More Menu Structure

The "More" tab serves as the overflow navigation for screens that do not have their own bottom tab:

```
┌─────────────────────────────────┐
│  Gradient Header: "More"        │
├─────────────────────────────────┤
│                                 │
│  ┌─ Modules ─────────────────┐  │
│  │ 📦 Module Catalogue       │  │
│  │ 🔗 Dependencies           │  │
│  └───────────────────────────┘  │
│                                 │
│  ┌─ Users ───────────────────┐  │
│  │ 👤 Platform Users         │  │
│  │ 👥 Tenant Users           │  │
│  └───────────────────────────┘  │
│                                 │
│  ┌─ Reports ─────────────────┐  │
│  │ 📊 Platform Analytics     │  │
│  │ 🛡 Audit Logs             │  │
│  └───────────────────────────┘  │
│                                 │
│  ┌─ Support ─────────────────┐  │
│  │ 🎫 Support Tickets        │  │
│  │ 📢 Announcements          │  │
│  └───────────────────────────┘  │
│                                 │
└─────────────────────────────────┘
```

Each menu item is a pressable row with icon, label, and right chevron. Section grouping uses `SectionCard` with section title header. Items use `router.push()` to navigate to the appropriate route.

---

## 14. Data Flow & Screen Linkages

This section maps every major user journey through the Super Admin mobile app, identifying the screens involved, data passed between them, API calls triggered, and state management responsibilities.

---

### 14.1 Dashboard to Company Detail Flow

**Journey:** Super Admin opens app, sees platform overview, identifies a tenant needing attention, navigates to its detail.

```
┌──────────────┐     tap tenant row     ┌──────────────────┐
│   Dashboard  │  ─────────────────────→ │  Company Detail   │
│   (index)    │                         │  (tenant/[id])    │
└──────────────┘                         └──────────────────┘
       │                                         │
       │ useQuery: GET /api/platform/dashboard    │ useQuery: GET /api/platform/tenants/:id
       │ Returns: KPI cards, tenant health table, │ Returns: Full tenant config, subscription,
       │ recent activity, alerts                  │ modules, users, billing, audit
       │                                         │
       │ Zustand: dashboardFilters               │ Zustand: selectedTab (Overview|Config|...)
       │ (dateRange, sortBy)                     │
```

**Data passed via navigation:**

```tsx
// From Dashboard
router.push({
  pathname: '/(app)/tenant/[id]',
  params: { id: tenant.id },
});

// Company Detail reads the param
const { id } = useLocalSearchParams<{ id: string }>();
const { data: tenant, isLoading } = useTenantDetail(id);
```

**Tenant Health Table → Detail linkage:**
The dashboard's tenant health table shows a summarized row per tenant (name, status, health score, MRR, active users). Tapping any row navigates to the full Company Detail screen. The detail screen fetches fresh data (not cached from the table) to ensure the user always sees the latest state.

---

### 14.2 Onboarding to Activation Flow

**Journey:** Super Admin creates a new tenant through the 16-step wizard, which provisions the tenant in the backend upon activation.

```
┌──────────┐   tap "Add"   ┌────────────────────┐   Step 16    ┌──────────────┐
│ Company  │ ────────────→ │  Onboarding Wizard │ ──────────→ │ Company List │
│ List     │               │  (16 steps)        │  Activate    │ (refreshed)  │
└──────────┘               └────────────────────┘              └──────────────┘
     │                              │                                 │
     │ FAB onPress:                 │ Local state (Zustand):          │ Invalidate:
     │ router.push(                 │ - step1..step16 form data       │ queryClient.invalidateQueries(
     │   'tenant/add-company'       │ - currentStep: number           │   ['tenants']
     │ )                            │ - stepErrors: Record            │ )
                                    │                                 │
                                    │ Step 16 "Activate":             │
                                    │ POST /api/platform/tenants      │
                                    │ Body: complete tenant config    │
                                    │ Response: { id, status }        │
```

**State management during onboarding:**

The wizard state is held entirely in `index.tsx` via `useState` hooks (not Zustand) because it is ephemeral and scoped to the wizard lifetime:

```tsx
// Simplified state structure in TenantOnboardingScreen
const [currentStep, setCurrentStep] = useState(0);
const [stepErrors, setStepErrors] = useState<Record<string, string>>({});

// Step 1 state
const [companyName, setCompanyName] = useState('');
const [tradeName, setTradeName] = useState('');
const [industry, setIndustry] = useState('');
// ... (all step state as individual useState hooks)

// Validation before advancing
const handleNext = () => {
  const errors = validateCurrentStep();
  if (Object.keys(errors).length > 0) {
    setStepErrors(errors);
    return; // Block navigation
  }
  setStepErrors({});
  setCurrentStep((prev) => prev + 1);
};
```

**Activation API call (Step 16):**

```tsx
const activateMutation = useMutation({
  mutationFn: (payload: TenantCreatePayload) =>
    apiClient.post('/api/platform/tenants', payload),
  onSuccess: (data) => {
    queryClient.invalidateQueries({ queryKey: ['tenants'] });
    queryClient.invalidateQueries({ queryKey: ['dashboard'] });
    router.replace({
      pathname: '/(app)/tenant/[id]',
      params: { id: data.id },
    });
  },
  onError: (error) => {
    // Show error in activation step — do NOT use Alert
    setActivationError(error.message);
  },
});
```

**Draft saving:** If the user navigates away mid-wizard, the app prompts via `ConfirmModal`:

```tsx
show({
  title: 'Save as Draft?',
  message: 'You have unsaved onboarding progress. Save as draft to continue later?',
  variant: 'primary',
  confirmText: 'Save Draft',
  onConfirm: () => saveDraftMutation.mutate(collectWizardState()),
});
```

Drafts are stored server-side via `POST /api/platform/tenants/drafts` and appear in the Company List with status "Draft".

---

### 14.3 Module Assignment Flow

**Journey:** Super Admin navigates to a tenant's Modules tab, toggles a module on, reviews dependency and pricing impact, confirms.

```
┌──────────────┐   Modules tab   ┌────────────────────┐   Confirm   ┌──────────────┐
│ Company      │ ──────────────→ │ Module Assignment  │ ──────────→ │ Updated      │
│ Detail       │                 │ (toggle + deps)    │             │ Company      │
│ (Modules)    │                 └────────────────────┘             │ Detail       │
└──────────────┘                          │                         └──────────────┘
                                          │
                                          │ 1. Toggle module ON
                                          │ 2. Check dependencies (client-side from MODULE_CATALOGUE)
                                          │ 3. If unmet deps → show warning with required modules
                                          │ 4. Calculate pricing impact (from tier pricing)
                                          │ 5. Show ConfirmModal with summary
                                          │ 6. PATCH /api/platform/tenants/:id/modules
                                          │ 7. Invalidate tenant detail + billing queries
```

**Dependency resolution (client-side):**

```tsx
import { MODULE_CATALOGUE } from '@/features/super-admin/tenant-onboarding/constants';

function resolveDependencies(moduleId: string, currentlyEnabled: string[]): {
  required: string[];    // Modules that must also be enabled
  willDisable: string[]; // Modules that depend on this one (if disabling)
} {
  const module = MODULE_CATALOGUE.find((m) => m.id === moduleId);
  const required = (module?.dependencies ?? []).filter(
    (depId) => !currentlyEnabled.includes(depId)
  );
  const willDisable = MODULE_CATALOGUE
    .filter((m) => m.dependencies?.includes(moduleId) && currentlyEnabled.includes(m.id))
    .map((m) => m.id);
  return { required, willDisable };
}
```

**Pricing impact display:**

When a module is toggled, the assignment screen shows a bottom section:

```
┌──────────────────────────────────┐
│ Pricing Impact                   │
│                                  │
│ Current MRR:        ₹12,500/mo  │
│ + Manufacturing:    + ₹3,000/mo │
│ + Quality (req'd):  + ₹1,500/mo │
│ ─────────────────────────────── │
│ New MRR:            ₹17,000/mo  │
│                                  │
│ [Cancel]            [Confirm]    │
└──────────────────────────────────┘
```

---

### 14.4 Billing Flow

**Journey:** Super Admin reviews billing overview, drills into a tenant's billing, generates an invoice, records payment.

```
┌──────────┐   tap tenant   ┌──────────────┐   Generate    ┌──────────────┐
│ Billing  │ ─────────────→ │ Tenant       │ ───────────→ │ Invoice      │
│ Overview │                │ Billing Tab  │  Invoice      │ Detail       │
└──────────┘                └──────────────┘               └──────────────┘
     │                            │                              │
     │ GET /api/platform/         │ GET /api/platform/           │ POST /api/platform/
     │   billing/overview         │   tenants/:id/billing        │   invoices/generate
     │                            │                              │
     │ Shows:                     │ Shows:                       │ Shows:
     │ • Total MRR/ARR            │ • Subscription plan          │ • Invoice number
     │ • Outstanding amount       │ • Invoice history            │ • Line items (modules)
     │ • Overdue invoices         │ • Payment history            │ • Tax breakdown
     │ • Revenue trend chart      │ • Next billing date          │ • Total amount
     │ • Tenant-wise breakdown    │ • Credit balance             │ • Payment status
     │                            │ • Usage metrics              │ • Record Payment button
```

**Invoice generation flow:**

```tsx
// Bottom sheet action from Tenant Billing tab
const generateInvoiceMutation = useMutation({
  mutationFn: (params: { tenantId: string; billingPeriod: string }) =>
    apiClient.post('/api/platform/invoices/generate', params),
  onSuccess: (invoice) => {
    queryClient.invalidateQueries({ queryKey: ['invoices'] });
    queryClient.invalidateQueries({ queryKey: ['tenant-billing', tenantId] });
    router.push({
      pathname: '/(app)/billing/invoices/[invoiceId]',
      params: { invoiceId: invoice.id },
    });
  },
});
```

**Payment recording flow:**

```tsx
// From Invoice Detail screen
const recordPaymentMutation = useMutation({
  mutationFn: (payment: {
    invoiceId: string;
    amount: number;
    method: 'bank_transfer' | 'upi' | 'card' | 'cheque';
    reference: string;
    paidAt: string;
  }) => apiClient.post(`/api/platform/invoices/${payment.invoiceId}/payments`, payment),
  onSuccess: () => {
    queryClient.invalidateQueries({ queryKey: ['invoices'] });
    queryClient.invalidateQueries({ queryKey: ['revenue'] });
    queryClient.invalidateQueries({ queryKey: ['dashboard'] }); // Update MRR on dashboard
  },
});
```

**Billing state flow diagram:**

```
Invoice Generated → Sent → Viewed → Payment Recorded → Paid
                  ↘ Overdue (past due date) → Reminder Sent → Payment Recorded → Paid
                  ↘ Voided (ConfirmModal required)
                  ↘ Disputed → Resolution → Paid / Credit Issued
```

---

### 14.5 User Management Flow

**Journey:** Super Admin manages platform users (other Super Admins) and views tenant user statistics.

```
┌──────┐   More → Users   ┌──────────────────┐   tap user   ┌──────────────┐
│ More │ ────────────────→ │ Platform Users   │ ───────────→ │ User Detail  │
│ Menu │                   │ (SA accounts)    │              │ (edit role)  │
└──────┘                   └──────────────────┘              └──────────────┘
                                                                    │
                                                                    │ PATCH /api/platform/users/:id
                                                                    │ • Update role
                                                                    │ • Enable/disable MFA
                                                                    │ • Deactivate account

┌──────┐   More → Users   ┌──────────────────┐   tap tenant  ┌─────────────┐
│ More │ ────────────────→ │ Tenant User      │ ────────────→ │ Company     │
│ Menu │                   │ Overview         │               │ Detail      │
└──────┘                   │ (cross-tenant)   │               │ (Users tab) │
                           └──────────────────┘               └─────────────┘
```

**Platform Users data:**

```tsx
// GET /api/platform/users
interface PlatformUser {
  id: string;
  name: string;
  email: string;
  role: 'super_admin' | 'platform_support' | 'platform_viewer';
  mfaEnabled: boolean;
  lastLogin: string;
  status: 'active' | 'inactive';
  createdAt: string;
}
```

**Tenant User Overview data:**

```tsx
// GET /api/platform/users/tenant-overview
interface TenantUserSummary {
  tenantId: string;
  tenantName: string;
  totalUsers: number;
  activeUsers: number;
  licensedUsers: number;     // From subscription tier
  utilizationPercent: number; // activeUsers / licensedUsers
  adminCount: number;
  lastUserActivity: string;
}
```

This screen is read-only for Super Admin. Actual user management (create, edit roles, deactivate) within a tenant is the Company Admin's responsibility. Super Admin can see aggregated stats and license utilization but cannot modify tenant users directly.

---

### 14.6 Audit Log Flow

**Journey:** Super Admin investigates platform activity through the audit log viewer.

```
┌──────┐   More → Audit   ┌──────────────────────────────────────────┐
│ More │ ────────────────→ │ Audit Log Viewer                        │
│ Menu │                   │                                          │
└──────┘                   │ Filters:                                 │
                           │ • Date range picker (start–end)          │
                           │ • Actor (dropdown: all SA users)         │
                           │ • Action type (chip: Create, Update,     │
                           │   Delete, Login, Config, Module, Billing)│
                           │ • Entity type (chip: Tenant, Module,     │
                           │   Invoice, User, Setting, Announcement)  │
                           │ • Tenant (dropdown: all tenants or All)  │
                           │                                          │
                           │ Each log entry (expandable):             │
                           │ ┌──────────────────────────────────────┐ │
                           │ │ [timestamp] Actor performed Action   │ │
                           │ │ on EntityType "EntityName"           │ │
                           │ │ ▼ Expand for details                │ │
                           │ │   Old value: { ... }                │ │
                           │ │   New value: { ... }                │ │
                           │ │   IP: 192.168.1.1                   │ │
                           │ │   User-Agent: ...                   │ │
                           │ └──────────────────────────────────────┘ │
                           └──────────────────────────────────────────┘
```

**Audit log entry type:**

```tsx
interface AuditLogEntry {
  id: string;
  timestamp: string;
  actor: {
    id: string;
    name: string;
    email: string;
    role: string;
  };
  action: 'create' | 'update' | 'delete' | 'login' | 'logout' | 'activate' | 'deactivate'
        | 'assign' | 'revoke' | 'generate' | 'void' | 'export' | 'config_change';
  entityType: 'tenant' | 'module' | 'invoice' | 'payment' | 'user' | 'setting'
            | 'announcement' | 'ticket' | 'integration';
  entityId: string;
  entityName: string;
  tenantId: string | null;   // null for platform-level actions
  tenantName: string | null;
  changes: {
    field: string;
    oldValue: unknown;
    newValue: unknown;
  }[] | null;
  metadata: {
    ipAddress: string;
    userAgent: string;
    requestId: string;
  };
}
```

**API call:**

```tsx
const { data, fetchNextPage, hasNextPage } = useInfiniteQuery({
  queryKey: ['audit-logs', filters],
  queryFn: ({ pageParam = 1 }) =>
    apiClient.get('/api/platform/audit-logs', {
      params: {
        page: pageParam,
        limit: 50,
        ...filters,
      },
    }),
  getNextPageParam: (lastPage) =>
    lastPage.hasMore ? lastPage.page + 1 : undefined,
});
```

Audit logs are append-only and immutable. They cannot be edited or deleted by anyone, including Super Admin.

---

### 14.7 Backend API Integration Pattern

All Super Admin screens follow a consistent pattern for server communication:

**React Query for server state:**

```tsx
// READ: useQuery for all GET requests
const { data, isLoading, isError, error, refetch } = useQuery({
  queryKey: ['tenants', filters],
  queryFn: () => apiClient.get('/api/platform/tenants', { params: filters }),
  staleTime: 30_000,        // 30 seconds before refetch
  gcTime: 5 * 60_000,       // 5 minutes cache lifetime
  refetchOnWindowFocus: true,
});

// WRITE: useMutation for all POST/PATCH/DELETE requests
const mutation = useMutation({
  mutationFn: (payload) => apiClient.patch(`/api/platform/tenants/${id}`, payload),

  // Optimistic update for instant UI feedback
  onMutate: async (payload) => {
    await queryClient.cancelQueries({ queryKey: ['tenant', id] });
    const previous = queryClient.getQueryData(['tenant', id]);
    queryClient.setQueryData(['tenant', id], (old) => ({ ...old, ...payload }));
    return { previous };
  },

  // Rollback on error
  onError: (err, payload, context) => {
    queryClient.setQueryData(['tenant', id], context?.previous);
  },

  // Always refetch after mutation to ensure consistency
  onSettled: () => {
    queryClient.invalidateQueries({ queryKey: ['tenant', id] });
    queryClient.invalidateQueries({ queryKey: ['tenants'] });
    queryClient.invalidateQueries({ queryKey: ['dashboard'] });
  },
});
```

**Zustand for local UI state:**

```tsx
// src/features/super-admin/hooks/useSuperAdminStore.ts
import { create } from 'zustand';

interface SuperAdminUIState {
  // Company List filters
  companyFilters: {
    search: string;
    status: string[];
    sortBy: 'name' | 'createdAt' | 'mrr' | 'healthScore';
    sortOrder: 'asc' | 'desc';
  };
  setCompanyFilters: (filters: Partial<SuperAdminUIState['companyFilters']>) => void;

  // Audit Log filters
  auditFilters: AuditFilter;
  setAuditFilters: (filters: Partial<AuditFilter>) => void;

  // Dashboard date range
  dashboardDateRange: { start: string; end: string };
  setDashboardDateRange: (range: { start: string; end: string }) => void;
}

export const useSuperAdminStore = create<SuperAdminUIState>((set) => ({
  companyFilters: {
    search: '',
    status: [],
    sortBy: 'name',
    sortOrder: 'asc',
  },
  setCompanyFilters: (filters) =>
    set((state) => ({
      companyFilters: { ...state.companyFilters, ...filters },
    })),
  // ... other slices
}));
```

**MMKV for persistent local storage:**

```tsx
import { MMKV } from 'react-native-mmkv';

const storage = new MMKV();

// Auth tokens (persisted across app restarts)
storage.set('auth.accessToken', token);
storage.set('auth.refreshToken', refreshToken);

// Cached settings (reduce initial load time)
storage.set('cache.platformSettings', JSON.stringify(settings));

// User preferences
storage.set('pref.dashboardLayout', 'compact');
storage.set('pref.defaultDateRange', '30d');
```

**API client setup:**

```tsx
// src/lib/api-client.ts
import axios from 'axios';
import { MMKV } from 'react-native-mmkv';

const storage = new MMKV();

const apiClient = axios.create({
  baseURL: process.env.EXPO_PUBLIC_API_URL,
  timeout: 15_000,
  headers: { 'Content-Type': 'application/json' },
});

// Attach JWT to every request
apiClient.interceptors.request.use((config) => {
  const token = storage.getString('auth.accessToken');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Handle 401 → refresh token → retry
apiClient.interceptors.response.use(
  (response) => response.data,
  async (error) => {
    if (error.response?.status === 401) {
      const refreshed = await refreshAccessToken();
      if (refreshed) {
        error.config.headers.Authorization = `Bearer ${refreshed}`;
        return apiClient(error.config);
      }
      // Refresh failed → force logout
      useAuthStore.getState().logout();
    }
    return Promise.reject(error);
  }
);
```

**Query key conventions:**

| Resource | Query Key | Invalidated By |
|----------|-----------|----------------|
| Dashboard data | `['dashboard', dateRange]` | Tenant create/update, invoice, payment |
| Tenant list | `['tenants', filters]` | Tenant create/update/delete |
| Single tenant | `['tenant', id]` | Tenant update, module assign/revoke |
| Tenant billing | `['tenant-billing', tenantId]` | Invoice generate, payment record |
| Invoice list | `['invoices', filters]` | Invoice generate/void/payment |
| Revenue metrics | `['revenue', dateRange]` | Invoice, payment |
| Module catalogue | `['modules']` | Module create/update |
| Platform users | `['platform-users']` | User create/update/delete |
| Audit logs | `['audit-logs', filters]` | Never invalidated (append-only) |
| Announcements | `['announcements']` | Announcement create/update/delete |
| Support tickets | `['tickets', filters]` | Ticket create/update |
| Platform settings | `['platform-settings']` | Setting update |

---

### 14.8 Cross-Screen Data Dependencies

Some screens share data and must stay in sync:

```
Dashboard KPIs ←────── Tenant create/update
       ↑                      ↓
       ├──── Invoice generate/void
       ↑                      ↓
       ├──── Payment recorded
       ↑                      ↓
       └──── Module assign/revoke

Company List ←─────── Tenant status change
       ↑                      ↓
       └──── Onboarding completed

Company Detail ←───── Module assignment
       ↑                      ↓
       ├──── Subscription edit
       ↑                      ↓
       └──── User changes (from tenant admin)
```

All cross-screen sync is handled through React Query's `invalidateQueries`. When a mutation succeeds, it invalidates all related query keys so that any screen displaying that data will refetch on next render or focus.

---

## 15. Security & Access Control for Super Admin Panel

The Super Admin panel has the highest privilege level in the Avy ERP platform. Security is designed in layers: authentication proves identity, authorization enforces boundaries, audit logging provides accountability, and infrastructure controls limit attack surface.

---

### 15.1 Authentication

#### 15.1.1 Login Flow

```
┌──────────┐   email + password   ┌──────────┐   TOTP code   ┌──────────┐
│  Login   │ ───────────────────→ │  MFA     │ ────────────→ │  App     │
│  Screen  │                      │  Screen  │               │  (tabs)  │
└──────────┘                      └──────────┘               └──────────┘
      │                                │                          │
      │ POST /api/auth/login           │ POST /api/auth/mfa       │ JWT stored in MMKV
      │ Body: { email, password }      │ Body: { tempToken, code }│ Refresh token stored
      │ Response: { tempToken,         │ Response: {              │ in MMKV (encrypted)
      │   mfaRequired: true }          │   accessToken,           │
      │                                │   refreshToken,          │
      │ If mfaRequired=false           │   user, expiresIn        │
      │ (MFA not yet enabled):         │ }                        │
      │ → Force MFA setup flow         │                          │
```

#### 15.1.2 Token Management

| Token | Lifetime | Storage | Rotation |
|-------|----------|---------|----------|
| Access Token (JWT) | 15 minutes | MMKV `auth.accessToken` | Refreshed automatically via interceptor |
| Refresh Token | 7 days | MMKV `auth.refreshToken` | Rotated on each use (old one invalidated) |
| MFA Temp Token | 5 minutes | In-memory only (React state) | Single use, expires after MFA verification |

#### 15.1.3 JWT Claims (Access Token)

```json
{
  "sub": "user_abc123",
  "email": "admin@avyren.com",
  "name": "Chetan",
  "role": "super_admin",
  "permissions": ["platform:*"],
  "iat": 1711036800,
  "exp": 1711037700,
  "iss": "avy-erp-platform",
  "jti": "unique-token-id"
}
```

Note: No `tenant_id` claim. Super Admin tokens are platform-scoped, granting access across all tenants at the platform management level (not tenant data level).

#### 15.1.4 Session Management

- **Idle timeout:** Configurable, default 30 minutes. After 30 minutes of no API calls, the next request triggers a re-authentication prompt (not a full login — just MFA code re-entry if configured).
- **Absolute timeout:** 12 hours. After 12 hours, regardless of activity, the session expires and requires full re-login.
- **Concurrent sessions:** Configurable limit (default: 3 devices). New login on 4th device invalidates the oldest session.
- **Logout:** `POST /api/auth/logout` revokes the refresh token server-side. Client clears MMKV tokens.
- **Force logout:** Super Admin can force-logout other SA sessions via Platform Users screen.

#### 15.1.5 MFA Requirements

- MFA is mandatory for all Super Admin accounts. There is no option to disable it.
- Supported methods: TOTP (Google Authenticator, Authy, etc.)
- Backup codes: 10 single-use backup codes generated during MFA setup, stored hashed server-side.
- Recovery: If MFA device is lost, recovery requires identity verification by another Super Admin + backup code.

---

### 15.2 Authorization

#### 15.2.1 Middleware Chain

Every API request to the platform routes passes through this middleware chain:

```
Request → rateLimiter → ipWhitelist → authenticate → isSuperAdmin → route handler
                                          │
                                          ├── Verify JWT signature
                                          ├── Check token not expired
                                          ├── Check token not in revocation list
                                          └── Attach user to request

                                                        │
                                                        ├── Verify user.role === 'super_admin'
                                                        ├── Verify user.status === 'active'
                                                        └── Log access in audit trail
```

#### 15.2.2 Backend Middleware Implementation

```typescript
// middleware/isSuperAdmin.ts
export function isSuperAdmin(req: Request, res: Response, next: NextFunction) {
  const user = req.user; // Attached by authenticate middleware

  if (!user) {
    return res.status(401).json({ error: 'Authentication required' });
  }

  if (user.role !== 'super_admin') {
    // Log unauthorized access attempt
    auditLogger.warn('Unauthorized platform access attempt', {
      userId: user.id,
      role: user.role,
      path: req.path,
      ip: req.ip,
    });
    return res.status(403).json({ error: 'Insufficient permissions' });
  }

  if (user.status !== 'active') {
    return res.status(403).json({ error: 'Account deactivated' });
  }

  next();
}
```

#### 15.2.3 Platform Roles

Super Admin is not a single monolithic role. There are sub-roles for granular access:

| Role | Scope | Can Manage Tenants | Can Manage Billing | Can Manage Platform Users | Can View Audit |
|------|-------|--------------------|--------------------|--------------------------|----------------|
| `super_admin` | Full platform access | Yes (CRUD) | Yes (CRUD) | Yes (CRUD) | Yes |
| `platform_support` | Read + limited write | Read + support access | Read only | No | Yes (read only) |
| `platform_viewer` | Read only | Read only | Read only | No | Yes (read only) |

The mobile app adapts its UI based on role:
- `super_admin`: All screens, all actions, FABs visible, edit buttons shown
- `platform_support`: All screens visible, destructive actions hidden, support access grant button shown
- `platform_viewer`: All screens visible, all write actions hidden, export buttons shown

---

### 15.3 Access Boundaries

#### 15.3.1 What Super Admin CAN Do

| Domain | Allowed Actions |
|--------|----------------|
| Tenant Management | Create, configure, activate, deactivate, suspend tenants |
| Module Management | View catalogue, assign/revoke modules, manage dependencies, set pricing |
| Billing | Generate invoices, record payments, void invoices, manage subscriptions |
| Platform Users | Create/edit/deactivate other Super Admin accounts |
| Tenant Users | View aggregated user counts and license utilization (read-only) |
| Audit | View all platform-level audit logs |
| Settings | Configure platform defaults, integrations, notification templates, security policies |
| Support | View/respond to support tickets, send system announcements |
| Analytics | View all platform-level analytics and reports |

#### 15.3.2 What Super Admin CANNOT Do (by default)

| Restriction | Rationale |
|-------------|-----------|
| Read tenant business data (employees, payroll, production, sales orders, etc.) | Data sovereignty — tenant data belongs to the tenant |
| Modify tenant user accounts (create, edit roles, reset passwords) | Company Admin's responsibility — separation of duties |
| Access tenant's module screens (e.g., open Manufacturing module as a tenant user) | Super Admin manages the platform, not tenant operations |
| Delete audit logs or modify audit entries | Audit trail integrity — append-only by design |
| Bypass MFA or disable it for their own account | Security policy — MFA is mandatory for platform admins |
| Access raw database or run arbitrary queries | All access is through controlled API endpoints |

#### 15.3.3 Temporary Support Access

When a tenant needs help and the Super Admin must view tenant-level data for support purposes:

```
┌──────────────┐   Request Access   ┌──────────────────┐
│ Company      │ ────────────────→ │ Support Access    │
│ Detail       │                    │ Grant Modal       │
│              │                    │                   │
│              │                    │ • Reason (req'd)  │
│              │                    │ • Duration: 1h/4h │
│              │                    │   /24h/custom     │
│              │                    │ • Access level:   │
│              │                    │   read-only       │
│              │                    │ • Modules to      │
│              │                    │   access (select) │
│              │                    │                   │
│              │   ConfirmModal     │ [Grant Access]    │
│              │ ←──────────────── │                   │
└──────────────┘                    └──────────────────┘
```

**Support access rules:**
- Always read-only (never write access to tenant data)
- Always time-limited (auto-expires, cannot be permanent)
- Always scoped to specific modules (not blanket access)
- Always requires a documented reason
- Always logged in audit trail (grant event, every access during grant, expiry event)
- Tenant Admin receives notification when support access is granted
- Can be revoked early by either Super Admin or Tenant Admin

**API:**

```typescript
// POST /api/platform/tenants/:id/support-access
{
  reason: "Investigating payroll calculation discrepancy reported in ticket #1234",
  duration: "4h",           // Auto-expires after 4 hours
  accessLevel: "read_only",
  moduleScope: ["payroll", "hr"],
}

// Response includes temporary scoped token
{
  supportAccessId: "sa_xyz789",
  expiresAt: "2026-03-18T20:00:00Z",
  tenantId: "tenant_abc123",
  moduleScope: ["payroll", "hr"],
}
```

---

### 15.4 Security Measures

#### 15.4.1 Transport Security

- All API communication over HTTPS with TLS 1.3 minimum
- HSTS (HTTP Strict Transport Security) headers enforced
- Certificate pinning on the mobile app for the API domain
- No downgrade to HTTP permitted

#### 15.4.2 IP Whitelisting

Super Admin panel access can be restricted to specific IP addresses or CIDR ranges:

```typescript
// Configured in Platform Settings → Security
{
  ipWhitelist: {
    enabled: true,
    allowedIPs: [
      "203.0.113.0/24",     // Office network
      "198.51.100.50",      // VPN exit
    ],
    bypassForMFA: false,    // If true, allows any IP if MFA is valid
  }
}
```

When enabled, requests from non-whitelisted IPs receive `403 Forbidden` even with a valid JWT. The mobile app shows a clear error: "Access denied. Your network is not authorized for platform administration."

#### 15.4.3 Rate Limiting

| Endpoint Category | Rate Limit | Window |
|-------------------|-----------|--------|
| `POST /api/auth/login` | 5 requests | 15 minutes (per IP) |
| `POST /api/auth/mfa` | 5 requests | 15 minutes (per IP) |
| `GET /api/platform/*` | 100 requests | 1 minute (per user) |
| `POST/PATCH/DELETE /api/platform/*` | 30 requests | 1 minute (per user) |
| `POST /api/platform/tenants` (create tenant) | 10 requests | 1 hour (per user) |
| `POST /api/platform/invoices/generate` | 20 requests | 1 hour (per user) |

Rate limit headers included in every response:

```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 87
X-RateLimit-Reset: 1711037760
```

Mobile app displays a friendly message when rate-limited: "You're making requests too quickly. Please wait a moment and try again."

#### 15.4.4 Sensitive Field Handling

All sensitive fields in the mobile app use the `SecretInput` atom:

| Field | Screen | Masked By Default | Copy Disabled |
|-------|--------|-------------------|---------------|
| API keys (RazorpayX, payment gateway) | Onboarding Step 5, Integration Settings | Yes | Yes |
| Webhook secrets | Integration Settings | Yes | Yes |
| Database connection strings | Backend Endpoint config | Yes | Yes |
| SMTP passwords | Notification Settings | Yes | Yes |
| Backup codes | MFA Setup | Yes (tap to reveal briefly) | No (user needs to copy) |

`SecretInput` component behavior:
- Renders `***••••••***` by default
- Eye icon toggles visibility
- Auto-hides after 10 seconds of visibility
- `secureTextEntry` on the TextInput prevents screen recording / screenshot capture (on supported OS versions)

#### 15.4.5 Audit Trail Coverage

Every Super Admin action generates an audit log entry. The following events are logged:

| Category | Events Logged |
|----------|--------------|
| Authentication | Login success, login failure, MFA success, MFA failure, logout, session expired, force logout |
| Tenant Management | Create, update config, activate, deactivate, suspend, resume, delete draft |
| Module Management | Assign module, revoke module, update pricing, create module, deprecate module |
| Billing | Generate invoice, void invoice, record payment, edit subscription, change tier |
| User Management | Create SA user, update SA role, deactivate SA user, reset MFA |
| Settings | Update platform setting, update integration config, update notification template |
| Support | Grant support access, revoke support access, create announcement, update ticket |
| Data Access | View tenant data (during support access), export data |

Each audit entry includes: timestamp, actor (user ID + name + email), action, entity type, entity ID, entity name, tenant ID (if applicable), detailed changes (old value vs new value), IP address, user agent, and request ID for correlation.

#### 15.4.6 Data Isolation

Tenant data isolation is enforced at every layer:

```
┌─────────────────────────────────────────────────┐
│ Application Layer                                │
│ • Every query includes tenant_id filter           │
│ • No cross-tenant JOINs without explicit scope   │
│ • Super Admin API never returns tenant biz data  │
├─────────────────────────────────────────────────┤
│ Database Layer                                   │
│ • Row-Level Security (RLS) policies in Postgres  │
│ • tenant_id column on every tenant-scoped table  │
│ • RLS policy: current_setting('app.tenant_id')   │
│   matches row tenant_id                          │
├─────────────────────────────────────────────────┤
│ API Layer                                        │
│ • Platform routes (/api/platform/*) return       │
│   only platform-level aggregated data            │
│ • Tenant routes (/api/tenant/*) set              │
│   app.tenant_id session variable                 │
│ • No endpoint returns raw data from multiple     │
│   tenants in a single response                   │
└─────────────────────────────────────────────────┘
```

#### 15.4.7 Mobile-Specific Security

| Measure | Implementation |
|---------|---------------|
| Biometric lock | Optional app-level biometric (Face ID / fingerprint) on re-open after background |
| Screen capture prevention | `FLAG_SECURE` on Android, `UIScreen.capturedDidChangeNotification` on iOS for sensitive screens |
| Jailbreak/root detection | Warning shown on compromised devices (not blocked — configurable) |
| App transport security | iOS ATS enforced, Android network security config restricts cleartext |
| Token storage | MMKV with encryption key stored in iOS Keychain / Android Keystore |
| Clipboard timeout | Sensitive data copied to clipboard auto-clears after 60 seconds |
| Deep link validation | All deep links validated against route whitelist before navigation |

---

## 16. Implementation Roadmap & Priorities

This roadmap sequences the Super Admin panel build-out into five phases, each building on the previous. Phases are designed so that each delivers a usable, deployable increment.

---

### 16.1 Phase 1 — Core Platform (MVP)

**Goal:** Minimum viable Super Admin experience — can onboard tenants, assign modules, and manage the platform.

**Timeline:** Weeks 1–6

**Screens & Features:**

| Screen | Feature File | Status | Priority |
|--------|-------------|--------|----------|
| Login + MFA | `auth/login-screen.tsx`, `auth/mfa-screen.tsx` | New | P0 |
| Platform Overview Dashboard | `super-admin/dashboard-screen.tsx` | Exists (enhance) | P0 |
| Company List | `super-admin/company-list-screen.tsx` | Exists (enhance) | P0 |
| Company Detail (tabbed) | `super-admin/company-detail-screen.tsx` | Exists (enhance) | P0 |
| 16-Step Onboarding Wizard | `super-admin/tenant-onboarding/` | Exists (complete) | P0 |
| Module Assignment | `super-admin/module-assignment-screen.tsx` | Exists (enhance) | P0 |
| More Menu | `super-admin/more-menu-screen.tsx` | Exists | P1 |
| Platform Settings (basic) | `super-admin/settings/platform-settings-screen.tsx` | New | P1 |
| Basic Audit Log | `super-admin/audit-log-screen.tsx` | New | P1 |
| Sidebar + Tab Navigation | `components/ui/sidebar.tsx`, `app/(app)/_layout.tsx` | Exists | P0 |

**Backend API Endpoints (Phase 1):**

```
POST   /api/auth/login
POST   /api/auth/mfa
POST   /api/auth/refresh
POST   /api/auth/logout

GET    /api/platform/dashboard
GET    /api/platform/tenants
GET    /api/platform/tenants/:id
POST   /api/platform/tenants                    # Create (from wizard)
PATCH  /api/platform/tenants/:id                # Update config
PATCH  /api/platform/tenants/:id/status         # Activate/deactivate
POST   /api/platform/tenants/drafts             # Save wizard draft
GET    /api/platform/tenants/drafts/:id         # Resume wizard draft

GET    /api/platform/modules                     # Module catalogue
PATCH  /api/platform/tenants/:id/modules         # Assign/revoke modules

GET    /api/platform/audit-logs                  # Basic audit log
GET    /api/platform/settings                    # Platform settings
PATCH  /api/platform/settings                    # Update settings
```

**Infrastructure:**
- PostgreSQL schema: `platform` schema for platform-level tables (tenants, modules, audit_logs, platform_users, settings)
- JWT signing with RS256 (asymmetric keys)
- Redis for refresh token storage and rate limiting
- Basic RLS policies on tenant-scoped tables

**Acceptance Criteria:**
- [ ] Super Admin can log in with email + password + MFA
- [ ] Dashboard shows: total tenants, active tenants, total MRR, recent activity
- [ ] Company List loads with search, filter by status, sort by name/date
- [ ] Tapping a company opens the Detail screen with Overview tab populated
- [ ] Onboarding wizard completes all 16 steps and creates a tenant via API
- [ ] Module assignment screen shows all modules with toggle, dependency warnings shown
- [ ] Audit log captures: login, tenant create, tenant update, module assign/revoke
- [ ] JWT refresh works transparently (user never sees unexpected logouts within session)
- [ ] All destructive actions use ConfirmModal (zero Alert.alert calls)
- [ ] Sidebar navigation works from every screen

---

### 16.2 Phase 2 — Billing & Subscription Management

**Goal:** Full billing lifecycle — subscriptions, invoices, payments, and revenue visibility.

**Timeline:** Weeks 7–10

**Screens & Features:**

| Screen | Feature File | Priority |
|--------|-------------|----------|
| Billing Overview | `super-admin/billing-overview-screen.tsx` | P0 |
| Invoice Management | `super-admin/invoice-management-screen.tsx` | P0 |
| Invoice Detail | `super-admin/invoice-detail-screen.tsx` | P0 |
| Payment History | `super-admin/payment-history-screen.tsx` | P1 |
| Revenue Dashboard | `super-admin/revenue-dashboard-screen.tsx` | P1 |
| Edit Subscription | Route: `tenant/edit-subscription.tsx` | P0 |
| Company Detail — Billing Tab | Enhancement to existing | P0 |

**Backend API Endpoints (Phase 2):**

```
GET    /api/platform/billing/overview            # Aggregated billing metrics
GET    /api/platform/billing/revenue             # Revenue breakdown (MRR, ARR, trend)

GET    /api/platform/invoices                    # All invoices (paginated, filterable)
GET    /api/platform/invoices/:id                # Single invoice detail
POST   /api/platform/invoices/generate           # Generate invoice for tenant
PATCH  /api/platform/invoices/:id/void           # Void an invoice

POST   /api/platform/invoices/:id/payments       # Record payment against invoice
GET    /api/platform/payments                    # All payments (paginated)

GET    /api/platform/tenants/:id/subscription    # Tenant subscription detail
PATCH  /api/platform/tenants/:id/subscription    # Update subscription (tier, cycle)
GET    /api/platform/tenants/:id/billing         # Tenant billing history
```

**Data Models:**

```typescript
interface Subscription {
  id: string;
  tenantId: string;
  tier: UserTierKey;                    // From USER_TIERS constant
  billingCycle: 'monthly' | 'quarterly' | 'annual';
  basePrice: number;                    // Per-user base price
  moduleAddOns: { moduleId: string; price: number }[];
  totalMRR: number;
  trialEndsAt: string | null;
  currentPeriodStart: string;
  currentPeriodEnd: string;
  status: 'active' | 'trial' | 'past_due' | 'cancelled';
  nextBillingDate: string;
}

interface Invoice {
  id: string;
  invoiceNumber: string;              // e.g., "INV-2026-0001"
  tenantId: string;
  tenantName: string;
  billingPeriod: { start: string; end: string };
  lineItems: {
    description: string;
    quantity: number;
    unitPrice: number;
    amount: number;
  }[];
  subtotal: number;
  taxRate: number;
  taxAmount: number;
  totalAmount: number;
  status: 'draft' | 'sent' | 'viewed' | 'paid' | 'overdue' | 'voided';
  dueDate: string;
  paidAt: string | null;
  payments: Payment[];
  createdAt: string;
}

interface Payment {
  id: string;
  invoiceId: string;
  amount: number;
  method: 'bank_transfer' | 'upi' | 'card' | 'cheque' | 'cash';
  reference: string;
  paidAt: string;
  recordedBy: string;
  notes: string;
}
```

**Acceptance Criteria:**
- [ ] Billing Overview shows: total MRR, ARR, outstanding amount, overdue count, revenue trend chart (30/90/365 days)
- [ ] Invoice list supports: search by tenant name or invoice number, filter by status (sent/paid/overdue/voided), sort by date/amount
- [ ] Generate Invoice creates correct line items from subscription + module add-ons + tax
- [ ] Record Payment updates invoice status to "paid" when fully paid, "partially paid" when partial
- [ ] Void Invoice requires ConfirmModal, updates status, logs in audit
- [ ] Revenue Dashboard shows: MRR trend, ARR, ARPU, revenue by tier, revenue by module
- [ ] Company Detail Billing tab shows subscription, invoices, payments for that tenant
- [ ] Edit Subscription screen allows tier change with prorated pricing preview

---

### 16.3 Phase 3 — Advanced Management & Analytics

**Goal:** Deeper platform visibility — module dependencies, cross-tenant insights, advanced audit, analytics.

**Timeline:** Weeks 11–15

**Screens & Features:**

| Screen | Feature File | Priority |
|--------|-------------|----------|
| Module Catalogue Management | `super-admin/module-catalogue-screen.tsx` | P0 |
| Module Detail | `super-admin/module-detail-screen.tsx` | P1 |
| Module Dependency Visualization | `super-admin/module-dependency-screen.tsx` | P1 |
| Cross-Tenant User Overview | `super-admin/tenant-user-overview-screen.tsx` | P1 |
| Advanced Audit Log | Enhancement to existing audit-log-screen | P0 |
| Platform Analytics Hub | `super-admin/platform-analytics-screen.tsx` | P1 |
| Tenant Health Report | `super-admin/tenant-health-screen.tsx` | P2 |
| Usage Analytics | `super-admin/usage-analytics-screen.tsx` | P2 |
| Growth Metrics | `super-admin/growth-metrics-screen.tsx` | P2 |

**Backend API Endpoints (Phase 3):**

```
GET    /api/platform/modules/:id                 # Module detail + adoption stats
POST   /api/platform/modules                     # Create new module
PATCH  /api/platform/modules/:id                 # Update module (price, description)
GET    /api/platform/modules/dependencies        # Full dependency graph

GET    /api/platform/users/tenant-overview       # Cross-tenant user summary
GET    /api/platform/tenants/:id/users           # Users in a specific tenant (summary)

GET    /api/platform/audit-logs                  # Enhanced: full filtering, export
GET    /api/platform/audit-logs/export           # CSV/JSON export

GET    /api/platform/analytics/overview          # Platform-wide KPIs
GET    /api/platform/analytics/tenant-health     # Health scores per tenant
GET    /api/platform/analytics/module-usage      # Module adoption + usage
GET    /api/platform/analytics/growth            # Acquisition, churn, expansion metrics

PATCH  /api/platform/tenants/:id/feature-toggles # Per-tenant feature flags
PATCH  /api/platform/tenants/:id/custom-pricing  # Custom pricing override
```

**Module Dependency Visualization:**

The dependency screen renders a directed graph showing module relationships. On mobile, this is implemented as an interactive tree layout (not a full graph library — too heavy). Each module is a node card; arrows show "depends on" relationships:

```
┌──────────────┐
│ Manufacturing │
│  ├── Quality Control (required)
│  ├── Inventory (required)
│  └── Maintenance (optional)
│
│ Payroll
│  ├── HR & Attendance (required)
│  └── Finance & Accounting (required)
│
│ Supply Chain
│  ├── Inventory (required)
│  └── Finance & Accounting (required)
└──────────────┘
```

**Analytics Data Points:**

| Metric | Source | Update Frequency |
|--------|--------|------------------|
| Total Tenants (by status) | `tenants` table | Real-time |
| MRR / ARR | `subscriptions` + `invoices` | Daily aggregation |
| ARPU (Average Revenue Per User) | MRR / total_active_users | Daily aggregation |
| Module Adoption Rate | `tenant_modules` / total_tenants | Real-time |
| Tenant Health Score | Composite: login frequency, module usage, payment timeliness | Daily calculation |
| Churn Rate | Tenants deactivated / total at period start | Monthly |
| Net Revenue Retention | (MRR at end - new MRR) / MRR at start | Monthly |
| License Utilization | active_users / licensed_users per tenant | Real-time |

**Acceptance Criteria:**
- [ ] Module Catalogue screen: list all modules, add new module, edit existing, deprecate (soft delete)
- [ ] Module Detail shows: description, price, dependency list, count of tenants using it, adoption trend
- [ ] Dependency screen renders tree view of all module dependencies
- [ ] Cross-Tenant User Overview: list all tenants with user counts, utilization bars, sortable
- [ ] Audit Log: filter by date range, actor, action, entity type, tenant; entries expandable with diff view
- [ ] Audit Log export: download filtered results as CSV
- [ ] Analytics Hub: KPI cards (tenants, MRR, ARPU, churn) + trend charts
- [ ] Tenant Health: color-coded list (green/amber/red health score) sortable by score
- [ ] Custom pricing: override standard tier pricing for specific tenants, logged in audit

---

### 16.4 Phase 4 — Communication & Support

**Goal:** Enable Super Admin to communicate with tenants and handle support cases.

**Timeline:** Weeks 16–19

**Screens & Features:**

| Screen | Feature File | Priority |
|--------|-------------|----------|
| Notification Template Management | `super-admin/settings/notification-templates-screen.tsx` | P0 |
| System Announcements | `super-admin/announcement-screen.tsx` | P0 |
| Support Ticket List | `super-admin/support-tickets-screen.tsx` | P1 |
| Ticket Detail / Thread | `super-admin/ticket-detail-screen.tsx` | P1 |
| Integration Settings | `super-admin/settings/integration-settings-screen.tsx` | P1 |
| Integration Detail | `super-admin/settings/integration-detail-screen.tsx` | P2 |

**Backend API Endpoints (Phase 4):**

```
GET    /api/platform/notifications/templates     # All templates
GET    /api/platform/notifications/templates/:id # Single template
POST   /api/platform/notifications/templates     # Create template
PATCH  /api/platform/notifications/templates/:id # Update template
POST   /api/platform/notifications/test          # Send test notification

GET    /api/platform/announcements               # All announcements
POST   /api/platform/announcements               # Create announcement
PATCH  /api/platform/announcements/:id           # Update / schedule
DELETE /api/platform/announcements/:id           # Delete draft announcement

GET    /api/platform/support/tickets             # All support tickets
GET    /api/platform/support/tickets/:id         # Ticket detail + messages
POST   /api/platform/support/tickets/:id/reply   # Reply to ticket
PATCH  /api/platform/support/tickets/:id/status  # Update ticket status

GET    /api/platform/integrations                # All integrations
GET    /api/platform/integrations/:id            # Integration detail
PATCH  /api/platform/integrations/:id/config     # Update integration config
POST   /api/platform/integrations/:id/test       # Test integration connection
```

**Notification Templates:**

Templates support variable interpolation for dynamic content:

```typescript
interface NotificationTemplate {
  id: string;
  name: string;                        // e.g., "Invoice Generated"
  channel: 'email' | 'sms' | 'push' | 'whatsapp';
  trigger: string;                     // e.g., "invoice.generated"
  subject: string;                     // For email: "Invoice {{invoiceNumber}} generated"
  body: string;                        // "Hi {{tenantAdmin}}, your invoice for {{period}}..."
  variables: string[];                 // ["invoiceNumber", "tenantAdmin", "period", "amount"]
  isActive: boolean;
  lastEditedAt: string;
  lastEditedBy: string;
}
```

**Announcements:**

```typescript
interface Announcement {
  id: string;
  title: string;
  body: string;                        // Markdown supported
  type: 'info' | 'warning' | 'maintenance' | 'feature' | 'urgent';
  audience: 'all_tenants' | 'specific_tenants' | 'specific_tiers';
  audienceFilter: {
    tenantIds?: string[];
    tiers?: UserTierKey[];
  };
  channels: ('in_app' | 'email' | 'push' | 'sms')[];
  status: 'draft' | 'scheduled' | 'sent' | 'cancelled';
  scheduledAt: string | null;
  sentAt: string | null;
  createdBy: string;
  readCount: number;
  totalRecipients: number;
}
```

**Support Ticket Flow:**

```
Tenant Admin                          Super Admin
    │                                      │
    │  Create ticket (from tenant app)     │
    ├─────────────────────────────────────→│
    │                                      │  Ticket appears in Support Tickets list
    │                                      │  Status: "open"
    │                                      │
    │      Reply / request info            │
    │←─────────────────────────────────────┤
    │                                      │
    │  Tenant responds                     │
    ├─────────────────────────────────────→│
    │                                      │
    │                                      │  Grant support access (if needed)
    │                                      │  → Investigate tenant data (read-only)
    │                                      │  → Resolve issue
    │                                      │
    │      Resolution message              │
    │←─────────────────────────────────────┤
    │                                      │  Status: "resolved"
    │                                      │
    │  Confirm resolution (or reopen)      │
    ├─────────────────────────────────────→│
    │                                      │  Status: "closed"
```

**Acceptance Criteria:**
- [ ] Notification Templates: list all templates, edit template content, preview with sample variables, send test
- [ ] Announcements: create draft, target specific tenants or tiers, schedule for future delivery, send immediately (ConfirmModal), view delivery stats
- [ ] Support Tickets: list with status filter (open/in-progress/resolved/closed), priority badges, unread indicator
- [ ] Ticket Detail: threaded conversation view, reply with text, attach images (via image picker), change status, link to grant support access
- [ ] Integration Settings: show all configured integrations (payment gateway, email provider, SMS provider), connection status indicator, test connection button
- [ ] Integration Detail: edit config fields (using SecretInput for keys/secrets), save, test, view last sync status

---

### 16.5 Phase 5 — Enterprise Features

**Goal:** Advanced platform administration for scale — security hardening, data management, system monitoring.

**Timeline:** Weeks 20–24

**Screens & Features:**

| Screen | Feature File | Priority |
|--------|-------------|----------|
| Security Settings | `super-admin/settings/security-settings-screen.tsx` | P0 |
| Platform Config | `super-admin/settings/platform-config-screen.tsx` | P1 |
| Platform Users (enhanced) | `super-admin/platform-users-screen.tsx` enhancement | P0 |
| Platform User Detail | `super-admin/platform-user-detail-screen.tsx` | P1 |
| System Health Monitor | New screen | P2 |

**Backend API Endpoints (Phase 5):**

```
GET    /api/platform/security                    # Security settings
PATCH  /api/platform/security                    # Update security config
GET    /api/platform/security/ip-whitelist       # IP whitelist entries
PATCH  /api/platform/security/ip-whitelist       # Update IP whitelist
GET    /api/platform/security/sessions           # Active sessions

POST   /api/platform/tenants/:id/support-access  # Grant support access
DELETE /api/platform/tenants/:id/support-access/:accessId # Revoke
GET    /api/platform/support-access/active       # All active support access grants

GET    /api/platform/tenants/:id/export          # Trigger data export
GET    /api/platform/tenants/:id/export/status   # Export job status
GET    /api/platform/tenants/:id/export/download # Download export

GET    /api/platform/health                      # System health (API, DB, Redis, queues)
GET    /api/platform/health/metrics              # Performance metrics

GET    /api/platform/users                       # Platform users (enhanced)
POST   /api/platform/users                       # Create platform user
PATCH  /api/platform/users/:id                   # Update platform user
PATCH  /api/platform/users/:id/mfa/reset         # Reset user's MFA
POST   /api/platform/users/:id/force-logout      # Force logout all sessions
```

**Security Settings Screen:**

```
┌─────────────────────────────────────┐
│  Gradient Header: Security          │
├─────────────────────────────────────┤
│                                     │
│  ┌─ Authentication ──────────────┐  │
│  │ MFA Enforcement: [Required ▼] │  │
│  │ Session Idle Timeout: [30m ▼] │  │
│  │ Max Sessions/User: [3]        │  │
│  │ Password Policy:              │  │
│  │   Min length: [12]            │  │
│  │   Require uppercase: [ON]     │  │
│  │   Require number: [ON]        │  │
│  │   Require special char: [ON]  │  │
│  └───────────────────────────────┘  │
│                                     │
│  ┌─ Network ─────────────────────┐  │
│  │ IP Whitelist: [Enabled ▼]     │  │
│  │ Allowed IPs:                  │  │
│  │   203.0.113.0/24  [✕]        │  │
│  │   198.51.100.50   [✕]        │  │
│  │   [+ Add IP]                  │  │
│  └───────────────────────────────┘  │
│                                     │
│  ┌─ Active Sessions ─────────────┐  │
│  │ admin@avyren.com              │  │
│  │   iPhone 15 Pro · Mumbai      │  │
│  │   Active now                  │  │
│  │                               │  │
│  │ ops@avyren.com                │  │
│  │   Chrome · Desktop · Pune     │  │
│  │   Last active 12m ago         │  │
│  │   [Force Logout]              │  │
│  └───────────────────────────────┘  │
│                                     │
└─────────────────────────────────────┘
```

**Tenant Data Export:**

Super Admin can trigger a full data export for a tenant (for migration, compliance, or offboarding). The export is asynchronous:

```
1. Super Admin requests export → POST /api/platform/tenants/:id/export
2. Backend queues export job → returns job ID
3. Mobile app polls status → GET /api/platform/tenants/:id/export/status
4. When complete → download link available for 24 hours
5. Export includes: all tenant config + business data in structured JSON/CSV
6. Export event logged in audit trail
```

**System Health Monitor:**

```typescript
interface SystemHealth {
  status: 'healthy' | 'degraded' | 'down';
  services: {
    api: { status: string; latencyMs: number; uptime: string };
    database: { status: string; connectionPool: { active: number; idle: number; max: number } };
    redis: { status: string; memoryUsageMB: number };
    queue: { status: string; pendingJobs: number; failedJobs: number };
    storage: { status: string; usedGB: number; totalGB: number };
  };
  lastChecked: string;
}
```

**Acceptance Criteria:**
- [ ] Security Settings: all authentication policies editable, IP whitelist CRUD, active session list with force logout
- [ ] IP whitelist: adding/removing IPs requires ConfirmModal, changes logged in audit
- [ ] Platform Users: full CRUD for SA accounts, role assignment (super_admin / platform_support / platform_viewer), MFA reset (with ConfirmModal)
- [ ] Support Access: grant time-limited read-only access to tenant data, auto-expiry works, tenant admin notified, audit logged
- [ ] Data Export: trigger export, show progress, download when complete, export logged in audit
- [ ] System Health: real-time status of all backend services, latency metrics, alert indicators for degraded/down
- [ ] All new features have corresponding audit log entries
- [ ] All sensitive config changes require ConfirmModal confirmation
- [ ] Rate limiting dashboard: view current limits, see top consumers (future — can defer)

---

### 16.6 Acceptance Criteria — Cross-Phase Requirements

These criteria apply to every phase and must be verified continuously:

#### 16.6.1 Quality Standards

- [ ] **Zero `Alert.alert()` calls** — all confirmations and notifications use `ConfirmModal` or toast
- [ ] **All imports use `@/` prefix** — no relative imports anywhere
- [ ] **`font-inter` on all `Text` components** — consistent typography
- [ ] **Safe area handling** — `useSafeAreaInsets()` applied on all screens
- [ ] **Loading states** — every screen shows skeleton loader while fetching data
- [ ] **Error states** — every screen shows error message + retry button on API failure
- [ ] **Empty states** — every list screen shows meaningful empty state with action button
- [ ] **Pull-to-refresh** — every list screen supports pull-to-refresh via `RefreshControl`
- [ ] **Pagination** — every list screen with potentially >20 items uses infinite scroll
- [ ] **Animations** — `FadeInDown` for list items, `FadeInUp` for page content, `SlideInRight` for navigation

#### 16.6.2 Security Standards

- [ ] **Audit trail** — every create, update, delete, and status change action generates an audit entry
- [ ] **ConfirmModal for destructive actions** — deactivate, delete, void, revoke, force logout
- [ ] **SecretInput for sensitive fields** — API keys, passwords, webhook secrets, connection strings
- [ ] **JWT validation** — every API call checked for valid, non-expired, non-revoked token
- [ ] **Rate limiting** — all endpoints rate-limited per the policy in Section 15.4.3
- [ ] **No cross-tenant data leakage** — verify with automated tests that no endpoint returns another tenant's business data

#### 16.6.3 Performance Targets

| Metric | Target | Measurement |
|--------|--------|-------------|
| Screen load (cached) | < 200ms | Time from navigation to content visible |
| Screen load (network) | < 1.5s | Time from navigation to data rendered |
| List scroll | 60 FPS | No frame drops during FlatList scroll |
| Wizard navigation | < 100ms | Step transition with validation |
| Search debounce | 300ms | Delay before API call on keystroke |
| App cold start | < 3s | Splash screen to interactive dashboard |
| API response (p95) | < 500ms | Backend response time (95th percentile) |

#### 16.6.4 Testing Requirements Per Phase

| Test Type | Coverage Target | Tool |
|-----------|----------------|------|
| Unit tests (utilities, validators, formatters) | 90%+ | Jest |
| Component tests (atoms, section cards) | 80%+ | React Native Testing Library |
| Hook tests (React Query hooks, Zustand stores) | 90%+ | Jest + MSW (Mock Service Worker) |
| Integration tests (screen-level flows) | Key flows per phase | Detox or Maestro |
| API contract tests | All endpoints | Supertest + Zod schema validation |
| Security tests | Auth, authorization, rate limiting | Manual + automated |

#### 16.6.5 Definition of Done (Per Screen)

A screen is considered "done" when:

1. **Functional:** All user interactions work as specified (tap, scroll, search, filter, submit)
2. **Data:** Connected to real API endpoints (not mock data), React Query configured with appropriate stale/cache times
3. **Validation:** All form inputs validated with Zod, errors displayed inline via atom `error` props
4. **States:** Loading skeleton, error with retry, empty state, populated state — all four handled
5. **Navigation:** Correct back behavior, deep link support, sidebar item highlights correctly
6. **Security:** Destructive actions guarded by ConfirmModal, sensitive fields use SecretInput, audit logged
7. **Accessibility:** All touchable areas minimum 44x44pt, labels on inputs, screen reader compatible
8. **Performance:** No unnecessary re-renders (verified with React DevTools), lists use `keyExtractor` and `getItemLayout` where possible
9. **Code:** TypeScript strict mode, no `any` types, feature file exports named export, route file re-exports as default
10. **Reviewed:** Code reviewed by at least one other developer, no lint warnings

---

### 16.7 Phase Summary Timeline

```
Week  1 ─── 6    Phase 1: Core Platform (MVP)
                  ✓ Auth, Dashboard, Companies, Onboarding, Modules, Basic Audit
                  → Deliverable: Super Admin can onboard and manage tenants

Week  7 ─── 10   Phase 2: Billing & Subscription
                  ✓ Invoices, Payments, Revenue, Subscription Management
                  → Deliverable: Full billing lifecycle operational

Week 11 ─── 15   Phase 3: Advanced Management & Analytics
                  ✓ Module Catalogue, Dependencies, Analytics, Advanced Audit, Cross-Tenant Users
                  → Deliverable: Deep platform visibility and advanced module management

Week 16 ─── 19   Phase 4: Communication & Support
                  ✓ Notifications, Announcements, Support Tickets, Integrations
                  → Deliverable: Tenant communication and support workflows

Week 20 ─── 24   Phase 5: Enterprise Features
                  ✓ Security Hardening, Data Export, System Monitoring, Platform Users (full)
                  → Deliverable: Enterprise-grade platform administration
```

Each phase ends with a stakeholder review and sign-off before proceeding to the next. Phases can overlap by 1 week if the previous phase's acceptance criteria are substantially met (>90% of checkboxes).

---

*Document End — Avy ERP Super Admin Panel Complete Reference v1.0*
*Maintained by Avyren Technologies — Product & Platform Team*
