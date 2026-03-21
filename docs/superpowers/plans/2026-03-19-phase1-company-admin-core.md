# Phase 1: Company Admin Core Infrastructure — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Company Admin can log in, navigate their dedicated dashboard, manage company settings (locations, shifts, contacts, No Series, IOT reasons, controls), manage users/roles/feature-toggles, and view audit logs — all scoped to their own tenant.

**Architecture:** Backend adds company-admin endpoints under `/api/v1/company/*` — mounted after the existing blanket tenant middleware in `routes.ts` (so auth + tenant + access validation are already applied). Role management reuses existing `/api/v1/rbac/*` endpoints (no duplication). Mobile and Web apps add company-admin navigation, screens, and API hooks. Company Admin **cannot** add new locations — only edit/delete existing ones.

**Key Decisions:**
- Company-admin routes are mounted **after** the blanket `authMiddleware + requireTenant + validateTenantAccess` in `routes.ts`, so no additional middleware needed on mount
- Role management uses existing `/rbac/roles` routes (already tenant-scoped with permission guards) — no duplicate `/company/roles` endpoints
- Feature toggle management uses existing `/feature-toggles` routes — screens built for company-admin UI
- `audit:read` permission must be added to `COMPANY_ADMIN` default permissions in `auth.middleware.ts`
- Location POST is explicitly defined to return 403 (not 404) for clear error messaging
- Dashboard KPIs redesigned to match available backend data (user/location/module counts) — HR-centric KPIs (employees, attendance, leave) will come in Phase 2+

**Tech Stack:** Node.js/Express/Prisma (backend), React Native/Expo Router (mobile), React/Vite/React Router (web), Zustand + React Query (state), Zod (validation), Tailwind/NativeWind (styling)

**Master Plan:** See `2026-03-19-company-admin-and-hrms-master-plan.md`

---

## File Structure

### Backend — New Files
```
avy-erp-backend/src/
├── core/
│   └── company-admin/
│       ├── company-admin.routes.ts      # All company-admin tenant-scoped routes
│       ├── company-admin.controller.ts  # Controller for company profile, settings
│       ├── company-admin.service.ts     # Service: get/update own company, locations, shifts, etc.
│       └── company-admin.validators.ts  # Zod schemas for company-admin inputs
```

### Backend — Modified Files
```
avy-erp-backend/src/
├── app/routes.ts                        # Mount company-admin routes
├── core/dashboard/dashboard.service.ts  # Enhance getCompanyAdminStats()
├── core/dashboard/dashboard.routes.ts   # Add activity endpoint for company-admin
├── core/audit/audit.routes.ts           # Add tenant-scoped audit log route
├── core/audit/audit.service.ts          # Add tenant-scoped query method
├── middleware/auth.middleware.ts         # Add audit:read to COMPANY_ADMIN permissions
```

### Mobile App — New Files
```
mobile-app/src/
├── app/(app)/company/
│   ├── _layout.tsx                      # Stack layout for company-admin screens
│   ├── profile.tsx                      # Company profile route
│   ├── locations.tsx                    # Location management route
│   ├── shifts.tsx                       # Shift management route
│   ├── contacts.tsx                     # Key contacts route
│   ├── no-series.tsx                    # No series config route
│   ├── iot-reasons.tsx                  # IOT reasons route
│   ├── controls.tsx                     # System controls route
│   ├── settings.tsx                     # Company settings route
│   ├── users.tsx                        # User management route
│   ├── roles.tsx                        # Role management route
│   └── feature-toggles.tsx              # Feature toggle management route
├── features/company-admin/
│   ├── api/
│   │   ├── use-company-admin-queries.ts # React Query hooks for company-admin
│   │   └── use-company-admin-mutations.ts # Mutations for updates
│   ├── company-profile-screen.tsx
│   ├── location-management-screen.tsx
│   ├── shift-management-screen.tsx
│   ├── contact-management-screen.tsx
│   ├── no-series-management-screen.tsx
│   ├── iot-reason-management-screen.tsx
│   ├── system-controls-screen.tsx
│   ├── company-settings-screen.tsx
│   ├── user-management-screen.tsx
│   ├── role-management-screen.tsx
│   └── feature-toggle-screen.tsx
├── lib/api/
│   └── company-admin.ts                 # API layer for company-admin endpoints
```

### Mobile App — Modified Files
```
mobile-app/src/
├── app/(app)/_layout.tsx                # Add company-admin sidebar sections + tabs
├── features/company-admin/dashboard-screen.tsx  # Enhance with real API data
├── lib/api/index.ts                     # Export new API modules
```

### Web App — New Files
```
web-system-app/src/
├── features/company-admin/
│   ├── CompanyProfileScreen.tsx
│   ├── LocationManagementScreen.tsx
│   ├── ShiftManagementScreen.tsx
│   ├── ContactManagementScreen.tsx
│   ├── NoSeriesManagementScreen.tsx
│   ├── IOTReasonManagementScreen.tsx
│   ├── SystemControlsScreen.tsx
│   ├── CompanySettingsScreen.tsx
│   ├── UserManagementScreen.tsx
│   ├── RoleManagementScreen.tsx
│   ├── FeatureToggleScreen.tsx
│   └── api/
│       ├── use-company-admin-queries.ts
│       └── use-company-admin-mutations.ts
├── lib/api/
│   └── company-admin.ts
```

### Web App — Modified Files
```
web-system-app/src/
├── App.tsx                              # Add company-admin routes
├── layouts/Sidebar.tsx                  # Add company-admin nav sections
├── features/company-admin/CompanyAdminDashboard.tsx  # Enhance
```

---

## Task 1: Backend — Company Admin API Endpoints

**Files:**
- Create: `avy-erp-backend/src/core/company-admin/company-admin.routes.ts`
- Create: `avy-erp-backend/src/core/company-admin/company-admin.controller.ts`
- Create: `avy-erp-backend/src/core/company-admin/company-admin.service.ts`
- Create: `avy-erp-backend/src/core/company-admin/company-admin.validators.ts`
- Modify: `avy-erp-backend/src/app/routes.ts`

### Endpoints to create:

```
# Company Profile (own company)
GET    /api/v1/company/profile              # Get own company detail
PATCH  /api/v1/company/profile/sections/:sectionKey  # Update allowed sections

# Locations (edit/delete only — NO create)
GET    /api/v1/company/locations             # List own company locations
GET    /api/v1/company/locations/:id         # Get single location
POST   /api/v1/company/locations             # BLOCKED — returns 403 with clear message
PATCH  /api/v1/company/locations/:id         # Update location
DELETE /api/v1/company/locations/:id         # Delete location

# Shifts
GET    /api/v1/company/shifts                # List shifts
POST   /api/v1/company/shifts                # Create shift
PATCH  /api/v1/company/shifts/:id            # Update shift
DELETE /api/v1/company/shifts/:id            # Delete shift

# Contacts
GET    /api/v1/company/contacts              # List contacts
POST   /api/v1/company/contacts              # Create contact
PATCH  /api/v1/company/contacts/:id          # Update contact
DELETE /api/v1/company/contacts/:id          # Delete contact

# No Series
GET    /api/v1/company/no-series             # List no series
POST   /api/v1/company/no-series             # Create no series
PATCH  /api/v1/company/no-series/:id         # Update no series
DELETE /api/v1/company/no-series/:id         # Delete no series

# IOT Reasons
GET    /api/v1/company/iot-reasons           # List IOT reasons
POST   /api/v1/company/iot-reasons           # Create IOT reason
PATCH  /api/v1/company/iot-reasons/:id       # Update IOT reason
DELETE /api/v1/company/iot-reasons/:id       # Delete IOT reason

# System Controls
GET    /api/v1/company/controls              # Get system controls
PATCH  /api/v1/company/controls              # Update system controls

# Settings (preferences)
GET    /api/v1/company/settings              # Get company settings/preferences
PATCH  /api/v1/company/settings              # Update settings

# Users (within own tenant)
GET    /api/v1/company/users                 # List users (with pagination: page, limit, search, role, status)
POST   /api/v1/company/users                 # Create user
GET    /api/v1/company/users/:id             # Get user
PATCH  /api/v1/company/users/:id             # Update user
PATCH  /api/v1/company/users/:id/status      # Activate/deactivate

# Audit Logs (tenant-scoped)
GET    /api/v1/company/audit-logs            # List own company audit logs (with pagination)

# Roles — REUSE existing /api/v1/rbac/* routes (already tenant-scoped)
# NO duplicate role endpoints under /company — frontend calls /rbac/roles directly

# Feature Toggles — REUSE existing /api/v1/feature-toggles routes (already tenant-scoped)
# NO duplicate endpoints — frontend calls /feature-toggles directly
```

- [ ] **Step 1: Create the validators file**

Create `avy-erp-backend/src/core/company-admin/company-admin.validators.ts` with Zod schemas for all inputs: location update, shift create/update, contact create/update, no-series, iot-reason, controls, settings, user create/update. Follow the pattern in `src/core/tenant/tenant.validators.ts`.

- [ ] **Step 2: Create the service file**

Create `avy-erp-backend/src/core/company-admin/company-admin.service.ts`. The service must:
- Accept `companyId` (derived from authenticated user's `req.user.companyId`)
- Use `platformPrisma` for all queries (same as CompanyService)
- For locations: support `findMany`, `findUnique`, `update`, `delete` — but NOT `create`
- For shifts/contacts/noSeries/iotReasons: full CRUD scoped to companyId
- For company profile: reuse `TenantService.getFullCompanyDetail()` for GET, restrict sections for PATCH (only: identity partial, contacts, shifts, noSeries, iotReasons, controls)
- For users: create with `COMPANY_ADMIN` or custom role, hash password with bcrypt, create TenantUser bridge record
- For audit logs: filter `AuditLog` by `tenantId` matching user's tenant

- [ ] **Step 3: Create the controller file**

Create `avy-erp-backend/src/core/company-admin/company-admin.controller.ts`. Follow the `CompanyController` pattern:
- Use `asyncHandler` wrapper
- Extract `companyId` from `req.user.companyId`
- Validate inputs with Zod schemas
- Return `createSuccessResponse()` or `createPaginatedResponse()`
- For location create attempts: return 403 with message "Only Super Admin can add new locations"

- [ ] **Step 4: Create the routes file**

Create `avy-erp-backend/src/core/company-admin/company-admin.routes.ts`. Use `requirePermissions()` middleware:
- Profile: `company:read`, `company:update`
- Locations: `company:read`, `company:update`, `company:delete` (NO create permission)
- Shifts/Contacts/NoSeries/IOT/Controls: `company:*`
- Users: `user:read`, `user:create`, `user:update`
- Audit: `audit:read`

- [ ] **Step 5: Mount routes in main router + fix permissions**

Modify `avy-erp-backend/src/app/routes.ts`:
- Import `companyAdminRoutes`
- Mount under `/company` AFTER the existing blanket middleware block (lines 87-91 which already apply `authMiddleware + requireTenant + validateTenantAccess`) — no additional middleware needed on mount
- Simply: `router.use('/company', companyAdminRoutes);`

Modify `avy-erp-backend/src/middleware/auth.middleware.ts`:
- Add `'audit:read'` to the `COMPANY_ADMIN` permissions array (currently has `user:*`, `role:*`, `company:*`, etc.)
- The updated array should include: `['user:*', 'role:*', 'company:*', 'hr:*', 'production:*', 'inventory:*', 'sales:*', 'finance:*', 'maintenance:*', 'reports:*', 'audit:read']`

- [ ] **Step 6: Enhance dashboard service**

Modify `avy-erp-backend/src/core/dashboard/dashboard.service.ts`:
- Add `getCompanyAdminActivity(companyId, limit)` method that queries `AuditLog` filtered by `tenantId`
- Enhance `getCompanyAdminStats()` to include: employee placeholders (0 for now, will be real in Phase 2), shifts count, contacts count, noSeries count, iot reasons count

- [ ] **Step 7: Add tenant-scoped audit log route**

Modify `avy-erp-backend/src/core/audit/audit.service.ts`:
- Add `listTenantAuditLogs(tenantId, options)` method with same pagination/filter as platform version but filtered by tenantId

Modify `avy-erp-backend/src/core/audit/audit.routes.ts` or add to `company-admin.routes.ts`:
- The audit log endpoint under `/company/audit-logs` should call this new method

- [ ] **Step 8: Test all endpoints**

Run: `npm run dev` and test with curl/Postman:
- Login as company-admin user → get token
- Test each endpoint with the token + `X-Tenant-ID` header
- Verify location create returns 403
- Verify audit logs are tenant-scoped

- [ ] **Step 9: Commit**

```bash
git add src/core/company-admin/ src/app/routes.ts src/core/dashboard/ src/core/audit/
git commit -m "feat: add company-admin backend API endpoints for self-service management"
```

---

## Task 2: Mobile App — Company Admin Navigation & Layout

**Files:**
- Modify: `mobile-app/src/app/(app)/_layout.tsx`
- Create: `mobile-app/src/app/(app)/company/_layout.tsx`

- [ ] **Step 1: Update tab layout with company-admin sidebar sections**

Modify `mobile-app/src/app/(app)/_layout.tsx`:
- Update the `companyAdminSections` array in the sidebar to include:
  - **Dashboard** section: Dashboard
  - **Company** section: Profile, Locations, Shifts, Contacts
  - **Configuration** section: No Series, IOT Reasons, Controls, Settings
  - **People** section: Users, Roles
  - **Reports** section: Audit Logs
  - **Support** section: Help, Support
- Each item should have: id, label, icon (from existing icon set), onPress (router.push)
- Add tab visibility for company-admin: show Dashboard + More tabs, hide Companies + Billing

- [ ] **Step 2: Create company stack layout**

Create `mobile-app/src/app/(app)/company/_layout.tsx`:
- Stack navigator for all company-admin sub-screens
- `screenOptions`: headerShown false (screens manage their own headers)

- [ ] **Step 3: Create route files for each screen**

Create route files that re-export from features (following existing pattern `export { Screen as default }`):
- `mobile-app/src/app/(app)/company/profile.tsx`
- `mobile-app/src/app/(app)/company/locations.tsx`
- `mobile-app/src/app/(app)/company/shifts.tsx`
- `mobile-app/src/app/(app)/company/contacts.tsx`
- `mobile-app/src/app/(app)/company/no-series.tsx`
- `mobile-app/src/app/(app)/company/iot-reasons.tsx`
- `mobile-app/src/app/(app)/company/controls.tsx`
- `mobile-app/src/app/(app)/company/settings.tsx`
- `mobile-app/src/app/(app)/company/users.tsx`
- `mobile-app/src/app/(app)/company/roles.tsx`

Each file is a thin wrapper:
```typescript
export { CompanyProfileScreen as default } from '@/features/company-admin/company-profile-screen';
```

- [ ] **Step 4: Commit**

```bash
git add src/app/
git commit -m "feat: add company-admin navigation layout and route files (mobile)"
```

---

## Task 3: Mobile App — API Layer & Query Hooks

**Files:**
- Create: `mobile-app/src/lib/api/company-admin.ts`
- Create: `mobile-app/src/features/company-admin/api/use-company-admin-queries.ts`
- Create: `mobile-app/src/features/company-admin/api/use-company-admin-mutations.ts`

- [ ] **Step 1: Create API layer**

Create `mobile-app/src/lib/api/company-admin.ts`:
```typescript
import { client } from './client';

export const companyAdminApi = {
  // Profile
  getProfile: () => client.get('/company/profile'),
  updateProfileSection: (sectionKey: string, data: any) =>
    client.patch(`/company/profile/sections/${sectionKey}`, data),

  // Locations (NO create)
  listLocations: () => client.get('/company/locations'),
  getLocation: (id: string) => client.get(`/company/locations/${id}`),
  updateLocation: (id: string, data: any) => client.patch(`/company/locations/${id}`, data),
  deleteLocation: (id: string) => client.delete(`/company/locations/${id}`),

  // Shifts
  listShifts: () => client.get('/company/shifts'),
  createShift: (data: any) => client.post('/company/shifts', data),
  updateShift: (id: string, data: any) => client.patch(`/company/shifts/${id}`, data),
  deleteShift: (id: string) => client.delete(`/company/shifts/${id}`),

  // Contacts
  listContacts: () => client.get('/company/contacts'),
  createContact: (data: any) => client.post('/company/contacts', data),
  updateContact: (id: string, data: any) => client.patch(`/company/contacts/${id}`, data),
  deleteContact: (id: string) => client.delete(`/company/contacts/${id}`),

  // No Series
  listNoSeries: () => client.get('/company/no-series'),
  createNoSeries: (data: any) => client.post('/company/no-series', data),
  updateNoSeries: (id: string, data: any) => client.patch(`/company/no-series/${id}`, data),
  deleteNoSeries: (id: string) => client.delete(`/company/no-series/${id}`),

  // IOT Reasons
  listIOTReasons: () => client.get('/company/iot-reasons'),
  createIOTReason: (data: any) => client.post('/company/iot-reasons', data),
  updateIOTReason: (id: string, data: any) => client.patch(`/company/iot-reasons/${id}`, data),
  deleteIOTReason: (id: string) => client.delete(`/company/iot-reasons/${id}`),

  // Controls
  getControls: () => client.get('/company/controls'),
  updateControls: (data: any) => client.patch('/company/controls', data),

  // Settings
  getSettings: () => client.get('/company/settings'),
  updateSettings: (data: any) => client.patch('/company/settings', data),

  // Users
  listUsers: (params?: any) => client.get('/company/users', { params }),
  getUser: (id: string) => client.get(`/company/users/${id}`),
  createUser: (data: any) => client.post('/company/users', data),
  updateUser: (id: string, data: any) => client.patch(`/company/users/${id}`, data),
  updateUserStatus: (id: string, data: any) => client.patch(`/company/users/${id}/status`, data),

  // Audit Logs
  listAuditLogs: (params?: any) => client.get('/company/audit-logs', { params }),
};
```

- [ ] **Step 2: Create query hooks**

Create `mobile-app/src/features/company-admin/api/use-company-admin-queries.ts` with query key factories and hooks:
- `useCompanyProfile()`, `useCompanyLocations()`, `useCompanyShifts()`, `useCompanyContacts()`
- `useCompanyNoSeries()`, `useCompanyIOTReasons()`, `useCompanyControls()`, `useCompanySettings()`
- `useCompanyUsers(params)`, `useCompanyAuditLogs(params)`
- Follow existing `tenantKeys` / `dashboardKeys` pattern

- [ ] **Step 3: Create mutation hooks**

Create `mobile-app/src/features/company-admin/api/use-company-admin-mutations.ts`:
- `useUpdateProfileSection()`, `useUpdateLocation()`, `useDeleteLocation()`
- `useCreateShift()`, `useUpdateShift()`, `useDeleteShift()`
- `useCreateContact()`, `useUpdateContact()`, `useDeleteContact()`
- `useCreateNoSeries()`, `useUpdateNoSeries()`, `useDeleteNoSeries()`
- `useCreateIOTReason()`, `useUpdateIOTReason()`, `useDeleteIOTReason()`
- `useUpdateControls()`, `useUpdateSettings()`
- `useCreateUser()`, `useUpdateUser()`, `useUpdateUserStatus()`
- Each mutation invalidates relevant query keys on success

- [ ] **Step 4: Commit**

```bash
git add src/lib/api/company-admin.ts src/features/company-admin/api/
git commit -m "feat: add company-admin API layer and React Query hooks (mobile)"
```

---

## Task 4: Mobile App — Enhanced Dashboard Screen

**Files:**
- Modify: `mobile-app/src/features/company-admin/dashboard-screen.tsx`

- [ ] **Step 1: Enhance the existing dashboard with real API data**

Replace mock data with real `useCompanyAdminStats()` and `useCompanyAdminActivity()` hooks.

KPI Cards (4-card grid):
- Total Users (from stats.totalUsers)
- Active Locations (from stats.totalLocations)
- Active Modules (from stats.activeModules)
- Company Status (from stats.wizardStatus with StatusBadge)

Quick Actions (navigate to company-admin screens):
- Manage Users → `/company/users`
- Manage Shifts → `/company/shifts`
- Manage Contacts → `/company/contacts`
- Audit Logs → `/reports/audit`

Recent Activity section using real audit log data.

Follow the exact same UI pattern as `SuperAdminDashboard`:
- LinearGradient header with HamburgerButton
- Animated FadeInDown/FadeInUp cards
- Pull-to-refresh with RefreshControl
- Loading skeleton, error state with retry

- [ ] **Step 2: Commit**

```bash
git add src/features/company-admin/dashboard-screen.tsx
git commit -m "feat: enhance company-admin dashboard with real API data (mobile)"
```

---

## Task 5: Mobile App — Company Profile Screen

**Files:**
- Create: `mobile-app/src/features/company-admin/company-profile-screen.tsx`

- [ ] **Step 1: Build the company profile screen**

Display company info in read-only cards with edit capability for allowed sections.

**Read-only sections** (display only, no edit):
- Company Code, Business Type, Industry, CIN
- Statutory: PAN, TAN, GSTIN, PF Reg, ESI Code
- Modules & Billing: selected modules, user tier, billing cycle

**Editable sections** (pencil icon → bottom sheet edit form):
- Display Name, Legal Name, Short Name, Logo
- Corporate Email Domain, Website
- Registered Address, Corporate Address

Use `useCompanyProfile()` query and `useUpdateProfileSection()` mutation.

Follow super-admin `company-detail-screen.tsx` pattern:
- ScrollView with SectionCards
- Bottom sheet modal for editing (using @gorhom/bottom-sheet)
- ConfirmModal for destructive actions
- StatusBadge for company status

- [ ] **Step 2: Commit**

```bash
git add src/features/company-admin/company-profile-screen.tsx
git commit -m "feat: add company profile screen for company-admin (mobile)"
```

---

## Task 6: Mobile App — Location Management Screen

**Files:**
- Create: `mobile-app/src/features/company-admin/location-management-screen.tsx`

- [ ] **Step 1: Build location management screen**

List all company locations with edit/delete capability but NO add button.

**List view:**
- FlatList of location cards
- Each card: name, code, facilityType, status, isHQ badge, city/state
- Search bar to filter by name/code

**Edit (bottom sheet):**
- Address fields, contact person, geo-fencing toggle
- GST details
- Status (Active/Inactive/Under Construction)
- Save button calls `useUpdateLocation()`

**Delete:**
- ConfirmModal with danger variant
- Cannot delete HQ location (show warning)
- Calls `useDeleteLocation()`

**Important:** No FAB, no "Add Location" button anywhere. If user asks, show info toast: "New locations can only be added by the Super Admin."

- [ ] **Step 2: Commit**

```bash
git add src/features/company-admin/location-management-screen.tsx
git commit -m "feat: add location management screen (edit/delete only) for company-admin (mobile)"
```

---

## Task 7: Mobile App — Shift, Contact, No Series, IOT, Controls Screens

**Files:**
- Create: `mobile-app/src/features/company-admin/shift-management-screen.tsx`
- Create: `mobile-app/src/features/company-admin/contact-management-screen.tsx`
- Create: `mobile-app/src/features/company-admin/no-series-management-screen.tsx`
- Create: `mobile-app/src/features/company-admin/iot-reason-management-screen.tsx`
- Create: `mobile-app/src/features/company-admin/system-controls-screen.tsx`

- [ ] **Step 1: Build shift management screen**

Full CRUD for shifts. List view + FAB to add + bottom sheet form for create/edit.
Fields: name, fromTime, toTime, noShuffle toggle, downtime slots (array).
Reuse shift form pattern from `tenant-onboarding/steps/step12-shifts.tsx`.

- [ ] **Step 2: Build contact management screen**

Full CRUD for contacts. List view + FAB to add + bottom sheet form.
Fields: name, designation, department, type, email, countryCode, mobile, linkedin.
Reuse contact form pattern from `tenant-onboarding/steps/step11-contacts.tsx`.

- [ ] **Step 3: Build No Series management screen**

Full CRUD. List with table view (code, description, linked screen, preview).
Bottom sheet form: code, description, linkedScreen (dropdown), prefix, suffix, numberCount, startNumber.
Live preview of generated number format.
Reuse pattern from `tenant-onboarding/steps/step13-no-series.tsx`.

- [ ] **Step 4: Build IOT Reason management screen**

Full CRUD. List + FAB. Bottom sheet form.
Fields: reasonType (Machine Idle/Alarm), reason, description, department, planned checkbox, duration (conditional).
Reuse pattern from `tenant-onboarding/steps/step14-iot-reasons.tsx`.

- [ ] **Step 5: Build system controls screen**

Toggle-based screen (no list). Uses `useCompanyControls()` + `useUpdateControls()`.
Sections: NC Reason Assignment, Load/Unload, Cycle Time, and any additional controls.
Reuse pattern from `tenant-onboarding/steps/step15-controls.tsx`.

- [ ] **Step 6: Commit**

```bash
git add src/features/company-admin/shift-management-screen.tsx \
        src/features/company-admin/contact-management-screen.tsx \
        src/features/company-admin/no-series-management-screen.tsx \
        src/features/company-admin/iot-reason-management-screen.tsx \
        src/features/company-admin/system-controls-screen.tsx
git commit -m "feat: add shift, contact, no-series, iot-reason, controls screens for company-admin (mobile)"
```

---

## Task 8: Mobile App — User, Role & Feature Toggle Screens

**Files:**
- Create: `mobile-app/src/features/company-admin/user-management-screen.tsx`
- Create: `mobile-app/src/features/company-admin/role-management-screen.tsx`
- Create: `mobile-app/src/features/company-admin/feature-toggle-screen.tsx`

- [ ] **Step 1: Build user management screen**

List users in the tenant. Search + filter by role/status.
Each user card: name, email, role, status (Active/Inactive), last login.
FAB to add user → bottom sheet form: fullName, email, phone, role (dropdown from tenant roles), password, status.
Edit user: same form pre-filled.
Deactivate: toggle status with ConfirmModal.

Uses `useCompanyUsers()` query and `useCreateUser()`, `useUpdateUser()`, `useUpdateUserStatus()` mutations from company-admin hooks.

- [ ] **Step 2: Build role management screen**

**Important:** This screen consumes the EXISTING `/rbac/roles` API endpoints — no new backend routes needed. The RBAC routes are already tenant-scoped and permission-guarded.

List roles. System roles shown with lock icon (non-editable).
FAB to create custom role.
Role form (full screen or bottom sheet):
- Name, description
- Permission matrix: expandable sections per module, checkboxes per action (View/Create/Edit/Delete/Approve)
- Use reference roles as templates (button: "Start from template" → calls `GET /rbac/reference-roles`)
Delete custom role: ConfirmModal (prevent if users assigned).

Create new hooks in `use-company-admin-queries.ts`:
- `useRoles()` → `GET /rbac/roles`
- `usePermissionCatalogue()` → `GET /rbac/permissions`
- `useReferenceRoles()` → `GET /rbac/reference-roles`
And mutations: `useCreateRole()`, `useUpdateRole()`, `useDeleteRole()`, `useAssignRole()`

- [ ] **Step 3: Build feature toggle screen**

**Important:** This screen consumes the EXISTING `/feature-toggles` API endpoints — no new backend routes needed.

Screen shows a list of users in the tenant. For each user, a collapsible card shows available feature toggles with on/off switches.
- Select user from dropdown/search → show their current feature overrides
- Toggle features on/off → calls `POST /feature-toggles` to create/update
- Show which features are inherited from role vs. explicitly overridden
- Use `GET /feature-toggles` to list current toggles

Create hooks:
- `useFeatureToggles()` → `GET /feature-toggles`
- `useSetFeatureToggle()` → `POST /feature-toggles`

- [ ] **Step 4: Commit**

```bash
git add src/features/company-admin/user-management-screen.tsx \
        src/features/company-admin/role-management-screen.tsx \
        src/features/company-admin/feature-toggle-screen.tsx
git commit -m "feat: add user, role, and feature toggle management screens for company-admin (mobile)"
```

---

## Task 9: Mobile App — Company Settings & Audit Log Screens

**Files:**
- Create: `mobile-app/src/features/company-admin/company-settings-screen.tsx`

- [ ] **Step 1: Build company settings screen**

Settings organized in SectionCards:
- **Locale**: Currency, Language, Date Format, Number Format, Time Format (dropdowns)
- **Compliance**: India Statutory Mode toggle, Multi-Currency toggle
- **Portal & App**: ESS Portal toggle, Mobile App toggle, AI Chatbot toggle, e-Sign toggle
- **Integrations**: Biometric Sync toggle, Payroll Bank Integration toggle, Email Notifications toggle, WhatsApp toggle

Use `useCompanySettings()` + `useUpdateSettings()`.

- [ ] **Step 2: Update audit log to work for company-admin**

The existing `audit-log-screen.tsx` calls `/platform/audit-logs` (super-admin only). For company-admin, it must call `/company/audit-logs` instead.

Update `mobile-app/src/lib/api/audit.ts`:
- Add `listTenantAuditLogs` method that calls `GET /company/audit-logs`

Update `mobile-app/src/features/super-admin/audit-log-screen.tsx` (or create a shared version):
- Import `useAuthStore.use.userRole()` to detect role
- If `userRole === 'company-admin'` → use `companyAdminApi.listAuditLogs()`
- If `userRole === 'super-admin'` → use existing `auditApi.listAuditLogs()`
- Alternatively, create a wrapper hook `useAuditLogsForRole()` that handles the conditional

Same approach for the web app's `AuditLogScreen.tsx`.

- [ ] **Step 3: Commit**

```bash
git add src/features/company-admin/company-settings-screen.tsx
git commit -m "feat: add company settings screen and audit log support for company-admin (mobile)"
```

---

## Task 10: Web App — Company Admin Routes & Sidebar

**Files:**
- Modify: `web-system-app/src/App.tsx`
- Modify: `web-system-app/src/layouts/Sidebar.tsx`

- [ ] **Step 1: Add company-admin routes to App.tsx**

Add routes under `/app/company/*` wrapped with `<RequireRole roles={['company-admin']}>`:
```
/app/company/profile          → CompanyProfileScreen
/app/company/locations         → LocationManagementScreen
/app/company/shifts            → ShiftManagementScreen
/app/company/contacts          → ContactManagementScreen
/app/company/no-series         → NoSeriesManagementScreen
/app/company/iot-reasons       → IOTReasonManagementScreen
/app/company/controls          → SystemControlsScreen
/app/company/settings          → CompanySettingsScreen
/app/company/users             → UserManagementScreen
/app/company/roles             → RoleManagementScreen
/app/company/feature-toggles   → FeatureToggleScreen
```

- [ ] **Step 2: Update sidebar with company-admin sections**

Modify `web-system-app/src/layouts/Sidebar.tsx`:
- Add company-admin sections to `NAV_CONFIG`:
  - **Overview**: Dashboard
  - **Company**: Profile, Locations, Shifts, Contacts
  - **Configuration**: No Series, IOT Reasons, Controls, Settings
  - **People**: Users & Access (sub-items: Users, Roles)
  - **Reports**: Audit Logs
- Filter by role: `roles: ['company_admin']`
- Add appropriate Lucide icons for each item

- [ ] **Step 3: Update TopBar PAGE_TITLES map**

Add titles for all new company-admin routes.

- [ ] **Step 4: Commit**

```bash
git add src/App.tsx src/layouts/Sidebar.tsx src/layouts/TopBar.tsx
git commit -m "feat: add company-admin routes and sidebar navigation (web)"
```

---

## Task 11: Web App — API Layer & Query Hooks

**Files:**
- Create: `web-system-app/src/lib/api/company-admin.ts`
- Create: `web-system-app/src/features/company-admin/api/use-company-admin-queries.ts`
- Create: `web-system-app/src/features/company-admin/api/use-company-admin-mutations.ts`

- [ ] **Step 1: Create API layer**

Mirror the mobile API layer in `web-system-app/src/lib/api/company-admin.ts` — same endpoints, same structure. Uses `client` from `./client`.

- [ ] **Step 2: Create query and mutation hooks**

Mirror mobile hooks in web format. Same query keys, same invalidation patterns.

- [ ] **Step 3: Commit**

```bash
git add src/lib/api/company-admin.ts src/features/company-admin/api/
git commit -m "feat: add company-admin API layer and React Query hooks (web)"
```

---

## Task 12: Web App — Company Admin Feature Screens

**Files:**
- Create all screens listed in the file structure above under `web-system-app/src/features/company-admin/`

- [ ] **Step 1: Build CompanyProfileScreen**

Two-column layout: left = company info cards, right = editable sections.
Read-only: company code, statutory info, modules.
Editable: display name, logo, addresses, website.
Modal for editing sections (using `<Modal />` component).
Follow `CompanyDetailScreen` pattern from super-admin.

- [ ] **Step 2: Build LocationManagementScreen**

DataTable with location rows. Action column: Edit, Delete.
NO "Add Location" button.
Edit modal with address, contact, GST, geo-fencing fields.
Delete with confirmation dialog.

- [ ] **Step 3: Build ShiftManagementScreen**

DataTable + "Add Shift" button.
Modal form: name, from/to time, no-shuffle, downtime slots.
Edit/delete actions per row.

- [ ] **Step 4: Build ContactManagementScreen**

Card grid or DataTable. "Add Contact" button.
Modal form: name, designation, department, type, email, phone.

- [ ] **Step 5: Build NoSeriesManagementScreen**

DataTable with preview column. "Add Series" button.
Modal form with live preview: `{prefix}{padded_number}{suffix}`.

- [ ] **Step 6: Build IOTReasonManagementScreen**

DataTable + "Add Reason". Modal form with conditional fields (planned checkbox → duration).

- [ ] **Step 7: Build SystemControlsScreen**

Card-based toggle layout. Sections with switch toggles.
Save button at bottom.

- [ ] **Step 8: Build CompanySettingsScreen**

Grouped settings: Locale, Compliance, Portal, Integrations.
Dropdown selectors and toggles.

- [ ] **Step 9: Build UserManagementScreen**

DataTable with user list. Search + filter by role/status.
"Add User" button → modal form.
Row actions: Edit, Activate/Deactivate.

- [ ] **Step 10: Build RoleManagementScreen**

Role list with system role badges. Uses existing `/rbac/roles` endpoints (no new backend routes).
"Create Role" button → full-page form with permission matrix grid.
Reference role templates as starting points (from `GET /rbac/reference-roles`).

- [ ] **Step 11: Build FeatureToggleScreen**

User selector → per-user toggle list. Uses existing `/feature-toggles` endpoints.
Show role-inherited permissions vs. explicit overrides.
Toggle switches to enable/disable features per user.

- [ ] **Step 12: Enhance CompanyAdminDashboard**

Replace mock data with real API calls. Match super-admin dashboard pattern:
- KPI cards with trend indicators
- DataTable for recent activity
- Quick action cards linking to company screens

- [ ] **Step 13: Commit**

```bash
git add src/features/company-admin/
git commit -m "feat: add all company-admin feature screens (web)"
```

---

## Task 13: Integration Testing

- [ ] **Step 1: Test complete flow — Backend**

1. Login as company-admin → get token
2. GET `/company/profile` → verify own company data returned
3. PATCH `/company/profile/sections/identity` → verify partial update works
4. GET `/company/locations` → verify locations listed
5. POST `/company/locations` → verify 403 Forbidden
6. PATCH `/company/locations/:id` → verify update works
7. Full CRUD on shifts, contacts, no-series, iot-reasons
8. GET/PATCH controls and settings
9. Create user, assign role, deactivate user
10. GET `/company/audit-logs` → verify tenant-scoped

- [ ] **Step 2: Test Mobile App**

1. Login as company-admin
2. Verify sidebar shows correct sections (not super-admin sections)
3. Navigate through all screens
4. Edit a location, create a shift, add a contact
5. Create a user, assign a role
6. View audit logs

- [ ] **Step 3: Test Web App**

Same flow as mobile but in browser.

- [ ] **Step 4: Commit any fixes**

```bash
git commit -m "fix: integration test fixes for company-admin flow"
```

---

## Task 14: Memory & Documentation Update

- [ ] **Step 1: Update project memory**

Update `/Users/chetan/.claude/projects/-Users-chetan-Documents-Avyren-Technologies-Products-Mobile-ERP/memory/MEMORY.md` with:
- New company-admin feature folder structure
- New API endpoints
- New route paths
- Updated sidebar sections

- [ ] **Step 2: Mark Phase 1 complete in master plan**

Update master plan document to mark Phase 1 as completed.

---

## Dependencies Between Tasks

```
Task 1 (Backend API) ─────┐
                           ├──► Task 4 (Mobile Dashboard)
Task 2 (Mobile Nav) ──────┤
                           ├──► Task 5-9 (Mobile Screens)
Task 3 (Mobile API) ──────┘
                                      │
Task 10 (Web Nav) ────────┐           │
                           ├──► Task 12 (Web Screens)
Task 11 (Web API) ────────┘           │
                                      ▼
                              Task 13 (Integration Testing)
                                      │
                                      ▼
                              Task 14 (Memory Update)
```

**Parallelizable:** Tasks 1-3 can run in parallel. Tasks 10-11 can run in parallel. Tasks 5-9 can run in parallel after Tasks 1-3 complete.

---

*Phase 1 implementation plan — Avy ERP Company Admin Core Infrastructure*
