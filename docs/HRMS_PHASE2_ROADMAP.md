# HRMS Module — Phase 2 Roadmap (Deferred Items)

**Created:** 2026-03-28
**Status:** Planned — Not yet implemented
**Prerequisite:** Phase 1 (all audit remediation) must be complete and stable

---

## Deferred Items

### RED-4: Form 16 & 24Q Generation (15-20 hours)
**Priority:** Critical for year-end (March 2027)
**Scope:**
- Form 16 Part B generation from PayrollEntry + ITDeclaration data
- Form 24Q quarterly TDS return in NSDL-prescribed format
- Bulk Form 16 generation and email dispatch
- Form 26AS reconciliation (match TDS deposited vs deducted)
**Dependencies:** RED-1 (IT declarations wired to TDS) must be complete
**Timeline:** Implement by February 2027

### ORA-7: E-Sign Integration (10-15 hours)
**Priority:** Medium
**Scope:** Aadhaar eSign / DigiSign / SignDesk integration for offer letters, appointment letters, confirmation letters, F&F settlement, asset receipts, warning letters
**Approach:** Abstract e-sign provider behind an interface; implement DigiSign adapter first
**Timeline:** Q3 2026

### ORA-8: AI HR Chatbot (20-30 hours)
**Priority:** Low — nice-to-have for ESS
**Scope:** AI chatbot in ESS for leave balance queries, payslip download, policy FAQ, attendance status, HR contact lookup
**Approach:** Use Claude API or similar LLM with RAG over company policies
**Timeline:** Q4 2026

### ORA-9: Production Incentive Module (15-20 hours)
**Priority:** Manufacturing-specific — implement only for manufacturing clients
**Scope:** Machine-wise production incentive with slab-based payout, machine-employee mapping, daily/weekly/monthly calculation, payroll auto-integration
**Dependencies:** Production module integration
**Timeline:** On-demand per client

### ORA-11: Data Retention & GDPR Controls (10-15 hours)
**Priority:** Required for EU operations or India DPDP Act 2023 compliance
**Scope:** Automated retention periods per data type, anonymisation after retention, GDPR data access requests, right to rectification, data portability, consent management
**Timeline:** Q4 2026

### YEL-5: Leave Sandwich Rule Verification
**Status:** Already implemented correctly in `calculateLeaveDays()` (verified in code audit)
**Action:** No code changes needed. Mark as verified.

### YEL-6: Shift Rotation Automation (5-8 hours)
**Priority:** Low — manual shift assignment works for pilot
**Scope:** Scheduled job that auto-rotates employee shift assignments based on roster pattern (weekly/fortnightly)
**Timeline:** Q3 2026

### YEL-7: Biometric Device Integration (20-30 hours)
**Priority:** Medium — use mobile GPS for pilot
**Scope:** ZKTeco/ESSL/Realtime SDK integration, real-time push, scheduled pull, device management, enrollment
**Timeline:** Q3 2026

### YEL-9: Travel Advance Recovery (3-5 hours)
**Priority:** Low — manual workaround available
**Scope:** Travel advance as lump-sum disbursement, recovery against expense settlement instead of EMI
**Timeline:** Q3 2026

---

*This document tracks deferred items from the HRMS audit. Each item will be converted to a detailed implementation plan when prioritized for development.*
