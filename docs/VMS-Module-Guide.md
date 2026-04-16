# Avy ERP -- Visitor Management System (VMS) Module Guide

> **Document:** VMS-Module-Guide  
> **Version:** 1.0  
> **Date:** April 2026  
> **Audience:** Developers, QA Engineers, Product Managers, Security Administrators  
> **PRD Reference:** `docs/Avy_ERP_Visitor_Management_Module_v2_PRD.md`

---

## 1. Module Overview

### 1.1 What VMS Does

The Visitor Management System (VMS) is a security-grade module that digitises the complete visitor lifecycle for manufacturing and industrial environments. It replaces paper logbooks with a tamper-proof digital audit trail covering every person who enters a facility -- from pre-registration through identity verification, safety induction, real-time on-site tracking, and check-out.

**Tagline:** *"Every person who enters is identified, informed, and accounted for."*

### 1.2 Key Capabilities

| Capability | Description |
|---|---|
| **3 Registration Methods** | Pre-registration, QR self-registration, walk-in |
| **Gate Check-In** | QR scan, visit code entry, watchlist/blocklist screening |
| **Identity Verification** | Government ID capture (Aadhaar, PAN, DL, Passport, Voter ID) |
| **Safety Induction** | Video, slides, questionnaire, or declaration -- per visitor type |
| **Host Approval** | Push/SMS notification to host with approve/reject |
| **Real-Time Tracking** | Dashboard showing all on-site visitors with overstay alerts |
| **4 Check-Out Methods** | Security desk, host-initiated, mobile link (self), auto end-of-day |
| **Watchlist & Blocklist** | Instant matching at check-in with denial logging |
| **Emergency Muster** | One-tap evacuation trigger with full muster list and SMS |
| **Recurring Passes** | Weekly/monthly/quarterly/annual passes for regular visitors |
| **Group Visits** | Batch check-in/check-out for delegations up to 100 people |
| **Vehicle Gate Passes** | Entry/exit logging for all 7 vehicle types |
| **Material Gate Passes** | Inward/outward/returnable tracking with return status |
| **Reports & Analytics** | Daily log, summary, overstay report, KPI analytics |

### 1.3 How It Fits in the ERP Ecosystem

```
                     +-----------------+
                     |   Navigation    |
                     |   Manifest      |
                     |   (Sidebar)     |
                     +--------+--------+
                              |
         +--------------------+--------------------+
         |                    |                    |
   +-----v-----+      +------v------+      +------v------+
   |    RBAC    |      |  HR Module  |      | Notification|
   | visitors:* |      |  Employee   |      |   Service   |
   | 7 actions  |      |  Master     |      |  13 events  |
   +-----+------+      +------+------+      +------+------+
         |                    |                    |
         +--------------------+--------------------+
                              |
                     +--------v--------+
                     |   VMS Module    |
                     |  15 Prisma      |
                     |  Models         |
                     |  55+ Endpoints  |
                     +--------+--------+
                              |
              +---------------+---------------+
              |               |               |
       +------v------+ +-----v------+ +------v------+
       | Number Series| | Approval   | | Public API  |
       | 7 linked    | | Workflow   | | (No Auth)   |
       | screens     | | Integration| | 6 endpoints |
       +-------------+ +------------+ +-------------+
```

**Integration points:**

- **HR Module** -- Host employee lookup via the Employee Master. Every visit requires a `hostEmployeeId` referencing an employee record.
- **RBAC** -- Permission module `visitors` with 7 actions. The navigation manifest defines 16 sidebar entries.
- **Notifications** -- Dispatches events like `VMS_PRE_REGISTRATION_CREATED`, `VMS_VISITOR_CHECKED_IN`, `VMS_VISITOR_CHECKED_OUT`, and `VMS_EMERGENCY_EVACUATION`.
- **Number Series** -- 7 linked screens for auto-generated reference numbers (visit numbers, badge numbers, pass numbers).
- **Approval Workflows** -- `VISITOR_WALK_IN_APPROVAL` and `VISITOR_SELF_REG_APPROVAL` trigger events.

---

## 2. Getting Started

### 2.1 Prerequisites

Before VMS can be used, the following must be in place:

| Requirement | Where | How to Verify |
|---|---|---|
| **Visitor module subscription** | Module Management | Company must have the `visitor` module active on at least one location |
| **Permissions assigned** | RBAC / Role Management | Users need `visitors:read` (minimum) or `visitors:configure` (full access) |
| **At least one plant/location** | Company Admin > Locations | `GET /company/locations` returns active locations |
| **At least one employee** | HR > Employees | Needed for host employee selection |
| **Number series configured** | Company Admin > Number Series | 7 VMS series must be set up |

### 2.2 Initial Setup Checklist

Complete these steps in order after subscribing to the VMS module:

**Step 1: Configure Number Series**

Navigate to **Company Admin > Number Series Config** and configure these 7 series:

| Linked Screen | Default Prefix | Example Output |
|---|---|---|
| Visitor Registration | `VIS-` | `VIS-00001` |
| Visitor Badge | `B-` | `B-00001` |
| Gate Pass | `GP-` | `GP-00001` |
| Recurring Visitor Pass | `RP-` | `RP-00001` |
| Vehicle Gate Pass | `VGP-` | `VGP-00001` |
| Material Gate Pass | `MGP-` | `MGP-00001` |
| Group Visit | `GV-` | `GV-00001` |

These number series are mandatory. If not configured, the system will throw: `"Number series not configured for [screen]. Please configure it in Number Series Config."`.

**Step 2: Review Default Visitor Types**

When the first visitor type is created, the system auto-seeds 9 default types:

| Name | Code | Badge Colour | Safety Induction | NDA | Host Approval | Max Duration |
|---|---|---|---|---|---|---|
| Business Guest | BG | #3B82F6 (blue) | No | No | Yes | 8 hours |
| Vendor / Supplier | VN | #22C55E (green) | No | No | Yes | 8 hours |
| Contractor | CT | #F97316 (orange) | Yes | Yes | Yes | 8 hours |
| Delivery Agent | DA | #EAB308 (yellow) | No | No | No | 2 hours |
| Government Inspector | GI | #EF4444 (red) | No | No | Yes | 8 hours |
| Job Candidate | JC | #A855F7 (purple) | No | No | Yes | 8 hours |
| Personal Visitor | FV | #F5F5F5 (light) | No | No | Yes | 8 hours |
| VIP / Board Member | VP | #F59E0B (amber) | No | No | No | 8 hours |
| Auditor | AU | #1F2937 (dark) | No | No | Yes | 8 hours |

Navigate to **VMS Settings > Visitor Types** to review and customise these.

**Step 3: Set Up Gates**

Navigate to **VMS Settings > Gates** and create at least one gate for each plant. Each gate gets an auto-generated QR poster URL at `https://app.avyerp.com/visit/register/{gateCode}`.

**Step 4: Configure Safety Inductions (Optional)**

If any visitor types require safety induction, create induction content under **VMS Settings > Safety Inductions**.

**Step 5: Review VMS Settings**

Navigate to **VMS Settings** and review the 21+ configuration toggles. Key defaults:

- Pre-registration: Enabled
- QR self-registration: Enabled
- Walk-in: Enabled (with approval required)
- Approval timeout: 15 minutes
- Auto-reject after: 30 minutes
- Auto check-out: Disabled (default time 20:00 if enabled)

### 2.3 First Visit Walkthrough

1. A host employee opens **Pre-Register Visitor** and fills in visitor details
2. The system generates a 6-character visit code (e.g., `A3HK9W`) and a visit number (e.g., `VIS-00001`)
3. A notification is sent to the host confirming the registration
4. When the visitor arrives, the security guard opens **Gate Check-In**, scans the QR or enters the visit code
5. The system verifies the visit, checks watchlist/blocklist, captures ID, and issues a badge
6. The visitor is now checked in and appears on the **Visitors Dashboard** under "On-Site"
7. When leaving, the guard checks the visitor out from the security desk
8. The visit is logged with full duration and audit trail

---

## 3. Complete Visitor Lifecycle

### 3.1 Pre-Registration Flow

**Actors:** Host Employee, Visitor (passive recipient)

**Step-by-step:**

1. **Host creates visit**: Fills in the pre-registration form with:
   - Visitor name, mobile, email, company, designation (visitor details)
   - Visitor type (from dropdown of active types)
   - Purpose (MEETING, DELIVERY, MAINTENANCE, AUDIT, INTERVIEW, SITE_TOUR, PERSONAL, OTHER)
   - Expected date, time, duration
   - Host employee (auto-filled or selected)
   - Plant and gate assignment
   - Optional: vehicle info, material carried, special instructions

2. **System generates codes**: A cryptographically random 6-character visit code is generated (excludes ambiguous characters I, O, 0, 1 for readability). A visit number is generated via the number series.

3. **Watchlist check**: Before creation, the system checks the visitor's mobile number and name against the watchlist/blocklist. If blocklisted, creation is denied with an error.

4. **Approval determination**: Based on the visitor type's `requireHostApproval` flag:
   - If `true` --> `approvalStatus = PENDING`, host receives approval notification
   - If `false` --> `approvalStatus = AUTO_APPROVED`

5. **Notification dispatched**: The system dispatches `VMS_PRE_REGISTRATION_CREATED` to the host employee with tokens: `{visitorName, visitorCompany, visitDate, visitCode}`.

6. **Visitor receives invitation**: Via the notification system (Email + SMS + WhatsApp), the visitor receives the visit code and (optionally) a QR code URL and pre-arrival form link.

**API call:**

```
POST /visitors/visits
Permission: visitors:create
Body: {
  visitorName, visitorMobile, visitorEmail?, visitorCompany?,
  visitorDesignation?, visitorTypeId, purpose, purposeNotes?,
  expectedDate, expectedTime?, expectedDurationMinutes?,
  hostEmployeeId, plantId, gateId?, vehicleRegNumber?,
  vehicleType?, materialCarriedIn?, specialInstructions?,
  emergencyContact?, meetingRef?, purchaseOrderRef?
}
Response: { success: true, data: Visit }
```

### 3.2 QR Self-Registration Flow

**Actors:** Visitor (at gate), Host Employee (approver)

**Step-by-step:**

1. **Visitor scans QR poster**: Each gate has a QR poster URL: `https://app.avyerp.com/visit/register/{gateCode}`. The visitor scans this with their phone.

2. **Public form loads**: The system returns the self-registration form configuration (no authentication required):
   - Company name and logo
   - Plant name
   - Available visitor types
   - Whether photo is required

3. **Visitor fills form**: Name, mobile, company (optional), purpose, and the name of the host employee they are visiting.

4. **Host employee lookup**: The system performs a fuzzy search on the employee name provided by the visitor. The best match is used as the host. If no match is found, the visitor is told to contact reception.

5. **Visit created**: The system creates a visit with `registrationMethod = PRE_REGISTERED` (reuses the same create flow). If the default visitor type is not specified, it falls back to the "Business Guest" (code `BG`) type.

6. **Host approval required**: The host receives a push notification to approve or reject.

7. **Visitor waits**: The visitor can check their visit status at `GET /public/visit/{visitCode}/status`.

**Public endpoints (no auth):**

```
GET  /public/visit/register/{plantCode}     -- Get form config
POST /public/visit/register/{plantCode}     -- Submit registration
GET  /public/visit/{visitCode}/status       -- Check approval status
```

### 3.3 Walk-In Flow

**Actors:** Security Guard, Host Employee (approver)

**Step-by-step:**

1. **Guard captures details**: The security guard opens the Gate Check-In screen and fills in visitor details manually (name, mobile, company, purpose, host employee).

2. **System creates visit**: A visit record is created with `registrationMethod = WALK_IN`.

3. **Host approval**: If `walkInApprovalRequired` is enabled in VMS config (default: `true`), the host receives an approval notification. The guard waits for approval.

4. **Approval timeout**: If the host does not respond within `approvalTimeoutMinutes` (default: 15), a reminder is sent. After `autoRejectAfterMinutes` (default: 30), the visit is auto-rejected.

5. **On approval**: The guard proceeds with safety induction (if required), badge issuance, and check-in.

### 3.4 Gate Check-In Process

**Actors:** Security Guard

The gate check-in process follows these steps, configurable per visitor type:

```
Visitor Arrives at Gate
        |
        v
  +-----------+
  | Identify  |  (QR scan, visit code entry, or walk-in form)
  +-----------+
        |
        v
  +-----------+
  | Watchlist  |  (Automatic check against blocklist/watchlist)
  | Check      |  If blocklisted: DENIED + DeniedEntry created
  +-----------+  If watchlisted: WARNING shown, guard decides
        |
        v
  +-----------+
  | Approval   |  (If requireHostApproval = true and status = PENDING)
  | Wait       |  Guard waits for host to approve/reject
  +-----------+
        |
        v
  +-----------+
  | ID Check   |  (If requireIdVerification = true)
  | & Photo    |  (If requirePhoto = true)
  +-----------+  Captures governmentIdType, governmentIdNumber, photos
        |
        v
  +-----------+
  | Safety     |  (If requireSafetyInduction = true)
  | Induction  |  Video/slides/questionnaire/declaration
  +-----------+  Passing score check (default 80%)
        |         Validity period: skip if completed within validityDays
        v
  +-----------+
  | NDA        |  (If requireNda = true)
  | Signing    |
  +-----------+
        |
        v
  +-----------+
  | Badge      |  Badge number generated via number series
  | Issuance   |  Format: DIGITAL or PRINTED
  +-----------+
        |
        v
  +-----------+
  | CHECK-IN   |  Status changes to CHECKED_IN
  | Complete   |  checkInTime, checkInGateId, checkInGuardId recorded
  +-----------+
        |
        v
  Host notification sent (VMS_VISITOR_CHECKED_IN)
```

**QR Scan Flow:**

1. Guard scans QR code on visitor's phone/printout
2. System looks up visit by `visitCode`
3. If found and status is `EXPECTED` or `ARRIVED`, proceed with check-in steps

**Visit Code Entry Flow:**

1. Guard manually types the 6-character visit code
2. Same lookup and validation as QR scan

**Watchlist/Blocklist Checking:**

The system checks the visitor's mobile number against `VisitorWatchlist` records:
- **Blocklist match**: Check-in is denied immediately. A `DeniedEntry` record is created with `denialReason = BLOCKLIST_MATCH`. If detected mid-check-in, the visit is reverted to `CANCELLED`.
- **Watchlist match**: A warning is shown to the guard with the reason. The guard can choose to proceed or deny entry.

**Atomic Check-In (Concurrency Safety):**

The check-in uses raw SQL with a conditional UPDATE to prevent duplicate check-ins:

```sql
UPDATE visits
SET status = 'CHECKED_IN', "checkInTime" = NOW(), ...
WHERE id = ? AND "companyId" = ? AND status IN ('EXPECTED', 'ARRIVED')
```

If `updated === 0`, the system checks why:
- Visit not found --> 404
- Already checked in --> 409 Conflict (with check-in timestamp)
- Invalid status --> 400 Bad Request

**API call:**

```
POST /visitors/visits/:id/check-in
Permission: visitors:create
Body: {
  checkInGateId,           -- Required: gate where check-in happens
  checkInGuardId?,         -- Guard employee ID
  visitorPhoto?,           -- Photo URL captured during check-in
  governmentIdType?,       -- AADHAAR | PAN | DRIVING_LICENCE | PASSPORT | VOTER_ID
  governmentIdNumber?,     -- ID number
  idDocumentPhoto?,        -- Photo URL of ID document
  badgeFormat?             -- DIGITAL | PRINTED
}
```

### 3.5 On-Site Tracking

Once checked in, visitors appear on the real-time dashboard.

**Dashboard Stats** (`GET /visitors/dashboard/today`):

| Metric | Description |
|---|---|
| `totalExpected` | All visits expected today |
| `checkedIn` | Visitors who checked in today |
| `checkedOut` | Visitors who checked out today |
| `onSiteNow` | Currently checked-in visitors (any date) |
| `walkIns` | Walk-in registrations today |
| `noShows` | Expected visitors who did not arrive |
| `overstaying` | Checked-in visitors past their expected duration |

**On-Site Visitors** (`GET /visitors/dashboard/on-site`):

Returns all visitors with `status = CHECKED_IN`, ordered by check-in time descending, including visitor type and check-in gate information.

**Overstay Detection:**

The system calculates overstay by comparing:
- `checkInTime + expectedDurationMinutes` against the current time
- If `now > checkInTime + expectedDurationMinutes`, the visitor is flagged as overstaying

Overstay alerts are dispatched via `VMS_OVERSTAY` notification to the host employee.

**Visit Extension** (`POST /visitors/visits/:id/extend`):

| Constraint | Value |
|---|---|
| Maximum extensions per visit | 3 |
| Minimum extension | 15 minutes |
| Maximum total duration | 24 hours (1440 minutes) |
| Can only extend | While `status = CHECKED_IN` |

The system tracks `originalDurationMinutes`, `extensionCount`, `lastExtendedAt`, and `lastExtendedBy`.

**Monthly KPI Stats** (`GET /visitors/dashboard/stats`):

Returns aggregated statistics for the current month:
- `totalVisitsThisMonth`, `avgDailyVisitors`
- `avgVisitDurationMinutes`
- `preRegisteredPercent`, `walkInPercent`
- `overstayRate` (percentage of completed visits that exceeded expected duration)
- `safetyInductionCompletionRate`

### 3.6 Check-Out Process

Four methods are supported, tracked in the `checkOutMethod` field:

**1. Security Desk Check-Out (`SECURITY_DESK`)**

The guard checks the visitor out from the Gate Check-In screen:

```
POST /visitors/visits/:id/check-out
Permission: visitors:create
Body: {
  checkOutGateId?,        -- Gate where check-out happens
  checkOutMethod,         -- 'SECURITY_DESK'
  badgeReturned?,         -- Boolean: was the badge collected?
  materialOut?            -- Description of material leaving with visitor
}
```

**2. Host-Initiated Check-Out (`HOST_INITIATED`)**

The host employee can check out their visitor from the visit detail screen:

```
POST /visitors/visits/:id/check-out
Body: { checkOutMethod: 'HOST_INITIATED' }
```

**3. Mobile Link Check-Out (`MOBILE_LINK`)**

The visitor receives a check-out link via SMS. They tap it to self-check-out. This is a public endpoint:

```
POST /public/visit/:visitCode/check-out
No authentication required
```

**4. Auto End-of-Day Check-Out (`AUTO_CHECKOUT`)**

If `autoCheckOutEnabled = true` in VMS config, all remaining checked-in visitors are automatically checked out at `autoCheckOutTime` (default: `20:00`). Status changes to `AUTO_CHECKED_OUT`.

**Atomic Check-Out (Concurrency Safety):**

Similar to check-in, check-out uses raw SQL:

```sql
UPDATE visits
SET status = 'CHECKED_OUT', "checkOutTime" = NOW(), ...
WHERE id = ? AND "companyId" = ? AND status = 'CHECKED_IN'
```

After check-out, the system calculates `visitDurationMinutes`:

```
visitDurationMinutes = round((checkOutTime - checkInTime) / 60000)
```

Host notification `VMS_VISITOR_CHECKED_OUT` is dispatched with `{visitorName, duration}`.

---

## 4. Configuration Guide

### 4.1 Visitor Types

**Endpoint:** `GET/POST/PUT/DELETE /visitors/types`  
**Permission:** `visitors:read` (list/view), `visitors:configure` (create/update/deactivate)

Each visitor type controls the check-in step requirements for visitors of that type.

**Fields:**

| Field | Type | Description |
|---|---|---|
| `name` | string (max 100) | Display name (e.g., "Business Guest") |
| `code` | string (max 5, uppercase) | Unique code within company (e.g., "BG") |
| `badgeColour` | hex string | Badge colour for visual identification (e.g., "#3B82F6") |
| `requirePhoto` | boolean | Require visitor photo at check-in |
| `requireIdVerification` | boolean | Require government ID at check-in |
| `requireSafetyInduction` | boolean | Require safety induction before check-in |
| `requireNda` | boolean | Require NDA signing |
| `requireHostApproval` | boolean | Require host approval before check-in |
| `requireEscort` | boolean | Require escort during visit |
| `defaultMaxDurationMinutes` | int (15-1440) | Default visit duration for this type |
| `safetyInductionId` | string? | Link to specific SafetyInduction content |
| `sortOrder` | int | Display order in lists |
| `isDefault` | boolean | System-seeded type (cannot be deactivated) |
| `isActive` | boolean | Soft-delete flag |

**Custom Type Creation Example:**

```json
POST /visitors/types
{
  "name": "External Auditor",
  "code": "EA",
  "badgeColour": "#DC2626",
  "requirePhoto": true,
  "requireIdVerification": true,
  "requireSafetyInduction": true,
  "requireNda": true,
  "requireHostApproval": true,
  "requireEscort": true,
  "defaultMaxDurationMinutes": 480,
  "safetyInductionId": "clu1234...",
  "sortOrder": 10
}
```

### 4.2 Gates

**Endpoint:** `GET/POST/PUT/DELETE /visitors/gates`  
**Permission:** `visitors:read` (list/view), `visitors:configure` (create/update/deactivate)

Gates represent physical entry/exit points at a plant. Each gate is tied to a specific plant (location).

**Fields:**

| Field | Type | Description |
|---|---|---|
| `plantId` | string | Location this gate belongs to |
| `name` | string (max 100) | Display name (e.g., "Main Gate") |
| `code` | string (max 20) | Unique code within company |
| `type` | GateType enum | `MAIN`, `SERVICE`, `LOADING_DOCK`, `VIP` |
| `openTime` | string? (HH:mm) | Gate opening time |
| `closeTime` | string? (HH:mm) | Gate closing time |
| `allowedVisitorTypeIds` | string[] | Restrict which visitor types can use this gate |
| `qrPosterUrl` | string (auto) | Auto-generated: `https://app.avyerp.com/visit/register/{code}` |
| `isActive` | boolean | Soft-delete flag |

**QR Poster URL:**

When a gate is created, the system auto-generates a QR poster URL. This URL points to a public web form where visitors can self-register. Print this URL as a QR code on a poster displayed at the gate.

**Gate Operating Hours:**

If `openTime` and `closeTime` are set, visitors attempting to check in outside these hours will be denied entry with `denialReason = GATE_CLOSED`.

### 4.3 Safety Inductions

**Endpoint:** `GET/POST/PUT/DELETE /visitors/safety-inductions`  
**Permission:** `visitors:read` (list/view), `visitors:configure` (create/update/deactivate)

Safety inductions ensure visitors understand facility safety rules before entering.

**Types:**

| Type | How It Works |
|---|---|
| `VIDEO` | Visitor watches a video. `contentUrl` points to the video file. `durationSeconds` sets minimum watch time. |
| `SLIDES` | Visitor views a slide deck. `contentUrl` points to the slide content. |
| `QUESTIONNAIRE` | Visitor answers multiple-choice questions. `questions` is a JSON array. `passingScore` determines pass/fail (default 80%). |
| `DECLARATION` | Visitor reads and acknowledges safety rules. Simple accept/decline. |

**Questionnaire Format:**

```json
{
  "questions": [
    {
      "question": "What should you do in case of a fire alarm?",
      "options": ["Continue working", "Evacuate to assembly point", "Call your manager", "Wait for instructions"],
      "correctAnswer": 1
    },
    {
      "question": "PPE required in the production area includes:",
      "options": ["Safety shoes only", "Hard hat and safety shoes", "No PPE required", "Gloves only"],
      "correctAnswer": 1
    }
  ],
  "passingScore": 80,
  "durationSeconds": 300
}
```

**Validity Period:**

The `validityDays` field (default: 30, max: 365) determines how long a completed induction remains valid. If a repeat visitor has completed the same induction within the validity period, they skip re-induction. The system checks `safetyInductionTimestamp` on previous visits.

**Completing Induction:**

```
POST /visitors/visits/:id/complete-induction
Permission: visitors:create
Body: { score?: number, passed: boolean }
```

This updates `safetyInductionStatus` to `COMPLETED` or `FAILED`, records the score, and timestamps the completion.

### 4.4 VMS Settings

**Endpoint:** `GET/PUT /visitors/config`  
**Permission:** `visitors:read` (view), `visitors:configure` (update)

The `VisitorManagementConfig` model holds all global VMS settings for a company. A default config is auto-created on first access.

**All Configuration Fields:**

| Field | Type | Default | Description |
|---|---|---|---|
| **Registration Methods** | | | |
| `preRegistrationEnabled` | boolean | `true` | Allow hosts to pre-register visitors |
| `qrSelfRegistrationEnabled` | boolean | `true` | Allow visitors to self-register via QR poster |
| `walkInAllowed` | boolean | `true` | Allow walk-in visitors |
| **Check-In Requirements** | | | |
| `photoCapture` | ConfigRequirement | `PER_VISITOR_TYPE` | `ALWAYS` / `PER_VISITOR_TYPE` / `NEVER` |
| `idVerification` | ConfigRequirement | `PER_VISITOR_TYPE` | `ALWAYS` / `PER_VISITOR_TYPE` / `NEVER` |
| `safetyInduction` | ConfigRequirement | `PER_VISITOR_TYPE` | `ALWAYS` / `PER_VISITOR_TYPE` / `NEVER` |
| `ndaRequired` | ConfigRequirement | `PER_VISITOR_TYPE` | `ALWAYS` / `PER_VISITOR_TYPE` / `NEVER` |
| **Badge Settings** | | | |
| `badgePrintingEnabled` | boolean | `true` | Enable physical badge printing |
| `digitalBadgeEnabled` | boolean | `true` | Enable digital badge via SMS link |
| **Approval Settings** | | | |
| `walkInApprovalRequired` | boolean | `true` | Require host approval for walk-ins |
| `qrSelfRegApprovalRequired` | boolean | `true` | Require host approval for QR self-registrations |
| `approvalTimeoutMinutes` | int | `15` | Minutes before approval reminder is sent |
| `autoRejectAfterMinutes` | int | `30` | Minutes before pending visit is auto-rejected |
| **Duration & Overstay** | | | |
| `overstayAlertEnabled` | boolean | `true` | Send alerts when visitors overstay |
| `defaultMaxDurationMinutes` | int | `480` | Default max visit duration (8 hours) |
| `autoCheckOutEnabled` | boolean | `false` | Auto check-out remaining visitors at end of day |
| `autoCheckOutTime` | string (HH:mm) | `"20:00"` | Time for auto check-out |
| **Feature Toggles** | | | |
| `vehicleGatePassEnabled` | boolean | `true` | Enable vehicle gate pass feature |
| `materialGatePassEnabled` | boolean | `true` | Enable material gate pass feature |
| `recurringPassEnabled` | boolean | `true` | Enable recurring visitor passes |
| `groupVisitEnabled` | boolean | `true` | Enable group visit management |
| `emergencyMusterEnabled` | boolean | `true` | Enable emergency muster feature |
| **Other** | | | |
| `privacyConsentText` | string? | `null` | Custom privacy consent text shown during registration |
| `checkInStepsOrder` | JSON? | `null` | Custom ordering of check-in steps |

**ConfigRequirement Enum:**

The `ConfigRequirement` enum allows three levels of control:
- `ALWAYS` -- Enforced for all visitors regardless of type
- `PER_VISITOR_TYPE` -- Determined by the visitor type's individual settings
- `NEVER` -- Disabled for all visitors

---

## 5. Security Features

### 5.1 Watchlist & Blocklist

**Endpoint:** `GET/POST/PUT/DELETE /visitors/watchlist`  
**Permission:** `visitors:read` (list/view/check), `visitors:configure` (create/update/delete)

The watchlist system provides two levels of screening:

| Type | Behaviour |
|---|---|
| `BLOCKLIST` | **Hard block.** Entry is denied immediately. A `DeniedEntry` record is auto-created. The visit is cancelled if already in progress. |
| `WATCHLIST` | **Soft alert.** A warning is shown to the guard with the reason and recommended action. The guard decides whether to proceed. |

**Watchlist Entry Fields:**

| Field | Type | Description |
|---|---|---|
| `type` | `BLOCKLIST` or `WATCHLIST` | Alert severity |
| `personName` | string | Person's name |
| `mobileNumber` | string? | Mobile number for matching |
| `email` | string? | Email for matching |
| `idNumber` | string? | Government ID for matching |
| `photo` | string? | Photo URL for visual identification |
| `reason` | string | Why this person is listed |
| `actionRequired` | string? | Instructions for security if matched |
| `blockDuration` | `PERMANENT` or `UNTIL_DATE` | Duration of the listing |
| `expiryDate` | DateTime? | Expiry date (if `UNTIL_DATE`) |
| `appliesToAllPlants` | boolean | Apply to all locations or specific ones |
| `plantIds` | string[] | Specific plant IDs (if not all) |

**Matching Algorithm:**

The system matches on:
1. **Mobile number** -- Exact match against `mobileNumber`
2. **Government ID number** -- Exact match against `idNumber`
3. **Name** -- Case-insensitive contains match against `personName` (for manual check endpoint only)

Expired `UNTIL_DATE` entries are automatically excluded from matching.

**Check Endpoint:**

```
POST /visitors/watchlist/check
Permission: visitors:read
Body: { name?: string, mobile?: string, idNumber?: string }
Response: {
  blocklisted: boolean,
  watchlisted: boolean,
  matches: WatchlistEntry[]
}
```

**When Matching Occurs:**

1. **Pre-registration** -- `visitService.createVisit()` calls `checkWatchlistBlocklist()` before creating the visit
2. **Check-in** -- `visitService.checkIn()` calls `checkWatchlistBlocklistSafe()` after the atomic status update. If a blocklist match is found post-check-in, the visit is reverted to `CANCELLED` and a denied entry is created.

### 5.2 Denied Entry Logging

**Endpoint:** `GET /visitors/denied-entries`  
**Permission:** `visitors:read`

Every denied entry is automatically logged. This is a read-only audit trail -- denied entries cannot be manually created, edited, or deleted.

**Denial Reasons (DenialReason enum):**

| Reason | When It Occurs |
|---|---|
| `BLOCKLIST_MATCH` | Visitor matched a blocklist entry |
| `HOST_REJECTED` | Host employee rejected the visit |
| `INDUCTION_FAILED` | Visitor failed the safety induction questionnaire |
| `GATE_CLOSED` | Attempted check-in outside gate operating hours |
| `WRONG_DATE` | Visitor arrived on a different date than expected |
| `WRONG_GATE` | Visitor arrived at a gate not assigned to their visit |
| `PASS_EXPIRED` | Recurring pass has expired |
| `APPROVAL_TIMEOUT` | Host did not respond within the timeout period |
| `MANUAL_DENIAL` | Guard manually denied entry |
| `VISIT_CANCELLED` | The visit was cancelled before arrival |

**DeniedEntry Fields:**

| Field | Description |
|---|---|
| `visitorName` | Name of the denied person |
| `visitorMobile` | Mobile number |
| `visitorCompany` | Company name |
| `visitorPhoto` | Photo if captured |
| `denialReason` | One of the 10 denial reasons |
| `denialDetails` | Free-text notes |
| `visitId` | Link to visit record (if applicable) |
| `watchlistId` | Link to watchlist entry (if blocklist match) |
| `gateId` | Gate where denial occurred |
| `plantId` | Plant location |
| `deniedBy` | Employee who denied entry |
| `deniedAt` | Timestamp of denial |
| `matchedField` | Which field triggered the match (e.g., "mobileNumber") |
| `matchedValue` | The matched value |

**List with Filters:**

```
GET /visitors/denied-entries?denialReason=BLOCKLIST_MATCH&fromDate=2026-04-01&toDate=2026-04-13&page=1&limit=20
```

---

## 6. Advanced Features

### 6.1 Recurring Visitor Passes

**Endpoint:** `GET/POST/PUT /visitors/recurring-passes`, `POST /:id/revoke`, `POST /:id/check-in`  
**Permission:** `visitors:read` (list/view), `visitors:create` (create/check-in), `visitors:update` (update), `visitors:delete` (revoke)

Recurring passes are for visitors who visit regularly (e.g., contractor who comes every Monday/Wednesday).

**Pass Types:**

| Type | Typical Use |
|---|---|
| `WEEKLY` | Weekly contractor visits |
| `MONTHLY` | Monthly audit visits |
| `QUARTERLY` | Quarterly vendor meetings |
| `ANNUAL` | Full-year access for regular suppliers |

**Key Fields:**

| Field | Description |
|---|---|
| `passNumber` | Auto-generated via number series (e.g., `RP-00001`) |
| `validFrom` / `validUntil` | Validity period |
| `allowedDays` | Array of allowed day numbers (0=Sun, 1=Mon, ..., 6=Sat) |
| `allowedTimeFrom` / `allowedTimeTo` | Allowed entry time window (HH:mm) |
| `allowedGateIds` | Restrict to specific gates |
| `status` | `ACTIVE`, `EXPIRED`, `REVOKED` |

**Check-In via Pass:**

When a recurring pass holder arrives, the guard uses the pass check-in endpoint. The system validates:
1. Pass is `ACTIVE`
2. Current date is within `validFrom`-`validUntil`
3. Current day of the week is in `allowedDays` (if configured)
4. Check-in gate is in `allowedGateIds` (if configured)

A full `Visit` record is created and linked to the pass via `recurringPassId`. The visit is auto-approved.

```
POST /visitors/recurring-passes/:id/check-in
Permission: visitors:create
Body: { checkInGateId: string }
```

**Revocation:**

```
POST /visitors/recurring-passes/:id/revoke
Permission: visitors:delete
Body: { reason: string }
```

### 6.2 Group Visits

**Endpoint:** `GET/POST/PUT /visitors/group-visits`, `POST /:id/batch-check-in`, `POST /:id/batch-check-out`  
**Permission:** `visitors:read` (list/view), `visitors:create` (create/batch-check-in/batch-check-out), `visitors:update` (update)

Group visits handle delegations, tour groups, or training batches.

**Creating a Group Visit:**

```json
POST /visitors/group-visits
{
  "groupName": "Q2 Board Meeting Delegation",
  "hostEmployeeId": "emp_123",
  "purpose": "Quarterly board meeting and facility tour",
  "expectedDate": "2026-04-15",
  "expectedTime": "09:00",
  "plantId": "plant_123",
  "gateId": "gate_456",
  "members": [
    { "visitorName": "John Smith", "visitorMobile": "9876543210", "visitorCompany": "Acme Corp" },
    { "visitorName": "Jane Doe", "visitorMobile": "9876543211", "visitorCompany": "Acme Corp" }
  ]
}
```

**Constraints:**
- Minimum 2 members, maximum 100
- Group visit code is prefixed with `G-` (e.g., `G-A3HK9W`)

**Statuses:**
- `PLANNED` --> Initial state
- `IN_PROGRESS` --> At least one member checked in
- `COMPLETED` --> All members checked out or marked no-show
- `CANCELLED` --> Group visit cancelled

**Batch Check-In:**

```
POST /visitors/group-visits/:id/batch-check-in
Body: { memberIds: ["member_1", "member_2"], checkInGateId: "gate_123" }
```

For each member, the system creates an individual `Visit` record (with visit number and badge number via number series) and links it to the group via `groupVisitId`.

**Batch Check-Out:**

```
POST /visitors/group-visits/:id/batch-check-out
Body: { memberIds?: ["member_1"], checkOutGateId?: "gate_123", checkOutMethod: "SECURITY_DESK" }
```

If `memberIds` is omitted, all checked-in members are checked out. When all members are done (checked out or no-show), the group status changes to `COMPLETED`.

### 6.3 Vehicle Gate Passes

**Endpoint:** `GET/POST /visitors/vehicle-passes`, `POST /:id/exit`  
**Permission:** `visitors:read` (list/view), `visitors:create` (create/exit)

Vehicle gate passes track vehicles entering and leaving the facility.

**Vehicle Types:**

`CAR`, `TWO_WHEELER`, `AUTO`, `TRUCK`, `VAN`, `TEMPO`, `BUS`

**Creating a Pass:**

```json
POST /visitors/vehicle-passes
{
  "vehicleRegNumber": "KA-01-AB-1234",
  "vehicleType": "TRUCK",
  "driverName": "Ravi Kumar",
  "driverMobile": "9876543210",
  "purpose": "Raw material delivery",
  "visitId": "visit_123",
  "materialDescription": "100 kg steel rods",
  "entryGateId": "gate_loading_dock",
  "plantId": "plant_123"
}
```

**Recording Exit:**

```
POST /visitors/vehicle-passes/:id/exit
Body: { exitGateId: "gate_456" }
```

This records `exitTime` and links the exit gate. A vehicle that has already exited returns a 409 Conflict.

### 6.4 Material Gate Passes

**Endpoint:** `GET/POST /visitors/material-passes`, `POST /:id/return`  
**Permission:** `visitors:read` (list/view), `visitors:create` (create), `visitors:update` (mark returned)

Material gate passes track physical items entering or leaving the facility.

**Pass Types:**

| Type | Description |
|---|---|
| `INWARD` | Material coming into the facility |
| `OUTWARD` | Material leaving the facility |
| `RETURNABLE` | Material leaving temporarily, expected to return |

**Return Status:**

| Status | Description |
|---|---|
| `NOT_APPLICABLE` | Non-returnable pass (INWARD or OUTWARD) |
| `PENDING_RETURN` | Returnable pass awaiting return |
| `PARTIAL` | Some quantity returned |
| `FULLY_RETURNED` | All material returned |

**Marking Return:**

```
POST /visitors/material-passes/:id/return
Body: { quantityReturned: "50 kg steel rods", returnStatus: "PARTIAL" }
```

When `returnStatus = FULLY_RETURNED`, the system records `returnedAt` timestamp.

### 6.5 Emergency Muster Management

**Endpoint:** `POST /visitors/emergency/trigger`, `GET /muster-list`, `POST /mark-safe`, `POST /resolve`  
**Permission:** `visitors:configure` (trigger/resolve), `visitors:read` (muster list), `visitors:create` (mark safe)

Emergency muster provides immediate accountability during evacuations.

**Triggering Emergency:**

```
POST /visitors/emergency/trigger
Body: { plantId: "plant_123", isDrill: false }
```

This:
1. Fetches all on-site visitors (status = `CHECKED_IN`) for the specified plant
2. If not a drill, dispatches `VMS_EMERGENCY_EVACUATION` SMS to all on-site visitors
3. Returns the complete muster list with visitor details, badge numbers, host info, and check-in locations

**Muster List:**

```
GET /visitors/emergency/muster-list?plantId=plant_123
```

Returns each on-site visitor with:
- `visitorName`, `visitorCompany`, `visitorPhoto`
- `visitorType`, `badgeColour`, `badgeNumber`
- `hostEmployeeId`, `checkInTime`, `checkInGate`
- `visitorMobile` (for direct contact)

**Marking Visitors Safe:**

```
POST /visitors/emergency/mark-safe
Body: { visitIds: ["visit_1", "visit_2"], plantId: "plant_123" }
```

This logs the marked-safe event (including who marked them and when) for audit purposes.

**Resolving Emergency:**

```
POST /visitors/emergency/resolve
Body: { plantId: "plant_123" }
```

Logs the resolution timestamp and who resolved it.

---

## 7. HR Module Integration

### 7.1 Host Employee Lookup

Every visit requires a `hostEmployeeId` referencing an employee in the Employee Master. The frontend provides an employee search/picker that queries:

```
GET /hr/employees?search=John&status=ACTIVE,PROBATION,CONFIRMED
```

The visit record stores `hostEmployeeId` but does NOT duplicate employee details. The host name and department are resolved at display time by joining with the Employee model.

### 7.2 How VMS Uses Employee Data

| VMS Context | Employee Data Used |
|---|---|
| Pre-registration form | Employee name (as host), department, designation |
| Host approval notification | Employee push token, mobile, email |
| Dashboard "Host" column | Employee firstName + lastName |
| QR self-registration | Fuzzy name match to find host employee |
| Emergency muster | Host employee info linked to each visitor |

### 7.3 Contractor Attendance Tracking

Contractors (visitor type `CT`) with recurring passes can have their attendance tracked through the VMS check-in/check-out system. Each check-in creates a `Visit` record with timestamps that can be cross-referenced with HR attendance data.

### 7.4 Approval Workflow Integration

VMS integrates with the ESS approval engine for two trigger events:

| Trigger Event | When Used |
|---|---|
| `VISITOR_WALK_IN_APPROVAL` | Walk-in visitor requires host approval |
| `VISITOR_SELF_REG_APPROVAL` | QR self-registered visitor requires host approval |

These are defined in `src/shared/constants/trigger-events.ts` and can be configured in the Approval Workflow Config screen to define multi-step approval chains.

---

## 8. RBAC & Permissions

### 8.1 Permission Module

The VMS uses the `visitors` permission module with 7 actions:

```typescript
// From permissions.ts
visitors: {
  label: 'Visitor Management',
  actions: ['read', 'create', 'update', 'delete', 'approve', 'export', 'configure'],
}
```

**Permission Inheritance:**

```
configure > approve > export > create = update = delete > read
```

This means:
- `visitors:configure` grants all 7 actions
- `visitors:approve` grants `approve` + `export` + `create` + `update` + `delete` + `read`
- `visitors:export` grants `export` + `create` + `update` + `delete` + `read`
- `visitors:create` grants `create` + `read`

**Module Subscription Mapping:**

```typescript
// From permissions.ts
'visitor': ['visitors']   // The 'visitor' subscription module maps to 'visitors' permission module
```

If the company does not have the `visitor` module subscribed, all `visitors:*` permissions are automatically suppressed.

### 8.2 Role-Permission Mapping

| Reference Role | VMS Permissions | Typical Use |
|---|---|---|
| Security Personnel | `visitors:*` (full) | Security managers |
| Company Admin | `visitors:configure` (full via inheritance) | System administrators |
| Employee (Host) | `visitors:create`, `visitors:read` | Host employees |

### 8.3 Navigation Manifest Integration

The VMS module has 16 sidebar entries in the navigation manifest, divided into two groups:

**Visitor Management Group (12 entries):**

| Manifest ID | Label | Permission | Sort |
|---|---|---|---|
| `vms-dashboard` | Visitors Dashboard | `visitors:read` | 750 |
| `vms-gate-checkin` | Gate Check-In | `visitors:create` | 751 |
| `vms-visitor-list` | All Visits | `visitors:read` | 752 |
| `vms-pre-register` | Pre-Register Visitor | `visitors:create` | 753 |
| `vms-recurring-passes` | Recurring Passes | `visitors:read` | 754 |
| `vms-group-visits` | Group Visits | `visitors:read` | 755 |
| `vms-vehicle-passes` | Vehicle Passes | `visitors:read` | 756 |
| `vms-material-passes` | Material Passes | `visitors:read` | 757 |
| `vms-watchlist` | Watchlist & Blocklist | `visitors:configure` | 758 |
| `vms-emergency` | Emergency Muster | `visitors:read` | 759 |
| `vms-reports` | Visitor Reports | `visitors:export` | 760 |
| `vms-history` | Visit History | `visitors:read` | 761 |

**VMS Settings Group (4 entries):**

| Manifest ID | Label | Permission | Sort |
|---|---|---|---|
| `vms-types` | Visitor Types | `visitors:configure` | 762 |
| `vms-gates` | Gates | `visitors:configure` | 763 |
| `vms-inductions` | Safety Inductions | `visitors:configure` | 764 |
| `vms-settings` | VMS Settings | `visitors:configure` | 765 |

All entries use `module: 'visitor'`, `roleScope: 'company'`.

### 8.4 Button-Level Permission Checks

In the web app, use the `useCanPerform` hook:

```typescript
const canConfigure = useCanPerform('visitors:configure');
const canApprove = useCanPerform('visitors:approve');
const canExport = useCanPerform('visitors:export');

// Show/hide buttons based on permissions
{canConfigure && <Button>Edit Visitor Type</Button>}
{canApprove && <Button>Approve Visit</Button>}
{canExport && <Button>Export Report</Button>}
```

In the mobile app, the same pattern applies using the permission context.

---

## 9. Number Series

### 9.1 VMS Number Series

The VMS module uses 7 number series, all registered in `src/shared/constants/linked-screens.ts`:

| Linked Screen Value | Label | Default Prefix | Used In |
|---|---|---|---|
| `Visitor` | Visitor Registration | `VIS-` | `visit.service.ts` -- `createVisit()` |
| `Visitor Badge` | Visitor Badge | `B-` | `visit.service.ts` -- `checkIn()` |
| `Gate Pass` | Gate Pass | `GP-` | General gate pass references |
| `Recurring Visitor Pass` | Recurring Visitor Pass | `RP-` | `recurring-pass.service.ts` -- `create()` |
| `Vehicle Gate Pass` | Vehicle Gate Pass | `VGP-` | `vehicle-pass.service.ts` -- `create()` |
| `Material Gate Pass` | Material Gate Pass | `MGP-` | `material-pass.service.ts` -- `create()` |
| `Group Visit` | Group Visit | `GV-` | Group visit creation |

### 9.2 How to Configure

1. Navigate to **Company Admin > Number Series Config**
2. The VMS linked screens appear automatically in the dropdown (populated via `GET /company/no-series/linked-screens`)
3. For each series, configure: prefix, starting number, padding (number of digits), optional suffix

### 9.3 Using generateNextNumber()

All VMS services use the shared `generateNextNumber()` utility:

```typescript
import { generateNextNumber } from '../../../shared/utils/number-series';

// Inside a transaction:
const visitNumber = await generateNextNumber(
  tx,                                               // Prisma transaction client
  companyId,                                        // Company ID
  ['Visitor', 'Visitor Registration'],             // Aliases (for backwards compatibility)
  'Visitor Registration',                           // Human-readable label for error messages
);
```

**Rules:**
- Always called inside a `$transaction` to ensure atomic increment
- Pass an array of aliases for backwards compatibility
- Never write custom number generators -- always use `generateNextNumber()`
- If not configured, throws `ApiError.badRequest` with a clear message directing the user to Number Series Config

---

## 10. Notification System

### 10.1 Notification Templates

The VMS module dispatches notifications for 13 different events:

| Template ID | Event | Default Channels | Variables |
|---|---|---|---|
| `VMS_INVITATION` | Pre-registration invite sent to visitor | Email + SMS + WhatsApp | `{visitorName}`, `{companyName}`, `{hostName}`, `{visitDate}`, `{visitTime}`, `{facilityAddress}`, `{qrCodeUrl}`, `{visitCode}`, `{preArrivalFormUrl}` |
| `VMS_HOST_ARRIVAL` | Visitor arrived at gate | Push + SMS | `{visitorName}`, `{visitorCompany}`, `{gate}`, `{time}` |
| `VMS_HOST_APPROVAL` | Walk-in/QR visitor needs approval | Push + SMS + Email | `{visitorName}`, `{visitorCompany}`, `{purpose}`, `{approveUrl}`, `{rejectUrl}` |
| `VMS_VISITOR_APPROVED` | Visit approved by host | SMS | `{visitorName}`, `{hostName}`, `{companyName}` |
| `VMS_VISITOR_REJECTED` | Visit rejected by host | SMS | `{visitorName}`, `{companyName}` |
| `VMS_HOST_CHECKED_IN` | Visitor checked in | Push + In-App | `{visitorName}`, `{gate}`, `{badgeNumber}` |
| `VMS_HOST_CHECKED_OUT` | Visitor checked out | In-App | `{visitorName}`, `{duration}` |
| `VMS_OVERSTAY` | Visitor overstaying expected duration | Push + SMS | `{visitorName}`, `{hostName}`, `{duration}`, `{expectedDuration}` |
| `VMS_EOD_UNCHECKED` | End-of-day: visitors still on-site | Email | `{visitorCount}`, `{visitorList}` |
| `VMS_BLOCKLIST_ALERT` | Blocklisted person attempted entry | Push + SMS + Email | `{personName}`, `{reason}`, `{gate}`, `{guard}` |
| `VMS_EMERGENCY` | Emergency evacuation triggered | SMS (to visitors) | `{companyName}`, `{assemblyPoint}` |
| `VMS_PASS_EXPIRY` | Recurring pass expiring soon | Email + In-App | `{visitorName}`, `{passNumber}`, `{expiryDate}` |
| `VMS_DIGITAL_BADGE` | Digital badge link sent to visitor | SMS + WhatsApp | `{visitorName}`, `{badgeUrl}` |

### 10.2 Currently Implemented Dispatch Points

The following trigger events are currently wired in the backend services:

| Service Method | Trigger Event | Recipient | Tokens |
|---|---|---|---|
| `visitService.createVisit()` | `VMS_PRE_REGISTRATION_CREATED` | Host employee | `visitorName`, `visitorCompany`, `visitDate`, `visitCode` |
| `visitService.checkIn()` | `VMS_VISITOR_CHECKED_IN` | Host employee | `visitorName`, `gate`, `badgeNumber` |
| `visitService.checkOut()` | `VMS_VISITOR_CHECKED_OUT` | Host employee | `visitorName`, `duration` |
| `emergencyService.triggerEmergency()` | `VMS_EMERGENCY_EVACUATION` | All on-site visitors | `visitorName`, `companyName` |

All dispatches are non-blocking (wrapped in try/catch). A failed notification dispatch does not prevent the core operation from completing.

### 10.3 How to Customise Templates

Notification templates are managed through the notification configuration system:

1. Navigate to **Company Admin > Notification Templates**
2. Select the VMS template to edit
3. Customise the message body, subject line, and enabled channels
4. Use the template variables (e.g., `{visitorName}`) within the message text

---

## 11. API Reference Summary

All VMS endpoints are mounted under the base path `/visitors/` (authenticated, tenant-scoped) or `/public/` (unauthenticated).

### 11.1 Authenticated Endpoints

**Base path:** `/visitors/` (requires auth + tenant middleware)

#### Configuration

| Method | Path | Permission | Description |
|---|---|---|---|
| GET | `/types` | `visitors:read` | List visitor types |
| POST | `/types` | `visitors:configure` | Create visitor type |
| GET | `/types/:id` | `visitors:read` | Get visitor type by ID |
| PUT | `/types/:id` | `visitors:configure` | Update visitor type |
| DELETE | `/types/:id` | `visitors:configure` | Deactivate visitor type |
| GET | `/gates` | `visitors:read` | List gates |
| POST | `/gates` | `visitors:configure` | Create gate |
| GET | `/gates/:id` | `visitors:read` | Get gate by ID |
| PUT | `/gates/:id` | `visitors:configure` | Update gate |
| DELETE | `/gates/:id` | `visitors:configure` | Deactivate gate |
| GET | `/safety-inductions` | `visitors:read` | List safety inductions |
| POST | `/safety-inductions` | `visitors:configure` | Create safety induction |
| GET | `/safety-inductions/:id` | `visitors:read` | Get safety induction by ID |
| PUT | `/safety-inductions/:id` | `visitors:configure` | Update safety induction |
| DELETE | `/safety-inductions/:id` | `visitors:configure` | Deactivate safety induction |
| GET | `/config` | `visitors:read` | Get VMS config |
| PUT | `/config` | `visitors:configure` | Update VMS config |

#### Core Visits

| Method | Path | Permission | Description |
|---|---|---|---|
| GET | `/visits` | `visitors:read` | List visits with filters |
| POST | `/visits` | `visitors:create` | Create pre-registration |
| GET | `/visits/code/:visitCode` | `visitors:read` | Get visit by code |
| GET | `/visits/:id` | `visitors:read` | Get visit by ID |
| PUT | `/visits/:id` | `visitors:update` | Update visit details |
| DELETE | `/visits/:id` | `visitors:delete` | Cancel visit |
| POST | `/visits/:id/check-in` | `visitors:create` | Check in visitor |
| POST | `/visits/:id/check-out` | `visitors:create` | Check out visitor |
| POST | `/visits/:id/approve` | `visitors:approve` | Approve visit |
| POST | `/visits/:id/reject` | `visitors:approve` | Reject visit |
| POST | `/visits/:id/extend` | `visitors:update` | Extend visit duration |
| POST | `/visits/:id/complete-induction` | `visitors:create` | Complete safety induction |

#### Security

| Method | Path | Permission | Description |
|---|---|---|---|
| GET | `/watchlist` | `visitors:read` | List watchlist entries |
| POST | `/watchlist` | `visitors:configure` | Create watchlist entry |
| POST | `/watchlist/check` | `visitors:read` | Check visitor against watchlist |
| GET | `/watchlist/:id` | `visitors:read` | Get watchlist entry by ID |
| PUT | `/watchlist/:id` | `visitors:configure` | Update watchlist entry |
| DELETE | `/watchlist/:id` | `visitors:configure` | Remove (deactivate) entry |
| GET | `/denied-entries` | `visitors:read` | List denied entries |
| GET | `/denied-entries/:id` | `visitors:read` | Get denied entry by ID |

#### Passes

| Method | Path | Permission | Description |
|---|---|---|---|
| GET | `/recurring-passes` | `visitors:read` | List recurring passes |
| POST | `/recurring-passes` | `visitors:create` | Create recurring pass |
| GET | `/recurring-passes/:id` | `visitors:read` | Get recurring pass by ID |
| PUT | `/recurring-passes/:id` | `visitors:update` | Update recurring pass |
| POST | `/recurring-passes/:id/revoke` | `visitors:delete` | Revoke recurring pass |
| POST | `/recurring-passes/:id/check-in` | `visitors:create` | Check in via recurring pass |
| GET | `/vehicle-passes` | `visitors:read` | List vehicle passes |
| POST | `/vehicle-passes` | `visitors:create` | Create vehicle pass |
| GET | `/vehicle-passes/:id` | `visitors:read` | Get vehicle pass by ID |
| POST | `/vehicle-passes/:id/exit` | `visitors:create` | Record vehicle exit |
| GET | `/material-passes` | `visitors:read` | List material passes |
| POST | `/material-passes` | `visitors:create` | Create material pass |
| GET | `/material-passes/:id` | `visitors:read` | Get material pass by ID |
| POST | `/material-passes/:id/return` | `visitors:update` | Mark material returned |

#### Group Visits

| Method | Path | Permission | Description |
|---|---|---|---|
| GET | `/group-visits` | `visitors:read` | List group visits |
| POST | `/group-visits` | `visitors:create` | Create group visit |
| GET | `/group-visits/:id` | `visitors:read` | Get group visit by ID |
| PUT | `/group-visits/:id` | `visitors:update` | Update group visit |
| POST | `/group-visits/:id/batch-check-in` | `visitors:create` | Batch check-in members |
| POST | `/group-visits/:id/batch-check-out` | `visitors:create` | Batch check-out members |

#### Dashboard & Reports

| Method | Path | Permission | Description |
|---|---|---|---|
| GET | `/dashboard/today` | `visitors:read` | Today's stats + visitor list |
| GET | `/dashboard/on-site` | `visitors:read` | Currently on-site visitors |
| GET | `/dashboard/stats` | `visitors:read` | Monthly KPI statistics |
| GET | `/reports/daily-log` | `visitors:export` | Daily visitor log |
| GET | `/reports/summary` | `visitors:export` | Date range summary |
| GET | `/reports/overstay` | `visitors:export` | Overstay report |
| GET | `/reports/analytics` | `visitors:read` | Analytics data |

#### Emergency

| Method | Path | Permission | Description |
|---|---|---|---|
| POST | `/emergency/trigger` | `visitors:configure` | Trigger emergency |
| GET | `/emergency/muster-list` | `visitors:read` | Get muster list |
| POST | `/emergency/mark-safe` | `visitors:create` | Mark visitors safe |
| POST | `/emergency/resolve` | `visitors:configure` | Resolve emergency |

### 11.2 Public Endpoints (No Authentication)

**Base path:** `/public/` (no auth, no tenant middleware)

| Method | Path | Description |
|---|---|---|
| GET | `/visit/:visitCode` | Get visit details for pre-arrival form |
| POST | `/visit/:visitCode/pre-arrival` | Submit pre-arrival form data |
| GET | `/visit/register/:plantCode` | Get self-registration form config |
| POST | `/visit/register/:plantCode` | Submit self-registration |
| GET | `/visit/:visitCode/status` | Check visit approval status |
| GET | `/visit/:visitCode/badge` | View digital badge |
| POST | `/visit/:visitCode/check-out` | Self-service check-out |

These endpoints are designed for visitors who do not have accounts in the system. They return limited information and accept limited input.

---

## 12. Troubleshooting

### 12.1 Common Issues and Solutions

| Issue | Cause | Solution |
|---|---|---|
| "Number series not configured for Visitor Registration" | Number series not set up | Go to Company Admin > Number Series Config and configure all 7 VMS series |
| "Visitor type not found" | Invalid or inactive visitor type ID | Verify the visitor type exists and `isActive = true` via `GET /visitors/types` |
| "Host employee not found" | Invalid employee ID or wrong company | Verify the employee exists in the same company via `GET /hr/employees` |
| "Plant/location not found" | Invalid plant ID or wrong company | Verify the location exists via `GET /company/locations` |
| "Entry denied: [reason]. This person is on the blocklist." | Visitor's mobile matches a blocklist entry | Remove from blocklist if false positive, or deny entry if legitimate |
| "Cannot check in a visit with status: CHECKED_IN" (409) | Duplicate check-in attempt | Visit is already checked in -- likely a concurrent request |
| "This visitor has already been checked out" (409) | Duplicate check-out attempt | Visit was already checked out |
| "Cannot update a visit that has already been checked in" | Attempting to edit after check-in | Visits can only be edited when status is `EXPECTED` or `ARRIVED` |
| "Maximum 3 extensions allowed per visit" | Extension limit reached | The visit has been extended 3 times already -- check out and create a new visit |
| "Total visit duration cannot exceed 24 hours" | Extension would exceed 24h | The combined duration would exceed 1440 minutes |
| "Pass is outside its validity period" | Recurring pass expired or not yet valid | Check `validFrom` and `validUntil` on the pass |
| "Pass is not valid for today" | Recurring pass not allowed on this day | Check `allowedDays` array on the pass |
| "Self-registration is not enabled at this facility" | `qrSelfRegistrationEnabled = false` | Enable QR self-registration in VMS Settings |
| "Could not find employee [name]" | Self-registration host name not matched | The visitor misspelled the host name, or the employee is inactive |
| "Can only update planned group visits" | Group visit already started | Group visits can only be edited in `PLANNED` status |
| "Material has already been fully returned" (409) | Duplicate return attempt | Material pass already fully returned |
| Sidebar does not show VMS items | Module not subscribed or no permissions | Verify `visitor` module is active on the location and user has `visitors:read` |

### 12.2 Error Messages Reference

**HTTP Status Codes Used:**

| Code | When |
|---|---|
| 200 | Successful read or update |
| 201 | Successful creation |
| 400 | Validation error, business rule violation |
| 401 | Missing or invalid authentication |
| 403 | Insufficient permissions |
| 404 | Entity not found |
| 409 | Conflict (duplicate check-in, already checked out, etc.) |

**API Error Pattern:**

All errors follow the standard Avy ERP error envelope:

```json
{
  "success": false,
  "error": "Error message here",
  "statusCode": 400
}
```

### 12.3 Database Model Quick Reference

The VMS module uses 15 Prisma models defined in `prisma/modules/visitors/visitors.prisma`:

| Model | Table Name | Purpose |
|---|---|---|
| `VisitorType` | `visitor_types` | Visitor classification with check-in rules |
| `VisitorGate` | `visitor_gates` | Physical entry/exit points |
| `SafetyInduction` | `safety_inductions` | Safety content for visitor induction |
| `Visit` | `visits` | Core visit record with full lifecycle data |
| `VisitorWatchlist` | `visitor_watchlists` | Blocklist and watchlist entries |
| `GroupVisit` | `group_visits` | Group visit header |
| `GroupVisitMember` | `group_visit_members` | Individual members of a group visit |
| `RecurringVisitorPass` | `recurring_visitor_passes` | Long-term visitor access passes |
| `VehicleGatePass` | `vehicle_gate_passes` | Vehicle entry/exit records |
| `MaterialGatePass` | `material_gate_passes` | Material movement records |
| `VisitorManagementConfig` | `visitor_management_configs` | Company-wide VMS settings |
| `DeniedEntry` | `denied_entries` | Audit trail of denied entries |

### 12.4 Backend File Map

```
avy-erp-backend/src/modules/visitors/
  routes.ts                           -- Main router (mounts all sub-routes)
  config/
    visitor-type.{service,controller,routes,validators}.ts
    gate.{service,controller,routes,validators}.ts
    safety-induction.{service,controller,routes,validators}.ts
    vms-config.{service,controller,routes}.ts
  core/
    visit.{service,controller,routes,validators,types}.ts
  security/
    watchlist.{service,controller,routes,validators}.ts
    denied-entry.{service,controller,routes}.ts
  passes/
    recurring-pass.{service,controller,routes,validators}.ts
    vehicle-pass.{service,controller,routes,validators}.ts
    material-pass.{service,controller,routes,validators}.ts
  group/
    group-visit.{service,controller,routes,validators}.ts
  dashboard/
    dashboard.{service,controller,routes}.ts
  reports/
    reports.{service,controller,routes}.ts
  emergency/
    emergency.{service,controller,routes}.ts
  public/
    public.{service,routes}.ts
```

### 12.5 Key Enums Reference

**VisitPurpose:** `MEETING`, `DELIVERY`, `MAINTENANCE`, `AUDIT`, `INTERVIEW`, `SITE_TOUR`, `PERSONAL`, `OTHER`

**RegistrationMethod:** `PRE_REGISTERED`, `QR_SELF_REG`, `WALK_IN`

**VisitStatus:** `EXPECTED`, `ARRIVED`, `CHECKED_IN`, `CHECKED_OUT`, `NO_SHOW`, `CANCELLED`, `REJECTED`, `AUTO_CHECKED_OUT`

**VisitApprovalStatus:** `PENDING`, `APPROVED`, `REJECTED`, `AUTO_APPROVED`

**CheckOutMethod:** `SECURITY_DESK`, `HOST_INITIATED`, `MOBILE_LINK`, `AUTO_CHECKOUT`

**InductionStatus:** `NOT_REQUIRED`, `PENDING`, `COMPLETED`, `FAILED`

**BadgeFormat:** `DIGITAL`, `PRINTED`

**GateType:** `MAIN`, `SERVICE`, `LOADING_DOCK`, `VIP`

**WatchlistType:** `BLOCKLIST`, `WATCHLIST`

**WatchlistDuration:** `PERMANENT`, `UNTIL_DATE`

**SafetyInductionType:** `VIDEO`, `SLIDES`, `QUESTIONNAIRE`, `DECLARATION`

**GroupVisitStatus:** `PLANNED`, `IN_PROGRESS`, `COMPLETED`, `CANCELLED`

**GroupMemberStatus:** `EXPECTED`, `CHECKED_IN`, `CHECKED_OUT`, `NO_SHOW`

**RecurringPassType:** `WEEKLY`, `MONTHLY`, `QUARTERLY`, `ANNUAL`

**RecurringPassStatus:** `ACTIVE`, `EXPIRED`, `REVOKED`

**VehicleType:** `CAR`, `TWO_WHEELER`, `AUTO`, `TRUCK`, `VAN`, `TEMPO`, `BUS`

**MaterialGatePassType:** `INWARD`, `OUTWARD`, `RETURNABLE`

**MaterialReturnStatus:** `NOT_APPLICABLE`, `PENDING_RETURN`, `PARTIAL`, `FULLY_RETURNED`

**ConfigRequirement:** `ALWAYS`, `PER_VISITOR_TYPE`, `NEVER`

**DenialReason:** `BLOCKLIST_MATCH`, `HOST_REJECTED`, `INDUCTION_FAILED`, `GATE_CLOSED`, `WRONG_DATE`, `WRONG_GATE`, `PASS_EXPIRED`, `APPROVAL_TIMEOUT`, `MANUAL_DENIAL`, `VISIT_CANCELLED`

---

*This guide reflects the implemented state of the VMS module as of April 2026. For the full product requirements, see `docs/Avy_ERP_Visitor_Management_Module_v2_PRD.md`. For implementation specifications, see `docs/specs/VMS-Implementation-Spec.md`.*
