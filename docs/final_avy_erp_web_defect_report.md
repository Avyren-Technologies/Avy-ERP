# AVY ERP -- Company Admin (Web) Defect Report

**Scope:** Company Admin + HRMS (Web Only)\
**Date:** March 20, 2026\
**Environment:** `http://localhost:3030`\
**Reference:** Manual Testing Guide

------------------------------------------------------------------------

# 🔴 **1. CRITICAL ISSUES (Core Blocking -- System Not Usable)**

------------------------------------------------------------------------

## 1.1 Company Profile -- Edit Not Working

-   **Module:** Company → Company Profile

-   **Issue:**

    -   Edit not working for:

        -   Legal Name
        -   Display Name
        -   Company Address
        -   Corporate Address

-   **API Error:**

        PATCH /api/v1/company/profile/sections/names → 400 Bad Request

-   **Expected:**

    -   Editable fields should update successfully

-   **Impact:** ❌ Cannot update company data

-   **Priority:** 🔴 Critical

------------------------------------------------------------------------

## 1.2 Shift Creation Fails

-   **Module:** Company → Shifts

-   **Issue:**

    -   Cannot create shift

-   **API Error:**

        POST /api/v1/company/shifts → 400 Bad Request

-   **Additional Issue:**

    -   "No Shuffle" toggle values incorrect

-   **Impact:** ❌ Attendance system blocked

-   **Priority:** 🔴 Critical

------------------------------------------------------------------------

## 1.3 Number Series Creation Fails

-   **Module:** Configuration → Number Series

-   **Issue:**

        POST /api/v1/company/no-series → 400 Bad Request

-   **Impact:** ❌ Employee ID / document numbering blocked

-   **Priority:** 🔴 Critical

------------------------------------------------------------------------

## 1.4 User Creation Not Working

-   **Module:** People & Access → Users

-   **Issue:**

        POST /api/v1/company/users → 400 Bad Request

-   **Additional Issue:**

    -   Role filter not working (Admin/Manager not filtering)

-   **Impact:** ❌ Cannot onboard users

-   **Priority:** 🔴 Critical

------------------------------------------------------------------------

## 1.5 Role Creation Fails

-   **Module:** Roles & Permissions

-   **Issue:**

        POST /api/v1/rbac/roles → 422 Unprocessable Entity

-   **Impact:** ❌ RBAC system blocked

-   **Priority:** 🔴 Critical

------------------------------------------------------------------------

## 1.6 Audit Logs Not Working

-   **Module:** Reports → Audit Logs

-   **Issue:**

        GET /api/v1/platform/audit-logs → 401 Unauthorized

-   **Expected:**

    -   Should use tenant-level endpoint (company scoped)

-   **Impact:** ❌ No audit visibility

-   **Priority:** 🔴 Critical

------------------------------------------------------------------------

## 1.7 Department Creation Fails

-   **Module:** HR → Departments

-   **Issue:**

        POST /api/v1/hr/departments → 500 Internal Server Error

-   **Additional Issue:**

    -   Parent Department & Cost Center dropdown missing

-   **Impact:** ❌ Org structure blocked

-   **Priority:** 🔴 Critical

------------------------------------------------------------------------

## 1.8 Designation Creation Fails

-   **Module:** HR → Designations

-   **Issues:**

    -   Dropdowns missing:

        -   Department
        -   Grade

    -   API error:

    ```{=html}
    <!-- -->
    ```
        POST /api/v1/hr/designations → 500 Internal Server Error

-   **Impact:** ❌ Employee setup blocked

-   **Priority:** 🔴 Critical

------------------------------------------------------------------------

## 1.9 Grade Creation Fails

-   **Module:** HR → Grades

-   **Issue:**

        POST /api/v1/hr/grades → 400 Bad Request

-   **Impact:** ❌ Salary & hierarchy blocked

-   **Priority:** 🔴 Critical

------------------------------------------------------------------------

## 1.10 Employee Type Creation Fails

-   **Module:** HR → Employee Types

-   **Issue:**

        POST /api/v1/hr/employee-types → 400 Bad Request

-   **Impact:** ❌ Payroll/statutory config blocked

-   **Priority:** 🔴 Critical

------------------------------------------------------------------------

## 1.11 Cost Centre Creation Fails

-   **Module:** HR → Cost Centres

-   **Issues:**

    -   Department dropdown missing
    -   API error:

    ```{=html}
    <!-- -->
    ```
        POST /api/v1/hr/cost-centres → 500 Internal Server Error

-   **Impact:** ❌ Financial mapping blocked

-   **Priority:** 🔴 Critical

------------------------------------------------------------------------

## 1.12 Employee Creation Issues

-   **Module:** HR → Employee

-   **Issues:**

    -   Missing dropdowns:

        -   Department
        -   Designation
        -   Grade
        -   Reporting Manager
        -   Functional Manager
        -   Location
        -   Cost Center

    -   IFSC → Bank name not auto-filled

    -   API error:

    ```{=html}
    <!-- -->
    ```
        POST /api/v1/hr/employees → 400 Bad Request

-   **Impact:** ❌ Core HR system unusable

-   **Priority:** 🔴 Critical

------------------------------------------------------------------------

## 1.13 All HR Transactions Failing (Transfers / Promotions / Delegation)

-   **APIs:**

    -   `/hr/transfers`
    -   `/hr/delegates`

-   **Issue:**

    -   Dropdowns missing (Employee, Dept, etc.)
    -   400 Bad Request

-   **Impact:** ❌ Employee lifecycle blocked

-   **Priority:** 🔴 Critical

------------------------------------------------------------------------

## 1.14 Attendance & Leave Modules Broken

-   **Issues:**

    -   Attendance not loading
    -   Holiday creation fails
    -   Roster creation fails
    -   Leave types creation fails

-   **APIs:**

        /hr/holidays → 400
        /hr/rosters → 400
        /hr/leave-types → 400

-   **Impact:** ❌ Attendance + Leave fully blocked

-   **Priority:** 🔴 Critical

------------------------------------------------------------------------

## 1.15 Payroll Configuration Fully Broken

-   **Modules affected:**

    -   Salary Components
    -   Salary Structure
    -   Employee Salary

-   **Issues:**

    -   Dropdowns missing
    -   Creation fails (400 errors)

-   **Impact:** ❌ Payroll cannot run

-   **Priority:** 🔴 Critical

------------------------------------------------------------------------

## 1.16 Loan / Salary Hold / Salary Revision Not Working

-   **Issue:**

    -   Employee dropdown missing
    -   All POST APIs failing (400)

-   **Impact:** ❌ Financial workflows blocked

-   **Priority:** 🔴 Critical

------------------------------------------------------------------------

## 1.17 ESS + Self-Service Broken

-   **Issues:**

    -   Profile not working
    -   Leave balance API failing
    -   Employee ID dependency issue

-   **API:**

        /hr/ess/my-leave-balance → 400

-   **Impact:** ❌ Employee self-service unusable

-   **Priority:** 🔴 Critical

------------------------------------------------------------------------

## 1.18 Performance Module Not Working

-   **Modules:**

    -   Appraisal
    -   Goals

-   **Issues:**

    -   Dropdowns missing
    -   API failures

-   **Impact:** ❌ Performance system blocked

-   **Priority:** 🔴 Critical

------------------------------------------------------------------------

## 1.19 Recruitment & Training Issues

-   **Issues:**

    -   Hiring Manager dropdown missing
    -   Unnecessary fields shown
    -   Requisition + Candidates merged (UI issue)

-   **Impact:** ❌ Recruitment unusable

-   **Priority:** 🔴 Critical

------------------------------------------------------------------------

## 1.20 Advanced HR Modules Broken

-   **Modules:**

    -   Assets
    -   Claims
    -   Letters
    -   Grievances
    -   Discipline

-   **Issues:**

    -   Employee dropdown missing everywhere
    -   API failures (400)

-   **Impact:** ❌ Advanced HR unusable

-   **Priority:** 🔴 Critical

------------------------------------------------------------------------

# 🟠 **2. HIGH PRIORITY ISSUES (UI / Functional)**

------------------------------------------------------------------------

## 2.1 Statutory & Tax UI Issues

-   Fix UI for:

    -   Registration Numbers

-   Alignment / formatting incorrect

------------------------------------------------------------------------

## 2.2 Location HQ Field Issue

-   HQ values incorrect / inconsistent
-   Needs validation + proper labeling

------------------------------------------------------------------------

## 2.3 IOT Reason -- Planned Field Issue

-   Planned toggle behaves incorrectly
-   Shows invalid values when false

------------------------------------------------------------------------

## 2.4 Company Settings Cleanup

-   Remove unnecessary fields:

    -   Currency
    -   Language
    -   Timezone
    -   Date format
    -   Compliance modes (if not required)

------------------------------------------------------------------------

## 2.5 Feature Toggle Page Empty

-   No data shown
-   Likely API not connected

------------------------------------------------------------------------

## 2.6 Module Catalogue UI

-   Remove either:

    -   Grid view OR List view

-   Keep only one

------------------------------------------------------------------------

## 2.7 Platform Monitor Access Issue

-   Should NOT be visible for Company Admin
-   Move to Super Admin only

------------------------------------------------------------------------

# 🟡 **3. MEDIUM PRIORITY (UX Improvements)**

------------------------------------------------------------------------

## 3.1 Key Contacts

-   Name field should auto-capitalize

------------------------------------------------------------------------

## 3.2 Dropdown Consistency Issue (GLOBAL)

Across entire system:

-   Employee dropdown missing
-   Department dropdown missing
-   Designation dropdown missing
-   Grade dropdown missing

👉 **Root Cause Insight:**

-   Master data APIs not implemented OR
-   Incorrect query filters (tenant/company scope)

------------------------------------------------------------------------

# 🔍 **4. ROOT CAUSE ANALYSIS (VERY IMPORTANT FOR DEV TEAM)**

### 🔴 Primary Problems:

1.  **Master Data Not Loaded**
2.  **Dropdown APIs Missing / Broken**
3.  **Validation Failures (400 errors)**
4.  **Authorization Issues**
5.  **Backend Stability Issues (500 errors)**

------------------------------------------------------------------------

# 📊 **5. OVERALL STATUS**

  Area                 Status
  -------------------- ---------------------
  Company Admin Core   ⚠️ Partially Broken
  HR Master Data       ❌ Broken
  Attendance           ❌ Broken
  Leave                ❌ Broken
  Payroll              ❌ Broken
  ESS                  ❌ Broken
  Performance          ❌ Broken
  Advanced HR          ❌ Broken

------------------------------------------------------------------------

# 🚀 **FINAL SUMMARY**

👉 The system is currently:

-   UI mostly ready
-   Backend integration incomplete / broken

👉 Biggest blocker:

> Master data + dropdown + API failures

👉 Recommendation:

1.  Fix master modules first
2.  Fix dropdown APIs
3.  Fix payroll & transactions
