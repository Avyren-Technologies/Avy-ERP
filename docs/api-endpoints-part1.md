# AVY ERP Backend - API Endpoint Documentation (Part 1)

> **Base URL:** `/api/v1` (configured via `API_PREFIX` env variable)
>
> **Generated:** 2026-03-21

---

## Table of Contents

1. [Authentication](#1-authentication)
2. [Super Admin - Tenant Management](#2-super-admin--tenant-management)
3. [Super Admin - Company Management](#3-super-admin--company-management)
4. [Super Admin - Dashboard](#4-super-admin--dashboard)
5. [Super Admin - Audit Logs](#5-super-admin--audit-logs)
6. [Super Admin - Billing](#6-super-admin--billing)
7. [Super Admin - Billing Config](#7-super-admin--billing-config)
8. [Super Admin - Invoices](#8-super-admin--invoices)
9. [Super Admin - Payments](#9-super-admin--payments)
10. [Super Admin - Subscriptions](#10-super-admin--subscriptions)
11. [Company Admin](#11-company-admin)
12. [Company Admin - Dashboard](#12-company-admin--dashboard)
13. [RBAC (Role-Based Access Control)](#13-rbac-role-based-access-control)
14. [Feature Toggles](#14-feature-toggles)

---

## 1. Authentication

**Base path:** `/api/v1/auth`

| Method | Path | Description | Auth Required |
|--------|------|-------------|---------------|
| POST | `/auth/login` | Authenticate user and receive tokens | No |
| POST | `/auth/register` | Register a new user account | No |
| POST | `/auth/refresh-token` | Refresh an expired access token | No |
| POST | `/auth/forgot-password` | Request a password reset code via email | No |
| POST | `/auth/verify-reset-code` | Verify the password reset code | No |
| POST | `/auth/reset-password` | Reset password using verified code | No |
| POST | `/auth/change-password` | Change password (logged-in user) | Yes |
| POST | `/auth/logout` | Invalidate current session/token | Yes |
| GET | `/auth/profile` | Get current authenticated user profile | Yes |

### POST `/auth/login` -- Request Body

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| email | string | Yes | User email address |
| password | string | Yes | User password |

### POST `/auth/register` -- Request Body

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| email | string | Yes | User email address |
| password | string | Yes | User password |
| firstName | string | Yes | User first name |
| lastName | string | Yes | User last name |
| phone | string | Yes | Phone number |
| companyName | string | Yes | Company name |

### POST `/auth/refresh-token` -- Request Body

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| refreshToken | string | Yes | The refresh token from login response |

### POST `/auth/forgot-password` -- Request Body

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| email | string | Yes | Email address of the account |

### POST `/auth/verify-reset-code` -- Request Body

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| email | string | Yes | Email address of the account |
| code | string | Yes | Reset code received via email |

### POST `/auth/reset-password` -- Request Body

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| email | string | Yes | Email address of the account |
| code | string | Yes | Verified reset code |
| newPassword | string | Yes | New password to set |

### POST `/auth/change-password` -- Request Body

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| currentPassword | string | Yes | Current password |
| newPassword | string | Yes | New password |

---

## 2. Super Admin -- Tenant Management

**Base path:** `/api/v1/platform/tenants`
**Auth:** Requires `platform:admin` permission (super-admin only)

| Method | Path | Description | Auth Required |
|--------|------|-------------|---------------|
| POST | `/platform/tenants/onboard` | Full tenant onboarding (16-step wizard data) | Yes |
| POST | `/platform/tenants/` | Create a new tenant | Yes |
| GET | `/platform/tenants/` | List all tenants (paginated) | Yes |
| GET | `/platform/tenants/stats` | Get tenant statistics | Yes |
| GET | `/platform/tenants/:tenantId` | Get a single tenant by ID | Yes |
| PUT | `/platform/tenants/:tenantId` | Update a tenant | Yes |
| DELETE | `/platform/tenants/:tenantId` | Delete a tenant | Yes |
| GET | `/platform/tenants/company/:companyId` | Get tenant by company ID | Yes |
| GET | `/platform/tenants/company/:companyId/detail` | Get full company detail | Yes |
| PATCH | `/platform/tenants/company/:companyId/section/:sectionKey` | Update a specific section of a company | Yes |
| PATCH | `/platform/tenants/company/:companyId/status` | Update company wizard status | Yes |
| DELETE | `/platform/tenants/company/:companyId` | Delete a company | Yes |

### POST `/platform/tenants/onboard` -- Request Body

Full onboarding payload with all 16 wizard sections:

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| identity | object | Yes | Company identity information |
| statutory | object | Yes | Statutory & tax registration details |
| address | object | Yes | Registered & corporate addresses |
| fiscal | object | Yes | Fiscal year & calendar configuration |
| preferences | object | Yes | System preferences & integrations |
| endpoint | object | Yes | Backend endpoint configuration |
| strategy | object | Yes | Multi-location strategy |
| locations | array | Yes | Plant/branch locations (min 1) |
| commercial | object | No | Module selection & pricing |
| contacts | array | No | Key contacts (default: []) |
| shifts | object | No | Shift master configuration |
| noSeries | array | No | Number series definitions (default: []) |
| iotReasons | array | No | IoT reason codes (default: []) |
| controls | object | No | System control toggles (default: {}) |
| users | array | No | Initial user accounts (default: []) |

#### `identity` object

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| displayName | string | Yes (min 2) | Display name of the company |
| legalName | string | Yes (min 2) | Legal registered name |
| businessType | string | Yes | Type of business |
| industry | string | Yes | Industry category |
| companyCode | string | Yes (min 2) | Unique company code |
| shortName | string | No | Short name / abbreviation |
| incorporationDate | string | No | Date of incorporation |
| employeeCount | string | No | Approximate employee count |
| cin | string | No | Corporate Identification Number |
| website | string | No | Company website URL |
| emailDomain | string | Yes | Primary email domain |
| logoUrl | string | No | Company logo URL |
| wizardStatus | string | No | Current wizard completion status |

#### `statutory` object

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| pan | string | Yes | PAN number |
| tan | string | No | TAN number |
| gstin | string | No | GSTIN number |
| pfRegNo | string | No | PF registration number |
| esiCode | string | No | ESI code |
| ptReg | string | No | Professional tax registration |
| lwfrNo | string | No | LWFR number |
| rocState | string | No | ROC state |

#### `address` object

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| registered | object | Yes | Registered address (line1, line2, city, district, state, pin, country, stdCode) |
| sameAsRegistered | boolean | Yes | Whether corporate address is same as registered |
| corporate | object | No | Corporate address (same fields as registered) |

#### `fiscal` object

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| fyType | string | Yes | Fiscal year type |
| fyCustomStartMonth | string | No | Custom FY start month |
| fyCustomEndMonth | string | No | Custom FY end month |
| payrollFreq | string | Yes | Payroll frequency |
| cutoffDay | string | Yes | Payroll cutoff day |
| disbursementDay | string | Yes | Salary disbursement day |
| weekStart | string | Yes | Week start day |
| timezone | string | Yes | Timezone |
| workingDays | string[] | Yes (min 1) | Working days of the week |

#### `preferences` object

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| currency | string | Yes | Base currency |
| language | string | Yes | Default language |
| dateFormat | string | Yes | Date format |
| numberFormat | string | No | Number format |
| timeFormat | string | No | Time format (12h/24h) |
| indiaCompliance | boolean | Yes | India compliance mode |
| multiCurrency | boolean | No | Multi-currency support |
| ess | boolean | No | Employee self-service |
| mobileApp | boolean | Yes | Mobile app access |
| webApp | boolean | Yes | Web app access |
| systemApp | boolean | No | System app access |
| aiChatbot | boolean | No | AI chatbot enabled |
| eSign | boolean | No | E-signature enabled |
| biometric | boolean | Yes | Biometric attendance |
| bankIntegration | boolean | Yes | Bank integration |
| emailNotif | boolean | Yes | Email notifications |
| whatsapp | boolean | No | WhatsApp notifications |
| razorpayEnabled | boolean | No | RazorpayX integration |
| razorpayKeyId | string | No | Razorpay Key ID |
| razorpayKeySecret | string | No | Razorpay Key Secret |
| razorpayWebhookSecret | string | No | Razorpay Webhook Secret |
| razorpayAccountNumber | string | No | Razorpay account number |
| razorpayAutoDisbursement | boolean | No | Auto disbursement via Razorpay |
| razorpayTestMode | boolean | No | Razorpay test mode |

#### `endpoint` object

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| endpointType | enum | Yes | `'default'` or `'custom'` |
| customBaseUrl | string | No | Custom backend URL (when type is custom) |

#### `strategy` object

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| multiLocationMode | boolean | Yes | Enable multi-location mode |
| locationConfig | enum | Yes | `'common'` or `'per-location'` |

#### `locations[]` array items

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| name | string | Yes | Location name |
| code | string | Yes | Location code |
| facilityType | string | Yes | Facility type |
| customFacilityType | string | No | Custom facility type name |
| status | string | No | Status (default: 'Active') |
| isHQ | boolean | No | Is headquarters (default: false) |
| addressLine1 | string | No | Address line 1 |
| addressLine2 | string | No | Address line 2 |
| city | string | No | City |
| district | string | No | District |
| state | string | No | State |
| pin | string | No | PIN/ZIP code |
| country | string | No | Country |
| stdCode | string | No | STD code |
| gstin | string | No | Location GSTIN |
| stateGST | string | No | State GST code |
| contactName | string | No | Contact person name |
| contactDesignation | string | No | Contact person designation |
| contactEmail | string | No | Contact email (validated) |
| contactCountryCode | string | No | Phone country code |
| contactPhone | string | No | Contact phone number |
| geoEnabled | boolean | No | Geo-fencing enabled (default: false) |
| geoLocationName | string | No | Geo location name |
| geoLat | string | No | Latitude |
| geoLng | string | No | Longitude |
| geoRadius | number | No | Geo-fence radius (meters) |
| geoShape | string | No | Geo-fence shape |
| moduleIds | string[] | No | Per-location module IDs |
| customModulePricing | Record<string, number> | No | Per-location custom module pricing |
| userTier | string | No | Per-location user tier |
| customUserLimit | string | No | Custom user limit |
| customTierPrice | string | No | Custom tier price |
| billingType | string | No | Per-location billing type |
| trialDays | number | No | Trial period in days |

#### `commercial` object (optional)

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| selectedModuleIds | string[] | No | Selected module IDs |
| customModulePricing | Record<string, number> | No | Custom pricing per module |
| userTier | string | No | User tier key |
| customUserLimit | string | No | Custom user limit |
| customTierPrice | string | No | Custom tier price |
| billingType | string | No | Billing type |
| trialDays | number | No | Trial period in days (integer, min 0) |

#### `contacts[]` array items

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| name | string | Yes | Contact name |
| designation | string | No | Designation |
| department | string | No | Department |
| type | string | Yes | Contact type |
| email | string | Yes | Email (validated) |
| countryCode | string | No | Phone country code |
| mobile | string | Yes | Mobile number |
| linkedin | string | No | LinkedIn profile URL |

#### `shifts` object

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| dayStartTime | string | No | Day boundary start time |
| dayEndTime | string | No | Day boundary end time |
| weeklyOffs | string[] | No | Weekly off days |
| items | array | No | Shift definitions (default: []) |

#### `shifts.items[]` array items

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| name | string | Yes | Shift name |
| fromTime | string | Yes | Shift start time |
| toTime | string | Yes | Shift end time |
| noShuffle | boolean | No | Disable shift shuffling |
| downtimeSlots | array | No | Downtime slot definitions |

#### `shifts.items[].downtimeSlots[]`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| type | string | Yes | Downtime type |
| duration | string | Yes | Duration |

#### `noSeries[]` array items

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| code | string | Yes | Series code |
| linkedScreen | string | Yes | Linked screen/module |
| description | string | No | Description |
| prefix | string | Yes | Number prefix |
| suffix | string | No | Number suffix |
| numberCount | number | No | Digit count (integer, min 1) |
| startNumber | number | No | Starting number (integer, min 0) |

#### `iotReasons[]` array items

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| reasonType | string | Yes | Reason type category |
| reason | string | Yes | Reason description |
| description | string | No | Detailed description |
| department | string | No | Department |
| planned | boolean | No | Is planned downtime |
| duration | string | No | Expected duration |

#### `controls` object

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| ncEditMode | boolean | No | NC edit mode |
| loadUnload | boolean | No | Load/unload tracking |
| cycleTime | boolean | No | Cycle time tracking |
| payrollLock | boolean | No | Payroll lock |
| leaveCarryForward | boolean | No | Leave carry forward |
| overtimeApproval | boolean | No | Overtime approval required |
| mfa | boolean | No | Multi-factor authentication |

#### `users[]` array items

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| fullName | string | Yes (min 2) | Full name |
| username | string | Yes (min 2) | Username |
| password | string | Yes (min 6) | Password |
| role | string | Yes | Role assignment |
| email | string | Yes | Email (validated) |
| mobile | string | No | Mobile number |
| department | string | No | Department |

### PATCH `/platform/tenants/company/:companyId/section/:sectionKey` -- Request Body

The request body depends on the `sectionKey` path parameter. Valid section keys and their schemas:

| Section Key | Schema | Description |
|-------------|--------|-------------|
| `identity` | identity object (see onboard) | Company identity fields |
| `statutory` | statutory object (see onboard) | Statutory & tax fields |
| `address` | address object (see onboard) | Address fields |
| `fiscal` | fiscal object (see onboard) | Fiscal & calendar fields |
| `preferences` | preferences object (see onboard) | System preferences |
| `endpoint` | endpoint object (see onboard) | Backend endpoint config |
| `strategy` | strategy object (see onboard) | Multi-location strategy |
| `controls` | controls object (see onboard) | System control toggles |
| `locations` | locations[] array (min 1) | Plant/branch locations |
| `contacts` | contacts[] array | Key contacts |
| `shifts` | shifts object (see onboard) | Shift configuration |
| `noSeries` | noSeries[] array | Number series |
| `iotReasons` | iotReasons[] array | IoT reason codes |
| `users` | users[] array | User accounts |
| `commercial` | commercial object (see onboard) | Module & pricing config |

### PATCH `/platform/tenants/company/:companyId/status` -- Request Body

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| status | enum | Yes | `'Draft'`, `'Pilot'`, `'Active'`, or `'Inactive'` |

---

## 3. Super Admin -- Company Management

**Base path:** `/api/v1/platform/companies`
**Auth:** Requires `platform:admin` permission (super-admin only)

| Method | Path | Description | Auth Required |
|--------|------|-------------|---------------|
| GET | `/platform/companies/` | List companies (paginated, searchable, filterable) | Yes |
| GET | `/platform/companies/:companyId` | Get full company detail | Yes |
| PATCH | `/platform/companies/:companyId/sections/:sectionKey` | Section-based partial update | Yes |
| PUT | `/platform/companies/:companyId/status` | Update company wizard status | Yes |
| DELETE | `/platform/companies/:companyId` | Delete a company | Yes |

### PATCH `/platform/companies/:companyId/sections/:sectionKey` -- Request Body

Same section schemas as tenant section update (see Section 2 above).

### PUT `/platform/companies/:companyId/status` -- Request Body

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| status | enum | Yes | `'Draft'`, `'Pilot'`, `'Active'`, or `'Inactive'` |

---

## 4. Super Admin -- Dashboard

**Base path:** `/api/v1/platform/dashboard`
**Auth:** Requires `platform:admin` permission (super-admin only)

| Method | Path | Description | Auth Required |
|--------|------|-------------|---------------|
| GET | `/platform/dashboard/stats` | Get super admin dashboard KPIs | Yes |
| GET | `/platform/dashboard/activity` | Get recent platform activity | Yes |
| GET | `/platform/dashboard/revenue` | Get revenue metrics | Yes |

---

## 5. Super Admin -- Audit Logs

**Base path:** `/api/v1/platform/audit-logs`
**Auth:** Requires `platform:admin` permission (super-admin only)

| Method | Path | Description | Auth Required |
|--------|------|-------------|---------------|
| GET | `/platform/audit-logs/` | List audit logs (paginated, filterable) | Yes |
| GET | `/platform/audit-logs/filters` | Get available filter options (action types + entity types) | Yes |
| GET | `/platform/audit-logs/entity/:entityType/:entityId` | Get audit logs for a specific entity | Yes |
| GET | `/platform/audit-logs/:id` | Get a single audit log by ID | Yes |

---

## 6. Super Admin -- Billing

**Base path:** `/api/v1/platform/billing`
**Auth:** Requires `platform:admin` permission (super-admin only)

| Method | Path | Description | Auth Required |
|--------|------|-------------|---------------|
| GET | `/platform/billing/summary` | Get revenue summary KPIs | Yes |
| GET | `/platform/billing/revenue-chart` | Get monthly revenue chart data | Yes |

---

## 7. Super Admin -- Billing Config

**Base path:** `/api/v1/platform/billing/config`
**Auth:** Requires `platform:admin` permission (super-admin only)

| Method | Path | Description | Auth Required |
|--------|------|-------------|---------------|
| GET | `/platform/billing/config/defaults` | Get billing config defaults | Yes |
| PATCH | `/platform/billing/config/defaults` | Update billing config defaults | Yes |

### PATCH `/platform/billing/config/defaults` -- Request Body

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| defaultOneTimeMultiplier | number | No | One-time license fee multiplier (min 0) |
| defaultAmcPercentage | number | No | AMC percentage (0-100) |
| defaultCgstRate | number | No | CGST rate (0-100) |
| defaultSgstRate | number | No | SGST rate (0-100) |
| defaultIgstRate | number | No | IGST rate (0-100) |
| platformGstin | string | No | Platform GSTIN number |
| invoicePrefix | string | No | Invoice number prefix |

---

## 8. Super Admin -- Invoices

**Base path:** `/api/v1/platform/billing/invoices`
**Auth:** Requires `platform:admin` permission (super-admin only)

| Method | Path | Description | Auth Required |
|--------|------|-------------|---------------|
| GET | `/platform/billing/invoices/` | List invoices (paginated, filterable) | Yes |
| GET | `/platform/billing/invoices/:id` | Get single invoice by ID | Yes |
| POST | `/platform/billing/invoices/generate` | Generate a new invoice | Yes |
| PATCH | `/platform/billing/invoices/:id/mark-paid` | Mark invoice as paid | Yes |
| PATCH | `/platform/billing/invoices/:id/void` | Void an invoice | Yes |
| POST | `/platform/billing/invoices/:id/send-email` | Send invoice via email | Yes |
| GET | `/platform/billing/invoices/:id/pdf` | Download invoice as PDF | Yes |

### POST `/platform/billing/invoices/generate` -- Request Body

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| companyId | string | Yes | Target company ID |
| locationId | string | No | Specific location ID |
| invoiceType | enum | Yes | `'SUBSCRIPTION'`, `'ONE_TIME_LICENSE'`, `'AMC'`, or `'PRORATED_ADJUSTMENT'` |
| billingPeriodStart | string | No | Billing period start date |
| billingPeriodEnd | string | No | Billing period end date |
| customLineItems | array | No | Custom line items |
| notes | string | No | Invoice notes |

#### `customLineItems[]` array items

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| description | string | Yes | Line item description |
| quantity | number | Yes (min 0) | Quantity |
| unitPrice | number | Yes (min 0) | Unit price |
| amount | number | Yes (min 0) | Total amount |

### PATCH `/platform/billing/invoices/:id/mark-paid` -- Request Body

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| method | enum | Yes | `'BANK_TRANSFER'`, `'CHEQUE'`, `'CASH'`, `'RAZORPAY'`, `'UPI'`, or `'OTHER'` |
| transactionReference | string | No | Transaction reference/ID |
| paidAt | string | No | Payment date (ISO string) |
| notes | string | No | Payment notes |

---

## 9. Super Admin -- Payments

**Base path:** `/api/v1/platform/billing/payments`
**Auth:** Requires `platform:admin` permission (super-admin only)

| Method | Path | Description | Auth Required |
|--------|------|-------------|---------------|
| GET | `/platform/billing/payments/` | List payments (paginated, filterable by companyId, invoiceId, method, dateFrom, dateTo) | Yes |
| GET | `/platform/billing/payments/:id` | Get single payment by ID | Yes |
| POST | `/platform/billing/payments/record` | Record a new payment against an invoice | Yes |

### POST `/platform/billing/payments/record` -- Request Body

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| invoiceId | string | Yes | Invoice ID to apply payment to |
| amount | number | Yes (positive) | Payment amount |
| method | enum | Yes | `'BANK_TRANSFER'`, `'CHEQUE'`, `'CASH'`, `'RAZORPAY'`, `'UPI'`, or `'OTHER'` |
| transactionReference | string | No | Transaction reference/ID |
| paidAt | string | No | Payment date (ISO string) |
| notes | string | No | Payment notes |

---

## 10. Super Admin -- Subscriptions

**Base path:** `/api/v1/platform/billing/subscriptions`
**Auth:** Requires `platform:admin` permission (super-admin only)

| Method | Path | Description | Auth Required |
|--------|------|-------------|---------------|
| GET | `/platform/billing/subscriptions/:companyId` | Get subscription detail for a company | Yes |
| GET | `/platform/billing/subscriptions/:companyId/cost-preview` | Preview cost changes | Yes |
| PATCH | `/platform/billing/subscriptions/:companyId/billing-type` | Change billing type | Yes |
| PATCH | `/platform/billing/subscriptions/:companyId/tier` | Change user tier | Yes |
| PATCH | `/platform/billing/subscriptions/:companyId/trial` | Extend trial period | Yes |
| POST | `/platform/billing/subscriptions/:companyId/cancel` | Cancel subscription | Yes |
| POST | `/platform/billing/subscriptions/:companyId/reactivate` | Reactivate cancelled subscription | Yes |

### PATCH `/platform/billing/subscriptions/:companyId/billing-type` -- Request Body

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| billingType | enum | Yes | `'MONTHLY'`, `'ANNUAL'`, or `'ONE_TIME_AMC'` |
| locationId | string | No | Specific location ID |
| oneTimeOverride | number | No | One-time fee override (min 0) |
| amcOverride | number | No | AMC fee override (min 0) |

### PATCH `/platform/billing/subscriptions/:companyId/tier` -- Request Body

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| newTier | string | Yes | New tier key |
| locationId | string | No | Specific location ID |
| customUserLimit | string | No | Custom user limit |
| customTierPrice | string | No | Custom tier price |

### PATCH `/platform/billing/subscriptions/:companyId/trial` -- Request Body

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| newEndDate | string | Yes | New trial end date |
| locationId | string | No | Specific location ID |

---

## 11. Company Admin

**Base path:** `/api/v1/company`
**Auth:** Requires tenant context + specific permissions per endpoint

### Profile

| Method | Path | Description | Auth Required | Permission |
|--------|------|-------------|---------------|------------|
| GET | `/company/profile` | Get own company profile | Yes | `company:read` |
| PATCH | `/company/profile/sections/:sectionKey` | Update a profile section | Yes | `company:update` |

#### PATCH `/company/profile/sections/:sectionKey` -- Request Body

Valid section keys: `identity`, `address`, `contacts`

**`identity` section:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| displayName | string | No (min 2) | Display name |
| legalName | string | No (min 2) | Legal name |
| shortName | string | No | Short name |
| logoUrl | string | No | Logo URL |
| website | string | No | Website |
| emailDomain | string | No | Email domain |

**`address` section:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| registered | object | Yes | Registered address (line1, line2, city, district, state, pin, country, stdCode) |
| sameAsRegistered | boolean | Yes | Same as registered flag |
| corporate | object | No | Corporate address (same fields) |

**`contacts` section:** Array of contact objects (name, designation, department, type, email, countryCode, mobile, linkedin)

### Locations

| Method | Path | Description | Auth Required | Permission |
|--------|------|-------------|---------------|------------|
| GET | `/company/locations` | List all locations | Yes | `company:read` |
| GET | `/company/locations/:id` | Get location by ID | Yes | `company:read` |
| POST | `/company/locations` | Create location (returns 403 -- super admin only) | Yes | `location:write` |
| PATCH | `/company/locations/:id` | Update a location | Yes | `company:update` |
| DELETE | `/company/locations/:id` | Delete a location | Yes | `company:delete` |

#### PATCH `/company/locations/:id` -- Request Body

All fields are optional:

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| name | string | No | Location name |
| facilityType | string | No | Facility type |
| customFacilityType | string | No | Custom facility type |
| status | string | No | Status |
| addressLine1 | string | No | Address line 1 |
| addressLine2 | string | No | Address line 2 |
| city | string | No | City |
| district | string | No | District |
| state | string | No | State |
| pin | string | No | PIN/ZIP code |
| country | string | No | Country |
| stdCode | string | No | STD code |
| gstin | string | No | GSTIN |
| stateGST | string | No | State GST |
| contactName | string | No | Contact name |
| contactDesignation | string | No | Contact designation |
| contactEmail | string | No | Contact email |
| contactCountryCode | string | No | Country code |
| contactPhone | string | No | Contact phone |
| geoEnabled | boolean | No | Geo-fencing enabled |
| geoLocationName | string | No | Geo location name |
| geoLat | string | No | Latitude |
| geoLng | string | No | Longitude |
| geoRadius | number | No | Radius (meters) |
| geoShape | string | No | Fence shape |

### Shifts

| Method | Path | Description | Auth Required | Permission |
|--------|------|-------------|---------------|------------|
| GET | `/company/shifts` | List all shifts | Yes | `company:read` |
| GET | `/company/shifts/:id` | Get shift by ID | Yes | `company:read` |
| POST | `/company/shifts` | Create a shift | Yes | `company:create` |
| PATCH | `/company/shifts/:id` | Update a shift | Yes | `company:update` |
| DELETE | `/company/shifts/:id` | Delete a shift | Yes | `company:delete` |

#### POST `/company/shifts` -- Request Body

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| name | string | Yes | Shift name |
| fromTime | string | Yes | Shift start time |
| toTime | string | Yes | Shift end time |
| noShuffle | boolean | No | Disable shift shuffling |
| downtimeSlots | array | No | Downtime slot definitions |

#### `downtimeSlots[]` items: `{ type: string, duration: string }`

#### PATCH `/company/shifts/:id` -- Request Body

Same fields as POST, all optional (partial update).

### Contacts

| Method | Path | Description | Auth Required | Permission |
|--------|------|-------------|---------------|------------|
| GET | `/company/contacts` | List all contacts | Yes | `company:read` |
| GET | `/company/contacts/:id` | Get contact by ID | Yes | `company:read` |
| POST | `/company/contacts` | Create a contact | Yes | `company:create` |
| PATCH | `/company/contacts/:id` | Update a contact | Yes | `company:update` |
| DELETE | `/company/contacts/:id` | Delete a contact | Yes | `company:delete` |

#### POST `/company/contacts` -- Request Body

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| name | string | Yes | Contact name |
| designation | string | No | Designation |
| department | string | No | Department |
| type | string | Yes | Contact type |
| email | string | Yes | Email (validated) |
| countryCode | string | No | Phone country code |
| mobile | string | Yes | Mobile number |
| linkedin | string | No | LinkedIn URL |

#### PATCH `/company/contacts/:id` -- Request Body

Same fields as POST, all optional (partial update).

### No. Series

| Method | Path | Description | Auth Required | Permission |
|--------|------|-------------|---------------|------------|
| GET | `/company/no-series` | List all number series | Yes | `company:read` |
| GET | `/company/no-series/:id` | Get number series by ID | Yes | `company:read` |
| POST | `/company/no-series` | Create a number series | Yes | `company:create` |
| PATCH | `/company/no-series/:id` | Update a number series | Yes | `company:update` |
| DELETE | `/company/no-series/:id` | Delete a number series | Yes | `company:delete` |

#### POST `/company/no-series` -- Request Body

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| code | string | Yes | Series code |
| linkedScreen | string | Yes | Linked screen/module |
| description | string | No | Description |
| prefix | string | Yes | Number prefix |
| suffix | string | No | Number suffix |
| numberCount | number | No | Digit count (integer, min 1) |
| startNumber | number | No | Starting number (integer, min 0) |

#### PATCH `/company/no-series/:id` -- Request Body

Same fields as POST, all optional (partial update).

### IoT Reasons

| Method | Path | Description | Auth Required | Permission |
|--------|------|-------------|---------------|------------|
| GET | `/company/iot-reasons` | List all IoT reasons | Yes | `company:read` |
| GET | `/company/iot-reasons/:id` | Get IoT reason by ID | Yes | `company:read` |
| POST | `/company/iot-reasons` | Create an IoT reason | Yes | `company:create` |
| PATCH | `/company/iot-reasons/:id` | Update an IoT reason | Yes | `company:update` |
| DELETE | `/company/iot-reasons/:id` | Delete an IoT reason | Yes | `company:delete` |

#### POST `/company/iot-reasons` -- Request Body

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| reasonType | string | Yes | Reason type category |
| reason | string | Yes | Reason description |
| description | string | No | Detailed description |
| department | string | No | Department |
| planned | boolean | No | Is planned downtime |
| duration | string | No | Expected duration |

#### PATCH `/company/iot-reasons/:id` -- Request Body

Same fields as POST, all optional (partial update).

### Controls

| Method | Path | Description | Auth Required | Permission |
|--------|------|-------------|---------------|------------|
| GET | `/company/controls` | Get system control toggles | Yes | `company:read` |
| PATCH | `/company/controls` | Update system control toggles | Yes | `company:update` |

#### PATCH `/company/controls` -- Request Body

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| ncEditMode | boolean | No | NC edit mode |
| loadUnload | boolean | No | Load/unload tracking |
| cycleTime | boolean | No | Cycle time tracking |
| payrollLock | boolean | No | Payroll lock |
| leaveCarryForward | boolean | No | Leave carry forward |
| overtimeApproval | boolean | No | Overtime approval required |
| mfa | boolean | No | Multi-factor authentication |

### Settings

| Method | Path | Description | Auth Required | Permission |
|--------|------|-------------|---------------|------------|
| GET | `/company/settings` | Get company settings (preferences) | Yes | `company:read` |
| PATCH | `/company/settings` | Update company settings | Yes | `company:update` |

#### PATCH `/company/settings` -- Request Body

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| currency | string | No | Base currency |
| language | string | No | Default language |
| dateFormat | string | No | Date format |
| numberFormat | string | No | Number format |
| timeFormat | string | No | Time format |
| indiaCompliance | boolean | No | India compliance mode |
| multiCurrency | boolean | No | Multi-currency support |
| ess | boolean | No | Employee self-service |
| mobileApp | boolean | No | Mobile app access |
| webApp | boolean | No | Web app access |
| systemApp | boolean | No | System app access |
| aiChatbot | boolean | No | AI chatbot |
| eSign | boolean | No | E-signature |
| biometric | boolean | No | Biometric attendance |
| bankIntegration | boolean | No | Bank integration |
| emailNotif | boolean | No | Email notifications |
| whatsapp | boolean | No | WhatsApp notifications |

### Users

| Method | Path | Description | Auth Required | Permission |
|--------|------|-------------|---------------|------------|
| GET | `/company/users` | List all users | Yes | `user:read` |
| GET | `/company/users/:id` | Get user by ID | Yes | `user:read` |
| POST | `/company/users` | Create a new user | Yes | `user:create` |
| PATCH | `/company/users/:id` | Update user details | Yes | `user:update` |
| PATCH | `/company/users/:id/status` | Activate/deactivate a user | Yes | `user:update` |

#### POST `/company/users` -- Request Body

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| firstName | string | Yes | First name |
| lastName | string | Yes | Last name |
| email | string | Yes | Email (validated) |
| password | string | Yes (min 6) | Password |
| phone | string | No | Phone number |
| role | string | No | Role to assign |

#### PATCH `/company/users/:id` -- Request Body

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| firstName | string | No | First name |
| lastName | string | No | Last name |
| email | string | No | Email (validated) |
| phone | string | No | Phone number |
| role | string | No | Role |

#### PATCH `/company/users/:id/status` -- Request Body

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| isActive | boolean | Yes | Whether the user is active |

### Audit Logs

| Method | Path | Description | Auth Required | Permission |
|--------|------|-------------|---------------|------------|
| GET | `/company/audit-logs` | List company audit logs (paginated) | Yes | `audit:read` |

---

## 12. Company Admin -- Dashboard

**Base path:** `/api/v1/dashboard`
**Auth:** Requires tenant context (company-admin)

| Method | Path | Description | Auth Required |
|--------|------|-------------|---------------|
| GET | `/dashboard/company-stats` | Get company admin dashboard KPIs | Yes |
| GET | `/dashboard/company-activity` | Get recent company activity feed | Yes |

---

## 13. RBAC (Role-Based Access Control)

**Base path:** `/api/v1/rbac`
**Auth:** Requires tenant context + specific permissions per endpoint

| Method | Path | Description | Auth Required | Permission |
|--------|------|-------------|---------------|------------|
| GET | `/rbac/roles` | List all roles for the tenant | Yes | `role:read` |
| GET | `/rbac/roles/:id` | Get role by ID | Yes | `role:read` |
| POST | `/rbac/roles` | Create a new custom role | Yes | `role:create` |
| PUT | `/rbac/roles/:id` | Update a role | Yes | `role:update` |
| DELETE | `/rbac/roles/:id` | Delete a role | Yes | `role:delete` |
| POST | `/rbac/roles/assign` | Assign a role to a user | Yes | `role:update` |
| GET | `/rbac/permissions` | Get permission catalogue | Yes | `role:read` |
| GET | `/rbac/reference-roles` | Get reference/template roles | Yes | `role:read` |

### POST `/rbac/roles` -- Request Body

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| name | string | Yes | Role name |
| description | string | No | Role description |
| permissions | string[] | Yes | Array of permission strings |

### PUT `/rbac/roles/:id` -- Request Body

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| name | string | No | Role name |
| description | string | No | Role description |
| permissions | string[] | No | Array of permission strings |
| isActive | boolean | No | Whether the role is active |

### POST `/rbac/roles/assign` -- Request Body

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| userId | string | Yes | User ID to assign role to |
| roleId | string | Yes | Role ID to assign |

---

## 14. Feature Toggles

**Base path:** `/api/v1/feature-toggles`
**Auth:** Requires tenant context + specific permissions per endpoint

| Method | Path | Description | Auth Required | Permission |
|--------|------|-------------|---------------|------------|
| GET | `/feature-toggles/` | Get feature toggles (for self or specific user via `?userId=`) | Yes | `user:read` |
| PUT | `/feature-toggles/user/:userId` | Set feature toggles for a specific user | Yes | `user:update` |

### PUT `/feature-toggles/user/:userId` -- Request Body

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| toggles | Record<string, boolean> | Yes | Key-value map of feature toggle names to enabled/disabled state |

---

## Appendix: Common Query Parameters

Many list endpoints support the following query parameters:

| Parameter | Type | Description |
|-----------|------|-------------|
| page | number | Page number (default: 1) |
| limit | number | Items per page (default: 20) |
| search | string | Search query string |
| sortBy | string | Field to sort by |
| sortOrder | string | `'asc'` or `'desc'` |

### Audit Log Query Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| page | number | Page number |
| limit | number | Items per page |
| action | string | Filter by action type |
| entityType | string | Filter by entity type |
| userId | string | Filter by user ID |
| dateFrom | string | Filter from date |
| dateTo | string | Filter to date |

### Payment Query Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| companyId | string | Filter by company ID |
| invoiceId | string | Filter by invoice ID |
| method | string | Filter by payment method |
| dateFrom | string | Filter from date |
| dateTo | string | Filter to date |
