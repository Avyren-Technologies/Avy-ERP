# Avy ERP — Master Product Requirements Document
## Part 2: Platform Capabilities — Access Control, Subscriptions, Offline Architecture & Non-Functional Requirements

> **Product:** Avy ERP
> **Company:** Avyren Technologies
> **Document Series:** PRD-002 of 5
> **Version:** 2.0
> **Date:** April 2026
> **Status:** Final Draft · Confidential
> **Scope:** RBAC, Feature Toggles, Subscription Model, Offline-First Design, Analytics & Reporting, Platform Interfaces, Integration Strategy, and Non-Functional Requirements

---

## Table of Contents

1. [Role-Based Access Control (RBAC)](#1-role-based-access-control-rbac)
2. [Feature Toggles](#2-feature-toggles)
3. [Subscription & Pricing Model](#3-subscription--pricing-model)
4. [Module Catalogue & Dependencies](#4-module-catalogue--dependencies)
5. [Offline-First Architecture](#5-offline-first-architecture)
6. [Analytics & Reporting](#6-analytics--reporting)
7. [Platform Interfaces](#7-platform-interfaces)
8. [Integration Strategy](#8-integration-strategy)
9. [Non-Functional Requirements](#9-non-functional-requirements)
10. [Bulk Data Management](#10-bulk-data-management)

---

## 1. Role-Based Access Control (RBAC)

### 1.1 RBAC Model Overview

Avy ERP enforces a **hierarchical, tenant-scoped RBAC model**. Every screen, data record, API endpoint, and user action is protected by permission checks. Permissions are checked at the API layer — not just in the user interface — meaning no bypass through direct API calls is possible.

### 1.2 Role Hierarchy

The system has a fixed, two-level platform hierarchy:

```
Super Admin (Platform Level — Avyren Technologies)
  └── Company Admin (Tenant Level — per subscribing company)
        └── Custom Roles (defined by Company Admin)
              └── Users (assigned to one or more roles)
```

**Super Admin** — Global, cross-tenant access. Can create, configure, suspend, and delete any tenant. Can view billing and usage across all tenants. Cannot access tenant business data unless explicitly granted for support purposes.

**Company Admin** — Full access within their own tenant only. Can create unlimited custom roles and assign them to users. Can configure tenant-wide settings. Cannot access other tenants.

**Custom Roles** — Defined entirely by the Company Admin. The platform provides a reference set of common roles to accelerate setup, but these are templates — any role can be modified, cloned, or replaced.

### 1.3 Reference Role Templates

The following reference roles are pre-configured as starting templates and can be freely modified:

| Reference Role | Default Module Access |
|---|---|
| General Manager | Multi-module read access + all dashboards |
| Plant Manager | Plant-scoped operational modules |
| HR Personnel | Full HR module |
| Finance Team | Finance module + read-only payroll |
| Production Manager | Production + Machine Maintenance |
| Maintenance Technician | Machine Maintenance module |
| Sales Executive | Sales & Invoicing module |
| Security Personnel | Security + Visitor Management |
| Stores Clerk | Inventory module |
| Quality Inspector | Production NC entry + Quality module + reports |
| Auditor | Read-only access across all active modules |
| Viewer | Read-only, scope configurable |

These are reference configurations. A Company Admin may create roles with any combination of permissions.

### 1.4 Permission Granularity

Each role is configured with permissions at two levels:

**Module Level** — Whether the role can access the module at all.

**Action Level** — Within an accessible module, which actions are permitted:

| Action | Description |
|---|---|
| **View** | Read list screens and detail records |
| **Create** | Submit new records |
| **Edit** | Modify existing records |
| **Delete** | Remove records (usually restricted to admins) |
| **Approve** | Approve leave requests, POs, production records, etc. |
| **Export** | Download data in PDF or Excel format |
| **Configure** | Access settings, masters, and configuration screens |

**Field-Level Permissions (HRMS):** In the HR module, specific sensitive fields (e.g., salary details, bank account numbers) can be restricted on a field-by-field basis within a role. A manager can view an employee's profile without seeing their salary band.

### 1.5 RBAC Enforcement

RBAC is enforced at multiple levels:

- **API Layer** — Every endpoint checks `permissions[]` from the JWT before processing the request; no bypass is possible through direct API calls
- **UI Layer** — Menu items, buttons, and screens invisible or disabled based on role (defence-in-depth; not the primary enforcement layer)
- **Data Layer** — Plant-scoped roles can only read/write records tagged to their assigned plant(s)

### 1.6 Access Differentiation: Super Admin vs Company Admin

| Capability | Super Admin | Company Admin |
|---|---|---|
| View all companies | Yes | No (own company only) |
| Add a new company / tenant | Yes | No |
| Delete a company | Yes | No |
| Edit company general info | Yes (full) | Read-only |
| Edit time management settings | Yes | Yes |
| Edit system controls | Yes | Yes |
| Add users | Yes (any company) | Yes (own company only) |
| Change company status | Yes | No |
| Configure modules | Yes | Yes (within subscription) |

---

## 2. Feature Toggles

### 2.1 Purpose

Feature Toggles are user-level permission overrides that operate independently of the user's assigned role. They solve the problem where two users share the same role (e.g., both are "Production Manager") but have different specific responsibilities that require slightly different access.

### 2.2 How Feature Toggles Work

A Feature Toggle can either **grant additional access** that the role does not normally have, or **restrict default access** that the role would normally grant.

Example: Two users are both Production Managers. User A also handles incentive review, so they receive a Feature Toggle granting access to the Payroll module's incentive reporting view — a screen their role normally doesn't show. User B does not receive this toggle and sees only standard production screens.

Feature Toggles are configured per-user from the User Management screen. The interface presents a checklist of available features per module, shown alongside the user's current role permissions for clarity. Changes take effect on the user's next session or within a short propagation window (typically under 60 seconds).

### 2.3 Toggle Scope

Feature Toggles are available for every module and for cross-module data views. Common uses:

- Grant a non-HR role access to read-only payroll summaries
- Restrict a manager from deleting records even though their role permits it
- Allow a senior technician to configure PM schedules without being a full admin
- Enable a sales executive to see purchase orders (read-only) for coordination purposes

---

## 3. Subscription & Pricing Model

### 3.1 Pricing Dimensions

Avy ERP pricing is built on two independent dimensions that combine to form the total subscription cost:

1. **Module Cost** — Each module has its own individual price (monthly or annual billing)
2. **User Tier Cost** — Pricing is tiered by the number of active users in the tenant

### 3.2 User Tiers

| Tier | User Range | Description |
|---|---|---|
| **Starter** | 50 – 100 users | Entry tier for small factories |
| **Growth** | 101 – 200 users | Mid-sized operations |
| **Scale** | 201 – 500 users | Multi-shift, multi-line facilities |
| **Enterprise** | 501 – 1,000 users | Large manufacturing complexes |
| **Custom** | 1,000+ users | Negotiated directly with Avyren |

If a tenant's active user count crosses its subscribed tier's ceiling, additional billing applies automatically and the Company Admin is notified with options to upgrade their tier.

### 3.3 Billing Cycles

- **Monthly Billing** — Charged at the start of each billing month; can be cancelled with 30 days' notice
- **Annual Billing** — Paid upfront for 12 months; discounted rate vs monthly equivalent; no mid-term cancellation refunds

### 3.4 Module Pricing

All modules are individually purchasable at published per-module rates. Pricing is displayed in the module catalogue during the signup flow and is adjustable for enterprise accounts by the Super Admin.

### 3.5 Invoice & Payment Management

- Invoices are auto-generated at the start of each billing period
- Super Admin can view, regenerate, and resend invoices for any tenant
- Payment is processed through an integrated payment gateway
- Failed payments trigger the tenant suspension flow after a grace period
- Super Admin can set custom pricing for enterprise or negotiated deals

---

## 4. Module Catalogue & Dependencies

### 4.1 Module Overview

Avy ERP is organised into **ten core modules** plus a specialised Calibration sub-module. All modules are independently purchasable and independently activatable.

| # | Module | Primary Function |
|---|---|---|
| 1 | **Sales & Invoicing** | Quote-to-cash lifecycle; GST-compliant invoicing |
| 2 | **Inventory Management** | Stock tracking, goods receipt, material requests |
| 3 | **Security** | Gate attendance, goods verification, visitor verification |
| 4 | **Vendor Management** | Procurement lifecycle, PO, ASN, GRN |
| 5 | **Finance** | Payables, receivables, payments, financial reports |
| 6 | **Machine Maintenance** | PM scheduling, breakdown management, spare parts |
| 7 | **HR Management** | Full employee lifecycle, payroll, attendance, compliance |
| 8 | **Production** | OEE, shop-floor logging, scrap, incentive computation |
| 9 | **Visitor Management** | Visitor lifecycle, gate check-in, safety induction |
| 10 | **Masters** | Shared reference data (items, machines, shifts, operations) |
| — | **Calibration** | Instrument and equipment calibration compliance (sub-module of Machine Maintenance) |
| — | **Quality Management** | Incoming, in-process, and outgoing quality inspections; CAPA |
| — | **EHSS** | Environmental Health, Safety & Sustainability management |
| — | **CRM** | Customer relationship management; lead-to-opportunity pipeline |
| — | **Project Management** | Multi-phase project tracking; resource and milestone management |

### 4.2 Cross-Module Data Dependencies

Certain modules feed data to others. When a module is activated, dependent modules are automatically included in the subscription to ensure data integrity.

| Module Activated | Automatically Includes | Reason |
|---|---|---|
| HR Management | Security | Attendance data originates from Security gate scans |
| Visitor Management | Security | Gate operations and check-in/out managed by Security |
| Machine Maintenance | Masters | Machine Master is the central registry for PM scheduling |
| Production | Machine Maintenance + Masters | OEE requires machine data; production slips reference Masters |
| Inventory | Masters | Item Master drives all stock operations |
| Vendor Management | Inventory + Masters | GRN updates inventory; PO references Item Master |
| Sales & Invoicing | Finance + Masters | Invoices create receivables; line items need Item Master |
| Finance | Masters | No Series and configuration dependencies |

**Dependency notification:** When a dependent module is automatically added to the cart, the Company Admin is shown a clear explanation and the additional cost is included in the billing estimate before checkout.

### 4.3 Cross-Module Data Flow Summary

| Data Flow | Source Module | Destination Module |
|---|---|---|
| Gate timestamps → attendance records | Security | HR Management |
| Production output quantities → incentive calculations | Production | HR Management (Payroll) |
| Processed payroll → salary payable entries | HR Management | Finance |
| Machine data → OEE availability factor | Machine Maintenance | Production |
| Downtime durations → availability % | Machine Maintenance | Production |
| Spare part low stock → PO trigger | Machine Maintenance | Vendor Management |
| Pre-registrations → expected visitors list | Visitor Management | Security |
| ASN data → gate verification | Vendor Management | Security |
| GRN confirmed → stock level update | Vendor Management | Inventory |
| Sales invoice created → receivable entry | Sales & Invoicing | Finance |
| Shift timings → planned production time | Masters | Machine Maintenance |
| Item data → PO line items, invoice line items, stock records | Masters | Inventory + Vendor Management + Sales |

---

## 5. Offline-First Architecture

### 5.1 Philosophy

The mobile application is designed with an offline-first architecture. In manufacturing environments, internet connectivity on the shop floor, in warehouses, or at remote plant gates is frequently unreliable. The system must never fail to record a critical operational event due to connectivity loss.

### 5.2 Offline Scope

The following operations are available fully offline on the mobile application:

| Module | Offline Capabilities |
|---|---|
| Security | Gate attendance marking (manual codes); visitor check-in/check-out recording |
| Production | Production slip entry; scrap and NC logging; OEE data entry |
| Machine Maintenance | Breakdown reporting; PM task execution; spare part usage logging |
| HR | Leave requests; attendance regularisation; payslip viewing (last cached) |
| Inventory | Stock viewing (last cached); material request submission |
| Visitor Management | Walk-in visitor check-in; check-out |

Operations that require real-time cross-module validation (e.g., checking live stock availability before creating a material issue) may have limited functionality offline and will queue for completion on reconnection.

### 5.3 Offline Mechanism

The offline architecture works as follows:

**Local Storage Layer:** The mobile app maintains a local SQLite database (via Expo SQLite). When the device has connectivity, data is fetched from the backend API and cached locally. All subsequent reads use the local cache.

**Sync Queue:** When the user performs a write operation (create/update/delete) while offline, the operation is recorded in a local sync queue with a timestamp, operation type, payload, and retry count.

**Online Detection:** The app continuously monitors network availability. When connectivity is restored, the sync queue is processed automatically in background without requiring user action.

**Conflict Resolution:** If a record was modified both locally (offline) and on the server (by another user with connectivity) during the same period, the system applies the following rules:
- Server-side changes made after the offline period began take precedence
- The offline user's changes are presented for manual review if a conflict is detected
- Operational records (attendance punches, production slips) never conflict — they are additive by nature

**Sync Completion:** The user is notified of sync completion (or any conflicts requiring attention) via an in-app notification. The target sync window is within 30 seconds of reconnection for normal queue depths.

### 5.4 Offline Data Freshness

The system tracks when each locally cached dataset was last synchronised and displays a timestamp in the UI. Data older than a configurable threshold (default: 4 hours) is flagged as potentially stale.

---

## 6. Analytics & Reporting

### 6.1 Home Dashboard

The Home Dashboard is the entry point for every user after login. It is **role-filtered** — each user sees only the KPI cards, charts, and metrics relevant to their function and access level.

**Home Dashboard Components:**

| Component | Description |
|---|---|
| KPI Cards | Key operational metrics for the user's role (see 6.2) |
| Sales Trend Chart | Last 7-day rolling revenue (Sales / Finance roles) |
| Recent Activity Feed | Timestamped log of recent events across accessible modules |
| Quick Access Grid | Shortcuts to the user's most-used screens |
| Alert Banner | Overdue tasks, pending approvals, critical stock alerts |

### 6.2 Role-Filtered KPI Cards

| KPI Card | Visible To |
|---|---|
| Today's Sales | Business Owner, Sales Team |
| Pending Payments | Business Owner, Finance Team |
| Open Purchase Orders | Business Owner, Procurement Team |
| Items in Stock / Low Stock Alerts | Business Owner, Stores Clerk |
| Present / Absent Headcount | Business Owner, HR Manager |
| Employees on Leave Today | HR Manager |
| Active Breakdowns | Business Owner, Maintenance Manager |
| OEE Summary (Today) | Business Owner, Production Manager |
| Visitors On-Site | Business Owner, Security Personnel |
| Pending Leave Approvals | HR Manager |

### 6.3 Module Dashboards

Each module has its own dedicated dashboard with module-specific metrics:

| Module Dashboard | Key Metrics |
|---|---|
| Production OEE Dashboard | Availability %, Performance %, Quality %, OEE % per machine; colour-coded by threshold |
| HR Summary | Present / Absent / On Leave headcount by department; attendance trend |
| Finance Overview | Total Payables, Total Receivables, Cash Position, ageing buckets |
| Maintenance Dashboard | Pending PM tasks, Active breakdowns, MTTR trend, overdue escalations |
| Visitor Activity | Expected today, Checked In, Checked Out, On-Site count |
| Inventory Dashboard | Total SKUs, Low Stock items, Pending GRNs, Pending Material Requests |
| Sales Dashboard | Monthly revenue vs target, top customers, pending invoices |

### 6.4 Operational Reports

The following standard reports are generated across modules:

| Report | Module | Description |
|---|---|---|
| Sales Report | Sales | Revenue by customer, period, and product |
| Invoice Ageing | Finance | Outstanding invoices by ageing bucket (Current / 30+ / 60+ / 90+ days) |
| Payables Ageing | Finance | Vendor payment obligations by due-date status |
| Profit & Loss Statement | Finance | Monthly / annual P&L |
| Balance Sheet | Finance | Assets and liabilities snapshot |
| Cash Flow Statement | Finance | Cash inflow and outflow by period |
| Attendance Report | HR | Headcount, present/absent, department-wise breakdown |
| Leave Report | HR | Leave taken by type, employee, and period |
| Payroll Summary | HR | Salary processed, deductions, net pay by employee |
| Incentive Report | HR / Production | Incentive payouts by employee and period |
| Production Summary | Production | Units produced vs target by shift, machine, and date |
| Scrap & NC Report | Production | Rejection quantities by reason, part, and period |
| OEE Report | Production | OEE components by machine, shift, and period |
| Maintenance History | Machine Maintenance | PM completion rates, overdue tasks, MTTR |
| Breakdown Report | Machine Maintenance | Downtime by machine, issue type, and frequency |
| Visit History Report | Visitor Management | All visitor entries with full audit trail |
| Stock Report | Inventory | Current stock levels, reorder alerts, movement history |
| GRN Report | Inventory / Vendor | Received goods with condition, quantities, and discrepancies |
| Calibration Due Report | Calibration | Equipment overdue or due for calibration |
| Vendor Performance Report | Vendor Management | On-time delivery, quality rejection rates by vendor |

### 6.5 Report Output Formats

All reports can be:
- Viewed directly in the browser (web) or app (mobile) with pagination and inline filters
- Exported as **PDF** (formatted, printable, with company logo and date)
- Exported as **Excel / CSV** (for further analysis or accounting system import)

Report generation for standard reports completes in under 5 seconds. Complex date-range reports may take up to 30 seconds.

### 6.6 Insights Layer

Beyond standard reports, the platform surfaces proactive operational intelligence:

**Anomaly Alerts:**
- Unusual drops in daily production output compared to rolling average
- Machines with rapidly increasing breakdown frequency (predictive maintenance signals)
- Unexpected attendance spikes or drops (large absences, possible holidays not configured)

**Trend Indicators:**
- Week-on-week and month-on-month comparisons on all major KPIs
- Direction arrows (↑↓) on KPI cards indicating trend vs prior period

**Overdue Escalations (automatic surfacing):**
- Overdue invoices and pending payments
- Pending leave approval requests older than a configurable threshold
- PM tasks past their scheduled date
- Calibration instruments past their due date
- Purchase orders awaiting acknowledgement

---

## 7. Platform Interfaces

### 7.1 Mobile Application

The mobile application is the **primary operational platform** — designed for shop-floor operators, HR personnel, security staff, maintenance technicians, and sales teams who need ERP access in motion and on the factory floor.

**Navigation Structure:**
- Bottom navigation bar for the four most-used modules (configurable per role)
- Side drawer for access to all 10+ modules
- Bottom-sheet modals for quick data entry (attendance marking, production slip, material request)
- Full detail views for record inspection and contextual actions

**Mobile UX Principles:**
- Large touch targets optimised for use with gloved hands on the shop floor
- Offline-first — all critical operations work without connectivity
- Camera integration for face-scan attendance, QR code scanning (visitor pre-registration), and document capture
- Push notifications for approvals, alerts, PM due reminders, and visitor arrivals
- Portrait and landscape orientation support
- Minimum supported screen size: 5-inch phone screens

**Platform:** iOS and Android (same React Native codebase). Distributed via App Store and Google Play.

### 7.2 Web Application

The web application is the **primary management and administration platform** — designed for Company Admins, HR managers, finance teams, operations managers, and the Avyren Super Admin who need deep data access, multi-screen workflows, and configuration capability.

**Web-specific capabilities:**
- Full Company Master configuration (plants, shifts, No Series, IOT Reasons, system controls)
- Complete user management and RBAC configuration interface
- Full financial report generation with PDF and Excel export
- Payroll processing, review, and bank disbursement export
- Advanced filtering, sorting, column selection, and bulk operations across all modules
- Document download and export (invoices as PDF, payslips as PDF, GRN reports as Excel)
- Super Admin panel for tenant management (Avyren staff only — accessible only with Super Admin JWT)
- Multi-tab browser support for simultaneous access to multiple module screens

**Responsive design:** The web application is designed for 1280px to 4K displays.

### 7.3 Desktop Application

The desktop application (ElectronJS) is an installed client that wraps the web application codebase for environments where a browser is not available or where system-level hardware integration is required.

**Desktop-specific capabilities beyond the web application:**
- Works in network-restricted environments where browser-based access is blocked
- Native system notifications (OS-level alerts even when the app is minimised)
- Tighter integration with local hardware: biometric device drivers, receipt printers, label printers
- Offline capability equivalent to the mobile application
- Auto-update via the Electron update mechanism (silent background updates)

**Platform:** Windows and macOS. Distributed as a signed installer.

### 7.4 Kiosk Mode

The Visitor Management module supports a dedicated **Kiosk Mode** — a locked, full-screen self-service terminal intended to be deployed on a tablet or wall-mounted screen at the facility entrance.

In Kiosk Mode:
- The interface is locked to visitor self-registration and check-in flows only
- Visitors can scan their pre-registration QR code or fill in a walk-in form
- The app cannot navigate away from the kiosk screens
- No login is required for the kiosk terminal — it operates with a pre-authorised kiosk token
- Accessibility features (large text, high-contrast mode) are available

---

## 8. Integration Strategy

### 8.1 Integration Philosophy

Avy ERP is designed to be the operational core of a manufacturing business, not an island. It exposes a defined integration layer for connecting external systems, sensors, and services.

### 8.2 Biometric & Attendance Systems

**Direction:** Inbound (device → Avy ERP)

Avy ERP integrates with facial recognition and fingerprint biometric devices deployed at facility gates. The Security module receives punch-in and punch-out events from these devices and translates them into attendance records for the HR module.

Supported integration methods:
- Direct biometric device SDK integration (device-specific)
- Standard REST callback from biometric device controller
- Batch file sync (CSV export from device controller, imported on schedule)

### 8.3 IoT Machine Sensors

**Direction:** Inbound (sensor → Avy ERP)

Real-time machine status, cycle counts, and operational data from IoT sensors connected to manufacturing equipment feed the Production module's OEE engine and the Machine Maintenance module's breakdown detection.

Data received: machine-on/off events, cycle counts, error codes, temperature/pressure readings (equipment-dependent).

### 8.4 Payment Gateways

**Direction:** Outbound (Avy ERP → gateway)

SaaS subscription billing and tenant payment processing is handled through an integrated payment gateway. Supports card payments, UPI, and bank transfers (India). Invoice generation and payment reconciliation are automated.

### 8.5 Accounting Systems

**Direction:** Bidirectional (Avy ERP ↔ accounting system)

Avy ERP can sync payroll journal entries, payables, receivables, and GL postings with external accounting software:
- **Tally ERP** — Two-way sync of vouchers and ledger entries
- **QuickBooks** — Bidirectional sync of invoices, payments, and payroll

This allows companies to continue using a familiar accounting tool for bookkeeping while using Avy ERP for operations.

### 8.6 Email & SMS Notification Providers

**Direction:** Outbound (Avy ERP → provider)

All system notifications (leave approval, invoice reminders, overdue alerts, visitor check-in, OTP delivery) are routed through configurable email and SMS providers. Supported: SMTP, SendGrid, Twilio, and Indian SMS gateway integrations.

### 8.7 Quality Management Systems (QMS)

**Direction:** Bidirectional

For facilities with an existing QMS, Avy ERP can share calibration data, non-conformance records, and inspection results. This allows the QMS to remain the system of record for quality compliance while Avy ERP captures the operational events.

### 8.8 Manufacturing Execution Systems (MES)

**Direction:** Bidirectional

For facilities that already operate a standalone MES, Avy ERP can exchange production order data, shop-floor completion records, and OEE metrics. This supports phased migration scenarios where a company adopts Avy ERP for some modules while retaining their MES for shop-floor control.

### 8.9 Cloud Storage

**Direction:** Outbound

All document attachments — invoices, purchase orders, employee documents, calibration records — are stored in S3-compatible cloud object storage. Documents are stored per-tenant in isolated storage paths.

---

## 9. Non-Functional Requirements

### 9.1 Performance

| Requirement | Target |
|---|---|
| API response time (95th percentile) | < 300 ms |
| Dashboard load time (cold, first visit) | < 2 seconds |
| Mobile screen transition | < 200 ms |
| Offline sync queue processing (on reconnection) | Within 30 seconds |
| Standard report generation | < 5 seconds |
| Complex date-range report generation | < 30 seconds |
| Tenant provisioning (new company onboarding) | < 5 minutes end-to-end |
| Document export (PDF/Excel) | < 10 seconds |

### 9.2 Availability & Reliability

| Requirement | Target |
|---|---|
| Platform uptime | 99.9% (excluding planned maintenance windows) |
| Planned maintenance windows | Announced 48 hours in advance; conducted off-peak |
| Data backup frequency | Daily automated backups |
| Recovery Point Objective (RPO) | 24 hours |
| Recovery Time Objective (RTO) | 4 hours |
| Database replication | Synchronous primary + async read replica |

### 9.3 Security

**Transport Security:**
- All data in transit encrypted via TLS 1.3
- HTTPS enforced on all web and API endpoints; HTTP redirected to HTTPS
- Certificate management via Let's Encrypt (automated renewal)

**Data at Rest:**
- All data at rest encrypted at the database and object storage layer
- Encryption keys managed per-tenant where applicable

**Authentication & Session:**
- JWT tokens are tenant-scoped — a token from Tenant A cannot access Tenant B data
- Session expiry with configurable idle timeout per tenant (default: 30 minutes)
- Account lockout after configurable number of failed login attempts
- MFA available at platform, tenant, role, and user levels

**Access Control:**
- RBAC enforced at the API layer — not just the UI
- No SQL query can cross tenant schema boundaries
- Super Admin access to tenant business data requires explicit, logged approval

**Audit & Compliance:**
- Full immutable audit log for all create, update, and delete operations (who, what, when, from where)
- Audit logs are scoped to the tenant's schema and cannot be modified by anyone including Super Admin
- Password policy configurable per tenant (minimum length, complexity, history, expiry)

### 9.4 Scalability

| Dimension | Approach |
|---|---|
| Horizontal backend scaling | Load-balanced backend instances |
| Database growth | Additional PostgreSQL shards added as tenant volume increases |
| Tenant isolation at scale | Schema-per-tenant; heavy tenants migrated to dedicated DB instances |
| Concurrent users | Architecture supports thousands of concurrent users across all tenants |
| Message queue | Event bus handles async cross-module communication without blocking requests |

### 9.5 Accessibility & Localisation

- Mobile app supports both portrait and landscape orientations
- Web app responsive from 1280px to 4K displays
- Date, currency, and number formats configurable per tenant locale
- **India compliance built-in:** GST (CGST/SGST/IGST), PF, ESI, TDS, PT, LWF — all computed natively
- Multi-language support planned for Phase 2 (initially English only)
- HSN code-based GST rate lookup for invoice line items
- Currency: INR (primary); configurable to USD, EUR, and others per tenant

### 9.6 Data Retention

| Data Category | Retention Period | Notes |
|---|---|---|
| Payroll & Tax records | 7 years | Indian regulatory requirement |
| Attendance records | 3 years minimum | Factory Act requirement |
| Visitor records | 1 year (configurable) | Security compliance |
| Audit logs | 7 years | Non-deletable by any user |
| Production records | 5 years | Quality and traceability |
| Calibration records | Equipment lifecycle + 5 years | ISO 9001 requirement |

---

## 10. Bulk Data Management

### 10.1 Bulk Import

The Super Admin and Company Admin can import bulk data for master records using CSV or Excel files. This is essential during initial setup when migrating from legacy systems.

**Importable Masters:**

| Master | Key Fields |
|---|---|
| Company Master | Company Code, Name, Industry, Country, Status |
| IOT Reason Master | Reason Type, Reason, Description, Department |
| No Series | Code, Description, Linked Screen, Prefix, Suffix, Start Number |
| Employee Master | Employee ID, Name, Department, Designation, Joining Date |
| Item Master | Item Code, Description, HSN, GST Rate, UOM, Type |
| Vendor Master | Vendor Code, Name, GSTIN, Category, Contact |
| Customer Master | Customer Code, Name, GSTIN, State, Contact |
| Machine Master | Machine Code, Name, Type, Location, Shift |

**Import Workflow:**
1. Select import target and download the sample template
2. Fill the template with data
3. Upload the file (drag-and-drop or click; .csv or .xlsx; max 5 MB)
4. Choose duplicate handling: **Skip Existing** or **Overwrite Existing**
5. Review the parsed preview table; validation errors are highlighted
6. Confirm import; view success/failure summary

### 10.2 Bulk Export

All list screens across every module support bulk export:
- Export all or selected records as CSV or Excel
- Export formatted reports as PDF
- Document attachments (invoices, payslips) are individually downloadable and bulk-downloadable as ZIP

---

*This is Part 2 of 5 of the Avy ERP Master PRD.*
*Part 3 covers: HR Management, Security, and Visitor Management modules.*
*Part 4 covers: Sales & Invoicing, Inventory, Vendor Management, and Finance modules.*
*Part 5 covers: Production, Machine Maintenance, Calibration, Quality Management, EHSS, CRM, and Project Management modules.*

---

**Document Control**

| Field | Value |
|---|---|
| Product | Avy ERP |
| Company | Avyren Technologies |
| Part | 2 of 5 — Platform Capabilities |
| Version | 2.0 |
| Date | April 2026 |
| Status | Final Draft |
| Classification | Confidential — Internal Use Only |
