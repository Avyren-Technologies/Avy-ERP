# Avy ERP -- VMS Module QA Test Cases

> **Document Code:** AVY-VMS-QA-001
> **Module:** Visitor Management System (VMS)
> **Version:** 1.0
> **Date:** April 2026
> **Status:** Ready for Testing

---

## Test Environment Setup

### Prerequisites

1. A running instance of Avy ERP backend (`avy-erp-backend`) connected to a seeded database.
2. Web system app (`web-system-app`) accessible in a browser.
3. Mobile app (`mobile-app`) running on Expo Go or a physical device.
4. At least one company fully onboarded with VMS module subscription active.
5. Number Series configured for:
   - "Visitor" or "Visitor Registration" (for visit numbers)
   - "Visitor Badge" or "Badge" (for badge numbers)
   - "Recurring Visitor Pass" or "Recurring Pass" (for pass numbers)
   - "Vehicle Gate Pass" or "Gate Pass" (for vehicle pass numbers)
   - "Material Gate Pass" or "Gate Pass" (for material pass numbers)

### Test Data to Prepare

| Entity             | Minimum Count | Details                                                                 |
|--------------------|---------------|-------------------------------------------------------------------------|
| Company            | 1             | Fully onboarded company with VMS module subscription                    |
| Locations (Plants) | 2             | Two active plant/locations under the company                            |
| Employees          | 5             | Active employees to act as hosts (at least 1 per plant)                 |
| Gates              | 3             | At least 2 gates for Plant A, 1 gate for Plant B                        |
| Visitor Types      | 3+            | At least Business Guest, Contractor, Delivery Agent (seeded defaults)   |
| Safety Inductions  | 1             | Video or questionnaire type, linked to Contractor visitor type          |

### User Roles to Test With

| Role              | Permission Scope              | User to Create                          |
|-------------------|-------------------------------|-----------------------------------------|
| Security Guard    | `visitors:read`, `visitors:create` | Employee with Security Guard role   |
| Security Manager  | `visitors:*` (all)            | Employee with Security Manager role     |
| Host Employee     | `visitors:read` (own guests)  | Regular employee who pre-registers      |
| Company Admin     | `visitors:configure`          | Company admin user                      |
| No VMS Access     | No `visitors:*` permissions   | Employee without VMS permissions        |

### Browser / Device Requirements

- Web: Chrome 100+, Firefox 100+, Safari 16+, Edge 100+
- Mobile: iOS 16+ or Android 12+ with Expo Go installed
- Screen sizes: Desktop 1280px+, Tablet 768px, Mobile 375px

---

## Test Case Format

Each test case follows this structure:

| Field          | Description                                                      |
|----------------|------------------------------------------------------------------|
| **ID**         | Unique identifier (TC-VMS-SECTION-NNN)                           |
| **Title**      | Short description of what is being tested                        |
| **Priority**   | P1 (critical path), P2 (important), P3 (edge case / nice-to-have)|
| **Preconditions** | State required before execution                               |
| **Steps**      | Numbered actions to perform                                      |
| **Expected Result** | Observable outcome that constitutes a pass                  |

---

## 1. Visitor Type Management (TC-VMS-TYPE-*)

### TC-VMS-TYPE-001: Create visitor type with valid data
| Field | Value |
|---|---|
| **Priority** | P1 |
| **Preconditions** | Logged in as Company Admin. Navigate to VMS > Visitor Types. |
| **Steps** | 1. Click "Add Visitor Type". 2. Enter Name: "Media Representative", Code: "MR", Badge Colour: "#FF5733". 3. Set requirePhoto=true, requireIdVerification=true, requireSafetyInduction=false, requireHostApproval=true. 4. Set defaultMaxDurationMinutes=240. 5. Click Save. |
| **Expected Result** | Visitor type created successfully. Appears in the list with all fields saved correctly. Response contains the new type ID. |

### TC-VMS-TYPE-002: Create visitor type with duplicate code
| Field | Value |
|---|---|
| **Priority** | P2 |
| **Preconditions** | Visitor type with code "MR" already exists for this company. |
| **Steps** | 1. Click "Add Visitor Type". 2. Enter Name: "Media Rep 2", Code: "MR". 3. Click Save. |
| **Expected Result** | Error returned: `Visitor type code "MR" already exists` (HTTP 409 Conflict). Type is not created. |

### TC-VMS-TYPE-003: Update visitor type
| Field | Value |
|---|---|
| **Priority** | P1 |
| **Preconditions** | At least one custom visitor type exists. |
| **Steps** | 1. Select the custom visitor type. 2. Change name to "Media & Press". 3. Change requireSafetyInduction to true. 4. Click Save. |
| **Expected Result** | Visitor type updated. Name and safety induction requirement reflect the changes. |

### TC-VMS-TYPE-004: Deactivate visitor type
| Field | Value |
|---|---|
| **Priority** | P2 |
| **Preconditions** | A custom (non-default) visitor type exists and is active. |
| **Steps** | 1. Select the custom visitor type. 2. Click "Deactivate". 3. Confirm action. |
| **Expected Result** | Visitor type isActive set to false. It no longer appears in active-only lists. It is still visible when filtering with isActive=false. |

### TC-VMS-TYPE-005: Attempt to deactivate a default visitor type
| Field | Value |
|---|---|
| **Priority** | P2 |
| **Preconditions** | A default visitor type exists (e.g., "Business Guest", isDefault=true). |
| **Steps** | 1. Select the default visitor type. 2. Attempt to deactivate. |
| **Expected Result** | Error returned: `Cannot deactivate a default visitor type` (HTTP 400). Type remains active. |

### TC-VMS-TYPE-006: Verify default types seeded on first access
| Field | Value |
|---|---|
| **Priority** | P1 |
| **Preconditions** | A new company with VMS module enabled but no visitor types yet. |
| **Steps** | 1. Create the first visitor type for this company. |
| **Expected Result** | Before the custom type is created, 9 default visitor types are seeded: Business Guest (BG), Vendor/Supplier (VN), Contractor (CT), Delivery Agent (DA), Government Inspector (GI), Job Candidate (JC), Personal Visitor (FV), VIP/Board Member (VP), Auditor (AU). All have isDefault=true, isActive=true. |

### TC-VMS-TYPE-007: Verify permission -- non-admin cannot create types
| Field | Value |
|---|---|
| **Priority** | P2 |
| **Preconditions** | Logged in as Security Guard (visitors:read, visitors:create only). |
| **Steps** | 1. Attempt to POST to /visitors/types with valid data. |
| **Expected Result** | HTTP 403 Forbidden. Only users with `visitors:configure` can manage visitor types. |

### TC-VMS-TYPE-008: List visitor types with pagination
| Field | Value |
|---|---|
| **Priority** | P2 |
| **Preconditions** | 10+ visitor types exist. |
| **Steps** | 1. GET /visitors/types?page=1&limit=5. 2. GET /visitors/types?page=2&limit=5. |
| **Expected Result** | Page 1 returns 5 items, page 2 returns remaining items. Total count is accurate. Types ordered by sortOrder ascending. |

### TC-VMS-TYPE-009: Filter visitor types by active status
| Field | Value |
|---|---|
| **Priority** | P3 |
| **Preconditions** | At least 1 active and 1 inactive visitor type exist. |
| **Steps** | 1. GET /visitors/types?isActive=true. 2. GET /visitors/types?isActive=false. |
| **Expected Result** | First query returns only active types. Second returns only inactive types. |

### TC-VMS-TYPE-010: Update visitor type code to an existing code
| Field | Value |
|---|---|
| **Priority** | P2 |
| **Preconditions** | Two visitor types exist: "MR" and "BG". |
| **Steps** | 1. Update the "MR" type, changing code to "BG". |
| **Expected Result** | Error: `Visitor type code "BG" already exists` (HTTP 409). Code not changed. |

---

## 2. Gate Management (TC-VMS-GATE-*)

### TC-VMS-GATE-001: Create gate with valid data
| Field | Value |
|---|---|
| **Priority** | P1 |
| **Preconditions** | At least one plant/location exists. Logged in as Company Admin. |
| **Steps** | 1. Navigate to VMS > Gates. 2. Click "Add Gate". 3. Enter plantId (Plant A), Name: "Main Entrance", Code: "GATE-A1", Type: "MAIN". 4. Set openTime: "06:00", closeTime: "22:00". 5. Click Save. |
| **Expected Result** | Gate created. qrPosterUrl auto-generated as `{APP_URL}/visit/register/GATE-A1`. All fields saved correctly. |

### TC-VMS-GATE-002: Verify QR poster URL auto-generated
| Field | Value |
|---|---|
| **Priority** | P1 |
| **Preconditions** | Gate created with code "GATE-A1". |
| **Steps** | 1. Retrieve the gate by ID. 2. Inspect qrPosterUrl field. |
| **Expected Result** | qrPosterUrl equals `{APP_URL}/visit/register/GATE-A1` (where APP_URL is the configured environment variable). |

### TC-VMS-GATE-003: Create gate with duplicate code
| Field | Value |
|---|---|
| **Priority** | P2 |
| **Preconditions** | Gate with code "GATE-A1" exists for this company. |
| **Steps** | 1. Attempt to create another gate with Code: "GATE-A1". |
| **Expected Result** | Error: `Gate code "GATE-A1" already exists` (HTTP 409). Gate not created. |

### TC-VMS-GATE-004: Filter gates by plant
| Field | Value |
|---|---|
| **Priority** | P2 |
| **Preconditions** | Gates exist for Plant A and Plant B. |
| **Steps** | 1. GET /visitors/gates?plantId={plantAId}. 2. GET /visitors/gates?plantId={plantBId}. |
| **Expected Result** | Each query returns only gates belonging to the specified plant. |

### TC-VMS-GATE-005: Deactivate gate
| Field | Value |
|---|---|
| **Priority** | P2 |
| **Preconditions** | An active gate exists. |
| **Steps** | 1. Call deactivate on the gate. |
| **Expected Result** | Gate isActive set to false. Gate no longer appears in active gate lists. |

### TC-VMS-GATE-006: Update gate code regenerates QR poster URL
| Field | Value |
|---|---|
| **Priority** | P2 |
| **Preconditions** | Gate exists with code "GATE-A1" and qrPosterUrl pointing to GATE-A1. |
| **Steps** | 1. Update gate code to "GATE-A2". |
| **Expected Result** | qrPosterUrl updated to `{APP_URL}/visit/register/GATE-A2`. |

### TC-VMS-GATE-007: Create gate with all gate types
| Field | Value |
|---|---|
| **Priority** | P3 |
| **Preconditions** | Plant exists. |
| **Steps** | 1. Create gates with types: MAIN, SERVICE, LOADING_DOCK, VIP. |
| **Expected Result** | All four gate types created successfully. Type stored correctly. |

### TC-VMS-GATE-008: Create gate with allowed visitor types
| Field | Value |
|---|---|
| **Priority** | P3 |
| **Preconditions** | Visitor types exist. |
| **Steps** | 1. Create gate with allowedVisitorTypeIds containing 2 type IDs. |
| **Expected Result** | Gate created with allowedVisitorTypeIds array containing both IDs. |

---

## 3. Safety Induction Management (TC-VMS-INDUCT-CFG-*)

### TC-VMS-INDUCT-CFG-001: Create video induction
| Field | Value |
|---|---|
| **Priority** | P1 |
| **Preconditions** | Logged in as Company Admin. |
| **Steps** | 1. POST /visitors/safety-inductions with name: "Factory Floor Safety", type: "VIDEO", contentUrl: "https://example.com/video.mp4", durationSeconds: 300, validityDays: 30, passingScore: 80. |
| **Expected Result** | Safety induction created. All fields saved. ID returned. |

### TC-VMS-INDUCT-CFG-002: Create questionnaire induction
| Field | Value |
|---|---|
| **Priority** | P1 |
| **Preconditions** | Logged in as Company Admin. |
| **Steps** | 1. POST /visitors/safety-inductions with type: "QUESTIONNAIRE", questions: [{question: "What is PPE?", options: ["Clothing", "Personal Protective Equipment", "Process"], correctAnswer: 1}], passingScore: 80. |
| **Expected Result** | Safety induction created with questions stored as JSON. |

### TC-VMS-INDUCT-CFG-003: List safety inductions with filters
| Field | Value |
|---|---|
| **Priority** | P2 |
| **Preconditions** | Multiple inductions exist across plants. |
| **Steps** | 1. GET /visitors/safety-inductions?plantId={plantA}. 2. GET /visitors/safety-inductions?isActive=true. |
| **Expected Result** | Filters applied correctly. Results paginated. |

### TC-VMS-INDUCT-CFG-004: Update safety induction
| Field | Value |
|---|---|
| **Priority** | P2 |
| **Preconditions** | A safety induction exists. |
| **Steps** | 1. PUT /visitors/safety-inductions/:id with updated passingScore: 90. |
| **Expected Result** | Passing score updated to 90. Other fields unchanged. |

### TC-VMS-INDUCT-CFG-005: Deactivate safety induction
| Field | Value |
|---|---|
| **Priority** | P2 |
| **Preconditions** | An active safety induction exists. |
| **Steps** | 1. DELETE /visitors/safety-inductions/:id (deactivate). |
| **Expected Result** | Induction isActive set to false. |

### TC-VMS-INDUCT-CFG-006: Link safety induction to visitor type
| Field | Value |
|---|---|
| **Priority** | P1 |
| **Preconditions** | Safety induction and Contractor visitor type exist. |
| **Steps** | 1. Update Contractor visitor type: set requireSafetyInduction=true, safetyInductionId={inductionId}. |
| **Expected Result** | Contractor type now requires induction. Fetching type by ID includes safetyInduction relation. |

---

## 4. VMS Configuration (TC-VMS-CFG-*)

### TC-VMS-CFG-001: Get config -- auto-creates with defaults if none
| Field | Value |
|---|---|
| **Priority** | P1 |
| **Preconditions** | No VMS config exists for this company (first access). |
| **Steps** | 1. GET /visitors/config. |
| **Expected Result** | Config record created with default values. Response contains the config object with companyId matching. |

### TC-VMS-CFG-002: Update individual toggles
| Field | Value |
|---|---|
| **Priority** | P1 |
| **Preconditions** | VMS config exists. |
| **Steps** | 1. PUT /visitors/config with { qrSelfRegistrationEnabled: false }. 2. GET /visitors/config. |
| **Expected Result** | qrSelfRegistrationEnabled is false. All other config values remain at their previous settings (upsert behavior). |

### TC-VMS-CFG-003: Update config -- photoCapture setting
| Field | Value |
|---|---|
| **Priority** | P2 |
| **Preconditions** | VMS config exists. |
| **Steps** | 1. PUT /visitors/config with { photoCapture: "ALWAYS" }. |
| **Expected Result** | Config updated. photoCapture is "ALWAYS". |

### TC-VMS-CFG-004: Update config -- privacyConsentText
| Field | Value |
|---|---|
| **Priority** | P3 |
| **Preconditions** | VMS config exists. |
| **Steps** | 1. PUT /visitors/config with { privacyConsentText: "We collect your data for security purposes only." }. |
| **Expected Result** | Config updated with the new consent text. |

### TC-VMS-CFG-005: Verify config changes reflect in self-registration flow
| Field | Value |
|---|---|
| **Priority** | P2 |
| **Preconditions** | VMS config with qrSelfRegistrationEnabled=false. |
| **Steps** | 1. Access the public self-registration endpoint: GET /public/visit/register/{plantCode}. |
| **Expected Result** | Error: `Self-registration is not enabled at this facility` (HTTP 400). |

---

## 5. Pre-Registration (TC-VMS-PREREG-*)

### TC-VMS-PREREG-001: Create pre-registration with all fields
| Field | Value |
|---|---|
| **Priority** | P1 |
| **Preconditions** | Active visitor type, host employee, plant, and gate exist. Number series configured. |
| **Steps** | 1. POST /visitors/visits with all fields: visitorName, visitorMobile, visitorEmail, visitorCompany, visitorDesignation, visitorTypeId, purpose: "MEETING", purposeNotes, expectedDate (future), expectedTime: "14:00", expectedDurationMinutes: 120, hostEmployeeId, plantId, gateId, vehicleRegNumber, vehicleType, materialCarriedIn, specialInstructions, emergencyContact, meetingRef, purchaseOrderRef. |
| **Expected Result** | Visit created with status: "EXPECTED", registrationMethod: "PRE_REGISTERED". visitCode is 6 chars (no ambiguous characters I/O/0/1). visitNumber generated from number series. approvalStatus depends on visitor type (PENDING if requireHostApproval=true, AUTO_APPROVED otherwise). safetyInductionStatus is PENDING or NOT_REQUIRED based on visitor type. |

### TC-VMS-PREREG-002: Create pre-registration with minimum required fields
| Field | Value |
|---|---|
| **Priority** | P1 |
| **Preconditions** | Active visitor type, host employee, plant exist. |
| **Steps** | 1. POST /visitors/visits with only: visitorName, visitorMobile, visitorTypeId, purpose: "MEETING", expectedDate, hostEmployeeId, plantId. |
| **Expected Result** | Visit created successfully. Optional fields are null. expectedDurationMinutes defaults to visitor type's defaultMaxDurationMinutes. |

### TC-VMS-PREREG-003: Verify visit code generated -- 6 characters, no ambiguous chars
| Field | Value |
|---|---|
| **Priority** | P1 |
| **Preconditions** | A visit is created. |
| **Steps** | 1. Inspect the visitCode field on the created visit. |
| **Expected Result** | visitCode is exactly 6 characters. Contains only characters from set: ABCDEFGHJKLMNPQRSTUVWXYZ23456789 (no I, O, 0, 1). |

### TC-VMS-PREREG-004: Verify host notification dispatched on creation
| Field | Value |
|---|---|
| **Priority** | P2 |
| **Preconditions** | Notification service is operational. |
| **Steps** | 1. Create a pre-registration visit. 2. Check notification logs. |
| **Expected Result** | Notification dispatched with triggerEvent: "VMS_PRE_REGISTRATION_CREATED" to the host employee. Contains visitorName, visitorCompany, visitDate, visitCode tokens. |

### TC-VMS-PREREG-005: Create with invalid host employee
| Field | Value |
|---|---|
| **Priority** | P1 |
| **Preconditions** | A random UUID that does not match any employee. |
| **Steps** | 1. POST /visitors/visits with hostEmployeeId set to a non-existent ID. |
| **Expected Result** | Error: `Host employee not found` (HTTP 404). |

### TC-VMS-PREREG-006: Create with invalid visitor type
| Field | Value |
|---|---|
| **Priority** | P1 |
| **Preconditions** | A random UUID that does not match any visitor type. |
| **Steps** | 1. POST /visitors/visits with visitorTypeId set to a non-existent ID. |
| **Expected Result** | Error: `Visitor type not found` (HTTP 404). |

### TC-VMS-PREREG-007: Create with inactive visitor type
| Field | Value |
|---|---|
| **Priority** | P2 |
| **Preconditions** | An inactive visitor type exists. |
| **Steps** | 1. POST /visitors/visits with visitorTypeId set to the inactive type's ID. |
| **Expected Result** | Error: `Visitor type not found` (HTTP 404) -- service filters by isActive=true. |

### TC-VMS-PREREG-008: Create with invalid plant
| Field | Value |
|---|---|
| **Priority** | P1 |
| **Preconditions** | A random UUID that does not match any location. |
| **Steps** | 1. POST /visitors/visits with plantId set to a non-existent ID. |
| **Expected Result** | Error: `Plant/location not found` (HTTP 404). |

### TC-VMS-PREREG-009: Create pre-registration for blocklisted visitor
| Field | Value |
|---|---|
| **Priority** | P1 |
| **Preconditions** | A blocklist entry exists for mobile "9876543210". |
| **Steps** | 1. POST /visitors/visits with visitorMobile: "9876543210". |
| **Expected Result** | Error: `Entry denied: [reason]. This person is on the blocklist.` (HTTP 400). Visit not created. |

### TC-VMS-PREREG-010: Create pre-registration for watchlisted visitor
| Field | Value |
|---|---|
| **Priority** | P2 |
| **Preconditions** | A watchlist (not blocklist) entry exists for mobile "9876543211". |
| **Steps** | 1. POST /visitors/visits with visitorMobile: "9876543211". |
| **Expected Result** | Visit created successfully (watchlist does not block creation). No error thrown. |

### TC-VMS-PREREG-011: Create multi-visitor with same meetingRef
| Field | Value |
|---|---|
| **Priority** | P2 |
| **Preconditions** | Valid host, plant, visitor type. |
| **Steps** | 1. POST /visitors/visits for Visitor A with meetingRef: "MTG-001". 2. POST /visitors/visits for Visitor B with meetingRef: "MTG-001". 3. GET /visitors/visits?search=MTG-001. |
| **Expected Result** | Both visits created with independent visitCodes and visitNumbers. Both share meetingRef "MTG-001". Search returns both visits. |

### TC-VMS-PREREG-012: Cancel pre-registration
| Field | Value |
|---|---|
| **Priority** | P1 |
| **Preconditions** | A visit exists with status "EXPECTED". |
| **Steps** | 1. DELETE /visitors/visits/:id (cancel). |
| **Expected Result** | Visit status changed to "CANCELLED". |

### TC-VMS-PREREG-013: Cannot cancel a checked-in visit
| Field | Value |
|---|---|
| **Priority** | P1 |
| **Preconditions** | A visit exists with status "CHECKED_IN". |
| **Steps** | 1. DELETE /visitors/visits/:id (cancel). |
| **Expected Result** | Error: `Cannot cancel a visit that is already in progress or completed` (HTTP 400). Status unchanged. |

### TC-VMS-PREREG-014: Cannot cancel a completed visit
| Field | Value |
|---|---|
| **Priority** | P2 |
| **Preconditions** | A visit exists with status "CHECKED_OUT". |
| **Steps** | 1. DELETE /visitors/visits/:id (cancel). |
| **Expected Result** | Error: `Cannot cancel a visit that is already in progress or completed` (HTTP 400). |

### TC-VMS-PREREG-015: Update pre-registration details
| Field | Value |
|---|---|
| **Priority** | P1 |
| **Preconditions** | A visit exists with status "EXPECTED". |
| **Steps** | 1. PUT /visitors/visits/:id with { visitorName: "Updated Name", expectedTime: "15:00" }. |
| **Expected Result** | Visit updated. visitorName is "Updated Name". expectedTime is "15:00". Other fields unchanged. |

### TC-VMS-PREREG-016: Cannot update a checked-in visit
| Field | Value |
|---|---|
| **Priority** | P1 |
| **Preconditions** | A visit exists with status "CHECKED_IN". |
| **Steps** | 1. PUT /visitors/visits/:id with { visitorName: "New Name" }. |
| **Expected Result** | Error: `Cannot update a visit that has already been checked in or completed` (HTTP 400). |

### TC-VMS-PREREG-017: Get visit by ID
| Field | Value |
|---|---|
| **Priority** | P1 |
| **Preconditions** | A visit exists. |
| **Steps** | 1. GET /visitors/visits/:id. |
| **Expected Result** | Visit returned with visitorType, checkInGate, checkOutGate, assignedGate, groupVisit, recurringPass relations included. |

### TC-VMS-PREREG-018: Get visit by visit code
| Field | Value |
|---|---|
| **Priority** | P1 |
| **Preconditions** | A visit exists with known visitCode. |
| **Steps** | 1. GET /visitors/visits/code/{visitCode}. |
| **Expected Result** | Visit returned with visitorType included. |

### TC-VMS-PREREG-019: Get visit by invalid visit code
| Field | Value |
|---|---|
| **Priority** | P2 |
| **Preconditions** | No visit with code "XXXXXX" exists. |
| **Steps** | 1. GET /visitors/visits/code/XXXXXX. |
| **Expected Result** | Error: `Visit not found for the provided code` (HTTP 404). |

### TC-VMS-PREREG-020: List visits with filters and pagination
| Field | Value |
|---|---|
| **Priority** | P1 |
| **Preconditions** | Multiple visits exist with various statuses, types, and dates. |
| **Steps** | 1. GET /visitors/visits?status=EXPECTED&page=1&limit=10. 2. GET /visitors/visits?hostEmployeeId={id}&fromDate=2026-04-01&toDate=2026-04-30. 3. GET /visitors/visits?search=John. |
| **Expected Result** | Each query returns correctly filtered results. Pagination metadata (total) is accurate. Results ordered by expectedDate desc. Search matches visitorName, visitorMobile, visitorCompany, visitCode, or visitNumber. |

### TC-VMS-PREREG-021: Visitor type with requireHostApproval=true sets PENDING
| Field | Value |
|---|---|
| **Priority** | P1 |
| **Preconditions** | Visitor type "Business Guest" has requireHostApproval=true. |
| **Steps** | 1. Create visit with this visitor type. |
| **Expected Result** | Visit approvalStatus is "PENDING". |

### TC-VMS-PREREG-022: Visitor type with requireHostApproval=false sets AUTO_APPROVED
| Field | Value |
|---|---|
| **Priority** | P1 |
| **Preconditions** | Visitor type "Delivery Agent" has requireHostApproval=false. |
| **Steps** | 1. Create visit with this visitor type. |
| **Expected Result** | Visit approvalStatus is "AUTO_APPROVED". |

### TC-VMS-PREREG-023: Validation -- missing required fields
| Field | Value |
|---|---|
| **Priority** | P1 |
| **Preconditions** | None. |
| **Steps** | 1. POST /visitors/visits with empty body. 2. POST with visitorName but missing visitorMobile. 3. POST with invalid purpose value "INVALID". |
| **Expected Result** | Each request returns HTTP 400 with descriptive Zod validation error messages. |

### TC-VMS-PREREG-024: Validation -- expectedTime format
| Field | Value |
|---|---|
| **Priority** | P3 |
| **Preconditions** | None. |
| **Steps** | 1. POST /visitors/visits with expectedTime: "2pm" (invalid). 2. POST with expectedTime: "14:00" (valid). |
| **Expected Result** | First request returns validation error: `Time must be HH:mm format`. Second succeeds. |

### TC-VMS-PREREG-025: Validation -- expectedDurationMinutes range
| Field | Value |
|---|---|
| **Priority** | P3 |
| **Preconditions** | None. |
| **Steps** | 1. POST with expectedDurationMinutes: 10 (below min 15). 2. POST with expectedDurationMinutes: 1500 (above max 1440). |
| **Expected Result** | Both return validation errors about the allowed range. |

---

## 6. Gate Check-In (TC-VMS-CHECKIN-*)

### TC-VMS-CHECKIN-001: Check in pre-registered visitor
| Field | Value |
|---|---|
| **Priority** | P1 |
| **Preconditions** | Visit exists with status "EXPECTED" or "ARRIVED". Gate exists. User is Security Guard. |
| **Steps** | 1. POST /visitors/visits/:id/check-in with { checkInGateId: "{gateId}" }. |
| **Expected Result** | Visit status changed to "CHECKED_IN". checkInTime populated with current timestamp. checkInGateId matches. checkInGuardId set to the current user. badgeNumber generated from number series. Response includes visitorType and checkInGate relations. |

### TC-VMS-CHECKIN-002: Check in with full identity details
| Field | Value |
|---|---|
| **Priority** | P1 |
| **Preconditions** | Visit exists with status "EXPECTED". |
| **Steps** | 1. POST /visitors/visits/:id/check-in with { checkInGateId, visitorPhoto: "https://example.com/photo.jpg", governmentIdType: "AADHAAR", governmentIdNumber: "1234-5678-9012", idDocumentPhoto: "https://example.com/id.jpg", badgeFormat: "DIGITAL" }. |
| **Expected Result** | All identity fields saved on the visit record. Check-in succeeds. |

### TC-VMS-CHECKIN-003: Duplicate check-in attempt
| Field | Value |
|---|---|
| **Priority** | P1 |
| **Preconditions** | Visit already has status "CHECKED_IN". |
| **Steps** | 1. POST /visitors/visits/:id/check-in with valid data. |
| **Expected Result** | Error: `This visitor is already checked in (checked in at ...)` (HTTP 409 Conflict). |

### TC-VMS-CHECKIN-004: Check in visitor matching blocklist
| Field | Value |
|---|---|
| **Priority** | P1 |
| **Preconditions** | Visitor's mobile matches a blocklist entry. Visit was created before the blocklist entry (so pre-registration succeeded). |
| **Steps** | 1. Add the visitor's mobile to the blocklist. 2. POST /visitors/visits/:id/check-in. |
| **Expected Result** | Check-in reverted. Visit status set to "CANCELLED". DeniedEntry record created with denialReason: "BLOCKLIST_MATCH". Error thrown to the guard. |

### TC-VMS-CHECKIN-005: Check in visitor matching watchlist
| Field | Value |
|---|---|
| **Priority** | P2 |
| **Preconditions** | Visitor's mobile matches a watchlist (not blocklist) entry. |
| **Steps** | 1. POST /visitors/visits/:id/check-in. |
| **Expected Result** | Check-in succeeds. Response includes watchlistWarning with the alert reason. Guard is informed but can proceed. |

### TC-VMS-CHECKIN-006: Check in with invalid visit code
| Field | Value |
|---|---|
| **Priority** | P2 |
| **Preconditions** | No visit with the given ID exists. |
| **Steps** | 1. POST /visitors/visits/{invalidId}/check-in. |
| **Expected Result** | Error: `Visit not found` (HTTP 404). |

### TC-VMS-CHECKIN-007: Check in a cancelled visit
| Field | Value |
|---|---|
| **Priority** | P2 |
| **Preconditions** | Visit has status "CANCELLED". |
| **Steps** | 1. POST /visitors/visits/:id/check-in. |
| **Expected Result** | Error: `Cannot check in a visit with status: CANCELLED` (HTTP 400). |

### TC-VMS-CHECKIN-008: Check in a rejected visit
| Field | Value |
|---|---|
| **Priority** | P2 |
| **Preconditions** | Visit has status "REJECTED" (host rejected). |
| **Steps** | 1. POST /visitors/visits/:id/check-in. |
| **Expected Result** | Error: `Cannot check in a visit with status: REJECTED` (HTTP 400). |

### TC-VMS-CHECKIN-009: Badge number generated on check-in
| Field | Value |
|---|---|
| **Priority** | P1 |
| **Preconditions** | Number series configured for "Visitor Badge" or "Badge". |
| **Steps** | 1. Check in a visitor. 2. Inspect the badgeNumber field. |
| **Expected Result** | badgeNumber is non-null, follows the configured number series format (e.g., "VB-00001"). |

### TC-VMS-CHECKIN-010: Host notification sent on check-in
| Field | Value |
|---|---|
| **Priority** | P2 |
| **Preconditions** | Notification service is operational. |
| **Steps** | 1. Check in a visitor. 2. Verify notification logs. |
| **Expected Result** | Notification dispatched with triggerEvent: "VMS_VISITOR_CHECKED_IN" to host employee. Contains visitorName, gate name, badgeNumber tokens. |

### TC-VMS-CHECKIN-011: Concurrent check-in by two guards -- only one succeeds
| Field | Value |
|---|---|
| **Priority** | P1 |
| **Preconditions** | Visit with status "EXPECTED". Two guard sessions available. |
| **Steps** | 1. Simultaneously send two check-in requests for the same visit from two different guard accounts. |
| **Expected Result** | Exactly one request succeeds (HTTP 200). The other returns HTTP 409: `This visitor is already checked in`. This is enforced by the atomic conditional UPDATE in SQL (status IN ('EXPECTED', 'ARRIVED')). |

### TC-VMS-CHECKIN-012: Check in without number series configured
| Field | Value |
|---|---|
| **Priority** | P2 |
| **Preconditions** | No number series configured for "Visitor Badge". |
| **Steps** | 1. Attempt to check in a visitor. |
| **Expected Result** | Error from generateNextNumber indicating the number series is not configured. Guard cannot complete check-in until admin configures the series. |

### TC-VMS-CHECKIN-013: Validation -- missing checkInGateId
| Field | Value |
|---|---|
| **Priority** | P2 |
| **Preconditions** | Valid visit. |
| **Steps** | 1. POST /visitors/visits/:id/check-in with empty body (no checkInGateId). |
| **Expected Result** | Validation error: `Gate is required`. |

### TC-VMS-CHECKIN-014: Validation -- invalid governmentIdType
| Field | Value |
|---|---|
| **Priority** | P3 |
| **Preconditions** | Valid visit. |
| **Steps** | 1. POST /visitors/visits/:id/check-in with governmentIdType: "INVALID_TYPE". |
| **Expected Result** | Validation error listing allowed values: AADHAAR, PAN, DRIVING_LICENCE, PASSPORT, VOTER_ID. |

---

## 7. Check-Out (TC-VMS-CHECKOUT-*)

### TC-VMS-CHECKOUT-001: Check out at security desk
| Field | Value |
|---|---|
| **Priority** | P1 |
| **Preconditions** | Visit with status "CHECKED_IN". Gate exists. |
| **Steps** | 1. POST /visitors/visits/:id/check-out with { checkOutGateId: "{gateId}", checkOutMethod: "SECURITY_DESK", badgeReturned: true }. |
| **Expected Result** | Visit status changed to "CHECKED_OUT". checkOutTime populated. checkOutGateId set. checkOutMethod is "SECURITY_DESK". badgeReturned is true. |

### TC-VMS-CHECKOUT-002: Host-initiated check-out
| Field | Value |
|---|---|
| **Priority** | P2 |
| **Preconditions** | Visit with status "CHECKED_IN". Host employee is logged in. |
| **Steps** | 1. POST /visitors/visits/:id/check-out with { checkOutMethod: "HOST_INITIATED" }. |
| **Expected Result** | Check-out succeeds with checkOutMethod "HOST_INITIATED". checkOutGateId is null (host may not know gate). |

### TC-VMS-CHECKOUT-003: Duplicate check-out attempt
| Field | Value |
|---|---|
| **Priority** | P1 |
| **Preconditions** | Visit already has status "CHECKED_OUT". |
| **Steps** | 1. POST /visitors/visits/:id/check-out with valid data. |
| **Expected Result** | Error: `This visitor has already been checked out` (HTTP 409 Conflict). |

### TC-VMS-CHECKOUT-004: Visit duration calculated correctly
| Field | Value |
|---|---|
| **Priority** | P1 |
| **Preconditions** | Visit checked in 2 hours ago (checkInTime is 120 minutes in the past). |
| **Steps** | 1. Check out the visitor. 2. Inspect visitDurationMinutes. |
| **Expected Result** | visitDurationMinutes is approximately 120 (within +/- 1 minute tolerance for test execution time). |

### TC-VMS-CHECKOUT-005: Check out visitor who is not checked in (status EXPECTED)
| Field | Value |
|---|---|
| **Priority** | P2 |
| **Preconditions** | Visit with status "EXPECTED". |
| **Steps** | 1. POST /visitors/visits/:id/check-out. |
| **Expected Result** | Error: `Cannot check out a visit with status: EXPECTED` (HTTP 400). |

### TC-VMS-CHECKOUT-006: Check out auto-checked-out visitor
| Field | Value |
|---|---|
| **Priority** | P2 |
| **Preconditions** | Visit with status "AUTO_CHECKED_OUT". |
| **Steps** | 1. POST /visitors/visits/:id/check-out. |
| **Expected Result** | Error: `This visitor has already been checked out` (HTTP 409). |

### TC-VMS-CHECKOUT-007: Host notification sent on check-out
| Field | Value |
|---|---|
| **Priority** | P2 |
| **Preconditions** | Notification service is operational. Visit is CHECKED_IN. |
| **Steps** | 1. Check out the visitor. 2. Verify notification logs. |
| **Expected Result** | Notification dispatched with triggerEvent: "VMS_VISITOR_CHECKED_OUT" to host employee. Contains visitorName and duration tokens. |

### TC-VMS-CHECKOUT-008: Material-out recorded on check-out
| Field | Value |
|---|---|
| **Priority** | P3 |
| **Preconditions** | Visit is CHECKED_IN. |
| **Steps** | 1. POST /visitors/visits/:id/check-out with { checkOutMethod: "SECURITY_DESK", materialOut: "Laptop bag, 2 sample boxes" }. |
| **Expected Result** | materialOut field saved on the visit record. |

### TC-VMS-CHECKOUT-009: Validation -- invalid checkOutMethod
| Field | Value |
|---|---|
| **Priority** | P3 |
| **Preconditions** | Visit is CHECKED_IN. |
| **Steps** | 1. POST /visitors/visits/:id/check-out with { checkOutMethod: "INVALID" }. |
| **Expected Result** | Validation error. Allowed values: SECURITY_DESK, HOST_INITIATED, MOBILE_LINK, AUTO_CHECKOUT. |

---

## 8. Approval Workflow (TC-VMS-APPROVAL-*)

### TC-VMS-APPROVAL-001: Approve a pending visit
| Field | Value |
|---|---|
| **Priority** | P1 |
| **Preconditions** | Visit with approvalStatus "PENDING". Host employee logged in. |
| **Steps** | 1. POST /visitors/visits/:id/approve with { notes: "Approved for meeting" }. |
| **Expected Result** | approvalStatus changed to "APPROVED". approvedBy set to current user. approvalTimestamp populated. approvalNotes saved. |

### TC-VMS-APPROVAL-002: Reject a pending visit
| Field | Value |
|---|---|
| **Priority** | P1 |
| **Preconditions** | Visit with approvalStatus "PENDING". |
| **Steps** | 1. POST /visitors/visits/:id/reject with { notes: "Meeting cancelled" }. |
| **Expected Result** | approvalStatus changed to "REJECTED". Visit status changed to "REJECTED". DeniedEntry record created with denialReason: "HOST_REJECTED", denialDetails: "Meeting cancelled". |

### TC-VMS-APPROVAL-003: Attempt to approve already-approved visit
| Field | Value |
|---|---|
| **Priority** | P2 |
| **Preconditions** | Visit with approvalStatus "APPROVED". |
| **Steps** | 1. POST /visitors/visits/:id/approve. |
| **Expected Result** | Error: `Visit is already approved` (HTTP 400). |

### TC-VMS-APPROVAL-004: Attempt to reject already-rejected visit
| Field | Value |
|---|---|
| **Priority** | P2 |
| **Preconditions** | Visit with approvalStatus "REJECTED". |
| **Steps** | 1. POST /visitors/visits/:id/reject. |
| **Expected Result** | Error: `Visit is already rejected` (HTTP 400). |

### TC-VMS-APPROVAL-005: Pre-registered visitor with auto-approval
| Field | Value |
|---|---|
| **Priority** | P1 |
| **Preconditions** | Visitor type has requireHostApproval=false (e.g., "Delivery Agent"). |
| **Steps** | 1. Create a visit with this visitor type. |
| **Expected Result** | Visit created with approvalStatus "AUTO_APPROVED". No approval action needed. |

### TC-VMS-APPROVAL-006: Permission check -- visitors:approve required
| Field | Value |
|---|---|
| **Priority** | P2 |
| **Preconditions** | User has visitors:create but NOT visitors:approve. |
| **Steps** | 1. POST /visitors/visits/:id/approve. |
| **Expected Result** | HTTP 403 Forbidden. Approval requires visitors:approve permission. |

### TC-VMS-APPROVAL-007: Approve visit without notes
| Field | Value |
|---|---|
| **Priority** | P3 |
| **Preconditions** | Visit with approvalStatus "PENDING". |
| **Steps** | 1. POST /visitors/visits/:id/approve with empty body (no notes). |
| **Expected Result** | Approval succeeds. approvalNotes is null. |

---

## 9. Safety Induction (TC-VMS-INDUCTION-*)

### TC-VMS-INDUCTION-001: Complete induction -- passed
| Field | Value |
|---|---|
| **Priority** | P1 |
| **Preconditions** | Visit exists with safetyInductionStatus "PENDING". |
| **Steps** | 1. POST /visitors/visits/:id/complete-induction with { score: 90, passed: true }. |
| **Expected Result** | safetyInductionStatus changed to "COMPLETED". safetyInductionScore is 90. safetyInductionTimestamp populated. |

### TC-VMS-INDUCTION-002: Complete induction -- failed
| Field | Value |
|---|---|
| **Priority** | P1 |
| **Preconditions** | Visit exists with safetyInductionStatus "PENDING". |
| **Steps** | 1. POST /visitors/visits/:id/complete-induction with { score: 50, passed: false }. |
| **Expected Result** | safetyInductionStatus changed to "FAILED". safetyInductionScore is 50. |

### TC-VMS-INDUCTION-003: Complete induction without score (declaration type)
| Field | Value |
|---|---|
| **Priority** | P2 |
| **Preconditions** | Visit with PENDING induction. Induction type is DECLARATION. |
| **Steps** | 1. POST /visitors/visits/:id/complete-induction with { passed: true } (no score). |
| **Expected Result** | safetyInductionStatus changed to "COMPLETED". safetyInductionScore is null. |

### TC-VMS-INDUCTION-004: Visitor type without induction requirement
| Field | Value |
|---|---|
| **Priority** | P2 |
| **Preconditions** | Visit created with visitor type that has requireSafetyInduction=false. |
| **Steps** | 1. Inspect the visit's safetyInductionStatus. |
| **Expected Result** | safetyInductionStatus is "NOT_REQUIRED". |

### TC-VMS-INDUCTION-005: Contractor type requires induction
| Field | Value |
|---|---|
| **Priority** | P1 |
| **Preconditions** | Contractor visitor type has requireSafetyInduction=true. |
| **Steps** | 1. Create visit with Contractor type. 2. Inspect safetyInductionStatus. |
| **Expected Result** | safetyInductionStatus is "PENDING". |

### TC-VMS-INDUCTION-006: Validation -- score out of range
| Field | Value |
|---|---|
| **Priority** | P3 |
| **Preconditions** | Visit with PENDING induction. |
| **Steps** | 1. POST with { score: 150, passed: true }. 2. POST with { score: -10, passed: false }. |
| **Expected Result** | Both return validation errors. Score must be 0-100. |

---

## 10. Visit Extension (TC-VMS-EXTEND-*)

### TC-VMS-EXTEND-001: Extend active visit by 1 hour
| Field | Value |
|---|---|
| **Priority** | P1 |
| **Preconditions** | Visit with status "CHECKED_IN", expectedDurationMinutes=120. |
| **Steps** | 1. POST /visitors/visits/:id/extend with { additionalMinutes: 60, reason: "Meeting extended" }. |
| **Expected Result** | expectedDurationMinutes increased to 180. extensionCount is 1. originalDurationMinutes set to 120. lastExtendedAt populated. |

### TC-VMS-EXTEND-002: Extend beyond maximum 3 extensions
| Field | Value |
|---|---|
| **Priority** | P1 |
| **Preconditions** | Visit already has extensionCount=3. |
| **Steps** | 1. POST /visitors/visits/:id/extend with { additionalMinutes: 60, reason: "Further delay" }. |
| **Expected Result** | Error: `Maximum 3 extensions allowed per visit` (HTTP 400). |

### TC-VMS-EXTEND-003: Extend beyond 24 hours total duration
| Field | Value |
|---|---|
| **Priority** | P1 |
| **Preconditions** | Visit has expectedDurationMinutes=1400 (23h 20m). |
| **Steps** | 1. POST /visitors/visits/:id/extend with { additionalMinutes: 60, reason: "Overnight" }. |
| **Expected Result** | Error: `Total visit duration cannot exceed 24 hours` (HTTP 400). 1400 + 60 = 1460 > 1440. |

### TC-VMS-EXTEND-004: Cannot extend a non-active visit
| Field | Value |
|---|---|
| **Priority** | P2 |
| **Preconditions** | Visit with status "EXPECTED" (not yet checked in). |
| **Steps** | 1. POST /visitors/visits/:id/extend with valid data. |
| **Expected Result** | Error: `Can only extend an active (checked-in) visit` (HTTP 400). |

### TC-VMS-EXTEND-005: Cannot extend a checked-out visit
| Field | Value |
|---|---|
| **Priority** | P2 |
| **Preconditions** | Visit with status "CHECKED_OUT". |
| **Steps** | 1. POST /visitors/visits/:id/extend with valid data. |
| **Expected Result** | Error: `Can only extend an active (checked-in) visit` (HTTP 400). |

### TC-VMS-EXTEND-006: Multiple extensions increment count correctly
| Field | Value |
|---|---|
| **Priority** | P2 |
| **Preconditions** | Visit with status "CHECKED_IN", extensionCount=0, expectedDurationMinutes=120. |
| **Steps** | 1. Extend by 30 minutes. 2. Extend by 30 minutes again. 3. Extend by 30 minutes a third time. |
| **Expected Result** | After each extension: extensionCount is 1, 2, 3 respectively. expectedDurationMinutes is 150, 180, 210. originalDurationMinutes remains 120 throughout. |

### TC-VMS-EXTEND-007: Validation -- additionalMinutes range
| Field | Value |
|---|---|
| **Priority** | P3 |
| **Preconditions** | Visit with status "CHECKED_IN". |
| **Steps** | 1. POST with { additionalMinutes: 10, reason: "Test" } (below minimum 15). 2. POST with { additionalMinutes: 1500, reason: "Test" } (above maximum 1440). |
| **Expected Result** | Both return validation errors about the allowed range. |

### TC-VMS-EXTEND-008: Validation -- reason is required
| Field | Value |
|---|---|
| **Priority** | P3 |
| **Preconditions** | Visit with status "CHECKED_IN". |
| **Steps** | 1. POST with { additionalMinutes: 60 } (no reason). |
| **Expected Result** | Validation error: `Reason is required`. |

---

## 11. Watchlist & Blocklist (TC-VMS-WATCH-*)

### TC-VMS-WATCH-001: Create blocklist entry
| Field | Value |
|---|---|
| **Priority** | P1 |
| **Preconditions** | Logged in as Security Manager or Company Admin. |
| **Steps** | 1. POST /visitors/watchlist with { type: "BLOCKLIST", personName: "Bad Actor", mobileNumber: "9999999999", reason: "Security incident", blockDuration: "PERMANENT", appliesToAllPlants: true }. |
| **Expected Result** | Entry created with type "BLOCKLIST", isActive=true. |

### TC-VMS-WATCH-002: Create watchlist entry
| Field | Value |
|---|---|
| **Priority** | P1 |
| **Preconditions** | Logged in as Security Manager. |
| **Steps** | 1. POST /visitors/watchlist with { type: "WATCHLIST", personName: "Watch Person", mobileNumber: "8888888888", reason: "Previous minor incident", blockDuration: "UNTIL_DATE", expiryDate: "2026-12-31" }. |
| **Expected Result** | Entry created with type "WATCHLIST", expiryDate set. |

### TC-VMS-WATCH-003: Check visitor against lists -- blocklist match
| Field | Value |
|---|---|
| **Priority** | P1 |
| **Preconditions** | Blocklist entry for mobile "9999999999" exists. |
| **Steps** | 1. POST /visitors/watchlist/check with { mobile: "9999999999" }. |
| **Expected Result** | Response: { blocklisted: true, watchlisted: false, matches: [entry] }. |

### TC-VMS-WATCH-004: Check visitor against lists -- watchlist match
| Field | Value |
|---|---|
| **Priority** | P1 |
| **Preconditions** | Watchlist entry for mobile "8888888888" exists. |
| **Steps** | 1. POST /visitors/watchlist/check with { mobile: "8888888888" }. |
| **Expected Result** | Response: { blocklisted: false, watchlisted: true, matches: [entry] }. |

### TC-VMS-WATCH-005: Expired UNTIL_DATE entry not matched
| Field | Value |
|---|---|
| **Priority** | P1 |
| **Preconditions** | Watchlist entry with blockDuration "UNTIL_DATE" and expiryDate in the past. |
| **Steps** | 1. POST /visitors/watchlist/check with the matching mobile. |
| **Expected Result** | Response: { blocklisted: false, watchlisted: false, matches: [] }. Expired entry filtered out. |

### TC-VMS-WATCH-006: Check with no criteria
| Field | Value |
|---|---|
| **Priority** | P3 |
| **Preconditions** | None. |
| **Steps** | 1. POST /visitors/watchlist/check with empty object {}. |
| **Expected Result** | Response: { blocklisted: false, watchlisted: false, matches: [] }. No error. |

### TC-VMS-WATCH-007: Check by name (fuzzy match)
| Field | Value |
|---|---|
| **Priority** | P2 |
| **Preconditions** | Blocklist entry with personName "Bad Actor". |
| **Steps** | 1. POST /visitors/watchlist/check with { name: "Bad" }. |
| **Expected Result** | Match found (case-insensitive contains search on personName). |

### TC-VMS-WATCH-008: Check by ID number
| Field | Value |
|---|---|
| **Priority** | P2 |
| **Preconditions** | Blocklist entry with idNumber "AADHAAR123". |
| **Steps** | 1. POST /visitors/watchlist/check with { idNumber: "AADHAAR123" }. |
| **Expected Result** | Match found. |

### TC-VMS-WATCH-009: Update watchlist entry
| Field | Value |
|---|---|
| **Priority** | P2 |
| **Preconditions** | Watchlist entry exists. |
| **Steps** | 1. PUT /visitors/watchlist/:id with { reason: "Updated reason", expiryDate: "2027-06-30" }. |
| **Expected Result** | Entry updated. reason and expiryDate reflect new values. |

### TC-VMS-WATCH-010: Remove (soft-delete) watchlist entry
| Field | Value |
|---|---|
| **Priority** | P2 |
| **Preconditions** | Active watchlist entry exists. |
| **Steps** | 1. DELETE /visitors/watchlist/:id. |
| **Expected Result** | Entry isActive set to false. No longer matches in checks. |

### TC-VMS-WATCH-011: List watchlist entries with filters
| Field | Value |
|---|---|
| **Priority** | P2 |
| **Preconditions** | Multiple blocklist and watchlist entries exist. |
| **Steps** | 1. GET /visitors/watchlist?type=BLOCKLIST. 2. GET /visitors/watchlist?type=WATCHLIST. 3. GET /visitors/watchlist?search=Bad. |
| **Expected Result** | Each query returns correctly filtered results. Search matches personName, mobileNumber, or idNumber. |

### TC-VMS-WATCH-012: Create blocklist entry with plant-specific scope
| Field | Value |
|---|---|
| **Priority** | P3 |
| **Preconditions** | Two plants exist. |
| **Steps** | 1. POST /visitors/watchlist with { type: "BLOCKLIST", personName: "Plant Specific", mobileNumber: "7777777777", reason: "Incident at Plant A", blockDuration: "PERMANENT", appliesToAllPlants: false, plantIds: ["{plantAId}"] }. |
| **Expected Result** | Entry created with appliesToAllPlants=false and plantIds containing only Plant A's ID. |

---

## 12. Denied Entries (TC-VMS-DENIED-*)

### TC-VMS-DENIED-001: Denied entry created on blocklist match during check-in
| Field | Value |
|---|---|
| **Priority** | P1 |
| **Preconditions** | Visit exists. Blocklist entry matches the visitor's mobile. |
| **Steps** | 1. Attempt to check in the visitor. 2. Query denied entries. |
| **Expected Result** | DeniedEntry record created with denialReason: "BLOCKLIST_MATCH", denialDetails: "Blocklist match detected during check-in", visitId linked, plantId set, deniedBy set to the guard. |

### TC-VMS-DENIED-002: Denied entry created on host rejection
| Field | Value |
|---|---|
| **Priority** | P1 |
| **Preconditions** | Visit with approvalStatus "PENDING". |
| **Steps** | 1. POST /visitors/visits/:id/reject with { notes: "Not authorized" }. 2. Query denied entries. |
| **Expected Result** | DeniedEntry record created with denialReason: "HOST_REJECTED", denialDetails: "Not authorized", visitId linked, deniedBy set to the rejecting user. |

### TC-VMS-DENIED-003: List denied entries with filters
| Field | Value |
|---|---|
| **Priority** | P2 |
| **Preconditions** | Multiple denied entries exist. |
| **Steps** | 1. GET /visitors/denied-entries?denialReason=HOST_REJECTED. 2. GET /visitors/denied-entries?fromDate=2026-04-01&toDate=2026-04-30. 3. GET /visitors/denied-entries?search=Bad. |
| **Expected Result** | Each query returns correctly filtered, paginated results. Results include visit and watchlistEntry relations. Ordered by deniedAt desc. |

### TC-VMS-DENIED-004: Denied entry includes full context
| Field | Value |
|---|---|
| **Priority** | P2 |
| **Preconditions** | A denied entry exists. |
| **Steps** | 1. GET /visitors/denied-entries/:id. |
| **Expected Result** | Response includes: visitorName, visitorMobile, visitorCompany, denialReason, denialDetails, visit (relation), watchlistEntry (relation if applicable), plantId, deniedBy, deniedAt. |

### TC-VMS-DENIED-005: Get non-existent denied entry
| Field | Value |
|---|---|
| **Priority** | P3 |
| **Preconditions** | Random UUID. |
| **Steps** | 1. GET /visitors/denied-entries/{randomId}. |
| **Expected Result** | Error: `Denied entry not found` (HTTP 404). |

---

## 13. Dashboard (TC-VMS-DASH-*)

### TC-VMS-DASH-001: Today's stats show correct counts
| Field | Value |
|---|---|
| **Priority** | P1 |
| **Preconditions** | Today: 3 visits expected, 2 checked in, 1 checked out, 1 on-site, 1 walk-in, 0 no-shows. |
| **Steps** | 1. GET /visitors/dashboard/today. |
| **Expected Result** | Response contains paginated today's visitors list and correct today stats: totalExpected, checkedIn, checkedOut, onSiteNow, walkIns, noShows, overstaying. All counts match the prepared test data. |

### TC-VMS-DASH-002: On-site visitors list is accurate
| Field | Value |
|---|---|
| **Priority** | P1 |
| **Preconditions** | 2 visitors currently checked in (status CHECKED_IN). |
| **Steps** | 1. GET /visitors/dashboard/on-site. |
| **Expected Result** | Returns exactly 2 visitors. Each includes visitorType and checkInGate relations. Ordered by checkInTime desc. |

### TC-VMS-DASH-003: Overstaying visitors flagged correctly
| Field | Value |
|---|---|
| **Priority** | P1 |
| **Preconditions** | Visitor A checked in 3 hours ago with expectedDurationMinutes=120 (overstaying). Visitor B checked in 30 minutes ago with expectedDurationMinutes=120 (not overstaying). |
| **Steps** | 1. GET /visitors/dashboard/today (check overstaying stat). |
| **Expected Result** | overstaying count is 1 (only Visitor A). |

### TC-VMS-DASH-004: Filter by plant
| Field | Value |
|---|---|
| **Priority** | P2 |
| **Preconditions** | Visits exist for Plant A and Plant B. |
| **Steps** | 1. GET /visitors/dashboard/today?plantId={plantAId}. |
| **Expected Result** | Only visits for Plant A are counted in stats and listed. |

### TC-VMS-DASH-005: Monthly stats (KPI)
| Field | Value |
|---|---|
| **Priority** | P2 |
| **Preconditions** | Multiple visits exist this month with various statuses. |
| **Steps** | 1. GET /visitors/dashboard/stats. |
| **Expected Result** | Response includes: totalVisitsThisMonth, avgDailyVisitors, avgVisitDurationMinutes, preRegisteredPercent, walkInPercent, overstayRate, safetyInductionCompletionRate. All percentages are 0-100. |

### TC-VMS-DASH-006: Dashboard with no visits today
| Field | Value |
|---|---|
| **Priority** | P3 |
| **Preconditions** | No visits for today. |
| **Steps** | 1. GET /visitors/dashboard/today. |
| **Expected Result** | All stats are 0. Empty visitors list. No errors. |

### TC-VMS-DASH-007: Dashboard uses company timezone
| Field | Value |
|---|---|
| **Priority** | P2 |
| **Preconditions** | Company timezone set to "America/New_York". Visit created for today in that timezone. |
| **Steps** | 1. GET /visitors/dashboard/today. |
| **Expected Result** | "Today" is calculated using the company's timezone, not UTC. If it is 11 PM in New York but 3 AM next day UTC, the visit for "today in New York" is included. |

### TC-VMS-DASH-008: On-site visitors with plant filter
| Field | Value |
|---|---|
| **Priority** | P3 |
| **Preconditions** | Checked-in visitors at both plants. |
| **Steps** | 1. GET /visitors/dashboard/on-site?plantId={plantAId}. |
| **Expected Result** | Only on-site visitors at Plant A returned. |

---

## 14. Recurring Passes (TC-VMS-PASS-*)

### TC-VMS-PASS-001: Create recurring pass
| Field | Value |
|---|---|
| **Priority** | P1 |
| **Preconditions** | Host employee, plant exist. Number series configured for "Recurring Visitor Pass". |
| **Steps** | 1. POST /visitors/recurring-passes with { visitorName, visitorCompany, visitorMobile, passType: "MONTHLY", validFrom: "2026-04-01", validUntil: "2026-04-30", allowedDays: [1,2,3,4,5], allowedTimeFrom: "09:00", allowedTimeTo: "18:00", hostEmployeeId, purpose, plantId }. |
| **Expected Result** | Pass created with status "ACTIVE". passNumber generated from number series. All fields saved correctly. |

### TC-VMS-PASS-002: Check in via recurring pass
| Field | Value |
|---|---|
| **Priority** | P1 |
| **Preconditions** | Active pass exists. Today is within valid dates and allowed days. |
| **Steps** | 1. POST /visitors/recurring-passes/:id/check-in with { gateId: "{gateId}" }. |
| **Expected Result** | A new Visit record created linked to the pass (recurringPassId set). Visit status is "CHECKED_IN". visitNumber and badgeNumber generated. registrationMethod is "PRE_REGISTERED". approvalStatus is "AUTO_APPROVED". |

### TC-VMS-PASS-003: Check in outside valid dates
| Field | Value |
|---|---|
| **Priority** | P1 |
| **Preconditions** | Pass with validFrom in the future OR validUntil in the past. |
| **Steps** | 1. Attempt check-in via pass. |
| **Expected Result** | Error: `Pass is outside its validity period` (HTTP 400). |

### TC-VMS-PASS-004: Check in on non-allowed day
| Field | Value |
|---|---|
| **Priority** | P1 |
| **Preconditions** | Pass with allowedDays: [1,2,3,4,5] (Mon-Fri). Today is Saturday (6) or Sunday (0). |
| **Steps** | 1. Attempt check-in via pass. |
| **Expected Result** | Error: `Pass is not valid for today` (HTTP 400). |

### TC-VMS-PASS-005: Check in at non-allowed gate
| Field | Value |
|---|---|
| **Priority** | P2 |
| **Preconditions** | Pass with allowedGateIds: [gateA]. Attempting check-in at gateB. |
| **Steps** | 1. POST /visitors/recurring-passes/:id/check-in with { gateId: "{gateBId}" }. |
| **Expected Result** | Error: `Pass is not valid for this gate` (HTTP 400). |

### TC-VMS-PASS-006: Revoke pass
| Field | Value |
|---|---|
| **Priority** | P1 |
| **Preconditions** | Active pass exists. |
| **Steps** | 1. POST /visitors/recurring-passes/:id/revoke with { reason: "No longer needed" }. |
| **Expected Result** | Pass status changed to "REVOKED". revokedAt and revokedBy populated. revokeReason saved. |

### TC-VMS-PASS-007: Check in with revoked pass
| Field | Value |
|---|---|
| **Priority** | P1 |
| **Preconditions** | Pass with status "REVOKED". |
| **Steps** | 1. Attempt check-in via pass. |
| **Expected Result** | Error: `Pass is not active` (HTTP 400). |

### TC-VMS-PASS-008: Update active pass
| Field | Value |
|---|---|
| **Priority** | P2 |
| **Preconditions** | Active pass exists. |
| **Steps** | 1. PUT /visitors/recurring-passes/:id with { validUntil: "2026-05-31" }. |
| **Expected Result** | validUntil extended. |

### TC-VMS-PASS-009: Cannot update revoked pass
| Field | Value |
|---|---|
| **Priority** | P2 |
| **Preconditions** | Revoked pass exists. |
| **Steps** | 1. PUT /visitors/recurring-passes/:id with any update. |
| **Expected Result** | Error: `Can only update active passes` (HTTP 400). |

### TC-VMS-PASS-010: List passes with status filter
| Field | Value |
|---|---|
| **Priority** | P2 |
| **Preconditions** | Active and revoked passes exist. |
| **Steps** | 1. GET /visitors/recurring-passes?status=ACTIVE. 2. GET /visitors/recurring-passes?status=REVOKED. |
| **Expected Result** | Each query returns only passes with the specified status. |

### TC-VMS-PASS-011: Pass with empty allowedDays allows all days
| Field | Value |
|---|---|
| **Priority** | P3 |
| **Preconditions** | Pass with allowedDays: [] (empty). |
| **Steps** | 1. Attempt check-in any day of the week. |
| **Expected Result** | Check-in succeeds. Empty allowedDays means all days are permitted. |

### TC-VMS-PASS-012: Pass with empty allowedGateIds allows all gates
| Field | Value |
|---|---|
| **Priority** | P3 |
| **Preconditions** | Pass with allowedGateIds: [] (empty). |
| **Steps** | 1. Attempt check-in at any gate. |
| **Expected Result** | Check-in succeeds. Empty allowedGateIds means all gates are permitted. |

---

## 15. Group Visits (TC-VMS-GROUP-*)

### TC-VMS-GROUP-001: Create group visit with members
| Field | Value |
|---|---|
| **Priority** | P1 |
| **Preconditions** | Host employee, plant exist. |
| **Steps** | 1. POST /visitors/group-visits with { groupName: "ABC Corp Audit Team", hostEmployeeId, purpose: "Annual audit", expectedDate: "2026-04-15", expectedTime: "10:00", plantId, members: [{visitorName: "Alice", visitorMobile: "9000000001"}, {visitorName: "Bob", visitorMobile: "9000000002"}, {visitorName: "Carol", visitorMobile: "9000000003"}] }. |
| **Expected Result** | GroupVisit created with status "PLANNED". visitCode starts with "G-" followed by 6 chars. totalMembers=3. 3 GroupVisitMember records created, each with status "EXPECTED". |

### TC-VMS-GROUP-002: Minimum 2 members required
| Field | Value |
|---|---|
| **Priority** | P2 |
| **Preconditions** | None. |
| **Steps** | 1. POST /visitors/group-visits with only 1 member in the members array. |
| **Expected Result** | Validation error: `Group visit requires at least 2 members`. |

### TC-VMS-GROUP-003: Maximum 100 members
| Field | Value |
|---|---|
| **Priority** | P3 |
| **Preconditions** | None. |
| **Steps** | 1. POST /visitors/group-visits with 101 members. |
| **Expected Result** | Validation error about exceeding max 100 members. |

### TC-VMS-GROUP-004: Batch check-in selected members
| Field | Value |
|---|---|
| **Priority** | P1 |
| **Preconditions** | Group visit with 3 members, all EXPECTED. Number series configured. |
| **Steps** | 1. POST /visitors/group-visits/:id/check-in with { memberIds: [member1Id, member2Id], checkInGateId: "{gateId}" }. |
| **Expected Result** | 2 individual Visit records created (one per member), each with status "CHECKED_IN", badgeNumber generated, groupVisitId set. GroupVisitMember records for member1 and member2 updated to status "CHECKED_IN" with visitId linked. Group status changed to "IN_PROGRESS". Member3 remains "EXPECTED". |

### TC-VMS-GROUP-005: Batch check-out all members
| Field | Value |
|---|---|
| **Priority** | P1 |
| **Preconditions** | Group visit with 2 members checked in. |
| **Steps** | 1. POST /visitors/group-visits/:id/check-out with { checkOutMethod: "SECURITY_DESK" } (no memberIds -- checks out all). |
| **Expected Result** | Both members' visits checked out. GroupVisitMember statuses changed to "CHECKED_OUT". If all members are done (CHECKED_OUT or NO_SHOW), group status changes to "COMPLETED". |

### TC-VMS-GROUP-006: Batch check-out selected members
| Field | Value |
|---|---|
| **Priority** | P2 |
| **Preconditions** | Group visit with 3 members checked in. |
| **Steps** | 1. POST /visitors/group-visits/:id/check-out with { memberIds: [member1Id], checkOutMethod: "SECURITY_DESK" }. |
| **Expected Result** | Only member1 checked out. member2 and member3 remain CHECKED_IN. Group status stays "IN_PROGRESS". |

### TC-VMS-GROUP-007: Update planned group visit
| Field | Value |
|---|---|
| **Priority** | P2 |
| **Preconditions** | Group visit with status "PLANNED". |
| **Steps** | 1. PUT /visitors/group-visits/:id with { groupName: "Updated Name", expectedDate: "2026-04-20" }. |
| **Expected Result** | Group name and date updated. |

### TC-VMS-GROUP-008: Cannot update non-planned group visit
| Field | Value |
|---|---|
| **Priority** | P2 |
| **Preconditions** | Group visit with status "IN_PROGRESS". |
| **Steps** | 1. PUT /visitors/group-visits/:id with { groupName: "New Name" }. |
| **Expected Result** | Error: `Can only update planned group visits` (HTTP 400). |

### TC-VMS-GROUP-009: List group visits with filters
| Field | Value |
|---|---|
| **Priority** | P2 |
| **Preconditions** | Multiple group visits exist. |
| **Steps** | 1. GET /visitors/group-visits?status=PLANNED. 2. GET /visitors/group-visits?search=ABC. 3. GET /visitors/group-visits?fromDate=2026-04-01&toDate=2026-04-30. |
| **Expected Result** | Each query returns correctly filtered results with members included. |

### TC-VMS-GROUP-010: Get group visit by ID with member details
| Field | Value |
|---|---|
| **Priority** | P2 |
| **Preconditions** | Group visit exists with members (some checked in). |
| **Steps** | 1. GET /visitors/group-visits/:id. |
| **Expected Result** | Response includes members array, each member includes their visit (if linked). |

---

## 16. Vehicle Gate Pass (TC-VMS-VEHICLE-*)

### TC-VMS-VEHICLE-001: Create vehicle pass
| Field | Value |
|---|---|
| **Priority** | P1 |
| **Preconditions** | Gate, plant exist. Number series configured for "Vehicle Gate Pass". |
| **Steps** | 1. POST /visitors/vehicle-passes with { vehicleRegNumber: "KA-01-AB-1234", vehicleType: "TRUCK", driverName: "Ramesh Kumar", driverMobile: "9100000001", purpose: "Raw material delivery", entryGateId, plantId }. |
| **Expected Result** | Vehicle pass created. passNumber generated from number series. entryTime auto-set to now. exitTime is null. Includes entryGate relation. |

### TC-VMS-VEHICLE-002: Record vehicle exit
| Field | Value |
|---|---|
| **Priority** | P1 |
| **Preconditions** | Vehicle pass exists with exitTime=null. |
| **Steps** | 1. POST /visitors/vehicle-passes/:id/exit with { exitGateId: "{gateId}" }. |
| **Expected Result** | exitGateId set. exitTime populated. Response includes both entryGate and exitGate relations. |

### TC-VMS-VEHICLE-003: Duplicate exit attempt
| Field | Value |
|---|---|
| **Priority** | P2 |
| **Preconditions** | Vehicle pass already has exitTime. |
| **Steps** | 1. POST /visitors/vehicle-passes/:id/exit with valid data. |
| **Expected Result** | Error: `Vehicle has already exited` (HTTP 409). |

### TC-VMS-VEHICLE-004: List with date filter
| Field | Value |
|---|---|
| **Priority** | P2 |
| **Preconditions** | Vehicle passes exist across multiple dates. |
| **Steps** | 1. GET /visitors/vehicle-passes?fromDate=2026-04-01&toDate=2026-04-13. |
| **Expected Result** | Only passes with entryTime within the date range returned. |

### TC-VMS-VEHICLE-005: Search by vehicle registration number
| Field | Value |
|---|---|
| **Priority** | P2 |
| **Preconditions** | Vehicle pass with regNumber "KA-01-AB-1234" exists. |
| **Steps** | 1. GET /visitors/vehicle-passes?search=KA-01. |
| **Expected Result** | Pass found. Search matches vehicleRegNumber, driverName, and passNumber. |

### TC-VMS-VEHICLE-006: Create vehicle pass linked to a visit
| Field | Value |
|---|---|
| **Priority** | P3 |
| **Preconditions** | A visit exists. |
| **Steps** | 1. POST /visitors/vehicle-passes with visitId set to the visit's ID. |
| **Expected Result** | Vehicle pass created with visitId linked. |

### TC-VMS-VEHICLE-007: All vehicle types accepted
| Field | Value |
|---|---|
| **Priority** | P3 |
| **Preconditions** | None. |
| **Steps** | 1. Create passes with each vehicleType: CAR, TWO_WHEELER, AUTO, TRUCK, VAN, TEMPO, BUS. |
| **Expected Result** | All 7 vehicle types accepted. |

---

## 17. Material Gate Pass (TC-VMS-MATERIAL-*)

### TC-VMS-MATERIAL-001: Create inward material pass
| Field | Value |
|---|---|
| **Priority** | P1 |
| **Preconditions** | Gate, plant exist. Number series configured. |
| **Steps** | 1. POST /visitors/material-passes with { type: "INWARD", description: "Spare parts for CNC machine", quantityIssued: "5 boxes", authorizedBy: "{employeeId}", purpose: "Maintenance", gateId, plantId }. |
| **Expected Result** | Pass created. returnStatus automatically set to "NOT_APPLICABLE" (not INWARD type -- actually, INWARD does not need return). passNumber generated. |

### TC-VMS-MATERIAL-002: Create returnable material pass
| Field | Value |
|---|---|
| **Priority** | P1 |
| **Preconditions** | Gate, plant exist. |
| **Steps** | 1. POST /visitors/material-passes with { type: "RETURNABLE", description: "Testing equipment", quantityIssued: "3 units", authorizedBy, purpose: "Quality testing", expectedReturnDate: "2026-04-20", gateId, plantId }. |
| **Expected Result** | Pass created. returnStatus automatically set to "PENDING" (because type is RETURNABLE). |

### TC-VMS-MATERIAL-003: Create outward material pass
| Field | Value |
|---|---|
| **Priority** | P2 |
| **Preconditions** | Gate, plant exist. |
| **Steps** | 1. POST /visitors/material-passes with { type: "OUTWARD", description: "Sample products", authorizedBy, purpose: "Client samples", gateId, plantId }. |
| **Expected Result** | Pass created. returnStatus is "NOT_APPLICABLE". |

### TC-VMS-MATERIAL-004: Mark partial return
| Field | Value |
|---|---|
| **Priority** | P1 |
| **Preconditions** | Returnable material pass with returnStatus "PENDING". |
| **Steps** | 1. POST /visitors/material-passes/:id/return with { quantityReturned: "2 of 3 units", returnStatus: "PARTIAL" }. |
| **Expected Result** | returnStatus changed to "PARTIAL". quantityReturned saved. returnedAt is null (partial). |

### TC-VMS-MATERIAL-005: Mark full return
| Field | Value |
|---|---|
| **Priority** | P1 |
| **Preconditions** | Returnable material pass with returnStatus "PENDING" or "PARTIAL". |
| **Steps** | 1. POST /visitors/material-passes/:id/return with { quantityReturned: "3 of 3 units", returnStatus: "FULLY_RETURNED" }. |
| **Expected Result** | returnStatus changed to "FULLY_RETURNED". returnedAt timestamp populated. |

### TC-VMS-MATERIAL-006: Cannot return already fully returned pass
| Field | Value |
|---|---|
| **Priority** | P2 |
| **Preconditions** | Material pass with returnStatus "FULLY_RETURNED". |
| **Steps** | 1. POST /visitors/material-passes/:id/return. |
| **Expected Result** | Error: `Material has already been fully returned` (HTTP 409). |

### TC-VMS-MATERIAL-007: Cannot return non-returnable pass
| Field | Value |
|---|---|
| **Priority** | P2 |
| **Preconditions** | Material pass with type "INWARD" (returnStatus "NOT_APPLICABLE"). |
| **Steps** | 1. POST /visitors/material-passes/:id/return. |
| **Expected Result** | Error: `This pass does not require a return` (HTTP 400). |

### TC-VMS-MATERIAL-008: List material passes with type filter
| Field | Value |
|---|---|
| **Priority** | P2 |
| **Preconditions** | Passes of all three types exist. |
| **Steps** | 1. GET /visitors/material-passes?type=RETURNABLE. 2. GET /visitors/material-passes?returnStatus=PENDING. |
| **Expected Result** | Correctly filtered results. |

---

## 18. Emergency Muster (TC-VMS-EMERGENCY-*)

### TC-VMS-EMERGENCY-001: Trigger emergency
| Field | Value |
|---|---|
| **Priority** | P1 |
| **Preconditions** | 3 visitors currently checked in at Plant A. User has visitors:configure permission. |
| **Steps** | 1. POST /visitors/emergency/trigger with { plantId: "{plantAId}", isDrill: false }. |
| **Expected Result** | Response includes: emergency=true, isDrill=false, totalOnSite=3, musterList with 3 entries each containing: id, visitorName, visitorCompany, visitorPhoto, visitorType, badgeNumber, hostEmployeeId, checkInTime, checkInGate, marshalStatus="UNKNOWN". Notifications dispatched to all on-site visitors. |

### TC-VMS-EMERGENCY-002: Trigger emergency drill
| Field | Value |
|---|---|
| **Priority** | P2 |
| **Preconditions** | Visitors checked in. |
| **Steps** | 1. POST /visitors/emergency/trigger with { plantId, isDrill: true }. |
| **Expected Result** | Response same as real emergency but isDrill=true. Notifications NOT dispatched (drill mode skips notification). |

### TC-VMS-EMERGENCY-003: Get muster list
| Field | Value |
|---|---|
| **Priority** | P1 |
| **Preconditions** | Visitors currently checked in at the plant. |
| **Steps** | 1. GET /visitors/emergency/muster-list?plantId={plantId}. |
| **Expected Result** | List of all on-site visitors with: id, visitorName, visitorCompany, visitorPhoto, visitorType, badgeColour, badgeNumber, hostEmployeeId, checkInTime, checkInGate, visitorMobile. |

### TC-VMS-EMERGENCY-004: Mark visitors as safe
| Field | Value |
|---|---|
| **Priority** | P1 |
| **Preconditions** | Emergency triggered. On-site visitors exist. |
| **Steps** | 1. POST /visitors/emergency/mark-safe with { visitIds: [visitor1Id, visitor2Id], plantId }. |
| **Expected Result** | Response: { markedSafe: 2, visitors: [{id, visitorName}, {id, visitorName}] }. Event logged. |

### TC-VMS-EMERGENCY-005: Mark safe with invalid visit IDs
| Field | Value |
|---|---|
| **Priority** | P2 |
| **Preconditions** | Emergency active. |
| **Steps** | 1. POST /visitors/emergency/mark-safe with { visitIds: [randomUUID], plantId }. |
| **Expected Result** | Error: `No valid checked-in visits found for the provided IDs` (HTTP 400). |

### TC-VMS-EMERGENCY-006: Resolve emergency
| Field | Value |
|---|---|
| **Priority** | P1 |
| **Preconditions** | Emergency was triggered. |
| **Steps** | 1. POST /visitors/emergency/resolve with { plantId }. |
| **Expected Result** | Response: { resolved: true, resolvedAt: timestamp }. Event logged. |

### TC-VMS-EMERGENCY-007: Permission -- only configure can trigger/resolve
| Field | Value |
|---|---|
| **Priority** | P2 |
| **Preconditions** | User with visitors:read but NOT visitors:configure. |
| **Steps** | 1. POST /visitors/emergency/trigger. 2. POST /visitors/emergency/resolve. |
| **Expected Result** | Both return HTTP 403 Forbidden. |

### TC-VMS-EMERGENCY-008: Guard can mark safe but not trigger
| Field | Value |
|---|---|
| **Priority** | P2 |
| **Preconditions** | User with visitors:create but NOT visitors:configure. |
| **Steps** | 1. POST /visitors/emergency/mark-safe with valid data. |
| **Expected Result** | Succeeds (visitors:create permission is sufficient for mark-safe). |

---

## 19. Reports (TC-VMS-REPORTS-*)

### TC-VMS-REPORTS-001: Daily visitor log
| Field | Value |
|---|---|
| **Priority** | P1 |
| **Preconditions** | Visits exist for 2026-04-13. |
| **Steps** | 1. GET /visitors/reports/daily-log?date=2026-04-13. |
| **Expected Result** | Returns all visits for that date, ordered by checkInTime asc. Includes visitorType, checkInGate, checkOutGate relations. |

### TC-VMS-REPORTS-002: Daily log filtered by plant
| Field | Value |
|---|---|
| **Priority** | P2 |
| **Preconditions** | Visits at multiple plants on the same date. |
| **Steps** | 1. GET /visitors/reports/daily-log?date=2026-04-13&plantId={plantAId}. |
| **Expected Result** | Only visits at Plant A returned. |

### TC-VMS-REPORTS-003: Summary report
| Field | Value |
|---|---|
| **Priority** | P1 |
| **Preconditions** | Visits exist within the date range. |
| **Steps** | 1. GET /visitors/reports/summary?fromDate=2026-04-01&toDate=2026-04-13. |
| **Expected Result** | Response includes: totalVisits, byType (grouped counts), byMethod (PRE_REGISTERED / WALK_IN counts), byStatus (grouped counts), avgDurationMinutes. |

### TC-VMS-REPORTS-004: Overstay report
| Field | Value |
|---|---|
| **Priority** | P1 |
| **Preconditions** | Some completed visits had visitDurationMinutes > expectedDurationMinutes. |
| **Steps** | 1. GET /visitors/reports/overstay?fromDate=2026-04-01&toDate=2026-04-13. |
| **Expected Result** | Returns only visits where actual duration exceeded expected duration. Each includes visitorType. |

### TC-VMS-REPORTS-005: Analytics dashboard data
| Field | Value |
|---|---|
| **Priority** | P2 |
| **Preconditions** | Visits exist within the date range. |
| **Steps** | 1. GET /visitors/reports/analytics?fromDate=2026-04-01&toDate=2026-04-13. |
| **Expected Result** | Response includes: totalVisits, avgDurationMinutes, preRegisteredPercent, overstayRatePercent, safetyInductionCompletionPercent. All percentages are 0-100. |

### TC-VMS-REPORTS-006: Permission -- export permission required for daily-log/summary/overstay
| Field | Value |
|---|---|
| **Priority** | P2 |
| **Preconditions** | User with visitors:read but NOT visitors:export. |
| **Steps** | 1. GET /visitors/reports/daily-log. 2. GET /visitors/reports/summary. 3. GET /visitors/reports/overstay. |
| **Expected Result** | All three return HTTP 403. These require visitors:export permission. |

### TC-VMS-REPORTS-007: Analytics only requires read permission
| Field | Value |
|---|---|
| **Priority** | P2 |
| **Preconditions** | User with visitors:read. |
| **Steps** | 1. GET /visitors/reports/analytics?fromDate=2026-04-01&toDate=2026-04-13. |
| **Expected Result** | Succeeds (visitors:read is sufficient for analytics). |

### TC-VMS-REPORTS-008: Empty date range returns zero counts
| Field | Value |
|---|---|
| **Priority** | P3 |
| **Preconditions** | No visits in the specified date range. |
| **Steps** | 1. GET /visitors/reports/summary?fromDate=2020-01-01&toDate=2020-01-31. |
| **Expected Result** | totalVisits=0, all grouped counts empty, avgDurationMinutes=null. No errors. |

---

## 20. Public Endpoints (TC-VMS-PUBLIC-*)

### TC-VMS-PUBLIC-001: Get visit by code (pre-arrival form)
| Field | Value |
|---|---|
| **Priority** | P1 |
| **Preconditions** | Pre-registered visit exists with known visitCode. No authentication. |
| **Steps** | 1. GET /public/visit/{visitCode}. |
| **Expected Result** | Response includes: visitCode, visitorName, visitorEmail, visitorCompany, expectedDate, expectedTime, purpose, status, approvalStatus, visitorType (name, code, badgeColour, requirePhoto, requireIdVerification, requireNda), company (name, displayName, logoUrl). Does NOT include sensitive fields like hostEmployeeId or internal IDs. |

### TC-VMS-PUBLIC-002: Submit pre-arrival form
| Field | Value |
|---|---|
| **Priority** | P1 |
| **Preconditions** | Visit with status "EXPECTED" and known visitCode. |
| **Steps** | 1. POST /public/visit/{visitCode}/pre-arrival with { visitorPhoto: "https://example.com/photo.jpg", governmentIdType: "AADHAAR", governmentIdNumber: "1234-5678-9012", vehicleRegNumber: "KA-01-AB-5678", emergencyContact: "9876543210", ndaSigned: true }. |
| **Expected Result** | Response: { success: true, message: "Pre-arrival information submitted successfully." }. Fields saved on the visit record. |

### TC-VMS-PUBLIC-003: Submit pre-arrival form for non-EXPECTED visit
| Field | Value |
|---|---|
| **Priority** | P2 |
| **Preconditions** | Visit with status "CHECKED_IN". |
| **Steps** | 1. POST /public/visit/{visitCode}/pre-arrival with valid data. |
| **Expected Result** | Error: `This visit is no longer accepting pre-arrival information` (HTTP 400). |

### TC-VMS-PUBLIC-004: Self-registration config -- enabled
| Field | Value |
|---|---|
| **Priority** | P1 |
| **Preconditions** | VMS config has qrSelfRegistrationEnabled=true. Plant with known code. |
| **Steps** | 1. GET /public/visit/register/{plantCode}. |
| **Expected Result** | Response includes: company info (name, displayName, logoUrl), plant info (id, name, code), visitorTypes (active types list), config (photoRequired, privacyConsentText). |

### TC-VMS-PUBLIC-005: Self-registration config -- disabled
| Field | Value |
|---|---|
| **Priority** | P1 |
| **Preconditions** | VMS config has qrSelfRegistrationEnabled=false. |
| **Steps** | 1. GET /public/visit/register/{plantCode}. |
| **Expected Result** | Error: `Self-registration is not enabled at this facility` (HTTP 400). |

### TC-VMS-PUBLIC-006: Self-registration config -- invalid plant code
| Field | Value |
|---|---|
| **Priority** | P2 |
| **Preconditions** | No plant with code "INVALID". |
| **Steps** | 1. GET /public/visit/register/INVALID. |
| **Expected Result** | Error: `Facility not found. Please check the QR code.` (HTTP 404). |

### TC-VMS-PUBLIC-007: Submit self-registration
| Field | Value |
|---|---|
| **Priority** | P1 |
| **Preconditions** | qrSelfRegistrationEnabled=true. Active plant, active employee, active visitor types. |
| **Steps** | 1. POST /public/visit/register/{plantCode} with { visitorName: "Self Reg Visitor", visitorMobile: "9111111111", visitorCompany: "Vendor Corp", purpose: "MEETING", hostEmployeeName: "{firstName of an active employee}" }. |
| **Expected Result** | Response includes: visitCode (6 chars), message: "Registration submitted. Waiting for host approval.", hostName: "{employee full name}". Visit created internally with registrationMethod "PRE_REGISTERED" (via visitService.createVisit). |

### TC-VMS-PUBLIC-008: Self-registration -- host employee not found
| Field | Value |
|---|---|
| **Priority** | P2 |
| **Preconditions** | No employee with the given name at the company. |
| **Steps** | 1. POST /public/visit/register/{plantCode} with { hostEmployeeName: "NonExistent Person", ... }. |
| **Expected Result** | Error: `Could not find employee "NonExistent Person". Please contact the facility reception.` (HTTP 400). |

### TC-VMS-PUBLIC-009: Check visit status
| Field | Value |
|---|---|
| **Priority** | P1 |
| **Preconditions** | Visit exists with known visitCode. |
| **Steps** | 1. GET /public/visit/{visitCode}/status. |
| **Expected Result** | Response includes: visitCode, visitorName, status, approvalStatus, expectedDate, expectedTime. |

### TC-VMS-PUBLIC-010: View digital badge -- active visit
| Field | Value |
|---|---|
| **Priority** | P1 |
| **Preconditions** | Visit with status "CHECKED_IN" and known visitCode. |
| **Steps** | 1. GET /public/visit/{visitCode}/badge. |
| **Expected Result** | Response status: "ACTIVE", includes: visitorName, visitorCompany, badgeNumber, visitorType, company, checkInTime, expectedDurationMinutes, qrCodeData (the visit code). |

### TC-VMS-PUBLIC-011: View digital badge -- not yet started
| Field | Value |
|---|---|
| **Priority** | P2 |
| **Preconditions** | Visit with status "EXPECTED". |
| **Steps** | 1. GET /public/visit/{visitCode}/badge. |
| **Expected Result** | Response status: "NOT_STARTED", message: "Visit not yet started. Please check in at the gate." |

### TC-VMS-PUBLIC-012: View digital badge -- ended visit
| Field | Value |
|---|---|
| **Priority** | P2 |
| **Preconditions** | Visit with status "CHECKED_OUT". |
| **Steps** | 1. GET /public/visit/{visitCode}/badge. |
| **Expected Result** | Response status: "ENDED", message: "Visit ended.", includes: visitorName, visitDate. |

### TC-VMS-PUBLIC-013: View digital badge -- cancelled/rejected visit
| Field | Value |
|---|---|
| **Priority** | P2 |
| **Preconditions** | Visit with status "CANCELLED" or "REJECTED". |
| **Steps** | 1. GET /public/visit/{visitCode}/badge. |
| **Expected Result** | Response status: "CANCELLED", message: "This visit has been cancelled." |

### TC-VMS-PUBLIC-014: Self check-out
| Field | Value |
|---|---|
| **Priority** | P1 |
| **Preconditions** | Visit with status "CHECKED_IN" and known visitCode. |
| **Steps** | 1. POST /public/visit/{visitCode}/check-out. |
| **Expected Result** | Response: { message: "You have been checked out. Thank you for visiting!", checkOutTime, visitDurationMinutes }. Visit status changed to "CHECKED_OUT". checkOutMethod set to "MOBILE_LINK". |

### TC-VMS-PUBLIC-015: Self check-out -- not checked in
| Field | Value |
|---|---|
| **Priority** | P2 |
| **Preconditions** | Visit with status "EXPECTED". |
| **Steps** | 1. POST /public/visit/{visitCode}/check-out. |
| **Expected Result** | Error: `This visit is not currently checked in` (HTTP 400). |

### TC-VMS-PUBLIC-016: Self check-out -- already checked out
| Field | Value |
|---|---|
| **Priority** | P2 |
| **Preconditions** | Visit with status "CHECKED_OUT". |
| **Steps** | 1. POST /public/visit/{visitCode}/check-out. |
| **Expected Result** | Error: `This visit is not currently checked in` (HTTP 400). |

### TC-VMS-PUBLIC-017: Invalid visit code on all public endpoints
| Field | Value |
|---|---|
| **Priority** | P1 |
| **Preconditions** | No visit with code "ZZZZZZ". |
| **Steps** | 1. GET /public/visit/ZZZZZZ. 2. POST /public/visit/ZZZZZZ/pre-arrival. 3. GET /public/visit/ZZZZZZ/status. 4. GET /public/visit/ZZZZZZ/badge. 5. POST /public/visit/ZZZZZZ/check-out. |
| **Expected Result** | All return: `Visit not found` or `Visit not found. Please check your visit code.` (HTTP 404). |

### TC-VMS-PUBLIC-018: Self-registration validation errors
| Field | Value |
|---|---|
| **Priority** | P2 |
| **Preconditions** | None. |
| **Steps** | 1. POST /public/visit/register/{plantCode} with empty body. 2. POST with visitorName only (missing visitorMobile, purpose, hostEmployeeName). 3. POST with visitorMobile < 10 chars. 4. POST with visitorName > 200 chars. |
| **Expected Result** | Each returns HTTP 400 with specific validation error messages. |

---

## 21. Permissions & RBAC (TC-VMS-RBAC-*)

### TC-VMS-RBAC-001: Security Guard can check-in and check-out
| Field | Value |
|---|---|
| **Priority** | P1 |
| **Preconditions** | User with visitors:read and visitors:create permissions. |
| **Steps** | 1. GET /visitors/visits (read). 2. POST /visitors/visits/:id/check-in (create). 3. POST /visitors/visits/:id/check-out (create). |
| **Expected Result** | All three succeed. |

### TC-VMS-RBAC-002: Security Guard cannot configure
| Field | Value |
|---|---|
| **Priority** | P1 |
| **Preconditions** | User with visitors:read and visitors:create only (no configure). |
| **Steps** | 1. POST /visitors/types (configure). 2. PUT /visitors/config (configure). 3. POST /visitors/emergency/trigger (configure). |
| **Expected Result** | All three return HTTP 403 Forbidden. |

### TC-VMS-RBAC-003: Security Manager has full access
| Field | Value |
|---|---|
| **Priority** | P1 |
| **Preconditions** | User with visitors:* (all permissions). |
| **Steps** | 1. Create visitor type. 2. Create gate. 3. Create visit. 4. Check in. 5. Check out. 6. Approve/reject. 7. Manage watchlist. 8. Trigger emergency. 9. View reports. 10. Export reports. |
| **Expected Result** | All operations succeed. |

### TC-VMS-RBAC-004: Company Admin can configure everything
| Field | Value |
|---|---|
| **Priority** | P1 |
| **Preconditions** | Company admin user. |
| **Steps** | 1. CRUD on visitor types. 2. CRUD on gates. 3. Update VMS config. 4. CRUD on safety inductions. 5. Manage watchlist. |
| **Expected Result** | All configuration operations succeed. |

### TC-VMS-RBAC-005: User without VMS subscription sees no sidebar items
| Field | Value |
|---|---|
| **Priority** | P2 |
| **Preconditions** | Company does not have VMS/visitors module subscription active. |
| **Steps** | 1. GET /rbac/navigation-manifest as a user of that company. |
| **Expected Result** | No VMS-related sidebar items appear. Module suppression hides all visitor-related entries. |

### TC-VMS-RBAC-006: Approve permission specifically required for approval endpoints
| Field | Value |
|---|---|
| **Priority** | P2 |
| **Preconditions** | User with visitors:create but NOT visitors:approve. |
| **Steps** | 1. POST /visitors/visits/:id/approve. 2. POST /visitors/visits/:id/reject. |
| **Expected Result** | Both return HTTP 403. Approval requires visitors:approve specifically. |

### TC-VMS-RBAC-007: Export permission required for report exports
| Field | Value |
|---|---|
| **Priority** | P2 |
| **Preconditions** | User with visitors:read but NOT visitors:export. |
| **Steps** | 1. GET /visitors/reports/daily-log. 2. GET /visitors/reports/summary. 3. GET /visitors/reports/overstay. |
| **Expected Result** | All return HTTP 403. Export permission required. |

### TC-VMS-RBAC-008: Read permission sufficient for analytics
| Field | Value |
|---|---|
| **Priority** | P2 |
| **Preconditions** | User with visitors:read only. |
| **Steps** | 1. GET /visitors/reports/analytics. 2. GET /visitors/dashboard/today. 3. GET /visitors/dashboard/on-site. |
| **Expected Result** | All succeed. Read permission sufficient for dashboard and analytics. |

---

## 22. Cross-Module Integration (TC-VMS-INTEG-*)

### TC-VMS-INTEG-001: Host employee lookup uses Employee Master
| Field | Value |
|---|---|
| **Priority** | P1 |
| **Preconditions** | Employees exist in Employee Master for this company. |
| **Steps** | 1. Create a pre-registration with a valid hostEmployeeId from Employee Master. 2. Create with an ID from a different company. |
| **Expected Result** | First succeeds. Second fails with "Host employee not found" (employee validated against companyId). |

### TC-VMS-INTEG-002: Plant/location from Location Master
| Field | Value |
|---|---|
| **Priority** | P1 |
| **Preconditions** | Locations exist for the company. |
| **Steps** | 1. Create visit with valid plantId. 2. Create with plantId from another company. |
| **Expected Result** | First succeeds. Second fails with "Plant/location not found" (location validated against companyId). |

### TC-VMS-INTEG-003: Number series generates correct format
| Field | Value |
|---|---|
| **Priority** | P1 |
| **Preconditions** | Number series configured for Visitor Registration with prefix "VIS-" and padding 5. |
| **Steps** | 1. Create a visit. 2. Check the visitNumber field. 3. Create another visit. 4. Check the visitNumber field. |
| **Expected Result** | First: "VIS-00001". Second: "VIS-00002". Sequential, atomic increment. |

### TC-VMS-INTEG-004: Number series not configured -- clear error
| Field | Value |
|---|---|
| **Priority** | P1 |
| **Preconditions** | No number series configured for "Visitor Registration" or "Visitor". |
| **Steps** | 1. Attempt to create a visit. |
| **Expected Result** | Error with user-friendly message indicating the number series for Visitor Registration is not configured. Admin needs to set it up in Number Series Config. |

### TC-VMS-INTEG-005: Notification dispatch on key events
| Field | Value |
|---|---|
| **Priority** | P2 |
| **Preconditions** | Notification service running. |
| **Steps** | 1. Create visit (triggers VMS_PRE_REGISTRATION_CREATED). 2. Check in (triggers VMS_VISITOR_CHECKED_IN). 3. Check out (triggers VMS_VISITOR_CHECKED_OUT). 4. Trigger emergency (triggers VMS_EMERGENCY_EVACUATION for all on-site visitors). |
| **Expected Result** | All four trigger events dispatch notifications. Failures logged as warnings but do not block the operation. |

### TC-VMS-INTEG-006: Self-registration uses employee fuzzy search
| Field | Value |
|---|---|
| **Priority** | P2 |
| **Preconditions** | Employee "John Smith" exists. |
| **Steps** | 1. POST /public/visit/register/{plantCode} with hostEmployeeName: "John". |
| **Expected Result** | Employee matched by firstName containing "John" (case-insensitive). First match used as host. Visit created. |

### TC-VMS-INTEG-007: Self-registration with inactive employee status
| Field | Value |
|---|---|
| **Priority** | P3 |
| **Preconditions** | Only employee matching the name is in TERMINATED or RESIGNED status. |
| **Steps** | 1. POST /public/visit/register/{plantCode} with that employee's name. |
| **Expected Result** | Error: `Could not find employee...`. Service only searches employees with status ACTIVE, PROBATION, or CONFIRMED. |

---

## 23. Edge Cases & Error Handling (TC-VMS-EDGE-*)

### TC-VMS-EDGE-001: Very long visitor name (200 chars)
| Field | Value |
|---|---|
| **Priority** | P2 |
| **Preconditions** | None. |
| **Steps** | 1. Create visit with visitorName of exactly 200 characters. 2. Create visit with visitorName of 201 characters. |
| **Expected Result** | 200 chars succeeds. 201 chars returns validation error (max 200). |

### TC-VMS-EDGE-002: Special characters in visitor name
| Field | Value |
|---|---|
| **Priority** | P2 |
| **Preconditions** | None. |
| **Steps** | 1. Create visit with visitorName: "O'Brien-Smith, Jr.". 2. Create with visitorName containing unicode: "Sato Yuki". |
| **Expected Result** | Both succeed. Names stored correctly with special characters preserved. |

### TC-VMS-EDGE-003: International phone numbers
| Field | Value |
|---|---|
| **Priority** | P2 |
| **Preconditions** | None. |
| **Steps** | 1. Create visit with visitorMobile: "+919876543210" (Indian, 13 chars). 2. Create with visitorMobile: "+14155551234" (US, 12 chars). 3. Create with visitorMobile: "9876543210" (10 chars, no country code). |
| **Expected Result** | All succeed. Mobile stored as-is. Min 10, max 15 characters validation. |

### TC-VMS-EDGE-004: Phone number too short
| Field | Value |
|---|---|
| **Priority** | P3 |
| **Preconditions** | None. |
| **Steps** | 1. Create visit with visitorMobile: "12345" (5 chars). |
| **Expected Result** | Validation error: `Valid mobile number required` (min 10 chars). |

### TC-VMS-EDGE-005: Multiple concurrent visit creations
| Field | Value |
|---|---|
| **Priority** | P2 |
| **Preconditions** | Valid data for visit creation. |
| **Steps** | 1. Send 5 simultaneous POST /visitors/visits requests. |
| **Expected Result** | All 5 succeed with unique visitCodes and visitNumbers. No collisions due to atomic number series generation and retry logic for visit codes. |

### TC-VMS-EDGE-006: Visit code collision retry
| Field | Value |
|---|---|
| **Priority** | P3 |
| **Preconditions** | Extremely unlikely -- requires millions of existing codes. |
| **Steps** | 1. (Theoretical) The code generator retries up to 3 times on collision. |
| **Expected Result** | After 3 failed attempts, returns: `Unable to generate unique visit code. Please try again.` (HTTP 409). |

### TC-VMS-EDGE-007: Empty search string returns all results
| Field | Value |
|---|---|
| **Priority** | P3 |
| **Preconditions** | Multiple visits exist. |
| **Steps** | 1. GET /visitors/visits?search=. |
| **Expected Result** | Empty search string is treated as no search filter. All visits returned (paginated). |

### TC-VMS-EDGE-008: Invalid UUID format for IDs
| Field | Value |
|---|---|
| **Priority** | P3 |
| **Preconditions** | None. |
| **Steps** | 1. GET /visitors/visits/not-a-valid-uuid. 2. POST /visitors/visits/not-a-valid-uuid/check-in. |
| **Expected Result** | Returns "Visit not found" (HTTP 404) or Prisma client error handled gracefully. No 500 server errors. |

### TC-VMS-EDGE-009: Large page/limit values
| Field | Value |
|---|---|
| **Priority** | P3 |
| **Preconditions** | None. |
| **Steps** | 1. GET /visitors/visits?page=1&limit=100 (max allowed). 2. GET /visitors/visits?page=1&limit=101 (exceeds max). |
| **Expected Result** | limit=100 succeeds. limit=101 returns validation error (max 100). |

### TC-VMS-EDGE-010: Trimming whitespace in string inputs
| Field | Value |
|---|---|
| **Priority** | P3 |
| **Preconditions** | None. |
| **Steps** | 1. Create visit with visitorName: "  John Doe  " (leading/trailing spaces). |
| **Expected Result** | visitorName stored as "John Doe" (trimmed). Validators use trimString preprocessor. |

### TC-VMS-EDGE-011: Invalid hex colour for badge
| Field | Value |
|---|---|
| **Priority** | P3 |
| **Preconditions** | None. |
| **Steps** | 1. Create visitor type with badgeColour: "red" (not hex). 2. Create with badgeColour: "#GGG" (invalid hex). |
| **Expected Result** | Both return validation error: `Must be a hex colour`. Only #RRGGBB format accepted. |

### TC-VMS-EDGE-012: Cross-company data isolation
| Field | Value |
|---|---|
| **Priority** | P1 |
| **Preconditions** | Two companies (A and B) each with visits. |
| **Steps** | 1. As Company A admin, GET /visitors/visits. 2. As Company A admin, GET /visitors/visits/{companyBVisitId}. |
| **Expected Result** | First returns only Company A visits. Second returns "Visit not found" (HTTP 404) -- visit belongs to Company B, filtered by companyId. |

### TC-VMS-EDGE-013: Deactivated gate still shows in historical visit records
| Field | Value |
|---|---|
| **Priority** | P3 |
| **Preconditions** | Visit was checked in at Gate A. Gate A is then deactivated. |
| **Steps** | 1. GET /visitors/visits/:id (the historical visit). |
| **Expected Result** | checkInGate relation still shows Gate A's data. Historical references preserved even when gate is deactivated. |

### TC-VMS-EDGE-014: Email validation on optional fields
| Field | Value |
|---|---|
| **Priority** | P3 |
| **Preconditions** | None. |
| **Steps** | 1. Create visit with visitorEmail: "not-an-email". 2. Create visit with visitorEmail: "valid@email.com". 3. Create visit without visitorEmail (optional). |
| **Expected Result** | First returns validation error. Second and third succeed. |

### TC-VMS-EDGE-015: Purpose enum validation
| Field | Value |
|---|---|
| **Priority** | P2 |
| **Preconditions** | None. |
| **Steps** | 1. Create visit with purpose: "MEETING" (valid). 2. Create with purpose: "INVALID_PURPOSE". |
| **Expected Result** | First succeeds. Second returns validation error. Valid values: MEETING, DELIVERY, MAINTENANCE, AUDIT, INTERVIEW, SITE_TOUR, PERSONAL, OTHER. |

### TC-VMS-EDGE-016: URL validation for photo fields
| Field | Value |
|---|---|
| **Priority** | P3 |
| **Preconditions** | None. |
| **Steps** | 1. Check in with visitorPhoto: "not-a-url". 2. Check in with visitorPhoto: "https://example.com/photo.jpg" (valid). |
| **Expected Result** | First returns validation error. Second succeeds. |

### TC-VMS-EDGE-017: Concurrent approval and rejection
| Field | Value |
|---|---|
| **Priority** | P2 |
| **Preconditions** | Visit with approvalStatus "PENDING". |
| **Steps** | 1. Simultaneously send approve and reject requests. |
| **Expected Result** | One succeeds, the other returns "Visit is already approved/rejected" error. No inconsistent state. |

---

## Test Execution Summary Template

| Section | Total TCs | P1 | P2 | P3 | Pass | Fail | Blocked | Notes |
|---------|-----------|----|----|----|----- |------|---------|-------|
| 1. Visitor Types | 10 | 3 | 5 | 2 | | | | |
| 2. Gates | 8 | 2 | 3 | 3 | | | | |
| 3. Safety Induction Config | 6 | 2 | 3 | 1 | | | | |
| 4. VMS Configuration | 5 | 2 | 2 | 1 | | | | |
| 5. Pre-Registration | 25 | 14 | 8 | 3 | | | | |
| 6. Check-In | 14 | 6 | 5 | 3 | | | | |
| 7. Check-Out | 9 | 3 | 3 | 3 | | | | |
| 8. Approval Workflow | 7 | 3 | 3 | 1 | | | | |
| 9. Safety Induction | 6 | 3 | 2 | 1 | | | | |
| 10. Visit Extension | 8 | 3 | 3 | 2 | | | | |
| 11. Watchlist/Blocklist | 12 | 4 | 5 | 3 | | | | |
| 12. Denied Entries | 5 | 2 | 2 | 1 | | | | |
| 13. Dashboard | 8 | 3 | 3 | 2 | | | | |
| 14. Recurring Passes | 12 | 5 | 4 | 3 | | | | |
| 15. Group Visits | 10 | 3 | 5 | 2 | | | | |
| 16. Vehicle Gate Pass | 7 | 2 | 3 | 2 | | | | |
| 17. Material Gate Pass | 8 | 3 | 3 | 2 | | | | |
| 18. Emergency Muster | 8 | 3 | 4 | 1 | | | | |
| 19. Reports | 8 | 3 | 4 | 1 | | | | |
| 20. Public Endpoints | 18 | 7 | 8 | 3 | | | | |
| 21. Permissions & RBAC | 8 | 3 | 5 | 0 | | | | |
| 22. Cross-Module Integration | 7 | 3 | 3 | 1 | | | | |
| 23. Edge Cases | 17 | 1 | 5 | 11 | | | | |
| **TOTAL** | **226** | **83** | **91** | **52** | | | | |

---

## API Endpoint Quick Reference

| Method | Endpoint | Permission | Section |
|--------|----------|------------|---------|
| GET | /visitors/types | visitors:configure | Visitor Types |
| POST | /visitors/types | visitors:configure | Visitor Types |
| GET | /visitors/types/:id | visitors:configure | Visitor Types |
| PUT | /visitors/types/:id | visitors:configure | Visitor Types |
| DELETE | /visitors/types/:id | visitors:configure | Visitor Types |
| GET | /visitors/gates | visitors:configure | Gates |
| POST | /visitors/gates | visitors:configure | Gates |
| GET | /visitors/gates/:id | visitors:configure | Gates |
| PUT | /visitors/gates/:id | visitors:configure | Gates |
| DELETE | /visitors/gates/:id | visitors:configure | Gates |
| GET | /visitors/safety-inductions | visitors:configure | Safety Induction |
| POST | /visitors/safety-inductions | visitors:configure | Safety Induction |
| PUT | /visitors/safety-inductions/:id | visitors:configure | Safety Induction |
| DELETE | /visitors/safety-inductions/:id | visitors:configure | Safety Induction |
| GET | /visitors/config | visitors:configure | VMS Config |
| PUT | /visitors/config | visitors:configure | VMS Config |
| GET | /visitors/visits | visitors:read | Visits |
| POST | /visitors/visits | visitors:create | Visits |
| GET | /visitors/visits/code/:visitCode | visitors:read | Visits |
| GET | /visitors/visits/:id | visitors:read | Visits |
| PUT | /visitors/visits/:id | visitors:update | Visits |
| DELETE | /visitors/visits/:id | visitors:delete | Visits |
| POST | /visitors/visits/:id/check-in | visitors:create | Check-In |
| POST | /visitors/visits/:id/check-out | visitors:create | Check-Out |
| POST | /visitors/visits/:id/approve | visitors:approve | Approval |
| POST | /visitors/visits/:id/reject | visitors:approve | Approval |
| POST | /visitors/visits/:id/extend | visitors:update | Extension |
| POST | /visitors/visits/:id/complete-induction | visitors:create | Induction |
| GET | /visitors/watchlist | visitors:read | Watchlist |
| POST | /visitors/watchlist | visitors:create | Watchlist |
| PUT | /visitors/watchlist/:id | visitors:update | Watchlist |
| DELETE | /visitors/watchlist/:id | visitors:delete | Watchlist |
| POST | /visitors/watchlist/check | visitors:read | Watchlist |
| GET | /visitors/denied-entries | visitors:read | Denied Entries |
| GET | /visitors/denied-entries/:id | visitors:read | Denied Entries |
| GET | /visitors/recurring-passes | visitors:read | Recurring Passes |
| POST | /visitors/recurring-passes | visitors:create | Recurring Passes |
| GET | /visitors/recurring-passes/:id | visitors:read | Recurring Passes |
| PUT | /visitors/recurring-passes/:id | visitors:update | Recurring Passes |
| POST | /visitors/recurring-passes/:id/revoke | visitors:update | Recurring Passes |
| POST | /visitors/recurring-passes/:id/check-in | visitors:create | Recurring Passes |
| GET | /visitors/vehicle-passes | visitors:read | Vehicle Pass |
| POST | /visitors/vehicle-passes | visitors:create | Vehicle Pass |
| GET | /visitors/vehicle-passes/:id | visitors:read | Vehicle Pass |
| POST | /visitors/vehicle-passes/:id/exit | visitors:update | Vehicle Pass |
| GET | /visitors/material-passes | visitors:read | Material Pass |
| POST | /visitors/material-passes | visitors:create | Material Pass |
| GET | /visitors/material-passes/:id | visitors:read | Material Pass |
| POST | /visitors/material-passes/:id/return | visitors:update | Material Pass |
| GET | /visitors/group-visits | visitors:read | Group Visits |
| POST | /visitors/group-visits | visitors:create | Group Visits |
| GET | /visitors/group-visits/:id | visitors:read | Group Visits |
| PUT | /visitors/group-visits/:id | visitors:update | Group Visits |
| POST | /visitors/group-visits/:id/check-in | visitors:create | Group Visits |
| POST | /visitors/group-visits/:id/check-out | visitors:create | Group Visits |
| GET | /visitors/dashboard/today | visitors:read | Dashboard |
| GET | /visitors/dashboard/on-site | visitors:read | Dashboard |
| GET | /visitors/dashboard/stats | visitors:read | Dashboard |
| POST | /visitors/emergency/trigger | visitors:configure | Emergency |
| GET | /visitors/emergency/muster-list | visitors:read | Emergency |
| POST | /visitors/emergency/mark-safe | visitors:create | Emergency |
| POST | /visitors/emergency/resolve | visitors:configure | Emergency |
| GET | /visitors/reports/daily-log | visitors:export | Reports |
| GET | /visitors/reports/summary | visitors:export | Reports |
| GET | /visitors/reports/overstay | visitors:export | Reports |
| GET | /visitors/reports/analytics | visitors:read | Reports |
| GET | /public/visit/:visitCode | (none) | Public |
| POST | /public/visit/:visitCode/pre-arrival | (none) | Public |
| GET | /public/visit/register/:plantCode | (none) | Public |
| POST | /public/visit/register/:plantCode | (none) | Public |
| GET | /public/visit/:visitCode/status | (none) | Public |
| GET | /public/visit/:visitCode/badge | (none) | Public |
| POST | /public/visit/:visitCode/check-out | (none) | Public |
