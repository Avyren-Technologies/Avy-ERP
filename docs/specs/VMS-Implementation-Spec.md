# Avy ERP -- Visitor Management System (VMS)
## Implementation Specification

### Document Info

| Field | Value |
|---|---|
| Document Code | AVY-VMS-IMPL-001 |
| Version | 1.0 |
| Date | 2026-04-13 |
| Status | Implementation-Ready |
| PRD Reference | `docs/Avy_ERP_Visitor_Management_Module_v2_PRD.md` (AVY-VMS-PRD-002) |
| Author | Generated from PRD v2.0 |

---

### Table of Contents

1. [Architecture Overview](#1-architecture-overview)
2. [Prisma Schema -- Complete Models](#2-prisma-schema----complete-models)
3. [Backend Implementation -- File-by-File Specification](#3-backend-implementation----file-by-file-specification)
4. [Constants & Configuration Updates](#4-constants--configuration-updates)
5. [Web App Implementation](#5-web-app-implementation)
6. [Mobile App Implementation](#6-mobile-app-implementation)
7. [Public Web Pages](#7-public-web-pages)
8. [Notification Integration](#8-notification-integration)
9. [Approval Workflow Integration](#9-approval-workflow-integration)
10. [Concurrency & Data Integrity](#10-concurrency--data-integrity)
11. [Cron Jobs & Scheduled Tasks](#11-cron-jobs--scheduled-tasks)
12. [Implementation Order (Sprint Plan)](#12-implementation-order-sprint-plan)

---

## 1. Architecture Overview

### 1.1 Module Boundaries

The VMS module is a standalone business module that integrates with:
- **HR Module** -- Host employee lookup via Employee Master
- **RBAC** -- Permission module `visitors` with actions: `read, create, update, delete, approve, export, configure`
- **Notifications** -- Leverages `notificationService.dispatch()` for push/SMS/email
- **Number Series** -- `generateNextNumber()` for visit IDs, badges, passes
- **Approval Workflows** -- `essService.createRequest()` for walk-in/QR self-reg approval

### 1.2 File Structure

```
avy-erp-backend/
  prisma/modules/visitors/
    visitors.prisma              # All VMS models + enums

  src/modules/visitors/
    routes.ts                    # Main router mounting all sub-routes
    core/
      visit.routes.ts
      visit.controller.ts
      visit.service.ts
      visit.validators.ts
      visit.types.ts
    config/
      visitor-type.routes.ts
      visitor-type.controller.ts
      visitor-type.service.ts
      visitor-type.validators.ts
      gate.routes.ts
      gate.controller.ts
      gate.service.ts
      gate.validators.ts
      safety-induction.routes.ts
      safety-induction.controller.ts
      safety-induction.service.ts
      safety-induction.validators.ts
      vms-config.routes.ts
      vms-config.controller.ts
      vms-config.service.ts
    security/
      watchlist.routes.ts
      watchlist.controller.ts
      watchlist.service.ts
      watchlist.validators.ts
      denied-entry.routes.ts
      denied-entry.controller.ts
      denied-entry.service.ts
    passes/
      recurring-pass.routes.ts
      recurring-pass.controller.ts
      recurring-pass.service.ts
      recurring-pass.validators.ts
      vehicle-pass.routes.ts
      vehicle-pass.controller.ts
      vehicle-pass.service.ts
      vehicle-pass.validators.ts
      material-pass.routes.ts
      material-pass.controller.ts
      material-pass.service.ts
      material-pass.validators.ts
    group/
      group-visit.routes.ts
      group-visit.controller.ts
      group-visit.service.ts
      group-visit.validators.ts
    dashboard/
      dashboard.routes.ts
      dashboard.controller.ts
      dashboard.service.ts
    reports/
      reports.routes.ts
      reports.controller.ts
      reports.service.ts
    emergency/
      emergency.routes.ts
      emergency.controller.ts
      emergency.service.ts
    public/
      public.routes.ts
      public.service.ts
```

### 1.3 Database Schema Location

All VMS Prisma models go in a single file: `prisma/modules/visitors/visitors.prisma`

This file contains 12 models and 20 enums. After editing, run `pnpm prisma:merge` then `pnpm db:generate`.

### 1.4 Route Mounting

The VMS routes are already mounted in `src/app/routes.ts` at line 142:
```typescript
router.use('/visitors', visitorsRoutes);
```

This is inside the auth + tenant required section, so all VMS routes (except public) automatically require authentication and tenant context.

Public routes for visitor-facing pages are mounted separately (see Section 7).

---

## 2. Prisma Schema -- Complete Models

**File:** `prisma/modules/visitors/visitors.prisma`

```prisma
// ══════════════════════════════════════════════════════════════════════
// VISITOR MANAGEMENT MODULE — All models and enums
// ══════════════════════════════════════════════════════════════════════

// ── Enums ──────────────────────────────────────────────────────────

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

enum VisitApprovalStatus {
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
  AUTO_CHECKOUT
}

enum SafetyInductionType {
  VIDEO
  SLIDES
  QUESTIONNAIRE
  DECLARATION
}

enum GateType {
  MAIN
  SERVICE
  LOADING_DOCK
  VIP
}

enum WatchlistType {
  BLOCKLIST
  WATCHLIST
}

enum WatchlistDuration {
  PERMANENT
  UNTIL_DATE
}

enum GroupVisitStatus {
  PLANNED
  IN_PROGRESS
  COMPLETED
  CANCELLED
}

enum GroupMemberStatus {
  EXPECTED
  CHECKED_IN
  CHECKED_OUT
  NO_SHOW
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
  NOT_APPLICABLE
  PENDING
  PARTIAL
  FULLY_RETURNED
}

enum ConfigRequirement {
  ALWAYS
  PER_VISITOR_TYPE
  NEVER
}

enum DenialReason {
  BLOCKLIST_MATCH
  HOST_REJECTED
  INDUCTION_FAILED
  GATE_CLOSED
  WRONG_DATE
  WRONG_GATE
  PASS_EXPIRED
  APPROVAL_TIMEOUT
  MANUAL_DENIAL
  VISIT_CANCELLED
}

// ── Models ─────────────────────────────────────────────────────────

model VisitorType {
  id                        String   @id @default(cuid())
  companyId                 String
  name                      String
  code                      String
  badgeColour               String   @default("#3B82F6")
  isDefault                 Boolean  @default(false)
  isActive                  Boolean  @default(true)

  requirePhoto              Boolean  @default(true)
  requireIdVerification     Boolean  @default(true)
  requireSafetyInduction    Boolean  @default(false)
  requireNda                Boolean  @default(false)
  requireHostApproval       Boolean  @default(true)
  requireEscort             Boolean  @default(false)

  defaultMaxDurationMinutes Int?     @default(480)

  safetyInductionId         String?

  sortOrder                 Int      @default(0)
  createdAt                 DateTime @default(now())
  updatedAt                 DateTime @updatedAt

  company                   Company  @relation(fields: [companyId], references: [id], onDelete: Cascade)
  safetyInduction           SafetyInduction? @relation(fields: [safetyInductionId], references: [id])
  visits                    Visit[]

  @@unique([companyId, code])
  @@index([companyId, isActive])
  @@map("visitor_types")
}

model VisitorGate {
  id                       String   @id @default(cuid())
  companyId                String
  plantId                  String
  name                     String
  code                     String
  type                     GateType @default(MAIN)
  openTime                 String?
  closeTime                String?
  allowedVisitorTypeIds    String[]
  qrPosterUrl              String?
  isActive                 Boolean  @default(true)
  createdAt                DateTime @default(now())
  updatedAt                DateTime @updatedAt

  company                  Company  @relation(fields: [companyId], references: [id], onDelete: Cascade)

  visitsCheckIn            Visit[]  @relation("CheckInGate")
  visitsCheckOut           Visit[]  @relation("CheckOutGate")
  visitsAssigned           Visit[]  @relation("AssignedGate")
  vehiclePassEntry         VehicleGatePass[] @relation("VehicleEntryGate")
  vehiclePassExit          VehicleGatePass[] @relation("VehicleExitGate")
  materialPasses           MaterialGatePass[]

  @@unique([companyId, code])
  @@index([companyId, plantId, isActive])
  @@map("visitor_gates")
}

model SafetyInduction {
  id                String              @id @default(cuid())
  companyId         String
  name              String
  type              SafetyInductionType
  contentUrl        String?
  questions         Json?
  passingScore      Int?                @default(80)
  durationSeconds   Int?                @default(120)
  validityDays      Int?                @default(30)
  isActive          Boolean             @default(true)
  plantId           String?
  createdAt         DateTime            @default(now())
  updatedAt         DateTime            @updatedAt

  company           Company             @relation(fields: [companyId], references: [id], onDelete: Cascade)
  visitorTypes      VisitorType[]

  @@index([companyId, isActive])
  @@map("safety_inductions")
}

model Visit {
  id                        String              @id @default(cuid())
  companyId                 String
  visitNumber               String              @unique
  visitCode                 String              @unique
  qrCodeUrl                 String?

  // Visitor details
  visitorName               String
  visitorMobile             String
  visitorEmail              String?
  visitorCompany            String?
  visitorDesignation        String?
  visitorPhoto              String?
  governmentIdType          String?
  governmentIdNumber        String?
  idDocumentPhoto           String?

  // Visit details
  visitorTypeId             String
  purpose                   VisitPurpose
  purposeNotes              String?
  expectedDate              DateTime
  expectedTime              String?
  expectedDurationMinutes   Int?

  // Host & location
  hostEmployeeId            String
  plantId                   String
  gateId                    String?

  // Registration
  registrationMethod        RegistrationMethod

  // Approval
  approvalStatus            VisitApprovalStatus @default(PENDING)
  approvedBy                String?
  approvalTimestamp          DateTime?
  approvalNotes             String?

  // Check-in
  checkInTime               DateTime?
  checkInGateId             String?
  checkInGuardId            String?

  // Badge
  badgeNumber               String?
  badgeFormat               BadgeFormat?

  // Safety & compliance
  safetyInductionStatus     InductionStatus     @default(NOT_REQUIRED)
  safetyInductionScore      Int?
  safetyInductionTimestamp  DateTime?
  ndaSigned                 Boolean             @default(false)
  ndaDocumentUrl            String?
  ppeIssued                 Json?

  // Check-out
  checkOutTime              DateTime?
  checkOutGateId            String?
  checkOutMethod            CheckOutMethod?
  badgeReturned             Boolean?
  materialOut               String?

  // Duration
  visitDurationMinutes      Int?

  // Extension tracking
  originalDurationMinutes   Int?
  extensionCount            Int                 @default(0)
  lastExtendedAt            DateTime?
  lastExtendedBy            String?

  // Status
  status                    VisitStatus         @default(EXPECTED)

  // Vehicle
  vehicleRegNumber          String?
  vehicleType               String?

  // Material & misc
  materialCarriedIn         String?
  specialInstructions       String?
  emergencyContact          String?

  // Links
  groupVisitId              String?
  recurringPassId           String?
  purchaseOrderRef          String?
  meetingRef                String?

  // Audit
  createdBy                 String
  createdAt                 DateTime            @default(now())
  updatedBy                 String?
  updatedAt                 DateTime            @updatedAt

  company                   Company             @relation(fields: [companyId], references: [id], onDelete: Cascade)
  visitorType               VisitorType         @relation(fields: [visitorTypeId], references: [id])
  checkInGate               VisitorGate?        @relation("CheckInGate", fields: [checkInGateId], references: [id])
  checkOutGate              VisitorGate?        @relation("CheckOutGate", fields: [checkOutGateId], references: [id])
  assignedGate              VisitorGate?        @relation("AssignedGate", fields: [gateId], references: [id])
  groupVisit                GroupVisit?         @relation(fields: [groupVisitId], references: [id])
  recurringPass             RecurringVisitorPass? @relation(fields: [recurringPassId], references: [id])
  groupVisitMember          GroupVisitMember?
  deniedEntries             DeniedEntry[]

  @@index([companyId, status])
  @@index([companyId, expectedDate])
  @@index([companyId, hostEmployeeId])
  @@index([companyId, visitorMobile])
  @@index([visitCode])
  @@map("visits")
}

model VisitorWatchlist {
  id                  String            @id @default(cuid())
  companyId           String
  type                WatchlistType
  personName          String
  mobileNumber        String?
  email               String?
  idNumber            String?
  photo               String?
  reason              String
  actionRequired      String?
  blockDuration       WatchlistDuration
  expiryDate          DateTime?
  appliesToAllPlants  Boolean           @default(true)
  plantIds            String[]
  createdBy           String
  isActive            Boolean           @default(true)
  createdAt           DateTime          @default(now())
  updatedAt           DateTime          @updatedAt

  company             Company           @relation(fields: [companyId], references: [id], onDelete: Cascade)
  deniedEntries       DeniedEntry[]

  @@index([companyId, type, isActive])
  @@index([companyId, mobileNumber])
  @@index([companyId, idNumber])
  @@map("visitor_watchlists")
}

model GroupVisit {
  id                String           @id @default(cuid())
  companyId         String
  groupName         String
  visitCode         String           @unique
  qrCode            String?
  hostEmployeeId    String
  purpose           String
  expectedDate      DateTime
  expectedTime      String?
  plantId           String
  gateId            String?
  totalMembers      Int
  status            GroupVisitStatus  @default(PLANNED)
  createdBy         String
  createdAt         DateTime         @default(now())
  updatedAt         DateTime         @updatedAt

  company           Company          @relation(fields: [companyId], references: [id], onDelete: Cascade)
  members           GroupVisitMember[]
  visits            Visit[]

  @@index([companyId, status])
  @@index([companyId, expectedDate])
  @@map("group_visits")
}

model GroupVisitMember {
  id              String            @id @default(cuid())
  groupVisitId    String
  visitorName     String
  visitorMobile   String
  visitorEmail    String?
  visitorCompany  String?
  visitId         String?           @unique
  status          GroupMemberStatus  @default(EXPECTED)
  createdAt       DateTime          @default(now())
  updatedAt       DateTime          @updatedAt

  groupVisit      GroupVisit        @relation(fields: [groupVisitId], references: [id], onDelete: Cascade)
  visit           Visit?            @relation(fields: [visitId], references: [id])

  @@index([groupVisitId, status])
  @@map("group_visit_members")
}

model RecurringVisitorPass {
  id                           String              @id @default(cuid())
  companyId                    String
  passNumber                   String              @unique
  qrCode                       String?

  visitorName                  String
  visitorCompany               String
  visitorMobile                String
  visitorEmail                 String?
  visitorPhoto                 String?
  visitorIdType                String?
  visitorIdNumber              String?

  passType                     RecurringPassType
  validFrom                    DateTime
  validUntil                   DateTime
  allowedDays                  Int[]
  allowedTimeFrom              String?
  allowedTimeTo                String?
  allowedGateIds               String[]

  hostEmployeeId               String
  purpose                      String
  plantId                      String

  status                       RecurringPassStatus  @default(ACTIVE)
  revokedAt                    DateTime?
  revokedBy                    String?
  revokeReason                 String?

  safetyInductionCompletedAt   DateTime?
  safetyInductionValidUntil    DateTime?

  createdBy                    String
  createdAt                    DateTime             @default(now())
  updatedAt                    DateTime             @updatedAt

  company                      Company              @relation(fields: [companyId], references: [id], onDelete: Cascade)
  visits                       Visit[]

  @@index([companyId, status])
  @@index([companyId, visitorMobile])
  @@map("recurring_visitor_passes")
}

model VehicleGatePass {
  id                 String      @id @default(cuid())
  companyId          String
  passNumber         String      @unique
  vehicleRegNumber   String
  vehicleType        VehicleType
  driverName         String
  driverMobile       String?
  purpose            String
  visitId            String?
  materialDescription String?
  vehiclePhoto       String?
  entryGateId        String
  exitGateId         String?
  entryTime          DateTime    @default(now())
  exitTime           DateTime?
  plantId            String
  createdBy          String
  createdAt          DateTime    @default(now())
  updatedAt          DateTime    @updatedAt

  company            Company     @relation(fields: [companyId], references: [id], onDelete: Cascade)
  entryGate          VisitorGate @relation("VehicleEntryGate", fields: [entryGateId], references: [id])
  exitGate           VisitorGate? @relation("VehicleExitGate", fields: [exitGateId], references: [id])

  @@index([companyId, entryTime])
  @@index([companyId, vehicleRegNumber])
  @@map("vehicle_gate_passes")
}

model MaterialGatePass {
  id                  String              @id @default(cuid())
  companyId           String
  passNumber          String              @unique
  type                MaterialGatePassType
  description         String
  quantityIssued      String?
  quantityReturned    String?
  visitId             String?
  authorizedBy        String
  purpose             String
  expectedReturnDate  DateTime?
  returnedAt          DateTime?
  returnStatus        MaterialReturnStatus @default(NOT_APPLICABLE)
  gateId              String
  plantId             String
  createdBy           String
  createdAt           DateTime            @default(now())
  updatedAt           DateTime            @updatedAt

  company             Company             @relation(fields: [companyId], references: [id], onDelete: Cascade)
  gate                VisitorGate         @relation(fields: [gateId], references: [id])

  @@index([companyId, type])
  @@index([companyId, returnStatus])
  @@map("material_gate_passes")
}

model VisitorManagementConfig {
  id                          String            @id @default(cuid())
  companyId                   String            @unique

  preRegistrationEnabled      Boolean           @default(true)
  qrSelfRegistrationEnabled   Boolean           @default(true)
  walkInAllowed               Boolean           @default(true)

  photoCapture                ConfigRequirement @default(PER_VISITOR_TYPE)
  idVerification              ConfigRequirement @default(PER_VISITOR_TYPE)
  safetyInduction             ConfigRequirement @default(PER_VISITOR_TYPE)
  ndaRequired                 ConfigRequirement @default(PER_VISITOR_TYPE)

  badgePrintingEnabled        Boolean           @default(true)
  digitalBadgeEnabled         Boolean           @default(true)

  walkInApprovalRequired      Boolean           @default(true)
  qrSelfRegApprovalRequired   Boolean           @default(true)
  approvalTimeoutMinutes      Int               @default(15)
  autoRejectAfterMinutes      Int               @default(30)

  overstayAlertEnabled        Boolean           @default(true)
  defaultMaxDurationMinutes   Int               @default(480)
  autoCheckOutEnabled         Boolean           @default(false)
  autoCheckOutTime            String            @default("20:00")

  vehicleGatePassEnabled      Boolean           @default(true)
  materialGatePassEnabled     Boolean           @default(true)
  recurringPassEnabled        Boolean           @default(true)
  groupVisitEnabled           Boolean           @default(true)
  emergencyMusterEnabled      Boolean           @default(true)

  privacyConsentText          String?
  checkInStepsOrder           Json?

  createdAt                   DateTime          @default(now())
  updatedAt                   DateTime          @updatedAt

  company                     Company           @relation(fields: [companyId], references: [id], onDelete: Cascade)

  @@map("visitor_management_configs")
}

model DeniedEntry {
  id              String        @id @default(cuid())
  companyId       String
  visitorName     String
  visitorMobile   String?
  visitorCompany  String?
  visitorPhoto    String?
  denialReason    DenialReason
  denialDetails   String?
  visitId         String?
  watchlistId     String?
  gateId          String?
  plantId         String
  deniedAt        DateTime      @default(now())
  deniedBy        String
  matchedField    String?
  matchedValue    String?
  createdAt       DateTime      @default(now())

  company         Company       @relation(fields: [companyId], references: [id], onDelete: Cascade)
  visit           Visit?        @relation(fields: [visitId], references: [id])
  watchlistEntry  VisitorWatchlist? @relation(fields: [watchlistId], references: [id])

  @@index([companyId, deniedAt])
  @@index([companyId, denialReason])
  @@map("denied_entries")
}
```

### 2.1 Required Relation Additions to Company Model

Add these relation fields to the existing `Company` model in the appropriate platform prisma file:

```prisma
// In the Company model, add:
visitorTypes              VisitorType[]
visitorGates              VisitorGate[]
safetyInductions          SafetyInduction[]
visits                    Visit[]
visitorWatchlists         VisitorWatchlist[]
groupVisits               GroupVisit[]
recurringVisitorPasses    RecurringVisitorPass[]
vehicleGatePasses         VehicleGatePass[]
materialGatePasses        MaterialGatePass[]
visitorManagementConfig   VisitorManagementConfig?
deniedEntries             DeniedEntry[]
```

---

## 3. Backend Implementation -- File-by-File Specification

### 3.1 Main Router: `src/modules/visitors/routes.ts`

Replaces the existing stub file.

```typescript
import { Router } from 'express';
import { requirePermissions } from '../../middleware/auth.middleware';
import { requireModuleEnabled } from '../../middleware/module.middleware';
import { visitRoutes } from './core/visit.routes';
import { visitorTypeRoutes } from './config/visitor-type.routes';
import { gateRoutes } from './config/gate.routes';
import { safetyInductionRoutes } from './config/safety-induction.routes';
import { vmsConfigRoutes } from './config/vms-config.routes';
import { watchlistRoutes } from './security/watchlist.routes';
import { deniedEntryRoutes } from './security/denied-entry.routes';
import { recurringPassRoutes } from './passes/recurring-pass.routes';
import { vehiclePassRoutes } from './passes/vehicle-pass.routes';
import { materialPassRoutes } from './passes/material-pass.routes';
import { groupVisitRoutes } from './group/group-visit.routes';
import { dashboardRoutes } from './dashboard/dashboard.routes';
import { reportsRoutes } from './reports/reports.routes';
import { emergencyRoutes } from './emergency/emergency.routes';

const router = Router();

// All VMS routes require the visitor module to be enabled
router.use(requireModuleEnabled('visitor'));

// Mount sub-routers
router.use('/visits', visitRoutes);
router.use('/types', visitorTypeRoutes);
router.use('/gates', gateRoutes);
router.use('/safety-inductions', safetyInductionRoutes);
router.use('/config', vmsConfigRoutes);
router.use('/watchlist', watchlistRoutes);
router.use('/denied-entries', deniedEntryRoutes);
router.use('/recurring-passes', recurringPassRoutes);
router.use('/vehicle-passes', vehiclePassRoutes);
router.use('/material-passes', materialPassRoutes);
router.use('/group-visits', groupVisitRoutes);
router.use('/dashboard', dashboardRoutes);
router.use('/reports', reportsRoutes);
router.use('/emergency', emergencyRoutes);

export { router as visitorsRoutes };
```

---

### 3.2 Core Visit Management

#### 3.2.1 `src/modules/visitors/core/visit.types.ts`

```typescript
export interface CreateVisitInput {
  visitorName: string;
  visitorMobile: string;
  visitorEmail?: string;
  visitorCompany?: string;
  visitorDesignation?: string;
  visitorTypeId: string;
  purpose: string; // VisitPurpose enum value
  purposeNotes?: string;
  expectedDate: string; // ISO date string
  expectedTime?: string; // HH:mm
  expectedDurationMinutes?: number;
  hostEmployeeId: string;
  plantId: string;
  gateId?: string;
  vehicleRegNumber?: string;
  vehicleType?: string;
  materialCarriedIn?: string;
  specialInstructions?: string;
  emergencyContact?: string;
  meetingRef?: string;
}

export interface CheckInInput {
  checkInGateId: string;
  checkInGuardId?: string;
  visitorPhoto?: string;
  governmentIdType?: string;
  governmentIdNumber?: string;
  idDocumentPhoto?: string;
  badgeFormat?: string;
}

export interface CheckOutInput {
  checkOutGateId?: string;
  checkOutMethod: string;
  badgeReturned?: boolean;
  materialOut?: string;
}

export interface ExtendVisitInput {
  additionalMinutes: number;
  reason: string;
}

export interface VisitListFilters {
  status?: string;
  visitorTypeId?: string;
  hostEmployeeId?: string;
  plantId?: string;
  gateId?: string;
  registrationMethod?: string;
  fromDate?: string;
  toDate?: string;
  search?: string;
  page: number;
  limit: number;
}
```

#### 3.2.2 `src/modules/visitors/core/visit.validators.ts`

```typescript
import { z } from 'zod';

const trimString = (val: unknown) => (typeof val === 'string' ? val.trim() : val);

export const createVisitSchema = z.object({
  visitorName: z.preprocess(trimString, z.string().min(1, 'Visitor name is required').max(200)),
  visitorMobile: z.preprocess(trimString, z.string().min(10, 'Valid mobile number required').max(15)),
  visitorEmail: z.preprocess(trimString, z.string().email().max(200)).optional(),
  visitorCompany: z.preprocess(trimString, z.string().max(200)).optional(),
  visitorDesignation: z.preprocess(trimString, z.string().max(100)).optional(),
  visitorTypeId: z.string().min(1, 'Visitor type is required'),
  purpose: z.enum(['MEETING', 'DELIVERY', 'MAINTENANCE', 'AUDIT', 'INTERVIEW', 'SITE_TOUR', 'PERSONAL', 'OTHER']),
  purposeNotes: z.preprocess(trimString, z.string().max(500)).optional(),
  expectedDate: z.string().min(1, 'Expected date is required'),
  expectedTime: z.string().regex(/^\d{2}:\d{2}$/, 'Time must be HH:mm format').optional(),
  expectedDurationMinutes: z.number().int().min(15).max(1440).optional(),
  hostEmployeeId: z.string().min(1, 'Host employee is required'),
  plantId: z.string().min(1, 'Plant is required'),
  gateId: z.string().optional(),
  vehicleRegNumber: z.preprocess(trimString, z.string().max(20)).optional(),
  vehicleType: z.preprocess(trimString, z.string().max(30)).optional(),
  materialCarriedIn: z.preprocess(trimString, z.string().max(500)).optional(),
  specialInstructions: z.preprocess(trimString, z.string().max(500)).optional(),
  emergencyContact: z.preprocess(trimString, z.string().max(100)).optional(),
  meetingRef: z.preprocess(trimString, z.string().max(50)).optional(),
});

export const createMultiVisitSchema = z.object({
  visitors: z.array(z.object({
    visitorName: z.preprocess(trimString, z.string().min(1).max(200)),
    visitorMobile: z.preprocess(trimString, z.string().min(10).max(15)),
    visitorEmail: z.preprocess(trimString, z.string().email().max(200)).optional(),
    visitorCompany: z.preprocess(trimString, z.string().max(200)).optional(),
  })).min(1, 'At least one visitor is required').max(50, 'Maximum 50 visitors'),
  visitorTypeId: z.string().min(1),
  purpose: z.enum(['MEETING', 'DELIVERY', 'MAINTENANCE', 'AUDIT', 'INTERVIEW', 'SITE_TOUR', 'PERSONAL', 'OTHER']),
  purposeNotes: z.preprocess(trimString, z.string().max(500)).optional(),
  expectedDate: z.string().min(1),
  expectedTime: z.string().regex(/^\d{2}:\d{2}$/).optional(),
  expectedDurationMinutes: z.number().int().min(15).max(1440).optional(),
  hostEmployeeId: z.string().min(1),
  plantId: z.string().min(1),
  gateId: z.string().optional(),
  specialInstructions: z.preprocess(trimString, z.string().max(500)).optional(),
});

export const updateVisitSchema = createVisitSchema.partial();

export const checkInSchema = z.object({
  checkInGateId: z.string().min(1, 'Gate is required'),
  checkInGuardId: z.string().optional(),
  visitorPhoto: z.string().url().optional(),
  governmentIdType: z.enum(['AADHAAR', 'PAN', 'DRIVING_LICENCE', 'PASSPORT', 'VOTER_ID']).optional(),
  governmentIdNumber: z.preprocess(trimString, z.string().max(50)).optional(),
  idDocumentPhoto: z.string().url().optional(),
  badgeFormat: z.enum(['DIGITAL', 'PRINTED']).optional(),
});

export const checkOutSchema = z.object({
  checkOutGateId: z.string().optional(),
  checkOutMethod: z.enum(['SECURITY_DESK', 'HOST_INITIATED', 'MOBILE_LINK', 'AUTO_CHECKOUT']),
  badgeReturned: z.boolean().optional(),
  materialOut: z.preprocess(trimString, z.string().max(500)).optional(),
});

export const extendVisitSchema = z.object({
  additionalMinutes: z.number().int().min(15, 'Minimum 15 minutes').max(1440, 'Maximum 24 hours'),
  reason: z.preprocess(trimString, z.string().min(1, 'Reason is required').max(500)),
});

export const approveRejectSchema = z.object({
  notes: z.preprocess(trimString, z.string().max(500)).optional(),
});

export const visitListQuerySchema = z.object({
  status: z.string().optional(),
  visitorTypeId: z.string().optional(),
  hostEmployeeId: z.string().optional(),
  plantId: z.string().optional(),
  gateId: z.string().optional(),
  registrationMethod: z.string().optional(),
  fromDate: z.string().optional(),
  toDate: z.string().optional(),
  search: z.string().optional(),
  page: z.coerce.number().int().min(1).default(1),
  limit: z.coerce.number().int().min(1).max(100).default(20),
});

export const completeInductionSchema = z.object({
  score: z.number().int().min(0).max(100).optional(),
  passed: z.boolean(),
});
```

#### 3.2.3 `src/modules/visitors/core/visit.service.ts`

```typescript
import { platformPrisma } from '../../../config/database';
import { ApiError } from '../../../shared/errors';
import { logger } from '../../../config/logger';
import { generateNextNumber } from '../../../shared/utils/number-series';
import { n } from '../../../shared/utils/prisma-helpers';
import crypto from 'crypto';
import type {
  CreateVisitInput,
  CheckInInput,
  CheckOutInput,
  ExtendVisitInput,
  VisitListFilters,
} from './visit.types';

class VisitService {

  /**
   * Generate a cryptographically random 6-character visit code.
   * Retries up to 3 times on collision.
   */
  private async generateVisitCode(): Promise<string> {
    const chars = 'ABCDEFGHJKLMNPQRSTUVWXYZ23456789'; // Excludes I, O, 0, 1 for readability
    for (let attempt = 0; attempt < 3; attempt++) {
      let code = '';
      const bytes = crypto.randomBytes(6);
      for (let i = 0; i < 6; i++) {
        code += chars[bytes[i] % chars.length];
      }
      const existing = await platformPrisma.visit.findUnique({ where: { visitCode: code } });
      if (!existing) return code;
    }
    throw ApiError.conflict('Unable to generate unique visit code. Please try again.');
  }

  /**
   * Create a pre-registration (single visitor)
   */
  async createVisit(companyId: string, input: CreateVisitInput, createdBy: string): Promise<any> {
    // Validate visitor type exists
    const visitorType = await platformPrisma.visitorType.findFirst({
      where: { id: input.visitorTypeId, companyId, isActive: true },
    });
    if (!visitorType) throw ApiError.notFound('Visitor type not found');

    // Check watchlist/blocklist
    await this.checkWatchlistBlocklist(companyId, input.visitorMobile, input.visitorName);

    const visitCode = await this.generateVisitCode();

    return platformPrisma.$transaction(async (tx) => {
      const visitNumber = await generateNextNumber(
        tx, companyId, ['Visitor', 'Visitor Registration'], 'Visitor Registration',
      );

      const visit = await tx.visit.create({
        data: {
          companyId,
          visitNumber,
          visitCode,
          visitorName: input.visitorName,
          visitorMobile: input.visitorMobile,
          visitorEmail: n(input.visitorEmail),
          visitorCompany: n(input.visitorCompany),
          visitorDesignation: n(input.visitorDesignation),
          visitorTypeId: input.visitorTypeId,
          purpose: input.purpose as any,
          purposeNotes: n(input.purposeNotes),
          expectedDate: new Date(input.expectedDate),
          expectedTime: n(input.expectedTime),
          expectedDurationMinutes: input.expectedDurationMinutes ?? visitorType.defaultMaxDurationMinutes ?? undefined,
          hostEmployeeId: input.hostEmployeeId,
          plantId: input.plantId,
          gateId: n(input.gateId),
          registrationMethod: 'PRE_REGISTERED',
          approvalStatus: visitorType.requireHostApproval ? 'PENDING' : 'AUTO_APPROVED',
          status: 'EXPECTED',
          vehicleRegNumber: n(input.vehicleRegNumber),
          vehicleType: n(input.vehicleType),
          materialCarriedIn: n(input.materialCarriedIn),
          specialInstructions: n(input.specialInstructions),
          emergencyContact: n(input.emergencyContact),
          meetingRef: n(input.meetingRef),
          safetyInductionStatus: visitorType.requireSafetyInduction ? 'PENDING' : 'NOT_REQUIRED',
          createdBy,
        },
        include: { visitorType: true },
      });

      // Dispatch notification to host (non-blocking)
      try {
        const { notificationService } = await import('../../../core/notifications/notification.service');
        await notificationService.dispatch({
          companyId,
          triggerEvent: 'VMS_PRE_REGISTRATION_CREATED',
          entityType: 'visit',
          entityId: visit.id,
          explicitRecipients: [input.hostEmployeeId],
          tokens: {
            visitorName: input.visitorName,
            visitorCompany: input.visitorCompany ?? '',
            visitDate: input.expectedDate,
            visitCode,
          },
          type: 'info',
        });
      } catch (err) {
        logger.warn('Failed to dispatch VMS pre-registration notification', { error: err, visitId: visit.id });
      }

      return visit;
    });
  }

  /**
   * Create multiple pre-registrations for the same meeting
   */
  async createMultiVisit(
    companyId: string,
    visitors: Array<{ visitorName: string; visitorMobile: string; visitorEmail?: string; visitorCompany?: string }>,
    commonData: Omit<CreateVisitInput, 'visitorName' | 'visitorMobile' | 'visitorEmail' | 'visitorCompany'>,
    createdBy: string,
  ): Promise<any[]> {
    const meetingRef = crypto.randomUUID().slice(0, 8).toUpperCase();
    const results: any[] = [];
    for (const visitor of visitors) {
      const visit = await this.createVisit(companyId, {
        ...commonData,
        visitorName: visitor.visitorName,
        visitorMobile: visitor.visitorMobile,
        visitorEmail: visitor.visitorEmail,
        visitorCompany: visitor.visitorCompany,
        meetingRef,
      }, createdBy);
      results.push(visit);
    }
    return results;
  }

  /**
   * List visits with filters and pagination
   */
  async listVisits(companyId: string, filters: VisitListFilters): Promise<{ data: any[]; total: number }> {
    const { page, limit, status, visitorTypeId, hostEmployeeId, plantId, gateId, registrationMethod, fromDate, toDate, search } = filters;
    const offset = (page - 1) * limit;

    const where: any = { companyId };
    if (status) where.status = status;
    if (visitorTypeId) where.visitorTypeId = visitorTypeId;
    if (hostEmployeeId) where.hostEmployeeId = hostEmployeeId;
    if (plantId) where.plantId = plantId;
    if (gateId) where.gateId = gateId;
    if (registrationMethod) where.registrationMethod = registrationMethod;
    if (fromDate || toDate) {
      where.expectedDate = {};
      if (fromDate) where.expectedDate.gte = new Date(fromDate);
      if (toDate) where.expectedDate.lte = new Date(toDate);
    }
    if (search) {
      where.OR = [
        { visitorName: { contains: search, mode: 'insensitive' } },
        { visitorMobile: { contains: search } },
        { visitorCompany: { contains: search, mode: 'insensitive' } },
        { visitCode: { contains: search, mode: 'insensitive' } },
        { visitNumber: { contains: search, mode: 'insensitive' } },
      ];
    }

    const [data, total] = await Promise.all([
      platformPrisma.visit.findMany({
        where,
        skip: offset,
        take: limit,
        orderBy: { expectedDate: 'desc' },
        include: { visitorType: true },
      }),
      platformPrisma.visit.count({ where }),
    ]);

    return { data, total };
  }

  /**
   * Get visit by ID
   */
  async getVisitById(companyId: string, id: string): Promise<any> {
    const visit = await platformPrisma.visit.findFirst({
      where: { id, companyId },
      include: {
        visitorType: true,
        checkInGate: true,
        checkOutGate: true,
        assignedGate: true,
        groupVisit: true,
        recurringPass: true,
      },
    });
    if (!visit) throw ApiError.notFound('Visit not found');
    return visit;
  }

  /**
   * Get visit by visit code (for QR scan / code entry)
   */
  async getVisitByCode(visitCode: string): Promise<any> {
    const visit = await platformPrisma.visit.findUnique({
      where: { visitCode },
      include: { visitorType: true },
    });
    if (!visit) throw ApiError.notFound('Visit not found for the provided code');
    return visit;
  }

  /**
   * Update visit (pre-registration only, before check-in)
   */
  async updateVisit(companyId: string, id: string, input: Partial<CreateVisitInput>, updatedBy: string): Promise<any> {
    const visit = await platformPrisma.visit.findFirst({ where: { id, companyId } });
    if (!visit) throw ApiError.notFound('Visit not found');
    if (!['EXPECTED', 'ARRIVED'].includes(visit.status)) {
      throw ApiError.badRequest('Cannot update a visit that has already been checked in or completed');
    }

    return platformPrisma.visit.update({
      where: { id },
      data: {
        ...(input.visitorName && { visitorName: input.visitorName }),
        ...(input.visitorMobile && { visitorMobile: input.visitorMobile }),
        ...(input.visitorEmail !== undefined && { visitorEmail: n(input.visitorEmail) }),
        ...(input.visitorCompany !== undefined && { visitorCompany: n(input.visitorCompany) }),
        ...(input.visitorDesignation !== undefined && { visitorDesignation: n(input.visitorDesignation) }),
        ...(input.visitorTypeId && { visitorTypeId: input.visitorTypeId }),
        ...(input.purpose && { purpose: input.purpose as any }),
        ...(input.purposeNotes !== undefined && { purposeNotes: n(input.purposeNotes) }),
        ...(input.expectedDate && { expectedDate: new Date(input.expectedDate) }),
        ...(input.expectedTime !== undefined && { expectedTime: n(input.expectedTime) }),
        ...(input.expectedDurationMinutes && { expectedDurationMinutes: input.expectedDurationMinutes }),
        ...(input.hostEmployeeId && { hostEmployeeId: input.hostEmployeeId }),
        ...(input.plantId && { plantId: input.plantId }),
        ...(input.gateId !== undefined && { gateId: n(input.gateId) }),
        ...(input.vehicleRegNumber !== undefined && { vehicleRegNumber: n(input.vehicleRegNumber) }),
        ...(input.vehicleType !== undefined && { vehicleType: n(input.vehicleType) }),
        ...(input.materialCarriedIn !== undefined && { materialCarriedIn: n(input.materialCarriedIn) }),
        ...(input.specialInstructions !== undefined && { specialInstructions: n(input.specialInstructions) }),
        ...(input.emergencyContact !== undefined && { emergencyContact: n(input.emergencyContact) }),
        updatedBy,
      },
      include: { visitorType: true },
    });
  }

  /**
   * Cancel a visit
   */
  async cancelVisit(companyId: string, id: string, cancelledBy: string): Promise<any> {
    const visit = await platformPrisma.visit.findFirst({ where: { id, companyId } });
    if (!visit) throw ApiError.notFound('Visit not found');
    if (['CHECKED_IN', 'CHECKED_OUT', 'AUTO_CHECKED_OUT'].includes(visit.status)) {
      throw ApiError.badRequest('Cannot cancel a visit that is already in progress or completed');
    }

    return platformPrisma.visit.update({
      where: { id },
      data: { status: 'CANCELLED', updatedBy: cancelledBy },
    });
  }

  /**
   * Check in a visitor — atomic conditional update to prevent duplicates
   */
  async checkIn(companyId: string, id: string, input: CheckInInput, guardId: string): Promise<any> {
    return platformPrisma.$transaction(async (tx) => {
      // Atomic conditional update: only update if status is EXPECTED or ARRIVED
      const updated = await tx.$executeRaw`
        UPDATE visits
        SET status = 'CHECKED_IN',
            "checkInTime" = NOW(),
            "checkInGateId" = ${input.checkInGateId},
            "checkInGuardId" = ${guardId},
            "visitorPhoto" = COALESCE(${input.visitorPhoto ?? null}, "visitorPhoto"),
            "governmentIdType" = COALESCE(${input.governmentIdType ?? null}, "governmentIdType"),
            "governmentIdNumber" = COALESCE(${input.governmentIdNumber ?? null}, "governmentIdNumber"),
            "idDocumentPhoto" = COALESCE(${input.idDocumentPhoto ?? null}, "idDocumentPhoto"),
            "badgeFormat" = COALESCE(${input.badgeFormat ?? null}, "badgeFormat"),
            "updatedAt" = NOW(),
            "updatedBy" = ${guardId}
        WHERE id = ${id}
          AND "companyId" = ${companyId}
          AND status IN ('EXPECTED', 'ARRIVED')
      `;

      if (updated === 0) {
        // Check if visit exists and why it could not be checked in
        const existing = await tx.visit.findFirst({ where: { id, companyId } });
        if (!existing) throw ApiError.notFound('Visit not found');
        if (existing.status === 'CHECKED_IN') {
          throw ApiError.conflict(
            `This visitor is already checked in (checked in at ${existing.checkInTime?.toISOString()})`,
          );
        }
        throw ApiError.badRequest(`Cannot check in a visit with status: ${existing.status}`);
      }

      // Generate badge number
      const badgeNumber = await generateNextNumber(
        tx, companyId, ['Visitor Badge', 'Badge'], 'Visitor Badge',
      );
      await tx.visit.update({
        where: { id },
        data: { badgeNumber },
      });

      const visit = await tx.visit.findUnique({
        where: { id },
        include: { visitorType: true, checkInGate: true },
      });

      // Dispatch host notification (non-blocking)
      try {
        const { notificationService } = await import('../../../core/notifications/notification.service');
        await notificationService.dispatch({
          companyId,
          triggerEvent: 'VMS_VISITOR_CHECKED_IN',
          entityType: 'visit',
          entityId: id,
          explicitRecipients: [visit!.hostEmployeeId],
          tokens: {
            visitorName: visit!.visitorName,
            gate: visit!.checkInGate?.name ?? 'Unknown',
            badgeNumber: badgeNumber,
          },
          type: 'info',
        });
      } catch (err) {
        logger.warn('Failed to dispatch VMS check-in notification', { error: err, visitId: id });
      }

      return visit;
    });
  }

  /**
   * Check out a visitor — atomic conditional update
   */
  async checkOut(companyId: string, id: string, input: CheckOutInput, userId: string): Promise<any> {
    return platformPrisma.$transaction(async (tx) => {
      const updated = await tx.$executeRaw`
        UPDATE visits
        SET status = 'CHECKED_OUT',
            "checkOutTime" = NOW(),
            "checkOutGateId" = ${input.checkOutGateId ?? null},
            "checkOutMethod" = ${input.checkOutMethod}::"CheckOutMethod",
            "badgeReturned" = ${input.badgeReturned ?? null},
            "materialOut" = ${input.materialOut ?? null},
            "updatedAt" = NOW(),
            "updatedBy" = ${userId}
        WHERE id = ${id}
          AND "companyId" = ${companyId}
          AND status = 'CHECKED_IN'
      `;

      if (updated === 0) {
        const existing = await tx.visit.findFirst({ where: { id, companyId } });
        if (!existing) throw ApiError.notFound('Visit not found');
        if (existing.status === 'CHECKED_OUT' || existing.status === 'AUTO_CHECKED_OUT') {
          throw ApiError.conflict('This visitor has already been checked out');
        }
        throw ApiError.badRequest(`Cannot check out a visit with status: ${existing.status}`);
      }

      // Calculate visit duration
      const visit = await tx.visit.findUnique({ where: { id } });
      if (visit?.checkInTime && visit?.checkOutTime) {
        const durationMs = visit.checkOutTime.getTime() - visit.checkInTime.getTime();
        const durationMinutes = Math.round(durationMs / 60000);
        await tx.visit.update({
          where: { id },
          data: { visitDurationMinutes: durationMinutes },
        });
      }

      const final = await tx.visit.findUnique({
        where: { id },
        include: { visitorType: true },
      });

      // Dispatch host notification (non-blocking)
      try {
        const { notificationService } = await import('../../../core/notifications/notification.service');
        await notificationService.dispatch({
          companyId,
          triggerEvent: 'VMS_VISITOR_CHECKED_OUT',
          entityType: 'visit',
          entityId: id,
          explicitRecipients: [final!.hostEmployeeId],
          tokens: {
            visitorName: final!.visitorName,
            duration: `${final!.visitDurationMinutes ?? 0} minutes`,
          },
          type: 'info',
        });
      } catch (err) {
        logger.warn('Failed to dispatch VMS check-out notification', { error: err, visitId: id });
      }

      return final;
    });
  }

  /**
   * Approve a visit
   */
  async approveVisit(companyId: string, id: string, approvedBy: string, notes?: string): Promise<any> {
    const visit = await platformPrisma.visit.findFirst({ where: { id, companyId } });
    if (!visit) throw ApiError.notFound('Visit not found');
    if (visit.approvalStatus !== 'PENDING') {
      throw ApiError.badRequest(`Visit is already ${visit.approvalStatus.toLowerCase()}`);
    }

    return platformPrisma.visit.update({
      where: { id },
      data: {
        approvalStatus: 'APPROVED',
        approvedBy,
        approvalTimestamp: new Date(),
        approvalNotes: n(notes),
        updatedBy: approvedBy,
      },
      include: { visitorType: true },
    });
  }

  /**
   * Reject a visit
   */
  async rejectVisit(companyId: string, id: string, rejectedBy: string, notes?: string): Promise<any> {
    const visit = await platformPrisma.visit.findFirst({ where: { id, companyId } });
    if (!visit) throw ApiError.notFound('Visit not found');
    if (visit.approvalStatus !== 'PENDING') {
      throw ApiError.badRequest(`Visit is already ${visit.approvalStatus.toLowerCase()}`);
    }

    const updated = await platformPrisma.visit.update({
      where: { id },
      data: {
        approvalStatus: 'REJECTED',
        status: 'REJECTED',
        approvedBy: rejectedBy,
        approvalTimestamp: new Date(),
        approvalNotes: n(notes),
        updatedBy: rejectedBy,
      },
    });

    // Create denied entry record
    await platformPrisma.deniedEntry.create({
      data: {
        companyId,
        visitorName: visit.visitorName,
        visitorMobile: visit.visitorMobile,
        visitorCompany: visit.visitorCompany,
        denialReason: 'HOST_REJECTED',
        denialDetails: notes,
        visitId: id,
        plantId: visit.plantId,
        deniedBy: rejectedBy,
      },
    });

    return updated;
  }

  /**
   * Extend visit duration
   */
  async extendVisit(companyId: string, id: string, input: ExtendVisitInput, extendedBy: string): Promise<any> {
    const visit = await platformPrisma.visit.findFirst({ where: { id, companyId } });
    if (!visit) throw ApiError.notFound('Visit not found');
    if (visit.status !== 'CHECKED_IN') {
      throw ApiError.badRequest('Can only extend an active (checked-in) visit');
    }

    // Load config for max extensions
    const config = await platformPrisma.visitorManagementConfig.findUnique({ where: { companyId } });
    const maxExtensions = 3; // Default, could be in config

    if (visit.extensionCount >= maxExtensions) {
      throw ApiError.badRequest(`Maximum ${maxExtensions} extensions allowed per visit`);
    }

    const currentDuration = visit.expectedDurationMinutes ?? 480;
    const newDuration = currentDuration + input.additionalMinutes;
    if (newDuration > 1440) {
      throw ApiError.badRequest('Total visit duration cannot exceed 24 hours');
    }

    return platformPrisma.visit.update({
      where: { id },
      data: {
        expectedDurationMinutes: newDuration,
        originalDurationMinutes: visit.originalDurationMinutes ?? currentDuration,
        extensionCount: visit.extensionCount + 1,
        lastExtendedAt: new Date(),
        lastExtendedBy: extendedBy,
        updatedBy: extendedBy,
      },
      include: { visitorType: true },
    });
  }

  /**
   * Complete safety induction for a visit
   */
  async completeInduction(companyId: string, id: string, score: number | undefined, passed: boolean): Promise<any> {
    const visit = await platformPrisma.visit.findFirst({ where: { id, companyId } });
    if (!visit) throw ApiError.notFound('Visit not found');

    return platformPrisma.visit.update({
      where: { id },
      data: {
        safetyInductionStatus: passed ? 'COMPLETED' : 'FAILED',
        safetyInductionScore: score,
        safetyInductionTimestamp: new Date(),
      },
    });
  }

  /**
   * Check visitor against watchlist/blocklist.
   * Throws ApiError if blocklisted. Returns watchlist match if found.
   */
  async checkWatchlistBlocklist(
    companyId: string,
    mobile: string,
    name: string,
    idNumber?: string,
  ): Promise<any | null> {
    const conditions: any[] = [];
    if (mobile) conditions.push({ mobileNumber: mobile });
    if (idNumber) conditions.push({ idNumber });

    if (conditions.length === 0) return null;

    const entries = await platformPrisma.visitorWatchlist.findMany({
      where: {
        companyId,
        isActive: true,
        OR: conditions,
        // Exclude expired UNTIL_DATE entries
        NOT: {
          blockDuration: 'UNTIL_DATE',
          expiryDate: { lt: new Date() },
        },
      },
    });

    const blocklisted = entries.find(e => e.type === 'BLOCKLIST');
    if (blocklisted) {
      throw ApiError.badRequest(
        `Entry denied: ${blocklisted.reason}. This person is on the blocklist.`,
      );
    }

    const watchlisted = entries.find(e => e.type === 'WATCHLIST');
    return watchlisted ?? null;
  }

  /**
   * Walk-in registration — creates visit + sends approval request to host
   */
  async createWalkIn(companyId: string, input: CreateVisitInput, createdBy: string): Promise<any> {
    const visit = await this.createVisit(companyId, {
      ...input,
    }, createdBy);

    // Override registration method
    const updated = await platformPrisma.visit.update({
      where: { id: visit.id },
      data: {
        registrationMethod: 'WALK_IN',
        status: 'ARRIVED',
      },
      include: { visitorType: true },
    });

    // If approval is required, send approval request to host
    const config = await platformPrisma.visitorManagementConfig.findUnique({ where: { companyId } });
    if (config?.walkInApprovalRequired) {
      try {
        const { notificationService } = await import('../../../core/notifications/notification.service');
        await notificationService.dispatch({
          companyId,
          triggerEvent: 'VMS_HOST_APPROVAL_REQUEST',
          entityType: 'visit',
          entityId: visit.id,
          explicitRecipients: [input.hostEmployeeId],
          tokens: {
            visitorName: input.visitorName,
            visitorCompany: input.visitorCompany ?? '',
            purpose: input.purpose,
          },
          type: 'urgent',
        });
      } catch (err) {
        logger.warn('Failed to dispatch VMS approval request', { error: err, visitId: visit.id });
      }
    }

    return updated;
  }

  /**
   * Auto check-out all visitors still checked in at end of day.
   * Called by cron job.
   */
  async autoCheckOutAll(companyId: string): Promise<number> {
    const result = await platformPrisma.$executeRaw`
      UPDATE visits
      SET status = 'AUTO_CHECKED_OUT',
          "checkOutTime" = NOW(),
          "checkOutMethod" = 'AUTO_CHECKOUT',
          "updatedAt" = NOW()
      WHERE "companyId" = ${companyId}
        AND status = 'CHECKED_IN'
    `;
    return result;
  }

  /**
   * Mark no-show for expired pre-registrations (>7 days old, still EXPECTED).
   * Called by cron job.
   */
  async markNoShows(): Promise<number> {
    const sevenDaysAgo = new Date();
    sevenDaysAgo.setDate(sevenDaysAgo.getDate() - 7);

    const result = await platformPrisma.$executeRaw`
      UPDATE visits
      SET status = 'NO_SHOW',
          "updatedAt" = NOW()
      WHERE status = 'EXPECTED'
        AND "expectedDate" < ${sevenDaysAgo}
    `;
    return result;
  }

  /**
   * Get overstaying visitors for a company.
   */
  async getOverstayingVisitors(companyId: string): Promise<any[]> {
    const visitors = await platformPrisma.visit.findMany({
      where: {
        companyId,
        status: 'CHECKED_IN',
        checkInTime: { not: null },
      },
      include: { visitorType: true, checkInGate: true },
    });

    const now = new Date();
    return visitors.filter(v => {
      if (!v.checkInTime || !v.expectedDurationMinutes) return false;
      const expectedEnd = new Date(v.checkInTime.getTime() + v.expectedDurationMinutes * 60000);
      return now > expectedEnd;
    });
  }
}

export const visitService = new VisitService();
```

#### 3.2.4 `src/modules/visitors/core/visit.controller.ts`

```typescript
import { Request, Response } from 'express';
import { asyncHandler } from '../../../middleware/error.middleware';
import { ApiError } from '../../../shared/errors';
import { createSuccessResponse, createPaginatedResponse } from '../../../shared/utils';
import { visitService } from './visit.service';
import {
  createVisitSchema,
  createMultiVisitSchema,
  updateVisitSchema,
  checkInSchema,
  checkOutSchema,
  extendVisitSchema,
  approveRejectSchema,
  visitListQuerySchema,
  completeInductionSchema,
} from './visit.validators';

class VisitController {

  createVisit = asyncHandler(async (req: Request, res: Response) => {
    const companyId = req.user?.companyId;
    if (!companyId) throw ApiError.badRequest('Company ID is required');
    const parsed = createVisitSchema.safeParse(req.body);
    if (!parsed.success) throw ApiError.badRequest(parsed.error.errors.map(e => e.message).join(', '));
    const result = await visitService.createVisit(companyId, parsed.data, req.user!.employeeId ?? req.user!.id);
    res.status(201).json(createSuccessResponse(result, 'Visit pre-registration created'));
  });

  createMultiVisit = asyncHandler(async (req: Request, res: Response) => {
    const companyId = req.user?.companyId;
    if (!companyId) throw ApiError.badRequest('Company ID is required');
    const parsed = createMultiVisitSchema.safeParse(req.body);
    if (!parsed.success) throw ApiError.badRequest(parsed.error.errors.map(e => e.message).join(', '));
    const { visitors, ...commonData } = parsed.data;
    const result = await visitService.createMultiVisit(companyId, visitors, commonData, req.user!.employeeId ?? req.user!.id);
    res.status(201).json(createSuccessResponse(result, `${result.length} visit(s) created`));
  });

  createWalkIn = asyncHandler(async (req: Request, res: Response) => {
    const companyId = req.user?.companyId;
    if (!companyId) throw ApiError.badRequest('Company ID is required');
    const parsed = createVisitSchema.safeParse(req.body);
    if (!parsed.success) throw ApiError.badRequest(parsed.error.errors.map(e => e.message).join(', '));
    const result = await visitService.createWalkIn(companyId, parsed.data, req.user!.employeeId ?? req.user!.id);
    res.status(201).json(createSuccessResponse(result, 'Walk-in visit registered'));
  });

  listVisits = asyncHandler(async (req: Request, res: Response) => {
    const companyId = req.user?.companyId;
    if (!companyId) throw ApiError.badRequest('Company ID is required');
    const parsed = visitListQuerySchema.safeParse(req.query);
    if (!parsed.success) throw ApiError.badRequest(parsed.error.errors.map(e => e.message).join(', '));
    const { data, total } = await visitService.listVisits(companyId, parsed.data);
    res.json(createPaginatedResponse(data, {
      page: parsed.data.page,
      limit: parsed.data.limit,
      total,
      totalPages: Math.ceil(total / parsed.data.limit),
    }));
  });

  getVisitById = asyncHandler(async (req: Request, res: Response) => {
    const companyId = req.user?.companyId;
    if (!companyId) throw ApiError.badRequest('Company ID is required');
    const result = await visitService.getVisitById(companyId, req.params.id);
    res.json(createSuccessResponse(result, 'Visit retrieved'));
  });

  getVisitByCode = asyncHandler(async (req: Request, res: Response) => {
    const result = await visitService.getVisitByCode(req.params.code);
    res.json(createSuccessResponse(result, 'Visit retrieved'));
  });

  updateVisit = asyncHandler(async (req: Request, res: Response) => {
    const companyId = req.user?.companyId;
    if (!companyId) throw ApiError.badRequest('Company ID is required');
    const parsed = updateVisitSchema.safeParse(req.body);
    if (!parsed.success) throw ApiError.badRequest(parsed.error.errors.map(e => e.message).join(', '));
    const result = await visitService.updateVisit(companyId, req.params.id, parsed.data, req.user!.employeeId ?? req.user!.id);
    res.json(createSuccessResponse(result, 'Visit updated'));
  });

  cancelVisit = asyncHandler(async (req: Request, res: Response) => {
    const companyId = req.user?.companyId;
    if (!companyId) throw ApiError.badRequest('Company ID is required');
    const result = await visitService.cancelVisit(companyId, req.params.id, req.user!.employeeId ?? req.user!.id);
    res.json(createSuccessResponse(result, 'Visit cancelled'));
  });

  checkIn = asyncHandler(async (req: Request, res: Response) => {
    const companyId = req.user?.companyId;
    if (!companyId) throw ApiError.badRequest('Company ID is required');
    const parsed = checkInSchema.safeParse(req.body);
    if (!parsed.success) throw ApiError.badRequest(parsed.error.errors.map(e => e.message).join(', '));
    const result = await visitService.checkIn(companyId, req.params.id, parsed.data, req.user!.employeeId ?? req.user!.id);
    res.json(createSuccessResponse(result, 'Visitor checked in'));
  });

  checkOut = asyncHandler(async (req: Request, res: Response) => {
    const companyId = req.user?.companyId;
    if (!companyId) throw ApiError.badRequest('Company ID is required');
    const parsed = checkOutSchema.safeParse(req.body);
    if (!parsed.success) throw ApiError.badRequest(parsed.error.errors.map(e => e.message).join(', '));
    const result = await visitService.checkOut(companyId, req.params.id, parsed.data, req.user!.employeeId ?? req.user!.id);
    res.json(createSuccessResponse(result, 'Visitor checked out'));
  });

  approve = asyncHandler(async (req: Request, res: Response) => {
    const companyId = req.user?.companyId;
    if (!companyId) throw ApiError.badRequest('Company ID is required');
    const parsed = approveRejectSchema.safeParse(req.body);
    if (!parsed.success) throw ApiError.badRequest(parsed.error.errors.map(e => e.message).join(', '));
    const result = await visitService.approveVisit(companyId, req.params.id, req.user!.employeeId ?? req.user!.id, parsed.data.notes);
    res.json(createSuccessResponse(result, 'Visit approved'));
  });

  reject = asyncHandler(async (req: Request, res: Response) => {
    const companyId = req.user?.companyId;
    if (!companyId) throw ApiError.badRequest('Company ID is required');
    const parsed = approveRejectSchema.safeParse(req.body);
    if (!parsed.success) throw ApiError.badRequest(parsed.error.errors.map(e => e.message).join(', '));
    const result = await visitService.rejectVisit(companyId, req.params.id, req.user!.employeeId ?? req.user!.id, parsed.data.notes);
    res.json(createSuccessResponse(result, 'Visit rejected'));
  });

  extend = asyncHandler(async (req: Request, res: Response) => {
    const companyId = req.user?.companyId;
    if (!companyId) throw ApiError.badRequest('Company ID is required');
    const parsed = extendVisitSchema.safeParse(req.body);
    if (!parsed.success) throw ApiError.badRequest(parsed.error.errors.map(e => e.message).join(', '));
    const result = await visitService.extendVisit(companyId, req.params.id, parsed.data, req.user!.employeeId ?? req.user!.id);
    res.json(createSuccessResponse(result, 'Visit extended'));
  });

  completeInduction = asyncHandler(async (req: Request, res: Response) => {
    const companyId = req.user?.companyId;
    if (!companyId) throw ApiError.badRequest('Company ID is required');
    const parsed = completeInductionSchema.safeParse(req.body);
    if (!parsed.success) throw ApiError.badRequest(parsed.error.errors.map(e => e.message).join(', '));
    const result = await visitService.completeInduction(companyId, req.params.id, parsed.data.score, parsed.data.passed);
    res.json(createSuccessResponse(result, 'Induction recorded'));
  });
}

export const visitController = new VisitController();
```

#### 3.2.5 `src/modules/visitors/core/visit.routes.ts`

```typescript
import { Router } from 'express';
import { requirePermissions } from '../../../middleware/auth.middleware';
import { visitController } from './visit.controller';

const router = Router();

// List visits (with filters)
router.get('/', requirePermissions(['visitors:read']), visitController.listVisits);

// Named routes BEFORE :id routes
router.post('/walk-in', requirePermissions(['visitors:create']), visitController.createWalkIn);
router.post('/multi', requirePermissions(['visitors:create']), visitController.createMultiVisit);
router.get('/code/:code', requirePermissions(['visitors:read']), visitController.getVisitByCode);

// Create pre-registration
router.post('/', requirePermissions(['visitors:create']), visitController.createVisit);

// Visit by ID
router.get('/:id', requirePermissions(['visitors:read']), visitController.getVisitById);
router.put('/:id', requirePermissions(['visitors:update']), visitController.updateVisit);
router.delete('/:id', requirePermissions(['visitors:delete']), visitController.cancelVisit);

// Visit actions
router.post('/:id/check-in', requirePermissions(['visitors:create']), visitController.checkIn);
router.post('/:id/check-out', requirePermissions(['visitors:create']), visitController.checkOut);
router.post('/:id/approve', requirePermissions(['visitors:approve']), visitController.approve);
router.post('/:id/reject', requirePermissions(['visitors:approve']), visitController.reject);
router.post('/:id/extend', requirePermissions(['visitors:update']), visitController.extend);
router.post('/:id/complete-induction', requirePermissions(['visitors:create']), visitController.completeInduction);

export { router as visitRoutes };
```

---

### 3.3 Visitor Type Configuration

#### 3.3.1 `src/modules/visitors/config/visitor-type.validators.ts`

```typescript
import { z } from 'zod';

const trimString = (val: unknown) => (typeof val === 'string' ? val.trim() : val);

export const createVisitorTypeSchema = z.object({
  name: z.preprocess(trimString, z.string().min(1, 'Name is required').max(100)),
  code: z.preprocess(trimString, z.string().min(1, 'Code is required').max(5).toUpperCase()),
  badgeColour: z.string().regex(/^#[0-9A-Fa-f]{6}$/, 'Must be a hex colour').default('#3B82F6'),
  requirePhoto: z.boolean().default(true),
  requireIdVerification: z.boolean().default(true),
  requireSafetyInduction: z.boolean().default(false),
  requireNda: z.boolean().default(false),
  requireHostApproval: z.boolean().default(true),
  requireEscort: z.boolean().default(false),
  defaultMaxDurationMinutes: z.number().int().min(15).max(1440).optional(),
  safetyInductionId: z.string().optional(),
  sortOrder: z.number().int().default(0),
});

export const updateVisitorTypeSchema = createVisitorTypeSchema.partial();

export const visitorTypeListQuerySchema = z.object({
  isActive: z.coerce.boolean().optional(),
  page: z.coerce.number().int().min(1).default(1),
  limit: z.coerce.number().int().min(1).max(100).default(50),
});
```

#### 3.3.2 `src/modules/visitors/config/visitor-type.service.ts`

```typescript
import { platformPrisma } from '../../../config/database';
import { ApiError } from '../../../shared/errors';
import { n } from '../../../shared/utils/prisma-helpers';

class VisitorTypeService {

  async list(companyId: string, filters: { isActive?: boolean; page: number; limit: number }) {
    const { page, limit, isActive } = filters;
    const offset = (page - 1) * limit;
    const where: any = { companyId };
    if (isActive !== undefined) where.isActive = isActive;

    const [data, total] = await Promise.all([
      platformPrisma.visitorType.findMany({
        where,
        skip: offset,
        take: limit,
        orderBy: { sortOrder: 'asc' },
      }),
      platformPrisma.visitorType.count({ where }),
    ]);

    return { data, total };
  }

  async getById(companyId: string, id: string) {
    const type = await platformPrisma.visitorType.findFirst({ where: { id, companyId } });
    if (!type) throw ApiError.notFound('Visitor type not found');
    return type;
  }

  async create(companyId: string, input: any) {
    // Check for duplicate code
    const existing = await platformPrisma.visitorType.findFirst({
      where: { companyId, code: input.code },
    });
    if (existing) throw ApiError.conflict(`Visitor type code "${input.code}" already exists`);

    return platformPrisma.visitorType.create({
      data: {
        companyId,
        name: input.name,
        code: input.code,
        badgeColour: input.badgeColour ?? '#3B82F6',
        requirePhoto: input.requirePhoto ?? true,
        requireIdVerification: input.requireIdVerification ?? true,
        requireSafetyInduction: input.requireSafetyInduction ?? false,
        requireNda: input.requireNda ?? false,
        requireHostApproval: input.requireHostApproval ?? true,
        requireEscort: input.requireEscort ?? false,
        defaultMaxDurationMinutes: input.defaultMaxDurationMinutes ?? undefined,
        safetyInductionId: n(input.safetyInductionId),
        sortOrder: input.sortOrder ?? 0,
      },
    });
  }

  async update(companyId: string, id: string, input: any) {
    const existing = await platformPrisma.visitorType.findFirst({ where: { id, companyId } });
    if (!existing) throw ApiError.notFound('Visitor type not found');

    if (input.code && input.code !== existing.code) {
      const dup = await platformPrisma.visitorType.findFirst({
        where: { companyId, code: input.code, id: { not: id } },
      });
      if (dup) throw ApiError.conflict(`Visitor type code "${input.code}" already exists`);
    }

    return platformPrisma.visitorType.update({
      where: { id },
      data: {
        ...(input.name && { name: input.name }),
        ...(input.code && { code: input.code }),
        ...(input.badgeColour && { badgeColour: input.badgeColour }),
        ...(input.requirePhoto !== undefined && { requirePhoto: input.requirePhoto }),
        ...(input.requireIdVerification !== undefined && { requireIdVerification: input.requireIdVerification }),
        ...(input.requireSafetyInduction !== undefined && { requireSafetyInduction: input.requireSafetyInduction }),
        ...(input.requireNda !== undefined && { requireNda: input.requireNda }),
        ...(input.requireHostApproval !== undefined && { requireHostApproval: input.requireHostApproval }),
        ...(input.requireEscort !== undefined && { requireEscort: input.requireEscort }),
        ...(input.defaultMaxDurationMinutes !== undefined && { defaultMaxDurationMinutes: input.defaultMaxDurationMinutes }),
        ...(input.safetyInductionId !== undefined && { safetyInductionId: n(input.safetyInductionId) }),
        ...(input.sortOrder !== undefined && { sortOrder: input.sortOrder }),
      },
    });
  }

  async deactivate(companyId: string, id: string) {
    const existing = await platformPrisma.visitorType.findFirst({ where: { id, companyId } });
    if (!existing) throw ApiError.notFound('Visitor type not found');
    if (existing.isDefault) throw ApiError.badRequest('Cannot deactivate a default visitor type');

    return platformPrisma.visitorType.update({
      where: { id },
      data: { isActive: false },
    });
  }

  /**
   * Seed default visitor types for a new company.
   * Called when VMS module is first activated.
   */
  async seedDefaults(companyId: string) {
    const defaults = [
      { name: 'Business Guest', code: 'BG', badgeColour: '#3B82F6', requireSafetyInduction: false, requireNda: false, sortOrder: 1 },
      { name: 'Vendor / Supplier', code: 'VN', badgeColour: '#22C55E', requireSafetyInduction: false, requireNda: false, sortOrder: 2 },
      { name: 'Contractor', code: 'CT', badgeColour: '#F97316', requireSafetyInduction: true, requireNda: true, sortOrder: 3 },
      { name: 'Delivery Agent', code: 'DA', badgeColour: '#EAB308', requireSafetyInduction: false, requireNda: false, requireHostApproval: false, defaultMaxDurationMinutes: 120, sortOrder: 4 },
      { name: 'Government Inspector', code: 'GI', badgeColour: '#EF4444', requireSafetyInduction: false, requireNda: false, sortOrder: 5 },
      { name: 'Job Candidate', code: 'JC', badgeColour: '#A855F7', requireSafetyInduction: false, requireNda: false, sortOrder: 6 },
      { name: 'Personal Visitor', code: 'FV', badgeColour: '#F5F5F5', requireSafetyInduction: false, requireNda: false, sortOrder: 7 },
      { name: 'VIP / Board Member', code: 'VP', badgeColour: '#F59E0B', requireSafetyInduction: false, requireNda: false, requireHostApproval: false, sortOrder: 8 },
      { name: 'Auditor', code: 'AU', badgeColour: '#1F2937', requireSafetyInduction: false, requireNda: false, sortOrder: 9 },
    ];

    for (const def of defaults) {
      const existing = await platformPrisma.visitorType.findFirst({
        where: { companyId, code: def.code },
      });
      if (!existing) {
        await platformPrisma.visitorType.create({
          data: {
            companyId,
            ...def,
            isDefault: true,
            isActive: true,
            requirePhoto: true,
            requireIdVerification: true,
            requireHostApproval: def.requireHostApproval ?? true,
            defaultMaxDurationMinutes: def.defaultMaxDurationMinutes ?? 480,
          },
        });
      }
    }
  }
}

export const visitorTypeService = new VisitorTypeService();
```

#### 3.3.3 `src/modules/visitors/config/visitor-type.controller.ts`

```typescript
import { Request, Response } from 'express';
import { asyncHandler } from '../../../middleware/error.middleware';
import { ApiError } from '../../../shared/errors';
import { createSuccessResponse, createPaginatedResponse } from '../../../shared/utils';
import { visitorTypeService } from './visitor-type.service';
import { createVisitorTypeSchema, updateVisitorTypeSchema, visitorTypeListQuerySchema } from './visitor-type.validators';

class VisitorTypeController {

  list = asyncHandler(async (req: Request, res: Response) => {
    const companyId = req.user?.companyId;
    if (!companyId) throw ApiError.badRequest('Company ID is required');
    const parsed = visitorTypeListQuerySchema.safeParse(req.query);
    if (!parsed.success) throw ApiError.badRequest(parsed.error.errors.map(e => e.message).join(', '));
    const { data, total } = await visitorTypeService.list(companyId, parsed.data);
    res.json(createPaginatedResponse(data, {
      page: parsed.data.page, limit: parsed.data.limit, total, totalPages: Math.ceil(total / parsed.data.limit),
    }));
  });

  getById = asyncHandler(async (req: Request, res: Response) => {
    const companyId = req.user?.companyId;
    if (!companyId) throw ApiError.badRequest('Company ID is required');
    const result = await visitorTypeService.getById(companyId, req.params.id);
    res.json(createSuccessResponse(result, 'Visitor type retrieved'));
  });

  create = asyncHandler(async (req: Request, res: Response) => {
    const companyId = req.user?.companyId;
    if (!companyId) throw ApiError.badRequest('Company ID is required');
    const parsed = createVisitorTypeSchema.safeParse(req.body);
    if (!parsed.success) throw ApiError.badRequest(parsed.error.errors.map(e => e.message).join(', '));
    const result = await visitorTypeService.create(companyId, parsed.data);
    res.status(201).json(createSuccessResponse(result, 'Visitor type created'));
  });

  update = asyncHandler(async (req: Request, res: Response) => {
    const companyId = req.user?.companyId;
    if (!companyId) throw ApiError.badRequest('Company ID is required');
    const parsed = updateVisitorTypeSchema.safeParse(req.body);
    if (!parsed.success) throw ApiError.badRequest(parsed.error.errors.map(e => e.message).join(', '));
    const result = await visitorTypeService.update(companyId, req.params.id, parsed.data);
    res.json(createSuccessResponse(result, 'Visitor type updated'));
  });

  deactivate = asyncHandler(async (req: Request, res: Response) => {
    const companyId = req.user?.companyId;
    if (!companyId) throw ApiError.badRequest('Company ID is required');
    const result = await visitorTypeService.deactivate(companyId, req.params.id);
    res.json(createSuccessResponse(result, 'Visitor type deactivated'));
  });
}

export const visitorTypeController = new VisitorTypeController();
```

#### 3.3.4 `src/modules/visitors/config/visitor-type.routes.ts`

```typescript
import { Router } from 'express';
import { requirePermissions } from '../../../middleware/auth.middleware';
import { visitorTypeController } from './visitor-type.controller';

const router = Router();

router.get('/', requirePermissions(['visitors:read']), visitorTypeController.list);
router.post('/', requirePermissions(['visitors:configure']), visitorTypeController.create);
router.get('/:id', requirePermissions(['visitors:read']), visitorTypeController.getById);
router.put('/:id', requirePermissions(['visitors:configure']), visitorTypeController.update);
router.delete('/:id', requirePermissions(['visitors:configure']), visitorTypeController.deactivate);

export { router as visitorTypeRoutes };
```

---

### 3.4 Gate Configuration

#### 3.4.1 `src/modules/visitors/config/gate.validators.ts`

```typescript
import { z } from 'zod';

const trimString = (val: unknown) => (typeof val === 'string' ? val.trim() : val);

export const createGateSchema = z.object({
  plantId: z.string().min(1, 'Plant is required'),
  name: z.preprocess(trimString, z.string().min(1, 'Gate name is required').max(100)),
  code: z.preprocess(trimString, z.string().min(1, 'Gate code is required').max(20)),
  type: z.enum(['MAIN', 'SERVICE', 'LOADING_DOCK', 'VIP']).default('MAIN'),
  openTime: z.string().regex(/^\d{2}:\d{2}$/, 'Time must be HH:mm').optional(),
  closeTime: z.string().regex(/^\d{2}:\d{2}$/, 'Time must be HH:mm').optional(),
  allowedVisitorTypeIds: z.array(z.string()).default([]),
});

export const updateGateSchema = createGateSchema.partial();

export const gateListQuerySchema = z.object({
  plantId: z.string().optional(),
  isActive: z.coerce.boolean().optional(),
  page: z.coerce.number().int().min(1).default(1),
  limit: z.coerce.number().int().min(1).max(100).default(50),
});
```

#### 3.4.2 `src/modules/visitors/config/gate.service.ts`

```typescript
import { platformPrisma } from '../../../config/database';
import { ApiError } from '../../../shared/errors';
import { n } from '../../../shared/utils/prisma-helpers';

class GateService {

  async list(companyId: string, filters: { plantId?: string; isActive?: boolean; page: number; limit: number }) {
    const { page, limit, plantId, isActive } = filters;
    const offset = (page - 1) * limit;
    const where: any = { companyId };
    if (plantId) where.plantId = plantId;
    if (isActive !== undefined) where.isActive = isActive;

    const [data, total] = await Promise.all([
      platformPrisma.visitorGate.findMany({ where, skip: offset, take: limit, orderBy: { name: 'asc' } }),
      platformPrisma.visitorGate.count({ where }),
    ]);
    return { data, total };
  }

  async getById(companyId: string, id: string) {
    const gate = await platformPrisma.visitorGate.findFirst({ where: { id, companyId } });
    if (!gate) throw ApiError.notFound('Gate not found');
    return gate;
  }

  async create(companyId: string, input: any) {
    const existing = await platformPrisma.visitorGate.findFirst({
      where: { companyId, code: input.code },
    });
    if (existing) throw ApiError.conflict(`Gate code "${input.code}" already exists`);

    return platformPrisma.visitorGate.create({
      data: {
        companyId,
        plantId: input.plantId,
        name: input.name,
        code: input.code,
        type: input.type ?? 'MAIN',
        openTime: n(input.openTime),
        closeTime: n(input.closeTime),
        allowedVisitorTypeIds: input.allowedVisitorTypeIds ?? [],
      },
    });
  }

  async update(companyId: string, id: string, input: any) {
    const existing = await platformPrisma.visitorGate.findFirst({ where: { id, companyId } });
    if (!existing) throw ApiError.notFound('Gate not found');

    if (input.code && input.code !== existing.code) {
      const dup = await platformPrisma.visitorGate.findFirst({
        where: { companyId, code: input.code, id: { not: id } },
      });
      if (dup) throw ApiError.conflict(`Gate code "${input.code}" already exists`);
    }

    return platformPrisma.visitorGate.update({
      where: { id },
      data: {
        ...(input.plantId && { plantId: input.plantId }),
        ...(input.name && { name: input.name }),
        ...(input.code && { code: input.code }),
        ...(input.type && { type: input.type }),
        ...(input.openTime !== undefined && { openTime: n(input.openTime) }),
        ...(input.closeTime !== undefined && { closeTime: n(input.closeTime) }),
        ...(input.allowedVisitorTypeIds && { allowedVisitorTypeIds: input.allowedVisitorTypeIds }),
      },
    });
  }

  async deactivate(companyId: string, id: string) {
    const existing = await platformPrisma.visitorGate.findFirst({ where: { id, companyId } });
    if (!existing) throw ApiError.notFound('Gate not found');
    return platformPrisma.visitorGate.update({ where: { id }, data: { isActive: false } });
  }
}

export const gateService = new GateService();
```

#### 3.4.3 `src/modules/visitors/config/gate.controller.ts`

```typescript
import { Request, Response } from 'express';
import { asyncHandler } from '../../../middleware/error.middleware';
import { ApiError } from '../../../shared/errors';
import { createSuccessResponse, createPaginatedResponse } from '../../../shared/utils';
import { gateService } from './gate.service';
import { createGateSchema, updateGateSchema, gateListQuerySchema } from './gate.validators';

class GateController {

  list = asyncHandler(async (req: Request, res: Response) => {
    const companyId = req.user?.companyId;
    if (!companyId) throw ApiError.badRequest('Company ID is required');
    const parsed = gateListQuerySchema.safeParse(req.query);
    if (!parsed.success) throw ApiError.badRequest(parsed.error.errors.map(e => e.message).join(', '));
    const { data, total } = await gateService.list(companyId, parsed.data);
    res.json(createPaginatedResponse(data, { page: parsed.data.page, limit: parsed.data.limit, total, totalPages: Math.ceil(total / parsed.data.limit) }));
  });

  getById = asyncHandler(async (req: Request, res: Response) => {
    const companyId = req.user?.companyId;
    if (!companyId) throw ApiError.badRequest('Company ID is required');
    const result = await gateService.getById(companyId, req.params.id);
    res.json(createSuccessResponse(result, 'Gate retrieved'));
  });

  create = asyncHandler(async (req: Request, res: Response) => {
    const companyId = req.user?.companyId;
    if (!companyId) throw ApiError.badRequest('Company ID is required');
    const parsed = createGateSchema.safeParse(req.body);
    if (!parsed.success) throw ApiError.badRequest(parsed.error.errors.map(e => e.message).join(', '));
    const result = await gateService.create(companyId, parsed.data);
    res.status(201).json(createSuccessResponse(result, 'Gate created'));
  });

  update = asyncHandler(async (req: Request, res: Response) => {
    const companyId = req.user?.companyId;
    if (!companyId) throw ApiError.badRequest('Company ID is required');
    const parsed = updateGateSchema.safeParse(req.body);
    if (!parsed.success) throw ApiError.badRequest(parsed.error.errors.map(e => e.message).join(', '));
    const result = await gateService.update(companyId, req.params.id, parsed.data);
    res.json(createSuccessResponse(result, 'Gate updated'));
  });

  deactivate = asyncHandler(async (req: Request, res: Response) => {
    const companyId = req.user?.companyId;
    if (!companyId) throw ApiError.badRequest('Company ID is required');
    const result = await gateService.deactivate(companyId, req.params.id);
    res.json(createSuccessResponse(result, 'Gate deactivated'));
  });
}

export const gateController = new GateController();
```

#### 3.4.4 `src/modules/visitors/config/gate.routes.ts`

```typescript
import { Router } from 'express';
import { requirePermissions } from '../../../middleware/auth.middleware';
import { gateController } from './gate.controller';

const router = Router();

router.get('/', requirePermissions(['visitors:read']), gateController.list);
router.post('/', requirePermissions(['visitors:configure']), gateController.create);
router.get('/:id', requirePermissions(['visitors:read']), gateController.getById);
router.put('/:id', requirePermissions(['visitors:configure']), gateController.update);
router.delete('/:id', requirePermissions(['visitors:configure']), gateController.deactivate);

export { router as gateRoutes };
```

---

### 3.5 Safety Induction Configuration

#### 3.5.1 `src/modules/visitors/config/safety-induction.validators.ts`

```typescript
import { z } from 'zod';

const trimString = (val: unknown) => (typeof val === 'string' ? val.trim() : val);

export const createSafetyInductionSchema = z.object({
  name: z.preprocess(trimString, z.string().min(1, 'Name is required').max(200)),
  type: z.enum(['VIDEO', 'SLIDES', 'QUESTIONNAIRE', 'DECLARATION']),
  contentUrl: z.string().url().optional(),
  questions: z.array(z.object({
    question: z.string(),
    options: z.array(z.string()),
    correctAnswer: z.number().int(),
  })).optional(),
  passingScore: z.number().int().min(0).max(100).default(80),
  durationSeconds: z.number().int().min(10).max(600).default(120),
  validityDays: z.number().int().min(1).max(365).default(30),
  plantId: z.string().optional(),
});

export const updateSafetyInductionSchema = createSafetyInductionSchema.partial();

export const safetyInductionListQuerySchema = z.object({
  plantId: z.string().optional(),
  isActive: z.coerce.boolean().optional(),
  page: z.coerce.number().int().min(1).default(1),
  limit: z.coerce.number().int().min(1).max(100).default(50),
});
```

#### 3.5.2 `src/modules/visitors/config/safety-induction.service.ts`

```typescript
import { platformPrisma } from '../../../config/database';
import { ApiError } from '../../../shared/errors';
import { n } from '../../../shared/utils/prisma-helpers';

class SafetyInductionService {

  async list(companyId: string, filters: { plantId?: string; isActive?: boolean; page: number; limit: number }) {
    const { page, limit, plantId, isActive } = filters;
    const offset = (page - 1) * limit;
    const where: any = { companyId };
    if (plantId) where.plantId = plantId;
    if (isActive !== undefined) where.isActive = isActive;

    const [data, total] = await Promise.all([
      platformPrisma.safetyInduction.findMany({ where, skip: offset, take: limit, orderBy: { name: 'asc' } }),
      platformPrisma.safetyInduction.count({ where }),
    ]);
    return { data, total };
  }

  async getById(companyId: string, id: string) {
    const induction = await platformPrisma.safetyInduction.findFirst({ where: { id, companyId } });
    if (!induction) throw ApiError.notFound('Safety induction not found');
    return induction;
  }

  async create(companyId: string, input: any) {
    return platformPrisma.safetyInduction.create({
      data: {
        companyId,
        name: input.name,
        type: input.type,
        contentUrl: n(input.contentUrl),
        questions: input.questions ?? undefined,
        passingScore: input.passingScore ?? 80,
        durationSeconds: input.durationSeconds ?? 120,
        validityDays: input.validityDays ?? 30,
        plantId: n(input.plantId),
      },
    });
  }

  async update(companyId: string, id: string, input: any) {
    const existing = await platformPrisma.safetyInduction.findFirst({ where: { id, companyId } });
    if (!existing) throw ApiError.notFound('Safety induction not found');

    return platformPrisma.safetyInduction.update({
      where: { id },
      data: {
        ...(input.name && { name: input.name }),
        ...(input.type && { type: input.type }),
        ...(input.contentUrl !== undefined && { contentUrl: n(input.contentUrl) }),
        ...(input.questions !== undefined && { questions: input.questions }),
        ...(input.passingScore !== undefined && { passingScore: input.passingScore }),
        ...(input.durationSeconds !== undefined && { durationSeconds: input.durationSeconds }),
        ...(input.validityDays !== undefined && { validityDays: input.validityDays }),
        ...(input.plantId !== undefined && { plantId: n(input.plantId) }),
      },
    });
  }

  async deactivate(companyId: string, id: string) {
    const existing = await platformPrisma.safetyInduction.findFirst({ where: { id, companyId } });
    if (!existing) throw ApiError.notFound('Safety induction not found');
    return platformPrisma.safetyInduction.update({ where: { id }, data: { isActive: false } });
  }
}

export const safetyInductionService = new SafetyInductionService();
```

#### 3.5.3 `src/modules/visitors/config/safety-induction.controller.ts`

Same class-based pattern as VisitorTypeController: `list`, `getById`, `create`, `update`, `deactivate` methods. Each follows `asyncHandler` + `companyId` extraction + `safeParse` + service call + `createSuccessResponse` / `createPaginatedResponse`.

#### 3.5.4 `src/modules/visitors/config/safety-induction.routes.ts`

```typescript
import { Router } from 'express';
import { requirePermissions } from '../../../middleware/auth.middleware';
import { safetyInductionController } from './safety-induction.controller';

const router = Router();

router.get('/', requirePermissions(['visitors:read']), safetyInductionController.list);
router.post('/', requirePermissions(['visitors:configure']), safetyInductionController.create);
router.get('/:id', requirePermissions(['visitors:read']), safetyInductionController.getById);
router.put('/:id', requirePermissions(['visitors:configure']), safetyInductionController.update);
router.delete('/:id', requirePermissions(['visitors:configure']), safetyInductionController.deactivate);

export { router as safetyInductionRoutes };
```

---

### 3.6 VMS Configuration

#### 3.6.1 `src/modules/visitors/config/vms-config.routes.ts`

```typescript
import { Router } from 'express';
import { requirePermissions } from '../../../middleware/auth.middleware';
import { vmsConfigController } from './vms-config.controller';

const router = Router();

router.get('/', requirePermissions(['visitors:read']), vmsConfigController.get);
router.put('/', requirePermissions(['visitors:configure']), vmsConfigController.update);

export { router as vmsConfigRoutes };
```

#### 3.6.2 `src/modules/visitors/config/vms-config.service.ts`

```typescript
import { platformPrisma } from '../../../config/database';

class VmsConfigService {

  async get(companyId: string) {
    let config = await platformPrisma.visitorManagementConfig.findUnique({ where: { companyId } });
    if (!config) {
      // Create default config on first access
      config = await platformPrisma.visitorManagementConfig.create({
        data: { companyId },
      });
    }
    return config;
  }

  async update(companyId: string, input: any) {
    return platformPrisma.visitorManagementConfig.upsert({
      where: { companyId },
      create: { companyId, ...input },
      update: input,
    });
  }
}

export const vmsConfigService = new VmsConfigService();
```

#### 3.6.3 `src/modules/visitors/config/vms-config.controller.ts`

Standard controller with `get` and `update` methods following the same pattern.

---

### 3.7 Watchlist & Blocklist

#### 3.7.1 `src/modules/visitors/security/watchlist.validators.ts`

```typescript
import { z } from 'zod';

const trimString = (val: unknown) => (typeof val === 'string' ? val.trim() : val);

export const createWatchlistSchema = z.object({
  type: z.enum(['BLOCKLIST', 'WATCHLIST']),
  personName: z.preprocess(trimString, z.string().min(1, 'Person name is required').max(200)),
  mobileNumber: z.preprocess(trimString, z.string().max(15)).optional(),
  email: z.preprocess(trimString, z.string().email().max(200)).optional(),
  idNumber: z.preprocess(trimString, z.string().max(50)).optional(),
  photo: z.string().url().optional(),
  reason: z.preprocess(trimString, z.string().min(1, 'Reason is required').max(500)),
  actionRequired: z.preprocess(trimString, z.string().max(500)).optional(),
  blockDuration: z.enum(['PERMANENT', 'UNTIL_DATE']),
  expiryDate: z.string().optional(),
  appliesToAllPlants: z.boolean().default(true),
  plantIds: z.array(z.string()).default([]),
});

export const updateWatchlistSchema = createWatchlistSchema.partial();

export const watchlistListQuerySchema = z.object({
  type: z.enum(['BLOCKLIST', 'WATCHLIST']).optional(),
  isActive: z.coerce.boolean().optional(),
  search: z.string().optional(),
  page: z.coerce.number().int().min(1).default(1),
  limit: z.coerce.number().int().min(1).max(100).default(20),
});

export const watchlistCheckSchema = z.object({
  name: z.preprocess(trimString, z.string()).optional(),
  mobile: z.preprocess(trimString, z.string()).optional(),
  idNumber: z.preprocess(trimString, z.string()).optional(),
});
```

#### 3.7.2 `src/modules/visitors/security/watchlist.service.ts`

```typescript
import { platformPrisma } from '../../../config/database';
import { ApiError } from '../../../shared/errors';
import { n } from '../../../shared/utils/prisma-helpers';

class WatchlistService {

  async list(companyId: string, filters: { type?: string; isActive?: boolean; search?: string; page: number; limit: number }) {
    const { page, limit, type, isActive, search } = filters;
    const offset = (page - 1) * limit;
    const where: any = { companyId };
    if (type) where.type = type;
    if (isActive !== undefined) where.isActive = isActive;
    if (search) {
      where.OR = [
        { personName: { contains: search, mode: 'insensitive' } },
        { mobileNumber: { contains: search } },
        { idNumber: { contains: search } },
      ];
    }

    const [data, total] = await Promise.all([
      platformPrisma.visitorWatchlist.findMany({ where, skip: offset, take: limit, orderBy: { createdAt: 'desc' } }),
      platformPrisma.visitorWatchlist.count({ where }),
    ]);
    return { data, total };
  }

  async create(companyId: string, input: any, createdBy: string) {
    return platformPrisma.visitorWatchlist.create({
      data: {
        companyId,
        type: input.type,
        personName: input.personName,
        mobileNumber: n(input.mobileNumber),
        email: n(input.email),
        idNumber: n(input.idNumber),
        photo: n(input.photo),
        reason: input.reason,
        actionRequired: n(input.actionRequired),
        blockDuration: input.blockDuration,
        expiryDate: input.expiryDate ? new Date(input.expiryDate) : undefined,
        appliesToAllPlants: input.appliesToAllPlants ?? true,
        plantIds: input.plantIds ?? [],
        createdBy,
      },
    });
  }

  async update(companyId: string, id: string, input: any) {
    const existing = await platformPrisma.visitorWatchlist.findFirst({ where: { id, companyId } });
    if (!existing) throw ApiError.notFound('Watchlist entry not found');

    return platformPrisma.visitorWatchlist.update({
      where: { id },
      data: {
        ...(input.type && { type: input.type }),
        ...(input.personName && { personName: input.personName }),
        ...(input.mobileNumber !== undefined && { mobileNumber: n(input.mobileNumber) }),
        ...(input.email !== undefined && { email: n(input.email) }),
        ...(input.idNumber !== undefined && { idNumber: n(input.idNumber) }),
        ...(input.photo !== undefined && { photo: n(input.photo) }),
        ...(input.reason && { reason: input.reason }),
        ...(input.actionRequired !== undefined && { actionRequired: n(input.actionRequired) }),
        ...(input.blockDuration && { blockDuration: input.blockDuration }),
        ...(input.expiryDate !== undefined && { expiryDate: input.expiryDate ? new Date(input.expiryDate) : undefined }),
        ...(input.appliesToAllPlants !== undefined && { appliesToAllPlants: input.appliesToAllPlants }),
        ...(input.plantIds && { plantIds: input.plantIds }),
      },
    });
  }

  async remove(companyId: string, id: string) {
    const existing = await platformPrisma.visitorWatchlist.findFirst({ where: { id, companyId } });
    if (!existing) throw ApiError.notFound('Watchlist entry not found');
    return platformPrisma.visitorWatchlist.update({ where: { id }, data: { isActive: false } });
  }

  /**
   * Check name/mobile/ID against watchlist and blocklist.
   * Returns matching entries.
   */
  async check(companyId: string, input: { name?: string; mobile?: string; idNumber?: string }) {
    const conditions: any[] = [];
    if (input.mobile) conditions.push({ mobileNumber: input.mobile });
    if (input.idNumber) conditions.push({ idNumber: input.idNumber });
    if (conditions.length === 0) return { blocklist: [], watchlist: [] };

    const entries = await platformPrisma.visitorWatchlist.findMany({
      where: {
        companyId,
        isActive: true,
        OR: conditions,
      },
    });

    return {
      blocklist: entries.filter(e => e.type === 'BLOCKLIST'),
      watchlist: entries.filter(e => e.type === 'WATCHLIST'),
    };
  }
}

export const watchlistService = new WatchlistService();
```

#### 3.7.3 `src/modules/visitors/security/watchlist.controller.ts`

Standard controller: `list`, `create`, `update`, `remove`, `check` methods.

#### 3.7.4 `src/modules/visitors/security/watchlist.routes.ts`

```typescript
import { Router } from 'express';
import { requirePermissions } from '../../../middleware/auth.middleware';
import { watchlistController } from './watchlist.controller';

const router = Router();

router.get('/', requirePermissions(['visitors:read']), watchlistController.list);
router.post('/', requirePermissions(['visitors:configure']), watchlistController.create);
router.post('/check', requirePermissions(['visitors:read']), watchlistController.check);
router.put('/:id', requirePermissions(['visitors:configure']), watchlistController.update);
router.delete('/:id', requirePermissions(['visitors:configure']), watchlistController.remove);

export { router as watchlistRoutes };
```

---

### 3.8 Denied Entries

#### 3.8.1 `src/modules/visitors/security/denied-entry.service.ts`

```typescript
import { platformPrisma } from '../../../config/database';
import { ApiError } from '../../../shared/errors';

class DeniedEntryService {

  async list(companyId: string, filters: { denialReason?: string; fromDate?: string; toDate?: string; search?: string; page: number; limit: number }) {
    const { page, limit, denialReason, fromDate, toDate, search } = filters;
    const offset = (page - 1) * limit;
    const where: any = { companyId };
    if (denialReason) where.denialReason = denialReason;
    if (fromDate || toDate) {
      where.deniedAt = {};
      if (fromDate) where.deniedAt.gte = new Date(fromDate);
      if (toDate) where.deniedAt.lte = new Date(toDate);
    }
    if (search) {
      where.OR = [
        { visitorName: { contains: search, mode: 'insensitive' } },
        { visitorMobile: { contains: search } },
      ];
    }

    const [data, total] = await Promise.all([
      platformPrisma.deniedEntry.findMany({
        where,
        skip: offset,
        take: limit,
        orderBy: { deniedAt: 'desc' },
        include: { visit: true, watchlistEntry: true },
      }),
      platformPrisma.deniedEntry.count({ where }),
    ]);
    return { data, total };
  }

  async getById(companyId: string, id: string) {
    const entry = await platformPrisma.deniedEntry.findFirst({
      where: { id, companyId },
      include: { visit: true, watchlistEntry: true },
    });
    if (!entry) throw ApiError.notFound('Denied entry not found');
    return entry;
  }
}

export const deniedEntryService = new DeniedEntryService();
```

#### 3.8.2 `src/modules/visitors/security/denied-entry.routes.ts`

```typescript
import { Router } from 'express';
import { requirePermissions } from '../../../middleware/auth.middleware';
import { deniedEntryController } from './denied-entry.controller';

const router = Router();

router.get('/', requirePermissions(['visitors:read']), deniedEntryController.list);
router.get('/:id', requirePermissions(['visitors:read']), deniedEntryController.getById);

export { router as deniedEntryRoutes };
```

---

### 3.9 Recurring Passes

#### 3.9.1 `src/modules/visitors/passes/recurring-pass.validators.ts`

```typescript
import { z } from 'zod';

const trimString = (val: unknown) => (typeof val === 'string' ? val.trim() : val);

export const createRecurringPassSchema = z.object({
  visitorName: z.preprocess(trimString, z.string().min(1).max(200)),
  visitorCompany: z.preprocess(trimString, z.string().min(1).max(200)),
  visitorMobile: z.preprocess(trimString, z.string().min(10).max(15)),
  visitorEmail: z.preprocess(trimString, z.string().email().max(200)).optional(),
  visitorPhoto: z.string().url().optional(),
  visitorIdType: z.string().optional(),
  visitorIdNumber: z.preprocess(trimString, z.string().max(50)).optional(),
  passType: z.enum(['WEEKLY', 'MONTHLY', 'QUARTERLY', 'ANNUAL']),
  validFrom: z.string().min(1, 'Valid from date is required'),
  validUntil: z.string().min(1, 'Valid until date is required'),
  allowedDays: z.array(z.number().int().min(0).max(6)).default([]),
  allowedTimeFrom: z.string().regex(/^\d{2}:\d{2}$/).optional(),
  allowedTimeTo: z.string().regex(/^\d{2}:\d{2}$/).optional(),
  allowedGateIds: z.array(z.string()).default([]),
  hostEmployeeId: z.string().min(1, 'Host employee is required'),
  purpose: z.preprocess(trimString, z.string().min(1).max(500)),
  plantId: z.string().min(1, 'Plant is required'),
});

export const updateRecurringPassSchema = createRecurringPassSchema.partial();

export const revokePassSchema = z.object({
  reason: z.preprocess(trimString, z.string().min(1, 'Revoke reason is required').max(500)),
});

export const recurringPassListQuerySchema = z.object({
  status: z.enum(['ACTIVE', 'EXPIRED', 'REVOKED']).optional(),
  search: z.string().optional(),
  page: z.coerce.number().int().min(1).default(1),
  limit: z.coerce.number().int().min(1).max(100).default(20),
});
```

#### 3.9.2 `src/modules/visitors/passes/recurring-pass.service.ts`

```typescript
import { platformPrisma } from '../../../config/database';
import { ApiError } from '../../../shared/errors';
import { generateNextNumber } from '../../../shared/utils/number-series';
import { n } from '../../../shared/utils/prisma-helpers';

class RecurringPassService {

  async list(companyId: string, filters: { status?: string; search?: string; page: number; limit: number }) {
    const { page, limit, status, search } = filters;
    const offset = (page - 1) * limit;
    const where: any = { companyId };
    if (status) where.status = status;
    if (search) {
      where.OR = [
        { visitorName: { contains: search, mode: 'insensitive' } },
        { visitorCompany: { contains: search, mode: 'insensitive' } },
        { visitorMobile: { contains: search } },
        { passNumber: { contains: search, mode: 'insensitive' } },
      ];
    }

    const [data, total] = await Promise.all([
      platformPrisma.recurringVisitorPass.findMany({ where, skip: offset, take: limit, orderBy: { createdAt: 'desc' } }),
      platformPrisma.recurringVisitorPass.count({ where }),
    ]);
    return { data, total };
  }

  async getById(companyId: string, id: string) {
    const pass = await platformPrisma.recurringVisitorPass.findFirst({ where: { id, companyId } });
    if (!pass) throw ApiError.notFound('Recurring pass not found');
    return pass;
  }

  async create(companyId: string, input: any, createdBy: string) {
    return platformPrisma.$transaction(async (tx) => {
      const passNumber = await generateNextNumber(
        tx, companyId, ['Recurring Visitor Pass', 'Recurring Pass'], 'Recurring Visitor Pass',
      );

      return tx.recurringVisitorPass.create({
        data: {
          companyId,
          passNumber,
          visitorName: input.visitorName,
          visitorCompany: input.visitorCompany,
          visitorMobile: input.visitorMobile,
          visitorEmail: n(input.visitorEmail),
          visitorPhoto: n(input.visitorPhoto),
          visitorIdType: n(input.visitorIdType),
          visitorIdNumber: n(input.visitorIdNumber),
          passType: input.passType,
          validFrom: new Date(input.validFrom),
          validUntil: new Date(input.validUntil),
          allowedDays: input.allowedDays ?? [],
          allowedTimeFrom: n(input.allowedTimeFrom),
          allowedTimeTo: n(input.allowedTimeTo),
          allowedGateIds: input.allowedGateIds ?? [],
          hostEmployeeId: input.hostEmployeeId,
          purpose: input.purpose,
          plantId: input.plantId,
          createdBy,
        },
      });
    });
  }

  async update(companyId: string, id: string, input: any) {
    const existing = await platformPrisma.recurringVisitorPass.findFirst({ where: { id, companyId } });
    if (!existing) throw ApiError.notFound('Recurring pass not found');
    if (existing.status !== 'ACTIVE') throw ApiError.badRequest('Can only update active passes');

    return platformPrisma.recurringVisitorPass.update({
      where: { id },
      data: {
        ...(input.visitorName && { visitorName: input.visitorName }),
        ...(input.visitorCompany && { visitorCompany: input.visitorCompany }),
        ...(input.visitorMobile && { visitorMobile: input.visitorMobile }),
        ...(input.visitorEmail !== undefined && { visitorEmail: n(input.visitorEmail) }),
        ...(input.visitorPhoto !== undefined && { visitorPhoto: n(input.visitorPhoto) }),
        ...(input.passType && { passType: input.passType }),
        ...(input.validFrom && { validFrom: new Date(input.validFrom) }),
        ...(input.validUntil && { validUntil: new Date(input.validUntil) }),
        ...(input.allowedDays && { allowedDays: input.allowedDays }),
        ...(input.allowedTimeFrom !== undefined && { allowedTimeFrom: n(input.allowedTimeFrom) }),
        ...(input.allowedTimeTo !== undefined && { allowedTimeTo: n(input.allowedTimeTo) }),
        ...(input.allowedGateIds && { allowedGateIds: input.allowedGateIds }),
        ...(input.hostEmployeeId && { hostEmployeeId: input.hostEmployeeId }),
        ...(input.purpose && { purpose: input.purpose }),
        ...(input.plantId && { plantId: input.plantId }),
      },
    });
  }

  async revoke(companyId: string, id: string, reason: string, revokedBy: string) {
    const existing = await platformPrisma.recurringVisitorPass.findFirst({ where: { id, companyId } });
    if (!existing) throw ApiError.notFound('Recurring pass not found');
    if (existing.status !== 'ACTIVE') throw ApiError.badRequest('Pass is already revoked or expired');

    return platformPrisma.recurringVisitorPass.update({
      where: { id },
      data: { status: 'REVOKED', revokedAt: new Date(), revokedBy, revokeReason: reason },
    });
  }

  /**
   * Check in via recurring pass. Creates a full Visit record linked to the pass.
   */
  async checkInViaPass(companyId: string, passId: string, gateId: string, guardId: string) {
    const pass = await platformPrisma.recurringVisitorPass.findFirst({ where: { id: passId, companyId } });
    if (!pass) throw ApiError.notFound('Recurring pass not found');
    if (pass.status !== 'ACTIVE') throw ApiError.badRequest('Pass is not active');

    const now = new Date();
    if (now < pass.validFrom || now > pass.validUntil) {
      throw ApiError.badRequest('Pass is outside its validity period');
    }

    // Check allowed day
    if (pass.allowedDays.length > 0) {
      const today = now.getDay(); // 0=Sun
      if (!pass.allowedDays.includes(today)) {
        throw ApiError.badRequest('Pass is not valid for today');
      }
    }

    // Check allowed gate
    if (pass.allowedGateIds.length > 0 && !pass.allowedGateIds.includes(gateId)) {
      throw ApiError.badRequest('Pass is not valid for this gate');
    }

    // Import visit service to create visit
    const { visitService } = await import('../core/visit.service');
    // Create a visit record linked to this pass
    return platformPrisma.$transaction(async (tx) => {
      const visitCode = await (visitService as any).generateVisitCode();
      const visitNumber = await generateNextNumber(
        tx, companyId, ['Visitor', 'Visitor Registration'], 'Visitor Registration',
      );
      const badgeNumber = await generateNextNumber(
        tx, companyId, ['Visitor Badge', 'Badge'], 'Visitor Badge',
      );

      return tx.visit.create({
        data: {
          companyId,
          visitNumber,
          visitCode,
          visitorName: pass.visitorName,
          visitorMobile: pass.visitorMobile,
          visitorEmail: pass.visitorEmail,
          visitorCompany: pass.visitorCompany,
          visitorPhoto: pass.visitorPhoto,
          visitorIdType: pass.visitorIdType,
          governmentIdNumber: pass.visitorIdNumber,
          visitorTypeId: '', // Will be resolved from config or default
          purpose: 'OTHER' as any,
          purposeNotes: pass.purpose,
          expectedDate: now,
          hostEmployeeId: pass.hostEmployeeId,
          plantId: pass.plantId,
          gateId,
          registrationMethod: 'PRE_REGISTERED',
          approvalStatus: 'AUTO_APPROVED',
          status: 'CHECKED_IN',
          checkInTime: now,
          checkInGateId: gateId,
          checkInGuardId: guardId,
          badgeNumber,
          recurringPassId: passId,
          createdBy: guardId,
        },
      });
    });
  }
}

export const recurringPassService = new RecurringPassService();
```

#### 3.9.3 `src/modules/visitors/passes/recurring-pass.routes.ts`

```typescript
import { Router } from 'express';
import { requirePermissions } from '../../../middleware/auth.middleware';
import { recurringPassController } from './recurring-pass.controller';

const router = Router();

router.get('/', requirePermissions(['visitors:read']), recurringPassController.list);
router.post('/', requirePermissions(['visitors:create']), recurringPassController.create);
router.get('/:id', requirePermissions(['visitors:read']), recurringPassController.getById);
router.put('/:id', requirePermissions(['visitors:update']), recurringPassController.update);
router.post('/:id/revoke', requirePermissions(['visitors:delete']), recurringPassController.revoke);
router.post('/:id/check-in', requirePermissions(['visitors:create']), recurringPassController.checkIn);

export { router as recurringPassRoutes };
```

---

### 3.10 Vehicle Gate Pass

#### 3.10.1 `src/modules/visitors/passes/vehicle-pass.validators.ts`

```typescript
import { z } from 'zod';

const trimString = (val: unknown) => (typeof val === 'string' ? val.trim() : val);

export const createVehiclePassSchema = z.object({
  vehicleRegNumber: z.preprocess(trimString, z.string().min(1, 'Vehicle registration is required').max(20)),
  vehicleType: z.enum(['CAR', 'TWO_WHEELER', 'AUTO', 'TRUCK', 'VAN', 'TEMPO', 'BUS']),
  driverName: z.preprocess(trimString, z.string().min(1, 'Driver name is required').max(200)),
  driverMobile: z.preprocess(trimString, z.string().max(15)).optional(),
  purpose: z.preprocess(trimString, z.string().min(1, 'Purpose is required').max(500)),
  visitId: z.string().optional(),
  materialDescription: z.preprocess(trimString, z.string().max(500)).optional(),
  vehiclePhoto: z.string().url().optional(),
  entryGateId: z.string().min(1, 'Entry gate is required'),
  plantId: z.string().min(1, 'Plant is required'),
});

export const vehicleExitSchema = z.object({
  exitGateId: z.string().min(1, 'Exit gate is required'),
});

export const vehiclePassListQuerySchema = z.object({
  fromDate: z.string().optional(),
  toDate: z.string().optional(),
  search: z.string().optional(),
  page: z.coerce.number().int().min(1).default(1),
  limit: z.coerce.number().int().min(1).max(100).default(20),
});
```

#### 3.10.2 `src/modules/visitors/passes/vehicle-pass.service.ts`

```typescript
import { platformPrisma } from '../../../config/database';
import { ApiError } from '../../../shared/errors';
import { generateNextNumber } from '../../../shared/utils/number-series';
import { n } from '../../../shared/utils/prisma-helpers';

class VehiclePassService {

  async list(companyId: string, filters: { fromDate?: string; toDate?: string; search?: string; page: number; limit: number }) {
    const { page, limit, fromDate, toDate, search } = filters;
    const offset = (page - 1) * limit;
    const where: any = { companyId };
    if (fromDate || toDate) {
      where.entryTime = {};
      if (fromDate) where.entryTime.gte = new Date(fromDate);
      if (toDate) where.entryTime.lte = new Date(toDate);
    }
    if (search) {
      where.OR = [
        { vehicleRegNumber: { contains: search, mode: 'insensitive' } },
        { driverName: { contains: search, mode: 'insensitive' } },
        { passNumber: { contains: search, mode: 'insensitive' } },
      ];
    }

    const [data, total] = await Promise.all([
      platformPrisma.vehicleGatePass.findMany({ where, skip: offset, take: limit, orderBy: { entryTime: 'desc' }, include: { entryGate: true, exitGate: true } }),
      platformPrisma.vehicleGatePass.count({ where }),
    ]);
    return { data, total };
  }

  async create(companyId: string, input: any, createdBy: string) {
    return platformPrisma.$transaction(async (tx) => {
      const passNumber = await generateNextNumber(
        tx, companyId, ['Vehicle Gate Pass', 'Gate Pass'], 'Vehicle Gate Pass',
      );

      return tx.vehicleGatePass.create({
        data: {
          companyId,
          passNumber,
          vehicleRegNumber: input.vehicleRegNumber,
          vehicleType: input.vehicleType,
          driverName: input.driverName,
          driverMobile: n(input.driverMobile),
          purpose: input.purpose,
          visitId: n(input.visitId),
          materialDescription: n(input.materialDescription),
          vehiclePhoto: n(input.vehiclePhoto),
          entryGateId: input.entryGateId,
          plantId: input.plantId,
          createdBy,
        },
        include: { entryGate: true },
      });
    });
  }

  async recordExit(companyId: string, id: string, exitGateId: string) {
    const pass = await platformPrisma.vehicleGatePass.findFirst({ where: { id, companyId } });
    if (!pass) throw ApiError.notFound('Vehicle gate pass not found');
    if (pass.exitTime) throw ApiError.conflict('Vehicle has already exited');

    return platformPrisma.vehicleGatePass.update({
      where: { id },
      data: { exitGateId, exitTime: new Date() },
      include: { entryGate: true, exitGate: true },
    });
  }
}

export const vehiclePassService = new VehiclePassService();
```

#### 3.10.3 `src/modules/visitors/passes/vehicle-pass.routes.ts`

```typescript
import { Router } from 'express';
import { requirePermissions } from '../../../middleware/auth.middleware';
import { vehiclePassController } from './vehicle-pass.controller';

const router = Router();

router.get('/', requirePermissions(['visitors:read']), vehiclePassController.list);
router.post('/', requirePermissions(['visitors:create']), vehiclePassController.create);
router.post('/:id/exit', requirePermissions(['visitors:create']), vehiclePassController.recordExit);

export { router as vehiclePassRoutes };
```

---

### 3.11 Material Gate Pass

#### 3.11.1 `src/modules/visitors/passes/material-pass.validators.ts`

```typescript
import { z } from 'zod';

const trimString = (val: unknown) => (typeof val === 'string' ? val.trim() : val);

export const createMaterialPassSchema = z.object({
  type: z.enum(['INWARD', 'OUTWARD', 'RETURNABLE']),
  description: z.preprocess(trimString, z.string().min(1, 'Description is required').max(500)),
  quantityIssued: z.preprocess(trimString, z.string().max(100)).optional(),
  visitId: z.string().optional(),
  authorizedBy: z.string().min(1, 'Authorized by is required'),
  purpose: z.preprocess(trimString, z.string().min(1, 'Purpose is required').max(500)),
  expectedReturnDate: z.string().optional(),
  gateId: z.string().min(1, 'Gate is required'),
  plantId: z.string().min(1, 'Plant is required'),
});

export const materialReturnSchema = z.object({
  quantityReturned: z.preprocess(trimString, z.string().min(1, 'Quantity returned is required').max(100)),
  returnStatus: z.enum(['PARTIAL', 'FULLY_RETURNED']),
});

export const materialPassListQuerySchema = z.object({
  type: z.enum(['INWARD', 'OUTWARD', 'RETURNABLE']).optional(),
  returnStatus: z.enum(['NOT_APPLICABLE', 'PENDING', 'PARTIAL', 'FULLY_RETURNED']).optional(),
  fromDate: z.string().optional(),
  toDate: z.string().optional(),
  search: z.string().optional(),
  page: z.coerce.number().int().min(1).default(1),
  limit: z.coerce.number().int().min(1).max(100).default(20),
});
```

#### 3.11.2 `src/modules/visitors/passes/material-pass.service.ts`

```typescript
import { platformPrisma } from '../../../config/database';
import { ApiError } from '../../../shared/errors';
import { generateNextNumber } from '../../../shared/utils/number-series';
import { n } from '../../../shared/utils/prisma-helpers';

class MaterialPassService {

  async list(companyId: string, filters: { type?: string; returnStatus?: string; fromDate?: string; toDate?: string; search?: string; page: number; limit: number }) {
    const { page, limit, type, returnStatus, fromDate, toDate, search } = filters;
    const offset = (page - 1) * limit;
    const where: any = { companyId };
    if (type) where.type = type;
    if (returnStatus) where.returnStatus = returnStatus;
    if (fromDate || toDate) {
      where.createdAt = {};
      if (fromDate) where.createdAt.gte = new Date(fromDate);
      if (toDate) where.createdAt.lte = new Date(toDate);
    }
    if (search) {
      where.OR = [
        { description: { contains: search, mode: 'insensitive' } },
        { passNumber: { contains: search, mode: 'insensitive' } },
      ];
    }

    const [data, total] = await Promise.all([
      platformPrisma.materialGatePass.findMany({ where, skip: offset, take: limit, orderBy: { createdAt: 'desc' }, include: { gate: true } }),
      platformPrisma.materialGatePass.count({ where }),
    ]);
    return { data, total };
  }

  async create(companyId: string, input: any, createdBy: string) {
    return platformPrisma.$transaction(async (tx) => {
      const passNumber = await generateNextNumber(
        tx, companyId, ['Material Gate Pass', 'Gate Pass'], 'Material Gate Pass',
      );

      const returnStatus = input.type === 'RETURNABLE' ? 'PENDING' : 'NOT_APPLICABLE';

      return tx.materialGatePass.create({
        data: {
          companyId,
          passNumber,
          type: input.type,
          description: input.description,
          quantityIssued: n(input.quantityIssued),
          visitId: n(input.visitId),
          authorizedBy: input.authorizedBy,
          purpose: input.purpose,
          expectedReturnDate: input.expectedReturnDate ? new Date(input.expectedReturnDate) : undefined,
          returnStatus: returnStatus as any,
          gateId: input.gateId,
          plantId: input.plantId,
          createdBy,
        },
        include: { gate: true },
      });
    });
  }

  async markReturned(companyId: string, id: string, input: { quantityReturned: string; returnStatus: string }) {
    const pass = await platformPrisma.materialGatePass.findFirst({ where: { id, companyId } });
    if (!pass) throw ApiError.notFound('Material gate pass not found');
    if (pass.returnStatus === 'FULLY_RETURNED') throw ApiError.conflict('Material has already been fully returned');
    if (pass.returnStatus === 'NOT_APPLICABLE') throw ApiError.badRequest('This pass does not require a return');

    return platformPrisma.materialGatePass.update({
      where: { id },
      data: {
        quantityReturned: input.quantityReturned,
        returnStatus: input.returnStatus as any,
        returnedAt: input.returnStatus === 'FULLY_RETURNED' ? new Date() : undefined,
      },
      include: { gate: true },
    });
  }
}

export const materialPassService = new MaterialPassService();
```

#### 3.11.3 `src/modules/visitors/passes/material-pass.routes.ts`

```typescript
import { Router } from 'express';
import { requirePermissions } from '../../../middleware/auth.middleware';
import { materialPassController } from './material-pass.controller';

const router = Router();

router.get('/', requirePermissions(['visitors:read']), materialPassController.list);
router.post('/', requirePermissions(['visitors:create']), materialPassController.create);
router.post('/:id/return', requirePermissions(['visitors:update']), materialPassController.markReturned);

export { router as materialPassRoutes };
```

---

### 3.12 Group Visits

#### 3.12.1 `src/modules/visitors/group/group-visit.validators.ts`

```typescript
import { z } from 'zod';

const trimString = (val: unknown) => (typeof val === 'string' ? val.trim() : val);

export const createGroupVisitSchema = z.object({
  groupName: z.preprocess(trimString, z.string().min(1, 'Group name is required').max(200)),
  hostEmployeeId: z.string().min(1, 'Host employee is required'),
  purpose: z.preprocess(trimString, z.string().min(1, 'Purpose is required').max(500)),
  expectedDate: z.string().min(1, 'Expected date is required'),
  expectedTime: z.string().regex(/^\d{2}:\d{2}$/).optional(),
  plantId: z.string().min(1, 'Plant is required'),
  gateId: z.string().optional(),
  members: z.array(z.object({
    visitorName: z.preprocess(trimString, z.string().min(1).max(200)),
    visitorMobile: z.preprocess(trimString, z.string().min(10).max(15)),
    visitorEmail: z.preprocess(trimString, z.string().email().max(200)).optional(),
    visitorCompany: z.preprocess(trimString, z.string().max(200)).optional(),
  })).min(2, 'Group visit requires at least 2 members').max(100),
});

export const updateGroupVisitSchema = z.object({
  groupName: z.preprocess(trimString, z.string().min(1).max(200)).optional(),
  purpose: z.preprocess(trimString, z.string().min(1).max(500)).optional(),
  expectedDate: z.string().optional(),
  expectedTime: z.string().regex(/^\d{2}:\d{2}$/).optional(),
});

export const batchCheckInSchema = z.object({
  memberIds: z.array(z.string()).min(1, 'At least one member is required'),
  checkInGateId: z.string().min(1, 'Gate is required'),
});

export const batchCheckOutSchema = z.object({
  memberIds: z.array(z.string()).optional(), // If omitted, check out all
  checkOutGateId: z.string().optional(),
  checkOutMethod: z.enum(['SECURITY_DESK', 'HOST_INITIATED']).default('SECURITY_DESK'),
});

export const groupVisitListQuerySchema = z.object({
  status: z.enum(['PLANNED', 'IN_PROGRESS', 'COMPLETED', 'CANCELLED']).optional(),
  fromDate: z.string().optional(),
  toDate: z.string().optional(),
  search: z.string().optional(),
  page: z.coerce.number().int().min(1).default(1),
  limit: z.coerce.number().int().min(1).max(100).default(20),
});
```

#### 3.12.2 `src/modules/visitors/group/group-visit.service.ts`

```typescript
import { platformPrisma } from '../../../config/database';
import { ApiError } from '../../../shared/errors';
import { generateNextNumber } from '../../../shared/utils/number-series';
import { n } from '../../../shared/utils/prisma-helpers';
import crypto from 'crypto';

class GroupVisitService {

  private async generateGroupVisitCode(): Promise<string> {
    const chars = 'ABCDEFGHJKLMNPQRSTUVWXYZ23456789';
    for (let attempt = 0; attempt < 3; attempt++) {
      let code = 'G-';
      const bytes = crypto.randomBytes(6);
      for (let i = 0; i < 6; i++) {
        code += chars[bytes[i] % chars.length];
      }
      const existing = await platformPrisma.groupVisit.findUnique({ where: { visitCode: code } });
      if (!existing) return code;
    }
    throw ApiError.conflict('Unable to generate unique group visit code');
  }

  async list(companyId: string, filters: { status?: string; fromDate?: string; toDate?: string; search?: string; page: number; limit: number }) {
    const { page, limit, status, fromDate, toDate, search } = filters;
    const offset = (page - 1) * limit;
    const where: any = { companyId };
    if (status) where.status = status;
    if (fromDate || toDate) {
      where.expectedDate = {};
      if (fromDate) where.expectedDate.gte = new Date(fromDate);
      if (toDate) where.expectedDate.lte = new Date(toDate);
    }
    if (search) {
      where.OR = [
        { groupName: { contains: search, mode: 'insensitive' } },
        { visitCode: { contains: search, mode: 'insensitive' } },
      ];
    }

    const [data, total] = await Promise.all([
      platformPrisma.groupVisit.findMany({
        where,
        skip: offset,
        take: limit,
        orderBy: { expectedDate: 'desc' },
        include: { members: true },
      }),
      platformPrisma.groupVisit.count({ where }),
    ]);
    return { data, total };
  }

  async getById(companyId: string, id: string) {
    const group = await platformPrisma.groupVisit.findFirst({
      where: { id, companyId },
      include: { members: { include: { visit: true } } },
    });
    if (!group) throw ApiError.notFound('Group visit not found');
    return group;
  }

  async create(companyId: string, input: any, createdBy: string) {
    const visitCode = await this.generateGroupVisitCode();

    return platformPrisma.$transaction(async (tx) => {
      const group = await tx.groupVisit.create({
        data: {
          companyId,
          groupName: input.groupName,
          visitCode,
          hostEmployeeId: input.hostEmployeeId,
          purpose: input.purpose,
          expectedDate: new Date(input.expectedDate),
          expectedTime: n(input.expectedTime),
          plantId: input.plantId,
          gateId: n(input.gateId),
          totalMembers: input.members.length,
          createdBy,
        },
      });

      // Create group members
      for (const member of input.members) {
        await tx.groupVisitMember.create({
          data: {
            groupVisitId: group.id,
            visitorName: member.visitorName,
            visitorMobile: member.visitorMobile,
            visitorEmail: n(member.visitorEmail),
            visitorCompany: n(member.visitorCompany),
          },
        });
      }

      return tx.groupVisit.findUnique({
        where: { id: group.id },
        include: { members: true },
      });
    });
  }

  async batchCheckIn(companyId: string, groupId: string, memberIds: string[], gateId: string, guardId: string) {
    const group = await platformPrisma.groupVisit.findFirst({
      where: { id: groupId, companyId },
      include: { members: true },
    });
    if (!group) throw ApiError.notFound('Group visit not found');

    const results: any[] = [];
    await platformPrisma.$transaction(async (tx) => {
      for (const memberId of memberIds) {
        const member = group.members.find(m => m.id === memberId);
        if (!member) continue;
        if (member.status !== 'EXPECTED') continue;

        // Create individual visit record for this member
        const visitCode = crypto.randomBytes(4).toString('hex').toUpperCase().slice(0, 6);
        const visitNumber = await generateNextNumber(
          tx, companyId, ['Visitor', 'Visitor Registration'], 'Visitor Registration',
        );
        const badgeNumber = await generateNextNumber(
          tx, companyId, ['Visitor Badge', 'Badge'], 'Visitor Badge',
        );

        const visit = await tx.visit.create({
          data: {
            companyId,
            visitNumber,
            visitCode,
            visitorName: member.visitorName,
            visitorMobile: member.visitorMobile,
            visitorEmail: member.visitorEmail,
            visitorCompany: member.visitorCompany,
            visitorTypeId: '', // Resolved from default
            purpose: 'OTHER' as any,
            purposeNotes: group.purpose,
            expectedDate: group.expectedDate,
            hostEmployeeId: group.hostEmployeeId,
            plantId: group.plantId,
            gateId,
            registrationMethod: 'PRE_REGISTERED',
            approvalStatus: 'AUTO_APPROVED',
            status: 'CHECKED_IN',
            checkInTime: new Date(),
            checkInGateId: gateId,
            checkInGuardId: guardId,
            badgeNumber,
            groupVisitId: groupId,
            createdBy: guardId,
          },
        });

        await tx.groupVisitMember.update({
          where: { id: memberId },
          data: { visitId: visit.id, status: 'CHECKED_IN' },
        });

        results.push(visit);
      }

      // Update group status
      await tx.groupVisit.update({
        where: { id: groupId },
        data: { status: 'IN_PROGRESS' },
      });
    });

    return results;
  }

  async batchCheckOut(companyId: string, groupId: string, memberIds: string[] | undefined, gateId: string | undefined, method: string, userId: string) {
    const group = await platformPrisma.groupVisit.findFirst({
      where: { id: groupId, companyId },
      include: { members: { include: { visit: true } } },
    });
    if (!group) throw ApiError.notFound('Group visit not found');

    const membersToCheckOut = memberIds
      ? group.members.filter(m => memberIds.includes(m.id) && m.status === 'CHECKED_IN')
      : group.members.filter(m => m.status === 'CHECKED_IN');

    const { visitService } = await import('../core/visit.service');

    for (const member of membersToCheckOut) {
      if (member.visitId) {
        await visitService.checkOut(companyId, member.visitId, {
          checkOutGateId: gateId,
          checkOutMethod: method,
        }, userId);

        await platformPrisma.groupVisitMember.update({
          where: { id: member.id },
          data: { status: 'CHECKED_OUT' },
        });
      }
    }

    // Check if all members are done
    const updatedGroup = await platformPrisma.groupVisit.findUnique({
      where: { id: groupId },
      include: { members: true },
    });
    const allDone = updatedGroup?.members.every(m => ['CHECKED_OUT', 'NO_SHOW'].includes(m.status));
    if (allDone) {
      await platformPrisma.groupVisit.update({
        where: { id: groupId },
        data: { status: 'COMPLETED' },
      });
    }

    return updatedGroup;
  }
}

export const groupVisitService = new GroupVisitService();
```

#### 3.12.3 `src/modules/visitors/group/group-visit.routes.ts`

```typescript
import { Router } from 'express';
import { requirePermissions } from '../../../middleware/auth.middleware';
import { groupVisitController } from './group-visit.controller';

const router = Router();

router.get('/', requirePermissions(['visitors:read']), groupVisitController.list);
router.post('/', requirePermissions(['visitors:create']), groupVisitController.create);
router.get('/:id', requirePermissions(['visitors:read']), groupVisitController.getById);
router.put('/:id', requirePermissions(['visitors:update']), groupVisitController.update);
router.post('/:id/batch-check-in', requirePermissions(['visitors:create']), groupVisitController.batchCheckIn);
router.post('/:id/batch-check-out', requirePermissions(['visitors:create']), groupVisitController.batchCheckOut);

export { router as groupVisitRoutes };
```

---

### 3.13 Dashboard

#### 3.13.1 `src/modules/visitors/dashboard/dashboard.service.ts`

```typescript
import { platformPrisma } from '../../../config/database';
import { DateTime } from 'luxon';

class DashboardService {

  async getTodayStats(companyId: string, plantId?: string, timezone?: string) {
    const tz = timezone ?? 'Asia/Kolkata';
    const todayStart = DateTime.now().setZone(tz).startOf('day').toJSDate();
    const todayEnd = DateTime.now().setZone(tz).endOf('day').toJSDate();

    const where: any = {
      companyId,
      expectedDate: { gte: todayStart, lte: todayEnd },
    };
    if (plantId) where.plantId = plantId;

    const [totalExpected, checkedIn, checkedOut, onSite, walkIns, noShows, overstaying] = await Promise.all([
      platformPrisma.visit.count({ where: { ...where } }),
      platformPrisma.visit.count({ where: { ...where, status: { in: ['CHECKED_IN', 'CHECKED_OUT', 'AUTO_CHECKED_OUT'] } } }),
      platformPrisma.visit.count({ where: { ...where, status: { in: ['CHECKED_OUT', 'AUTO_CHECKED_OUT'] } } }),
      platformPrisma.visit.count({ where: { companyId, status: 'CHECKED_IN', ...(plantId ? { plantId } : {}) } }),
      platformPrisma.visit.count({ where: { ...where, registrationMethod: 'WALK_IN' } }),
      platformPrisma.visit.count({ where: { ...where, status: 'NO_SHOW' } }),
      this.countOverstaying(companyId, plantId),
    ]);

    return {
      totalExpected,
      checkedIn,
      checkedOut,
      onSite,
      walkIns,
      noShows,
      overstaying,
    };
  }

  async getTodayVisitors(companyId: string, filters: { plantId?: string; gateId?: string; status?: string; search?: string; page: number; limit: number }, timezone?: string) {
    const tz = timezone ?? 'Asia/Kolkata';
    const todayStart = DateTime.now().setZone(tz).startOf('day').toJSDate();
    const todayEnd = DateTime.now().setZone(tz).endOf('day').toJSDate();

    const { page, limit, plantId, gateId, status, search } = filters;
    const offset = (page - 1) * limit;

    const where: any = {
      companyId,
      expectedDate: { gte: todayStart, lte: todayEnd },
    };
    if (plantId) where.plantId = plantId;
    if (gateId) where.gateId = gateId;
    if (status) where.status = status;
    if (search) {
      where.OR = [
        { visitorName: { contains: search, mode: 'insensitive' } },
        { visitorCompany: { contains: search, mode: 'insensitive' } },
        { visitCode: { contains: search, mode: 'insensitive' } },
      ];
    }

    const [data, total] = await Promise.all([
      platformPrisma.visit.findMany({
        where,
        skip: offset,
        take: limit,
        orderBy: { expectedDate: 'asc' },
        include: { visitorType: true, checkInGate: true },
      }),
      platformPrisma.visit.count({ where }),
    ]);

    return { data, total };
  }

  async getOnSiteVisitors(companyId: string, plantId?: string) {
    const where: any = { companyId, status: 'CHECKED_IN' };
    if (plantId) where.plantId = plantId;

    return platformPrisma.visit.findMany({
      where,
      orderBy: { checkInTime: 'asc' },
      include: { visitorType: true, checkInGate: true },
    });
  }

  private async countOverstaying(companyId: string, plantId?: string): Promise<number> {
    const where: any = { companyId, status: 'CHECKED_IN', checkInTime: { not: null } };
    if (plantId) where.plantId = plantId;

    const visitors = await platformPrisma.visit.findMany({ where, select: { checkInTime: true, expectedDurationMinutes: true } });
    const now = new Date();
    return visitors.filter(v => {
      if (!v.checkInTime || !v.expectedDurationMinutes) return false;
      const end = new Date(v.checkInTime.getTime() + v.expectedDurationMinutes * 60000);
      return now > end;
    }).length;
  }
}

export const dashboardService = new DashboardService();
```

#### 3.13.2 `src/modules/visitors/dashboard/dashboard.routes.ts`

```typescript
import { Router } from 'express';
import { requirePermissions } from '../../../middleware/auth.middleware';
import { dashboardController } from './dashboard.controller';

const router = Router();

router.get('/today', requirePermissions(['visitors:read']), dashboardController.getTodayDashboard);
router.get('/on-site', requirePermissions(['visitors:read']), dashboardController.getOnSite);
router.get('/stats', requirePermissions(['visitors:read']), dashboardController.getStats);

export { router as dashboardRoutes };
```

---

### 3.14 Reports

#### 3.14.1 `src/modules/visitors/reports/reports.service.ts`

```typescript
import { platformPrisma } from '../../../config/database';

class ReportsService {

  async getDailyLog(companyId: string, date: string, plantId?: string) {
    const dayStart = new Date(date);
    const dayEnd = new Date(date);
    dayEnd.setDate(dayEnd.getDate() + 1);

    const where: any = {
      companyId,
      expectedDate: { gte: dayStart, lt: dayEnd },
    };
    if (plantId) where.plantId = plantId;

    return platformPrisma.visit.findMany({
      where,
      orderBy: { checkInTime: 'asc' },
      include: { visitorType: true, checkInGate: true, checkOutGate: true },
    });
  }

  async getSummary(companyId: string, fromDate: string, toDate: string, plantId?: string) {
    const where: any = {
      companyId,
      expectedDate: { gte: new Date(fromDate), lte: new Date(toDate) },
    };
    if (plantId) where.plantId = plantId;

    const [totalVisits, byType, byMethod, byStatus, avgDuration] = await Promise.all([
      platformPrisma.visit.count({ where }),
      platformPrisma.visit.groupBy({ by: ['visitorTypeId'], where, _count: true }),
      platformPrisma.visit.groupBy({ by: ['registrationMethod'], where, _count: true }),
      platformPrisma.visit.groupBy({ by: ['status'], where, _count: true }),
      platformPrisma.visit.aggregate({ where: { ...where, visitDurationMinutes: { not: null } }, _avg: { visitDurationMinutes: true } }),
    ]);

    return { totalVisits, byType, byMethod, byStatus, avgDurationMinutes: avgDuration._avg.visitDurationMinutes };
  }

  async getOverstayReport(companyId: string, fromDate: string, toDate: string) {
    const visits = await platformPrisma.visit.findMany({
      where: {
        companyId,
        expectedDate: { gte: new Date(fromDate), lte: new Date(toDate) },
        status: { in: ['CHECKED_OUT', 'AUTO_CHECKED_OUT'] },
        visitDurationMinutes: { not: null },
        expectedDurationMinutes: { not: null },
      },
      include: { visitorType: true },
    });

    return visits.filter(v =>
      v.visitDurationMinutes! > v.expectedDurationMinutes!
    );
  }

  async getAnalytics(companyId: string, fromDate: string, toDate: string) {
    const where: any = {
      companyId,
      expectedDate: { gte: new Date(fromDate), lte: new Date(toDate) },
    };

    const [totalVisits, avgDuration, preRegPct, overstayRate, inductionRate] = await Promise.all([
      platformPrisma.visit.count({ where }),
      platformPrisma.visit.aggregate({ where: { ...where, visitDurationMinutes: { not: null } }, _avg: { visitDurationMinutes: true } }),
      platformPrisma.visit.count({ where: { ...where, registrationMethod: 'PRE_REGISTERED' } }),
      this.calculateOverstayRate(companyId, where),
      this.calculateInductionRate(companyId, where),
    ]);

    return {
      totalVisits,
      avgDurationMinutes: avgDuration._avg.visitDurationMinutes,
      preRegisteredPercent: totalVisits > 0 ? Math.round((preRegPct / totalVisits) * 100) : 0,
      overstayRatePercent: overstayRate,
      safetyInductionCompletionPercent: inductionRate,
    };
  }

  private async calculateOverstayRate(companyId: string, where: any): Promise<number> {
    const completed = await platformPrisma.visit.findMany({
      where: { ...where, status: { in: ['CHECKED_OUT', 'AUTO_CHECKED_OUT'] }, visitDurationMinutes: { not: null }, expectedDurationMinutes: { not: null } },
      select: { visitDurationMinutes: true, expectedDurationMinutes: true },
    });
    if (completed.length === 0) return 0;
    const overstayed = completed.filter(v => v.visitDurationMinutes! > v.expectedDurationMinutes!);
    return Math.round((overstayed.length / completed.length) * 100);
  }

  private async calculateInductionRate(companyId: string, where: any): Promise<number> {
    const required = await platformPrisma.visit.count({ where: { ...where, safetyInductionStatus: { not: 'NOT_REQUIRED' } } });
    if (required === 0) return 100;
    const completed = await platformPrisma.visit.count({ where: { ...where, safetyInductionStatus: 'COMPLETED' } });
    return Math.round((completed / required) * 100);
  }
}

export const reportsService = new ReportsService();
```

#### 3.14.2 `src/modules/visitors/reports/reports.routes.ts`

```typescript
import { Router } from 'express';
import { requirePermissions } from '../../../middleware/auth.middleware';
import { reportsController } from './reports.controller';

const router = Router();

router.get('/daily-log', requirePermissions(['visitors:export']), reportsController.getDailyLog);
router.get('/summary', requirePermissions(['visitors:export']), reportsController.getSummary);
router.get('/overstay', requirePermissions(['visitors:export']), reportsController.getOverstay);
router.get('/analytics', requirePermissions(['visitors:read']), reportsController.getAnalytics);

export { router as reportsRoutes };
```

---

### 3.15 Emergency Muster

#### 3.15.1 `src/modules/visitors/emergency/emergency.service.ts`

```typescript
import { platformPrisma } from '../../../config/database';
import { ApiError } from '../../../shared/errors';
import { logger } from '../../../config/logger';

class EmergencyService {

  async triggerEmergency(companyId: string, plantId: string, triggeredBy: string, isDrill: boolean = false) {
    // Get all on-site visitors
    const onSiteVisitors = await platformPrisma.visit.findMany({
      where: { companyId, plantId, status: 'CHECKED_IN' },
      include: { visitorType: true, checkInGate: true },
    });

    // Send SMS to all on-site visitors (if not a drill)
    if (!isDrill) {
      try {
        const { notificationService } = await import('../../../core/notifications/notification.service');
        for (const visitor of onSiteVisitors) {
          await notificationService.dispatch({
            companyId,
            triggerEvent: 'VMS_EMERGENCY_EVACUATION',
            entityType: 'visit',
            entityId: visitor.id,
            tokens: {
              visitorName: visitor.visitorName,
              companyName: '', // Resolved from company settings
            },
            type: 'critical',
          });
        }
      } catch (err) {
        logger.warn('Failed to dispatch some emergency notifications', { error: err });
      }
    }

    return {
      emergency: true,
      isDrill,
      triggeredBy,
      plantId,
      totalOnSite: onSiteVisitors.length,
      musterList: onSiteVisitors.map(v => ({
        id: v.id,
        visitorName: v.visitorName,
        visitorCompany: v.visitorCompany,
        visitorPhoto: v.visitorPhoto,
        visitorType: v.visitorType?.name,
        badgeNumber: v.badgeNumber,
        hostEmployeeId: v.hostEmployeeId,
        checkInTime: v.checkInTime,
        checkInGate: v.checkInGate?.name,
        marshalStatus: 'UNKNOWN', // Default, to be updated by marshals
      })),
    };
  }

  async getMusterList(companyId: string, plantId: string) {
    const visitors = await platformPrisma.visit.findMany({
      where: { companyId, plantId, status: 'CHECKED_IN' },
      include: { visitorType: true, checkInGate: true },
    });

    return visitors.map(v => ({
      id: v.id,
      visitorName: v.visitorName,
      visitorCompany: v.visitorCompany,
      visitorPhoto: v.visitorPhoto,
      visitorType: v.visitorType?.name,
      badgeColour: v.visitorType?.badgeColour,
      badgeNumber: v.badgeNumber,
      hostEmployeeId: v.hostEmployeeId,
      checkInTime: v.checkInTime,
      checkInGate: v.checkInGate?.name,
      visitorMobile: v.visitorMobile,
    }));
  }

  async resolveEmergency(companyId: string, plantId: string) {
    // Log the resolution
    logger.info('Emergency resolved', { companyId, plantId, resolvedAt: new Date().toISOString() });
    return { resolved: true, resolvedAt: new Date().toISOString() };
  }
}

export const emergencyService = new EmergencyService();
```

#### 3.15.2 `src/modules/visitors/emergency/emergency.routes.ts`

```typescript
import { Router } from 'express';
import { requirePermissions } from '../../../middleware/auth.middleware';
import { emergencyController } from './emergency.controller';

const router = Router();

router.post('/trigger', requirePermissions(['visitors:configure']), emergencyController.trigger);
router.get('/muster-list', requirePermissions(['visitors:read']), emergencyController.getMusterList);
router.post('/resolve', requirePermissions(['visitors:configure']), emergencyController.resolve);

export { router as emergencyRoutes };
```

---

### 3.16 Public Routes

#### 3.16.1 `src/modules/visitors/public/public.routes.ts`

These routes are mounted separately in `src/app/routes.ts`, before the auth middleware, because they are unauthenticated.

```typescript
import { Router } from 'express';
import { asyncHandler } from '../../../middleware/error.middleware';
import { publicVisitorService } from './public.service';

const router = Router();

// GET /public/visit/:visitCode — Get visit details for pre-arrival form
router.get('/visit/:visitCode', asyncHandler(async (req, res) => {
  const result = await publicVisitorService.getVisitForPreArrival(req.params.visitCode);
  res.json({ success: true, data: result });
}));

// POST /public/visit/:visitCode/pre-arrival — Submit pre-arrival form
router.post('/visit/:visitCode/pre-arrival', asyncHandler(async (req, res) => {
  const result = await publicVisitorService.submitPreArrivalForm(req.params.visitCode, req.body);
  res.json({ success: true, data: result, message: 'Pre-arrival form submitted' });
}));

// GET /public/visit/register/:plantCode — Get self-registration form config
router.get('/visit/register/:plantCode', asyncHandler(async (req, res) => {
  const result = await publicVisitorService.getSelfRegistrationConfig(req.params.plantCode);
  res.json({ success: true, data: result });
}));

// POST /public/visit/register/:plantCode — Submit self-registration
router.post('/visit/register/:plantCode', asyncHandler(async (req, res) => {
  const result = await publicVisitorService.submitSelfRegistration(req.params.plantCode, req.body);
  res.json({ success: true, data: result, message: 'Registration submitted. Awaiting host approval.' });
}));

// GET /public/visit/:visitCode/status — Check visit approval status
router.get('/visit/:visitCode/status', asyncHandler(async (req, res) => {
  const result = await publicVisitorService.getVisitStatus(req.params.visitCode);
  res.json({ success: true, data: result });
}));

// GET /public/visit/:visitCode/badge — View digital badge
router.get('/visit/:visitCode/badge', asyncHandler(async (req, res) => {
  const result = await publicVisitorService.getDigitalBadge(req.params.visitCode);
  res.json({ success: true, data: result });
}));

// POST /public/visit/:visitCode/check-out — Self check-out
router.post('/visit/:visitCode/check-out', asyncHandler(async (req, res) => {
  const result = await publicVisitorService.selfCheckOut(req.params.visitCode);
  res.json({ success: true, data: result, message: 'You have been checked out. Thank you for visiting.' });
}));

export { router as publicVisitorRoutes };
```

#### 3.16.2 `src/modules/visitors/public/public.service.ts`

```typescript
import { platformPrisma } from '../../../config/database';
import { ApiError } from '../../../shared/errors';
import { n } from '../../../shared/utils/prisma-helpers';

class PublicVisitorService {

  async getVisitForPreArrival(visitCode: string) {
    const visit = await platformPrisma.visit.findUnique({
      where: { visitCode },
      select: {
        visitorName: true,
        visitorEmail: true,
        visitorCompany: true,
        expectedDate: true,
        expectedTime: true,
        purpose: true,
        status: true,
        visitorType: { select: { name: true, requirePhoto: true, requireIdVerification: true, requireSafetyInduction: true, requireNda: true } },
      },
    });
    if (!visit) throw ApiError.notFound('Visit not found');
    if (visit.status === 'CANCELLED') throw ApiError.badRequest('This visit has been cancelled');
    return visit;
  }

  async submitPreArrivalForm(visitCode: string, data: any) {
    const visit = await platformPrisma.visit.findUnique({ where: { visitCode } });
    if (!visit) throw ApiError.notFound('Visit not found');
    if (!['EXPECTED'].includes(visit.status)) {
      throw ApiError.badRequest('Pre-arrival form can only be submitted for expected visits');
    }

    return platformPrisma.visit.update({
      where: { visitCode },
      data: {
        visitorPhoto: n(data.visitorPhoto),
        governmentIdType: n(data.governmentIdType),
        governmentIdNumber: n(data.governmentIdNumber),
        idDocumentPhoto: n(data.idDocumentPhoto),
        vehicleRegNumber: n(data.vehicleRegNumber),
        vehicleType: n(data.vehicleType),
        materialCarriedIn: n(data.materialCarriedIn),
        emergencyContact: n(data.emergencyContact),
        ndaSigned: data.ndaSigned ?? false,
      },
    });
  }

  async getSelfRegistrationConfig(plantCode: string) {
    // Look up the plant by code and return the self-registration configuration
    // This is a simplified version — production would look up Location by code
    return {
      plantCode,
      fields: ['visitorName', 'visitorMobile', 'visitorCompany', 'purpose', 'hostEmployeeName'],
      purposeOptions: ['MEETING', 'DELIVERY', 'MAINTENANCE', 'AUDIT', 'INTERVIEW', 'SITE_TOUR', 'PERSONAL', 'OTHER'],
      termsText: 'By registering, you consent to the collection and processing of your personal data for security purposes.',
    };
  }

  async submitSelfRegistration(plantCode: string, data: any) {
    // Validate required fields
    if (!data.visitorName || !data.visitorMobile || !data.purpose) {
      throw ApiError.badRequest('Name, mobile, and purpose are required');
    }

    // Rate limiting check would be done at middleware level (per phone, per IP)

    // Find the plant and create a visit with QR_SELF_REG method
    // In production, this would look up the plant by code, find the company,
    // and match the host employee by name search
    // For now, this is a placeholder that shows the structure

    throw ApiError.badRequest('Self-registration requires plant configuration. Contact the facility.');
  }

  async getVisitStatus(visitCode: string) {
    const visit = await platformPrisma.visit.findUnique({
      where: { visitCode },
      select: {
        status: true,
        approvalStatus: true,
        visitorName: true,
        expectedDate: true,
        expectedTime: true,
      },
    });
    if (!visit) throw ApiError.notFound('Visit not found');
    return visit;
  }

  async getDigitalBadge(visitCode: string) {
    const visit = await platformPrisma.visit.findUnique({
      where: { visitCode },
      select: {
        status: true,
        visitorName: true,
        visitorCompany: true,
        visitorPhoto: true,
        badgeNumber: true,
        expectedDate: true,
        checkInTime: true,
        checkOutTime: true,
        hostEmployeeId: true,
        expectedDurationMinutes: true,
        visitorType: { select: { name: true, badgeColour: true } },
      },
    });
    if (!visit) throw ApiError.notFound('Visit not found');

    // Badge content varies by status
    if (visit.status === 'EXPECTED') {
      return { status: 'NOT_STARTED', message: 'Visit not yet started. Please check in at the gate.' };
    }
    if (visit.status === 'CHECKED_IN') {
      return { status: 'ACTIVE', badge: visit };
    }
    if (['CHECKED_OUT', 'AUTO_CHECKED_OUT'].includes(visit.status)) {
      return { status: 'ENDED', message: 'Visit ended.', visitorName: visit.visitorName, visitDate: visit.expectedDate };
    }
    return { status: 'CANCELLED', message: 'This visit has been cancelled.' };
  }

  async selfCheckOut(visitCode: string) {
    const visit = await platformPrisma.visit.findUnique({ where: { visitCode } });
    if (!visit) throw ApiError.notFound('Visit not found');
    if (visit.status !== 'CHECKED_IN') throw ApiError.badRequest('Visit is not currently checked in');

    const checkOutTime = new Date();
    const durationMinutes = visit.checkInTime
      ? Math.round((checkOutTime.getTime() - visit.checkInTime.getTime()) / 60000)
      : undefined;

    return platformPrisma.visit.update({
      where: { visitCode },
      data: {
        status: 'CHECKED_OUT',
        checkOutTime,
        checkOutMethod: 'MOBILE_LINK',
        visitDurationMinutes: durationMinutes,
      },
    });
  }
}

export const publicVisitorService = new PublicVisitorService();
```

### 3.17 Route Mounting Update for Public Routes

Add to `src/app/routes.ts`, before the auth middleware section (after health check, before the blanket auth):

```typescript
import { publicVisitorRoutes } from '../modules/visitors/public/public.routes';

// Public visitor routes (no auth required)
router.use('/public', publicVisitorRoutes);
```

---

## 4. Constants & Configuration Updates

### 4.1 Navigation Manifest Entries

Add to `src/shared/constants/navigation-manifest.ts` after the HRMS section (sortOrder 800+):

```typescript
// ═══════ VISITOR MANAGEMENT ═══════
{ id: 'vms-dashboard', label: 'Visitors Dashboard', icon: 'users', requiredPerm: 'visitors:read', path: '/app/company/visitors/dashboard', module: 'visitor', group: 'Visitor Management', moduleSeparator: 'Visitor Management', roleScope: 'company', sortOrder: 800 },
{ id: 'vms-gate-checkin', label: 'Gate Check-In', icon: 'log-in', requiredPerm: 'visitors:create', path: '/app/company/visitors/gate-check-in', module: 'visitor', group: 'Visitor Management', roleScope: 'company', sortOrder: 801 },
{ id: 'vms-visitor-list', label: 'All Visits', icon: 'list', requiredPerm: 'visitors:read', path: '/app/company/visitors/list', module: 'visitor', group: 'Visitor Management', roleScope: 'company', sortOrder: 802 },
{ id: 'vms-pre-register', label: 'Pre-Register Visitor', icon: 'user-plus', requiredPerm: 'visitors:create', path: '/app/company/visitors/new', module: 'visitor', group: 'Visitor Management', roleScope: 'company', sortOrder: 803 },
{ id: 'vms-recurring-passes', label: 'Recurring Passes', icon: 'repeat', requiredPerm: 'visitors:read', path: '/app/company/visitors/recurring-passes', module: 'visitor', group: 'Passes & Groups', roleScope: 'company', sortOrder: 810 },
{ id: 'vms-group-visits', label: 'Group Visits', icon: 'users', requiredPerm: 'visitors:read', path: '/app/company/visitors/group-visits', module: 'visitor', group: 'Passes & Groups', roleScope: 'company', sortOrder: 811 },
{ id: 'vms-vehicle-passes', label: 'Vehicle Passes', icon: 'truck', requiredPerm: 'visitors:read', path: '/app/company/visitors/vehicle-passes', module: 'visitor', group: 'Passes & Groups', roleScope: 'company', sortOrder: 812 },
{ id: 'vms-material-passes', label: 'Material Passes', icon: 'package', requiredPerm: 'visitors:read', path: '/app/company/visitors/material-passes', module: 'visitor', group: 'Passes & Groups', roleScope: 'company', sortOrder: 813 },
{ id: 'vms-watchlist', label: 'Watchlist & Blocklist', icon: 'shield-alert', requiredPerm: 'visitors:configure', path: '/app/company/visitors/watchlist', module: 'visitor', group: 'Security', roleScope: 'company', sortOrder: 820 },
{ id: 'vms-denied-entries', label: 'Denied Entries', icon: 'x-circle', requiredPerm: 'visitors:read', path: '/app/company/visitors/denied-entries', module: 'visitor', group: 'Security', roleScope: 'company', sortOrder: 821 },
{ id: 'vms-emergency', label: 'Emergency Muster', icon: 'alert-triangle', requiredPerm: 'visitors:read', path: '/app/company/visitors/emergency', module: 'visitor', group: 'Security', roleScope: 'company', sortOrder: 822 },
{ id: 'vms-reports', label: 'Visitor Reports', icon: 'bar-chart', requiredPerm: 'visitors:export', path: '/app/company/visitors/reports', module: 'visitor', group: 'VMS Config', roleScope: 'company', sortOrder: 830 },
{ id: 'vms-history', label: 'Visit History', icon: 'clock', requiredPerm: 'visitors:read', path: '/app/company/visitors/history', module: 'visitor', group: 'VMS Config', roleScope: 'company', sortOrder: 831 },
{ id: 'vms-types', label: 'Visitor Types', icon: 'tag', requiredPerm: 'visitors:configure', path: '/app/company/visitors/settings/types', module: 'visitor', group: 'VMS Config', roleScope: 'company', sortOrder: 840 },
{ id: 'vms-gates', label: 'Gates', icon: 'door-open', requiredPerm: 'visitors:configure', path: '/app/company/visitors/settings/gates', module: 'visitor', group: 'VMS Config', roleScope: 'company', sortOrder: 841 },
{ id: 'vms-inductions', label: 'Safety Inductions', icon: 'shield-check', requiredPerm: 'visitors:configure', path: '/app/company/visitors/settings/inductions', module: 'visitor', group: 'VMS Config', roleScope: 'company', sortOrder: 842 },
{ id: 'vms-settings', label: 'VMS Settings', icon: 'settings', requiredPerm: 'visitors:configure', path: '/app/company/visitors/settings', module: 'visitor', group: 'VMS Config', roleScope: 'company', sortOrder: 850 },
```

**IMPORTANT:** The `module` field must be `'visitor'` (not `'visitors'`) to match the `MODULE_TO_PERMISSION_MAP` key.

### 4.2 Permission Updates

Already defined in `src/shared/constants/permissions.ts`:
- `visitors` module with actions `['read', 'create', 'update', 'delete', 'export', 'configure']`
- `MODULE_TO_PERMISSION_MAP`: `'visitor': ['visitors']`
- Security Personnel role: `'visitors:*'`

**Add `approve` action** to the visitors module:
```typescript
visitors: {
  label: 'Visitor Management',
  actions: ['read', 'create', 'update', 'delete', 'approve', 'export', 'configure'],
},
```

### 4.3 Linked Screens Updates

Add to `src/shared/constants/linked-screens.ts` in the Visitors section:

```typescript
{
  value: 'Visitor Badge',
  label: 'Visitor Badge Number',
  module: 'Visitors',
  description: 'Reference numbers for visitor badge serial numbers',
  defaultPrefix: 'B-',
},
{
  value: 'Recurring Visitor Pass',
  label: 'Recurring Visitor Pass',
  module: 'Visitors',
  description: 'Reference numbers for recurring visitor passes',
  defaultPrefix: 'RP-',
},
{
  value: 'Vehicle Gate Pass',
  label: 'Vehicle Gate Pass',
  module: 'Visitors',
  description: 'Reference numbers for vehicle gate passes',
  defaultPrefix: 'VGP-',
},
{
  value: 'Material Gate Pass',
  label: 'Material Gate Pass',
  module: 'Visitors',
  description: 'Reference numbers for material in/out gate passes',
  defaultPrefix: 'MGP-',
},
{
  value: 'Group Visit',
  label: 'Group Visit',
  module: 'Visitors',
  description: 'Reference numbers for group visit batches',
  defaultPrefix: 'GV-',
},
```

### 4.4 Trigger Events

Add to `src/shared/constants/trigger-events.ts`:

```typescript
// ── Visitor Management ───────────────────────────────────────────────
{
  value: 'VISITOR_HOST_APPROVAL',
  label: 'Visitor Host Approval',
  module: 'Visitors',
  description: 'Triggered when a walk-in or QR self-registered visitor needs host approval',
},
{
  value: 'VISITOR_WALK_IN_APPROVAL',
  label: 'Walk-In Visitor Approval',
  module: 'Visitors',
  description: 'Triggered when a walk-in visitor requires approval before check-in',
},
```

### 4.5 Constants Updates

Update `VISITOR_STATUSES` in `src/shared/constants/index.ts`:

```typescript
VISITOR_STATUSES: {
  EXPECTED: 'EXPECTED',
  ARRIVED: 'ARRIVED',
  CHECKED_IN: 'CHECKED_IN',
  CHECKED_OUT: 'CHECKED_OUT',
  NO_SHOW: 'NO_SHOW',
  CANCELLED: 'CANCELLED',
  REJECTED: 'REJECTED',
  AUTO_CHECKED_OUT: 'AUTO_CHECKED_OUT',
},
```

### 4.6 Route Mounting

Replace the existing stub import in `src/app/routes.ts`:

```typescript
// Replace this line:
import { visitorsRoutes } from '../modules/visitors/routes';
// With the same line (no change needed — the routes.ts file is being replaced)
```

The import already exists at line 27. The stub file at `src/modules/visitors/routes.ts` will be replaced with the full router from Section 3.1.

---

## 5. Web App Implementation

### 5.1 API Client

**File:** `src/lib/api/visitors.ts`

```typescript
import { apiClient } from './client';

// === Visit Management ===
export const visitorApi = {
  // Visits
  listVisits: (params?: Record<string, any>) =>
    apiClient.get('/visitors/visits', { params }).then(r => r.data),
  getVisit: (id: string) =>
    apiClient.get(`/visitors/visits/${id}`).then(r => r.data),
  getVisitByCode: (code: string) =>
    apiClient.get(`/visitors/visits/code/${code}`).then(r => r.data),
  createVisit: (data: any) =>
    apiClient.post('/visitors/visits', data).then(r => r.data),
  createMultiVisit: (data: any) =>
    apiClient.post('/visitors/visits/multi', data).then(r => r.data),
  createWalkIn: (data: any) =>
    apiClient.post('/visitors/visits/walk-in', data).then(r => r.data),
  updateVisit: (id: string, data: any) =>
    apiClient.put(`/visitors/visits/${id}`, data).then(r => r.data),
  cancelVisit: (id: string) =>
    apiClient.delete(`/visitors/visits/${id}`).then(r => r.data),
  checkIn: (id: string, data: any) =>
    apiClient.post(`/visitors/visits/${id}/check-in`, data).then(r => r.data),
  checkOut: (id: string, data: any) =>
    apiClient.post(`/visitors/visits/${id}/check-out`, data).then(r => r.data),
  approveVisit: (id: string, data?: any) =>
    apiClient.post(`/visitors/visits/${id}/approve`, data).then(r => r.data),
  rejectVisit: (id: string, data?: any) =>
    apiClient.post(`/visitors/visits/${id}/reject`, data).then(r => r.data),
  extendVisit: (id: string, data: any) =>
    apiClient.post(`/visitors/visits/${id}/extend`, data).then(r => r.data),
  completeInduction: (id: string, data: any) =>
    apiClient.post(`/visitors/visits/${id}/complete-induction`, data).then(r => r.data),

  // Visitor Types
  listVisitorTypes: (params?: Record<string, any>) =>
    apiClient.get('/visitors/types', { params }).then(r => r.data),
  getVisitorType: (id: string) =>
    apiClient.get(`/visitors/types/${id}`).then(r => r.data),
  createVisitorType: (data: any) =>
    apiClient.post('/visitors/types', data).then(r => r.data),
  updateVisitorType: (id: string, data: any) =>
    apiClient.put(`/visitors/types/${id}`, data).then(r => r.data),
  deactivateVisitorType: (id: string) =>
    apiClient.delete(`/visitors/types/${id}`).then(r => r.data),

  // Gates
  listGates: (params?: Record<string, any>) =>
    apiClient.get('/visitors/gates', { params }).then(r => r.data),
  createGate: (data: any) =>
    apiClient.post('/visitors/gates', data).then(r => r.data),
  updateGate: (id: string, data: any) =>
    apiClient.put(`/visitors/gates/${id}`, data).then(r => r.data),
  deactivateGate: (id: string) =>
    apiClient.delete(`/visitors/gates/${id}`).then(r => r.data),

  // Safety Inductions
  listSafetyInductions: (params?: Record<string, any>) =>
    apiClient.get('/visitors/safety-inductions', { params }).then(r => r.data),
  createSafetyInduction: (data: any) =>
    apiClient.post('/visitors/safety-inductions', data).then(r => r.data),
  updateSafetyInduction: (id: string, data: any) =>
    apiClient.put(`/visitors/safety-inductions/${id}`, data).then(r => r.data),
  deactivateSafetyInduction: (id: string) =>
    apiClient.delete(`/visitors/safety-inductions/${id}`).then(r => r.data),

  // VMS Config
  getConfig: () =>
    apiClient.get('/visitors/config').then(r => r.data),
  updateConfig: (data: any) =>
    apiClient.put('/visitors/config', data).then(r => r.data),

  // Watchlist / Blocklist
  listWatchlist: (params?: Record<string, any>) =>
    apiClient.get('/visitors/watchlist', { params }).then(r => r.data),
  createWatchlistEntry: (data: any) =>
    apiClient.post('/visitors/watchlist', data).then(r => r.data),
  updateWatchlistEntry: (id: string, data: any) =>
    apiClient.put(`/visitors/watchlist/${id}`, data).then(r => r.data),
  removeWatchlistEntry: (id: string) =>
    apiClient.delete(`/visitors/watchlist/${id}`).then(r => r.data),
  checkWatchlist: (data: any) =>
    apiClient.post('/visitors/watchlist/check', data).then(r => r.data),

  // Denied Entries
  listDeniedEntries: (params?: Record<string, any>) =>
    apiClient.get('/visitors/denied-entries', { params }).then(r => r.data),
  getDeniedEntry: (id: string) =>
    apiClient.get(`/visitors/denied-entries/${id}`).then(r => r.data),

  // Recurring Passes
  listRecurringPasses: (params?: Record<string, any>) =>
    apiClient.get('/visitors/recurring-passes', { params }).then(r => r.data),
  createRecurringPass: (data: any) =>
    apiClient.post('/visitors/recurring-passes', data).then(r => r.data),
  updateRecurringPass: (id: string, data: any) =>
    apiClient.put(`/visitors/recurring-passes/${id}`, data).then(r => r.data),
  revokeRecurringPass: (id: string, data: any) =>
    apiClient.post(`/visitors/recurring-passes/${id}/revoke`, data).then(r => r.data),
  checkInViaPass: (id: string, data: any) =>
    apiClient.post(`/visitors/recurring-passes/${id}/check-in`, data).then(r => r.data),

  // Group Visits
  listGroupVisits: (params?: Record<string, any>) =>
    apiClient.get('/visitors/group-visits', { params }).then(r => r.data),
  getGroupVisit: (id: string) =>
    apiClient.get(`/visitors/group-visits/${id}`).then(r => r.data),
  createGroupVisit: (data: any) =>
    apiClient.post('/visitors/group-visits', data).then(r => r.data),
  updateGroupVisit: (id: string, data: any) =>
    apiClient.put(`/visitors/group-visits/${id}`, data).then(r => r.data),
  batchCheckIn: (id: string, data: any) =>
    apiClient.post(`/visitors/group-visits/${id}/batch-check-in`, data).then(r => r.data),
  batchCheckOut: (id: string, data: any) =>
    apiClient.post(`/visitors/group-visits/${id}/batch-check-out`, data).then(r => r.data),

  // Vehicle Passes
  listVehiclePasses: (params?: Record<string, any>) =>
    apiClient.get('/visitors/vehicle-passes', { params }).then(r => r.data),
  createVehiclePass: (data: any) =>
    apiClient.post('/visitors/vehicle-passes', data).then(r => r.data),
  recordVehicleExit: (id: string, data: any) =>
    apiClient.post(`/visitors/vehicle-passes/${id}/exit`, data).then(r => r.data),

  // Material Passes
  listMaterialPasses: (params?: Record<string, any>) =>
    apiClient.get('/visitors/material-passes', { params }).then(r => r.data),
  createMaterialPass: (data: any) =>
    apiClient.post('/visitors/material-passes', data).then(r => r.data),
  markMaterialReturned: (id: string, data: any) =>
    apiClient.post(`/visitors/material-passes/${id}/return`, data).then(r => r.data),

  // Dashboard
  getTodayDashboard: (params?: Record<string, any>) =>
    apiClient.get('/visitors/dashboard/today', { params }).then(r => r.data),
  getOnSiteVisitors: (params?: Record<string, any>) =>
    apiClient.get('/visitors/dashboard/on-site', { params }).then(r => r.data),
  getDashboardStats: (params?: Record<string, any>) =>
    apiClient.get('/visitors/dashboard/stats', { params }).then(r => r.data),

  // Reports
  getDailyLog: (params: Record<string, any>) =>
    apiClient.get('/visitors/reports/daily-log', { params }).then(r => r.data),
  getSummaryReport: (params: Record<string, any>) =>
    apiClient.get('/visitors/reports/summary', { params }).then(r => r.data),
  getOverstayReport: (params: Record<string, any>) =>
    apiClient.get('/visitors/reports/overstay', { params }).then(r => r.data),
  getAnalytics: (params: Record<string, any>) =>
    apiClient.get('/visitors/reports/analytics', { params }).then(r => r.data),

  // Emergency
  triggerEmergency: (data: any) =>
    apiClient.post('/visitors/emergency/trigger', data).then(r => r.data),
  getMusterList: (params: Record<string, any>) =>
    apiClient.get('/visitors/emergency/muster-list', { params }).then(r => r.data),
  resolveEmergency: (data: any) =>
    apiClient.post('/visitors/emergency/resolve', data).then(r => r.data),
};
```

### 5.2 Query Key Factory & Hooks

**File:** `src/features/company-admin/api/use-visitor-queries.ts`

```typescript
import { useQuery } from '@tanstack/react-query';
import { visitorApi } from '@/lib/api/visitors';

export const visitorKeys = {
  all: ['visitors'] as const,
  visits: (params?: any) => params ? [...visitorKeys.all, 'visits', params] : [...visitorKeys.all, 'visits'],
  visit: (id: string) => [...visitorKeys.all, 'visit', id],
  types: (params?: any) => params ? [...visitorKeys.all, 'types', params] : [...visitorKeys.all, 'types'],
  gates: (params?: any) => params ? [...visitorKeys.all, 'gates', params] : [...visitorKeys.all, 'gates'],
  inductions: (params?: any) => params ? [...visitorKeys.all, 'inductions', params] : [...visitorKeys.all, 'inductions'],
  config: () => [...visitorKeys.all, 'config'],
  watchlist: (params?: any) => params ? [...visitorKeys.all, 'watchlist', params] : [...visitorKeys.all, 'watchlist'],
  deniedEntries: (params?: any) => params ? [...visitorKeys.all, 'denied-entries', params] : [...visitorKeys.all, 'denied-entries'],
  recurringPasses: (params?: any) => params ? [...visitorKeys.all, 'recurring-passes', params] : [...visitorKeys.all, 'recurring-passes'],
  groupVisits: (params?: any) => params ? [...visitorKeys.all, 'group-visits', params] : [...visitorKeys.all, 'group-visits'],
  groupVisit: (id: string) => [...visitorKeys.all, 'group-visit', id],
  vehiclePasses: (params?: any) => params ? [...visitorKeys.all, 'vehicle-passes', params] : [...visitorKeys.all, 'vehicle-passes'],
  materialPasses: (params?: any) => params ? [...visitorKeys.all, 'material-passes', params] : [...visitorKeys.all, 'material-passes'],
  dashboard: (params?: any) => params ? [...visitorKeys.all, 'dashboard', params] : [...visitorKeys.all, 'dashboard'],
  onSite: (params?: any) => params ? [...visitorKeys.all, 'on-site', params] : [...visitorKeys.all, 'on-site'],
  stats: (params?: any) => params ? [...visitorKeys.all, 'stats', params] : [...visitorKeys.all, 'stats'],
  analytics: (params?: any) => params ? [...visitorKeys.all, 'analytics', params] : [...visitorKeys.all, 'analytics'],
};

export function useVisits(params?: any) {
  return useQuery({ queryKey: visitorKeys.visits(params), queryFn: () => visitorApi.listVisits(params) });
}

export function useVisit(id: string) {
  return useQuery({ queryKey: visitorKeys.visit(id), queryFn: () => visitorApi.getVisit(id), enabled: !!id });
}

export function useVisitorTypes(params?: any) {
  return useQuery({ queryKey: visitorKeys.types(params), queryFn: () => visitorApi.listVisitorTypes(params) });
}

export function useGates(params?: any) {
  return useQuery({ queryKey: visitorKeys.gates(params), queryFn: () => visitorApi.listGates(params) });
}

export function useSafetyInductions(params?: any) {
  return useQuery({ queryKey: visitorKeys.inductions(params), queryFn: () => visitorApi.listSafetyInductions(params) });
}

export function useVmsConfig() {
  return useQuery({ queryKey: visitorKeys.config(), queryFn: () => visitorApi.getConfig() });
}

export function useWatchlist(params?: any) {
  return useQuery({ queryKey: visitorKeys.watchlist(params), queryFn: () => visitorApi.listWatchlist(params) });
}

export function useDeniedEntries(params?: any) {
  return useQuery({ queryKey: visitorKeys.deniedEntries(params), queryFn: () => visitorApi.listDeniedEntries(params) });
}

export function useRecurringPasses(params?: any) {
  return useQuery({ queryKey: visitorKeys.recurringPasses(params), queryFn: () => visitorApi.listRecurringPasses(params) });
}

export function useGroupVisits(params?: any) {
  return useQuery({ queryKey: visitorKeys.groupVisits(params), queryFn: () => visitorApi.listGroupVisits(params) });
}

export function useGroupVisit(id: string) {
  return useQuery({ queryKey: visitorKeys.groupVisit(id), queryFn: () => visitorApi.getGroupVisit(id), enabled: !!id });
}

export function useVehiclePasses(params?: any) {
  return useQuery({ queryKey: visitorKeys.vehiclePasses(params), queryFn: () => visitorApi.listVehiclePasses(params) });
}

export function useMaterialPasses(params?: any) {
  return useQuery({ queryKey: visitorKeys.materialPasses(params), queryFn: () => visitorApi.listMaterialPasses(params) });
}

export function useTodayDashboard(params?: any) {
  return useQuery({ queryKey: visitorKeys.dashboard(params), queryFn: () => visitorApi.getTodayDashboard(params), refetchInterval: 30000 });
}

export function useOnSiteVisitors(params?: any) {
  return useQuery({ queryKey: visitorKeys.onSite(params), queryFn: () => visitorApi.getOnSiteVisitors(params), refetchInterval: 30000 });
}

export function useVisitorAnalytics(params: any) {
  return useQuery({ queryKey: visitorKeys.analytics(params), queryFn: () => visitorApi.getAnalytics(params) });
}
```

### 5.3 Mutation Hooks

**File:** `src/features/company-admin/api/use-visitor-mutations.ts`

```typescript
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { visitorApi } from '@/lib/api/visitors';
import { showSuccess, showApiError } from '@/lib/toast';
import { visitorKeys } from './use-visitor-queries';

export function useCreateVisit() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (data: any) => visitorApi.createVisit(data),
    onSuccess: () => { showSuccess('Visit pre-registration created'); qc.invalidateQueries({ queryKey: visitorKeys.all }); },
    onError: showApiError,
  });
}

export function useCreateWalkIn() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (data: any) => visitorApi.createWalkIn(data),
    onSuccess: () => { showSuccess('Walk-in visit registered'); qc.invalidateQueries({ queryKey: visitorKeys.all }); },
    onError: showApiError,
  });
}

export function useCheckIn() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: any }) => visitorApi.checkIn(id, data),
    onSuccess: () => { showSuccess('Visitor checked in'); qc.invalidateQueries({ queryKey: visitorKeys.all }); },
    onError: showApiError,
  });
}

export function useCheckOut() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: any }) => visitorApi.checkOut(id, data),
    onSuccess: () => { showSuccess('Visitor checked out'); qc.invalidateQueries({ queryKey: visitorKeys.all }); },
    onError: showApiError,
  });
}

export function useApproveVisit() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ id, data }: { id: string; data?: any }) => visitorApi.approveVisit(id, data),
    onSuccess: () => { showSuccess('Visit approved'); qc.invalidateQueries({ queryKey: visitorKeys.all }); },
    onError: showApiError,
  });
}

export function useRejectVisit() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ id, data }: { id: string; data?: any }) => visitorApi.rejectVisit(id, data),
    onSuccess: () => { showSuccess('Visit rejected'); qc.invalidateQueries({ queryKey: visitorKeys.all }); },
    onError: showApiError,
  });
}

export function useExtendVisit() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: any }) => visitorApi.extendVisit(id, data),
    onSuccess: () => { showSuccess('Visit extended'); qc.invalidateQueries({ queryKey: visitorKeys.all }); },
    onError: showApiError,
  });
}

export function useCancelVisit() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => visitorApi.cancelVisit(id),
    onSuccess: () => { showSuccess('Visit cancelled'); qc.invalidateQueries({ queryKey: visitorKeys.all }); },
    onError: showApiError,
  });
}

// Visitor Types
export function useCreateVisitorType() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (data: any) => visitorApi.createVisitorType(data),
    onSuccess: () => { showSuccess('Visitor type created'); qc.invalidateQueries({ queryKey: visitorKeys.types() }); },
    onError: showApiError,
  });
}

export function useUpdateVisitorType() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: any }) => visitorApi.updateVisitorType(id, data),
    onSuccess: () => { showSuccess('Visitor type updated'); qc.invalidateQueries({ queryKey: visitorKeys.types() }); },
    onError: showApiError,
  });
}

// Gates
export function useCreateGate() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (data: any) => visitorApi.createGate(data),
    onSuccess: () => { showSuccess('Gate created'); qc.invalidateQueries({ queryKey: visitorKeys.gates() }); },
    onError: showApiError,
  });
}

export function useUpdateGate() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: any }) => visitorApi.updateGate(id, data),
    onSuccess: () => { showSuccess('Gate updated'); qc.invalidateQueries({ queryKey: visitorKeys.gates() }); },
    onError: showApiError,
  });
}

// VMS Config
export function useUpdateVmsConfig() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (data: any) => visitorApi.updateConfig(data),
    onSuccess: () => { showSuccess('VMS settings updated'); qc.invalidateQueries({ queryKey: visitorKeys.config() }); },
    onError: showApiError,
  });
}

// Watchlist
export function useCreateWatchlistEntry() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (data: any) => visitorApi.createWatchlistEntry(data),
    onSuccess: () => { showSuccess('Watchlist entry added'); qc.invalidateQueries({ queryKey: visitorKeys.watchlist() }); },
    onError: showApiError,
  });
}

// Recurring Passes
export function useCreateRecurringPass() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (data: any) => visitorApi.createRecurringPass(data),
    onSuccess: () => { showSuccess('Recurring pass created'); qc.invalidateQueries({ queryKey: visitorKeys.recurringPasses() }); },
    onError: showApiError,
  });
}

export function useRevokeRecurringPass() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: any }) => visitorApi.revokeRecurringPass(id, data),
    onSuccess: () => { showSuccess('Recurring pass revoked'); qc.invalidateQueries({ queryKey: visitorKeys.recurringPasses() }); },
    onError: showApiError,
  });
}

// Group Visits
export function useCreateGroupVisit() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (data: any) => visitorApi.createGroupVisit(data),
    onSuccess: () => { showSuccess('Group visit created'); qc.invalidateQueries({ queryKey: visitorKeys.groupVisits() }); },
    onError: showApiError,
  });
}

export function useBatchCheckIn() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: any }) => visitorApi.batchCheckIn(id, data),
    onSuccess: () => { showSuccess('Batch check-in completed'); qc.invalidateQueries({ queryKey: visitorKeys.all }); },
    onError: showApiError,
  });
}

// Vehicle/Material
export function useCreateVehiclePass() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (data: any) => visitorApi.createVehiclePass(data),
    onSuccess: () => { showSuccess('Vehicle gate pass created'); qc.invalidateQueries({ queryKey: visitorKeys.vehiclePasses() }); },
    onError: showApiError,
  });
}

export function useCreateMaterialPass() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (data: any) => visitorApi.createMaterialPass(data),
    onSuccess: () => { showSuccess('Material gate pass created'); qc.invalidateQueries({ queryKey: visitorKeys.materialPasses() }); },
    onError: showApiError,
  });
}

// Emergency
export function useTriggerEmergency() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (data: any) => visitorApi.triggerEmergency(data),
    onSuccess: () => { showSuccess('Emergency muster triggered'); },
    onError: showApiError,
  });
}
```

### 5.4 Screens (17 screens)

All screens are named exports in `src/features/company-admin/visitors/`:

| # | File Path | Component | Route Path | Permission |
|---|---|---|---|---|
| 1 | `visitors/VmsDashboardScreen.tsx` | `VmsDashboardScreen` | `/app/company/visitors/dashboard` | `visitors:read` |
| 2 | `visitors/GateCheckInScreen.tsx` | `GateCheckInScreen` | `/app/company/visitors/gate-check-in` | `visitors:create` |
| 3 | `visitors/VisitorListScreen.tsx` | `VisitorListScreen` | `/app/company/visitors/list` | `visitors:read` |
| 4 | `visitors/VisitorDetailScreen.tsx` | `VisitorDetailScreen` | `/app/company/visitors/:id` | `visitors:read` |
| 5 | `visitors/PreRegisterScreen.tsx` | `PreRegisterScreen` | `/app/company/visitors/new` | `visitors:create` |
| 6 | `visitors/VisitorTypesScreen.tsx` | `VisitorTypesScreen` | `/app/company/visitors/settings/types` | `visitors:configure` |
| 7 | `visitors/GatesScreen.tsx` | `GatesScreen` | `/app/company/visitors/settings/gates` | `visitors:configure` |
| 8 | `visitors/SafetyInductionsScreen.tsx` | `SafetyInductionsScreen` | `/app/company/visitors/settings/inductions` | `visitors:configure` |
| 9 | `visitors/VmsSettingsScreen.tsx` | `VmsSettingsScreen` | `/app/company/visitors/settings` | `visitors:configure` |
| 10 | `visitors/WatchlistScreen.tsx` | `WatchlistScreen` | `/app/company/visitors/watchlist` | `visitors:configure` |
| 11 | `visitors/DeniedEntriesScreen.tsx` | `DeniedEntriesScreen` | `/app/company/visitors/denied-entries` | `visitors:read` |
| 12 | `visitors/RecurringPassesScreen.tsx` | `RecurringPassesScreen` | `/app/company/visitors/recurring-passes` | `visitors:read` |
| 13 | `visitors/GroupVisitsScreen.tsx` | `GroupVisitsScreen` | `/app/company/visitors/group-visits` | `visitors:read` |
| 14 | `visitors/VehiclePassesScreen.tsx` | `VehiclePassesScreen` | `/app/company/visitors/vehicle-passes` | `visitors:read` |
| 15 | `visitors/MaterialPassesScreen.tsx` | `MaterialPassesScreen` | `/app/company/visitors/material-passes` | `visitors:read` |
| 16 | `visitors/VisitorReportsScreen.tsx` | `VisitorReportsScreen` | `/app/company/visitors/reports` | `visitors:export` |
| 17 | `visitors/EmergencyMusterScreen.tsx` | `EmergencyMusterScreen` | `/app/company/visitors/emergency` | `visitors:read` |

### 5.5 Route Definitions

Add to `App.tsx` inside the company admin route group:

```tsx
// Visitor Management
<Route path="company/visitors/dashboard" element={<RequirePermission permission="visitors:read"><Suspense fallback={<Loading />}><VmsDashboardScreen /></Suspense></RequirePermission>} />
<Route path="company/visitors/gate-check-in" element={<RequirePermission permission="visitors:create"><Suspense fallback={<Loading />}><GateCheckInScreen /></Suspense></RequirePermission>} />
<Route path="company/visitors/list" element={<RequirePermission permission="visitors:read"><Suspense fallback={<Loading />}><VisitorListScreen /></Suspense></RequirePermission>} />
<Route path="company/visitors/new" element={<RequirePermission permission="visitors:create"><Suspense fallback={<Loading />}><PreRegisterScreen /></Suspense></RequirePermission>} />
<Route path="company/visitors/:id" element={<RequirePermission permission="visitors:read"><Suspense fallback={<Loading />}><VisitorDetailScreen /></Suspense></RequirePermission>} />
<Route path="company/visitors/recurring-passes" element={<RequirePermission permission="visitors:read"><Suspense fallback={<Loading />}><RecurringPassesScreen /></Suspense></RequirePermission>} />
<Route path="company/visitors/group-visits" element={<RequirePermission permission="visitors:read"><Suspense fallback={<Loading />}><GroupVisitsScreen /></Suspense></RequirePermission>} />
<Route path="company/visitors/vehicle-passes" element={<RequirePermission permission="visitors:read"><Suspense fallback={<Loading />}><VehiclePassesScreen /></Suspense></RequirePermission>} />
<Route path="company/visitors/material-passes" element={<RequirePermission permission="visitors:read"><Suspense fallback={<Loading />}><MaterialPassesScreen /></Suspense></RequirePermission>} />
<Route path="company/visitors/watchlist" element={<RequirePermission permission="visitors:configure"><Suspense fallback={<Loading />}><WatchlistScreen /></Suspense></RequirePermission>} />
<Route path="company/visitors/denied-entries" element={<RequirePermission permission="visitors:read"><Suspense fallback={<Loading />}><DeniedEntriesScreen /></Suspense></RequirePermission>} />
<Route path="company/visitors/emergency" element={<RequirePermission permission="visitors:read"><Suspense fallback={<Loading />}><EmergencyMusterScreen /></Suspense></RequirePermission>} />
<Route path="company/visitors/reports" element={<RequirePermission permission="visitors:export"><Suspense fallback={<Loading />}><VisitorReportsScreen /></Suspense></RequirePermission>} />
<Route path="company/visitors/settings" element={<RequirePermission permission="visitors:configure"><Suspense fallback={<Loading />}><VmsSettingsScreen /></Suspense></RequirePermission>} />
<Route path="company/visitors/settings/types" element={<RequirePermission permission="visitors:configure"><Suspense fallback={<Loading />}><VisitorTypesScreen /></Suspense></RequirePermission>} />
<Route path="company/visitors/settings/gates" element={<RequirePermission permission="visitors:configure"><Suspense fallback={<Loading />}><GatesScreen /></Suspense></RequirePermission>} />
<Route path="company/visitors/settings/inductions" element={<RequirePermission permission="visitors:configure"><Suspense fallback={<Loading />}><SafetyInductionsScreen /></Suspense></RequirePermission>} />
```

Lazy imports at top of `App.tsx`:

```tsx
const VmsDashboardScreen = lazy(() => import('@/features/company-admin/visitors/VmsDashboardScreen').then(m => ({ default: m.VmsDashboardScreen })));
const GateCheckInScreen = lazy(() => import('@/features/company-admin/visitors/GateCheckInScreen').then(m => ({ default: m.GateCheckInScreen })));
// ... (same pattern for all 17 screens)
```

---

## 6. Mobile App Implementation

### 6.1 API Client

**File:** `src/lib/api/visitors.ts`

Same API methods as web (Section 5.1), but using the mobile Axios client:

```typescript
import { apiClient } from './client';

export const visitorApi = {
  // (identical method signatures as web — mobile apiClient has same response interceptor)
  listVisits: (params?: Record<string, any>) =>
    apiClient.get('/visitors/visits', { params }),
  getVisit: (id: string) =>
    apiClient.get(`/visitors/visits/${id}`),
  // ... all methods from Section 5.1
};
```

### 6.2 Query/Mutation Hooks

**File:** `src/features/company-admin/visitors/api/use-visitor-queries.ts`

Same query key factory and hooks as web Section 5.2.

**File:** `src/features/company-admin/visitors/api/use-visitor-mutations.ts`

Same mutations as web Section 5.3, but using `ConfirmModal` instead of toast for destructive actions.

### 6.3 Layout File

**File:** `src/app/(app)/company/visitors/_layout.tsx`

```tsx
import { Stack } from 'expo-router';

export default function VisitorsLayout() {
  return <Stack screenOptions={{ headerShown: false }} />;
}
```

### 6.4 Screens (10+ screens)

| # | Feature File | Route File | Component |
|---|---|---|---|
| 1 | `src/features/company-admin/visitors/VmsDashboardScreen.tsx` | `src/app/(app)/company/visitors/dashboard.tsx` | `VmsDashboardScreen` |
| 2 | `src/features/company-admin/visitors/GateCheckInScreen.tsx` | `src/app/(app)/company/visitors/gate-check-in.tsx` | `GateCheckInScreen` |
| 3 | `src/features/company-admin/visitors/VisitorListScreen.tsx` | `src/app/(app)/company/visitors/list.tsx` | `VisitorListScreen` |
| 4 | `src/features/company-admin/visitors/VisitorDetailScreen.tsx` | `src/app/(app)/company/visitors/[id].tsx` | `VisitorDetailScreen` |
| 5 | `src/features/company-admin/visitors/PreRegisterScreen.tsx` | `src/app/(app)/company/visitors/new.tsx` | `PreRegisterScreen` |
| 6 | `src/features/company-admin/visitors/OnSiteVisitorsScreen.tsx` | `src/app/(app)/company/visitors/on-site.tsx` | `OnSiteVisitorsScreen` |
| 7 | `src/features/company-admin/visitors/QuickCheckOutScreen.tsx` | `src/app/(app)/company/visitors/quick-check-out.tsx` | `QuickCheckOutScreen` |
| 8 | `src/features/company-admin/visitors/EmergencyMusterScreen.tsx` | `src/app/(app)/company/visitors/emergency.tsx` | `EmergencyMusterScreen` |
| 9 | `src/features/company-admin/visitors/VisitorTypesScreen.tsx` | `src/app/(app)/company/visitors/settings/types.tsx` | `VisitorTypesScreen` |
| 10 | `src/features/company-admin/visitors/GatesScreen.tsx` | `src/app/(app)/company/visitors/settings/gates.tsx` | `GatesScreen` |
| 11 | `src/features/company-admin/visitors/WatchlistScreen.tsx` | `src/app/(app)/company/visitors/watchlist.tsx` | `WatchlistScreen` |
| 12 | `src/features/company-admin/visitors/VmsSettingsScreen.tsx` | `src/app/(app)/company/visitors/settings/index.tsx` | `VmsSettingsScreen` |

Each route file is a single-line re-export:

```tsx
// src/app/(app)/company/visitors/dashboard.tsx
export { VmsDashboardScreen as default } from '@/features/company-admin/visitors/VmsDashboardScreen';
```

### 6.5 Screen Implementation Pattern

Each screen follows this structure:

```tsx
import { View, ScrollView, StyleSheet, TouchableOpacity, Text, RefreshControl } from 'react-native';
import Animated, { FadeInDown } from 'react-native-reanimated';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { LinearGradient } from 'expo-linear-gradient';
import { colors } from '@/components/ui/colors';
import { useIsDark } from '@/hooks/use-is-dark';
import { AppTopHeader } from '@/components/ui';
// Import query/mutation hooks
// Import ConfirmModal (never Alert.alert)

export function VmsDashboardScreen() {
  const insets = useSafeAreaInsets();
  const isDark = useIsDark();
  // Query hooks, state, etc.

  return (
    <View style={[styles.container, { paddingTop: insets.top }]}>
      <AppTopHeader title="Visitors Dashboard" />
      <ScrollView>
        {/* Stat cards, visitor list, quick actions */}
      </ScrollView>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#F9FAFB' },
});
```

---

## 7. Public Web Pages (5 pages)

### 7.1 Backend Mounting

Public routes are mounted in `src/app/routes.ts` before any auth middleware:

```typescript
// After health check, before auth routes:
import { publicVisitorRoutes } from '../modules/visitors/public/public.routes';
router.use('/public', publicVisitorRoutes);
```

### 7.2 Web App Public Routes

These are standalone pages outside the authenticated dashboard layout. Add to `App.tsx`:

```tsx
// Public visitor pages (outside RequireAuth)
<Route path="/visit/:visitCode" element={<PreArrivalFormPage />} />
<Route path="/visit/register/:plantCode" element={<SelfRegistrationPage />} />
<Route path="/visit/status/:visitCode" element={<VisitStatusPage />} />
<Route path="/visit/badge/:visitCode" element={<DigitalBadgePage />} />
<Route path="/visit/checkout/:visitCode" element={<SelfCheckOutPage />} />
```

### 7.3 Public Page Files

**Directory:** `src/features/public/visitors/`

| # | File | Component | Description |
|---|---|---|---|
| 1 | `PreArrivalFormPage.tsx` | `PreArrivalFormPage` | Visitor fills details before arrival (photo, ID, vehicle, NDA) |
| 2 | `SelfRegistrationPage.tsx` | `SelfRegistrationPage` | QR poster self-registration form |
| 3 | `VisitStatusPage.tsx` | `VisitStatusPage` | Visitor checks approval status |
| 4 | `DigitalBadgePage.tsx` | `DigitalBadgePage` | Shows digital visitor badge with QR |
| 5 | `SelfCheckOutPage.tsx` | `SelfCheckOutPage` | Self-service check-out |

These pages call the public API endpoints (no auth token needed) and are styled with the company's branding (fetched from the visit data).

---

## 8. Notification Integration

### 8.1 Notification Template IDs

| Template ID | Trigger Point in Code | Recipients |
|---|---|---|
| `VMS_INVITATION` | `visitService.createVisit()` after successful creation | Visitor (via email/SMS) |
| `VMS_HOST_ARRIVAL` | `visitService.checkIn()` after status update | Host employee |
| `VMS_HOST_APPROVAL` | `visitService.createWalkIn()` when approval required | Host employee |
| `VMS_VISITOR_APPROVED` | `visitService.approveVisit()` | Visitor (via SMS) |
| `VMS_VISITOR_REJECTED` | `visitService.rejectVisit()` | Visitor (via SMS) |
| `VMS_HOST_CHECKED_IN` | `visitService.checkIn()` | Host employee |
| `VMS_HOST_CHECKED_OUT` | `visitService.checkOut()` | Host employee |
| `VMS_OVERSTAY` | Cron job `overstayCheck` | Host employee + Security Manager |
| `VMS_EOD_UNCHECKED` | Cron job `autoCheckOut` | Security Manager |
| `VMS_BLOCKLIST_ALERT` | `visitService.checkWatchlistBlocklist()` on blocklist match | Security Manager |
| `VMS_EMERGENCY` | `emergencyService.triggerEmergency()` | All on-site visitors (SMS) |
| `VMS_PASS_EXPIRY` | Cron job `passExpiryNotification` | Pass holder host + visitor |
| `VMS_DIGITAL_BADGE` | `visitService.checkIn()` after badge generation | Visitor (SMS) |

### 8.2 Dispatch Pattern

All notifications are non-blocking (wrapped in try/catch):

```typescript
try {
  const { notificationService } = await import('../../../core/notifications/notification.service');
  await notificationService.dispatch({
    companyId,
    triggerEvent: 'VMS_HOST_CHECKED_IN',
    entityType: 'visit',
    entityId: visit.id,
    explicitRecipients: [visit.hostEmployeeId],
    tokens: { visitorName: visit.visitorName, gate: gateName, badgeNumber },
    type: 'info',
  });
} catch (err) {
  logger.warn('Failed to dispatch VMS notification', { error: err, visitId: visit.id });
}
```

---

## 9. Approval Workflow Integration

### 9.1 Trigger Events

Two new trigger events in `src/shared/constants/trigger-events.ts`:

- `VISITOR_HOST_APPROVAL` -- Walk-in or QR self-reg needs host approval
- `VISITOR_WALK_IN_APPROVAL` -- Specifically for walk-in approval workflows

### 9.2 ESS Service Integration

For walk-in and QR self-registration approvals that use the full approval workflow engine (multi-step, escalation), wire into `essService.createRequest()`:

```typescript
// In visit.service.ts, when creating a walk-in that needs approval:
const { essService } = await import('../../hr/ess/ess.service');
await essService.createRequest({
  companyId,
  employeeId: input.hostEmployeeId, // The host is the "requester"
  triggerEvent: 'VISITOR_HOST_APPROVAL',
  entityType: 'visit',
  entityId: visit.id,
  data: {
    visitorName: input.visitorName,
    visitorCompany: input.visitorCompany,
    purpose: input.purpose,
  },
});
```

### 9.3 onApprovalComplete Handler

Add a case in `ess.service.ts` `onApprovalComplete()` switch:

```typescript
case 'visit': {
  const { visitService } = await import('../../visitors/core/visit.service');
  if (approved) {
    await visitService.approveVisit(companyId, entityId, approvedBy);
  } else {
    await visitService.rejectVisit(companyId, entityId, approvedBy, 'Approval workflow rejected');
  }
  break;
}
```

---

## 10. Concurrency & Data Integrity

### 10.1 Atomic Check-In

The check-in operation uses `$executeRaw` with a conditional `WHERE status IN ('EXPECTED', 'ARRIVED')`:

```sql
UPDATE visits
SET status = 'CHECKED_IN', "checkInTime" = NOW(), ...
WHERE id = :id AND "companyId" = :companyId AND status IN ('EXPECTED', 'ARRIVED')
```

If zero rows are affected, the visit was already checked in (or in an ineligible state). This prevents TOCTOU races when two guards scan the same QR simultaneously.

### 10.2 Atomic Check-Out

Same pattern: `WHERE status = 'CHECKED_IN'`. Second check-out attempt returns conflict error.

### 10.3 Visit Code Uniqueness

- Generated via `crypto.randomBytes()` using charset without ambiguous characters (I, O, 0, 1 excluded)
- Enforced by `@@unique` constraint in Prisma schema
- Retry up to 3 times on collision

### 10.4 Transaction Boundaries

Operations that span multiple writes use `platformPrisma.$transaction()`:
- Visit creation (visit record + number series)
- Check-in (status update + badge generation)
- Group batch check-in (multiple visit records + member status updates)
- Recurring pass check-in (pass validation + visit record creation)

---

## 11. Cron Jobs & Scheduled Tasks

### 11.1 Auto Check-Out (Daily)

**Schedule:** Daily at the configured `autoCheckOutTime` (default 20:00)

```typescript
// In a cron job file (e.g., src/jobs/vms-auto-checkout.ts)
import { platformPrisma } from '../config/database';
import { visitService } from '../modules/visitors/core/visit.service';
import { logger } from '../config/logger';

export async function vmsAutoCheckOutJob() {
  // Get all companies with auto-checkout enabled
  const configs = await platformPrisma.visitorManagementConfig.findMany({
    where: { autoCheckOutEnabled: true },
  });

  for (const config of configs) {
    try {
      const count = await visitService.autoCheckOutAll(config.companyId);
      if (count > 0) {
        logger.info(`VMS auto-checkout: ${count} visitors for company ${config.companyId}`);
        // Dispatch VMS_EOD_UNCHECKED notification
      }
    } catch (err) {
      logger.error('VMS auto-checkout failed', { companyId: config.companyId, error: err });
    }
  }
}
```

### 11.2 Overstay Detection (Every 15 minutes)

**Schedule:** Every 15 minutes

```typescript
export async function vmsOverstayCheckJob() {
  const companies = await platformPrisma.visitorManagementConfig.findMany({
    where: { overstayAlertEnabled: true },
    select: { companyId: true },
  });

  for (const { companyId } of companies) {
    try {
      const overstaying = await visitService.getOverstayingVisitors(companyId);
      for (const visitor of overstaying) {
        // Dispatch VMS_OVERSTAY notification to host + security manager
      }
    } catch (err) {
      logger.error('VMS overstay check failed', { companyId, error: err });
    }
  }
}
```

### 11.3 No-Show Marking (Daily at midnight)

**Schedule:** Daily at 00:00

```typescript
export async function vmsNoShowJob() {
  const count = await visitService.markNoShows();
  if (count > 0) {
    logger.info(`VMS no-show: marked ${count} visits as NO_SHOW`);
  }
}
```

### 11.4 Recurring Pass Expiry Notification (Daily)

**Schedule:** Daily at 09:00

```typescript
export async function vmsPassExpiryJob() {
  // Find passes expiring in the next 7 days
  const sevenDaysFromNow = new Date();
  sevenDaysFromNow.setDate(sevenDaysFromNow.getDate() + 7);

  const expiringPasses = await platformPrisma.recurringVisitorPass.findMany({
    where: {
      status: 'ACTIVE',
      validUntil: { lte: sevenDaysFromNow, gte: new Date() },
    },
  });

  for (const pass of expiringPasses) {
    // Dispatch VMS_PASS_EXPIRY notification
  }

  // Also mark expired passes
  await platformPrisma.recurringVisitorPass.updateMany({
    where: { status: 'ACTIVE', validUntil: { lt: new Date() } },
    data: { status: 'EXPIRED' },
  });
}
```

---

## 12. Implementation Order (Sprint Plan)

### Sprint 1: Schema + Configuration Foundation (Week 1)
**Backend:**
- Create `prisma/modules/visitors/visitors.prisma` with all 12 models + 20 enums
- Add Company relation fields
- Run `pnpm prisma:merge` and `pnpm db:migrate`
- Implement `config/` subdomain: visitor-type CRUD, gate CRUD, safety-induction CRUD, vms-config
- Implement `routes.ts` main router
- Add navigation manifest entries
- Add linked screens for number series
- Add trigger events
- Seed default visitor types method

**Web:**
- Create `src/lib/api/visitors.ts`
- Create query key factory and query hooks
- Implement: VisitorTypesScreen, GatesScreen, SafetyInductionsScreen, VmsSettingsScreen

**Mobile:**
- Create `src/lib/api/visitors.ts`
- Create layout and basic navigation
- Implement: VisitorTypesScreen, GatesScreen, VmsSettingsScreen

### Sprint 2: Core Visit Lifecycle (Week 2)
**Backend:**
- Implement `core/` subdomain: visit.service (create, list, get, update, cancel)
- Pre-registration with visit code + QR generation
- Walk-in registration
- Check-in with atomic conditional update
- Check-out with atomic conditional update
- Approve/Reject flow
- Badge number generation

**Web:**
- Implement: VmsDashboardScreen (stats + today's list)
- Implement: PreRegisterScreen (single + multi-visitor)
- Implement: GateCheckInScreen (expected visitors + check-in form + QR scan)
- Implement: VisitorListScreen (filterable list)
- Implement: VisitorDetailScreen (full detail with timeline)

**Mobile:**
- Implement: VmsDashboardScreen
- Implement: GateCheckInScreen (with camera for QR)
- Implement: PreRegisterScreen
- Implement: QuickCheckOutScreen

### Sprint 3: Security & Compliance (Week 3)
**Backend:**
- Implement `security/` subdomain: watchlist CRUD, blocklist check at check-in
- Implement denied entry auto-creation and listing
- Safety induction completion recording
- Overstay detection service
- Visit extension flow

**Web:**
- Implement: WatchlistScreen (CRUD + search)
- Implement: DeniedEntriesScreen (read-only list)
- Safety induction flow in GateCheckInScreen

**Mobile:**
- Implement: WatchlistScreen
- Implement: OnSiteVisitorsScreen
- Safety induction step in check-in flow

### Sprint 4: Advanced Features (Week 4)
**Backend:**
- Implement `passes/` subdomain: recurring-pass CRUD + check-in-via-pass
- Implement vehicle-pass CRUD + exit recording
- Implement material-pass CRUD + return marking
- Implement `group/` subdomain: group-visit CRUD + batch check-in/check-out

**Web:**
- Implement: RecurringPassesScreen
- Implement: GroupVisitsScreen (with batch operations)
- Implement: VehiclePassesScreen
- Implement: MaterialPassesScreen

**Mobile:**
- Implement: recurring pass check-in flow
- Implement: vehicle/material pass screens (if needed)

### Sprint 5: Reports + Emergency + Cron (Week 5)
**Backend:**
- Implement `reports/` subdomain: daily log, summary, overstay, analytics
- Implement `emergency/` subdomain: trigger, muster list, resolve
- Implement cron jobs: auto-checkout, overstay check, no-show marking, pass expiry
- Notification dispatch for all VMS events

**Web:**
- Implement: VisitorReportsScreen (reports + analytics charts)
- Implement: EmergencyMusterScreen
- Visit history screen (historical data)

**Mobile:**
- Implement: EmergencyMusterScreen (trigger + muster list + marshal marking)

### Sprint 6: Public Pages + Polish (Week 6)
**Backend:**
- Implement `public/` subdomain: all 7 public endpoints
- Mount public routes before auth middleware
- Rate limiting middleware for self-registration

**Web:**
- Implement: 5 public visitor pages (PreArrivalForm, SelfRegistration, VisitStatus, DigitalBadge, SelfCheckOut)
- Badge print template (HTML/CSS for browser print)

**Mobile:**
- QR code scanning integration (expo-camera)
- Offline caching strategy for expected visitors
- Final polish and testing

---

## Appendix A: File Count Summary

| Area | Files |
|---|---|
| Prisma schema | 1 file |
| Backend (routes, controllers, services, validators, types) | ~42 files |
| Web (API client, hooks, screens) | ~22 files |
| Mobile (API client, hooks, screens, routes, layout) | ~25 files |
| Constants updates | 4 files modified |
| **Total** | **~94 files** |

## Appendix B: API Endpoint Summary

| Group | Count |
|---|---|
| Visit management | 12 endpoints |
| Dashboard | 3 endpoints |
| Visitor types | 5 endpoints |
| Gates | 5 endpoints |
| Safety inductions | 5 endpoints |
| VMS config | 2 endpoints |
| Watchlist/Blocklist | 5 endpoints |
| Denied entries | 2 endpoints |
| Recurring passes | 6 endpoints |
| Group visits | 6 endpoints |
| Vehicle passes | 3 endpoints |
| Material passes | 3 endpoints |
| Reports | 4 endpoints |
| Emergency | 3 endpoints |
| Public (no auth) | 7 endpoints |
| **Total** | **~71 endpoints** |
