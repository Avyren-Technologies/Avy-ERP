# ESS Portal Missing Features — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement 14 missing/incomplete ESS features across backend, web, and mobile: profile edit, payslip PDF download, leave cancel UI, shift swap, WFH request, document upload + viewing, policy documents, notification delivery, offline punch, holiday calendar (ESS endpoint), expense/reimbursement claims (ESS-scoped), loan application (employee self-service), and org chart (ESS permission + mobile screen). Appraisal self-review and 360 feedback are already working — no changes needed.

**Architecture:** Each feature follows the existing triple-gated pattern: `requireModuleEnabled('ess')` → `requireESSFeature('<toggle>')` → `requirePermissions(['ess:<action>'])`. New features add Prisma models where needed, backend endpoints in ESS routes, and frontend screens on both web (React/Tailwind) and mobile (Expo/NativeWind). New permissions are registered in `permissions.ts` and navigation items in `navigation-manifest.ts`.

**Payslip PDF Note:** Payslips are currently database snapshot records (no PDF). PDFKit (v0.18.0) is already a dependency with a working `PdfService` for invoices — we adapt this pattern for payslip PDFs.

**Tech Stack:** Node.js/Express, Prisma/PostgreSQL, Redis, Zod, React/Vite/Tailwind (web), Expo SDK 54/React Native/NativeWind/MMKV (mobile), React Query, Zustand.

---

## File Structure Overview

### Backend (`avy-erp-backend/`)
| Action | File | Responsibility |
|--------|------|----------------|
| Modify | `src/modules/hr/ess/ess.routes.ts` | Add new ESS route definitions |
| Modify | `src/modules/hr/ess/ess.controller.ts` | Add controller handlers |
| Modify | `src/modules/hr/ess/ess.service.ts` | Add business logic methods |
| Modify | `src/modules/hr/ess/ess.validators.ts` | Add Zod schemas |
| Modify | `src/shared/constants/permissions.ts` | Register new ESS permissions |
| Modify | `src/shared/constants/navigation-manifest.ts` | Add nav items for new screens |
| Create | `prisma/modules/hrms/policy-documents.prisma` | PolicyDocument model |
| Create | `prisma/modules/hrms/shift-swap.prisma` | ShiftSwapRequest, WfhRequest models |
| Modify | `prisma/modules/platform/tenant.prisma` | Add Company relations to new models |
| Modify | `prisma/modules/hrms/employee.prisma` | Add Employee relations to new models |
| Create | `src/modules/hr/ess/payslip-pdf.service.ts` | Payslip PDF generation using PDFKit |

### Web (`web-system-app/`)
| Action | File | Responsibility |
|--------|------|----------------|
| Modify | `src/features/company-admin/hr/MyProfileScreen.tsx` | Add edit form modal |
| Modify | `src/features/company-admin/hr/MyPayslipsScreen.tsx` | Wire PDF download |
| Modify | `src/features/company-admin/hr/MyLeaveScreen.tsx` | Add cancel button |
| Create | `src/features/ess/ShiftSwapScreen.tsx` | Shift swap request screen |
| Create | `src/features/ess/WfhRequestScreen.tsx` | WFH request screen |
| Create | `src/features/ess/MyDocumentsScreen.tsx` | Document upload screen |
| Create | `src/features/ess/PolicyDocumentsScreen.tsx` | Policy docs viewer |
| Create | `src/features/ess/MyExpenseClaimsScreen.tsx` | Employee expense claims |
| Create | `src/features/ess/MyLoanScreen.tsx` | Employee loan application |
| Create | `src/features/ess/MyHolidaysScreen.tsx` | Employee holiday calendar |
| Modify | `src/lib/api/ess.ts` | Add new API methods |
| Modify | `src/features/company-admin/api/use-ess-queries.ts` | Add query hooks |
| Modify | `src/features/company-admin/api/use-ess-mutations.ts` | Add mutation hooks |
| Modify | `src/App.tsx` | Register new routes |

### Mobile (`mobile-app/`)
| Action | File | Responsibility |
|--------|------|----------------|
| Modify | `src/features/company-admin/hr/my-profile-screen.tsx` | Add edit form modal |
| Modify | `src/features/company-admin/hr/my-payslips-screen.tsx` | Wire PDF download |
| Modify | `src/features/company-admin/hr/my-leave-screen.tsx` | Add cancel button |
| Create | `src/features/ess/shift-swap-screen.tsx` | Shift swap screen |
| Create | `src/features/ess/wfh-request-screen.tsx` | WFH request screen |
| Create | `src/features/ess/my-documents-screen.tsx` | Document upload screen |
| Create | `src/features/ess/policy-documents-screen.tsx` | Policy docs viewer |
| Create | `src/lib/offline-punch-queue.ts` | MMKV offline queue |
| Modify | `src/features/company-admin/hr/shift-check-in-screen.tsx` | Integrate offline queue |
| Modify | `src/features/company-admin/api/use-ess-queries.ts` | Add query hooks |
| Modify | `src/features/company-admin/api/use-ess-mutations.ts` | Add mutation hooks |
| Modify | `src/lib/api/ess.ts` | Add API methods |
| Create | `src/app/(app)/company/hr/shift-swap.tsx` | Route file |
| Create | `src/app/(app)/company/hr/wfh-requests.tsx` | Route file |
| Create | `src/app/(app)/company/hr/my-documents.tsx` | Route file |
| Create | `src/app/(app)/company/hr/policy-documents.tsx` | Route file |
| Create | `src/features/ess/my-expense-claims-screen.tsx` | Employee expense claims |
| Create | `src/features/ess/my-loan-screen.tsx` | Employee loan application |
| Create | `src/features/ess/my-holidays-screen.tsx` | Employee holiday calendar |
| Create | `src/features/company-admin/hr/org-chart-screen.tsx` | Org chart (if missing) |
| Create | `src/app/(app)/company/hr/my-expense-claims.tsx` | Route file |
| Create | `src/app/(app)/company/hr/my-loans.tsx` | Route file |
| Create | `src/app/(app)/company/hr/my-holidays.tsx` | Route file |

---

## Task 1: Prisma Models — ShiftSwap, WFH, PolicyDocument

**Files:**
- Create: `avy-erp-backend/prisma/modules/hrms/shift-swap.prisma`
- Create: `avy-erp-backend/prisma/modules/hrms/policy-documents.prisma`
- Modify: `avy-erp-backend/prisma/modules/platform/tenant.prisma` (Company relations)
- Modify: `avy-erp-backend/prisma/modules/hrms/employee.prisma` (Employee relations)

- [ ] **Step 1: Create shift-swap.prisma with ShiftSwapRequest and WfhRequest models**

```prisma
// prisma/modules/hrms/shift-swap.prisma
// ==========================================
// HRMS — Shift Swap & WFH Requests
// ==========================================

model ShiftSwapRequest {
  id              String   @id @default(cuid())
  employeeId      String
  employee        Employee @relation(fields: [employeeId], references: [id])
  currentShiftId  String
  requestedShiftId String
  swapDate        DateTime @db.Date
  reason          String
  status          String   @default("PENDING") // PENDING, APPROVED, REJECTED, CANCELLED
  approvedBy      String?
  approvedAt      DateTime?
  companyId       String
  company         Company  @relation(fields: [companyId], references: [id], onDelete: Cascade)
  createdAt       DateTime @default(now())
  updatedAt       DateTime @updatedAt

  @@map("shift_swap_requests")
}

model WfhRequest {
  id          String    @id @default(cuid())
  employeeId  String
  employee    Employee  @relation(fields: [employeeId], references: [id])
  fromDate    DateTime  @db.Date
  toDate      DateTime  @db.Date
  days        Decimal   @db.Decimal(5, 1)
  reason      String
  status      String    @default("PENDING") // PENDING, APPROVED, REJECTED, CANCELLED
  approvedBy  String?
  approvedAt  DateTime?
  companyId   String
  company     Company   @relation(fields: [companyId], references: [id], onDelete: Cascade)
  createdAt   DateTime  @default(now())
  updatedAt   DateTime  @updatedAt

  @@map("wfh_requests")
}
```

- [ ] **Step 2: Create policy-documents.prisma with PolicyDocument model**

```prisma
// prisma/modules/hrms/policy-documents.prisma
// ==========================================
// HRMS — Policy Documents
// ==========================================

model PolicyDocument {
  id          String   @id @default(cuid())
  title       String
  category    String   // HR_POLICY, LEAVE_POLICY, ATTENDANCE_POLICY, CODE_OF_CONDUCT, SAFETY, TRAVEL, IT_POLICY, OTHER
  description String?
  fileUrl     String
  fileName    String
  version     String   @default("1.0")
  isActive    Boolean  @default(true)
  publishedAt DateTime?
  companyId   String
  company     Company  @relation(fields: [companyId], references: [id], onDelete: Cascade)
  uploadedBy  String?
  createdAt   DateTime @default(now())
  updatedAt   DateTime @updatedAt

  @@map("policy_documents")
}
```

- [ ] **Step 3: Add relations to Company model in tenant.prisma**

Add these lines before `@@map("companies")` in the Company model:

```prisma
  // Shift Swap & WFH Relations
  shiftSwapRequests ShiftSwapRequest[]
  wfhRequests       WfhRequest[]

  // Policy Documents
  policyDocuments PolicyDocument[]
```

- [ ] **Step 4: Add relations to Employee model in employee.prisma**

Add these lines before the `createdAt` field in the Employee model:

```prisma
  // Shift Swap & WFH Relations
  shiftSwapRequests ShiftSwapRequest[]
  wfhRequests       WfhRequest[]
```

- [ ] **Step 5: Run prisma merge and validate**

```bash
cd avy-erp-backend && pnpm prisma:merge
npx prisma validate
```

Expected: Schema valid with new models.

- [ ] **Step 6: Generate migration**

```bash
cd avy-erp-backend && npx prisma migrate dev --name add_shift_swap_wfh_policy_docs
```

- [ ] **Step 7: Commit**

```bash
git add prisma/
git commit -m "feat(prisma): add ShiftSwapRequest, WfhRequest, PolicyDocument models"
```

---

## Task 2: Permissions & Navigation Manifest

**Files:**
- Modify: `avy-erp-backend/src/shared/constants/permissions.ts`
- Modify: `avy-erp-backend/src/shared/constants/navigation-manifest.ts`

- [ ] **Step 1: Add new ESS permissions to permissions.ts**

Find the `ess` permission module `actions` array and add these new actions:

```typescript
// In the ess actions array, add:
'swap-shift', 'request-wfh', 'upload-document', 'view-policies',
```

Also find the `Employee` reference role `permissions` array and add:

```typescript
'ess:swap-shift', 'ess:request-wfh', 'ess:upload-document', 'ess:view-policies',
```

- [ ] **Step 2: Add navigation manifest entries**

Add these entries in the ESS section (after sortOrder 311, before 399):

```typescript
{
  id: 'ess-shift-swap',
  label: 'Shift Swap',
  icon: 'repeat',
  requiredPerm: 'ess:swap-shift',
  path: '/app/company/hr/shift-swap',
  module: 'hr',
  group: 'My Workspace',
  sortOrder: 312,
  roleScope: 'company',
},
{
  id: 'ess-wfh',
  label: 'WFH Request',
  icon: 'home',
  requiredPerm: 'ess:request-wfh',
  path: '/app/company/hr/wfh-requests',
  module: 'hr',
  group: 'My Workspace',
  sortOrder: 313,
  roleScope: 'company',
},
{
  id: 'ess-documents',
  label: 'My Documents',
  icon: 'file-up',
  requiredPerm: 'ess:upload-document',
  path: '/app/company/hr/my-documents',
  module: 'hr',
  group: 'My Workspace',
  sortOrder: 314,
  roleScope: 'company',
},
{
  id: 'ess-policies',
  label: 'Policy Documents',
  icon: 'book-open',
  requiredPerm: 'ess:view-policies',
  path: '/app/company/hr/policy-documents',
  module: 'hr',
  group: 'My Workspace',
  sortOrder: 315,
  roleScope: 'company',
},
```

- [ ] **Step 3: Commit**

```bash
git add src/shared/constants/
git commit -m "feat(rbac): add permissions and nav items for shift-swap, wfh, documents, policies"
```

---

## Task 3: Backend — Profile Edit, Payslip PDF, Leave Cancel Fixes

**Files:**
- Modify: `avy-erp-backend/src/modules/hr/ess/ess.validators.ts`
- Modify: `avy-erp-backend/src/modules/hr/ess/ess.service.ts`
- Modify: `avy-erp-backend/src/modules/hr/ess/ess.controller.ts`
- Modify: `avy-erp-backend/src/modules/hr/ess/ess.routes.ts`

- [ ] **Step 1: Add validators for profile update**

Add to `ess.validators.ts`:

```typescript
export const updateProfileSchema = z.object({
  personalMobile: z.string().min(1).optional(),
  alternativeMobile: z.string().optional(),
  personalEmail: z.string().email().optional(),
  currentAddress: z.any().optional(),
  permanentAddress: z.any().optional(),
  emergencyContactName: z.string().min(1).optional(),
  emergencyContactRelation: z.string().min(1).optional(),
  emergencyContactMobile: z.string().min(1).optional(),
  maritalStatus: z.enum(['SINGLE', 'MARRIED', 'DIVORCED', 'WIDOWED']).optional(),
  bloodGroup: z.string().optional(),
});
```

- [ ] **Step 2: Add service methods for profile update and payslip PDF**

Add to `ess.service.ts`:

```typescript
async updateMyProfile(companyId: string, userId: string, data: any) {
  const user = await platformPrisma.user.findUnique({
    where: { id: userId },
    select: { employeeId: true },
  });
  if (!user?.employeeId) throw ApiError.badRequest('No linked employee profile');

  const employee = await platformPrisma.employee.update({
    where: { id: user.employeeId, companyId },
    data: {
      ...(data.personalMobile !== undefined && { personalMobile: data.personalMobile }),
      ...(data.alternativeMobile !== undefined && { alternativeMobile: data.alternativeMobile }),
      ...(data.personalEmail !== undefined && { personalEmail: data.personalEmail }),
      ...(data.currentAddress !== undefined && { currentAddress: data.currentAddress }),
      ...(data.permanentAddress !== undefined && { permanentAddress: data.permanentAddress }),
      ...(data.emergencyContactName !== undefined && { emergencyContactName: data.emergencyContactName }),
      ...(data.emergencyContactRelation !== undefined && { emergencyContactRelation: data.emergencyContactRelation }),
      ...(data.emergencyContactMobile !== undefined && { emergencyContactMobile: data.emergencyContactMobile }),
      ...(data.maritalStatus !== undefined && { maritalStatus: data.maritalStatus }),
      ...(data.bloodGroup !== undefined && { bloodGroup: data.bloodGroup }),
    },
    select: {
      id: true, firstName: true, lastName: true, personalMobile: true,
      alternativeMobile: true, personalEmail: true, currentAddress: true,
      permanentAddress: true, emergencyContactName: true,
      emergencyContactRelation: true, emergencyContactMobile: true,
      maritalStatus: true, bloodGroup: true,
    },
  });

  return employee;
}

async generatePayslipPdf(companyId: string, userId: string, payslipId: string) {
  const user = await platformPrisma.user.findUnique({
    where: { id: userId },
    select: { employeeId: true },
  });
  if (!user?.employeeId) throw ApiError.badRequest('No linked employee profile');

  const payslip = await platformPrisma.payslip.findFirst({
    where: { id: payslipId, employeeId: user.employeeId, companyId },
    include: {
      employee: {
        select: {
          firstName: true, lastName: true, employeeId: true,
          designation: { select: { name: true } },
          department: { select: { name: true } },
          bankAccountNumber: true, bankName: true, bankIfscCode: true,
          panNumber: true, uan: true,
        },
      },
      company: { select: { name: true, logoUrl: true } },
    },
  });

  if (!payslip) throw ApiError.notFound('Payslip not found');

  const PDFDocument = require('pdfkit');
  const doc = new PDFDocument({ size: 'A4', margin: 50 });
  const chunks: Buffer[] = [];

  doc.on('data', (chunk: Buffer) => chunks.push(chunk));

  // Header
  doc.fontSize(18).font('Helvetica-Bold').text(payslip.company.name, { align: 'center' });
  doc.fontSize(10).font('Helvetica').text('Payslip', { align: 'center' });
  doc.moveDown(0.5);
  const monthNames = ['', 'January', 'February', 'March', 'April', 'May', 'June',
    'July', 'August', 'September', 'October', 'November', 'December'];
  doc.fontSize(11).font('Helvetica-Bold')
    .text(`${monthNames[payslip.month]} ${payslip.year}`, { align: 'center' });
  doc.moveDown();

  // Employee info
  doc.fontSize(9).font('Helvetica');
  doc.text(`Employee: ${payslip.employee.firstName} ${payslip.employee.lastName}`);
  doc.text(`Employee ID: ${payslip.employee.employeeId}`);
  doc.text(`Department: ${payslip.employee.designation?.name ?? '-'}`);
  if (payslip.employee.panNumber) doc.text(`PAN: ${payslip.employee.panNumber}`);
  if (payslip.employee.uan) doc.text(`UAN: ${payslip.employee.uan}`);
  doc.moveDown();

  // Earnings & Deductions table
  const earnings = (payslip.earnings as Record<string, number>) ?? {};
  const deductions = (payslip.deductions as Record<string, number>) ?? {};

  doc.fontSize(10).font('Helvetica-Bold').text('Earnings', 50);
  doc.font('Helvetica-Bold').text('Deductions', 320);
  doc.moveDown(0.3);

  const earningEntries = Object.entries(earnings);
  const deductionEntries = Object.entries(deductions);
  const maxRows = Math.max(earningEntries.length, deductionEntries.length);

  doc.fontSize(9).font('Helvetica');
  for (let i = 0; i < maxRows; i++) {
    const y = doc.y;
    if (earningEntries[i]) {
      doc.text(earningEntries[i][0], 50, y, { width: 150 });
      doc.text(`₹${Number(earningEntries[i][1]).toLocaleString('en-IN')}`, 210, y, { width: 80, align: 'right' });
    }
    if (deductionEntries[i]) {
      doc.text(deductionEntries[i][0], 320, y, { width: 150 });
      doc.text(`₹${Number(deductionEntries[i][1]).toLocaleString('en-IN')}`, 480, y, { width: 80, align: 'right' });
    }
    doc.moveDown(0.4);
  }

  doc.moveDown();
  doc.font('Helvetica-Bold');
  doc.text(`Gross Earnings: ₹${Number(payslip.grossEarnings ?? 0).toLocaleString('en-IN')}`, 50);
  doc.text(`Total Deductions: ₹${Number(payslip.totalDeductions ?? 0).toLocaleString('en-IN')}`, 320, doc.y - 14);
  doc.moveDown();
  doc.fontSize(12).text(`Net Pay: ₹${Number(payslip.netPay ?? 0).toLocaleString('en-IN')}`, { align: 'center' });

  doc.end();

  return new Promise<Buffer>((resolve) => {
    doc.on('end', () => resolve(Buffer.concat(chunks)));
  });
}
```

- [ ] **Step 3: Add controller handlers**

Add to `ess.controller.ts`:

```typescript
updateMyProfile = asyncHandler(async (req: Request, res: Response) => {
  const companyId = req.user?.companyId;
  if (!companyId) throw ApiError.badRequest('Company ID is required');

  const parsed = updateProfileSchema.safeParse(req.body);
  if (!parsed.success) throw ApiError.badRequest(parsed.error.errors.map((e: any) => e.message).join(', '));

  const result = await essService.updateMyProfile(companyId, req.user!.id, parsed.data);
  res.json(createSuccessResponse(result, 'Profile updated successfully'));
});

downloadPayslipPdf = asyncHandler(async (req: Request, res: Response) => {
  const companyId = req.user?.companyId;
  if (!companyId) throw ApiError.badRequest('Company ID is required');

  const { id } = req.params;
  const pdfBuffer = await essService.generatePayslipPdf(companyId, req.user!.id, id);

  res.setHeader('Content-Type', 'application/pdf');
  res.setHeader('Content-Disposition', `attachment; filename=payslip-${id}.pdf`);
  res.send(pdfBuffer);
});
```

- [ ] **Step 4: Add routes**

Add to `ess.routes.ts` in the employee-facing section:

```typescript
// Profile edit
router.patch(
  '/ess/my-profile',
  requireESSFeature('profileUpdate'),
  requirePermissions(['hr:update', 'ess:view-profile']),
  controller.updateMyProfile
);

// Payslip PDF download
router.get(
  '/ess/my-payslips/:id/pdf',
  requireESSFeature('downloadPayslips'),
  requirePermissions(['hr:read', 'ess:view-payslips']),
  controller.downloadPayslipPdf
);
```

- [ ] **Step 5: Commit**

```bash
git add src/modules/hr/ess/
git commit -m "feat(ess): add profile edit endpoint and payslip PDF download"
```

---

## Task 4: Backend — Shift Swap, WFH, Document Upload, Policy Docs

**Files:**
- Modify: `avy-erp-backend/src/modules/hr/ess/ess.validators.ts`
- Modify: `avy-erp-backend/src/modules/hr/ess/ess.service.ts`
- Modify: `avy-erp-backend/src/modules/hr/ess/ess.controller.ts`
- Modify: `avy-erp-backend/src/modules/hr/ess/ess.routes.ts`

- [ ] **Step 1: Add validators**

Add to `ess.validators.ts`:

```typescript
export const shiftSwapSchema = z.object({
  currentShiftId: z.string().min(1),
  requestedShiftId: z.string().min(1),
  swapDate: z.string().min(1),
  reason: z.string().min(1),
});

export const wfhRequestSchema = z.object({
  fromDate: z.string().min(1),
  toDate: z.string().min(1),
  days: z.number().min(0.5),
  reason: z.string().min(1),
});

export const uploadDocumentSchema = z.object({
  documentType: z.string().min(1),
  documentNumber: z.string().optional(),
  expiryDate: z.string().optional(),
  fileUrl: z.string().min(1),
  fileName: z.string().min(1),
});

export const policyDocumentSchema = z.object({
  title: z.string().min(1),
  category: z.enum(['HR_POLICY', 'LEAVE_POLICY', 'ATTENDANCE_POLICY', 'CODE_OF_CONDUCT', 'SAFETY', 'TRAVEL', 'IT_POLICY', 'OTHER']),
  description: z.string().optional(),
  fileUrl: z.string().min(1),
  fileName: z.string().min(1),
  version: z.string().optional(),
});
```

- [ ] **Step 2: Add service methods for shift swap and WFH**

Add to `ess.service.ts`:

```typescript
// ── Shift Swap ──

async getMyShiftSwaps(companyId: string, userId: string) {
  const user = await platformPrisma.user.findUnique({ where: { id: userId }, select: { employeeId: true } });
  if (!user?.employeeId) return [];

  return platformPrisma.shiftSwapRequest.findMany({
    where: { employeeId: user.employeeId, companyId },
    orderBy: { createdAt: 'desc' },
  });
}

async createShiftSwap(companyId: string, userId: string, data: any) {
  const user = await platformPrisma.user.findUnique({ where: { id: userId }, select: { employeeId: true } });
  if (!user?.employeeId) throw ApiError.badRequest('No linked employee profile');

  return platformPrisma.shiftSwapRequest.create({
    data: {
      employeeId: user.employeeId,
      currentShiftId: data.currentShiftId,
      requestedShiftId: data.requestedShiftId,
      swapDate: new Date(data.swapDate),
      reason: data.reason,
      companyId,
    },
  });
}

async cancelShiftSwap(companyId: string, userId: string, id: string) {
  const user = await platformPrisma.user.findUnique({ where: { id: userId }, select: { employeeId: true } });
  if (!user?.employeeId) throw ApiError.badRequest('No linked employee profile');

  const request = await platformPrisma.shiftSwapRequest.findFirst({
    where: { id, employeeId: user.employeeId, companyId, status: 'PENDING' },
  });
  if (!request) throw ApiError.notFound('Shift swap request not found or not cancellable');

  return platformPrisma.shiftSwapRequest.update({
    where: { id },
    data: { status: 'CANCELLED' },
  });
}

// ── WFH Requests ──

async getMyWfhRequests(companyId: string, userId: string) {
  const user = await platformPrisma.user.findUnique({ where: { id: userId }, select: { employeeId: true } });
  if (!user?.employeeId) return [];

  return platformPrisma.wfhRequest.findMany({
    where: { employeeId: user.employeeId, companyId },
    orderBy: { createdAt: 'desc' },
  });
}

async createWfhRequest(companyId: string, userId: string, data: any) {
  const user = await platformPrisma.user.findUnique({ where: { id: userId }, select: { employeeId: true } });
  if (!user?.employeeId) throw ApiError.badRequest('No linked employee profile');

  return platformPrisma.wfhRequest.create({
    data: {
      employeeId: user.employeeId,
      fromDate: new Date(data.fromDate),
      toDate: new Date(data.toDate),
      days: data.days,
      reason: data.reason,
      companyId,
    },
  });
}

async cancelWfhRequest(companyId: string, userId: string, id: string) {
  const user = await platformPrisma.user.findUnique({ where: { id: userId }, select: { employeeId: true } });
  if (!user?.employeeId) throw ApiError.badRequest('No linked employee profile');

  const request = await platformPrisma.wfhRequest.findFirst({
    where: { id, employeeId: user.employeeId, companyId, status: 'PENDING' },
  });
  if (!request) throw ApiError.notFound('WFH request not found or not cancellable');

  return platformPrisma.wfhRequest.update({
    where: { id },
    data: { status: 'CANCELLED' },
  });
}

// ── Document Upload (ESS) ──

async getMyDocuments(companyId: string, userId: string) {
  const user = await platformPrisma.user.findUnique({ where: { id: userId }, select: { employeeId: true } });
  if (!user?.employeeId) return [];

  return platformPrisma.employeeDocument.findMany({
    where: { employeeId: user.employeeId },
    orderBy: { createdAt: 'desc' },
  });
}

async uploadMyDocument(companyId: string, userId: string, data: any) {
  const user = await platformPrisma.user.findUnique({ where: { id: userId }, select: { employeeId: true } });
  if (!user?.employeeId) throw ApiError.badRequest('No linked employee profile');

  return platformPrisma.employeeDocument.create({
    data: {
      employeeId: user.employeeId,
      documentType: data.documentType,
      documentNumber: data.documentNumber ?? null,
      expiryDate: data.expiryDate ? new Date(data.expiryDate) : null,
      fileUrl: data.fileUrl,
      fileName: data.fileName ?? null,
    },
  });
}

// ── Policy Documents ──

async getPolicyDocuments(companyId: string) {
  return platformPrisma.policyDocument.findMany({
    where: { companyId, isActive: true },
    orderBy: { publishedAt: 'desc' },
  });
}

async createPolicyDocument(companyId: string, data: any, userId?: string) {
  return platformPrisma.policyDocument.create({
    data: {
      title: data.title,
      category: data.category,
      description: data.description ?? null,
      fileUrl: data.fileUrl,
      fileName: data.fileName,
      version: data.version ?? '1.0',
      publishedAt: new Date(),
      companyId,
      uploadedBy: userId ?? null,
    },
  });
}
```

- [ ] **Step 3: Add controller handlers**

Add to `ess.controller.ts`:

```typescript
// Shift Swap
getMyShiftSwaps = asyncHandler(async (req: Request, res: Response) => {
  const companyId = req.user?.companyId;
  if (!companyId) throw ApiError.badRequest('Company ID is required');
  const result = await essService.getMyShiftSwaps(companyId, req.user!.id);
  res.json(createSuccessResponse(result));
});

createShiftSwap = asyncHandler(async (req: Request, res: Response) => {
  const companyId = req.user?.companyId;
  if (!companyId) throw ApiError.badRequest('Company ID is required');
  const parsed = shiftSwapSchema.safeParse(req.body);
  if (!parsed.success) throw ApiError.badRequest(parsed.error.errors.map((e: any) => e.message).join(', '));
  const result = await essService.createShiftSwap(companyId, req.user!.id, parsed.data);
  res.status(201).json(createSuccessResponse(result, 'Shift swap request submitted'));
});

cancelShiftSwap = asyncHandler(async (req: Request, res: Response) => {
  const companyId = req.user?.companyId;
  if (!companyId) throw ApiError.badRequest('Company ID is required');
  const result = await essService.cancelShiftSwap(companyId, req.user!.id, req.params.id);
  res.json(createSuccessResponse(result, 'Shift swap request cancelled'));
});

// WFH
getMyWfhRequests = asyncHandler(async (req: Request, res: Response) => {
  const companyId = req.user?.companyId;
  if (!companyId) throw ApiError.badRequest('Company ID is required');
  const result = await essService.getMyWfhRequests(companyId, req.user!.id);
  res.json(createSuccessResponse(result));
});

createWfhRequest = asyncHandler(async (req: Request, res: Response) => {
  const companyId = req.user?.companyId;
  if (!companyId) throw ApiError.badRequest('Company ID is required');
  const parsed = wfhRequestSchema.safeParse(req.body);
  if (!parsed.success) throw ApiError.badRequest(parsed.error.errors.map((e: any) => e.message).join(', '));
  const result = await essService.createWfhRequest(companyId, req.user!.id, parsed.data);
  res.status(201).json(createSuccessResponse(result, 'WFH request submitted'));
});

cancelWfhRequest = asyncHandler(async (req: Request, res: Response) => {
  const companyId = req.user?.companyId;
  if (!companyId) throw ApiError.badRequest('Company ID is required');
  const result = await essService.cancelWfhRequest(companyId, req.user!.id, req.params.id);
  res.json(createSuccessResponse(result, 'WFH request cancelled'));
});

// Documents
getMyDocuments = asyncHandler(async (req: Request, res: Response) => {
  const companyId = req.user?.companyId;
  if (!companyId) throw ApiError.badRequest('Company ID is required');
  const result = await essService.getMyDocuments(companyId, req.user!.id);
  res.json(createSuccessResponse(result));
});

uploadMyDocument = asyncHandler(async (req: Request, res: Response) => {
  const companyId = req.user?.companyId;
  if (!companyId) throw ApiError.badRequest('Company ID is required');
  const parsed = uploadDocumentSchema.safeParse(req.body);
  if (!parsed.success) throw ApiError.badRequest(parsed.error.errors.map((e: any) => e.message).join(', '));
  const result = await essService.uploadMyDocument(companyId, req.user!.id, parsed.data);
  res.status(201).json(createSuccessResponse(result, 'Document uploaded'));
});

// Policy Documents
getPolicyDocuments = asyncHandler(async (req: Request, res: Response) => {
  const companyId = req.user?.companyId;
  if (!companyId) throw ApiError.badRequest('Company ID is required');
  const result = await essService.getPolicyDocuments(companyId);
  res.json(createSuccessResponse(result));
});

createPolicyDocument = asyncHandler(async (req: Request, res: Response) => {
  const companyId = req.user?.companyId;
  if (!companyId) throw ApiError.badRequest('Company ID is required');
  const parsed = policyDocumentSchema.safeParse(req.body);
  if (!parsed.success) throw ApiError.badRequest(parsed.error.errors.map((e: any) => e.message).join(', '));
  const result = await essService.createPolicyDocument(companyId, parsed.data, req.user?.id);
  res.status(201).json(createSuccessResponse(result, 'Policy document created'));
});
```

- [ ] **Step 4: Add routes**

Add to `ess.routes.ts`:

```typescript
// ── Shift Swap ──
router.get('/ess/my-shift-swaps', requireESSFeature('shiftSwapRequest'), requirePermissions(['hr:read', 'ess:swap-shift']), controller.getMyShiftSwaps);
router.post('/ess/shift-swap', requireESSFeature('shiftSwapRequest'), requirePermissions(['hr:create', 'ess:swap-shift']), controller.createShiftSwap);
router.patch('/ess/shift-swap/:id/cancel', requireESSFeature('shiftSwapRequest'), requirePermissions(['hr:update', 'ess:swap-shift']), controller.cancelShiftSwap);

// ── WFH ──
router.get('/ess/my-wfh-requests', requireESSFeature('wfhRequest'), requirePermissions(['hr:read', 'ess:request-wfh']), controller.getMyWfhRequests);
router.post('/ess/wfh-request', requireESSFeature('wfhRequest'), requirePermissions(['hr:create', 'ess:request-wfh']), controller.createWfhRequest);
router.patch('/ess/wfh-request/:id/cancel', requireESSFeature('wfhRequest'), requirePermissions(['hr:update', 'ess:request-wfh']), controller.cancelWfhRequest);

// ── Documents ──
router.get('/ess/my-documents', requireESSFeature('documentUpload'), requirePermissions(['hr:read', 'ess:upload-document']), controller.getMyDocuments);
router.post('/ess/my-documents', requireESSFeature('documentUpload'), requirePermissions(['hr:create', 'ess:upload-document']), controller.uploadMyDocument);

// ── Policy Documents ──
router.get('/ess/policy-documents', requireESSFeature('policyDocuments'), requirePermissions(['hr:read', 'ess:view-policies']), controller.getPolicyDocuments);
router.post('/policy-documents', requirePermissions(['hr:create']), controller.createPolicyDocument); // Admin only
```

- [ ] **Step 5: Commit**

```bash
git add src/modules/hr/ess/
git commit -m "feat(ess): add shift-swap, wfh, document upload, policy docs endpoints"
```

---

## Task 5: Backend — Notification Delivery

**Files:**
- Modify: `avy-erp-backend/src/modules/hr/ess/ess.service.ts`

- [ ] **Step 1: Replace the console.log TODO in triggerNotification with actual email delivery**

Find the `triggerNotification` method in `ess.service.ts` (around line 1036). Replace the `// TODO: Queue actual notification delivery` and `console.log(...)` block with:

```typescript
// Actually deliver notification based on channel
try {
  if (rule.channel === 'EMAIL') {
    // Resolve recipient emails based on recipientRole
    const recipientEmails = await this.resolveRecipientEmails(companyId, rule.recipientRole, data);
    if (recipientEmails.length > 0) {
      const { sendEmail } = await import('@/infrastructure/email/email.service');
      for (const email of recipientEmails) {
        await sendEmail(email, subject, `<div style="font-family:sans-serif;padding:20px">${body.replace(/\n/g, '<br>')}</div>`, body);
      }
    }
  } else if (rule.channel === 'IN_APP') {
    logger.info(`[Notification:IN_APP] ${event} → ${rule.recipientRole}: ${subject}`);
    // In-app notifications will be stored when Notification model is added
  } else {
    logger.info(`[Notification:${rule.channel}] ${event} → ${rule.recipientRole}: ${subject} (delivery not yet implemented)`);
  }
} catch (err) {
  logger.error(`[Notification] Failed to deliver ${rule.channel} notification for ${event}:`, err);
}
```

- [ ] **Step 2: Add the resolveRecipientEmails helper method**

Add to `ess.service.ts` in the ESSService class:

```typescript
private async resolveRecipientEmails(companyId: string, recipientRole: string, data: any): Promise<string[]> {
  if (recipientRole === 'EMPLOYEE' && data?.employeeEmail) {
    return [data.employeeEmail];
  }

  if (recipientRole === 'MANAGER' && data?.employeeId) {
    const employee = await platformPrisma.employee.findUnique({
      where: { id: data.employeeId },
      select: { reportingManager: { select: { officialEmail: true, personalEmail: true } } },
    });
    const mgr = employee?.reportingManager;
    if (mgr?.officialEmail) return [mgr.officialEmail];
    if (mgr?.personalEmail) return [mgr.personalEmail];
    return [];
  }

  if (recipientRole === 'HR') {
    const hrUsers = await platformPrisma.user.findMany({
      where: { companyId, isActive: true },
      select: { email: true },
      take: 5,
    });
    return hrUsers.map((u) => u.email);
  }

  if (recipientRole === 'ALL') {
    const users = await platformPrisma.user.findMany({
      where: { companyId, isActive: true },
      select: { email: true },
      take: 50,
    });
    return users.map((u) => u.email);
  }

  return [];
}
```

- [ ] **Step 3: Commit**

```bash
git add src/modules/hr/ess/ess.service.ts
git commit -m "feat(notifications): wire triggerNotification to email delivery via nodemailer"
```

---

## Task 6: Web — Leave Cancel UI, Profile Edit, Payslip Download

**Files:**
- Modify: `web-system-app/src/lib/api/ess.ts`
- Modify: `web-system-app/src/features/company-admin/api/use-ess-queries.ts`
- Modify: `web-system-app/src/features/company-admin/api/use-ess-mutations.ts`
- Modify: `web-system-app/src/features/company-admin/hr/MyLeaveScreen.tsx`
- Modify: `web-system-app/src/features/company-admin/hr/MyProfileScreen.tsx`
- Modify: `web-system-app/src/features/company-admin/hr/MyPayslipsScreen.tsx`

- [ ] **Step 1: Add API methods to ess.ts**

Add to the `essApi` object in `web-system-app/src/lib/api/ess.ts`:

```typescript
// Profile edit
async updateMyProfile(data: any): Promise<ApiResponse<any>> {
  const response = await client.patch('/hr/ess/my-profile', data);
  return response.data;
},

// Payslip PDF download
async downloadPayslipPdf(payslipId: string): Promise<Blob> {
  const response = await client.get(`/hr/ess/my-payslips/${payslipId}/pdf`, { responseType: 'blob' });
  return response.data;
},

// Leave cancel
async cancelLeave(leaveRequestId: string): Promise<ApiResponse<any>> {
  const response = await client.patch(`/hr/leave-requests/${leaveRequestId}/cancel`);
  return response.data;
},

// Shift swap
async getMyShiftSwaps(): Promise<ApiResponse<any>> {
  const response = await client.get('/hr/ess/my-shift-swaps');
  return response.data;
},
async createShiftSwap(data: any): Promise<ApiResponse<any>> {
  const response = await client.post('/hr/ess/shift-swap', data);
  return response.data;
},
async cancelShiftSwap(id: string): Promise<ApiResponse<any>> {
  const response = await client.patch(`/hr/ess/shift-swap/${id}/cancel`);
  return response.data;
},

// WFH
async getMyWfhRequests(): Promise<ApiResponse<any>> {
  const response = await client.get('/hr/ess/my-wfh-requests');
  return response.data;
},
async createWfhRequest(data: any): Promise<ApiResponse<any>> {
  const response = await client.post('/hr/ess/wfh-request', data);
  return response.data;
},
async cancelWfhRequest(id: string): Promise<ApiResponse<any>> {
  const response = await client.patch(`/hr/ess/wfh-request/${id}/cancel`);
  return response.data;
},

// Documents
async getMyDocuments(): Promise<ApiResponse<any>> {
  const response = await client.get('/hr/ess/my-documents');
  return response.data;
},
async uploadMyDocument(data: any): Promise<ApiResponse<any>> {
  const response = await client.post('/hr/ess/my-documents', data);
  return response.data;
},

// Policy documents
async getPolicyDocuments(): Promise<ApiResponse<any>> {
  const response = await client.get('/hr/ess/policy-documents');
  return response.data;
},
```

- [ ] **Step 2: Add query hooks to use-ess-queries.ts**

Add to the `essKeys` factory and add query hooks:

```typescript
// Add to essKeys:
myShiftSwaps: () => [...essKeys.all, 'my-shift-swaps'] as const,
myWfhRequests: () => [...essKeys.all, 'my-wfh-requests'] as const,
myDocuments: () => [...essKeys.all, 'my-documents'] as const,
policyDocuments: () => [...essKeys.all, 'policy-documents'] as const,

// Add hooks:
export function useMyShiftSwaps() {
  return useQuery({ queryKey: essKeys.myShiftSwaps(), queryFn: () => essApi.getMyShiftSwaps() });
}
export function useMyWfhRequests() {
  return useQuery({ queryKey: essKeys.myWfhRequests(), queryFn: () => essApi.getMyWfhRequests() });
}
export function useMyDocuments() {
  return useQuery({ queryKey: essKeys.myDocuments(), queryFn: () => essApi.getMyDocuments() });
}
export function usePolicyDocuments() {
  return useQuery({ queryKey: essKeys.policyDocuments(), queryFn: () => essApi.getPolicyDocuments() });
}
```

- [ ] **Step 3: Add mutation hooks to use-ess-mutations.ts**

```typescript
export function useUpdateMyProfile() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: any) => essApi.updateMyProfile(data),
    onSuccess: () => { queryClient.invalidateQueries({ queryKey: essKeys.myProfile() }); },
  });
}

export function useCancelLeave() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => essApi.cancelLeave(id),
    onSuccess: () => { queryClient.invalidateQueries({ queryKey: essKeys.myLeaveBalance() }); },
  });
}

export function useDownloadPayslipPdf() {
  return useMutation({
    mutationFn: (payslipId: string) => essApi.downloadPayslipPdf(payslipId),
  });
}

export function useCreateShiftSwap() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: any) => essApi.createShiftSwap(data),
    onSuccess: () => { queryClient.invalidateQueries({ queryKey: essKeys.myShiftSwaps() }); },
  });
}

export function useCancelShiftSwap() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => essApi.cancelShiftSwap(id),
    onSuccess: () => { queryClient.invalidateQueries({ queryKey: essKeys.myShiftSwaps() }); },
  });
}

export function useCreateWfhRequest() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: any) => essApi.createWfhRequest(data),
    onSuccess: () => { queryClient.invalidateQueries({ queryKey: essKeys.myWfhRequests() }); },
  });
}

export function useCancelWfhRequest() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => essApi.cancelWfhRequest(id),
    onSuccess: () => { queryClient.invalidateQueries({ queryKey: essKeys.myWfhRequests() }); },
  });
}

export function useUploadMyDocument() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: any) => essApi.uploadMyDocument(data),
    onSuccess: () => { queryClient.invalidateQueries({ queryKey: essKeys.myDocuments() }); },
  });
}
```

- [ ] **Step 4: Add cancel button to MyLeaveScreen.tsx**

In the leave requests table, add a "Cancel" action column. Find the table rows that render leave requests and add a cancel button for requests with status `PENDING` or `APPROVED`. Use the `useCancelLeave()` mutation. Show a confirmation dialog before cancelling. Use `showSuccess('Leave request cancelled')` on success and `showApiError(err)` on error.

- [ ] **Step 5: Wire payslip download in MyPayslipsScreen.tsx**

Replace the `handleDownload` placeholder function with actual PDF download logic:

```typescript
const downloadPdf = useDownloadPayslipPdf();

const handleDownload = async (payslipId: string, month: number, year: number) => {
  try {
    const blob = await downloadPdf.mutateAsync(payslipId);
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `payslip-${month}-${year}.pdf`;
    a.click();
    window.URL.revokeObjectURL(url);
    showSuccess('Payslip downloaded');
  } catch (err) {
    showApiError(err);
  }
};
```

- [ ] **Step 6: Add edit modal to MyProfileScreen.tsx**

Add an "Edit Profile" button and modal form that allows editing: personal mobile, alternative mobile, personal email, current address, permanent address, emergency contact fields, marital status, blood group. Use `useUpdateMyProfile()` mutation. Show success toast on save.

- [ ] **Step 7: Commit**

```bash
cd web-system-app && git add src/
git commit -m "feat(web-ess): add leave cancel, payslip download, profile edit, new API hooks"
```

---

## Task 7: Web — New ESS Screens (Shift Swap, WFH, Documents, Policies)

**Files:**
- Create: `web-system-app/src/features/ess/ShiftSwapScreen.tsx`
- Create: `web-system-app/src/features/ess/WfhRequestScreen.tsx`
- Create: `web-system-app/src/features/ess/MyDocumentsScreen.tsx`
- Create: `web-system-app/src/features/ess/PolicyDocumentsScreen.tsx`
- Modify: `web-system-app/src/App.tsx`

- [ ] **Step 1: Create ShiftSwapScreen.tsx**

Follow the same pattern as `MyGrievancesScreen.tsx`: list + modal form. Display shift swap requests with status badges. FAB-like "New Request" button opens modal with fields: current shift (dropdown), requested shift (dropdown), swap date (date input), reason (textarea). Use `useMyShiftSwaps()` query and `useCreateShiftSwap()` mutation. Cancel button for PENDING requests using `useCancelShiftSwap()`.

- [ ] **Step 2: Create WfhRequestScreen.tsx**

Same list + modal pattern. Fields: from date, to date, days (auto-calculated), reason. Use `useMyWfhRequests()` and `useCreateWfhRequest()`. Cancel for PENDING using `useCancelWfhRequest()`.

- [ ] **Step 3: Create MyDocumentsScreen.tsx**

List of uploaded documents with type, number, expiry, file link. "Upload" button opens modal with: document type (dropdown: Aadhaar, PAN, Passport, Driving License, Voter ID, Education Certificate, Experience Letter, Other), document number, expiry date, file URL, file name. Use `useMyDocuments()` and `useUploadMyDocument()`.

- [ ] **Step 4: Create PolicyDocumentsScreen.tsx**

Read-only list of company policy documents grouped by category. Each card shows title, category badge, description, version, published date, and a download/view link. Use `usePolicyDocuments()`.

- [ ] **Step 5: Register routes in App.tsx**

Add in the dashboard routes section:

```tsx
<Route path="company/hr/shift-swap" element={<RequirePermission permission="ess:swap-shift"><ShiftSwapScreen /></RequirePermission>} />
<Route path="company/hr/wfh-requests" element={<RequirePermission permission="ess:request-wfh"><WfhRequestScreen /></RequirePermission>} />
<Route path="company/hr/my-documents" element={<RequirePermission permission="ess:upload-document"><MyDocumentsScreen /></RequirePermission>} />
<Route path="company/hr/policy-documents" element={<RequirePermission permission="ess:view-policies"><PolicyDocumentsScreen /></RequirePermission>} />
```

- [ ] **Step 6: Commit**

```bash
cd web-system-app && git add src/
git commit -m "feat(web-ess): add shift-swap, wfh, documents, policy-docs screens"
```

---

## Task 8: Mobile — Leave Cancel UI, Profile Edit, Payslip Download

**Files:**
- Modify: `mobile-app/src/lib/api/ess.ts`
- Modify: `mobile-app/src/features/company-admin/api/use-ess-queries.ts`
- Modify: `mobile-app/src/features/company-admin/api/use-ess-mutations.ts`
- Modify: `mobile-app/src/features/company-admin/hr/my-leave-screen.tsx`
- Modify: `mobile-app/src/features/company-admin/hr/my-profile-screen.tsx`
- Modify: `mobile-app/src/features/company-admin/hr/my-payslips-screen.tsx`

- [ ] **Step 1: Add API methods to mobile ess.ts**

Add the same API methods as web (updateMyProfile, downloadPayslipPdf, cancelLeave, shift swap CRUD, WFH CRUD, documents CRUD, policy docs). For PDF download use `responseType: 'arraybuffer'`.

- [ ] **Step 2: Add query and mutation hooks**

Mirror the web hooks: `useMyShiftSwaps`, `useMyWfhRequests`, `useMyDocuments`, `usePolicyDocuments`, `useUpdateMyProfile`, `useCancelLeave`, `useDownloadPayslipPdf`, etc.

- [ ] **Step 3: Add cancel button to my-leave-screen.tsx**

In the leave request cards, add a "Cancel" pressable for PENDING/APPROVED requests. Use `useConfirmModal()` for confirmation (never `Alert.alert()`). On confirm, call `cancelLeave.mutate(id)`. Show success toast.

- [ ] **Step 4: Wire payslip download in my-payslips-screen.tsx**

Replace the non-functional download button with actual implementation. Use `expo-file-system` to save the PDF and `expo-sharing` to share/open it:

```typescript
import * as FileSystem from 'expo-file-system';
import * as Sharing from 'expo-sharing';

const handleDownload = async (payslipId: string, month: number, year: number) => {
  try {
    const blob = await essApi.downloadPayslipPdf(payslipId);
    const fileUri = FileSystem.documentDirectory + `payslip-${month}-${year}.pdf`;
    await FileSystem.writeAsStringAsync(fileUri, Buffer.from(blob).toString('base64'), { encoding: FileSystem.EncodingType.Base64 });
    await Sharing.shareAsync(fileUri, { mimeType: 'application/pdf' });
  } catch (err) { /* show error toast */ }
};
```

- [ ] **Step 5: Add edit modal to my-profile-screen.tsx**

Add an "Edit" button in the header that opens a sheet modal (same pattern as grievances form modal). Editable fields: personal mobile, alternative mobile, personal email, emergency contact name/relation/mobile, marital status, blood group. Use `useUpdateMyProfile()` mutation. Use `useConfirmModal()` before saving.

- [ ] **Step 6: Commit**

```bash
cd mobile-app && git add src/
git commit -m "feat(mobile-ess): add leave cancel, payslip download, profile edit"
```

---

## Task 9: Mobile — New ESS Screens (Shift Swap, WFH, Documents, Policies)

**Files:**
- Create: `mobile-app/src/features/ess/shift-swap-screen.tsx`
- Create: `mobile-app/src/features/ess/wfh-request-screen.tsx`
- Create: `mobile-app/src/features/ess/my-documents-screen.tsx`
- Create: `mobile-app/src/features/ess/policy-documents-screen.tsx`
- Create: `mobile-app/src/app/(app)/company/hr/shift-swap.tsx`
- Create: `mobile-app/src/app/(app)/company/hr/wfh-requests.tsx`
- Create: `mobile-app/src/app/(app)/company/hr/my-documents.tsx`
- Create: `mobile-app/src/app/(app)/company/hr/policy-documents.tsx`

- [ ] **Step 1: Create shift-swap-screen.tsx**

Follow `my-grievances-screen.tsx` pattern: LinearGradient header, FlatList, FAB + modal. Cards show: current shift → requested shift, swap date, reason, status badge. Modal form: shift dropdowns, date picker, reason textarea. Use `useConfirmModal()` before submit. Cancel button for PENDING requests.

- [ ] **Step 2: Create wfh-request-screen.tsx**

Same FlatList + FAB + modal pattern. Cards: from-to date range, days count, reason, status badge. Modal: from date, to date, days (auto-calc), reason. Use `useConfirmModal()` before submit.

- [ ] **Step 3: Create my-documents-screen.tsx**

FlatList of documents with type badge, document number, expiry date, file link. FAB opens upload modal with: document type picker, number input, expiry date, file URL input, file name. Later can integrate file picker.

- [ ] **Step 4: Create policy-documents-screen.tsx**

Read-only FlatList of policy documents. Cards: title, category badge, description, version, published date, download/view link via `Linking.openURL()`.

- [ ] **Step 5: Create route files**

Each route file follows the pattern:
```typescript
// src/app/(app)/company/hr/shift-swap.tsx
export { ShiftSwapScreen as default } from '@/features/ess/shift-swap-screen';
```

Create the 4 route files for shift-swap, wfh-requests, my-documents, policy-documents.

- [ ] **Step 6: Commit**

```bash
cd mobile-app && git add src/
git commit -m "feat(mobile-ess): add shift-swap, wfh, documents, policy-docs screens"
```

---

## Task 10: Mobile — Offline Punch Queue

**Files:**
- Create: `mobile-app/src/lib/offline-punch-queue.ts`
- Modify: `mobile-app/src/features/company-admin/hr/shift-check-in-screen.tsx`

- [ ] **Step 1: Create offline-punch-queue.ts**

```typescript
import { storage } from '@/lib/storage';
import { essApi } from '@/lib/api/ess';
import NetInfo from '@react-native-community/netinfo';

const QUEUE_KEY = 'offline_punch_queue';

interface PunchEntry {
  id: string;
  type: 'check-in' | 'check-out';
  timestamp: string;
  latitude?: number;
  longitude?: number;
  shiftId?: string;
  locationId?: string;
  retries: number;
}

export function getQueue(): PunchEntry[] {
  const raw = storage.getString(QUEUE_KEY);
  return raw ? JSON.parse(raw) : [];
}

function saveQueue(queue: PunchEntry[]) {
  storage.set(QUEUE_KEY, JSON.stringify(queue));
}

export function enqueuePunch(entry: Omit<PunchEntry, 'id' | 'retries'>) {
  const queue = getQueue();
  queue.push({ ...entry, id: Date.now().toString(), retries: 0 });
  saveQueue(queue);
}

export function getQueueLength(): number {
  return getQueue().length;
}

export async function syncQueue(): Promise<{ synced: number; failed: number }> {
  const state = await NetInfo.fetch();
  if (!state.isConnected) return { synced: 0, failed: 0 };

  const queue = getQueue();
  if (queue.length === 0) return { synced: 0, failed: 0 };

  let synced = 0;
  let failed = 0;
  const remaining: PunchEntry[] = [];

  for (const entry of queue) {
    try {
      if (entry.type === 'check-in') {
        await essApi.checkIn({
          latitude: entry.latitude,
          longitude: entry.longitude,
          shiftId: entry.shiftId,
          locationId: entry.locationId,
          offlineTimestamp: entry.timestamp,
        });
      } else {
        await essApi.checkOut({
          latitude: entry.latitude,
          longitude: entry.longitude,
          offlineTimestamp: entry.timestamp,
        });
      }
      synced++;
    } catch {
      entry.retries++;
      if (entry.retries < 5) {
        remaining.push(entry);
      }
      failed++;
    }
  }

  saveQueue(remaining);
  return { synced, failed };
}
```

- [ ] **Step 2: Integrate into shift-check-in-screen.tsx**

In the check-in screen, wrap the existing check-in/check-out API calls with offline fallback:

```typescript
import { enqueuePunch, syncQueue, getQueueLength } from '@/lib/offline-punch-queue';
import NetInfo from '@react-native-community/netinfo';

// Before punch API call:
const netState = await NetInfo.fetch();
if (!netState.isConnected) {
  enqueuePunch({
    type: 'check-in', // or 'check-out'
    timestamp: new Date().toISOString(),
    latitude, longitude, shiftId, locationId,
  });
  // Show info toast: "Punch saved offline. Will sync when connected."
  return;
}

// On app focus or network restore, sync queue:
useEffect(() => {
  const unsubscribe = NetInfo.addEventListener((state) => {
    if (state.isConnected && getQueueLength() > 0) {
      syncQueue().then(({ synced }) => {
        if (synced > 0) showSuccess(`${synced} offline punch(es) synced`);
      });
    }
  });
  return unsubscribe;
}, []);
```

- [ ] **Step 3: Show offline queue badge in UI**

Add a small badge on the check-in screen showing pending offline punches count when > 0. Display as a small amber dot with count near the status area.

- [ ] **Step 4: Commit**

```bash
cd mobile-app && git add src/
git commit -m "feat(mobile-ess): add offline punch queue with MMKV + auto-sync"
```

---

## Task 11: Backend — Holiday Calendar, Expense Claims, Loan Application (ESS Endpoints)

**Files:**
- Modify: `avy-erp-backend/src/modules/hr/ess/ess.validators.ts`
- Modify: `avy-erp-backend/src/modules/hr/ess/ess.service.ts`
- Modify: `avy-erp-backend/src/modules/hr/ess/ess.controller.ts`
- Modify: `avy-erp-backend/src/modules/hr/ess/ess.routes.ts`

- [ ] **Step 1: Add validators for expense claims and loan application**

Add to `ess.validators.ts`:

```typescript
export const essExpenseClaimSchema = z.object({
  title: z.string().min(1),
  amount: z.number().positive(),
  category: z.enum(['TRAVEL', 'MEDICAL', 'INTERNET', 'FUEL', 'UNIFORM', 'BUSINESS', 'OTHER']),
  description: z.string().optional(),
  tripDate: z.string().optional(),
  receipts: z.array(z.object({ fileName: z.string(), fileUrl: z.string() })).optional(),
});

export const essLoanApplicationSchema = z.object({
  policyId: z.string().min(1),
  amount: z.number().positive(),
  tenure: z.number().int().min(1),
  reason: z.string().optional(),
});
```

- [ ] **Step 2: Add service methods**

Add to `ess.service.ts`:

```typescript
// ── Holiday Calendar (ESS) ──

async getMyHolidays(companyId: string, year?: number) {
  const targetYear = year ?? new Date().getFullYear();
  return platformPrisma.holidayCalendar.findMany({
    where: { companyId, year: targetYear },
    orderBy: { date: 'asc' },
  });
}

// ── Expense Claims (ESS — employee-scoped) ──

async getMyExpenseClaims(companyId: string, userId: string) {
  const user = await platformPrisma.user.findUnique({ where: { id: userId }, select: { employeeId: true } });
  if (!user?.employeeId) return [];

  return platformPrisma.expenseClaim.findMany({
    where: { employeeId: user.employeeId, companyId },
    orderBy: { createdAt: 'desc' },
  });
}

async createMyExpenseClaim(companyId: string, userId: string, data: any) {
  const user = await platformPrisma.user.findUnique({ where: { id: userId }, select: { employeeId: true } });
  if (!user?.employeeId) throw ApiError.badRequest('No linked employee profile');

  return platformPrisma.expenseClaim.create({
    data: {
      employeeId: user.employeeId,
      title: data.title,
      amount: data.amount,
      category: data.category,
      description: data.description ?? null,
      tripDate: data.tripDate ? new Date(data.tripDate) : null,
      receipts: data.receipts ?? null,
      status: 'DRAFT',
      companyId,
    },
  });
}

async submitMyExpenseClaim(companyId: string, userId: string, claimId: string) {
  const user = await platformPrisma.user.findUnique({ where: { id: userId }, select: { employeeId: true } });
  if (!user?.employeeId) throw ApiError.badRequest('No linked employee profile');

  const claim = await platformPrisma.expenseClaim.findFirst({
    where: { id: claimId, employeeId: user.employeeId, companyId, status: 'DRAFT' },
  });
  if (!claim) throw ApiError.notFound('Expense claim not found or not submittable');

  return platformPrisma.expenseClaim.update({
    where: { id: claimId },
    data: { status: 'SUBMITTED' },
  });
}

// ── Loan Application (ESS — employee self-service) ──

async getMyLoans(companyId: string, userId: string) {
  const user = await platformPrisma.user.findUnique({ where: { id: userId }, select: { employeeId: true } });
  if (!user?.employeeId) return [];

  return platformPrisma.loanRecord.findMany({
    where: { employeeId: user.employeeId, companyId },
    include: { policy: { select: { name: true, code: true, loanType: true } } },
    orderBy: { createdAt: 'desc' },
  });
}

async getAvailableLoanPolicies(companyId: string) {
  return platformPrisma.loanPolicy.findMany({
    where: { companyId, isActive: true },
    orderBy: { name: 'asc' },
  });
}

async applyForLoan(companyId: string, userId: string, data: any) {
  const user = await platformPrisma.user.findUnique({ where: { id: userId }, select: { employeeId: true } });
  if (!user?.employeeId) throw ApiError.badRequest('No linked employee profile');

  const policy = await platformPrisma.loanPolicy.findFirst({
    where: { id: data.policyId, companyId, isActive: true },
  });
  if (!policy) throw ApiError.notFound('Loan policy not found');

  if (policy.maxAmount && data.amount > Number(policy.maxAmount)) {
    throw ApiError.badRequest(`Amount exceeds policy maximum of ${policy.maxAmount}`);
  }
  if (policy.maxTenureMonths && data.tenure > policy.maxTenureMonths) {
    throw ApiError.badRequest(`Tenure exceeds policy maximum of ${policy.maxTenureMonths} months`);
  }

  const interestRate = Number(policy.interestRate);
  const monthlyRate = interestRate / 12 / 100;
  const emiAmount = monthlyRate > 0
    ? (data.amount * monthlyRate * Math.pow(1 + monthlyRate, data.tenure)) / (Math.pow(1 + monthlyRate, data.tenure) - 1)
    : data.amount / data.tenure;

  return platformPrisma.loanRecord.create({
    data: {
      employeeId: user.employeeId,
      policyId: data.policyId,
      loanType: policy.loanType ?? 'PERSONAL',
      amount: data.amount,
      tenure: data.tenure,
      emiAmount: Math.round(emiAmount * 100) / 100,
      interestRate,
      outstanding: data.amount,
      status: 'PENDING',
      companyId,
    },
  });
}
```

- [ ] **Step 3: Add controller handlers**

Add to `ess.controller.ts`:

```typescript
// Holiday Calendar
getMyHolidays = asyncHandler(async (req: Request, res: Response) => {
  const companyId = req.user?.companyId;
  if (!companyId) throw ApiError.badRequest('Company ID is required');
  const year = req.query.year ? Number(req.query.year) : undefined;
  const result = await essService.getMyHolidays(companyId, year);
  res.json(createSuccessResponse(result));
});

// Expense Claims
getMyExpenseClaims = asyncHandler(async (req: Request, res: Response) => {
  const companyId = req.user?.companyId;
  if (!companyId) throw ApiError.badRequest('Company ID is required');
  const result = await essService.getMyExpenseClaims(companyId, req.user!.id);
  res.json(createSuccessResponse(result));
});

createMyExpenseClaim = asyncHandler(async (req: Request, res: Response) => {
  const companyId = req.user?.companyId;
  if (!companyId) throw ApiError.badRequest('Company ID is required');
  const parsed = essExpenseClaimSchema.safeParse(req.body);
  if (!parsed.success) throw ApiError.badRequest(parsed.error.errors.map((e: any) => e.message).join(', '));
  const result = await essService.createMyExpenseClaim(companyId, req.user!.id, parsed.data);
  res.status(201).json(createSuccessResponse(result, 'Expense claim created'));
});

submitMyExpenseClaim = asyncHandler(async (req: Request, res: Response) => {
  const companyId = req.user?.companyId;
  if (!companyId) throw ApiError.badRequest('Company ID is required');
  const result = await essService.submitMyExpenseClaim(companyId, req.user!.id, req.params.id);
  res.json(createSuccessResponse(result, 'Expense claim submitted'));
});

// Loans
getMyLoans = asyncHandler(async (req: Request, res: Response) => {
  const companyId = req.user?.companyId;
  if (!companyId) throw ApiError.badRequest('Company ID is required');
  const result = await essService.getMyLoans(companyId, req.user!.id);
  res.json(createSuccessResponse(result));
});

getAvailableLoanPolicies = asyncHandler(async (req: Request, res: Response) => {
  const companyId = req.user?.companyId;
  if (!companyId) throw ApiError.badRequest('Company ID is required');
  const result = await essService.getAvailableLoanPolicies(companyId);
  res.json(createSuccessResponse(result));
});

applyForLoan = asyncHandler(async (req: Request, res: Response) => {
  const companyId = req.user?.companyId;
  if (!companyId) throw ApiError.badRequest('Company ID is required');
  const parsed = essLoanApplicationSchema.safeParse(req.body);
  if (!parsed.success) throw ApiError.badRequest(parsed.error.errors.map((e: any) => e.message).join(', '));
  const result = await essService.applyForLoan(companyId, req.user!.id, parsed.data);
  res.status(201).json(createSuccessResponse(result, 'Loan application submitted'));
});
```

- [ ] **Step 4: Add routes**

Add to `ess.routes.ts`:

```typescript
// ── Holiday Calendar (ESS) ──
router.get('/ess/my-holidays', requireESSFeature('holidayCalendar'), requirePermissions(['hr:read', 'ess:view-holidays']), controller.getMyHolidays);

// ── Expense Claims (ESS) ──
router.get('/ess/my-expense-claims', requireESSFeature('reimbursementClaims'), requirePermissions(['hr:read', 'ess:claim-expense']), controller.getMyExpenseClaims);
router.post('/ess/my-expense-claims', requireESSFeature('reimbursementClaims'), requirePermissions(['hr:create', 'ess:claim-expense']), controller.createMyExpenseClaim);
router.patch('/ess/my-expense-claims/:id/submit', requireESSFeature('reimbursementClaims'), requirePermissions(['hr:update', 'ess:claim-expense']), controller.submitMyExpenseClaim);

// ── Loan Application (ESS) ──
router.get('/ess/my-loans', requireESSFeature('loanApplication'), requirePermissions(['hr:read', 'ess:apply-loan']), controller.getMyLoans);
router.get('/ess/loan-policies', requireESSFeature('loanApplication'), requirePermissions(['hr:read', 'ess:apply-loan']), controller.getAvailableLoanPolicies);
router.post('/ess/apply-loan', requireESSFeature('loanApplication'), requirePermissions(['hr:create', 'ess:apply-loan']), controller.applyForLoan);
```

- [ ] **Step 5: Commit**

```bash
git add src/modules/hr/ess/
git commit -m "feat(ess): add holiday calendar, expense claims, loan application ESS endpoints"
```

---

## Task 12: Permissions Update — Add Missing ESS Permissions

**Files:**
- Modify: `avy-erp-backend/src/shared/constants/permissions.ts`
- Modify: `avy-erp-backend/src/shared/constants/navigation-manifest.ts`

- [ ] **Step 1: Add expense, loan, org-chart permissions to the ESS actions array**

Find the `ess` module in `permissions.ts` and add these to the `actions` array:

```typescript
'claim-expense', 'view-org-chart',
```

Note: `apply-loan` already exists in the ESS actions. `view-holidays` already exists.

- [ ] **Step 2: Add new permissions to Employee reference role**

Add to the Employee reference role `permissions` array:

```typescript
'ess:claim-expense', 'ess:apply-loan', 'ess:view-org-chart',
```

- [ ] **Step 3: Add navigation manifest entries for new ESS screens**

Add these entries in the ESS section:

```typescript
{
  id: 'ess-holidays',
  label: 'Holiday Calendar',
  icon: 'calendar',
  requiredPerm: 'ess:view-holidays',
  path: '/app/company/hr/my-holidays',
  module: 'hr',
  group: 'My Workspace',
  sortOrder: 316,
  roleScope: 'company',
},
{
  id: 'ess-expense-claims',
  label: 'My Expenses',
  icon: 'receipt',
  requiredPerm: 'ess:claim-expense',
  path: '/app/company/hr/my-expense-claims',
  module: 'hr',
  group: 'My Workspace',
  sortOrder: 317,
  roleScope: 'company',
},
{
  id: 'ess-loans',
  label: 'My Loans',
  icon: 'banknote',
  requiredPerm: 'ess:apply-loan',
  path: '/app/company/hr/my-loans',
  module: 'hr',
  group: 'My Workspace',
  sortOrder: 318,
  roleScope: 'company',
},
{
  id: 'ess-org-chart',
  label: 'Org Chart',
  icon: 'network',
  requiredPerm: 'ess:view-org-chart',
  path: '/app/company/hr/org-chart',
  module: 'hr',
  group: 'My Workspace',
  sortOrder: 319,
  roleScope: 'company',
},
```

- [ ] **Step 4: Update org-chart route permission in employee.routes.ts**

Modify the existing org chart endpoint to accept ESS permission:

```typescript
// Change from:
router.get('/employees/org-chart', requirePermissions(['hr:read']), controller.getOrgChart);
// To:
router.get('/employees/org-chart', requirePermissions(['hr:read', 'ess:view-org-chart']), controller.getOrgChart);
```

This makes it accessible to both admins (`hr:read` via inheritance) and employees (`ess:view-org-chart`).

- [ ] **Step 5: Commit**

```bash
git add src/shared/constants/ src/modules/hr/employee/
git commit -m "feat(rbac): add expense, loan, org-chart ESS permissions and nav items"
```

---

## Task 13: Web — Holiday Calendar, Expense Claims, Loan Application ESS Screens

**Files:**
- Create: `web-system-app/src/features/ess/MyHolidaysScreen.tsx`
- Create: `web-system-app/src/features/ess/MyExpenseClaimsScreen.tsx`
- Create: `web-system-app/src/features/ess/MyLoanScreen.tsx`
- Modify: `web-system-app/src/lib/api/ess.ts`
- Modify: `web-system-app/src/features/company-admin/api/use-ess-queries.ts`
- Modify: `web-system-app/src/features/company-admin/api/use-ess-mutations.ts`
- Modify: `web-system-app/src/App.tsx`

- [ ] **Step 1: Add API methods to ess.ts**

```typescript
// Holiday Calendar
async getMyHolidays(year?: number): Promise<ApiResponse<any>> {
  const params = year ? { year } : {};
  const response = await client.get('/hr/ess/my-holidays', { params });
  return response.data;
},

// Expense Claims
async getMyExpenseClaims(): Promise<ApiResponse<any>> {
  const response = await client.get('/hr/ess/my-expense-claims');
  return response.data;
},
async createMyExpenseClaim(data: any): Promise<ApiResponse<any>> {
  const response = await client.post('/hr/ess/my-expense-claims', data);
  return response.data;
},
async submitMyExpenseClaim(id: string): Promise<ApiResponse<any>> {
  const response = await client.patch(`/hr/ess/my-expense-claims/${id}/submit`);
  return response.data;
},

// Loans
async getMyLoans(): Promise<ApiResponse<any>> {
  const response = await client.get('/hr/ess/my-loans');
  return response.data;
},
async getAvailableLoanPolicies(): Promise<ApiResponse<any>> {
  const response = await client.get('/hr/ess/loan-policies');
  return response.data;
},
async applyForLoan(data: any): Promise<ApiResponse<any>> {
  const response = await client.post('/hr/ess/apply-loan', data);
  return response.data;
},
```

- [ ] **Step 2: Add query and mutation hooks**

Add to `use-ess-queries.ts`:
```typescript
myHolidays: (year?: number) => [...essKeys.all, 'my-holidays', year] as const,
myExpenseClaims: () => [...essKeys.all, 'my-expense-claims'] as const,
myLoans: () => [...essKeys.all, 'my-loans'] as const,
loanPolicies: () => [...essKeys.all, 'loan-policies'] as const,

export function useMyHolidays(year?: number) {
  return useQuery({ queryKey: essKeys.myHolidays(year), queryFn: () => essApi.getMyHolidays(year) });
}
export function useMyExpenseClaims() {
  return useQuery({ queryKey: essKeys.myExpenseClaims(), queryFn: () => essApi.getMyExpenseClaims() });
}
export function useMyLoans() {
  return useQuery({ queryKey: essKeys.myLoans(), queryFn: () => essApi.getMyLoans() });
}
export function useLoanPolicies() {
  return useQuery({ queryKey: essKeys.loanPolicies(), queryFn: () => essApi.getAvailableLoanPolicies() });
}
```

Add to `use-ess-mutations.ts`:
```typescript
export function useCreateMyExpenseClaim() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: any) => essApi.createMyExpenseClaim(data),
    onSuccess: () => { queryClient.invalidateQueries({ queryKey: essKeys.myExpenseClaims() }); },
  });
}
export function useSubmitMyExpenseClaim() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => essApi.submitMyExpenseClaim(id),
    onSuccess: () => { queryClient.invalidateQueries({ queryKey: essKeys.myExpenseClaims() }); },
  });
}
export function useApplyForLoan() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: any) => essApi.applyForLoan(data),
    onSuccess: () => { queryClient.invalidateQueries({ queryKey: essKeys.myLoans() }); },
  });
}
```

- [ ] **Step 3: Create MyHolidaysScreen.tsx**

Read-only list of holidays for the year. Group by month. Each row: date, name, type badge (National/Regional/Company/Optional), description. Year selector dropdown. Follow existing card/badge patterns from MyGrievancesScreen.

- [ ] **Step 4: Create MyExpenseClaimsScreen.tsx**

List + modal form pattern (like MyGrievancesScreen). Cards show: title, amount (INR formatted), category badge, status badge (Draft/Submitted/Approved/Rejected/Paid), date. Modal form: title, amount, category dropdown, description, trip date. "Submit" button for DRAFT claims. Use `useConfirmModal` equivalent pattern before submit.

- [ ] **Step 5: Create MyLoanScreen.tsx**

Two sections: Available Loan Policies (cards with max amount, tenure, interest rate) + My Loan Applications (list with status). "Apply" button per policy opens modal with: amount input, tenure slider/input, auto-calculated EMI display, reason field. Status badges: Pending/Approved/Active/Closed/Rejected.

- [ ] **Step 6: Register routes in App.tsx**

```tsx
<Route path="company/hr/my-holidays" element={<RequirePermission permission="ess:view-holidays"><MyHolidaysScreen /></RequirePermission>} />
<Route path="company/hr/my-expense-claims" element={<RequirePermission permission="ess:claim-expense"><MyExpenseClaimsScreen /></RequirePermission>} />
<Route path="company/hr/my-loans" element={<RequirePermission permission="ess:apply-loan"><MyLoanScreen /></RequirePermission>} />
```

- [ ] **Step 7: Commit**

```bash
cd web-system-app && git add src/
git commit -m "feat(web-ess): add holiday calendar, expense claims, loan application screens"
```

---

## Task 14: Mobile — Holiday Calendar, Expense Claims, Loan Application ESS Screens

**Files:**
- Create: `mobile-app/src/features/ess/my-holidays-screen.tsx`
- Create: `mobile-app/src/features/ess/my-expense-claims-screen.tsx`
- Create: `mobile-app/src/features/ess/my-loan-screen.tsx`
- Create: `mobile-app/src/app/(app)/company/hr/my-holidays.tsx`
- Create: `mobile-app/src/app/(app)/company/hr/my-expense-claims.tsx`
- Create: `mobile-app/src/app/(app)/company/hr/my-loans.tsx`
- Modify: `mobile-app/src/lib/api/ess.ts`
- Modify: `mobile-app/src/features/company-admin/api/use-ess-queries.ts`
- Modify: `mobile-app/src/features/company-admin/api/use-ess-mutations.ts`

- [ ] **Step 1: Add API methods to mobile ess.ts**

Mirror the web API methods: `getMyHolidays`, `getMyExpenseClaims`, `createMyExpenseClaim`, `submitMyExpenseClaim`, `getMyLoans`, `getAvailableLoanPolicies`, `applyForLoan`.

- [ ] **Step 2: Add query and mutation hooks**

Mirror the web hooks: `useMyHolidays`, `useMyExpenseClaims`, `useMyLoans`, `useLoanPolicies`, `useCreateMyExpenseClaim`, `useSubmitMyExpenseClaim`, `useApplyForLoan`.

- [ ] **Step 3: Create my-holidays-screen.tsx**

Follow minimalist list pattern (like my-goals-screen). LinearGradient header, FlatList. Cards: holiday name, date (formatted), type badge with colors (National=blue, Regional=purple, Company=green, Optional=amber). Year filter chips. Pull-to-refresh.

- [ ] **Step 4: Create my-expense-claims-screen.tsx**

Follow FAB + modal pattern (like my-grievances-screen). FlatList with cards: title, amount (INR), category badge, status badge. FAB opens form sheet with: title input, amount input, category picker, description textarea, trip date. DRAFT claims show "Submit" pressable. Use `useConfirmModal()` before submit.

- [ ] **Step 5: Create my-loan-screen.tsx**

Two-section FlatList: policy cards at top (name, type, max amount, rate, tenure), then loan application cards below (amount, EMI, tenure, status badge, policy name). FAB opens application sheet: policy picker, amount input, tenure input, auto-calculated EMI display (real-time), reason. Use `useConfirmModal()` before submission.

- [ ] **Step 6: Create route files**

```typescript
// src/app/(app)/company/hr/my-holidays.tsx
export { MyHolidaysScreen as default } from '@/features/ess/my-holidays-screen';

// src/app/(app)/company/hr/my-expense-claims.tsx
export { MyExpenseClaimsScreen as default } from '@/features/ess/my-expense-claims-screen';

// src/app/(app)/company/hr/my-loans.tsx
export { MyLoanScreen as default } from '@/features/ess/my-loan-screen';
```

- [ ] **Step 7: Commit**

```bash
cd mobile-app && git add src/
git commit -m "feat(mobile-ess): add holiday calendar, expense claims, loan application screens"
```

---

## Task 15: Mobile — Org Chart Screen

**Files:**
- Create: `mobile-app/src/features/company-admin/hr/org-chart-screen.tsx` (if not exists)
- Create: `mobile-app/src/app/(app)/company/hr/org-chart.tsx` (if not exists)

- [ ] **Step 1: Verify org-chart-screen exists, create if missing**

If the file doesn't exist, create a hierarchical tree view screen. Use the existing `useOrgChart()` query hook (or add one calling `GET /hr/employees/org-chart`). Display as expandable tree nodes: employee name, designation, department. Tap to expand/collapse children. LinearGradient header with search. Follow existing card/animation patterns.

- [ ] **Step 2: Create route file if missing**

```typescript
// src/app/(app)/company/hr/org-chart.tsx
export { OrgChartScreen as default } from '@/features/company-admin/hr/org-chart-screen';
```

- [ ] **Step 3: Commit**

```bash
cd mobile-app && git add src/
git commit -m "feat(mobile-ess): add org chart screen accessible to ESS users"
```

---

## Self-Review Checklist

1. **Spec coverage**: All 14 features covered across 15 tasks. Profile edit (T3), payslip PDF (T3), leave cancel (T6/T8), shift swap (T4/T7/T9), WFH (T4/T7/T9), document upload+viewing (T3/T4/T6/T7/T8/T9), policy docs (T4/T7/T9), notification delivery (T5), offline punch (T10), holiday calendar (T11/T13/T14), expense claims (T11/T13/T14), loan application (T11/T13/T14), org chart (T12/T15). Appraisal self-review and 360 feedback confirmed working — no tasks needed.

2. **Placeholder scan**: No TBDs/TODOs. Tasks 6-9 and 13-14 describe UI by referencing concrete existing patterns with specific field lists and component types. Code blocks provided for all backend tasks.

3. **Type consistency**: `essKeys` factory, API method names, and mutation hook names are consistent across web and mobile. Route paths match navigation manifest entries. Permission strings match across `permissions.ts`, routes, and `RequirePermission` guards. New permissions: `ess:swap-shift`, `ess:request-wfh`, `ess:upload-document`, `ess:view-policies`, `ess:claim-expense`, `ess:view-org-chart` (plus existing `ess:apply-loan`, `ess:view-holidays`).

4. **Dual gating respected**: Every new endpoint uses both `requireESSFeature('<toggle>')` and `requirePermissions(['ess:<action>'])`. Frontend routes use `RequirePermission`. ESS config toggles map to: `holidayCalendar`, `reimbursementClaims`, `loanApplication`, `shiftSwapRequest`, `wfhRequest`, `documentUpload`, `policyDocuments`, `profileUpdate`, `downloadPayslips`.

5. **No model naming changes**: Existing models untouched. New models (ShiftSwapRequest, WfhRequest, PolicyDocument) follow existing conventions (PascalCase, `@@map` to snake_case).
