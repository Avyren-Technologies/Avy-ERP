# Avy ERP HRMS — Feature Scope Register

> **Date:** March 20, 2026  
> **Purpose:** Single reference of HRMS features that are currently in scope vs not in current scope, based on:
>
> - `docs/superpowers/plans/2026-03-20-implementation-checklist.md`
> - `docs/superpowers/plans/2026-03-19-phase1-company-admin-core.md`
> - `docs/AVY_ERP_HRMS_FINALISED.md`

---

## 1) Features Considered Now (Current Scope)

### A. Core Foundation and Access

- Inherited tenant onboarding data usage inside HRMS (company identity, statutory, addresses, fiscal, locations, shifts).
- Company-admin self-service foundation:
  - Company profile and settings
  - Locations (edit/delete), shifts, contacts, no-series, IOT reasons, controls
  - Users, roles, feature toggles
  - Tenant-scoped audit log access
- Role-based access control with prebuilt and custom roles.
- Approval workflow engine with multi-step chains and SLA/escalation logic.
- Notification templates and rules framework.

### B. Organisational Structure

- Department master.
- Designation/job title master.
- Grade/band/level master.
- Employee type master (with statutory flags).
- Cost centre master.
- Reporting hierarchy foundations (manager relationships on employee records).
- Work type categorization (on-site/remote/hybrid style classification).

### C. Employee Master and Lifecycle Core

- Employee directory with search/filter.
- Employee profile (6-tab structure):
  - Personal information
  - Professional/employment details
  - Salary/CTC details
  - Bank details
  - Documents
  - Emergency contacts
- Employee nominee details.
- Employee education details.
- Employee previous employment details.
- Employee document records.
- Employee timeline and lifecycle event logging.
- Employee onboarding entry flow foundations.

### D. Attendance Management

- Attendance record management.
- Attendance dashboards and summaries.
- Attendance rules configuration.
- Attendance override/regularization workflows.
- Shift master usage within attendance.
- Roster/work-week configuration.
- Holiday calendar configuration (including year handling/clone patterns).
- Overtime rule configuration.

### E. Leave Management

- Leave type master.
- Leave policy assignment (multi-level assignment model).
- Leave application flow.
- Leave approval/rejection/cancellation flow.
- Leave balance tracking and adjustment flows.
- Comp-off handling through leave category/policy setup.
- Leave override style operations through HR adjustment flows.

### F. Payroll Configuration

- Salary component master.
- Salary structure/template management.
- Employee salary assignment and breakup handling.
- Payroll run configuration foundations.
- Salary revision configuration.
- PF configuration.
- ESI configuration.
- PT configuration.
- Gratuity configuration.
- Bonus configuration.
- LWF configuration.
- Bank disbursement configuration.
- Loan policy configuration.
- Loan record management.
- Tax regime and slab configuration.
- IT declaration configuration (Form 12BB sections).

### G. Payroll Operations and Statutory Operations

- Monthly payroll 6-step operational wizard structure:
  - Lock
  - Exceptions
  - Compute
  - Statutory
  - Approval
  - Disburse
- Payslip record generation flow.
- Salary hold and release flows.
- Arrear processing.
- Salary revision wizard (individual flow).
- Statutory compliance dashboard.
- Statutory filing management records.
- Payroll reporting base set (salary register and related statutory/payroll outputs).
- Exit-linked payroll/F&F calculations.

### H. ESS and MSS

- ESS access configuration foundations.
- ESS modules:
  - Profile self-service
  - Payslips
  - Leave actions and views
  - Attendance views/regularization
- MSS modules:
  - Team views
  - Approval actions
  - Team attendance/leave context

### I. Performance Management

- Appraisal cycle configuration.
- KRA/OKR goal configuration.
- 360-degree feedback flow.
- Appraisal rating and calibration flow.
- Skill library/mapping and gap analysis foundations.
- Succession planning foundations (readiness and bench-strength style setup).
- Performance dashboard baseline.

### J. Recruitment and ATS

- Job requisition management.
- Candidate profile and pipeline/stage progression.
- Interview scheduling and feedback flow.
- Offer-to-hire linkage foundations in ATS-to-employee flow.

### K. Training and Learning

- Training catalogue configuration.
- Training nominations.
- Training completion capture foundations.
- Skill auto-update linkage from training outcomes.
- Mandatory training flag foundations.

### L. Loan, Advance, Reimbursement, Travel and Expense

- Loan policy and workflow-aligned processing foundations.
- Loan disbursement and payroll deduction linkage.
- Expense claim management flow:
  - Submission
  - Receipt attachment
  - Approval/rejection
  - Payroll linkage
- Travel/expense operational foundations through claims model.

### M. Asset Management

- Asset category master.
- Asset inventory/master records.
- Asset assignment/issuance tracking.
- Asset return tracking.
- Asset linkage into employee exit/F&F context.

### N. HR Letters, Grievance, Discipline

- HR letter template management.
- Letter generation foundations with employee tokenized data.
- Grievance category and case handling.
- Discipline actions (warning/SCN/PIP/suspension/termination style actions).

### O. Offboarding and Full & Final

- Resignation and exit workflow.
- Last working day and notice-related handling foundations.
- Exit interview capture.
- Multi-department clearance tracking.
- F&F settlement computation:
  - Salary for worked days
  - Leave encashment
  - Gratuity
  - Bonus
  - Notice pay
  - Loan recovery
  - Asset recovery
  - Tax treatment on F&F components
- Separation type handling in F&F logic (resignation/retirement/termination/layoff/death patterns).
- Knowledge-transfer linkage foundations in exit records.

### P. Audit, Reporting and Cross-Cutting Foundations

- Tenant-scoped audit trail visibility.
- Payroll/compliance-focused reports.
- Cross-module HRMS data flow between attendance, leave, payroll, exits, and ESS.

---

## 2) Features Not Considered Now (Not in Current Scope)

### A. Attendance Hardware and Advanced Capture Integrations

- Biometric device integration setup and syncing (vendor-level integrations).
- Face recognition attendance setup and matching flow.
- Mobile GPS punch with geolocation/background behavior.
- Full geofence map tooling and enforcement workflows.

### B. Advanced Employee Lifecycle Modules

- Full onboarding task engine with department-wise task ownership dashboard.
- Probation tracking workflow with formal confirm/extend/terminate lifecycle actions.
- Transfer workflow with full transactional wizard and downstream document automation.
- Promotion workflow with all advanced policy gates and auto-document dispatch.
- Dynamic custom fields framework for employee master.

### C. Compensation and Payroll Advanced Automations

- Bulk increment upload/import workflow (Excel/CSV ingestion).
- Full Form 16 and 24Q output generation pipeline (final document/export-grade layer).
- Perquisites management engine (detailed taxable perquisite rules lifecycle).
- Bank file auto-push and payment retry orchestration via direct bank APIs.
- Dedicated payroll exception manager module for exits as a standalone feature.

### D. Recruitment and Hiring Advanced Integrations

- AI-based resume parser.
- Auto-generated meeting links (Google Meet / Microsoft Teams) in interview scheduling.
- Offer letter e-sign orchestration with external signature providers.

### E. Training and Talent Advanced Controls

- Mandatory training deadline enforcement and escalation engine.
- Department/employee training budget governance and budget analytics depth.
- External certification lifecycle management with expiry/renewal orchestration.
- Promotion block orchestration driven by certification expiry in full policy form.
- Employee engagement modules (pulse surveys, eNPS).
- Industry preset templates as packaged setup accelerators.
- HiPo development programme tracking workflow.

### F. Travel and Compliance Depth

- Full travel policy matrix (grade-level entitlement, air class, hotel category, DA policy engine).
- POSH committee lifecycle tracking and statutory annual report workflow.

### G. Data Governance and Privacy Controls

- Field-level masking controls by role/permission at a per-field level.
- Data retention policy automation with archival/purge job orchestration.
- GDPR/advanced privacy controls (consent, portability, compliance workflows).

### H. Communications and Identity Integrations

- SSO integrations (Google/Microsoft/Azure AD style production connectors).
- Live channel dispatch integrations for:
  - SMTP email provider wiring
  - SMS gateway provider wiring
  - WhatsApp provider wiring
  - Teams/Slack communication bot integrations

### I. External Enterprise and Government Integrations

- ERP connector integrations (Tally/SAP/QuickBooks/Oracle Finance style connectors).
- Government statutory portal integrations (EPFO/ESIC/TRACES direct submission workflows).
- E-sign provider integrations (Aadhaar eSign / DigiSign / SignDesk style live connectors).
- Banking integrations for automatic salary disbursement push and failure recovery.
- Third-party HRMS/ERP migration/co-existence connector layer.

### J. Production/Operations Deep Integration

- Production incentive engine integrated with machine/production output.
- OEE and production KPI auto-pull into HR/performance/payroll workflows.
- Employee-machine mapping level integration with production operations.

### K. Reporting and Analytics Full Suite

- Full HRMS report suite breadth as listed in finalized document (all report variants).
- Full analytics dashboard suite breadth (attrition, recruitment funnel, training utilization, succession depth, etc. in complete form).

### L. UI Architecture Consolidation Targets

- Strict realization of "6 Smart Configuration Pages" and "6 Smart Transactional Pages" as exact consolidated UI architecture targets.

---

## 3) Notes for Usage

- This register is intentionally a **scope inventory** only.
- It does not classify features by delivery stage, release readiness, or deployment status.
- For execution sequencing, use the existing phase/checklist planning documents.

