# Avy ERP — Tenant Onboarding Guide
## Super Admin Configuration Reference

> **Document Code:** AVY-CFG-001  
> **Module:** System Administration — Tenant / Company Onboarding  
> **Audience:** Super Administrators  
> **Version:** 1.0  
> **Product:** Avy ERP (Avyren Technologies)

---

## Table of Contents

1. [Overview & Purpose](#1-overview--purpose)
2. [Super Admin Access & Roles](#2-super-admin-access--roles)
3. [Company Identity & Basic Information](#3-company-identity--basic-information)
4. [Statutory & Tax Identifiers (Compliance)](#4-statutory--tax-identifiers-compliance)
5. [Registered & Correspondence Address](#5-registered--correspondence-address)
6. [Fiscal Year & Calendar Settings](#6-fiscal-year--calendar-settings)
7. [System Preferences & Feature Flags](#7-system-preferences--feature-flags)
8. [Branch / Location Setup](#8-branch--location-setup)
9. [Key Contacts Management](#9-key-contacts-management)
10. [Plant / Multi-Location Management](#10-plant--multi-location-management)
11. [Shift & Time Management](#11-shift--time-management)
12. [Number Series (No Series) Configuration](#12-number-series-no-series-configuration)
13. [IOT Reason Master](#13-iot-reason-master)
14. [System Controls & Operational Settings](#14-system-controls--operational-settings)
15. [Company Status & Lifecycle Management](#15-company-status--lifecycle-management)
16. [User Management & Role-Based Access Control](#16-user-management--role-based-access-control)
17. [Bulk Data Import](#17-bulk-data-import)
18. [Tenant Provisioning Checklist](#18-tenant-provisioning-checklist)
19. [Audit Trail & Change Logging](#19-audit-trail--change-logging)
20. [Multi-Tenant Architecture Notes](#20-multi-tenant-architecture-notes)

---

## 1. Overview & Purpose

Tenant Onboarding in Avy ERP is the process by which the **Super Administrator** registers and fully configures a new company (tenant) into the system. Each company onboarded is an independent tenant with its own data boundary, configuration space, compliance settings, and user base.

This document serves as the **exhaustive reference** for every screen, field, toggle, and decision point that a Super Admin must address when onboarding a new tenant — from initial registration through to full operational readiness.

### Onboarding Flow Summary

```
1. Create Company Record  →
2. Fill Basic Identity    →
3. Add Statutory IDs      →
4. Configure Address      →
5. Set Fiscal Year        →
6. Configure Preferences  →
7. Add Branches           →
8. Add Key Contacts       →
9. Set Up Plants          →
10. Configure Shifts      →
11. Define No Series      →
12. IOT Reason Master     →
13. System Controls       →
14. Assign Admin Users    →
15. Activate Tenant       →  GO LIVE
```

---

## 2. Super Admin Access & Roles

### 2.1 Super Admin Identity

The Super Admin is the **highest-privilege system user** who has full access to all companies, all configuration screens, and all modules within Avy ERP.

| Attribute | Details |
|---|---|
| Role Label | Super Admin |
| Access Scope | All Companies (Cross-Tenant) |
| Screen Access | All 32+ Configuration Screens |
| Data Access | Read + Write + Delete across all tenants |
| Session Management | Live session timer displayed in UI |
| Authentication | Username + Password (with show/hide password toggle) |

### 2.2 Role Hierarchy

```
Super Admin (Platform Level)
  └── Tenant Admin (Company Level)
        └── HR Manager
        └── Finance Manager
        └── Operations Manager
              └── Supervisors
                    └── Employees (ESS)
```

### 2.3 Super Admin Permissions

- Create, edit, and delete any company/tenant record
- Access all configuration tabs across all companies
- Add and manage all types of users
- Enable or disable system-wide feature flags
- Perform bulk data imports
- View audit logs across all tenants
- Manage No Series, Shifts, IOT Reasons, Controls globally
- Switch between companies using the Company Selector panel
- Access the Global Search (⌘K / Ctrl+K) to jump to any screen

### 2.4 Company Selector Panel

The left panel hosts a **Company Selector** that allows the Super Admin to:

- View the total count of onboarded companies (e.g., badge showing "3")
- Search companies by name via inline search
- Switch between tenants by clicking the company row
- See company status badges (Active / Draft / Inactive / Pilot)
- Add a new company using the "+ Add Company" button
- Each company row shows: Logo Initial, Company Name, Company Code, Status

---

## 3. Company Identity & Basic Information

This is the **first and foundational tab** in the company setup. All downstream configuration depends on accurate data here.

### 3.1 Company Logo

| Field | Details |
|---|---|
| Upload Format | PNG, JPG, or SVG |
| Maximum File Size | 2 MB |
| Recommended Dimensions | 200 × 200 px |
| Usage | Shown on payslips, offer letters, reports, and all employee-facing screens |
| Action | Click to upload or drag-and-drop; instant preview on upload |

### 3.2 Core Identity Fields

| Field | Type | Required | Notes |
|---|---|---|---|
| Display Name | Text | ✅ Yes | Shown on all employee-facing screens, payslips, portals |
| Legal / Registered Name | Text | ✅ Yes | Full name as per incorporation documents |
| Business Type | Dropdown | ✅ Yes | Private Limited (Pvt. Ltd.), Public Limited, LLP, Partnership, Proprietorship, Others |
| Nature of Industry | Dropdown | ✅ Yes | IT, Manufacturing, BFSI, Healthcare, Retail, Automotive, Pharma, Education, etc. |
| Company Code | Text (Auto-generated) | ✅ Yes | Unique system identifier; format: `ABC-IN-001` — auto-generated, can be overridden |
| Short Name | Text | No | Abbreviated name used in screen headers and compact displays |
| Date of Incorporation | Date | ✅ Yes | As per MCA / ROC registration |
| Number of Employees | Number | No | Approximate headcount; used for compliance threshold checks (PF, ESI, PT) |
| CIN Number | Text | No | Corporate Identity Number issued by MCA; format: `U72900KA2019PTC312847` |
| Official Website | URL | No | Company website URL; includes "Visit ↗" quick-open button |
| Corporate Email Domain | Text | ✅ Yes | Used for auto-provisioning employee email IDs; includes "Verify ✓" domain check |

### 3.3 Status Control

The company status can be set during or after initial creation:

| Status | Color | Meaning |
|---|---|---|
| Active | 🟢 Green | Company is live and operational |
| Pilot | 🔵 Blue | Company is in trial or testing phase |
| Inactive | 🔴 Red | Company has been deactivated |
| Draft | 🟡 Amber | Company setup is incomplete / not yet activated |

### 3.4 Additional Identity Fields (Recommended)

> These fields are not visible in the current screens but are standard for comprehensive ERP onboarding and should be included:

| Field | Notes |
|---|---|
| Group / Parent Company | For conglomerates or subsidiaries |
| Country of Incorporation | Primary operating jurisdiction |
| Listed / Unlisted | For public companies — stock exchange details |
| MSME Registration | If applicable — Micro / Small / Medium classification |
| Import Export Code (IEC) | For companies with import-export operations |
| DPIIT Registration | For start-ups registered with Government of India |
| Udyam Registration Number | For MSME-registered companies |
| Company Description / About | Brief description for internal documentation |
| ERP Go-Live Date | Date of first productive use of Avy ERP |
| Subscription Tier | Basic / Professional / Enterprise |
| Contract Start / End Date | Tenant subscription period |

---

## 4. Statutory & Tax Identifiers (Compliance)

> ⚠️ **Critical Warning:** These identifiers drive payroll, TDS computation, statutory filings, and Form 16 generation. Ensure 100% accuracy before saving. Incorrect identifiers will cause compliance failures and regulatory penalties.

### 4.1 India Statutory Identifiers

| Field | Label | Format | Required | Notes |
|---|---|---|---|---|
| PAN | Income Tax Permanent Account Number | `AARCA5678F` (10 chars) | ✅ Yes | Required for TDS, Form 16, Form 24Q |
| TAN | Tax Deduction Account Number | `BLRA98765T` (10 chars) | ✅ Yes | Required for TDS deduction and quarterly returns |
| GSTIN | Goods and Services Tax Identification Number | `29AARCA5678F1Z3` (15 chars) | Conditional | Required if company is GST-registered; state code auto-prefixed |
| PF Registration No. | Provident Fund Employer Code | `KA/BLR/0112345/000/0001` | ✅ Yes | Required for PF deductions and monthly ECR uploads |
| ESI Employer Code | Employee State Insurance Code | `53-00-123456-000-0001` | Conditional | Required if any employee earns ≤ ₹21,000/month gross |
| PT Registration | Professional Tax Registration Number | State-specific format | Conditional | Required in PT-applicable states (Karnataka, Maharashtra, etc.) |
| LWFR Number | Labour Welfare Fund Registration | Optional | No | State-specific; required in LWF-applicable states |
| ROC Filing State | Registrar of Companies | `RoC Bengaluru, Karnataka` | ✅ Yes | Determines filing jurisdiction for annual returns |

### 4.2 Additional Statutory Fields (Recommended)

| Field | Notes |
|---|---|
| TRACES Username | For TDS return filing via Income Tax portal |
| EPF DSC / EFiling Credentials | For ECR upload via EPFO Unified Portal |
| ESIC Web Portal Credentials | For ESI return filing |
| PT Challan Reference State | State-specific PT authority |
| Gratuity Trust Registration | If company maintains a private Gratuity Trust |
| Superannuation Scheme | If company offers superannuation benefit |
| NPS Registration | National Pension System employer registration |
| TDS Section 192 Regime | Old Tax Regime / New Tax Regime default for TDS |

### 4.3 International Statutory Fields (for Global Companies)

| Field | Notes |
|---|---|
| VAT Registration Number | For UAE, EU, UK tenants |
| Social Security Employer ID | For US entities |
| Employer Identification Number (EIN) | For US entities |
| RFC Number | For Mexico entities |
| Tax ID (TIN) | Generic international tax identifier |
| Payroll Tax Reference | Country-specific payroll tax authority reference |

---

## 5. Registered & Correspondence Address

The system supports **two separate addresses** for a company:

### 5.1 Registered Address (Primary)

The address as filed with the Registrar of Companies (ROC) and used on statutory documents.

| Field | Required | Notes |
|---|---|---|
| Address Line 1 | ✅ Yes | Street, building, floor |
| Address Line 2 | No | Area, landmark, locality |
| City | ✅ Yes | |
| District | No | Important for certain statutory filings |
| State | ✅ Yes | Dropdown — all Indian states listed |
| Country | ✅ Yes | Default: India; supports international |
| PIN Code | ✅ Yes | 6-digit PIN; includes "🔍 Lookup" to auto-fill city/state |
| STD Code | No | Telephone area code |

### 5.2 Corporate / HQ Address (Operational)

The address of the main operational office (may differ from registered address).

| Field | Notes |
|---|---|
| Same as Registered | Checkbox — auto-copies registered address when checked |
| Address Line 1 | Corporate office address |
| City | |
| State | |
| PIN Code | |

### 5.3 Address Usage in System

| Context | Address Used |
|---|---|
| Payslips | Corporate / HQ Address |
| Statutory Filings | Registered Address |
| Offer Letters | Corporate / HQ Address |
| GST Invoices | GSTIN-linked plant address |
| Delivery Challans | Shipping address (plant-level) |

---

## 6. Fiscal Year & Calendar Settings

### 6.1 Financial Year Start

Select the financial year start month. This determines the payroll year, TDS computation period, and all date-range calculations.

| Option | Description |
|---|---|
| April – March | Standard India FY (default for Indian companies) |
| January – December | Calendar year (global standard) |
| July – June | Australia / New Zealand style |
| October – September | Some Middle East / custom structures |
| Custom Range | Define custom start month |

### 6.2 Payroll Cycle

| Field | Options | Notes |
|---|---|---|
| Frequency | Monthly, Bi-Monthly, Weekly | Monthly is the standard for salaried employees |
| Cut-off Day | Last Working Day, 25th, 1st of Next Month | Day when attendance/leaves are frozen for payroll |
| Disbursement Day | 1st of Next Month, Last Day, 28th | Day salaries are credited |

### 6.3 Week & Timezone

| Field | Options | Notes |
|---|---|---|
| Week Start | Monday, Sunday | Affects attendance, leave, and report calculations |
| Working Days | Mon–Fri (5 days), Mon–Sat (6 days), Alternate Sat Off | Default work week structure |
| Timezone | IST UTC+5:30, UTC+0, EST UTC−5, and others | Critical for attendance punch-in/out timestamps |

### 6.4 Working Days Toggle

Each day of the week can be individually toggled ON/OFF:

| Day | Default (India) |
|---|---|
| Monday | ✅ Working |
| Tuesday | ✅ Working |
| Wednesday | ✅ Working |
| Thursday | ✅ Working |
| Friday | ✅ Working |
| Saturday | ✅ Working (for 6-day companies) |
| Sunday | ❌ Weekly Off |

### 6.5 Additional Calendar Settings (Recommended)

| Setting | Notes |
|---|---|
| Company Holiday Calendar | National holidays, regional holidays, company-specific holidays |
| Alternate Saturday Policy | 1st & 3rd Saturday off / 2nd & 4th Saturday off |
| Compensatory Off Policy | Auto-generate comp-off on working Sundays/holidays |
| Shift Change Policy | Minimum rest period between shifts (e.g., 8 hours) |
| Grace Period for Attendance | Minutes of late arrival allowed without marking LOP |
| Half-Day Calculation Threshold | Time after which half-day is marked |

---

## 7. System Preferences & Feature Flags

### 7.1 Locale & Format Settings

| Setting | Options | Notes |
|---|---|---|
| Currency | INR — ₹, USD — $, GBP — £, EUR — €, AED — د.إ, others | Primary currency for all financial transactions |
| Language | English, Hindi, Tamil, Kannada, Telugu, Malayalam | UI language for the tenant |
| Date Format | DD/MM/YYYY, MM/DD/YYYY, YYYY-MM-DD | Applied globally across all date fields in the tenant |
| Number Format | Indian (2,00,000) / International (200,000) | Applied to all numeric displays |
| Time Format | 12-hour (AM/PM), 24-hour | Applied to all time fields |

### 7.2 Compliance Feature Toggles

| Feature | Description | Default |
|---|---|---|
| 🇮🇳 India Statutory Compliance Mode | Enables PF, ESI, PT, TDS, Form 16, Gratuity, Bonus Act calculations | ON |
| Multi-Currency Payroll | Support for international employees in multiple currencies | OFF |
| International Tax Compliance | FATCA, transfer pricing, foreign remittances | OFF |

### 7.3 Employee Portal & App Toggles

| Feature | Description | Default |
|---|---|---|
| 📱 Employee Self-Service (ESS) Portal | Employee login for leaves, payslips, IT declarations | ON |
| 📲 Mobile App (iOS & Android) | Avy ERP mobile app access for all employees | ON |
| 🤖 AI HR Assistant Chatbot | NLP chatbot for leave balance queries, policy FAQs | OFF |
| ✍️ e-Sign Integration | Digital signatures for offer letters, Full & Final settlement | OFF |

### 7.4 Integration & Device Toggles

| Feature | Description | Default |
|---|---|---|
| 🔔 Biometric / Device Sync | Auto-sync attendance from ZKTeco, ESSL, and other biometric devices | OFF |
| 📊 Payroll Bank Integration | Direct bank file (NEFT/RTGS) generation for salary disbursement | OFF |
| 📧 Email Notifications | Automated emails for payslips, leave approvals, alerts | OFF |
| 📲 WhatsApp Notifications | Salary credit alerts, leave status via WhatsApp Business API | OFF |
| 🔗 Third-Party HRMS Sync | Integration with external HRMS tools (Darwinbox, Keka, etc.) | OFF |

### 7.5 Advanced Feature Flags (Recommended)

| Feature | Description |
|---|---|
| Geo-Fencing Attendance | Restrict attendance punch-in to within defined GPS radius |
| Face Recognition Attendance | AI-powered face recognition for touchless attendance |
| Document Management System | Digital storage of employee documents (Aadhaar, PAN, etc.) |
| Loan & Advance Module | Employee loan and salary advance management |
| Asset Management | Assign and track company assets to employees |
| Travel & Expense Management | Expense claim submission and approval workflow |
| Learning Management System (LMS) | Online training module for employees |
| Performance Management System (PMS) | KRA/KPI-based appraisal cycles |
| Recruitment (ATS) | Job requisition, applicant tracking, offer generation |
| Canteen / Cafeteria Management | Meal booking and deduction integration |
| Vehicle / Fleet Management | Company vehicle assignment and fuel tracking |
| Visitor Management | Gate-level visitor log for security |

---

## 8. Branch / Location Setup

Branches are sub-units of a company at different geographic locations. They share the same legal entity but may have different addresses, contacts, and compliance registrations.

### 8.1 Branch Fields

| Field | Required | Options / Notes |
|---|---|---|
| Branch Name | ✅ Yes | e.g., "Bengaluru HQ", "Mumbai Office" |
| Branch Code | ✅ Yes | Unique identifier; format: `BLR-HQ-001` |
| Branch Type | No | Head Office, Regional Office, Satellite Office, Warehouse, Service Centre |
| Address Line 1 | No | Street address |
| City | No | |
| State | No | Dropdown — all states |
| PIN Code | No | 6-digit PIN |
| Contact Number | No | Branch phone number |
| Geo-Fencing Radius (metres) | No | Radius in metres for GPS-based attendance (e.g., 200 m) — used when employees must punch-in within campus |

### 8.2 Branch Management Actions

| Action | Description |
|---|---|
| + Add Branch | Add a new branch row for the current company |
| Save Branch | Save or update an existing branch |
| Delete Branch | Remove a branch (with confirmation dialog) |
| Set as Primary | Designate a branch as the primary/head location |

### 8.3 Additional Branch-Level Settings (Recommended)

| Setting | Notes |
|---|---|
| Branch-specific Holiday Calendar | Branch may have state/regional holidays different from HQ |
| Branch-specific PT Registration | Some branches in different states may have their own PT registration |
| Branch GSTIN | If branch is in a different state — separate GSTIN required |
| Branch HR Contact | Dedicated HR person for that branch |
| Branch Payroll Configuration | Option to use branch-specific payroll cutoff or disbursement day |

---

## 9. Key Contacts Management

Multiple key contacts can be added for a company, categorized by role. These contacts are used for communication, escalation, and documentation purposes.

### 9.1 Contact Fields

| Field | Required | Notes |
|---|---|---|
| Contact Name | ✅ Yes | Full name of the person |
| Designation | No | Job title (e.g., CEO, CHRO, CFO) |
| Department | No | Functional area (e.g., Executive Management, HR, Finance) |
| Mobile Number | ✅ Yes | Primary mobile with country code |
| Email Address | ✅ Yes | Official email address |
| Contact Type | No | Primary, HR Contact, Finance Contact, IT Contact, Legal Contact |
| LinkedIn Profile | No | URL to LinkedIn profile |
| Alternative Email | No | Secondary email |

### 9.2 Contact Types

| Type | Purpose |
|---|---|
| Primary | Main point of contact for all communication |
| HR Contact | HRMS-related queries and configuration |
| Finance Contact | Payroll, statutory payments, invoicing |
| IT Contact | System access, technical issues |
| Legal Contact | Compliance, regulatory matters |
| Operations Contact | Plant/shift/production queries |

### 9.3 Actions

| Action | Description |
|---|---|
| + Add Contact | Add a new contact card |
| Remove Contact | Delete a specific contact |
| Save Contact | Save or update contact details |

---

## 10. Plant / Multi-Location Management

This section handles companies with multiple manufacturing plants, offices, or operational locations, each potentially in different states (requiring separate GSTIN) or with different shift patterns.

### 10.1 Multi-Plant Mode Toggle

| Setting | Description |
|---|---|
| Multi-Plant Mode | Enable if the company operates from multiple plants or locations |
| Status | OFF (default) / ON |
| Impact | When ON, activates the Plants tab and plant-level configuration |

### 10.2 Plant Data Management Strategy

When Multi-Plant Mode is ON, the admin must choose how plant-level data is managed:

| Option | Description | Best For |
|---|---|---|
| 🔗 Common Configuration | All plants share the same shift schedules, No Series, and IOT Reason lists | Companies where all plants follow identical patterns |
| 🏭 Per-Plant Configuration | Each plant has its own independent shift schedules, No Series counters, and IOT Reason lists | Companies where plants have different working hours or need separate serial tracking |

**What always remains company-level (regardless of config mode):**
- Controls & System Settings
- User Management
- Statutory & Tax Identifiers

### 10.3 Plant Identity Fields

| Field | Required | Notes |
|---|---|---|
| Plant Name | ✅ Yes | e.g., "Pune Plant", "Chennai Unit 2", "Bengaluru HQ" |
| Plant Code | ✅ Yes | Unique code; format: `PLT-PUN-01`, `PLT-CHN-02` |
| Plant Type | No | Manufacturing Plant, Assembly Unit, Warehouse/Distribution, R&D Centre, Head Office, Regional Office, Service Centre |
| Status | No | Active, Inactive, Under Construction |

### 10.4 Head Quarter (HQ) Plant Designation

| Feature | Description |
|---|---|
| Mark as HQ | Toggle to designate a plant as the company's Head Quarter |
| HQ Sync | When a plant is marked as HQ, its address and GST details auto-populate the General Information tab |
| Only One HQ | System enforces a single HQ per company; changing HQ shows a confirmation dialog |

### 10.5 Plant GST / Tax Details

| Field | Required | Notes |
|---|---|---|
| Plant GSTIN | Conditional | State-wise GSTIN; in India, a separate GSTIN is required for each state where the company operates |
| State (for GST) | Conditional | Auto-prefixes the 2-digit state code to the GSTIN |
| Inherit from HQ | Default | If blank, the plant inherits the company's HQ GSTIN |

All 28 Indian states + UTs are available in the GST State dropdown, with their 2-digit state codes (01–38).

### 10.6 Plant Address

| Field | Required | Notes |
|---|---|---|
| Address Line 1 | ✅ Yes | |
| Address Line 2 | No | |
| City | ✅ Yes | |
| District | No | |
| State | ✅ Yes | |
| PIN Code | No | |

### 10.7 Plant Contact Persons

Each plant can have its own list of contact persons (same structure as company-level contacts).

### 10.8 Plant Status Management

| Status | Meaning |
|---|---|
| Active | Plant is operational |
| Inactive | Plant has ceased operations |
| Under Construction | Plant is being set up |

### 10.9 Plant Statistics Summary

The Plants tab displays summary stat chips showing:
- Total Plants
- Active Plants
- Plants with own GST
- Plants in Construction

---

## 11. Shift & Time Management

### 11.1 Day Boundary Configuration

Before defining individual shifts, set the overall production/operational day boundary:

| Field | Required | Notes |
|---|---|---|
| Day Start Time | ✅ Yes | The time at which the production or working day begins |
| Day End Time | ✅ Yes | The time at which the production or working day ends |

### 11.2 Weekly Off Days

Select which days of the week are non-working (weekly offs):

| Day | Configurable | Notes |
|---|---|---|
| Monday | ✅ | |
| Tuesday | ✅ | |
| Wednesday | ✅ | |
| Thursday | ✅ | |
| Friday | ✅ | |
| Saturday | ✅ | Often Sunday + alternate Saturdays |
| Sunday | ✅ | Standard weekly off |

### 11.3 Shift Master

Multiple shifts can be defined per company or per plant (depending on Multi-Plant config):

| Field | Required | Notes |
|---|---|---|
| Shift Name | ✅ Yes | e.g., "Morning Shift", "General Shift", "Night Shift", "Shift A" |
| From Time | ✅ Yes | Shift start time in HH:MM AM/PM format |
| To Time | ✅ Yes | Shift end time in HH:MM AM/PM format |
| No Shuffle | No | When checked, employees in this shift are not included in shift rotation |

### 11.4 Planned Downtime Slots (Per Shift)

Each shift can have multiple planned downtime slots. These are used for OEE (Overall Equipment Effectiveness) calculations and production planning.

| Field | Options |
|---|---|
| Downtime Type | Scheduled Maintenance, Lunch Break, Changeover, Training, Cleaning, Tea Break, Other |
| Duration (minutes) | Numeric; defines the planned break duration |

Multiple downtime slots can be added to each shift using the "+ Add Downtime Slot" button.

### 11.5 Shift Actions

| Action | Description |
|---|---|
| New Shift | Add a new shift entry |
| Save Shift | Save or update a shift record |
| Delete Shift | Remove a shift (with confirmation) |
| Search Shifts | Filter shift table by name |

### 11.6 Shift Table View

The shift table displays:
- Shift Name
- From Time
- To Time
- Weekly Off Days (shown as chips)
- Pagination controls

---

## 12. Number Series (No Series) Configuration

Number Series defines the auto-numbering format for all transactional documents generated across modules in Avy ERP. This ensures consistent, unique, and traceable document numbering.

### 12.1 Scope Configuration

When Multi-Plant Mode is active:

| Scope | Description | Example |
|---|---|---|
| 🏢 Company-wide | All series use a single shared counter across all plants | `EMP-00001`, `TKT-00001` |
| 🏭 Plant-wise | Each plant runs its own independent counter per series; plant code is auto-embedded in prefix | `DOC-PUN-00001`, `DOC-CHN-00001` |

### 12.2 No Series Record Fields

| Field | Required | Notes |
|---|---|---|
| Code | ✅ Yes | Short identifier for the series (e.g., `DOC`, `EMP`, `TKT`) |
| Description | No | Human-readable name (e.g., "Employee ID", "Ticket Number") |
| Linked Screen | ✅ Yes | The module/screen where this series is applied |
| Prefix | No | Text before the number (e.g., `EMP-`, `TKT-`, `WO-`) |
| Suffix | No | Text after the number (e.g., `-2026`) |
| Number Count | No | Number of digits in the counter (e.g., 3 = `001`, 5 = `00001`) |
| Starting Number | No | The first number in the series (default: 1) |

### 12.3 Linked Screen Options

No Series can be configured for the following screens/modules:

**HR / People**
- Employee Onboarding (Employee ID)
- Attendance
- Leave Management
- Payroll

**Production / Operations**
- Work Order
- Production Order
- Andon Ticket

**Quality**
- Quality Check
- Non-Conformance

**Maintenance**
- Maintenance Ticket
- Preventive Maintenance

**Inventory / Stores**
- Goods Receipt Note (GRN)
- Material Request
- Gate Pass
- Stock Transfer

**Commercial / Finance**
- Sales Invoice
- Purchase Order
- Delivery Challan
- Goods Return

### 12.4 Preview & Validation

The system provides a **live preview** of how the generated document number will look:
```
Prefix: EMP-  |  Count: 5  |  Start: 1  →  Preview: EMP-00001
```

### 12.5 No Series Table Actions

| Action | Description |
|---|---|
| + New | Create a new No Series record |
| ✓ Save | Save the current record |
| 🗑 Delete | Delete the selected record |
| Search | Filter records by Code or Description |
| Sort | Sort by Code or Description |
| Pagination | Configure page size (5 / 10 / 20 records per page) |

---

## 13. IOT Reason Master

The IOT Reason Master is used in **OEE Monitoring** and **Production Management** to classify and track machine downtime events. These reasons are logged when machines go idle or raise alarms on the shop floor.

### 13.1 Scope

Same as No Series — can be configured as **Company-wide** or **Per-Plant** depending on the Multi-Plant configuration mode.

### 13.2 IOT Reason Fields

| Field | Required | Options / Notes |
|---|---|---|
| Reason Type | ✅ Yes | Machine Idle, Machine Alarm |
| Reason | ✅ Yes | Short label (e.g., "PREVENTIVE MAINTENANCE", "MATERIAL SHORTAGE") |
| Description | No | Detailed explanation of the reason |
| Department | No | The department responsible for the reason (selectable from department master; new departments can be added inline) |
| Planned | Checkbox | Available only when Reason Type = Machine Idle; marks the reason as planned downtime |
| Duration (minutes) | Conditional | Appears only when Reason Type = Machine Idle AND Planned = checked; defines maximum planned idle time |

### 13.3 Planned vs Unplanned Downtime Logic

| Scenario | Classification |
|---|---|
| Machine Idle + Planned = Yes + Actual ≤ Duration | In-Process Planned Downtime |
| Machine Idle + Planned = Yes + Actual > Duration | Excess treated as Unplanned Downtime |
| Machine Idle + Planned = No | Unplanned Downtime |
| Machine Alarm | Equipment/Alarm Downtime |

This classification directly impacts **OEE calculations** by separating planned and unplanned downtime.

### 13.4 IOT Reason Actions

| Action | Description |
|---|---|
| + New | Create a new IOT Reason record |
| ✓ Save | Save the current record |
| 🗑 Delete | Delete the selected record |
| + Add Category | Add a new department inline without navigating away |
| Search | Filter reason list |
| Sort | Sort by Reason or Description |

---

## 14. System Controls & Operational Settings

Controls are **always company-level** — they apply to all plants regardless of the Multi-Plant configuration.

### 14.1 NC Reason Assignment Screen Control

| Setting | Description |
|---|---|
| Enable Edit Mode | When enabled, operators can edit or delete existing Non-Conformance (NC) entries directly in the NC Reason Assignment screen |

### 14.2 Load & Unload Assignment Control

| Setting | Description |
|---|---|
| Load/Unload | When enabled, Load & Unload time is tracked and assigned to the selected category |
| Cycle Time | When enabled, cycle time data is captured and included in production analytics |

### 14.3 Additional System Controls (Recommended)

| Control | Description |
|---|---|
| Payroll Lock Control | Prevent payroll modifications after lock date |
| Attendance Regularization Window | Number of days an employee can regularize past attendance |
| Leave Carry Forward Control | Enable/disable automatic carry forward at year end |
| Reimbursement Approval Levels | Configure single vs multi-level approval for expenses |
| Overtime Approval | Require manager approval before overtime is paid |
| Backdated Entry Control | Restrict creation of records with past dates beyond X days |
| Document Number Edit Lock | Prevent manual editing of auto-generated document numbers |
| Data Archival Policy | Frequency and scope of data archival |
| Session Timeout | Idle session auto-logout duration (e.g., 30 mins) |
| Password Policy | Minimum length, complexity, expiry, history rules |
| MFA (Multi-Factor Authentication) | Require OTP/Authenticator app for login |
| IP Whitelist | Restrict ERP access to approved IP addresses or VPN |
| Email Notification Controls | Global on/off for system-generated emails |
| Audit Log Retention | Duration for which audit logs are retained |

---

## 15. Company Status & Lifecycle Management

### 15.1 Company Status

| Status | When to Use |
|---|---|
| Draft | Initial setup is in progress; system is not yet active for this tenant |
| Pilot | Company is in trial/UAT phase; limited users onboarded |
| Active | Company is live; full production use |
| Inactive | Company has terminated its subscription or ceased operations |
| Suspended | Temporary suspension due to payment or compliance issue |

### 15.2 Last Saved & Auto-Save

| Feature | Description |
|---|---|
| Auto-Save | System auto-saves form data periodically; status shown as "Saved · HH:MM" |
| Last Saved | Timestamp of the most recent manual save |
| Save Draft | Saves incomplete configuration without activating the tenant |
| Reset | Reverts all unsaved changes to the last saved state |
| Save & Continue | Saves current tab and navigates to the next configuration step |

### 15.3 Company Management Actions

| Action | Description |
|---|---|
| New Company | Opens a blank form for creating a new tenant |
| Save Company | Saves all configuration for the selected company |
| Delete Company | Permanently removes a company (with confirmation; irreversible) |
| Duplicate Company | Clone an existing company setup as a template for a new tenant |
| Export Company Config | Export the configuration as JSON/Excel for documentation or migration |

---

## 16. User Management & Role-Based Access Control

### 16.1 Role Levels

Avy ERP implements a **5-level role hierarchy**:

| Level | Role Category | Examples |
|---|---|---|
| Level 1 — System | Platform-wide roles | Super Admin, Platform Owner |
| Level 2 — Management | Company-wide management | HR Manager, Finance Manager, Operations Manager |
| Level 3 — Supervisory | Department / team leads | HR Executive, Payroll Executive, Plant Supervisor |
| Level 4 — Operational | Day-to-day users | Attendance Operator, Storekeeper, Quality Inspector |
| Level 5 — Read-Only | View-only access | Auditor, Compliance Reviewer |

### 16.2 User Record Fields

| Field | Required | Notes |
|---|---|---|
| Full Name | ✅ Yes | |
| User ID / Username | ✅ Yes | Used for login; typically email format |
| Password | ✅ Yes | Enforced per password policy |
| Role | ✅ Yes | Assigned from the role hierarchy |
| Company Access | ✅ Yes | SA = all companies; Admin = assigned company only |
| Status | ✅ Yes | Active / Inactive / Locked |
| Email | ✅ Yes | For notifications and password reset |
| Mobile | No | For OTP-based MFA |
| Department | No | For scoping data visibility |
| Effective From / To | No | Time-bounded access |

### 16.3 Module-Level Permissions

For each user, permissions can be granted per module per action:

| Module | View | Create | Edit | Delete | Approve |
|---|---|---|---|---|---|
| Company Setup | ☐ | ☐ | ☐ | ☐ | — |
| Employee Master | ☐ | ☐ | ☐ | ☐ | — |
| Attendance | ☐ | ☐ | ☐ | ☐ | ☐ |
| Leave Management | ☐ | ☐ | ☐ | ☐ | ☐ |
| Payroll | ☐ | ☐ | ☐ | ☐ | ☐ |
| Statutory Compliance | ☐ | ☐ | ☐ | ☐ | — |
| Reports | ☐ | ☐ | ☐ | — | — |
| User Management | ☐ | ☐ | ☐ | ☐ | — |
| Plant Management | ☐ | ☐ | ☐ | ☐ | — |

### 16.4 Access Differentiation: Super Admin vs Company Admin

| Capability | Super Admin | Company Admin |
|---|---|---|
| View all companies | ✅ | ❌ (Own company only) |
| Add new company | ✅ | ❌ |
| Delete company | ✅ | ❌ |
| Edit General Info | ✅ Full | ❌ Read-only |
| Edit Time Management | ✅ | ✅ |
| Edit Controls | ✅ | ✅ |
| Add users | ✅ All companies | ✅ Own company |
| Change company status | ✅ | ❌ |

---

## 17. Bulk Data Import

The Super Admin can import bulk data for Company Master, IOT Reason, and No Series records using CSV or Excel files.

### 17.1 Import Workflow

**Step 1 — Select Master & Download Template**
- Choose import target: Company Master / IOT Reason / No Series
- Download the sample template (pre-formatted CSV/Excel with column headers)

**Step 2 — Upload File**
- Drag-and-drop or click-to-browse
- Supported formats: `.csv`, `.xlsx`
- File size limit: 5 MB (recommended)

**Step 3 — Duplicate Handling**
| Mode | Behaviour |
|---|---|
| Skip Existing | Imported records that match existing keys are ignored; current records remain unchanged |
| Overwrite Existing | Imported records replace matching existing records |

**Step 4 — Preview**
- System shows a preview table of parsed records before import
- Displays record count and column mapping
- Validation errors are highlighted in red

**Step 5 — Confirm Import**
- Click "✓ Import Records" to execute
- System shows success/failure summary after import

### 17.2 Importable Masters

| Master | Key Fields | Template Columns |
|---|---|---|
| Company Master | Company Code, Name, Industry, Country, Status | code, name, short_name, industry, country, status, gst, employees |
| IOT Reason | Reason Type, Reason, Description, Department | reason_type, reason, description, department, planned, duration |
| No Series | Code, Description, Linked Screen, Prefix, Suffix, Count, Start | code, description, linked_screen, prefix, suffix, num_count, start_num |

---

## 18. Tenant Provisioning Checklist

Use this checklist to ensure no step is missed during onboarding:

### Phase 1: Company Identity
- [ ] Company logo uploaded
- [ ] Display name and legal name filled
- [ ] Business type and industry selected
- [ ] Company code confirmed (auto-generated or custom)
- [ ] Date of incorporation entered
- [ ] CIN number entered
- [ ] Corporate email domain verified
- [ ] Website URL saved

### Phase 2: Compliance & Statutory
- [ ] PAN entered and verified
- [ ] TAN entered
- [ ] GSTIN entered (if applicable)
- [ ] PF Registration Number entered
- [ ] ESI Employer Code entered (if applicable)
- [ ] PT Registration entered (if applicable)
- [ ] LWFR Number entered (if applicable)
- [ ] ROC Filing State selected

### Phase 3: Address
- [ ] Registered address complete (Line 1, City, State, PIN)
- [ ] Corporate/HQ address confirmed or marked same as registered

### Phase 4: Fiscal & Calendar
- [ ] Financial year period selected
- [ ] Payroll frequency and cutoff day configured
- [ ] Disbursement day set
- [ ] Week start and timezone configured
- [ ] Working days selected

### Phase 5: Preferences & Feature Flags
- [ ] Currency and language set
- [ ] Date format selected
- [ ] Statutory compliance mode toggled
- [ ] ESS portal enabled/disabled
- [ ] Mobile app access configured
- [ ] Required integrations enabled (biometric, e-sign, etc.)

### Phase 6: Locations
- [ ] All branches added with addresses and geo-fencing radii
- [ ] Multi-plant mode enabled (if applicable)
- [ ] All plants added with codes, types, and addresses
- [ ] HQ plant designated
- [ ] State-wise GSTINs assigned to plants

### Phase 7: Contacts
- [ ] Primary contact added
- [ ] HR contact added
- [ ] Finance contact added

### Phase 8: Time Management
- [ ] Day boundary configured
- [ ] Weekly off days set
- [ ] All shifts created (Morning, General, Afternoon, Night as applicable)
- [ ] Planned downtime slots added per shift

### Phase 9: Configuration Masters
- [ ] No Series records created for all required modules
- [ ] IOT Reason master populated (if production/manufacturing)
- [ ] System controls reviewed and configured

### Phase 10: User Access
- [ ] Company Admin user created
- [ ] All required user accounts created
- [ ] Role assignments confirmed
- [ ] Module permissions reviewed

### Phase 11: Activation
- [ ] Company status changed from Draft → Active
- [ ] Test login performed by Company Admin
- [ ] First payroll run verified in staging
- [ ] Go-live date recorded

---

## 19. Audit Trail & Change Logging

Every configuration change made during and after onboarding should be captured in the audit log.

| Logged Event | Details Captured |
|---|---|
| Company Created | Timestamp, Super Admin ID, Company Code |
| Field Updated | Field name, old value, new value, changed by, timestamp |
| Status Changed | Old status, new status, changed by |
| User Added/Removed | User ID, role, changed by, timestamp |
| Feature Toggle Changed | Feature name, old state, new state |
| Plant Added/Edited | Plant code, changed fields |
| Shift Added/Modified | Shift name, changed fields |
| No Series Modified | Series code, field changed |
| Import Executed | Import target, records imported/skipped/failed |
| Login/Logout Events | User, timestamp, IP address |

---

## 20. Multi-Tenant Architecture Notes

### 20.1 Data Isolation

Each tenant (company) in Avy ERP operates in a **fully isolated data partition**. There is no data leakage between tenants. The Super Admin has cross-tenant visibility but cannot mix or transfer data between companies.

### 20.2 Subdomain / URL Structure

Each tenant is typically accessible at a unique URL or identifier:
```
https://avyerp.com/tenant/AVR-IN-001/
https://avyerp.com/tenant/NEX-IN-002/
```

### 20.3 Module Activation Per Tenant

Each module (HRMS, Payroll, Production, Quality, Inventory, Finance) can be independently activated or deactivated per tenant, based on subscription.

### 20.4 Tenant Suspension & Reactivation

When a tenant is suspended (e.g., for non-payment), employees cannot log in, but Super Admin retains read access to the tenant's data for audit/recovery purposes.

### 20.5 Data Portability & Offboarding

When a tenant is permanently offboarded:
- Final data export (CSV/Excel/PDF) must be generated and provided
- All data is archived for a regulatory retention period (typically 7 years)
- After retention period, data is purged as per data destruction policy

---

*Document End — Avy ERP Tenant Onboarding Guide (Super Admin) v1.0*  
*Maintained by Avyren Technologies — Product Team*
