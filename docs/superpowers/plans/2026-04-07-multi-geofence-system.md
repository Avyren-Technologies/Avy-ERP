# Multi-Geofence System — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a dedicated Geofence model supporting multiple named geofence zones per location, with Google Maps integration (searchable places, draggable markers, radius visualization) in both web and mobile company admin, geofence assignment on employees/users, and updated attendance check-in logic.

**Architecture:** New `Geofence` Prisma model (many-to-one with Location). Backend CRUD endpoints under `/company/locations/:locationId/geofences`. Web gets `@react-google-maps/api` based split-panel manager inside location edit. Mobile updates existing location management screen with geofence list + full-screen map editor. Employee model gets `geofenceId` FK with auto-assignment of location's default geofence. Attendance check-in updated to validate against assigned geofence or fall back to all location geofences.

**Tech Stack:** Prisma, ExcelJS (existing), `@react-google-maps/api` (new for web), `react-native-maps` + `react-native-google-places-autocomplete` (existing for mobile), Google Maps JavaScript API + Places API

**Spec:** `docs/superpowers/specs/2026-04-07-multi-geofence-system-design.md`

---

## File Structure

### Backend (avy-erp-backend)

| Action | File | Responsibility |
|--------|------|----------------|
| Create | `prisma/modules/company-admin/geofence.prisma` | Geofence model definition |
| Modify | `prisma/modules/hrms/employee.prisma` | Add geofenceId field + relation |
| Modify | `prisma/modules/company-admin/locations.prisma` | Add geofences relation |
| Modify | `prisma/modules/platform/tenant.prisma` | Add geofences relation on Company |
| Create | `src/core/company-admin/geofence.validators.ts` | Zod schemas for geofence CRUD |
| Create | `src/core/company-admin/geofence.service.ts` | Geofence CRUD + default management |
| Create | `src/core/company-admin/geofence.controller.ts` | Endpoint handlers |
| Modify | `src/core/company-admin/company-admin.routes.ts` | Mount geofence routes |
| Modify | `src/modules/hr/ess/ess.controller.ts` | Update check-in geofence validation |
| Modify | `src/modules/hr/employee/employee.service.ts` | Auto-assign default geofence |
| Modify | `src/modules/hr/employee/employee.validators.ts` | Add geofenceId field |

### Web (web-system-app)

| Action | File | Responsibility |
|--------|------|----------------|
| Install | `@react-google-maps/api` | Google Maps React components |
| Add | `.env` — `VITE_GOOGLE_MAPS_API_KEY` | API key env var |
| Modify | `src/lib/api/company-admin.ts` | Add geofence API functions |
| Create | `src/features/company-admin/api/use-geofence-queries.ts` | React Query hooks for geofence CRUD |
| Create | `src/features/company-admin/settings/GeofenceManager.tsx` | Split-panel geofence manager (list + Google Maps) |
| Modify | `src/features/company-admin/LocationManagementScreen.tsx` | Add Geofences section using GeofenceManager |
| Modify | `src/features/company-admin/hr/EmployeeProfileScreen.tsx` | Add geofence dropdown after location |

### Mobile (mobile-app)

| Action | File | Responsibility |
|--------|------|----------------|
| Modify | `src/lib/api/company-admin.ts` | Add geofence API functions |
| Create | `src/features/company-admin/api/use-geofence-queries.ts` | React Query hooks |
| Create | `src/features/company-admin/geofence-editor-screen.tsx` | Full-screen map editor for add/edit geofence |
| Create | `src/app/(app)/company/geofence-editor.tsx` | Route file |
| Modify | `src/features/company-admin/location-management-screen.tsx` | Add geofences list per location |
| Modify | `src/features/company-admin/hr/employee-detail-screen.tsx` | Add geofence dropdown |

---

## Task 1: Prisma Schema — Geofence Model + Employee/Location Relations

**Files:**
- Create: `avy-erp-backend/prisma/modules/company-admin/geofence.prisma`
- Modify: `avy-erp-backend/prisma/modules/hrms/employee.prisma`
- Modify: `avy-erp-backend/prisma/modules/company-admin/locations.prisma`
- Modify: `avy-erp-backend/prisma/modules/platform/tenant.prisma`

- [ ] **Step 1: Create the Geofence model**

Create `prisma/modules/company-admin/geofence.prisma`:

```prisma
// ==========================================
// COMPANY ADMIN — Geofences
// ==========================================
// Multiple named geofence zones per Location

model Geofence {
  id         String   @id @default(cuid())
  locationId String
  location   Location @relation(fields: [locationId], references: [id], onDelete: Cascade)
  companyId  String
  company    Company  @relation(fields: [companyId], references: [id], onDelete: Cascade)

  name       String
  lat        Float
  lng        Float
  radius     Int      @default(100)
  address    String?

  isDefault  Boolean  @default(false)
  isActive   Boolean  @default(true)

  createdAt  DateTime @default(now())
  updatedAt  DateTime @updatedAt

  employees  Employee[]

  @@unique([locationId, name])
  @@index([companyId])
  @@index([locationId])
  @@map("geofences")
}
```

- [ ] **Step 2: Add geofences relation to Location model**

In `prisma/modules/company-admin/locations.prisma`, add this line inside the Location model, after the existing relations (after `transfersTo` line):

```prisma
  // Geofences
  geofences   Geofence[]
```

- [ ] **Step 3: Add geofences relation to Company model**

In `prisma/modules/platform/tenant.prisma`, find the Company model and add:

```prisma
  geofences          Geofence[]
```

Add it near the other relation arrays (after existing relations like `locations`, `employees`, etc.).

- [ ] **Step 4: Add geofenceId to Employee model**

In `prisma/modules/hrms/employee.prisma`, add after the `locationId`/`location` fields (around line 60):

```prisma
  geofenceId          String?
  geofence            Geofence? @relation(fields: [geofenceId], references: [id])
```

- [ ] **Step 5: Merge and generate Prisma client**

```bash
cd avy-erp-backend && pnpm prisma:merge && pnpm db:generate
```

- [ ] **Step 6: Run migration**

```bash
cd avy-erp-backend && pnpm db:migrate
```

Migration name: `add_geofence_model`

- [ ] **Step 7: Verify TypeScript compiles**

```bash
npx tsc --noEmit 2>&1 | head -10
```

- [ ] **Step 8: Commit**

```bash
git add prisma/
git commit -m "feat(geofence): add Geofence model with Location/Employee relations and migrate"
```

---

## Task 2: Backend — Geofence Validators

**Files:**
- Create: `avy-erp-backend/src/core/company-admin/geofence.validators.ts`

- [ ] **Step 1: Create Zod schemas for geofence CRUD**

```typescript
import { z } from 'zod';

export const createGeofenceSchema = z.object({
  name: z.string().min(1, 'Name is required').max(100),
  lat: z.number().min(-90).max(90, 'Latitude must be between -90 and 90'),
  lng: z.number().min(-180).max(180, 'Longitude must be between -180 and 180'),
  radius: z.number().int().min(10, 'Minimum radius is 10m').max(10000, 'Maximum radius is 10km').default(100),
  address: z.string().optional(),
  isDefault: z.boolean().optional(),
});

export const updateGeofenceSchema = createGeofenceSchema.partial();
```

- [ ] **Step 2: Verify compiles**

```bash
cd avy-erp-backend && npx tsc --noEmit 2>&1 | head -5
```

- [ ] **Step 3: Commit**

```bash
git add src/core/company-admin/geofence.validators.ts
git commit -m "feat(geofence): add Zod schemas for geofence CRUD"
```

---

## Task 3: Backend — Geofence Service

**Files:**
- Create: `avy-erp-backend/src/core/company-admin/geofence.service.ts`

- [ ] **Step 1: Create the geofence service**

Class-based service with these methods:

**Imports (relative paths):**
```typescript
import { platformPrisma } from '../../config/database';
import { logger } from '../../config/logger';
import { ApiError } from '../../shared/errors';
```

**Methods:**

1. `async listGeofences(companyId: string, locationId: string)` — Find all geofences for a location (ordered by isDefault desc, name asc). Include `_count: { employees: true }` to show employee count per geofence.

2. `async getGeofence(companyId: string, id: string)` — Find one geofence, verify companyId matches, include employee count.

3. `async createGeofence(companyId: string, locationId: string, data: { name, lat, lng, radius, address?, isDefault? })`:
   - Verify location exists and belongs to company
   - If `isDefault: true`, unset existing default for this location atomically (`updateMany where locationId + isDefault: true → isDefault: false`)
   - Create the geofence record
   - If this is the first geofence for the location, auto-set as default
   - Return created record

4. `async updateGeofence(companyId: string, id: string, data: Partial)`:
   - Verify geofence exists and belongs to company
   - If `isDefault: true`, unset existing default for this location first
   - Update the record
   - Return updated record

5. `async deleteGeofence(companyId: string, id: string)`:
   - Verify geofence exists and belongs to company
   - Check if any employees are assigned: `count where geofenceId = id`. If count > 0, throw ApiError.badRequest with count.
   - If this was the default, try to set another geofence as default (first remaining active one)
   - Delete the record

6. `async setDefault(companyId: string, id: string)`:
   - Verify geofence exists and belongs to company
   - Unset existing default for this location
   - Set this one as default
   - Return updated record

7. `async listGeofencesForDropdown(companyId: string, locationId: string)` — Simplified list for employee form dropdowns: returns `{ id, name, radius, isDefault }` for all active geofences.

**Export:** `export const geofenceService = new GeofenceService();`

- [ ] **Step 2: Verify compiles**

```bash
cd avy-erp-backend && npx tsc --noEmit 2>&1 | head -10
```

- [ ] **Step 3: Commit**

```bash
git add src/core/company-admin/geofence.service.ts
git commit -m "feat(geofence): add geofence CRUD service with default management"
```

---

## Task 4: Backend — Geofence Controller & Routes

**Files:**
- Create: `avy-erp-backend/src/core/company-admin/geofence.controller.ts`
- Modify: `avy-erp-backend/src/core/company-admin/company-admin.routes.ts`

- [ ] **Step 1: Create the controller**

Follow existing company-admin controller pattern. Methods:
- `listGeofences` — GET, extracts locationId from params, companyId from req.user
- `createGeofence` — POST, validates with createGeofenceSchema
- `updateGeofence` — PATCH, validates with updateGeofenceSchema
- `deleteGeofence` — DELETE
- `setDefault` — PATCH /:id/default
- `listForDropdown` — GET /company/geofences?locationId=X (flat route for dropdowns)

All use `asyncHandler`, `ApiError`, `createSuccessResponse` pattern.

- [ ] **Step 2: Mount routes in company-admin.routes.ts**

Add AFTER the locations routes (after line 16 `router.delete('/locations/:id', ...)`):

```typescript
import { geofenceController } from './geofence.controller';

// ── Geofences ─────────────────────────────────────────────────────────
router.get('/geofences', requirePermissions(['company:read']), geofenceController.listForDropdown);
router.get('/locations/:locationId/geofences', requirePermissions(['company:read']), geofenceController.listGeofences);
router.post('/locations/:locationId/geofences', requirePermissions(['company:configure']), geofenceController.createGeofence);
router.patch('/locations/:locationId/geofences/:id', requirePermissions(['company:configure']), geofenceController.updateGeofence);
router.delete('/locations/:locationId/geofences/:id', requirePermissions(['company:configure']), geofenceController.deleteGeofence);
router.patch('/locations/:locationId/geofences/:id/default', requirePermissions(['company:configure']), geofenceController.setDefault);
```

- [ ] **Step 3: Verify compiles**

```bash
cd avy-erp-backend && npx tsc --noEmit 2>&1 | head -10
```

- [ ] **Step 4: Commit**

```bash
git add src/core/company-admin/geofence.controller.ts src/core/company-admin/company-admin.routes.ts
git commit -m "feat(geofence): add controller and mount geofence routes"
```

---

## Task 5: Backend — Update Attendance Check-In & Employee Service

**Files:**
- Modify: `avy-erp-backend/src/modules/hr/ess/ess.controller.ts`
- Modify: `avy-erp-backend/src/modules/hr/employee/employee.service.ts`
- Modify: `avy-erp-backend/src/modules/hr/employee/employee.validators.ts`

- [ ] **Step 1: Update check-in geofence validation in ess.controller.ts**

Replace the current geofence validation block (lines 1130-1143) with new logic:

```typescript
// Geofence validation — check against employee's assigned geofence or all location geofences
let geoStatus = 'NO_LOCATION';
if (latitude != null && longitude != null) {
  const employee = await platformPrisma.employee.findUnique({
    where: { id: employeeId },
    select: { geofenceId: true, locationId: true },
  });

  const effectiveLocationId = locationId || employee?.locationId;

  if (employee?.geofenceId) {
    // Check against specific assigned geofence
    const geofence = await platformPrisma.geofence.findUnique({ where: { id: employee.geofenceId } });
    if (geofence?.isActive) {
      const dist = calculateDistance(latitude, longitude, geofence.lat, geofence.lng);
      geoStatus = dist <= geofence.radius ? 'INSIDE_GEOFENCE' : 'OUTSIDE_GEOFENCE';
    }
  } else if (effectiveLocationId) {
    // Check against ALL active geofences for the location
    const geofences = await platformPrisma.geofence.findMany({
      where: { locationId: effectiveLocationId, isActive: true },
    });
    if (geofences.length > 0) {
      const insideAny = geofences.some(gf => calculateDistance(latitude, longitude, gf.lat, gf.lng) <= gf.radius);
      geoStatus = insideAny ? 'INSIDE_GEOFENCE' : 'OUTSIDE_GEOFENCE';
    } else {
      // Fall back to legacy Location geo fields
      const location = await platformPrisma.location.findUnique({ where: { id: effectiveLocationId } });
      if (location?.geoEnabled && location.geoLat && location.geoLng) {
        const dist = calculateDistance(latitude, longitude, parseFloat(location.geoLat), parseFloat(location.geoLng));
        geoStatus = dist <= location.geoRadius ? 'INSIDE_GEOFENCE' : 'OUTSIDE_GEOFENCE';
      }
    }
  }
}
```

- [ ] **Step 2: Add geofenceId to employee validators**

In `employee.validators.ts`, add to `createEmployeeSchema` (after `locationId`):

```typescript
  geofenceId: z.string().optional(),
```

- [ ] **Step 3: Auto-assign default geofence in employee.service.ts**

In the `createEmployee` method, after the employee is created in the transaction (after the `tx.employee.create()` call), add logic to auto-assign the default geofence:

```typescript
// Auto-assign default geofence if location is set and no geofence specified
if (!data.geofenceId && (data.locationId || employee.locationId)) {
  const effectiveLocationId = data.locationId || employee.locationId;
  const defaultGeofence = await tx.geofence.findFirst({
    where: { locationId: effectiveLocationId!, isDefault: true, isActive: true },
    select: { id: true },
  });
  if (defaultGeofence) {
    await tx.employee.update({
      where: { id: employee.id },
      data: { geofenceId: defaultGeofence.id },
    });
  }
}
```

Also in the `updateEmployee` method, when `locationId` changes, clear old geofence and assign new default:

```typescript
// If location changed, reassign default geofence
if (data.locationId && data.locationId !== existing.locationId) {
  if (!data.geofenceId) {
    const defaultGeofence = await platformPrisma.geofence.findFirst({
      where: { locationId: data.locationId, isDefault: true, isActive: true },
      select: { id: true },
    });
    updateData.geofenceId = defaultGeofence?.id ?? null;
  }
}
```

Add `geofenceId` to the employee create data mapping (in the `tx.employee.create({ data: { ... } })` block):

```typescript
geofenceId: n(data.geofenceId),
```

- [ ] **Step 4: Verify compiles**

```bash
cd avy-erp-backend && npx tsc --noEmit 2>&1 | head -10
```

- [ ] **Step 5: Commit**

```bash
git add src/modules/hr/ess/ess.controller.ts src/modules/hr/employee/employee.service.ts src/modules/hr/employee/employee.validators.ts
git commit -m "feat(geofence): update attendance check-in and employee auto-assignment"
```

---

## Task 6: Web — API Layer & Hooks

**Files:**
- Modify: `web-system-app/src/lib/api/company-admin.ts`
- Create: `web-system-app/src/features/company-admin/api/use-geofence-queries.ts`

- [ ] **Step 1: Read existing company-admin API file to understand patterns**

Read `web-system-app/src/lib/api/company-admin.ts` to see how location API functions are structured.

- [ ] **Step 2: Add geofence API functions to company-admin.ts**

Add to the `companyAdminApi` object:

```typescript
// Geofences
listGeofences: (locationId: string) =>
    client.get(`/company/locations/${locationId}/geofences`).then(r => r.data),

listGeofencesForDropdown: (locationId: string) =>
    client.get('/company/geofences', { params: { locationId } }).then(r => r.data),

createGeofence: (locationId: string, data: any) =>
    client.post(`/company/locations/${locationId}/geofences`, data).then(r => r.data),

updateGeofence: (locationId: string, id: string, data: any) =>
    client.patch(`/company/locations/${locationId}/geofences/${id}`, data).then(r => r.data),

deleteGeofence: (locationId: string, id: string) =>
    client.delete(`/company/locations/${locationId}/geofences/${id}`).then(r => r.data),

setDefaultGeofence: (locationId: string, id: string) =>
    client.patch(`/company/locations/${locationId}/geofences/${id}/default`).then(r => r.data),
```

Adjust the pattern to match whatever the existing file uses (some files use `async function` + `response.data`, others use arrow functions with `.then`).

- [ ] **Step 3: Create React Query hooks**

Create `web-system-app/src/features/company-admin/api/use-geofence-queries.ts`:

```typescript
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { companyAdminApi } from '@/lib/api/company-admin';
import { showApiError } from '@/lib/toast';

export const geofenceKeys = {
    all: ['geofences'] as const,
    byLocation: (locationId: string) => [...geofenceKeys.all, locationId] as const,
    dropdown: (locationId: string) => [...geofenceKeys.all, 'dropdown', locationId] as const,
};

export function useGeofences(locationId: string) {
    return useQuery({
        queryKey: geofenceKeys.byLocation(locationId),
        queryFn: () => companyAdminApi.listGeofences(locationId),
        enabled: !!locationId,
    });
}

export function useGeofencesForDropdown(locationId?: string) {
    return useQuery({
        queryKey: geofenceKeys.dropdown(locationId!),
        queryFn: () => companyAdminApi.listGeofencesForDropdown(locationId!),
        enabled: !!locationId,
    });
}

export function useCreateGeofence() {
    const qc = useQueryClient();
    return useMutation({
        mutationFn: ({ locationId, data }: { locationId: string; data: any }) =>
            companyAdminApi.createGeofence(locationId, data),
        onSuccess: (_, vars) => {
            qc.invalidateQueries({ queryKey: geofenceKeys.byLocation(vars.locationId) });
            qc.invalidateQueries({ queryKey: geofenceKeys.dropdown(vars.locationId) });
        },
        onError: showApiError,
    });
}

export function useUpdateGeofence() {
    const qc = useQueryClient();
    return useMutation({
        mutationFn: ({ locationId, id, data }: { locationId: string; id: string; data: any }) =>
            companyAdminApi.updateGeofence(locationId, id, data),
        onSuccess: (_, vars) => {
            qc.invalidateQueries({ queryKey: geofenceKeys.byLocation(vars.locationId) });
            qc.invalidateQueries({ queryKey: geofenceKeys.dropdown(vars.locationId) });
        },
        onError: showApiError,
    });
}

export function useDeleteGeofence() {
    const qc = useQueryClient();
    return useMutation({
        mutationFn: ({ locationId, id }: { locationId: string; id: string }) =>
            companyAdminApi.deleteGeofence(locationId, id),
        onSuccess: (_, vars) => {
            qc.invalidateQueries({ queryKey: geofenceKeys.byLocation(vars.locationId) });
            qc.invalidateQueries({ queryKey: geofenceKeys.dropdown(vars.locationId) });
        },
        onError: showApiError,
    });
}

export function useSetDefaultGeofence() {
    const qc = useQueryClient();
    return useMutation({
        mutationFn: ({ locationId, id }: { locationId: string; id: string }) =>
            companyAdminApi.setDefaultGeofence(locationId, id),
        onSuccess: (_, vars) => {
            qc.invalidateQueries({ queryKey: geofenceKeys.byLocation(vars.locationId) });
            qc.invalidateQueries({ queryKey: geofenceKeys.dropdown(vars.locationId) });
        },
        onError: showApiError,
    });
}
```

- [ ] **Step 4: Verify compiles**

```bash
cd web-system-app && npx tsc --noEmit 2>&1 | head -10
```

- [ ] **Step 5: Commit**

```bash
git add src/lib/api/company-admin.ts src/features/company-admin/api/use-geofence-queries.ts
git commit -m "feat(geofence): add web API layer and React Query hooks for geofence CRUD"
```

---

## Task 7: Web — GeofenceManager Component (Google Maps)

**Files:**
- Create: `web-system-app/src/features/company-admin/settings/GeofenceManager.tsx`

- [ ] **Step 1: Install Google Maps package**

```bash
cd web-system-app && pnpm add @react-google-maps/api
```

- [ ] **Step 2: Add env variable**

Add `VITE_GOOGLE_MAPS_API_KEY=` to `.env` (or `.env.local`). The developer fills in their API key.

- [ ] **Step 3: Create the GeofenceManager component**

This is the main UI component. Read the spec for the exact layout:

**Props:** `{ locationId: string; companyId: string; locationLat?: string; locationLng?: string }`

**Layout:** Split-panel — left list (300px) + right map (flex).

**Left Panel:**
- Header: "Geofences" + count badge + "Add Geofence" button (primary, indigo)
- List of geofence cards (scrollable):
  - Name (bold), Address (gray, truncated), Radius badge, Default badge (indigo if isDefault)
  - Active/Inactive toggle (small switch)
  - Edit icon → select for editing on map
  - Delete icon → confirm modal → calls delete mutation
  - Click card → highlights on map, shows edit form
- Empty state: icon + "No geofences configured" message

**Right Panel (Google Maps):**
- `GoogleMap` component from `@react-google-maps/api`
- Load with `useJsApiLoader({ googleMapsApiKey: import.meta.env.VITE_GOOGLE_MAPS_API_KEY, libraries: ['places'] })`
- Map default center: `locationLat/locationLng` or India center (20.5937, 78.9629)
- **Google Places Autocomplete:** `Autocomplete` component from `@react-google-maps/api` at top of map — search bar with icon. On place selected: map pans + marker moves + lat/lng updates.
- **Draggable Marker:** `Marker` with `draggable={true}`, `onDragEnd` updates lat/lng in form state
- **Circle overlay:** `Circle` component showing radius of editing geofence (semi-transparent indigo fill `rgba(79, 70, 229, 0.15)`, indigo stroke)
- All existing geofences shown as gray semi-transparent circles with center markers
- Selected/editing geofence highlighted in indigo

**Below map (edit form, only visible when adding/editing):**
- Name input
- Lat/Lng display (read-only, auto-updated by marker drag/search)
- Radius selector: chip buttons (50m, 100m, 200m, 300m, 500m, 1km) + custom number input
- Address display (auto-filled from Places, editable)
- "Set as Default" checkbox
- Save / Cancel buttons

**Styling:**
- Tailwind CSS with primary=indigo palette
- Rounded-xl borders, subtle shadows
- Map height: min 400px, flex to fill available space
- Consistent with existing company admin screens

**State management:**
- `editingGeofence: Geofence | null` — currently editing/adding
- `isAdding: boolean` — new vs edit mode
- Form state: name, lat, lng, radius, address, isDefault

**Mutations used:**
- `useGeofences(locationId)` — list
- `useCreateGeofence()` — create
- `useUpdateGeofence()` — update
- `useDeleteGeofence()` — delete
- `useSetDefaultGeofence()` — set default

- [ ] **Step 4: Verify compiles**

```bash
cd web-system-app && npx tsc --noEmit 2>&1 | head -10
```

- [ ] **Step 5: Commit**

```bash
git add src/features/company-admin/settings/GeofenceManager.tsx
git commit -m "feat(geofence): add GeofenceManager with Google Maps, Places search, draggable markers"
```

---

## Task 8: Web — Integrate GeofenceManager into Location Screen + Employee Form

**Files:**
- Modify: `web-system-app/src/features/company-admin/LocationManagementScreen.tsx`
- Modify: `web-system-app/src/features/company-admin/hr/EmployeeProfileScreen.tsx`

- [ ] **Step 1: Read LocationManagementScreen.tsx to understand the edit modal/form structure**

Read the full file. The location edit is likely a modal or inline form. Find where to add the GeofenceManager section.

- [ ] **Step 2: Add GeofenceManager section to location edit**

When a location is being edited (editingLocation is set), add a "Geofences" section below the existing fields:

```tsx
import GeofenceManager from '@/features/company-admin/settings/GeofenceManager';

// In the edit form/modal, after existing location fields:
{editingLocation && (
  <div className="mt-6 border-t border-neutral-200 dark:border-neutral-700 pt-6">
    <GeofenceManager
      locationId={editingLocation.id}
      companyId={editingLocation.companyId}
      locationLat={editingLocation.geoLat}
      locationLng={editingLocation.geoLng}
    />
  </div>
)}
```

The exact placement depends on the screen layout — it should be a full-width section below the location edit form fields.

- [ ] **Step 3: Read EmployeeProfileScreen.tsx to find the location dropdown**

Find the Professional tab section where `locationId` dropdown is rendered. Add a geofence dropdown after it.

- [ ] **Step 4: Add geofence dropdown to employee form**

After the Location dropdown in the Professional tab:

```tsx
import { useGeofencesForDropdown } from '@/features/company-admin/api/use-geofence-queries';

// In the component, after the location field:
const { data: geofenceData } = useGeofencesForDropdown(formState.locationId);
const geofenceOptions = (geofenceData?.data ?? []) as { id: string; name: string; radius: number; isDefault: boolean }[];

// When locationId changes, auto-select default geofence:
// In the location onChange handler, add:
const defaultGf = geofenceOptions.find(gf => gf.isDefault);
if (defaultGf) setFormField('geofenceId', defaultGf.id);

// Dropdown JSX (after Location dropdown):
<div>
  <label>Geofence</label>
  <select
    value={formState.geofenceId ?? ''}
    onChange={(e) => setFormField('geofenceId', e.target.value || undefined)}
    disabled={!formState.locationId}
  >
    <option value="">No specific geofence</option>
    {geofenceOptions.map(gf => (
      <option key={gf.id} value={gf.id}>
        {gf.name} ({gf.radius}m){gf.isDefault ? ' — Default' : ''}
      </option>
    ))}
  </select>
</div>
```

Match the exact styling pattern used by other dropdowns in the same form (likely using a custom Select component or native select with Tailwind classes).

- [ ] **Step 5: Verify compiles**

```bash
cd web-system-app && npx tsc --noEmit 2>&1 | head -10
```

- [ ] **Step 6: Commit**

```bash
git add src/features/company-admin/LocationManagementScreen.tsx src/features/company-admin/hr/EmployeeProfileScreen.tsx
git commit -m "feat(geofence): integrate GeofenceManager into location screen and add geofence dropdown to employee form"
```

---

## Task 9: Mobile — API Layer & Hooks

**Files:**
- Modify: `mobile-app/src/lib/api/company-admin.ts`
- Create: `mobile-app/src/features/company-admin/api/use-geofence-queries.ts`

- [ ] **Step 1: Read mobile company-admin API to understand patterns**

Read `mobile-app/src/lib/api/company-admin.ts` to see how existing location APIs are structured.

- [ ] **Step 2: Add geofence API functions**

Add to the `companyAdminApi` object (following existing pattern — likely arrow functions returning `client.get/post/patch/delete`):

```typescript
// Geofences
listGeofences: (locationId: string) =>
  client.get(`/company/locations/${locationId}/geofences`),

listGeofencesForDropdown: (locationId: string) =>
  client.get('/company/geofences', { params: { locationId } }),

createGeofence: (locationId: string, data: any) =>
  client.post(`/company/locations/${locationId}/geofences`, data),

updateGeofence: (locationId: string, id: string, data: any) =>
  client.patch(`/company/locations/${locationId}/geofences/${id}`, data),

deleteGeofence: (locationId: string, id: string) =>
  client.delete(`/company/locations/${locationId}/geofences/${id}`),

setDefaultGeofence: (locationId: string, id: string) =>
  client.patch(`/company/locations/${locationId}/geofences/${id}/default`),
```

- [ ] **Step 3: Create React Query hooks file**

Create `mobile-app/src/features/company-admin/api/use-geofence-queries.ts` with the same hooks as web (useGeofences, useGeofencesForDropdown, useCreateGeofence, useUpdateGeofence, useDeleteGeofence, useSetDefaultGeofence). Follow the same pattern as the web hooks but import from `@/lib/api/company-admin`.

- [ ] **Step 4: Verify compiles**

```bash
cd mobile-app && pnpm type-check 2>&1 | head -10
```

- [ ] **Step 5: Commit**

```bash
git add src/lib/api/company-admin.ts src/features/company-admin/api/use-geofence-queries.ts
git commit -m "feat(geofence): add mobile API layer and React Query hooks"
```

---

## Task 10: Mobile — Geofence Editor Screen

**Files:**
- Create: `mobile-app/src/features/company-admin/geofence-editor-screen.tsx`
- Create: `mobile-app/src/app/(app)/company/geofence-editor.tsx`

- [ ] **Step 1: Read the existing GeoFencingModal in super admin atoms.tsx for map patterns**

Read `/Users/chetan/Documents/Avyren-Technologies/Products/Mobile-ERP/mobile-app/src/features/super-admin/tenant-onboarding/atoms.tsx` (lines 842+) to understand the existing map, Places autocomplete, and draggable marker patterns.

- [ ] **Step 2: Create the geofence editor screen**

Full-screen component with:
- LinearGradient header ("Add Geofence" / "Edit Geofence")
- `GooglePlacesAutocomplete` search bar
- `MapView` from `react-native-maps` with:
  - Draggable `Marker`
  - `Circle` overlay (semi-transparent indigo fill, `colors.primary[500]` with opacity 0.15)
  - "My Location" button (uses `expo-location` to get current GPS)
- Below map (ScrollView):
  - Name TextInput
  - Lat/Lng display (read-only)
  - Radius chips: 50m, 100m, 200m, 300m, 500m, 1km
  - Address TextInput (auto-filled from Places, editable)
  - "Set as Default" toggle
  - Save button (calls create or update mutation)

**Props via route params:** `{ locationId, companyId, geofenceId?, initialLat?, initialLng? }`

- If `geofenceId` provided: edit mode — fetch existing geofence and pre-fill
- If not: create mode — center on location's address or initial lat/lng

Follow mobile CLAUDE.md patterns: `font-inter`, colors, FadeInDown, SafeAreaInsets, ConfirmModal, showSuccess/showErrorMessage.

- [ ] **Step 3: Create route file**

```typescript
// src/app/(app)/company/geofence-editor.tsx
export { GeofenceEditorScreen as default } from '@/features/company-admin/geofence-editor-screen';
```

- [ ] **Step 4: Verify compiles**

```bash
cd mobile-app && pnpm type-check 2>&1 | head -10
```

- [ ] **Step 5: Commit**

```bash
git add src/features/company-admin/geofence-editor-screen.tsx src/app/\(app\)/company/geofence-editor.tsx
git commit -m "feat(geofence): add mobile geofence editor screen with Google Maps"
```

---

## Task 11: Mobile — Integrate into Location Screen + Employee Form

**Files:**
- Modify: `mobile-app/src/features/company-admin/location-management-screen.tsx`
- Modify: `mobile-app/src/features/company-admin/hr/employee-detail-screen.tsx`

- [ ] **Step 1: Read location-management-screen.tsx to understand edit flow**

Read the full file. Find where location details are shown/edited.

- [ ] **Step 2: Add geofences section to location edit**

When viewing/editing a location, add a "Geofences" section below existing fields:
- FlatList of geofence cards: name, radius badge, default badge, active toggle
- "Add Geofence" button → navigates to geofence editor: `router.push({ pathname: '/company/geofence-editor', params: { locationId, companyId } })`
- Tap existing geofence → navigates with `geofenceId` param for editing
- Swipe to delete with ConfirmModal

- [ ] **Step 3: Add geofence dropdown to employee form**

Read `employee-detail-screen.tsx`, find the Professional tab's Location dropdown. Add a geofence dropdown after it:
- Uses `useGeofencesForDropdown(locationId)`
- Shows geofence name + radius
- Auto-selects default when location changes
- Optional (can be cleared)

- [ ] **Step 4: Verify compiles**

```bash
cd mobile-app && pnpm type-check 2>&1 | head -10
```

- [ ] **Step 5: Commit**

```bash
git add src/features/company-admin/location-management-screen.tsx src/features/company-admin/hr/employee-detail-screen.tsx
git commit -m "feat(geofence): integrate geofences into mobile location screen and employee form"
```

---

## Task 12: Cross-Codebase Consistency Review

- [ ] **Step 1: Verify API contracts match**

Check that web and mobile API calls use the exact same endpoint paths as the backend routes:
- `GET /company/locations/:locationId/geofences`
- `POST /company/locations/:locationId/geofences`
- `PATCH /company/locations/:locationId/geofences/:id`
- `DELETE /company/locations/:locationId/geofences/:id`
- `PATCH /company/locations/:locationId/geofences/:id/default`
- `GET /company/geofences?locationId=X`

- [ ] **Step 2: Verify geofence response shape used consistently**

Check that both web and mobile read the same fields: `id, name, lat, lng, radius, address, isDefault, isActive, employeeCount`.

- [ ] **Step 3: Verify employee form saves geofenceId correctly**

Check both web and mobile employee forms send `geofenceId` in the create/update payload, and the backend employee validators accept it.

- [ ] **Step 4: Verify attendance check-in fallback chain**

Read the updated `ess.controller.ts` check-in code and verify:
1. Employee's assigned geofence → 2. All location geofences → 3. Legacy location geo fields → 4. NO_LOCATION

- [ ] **Step 5: Type-check all codebases**

```bash
cd avy-erp-backend && npx tsc --noEmit
cd web-system-app && npx tsc --noEmit
cd mobile-app && pnpm type-check
```

- [ ] **Step 6: Commit any fixes**

```bash
git add -A && git commit -m "fix(geofence): address consistency issues from review"
```
