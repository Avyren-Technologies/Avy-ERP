# Avy ERP — Master Product Requirements Document
## Part 3: Module Specifications — HR Management, Security & Visitor Management

> **Product:** Avy ERP
> **Company:** Avyren Technologies
> **Document Series:** PRD-003 of 5
> **Version:** 2.0
> **Date:** April 2026
> **Status:** Final Draft · Confidential
> **Scope:** Full module definitions for HR Management (HRMS), Security, and Visitor Management

---

## Table of Contents

1. [Module 7 — HR Management (HRMS)](#1-module-7--hr-management-hrms)
   - 1.1 [Module Overview & Sub-Modules](#11-module-overview--sub-modules)
   - 1.2 [Organisational Structure](#12-organisational-structure)
   - 1.3 [Employee Master](#13-employee-master)
   - 1.4 [Recruitment & ATS](#14-recruitment--ats)
   - 1.5 [Onboarding Workflow](#15-onboarding-workflow)
   - 1.6 [Attendance Management](#16-attendance-management)
   - 1.7 [Leave Management](#17-leave-management)
   - 1.8 [Payroll Engine](#18-payroll-engine)
   - 1.9 [Statutory Compliance](#19-statutory-compliance)
   - 1.10 [TDS & Income Tax](#110-tds--income-tax)
   - 1.11 [Employee Self-Service (ESS)](#111-employee-self-service-ess)
   - 1.12 [Performance Management](#112-performance-management)
   - 1.13 [Training & Learning Management](#113-training--learning-management)
   - 1.14 [Loans, Advances & Reimbursements](#114-loans-advances--reimbursements)
   - 1.15 [Travel & Expense Management](#115-travel--expense-management)
   - 1.16 [HR Letters & Certificates](#116-hr-letters--certificates)
   - 1.17 [Grievance & Discipline Management](#117-grievance--discipline-management)
   - 1.18 [Employee Offboarding & Full & Final Settlement](#118-employee-offboarding--full--final-settlement)
2. [Module 3 — Security](#2-module-3--security)
   - 2.1 [Module Overview](#21-module-overview)
   - 2.2 [Employee Gate Attendance](#22-employee-gate-attendance)
   - 2.3 [Goods Verification](#23-goods-verification)
   - 2.4 [Gate Management Operations](#24-gate-management-operations)
3. [Module 9 — Visitor Management](#3-module-9--visitor-management)
   - 3.1 [Module Overview](#31-module-overview)
   - 3.2 [Visitor Lifecycle](#32-visitor-lifecycle)
   - 3.3 [Visitor Types & Classification](#33-visitor-types--classification)
   - 3.4 [Pre-Registration & Invitation](#34-pre-registration--invitation)
   - 3.5 [Walk-In Visitor Flow](#35-walk-in-visitor-flow)
   - 3.6 [QR Self-Registration](#36-qr-self-registration)
   - 3.7 [Check-In Process](#37-check-in-process)
   - 3.8 [Safety Induction at Check-In](#38-safety-induction-at-check-in)
   - 3.9 [Visitor Badge & Identification](#39-visitor-badge--identification)
   - 3.10 [Host Notification & Approval](#310-host-notification--approval)
   - 3.11 [On-Site Tracking & Check-Out](#311-on-site-tracking--check-out)
   - 3.12 [Today's Visitors Dashboard](#312-todays-visitors-dashboard)
   - 3.13 [Watchlist & Blocklist](#313-watchlist--blocklist)
   - 3.14 [Emergency Evacuation & Muster Management](#314-emergency-evacuation--muster-management)
   - 3.15 [Contractor & Vendor Visit Management](#315-contractor--vendor-visit-management)
   - 3.16 [Group Visit & Event Management](#316-group-visit--event-management)
   - 3.17 [Recurring Visitor & Frequent Visitor Pass](#317-recurring-visitor--frequent-visitor-pass)
   - 3.18 [Vehicle & Material Gate Pass](#318-vehicle--material-gate-pass)
   - 3.19 [Multi-Gate & Multi-Plant Support](#319-multi-gate--multi-plant-support)

---

## 1. Module 7 — HR Management (HRMS)

### 1.1 Module Overview & Sub-Modules

The HR Management module is the **central system of record for all people-related data** in the organisation. It covers the full employee lifecycle — from requisition and recruitment through onboarding, attendance, payroll, compliance, performance, and exit.

The HRMS is tightly integrated with the Security module (which provides raw attendance timestamps), the Production module (which provides the output quantities used for incentive calculations), and the Finance module (which receives processed payroll as salary payable journal entries).

**HRMS Sub-Modules:**

```
HRMS
├── Organisational Structure
│     ├── Department Master
│     ├── Designation / Job Title Master
│     ├── Grade / Band Master
│     └── Reporting Hierarchy
├── Employee Master (Core data, documents, employment history)
├── Recruitment & ATS
│     ├── Job Requisition Management
│     ├── Job Posting
│     ├── Applicant Tracking Pipeline
│     └── Offer Management
├── Onboarding (Joining workflow, document collection, checklist)
├── Attendance Management
│     ├── Biometric / Face Scan Attendance
│     ├── Mobile GPS Attendance
│     ├── Manual Attendance Entry
│     └── Rotational Shift Attendance
├── Leave Management
│     ├── Leave Type Master
│     ├── Leave Policy
│     ├── Holiday Calendar
│     └── Leave Request & Approval Workflow
├── Payroll
│     ├── Salary Structure Master
│     ├── Payroll Processing Engine (6-Step Run Wizard)
│     └── Bank Disbursement
├── Statutory Compliance
│     ├── PF (Provident Fund)
│     ├── ESI (Employee State Insurance)
│     ├── PT (Professional Tax)
│     ├── LWF (Labour Welfare Fund)
│     ├── Gratuity
│     └── Bonus
├── TDS & Income Tax (Form 16, 24Q, IT Declarations)
├── Employee Self-Service (ESS) Portal
├── Manager Self-Service (MSS)
├── Performance Management (KRA/OKR, Appraisals, 360°, Succession)
├── Training & Learning Management (LMS, Skill Mapping)
├── Loan & Advance Management
├── Travel & Expense Management
├── Asset Management (Employee-assigned assets)
├── HR Letters & Certificates
├── Grievance & Discipline Management
└── Offboarding & Full & Final Settlement (F&F)
```

**Smart Configuration Philosophy:** The HRMS follows a mobile-first, single-page smart-sections approach. All 32 original configuration screens are consolidated into 6 Smart Configuration Pages; all 28 transactional screens are consolidated into 6 Smart Transactional Pages. Fields are context-aware and appear only when relevant.

### 1.2 Organisational Structure

The organisational structure is configured before any employees are added, as all employee records reference these masters.

**Department Master:**
Each department in the organisation is registered with: Department Name, Department Code, Department Head (employee reference), Cost Centre Code (linked to Finance), Parent Department (for nested hierarchies), and Status.

**Designation / Job Title Master:**
Each job title in the organisation: Designation Name, Designation Code, linked Department (default), linked Grade/Band, Job Level (Junior / Mid / Senior / Lead / Manager / Director / C-Suite), Status.

**Grade / Band / Level Master:**
Grades group employees at similar compensation levels: Grade Code, Grade Name, CTC Range (Min/Max), HRA Percentage, Leave Entitlement Override, Probation Period, Notice Period, Status.

**Reporting Hierarchy:**
Each employee record designates a reporting manager. The system builds the reporting tree automatically. This tree governs approval routing for leave, expense, and exit requests.

### 1.3 Employee Master

The Employee Master is the central record for every person in the organisation. It is the source of truth for all HR, payroll, and compliance operations.

**Employee Master Data Sections:**

| Section | Key Fields |
|---|---|
| Personal Information | Full name, date of birth, gender, nationality, marital status, personal email, personal phone |
| Employment Information | Employee ID (auto-generated by No Series), joining date, employment type (full-time/contract/intern), department, designation, grade, plant, branch, reporting manager |
| Contact & Address | Permanent address, current address, emergency contact details |
| Bank Details | Bank name, account number, IFSC code, account type (for payroll disbursement) |
| Identification Documents | PAN, Aadhaar, Passport, Voter ID, Driving Licence — with upload |
| Statutory Details | PF account number, UAN (Universal Account Number), ESI IP number |
| Salary Details | CTC, salary structure assignment, individual component overrides |
| Documents | Offer letter, joining letter, previous experience certificates, educational certificates |
| Employment History | Previous employers, roles, tenure |

**Employee States:** Active, On Probation, On Notice Period, Resigned, Terminated, Absconded.

### 1.4 Recruitment & ATS

The Applicant Tracking System (ATS) manages the full pipeline from job requisition to offer acceptance.

**Recruitment Workflow:**

1. **Job Requisition** — Department head raises a request for a new hire; HR approves and converts to a job posting
2. **Job Posting** — Posted internally, externally, or on job boards; tracks application channel
3. **Application Screening** — Applications received and assigned a screening status
4. **Interview Pipeline** — Multi-stage interview rounds (Phone Screen → Technical Round → HR Round → Final); each stage has a pass/fail/hold disposition
5. **Offer Management** — Approved candidates receive an offer letter (auto-generated from template); candidate can accept or decline
6. **Pre-Joining** — Accepted candidates enter the pre-onboarding flow; document collection begins before joining date

**Key metrics tracked:** Time-to-fill, source of hire, interview-to-offer ratio, offer acceptance rate.

### 1.5 Onboarding Workflow

When a new employee's joining date arrives, the system triggers the onboarding workflow:

- Welcome email sent automatically with login credentials
- Onboarding checklist assigned: document submission, policy acknowledgements, asset assignment, IT setup
- System access provisioned based on role assignment
- First-day tasks and buddy assignment (configurable)
- Probation period tracked with scheduled review reminders

### 1.6 Attendance Management

Attendance is the foundational input to payroll. Avy ERP supports four attendance capture methods:

**Method 1 — Biometric / Face Scan (via Security Module):**
Biometric devices at the facility gate capture punch-in and punch-out timestamps. The Security module receives these events and the HR module consumes them automatically. This is the primary attendance source for most manufacturing facilities.

**Method 2 — Mobile GPS Attendance:**
Employees with mobile app access can mark attendance from their phone. The app captures GPS coordinates at the time of marking. The system validates that the GPS coordinates fall within the configured geo-fencing radius for the employee's assigned branch. Geo-fencing enforcement is a configurable toggle per tenant.

**Method 3 — Manual Entry:**
HR Managers can manually enter or correct attendance records. Manual overrides are logged in the audit trail with the reason and the authorising user.

**Method 4 — Rotational Shift Attendance:**
For employees on rotating shift schedules, the attendance calculation engine determines the applicable shift for each day based on the rotational schedule configuration.

**Attendance Processing Logic:**

| Working Hours | Status |
|---|---|
| ≥ Full Day Threshold (configurable, e.g., 8 hours) | Full Day Present |
| ≥ Half Day Threshold (configurable, e.g., 4 hours) | Half Day Present |
| < Half Day Threshold | Absent |
| No punch recorded | Absent (with LOP flag unless leave applied) |

**Attendance Regularisation:** An employee can submit a regularisation request for a missed punch (e.g., forgot to scan at gate). The request goes through the approval workflow. Approved regularisations update the attendance record without overwriting the original.

### 1.7 Leave Management

**Leave Type Master:**
The company configures all leave types applicable to their workforce. Each leave type carries:

| Field | Options / Notes |
|---|---|
| Leave Type Name | Earned Leave, Casual Leave, Sick Leave, Maternity Leave, Paternity Leave, Comp Off, etc. |
| Accrual Frequency | Monthly, Quarterly, Annually, or At-Once allocation |
| Accrual Rate | Number of days per period |
| Carry Forward | Whether unused balance carries to the next year; maximum carry-forward limit |
| Encashment | Whether unused leave can be encashed; applicable conditions |
| Applicable Gender | All / Male / Female (for maternity/paternity) |
| Minimum Tenure Required | Leaves applicable only after N months of service |
| Maximum Continuous Days | Maximum consecutive days allowed per application |
| Backdated Application Allowed | Whether past-date leave can be applied for |
| Requires Document | Medical certificate, etc. |

**Leave Policy:**
Leave policies bundle leave type entitlements and are assigned to employee grades or departments. This allows different grades to have different annual leave entitlements.

**Holiday Calendar:**
A company-wide or plant-specific list of public holidays and company-declared holidays for the year. Holidays are excluded from leave calculations.

**Leave Request Workflow:**
1. Employee submits leave request (mobile or ESS portal) specifying type, dates, and reason
2. System checks leave balance and policy rules; blocks submission if balance insufficient
3. Request routed to reporting manager for approval
4. Manager approves or rejects with comments
5. Employee notified via push notification and email
6. Approved leave is reflected in the attendance dashboard and payroll deduction engine

### 1.8 Payroll Engine

The Payroll Engine is the computational core of the HRMS. It processes gross and net salary for every employee in a 6-step run wizard.

**Payroll Formula:**
> **Net Pay = (Basic + HRA + Conveyance + Special Allowances + Incentives) − (PF Employee Share + ESI Employee Share + PT + TDS + Loan EMI + Other Deductions) × Attendance Factor**

**Attendance Factor:**
> Attendance Factor = Working Days Present / Total Payroll Days

**Salary Structure Master:**
Salary structures define the components that make up an employee's CTC. Multiple structures can be configured (e.g., "Staff Structure", "Worker Structure", "Contract Structure"). Each structure defines:

- **Earnings Components:** Basic Salary (as % of CTC or fixed), HRA (as % of Basic), Conveyance Allowance, Medical Allowance, Special Allowance (balancing component), Variable Pay
- **Deduction Components:** PF Employee Contribution (12% of Basic, subject to ceiling), ESI Employee Contribution (0.75% of gross for eligible employees), Professional Tax (slab-based, state-specific), TDS (computed from IT declaration), Loan EMI (auto-deducted if active loan), Advance Recovery

**6-Step Payroll Run Wizard:**

| Step | Action |
|---|---|
| Step 1: Select Period | Choose the payroll month; the system shows the payroll cut-off date |
| Step 2: Data Verification | Review attendance data; flag exceptions (missing punches, unapproved leaves) |
| Step 3: Preview Compute | System computes gross, deductions, and net pay for all employees; view summary and individual payslips |
| Step 4: Adjustments | Enter one-time additions or deductions (bonus, LOP correction, advance recovery override) |
| Step 5: Final Compute & Lock | Re-compute with adjustments; lock the payroll run (no further changes after this step) |
| Step 6: Disburse | Generate bank advice file (NEFT/RTGS format); mark payroll as disbursed; send payslip PDFs to employees |

**Payslip:** Auto-generated PDF with company logo, all earnings and deduction components, YTD totals, leave balance, and bank details. Delivered to the employee's ESS portal and optionally via email.

### 1.9 Statutory Compliance

**Provident Fund (PF):**
- Employer contribution: 12% of Basic + DA
- Employee contribution: 12% of Basic + DA
- Differential between 12% employer and 3.67% EPF allocation goes to EPS
- Monthly ECR (Electronic Challan cum Return) generated in prescribed format
- Contribution ceiling: configurable (currently ₹15,000 Basic for mandatory applicability)

**Employee State Insurance (ESI):**
- Applicable if company has 10+ employees and employee's monthly gross ≤ ₹21,000
- Employee contribution: 0.75% of gross wages
- Employer contribution: 3.25% of gross wages
- Monthly challan generated; semi-annual returns supported

**Professional Tax (PT):**
- State-specific slab-based deduction
- Monthly or quarterly remittance depending on state rules
- States supported: Karnataka, Maharashtra, West Bengal, Andhra Pradesh, Telangana, Gujarat, Tamil Nadu, and others

**Labour Welfare Fund (LWF):**
- Applicable in states with LWF legislation
- Deducted bi-annually (June and December) at statutory rates

**Gratuity:**
- Accrual tracking for employees with 5+ years of service
- Formula: (15/26 × Last Basic + DA × Years of Service)
- Gratuity liability report generated for actuarial and accounting purposes

**Bonus:**
- Statutory bonus under the Payment of Bonus Act (8.33%–20% of basic/minimum wage, configurable)
- Annual computation in the month configured by the company

### 1.10 TDS & Income Tax

**IT Declaration:**
At the beginning of the financial year, employees submit an IT declaration declaring their planned investments under Sections 80C, 80D, 80E, HRA exemption, LTA, etc. The payroll engine uses this declaration to project the annual tax liability and distribute monthly TDS deductions.

**Tax Computation:**
- Supports both Old Tax Regime (with deductions) and New Tax Regime (flat slabs, no deductions)
- Employee selects preferred regime; system computes both and suggests optimal
- Quarterly TDS amounts recalculated as actuals deviate from declarations

**Documents Generated:**
- **Form 16 (Part A):** TDS certificate showing deductions and deposits (auto-generated at year-end)
- **Form 16 (Part B):** Computation of total income and tax liability
- **Form 24Q:** Quarterly TDS return in prescribed format for filing with tax authorities

### 1.11 Employee Self-Service (ESS)

The ESS Portal gives every employee direct access to their own HR data without HR team intervention.

**ESS Capabilities:**

| Feature | Employee Can |
|---|---|
| Profile | View their own profile; request updates (HR approval required) |
| Payslips | Download payslip PDFs for any past month |
| Attendance | View attendance register; submit regularisation requests |
| Leave | Apply for leave; view balance; track approval status |
| IT Declarations | Submit and update income tax declarations |
| Loan/Advance | Apply for a salary advance; view loan account and repayment schedule |
| Expense Claims | Submit reimbursement claims with receipts |
| HR Letters | Download experience certificates, salary certificates, offer letters on demand |
| Appraisals | Complete self-evaluation forms; view rating history |
| Training | Enroll in available training programmes |
| Grievances | Raise a grievance or query |

**Manager Self-Service (MSS):**
Managers access an extended view that includes team attendance, leave balances, pending approvals, and team performance summaries — scoped to their direct and indirect reports.

### 1.12 Performance Management

**Performance Cycle:**
Performance reviews are configured as cycles (e.g., Annual, Semi-Annual, Quarterly). Each cycle has defined phases: Goal Setting → Mid-Review → Final Appraisal → Calibration → Outcome.

**KRA / OKR Framework:**
- Employees and managers collaboratively set Key Result Areas (KRAs) or OKRs at the start of each cycle
- KRAs are weighted; total weightage must sum to 100%
- Ratings can be numeric (1–5), descriptive (Exceeds / Meets / Below), or custom
- Mid-cycle check-ins allow progress tracking without a formal review

**360° Feedback:**
Configurable multi-rater feedback where an employee receives input from their manager, peers, direct reports, and optionally internal customers. Responses are anonymised for peer and skip-level feedback.

**Succession Planning:**
High-potential employees can be tagged. Succession plans link potential successors to critical roles, with readiness timelines.

**Industry Presets:**
Pre-configured KRA templates for common manufacturing roles (Production Supervisor, Maintenance Technician, Quality Inspector, HR Executive) to accelerate the initial performance setup.

### 1.13 Training & Learning Management

The Training module manages the full training lifecycle from needs identification to completion tracking.

**Training Programme Master:**
Each training programme carries: Name, Type (Classroom / On-the-Job / e-Learning / External), Duration, Trainer (internal employee or external vendor), Cost, Certification issued, Skills addressed.

**Training Calendar:**
Scheduled training sessions with batch sizes, venue, and enrollment management.

**Training Needs Identification (TNI):**
Managers can flag skill gaps for their team members. HR consolidates gaps into a training calendar.

**Completion Tracking:**
- Attendance recorded per session
- Assessment scores captured (if applicable)
- Certification issued and stored in employee record
- Training effectiveness feedback collected post-training

**Skill Matrix:**
A matrix of employees vs required skills with proficiency levels (Beginner / Intermediate / Expert). Gaps highlighted automatically.

### 1.14 Loans, Advances & Reimbursements

**Salary Advance:** Employees can apply for a lump-sum advance against future salary. Approved advances are auto-deducted in equal EMIs from subsequent payrolls.

**Salary Loan:** Similar to advance but for larger amounts with a formal repayment schedule agreed upfront.

**Reimbursements:** Employees submit expense claims with receipts (uploaded as images). Claims go through manager and finance approval. Approved amounts are added to the next payroll as a non-taxable reimbursement component.

### 1.15 Travel & Expense Management

**Travel Request:** Employee raises a travel request specifying destination, dates, purpose, estimated costs, and advance required. Approved travel requests unlock an advance disbursement.

**Expense Claim:** Post-travel, employee submits actual expenses against each category (flights, hotels, per diem, local transport) with receipt uploads. Actuals are compared against policy limits. Overspend requires justification and additional approval.

**Expense Policy:** Configurable per-city/grade limits for hotels, meals, and transport. System flags policy violations automatically.

### 1.16 HR Letters & Certificates

Auto-generated from templates with employee data populated dynamically. All letters carry the company logo and authorised signatory details.

| Document | Trigger |
|---|---|
| Offer Letter | Generated at offer acceptance in ATS |
| Appointment Letter | Generated on joining date |
| Confirmation Letter | Generated on probation completion |
| Salary Increment Letter | Generated on appraisal completion |
| Promotion Letter | Generated on promotion event |
| Experience / Relieving Letter | Generated on exit completion |
| Salary Certificate | On-demand from ESS |
| Bonafide Certificate | On-demand from ESS |
| No Objection Certificate (NOC) | On-demand with manager approval |
| Show Cause Notice (SCN) | Generated in discipline management |

### 1.17 Grievance & Discipline Management

**Grievance Management:**
Employees raise grievances through the ESS portal. Each grievance is categorised, assigned to an HR executive, and tracked through resolution. SLA timers are configurable per category.

**Discipline Management:**
- **Show Cause Notice (SCN)** — Issued for a specific misconduct; employee provides written response within a deadline
- **Warning Letter** — Formal warning recorded in the employee's file
- **Performance Improvement Plan (PIP)** — Time-bound structured plan with measurable milestones; outcome determines retention or termination

### 1.18 Employee Offboarding & Full & Final Settlement

**Offboarding Workflow:**

1. **Resignation / Termination event** recorded by HR; separation type and effective date captured
2. **Notice period tracking** — System calculates notice period balance (served vs required); shortfall or excess affects F&F
3. **Clearance checklist** — Departments confirm asset return, IT equipment, locker, etc.
4. **Exit interview** — Conducted and outcome recorded
5. **F&F Computation** — Final salary, leave encashment, gratuity (if eligible), bonus recovery or payment, notice period adjustment
6. **F&F Release** — HR and Finance approve; final payment processed via payroll
7. **System access revoked** — On last working day, user account is deactivated
8. **Relieving letter generated** — Auto-generated and available for download

**F&F by Separation Type:**

| Separation Type | Key F&F Considerations |
|---|---|
| Voluntary Resignation | Notice period shortfall deduction if applicable; leave encashment; gratuity if 5+ years |
| Retirement | Full gratuity; leave encashment; superannuation benefits |
| Termination (with cause) | No gratuity; no notice period payment; pending dues settled |
| Termination (without cause) | Notice pay in lieu; gratuity if 5+ years; all outstanding dues |
| Absconding | Legal recovery process; no F&F until contact re-established |

---

## 2. Module 3 — Security

### 2.1 Module Overview

The Security module is the **gate-level operational layer** of Avy ERP. It is used by security personnel stationed at facility entrances and serves three primary functions: recording employee attendance (which feeds into the HR module), verifying incoming goods against Advance Shipping Notices (which feeds Inventory), and managing visitor entry (which connects to the Visitor Management module).

The Security module is a **source module** — it generates records that other modules consume. This is why it is a mandatory dependency for both HR Management and Visitor Management.

### 2.2 Employee Gate Attendance

**Attendance Capture Methods at Gate:**

| Method | Description |
|---|---|
| Manual Code Entry | Security guard enters employee's ID or badge number manually |
| Face Scan (Biometric) | Facial recognition device at gate; auto-punches on recognition |
| QR Code Scan | Employee shows QR code from mobile app; guard scans it |

**Attendance Recording Logic:**
- First scan of the day → recorded as Punch-In
- Subsequent scan → recorded as Punch-Out (or Punch-In if Punch-Out already recorded, for multi-punch scenarios)
- Multi-punch sequences stored; first and last punches used for working hours calculation
- Gate-level time stamp (not device time) used as the authoritative timestamp

**Real-Time Gate Count:**
The Security module dashboard shows a live count of employees currently inside the facility per shift. This is derived from punch-in/punch-out pairs without a corresponding exit being counted as "inside."

**Late Arrival & Early Departure Flags:**
The system automatically flags:
- Employees who punch in after the shift start time (plus configurable grace period)
- Employees who punch out before the shift end time (minus configurable grace period)

These flags are visible in the HR module's attendance dashboard for HR review.

### 2.3 Goods Verification

When a vendor's goods delivery arrives at the gate, the security personnel must verify the delivery before allowing it in. Two verification methods are supported:

**Method 1 — ASN-Based Verification:**
The vendor has previously created an Advance Shipping Notice (ASN) against a Purchase Order. The security guard looks up the ASN (by ASN number or vendor name), confirms the physical goods match the ASN details (item, quantity, vehicle number), and marks the ASN as "Gate Verified." This verification triggers Inventory to create a Goods Receipt Note (GRN) for stores staff to complete.

**Method 2 — Manual Invoice Verification:**
For deliveries without a pre-existing ASN, the security guard manually records the supplier name, invoice number, items, and quantity from the physical delivery documents. This creates a record for stores staff to follow up on.

**Outward Goods Verification:**
When goods are dispatched from the facility (finished goods delivery, material return to vendor), the guard verifies the dispatch against a delivery note or sales invoice and records the outward gate pass.

### 2.4 Gate Management Operations

**Shift Dashboard:**
Security personnel see a shift-specific dashboard showing:
- Total employees punched in during current shift
- Vehicles currently inside (if vehicle tracking is enabled)
- Expected visitors for the day
- Active ASNs awaiting delivery

**Visitor Integration:**
The Security module receives the list of pre-registered expected visitors for the day from the Visitor Management module. When a visitor arrives, the gate personnel sees their pre-registration status and can complete check-in without re-entering details.

**Emergency Mode:**
A one-tap "Emergency Lockdown" button blocks all new entries and triggers an alert. The current on-site headcount (employees + visitors) is instantly available for muster purposes.

---

## 3. Module 9 — Visitor Management

### 3.1 Module Overview

The Visitor Management module is a comprehensive, digitally-native system designed to replace paper visitor logbooks with an intelligent, secure, and auditable platform. It manages the complete lifecycle of every external person who enters a company's premises — from when a visit is planned to when the visitor exits.

Built specifically for manufacturing enterprises and industrial facilities, this module goes beyond simple check-in/check-out. It enforces safety inductions, captures PPE acknowledgements, manages contractor compliance, integrates with gate security operations, and maintains a real-time headcount for emergency evacuations.

**Module Vision:** Every person who enters the facility is identified, informed, and accounted for — from the moment they are invited to the moment they leave. No exceptions. No paper. No guesswork.

### 3.2 Visitor Lifecycle

```
Pre-Registration (by host) ──► Invitation sent ──► QR Code generated
        │                                                │
   Walk-In Arrival ◄──────────────────────────────────── │
        │                                                │
        ▼                                                ▼
   Arrival at Gate ──────────────────────────────► Scan QR at Gate
        │
        ▼
   Identity Verification (ID check)
        │
        ▼
   Safety Induction (if shop floor / production area)
        │
        ▼
   Host Notification & Approval
        │
        ▼
   Badge Printed / Digital Badge issued
        │
        ▼
   On-Site → Visitor tracked as "Checked In"
        │
        ▼
   Check-Out at Gate
        │
        ▼
   Audit Record Finalised
```

### 3.3 Visitor Types & Classification

| Visitor Type | Description | Special Handling |
|---|---|---|
| Business Visitor | Client, partner, investor, auditor | Standard flow |
| Contractor | Third-party worker on-site for work | Contractor compliance documents required |
| Vendor Representative | Supplier's delivery or sales rep | Linked to Vendor Management module |
| Delivery Personnel | Package or courier delivery | Goods gate pass workflow |
| Government Inspector | Regulatory / statutory inspector | Senior host auto-notified; expedited entry |
| Job Applicant | Candidate attending interview | Linked to ATS if configured |
| Personal / Family | Employee's personal visitor | Host directly responsible |
| Group / Event | Multiple visitors arriving together | Group visit workflow |

### 3.4 Pre-Registration & Invitation

A host employee (any Avy ERP user with VMS access) pre-registers an expected visitor:

**Pre-Registration Fields:**
- Visitor Name, Company / Organisation, Designation
- Contact Phone and Email
- Purpose of Visit (dropdown + free text)
- Expected Arrival Date and Time
- Expected Departure Time
- Host Employee (the registering employee is the default host)
- Meeting Location within the facility
- Access Areas required (selected from a configured list of zones)
- Vehicle Number (optional)
- Number of Visitors (for group visits)
- Attachments (NDA, meeting agenda, etc.)

**On Pre-Registration:**
1. The system generates a unique visit ID and QR code
2. An email invitation is sent to the visitor with the QR code, date, time, directions, and parking instructions
3. The visit appears on the Security module's "Expected Today" list at the gate
4. The host receives a calendar reminder for the meeting

### 3.5 Walk-In Visitor Flow

When a visitor arrives without prior registration, the security guard initiates a walk-in entry:

1. Security guard collects visitor's name, phone, company, and purpose
2. System searches for any previous visit records (returning visitor recognition)
3. Host employee searched and selected from the directory
4. Host notified instantly via push notification and SMS
5. Host approves or declines the visit (configurable approval requirement for walk-ins)
6. On approval, visitor proceeds to check-in

### 3.6 QR Self-Registration

A QR code is displayed at the facility entrance (printed poster or digital display). Visitors who are not pre-registered can self-register by scanning this QR code:

1. Visitor scans the entrance QR code with their phone camera
2. Opens a mobile-optimised web form (no app download required)
3. Visitor fills in: Name, Company, Purpose, Host employee name, Phone
4. Host is notified; approves or declines
5. On approval, a digital badge is issued and the visitor is allowed entry
6. The entire flow takes under 3 minutes for a walk-in

### 3.7 Check-In Process

**For Pre-Registered Visitors:**
1. Security guard scans visitor's pre-registration QR code or looks them up
2. System shows full pre-registration details for confirmation
3. Security guard verifies visitor's identity (ID document type and number captured)
4. Safety induction completed (if required for the access area)
5. Visitor is checked in; timestamp recorded
6. Host notified of visitor's arrival

**For Walk-In Visitors:**
The walk-in flow above completes with the same ID capture and induction steps.

**Check-In captures:**
- Actual arrival timestamp
- Identity document type and number
- Photo of visitor (optional; captured via mobile camera)
- Safety acknowledgement signature or digital confirmation

### 3.8 Safety Induction at Check-In

For visitors accessing production areas, warehouses, or any designated safety-critical zones, a safety induction is mandatory before entry can be completed.

**Safety Induction Types:**
- **Video Induction** — Visitor watches a short safety briefing video (played on kiosk or sent to phone)
- **Document Acknowledgement** — Visitor reads and digitally signs a safety rules document
- **Verbal Confirmation** — Security guard confirms verbal briefing was given; records acknowledgement

**Induction Content:**
- Emergency evacuation procedures and muster points
- PPE requirements for the area being visited
- Prohibited items and behaviours on-site
- Fire exits and assembly points

**PPE Distribution Record:**
If PPE (hard hats, safety vests, safety shoes) is issued to the visitor at the gate, the type and number of items is recorded. Items must be returned at check-out.

**Compliance Lock:**
A visit cannot be marked as fully checked in until all mandatory safety steps for the requested access areas are completed.

### 3.9 Visitor Badge & Identification

**Badge Contents:**
- Visitor Name and Photo (if captured)
- Visitor Company
- Purpose of Visit
- Host Employee Name
- Date of Visit
- Valid Until (check-out expected time or date)
- Unique Visit ID / QR Code
- Permitted Access Areas
- Emergency contact number

**Badge Options:**
- Printed physical badge (requires label printer at gate)
- Digital badge displayed on visitor's phone screen
- Colour-coded by visitor type (Business / Contractor / Government)

### 3.10 Host Notification & Approval

**Notification triggers and methods:**

| Trigger | Notification Method |
|---|---|
| Pre-registration submitted (confirmation) | In-app |
| Visitor arrived at gate (pre-registered) | Push notification + SMS |
| Walk-in visitor requesting approval | Push notification + SMS with Accept/Decline |
| QR self-registration submitted | Push notification + SMS |
| Visitor checked out | In-app |
| Overstay alert (visitor not checked out by expected time) | Push notification + SMS to host |

**Approval expiry:** If a host does not respond to a walk-in approval request within a configurable time window (default: 5 minutes), the security guard is given options to escalate to a deputy host or deny entry.

### 3.11 On-Site Tracking & Check-Out

**On-Site Status:**
A live dashboard shows all visitors currently on-site: name, company, host, check-in time, permitted areas, and current status.

**Area Access Tracking:**
If the facility has multiple access zones with configured checkpoints, visitor movements between zones can be logged (entry to production floor, exit from production floor, etc.).

**Check-Out Process:**
1. Visitor presents badge at the gate
2. Security guard scans badge QR code or looks up the visitor
3. System shows check-in details and duration
4. Security confirms PPE return (if applicable)
5. Visitor is checked out; departure time recorded
6. Host notified of departure
7. Visit record is finalised in the audit trail

**Forced Check-Out:**
If a visitor does not check out before end of day, the system allows the security supervisor to force a check-out with a note. This prevents the visitor from appearing as permanently on-site.

### 3.12 Today's Visitors Dashboard

A real-time dashboard showing all visitor activity for the current day:

| Status Badge | Meaning |
|---|---|
| Expected | Pre-registered; not yet arrived |
| Checked In | Currently on-site |
| Checked Out | Visit completed |
| Walk-In | Arrived without prior registration |
| Denied | Entry was rejected |
| Overstay | Expected departure time has passed; still on-site |

**Filters:** By status, visitor type, host employee, access area, gate.

**Metrics Bar:** Total Expected today / Total Checked In / Currently On-Site / Checked Out.

### 3.13 Watchlist & Blocklist

**Watchlist:** Visitors flagged for additional scrutiny or secondary screening. An alert is shown to security at check-in, but entry is not automatically blocked.

**Blocklist:** Visitors who are not permitted entry under any circumstances. Check-in is automatically blocked and the security supervisor is notified. The blocklist is managed by authorised HR or Security managers.

**Criteria for listing:**
- Prior security incidents on-site
- Court orders or legal restrictions
- Company policy violations during previous visits
- Vendor / contractor compliance failures

### 3.14 Emergency Evacuation & Muster Management

**Emergency Muster List:**
With a single tap, any authorised user can generate a real-time muster list containing:
- All visitors currently checked in (on-site)
- All employees with active punch-ins (from Security module)
- Each person's last known location (if area tracking is enabled)
- Contact details for visitors and emergency contacts for employees

**Use in Emergency:**
The muster list is available offline (last cached state) even when connectivity fails. Security personnel use it to account for every individual during evacuation.

**Headcount Reconciliation:**
Post-evacuation, security can mark each person as "Accounted For" or "Unaccounted" from the muster list to quickly identify anyone not at the muster point.

### 3.15 Contractor & Vendor Visit Management

Contractors (third-party workers on-site for an extended period) are handled differently from one-time visitors:

**Contractor Registration:**
- Linked to the Vendor Management module (contractor = a vendor's employee)
- Documents required before entry: ID, safety training certificate, work permit, insurance
- Document expiry dates tracked; entry blocked if documents are expired
- Contractor-specific induction (more detailed than standard visitor induction)

**Work Permit:**
For contractors performing high-risk work (height work, electrical, confined space), a work permit must be generated and approved by the facility safety officer before work commences. The gate system checks for an active work permit before allowing a contractor into the relevant work area.

### 3.16 Group Visit & Event Management

When multiple visitors arrive together (e.g., a client delegation, school tour, supplier inspection team):

- A group visit is registered with a group name and expected count
- Individual visitor names can be pre-filled or captured on arrival
- A single group host is responsible for the entire group
- Group safety induction is conducted once for all members
- Group badge (common visit ID) printed for each member
- Single check-out action can check out the entire group

### 3.17 Recurring Visitor & Frequent Visitor Pass

**Recurring Visitor:**
For visitors who come regularly (e.g., a vendor representative who visits every week), a recurring visit profile is created. The profile stores their details, approved access areas, and standard purpose. New visits for recurring visitors are created with one click — no re-entry of details.

**Frequent Visitor Pass:**
An extended-validity pass issued to approved recurring visitors. The pass is valid for a configured period (e.g., 30 or 90 days). Gate check-in is expedited — the guard scans the pass and the visitor is checked in without the full registration flow. Document expiry is still checked on each visit.

### 3.18 Vehicle & Material Gate Pass

**Vehicle Gate Pass:**
For vehicles entering or exiting the facility:
- Vehicle number, type, driver name, company
- Purpose (delivery, pickup, employee vehicle)
- Entry time / exit time
- Linked to a GRN or delivery note where applicable

**Material Gate Pass (Outward):**
When material is dispatched from the facility:
- Items, quantities, destination
- Linked to a Sales Invoice or Vendor Return
- Authorization required above a configurable value threshold

**Material Gate Pass (Inward — Returnable):**
For items entering the facility temporarily (equipment for repair, demo units, samples):
- Expected return date captured
- Overdue return alert generated automatically

### 3.19 Multi-Gate & Multi-Plant Support

For facilities with multiple entry points or multiple plants:

- Each gate is independently configured with its own name, access areas controlled, and assigned security personnel
- Visitor registration specifies which gate they will arrive at
- Each gate has its own real-time dashboard; the Today's Visitors dashboard can be filtered by gate
- Plant-level configuration: visitor policies, safety induction content, and access areas can vary by plant
- Central reporting aggregates data across all gates and plants

---

*This is Part 3 of 5 of the Avy ERP Master PRD.*
*Part 4 covers: Sales & Invoicing, Inventory, Vendor Management, and Finance modules.*
*Part 5 covers: Production, Machine Maintenance, Calibration, Quality Management, EHSS, CRM, and Project Management modules.*

---

**Document Control**

| Field | Value |
|---|---|
| Product | Avy ERP |
| Company | Avyren Technologies |
| Part | 3 of 5 — HR Management, Security & Visitor Management |
| Version | 2.0 |
| Date | April 2026 |
| Status | Final Draft |
| Classification | Confidential — Internal Use Only |
