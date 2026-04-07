# Bulk Employee Import — Design Spec

**Date:** 2026-04-06
**Status:** Approved
**Scope:** Backend (3 endpoints) + Web UI + Mobile UI

---

## Overview

Add bulk employee onboarding via Excel upload to all three codebases. HR admins download a template pre-populated with the company's master data (departments, designations, grades, employee types, locations, shifts, cost centres, roles, salary structures), fill in employee rows, upload for validation, review results, then confirm import. Each imported employee optionally gets a user account (default: yes) with a shared default password.

---

## API Endpoints

### 1. `GET /hr/employees/bulk/template`

Download an Excel (.xlsx) template pre-populated with the company's active master data.

- **Auth:** `hr:create` permission
- **Response:** `application/vnd.openxmlformats-officedocument.spreadsheetml.sheet`
- **Filename:** `Employee_Import_Template_{CompanyShortName}.xlsx`

#### Sheets

| # | Sheet Name | Purpose | Content |
|---|-----------|---------|---------|
| 1 | Employees | Input sheet | Column headers (row 1), example row (row 2, italic/gray), data validation dropdowns on enum columns |
| 2 | Departments | Reference (read-only) | code, name, status — only Active |
| 3 | Designations | Reference | code, name, linked department code, linked grade code, probationDays |
| 4 | Grades | Reference | code, name, probationMonths, noticeDays, ctcMin, ctcMax |
| 5 | Employee Types | Reference | code, name, PF, ESI, PT, Gratuity, Bonus flags |
| 6 | Locations | Reference | code, name, city, state |
| 7 | Shifts | Reference | name, startTime, endTime, shiftType |
| 8 | Cost Centres | Reference | code, name, linked department code |
| 9 | Roles | Reference | name (from company's RBAC roles, excludes system "Company Admin" role) |
| 10 | Salary Structures | Reference | name (from company's configured salary structures) |
| 11 | Instructions | Help text | Field descriptions, required/optional, format rules, enum values |

#### Excel Features
- Frozen header row on Employees sheet
- Dropdown data validation on enum columns (Gender, Marital Status, Work Type, Payment Mode, Account Type, Create Account Yes/No)
- Dropdown validation on master code columns (Department Code, Designation Code, etc.) sourced from reference sheets
- Auto-sized column widths
- Professional styling: indigo (#4F46E5) header fill, white text, alternating row shading on reference sheets
- Example row in Employees sheet: italic, gray text, clearly marked as "(Example — delete this row)"
- Reference sheets protected/locked (read-only indicator in header)

---

### 2. `POST /hr/employees/bulk/validate`

Upload Excel file and validate all rows without creating any records.

- **Auth:** `hr:create` permission
- **Content-Type:** `multipart/form-data`
- **Body:**
  - `file` — xlsx file (max 10MB)
  - `defaultPassword` — string (min 6 chars), used for all user accounts
- **Response:**

```json
{
  "success": true,
  "data": {
    "totalRows": 50,
    "validCount": 47,
    "errorCount": 3,
    "rows": [
      {
        "rowNum": 2,
        "valid": true,
        "data": {
          "firstName": "Rahul",
          "lastName": "Sharma",
          "departmentCode": "HR-001",
          "departmentId": "clxyz...",
          "designationCode": "MGR-01",
          "designationId": "clxyz...",
          "createAccount": true,
          "officialEmail": "rahul@company.com"
        }
      },
      {
        "rowNum": 4,
        "valid": false,
        "errors": [
          "Department code 'XYZ' not found in company masters",
          "Personal email is required"
        ]
      }
    ]
  }
}
```

#### Validation Rules

**File-level:**
- File must be `.xlsx` format
- File size max 10MB
- Must have "Employees" sheet (sheet 1)
- Must have at least 1 data row (row 2+, excluding example row)
- Max 500 rows per upload

**Per-row field validation (same as single employee creation):**
- firstName, lastName: required, non-empty strings
- personalMobile: required, min 10 digits
- personalEmail: required, valid email format, unique within file + unique within company (excluding EXITED employees)
- officialEmail: valid email if provided, required if createAccount = Yes, unique within file + unique within company
- emergencyContactName, emergencyContactRelation, emergencyContactMobile: required
- joiningDate: required, valid YYYY-MM-DD, within HR date range (1900-2200)
- dateOfBirth: valid YYYY-MM-DD if provided
- employeeTypeCode: required, must match active EmployeeType in company
- departmentCode: required, must match active Department in company
- designationCode: required, must match active Designation in company
- gradeCode: must match active Grade if provided
- locationCode: must match active Location if provided
- shiftName: must match existing CompanyShift if provided
- costCentreCode: must match existing CostCentre if provided
- reportingManagerEmpId: must match existing non-EXITED Employee.employeeId if provided
- gender: must be one of MALE, FEMALE, NON_BINARY, PREFER_NOT_TO_SAY (case-insensitive mapping)
- maritalStatus: must be one of SINGLE, MARRIED, DIVORCED, WIDOWED
- workType: must be one of ON_SITE, REMOTE, HYBRID
- paymentMode: must be one of NEFT, IMPS, CHEQUE
- accountType: must be one of SAVINGS, CURRENT
- panNumber: 10 chars, format ABCDE1234F if provided
- aadhaarNumber: 12 digits if provided
- bankIfscCode: 11 chars if provided
- annualCtc: positive number if provided
- createAccount: Yes/No, defaults to Yes if empty
- role: must match existing RBAC Role name if provided; defaults to first non-system role

**Cross-row validation:**
- Duplicate personalEmail within file → error on all duplicate rows
- Duplicate officialEmail within file → error on all duplicate rows

**Master code resolution:**
- All code matching is case-insensitive
- Only Active status masters are accepted
- Resolved IDs are included in the validated row data (passed to import step)

---

### 3. `POST /hr/employees/bulk/import`

Create employees from previously validated data.

- **Auth:** `hr:create` permission
- **Content-Type:** `application/json`
- **Body:**

```json
{
  "rows": [ /* validated row objects from step 2 */ ],
  "defaultPassword": "Company@123"
}
```

- **Response:**

```json
{
  "success": true,
  "data": {
    "total": 47,
    "successCount": 45,
    "failureCount": 2,
    "results": [
      {
        "rowNum": 2,
        "success": true,
        "employeeId": "EMP00001",
        "firstName": "Rahul",
        "lastName": "Sharma",
        "email": "rahul@company.com",
        "accountCreated": true
      },
      {
        "rowNum": 5,
        "success": false,
        "error": "Number series exhausted for Employee"
      }
    ]
  }
}
```

#### Import Logic (per row)

Each row follows the same creation flow as single employee creation:

1. Generate employeeId via `generateNextNumber()` (atomic, transaction-safe)
2. Calculate probationEndDate from Designation.probationDays > Grade.probationMonths
3. Calculate noticePeriodDays from Grade.noticeDays
4. Create Employee record with status = PROBATION
5. Create JOINED timeline event
6. If createAccount = Yes:
   - Create User with `defaultPassword` (hashed), role = COMPANY_ADMIN platform role
   - Create TenantUser bridge with specified RBAC role
   - Link User.employeeId = employee.id
7. Auto-generate OnboardingTasks from default template (if exists)
8. Non-blocking post-creation: LeaveBalance init, ProbationReview, ITDeclaration

**Error isolation:** Each row is processed independently. One row's failure does not affect others. Errors are captured per-row and returned in results.

**Transaction strategy:** Each employee is created in its own transaction. This prevents a single failure from rolling back all employees while maintaining atomicity per employee.

---

## Template Columns (Sheet 1: "Employees")

| Col | Header | Required | Format | Maps To | Notes |
|-----|--------|----------|--------|---------|-------|
| A | First Name | Yes | Text | firstName | |
| B | Middle Name | No | Text | middleName | |
| C | Last Name | Yes | Text | lastName | |
| D | Date of Birth | No | YYYY-MM-DD | dateOfBirth | |
| E | Gender | No | Dropdown | gender | Male/Female/Other/Prefer Not to Say → MALE/FEMALE/NON_BINARY/PREFER_NOT_TO_SAY |
| F | Marital Status | No | Dropdown | maritalStatus | Single/Married/Divorced/Widowed |
| G | Blood Group | No | Text | bloodGroup | |
| H | Father/Mother Name | No | Text | fatherMotherName | |
| I | Nationality | No | Text | nationality | Default: Indian |
| J | Personal Mobile | Yes | 10+ digits | personalMobile | |
| K | Personal Email | Yes | Email | personalEmail | Unique per company |
| L | Official Email | Conditional | Email | officialEmail | Required if Create Account = Yes |
| M | Emergency Contact Name | Yes | Text | emergencyContactName | |
| N | Emergency Contact Relation | Yes | Text | emergencyContactRelation | |
| O | Emergency Contact Mobile | Yes | 10+ digits | emergencyContactMobile | |
| P | Joining Date | Yes | YYYY-MM-DD | joiningDate | |
| Q | Employee Type Code | Yes | From ref | employeeTypeId | Resolved via company EmployeeType |
| R | Department Code | Yes | From ref | departmentId | Resolved via company Department |
| S | Designation Code | Yes | From ref | designationId | Resolved via company Designation |
| T | Grade Code | No | From ref | gradeId | Resolved via company Grade |
| U | Location Code | No | From ref | locationId | Resolved via company Location |
| V | Shift Name | No | From ref | shiftId | Resolved via company CompanyShift |
| W | Cost Centre Code | No | From ref | costCentreId | Resolved via company CostCentre |
| X | Reporting Manager EmpID | No | Text | reportingManagerId | Must match existing Employee.employeeId |
| Y | Work Type | No | Dropdown | workType | ON_SITE/REMOTE/HYBRID |
| Z | Annual CTC | No | Number | annualCtc | Positive decimal |
| AA | Payment Mode | No | Dropdown | paymentMode | NEFT/IMPS/CHEQUE |
| AB | Salary Structure | No | From ref | salaryStructureId | Resolved via company SalaryStructure name |
| AC | Bank Account No | No | Text | bankAccountNumber | |
| AD | Bank IFSC | No | 11 chars | bankIfscCode | |
| AE | Bank Name | No | Text | bankName | |
| AF | Account Type | No | Dropdown | accountType | SAVINGS/CURRENT |
| AG | PAN | No | ABCDE1234F | panNumber | |
| AH | Aadhaar | No | 12 digits | aadhaarNumber | |
| AI | UAN | No | Text | uan | |
| AJ | ESI IP Number | No | Text | esiIpNumber | |
| AK | Create Account | No | Dropdown | createAccount | Yes/No, default: Yes |
| AL | Role | No | From ref | roleId | RBAC role name, default: first non-system role |

---

## Web UI

### Entry Point
- **Employee Directory screen** header: new "Bulk Import" button (icon: Upload) next to existing "Add Employee" button
- Permission-gated: only visible if user has `hr:create`

### Bulk Import Modal (3 steps)

**Step 1: Download Template**
- Heading: "Step 1: Download Template"
- Description: "Download the Excel template pre-populated with your company's master data. Fill in employee details and upload in the next step."
- Button: "Download Template" (triggers GET /bulk/template, saves file)
- Info box: "The template includes reference sheets for departments, designations, grades, and other master data."
- "Next" button to proceed

**Step 2: Upload & Validate**
- Heading: "Step 2: Upload & Validate"
- File dropzone: drag & drop or click to browse, accepts .xlsx only, max 10MB
- Password field: "Default Password for New Accounts" (required, min 6 chars, show/hide toggle)
- Helper text: "This password will be used for all employee login accounts. Employees should change it on first login."
- "Validate" button (disabled until file + password provided)
- Loading state: "Validating {n} rows..."
- Results display:
  - Summary bar: "{validCount} valid, {errorCount} errors out of {totalRows} rows"
  - Table with columns: Row #, Name, Status (green check / red X), Errors
  - Error rows highlighted in red with expandable error messages
  - "Re-upload" button to start over
  - "Import {validCount} Valid Rows" button (disabled if validCount = 0)

**Step 3: Import Results**
- Heading: "Step 3: Import Results"
- Loading state: "Creating employees... ({current}/{total})"
- Summary cards: Success count (green), Failed count (red)
- Results table: Row #, Employee ID, Name, Account Created (Yes/No), Status (success/error)
- "Done" button closes modal and refreshes employee list
- Optional: "Download Results" button to export results as xlsx

### UI Components
- Uses existing modal/dialog pattern from the web app
- Toast notifications: `showSuccess()` on completion, `showApiError()` on failure
- Consistent with existing Tailwind styling (primary=indigo, accent=violet)

---

## Mobile UI

### Entry Point
- **Employee Directory screen**: "Bulk Import" button in the gradient header area (next to search, or as a header-right action)
- Alternative: action in the FAB menu (if FAB supports multiple actions) or as a separate button below the search bar
- Permission-gated: `hr:create`

### Bulk Import Screen (Full-screen modal or pushed screen)

**Step 1: Download Template**
- Card with description text
- "Download Template" button → uses `expo-file-system` to download the xlsx, then `expo-sharing` to share/save the file
- Shows toast: "Template saved to Downloads" or opens share sheet
- "Next" button

**Step 2: Upload & Validate**
- File picker button: "Select Excel File" → opens `expo-document-picker` filtered to `.xlsx`
- Shows selected filename + file size after picking
- Password input: `TextInput` with show/hide toggle, label: "Default Password"
- "Validate" button
- Results displayed in a `FlatList`:
  - Summary section: valid/error counts with colored badges
  - Each row: employee name, status badge (Valid/Error), expandable error messages
  - Error rows show red border
- "Import Valid Rows" button at bottom (sticky)

**Step 3: Import Results**
- Summary cards at top: Success (green), Failed (red)
- `FlatList` of results: Row #, EmpID, Name, Account status, Success/Fail badge
- "Done" button → navigates back to Employee Directory (triggers refetch)

### Mobile-Specific Patterns
- Uses `@gorhom/bottom-sheet` for confirmation dialogs
- `ConfirmModal` for destructive actions (never `Alert.alert()`)
- Animations: `FadeInDown`, `FadeInUp` from reanimated
- Font: `font-inter` on all `<Text>` components
- Colors from `@/components/ui/colors`
- Safe area insets for padding
- LinearGradient header consistent with other screens

---

## Files to Create/Modify

### Backend (avy-erp-backend)
| Action | File | Purpose |
|--------|------|---------|
| Create | `src/modules/hr/employee/bulk-import.service.ts` | Template generation, Excel parsing, validation, import orchestration |
| Create | `src/modules/hr/employee/bulk-import.controller.ts` | Endpoint handlers with multer middleware |
| Create | `src/modules/hr/employee/bulk-import.validators.ts` | Zod schemas for upload validation |
| Modify | `src/modules/hr/employee/employee.routes.ts` | Mount bulk import routes under `/employees/bulk/*` |

### Web (web-system-app)
| Action | File | Purpose |
|--------|------|---------|
| Create | `src/features/company-admin/hr/BulkEmployeeImportModal.tsx` | 3-step import modal component |
| Modify | `src/features/company-admin/hr/EmployeeDirectoryScreen.tsx` | Add "Bulk Import" button |
| Modify | `src/features/company-admin/api/use-hr-mutations.ts` | Add bulk validate/import mutation hooks |
| Modify | `src/features/company-admin/api/use-hr-queries.ts` | Add template download query/function |

### Mobile (mobile-app)
| Action | File | Purpose |
|--------|------|---------|
| Create | `src/features/company-admin/hr/bulk-employee-import-screen.tsx` | 3-step import screen |
| Create | `src/app/(app)/hr/bulk-employee-import.tsx` | Route file (re-export) |
| Modify | `src/features/company-admin/hr/employee-directory-screen.tsx` | Add "Bulk Import" button |
| Modify | `src/features/company-admin/api/use-hr-mutations.ts` | Add bulk mutation hooks |
| Modify | `src/features/company-admin/api/use-hr-queries.ts` | Add template download function |

---

## Dependencies

### Already Installed (no new packages needed)
- **exceljs** `^4.4.0` — Excel generation and parsing
- **multer** `^1.4.5-lts.1` — File upload middleware
- **zod** `^3.22.4` — Validation

### Mobile (already installed)
- **expo-document-picker** — File selection
- **expo-file-system** — File download/save
- **expo-sharing** — Share downloaded files

---

## Constraints & Limits

- Max file size: 10MB
- Max rows per upload: 500
- Only `.xlsx` format accepted (no `.xls`, `.csv`)
- Only Active masters included in template and accepted during validation
- Each employee created in its own transaction (failure isolation)
- Rate limit: reuse existing API rate limits (no special limit needed since it's an authenticated admin action)
