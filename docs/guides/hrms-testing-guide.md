# HRMS Feature Testing Guide

A comprehensive guide to testing every HRMS feature in Avy ERP, with step-by-step instructions for complex features like Payroll, Form 16, IT Declarations, and Statutory Compliance.

---

## Prerequisites

Before testing, ensure your seed data is in place:
```bash
pnpm seed:hrms --company-id <your-company-id> --months 3 --employees 25
```

Login as **Company Admin** (full access) or **HR Manager** (hr:* permissions).

---

## 1. Org Structure (HRMS > Org Structure)

### Departments
- **Screen**: `/app/company/hr/departments`
- **What to test**: View tree hierarchy, create sub-department, edit, deactivate
- **Seed data**: 9 departments (Executive, HR, Finance, Operations, Technology, Sales, Support, Admin, Quality)

### Designations
- **Screen**: `/app/company/hr/designations`
- **What to test**: List, create with job level, set managerial flag, probation days
- **Seed data**: 15 designations (CEO → Intern)

### Grades & Bands
- **Screen**: `/app/company/hr/grades`
- **What to test**: View CTC ranges, min/max bands, probation/notice periods
- **Seed data**: 5 grades (G1-G5, Entry to Leadership)

### Employee Types
- **Screen**: `/app/company/hr/employee-types`
- **What to test**: View statutory flags (PF applicable, ESI applicable), create custom type
- **Seed data**: 6 types (Permanent, Probation, Contract, Consultant, Apprentice, Trainee)

### Cost Centres
- **Screen**: `/app/company/hr/cost-centres`
- **What to test**: Link to departments, budget tracking
- **Seed data**: 8 cost centres

### Employee Directory
- **Screen**: `/app/company/hr/employees`
- **What to test**: Search, filter by dept/grade/status, create new employee (all 6 tabs: Personal, Professional, Salary, Bank, Documents, Statutory)
- **Seed data**: 28 employees with complete profiles

---

## 2. Attendance (HRMS > Attendance)

### Attendance Dashboard
- **Screen**: `/app/company/hr/attendance`
- **What to test**: Daily summary (present, absent, late, half-day), filter by date/department/location
- **Seed data**: ~1,533 attendance records across 3 months with realistic distribution (88% present, 4% late, 3% half-day, 2% absent, 2% on-leave, 1% overtime)

### Holiday Calendar
- **Screen**: `/app/company/hr/holidays`
- **What to test**: View yearly holidays, add/edit/delete, regional vs national
- **Seed data**: 15 holidays for 2026

### Rosters
- **Screen**: `/app/company/hr/rosters`
- **What to test**: Create shift patterns, assign to employees
- **Seed data**: Default rosters

### Attendance Overrides
- **Screen**: `/app/company/hr/attendance-overrides`
- **What to test**: Regularization requests, approve/reject
- **Seed data**: Created with attendance records

### Attendance Rules
- **Screen**: `/app/company/hr/attendance-rules`
- **What to test**: Grace period, full-day threshold hours, late marking rules, half-day rules
- **How to configure**: Set grace period (e.g., 15 min), full-day hours (8h), overtime threshold

### Overtime Rules
- **Screen**: `/app/company/hr/overtime-rules`
- **What to test**: OT multiplier (1.5x/2x), caps (max 4 hrs/day), auto-include in payroll
- **Seed data**: 18 overtime requests

---

## 3. Leave Management (HRMS > Leave)

### Leave Types
- **Screen**: `/app/company/hr/leave-types`
- **What to test**: View/edit annual entitlement, accrual frequency, carry-forward, encashment rules
- **Seed data**: 8 types (CL, SL, EL, ML, PL, BL, CO, LWP)

### Leave Policies
- **Screen**: `/app/company/hr/leave-policies`
- **What to test**: Override leave rules by department/designation/grade
- **Example**: "Engineering gets 15 EL instead of default 12"

### Leave Requests
- **Screen**: `/app/company/hr/leave-requests`
- **What to test**: View all requests, filter by status/type/employee, approve/reject
- **Seed data**: 34 requests (70% approved, 15% pending, 10% rejected, 5% cancelled)

### Leave Balances
- **Screen**: `/app/company/hr/leave-balances`
- **What to test**: View per-employee balances, opening/accrued/taken/adjusted/balance
- **Seed data**: 168 balance records (28 employees × 6 leave types)

---

## 4. Payroll Configuration (HRMS > Payroll & Compliance)

### Salary Components
- **Screen**: `/app/company/hr/salary-components`
- **What to test**: View 13 default components, edit calculation method, create custom component
- **Key components**:
  - **Earnings**: Basic (40% of Gross), HRA (50% of Basic), DA (10% of Basic), Conveyance (Fixed), Medical (Fixed), Special Allowance (Balance)
  - **Deductions**: PF Employee (12% of Basic), ESI Employee (0.75% of Gross), PT (Fixed), TDS (Formula)
  - **Employer**: PF Employer (12% of Basic), ESI Employer (3.25% of Gross)

### Salary Structures
- **Screen**: `/app/company/hr/salary-structures`
- **What to test**: Create structure with component mix, assign to grades/designations
- **Seed data**: 1 structure (Standard CTC)

### Employee Salary
- **Screen**: `/app/company/hr/employee-salary`
- **What to test**: View current salaries, assign new salary, revision history
- **Seed data**: 28 salary assignments

### Statutory Config
- **Screen**: `/app/company/hr/statutory-config`
- **What to test**: Configure PF, ESI, PT rates and wage ceilings

#### PF (Provident Fund)
- **Employee rate**: 12% of Basic (capped at Basic from 15000 wage ceiling)
- **Employer EPF**: 3.67% of Basic
- **Employer EPS**: 8.33% of Basic
- **Employer EDLI**: 0.5% of Basic
- **Wage ceiling**: Rs. 15,000 — PF calculated on min(Basic, 15000)
- **VPF**: Optional voluntary contribution above 12%

#### ESI (Employee State Insurance)
- **Employee rate**: 0.75% of Gross
- **Employer rate**: 3.25% of Gross
- **Wage ceiling**: Rs. 21,000 — ESI only if monthly gross < 21000
- **Note**: High-salary employees are ESI-exempt

#### PT (Professional Tax)
- **State-wise slabs**: e.g., Karnataka: 0-15000=Nil, 15001-25000=Rs.150, 25001+=Rs.200
- **Monthly deduction** from salary

#### Gratuity
- **Standard formula**: (15 × Last Drawn Basic+DA × Years of Service) / 26
- **Minimum service**: 5 years
- **When used**: Only during F&F settlement (employee exit)
- **Custom formula**: Company can define higher multiplier than statutory

#### Bonus
- **Statutory range**: 8.33% to 20% of Basic
- **Wage ceiling**: Rs. 21,000
- **Calculation period**: April-March (FY)
- **When used**: During annual bonus batch run

### Tax & TDS
- **Screen**: `/app/company/hr/tax-config`
- **What to test**: Old vs New regime slabs, surcharge rates, cess (4%)

#### How TDS Works
1. System estimates annual taxable income from salary components
2. Applies tax slab rates (old or new regime based on employee's choice)
3. Deducts monthly TDS = annual tax / 12
4. IT Declarations (Section 80C, 80D, HRA) reduce taxable income

**New Regime Slabs (FY 2025-26)**:
| Income Range | Rate |
|-------------|------|
| 0 - 4,00,000 | Nil |
| 4,00,001 - 8,00,000 | 5% |
| 8,00,001 - 12,00,000 | 10% |
| 12,00,001 - 16,00,000 | 15% |
| 16,00,001 - 20,00,000 | 20% |
| 20,00,001 - 24,00,000 | 25% |
| 24,00,001+ | 30% |
+ 4% Health & Education Cess on total tax

### Bank Config
- **Screen**: `/app/company/hr/bank-config`
- **What to test**: Company's bank account for salary disbursement (NEFT/RTGS/IMPS)

### Loan Policies
- **Screen**: `/app/company/hr/loan-policies`
- **What to test**: View/create loan types (Personal, Salary Advance, Emergency, Education, Vehicle)
- **Seed data**: 5 policies with interest rates and max amounts

### Loans
- **Screen**: `/app/company/hr/loans`
- **What to test**: Active loans, EMI schedule, disbursement status
- **Seed data**: 7 loan records (ACTIVE, CLOSED, PENDING)

---

## 5. Payroll Operations (HRMS > Payroll Operations)

### Payroll Runs — THE MOST IMPORTANT FEATURE
- **Screen**: `/app/company/hr/payroll-runs`
- **Seed data**: 3 runs (Jan=DISBURSED, Feb=APPROVED, Mar=COMPUTED)

#### How Payroll Processing Works (6 Steps)

**Step 1: Create Payroll Run**
- Click "New Payroll Run"
- Select month/year
- Status: DRAFT

**Step 2: Lock Attendance**
- System counts attendance for the month:
  - Present days, absent days, late days, half days
  - LOP (Loss of Pay) days = absences not covered by leave
- Checks for pending attendance overrides
- Status: ATTENDANCE_LOCKED

**Step 3: Review Exceptions**
- Shows edge cases:
  - New joiners (joined mid-month → pro-rate salary)
  - Exiting employees (last working day in this month)
  - Missing attendance data
  - Employees on salary hold
- Status: EXCEPTIONS_REVIEWED

**Step 4: Compute Salaries**
- For each employee, calculates:
  - **Gross Earnings**: Basic + HRA + DA + Allowances (pro-rated for LOP days)
  - **Statutory Deductions**: PF (12% of Basic, max 15000 ceiling), ESI (0.75% if eligible), PT (state slab)
  - **TDS**: Annual tax estimate / 12, adjusted for IT declarations
  - **Other Deductions**: Loan EMIs, salary advances, holds
  - **Net Pay**: Gross - All Deductions
- Status: SALARIES_COMPUTED

**Step 5: Approve**
- Review computed amounts
- Approve for disbursement
- Status: APPROVED

**Step 6: Disburse / Finalize**
- Generate payslips
- Process bank transfer (if integrated)
- Status: DISBURSED / FINALIZED

#### Testing Payroll
1. Navigate to the March 2026 run (COMPUTED status)
2. Review the entries — each employee should show:
   - Gross: matches their CTC/12
   - PF: 12% of Basic
   - ESI: 0.75% of Gross (only if gross < 21000)
   - PT: Rs. 200 (Karnataka)
   - TDS: varies by income
   - Net: Gross - All Deductions
3. Approve the run → status changes to APPROVED
4. Finalize → payslips generated

### Payslips
- **Screen**: `/app/company/hr/payslips`
- **What to test**: View individual payslips, download, filter by month/employee
- **Seed data**: 42 payslips (21 for Jan + 21 for Feb)

### Salary Holds
- **Screen**: `/app/company/hr/salary-holds`
- **What to test**: Place full/partial hold on an employee's salary
- **When used**: During investigation, employee dispute, etc.

### Salary Revisions
- **Screen**: `/app/company/hr/salary-revisions`
- **What to test**: Revise an employee's CTC with effective date
- **Important**: If effective date is in the past → system computes arrears

### Bonus Batches
- **Screen**: `/app/company/hr/bonus-batches`
- **What to test**: Create bonus batch (PERFORMANCE, FESTIVE, SPOT), assign amounts, process

### Form 16 & 24Q
- **Screen**: `/app/company/hr/form-16`

#### What is Form 16?
Form 16 is a **TDS certificate** issued by the employer to the employee. It shows:
- Part A: TDS deducted and deposited with the government (quarterly, from 24Q)
- Part B: Detailed salary breakup, deductions claimed, tax computation

#### What is Form 24Q?
Form 24Q is the **quarterly TDS return** filed by the employer with the government:
- Q1: April-June
- Q2: July-September
- Q3: October-December
- Q4: January-March

#### How to Test
1. You need **at least 1 full quarter of payroll data** (Jan-Mar seeded)
2. Navigate to Form 16 screen → should show employees with TDS deducted
3. Generate Form 16 for an employee → downloads Part B with salary and tax details

**Prerequisite**: Payroll runs must be FINALIZED for the period, with TDS calculated.

### Statutory Filings
- **Screen**: `/app/company/hr/statutory-filings`
- **What to test**: View PF ECR, ESI Challan, PT, TDS 24Q filings
- **Seed data**: 10 filing records (monthly PF/ESI/PT + quarterly TDS)

---

## 6. IT Declarations (ESS / HR Admin)

### What are IT Declarations?
Employees declare their tax-saving investments to **reduce TDS deduction**:

| Section | What | Max Limit |
|---------|------|-----------|
| **80C** | PPF, ELSS, NSC, Life Insurance, Tuition Fees, Home Loan Principal | Rs. 1,50,000 |
| **80D** | Health Insurance Premium (self/family/parents) | Rs. 25,000-50,000 |
| **80E** | Education Loan Interest | No limit |
| **HRA** | House Rent Allowance exemption | Based on formula |
| **LTA** | Leave Travel Allowance | Actual travel cost |
| **80G** | Donations to approved charities | 50-100% of donation |

### How IT Declarations Work
1. Employee submits declaration at start of FY (April)
2. HR reviews and approves
3. System reduces taxable income → lower TDS per month
4. At year-end, employee submits proofs (receipts, statements)
5. If proofs < declarations → TDS adjusted in March payroll

### How to Test
- **ESS Screen**: `/app/company/hr/it-declarations` (employee submits)
- **HR Screen**: `/app/company/hr/it-declarations` (HR reviews all)
- **Seed data**: 7 IT declarations

1. Login as employee → go to IT Declarations
2. Submit a declaration:
   - Section 80C: PPF Rs. 50,000 + ELSS Rs. 30,000
   - Section 80D: Health Insurance Rs. 25,000
3. Login as HR → view all declarations → approve/reject
4. Approved declarations reduce TDS in next payroll computation

---

## 7. Performance (HRMS > Performance)

### Appraisal Cycles
- **Screen**: `/app/company/hr/appraisal-cycles`
- **What to test**: Create cycle, set rating scale, bell curve, mid-year review
- **Seed data**: 1 cycle (Annual Review FY 2025-26, IN_PROGRESS)

### Goals & OKRs
- **Screen**: `/app/company/hr/goals`
- **What to test**: Create company/dept/individual goals, cascading, weight assignment
- **Seed data**: 86 goals across employees

### 360 Feedback
- **Screen**: `/app/company/hr/feedback-360`
- **What to test**: Multi-rater feedback (peer, subordinate, cross-function)
- **Seed data**: 10 feedback records

### Skills & Mapping
- **Screen**: `/app/company/hr/skills`
- **What to test**: Skill library, assign skills to employees, current vs required level
- **Seed data**: 10 skills, 83 skill mappings

### Succession Planning
- **Screen**: `/app/company/hr/succession`
- **What to test**: Identify critical roles, map successors, readiness assessment
- **Seed data**: 3 succession plans

---

## 8. Recruitment & Training

### Job Requisitions
- **Screen**: `/app/company/hr/requisitions`
- **Seed data**: 4 requisitions (OPEN, INTERVIEWING, FILLED, CANCELLED)

### Candidates
- **Screen**: `/app/company/hr/candidates`
- **Seed data**: 15 candidates across requisitions

### Training Catalogue
- **Screen**: `/app/company/hr/training`
- **Seed data**: 6 courses (Technical, Compliance, Soft Skills)

### Training Nominations
- **Screen**: `/app/company/hr/training-nominations`
- **Seed data**: 15 nominations

---

## 9. Advanced HR

### Asset Management
- **Screen**: `/app/company/hr/assets`
- **What to test**: View assets, assign/return, track condition
- **Seed data**: 25 assets, 21 assignments

### Expense Claims
- **Screen**: `/app/company/hr/expenses`
- **What to test**: Create claim with line items, approve/reject, reimbursement
- **Seed data**: 15 claims with 43 line items

### HR Letters
- **Screen**: `/app/company/hr/hr-letters`
- **What to test**: Generate offer/appointment/confirmation letters from templates
- **Seed data**: 5 templates, 13 generated letters

### Grievances
- **Screen**: `/app/company/hr/grievances`
- **Seed data**: 5 cases (OPEN, INVESTIGATING, RESOLVED, CLOSED)

### Disciplinary Actions
- **Screen**: `/app/company/hr/disciplinary`
- **Seed data**: 3 actions

### Policy Documents
- **Screen**: `/app/company/hr/policy-documents`
- **Seed data**: 8 policies (Leave, Code of Conduct, WFH, POSH, etc.)

---

## 10. ESS & Workflows (HRMS > ESS Config)

### ESS Config
- **Screen**: `/app/company/hr/ess-config`
- **What to test**: Toggle ON/OFF for each ESS feature (30+ toggles)
- **Impact**: Toggling OFF hides the feature from employee sidebar

### Approval Workflows
- **Screen**: `/app/company/hr/approval-workflows`
- **What to test**: Configure multi-step approval chains, SLA hours, auto-escalation
- **Default workflows**: Leave, Attendance, Overtime, Expense, Loan

### Notification Templates
- **Screen**: `/app/company/hr/notification-templates`
- **What to test**: Edit email/SMS templates with token placeholders

---

## 11. Exit & Offboarding (HRMS > Exit)

### Exit Requests
- **Screen**: `/app/company/hr/exit-requests`
- **What to test**: Submit resignation, separation types (RESIGNATION, TERMINATION, RETIREMENT)

### Clearance Dashboard
- **Screen**: `/app/company/hr/clearance-dashboard`
- **What to test**: Department-wise handover checklist (IT assets, finance, admin)

### F&F Settlement
- **Screen**: `/app/company/hr/fnf-settlement`
- **What to test**: Calculate final settlement:
  - Remaining salary (pro-rated)
  - Leave encashment (unused EL × daily rate)
  - Gratuity (if 5+ years service)
  - Bonus (pro-rated)
  - Loan recovery (outstanding balance)
  - TDS on settlement
  - Net payable

---

## 12. Analytics (HRMS > Analytics)

### Analytics Hub
- **Screen**: `/app/company/hr/analytics`
- **Seed data**: Daily employee + attendance analytics, monthly payroll + attrition metrics

### Key Dashboards
| Dashboard | What it shows |
|-----------|-------------|
| Executive Overview | Total headcount, joiners, leavers, payroll cost |
| Workforce Analytics | Department/grade/gender distribution, tenure bands |
| Attendance & Productivity | Present/absent/late trends, department comparison |
| Payroll & Cost | Gross/net trends, component breakdown, CTC bands |
| Attrition & Retention | Attrition rate, exit reasons, department hotspots |
| Compliance & Risk | PF/ESI filing status, pending statutory obligations |

---

## 13. Self-Service (Employee View)

Login as a regular employee (use any seeded employee's email with password `Password@123`):

| Screen | What to test |
|--------|-------------|
| My Profile | View/edit personal details |
| My Payslips | View monthly payslips, download |
| My Leave | Apply leave, view balance, cancel request |
| My Attendance | View daily punch records, regularize |
| Shift Check-In | Punch in/out with geo-tagging |
| Holiday Calendar | View upcoming holidays |
| My Goals | View assigned goals, update progress |
| IT Declarations | Submit tax-saving declarations |
| My Expenses | Submit expense claims |
| My Loans | View active loans, EMI schedule |
| My Assets | View assigned assets |
| My Training | View nominated training, mark completion |

---

## Quick Reference: Payroll Calculation Formula

```
Monthly Gross = Annual CTC / 12

Earnings:
  Basic         = 40% of Gross
  HRA           = 50% of Basic
  DA            = 10% of Basic
  Conveyance    = Fixed (Rs. 1,600)
  Medical       = Fixed (Rs. 1,250)
  Special Allow = Gross - (Basic + HRA + DA + Conv + Med)

Deductions:
  PF (Employee)  = 12% of min(Basic, Rs. 15,000)
  ESI (Employee) = 0.75% of Gross (only if Gross < Rs. 21,000)
  PT             = State slab (Karnataka: Rs. 200 for > Rs. 25,000)
  TDS            = (Annual Tax / 12), based on chosen regime

Employer Cost (not deducted from employee):
  PF (Employer)  = 12% of min(Basic, Rs. 15,000)
  ESI (Employer) = 3.25% of Gross (only if Gross < Rs. 21,000)

Net Pay = Gross - (PF_EE + ESI_EE + PT + TDS + Loan EMI)
CTC = Gross + PF_ER + ESI_ER
```
