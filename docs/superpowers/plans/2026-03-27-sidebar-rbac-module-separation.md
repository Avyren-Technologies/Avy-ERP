# Sidebar RBAC & Module Separation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make sidebar navigation permission-aware (RBAC-driven) on both web and mobile, add module-based visual separators, and standardize section ordering across both apps.

**Architecture:** Three changes: (1) Web sidebar switches from role-only filtering to permission-based filtering matching how mobile already works, (2) Both apps add a `moduleSeparator` field to section definitions that renders a styled divider with module name, (3) Section ordering is standardized across both apps following a logical grouping: Dashboard > Company Admin > HRMS > Operations > Reports & Support.

**Tech Stack:** React (web), React Native + Expo Router (mobile), TypeScript, Zustand auth store, `checkPermission()` utility

---

## Standardized Section Order (Reference)

Both web and mobile will use this exact ordering for non-super-admin users:

```
── Overview ──
  Dashboard                                (always visible)

── COMPANY ADMIN ── (module separator)
  Company                                  (company:read)
    Profile, Locations, Shifts & Time, Key Contacts
  People & Access                          (per-item: user:read, role:read)
    User Management, Roles & Permissions, Feature Toggles
  Configuration                            (company:read + company:configure for Controls)
    Number Series, IOT Reasons, System Controls, Settings
  Billing                                  (company:read)
    Overview, Invoices, Payments

── HRMS ── (module separator)
  Org Structure                            (hr:read)
    Departments, Designations, Grades & Bands, Employee Types, Cost Centres, Employee Directory
  Attendance                               (hr:read)
    Dashboard, Holiday Calendar, Rosters, Attendance Rules, Overtime Rules
  Leave Management                         (hr:read)
    Leave Types, Leave Policies, Leave Requests, Leave Balances
  Payroll & Compliance                     (hr:read)
    Salary Components, Salary Structures, Employee Salary, Statutory Config, Tax & TDS, Bank Config, Loan Policies, Loans
  Payroll Operations                       (hr:read)
    Payroll Runs, Payslips, Salary Holds, Salary Revisions, Statutory Filings, Payroll Reports
  Self-Service                             (hr:read)
    My Profile, My Payslips, My Leave, My Attendance, Shift Check-In, Team View
  ESS & Workflows                          (hr:read)
    ESS Config, Approval Workflows, Notification Templates, Notification Rules, IT Declarations
  Transfers & Promotions                   (hr:read)
    Employee Transfers, Employee Promotions, Manager Delegation
  Performance                              (hr:read)
    Appraisal Cycles, Goals & OKRs, 360 Feedback, Ratings & Calibration, Skills & Mapping, Succession Planning, Performance Dashboard
  Recruitment & Training                   (hr:read)
    Job Requisitions, Candidates, Training Catalogue, Training Nominations
  Exit & Separation                        (hr:read)
    Exit Requests, Clearance Dashboard, F&F Settlement
  Advanced HR                              (hr:read)
    Asset Management, Expense Claims, HR Letters, Grievances, Disciplinary Actions

── OPERATIONS ── (module separator, future modules)
  Operations                               (per-item: inventory:read, production:read, maintenance:read)
    Inventory, Production, Maintenance

── REPORTS & SUPPORT ──
  Reports                                  (audit:read)
    Audit Logs
  Support                                  (always visible)
    Help & Support
```

Super admin order:
```
── Overview ──
  Dashboard

── PLATFORM MANAGEMENT ── (module separator)
  Companies
  Billing (Overview, Invoices, Payments)
  Audit Log

── SYSTEM ── (module separator)
  Module Catalogue, Platform Monitor
  User Management
  Settings, Support
```

## File Structure

| File | Action | Responsibility |
|------|--------|----------------|
| `mobile-app/src/components/ui/sidebar.tsx` | Modify | Add `moduleSeparator` to `SidebarSection` interface, render separator UI |
| `mobile-app/src/app/(app)/_layout.tsx` | Modify | Add module separators to sections, reorder to match standard |
| `web-system-app/src/layouts/Sidebar.tsx` | Modify | Add `requiredPerm`/`moduleSeparator` to `NavSection`, permission-based filtering, reorder, separator UI |
| `web-system-app/src/layouts/DashboardLayout.tsx` | Modify | Pass `permissions` from auth store to Sidebar |

---

### Task 1: Mobile — Add Module Separator to Sidebar Component

**Files:**
- Modify: `mobile-app/src/components/ui/sidebar.tsx:44-47` (SidebarSection interface)
- Modify: `mobile-app/src/components/ui/sidebar.tsx:400-413` (section rendering)
- Modify: `mobile-app/src/components/ui/sidebar.tsx:510-677` (styles)

- [ ] **Step 1: Add `moduleSeparator` to `SidebarSection` interface**

In `mobile-app/src/components/ui/sidebar.tsx`, update the interface at line 44:

```typescript
export interface SidebarSection {
    title?: string;
    /** When set, renders a styled module divider above this section (e.g. "HRMS", "COMPANY ADMIN") */
    moduleSeparator?: string;
    items: SidebarNavItem[];
}
```

- [ ] **Step 2: Add module separator rendering in the ScrollView**

Replace the section rendering block (lines 400-413) with:

```typescript
{sections.map((section) => (
    <View key={section.title ?? section.items[0]?.id ?? 'default'}>
        {/* Module separator */}
        {section.moduleSeparator && (
            <View style={styles.moduleSeparator}>
                <View style={styles.moduleSeparatorLine} />
                <Text className="font-inter text-[9px] font-bold uppercase tracking-[2px] text-primary-500">
                    {section.moduleSeparator}
                </Text>
                <View style={styles.moduleSeparatorLine} />
            </View>
        )}
        <View style={styles.navSection}>
            {section.title && (
                <View style={styles.sectionTitleWrap}>
                    <Text className="mb-1 font-inter text-[10px] font-bold uppercase tracking-widest text-neutral-400">
                        {section.title}
                    </Text>
                </View>
            )}
            {section.items.map((item) => (
                <SidebarNavItem key={item.id} item={item} onClose={close} />
            ))}
        </View>
    </View>
))}
```

- [ ] **Step 3: Add module separator styles**

Add these styles to the `StyleSheet.create({})` block:

```typescript
moduleSeparator: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 16,
    paddingTop: 16,
    paddingBottom: 4,
    gap: 8,
},
moduleSeparatorLine: {
    flex: 1,
    height: 1,
    backgroundColor: colors.primary[100],
},
```

- [ ] **Step 4: Verify the app compiles**

Run: `cd mobile-app && npx expo start --clear` (check for TypeScript errors)

- [ ] **Step 5: Commit**

```bash
git add mobile-app/src/components/ui/sidebar.tsx
git commit -m "feat(mobile): add moduleSeparator support to sidebar component"
```

---

### Task 2: Mobile — Add Module Separators & Reorder Sidebar Sections

**Files:**
- Modify: `mobile-app/src/app/(app)/_layout.tsx:107-410` (sections definition in AppSidebar)

- [ ] **Step 1: Update super admin sections with module separators**

Replace the super admin section block (lines 108-139) with:

```typescript
return [
    {
        items: [
            { id: 'dashboard', label: 'Dashboard', icon: 'dashboard' as const, isActive: pathname === '/', onPress: () => router.push('/') },
        ],
    },
    {
        moduleSeparator: 'Platform Management',
        title: 'Management',
        items: [
            { id: 'companies', label: 'Companies', icon: 'companies' as const, isActive: pathname === '/companies', onPress: () => router.push('/companies') },
        ],
    },
    {
        title: 'Billing',
        items: [
            { id: 'billing-overview', label: 'Overview', icon: 'billing' as const, isActive: pathname === '/billing', onPress: () => router.push('/billing') },
            { id: 'billing-invoices', label: 'Invoices', icon: 'billing' as const, isActive: pathname.startsWith('/billing/invoices'), onPress: () => router.push('/(app)/billing/invoices' as any) },
            { id: 'billing-payments', label: 'Payments', icon: 'billing' as const, isActive: pathname.startsWith('/billing/payments'), onPress: () => router.push('/(app)/billing/payments' as any) },
        ],
    },
    {
        title: 'Administration',
        items: [
            { id: 'audit', label: 'Audit Logs', icon: 'audit' as const, isActive: pathname === '/reports/audit', onPress: () => router.push('/(app)/reports/audit' as any) },
        ],
    },
    {
        moduleSeparator: 'System',
        title: 'System',
        items: [
            { id: 'module-catalogue', label: 'Module Catalogue', icon: 'settings' as const, isActive: false, onPress: () => {} },
            { id: 'platform-monitor', label: 'Platform Monitor', icon: 'dashboard' as const, isActive: false, onPress: () => {} },
            { id: 'users', label: 'User Management', icon: 'users' as const, isActive: false, onPress: () => {} },
            { id: 'settings', label: 'Settings', icon: 'settings' as const, isActive: pathname === '/settings', onPress: () => router.push('/settings') },
            { id: 'support', label: 'Support', icon: 'support' as const, isActive: false, onPress: () => {} },
        ],
    },
];
```

- [ ] **Step 2: Reorder non-super-admin sections with module separators**

Replace the entire `allSections` array (lines 143-404) with the new ordered array. The key changes:
1. Add `moduleSeparator: 'Company Admin'` to the Company section (first section after Dashboard)
2. Move People & Access right after Company
3. Move Configuration after People & Access
4. Move Billing after Configuration
5. Add `moduleSeparator: 'HRMS'` to the first HR section (Org Structure, renamed from "HR & People")
6. Move Self-Service before ESS & Workflows (user-facing before admin-facing)
7. Add `moduleSeparator: 'Operations'` to the Operations section
8. Keep Reports and Support at the bottom

```typescript
const allSections: Array<{ section: SidebarSection; requiredPerm?: string }> = [
    // ── Overview ──
    {
        section: {
            items: [
                { id: 'dashboard', label: 'Dashboard', icon: 'dashboard' as const, onPress: () => router.push('/'), isActive: pathname === '/' },
            ],
        },
    },

    // ══════════ COMPANY ADMIN ══════════
    {
        requiredPerm: 'company:read',
        section: {
            moduleSeparator: 'Company Admin',
            title: 'Company',
            items: [
                { id: 'profile', label: 'Company Profile', icon: 'companies' as const, onPress: () => router.push('/company/profile' as any), isActive: pathname.startsWith('/company/profile') },
                { id: 'locations', label: 'Locations', icon: 'companies' as const, onPress: () => router.push('/company/locations' as any), isActive: pathname.startsWith('/company/locations') },
                { id: 'shifts', label: 'Shifts & Time', icon: 'settings' as const, onPress: () => router.push('/company/shifts' as any), isActive: pathname.startsWith('/company/shifts') },
                { id: 'contacts', label: 'Key Contacts', icon: 'users' as const, onPress: () => router.push('/company/contacts' as any), isActive: pathname.startsWith('/company/contacts') },
            ],
        },
    },
    // People & Access — permission-gated per item
    {
        section: {
            title: 'People & Access',
            items: [
                ...(hasPerm('user:read') ? [{ id: 'users', label: 'User Management', icon: 'users' as const, onPress: () => router.push('/company/users' as any), isActive: pathname.startsWith('/company/users') }] : []),
                ...(hasPerm('role:read') ? [{ id: 'roles', label: 'Roles & Permissions', icon: 'users' as const, onPress: () => router.push('/company/roles' as any), isActive: pathname.startsWith('/company/roles') }] : []),
                ...(hasPerm('role:read') ? [{ id: 'feature-toggles', label: 'Feature Toggles', icon: 'settings' as const, onPress: () => router.push('/company/feature-toggles' as any), isActive: pathname.startsWith('/company/feature-toggles') }] : []),
            ],
        },
    },
    // Configuration — requires company:read
    {
        requiredPerm: 'company:read',
        section: {
            title: 'Configuration',
            items: [
                { id: 'no-series', label: 'Number Series', icon: 'settings' as const, onPress: () => router.push('/company/no-series' as any), isActive: pathname.startsWith('/company/no-series') },
                { id: 'iot-reasons', label: 'IOT Reasons', icon: 'settings' as const, onPress: () => router.push('/company/iot-reasons' as any), isActive: pathname.startsWith('/company/iot-reasons') },
                { id: 'controls', label: 'System Controls', icon: 'settings' as const, onPress: () => router.push('/company/controls' as any), isActive: pathname.startsWith('/company/controls') },
                { id: 'settings', label: 'Settings', icon: 'settings' as const, onPress: () => router.push('/company/settings' as any), isActive: pathname.startsWith('/company/settings') },
            ],
        },
    },
    // Billing — requires company:read
    {
        requiredPerm: 'company:read',
        section: {
            title: 'Billing',
            items: [
                { id: 'billing-overview', label: 'Billing Overview', icon: 'billing' as const, onPress: () => router.push('/company/billing' as any), isActive: pathname === '/company/billing' },
                { id: 'billing-invoices', label: 'Invoices', icon: 'billing' as const, onPress: () => router.push('/company/billing-invoices' as any), isActive: pathname.startsWith('/company/billing-invoices') },
                { id: 'billing-payments', label: 'Payments', icon: 'billing' as const, onPress: () => router.push('/company/billing-payments' as any), isActive: pathname.startsWith('/company/billing-payments') },
            ],
        },
    },

    // ══════════ HRMS ══════════
    {
        requiredPerm: 'hr:read',
        section: {
            moduleSeparator: 'HRMS',
            title: 'Org Structure',
            items: [
                { id: 'departments', label: 'Departments', icon: 'companies' as const, onPress: () => router.push('/company/hr/departments' as any), isActive: pathname.startsWith('/company/hr/departments') },
                { id: 'designations', label: 'Designations', icon: 'users' as const, onPress: () => router.push('/company/hr/designations' as any), isActive: pathname.startsWith('/company/hr/designations') },
                { id: 'grades', label: 'Grades & Bands', icon: 'settings' as const, onPress: () => router.push('/company/hr/grades' as any), isActive: pathname.startsWith('/company/hr/grades') },
                { id: 'emp-types', label: 'Employee Types', icon: 'users' as const, onPress: () => router.push('/company/hr/employee-types' as any), isActive: pathname.startsWith('/company/hr/employee-types') },
                { id: 'cost-centres', label: 'Cost Centres', icon: 'billing' as const, onPress: () => router.push('/company/hr/cost-centres' as any), isActive: pathname.startsWith('/company/hr/cost-centres') },
                { id: 'employees', label: 'Employee Directory', icon: 'users' as const, onPress: () => router.push('/company/hr/employees' as any), isActive: pathname.startsWith('/company/hr/employees') },
            ],
        },
    },
    {
        requiredPerm: 'hr:read',
        section: {
            title: 'Attendance',
            items: [
                { id: 'attendance', label: 'Attendance Dashboard', icon: 'settings' as const, onPress: () => router.push('/company/hr/attendance' as any), isActive: pathname === '/company/hr/attendance' },
                { id: 'holidays', label: 'Holiday Calendar', icon: 'settings' as const, onPress: () => router.push('/company/hr/holidays' as any), isActive: pathname.startsWith('/company/hr/holidays') },
                { id: 'rosters', label: 'Rosters', icon: 'settings' as const, onPress: () => router.push('/company/hr/rosters' as any), isActive: pathname.startsWith('/company/hr/rosters') },
                { id: 'attendance-rules', label: 'Attendance Rules', icon: 'settings' as const, onPress: () => router.push('/company/hr/attendance-rules' as any), isActive: pathname.startsWith('/company/hr/attendance-rules') },
                { id: 'overtime-rules', label: 'Overtime Rules', icon: 'settings' as const, onPress: () => router.push('/company/hr/overtime-rules' as any), isActive: pathname.startsWith('/company/hr/overtime-rules') },
            ],
        },
    },
    {
        requiredPerm: 'hr:read',
        section: {
            title: 'Leave Management',
            items: [
                { id: 'leave-types', label: 'Leave Types', icon: 'settings' as const, onPress: () => router.push('/company/hr/leave-types' as any), isActive: pathname.startsWith('/company/hr/leave-types') },
                { id: 'leave-policies', label: 'Leave Policies', icon: 'settings' as const, onPress: () => router.push('/company/hr/leave-policies' as any), isActive: pathname.startsWith('/company/hr/leave-policies') },
                { id: 'leave-requests', label: 'Leave Requests', icon: 'users' as const, onPress: () => router.push('/company/hr/leave-requests' as any), isActive: pathname.startsWith('/company/hr/leave-requests') },
                { id: 'leave-balances', label: 'Leave Balances', icon: 'billing' as const, onPress: () => router.push('/company/hr/leave-balances' as any), isActive: pathname.startsWith('/company/hr/leave-balances') },
            ],
        },
    },
    {
        requiredPerm: 'hr:read',
        section: {
            title: 'Payroll & Compliance',
            items: [
                { id: 'salary-components', label: 'Salary Components', icon: 'billing' as const, onPress: () => router.push('/company/hr/salary-components' as any), isActive: pathname.startsWith('/company/hr/salary-components') },
                { id: 'salary-structures', label: 'Salary Structures', icon: 'settings' as const, onPress: () => router.push('/company/hr/salary-structures' as any), isActive: pathname.startsWith('/company/hr/salary-structures') },
                { id: 'employee-salary', label: 'Employee Salary', icon: 'billing' as const, onPress: () => router.push('/company/hr/employee-salary' as any), isActive: pathname.startsWith('/company/hr/employee-salary') },
                { id: 'statutory-config', label: 'Statutory Config', icon: 'settings' as const, onPress: () => router.push('/company/hr/statutory-config' as any), isActive: pathname.startsWith('/company/hr/statutory-config') },
                { id: 'tax-config', label: 'Tax & TDS', icon: 'settings' as const, onPress: () => router.push('/company/hr/tax-config' as any), isActive: pathname.startsWith('/company/hr/tax-config') },
                { id: 'bank-config', label: 'Bank Config', icon: 'billing' as const, onPress: () => router.push('/company/hr/bank-config' as any), isActive: pathname.startsWith('/company/hr/bank-config') },
                { id: 'loan-policies', label: 'Loan Policies', icon: 'settings' as const, onPress: () => router.push('/company/hr/loan-policies' as any), isActive: pathname.startsWith('/company/hr/loan-policies') },
                { id: 'loans', label: 'Loans', icon: 'billing' as const, onPress: () => router.push('/company/hr/loans' as any), isActive: pathname.startsWith('/company/hr/loans') },
            ],
        },
    },
    {
        requiredPerm: 'hr:read',
        section: {
            title: 'Payroll Operations',
            items: [
                { id: 'payroll-runs', label: 'Payroll Runs', icon: 'settings' as const, onPress: () => router.push('/company/hr/payroll-runs' as any), isActive: pathname.startsWith('/company/hr/payroll-runs') },
                { id: 'payslips', label: 'Payslips', icon: 'billing' as const, onPress: () => router.push('/company/hr/payslips' as any), isActive: pathname.startsWith('/company/hr/payslips') },
                { id: 'salary-holds', label: 'Salary Holds', icon: 'settings' as const, onPress: () => router.push('/company/hr/salary-holds' as any), isActive: pathname.startsWith('/company/hr/salary-holds') },
                { id: 'salary-revisions', label: 'Salary Revisions', icon: 'billing' as const, onPress: () => router.push('/company/hr/salary-revisions' as any), isActive: pathname.startsWith('/company/hr/salary-revisions') },
                { id: 'statutory-filings', label: 'Statutory Filings', icon: 'settings' as const, onPress: () => router.push('/company/hr/statutory-filings' as any), isActive: pathname.startsWith('/company/hr/statutory-filings') },
                { id: 'payroll-reports', label: 'Payroll Reports', icon: 'billing' as const, onPress: () => router.push('/company/hr/payroll-reports' as any), isActive: pathname.startsWith('/company/hr/payroll-reports') },
            ],
        },
    },
    {
        requiredPerm: 'hr:read',
        section: {
            title: 'Self-Service',
            items: [
                { id: 'my-profile', label: 'My Profile', icon: 'users' as const, onPress: () => router.push('/company/hr/my-profile' as any), isActive: pathname.startsWith('/company/hr/my-profile') },
                { id: 'my-payslips', label: 'My Payslips', icon: 'billing' as const, onPress: () => router.push('/company/hr/my-payslips' as any), isActive: pathname.startsWith('/company/hr/my-payslips') },
                { id: 'my-leave', label: 'My Leave', icon: 'settings' as const, onPress: () => router.push('/company/hr/my-leave' as any), isActive: pathname.startsWith('/company/hr/my-leave') },
                { id: 'my-attendance', label: 'My Attendance', icon: 'settings' as const, onPress: () => router.push('/company/hr/my-attendance' as any), isActive: pathname.startsWith('/company/hr/my-attendance') },
                { id: 'shift-check-in', label: 'Shift Check-In', icon: 'settings' as const, onPress: () => router.push('/company/hr/shift-check-in' as any), isActive: pathname.startsWith('/company/hr/shift-check-in') },
                { id: 'team-view', label: 'Team View (MSS)', icon: 'users' as const, onPress: () => router.push('/company/hr/team-view' as any), isActive: pathname.startsWith('/company/hr/team-view') },
            ],
        },
    },
    {
        requiredPerm: 'hr:read',
        section: {
            title: 'ESS & Workflows',
            items: [
                { id: 'ess-config', label: 'ESS Config', icon: 'settings' as const, onPress: () => router.push('/company/hr/ess-config' as any), isActive: pathname.startsWith('/company/hr/ess-config') },
                { id: 'approval-workflows', label: 'Approval Workflows', icon: 'settings' as const, onPress: () => router.push('/company/hr/approval-workflows' as any), isActive: pathname.startsWith('/company/hr/approval-workflows') },
                { id: 'approval-requests', label: 'Approval Requests', icon: 'users' as const, onPress: () => router.push('/company/hr/approval-requests' as any), isActive: pathname.startsWith('/company/hr/approval-requests') },
                { id: 'notification-templates', label: 'Notification Templates', icon: 'settings' as const, onPress: () => router.push('/company/hr/notification-templates' as any), isActive: pathname.startsWith('/company/hr/notification-templates') },
                { id: 'notification-rules', label: 'Notification Rules', icon: 'settings' as const, onPress: () => router.push('/company/hr/notification-rules' as any), isActive: pathname.startsWith('/company/hr/notification-rules') },
                { id: 'it-declarations', label: 'IT Declarations', icon: 'billing' as const, onPress: () => router.push('/company/hr/it-declarations' as any), isActive: pathname.startsWith('/company/hr/it-declarations') },
            ],
        },
    },
    {
        requiredPerm: 'hr:read',
        section: {
            title: 'Transfers & Promotions',
            items: [
                { id: 'transfers', label: 'Employee Transfers', icon: 'settings' as const, onPress: () => router.push('/company/hr/transfers' as any), isActive: pathname.startsWith('/company/hr/transfers') },
                { id: 'promotions', label: 'Employee Promotions', icon: 'settings' as const, onPress: () => router.push('/company/hr/promotions' as any), isActive: pathname.startsWith('/company/hr/promotions') },
                { id: 'delegates', label: 'Manager Delegation', icon: 'users' as const, onPress: () => router.push('/company/hr/delegates' as any), isActive: pathname.startsWith('/company/hr/delegates') },
            ],
        },
    },
    {
        requiredPerm: 'hr:read',
        section: {
            title: 'Performance',
            items: [
                { id: 'appraisal-cycles', label: 'Appraisal Cycles', icon: 'settings' as const, onPress: () => router.push('/company/hr/appraisal-cycles' as any), isActive: pathname.startsWith('/company/hr/appraisal-cycles') },
                { id: 'goals', label: 'Goals & OKRs', icon: 'settings' as const, onPress: () => router.push('/company/hr/goals' as any), isActive: pathname.startsWith('/company/hr/goals') },
                { id: 'feedback-360', label: '360 Feedback', icon: 'users' as const, onPress: () => router.push('/company/hr/feedback-360' as any), isActive: pathname.startsWith('/company/hr/feedback-360') },
                { id: 'ratings', label: 'Ratings & Calibration', icon: 'settings' as const, onPress: () => router.push('/company/hr/ratings' as any), isActive: pathname.startsWith('/company/hr/ratings') },
                { id: 'skills', label: 'Skills & Mapping', icon: 'settings' as const, onPress: () => router.push('/company/hr/skills' as any), isActive: pathname.startsWith('/company/hr/skills') },
                { id: 'succession', label: 'Succession Planning', icon: 'users' as const, onPress: () => router.push('/company/hr/succession' as any), isActive: pathname.startsWith('/company/hr/succession') },
                { id: 'performance-dashboard', label: 'Performance Dashboard', icon: 'dashboard' as const, onPress: () => router.push('/company/hr/performance-dashboard' as any), isActive: pathname.startsWith('/company/hr/performance-dashboard') },
            ],
        },
    },
    {
        requiredPerm: 'hr:read',
        section: {
            title: 'Recruitment & Training',
            items: [
                { id: 'requisitions', label: 'Job Requisitions', icon: 'settings' as const, onPress: () => router.push('/company/hr/requisitions' as any), isActive: pathname.startsWith('/company/hr/requisitions') },
                { id: 'candidates', label: 'Candidates', icon: 'users' as const, onPress: () => router.push('/company/hr/candidates' as any), isActive: pathname.startsWith('/company/hr/candidates') },
                { id: 'training', label: 'Training Catalogue', icon: 'settings' as const, onPress: () => router.push('/company/hr/training' as any), isActive: pathname.startsWith('/company/hr/training') },
                { id: 'training-nominations', label: 'Training Nominations', icon: 'users' as const, onPress: () => router.push('/company/hr/training-nominations' as any), isActive: pathname.startsWith('/company/hr/training-nominations') },
            ],
        },
    },
    {
        requiredPerm: 'hr:read',
        section: {
            title: 'Exit & Separation',
            items: [
                { id: 'exit-requests', label: 'Exit Requests', icon: 'users' as const, onPress: () => router.push('/company/hr/exit-requests' as any), isActive: pathname.startsWith('/company/hr/exit-requests') },
                { id: 'clearance-dashboard', label: 'Clearance Dashboard', icon: 'settings' as const, onPress: () => router.push('/company/hr/clearance-dashboard' as any), isActive: pathname.startsWith('/company/hr/clearance-dashboard') },
                { id: 'fnf-settlement', label: 'F&F Settlement', icon: 'billing' as const, onPress: () => router.push('/company/hr/fnf-settlement' as any), isActive: pathname.startsWith('/company/hr/fnf-settlement') },
            ],
        },
    },
    {
        requiredPerm: 'hr:read',
        section: {
            title: 'Advanced HR',
            items: [
                { id: 'assets', label: 'Asset Management', icon: 'settings' as const, onPress: () => router.push('/company/hr/assets' as any), isActive: pathname.startsWith('/company/hr/assets') },
                { id: 'expenses', label: 'Expense Claims', icon: 'billing' as const, onPress: () => router.push('/company/hr/expenses' as any), isActive: pathname.startsWith('/company/hr/expenses') },
                { id: 'hr-letters', label: 'HR Letters', icon: 'settings' as const, onPress: () => router.push('/company/hr/hr-letters' as any), isActive: pathname.startsWith('/company/hr/hr-letters') },
                { id: 'grievances', label: 'Grievances', icon: 'users' as const, onPress: () => router.push('/company/hr/grievances' as any), isActive: pathname.startsWith('/company/hr/grievances') },
                { id: 'disciplinary', label: 'Disciplinary Actions', icon: 'settings' as const, onPress: () => router.push('/company/hr/disciplinary' as any), isActive: pathname.startsWith('/company/hr/disciplinary') },
            ],
        },
    },

    // ══════════ OPERATIONS ══════════
    {
        section: {
            moduleSeparator: 'Operations',
            title: 'Operations',
            items: [
                ...(hasPerm('inventory:read') ? [{ id: 'inventory', label: 'Inventory', icon: 'companies' as const, onPress: () => router.push('/company/inventory' as any), isActive: pathname.startsWith('/company/inventory') }] : []),
                ...(hasPerm('production:read') ? [{ id: 'production', label: 'Production', icon: 'settings' as const, onPress: () => router.push('/company/production' as any), isActive: pathname.startsWith('/company/production') }] : []),
                ...(hasPerm('maintenance:read') ? [{ id: 'maintenance', label: 'Maintenance', icon: 'settings' as const, onPress: () => router.push('/company/maintenance' as any), isActive: pathname.startsWith('/company/maintenance') }] : []),
            ],
        },
    },

    // ══════════ REPORTS & SUPPORT ══════════
    {
        requiredPerm: 'audit:read',
        section: {
            title: 'Reports',
            items: [
                { id: 'audit', label: 'Audit Logs', icon: 'audit' as const, onPress: () => router.push('/(app)/reports/audit' as any), isActive: pathname.startsWith('/reports/audit') },
            ],
        },
    },
    {
        section: {
            title: 'Support',
            items: [
                { id: 'support', label: 'Help & Support', icon: 'support' as const, onPress: () => {}, isActive: false },
            ],
        },
    },
];
```

- [ ] **Step 2: Verify the app compiles and sidebar renders correctly**

Run: `cd mobile-app && npx expo start --clear`

- [ ] **Step 3: Commit**

```bash
git add mobile-app/src/app/\(app\)/_layout.tsx
git commit -m "feat(mobile): add module separators and reorder sidebar sections"
```

---

### Task 3: Web — Add Permission-Based Filtering, Module Separators & Reorder

**Files:**
- Modify: `web-system-app/src/layouts/Sidebar.tsx:30-613` (types + NAV_CONFIG)
- Modify: `web-system-app/src/layouts/Sidebar.tsx:625-688` (props + filtering logic)
- Modify: `web-system-app/src/layouts/Sidebar.tsx:757-879` (rendering)

- [ ] **Step 1: Update types to support permissions and module separators**

Replace lines 30-51 with:

```typescript
export type SidebarUserRole = 'super_admin' | 'company_admin' | 'viewer';
/** @deprecated Use SidebarUserRole */
export type UserRole = SidebarUserRole;

interface SubItem {
    label: string;
    path: string;
    badge?: string | number;
    requiredPerm?: string;
}

interface NavSection {
    group: string;
    /** When set, renders a styled module divider above this section */
    moduleSeparator?: string;
    roles?: SidebarUserRole[]; // undefined = visible to all
    /** Permission required for the entire section (checked via checkPermission) */
    requiredPerm?: string;
    items: {
        icon: React.ComponentType<{ size?: number; strokeWidth?: number; className?: string }>;
        label: string;
        path: string;
        badge?: string | number;
        roles?: SidebarUserRole[];
        /** Permission required for this specific item */
        requiredPerm?: string;
        children?: SubItem[];
    }[];
}
```

- [ ] **Step 2: Replace NAV_CONFIG with permission-aware, reordered configuration**

Replace lines 53-613 with the new `NAV_CONFIG` that:
- Adds `requiredPerm` to each section and item where permissions apply
- Adds `moduleSeparator` to module-boundary sections
- Reorders sections to match the standardized order
- Removes the `Modules` section (moved into super admin Platform Management and company admin Configuration)

```typescript
const NAV_CONFIG: NavSection[] = [
    // ── Overview ──
    {
        group: 'Overview',
        items: [
            { icon: LayoutDashboard, label: 'Dashboard', path: '/app/dashboard' },
        ],
    },

    // ══════════ SUPER ADMIN: PLATFORM MANAGEMENT ══════════
    {
        group: 'Platform Management',
        moduleSeparator: 'Platform Management',
        roles: ['super_admin'],
        items: [
            { icon: Building2, label: 'Companies', path: '/app/companies' },
            {
                icon: CreditCard, label: 'Billing', path: '/app/billing',
                children: [
                    { label: 'Overview', path: '/app/billing' },
                    { label: 'Invoices', path: '/app/billing/invoices' },
                    { label: 'Payments', path: '/app/billing/payments' },
                ],
            },
            { icon: ShieldCheck, label: 'Audit Log', path: '/app/reports/audit' },
        ],
    },
    {
        group: 'System',
        moduleSeparator: 'System',
        roles: ['super_admin'],
        items: [
            { icon: Blocks, label: 'Module Catalogue', path: '/app/modules' },
            { icon: Activity, label: 'Platform Monitor', path: '/app/monitor' },
            { icon: UserCog, label: 'User Management', path: '/app/admin/users' },
        ],
    },

    // ══════════ COMPANY ADMIN ══════════
    {
        group: 'Company',
        moduleSeparator: 'Company Admin',
        roles: ['company_admin'],
        requiredPerm: 'company:read',
        items: [
            { icon: Building2, label: 'Company Profile', path: '/app/company/profile', requiredPerm: 'company:read' },
            { icon: MapPin, label: 'Locations', path: '/app/company/locations', requiredPerm: 'company:read' },
            { icon: Clock, label: 'Shifts & Time', path: '/app/company/shifts', requiredPerm: 'company:read' },
            { icon: Users, label: 'Key Contacts', path: '/app/company/contacts', requiredPerm: 'company:read' },
        ],
    },
    {
        group: 'People & Access',
        roles: ['company_admin'],
        items: [
            { icon: UserCog, label: 'User Management', path: '/app/company/users', requiredPerm: 'user:read' },
            { icon: Shield, label: 'Roles & Permissions', path: '/app/company/roles', requiredPerm: 'role:read' },
            { icon: ToggleLeft, label: 'Feature Toggles', path: '/app/company/feature-toggles', requiredPerm: 'role:read' },
        ],
    },
    {
        group: 'Configuration',
        roles: ['company_admin'],
        requiredPerm: 'company:read',
        items: [
            { icon: Hash, label: 'Number Series', path: '/app/company/no-series', requiredPerm: 'company:read' },
            { icon: Cpu, label: 'IOT Reasons', path: '/app/company/iot-reasons', requiredPerm: 'company:read' },
            { icon: SlidersHorizontal, label: 'System Controls', path: '/app/company/controls', requiredPerm: 'company:configure' },
            { icon: Settings, label: 'Settings', path: '/app/company/settings', requiredPerm: 'company:read' },
        ],
    },
    {
        group: 'Billing',
        roles: ['company_admin'],
        requiredPerm: 'company:read',
        items: [
            {
                icon: CreditCard, label: 'Billing', path: '/app/company/billing', requiredPerm: 'company:read',
                children: [
                    { label: 'Overview', path: '/app/company/billing' },
                    { label: 'Invoices', path: '/app/company/billing/invoices' },
                    { label: 'Payments', path: '/app/company/billing/payments' },
                ],
            },
        ],
    },

    // ══════════ HRMS ══════════
    {
        group: 'Org Structure',
        moduleSeparator: 'HRMS',
        roles: ['company_admin'],
        requiredPerm: 'hr:read',
        items: [
            { icon: Building2, label: 'Departments', path: '/app/company/hr/departments', requiredPerm: 'hr:read' },
            { icon: Briefcase, label: 'Designations', path: '/app/company/hr/designations', requiredPerm: 'hr:read' },
            { icon: BarChart3, label: 'Grades & Bands', path: '/app/company/hr/grades', requiredPerm: 'hr:read' },
            { icon: UserCheck, label: 'Employee Types', path: '/app/company/hr/employee-types', requiredPerm: 'hr:read' },
            { icon: Wallet, label: 'Cost Centres', path: '/app/company/hr/cost-centres', requiredPerm: 'hr:read' },
            { icon: Users, label: 'Employee Directory', path: '/app/company/hr/employees', requiredPerm: 'hr:read' },
        ],
    },
    {
        group: 'Attendance',
        roles: ['company_admin'],
        requiredPerm: 'hr:read',
        items: [
            { icon: CalendarCheck, label: 'Attendance Dashboard', path: '/app/company/hr/attendance', requiredPerm: 'hr:read' },
            { icon: Calendar, label: 'Holiday Calendar', path: '/app/company/hr/holidays', requiredPerm: 'hr:read' },
            { icon: CalendarDays, label: 'Rosters', path: '/app/company/hr/rosters', requiredPerm: 'hr:read' },
            { icon: ClipboardList, label: 'Attendance Rules', path: '/app/company/hr/attendance-rules', requiredPerm: 'hr:read' },
            { icon: Timer, label: 'Overtime Rules', path: '/app/company/hr/overtime-rules', requiredPerm: 'hr:read' },
        ],
    },
    {
        group: 'Leave Management',
        roles: ['company_admin'],
        requiredPerm: 'hr:read',
        items: [
            { icon: FileText, label: 'Leave Types', path: '/app/company/hr/leave-types', requiredPerm: 'hr:read' },
            { icon: BookOpen, label: 'Leave Policies', path: '/app/company/hr/leave-policies', requiredPerm: 'hr:read' },
            { icon: Send, label: 'Leave Requests', path: '/app/company/hr/leave-requests', requiredPerm: 'hr:read' },
            { icon: Scale, label: 'Leave Balances', path: '/app/company/hr/leave-balances', requiredPerm: 'hr:read' },
        ],
    },
    {
        group: 'Payroll & Compliance',
        roles: ['company_admin'],
        requiredPerm: 'hr:read',
        items: [
            { icon: DollarSign, label: 'Salary Components', path: '/app/company/hr/salary-components', requiredPerm: 'hr:read' },
            { icon: FileSpreadsheet, label: 'Salary Structures', path: '/app/company/hr/salary-structures', requiredPerm: 'hr:read' },
            { icon: CreditCard, label: 'Employee Salary', path: '/app/company/hr/employee-salary', requiredPerm: 'hr:read' },
            { icon: Shield, label: 'Statutory Config', path: '/app/company/hr/statutory-config', requiredPerm: 'hr:configure' },
            { icon: Calculator, label: 'Tax & TDS', path: '/app/company/hr/tax-config', requiredPerm: 'hr:configure' },
            { icon: Landmark, label: 'Bank Config', path: '/app/company/hr/bank-config', requiredPerm: 'hr:configure' },
            { icon: HandCoins, label: 'Loan Policies', path: '/app/company/hr/loan-policies', requiredPerm: 'hr:read' },
            { icon: Receipt, label: 'Loans', path: '/app/company/hr/loans', requiredPerm: 'hr:read' },
        ],
    },
    {
        group: 'Payroll Operations',
        roles: ['company_admin'],
        requiredPerm: 'hr:read',
        items: [
            { icon: Play, label: 'Payroll Runs', path: '/app/company/hr/payroll-runs', requiredPerm: 'hr:read' },
            { icon: FileText, label: 'Payslips', path: '/app/company/hr/payslips', requiredPerm: 'hr:read' },
            { icon: PauseCircle, label: 'Salary Holds', path: '/app/company/hr/salary-holds', requiredPerm: 'hr:read' },
            { icon: TrendingUp, label: 'Salary Revisions', path: '/app/company/hr/salary-revisions', requiredPerm: 'hr:read' },
            { icon: Stamp, label: 'Statutory Filings', path: '/app/company/hr/statutory-filings', requiredPerm: 'hr:read' },
            { icon: BarChart3, label: 'Payroll Reports', path: '/app/company/hr/payroll-reports', requiredPerm: 'hr:read' },
        ],
    },
    {
        group: 'Self-Service',
        roles: ['company_admin'],
        requiredPerm: 'hr:read',
        items: [
            { icon: UserCircle, label: 'My Profile', path: '/app/company/hr/my-profile', requiredPerm: 'hr:read' },
            { icon: Receipt, label: 'My Payslips', path: '/app/company/hr/my-payslips', requiredPerm: 'hr:read' },
            { icon: CalendarOff, label: 'My Leave', path: '/app/company/hr/my-leave', requiredPerm: 'hr:read' },
            { icon: Clock, label: 'My Attendance', path: '/app/company/hr/my-attendance', requiredPerm: 'hr:read' },
            { icon: LogIn, label: 'Shift Check-In', path: '/app/company/hr/shift-check-in', requiredPerm: 'hr:read' },
            { icon: Users, label: 'Team View', path: '/app/company/hr/team-view', requiredPerm: 'hr:read' },
        ],
    },
    {
        group: 'ESS & Workflows',
        roles: ['company_admin'],
        requiredPerm: 'hr:read',
        items: [
            { icon: Settings2, label: 'ESS Config', path: '/app/company/hr/ess-config', requiredPerm: 'hr:configure' },
            { icon: GitBranch, label: 'Approval Workflows', path: '/app/company/hr/approval-workflows', requiredPerm: 'hr:configure' },
            { icon: Mail, label: 'Notification Templates', path: '/app/company/hr/notification-templates', requiredPerm: 'hr:configure' },
            { icon: BellRing, label: 'Notification Rules', path: '/app/company/hr/notification-rules', requiredPerm: 'hr:configure' },
            { icon: FileCheck, label: 'IT Declarations', path: '/app/company/hr/it-declarations', requiredPerm: 'hr:read' },
        ],
    },
    {
        group: 'Transfers & Promotions',
        roles: ['company_admin'],
        requiredPerm: 'hr:read',
        items: [
            { icon: ArrowLeftRight, label: 'Transfers', path: '/app/company/hr/transfers', requiredPerm: 'hr:read' },
            { icon: TrendingUp, label: 'Promotions', path: '/app/company/hr/promotions', requiredPerm: 'hr:read' },
            { icon: UserCheck, label: 'Delegation', path: '/app/company/hr/delegates', requiredPerm: 'hr:read' },
        ],
    },
    {
        group: 'Performance',
        roles: ['company_admin'],
        requiredPerm: 'hr:read',
        items: [
            { icon: Target, label: 'Appraisal Cycles', path: '/app/company/hr/appraisal-cycles', requiredPerm: 'hr:read' },
            { icon: Flag, label: 'Goals & OKRs', path: '/app/company/hr/goals', requiredPerm: 'hr:read' },
            { icon: MessageSquare, label: '360 Feedback', path: '/app/company/hr/feedback-360', requiredPerm: 'hr:read' },
            { icon: Star, label: 'Ratings & Calibration', path: '/app/company/hr/ratings', requiredPerm: 'hr:read' },
            { icon: Brain, label: 'Skills & Mapping', path: '/app/company/hr/skills', requiredPerm: 'hr:read' },
            { icon: GitFork, label: 'Succession Planning', path: '/app/company/hr/succession', requiredPerm: 'hr:read' },
            { icon: Activity, label: 'Performance Dashboard', path: '/app/company/hr/performance-dashboard', requiredPerm: 'hr:read' },
        ],
    },
    {
        group: 'Recruitment & Training',
        roles: ['company_admin'],
        requiredPerm: 'hr:read',
        items: [
            { icon: Briefcase, label: 'Requisitions', path: '/app/company/hr/requisitions', requiredPerm: 'hr:read' },
            { icon: UserPlus, label: 'Candidates', path: '/app/company/hr/candidates', requiredPerm: 'hr:read' },
            { icon: GraduationCap, label: 'Training', path: '/app/company/hr/training', requiredPerm: 'hr:read' },
            { icon: Award, label: 'Nominations', path: '/app/company/hr/training-nominations', requiredPerm: 'hr:read' },
        ],
    },
    {
        group: 'Exit & Separation',
        roles: ['company_admin'],
        requiredPerm: 'hr:read',
        items: [
            { icon: LogOut, label: 'Exit Requests', path: '/app/company/hr/exit-requests', requiredPerm: 'hr:read' },
            { icon: ClipboardList, label: 'Clearance Dashboard', path: '/app/company/hr/clearance-dashboard', requiredPerm: 'hr:read' },
            { icon: Calculator, label: 'F&F Settlement', path: '/app/company/hr/fnf-settlement', requiredPerm: 'hr:read' },
        ],
    },
    {
        group: 'Advanced HR',
        roles: ['company_admin'],
        requiredPerm: 'hr:read',
        items: [
            { icon: Package, label: 'Assets', path: '/app/company/hr/assets', requiredPerm: 'hr:read' },
            { icon: Receipt, label: 'Expenses', path: '/app/company/hr/expenses', requiredPerm: 'hr:read' },
            { icon: FileSignature, label: 'Letters', path: '/app/company/hr/hr-letters', requiredPerm: 'hr:read' },
            { icon: AlertTriangle, label: 'Grievances', path: '/app/company/hr/grievances', requiredPerm: 'hr:read' },
            { icon: Gavel, label: 'Discipline', path: '/app/company/hr/disciplinary', requiredPerm: 'hr:read' },
        ],
    },

    // ══════════ OPERATIONS ══════════
    {
        group: 'Operations',
        moduleSeparator: 'Operations',
        roles: ['company_admin'],
        items: [
            { icon: Package, label: 'Inventory', path: '/app/inventory', requiredPerm: 'inventory:read' },
            {
                icon: Wrench, label: 'Maintenance', path: '/app/maintenance', requiredPerm: 'maintenance:read',
                children: [
                    { label: 'Work Orders', path: '/app/maintenance/orders' },
                    { label: 'Machine Registry', path: '/app/maintenance/machines' },
                ],
            },
            { icon: ClipboardList, label: 'Production', path: '/app/production', requiredPerm: 'production:read' },
        ],
    },

    // ══════════ REPORTS ══════════
    {
        group: 'Reports',
        roles: ['company_admin'],
        requiredPerm: 'audit:read',
        items: [
            { icon: FileText, label: 'Audit Logs', path: '/app/reports/audit', requiredPerm: 'audit:read' },
        ],
    },
];
```

- [ ] **Step 3: Update Sidebar props to accept permissions**

Replace the `SidebarProps` interface (line 625) with:

```typescript
interface SidebarProps {
    collapsed: boolean;
    onCollapse: (v: boolean) => void;
    role?: SidebarUserRole;
    permissions?: string[];
}
```

Update the function signature (line 631):

```typescript
export function Sidebar({ collapsed, onCollapse, role = 'super_admin', permissions = [] }: SidebarProps) {
```

- [ ] **Step 4: Update filtering logic to use permissions**

Replace the filtering block (lines 682-688) with:

```typescript
// Import at top of file
// import { checkPermission } from '@/lib/api/auth';

const hasPerm = (perm: string) => checkPermission(permissions, perm);

// Filter sections by role AND permissions
const visibleSections = NAV_CONFIG.filter((s) => {
    // Role gate
    if (s.roles && !s.roles.includes(role)) return false;
    // Permission gate (super_admin has '*' which passes all checks)
    if (s.requiredPerm && !hasPerm(s.requiredPerm)) return false;
    return true;
}).map((s) => ({
    ...s,
    items: s.items.filter((i) => {
        if (i.roles && !i.roles.includes(role)) return false;
        if (i.requiredPerm && !hasPerm(i.requiredPerm)) return false;
        return true;
    }),
})).filter((s) => s.items.length > 0);
```

Add the import at the top of the file (after line 23):

```typescript
import { checkPermission } from '@/lib/api/auth';
```

- [ ] **Step 5: Add module separator rendering in the nav section**

Replace the nav rendering block (lines 757-879) — specifically the section map. Inside the `<nav>` element, replace `{visibleSections.map((section) => (` block with:

```tsx
{visibleSections.map((section) => (
    <div key={section.group}>
        {/* Module Separator */}
        {section.moduleSeparator && !collapsed && (
            <div className="flex items-center gap-2 px-5 pt-5 pb-1">
                <div className="flex-1 h-px bg-primary-100 dark:bg-primary-900/40" />
                <span className="text-[9px] font-bold uppercase tracking-[2px] text-primary-500 dark:text-primary-400 whitespace-nowrap">
                    {section.moduleSeparator}
                </span>
                <div className="flex-1 h-px bg-primary-100 dark:bg-primary-900/40" />
            </div>
        )}
        {collapsed && section.moduleSeparator && (
            <div className="mx-3 mt-3 mb-1 h-px bg-primary-100 dark:bg-primary-900/40" />
        )}

        <div className={cn('mb-1', collapsed ? 'px-2' : 'px-3')}>
            {/* Section label */}
            {!collapsed && (
                <p className="px-3 pt-3 pb-1.5 text-[10px] font-bold uppercase tracking-widest text-neutral-400 dark:text-neutral-500">
                    {section.group}
                </p>
            )}
            {collapsed && <div className="h-3" />}

            {section.items.map((item) => {
                // ... existing item rendering code (unchanged)
            })}
        </div>
    </div>
))}
```

- [ ] **Step 6: Commit**

```bash
git add web-system-app/src/layouts/Sidebar.tsx
git commit -m "feat(web): add permission-based RBAC filtering, module separators, and reorder sidebar"
```

---

### Task 4: Web — Pass Permissions from Auth Store to Sidebar

**Files:**
- Modify: `web-system-app/src/layouts/DashboardLayout.tsx`

- [ ] **Step 1: Pass permissions to Sidebar**

Update `DashboardLayout.tsx` to read permissions from auth store and pass them:

```typescript
import { useState } from 'react';
import { Outlet } from 'react-router-dom';
import { Sidebar } from './Sidebar';
import { TopBar } from './TopBar';
import { useAuthStore } from '@/store/useAuthStore';
import type { UserRole } from '@/store/useAuthStore';
import type { SidebarUserRole } from './Sidebar';

/** Map auth store role (hyphen) to sidebar role (underscore). */
function toSidebarRole(role: UserRole | null): SidebarUserRole {
    switch (role) {
        case 'super-admin': return 'super_admin';
        case 'company-admin': return 'company_admin';
        case 'user': return 'viewer';
        default: return 'viewer';
    }
}

export function DashboardLayout() {
    const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
    const userRole = useAuthStore((s) => s.userRole);
    const permissions = useAuthStore((s) => s.permissions);

    return (
        <div className="flex h-screen w-full overflow-hidden bg-[var(--background)] dark:bg-neutral-950 transition-colors">
            <Sidebar
                collapsed={sidebarCollapsed}
                onCollapse={setSidebarCollapsed}
                role={toSidebarRole(userRole)}
                permissions={permissions}
            />
            <main className="flex-1 flex flex-col min-w-0 bg-[var(--background)] dark:bg-neutral-950 transition-colors">
                <TopBar sidebarCollapsed={sidebarCollapsed} />
                <div className="flex-1 overflow-y-auto p-4 md:p-8 custom-scrollbar">
                    <div className="max-w-7xl mx-auto">
                        <Outlet />
                    </div>
                </div>
            </main>
        </div>
    );
}
```

- [ ] **Step 2: Verify web app compiles**

Run: `cd web-system-app && npm run dev`

- [ ] **Step 3: Commit**

```bash
git add web-system-app/src/layouts/DashboardLayout.tsx
git commit -m "feat(web): pass permissions from auth store to sidebar for RBAC filtering"
```

---

### Task 5: Verification & Final Commit

**Files:** All modified files from Tasks 1-4

- [ ] **Step 1: Verify mobile TypeScript compilation**

Run: `cd mobile-app && npx tsc --noEmit`
Expected: No errors

- [ ] **Step 2: Verify web TypeScript compilation**

Run: `cd web-system-app && npx tsc --noEmit`
Expected: No errors

- [ ] **Step 3: Test with different permission sets mentally**

Verify these scenarios by tracing the code:
- **Super admin** (permissions: `['*']`): Should see Dashboard + Platform Management + System sections
- **Company admin with all permissions** (permissions: `['company:*', 'hr:*', 'user:*', 'role:*', 'audit:*']`): Should see all Company Admin + HRMS + Reports sections
- **Company admin with only company:read** (permissions: `['company:read']`): Should see only Company section + Configuration (except System Controls which needs `company:configure`) + Billing. No HRMS, no People & Access, no Reports
- **Company admin with only hr:read** (permissions: `['hr:read']`): Should see all HRMS sections but NOT Company, Configuration, Billing, People & Access, or Reports
- **Viewer with no permissions** (permissions: `[]`): Should see only Dashboard and Support

- [ ] **Step 4: Final commit if any remaining changes**

```bash
git add -A
git commit -m "feat: complete sidebar RBAC + module separation across web and mobile"
```
