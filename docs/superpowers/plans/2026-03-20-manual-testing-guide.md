# Avy ERP — Company Admin & HRMS Manual Testing Guide

> **Date:** March 20, 2026
> **Scope:** Phase 1–9 (Company Admin Core + Full HRMS Module)
> **Platforms:** Backend API, Mobile App (React Native/Expo), Web App (React/Vite)

---

## Pre-Requisites

### 1. Database Setup
```bash
cd avy-erp-backend
npx prisma migrate dev --name "add-company-admin-hrms-models"
npx prisma generate
npm run dev
```
This creates all ~76 new tables + ~50 enums from Phases 1–9.

### 2. Test User Setup
You need at minimum:
- **Super Admin** account (to create a company + company-admin user via tenant onboarding wizard)
- **Company Admin** account (created during onboarding OR via `POST /api/v1/platform/tenants/onboard` with users array)

### 3. Start All Services
```bash
# Backend
cd avy-erp-backend && npm run dev    # http://localhost:3000

# Web App
cd web-system-app && npm run dev     # http://localhost:5173

# Mobile App
cd mobile-app && npx expo start      # Expo dev server
```

---

## How to Navigate

### Mobile App
- **Hamburger button** (top-left on every screen) → opens **Sidebar**
- Sidebar has **17 sections** for company-admin role (see section list below)
- Tap any sidebar item → navigates to that screen
- **Back button** (top-left) on every sub-screen → returns to previous screen

### Web App
- **Left sidebar** (always visible, collapsible) → has **17 sections** for company-admin role
- Click any sidebar item → loads that screen in the main content area
- **Cmd+K / Ctrl+K** → Command Palette search for any page

---

## PHASE 1: Company Admin Core Infrastructure

### Test 1.1: Login & Navigation
| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | Login as Company Admin | Dashboard loads with company-admin KPIs |
| 2 | Check sidebar (mobile: hamburger → sidebar; web: left sidebar) | Should show 17 sections: Dashboard, Company, HR & People, Attendance, Leave Management, Payroll & Compliance, Payroll Operations, ESS & Workflows, Self-Service, Performance, Recruitment & Training, Exit & Separation, Advanced HR, Configuration, People & Access, Reports, Support |
| 3 | Check tabs are hidden | Mobile: only Dashboard + More tabs visible. Companies + Billing tabs hidden |
| 4 | Try accessing `/companies` or `/billing` URL directly | Should redirect or show No Permission screen |

### Test 1.2: Company Admin Dashboard
**Navigate:** Sidebar → Dashboard
| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | View KPI cards | 4 cards: Total Users, Locations, Active Modules, Company Status |
| 2 | Quick Actions | 4 buttons linking to: Users, Shifts, Contacts, Audit Logs |
| 3 | Company Overview card | Shows company name, status badge, modules count, user tier |
| 4 | Recent Activity | Shows last 5 audit log entries with timestamps |
| 5 | Pull to refresh (mobile) / auto-refresh | Data refreshes |

### Test 1.3: Company Profile
**Navigate:** Sidebar → Company → Company Profile
| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | View read-only sections | Company Code, Business Type, Industry, CIN, Statutory IDs (PAN, TAN, GSTIN etc.) — all display with lock icon, NOT editable |
| 2 | View editable sections | Display Name, Legal Name, Short Name, Email Domain, Website — show pencil icon |
| 3 | Edit Display Name | Tap pencil → bottom sheet (mobile) / modal (web) → change name → Save → success toast → name updated |
| 4 | Edit Address | Edit registered/corporate address → Save → verify updated |
| 5 | View Modules & Billing | Selected modules as chips, User Tier, Billing Cycle — read-only |

### Test 1.4: Location Management (CRITICAL — NO CREATE)
**Navigate:** Sidebar → Company → Locations
| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | View location list | All company locations displayed with name, code, facility type, status, HQ badge |
| 2 | **Verify NO "Add" button exists** | No FAB, no "Add Location" button anywhere on the screen |
| 3 | Edit a location | Tap edit → modify address, contact, GST → Save → updated |
| 4 | Try deleting HQ location | Should show warning: "Cannot delete headquarters location" |
| 5 | Delete a non-HQ location | ConfirmModal → confirm → deleted |
| 6 | **API test**: `POST /api/v1/company/locations` | Should return **403 Forbidden** with message "Only Super Admin can add new locations" |

### Test 1.5: Shift Management
**Navigate:** Sidebar → Company → Shifts & Time
| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | View shifts | List of company shifts with name, from/to time, downtime slots |
| 2 | Add shift | FAB → form: name, from time, to time, no-shuffle toggle, add downtime slots → Save |
| 3 | Edit shift | Tap edit → modify → Save |
| 4 | Delete shift | ConfirmModal → delete |

### Test 1.6: Key Contacts
**Navigate:** Sidebar → Company → Key Contacts
| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | View contacts | Cards with name, designation, type badge, email, phone |
| 2 | Add contact | FAB → form with name, designation, department, type (Primary/HR/Finance/IT/Legal/Operations), email, phone → Save |
| 3 | Edit/Delete | Standard CRUD operations |

### Test 1.7: Number Series
**Navigate:** Sidebar → Configuration → Number Series
| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | View series | Code, description, linked screen, live preview (e.g., `EMP-00001`) |
| 2 | Add series | Code, Description, Linked Screen dropdown, Prefix, Suffix, Number Count, Starting Number → live preview updates → Save |
| 3 | Verify preview | Changing prefix/suffix/count updates preview in real-time |

### Test 1.8: IOT Reasons
**Navigate:** Sidebar → Configuration → IOT Reasons
| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | Add reason | Type: Machine Idle → Planned checkbox appears → Duration field appears when Planned=true |
| 2 | Type: Machine Alarm | Planned checkbox should NOT appear |

### Test 1.9: System Controls
**Navigate:** Sidebar → Configuration → System Controls
| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | View sections | Production Controls, Payroll Controls, Security Controls, Leave Controls, Notification Controls |
| 2 | Toggle controls | Toggle switches → Save → verify persisted on reload |

### Test 1.10: Company Settings
**Navigate:** Sidebar → Configuration → Settings
| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | Locale section | Change Currency, Language, Date Format, Number Format, Time Format |
| 2 | Compliance toggles | India Statutory, Multi-Currency, International Tax |
| 3 | Portal toggles | ESS, Mobile App, AI Chatbot, e-Sign |
| 4 | Integration toggles | Biometric, Payroll Bank, Email, WhatsApp |
| 5 | Save | Only enabled when form is dirty → Save → success toast |

### Test 1.11: User Management
**Navigate:** Sidebar → People & Access → User Management
| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | View users | List with name, email, role, status (Active/Inactive), last login |
| 2 | Search/filter | Search by name/email, filter by Active/Inactive |
| 3 | Add user | FAB → Full Name, Email, Phone, Role dropdown (from tenant roles), Password → Save |
| 4 | Edit user | Modify name, phone, role |
| 5 | Deactivate | Toggle status with ConfirmModal |

### Test 1.12: Role Management
**Navigate:** Sidebar → People & Access → Roles & Permissions
| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | View roles | System roles (lock icon, non-editable) + custom roles |
| 2 | Create role | Name, Description, "Start from Template" loads reference roles, Permission matrix with modules × actions |
| 3 | Delete custom role | ConfirmModal. Blocked if users assigned |
| 4 | Cannot edit system roles | System roles should be grayed out / non-editable |

### Test 1.13: Feature Toggles
**Navigate:** Sidebar → People & Access → Feature Toggles
| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | Select user | Shows available feature toggles |
| 2 | Toggle feature | On/off switch → calls API → persists |
| 3 | Source indicator | Shows "Role" (inherited) vs "Override" (explicit) |

### Test 1.14: Audit Logs
**Navigate:** Sidebar → Reports → Audit Logs
| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | View logs | Company-scoped audit entries (NOT all companies) |
| 2 | Filter | By action type, date range, search |
| 3 | Verify scope | Only shows logs for THIS company, not others |

---

## PHASE 2: Org Structure & Employee Master

### Test 2.1: Department Master
**Navigate:** Sidebar → HR & People → Departments
| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | Add department | Name, Code, Parent Department (dropdown for hierarchy), Cost Centre Code, Status → Save |
| 2 | Verify unique code | Try duplicate code → error message |
| 3 | Delete with employees | Should block: "Cannot delete: X employees assigned" |
| 4 | Parent hierarchy | Create child department → verify parent shows in card |

### Test 2.2: Designation Master
**Navigate:** Sidebar → HR & People → Designations
| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | Add designation | Name, Code, Department (dropdown), Grade (dropdown), Job Level (L1-L7), Managerial toggle, Probation Days |
| 2 | Verify dropdowns | Department and Grade dropdowns populated from existing masters |

### Test 2.3: Grade / Band Master
**Navigate:** Sidebar → HR & People → Grades & Bands
| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | Add grade | Code, Name, CTC Min/Max (₹ formatted), HRA %, PF Tier, Probation Months, Notice Days |
| 2 | Verify currency formatting | CTC fields show ₹ with Indian number format |

### Test 2.4: Employee Type Master
**Navigate:** Sidebar → HR & People → Employee Types
| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | Add type | Name, Code, 5 statutory toggles (PF, ESI, PT, Gratuity, Bonus) |
| 2 | Verify flags display | Statutory chips show ✓ (green) or ✗ (red) per flag |

### Test 2.5: Cost Centre Master
**Navigate:** Sidebar → HR & People → Cost Centres
| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | Add cost centre | Code, Name, Department (dropdown), Location (dropdown), Annual Budget, GL Account Code |

### Test 2.6: Employee Directory
**Navigate:** Sidebar → HR & People → Employee Directory
| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | View directory | List with photo/initials, Employee ID, Name, Department, Designation, Location, Status badge |
| 2 | Search | By name, employee ID, email |
| 3 | Filter by status | All, Active, Probation, Confirmed, On Notice, Exited |
| 4 | Filter by department | Dropdown populated from department master |
| 5 | Tap employee | Navigates to employee detail/profile screen |
| 6 | Add employee (FAB) | Opens 6-tab form in create mode |

### Test 2.7: Employee Profile — 6-Tab Form
**Navigate:** Employee Directory → tap employee OR FAB "Add Employee"

**Tab 1 — Personal:**
| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | Fill required fields | First Name, Last Name, DOB, Gender, Personal Mobile, Personal Email, Emergency Contact (name, relation, mobile) |
| 2 | Address | Current Address fields. "Same as current" toggle for Permanent Address |
| 3 | Optional fields | Middle Name, Marital Status, Blood Group, Nationality, Religion, Category |

**Tab 2 — Professional:**
| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | Required fields | Joining Date, Employee Type (dropdown), Department, Designation |
| 2 | Optional fields | Grade, Reporting Manager (search), Work Type (On-site/Remote/Hybrid), Shift, Location, Cost Centre |
| 3 | Probation End Date | Auto-calculated from Joining Date + Grade probation months |

**Tab 3 — Salary:**
| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | Annual CTC | Enter CTC → monthly gross auto-computed |
| 2 | Payment Mode | NEFT/IMPS/Cheque selector |

**Tab 4 — Bank:**
| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | IFSC Code | Enter IFSC → bank name/branch auto-fill |
| 2 | Account Number + Confirm | Must match |
| 3 | Account Type | Savings/Current |

**Tab 5 — Documents:**
| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | Statutory IDs | PAN, Aadhaar (masked display), UAN, ESI IP Number |
| 2 | Document list | Uploaded documents with type, name, date |
| 3 | Upload button | File picker placeholder |

**Tab 6 — Timeline:**
| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | View events | JOINED event auto-created when employee created |
| 2 | Event display | Color-coded dots, icon, title, description, timestamp |

**Save:**
| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | Save new employee | Employee ID auto-generated from No Series (e.g., EMP-00001) |
| 2 | Timeline entry | JOINED event appears in timeline |
| 3 | Status | Defaults to PROBATION |
| 4 | Status change | Confirm Employee → status changes to CONFIRMED, timeline event added |

---

## PHASE 3: Attendance & Leave Management

### Test 3.1: Holiday Calendar
**Navigate:** Sidebar → Attendance → Holiday Calendar
| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | Year selector | Switch between years (2025/2026/2027) |
| 2 | Add holiday | Name, Date, Type (National/Regional/Company/Optional/Restricted), Branch scope, Description |
| 3 | Type badges | Color-coded: National=blue, Regional=indigo, Company=green, Optional=amber |
| 4 | Clone Year | Button → select fromYear/toYear → clones all holidays with adjusted dates |

### Test 3.2: Rosters
**Navigate:** Sidebar → Attendance → Rosters
| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | Add roster | Name, Pattern (Mon-Fri/Mon-Sat/Mon-Sat Alt/Custom), Week-Off days, Applicable Employee Types, Effective From |
| 2 | Default roster | Toggle → only one roster can be default |

### Test 3.3: Attendance Rules
**Navigate:** Sidebar → Attendance → Attendance Rules
| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | Configure | Grace Period, Half-Day/Full-Day thresholds, Late arrivals allowed, LOP toggle, Missing punch alert, Selfie/GPS toggles |
| 2 | Save | Persists on reload |

### Test 3.4: Attendance Dashboard
**Navigate:** Sidebar → Attendance → Attendance Dashboard
| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | KPI cards | Present, Absent, Late, On Leave counts |
| 2 | Date picker | Navigate between dates |
| 3 | Department filter | Filter by department |
| 4 | Records list | Employee punch in/out, worked hours, status badge |

### Test 3.5: Attendance Overrides
**Navigate:** Sidebar → Attendance → Attendance Rules (mobile has separate override screen)
| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | Create override | Employee, Issue Type (Missing Punch In/Out, Absent Override, etc.), Corrected times, Reason |
| 2 | Approve/Reject | Pending tab → Approve or Reject buttons |
| 3 | Approved override | Updates the parent attendance record |

### Test 3.6: Overtime Rules
**Navigate:** Sidebar → Attendance → Overtime Rules
| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | Configure | Eligible types, Rate multiplier (1.5x/2x), Threshold, Caps, Auto-include payroll toggle, Approval required toggle |

### Test 3.7: Leave Type Master
**Navigate:** Sidebar → Leave Management → Leave Types
| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | Add leave type | Full form with: Name, Code, Category (Paid/Unpaid/Compensatory/Statutory), Annual Entitlement |
| 2 | Accrual settings | Frequency, Accrual Day |
| 3 | Carry Forward | Toggle + Max Days |
| 4 | Encashment | Toggle + Max Days + Rate (Basic/Gross) |
| 5 | Rules | Min advance notice, Max consecutive days, Half-day toggle, Weekend/Holiday sandwich toggles, Document required |

### Test 3.8: Leave Policies
**Navigate:** Sidebar → Leave Management → Leave Policies
| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | Add policy | Leave Type dropdown, Assignment Level (Company/Department/Grade/EmployeeType/Individual), Target (dynamic based on level), Override fields |

### Test 3.9: Leave Requests
**Navigate:** Sidebar → Leave Management → Leave Requests
| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | Pending approvals section | Shows pending requests with Approve/Reject buttons |
| 2 | Apply leave | Employee, Leave Type, From/To Date, Half Day toggle, auto-computed days, Reason |
| 3 | Approve | Sets status APPROVED, updates balance |
| 4 | Reject | Requires rejection note, refunds balance |
| 5 | Cancel | Only for PENDING or future APPROVED requests, refunds balance |

### Test 3.10: Leave Balances
**Navigate:** Sidebar → Leave Management → Leave Balances
| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | Balance grid | Per-employee: CL, PL, SL, EL columns with color coding (green >50%, amber 25-50%, red <25%) |
| 2 | Adjust balance | Select employee → Credit/Debit, Days, Reason → balance recalculated |

---

## PHASE 4: Payroll Configuration

### Test 4.1: Salary Components
**Navigate:** Sidebar → Payroll & Compliance → Salary Components
| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | Add earning | Name: "Basic Salary", Code: "BASIC", Type: Earning, Calculation: Fixed, Taxable: Fully Taxable |
| 2 | Add deduction | Name: "PF Employee", Code: "PF_EE", Type: Deduction |
| 3 | Conditional fields | Formula field appears when Calculation=Formula. Exemption fields appear when Taxable≠Fully Taxable |

### Test 4.2: Salary Structures
**Navigate:** Sidebar → Payroll & Compliance → Salary Structures
| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | Add structure | Name, Code, CTC Basis, Applicable Grades (multi-select), Components (dynamic rows: component dropdown + method + value) |
| 2 | Preview | Monthly breakup preview for sample CTC |

### Test 4.3: Employee Salary Assignment
**Navigate:** Sidebar → Payroll & Compliance → Employee Salary
| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | Assign salary | Employee, Structure, Annual CTC → auto-breakup preview → Save |
| 2 | Previous salary | Previous record set to isCurrent=false |

### Test 4.4: Statutory Config
**Navigate:** Sidebar → Payroll & Compliance → Statutory Config
| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | PF section | Employee Rate 12%, Employer EPF/EPS/EDLI rates, Wage Ceiling ₹15,000, VPF toggle |
| 2 | ESI section | Employee 0.75%, Employer 3.25%, Wage Ceiling ₹21,000 |
| 3 | PT section (multi-state) | Add state → enter slabs (from/to/amount), Registration Number |
| 4 | Gratuity | Formula, Base Salary, Max ₹20L, Provision Method |
| 5 | Bonus | Wage Ceiling, Min/Max %, Eligibility Days |
| 6 | LWF (multi-state) | Add state → employee/employer amounts, frequency |

### Test 4.5: Tax Config
**Navigate:** Sidebar → Payroll & Compliance → Tax & TDS
| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | Default Regime | Old/New selector |
| 2 | Slabs | Old Regime and New Regime slab tables (add/remove rows) |
| 3 | Cess Rate | Default 4% |

### Test 4.6: Bank Config
**Navigate:** Sidebar → Payroll & Compliance → Bank Config
| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | Configure | Bank Name, Account, IFSC, Branch, Payment Mode, Auto-Push toggle |

### Test 4.7: Loan Policies & Loans
**Navigate:** Sidebar → Payroll & Compliance → Loan Policies / Loans
| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | Add policy | Name, Code, Max Amount, Max Tenure, Interest Rate, EMI Cap |
| 2 | Create loan | Employee, Policy → auto-fills rate, Amount, Tenure → auto-computed EMI |
| 3 | Status transitions | Approve → Disburse (Active) → Close |

---

## PHASE 5: Payroll Run & Statutory Operations

### Test 5.1: Payroll Run — 6-Step Wizard (CRITICAL FLOW)
**Navigate:** Sidebar → Payroll Operations → Payroll Runs
| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | Create run | FAB → select Month/Year → DRAFT run created |
| 2 | **Step 1: Lock Attendance** | Shows employee count + unresolved issues → "Lock" button → status: ATTENDANCE_LOCKED |
| 3 | **Step 2: Review Exceptions** | List of exceptions (new hires, holds, missing records) → Accept/Override each → status: EXCEPTIONS_REVIEWED |
| 4 | **Step 3: Compute Salaries** | "Compute" button → shows totals (gross, deductions, net, employee count) → variance warnings for >10% changes → status: COMPUTED |
| 5 | **Step 4: Statutory Deductions** | PF/ESI/PT/TDS/LWF summary cards → "Compute Statutory" → status: STATUTORY_DONE |
| 6 | **Step 5: Approve** | Final summary → ConfirmModal → status: APPROVED |
| 7 | **Step 6: Disburse** | ConfirmModal → payslips auto-generated → status: DISBURSED/ARCHIVED |
| 8 | Verify step locking | Cannot skip steps. Each step only enabled when previous is complete |

### Test 5.2: Payslips
**Navigate:** Sidebar → Payroll Operations → Payslips
| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | View payslips | Filter by employee, month/year |
| 2 | Detail | Full earnings/deductions breakdown |
| 3 | Email button | Sends payslip (or placeholder action) |

### Test 5.3: Salary Holds
**Navigate:** Sidebar → Payroll Operations → Salary Holds
| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | Create hold | Payroll Run, Employee, Type (Full/Partial), Reason |
| 2 | Partial hold | Shows component selector |
| 3 | Release | ConfirmModal → released |

### Test 5.4: Salary Revisions
**Navigate:** Sidebar → Payroll Operations → Salary Revisions
| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | Create revision | Employee, New CTC, Effective Date → auto-calculates increment % |
| 2 | Approve → Apply | Apply creates new salary record + computes month-by-month arrears |
| 3 | Arrear detail | View month-by-month arrear breakdown |

### Test 5.5: Statutory Filings
**Navigate:** Sidebar → Payroll Operations → Statutory Filings
| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | Dashboard cards | Filed On Time %, Due This Week, Overdue |
| 2 | Create filing | Type (PF_ECR, ESI, PT, TDS, etc.), Month, Year, Amount, Due Date |
| 3 | Status transitions | Pending → Generated → Filed → Verified |

### Test 5.6: Payroll Reports
**Navigate:** Sidebar → Payroll Operations → Payroll Reports
| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | Report hub | 6 cards: Salary Register, Bank File, PF ECR, ESI Challan, PT Challan, Variance |
| 2 | Select report | Month/Year → loads report data in table format |
| 3 | Variance report | Highlights entries with >10% change |

---

## PHASE 6: ESS Portal & Approval Workflows

### Test 6.1: ESS Config
**Navigate:** Sidebar → ESS & Workflows → ESS Config
| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | Portal Access | Login Method, Password Policy, Session Timeout, MFA |
| 2 | Feature toggles | 20+ employee feature toggles (payslips, leave, attendance, etc.) |

### Test 6.2: Approval Workflows
**Navigate:** Sidebar → ESS & Workflows → Approval Workflows
| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | Add workflow | Name, Trigger Event (Leave Application, etc.), Dynamic step builder |
| 2 | Add steps | Step 1: Manager (SLA 48hrs) → Step 2: HR (SLA 24hrs) → auto-escalate toggles |
| 3 | Unique trigger | Cannot have two workflows for same trigger event |

### Test 6.3: Approval Requests
**Navigate:** Sidebar → ESS & Workflows → Approval Requests
| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | Pending tab | Shows requests pending for current user |
| 2 | Approve/Reject | Actions advance workflow or reject request |
| 3 | Step progress | Shows which step the request is at |

### Test 6.4: Notification Templates & Rules
**Navigate:** Sidebar → ESS & Workflows → Notification Templates / Rules
| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | Add template | Name, Channel (Email/SMS/Push/etc.), Subject, Body with tokens ({employee_name}, etc.) |
| 2 | Add rule | Trigger Event → Template → Recipient Role → Channel |

### Test 6.5: IT Declarations (Form 12BB)
**Navigate:** Sidebar → ESS & Workflows → IT Declarations
| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | Create declaration | Employee, FY, Regime (Old/New) |
| 2 | Sections | 80C (with ₹1.5L cap), 80CCD, 80D, 80E, 80G, 80GG, 80TTA, HRA, LTA, Home Loan, Other Income |
| 3 | Status lifecycle | Draft → Submit → Verify (HR) → Lock (for payroll) |

### Test 6.6: Self-Service Screens
**Navigate:** Sidebar → Self-Service → My Profile / My Payslips / My Leave / My Attendance / Team View

| Screen | What to verify |
|--------|---------------|
| **My Profile** | Read-only view of own employee data. "Request Update" button (placeholder). |
| **My Payslips** | Own payslips list. Detail view with earnings/deductions breakdown. |
| **My Leave** | Leave balance cards at top. "Apply Leave" form. My requests list with status. |
| **My Attendance** | Calendar view with color dots. Summary stats. "Regularize" button for missing punches. |
| **Team View (MSS)** | Team members list. Pending approvals (approve/reject). Team attendance. Team leave calendar. |

---

## PHASE 7: Performance Management

### Test 7.1: Appraisal Cycles
**Navigate:** Sidebar → Performance → Appraisal Cycles
| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | Create cycle | Name, Frequency, Start/End Date, Rating Scale (1-5 or 1-10), KRA/Competency weightage, Bell Curve toggle |
| 2 | Lifecycle | Draft → Activate → Review → Calibration → Publish → Close |

### Test 7.2: Goals & OKRs
**Navigate:** Sidebar → Performance → Goals & OKRs
| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | Create company goal | Level: Company, Title, KPI, Target, Weightage |
| 2 | Cascade | Create department goal with parent=company goal |
| 3 | Individual goals | Employee-level goals linked to department goals |

### Test 7.3: 360 Feedback
**Navigate:** Sidebar → Performance → 360 Feedback
| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | Request feedback | Employee, Rater, Rater Type (Peer/Subordinate/etc.), Dimension ratings (1-5) |
| 2 | Aggregated report | Per-dimension averages. Anonymized verbatims. |
| 3 | Anonymity suppression | If <3 responses from a rater type → that dimension suppressed |

### Test 7.4: Ratings & Calibration
**Navigate:** Sidebar → Performance → Ratings & Calibration
| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | Self-Review | Employee submits self-rating + comments |
| 2 | Manager Review | Manager assigns rating, comments, promotion recommendation |
| 3 | Publish | Sets final rating |
| 4 | Calibration view | Bell curve showing rating distribution |

### Test 7.5: Skills & Mapping
**Navigate:** Sidebar → Performance → Skills & Mapping
| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | Skill Library tab | Add skills with category (Technical/Soft/Compliance/Domain) |
| 2 | Mappings tab | Map skills to employees with current/required levels (1-5) |
| 3 | Gap analysis | Skills where current < required highlighted |

### Test 7.6: Succession Planning
**Navigate:** Sidebar → Performance → Succession Planning
| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | Plans tab | Add plan: Critical Role, Successor, Readiness (Ready Now/1 Year/2 Years/Not Ready) |
| 2 | 9-Box Grid tab | 3×3 grid with employees placed by performance × potential |
| 3 | Bench strength | Coverage stats |

---

## PHASE 8: Recruitment, Training & Advanced

### Test 8.1: Job Requisitions & Candidates
**Navigate:** Sidebar → Recruitment & Training → Job Requisitions / Candidates
| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | Create requisition | Title, Department, Openings, Budget Range, Status lifecycle |
| 2 | Add candidate | Name, Email, Source, CTC, Resume → stage progression (Applied→Shortlisted→HR→Technical→Offer→Hired) |
| 3 | Schedule interview | Round, Panelists, Date/Time, Meeting Link → Complete with feedback |

### Test 8.2: Training
**Navigate:** Sidebar → Recruitment & Training → Training Catalogue / Nominations
| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | Add training | Name, Type, Mode, Duration, Mandatory flag, Certification, Cost |
| 2 | Nominate employee | Employee + Training → status: Nominated → Enrolled → Completed |
| 3 | Completion | Completing training auto-updates linked skill proficiency |

### Test 8.3: Asset Management
**Navigate:** Sidebar → Advanced HR → Asset Management
| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | Add category | Name, Depreciation Rate |
| 2 | Add asset | Name, Category, Serial Number, Purchase Date/Value, Condition |
| 3 | Assign to employee | Asset status changes to ASSIGNED |
| 4 | Return | Set return date/condition → status back to IN_STOCK |

### Test 8.4: Expense Claims
**Navigate:** Sidebar → Advanced HR → Expense Claims
| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | Submit claim | Employee, Title, Amount, Category, Description → SUBMITTED |
| 2 | Approve/Reject | HR reviews → approve (APPROVED) or reject (REJECTED) |

### Test 8.5: HR Letters
**Navigate:** Sidebar → Advanced HR → HR Letters
| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | Templates tab | Create template with type (Offer/Appointment/etc.), body with {tokens} |
| 2 | Letters tab | Generate letter: select template + employee + date → token-resolved letter created |

### Test 8.6: Grievances
**Navigate:** Sidebar → Advanced HR → Grievances
| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | Categories | Add with name, SLA hours, auto-escalate-to |
| 2 | File grievance | Category, Description, Anonymous toggle → OPEN |
| 3 | Status flow | Open → Investigating → Resolved/Escalated → Closed |

### Test 8.7: Disciplinary Actions
**Navigate:** Sidebar → Advanced HR → Disciplinary Actions
| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | Issue warning | Employee, Type (Verbal/Written/SCN/PIP/Suspension/Termination), Charges |
| 2 | SCN specific | Reply Due By date field appears |
| 3 | PIP specific | Duration field appears. Outcome: Success/Partial/Failure |

---

## PHASE 9: Offboarding & Full & Final

### Test 9.1: Exit Requests
**Navigate:** Sidebar → Exit & Separation → Exit Requests
| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | Initiate exit | Employee, Separation Type (Resignation/Retirement/Termination/Layoff/Death), Resignation Date, Notice Waiver toggle |
| 2 | Auto LWD | Last Working Date auto-calculated from resignation date + notice period |
| 3 | Auto clearances | 5 department clearance records auto-created (IT/Admin/Finance/HR/Library) |
| 4 | Employee status | Changes to ON_NOTICE |

### Test 9.2: Clearance Dashboard
**Navigate:** Sidebar → Exit & Separation → Clearance Dashboard
| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | View departments | 5 cards: IT, Admin, Finance, HR, Library — each with checklist items |
| 2 | Clear department | ConfirmModal → marks CLEARED |
| 3 | All cleared | Exit status auto-advances to CLEARANCE_DONE |
| 4 | Progress bar | Visual indicator of clearance completion |

### Test 9.3: F&F Settlement (CRITICAL FLOW)
**Navigate:** Sidebar → Exit & Separation → F&F Settlement
| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | Compute F&F | Select exit request → "Compute" button → auto-calculates all components |
| 2 | **Verify breakdown:** | |
| | - Salary for Worked Days | Pro-rated monthly salary |
| | - Leave Encashment | Remaining PL/EL × (basic/26) |
| | - Gratuity | If tenure ≥ 5 years: (lastBasic × 15 × years) / 26, cap ₹20L |
| | - Bonus Pro-rata | If eligible under Bonus Act |
| | - Notice Pay | Positive (company pays) or negative (employee owes) |
| | - Loan Recovery | Outstanding loan balances |
| | - Asset Recovery | Unreturned/damaged asset values |
| | - Reimbursement | Approved but unpaid claims |
| | - TDS | Tax on taxable F&F components |
| | - **Net Amount** | Total of all components |
| 3 | **Separation type differences:** | |
| | - Resignation | Standard all components |
| | - Retirement | Gratuity compulsory, no notice recovery |
| | - Termination | Gratuity may be forfeited, no bonus |
| | - Layoff | Add retrenchment compensation (15 days per year) |
| 4 | Approve | ConfirmModal → APPROVED |
| 5 | Pay | ConfirmModal → PAID → employee status changes to EXITED |

---

## Files Modified from Existing Codebase (Phase 1–9)

These are PRE-EXISTING files that were updated during implementation:

| File | What Changed |
|------|-------------|
| **Backend** | |
| `avy-erp-backend/src/app/routes.ts` | Added `/company` route mount for company-admin |
| `avy-erp-backend/src/middleware/auth.middleware.ts` | Added `audit:read` to COMPANY_ADMIN permissions |
| `avy-erp-backend/src/core/dashboard/dashboard.service.ts` | Enhanced `getCompanyAdminStats()` + added `getCompanyAdminActivity()` |
| `avy-erp-backend/src/core/dashboard/dashboard.controller.ts` | Added activity controller method |
| `avy-erp-backend/src/core/dashboard/dashboard.routes.ts` | Added `/company-activity` tenant route |
| `avy-erp-backend/src/modules/hr/routes.ts` | Mounted org-structure, employee, attendance, leave, payroll, payroll-run, ess, performance, advanced, offboarding routes |
| `avy-erp-backend/prisma/schema.prisma` | Added ~76 models + ~50 enums (Phases 2-9) |
| **Mobile App** | |
| `mobile-app/src/app/(app)/_layout.tsx` | Added 17 company-admin sidebar sections |
| `mobile-app/src/app/(app)/company/_layout.tsx` | Registered `hr` nested Stack.Screen |
| `mobile-app/src/features/company-admin/dashboard-screen.tsx` | Replaced mock data with real API calls |
| `mobile-app/src/features/super-admin/audit-log-screen.tsx` | Added role-aware endpoint routing |
| `mobile-app/src/lib/api/audit.ts` | Added `listTenantAuditLogs()` method |
| `mobile-app/src/features/company-admin/api/index.ts` | Added re-exports for all 9 phase modules |
| **Web App** | |
| `web-system-app/src/App.tsx` | Added ~70 company-admin routes with RequireRole guards |
| `web-system-app/src/layouts/Sidebar.tsx` | Added 17 company-admin nav sections with Lucide icons |
| `web-system-app/src/layouts/TopBar.tsx` | Added ~70 PAGE_TITLES + SEARCH_ITEMS entries |
| `web-system-app/src/features/company-admin/CompanyAdminDashboard.tsx` | Replaced mock data with real API calls |
| `web-system-app/src/features/company-admin/api/index.ts` | Added re-exports for all 9 phase modules |

---

## Quick Smoke Test Checklist

Run through these rapidly to verify basic functionality:

- [ ] Login as Company Admin → Dashboard loads
- [ ] Sidebar shows all 17 sections
- [ ] Company Profile → can view, can edit display name, cannot edit statutory
- [ ] Locations → can edit, can delete, **CANNOT add**
- [ ] Create a Department → appears in list
- [ ] Create an Employee → Employee ID auto-generated → appears in directory
- [ ] Add a Holiday → appears in calendar
- [ ] Create a Leave Type → assign policy → apply leave → approve → balance updated
- [ ] Add Salary Component → create Structure → assign to Employee
- [ ] Run Payroll → complete all 6 steps → payslips generated
- [ ] Configure Approval Workflow → create approval request → approve steps
- [ ] Create IT Declaration → submit → verify → lock
- [ ] View My Profile (ESS) → shows own data
- [ ] Create Appraisal Cycle → add goals → self-review → manager review
- [ ] Create Job Requisition → add candidate → schedule interview
- [ ] Initiate Exit → clearances auto-created → clear all departments → compute F&F → approve → pay
- [ ] Audit Logs → shows company-scoped entries only

---

## SECTION A: Phase Dependency Map & Impact Analysis

Understanding how phases depend on each other is critical. A failure in an earlier phase cascades downstream.

### Dependency Chain

```
Phase 1 (Company Admin Core)
  └──► Phase 2 (Org Structure & Employee)
         ├──► Phase 3 (Attendance & Leave) — needs Employee + Shifts
         │      └──► Phase 5 (Payroll Run) — needs attendance data for LOP/OT
         ├──► Phase 4 (Payroll Config) — needs Employee for salary assignment
         │      └──► Phase 5 (Payroll Run) — needs components, structures, statutory config
         ├──► Phase 6 (ESS & Workflows) — needs Employee for self-service
         ├──► Phase 7 (Performance) — needs Employee + Department for goals/appraisals
         ├──► Phase 8 (Recruitment/Training/Advanced) — needs Department + Designation for requisitions, Employee for nominations/assets/grievance
         └──► Phase 9 (Offboarding) — needs Employee + Salary + Leave + Loans + Assets for F&F
```

### What Breaks If a Phase Fails

| Failed Phase | Impact |
|-------------|--------|
| **Phase 1** | TOTAL BLOCK — cannot login, navigate, or manage company. All other phases non-functional. |
| **Phase 2** | Cannot create employees → Phases 3–9 have no employee data to work with. Attendance, leave, payroll, performance, exit — all empty. |
| **Phase 3** | Attendance/Leave not tracked → Payroll Run (Phase 5) cannot compute LOP deductions or OT. Leave balances unavailable for F&F encashment. |
| **Phase 4** | No salary components/structures → Payroll Run cannot compute salaries. Employee salary assignment fails. |
| **Phase 5** | Payroll cannot run → no payslips, no statutory filings. Employee salaries not disbursed. |
| **Phase 6** | No approval workflows → leave/loan/expense approvals skip workflow (auto-approve or stuck). ESS self-service unavailable. |
| **Phase 7** | Performance reviews unavailable → no impact on payroll or other modules (isolated). |
| **Phase 8** | Recruitment/training/assets/grievance unavailable → no direct impact on core HR/payroll (isolated). |
| **Phase 9** | Cannot process exits → employees cannot be properly offboarded. F&F cannot be computed. |

### Testing Order Recommendation

Always test in phase order: **1 → 2 → 3 → 4 → 5 → 6 → 7 → 8 → 9**. Do NOT skip ahead — each phase builds on data created in the previous.

---

## SECTION B: Negative Testing Scenarios

### B.1: Authentication & Authorization Failures

| # | Scenario | Steps | Expected Result |
|---|----------|-------|-----------------|
| N-1 | Invalid login credentials | Enter wrong email/password → Login | Error toast: "Invalid credentials". No redirect. |
| N-2 | Empty email/password | Submit login form with blank fields | Validation error: "Email is required", "Password is required" |
| N-3 | Expired JWT token | Wait for token expiry (15min) → make API call | Auto-refresh via refresh token. If refresh also expired → redirect to login. |
| N-4 | Company Admin accessing Super Admin routes | Navigate to `/companies` or `/billing` directly | "No Permission" screen OR redirect to dashboard |
| N-5 | Company Admin accessing another tenant's data | Manually call `GET /api/v1/company/profile` with different `X-Tenant-ID` header | 403 Forbidden — `validateTenantAccess` blocks it |
| N-6 | Deactivated user login | Deactivate a user → try to login with that account | Error: "Account is inactive" |
| N-7 | API call without Authorization header | `curl http://localhost:3000/api/v1/company/profile` (no Bearer token) | 401 Unauthorized |
| N-8 | API call with malformed JWT | Use `Authorization: Bearer invalidtoken123` | 401 Unauthorized: "Invalid token" |

### B.2: Form Validation & Invalid Input

| # | Scenario | Screen | Steps | Expected Result |
|---|----------|--------|-------|-----------------|
| N-9 | Empty required fields | Employee Profile | Leave First Name, Last Name, DOB blank → Save | Validation errors on each required field |
| N-10 | Invalid email format | User Management | Enter "notanemail" in email field → Save | Error: "Invalid email format" |
| N-11 | Duplicate department code | Departments | Create dept with code "HR-001" twice | Error: "Department code already exists" |
| N-12 | Duplicate employee email | Employee Profile | Create 2 employees with same personal email | Error or unique constraint violation message |
| N-13 | Negative CTC value | Employee Salary | Enter `-500000` as Annual CTC | Validation: "CTC must be positive" |
| N-14 | CTC exceeds grade band | Employee Salary | Assign CTC ₹50L to Grade G1 (max ₹28,000) | Warning: "CTC exceeds grade band maximum" |
| N-15 | Future DOB | Employee Profile | Set DOB to tomorrow's date | Validation: "Date of birth cannot be in the future" |
| N-16 | Account numbers mismatch | Employee Profile Tab 4 | Enter different values in "Account Number" and "Confirm Account Number" | Error: "Account numbers do not match" |
| N-17 | Leave days exceed balance | Leave Requests | Apply 15 CL when balance is 8 | Error: "Insufficient leave balance" |
| N-18 | Overlapping leave dates | Leave Requests | Apply CL for dates that overlap an existing approved leave | Error: "Leave dates overlap with existing request" |
| N-19 | Backward date range | Leave Requests | Set "From Date" after "To Date" | Validation error or auto-swap |
| N-20 | PAN format invalid | Employee Profile | Enter "ABC" (not 10-char alphanumeric) | Validation: "Invalid PAN format" |
| N-21 | Aadhaar format invalid | Employee Profile | Enter "123" (not 12 digits) | Validation: "Aadhaar must be 12 digits" |
| N-22 | Nominee share exceeds 100% | Employee Nominees | Add 2 nominees with 60% + 60% = 120% | Error: "Nominee shares must sum to 100% or less" |
| N-23 | Payroll month duplicate | Payroll Runs | Create run for March 2026 when one already exists | Error: "Payroll run already exists for this month" |
| N-24 | Zero annual entitlement | Leave Types | Create leave type with 0 days entitlement | Validation: "Annual entitlement must be positive" |

### B.3: Business Rule Violations

| # | Scenario | Steps | Expected Result |
|---|----------|-------|-----------------|
| N-25 | Delete department with employees | Create dept → assign employee → try delete | Block: "Cannot delete: X employees assigned to this department" |
| N-26 | Delete role with users assigned | Create role → assign to user → try delete | Block: "Cannot delete role with assigned users" |
| N-27 | Location create by company admin | `POST /api/v1/company/locations` via API | 403: "Only Super Admin can add new locations" |
| N-28 | Delete HQ location | Try deleting the location marked as HQ | Warning modal: "Cannot delete headquarters" |
| N-29 | Skip payroll wizard step | On DRAFT run, try to click "Compute" (Step 3) without locking attendance | Button disabled / error: "Must complete previous steps first" |
| N-30 | Approve payroll without computing | Try to approve a COMPUTED run (skipping statutory step) | Button disabled |
| N-31 | Cancel future leave only | Try to cancel a past APPROVED leave | Error: "Cannot cancel past leave requests" |
| N-32 | Double payroll disburse | Try to disburse an already DISBURSED run | Button disabled / error: "Payroll already disbursed" |
| N-33 | Edit locked IT declaration | Modify an IT declaration with status LOCKED | All fields read-only / error on API |
| N-34 | Gratuity for <5 year tenure | Employee with 3 years tenure exits | F&F: gratuity = ₹0 (not eligible) |
| N-35 | Loan when existing loan active | Apply for loan when employee already has ACTIVE loan (if policy restricts) | Error: "Employee has an existing active loan" |

### B.4: Navigation & Route Failures

| # | Scenario | Steps | Expected Result |
|---|----------|-------|-----------------|
| N-36 | Invalid URL path | Navigate to `/app/company/hr/nonexistent` | 404 page or redirect to dashboard |
| N-37 | Direct URL access without login | Open `/app/company/profile` in incognito | Redirect to login page |
| N-38 | Browser back after logout | Logout → press browser Back | Should NOT show authenticated content; redirect to login |
| N-39 | Deep link to employee detail with invalid ID | Navigate to `/app/company/hr/employees/invalid-id-123` | "Employee not found" error or empty state |

---

## SECTION C: End-to-End User Flows

### E2E Flow 1: Complete Employee Lifecycle

**Flow:** Hire → Configure → Attend → Leave → Payroll → Payslip → Exit

| Step | Screen | Action | Verify |
|------|--------|--------|--------|
| 1 | Departments | Create "Engineering" department (ENG-001) | Appears in list |
| 2 | Designations | Create "Software Engineer" (SE-L3, Grade G3, 90 days probation) | Linked to department + grade |
| 3 | Employee Types | Create "Full-Time Permanent" (FTP-001, PF=Yes, ESI=Yes, PT=Yes) | Statutory flags correct |
| 4 | Salary Components | Create Basic (40% of CTC), HRA (50% of Basic), Special Allowance (remaining) | 3 components active |
| 5 | Salary Structures | Create "L3 Standard" with the 3 components above | Structure linked to Grade G3 |
| 6 | Employee Directory → FAB | Create employee: John Doe, DOB, Gender, Contact, Joining Date=today | Employee ID auto-generated (EMP-00001) |
| 7 | Employee Salary | Assign salary: Employee=John, Structure=L3 Standard, CTC=₹8,00,000 | Breakup preview shows Basic=₹3,20,000, HRA=₹1,60,000, SA=₹3,20,000 |
| 8 | Holiday Calendar | Add "Independence Day" 15-Aug-2026, National | Appears in calendar |
| 9 | Attendance Dashboard | Log attendance for John: Punch In 9:00 AM, Punch Out 6:00 PM | Status: PRESENT, 9 hours |
| 10 | Leave Types | Create CL (12 days/year, Paid, Monthly accrual) | Active in leave module |
| 11 | Leave Balances | Initialize balances for John | CL balance = pro-rata based on joining date |
| 12 | Leave Requests | Apply 2 days CL for John → Approve | Balance decremented by 2 |
| 13 | PF Config | Set 12% employee, 3.67% EPF employer, ₹15,000 ceiling | Saved |
| 14 | Payroll Runs | Create March 2026 run → Lock → Exceptions → Compute | John's entry shows gross, PF deduction, net pay |
| 15 | Payroll Runs | Statutory → Approve → Disburse | Payslip generated for John |
| 16 | Payslips | View John's March 2026 payslip | Earnings + Deductions + Net correct |
| 17 | Exit Requests | Initiate resignation for John | Status: ON_NOTICE, LWD calculated, 5 clearances created |
| 18 | Clearance Dashboard | Clear all 5 departments | Status: CLEARANCE_DONE |
| 19 | F&F Settlement | Compute F&F | Salary for worked days + leave encashment + loan recovery (if any) |
| 20 | F&F Settlement | Approve → Pay | Employee status: EXITED. Timeline shows EXITED event |

**Cross-module validations after this flow:**
- Employee should NOT appear in active employee filters
- Employee's payroll entry should be excluded from next month's run
- Employee's leave requests should not be approvable
- Employee's attendance should stop accepting new records

### E2E Flow 2: Complete Payroll Cycle

| Step | Screen | Action | Verify |
|------|--------|--------|--------|
| 1 | Attendance Dashboard | Verify all employees have attendance for the month | No missing records |
| 2 | Leave Requests | All pending requests approved or rejected | No PENDING status |
| 3 | Attendance Overrides | All pending overrides processed | No PENDING overrides |
| 4 | Salary Holds | Create hold for employee on disciplinary review | Hold appears |
| 5 | Payroll Runs → Step 1 | Lock attendance | Employee count correct, issues flagged |
| 6 | Step 2 | Review exceptions: held employee flagged, new hire flagged | Mark as reviewed |
| 7 | Step 3 | Compute | Held employee's salary computed but flagged. Check: Basic correctly prorated for LOP days |
| 8 | Step 4 | Statutory | PF: 12% of basic (capped at ₹15,000 PF wage). ESI: 0.75% of gross (only if gross ≤ ₹21,000). PT: state slab. TDS: monthly projection |
| 9 | Step 5 | Approve | Manager/finance signs off |
| 10 | Step 6 | Disburse | Held employee excluded from payslips. Other payslips generated. |
| 11 | Payslips | Verify each payslip | Net = Gross - PF - ESI - PT - TDS - LWF - Loan EMI |
| 12 | Salary Holds | Release hold | Employee included in next cycle |
| 13 | Payroll Reports | Check salary register | All employee entries match computation |
| 14 | Statutory Filings | Create PF ECR filing | Amount matches total PF |

### E2E Flow 3: Leave Application with Approval Workflow

| Step | Screen | Action | Verify |
|------|--------|--------|--------|
| 1 | Approval Workflows | Create workflow: Leave Application → Step 1: Manager (SLA 48h) → Step 2: HR (SLA 24h) | Saved |
| 2 | My Leave (ESS) | Employee applies for 3 days CL | Request created as PENDING |
| 3 | Approval Requests | Approval request auto-created, currentStep=1 | Visible in manager's pending list |
| 4 | Team View (MSS) | Manager sees pending approval | Can approve or reject |
| 5 | Approval Requests | Manager approves step 1 | Request advances to step 2 (HR) |
| 6 | Approval Requests | HR approves step 2 | Overall status: APPROVED |
| 7 | Leave Requests | Leave request status = APPROVED | Balance decremented |
| 8 | My Leave (ESS) | Employee sees approved leave | Status updated |

### E2E Flow 4: Salary Revision with Arrears

| Step | Screen | Action | Verify |
|------|--------|--------|--------|
| 1 | Salary Revisions | Create revision: Employee X, New CTC ₹12L (was ₹10L), Effective Date: 3 months ago | Increment % auto-calculated (20%) |
| 2 | Salary Revisions | Approve | Status: APPROVED |
| 3 | Salary Revisions | Apply | New EmployeeSalary created (isCurrent=true). Old one set to isCurrent=false. Arrear entries created for 3 months |
| 4 | Arrear detail | View breakdown | Month-by-month difference amounts shown |
| 5 | Next Payroll Run → Compute | Arrears included in computation | Total includes arrear amount |

---

## SECTION D: Bug-Prone & High-Risk Areas

### D.1: Payroll Calculation Risks

| Area | Risk | What to Verify |
|------|------|----------------|
| LOP Deduction | Wrong working days divisor (26 vs 30 vs actual) | Check: `componentAmount × (lopDays / totalWorkingDays)` per component. Verify divisor matches company config. |
| PF Wage Ceiling | PF calculated on full basic instead of capped ₹15,000 | If Basic > ₹15,000, PF employee = 12% × 15000 = ₹1,800 (not 12% × actual basic) |
| ESI Eligibility | ESI deducted for employees above ₹21,000 gross | If gross > ₹21,000 → ESI should be ₹0 |
| PT Slab Mismatch | Wrong state slab applied | Verify PT amount matches the state where employee is located |
| Rounding Errors | Net pay has decimal fractions (₹45,233.33) | Check rounding to nearest rupee per company config |
| Variance False Positives | >10% flag triggered by normal changes (new hire, salary revision) | First month employees should not trigger variance |
| Arrears Double-Count | Arrears computed twice if revision applied mid-cycle | Verify arrears only computed once per revision |
| Negative Net Pay | Deductions exceed earnings (heavy LOP + loan EMI) | System should flag for review, not disburse negative amount |

### D.2: Leave Balance Risks

| Area | Risk | What to Verify |
|------|------|----------------|
| Balance goes negative | Leave approved when balance = 0 | System should block or convert to LOP |
| Carry forward overflow | Carried 20 days when max = 10 | Max carry forward cap enforced |
| Pro-rata miscalculation | Mid-year joiner gets full-year entitlement | If joined July: entitlement = (12/12) × 9 months remaining |
| Sandwich rule inconsistency | Weekend counted as leave day incorrectly | If weekendSandwich=false, Fri-Mon should be 2 days (not 4) |
| Balance not refunded on rejection | Leave rejected but balance not restored | After rejection: balance should increase by requested days |
| Double deduction | Approve same request twice (race condition) | Balance should only decrement once |

### D.3: Multi-Step Workflow Risks

| Area | Risk | What to Verify |
|------|------|----------------|
| Payroll wizard state corruption | Step skipped via browser manipulation | Backend validates current status before allowing step transition |
| Approval workflow stuck | Approver goes on leave, SLA expires | Auto-escalation should trigger |
| Concurrent payroll runs | Two admins create run for same month | Unique constraint `[companyId, month, year]` should prevent |
| F&F computed before clearances done | Compute button available while clearances pending | Button should be disabled until CLEARANCE_DONE |
| Appraisal published prematurely | Manager publishes before HR calibration | Status must be CALIBRATION before PUBLISHED transition |

### D.4: Role-Based Access Leak Risks

| Area | Risk | What to Verify |
|------|------|----------------|
| Company Admin sees other companies | Data leak across tenants | All queries scoped by `companyId` from JWT, not client input |
| Location creation bypass | POST via API tools (Postman) | Backend returns 403 regardless of frontend |
| Sensitive field exposure | Aadhaar/PAN visible to unauthorized roles | Masked display (XXXX XXXX 4521) in all views |
| Super Admin routes accessible | Company admin calls `/platform/companies` | 403: requires `platform:admin` permission |
| Deactivated user can still act | Token cached after user deactivated | Should invalidate session / check isActive on each request |

### D.5: Data Sync Risks Across Modules

| Area | Risk | What to Verify |
|------|------|----------------|
| Employee created but salary not assigned | Employee in directory but no salary for payroll | Payroll compute should flag as exception |
| Leave approved but attendance not updated | Leave for today but attendance shows PRESENT | Attendance should auto-mark ON_LEAVE for approved leave dates |
| Loan approved but EMI not in payroll | Active loan exists but payroll doesn't deduct EMI | Payroll compute should pull active loans and deduct EMI |
| Training completed but skill not updated | Nomination completed but SkillMapping unchanged | Completion should auto-increment skill proficiency |
| Asset assigned but not in exit checklist | Asset assigned to employee but not in clearance items | Exit clearance IT department should list all assigned assets |

---

## SECTION E: API & Failure Testing

### E.1: Authentication & Token Handling

| # | Scenario | API Call | Expected |
|---|----------|---------|----------|
| A-1 | Valid token | `GET /company/profile` with valid Bearer | 200 OK |
| A-2 | Expired access token | Make call after 15min expiry | 401 → auto-refresh → retry → 200 (frontend handles) |
| A-3 | Expired refresh token | Both tokens expired | 401 → redirect to login (frontend handles) |
| A-4 | Blacklisted token (post-logout) | Logout → reuse old token | 401: "Token blacklisted" |
| A-5 | Missing X-Tenant-ID | Call tenant-scoped endpoint without header | Tenant resolved from JWT or 400 |
| A-6 | Wrong tenant ID in header | `X-Tenant-ID: other-company-tenant` | 403: "Access denied to this tenant" |

### E.2: Invalid Payload Testing

| # | Scenario | API Call | Expected |
|---|----------|---------|----------|
| A-7 | Empty body | `POST /company/shifts` with `{}` | 400: Zod validation errors listing required fields |
| A-8 | Wrong data types | `POST /hr/departments` with `{ "name": 123 }` | 400: "Expected string, received number" |
| A-9 | Extra unknown fields | Include `{ "hackerField": "malicious" }` | Extra fields ignored (Zod strips unknown), no error |
| A-10 | SQL injection in search | `GET /hr/employees?search='; DROP TABLE employees;--` | Parameterized query via Prisma. No SQL injection. Normal empty result. |
| A-11 | XSS in text fields | Create department with name `<script>alert('xss')</script>` | Stored as-is but rendered as text (not HTML) in frontend |
| A-12 | Very long string | 10,000 character department name | 400: Validation max length exceeded |
| A-13 | Negative numbers | Annual CTC = `-500000` | 400: "Must be positive" |

### E.3: Database Constraint Failures

| # | Scenario | Expected |
|---|----------|----------|
| A-14 | Unique constraint violation (duplicate dept code) | 409 Conflict or 400: "Code already exists for this company" |
| A-15 | Foreign key violation (invalid departmentId) | 400: "Department not found" |
| A-16 | Cascade delete | Delete company (Super Admin) → all HR data deleted | All child records (employees, departments, etc.) cascade deleted |
| A-17 | Self-referencing violation | Set department parent = itself | 400: "Department cannot be its own parent" |

### E.4: Network & Server Failure Behavior

| # | Scenario | Frontend Expected Behavior |
|---|----------|---------------------------|
| A-18 | Backend server down (503) | Error toast: "Server unavailable". Retry button shown. Cached data remains visible. |
| A-19 | Slow network (>5s response) | Loading spinner/skeleton shown. No duplicate submissions. |
| A-20 | Network disconnected mid-save | Error toast: "Network error". Form data preserved (not lost). |
| A-21 | Double-click submit | Only one API call made (button disabled after first click / mutation dedup) |
| A-22 | 429 Rate Limit | Toast: "Too many requests. Try again later." |

---

## SECTION F: Data Consistency Validation

### F.1: Cross-Module Visibility Tests

| # | Action | Modules to Check | Expected |
|---|--------|-----------------|----------|
| D-1 | Create employee | Employee Directory, Attendance Dashboard, Leave Balances, Payroll (Employee Salary), My Profile (ESS) | Employee appears in ALL modules |
| D-2 | Assign salary to employee | Employee Salary, Payroll Run (compute step), Payslip detail | Same CTC/breakup reflected everywhere |
| D-3 | Approve leave request | Leave Requests, Leave Balances, Attendance Dashboard (for leave dates), My Leave (ESS) | Balance decremented. Attendance shows ON_LEAVE for those dates. |
| D-4 | Complete salary revision | Employee Salary (new record, old isCurrent=false), Next payroll run (new salary used), Arrear entries | Revision reflected in payroll computation |
| D-5 | Initiate exit | Exit Requests, Employee Directory (status=ON_NOTICE), Employee Profile (status badge), Clearance Dashboard (5 records created) | Status change visible system-wide |
| D-6 | Pay F&F | Employee status=EXITED, Employee Directory (filtered out from Active), Leave system (no new requests), Payroll (excluded from next run) | Fully removed from active flows |
| D-7 | Approve loan | Loan Records (ACTIVE), Payroll Run (EMI deducted), Employee Profile | Loan visible and EMI auto-deducted |
| D-8 | Assign asset to employee | Asset Inventory (status=ASSIGNED), Asset Assignments, Employee clearance (exit) | Asset tracked and included in exit checklist |

### F.2: Balance Integrity Tests

| # | Scenario | Verify Formula |
|---|----------|---------------|
| D-9 | Leave balance after approval | `balance = opening + accrued - taken + adjusted`. After approving 2 CL: `taken` should increase by 2, `balance` should decrease by 2 |
| D-10 | Leave balance after rejection | Balance should be SAME as before the request (refunded) |
| D-11 | Leave balance after cancellation | Balance should be SAME as before the request (refunded) |
| D-12 | Loan outstanding after EMI deduction | `outstanding = outstanding - emiAmount` after each payroll run |
| D-13 | Employee salary isCurrent flag | Only ONE salary record should have `isCurrent=true` per employee at any time |
| D-14 | Payroll run totals | `totalGross = SUM(entries.grossEarnings)`, `totalNet = SUM(entries.netPay)` |

### F.3: Temporal Consistency

| # | Scenario | Verify |
|---|----------|--------|
| D-15 | Employee joining date vs probation end | `probationEndDate = joiningDate + (grade.probationMonths × 30 days)` |
| D-16 | Exit LWD calculation | `lastWorkingDate = resignationDate + noticePeriodDays` |
| D-17 | Leave pro-rata for mid-year joiner | If joined July: `entitlement = annualEntitlement × (9/12)` |
| D-18 | Salary revision arrears span | Arrear entries should cover exactly `effectiveDate → currentMonth` (no gaps, no overlaps) |

---

## SECTION G: Performance & Load Sanity Checks

These are not stress tests — they are basic sanity checks to catch obvious performance issues before production.

### G.1: Dashboard Load Times

| # | Screen | Data Volume | Acceptable Time | How to Test |
|---|--------|------------|-----------------|-------------|
| P-1 | Company Admin Dashboard | Standard | < 2 seconds | Time from navigation click to KPIs visible |
| P-2 | Employee Directory | 100 employees | < 2 seconds | Load time with search cleared |
| P-3 | Employee Directory | 500 employees | < 3 seconds | Pagination should load quickly |
| P-4 | Attendance Dashboard | 100 employees × 30 days | < 3 seconds | Summary + records list |
| P-5 | Leave Balance grid | 100 employees × 6 leave types | < 2 seconds | Grid should render without lag |
| P-6 | Payroll Run (Compute) | 100 employees | < 10 seconds | Salary computation for all employees |
| P-7 | Payroll Run (Compute) | 500 employees | < 30 seconds | Should complete without timeout |
| P-8 | Payroll Reports | 500-employee salary register | < 5 seconds | Report data load time |

### G.2: Bulk Operation Performance

| # | Operation | Volume | Acceptable Time |
|---|-----------|--------|-----------------|
| P-9 | Payslip generation (bulk) | 100 payslips in one run | < 15 seconds |
| P-10 | Holiday clone (year) | 20 holidays cloned | < 3 seconds |
| P-11 | Leave balance initialization | 100 employees × 6 types | < 10 seconds |
| P-12 | F&F computation | Single employee with 3 years of data | < 5 seconds |

### G.3: UI Responsiveness

| # | Check | How to Test | Acceptable |
|---|-------|-------------|------------|
| P-13 | Form input lag | Rapid typing in search fields | No visible lag |
| P-14 | Tab switching (Employee Profile) | Switch between 6 tabs rapidly | Instant switch, data preserved |
| P-15 | Sidebar animation | Open/close sidebar repeatedly | Smooth animation, no jank |
| P-16 | Bottom sheet performance (mobile) | Open/close edit forms rapidly | No crash or hang |
| P-17 | Infinite scroll (mobile) | Scroll through 500 employees | Smooth scrolling, new pages load |

---

## SECTION H: Enhanced Edge Cases for Existing Tests

### H.1: Employee Profile Edge Cases
*(Enhancement to Test 2.7)*

| # | Edge Case | Steps | Expected |
|---|-----------|-------|----------|
| E-1 | Employee with no grade | Create employee without selecting Grade | Probation End Date should be empty (no auto-calculation) |
| E-2 | Self as reporting manager | Try to set an employee's reporting manager to themselves | Error: "Employee cannot report to themselves" |
| E-3 | Circular reporting | A reports to B, then B reports to A | Should block or warn about circular hierarchy |
| E-4 | Future joining date | Set joining date to next month | Employee created with PROBATION status. Should be excluded from current payroll. |
| E-5 | Employee with all optional fields empty | Only fill required fields, save | Should save successfully with nulls for optional fields |

### H.2: Leave Management Edge Cases
*(Enhancement to Tests 3.7–3.10)*

| # | Edge Case | Steps | Expected |
|---|-----------|-------|----------|
| E-6 | Half-day leave | Apply 0.5 day leave | Balance decremented by 0.5 |
| E-7 | Leave spanning weekend (no sandwich) | Apply Fri-Mon with weekendSandwich=false | Days = 2 (Fri + Mon), not 4 |
| E-8 | Leave spanning weekend (with sandwich) | Apply Fri-Mon with weekendSandwich=true | Days = 4 (Fri + Sat + Sun + Mon) |
| E-9 | Leave spanning holiday | Apply leave on a national holiday date | If holidaySandwich=false → holiday excluded from count |
| E-10 | Leave during probation | Apply leave type with probationRestricted=true while on probation | Error: "Leave type not available during probation" |
| E-11 | Leave without min advance notice | Apply leave for tomorrow with minAdvanceNotice=7 days | Error: "Must apply at least 7 days in advance" |
| E-12 | Max consecutive days exceeded | Apply 20 days when maxConsecutiveDays=15 | Error: "Maximum 15 consecutive days allowed" |

### H.3: Payroll Computation Edge Cases
*(Enhancement to Test 5.1)*

| # | Edge Case | Steps | Expected |
|---|-----------|-------|----------|
| E-13 | Employee with 100% LOP | Employee absent entire month | All earning components = ₹0. Only employer contributions may remain. |
| E-14 | Mid-month joiner | Employee joined on 15th → run payroll | Salary pro-rated to 16/30 (or working days ratio) |
| E-15 | Employee crosses ESI ceiling | Employee promoted, new gross > ₹21,000 | ESI should be ₹0 from the month gross exceeds ceiling |
| E-16 | VPF enabled | Employee opts for 20% VPF instead of 12% | Employee PF = 20% of PF wage. Employer PF remains 12%. |
| E-17 | Multiple salary revisions in one month | Two revisions with different effective dates in same month | Latest revision should be used for computation |

### H.4: F&F Settlement Edge Cases
*(Enhancement to Test 9.3)*

| # | Edge Case | Steps | Expected |
|---|-----------|-------|----------|
| E-18 | Employee with < 5 years tenure | 3-year employee resigns | Gratuity = ₹0 (ineligible) |
| E-19 | Employee with exactly 5 years | 5-year employee resigns | Gratuity = (lastBasic × 15 × 5) / 26 |
| E-20 | Gratuity exceeds ₹20L cap | Very senior employee with high basic | Gratuity capped at ₹20,00,000 |
| E-21 | Notice period buyout (company initiates) | Employer waives notice | Notice pay = positive (company pays employee) |
| E-22 | Notice period shortfall (employee initiates) | Employee leaves early | Notice pay = negative (deducted from employee) |
| E-23 | Employee with no salary record | Employee created but salary never assigned | F&F: salary = ₹0, flag as exception |
| E-24 | Employee with unreturned asset | Laptop ASSIGNED but not returned | Asset recovery amount included in F&F deductions |
| E-25 | Death separation | Separation type = DEATH | Gratuity compulsory (regardless of tenure). All dues to nominee. No notice recovery. |

---

## SECTION I: Test Execution Tracking Template

Use this template to track test execution:

| Test ID | Phase | Description | Tester | Date | Status | Bug ID (if fail) | Notes |
|---------|-------|-------------|--------|------|--------|-------------------|-------|
| 1.1 | P1 | Login & Navigation | | | ☐ Pass ☐ Fail ☐ Block | | |
| 1.2 | P1 | Dashboard KPIs | | | ☐ Pass ☐ Fail ☐ Block | | |
| 1.3 | P1 | Company Profile | | | ☐ Pass ☐ Fail ☐ Block | | |
| 1.4 | P1 | Location NO CREATE | | | ☐ Pass ☐ Fail ☐ Block | | |
| ... | | | | | | | |
| N-1 | NEG | Invalid login | | | ☐ Pass ☐ Fail ☐ Block | | |
| ... | | | | | | | |
| E2E-1 | E2E | Employee Lifecycle | | | ☐ Pass ☐ Fail ☐ Block | | |
| ... | | | | | | | |

---

## SECTION J: Pre-Release Sign-Off Criteria

Before marking the release as ready for production:

### Mandatory Pass (all must be GREEN)
- [ ] All Phase 1–9 smoke tests pass
- [ ] Location CREATE restriction verified (API returns 403)
- [ ] Payroll 6-step wizard completes end-to-end
- [ ] F&F computation matches expected values
- [ ] Role-based access verified (company admin cannot access super admin routes)
- [ ] Tenant isolation verified (no cross-company data leak)
- [ ] All 4 E2E flows complete successfully
- [ ] No Critical/Blocker bugs open

### Recommended Pass
- [ ] Negative tests for authentication (N-1 through N-8) pass
- [ ] Form validation tests (N-9 through N-24) pass
- [ ] Data consistency checks (D-1 through D-18) pass
- [ ] Performance sanity checks within acceptable thresholds
- [ ] Edge cases for payroll + leave + F&F pass

### Sign-Off

| Role | Name | Date | Signature |
|------|------|------|-----------|
| QA Lead | | | |
| Dev Lead | | | |
| Product Owner | | | |

---

## SECTION K: Gap Fix Testing — Approval Workflow Wiring, SLA, Delegation, Transfers & Promotions

> **Added:** March 20, 2026 — Post Phase 1-9 gap fixes

### K.1: Approval Workflow Wiring — All 12 Modules

The approval workflow engine is now wired to ALL modules. For each trigger event below, test that creating the entity automatically creates an ApprovalRequest (when a workflow is configured).

**Pre-requisite:** Configure an approval workflow for each trigger event via Sidebar → ESS & Workflows → Approval Workflows.

| # | Trigger Event | Module | Action That Creates Request | Navigate To |
|---|--------------|--------|---------------------------|-------------|
| W-1 | `LEAVE_APPLICATION` | Leave | Apply for leave (ESS: My Leave → Apply) | Leave Requests |
| W-2 | `ATTENDANCE_REGULARIZATION` | Attendance | Request regularization (ESS: My Attendance → Regularize) | Attendance Overrides |
| W-3 | `LOAN_APPLICATION` | Payroll | Create a new loan (Payroll → Loans → New Loan) | Loans |
| W-4 | `REIMBURSEMENT` | Advanced | Submit expense claim (Advanced HR → Expense Claims → Submit) | Expense Claims |
| W-5 | `RESIGNATION` | Exit | Initiate exit request (Exit & Separation → Exit Requests → Initiate) | Exit Requests |
| W-6 | `PAYROLL_APPROVAL` | Payroll Run | Approve payroll run (Step 5 of 6-step wizard) | Payroll Runs |
| W-7 | `SALARY_REVISION` | Payroll Run | Approve salary revision (Salary Revisions → Approve) | Salary Revisions |
| W-8 | `JOB_REQUISITION` | Recruitment | Create job requisition (Recruitment → Requisitions → New) | Requisitions |
| W-9 | `ASSET_ISSUANCE` | Advanced | Assign asset to employee (Advanced HR → Assets → Assign) | Asset Management |
| W-10 | `EMPLOYEE_TRANSFER` | Transfer | Initiate transfer (Transfers & Promotions → Transfers → Initiate) | Transfers |
| W-11 | `EMPLOYEE_PROMOTION` | Transfer | Initiate promotion (Transfers & Promotions → Promotions → Initiate) | Promotions |
| W-12 | `OVERTIME_CLAIM` | Attendance | *(Placeholder — not yet wired to specific screen)* | — |

**Test steps for each:**
| Step | Action | Expected |
|------|--------|----------|
| 1 | Create workflow for the trigger event (e.g., LEAVE_APPLICATION → Step 1: Manager, SLA 48h → Step 2: HR, SLA 24h) | Workflow saved |
| 2 | Perform the triggering action (e.g., apply leave) | Entity created + ApprovalRequest auto-created |
| 3 | Check Approval Requests screen | New request visible with status PENDING, step 1 |
| 4 | Approve step 1 | Request advances to step 2 (IN_PROGRESS) |
| 5 | Approve step 2 | Request status → APPROVED |
| 6 | **No workflow test:** Delete the workflow → repeat action | Entity created normally, NO approval request created (auto-approved behavior) |

### K.2: SLA Enforcement (Cron Job)

The SLA cron runs every **15 minutes** and enforces SLA deadlines on approval steps.

**Navigate:** ESS & Workflows → Approval Workflows (configure SLA) + Approval Requests (observe results)

| # | Scenario | Steps | Expected |
|---|----------|-------|----------|
| SLA-1 | Auto-Escalate on SLA breach | Create workflow with Step 1: Manager, SLA=1h, autoEscalate=true → Create request → Wait >1h (or manually adjust createdAt in DB for testing) | After next cron run: request status = ESCALATED, stepHistory shows `{ action: "system", by: "SYSTEM_SLA" }` |
| SLA-2 | Auto-Approve on SLA breach | Workflow Step with SLA=1h, autoApprove=true → Wait for breach | After cron: if last step → AUTO_APPROVED, if not → advances to next step |
| SLA-3 | Auto-Reject on SLA breach | Workflow Step with SLA=1h, autoReject=true → Wait for breach | After cron: status = AUTO_REJECTED |
| SLA-4 | SLA not breached | SLA=48h, request created 1h ago | Cron runs but no action taken (deadline not reached) |
| SLA-5 | Cron startup | Restart backend server | Log message: "Starting SLA enforcement cron (every 15 minutes)" + immediate first run |

**Testing tip:** To test without waiting, temporarily set SLA to 0 hours in the workflow, or update the `createdAt` of an ApprovalRequest to a past time via DB.

### K.3: Manager Delegation / Proxy

**Navigate:** Sidebar → Transfers & Promotions → Manager Delegation

| # | Scenario | Steps | Expected |
|---|----------|-------|----------|
| DEL-1 | Create delegation | Manager = John (going on leave), Delegate = Jane, From = Mar 20, To = Apr 5, Reason = "Annual leave" → Save | Delegation created with Active badge |
| DEL-2 | Delegate sees pending approvals | Login as Jane (delegate) → Check approval requests | Jane should see requests that are pending for John's approval role |
| DEL-3 | Delegate cannot see outside date range | Set delegation from Apr 1–Apr 5 → Check today (Mar 20) | Jane should NOT see John's pending requests (not within active range) |
| DEL-4 | Revoke delegation | Click Revoke on an active delegation → ConfirmModal → Confirm | Delegation marked as inactive. Delegate no longer sees manager's requests. |
| DEL-5 | Overlap prevention | Create delegation for John → Jane (Mar 20–Apr 5), then create another for John → Mike (Mar 25–Apr 10) | Should block or warn about overlapping delegation dates |
| DEL-6 | Self-delegation blocked | Try to create delegation where Manager = Delegate (same person) | Error: cannot delegate to self |

### K.4: Employee Transfers

**Navigate:** Sidebar → Transfers & Promotions → Employee Transfers

| # | Scenario | Steps | Expected |
|---|----------|-------|----------|
| TR-1 | Create transfer | FAB → Employee: John, To Department: Finance (from Engineering), To Location: Mumbai (from Bangalore), Effective Date: Apr 1, Reason: "Restructuring", Type: Relocation → Save | Transfer created with status REQUESTED. `from*` fields auto-populated from John's current data. |
| TR-2 | Approval workflow triggered | If EMPLOYEE_TRANSFER workflow configured | ApprovalRequest auto-created |
| TR-3 | Approve transfer | Click Approve → ConfirmModal | Status: APPROVED |
| TR-4 | Apply transfer (manual) | Click Apply on APPROVED transfer | Employee's department, location updated. Timeline shows TRANSFERRED event. Transfer letter generated (if template exists). Status: APPLIED |
| TR-5 | Auto-apply on effective date | Approve transfer with effectiveDate = today | Should auto-apply immediately on approval |
| TR-6 | Future-dated transfer | Approve transfer with effectiveDate = next month | Status stays APPROVED (not auto-applied). Manual Apply required when date arrives. |
| TR-7 | Verify employee updated | After Apply → go to Employee Directory → check John's profile | Department = Finance, Location = Mumbai (new values) |
| TR-8 | Verify timeline | Employee Profile → Tab 6 (Timeline) | TRANSFERRED event with from/to details |
| TR-9 | Reject transfer | Create transfer → Reject with note | Status: REJECTED. Employee data unchanged. |
| TR-10 | Cancel transfer | Create transfer (REQUESTED) → Cancel | Status: CANCELLED. Only REQUESTED transfers can be cancelled. |

### K.5: Employee Promotions

**Navigate:** Sidebar → Transfers & Promotions → Employee Promotions

| # | Scenario | Steps | Expected |
|---|----------|-------|----------|
| PR-1 | Create promotion | FAB → Employee: John, To Designation: Senior Engineer (from Engineer), To Grade: G4 (from G3), New CTC: ₹12,00,000 (from ₹8,00,000), Effective Date: Apr 1 → Save | Promotion created. Increment % auto-calculated: 50%. `from*` fields from current data. |
| PR-2 | Grade validation | Try promoting to a lower grade (G2 when current is G3) | Warning: "Target grade is lower than current grade" |
| PR-3 | Approval workflow | If EMPLOYEE_PROMOTION workflow configured | ApprovalRequest created |
| PR-4 | Apply promotion | Approve → Apply | Employee designation = Senior Engineer, grade = G4. New EmployeeSalary created with CTC ₹12L (previous isCurrent=false). Timeline: PROMOTED event. Promotion letter generated. |
| PR-5 | Promotion without CTC change | Create promotion with only designation/grade change, no newCtc | Employee designation/grade updated but salary unchanged |
| PR-6 | Promotion from appraisal | In Performance → Ratings, mark promotionRecommended=true → Create promotion with appraisalEntryId linked | Promotion linked to appraisal recommendation |
| PR-7 | Verify salary update | After Apply with CTC change → Payroll → Employee Salary | New salary record with isCurrent=true, old record isCurrent=false |
| PR-8 | Verify arrears | If effectiveDate is 2 months ago and new CTC is higher | Arrears should be computed for the backdated months (via salary revision logic) |

### K.6: Cross-Module Workflow Integration Tests

| # | Scenario | Steps | Expected |
|---|----------|-------|----------|
| CW-1 | Loan with workflow | Configure LOAN_APPLICATION workflow → Create loan → Approve all steps → Verify loan status | Loan should only become APPROVED after workflow completes |
| CW-2 | Expense with workflow | Configure REIMBURSEMENT workflow → Submit claim → Approve steps | Claim approved only after workflow |
| CW-3 | Exit with workflow | Configure RESIGNATION workflow → Initiate exit → Approve steps | Exit proceeds only after workflow approval |
| CW-4 | Payroll with workflow | Configure PAYROLL_APPROVAL workflow → Run payroll wizard → Step 5 (Approve) | Returns "approval pending" if workflow exists. Payroll not auto-approved until workflow completes. |
| CW-5 | Transfer + Salary Revision | Create promotion with new CTC → Apply | Both employee profile AND salary updated in one flow |
| CW-6 | Delegate + Leave Approval | Manager on leave → Delegation active → Employee applies leave → Delegate approves | Leave approved by delegate, stepHistory shows delegate's userId |

### K.7: Updated Smoke Test Additions

Add these to the Quick Smoke Test Checklist:

- [ ] Configure approval workflow for Leave → Apply leave → Approval request created → Approve steps → Leave approved
- [ ] Create manager delegation → Delegate sees manager's pending approvals
- [ ] Initiate employee transfer → Approve → Apply → Employee data updated
- [ ] Initiate employee promotion → Approve → Apply → Designation + salary updated
- [ ] Create loan → Approval request created (if workflow configured)
- [ ] Submit expense → Approval request created (if workflow configured)
- [ ] SLA cron: Verify log message on server startup

### K.8: Files Modified/Created in Gap Fixes

| File | What Changed |
|------|-------------|
| **Backend — Schema** | |
| `prisma/schema.prisma` | Added ManagerDelegate, EmployeeTransfer, EmployeePromotion models + TransferStatus, PromotionStatus enums |
| **Backend — Workflow Wiring** | |
| `src/modules/hr/advanced/advanced.service.ts` | Added `createRequest()` calls in createRequisition, submitExpenseClaim, createAssetAssignment |
| `src/modules/hr/offboarding/offboarding.service.ts` | Added `createRequest()` in createExitRequest |
| `src/modules/hr/payroll-run/payroll-run.service.ts` | Added workflow check in approveRun, approveRevision |
| `src/modules/hr/payroll/payroll.service.ts` | Added `createRequest()` in createLoan |
| **Backend — SLA Cron** | |
| `src/workers/approval-sla.worker.ts` | NEW — SLA breach detection + auto-escalate/approve/reject |
| `src/workers/sla-cron.ts` | NEW — 15-minute interval scheduler |
| `src/app/server.ts` | Added `startSLACron()` call |
| **Backend — Delegation** | |
| `src/modules/hr/ess/ess.service.ts` | Added getActiveDelegates, listDelegates, createDelegate, revokeDelegate + enhanced getPendingForUser |
| `src/modules/hr/ess/ess.validators.ts` | Added createDelegateSchema |
| `src/modules/hr/ess/ess.controller.ts` | Added delegate controller methods |
| `src/modules/hr/ess/ess.routes.ts` | Added 3 delegate routes |
| **Backend — Transfer/Promotion** | |
| `src/modules/hr/transfer/` | NEW module — validators, service, controller, routes (14 endpoints) |
| `src/modules/hr/routes.ts` | Mounted transferRoutes |
| **Mobile App** | |
| `src/lib/api/transfer.ts` | NEW API layer |
| `src/features/company-admin/api/use-transfer-queries.ts` | NEW query hooks |
| `src/features/company-admin/api/use-transfer-mutations.ts` | NEW mutation hooks |
| `src/features/company-admin/hr/transfer-screen.tsx` | NEW screen |
| `src/features/company-admin/hr/promotion-screen.tsx` | NEW screen |
| `src/features/company-admin/hr/delegate-screen.tsx` | NEW screen |
| `src/app/(app)/_layout.tsx` | Added "Transfers & Promotions" sidebar section |
| `src/app/(app)/company/hr/_layout.tsx` | Registered 3 screens |
| **Web App** | |
| `src/lib/api/transfer.ts` | NEW API layer |
| `src/features/company-admin/hr/TransferScreen.tsx` | NEW screen |
| `src/features/company-admin/hr/PromotionScreen.tsx` | NEW screen |
| `src/features/company-admin/hr/DelegateScreen.tsx` | NEW screen |
| `src/App.tsx` | Added 3 routes |
| `src/layouts/Sidebar.tsx` | Added "Transfers & Promotions" section |
| `src/layouts/TopBar.tsx` | Added 3 page titles |

---

*Enterprise QA Testing Document — Avy ERP Company Admin & HRMS*
*Original: March 20, 2026 | Enhanced: March 20, 2026 | Gap Fixes: March 20, 2026*
*Document Version: 3.0*
