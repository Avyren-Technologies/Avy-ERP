# Company Admin & HRMS Module — Master Development Plan

> **Document Code:** AVY-DEV-PLAN-001
> **Product:** Avy ERP (Avyren Technologies)
> **Date:** March 19, 2026
> **Status:** Approved
> **Scope:** Company Admin Role + Full HRMS Module (9 Phases)

---

## Executive Summary

This document is the **master development plan** for building the Company Admin role and the complete HRMS module in Avy ERP. It covers 9 phases, from Company Admin core infrastructure through to Employee Offboarding & Full & Final Settlement.

The plan ensures seamless integration with the existing Super Admin codebase across all three platforms (Backend, Mobile App, Web App) while maintaining the established architecture patterns.

---

## Key Constraints

1. **Company Admin can Read/Update/Delete existing locations but CANNOT add new locations** — only Super Admin creates locations during tenant onboarding
2. **All new HRMS tables** go into the existing Prisma schema alongside Company, Tenant, User, Location
3. **All new tables are tenant-scoped** (companyId foreign key) — same pattern as existing Location, CompanyShift
4. **UI patterns** must match existing Super Admin screens exactly (same colors, components, layouts)
5. **HRMS inherits data** from onboarding (shifts, locations, contacts, fiscal config) — no duplication

---

## Architecture Decisions

### Backend
- New API routes: `/api/v1/company/*` (company-admin self-service), `/api/v1/hr/*`, `/api/v1/payroll/*`, `/api/v1/performance/*`
- All routes use existing `authMiddleware + tenantMiddleware + requirePermissions` chain
- Company Admin endpoints use `validateTenantAccess()` — users access only their own company
- Services follow existing class-based singleton pattern (e.g., `export const companyAdminService = new CompanyAdminService()`)
- Controllers use `asyncHandler` wrapper pattern

### Mobile App
- New feature folder: `src/features/company-admin/` with sub-folders per domain
- New API layer: `src/lib/api/company-admin.ts`, `src/lib/api/hr.ts`
- New query hooks: `src/features/company-admin/api/`
- Route files in `src/app/(app)/company/` for company-admin-specific screens
- Same UI atoms, colors, and layout patterns as super-admin screens

### Web App
- New feature folder: `src/features/company-admin/` with sub-folders per domain
- New routes under `/app/company/*` in `App.tsx`
- Same Tailwind styling, Lucide icons, and component patterns
- Sidebar sections updated with company-admin-specific navigation

---

## Phase Overview

| Phase | Name | Priority | Dependencies | Est. Tasks |
|-------|------|----------|--------------|------------|
| **Phase 1** | Company Admin Core Infrastructure | P0 | None | 14 tasks |
| **Phase 2** | HRMS — Org Structure & Employee Master | P1 | Phase 1 | 10 tasks |
| **Phase 3** | HRMS — Attendance & Leave Management | P1 | Phase 2 | 13 tasks |
| **Phase 4** | HRMS — Payroll Configuration | P2 | Phase 2 | 9 tasks |
| **Phase 5** | HRMS — Payroll Run & Statutory Operations | P2 | Phase 3, 4 | 9 tasks |
| **Phase 6** | HRMS — ESS Portal & Approval Workflows | P3 | Phase 3 | 6 tasks |
| **Phase 7** | HRMS — Performance Management | P3 | Phase 2 | 7 tasks |
| **Phase 8** | HRMS — Recruitment, Training & Advanced | P4 | Phase 2 | 7 tasks |
| **Phase 9** | HRMS — Offboarding & Full & Final | P4 | Phase 5 | 4 tasks |

---

## Phase 1: Company Admin Core Infrastructure

**Goal:** Company Admin can log in, navigate, manage company settings, users, and roles

**Detailed implementation plan:** See `2026-03-19-phase1-company-admin-core.md`

### Tasks
1.1. Company Admin Navigation & Layout (Mobile + Web)
1.2. Company Admin Dashboard — Enhanced with real API data
1.3. Company Profile Screen — View/edit own company (partial access)
1.4. Location Management — Edit/Delete existing locations only (NO create)
1.5. Shift & Time Management — CRUD shifts, day boundary, weekly offs
1.6. No Series Management — Configure document numbering
1.7. IOT Reason Management — Configure machine downtime reasons
1.8. System Controls — Toggle company-level operational controls
1.9. Key Contacts Management — Add/edit/remove contacts
1.10. Company-Scoped Audit Log — View tenant-scoped audit trail
1.11. Company Settings — Locale, date format, notifications, feature flags
1.12. User Management — List, create, edit, deactivate users within tenant
1.13. Role Management — Create custom roles, assign permissions
1.14. Feature Toggle Management — Per-user feature overrides

---

## Phase 2: HRMS — Org Structure & Employee Master

**Goal:** HR Admin can set up organisational hierarchy and manage employees

**Reference Doc:** AVY-HRMS-CFG-002, Sections 4–5

### Database Models (New)
- `Department` — name, code, headEmployeeId, parentDepartmentId, costCentreCode, status, companyId
- `Designation` — name, code, departmentId, gradeId, jobLevel, managerialFlag, probationDays, status, companyId
- `Grade` — code, name, ctcMin, ctcMax, hraPercent, pfTier, probationMonths, noticeDays, status, companyId
- `EmployeeType` — name, code, pfApplicable, esiApplicable, ptApplicable, gratuityEligible, bonusEligible, status, companyId
- `CostCentre` — code, name, departmentId, locationId, annualBudget, glAccountCode, companyId
- `Employee` — Full 6-tab model: personal info, professional details, salary/CTC, bank, documents, emergency contacts, companyId
- `EmployeeNominee` — employeeId, name, relation, dob, sharePercent, aadhaar, pan, address
- `EmployeeEducation` — employeeId, qualification, degree, institution, university, yearOfPassing, marks
- `EmployeePrevEmployment` — employeeId, employer, designation, lastCtc, joinDate, leaveDate, reason
- `EmployeeDocument` — employeeId, documentType, documentNumber, expiryDate, fileUrl
- `EmployeeTimeline` — employeeId, eventType, eventData, timestamp

### Tasks
2.1. Database Schema — HRMS Core Models (Prisma migration)
2.2. Department Master — Backend API + Mobile + Web CRUD
2.3. Designation Master — Backend API + Mobile + Web CRUD
2.4. Grade/Band Master — Backend API + Mobile + Web CRUD
2.5. Employee Type Master — Backend API + Mobile + Web CRUD with statutory flags
2.6. Cost Centre Master — Backend API + Mobile + Web CRUD
2.7. Employee Directory — Searchable list with filters (department, location, status, type)
2.8. Employee Profile — 6-Tab Smart Form (Personal, Professional, Salary, Bank, Documents, Emergency)
2.9. Employee Onboarding Checklist — Auto-generated tasks per department on new hire
2.10. Employee Timeline & Lifecycle Events — Auto-logged events

---

## Phase 3: HRMS — Attendance & Leave Management

**Goal:** Attendance tracking and leave workflows operational

**Reference Doc:** AVY-HRMS-CFG-002, Sections 6–7

### Database Models (New)
- `AttendanceRecord` — employeeId, date, shiftId, punchIn, punchOut, status (Present/Absent/HalfDay/Late/LOP), source, companyId
- `AttendanceOverride` — attendanceRecordId, issueType, correctedInTime, correctedOutTime, reason, approvedBy, status
- `LeaveType` — name, code, category, annualEntitlement, accrualFrequency, carryForward, encashment, applicableTypes, companyId
- `LeavePolicy` — leaveTypeId, assignmentLevel, assignmentId, overrides (JSON), companyId
- `LeaveBalance` — employeeId, leaveTypeId, openingBalance, accrued, taken, adjusted, balance, year
- `LeaveRequest` — employeeId, leaveTypeId, fromDate, toDate, days, halfDay, reason, status, approvedBy, companyId
- `HolidayCalendar` — name, date, type, branchIds, year, companyId
- `Roster` — name, pattern, weekOff1, weekOff2, applicableTypes, effectiveFrom, companyId
- `OvertimeRule` — eligibleTypes, rateMultiplier, threshold, monthlyCap, weeklyCap, autoInclude, approvalRequired, companyId

### Tasks
3.1. Database Schema — Attendance & Leave models
3.2. Holiday Calendar — CRUD holidays, branch-specific, clone year
3.3. Roster/Work Week Config — Define rosters, assign to employee types
3.4. Attendance Dashboard — Daily summary: present/absent/late/half-day by department
3.5. Attendance Rules Config — Grace period, half-day threshold, LOP rules
3.6. Attendance Override/Regularization — HR corrects with reason + approval
3.7. Overtime Rules — Eligible types, multiplier, caps, auto-payroll
3.8. Leave Type Master — CRUD with accrual, carry-forward, encashment rules
3.9. Leave Policy Assignment — Assign by company/department/grade/type
3.10. Leave Application & Approval — Apply, approve/reject, auto-escalation
3.11. Leave Balance Dashboard — Real-time balances, pro-rata calculation
3.12. Leave Override (HR) — Manual credit/debit with approval
3.13. Comp-Off Configuration — Accrual on worked holidays, validity, expiry

---

## Phase 4: HRMS — Payroll Configuration

**Goal:** Salary structures and statutory rules ready for payroll run

**Reference Doc:** AVY-HRMS-CFG-002, Sections 8–10

### Database Models (New)
- `SalaryComponent` — name, code, type (Earning/Deduction/EmployerContribution), calculationMethod, formula, taxable, exemptionSection, pfInclusion, esiInclusion, showOnPayslip, companyId
- `SalaryStructure` — name, code, applicableGrades, applicableDesignations, applicableTypes, components (JSON), ctcBasis, companyId
- `EmployeeSalary` — employeeId, structureId, annualCtc, components (JSON breakup), effectiveFrom, paymentMode
- `PFConfig` — employeeRate, employerRate, wageCeiling, excludedComponents, companyId
- `ESIConfig` — employeeRate, employerRate, wageCeiling, companyId
- `PTConfig` — state, slabs (JSON), frequency, registrationNumber, companyId
- `GratuityConfig` — formula, base, maxAmount, provisionMethod, companyId
- `BonusConfig` — wageCeiling, minBonus, maxBonus, eligibilityDays, companyId
- `LoanPolicy` — type, maxAmount, maxTenure, interestRate, emiCapPercent, eligibilityCriteria (JSON), companyId
- `LoanRecord` — employeeId, policyId, amount, tenure, emi, outstanding, status, companyId
- `TaxConfig` — regime (Old/New), slabs (JSON), declarationDeadline, companyId

### Tasks
4.1. Database Schema — Payroll models (Prisma migration)
4.2. Salary Component Master — CRUD with tax treatment toggles
4.3. Salary Structure Templates — Map components to grades/designations
4.4. PF/ESI/PT Rules Config — Pre-loaded rates, wage ceilings, state-wise PT slabs
4.5. Gratuity & Bonus Config — Applicability rules, calculation formulas
4.6. Bank Disbursement Config — Payment modes, bank file formats
4.7. Loan Policy Config — Types, limits, tenure, interest, EMI caps
4.8. Employee Salary Assignment — Assign CTC + structure, breakup preview
4.9. TDS & Tax Config — Old/New regime slabs, Form 12BB declarations

---

## Phase 5: HRMS — Payroll Run & Statutory Operations

**Goal:** Monthly payroll execution end-to-end

**Reference Doc:** AVY-HRMS-CFG-002, Sections 18, 28

### Database Models (New)
- `PayrollRun` — month, year, status (Draft/Locked/Computed/Approved/Disbursed), lockedBy, approvedBy, companyId
- `PayrollEntry` — payrollRunId, employeeId, grossEarnings, totalDeductions, netPay, components (JSON), workingDays, lopDays
- `Payslip` — payrollEntryId, employeeId, month, year, pdfUrl, emailedAt
- `StatutoryFiling` — type (PF_ECR/ESI/PT/TDS_24Q), month, year, status, filedAt, amount, companyId
- `SalaryHold` — employeeId, payrollRunId, reason, holdType, releasedAt
- `SalaryRevision` — employeeId, oldCtc, newCtc, effectiveDate, arrears, revisionLetterUrl, status
- `ArrearEntry` — employeeId, payrollRunId, components (JSON), fromMonth, toMonth, totalAmount

### Tasks
5.1. Database Schema — Payroll Run models
5.2. Payroll Run — 6-Step Wizard (Lock → Exceptions → Compute → Statutory → Approve → Disburse)
5.3. Payslip Generation — Auto-generate PDF, email dispatch
5.4. Salary Hold/Release — Hold specific employees with reason
5.5. Arrear Processing — Auto-compute on retrospective revision
5.6. Salary Revision Wizard — Individual + bulk with grade band validation
5.7. Statutory Compliance Dashboard — PF ECR, ESI challan, PT, TDS status
5.8. Form 16/24Q Generation — Quarterly TDS returns, annual certificates
5.9. Payroll Reports — Salary register, CTC statement, statutory summaries

---

## Phase 6: HRMS — ESS Portal & Approval Workflows

**Goal:** Employees and managers can self-serve

**Reference Doc:** AVY-HRMS-CFG-002, Sections 11, 13–14

### Database Models (New)
- `ESSConfig` — features (JSON toggles), loginMethod, passwordPolicy, sessionTimeout, mfaRequired, companyId
- `ApprovalWorkflow` — name, triggerEvent, steps (JSON: [{role, slaHours, autoEscalate}]), companyId
- `ApprovalRequest` — workflowId, requesterId, currentStep, status, data (JSON), companyId
- `NotificationRule` — triggerEvent, templateId, recipientRole, channel, companyId
- `NotificationTemplate` — name, subject, body (with tokens), channel, companyId
- `ITDeclaration` — employeeId, year, regime, declarations (JSON per section), status, companyId

### Tasks
6.1. ESS Portal Config — Enable/disable features per company
6.2. Employee ESS — Mobile screens: payslips, leave balance, apply leave, attendance, profile
6.3. Manager Self-Service (MSS) — Approve leaves, team attendance, OT approval
6.4. Approval Workflow Engine — Configurable multi-level chains with SLA + auto-escalation
6.5. Notification Engine — Email/SMS/push triggers for HR events
6.6. IT Declaration (Form 12BB) — Employee investment declarations for TDS

---

## Phase 7: HRMS — Performance Management

**Goal:** Appraisal cycles, goals, feedback, skill mapping

**Reference Doc:** AVY-HRMS-CFG-002, Section 21

### Database Models (New)
- `AppraisalCycle` — name, frequency, startDate, endDate, ratingScale, weightages (JSON), bellCurve (JSON), status, companyId
- `KRA` / `Goal` — employeeId, cycleId, title, description, weightage, targetValue, achievement, status
- `AppraisalEntry` — employeeId, cycleId, selfRating, managerRating, finalRating, status
- `Feedback360` — employeeId, cycleId, raterId, raterType, ratings (JSON), openText, anonymous
- `SkillLibrary` — name, category, companyId
- `SkillMapping` — employeeId, skillId, proficiencyLevel, requiredLevel
- `SuccessionPlan` — criticalRoleId, successorEmployeeId, readiness, developmentPlan

### Tasks
7.1. Database Schema — Performance models
7.2. Appraisal Cycle Config — Frequency, rating scale, weightages, bell curve
7.3. KRA/OKR Goal Setting — Company → Dept → Individual cascade
7.4. 360° Multi-Rater Feedback — Anonymous feedback with response tracking
7.5. Appraisal Rating & Calibration — Self → Manager → HR → Publish
7.6. Skill Mapping & Gap Analysis — Skill library, proficiency heatmap
7.7. Succession Planning — Critical roles, 9-box grid, bench strength

---

## Phase 8: HRMS — Recruitment, Training & Advanced

**Goal:** Complete hiring pipeline, LMS, and advanced features

**Reference Doc:** AVY-HRMS-CFG-002, Sections 16, 22–27

### Database Models (New)
- `JobRequisition` — title, departmentId, designationId, openings, budgetMin, budgetMax, status, companyId
- `Candidate` — name, email, phone, source, currentCtc, resumeUrl, stage, requisitionId
- `Interview` — candidateId, round, panelists, scheduledAt, feedbackRating, status
- `TrainingCatalogue` — name, type, mode, duration, linkedSkills, mandatory, cost, companyId
- `TrainingNomination` — employeeId, trainingId, status, completionDate, score, certificateUrl
- `AssetCategory` — name, depreciationRate, returnChecklist (JSON), companyId
- `Asset` — name, categoryId, serialNumber, purchaseDate, purchaseValue, condition, status, companyId
- `AssetAssignment` — assetId, employeeId, issueDate, returnDate, returnCondition
- `TravelPolicy` — gradeId, airClass, hotelCategory, dailyAllowance (JSON), companyId
- `ExpenseClaim` — employeeId, tripId, amount, receipts, status, approvedBy, companyId
- `HRLetterTemplate` — type, name, bodyTemplate (with tokens), companyId
- `HRLetter` — employeeId, templateId, effectiveDate, pdfUrl, eSignStatus
- `GrievanceCategory` — name, slaHours, autoEscalateTo, companyId
- `GrievanceCase` — employeeId, categoryId, description, anonymous, status, companyId
- `DisciplinaryAction` — employeeId, type (Warning/SCN/PIP/Suspension/Termination), charges, replyDueBy, status

### Tasks
8.1. Recruitment & ATS — Job requisitions, candidate pipeline (Kanban), interviews, offers
8.2. Training & LMS Config — Catalogue, mandatory training, budget tracking, certifications
8.3. Loan & Advance Processing — Application → approval → disbursement → EMI deduction
8.4. Asset Management — Asset master, issuance, return tracking, exit checklist
8.5. Travel & Expense Management — Claims, receipts, approval, payroll integration
8.6. HR Letters & Certificates — Template-based auto-generation (offer, appointment, relieving)
8.7. Grievance & Discipline — Categories, SLA, SCN, PIP, warnings

---

## Phase 9: HRMS — Offboarding & Full & Final Settlement

**Goal:** Complete exit management

**Reference Doc:** AVY-HRMS-CFG-002, Section 20

### Database Models (New)
- `ExitRequest` — employeeId, separationType, resignationDate, lastWorkingDay, noticePeriodWaiver, status, companyId
- `ExitClearance` — exitRequestId, department, items (JSON), clearedBy, clearedAt, status
- `ExitInterview` — exitRequestId, responses (JSON), conductedBy
- `FnFSettlement` — exitRequestId, employeeId, components (JSON: salary, leaveEncashment, gratuity, bonus, noticePay, loanRecovery, assetRecovery), totalAmount, status, payslipUrl

### Tasks
9.1. Resignation & Exit Workflow — Submit resignation, notice period, exit interview
9.2. Multi-Department Clearance Dashboard — IT/Admin/Finance/HR clearance tracking
9.3. Full & Final Settlement — Auto-compute all components by separation type
9.4. F&F by Separation Type — Resignation/Retirement/Termination/Layoff/Death treatment

---

## Company Admin vs Super Admin — Access Matrix

| Capability | Super Admin | Company Admin |
|-----------|-------------|---------------|
| View all companies | ✅ | ❌ (own only) |
| Create/delete company | ✅ | ❌ |
| Edit company identity | ✅ (full) | Partial (display name, logo, contacts) |
| Edit statutory info | ✅ | Read-only |
| **Add new locations** | **✅** | **❌ (BLOCKED)** |
| Edit/delete existing locations | ✅ | ✅ (own company) |
| Manage shifts | ✅ | ✅ (own company) |
| Manage No Series / IOT | ✅ | ✅ (own company) |
| Manage system controls | ✅ | ✅ (own company) |
| Create/manage users | ✅ (all companies) | ✅ (own company) |
| Create/manage roles | ✅ | ✅ (own company) |
| Feature toggles | ✅ | ✅ (own company) |
| View billing/subscription | ✅ (all) | Read-only (own) |
| Change company status | ✅ | ❌ |
| View audit logs | ✅ (all) | ✅ (own company) |
| HRMS: All modules | N/A | ✅ (own company) |

---

## Technology Reference

### Backend
- Runtime: Node.js + Express.js + TypeScript
- ORM: Prisma 5.7 with PostgreSQL
- Auth: JWT (HS256) with refresh tokens
- Validation: Zod
- Cache: Redis (ioredis)
- Queue: Bull

### Mobile App
- Expo SDK 54, React Native 0.81.5, TypeScript
- Expo Router 6 (file-based routing)
- NativeWind/Tailwind + StyleSheet.create()
- Zustand (global state), React Query (server state)
- MMKV (storage), @gorhom/bottom-sheet

### Web App
- React 19 + TypeScript + Vite 7.3
- React Router DOM 7.13
- Zustand + TanStack Query 5.90
- Tailwind CSS 3.4 + Lucide React icons
- React Hook Form + Zod

---

*Document maintained by Avyren Technologies — Product Team*
*Last updated: March 19, 2026*
