# Avy ERP — Master Product Requirements Document
## Part 4: Module Specifications — Sales & Invoicing, Inventory, Vendor Management & Finance

> **Product:** Avy ERP
> **Company:** Avyren Technologies
> **Document Series:** PRD-004 of 5
> **Version:** 2.0
> **Date:** April 2026
> **Status:** Final Draft · Confidential
> **Scope:** Full module definitions for Sales & Invoicing, Inventory Management, Vendor Management & Procurement, and Finance & Accounting

---

## Table of Contents

1. [Module 1 — Sales & Invoicing](#1-module-1--sales--invoicing)
   - 1.1 [Module Overview](#11-module-overview)
   - 1.2 [Customer Master](#12-customer-master)
   - 1.3 [Inward Purchase Orders (Customer PO)](#13-inward-purchase-orders-customer-po)
   - 1.4 [Quotation Management](#14-quotation-management)
   - 1.5 [Invoice Creation & Management](#15-invoice-creation--management)
   - 1.6 [GST Tax Engine](#16-gst-tax-engine)
   - 1.7 [Payment-In Recording](#17-payment-in-recording)
   - 1.8 [Customer Ledger & Receivables](#18-customer-ledger--receivables)
   - 1.9 [Sales Dashboard & Reports](#19-sales-dashboard--reports)
   - 1.10 [CRM Integration](#110-crm-integration)
2. [Module 2 — Inventory Management](#2-module-2--inventory-management)
   - 2.1 [Module Overview](#21-module-overview)
   - 2.2 [Item Master](#22-item-master)
   - 2.3 [Warehouse & Location Configuration](#23-warehouse--location-configuration)
   - 2.4 [Goods Receipt Note (GRN)](#24-goods-receipt-note-grn)
   - 2.5 [Stock Management](#25-stock-management)
   - 2.6 [Material Request & Approval](#26-material-request--approval)
   - 2.7 [Material Issue](#27-material-issue)
   - 2.8 [Stock Adjustments & Physical Count](#28-stock-adjustments--physical-count)
   - 2.9 [Inventory Reports](#29-inventory-reports)
3. [Module 4 — Vendor Management & Procurement](#3-module-4--vendor-management--procurement)
   - 3.1 [Module Overview](#31-module-overview)
   - 3.2 [Vendor Master](#32-vendor-master)
   - 3.3 [Purchase Order Management](#33-purchase-order-management)
   - 3.4 [Advance Shipping Notice (ASN)](#34-advance-shipping-notice-asn)
   - 3.5 [Goods Receipt & GRN Completion](#35-goods-receipt--grn-completion)
   - 3.6 [Vendor Performance Management](#36-vendor-performance-management)
   - 3.7 [Procurement Reports](#37-procurement-reports)
4. [Module 5 — Finance & Accounting](#4-module-5--finance--accounting)
   - 4.1 [Module Overview](#41-module-overview)
   - 4.2 [Chart of Accounts](#42-chart-of-accounts)
   - 4.3 [Accounts Receivable](#43-accounts-receivable)
   - 4.4 [Accounts Payable](#44-accounts-payable)
   - 4.5 [Payment Recording](#45-payment-recording)
   - 4.6 [Journal Entries & GL](#46-journal-entries--gl)
   - 4.7 [Bank Reconciliation](#47-bank-reconciliation)
   - 4.8 [Financial Statements](#48-financial-statements)
   - 4.9 [GST Returns Support](#49-gst-returns-support)
   - 4.10 [Finance Reports & Export](#410-finance-reports--export)
5. [Module 10 — Masters](#5-module-10--masters)
   - 5.1 [Item Master (Shared)](#51-item-master-shared)
   - 5.2 [Machine Master (Shared)](#52-machine-master-shared)
   - 5.3 [Operation Master](#53-operation-master)
   - 5.4 [Part / Finished Goods Master](#54-part--finished-goods-master)
   - 5.5 [Shift Master (Shared)](#55-shift-master-shared)
   - 5.6 [UOM Master](#56-uom-master)

---

## 1. Module 1 — Sales & Invoicing

### 1.1 Module Overview

The Sales & Invoicing module manages the complete **quote-to-cash lifecycle** for a manufacturing enterprise. It handles customer relationships, inbound customer POs, quotation creation, GST-compliant invoice generation, payment recording, and the customer ledger.

The module is tightly integrated with the Finance module (invoices create receivable entries automatically), the Inventory module (finished goods dispatched from inventory on invoice confirmation), and the Masters module (Item Master drives invoice line items).

**Key Capabilities:**
- GST-compliant invoicing with automatic CGST/SGST vs IGST determination
- PO-referenced and general invoice modes
- Partial payment support with running balance tracking
- Visual sales pipeline and revenue dashboards
- Proforma Invoice generation for advance payments

### 1.2 Customer Master

Every customer (buyer) in the system is registered in the Customer Master before any transaction can be created for them.

**Customer Master Fields:**

| Field | Notes |
|---|---|
| Customer Name | Display name as shown on invoices |
| Customer Code | Auto-generated or manual unique identifier |
| Legal Name | Name as per GST registration |
| GSTIN | Customer's GST number; used for tax determination |
| State | Customer's state; determines CGST/SGST vs IGST |
| PAN | For TDS-applicable transactions |
| Billing Address | Address printed on invoices |
| Shipping Addresses | Multiple shipping addresses supported |
| Contact Person(s) | Name, designation, phone, email |
| Payment Terms | Standard credit period (e.g., Net 30, Net 45, Cash on Delivery) |
| Credit Limit | Maximum outstanding balance allowed; system warns when limit is approached |
| Currency | Default transaction currency (INR for most; configurable) |
| Customer Category | Domestic / Export / SEZ |
| Bank Details | For NEFT/RTGS payment inflow reconciliation |

### 1.3 Inward Purchase Orders (Customer PO)

When a customer places a Purchase Order on the company, it is registered as an Inward PO:

- **PO Number** (customer's reference), date, customer, items, quantities, unit rates, delivery schedule
- Inward POs are the authorisation baseline for creating sales invoices; invoices can be created directly against a PO reference
- Outstanding quantity tracking: system shows how much of each PO line has been invoiced
- Partial fulfilment: a single PO can be fulfilled across multiple invoices (shipments)
- PO expiry: system flags POs past their validity date

### 1.4 Quotation Management

**Quote Creation:**
Quotations are prepared against a potential customer. Line items reference the Item Master (products, services, or custom line entries).

**Quote Fields:**
- Quote number (from No Series), date, validity date
- Customer reference
- Line items: Item (from master), description, quantity, unit, rate, discount, tax
- Terms and conditions (configurable templates)
- Optional: linked to a CRM opportunity

**Quote States:** Draft → Sent → Accepted → Rejected → Converted to Invoice

**Quote-to-Invoice Conversion:**
An accepted quotation is converted to a sales invoice with a single action. All line items, pricing, and customer details carry forward. The quote is linked to the invoice for traceability.

### 1.5 Invoice Creation & Management

**Invoice Modes:**

| Mode | Use Case |
|---|---|
| **PO-Referenced Invoice** | Invoice created against a customer's registered Inward PO; quantities validated against PO balance |
| **General Invoice** | Invoice without a pre-registered PO; used for ad-hoc or service billing |
| **Proforma Invoice** | Non-accounting document for advance payment requests; converted to a tax invoice on payment |
| **Credit Note** | Issued to reverse a posted invoice (full or partial); reduces the customer's outstanding balance |
| **Debit Note** | Issued to add additional charges to a posted invoice |

**Invoice Fields:**

| Field | Notes |
|---|---|
| Invoice Number | Auto-generated from No Series |
| Invoice Date | Tax point date for GST |
| Place of Supply | State of supply; drives CGST/SGST vs IGST determination |
| Customer reference | |
| Billing and Shipping address | |
| Line Items | Item, description, HSN/SAC code, quantity, unit, rate, discount, taxable value, tax components |
| Transport Details | Vehicle number, LR number, transporter name (for e-way bill requirements) |
| Payment Terms | Due date calculated from terms |
| Notes / Narration | Free-text internal and external notes |
| Attachments | Supporting documents |

**Invoice States:** Draft → Confirmed → Partially Paid → Fully Paid → Cancelled

Once confirmed, an invoice creates a receivable entry in the Finance module automatically.

### 1.6 GST Tax Engine

The GST tax engine is built natively into Avy ERP and handles the complex Indian GST determination rules automatically.

**Tax Determination Logic:**

| Scenario | Tax Applied |
|---|---|
| Supplier state = Customer state (Intra-state) | CGST + SGST (equal split of total GST rate) |
| Supplier state ≠ Customer state (Inter-state) | IGST (full rate) |
| SEZ / Export supply | Zero-rated (0% GST; letter of undertaking required) |

**HSN / SAC Code Integration:**
Each item in the Item Master carries an HSN code (Harmonised System of Nomenclature for goods) or SAC code (Service Accounting Code). The applicable GST rate is mapped to the HSN/SAC code and applied automatically when the item is added to an invoice.

**Tax Components on Invoice:**
The invoice shows a clean breakdown of taxable value, CGST amount, SGST amount (or IGST amount), and the total invoice value. This breakdown is mandatory for valid tax invoice format under Indian GST law.

**E-Way Bill:** For consignments above ₹50,000 in value, Avy ERP generates the data required for e-Way Bill generation. Direct API integration with the GSTN e-Way Bill portal is planned.

### 1.7 Payment-In Recording

When a customer makes a payment (full or partial) against an outstanding invoice:

- **Payment Mode:** NEFT, RTGS, Cheque, Cash, UPI, Card
- **Reference Number:** Bank reference or cheque number
- **Amount:** Can be less than the invoice total (partial payment)
- **Allocation:** The payment is allocated against one or more invoices; any unallocated amount is held as an advance credit

**Partial Payment Tracking:**
The system maintains a running balance for each invoice: Invoiced Amount, Total Paid, Outstanding Balance, Last Payment Date. This is visible on the invoice detail screen and the customer ledger.

### 1.8 Customer Ledger & Receivables

**Customer Ledger:**
A chronological statement of all transactions for a customer: invoices raised, credit notes, payments received, advances applied. Shows opening balance, transaction rows, and closing balance.

**Receivables Ageing:**
The receivables list shows all outstanding invoices grouped by ageing bucket: Current (within payment terms), Due Soon (within 7 days of due date), Overdue 1–30 days, Overdue 31–60 days, Overdue 60+ days.

**Reminder Actions:**
For overdue invoices, the system supports:
- One-click email reminder to customer (from a configurable template)
- Manual flag for "In Follow-Up"
- Escalation to legal/collections flag

### 1.9 Sales Dashboard & Reports

**Sales Dashboard KPIs:**
- Total Revenue (current month vs prior month)
- Invoice Count (current month)
- Outstanding Receivables (total and by ageing bucket)
- Top 5 Customers by Revenue
- Revenue Trend Chart (last 12 months)
- Pending Quotations (to be followed up)

**Sales Reports:**
- Sales Register: All invoices in a date range with GST break-up
- Customer-wise Sales: Revenue and outstanding per customer
- Product-wise Sales: Revenue by item/SKU
- Receivables Ageing Report
- Payment Receipt Register
- GST Output Report (GSTR-1 supporting data)

### 1.10 CRM Integration

When the CRM module is active, the Sales & Invoicing module integrates with the sales pipeline:
- A won opportunity in CRM auto-creates a Customer record if not already present
- The quotation in Sales & Invoicing can be linked to a CRM opportunity
- Invoice creation can be triggered from a CRM deal on closure

---

## 2. Module 2 — Inventory Management

### 2.1 Module Overview

The Inventory module tracks all physical stock — raw materials, work-in-progress (WIP), spare parts, and finished goods — across multiple warehouses and storage locations. It manages the complete inward and outward stock movement cycle.

The module integrates with Vendor Management (GRN from PO/ASN updates stock), Production (raw material issues to production; finished goods receipt from production), Sales & Invoicing (finished goods dispatched on invoice), and Machine Maintenance (spare parts consumed from inventory).

### 2.2 Item Master

The Item Master is the central registry of every product, material, and service traded or used by the company. It is shared across all modules that reference items.

**Item Master Fields:**

| Field | Notes |
|---|---|
| Item Code | Unique identifier (auto-generated or manual) |
| Item Name / Description | Display name |
| Item Type | Raw Material / Finished Good / WIP / Spare Part / Service / Consumable |
| Unit of Measure (UOM) | Primary UOM (e.g., KG, PCS, LTR, MTR) |
| Alternate UOMs | With conversion factors (e.g., 1 box = 12 PCS) |
| HSN Code | For GST compliance |
| GST Rate | Auto-applied on invoice/PO line items |
| Reorder Point | Stock level below which a reorder alert is triggered |
| Reorder Quantity | Suggested replenishment quantity |
| Standard Cost / Standard Price | For valuation |
| Shelf Life / Expiry Tracking | For perishable or pharma items |
| Serial / Lot Number Tracking | For items requiring individual serialization or batch traceability |
| Status | Active / Inactive |

### 2.3 Warehouse & Location Configuration

**Warehouse Master:**
A warehouse is a physical storage facility. Each warehouse has a name, code, address, and assigned custodian. Multiple warehouses are supported per company.

**Bin / Location:**
Within a warehouse, storage bins or aisles can be defined for precise stock location tracking (row, shelf, bin code). Bin-level tracking is optional and configured per warehouse.

**Default Bins per Item:**
An item can be assigned a default bin within each warehouse to guide putaway operations.

### 2.4 Goods Receipt Note (GRN)

A GRN records the physical receipt of goods into the warehouse. It is the document that updates inventory levels.

**GRN Creation Sources:**

| Source | Triggered By |
|---|---|
| Against ASN | Vendor Management: after security gate verification of an ASN |
| Against PO | Direct GRN against a Purchase Order (when no ASN was created) |
| Manual / Without Reference | For ad-hoc receipts (samples, returns, internal transfers) |
| From Production | Finished goods produced and received into the FG warehouse |

**GRN Fields:**
- GRN Number (from No Series), date
- Source PO / ASN reference
- Vendor / supplier
- Line items: expected qty, received qty, accepted qty, rejected qty
- Condition of goods: Good / Damaged / Short / Excess
- Storage location (warehouse, bin)
- Quality inspection link (if Quality module is active — GRN triggers incoming inspection)
- Received by (store employee)

**GRN Discrepancy Handling:**
If the received quantity differs from the expected quantity, the GRN records the discrepancy. Short receipts leave the PO/ASN balance open for the remaining quantity. Excess receipts require manager approval to accept the surplus.

### 2.5 Stock Management

**Stock Ledger:**
A real-time ledger showing every inward and outward movement of each item with timestamps, document references, quantities, and running balance.

**Current Stock View:**
A snapshot of current stock levels by item and warehouse. Each item shows:
- Current quantity
- Reserved quantity (committed to a material request or production order)
- Available quantity (current minus reserved)
- Stock status badge: **Normal** / **Low** (below reorder point) / **Critical** (below minimum safety stock)

**Low Stock Alerts:**
When any item crosses its reorder point, an alert is automatically generated and sent to the designated stores manager and optionally triggers a draft Purchase Requisition in the Vendor Management module.

**Stock Valuation Methods:**
- FIFO (First In First Out) — default
- Weighted Average Cost
- Standard Cost (manufacturing use case)

**Multi-Warehouse View:**
Stock can be viewed aggregated (all warehouses combined) or per-warehouse. Transfers between warehouses are recorded as paired outward and inward movements.

### 2.6 Material Request & Approval

**Material Request (MR):**
Any department or production line can raise a Material Request for items they need from the store.

**MR Fields:**
- Requesting department / plant
- Required date
- Line items: Item, required quantity, purpose / work order reference
- Priority: Normal / Urgent

**Approval Workflow:**
1. MR submitted by requester
2. Routed to the departmental approver (configurable, typically department head)
3. Approved MR moves to "Ready for Issue" status
4. Stores staff sees all approved, pending MRs in the issue queue

**Insufficient Stock Handling:**
If an approved MR cannot be fulfilled due to insufficient stock, it is placed in a "Pending Stock" status and linked to a draft PO for the shortage items. The requester is notified.

### 2.7 Material Issue

**Material Issue:**
The physical handover of items from the store to the requesting department. Issued against an approved Material Request.

**Issue Fields:**
- Issue Number (from No Series), date
- Reference MR
- Issued items: Item, issued quantity (may be partial), lot/serial numbers if tracked
- Issued by (stores staff), received by (department representative)

**Post-Issue:**
- Stock ledger is updated (issued quantity deducted)
- MR is marked as fulfilled (or partially fulfilled if issued quantity < requested quantity)
- If production integration is active, the issued materials are linked to the production order they feed

### 2.8 Stock Adjustments & Physical Count

**Stock Adjustment:**
Allows stores managers to correct stock levels for reasons such as: damaged goods writeoff, excess found during counting, item classification correction.

Every adjustment records: reason, authorised by, quantity change (positive or negative).

**Physical Stock Count:**
A structured process for verifying physical inventory against system records.

1. A physical count sheet is generated listing all items in selected warehouses
2. Count team records actual physical quantities on the sheet (or directly in the mobile app)
3. System compares recorded vs expected quantities; shows variance per item
4. Discrepancies above a configurable threshold require manager approval to post
5. On posting, stock levels are adjusted to match physical count; variance report is saved

### 2.9 Inventory Reports

| Report | Description |
|---|---|
| Current Stock Report | Snapshot of all item quantities by warehouse |
| Stock Ledger Report | All movements for selected items and date range |
| Low Stock Report | Items below reorder point with suggested PO quantities |
| GRN Report | All goods received in a date range |
| Material Issue Report | All issues by department and item |
| Inventory Valuation Report | Total inventory value by valuation method |
| Slow-Moving / Non-Moving Report | Items with no movement in a configurable period |
| Physical Count Variance Report | Differences between physical count and system records |

---

## 3. Module 4 — Vendor Management & Procurement

### 3.1 Module Overview

The Vendor Management module covers the full procurement lifecycle: from vendor qualification and directory management through purchase orders, advance shipping notices, goods receipt, and vendor performance tracking.

It is tightly integrated with Inventory (GRN updates stock), Finance (PO creates a payable liability on receipt), Security (ASN gate verification), and Machine Maintenance (spare part low-stock triggers draft POs automatically).

### 3.2 Vendor Master

Every supplier, vendor, and contractor is registered in the Vendor Master.

**Vendor Master Fields:**

| Field | Notes |
|---|---|
| Vendor Name | Display name |
| Vendor Code | Unique identifier |
| Legal Name | As per GST registration |
| GSTIN | For purchase tax credit (Input Tax Credit — ITC) |
| PAN | For TDS-applicable vendor payments |
| State | For CGST/SGST vs IGST determination on purchase invoices |
| Address | Registered and correspondence addresses |
| Contact Person(s) | Name, designation, phone, email |
| Vendor Category | Raw Material / Spare Parts / Service / Contractor / Transporter |
| Payment Terms | Standard credit period for this vendor |
| Bank Details | For outward payment via NEFT/RTGS |
| Approved Status | Approved / Under Review / Blacklisted |
| Vendor Rating | Computed from performance data (on-time delivery, quality acceptance rate) |
| Documents | MSME certificate, ISO certification, quality approvals — with expiry tracking |

### 3.3 Purchase Order Management

**PO Creation:**
A Purchase Order is the company's formal commitment to buy from a vendor.

**PO Fields:**

| Field | Notes |
|---|---|
| PO Number | Auto-generated from No Series |
| PO Date, Delivery Date | |
| Vendor | |
| Delivery Location | Which plant/warehouse the goods should be delivered to |
| Line Items | Item (from Item Master), description, quantity, unit, rate, discount, taxable value, GST components |
| Terms & Conditions | Standard or custom |
| Advance Payment Required | If yes, links to Finance for advance payment recording |
| Attachments | Specifications, drawings |

**PO Approval Workflow:**
- POs below a configurable value threshold are auto-approved
- POs above the threshold require one or two levels of approval (configurable)
- Department head approval for operational POs; Finance approval for high-value POs
- Approved PO is sent to the vendor (email delivery with PDF attachment)

**PO States:** Draft → Pending Approval → Approved → Sent to Vendor → Partially Received → Fully Received → Cancelled

**PO Amendments:**
Changes to a confirmed PO (quantity, rate, date) create a formal amendment; the vendor is notified and must re-acknowledge. All amendment versions are retained in history.

### 3.4 Advance Shipping Notice (ASN)

The ASN is created by the vendor (or on the vendor's behalf by the procurement team) to notify the company of an impending delivery.

**ASN Purpose:**
- Gives the warehouse advance notice to prepare receiving space
- Enables gate security to verify the delivery against a pre-loaded manifest
- Provides the reference document for GRN creation on arrival

**ASN Fields:**
- ASN Number, creation date, expected delivery date
- Reference PO number(s)
- Vendor details
- Consignment items: Item, PO quantity, ASN quantity (may differ from PO if partial shipment)
- Vehicle number, LR number, transporter
- Remarks / special handling instructions

**Vendor Self-Service ASN Creation:**
Approved vendors with access to the Vendor Portal can create ASNs themselves against their open POs. This eliminates data entry on the company's side.

**ASN States:** Created → Gate Verified → GRN Pending → GRN Completed → Closed

### 3.5 Goods Receipt & GRN Completion

When goods arrive at the gate and are security-verified (see Security module), stores staff complete the GRN:

1. Open the gate-verified ASN from the Inventory module
2. Record actual received quantities (may differ from ASN quantities)
3. Condition inspection: Good / Damaged / Short / Excess
4. If Quality module is active: GRN triggers an inspection request; items quarantined until inspection passes
5. On GRN posting: stock levels updated, payable entry created in Finance (pending the purchase invoice from vendor)

**Three-Way Match:**
For financial control, the system performs a three-way match before authorising vendor payment:
1. Purchase Order (committed quantity and price)
2. GRN (received quantity)
3. Vendor Invoice (billed quantity and price)

Discrepancies between any of the three documents flag the payment for manual review.

### 3.6 Vendor Performance Management

Avy ERP tracks and scores vendor performance automatically based on transaction data:

| Performance Metric | Data Source |
|---|---|
| On-Time Delivery Rate | ASN expected date vs GRN date |
| Fill Rate | ASN quantity vs GRN accepted quantity |
| Quality Acceptance Rate | GRN accepted qty vs GRN total received qty |
| Invoice Accuracy | PO rate vs vendor invoice rate |
| Price Variance | Actual price vs contracted price |

**Vendor Scorecard:**
A computed vendor rating (Good / Average / Poor) is displayed on the vendor record and in the vendor directory. Companies can define the weighting for each metric.

**Vendor Review Alerts:**
- Vendors falling below a configurable performance threshold are flagged for review
- Repeat quality rejections trigger an automatic escalation to the Quality or Procurement Manager
- Blacklisted vendors cannot be selected on new POs

### 3.7 Procurement Reports

| Report | Description |
|---|---|
| Purchase Register | All POs in a date range with line-item detail |
| GRN Report | All goods received, quantities, conditions |
| Vendor Wise Purchase | Total purchase value by vendor |
| Item Wise Purchase | Total purchase value by item |
| Open PO Report | POs with pending delivery quantity |
| Payables Ageing | Outstanding vendor invoices by due date bucket |
| Vendor Performance Report | Scorecard data for all vendors |
| Three-Way Match Exception Report | GRNs with PO or invoice discrepancies |

---

## 4. Module 5 — Finance & Accounting

### 4.1 Module Overview

The Finance module manages accounts receivable, accounts payable, payment recording, journal entries, bank reconciliation, and financial reporting. It is the accounting backbone that receives automated entries from the Sales & Invoicing, HR (payroll), and Vendor Management modules, reducing manual journal entry work to a minimum.

### 4.2 Chart of Accounts

**Chart of Accounts (CoA):**
The CoA is the structured list of all ledger accounts used by the company. Avy ERP provides a pre-configured CoA template for manufacturing enterprises that can be customised.

**Account Groups:**

| Group | Type |
|---|---|
| Fixed Assets | Asset |
| Current Assets (Inventory, Receivables, Cash, Bank) | Asset |
| Capital & Reserves | Equity |
| Long-Term Liabilities | Liability |
| Current Liabilities (Payables, Statutory dues) | Liability |
| Direct Income (Revenue) | Income |
| Indirect Income (Other income) | Income |
| Cost of Goods Sold / Direct Expenses | Expense |
| Indirect Expenses / Overheads | Expense |

Companies can add, rename, or reorganise accounts within the prescribed structure. Some accounts are system-controlled (e.g., the Salary Payable account that receives payroll entries) and cannot be deleted.

### 4.3 Accounts Receivable

**Receivable Ledger:**
Every confirmed sales invoice creates an entry in Accounts Receivable:
- Debit: Customer account (receivable)
- Credit: Revenue account (linked to the invoice item's revenue category)
- Credit: GST output liability accounts (CGST, SGST, or IGST)

**Receivables Management Dashboard:**
- Total outstanding receivables
- Overdue amount
- Receivables ageing: Current / 30+ / 60+ / 90+ days
- Customer-wise outstanding
- Days Sales Outstanding (DSO) metric

**Reminder Workflow:**
Configurable automated email reminders sent to customers at defined intervals before and after the invoice due date.

### 4.4 Accounts Payable

**Payable Ledger:**
Every confirmed GRN triggers a payable entry (liability) pending the vendor invoice. When the vendor's invoice arrives and is matched (three-way match), the payable is confirmed for payment.

- Debit: Inventory / Expense account
- Credit: Vendor account (payable)
- Debit: GST input account (ITC claim)

**Payables Management Dashboard:**
- Total outstanding payables
- Amount due within 7 days
- Overdue payables
- Payables ageing: Current / 30+ / 60+ / 90+ days
- Vendor-wise outstanding

### 4.5 Payment Recording

**Outward Payments (to vendors):**
- Payment mode: NEFT, RTGS, Cheque, Cash
- Reference number, payment date, bank account
- Allocated against one or more vendor invoices
- TDS deduction applied if vendor is TDS-applicable
- Payment advice generated as PDF (sent to vendor)

**Inward Payments (from customers):**
- Already handled in the Sales & Invoicing module (Payment-In)
- The Finance module reflects these as credits to the customer's receivable account

**Advance Payments:**
- Advances paid to vendors before delivery: recorded as an asset (advance to vendor)
- Advances received from customers before invoicing: recorded as a liability (customer advance)
- Advances automatically adjusted against the corresponding invoice when created

### 4.6 Journal Entries & GL

**Manual Journal Entries:**
For transactions not generated by other modules (depreciation, accruals, provisions, adjustments), the Finance team posts manual journal entries.

A journal entry must:
- Have equal debit and credit totals (system enforces this)
- Reference at least two accounts
- Carry a narration explaining the entry
- Be approved (optional, configurable for above-threshold entries)

**General Ledger:**
The GL is the aggregate record of all entries. It can be viewed by account, date range, or transaction reference. Every entry is traceable back to the source document (invoice, GRN, payslip, etc.).

### 4.7 Bank Reconciliation

Bank reconciliation matches the company's internal payment records against the bank statement to identify any discrepancies.

**Workflow:**
1. Import bank statement (CSV or manually entered)
2. System auto-matches entries based on amount, date, and reference
3. Unmatched entries flagged for manual review
4. Matched entries marked as reconciled
5. Reconciliation report shows closing balance alignment

### 4.8 Financial Statements

**Profit & Loss Statement:**
Compares revenue and expenses for a selected period. Shows Gross Profit, Operating Profit, and Net Profit. Comparable against the prior period.

**Balance Sheet:**
Snapshot of the company's financial position: Assets, Liabilities, and Equity at a point in time.

**Cash Flow Statement:**
Three-section statement: Operating Activities, Investing Activities, Financing Activities. Computed from the accounting data using the indirect method.

**Trial Balance:**
Debit and credit column summaries for all accounts for a period. Used for period-end checks before generating financial statements.

All financial statements can be generated for any date range and exported as PDF or Excel.

### 4.9 GST Returns Support

**GSTR-1 (Outward Supplies):**
The system generates the GSTR-1 data extract from confirmed sales invoices. Data includes invoice-wise, credit note-wise, and HSN-wise summary in the prescribed format for uploading to the GST portal.

**GSTR-2B Reconciliation (Input Tax Credit):**
The system can be configured to compare purchase invoice data against the GSTR-2B report downloaded from the GST portal, flagging mismatches for follow-up with vendors.

**GSTR-3B (Monthly Summary):**
Aggregate summary of output tax, input tax credit, and net tax payable — generated from the system's sales and purchase data in the prescribed format.

### 4.10 Finance Reports & Export

| Report | Description |
|---|---|
| P&L Statement | Revenue vs expenses for any period |
| Balance Sheet | Financial position snapshot |
| Cash Flow Statement | Cash movements by activity |
| Trial Balance | All account balances for period-end check |
| Receivables Ageing | Customer outstanding by age bucket |
| Payables Ageing | Vendor outstanding by age bucket |
| GST Output Report | GSTR-1 data for outward supplies |
| GST Input Report | Purchase invoice-wise ITC data |
| Bank Reconciliation Report | Matched and unmatched entries |
| Vendor Payment History | All payments made to a vendor |
| Customer Receipt History | All receipts from a customer |
| Cost Centre Report | Expenses by department / cost centre |

All reports exportable as PDF and Excel.

---

## 5. Module 10 — Masters

The Masters module is the shared configuration layer that all other modules reference. It is not a standalone transactional module but a foundational data set that must be configured before other modules can function correctly.

### 5.1 Item Master (Shared)

Detailed in Inventory Management (Section 2.2). The Item Master is shared across Sales & Invoicing, Inventory, Vendor Management, and Production modules.

### 5.2 Machine Master (Shared)

The Machine Master is the central registry of all production equipment and machinery.

**Machine Master Fields:**

| Field | Notes |
|---|---|
| Machine Code | Unique identifier |
| Machine Name | Common name |
| Machine Type | CNC / VMC / Lathe / Hydraulic Press / Welding / Conveyor / etc. |
| Plant / Location | Where this machine is physically located |
| Department | Owning department |
| Make & Model | Manufacturer name and model number |
| Serial Number | Manufacturer serial number |
| Year of Manufacture | |
| Date of Installation | |
| Rated Capacity | Production capacity per shift/day at 100% |
| Power Rating (KW) | For energy consumption tracking |
| Shift Availability | Which shifts this machine is scheduled to run |
| Linked Operations | Operations that can be performed on this machine |
| PM Schedule | Linked preventive maintenance schedule |
| Asset ID | Link to Finance module asset register |

### 5.3 Operation Master

Operations are the manufacturing processes that can be performed in the facility (e.g., Drilling, Welding, Grinding, Assembly, Painting). The Operation Master stores:
- Operation Code and Name
- Standard time per unit (cycle time)
- Machine(s) capable of performing this operation
- Labour category (which employee grade/skill is required)
- Incentive rate (used in payroll incentive computation)

### 5.4 Part / Finished Goods Master

A specialised subset of the Item Master focusing on manufactured parts and finished products:
- Part Code, Part Name
- Drawing number / revision
- Bill of Materials (BOM) reference — list of raw materials required to produce one unit
- Routing — sequence of operations and machines required
- Standard production time per unit

### 5.5 Shift Master (Shared)

Detailed in the Company Configuration section (Part 1, Section 8.8). The Shift Master is shared across Attendance, Production, and Machine Maintenance modules as the common time reference.

### 5.6 UOM Master

The Unit of Measure master stores all measurement units used in the company:
- Primary UOMs: KG, Grams, LTR, ML, MTR, CM, PCS, BOX, SET, ROLL, SHEET
- Alternate UOM conversions: 1 BOX = 12 PCS, 1 KG = 1000 Grams
- UOMs are selected when creating item records and used consistently across all transactions

---

*This is Part 4 of 5 of the Avy ERP Master PRD.*
*Part 5 covers: Production, Machine Maintenance, Calibration Management, Quality Management, EHSS, CRM, and Project Management modules.*

---

**Document Control**

| Field | Value |
|---|---|
| Product | Avy ERP |
| Company | Avyren Technologies |
| Part | 4 of 5 — Sales, Inventory, Vendor Management & Finance |
| Version | 2.0 |
| Date | April 2026 |
| Status | Final Draft |
| Classification | Confidential — Internal Use Only |
