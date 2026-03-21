# Avy ERP — Company Admin & HRMS Implementation Checklist

> **Date:** March 20, 2026
> **Status:** All 9 Phases Completed + Gap Fixes Applied
> **Reference:** AVY-HRMS-CFG-002 (HRMS Module Configuration Guide v2.1)
> **Last Updated:** March 20, 2026 (v2.0 — post gap fixes)

---

## Summary

| Metric | Count |
|--------|-------|
| **Phases completed** | 9 / 9 + Gap Fixes |
| **Prisma models added** | 79 models + ~52 enums |
| **Backend API endpoints** | ~385+ |
| **Mobile screens** | ~113 |
| **Web screens** | ~111 |
| **Total new files** | ~430+ across 3 codebases |
| **TypeScript errors** | 0 |

---

## Phase 1: Company Admin Core Infrastructure

| # | Feature | Backend | Mobile | Web | Status |
|---|---------|---------|--------|-----|--------|
| 1.1 | Company Admin Navigation & Layout | — | ✅ | ✅ | Done |
| 1.2 | Company Admin Dashboard (real API) | ✅ | ✅ | ✅ | Done |
| 1.3 | Company Profile (view/edit) | ✅ | ✅ | ✅ | Done |
| 1.4 | Location Management (edit/delete only, NO create) | ✅ | ✅ | ✅ | Done |
| 1.5 | Shift & Time Management | ✅ | ✅ | ✅ | Done |
| 1.6 | No Series Management | ✅ | ✅ | ✅ | Done |
| 1.7 | IOT Reason Management | ✅ | ✅ | ✅ | Done |
| 1.8 | System Controls | ✅ | ✅ | ✅ | Done |
| 1.9 | Key Contacts Management | ✅ | ✅ | ✅ | Done |
| 1.10 | Company-Scoped Audit Log | ✅ | ✅ | ✅ | Done |
| 1.11 | Company Settings | ✅ | ✅ | ✅ | Done |
| 1.12 | User Management | ✅ | ✅ | ✅ | Done |
| 1.13 | Role Management (via /rbac) | ✅ | ✅ | ✅ | Done |
| 1.14 | Feature Toggle Management | ✅ | ✅ | ✅ | Done |

---

## Phase 2: HRMS — Org Structure & Employee Master
**Reference:** AVY-HRMS-CFG-002, Sections 4–5

| # | Feature | Spec Section | Backend | Mobile | Web | Status |
|---|---------|-------------|---------|--------|-----|--------|
| 2.1 | Department Master | 4.1 | ✅ | ✅ | ✅ | Done |
| 2.2 | Designation / Job Title Master | 4.2 | ✅ | ✅ | ✅ | Done |
| 2.3 | Grade / Band / Level Master | 4.3 | ✅ | ✅ | ✅ | Done |
| 2.4 | Employee Type Master (statutory flags) | 4.4 | ✅ | ✅ | ✅ | Done |
| 2.5 | Cost Centre Master | 4.6 | ✅ | ✅ | ✅ | Done |
| 2.6 | Employee Directory (searchable, filtered) | 5.x | ✅ | ✅ | ✅ | Done |
| 2.7 | Employee Profile — 6-Tab Form | 5.2–5.8 | ✅ | ✅ | ✅ | Done |
| 2.8 | Employee Timeline & Lifecycle | 5.10 | ✅ | ✅ | ✅ | Done |
| 2.9 | Reporting Structure / Hierarchy | 4.5 | ✅ Partial | — | — | Self-relations built (reportingManager, functionalManager). Visual org chart not implemented. |
| 2.10 | Work Location Categories | 4.7 | ✅ | — | — | WorkType enum (ON_SITE/REMOTE/HYBRID) in Employee model |
| 2.11 | **Employee Transfer** (Gap Fix) | 17.5 | ✅ | ✅ | ✅ | **NEW** — Full transfer module: request → approve → apply. Dept/designation/location/manager changes. Future-dated support. Auto-letter generation. Workflow integration. |
| 2.12 | **Employee Promotion** (Gap Fix) | 17.5 | ✅ | ✅ | ✅ | **NEW** — Full promotion module: request → approve → apply. Designation/grade/CTC changes. Auto-increment %, arrears on backdated. Linked to appraisal. Workflow integration. |
| 2.13 | Production Incentive Config | 4.8 | ❌ | ❌ | ❌ | Deferred — requires Production module integration |
| 2.14 | Employee Custom Fields | 5.9 | ❌ | ❌ | ❌ | Deferred — dynamic field system needs separate design |
| 2.15 | Employee Onboarding Checklist | 5.4 Tab 6 | ✅ Partial | — | — | Timeline event on creation. Full task-based checklist deferred. |

---

## Phase 3: HRMS — Attendance & Leave Management
**Reference:** AVY-HRMS-CFG-002, Sections 6–7

| # | Feature | Spec Section | Backend | Mobile | Web | Status |
|---|---------|-------------|---------|--------|-----|--------|
| 3.1 | Attendance Record CRUD | 6.x | ✅ | ✅ | ✅ | Done |
| 3.2 | Attendance Dashboard (summary) | 6.x | ✅ | ✅ | ✅ | Done |
| 3.3 | Attendance Rules Config | 6.8 | ✅ | ✅ | ✅ | Done |
| 3.4 | Attendance Override/Regularization | 6.x | ✅ | ✅ | ✅ | Done |
| 3.5 | Holiday Calendar (CRUD + clone year) | 6.6 | ✅ | ✅ | ✅ | Done |
| 3.6 | Roster / Work Week Config | 6.5 | ✅ | ✅ | ✅ | Done |
| 3.7 | Overtime Rules Config | 6.7 | ✅ | ✅ | ✅ | Done |
| 3.8 | Shift Master Config | 6.4 | ✅ | ✅ | ✅ | Done (inherited from Phase 1 shift management) |
| 3.9 | Leave Type Master | 7.1–7.2 | ✅ | ✅ | ✅ | Done (with accrual, carry-forward, encashment, sandwich rules) |
| 3.10 | Leave Policy Assignment | 7.4 | ✅ | ✅ | ✅ | Done (multi-level: company/dept/grade/type/individual) |
| 3.11 | Leave Application & Approval | 7.5 | ✅ | ✅ | ✅ | Done (apply, approve, reject, cancel with balance management) |
| 3.12 | Leave Balance Dashboard | 7.6 | ✅ | ✅ | ✅ | Done (with adjust/initialize, pro-rata) |
| 3.13 | Comp-Off Configuration | 7.7 | ✅ | ✅ | ✅ | Done (as COMPENSATORY leave category) |
| 3.14 | Biometric Device Config | 6.2 | ❌ | ❌ | ❌ | Deferred — requires hardware integration |
| 3.15 | Geo-Fence Zone Config | 6.3 | ✅ Partial | — | — | Location model has geo fields. Real maps not integrated. |
| 3.16 | Face Recognition Attendance | 6.1 | ❌ | ❌ | ❌ | Deferred — requires camera integration |
| 3.17 | Mobile GPS Punch | 6.1 | ❌ | ❌ | ❌ | Deferred — requires geolocation + background service |

---

## Phase 4: HRMS — Payroll Configuration
**Reference:** AVY-HRMS-CFG-002, Sections 8–10

| # | Feature | Spec Section | Backend | Mobile | Web | Status |
|---|---------|-------------|---------|--------|-----|--------|
| 4.1 | Salary Component Master | 8.1–8.2 | ✅ | ✅ | ✅ | Done |
| 4.2 | Salary Structure Templates | 8.4 | ✅ | ✅ | ✅ | Done |
| 4.3 | Employee Salary Assignment | 8.x | ✅ | ✅ | ✅ | Done (auto-breakup from structure) |
| 4.4 | PF Configuration | 8.3, 9.1 | ✅ | ✅ | ✅ | Done |
| 4.5 | ESI Configuration | 8.3, 9.2 | ✅ | ✅ | ✅ | Done |
| 4.6 | PT Configuration (multi-state) | 9.3 | ✅ | ✅ | ✅ | Done |
| 4.7 | Gratuity Configuration | 9.4 | ✅ | ✅ | ✅ | Done |
| 4.8 | Bonus Configuration | 9.5 | ✅ | ✅ | ✅ | Done |
| 4.9 | LWF Configuration (multi-state) | 9.6 | ✅ | ✅ | ✅ | Done |
| 4.10 | Bank Disbursement Config | 8.7 | ✅ | ✅ | ✅ | Done |
| 4.11 | Loan Policy Config | 8.8 | ✅ | ✅ | ✅ | Done |
| 4.12 | Loan Records (apply, approve, disburse) | 8.8 | ✅ | ✅ | ✅ | Done |
| 4.13 | TDS & Income Tax Config (slabs) | 10.1–10.2 | ✅ | ✅ | ✅ | Done (Old + New regime, FY 2025-26 defaults) |
| 4.14 | Payroll Run Config (lock, LOP rate, rounding) | 8.5 | ✅ | — | — | Configured via payroll run service |
| 4.15 | Salary Revision Config | 8.6 | ✅ | ✅ | ✅ | Done |
| 4.16 | Reimbursement Types | 8.9 | ✅ Partial | — | — | Via ExpenseClaim in Phase 8 |

---

## Phase 5: HRMS — Payroll Run & Statutory Operations
**Reference:** AVY-HRMS-CFG-002, Section 18, 28

| # | Feature | Spec Section | Backend | Mobile | Web | Status |
|---|---------|-------------|---------|--------|-----|--------|
| 5.1 | Payroll Run — 6-Step Wizard | 18.1 | ✅ | ✅ | ✅ | Done (Lock → Exceptions → Compute → Statutory → Approve → Disburse) |
| 5.2 | Payslip Generation | 18.1 Step 6 | ✅ | ✅ | ✅ | Done (records + PDF placeholder) |
| 5.3 | Salary Hold / Release | 18.2 | ✅ | ✅ | ✅ | Done (Full + Partial holds) |
| 5.4 | Arrear Processing | 18.3 | ✅ | ✅ | ✅ | Done (month-by-month from revision) |
| 5.5 | Salary Revision Wizard | 18.4 | ✅ | ✅ | ✅ | Done (individual, with arrears) |
| 5.6 | Statutory Compliance Dashboard | 28.1–28.2 | ✅ | ✅ | ✅ | Done (filed %, due, overdue) |
| 5.7 | Statutory Filing Management | 9.7 | ✅ | ✅ | ✅ | Done (PF ECR, ESI, PT, TDS, LWF) |
| 5.8 | Payroll Reports | 30.1 | ✅ | ✅ | ✅ | Done (salary register, bank file, PF ECR, ESI/PT challan, variance) |
| 5.9 | Form 16 / 24Q Generation | 10.5 | ✅ Partial | — | — | Filing record exists. Actual PDF/XML generation deferred. |
| 5.10 | Bulk Increment Upload | 18.4 | ❌ | ❌ | ❌ | Deferred — Excel import feature |
| 5.11 | Bank File Auto-Push | 8.7 | ❌ | ❌ | ❌ | Deferred — requires banking API integration |

---

## Phase 6: HRMS — ESS Portal & Approval Workflows
**Reference:** AVY-HRMS-CFG-002, Sections 11–14

| # | Feature | Spec Section | Backend | Mobile | Web | Status |
|---|---------|-------------|---------|--------|-----|--------|
| 6.1 | ESS Portal Config | 11.1–11.2 | ✅ | ✅ | ✅ | Done (20+ feature toggles) |
| 6.2 | Employee Self-Service — Profile | 11.2 | ✅ | ✅ | ✅ | Done |
| 6.3 | Employee Self-Service — Payslips | 11.2 | ✅ | ✅ | ✅ | Done |
| 6.4 | Employee Self-Service — Leave | 11.2 | ✅ | ✅ | ✅ | Done (apply + balance view) |
| 6.5 | Employee Self-Service — Attendance | 11.2 | ✅ | ✅ | ✅ | Done (view + regularize) |
| 6.6 | Manager Self-Service (MSS) | 11.3 | ✅ | ✅ | ✅ | Done (team, approvals, attendance, leave calendar) |
| 6.7 | Approval Workflow Engine | 13.1–13.2 | ✅ | ✅ | ✅ | Done (multi-step, SLA, auto-escalation) |
| 6.8 | Approval Request Queue | 13.x | ✅ | ✅ | ✅ | Done (pending for me + all requests + delegate visibility) |
| 6.9 | Notification Templates | 14.2 | ✅ | ✅ | ✅ | Done (with token system) |
| 6.10 | Notification Rules | 14.1–14.3 | ✅ | ✅ | ✅ | Done (event → template → role → channel) |
| 6.11 | IT Declaration (Form 12BB) | 10.3 | ✅ | ✅ | ✅ | Done (all sections: 80C/D/E/G/GG/TTA, HRA, LTA, Home Loan) |
| 6.12 | **Workflow Wired to All 12 Modules** (Gap Fix) | 13.1 | ✅ | — | — | **NEW** — Leave, Attendance, Loan, Expense, Exit, Payroll, Revision, Requisition, Asset, Transfer, Promotion all create ApprovalRequests when workflows configured |
| 6.13 | **SLA Enforcement Cron** (Gap Fix) | 13.2 | ✅ | — | — | **NEW** — Background job every 15min: auto-escalate, auto-approve, or auto-reject on SLA breach |
| 6.14 | **Manager Delegation / Proxy** (Gap Fix) | 13.1 | ✅ | ✅ | ✅ | **NEW** — ManagerDelegate model, delegate CRUD, pending approvals include delegated requests |
| 6.15 | AI HR Chatbot | 11.4 | ❌ | ❌ | ❌ | Deferred — requires NLP/AI integration |
| 6.16 | SSO Integration (Google/Microsoft) | 11.1 | ❌ | ❌ | ❌ | Deferred — requires OAuth setup |
| 6.17 | Email/SMS/WhatsApp Dispatch | 14.1 | ✅ Partial | — | — | Rules engine built. Actual dispatch via email/SMS/WhatsApp providers not connected. |

---

## Phase 7: HRMS — Performance Management
**Reference:** AVY-HRMS-CFG-002, Section 21

| # | Feature | Spec Section | Backend | Mobile | Web | Status |
|---|---------|-------------|---------|--------|-----|--------|
| 7.1 | Appraisal Cycle Config | 21.1 | ✅ | ✅ | ✅ | Done (frequency, scale, weightage, bell curve, lifecycle) |
| 7.2 | KRA / OKR Goal Setting | 21.2 | ✅ | ✅ | ✅ | Done (company → dept → individual cascade) |
| 7.3 | 360° Multi-Rater Feedback | 21.3 | ✅ | ✅ | ✅ | Done (anonymous, suppression <3 responses) |
| 7.4 | Appraisal Rating & Calibration | 21.4 | ✅ | ✅ | ✅ | Done (self → manager → publish, bell curve) |
| 7.5 | Skill Mapping & Gap Analysis | 21.5 | ✅ | ✅ | ✅ | Done (library, proficiency 1-5, gap heatmap) |
| 7.6 | Succession Planning | 21.7 | ✅ | ✅ | ✅ | Done (9-box grid, readiness, bench strength) |
| 7.7 | Performance Dashboard | 21.x | ✅ | ✅ | ✅ | Done |
| 7.8 | Employee Engagement (Pulse Surveys, eNPS) | 21.8 | ❌ | ❌ | ❌ | Deferred — separate survey engine needed |
| 7.9 | Industry Preset Templates | 21.9 | ❌ | ❌ | ❌ | Deferred — seed data/import feature |
| 7.10 | OEE / Production KPI Auto-Pull | 21.1 | ❌ | ❌ | ❌ | Deferred — requires Production module integration |
| 7.11 | HiPo Development Programme | 21.7 | ❌ | ❌ | ❌ | Deferred — succession model has readiness field but no development programme tracking |

---

## Phase 8: HRMS — Recruitment, Training & Advanced
**Reference:** AVY-HRMS-CFG-002, Sections 16, 22–27

| # | Feature | Spec Section | Backend | Mobile | Web | Status |
|---|---------|-------------|---------|--------|-----|--------|
| 8.1 | Job Requisition | 16.2 | ✅ | ✅ | ✅ | Done |
| 8.2 | Candidate Pipeline (ATS) | 16.3 | ✅ | ✅ | ✅ | Done (stage progression, source tracking) |
| 8.3 | Interview Scheduler | 16.4 | ✅ | ✅ | ✅ | Done (schedule, complete, cancel, feedback) |
| 8.4 | Training Catalogue | 22.1 | ✅ | ✅ | ✅ | Done |
| 8.5 | Training Nominations | 21.6 | ✅ | ✅ | ✅ | Done (with skill auto-update on completion) |
| 8.6 | Asset Category Master | 24.1 | ✅ | ✅ | ✅ | Done |
| 8.7 | Asset Inventory & Assignment | 24.2–24.4 | ✅ | ✅ | ✅ | Done (assign, return, condition tracking) |
| 8.8 | Expense Claims | 25.x | ✅ | ✅ | ✅ | Done (submit, approve, reject) |
| 8.9 | HR Letter Templates | 26.1–26.3 | ✅ | ✅ | ✅ | Done (token-based generation) |
| 8.10 | Grievance Management | 27.1 | ✅ | ✅ | ✅ | Done (categories, SLA, cases, resolution) |
| 8.11 | Discipline Management (SCN, PIP, Warnings) | 27.2 | ✅ | ✅ | ✅ | Done |
| 8.12 | Resume Parser (AI) | 16.3 | ❌ | ❌ | ❌ | Deferred — AI/ML feature |
| 8.13 | Video Link Auto-Generate (Meet/Teams) | 16.4 | ❌ | ❌ | ❌ | Deferred — calendar API integration |
| 8.14 | Offer Letter e-Sign | 16.5 | ❌ | ❌ | ❌ | Deferred — e-sign provider integration |
| 8.15 | Travel Policy / DA Config | 25.x | ❌ | ❌ | ❌ | Deferred — complex travel grade system |
| 8.16 | POSH Committee Tracking | 27.1 | ❌ | ❌ | ❌ | Deferred — separate compliance module |
| 8.17 | Mandatory Training Compliance | 22.2 | ✅ Partial | — | — | mandatory flag exists; deadline enforcement deferred |

---

## Phase 9: HRMS — Offboarding & Full & Final
**Reference:** AVY-HRMS-CFG-002, Section 20

| # | Feature | Spec Section | Backend | Mobile | Web | Status |
|---|---------|-------------|---------|--------|-----|--------|
| 9.1 | Resignation / Exit Workflow | 20.1 | ✅ | ✅ | ✅ | Done (with auto LWD calculation, notice waiver) |
| 9.2 | Multi-Department Clearance Dashboard | 20.2 | ✅ | ✅ | ✅ | Done (IT/Admin/Finance/HR/Library) |
| 9.3 | Exit Interview | 20.1 | ✅ | ✅ | ✅ | Done (questionnaire + rating) |
| 9.4 | F&F Settlement Computation | 20.3–20.4 | ✅ | ✅ | ✅ | Done (salary, leave encashment, gratuity, bonus, notice pay, loan/asset recovery, TDS) |
| 9.5 | F&F by Separation Type | 20.4 | ✅ | — | — | Different treatment for resignation/retirement/termination/layoff/death |
| 9.6 | Payroll Exception Manager for Exits | 20.5 | ✅ Partial | — | — | Mid-month pro-rata via F&F computation. Dedicated exception manager deferred. |
| 9.7 | Knowledge Transfer Checklist | 20.1 | ✅ Partial | — | — | Boolean flag on ExitRequest. Full task-based KT checklist deferred. |

---

## Cross-Cutting Features (from HRMS spec)

| # | Feature | Spec Section | Status | Notes |
|---|---------|-------------|--------|-------|
| C.1 | Data Inherited from Onboarding | 2.x | ✅ | Company, fiscal, shifts, locations all inherited |
| C.2 | RBAC (Pre-built + Custom Roles) | 12.x | ✅ | Phase 1: role management + permission matrix |
| C.3 | Field-Level Masking | 12.3 | ❌ | Deferred — requires per-field access control system |
| C.4 | Audit Trail (Immutable) | 29.x | ✅ | Platform-level AuditLog + tenant-scoped queries |
| C.5 | Data Retention Policy | 15.x | ❌ | Deferred — requires background archival jobs |
| C.6 | GDPR / Data Privacy | 15.3 | ❌ | Deferred — consent management, data portability |
| C.7 | Reports & Analytics | 30.x | ✅ Partial | Payroll reports done. Full 26-report suite deferred. |
| C.8 | Integration: Tally/SAP/QuickBooks | 31.1 | ❌ | Deferred — ERP connector development |
| C.9 | Integration: EPFO/ESIC Portal | 31.5 | ❌ | Deferred — government portal API integration |
| C.10 | Integration: E-Sign | 31.6 | ❌ | Deferred — Aadhaar eSign / DigiSign integration |
| C.11 | Integration: Banking (Auto-Push) | 31.8 | ❌ | Deferred — bank API integration |
| C.12 | Smart Config Pages (32→6) | 3.1 | ✅ Partial | Screens are organized but not exactly 6 consolidated pages |
| C.13 | Smart Transactional Pages (28→6) | 3.2 | ✅ Partial | Individual screens rather than 6 mega-pages |

---

## Summary: What's Built vs What's Deferred

### Built (Core HRMS — ~92% of daily-use functionality)
- Full org structure management (departments, designations, grades, types, cost centres)
- Complete employee lifecycle (hire → manage → exit)
- **Employee transfers** with request → approve → apply workflow, future-dated support, auto-letter generation
- **Employee promotions** with designation/grade/CTC changes, arrears, appraisal linkage
- Attendance management with rules, overrides, holidays, rosters, overtime
- Leave management with types, policies, balances, application/approval, sandwich rules
- Full payroll pipeline (components → structures → assignment → 6-step run → payslips → statutory)
- ESS & MSS portals
- **Approval workflow engine wired to all 12 modules** (leave, attendance, loan, expense, exit, payroll, revision, requisition, asset, transfer, promotion, overtime)
- **SLA enforcement via background cron** (auto-escalate, auto-approve, auto-reject on deadline breach)
- **Manager delegation/proxy** (delegate approval authority during leave, with CRUD + auto-detection)
- Notification rules & templates with token system
- IT declarations (Form 12BB) with full section 80C/D/E/G/TTA/HRA/LTA coverage
- Performance management (appraisals, goals, 360 feedback, skills, succession)
- Recruitment & ATS (requisitions, candidates, interviews)
- Training & LMS (catalogue, nominations, skill auto-update)
- Asset management (categories, inventory, assignments)
- Expense claims management
- HR letter generation (template-based with token resolution)
- Grievance & discipline management (SCN, PIP, warnings)
- Full offboarding with F&F settlement by separation type
- Company admin self-service (profile, locations, settings, users, roles, feature toggles)

### Deferred (Integration & Advanced Features — ~8%)
- Hardware integrations (biometric devices, face recognition, GPS punch, real maps)
- External system integrations (Tally/SAP, EPFO/ESIC portals, banking APIs, e-sign providers, email/SMS/WhatsApp dispatch)
- AI features (resume parser, HR chatbot, attrition prediction)
- Advanced analytics (full 26-report suite, engagement surveys, eNPS)
- Data governance (retention policies, GDPR, field-level masking)
- Import/export features (bulk increment upload, Excel import, data migration)
- Calendar integrations (Google Meet/Teams auto-linking)
- Production module integration (incentives, OEE auto-pull)
- Employee custom fields (dynamic field system)
- Visual org chart rendering

---

## Gap Fixes Applied (Post Phase 1-9)

| Gap | What Was Fixed | Impact |
|-----|---------------|--------|
| **Workflow Wiring** | `createRequest()` wired to all 12 modules (was only 2) | All approval-required actions now go through workflow engine when configured |
| **SLA Enforcement** | Background cron job (every 15min) auto-escalates/approves/rejects | Approvals no longer get stuck — SLA timers are enforced |
| **Manager Delegation** | ManagerDelegate model + CRUD + delegate resolution in pending approvals | Approvals don't block when manager is on leave |
| **Employee Transfers** | Full module: EmployeeTransfer model, request → approve → apply lifecycle, auto-letter | Formal transfer process with audit trail |
| **Employee Promotions** | Full module: EmployeePromotion model, request → approve → apply, salary revision | Formal promotion process linked to appraisals |
| **Frontend Screens** | 3 new screens (Transfer, Promotion, Delegate) in both mobile + web | Complete UI for all gap features |

---

*Document maintained by Avyren Technologies — Product Team*
*Generated: March 20, 2026 | Updated: March 20, 2026 (v2.0 — gap fixes)*
