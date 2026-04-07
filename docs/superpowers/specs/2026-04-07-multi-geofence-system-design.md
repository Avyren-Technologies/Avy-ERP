# Multi-Geofence System — Design Spec

**Date:** 2026-04-07
**Status:** Approved
**Scope:** Backend (new Geofence model + CRUD + attendance integration) + Web UI (Google Maps geofence manager in location edit) + Mobile UI (geofence management in location screen) + Employee/User geofence assignment

---

## Overview

Replace the single-geofence-per-location system (fields embedded on the Location model) with a dedicated `Geofence` model supporting multiple named geofence zones per location. Add Google Maps integration with searchable places, draggable markers, and radius visualization. Auto-assign default geofences to employees and allow HR to override via dropdown on employee/user forms. Update attendance check-in to validate against the new Geofence model.

---

## Database Schema

### New Model: `Geofence`

**Prisma file:** `prisma/modules/company-admin/geofence.prisma`

```prisma
model Geofence {
  id         String   @id @default(cuid())
  locationId String
  location   Location @relation(fields: [locationId], references: [id], onDelete: Cascade)
  companyId  String
  company    Company  @relation(fields: [companyId], references: [id], onDelete: Cascade)

  name       String                  // e.g., "Main Gate", "Parking Lot", "Warehouse Entry"
  lat        Float                   // Latitude
  lng        Float                   // Longitude
  radius     Int      @default(100)  // Radius in meters
  address    String?                 // Human-readable address from Google Places

  isDefault  Boolean  @default(false) // One default per location — auto-assigned to new employees
  isActive   Boolean  @default(true)  // Soft disable without deleting

  createdAt  DateTime @default(now())
  updatedAt  DateTime @updatedAt

  employees  Employee[]              // Employees assigned to this geofence

  @@unique([locationId, name])       // No duplicate names within a location
  @@index([companyId])
  @@index([locationId])
  @@map("geofences")
}
```

### Employee Model Changes

**File:** `prisma/modules/hrms/employee.prisma`

Add:
```prisma
geofenceId    String?
geofence      Geofence? @relation(fields: [geofenceId], references: [id])
```

### Location Model (unchanged)

Keep existing `geoLat`, `geoLng`, `geoRadius`, `geoEnabled`, `geoShape`, `geoPolygon`, `geoLocationName` fields for backward compatibility. The check-in logic will prefer the new Geofence model but fall back to legacy fields if no geofences exist.

Add relation:
```prisma
geofences  Geofence[]
```

### Company Model

Add relation:
```prisma
geofences  Geofence[]
```

---

## Backend API Endpoints

### Geofence CRUD

All under `/company/locations/:locationId/geofences`. Permission: `company:configure` (or `company:create`/`company:update`/`company:delete`).

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/company/locations/:locationId/geofences` | List all geofences for a location |
| POST | `/company/locations/:locationId/geofences` | Create a new geofence |
| PATCH | `/company/locations/:locationId/geofences/:id` | Update geofence (name, lat, lng, radius, address, isActive) |
| DELETE | `/company/locations/:locationId/geofences/:id` | Delete geofence (fails if employees assigned) |
| PATCH | `/company/locations/:locationId/geofences/:id/default` | Set as default geofence for this location |

### Geofence List for Dropdowns

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/company/geofences?locationId=X` | List geofences for dropdown (simpler — no nesting, supports filtering by location) |

### Request/Response Shapes

**Create/Update Body:**
```json
{
  "name": "Main Gate",
  "lat": 12.9716,
  "lng": 77.5946,
  "radius": 200,
  "address": "42, Industrial Layout, Peenya, Bengaluru",
  "isDefault": true
}
```

**List Response:**
```json
{
  "success": true,
  "data": [
    {
      "id": "clxyz...",
      "locationId": "clxyz...",
      "name": "Main Gate",
      "lat": 12.9716,
      "lng": 77.5946,
      "radius": 200,
      "address": "42, Industrial Layout, Peenya, Bengaluru",
      "isDefault": true,
      "isActive": true,
      "employeeCount": 45,
      "createdAt": "2026-04-07T..."
    }
  ]
}
```

### Validation Rules

- `name`: required, 1-100 chars, unique within location
- `lat`: required, -90 to 90
- `lng`: required, -180 to 180
- `radius`: required, 10-10000 meters
- `address`: optional string
- `isDefault`: when set to true, unset previous default for same location (atomic)
- Delete: fails with error if any active employees have this geofence assigned. Error message lists count of assigned employees.

---

## Attendance Check-In Update

**Current logic** (in `ess.controller.ts`):
```
location.geoEnabled → haversine(userLat, userLng, location.geoLat, location.geoLng) vs location.geoRadius
```

**New logic:**
```
1. Get employee record (includes geofenceId)
2. If employee.geofenceId is set:
   a. Load that specific geofence
   b. If geofence.isActive → haversine check against geofence.lat/lng/radius
   c. Return INSIDE_GEOFENCE or OUTSIDE_GEOFENCE
3. Else if employee.locationId is set:
   a. Load ALL active geofences for that location
   b. If any geofences exist → check each, INSIDE if within ANY
   c. If no geofences exist → fall back to legacy location.geoLat/geoLng/geoRadius
4. If nothing configured → geoStatus = 'NO_LOCATION'
```

This is fully backward compatible — existing companies with legacy geo fields continue working.

---

## Employee Form Changes

### Employee Create (EmployeeProfileScreen / employee-detail-screen)

After the **Location** dropdown in the Professional tab, add a **"Geofence"** dropdown:
- Disabled until a location is selected
- When location changes: fetch geofences for that location, auto-select the default geofence
- Dropdown options: all active geofences for the selected location, formatted as "Name (Radius m)" — e.g., "Main Gate (200m)"
- Optional — can be left empty (employee validates against all location geofences during check-in)

### Employee Edit

Same dropdown, pre-populated with current `geofenceId`.

### User Management Screen

Add the same geofence dropdown per user, editable inline or via edit modal. Uses same logic: fetch geofences for user's location, show dropdown.

---

## Web UI — Geofence Manager

### Location: Inside Location Edit Screen

Add a **"Geofences"** section/tab in the existing location edit screen (company admin settings).

### Layout: Split Panel

**Left panel (300px, scrollable):**
- Header: "Geofences" + count badge + "Add Geofence" button
- List of geofence cards:
  - Name (bold)
  - Address (truncated, gray)
  - Radius badge (e.g., "200m")
  - Default badge (indigo, if isDefault)
  - Active/Inactive toggle
  - Edit/Delete action icons
  - Click → highlights on map + opens edit form
- Empty state: "No geofences configured. Add one to enable location-based attendance."

**Right panel (flex, map):**
- Google Maps (`@react-google-maps/api`) showing the location area
- Map features:
  - **Google Places Autocomplete** search bar at top of map (type to search, select result → map pans + marker moves)
  - **Draggable marker** — drag to set precise lat/lng. Coordinates update live in form.
  - **Translucent circle overlay** — shows radius, resizes when radius changes
  - All existing geofences shown as semi-transparent circles with labels
  - Selected/editing geofence highlighted in indigo, others in gray
- Below map: edit form (when adding/editing):
  - Name input
  - Lat/Lng display (read-only, set by marker/search)
  - Radius selector: chips (50m, 100m, 200m, 300m, 500m, 1km) + custom input
  - Address (auto-filled from Places, editable)
  - "Set as Default" checkbox
  - Save / Cancel buttons

### Google Maps Package

Install `@react-google-maps/api` in web-system-app. This is the standard React wrapper for Google Maps JavaScript API.

Configure via `VITE_GOOGLE_MAPS_API_KEY` environment variable. Load with `libraries: ['places']` for Places Autocomplete.

---

## Mobile UI — Geofence Management

### Location: Inside Location Management Screen

Update the existing `location-management-screen.tsx` to show geofences.

### Geofence List

When viewing/editing a location, show a **"Geofences" section**:
- FlatList of geofence cards (name, radius, default badge, active toggle)
- "Add Geofence" button (FAB or inline button)
- Swipe to delete (with ConfirmModal)

### Add/Edit Geofence Modal (Full Screen)

Full-screen pushed screen or bottom sheet:
- **Header:** "Add Geofence" / "Edit Geofence" with back button
- **Google Places search bar** at top (using existing `GooglePlacesAutocomplete` component from `react-native-google-places-autocomplete` — already used in super admin onboarding)
- **`react-native-maps` MapView:**
  - Draggable `Marker` — user drags to set position
  - `Circle` overlay showing radius (semi-transparent indigo fill)
  - "My Location" button to center on device GPS
  - Map type toggle (standard/satellite)
- **Below map:**
  - Name TextInput
  - Lat/Lng display (read-only)
  - Radius chips: 50m, 100m, 200m, 500m, 1km
  - Address (auto-filled, editable)
  - "Set as Default" toggle
  - Save button

### Existing GeoFencingModal

The existing `GeoFencingModal` in `atoms.tsx` (super admin onboarding) will remain for super admin use. The company admin geofence management is a separate, richer implementation.

---

## Auto-Assignment Logic

### During Employee Creation

When `employeeService.createEmployee()` is called with a `locationId`:
1. If `geofenceId` is explicitly provided → use it
2. If not provided → find the default geofence for that location (`isDefault: true, isActive: true`)
3. If default exists → auto-assign `geofenceId = defaultGeofence.id`
4. If no default → leave `geofenceId = null` (check-in validates against all location geofences)

### During Location Change

When employee's location is changed (update):
1. If new location has a default geofence → auto-assign it
2. If employee had a geofence from the old location → clear it (prevents stale cross-location assignment)

---

## Migration: Seed Geofences from Legacy Data

Create a one-time migration or seed script:

For each Location where `geoEnabled = true` AND `geoLat` AND `geoLng` are set:
1. Create a Geofence record:
   - `name`: location's `geoLocationName` or "Default"
   - `lat`: parseFloat(location.geoLat)
   - `lng`: parseFloat(location.geoLng)
   - `radius`: location.geoRadius (or 100 if not set)
   - `isDefault`: true
   - `locationId`: location.id
   - `companyId`: location.companyId
2. Log: "Migrated geofence for location {name}"

This runs as part of the Prisma migration or as a standalone script.

---

## Files to Create/Modify

### Backend (avy-erp-backend)

| Action | File | Purpose |
|--------|------|---------|
| Create | `prisma/modules/company-admin/geofence.prisma` | Geofence model |
| Modify | `prisma/modules/hrms/employee.prisma` | Add geofenceId field + relation |
| Modify | `prisma/modules/company-admin/locations.prisma` | Add geofences relation |
| Modify | `prisma/modules/platform/tenant.prisma` | Add geofences relation on Company |
| Create | `src/core/company-admin/geofence.service.ts` | CRUD + default management |
| Create | `src/core/company-admin/geofence.controller.ts` | Endpoint handlers |
| Create | `src/core/company-admin/geofence.validators.ts` | Zod schemas |
| Modify | `src/core/company-admin/company-admin.routes.ts` | Mount geofence routes |
| Modify | `src/modules/hr/ess/ess.controller.ts` | Update check-in to use Geofence model |
| Modify | `src/modules/hr/employee/employee.service.ts` | Auto-assign default geofence on create/location change |
| Modify | `src/modules/hr/employee/employee.validators.ts` | Add geofenceId field |
| Create | `scripts/migrate-geofences.ts` | One-time migration from legacy geo fields |

### Web (web-system-app)

| Action | File | Purpose |
|--------|------|---------|
| Install | `@react-google-maps/api` | Google Maps React wrapper |
| Add | `.env` — `VITE_GOOGLE_MAPS_API_KEY` | Google Maps API key |
| Create | `src/features/company-admin/settings/GeofenceManager.tsx` | Split-panel geofence manager (list + map) |
| Modify | Location edit screen | Add Geofences section using GeofenceManager |
| Create | `src/features/company-admin/api/use-geofence-queries.ts` | React Query hooks for geofence CRUD |
| Modify | `src/lib/api/company-admin.ts` | Add geofence API functions |
| Modify | Employee form (EmployeeProfileScreen.tsx) | Add geofence dropdown after location |
| Modify | User management screen | Add geofence dropdown |

### Mobile (mobile-app)

| Action | File | Purpose |
|--------|------|---------|
| Create | `src/features/company-admin/geofence-editor-screen.tsx` | Full-screen geofence add/edit with map |
| Modify | `src/features/company-admin/location-management-screen.tsx` | Add geofences list section |
| Create | `src/features/company-admin/api/use-geofence-queries.ts` | React Query hooks |
| Modify | `src/lib/api/company-admin.ts` | Add geofence API functions |
| Modify | Employee form (employee-detail-screen.tsx) | Add geofence dropdown |

---

## Packages

### Web (new)
- `@react-google-maps/api` — Google Maps React components (Map, Marker, Circle, Autocomplete)

### Mobile (already installed)
- `react-native-maps` — MapView, Marker, Circle
- `react-native-google-places-autocomplete` — Places search
- `expo-location` — Device GPS

### Backend
- No new packages needed

---

## Environment Variables

### Web
```
VITE_GOOGLE_MAPS_API_KEY=your-api-key-here
```

### Mobile (already exists)
```
GOOGLE_MAPS_API_KEY=your-api-key-here
```

---

## Constraints

- Radius: 10m minimum, 10,000m (10km) maximum
- Max geofences per location: 20 (prevent abuse)
- Delete protection: cannot delete a geofence with assigned employees
- One default per location: setting a new default atomically unsets the previous one
- Freeform/polygon: `geoPolygon` field exists but is NOT implemented in this phase — radius-based circles only
