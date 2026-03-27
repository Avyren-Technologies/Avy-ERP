# Module CRUD & Support Ticket System — Design Spec

**Date:** 2026-03-27
**Status:** Approved
**Scope:** Backend + Web + Mobile

---

## 1. Overview

Three interconnected subsystems:

1. **Module CRUD for Company Admin** — add/remove modules on locations (billing-gated)
2. **Support Ticket / Chat System** — messaging between tenants and super-admin
3. **Super Admin Support Dashboard** — manage incoming tickets, approve/reject module requests

Build order: Schema → Backend → Web → Mobile

---

## 2. Billing-Gated Module Management

### Rules

The billing gate uses `Location.billingType` (a string field, lowercase values). When `Company.locationConfig === "common"`, use `Company.billingType` as the source of truth.

| Location/Company billingType | Behavior |
|---|---|
| `"monthly"` / `"annual"` | Company Admin can directly add/remove modules via API |
| Any other value (e.g., `"one_time"`) OR `Location.oneTimeLicenseFee > 0` | Company Admin must raise a support ticket; Super Admin approves/rejects |

### locationConfig handling

- **`"per-location"`** (default): Module CRUD operates on individual `Location.moduleIds`. Each location is independent.
- **`"common"`**: Module CRUD operates on `Company.selectedModuleIds`. When modules are added/removed, the change applies to ALL locations (all locations' `moduleIds` are synced).

### Dependency Resolution (server-side)

Adding a module auto-adds its dependencies. Removing a module is blocked if other active modules depend on it.

Dependencies (from `MODULE_CATALOGUE`):
- `masters` → no deps (always required, cannot be removed)
- `security` → `[masters]`
- `hr` → `[security]`
- `production` → `[machine-maintenance, masters]`
- `machine-maintenance` → `[masters]`
- `inventory` → `[masters]`
- `vendor` → `[inventory, masters]`
- `sales` → `[finance, masters]`
- `finance` → `[masters]`
- `visitor` → `[security]`

### Backend Endpoints

Added to `company-admin.routes.ts`. Permission: `module:manage` (new permission added to COMPANY_ADMIN default role).

```
POST   /company/locations/:locationId/modules           → addModules
DELETE /company/locations/:locationId/modules/:moduleId  → removeModule
```

**`POST /company/locations/:locationId/modules`**
- Body: `{ moduleIds: string[] }`
- Validates: location belongs to company, modules exist in catalogue
- Checks billing type → 403 if one-time (with message: "One-time billing tenants must request module changes via support")
- Resolves dependencies → adds missing deps automatically
- If `locationConfig === "common"`: updates ALL locations + `Company.selectedModuleIds`
- If `locationConfig === "per-location"`: updates target `Location.moduleIds` + re-aggregates `Company.selectedModuleIds`
- Audit log: `module:add` on `location` entity
- Returns: `{ location, autoAddedDeps: string[], billingImpact: { addedModules: { id, name, price }[], monthlyDelta: number } }`

**`DELETE /company/locations/:locationId/modules/:moduleId`**
- Validates: location belongs to company, module is currently active
- Checks billing type → 403 if one-time
- Checks dependents → 409 Conflict if other active modules depend on this one (returns `{ blockingModules: { id, name }[] }`)
- Cannot remove `masters` → 400
- Same locationConfig handling as add
- Audit log: `module:remove` on `location` entity
- Returns: updated location

**Idempotency:** Adding a module that already exists is a no-op (200 success, no duplicate). Removing a module that isn't active returns 404.

**Validators** (`company-admin.validators.ts`):

```typescript
const addModulesSchema = z.object({
    moduleIds: z.array(z.string().min(1)).min(1).max(10),
});
```

**Service methods** (`company-admin.service.ts`):

```typescript
async addModulesToLocation(companyId: string, locationId: string, moduleIds: string[]): Promise<AddModulesResult>
async removeModuleFromLocation(companyId: string, locationId: string, moduleId: string): Promise<Location>
```

Both methods use a transaction to atomically update Location + Company. Company re-aggregation is incremental: on add, union with existing set; on remove, check if any other location still uses the module before removing from company set.

---

## 3. Support Ticket / Chat System

### 3.1 Database Schema

```prisma
enum TicketCategory {
  MODULE_CHANGE
  BILLING
  TECHNICAL
  GENERAL
}

enum TicketPriority {
  LOW
  NORMAL
  HIGH
  URGENT
}

enum TicketStatus {
  OPEN
  IN_PROGRESS
  WAITING_ON_CUSTOMER
  RESOLVED
  CLOSED
}

enum SenderRole {
  COMPANY_ADMIN
  SUPER_ADMIN
  SYSTEM
}

model SupportTicket {
  id              String         @id @default(cuid())
  tenantId        String
  companyId       String
  companyName     String         // Denormalized for super-admin list display
  createdByUserId String
  createdByName   String         // Denormalized
  subject         String
  category        TicketCategory @default(GENERAL)
  priority        TicketPriority @default(NORMAL)
  status          TicketStatus   @default(OPEN)
  assignedToUserId String?
  metadata        Json?          // For MODULE_CHANGE: { type: 'add'|'remove', locationId, locationName, moduleId, moduleName }
  resolvedAt      DateTime?
  closedAt        DateTime?
  createdAt       DateTime       @default(now())
  updatedAt       DateTime       @updatedAt

  // Relations
  company  Company          @relation(fields: [companyId], references: [id], onDelete: Cascade)
  messages SupportMessage[]

  @@index([tenantId])
  @@index([companyId])
  @@index([status])
  @@index([category])
  @@map("support_tickets")
}

model SupportMessage {
  id              String     @id @default(cuid())
  ticketId        String
  senderUserId    String?    // null for system messages
  senderName      String     // "System" for system messages
  senderRole      SenderRole @default(COMPANY_ADMIN)
  body            String
  isSystemMessage Boolean    @default(false)
  createdAt       DateTime   @default(now())

  ticket SupportTicket @relation(fields: [ticketId], references: [id], onDelete: Cascade)

  @@index([ticketId])
  @@map("support_messages")
}
```

**Note:** Add `supportTickets SupportTicket[]` back-relation to the `Company` model.

### 3.2 Backend Endpoints

**Company Admin** — `src/core/support/` (new module)

Routes mounted at `/company/support/*` (requires auth + tenant middleware, inherits from `/company` prefix). Permission: `support:read` for GET, `support:write` for POST/PATCH.

```
POST   /tickets                    → createTicket
GET    /tickets                    → listMyTickets (paginated, filterable)
GET    /tickets/:id                → getTicket (with messages)
POST   /tickets/:id/messages       → sendMessage
PATCH  /tickets/:id/close          → closeTicket
```

**Super Admin** — same module, separate router export

Routes mounted at `/platform/support/*` (requires `platform:admin` permission).

```
GET    /tickets                    → listAllTickets (paginated, filterable by company, status, category)
GET    /tickets/:id                → getTicket (with messages + company context via relation)
POST   /tickets/:id/messages       → replyToTicket
PATCH  /tickets/:id/status         → updateTicketStatus
POST   /tickets/:id/approve-module → approveModuleChange
POST   /tickets/:id/reject-module  → rejectModuleChange
GET    /stats                      → getTicketStats (counts by status)
```

**Route file exports** two routers: `supportCompanyRoutes` and `supportPlatformRoutes`, mounted separately in `routes.ts`.

### 3.3 Status Transition Rules

| From | Allowed To |
|---|---|
| `OPEN` | `IN_PROGRESS`, `WAITING_ON_CUSTOMER`, `RESOLVED`, `CLOSED` |
| `IN_PROGRESS` | `WAITING_ON_CUSTOMER`, `RESOLVED`, `CLOSED` |
| `WAITING_ON_CUSTOMER` | `OPEN`, `IN_PROGRESS`, `RESOLVED`, `CLOSED` |
| `RESOLVED` | `CLOSED` (only) |
| `CLOSED` | (no transitions — terminal state) |

Company Admin can only: close their own tickets (any non-CLOSED status → CLOSED).
Super Admin can: transition to any allowed status per the table above.

`resolvedAt` is set when status transitions to `RESOLVED`.
`closedAt` is set when status transitions to `CLOSED`.

### 3.4 Module Change Request Flow

**Creating a module change request:**

1. Company Admin (one-time billing) clicks "Request" on a module
2. Frontend calls `POST /company/support/tickets` with:
   ```json
   {
     "subject": "Module Change Request",
     "category": "MODULE_CHANGE",
     "message": "I would like to add HR Management module to Bengaluru HQ location.",
     "metadata": {
       "type": "add",
       "locationId": "cmn2pczq60004...",
       "locationName": "Bengaluru HQ",
       "moduleId": "hr",
       "moduleName": "HR Management"
     }
   }
   ```
3. Backend creates `SupportTicket` + initial `SupportMessage` (from user) + system message summarizing the request

**Duplicate prevention:** Before creating a MODULE_CHANGE ticket, the service checks for existing non-resolved tickets with matching `metadata.locationId + metadata.moduleId + metadata.type`. If found, returns 409 Conflict with the existing ticket ID.

**Approving:**

1. Super Admin calls `POST /platform/support/tickets/:id/approve-module`
2. Backend:
   - Checks ticket status is NOT `RESOLVED` or `CLOSED` → 409 if already resolved
   - Reads `metadata` from ticket
   - If `type === 'add'`: adds moduleId (+ deps) to Location.moduleIds (handles locationConfig)
   - If `type === 'remove'`: removes moduleId from Location.moduleIds (checks dependents)
   - Updates Company.selectedModuleIds (re-aggregate)
   - Creates system message: "Module change approved: HR Management added to Bengaluru HQ"
   - Sets ticket status to `RESOLVED`, sets `resolvedAt`
   - Audit log entry

**Rejecting:**

1. Super Admin calls `POST /platform/support/tickets/:id/reject-module` with `{ reason: "..." }`
2. Backend:
   - Checks ticket status is NOT `RESOLVED` or `CLOSED` → 409 if already resolved
   - Creates system message: "Module change rejected: {reason}"
   - Sets ticket status to `RESOLVED`, sets `resolvedAt`

### 3.5 Validators

```typescript
const moduleChangeMetadataSchema = z.object({
    type: z.enum(['add', 'remove']),
    locationId: z.string().min(1),
    locationName: z.string().min(1),
    moduleId: z.string().min(1),
    moduleName: z.string().min(1),
});

const createTicketSchema = z.object({
    subject: z.string().min(3).max(200),
    category: z.enum(['MODULE_CHANGE', 'BILLING', 'TECHNICAL', 'GENERAL']).default('GENERAL'),
    priority: z.enum(['LOW', 'NORMAL', 'HIGH', 'URGENT']).optional(),
    message: z.string().min(1).max(5000),
    metadata: z.record(z.unknown()).optional(),
}).refine(
    (data) => {
        if (data.category === 'MODULE_CHANGE') {
            return moduleChangeMetadataSchema.safeParse(data.metadata).success;
        }
        return true;
    },
    { message: 'MODULE_CHANGE tickets require valid metadata (type, locationId, locationName, moduleId, moduleName)' }
);

const sendMessageSchema = z.object({
    body: z.string().min(1).max(5000),
});

const updateStatusSchema = z.object({
    status: z.enum(['OPEN', 'IN_PROGRESS', 'WAITING_ON_CUSTOMER', 'RESOLVED', 'CLOSED']),
});

const rejectModuleSchema = z.object({
    reason: z.string().min(1).max(1000),
});
```

### 3.6 Service Layer

**File:** `src/core/support/support.service.ts`

Key methods:
- `createTicket(companyId, userId, data)` — creates ticket + first message + system message (if MODULE_CHANGE). Checks for duplicate MODULE_CHANGE tickets.
- `listTickets(filters)` — paginated, scoped by companyId (company-admin) or all (super-admin)
- `getTicket(ticketId, companyId?)` — ticket + messages (all messages, no pagination — tickets are expected to be short conversations), scoped validation
- `sendMessage(ticketId, userId, role, body)` — append message, update ticket.updatedAt. Validates ticket is not CLOSED.
- `updateStatus(ticketId, newStatus)` — validates transition per rules table, sets resolvedAt/closedAt as appropriate
- `approveModuleChange(ticketId, approverUserId)` — atomic: validate not already resolved, update location modules + resolve ticket
- `rejectModuleChange(ticketId, approverUserId, reason)` — validate not already resolved, resolve ticket with rejection message
- `getStats(tenantId?)` — counts grouped by status

### 3.7 Chat Polling

Phase 1 uses polling: ticket detail queries use `refetchInterval: 10000` (10s) when the chat view is open. Real-time via WebSocket/SSE is deferred to a future phase.

---

## 4. Frontend — Company Admin

### 4.1 Module Management on Company Profile

**Location:** Both `CompanyProfileScreen.tsx` (web) and `company-profile-screen.tsx` (mobile)

Transform the read-only "Active Modules" section:

- Each location expands to show all catalogue modules as toggle cards
- Active modules: toggle ON (green), with remove button
- Inactive modules: toggle OFF (muted), with add button
- Dependency badges shown on each module card
- **Monthly/Annual tenants:** toggles directly call add/remove API. On add, show confirmation with billing impact (price delta) before committing.
- **One-time tenants:** toggles replaced with "Request Add" / "Request Remove" buttons that navigate to Help & Support with pre-filled ticket

### 4.2 Help & Support Screen

**Web route:** `/app/help` (replace existing `HelpSupportScreen.tsx`)
**Mobile routes:**
- `src/app/(app)/support.tsx` — Help & Support screen (ticket list + help center tabs)
- `src/app/(app)/support/ticket/[id].tsx` — Ticket chat view

**Layout — Two tabs:**

**Tab: My Tickets**
- List view: ticket cards with subject, category chip, status badge, last message preview, timestamp
- Filter bar: status dropdown, category dropdown
- Empty state: "No tickets yet" with create button
- FAB / "New Ticket" button → create ticket form (subject, category, message)
- Tap ticket → chat view
- Unread indicator: tickets with messages after user's last view

**Tab: Help Center**
- Keep existing Quick Start Guide + FAQ content (web already has this)
- Mobile: port the web FAQ content

**Chat View (ticket detail):**
- Header: ticket subject, status badge, category chip
- For MODULE_CHANGE tickets: request summary card at top (module name, location, status)
- Message list: chat bubbles (refetchInterval: 10s while open)
  - Right-aligned (blue/primary): own messages
  - Left-aligned (neutral): super-admin messages
  - Center (muted, italic): system messages
- Input bar at bottom: text input + send button (disabled if ticket is CLOSED)
- Close ticket button (in header menu)

### 4.3 API Hooks

**New query keys** added to `companyAdminKeys`:
```typescript
supportTickets: (params?) => [...all, 'support-tickets', params],
supportTicket: (id) => [...all, 'support-ticket', id],
```

**New queries:**
- `useSupportTickets(params?)` — list tickets
- `useSupportTicket(id)` — single ticket with messages (refetchInterval: 10s)

**New mutations:**
- `useCreateSupportTicket()` — invalidates supportTickets
- `useSendSupportMessage()` — invalidates supportTicket(id)
- `useCloseSupportTicket()` — invalidates both

**New API functions** in `company-admin.ts`:
```typescript
createSupportTicket: (data) => client.post('/company/support/tickets', data)
listSupportTickets: (params) => client.get('/company/support/tickets', { params })
getSupportTicket: (id) => client.get(`/company/support/tickets/${id}`)
sendSupportMessage: (id, data) => client.post(`/company/support/tickets/${id}/messages`, data)
closeSupportTicket: (id) => client.patch(`/company/support/tickets/${id}/close`)
```

### 4.4 Module CRUD API Hooks

**New mutations:**
- `useAddLocationModules()` — `POST /company/locations/:locationId/modules`
- `useRemoveLocationModule()` — `DELETE /company/locations/:locationId/modules/:moduleId`
- Both invalidate: `locations`, `profile`, `moduleCatalogue`

---

## 5. Frontend — Super Admin

### 5.1 Support Dashboard Screen

**Web route:** `/app/support` (new)
**Mobile routes:**
- `src/app/(app)/support.tsx` — Support dashboard (reused path, role-aware)
- `src/app/(app)/support/ticket/[id].tsx` — Ticket chat view (shared)
**Sidebar:** Add "Support" item with badge count

**Layout:**

**Stats bar:** 4 stat cards — Open, In Progress, Waiting, Resolved Today

**Ticket list:**
- Table/card layout with columns: Subject, Company, Category, Priority, Status, Created, Last Activity
- Filters: status, category, priority, company search, date range
- Module change tickets: highlighted with special icon/badge
- Pagination

**Ticket detail (chat view):**
- Same chat bubble UI as company admin
- Additional controls:
  - Status dropdown (can change per transition rules)
  - For MODULE_CHANGE tickets:
    - Request summary card with module details + location info
    - "Approve" button (green) — calls approve-module endpoint
    - "Reject" button (red) — opens reason input, calls reject-module endpoint
  - Company context card: tenant name, billing type, plan (loaded via ticket's company relation)

### 5.2 API Hooks

**New file:** `use-support-queries.ts` + `use-support-mutations.ts` in super-admin API folder

**Query keys:**
```typescript
supportKeys = {
    all: ['platform-support'],
    tickets: (params?) => [...all, 'tickets', params],
    ticket: (id) => [...all, 'ticket', id],
    stats: () => [...all, 'stats'],
}
```

**Queries:**
- `usePlatformSupportTickets(params?)` — all tickets
- `usePlatformSupportTicket(id)` — ticket with messages + company context
- `usePlatformSupportStats()` — badge counts (refetchInterval: 30s)

**Mutations:**
- `useReplySupportTicket()` — send message, invalidate ticket
- `useUpdateTicketStatus()` — change status, invalidate tickets + ticket
- `useApproveModuleChange()` — approve, invalidate ticket + tickets
- `useRejectModuleChange()` — reject, invalidate ticket + tickets

**New API functions** in platform API layer:
```typescript
listSupportTickets: (params) => client.get('/platform/support/tickets', { params })
getSupportTicket: (id) => client.get(`/platform/support/tickets/${id}`)
replySupportTicket: (id, data) => client.post(`/platform/support/tickets/${id}/messages`, data)
updateTicketStatus: (id, data) => client.patch(`/platform/support/tickets/${id}/status`, data)
approveModuleChange: (id) => client.post(`/platform/support/tickets/${id}/approve-module`)
rejectModuleChange: (id, data) => client.post(`/platform/support/tickets/${id}/reject-module`, data)
getSupportStats: () => client.get('/platform/support/stats')
```

### 5.3 Navigation Changes

**Web sidebar (`Sidebar.tsx`):**
- Super Admin: add "Support" item under Management section (with badge from stats query)
- Company Admin: existing "Help & Support" in bottom nav routes to new screen

**Mobile sidebar (`_layout.tsx`):**
- Super Admin: wire "Support" item (currently empty handler) → new support screen
- Company Admin: add "Help & Support" item → new support screen

### 5.4 Sidebar Badge

Super Admin sidebar "Support" item shows badge count = `stats.open + stats.inProgress` (from `usePlatformSupportStats()`).
Company Admin sidebar "Help & Support" shows no badge (MVP — can add unread count later).

---

## 6. File Structure

### Backend (new files)
```
src/core/support/
├── support.routes.ts        # Exports supportCompanyRoutes + supportPlatformRoutes
├── support.controller.ts    # Request handlers
├── support.service.ts       # Business logic
└── support.validators.ts    # Zod schemas
```

### Web App (new/modified files)
```
src/features/support/
├── HelpSupportScreen.tsx          # Company Admin — replaces existing
├── TicketChatScreen.tsx            # Shared chat view
├── components/
│   ├── TicketList.tsx
│   ├── TicketCard.tsx
│   ├── ChatBubble.tsx
│   ├── CreateTicketModal.tsx
│   ├── ModuleRequestCard.tsx
│   └── TicketFilters.tsx
└── api/
    ├── use-support-queries.ts
    └── use-support-mutations.ts

src/features/super-admin/support/
├── SupportDashboardScreen.tsx     # Super Admin support page
└── components/
    ├── TicketStatsBar.tsx
    ├── ModuleApprovalCard.tsx
    └── CompanyContextCard.tsx
```

### Mobile App (new/modified files)
```
src/app/(app)/
├── support.tsx                     # Role-aware: company-admin → help, super-admin → dashboard
└── support/
    └── ticket/
        └── [id].tsx                # Ticket chat view

src/features/support/
├── help-support-screen.tsx         # Company Admin
├── ticket-chat-screen.tsx          # Shared chat view
├── components/
│   ├── ticket-list.tsx
│   ├── ticket-card.tsx
│   ├── chat-bubble.tsx
│   ├── create-ticket-sheet.tsx     # Bottom sheet form
│   └── module-request-card.tsx
└── api/
    ├── use-support-queries.ts
    └── use-support-mutations.ts

src/features/super-admin/support/
├── support-dashboard-screen.tsx    # Super Admin
└── components/
    ├── ticket-stats-bar.tsx
    ├── module-approval-card.tsx
    └── company-context-card.tsx
```

### Modified files
- `prisma/schema.prisma` — new models + enums + Company back-relation
- `src/app/routes.ts` — mount supportCompanyRoutes + supportPlatformRoutes
- `src/core/company-admin/company-admin.routes.ts` — module CRUD endpoints
- `src/core/company-admin/company-admin.service.ts` — module add/remove methods
- `src/core/company-admin/company-admin.validators.ts` — module schemas
- Web: `CompanyProfileScreen.tsx` (company-admin) — interactive module management
- Mobile: `company-profile-screen.tsx` (company-admin) — interactive module management
- Web: `Sidebar.tsx` — navigation updates + badge
- Mobile: `_layout.tsx` — navigation updates
- Both: `company-admin.ts` API service — new endpoints (module CRUD + support)
- Both: `use-company-admin-queries.ts` — new query keys
- Both: `use-company-admin-mutations.ts` — new mutations
