# Avy ERP — HRMS Module Configuration Guide
## Comprehensive HRMS Setup & Integration Reference

> **Document Code:** AVY-HRMS-CFG-001  
> **Module:** HRMS (Human Resource Management System)  
> **Audience:** HR Administrators, Payroll Managers, System Administrators  
> **Version:** 1.0  
> **Product:** Avy ERP (Avyren Technologies)

---

## Table of Contents

1. [Overview & HRMS Module Scope](#1-overview--hrms-module-scope)
2. [Pre-Configured Data Inherited from Tenant Onboarding](#2-pre-configured-data-inherited-from-tenant-onboarding)
3. [Organisational Structure Configuration](#3-organisational-structure-configuration)
4. [Employee Master & Core Data Configuration](#4-employee-master--core-data-configuration)
5. [Attendance Management Configuration](#5-attendance-management-configuration)
6. [Leave Management Configuration](#6-leave-management-configuration)
7. [Payroll Configuration](#7-payroll-configuration)
8. [Statutory Compliance Configuration](#8-statutory-compliance-configuration)
9. [TDS & Income Tax Configuration](#9-tds--income-tax-configuration)
10. [Employee Self-Service (ESS) Portal Configuration](#10-employee-self-service-ess-portal-configuration)
11. [Recruitment & Onboarding Workflow Configuration](#11-recruitment--onboarding-workflow-configuration)
12. [Employee Offboarding & Full & Final (F&F) Configuration](#12-employee-offboarding--full--final-ff-configuration)
13. [Performance Management Configuration](#13-performance-management-configuration)
14. [Training & Learning Management Configuration](#14-training--learning-management-configuration)
15. [Loan, Advance & Reimbursement Configuration](#15-loan-advance--reimbursement-configuration)
16. [Asset Management Configuration](#16-asset-management-configuration)
17. [Travel & Expense Management Configuration](#17-travel--expense-management-configuration)
18. [Notification & Workflow Configuration](#18-notification--workflow-configuration)
19. [Reports & Analytics Configuration](#19-reports--analytics-configuration)
20. [HRMS Integration with Other Modules](#20-hrms-integration-with-other-modules)
21. [HRMS Go-Live Readiness Checklist](#21-hrms-go-live-readiness-checklist)

---

## 1. Overview & HRMS Module Scope

The HRMS module in Avy ERP is the **central system of record for all people-related data** in an organisation. It covers the full employee lifecycle — from recruitment and onboarding to payroll, compliance, performance, and exit.

### 1.1 HRMS Sub-Modules

```
HRMS
├── Organisational Structure (Departments, Designations, Grades)
├── Employee Master (Core employee data & documents)
├── Recruitment (ATS — Applicant Tracking System)
├── Onboarding (Joining workflow, document collection)
├── Attendance Management (Biometric, Mobile, Manual)
├── Leave Management (Leave types, policies, approvals)
├── Payroll (Salary structures, computation, disbursement)
├── Statutory Compliance (PF, ESI, PT, Gratuity, Bonus)
├── TDS & Income Tax (Form 16, 24Q, IT declarations)
├── Employee Self-Service Portal (ESS)
├── Performance Management (KRA, Appraisals)
├── Training & Development (LMS)
├── Loan & Advance Management
├── Travel & Expense Management
├── Asset Management (Employee-assigned assets)
└── Offboarding & Full & Final Settlement (F&F)
```

### 1.2 HRMS Data Flow Overview

```
Org Structure  →  Employee Master  →  Attendance & Leave
                                            ↓
                                      Payroll Engine
                                            ↓
              Statutory Compliance  ←  Salary Components
                  (PF, ESI, PT)              ↓
                                        Bank Disbursement
                                            ↓
                                    Finance / GL Integration
```

---

## 2. Pre-Configured Data Inherited from Tenant Onboarding

The following data is **already configured** during Super Admin tenant onboarding (CFG-001) and is directly inherited by the HRMS module. No re-entry is required; however, HR Admin must **verify** accuracy before activating payroll.

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

### 2.5 Branch & Location Data — Inherited

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

---

## 3. Organisational Structure Configuration

### 3.1 Department Master

Define all departments in the organisation. Departments drive payroll cost centre allocation, leave policy assignment, and approval routing.

| Field | Required | Notes |
|---|---|---|
| Department Name | ✅ Yes | e.g., "Human Resources", "Engineering", "Finance", "Sales" |
| Department Code | ✅ Yes | Unique code; e.g., `HR`, `ENG`, `FIN`, `SALES` |
| Department Head | No | Employee designated as head of department |
| Cost Centre Code | No | Links to Finance module for payroll cost booking |
| Parent Department | No | For nested/hierarchical department structures |
| Status | ✅ Yes | Active / Inactive |

### 3.2 Designation / Job Title Master

| Field | Required | Notes |
|---|---|---|
| Designation Name | ✅ Yes | e.g., "Software Engineer", "Senior Manager", "HR Executive" |
| Designation Code | ✅ Yes | Unique short code; e.g., `SWE`, `SM`, `HRE` |
| Department | No | Default department for this designation |
| Grade / Band | No | Links to the Grade Master for salary range reference |
| Job Level | No | Junior / Mid-Level / Senior / Lead / Manager / Director / C-Suite |
| Status | ✅ Yes | Active / Inactive |

### 3.3 Grade / Band / Level Master

Grades define salary bands and benefit entitlements for employees grouped at similar levels.

| Field | Required | Notes |
|---|---|---|
| Grade Code | ✅ Yes | e.g., `G1`, `G2`, `M1`, `M2`, `E1` |
| Grade Name | ✅ Yes | e.g., "Associate", "Junior", "Senior", "Manager", "VP" |
| CTC Range (Min) | No | Minimum CTC for this grade |
| CTC Range (Max) | No | Maximum CTC for this grade |
| HRA Percentage | No | Grade-specific HRA entitlement |
| Leave Entitlement Override | No | If this grade has a different leave policy |
| Probation Period (months) | No | Default probation period for this grade |
| Notice Period (days) | No | Default notice period |
| Status | ✅ Yes | Active / Inactive |

### 3.4 Reporting Structure / Hierarchy

| Feature | Configuration |
|---|---|
| Reporting Manager | Each employee is linked to a reporting manager |
| Functional Manager | Secondary manager for matrix organisations |
| Skip-Level Manager | For escalation and bypass approvals |
| HR Business Partner | Dedicated HR person per department/unit |
| Org Chart | Visual hierarchical chart generated from reporting relationships |
| Approval Chain | Configures multi-level approval routing (Leave → Manager → HR → Director) |

### 3.5 Cost Centre Master

| Field | Required | Notes |
|---|---|---|
| Cost Centre Code | ✅ Yes | Linked to Finance / Accounts module |
| Cost Centre Name | ✅ Yes | e.g., "Engineering — Bengaluru" |
| Linked Department | No | Department whose payroll costs are booked here |
| Linked Plant | No | For manufacturing cost centres |
| Budget (Annual) | No | For cost control tracking |
| GL Account Code | No | General Ledger account for payroll journal entries |

### 3.6 Work Location / Category

| Category | Examples |
|---|---|
| Work Type | On-site, Remote, Hybrid |
| Employment Type | Full-time, Part-time, Contract, Intern, Consultant |
| Employment Category | Permanent, Fixed-Term, Probationary, Trainee |

---

## 4. Employee Master & Core Data Configuration

### 4.1 Employee ID Numbering

The Employee ID format is configured via the **No Series master** (inherited from onboarding, linked screen: "Employee Onboarding").

| Example Format | Config |
|---|---|
| `EMP-00001` | Prefix: `EMP-`, Count: 5, Start: 1 |
| `AVR-2026-0001` | Prefix: `AVR-2026-`, Count: 4 |
| `TMP-001` (for Contractual) | Separate No Series for each category |

### 4.2 Employee Personal Information

| Field | Required | Notes |
|---|---|---|
| Employee ID | ✅ Auto | Auto-generated from No Series |
| First Name | ✅ Yes | |
| Middle Name | No | |
| Last Name | ✅ Yes | |
| Date of Birth | ✅ Yes | For age-based compliance (retirement, ESI threshold age, etc.) |
| Gender | ✅ Yes | Male, Female, Non-Binary, Prefer not to say |
| Marital Status | No | Single, Married, Divorced, Widowed |
| Blood Group | No | For emergency records |
| Father's / Mother's Name | No | For statutory forms |
| Nationality | ✅ Yes | Indian / Foreign National |
| Religion | No | Optional; required for certain HR surveys |
| Category | No | General, OBC, SC, ST (for government contract compliance) |
| Differently Abled | No | Flag + type; for Persons with Disabilities Act compliance |
| Profile Photo | No | Photo for ID card, ESS portal, payslips |

### 4.3 Employee Contact Information

| Field | Required | Notes |
|---|---|---|
| Personal Mobile | ✅ Yes | Primary contact number |
| Alternative Mobile | No | Secondary contact number |
| Personal Email | ✅ Yes | Pre-join communication; also for ESS login |
| Official Email | No | Auto-generated from corporate email domain post-join |
| Current Residential Address | ✅ Yes | Full address with city, state, PIN |
| Permanent Address | No | If different from current; used for Form 16 |
| Emergency Contact Name | ✅ Yes | Person to contact in case of emergency |
| Emergency Contact Relation | ✅ Yes | Spouse, Parent, Sibling, Friend, etc. |
| Emergency Contact Mobile | ✅ Yes | |

### 4.4 Employment Details

| Field | Required | Notes |
|---|---|---|
| Date of Joining | ✅ Yes | Official joining date; drives all tenure calculations |
| Department | ✅ Yes | From Department Master |
| Designation | ✅ Yes | From Designation Master |
| Grade / Band | No | From Grade Master |
| Branch / Location | ✅ Yes | From Branch/Location Master |
| Plant | No | If multi-plant company |
| Employment Type | ✅ Yes | Permanent, Contract, Intern, Consultant |
| Employment Category | ✅ Yes | Full-Time, Part-Time |
| Probation End Date | No | Auto-calculated from joining date + grade probation period |
| Confirmation Date | No | Date of employment confirmation post-probation |
| Reporting Manager | ✅ Yes | Direct reporting manager |
| Functional Manager | No | Dotted-line manager (matrix structure) |
| Work Location Type | No | On-site / Remote / Hybrid |
| Shift | No | Default shift assignment from Shift Master |
| Cost Centre | No | For payroll cost allocation |

### 4.5 Statutory & Identity Documents

| Document | Field | Validation |
|---|---|---|
| PAN Card | PAN Number | 10-char alphanumeric; required for TDS |
| Aadhaar Card | Aadhaar Number | 12-digit; masked display; required for UAN linking |
| Passport | Passport Number, Expiry Date | For foreign national employees |
| Driving Licence | DL Number, Expiry Date | Optional |
| Voter ID | Voter ID Number | Optional |
| UAN | Universal Account Number (PF) | Auto-fetched or manually entered; required for PF |
| ESI IP Number | Insurance Policy Number | Auto-assigned on ESI registration |
| Bank Account No. | Primary salary account | For payroll disbursement |
| Bank IFSC Code | | |
| Bank Name & Branch | | |
| Account Type | Savings / Current | |
| PRAN | Permanent Retirement Account No. | For NPS-enrolled employees |

### 4.6 Nominee / Beneficiary Details

| Field | Notes |
|---|---|
| Nominee Name | For PF, Gratuity, Group Insurance |
| Relation to Employee | Spouse, Child, Parent, Sibling |
| Nominee Date of Birth | |
| Nominee Share % | If multiple nominees — must sum to 100% |
| Nominee Aadhaar / PAN | For identification |
| Nominee Address | |

### 4.7 Education & Qualification

| Field | Notes |
|---|---|
| Highest Qualification | Graduate, Post-Graduate, Doctorate, Diploma, etc. |
| Degree / Course Name | e.g., B.Tech CSE, MBA HR |
| Institution Name | |
| University / Board | |
| Year of Passing | |
| Marks / CGPA | |
| Certificate Upload | PDF/image of mark sheet / degree |

### 4.8 Previous Employment

| Field | Notes |
|---|---|
| Previous Employer Name | |
| Designation Held | |
| Last CTC | |
| Date of Joining (Previous) | |
| Date of Leaving | |
| Reason for Leaving | |
| Experience Letter | Upload |
| Relieving Letter | Upload |
| Previous PF Account Number | For PF transfer |

### 4.9 Employee Custom Fields

The HR Admin can define custom fields to capture company-specific data:

| Config Option | Description |
|---|---|
| Field Type | Text, Number, Date, Dropdown, Checkbox, File Upload |
| Field Label | Custom name |
| Required / Optional | |
| Section | Which section of the employee form this field appears in |
| Applicable Employment Types | e.g., Custom field only for contractual employees |

---

## 5. Attendance Management Configuration

### 5.1 Attendance Capture Methods

Configure one or more attendance capture methods:

| Method | Configuration Required |
|---|---|
| Biometric Device (ZKTeco, ESSL) | Device IP, Port, Device ID; sync interval (real-time / hourly / EOD) |
| Mobile App (GPS) | Geo-fencing ON/OFF; GPS accuracy tolerance (metres) |
| Web Punch (Browser-based) | IP restriction option; available to all employees |
| Manual Entry (HR Entry) | Who can do manual entries (HR only, or manager also) |
| Facial Recognition | Camera device credentials; face model training data |
| RFID / Proximity Card | Card reader device credentials; card-to-employee mapping |
| QR Code Scan | QR code generation and scan frequency |

### 5.2 Attendance Rules

| Rule | Configuration | Notes |
|---|---|---|
| Grace Period (Late Arrival) | Minutes | e.g., 15 mins before marking Late |
| Grace Period (Early Departure) | Minutes | e.g., 15 mins before marking Half-Day |
| Half-Day Threshold | Time in office | e.g., < 4 hours = Half-Day |
| Full-Day Threshold | Time in office | e.g., ≥ 6 hours = Full Day |
| Overtime Threshold | Hours beyond shift end | When OT computation begins |
| Night Shift Cutoff | Day-change crossing time | For night shift date attribution |
| Consecutive Absent Alert | Days | Alert HR after N consecutive absent days |
| Long Absence Policy | Days | When to trigger leave-without-pay escalation |

### 5.3 Regularization Configuration

| Setting | Description |
|---|---|
| Regularization Window | Number of days in the past an employee can regularize attendance |
| Max Regularizations per Month | Limit per employee (e.g., max 2 per month) |
| Regularization Approval | Single level (Manager) or multi-level (Manager + HR) |
| Regularization Reasons | Pre-defined list: WFH, Travel, System Error, Medical, Other |
| Auto-Regularize on Approved Leave | If leave is approved retroactively, attendance is auto-corrected |

### 5.4 Overtime (OT) Configuration

| Setting | Description |
|---|---|
| OT Calculation Method | Per-hour / flat rate / shift-based |
| OT Eligibility | By designation, grade, or department |
| OT Rate Multiplier | e.g., 1.5x for regular OT, 2x for holiday OT |
| OT Approval Required | Yes / No |
| OT Cap per Day | Maximum OT hours claimable per day |
| OT Cap per Month | Maximum OT hours claimable per month |
| OT Pay in Payroll | Auto-include in payroll or manual claim |

### 5.5 Shift Roster Configuration

| Feature | Description |
|---|---|
| Shift Assignment | Assign individual employees or groups to shifts |
| Shift Rotation | Configure cyclic shift rotation pattern (e.g., weekly shift change) |
| Shift Change Request | Employee can request shift change via ESS |
| Shift Swap | Two employees can swap shifts with manager approval |
| Default Shift | Each employee has a default shift; overrides apply on specific dates |

### 5.6 Biometric Device Integration

| Config | Description |
|---|---|
| Device Brand | ZKTeco, ESSL, Realtime, BioEnable, Mantra, etc. |
| Device IP / Port | Network address of the device |
| Device ID | Unique device identifier |
| Sync Mode | Real-time Push, Scheduled Pull (every N minutes), Manual |
| Employee Enrollment | Enroll fingerprints/face via the device or via software |
| Device Location Mapping | Map device to branch/plant for auto-assignment |
| Failed Sync Alert | Notify IT if device loses connectivity |

---

## 6. Leave Management Configuration

### 6.1 Leave Type Master

Define all leave types. Each type has its own policy, accrual rules, and approval flow.

| Field | Required | Notes |
|---|---|---|
| Leave Type Name | ✅ Yes | e.g., "Casual Leave", "Privilege Leave", "Sick Leave" |
| Leave Code | ✅ Yes | Short code; e.g., `CL`, `PL`, `SL`, `EL`, `CO`, `ML`, `PL` |
| Leave Category | ✅ Yes | Paid Leave, Unpaid Leave, Compensatory, Statutory |
| Annual Entitlement (Days) | ✅ Yes | Total days per leave year |
| Accrual Frequency | No | Monthly / Quarterly / Annual / Pro-rata |
| Accrual Day | No | Day of month when leave is credited (e.g., 1st) |
| Carry Forward Allowed | No | Yes / No |
| Max Carry Forward Days | No | Upper limit on days that can be carried to next year |
| Carry Forward Expiry | No | Carried leaves must be consumed by a date |
| Encashment Allowed | No | Yes / No |
| Max Encashable Days | No | Per year / total tenure |
| Encashment Rate | No | Per day salary calculation base (Basic / Gross) |
| Applicable Employment Types | No | All / Permanent / Contract / Intern |
| Applicable Gender | No | All / Female only (e.g., Maternity Leave) |
| Minimum Tenure for Eligibility | No | e.g., must have completed 6 months to avail PL |
| Minimum Advance Notice | No | Days before leave must be applied |
| Min Days per Application | No | e.g., ML must be taken for minimum 26 weeks |
| Max Consecutive Days | No | Max days in a single leave application |
| Allow Half-Day | No | Yes / No |
| Weekend Sandwich Rule | No | If weekend falls between leave days, include or exclude |
| Holiday Sandwich Rule | No | Same for holidays between leave days |
| Documentation Required | No | Medical certificate, etc. — for how many days |
| LOP on Excess | No | If leave exceeds balance, auto-convert to LOP |

### 6.2 Standard Leave Types (India)

| Leave Type | Code | Statutory Basis | Typical Entitlement |
|---|---|---|---|
| Casual Leave | CL | Factories Act / Shops & Establishments | 12 days / year |
| Privilege Leave / Earned Leave | PL / EL | Factories Act | 15–18 days / year |
| Sick Leave | SL | Shops & Establishments | 12 days / year |
| Maternity Leave | ML | Maternity Benefit Act, 1961 | 26 weeks (for first 2 children) |
| Paternity Leave | PTL | Company policy | 5–15 days |
| Bereavement Leave | BL | Company policy | 3–5 days |
| Compensatory Off | CO | Company policy | Accrued on worked holidays |
| Leave Without Pay | LOP | — | No entitlement; auto-deduction |
| National Holidays | NH | National & Festival Holidays Act | 3 national + state-declared |
| Optional Holidays | OH | Company policy | Typically 2 per year |
| Marriage Leave | MAL | Company policy | 3–5 days |
| Study Leave | STL | Company policy | Varies |
| Sabbatical | SAB | Company policy | Varies |

### 6.3 Holiday Calendar

| Feature | Configuration |
|---|---|
| Holiday Name | e.g., "Independence Day", "Deepavali", "Eid" |
| Holiday Date | Specific calendar date |
| Holiday Type | National Holiday, Regional Holiday, Company Holiday, Optional Holiday |
| Branch / Location Specific | Some holidays may apply only to specific branches (e.g., regional holidays) |
| Repeating | Annual holidays auto-repeat |
| Restricted Holiday | Optional holiday that employee must request in advance |

### 6.4 Leave Policy Assignment

Leave policies can be assigned at multiple levels:

| Assignment Level | Description |
|---|---|
| Company-wide | All employees get the same leave policy |
| Department-wise | Different departments have different entitlements |
| Designation-wise | e.g., C-suite may have extra privilege leave |
| Grade-wise | Higher grades may have more carry-forward allowances |
| Employment Type-wise | Contract employees get fewer leaves than permanent |
| Individual Override | Specific employee overrides (e.g., extended maternity) |

### 6.5 Leave Approval Workflow

| Configuration | Options |
|---|---|
| Approval Levels | 1-level (Manager only) / 2-level (Manager + HR) / 3-level (Manager + HR + Director) |
| Auto-Approval | For certain leave types after N days of no action |
| Auto-Rejection | If no action taken beyond N days |
| Manager Proxy | Designate an alternate approver when manager is on leave |
| HR Override | HR can approve/reject any leave regardless of hierarchy |
| Notification | Email / mobile push when leave is applied, approved, rejected |

### 6.6 Leave Balance Management

| Feature | Description |
|---|---|
| Opening Balance | Enter opening balances for employees joining mid-year |
| Pro-rata Calculation | Auto-calculate entitlement based on joining date |
| Year-End Processing | Carry forward, encash, or lapse expired balances |
| Leave Adjustment | Manual credit/debit with reason by HR |
| Negative Leave Balance | Allow or restrict employees from going into negative balance |

---

## 7. Payroll Configuration

### 7.1 Salary Component Master

Define all components that make up an employee's salary package.

| Field | Required | Notes |
|---|---|---|
| Component Name | ✅ Yes | e.g., "Basic Salary", "HRA", "Special Allowance" |
| Component Code | ✅ Yes | Short code; e.g., `BASIC`, `HRA`, `SA`, `TA` |
| Component Type | ✅ Yes | Earning / Deduction / Employer Contribution |
| Calculation Method | ✅ Yes | Fixed Amount, % of Basic, % of Gross, Formula-based |
| Calculation Formula | Conditional | e.g., `HRA = 40% of Basic` or `SA = Gross - Basic - HRA - TA` |
| Taxable | ✅ Yes | Fully Taxable / Partially Exempt / Fully Exempt |
| Exemption Section | Conditional | e.g., Section 10(13A) for HRA, Section 10(14) for TA |
| Exemption Limit | Conditional | e.g., ₹200/day for food allowance |
| PF Inclusion | No | Include in PF wage calculation |
| ESI Inclusion | No | Include in ESI gross salary |
| Bonus Inclusion | No | Include in bonus computation base |
| Gratuity Inclusion | No | Include in gratuity base salary |
| Show on Payslip | ✅ Yes | Yes / No — controls payslip visibility |
| Payslip Order | No | Display sequence on payslip |
| Status | ✅ Yes | Active / Inactive |

### 7.2 Standard Salary Components (India)

**Earnings:**
| Component | Code | Typical % | Tax Treatment |
|---|---|---|---|
| Basic Salary | BASIC | 40–50% of Gross CTC | Fully Taxable |
| House Rent Allowance (HRA) | HRA | 40–50% of Basic | Exempt u/s 10(13A) — conditions apply |
| Special Allowance | SA | Residual amount | Fully Taxable |
| Conveyance Allowance | CA | Fixed ₹1,600/month | Fully Taxable (post 2018) |
| Medical Allowance | MA | Fixed ₹1,250/month | Fully Taxable (post 2018) |
| Leave Travel Allowance (LTA) | LTA | Fixed | Exempt u/s 10(5) — twice in 4 years |
| Food/Meal Allowance | FOOD | ₹50/meal | Exempt up to ₹50/meal |
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
| Loan EMI Deduction | LOAN | If employee has taken salary loan |
| Salary Advance Recovery | ADV | Recovery of advance paid |

**Employer Contributions (not part of employee CTC unless structured):**
| Component | Code | Notes |
|---|---|---|
| PF Employer Contribution | PF_ER | 12% of Basic (up to ₹15,000 wage cap) |
| ESI Employer Contribution | ESI_ER | 3.25% of Gross (for gross ≤ ₹21,000) |
| Gratuity Provision | GRAT | 4.81% of Basic (actuarial or AS-15 basis) |
| Superannuation | SA_ER | 15% of Basic (if scheme exists) |

### 7.3 Salary Structure / Template

A salary structure maps which components apply to which employees, along with their calculation basis.

| Field | Required | Notes |
|---|---|---|
| Structure Name | ✅ Yes | e.g., "IT Employee Grade 1 Structure" |
| Structure Code | ✅ Yes | Short unique code |
| Applicable Grade(s) | No | Assign to one or more grades |
| Applicable Designation(s) | No | Assign to specific designations |
| Applicable Employment Type | No | Permanent / Contract / Intern |
| Components | ✅ Yes | Select active components from Component Master |
| CTC Basis | ✅ Yes | Whether the structure is CTC-based or take-home based |

### 7.4 Payroll Run Configuration

| Setting | Description |
|---|---|
| Payroll Month Lock | Lock a month's payroll after processing to prevent changes |
| Arrears Processing | Enable/disable automatic arrears calculation when salary is revised mid-month |
| Revised Salary Effective Date | Configure whether revision takes effect from start of month or joining date |
| LOP (Loss of Pay) Rate | Per-day calculation basis: Monthly Salary ÷ 26 days / ÷ 30 days / ÷ Actual Working Days |
| Pro-rata for New Joiners | Calculate salary proportionally for joiners mid-month |
| Pro-rata for Exits | Same for employees exiting mid-month |
| Rounding Rules | Round payslip components to nearest rupee / 50p / no rounding |
| Negative Salary Handling | What to do if deductions exceed earnings — flag for review or generate negative payslip |

### 7.5 Salary Revision Configuration

| Feature | Description |
|---|---|
| Increment Types | % increment, Fixed increment, New CTC |
| Effective Date Options | Retrospective / Prospective |
| Arrears Auto-Calculation | Compute and pay arrears automatically |
| Revision Letter Generation | Auto-generate revised appointment / increment letter |
| Increment Freeze Policy | Lock increments during appraisal/budget cycle |

### 7.6 Bank Disbursement Configuration

| Setting | Description |
|---|---|
| Payment Mode | NEFT, RTGS, IMPS, Cheque |
| Bank File Format | Bank-specific salary advice formats (SBI, HDFC, ICICI, Axis, Kotak, etc.) |
| Bank Account (Employer) | Company's salary disbursement account details |
| Bulk Transfer | Generate a single debit file for all employee salaries |
| Payment Date | Linked to the disbursement day configured during onboarding |
| Failed Transaction Handling | Re-attempt logic and alert on bounced payments |
| Salary On Hold | Flag specific employees' salary to not be disbursed |

### 7.7 Reimbursements Configuration

| Setting | Description |
|---|---|
| Reimbursement Types | Medical, LTA, Internet, Phone, Fuel, Vehicle, Books, Uniform, etc. |
| Claim Submission Deadline | Last date to submit claims per month |
| Approval Workflow | Single / multi-level |
| Documentation Required | Receipts, bills, travel tickets |
| Maximum Claim Limit | Per claim / per month / per year |
| Tax Treatment | Which reimbursements are tax-exempt and conditions |
| Payroll Integration | Include approved claims in payroll automatically |

---

## 8. Statutory Compliance Configuration

### 8.1 Provident Fund (PF) Configuration

| Setting | Options | Notes |
|---|---|---|
| PF Applicability Threshold | Employees with Basic ≤ ₹15,000 are mandatory; voluntary contribution allowed above | |
| Employee Contribution Rate | 12% (standard) | Can be increased voluntarily |
| Employer Contribution — EPF | 3.67% of Basic | Remaining after EPS allocation |
| Employer Contribution — EPS | 8.33% of Basic (max ₹1,250/month) | Employees' Pension Scheme |
| Employer Contribution — EDLI | 0.5% of Basic (max ₹75/month) | Employees' Deposit Linked Insurance |
| PF Admin Charges | 0.50% of Basic (min ₹500/month) | EPF Admin; 0.01% for EDLI Admin |
| Wage Ceiling | ₹15,000 | PF calculated on Basic up to ₹15,000 |
| Voluntary PF | Allow employees to contribute more than 12% | Excess is VPF; employer doesn't match |
| Excluded Components | Specify components excluded from PF wage | e.g., HRA, allowances |
| PF Returns Format | ECR 2.0 (Electronic Challan cum Return) | Monthly upload to EPFO portal |

### 8.2 ESI (Employee State Insurance) Configuration

| Setting | Options | Notes |
|---|---|---|
| ESI Applicability | Mandatory for companies with ≥ 10 employees AND employee gross ≤ ₹21,000/month | |
| Employee Contribution Rate | 0.75% of Gross | |
| Employer Contribution Rate | 3.25% of Gross | |
| ESI Wage Ceiling | ₹21,000/month gross | Above this, employee exits ESI |
| ESI Month Closure Date | 15th / 21st of following month for challan | |
| ESI Excluded Wages | List components excluded from ESI gross | |

### 8.3 Professional Tax (PT) Configuration

PT rates and applicability vary by state. Configure for each state in which the company has employees:

| State | Applicability | Slab Configuration |
|---|---|---|
| Karnataka | ✅ Applicable | Monthly slab: ₹0–₹14,999 = Nil; ₹15,000+ = ₹200/month |
| Maharashtra | ✅ Applicable | Monthly slab based on income range |
| Tamil Nadu | ✅ Applicable | State-specific slabs |
| Andhra Pradesh | ✅ Applicable | State-specific slabs |
| West Bengal | ✅ Applicable | State-specific slabs |
| Gujarat | ✅ Applicable | State-specific slabs |
| Telangana | ✅ Applicable | State-specific slabs |
| Kerala | ✅ Applicable | State-specific slabs |
| Other States | Not applicable | No PT in remaining states |

For each applicable state:
- Configure income slabs (From Amount, To Amount)
- PT Amount per slab
- Frequency: Monthly / Semi-annual
- PT Registration Number (from Statutory Identifiers)

### 8.4 Gratuity Configuration

| Setting | Description |
|---|---|
| Applicability | Employees with ≥ 5 years of service |
| Calculation Formula | (Last Basic Salary × 15 × Years of Service) ÷ 26 |
| Gratuity Base | Basic + DA (or as per Payment of Gratuity Act) |
| Maximum Gratuity | ₹20,00,000 (tax-exempt limit) |
| Provision Method | Monthly accounting provision or actual at exit |
| Gratuity Trust | Yes (private trust) / No (LICI scheme or employer-funded) |
| Forfeiture Rules | Forfeiture for terminated employees as per Act |

### 8.5 Bonus Configuration (Payment of Bonus Act)

| Setting | Description |
|---|---|
| Applicability | Employees with annual salary ≤ ₹21,000/month AND establishment employing ≥ 20 persons |
| Bonus Wage Ceiling | ₹7,000/month (or minimum wage, whichever is higher) — for calculation |
| Minimum Bonus | 8.33% of annual wages |
| Maximum Bonus | 20% of annual wages |
| Bonus Calculation Period | April – March |
| Eligibility: Minimum Working Days | 30 working days in the year |
| Bonus Payment Due Date | 8 months after accounting year closure |
| Allocable Surplus | Bonus drawn from 60% of gross profit (public companies) / 67% (others) |

### 8.6 Labour Welfare Fund (LWF) Configuration

| Setting | Description |
|---|---|
| Applicable States | Configure for each state with LWF (Maharashtra, Andhra Pradesh, Karnataka, etc.) |
| Employee Contribution | State-specific amount (typically ₹6–₹30 per period) |
| Employer Contribution | State-specific multiplier of employee contribution |
| Deduction Frequency | Monthly / 6-monthly / Annual (state-specific) |

### 8.7 Statutory Reports & Filings

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

## 9. TDS & Income Tax Configuration

### 9.1 Tax Regime Configuration

| Setting | Options | Notes |
|---|---|---|
| Default Tax Regime | Old Regime / New Regime (default post FY 2023-24) | Employees can individually opt out |
| Employee Declaration Deadline | Date by when employees must submit Form 12BB / IT declaration | |
| Provisional vs Final Declaration | System uses provisional at the start of year; switches to final at year end | |

### 9.2 Income Tax Slabs

Configure slabs for both regimes:

**Old Tax Regime (FY 2025-26):**
| Income Slab | Tax Rate |
|---|---|
| Up to ₹2,50,000 | Nil |
| ₹2,50,001 – ₹5,00,000 | 5% |
| ₹5,00,001 – ₹10,00,000 | 20% |
| Above ₹10,00,000 | 30% |
| Surcharge & Cess | As applicable |

**New Tax Regime (FY 2025-26):**
| Income Slab | Tax Rate |
|---|---|
| Up to ₹3,00,000 | Nil |
| ₹3,00,001 – ₹7,00,000 | 5% |
| ₹7,00,001 – ₹10,00,000 | 10% |
| ₹10,00,001 – ₹12,00,000 | 15% |
| ₹12,00,001 – ₹15,00,000 | 20% |
| Above ₹15,00,000 | 30% |

> **Note:** Tax slabs must be updated every April at the start of a new financial year per Union Budget announcements.

### 9.3 Investment Declaration Configuration

Configure the deduction heads that employees can declare under IT declarations (Form 12BB):

| Section | Description | Limit |
|---|---|---|
| 80C | LIC, PPF, ELSS, NSC, Home Loan Principal, School Fees, etc. | ₹1,50,000 |
| 80CCC | Pension Fund | ₹1,50,000 (within 80C limit) |
| 80CCD(1) | NPS Employee Contribution | ₹1,50,000 (within 80C limit) |
| 80CCD(1B) | NPS Additional Contribution | ₹50,000 (over and above 80C) |
| 80D | Health Insurance Premium (self, family, parents) | ₹25,000 / ₹50,000 (senior citizen) |
| 80DD | Dependent Disabled | ₹75,000 / ₹1,25,000 |
| 80DDB | Medical Treatment (specified diseases) | ₹40,000 / ₹1,00,000 |
| 80E | Education Loan Interest | No limit |
| 80EEA | Home Loan Interest (affordable housing) | ₹1,50,000 |
| 80G | Donations | 50% / 100% depending on organisation |
| 80GG | Rent (HRA not received) | Least of three conditions |
| 80TTA | Savings Bank Interest | ₹10,000 |
| 80TTB | Senior Citizen FD/RD Interest | ₹50,000 |
| HRA Exemption | Rent paid; HRA exemption u/s 10(13A) | Min of 3 conditions |
| LTA Exemption | Leave Travel Allowance u/s 10(5) | Actual travel cost |
| Home Loan Interest | Section 24(b) | ₹2,00,000 |

### 9.4 Perquisites Configuration

| Perquisite | Tax Treatment |
|---|---|
| Company Car (personal use) | Taxable as perquisite — cc-based rate |
| Accommodation (company-provided) | % of salary depending on city population |
| Stock Options (ESOPs) | Taxable at vesting/exercise |
| Interest-free / concessional loans | Taxable on differential interest |
| Club Membership | Fully taxable perquisite |
| Gift Vouchers | Up to ₹5,000 per year tax-exempt |
| Medical reimbursement | Up to ₹15,000 per year (Old Regime) |

### 9.5 TDS Computation & Form 16

| Feature | Description |
|---|---|
| Monthly TDS Projection | System computes estimated annual tax and divides by remaining months for monthly TDS |
| Revised TDS Computation | Auto-recalculates when salary is revised or new declarations submitted |
| Shortfall Recovery | If TDS shortfall detected in last 3 months of FY, recovered from those months |
| Form 16 — Part A | TDS certificate generated from 26AS data; issued by May 31 |
| Form 16 — Part B | Salary breakdown and exemption details; generated by system |
| Bulk Form 16 Generation | Generate for all employees in one action; auto-emailed to employees |
| Form 26AS Reconciliation | Match TDS deposited against 26AS for employee records |
| Form 24Q | Quarterly TDS return filed with Income Tax Department |

---

## 10. Employee Self-Service (ESS) Portal Configuration

### 10.1 ESS Access Configuration

| Setting | Description |
|---|---|
| ESS URL / Subdomain | Unique URL for the company's ESS portal |
| Login Method | Username + Password / SSO (Google / Microsoft) / OTP |
| First Login Password | Auto-set to Employee Code or DOB; force change on first login |
| Password Policy | Min length, complexity, expiry, history |
| Session Timeout | Auto-logout after N minutes of inactivity |
| MFA | Optional / Mandatory for all / Mandatory for sensitive actions |

### 10.2 ESS Module Enablement

Enable or disable ESS features per company policy:

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
| Training Enrollment | Configurable | Browse and enroll in training programs |
| Help Desk / Ticket Raise | Configurable | Raise HR, IT, or Admin queries |
| Directory | Configurable | Company employee directory with contacts |
| Holiday Calendar View | ✅ Recommended | View upcoming company holidays |
| HR Policy Documents | Configurable | Employee handbook, policies, SOPs |

### 10.3 Manager Self-Service (MSS) Configuration

Managers get additional features in the same portal:

| Feature | Description |
|---|---|
| Leave Approval | Approve / reject team members' leave requests |
| Attendance Regularization Approval | Approve regularization requests |
| Team Attendance View | View team's daily/monthly attendance |
| Team Leave Calendar | Calendar view of team leaves for planning |
| OT Approval | Approve team overtime claims |
| Performance Review | Set KRAs and submit reviews for reportees |
| Reimbursement Approval | Approve expense claims |
| Asset Approval | Approve asset requests |

---

## 11. Recruitment & Onboarding Workflow Configuration

### 11.1 Recruitment Module Setup

| Configuration | Description |
|---|---|
| Job Requisition Approval | Multi-level approval before a job opening is posted (e.g., Department Head → HR → CEO) |
| Job Portal Integration | Link to Naukri, LinkedIn, Indeed, Internshala for auto-posting |
| Application Sources | Walk-in, Referral, Job Portal, Campus, Consultancy, Direct |
| Applicant ID Series | No Series for applicant tracking (linked to "Recruitment" screen) |
| Interview Stages | Configurable pipeline: Screening → L1 Interview → L2 Interview → HR Interview → Offer |
| Interview Feedback Form | Structured form with rating scales per competency |
| Offer Letter Template | Auto-populate with candidate details and salary structure |
| Offer Validity Period | Number of days offer is valid |
| Background Verification | BGV agency integration and checklist |
| Offer to Joining Conversion | Mark as joined and trigger employee onboarding |

### 11.2 Employee Onboarding Checklist

Pre-configure the joining checklist that must be completed for every new employee:

| Checklist Item | Responsible | Timing |
|---|---|---|
| Appointment Letter Issuance | HR | Before joining |
| Bank Account Opening | Employee / HR | Day 1 |
| ID Card Generation | Admin / HR | Day 1 |
| Workstation / Laptop Allotment | IT | Day 1 |
| Email ID Creation | IT | Day 1 |
| System Access Provisioning | IT | Day 1 |
| Induction Program Scheduling | HR | Week 1 |
| Document Collection (PAN, Aadhaar, Bank, Salary Slips) | HR | Day 1 – Week 1 |
| UAN Activation / PF Enrollment | HR | Within 30 days |
| ESI Registration (if applicable) | HR | Within 10 days |
| Probation Period Confirmation | HR / Manager | End of probation |

### 11.3 Document Collection Configuration

Define required documents per employment type:

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

---

## 12. Employee Offboarding & Full & Final (F&F) Configuration

### 12.1 Resignation & Exit Workflow

| Configuration | Description |
|---|---|
| Resignation Submission | Employee submits via ESS or HR enters on behalf |
| Notice Period Calculation | Auto-calculated from designation/grade notice period setting |
| Notice Period Waiver | Manager / HR can approve notice period buyout |
| Exit Interview | Configure questionnaire; assigned to HR |
| Knowledge Transfer Checklist | Configure tasks to be completed before exit |
| Clearance Process | Department-wise clearance (IT, Finance, Admin, Library, etc.) |
| Clearance Approval | Each department head must digitally clear the employee |

### 12.2 Full & Final Settlement Configuration

| Component | Description |
|---|---|
| Salary for Worked Days | Pro-rated salary for the exit month |
| Leave Encashment | Remaining EL/PL balance encashed as per policy |
| Gratuity Payment | If tenure ≥ 5 years; calculated per formula |
| Bonus (Pro-rata) | If applicable under Bonus Act |
| Loan / Advance Recovery | Deduct outstanding loan/advance balance |
| Asset Recovery | Value deduction for unreturned assets |
| Notice Period Pay Recovery | If employee leaves short of notice period |
| Reimbursement Settlement | Pay any pending approved claims |
| TDS on F&F | Compute tax on gratuity (excess of ₹20L), notice pay, etc. |
| F&F Payslip | Generate a final payslip showing all F&F components |

### 12.3 Employee Separation Types

| Type | Examples | Notes |
|---|---|---|
| Voluntary Resignation | Employee-initiated | Notice period applicable |
| Retirement | Age-based (typically 58/60) | Gratuity compulsory |
| Superannuation | Fixed-term contract end | |
| Termination (For Cause) | Disciplinary action | Gratuity forfeiture rules apply |
| Layoff / Retrenchment | Organisational restructuring | Statutory compensation as per ID Act |
| Death / Incapacitation | | Nominee receives all dues |
| Absconding | Unauthorised absence | Legal notice before deactivation |

---

## 13. Performance Management Configuration

### 13.1 Appraisal Cycle Setup

| Setting | Description |
|---|---|
| Appraisal Frequency | Annual / Semi-annual / Quarterly |
| Appraisal Period | e.g., April 2024 – March 2025 |
| Appraisal Start Date | When employees / managers start filling forms |
| Appraisal Submission Deadline | Last date for form submission |
| Rating Scale | 1–5, 1–10, or custom labels (Exceptional / Exceeds / Meets / Below / Poor) |
| Appraisal Participants | Self-appraisal, Manager review, Skip-level review, Peer review (360°) |
| Weightages | e.g., KRA: 70%, Competency: 20%, Behaviour: 10% |
| Moderation | Group moderation after individual reviews to normalize ratings |
| Bell Curve / Forced Distribution | Configurable distribution (e.g., 10% Exceptional, 25% Exceeds, etc.) |

### 13.2 KRA / KPI Configuration

| Setting | Description |
|---|---|
| KRA Master | Define company-wide Key Result Areas |
| KPI per KRA | Define measurable KPIs for each KRA |
| Department KRA Template | Pre-assign KRAs by department to save setup time |
| Target Setting | Numeric targets or qualitative milestones |
| Mid-Year Review | Optional check-in at 6 months |
| Goal Cascading | Manager-set org goals cascade to employee-level KRAs |

---

## 14. Training & Learning Management Configuration

| Setting | Description |
|---|---|
| Training Catalogue | Define available training programs (internal + external) |
| Training Type | Technical, Compliance, Soft Skills, On-the-Job, E-Learning |
| Mandatory Trainings | Flag certain trainings as mandatory with completion deadlines |
| Training Nomination | HR / Manager nominates employees; or employee self-enroll |
| Training Attendance | Mark attendance / completion |
| Assessment / Test | Post-training quiz to validate learning |
| Training Cost | Track per-employee training cost |
| Training Budget | Department-wise training budget |
| External Training | Track external certifications, courses, degrees |
| Training Calendar | Published company training schedule |

---

## 15. Loan, Advance & Reimbursement Configuration

### 15.1 Loan Types

| Loan Type | Config Required |
|---|---|
| Salary Advance | Max advance amount (e.g., 1 month gross), number of EMI months |
| Personal Loan | Max loan amount, interest rate (if any), EMI configuration |
| Emergency Loan | Fast-track approval; higher limits for critical situations |
| Vehicle Loan (Company-subsidised) | Loan terms, interest rate, EMI from salary |
| Education Loan | Linked to training / professional development |

### 15.2 Loan Configuration

| Setting | Description |
|---|---|
| Maximum Loan Amount | Fixed cap or formula based on CTC/tenure |
| Tenure (months) | Maximum repayment period |
| Interest Rate | 0% (interest-free) or configured % |
| EMI from Payroll | Auto-deduct from monthly payroll |
| Approval Levels | HR → Finance → Management |
| Eligibility Criteria | Min tenure, employment type, no pending loan |
| Prepayment | Allow/disallow early repayment |
| F&F Recovery | Outstanding balance recovered during Full & Final |

### 15.3 Reimbursement Types

| Type | Description | Tax Treatment |
|---|---|---|
| Medical Reimbursement | Bills for self/family treatment | Up to ₹15,000/year exempt (Old Regime) |
| LTA Reimbursement | Travel costs for LTA claim | Exempt u/s 10(5) — conditions apply |
| Internet/Phone Allowance | Monthly bill reimbursement | Taxable if above prescribed limit |
| Fuel Allowance | Petrol bills for official use | Company policy-based |
| Business Travel | Hotels, flights, meals on official trips | Non-taxable with receipts |
| Uniform Allowance | Purchase of company uniform | Non-taxable up to prescribed limit |

---

## 16. Asset Management Configuration

| Configuration | Description |
|---|---|
| Asset Category Master | Laptop, Desktop, Mobile, Car, SIM Card, ID Card, Access Card, Keys, etc. |
| Asset Master | List of all physical assets with serial numbers, purchase date, value |
| Asset Assignment | Map asset to employee; generate asset receipt/acknowledgement |
| Asset Condition Tracking | Good / Damaged / Lost |
| Depreciation | Asset depreciation schedule (linked to Finance module) |
| Asset Return on Exit | Mandatory asset return checklist during offboarding |
| Asset Value Deduction | Deduct asset value from F&F if not returned or damaged |

---

## 17. Travel & Expense Management Configuration

| Configuration | Description |
|---|---|
| Travel Grades | Define travel entitlements by grade (air class, hotel category) |
| Daily Allowance (DA) | City-wise per diem rates |
| Advance Request | Enable employee to request travel advance before trip |
| Expense Claim Submission | Post-trip expense claim with bills |
| Receipt Upload | Mandatory receipt upload for claims above ₹N |
| Approval Workflow | Manager → Finance approval |
| Expense Policies | Company travel policy document linkable to claim form |
| Integration with Payroll | Approved claims auto-added to payroll |
| GST on Expenses | Capture GST invoice details for input credit |

---

## 18. Notification & Workflow Configuration

### 18.1 Notification Channels

| Channel | Use Cases |
|---|---|
| Email | Payslip dispatch, Form 16, leave approval/rejection, salary revision letter |
| SMS | Salary credit alert, OTP for ESS login |
| In-App Notification | Leave status, attendance alerts, task reminders |
| WhatsApp | Salary credit, leave approval, payslip (optional; via WhatsApp Business API) |
| Push Notification (Mobile App) | Leave updates, shift change, announcements |

### 18.2 Automated Notification Triggers

| Event | Recipients |
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
| Probation approaching end | HR, Manager |
| Work anniversary / Birthday | HR (optional: employee too) |
| Exit clearance pending | Clearance department head |
| F&F payment processed | Employee |
| Statutory payment due reminder | HR / Finance |

### 18.3 Approval Workflow Configuration

| Workflow | Configuration |
|---|---|
| Leave Approval | Number of levels, escalation time, auto-approve/reject |
| Attendance Regularization | Number of levels |
| Overtime Approval | Levels, per-request or batch |
| Reimbursement Claim | Levels, Finance countersign for amounts above threshold |
| Loan Application | Levels, automated credit check |
| Exit / Resignation | Levels, notice period waiver approval |
| Payroll Approval | Finance Manager → CFO for disbursement |
| Salary Revision | HR → Management approval |
| Job Requisition | Department Head → HR Head → CEO |

---

## 19. Reports & Analytics Configuration

### 19.1 Standard HRMS Reports

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
| Form 24Q (Quarterly) | Quarterly | Finance, Compliance |
| Form 16 (Annual) | Annual | All employees |
| Gratuity Provision Report | Annual | Finance |
| Bonus Provision Report | Annual | Finance |
| Headcount by Department | On-demand | HR, Management |
| New Joiners Report | Monthly | HR |
| Exit / Resigned Employees Report | Monthly | HR |
| Employee Anniversary Report | Monthly | HR |
| Training Completion Report | Quarterly | HR, L&D |

### 19.2 Analytics Dashboards

| Dashboard | KPIs Displayed |
|---|---|
| HR Overview Dashboard | Total headcount, new joiners, exits, open positions |
| Payroll Dashboard | Total payroll cost, average CTC, month-over-month trend |
| Attendance Dashboard | Average attendance %, late comers, absenteeism rate |
| Leave Dashboard | Leave utilisation %, leave type distribution |
| Compliance Dashboard | PF/ESI/PT payment status, pending filings |
| Attrition Dashboard | Attrition %, department-wise, trend analysis |

---

## 20. HRMS Integration with Other Modules

### 20.1 HRMS ↔ Finance / Accounts

| Integration Point | Data Flow |
|---|---|
| Payroll Journal Entry | Monthly salary journal posted to GL accounts |
| Statutory Liability Booking | PF/ESI/PT accruals booked as liability |
| Gratuity Provision | Monthly provision entry to GL |
| Bonus Provision | Annual provision entry |
| Loan Disbursement | Employee loan amount debited from company accounts |
| Reimbursement Payment | Expense claims settled via accounts |
| Cost Centre Allocation | Payroll costs tagged to respective cost centres |

### 20.2 HRMS ↔ Payroll Engine

This is an internal integration (both are parts of Avy ERP HRMS), but key handshake points are:

| Handshake | Description |
|---|---|
| Attendance ↔ Payroll | Approved attendance data (present days, LOP days, OT hours) feeds into payroll |
| Leave ↔ Payroll | LOP days deducted; leave encashment amount added |
| Loan ↔ Payroll | EMI amounts auto-deducted in payroll |
| Reimbursements ↔ Payroll | Approved claims added to payslip |
| Salary Revision ↔ Payroll | Revised CTC effective date determines arrears |
| Employee Status ↔ Payroll | Exited employees excluded from next payroll run |

### 20.3 HRMS ↔ Production / Operations (for Manufacturing Companies)

| Integration Point | Description |
|---|---|
| Shift Master | Shared shift data drives both employee attendance and production planning |
| Employee to Machine Mapping | Operator assignment to machines for production tracking |
| Attendance at Plant Level | Plant-level attendance feeds into production OEE calculations |
| Holiday Calendar | Company holidays affect production scheduling and OEE planned time |
| Overtime Hours | OT hours logged in HRMS are cross-referenced with production records |

### 20.4 HRMS ↔ Biometric / Access Control Devices

| Integration | Configuration |
|---|---|
| ZKTeco / ESSL | Device IP, push SDK, employee enrollment via software |
| Smart Card / RFID | Card-to-employee mapping, reader IP config |
| Face Recognition | Camera setup, face model training, live comparison |
| GPS / Mobile App | Geo-fence coordinates from Branch setup, GPS tolerance setting |
| Fingerprint | Enrollment via device or software |
| Data Sync | Real-time push or scheduled pull; missing punch alerts |

### 20.5 HRMS ↔ Statutory Portals (External Integrations)

| Portal | Integration Type |
|---|---|
| EPFO Unified Portal | ECR file export for PF uploads; UAN management |
| ESIC Portal | Challan export; IP registration; Form 1 generation |
| TRACES / Income Tax | Form 24Q export; Form 16 generation |
| MCA / ROC | No direct integration; data used for filings |
| State PT Portals | PT challan export per state |
| DPIIT / MSME | No direct integration; data reference |

### 20.6 HRMS ↔ Communication Platforms

| Platform | Integration |
|---|---|
| Email (SMTP) | Payslip, Form 16, notifications via configured SMTP server |
| WhatsApp Business API | Salary alerts, leave status (optional) |
| SMS Gateway | OTP, salary credit SMS |
| Microsoft Teams / Slack | HR bot for leave balance queries, announcements (optional) |

### 20.7 HRMS ↔ Third-Party HRMS / ERP (Migration / Co-existence)

| Scenario | Description |
|---|---|
| Data Migration from Legacy HRMS | Import historical employee data, leave balances, payroll history |
| API Integration | REST API for real-time sync with external systems |
| Single Sign-On (SSO) | SAML / OAuth SSO with company's identity provider (Google Workspace, Azure AD) |

---

## 21. HRMS Go-Live Readiness Checklist

### Phase 1: Organisation Setup
- [ ] Department Master created and complete
- [ ] Designation Master created and complete
- [ ] Grade / Band Master configured
- [ ] Cost Centre Master linked to Finance
- [ ] Reporting hierarchy defined

### Phase 2: Employee Data
- [ ] All active employee records created
- [ ] Personal, contact, and employment details complete
- [ ] PAN, Aadhaar, UAN, bank details captured for all employees
- [ ] Nominee details added
- [ ] Profile photos uploaded (optional)

### Phase 3: Attendance
- [ ] Attendance capture method configured
- [ ] Biometric devices enrolled and synced (if applicable)
- [ ] Shift assignment completed for all employees
- [ ] Attendance rules configured (grace period, half-day threshold)
- [ ] Geo-fencing coordinates set for all branches

### Phase 4: Leave Management
- [ ] All leave types created and configured
- [ ] Holiday calendar published for current year
- [ ] Leave policies assigned to all employees/grades
- [ ] Opening leave balances entered for existing employees
- [ ] Approval workflow configured

### Phase 5: Payroll
- [ ] All salary components created
- [ ] Salary structures created per grade/designation
- [ ] Each employee's CTC entered and salary structure assigned
- [ ] Payroll run cycle confirmed
- [ ] Bank details verified for all employees
- [ ] PF/ESI/PT configurations verified

### Phase 6: Statutory Compliance
- [ ] PF registration and settings configured
- [ ] ESI settings verified (eligibility threshold, rates)
- [ ] PT slabs configured for all applicable states
- [ ] Gratuity and Bonus settings configured
- [ ] TDS regime defaults set
- [ ] Investment declaration window opened for employees

### Phase 7: ESS Portal
- [ ] ESS portal URL shared with all employees
- [ ] Login credentials distributed
- [ ] ESS features enabled as per policy
- [ ] Employee training on ESS completed

### Phase 8: Integration Verification
- [ ] Finance GL codes mapped to payroll components
- [ ] Biometric sync tested and verified
- [ ] Payroll bank file format tested with bank
- [ ] Statutory report formats verified
- [ ] Form 16 / 24Q test generation done

### Phase 9: First Payroll Run
- [ ] Test payroll run completed in staging
- [ ] Outputs verified (payslips, statutory amounts, bank totals)
- [ ] Finance sign-off obtained
- [ ] First live payroll processed
- [ ] Payslips distributed to employees
- [ ] Statutory payments initiated (PF/ESI challan, TDS)

### Phase 10: Post-Go-Live Monitoring
- [ ] Attendance sync monitored for first week
- [ ] Leave applications tested end-to-end
- [ ] Payroll accuracy verified after first live run
- [ ] Employee feedback on ESS collected
- [ ] Support escalation matrix configured

---

*Document End — Avy ERP HRMS Module Configuration Guide v1.0*  
*Maintained by Avyren Technologies — Product & HR-Tech Team*
