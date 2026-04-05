# Recruitment & Training Enhancement — Design Spec

**Date:** 2026-04-05
**Status:** Approved
**Scope:** Backend (avy-erp-backend) + Web (web-system-app) + Mobile (mobile-app)

---

## Table of Contents

1. [Current State Summary](#1-current-state-summary)
2. [Verified Gaps](#2-verified-gaps)
3. [Cross-Cutting Concerns](#3-cross-cutting-concerns)
4. [Phase 1 — Data Integrity & Indexes](#4-phase-1--data-integrity--indexes)
5. [Phase 2 — Recruitment Enhancements](#5-phase-2--recruitment-enhancements)
6. [Phase 3 — Training Enhancements](#6-phase-3--training-enhancements)
7. [Phase 4 — Advanced Features](#7-phase-4--advanced-features)
8. [State Machine Transitions](#8-state-machine-transitions)
9. [Permission Matrix](#9-permission-matrix)
10. [Notification Flows](#10-notification-flows)
11. [Event System](#11-event-system)
12. [Audit Trail](#12-audit-trail)
13. [Aggregation & Performance](#13-aggregation--performance)
14. [Scope Summary](#14-scope-summary)

---

## 1. Current State Summary

### Existing Models

| Model | File | Fields | Purpose |
|-------|------|--------|---------|
| `JobRequisition` | `recruitment.prisma` | requisitionNumber, title, designationId, departmentId, openings, description, budgetMin/Max, targetDate, sourceChannels, status, approvedBy | Job opening tracking |
| `Candidate` | `recruitment.prisma` | name, email, phone, source, currentCtc, expectedCtc, resumeUrl, stage, rating, notes | Applicant management |
| `Interview` | `recruitment.prisma` | candidateId, round, panelists, scheduledAt, duration, meetingLink, feedbackRating, feedbackNotes, status | Interview scheduling & feedback |
| `TrainingCatalogue` | `training.prisma` | catalogueNumber, name, type, mode, duration, linkedSkillIds, proficiencyGain, mandatory, certificationName/Body/Validity, vendorProvider, costPerHead, isActive | Training program definitions |
| `TrainingNomination` | `training.prisma` | employeeId, trainingId, status, completionDate, score, certificateUrl | Employee training assignments |

### Existing Enums

- `RequisitionStatus`: DRAFT, OPEN, INTERVIEWING, OFFERED, FILLED, CANCELLED
- `CandidateStage`: APPLIED, SHORTLISTED, HR_ROUND, TECHNICAL, FINAL, ASSESSMENT, OFFER_SENT, HIRED, REJECTED, ON_HOLD
- `InterviewStatus`: SCHEDULED, COMPLETED, CANCELLED, NO_SHOW
- `TrainingMode`: ONLINE, CLASSROOM, WORKSHOP, EXTERNAL, BLENDED, ON_THE_JOB
- `TrainingNominationStatus`: NOMINATED, ENROLLED, COMPLETED, CANCELLED

### Existing Endpoints

- Requisitions: 6 endpoints (CRUD + status)
- Candidates: 6 endpoints (CRUD + stage advance)
- Interviews: 7 endpoints (CRUD + complete/cancel)
- Training Catalogues: 5 endpoints (CRUD)
- Training Nominations: 6 endpoints (CRUD + complete)
- Dashboards: 2 endpoints (recruitment + training)
- ESS: 1 endpoint (my-training)

### Existing Screens

- Web: RequisitionScreen (3 tabs), TrainingCatalogueScreen (2 tabs), MyTrainingScreen, RecruitmentDashboardScreen
- Mobile: RequisitionsScreen (3 tabs), TrainingScreen (2 tabs), MyTrainingScreen, RecruitmentDashboardScreen

---

## 2. Verified Gaps

### Recruitment Gaps

| ID | Gap | Details |
|----|-----|---------|
| R1 | No Offer Management | No Offer model, no offer CRUD, no acceptance/rejection workflow |
| R2 | No Candidate Education & Experience | Only name, email, phone, source, CTC, resumeUrl |
| R3 | No Structured Interview Evaluation | Only feedbackRating (0-10) + feedbackNotes text |
| R4 | No Candidate Stage History | Stage updated in-place, no audit trail of transitions |
| R5 | No Candidate Documents | Single resumeUrl string, no multi-document support |
| R6 | No Candidate-to-Employee Conversion | Manual employee creation, no auto-population |
| R7 | Interview Complete/Cancel missing from UI | Backend has endpoints, web/mobile don't wire them |
| R8 | Candidate Delete missing from UI | Backend has endpoint, web/mobile don't wire it |
| R9 | Requisition Detail Fields missing | Web form sends employmentType, priority, location, requirements — backend drops them |
| R10 | Web-Backend Field Mismatch | Multiple form fields silently dropped by backend |

### Training Gaps

| ID | Gap | Details |
|----|-----|---------|
| T1 | No Training Sessions | Cannot schedule when/where trainings run |
| T2 | No Training Attendance | No per-session attendance records |
| T3 | No Training Evaluation/Feedback | Only score field on nomination |
| T4 | No Certificate Lifecycle | No issuance date, expiry, renewal tracking |
| T5 | No Trainer Management | Only vendorProvider string |
| T6 | No Training Programs/Learning Paths | Individual catalogues only |
| T7 | No Training Materials | No course content management |
| T8 | No Training Budget Tracking | Only costPerHead on catalogue |
| T9 | No Training Dashboard Screen | Backend/hooks exist, no UI component |
| T10 | System Controls not gating nav items | recruitmentEnabled/trainingEnabled not in NAV_TO_SYSTEM_MODULE |

### Data Integrity Issues

| ID | Issue | Details |
|----|-------|---------|
| D1 | Web form fields dropped by backend | employmentType, priority, location, requirements sent but not persisted |
| D2 | Candidate name handling mismatch | Web splits first/last, backend uses single name |
| D3 | Interview type vs round mismatch | Web sends type, mobile sends number, backend expects string |
| D4 | Training nomination status mismatch | Web shows APPROVED/IN_PROGRESS, enum lacks them |
| D5 | No DB indexes | Missing indexes on high-frequency query columns |

---

## 3. Cross-Cutting Concerns

These apply across ALL phases and are built incrementally.

### 3.1 State Machine (CC1)

Generic utility: `src/shared/utils/state-machine.ts`

```typescript
function validateTransition<T extends string>(
  currentState: T,
  newState: T,
  allowedTransitions: Record<T, T[]>,
  entityName: string,
): void
// Throws ApiError.badRequest() on invalid transition
```

Every status update endpoint calls this before persisting. See [Section 8](#8-state-machine-transitions) for all transition maps.

### 3.2 Cross-Module Linking (CC2)

Closed-loop HR system flows:

1. **Candidate HIRED + Offer ACCEPTED → Employee created** (Phase 2)
2. **New Employee → Auto-assign mandatory trainings**: On employee creation, query `TrainingCatalogue` where `mandatory = true`, auto-create nominations
3. **Training COMPLETED → Update Employee Skills**: Enhance existing skill auto-mapping. Use evaluation `postAssessmentScore` to determine proficiency level (80+ → level 4, 60-79 → level 3, etc.)
4. **Offer → Payroll linkage**: `CandidateOffer.ctcBreakup` passed through during candidate→employee conversion to pre-populate salary structure
5. **Skills gap → Training recommendation**: Dashboard query matching `SkillMapping.currentLevel < requiredLevel` with `TrainingCatalogue.linkedSkillIds` to suggest relevant trainings

### 3.3 Aggregation Layer (CC3)

See [Section 13](#13-aggregation--performance).

### 3.4 Audit Trail (CC4)

See [Section 12](#12-audit-trail).

### 3.5 Permission Granularity (CC5)

See [Section 9](#9-permission-matrix).

### 3.6 UX Tab Grouping (CC6)

Candidate Detail Screen uses grouped sections instead of flat tabs:

- **Profile card** (always visible): Name, email, phone, source, rating, stage badge
- **Tab Group 1 — Background**: Education, Experience, Documents
- **Tab Group 2 — Hiring Pipeline**: Interviews (with evaluations), Offers, Stage History (timeline)

Web: sidebar + content layout. Mobile: scrollable tab bar with section headers.

### 3.7 Notifications (CC7)

See [Section 10](#10-notification-flows).

### 3.8 Event System (CC8)

See [Section 11](#11-event-system).

---

## 4. Phase 1 — Data Integrity & Indexes

**Goal:** Fix mismatches between frontend forms and backend schema, add DB indexes, wire missing UI actions.

### 4.1 JobRequisition Schema Enhancement

Add fields to `recruitment.prisma` → `JobRequisition`:

```prisma
employmentType  EmploymentType?
priority        RequisitionPriority?
location        String?
requirements    String?
experienceMin   Int?
experienceMax   Int?
```

New enums:

```prisma
enum EmploymentType {
  FULL_TIME
  PART_TIME
  CONTRACT
  INTERNSHIP
}

enum RequisitionPriority {
  LOW
  MEDIUM
  HIGH
  URGENT
}
```

Update `createRequisitionSchema` and `updateRequisitionSchema` in validators. Update service to persist all fields. Update mobile form to include employmentType, priority, location, requirements, experienceMin/Max.

### 4.2 Training Nomination Status Enum Fix

Add `APPROVED` and `IN_PROGRESS` to `TrainingNominationStatus`:

```prisma
enum TrainingNominationStatus {
  NOMINATED
  APPROVED
  IN_PROGRESS
  COMPLETED
  CANCELLED
}
```

Workflow: NOMINATED → APPROVED → IN_PROGRESS → COMPLETED (or CANCELLED from any except COMPLETED).

Update validators, service status handling, and mobile UI to match.

### 4.3 DB Indexes

```prisma
// recruitment.prisma
model JobRequisition {
  @@index([companyId, status])
}
model Candidate {
  @@index([companyId, stage])
  @@index([requisitionId, stage])
  @@index([email])
}
model Interview {
  @@index([companyId, status])
  @@index([candidateId, status])
  @@index([scheduledAt])
}

// training.prisma
model TrainingCatalogue {
  @@index([companyId, isActive])
}
model TrainingNomination {
  @@index([companyId, status])
  @@index([employeeId, status])
}
```

### 4.4 Wire Missing UI Actions

**Web + Mobile:**
- Add **Complete Interview** button (calls `PATCH /interviews/:id/complete`) — prompts for feedbackRating + feedbackNotes
- Add **Cancel Interview** button (calls `PATCH /interviews/:id/cancel`) — with confirmation modal
- Add **Delete Candidate** button (calls `DELETE /candidates/:id`) — with confirmation modal

**Candidate name fix:** Keep single `name` field in backend. Fix web form to use single name input instead of split first/last.

**Interview round fix:** Standardize to string field. Web sends interview type label (Phone, Video, Technical, etc.) directly as `round`. Mobile updated to match.

### 4.5 System Controls Nav Gating

Add to `NAV_TO_SYSTEM_MODULE` in `rbac.service.ts`:

```typescript
'hr-requisitions': 'recruitmentEnabled',
'hr-candidates': 'recruitmentEnabled',
'hr-analytics-recruitment': 'recruitmentEnabled',
'hr-training': 'trainingEnabled',
'hr-nominations': 'trainingEnabled',
'ess-training': 'trainingEnabled',
```

### 4.6 State Machine Utility

Create `src/shared/utils/state-machine.ts` with generic `validateTransition()`. Wire into existing `updateRequisitionStatus` and `advanceCandidateStage` service methods.

---

## 5. Phase 2 — Recruitment Enhancements

**Goal:** Offer management, candidate profile enrichment, structured evaluations, stage history, candidate-to-employee conversion.

### 5.1 Offer Management

**New model: `CandidateOffer`** in `recruitment.prisma`

```prisma
model CandidateOffer {
  id              String      @id @default(cuid())
  offerNumber     String?
  candidateId     String
  candidate       Candidate   @relation(fields: [candidateId], references: [id], onDelete: Cascade)
  designationId   String?
  designation     Designation? @relation(fields: [designationId], references: [id])
  departmentId    String?
  department      Department? @relation(fields: [departmentId], references: [id])
  offeredCtc      Decimal     @db.Decimal(15, 2)
  ctcBreakup      Json?
  joiningDate     DateTime?   @db.Date
  offerLetterUrl  String?
  validUntil      DateTime?   @db.Date
  status          OfferStatus @default(DRAFT)
  acceptedAt      DateTime?
  rejectedAt      DateTime?
  rejectionReason String?
  withdrawnAt     DateTime?
  notes           String?
  companyId       String
  company         Company     @relation(fields: [companyId], references: [id], onDelete: Cascade)
  createdAt       DateTime    @default(now())
  updatedAt       DateTime    @updatedAt

  @@index([companyId, status])
  @@index([candidateId])
  @@map("candidate_offers")
}

enum OfferStatus {
  DRAFT
  SENT
  ACCEPTED
  REJECTED
  WITHDRAWN
  EXPIRED
}
```

**Number Series:** Add `'Offer Management'` to `linked-screens.ts` with defaultPrefix `'OFF-'`.

**Endpoints:**

| Method | Path | Permission | Purpose |
|--------|------|-----------|---------|
| GET | `/hr/offers` | `recruitment-offer:read` | List with filters (candidateId, status) |
| POST | `/hr/offers` | `recruitment-offer:create` | Create offer for candidate |
| GET | `/hr/offers/:id` | `recruitment-offer:read` | Get offer details |
| PATCH | `/hr/offers/:id` | `recruitment-offer:update` | Update draft offer |
| PATCH | `/hr/offers/:id/status` | `recruitment-offer:approve` | Send / Accept / Reject / Withdraw |
| DELETE | `/hr/offers/:id` | `recruitment-offer:delete` | Delete (DRAFT only) |

**State transitions:** DRAFT → SENT → ACCEPTED / REJECTED / EXPIRED. WITHDRAWN from DRAFT or SENT only.

**Side effects:**
- Offer SENT → emit `offer.sent` event → notification to hiring manager
- Offer ACCEPTED → emit `offer.accepted` → auto-advance candidate stage to HIRED
- Offer EXPIRED → checked lazily on read (if `validUntil < now()` and status = SENT, update to EXPIRED)

**UI:** New "Offers" tab in RequisitionScreen (web) and RequisitionsScreen (mobile). Offer cards show candidate name, offered CTC, joining date, status badge, validity countdown.

### 5.2 Candidate Profile Enrichment

**New models** in `recruitment.prisma`:

```prisma
model CandidateEducation {
  id            String    @id @default(cuid())
  candidateId   String
  candidate     Candidate @relation(fields: [candidateId], references: [id], onDelete: Cascade)
  qualification String
  degree        String?
  institution   String?
  university    String?
  yearOfPassing Int?
  percentage    Decimal?  @db.Decimal(5, 2)
  certificateUrl String?
  companyId     String
  company       Company   @relation(fields: [companyId], references: [id], onDelete: Cascade)
  createdAt     DateTime  @default(now())
  updatedAt     DateTime  @updatedAt

  @@index([candidateId])
  @@map("candidate_education")
}

model CandidateExperience {
  id              String    @id @default(cuid())
  candidateId     String
  candidate       Candidate @relation(fields: [candidateId], references: [id], onDelete: Cascade)
  companyName     String
  designation     String
  fromDate        DateTime? @db.Date
  toDate          DateTime? @db.Date
  currentlyWorking Boolean  @default(false)
  ctc             Decimal?  @db.Decimal(15, 2)
  description     String?
  companyId       String
  company         Company   @relation(fields: [companyId], references: [id], onDelete: Cascade)
  createdAt       DateTime  @default(now())
  updatedAt       DateTime  @updatedAt

  @@index([candidateId])
  @@map("candidate_experience")
}

model CandidateDocument {
  id            String    @id @default(cuid())
  candidateId   String
  candidate     Candidate @relation(fields: [candidateId], references: [id], onDelete: Cascade)
  documentType  String
  fileName      String
  fileUrl       String
  companyId     String
  company       Company   @relation(fields: [companyId], references: [id], onDelete: Cascade)
  createdAt     DateTime  @default(now())
  updatedAt     DateTime  @updatedAt

  @@index([candidateId])
  @@map("candidate_documents")
}
```

Document types: RESUME, COVER_LETTER, CERTIFICATE, ID_PROOF, PORTFOLIO.

**Endpoints (nested under candidate):**

| Method | Path | Permission | Purpose |
|--------|------|-----------|---------|
| GET | `/hr/candidates/:id/education` | `recruitment:read` | List education records |
| POST | `/hr/candidates/:id/education` | `recruitment:create` | Add education record |
| PATCH | `/hr/candidate-education/:id` | `recruitment:update` | Update education |
| DELETE | `/hr/candidate-education/:id` | `recruitment:delete` | Delete education |
| GET | `/hr/candidates/:id/experience` | `recruitment:read` | List experience records |
| POST | `/hr/candidates/:id/experience` | `recruitment:create` | Add experience record |
| PATCH | `/hr/candidate-experience/:id` | `recruitment:update` | Update experience |
| DELETE | `/hr/candidate-experience/:id` | `recruitment:delete` | Delete experience |
| GET | `/hr/candidates/:id/documents` | `recruitment:read` | List documents |
| POST | `/hr/candidates/:id/documents` | `recruitment:create` | Upload document |
| DELETE | `/hr/candidate-documents/:id` | `recruitment:delete` | Delete document |

**UI:** New Candidate Detail Screen (dedicated page, not modal) with grouped tabs:
- **Profile card** (top): Name, email, phone, source, rating stars, stage badge
- **Background tabs**: Education, Experience, Documents
- **Pipeline tabs**: Interviews, Offers, Stage History

### 5.3 Structured Interview Evaluation

**New model** in `recruitment.prisma`:

```prisma
model InterviewEvaluation {
  id             String             @id @default(cuid())
  interviewId    String
  interview      Interview          @relation(fields: [interviewId], references: [id], onDelete: Cascade)
  evaluatorId    String
  dimension      String
  rating         Int
  comments       String?
  recommendation EvalRecommendation
  companyId      String
  company        Company            @relation(fields: [companyId], references: [id], onDelete: Cascade)
  createdAt      DateTime           @default(now())
  updatedAt      DateTime           @updatedAt

  @@index([interviewId])
  @@map("interview_evaluations")
}

enum EvalRecommendation {
  STRONG_HIRE
  HIRE
  MAYBE
  NO_HIRE
  STRONG_NO_HIRE
}
```

Standard dimensions: "Technical Skills", "Communication", "Problem Solving", "Cultural Fit", "Domain Knowledge". Rating: 1-5 scale.

Each panelist submits their own set of evaluations per interview. Existing `feedbackRating` + `feedbackNotes` on Interview remain as a quick summary field.

**Endpoints:**

| Method | Path | Permission | Purpose |
|--------|------|-----------|---------|
| POST | `/hr/interviews/:id/evaluations` | `training-evaluation:create` | Submit evaluation (array of dimensions) |
| GET | `/hr/interviews/:id/evaluations` | `recruitment:read` | List all evaluations for interview |

**UI:** "Submit Feedback" button on interview cards → opens form with dimension rows (rating slider + comments) + overall recommendation dropdown.

### 5.4 Candidate Stage History

**New model** in `recruitment.prisma`:

```prisma
model CandidateStageHistory {
  id          String         @id @default(cuid())
  candidateId String
  candidate   Candidate      @relation(fields: [candidateId], references: [id], onDelete: Cascade)
  fromStage   CandidateStage
  toStage     CandidateStage
  reason      String?
  notes       String?
  changedBy   String?
  changedAt   DateTime       @default(now())
  companyId   String
  company     Company        @relation(fields: [companyId], references: [id], onDelete: Cascade)

  @@index([candidateId])
  @@map("candidate_stage_history")
}
```

**Implementation:** Auto-created inside `advanceCandidateStage` service method. No extra CRUD endpoints needed — history is read via `GET /hr/candidates/:id` (included in response).

**Rejection/hold reasons:** Update `advanceCandidateStageSchema` to require `reason` when stage = REJECTED or ON_HOLD.

**UI:** Timeline view in Candidate Detail Screen → Stage History tab showing progression with dates, who changed, and reasons.

### 5.5 Candidate-to-Employee Conversion

**New field on Candidate:** `employeeId String?` — set after conversion to link records.

**New endpoint:**

| Method | Path | Permission | Purpose |
|--------|------|-----------|---------|
| POST | `/hr/candidates/:id/convert-to-employee` | `recruitment:configure` | Convert hired candidate to employee |

**Behavior:**
1. Validate candidate stage = HIRED and has an ACCEPTED offer
2. Pre-populate Employee data: name, email, phone from candidate + designation, department, CTC, joining date from offer
3. Create Employee with status PROBATION
4. Set `candidate.employeeId = newEmployee.id`
5. Auto-assign mandatory trainings (query TrainingCatalogue where mandatory = true, create nominations)
6. Emit `candidate.hired` event
7. Return created employee for further editing

**UI:** "Convert to Employee" button on HIRED candidates in detail screen. Opens pre-filled employee form for review before submission.

---

## 6. Phase 3 — Training Enhancements

**Goal:** Training sessions, attendance, evaluation/feedback, certificate lifecycle, trainer management, dashboard screen.

### 6.1 Training Sessions

**New model** in `training.prisma`:

```prisma
model TrainingSession {
  id              String                @id @default(cuid())
  sessionNumber   String?
  trainingId      String
  training        TrainingCatalogue     @relation(fields: [trainingId], references: [id], onDelete: Cascade)
  batchName       String?
  startDateTime   DateTime
  endDateTime     DateTime
  venue           String?
  meetingLink     String?
  maxParticipants Int?
  trainerId       String?
  trainer         Trainer?              @relation(fields: [trainerId], references: [id])
  status          TrainingSessionStatus @default(SCHEDULED)
  cancelledReason String?
  notes           String?
  companyId       String
  company         Company               @relation(fields: [companyId], references: [id], onDelete: Cascade)
  createdAt       DateTime              @default(now())
  updatedAt       DateTime              @updatedAt

  attendees       TrainingAttendance[]
  evaluations     TrainingEvaluation[]

  @@index([companyId, status])
  @@index([trainingId])
  @@index([trainerId])
  @@map("training_sessions")
}

enum TrainingSessionStatus {
  SCHEDULED
  IN_PROGRESS
  COMPLETED
  CANCELLED
}
```

**Number Series:** Add `'Training Session'` to `linked-screens.ts` with defaultPrefix `'TSN-'`.

**Relation update:** Add optional `sessionId String?` to `TrainingNomination` to link nominations to specific sessions.

**Endpoints:**

| Method | Path | Permission | Purpose |
|--------|------|-----------|---------|
| GET | `/hr/training-sessions` | `training:read` | List with filters (trainingId, status, trainerId) |
| POST | `/hr/training-sessions` | `training:create` | Create session for a catalogue |
| GET | `/hr/training-sessions/:id` | `training:read` | Get with attendee count |
| PATCH | `/hr/training-sessions/:id` | `training:update` | Update (SCHEDULED only) |
| PATCH | `/hr/training-sessions/:id/status` | `training:approve` | Start / Complete / Cancel |
| DELETE | `/hr/training-sessions/:id` | `training:delete` | Delete (SCHEDULED only, no attendees) |

**State transitions:** SCHEDULED → IN_PROGRESS → COMPLETED. CANCELLED from SCHEDULED only.

**UI:** New "Sessions" tab in TrainingCatalogueScreen (web) and TrainingScreen (mobile). Cards show date range, venue, trainer, capacity vs enrolled, status badge.

### 6.2 Training Attendance

**New model** in `training.prisma`:

```prisma
model TrainingAttendance {
  id            String           @id @default(cuid())
  sessionId     String
  session       TrainingSession  @relation(fields: [sessionId], references: [id], onDelete: Cascade)
  employeeId    String
  employee      Employee         @relation(fields: [employeeId], references: [id], onDelete: Cascade)
  nominationId  String?
  nomination    TrainingNomination? @relation(fields: [nominationId], references: [id])
  status        AttendanceStatus @default(REGISTERED)
  checkInTime   DateTime?
  checkOutTime  DateTime?
  hoursAttended Decimal?         @db.Decimal(4, 1)
  remarks       String?
  companyId     String
  company       Company          @relation(fields: [companyId], references: [id], onDelete: Cascade)
  createdAt     DateTime         @default(now())
  updatedAt     DateTime         @updatedAt

  @@unique([sessionId, employeeId])
  @@index([sessionId])
  @@index([employeeId])
  @@map("training_attendance")
}

enum AttendanceStatus {
  REGISTERED
  PRESENT
  ABSENT
  LATE
  EXCUSED
}
```

**Endpoints:**

| Method | Path | Permission | Purpose |
|--------|------|-----------|---------|
| GET | `/hr/training-sessions/:id/attendance` | `training:read` | List attendees for session |
| POST | `/hr/training-sessions/:id/attendance` | `training:create` | Register employees (bulk array of employeeIds) |
| PATCH | `/hr/training-attendance/:id` | `training:update` | Mark individual attendance |
| PATCH | `/hr/training-sessions/:id/attendance/bulk` | `training:update` | Bulk mark attendance |

**Workflow:** When session → COMPLETED, auto-calculate `hoursAttended` from check-in/out. Employees with PRESENT/LATE and sufficient hours → nomination advanced to COMPLETED.

**UI:** "Attendance" action on session cards → opens attendance sheet with employee list, status dropdowns, time fields. Bulk "Mark All Present" button.

### 6.3 Training Evaluation & Feedback

**New model** in `training.prisma`:

```prisma
model TrainingEvaluation {
  id                    String          @id @default(cuid())
  nominationId          String
  nomination            TrainingNomination @relation(fields: [nominationId], references: [id], onDelete: Cascade)
  sessionId             String?
  session               TrainingSession? @relation(fields: [sessionId], references: [id])
  type                  EvaluationType
  contentRelevance      Int?
  trainerEffectiveness  Int?
  overallSatisfaction   Int?
  knowledgeGain         Int?
  practicalApplicability Int?
  preAssessmentScore    Decimal?        @db.Decimal(5, 2)
  postAssessmentScore   Decimal?        @db.Decimal(5, 2)
  comments              String?
  improvementSuggestions String?
  submittedBy           String?
  submittedAt           DateTime?
  companyId             String
  company               Company         @relation(fields: [companyId], references: [id], onDelete: Cascade)
  createdAt             DateTime        @default(now())
  updatedAt             DateTime        @updatedAt

  @@index([nominationId])
  @@index([sessionId])
  @@map("training_evaluations")
}

enum EvaluationType {
  PARTICIPANT_FEEDBACK
  TRAINER_ASSESSMENT
}
```

Rating fields: 1-5 scale. Assessment scores: 0-100 scale.

**Endpoints:**

| Method | Path | Permission | Purpose |
|--------|------|-----------|---------|
| POST | `/hr/training-nominations/:id/evaluation` | `training-evaluation:create` | Submit evaluation |
| GET | `/hr/training-nominations/:id/evaluation` | `training:read` | Get evaluation for nomination |
| GET | `/hr/training-sessions/:id/evaluations` | `training:read` | All evaluations for session |
| GET | `/hr/training-evaluations/summary` | `training:read` | Aggregated ratings by trainingId |
| POST | `/ess/training/:nominationId/feedback` | `ess:enroll-training` | ESS: employee submits feedback |

**UI:**
- Admin: "Evaluations" column on nominations showing aggregate score
- ESS My Training: "Give Feedback" button on COMPLETED nominations → rating form with 5 dimensions + comments

### 6.4 Training Certificate Lifecycle

**New fields on `TrainingNomination`:**

```prisma
certificateNumber     String?
certificateIssuedAt   DateTime?
certificateExpiryDate DateTime?
certificateStatus     CertificateStatus?
```

**New enum:**

```prisma
enum CertificateStatus {
  EARNED
  EXPIRING_SOON
  EXPIRED
  RENEWED
}
```

**Behavior:**
- On nomination COMPLETED + catalogue has `certificationName`: auto-set `certificateIssuedAt = now()`, calculate `certificateExpiryDate = issuedAt + certificationValidity years`
- `EXPIRING_SOON` set when within 30 days of expiry (checked on read or via event)
- `EXPIRED` set when past expiry date

**New endpoint:**

| Method | Path | Permission | Purpose |
|--------|------|-----------|---------|
| GET | `/hr/training-certificates/expiring` | `training:read` | Certificates expiring within N days (query param: `days`) |

**UI:** Certificate badge on nomination cards. Dashboard widget for expiring certificates.

### 6.5 Trainer Management

**New model** in `training.prisma`:

```prisma
model Trainer {
  id              String    @id @default(cuid())
  employeeId      String?
  employee        Employee? @relation(fields: [employeeId], references: [id])
  externalName    String?
  email           String
  phone           String?
  specializations Json?
  qualifications  String?
  experienceYears Int?
  averageRating   Decimal?  @db.Decimal(3, 2)
  totalSessions   Int       @default(0)
  isInternal      Boolean   @default(true)
  isActive        Boolean   @default(true)
  companyId       String
  company         Company   @relation(fields: [companyId], references: [id], onDelete: Cascade)
  createdAt       DateTime  @default(now())
  updatedAt       DateTime  @updatedAt

  sessions        TrainingSession[]

  @@index([companyId, isActive])
  @@map("trainers")
}
```

Validation: Either `employeeId` (internal) OR `externalName` (external) must be set.

**Endpoints:**

| Method | Path | Permission | Purpose |
|--------|------|-----------|---------|
| GET | `/hr/trainers` | `training:read` | List with filters (isInternal, isActive) |
| POST | `/hr/trainers` | `training:create` | Create trainer profile |
| GET | `/hr/trainers/:id` | `training:read` | Get with session history |
| PATCH | `/hr/trainers/:id` | `training:update` | Update |
| DELETE | `/hr/trainers/:id` | `training:delete` | Soft delete (isActive=false) |

**Integration:** Session completion increments `totalSessions`. `averageRating` recalculated from PARTICIPANT_FEEDBACK `trainerEffectiveness` scores.

**UI:** New "Trainers" tab in TrainingCatalogueScreen/TrainingScreen. Trainer cards: name, type badge, specializations, rating stars, session count.

### 6.6 Training Dashboard Screen

Build missing `TrainingDashboardScreen` for web and mobile, following RecruitmentDashboardScreen pattern.

**KPIs:**
- Total programmes (active)
- Active nominations
- Completion rate %
- Mandatory coverage %

**Widgets:**
- Training completion trends chart
- Nominations by status distribution
- Expiring certificates list
- Top trainers by rating
- Mandatory training compliance table

**Nav manifest:** Add `hr-analytics-training` entry to `NAVIGATION_MANIFEST`.

---

## 7. Phase 4 — Advanced Features

**Goal:** Learning paths, budget tracking, training materials, enhanced analytics.

### 7.1 Training Programs / Learning Paths

**New models** in `training.prisma`:

```prisma
model TrainingProgram {
  id            String    @id @default(cuid())
  programNumber String?
  name          String
  description   String?
  category      String
  level         String?
  totalDuration String?
  isCompulsory  Boolean   @default(false)
  isActive      Boolean   @default(true)
  companyId     String
  company       Company   @relation(fields: [companyId], references: [id], onDelete: Cascade)
  createdAt     DateTime  @default(now())
  updatedAt     DateTime  @updatedAt

  courses       TrainingProgramCourse[]
  enrollments   TrainingProgramEnrollment[]

  @@index([companyId, isActive])
  @@map("training_programs")
}

model TrainingProgramCourse {
  id            String            @id @default(cuid())
  programId     String
  program       TrainingProgram   @relation(fields: [programId], references: [id], onDelete: Cascade)
  trainingId    String
  training      TrainingCatalogue @relation(fields: [trainingId], references: [id], onDelete: Cascade)
  sequenceOrder Int
  isPrerequisite Boolean          @default(false)
  minPassScore  Decimal?          @db.Decimal(5, 2)
  companyId     String
  company       Company           @relation(fields: [companyId], references: [id], onDelete: Cascade)
  createdAt     DateTime          @default(now())

  @@unique([programId, trainingId])
  @@index([programId])
  @@map("training_program_courses")
}

model TrainingProgramEnrollment {
  id              String                   @id @default(cuid())
  programId       String
  program         TrainingProgram          @relation(fields: [programId], references: [id], onDelete: Cascade)
  employeeId      String
  employee        Employee                 @relation(fields: [employeeId], references: [id], onDelete: Cascade)
  enrolledAt      DateTime                 @default(now())
  completedAt     DateTime?
  status          ProgramEnrollmentStatus  @default(ENROLLED)
  progressPercent Int                      @default(0)
  companyId       String
  company         Company                  @relation(fields: [companyId], references: [id], onDelete: Cascade)
  createdAt       DateTime                 @default(now())
  updatedAt       DateTime                 @updatedAt

  @@unique([programId, employeeId])
  @@index([programId])
  @@index([employeeId])
  @@map("training_program_enrollments")
}

enum ProgramEnrollmentStatus {
  ENROLLED
  IN_PROGRESS
  COMPLETED
  FAILED
  ABANDONED
}
```

Program categories: CERTIFICATION, SKILL_DEVELOPMENT, COMPLIANCE, ONBOARDING.
Program levels: BEGINNER, INTERMEDIATE, ADVANCED.

**Number Series:** Add `'Training Program'` to `linked-screens.ts` with defaultPrefix `'PRG-'`.

**Endpoints:**

| Method | Path | Permission | Purpose |
|--------|------|-----------|---------|
| GET | `/hr/training-programs` | `training:read` | List programs |
| POST | `/hr/training-programs` | `training:create` | Create program |
| GET | `/hr/training-programs/:id` | `training:read` | Get with courses and enrollment count |
| PATCH | `/hr/training-programs/:id` | `training:update` | Update program |
| DELETE | `/hr/training-programs/:id` | `training:delete` | Delete (no enrollments) |
| POST | `/hr/training-programs/:id/courses` | `training:configure` | Add course to program |
| DELETE | `/hr/training-programs/:id/courses/:courseId` | `training:configure` | Remove course |
| POST | `/hr/training-programs/:id/enroll` | `training:create` | Enroll employees |
| GET | `/hr/training-programs/:id/enrollments` | `training:read` | List enrollments with progress |

**Workflow:**
- Nomination COMPLETED for a program course → recalculate `progressPercent`
- Prerequisite course not completed → block next course nomination (validation error)
- All courses completed → auto-set enrollment COMPLETED

**UI:** New "Programs" tab. Program detail: ordered course list, enrollment count, progress bars.

### 7.2 Training Budget Tracking

**New model** in `training.prisma`:

```prisma
model TrainingBudget {
  id              String      @id @default(cuid())
  fiscalYear      String
  departmentId    String?
  department      Department? @relation(fields: [departmentId], references: [id])
  allocatedAmount Decimal     @db.Decimal(15, 2)
  usedAmount      Decimal     @default(0) @db.Decimal(15, 2)
  companyId       String
  company         Company     @relation(fields: [companyId], references: [id], onDelete: Cascade)
  createdAt       DateTime    @default(now())
  updatedAt       DateTime    @updatedAt

  @@unique([fiscalYear, companyId, departmentId])
  @@map("training_budgets")
}
```

**Endpoints:**

| Method | Path | Permission | Purpose |
|--------|------|-----------|---------|
| GET | `/hr/training-budgets` | `training:read` | List by fiscal year |
| POST | `/hr/training-budgets` | `training:configure` | Allocate budget |
| PATCH | `/hr/training-budgets/:id` | `training:configure` | Update allocation |
| GET | `/hr/training-budgets/utilization` | `training:read` | Budget vs actual by department |

**Workflow:** Nomination COMPLETED → increment `usedAmount` on matching budget (fiscal year + employee's department).

**UI:** Budget management section in training admin. Dashboard widget: utilization bar chart by department.

### 7.3 Training Materials

**New model** in `training.prisma`:

```prisma
model TrainingMaterial {
  id            String            @id @default(cuid())
  trainingId    String
  training      TrainingCatalogue @relation(fields: [trainingId], references: [id], onDelete: Cascade)
  name          String
  type          String
  url           String
  description   String?
  sequenceOrder Int?
  isMandatory   Boolean           @default(true)
  isActive      Boolean           @default(true)
  companyId     String
  company       Company           @relation(fields: [companyId], references: [id], onDelete: Cascade)
  createdAt     DateTime          @default(now())
  updatedAt     DateTime          @updatedAt

  @@index([trainingId])
  @@map("training_materials")
}
```

Material types: PDF, VIDEO, LINK, PRESENTATION, DOCUMENT.

**Endpoints:**

| Method | Path | Permission | Purpose |
|--------|------|-----------|---------|
| GET | `/hr/training-catalogues/:id/materials` | `training:read` | List materials |
| POST | `/hr/training-catalogues/:id/materials` | `training:create` | Add material |
| PATCH | `/hr/training-materials/:id` | `training:update` | Update |
| DELETE | `/hr/training-materials/:id` | `training:delete` | Remove |

**UI:** "Materials" section in catalogue detail. ESS My Training → tapping training shows materials list.

### 7.4 Enhanced Analytics

Extend existing dashboard service methods (no new endpoints):

**Recruitment Dashboard additions:**
- Source effectiveness: hires per source
- Funnel conversion rates: % drop-off at each stage (from CandidateStageHistory)
- Offer acceptance rate (from CandidateOffer data)
- Average time per stage
- Requisition aging: days open per requisition

**Training Dashboard additions:**
- Training effectiveness: avg pre vs post assessment scores (from evaluations)
- Trainer leaderboard by rating
- Budget utilization by department
- Certificate expiry timeline
- Program completion rates
- Skill gap coverage: % of required skills addressed by completed trainings

---

## 8. State Machine Transitions

All enforced via `validateTransition()` in `src/shared/utils/state-machine.ts`.

### RequisitionStatus

```
DRAFT       → [OPEN, CANCELLED]
OPEN        → [INTERVIEWING, CANCELLED]
INTERVIEWING → [OFFERED, CANCELLED]
OFFERED     → [FILLED, INTERVIEWING, CANCELLED]
FILLED      → [] (terminal)
CANCELLED   → [] (terminal)
```

### CandidateStage

```
APPLIED     → [SHORTLISTED, REJECTED, ON_HOLD]
SHORTLISTED → [HR_ROUND, REJECTED, ON_HOLD]
HR_ROUND    → [TECHNICAL, REJECTED, ON_HOLD]
TECHNICAL   → [FINAL, REJECTED, ON_HOLD]
FINAL       → [ASSESSMENT, OFFER_SENT, REJECTED, ON_HOLD]
ASSESSMENT  → [OFFER_SENT, REJECTED, ON_HOLD]
OFFER_SENT  → [HIRED, REJECTED, ON_HOLD]
ON_HOLD     → [APPLIED, SHORTLISTED, HR_ROUND, TECHNICAL, FINAL, ASSESSMENT, OFFER_SENT, REJECTED]
HIRED       → [] (terminal)
REJECTED    → [] (terminal)
```

### OfferStatus

```
DRAFT      → [SENT, WITHDRAWN]
SENT       → [ACCEPTED, REJECTED, EXPIRED, WITHDRAWN]
ACCEPTED   → [] (terminal)
REJECTED   → [] (terminal)
WITHDRAWN  → [] (terminal)
EXPIRED    → [] (terminal)
```

### InterviewStatus

```
SCHEDULED  → [COMPLETED, CANCELLED, NO_SHOW]
COMPLETED  → [] (terminal)
CANCELLED  → [] (terminal)
NO_SHOW    → [] (terminal)
```

### TrainingNominationStatus

```
NOMINATED   → [APPROVED, CANCELLED]
APPROVED    → [IN_PROGRESS, CANCELLED]
IN_PROGRESS → [COMPLETED, CANCELLED]
COMPLETED   → [] (terminal)
CANCELLED   → [] (terminal)
```

### TrainingSessionStatus

```
SCHEDULED   → [IN_PROGRESS, CANCELLED]
IN_PROGRESS → [COMPLETED]
COMPLETED   → [] (terminal)
CANCELLED   → [] (terminal)
```

### OfferStatus (Lazy Expiry)

SENT offers with `validUntil < now()` are auto-updated to EXPIRED on read. No cron needed.

### ProgramEnrollmentStatus

```
ENROLLED    → [IN_PROGRESS, ABANDONED]
IN_PROGRESS → [COMPLETED, FAILED, ABANDONED]
COMPLETED   → [] (terminal)
FAILED      → [] (terminal)
ABANDONED   → [] (terminal)
```

---

## 9. Permission Matrix

### New Permission Modules

Added to `PERMISSION_MODULES` in `permissions.ts`:

| Module | Actions | Tied to Subscription |
|--------|---------|---------------------|
| `recruitment` | read, create, update, delete, approve, export, configure | hr |
| `recruitment-offer` | read, create, update, approve | hr |
| `training` | read, create, update, delete, approve, export, configure | hr |
| `training-evaluation` | read, create | hr |

### Permission Mapping

| Feature | Read | Create | Update | Delete | Approve | Configure |
|---------|------|--------|--------|--------|---------|-----------|
| Requisitions | `recruitment:read` | `recruitment:create` | `recruitment:update` | `recruitment:delete` | `recruitment:approve` | — |
| Candidates | `recruitment:read` | `recruitment:create` | `recruitment:update` | `recruitment:delete` | — | — |
| Interviews | `recruitment:read` | `recruitment:create` | `recruitment:update` | `recruitment:delete` | — | — |
| Offers | `recruitment-offer:read` | `recruitment-offer:create` | `recruitment-offer:update` | — | `recruitment-offer:approve` | — |
| Training Catalogues | `training:read` | `training:create` | `training:update` | `training:delete` | — | `training:configure` |
| Training Sessions | `training:read` | `training:create` | `training:update` | `training:delete` | `training:approve` | — |
| Training Nominations | `training:read` | `training:create` | `training:update` | `training:delete` | `training:approve` | — |
| Evaluations | `training-evaluation:read` | `training-evaluation:create` | — | — | — | — |
| Trainers | `training:read` | `training:create` | `training:update` | `training:delete` | — | — |
| Programs | `training:read` | `training:create` | `training:update` | `training:delete` | — | `training:configure` |
| Budgets | `training:read` | — | — | — | — | `training:configure` |

### Reference Role Updates

| Role | Permissions |
|------|------------|
| Employee | `ess:enroll-training`, `training-evaluation:create` |
| Manager | `recruitment:read`, `training:read`, `training-evaluation:create` |
| HR Personnel | `recruitment:*`, `recruitment-offer:*`, `training:*`, `training-evaluation:*` |
| HR Manager | `recruitment:*`, `recruitment-offer:*`, `training:*`, `training-evaluation:*` |
| Company Admin | All (via `*`) |

### Migration Path

Existing `hr:read/create/update/delete` guards replaced with specific permissions. Inheritance still applies: `recruitment:configure` grants all lower actions.

---

## 10. Notification Flows

### Architecture

**Global notification service** at `src/core/notifications/` — used by ALL modules.

**Delivery channels:**
- **In-app:** Stored in `Notification` model, queried via REST API
- **FCM Push:** Firebase Cloud Messaging for mobile (via `expo-notifications` + FCM) and web (FCM web push via service worker)
- **Email:** Via existing email infrastructure (future)

### Models

```prisma
// In prisma/modules/platform/notifications.prisma

model Notification {
  id          String    @id @default(cuid())
  userId      String
  title       String
  body        String
  type        String
  entityType  String?
  entityId    String?
  data        Json?
  isRead      Boolean   @default(false)
  companyId   String
  createdAt   DateTime  @default(now())

  @@index([userId, isRead])
  @@index([companyId, createdAt])
  @@map("notifications")
}

model UserDevice {
  id          String    @id @default(cuid())
  userId      String
  platform    String
  fcmToken    String
  deviceName  String?
  lastActiveAt DateTime @default(now())
  createdAt   DateTime  @default(now())
  updatedAt   DateTime  @updatedAt

  @@unique([userId, fcmToken])
  @@index([userId])
  @@map("user_devices")
}
```

Platform values: `MOBILE_IOS`, `MOBILE_ANDROID`, `WEB`.

### Endpoints

| Method | Path | Permission | Purpose |
|--------|------|-----------|---------|
| POST | `/notifications/register-device` | authenticated | Register FCM token |
| DELETE | `/notifications/register-device` | authenticated | Unregister on logout |
| GET | `/notifications` | authenticated | List user's notifications (paginated) |
| PATCH | `/notifications/:id/read` | authenticated | Mark as read |
| PATCH | `/notifications/read-all` | authenticated | Mark all as read |
| GET | `/notifications/unread-count` | authenticated | Get unread count |

### Service Interface

```typescript
// src/core/notifications/notification.service.ts
class NotificationService {
  async send(params: {
    recipientIds: string[];
    title: string;
    body: string;
    type: string;
    entityType?: string;
    entityId?: string;
    channels: ('in_app' | 'push' | 'email')[];
    data?: Record<string, any>;  // FCM deep-link payload
    companyId: string;
  }): Promise<void>
}
```

Any module imports and calls this service. Push delivery is async (fire-and-forget).

### FCM Integration

- Backend: `firebase-admin` SDK for sending FCM messages
- Mobile: `expo-notifications` with FCM credentials, registers token on app launch
- Web: FCM web push via service worker (`firebase/messaging`), registers token on login
- FCM data payload includes `entityType` + `entityId` for deep-linking on tap

### Notification Triggers (HR Module)

| Event | Recipients | Channels |
|-------|-----------|----------|
| Interview scheduled | Panelists | in_app + push |
| Interview completed | Hiring manager | in_app |
| Offer sent | Hiring manager | in_app + push |
| Offer accepted | Hiring manager + HR | in_app + push |
| Offer rejected | Hiring manager + HR | in_app + push |
| Training nomination created | Nominated employee | in_app + push |
| Training session upcoming (1 day before) | Registered attendees | in_app + push |
| Certificate expiring (30 days) | Employee + HR admin | in_app + push |
| Mandatory training overdue | Employee + Manager | in_app + push |

### Reusability

This notification service is module-agnostic. Other modules use it identically:
- Support tickets: `ticket:new`, `ticket:resolved`
- Approvals: `approval:pending`, `approval:completed`
- Attendance: `attendance:anomaly`
- Any future module

---

## 11. Event System

### Architecture

Lightweight typed EventEmitter at `src/shared/events/`.

```typescript
// src/shared/events/hr-events.ts
type HREvent =
  | { type: 'candidate.stage_changed'; candidateId: string; fromStage: string; toStage: string; changedBy: string; companyId: string }
  | { type: 'candidate.hired'; candidateId: string; offerId?: string; companyId: string }
  | { type: 'offer.sent'; offerId: string; candidateId: string; companyId: string }
  | { type: 'offer.accepted'; offerId: string; candidateId: string; companyId: string }
  | { type: 'offer.rejected'; offerId: string; candidateId: string; companyId: string }
  | { type: 'interview.scheduled'; interviewId: string; panelistIds: string[]; companyId: string }
  | { type: 'interview.completed'; interviewId: string; candidateId: string; companyId: string }
  | { type: 'training.nomination.created'; nominationId: string; employeeId: string; companyId: string }
  | { type: 'training.completed'; nominationId: string; employeeId: string; companyId: string }
  | { type: 'training.session.upcoming'; sessionId: string; date: string; companyId: string }
  | { type: 'certificate.expiring'; nominationId: string; employeeId: string; expiryDate: string; companyId: string }
```

### Listener Registration

Listeners registered at app startup in `src/shared/events/listeners/`:

| Event | Side Effects |
|-------|-------------|
| `candidate.hired` | Create audit log, send notification |
| `offer.accepted` | Advance candidate stage to HIRED, send notification, create audit log |
| `offer.rejected` | Send notification, create audit log |
| `training.completed` | Update employee skill mappings, check program progress, increment budget usage, send notification, create audit log |
| `interview.scheduled` | Send notification to panelists |
| `training.nomination.created` | Send notification to employee |
| `certificate.expiring` | Send notification to employee + HR |

Services emit events and return immediately. Side effects are decoupled.

---

## 12. Audit Trail

### Model

```prisma
// In prisma/modules/platform/audit.prisma

model AuditLog {
  id            String    @id @default(cuid())
  entityType    String
  entityId      String
  action        String
  changes       Json?
  changedBy     String
  changedAt     DateTime  @default(now())
  retentionDate DateTime
  companyId     String
  company       Company   @relation(fields: [companyId], references: [id], onDelete: Cascade)

  @@index([companyId, entityType, entityId])
  @@index([retentionDate])
  @@map("audit_logs")
}
```

Actions: `CREATE`, `UPDATE`, `DELETE`, `STATUS_CHANGE`.

### Changes Field Format

- **CREATE:** Full snapshot of created record as `{field: {to: value}}`
- **UPDATE / STATUS_CHANGE:** Diff only as `{field: {from: oldValue, to: newValue}}`
- **DELETE:** Full snapshot of deleted record as `{field: {from: value}}`

### Diff Utility

```typescript
// src/shared/utils/audit.ts
function computeDiff(before: Record<string, any>, after: Record<string, any>): Record<string, {from: any, to: any}>
// Returns only changed fields, excludes updatedAt

async function auditLog(params: {
  tenantPrisma: PrismaClient;
  entityType: string;
  entityId: string;
  action: 'CREATE' | 'UPDATE' | 'DELETE' | 'STATUS_CHANGE';
  before?: Record<string, any>;
  after?: Record<string, any>;
  changedBy: string;
  companyId: string;
  retentionMonths?: number; // default 12
}): Promise<void>
```

### What Gets Audited

- All status/stage transitions (offers, candidates, requisitions, sessions, nominations)
- All creates/deletes on critical entities (offers, evaluations, training sessions)
- NOT every field update (too noisy) — only status changes and destructive actions

### Retention Policy

- `retentionDate` auto-calculated: `changedAt + retentionMonths` (default 12 months)
- Configurable per company via SystemControls: `auditRetentionMonths` field
- Cleanup: periodic `DELETE FROM audit_logs WHERE retentionDate < NOW()`
- Can be triggered manually by SUPER_ADMIN or via scheduled job
- Future: export to S3/object storage before deletion for cold archive

### Endpoint

| Method | Path | Permission | Purpose |
|--------|------|-----------|---------|
| GET | `/hr/audit-log` | `hr:read` | Query by entityType, entityId, dateRange |

**UI:** "Activity" / "History" section at bottom of detail screens showing timeline of changes.

---

## 13. Aggregation & Performance

### Strategy

Lazy computation with caching. No cron jobs for Phase 1-4.

### AnalyticsSnapshot Model

```prisma
// In prisma/modules/platform/analytics.prisma

model AnalyticsSnapshot {
  id            String    @id @default(cuid())
  companyId     String
  snapshotType  String
  snapshotDate  DateTime  @default(now())
  data          Json
  createdAt     DateTime  @default(now())

  @@index([companyId, snapshotType])
  @@map("analytics_snapshots")
}
```

Snapshot types: `RECRUITMENT_FUNNEL`, `TRAINING_COMPLETION`, `BUDGET_UTILIZATION`, `CERTIFICATE_EXPIRY`, `SKILL_GAP`.

### Caching Flow

1. Dashboard endpoint checks for snapshot < 1 hour old
2. If fresh → return cached data
3. If stale → recompute, store new snapshot, return
4. Redis layer: 15-minute TTL using `createTenantCacheKey('recruitment-dashboard', companyId)`
5. Cache invalidated on relevant mutations (new hire, training completion, etc.)

### Refresh Controls

- Company admins: "Refresh" button on dashboards (debounced to 1 per 5 minutes)
- SUPER_ADMIN: `POST /platform/analytics/refresh` to force recompute for any company

---

## 14. Scope Summary

### New Models (15)

| Phase | Model | File |
|-------|-------|------|
| P2 | CandidateOffer | recruitment.prisma |
| P2 | CandidateEducation | recruitment.prisma |
| P2 | CandidateExperience | recruitment.prisma |
| P2 | CandidateDocument | recruitment.prisma |
| P2 | InterviewEvaluation | recruitment.prisma |
| P2 | CandidateStageHistory | recruitment.prisma |
| P3 | TrainingSession | training.prisma |
| P3 | TrainingAttendance | training.prisma |
| P3 | TrainingEvaluation | training.prisma |
| P3 | Trainer | training.prisma |
| P4 | TrainingProgram | training.prisma |
| P4 | TrainingProgramCourse | training.prisma |
| P4 | TrainingProgramEnrollment | training.prisma |
| P4 | TrainingBudget | training.prisma |
| P4 | TrainingMaterial | training.prisma |

### Cross-Cutting Models (4)

| Model | File |
|-------|------|
| Notification | notifications.prisma |
| UserDevice | notifications.prisma |
| AuditLog | audit.prisma |
| AnalyticsSnapshot | analytics.prisma |

### New Enums (9)

EmploymentType, RequisitionPriority, OfferStatus, EvalRecommendation, TrainingSessionStatus, AttendanceStatus, EvaluationType, CertificateStatus, ProgramEnrollmentStatus

### New Endpoints (~70+)

| Area | Count |
|------|-------|
| Offers | 6 |
| Candidate Profile (edu/exp/docs) | 11 |
| Interview Evaluations | 2 |
| Candidate Convert | 1 |
| Training Sessions | 6 |
| Training Attendance | 4 |
| Training Evaluations | 5 |
| Trainers | 5 |
| Training Programs | 9 |
| Training Budgets | 4 |
| Training Materials | 4 |
| Certificates (expiring) | 1 |
| Notifications | 6 |
| Audit Log | 1 |
| Analytics Refresh | 1 |
| **Total** | **~66** |

### New/Modified Screens

| Phase | Web | Mobile |
|-------|-----|--------|
| P1 | Fix existing forms, wire buttons | Fix existing forms, wire buttons |
| P2 | Offers tab, Candidate Detail page, Evaluation form | Same |
| P3 | Sessions tab, Attendance sheet, Feedback form, Trainers tab, Training Dashboard | Same |
| P4 | Programs tab, Budget section, Materials section | Same |
| CC | Notification bell + list, Audit history sections | Same + FCM push setup |

### Permission Modules (4 new)

recruitment, recruitment-offer, training, training-evaluation
