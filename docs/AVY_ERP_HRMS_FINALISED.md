# Avy ERP — HRMS Module Configuration Guide
## Comprehensive HRMS Setup, Transactional Operations & Integration Reference

> **Document Code:** AVY-HRMS-CFG-002  
> **Module:** HRMS (Human Resource Management System)  
> **Audience:** HR Administrators, Payroll Managers, System Administrators, CHRO  
> **Version:** 2.1  
> **Product:** Avy ERP (Avyren Technologies)  
> **Supersedes:** AVY-HRMS-CFG-001 v1.0

---

## Table of Contents

1. [Overview & HRMS Module Scope](#1-overview--hrms-module-scope)
2. [Pre-Configured Data Inherited from Tenant Onboarding](#2-pre-configured-data-inherited-from-tenant-onboarding)
3. [HRMS Configuration Screen Architecture](#3-hrms-configuration-screen-architecture)
4. [Organisational Structure Configuration](#4-organisational-structure-configuration)
5. [Employee Master & Core Data Configuration](#5-employee-master--core-data-configuration)
6. [Attendance Management Configuration](#6-attendance-management-configuration)
7. [Leave Management Configuration](#7-leave-management-configuration)
8. [Payroll Configuration](#8-payroll-configuration)
9. [Statutory Compliance Configuration](#9-statutory-compliance-configuration)
10. [TDS & Income Tax Configuration](#10-tds--income-tax-configuration)
11. [Employee Self-Service (ESS) Portal Configuration](#11-employee-self-service-ess-portal-configuration)
12. [Role-Based Access Control (RBAC) Configuration](#12-role-based-access-control-rbac-configuration)
13. [Approval Workflows & Automation Configuration](#13-approval-workflows--automation-configuration)
14. [Notification & Communication Configuration](#14-notification--communication-configuration)
15. [Data Retention Policy Configuration](#15-data-retention-policy-configuration)
16. [Recruitment & ATS Transactional Operations](#16-recruitment--ats-transactional-operations)
17. [Employee Hub — Onboarding & Lifecycle Transactions](#17-employee-hub--onboarding--lifecycle-transactions)
18. [Payroll Run — Transactional Operations](#18-payroll-run--transactional-operations)
19. [HR Operations — Daily Transactional Operations](#19-hr-operations--daily-transactional-operations)
20. [Employee Offboarding & Full & Final (F&F) Configuration](#20-employee-offboarding--full--final-ff-configuration) *(incl. 20.4 F&F by Separation Type)*
21. [Performance Management Configuration & Transactions](#21-performance-management-configuration--transactions) *(incl. 21.8 Employee Engagement, 21.9 Industry Presets)*
22. [Training & Learning Management Configuration](#22-training--learning-management-configuration)
23. [Loan, Advance & Reimbursement Configuration](#23-loan-advance--reimbursement-configuration)
24. [Asset Management Configuration](#24-asset-management-configuration)
25. [Travel & Expense Management Configuration](#25-travel--expense-management-configuration)
26. [HR Letters & Certificates](#26-hr-letters--certificates)
27. [Grievance & Discipline Management](#27-grievance--discipline-management)
28. [Statutory Compliance Operations Dashboard](#28-statutory-compliance-operations-dashboard)
29. [Audit Trail & Data Governance](#29-audit-trail--data-governance)
30. [Reports & Analytics Configuration](#30-reports--analytics-configuration)
31. [HRMS Integration with Other Modules & External Systems](#31-hrms-integration-with-other-modules--external-systems)
32. [HRMS Go-Live Readiness Checklist](#32-hrms-go-live-readiness-checklist)

---

## 1. Overview & HRMS Module Scope

The HRMS module in Avy ERP is the **central system of record for all people-related data** in an organisation. It covers the full employee lifecycle — from recruitment and onboarding to payroll, compliance, performance, and exit.

### 1.1 HRMS Sub-Modules

```
HRMS
├── Organisational Structure (Departments, Designations, Grades, Cost Centres)
├── Employee Master (Core employee data, documents, history)
├── Recruitment & ATS (Applicant Tracking — Requisition to Hire)
├── Onboarding (Joining workflow, document collection, checklist)
├── Attendance Management (Biometric, Mobile GPS, Manual, Rotational)
├── Leave Management (Leave types, policies, approvals, holiday calendar)
├── Payroll (Salary structures, 6-step run wizard, disbursement)
├── Statutory Compliance (PF, ESI, PT, Gratuity, Bonus, LWF)
├── TDS & Income Tax (Form 16, 24Q, IT declarations, perquisites)
├── Employee Self-Service Portal (ESS)
├── Manager Self-Service (MSS)
├── Performance Management (KRA/OKR, Appraisals, 360°, Succession)
├── Training & Development (LMS, Skill Mapping)
├── Loan & Advance Management
├── Travel & Expense Management
├── Asset Management (Employee-assigned assets)
├── HR Letters & Certificates (Auto-generated documents)
├── Grievance & Discipline Management (SCN, PIP, Warnings)
├── Role-Based Access Control (RBAC, Field-Level Permissions)
├── Notification & Workflow Engine
└── Offboarding & Full & Final Settlement (F&F)
```

### 1.2 HRMS Data Flow Overview

```
Org Structure  →  Employee Master  →  Attendance & Leave
                                            ↓
                     Recruitment  ─────►  Payroll Engine
                     Onboarding              ↓
                                    Statutory Compliance
                                     (PF, ESI, PT, TDS)
                                            ↓
                                    Bank Disbursement
                                            ↓
                               Finance / GL Integration
                                            ↓
                              Performance → Training → Succession
                                            ↓
                                       Exit & F&F
```

### 1.3 Mobile-First & Smart Configuration Philosophy

Avy ERP HRMS follows a **mobile-first, single-page smart sections** philosophy:

- Every configuration page is a single scrollable page with collapsible smart sections
- Fields are **context-aware** — they appear only when relevant
- Tooltips, inline help text, and smart defaults eliminate the need for a separate manual
- Setup can be completed end-to-end from any mobile device in under 20 minutes
- The 32 original configuration screens are consolidated into **6 Smart Configuration Pages**
- The 28 original transactional screens are consolidated into **6 Smart Transactional Pages**

---

## 2. Pre-Configured Data Inherited from Tenant Onboarding

The following data is **already configured** during Super Admin tenant onboarding (AVY-CFG-001) and is directly inherited by the HRMS module. No re-entry is required; however, HR Admin must **verify** accuracy before activating payroll.

### 2.1 Company Identity Data — Inherited

| Data | Source (Onboarding Tab) | Used In HRMS |
|---|---|---|
| Company Display Name | Company Profile | Payslips, offer letters, ESS portal header |
| Company Logo | Company Profile | Payslips, form templates, reports |
| Legal / Registered Name | Company Profile | Form 16, Form 24Q, statutory certificates |
| Business Type | Company Profile | Gratuity threshold, bonus applicability logic |
| Industry Type | Company Profile | Compliance defaults (ESI threshold, etc.) |
| Date of Incorporation | Company Profile | Gratuity liability calculation |
| Corporate Email Domain | Company Profile | Auto-provisioning employee email IDs |
| Company Code | Company Profile | Employee ID prefixing, document numbering |
| Number of Employees | Company Profile | ESI applicability check (threshold: 10 employees) |

### 2.2 Statutory & Tax Data — Inherited

| Data | Source | Used In HRMS |
|---|---|---|
| PAN | Compliance Tab | Form 16, Form 26AS reconciliation, TDS returns |
| TAN | Compliance Tab | TDS deduction, Form 24Q quarterly returns |
| GSTIN | Compliance Tab | Expense reimbursements with GST |
| PF Registration No. | Compliance Tab | Monthly PF ECR (Electronic Challan cum Return) |
| ESI Employer Code | Compliance Tab | Monthly ESI challan, semi-annual returns |
| PT Registration No. | Compliance Tab | Monthly/quarterly PT deductions and remittance |
| LWFR Number | Compliance Tab | LWF deduction |
| ROC Filing State | Compliance Tab | Jurisdiction for labour law compliance |

### 2.3 Address & Contact Data — Inherited

| Data | Source | Used In HRMS |
|---|---|---|
| Registered Address | Address Tab | Statutory certificates, Form 16 |
| Corporate Address | Address Tab | Payslips, offer letters |
| Key Contacts (HR Contact) | Contacts Tab | Escalation matrix, system notifications |
| Key Contacts (Finance Contact) | Contacts Tab | Payroll approval and payment routing |

### 2.4 Calendar & Fiscal Data — Inherited

| Data | Source | Used In HRMS |
|---|---|---|
| Financial Year | Fiscal Tab | Payroll year boundaries, Leave year reset |
| Payroll Frequency | Fiscal Tab | Monthly/weekly payroll cycle |
| Payroll Cut-off Day | Fiscal Tab | Attendance freeze date for payroll |
| Disbursement Day | Fiscal Tab | Salary credit date |
| Timezone | Fiscal Tab | Attendance punch timestamps |
| Week Start Day | Fiscal Tab | Week-wise attendance and leave calculations |
| Working Days | Fiscal Tab | Daily wage calculation, LOP deduction |

### 2.5 Branch, Location & Shift Data — Inherited

| Data | Source | Used In HRMS |
|---|---|---|
| Branch List | Branch Tab | Employee assignment to branch, payroll grouping |
| Branch Addresses | Branch Tab | Branch-specific documents |
| Geo-Fencing Radius | Branch Tab | Mobile/GPS attendance boundary |
| Plant List | Plants Tab | Employee-to-plant mapping, shift assignment |
| Shift Master | Time Mgmt Tab | Employee shift assignment, attendance calculation |

### 2.6 System Preferences — Inherited

| Data | Source | Used In HRMS |
|---|---|---|
| Currency | Preferences Tab | All salary and payment amounts |
| Language | Preferences Tab | ESS portal UI language |
| Date Format | Preferences Tab | All date displays across HRMS |
| India Statutory Compliance Mode | Preferences Tab | Activates PF/ESI/PT/TDS computation engines |
| ESS Portal Toggle | Preferences Tab | Enables/disables employee self-service access |
| Mobile App Toggle | Preferences Tab | Enables mobile attendance, payslips, etc. |
| Biometric Sync Toggle | Preferences Tab | Enables attendance sync from biometric devices |

> **Important:** HR Admin must verify all inherited data before running the first payroll. Incorrect statutory identifiers will cause compliance failures.

---

## 3. HRMS Configuration Screen Architecture

### 3.1 Configuration Module: 32 Screens → 6 Smart Pages

The HRMS configuration module consolidates 32 original screens into 6 smart, scrollable pages to reduce setup time and cognitive load.

| Smart Page | Original CFG Screens Merged | Old Count | New Count |
|---|---|---|---|
| **Page 1 · Company & Organisation** | CFG-001 Company Master, CFG-002 Branch/Location, CFG-003 Department, CFG-004 Designation, CFG-005 Grade/Band, CFG-031 Notifications | 6 | 1 |
| **Page 2 · People & Policies** | CFG-006 Employee Type, CFG-013 Leave Policy, CFG-021 Probation Rules, CFG-022 Appraisal Config, CFG-023 Training Master, CFG-024 Document Types, CFG-025 Asset Categories, CFG-026 Grievance Setup | 8 | 1 |
| **Page 3 · Payroll & Compliance** | CFG-010 Pay Components, CFG-011 Tax Slabs, CFG-012 PF/ESI/PT Rules, CFG-014 Bank Master, CFG-020 Loan Policy, CFG-028 Salary Structure Templates | 6 | 1 |
| **Page 4 · Attendance & Time** | CFG-007 Shift Master, CFG-008 Holiday Calendar, CFG-009 Work Week/Roster, CFG-027 Biometric/Device, CFG-029 Geo-fence Zones, CFG-030 Overtime Rules | 6 | 1 |
| **Page 5 · Roles, Access & Workflows** | CFG-015 RBAC/User Roles, CFG-016 Field-Level Permissions, CFG-017 Workflow Designer, CFG-018 Approval Chains, CFG-019 Notification Rules, CFG-032 Data Retention | 6 | 1 |
| **Page 6 · Integrations & Advanced** | CFG-027 API Connectors, CFG-030 AI Chatbot Config, E-Sign Setup, ERP Connectors, Banking Config, EPFO/ESIC Portal Links | 6 | 1 |
| **TOTAL** | **All 32 CFG screens** | **32** | **6** |

### 3.2 Transactional Module: 28 Screens → 6 Smart Pages

The HRMS transactional module consolidates 28 original screens into 6 smart pages.

| Smart Page | Original TRN Screens Merged | Old Count | New Count |
|---|---|---|---|
| **Page 1 · Recruitment & ATS** | TRN-001 Job Requisition, TRN-002 Candidate Entry, TRN-003 Interview Scheduler, TRN-004 Assessment Tracker, TRN-005 Offer Letter | 5 | 1 |
| **Page 2 · Employee Hub** | TRN-010 Employee Master, TRN-006 Onboarding Checklist, TRN-007 Confirmation Tracking, TRN-008 Transfer/Promotion | 4 | 1 |
| **Page 3 · Payroll Run** | TRN-016 Payroll Processor, TRN-017 Hold Salary, TRN-018 F&F Settlement, TRN-019 Arrear Pay, TRN-020 Salary Revision | 5 | 1 |
| **Page 4 · HR Operations** | TRN-011 Attendance Adj, TRN-012 Leave Override, TRN-013 Bonus Upload, TRN-014 Loan/Advance, TRN-015 Asset Issuance | 5 | 1 |
| **Page 5 · Performance** | TRN-021 Goal/OKR, TRN-022 360° Feedback, TRN-023 Appraisal Rating, TRN-024 Skill Mapping, TRN-025 Training Tracker, TRN-026 Succession | 6 | 1 |
| **Page 6 · Exit & Separation** | TRN-009 Resignation/Exit Form, TRN-027 Separation Clearance Dashboard, TRN-028 Payroll Exception Manager | 3 | 1 |
| **TOTAL** | **All 28 TRN screens** | **28** | **6** |

### 3.3 Smart Configuration Setup Flow

```
CFG Page 1: Company & Organisation  →
CFG Page 2: People & Policies       →
CFG Page 3: Payroll & Compliance    →
CFG Page 4: Attendance & Time       →
CFG Page 5: Roles & Workflows       →
CFG Page 6: Integrations & Advanced →
  GO LIVE → Begin Transactional Operations
```

---

## 4. Organisational Structure Configuration

*(CFG-001 through CFG-006 — mapped to Smart Config Page 1)*

### 4.1 Department Master

Define all departments in the organisation. Departments drive payroll cost centre allocation, leave policy assignment, and approval routing.

| Field | Required | Notes |
|---|---|---|
| Department Name | ✅ Yes | e.g., "Human Resources", "Engineering", "Finance", "Sales" |
| Department Code | ✅ Yes | Unique code; e.g., `HR-001`, `ENG-001`, `FIN-001` |
| Department Head | No | Employee designated as head of department |
| Parent Department | No | For nested/hierarchical department structures |
| Cost Centre Code | No | Links to Finance module for payroll cost booking |
| Status | ✅ Yes | Active / Inactive |

**UX Feature:** Departments are added inline via "+ Add" chip — no separate screen. A live tree-view org hierarchy builds on the right as departments are added.

**Sample Data:**

| Department | Code | Parent Dept | Cost Centre | Head | Positions |
|---|---|---|---|---|---|
| Engineering | ENG-001 | Technology | CC-ENG-001 | Rajesh Kumar | 45 |
| Human Resources | HR-001 | Corporate | CC-HR-001 | Sunita Rao | 12 |
| Finance & Accounts | FIN-001 | Corporate | CC-FIN-001 | Vijay Menon | 18 |
| Sales & Marketing | SAL-001 | Business | CC-SAL-001 | Deepa Nair | 32 |
| IT Infrastructure | IT-001 | Technology | CC-IT-001 | Suresh Babu | 20 |

### 4.2 Designation / Job Title Master

| Field | Required | Notes |
|---|---|---|
| Designation Name | ✅ Yes | e.g., "Software Engineer", "Senior Manager", "HR Executive" |
| Designation Code | ✅ Yes | Unique short code; e.g., `SE-L3`, `SSE-L4`, `EM-L5` |
| Department | No | Default department for this designation |
| Grade / Band | No | Links to the Grade Master for salary range reference |
| Job Level | No | L1 / L2 / L3 (Junior) / L4 (Senior) / L5 (Lead/Manager) / L6 (Director) / L7 (VP) |
| Managerial Flag | No | Yes / No — determines if this role has reportees |
| Reports To | No | Designations this role reports to |
| Probation Period | No | Default probation period for this designation (in days) |
| Status | ✅ Yes | Active / Inactive |

**Sample Data:**

| Designation | Code | Grade Band | Managerial | Reports To | Probation |
|---|---|---|---|---|---|
| Software Engineer | SE-L3 | G3–G4 | No | Tech Lead L4 | 90 days |
| Senior Software Engineer | SSE-L4 | G4–G5 | No | Engg. Manager L5 | 60 days |
| Engineering Manager | EM-L5 | G5–G6 | Yes | VP Engineering L7 | 90 days |
| Product Manager | PM-L5 | G5–G6 | Yes | VP Product L7 | 90 days |
| HR Business Partner | HRBP-L4 | G4–G5 | No | HR Manager L5 | 60 days |

### 4.3 Grade / Band / Level Master

Grades define salary bands and benefit entitlements for employees grouped at similar levels.

| Field | Required | Notes |
|---|---|---|
| Grade Code | ✅ Yes | e.g., `G1`, `G2`, `G3`, `G4`, `G5`, `M1`, `E1` |
| Grade Name | ✅ Yes | e.g., "Associate", "Junior", "Senior", "Lead", "Manager", "VP" |
| CTC Range (Min) | No | Minimum CTC for this grade |
| CTC Range (Max) | No | Maximum CTC for this grade; system warns if revision exceeds band |
| HRA Percentage | No | Grade-specific HRA entitlement (e.g., 40% or 50% of Basic) |
| PF Tier | No | Applicable / Not Applicable; links to PF rules |
| Benefit Eligibility | No | Flags for vehicle allowance, club membership, company accommodation |
| Probation Period (months) | No | Default probation period for this grade |
| Notice Period (days) | No | Default notice period |
| Status | ✅ Yes | Active / Inactive |

**Sample Grade Structure:**

| Grade Code | Grade Name | Pay Min | Pay Max | PF | HRA Slab |
|---|---|---|---|---|---|
| G1 | Associate | ₹18,000 | ₹28,000 | Applicable | 40% |
| G2 | Junior | ₹28,001 | ₹45,000 | Applicable | 40% |
| G3 | Senior | ₹45,001 | ₹80,000 | Applicable | 40% |
| G4 | Lead | ₹80,001 | ₹1,50,000 | Applicable | 50% |
| G5 | Manager | ₹1,50,001 | ₹3,00,000 | Applicable | 50% |
| G6 | Senior Manager | ₹3,00,001 | ₹6,00,000 | Optional | 50% |
| G7 | Director | ₹6,00,001 | ₹12,00,000 | Optional | 50% |

### 4.4 Employee Type Master

Define all categories of employees. Each type carries statutory applicability flags that drive compliance calculations automatically.

| Field | Required | Notes |
|---|---|---|
| Type Name | ✅ Yes | e.g., Permanent, Contractual, Intern, Consultant, Apprentice, Part-Time |
| Type Code | ✅ Yes | e.g., `FTP-001`, `CTR-002`, `INT-003`, `CON-004`, `PRT-005` |
| PF Applicable | ✅ Yes | Toggle — Yes / No |
| ESI Applicable | ✅ Yes | Toggle — Yes / No |
| PT Applicable | ✅ Yes | Toggle — Yes / No |
| Gratuity Eligible | ✅ Yes | Toggle — Yes / No |
| Bonus Eligible | ✅ Yes | Toggle — Yes / No (under Payment of Bonus Act) |
| Default Contract Template | No | Assign offer letter / appointment letter template to this type |
| Status | ✅ Yes | Active / Inactive |

**Statutory Flags by Employee Type:**

| Employee Type | Code | PF | ESI | PT | Bonus | Gratuity |
|---|---|---|---|---|---|---|
| Full-Time Permanent | FTP-001 | Yes | Yes | Yes | Yes | Yes |
| Contractual / Fixed Term | CTR-002 | Yes | Yes | Yes | No | Conditional |
| Intern / Trainee | INT-003 | No | No | No | No | No |
| Consultant / Freelancer | CON-004 | No | No | No | No | No |
| Part-Time | PRT-005 | No | Yes | No | No | No |
| Apprentice | APR-006 | No | No | No | No | No |

### 4.5 Reporting Structure / Hierarchy

| Feature | Configuration |
|---|---|
| Reporting Manager | Each employee is linked to a direct reporting manager |
| Functional Manager | Secondary manager for matrix organisations |
| Skip-Level Manager | For escalation and bypass approvals |
| HR Business Partner | Dedicated HR person per department/unit |
| Org Chart | Visual hierarchical chart auto-generated from reporting relationships |
| Approval Chain | Configures multi-level approval routing (Leave → Manager → HR → Director) |

### 4.6 Cost Centre Master

| Field | Required | Notes |
|---|---|---|
| Cost Centre Code | ✅ Yes | Linked to Finance / Accounts module |
| Cost Centre Name | ✅ Yes | e.g., "Engineering — Bengaluru" |
| Linked Department | No | Department whose payroll costs are booked here |
| Linked Plant | No | For manufacturing cost centres |
| Budget (Annual) | No | For cost control tracking |
| GL Account Code | No | General Ledger account for payroll journal entries |

### 4.7 Work Location Categories

| Category | Options |
|---|---|
| Work Type | On-site, Remote, Hybrid |
| Employment Type | Full-time, Part-time, Contract, Intern, Consultant, Apprentice |
| Employment Category | Permanent, Fixed-Term, Probationary, Trainee |
| Work Calendar | India Standard (Mon–Fri), US Calendar, 24×7 Rotation, Custom |

### 4.8 Production Incentive Configuration (Manufacturing)

For manufacturing companies, configure machine-wise production incentives linked to HRMS payroll.

| Setting | Description |
|---|---|
| Incentive Basis | Component-wise, Model-wise, Finish Part-wise |
| Slab-Based Payout | Define output slabs and corresponding incentive amounts |
| Machine Assignment | Link employee/operator to specific machines |
| Incentive Period | Daily / Weekly / Monthly calculation cycle |
| Payroll Integration | Auto-include computed incentive in monthly payroll run |
| Department Linkage | Link production incentive to manufacturing department |

**Sample Production Incentive Slab (Machine-Wise):**

| Output Units (Daily) | Incentive Amount |
|---|---|
| Below 100 units | ₹0 (Base only) |
| 100 – 120 units | ₹500 |
| 121 – 150 units | ₹800 |
| 151 – 180 units | ₹1,200 |
| Above 180 units | ₹1,500 |

Incentive amounts are auto-computed daily from production module data and aggregated monthly before inclusion in the payroll run. The payroll component is tagged as "Production Incentive (OT)" and is fully taxable.

---

## 5. Employee Master & Core Data Configuration

### 5.1 Employee ID Numbering

The Employee ID format is configured via the **No Series master** (inherited from onboarding, linked screen: "Employee Onboarding").

| Example Format | Config |
|---|---|
| `EMP-00001` | Prefix: `EMP-`, Count: 5, Start: 1 |
| `AVR-2026-0001` | Prefix: `AVR-2026-`, Count: 4 |
| `TMP-001` (for Contractual) | Separate No Series per category |

> **UX Feature:** Employee ID is auto-generated on final form submission; displayed as read-only preview during data entry.

### 5.2 Employee Personal Information

| Field | Required | Notes |
|---|---|---|
| Employee ID | ✅ Auto | Auto-generated from No Series on submission |
| First Name | ✅ Yes | |
| Middle Name | No | |
| Last Name | ✅ Yes | |
| Date of Birth | ✅ Yes | For age-based compliance (retirement, ESI threshold age, etc.) |
| Gender | ✅ Yes | Male, Female, Non-Binary, Prefer not to say |
| Marital Status | No | Single, Married, Divorced, Widowed |
| Blood Group | No | For emergency records |
| Father's / Mother's Name | No | For statutory forms |
| Nationality | ✅ Yes | Indian / Foreign National |
| Religion | No | Optional; for HR demographic surveys |
| Category | No | General, OBC, SC, ST (for government contract compliance) |
| Differently Abled | No | Flag + type; for Persons with Disabilities Act compliance |
| Profile Photo | No | Photo for ID card, ESS portal, payslips |

### 5.3 Employee Contact Information

| Field | Required | Notes |
|---|---|---|
| Personal Mobile | ✅ Yes | Primary contact number |
| Alternative Mobile | No | Secondary contact number |
| Personal Email | ✅ Yes | Pre-join communication; also for ESS login |
| Official Email | No | Auto-generated from corporate email domain post-join |
| Current Residential Address | ✅ Yes | Full address with city, state, PIN |
| Permanent Address | No | If different from current; used for Form 16 |
| Emergency Contact Name | ✅ Yes | Person to contact in emergency |
| Emergency Contact Relation | ✅ Yes | Spouse, Parent, Sibling, Friend, etc. |
| Emergency Contact Mobile | ✅ Yes | |

### 5.4 Employment Details (New Hire — 6-Tab Form)

The new hire entry form has **6 smart tabs** with auto-save. Offer letter acceptance auto-imports professional details to pre-fill the form.

**Tab 1 — Personal Information:**
- Name, DOB, Gender, Aadhaar (masked), PAN, Current & Permanent Address, Emergency Contact

**Tab 2 — Professional Details:**

| Field | Required | Notes |
|---|---|---|
| Joining Date | ✅ Yes | Official joining date; drives all tenure calculations |
| Employee Type | ✅ Yes | From Employee Type Master |
| Department | ✅ Yes | From Department Master |
| Designation | ✅ Yes | From Designation Master |
| Grade / Band | No | From Grade Master |
| Reporting Manager | ✅ Yes | Direct reporting manager |
| Functional Manager | No | Dotted-line manager (matrix structure) |
| Work Location | ✅ Yes | From Branch/Location Master (On-site, Remote, Hybrid) |
| Shift | No | Default shift assignment |
| Cost Centre | No | For payroll cost allocation |
| Notice Period | No | Auto-set from designation/grade; editable |
| Work Calendar | No | India Standard (Mon–Fri), US Calendar, 24×7 Rotation |
| Branch / Location | ✅ Yes | |
| Plant | No | If multi-plant company |
| Probation End Date | Auto | Auto-calculated from joining date + grade probation period |
| Confirmation Reminder | Auto | Alert sent 30 days before probation end |

**Tab 3 — Salary & CTC:**
- Annual CTC (₹ LPA), Salary Structure Template (auto-applies from grade), CTC Breakup Preview, Payment Mode (NEFT / IMPS / Cheque)

**Tab 4 — Bank Details:**
- IFSC Code (auto-lookups bank name, branch, city), Account Number (with confirmation), Account Type (Savings / Current)

**Tab 5 — Documents:**
- Upload: Aadhaar, PAN, profile photo, education certificates, previous offer letter, experience & relieving letters

**Tab 6 — Emergency & Final Review:**
- Emergency contact verification, full data review, submit → Employee ID auto-generated → onboarding checklist auto-triggered

### 5.5 Statutory & Identity Documents

| Document | Field | Validation / Notes |
|---|---|---|
| PAN Card | PAN Number | 10-char alphanumeric; required for TDS |
| Aadhaar Card | Aadhaar Number | 12-digit; masked display (`XXXX XXXX 4521`); required for UAN |
| Passport | Passport Number, Expiry Date | For foreign national employees |
| Driving Licence | DL Number, Expiry Date | Optional |
| Voter ID | Voter ID Number | Optional |
| UAN | Universal Account Number (PF) | Auto-fetched or manually entered; required for PF ECR |
| ESI IP Number | Insurance Policy Number | Auto-assigned on ESI registration |
| Bank Account No. | Primary salary account | For payroll disbursement |
| Bank IFSC Code | Auto-validates bank & branch | |
| Bank Name & Branch | Auto-filled from IFSC | |
| Account Type | Savings / Current | |
| PRAN | Permanent Retirement Account No. | For NPS-enrolled employees |

### 5.6 Nominee / Beneficiary Details

| Field | Notes |
|---|---|
| Nominee Name | For PF, Gratuity, Group Insurance |
| Relation to Employee | Spouse, Child, Parent, Sibling |
| Nominee Date of Birth | |
| Nominee Share % | If multiple nominees — must sum to 100% |
| Nominee Aadhaar / PAN | For identification |
| Nominee Address | |

### 5.7 Education & Qualification

| Field | Notes |
|---|---|
| Highest Qualification | Graduate, Post-Graduate, Doctorate, Diploma, etc. |
| Degree / Course Name | e.g., B.Tech CSE, MBA HR |
| Institution Name | |
| University / Board | |
| Year of Passing | |
| Marks / CGPA | |
| Certificate Upload | PDF/image of mark sheet / degree |

### 5.8 Previous Employment

| Field | Notes |
|---|---|
| Previous Employer Name | |
| Designation Held | |
| Last CTC | |
| Date of Joining / Leaving | |
| Reason for Leaving | |
| Experience Letter | Upload |
| Relieving Letter | Upload |
| Previous PF Account Number | For PF transfer |

### 5.9 Employee Custom Fields

| Config Option | Description |
|---|---|
| Field Type | Text, Number, Date, Dropdown, Checkbox, File Upload |
| Field Label | Custom name |
| Applicable Section | Personal / Employment / Statutory |
| Mandatory | Yes / No |

### 5.10 Employee Timeline & Lifecycle Events

All lifecycle events are auto-logged in the employee's timeline view:

| Event | Auto-logged |
|---|---|
| Offer letter accepted → Employee ID generated | ✅ |
| Onboarding checklist created | ✅ |
| Probation end reminder triggered | ✅ |
| Confirmation letter generated | ✅ |
| Transfer / Promotion with org chart update | ✅ |
| Salary revision with revision letter | ✅ |
| Resignation / Exit initiation | ✅ |

---

## 6. Attendance Management Configuration

*(CFG-007, CFG-008, CFG-009, CFG-027, CFG-029, CFG-030 — mapped to Smart Config Page 4)*

### 6.1 Attendance Capture Methods

| Method | Description |
|---|---|
| Biometric (Fingerprint) | Integration with ZKTeco, ESSL, Realtime, BioEnable, Mantra devices |
| Face Recognition | Camera-based facial recognition; live match at entry/exit |
| Smart Card / RFID | Card-to-employee mapping; reader IP config |
| Mobile App / GPS | Employee punches via mobile app within geo-fence boundary; selfie capture optional |
| Web / ESS Portal | Manual clock-in via browser; requires manager approval |
| Manual Entry | HR enters attendance; approval required |
| IoT / Integration | Attendance from production machines / access control systems |

### 6.2 Biometric Device Configuration

| Config | Description |
|---|---|
| Device Brand | ZKTeco, ESSL, Realtime, BioEnable, Mantra, etc. |
| Device IP / Port | Network address of the device |
| Device ID | Unique device identifier |
| Sync Mode | Real-time Push, Scheduled Pull (every N minutes), Manual |
| Sync Schedule | Pull interval in minutes (e.g., every 5 min) |
| Test Connection | Live test button shows green/red status |
| Employee Enrollment | Enroll fingerprints/face via device or via software |
| Device Location Mapping | Map device to branch/plant for auto-assignment |
| Failed Sync Alert | Notify IT if device loses connectivity |

### 6.3 Geo-Fence Zone Configuration

| Config | Description |
|---|---|
| Zone Name | Linked to branch/location |
| Map-Based Drawing | Draw a circle around the office on an embedded map |
| Radius | 50m to 500m; configurable per location |
| Location Assignment | Assign geo-fence zone to one or more branches |
| Selfie Capture Toggle | Require selfie photo on mobile punch |
| GPS Tolerance | Buffer allowance for GPS accuracy |

### 6.4 Shift Master Configuration

| Field | Description |
|---|---|
| Shift Name & Code | e.g., "General Shift (GS-001)", "Night Shift (NS-004)" |
| Start & End Time | Via drag on 24-hour visual bar; or direct time entry |
| Grace Period | Slider: 0–60 minutes (late-in tolerance) |
| Break Duration | Scheduled break in minutes |
| Night Shift Flag | Auto-flagged if shift spans midnight |
| Rotational Rules | Define rotation pattern (weekly / fortnightly); assign to departments |
| Planned Downtime | Slots added per shift (maintenance windows, etc.) |

**Sample Shifts:**

| Shift Name | Code | Start | End | Grace (min) | Break (min) |
|---|---|---|---|---|---|
| General Shift | GS-001 | 09:00 AM | 06:00 PM | 15 | 60 |
| Morning Shift | MS-002 | 06:00 AM | 02:00 PM | 10 | 30 |
| Afternoon Shift | AS-003 | 02:00 PM | 10:00 PM | 10 | 30 |
| Night Shift | NS-004 | 10:00 PM | 06:00 AM | 15 | 45 |
| Flexible Shift | FS-005 | 10:00 AM | 07:00 PM | 30 | 60 |

### 6.5 Work Week / Roster Configuration

| Field | Description |
|---|---|
| Roster Name | e.g., "Standard 5-Day", "Alternate Saturday", "6-Day Week" |
| Pattern | Mon–Fri / Mon–Sat / Mon–Sat Alt / Custom |
| Week-Off Day 1 | Primary weekly off day |
| Week-Off Day 2 | Secondary weekly off day (if applicable) |
| Applicable Employee Types | Assign roster to specific employee types |
| Effective From | Date from which roster applies |

**Sample Rosters:**

| Roster Name | Pattern | Week-Off 1 | Week-Off 2 | Emp Types |
|---|---|---|---|---|
| Standard 5-Day | Mon–Fri | Saturday | Sunday | FTP, CTR |
| Alternate Saturday | Mon–Sat Alt | Alt Saturday | Sunday | FTP |
| 6-Day Week | Mon–Sat | Sunday | — | CTR, PRT |
| Night Roster | Mon–Fri Night | Saturday | Sunday | FTP |
| Flexible Work | Custom | Saturday | Sunday | CON, INT |

### 6.6 Holiday Calendar Configuration

| Feature | Configuration |
|---|---|
| Holiday Name | e.g., "Independence Day", "Deepavali", "Eid" |
| Holiday Date | Specific calendar date |
| Holiday Type | National / Regional / Company / Optional / Restricted |
| Branch / Location Specific | Regional holidays apply to specific branches only |
| Applicable Branches | All Branches / Select Branches |
| Year | Calendar year for the holiday |
| 1-Click Import | Import all public holidays for any state in one action |
| Clone for Next Year | One-button copy and adjust for next financial year |
| Restricted Holiday | Employee must request in advance; limited slots |

### 6.7 Overtime Rules Configuration

| Config | Description |
|---|---|
| Eligible Employee Types | Which types qualify for OT (e.g., Permanent, Contractual) |
| OT Rate Multiplier | 1.5× or 2× the daily/hourly rate |
| OT Eligibility Threshold | Minimum extra hours before OT applies |
| Monthly OT Cap | Maximum OT hours claimable per month |
| Weekly OT Cap | Maximum OT hours per week |
| Payroll Auto-Include | Toggle to auto-include OT in monthly payroll |
| OT Approval Required | Yes / No; if Yes, approval from manager before payroll |
| Monthly Cost Estimate | System shows estimated OT cost based on current headcount |

### 6.8 Attendance Rules

| Rule | Description |
|---|---|
| Day Boundary | Time at which calendar day changes for night shifts |
| Half-Day Threshold | Hours present to qualify as half-day (e.g., < 5 hours = absent, 5–8 hours = half-day) |
| Late Arrival Rule | Number of late arrivals allowed per month before deduction |
| Early Exit Rule | Rules for employees leaving before shift end |
| LOP Deduction | Auto-deduct from salary for unauthorised absence |
| Missing Punch Alert | Notify employee and HR for missing punch-in or punch-out |
| Default Shift Assignment | Each employee has a default shift; shift overrides apply on specific dates |

---

## 7. Leave Management Configuration

*(CFG-013 — mapped to Smart Config Page 2)*

### 7.1 Leave Type Master

Define all leave types. Each type has its own policy, accrual rules, and approval flow.

| Field | Required | Notes |
|---|---|---|
| Leave Type Name | ✅ Yes | e.g., "Casual Leave", "Privilege Leave", "Sick Leave" |
| Leave Code | ✅ Yes | Short code; e.g., `CL`, `PL`, `SL`, `EL`, `CO`, `ML` |
| Leave Category | ✅ Yes | Paid Leave, Unpaid Leave, Compensatory, Statutory |
| Annual Entitlement (Days) | ✅ Yes | Total days per leave year |
| Statutory Minimum | Auto | System enforces statutory minimums per applicable law |
| Accrual Frequency | No | Monthly / Quarterly / Annual / Pro-rata / Upfront |
| Accrual Day | No | Day of month when leave is credited (e.g., 1st) |
| Carry Forward Allowed | No | Yes / No |
| Max Carry Forward Days | No | Upper limit on days carried to next year |
| Carry Forward Expiry | No | Carried leaves must be consumed by a date |
| Encashment Allowed | No | Yes / No |
| Max Encashable Days | No | Per year / total tenure |
| Encashment Rate | No | Per day salary basis: Basic / Gross. Formula: Encashable Days × (Last Drawn Basic ÷ 26). Tax exemption: up to ₹25,00,000 on retirement / resignation (post Budget 2023 amendment). |
| Applicable Employment Types | No | All / Permanent / Contract / Intern |
| Applicable Gender | No | All / Female only (e.g., Maternity Leave) |
| Probation Restriction | No | Which leave types are blocked during probation period |
| Minimum Tenure for Eligibility | No | e.g., must complete 6 months to avail PL |
| Minimum Advance Notice | No | Days before leave that application must be submitted |
| Min Days per Application | No | e.g., ML must be taken for minimum 26 weeks |
| Max Consecutive Days | No | Maximum days in a single leave application |
| Allow Half-Day | No | Yes / No |
| Weekend Sandwich Rule | No | Include or exclude weekends within leave period |
| Holiday Sandwich Rule | No | Include or exclude holidays between leave days |
| Documentation Required | No | Medical certificate required after N days of SL |
| LOP on Excess | No | Auto-convert to LOP when leave balance exhausted |
| e-Sign Required | No | Toggle — whether leave approval letter requires e-sign |

### 7.2 Standard Leave Types (India)

| Leave Type | Code | Statutory Basis | Typical Entitlement |
|---|---|---|---|
| Casual Leave | CL | Factories Act / Shops & Establishments | 12 days / year |
| Privilege / Earned Leave | PL / EL | Factories Act | 15–18 days / year |
| Sick Leave | SL | Shops & Establishments | 12 days / year |
| Maternity Leave | ML | Maternity Benefit Act, 1961 | 26 weeks (first 2 children); 12 weeks (3rd child onwards); PF/ESI contributions continue during leave; salary paid at average of last 3 months' wages; no deductions of any kind during leave period |
| Paternity Leave | PTL | Company policy | 5–15 days |
| Bereavement Leave | BL | Company policy | 3–5 days |
| Compensatory Off | CO | Company policy | Accrued on worked holidays |
| Leave Without Pay | LOP | — | No entitlement; auto-deduction |
| National Holidays | NH | National & Festival Holidays Act | 3 national + state-declared |
| Optional Holidays | OH | Company policy | Typically 2 per year |
| Marriage Leave | MAL | Company policy | 3–5 days |
| Study Leave | STL | Company policy | Varies |
| Sabbatical | SAB | Company policy | Varies |

### 7.3 Holiday Calendar

*(Detailed configuration covered in Section 6.6 — shared with Attendance module)*

### 7.4 Leave Policy Assignment

Leave policies can be assigned at multiple levels:

| Assignment Level | Description |
|---|---|
| Company-wide | All employees get the same leave policy |
| Department-wise | Different departments have different entitlements |
| Designation-wise | e.g., C-suite may have extra privilege leave |
| Grade-wise | Higher grades may have more carry-forward allowances |
| Employment Type-wise | Contract employees get fewer leaves than permanent |
| Individual Override | Specific employee overrides (e.g., extended maternity) |

**Quick Template Feature:** Choose industry and system pre-fills all standard leave types with correct statutory minimums.

### 7.5 Leave Approval Workflow

| Configuration | Options |
|---|---|
| Approval Levels | 1-level (Manager only) / 2-level (Manager + HR) / 3-level (Manager + HR + Director) |
| SLA per Level | Number of days before auto-escalation |
| Auto-Approval | For certain leave types after N days of no action (configurable safety valve) |
| Auto-Rejection | If no action taken beyond N days |
| Manager Proxy | Designate alternate approver when manager is on leave |
| HR Override | HR can approve/reject any leave regardless of hierarchy |
| Notification | Email / mobile push when leave is applied, approved, rejected |

### 7.6 Leave Balance Management

| Feature | Description |
|---|---|
| Opening Balance | Enter opening balances for employees joining mid-year |
| Pro-rata Calculation | Auto-calculate entitlement based on joining date |
| Year-End Processing | Carry forward, encash, or lapse expired balances |
| Leave Adjustment (Override) | Manual credit/debit with reason by HR; requires HR Head approval |
| Negative Leave Balance | Allow or restrict employees from going into negative balance |
| ESS Sync | Balance updates instantly on ESS after any HR override |

### 7.7 Compensatory Off (Comp-off) Configuration

| Setting | Description |
|---|---|
| Accrual Trigger | Employee works on holiday or week-off day |
| Accrual Rule | 1 comp-off per worked holiday (full day / half day) |
| Validity Period | Comp-off must be availed within N days of accrual |
| Expiry Handling | Lapse after validity period or auto-encash |
| Approval for Availing | Manager approval required to avail comp-off |
| Payroll Impact | Expired comp-off encashed in payroll if policy allows |

---

## 8. Payroll Configuration

*(CFG-010, CFG-011, CFG-012, CFG-014, CFG-020, CFG-028 — mapped to Smart Config Page 3)*

### 8.1 Salary Component Master

Define all components that make up an employee's salary package.

| Field | Required | Notes |
|---|---|---|
| Component Name | ✅ Yes | e.g., "Basic Salary", "HRA", "Special Allowance" |
| Component Code | ✅ Yes | Short code; e.g., `BASIC`, `HRA`, `SA`, `TA` |
| Component Type | ✅ Yes | Earning / Deduction / Employer Contribution |
| Calculation Method | ✅ Yes | Fixed Amount, % of Basic, % of Gross, Formula-based |
| Calculation Formula | Conditional | Plain English formula: "50% of Basic" not complex syntax |
| Taxable | ✅ Yes | Fully Taxable / Partially Exempt / Fully Exempt |
| Exemption Section | Conditional | e.g., Section 10(13A) for HRA, Section 10(14) for TA |
| Exemption Limit | Conditional | e.g., ₹200/day for food allowance |
| PF Inclusion | No | Include in PF wage calculation |
| ESI Inclusion | No | Include in ESI gross salary |
| Bonus Inclusion | No | Include in bonus computation base |
| Gratuity Inclusion | No | Include in gratuity base salary |
| Show on Payslip | ✅ Yes | Yes / No — toggle per component row |
| Payslip Order | No | Display sequence on payslip |
| Status | ✅ Yes | Active / Inactive |

### 8.2 Standard Salary Components (India)

**Earnings:**

| Component | Code | Typical % | Tax Treatment |
|---|---|---|---|
| Basic Salary | BASIC | 40–50% of CTC | Fully Taxable |
| House Rent Allowance (HRA) | HRA | 50% of Basic (metro) / 40% (non-metro) | Exempt u/s 10(13A) |
| Special Allowance | SA | Residual (balancing) | Fully Taxable |
| Conveyance Allowance | CA | Fixed ₹1,600/month | Fully Taxable |
| Medical Allowance | MA | Fixed ₹1,250/month | Fully Taxable |
| Leave Travel Allowance (LTA) | LTA | 8.33% of Basic | Exempt u/s 10(5) |
| Food / Meal Allowance | FOOD | ₹50/meal | Exempt up to ₹50/meal |
| Children Education Allowance | CEA | ₹100/child/month | Exempt up to ₹100/child |
| Children Hostel Allowance | CHA | ₹300/child/month | Exempt up to ₹300/child |
| Performance Bonus | PBONUS | Variable | Fully Taxable |
| Overtime Allowance | OT | Variable | Fully Taxable |
| Shift Allowance | SHIFT | Fixed or variable | Varies |

**Deductions (Employee):**

| Component | Code | Notes |
|---|---|---|
| Provident Fund (Employee) | PF_EE | 12% of Basic (up to ₹15,000 wage cap) |
| ESI (Employee) | ESI_EE | 0.75% of Gross (for gross ≤ ₹21,000) |
| Professional Tax (PT) | PT | State slab-based |
| TDS (Income Tax) | TDS | Monthly deduction based on annual TDS projection |
| Labour Welfare Fund (LWF) | LWF | State-specific amount |
| Loan EMI Deduction | LOAN | Auto-deduct from payroll if employee has active loan |
| Salary Advance Recovery | ADV | Recovery of advance paid |

**Employer Contributions:**

| Component | Code | Notes |
|---|---|---|
| PF Employer Contribution | PF_ER | 12% of Basic (up to ₹15,000 wage cap) |
| ESI Employer Contribution | ESI_ER | 3.25% of Gross (for gross ≤ ₹21,000) |
| Gratuity Provision | GRAT | 4.81% of Basic (actuarial or AS-15 basis) |
| Superannuation | SA_ER | 15% of Basic (if scheme exists) |

### 8.3 PF / ESI / PT Rules Configuration

*(Pre-loaded values — admin confirms each FY)*

**Provident Fund:**

| Component | Employee Rate | Employer Rate | Wage Ceiling | Applicability |
|---|---|---|---|---|
| Provident Fund | 12% | 12% | ₹15,000/month | FTP and CTR |

- VPF option toggle (employee may contribute more than 12%; employer does not match excess)
- EPFO portal link for ECR auto-upload

**ESI:**

| Component | Employee Rate | Employer Rate | Wage Ceiling | Applicability |
|---|---|---|---|---|
| ESI Employee | 0.75% | — | ₹21,000/month | FTP, CTR, PRT |
| ESI Employer | — | 3.25% | ₹21,000/month | FTP, CTR, PRT |

**Professional Tax (sample):**

| State | Employee Rate | Employer Rate | Wage Ceiling | Applicability |
|---|---|---|---|---|
| Karnataka | — | ₹200/month | No ceiling | All Employees |
| Maharashtra | — | ₹200/month | No ceiling | All Employees |

### 8.4 Salary Structure / Template

A salary structure maps which components apply to which employees.

| Field | Required | Notes |
|---|---|---|
| Structure Name | ✅ Yes | e.g., "L4 Standard", "Junior Grade Structure" |
| Structure Code | ✅ Yes | Short unique code |
| Applicable Grade(s) | No | Assign to one or more grades |
| Applicable Designation(s) | No | Assign to specific designations |
| Applicable Employment Type | No | Permanent / Contract / Intern |
| Components | ✅ Yes | Select active components; set formula/% |
| CTC Basis | ✅ Yes | Whether the structure is CTC-based or take-home based |
| Visual Pie Chart Preview | Auto | Pie chart showing % split across components |

### 8.5 Payroll Run Configuration

| Setting | Description |
|---|---|
| Payroll Month Lock | Lock a month's payroll after processing to prevent changes |
| Arrears Processing | Enable/disable automatic arrears calculation on salary revision |
| Revised Salary Effective Date | Start of month or actual joining/revision date |
| LOP Rate | Monthly Salary ÷ 26 / ÷ 30 / ÷ Actual Working Days |
| Pro-rata for New Joiners | Proportional salary for mid-month joiners |
| Pro-rata for Exits | Same for employees exiting mid-month |
| Rounding Rules | Round to nearest rupee / 50p / no rounding |
| Negative Salary Handling | Flag for review or generate negative payslip |
| Variance Alert | System auto-flags >10% change vs previous month |

### 8.6 Salary Revision Configuration

| Feature | Description |
|---|---|
| Increment Types | % increment, Fixed increment, New CTC |
| Effective Date Options | Retrospective / Prospective |
| Arrears Auto-Calculation | Compute and pay arrears automatically month-by-month |
| Grade Band Validation | Warns if revised salary exceeds grade band |
| Revision Letter Generation | Auto-generate increment / revised appointment letter |
| Increment Freeze Policy | Lock increments during appraisal/budget cycle |

### 8.7 Bank Disbursement Configuration

| Setting | Description |
|---|---|
| Payment Mode | NEFT, RTGS, IMPS, Cheque |
| Bank File Format | Bank-specific salary advice formats (SBI, HDFC, ICICI, Axis, Kotak, etc.) |
| Bank Account (Employer) | Company's salary disbursement account details |
| Bulk Transfer | Generate a single debit file for all employee salaries |
| Payment Date | Linked to the disbursement day configured during onboarding |
| Failed Transaction Handling | Re-attempt logic and alert on bounced payments |
| Auto-Push on Approval | Bank file auto-pushed after payroll manager approval |
| Salary On Hold | Flag specific employees' salary to not be disbursed |

### 8.8 Loan Policy Configuration

> Full loan policy configuration — loan types, amounts, tenure, interest, EMI cap, approval levels, and eligibility criteria — is documented in **Section 23 (Loan, Advance & Reimbursement Configuration)** to avoid duplication. Configured values here are reflected in the payroll deduction engine automatically.

### 8.9 Reimbursements Configuration

> Full reimbursement types, tax treatment, claim submission rules, and approval workflows are documented in **Section 23.3 (Reimbursement Types)**. Approved reimbursement claims are automatically included in the monthly payroll run.

---

## 9. Statutory Compliance Configuration

*(CFG-012 — mapped to Smart Config Page 3)*

### 9.1 Provident Fund (PF) Configuration

| Setting | Options | Notes |
|---|---|---|
| PF Applicability | Mandatory for Basic ≤ ₹15,000; voluntary above | |
| Employee Contribution Rate | 12% (standard) | May be increased voluntarily (VPF) |
| Employer Contribution — EPF | 3.67% of Basic | Remaining after EPS allocation |
| Employer Contribution — EPS | 8.33% of Basic (max ₹1,250/month) | Employees' Pension Scheme |
| Employer Contribution — EDLI | 0.5% of Basic (max ₹75/month) | Employees' Deposit Linked Insurance |
| PF Admin Charges | 0.50% of Basic (min ₹500/month) | EPF Admin; 0.01% for EDLI Admin |
| Wage Ceiling | ₹15,000 | PF calculated on Basic up to this limit |
| Excluded Components | Specify components excluded from PF wage | |
| PF Returns Format | ECR 2.0 (Electronic Challan cum Return) | Monthly upload to EPFO portal |

### 9.2 ESI (Employee State Insurance) Configuration

| Setting | Options | Notes |
|---|---|---|
| ESI Applicability | Mandatory for companies with ≥ 10 employees AND employee gross ≤ ₹21,000/month | |
| Employee Contribution Rate | 0.75% of Gross | |
| Employer Contribution Rate | 3.25% of Gross | |
| ESI Wage Ceiling | ₹21,000/month gross | Above this, employee exits ESI |
| ESI Month Closure Date | 15th / 21st of following month for challan | |
| ESI Excluded Wages | List components excluded from ESI gross | |

### 9.3 Professional Tax (PT) Configuration

PT rates and applicability vary by state. Configure for each state where the company has employees:

| State | Applicability | Slab Notes |
|---|---|---|
| Karnataka | ✅ Applicable | ₹0–₹14,999 = Nil; ₹15,000+ = ₹200/month |
| Maharashtra | ✅ Applicable | Monthly slab based on income range |
| Tamil Nadu | ✅ Applicable | State-specific slabs |
| Andhra Pradesh | ✅ Applicable | State-specific slabs |
| West Bengal | ✅ Applicable | State-specific slabs |
| Gujarat | ✅ Applicable | State-specific slabs |
| Telangana | ✅ Applicable | State-specific slabs |
| Kerala | ✅ Applicable | State-specific slabs |
| Other States | Not applicable | No PT in remaining states |

For each applicable state: configure income slabs (From / To Amount), PT Amount per slab, Frequency (Monthly / Semi-annual), PT Registration Number.

### 9.4 Gratuity Configuration

| Setting | Description |
|---|---|
| Applicability | Employees with ≥ 5 years of service |
| Calculation Formula | (Last Basic Salary × 15 × Years of Service) ÷ 26 |
| Gratuity Base | Basic + DA (as per Payment of Gratuity Act) |
| Maximum Gratuity | ₹20,00,000 (tax-exempt limit) |
| Provision Method | Monthly accounting provision or actual at exit |
| Gratuity Trust | Yes (private trust) / No (LICI scheme or employer-funded) |
| Forfeiture Rules | Forfeiture for terminated employees as per Act |

### 9.5 Bonus Configuration (Payment of Bonus Act)

| Setting | Description |
|---|---|
| Applicability | Employees with annual salary ≤ ₹21,000/month AND establishment employing ≥ 20 persons |
| Bonus Wage Ceiling | ₹7,000/month (or minimum wage, whichever is higher) |
| Minimum Bonus | 8.33% of annual wages |
| Maximum Bonus | 20% of annual wages |
| Bonus Calculation Period | April – March |
| Eligibility: Minimum Working Days | 30 working days in the year |
| Bonus Payment Due Date | 8 months after accounting year closure |
| Allocable Surplus | 60% of gross profit (public) / 67% (private) |

### 9.6 Labour Welfare Fund (LWF) Configuration

| Setting | Description |
|---|---|
| Applicable States | Maharashtra, Andhra Pradesh, Karnataka, Gujarat, Tamil Nadu, etc. |
| Employee Contribution | State-specific amount (typically ₹6–₹30 per period) |
| Employer Contribution | State-specific multiplier of employee contribution |
| Deduction Frequency | Monthly / 6-monthly / Annual (state-specific) |

### 9.7 Statutory Reports & Filings

| Report / Filing | Frequency | Statutory Basis |
|---|---|---|
| PF ECR (Challan cum Return) | Monthly | EPFO |
| ESI Challan | Monthly | ESIC |
| Form 24Q (TDS Return) | Quarterly | Income Tax Act |
| Form 16 (TDS Certificate) | Annual | Income Tax Act |
| PT Challan | Monthly / Semi-Annual | State PT Acts |
| LWF Contribution Statement | Monthly / Annual | State LWF Acts |
| Bonus Statement | Annual | Bonus Act |
| Gratuity Register (Form U) | Annual | Gratuity Act |
| Leave Register | Annual | Factories Act / S&E Act |
| Overtime Register | Annual | Factories Act |
| Wage Register | Annual | Minimum Wages Act |
| Attendance Register | Annual | Factories Act |
| POSH Annual Report | Annual | POSH Act 2013 |

---

## 10. TDS & Income Tax Configuration

### 10.1 Tax Regime Configuration

| Setting | Options | Notes |
|---|---|---|
| Default Tax Regime | Old Regime / New Regime | New Regime is default post FY 2023-24; employees can opt out |
| Employee Declaration Deadline | Date by when employees must submit Form 12BB / IT declaration | |
| Provisional vs Final Declaration | System uses provisional at start of year; switches to final at year-end | |

### 10.2 Income Tax Slabs (FY 2025-26)

**Old Tax Regime:**

| Income Slab | Tax Rate |
|---|---|
| Up to ₹2,50,000 | Nil |
| ₹2,50,001 – ₹5,00,000 | 5% |
| ₹5,00,001 – ₹10,00,000 | 20% |
| Above ₹10,00,000 | 30% |

**New Tax Regime (FY 2025-26):**

| Income Slab | Tax Rate |
|---|---|
| Up to ₹3,00,000 | Nil |
| ₹3,00,001 – ₹7,00,000 | 5% |
| ₹7,00,001 – ₹10,00,000 | 10% |
| ₹10,00,001 – ₹12,00,000 | 15% |
| ₹12,00,001 – ₹15,00,000 | 20% |
| Above ₹15,00,000 | 30% |

> **Note:** Tax slabs are pre-loaded for the current FY and must be updated every April per Union Budget announcements. Old and New regime slabs are both maintained simultaneously.

### 10.3 Investment Declaration Configuration (Form 12BB)

| Section | Description | Limit |
|---|---|---|
| 80C | LIC, PPF, ELSS, NSC, Home Loan Principal, School Fees, etc. | ₹1,50,000 |
| 80CCC | Pension Fund | ₹1,50,000 (within 80C limit) |
| 80CCD(1) | NPS Employee Contribution | ₹1,50,000 (within 80C limit) |
| 80CCD(1B) | NPS Additional Contribution | ₹50,000 (over and above 80C) |
| 80D | Health Insurance Premium | ₹25,000 / ₹50,000 (senior citizen) |
| 80DD | Dependent Disabled | ₹75,000 / ₹1,25,000 |
| 80DDB | Medical Treatment (specified diseases) | ₹40,000 / ₹1,00,000 |
| 80E | Education Loan Interest | No limit |
| 80EEA | Home Loan Interest (affordable housing) | ₹1,50,000 |
| 80G | Donations | 50% / 100% depending on organisation |
| 80GG | Rent (HRA not received) | Least of three conditions |
| 80TTA | Savings Bank Interest | ₹10,000 |
| 80TTB | Senior Citizen FD/RD Interest | ₹50,000 |
| HRA Exemption | Rent paid; exemption u/s 10(13A) | Min of 3 conditions |
| LTA Exemption | Leave Travel Allowance u/s 10(5) | Actual travel cost |
| Home Loan Interest | Section 24(b) | ₹2,00,000 |

### 10.4 Perquisites Configuration

| Perquisite | Tax Treatment |
|---|---|
| Company Car (personal use) | Taxable as perquisite — cc-based rate |
| Accommodation (company-provided) | % of salary depending on city population |
| Stock Options (ESOPs) | Taxable at vesting/exercise |
| Interest-free / concessional loans | Taxable on differential interest |
| Club Membership | Fully taxable perquisite |
| Gift Vouchers | Up to ₹5,000 per year tax-exempt |
| Medical reimbursement | Up to ₹15,000/year (Old Regime) |

### 10.5 TDS Computation & Form 16

| Feature | Description |
|---|---|
| Monthly TDS Projection | Estimated annual tax ÷ remaining months for monthly TDS |
| Revised TDS Computation | Auto-recalculates when salary revised or new declarations submitted |
| Shortfall Recovery | TDS shortfall recovered in last 3 months of FY |
| Form 16 — Part A | TDS certificate from 26AS data; issued by May 31 |
| Form 16 — Part B | Salary breakdown and exemption details |
| Bulk Form 16 Generation | All employees in one action; auto-emailed |
| Form 26AS Reconciliation | Match TDS deposited against 26AS |
| Form 24Q | Quarterly TDS return filed with Income Tax Department |

---

## 11. Employee Self-Service (ESS) Portal Configuration

### 11.1 ESS Access Configuration

| Setting | Description |
|---|---|
| ESS URL / Subdomain | Unique URL for the company's ESS portal |
| Login Method | Username + Password / SSO (Google / Microsoft) / OTP |
| First Login Password | Auto-set to Employee Code or DOB; force change on first login |
| Password Policy | Min length, complexity, expiry, history |
| Session Timeout | Auto-logout after N minutes of inactivity |
| MFA | Optional / Mandatory for all / Mandatory for sensitive actions |

### 11.2 ESS Module Enablement

| ESS Feature | Enable/Disable | Notes |
|---|---|---|
| View Payslips | ✅ Recommended | Monthly payslips downloadable as PDF |
| Download Form 16 | ✅ Recommended | Annual TDS certificate |
| Leave Application | ✅ Recommended | Apply, track, cancel leaves |
| Leave Balance View | ✅ Recommended | Real-time leave balance |
| IT Declaration Submission | ✅ Recommended | Form 12BB investment declarations |
| Attendance View | ✅ Recommended | View own attendance; flag discrepancies |
| Attendance Regularization | Configurable | Request missed punch correction |
| Reimbursement Claims | Configurable | Submit claims with receipts |
| Travel Claims | Configurable | Business travel expense submission |
| Profile Update | Configurable | Update personal details, bank account, nominee |
| Document Upload | Configurable | Upload ID proofs, certificates |
| Loan Application | Configurable | Apply for salary advance / loan |
| Asset View | Configurable | View assigned company assets |
| Performance Goal Setting | Configurable | View/set KRAs |
| Appraisal Form Access | Configurable | Self-appraisal submission |
| 360° Feedback Submission | Configurable | Anonymous multi-rater feedback |
| Training Enrollment | Configurable | Browse and enroll in training programs |
| Help Desk / Ticket Raise | Configurable | Raise HR, IT, or Admin queries |
| Employee Directory | Configurable | Company directory with contacts |
| Holiday Calendar View | ✅ Recommended | View upcoming company holidays |
| HR Policy Documents | Configurable | Employee handbook, policies, SOPs |
| Onboarding Checklist | ✅ Recommended | New joiner self-service steps from Day 1 |
| Grievance Submission | Configurable | Submit grievances via ESS |

### 11.3 Manager Self-Service (MSS) Configuration

Managers get additional features in the same portal:

| Feature | Description |
|---|---|
| Leave Approval | Approve / reject team members' leave requests |
| Attendance Regularization Approval | Approve missed punch correction requests |
| Team Attendance View | View team's daily/monthly attendance |
| Team Leave Calendar | Calendar view of team leaves for planning |
| OT Approval | Approve team overtime claims |
| Performance Review | Set KRAs and submit reviews for reportees |
| Reimbursement Approval | Approve expense claims |
| Asset Approval | Approve asset requests |
| Probation Confirmation | Submit probation feedback and confirmation decision |

### 11.4 AI Chatbot Integration for ESS

Configure an AI-powered HR chatbot accessible within ESS and on mobile/Slack/Teams:

| Setting | Description |
|---|---|
| Chatbot Toggle | Enable / Disable |
| Enabled Intents | Leave Balance Query, Payslip Download, Policy FAQ, Attendance Status, HR Contact |
| Deployment Channels | Web ESS / Mobile App / Slack / Microsoft Teams |
| Fallback to HR | Unresolved queries escalated to HR queue with ticket number |
| Language Support | English; Hindi (optional) |

---

## 12. Role-Based Access Control (RBAC) Configuration

*(CFG-015, CFG-016 — mapped to Smart Config Page 5)*

### 12.1 Pre-Built System Roles

The system includes 6 pre-built roles. Any role can be cloned and customised.

| Role | Code | Parent Role | Access Level | Screens |
|---|---|---|---|---|
| Super Administrator | SA-001 | — | Full System | All 32 CFG + All 28 TRN |
| HR Manager / Admin | HR-MGR | HR Director | Department | CFG-001 to CFG-025, All TRN |
| Payroll Manager | PAY-MGR | Finance Manager | Function | CFG-010 to CFG-014, TRN Payroll |
| Department Head / Manager | DEPT-HD | HR Manager | Team | MSS + Team Reports |
| Employee (ESS) | EMP-001 | Dept Head | Self Only | ESS Portal Only |
| CHRO | CHRO-01 | CEO | Full HR | All HR modules, No Finance |
| Finance Manager | FIN-MGR | CFO | Department | CFG-010 to CFG-012, Reports |

### 12.2 Module-Level Permission Matrix

Permission matrix is a visual grid: rows = modules, columns = roles. Click each cell to toggle View / Create / Edit / Delete.

| Module | Super Admin | HR Admin | Payroll Mgr | CHRO | Manager | Employee |
|---|---|---|---|---|---|---|
| Company Setup | ✅ Full | 👁 View | ❌ | 👁 View | ❌ | ❌ |
| Employee Master | ✅ Full | ✅ Full | 👁 View | ✅ Full | 👁 Own Team | 👁 Own Only |
| Attendance | ✅ Full | ✅ Full | 👁 View | 👁 View | ✅ Team | 👁 Own Only |
| Leave Management | ✅ Full | ✅ Full | 👁 View | 👁 View | ✅ Approve | ✅ Apply |
| Payroll | ✅ Full | 👁 View | ✅ Full | 👁 Summary | ❌ | 👁 Own Slip |
| Statutory Compliance | ✅ Full | ✅ Full | ✅ Full | 👁 View | ❌ | ❌ |
| Reports | ✅ Full | ✅ Full | ✅ Payroll | ✅ Full HR | ✅ Team | ❌ |
| Performance | ✅ Full | ✅ Full | ❌ | ✅ Full | ✅ Team | ✅ Own |
| User Management | ✅ Full | ✅ Own Co. | ❌ | ❌ | ❌ | ❌ |

### 12.3 Field-Level Masking

Mark sensitive fields as hidden for specific roles — toggle per field:

| Sensitive Field | Hidden From |
|---|---|
| Salary / CTC | Managers, Employees |
| Bank Account Number | Managers, Employees (partial mask shown) |
| Aadhaar Number | All (always masked — `XXXX XXXX 4521`) |
| PAN Number | Employees (shown in own profile only) |
| PAN / TAN of Company | Finance Masked from HR |

### 12.4 Custom Role Creation

- Clone any pre-built role to create a custom role
- Edit role name and description
- Adjust module-level permissions via matrix grid
- Adjust field-level masking toggles
- Assign to one or more users

---

## 13. Approval Workflows & Automation Configuration

*(CFG-017, CFG-018 — mapped to Smart Config Page 5)*

### 13.1 Workflow Designer

Each configurable workflow uses a **drag-and-drop** approver sequence builder — no coding required.

| Workflow | Configurable Approval Sequence |
|---|---|
| Leave Application | Employee → Manager → HR → Director |
| Attendance Regularization | Employee → Manager (→ HR for senior grades) |
| Overtime Claim | Employee → Manager → Payroll |
| Reimbursement Claim | Employee → Manager → Finance |
| Loan Application | Employee → HR → Finance Manager → CFO (if above limit) |
| Exit / Resignation | Employee → Manager → HR → Director |
| Payroll Approval | HR → Finance Manager → CFO |
| Salary Revision | HR → Management → Finance |
| Job Requisition | Department Head → HR Head → CEO |
| Bonus Upload | HR → Finance Manager → CFO (if above ₹1L) |
| Leave Override | HR Admin → HR Head |
| Asset Issuance | HR → Admin (→ IT for system assets) |

### 13.2 SLA & Auto-Escalation

| Setting | Description |
|---|---|
| SLA per Step | Number of days before escalation at each approval level |
| Auto-Escalate | If SLA exceeded, automatically move to next approver |
| Auto-Approve | Fallback option if no action taken after N days (configurable toggle) |
| Auto-Reject | Alternative: auto-reject if no action by deadline |
| Reminder Notifications | Alert sent X days before SLA deadline |

### 13.3 Approval Chain Reference Notation

Workflows are referenced in configuration notes using:
```
Company Setup → [Workflow Category] → [Workflow Name]
```
Examples:
- `Company Setup → HR Workflow → Leave Override`
- `Company Setup → Payroll Workflow → Bonus Approval`
- `Company Setup → HR Workflow → Loan Processing`

---

## 14. Notification & Communication Configuration

*(CFG-019, CFG-031 — mapped to Smart Config Pages 5 & 1)*

### 14.1 Notification Channels

| Channel | Use Cases |
|---|---|
| Email (SMTP) | Payslip dispatch, Form 16, leave approval/rejection, salary revision letter |
| SMS | Salary credit alert, OTP for ESS login |
| In-App Notification | Leave status, attendance alerts, task reminders |
| WhatsApp Business API | Salary credit, leave approval, payslip (optional) |
| Push Notification (Mobile App) | Leave updates, shift change, announcements |

### 14.2 Notification Rule Builder

Rules are built using a simple **"When [Event] → Send [Template] to [Role] via [Channel]"** picker — no coding required.

| Field | Description |
|---|---|
| Trigger Event | Select from event library (leave applied, payslip published, etc.) |
| Message Template | Select pre-defined template; edit inline with variable tokens (`{employee_name}`, `{leave_days}`, `{salary_amount}`) |
| Recipient Role | Employee / Manager / HR / Finance / IT / Admin / All |
| Channel | Email / SMS / In-App / WhatsApp / Push |

### 14.3 Standard Automated Notification Triggers

| Event | Default Recipients |
|---|---|
| Employee joins system | HR, IT, Admin, Reporting Manager |
| Payroll processed | Finance Admin |
| Payslip published | Employee |
| Leave applied | Approving Manager |
| Leave approved / rejected | Applying Employee |
| Attendance regularization approved | Employee |
| Salary revision | Employee, Finance |
| Form 16 generated | Employee |
| Loan EMI deducted | Employee |
| Probation approaching end (30 days) | HR, Manager |
| Work anniversary / Birthday | HR (and optionally the employee) |
| Exit clearance pending | Clearance department head |
| F&F payment processed | Employee |
| Statutory payment due reminder | HR / Finance |
| Document expiry approaching | HR, Employee |
| Asset return pending (exit) | Admin, IT, HR |
| Appraisal cycle opened | All Employees, All Managers |
| Training session scheduled | Nominated Employees |
| PIP / Warning issued | Employee, Manager, HR |

---

## 15. Data Retention Policy Configuration

*(CFG-032 — mapped to Smart Config Page 5)*

### 15.1 Retention Policy Setup

Set retention periods per data type. Post-retention, data is automatically archived or deleted per policy.

| Data Category | Default Retention | Action After Period |
|---|---|---|
| Employee Master Records | 7 years post-exit | Archive → Anonymise after 7 years |
| Payroll & Salary Records | 7 years | Archive |
| Statutory Filing Records | 8 years | Archive (regulatory requirement) |
| Attendance Records | 5 years | Archive |
| Leave Records | 5 years | Archive |
| Recruitment Records | 2 years | Delete after candidate rejection / 5 years post-hire |
| Training Records | 5 years | Archive |
| Disciplinary Records | 5 years post-resolution | Archive |
| Document Uploads | Linked to employee record period | Archive with record |
| Audit Log | 7 years | Archive; immutable |

### 15.2 Soft Delete vs Hard Delete

| Action | Description |
|---|---|
| Soft Delete | Record is deactivated but retained in the database; visible to Super Admin |
| Hard Delete | Permanent removal from all records; subject to retention period compliance |
| Anonymisation | PII fields replaced with pseudonyms; record structure retained for statistics |

### 15.3 GDPR & Data Privacy Controls

| Control | Description |
|---|---|
| Data Access Request | Employee can request a copy of their personal data via ESS |
| Right to Rectification | HR Admin can correct inaccurate data via audit-logged edit |
| Data Portability | Export employee data as PDF or structured CSV |
| Consent Management | Track consent for data collection and processing |
| Privacy Notice | Link to company privacy policy displayed at ESS login |
| Biometric Data Privacy | Fingerprint and facial recognition data classified as sensitive personal data under GDPR Article 9 and India DPDP Act 2023; explicit consent recorded at enrollment; biometric templates stored encrypted and never shared with third parties |
| Data Localisation | Employee data stored within India (or configured jurisdiction) per applicable data localisation requirements |

---

## 16. Recruitment & ATS Transactional Operations

*(Smart Transactional Page 1 — consolidates TRN-001 to TRN-005)*

### 16.1 Hiring Pipeline Flow

```
Job Requisition → Candidate Entry/Parse → Interview Schedule → Assessment → Offer Letter → Hired! → Onboarding
```

### 16.2 Job Requisition (TRN-001)

| Field | Description |
|---|---|
| Job Title / Designation | From Designation Master |
| Department | From Department Master |
| Number of Openings | Positions to fill |
| Job Description | Rich text or template-based |
| Budget (CTC Range) | Min and max CTC for the role |
| Target Joining Date | Urgency flag |
| Source Channels | LinkedIn, Naukri, Internshala, Internal, Referral, Campus, Consultancy, Walk-in |
| Approval Workflow | Department Head → HR Head → CEO (configurable) |

### 16.3 Candidate Entry & Pipeline (TRN-002)

| Feature | Description |
|---|---|
| Kanban Board | Drag candidate cards across hiring stages |
| Resume Parser | AI auto-fills candidate profile from PDF/DOCX upload |
| Quick Entry Form | Name, email, phone, source, current CTC |
| Source Tracking | LinkedIn / Naukri / Referral / Walk-in with hire-rate analytics |
| Pipeline Stages | Applied → Shortlisted → HR Round → Technical → Final → Assessment → Offer → Hired |
| Status per Stage | In Progress / Selected / Rejected / On Hold |

**Pipeline Status Dashboard:**

| Stage | Count |
|---|---|
| Applied | All incoming applications |
| Shortlisted | Screened for interview |
| Interviewing | Rounds in progress |
| Assessment | Skills/cultural assessment |
| Offer Sent | Offer letter dispatched |

### 16.4 Interview Scheduler (TRN-003)

| Feature | Description |
|---|---|
| Round-Wise Scheduling | HR Round / Technical Round / Final Round — each with own panel and date |
| Panelist Availability | Real-time calendar showing panelist free slots |
| Video Link Auto-Generate | Google Meet / Teams / Zoom link auto-created on schedule |
| Invite Dispatch | Email + SMS invite to candidate and all panelists in one click |
| Interview Feedback Form | Per-criterion rating: Technical / Communication / Culture Fit / Leadership — with free text |

### 16.5 Assessment & Offer (TRN-004 + TRN-005)

| Feature | Description |
|---|---|
| Panel Feedback Form | Rating grid per competency with consolidated panel score |
| Offer Letter Generator | Auto-fills CTC, designation, joining date from requisition; e-sign dispatch |
| Acceptance Tracking | Accepted / Counter-offer / Declined with timestamp |
| BGV Integration | Background verification agency link + checklist |
| Offer Validity Period | Configurable number of days |
| Offer to Hire Conversion | One click — marks candidate as Hired → triggers Employee Hub onboarding |

---

## 17. Employee Hub — Onboarding & Lifecycle Transactions

*(Smart Transactional Page 2 — consolidates TRN-006, TRN-007, TRN-008, TRN-010)*

### 17.1 New Hire Entry (TRN-010) — 6-Tab Smart Form

Full detail of the 6-tab form is covered in **Section 5.4**. Key smart features:
- Offer letter accepted → Employee ID auto-generated → Onboarding checklist auto-created
- Saved progress auto-resumes if form entry is interrupted
- Salary structure template auto-applies from grade; CTC breakup preview is live and editable
- IFSC lookup auto-fills bank name, branch, city

### 17.2 Onboarding Checklist (TRN-006)

| Feature | Description |
|---|---|
| Auto-Created Tasks | IT setup, ID card, email creation, system access, induction schedule — auto-assigned to owners |
| Task Owners | Assigned by department: IT tasks → IT, Admin tasks → Admin, HR tasks → HR |
| Progress Tracker | Visual progress bar per department; overdue tasks highlighted in red |
| New Joiner Self-Service | New employee sees their own checklist on ESS from Day 1 |
| Completion Notifications | Each owner notified on task assignment; HR notified on completion |

**Standard Onboarding Checklist:**

| Item | Responsible | Timing |
|---|---|---|
| Appointment Letter Issuance | HR | Before joining |
| Bank Account Opening | Employee / HR | Day 1 |
| ID Card Generation | Admin | Day 1 |
| Workstation / Laptop Allotment | IT | Day 1 |
| Email ID Creation | IT | Day 1 |
| System Access Provisioning | IT | Day 1 |
| Induction Program Scheduling | HR | Week 1 |
| Document Collection (PAN, Aadhaar, Bank, Salary Slips) | HR | Day 1–Week 1 |
| UAN Activation / PF Enrollment | HR | Within 30 days |
| ESI Registration (if applicable) | HR | Within 10 days |

### 17.3 Document Collection by Employment Type

| Document | Permanent | Contract | Intern |
|---|---|---|---|
| Offer Letter (Signed) | ✅ | ✅ | ✅ |
| Appointment Letter (Signed) | ✅ | ✅ | ✅ |
| PAN Card | ✅ | ✅ | ✅ |
| Aadhaar Card | ✅ | ✅ | ✅ |
| Bank Account Proof | ✅ | ✅ | ✅ |
| Previous Salary Slips (3 months) | ✅ | ✅ | ❌ |
| Experience / Relieving Letter | ✅ | ✅ | ❌ |
| Passport (Foreign nationals) | Conditional | Conditional | Conditional |
| Educational Certificates | ✅ | Conditional | ✅ |
| Photograph | ✅ | ✅ | ✅ |
| BGV Consent Form | ✅ | ✅ | ❌ |
| ESIC Form 1 (if applicable) | ✅ | ✅ | ❌ |
| PF Nomination Form (Form 2) | ✅ | ✅ | ❌ |
| NDA / Confidentiality Agreement | ✅ | ✅ | Conditional |

### 17.4 Probation & Confirmation Tracking (TRN-007)

| Feature | Description |
|---|---|
| Auto-Alert System | Alert sent to manager 30 days before probation end |
| Manager Feedback Form | Performance rating during probation; Confirm / Extend / Terminate decision |
| Extension Rules | 1× or 2× extension allowed per configuration |
| Confirmation Letter | Auto-generated on confirmation decision; e-sign dispatch to employee |
| Probation End Date | Auto-calculated from joining date + grade/designation probation period |

### 17.5 Transfer & Promotion (TRN-008)

| Feature | Description |
|---|---|
| Transfer Entry | Change department, location, reporting manager; effective date; auto-updates org chart |
| Promotion Wizard | New designation, grade, CTC revision; validates against grade band |
| Transfer / Promotion Letter | Auto-generated and dispatched via e-sign |
| Arrears on Promotion | If promotion is retrospective, arrears auto-computed |
| Certification Expiry Block | Promotion workflow is automatically blocked if the employee has a mandatory certification expiring within 30 days or already expired; HR and employee are alerted; promotion proceeds only after renewal |
| All Events Auto-Logged | Every lifecycle event recorded in employee timeline |

---

## 18. Payroll Run — Transactional Operations

*(Smart Transactional Page 3 — consolidates TRN-016 to TRN-020)*

### 18.1 Monthly Payroll — 6-Step Guided Wizard

Each step must be completed before proceeding. Exceptions surface automatically.

**Step 1 — Lock Attendance:**
- Freeze attendance data for the payroll month
- Unresolved exceptions shown with count
- Manual overrides allowed with reason and approval

**Step 2 — Review Exceptions:**
- Auto-detected exceptions: LOP mismatches, new hires not yet in system, salary holds, missing punch records
- Each exception: Accept (process as-is) or Override (with reason)
- Exception types: LOP mismatch, New hire missed, Salary hold, Negative balance

**Step 3 — Compute Salaries:**
- Run computation for all active employees
- Preview gross / net / deductions per employee before finalising
- Variance report auto-compares this month vs last month; flags >10% changes

**Step 4 — Statutory Deductions:**
- PF, ESI, PT, TDS auto-computed per configured rules
- ECR file for EPFO and Form 24Q data ready for review
- PT challan data generated per state

**Step 5 — Manager / Finance Approval:**
- Send for CFO / Finance Manager approval
- Approval chain from configuration auto-applied
- Approver sees payroll summary: total gross, statutory amounts, bank totals

**Step 6 — Disburse & Archive:**
- Bank file auto-generated in HDFC / ICICI / SBI / Axis / Kotak format
- Salary file pushed to bank on approval
- Payslips auto-generated and emailed to all employees
- Payroll month archived; locked from further edits

### 18.2 Salary Hold (TRN-017)

| Feature | Description |
|---|---|
| Hold Salary | Search employee; enter reason + authorisation code |
| Hold Types | Pending documents, disciplinary action, management instruction |
| Auto-Release | Release on next payroll cycle automatically or manually |
| Partial Hold | Hold specific components only (e.g., hold bonus, not basic) |
| Notification | Employee and manager notified of hold |

### 18.3 Arrear Entry (TRN-019)

| Feature | Description |
|---|---|
| Arrear Trigger | Effective date before current payroll period |
| Auto-Computation | Arrear spread month-by-month with TDS recalculation for each month |
| Components | Specify which components carry the arrear |
| Payslip Inclusion | Arrear included in current month payslip with separate line |
| Statutory Impact | PF / ESI / PT impact recomputed for each affected month |

### 18.4 Salary Revision / Increment Wizard (TRN-020)

| Feature | Description |
|---|---|
| Individual Revision | Enter new CTC → component breakup auto-redesigned per structure |
| Bulk Increment | Upload Excel with Employee ID + New CTC; system validates grade bands |
| Revision Letter | Auto-generated on save; e-sign dispatched to employee |
| Effective Date | Prospective or retrospective; arrears computed if retrospective |
| Grade Band Validation | Warning if revised salary exceeds configured band |

### 18.5 Full & Final Settlement (TRN-018)

F&F is auto-computed once all clearances are done:

| Component | Description |
|---|---|
| Salary for Worked Days | Pro-rated salary for the exit month |
| Leave Encashment | Remaining EL/PL balance encashed per policy |
| Gratuity Payment | If tenure ≥ 5 years; formula: (Last Basic × 15 × Years) ÷ 26 |
| Bonus (Pro-rata) | If applicable under Bonus Act |
| Notice Period Pay Recovery | Deduction if employee leaves short of notice |
| Loan / Advance Recovery | Outstanding loan/advance balance deducted |
| Asset Recovery | Value deduction for unreturned/damaged assets |
| Reimbursement Settlement | Approved pending claims paid |
| TDS on F&F | Tax computed on gratuity excess of ₹20L, notice pay, etc. |
| F&F Payslip | Final payslip showing all F&F components |
| Settlement Letter | Auto-generated and sent to employee |

---

## 19. HR Operations — Daily Transactional Operations

*(Smart Transactional Page 4 — consolidates TRN-011 to TRN-015)*

### 19.1 Attendance Adjustment / Override (TRN-011)

HR or authorised managers can correct attendance records before payroll cut-off.

| Override Type | Description |
|---|---|
| Missing Punch-In | Employee has out-punch but no in-punch |
| Missing Punch-Out | Employee has in-punch but no out-punch |
| Absent Override | Full-day marked absent; physical record confirms presence |
| Late Arrival Override | Waive late-in for the day with reason |
| No Punch at All | No biometric record; verified via physical register or manager sign-off |

**Override Form Fields:**
- Employee (search by name or ID)
- Date of correction
- Issue Type (from above)
- Corrected In Time / Out Time
- Reason (mandatory text)
- Payroll Impact Preview (e.g., "LOP reduced by 0.5 day → +₹3,200 added to payroll")
- Approval Workflow: Submitted to manager / HR Head for confirmation

**Attendance Correction Log:**
- Full audit trail: employee, department, date, issue type, corrected by, salary Δ, approval status

### 19.2 Leave Override (TRN-012)

HR can manually credit or debit leave balances for any employee.

| Feature | Description |
|---|---|
| Team Leave Snapshot | Table view of team leave balances across all types; flags (Low CL, SL Deficit) |
| Leave Type | CL, EL, SL, Comp-off, Maternity Leave |
| Action | Credit (➕) or Debit (➖) |
| Days | Decimal supported (e.g., 0.5) |
| Reason | Mandatory — policy correction, carry-forward, comp-off accrual, etc. |
| ESS Sync | Balance updates instantly on employee's ESS view on approval |
| Approval | Sent to HR Head for confirmation before applying |
| Leave Override Log | Full history of all overrides: employee, type, action, days, reason, by, status |

### 19.3 Bonus & Incentive Upload (TRN-013)

| Feature | Description |
|---|---|
| Bonus Types | Q1 Performance Bonus, Festive Bonus, Spot Award, Referral Bonus, Retention Bonus |
| Bulk Upload | Excel/CSV with Employee ID, Name, Amount, Remarks |
| Individual Entry | Add single employee bonus manually |
| Budget Cap | Finance-approved pool amount shown; system warns if exceeded |
| TDS Auto-Computation | TDS on bonus auto-computed and attached to batch |
| Merge to Payroll | Approved batch merged to current month payroll run |
| Approval Workflow | HR → Finance Manager → CFO (if above threshold) |
| Bonus Register | Full history by type, FY, employee |

### 19.4 Loans & Advances Processing (TRN-014)

Loan application processing using a **5-step workflow:**

```
Employee Request → HR Review → Finance Verification → CFO Approval (if above limit) → Disbursement → EMI Active
```

| Feature | Description |
|---|---|
| New Application Processing | HR reviews eligibility: tenure, CTC, existing loans, EMI cap |
| EMI Schedule Preview | Full amortisation table shown inline before approval |
| EMI Cap Validation | Warning if EMI exceeds 40% of monthly salary |
| Active Loan Register | Employee, type, principal, EMI, remaining balance, status |
| Disburse | Amount disbursed after final approval; added to next payroll |
| F&F Integration | Outstanding balance auto-deducted in Full & Final |

### 19.5 Asset Issuance & Management (TRN-015)

*(Full details in Section 24)*

---

## 20. Employee Offboarding & Full & Final (F&F) Configuration

*(Smart Transactional Page 6 — consolidates TRN-009, TRN-027, TRN-028)*

### 20.1 Resignation & Exit Workflow (TRN-009)

| Configuration | Description |
|---|---|
| Resignation Submission | Employee submits via ESS; HR can also enter on behalf |
| Last Working Day | Calculated from resignation date + notice period |
| Notice Period Waiver | Manager / HR can approve notice period buyout. Buyout amount = Remaining Notice Days × (Last Drawn Monthly Gross ÷ 30). Employee-initiated shortfall is deducted in F&F; employer-initiated waiver is paid out as notice pay and fully taxable. |
| Exit Interview | Configurable questionnaire; assigned to HR |
| Knowledge Transfer Checklist | Configure tasks to be completed before exit |

### 20.2 Multi-Department Clearance Dashboard (TRN-027)

HR sees every exiting employee's clearance status at a glance:

| Clearance Department | Items |
|---|---|
| IT | Laptop, mobile, access card, email deactivation |
| Admin | Locker key, parking pass, ID card |
| Finance | Pending reimbursements, travel advances, expense settlement |
| HR | Knowledge transfer, exit interview completion |
| Library / Others | Company property, manuals, books |

Each department head must digitally clear the employee. F&F payment is triggered automatically only after all clearances are completed.

### 20.3 Employee Separation Types

| Type | Examples | Notes |
|---|---|---|
| Voluntary Resignation | Employee-initiated | Notice period applicable |
| Retirement | Age-based (typically 58/60) | Gratuity compulsory |
| Superannuation | Fixed-term contract end | |
| Termination (For Cause) | Disciplinary action | Gratuity forfeiture rules apply |
| Layoff / Retrenchment | Organisational restructuring | Statutory compensation per ID Act |
| Death / Incapacitation | | Nominee receives all dues |
| Absconding | Unauthorised absence | Legal notice before deactivation |

### 20.4 F&F Treatment by Separation Type

The following matrix shows how key F&F components differ based on the reason for separation:

| F&F Component | Voluntary Resignation | Retirement | Termination for Cause | Layoff / Retrenchment | Death |
|---|---|---|---|---|---|
| Salary for Worked Days | ✅ Pro-rata | ✅ Pro-rata | ✅ Pro-rata | ✅ Pro-rata | ✅ Pro-rata to nominee |
| Leave Encashment | ✅ Per policy | ✅ Per policy | ✅ Per policy | ✅ Per policy | ✅ To nominee |
| Gratuity | ✅ If ≥ 5 years | ✅ Compulsory | ❌ May be forfeited per Gratuity Act S.4(6)(b) | ✅ Compulsory | ✅ Compulsory to nominee |
| Notice Pay Recovery | ✅ If short notice | ❌ None | ❌ None (no notice given) | ❌ None | ❌ None |
| Bonus (Pro-rata) | ✅ If eligible | ✅ If eligible | ❌ Forfeit at discretion | ✅ If eligible | ✅ To nominee |
| Retrenchment Compensation | ❌ None | ❌ None | ❌ None | ✅ 15 days wages per year of service (Industrial Disputes Act) | ❌ None |

### 20.5 Payroll Exception Manager for Exits (TRN-028)

Manages payroll exceptions specifically arising from employee exits:
- Mid-month exits: pro-rata calculation
- Notice period shortfall recovery
- Pending loans flagged for recovery
- Unreturned assets flagged for deduction
- All exceptions reviewed and confirmed before F&F payslip generation

---

## 21. Performance Management Configuration & Transactions

*(Smart Transactional Page 5 — consolidates TRN-021 to TRN-026)*

### 21.1 Appraisal Cycle Configuration

| Setting | Description |
|---|---|
| Appraisal Frequency | Annual / Semi-annual / Quarterly |
| Appraisal Period | e.g., April 2025 – March 2026 |
| Appraisal Start Date | When self-appraisal forms open |
| Appraisal Submission Deadline | Last date for form submission |
| Rating Scale | 1–5 or 1–10; or custom labels (Exceptional / Exceeds / Meets / Below / Poor) |
| Appraisal Participants | Self-appraisal, Manager review, Skip-level, Peer (360°) |
| Weightages | e.g., KRA: 70%, Competency: 30% |
| KRA vs Competency Split | Configurable; final rating auto-weighted |
| Mid-Year Review | Optional check-in window (configurable dates) |
| Moderation / Calibration | Group calibration after individual reviews to normalise ratings |
| Bell Curve / Forced Distribution | Configurable: e.g., 10% Exceptional (R5), 25% Exceeds (R4), 50% Meets (R3) |
| Manager Edit Window | Days after cycle close when managers can revise ratings |
| Promotion Link | Manager can recommend promotion inline; triggers salary revision workflow |
| Cycle Type Options | Annual (Apr–Mar), Annual (Jan–Dec), Semi-Annual (H1/H2), Quarterly, Monthly (Continuous), Project-Based, Rolling 90-Day |
| Lock After Submission | Yes — Manager Only Can Unlock / No — Employee Can Edit |
| Mid-Year Review Toggle | Enabled (configurable month) / Disabled |
| Reminder Frequency | Weekly (last 30 days) / Daily (last 7 days) / Manual Only |
| OEE / Production KPI Auto-Pull | When enabled, OEE and production output metrics are auto-populated as KRA inputs for production employees; eliminates manual data entry; source: Production module |
| Bell-Curve Enforcement | Configured distribution (e.g., 5% / 15% / 60% / 15% / 5%) enforced during calibration; HR calibration view flags departments deviating from configured band; HR can adjust individual ratings during calibration window; hard cap or soft warning configurable |
| Grade-Based Workflow Rules | Per-grade grid (L1–L7): configure Self-Appraisal (Skip / Simplified / Full), 360° (Skip / Simplified / Full), Calibration (Skip / Include), Increment Eligibility (Yes / No). Example: L1 Shop Floor skips self-appraisal; L7 C-Suite goes through board-driven review |

### 21.2 KRA / OKR Configuration (TRN-021)

| Setting | Description |
|---|---|
| Goal Framework | KRA (Key Result Area) / OKR (Objectives & Key Results) / SMART Goals |
| Company OKR | Defined at company level; cascades down to departments |
| Department OKR | Auto-cascaded from company OKRs; department head can add department-specific goals |
| Individual Goals | Employee sets own goals aligned to department OKRs |
| Auto-Cascade | Company → Department → Individual with one click; alignment visible |
| Goal Fields | Title, description, KPIs, weightage %, measurement method, target value |
| Mid-Year Edit Window | Configurable window for goal revision |
| Progress Tracking | % completion updated by employee; visible to manager |
| OKR Cascade Level | Options: Company → Dept → Individual; Company → Individual; Dept → Individual Only; Individual-Only (no cascade) |
| KRA Weightage Split | Default: KRA 60%, Behaviour 20%, Development 10%, Initiative 10%. Fully configurable; all weights must sum to 100% |
| Over-Achievement Cap | Maximum achievement % credited per goal (default: 120%); prevents gaming the metric with over-delivery |
| Goal Weightage Validation | Sum of all individual goals must equal 100%. System validates on save; warns if unbalanced and blocks submission |
| Mid-Year Edit Gate | Goal changes outside the configured mid-year edit window require manager approval; system enforces approval gate before saving |

### 21.3 360° Multi-Rater Feedback (TRN-022)

| Feature | Description |
|---|---|
| Anonymity | Rater identity is fully anonymous to rated employee |
| Rater Types | Self, Manager, Peers, Subordinates, Cross-function, Internal Customer |
| Minimum Raters | Configurable minimum per rater type (e.g., ≥ 3 peers) |
| Rater Selection | Employee nominates peers; HR approves rater list |
| Competency Ratings | Per-criterion rating scale (1–5) with guiding questions per criterion |
| Open Text | Greatest strength, one area to improve, "Would work with again?" |
| Response Tracking | Completion % per rater type visible to HR |
| Reminder Engine | Auto-reminders to pending raters; configurable frequency |
| Anonymity Suppression | If fewer than the configured minimum responses are received from a rater type, the 360° feedback report for that dimension is suppressed entirely to protect rater identity — particularly important in small teams |
| Open Text Handling | Open-text responses (Strength, Improvement Area, "Would Work With Again?") are presented as anonymised verbatims in the employee's development report; never attributed to a named rater |

**Standard 360° Competency Dimensions:**
- Delivery on Commitments
- Clarity & Responsiveness
- Psychological Safety (for managers)
- Collaboration & Teamwork
- Leadership & Decision-Making
- Technical Expertise / Domain Knowledge

### 21.4 Appraisal Rating & Calibration (TRN-023)

| Stage | Description |
|---|---|
| Self-Appraisal | Employee rates own KRA achievement and competencies; submits by deadline |
| Manager Review | Manager assigns final rating with comments; promotion recommendation inline |
| Calibration View | Bell-curve chart shows distribution before locking; HR can adjust |
| Skip-Level Review | Optional; configured in appraisal settings |
| HR Approval | HR signs off on all ratings before publishing |
| Rating Publication | Ratings published to employees simultaneously after HR approval |
| Increment Trigger | Rating → increment % mapping: R5 = 20%, R4 = 12%, R3 = 7%, R2 = 3%, R1 = 0% (no increment; PIP triggered) |
| PIP Auto-Trigger | Rating 1 (R1) automatically creates a Performance Improvement Plan (PIP) for the employee; HR and manager notified; PIP duration: 60–90 days configured in Section 27.2 |

### 21.5 Skill Mapping (TRN-024)

| Feature | Description |
|---|---|
| Skill Library | Pre-defined skill catalogue per function/role |
| Proficiency Scale | 1–5: **1** = Gap / Needs immediate training · **2** = Awareness / Basic conceptual knowledge · **3** = Practitioner / Can work independently · **4** = Advanced / Can coach others · **5** = Expert / Defines standards |
| Role Requirement | Each designation has required proficiency per skill |
| Skill Gap Analysis | Auto-highlights skills below required proficiency (Heatmap view) |
| Learning Plan | System auto-suggests training programs for each skill gap |
| Team Skill View | Manager sees team's collective strengths and weakest skills |
| Certification Expiry Alert | System alerts HR and employee 30 days before any mandatory certification expires; certification status visible in the skill heatmap |
| Certification Expiry Promotion Block | When a mandatory certification has expired, the promotion workflow for the affected employee is automatically blocked until the certification is renewed |
| Skill Review Frequency | Configurable: Annual (with appraisal cycle) / Semi-Annual / Quarterly |

### 21.6 Training Nominations (TRN-025)

| Feature | Description |
|---|---|
| Nomination Source | From skill gap analysis (one-click) or manual HR/manager nomination |
| Training Categories | Technical / Soft Skills / Compliance; Mandatory / Optional |
| Mode | Online / Classroom / On-the-Job |
| Budget Tracking | Per-employee training cost; department-wise budget |
| Attendance & Completion | Mark attendance; assessment score; certificate upload |
| Training Calendar | Published company training schedule visible on ESS |
| External Certifications | Track external courses, degrees, professional certifications |
| Auto-Nomination Rule | When an employee's skill proficiency drops below the configured gap threshold (≤1, ≤2, or ≤3), the system automatically creates a training nomination and recommends the appropriate programme from the skill template library; one-click approval by manager |
| Certification Renewal Nomination | When a mandatory certification is approaching expiry (30-day alert), the system auto-nominates the renewal training programme |
| Training → Skill Level Update | On training completion, the employee's proficiency level for the linked skill is auto-incremented by 1 level; HR can adjust manually |
| Mandatory Training Impact on Goals | Pending mandatory training reduces the employee's Development goal score until completion |

### 21.7 Succession Planning (TRN-026)

| Feature | Description |
|---|---|
| Critical Role Identification | Define which roles are business-critical and require a succession plan |
| Successor Nomination | List potential successors per critical role |
| Readiness Assessment | Ready Now / 1 Year / 2 Years per successor |
| 9-Box View | Performance × Potential grid for succession decisions |
| Development Plan | Action plan to prepare each successor for the critical role |
| Bench Strength | Dashboard showing overall succession coverage % |
| Flight Risk | Flag high-potential employees showing exit signals |
| HiPo Threshold Options | Top 3 cells (Top Talent + Future Star + High Performer) / Top 2 cells only / Rating 5 + Potential ≥ 4 |
| 9-Box Auto-Update | 9-box positions auto-update after each appraisal cycle closes; Performance axis from final appraisal rating; Potential axis manually updated by HR / leadership panel |
| Retention Risk Alert | HR notified automatically if a HiPo employee has not had a documented check-in conversation in 90 days |

**HiPo Development Programme:**

| Feature | Description |
|---|---|
| Accelerated Rotation Programme | HiPo employees are assigned cross-functional project rotations every 6–12 months |
| Executive Mentorship Pairing | Each HiPo is assigned a C-suite or senior leader as mentor |
| External Leadership Programme Budget | Additional learning budget allocated for HiPos above the standard training budget |
| Visible Succession Map (Toggle) | When enabled, HiPos can see which critical role(s) they are identified as a successor for |
| Zero Vacancy Alert | Critical roles with no "Ready Now" successor are highlighted in red on the succession dashboard |

### 21.8 Employee Engagement & Recognition

| Feature | Description |
|---|---|
| Pulse Surveys | Short configurable surveys (3–5 questions) sent on a configured frequency (Weekly / Bi-weekly / Monthly); anonymous responses |
| eNPS (Employee NPS) | Periodic "How likely are you to recommend this company as a workplace?" survey with trend tracking |
| Engagement Score | Rolling engagement score per department computed from pulse survey responses; visible to HR and HODs |
| Peer Recognition | Employees can send kudos / recognition to colleagues via ESS; visible on the team wall |
| Spot Award Integration | Recognition can trigger a spot award bonus (linked to Section 19.3 Bonus Upload) |
| Stay Interview Framework | Configurable questionnaire for HR to conduct stay interviews with high-risk employees; responses logged |
| Attrition Prediction | System flags employees showing combined exit signals (low engagement score + no check-in + poor rating) as flight risk |

### 21.9 Industry Preset Templates

To reduce configuration time, the system includes pre-built template libraries across 12 industries. Templates can be imported in one click and customised post-import.

| Template Category | Examples Included |
|---|---|
| **KRA / Goal Templates** | 25 role-specific goal templates (e.g., Sales Rep: Revenue target, Pipeline coverage, Win rate; Engineer: Story points, Bug fix rate, Code review; HR: Attrition %, Time-to-hire, Training completion) |
| **Competency Frameworks** | 25 pre-built competency definitions with 5-level behavioural anchors per level (e.g., Delivery, Communication, Leadership, Innovation, Customer Focus) |
| **360° Question Sets** | 25 validated question sets per competency dimension with guiding descriptions per rating level |
| **Skill Catalogues** | Industry-specific skill libraries: Manufacturing (CNC, LOTO, ISO 9001, Lean/5S, Welding), IT (Cloud/AWS, DevOps, Cybersecurity, ML/AI, Data Engineering), Healthcare (GMP, BLS/ACLS, Pharmacovigilance, EHR), Business (PMP, P&L, KAM, Data Visualisation) |
| **Critical Role Templates** | 20 critical role succession templates across C-Suite, Operations, Technical, Commercial, and Statutory categories |

**Supported Industry Presets:** Manufacturing, IT/SaaS, Healthcare/Pharma, BFSI, Retail, Logistics, Construction, Education, Hospitality, Professional Services, E-Commerce, Government/PSU.

---

## 22. Training & Learning Management Configuration

*(CFG-023 — mapped to Smart Config Page 2; transactions covered in Section 21.6)*

### 22.1 Training Catalogue Configuration

| Setting | Description |
|---|---|
| Training Name | Internal or external programme name |
| Training Type | Technical / Compliance (Mandatory) / Soft Skills / On-the-Job / E-Learning |
| Mode | Online / Classroom / Workshop / External Conference / Blended |
| Duration | Hours or days |
| Linked Skills | One or more skills from the Skill Library that this training builds |
| Proficiency Level Gain | Configured increment to proficiency on completion (default: +1 level) |
| Mandatory Flag | Yes / No; if mandatory, completion deadline is set |
| Certification | Yes / No; if yes, certification name, issuing body, validity period (years) |
| Vendor / Provider | Internal (HR-run) or External (vendor details) |
| Cost per Head | Training cost per employee; used in budget tracking |

### 22.2 Mandatory Training Configuration

| Setting | Description |
|---|---|
| Mandatory Training List | Define which trainings are mandatory (e.g., POSH, Fire Safety, ISO Awareness, LOTO) |
| Completion Deadline | Deadline from joining date or from annual cycle start |
| Non-Completion Alert | HR and manager notified when deadline approaches (30-day and 7-day alerts) |
| Impact on Goals | Pending mandatory training reduces Development goal score until completed |
| Escalation | After deadline, auto-escalation to HR Head; training recorded as overdue |

### 22.3 Training Budget & Cost Tracking

| Setting | Description |
|---|---|
| Annual Training Budget | Department-wise budget set at start of financial year |
| Per-Employee Budget | Configurable ceiling per employee per year |
| HiPo Budget Uplift | HiPo employees receive additional budget above standard |
| Budget Utilisation Dashboard | Real-time view: allocated vs. spent vs. remaining per department |
| Training Cost Report | Per-employee and per-programme cost summary for Finance |

### 22.4 Training Completion & Assessment

| Setting | Description |
|---|---|
| Attendance Marking | HR marks attendance; employee self-marks for online courses |
| Post-Training Assessment | Configurable quiz / test to validate learning; pass threshold configurable |
| Certificate Upload | Employee or HR uploads certificate; linked to employee profile and skill record |
| Completion → Skill Update | Auto-updates proficiency level for linked skill on completion |
| Training History | Full history per employee: programme, date, score, certificate, cost |

### 22.5 External Certification Tracking

| Setting | Description |
|---|---|
| Certification Name | e.g., AWS Solutions Architect, PMP, ISO 9001 Lead Auditor, LOTO Safety |
| Issuing Body | e.g., PMI, AWS, ISO |
| Issue Date | Date certification was awarded |
| Validity Period | Duration in years (e.g., 3 years for PMP, Annual for LOTO) |
| Expiry Date | Auto-calculated from issue date + validity |
| 30-Day Expiry Alert | HR and employee notified 30 days before expiry |
| Renewal Nomination | Auto-nominates renewal training on expiry alert |
| Promotion Block | Expired mandatory certification blocks promotion workflow automatically |

---

## 23. Loan, Advance & Reimbursement Configuration

*(CFG-020 — mapped to Smart Config Page 3; transactions in Section 19.4)*

### 23.1 Loan Types

| Loan Type | Config Required |
|---|---|
| Salary Advance | Max advance (e.g., 1 month gross), number of EMI months |
| Personal Loan | Max loan amount, interest rate, EMI configuration |
| Emergency / Medical Loan | Fast-track approval; higher limits for critical situations |
| Education Loan | Linked to training / professional development |
| Travel Advance | Lump-sum; recovered from expense settlement |
| Vehicle Loan (Company-subsidised) | Loan terms, interest rate, EMI from salary |

### 23.2 Loan Configuration

| Setting | Description |
|---|---|
| Maximum Loan Amount | Fixed cap or formula (e.g., 2× monthly CTC) |
| Repayment Tenure | Maximum months |
| Interest Rate | 0% (interest-free) or configured % |
| EMI Cap | Maximum % of monthly salary (e.g., 40%) |
| EMI Preview Calculator | Inline amortisation table |
| Approval Levels | HR → Finance → CFO (if above limit) |
| Eligibility Criteria | Min tenure, employment type, no existing pending loan |
| Prepayment | Allow/disallow early repayment |
| F&F Recovery | Outstanding balance auto-deducted in Full & Final |

### 23.3 Reimbursement Types

| Type | Description | Tax Treatment |
|---|---|---|
| Medical Reimbursement | Bills for self/family treatment | Up to ₹15,000/year exempt (Old Regime) |
| LTA Reimbursement | Travel costs for LTA claim | Exempt u/s 10(5) — conditions apply |
| Internet / Phone Allowance | Monthly bill reimbursement | Taxable if above prescribed limit |
| Fuel Allowance | Petrol bills for official use | Company policy-based |
| Business Travel | Hotels, flights, meals on official trips | Non-taxable with receipts |
| Uniform Allowance | Purchase of company uniform | Non-taxable up to prescribed limit |

---

## 24. Asset Management Configuration

*(CFG-025 — mapped to Smart Config Page 2; transactions in Section 19.5)*

### 24.1 Asset Category Master

| Category | Examples |
|---|---|
| Laptop / Desktop | MacBook Pro, Dell Laptop, iMac |
| Mobile Phone | iPhone, Samsung, Company handset |
| Monitor / Peripherals | Monitor, keyboard, mouse, webcam |
| Access Card | Building entry card, floor pass |
| Vehicle | Company car, scooter |
| SIM Card | Company-issued SIM |
| Keys | Office key, locker key |
| Others | Books, uniforms, tools, equipment |

**Per Category Configuration:**
- Depreciation Rate (% per year) — auto-suggested based on category
- Return Checklist Items (items to verify on return)
- E-Sign Required toggle for asset acknowledgement receipt

### 24.2 Asset Master Record

| Field | Description |
|---|---|
| Asset Name | e.g., "MacBook Pro 14" M3" |
| Category | From Asset Category Master |
| Serial Number | Unique device identifier |
| Purchase Date | |
| Purchase Value | Original cost |
| Condition | New / Like New / Good / Fair |
| Current Status | In Stock / Assigned / Under Repair / Pending Return / Retired |

### 24.3 Asset Issuance

| Feature | Description |
|---|---|
| Assign To | Employee (search by name or ID) |
| Issue Date | Date of handover |
| E-Sign Dispatch | Asset acknowledgement sent to employee's mobile/email immediately on save |
| Notes | Pre-loaded software, condition notes, special instructions |

### 24.4 Asset Return & Exit Tracking

| Feature | Description |
|---|---|
| Exit Checklist | All assets assigned to the exiting employee auto-listed |
| Return Status | Returned / Pending / Not Yet Returned (with deadline) |
| Condition on Return | Good / Damaged / Lost |
| F&F Deduction | If asset not returned or damaged, deduction included in F&F |
| Pending Return Dashboard | Shows all assets pending return from exiting employees |

### 24.5 Asset Reports

| Report | Description |
|---|---|
| Total Asset Inventory | All assets by category and status |
| Assigned Assets | Assets assigned per employee |
| In Stock | Assets available for issuance |
| Under Repair | Assets currently with service centre |
| Pending Return | Assets not yet returned by exited employees |
| Asset Depreciation | Book value per asset |

---

## 25. Travel & Expense Management Configuration

| Configuration | Description |
|---|---|
| Travel Grades | Define travel entitlements by grade (air class, hotel category) |
| Daily Allowance (DA) | City-wise per diem rates |
| Advance Request | Employee requests travel advance before trip |
| Expense Claim Submission | Post-trip expense claim with bill uploads |
| Receipt Upload | Mandatory for claims above ₹N |
| Approval Workflow | Manager → Finance approval |
| Expense Policies | Company travel policy document linkable to claim form |
| GST on Expenses | Capture GST invoice details for input credit |
| Integration with Payroll | Approved claims auto-added to payroll month |

---

## 26. HR Letters & Certificates

HR letters are auto-generated with employee data pre-filled. All letters can be previewed before generation and dispatched via Email, WhatsApp, or PDF download.

### 26.1 Letter Types

| Letter Type | Description | Auto-Triggered |
|---|---|---|
| Offer Letter | Candidate offer with CTC, designation, joining date | On offer creation in ATS |
| Appointment Letter | Formal employment letter on joining | On employee record creation |
| Confirmation Letter | Post-probation employment confirmation | On probation confirmation |
| Experience Certificate | Total experience in the organisation | On exit/F&F completion |
| Relieving Letter | Confirmation of last working day | On exit/F&F completion |
| Promotion Letter | New designation and grade | On promotion approval |
| Salary Revision Letter | New CTC breakup and effective date | On salary revision approval |
| Bank / Visa Salary Certificate | Salary confirmation for bank or visa purposes | On-demand |
| Transfer Letter | New location, reporting manager, effective date | On transfer approval |
| Disciplinary Warning Letter | Verbal / written warning details | On discipline action creation |
| Show Cause Notice (SCN) | Formal notice with charges and reply deadline | On SCN creation |
| PIP Letter | Performance Improvement Plan terms | On PIP creation |
| Suspension Letter | Suspension order with duration | On suspension action |
| Resignation Acceptance | Acceptance of resignation and notice terms | On resignation approval |

### 26.2 Letter Generation

| Field | Description |
|---|---|
| Employee | Search by name or ID |
| Letter Type | From above list |
| Effective Date | Date to appear on the letter |
| Additional Notes | Custom text to include in the letter body |
| Preview | View letter before generation |
| Delivery | Email + PDF Download / WhatsApp + Email / PDF Only |

### 26.3 Letter Templates

| Feature | Description |
|---|---|
| Variable Tokens | Templates use tokens: `{employee_name}`, `{designation}`, `{department}`, `{ctc}`, `{effective_date}` |
| Company Branding | Company logo and letterhead auto-applied |
| E-Sign Integration | Letters dispatched with e-sign request; acceptance tracked |
| History | Recently generated letters visible with timestamp and recipient |

---

## 27. Grievance & Discipline Management

*(CFG-026 — mapped to Smart Config Page 2)*

### 27.1 Grievance Configuration

| Setting | Description |
|---|---|
| Grievance Categories | Compensation, Workplace Harassment, Discrimination, Work Conditions, Management, Peers, Policy Violation, Other |
| SLA per Category | Hours by which grievance must be acknowledged and resolved |
| Auto-Escalation | If SLA breached, auto-escalate to next level (HR Head → CHRO) |
| Anonymity Option | Employee can submit anonymously (if policy allows) |
| POSH Committee | Internal Complaints Committee (ICC) cases tracked separately |

**Grievance SLA Configuration:**

| Category | SLA (Hours) | Auto-Escalate To |
|---|---|---|
| Workplace Harassment | 24 hours | CHRO |
| POSH / Sexual Harassment | 24 hours | ICC Chairperson |
| Compensation Dispute | 72 hours | HR Head |
| Work Conditions | 72 hours | HR Manager |
| General Grievance | 120 hours | HR Manager |

### 27.2 Discipline & Warning Management (TRN — HR Operations)

HR can issue disciplinary actions with formal document generation:

| Action Type | Description |
|---|---|
| Verbal Warning | Counselling conversation; logged in system |
| Written Warning | Formal warning letter; e-signed by HR and employee |
| Show Cause Notice (SCN) | Formal notice with charges; reply deadline set (e.g., 7 days) |
| Performance Improvement Plan (PIP) | 60–90 day improvement plan with KPIs; progress reviews |
| Suspension | Suspension order with duration and pay-during-suspension policy |
| Termination Notice | Formal termination with last working day and dues |

**Discipline Action Form:**
- Employee (search by name/ID)
- Action Type (from above)
- Charge / Reason (mandatory text description)
- Reply Due By (for SCN)
- Auto-generates and dispatches action letter on save

**Active Case Tracking:**
- Case reference number
- Status: SCN Issued / Reply Received / PIP Active / Resolved / Closed
- Timeline of all actions in the case

**PIP Outcome Workflow:**

| Outcome | Next Action |
|---|---|
| PIP Success (goals met within 60–90 days) | Case marked Resolved; employee returns to standard performance cycle; no adverse notation |
| PIP Partial Success | Manager may grant 1× extension (up to 30 days) with HR approval |
| PIP Failure (goals not met) | Manager submits PIP Failure Report → HR review → Termination recommendation → Legal sign-off → Termination notice issued. F&F includes: salary for worked days, leave encashment, and pro-rata statutory dues. Gratuity may be withheld per Gratuity Act Section 4(6)(b) if termination is for misconduct. |

---

## 28. Statutory Compliance Operations Dashboard

### 28.1 Compliance Dashboard Metrics

| Metric | Description |
|---|---|
| Filed On Time | % of filings submitted before deadline (MTD) |
| Due This Week | Count of filings due within 7 days (action needed) |
| Penalties | Total penalties incurred (target: ₹0) |
| Alert System | Due date alerts sent 7 days before each filing deadline |
| Penalty Tracker | Flags late filings with estimated penalty amounts |

### 28.2 Compliance Coverage

All of the following are tracked, filed, and managed from the Compliance Dashboard:

| Statutory | Portal / Filing | Frequency |
|---|---|---|
| Provident Fund (PF) | EPFO — ECR 2.0 | Monthly |
| Employee State Insurance (ESI) | ESIC Portal | Monthly |
| Professional Tax (PT) | State PT Portals | Monthly / Semi-annual |
| TDS / Income Tax | TRACES / NSDL | Monthly (deduction) + Quarterly (return) |
| Labour Welfare Fund (LWF) | State LWF Portals | Monthly / Annual |
| Gratuity | LICI / Private Trust | Annual provision |
| Bonus | Internal | Annual |
| POSH Report | Internal / Regulatory | Annual |

---

## 29. Audit Trail & Data Governance

*(CFG-032, Section S9 — HR Operations Audit Trail)*

### 29.1 What is Logged

Every action in the HRMS creates an immutable audit log entry:

| Logged Event | Details Captured |
|---|---|
| Employee Record Created / Modified | Field name, old value, new value, changed by (user ID, name, role), timestamp, IP |
| Salary Revision | Old CTC, new CTC, revised by, effective date |
| Attendance Override | Date, old record, new record, reason, approved by |
| Leave Override | Employee, leave type, action (credit/debit), days, reason, approved by |
| Payroll Processed | Month, total amount, processed by, approval chain |
| Login / Logout | User, timestamp, IP, session duration |
| Bulk Import Executed | Import type, records imported/skipped/failed, by |
| Role / Permission Changed | Old permission, new permission, changed by |
| Document Upload | File name, uploaded by, timestamp |
| Disciplinary Action | Action type, employee, issued by, timestamp |
| Data Export | Data type, exported by, timestamp, recipient |

### 29.2 Audit Trail Features

| Feature | Description |
|---|---|
| Immutability | Audit records cannot be edited or deleted — not even by Super Admin |
| Full Attribution | Every record has: user ID, name, role, IP address, timestamp |
| Anomaly Detection | System flags unusual patterns: bulk edits, after-hours access, mass deletions |
| Search & Filter | Filter audit log by user, date range, event type, employee |
| Export | Audit log exportable as CSV or PDF for compliance review |
| Retention | 7 years by default; configurable per industry regulation |

---

## 30. Reports & Analytics Configuration

### 30.1 Standard HRMS Reports

| Report | Frequency | Audience |
|---|---|---|
| Headcount Report | On-demand | HR, Management |
| Attrition Report | Monthly / Quarterly | HR, Management |
| Payroll Summary | Monthly | Finance, HR |
| Payslip (individual) | Monthly | Employee |
| CTC Statement | Annual | HR, Finance |
| Salary Register | Monthly | Finance, Audit |
| Attendance Summary | Monthly | HR, Manager |
| Late Comers Report | Weekly / Monthly | HR, Manager |
| Leave Balance Report | On-demand | HR |
| Leave Utilisation Report | Monthly / Annual | HR |
| Absenteeism Report | Weekly / Monthly | HR, Manager |
| OT Summary | Monthly | Finance, Operations |
| PF ECR Report | Monthly | HR, Compliance |
| ESI Contribution Statement | Monthly | HR, Compliance |
| PT Deduction Summary | Monthly | HR, Finance |
| TDS Deduction Report | Monthly / Quarterly | Finance |
| Form 24Q | Quarterly | Finance, Compliance |
| Form 16 | Annual | All employees |
| Gratuity Provision Report | Annual | Finance |
| Bonus Provision Report | Annual | Finance |
| New Joiners Report | Monthly | HR |
| Exit / Resigned Employees Report | Monthly | HR |
| Employee Anniversary Report | Monthly | HR |
| Training Completion Report | Quarterly | HR, L&D |
| Skill Gap Report | On-demand | HR, Management |
| Performance Rating Distribution | Post-appraisal cycle | HR, Management |
| Loan Outstanding Register | Monthly | Finance, HR |
| Asset Inventory Report | Monthly | Admin, HR |
| Disciplinary Case Log | On-demand | HR, Legal |
| Bonus Distribution Report | Per batch | Finance, HR |
| Correction Log (Attendance) | Monthly | HR, Manager |
| Leave Override Log | Monthly | HR |

### 30.2 Analytics Dashboards

| Dashboard | KPIs Displayed |
|---|---|
| HR Overview Dashboard | Total headcount, new joiners, exits, open positions |
| Payroll Dashboard | Total payroll cost, average CTC, month-over-month trend |
| Attendance Dashboard | Average attendance %, late comers, absenteeism rate |
| Leave Dashboard | Leave utilisation %, leave type distribution |
| Compliance Dashboard | PF/ESI/PT payment status, pending filings, penalty tracker |
| Attrition Dashboard | Attrition %, department-wise, trend analysis |
| Performance Dashboard | Avg rating by dept, bell curve distribution, promotions |
| Recruitment Dashboard | Open positions, pipeline strength, time-to-hire, offer acceptance rate |
| Training Dashboard | Completion %, budget utilisation, mandatory training coverage |
| Succession Dashboard | Bench strength %, critical roles covered, readiness levels |

---

## 31. HRMS Integration with Other Modules & External Systems

### 31.1 HRMS ↔ Finance / Accounts

| Integration Point | Data Flow |
|---|---|
| Payroll Journal Entry | Monthly salary journal posted to GL accounts |
| Statutory Liability Booking | PF/ESI/PT accruals booked as liability |
| Gratuity Provision | Monthly provision entry to GL |
| Bonus Provision | Annual provision entry |
| Loan Disbursement | Employee loan amount debited from company accounts |
| Reimbursement Payment | Expense claims settled via accounts |
| Cost Centre Allocation | Payroll costs tagged to respective cost centres |

**ERP Connector Configuration:**

| Connector | Description |
|---|---|
| Tally ERP 9 / Tally Prime | Enter Tally server URL + API key; bi-directional payroll journal sync on payroll run |
| SAP | OAuth-based connection; map HRMS cost centres to SAP GL codes |
| QuickBooks | OAuth connection; payroll expense sync |
| Oracle Financials | API-based integration; GL and cost centre mapping |

### 31.2 HRMS ↔ Internal Payroll Engine

| Handshake | Description |
|---|---|
| Attendance ↔ Payroll | Approved attendance data (present days, LOP, OT hours) feeds payroll |
| Leave ↔ Payroll | LOP days deducted; leave encashment amount added |
| Loan ↔ Payroll | EMI amounts auto-deducted in payroll |
| Reimbursements ↔ Payroll | Approved claims added to payslip |
| Salary Revision ↔ Payroll | Revised CTC effective date determines arrears |
| Employee Status ↔ Payroll | Exited employees excluded from next payroll run |
| Bonus ↔ Payroll | Approved bonus batches merged to payroll month |

### 31.3 HRMS ↔ Production / Operations (Manufacturing)

| Integration Point | Description |
|---|---|
| Shift Master | Shared shift data drives employee attendance and production planning |
| Employee to Machine Mapping | Operator assignment to machines for production tracking |
| Attendance at Plant Level | Plant-level attendance feeds into production OEE calculations |
| Holiday Calendar | Company holidays affect production scheduling |
| Overtime Hours | OT logged in HRMS cross-referenced with production records |
| Production Incentive | Machine-wise output linked to HRMS payroll incentive component |

### 31.4 HRMS ↔ Biometric / Access Control Devices

| Integration | Configuration |
|---|---|
| ZKTeco / ESSL / Realtime | Device IP, push SDK, employee enrollment via software |
| Smart Card / RFID | Card-to-employee mapping, reader IP config |
| Face Recognition | Camera setup, face model training, live comparison |
| GPS / Mobile App | Geo-fence coordinates from Branch setup, GPS tolerance setting |
| Fingerprint | Enrollment via device or software |
| Data Sync | Real-time push or scheduled pull; missing punch alerts |

### 31.5 HRMS ↔ Government Statutory Portals

| Portal | Integration Type |
|---|---|
| EPFO Unified Portal | ECR file export for PF uploads; UAN management; auto-submit on payroll close |
| ESIC Portal | Challan export; IP registration; Form 1 generation; auto-filing |
| TRACES / Income Tax (NSDL) | Form 24Q export; Form 16 generation; bulk download |
| MCA / ROC | No direct integration; data used for filings |
| State PT Portals | PT challan export per state |
| DPIIT / MSME | No direct integration; data reference |

### 31.6 E-Sign Integration

| Setting | Description |
|---|---|
| Provider | Choose: Aadhaar eSign / DigiSign / SignDesk |
| API Key | Paste provider API key; system handles the rest |
| Documents Requiring E-Sign | Configurable: offer letters, asset receipts, warning letters, F&F settlements |
| Signature Tracking | Signed / Pending / Declined status per document |
| Mobile / Email Dispatch | E-sign request sent to employee's mobile and email immediately |

### 31.7 HRMS ↔ Communication Platforms

| Platform | Integration |
|---|---|
| Email (SMTP) | Payslip, Form 16, notifications via configured SMTP server |
| WhatsApp Business API | Salary alerts, leave status, payslip (optional) |
| SMS Gateway | OTP, salary credit SMS |
| Microsoft Teams / Slack | HR chatbot for leave balance queries, announcements (optional) |

### 31.8 Banking Integration

| Setting | Description |
|---|---|
| Bank Selection | HDFC / ICICI / SBI / Axis / Kotak / Other |
| Salary File Format | Bank-specific NEFT/RTGS format |
| Auto-Push | Salary file auto-pushed to bank on payroll approval |
| Failed Payment Handling | Alert on bounced payments; re-attempt logic |

### 31.9 HRMS ↔ Third-Party HRMS / ERP (Migration / Co-existence)

| Scenario | Description |
|---|---|
| Data Migration from Legacy HRMS | Import historical employee data, leave balances, payroll history |
| API Integration | REST API for real-time sync with external systems |
| Single Sign-On (SSO) | SAML / OAuth SSO with company's identity provider (Google Workspace, Azure AD) |

---

## 32. HRMS Go-Live Readiness Checklist

### Phase 1: Organisation Setup
- [ ] Department Master created and complete (codes, heads, cost centres)
- [ ] Designation Master created (codes, levels, probation period, notice period)
- [ ] Grade / Band Master configured with CTC ranges
- [ ] Employee Type Master configured with all statutory flags
- [ ] Cost Centre Master linked to Finance GL codes
- [ ] Reporting hierarchy defined
- [ ] Work location categories configured

### Phase 2: Employee Data
- [ ] All active employee records created (6-tab form complete)
- [ ] Personal, contact, and employment details complete
- [ ] PAN, Aadhaar, UAN, bank details captured for all employees
- [ ] Nominee details added
- [ ] Profile photos uploaded (optional)
- [ ] All onboarding documents uploaded and verified
- [ ] Employee ID format (No Series) confirmed

### Phase 3: Attendance
- [ ] Attendance capture method configured
- [ ] Biometric devices enrolled and synced (if applicable)
- [ ] Shift assignment completed for all employees
- [ ] Roster patterns assigned per employee type
- [ ] Attendance rules configured (grace period, half-day threshold, LOP rate)
- [ ] Geo-fencing coordinates set for all branches
- [ ] Overtime rules configured
- [ ] Holiday calendar published for current year

### Phase 4: Leave Management
- [ ] All leave types created and configured (accrual, carry-forward, encashment)
- [ ] Leave policies assigned to all employees/grades
- [ ] Opening leave balances entered for existing employees
- [ ] Holiday calendar linked to leave management
- [ ] Approval workflow configured per leave type
- [ ] Probation restrictions set per leave type

### Phase 5: Payroll
- [ ] All salary components created (earnings, deductions, employer contributions)
- [ ] Salary structures created per grade/designation
- [ ] Each employee's CTC entered and salary structure assigned
- [ ] Payroll run cycle confirmed (cut-off day, disbursement day)
- [ ] Bank details verified for all employees
- [ ] PF/ESI/PT configurations verified
- [ ] LOP calculation method set (÷ 26 / ÷ 30 / ÷ Working Days)
- [ ] Rounding rules configured

### Phase 6: Statutory Compliance
- [ ] PF registration and settings configured (ECR format verified)
- [ ] ESI settings verified (eligibility threshold, rates)
- [ ] PT slabs configured for all applicable states
- [ ] Gratuity and Bonus settings configured
- [ ] TDS regime defaults set (Old / New)
- [ ] Investment declaration window opened for employees

### Phase 7: ESS Portal
- [ ] ESS portal URL shared with all employees
- [ ] Login credentials distributed
- [ ] ESS features enabled as per policy
- [ ] Employee training on ESS completed
- [ ] MSS features enabled for all managers
- [ ] AI chatbot configured (if enabled)

### Phase 8: RBAC & Workflows
- [ ] All user roles configured with correct permissions
- [ ] Field-level masking applied for sensitive fields
- [ ] All approval workflows configured (leave, attendance, payroll, loan, resignation)
- [ ] SLA and escalation rules set for each workflow
- [ ] Notification rules configured for all key events

### Phase 9: Integration Verification
- [ ] Finance GL codes mapped to payroll components
- [ ] Biometric sync tested and verified (test punch processed)
- [ ] Payroll bank file format tested with bank
- [ ] Statutory report formats verified
- [ ] Form 16 / 24Q test generation done
- [ ] E-sign integration tested
- [ ] ERP connector tested (if Tally/SAP/QuickBooks used)

### Phase 10: First Payroll Run
- [ ] Test payroll run completed in staging environment
- [ ] Outputs verified (payslips, statutory amounts, bank totals)
- [ ] Variance report reviewed
- [ ] Finance sign-off obtained
- [ ] First live payroll processed (6-step wizard completed)
- [ ] Payslips distributed to employees
- [ ] Statutory payments initiated (PF ECR, ESI challan, PT challan, TDS)

### Phase 11: Post-Go-Live Monitoring
- [ ] Attendance sync monitored for first week
- [ ] Leave applications tested end-to-end
- [ ] Payroll accuracy verified after first live run
- [ ] Employee feedback on ESS collected
- [ ] First appraisal cycle initiated (if within FY)
- [ ] Audit trail reviewed for completeness
- [ ] Support escalation matrix configured

### Phase 12: Performance & Engagement Setup
- [ ] Appraisal cycle configuration complete (cycle type, dates, rating scale, grade-based rules)
- [ ] KRA weightage split configured (KRA/Behaviour/Development/Initiative must sum to 100%)
- [ ] OKR cascade structure defined (Company → Dept → Individual)
- [ ] Bell-curve distribution % configured and calibration workflow set up
- [ ] 360° feedback questionnaire configured (competencies, minimum raters, anonymity rules)
- [ ] Skill library populated or industry preset imported
- [ ] Mandatory certifications identified and linked to promotion workflow
- [ ] Succession planning critical roles mapped (at least top 5)
- [ ] HiPo threshold and development programme configured
- [ ] Employee engagement pulse surveys configured (frequency, questions)
- [ ] eNPS baseline survey sent to all employees

---

*Document End — Avy ERP HRMS Module Configuration Guide v2.0*  
*Maintained by Avyren Technologies — Product & HR-Tech Team*  
*This document is the single source of truth for the HRMS module. All sub-module configurations, transactional workflows, and integration specifications are covered herein.*
*Last Reviewed & Updated: March 2026 — Version 2.1*
