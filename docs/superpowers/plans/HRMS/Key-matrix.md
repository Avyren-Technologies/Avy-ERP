## HRMS Traceability Matrix (Markdown)

Below is the section-wise comparison of `AVY_ERP_HRMS_FINALISED.md` against:
- `docs/superpowers/plans/2026-03-20-implementation-checklist.md`
- `docs/superpowers/plans/2026-03-19-phase1-company-admin-core.md`

### Status Legend
- `Completed` = implemented and marked done in checklist
- `Partial` = foundational or limited implementation
- `Deferred` = explicitly not implemented / integration pending
- `Not in scope` = informational/architecture section, not a direct build item

---

## A) Core Foundation & Architecture

| Finalised Section | Feature Area | Checklist Mapping | Status | Gap / Notes |
|---|---|---|---|---|
| 1 | HRMS scope and sub-modules | Phases 2–9 + cross-cutting | Completed | Core scope covered at module level |
| 2 | Inherited tenant onboarding data | C.1 Data inherited | Completed | Aligned |
| 3.1 | 32 config screens -> 6 smart pages | C.12 | Partial | Implemented as multiple screens, not strict 6-page consolidation |
| 3.2 | 28 transactional screens -> 6 smart pages | C.13 | Partial | Transactional coverage exists, page consolidation differs |
| 3.3 | Smart setup flow | Implied across phases | Partial | No single unified smart-flow implementation called out |

---

## B) Org Structure & Employee Master (Sections 4, 5, 17)

| Finalised Section | Feature Area | Checklist Mapping | Status | Gap / Notes |
|---|---|---|---|---|
| 4.1 | Department master | 2.1 | Completed | — |
| 4.2 | Designation master | 2.2 | Completed | — |
| 4.3 | Grade/Band master | 2.3 | Completed | — |
| 4.4 | Employee type + statutory flags | 2.4 | Completed | — |
| 4.5 | Reporting hierarchy | 2.9 | Partial | Self-relations implemented; visual org chart not complete |
| 4.6 | Cost centre | 2.5 | Completed | — |
| 4.7 | Work location categories | 2.10 | Partial | Enum-level only |
| 4.8 | Production incentive config | 2.11 | Deferred | Needs production integration |
| 5.1–5.8 | Employee master core + 6-tab profile + docs/education/history | 2.6, 2.7 | Completed | — |
| 5.9 | Employee custom fields | 2.12 | Deferred | Dynamic field framework pending |
| 5.10 | Employee timeline | 2.8 | Completed | — |
| 17.1 | New hire entry smart behavior | 2.7 + Phase 2 flows | Partial | Core form exists; advanced smart automations not fully explicit |
| 17.2 | Onboarding checklist TRN-006 | 2.13 | Partial | Full task engine deferred |
| 17.3 | Employment-type document matrix | Phase 2 docs capture | Partial | Matrix-driven enforcement not explicit |
| 17.4 | Probation/confirmation tracking | Not clearly mapped | Deferred | Missing dedicated workflow module |
| 17.5 | Transfer/promotion workflow | Not clearly mapped | Deferred | Missing dedicated transfer/promotion flows |

---

## C) Attendance & Leave (Sections 6, 7, 19.1, 19.2)

| Finalised Section | Feature Area | Checklist Mapping | Status | Gap / Notes |
|---|---|---|---|---|
| 6.1 | Attendance capture methods | 3.1 + 3.17 | Partial | Manual/core done; GPS/face capture deferred |
| 6.2 | Biometric device config | 3.14 | Deferred | Hardware integration pending |
| 6.3 | Geo-fence config | 3.15 | Partial | Geo fields exist; full map/device enforcement pending |
| 6.4 | Shift config | 3.8 | Completed | Inherited + operational |
| 6.5 | Roster/work week | 3.6 | Completed | — |
| 6.6 | Holiday calendar | 3.5 | Completed | — |
| 6.7 | OT rules | 3.7 | Completed | — |
| 6.8 | Attendance rules | 3.3 | Completed | — |
| 7.1–7.7 | Leave types, policy, approval, balances, comp-off | 3.9–3.13 | Completed | — |
| 19.1 | Attendance override TRN-011 | 3.4 | Completed | — |
| 19.2 | Leave override TRN-012 | 3.12 (adjust/initialize) | Completed | Operationally covered |

---

## D) Payroll, Statutory, Tax (Sections 8, 9, 10, 18, 28)

| Finalised Section | Feature Area | Checklist Mapping | Status | Gap / Notes |
|---|---|---|---|---|
| 8.1–8.4 | Salary components/structure | 4.1, 4.2 | Completed | — |
| 8.5 | Payroll run config | 4.14 | Partial | Service-level config only |
| 8.6 | Salary revision config | 4.15 | Completed | — |
| 8.7 | Bank disbursement config | 4.10 | Completed | Connector automation pending |
| 8.8 | Loan policy | 4.11, 4.12 | Completed | — |
| 8.9 | Reimbursements config | 4.16 + 8.8 | Partial | Expense claims exist; full reimbursement config depth limited |
| 9.1–9.6 | PF/ESI/PT/Gratuity/Bonus/LWF | 4.4–4.9 | Completed | — |
| 9.7 | Statutory reports & filings | 5.7 | Completed | Full portal automation still pending |
| 10.1–10.3 | Tax regime/slabs/12BB | 4.13 + 6.11 | Completed | — |
| 10.4 | Perquisites config | Not explicitly mapped | Deferred | Missing explicit perquisite engine |
| 10.5 | TDS, Form16, 24Q | 5.9 | Partial | Record flow exists; final generation/export deferred |
| 18.1 | 6-step payroll wizard | 5.1 | Completed | — |
| 18.2 | Salary hold | 5.3 | Completed | — |
| 18.3 | Arrears | 5.4 | Completed | — |
| 18.4 | Salary revision wizard + bulk upload | 5.5 + 5.10 | Partial | Individual done; bulk upload deferred |
| 18.5 | F&F linkage in payroll | 9.4 + 9.5 | Completed | — |
| 28 | Compliance ops dashboard | 5.6 | Completed | — |

---

## E) ESS, RBAC, Workflow, Notifications, Governance (Sections 11–15, 29)

| Finalised Section | Feature Area | Checklist Mapping | Status | Gap / Notes |
|---|---|---|---|---|
| 11.1 | ESS access config incl. SSO/MFA | 6.1, 6.13 | Partial | ESS config done; SSO deferred |
| 11.2 | ESS module enablement | 6.2–6.5 | Completed | — |
| 11.3 | MSS | 6.6 | Completed | — |
| 11.4 | AI chatbot | 6.12 | Deferred | AI integration pending |
| 12.1/12.2/12.4 | RBAC roles, permissions, custom roles | C.2 + Phase 1 role mgmt | Completed | — |
| 12.3 | Field-level masking | C.3 | Deferred | Not implemented |
| 13.1–13.3 | Workflow designer + SLA | 6.7, 6.8 | Completed | — |
| 14.1–14.3 | Notification channels/rules/triggers | 6.9, 6.10, 6.14 | Partial | Rule engine done; real channel connectors pending |
| 15.1–15.3 | Retention, delete policy, GDPR | C.5, C.6 | Deferred | Governance automation pending |
| 29 | Audit trail & governance | C.4 | Partial | Audit logging present; broader governance controls incomplete |

---

## F) Recruitment, Performance, Training, Loans, Assets, Travel, Letters, Discipline, Exit (Sections 16, 20–27)

| Finalised Section | Feature Area | Checklist Mapping | Status | Gap / Notes |
|---|---|---|---|---|
| 16.1–16.4 | Hiring flow, requisition, ATS, interview scheduler | 8.1–8.3 | Completed | — |
| 16.5 | Assessment/offer incl e-sign | 8.14 | Deferred | E-sign provider integration pending |
| 19.3 | Bonus & incentive upload | Not clearly mapped | Deferred | Missing dedicated transactional upload flow |
| 19.4 | Loans & advances processing | 4.12 + 8.8 | Completed | — |
| 19.5 | Asset issuance management | 8.6, 8.7 | Completed | — |
| 20.1 | Resignation & exit workflow | 9.1 | Completed | — |
| 20.2 | Multi-department clearance | 9.2 | Completed | — |
| 20.3/20.4 | Separation types + F&F treatment | 9.4, 9.5 | Completed | — |
| 20.5 | Payroll exception manager exits | 9.6 | Partial | Dedicated manager deferred |
| 21.1–21.7 | Appraisal, goals, 360, calibration, skill, succession | 7.1–7.7 | Completed | — |
| 21.8 | Engagement/eNPS | 7.8 | Deferred | Survey engine needed |
| 21.9 | Industry presets | 7.9 | Deferred | Template/seed module needed |
| 22.1 | Training catalogue | 8.4 | Completed | — |
| 22.2 | Mandatory training config | 8.17 | Partial | Deadline/escalation not complete |
| 22.3 | Training budget tracking | 8.4/8.5 (limited) | Partial | Full budget analytics not explicit |
| 22.4 | Training completion assessment | 8.5 | Partial | Core completion exists; richer assessment tracking unclear |
| 22.5 | External certification tracking | Not clearly mapped | Deferred | Expiry/renewal workflow not complete |
| 23.1/23.2 | Loan types + configuration | 4.11, 4.12 | Completed | — |
| 23.3 | Reimbursement types | 4.16 + 8.8 | Partial | Full tax/policy matrix not complete |
| 24.1–24.4 | Asset category/master/issue/return | 8.6, 8.7 | Completed | — |
| 24.5 | Asset reports | Not explicit | Partial | Some reporting likely, full suite not confirmed |
| 25 | Travel & expense config | 8.8 + 8.15 | Partial | Claims done; travel-grade/DA policy deferred |
| 26.1–26.3 | HR letters & templates | 8.9 | Completed | Advanced dispatch/e-sign pending |
| 27.1/27.2 | Grievance + discipline | 8.10, 8.11 | Completed | POSH committee tracking deferred |

---

## G) Reports, Analytics, Integrations, Go-Live (Sections 30–32)

| Finalised Section | Feature Area | Checklist Mapping | Status | Gap / Notes |
|---|---|---|---|---|
| 30.1 | Standard HRMS report suite | 5.8 + C.7 | Partial | Payroll-heavy reports done; full 26-report suite not complete |
| 30.2 | Analytics dashboards | 3.2, 5.6, 7.7 (limited) | Partial | Many dashboards from finalised doc pending |
| 31.1 | Finance/Accounts connectors | C.8 | Deferred | Tally/SAP/QuickBooks connectors pending |
| 31.2 | Internal payroll integration | Core phases 3–5 | Completed | Operationally integrated |
| 31.3 | Production integration | 2.11, 7.10 | Deferred | OEE/incentive links pending |
| 31.4 | Biometric/access devices | 3.14, 3.16, 3.17 | Deferred | Device/camera/GPS integrations pending |
| 31.5 | Govt portals EPFO/ESIC/TRACES | C.9 | Deferred | Export/manual likely; auto filing pending |
| 31.6 | E-sign integration | C.10 + 8.14 | Deferred | Provider integration pending |
| 31.7 | Communication platforms | 6.14 | Partial | Rules done, channel providers pending |
| 31.8 | Banking integration | 5.11 + C.11 | Deferred | Auto-push/retry pending |
| 31.9 | Migration/co-existence APIs | Not explicit | Deferred | Not covered in checklist |
| 32 | Go-live readiness checklist | Not a build feature | Not in scope | Validation checklist, not implementation feature |

---

## Overall Comparison Snapshot

| Category | Result |
|---|---|
| Core HRMS operations (Org, Employee, Attendance, Leave, Payroll, ESS, Performance, Exit) | **Largely Completed** |
| Advanced transaction depth (probation/transfer, bonus upload, certification lifecycle) | **Partial** |
| Integrations (biometric, statutory portals, e-sign, banking, ERP connectors, comm channels) | **Mostly Deferred** |
| Governance (field masking, retention automation, GDPR) | **Deferred** |
| Reporting/analytics breadth from final spec | **Partial** |

---

If you want, I can now generate a **“closure plan table”** with 3 buckets only:
1) **Quick wins (1–2 sprints)**  
2) **Medium effort (3–5 sprints)**  
3) **Heavy integrations (program-level work)**  
so your team can prioritize gap closure directly from this matrix.