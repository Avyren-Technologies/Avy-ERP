# Super Admin Sprint 1-3 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Complete Sprint 1 (toast, error handling, sidebar fixes), Sprint 2 (KPI navigation, skeletons, empty states), and Sprint 3 (audit log backend + frontend for both platforms).

**Architecture:** Three codebases — mobile-app (Expo/RN), web-system-app (Vite/React/Electron), avy-erp-backend (Express/Prisma). All share the same backend API. Mobile uses `react-native-flash-message` (already installed). Web needs `sonner` (lightweight, styled). Backend audit log needs a dedicated service/controller/routes module following the billing module pattern.

**Tech Stack:** TypeScript, React Native (Expo 54), React 19, Express, Prisma, TanStack React Query, Zustand, Zod, `react-native-flash-message`, `sonner`

**Shorthand Paths:**
- `M/` = `mobile-app/src/`
- `W/` = `web-system-app/src/`
- `B/` = `avy-erp-backend/src/`

---

## File Structure

### New Files
| File | Purpose |
|------|---------|
| `W/lib/toast.tsx` | Sonner provider + `showSuccess`/`showError` helpers for web |
| `M/components/ui/toast.tsx` | `showSuccess`/`showInfo` helpers wrapping `showMessage` for mobile |
| `M/components/ui/empty-state.tsx` | Reusable empty state component for mobile |
| `W/components/ui/EmptyState.tsx` | Reusable empty state component for web |
| `W/components/ui/Skeleton.tsx` | Skeleton loading component for web |
| `B/core/audit/audit.service.ts` | Audit log query service |
| `B/core/audit/audit.controller.ts` | Audit log HTTP controller |
| `B/core/audit/audit.routes.ts` | Audit log route definitions |
| `B/core/audit/__tests__/audit.service.test.ts` | Audit service tests |
| `M/lib/api/audit.ts` | Mobile audit log API functions |
| `M/features/super-admin/api/use-audit-queries.ts` | Mobile audit log React Query hooks |
| `M/features/super-admin/audit-log-screen.tsx` | Mobile audit log screen |
| `M/app/(app)/reports/audit.tsx` | Mobile audit log route file |
| `W/lib/api/audit.ts` | Web audit log API functions |
| `W/features/super-admin/api/use-audit-queries.ts` | Web audit log React Query hooks |
| `W/features/super-admin/AuditLogScreen.tsx` | Web audit log screen |

### Modified Files
| File | Changes |
|------|---------|
| `M/components/ui/utils.tsx` | Add `showSuccess`, `showInfo` helpers |
| `M/components/ui/index.tsx` | Export new components (EmptyState, toast helpers) |
| `M/features/super-admin/dashboard-screen.tsx` | Add KPI tap-to-navigate, "View All" links, skeleton loading |
| `M/features/super-admin/company-list-screen.tsx` | Add infinite scroll, skeleton loading, improved empty state |
| `M/features/super-admin/company-detail-screen.tsx` | Wire edit modal sections, add skeleton loading |
| `M/features/super-admin/billing-overview-screen.tsx` | Add skeleton loading, empty states |
| `M/components/ui/sidebar.tsx` | Fix billing section links (only show existing screens) |
| `M/lib/api/client.tsx` | Add 403 user-facing error toast |
| `W/App.tsx` | Add Toaster provider, audit log route |
| `W/features/super-admin/DashboardScreen.tsx` | Add KPI tap-to-navigate, "View All" links, skeleton loading |
| `W/features/super-admin/CompanyListScreen.tsx` | Add skeleton loading, improved empty state |
| `W/features/super-admin/CompanyDetailScreen.tsx` | Add skeleton loading |
| `W/features/super-admin/BillingOverviewScreen.tsx` | Add skeleton loading, empty states |
| `W/layouts/Sidebar.tsx` | Fix billing sub-items (remove non-existent routes) |
| `W/lib/api/client.ts` | Add 403 toast feedback |
| `B/app/routes.ts` | Register audit routes |

---

## Task 1: Install & Configure Toast — Web App

**Files:**
- Create: `W/lib/toast.tsx`
- Modify: `W/App.tsx`
- Modify: `W/features/super-admin/tenant-onboarding/TenantOnboardingWizard.tsx` (or `AddCompanyWizard.tsx`)

- [ ] **Step 1: Install sonner**

```bash
cd /Users/chetan/Documents/Avyren-Technologies/Products/Mobile-ERP/web-system-app
pnpm add sonner
```

- [ ] **Step 2: Create toast helper**

Create `W/lib/toast.tsx`:
```tsx
import { toast } from 'sonner';

export function showSuccess(message: string, description?: string) {
  toast.success(message, { description });
}

export function showError(message: string, description?: string) {
  toast.error(message, { description, duration: 5000 });
}

export function showInfo(message: string, description?: string) {
  toast.info(message, { description });
}

export function showWarning(message: string, description?: string) {
  toast.warning(message, { description, duration: 5000 });
}

export function showApiError(error: unknown) {
  const msg = extractErrorMessage(error);
  toast.error('Request Failed', { description: msg, duration: 5000 });
}

function extractErrorMessage(error: unknown): string {
  if (error && typeof error === 'object' && 'response' in error) {
    const resp = (error as any).response?.data;
    if (typeof resp?.message === 'string') return resp.message;
    if (typeof resp?.error === 'string') return resp.error;
  }
  if (error instanceof Error) return error.message;
  return 'Something went wrong';
}
```

- [ ] **Step 3: Add Toaster to App.tsx**

In `W/App.tsx`, import and add `<Toaster />` inside the router:
```tsx
import { Toaster } from 'sonner';

// Inside the return, after <Routes>...</Routes>:
<Toaster
  position="top-right"
  richColors
  closeButton
  toastOptions={{
    style: { fontFamily: 'Inter, system-ui, sans-serif' },
  }}
/>
```

- [ ] **Step 4: Wire toast to existing screens**

In `AddCompanyWizard.tsx` (or wherever the TODO comment is), replace the TODO with:
```tsx
import { showSuccess } from '@/lib/toast';
// In onSuccess callback:
showSuccess('Company Created', `${companyName} has been onboarded successfully.`);
```

In `CompanyDetailScreen.tsx`, add success toasts after mutation success callbacks:
```tsx
import { showSuccess } from '@/lib/toast';
// After suspend/delete success:
showSuccess('Status Updated', 'Company has been suspended.');
showSuccess('Company Deleted', 'Company has been permanently removed.');
```

In `CompanyDetailEditModal.tsx`, add success toast after save:
```tsx
import { showSuccess } from '@/lib/toast';
// After successful section update:
showSuccess('Section Updated', `${sectionLabel} has been saved.`);
```

- [ ] **Step 5: Verify toast displays correctly**

Run: `cd web-system-app && pnpm dev`
Test: Suspend a company, edit a section, create a company — confirm toasts appear top-right with correct colors.

- [ ] **Step 6: Commit**

```bash
git add -A && git commit -m "feat(web): add sonner toast system with success/error helpers"
```

---

## Task 2: Wire Toast Helpers — Mobile App

**Files:**
- Modify: `M/components/ui/utils.tsx`
- Modify: `M/features/super-admin/company-detail-screen.tsx`
- Modify: `M/features/super-admin/tenant-onboarding/index.tsx`
- Modify: `M/features/super-admin/billing-overview-screen.tsx`

- [ ] **Step 1: Add showSuccess and showInfo to utils.tsx**

In `M/components/ui/utils.tsx`, add:
```tsx
export function showSuccess(message: string, description?: string) {
  showMessage({
    message,
    description,
    type: 'success',
    duration: 3000,
    icon: 'success',
  });
}

export function showInfo(message: string, description?: string) {
  showMessage({
    message,
    description,
    type: 'info',
    duration: 3000,
    icon: 'info',
  });
}

export function showWarning(message: string, description?: string) {
  showMessage({
    message,
    description,
    type: 'warning',
    duration: 4000,
    icon: 'warning',
  });
}
```

- [ ] **Step 2: Wire success toasts to company-detail-screen.tsx**

After status mutation `onSuccess`:
```tsx
import { showSuccess } from '@/components/ui/utils';
// onSuccess for suspend: showSuccess('Status Updated', 'Company has been suspended.');
// onSuccess for delete: showSuccess('Company Deleted', 'Company removed successfully.');
```

- [ ] **Step 3: Wire success toast to onboarding wizard**

In `M/features/super-admin/tenant-onboarding/index.tsx`, after successful onboard:
```tsx
import { showSuccess } from '@/components/ui/utils';
// After onboardMutation success: showSuccess('Company Created', 'Tenant onboarded successfully.');
```

- [ ] **Step 4: Commit**

```bash
git add -A && git commit -m "feat(mobile): add showSuccess/showInfo/showWarning toast helpers and wire to screens"
```

---

## Task 3: API Error Handling — 403 Toast Feedback

**Files:**
- Modify: `M/lib/api/client.tsx`
- Modify: `W/lib/api/client.ts`

- [ ] **Step 1: Add 403 handling to mobile API client**

In `M/lib/api/client.tsx`, inside the response error interceptor, add a check before the 401 TOKEN_EXPIRED logic:
```tsx
import { showErrorMessage, showWarning } from '@/components/ui/utils';

// Add this BEFORE the 401 handling:
if (error.response?.status === 403) {
  showWarning('Access Denied', 'You do not have permission to perform this action.');
  return Promise.reject(error);
}

if (error.response?.status && error.response.status >= 500) {
  showErrorMessage('Server error. Please try again later.');
}
```

- [ ] **Step 2: Add 403 handling to web API client**

In `W/lib/api/client.ts`, inside the response error interceptor, add:
```tsx
import { showError, showWarning } from '@/lib/toast';

// Add BEFORE the 401 TOKEN_EXPIRED handling:
if (error.response?.status === 403) {
  showWarning('Access Denied', 'You do not have permission to perform this action.');
  return Promise.reject(error);
}

if (error.response?.status && error.response.status >= 500) {
  showError('Server Error', 'Something went wrong. Please try again later.');
}
```

- [ ] **Step 3: Commit**

```bash
git add -A && git commit -m "feat: add 403 permission denied and 5xx error toasts to API clients"
```

---

## Task 4: Fix Sidebar Billing Links

**Files:**
- Modify: `M/components/ui/sidebar.tsx`
- Modify: `W/layouts/Sidebar.tsx`

- [ ] **Step 1: Fix mobile sidebar billing section**

In `M/components/ui/sidebar.tsx`, find where sidebar sections are defined/passed. The billing section should only list "Billing Overview" (the only screen that exists). Remove or comment out any links to invoices, transactions, revenue, subscriptions that don't have screens yet. If the sections are passed as props from `_layout.tsx`, fix them there instead.

Look for the billing nav item and ensure its `onPress` navigates to `/(app)/billing`. Remove sub-items that are dead links.

- [ ] **Step 2: Fix web sidebar billing sub-items**

In `W/layouts/Sidebar.tsx`, find the Management > Billing section. It currently has sub-items: Overview, Invoices, Transactions. Remove "Invoices" and "Transactions" since those screens don't exist yet. Keep only "Overview" pointing to `/app/billing`.

Find the section in the `navSections` array:
```tsx
// Change from:
{ label: 'Billing', icon: CreditCard, children: [
  { label: 'Overview', path: '/app/billing' },
  { label: 'Invoices', path: '/app/billing/invoices' },
  { label: 'Transactions', path: '/app/billing/transactions' },
]}
// Change to:
{ label: 'Billing', icon: CreditCard, path: '/app/billing' }
// OR keep as expandable with only Overview:
{ label: 'Billing', icon: CreditCard, children: [
  { label: 'Overview', path: '/app/billing' },
]}
```

- [ ] **Step 3: Commit**

```bash
git add -A && git commit -m "fix: remove dead billing sub-links from sidebars on both platforms"
```

---

## Task 5: KPI Tap-to-Navigate + "View All" Links — Mobile

**Files:**
- Modify: `M/features/super-admin/dashboard-screen.tsx`

- [ ] **Step 1: Make KPI cards pressable with navigation**

In `dashboard-screen.tsx`, find the `KPICard` component or the grid rendering KPI cards. Wrap each card in a `Pressable` (or `TouchableOpacity`) and add `onPress` navigation:

```tsx
import { useRouter } from 'expo-router';
const router = useRouter();

// Define KPI navigation targets:
const kpiNavTargets: Record<string, string> = {
  'Active Companies': '/(app)/companies',
  'Total Users': '/(app)/companies', // no dedicated user screen yet
  'Monthly Revenue': '/(app)/billing',
  'Active Modules': '/(app)/companies',
};

// Wrap each KPI card render with Pressable:
<Pressable onPress={() => router.push(kpiNavTargets[kpi.title] as any)}>
  {/* existing card content */}
</Pressable>
```

- [ ] **Step 2: Add "View All" links to each section**

For **Alerts section** — add a "View All" pressable in the section header:
```tsx
<Pressable onPress={() => router.push('/(app)/reports/audit' as any)}>
  <Text className="font-inter" style={{ color: colors.primary[600], fontSize: 13 }}>View All</Text>
</Pressable>
```

For **Recent Activity** — wire the existing "See All" button:
```tsx
// The seeAllButton already exists — wire its onPress:
onPress={() => router.push('/(app)/reports/audit' as any)}
```

For **Tenant Health / Companies table** — add "View All":
```tsx
onPress={() => router.push('/(app)/companies' as any)}
```

For **Quick Actions** — wire "Generate Invoice" to `/(app)/billing` and "View Audit Logs" to `/(app)/reports/audit`:
```tsx
// In the quickActions array, update onPress for each:
{ label: 'Generate Invoice', onPress: () => router.push('/(app)/billing' as any) },
{ label: 'View Audit Logs', onPress: () => router.push('/(app)/reports/audit' as any) },
```

- [ ] **Step 3: Commit**

```bash
git add -A && git commit -m "feat(mobile): add KPI tap-to-navigate and View All links on dashboard"
```

---

## Task 6: KPI Tap-to-Navigate + "View All" Links — Web

**Files:**
- Modify: `W/features/super-admin/DashboardScreen.tsx`

- [ ] **Step 1: Make KPI cards clickable**

In `DashboardScreen.tsx`, wrap each KPI card with a link or add `onClick` with `useNavigate`:

```tsx
import { useNavigate } from 'react-router-dom';
const navigate = useNavigate();

const kpiNavTargets: Record<string, string> = {
  'Active Companies': '/app/companies',
  'Total Users': '/app/companies',
  'Monthly Revenue': '/app/billing',
  'Active Modules': '/app/modules',
};

// Add onClick and cursor-pointer to each KPI card div:
<div
  key={kpi.title}
  onClick={() => navigate(kpiNavTargets[kpi.title])}
  style={{ cursor: 'pointer' }}
  // ... existing styles
>
```

- [ ] **Step 2: Wire "View All" buttons**

For **Recent Activity** section — find "View All Activity" button, set onClick:
```tsx
onClick={() => navigate('/app/reports/audit')}
```

For **Recent Tenants** section — add or wire "View All" link:
```tsx
onClick={() => navigate('/app/companies')}
```

- [ ] **Step 3: Commit**

```bash
git add -A && git commit -m "feat(web): add KPI tap-to-navigate and View All links on dashboard"
```

---

## Task 7: Empty State Component — Both Platforms

**Files:**
- Create: `M/components/ui/empty-state.tsx`
- Create: `W/components/ui/EmptyState.tsx`
- Modify: `M/components/ui/index.tsx`

- [ ] **Step 1: Create mobile EmptyState component**

Create `M/components/ui/empty-state.tsx`:
```tsx
import React from 'react';
import { Pressable, StyleSheet, View } from 'react-native';
import Animated, { FadeIn } from 'react-native-reanimated';
import Svg, { Circle, Line, Path } from 'react-native-svg';
import { Text } from '@/components/ui/text';
import colors from '@/components/ui/colors';

interface EmptyStateProps {
  icon?: 'search' | 'list' | 'error' | 'inbox';
  title: string;
  message?: string;
  action?: { label: string; onPress: () => void };
}

function EmptyIcon({ type }: { type: string }) {
  const color = colors.neutral[300];
  // Simple SVG icons for each type
  if (type === 'search') {
    return (
      <Svg width={64} height={64} viewBox="0 0 24 24" fill="none">
        <Circle cx={11} cy={11} r={7} stroke={color} strokeWidth={2} />
        <Line x1={16.5} y1={16.5} x2={21} y2={21} stroke={color} strokeWidth={2} strokeLinecap="round" />
      </Svg>
    );
  }
  if (type === 'error') {
    return (
      <Svg width={64} height={64} viewBox="0 0 24 24" fill="none">
        <Circle cx={12} cy={12} r={10} stroke={colors.danger[300]} strokeWidth={2} />
        <Line x1={12} y1={8} x2={12} y2={12} stroke={colors.danger[300]} strokeWidth={2} strokeLinecap="round" />
        <Circle cx={12} cy={16} r={1} fill={colors.danger[300]} />
      </Svg>
    );
  }
  // Default: inbox/list
  return (
    <Svg width={64} height={64} viewBox="0 0 24 24" fill="none">
      <Path d="M3 8l4-4h10l4 4v10a2 2 0 01-2 2H5a2 2 0 01-2-2V8z" stroke={color} strokeWidth={2} />
      <Path d="M3 8h6l2 3h2l2-3h6" stroke={color} strokeWidth={2} />
    </Svg>
  );
}

export function EmptyState({ icon = 'list', title, message, action }: EmptyStateProps) {
  return (
    <Animated.View entering={FadeIn.duration(300)} style={styles.container}>
      <EmptyIcon type={icon} />
      <Text className="font-inter" style={styles.title}>{title}</Text>
      {message && <Text className="font-inter" style={styles.message}>{message}</Text>}
      {action && (
        <Pressable onPress={action.onPress} style={styles.actionButton}>
          <Text className="font-inter" style={styles.actionText}>{action.label}</Text>
        </Pressable>
      )}
    </Animated.View>
  );
}

const styles = StyleSheet.create({
  container: { alignItems: 'center', justifyContent: 'center', paddingVertical: 48, paddingHorizontal: 24, gap: 12 },
  title: { fontSize: 16, fontWeight: '600', color: colors.neutral[600], textAlign: 'center' },
  message: { fontSize: 14, color: colors.neutral[400], textAlign: 'center', maxWidth: 280 },
  actionButton: { marginTop: 8, paddingHorizontal: 20, paddingVertical: 10, backgroundColor: colors.primary[600], borderRadius: 8 },
  actionText: { color: '#fff', fontSize: 14, fontWeight: '600' },
});
```

Don't forget to add `import { Pressable } from 'react-native';` at the top.

- [ ] **Step 2: Create web EmptyState component**

Create `W/components/ui/EmptyState.tsx`:
```tsx
import { Inbox, Search, AlertCircle, FileText } from 'lucide-react';

interface EmptyStateProps {
  icon?: 'search' | 'list' | 'error' | 'inbox';
  title: string;
  message?: string;
  action?: { label: string; onClick: () => void };
}

const icons = {
  search: Search,
  list: FileText,
  error: AlertCircle,
  inbox: Inbox,
};

export function EmptyState({ icon = 'list', title, message, action }: EmptyStateProps) {
  const Icon = icons[icon];
  return (
    <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', padding: '48px 24px', gap: 12 }}>
      <Icon size={48} style={{ color: '#cbd5e1' }} />
      <p style={{ fontSize: 16, fontWeight: 600, color: '#475569', margin: 0 }}>{title}</p>
      {message && <p style={{ fontSize: 14, color: '#94a3b8', margin: 0, maxWidth: 320, textAlign: 'center' }}>{message}</p>}
      {action && (
        <button
          onClick={action.onClick}
          style={{ marginTop: 8, padding: '8px 20px', backgroundColor: '#4F46E5', color: '#fff', border: 'none', borderRadius: 8, fontSize: 14, fontWeight: 600, cursor: 'pointer' }}
        >
          {action.label}
        </button>
      )}
    </div>
  );
}
```

- [ ] **Step 3: Export EmptyState from mobile ui/index.tsx**

Add to `M/components/ui/index.tsx`:
```tsx
export * from './empty-state';
```

- [ ] **Step 4: Commit**

```bash
git add -A && git commit -m "feat: add EmptyState component for both mobile and web"
```

---

## Task 8: Skeleton Loading Component — Web App

**Files:**
- Create: `W/components/ui/Skeleton.tsx`

- [ ] **Step 1: Create web Skeleton component**

Create `W/components/ui/Skeleton.tsx`:
```tsx
import { CSSProperties } from 'react';

interface SkeletonProps {
  width?: string | number;
  height?: string | number;
  borderRadius?: number;
  style?: CSSProperties;
}

const shimmerKeyframes = `
@keyframes skeleton-shimmer {
  0% { background-position: -200px 0; }
  100% { background-position: calc(200px + 100%) 0; }
}
`;

// Inject keyframes once
if (typeof document !== 'undefined' && !document.getElementById('skeleton-styles')) {
  const style = document.createElement('style');
  style.id = 'skeleton-styles';
  style.textContent = shimmerKeyframes;
  document.head.appendChild(style);
}

export function Skeleton({ width = '100%', height = 16, borderRadius = 6, style }: SkeletonProps) {
  return (
    <div
      style={{
        width,
        height,
        borderRadius,
        background: 'linear-gradient(90deg, #e2e8f0 25%, #f1f5f9 50%, #e2e8f0 75%)',
        backgroundSize: '200px 100%',
        animation: 'skeleton-shimmer 1.5s ease-in-out infinite',
        ...style,
      }}
    />
  );
}

export function SkeletonCard() {
  return (
    <div style={{ padding: 16, borderRadius: 12, border: '1px solid #e2e8f0', display: 'flex', flexDirection: 'column', gap: 12 }}>
      <div style={{ display: 'flex', gap: 12, alignItems: 'center' }}>
        <Skeleton width={40} height={40} borderRadius={20} />
        <div style={{ flex: 1, display: 'flex', flexDirection: 'column', gap: 6 }}>
          <Skeleton width="60%" height={14} />
          <Skeleton width="40%" height={12} />
        </div>
      </div>
      <Skeleton height={12} />
      <Skeleton width="80%" height={12} />
    </div>
  );
}

export function SkeletonTable({ rows = 5, cols = 4 }: { rows?: number; cols?: number }) {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
      {Array.from({ length: rows }).map((_, i) => (
        <div key={i} style={{ display: 'flex', gap: 16, padding: '12px 16px', borderBottom: '1px solid #f1f5f9' }}>
          {Array.from({ length: cols }).map((_, j) => (
            <Skeleton key={j} width={j === 0 ? '30%' : '20%'} height={14} />
          ))}
        </div>
      ))}
    </div>
  );
}

export function SkeletonKPIGrid({ count = 4 }: { count?: number }) {
  return (
    <div style={{ display: 'grid', gridTemplateColumns: `repeat(${Math.min(count, 4)}, 1fr)`, gap: 16 }}>
      {Array.from({ length: count }).map((_, i) => (
        <div key={i} style={{ padding: 20, borderRadius: 12, border: '1px solid #e2e8f0', display: 'flex', flexDirection: 'column', gap: 10 }}>
          <Skeleton width={100} height={12} />
          <Skeleton width={80} height={28} />
          <Skeleton width={60} height={12} />
        </div>
      ))}
    </div>
  );
}
```

- [ ] **Step 2: Commit**

```bash
git add -A && git commit -m "feat(web): add Skeleton, SkeletonCard, SkeletonTable, SkeletonKPIGrid components"
```

---

## Task 9: Add Skeletons + Empty States to Dashboard — Mobile

**Files:**
- Modify: `M/features/super-admin/dashboard-screen.tsx`

- [ ] **Step 1: Add skeleton loading state to dashboard**

In `dashboard-screen.tsx`, the hooks `useSuperAdminStats()` and `useRecentActivity()` return `isLoading`. Use the existing `Skeleton` component from `@/components/ui/skeleton`:

```tsx
import { Skeleton, SkeletonCard } from '@/components/ui/skeleton';
import { EmptyState } from '@/components/ui/empty-state';

// In the KPI section, when stats are loading:
{statsQuery.isLoading ? (
  <Skeleton isLoading={true} layout={[
    { key: 'kpi1', width: CARD_WIDTH, height: 100, marginRight: 12 },
    { key: 'kpi2', width: CARD_WIDTH, height: 100 },
    { key: 'kpi3', width: CARD_WIDTH, height: 100, marginRight: 12, marginTop: 12 },
    { key: 'kpi4', width: CARD_WIDTH, height: 100, marginTop: 12 },
  ]}>
    <View />
  </Skeleton>
) : (
  // existing KPI grid
)}

// For activity feed when empty:
{!activityQuery.isLoading && activities.length === 0 && (
  <EmptyState icon="inbox" title="No recent activity" message="Activity will appear here as actions are performed." />
)}
```

- [ ] **Step 2: Commit**

```bash
git add -A && git commit -m "feat(mobile): add skeleton loading and empty states to dashboard"
```

---

## Task 10: Add Skeletons + Empty States to Dashboard — Web

**Files:**
- Modify: `W/features/super-admin/DashboardScreen.tsx`

- [ ] **Step 1: Add skeleton loading states**

```tsx
import { SkeletonKPIGrid, SkeletonTable, Skeleton } from '@/components/ui/Skeleton';
import { EmptyState } from '@/components/ui/EmptyState';

// Replace the loading spinner with skeleton layouts:
// KPI section:
{statsLoading ? <SkeletonKPIGrid count={4} /> : (/* existing KPI grid */)}

// Activity section:
{activityLoading ? (
  <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
    {[1,2,3,4,5].map(i => <Skeleton key={i} height={40} />)}
  </div>
) : activities.length === 0 ? (
  <EmptyState icon="inbox" title="No recent activity" message="Activity will appear as actions are performed." />
) : (/* existing activity list */)}

// Tenants table:
{tenantsLoading ? <SkeletonTable rows={5} cols={5} /> : tenants.length === 0 ? (
  <EmptyState icon="list" title="No tenants yet" message="Create your first company to get started." action={{ label: 'Add Company', onClick: () => navigate('/app/companies/add') }} />
) : (/* existing table */)}
```

- [ ] **Step 2: Commit**

```bash
git add -A && git commit -m "feat(web): add skeleton loading and empty states to dashboard"
```

---

## Task 11: Add Skeletons + Empty States to Company List — Both Platforms

**Files:**
- Modify: `M/features/super-admin/company-list-screen.tsx`
- Modify: `W/features/super-admin/CompanyListScreen.tsx`

- [ ] **Step 1: Mobile — improve company list loading and empty state**

In `company-list-screen.tsx`, replace the `renderEmpty` function's loading state with skeleton cards:

```tsx
import { Skeleton } from '@/components/ui/skeleton';
import { EmptyState } from '@/components/ui/empty-state';

// Replace renderEmpty loading state:
const renderEmpty = () => {
  if (isLoading) {
    return (
      <View style={{ gap: 12, paddingTop: 12 }}>
        {[1, 2, 3].map(i => (
          <Skeleton key={i} isLoading={true} layout={[
            { key: `card-${i}`, width: '100%', height: 140, borderRadius: 12 },
          ]}>
            <View />
          </Skeleton>
        ))}
      </View>
    );
  }
  if (isError) {
    return <EmptyState icon="error" title="Failed to load companies" message="Check your connection and try again." action={{ label: 'Retry', onPress: refetch }} />;
  }
  return <EmptyState icon="search" title="No companies found" message={searchQuery ? 'Try adjusting your search or filters.' : 'Create your first company to get started.'} />;
};
```

- [ ] **Step 2: Mobile — add infinite scroll**

In `company-list-screen.tsx`, add `onEndReached` to the FlatList for loading more:

```tsx
// Add state for page tracking:
const [page, setPage] = useState(1);
const limit = 25;

// Pass page to hook:
const { data, isLoading, isFetchingNextPage } = useTenantList({ page, limit, search: debouncedSearch, status: selectedStatus });

// Add onEndReached:
<FlatList
  // ... existing props
  onEndReached={() => {
    if (data?.meta && page < data.meta.totalPages) {
      setPage(prev => prev + 1);
    }
  }}
  onEndReachedThreshold={0.5}
  ListFooterComponent={isFetchingNextPage ? <ActivityIndicator style={{ paddingVertical: 16 }} /> : null}
/>
```

Note: If `useTenantList` doesn't support `useInfiniteQuery` pattern, this may need to accumulate results locally. Check the actual hook implementation and adapt.

- [ ] **Step 3: Web — add skeleton loading to company list**

In `CompanyListScreen.tsx`, replace loading state:

```tsx
import { SkeletonTable } from '@/components/ui/Skeleton';
import { EmptyState } from '@/components/ui/EmptyState';

// Replace loading spinner with skeleton table:
{isLoading ? (
  <SkeletonTable rows={8} cols={7} />
) : data?.data?.length === 0 ? (
  <EmptyState
    icon="search"
    title="No companies found"
    message={search ? 'Try adjusting your search or filters.' : 'Create your first company to get started.'}
    action={{ label: 'Add Company', onClick: () => navigate('/app/companies/add') }}
  />
) : (/* existing table */)}
```

- [ ] **Step 4: Commit**

```bash
git add -A && git commit -m "feat: add skeletons and empty states to company list on both platforms"
```

---

## Task 12: Add Skeletons to Company Detail + Billing — Both Platforms

**Files:**
- Modify: `M/features/super-admin/company-detail-screen.tsx`
- Modify: `M/features/super-admin/billing-overview-screen.tsx`
- Modify: `W/features/super-admin/CompanyDetailScreen.tsx`
- Modify: `W/features/super-admin/BillingOverviewScreen.tsx`

- [ ] **Step 1: Mobile company detail — skeleton loading**

In `company-detail-screen.tsx`, when `useTenantDetail` is loading, show skeleton layout instead of full-screen spinner:

```tsx
import { Skeleton } from '@/components/ui/skeleton';

// Replace loading state:
if (isLoading) {
  return (
    <SafeAreaView style={styles.container}>
      <Skeleton isLoading={true} layout={[
        { key: 'header', width: '100%', height: 180, borderRadius: 0 },
        { key: 'tab', width: '100%', height: 44, marginTop: 12 },
        { key: 'section1', width: '100%', height: 120, marginTop: 12, borderRadius: 12, marginHorizontal: 16 },
        { key: 'section2', width: '100%', height: 120, marginTop: 12, borderRadius: 12, marginHorizontal: 16 },
        { key: 'section3', width: '100%', height: 80, marginTop: 12, borderRadius: 12, marginHorizontal: 16 },
      ]}>
        <View />
      </Skeleton>
    </SafeAreaView>
  );
}
```

- [ ] **Step 2: Web company detail — skeleton loading**

In `CompanyDetailScreen.tsx`, replace loading spinner:

```tsx
import { Skeleton, SkeletonCard } from '@/components/ui/Skeleton';

if (isLoading) {
  return (
    <div style={{ maxWidth: 1200, margin: '0 auto', padding: 24 }}>
      <Skeleton width="100%" height={200} borderRadius={16} />
      <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr', gap: 24, marginTop: 24 }}>
        <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
          <SkeletonCard />
          <SkeletonCard />
          <SkeletonCard />
        </div>
        <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
          <SkeletonCard />
          <SkeletonCard />
        </div>
      </div>
    </div>
  );
}
```

- [ ] **Step 3: Mobile billing — skeleton loading + empty states**

In `billing-overview-screen.tsx`:
```tsx
import { Skeleton } from '@/components/ui/skeleton';
import { EmptyState } from '@/components/ui/empty-state';

// KPI section when loading:
{summaryLoading ? (
  <Skeleton isLoading={true} layout={[
    { key: 'k1', width: '48%', height: 80 },
    { key: 'k2', width: '48%', height: 80 },
    { key: 'k3', width: '48%', height: 80, marginTop: 8 },
    { key: 'k4', width: '48%', height: 80, marginTop: 8 },
  ]}>
    <View />
  </Skeleton>
) : (/* existing KPIs */)}

// Invoice list when empty:
{!invoicesLoading && invoices.length === 0 && (
  <EmptyState icon="inbox" title="No invoices yet" message="Invoices will appear here once billing is active." />
)}
```

- [ ] **Step 4: Web billing — skeleton loading + empty states**

In `BillingOverviewScreen.tsx`:
```tsx
import { SkeletonKPIGrid, SkeletonTable, Skeleton } from '@/components/ui/Skeleton';
import { EmptyState } from '@/components/ui/EmptyState';

// KPI section:
{summaryLoading ? <SkeletonKPIGrid count={4} /> : (/* existing */)}

// Chart section:
{chartLoading ? <Skeleton height={200} borderRadius={12} /> : (/* existing */)}

// Invoice table:
{invoicesLoading ? <SkeletonTable rows={6} cols={5} /> : invoices.length === 0 ? (
  <EmptyState icon="inbox" title="No invoices" message="Invoices will appear here once billing is active." />
) : (/* existing */)}
```

- [ ] **Step 5: Commit**

```bash
git add -A && git commit -m "feat: add skeleton loading and empty states to company detail and billing screens"
```

---

## Task 13: Backend — Audit Log Service + Controller + Routes

**Files:**
- Create: `B/core/audit/audit.service.ts`
- Create: `B/core/audit/audit.controller.ts`
- Create: `B/core/audit/audit.routes.ts`
- Modify: `B/app/routes.ts`

- [ ] **Step 1: Create audit service**

Create `B/core/audit/audit.service.ts`:
```typescript
import { platformPrisma } from '../../config/database';
import { Prisma } from '@prisma/client';

export interface AuditLogFilters {
  page?: number;
  limit?: number;
  action?: string;
  entityType?: string;
  userId?: string;
  tenantId?: string;
  dateFrom?: string;
  dateTo?: string;
  search?: string;
}

export class AuditService {
  async listAuditLogs(filters: AuditLogFilters = {}) {
    const {
      page = 1,
      limit = 25,
      action,
      entityType,
      userId,
      tenantId,
      dateFrom,
      dateTo,
      search,
    } = filters;

    const where: Prisma.AuditLogWhereInput = {};

    if (action) where.action = action;
    if (entityType) where.entityType = entityType;
    if (userId) where.userId = userId;
    if (tenantId) where.tenantId = tenantId;

    if (dateFrom || dateTo) {
      where.timestamp = {};
      if (dateFrom) where.timestamp.gte = new Date(dateFrom);
      if (dateTo) where.timestamp.lte = new Date(dateTo);
    }

    if (search) {
      where.OR = [
        { action: { contains: search, mode: 'insensitive' } },
        { entityType: { contains: search, mode: 'insensitive' } },
        { entityId: { contains: search, mode: 'insensitive' } },
      ];
    }

    const skip = (page - 1) * limit;

    const [logs, total] = await Promise.all([
      platformPrisma.auditLog.findMany({
        where,
        orderBy: { timestamp: 'desc' },
        skip,
        take: limit,
      }),
      platformPrisma.auditLog.count({ where }),
    ]);

    return { logs, total, page, limit, totalPages: Math.ceil(total / limit) };
  }

  async getAuditLogById(id: string) {
    return platformPrisma.auditLog.findUnique({ where: { id } });
  }

  async getAuditLogsByEntity(entityType: string, entityId: string, limit = 50) {
    return platformPrisma.auditLog.findMany({
      where: { entityType, entityId },
      orderBy: { timestamp: 'desc' },
      take: limit,
    });
  }

  async getActionTypes() {
    const result = await platformPrisma.auditLog.findMany({
      select: { action: true },
      distinct: ['action'],
      orderBy: { action: 'asc' },
    });
    return result.map(r => r.action);
  }

  async getEntityTypes() {
    const result = await platformPrisma.auditLog.findMany({
      select: { entityType: true },
      distinct: ['entityType'],
      orderBy: { entityType: 'asc' },
    });
    return result.map(r => r.entityType);
  }
}

export const auditService = new AuditService();
```

- [ ] **Step 2: Create audit controller**

Create `B/core/audit/audit.controller.ts`:
```typescript
import { Request, Response } from 'express';
import { asyncHandler } from '../../middleware/error.middleware';
import { createSuccessResponse, createPaginatedResponse, getPaginationParams } from '../../shared/utils';
import { auditService } from './audit.service';

export class AuditController {
  listAuditLogs = asyncHandler(async (req: Request, res: Response) => {
    const { page, limit } = getPaginationParams(req.query);
    const { action, entityType, userId, tenantId, dateFrom, dateTo, search } = req.query;

    const result = await auditService.listAuditLogs({
      page,
      limit,
      action: action as string,
      entityType: entityType as string,
      userId: userId as string,
      tenantId: tenantId as string,
      dateFrom: dateFrom as string,
      dateTo: dateTo as string,
      search: search as string,
    });

    res.json(createPaginatedResponse(
      result.logs,
      result.page,
      result.limit,
      result.total,
      'Audit logs retrieved successfully'
    ));
  });

  getAuditLogById = asyncHandler(async (req: Request, res: Response) => {
    const { id } = req.params;
    const log = await auditService.getAuditLogById(id);

    if (!log) {
      return res.status(404).json({ success: false, message: 'Audit log not found' });
    }

    res.json(createSuccessResponse(log, 'Audit log retrieved'));
  });

  getAuditLogsByEntity = asyncHandler(async (req: Request, res: Response) => {
    const { entityType, entityId } = req.params;
    const limit = parseInt(req.query.limit as string) || 50;
    const logs = await auditService.getAuditLogsByEntity(entityType, entityId, limit);
    res.json(createSuccessResponse(logs, 'Entity audit logs retrieved'));
  });

  getFilterOptions = asyncHandler(async (req: Request, res: Response) => {
    const [actionTypes, entityTypes] = await Promise.all([
      auditService.getActionTypes(),
      auditService.getEntityTypes(),
    ]);
    res.json(createSuccessResponse({ actionTypes, entityTypes }, 'Filter options retrieved'));
  });
}

export const auditController = new AuditController();
```

NOTE: Check if `getPaginationParams` and `createPaginatedResponse` exist in `shared/utils/`. If not, extract the pattern from `billing.controller.ts` where pagination params are manually parsed. Adapt accordingly.

- [ ] **Step 3: Create audit routes**

Create `B/core/audit/audit.routes.ts`:
```typescript
import { Router } from 'express';
import { auditController } from './audit.controller';

const router = Router();

router.get('/', auditController.listAuditLogs);
router.get('/filters', auditController.getFilterOptions);
router.get('/entity/:entityType/:entityId', auditController.getAuditLogsByEntity);
router.get('/:id', auditController.getAuditLogById);

export { router as auditRoutes };
```

- [ ] **Step 4: Register audit routes in main router**

In `B/app/routes.ts`, add the import at the top and register the route **immediately after the other `/platform/*` routes** (after `/platform/dashboard` and before the tenant-scoped routes block). This ensures it inherits the `platform:admin` permission middleware:

```typescript
import { auditRoutes } from '../core/audit/audit.routes';

// Place directly after: router.use('/platform/dashboard', dashboardPlatformRoutes);
router.use('/platform/audit-logs', auditRoutes);
```

- [ ] **Step 5: Verify the backend compiles**

```bash
cd /Users/chetan/Documents/Avyren-Technologies/Products/Mobile-ERP/avy-erp-backend
npx tsc --noEmit
```

- [ ] **Step 6: Commit**

```bash
git add -A && git commit -m "feat(backend): add audit log service, controller, and routes with filtering and pagination"
```

---

## Task 14: Backend — Audit Log Service Tests

**Files:**
- Create: `B/core/audit/__tests__/audit.service.test.ts`

- [ ] **Step 1: Write audit service tests**

Create `B/core/audit/__tests__/audit.service.test.ts`:
```typescript
import { auditService } from '../audit.service';
import { platformPrisma } from '../../../config/database';

jest.mock('../../../config/database', () => ({
  platformPrisma: {
    auditLog: {
      findMany: jest.fn(),
      findUnique: jest.fn(),
      count: jest.fn(),
    },
  },
}));

const mockAuditLog = platformPrisma.auditLog as any;

function makeSampleLog(overrides: Record<string, any> = {}) {
  return {
    id: 'log-1',
    tenantId: 'tenant-1',
    userId: 'user-1',
    action: 'CREATE_COMPANY',
    entityType: 'COMPANY',
    entityId: 'company-1',
    oldValues: null,
    newValues: { displayName: 'Test Corp' },
    ipAddress: '127.0.0.1',
    userAgent: 'Mozilla/5.0',
    timestamp: new Date('2026-03-19T10:00:00Z'),
    ...overrides,
  };
}

describe('AuditService', () => {
  beforeEach(() => jest.clearAllMocks());

  describe('listAuditLogs', () => {
    it('should return paginated audit logs with defaults', async () => {
      const logs = [makeSampleLog(), makeSampleLog({ id: 'log-2' })];
      mockAuditLog.findMany.mockResolvedValueOnce(logs);
      mockAuditLog.count.mockResolvedValueOnce(2);

      const result = await auditService.listAuditLogs();

      expect(result.logs).toHaveLength(2);
      expect(result.page).toBe(1);
      expect(result.limit).toBe(25);
      expect(result.total).toBe(2);
      expect(result.totalPages).toBe(1);
      expect(mockAuditLog.findMany).toHaveBeenCalledWith(expect.objectContaining({
        orderBy: { timestamp: 'desc' },
        skip: 0,
        take: 25,
      }));
    });

    it('should filter by action type', async () => {
      mockAuditLog.findMany.mockResolvedValueOnce([]);
      mockAuditLog.count.mockResolvedValueOnce(0);

      await auditService.listAuditLogs({ action: 'CREATE_COMPANY' });

      expect(mockAuditLog.findMany).toHaveBeenCalledWith(expect.objectContaining({
        where: expect.objectContaining({ action: 'CREATE_COMPANY' }),
      }));
    });

    it('should filter by date range', async () => {
      mockAuditLog.findMany.mockResolvedValueOnce([]);
      mockAuditLog.count.mockResolvedValueOnce(0);

      await auditService.listAuditLogs({
        dateFrom: '2026-03-01',
        dateTo: '2026-03-19',
      });

      expect(mockAuditLog.findMany).toHaveBeenCalledWith(expect.objectContaining({
        where: expect.objectContaining({
          timestamp: {
            gte: new Date('2026-03-01'),
            lte: new Date('2026-03-19'),
          },
        }),
      }));
    });

    it('should support search across action, entityType, entityId', async () => {
      mockAuditLog.findMany.mockResolvedValueOnce([]);
      mockAuditLog.count.mockResolvedValueOnce(0);

      await auditService.listAuditLogs({ search: 'company' });

      expect(mockAuditLog.findMany).toHaveBeenCalledWith(expect.objectContaining({
        where: expect.objectContaining({
          OR: expect.arrayContaining([
            expect.objectContaining({ action: { contains: 'company', mode: 'insensitive' } }),
          ]),
        }),
      }));
    });

    it('should handle pagination correctly', async () => {
      mockAuditLog.findMany.mockResolvedValueOnce([]);
      mockAuditLog.count.mockResolvedValueOnce(75);

      const result = await auditService.listAuditLogs({ page: 3, limit: 10 });

      expect(result.totalPages).toBe(8);
      expect(mockAuditLog.findMany).toHaveBeenCalledWith(expect.objectContaining({
        skip: 20,
        take: 10,
      }));
    });
  });

  describe('getAuditLogById', () => {
    it('should return a single audit log', async () => {
      const log = makeSampleLog();
      mockAuditLog.findUnique.mockResolvedValueOnce(log);

      const result = await auditService.getAuditLogById('log-1');

      expect(result).toEqual(log);
      expect(mockAuditLog.findUnique).toHaveBeenCalledWith({ where: { id: 'log-1' } });
    });

    it('should return null for non-existent log', async () => {
      mockAuditLog.findUnique.mockResolvedValueOnce(null);
      const result = await auditService.getAuditLogById('nonexistent');
      expect(result).toBeNull();
    });
  });

  describe('getAuditLogsByEntity', () => {
    it('should return logs for a specific entity', async () => {
      const logs = [makeSampleLog()];
      mockAuditLog.findMany.mockResolvedValueOnce(logs);

      const result = await auditService.getAuditLogsByEntity('COMPANY', 'company-1');

      expect(result).toHaveLength(1);
      expect(mockAuditLog.findMany).toHaveBeenCalledWith(expect.objectContaining({
        where: { entityType: 'COMPANY', entityId: 'company-1' },
      }));
    });
  });

  describe('getActionTypes', () => {
    it('should return distinct action types', async () => {
      mockAuditLog.findMany.mockResolvedValueOnce([
        { action: 'CREATE_COMPANY' },
        { action: 'UPDATE_STATUS' },
      ]);

      const result = await auditService.getActionTypes();
      expect(result).toEqual(['CREATE_COMPANY', 'UPDATE_STATUS']);
    });
  });
});
```

- [ ] **Step 2: Run tests**

```bash
cd /Users/chetan/Documents/Avyren-Technologies/Products/Mobile-ERP/avy-erp-backend
npx jest src/core/audit/__tests__/audit.service.test.ts --verbose
```

Expected: All tests pass.

- [ ] **Step 3: Commit**

```bash
git add -A && git commit -m "test(backend): add comprehensive audit log service tests"
```

---

## Task 15: Frontend — Audit Log API Hooks + Screen — Mobile

**Files:**
- Create: `M/lib/api/audit.ts`
- Create: `M/features/super-admin/api/use-audit-queries.ts`
- Create: `M/features/super-admin/audit-log-screen.tsx`
- Create: `M/app/(app)/reports/audit.tsx`

- [ ] **Step 1: Create mobile audit API functions**

Create `M/lib/api/audit.ts`:
```typescript
import { client } from '@/lib/api/client';

export interface AuditLogParams {
  page?: number;
  limit?: number;
  action?: string;
  entityType?: string;
  dateFrom?: string;
  dateTo?: string;
  search?: string;
}

export const auditApi = {
  listAuditLogs: (params: AuditLogParams = {}) =>
    client.get('/platform/audit-logs', { params }),

  getAuditLogById: (id: string) =>
    client.get(`/platform/audit-logs/${id}`),

  getFilterOptions: () =>
    client.get('/platform/audit-logs/filters'),

  getEntityAuditLogs: (entityType: string, entityId: string) =>
    client.get(`/platform/audit-logs/entity/${entityType}/${entityId}`),
};
```

- [ ] **Step 2: Create mobile audit query hooks**

Create `M/features/super-admin/api/use-audit-queries.ts`:
```typescript
import { useQuery } from '@tanstack/react-query';
import { auditApi, AuditLogParams } from '@/lib/api/audit';

export function useAuditLogs(params: AuditLogParams = {}) {
  return useQuery({
    queryKey: ['audit-logs', params],
    queryFn: () => auditApi.listAuditLogs(params),
  });
}

export function useAuditLogDetail(id: string) {
  return useQuery({
    queryKey: ['audit-log', id],
    queryFn: () => auditApi.getAuditLogById(id),
    enabled: !!id,
  });
}

export function useAuditFilterOptions() {
  return useQuery({
    queryKey: ['audit-log-filters'],
    queryFn: () => auditApi.getFilterOptions(),
    staleTime: 5 * 60 * 1000, // 5 minutes
  });
}

export function useEntityAuditLogs(entityType: string, entityId: string) {
  return useQuery({
    queryKey: ['audit-logs', 'entity', entityType, entityId],
    queryFn: () => auditApi.getEntityAuditLogs(entityType, entityId),
    enabled: !!entityType && !!entityId,
  });
}
```

- [ ] **Step 3: Create mobile audit log screen**

Create `M/features/super-admin/audit-log-screen.tsx`. This screen should follow the patterns from `company-list-screen.tsx`:

- LinearGradient header with HamburgerButton and title "Audit Log"
- Search bar at top
- Filter chips for action types (from `useAuditFilterOptions`)
- FlatList of audit log entries showing: timestamp, action badge, entity type, entity ID
- Each item is a card with:
  - Left: colored action icon/badge
  - Center: action text + entity info + user info
  - Right: formatted timestamp
- Skeleton loading when loading
- EmptyState when no results
- Pull-to-refresh via RefreshControl

The component should export as a named export:
```tsx
export function AuditLogScreen() { ... }
```

Key imports needed:
```tsx
import { LinearGradient } from 'expo-linear-gradient';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import Animated, { FadeInDown } from 'react-native-reanimated';
import { Text } from '@/components/ui';
import colors from '@/components/ui/colors';
import { HamburgerButton } from '@/components/ui/sidebar';
import { Skeleton } from '@/components/ui/skeleton';
import { EmptyState } from '@/components/ui/empty-state';
import { useAuditLogs, useAuditFilterOptions } from '@/features/super-admin/api/use-audit-queries';
```

Use the action type to determine badge color:
- CREATE_* → green (success)
- UPDATE_* / CHANGE_* → blue (primary)
- DELETE_* → red (danger)
- Default → gray (neutral)

Format timestamp using: `new Date(timestamp).toLocaleString()`

- [ ] **Step 4: Create route file**

Create the route directory and files. In Expo Router, a new directory group needs a `_layout.tsx` to render children within the tab navigator.

First create `M/app/(app)/reports/_layout.tsx`:
```tsx
import { Stack } from 'expo-router';

export default function ReportsLayout() {
  return <Stack screenOptions={{ headerShown: false }} />;
}
```

Then create `M/app/(app)/reports/audit.tsx`:
```tsx
export { AuditLogScreen as default } from '@/features/super-admin/audit-log-screen';
```

- [ ] **Step 5: Verify navigation works**

Run the mobile app and navigate to the audit log screen via sidebar or dashboard "View All" link.

- [ ] **Step 6: Commit**

```bash
git add -A && git commit -m "feat(mobile): add audit log screen with API hooks, filtering, and pagination"
```

---

## Task 16: Frontend — Audit Log API Hooks + Screen — Web

**Files:**
- Create: `W/lib/api/audit.ts`
- Create: `W/features/super-admin/api/use-audit-queries.ts`
- Create: `W/features/super-admin/AuditLogScreen.tsx`
- Modify: `W/App.tsx`

- [ ] **Step 1: Create web audit API functions**

Create `W/lib/api/audit.ts`:
```typescript
import { client } from '@/lib/api/client';

export interface AuditLogParams {
  page?: number;
  limit?: number;
  action?: string;
  entityType?: string;
  dateFrom?: string;
  dateTo?: string;
  search?: string;
}

export const auditApi = {
  listAuditLogs: (params: AuditLogParams = {}) =>
    client.get('/platform/audit-logs', { params }),

  getAuditLogById: (id: string) =>
    client.get(`/platform/audit-logs/${id}`),

  getFilterOptions: () =>
    client.get('/platform/audit-logs/filters'),

  getEntityAuditLogs: (entityType: string, entityId: string) =>
    client.get(`/platform/audit-logs/entity/${entityType}/${entityId}`),
};
```

- [ ] **Step 2: Create web audit query hooks**

Create `W/features/super-admin/api/use-audit-queries.ts`:
```typescript
import { useQuery } from '@tanstack/react-query';
import { auditApi, AuditLogParams } from '@/lib/api/audit';

export function useAuditLogs(params: AuditLogParams = {}) {
  return useQuery({
    queryKey: ['audit-logs', params],
    queryFn: () => auditApi.listAuditLogs(params),
    // NOTE: Web client does NOT unwrap .data like mobile does.
    // Access pattern: data?.data?.data for the logs array, data?.data?.meta for pagination.
    // Check the existing use-tenant-queries.ts / use-dashboard-queries.ts for the exact
    // access pattern used in this codebase (e.g., data?.data?.data or data?.data).
  });
}

export function useAuditFilterOptions() {
  return useQuery({
    queryKey: ['audit-log-filters'],
    queryFn: () => auditApi.getFilterOptions(),
    staleTime: 5 * 60 * 1000,
  });
}
```

- [ ] **Step 3: Create web audit log screen**

Create `W/features/super-admin/AuditLogScreen.tsx`. Follow the patterns from `CompanyListScreen.tsx`:

- Page header with "Audit Log" title and search bar
- Filter row: action type chips + entity type chips + date range inputs (dateFrom/dateTo)
- Data table with columns: Timestamp, Action, Entity Type, Entity ID, User, IP Address
- Action badges with colors (same scheme as mobile: CREATE=green, UPDATE=blue, DELETE=red)
- Pagination (prev/next buttons, "Showing X to Y of Z")
- Skeleton loading via `SkeletonTable`
- EmptyState when no results
- Click row to show detail (old/new values) in a side panel or modal

Key imports:
```tsx
import { useNavigate, useSearchParams } from 'react-router-dom';
import { Search, Filter, Calendar, ChevronLeft, ChevronRight } from 'lucide-react';
import { SkeletonTable } from '@/components/ui/Skeleton';
import { EmptyState } from '@/components/ui/EmptyState';
import { useAuditLogs, useAuditFilterOptions } from '@/features/super-admin/api/use-audit-queries';
```

- [ ] **Step 4: Add route to App.tsx**

In `W/App.tsx`, add the audit log route under the protected `/app/*` routes:
```tsx
import { AuditLogScreen } from '@/features/super-admin/AuditLogScreen';

// Inside Routes, under /app:
<Route path="reports/audit" element={<RequireRole roles={['super-admin']}><AuditLogScreen /></RequireRole>} />
```

- [ ] **Step 5: Wire sidebar navigation**

In `W/layouts/Sidebar.tsx`, ensure there's a navigation item for Audit Log. If it doesn't exist, add it under a "Reports" or "Administration" section:
```tsx
{ label: 'Audit Log', icon: FileText, path: '/app/reports/audit', roles: ['super_admin'] }
```

- [ ] **Step 6: Verify navigation and functionality**

Run: `cd web-system-app && pnpm dev`
Navigate to Audit Log via sidebar. Verify table loads, filters work, pagination works.

- [ ] **Step 7: Commit**

```bash
git add -A && git commit -m "feat(web): add audit log screen with filtering, pagination, and action badges"
```

---

## Task 17: Wire Audit Log Tab in Company Detail — Both Platforms

**Files:**
- Modify: `M/features/super-admin/company-detail-screen.tsx`
- Modify: `W/features/super-admin/CompanyDetailScreen.tsx`

- [ ] **Step 1: Mobile — add audit log tab content**

In `company-detail-screen.tsx`, find the Audit/Activity tab content area. Use `useEntityAuditLogs('COMPANY', companyId)` to fetch tenant-specific audit logs:

```tsx
import { useEntityAuditLogs } from '@/features/super-admin/api/use-audit-queries';

// Inside the component:
const { data: auditData, isLoading: auditLoading } = useEntityAuditLogs('COMPANY', companyId);

// In the audit tab render:
{auditLoading ? (
  <Skeleton isLoading layout={[...]} ><View /></Skeleton>
) : auditData?.data?.length === 0 ? (
  <EmptyState icon="inbox" title="No audit history" message="Changes to this company will be recorded here." />
) : (
  <FlatList
    data={auditData?.data || []}
    keyExtractor={item => item.id}
    renderItem={({ item }) => (
      <View style={styles.auditItem}>
        <Text className="font-inter" style={styles.auditAction}>{item.action}</Text>
        <Text className="font-inter" style={styles.auditTime}>
          {new Date(item.timestamp).toLocaleString()}
        </Text>
      </View>
    )}
  />
)}
```

- [ ] **Step 2: Web — add audit log section in company detail**

In `CompanyDetailScreen.tsx`, add an "Audit History" collapsible section using the same `useEntityAuditLogs` hook. Render as a simple timeline/list showing action, timestamp, and optionally oldValues/newValues diff.

- [ ] **Step 3: Commit**

```bash
git add -A && git commit -m "feat: add audit log tab to company detail screen on both platforms"
```

---

## Task 18: Update Checklist Document

**Files:**
- Modify: `docs/04_Super_Admin_Development_Checklist.md`

- [ ] **Step 1: Update completed items**

After all tasks above are done, update the checklist:
- I.6 Toast/snackbar: ❌ → ✅
- I.3 API error handling: 🔄 → ✅
- 1A.3 KPI tap-to-navigate: ❌ → ✅
- 1A.6, 1A.8, 1A.10 View All links: ❌ → ✅
- 1A.11 Quick Actions: 🔄 → ✅
- I.4 Loading skeletons: ❌ → ✅
- I.5 Empty state components: ❌ → ✅
- 1F.1-1F.5 Audit Log: ❌ → ✅
- 1C.7 Audit Log tab: ❌ → ✅

- [ ] **Step 2: Commit**

```bash
git add -A && git commit -m "docs: update super admin checklist with sprint 1-3 completion"
```

---

## Execution Summary

| Task | Description | Platforms | Est. Complexity |
|------|-------------|-----------|-----------------|
| 1 | Install & wire sonner toast (web) | Web | Low |
| 2 | Wire flash message toast helpers (mobile) | Mobile | Low |
| 3 | 403/5xx error toast in API clients | Both | Low |
| 4 | Fix sidebar billing links | Both | Low |
| 5 | KPI tap-to-navigate + View All (mobile) | Mobile | Medium |
| 6 | KPI tap-to-navigate + View All (web) | Web | Medium |
| 7 | EmptyState component | Both | Low |
| 8 | Skeleton component (web) | Web | Low |
| 9 | Dashboard skeletons + empty states (mobile) | Mobile | Medium |
| 10 | Dashboard skeletons + empty states (web) | Web | Medium |
| 11 | Company list skeletons + empty states | Both | Medium |
| 12 | Company detail + billing skeletons | Both | Medium |
| 13 | Audit log backend (service + controller + routes) | Backend | Medium |
| 14 | Audit log backend tests | Backend | Medium |
| 15 | Audit log screen (mobile) | Mobile | High |
| 16 | Audit log screen (web) | Web | High |
| 17 | Audit log tab in company detail | Both | Medium |
| 18 | Update checklist | Docs | Low |

**Total: 18 tasks across 3 codebases**

**Dependency order:**
- Task 1 (web toast) must complete before Task 3 (web error handling imports from toast.tsx)
- Tasks 2, 4 are independent of Task 1 — can run in parallel with it
- Tasks 5-6 (KPI navigation) are independent — can run in parallel
- Tasks 7-8 (components) must complete before Tasks 9-12 (usage in screens)
- Task 13 (backend) must complete before Tasks 15-17 (frontend screens)
- Task 14 (tests) can run parallel with Task 13 if mocks are ready
- Task 18 (checklist) runs last
