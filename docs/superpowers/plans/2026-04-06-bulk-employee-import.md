# Bulk Employee Import — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add bulk employee onboarding via Excel upload with template download (pre-populated with company master data), row-by-row validation, and confirmed import — across backend, web, and mobile.

**Architecture:** Three new backend endpoints under `/hr/employees/bulk/*` (template download, validate, import). Template generated with ExcelJS using company's live master data as reference sheets + dropdown validations. Validation resolves master codes→IDs and returns per-row results. Import reuses existing `employeeService.createEmployee()` per row. Web gets a 3-step modal, mobile gets a 3-step full-screen.

**Tech Stack:** ExcelJS 4.4.0 (already installed), Multer 1.4.5 (already installed), Zod, React Query, expo-document-picker, expo-file-system, expo-sharing

**Spec:** `docs/superpowers/specs/2026-04-06-bulk-employee-import-design.md`

---

## File Structure

### Backend (avy-erp-backend)

| Action | File | Responsibility |
|--------|------|----------------|
| Create | `src/modules/hr/employee/bulk-import.service.ts` | Template generation (ExcelJS), Excel parsing, row validation, master code→ID resolution, import orchestration |
| Create | `src/modules/hr/employee/bulk-import.controller.ts` | 3 endpoint handlers: template download, validate upload, confirm import |
| Create | `src/modules/hr/employee/bulk-import.validators.ts` | Zod schema for per-row validation, upload body schema |
| Modify | `src/modules/hr/employee/employee.routes.ts` | Mount 3 bulk routes before `/:id` catch-all |

### Web (web-system-app)

| Action | File | Responsibility |
|--------|------|----------------|
| Create | `src/features/company-admin/hr/BulkEmployeeImportModal.tsx` | 3-step modal: download, validate, import |
| Modify | `src/features/company-admin/hr/EmployeeDirectoryScreen.tsx` | Add "Bulk Import" button in header |
| Modify | `src/features/company-admin/api/use-hr-mutations.ts` | Add `useBulkValidate()` and `useBulkImport()` mutation hooks |
| Modify | `src/features/company-admin/api/use-hr-queries.ts` | Add `downloadBulkTemplate()` helper function |

### Mobile (mobile-app)

| Action | File | Responsibility |
|--------|------|----------------|
| Create | `src/features/company-admin/hr/bulk-employee-import-screen.tsx` | 3-step full-screen: download, validate, import |
| Create | `src/app/(app)/hr/bulk-employee-import.tsx` | Route file (re-export) |
| Modify | `src/features/company-admin/hr/employee-directory-screen.tsx` | Add "Bulk Import" button in header |
| Modify | `src/features/company-admin/api/use-hr-mutations.ts` | Add `useBulkValidate()` and `useBulkImport()` mutation hooks |
| Modify | `src/features/company-admin/api/use-hr-queries.ts` | Add `downloadBulkTemplate()` helper function |

---

## Task 1: Backend — Bulk Import Validators

**Files:**
- Create: `avy-erp-backend/src/modules/hr/employee/bulk-import.validators.ts`

- [ ] **Step 1: Create the Zod schemas for bulk import validation**

```typescript
// src/modules/hr/employee/bulk-import.validators.ts
import { z } from 'zod';

// ── Per-row schema matching Excel columns ─────────────────────────────
export const bulkEmployeeRowSchema = z.object({
  // Personal (required)
  firstName: z.string().min(1, 'First name is required'),
  middleName: z.string().optional(),
  lastName: z.string().min(1, 'Last name is required'),
  dateOfBirth: z.string().optional(),
  gender: z.enum(['MALE', 'FEMALE', 'NON_BINARY', 'PREFER_NOT_TO_SAY']).optional(),
  maritalStatus: z.enum(['SINGLE', 'MARRIED', 'DIVORCED', 'WIDOWED']).optional(),
  bloodGroup: z.string().optional(),
  fatherMotherName: z.string().optional(),
  nationality: z.string().optional(),

  // Contact (required)
  personalMobile: z.string().min(10, 'Mobile must be at least 10 digits'),
  personalEmail: z.string().email('Invalid personal email'),
  officialEmail: z.string().email('Invalid official email').optional(),
  emergencyContactName: z.string().min(1, 'Emergency contact name is required'),
  emergencyContactRelation: z.string().min(1, 'Emergency contact relation is required'),
  emergencyContactMobile: z.string().min(10, 'Emergency contact mobile must be at least 10 digits'),

  // Professional (required codes — resolved to IDs later)
  joiningDate: z.string().min(1, 'Joining date is required'),
  employeeTypeCode: z.string().min(1, 'Employee type code is required'),
  departmentCode: z.string().min(1, 'Department code is required'),
  designationCode: z.string().min(1, 'Designation code is required'),
  gradeCode: z.string().optional(),
  locationCode: z.string().optional(),
  shiftName: z.string().optional(),
  costCentreCode: z.string().optional(),
  reportingManagerEmpId: z.string().optional(),
  workType: z.enum(['ON_SITE', 'REMOTE', 'HYBRID']).optional(),

  // Salary
  annualCtc: z.number().positive().optional(),
  paymentMode: z.enum(['NEFT', 'IMPS', 'CHEQUE']).optional(),
  salaryStructureName: z.string().optional(),

  // Bank
  bankAccountNumber: z.string().optional(),
  bankIfscCode: z.string().optional(),
  bankName: z.string().optional(),
  accountType: z.enum(['SAVINGS', 'CURRENT']).optional(),

  // Statutory
  panNumber: z.string().optional(),
  aadhaarNumber: z.string().optional(),
  uan: z.string().optional(),
  esiIpNumber: z.string().optional(),

  // User account
  createAccount: z.boolean().default(true),
  roleName: z.string().optional(),
});

// ── Upload body schema ────────────────────────────────────────────────
export const bulkValidateBodySchema = z.object({
  defaultPassword: z.string().min(6, 'Default password must be at least 6 characters'),
});

// ── Import body schema ────────────────────────────────────────────────
export const bulkImportBodySchema = z.object({
  defaultPassword: z.string().min(6, 'Default password must be at least 6 characters'),
  rows: z.array(z.record(z.any())).min(1, 'At least one valid row is required'),
});

// ── Column mapping: Excel header → row field name ─────────────────────
export const EXCEL_COLUMN_MAP: { header: string; key: string; required: boolean }[] = [
  { header: 'First Name', key: 'firstName', required: true },
  { header: 'Middle Name', key: 'middleName', required: false },
  { header: 'Last Name', key: 'lastName', required: true },
  { header: 'Date of Birth', key: 'dateOfBirth', required: false },
  { header: 'Gender', key: 'gender', required: false },
  { header: 'Marital Status', key: 'maritalStatus', required: false },
  { header: 'Blood Group', key: 'bloodGroup', required: false },
  { header: 'Father/Mother Name', key: 'fatherMotherName', required: false },
  { header: 'Nationality', key: 'nationality', required: false },
  { header: 'Personal Mobile', key: 'personalMobile', required: true },
  { header: 'Personal Email', key: 'personalEmail', required: true },
  { header: 'Official Email', key: 'officialEmail', required: false },
  { header: 'Emergency Contact Name', key: 'emergencyContactName', required: true },
  { header: 'Emergency Contact Relation', key: 'emergencyContactRelation', required: true },
  { header: 'Emergency Contact Mobile', key: 'emergencyContactMobile', required: true },
  { header: 'Joining Date', key: 'joiningDate', required: true },
  { header: 'Employee Type Code', key: 'employeeTypeCode', required: true },
  { header: 'Department Code', key: 'departmentCode', required: true },
  { header: 'Designation Code', key: 'designationCode', required: true },
  { header: 'Grade Code', key: 'gradeCode', required: false },
  { header: 'Location Code', key: 'locationCode', required: false },
  { header: 'Shift Name', key: 'shiftName', required: false },
  { header: 'Cost Centre Code', key: 'costCentreCode', required: false },
  { header: 'Reporting Manager EmpID', key: 'reportingManagerEmpId', required: false },
  { header: 'Work Type', key: 'workType', required: false },
  { header: 'Annual CTC', key: 'annualCtc', required: false },
  { header: 'Payment Mode', key: 'paymentMode', required: false },
  { header: 'Salary Structure', key: 'salaryStructureName', required: false },
  { header: 'Bank Account No', key: 'bankAccountNumber', required: false },
  { header: 'Bank IFSC', key: 'bankIfscCode', required: false },
  { header: 'Bank Name', key: 'bankName', required: false },
  { header: 'Account Type', key: 'accountType', required: false },
  { header: 'PAN', key: 'panNumber', required: false },
  { header: 'Aadhaar', key: 'aadhaarNumber', required: false },
  { header: 'UAN', key: 'uan', required: false },
  { header: 'ESI IP Number', key: 'esiIpNumber', required: false },
  { header: 'Create Account', key: 'createAccount', required: false },
  { header: 'Role', key: 'roleName', required: false },
];

// ── Human-friendly enum mappings for Excel ────────────────────────────
export const GENDER_MAP: Record<string, string> = {
  'male': 'MALE',
  'female': 'FEMALE',
  'other': 'NON_BINARY',
  'prefer not to say': 'PREFER_NOT_TO_SAY',
};

export const MARITAL_STATUS_MAP: Record<string, string> = {
  'single': 'SINGLE',
  'married': 'MARRIED',
  'divorced': 'DIVORCED',
  'widowed': 'WIDOWED',
};

export const WORK_TYPE_MAP: Record<string, string> = {
  'on_site': 'ON_SITE', 'on-site': 'ON_SITE', 'onsite': 'ON_SITE',
  'remote': 'REMOTE',
  'hybrid': 'HYBRID',
};

export const PAYMENT_MODE_MAP: Record<string, string> = {
  'neft': 'NEFT', 'imps': 'IMPS', 'cheque': 'CHEQUE',
};

export const ACCOUNT_TYPE_MAP: Record<string, string> = {
  'savings': 'SAVINGS', 'current': 'CURRENT',
};

export const YES_NO_MAP: Record<string, boolean> = {
  'yes': true, 'y': true, '1': true, 'true': true,
  'no': false, 'n': false, '0': false, 'false': false,
};
```

- [ ] **Step 2: Verify file compiles**

Run: `cd avy-erp-backend && npx tsc --noEmit 2>&1 | head -5`
Expected: No errors

- [ ] **Step 3: Commit**

```bash
git add src/modules/hr/employee/bulk-import.validators.ts
git commit -m "feat(bulk-import): add Zod schemas and column mapping for bulk employee import"
```

---

## Task 2: Backend — Bulk Import Service (Template Generation)

**Files:**
- Create: `avy-erp-backend/src/modules/hr/employee/bulk-import.service.ts`

- [ ] **Step 1: Create the service with template generation method**

This method fetches all active master data for the company and generates a multi-sheet Excel workbook with dropdown validations.

```typescript
// src/modules/hr/employee/bulk-import.service.ts
import * as ExcelJS from 'exceljs';
import { platformPrisma } from '../../../config/database';
import { logger } from '../../../config/logger';
import { ApiError } from '../../../shared/errors';
import { EXCEL_COLUMN_MAP, GENDER_MAP, MARITAL_STATUS_MAP, WORK_TYPE_MAP, PAYMENT_MODE_MAP, ACCOUNT_TYPE_MAP, YES_NO_MAP, bulkEmployeeRowSchema } from './bulk-import.validators';
import { HEADER_FILL, HEADER_FONT, ALT_ROW_FILL } from '../../hr/analytics/exports/excel-exporter';
import { employeeService } from './employee.service';

class BulkImportService {
  /**
   * Generate Excel template pre-populated with the company's active master data.
   * Reference sheets provide code lookups; Employees sheet has dropdown validations.
   */
  async generateTemplate(companyId: string): Promise<ExcelJS.Workbook> {
    // Fetch all active master data in parallel
    const [departments, designations, grades, employeeTypes, locations, shifts, costCentres, roles, salaryStructures, company] = await Promise.all([
      platformPrisma.department.findMany({ where: { companyId, status: 'Active' }, select: { code: true, name: true }, orderBy: { name: 'asc' } }),
      platformPrisma.designation.findMany({ where: { companyId, status: 'Active' }, select: { code: true, name: true, departmentId: true, gradeId: true, probationDays: true }, orderBy: { name: 'asc' } }),
      platformPrisma.grade.findMany({ where: { companyId, status: 'Active' }, select: { code: true, name: true, probationMonths: true, noticeDays: true, ctcMin: true, ctcMax: true }, orderBy: { name: 'asc' } }),
      platformPrisma.employeeType.findMany({ where: { companyId, status: 'Active' }, select: { code: true, name: true, pfApplicable: true, esiApplicable: true, ptApplicable: true }, orderBy: { name: 'asc' } }),
      platformPrisma.location.findMany({ where: { companyId, status: 'Active' }, select: { code: true, name: true, city: true, state: true }, orderBy: { name: 'asc' } }),
      platformPrisma.companyShift.findMany({ where: { companyId }, select: { name: true, startTime: true, endTime: true, shiftType: true }, orderBy: { name: 'asc' } }),
      platformPrisma.costCentre.findMany({ where: { companyId }, select: { code: true, name: true }, orderBy: { name: 'asc' } }),
      platformPrisma.role.findMany({
        where: { tenantId: (await platformPrisma.company.findUnique({ where: { id: companyId }, select: { tenant: { select: { id: true } } } }))?.tenant?.id, isSystem: false },
        select: { name: true },
        orderBy: { name: 'asc' },
      }),
      platformPrisma.salaryStructure.findMany({ where: { companyId, isActive: true }, select: { name: true, code: true }, orderBy: { name: 'asc' } }),
      platformPrisma.company.findUnique({ where: { id: companyId }, select: { shortName: true, name: true } }),
    ]);

    const wb = new ExcelJS.Workbook();
    wb.creator = 'Avy ERP';
    wb.created = new Date();

    // ── Sheet 1: Employees (input sheet) ──────────────────────────────
    const empSheet = wb.addWorksheet('Employees', { views: [{ state: 'frozen', ySplit: 1 }] });

    // Headers
    const headerRow = empSheet.addRow(EXCEL_COLUMN_MAP.map(c => c.header));
    headerRow.eachCell((cell) => {
      cell.fill = HEADER_FILL;
      cell.font = HEADER_FONT;
      cell.alignment = { vertical: 'middle', horizontal: 'center', wrapText: true };
    });

    // Column widths
    EXCEL_COLUMN_MAP.forEach((col, i) => {
      empSheet.getColumn(i + 1).width = col.key.includes('Email') ? 28 : col.key.includes('Name') ? 20 : 18;
    });

    // Example row (gray italic — to be deleted by user)
    const exampleData = [
      'Rahul', '', 'Sharma', '1995-06-15', 'Male', 'Single', 'O+', 'Ramesh Sharma',
      'Indian', '9876543210', 'rahul@example.com', 'rahul@company.com',
      'Priya Sharma', 'Spouse', '9876543211', '2026-04-01',
      departments[0]?.code ?? 'HR-001', departments[0]?.code ?? 'HR-001',
      designations[0]?.code ?? 'SE-001', grades[0]?.code ?? 'G1',
      locations[0]?.code ?? '', shifts[0]?.name ?? '', costCentres[0]?.code ?? '',
      '', 'ON_SITE', '600000', 'NEFT', salaryStructures[0]?.name ?? '',
      '1234567890', 'SBIN0001234', 'State Bank of India', 'SAVINGS',
      'ABCDE1234F', '123456789012', '', '', 'Yes', roles[0]?.name ?? 'Employee',
    ];
    const exRow = empSheet.addRow(exampleData);
    exRow.eachCell((cell) => {
      cell.font = { italic: true, color: { argb: 'FF9CA3AF' } };
    });
    empSheet.getCell('A2').note = '⬅ Example row — delete before uploading';

    // ── Dropdown validations on enum columns ──────────────────────────
    const maxRows = 502; // header + example + 500 data rows
    const addDropdown = (colIndex: number, values: string[]) => {
      if (values.length === 0) return;
      const colLetter = empSheet.getColumn(colIndex).letter;
      for (let r = 3; r <= maxRows; r++) {
        empSheet.getCell(`${colLetter}${r}`).dataValidation = {
          type: 'list',
          allowBlank: true,
          formulae: [`"${values.join(',')}"`],
          showErrorMessage: true,
          errorTitle: 'Invalid value',
          error: `Must be one of: ${values.join(', ')}`,
        };
      }
    };

    // Find column index (1-based) by key
    const colIdx = (key: string) => EXCEL_COLUMN_MAP.findIndex(c => c.key === key) + 1;

    addDropdown(colIdx('gender'), ['Male', 'Female', 'Other', 'Prefer Not to Say']);
    addDropdown(colIdx('maritalStatus'), ['Single', 'Married', 'Divorced', 'Widowed']);
    addDropdown(colIdx('workType'), ['ON_SITE', 'REMOTE', 'HYBRID']);
    addDropdown(colIdx('paymentMode'), ['NEFT', 'IMPS', 'CHEQUE']);
    addDropdown(colIdx('accountType'), ['SAVINGS', 'CURRENT']);
    addDropdown(colIdx('createAccount'), ['Yes', 'No']);

    // Master-data dropdowns
    if (employeeTypes.length > 0) addDropdown(colIdx('employeeTypeCode'), employeeTypes.map(e => e.code));
    if (departments.length > 0) addDropdown(colIdx('departmentCode'), departments.map(d => d.code));
    if (designations.length > 0) addDropdown(colIdx('designationCode'), designations.map(d => d.code));
    if (grades.length > 0) addDropdown(colIdx('gradeCode'), grades.map(g => g.code));
    if (locations.length > 0) addDropdown(colIdx('locationCode'), locations.map(l => l.code));
    if (shifts.length > 0) addDropdown(colIdx('shiftName'), shifts.map(s => s.name));
    if (costCentres.length > 0) addDropdown(colIdx('costCentreCode'), costCentres.map(c => c.code));
    if (roles.length > 0) addDropdown(colIdx('roleName'), roles.map(r => r.name));
    if (salaryStructures.length > 0) addDropdown(colIdx('salaryStructureName'), salaryStructures.map(s => s.name));

    // ── Reference Sheets ──────────────────────────────────────────────
    const addRefSheet = (name: string, columns: { header: string; key: string; width: number }[], data: Record<string, unknown>[]) => {
      const sheet = wb.addWorksheet(name);
      const hRow = sheet.addRow(columns.map(c => c.header));
      hRow.eachCell((cell) => {
        cell.fill = HEADER_FILL;
        cell.font = HEADER_FONT;
        cell.alignment = { vertical: 'middle', horizontal: 'center' };
      });
      columns.forEach((col, i) => { sheet.getColumn(i + 1).width = col.width; });
      data.forEach((row, ri) => {
        const r = sheet.addRow(columns.map(c => row[c.key] ?? ''));
        if (ri % 2 === 1) r.eachCell((cell) => { cell.fill = ALT_ROW_FILL; });
      });
      sheet.protect('', { selectLockedCells: true, selectUnlockedCells: true });
    };

    addRefSheet('Departments', [
      { header: 'Code', key: 'code', width: 15 },
      { header: 'Name', key: 'name', width: 30 },
    ], departments);

    addRefSheet('Designations', [
      { header: 'Code', key: 'code', width: 15 },
      { header: 'Name', key: 'name', width: 30 },
      { header: 'Probation Days', key: 'probationDays', width: 16 },
    ], designations.map(d => ({ ...d, probationDays: d.probationDays ?? '' })));

    addRefSheet('Grades', [
      { header: 'Code', key: 'code', width: 15 },
      { header: 'Name', key: 'name', width: 30 },
      { header: 'Probation Months', key: 'probationMonths', width: 18 },
      { header: 'Notice Days', key: 'noticeDays', width: 14 },
      { header: 'CTC Min', key: 'ctcMin', width: 14 },
      { header: 'CTC Max', key: 'ctcMax', width: 14 },
    ], grades.map(g => ({ ...g, probationMonths: g.probationMonths ?? '', noticeDays: g.noticeDays ?? '', ctcMin: g.ctcMin ? Number(g.ctcMin) : '', ctcMax: g.ctcMax ? Number(g.ctcMax) : '' })));

    addRefSheet('Employee Types', [
      { header: 'Code', key: 'code', width: 15 },
      { header: 'Name', key: 'name', width: 25 },
      { header: 'PF', key: 'pfApplicable', width: 8 },
      { header: 'ESI', key: 'esiApplicable', width: 8 },
      { header: 'PT', key: 'ptApplicable', width: 8 },
    ], employeeTypes.map(e => ({ ...e, pfApplicable: e.pfApplicable ? 'Yes' : 'No', esiApplicable: e.esiApplicable ? 'Yes' : 'No', ptApplicable: e.ptApplicable ? 'Yes' : 'No' })));

    addRefSheet('Locations', [
      { header: 'Code', key: 'code', width: 15 },
      { header: 'Name', key: 'name', width: 25 },
      { header: 'City', key: 'city', width: 20 },
      { header: 'State', key: 'state', width: 20 },
    ], locations);

    addRefSheet('Shifts', [
      { header: 'Name', key: 'name', width: 25 },
      { header: 'Start', key: 'startTime', width: 12 },
      { header: 'End', key: 'endTime', width: 12 },
      { header: 'Type', key: 'shiftType', width: 12 },
    ], shifts);

    addRefSheet('Cost Centres', [
      { header: 'Code', key: 'code', width: 15 },
      { header: 'Name', key: 'name', width: 30 },
    ], costCentres);

    addRefSheet('Roles', [
      { header: 'Name', key: 'name', width: 30 },
    ], roles);

    addRefSheet('Salary Structures', [
      { header: 'Name', key: 'name', width: 30 },
      { header: 'Code', key: 'code', width: 15 },
    ], salaryStructures);

    // ── Instructions Sheet ────────────────────────────────────────────
    const instrSheet = wb.addWorksheet('Instructions');
    instrSheet.getColumn(1).width = 25;
    instrSheet.getColumn(2).width = 12;
    instrSheet.getColumn(3).width = 60;

    const instrHeader = instrSheet.addRow(['Column', 'Required', 'Description']);
    instrHeader.eachCell((cell) => { cell.fill = HEADER_FILL; cell.font = HEADER_FONT; });

    EXCEL_COLUMN_MAP.forEach((col) => {
      instrSheet.addRow([col.header, col.required ? 'Yes' : 'No', getFieldDescription(col.key)]);
    });

    instrSheet.addRow([]);
    instrSheet.addRow(['NOTES:']);
    instrSheet.addRow(['', '', 'Delete the example row (row 2) before uploading.']);
    instrSheet.addRow(['', '', 'Use codes from the reference sheets (Departments, Designations, etc.).']);
    instrSheet.addRow(['', '', 'Dates must be in YYYY-MM-DD format.']);
    instrSheet.addRow(['', '', 'Create Account defaults to Yes. Set to No to skip user account creation.']);
    instrSheet.addRow(['', '', 'Max 500 rows per upload.']);

    return wb;
  }

  /**
   * Parse uploaded Excel file and validate each row against company master data.
   * Returns per-row validation results without creating any records.
   */
  async validateUpload(companyId: string, fileBuffer: Buffer, defaultPassword: string) {
    const wb = new ExcelJS.Workbook();
    await wb.xlsx.load(fileBuffer);

    const sheet = wb.getWorksheet('Employees') || wb.getWorksheet(1);
    if (!sheet) throw ApiError.badRequest('Excel file must have an "Employees" sheet');

    // Build header→column index map from row 1
    const headerMap: Record<string, number> = {};
    const headerRow = sheet.getRow(1);
    headerRow.eachCell((cell, colNumber) => {
      const val = String(cell.value ?? '').trim();
      headerMap[val] = colNumber;
    });

    // Fetch master data for resolution (case-insensitive maps)
    const [departments, designations, grades, employeeTypes, locations, shifts, costCentres, roles, salaryStructures, existingEmails, existingOfficialEmails, existingEmployees] = await Promise.all([
      platformPrisma.department.findMany({ where: { companyId, status: 'Active' }, select: { id: true, code: true } }),
      platformPrisma.designation.findMany({ where: { companyId, status: 'Active' }, select: { id: true, code: true } }),
      platformPrisma.grade.findMany({ where: { companyId, status: 'Active' }, select: { id: true, code: true } }),
      platformPrisma.employeeType.findMany({ where: { companyId, status: 'Active' }, select: { id: true, code: true } }),
      platformPrisma.location.findMany({ where: { companyId, status: 'Active' }, select: { id: true, code: true } }),
      platformPrisma.companyShift.findMany({ where: { companyId }, select: { id: true, name: true } }),
      platformPrisma.costCentre.findMany({ where: { companyId }, select: { id: true, code: true } }),
      platformPrisma.role.findMany({
        where: { tenantId: (await platformPrisma.company.findUnique({ where: { id: companyId }, select: { tenant: { select: { id: true } } } }))?.tenant?.id },
        select: { id: true, name: true, isSystem: true },
      }),
      platformPrisma.salaryStructure.findMany({ where: { companyId, isActive: true }, select: { id: true, name: true } }),
      platformPrisma.employee.findMany({ where: { companyId, status: { not: 'EXITED' } }, select: { personalEmail: true } }),
      platformPrisma.employee.findMany({ where: { companyId, status: { not: 'EXITED' }, officialEmail: { not: null } }, select: { officialEmail: true } }),
      platformPrisma.employee.findMany({ where: { companyId, status: { not: 'EXITED' } }, select: { employeeId: true } }),
    ]);

    // Build case-insensitive lookup maps
    const deptMap = new Map(departments.map(d => [d.code.toLowerCase(), d.id]));
    const desigMap = new Map(designations.map(d => [d.code.toLowerCase(), d.id]));
    const gradeMap = new Map(grades.map(g => [g.code.toLowerCase(), g.id]));
    const empTypeMap = new Map(employeeTypes.map(e => [e.code.toLowerCase(), e.id]));
    const locMap = new Map(locations.map(l => [l.code.toLowerCase(), l.id]));
    const shiftMap = new Map(shifts.map(s => [s.name.toLowerCase(), s.id]));
    const ccMap = new Map(costCentres.map(c => [c.code.toLowerCase(), c.id]));
    const roleMap = new Map(roles.filter(r => !r.isSystem).map(r => [r.name.toLowerCase(), r.id]));
    const defaultRoleId = roles.find(r => !r.isSystem)?.id ?? roles.find(r => r.isSystem)?.id ?? null;
    const salStructMap = new Map(salaryStructures.map(s => [s.name.toLowerCase(), s.id]));

    const existingPersonalEmails = new Set(existingEmails.map(e => e.personalEmail?.toLowerCase()));
    const existingOfficialEmailSet = new Set(existingOfficialEmails.map(e => e.officialEmail?.toLowerCase()).filter(Boolean));
    const existingEmpIds = new Set(existingEmployees.map(e => e.employeeId));

    // Parse rows
    const rows: { rowNum: number; valid: boolean; data?: Record<string, unknown>; errors?: string[] }[] = [];
    const filePersonalEmails = new Map<string, number[]>(); // email → row numbers
    const fileOfficialEmails = new Map<string, number[]>();

    const totalRows = sheet.rowCount;
    if (totalRows < 2) throw ApiError.badRequest('No data rows found in the Excel file');
    if (totalRows > 502) throw ApiError.badRequest('Maximum 500 data rows allowed per upload');

    for (let rowNum = 2; rowNum <= totalRows; rowNum++) {
      const row = sheet.getRow(rowNum);
      if (!row.hasValues) continue;

      // Skip the example row (check if first cell is italic or contains "(Example")
      const firstCellValue = String(row.getCell(1).value ?? '').trim();
      if (firstCellValue === '' || firstCellValue.startsWith('(Example')) continue;

      const rawData: Record<string, unknown> = {};
      EXCEL_COLUMN_MAP.forEach((col) => {
        const colNum = headerMap[col.header];
        if (!colNum) return;
        let val = row.getCell(colNum).value;
        // Handle ExcelJS date objects
        if (val instanceof Date) {
          val = val.toISOString().split('T')[0]; // YYYY-MM-DD
        }
        if (val !== null && val !== undefined && val !== '') {
          rawData[col.key] = typeof val === 'string' ? val.trim() : val;
        }
      });

      // Map human-friendly enum values
      if (rawData.gender) rawData.gender = GENDER_MAP[String(rawData.gender).toLowerCase()] ?? rawData.gender;
      if (rawData.maritalStatus) rawData.maritalStatus = MARITAL_STATUS_MAP[String(rawData.maritalStatus).toLowerCase()] ?? rawData.maritalStatus;
      if (rawData.workType) rawData.workType = WORK_TYPE_MAP[String(rawData.workType).toLowerCase()] ?? rawData.workType;
      if (rawData.paymentMode) rawData.paymentMode = PAYMENT_MODE_MAP[String(rawData.paymentMode).toLowerCase()] ?? rawData.paymentMode;
      if (rawData.accountType) rawData.accountType = ACCOUNT_TYPE_MAP[String(rawData.accountType).toLowerCase()] ?? rawData.accountType;

      // Parse createAccount
      const createAccountRaw = String(rawData.createAccount ?? 'yes').toLowerCase();
      rawData.createAccount = YES_NO_MAP[createAccountRaw] ?? true;

      // Parse annualCtc as number
      if (rawData.annualCtc) rawData.annualCtc = Number(rawData.annualCtc);

      // Validate with Zod
      const errors: string[] = [];
      const parsed = bulkEmployeeRowSchema.safeParse(rawData);
      if (!parsed.success) {
        parsed.error.errors.forEach(e => errors.push(`${e.path.join('.')}: ${e.message}`));
      }

      // Resolve master codes → IDs
      const resolvedData: Record<string, unknown> = { ...rawData, rowNum };

      if (rawData.employeeTypeCode) {
        const id = empTypeMap.get(String(rawData.employeeTypeCode).toLowerCase());
        if (!id) errors.push(`Employee type code '${rawData.employeeTypeCode}' not found`);
        else resolvedData.employeeTypeId = id;
      }
      if (rawData.departmentCode) {
        const id = deptMap.get(String(rawData.departmentCode).toLowerCase());
        if (!id) errors.push(`Department code '${rawData.departmentCode}' not found`);
        else resolvedData.departmentId = id;
      }
      if (rawData.designationCode) {
        const id = desigMap.get(String(rawData.designationCode).toLowerCase());
        if (!id) errors.push(`Designation code '${rawData.designationCode}' not found`);
        else resolvedData.designationId = id;
      }
      if (rawData.gradeCode) {
        const id = gradeMap.get(String(rawData.gradeCode).toLowerCase());
        if (!id) errors.push(`Grade code '${rawData.gradeCode}' not found`);
        else resolvedData.gradeId = id;
      }
      if (rawData.locationCode) {
        const id = locMap.get(String(rawData.locationCode).toLowerCase());
        if (!id) errors.push(`Location code '${rawData.locationCode}' not found`);
        else resolvedData.locationId = id;
      }
      if (rawData.shiftName) {
        const id = shiftMap.get(String(rawData.shiftName).toLowerCase());
        if (!id) errors.push(`Shift '${rawData.shiftName}' not found`);
        else resolvedData.shiftId = id;
      }
      if (rawData.costCentreCode) {
        const id = ccMap.get(String(rawData.costCentreCode).toLowerCase());
        if (!id) errors.push(`Cost centre code '${rawData.costCentreCode}' not found`);
        else resolvedData.costCentreId = id;
      }
      if (rawData.reportingManagerEmpId) {
        if (!existingEmpIds.has(String(rawData.reportingManagerEmpId))) {
          errors.push(`Reporting manager EmpID '${rawData.reportingManagerEmpId}' not found`);
        } else {
          const mgr = await platformPrisma.employee.findFirst({
            where: { companyId, employeeId: String(rawData.reportingManagerEmpId), status: { not: 'EXITED' } },
            select: { id: true },
          });
          if (mgr) resolvedData.reportingManagerId = mgr.id;
        }
      }
      if (rawData.roleName) {
        const id = roleMap.get(String(rawData.roleName).toLowerCase());
        if (!id) errors.push(`Role '${rawData.roleName}' not found`);
        else resolvedData.userRole = id;
      } else {
        resolvedData.userRole = defaultRoleId;
      }
      if (rawData.salaryStructureName) {
        const id = salStructMap.get(String(rawData.salaryStructureName).toLowerCase());
        if (!id) errors.push(`Salary structure '${rawData.salaryStructureName}' not found`);
        // Note: salaryStructure on Employee is JSON, this is for EmployeeSalary — store reference for import step
        else resolvedData.salaryStructureId = id;
      }

      // Check createAccount requires officialEmail
      if (rawData.createAccount === true && !rawData.officialEmail) {
        errors.push('Official email is required when Create Account is Yes');
      }

      // Track emails for cross-row duplicate check
      const pe = String(rawData.personalEmail ?? '').toLowerCase();
      if (pe) {
        if (!filePersonalEmails.has(pe)) filePersonalEmails.set(pe, []);
        filePersonalEmails.get(pe)!.push(rowNum);
      }
      const oe = String(rawData.officialEmail ?? '').toLowerCase();
      if (oe) {
        if (!fileOfficialEmails.has(oe)) fileOfficialEmails.set(oe, []);
        fileOfficialEmails.get(oe)!.push(rowNum);
      }

      // Check against existing DB emails
      if (pe && existingPersonalEmails.has(pe)) {
        errors.push(`Personal email '${rawData.personalEmail}' already exists in company`);
      }
      if (oe && existingOfficialEmailSet.has(oe)) {
        errors.push(`Official email '${rawData.officialEmail}' already exists in company`);
      }

      rows.push({
        rowNum,
        valid: errors.length === 0,
        data: errors.length === 0 ? resolvedData : undefined,
        errors: errors.length > 0 ? errors : undefined,
      });
    }

    // Cross-row duplicate check
    for (const [email, rowNums] of filePersonalEmails) {
      if (rowNums.length > 1) {
        rowNums.forEach(rn => {
          const row = rows.find(r => r.rowNum === rn);
          if (row) {
            if (!row.errors) row.errors = [];
            row.errors.push(`Duplicate personal email '${email}' in rows ${rowNums.join(', ')}`);
            row.valid = false;
            row.data = undefined;
          }
        });
      }
    }
    for (const [email, rowNums] of fileOfficialEmails) {
      if (rowNums.length > 1) {
        rowNums.forEach(rn => {
          const row = rows.find(r => r.rowNum === rn);
          if (row) {
            if (!row.errors) row.errors = [];
            row.errors.push(`Duplicate official email '${email}' in rows ${rowNums.join(', ')}`);
            row.valid = false;
            row.data = undefined;
          }
        });
      }
    }

    const validCount = rows.filter(r => r.valid).length;
    const errorCount = rows.filter(r => !r.valid).length;

    return { totalRows: rows.length, validCount, errorCount, rows };
  }

  /**
   * Import validated rows — creates employees using the existing employeeService.createEmployee().
   * Each row is processed in its own transaction for failure isolation.
   */
  async importRows(companyId: string, validatedRows: Record<string, unknown>[], defaultPassword: string, performedBy?: string) {
    const results: { rowNum: number; success: boolean; employeeId?: string; firstName?: string; lastName?: string; email?: string; accountCreated?: boolean; error?: string }[] = [];
    let successCount = 0;
    let failureCount = 0;

    for (const row of validatedRows) {
      try {
        // Build data matching createEmployeeWithUserSchema
        const employeeData: Record<string, unknown> = {
          firstName: row.firstName,
          middleName: row.middleName,
          lastName: row.lastName,
          dateOfBirth: row.dateOfBirth,
          gender: row.gender,
          maritalStatus: row.maritalStatus,
          bloodGroup: row.bloodGroup,
          fatherMotherName: row.fatherMotherName,
          nationality: row.nationality ?? 'Indian',
          personalMobile: String(row.personalMobile),
          personalEmail: row.personalEmail,
          officialEmail: row.officialEmail,
          emergencyContactName: row.emergencyContactName,
          emergencyContactRelation: row.emergencyContactRelation,
          emergencyContactMobile: String(row.emergencyContactMobile),
          joiningDate: row.joiningDate,
          employeeTypeId: row.employeeTypeId,
          departmentId: row.departmentId,
          designationId: row.designationId,
          gradeId: row.gradeId,
          locationId: row.locationId,
          shiftId: row.shiftId,
          costCentreId: row.costCentreId,
          reportingManagerId: row.reportingManagerId,
          workType: row.workType,
          annualCtc: row.annualCtc,
          paymentMode: row.paymentMode,
          bankAccountNumber: row.bankAccountNumber,
          bankIfscCode: row.bankIfscCode,
          bankName: row.bankName,
          accountType: row.accountType,
          panNumber: row.panNumber,
          aadhaarNumber: row.aadhaarNumber ? String(row.aadhaarNumber) : undefined,
          uan: row.uan,
          esiIpNumber: row.esiIpNumber,
          // User account
          createUserAccount: row.createAccount === true && !!row.officialEmail,
          userPassword: row.createAccount === true ? defaultPassword : undefined,
          userRole: row.userRole,
        };

        const employee = await employeeService.createEmployee(companyId, employeeData, performedBy);
        successCount++;
        results.push({
          rowNum: row.rowNum as number,
          success: true,
          employeeId: employee.employeeId,
          firstName: employee.firstName,
          lastName: employee.lastName,
          email: employee.officialEmail ?? employee.personalEmail,
          accountCreated: employeeData.createUserAccount as boolean,
        });
      } catch (err: any) {
        failureCount++;
        results.push({
          rowNum: row.rowNum as number,
          success: false,
          error: err.message || 'Unknown error',
        });
        logger.warn(`Bulk import row ${row.rowNum} failed:`, err.message);
      }
    }

    return { total: validatedRows.length, successCount, failureCount, results };
  }
}

// ── Helper: field descriptions for Instructions sheet ──────────────────
function getFieldDescription(key: string): string {
  const descriptions: Record<string, string> = {
    firstName: 'Employee first name (required)',
    middleName: 'Employee middle name',
    lastName: 'Employee last name (required)',
    dateOfBirth: 'Date of birth in YYYY-MM-DD format',
    gender: 'Male, Female, Other, or Prefer Not to Say',
    maritalStatus: 'Single, Married, Divorced, or Widowed',
    bloodGroup: 'Blood group (e.g., O+, A-, B+)',
    fatherMotherName: 'Father or mother name',
    nationality: 'Nationality (defaults to Indian)',
    personalMobile: 'Personal mobile number, min 10 digits (required)',
    personalEmail: 'Personal email address (required, must be unique)',
    officialEmail: 'Company email address (required if Create Account = Yes)',
    emergencyContactName: 'Emergency contact person name (required)',
    emergencyContactRelation: 'Relation to employee, e.g. Spouse, Parent (required)',
    emergencyContactMobile: 'Emergency contact mobile, min 10 digits (required)',
    joiningDate: 'Date of joining in YYYY-MM-DD format (required)',
    employeeTypeCode: 'Code from Employee Types reference sheet (required)',
    departmentCode: 'Code from Departments reference sheet (required)',
    designationCode: 'Code from Designations reference sheet (required)',
    gradeCode: 'Code from Grades reference sheet (optional)',
    locationCode: 'Code from Locations reference sheet (optional)',
    shiftName: 'Name from Shifts reference sheet (optional)',
    costCentreCode: 'Code from Cost Centres reference sheet (optional)',
    reportingManagerEmpId: 'Employee ID of reporting manager (must exist)',
    workType: 'ON_SITE, REMOTE, or HYBRID',
    annualCtc: 'Annual CTC in numbers (e.g., 600000)',
    paymentMode: 'NEFT, IMPS, or CHEQUE',
    salaryStructureName: 'Name from Salary Structures reference sheet',
    bankAccountNumber: 'Bank account number',
    bankIfscCode: 'Bank IFSC code (11 characters)',
    bankName: 'Bank name',
    accountType: 'SAVINGS or CURRENT',
    panNumber: 'PAN number (format: ABCDE1234F)',
    aadhaarNumber: 'Aadhaar number (12 digits)',
    uan: 'Universal Account Number (PF)',
    esiIpNumber: 'ESI IP Number',
    createAccount: 'Yes or No — create login account (defaults to Yes)',
    roleName: 'Role name from Roles reference sheet (defaults to first available role)',
  };
  return descriptions[key] ?? '';
}

export const bulkImportService = new BulkImportService();
```

- [ ] **Step 2: Verify file compiles**

Run: `cd avy-erp-backend && npx tsc --noEmit 2>&1 | head -10`
Expected: No errors

- [ ] **Step 3: Commit**

```bash
git add src/modules/hr/employee/bulk-import.service.ts
git commit -m "feat(bulk-import): add service with template generation, validation, and import logic"
```

---

## Task 3: Backend — Bulk Import Controller & Routes

**Files:**
- Create: `avy-erp-backend/src/modules/hr/employee/bulk-import.controller.ts`
- Modify: `avy-erp-backend/src/modules/hr/employee/employee.routes.ts`

- [ ] **Step 1: Create the controller with multer middleware**

```typescript
// src/modules/hr/employee/bulk-import.controller.ts
import { Request, Response } from 'express';
import multer from 'multer';
import { asyncHandler } from '../../../middleware/error.middleware';
import { ApiError } from '../../../shared/errors';
import { createSuccessResponse } from '../../../shared/utils';
import { bulkImportService } from './bulk-import.service';
import { bulkValidateBodySchema, bulkImportBodySchema } from './bulk-import.validators';

// Multer config: memory storage, 10MB limit, xlsx only
const upload = multer({
  storage: multer.memoryStorage(),
  limits: { fileSize: 10 * 1024 * 1024 }, // 10MB
  fileFilter: (_req, file, cb) => {
    const allowed = [
      'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
      'application/vnd.ms-excel',
    ];
    if (allowed.includes(file.mimetype) || file.originalname.endsWith('.xlsx')) {
      cb(null, true);
    } else {
      cb(new Error('Only .xlsx files are accepted'));
    }
  },
});

export const bulkUploadMiddleware = upload.single('file');

class BulkImportController {
  /**
   * GET /hr/employees/bulk/template
   * Download Excel template pre-populated with company master data.
   */
  downloadTemplate = asyncHandler(async (req: Request, res: Response) => {
    const companyId = req.user?.companyId;
    if (!companyId) throw ApiError.badRequest('Company ID is required');

    const workbook = await bulkImportService.generateTemplate(companyId);

    res.setHeader('Content-Type', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet');
    res.setHeader('Content-Disposition', 'attachment; filename="Employee_Import_Template.xlsx"');

    await workbook.xlsx.write(res);
    res.end();
  });

  /**
   * POST /hr/employees/bulk/validate
   * Upload Excel file and validate rows without creating records.
   * Expects multipart/form-data with 'file' and 'defaultPassword'.
   */
  validateUpload = asyncHandler(async (req: Request, res: Response) => {
    const companyId = req.user?.companyId;
    if (!companyId) throw ApiError.badRequest('Company ID is required');

    if (!req.file) throw ApiError.badRequest('No file uploaded');

    const parsed = bulkValidateBodySchema.safeParse(req.body);
    if (!parsed.success) {
      throw ApiError.badRequest(parsed.error.errors.map(e => e.message).join(', '));
    }

    const result = await bulkImportService.validateUpload(companyId, req.file.buffer, parsed.data.defaultPassword);
    res.json(createSuccessResponse(result, 'Validation complete'));
  });

  /**
   * POST /hr/employees/bulk/import
   * Create employees from previously validated rows.
   */
  confirmImport = asyncHandler(async (req: Request, res: Response) => {
    const companyId = req.user?.companyId;
    if (!companyId) throw ApiError.badRequest('Company ID is required');

    const parsed = bulkImportBodySchema.safeParse(req.body);
    if (!parsed.success) {
      throw ApiError.badRequest(parsed.error.errors.map(e => e.message).join(', '));
    }

    const performedBy = req.user?.id;
    const result = await bulkImportService.importRows(companyId, parsed.data.rows, parsed.data.defaultPassword, performedBy);
    res.json(createSuccessResponse(result, `Import complete: ${result.successCount} created, ${result.failureCount} failed`));
  });
}

export const bulkImportController = new BulkImportController();
```

- [ ] **Step 2: Mount bulk routes in employee.routes.ts**

Add the 3 bulk routes **before** the `/:id` catch-all route. In `employee.routes.ts`, add these lines after the org-chart route and before `router.get('/employees/:id', ...)`:

```typescript
// ── Bulk Import — MUST be before /:id catch-all ───────────────────────
import { bulkImportController, bulkUploadMiddleware } from './bulk-import.controller';

router.get('/employees/bulk/template', requirePermissions(['hr:create']), bulkImportController.downloadTemplate);
router.post('/employees/bulk/validate', requirePermissions(['hr:create']), bulkUploadMiddleware, bulkImportController.validateUpload);
router.post('/employees/bulk/import', requirePermissions(['hr:create']), bulkImportController.confirmImport);
```

The final route order should be:
1. `GET /employees` (list)
2. `POST /employees` (create)
3. `GET /employees/probation-due`
4. `GET /employees/org-chart`
5. `GET /employees/bulk/template` ← NEW
6. `POST /employees/bulk/validate` ← NEW
7. `POST /employees/bulk/import` ← NEW
8. `GET /employees/:id` (single — catch-all)
9. ... remaining /:id routes

- [ ] **Step 3: Verify backend compiles**

Run: `cd avy-erp-backend && npx tsc --noEmit 2>&1 | head -10`
Expected: No errors

- [ ] **Step 4: Commit**

```bash
git add src/modules/hr/employee/bulk-import.controller.ts src/modules/hr/employee/employee.routes.ts
git commit -m "feat(bulk-import): add controller with multer upload and mount bulk routes"
```

---

## Task 4: Web — API Hooks for Bulk Import

**Files:**
- Modify: `web-system-app/src/features/company-admin/api/use-hr-queries.ts`
- Modify: `web-system-app/src/features/company-admin/api/use-hr-mutations.ts`

- [ ] **Step 1: Read the current API files to find the axios client and patterns**

Read `use-hr-queries.ts` and `use-hr-mutations.ts` to understand the exact import paths and patterns used (axios instance, query key factories, mutation patterns).

- [ ] **Step 2: Add template download helper to use-hr-queries.ts**

Add at the bottom of the file:

```typescript
// ── Bulk Import ───────────────────────────────────────────────────────
export async function downloadBulkEmployeeTemplate() {
  const response = await hrApi.get('/employees/bulk/template', { responseType: 'blob' });
  const blob = new Blob([response], { type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' });
  const url = window.URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = 'Employee_Import_Template.xlsx';
  document.body.appendChild(a);
  a.click();
  window.URL.revokeObjectURL(url);
  document.body.removeChild(a);
}
```

Note: `hrApi` is the axios instance used in this file — check the actual import name. The `.then(r => r.data)` interceptor strips the axios wrapper, so for blob responses, the interceptor may need the response type to be handled. If the axios client has `.then(r => r.data)`, the blob will come through directly. If not, adjust accordingly.

- [ ] **Step 3: Add bulk validate and import mutations to use-hr-mutations.ts**

Add at the bottom of the file:

```typescript
// ── Bulk Import ───────────────────────────────────────────────────────
export function useBulkValidateEmployees() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async ({ file, defaultPassword }: { file: File; defaultPassword: string }) => {
      const formData = new FormData();
      formData.append('file', file);
      formData.append('defaultPassword', defaultPassword);
      return hrApi.post('/employees/bulk/validate', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });
    },
  });
}

export function useBulkImportEmployees() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async ({ rows, defaultPassword }: { rows: Record<string, unknown>[]; defaultPassword: string }) => {
      return hrApi.post('/employees/bulk/import', { rows, defaultPassword });
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: hrKeys.employees() });
    },
  });
}
```

- [ ] **Step 4: Verify web app compiles**

Run: `cd web-system-app && npx tsc --noEmit 2>&1 | head -10`
Expected: No errors

- [ ] **Step 5: Commit**

```bash
cd web-system-app && git add src/features/company-admin/api/use-hr-queries.ts src/features/company-admin/api/use-hr-mutations.ts
git commit -m "feat(bulk-import): add web API hooks for bulk validate and import"
```

---

## Task 5: Web — Bulk Import Modal Component

**Files:**
- Create: `web-system-app/src/features/company-admin/hr/BulkEmployeeImportModal.tsx`
- Modify: `web-system-app/src/features/company-admin/hr/EmployeeDirectoryScreen.tsx`

- [ ] **Step 1: Read EmployeeDirectoryScreen.tsx to understand the header layout and import patterns**

Read the full file to know where to add the Bulk Import button and what UI components/patterns are used.

- [ ] **Step 2: Create BulkEmployeeImportModal.tsx**

Build a 3-step modal component:
- Step 1: Download Template button
- Step 2: File upload dropzone + password field + Validate button → results table
- Step 3: Import results table with success/failure per row

Follow the existing web app patterns:
- Tailwind CSS (primary=indigo, accent=violet)
- `showSuccess()`, `showApiError()` from `@/lib/toast`
- Use the mutation hooks created in Task 4
- Use `downloadBulkEmployeeTemplate()` from Task 4

The component should accept `isOpen` and `onClose` props. Use existing modal/dialog patterns from the codebase.

Key UI elements:
- Step indicator (1/2/3) at the top
- File input accepting `.xlsx` only
- Password field with show/hide toggle
- Results table with columns: Row #, Name (firstName + lastName), Status (green check/red X), Errors (expandable)
- Summary bar: "X valid, Y errors out of Z rows"
- Action buttons: "Re-upload" (back to step 2), "Import X Valid Rows" (proceed to step 3)
- Final results: Employee ID, Name, Account Created (Yes/No badge), Status

- [ ] **Step 3: Add "Bulk Import" button to EmployeeDirectoryScreen.tsx**

Add a button next to the existing "Add Employee" button in the header area. Use the Upload icon from lucide-react. Gate behind `hr:create` permission using `useCanPerform('hr:create')`.

```tsx
import { Upload } from 'lucide-react';
import BulkEmployeeImportModal from './BulkEmployeeImportModal';

// In the component:
const [bulkImportOpen, setBulkImportOpen] = useState(false);

// In the header JSX (next to Add Employee button):
<button
  onClick={() => setBulkImportOpen(true)}
  className="flex items-center gap-2 rounded-lg border border-primary-200 bg-white px-4 py-2 text-sm font-medium text-primary-700 hover:bg-primary-50 transition-colors"
>
  <Upload className="h-4 w-4" />
  Bulk Import
</button>

// At the end of the component JSX:
<BulkEmployeeImportModal isOpen={bulkImportOpen} onClose={() => setBulkImportOpen(false)} />
```

- [ ] **Step 4: Verify web app compiles**

Run: `cd web-system-app && npx tsc --noEmit 2>&1 | head -10`
Expected: No errors

- [ ] **Step 5: Commit**

```bash
cd web-system-app && git add src/features/company-admin/hr/BulkEmployeeImportModal.tsx src/features/company-admin/hr/EmployeeDirectoryScreen.tsx
git commit -m "feat(bulk-import): add 3-step bulk import modal and button on employee directory"
```

---

## Task 6: Mobile — API Hooks for Bulk Import

**Files:**
- Modify: `mobile-app/src/features/company-admin/api/use-hr-queries.ts`
- Modify: `mobile-app/src/features/company-admin/api/use-hr-mutations.ts`

- [ ] **Step 1: Read mobile API files to understand patterns**

Read the mobile `use-hr-queries.ts` and `use-hr-mutations.ts` to understand the exact axios client, query keys, and mutation patterns.

- [ ] **Step 2: Add template download helper to mobile use-hr-queries.ts**

```typescript
import * as FileSystem from 'expo-file-system';
import * as Sharing from 'expo-sharing';

export async function downloadBulkEmployeeTemplate() {
  const baseUrl = hrApi.defaults?.baseURL ?? '';
  // Use FileSystem.downloadAsync for binary files on mobile
  const fileUri = FileSystem.documentDirectory + 'Employee_Import_Template.xlsx';
  const result = await FileSystem.downloadAsync(
    `${baseUrl}/employees/bulk/template`,
    fileUri,
    { headers: { Authorization: `Bearer ${getAuthToken()}` } },
  );
  if (result.status === 200) {
    await Sharing.shareAsync(result.uri, {
      mimeType: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
      dialogTitle: 'Save Employee Template',
    });
  }
}
```

Note: Adjust `getAuthToken()` to however the mobile app accesses the auth token (likely from `useAuthStore`). The exact implementation depends on the mobile axios client setup — check the file.

- [ ] **Step 3: Add bulk validate and import mutations to mobile use-hr-mutations.ts**

```typescript
export function useBulkValidateEmployees() {
  return useMutation({
    mutationFn: async ({ fileUri, defaultPassword }: { fileUri: string; defaultPassword: string }) => {
      const formData = new FormData();
      formData.append('file', {
        uri: fileUri,
        type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        name: 'employees.xlsx',
      } as any);
      formData.append('defaultPassword', defaultPassword);
      return hrApi.post('/employees/bulk/validate', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });
    },
  });
}

export function useBulkImportEmployees() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async ({ rows, defaultPassword }: { rows: Record<string, unknown>[]; defaultPassword: string }) => {
      return hrApi.post('/employees/bulk/import', { rows, defaultPassword });
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: hrKeys.employees() });
    },
  });
}
```

- [ ] **Step 4: Verify mobile app compiles**

Run: `cd mobile-app && pnpm type-check 2>&1 | head -10`
Expected: No errors

- [ ] **Step 5: Commit**

```bash
cd mobile-app && git add src/features/company-admin/api/use-hr-queries.ts src/features/company-admin/api/use-hr-mutations.ts
git commit -m "feat(bulk-import): add mobile API hooks for bulk validate and import"
```

---

## Task 7: Mobile — Bulk Import Screen

**Files:**
- Create: `mobile-app/src/features/company-admin/hr/bulk-employee-import-screen.tsx`
- Create: `mobile-app/src/app/(app)/hr/bulk-employee-import.tsx`
- Modify: `mobile-app/src/features/company-admin/hr/employee-directory-screen.tsx`

- [ ] **Step 1: Read the mobile employee directory screen to understand header layout and navigation patterns**

Read the full `employee-directory-screen.tsx` to find where to place the Bulk Import button and how navigation works (expo-router).

- [ ] **Step 2: Create the bulk import screen component**

Create `src/features/company-admin/hr/bulk-employee-import-screen.tsx` with 3 steps:

Follow mobile app patterns:
- `LinearGradient` header with `colors.gradient.start/mid/end`
- `font-inter` on all `<Text>` components
- `useSafeAreaInsets()` for padding
- `FadeInDown`/`FadeInUp` animations from reanimated
- `expo-document-picker` for file selection (filter: `application/vnd.openxmlformats-officedocument.spreadsheetml.sheet`)
- `ConfirmModal` for confirmations (never `Alert.alert()`)
- Colors from `@/components/ui/colors`
- `showSuccess()`/`showErrorMessage()` for toasts

Step 1 (Download):
- Description card
- "Download Template" button → calls `downloadBulkEmployeeTemplate()`

Step 2 (Upload & Validate):
- "Select File" button → `expo-document-picker`
- Shows selected filename
- Password TextInput with show/hide toggle
- "Validate" button
- FlatList of results with status badges

Step 3 (Import Results):
- Summary cards (green/red)
- FlatList of results
- "Done" button → `router.back()` + trigger refetch

- [ ] **Step 3: Create the route file**

```typescript
// src/app/(app)/hr/bulk-employee-import.tsx
export { BulkEmployeeImportScreen as default } from '@/features/company-admin/hr/bulk-employee-import-screen';
```

- [ ] **Step 4: Add "Bulk Import" button to employee directory screen header**

Add a button/icon in the header area of the employee directory screen that navigates to the bulk import screen:

```typescript
import { router } from 'expo-router';

// In the header area (next to search or as a header action):
<TouchableOpacity
  onPress={() => router.push('/hr/bulk-employee-import')}
  className="bg-white/20 rounded-full p-2"
>
  <Ionicons name="cloud-upload-outline" size={20} color="white" />
</TouchableOpacity>
```

- [ ] **Step 5: Verify mobile app compiles**

Run: `cd mobile-app && pnpm type-check 2>&1 | head -10`
Expected: No errors

- [ ] **Step 6: Commit**

```bash
cd mobile-app && git add src/features/company-admin/hr/bulk-employee-import-screen.tsx src/app/\(app\)/hr/bulk-employee-import.tsx src/features/company-admin/hr/employee-directory-screen.tsx
git commit -m "feat(bulk-import): add mobile bulk import screen and entry point"
```

---

## Task 8: End-to-End Verification

- [ ] **Step 1: Start backend and test template download**

Run: `cd avy-erp-backend && pnpm dev`

Test with curl (replace token with a valid COMPANY_ADMIN JWT):
```bash
curl -H "Authorization: Bearer <token>" \
  http://localhost:3000/api/v1/hr/employees/bulk/template \
  -o template.xlsx
```
Expected: Downloads an xlsx file with multiple sheets populated with company master data.

- [ ] **Step 2: Test validate endpoint**

Create a test xlsx with 2-3 rows and upload:
```bash
curl -X POST \
  -H "Authorization: Bearer <token>" \
  -F "file=@template.xlsx" \
  -F "defaultPassword=Test@123" \
  http://localhost:3000/api/v1/hr/employees/bulk/validate
```
Expected: JSON response with per-row validation results.

- [ ] **Step 3: Test import endpoint**

Use the validated rows from step 2:
```bash
curl -X POST \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"defaultPassword":"Test@123","rows":[...validated rows...]}' \
  http://localhost:3000/api/v1/hr/employees/bulk/import
```
Expected: JSON with success/failure counts and per-row employee IDs.

- [ ] **Step 4: Test web UI**

1. Open Employee Directory in web app
2. Click "Bulk Import" button
3. Download template → verify it has company's departments, designations, etc.
4. Fill in 2-3 rows, upload, enter password, validate
5. Review results, click Import
6. Verify employees appear in the directory

- [ ] **Step 5: Test mobile UI**

1. Open Employee Directory in mobile app
2. Tap Bulk Import button
3. Download template → verify share sheet opens
4. Upload a filled template, enter password, validate
5. Review results, tap Import
6. Verify employees appear in directory

- [ ] **Step 6: Final commit if any fixes were needed**

```bash
git add -A && git commit -m "fix(bulk-import): address issues found during e2e testing"
```
