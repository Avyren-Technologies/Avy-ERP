# Form 16 PDF Generation + Comp-Off Expiry Cron — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Generate downloadable Form 16 PDFs (Part A + Part B) using pdfkit, and implement a daily cron job to clean up expired compensatory leave balances.

**Architecture:** New `form16-pdf.service.ts` generates PDFs from existing `generateForm16()` JSON data, uploads to R2, stores URL. New cron job queries expired LeaveBalance records daily and zeroes them out with notification.

**Tech Stack:** pdfkit, Prisma, node-cron, R2/S3 upload, Luxon

**Spec:** `docs/superpowers/specs/2026-04-16-form16-pdf-compoff-cron-design.md`

---

## File Structure

### New Files
| File | Responsibility |
|------|---------------|
| `avy-erp-backend/src/modules/hr/payroll-run/form16-pdf.service.ts` | PDF generation using pdfkit |
| `avy-erp-backend/src/shared/jobs/compoff-expiry.job.ts` | Cron job for comp-off cleanup |

### Modified Files
| File | Change |
|------|--------|
| `avy-erp-backend/src/modules/hr/payroll-run/payroll-run.service.ts` | Update Form 16 endpoint to generate + store PDF |
| `avy-erp-backend/src/app/server.ts` | Register comp-off cron |
| `avy-erp-backend/src/shared/constants/trigger-events.ts` | Add `COMP_OFF_EXPIRED` |
| `avy-erp-backend/src/core/notifications/templates/defaults.ts` | Add template |
| `avy-erp-backend/src/shared/constants/notification-categories.ts` | Add mapping |
| Web ReportsHubScreen | Fix Form 16 report mapping |

---

## Task 1: Form 16 PDF Service

**Files:**
- Create: `avy-erp-backend/src/modules/hr/payroll-run/form16-pdf.service.ts`

- [ ] **Step 1: Create PDF generation service**

Create `form16-pdf.service.ts`. Use the same pdfkit pattern as `src/core/billing/pdf.service.ts` (dynamic import):

```typescript
import { logger } from '../../../config/logger';

interface Form16Data {
  // Part A
  employer: {
    name: string;
    pan: string;
    tan: string;
    address: string;
  };
  employee: {
    name: string;
    pan: string;
    assessmentYear: string;
    designation: string;
    uan: string;
  };
  // Part B
  grossSalary: number;
  exemptions: { section: string; amount: number }[];
  standardDeduction: number;
  incomeFromSalary: number;
  otherIncome: number;
  grossTotalIncome: number;
  deductions: { section: string; amount: number }[];
  totalDeductions: number;
  taxableIncome: number;
  taxOnIncome: number;
  rebate87A: number;
  surcharge: number;
  cess: number;
  totalTaxPayable: number;
  totalTdsDeducted: number;
  // Monthly breakdown
  monthlyBreakdown: {
    month: string;
    gross: number;
    pf: number;
    esi: number;
    pt: number;
    tds: number;
    net: number;
  }[];
}

export async function generateForm16PDF(data: Form16Data): Promise<Buffer> {
  const PDFDocument = (await import('pdfkit')).default;

  return new Promise((resolve, reject) => {
    const doc = new PDFDocument({ size: 'A4', margin: 40 });
    const buffers: Buffer[] = [];
    doc.on('data', (chunk: Buffer) => buffers.push(chunk));
    doc.on('end', () => resolve(Buffer.concat(buffers)));
    doc.on('error', reject);

    // ── Header ──
    doc.fontSize(14).font('Helvetica-Bold').text('FORM No. 16', { align: 'center' });
    doc.fontSize(8).font('Helvetica')
      .text('[See Rule 31(1)(a) of the Income-tax Rules, 1962]', { align: 'center' });
    doc.moveDown(0.5);

    // ── Part A ──
    doc.fontSize(11).font('Helvetica-Bold').text('PART A');
    doc.fontSize(8).font('Helvetica')
      .text('Certificate under section 203 of the Income-tax Act, 1961 for TDS on Salary');
    doc.moveDown(0.3);

    doc.fontSize(9).font('Helvetica');
    doc.text(`Name of Employer: ${data.employer.name}`);
    doc.text(`PAN: ${data.employer.pan}    TAN: ${data.employer.tan}`);
    doc.text(`Address: ${data.employer.address}`);
    doc.moveDown(0.3);
    doc.text(`Name of Employee: ${data.employee.name}`);
    doc.text(`PAN: ${data.employee.pan}    Assessment Year: ${data.employee.assessmentYear}`);
    doc.text(`Designation: ${data.employee.designation}    UAN: ${data.employee.uan}`);
    doc.moveDown(0.5);

    // ── Monthly TDS Summary Table ──
    doc.fontSize(9).font('Helvetica-Bold').text('Summary of Tax Deducted at Source');
    doc.moveDown(0.2);

    // Table header
    const tableTop = doc.y;
    const colWidths = [60, 70, 70, 60, 60, 60, 60];
    const headers = ['Month', 'Gross', 'PF', 'ESI', 'PT', 'TDS', 'Net'];
    let x = 40;
    doc.fontSize(7).font('Helvetica-Bold');
    headers.forEach((h, i) => {
      doc.text(h, x, tableTop, { width: colWidths[i], align: 'right' });
      x += colWidths[i];
    });
    doc.moveDown(0.3);

    // Table rows
    doc.font('Helvetica').fontSize(7);
    for (const m of data.monthlyBreakdown) {
      const y = doc.y;
      x = 40;
      const values = [m.month, m.gross, m.pf, m.esi, m.pt, m.tds, m.net];
      values.forEach((v, i) => {
        doc.text(typeof v === 'number' ? v.toLocaleString('en-IN') : v, x, y, { width: colWidths[i], align: 'right' });
        x += colWidths[i];
      });
      doc.moveDown(0.2);
    }
    doc.moveDown(0.5);

    // ── Part B ──
    doc.fontSize(11).font('Helvetica-Bold').text('PART B (Annexure)');
    doc.fontSize(8).font('Helvetica')
      .text('Details of Salary Paid and any other income and tax deducted');
    doc.moveDown(0.3);

    const addLine = (label: string, amount: number | string, indent = 0) => {
      doc.fontSize(8).font('Helvetica');
      const prefix = indent > 0 ? '  '.repeat(indent) : '';
      doc.text(`${prefix}${label}`, 40, doc.y, { continued: true, width: 350 });
      doc.text(typeof amount === 'number' ? `₹${amount.toLocaleString('en-IN')}` : amount, { align: 'right', width: 130 });
    };

    addLine('1. Gross Salary', data.grossSalary);
    for (const ex of data.exemptions) {
      addLine(`   Less: ${ex.section}`, ex.amount, 1);
    }
    addLine('2. Balance', data.grossSalary - data.exemptions.reduce((s, e) => s + e.amount, 0));
    addLine('3. Standard Deduction', data.standardDeduction);
    addLine('4. Income from Salary (2-3)', data.incomeFromSalary);
    addLine('5. Other Income', data.otherIncome);
    addLine('6. Gross Total Income (4+5)', data.grossTotalIncome);
    doc.moveDown(0.2);

    addLine('7. Deductions under Chapter VI-A', data.totalDeductions);
    for (const d of data.deductions) {
      addLine(`   ${d.section}`, d.amount, 1);
    }
    doc.moveDown(0.2);

    addLine('8. Total Taxable Income (6-7)', data.taxableIncome);
    addLine('9. Tax on Total Income', data.taxOnIncome);
    addLine('10. Rebate under S.87A', data.rebate87A);
    addLine('11. Surcharge', data.surcharge);
    addLine('12. Health & Education Cess (4%)', data.cess);
    addLine('13. Total Tax Payable', data.totalTaxPayable);
    doc.moveDown(0.3);

    doc.fontSize(9).font('Helvetica-Bold');
    addLine('14. Total TDS Deducted', data.totalTdsDeducted);
    doc.moveDown(0.5);

    // ── Verification ──
    doc.fontSize(7).font('Helvetica')
      .text('Verification: I hereby certify that the information given above is true, complete and correct.', 40);

    doc.end();
  });
}
```

- [ ] **Step 2: Commit**

```bash
cd /Users/chetan/Documents/Avyren-Technologies/Products/Mobile-ERP/avy-erp-backend
git add src/modules/hr/payroll-run/form16-pdf.service.ts
git commit -m "feat(payroll): add Form 16 PDF generation service using pdfkit"
```

---

## Task 2: Integrate PDF Generation into Existing Endpoints

**Files:**
- Modify: `avy-erp-backend/src/modules/hr/payroll-run/payroll-run.service.ts`

- [ ] **Step 1: Update generateForm16 to produce + upload PDFs**

Find the `generateForm16` method (around line 2904). After it generates the JSON data for each employee, add PDF generation and R2 upload:

```typescript
import { generateForm16PDF } from './form16-pdf.service';

// Inside generateForm16(), after building the form16Data for each employee:
// Generate PDF
const pdfBuffer = await generateForm16PDF(form16Data);

// Upload to R2
const key = `form16/${companyId}/${financialYear}/${employee.id}.pdf`;
const { uploadUrl } = await uploadService.requestUpload({
  companyId,
  category: 'FORM_16',
  entityId: employee.id,
  fileName: `Form16_${employee.name}_${financialYear}.pdf`,
  fileSize: pdfBuffer.length,
  contentType: 'application/pdf',
});
// Upload the buffer
await r2Service.uploadBuffer(key, pdfBuffer, 'application/pdf');

// Store PDF URL
form16Record.pdfUrl = r2Service.getPublicUrl(key);
```

Read the existing upload service and R2 service to understand the exact API. The billing pdf.service.ts has the pattern.

If direct buffer upload is not supported, generate a presigned URL and upload via HTTP PUT. Adapt to the existing pattern.

- [ ] **Step 2: Commit**

```bash
cd /Users/chetan/Documents/Avyren-Technologies/Products/Mobile-ERP/avy-erp-backend
git add src/modules/hr/payroll-run/payroll-run.service.ts
git commit -m "feat(payroll): integrate Form 16 PDF generation + R2 upload into endpoint"
```

---

## Task 3: Comp-Off Expiry Cron Job

**Files:**
- Create: `avy-erp-backend/src/shared/jobs/compoff-expiry.job.ts`
- Modify: `avy-erp-backend/src/app/server.ts`
- Modify: `avy-erp-backend/src/shared/constants/trigger-events.ts`
- Modify: `avy-erp-backend/src/core/notifications/templates/defaults.ts`
- Modify: `avy-erp-backend/src/shared/constants/notification-categories.ts`

- [ ] **Step 1: Add trigger event and notification template**

In `trigger-events.ts`:
```typescript
  {
    value: 'COMP_OFF_EXPIRED',
    label: 'Compensatory Off Expired',
    module: 'Leave',
    description: 'Triggered when compensatory off leave balance expires',
  },
```

In `defaults.ts`:
```typescript
  {
    code: 'COMP_OFF_EXPIRED',
    name: 'Compensatory Off Expired',
    subject: 'Compensatory Off Expired',
    body: 'Your compensatory off balance of {{days}} day(s) has expired. The balance has been reset.',
    channels: ['PUSH', 'IN_APP'],
    priority: 'LOW',
    variables: ['employee_name', 'days', 'date'],
    sensitiveFields: [],
    category: 'OVERTIME',
    triggerEvent: 'COMP_OFF_EXPIRED',
    recipientRole: 'SELF',
  },
```

In `notification-categories.ts`: `COMP_OFF_EXPIRED: 'OVERTIME',`

- [ ] **Step 2: Create cron job**

Create `avy-erp-backend/src/shared/jobs/compoff-expiry.job.ts`:

```typescript
import cron from 'node-cron';
import { platformPrisma } from '../../config/database';
import { logger } from '../../config/logger';
import { notificationService } from '../../core/notifications/notification.service';

class CompOffExpiryCronService {
  /**
   * Clean up expired compensatory leave balances.
   * Runs daily at 1:00 AM.
   */
  async processExpiredCompOff() {
    const now = new Date();

    // Find all expired comp-off balances with remaining balance
    const expiredBalances = await platformPrisma.leaveBalance.findMany({
      where: {
        expiresAt: { lt: now },
        balance: { gt: 0 },
        leaveType: { category: 'COMPENSATORY' },
      },
      include: {
        leaveType: { select: { name: true } },
      },
    });

    if (expiredBalances.length === 0) {
      logger.debug('No expired comp-off balances found');
      return;
    }

    let processed = 0;

    for (const balance of expiredBalances) {
      const expiredDays = Number(balance.balance);

      // Zero out the balance
      await platformPrisma.leaveBalance.update({
        where: { id: balance.id },
        data: {
          balance: 0,
          adjusted: { decrement: expiredDays },
        },
      });

      // Notify employee
      await notificationService.dispatch({
        companyId: balance.companyId,
        triggerEvent: 'COMP_OFF_EXPIRED',
        entityType: 'LeaveBalance',
        entityId: balance.id,
        explicitRecipients: [balance.employeeId],
        tokens: {
          employee_name: '',
          days: expiredDays,
          date: balance.expiresAt!.toISOString().split('T')[0],
        },
        priority: 'LOW',
        type: 'OVERTIME',
        actionUrl: '/company/hr/my-leave',
      }).catch((err: any) => logger.warn('Failed to dispatch COMP_OFF_EXPIRED notification', err));

      processed++;
    }

    logger.info(`Comp-off expiry processed: ${processed} balances expired`);
  }

  startAll() {
    // Daily at 1:00 AM
    cron.schedule('0 1 * * *', () => {
      this.processExpiredCompOff().catch((err) =>
        logger.error('Comp-off expiry cron failed', err),
      );
    });

    logger.info('Comp-off expiry cron job started (daily@1AM)');
  }
}

export const compOffExpiryCronService = new CompOffExpiryCronService();
```

- [ ] **Step 3: Register in server.ts**

In `avy-erp-backend/src/app/server.ts`, after existing cron registrations:

```typescript
import { compOffExpiryCronService } from '../shared/jobs/compoff-expiry.job';

// In startup:
compOffExpiryCronService.startAll();
```

- [ ] **Step 4: Commit**

```bash
cd /Users/chetan/Documents/Avyren-Technologies/Products/Mobile-ERP/avy-erp-backend
git add src/shared/jobs/compoff-expiry.job.ts src/app/server.ts src/shared/constants/ src/core/notifications/
git commit -m "feat(leave): add comp-off expiry daily cron with notification"
```

---

## Task 4: Web — Fix Form 16 Report Mapping

**Files:**
- Modify: `web-system-app/src/features/company-admin/hr/analytics/ReportsHubScreen.tsx`

- [ ] **Step 1: Fix the Form 16 report button**

In ReportsHubScreen, find where "Form 16" report is listed. The report definition likely maps to a report generator key. Ensure it calls the correct endpoint (`POST /payroll-reports/form-16`) instead of a non-existent analytics export.

If the button currently calls `analyticsApi.exportReport('form-16', params)`, change it to call the payroll Form 16 endpoint directly:

```typescript
// Replace the analytics export call with direct Form 16 generation
const response = await payrollApi.generateForm16({ financialYear: selectedFY });
showSuccess('Form 16 generated successfully');
```

- [ ] **Step 2: Commit**

```bash
cd /Users/chetan/Documents/Avyren-Technologies/Products/Mobile-ERP/web-system-app
git add src/features/company-admin/hr/analytics/
git commit -m "fix(web): fix Form 16 report button to use correct endpoint"
```

---

## Task 5: Type Check & Lint

- [ ] **Step 1: Backend**
```bash
cd avy-erp-backend && pnpm build
```

- [ ] **Step 2: Web**
```bash
cd web-system-app && pnpm build
```

- [ ] **Step 3: Fix any errors and commit**
