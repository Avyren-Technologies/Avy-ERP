# Billing, Invoicing & Subscription Management — Design Spec

**Date:** 2026-03-19
**Status:** Approved (reviewer issues resolved)
**Scope:** Backend + Mobile App + Web App

---

## Overview

Extend the existing billing system to support three billing types (Monthly, Annual, One-Time+AMC), full invoice management with Indian GST compliance, subscription lifecycle management, and payment history tracking.

## Business Rules

### Billing Types
1. **Monthly** — Recurring monthly subscription per location
2. **Annual** — Pay 10 months, get 12 months access per location (16.67% discount)
3. **One-Time + AMC** — Perpetual license fee + Annual Maintenance Contract

### One-Time + AMC Rules
- One-time license fee = monthly cost × configurable multiplier (default 24x)
- AMC is **required** when `endpointType === 'default'` (platform-hosted)
- AMC is **not required** when `endpointType === 'custom'` (self-hosted)
- AMC amount = one-time fee × configurable percentage (default 18%)
- AMC non-payment on default endpoint → tenant set to **Inactive**
- Both multiplier and AMC% are configurable at: platform level → tenant level → location level (cascading override)

### GST Rules
- Platform company has registered GSTIN (state code from first 2 digits)
- Each tenant location has GSTIN
- Same state → CGST (9%) + SGST (9%)
- Different state → IGST (18%)
- Tax rates configurable in platform settings
- **Constraint:** `igstRate` must always equal `cgstRate + sgstRate` (validated on save)
- **Null GSTIN handling:** If platform GSTIN or location GSTIN is missing, GST is set to 0 for all fields and a warning flag `gstNotApplicable: true` is included on the invoice. Invoice generation still proceeds (some tenants may not have GSTIN during trial/setup).

### Pricing Hierarchy (cascade)
```
Platform defaults → Tenant-level overrides → Location-level overrides
```

### Zero-Cost Guard
If `calculateLocationMonthlyCost()` returns 0 (no modules or custom tier with no price set), the system:
- Allows it for TRIAL status subscriptions (₹0 invoices acceptable during trial)
- Shows a warning in the UI for non-trial: "Monthly cost is ₹0 — please set module prices or custom tier pricing"
- Does NOT block invoice generation (the super admin may intentionally set ₹0 for pilot tenants)

---

## Data Model Changes

### Migration Strategy

**Rename `BillingCycle` to `BillingType`:**
1. The existing `BillingCycle` enum (`MONTHLY | ANNUAL`) on the `Subscription` model is replaced by a new `BillingType` enum (`MONTHLY | ANNUAL | ONE_TIME_AMC`)
2. Prisma migration: Add `billingType` column with default `MONTHLY`, backfill from existing `billingCycle` values, then drop `billingCycle` from `Subscription`
3. On `Company` and `Location` models, the existing `billingCycle String?` field is renamed to `billingType String?` with value migration: `'monthly'` stays `'monthly'`, `'annual'` stays `'annual'`
4. The `BillingCycle` enum is dropped after migration
5. Existing `Invoice` records: backfill `invoiceNumber` (generate sequential), set `invoiceType = 'SUBSCRIPTION'`, set `subtotal = amount`, `totalTax = 0`, `totalAmount = amount`, `lineItems = []`

**Subscription model — one per tenant (unchanged):**
The existing `tenantId @unique` constraint is kept. A single `Subscription` record represents the tenant's overall billing state. Per-location cost breakdowns are computed from `Location` records at query time, not stored as separate subscriptions. The subscription `billingType` represents the default for new locations; individual locations can override via their own `billingType` field.

### New Enums

```prisma
enum BillingType {
  MONTHLY
  ANNUAL
  ONE_TIME_AMC
}

enum InvoiceType {
  SUBSCRIPTION
  ONE_TIME_LICENSE
  AMC
  PRORATED_ADJUSTMENT
}

enum AmcStatus {
  ACTIVE
  OVERDUE
  LAPSED
  NOT_APPLICABLE
}

enum PaymentMethod {
  BANK_TRANSFER
  CHEQUE
  CASH
  RAZORPAY
  UPI
  OTHER
}
```

### Subscription Model — Modified Fields
- Replace `billingCycle` with `billingType` BillingType (default: MONTHLY)
- Add `oneTimeLicenseFee` Float? (total one-time amount, aggregated)
- Add `amcAmount` Float? (annual AMC fee, aggregated)
- Add `amcDueDate` DateTime? (next AMC due date)
- Add `amcStatus` AmcStatus (default: NOT_APPLICABLE)

### Invoice Model — Add Fields
- `invoiceNumber` String @unique (auto-generated: INV-{YYYY}-{0001})
- `invoiceType` InvoiceType (default: SUBSCRIPTION)
- `lineItems` Json (array of LineItem objects)
- `subtotal` Float
- `cgst` Float (default: 0)
- `sgst` Float (default: 0)
- `igst` Float (default: 0)
- `totalTax` Float
- `totalAmount` Float (this replaces the semantic meaning of the old `amount` field)
- `billingPeriodStart` DateTime?
- `billingPeriodEnd` DateTime?
- `paidVia` PaymentMethod? (enum, not string)
- `paymentReference` String?
- `sentAt` DateTime? (email sent timestamp)
- `pdfUrl` String?
- Add relation: `payments Payment[]`

### LineItem JSON Structure
```typescript
{
  description: string;
  moduleId?: string;
  locationId?: string;
  locationName?: string;
  quantity: number;
  unitPrice: number;
  amount: number;
  hsnCode?: string;
}
```

### New Model: Payment
```prisma
model Payment {
  id                   String        @id @default(cuid())
  invoiceId            String
  invoice              Invoice       @relation(fields: [invoiceId], references: [id])
  amount               Float
  method               PaymentMethod
  transactionReference String?
  paidAt               DateTime
  recordedBy           String        // userId who recorded
  notes                String?
  createdAt            DateTime      @default(now())
  @@map("payments")
}
```

### New Model: PlatformBillingConfig
```prisma
model PlatformBillingConfig {
  id                      String   @id @default(cuid())
  defaultOneTimeMultiplier Float   @default(24)
  defaultAmcPercentage     Float   @default(18)
  defaultCgstRate          Float   @default(9)
  defaultSgstRate          Float   @default(9)
  defaultIgstRate          Float   @default(18)
  platformGstin            String?
  invoicePrefix            String  @default("INV")
  nextInvoiceSeq           Int     @default(1)
  updatedAt                DateTime @updatedAt
  @@map("platform_billing_config")
}
```

**Validation on save:** `defaultIgstRate` must equal `defaultCgstRate + defaultSgstRate`.

### Company Model — Add Fields
- `oneTimeMultiplier` Float? (overrides platform default)
- `amcPercentage` Float? (overrides platform default)

### Location Model — Modify/Add Fields
- Rename `billingCycle` to `billingType` String? ('monthly' | 'annual' | 'one_time_amc')
- Add `oneTimeLicenseFee` Float? (calculated or manual override)
- Add `amcAmount` Float? (calculated or manual override)

### Frontend Type Change
- `LocationCommercialEntry.billingCycle` renamed to `billingType` with values: `'monthly' | 'annual' | 'one_time_amc'`
- Both mobile and web `types.ts` and `constants.ts` updated

---

## Backend API Endpoints

### Subscription Management (`/platform/billing/subscriptions`)

| Method | Path | Description |
|--------|------|-------------|
| GET | `/:companyId` | Full subscription detail with per-location breakdown (companyId used in API, internally resolves to tenant) |
| GET | `/:companyId/cost-preview` | Calculate cost preview without saving (query: `billingType, locationId`) |
| PATCH | `/:companyId/billing-type` | Change billing type with cost recalculation |
| PATCH | `/:companyId/tier` | Upgrade/downgrade tier with prorated cost |
| PATCH | `/:companyId/trial` | Extend trial period |
| POST | `/:companyId/cancel` | Cancel → CANCELLED status, 30-day export window |
| POST | `/:companyId/reactivate` | Reactivate suspended/expired → ACTIVE |

**Note:** `companyId` in the URL is the external identifier. Internally, the service resolves `company → tenant → subscription` via the existing relations.

### Invoice Management (`/platform/billing/invoices`)

| Method | Path | Description |
|--------|------|-------------|
| GET | `/` | Paginated list with filters (status, invoiceType, companyId, dateFrom, dateTo, search) |
| GET | `/:id` | Invoice detail with line items + GST breakdown + payments |
| POST | `/generate` | Generate invoice (body below) |
| PATCH | `/:id/mark-paid` | Mark paid with payment details |
| PATCH | `/:id/void` | Void/cancel an unpaid invoice → status CANCELLED |
| POST | `/:id/send-email` | Send invoice via email |
| GET | `/:id/pdf` | Download invoice as PDF |

**Generate Invoice Request Body:**
```typescript
{
  companyId: string;
  locationId?: string;        // specific location, or all if omitted
  invoiceType: InvoiceType;   // SUBSCRIPTION, ONE_TIME_LICENSE, AMC
  billingPeriodStart?: string; // ISO date
  billingPeriodEnd?: string;   // ISO date
  customLineItems?: LineItem[]; // optional overrides; if omitted, auto-calculated
  notes?: string;
}
```

### Payment History (`/platform/billing/payments`)

| Method | Path | Description |
|--------|------|-------------|
| GET | `/` | Paginated list with filters (companyId, invoiceId, dateFrom, dateTo, method) |
| GET | `/:id` | Payment detail |
| POST | `/record` | Record manual payment (body: `{ invoiceId, amount, method, transactionReference, paidAt, notes }`) |

### Platform Billing Config (`/platform/billing/config`)

| Method | Path | Description |
|--------|------|-------------|
| GET | `/defaults` | Get platform billing defaults |
| PATCH | `/defaults` | Update defaults (with IGST = CGST+SGST validation) |

---

## Pricing Calculation Service

### calculateLocationMonthlyCost(location, company)
```
moduleIds = location.moduleIds ?? company.selectedModuleIds ?? []
customPricing = location.customModulePricing ?? company.customModulePricing ?? {}

moduleCost = moduleIds.reduce((sum, id) => {
  price = customPricing[id] ?? MODULE_CATALOGUE.find(m => m.id === id)?.price ?? 0
  return sum + price
}, 0)

tier = USER_TIERS.find(t => t.key === location.userTier)
tierCost = (location.userTier === 'custom')
  ? parseFloat(location.customTierPrice || '0')
  : (tier?.basePrice ?? 0)

return moduleCost + tierCost
```

### calculateAnnualCost(location, company)
```
monthly = calculateLocationMonthlyCost(location, company)
return monthly × 10  // pay 10 months, get 12 months (16.67% discount)
```

### calculateOneTimeFee(location, company, platformConfig)
```
monthly = calculateLocationMonthlyCost(location, company)
multiplier = company.oneTimeMultiplier ?? platformConfig.defaultOneTimeMultiplier
return location.oneTimeLicenseFee ?? (monthly × multiplier)
```

### calculateAmcFee(location, company, platformConfig)
```
oneTimeFee = calculateOneTimeFee(location, company, platformConfig)
amcPercent = company.amcPercentage ?? platformConfig.defaultAmcPercentage
return location.amcAmount ?? (oneTimeFee × (amcPercent / 100))
```

### calculateGST(platformGstin, locationGstin, amount, platformConfig)
```
if (!platformGstin || !locationGstin):
  return { cgst: 0, sgst: 0, igst: 0, totalTax: 0, gstNotApplicable: true }

platformState = platformGstin.substring(0, 2)
locationState = locationGstin.substring(0, 2)

if (platformState === locationState):
  cgst = round(amount × (platformConfig.defaultCgstRate / 100), 2)
  sgst = round(amount × (platformConfig.defaultSgstRate / 100), 2)
  igst = 0
else:
  cgst = 0
  sgst = 0
  igst = round(amount × (platformConfig.defaultIgstRate / 100), 2)

return { cgst, sgst, igst, totalTax: cgst + sgst + igst, gstNotApplicable: false }
```

### Invoice Number Generation
```
prefix = platformConfig.invoicePrefix  // "INV"
year = currentFiscalYear               // "2026"
seq = platformConfig.nextInvoiceSeq    // auto-increment atomically
format: "{prefix}-{year}-{seq padded to 4 digits}"
example: "INV-2026-0001"
// After generation: UPDATE platformBillingConfig SET nextInvoiceSeq = nextInvoiceSeq + 1
```

---

## Scheduled Jobs (Background Workers)

### Recurring Invoice Generation (Monthly)
- **Schedule:** 1st of every month at 00:00 UTC
- **Logic:** For each active subscription with `billingType = MONTHLY`:
  - For each location: generate SUBSCRIPTION invoice with line items (modules + tier)
  - Calculate GST per location
  - Set `dueDate = billingPeriodEnd + 15 days`
  - Set invoice `status = PENDING`

### Recurring Invoice Generation (Annual)
- **Schedule:** Daily at 01:00 UTC
- **Logic:** Check subscriptions where `billingType = ANNUAL` and `endDate` is within 30 days
  - Generate renewal invoice
  - Send email notification about upcoming renewal

### AMC Due Date Check
- **Schedule:** Daily at 02:00 UTC
- **Logic:** For each subscription with `amcStatus = ACTIVE`:
  - If `amcDueDate` < today: set `amcStatus = OVERDUE`
  - If `amcDueDate` < today - 30 days AND `endpointType = 'default'`: set `amcStatus = LAPSED`, set tenant status to `INACTIVE`
  - Send notification emails at: 30 days before due, 15 days before, 7 days before, on due date, 7 days after (overdue warning)

**Note:** These cron jobs use the existing Bull queue + worker infrastructure in `src/workers/`. For this sprint, the cron configuration is created but the actual scheduling can be enabled once the core CRUD is working. The manual invoice generation covers the immediate need.

---

## Frontend Screens

### Onboarding Wizard Changes (Step 10 — Per-Location Tier & Pricing)

**Add to existing step:**
- Billing type selector: Monthly | Annual | One-Time + AMC (radio cards, replacing the existing monthly/annual toggle)
- When One-Time+AMC selected:
  - Show calculated one-time fee (monthly × multiplier)
  - "Override" toggle → manual one-time fee input
  - If endpoint is default: show AMC amount (one-time × AMC%)
  - "Override AMC" toggle → manual AMC fee input
  - If endpoint is custom: show "AMC not required (self-hosted)" info badge
- Pricing summary updates dynamically based on billing type
- Annual shows: "Pay ₹X (10 months) for 12 months access — save 16.67%"

### Invoice Management Screen (NEW — both platforms)

**Route:** `/(app)/billing/invoices` (mobile), `/app/billing/invoices` (web)

**Features:**
- Invoice list with columns: Invoice #, Tenant, Type badge, Amount, Due Date, Status badge
- Filter chips: All, Paid, Pending, Overdue, Draft
- Filter by invoice type: All, Subscription, One-Time License, AMC
- Search by invoice number or tenant name
- FAB/button → Generate Invoice flow (see below)
- Pagination
- Skeleton loading, EmptyState for no results

**Generate Invoice Flow:**
1. Select company (searchable dropdown)
2. Select location (dropdown, or "All Locations")
3. Select invoice type (Subscription / One-Time License / AMC)
4. System auto-calculates line items, subtotal, GST, total
5. Preview step showing full invoice breakdown
6. Confirm → generates invoice, navigates to detail

### Invoice Detail Screen (NEW — both platforms)

**Route:** `/(app)/billing/invoices/[id]` (mobile), `/app/billing/invoices/:id` (web)

**Sections:**
- Header: Invoice #, tenant name, billing period, status badge
- Line items table: description, location, quantity, unit price, amount
- Tax breakdown card: Subtotal, CGST, SGST, IGST, Total Tax, Grand Total
- Actions bar: Mark as Paid, Send Email, Download PDF, Void (if unpaid)
- Payment history for this invoice (if any payments recorded)
- Mark as Paid → modal with: method selector (dropdown of PaymentMethod values), transaction reference, date picker, notes

### Subscription Detail Screen (NEW — both platforms)

**Route:** `/(app)/billing/subscriptions/[companyId]` (mobile), `/app/billing/subscriptions/:companyId` (web)

**Access:** Navigate from Company Detail billing tab or Billing Overview tenant cards.

**Sections:**
- Header: Tenant name, overall status badge, default billing type badge
- Per-location breakdown cards:
  - Location name, billing type badge, tier badge, modules count
  - Cost display based on billing type (Monthly cost / Annual cost / One-Time + AMC)
  - AMC amount + AMC status badge (if applicable, only for default endpoint)
  - Next renewal/AMC due date
- Actions: Change Billing Type, Upgrade/Downgrade Tier, Extend Trial, Cancel, Reactivate
- Each action opens a modal with cost preview before confirming

### Payment History Screen (NEW — both platforms)

**Route:** `/(app)/billing/payments` (mobile), `/app/billing/payments` (web)

**Features:**
- Payment list: Date, Invoice #, Tenant, Amount, Method badge, Reference
- Filters: tenant (searchable), date range, payment method
- Record Manual Payment button → modal with invoice selector (searchable), amount, method, reference, date, notes
- Skeleton loading, EmptyState

### Billing Overview Enhancement

**Add to existing screen:**
- "View All Invoices" → navigate to invoice list
- "View Subscriptions" link on tenant health cards
- New KPI: One-Time Revenue (total one-time license fees collected)

### Sidebar Updates
- Billing section becomes expandable with sub-items:
  - Overview (`/billing`)
  - Invoices (`/billing/invoices`)
  - Payments (`/billing/payments`)

### Mobile Routing Migration
The existing `app/(app)/billing.tsx` (flat file) must be migrated to:
- `app/(app)/billing/_layout.tsx` (Stack navigator)
- `app/(app)/billing/index.tsx` (re-exports BillingOverviewScreen)
- `app/(app)/billing/invoices.tsx`
- `app/(app)/billing/invoices/[id].tsx`
- `app/(app)/billing/subscriptions/[companyId].tsx`
- `app/(app)/billing/payments.tsx`

---

## Backend Service Architecture

### New Files
```
core/billing/
├── billing.service.ts          (enhance existing — add one-time revenue KPI)
├── billing.controller.ts       (enhance existing)
├── billing.routes.ts           (enhance existing — register sub-routers)
├── pricing.service.ts          (NEW — all calculation logic)
├── invoice.service.ts          (NEW — invoice CRUD + generation + PDF)
├── invoice.controller.ts       (NEW)
├── invoice.routes.ts           (NEW)
├── subscription.service.ts     (NEW — subscription lifecycle)
├── subscription.controller.ts  (NEW)
├── subscription.routes.ts      (NEW)
├── payment.service.ts          (NEW — payment recording + history)
├── payment.controller.ts       (NEW)
├── payment.routes.ts           (NEW)
├── pdf.service.ts              (NEW — invoice PDF generation using pdfkit or similar)
├── billing-config.service.ts   (NEW — platform billing config CRUD)
├── billing-config.controller.ts(NEW)
├── billing-config.routes.ts    (NEW)
└── __tests__/
    ├── pricing.service.test.ts
    ├── invoice.service.test.ts
    ├── subscription.service.test.ts
    └── payment.service.test.ts
```

### Frontend New Files (per platform)
```
Mobile:
  lib/api/invoice.ts
  lib/api/subscription.ts
  lib/api/payment.ts
  features/super-admin/api/use-invoice-queries.ts
  features/super-admin/api/use-subscription-queries.ts
  features/super-admin/api/use-payment-queries.ts
  features/super-admin/invoice-list-screen.tsx
  features/super-admin/invoice-detail-screen.tsx
  features/super-admin/subscription-detail-screen.tsx
  features/super-admin/payment-history-screen.tsx
  app/(app)/billing/_layout.tsx
  app/(app)/billing/index.tsx
  app/(app)/billing/invoices.tsx
  app/(app)/billing/invoices/[id].tsx
  app/(app)/billing/subscriptions/[companyId].tsx
  app/(app)/billing/payments.tsx

Web:
  lib/api/invoice.ts
  lib/api/subscription.ts
  lib/api/payment.ts
  features/super-admin/api/use-invoice-queries.ts
  features/super-admin/api/use-subscription-queries.ts
  features/super-admin/api/use-payment-queries.ts
  features/super-admin/InvoiceListScreen.tsx
  features/super-admin/InvoiceDetailScreen.tsx
  features/super-admin/SubscriptionDetailScreen.tsx
  features/super-admin/PaymentHistoryScreen.tsx
```

---

## Email & PDF (Deferred Details)

### Invoice Email
- Uses existing Nodemailer infrastructure (`src/infrastructure/email/`)
- Template: HTML email with invoice summary (number, amount, due date, line items, GST)
- Attaches PDF if generated
- Sends to all company contacts with `designation` containing "finance" or "billing", or primary contact

### Invoice PDF
- Library: `pdfkit` (lightweight, no external dependencies)
- Template: Company letterhead area (Avyren branding), invoice details, line items table, GST breakdown, payment instructions, footer with terms
- Stored at: `/uploads/invoices/{invoiceNumber}.pdf` (or cloud storage if configured)
- Accessible via `GET /platform/billing/invoices/:id/pdf`
