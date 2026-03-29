# Avy ERP — Monorepo Development Guide

This is a multi-tenant SaaS ERP platform with 3 submodules:
- `avy-erp-backend/` — Node.js/Express API
- `web-system-app/` — React (Vite) web app
- `mobile-app/` — React Native (Expo) mobile app

## Architecture: Multi-Tenant SaaS

- **Platform DB** (shared): Users, Companies, Tenants, Roles, Subscriptions, SupportTickets
- **Tenant DBs** (per-tenant): HR, Production, Inventory, etc.
- **3 user roles**: `SUPER_ADMIN` (platform), `COMPANY_ADMIN` (tenant), `user` (employee/manager)
- **RBAC**: Dynamic permissions via `navigation-manifest.ts` + `permissions.ts`

---

## Mandatory Rules (ALL codebases)

### Imports
- **ALWAYS** use path aliases (`@/` prefix). Never relative imports.
- Backend: `@/shared/utils`, `@/core/auth`, `@/modules/hr/`
- Web: `@/features/company-admin`, `@/lib/api/auth`
- Mobile: `@/components/ui`, `@/features/auth/use-auth-store`

### API Response Envelope
Every backend response follows this structure. Frontends MUST unwrap correctly:
```typescript
// Success: { success: true, data: T, message?: string }
// Paginated: { success: true, data: T[], meta: { page, limit, total, totalPages } }
// Frontend extraction: const result = apiResponse?.data;  // NOT apiResponse?.ticket
```

### Error Handling
- Backend: Throw `ApiError.notFound()`, `ApiError.badRequest()` etc. Never raw `throw new Error()`
- Web: Use `showApiError(err)` from `@/lib/toast` in mutation `onError` callbacks
- Mobile: **NEVER use `Alert.alert()`** — use `ConfirmModal` from `@/components/ui/confirm-modal`

### TypeScript
- All 3 codebases use strict mode. Fix all TS errors before committing.
- Backend has `exactOptionalPropertyTypes: true` — optional fields need explicit handling

---

## Backend (avy-erp-backend)

### Commands
```bash
pnpm dev              # Start dev server (ts-node-dev)
pnpm build            # Compile TypeScript
pnpm test             # Jest
pnpm lint             # ESLint
pnpm db:generate      # Prisma generate
pnpm db:migrate       # Prisma migrate dev
pnpm db:studio        # Prisma Studio GUI
```

### File Patterns
| Type | Naming | Location |
|------|--------|----------|
| Service | `[name].service.ts` | `src/core/[module]/` or `src/modules/[module]/` |
| Controller | `[name].controller.ts` | Same folder as service |
| Routes | `[name].routes.ts` | Same folder |
| Validators | `[name].validators.ts` | Same folder (Zod schemas) |
| Types | `[name].types.ts` | Same folder or `src/shared/types/` |
| Constants | `[name].ts` | `src/shared/constants/` |

### Controller Pattern (MUST follow)
```typescript
methodName = asyncHandler(async (req: Request, res: Response) => {
  const parsed = schema.safeParse(req.body);
  if (!parsed.success) throw ApiError.badRequest(parsed.error.errors.map(e => e.message).join(', '));
  const result = await service.method(parsed.data);
  res.json(createSuccessResponse(result, 'Action completed'));
});
```

### Route Mounting Order (DO NOT change)
1. `/health` (no auth)
2. `/auth` (no tenant)
3. `/platform/*` (super-admin, no tenant)
4. Blanket `tenantMiddleware()`
5. `/modules/catalogue` (auth, no tenant)
6. `/tenants/:tenantId/*` (tenant-scoped)
7. Auth + tenant required modules: `/hr`, `/production`, `/inventory`, etc.
8. `/rbac`, `/feature-toggles`, `/company/*`, `/company/support/*`

### Permission System (Dynamic RBAC)
- **Permissions**: `module:action` format (e.g., `hr:read`, `company:configure`)
- **Inheritance**: `configure > approve > export > create = update = delete > read`
  - Having `hr:configure` automatically grants `hr:read`, `hr:create`, etc.
- **Module suppression**: Unsubscribed modules auto-suppress all related permissions
- **Wildcards**: `*` (all), `hr:*` (all HR actions)
- **Navigation manifest**: `src/shared/constants/navigation-manifest.ts` — single source of truth for all sidebar items
  - **Adding a new page**: Add one entry to `NAVIGATION_MANIFEST` array. Both frontends auto-render.
- **Reference roles**: 14 templates in `permissions.ts` (Employee, Manager, HR Personnel, etc.)

### Logging
- Use `logger` from `@/config/logger` (Winston). Never `console.log()` in production code.

### Caching
- Redis with 30-minute TTL for user auth/permissions
- Use `createUserCacheKey()`, `createTenantCacheKey()` helpers from `@/shared/utils`
- Cache invalidation: always invalidate on role/permission changes

### Socket.io
- JWT-authenticated connections (`socket.handshake.auth.token`)
- Room authorization: company rooms restricted to own company, admin room restricted to SUPER_ADMIN
- Events: `ticket:message`, `ticket:status-changed`, `ticket:new`, `ticket:resolved`, `ticket:updated`

---

## Web App (web-system-app)

### Commands
```bash
pnpm dev              # Vite dev server
pnpm build            # TypeScript + Vite build
pnpm lint             # ESLint
pnpm test             # Vitest
```

### Key Patterns
- **Styling**: Tailwind CSS with custom color palette (primary=indigo, accent=violet)
- **State**: Zustand (`useAuthStore`) for auth, React Query for server state
- **Forms**: React Hook Form or inline state
- **Toast**: `showSuccess()`, `showApiError()` from `@/lib/toast`
- **Route guards**: `<RequireAuth>`, `<RequireRole>`, `<RequirePermission>`
- **Sidebar**: Dynamic from navigation manifest API (`GET /rbac/navigation-manifest`)
- **Button-level permissions**: `useCanPerform('hr:create')` hook from `@/hooks/useCanPerform`
- **Permission auto-refresh**: `usePermissionRefresh()` in `DashboardLayout` — no logout needed after role changes

### React Query Key Pattern
```typescript
companyAdminKeys = {
  all: ['company-admin'],
  profile: () => [...all, 'profile'],
  supportTickets: (params?) => params ? [...all, 'support-tickets', params] : [...all, 'support-tickets'],
  // IMPORTANT: Key factories without params must return prefix-only (no trailing undefined)
}
```

### API Client
- Axios client with interceptors for auth token + token refresh
- `.then(r => r.data)` on all API calls — strips axios wrapper, returns API envelope
- In components: `data?.data` to unwrap the `{ success, data }` envelope

---

## Mobile App (mobile-app)

### Commands
```bash
pnpm start            # Expo dev server
pnpm ios              # Run on iOS
pnpm android          # Run on Android
pnpm lint             # ESLint
pnpm type-check       # TypeScript validation
pnpm test             # Jest
```

### Key Patterns
- **Expo SDK 54**, React Native 0.81.5, Expo Router 6 (file-based routing)
- **Styling**: `StyleSheet.create()` for layouts + NativeWind `className` for text
- **Font**: `font-inter` on ALL `<Text>` components
- **Colors**: `@/components/ui/colors` — primary (indigo), accent (violet), gradient (start/mid/end)
- **Animations**: `FadeInDown`, `FadeInUp` from `react-native-reanimated`
- **Safe area**: `useSafeAreaInsets()` for padding
- **Headers**: `LinearGradient` with `colors.gradient.start/mid/end`
- **NEVER use `Alert`**: Use `ConfirmModal` from `@/components/ui/confirm-modal`
- **Bottom sheets**: `@gorhom/bottom-sheet` for modals/action sheets
- **Sidebar**: Dynamic from navigation manifest (same API as web)
- **Permission refresh**: `usePermissionRefresh()` in `AppSidebar`

### File Patterns
- Feature screens: named exports (`export function MyScreen()`)
- Route files: re-export as default (`export { MyScreen as default } from '@/features/...'`)
- Routes in `src/app/(app)/` — file-based routing
- Features in `src/features/[feature-name]/`
- Reusable UI in `src/components/ui/` — exported from `index.tsx`

### API Client
- Axios with response interceptor that does `response.data` (strips axios wrapper)
- `companyAdminApi` methods return the API envelope directly (no additional `.then`)
- In components: `data?.data` to unwrap

### SidebarSection Interface
```typescript
interface SidebarSection {
  title?: string;
  moduleSeparator?: string;  // Renders styled divider with module name
  items: SidebarNavItem[];
}
// Icon types: 'dashboard' | 'companies' | 'billing' | 'users' | 'reports' | 'settings' | 'support' | 'logout' | 'more' | 'audit' | 'onboarding'
```

---

## Adding a New Feature (Checklist)

### New Backend Endpoint
1. Create `[name].validators.ts` with Zod schemas
2. Create `[name].service.ts` with business logic (class-based)
3. Create `[name].controller.ts` wrapping service with `asyncHandler`
4. Create `[name].routes.ts` with `requirePermissions()` guards
5. Mount in `routes.ts` in the correct section
6. If new permission module needed: add to `PERMISSION_MODULES` in `permissions.ts`

### New Sidebar Page
1. Add entry to `NAVIGATION_MANIFEST` in backend `navigation-manifest.ts`
2. Create screen component in `src/features/[module]/`
3. Create route file (web: in `App.tsx`, mobile: in `src/app/(app)/`)
4. Both sidebars auto-render from manifest — NO frontend sidebar config needed

### New Permission Module
1. Add to `PERMISSION_MODULES` in `permissions.ts`
2. Add to `MODULE_TO_PERMISSION_MAP` if tied to a subscription module
3. Reference roles auto-update if using module wildcards

---

## Support Ticket System
- Company admin: `POST/GET /company/support/tickets`, chat via `/tickets/:id/messages`
- Super admin: `GET /platform/support/tickets`, approve/reject module changes
- Real-time: Socket.io with JWT auth, rooms per ticket/company/admin
- Module change flow: one-time billing → create ticket → admin approves → modules updated atomically

## Module Management
- `GET /modules/catalogue` — returns modules with per-location breakdown + billing type
- `POST /company/locations/:id/modules` — add modules (billing gate: monthly/annual only)
- `DELETE /company/locations/:id/modules/:moduleId` — remove (dependency check + masters protection)
- One-time billing → redirected to support ticket
