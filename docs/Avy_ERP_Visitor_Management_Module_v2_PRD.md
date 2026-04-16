# Avy ERP — Visitor Management Module (v2)
## Focused Implementation PRD — Industry-Essential Features

> **Document Code:** AVY-VMS-PRD-002
> **Module:** Visitor Management System (VMS)
> **Version:** 2.0
> **Date:** April 2026
> **Status:** Implementation-Ready

---

## Table of Contents

1. [Product Overview](#1-product-overview)
2. [Problem Statement](#2-problem-statement)
3. [Target Users & Roles](#3-target-users--roles)
4. [Visitor Lifecycle — End-to-End Flow](#4-visitor-lifecycle--end-to-end-flow)
5. [Visitor Types & Classification](#5-visitor-types--classification)
6. [Registration Flows](#6-registration-flows)
7. [Gate Check-In Operations](#7-gate-check-in-operations)
8. [Identity Verification & Visitor Badges](#8-identity-verification--visitor-badges)
9. [Safety Induction & Compliance](#9-safety-induction--compliance)
10. [Host Notification & Approval Engine](#10-host-notification--approval-engine)
11. [Real-Time Visitor Tracking & Overstay Detection](#11-real-time-visitor-tracking--overstay-detection)
12. [Check-Out Process](#12-check-out-process)
13. [Today's Visitors Dashboard](#13-todays-visitors-dashboard)
14. [Visit History & Audit Trail](#14-visit-history--audit-trail)
15. [Watchlist & Blocklist](#15-watchlist--blocklist)
16. [Multi-Gate & Multi-Plant Support](#16-multi-gate--multi-plant-support)
17. [Emergency Muster Management](#17-emergency-muster-management)
18. [Contractor & Vendor Visit Management](#18-contractor--vendor-visit-management)
19. [Group Visits](#19-group-visits)
20. [Recurring Visitor Pass](#20-recurring-visitor-pass)
21. [Vehicle & Material Gate Pass](#21-vehicle--material-gate-pass)
22. [Reporting & Analytics](#22-reporting--analytics)
23. [ERP Integrations](#23-erp-integrations)
24. [Privacy, Compliance & Data Retention](#24-privacy-compliance--data-retention)
25. [VMS Configuration & System Settings](#25-vms-configuration--system-settings)
26. [Number Series Configuration](#26-number-series-configuration)
27. [Data Model — Complete Field Reference](#27-data-model--complete-field-reference)
28. [API Endpoints Reference](#28-api-endpoints-reference)
29. [Screen Inventory — Web & Mobile](#29-screen-inventory--web--mobile)
30. [Notification Templates](#30-notification-templates)
31. [Permissions & RBAC](#31-permissions--rbac)
32. [Implementation Phases](#32-implementation-phases)
33. [Concurrency & Duplicate Check-In Prevention](#33-concurrency--duplicate-check-in-prevention)
34. [Offline Mode Specification](#34-offline-mode-specification)
35. [Visit Amendment & Extension Workflow](#35-visit-amendment--extension-workflow)
36. [Denied Entry & Failed Check-In Logging](#36-denied-entry--failed-check-in-logging)
37. [Badge Lifecycle & Invalidation](#37-badge-lifecycle--invalidation)
38. [Badge Printer Integration Specification](#38-badge-printer-integration-specification)
39. [Error States & Edge Cases](#39-error-states--edge-cases)

---

## 1. Product Overview

**Module Name:** Avy ERP Visitor Management
**Tagline:** *"Every person who enters is identified, informed, and accounted for."*
**Classification:** Industrial-Grade Security · Audit-Ready · Digital-First

Avy ERP Visitor Management is a digital platform that manages the complete visitor lifecycle — from pre-registration and invitation through identity verification, safety induction, real-time tracking, and exit logging. It is designed specifically for manufacturing and industrial environments where security, safety compliance, and emergency accountability are non-negotiable.

**This module replaces paper logbooks entirely.** Every visitor interaction is digitally logged with timestamps, creating a tamper-proof audit trail that supports regulatory compliance (OSHA, ISO, Factories Act, and company-specific policies).

---

## 2. Problem Statement

| Problem | Impact |
|---|---|
| **Lost Records** | Manual logs are easy to misplace, incomplete, or illegible — creating gaps in the security record |
| **Unverified Identity** | Visitor identity is rarely validated properly at the gate, exposing the facility to unauthorized access |
| **Safety Gaps** | PPE checks and safety inductions are difficult to enforce without a structured digital workflow |
| **Emergency Risk** | Inaccurate muster lists during emergencies make accountability impossible when it matters most |
| **No Real-Time Visibility** | Operations have no way to know exactly who is on-site at any given moment |
| **Audit Failures** | Paper records cannot satisfy regulatory inspections for Factories Act, ISO, or OSHA compliance |

---

## 3. Target Users & Roles

### 3.1 User Personas

| User Type | Role in VMS | Core Need |
|---|---|---|
| **Security Guard** | Gate operator — checks visitors in/out | Fast, one-screen check-in with verified identity |
| **Security Manager** | VMS admin — dashboards, reports, watchlists | Real-time visibility, alert management, audit oversight |
| **Host Employee** | Inviter — pre-registers visitors, approves walk-ins | Quick pre-registration, instant arrival alerts |
| **Receptionist** | Front desk — manages visitor queues, walk-ins | Efficient walk-in handling, badge issuance |
| **Company Admin** | Configuration — sets up VMS rules, visitor types | Full control over VMS behaviour and compliance settings |
| **Visitor** (external) | Guest — no app required | Frictionless check-in via QR code or visit code |

### 3.2 Role-Permission Matrix

| Capability | Security Guard | Security Manager | Host Employee | Receptionist | Company Admin |
|---|---|---|---|---|---|
| Check-in visitors at gate | Yes | Yes | No | Yes | No |
| Check-out visitors | Yes | Yes | No | Yes | No |
| View Today's Visitors Dashboard | Yes | Yes | Own guests only | Yes | Yes |
| Pre-register visitors | No | Yes | Yes | Yes | Yes |
| Approve/Reject visitor requests | No | Yes | Own guests only | No | Yes |
| View Visit History | No | Yes | Own guests only | Limited | Yes |
| Manage Watchlist / Blocklist | No | Yes | No | No | Yes |
| Configure VMS Settings | No | No | No | No | Yes |
| Generate / Export Reports | No | Yes | No | No | Yes |
| Trigger Emergency Muster | Yes | Yes | No | No | Yes |
| Create Recurring Passes | No | Yes | Yes | Yes | Yes |
| Issue Vehicle Gate Pass | Yes | Yes | No | Yes | Yes |

---

## 4. Visitor Lifecycle — End-to-End Flow

Every stage of the visitor journey is controlled, logged, and visible.

```
Pre-Registration / Self-Registration / Walk-In
    ↓
Arrival at Gate
    ↓
Identity Verification (QR scan / Visit code / ID check)
    ↓
Safety Induction (if required by visitor type)
    ↓
Host Notification & Approval (if required)
    ↓
Badge Issuance (digital or printed)
    ↓
Visitor Checked In → Real-Time On-Site Tracking
    ↓
Overstay Detection (alerts if exceeding expected duration)
    ↓
Check-Out (security desk / host-initiated / auto end-of-day)
    ↓
Visit Complete → Logged in Audit Trail
```

### 4.1 Detailed Lifecycle Diagram

```
                    ┌─────────────────────┐
                    │   PRE-REGISTRATION   │
                    │  Host creates visit  │
                    │  QR + Visit Code     │
                    │  generated           │
                    │  Invite sent via     │
                    │  Email/SMS/WhatsApp  │
                    └─────────┬───────────┘
                              │
    ┌─────────────────────────┼─────────────────────────┐
    │                         │                         │
    ▼                         ▼                         ▼
┌──────────┐          ┌──────────────┐          ┌──────────────┐
│ PRE-REG  │          │  QR SELF-REG │          │   WALK-IN    │
│ Visitor  │          │  Visitor     │          │   Security   │
│ arrives  │          │  scans QR    │          │   captures   │
│ with QR  │          │  poster at   │          │   details    │
│ or code  │          │  gate, fills │          │   manually   │
│          │          │  web form    │          │              │
└────┬─────┘          └──────┬───────┘          └──────┬───────┘
     │                       │                         │
     └───────────────────────┼─────────────────────────┘
                             ▼
                    ┌─────────────────────┐
                    │   GATE CHECK-IN     │
                    │  1. ID Verification │
                    │  2. Photo Capture   │
                    │  3. Safety Induct.  │
                    │  4. NDA (if req.)   │
                    │  5. Host Notified   │
                    │  6. Badge Issued    │
                    └─────────┬───────────┘
                              │
                              ▼
                    ┌─────────────────────┐
                    │   ON-SITE TRACKING  │
                    │  Real-time count    │
                    │  Overstay alerts    │
                    │  Host accountability│
                    └─────────┬───────────┘
                              │
                              ▼
                    ┌─────────────────────┐
                    │     CHECK-OUT       │
                    │  Security desk /    │
                    │  Host-initiated /   │
                    │  Mobile link /      │
                    │  Auto end-of-day    │
                    └─────────┬───────────┘
                              │
                              ▼
                    ┌─────────────────────┐
                    │   VISIT COMPLETE    │
                    │  Full audit trail   │
                    │  Visit logged       │
                    └─────────────────────┘
```

---

## 5. Visitor Types & Classification

Every visitor is classified at registration time. The visitor type drives the check-in workflow, badge design, and safety requirements.

### 5.1 Default Visitor Types

| Visitor Type | Code | Description | Typical Flow | Badge Colour |
|---|---|---|---|---|
| Business Guest | `BG` | Client, partner, prospective customer | Pre-reg → QR Scan → Badge → Host Notified | Blue |
| Vendor / Supplier | `VN` | Vendor representative for procurement, delivery | Pre-reg (linked to PO) → ID Check → Badge | Green |
| Contractor | `CT` | Technician, AMC engineer, maintenance worker | Pre-reg + Safety Induction + NDA → Badge | Orange |
| Delivery Agent | `DA` | Courier, logistics, raw material delivery | Walk-in → Quick Reg → Temporary Badge | Yellow |
| Government Inspector | `GI` | Labour/factory/pollution inspector, tax officer | Walk-in → Full ID Verification → VIP Badge | Red |
| Job Candidate | `JC` | Recruitment interview candidate | Pre-reg by HR → QR Scan → Badge | Purple |
| Personal Visitor | `FV` | Employee's family member / personal guest | Walk-in → Host Approval → Temporary Badge | White |
| VIP / Board Member | `VP` | Senior executive, investor, dignitary | Pre-reg by Admin → Expedited Check-In → VIP Badge | Gold |
| Auditor | `AU` | Internal/external auditor (financial, quality, safety) | Pre-reg → Full ID Verification → Badge | Black |

### 5.2 Custom Visitor Types

Company Admin can create additional visitor types with these configurable properties:

| Property | Description |
|---|---|
| Type Name | Custom label (e.g., "Consultant", "Media") |
| Type Code | Unique 2-3 character code |
| Badge Colour | Hex colour for visual identification |
| Safety Induction Required | Yes / No — which induction content to show |
| NDA Required | Yes / No |
| Photo Capture Required | Yes / No |
| ID Verification Required | Yes / No |
| Host Approval Required | Yes / No — and at which stage (pre-registration or gate arrival) |
| Maximum Visit Duration | Auto-checkout trigger (e.g., 4 hours, 8 hours) |
| Escort Required | Whether visitor must be accompanied by host |

### 5.3 Visitor Type Data Model

```
VisitorType {
  id              String    @id @default(cuid())
  companyId       String
  name            String                          // "Business Guest"
  code            String                          // "BG"
  badgeColour     String    @default("#3B82F6")   // Hex colour
  isDefault       Boolean   @default(false)       // System-provided types
  isActive        Boolean   @default(true)

  // Check-in step configuration
  requirePhoto          Boolean @default(true)
  requireIdVerification Boolean @default(true)
  requireSafetyInduction Boolean @default(false)
  requireNda            Boolean @default(false)
  requireHostApproval   Boolean @default(true)
  requireEscort         Boolean @default(false)

  // Duration & limits
  defaultMaxDurationMinutes  Int?    @default(480)  // 8 hours

  // Induction config
  safetyInductionId     String?   // FK to SafetyInduction content

  sortOrder             Int       @default(0)
  createdAt             DateTime  @default(now())
  updatedAt             DateTime  @updatedAt
}
```

---

## 6. Registration Flows

Avy ERP supports three distinct registration paths. Every path maintains full control and audit logging.

### 6.1 Pre-Registration (Host-Initiated)

**This is the recommended and fastest path.** The host employee creates the visit in advance, and the visitor receives an invitation with a QR code for instant gate check-in.

#### 6.1.1 Pre-Registration Flow

```
Host Employee → Creates visit in Avy ERP (Web or Mobile)
    ↓
System generates unique Visit Code (6-char alphanumeric) + QR Code
    ↓
[If approval required] → Routes to Approver → Approved/Rejected
    ↓
System sends Invitation to visitor (Email / SMS / WhatsApp)
    - Visit confirmation details
    - QR code image
    - Visit code (fallback)
    - Facility address + directions
    - Safety instructions
    - Optional: Pre-arrival form link
    ↓
[Optional] Visitor completes Pre-Arrival Form on own device
    - Photo upload, ID details, vehicle info
    - NDA e-signature (if required)
    - Safety acknowledgement
    ↓
Visit Day: Visitor arrives at gate
    ↓
Security scans QR / enters visit code
    ↓
System displays pre-filled visitor record → Quick identity confirmation
    ↓
Visitor Checked In (< 60 seconds for pre-registered visitors)
    ↓
Host receives arrival notification
```

#### 6.1.2 Pre-Registration Data Fields

| Field | Required | Notes |
|---|---|---|
| Visitor Full Name | Yes | |
| Visitor Mobile Number | Yes | For invitation delivery and OTP |
| Visitor Email | No | For formal email invitation |
| Visitor Company / Organisation | No | |
| Visitor Type | Yes | From Visitor Type Master |
| Purpose of Visit | Yes | Dropdown: Meeting, Delivery, Maintenance, Audit, Interview, Site Tour, Personal, Other |
| Purpose Notes | No | Free text for additional context |
| Expected Date of Visit | Yes | Single date or date range |
| Expected Arrival Time | No | Approximate arrival time |
| Expected Duration (hours) | No | Used for overstay alert |
| Host Employee | Yes | Auto-complete search from Employee Master |
| Plant / Location | Yes | Auto-defaults to host's plant |
| Gate / Entry Point | No | Auto-defaults to plant's primary gate |
| Number of Accompanying Persons | No | For group visits |
| Vehicle Details (Reg. Number, Type) | No | If visitor is driving |
| Material / Equipment Carried | No | For security clearance |
| Special Instructions | No | Parking, dress code, PPE |

#### 6.1.3 Invitation Content

When pre-registration is confirmed, the system sends an invitation containing:

| Component | Description |
|---|---|
| Visit Confirmation | "Your visit to [Company Name] has been confirmed" |
| Visit Date & Time | Expected date, arrival time, estimated duration |
| Host Name & Designation | Who the visitor is meeting |
| Facility Address | Full address with map link |
| Directions / Parking | Custom text configured per plant |
| QR Code | Unique QR code encoding the visit code — for instant gate check-in |
| Visit Code | 6-digit alphanumeric code (fallback if QR scan fails) |
| Safety Instructions | "Please wear closed-toe shoes. Safety gear provided at gate." |
| Pre-Arrival Form Link | URL to complete details in advance (optional) |
| Contact Number | Facility reception or security contact |
| Company Logo & Branding | Branded invitation reflecting company identity |

#### 6.1.4 Pre-Arrival Form (Optional — Visitor Completes Before Arriving)

This web form (accessible via link in invitation, no login needed) allows visitors to submit details before arrival, making gate check-in nearly instant.

| Field | Notes |
|---|---|
| Full Name | Pre-filled from invitation |
| Photo Upload | Selfie or passport photo |
| Government ID Type | Aadhaar, PAN, Passport, Driving Licence, Voter ID |
| Government ID Number | |
| ID Photo Upload | Front of ID document |
| Vehicle Registration Number | If driving |
| Vehicle Type | Car, Two-Wheeler, Truck, Van |
| Material Declaration | Items being brought in |
| NDA / Confidentiality Agreement | e-Signature on digital NDA (if required by visitor type) |
| Safety Acknowledgement | "I have read and understood the safety guidelines" |
| Emergency Contact | Name + mobile number |

**Technical:** The pre-arrival form is a public web page at `{APP_URL}/visit/{visitCode}` — no authentication required. The form is pre-populated with invitation data. Submitted data is saved to the visit record and available at gate check-in.

#### 6.1.5 Multi-Visitor Pre-Registration (Same Meeting)

When a host invites multiple visitors from the same company for a single meeting, they do not need to use Group Visit. Instead, the Pre-Registration form supports adding multiple visitors in a single flow:

1. Host fills in meeting details (purpose, date, time, plant)
2. Host adds visitor 1 (name, mobile, email, company)
3. Host clicks "Add Another Visitor" to add visitor 2, 3, etc.
4. On submit, the system creates **individual Visit records** for each visitor — each with their own visit code, QR code, and invitation
5. All visits share a common `meetingRef` field for grouping

**This differs from Group Visit** in that each visitor has an independent lifecycle — individual check-in, individual badge, individual check-out. The `meetingRef` simply links them for the host's convenience (view all visitors for this meeting in one place).

The host's "My Visitors Today" screen groups visits by `meetingRef` when present, showing a "3 visitors for 2:00 PM meeting with ABC Corp" summary.

### 6.2 QR Self-Registration (Visitor-Initiated, No App Required)

For visitors who arrive without prior registration but the facility has QR self-registration enabled. A QR poster is displayed at the facility entrance.

#### 6.2.1 QR Self-Registration Flow

```
QR Code Poster displayed at facility entrance / gate
    ↓
Visitor scans QR code using phone camera
    ↓
Web form opens in visitor's mobile browser (NO app download required)
    ↓
Visitor fills: Name, Mobile, Company, Purpose, Photo (selfie), Host Employee name
    ↓
Visitor accepts: Safety Terms + Privacy Consent
    ↓
Form submitted → System identifies Host Employee
    ↓
Host receives Approval Request (Push + SMS)
    ↓
Host Approves → Visitor gets confirmation on phone → Gate notified
Host Rejects → Visitor informed politely on phone
    ↓
Visitor proceeds to gate → Security verifies ID → Completes check-in
```

#### 6.2.2 QR Poster Configuration

| Setting | Description |
|---|---|
| QR Code URL | Unique URL per plant/gate: `{APP_URL}/visit/register/{plantCode}` |
| Poster Design | Company-branded poster with logo, QR code, short instructions |
| Form Fields | Configurable — admin chooses which fields are shown |
| Rate Limiting | Max 5 submissions per phone number per day (prevent spam) |

#### 6.2.4 Self-Registration Rate Limiting & Abuse Prevention

| Control | Description |
|---|---|
| **Phone-based limit** | Max 5 submissions per phone number per day. On exceeding: visitor sees "You have reached the maximum registration attempts for today. Please contact the facility reception at [phone]." |
| **IP-based limit** | Max 20 submissions per IP address per hour. Prevents automated spam even if phone numbers rotate. |
| **Phone number bypass** | If a person changes phone numbers to bypass phone-based limiting, IP limiting acts as the second layer. Repeated violations from the same IP are logged and flagged for Security Manager review. |
| **CAPTCHA** | After 3 submissions from the same device session, a CAPTCHA challenge is shown. |
| **Suspicious activity logging** | All rate-limit hits are logged in the VMS audit trail with IP, phone, user-agent, and timestamp for security review. |

#### 6.2.3 Self-Registration Form Fields

| Field | Required | Notes |
|---|---|---|
| Full Name | Yes | |
| Mobile Number | Yes | For OTP verification and notifications |
| Company / Organisation | No | |
| Purpose of Visit | Yes | Dropdown |
| Host Employee Name | Yes | Type-ahead search — system matches to Employee Master |
| Photo (Selfie) | Configurable | Camera capture on visitor's phone |
| Safety Terms Acceptance | Yes | Checkbox with terms text |
| Privacy Consent | Yes | Checkbox with privacy notice |

### 6.3 Walk-In Registration (Security/Reception Initiated)

For unannounced visitors. Security guard or receptionist captures details manually.

#### 6.3.1 Walk-In Flow

```
Visitor arrives at gate without prior registration
    ↓
Security guard opens Walk-In Registration screen
    ↓
Guard captures: Name, Mobile, Company, Purpose, Visitor Type, Host Employee
    ↓
Guard captures visitor photo (tablet/phone camera)
    ↓
Guard captures / scans ID document
    ↓
System sends approval request to Host Employee
    ↓
Host Approves → Safety Induction (if required) → Badge Issued → Checked In
Host Rejects → Visitor turned away politely
    ↓
[If host not reachable] Guard contacts host by phone for verbal confirmation
```

---

## 7. Gate Check-In Operations

The gate check-in screen is the **primary operational interface** for security guards. It must be designed for speed, clarity, and one-screen operations.

### 7.1 Gate Check-In Screen Layout

| Section | Content |
|---|---|
| **Expected Visitors Panel** (Left/Top) | Pre-registered visitors expected today, with status badges (Expected / Arrived / Checked In / No Show). Sorted by arrival time. Searchable by name. |
| **Active Check-In Form** (Centre) | Form for the visitor currently being processed — walk-in or pre-registered. |
| **Today's Stats Bar** (Top) | Total Expected · Checked In · Checked Out · Currently On-Site · Walk-Ins · Overstaying |
| **Quick Actions** (Right/Bottom) | Buttons: New Walk-In · Scan QR · Search Visitor · Emergency Muster · Print Badge |

### 7.2 Check-In Steps (Configurable per Visitor Type)

The system enforces a configurable sequence of check-in steps:

```
1. Identity Verification → 2. Photo Capture → 3. Safety Induction → 4. NDA/Waiver → 5. Host Notification → 6. Badge Issuance → 7. Check-In Confirmed
```

Each step can be toggled ON/OFF per visitor type by Company Admin:

| Step | Business Guest | Contractor | Delivery Agent | VIP | Job Candidate |
|---|---|---|---|---|---|
| Identity Verification | Yes | Yes | Yes | Yes | Yes |
| Photo Capture | Yes | Yes | Optional | No (pre-captured) | Yes |
| Safety Induction | No | Yes (mandatory) | No | No | No |
| NDA / Waiver | Optional | Yes (mandatory) | No | No | Optional |
| Host Notification | Yes | Yes | Yes | Yes (to PA/EA) | Yes (to HR) |
| Badge Issuance | Yes | Yes | Yes (temporary) | Yes (VIP badge) | Yes |

### 7.3 QR Code Scanning

When a pre-registered visitor arrives:

1. Guard taps "Scan QR" on the gate check-in screen
2. Camera opens — scans the QR code from visitor's phone/printout
3. QR code contains the visit code (e.g., `VIS-A3B7K2`)
4. System instantly pulls up the pre-registered visit record
5. All pre-filled data is displayed — guard confirms identity visually
6. Guard taps "Check In" — visitor is checked in

**QR Code Encoding:** The QR code encodes a URL: `{APP_URL}/visit/verify/{visitCode}`. When scanned by the gate app, it extracts the visit code and looks up the record. When scanned by a regular phone camera, it opens the visit status page.

### 7.4 Visit Code Manual Entry

If QR scan fails (damaged QR, low light, screen glare):
1. Guard taps "Enter Visit Code"
2. Visitor reads the 6-character code from their invitation
3. Guard types the code → system looks up the record
4. Same flow as QR scan from this point

---

## 8. Identity Verification & Visitor Badges

### 8.1 Identity Verification Methods

| Method | Description | When Used |
|---|---|---|
| **QR Code Scan** | Instant verification for pre-registered visitors | Pre-registered visitors — fastest method |
| **Visit Code Entry** | 6-digit code entered manually | Fallback when QR scan fails |
| **Government ID Scan** | Guard photographs visitor's Aadhaar, PAN, DL, Passport, or Voter ID | Default for all visitor types at first visit |
| **OTP Verification** | System sends OTP to visitor's registered mobile | High-security facilities (configurable) |

### 8.2 Visitor Badge Content

Every badge contains:

| Field | Description |
|---|---|
| Visitor Name | Full name in large, readable font |
| Visitor Photo | Captured at check-in or from pre-arrival form |
| Visitor Company | Organisation name |
| Host Employee Name | Who the visitor is meeting |
| Host Department | Department being visited |
| Visitor Type | With colour coding (e.g., "CONTRACTOR" in orange badge) |
| Badge Number | Unique ID from Number Series |
| Visit Date | Today's date |
| Valid Until | Auto-calculated from expected duration |
| QR Code on Badge | For quick check-out scanning and movement logging |
| Company Logo | Facility branding |
| Emergency Contact | Facility emergency number |

### 8.3 Badge Formats

| Format | Use Case |
|---|---|
| **Digital Badge** (on visitor's phone) | Shown on phone screen — primary format. Sent via SMS/WhatsApp link after check-in. |
| **Printed Badge** (adhesive label) | Standard physical badge — printed at gate on label printer. Worn on clothing. |
| **Printed Badge** (card) | Reusable PVC card for recurring visitors/contractors. |

### 8.4 Badge Configuration

| Setting | Description |
|---|---|
| Badge Template | Configurable layout — admin adjusts fields, logo, colour scheme |
| Auto-Print on Check-In | Badge prints automatically when check-in completes |
| Digital Badge Enabled | Send digital badge link to visitor's phone |
| Badge Size | Standard: 3.5" x 2.5" (horizontal) — configurable |

---

## 9. Safety Induction & Compliance

For manufacturing facilities, safety induction at check-in is a regulatory and operational necessity. Avy ERP enforces safety compliance as part of the visitor check-in flow.

### 9.1 Safety Induction Types

| Type | Description | Duration |
|---|---|---|
| **Safety Video** | Short video covering plant safety rules, PPE requirements, emergency exits, prohibited actions | 60-180 sec |
| **Safety Slide Deck** | Series of slides with photos and instructions (alternative for low-bandwidth) | 60-120 sec |
| **Safety Questionnaire** | 3-5 multiple-choice questions to confirm understanding (must pass to proceed) | 60 sec |
| **PPE Acknowledgement** | Checklist of PPE items visitor will receive (helmet, goggles, safety shoes, ear plugs, hi-vis vest) | 30 sec |
| **Safety Declaration** | Formal declaration: "I understand and agree to follow all safety rules" with e-signature | 30 sec |

### 9.2 Safety Induction Configuration

| Setting | Description |
|---|---|
| Induction Content per Visitor Type | Different induction for contractors vs. business guests |
| Induction Content per Plant | Different plants may have different hazards |
| Pass Criteria (Questionnaire) | Minimum score to proceed (e.g., 4 out of 5) |
| Failed Induction Action | Retry allowed (max 2 attempts) → fails again requires Security Manager intervention |
| Induction Validity | How long a completed induction remains valid (e.g., 30 days). Repeat visitors skip re-induction within validity. |
| Induction Completion Log | Stored with visit record — timestamp, score, content version |
| PPE Issue Tracking | Which PPE items issued — linked to badge for return tracking |

### 9.3 NDA & Document Signing

| Setting | Description |
|---|---|
| NDA Template | Configurable NDA document per visitor type |
| e-Signature Capture | Visitor signs on tablet/phone screen |
| Document Storage | Signed NDA stored as PDF in visitor's digital record |
| NDA Validity | Duration for which a signed NDA remains valid (e.g., 12 months). Repeat visitors skip re-signing within validity. |

### 9.4 Safety Induction Data Model

```
SafetyInduction {
  id              String    @id @default(cuid())
  companyId       String
  name            String                          // "Factory Floor Safety"
  type            SafetyInductionType             // VIDEO, SLIDES, QUESTIONNAIRE
  contentUrl      String?                         // Video/slide URL
  questions       Json?                           // Array of {question, options[], correctAnswer}
  passingScore    Int?        @default(80)        // Percentage
  durationSeconds Int?        @default(120)
  validityDays    Int?        @default(30)        // Skip re-induction within this period
  isActive        Boolean     @default(true)
  plantId         String?                         // If plant-specific, null = all plants
  createdAt       DateTime    @default(now())
  updatedAt       DateTime    @updatedAt
}

enum SafetyInductionType {
  VIDEO
  SLIDES
  QUESTIONNAIRE
  DECLARATION
}
```

---

## 10. Host Notification & Approval Engine

### 10.1 Notification Events

| Event | Recipient(s) | Channels | Priority |
|---|---|---|---|
| Pre-Registration Created | Host Employee | In-App, Email | Normal |
| Visitor Invitation Sent | Visitor | Email, SMS, WhatsApp | Normal |
| Visitor Arrived at Gate | Host Employee | Push, SMS | High |
| Visitor Checked In | Host Employee | Push, In-App | High |
| Approval Request (Walk-In / QR Self-Reg) | Host Employee | Push, SMS, Email | Urgent |
| Approval Timeout (No Response) | Host's Manager (Escalation) | Push, SMS | Urgent |
| Visitor Checked Out | Host Employee | In-App | Low |
| Visitor Overstaying | Host + Security Manager | Push, SMS | High |
| End-of-Day Unchecked-Out Visitors | Security Manager | Push, Email | High |
| Blocklisted Visitor Attempt | Security Manager | Push, SMS, Email | Critical |
| Emergency Evacuation Triggered | All on-site visitors (via SMS) | SMS | Critical |

### 10.2 Approval Workflow Configuration

| Setting | Description | Default |
|---|---|---|
| Auto-Approve Pre-Registered | Pre-registered visitors auto-approved at gate (no second approval) | Yes |
| Approval Required for Walk-Ins | Walk-in visitors require host approval before badge issued | Yes |
| Approval Required for QR Self-Reg | Self-registered visitors require host approval | Yes |
| Approval Timeout (minutes) | Minutes after which request escalates to host's manager | 15 |
| Escalation Chain | Host → Host's Manager → Security Manager | Fixed |
| Auto-Reject After Final Escalation | If no response from escalation chain within N minutes after initial timeout, auto-reject | 30 min (i.e., 15 min to host + 15 min to manager = 30 min total before auto-reject) |

### 10.3 Approval Flow

```
Visitor arrives (Walk-In or QR Self-Reg)
    ↓
System sends approval request to Host Employee
    - Push notification with Approve / Reject buttons
    - SMS with approval link
    - Email with details + action buttons
    ↓
Host sees: Visitor name, photo, company, purpose, visitor type
    ↓
Host taps "Approve" → Gate notified → Check-in proceeds
Host taps "Reject" → Visitor informed → Visit denied
    ↓
[If no response within timeout] → Escalation to Host's Manager
    ↓
[If still no response] → Auto-reject with message: "Unable to reach host. Please contact reception."
```

### 10.4 Approval from Mobile App

The host employee receives a push notification with:
- Visitor name, company, photo (if captured)
- Purpose of visit
- "Approve" and "Reject" buttons directly in the notification
- Tapping either button sends the response immediately
- Also accessible from the Avy ERP mobile app notifications screen

---

## 11. Real-Time Visitor Tracking & Overstay Detection

### 11.1 Real-Time On-Site Count

The system maintains a live count of all visitors currently on-site:

| Metric | Description |
|---|---|
| **Total On-Site Now** | Count of all visitors currently checked in but not checked out |
| **By Visitor Type** | Breakdown: Business Guests, Contractors, Delivery, etc. |
| **By Host Department** | Which departments have the most visitors |
| **By Plant / Location** | For multi-plant: visitors at each plant |
| **By Gate** | For multi-gate: arrivals per gate |
| **Average Visit Duration (Today)** | Mean time spent on-site by visitors checked out today |

### 11.2 Overstay Detection & Alerts

| Setting | Description | Default |
|---|---|---|
| Expected Duration (per Visit) | Set during pre-registration or at check-in | From visitor type default |
| Default Max Duration (per Visitor Type) | Configurable per type (e.g., Business Guest = 4 hrs, Contractor = 8 hrs) | 8 hours |
| Overstay Alert Threshold | Alert triggered X minutes after expected duration | 30 minutes |
| Overstay Alert Recipients | Host Employee + Security Manager | Both |
| Auto Check-Out Time | Hard cutoff — auto-check-out at this time daily | 20:00 (8 PM) |

### 11.3 Overstay Alert Flow

```
Visitor expected duration expires
    ↓ (+30 min grace period)
System sends overstay alert to Host Employee
    "Your visitor [Name] has been on-site for [X hours], exceeding the expected [Y hours]."
    ↓ (+30 min, still no check-out)
Escalation alert to Security Manager
    "Overstaying visitor [Name] at [Plant/Gate]. Host: [Host Name]. On-site since [Time]."
    ↓ (At auto check-out time, e.g., 8 PM)
System auto-checks out all remaining visitors
    Visit marked as "Auto-Checked-Out" in audit trail
```

---

## 12. Check-Out Process

### 12.1 Check-Out Methods

| Method | Description | Best For |
|---|---|---|
| **Security Desk** | Guard scans badge QR or searches visitor record → marks as checked out | Standard — all visitor types |
| **Host-Initiated** | Host employee marks visitor as checked out from mobile app | When host walks visitor to exit |
| **Mobile Link** | Visitor clicks "Check Out" link sent via SMS after check-in | Self-service — contactless |
| **Auto End-of-Day** | System auto-checks out all visitors at configured time (e.g., 8 PM) | End-of-day cleanup |

### 12.2 Check-Out Data Captured

| Field | Notes |
|---|---|
| Check-Out Timestamp | Exact date and time |
| Check-Out Gate | Which gate the visitor exited from |
| Check-Out Method | How check-out was performed (Manual / Self / Auto / Host) |
| Badge Returned | Yes / No |
| Material Out | Any material being taken out (for security clearance) |
| Visit Duration | Auto-calculated: Check-Out Time - Check-In Time |

---

## 13. Today's Visitors Dashboard

The central command screen for visitor operations. Real-time, single-screen view of all visitor activity for the current day.

### 13.1 Dashboard Components

**Stat Cards (Top Bar):**
| Card | Description |
|---|---|
| Total Expected | Pre-registered visitors for today |
| Checked In | Total checked in (including walk-ins) |
| On-Site Now | Currently on-site (checked in but not out) |
| Checked Out | Completed visits |
| Walk-Ins | Unscheduled visitors today |
| No Shows | Pre-registered but did not arrive |
| Overstaying | Visitors exceeding expected duration (highlighted in red) |

**Filter Bar:**
| Filter | Options |
|---|---|
| Status | All / Expected / Checked In / On-Site / Checked Out / No Show |
| Visitor Type | All / Business Guest / Contractor / Delivery / etc. |
| Host | Search by employee name |
| Plant / Gate | Dropdown (if multi-plant/gate) |

**Visitor List (Main Area):**
Each row shows: Visitor Photo | Name | Company | Type Badge | Host | Check-In Time | Status Badge | Actions (Check-In / Check-Out / View)

**Quick Actions:**
- New Walk-In
- Scan QR
- Emergency Muster
- Export Today's Log

### 13.2 Visit Status Badges

| Status | Colour | Meaning |
|---|---|---|
| Expected | Blue | Pre-registered but not yet arrived |
| Arrived | Amber | At gate, check-in in progress |
| Checked In | Green | On-site, properly checked in |
| Checked Out | Grey | Visit completed, exited |
| No Show | Light Grey | Pre-registered but did not arrive |
| Overstaying | Red | Exceeded expected duration |
| Rejected | Red | Visit request denied |
| Cancelled | Light Grey | Pre-registration cancelled by host |

---

## 14. Visit History & Audit Trail

### 14.1 Visit History Screen

Searchable, filterable, exportable log of all visits.

**Filters:**
| Filter | Options |
|---|---|
| Date Range | Custom from/to date picker |
| Visitor Name | Text search |
| Visitor Company | Text search |
| Visitor Type | Dropdown |
| Host Employee | Search by name |
| Registration Method | Pre-Registered / QR Self-Reg / Walk-In |
| Status | Completed / No Show / Rejected / Cancelled |
| Plant / Gate | Dropdown |

### 14.2 Visit Record Detail View

Clicking any visit opens a complete detail view with these sections:

| Section | Fields |
|---|---|
| **Visitor Details** | Name, Company, Mobile, Email, Photo, ID Document |
| **Visit Details** | Date, Purpose, Visitor Type, Visit Code, Badge Number |
| **Host Details** | Host Employee Name, Department, Designation |
| **Timeline** | Pre-Registration → Invitation Sent → Arrival → Check-In → Check-Out (each with timestamp) |
| **Safety Compliance** | Induction Completed (Y/N, Score, Timestamp) · NDA Signed (Y/N, PDF link) · PPE Issued (items list) |
| **Approval Trail** | Who approved, when, from which channel |
| **Gate Details** | Check-In Gate, Check-Out Gate, Security Guard Name |
| **Vehicle Details** | Registration Number, Vehicle Type |
| **Material In/Out** | Items declared at entry and exit |
| **Visit Duration** | Calculated total duration |
| **Audit Log** | Every action on this record with user, timestamp, change details |

### 14.3 Audit Trail Events

Every action is permanently logged:

| Event | Data Captured |
|---|---|
| Visit Created | Created by, timestamp, method (Pre-Reg / Walk-In / QR) |
| Invitation Sent | Channel (Email/SMS/WhatsApp), timestamp |
| Pre-Arrival Form Completed | Timestamp, fields filled |
| Approval Requested | Sent to host name, timestamp |
| Approval Granted/Denied | By whom, timestamp, channel |
| Check-In Completed | Security guard, gate, timestamp |
| Badge Issued | Badge number, format (digital/printed) |
| Safety Induction Completed | Score, attempt count, timestamp |
| NDA Signed | Document version, e-signature timestamp |
| Check-Out Completed | Method, gate, timestamp |
| Badge Returned | Yes/No, timestamp |
| Record Modified | Field changed, old value → new value, changed by, timestamp |

---

## 15. Watchlist & Blocklist

### 15.1 Blocklist (Deny Entry)

Individuals permanently or temporarily denied entry to the facility.

| Field | Required | Notes |
|---|---|---|
| Person Name | Yes | |
| Mobile Number | No | For matching at check-in |
| Email | No | |
| ID Number (Aadhaar/PAN/DL) | No | For precise matching |
| Photo | No | For visual identification by guard |
| Reason for Blocking | Yes | Theft, Misconduct, Terminated Employee, Legal Order, Trespassing, etc. |
| Blocked By | Auto | User who added the entry |
| Block Date | Auto | |
| Block Duration | Yes | Permanent / Until [specific date] |
| Applies To | No | All Plants / Specific Plant(s) |

**System Behaviour:** When a visitor's name, mobile, or ID number matches a blocklisted entry during check-in:
1. **Red warning banner** displayed immediately to security guard
2. Check-in process is **blocked** — cannot proceed
3. Security Manager receives **instant alert** (Push + SMS + Email)
4. Incident logged in audit trail with timestamp and guard who attempted

### 15.2 Watchlist (Flag for Attention)

Individuals not blocked but requiring special attention or additional verification.

| Field | Notes |
|---|---|
| Person Name | |
| Matching Criteria | Name, Mobile, ID Number |
| Watch Reason | Former Employee, Pending Investigation, Vendor Dispute, Repeated Overstay, etc. |
| Action Required | Additional ID check / Security Manager approval / Escort mandatory |
| Added By | Auto |
| Expiry Date | When the watchlist entry expires |

**System Behaviour:** When a watchlisted visitor checks in:
1. **Yellow warning banner** displayed to security guard with watch reason and required action
2. Check-in **can proceed** but only after the required action is completed
3. Security Manager notified
4. Incident logged in audit trail

### 15.3 Watchlist/Blocklist Data Model

```
VisitorWatchlist {
  id              String    @id @default(cuid())
  companyId       String
  type            WatchlistType                // BLOCKLIST, WATCHLIST
  personName      String
  mobileNumber    String?
  email           String?
  idNumber        String?
  photo           String?                      // URL
  reason          String
  actionRequired  String?                      // For watchlist: what guard must do
  blockDuration   WatchlistDuration            // PERMANENT, UNTIL_DATE
  expiryDate      DateTime?
  appliesToAllPlants  Boolean  @default(true)
  plantIds        String[]                     // If not all plants
  createdBy       String                       // Employee ID
  isActive        Boolean    @default(true)
  createdAt       DateTime   @default(now())
  updatedAt       DateTime   @updatedAt
}

enum WatchlistType {
  BLOCKLIST
  WATCHLIST
}

enum WatchlistDuration {
  PERMANENT
  UNTIL_DATE
}
```

---

## 16. Multi-Gate & Multi-Plant Support

### 16.1 Gate Configuration

Each gate is a defined entry/exit point at a plant. Gates can have their own visitor types, operating hours, and QR poster URLs.

| Setting | Description |
|---|---|
| Gate Name | e.g., "Main Gate", "Factory Gate 2", "Loading Bay" |
| Gate Code | Unique code: `GATE-BLR-01` |
| Gate Type | Main Entry / Service Entry / Loading Dock / VIP Entry |
| Plant Assignment | Which plant this gate belongs to |
| Allowed Visitor Types | Which visitor types can enter through this gate |
| Operating Hours | Gate open/close timings |
| QR Poster URL | Unique self-registration URL for this gate |

### 16.2 Gate Data Model

```
VisitorGate {
  id              String    @id @default(cuid())
  companyId       String
  plantId         String                        // FK to Plant/Location
  name            String                        // "Main Gate"
  code            String                        // "GATE-BLR-01"
  type            GateType                      // MAIN, SERVICE, LOADING_DOCK, VIP
  openTime        String?                       // "06:00" (HH:mm)
  closeTime       String?                       // "22:00"
  allowedVisitorTypeIds  String[]               // Empty = all types allowed
  qrPosterUrl     String?                       // Auto-generated
  isActive        Boolean   @default(true)
  createdAt       DateTime  @default(now())
  updatedAt       DateTime  @updatedAt
}

enum GateType {
  MAIN
  SERVICE
  LOADING_DOCK
  VIP
}
```

### 16.3 Multi-Plant Features

| Feature | Description |
|---|---|
| Plant-Level Dashboard | Each plant has its own Today's Visitors dashboard |
| Unified Security View | Security Managers see all plants in a consolidated dashboard |
| Plant-Specific Safety Inductions | Different induction content per plant |
| Plant-Specific Watchlist | Blocklist entries can be global or plant-specific |
| Centralised Reporting | Company-wide visitor analytics across all plants |

---

## 17. Emergency Muster Management

In an emergency, every second counts. The system instantly generates a complete muster list of all visitors on-site.

### 17.1 Emergency Response Flow

```
Step 1: Emergency Triggered
    ↓  Manual trigger by authorized user (Security Guard, Security Manager, Company Admin)
    ↓  OR automated trigger from building alarm system (future)

Step 2: Instant Muster List Generated
    ↓  System queries all visitors with status "Checked In" (on-site)
    ↓  Muster list displayed on Security Dashboard immediately

Step 3: SMS Alerts Sent to All On-Site Visitors
    ↓  Emergency SMS: "Emergency Evacuation at [Facility]. Proceed to Assembly Point [X]. Reply OK when safe."
    ↓  SMS sent to every visitor's registered mobile number

Step 4: Marshal Accountability
    ↓  Security marshals use mobile app to mark each visitor:
    ↓  SAFE / MISSING / INJURED / EVACUATED

Step 5: Missing Visitor Escalation
    ↓  If any visitor not marked "Safe" within threshold time:
    ↓  Missing visitor alert with name, photo, host, last check-in gate
    ↓  Search & rescue team notified
```

### 17.2 Muster List Fields

| Field | Description |
|---|---|
| Visitor Name | |
| Visitor Photo | For identification |
| Visitor Company | |
| Host Employee | |
| Check-In Time | When they entered |
| Visitor Type | Badge colour for identification |
| Badge Number | |
| Check-In Gate | Which gate they entered from |
| SMS Sent Status | Delivered / Failed |
| Visitor Response | OK / No Response |
| Marshal Status | Safe / Missing / Injured / Evacuated |
| Marked By | Marshal name + timestamp |

### 17.3 Emergency Configuration

| Setting | Description |
|---|---|
| Emergency Trigger Access | Roles that can trigger: Security Guard, Security Manager, Company Admin |
| Assembly Points | Defined per plant/gate |
| SMS Template | Configurable emergency SMS text |
| Drill Mode | Run evacuation drill without sending real SMS — internal muster list only |
| Post-Evacuation Report | Auto-generated: total on-site, response rate, time to full accountability |

---

## 18. Contractor & Vendor Visit Management

Contractors and vendors are the most frequent and compliance-sensitive visitors in manufacturing.

### 18.1 Contractor-Specific Check-In Requirements

| Requirement | Description |
|---|---|
| Work Permit / PO Reference | Must have valid work permit or purchase order |
| Safety Induction (Mandatory) | Full safety induction with questionnaire — no bypass |
| Tool/Equipment Declaration | List of tools being brought in |
| Insurance / Licence Verification | Upload contractor's insurance certificate, trade licence |
| PPE Issuance (Mandatory) | Full PPE kit issued and acknowledged |
| NDA / Confidentiality Agreement | Mandatory for production area access |
| Escort Requirement | Configurable — escort required in restricted zones |
| Daily Re-Check-In | Multi-day contractors must check in each day |

### 18.2 Vendor Visit — Linked to Purchase Orders

When a vendor representative visits, the visit can optionally be linked to an active Purchase Order (PO):

```
Purchase Order (Vendor Management Module)
    → Pre-Registration created with PO reference
        → Check-In at gate (guard sees PO context)
            → If delivering goods → triggers Goods Receipt workflow (Inventory Module)
```

This provides context to the gate guard: *"This vendor is here for PO #12345 — expected delivery of 500 units of Part X."*

---

## 19. Group Visits

For situations where multiple visitors arrive together (factory tour, training, audit team, vendor delegation).

### 19.1 Group Visit Features

| Feature | Description |
|---|---|
| Group Pre-Registration | Host registers group with group name + attendee list (manual entry or CSV upload) |
| Group Visit Code | Single QR / visit code for the entire group |
| Batch Check-In | Security can check in all members at once or individually |
| Group Badge Printing | Batch print badges for all group members |
| Group Induction | Single induction session for the group (not per person) |
| Group Host | One host employee responsible for entire group |
| Group Check-Out | Batch check-out or individual check-out |
| Individual Member Tracking | Each group member has their own status (Expected / Checked In / Checked Out / No Show) and linked Visit record |

### 19.2 Group Visit Data Model

```
GroupVisit {
  id              String    @id @default(cuid())
  companyId       String
  groupName       String                        // "ABC Corp Audit Team"
  visitCode       String    @unique             // Group visit code
  qrCode          String?                       // QR code URL
  hostEmployeeId  String                        // FK to Employee
  purpose         String
  expectedDate    DateTime
  expectedTime    String?                       // HH:mm
  plantId         String                        // FK to Plant
  gateId          String?                       // FK to Gate
  totalMembers    Int
  status          GroupVisitStatus              // PLANNED, IN_PROGRESS, COMPLETED, CANCELLED
  createdBy       String
  createdAt       DateTime  @default(now())
  updatedAt       DateTime  @updatedAt
}

enum GroupVisitStatus {
  PLANNED
  IN_PROGRESS
  COMPLETED
  CANCELLED
}

GroupVisitMember {
  id              String    @id @default(cuid())
  groupVisitId    String                        // FK to GroupVisit
  visitorName     String
  visitorMobile   String
  visitorEmail    String?
  visitorCompany  String?
  visitId         String?   @unique             // FK to Visit — created when this member checks in
  status          GroupMemberStatus             // EXPECTED, CHECKED_IN, CHECKED_OUT, NO_SHOW
  createdAt       DateTime  @default(now())
  updatedAt       DateTime  @updatedAt
}

enum GroupMemberStatus {
  EXPECTED
  CHECKED_IN
  CHECKED_OUT
  NO_SHOW
}
```

---

## 20. Recurring Visitor Pass

For visitors who visit regularly (AMC technicians, vendor account managers, consultants). A recurring pass eliminates the need to create a new registration every time.

### 20.1 Recurring Pass Configuration

| Field | Required | Notes |
|---|---|---|
| Visitor Name | Yes | |
| Visitor Company | Yes | |
| Visitor Mobile | Yes | |
| Visitor Photo | Yes | Captured once, reused for all visits |
| Visitor ID Number | Yes | |
| Pass Type | Yes | Weekly / Monthly / Quarterly / Annual |
| Valid From | Yes | |
| Valid Until | Yes | |
| Allowed Days | No | e.g., Mon-Fri only, or specific days |
| Allowed Time Window | No | e.g., 9 AM - 6 PM |
| Allowed Gates | No | Specific gates or all |
| Host Employee | Yes | Default host for each visit |
| Purpose | Yes | |
| Safety Induction Status | Auto | Once completed, valid for pass duration |
| Pass Number | Auto | From Number Series |
| Status | Auto | Active / Expired / Revoked |

### 20.2 Recurring Pass Check-In Flow

```
Pass holder arrives at gate
    ↓
Scan pass QR code or enter pass number
    ↓
System validates: pass active + within valid dates + allowed day + allowed time + correct gate
    ↓
If valid → Quick check-in (no re-registration, no re-induction)
    ↓
Badge prints with "Recurring Pass" indicator
    ↓
Host notified
    ↓
If expired or revoked → Entry BLOCKED → Security alerted
```

**Important:** Every recurring pass check-in creates a **full Visit record** in the main Visit table with `recurringPassId` linked. This ensures:
- The visit appears in Today's Dashboard and real-time on-site count
- Overstay detection works normally
- Check-out is tracked in the standard Visit audit trail
- Reports include recurring pass visits alongside regular visits
- The Visit record inherits visitor details from the pass (no re-entry needed)

### 20.3 Recurring Pass Data Model

```
RecurringVisitorPass {
  id              String    @id @default(cuid())
  companyId       String
  passNumber      String    @unique             // From Number Series
  qrCode          String?

  // Visitor details (captured once)
  visitorName     String
  visitorCompany  String
  visitorMobile   String
  visitorEmail    String?
  visitorPhoto    String?                       // URL
  visitorIdType   String?
  visitorIdNumber String?

  // Pass configuration
  passType        RecurringPassType             // WEEKLY, MONTHLY, QUARTERLY, ANNUAL
  validFrom       DateTime
  validUntil      DateTime
  allowedDays     Int[]                         // 0=Sun, 1=Mon...6=Sat. Empty = all days
  allowedTimeFrom String?                       // "09:00"
  allowedTimeTo   String?                       // "18:00"
  allowedGateIds  String[]                      // Empty = all gates

  hostEmployeeId  String
  purpose         String
  plantId         String

  // Status
  status          RecurringPassStatus           // ACTIVE, EXPIRED, REVOKED
  revokedAt       DateTime?
  revokedBy       String?
  revokeReason    String?

  // Safety
  safetyInductionCompletedAt  DateTime?
  safetyInductionValidUntil   DateTime?

  createdBy       String
  createdAt       DateTime  @default(now())
  updatedAt       DateTime  @updatedAt
}

enum RecurringPassType {
  WEEKLY
  MONTHLY
  QUARTERLY
  ANNUAL
}

enum RecurringPassStatus {
  ACTIVE
  EXPIRED
  REVOKED
}
```

---

## 21. Vehicle & Material Gate Pass

### 21.1 Vehicle Gate Pass

For tracking vehicles entering/leaving the facility.

| Field | Required | Notes |
|---|---|---|
| Vehicle Registration Number | Yes | |
| Vehicle Type | Yes | Car, Two-Wheeler, Auto, Truck, Van, Tempo, Bus |
| Driver Name | Yes | |
| Driver Mobile | No | |
| Purpose | Yes | Delivery, Pick-Up, Visitor Vehicle, Contractor Vehicle |
| Associated Visit Record | No | Link to visitor's visit record |
| Material in Vehicle | No | Declaration of goods |
| Entry Time | Auto | |
| Exit Time | Auto | |
| Vehicle Photo | No | Captured at gate |
| Gate Pass Number | Auto | From Number Series |

### 21.2 Material Gate Pass

For tracking material entering or leaving the facility.

| Field | Required | Notes |
|---|---|---|
| Gate Pass Type | Yes | Inward (In) / Outward (Out) / Returnable |
| Material Description | Yes | What is being brought in or taken out |
| Quantity Issued | No | e.g., "10 units", "5 boxes" |
| Quantity Returned | No | For partial returns tracking |
| Associated Visit Record | No | Link to visitor |
| Authorized By | Yes | Employee who authorized the material movement |
| Purpose | Yes | Delivery, Repair, Replacement, Sample, Return, Personal |
| Expected Return Date | Conditional | For returnable gate passes |
| Return Status | Auto | Not Applicable / Pending / Partial / Fully Returned |
| Gate Pass Number | Auto | From Number Series |

### 21.3 Gate Pass Data Models

```
VehicleGatePass {
  id              String    @id @default(cuid())
  companyId       String
  passNumber      String    @unique             // From Number Series
  vehicleRegNumber String
  vehicleType     VehicleType
  driverName      String
  driverMobile    String?
  purpose         String
  visitId         String?                       // FK to Visit (optional link)
  materialDescription String?
  vehiclePhoto    String?                       // URL
  entryGateId     String
  exitGateId      String?
  entryTime       DateTime  @default(now())
  exitTime        DateTime?
  plantId         String
  createdBy       String
  createdAt       DateTime  @default(now())
  updatedAt       DateTime  @updatedAt
}

MaterialGatePass {
  id              String    @id @default(cuid())
  companyId       String
  passNumber      String    @unique             // From Number Series
  type            MaterialGatePassType          // INWARD, OUTWARD, RETURNABLE
  description     String
  quantityIssued  String?                       // e.g., "10 units", "5 boxes"
  quantityReturned String?                      // For partial returns: "7 of 10 units returned"
  visitId         String?                       // FK to Visit (optional link)
  authorizedBy    String                        // Employee ID
  purpose         String
  expectedReturnDate DateTime?                  // For returnable
  returnedAt      DateTime?
  returnStatus    MaterialReturnStatus @default(NOT_APPLICABLE)  // NOT_APPLICABLE, PENDING, PARTIAL, FULLY_RETURNED
  gateId          String
  plantId         String
  createdBy       String
  createdAt       DateTime  @default(now())
  updatedAt       DateTime  @updatedAt
}

enum VehicleType {
  CAR
  TWO_WHEELER
  AUTO
  TRUCK
  VAN
  TEMPO
  BUS
}

enum MaterialGatePassType {
  INWARD
  OUTWARD
  RETURNABLE
}

enum MaterialReturnStatus {
  NOT_APPLICABLE                              // Inward/Outward (non-returnable)
  PENDING                                     // Returnable but not yet returned
  PARTIAL                                     // Some items returned
  FULLY_RETURNED                              // All items returned
}
```

---

## 22. Reporting & Analytics

### 22.1 Standard Reports

| Report | Frequency | Audience | Description |
|---|---|---|---|
| Daily Visitor Log | Daily | Security Manager | All visitors for a specific date with full details |
| Weekly Visitor Summary | Weekly | Management | Total visitors, breakdown by type, top hosts, peak hours |
| Overstay Report | On-Demand | Security Manager | Visitors who exceeded expected duration |
| No-Show Report | On-Demand | Hosts, Admin | Pre-registered visitors who did not arrive |
| Watchlist/Blocklist Incident Report | On-Demand | Security Manager | Attempted entries by flagged individuals |
| Contractor Compliance Report | Monthly | Safety Officer | Induction completion, NDA status, PPE issuance |
| Gate-wise Traffic Report | Daily/Weekly | Security Manager | Visitor volume per gate |
| Plant-wise Visitor Report | Monthly | Plant Manager | Visitor volume per plant |
| Vehicle Gate Pass Report | On-Demand | Security Manager | All vehicle entries/exits |
| Material Gate Pass Report | On-Demand | Security, Stores | All material movements |
| Peak Hours Analysis | Monthly | Operations | Busiest times — for staffing optimization |

### 22.2 Analytics Dashboard KPIs

| KPI | Description |
|---|---|
| Total Visits (This Month) | Aggregate count |
| Avg. Daily Visitors | Running average |
| Avg. Visit Duration | Mean time on-site |
| Pre-Registered vs Walk-In % | Registration method split |
| Overstay Rate % | Visitors exceeding expected duration |
| Safety Induction Completion % | Compliance metric |

### 22.3 Analytics Charts

| Chart | Type |
|---|---|
| Visitor Volume Trend (30 days) | Line chart |
| Visitor Type Distribution | Pie/Donut chart |
| Peak Hours Heatmap | Heatmap (Day x Hour) |
| Top 10 Host Employees | Bar chart |
| Gate-wise Traffic | Stacked bar chart |

---

## 23. ERP Integrations

The Visitor Management module integrates with multiple Avy ERP modules:

| Module | Integration | Description |
|---|---|---|
| **HR Module** | Host Employee Lookup | VMS queries Employee Master for host verification, department, designation |
| **HR Module** | Contractor Attendance | Contractor check-in/out times fed into HR attendance for contract workforce tracking |
| **Vendor Management** | PO-Linked Visits | Vendor visits linked to Purchase Orders — gate guard sees PO context |
| **Inventory** | Goods Receipt | Delivery agent check-in with materials triggers GRN workflow |
| **Notification System** | Push/SMS/Email/WhatsApp | Leverages existing notification infrastructure for all VMS alerts |
| **Number Series** | Auto-Numbering | Visit IDs, badges, gate passes use tenant Number Series |
| **RBAC** | Permissions | VMS permissions integrated into existing `module:action` RBAC system |
| **Navigation Manifest** | Sidebar | VMS screens auto-appear in sidebar based on permissions + module subscription |

### 23.1 Module Dependencies

| Module Activated | Auto-Includes | Reason |
|---|---|---|
| Visitor Management | (none — standalone) | Can operate independently. HR integration enriches host lookup but is optional. |

---

## 24. Privacy, Compliance & Data Retention

### 24.1 Privacy Principles

| Principle | Implementation |
|---|---|
| **Consent** | Visitors consent to data collection at check-in (consent checkbox on form) |
| **Purpose Limitation** | Data collected only for security, safety, and operational purposes |
| **Data Minimisation** | Only necessary fields are mandatory; optional fields clearly marked |
| **Storage Security** | All visitor data encrypted at rest and in transit (TLS 1.3) |
| **Access Control** | RBAC enforced — only authorized roles can view records |
| **Right to Erasure** | Visitors can request deletion (subject to retention policy) |
| **Minor Visitor Consent** | Visitors under 18 require guardian/parent consent for photo capture and data collection. The system displays an age confirmation prompt during registration. If visitor indicates they are under 18, the system requires an accompanying adult's name and consent checkbox. This aligns with India's DPDPA 2023 and GDPR Article 8 requirements for processing children's data. |

### 24.2 Data Retention Policy

| Data Category | Default Retention | Configurable | Notes |
|---|---|---|---|
| Visit Records (metadata) | 3 years | Yes (1-7 years) | Visit ID, name, dates, host, purpose |
| Visitor Photos | 90 days | Yes (30 days - 1 year) | Photos captured at check-in |
| ID Document Photos | 30 days | Yes (7-90 days) | Sensitive — short retention |
| Signed NDAs | NDA duration + 1 year | Yes | Legal document |
| Safety Induction Logs | 3 years | Yes | Compliance evidence |
| Audit Trail | 7 years | No (fixed) | Regulatory requirement |
| Emergency Drill Records | 7 years | No (fixed) | Regulatory requirement |

### 24.3 Regulatory Compliance

| Regulation | How VMS Supports |
|---|---|
| **Factories Act (India)** | Digital visitor register; available for inspector review |
| **OSHA (US)** | Safety induction logs, PPE records, emergency accountability |
| **ISO 9001 / ISO 45001** | Document control (NDA versions), safety records, audit trails |
| **GDPR (EU)** | Consent capture, data minimisation, right to erasure |
| **IT Act (India)** | Secure storage of personal data, access logging |

---

## 25. VMS Configuration & System Settings

Company Admin configures VMS behaviour from the settings screen.

### 25.1 Global Settings

| Setting | Options | Default |
|---|---|---|
| Pre-Registration Enabled | ON / OFF | ON |
| QR Self-Registration Enabled | ON / OFF | ON |
| Walk-In Registration Allowed | ON / OFF | ON |
| Photo Capture Required | Always / Per Visitor Type / Never | Per Visitor Type |
| ID Verification Required | Always / Per Visitor Type / Never | Per Visitor Type |
| Safety Induction Required | Always / Per Visitor Type / Never | Per Visitor Type |
| NDA Required | Always / Per Visitor Type / Never | Per Visitor Type |
| Badge Printing Enabled | ON / OFF | ON |
| Digital Badge Enabled | ON / OFF | ON |
| Host Approval for Walk-Ins | ON / OFF | ON |
| Host Approval for QR Self-Reg | ON / OFF | ON |
| Approval Timeout (minutes) | Number | 15 |
| Overstay Alert Enabled | ON / OFF | ON |
| Default Max Visit Duration (hours) | Number | 8 |
| Auto Check-Out Enabled | ON / OFF | OFF |
| Auto Check-Out Time | Time | 20:00 |
| Vehicle Gate Pass Enabled | ON / OFF | ON |
| Material Gate Pass Enabled | ON / OFF | ON |
| Recurring Pass Enabled | ON / OFF | ON |
| Group Visit Enabled | ON / OFF | ON |
| Emergency Muster Enabled | ON / OFF | ON |
| Privacy Consent Text | Rich Text | Default template |
| Default Check-In Steps | Ordered List | ID → Photo → Induction → NDA → Badge |

### 25.2 VMS Settings Data Model

```
VisitorManagementConfig {
  id                    String    @id @default(cuid())
  companyId             String    @unique

  preRegistrationEnabled      Boolean @default(true)
  qrSelfRegistrationEnabled   Boolean @default(true)
  walkInAllowed               Boolean @default(true)

  photoCapture          ConfigRequirement @default(PER_VISITOR_TYPE)
  idVerification        ConfigRequirement @default(PER_VISITOR_TYPE)
  safetyInduction       ConfigRequirement @default(PER_VISITOR_TYPE)
  ndaRequired           ConfigRequirement @default(PER_VISITOR_TYPE)

  badgePrintingEnabled  Boolean @default(true)
  digitalBadgeEnabled   Boolean @default(true)

  walkInApprovalRequired       Boolean @default(true)
  qrSelfRegApprovalRequired    Boolean @default(true)
  approvalTimeoutMinutes       Int     @default(15)
  autoRejectAfterMinutes       Int     @default(30)

  overstayAlertEnabled         Boolean @default(true)
  defaultMaxDurationMinutes    Int     @default(480)
  autoCheckOutEnabled          Boolean @default(false)
  autoCheckOutTime             String  @default("20:00")

  vehicleGatePassEnabled       Boolean @default(true)
  materialGatePassEnabled      Boolean @default(true)
  recurringPassEnabled         Boolean @default(true)
  groupVisitEnabled            Boolean @default(true)
  emergencyMusterEnabled       Boolean @default(true)

  privacyConsentText           String?
  checkInStepsOrder            Json?   // ["ID_VERIFICATION", "PHOTO", "INDUCTION", "NDA", "BADGE"]

  createdAt             DateTime  @default(now())
  updatedAt             DateTime  @updatedAt
}

enum ConfigRequirement {
  ALWAYS
  PER_VISITOR_TYPE
  NEVER
}
```

---

## 26. Number Series Configuration

The following Number Series records should be created for VMS (using existing `generateNextNumber()` utility):

| Series | Linked Screen | Default Prefix | Digits | Example | Description |
|---|---|---|---|---|---|
| Visit ID | Visitor | `VIS-` | 6 | `VIS-000001` | Unique visit record identifier |
| Badge Number | Visitor Badge | `B-` | 5 | `B-00001` | Printed/digital badge serial |
| Recurring Pass | Recurring Visitor Pass | `RP-` | 4 | `RP-0001` | Recurring pass number |
| Vehicle Gate Pass | Vehicle Gate Pass | `VGP-` | 5 | `VGP-00001` | Vehicle entry/exit pass |
| Material Gate Pass | Material Gate Pass | `MGP-` | 5 | `MGP-00001` | Material in/out gate pass |
| Group Visit | Group Visit | `GV-` | 4 | `GV-0001` | Group visit batch number |

**Implementation:** Add these to `src/shared/constants/linked-screens.ts` and use `generateNextNumber()` in services. See CLAUDE.md "Adding Number Series to a New Screen" for the exact pattern.

---

## 27. Data Model — Complete Field Reference

> **Note:** The data models below are **reference models** intended to communicate intent, field requirements, and relationships. Final schema design may vary during implementation review — field names, types, indexes, and normalization decisions should be validated during sprint planning. These models are a starting point, not a locked specification.

### 27.1 Visit Record (Core Entity)

```
Visit {
  id                    String    @id @default(cuid())
  companyId             String
  visitNumber           String    @unique         // From Number Series: VIS-000001
  visitCode             String    @unique         // 6-char alphanumeric for gate check-in
  qrCodeUrl             String?                   // Generated QR code image URL

  // Visitor details
  visitorName           String
  visitorMobile         String
  visitorEmail          String?
  visitorCompany        String?
  visitorDesignation    String?
  visitorPhoto          String?                   // URL
  governmentIdType      String?                   // AADHAAR, PAN, DL, PASSPORT, VOTER_ID
  governmentIdNumber    String?
  idDocumentPhoto       String?                   // URL

  // Visit details
  visitorTypeId         String                    // FK to VisitorType
  purpose               VisitPurpose
  purposeNotes          String?
  expectedDate          DateTime
  expectedTime          String?                   // HH:mm
  expectedDurationMinutes Int?

  // Host & location
  hostEmployeeId        String                    // FK to Employee Master
  plantId               String                    // FK to Plant/Location
  gateId                String?                   // FK to VisitorGate

  // Registration
  registrationMethod    RegistrationMethod        // PRE_REGISTERED, QR_SELF_REG, WALK_IN

  // Approval
  approvalStatus        ApprovalStatus @default(PENDING)
  approvedBy            String?                   // Employee ID
  approvalTimestamp     DateTime?
  approvalNotes         String?

  // Check-in
  checkInTime           DateTime?
  checkInGateId         String?                   // FK to VisitorGate
  checkInGuardId        String?                   // Employee ID (security guard)

  // Badge
  badgeNumber           String?                   // From Number Series
  badgeFormat           BadgeFormat?              // DIGITAL, PRINTED

  // Safety & compliance
  safetyInductionStatus   InductionStatus @default(NOT_REQUIRED)
  safetyInductionScore    Int?
  safetyInductionTimestamp DateTime?
  ndaSigned               Boolean   @default(false)
  ndaDocumentUrl          String?
  ppeIssued               Json?                   // ["Helmet", "Goggles", "Safety Shoes"]

  // Check-out
  checkOutTime          DateTime?
  checkOutGateId        String?
  checkOutMethod        CheckOutMethod?
  badgeReturned         Boolean?
  materialOut           String?

  // Duration
  visitDurationMinutes  Int?                      // Calculated

  // Extension tracking
  originalDurationMinutes   Int?                      // Original expected duration (before any extensions)
  extensionCount            Int     @default(0)       // Number of times extended
  lastExtendedAt            DateTime?
  lastExtendedBy            String?                   // Employee ID

  // Status
  status                VisitStatus @default(EXPECTED)

  // Vehicle
  vehicleRegNumber      String?
  vehicleType           String?

  // Material
  materialCarriedIn     String?
  specialInstructions   String?
  emergencyContact      String?

  // Links
  groupVisitId          String?                   // FK to GroupVisit
  recurringPassId       String?                   // FK to RecurringVisitorPass
  purchaseOrderRef      String?                   // PO reference for vendor visits
  meetingRef            String?                   // Links multiple individual visits to same meeting/occasion

  // Audit
  createdBy             String
  createdAt             DateTime  @default(now())
  updatedBy             String?
  updatedAt             DateTime  @updatedAt
}

// Enums

enum VisitPurpose {
  MEETING
  DELIVERY
  MAINTENANCE
  AUDIT
  INTERVIEW
  SITE_TOUR
  PERSONAL
  OTHER
}

enum RegistrationMethod {
  PRE_REGISTERED
  QR_SELF_REG
  WALK_IN
}

enum ApprovalStatus {
  PENDING
  APPROVED
  REJECTED
  AUTO_APPROVED
}

enum VisitStatus {
  EXPECTED
  ARRIVED
  CHECKED_IN
  CHECKED_OUT
  NO_SHOW
  CANCELLED
  REJECTED
  AUTO_CHECKED_OUT
}

enum BadgeFormat {
  DIGITAL
  PRINTED
}

enum InductionStatus {
  NOT_REQUIRED
  PENDING
  COMPLETED
  FAILED
}

enum CheckOutMethod {
  SECURITY_DESK
  HOST_INITIATED
  MOBILE_LINK
  AUTO_CHECKOUT                               // Triggered by end-of-day auto-checkout or manual system checkout
}
```

---

## 28. API Endpoints Reference

> **Note:** The endpoints listed below are a **capability reference** intended to communicate scope and permission structure. Final API contract design (exact paths, request/response shapes, pagination) will be determined during sprint planning and implementation review. Developers should treat these as guidance, not gospel.

### 28.1 Visit Management

| Method | Endpoint | Description | Permission |
|---|---|---|---|
| POST | `/visitors/visits` | Create pre-registration | `visitors:create` |
| GET | `/visitors/visits` | List visits (with filters) | `visitors:read` |
| GET | `/visitors/visits/:id` | Get visit detail | `visitors:read` |
| PUT | `/visitors/visits/:id` | Update visit | `visitors:update` |
| DELETE | `/visitors/visits/:id` | Cancel visit | `visitors:delete` |
| POST | `/visitors/visits/:id/check-in` | Check in visitor | `visitors:create` |
| POST | `/visitors/visits/:id/check-out` | Check out visitor | `visitors:create` |
| POST | `/visitors/visits/:id/approve` | Approve visit | `visitors:approve` |
| POST | `/visitors/visits/:id/reject` | Reject visit | `visitors:approve` |
| POST | `/visitors/visits/:id/extend` | Extend visit duration | `visitors:update` |

### 28.2 Today's Dashboard

| Method | Endpoint | Description | Permission |
|---|---|---|---|
| GET | `/visitors/dashboard/today` | Today's visitor stats + list | `visitors:read` |
| GET | `/visitors/dashboard/on-site` | Currently on-site visitors | `visitors:read` |
| GET | `/visitors/dashboard/stats` | KPI stats (counts, averages) | `visitors:read` |

### 28.3 Self-Registration & Public Endpoints (No Auth)

| Method | Endpoint | Description | Auth |
|---|---|---|---|
| GET | `/public/visit/:visitCode` | Get visit details for pre-arrival form | None |
| POST | `/public/visit/:visitCode/pre-arrival` | Submit pre-arrival form | None |
| GET | `/public/visit/register/:plantCode` | Get self-registration form config | None |
| POST | `/public/visit/register/:plantCode` | Submit self-registration | None |
| GET | `/public/visit/:visitCode/status` | Check visit approval status | None |
| GET | `/public/visit/:visitCode/badge` | View digital badge | None |
| POST | `/public/visit/:visitCode/check-out` | Self check-out | None |

### 28.4 Visitor Types

| Method | Endpoint | Description | Permission |
|---|---|---|---|
| GET | `/visitors/types` | List visitor types | `visitors:read` |
| POST | `/visitors/types` | Create custom visitor type | `visitors:configure` |
| PUT | `/visitors/types/:id` | Update visitor type | `visitors:configure` |
| DELETE | `/visitors/types/:id` | Deactivate visitor type | `visitors:configure` |

### 28.5 Gates

| Method | Endpoint | Description | Permission |
|---|---|---|---|
| GET | `/visitors/gates` | List gates | `visitors:read` |
| POST | `/visitors/gates` | Create gate | `visitors:configure` |
| PUT | `/visitors/gates/:id` | Update gate | `visitors:configure` |
| DELETE | `/visitors/gates/:id` | Deactivate gate | `visitors:configure` |

### 28.6 Watchlist & Blocklist

| Method | Endpoint | Description | Permission |
|---|---|---|---|
| GET | `/visitors/watchlist` | List watchlist/blocklist entries | `visitors:read` |
| POST | `/visitors/watchlist` | Add entry | `visitors:configure` |
| PUT | `/visitors/watchlist/:id` | Update entry | `visitors:configure` |
| DELETE | `/visitors/watchlist/:id` | Remove entry | `visitors:configure` |
| POST | `/visitors/watchlist/check` | Check name/mobile/ID against lists | `visitors:read` |

### 28.7 Denied Entries

| Method | Endpoint | Description | Permission |
|---|---|---|---|
| GET | `/visitors/denied-entries` | List denied entries (with filters) | `visitors:read` |
| GET | `/visitors/denied-entries/:id` | Get denied entry detail | `visitors:read` |

### 28.8 Recurring Passes

| Method | Endpoint | Description | Permission |
|---|---|---|---|
| GET | `/visitors/recurring-passes` | List passes | `visitors:read` |
| POST | `/visitors/recurring-passes` | Create pass | `visitors:create` |
| PUT | `/visitors/recurring-passes/:id` | Update pass | `visitors:update` |
| POST | `/visitors/recurring-passes/:id/revoke` | Revoke pass | `visitors:delete` |
| POST | `/visitors/recurring-passes/:id/check-in` | Check in via pass | `visitors:create` |

### 28.9 Group Visits

| Method | Endpoint | Description | Permission |
|---|---|---|---|
| GET | `/visitors/group-visits` | List group visits | `visitors:read` |
| POST | `/visitors/group-visits` | Create group visit | `visitors:create` |
| PUT | `/visitors/group-visits/:id` | Update group visit | `visitors:update` |
| POST | `/visitors/group-visits/:id/batch-check-in` | Batch check in | `visitors:create` |
| POST | `/visitors/group-visits/:id/batch-check-out` | Batch check out | `visitors:create` |

### 28.10 Gate Passes

| Method | Endpoint | Description | Permission |
|---|---|---|---|
| GET | `/visitors/vehicle-passes` | List vehicle gate passes | `visitors:read` |
| POST | `/visitors/vehicle-passes` | Create vehicle gate pass | `visitors:create` |
| POST | `/visitors/vehicle-passes/:id/exit` | Record vehicle exit | `visitors:create` |
| GET | `/visitors/material-passes` | List material gate passes | `visitors:read` |
| POST | `/visitors/material-passes` | Create material gate pass | `visitors:create` |
| POST | `/visitors/material-passes/:id/return` | Mark material returned | `visitors:update` |

### 28.11 Safety Induction

| Method | Endpoint | Description | Permission |
|---|---|---|---|
| GET | `/visitors/safety-inductions` | List induction content | `visitors:read` |
| POST | `/visitors/safety-inductions` | Create induction | `visitors:configure` |
| PUT | `/visitors/safety-inductions/:id` | Update induction | `visitors:configure` |
| POST | `/visitors/visits/:id/complete-induction` | Record induction completion | `visitors:create` |

### 28.12 Emergency Muster

| Method | Endpoint | Description | Permission |
|---|---|---|---|
| POST | `/visitors/emergency/trigger` | Trigger emergency muster | `visitors:configure` |
| GET | `/visitors/emergency/muster-list` | Get current muster list | `visitors:read` |
| POST | `/visitors/emergency/mark-safe` | Mark visitor as safe | `visitors:create` |
| POST | `/visitors/emergency/resolve` | End emergency | `visitors:configure` |

### 28.13 Reports

| Method | Endpoint | Description | Permission |
|---|---|---|---|
| GET | `/visitors/reports/daily-log` | Daily visitor log | `visitors:export` |
| GET | `/visitors/reports/summary` | Weekly/monthly summary | `visitors:export` |
| GET | `/visitors/reports/overstay` | Overstay report | `visitors:export` |
| GET | `/visitors/reports/analytics` | Analytics dashboard data | `visitors:read` |

### 28.14 VMS Configuration

| Method | Endpoint | Description | Permission |
|---|---|---|---|
| GET | `/visitors/config` | Get VMS configuration | `visitors:read` |
| PUT | `/visitors/config` | Update VMS configuration | `visitors:configure` |

---

## 29. Screen Inventory — Web & Mobile

### 29.1 Company Admin Screens (Web)

| Screen | Route | Description |
|---|---|---|
| VMS Dashboard | `/visitors/dashboard` | Today's visitors + stats + quick actions |
| Visitor List | `/visitors/list` | Filterable list of all visits |
| Visitor Detail | `/visitors/:id` | Complete visit record with timeline + audit |
| Pre-Register Visitor | `/visitors/new` | Create new pre-registration |
| Gate Check-In | `/visitors/gate-check-in` | Gate operations screen (expected visitors + check-in form) |
| Visitor Types | `/visitors/settings/types` | Manage visitor type master |
| Gates | `/visitors/settings/gates` | Manage gates |
| Watchlist & Blocklist | `/visitors/watchlist` | Manage blocked/flagged visitors |
| Recurring Passes | `/visitors/recurring-passes` | Manage recurring passes |
| Group Visits | `/visitors/group-visits` | Manage group visits |
| Vehicle Gate Passes | `/visitors/vehicle-passes` | Vehicle entry/exit log |
| Material Gate Passes | `/visitors/material-passes` | Material in/out log |
| Safety Inductions | `/visitors/settings/inductions` | Manage induction content |
| VMS Settings | `/visitors/settings` | Global VMS configuration |
| Reports | `/visitors/reports` | VMS reports + analytics |
| Emergency Muster | `/visitors/emergency` | Emergency muster dashboard |
| Visit History | `/visitors/history` | Historical visits with audit trail |

### 29.2 Mobile App Screens

**Security Guard / Receptionist:**
| Screen | Description |
|---|---|
| Today's Visitors | Expected visitors for today + on-site count |
| Gate Check-In | QR scan + walk-in registration |
| Quick Check-Out | Scan badge or search visitor |
| Emergency Muster | Trigger evacuation + real-time muster list |
| On-Site Visitors | Live list of all currently on-site visitors |

**Host Employee:**
| Screen | Description |
|---|---|
| Pre-Register Visitor | Quick form to register expected visitor |
| My Visitors Today | Your expected + checked-in visitors |
| Approve/Reject | Notification with approve/reject actions |
| Check-Out My Visitor | Mark your visitor as checked out |

**Company Admin (in addition to above):**
| Screen | Description |
|---|---|
| VMS Dashboard | Full stats + analytics |
| Visitor Types Config | Manage types |
| Gate Config | Manage gates |
| Watchlist/Blocklist | Manage flagged visitors |
| VMS Settings | Configure all VMS settings |

### 29.3 Public Web Pages (No Auth — Visitor-Facing)

| Page | URL | Description |
|---|---|---|
| Pre-Arrival Form | `/visit/:visitCode` | Visitor fills details before arrival |
| Self-Registration | `/visit/register/:plantCode` | QR poster self-registration |
| Visit Status | `/visit/status/:visitCode` | Visitor checks approval status |
| Digital Badge | `/visit/badge/:visitCode` | Shows digital visitor badge |
| Self Check-Out | `/visit/checkout/:visitCode` | Self-service check-out |

---

## 30. Notification Templates

| Template ID | Event | Default Channel | Variables |
|---|---|---|---|
| `VMS_INVITATION` | Pre-registration confirmed → invite sent to visitor | Email + SMS + WhatsApp | `{visitorName}`, `{companyName}`, `{hostName}`, `{visitDate}`, `{visitTime}`, `{facilityAddress}`, `{qrCodeUrl}`, `{visitCode}`, `{preArrivalFormUrl}` |
| `VMS_HOST_ARRIVAL` | Visitor arrived at gate | Push + SMS | `{visitorName}`, `{visitorCompany}`, `{gate}`, `{time}` |
| `VMS_HOST_APPROVAL` | Walk-in/QR visitor needs approval | Push + SMS + Email | `{visitorName}`, `{visitorCompany}`, `{purpose}`, `{approveUrl}`, `{rejectUrl}` |
| `VMS_VISITOR_APPROVED` | Visit approved by host | SMS | `{visitorName}`, `{hostName}`, `{companyName}` |
| `VMS_VISITOR_REJECTED` | Visit rejected by host | SMS | `{visitorName}`, `{companyName}` |
| `VMS_HOST_CHECKED_IN` | Visitor checked in | Push + In-App | `{visitorName}`, `{gate}`, `{badgeNumber}` |
| `VMS_HOST_CHECKED_OUT` | Visitor checked out | In-App | `{visitorName}`, `{duration}` |
| `VMS_OVERSTAY` | Visitor overstaying | Push + SMS | `{visitorName}`, `{hostName}`, `{duration}`, `{expectedDuration}` |
| `VMS_EOD_UNCHECKED` | End-of-day: visitors still on-site | Email | `{visitorCount}`, `{visitorList}` |
| `VMS_BLOCKLIST_ALERT` | Blocklisted person attempted entry | Push + SMS + Email | `{personName}`, `{reason}`, `{gate}`, `{guard}` |
| `VMS_EMERGENCY` | Emergency evacuation triggered | SMS (to visitors) | `{companyName}`, `{assemblyPoint}` |
| `VMS_PASS_EXPIRY` | Recurring pass expiring soon | Email + In-App | `{visitorName}`, `{passNumber}`, `{expiryDate}` |
| `VMS_DIGITAL_BADGE` | Digital badge link sent to visitor | SMS + WhatsApp | `{visitorName}`, `{badgeUrl}` |

---

## 31. Permissions & RBAC

### 31.1 Permission Module

Add to `PERMISSION_MODULES` in `permissions.ts`:

```typescript
visitors: {
  label: 'Visitor Management',
  actions: ['read', 'create', 'update', 'delete', 'approve', 'export', 'configure'],
}
```

**Permission inheritance** (existing pattern):
`configure > approve > export > create = update = delete > read`

So `visitors:configure` grants all visitor permissions. `visitors:approve` grants read + create + update + delete + approve.

### 31.2 Navigation Manifest Entries

Add to `NAVIGATION_MANIFEST` in `navigation-manifest.ts`:

```typescript
// Visitor Management section
{ id: 'vms-dashboard', label: 'Visitors Dashboard', path: '/visitors/dashboard', icon: 'visitors', module: 'visitors', permission: 'visitors:read', section: 'Visitor Management' },
{ id: 'vms-gate-checkin', label: 'Gate Check-In', path: '/visitors/gate-check-in', icon: 'visitors', module: 'visitors', permission: 'visitors:create', section: 'Visitor Management' },
{ id: 'vms-visitor-list', label: 'All Visits', path: '/visitors/list', icon: 'visitors', module: 'visitors', permission: 'visitors:read', section: 'Visitor Management' },
{ id: 'vms-pre-register', label: 'Pre-Register Visitor', path: '/visitors/new', icon: 'visitors', module: 'visitors', permission: 'visitors:create', section: 'Visitor Management' },
{ id: 'vms-recurring-passes', label: 'Recurring Passes', path: '/visitors/recurring-passes', icon: 'visitors', module: 'visitors', permission: 'visitors:read', section: 'Visitor Management' },
{ id: 'vms-group-visits', label: 'Group Visits', path: '/visitors/group-visits', icon: 'visitors', module: 'visitors', permission: 'visitors:read', section: 'Visitor Management' },
{ id: 'vms-vehicle-passes', label: 'Vehicle Passes', path: '/visitors/vehicle-passes', icon: 'visitors', module: 'visitors', permission: 'visitors:read', section: 'Visitor Management' },
{ id: 'vms-material-passes', label: 'Material Passes', path: '/visitors/material-passes', icon: 'visitors', module: 'visitors', permission: 'visitors:read', section: 'Visitor Management' },
{ id: 'vms-watchlist', label: 'Watchlist & Blocklist', path: '/visitors/watchlist', icon: 'visitors', module: 'visitors', permission: 'visitors:configure', section: 'Visitor Management' },
{ id: 'vms-emergency', label: 'Emergency Muster', path: '/visitors/emergency', icon: 'visitors', module: 'visitors', permission: 'visitors:read', section: 'Visitor Management' },
{ id: 'vms-reports', label: 'Visitor Reports', path: '/visitors/reports', icon: 'visitors', module: 'visitors', permission: 'visitors:export', section: 'Visitor Management' },
{ id: 'vms-history', label: 'Visit History', path: '/visitors/history', icon: 'visitors', module: 'visitors', permission: 'visitors:read', section: 'Visitor Management' },
{ id: 'vms-settings', label: 'VMS Settings', path: '/visitors/settings', icon: 'visitors', module: 'visitors', permission: 'visitors:configure', section: 'Visitor Management' },
```

### 31.3 Reference Role Updates

Update reference roles in `permissions.ts`:

| Role | VMS Permission |
|---|---|
| Security Personnel | `visitors:*` (full access) |
| Security Guard | `visitors:create`, `visitors:read` |
| HR Manager | `visitors:read` |
| Employee (Host) | `visitors:create`, `visitors:read` (own visits only — filtered in service layer) |
| Company Admin | `visitors:configure` (full access via inheritance) |

---

## 32. Implementation Phases

### Phase 1: Core Visitor Management (MVP)
- Visitor Type Master (CRUD + defaults)
- Gate Master (CRUD)
- Pre-Registration with QR code + visit code generation
- Invitation sending (Email + SMS + WhatsApp via existing notification system)
- Walk-In Registration
- Gate Check-In screen (QR scan + visit code + walk-in)
- Identity verification (QR, code, ID scan)
- Host Notification & Approval workflow
- Visitor Badge (digital via SMS link)
- Check-Out (security desk + host-initiated + auto end-of-day)
- Today's Visitors Dashboard (stats + list + filters)
- Visit History & Audit Trail
- VMS Configuration screen
- Permissions & Navigation Manifest integration
- Number Series integration

### Phase 2: Security & Compliance
- Watchlist & Blocklist with real-time matching at check-in
- Safety Induction (video/slides/questionnaire)
- NDA / Document e-signing
- PPE issuance tracking
- Overstay detection & alerts
- Emergency Muster management (trigger + muster list + SMS + marshal marking)

### Phase 3: Advanced Features
- QR Self-Registration (poster at gate, web form, host approval)
- Pre-Arrival Form (public web page)
- Recurring Visitor Passes
- Group Visits (batch operations)
- Vehicle Gate Pass
- Material Gate Pass
- Reporting & Analytics dashboard
- Badge printing (physical printer integration)

### Phase 4: Integrations
- Vendor Management integration (PO-linked visits)
- Inventory integration (delivery → GRN workflow)
- HR Contractor Attendance integration
- Advanced analytics (peak hours heatmap, trend analysis)

---

## 33. Concurrency & Duplicate Check-In Prevention

Gate operations are high-throughput and multi-user. The system must prevent race conditions at the database level.

### 33.1 Duplicate Check-In Prevention

**Requirement:** A visit record in `CHECKED_IN` status cannot be checked in again. The system must return a clear error: *"This visitor is already checked in (checked in at [time] by [guard])."*

**Implementation:**
- The check-in operation must use an **atomic conditional update**: `UPDATE visit SET status = 'CHECKED_IN', checkInTime = NOW() WHERE id = :id AND status IN ('EXPECTED', 'ARRIVED') RETURNING *`. If zero rows are affected, the visit was already checked in (or in another non-eligible state).
- Alternatively, use Prisma's optimistic concurrency with a `version` field: `@@version` or manual `updatedAt` comparison.
- The `visitCode` lookup + status check + status update must happen in a **single database transaction** to prevent TOCTOU races.

### 33.2 Concurrent QR Scan Protection

If two guards at the same gate scan the same QR code simultaneously:
- The first request acquires the row lock and completes check-in
- The second request finds the visit already in `CHECKED_IN` status and returns: *"Already checked in at [gate] by [guard] at [time]."*

### 33.3 Concurrent Check-Out Protection

Same pattern as check-in: `UPDATE visit SET status = 'CHECKED_OUT' WHERE id = :id AND status = 'CHECKED_IN' RETURNING *`. If zero rows updated, the visitor was already checked out.

### 33.4 Visit Code Uniqueness

Visit codes are 6-character alphanumeric strings. The system must:
- Generate codes using a cryptographically random function (not sequential)
- Enforce `@@unique` constraint on `visitCode` in the database
- On the rare collision during generation, retry with a new code (max 3 retries)
- Visit codes are **single-use** — once a visit is completed/cancelled, the code cannot be reused for a different visit

---

## 34. Offline Mode Specification

Gate operations must work even when internet connectivity is intermittent — a common scenario at remote manufacturing plants.

### 34.1 Offline-Capable Operations

| Operation | Offline Behaviour |
|---|---|
| View Today's Expected Visitors | Cached from last sync. List may be stale. |
| Walk-In Check-In | Data stored locally on device; synced when online. Badge printed locally. |
| Pre-Registered Check-In (QR Scan) | Works if visit record was pre-cached. System caches all expected visits for today on device. |
| Check-Out | Recorded locally with timestamp; synced when online. |
| Badge Printing | Works offline — printer connected locally (USB/Bluetooth). |
| Photo Capture | Stored locally on device; uploaded on reconnect. |
| Emergency Muster List | Generated from locally cached on-site visitor data. |

### 34.2 Operations Requiring Connectivity

| Operation | Why |
|---|---|
| Host Notification / Approval | SMS/Push requires internet. **Fallback:** Guard calls host by phone and records verbal approval. |
| QR Self-Registration (visitor's phone) | Visitor's device needs internet to load the web form. |
| Watchlist / Blocklist Check | Cached list used offline; full check runs on reconnect. **Risk:** A newly added blocklist entry may not be on the device yet. |
| Real-Time Dashboard (web) | Requires internet. Dashboard shows "Last synced at [time]" warning. |
| Overstay Alerts | Calculated locally based on cached check-in times; notifications queued for delivery on reconnect. |
| Invitation Sending | Queued; sent on reconnect. |

### 34.3 Data Sync Behaviour

- All offline data is queued with **device-local timestamps** (not server time)
- On reconnection, data syncs in **chronological order** (oldest first)
- **Conflict resolution:** If a visit record was modified both offline and online (e.g., host approved online while guard checked in offline), the system applies **last-write-wins** with full audit trail logging both changes
- **Offline indicator:** Prominent banner shown on screen: "OFFLINE — data will sync when connected"
- **Last synced timestamp:** Displayed on every screen
- **Pre-cache strategy:** When online, the app automatically caches today's expected visitors, active watchlist/blocklist entries, and visitor type configuration for offline use

### 34.4 Offline Duration Limits

- If the device has been offline for **more than 24 hours**, the cached data is considered stale and the system shows a **warning banner**: "Data is more than 24 hours old. Some visitor records may be outdated."
- If offline for **more than 72 hours**, the system **blocks new check-ins** (except walk-ins) until connectivity is restored, to prevent operating on severely stale data

---

## 35. Visit Amendment & Extension Workflow

Visitors frequently need to extend their stay beyond the original expected duration. Without a formal extension mechanism, every legitimate extension generates false overstay alerts.

### 35.1 Extension Flow

```
Visit is active (status = CHECKED_IN)
    ↓
Host or Guard initiates extension request
    ↓
Guard can extend up to 2 hours without approval
    ↓
Extensions beyond 2 hours require Host Employee approval
    ↓
System updates expectedDurationMinutes on the Visit record
    ↓
Overstay timer resets based on new duration
    ↓
Extension logged in audit trail: "Visit extended by [X hours] by [user] at [time]. New expected check-out: [time]."
```

### 35.2 Extension Rules

| Rule | Description |
|---|---|
| Who can extend | Security Guard (up to 2 hours), Host Employee (unlimited), Security Manager (unlimited), Company Admin (unlimited) |
| Maximum extensions per visit | 3 (configurable in VMS Settings) |
| Maximum total duration | 24 hours (configurable — prevents indefinite extensions) |
| Extension logging | Every extension is a separate audit trail entry with old duration, new duration, reason, and approver |
| Notification | Host is notified when a guard extends. Security Manager notified if total duration exceeds default max. |

### 35.3 Extension API

| Method | Endpoint | Description | Permission |
|---|---|---|---|
| POST | `/visitors/visits/:id/extend` | Extend visit duration | `visitors:update` |

**Request body:** `{ additionalMinutes: number, reason: string }`

### 35.4 Visit Data Model Addition

Add to Visit model:
```
  // Extension tracking
  originalDurationMinutes   Int?                // Original expected duration (preserved for audit)
  extensionCount            Int     @default(0) // Number of times extended
  lastExtendedAt            DateTime?
  lastExtendedBy            String?             // Employee ID
```

---

## 36. Denied Entry & Failed Check-In Logging

Every denied entry — blocklist hit, host rejection, failed induction, gate closed, wrong date — must be recorded with full context. This is critical for audit readiness and security incident tracking.

### 36.1 Denied Entry Record

```
DeniedEntry {
  id              String    @id @default(cuid())
  companyId       String

  // Who was denied
  visitorName     String
  visitorMobile   String?
  visitorCompany  String?
  visitorPhoto    String?                       // If captured before denial

  // What happened
  denialReason    DenialReason
  denialDetails   String?                       // Free text with additional context
  visitId         String?                       // FK to Visit record (if one exists — e.g., pre-reg that was rejected)
  watchlistId     String?                       // FK to VisitorWatchlist (if blocklist/watchlist match)

  // Where and when
  gateId          String?                       // FK to VisitorGate
  plantId         String
  deniedAt        DateTime  @default(now())
  deniedBy        String                        // Employee ID (guard who processed)

  // Matching details (for blocklist/watchlist hits)
  matchedField    String?                       // "mobile", "name", "idNumber"
  matchedValue    String?                       // The value that matched

  createdAt       DateTime  @default(now())
}

enum DenialReason {
  BLOCKLIST_MATCH                              // Visitor matched blocklist entry
  HOST_REJECTED                                // Host declined the visit
  INDUCTION_FAILED                             // Failed safety induction after max retries
  GATE_CLOSED                                  // Arrived outside gate operating hours
  WRONG_DATE                                   // Pre-registered for a different date
  WRONG_GATE                                   // Visitor type not allowed at this gate
  PASS_EXPIRED                                 // Recurring pass expired or revoked
  APPROVAL_TIMEOUT                             // No host response within auto-reject timeout
  MANUAL_DENIAL                                // Guard manually denied for other reason
  VISIT_CANCELLED                              // Pre-registration was cancelled before arrival
}
```

### 36.2 Denied Entry API

| Method | Endpoint | Description | Permission |
|---|---|---|---|
| GET | `/visitors/denied-entries` | List denied entries (with filters) | `visitors:read` |
| GET | `/visitors/denied-entries/:id` | Get denied entry detail | `visitors:read` |

**Note:** Denied entries are **auto-created** by the system when a check-in is blocked. They are not manually created. The Watchlist/Blocklist Incident Report (Section 22.1) pulls data from this table.

---

## 37. Badge Lifecycle & Invalidation

### 37.1 Digital Badge Expiry

Digital badge URLs must have a defined lifecycle:

| Visit Status | Badge Behaviour |
|---|---|
| EXPECTED | Badge URL returns "Visit not yet started. Please check in at the gate." |
| CHECKED_IN | Badge URL shows active badge with all details + QR code for check-out |
| CHECKED_OUT | Badge URL shows "Visit Ended" message with visit summary (no sensitive details) |
| CANCELLED / REJECTED | Badge URL shows "This visit has been cancelled." |
| AUTO_CHECKED_OUT | Badge URL shows "Visit Ended (auto)" message |

### 37.2 Implementation

- Badge URLs include a **signed token** (HMAC or JWT) that encodes `visitId + expiryTimestamp`
- The badge page checks visit status on every load — no caching of active badge state
- Badge URLs do **not** expose the visit code or any data that could be used to re-check-in
- After check-out, the badge page shows only: visitor name, visit date, "Visit Complete" status. No host name, no QR code, no sensitive details.

### 37.3 Physical Badge

- Physical badges are collected at the gate during check-out
- The `badgeReturned` field on the Visit record tracks whether the badge was returned
- If a physical badge is not returned, the system flags it in the end-of-day report
- Badge numbers from unreturned badges are **not reused** — the Number Series continues incrementing

---

## 38. Badge Printer Integration Specification

### 38.1 Supported Printer Protocols

| Protocol | Printers | Use Case |
|---|---|---|
| **ZPL (Zebra Programming Language)** | Zebra GK420, ZD220, ZD620 | Industry standard for label printers in manufacturing. Recommended for production environments. |
| **Browser Print (window.print)** | Any printer | Fallback — works with any connected printer via browser print dialog. No special drivers needed. |
| **ESC/POS** | Epson, Star Micronics | Receipt-style printers. Suitable for temporary adhesive badges. |

### 38.2 Label Dimensions

| Badge Type | Dimensions | Printer |
|---|---|---|
| Standard Adhesive Label | 89mm x 51mm (3.5" x 2") | Zebra label printer |
| Name Badge Card | 86mm x 54mm (CR80 card size) | Card printer or pre-cut inserts |
| Browser Print | A6 (105mm x 148mm) | Any desktop printer |

### 38.3 Print Template Format

Badge templates are defined as **HTML/CSS templates** stored in VMS configuration. Variables are injected at print time:

```
{visitorName}, {visitorCompany}, {hostName}, {hostDepartment},
{visitorType}, {badgeColour}, {badgeNumber}, {visitDate},
{validUntil}, {qrCodeDataUrl}, {companyLogo}, {emergencyContact}
```

For ZPL printers, the system generates ZPL commands server-side from the HTML template data.

### 38.4 Print Trigger

| Trigger | Description |
|---|---|
| **Auto-print on check-in** | When check-in completes, the system sends a print job to the gate's assigned printer. Triggered from the **client browser** (for browser print) or **server** (for ZPL via network printer). |
| **Manual reprint** | Guard can reprint a badge from the visit detail screen. Reprint is logged in audit trail. |
| **Batch print (group visits)** | All group member badges printed sequentially. |

### 38.5 Printer Offline Handling

If the badge printer is offline at the time of check-in:
1. Check-in **still completes** — badge printing is not a blocker
2. Digital badge is sent to the visitor's phone as fallback
3. Guard sees a warning: "Badge printer offline. Digital badge sent to visitor."
4. Print job is queued; prints automatically when the printer comes back online
5. Guard can manually trigger reprint later from the visit detail screen

---

## 39. Error States & Edge Cases

This section documents non-happy-path scenarios that must be handled by the system.

### 39.1 Host Employee Edge Cases

| Scenario | System Behaviour |
|---|---|
| **Host is on leave** | System checks host's leave status. If on approved leave, shows warning to guard: "Host [Name] is currently on leave. Contact alternate: [Manager Name]." Approval request is automatically escalated to host's reporting manager. |
| **Host has left the company** | If host employee status is "Inactive" or "Terminated", pre-registration is blocked: "This employee is no longer active. Please select a different host." For existing pre-registrations, the system flags them in the dashboard: "Host no longer active — reassign required." |
| **Host not found in Employee Master** | QR self-registration allows free-text host name. If no exact match: show top 3 suggestions. If still no match: "We couldn't find this employee. Please contact reception at [phone]." |

### 39.2 Visit Timing Edge Cases

| Scenario | System Behaviour |
|---|---|
| **Visitor arrives on wrong date** | If a pre-registered visitor's QR is scanned on a different date: "This visit is scheduled for [date]. Would you like to check in anyway?" Guard can override. The visit record is updated with the actual date and flagged "Date Override" in audit trail. |
| **Visitor arrives before gate opens** | If visitor scans QR outside gate operating hours: "Gate [Name] is closed. Operating hours: [open] - [close]." Denied entry logged. Guard can manually override if authorized. |
| **Visitor arrives after expected time** | System allows check-in but shows: "Visitor was expected at [time], arriving [X hours] late." Logged in audit trail. |
| **Pre-registration expired (> 7 days old)** | Pre-registrations older than 7 days without check-in are auto-marked "NO_SHOW". If visitor arrives with an expired code: "This visit registration has expired. Please ask your host to create a new registration." |

### 39.3 Technical Failure Edge Cases

| Scenario | System Behaviour |
|---|---|
| **Safety induction video fails to load** | Show "Safety induction content could not be loaded." Offer fallback: text-based safety declaration that the visitor reads and signs. Log the content delivery failure. Do not block check-in. |
| **Badge printer offline** | See Section 38.5 — check-in proceeds, digital badge sent, print job queued. |
| **SMS/notification delivery fails** | Check-in proceeds. Failed notification is retried 3 times with exponential backoff. If all retries fail, the failure is logged and shown to the guard: "Host notification failed — please inform the host manually." |
| **QR code unreadable** | Guard falls back to Visit Code manual entry (Section 7.4). If visit code is also unavailable, guard searches by visitor name/mobile. |
| **Database connection lost mid-check-in** | If the check-in transaction fails, the system rolls back and shows: "Check-in failed. Please try again." No partial state is persisted. |

### 39.4 Security Edge Cases

| Scenario | System Behaviour |
|---|---|
| **Same visitor checks in at two different gates simultaneously** | Prevented by concurrent check-in protection (Section 33). Second attempt returns error. |
| **Visitor tries to use someone else's QR code** | Guard must visually verify visitor identity against photo on file. If mismatch, guard denies entry. System cannot detect identity fraud programmatically without biometric verification (future feature). |
| **Visitor refuses to comply with safety induction** | Guard marks induction as "REFUSED". Check-in is blocked. Denied entry record created with reason "INDUCTION_FAILED". Host and Security Manager notified. |

---

## Appendix A: Glossary

| Term | Definition |
|---|---|
| **Visit Code** | 6-character alphanumeric code (e.g., `A3B7K2`) generated for each visit. Used as fallback when QR scan fails. |
| **QR Code** | Machine-readable code encoding the visit URL. Printed in invitation and displayed at gate for scanning. |
| **QR Poster** | Physical poster at facility entrance with a QR code. Visitors scan it to self-register (no app needed). |
| **Pre-Registration** | Host creates a visit in advance. Visitor receives invitation with QR code. |
| **Walk-In** | Unannounced visitor. Security captures details manually at gate. |
| **QR Self-Registration** | Visitor scans QR poster, fills web form, awaits host approval. |
| **Digital Badge** | Visitor badge displayed on phone via SMS/WhatsApp link. Contains QR code for check-out. |
| **Muster List** | Emergency list of all visitors currently on-site. Used for evacuation accountability. |
| **Overstay** | When a visitor remains on-site beyond their expected visit duration. |
| **Recurring Pass** | Pre-approved pass for regular visitors (AMC technicians, vendors). Allows quick check-in without re-registration. |
| **Gate Pass** | Permit for vehicles or materials entering/leaving the facility. |
| **Watchlist** | Flagged individuals requiring extra verification at check-in (not blocked). |
| **Blocklist** | Individuals denied entry. System blocks check-in automatically. |

---

## Appendix B: Key Numbers

| Metric | Value |
|---|---|
| Registration Paths | 3 (Pre-registration, QR self-service, Walk-in) |
| Check-Out Methods | 4 (Security desk, host-initiated, mobile link, auto end-of-day) |
| Default Visitor Types | 9 (configurable + custom types) |
| ERP Integrations | 6 (HR, Vendor, Inventory, Notifications, Number Series, RBAC) |
| API Endpoints | ~50 |
| Web Screens | ~17 |
| Mobile Screens | ~10 |
| Number Series | 6 (Visit, Badge, Recurring Pass, Vehicle Pass, Material Pass, Group Visit) |
| Implementation Phases | 4 |
| Edge Cases Documented | 15+ scenarios across host, timing, technical, and security categories |
| Paper Logbooks | 0 — eliminated from day one |
