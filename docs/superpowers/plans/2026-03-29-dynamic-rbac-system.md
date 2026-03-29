# Dynamic RBAC & Permission System Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Transform the static, hardcoded permission system into a fully dynamic RBAC system where sidebar navigation, route guards, and button-level actions are all driven by a server-side navigation manifest and permission inheritance — so adding a new page or changing permissions never requires a code deployment.

**Architecture:** Three layers: (1) Backend serves a **navigation manifest** (sidebar items + required permissions + module dependencies) and implements **permission inheritance** (configure > approve > export > CRUD > read) + **module-aware suppression** (unsubscribed modules auto-suppress permissions). (2) Both frontends consume the manifest to dynamically render sidebars and use a `useCanPerform(permission)` hook for button-level control. (3) The RBAC management screen shows a full permission matrix aligned with navigation items grouped by module.

**Tech Stack:** Node.js/Express backend, React (web), React Native/Expo (mobile), Zustand, React Query, Prisma, Redis

---

## Scope: 3 Phases

This plan covers **Phase 1 only** — the foundational backend changes and frontend consumption. Phases 2-3 are follow-ups.

| Phase | What | Status |
|-------|------|--------|
| **Phase 1** | Backend navigation manifest API + permission inheritance + module suppression + frontend dynamic sidebar + `useCanPerform` hook + employee sidebar fix | **This plan** |
| Phase 2 | RBAC management screen enhancement (navigation-aware permission matrix) | Follow-up |
| Phase 3 | Audit logging for permission changes, permission change notifications | Follow-up |

---

## File Structure

### Backend (avy-erp-backend)
| File | Action | Purpose |
|------|--------|---------|
| `src/shared/constants/permissions.ts` | Modify | Add permission inheritance chain, module-to-subscription mapping |
| `src/shared/constants/navigation-manifest.ts` | Create | Central navigation registry — all sidebar items, permissions, module groups |
| `src/core/rbac/rbac.service.ts` | Modify | Add `getNavigationManifest()`, `resolveEffectivePermissions()` |
| `src/core/rbac/rbac.controller.ts` | Modify | Add `getNavigationManifest` handler |
| `src/core/rbac/rbac.routes.ts` | Modify | Add `GET /rbac/navigation-manifest` route |
| `src/middleware/auth.middleware.ts` | Modify | Apply permission inheritance + module suppression when resolving permissions |

### Web (web-system-app)
| File | Action | Purpose |
|------|--------|---------|
| `src/hooks/useCanPerform.ts` | Create | Button-level permission hook |
| `src/hooks/useNavigationManifest.ts` | Create | Fetch + cache navigation manifest |
| `src/layouts/Sidebar.tsx` | Modify | Render from manifest instead of hardcoded NAV_CONFIG |
| `src/layouts/DashboardLayout.tsx` | Modify | Pass manifest to sidebar |
| `src/features/company-admin/api/use-company-admin-queries.ts` | Modify | Add navigation manifest query |

### Mobile (mobile-app)
| File | Action | Purpose |
|------|--------|---------|
| `src/hooks/use-can-perform.ts` | Create | Button-level permission hook |
| `src/hooks/use-navigation-manifest.ts` | Create | Fetch + cache navigation manifest |
| `src/app/(app)/_layout.tsx` | Modify | Render sidebar from manifest |
| `src/features/company-admin/api/use-company-admin-queries.ts` | Modify | Add navigation manifest query |

---

### Task 1: Backend — Permission Inheritance + Module Suppression

**Files:**
- Modify: `avy-erp-backend/src/shared/constants/permissions.ts`
- Modify: `avy-erp-backend/src/middleware/auth.middleware.ts`

- [ ] **Step 1: Add permission inheritance chain to permissions.ts**

Add after line 8 (after `PERMISSION_ACTIONS`):

```typescript
/**
 * Permission inheritance: higher permissions imply lower ones.
 * configure > approve > export > create = update = delete > read
 * e.g., if user has 'hr:configure', they also have hr:approve, hr:export, hr:create, hr:update, hr:delete, hr:read
 */
export const PERMISSION_INHERITANCE: Record<string, string[]> = {
  configure: ['approve', 'export', 'create', 'update', 'delete', 'read'],
  approve: ['export', 'create', 'update', 'delete', 'read'],
  export: ['read'],
  create: ['read'],
  update: ['read'],
  delete: ['read'],
  read: [],
};

/**
 * Maps subscription module IDs (from MODULE_CATALOGUE) to permission module names.
 * When a company doesn't subscribe to a module, all permissions for that module are suppressed.
 */
export const MODULE_TO_PERMISSION_MAP: Record<string, string[]> = {
  'hr': ['hr', 'ess'],
  'security': ['security'],
  'production': ['production'],
  'machine-maintenance': ['maintenance'],
  'inventory': ['inventory'],
  'vendor': ['vendor'],
  'sales': ['sales'],
  'finance': ['finance'],
  'visitor': ['visitors'],
  'masters': ['masters'],
};

/**
 * Expand a flat permissions array by applying inheritance.
 * e.g., ['hr:configure'] → ['hr:configure', 'hr:approve', 'hr:export', 'hr:create', 'hr:update', 'hr:delete', 'hr:read']
 */
export function expandPermissionsWithInheritance(permissions: string[]): string[] {
  const expanded = new Set(permissions);

  for (const perm of permissions) {
    // Skip wildcards — they already grant everything
    if (perm === '*') return ['*'];

    const [module, action] = perm.split(':');
    if (!module || !action) continue;

    // Module wildcard: 'hr:*' — already covers all actions
    if (action === '*') continue;

    // Expand inherited actions
    const inherited = PERMISSION_INHERITANCE[action];
    if (inherited) {
      for (const inheritedAction of inherited) {
        expanded.add(`${module}:${inheritedAction}`);
      }
    }
  }

  return Array.from(expanded);
}

/**
 * Filter permissions by active company modules.
 * Removes any permission whose module is not in the company's subscription.
 * System modules (user, role, company, reports, audit, platform) are never suppressed.
 */
export function suppressByModules(permissions: string[], activeModuleIds: string[]): string[] {
  const SYSTEM_PERMISSION_MODULES = ['user', 'role', 'company', 'reports', 'audit', 'platform', 'ess'];

  // Build set of allowed permission modules from active subscriptions
  const allowedPermModules = new Set(SYSTEM_PERMISSION_MODULES);
  for (const modId of activeModuleIds) {
    const permModules = MODULE_TO_PERMISSION_MAP[modId];
    if (permModules) {
      permModules.forEach(m => allowedPermModules.add(m));
    }
  }

  return permissions.filter(perm => {
    if (perm === '*') return true;
    const [module] = perm.split(':');
    if (!module) return false;
    // Check if module wildcard (e.g., 'hr:*')
    return allowedPermModules.has(module);
  });
}
```

- [ ] **Step 2: Update auth middleware to apply inheritance + suppression**

In `avy-erp-backend/src/middleware/auth.middleware.ts`, find where permissions are resolved (around the section that calls `rbacService.getUserPermissions()`). After permissions are loaded, apply inheritance and module suppression.

Find the block that does:
```typescript
if (user.role === 'SUPER_ADMIN') {
  permissions = ['*'];
} else if (tenantId) {
  permissions = await rbacService.getUserPermissions(userId, tenantId);
} else {
  permissions = [];
}
```

Change to:
```typescript
import { expandPermissionsWithInheritance, suppressByModules } from '../shared/constants/permissions';

// ... inside the middleware ...

if (user.role === 'SUPER_ADMIN') {
  permissions = ['*'];
} else if (tenantId) {
  const rawPermissions = await rbacService.getUserPermissions(userId, tenantId);
  // 1. Expand by inheritance (configure → approve → read etc.)
  const expanded = expandPermissionsWithInheritance(rawPermissions);
  // 2. Suppress by active modules (if company context available)
  if (companyId) {
    const company = await platformPrisma.company.findUnique({
      where: { id: companyId },
      select: { selectedModuleIds: true },
    });
    const activeModuleIds: string[] = company?.selectedModuleIds
      ? (Array.isArray(company.selectedModuleIds) ? company.selectedModuleIds as string[] : JSON.parse(company.selectedModuleIds as string))
      : [];
    permissions = suppressByModules(expanded, activeModuleIds);
  } else {
    permissions = expanded;
  }
} else {
  permissions = [];
}
```

- [ ] **Step 3: Verify backend compiles**

Run: `cd avy-erp-backend && npx tsc --noEmit 2>&1 | grep -c "permissions\|auth.middleware"`
Expected: 0 errors in changed files

- [ ] **Step 4: Commit**

```bash
git add src/shared/constants/permissions.ts src/middleware/auth.middleware.ts
git commit -m "feat(rbac): add permission inheritance chain and module-aware suppression"
```

---

### Task 2: Backend — Navigation Manifest

**Files:**
- Create: `avy-erp-backend/src/shared/constants/navigation-manifest.ts`
- Modify: `avy-erp-backend/src/core/rbac/rbac.service.ts`
- Modify: `avy-erp-backend/src/core/rbac/rbac.controller.ts`
- Modify: `avy-erp-backend/src/core/rbac/rbac.routes.ts`

- [ ] **Step 1: Create navigation manifest constant**

Create `avy-erp-backend/src/shared/constants/navigation-manifest.ts`:

```typescript
/**
 * Navigation Manifest — Single source of truth for all sidebar items.
 *
 * Each entry defines:
 * - id: unique identifier
 * - label: display text
 * - icon: icon name (frontend maps to actual icon)
 * - requiredPerm: permission needed to see this item
 * - path: route path (web uses /app prefix, mobile adjusts)
 * - module: which subscription module this belongs to (null = always visible)
 * - group: section grouping name
 * - moduleSeparator: if set, renders a divider with this label before the group
 * - roleScope: 'super_admin' | 'company' | 'all' — which user types see this
 * - sortOrder: ordering within the group
 */

export interface NavigationItem {
  id: string;
  label: string;
  icon: string;
  requiredPerm: string | null;        // null = always visible
  path: string;                       // canonical path (web-style)
  module: string | null;              // subscription module ID (null = system)
  group: string;
  moduleSeparator?: string;
  roleScope: 'super_admin' | 'company' | 'all';
  sortOrder: number;
  children?: { label: string; path: string }[];
}

export const NAVIGATION_MANIFEST: NavigationItem[] = [
  // ═══════ OVERVIEW ═══════
  { id: 'dashboard', label: 'Dashboard', icon: 'dashboard', requiredPerm: null, path: '/app/dashboard', module: null, group: 'Overview', roleScope: 'all', sortOrder: 0 },

  // ═══════ SUPER ADMIN: PLATFORM ═══════
  { id: 'sa-companies', label: 'Companies', icon: 'building', requiredPerm: 'platform:admin', path: '/app/companies', module: null, group: 'Platform Management', moduleSeparator: 'Platform Management', roleScope: 'super_admin', sortOrder: 100 },
  { id: 'sa-billing', label: 'Billing', icon: 'credit-card', requiredPerm: 'platform:admin', path: '/app/billing', module: null, group: 'Platform Management', roleScope: 'super_admin', sortOrder: 101, children: [{ label: 'Overview', path: '/app/billing' }, { label: 'Invoices', path: '/app/billing/invoices' }, { label: 'Payments', path: '/app/billing/payments' }] },
  { id: 'sa-audit', label: 'Audit Log', icon: 'shield-check', requiredPerm: 'platform:admin', path: '/app/reports/audit', module: null, group: 'Platform Management', roleScope: 'super_admin', sortOrder: 102 },
  { id: 'sa-modules', label: 'Module Catalogue', icon: 'blocks', requiredPerm: 'platform:admin', path: '/app/modules', module: null, group: 'System', moduleSeparator: 'System', roleScope: 'super_admin', sortOrder: 200 },
  { id: 'sa-monitor', label: 'Platform Monitor', icon: 'activity', requiredPerm: 'platform:admin', path: '/app/monitor', module: null, group: 'System', roleScope: 'super_admin', sortOrder: 201 },
  { id: 'sa-users', label: 'User Management', icon: 'user-cog', requiredPerm: 'platform:admin', path: '/app/admin/users', module: null, group: 'System', roleScope: 'super_admin', sortOrder: 202 },
  { id: 'sa-support', label: 'Support Dashboard', icon: 'support', requiredPerm: 'platform:admin', path: '/app/support', module: null, group: 'System', roleScope: 'super_admin', sortOrder: 203 },

  // ═══════ SELF-SERVICE (ESS) — employees + managers + admins ═══════
  { id: 'ess-profile', label: 'My Profile', icon: 'user', requiredPerm: 'ess:view-profile', path: '/app/company/hr/my-profile', module: 'hr', group: 'My Workspace', moduleSeparator: 'Self-Service', roleScope: 'company', sortOrder: 300 },
  { id: 'ess-payslips', label: 'My Payslips', icon: 'receipt', requiredPerm: 'ess:view-payslips', path: '/app/company/hr/my-payslips', module: 'hr', group: 'My Workspace', roleScope: 'company', sortOrder: 301 },
  { id: 'ess-leave', label: 'My Leave', icon: 'calendar-off', requiredPerm: 'ess:view-leave', path: '/app/company/hr/my-leave', module: 'hr', group: 'My Workspace', roleScope: 'company', sortOrder: 302 },
  { id: 'ess-attendance', label: 'My Attendance', icon: 'clock', requiredPerm: 'ess:view-attendance', path: '/app/company/hr/my-attendance', module: 'hr', group: 'My Workspace', roleScope: 'company', sortOrder: 303 },
  { id: 'ess-checkin', label: 'Shift Check-In', icon: 'log-in', requiredPerm: 'ess:view-attendance', path: '/app/company/hr/shift-check-in', module: 'hr', group: 'My Workspace', roleScope: 'company', sortOrder: 304 },
  { id: 'ess-holidays', label: 'Holiday Calendar', icon: 'calendar', requiredPerm: 'ess:view-holidays', path: '/app/company/hr/holidays', module: 'hr', group: 'My Workspace', roleScope: 'company', sortOrder: 305 },
  { id: 'ess-goals', label: 'My Goals', icon: 'target', requiredPerm: 'ess:view-goals', path: '/app/company/hr/my-goals', module: 'hr', group: 'My Workspace', roleScope: 'company', sortOrder: 306 },
  { id: 'ess-it-dec', label: 'IT Declarations', icon: 'file-check', requiredPerm: 'ess:it-declaration', path: '/app/company/hr/it-declarations', module: 'hr', group: 'My Workspace', roleScope: 'company', sortOrder: 307 },
  { id: 'ess-form16', label: 'Form 16', icon: 'file-text', requiredPerm: 'ess:download-form16', path: '/app/company/hr/my-form16', module: 'hr', group: 'My Workspace', roleScope: 'company', sortOrder: 308 },
  { id: 'ess-grievance', label: 'Grievances', icon: 'alert-triangle', requiredPerm: 'ess:raise-grievance', path: '/app/company/hr/my-grievances', module: 'hr', group: 'My Workspace', roleScope: 'company', sortOrder: 309 },
  { id: 'ess-training', label: 'My Training', icon: 'graduation-cap', requiredPerm: 'ess:enroll-training', path: '/app/company/hr/my-training', module: 'hr', group: 'My Workspace', roleScope: 'company', sortOrder: 310 },
  { id: 'ess-assets', label: 'My Assets', icon: 'package', requiredPerm: 'ess:view-assets', path: '/app/company/hr/my-assets', module: 'hr', group: 'My Workspace', roleScope: 'company', sortOrder: 311 },
  { id: 'ess-helpdesk', label: 'Help & Support', icon: 'support', requiredPerm: null, path: '/app/help', module: null, group: 'My Workspace', roleScope: 'company', sortOrder: 399 },

  // ═══════ MANAGER SELF-SERVICE ═══════
  { id: 'mss-team', label: 'Team View', icon: 'users', requiredPerm: 'hr:approve', path: '/app/company/hr/team-view', module: 'hr', group: 'Team Management', roleScope: 'company', sortOrder: 350 },
  { id: 'mss-approvals', label: 'Approval Requests', icon: 'check-square', requiredPerm: 'hr:approve', path: '/app/company/hr/approval-requests', module: 'hr', group: 'Team Management', roleScope: 'company', sortOrder: 351 },

  // ═══════ COMPANY ADMIN ═══════
  { id: 'ca-profile', label: 'Company Profile', icon: 'building', requiredPerm: 'company:read', path: '/app/company/profile', module: null, group: 'Company', moduleSeparator: 'Company Admin', roleScope: 'company', sortOrder: 400 },
  { id: 'ca-locations', label: 'Locations', icon: 'map-pin', requiredPerm: 'company:read', path: '/app/company/locations', module: null, group: 'Company', roleScope: 'company', sortOrder: 401 },
  { id: 'ca-shifts', label: 'Shifts & Time', icon: 'clock', requiredPerm: 'company:read', path: '/app/company/shifts', module: null, group: 'Company', roleScope: 'company', sortOrder: 402 },
  { id: 'ca-contacts', label: 'Key Contacts', icon: 'users', requiredPerm: 'company:read', path: '/app/company/contacts', module: null, group: 'Company', roleScope: 'company', sortOrder: 403 },

  // People & Access
  { id: 'ca-users', label: 'User Management', icon: 'user-cog', requiredPerm: 'user:read', path: '/app/company/users', module: null, group: 'People & Access', roleScope: 'company', sortOrder: 410 },
  { id: 'ca-roles', label: 'Roles & Permissions', icon: 'shield', requiredPerm: 'role:read', path: '/app/company/roles', module: null, group: 'People & Access', roleScope: 'company', sortOrder: 411 },
  { id: 'ca-toggles', label: 'Feature Toggles', icon: 'toggle-left', requiredPerm: 'role:read', path: '/app/company/feature-toggles', module: null, group: 'People & Access', roleScope: 'company', sortOrder: 412 },

  // Configuration
  { id: 'ca-modules', label: 'Module Catalogue', icon: 'blocks', requiredPerm: 'company:read', path: '/app/modules', module: null, group: 'Configuration', roleScope: 'company', sortOrder: 420 },
  { id: 'ca-noseries', label: 'Number Series', icon: 'hash', requiredPerm: 'company:read', path: '/app/company/no-series', module: null, group: 'Configuration', roleScope: 'company', sortOrder: 421 },
  { id: 'ca-iot', label: 'IOT Reasons', icon: 'cpu', requiredPerm: 'company:read', path: '/app/company/iot-reasons', module: null, group: 'Configuration', roleScope: 'company', sortOrder: 422 },
  { id: 'ca-controls', label: 'System Controls', icon: 'sliders', requiredPerm: 'company:configure', path: '/app/company/controls', module: null, group: 'Configuration', roleScope: 'company', sortOrder: 423 },
  { id: 'ca-settings', label: 'Settings', icon: 'settings', requiredPerm: 'company:read', path: '/app/company/settings', module: null, group: 'Configuration', roleScope: 'company', sortOrder: 424 },

  // Billing
  { id: 'ca-billing', label: 'Billing Overview', icon: 'credit-card', requiredPerm: 'company:read', path: '/app/company/billing', module: null, group: 'Billing', roleScope: 'company', sortOrder: 430 },
  { id: 'ca-invoices', label: 'Invoices', icon: 'file-text', requiredPerm: 'company:read', path: '/app/company/billing/invoices', module: null, group: 'Billing', roleScope: 'company', sortOrder: 431 },
  { id: 'ca-payments', label: 'Payments', icon: 'credit-card', requiredPerm: 'company:read', path: '/app/company/billing/payments', module: null, group: 'Billing', roleScope: 'company', sortOrder: 432 },

  // ═══════ HRMS ═══════
  { id: 'hr-departments', label: 'Departments', icon: 'building', requiredPerm: 'hr:read', path: '/app/company/hr/departments', module: 'hr', group: 'Org Structure', moduleSeparator: 'HRMS', roleScope: 'company', sortOrder: 500 },
  { id: 'hr-designations', label: 'Designations', icon: 'briefcase', requiredPerm: 'hr:read', path: '/app/company/hr/designations', module: 'hr', group: 'Org Structure', roleScope: 'company', sortOrder: 501 },
  { id: 'hr-grades', label: 'Grades & Bands', icon: 'bar-chart', requiredPerm: 'hr:read', path: '/app/company/hr/grades', module: 'hr', group: 'Org Structure', roleScope: 'company', sortOrder: 502 },
  { id: 'hr-emptypes', label: 'Employee Types', icon: 'user-check', requiredPerm: 'hr:read', path: '/app/company/hr/employee-types', module: 'hr', group: 'Org Structure', roleScope: 'company', sortOrder: 503 },
  { id: 'hr-costcentres', label: 'Cost Centres', icon: 'wallet', requiredPerm: 'hr:read', path: '/app/company/hr/cost-centres', module: 'hr', group: 'Org Structure', roleScope: 'company', sortOrder: 504 },
  { id: 'hr-employees', label: 'Employee Directory', icon: 'users', requiredPerm: 'hr:read', path: '/app/company/hr/employees', module: 'hr', group: 'Org Structure', roleScope: 'company', sortOrder: 505 },
  { id: 'hr-orgchart', label: 'Org Chart', icon: 'git-fork', requiredPerm: 'hr:read', path: '/app/company/hr/org-chart', module: 'hr', group: 'Org Structure', roleScope: 'company', sortOrder: 506 },

  // Attendance
  { id: 'hr-att-dash', label: 'Attendance Dashboard', icon: 'calendar-check', requiredPerm: 'hr:read', path: '/app/company/hr/attendance', module: 'hr', group: 'Attendance', roleScope: 'company', sortOrder: 510 },
  { id: 'hr-holidays', label: 'Holiday Calendar', icon: 'calendar', requiredPerm: 'hr:read', path: '/app/company/hr/holidays', module: 'hr', group: 'Attendance', roleScope: 'company', sortOrder: 511 },
  { id: 'hr-rosters', label: 'Rosters', icon: 'calendar-days', requiredPerm: 'hr:read', path: '/app/company/hr/rosters', module: 'hr', group: 'Attendance', roleScope: 'company', sortOrder: 512 },
  { id: 'hr-att-rules', label: 'Attendance Rules', icon: 'clipboard-list', requiredPerm: 'hr:configure', path: '/app/company/hr/attendance-rules', module: 'hr', group: 'Attendance', roleScope: 'company', sortOrder: 513 },
  { id: 'hr-ot-rules', label: 'Overtime Rules', icon: 'timer', requiredPerm: 'hr:configure', path: '/app/company/hr/overtime-rules', module: 'hr', group: 'Attendance', roleScope: 'company', sortOrder: 514 },
  { id: 'hr-biometric', label: 'Biometric Devices', icon: 'cpu', requiredPerm: 'hr:configure', path: '/app/company/hr/biometric-devices', module: 'hr', group: 'Attendance', roleScope: 'company', sortOrder: 515 },
  { id: 'hr-rotations', label: 'Shift Rotations', icon: 'refresh-cw', requiredPerm: 'hr:configure', path: '/app/company/hr/shift-rotations', module: 'hr', group: 'Attendance', roleScope: 'company', sortOrder: 516 },

  // Leave Management
  { id: 'hr-leave-types', label: 'Leave Types', icon: 'file-text', requiredPerm: 'hr:read', path: '/app/company/hr/leave-types', module: 'hr', group: 'Leave Management', roleScope: 'company', sortOrder: 520 },
  { id: 'hr-leave-pol', label: 'Leave Policies', icon: 'book-open', requiredPerm: 'hr:read', path: '/app/company/hr/leave-policies', module: 'hr', group: 'Leave Management', roleScope: 'company', sortOrder: 521 },
  { id: 'hr-leave-req', label: 'Leave Requests', icon: 'send', requiredPerm: 'hr:read', path: '/app/company/hr/leave-requests', module: 'hr', group: 'Leave Management', roleScope: 'company', sortOrder: 522 },
  { id: 'hr-leave-bal', label: 'Leave Balances', icon: 'scale', requiredPerm: 'hr:read', path: '/app/company/hr/leave-balances', module: 'hr', group: 'Leave Management', roleScope: 'company', sortOrder: 523 },

  // Payroll & Compliance
  { id: 'hr-sal-comp', label: 'Salary Components', icon: 'dollar-sign', requiredPerm: 'hr:read', path: '/app/company/hr/salary-components', module: 'hr', group: 'Payroll & Compliance', roleScope: 'company', sortOrder: 530 },
  { id: 'hr-sal-struct', label: 'Salary Structures', icon: 'file-spreadsheet', requiredPerm: 'hr:read', path: '/app/company/hr/salary-structures', module: 'hr', group: 'Payroll & Compliance', roleScope: 'company', sortOrder: 531 },
  { id: 'hr-emp-sal', label: 'Employee Salary', icon: 'credit-card', requiredPerm: 'hr:read', path: '/app/company/hr/employee-salary', module: 'hr', group: 'Payroll & Compliance', roleScope: 'company', sortOrder: 532 },
  { id: 'hr-statutory', label: 'Statutory Config', icon: 'shield', requiredPerm: 'hr:configure', path: '/app/company/hr/statutory-config', module: 'hr', group: 'Payroll & Compliance', roleScope: 'company', sortOrder: 533 },
  { id: 'hr-tax', label: 'Tax & TDS', icon: 'calculator', requiredPerm: 'hr:configure', path: '/app/company/hr/tax-config', module: 'hr', group: 'Payroll & Compliance', roleScope: 'company', sortOrder: 534 },
  { id: 'hr-bank', label: 'Bank Config', icon: 'landmark', requiredPerm: 'hr:configure', path: '/app/company/hr/bank-config', module: 'hr', group: 'Payroll & Compliance', roleScope: 'company', sortOrder: 535 },
  { id: 'hr-loan-pol', label: 'Loan Policies', icon: 'hand-coins', requiredPerm: 'hr:read', path: '/app/company/hr/loan-policies', module: 'hr', group: 'Payroll & Compliance', roleScope: 'company', sortOrder: 536 },
  { id: 'hr-loans', label: 'Loans', icon: 'receipt', requiredPerm: 'hr:read', path: '/app/company/hr/loans', module: 'hr', group: 'Payroll & Compliance', roleScope: 'company', sortOrder: 537 },

  // Payroll Operations
  { id: 'hr-payroll-runs', label: 'Payroll Runs', icon: 'play', requiredPerm: 'hr:read', path: '/app/company/hr/payroll-runs', module: 'hr', group: 'Payroll Operations', roleScope: 'company', sortOrder: 540 },
  { id: 'hr-payslips', label: 'Payslips', icon: 'file-text', requiredPerm: 'hr:read', path: '/app/company/hr/payslips', module: 'hr', group: 'Payroll Operations', roleScope: 'company', sortOrder: 541 },
  { id: 'hr-sal-holds', label: 'Salary Holds', icon: 'pause-circle', requiredPerm: 'hr:read', path: '/app/company/hr/salary-holds', module: 'hr', group: 'Payroll Operations', roleScope: 'company', sortOrder: 542 },
  { id: 'hr-sal-rev', label: 'Salary Revisions', icon: 'trending-up', requiredPerm: 'hr:read', path: '/app/company/hr/salary-revisions', module: 'hr', group: 'Payroll Operations', roleScope: 'company', sortOrder: 543 },
  { id: 'hr-stat-fil', label: 'Statutory Filings', icon: 'stamp', requiredPerm: 'hr:read', path: '/app/company/hr/statutory-filings', module: 'hr', group: 'Payroll Operations', roleScope: 'company', sortOrder: 544 },
  { id: 'hr-pay-reports', label: 'Payroll Reports', icon: 'bar-chart', requiredPerm: 'hr:export', path: '/app/company/hr/payroll-reports', module: 'hr', group: 'Payroll Operations', roleScope: 'company', sortOrder: 545 },
  { id: 'hr-bonus', label: 'Bonus Batches', icon: 'gift', requiredPerm: 'hr:read', path: '/app/company/hr/bonus-batches', module: 'hr', group: 'Payroll Operations', roleScope: 'company', sortOrder: 546 },
  { id: 'hr-form16', label: 'Form 16 & 24Q', icon: 'file-text', requiredPerm: 'hr:read', path: '/app/company/hr/form-16', module: 'hr', group: 'Payroll Operations', roleScope: 'company', sortOrder: 547 },
  { id: 'hr-travel', label: 'Travel Advances', icon: 'plane', requiredPerm: 'hr:read', path: '/app/company/hr/travel-advances', module: 'hr', group: 'Payroll Operations', roleScope: 'company', sortOrder: 548 },

  // ESS & Workflows (admin config)
  { id: 'hr-ess-config', label: 'ESS Config', icon: 'settings', requiredPerm: 'hr:configure', path: '/app/company/hr/ess-config', module: 'hr', group: 'ESS & Workflows', roleScope: 'company', sortOrder: 550 },
  { id: 'hr-workflows', label: 'Approval Workflows', icon: 'git-branch', requiredPerm: 'hr:configure', path: '/app/company/hr/approval-workflows', module: 'hr', group: 'ESS & Workflows', roleScope: 'company', sortOrder: 551 },
  { id: 'hr-notif-tpl', label: 'Notification Templates', icon: 'mail', requiredPerm: 'hr:configure', path: '/app/company/hr/notification-templates', module: 'hr', group: 'ESS & Workflows', roleScope: 'company', sortOrder: 552 },
  { id: 'hr-notif-rules', label: 'Notification Rules', icon: 'bell-ring', requiredPerm: 'hr:configure', path: '/app/company/hr/notification-rules', module: 'hr', group: 'ESS & Workflows', roleScope: 'company', sortOrder: 553 },
  { id: 'hr-esign', label: 'E-Sign Tracking', icon: 'pen-tool', requiredPerm: 'hr:read', path: '/app/company/hr/esign', module: 'hr', group: 'ESS & Workflows', roleScope: 'company', sortOrder: 554 },

  // Transfers & Promotions
  { id: 'hr-transfers', label: 'Employee Transfers', icon: 'arrow-left-right', requiredPerm: 'hr:read', path: '/app/company/hr/transfers', module: 'hr', group: 'Transfers & Promotions', roleScope: 'company', sortOrder: 560 },
  { id: 'hr-promotions', label: 'Employee Promotions', icon: 'trending-up', requiredPerm: 'hr:read', path: '/app/company/hr/promotions', module: 'hr', group: 'Transfers & Promotions', roleScope: 'company', sortOrder: 561 },
  { id: 'hr-delegates', label: 'Manager Delegation', icon: 'user-check', requiredPerm: 'hr:read', path: '/app/company/hr/delegates', module: 'hr', group: 'Transfers & Promotions', roleScope: 'company', sortOrder: 562 },

  // Performance
  { id: 'hr-appraisals', label: 'Appraisal Cycles', icon: 'target', requiredPerm: 'hr:read', path: '/app/company/hr/appraisal-cycles', module: 'hr', group: 'Performance', roleScope: 'company', sortOrder: 570 },
  { id: 'hr-goals', label: 'Goals & OKRs', icon: 'flag', requiredPerm: 'hr:read', path: '/app/company/hr/goals', module: 'hr', group: 'Performance', roleScope: 'company', sortOrder: 571 },
  { id: 'hr-360', label: '360 Feedback', icon: 'message-square', requiredPerm: 'hr:read', path: '/app/company/hr/feedback-360', module: 'hr', group: 'Performance', roleScope: 'company', sortOrder: 572 },
  { id: 'hr-ratings', label: 'Ratings & Calibration', icon: 'star', requiredPerm: 'hr:read', path: '/app/company/hr/ratings', module: 'hr', group: 'Performance', roleScope: 'company', sortOrder: 573 },
  { id: 'hr-skills', label: 'Skills & Mapping', icon: 'brain', requiredPerm: 'hr:read', path: '/app/company/hr/skills', module: 'hr', group: 'Performance', roleScope: 'company', sortOrder: 574 },
  { id: 'hr-succession', label: 'Succession Planning', icon: 'git-fork', requiredPerm: 'hr:read', path: '/app/company/hr/succession', module: 'hr', group: 'Performance', roleScope: 'company', sortOrder: 575 },
  { id: 'hr-perf-dash', label: 'Performance Dashboard', icon: 'activity', requiredPerm: 'hr:read', path: '/app/company/hr/performance-dashboard', module: 'hr', group: 'Performance', roleScope: 'company', sortOrder: 576 },

  // Recruitment & Training
  { id: 'hr-requisitions', label: 'Job Requisitions', icon: 'briefcase', requiredPerm: 'hr:read', path: '/app/company/hr/requisitions', module: 'hr', group: 'Recruitment & Training', roleScope: 'company', sortOrder: 580 },
  { id: 'hr-candidates', label: 'Candidates', icon: 'user-plus', requiredPerm: 'hr:read', path: '/app/company/hr/candidates', module: 'hr', group: 'Recruitment & Training', roleScope: 'company', sortOrder: 581 },
  { id: 'hr-training', label: 'Training Catalogue', icon: 'graduation-cap', requiredPerm: 'hr:read', path: '/app/company/hr/training', module: 'hr', group: 'Recruitment & Training', roleScope: 'company', sortOrder: 582 },
  { id: 'hr-nominations', label: 'Training Nominations', icon: 'award', requiredPerm: 'hr:read', path: '/app/company/hr/training-nominations', module: 'hr', group: 'Recruitment & Training', roleScope: 'company', sortOrder: 583 },
  { id: 'hr-onboarding', label: 'Onboarding', icon: 'log-in', requiredPerm: 'hr:read', path: '/app/company/hr/onboarding', module: 'hr', group: 'Recruitment & Training', roleScope: 'company', sortOrder: 584 },
  { id: 'hr-probation', label: 'Probation Reviews', icon: 'clock', requiredPerm: 'hr:read', path: '/app/company/hr/probation-reviews', module: 'hr', group: 'Recruitment & Training', roleScope: 'company', sortOrder: 585 },

  // Exit & Separation
  { id: 'hr-exit', label: 'Exit Requests', icon: 'log-out', requiredPerm: 'hr:read', path: '/app/company/hr/exit-requests', module: 'hr', group: 'Exit & Separation', roleScope: 'company', sortOrder: 590 },
  { id: 'hr-clearance', label: 'Clearance Dashboard', icon: 'clipboard-list', requiredPerm: 'hr:read', path: '/app/company/hr/clearance-dashboard', module: 'hr', group: 'Exit & Separation', roleScope: 'company', sortOrder: 591 },
  { id: 'hr-fnf', label: 'F&F Settlement', icon: 'calculator', requiredPerm: 'hr:read', path: '/app/company/hr/fnf-settlement', module: 'hr', group: 'Exit & Separation', roleScope: 'company', sortOrder: 592 },

  // Advanced HR
  { id: 'hr-assets', label: 'Asset Management', icon: 'package', requiredPerm: 'hr:read', path: '/app/company/hr/assets', module: 'hr', group: 'Advanced HR', roleScope: 'company', sortOrder: 600 },
  { id: 'hr-expenses', label: 'Expense Claims', icon: 'receipt', requiredPerm: 'hr:read', path: '/app/company/hr/expenses', module: 'hr', group: 'Advanced HR', roleScope: 'company', sortOrder: 601 },
  { id: 'hr-letters', label: 'HR Letters', icon: 'file-signature', requiredPerm: 'hr:read', path: '/app/company/hr/hr-letters', module: 'hr', group: 'Advanced HR', roleScope: 'company', sortOrder: 602 },
  { id: 'hr-grievances', label: 'Grievances', icon: 'alert-triangle', requiredPerm: 'hr:read', path: '/app/company/hr/grievances', module: 'hr', group: 'Advanced HR', roleScope: 'company', sortOrder: 603 },
  { id: 'hr-disciplinary', label: 'Disciplinary Actions', icon: 'gavel', requiredPerm: 'hr:read', path: '/app/company/hr/disciplinary', module: 'hr', group: 'Advanced HR', roleScope: 'company', sortOrder: 604 },
  { id: 'hr-chatbot', label: 'HR Chatbot', icon: 'message-circle', requiredPerm: 'hr:read', path: '/app/company/hr/chatbot', module: 'hr', group: 'Advanced HR', roleScope: 'company', sortOrder: 605 },
  { id: 'hr-retention', label: 'Data Retention', icon: 'database', requiredPerm: 'hr:configure', path: '/app/company/hr/data-retention', module: 'hr', group: 'Advanced HR', roleScope: 'company', sortOrder: 606 },
  { id: 'hr-incentives', label: 'Production Incentives', icon: 'trending-up', requiredPerm: 'hr:read', path: '/app/company/hr/production-incentives', module: 'hr', group: 'Advanced HR', roleScope: 'company', sortOrder: 607 },

  // ═══════ OPERATIONS ═══════
  { id: 'ops-inventory', label: 'Inventory', icon: 'package', requiredPerm: 'inventory:read', path: '/app/inventory', module: 'inventory', group: 'Operations', moduleSeparator: 'Operations', roleScope: 'company', sortOrder: 700 },
  { id: 'ops-production', label: 'Production', icon: 'factory', requiredPerm: 'production:read', path: '/app/production', module: 'production', group: 'Operations', roleScope: 'company', sortOrder: 701 },
  { id: 'ops-maintenance', label: 'Maintenance', icon: 'wrench', requiredPerm: 'maintenance:read', path: '/app/maintenance', module: 'machine-maintenance', group: 'Operations', roleScope: 'company', sortOrder: 702, children: [{ label: 'Work Orders', path: '/app/maintenance/orders' }, { label: 'Machine Registry', path: '/app/maintenance/machines' }] },

  // ═══════ REPORTS ═══════
  { id: 'rpt-audit', label: 'Audit Logs', icon: 'shield-check', requiredPerm: 'audit:read', path: '/app/reports/audit', module: null, group: 'Reports', roleScope: 'company', sortOrder: 800 },
];

/**
 * Group navigation items by their group name, preserving sort order.
 * Returns sections with optional moduleSeparator from the first item in each group.
 */
export function getGroupedNavigation(items: NavigationItem[]): Array<{
  group: string;
  moduleSeparator?: string;
  items: NavigationItem[];
}> {
  const groups = new Map<string, { moduleSeparator?: string; items: NavigationItem[] }>();

  const sorted = [...items].sort((a, b) => a.sortOrder - b.sortOrder);

  for (const item of sorted) {
    if (!groups.has(item.group)) {
      groups.set(item.group, { moduleSeparator: item.moduleSeparator, items: [] });
    }
    groups.get(item.group)!.items.push(item);
  }

  return Array.from(groups.entries()).map(([group, data]) => ({
    group,
    moduleSeparator: data.moduleSeparator,
    items: data.items,
  }));
}
```

- [ ] **Step 2: Add manifest endpoint to RBAC service**

In `avy-erp-backend/src/core/rbac/rbac.service.ts`, add a new method:

```typescript
import { NAVIGATION_MANIFEST, getGroupedNavigation, type NavigationItem } from '../../shared/constants/navigation-manifest';
import { hasPermission } from '../../shared/constants/permissions';

// Add to RbacService class:

async getNavigationManifest(params: {
  userPermissions: string[];
  userRole: 'SUPER_ADMIN' | 'COMPANY_ADMIN' | string;
  activeModuleIds: string[];
}): Promise<ReturnType<typeof getGroupedNavigation>> {
  const { userPermissions, userRole, activeModuleIds } = params;
  const isSuperAdmin = userRole === 'SUPER_ADMIN';

  // Filter manifest by role scope + permissions + active modules
  const filtered = NAVIGATION_MANIFEST.filter((item) => {
    // Role scope filter
    if (item.roleScope === 'super_admin' && !isSuperAdmin) return false;
    if (item.roleScope === 'company' && isSuperAdmin) return false;

    // Module subscription filter (skip for system items with module: null)
    if (item.module && !activeModuleIds.includes(item.module)) return false;

    // Permission filter
    if (item.requiredPerm && !hasPermission(userPermissions, item.requiredPerm)) return false;

    return true;
  });

  return getGroupedNavigation(filtered);
}
```

- [ ] **Step 3: Add controller handler and route**

In `avy-erp-backend/src/core/rbac/rbac.controller.ts`, add:

```typescript
getNavigationManifest = asyncHandler(async (req: Request, res: Response) => {
  const userPermissions = req.user?.permissions ?? [];
  const userRole = req.user?.roleId ?? 'COMPANY_ADMIN';
  const companyId = req.user?.companyId;

  // Get active module IDs for the company
  let activeModuleIds: string[] = [];
  if (companyId) {
    const company = await platformPrisma.company.findUnique({
      where: { id: companyId },
      select: { selectedModuleIds: true },
    });
    if (company?.selectedModuleIds) {
      activeModuleIds = Array.isArray(company.selectedModuleIds)
        ? company.selectedModuleIds as string[]
        : JSON.parse(company.selectedModuleIds as string);
    }
  }

  const manifest = await rbacService.getNavigationManifest({
    userPermissions,
    userRole,
    activeModuleIds,
  });

  res.json(createSuccessResponse(manifest, 'Navigation manifest retrieved'));
});
```

In `avy-erp-backend/src/core/rbac/rbac.routes.ts`, add the route (before the roles routes):

```typescript
router.get('/navigation-manifest', rbacController.getNavigationManifest);
```

This route only needs `authMiddleware` (no specific permission) since the manifest is self-filtering based on the user's permissions.

- [ ] **Step 4: Verify backend compiles**

Run: `cd avy-erp-backend && npx tsc --noEmit 2>&1 | grep -v "attendance\|ess.service" | head -10`

- [ ] **Step 5: Commit**

```bash
git add src/shared/constants/navigation-manifest.ts src/core/rbac/
git commit -m "feat(rbac): add navigation manifest API with role/permission/module filtering"
```

---

### Task 3: Web — Dynamic Sidebar from Manifest + useCanPerform Hook

**Files:**
- Create: `web-system-app/src/hooks/useCanPerform.ts`
- Modify: `web-system-app/src/features/company-admin/api/use-company-admin-queries.ts`
- Modify: `web-system-app/src/layouts/Sidebar.tsx`
- Modify: `web-system-app/src/layouts/DashboardLayout.tsx`
- Modify: `web-system-app/src/lib/api/company-admin.ts`

- [ ] **Step 1: Add useCanPerform hook**

Create `web-system-app/src/hooks/useCanPerform.ts`:

```typescript
import { useAuthStore } from '@/store/useAuthStore';
import { checkPermission } from '@/lib/api/auth';

/**
 * Hook for button-level permission checks.
 * Returns true if the current user has the specified permission.
 * Supports wildcards: '*', 'module:*'
 *
 * Usage:
 *   const canCreate = useCanPerform('hr:create');
 *   {canCreate && <button>Add Employee</button>}
 */
export function useCanPerform(permission: string): boolean {
    const permissions = useAuthStore((s) => s.permissions);
    return checkPermission(permissions, permission);
}

/**
 * Hook that returns a permission checker function.
 * Useful when checking multiple permissions in a single component.
 *
 * Usage:
 *   const can = usePermissionChecker();
 *   const canRead = can('hr:read');
 *   const canCreate = can('hr:create');
 */
export function usePermissionChecker(): (permission: string) => boolean {
    const permissions = useAuthStore((s) => s.permissions);
    return (permission: string) => checkPermission(permissions, permission);
}
```

- [ ] **Step 2: Add navigation manifest API + query hook**

In `web-system-app/src/lib/api/company-admin.ts`, add to the `companyAdminApi` object:

```typescript
// ── Navigation Manifest ──
getNavigationManifest: () =>
    client.get('/rbac/navigation-manifest').then(r => r.data),
```

In `web-system-app/src/features/company-admin/api/use-company-admin-queries.ts`, add key + hook:

```typescript
// Add to companyAdminKeys:
navigationManifest: () => [...companyAdminKeys.all, 'navigation-manifest'] as const,

// Add hook:
export function useNavigationManifest() {
    return useQuery({
        queryKey: companyAdminKeys.navigationManifest(),
        queryFn: () => companyAdminApi.getNavigationManifest(),
        staleTime: 5 * 60 * 1000,  // Cache for 5 min — nav doesn't change often
    });
}
```

Export from index.ts.

- [ ] **Step 3: Update Sidebar to render from manifest**

Replace the hardcoded `NAV_CONFIG` array in `web-system-app/src/layouts/Sidebar.tsx` with manifest consumption. The Sidebar now receives `manifestSections` as a prop instead of filtering `NAV_CONFIG` internally.

Update `SidebarProps`:
```typescript
interface ManifestNavItem {
    id: string;
    label: string;
    icon: string;
    path: string;
    requiredPerm: string | null;
    children?: { label: string; path: string }[];
}

interface ManifestSection {
    group: string;
    moduleSeparator?: string;
    items: ManifestNavItem[];
}

interface SidebarProps {
    collapsed: boolean;
    onCollapse: (v: boolean) => void;
    manifestSections?: ManifestSection[];
    role?: SidebarUserRole;
    permissions?: string[];
}
```

The Sidebar should use `manifestSections` when available (from API), falling back to the existing `NAV_CONFIG` when the manifest hasn't loaded yet. Map `icon` strings to lucide-react components using an `ICON_MAP`.

Add icon mapping:
```typescript
const ICON_MAP: Record<string, React.ComponentType<any>> = {
    'dashboard': LayoutDashboard, 'building': Building2, 'credit-card': CreditCard,
    'shield-check': ShieldCheck, 'blocks': Blocks, 'activity': Activity,
    'user-cog': UserCog, 'support': HelpCircle, 'user': UserCircle,
    'receipt': Receipt, 'calendar-off': CalendarOff, 'clock': Clock,
    'log-in': LogIn, 'calendar': Calendar, 'target': Target,
    'file-check': FileCheck, 'file-text': FileText, 'alert-triangle': AlertTriangle,
    'graduation-cap': GraduationCap, 'package': Package, 'message-circle': MessageSquare,
    'map-pin': MapPin, 'users': Users, 'shield': Shield, 'toggle-left': ToggleLeft,
    'hash': Hash, 'cpu': Cpu, 'sliders': SlidersHorizontal, 'settings': Settings,
    'briefcase': Briefcase, 'bar-chart': BarChart3, 'user-check': UserCheck,
    'wallet': Wallet, 'calendar-check': CalendarCheck, 'calendar-days': CalendarDays,
    'clipboard-list': ClipboardList, 'timer': Timer, 'book-open': BookOpen,
    'send': Send, 'scale': Scale, 'dollar-sign': DollarSign,
    'file-spreadsheet': FileSpreadsheet, 'calculator': Calculator,
    'landmark': Landmark, 'hand-coins': HandCoins, 'play': Play,
    'pause-circle': PauseCircle, 'trending-up': TrendingUp, 'stamp': Stamp,
    'git-branch': GitBranch, 'mail': Mail, 'bell-ring': BellRing,
    'arrow-left-right': ArrowLeftRight, 'flag': Flag, 'star': Star,
    'brain': Brain, 'git-fork': GitFork, 'user-plus': UserPlus,
    'award': Award, 'log-out': LogOut, 'gavel': Gavel,
    'file-signature': FileSignature, 'wrench': Wrench, 'check-square': CheckCircle2,
    // defaults
    'default': Blocks,
};

function resolveIcon(iconName: string) {
    return ICON_MAP[iconName] ?? ICON_MAP['default'];
}
```

Update the rendering logic to use `manifestSections` when available:
```typescript
const visibleSections = manifestSections ?? /* existing NAV_CONFIG filtering as fallback */;
```

- [ ] **Step 4: Update DashboardLayout to fetch and pass manifest**

```typescript
import { useNavigationManifest } from '@/features/company-admin/api';

export function DashboardLayout() {
    const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
    const userRole = useAuthStore((s) => s.userRole);
    const permissions = useAuthStore((s) => s.permissions);
    const { data: manifestData } = useNavigationManifest();
    const manifestSections = manifestData?.data ?? undefined;

    return (
        <div className="flex h-screen w-full overflow-hidden ...">
            <Sidebar
                collapsed={sidebarCollapsed}
                onCollapse={setSidebarCollapsed}
                role={toSidebarRole(userRole)}
                permissions={permissions}
                manifestSections={manifestSections}
            />
            ...
        </div>
    );
}
```

- [ ] **Step 5: Commit**

```bash
git add src/hooks/useCanPerform.ts src/layouts/ src/features/company-admin/api/ src/lib/api/company-admin.ts
git commit -m "feat(web): dynamic sidebar from navigation manifest + useCanPerform hook"
```

---

### Task 4: Mobile — Dynamic Sidebar from Manifest + useCanPerform Hook

**Files:**
- Create: `mobile-app/src/hooks/use-can-perform.ts`
- Modify: `mobile-app/src/features/company-admin/api/use-company-admin-queries.ts`
- Modify: `mobile-app/src/lib/api/company-admin.ts`
- Modify: `mobile-app/src/app/(app)/_layout.tsx`

- [ ] **Step 1: Add useCanPerform hook**

Create `mobile-app/src/hooks/use-can-perform.ts`:

```typescript
import { useAuthStore } from '@/features/auth/use-auth-store';
import { checkPermission } from '@/lib/api/auth';

export function useCanPerform(permission: string): boolean {
    const permissions = useAuthStore.use.permissions();
    return checkPermission(permissions, permission);
}

export function usePermissionChecker(): (permission: string) => boolean {
    const permissions = useAuthStore.use.permissions();
    return (permission: string) => checkPermission(permissions, permission);
}
```

- [ ] **Step 2: Add navigation manifest API + query hook**

In mobile `company-admin.ts`, add:
```typescript
getNavigationManifest: () => client.get('/rbac/navigation-manifest'),
```

In mobile `use-company-admin-queries.ts`, add:
```typescript
navigationManifest: () => [...companyAdminKeys.all, 'navigation-manifest'] as const,

export function useNavigationManifest() {
    return useQuery({
        queryKey: companyAdminKeys.navigationManifest(),
        queryFn: () => companyAdminApi.getNavigationManifest(),
        staleTime: 5 * 60 * 1000,
    });
}
```

- [ ] **Step 3: Update _layout.tsx AppSidebar to use manifest**

Replace the hardcoded `allSections` array in the non-super-admin path with manifest consumption. The manifest provides all sections already filtered by the backend. The mobile just needs to map the manifest format to `SidebarSection[]`.

```typescript
function AppSidebar() {
    // ... existing hooks ...
    const { data: manifestData } = useNavigationManifest();

    const sections: SidebarSection[] = React.useMemo(() => {
        const rawManifest = manifestData?.data ?? manifestData;
        if (!Array.isArray(rawManifest) || rawManifest.length === 0) {
            // Fallback: return minimal sections while loading
            return [{ items: [{ id: 'dashboard', label: 'Dashboard', icon: 'dashboard' as const, isActive: pathname === '/', onPress: () => router.push('/') }] }];
        }

        // Map manifest sections to SidebarSection format
        return rawManifest.map((section: any) => ({
            moduleSeparator: section.moduleSeparator,
            title: section.group === 'Overview' ? undefined : section.group,
            items: section.items.map((item: any) => ({
                id: item.id,
                label: item.label,
                icon: mapIconName(item.icon),
                isActive: pathname.startsWith(item.path.replace('/app', '')),
                onPress: () => {
                    const mobilePath = item.path.replace('/app', '');
                    router.push(mobilePath as any);
                },
            })),
        })).filter((s: any) => s.items.length > 0);
    }, [manifestData, pathname, router]);

    // ... rest of component ...
}

function mapIconName(icon: string): SidebarIconType {
    const MAP: Record<string, SidebarIconType> = {
        'dashboard': 'dashboard', 'building': 'companies', 'credit-card': 'billing',
        'users': 'users', 'settings': 'settings', 'support': 'support',
        'shield-check': 'audit', 'log-out': 'logout', 'message-circle': 'support',
    };
    return MAP[icon] ?? 'settings';
}
```

- [ ] **Step 4: Commit**

```bash
git add src/hooks/use-can-perform.ts src/features/company-admin/api/ src/lib/api/company-admin.ts src/app/\(app\)/_layout.tsx
git commit -m "feat(mobile): dynamic sidebar from navigation manifest + useCanPerform hook"
```

---

### Task 5: Verification

- [ ] **Step 1: Verify all 3 codebases compile**

```bash
cd avy-erp-backend && npx tsc --noEmit 2>&1 | grep -v "attendance\|ess.service"
cd web-system-app && npx tsc --noEmit
cd mobile-app && npx tsc --noEmit
```

- [ ] **Step 2: Trace permission scenarios**

Verify by code-tracing:
- **Employee** with `['ess:view-profile', 'ess:view-leave', 'ess:view-attendance', 'ess:view-holidays']`: Should see My Workspace section only + Help & Support
- **Manager** with `['ess:*', 'hr:read', 'hr:approve']`: Should see My Workspace + Team Management + all HRMS read sections. `hr:approve` inherits `hr:read` via inheritance.
- **Company Admin** with `['company:*', 'hr:*', 'user:*', 'role:*', 'audit:read']`: Should see everything. `hr:*` covers `hr:configure` which inherits all.
- **User with `hr:configure`**: Should also see `hr:read` items (via inheritance)

- [ ] **Step 3: Final commit**

```bash
git add -A && git commit -m "feat: complete dynamic RBAC system with navigation manifest, permission inheritance, and module suppression"
```
