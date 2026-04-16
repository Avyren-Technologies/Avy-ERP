# App Version Control & Force Update System — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a server-controlled app version gating system that can force users to update, soft-prompt updates, block app usage for outdated versions, and apply OTA updates with visible progress — all managed by the super admin.

**Architecture:** A new `AppVersionConfig` table stores per-platform version rules (minimum, recommended, latest) and a maintenance mode flag. A public (no-auth) endpoint `/app-version/check` returns the update verdict. The mobile app calls this on every cold start — before auth — and renders a blocking full-screen gate when a force update or maintenance mode is active. Expo OTA updates are checked and applied with a visible loading screen before the version gate runs. Super admin CRUD endpoints manage version configs.

**Tech Stack:** Prisma (platform DB), Express + Zod (backend), React Native Modal + expo-updates + expo-application (mobile)

---

## File Structure

### Backend — New module: `src/core/app-version/`

| File | Responsibility |
|------|---------------|
| `prisma/modules/platform/app-version.prisma` | `AppVersionConfig` model |
| `src/core/app-version/app-version.validators.ts` | Zod schemas for create/update |
| `src/core/app-version/app-version.service.ts` | Version comparison logic + CRUD |
| `src/core/app-version/app-version.controller.ts` | Public check + admin CRUD handlers |
| `src/core/app-version/app-version.routes.ts` | Router with public + admin routes |

### Mobile — New files

| File | Responsibility |
|------|---------------|
| `src/lib/api/app-version.ts` | API client for `/app-version/check` |
| `src/components/ui/app-update-gate.tsx` | Full-screen blocking gate (force update + maintenance) |
| `src/components/ui/ota-update-screen.tsx` | OTA update progress screen |
| `src/components/ui/soft-update-prompt.tsx` | Dismissible update prompt modal |

### Modified files

| File | Change |
|------|--------|
| `avy-erp-backend/src/app/routes.ts` | Mount public + admin version routes |
| `mobile-app/src/app/(app)/_layout.tsx` | Wrap with `AppUpdateGate` and OTA check |
| `mobile-app/src/app/_layout.tsx` | Add OTA update check before providers |

---

## Task 1: Prisma Model — `AppVersionConfig`

**Files:**
- Create: `avy-erp-backend/prisma/modules/platform/app-version.prisma`

- [ ] **Step 1: Create the model file**

```prisma
// App version control — server-side gating for mobile/web clients.
// Super admin sets minimum + recommended versions per platform.
// Public endpoint lets clients check before even logging in.

model AppVersionConfig {
  id                  String   @id @default(cuid())

  // Target platform
  platform            String   // ANDROID | IOS

  // Version thresholds (semver strings e.g. "1.2.0")
  latestVersion       String   // Latest available version
  minimumVersion      String   // Force update below this
  recommendedVersion  String?  // Soft prompt below this (but >= minimum)

  // Store links
  updateUrl           String?  // Play Store / App Store URL

  // Maintenance mode — blocks ALL versions regardless of thresholds
  maintenanceMode     Boolean  @default(false)
  maintenanceMessage  String?  // Custom message shown during maintenance

  // Control flag — allows disabling a config without deleting
  isActive            Boolean  @default(true)

  createdAt           DateTime @default(now())
  updatedAt           DateTime @updatedAt

  @@unique([platform])
  @@map("app_version_configs")
}
```

- [ ] **Step 2: Merge and generate**

Run:
```bash
cd avy-erp-backend && pnpm prisma:merge && pnpm db:generate
```
Expected: Clean merge, Prisma client generated with `AppVersionConfig` type.

- [ ] **Step 3: Migrate**

Run:
```bash
cd avy-erp-backend && pnpm db:migrate -- --name add_app_version_config
```
Expected: Migration creates `app_version_configs` table.

- [ ] **Step 4: Commit**

```bash
git add prisma/modules/platform/app-version.prisma prisma/schema.prisma prisma/migrations/
git commit -m "feat(schema): add AppVersionConfig model for force update gating"
```

---

## Task 2: Backend Validators

**Files:**
- Create: `avy-erp-backend/src/core/app-version/app-version.validators.ts`

- [ ] **Step 1: Create validators**

```typescript
import { z } from 'zod';

// Semver-ish: 1.0.0, 1.2.3, 10.20.30
const semverRegex = /^\d+\.\d+\.\d+$/;
const semver = z.string().regex(semverRegex, 'Version must be in semver format (e.g. 1.2.3)');

export const platformEnum = z.enum(['ANDROID', 'IOS']);

export const createAppVersionConfigSchema = z.object({
  platform: platformEnum,
  latestVersion: semver,
  minimumVersion: semver,
  recommendedVersion: semver.optional(),
  updateUrl: z.string().url('Must be a valid URL').optional(),
  maintenanceMode: z.boolean().optional(),
  maintenanceMessage: z.string().max(500).optional(),
  isActive: z.boolean().optional(),
});

export const updateAppVersionConfigSchema = createAppVersionConfigSchema
  .omit({ platform: true })
  .partial();

export const checkVersionQuerySchema = z.object({
  platform: platformEnum,
  version: semver,
});
```

- [ ] **Step 2: Commit**

```bash
git add src/core/app-version/app-version.validators.ts
git commit -m "feat(app-version): add Zod validation schemas"
```

---

## Task 3: Backend Service — Version Comparison + CRUD

**Files:**
- Create: `avy-erp-backend/src/core/app-version/app-version.service.ts`

- [ ] **Step 1: Create service**

```typescript
import { platformPrisma } from '../../config/database';
import { ApiError } from '../../shared/errors';

type UpdateVerdict = 'force' | 'soft' | 'none';

interface VersionCheckResult {
  updateRequired: UpdateVerdict;
  currentVersion: string;        // Client's version (echoed back)
  latestVersion: string;
  minimumVersion: string;
  recommendedVersion: string | null;
  updateUrl: string | null;
  maintenanceMode: boolean;
  message: string;
}

/**
 * Compare two semver strings. Returns:
 *  -1 if a < b,  0 if a === b,  1 if a > b
 */
function compareSemver(a: string, b: string): number {
  const pa = a.split('.').map(Number);
  const pb = b.split('.').map(Number);
  for (let i = 0; i < 3; i++) {
    if (pa[i] < pb[i]) return -1;
    if (pa[i] > pb[i]) return 1;
  }
  return 0;
}

class AppVersionService {
  /**
   * Public check — no auth required.
   * Called by mobile/web clients on cold start.
   */
  async checkVersion(platform: string, clientVersion: string): Promise<VersionCheckResult> {
    const config = await platformPrisma.appVersionConfig.findUnique({
      where: { platform },
    });

    // No config for this platform — allow through
    if (!config || !config.isActive) {
      return {
        updateRequired: 'none',
        currentVersion: clientVersion,
        latestVersion: clientVersion,
        minimumVersion: '0.0.0',
        recommendedVersion: null,
        updateUrl: null,
        maintenanceMode: false,
        message: 'App is up to date',
      };
    }

    // Maintenance mode overrides everything
    if (config.maintenanceMode) {
      return {
        updateRequired: 'force',
        currentVersion: clientVersion,
        latestVersion: config.latestVersion,
        minimumVersion: config.minimumVersion,
        recommendedVersion: config.recommendedVersion,
        updateUrl: config.updateUrl,
        maintenanceMode: true,
        message: config.maintenanceMessage ?? 'The app is currently under maintenance. Please try again later.',
      };
    }

    let verdict: UpdateVerdict = 'none';
    let message = 'App is up to date';

    // Force update: client < minimum
    if (compareSemver(clientVersion, config.minimumVersion) < 0) {
      verdict = 'force';
      message = `Your app version (${clientVersion}) is no longer supported. Please update to version ${config.latestVersion} to continue.`;
    }
    // Soft update: client < recommended (but >= minimum)
    else if (
      config.recommendedVersion &&
      compareSemver(clientVersion, config.recommendedVersion) < 0
    ) {
      verdict = 'soft';
      message = `A new version (${config.latestVersion}) is available with improvements and bug fixes.`;
    }

    return {
      updateRequired: verdict,
      currentVersion: clientVersion,
      latestVersion: config.latestVersion,
      minimumVersion: config.minimumVersion,
      recommendedVersion: config.recommendedVersion,
      updateUrl: config.updateUrl,
      maintenanceMode: false,
      message,
    };
  }

  // ── Admin CRUD ──────────────────────────────────────────────

  async list() {
    return platformPrisma.appVersionConfig.findMany({
      orderBy: { platform: 'asc' },
    });
  }

  async getByPlatform(platform: string) {
    return platformPrisma.appVersionConfig.findUnique({
      where: { platform },
    });
  }

  async upsert(
    platform: string,
    data: {
      latestVersion: string;
      minimumVersion: string;
      recommendedVersion?: string;
      updateUrl?: string;
      maintenanceMode?: boolean;
      maintenanceMessage?: string;
      isActive?: boolean;
    },
  ) {
    // Validate: minimumVersion <= recommendedVersion <= latestVersion
    if (compareSemver(data.minimumVersion, data.latestVersion) > 0) {
      throw ApiError.badRequest('minimumVersion cannot be greater than latestVersion');
    }
    if (
      data.recommendedVersion &&
      compareSemver(data.recommendedVersion, data.latestVersion) > 0
    ) {
      throw ApiError.badRequest('recommendedVersion cannot be greater than latestVersion');
    }
    if (
      data.recommendedVersion &&
      compareSemver(data.minimumVersion, data.recommendedVersion) > 0
    ) {
      throw ApiError.badRequest('minimumVersion cannot be greater than recommendedVersion');
    }

    return platformPrisma.appVersionConfig.upsert({
      where: { platform },
      create: {
        platform,
        latestVersion: data.latestVersion,
        minimumVersion: data.minimumVersion,
        recommendedVersion: data.recommendedVersion ?? null,
        updateUrl: data.updateUrl ?? null,
        maintenanceMode: data.maintenanceMode ?? false,
        maintenanceMessage: data.maintenanceMessage ?? null,
        isActive: data.isActive ?? true,
      },
      update: {
        latestVersion: data.latestVersion,
        minimumVersion: data.minimumVersion,
        recommendedVersion: data.recommendedVersion ?? null,
        updateUrl: data.updateUrl ?? null,
        maintenanceMode: data.maintenanceMode ?? false,
        maintenanceMessage: data.maintenanceMessage ?? null,
        isActive: data.isActive ?? true,
      },
    });
  }

  async update(
    id: string,
    data: {
      latestVersion?: string;
      minimumVersion?: string;
      recommendedVersion?: string;
      updateUrl?: string;
      maintenanceMode?: boolean;
      maintenanceMessage?: string;
      isActive?: boolean;
    },
  ) {
    const existing = await platformPrisma.appVersionConfig.findUnique({ where: { id } });
    if (!existing) throw ApiError.notFound('App version config not found');

    // Merge with existing for cross-field validation
    const merged = {
      latestVersion: data.latestVersion ?? existing.latestVersion,
      minimumVersion: data.minimumVersion ?? existing.minimumVersion,
      recommendedVersion: data.recommendedVersion ?? existing.recommendedVersion,
    };

    if (compareSemver(merged.minimumVersion, merged.latestVersion) > 0) {
      throw ApiError.badRequest('minimumVersion cannot be greater than latestVersion');
    }
    if (
      merged.recommendedVersion &&
      compareSemver(merged.recommendedVersion, merged.latestVersion) > 0
    ) {
      throw ApiError.badRequest('recommendedVersion cannot be greater than latestVersion');
    }
    if (
      merged.recommendedVersion &&
      compareSemver(merged.minimumVersion, merged.recommendedVersion) > 0
    ) {
      throw ApiError.badRequest('minimumVersion cannot be greater than recommendedVersion');
    }

    return platformPrisma.appVersionConfig.update({
      where: { id },
      data: {
        latestVersion: data.latestVersion,
        minimumVersion: data.minimumVersion,
        recommendedVersion: data.recommendedVersion !== undefined ? (data.recommendedVersion ?? null) : undefined,
        updateUrl: data.updateUrl !== undefined ? (data.updateUrl ?? null) : undefined,
        maintenanceMode: data.maintenanceMode,
        maintenanceMessage: data.maintenanceMessage !== undefined ? (data.maintenanceMessage ?? null) : undefined,
        isActive: data.isActive,
      },
    });
  }

  async delete(id: string) {
    const existing = await platformPrisma.appVersionConfig.findUnique({ where: { id } });
    if (!existing) throw ApiError.notFound('App version config not found');
    return platformPrisma.appVersionConfig.delete({ where: { id } });
  }
}

export const appVersionService = new AppVersionService();
```

- [ ] **Step 2: Commit**

```bash
git add src/core/app-version/app-version.service.ts
git commit -m "feat(app-version): add service with semver comparison and CRUD"
```

---

## Task 4: Backend Controller

**Files:**
- Create: `avy-erp-backend/src/core/app-version/app-version.controller.ts`

- [ ] **Step 1: Create controller**

```typescript
import { Request, Response } from 'express';
import { appVersionService } from './app-version.service';
import {
  checkVersionQuerySchema,
  createAppVersionConfigSchema,
  updateAppVersionConfigSchema,
} from './app-version.validators';
import { createSuccessResponse } from '../../shared/utils';
import { asyncHandler } from '../../middleware/error.middleware';
import { ApiError } from '../../shared/errors';

class AppVersionController {
  /**
   * Public — no auth required.
   * GET /app-version/check?platform=ANDROID&version=1.0.5
   */
  checkVersion = asyncHandler(async (req: Request, res: Response) => {
    const parsed = checkVersionQuerySchema.safeParse(req.query);
    if (!parsed.success) {
      throw ApiError.badRequest(parsed.error.errors.map((e) => e.message).join(', '));
    }
    const result = await appVersionService.checkVersion(parsed.data.platform, parsed.data.version);
    res.json(createSuccessResponse(result, 'Version check completed'));
  });

  // ── Admin CRUD (super admin only) ──────────────────────────

  list = asyncHandler(async (_req: Request, res: Response) => {
    const configs = await appVersionService.list();
    res.json(createSuccessResponse(configs, 'App version configs retrieved'));
  });

  getByPlatform = asyncHandler(async (req: Request, res: Response) => {
    const platform = req.params.platform?.toUpperCase();
    if (!platform) throw ApiError.badRequest('Platform is required');
    const config = await appVersionService.getByPlatform(platform);
    if (!config) throw ApiError.notFound(`No config found for platform: ${platform}`);
    res.json(createSuccessResponse(config));
  });

  upsert = asyncHandler(async (req: Request, res: Response) => {
    const parsed = createAppVersionConfigSchema.safeParse(req.body);
    if (!parsed.success) {
      throw ApiError.badRequest(parsed.error.errors.map((e) => e.message).join(', '));
    }
    const config = await appVersionService.upsert(parsed.data.platform, parsed.data);
    res.status(201).json(createSuccessResponse(config, 'App version config saved'));
  });

  update = asyncHandler(async (req: Request, res: Response) => {
    const id = req.params.id;
    if (!id) throw ApiError.badRequest('Config ID is required');
    const parsed = updateAppVersionConfigSchema.safeParse(req.body);
    if (!parsed.success) {
      throw ApiError.badRequest(parsed.error.errors.map((e) => e.message).join(', '));
    }
    const config = await appVersionService.update(id, parsed.data);
    res.json(createSuccessResponse(config, 'App version config updated'));
  });

  delete = asyncHandler(async (req: Request, res: Response) => {
    const id = req.params.id;
    if (!id) throw ApiError.badRequest('Config ID is required');
    await appVersionService.delete(id);
    res.json(createSuccessResponse(null, 'App version config deleted'));
  });
}

export const appVersionController = new AppVersionController();
```

- [ ] **Step 2: Commit**

```bash
git add src/core/app-version/app-version.controller.ts
git commit -m "feat(app-version): add controller with public check + admin CRUD"
```

---

## Task 5: Backend Routes + Mount

**Files:**
- Create: `avy-erp-backend/src/core/app-version/app-version.routes.ts`
- Modify: `avy-erp-backend/src/app/routes.ts`

- [ ] **Step 1: Create routes file**

```typescript
import { Router } from 'express';
import { appVersionController as controller } from './app-version.controller';

// ── Public routes (no auth) ──────────────────────────────────
export const appVersionPublicRoutes = Router();
appVersionPublicRoutes.get('/check', controller.checkVersion);

// ── Admin routes (super admin only, mounted under /platform) ─
export const appVersionAdminRoutes = Router();
appVersionAdminRoutes.get('/', controller.list);
appVersionAdminRoutes.post('/', controller.upsert);
appVersionAdminRoutes.get('/:platform', controller.getByPlatform);
appVersionAdminRoutes.patch('/:id', controller.update);
appVersionAdminRoutes.delete('/:id', controller.delete);
```

- [ ] **Step 2: Mount in routes.ts**

In `avy-erp-backend/src/app/routes.ts`, add the import at the top with the other core module imports (after line 20):

```typescript
import { appVersionPublicRoutes, appVersionAdminRoutes } from '../core/app-version/app-version.routes';
```

Mount the public route **before** auth middleware (after the health check, around line 47), just before the auth routes:

```typescript
// App version check (public, no auth — must work before login)
router.use('/app-version', appVersionPublicRoutes);
```

Mount the admin route under `/platform` (after line 88):

```typescript
router.use('/platform/app-versions', appVersionAdminRoutes);
```

- [ ] **Step 3: Verify server starts**

Run:
```bash
cd avy-erp-backend && pnpm dev
```
Expected: Server starts without errors. `GET /api/v1/app-version/check?platform=ANDROID&version=1.0.5` returns `{ success: true, data: { updateRequired: "none", ... } }`.

- [ ] **Step 4: Commit**

```bash
git add src/core/app-version/app-version.routes.ts src/app/routes.ts
git commit -m "feat(app-version): mount public check + admin CRUD routes"
```

---

## Task 6: Mobile — API Client

**Files:**
- Create: `mobile-app/src/lib/api/app-version.ts`

- [ ] **Step 1: Create API module**

```typescript
import axios from 'axios';
import * as Application from 'expo-application';
import { Platform } from 'react-native';

import Env from 'env';

type UpdateVerdict = 'force' | 'soft' | 'none';

export interface VersionCheckResult {
  updateRequired: UpdateVerdict;
  currentVersion: string;
  latestVersion: string;
  minimumVersion: string;
  recommendedVersion: string | null;
  updateUrl: string | null;
  maintenanceMode: boolean;
  message: string;
}

/**
 * Check app version against server config.
 *
 * Uses a standalone axios instance (NOT the auth-intercepted `client`)
 * because this endpoint is public and must work before the user logs in.
 */
export async function checkAppVersion(): Promise<VersionCheckResult> {
  const platform = Platform.OS === 'ios' ? 'IOS' : 'ANDROID';
  const version = Application.nativeApplicationVersion ?? Env.EXPO_PUBLIC_VERSION;

  const response = await axios.get<{ success: boolean; data: VersionCheckResult }>(
    `${Env.EXPO_PUBLIC_API_URL}/app-version/check`,
    { params: { platform, version }, timeout: 10000 },
  );

  return response.data.data;
}
```

- [ ] **Step 2: Commit**

```bash
git add src/lib/api/app-version.ts
git commit -m "feat(app-version): add mobile API client for public version check"
```

---

## Task 7: Mobile — OTA Update Screen

**Files:**
- Create: `mobile-app/src/components/ui/ota-update-screen.tsx`

- [ ] **Step 1: Create OTA update screen**

This is a full-screen overlay shown during OTA update download. Renders on top of everything.

```typescript
import * as Updates from 'expo-updates';
import * as React from 'react';
import { useCallback, useEffect, useState } from 'react';
import { ActivityIndicator, Image, Modal, StyleSheet, View } from 'react-native';

import { Text } from '@/components/ui';
import colors from '@/components/ui/colors';
import { createLogger } from '@/lib/logger';

// eslint-disable-next-line @typescript-eslint/no-require-imports
const logo = require('../../../assets/logo.png') as number;

const logger = createLogger('OTAUpdate');

interface OtaUpdateScreenProps {
  /** Called when OTA check is complete (whether update was applied or not). */
  onComplete: () => void;
}

/**
 * Full-screen OTA update gate.
 *
 * On mount:
 * 1. Checks for a pending Expo update.
 * 2. If found → downloads it while showing progress.
 * 3. Reloads the app to apply the update.
 * 4. If no update (or error) → calls onComplete so the app continues.
 *
 * This component should be rendered ONCE at the top of the component tree,
 * before any navigation or auth logic runs.
 */
export function OtaUpdateScreen({ onComplete }: OtaUpdateScreenProps) {
  const [checking, setChecking] = useState(true);
  const [downloading, setDownloading] = useState(false);

  const runCheck = useCallback(async () => {
    try {
      logger.info('Checking for OTA updates...');
      const update = await Updates.checkForUpdateAsync();

      if (!update.isAvailable) {
        logger.info('No OTA update available');
        onComplete();
        return;
      }

      logger.info('OTA update available — downloading');
      setChecking(false);
      setDownloading(true);

      await Updates.fetchUpdateAsync();
      logger.info('OTA update downloaded — reloading app');
      await Updates.reloadAsync();
      // App restarts here — onComplete never fires after reload.
    } catch (err) {
      // Non-fatal: if the OTA check fails (network, no update channel in dev, etc.)
      // just continue to the app. The user can still use the current version.
      logger.warn('OTA update check failed — continuing with current version', { error: err });
      onComplete();
    }
  }, [onComplete]);

  useEffect(() => {
    runCheck();
  }, [runCheck]);

  // Only show the modal while we're actively checking or downloading
  if (!checking && !downloading) return null;

  return (
    <Modal visible transparent={false} animationType="fade" statusBarTranslucent>
      <View style={styles.container}>
        <Image source={logo} style={styles.logo} resizeMode="contain" />
        <ActivityIndicator size="large" color={colors.primary[600]} style={styles.spinner} />
        <Text style={styles.title}>
          {downloading ? 'Installing Update...' : 'Checking for Updates...'}
        </Text>
        <Text style={styles.subtitle}>
          {downloading
            ? 'A new version is being installed. The app will restart shortly.'
            : 'Please wait while we check for the latest version.'}
        </Text>
      </View>
    </Modal>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: colors.white,
    alignItems: 'center',
    justifyContent: 'center',
    paddingHorizontal: 32,
  },
  logo: {
    width: 96,
    height: 96,
    marginBottom: 32,
  },
  spinner: {
    marginBottom: 24,
  },
  title: {
    fontFamily: 'Inter',
    fontSize: 20,
    fontWeight: '700',
    color: colors.neutral[900],
    marginBottom: 8,
    textAlign: 'center',
  },
  subtitle: {
    fontFamily: 'Inter',
    fontSize: 14,
    fontWeight: '400',
    color: colors.neutral[500],
    textAlign: 'center',
    lineHeight: 20,
    maxWidth: 280,
  },
});
```

- [ ] **Step 2: Commit**

```bash
git add src/components/ui/ota-update-screen.tsx
git commit -m "feat(mobile): add OTA update screen with download + reload"
```

---

## Task 8: Mobile — Force Update Gate + Soft Update Prompt

**Files:**
- Create: `mobile-app/src/components/ui/app-update-gate.tsx`

- [ ] **Step 1: Create the update gate component**

This is the main orchestrator. It:
1. Runs the OTA update check first
2. Then calls the backend version check
3. Renders the appropriate blocking/prompting UI

```typescript
import * as React from 'react';
import { useCallback, useEffect, useState } from 'react';
import { Image, Linking, Modal, Pressable, StyleSheet, View } from 'react-native';
import * as Updates from 'expo-updates';

import { Text } from '@/components/ui';
import colors from '@/components/ui/colors';
import { OtaUpdateScreen } from '@/components/ui/ota-update-screen';
import { checkAppVersion } from '@/lib/api/app-version';
import type { VersionCheckResult } from '@/lib/api/app-version';
import { createLogger } from '@/lib/logger';

// eslint-disable-next-line @typescript-eslint/no-require-imports
const logo = require('../../../assets/logo.png') as number;

const logger = createLogger('AppUpdateGate');

interface AppUpdateGateProps {
  children: React.ReactNode;
}

/**
 * Top-level gate wrapping the entire app navigation.
 *
 * Sequence:
 * 1. OTA update check (Expo Updates) — shown as "Checking for updates"
 * 2. Backend version check — may block the app or show a soft prompt
 * 3. Children render (app navigation)
 *
 * Placed inside `_layout.tsx` root layout so it runs before auth.
 */
export function AppUpdateGate({ children }: AppUpdateGateProps) {
  const [otaDone, setOtaDone] = useState(() => {
    // Skip OTA in dev — expo-updates is not available in development builds
    if (__DEV__) return true;
    // Also skip if not using updates channel (e.g. simulator builds)
    if (!Updates.isEnabled) return true;
    return false;
  });

  const [versionCheck, setVersionCheck] = useState<VersionCheckResult | null>(null);
  const [softDismissed, setSoftDismissed] = useState(false);
  const [checkDone, setCheckDone] = useState(false);

  const handleOtaComplete = useCallback(() => {
    setOtaDone(true);
  }, []);

  // After OTA check, run backend version check
  useEffect(() => {
    if (!otaDone) return;

    let cancelled = false;

    (async () => {
      try {
        const result = await checkAppVersion();
        if (!cancelled) {
          setVersionCheck(result);
          logger.info('Version check result', { verdict: result.updateRequired });
        }
      } catch (err) {
        // Network failure — allow through (don't block the user)
        logger.warn('Version check failed — allowing through', { error: err });
      } finally {
        if (!cancelled) setCheckDone(true);
      }
    })();

    return () => { cancelled = true; };
  }, [otaDone]);

  const handleOpenStore = useCallback(() => {
    if (versionCheck?.updateUrl) {
      Linking.openURL(versionCheck.updateUrl);
    }
  }, [versionCheck]);

  const handleDismissSoft = useCallback(() => {
    setSoftDismissed(true);
  }, []);

  // Phase 1: OTA update check
  if (!otaDone) {
    return <OtaUpdateScreen onComplete={handleOtaComplete} />;
  }

  // Phase 2: Waiting for backend version check (brief, usually <1s)
  // Don't show a loader here — let the app render underneath.
  // The blocking modal will appear if needed.

  // Phase 3: Maintenance mode — full block, no dismiss
  if (checkDone && versionCheck?.maintenanceMode) {
    return (
      <>
        {children}
        <Modal visible transparent={false} animationType="fade" statusBarTranslucent>
          <View style={styles.container}>
            <Image source={logo} style={styles.logo} resizeMode="contain" />
            <Text style={styles.title}>Under Maintenance</Text>
            <Text style={styles.message}>{versionCheck.message}</Text>
          </View>
        </Modal>
      </>
    );
  }

  // Phase 4: Force update — full block, only action is "Update Now"
  if (checkDone && versionCheck?.updateRequired === 'force') {
    return (
      <>
        {children}
        <Modal visible transparent={false} animationType="fade" statusBarTranslucent>
          <View style={styles.container}>
            <Image source={logo} style={styles.logo} resizeMode="contain" />
            <View style={styles.badge}>
              <Text style={styles.badgeText}>Update Required</Text>
            </View>
            <Text style={styles.title}>Please Update Avy ERP</Text>
            <Text style={styles.message}>{versionCheck.message}</Text>
            {versionCheck.updateUrl && (
              <Pressable
                style={({ pressed }) => [styles.primaryButton, pressed && styles.primaryButtonPressed]}
                onPress={handleOpenStore}
              >
                <Text style={styles.primaryButtonText}>Update Now</Text>
              </Pressable>
            )}
          </View>
        </Modal>
      </>
    );
  }

  // Phase 5: Soft update — dismissible prompt overlay
  if (checkDone && versionCheck?.updateRequired === 'soft' && !softDismissed) {
    return (
      <>
        {children}
        <Modal visible transparent animationType="fade" statusBarTranslucent>
          <View style={styles.overlay}>
            <View style={styles.promptCard}>
              <Text style={styles.promptTitle}>Update Available</Text>
              <Text style={styles.promptMessage}>{versionCheck.message}</Text>
              <View style={styles.promptButtons}>
                <Pressable
                  style={({ pressed }) => [styles.secondaryButton, pressed && styles.secondaryButtonPressed]}
                  onPress={handleDismissSoft}
                >
                  <Text style={styles.secondaryButtonText}>Later</Text>
                </Pressable>
                {versionCheck.updateUrl && (
                  <Pressable
                    style={({ pressed }) => [styles.primaryButton, pressed && styles.primaryButtonPressed]}
                    onPress={handleOpenStore}
                  >
                    <Text style={styles.primaryButtonText}>Update</Text>
                  </Pressable>
                )}
              </View>
            </View>
          </View>
        </Modal>
      </>
    );
  }

  // Phase 6: All clear — render app
  return <>{children}</>;
}

const styles = StyleSheet.create({
  // ── Full-screen blocking (maintenance + force) ──
  container: {
    flex: 1,
    backgroundColor: colors.white,
    alignItems: 'center',
    justifyContent: 'center',
    paddingHorizontal: 32,
  },
  logo: {
    width: 96,
    height: 96,
    marginBottom: 24,
  },
  badge: {
    backgroundColor: colors.warning[100],
    borderRadius: 20,
    paddingHorizontal: 16,
    paddingVertical: 6,
    marginBottom: 16,
  },
  badgeText: {
    fontFamily: 'Inter',
    fontSize: 13,
    fontWeight: '600',
    color: colors.warning[700],
  },
  title: {
    fontFamily: 'Inter',
    fontSize: 24,
    fontWeight: '700',
    color: colors.neutral[900],
    marginBottom: 12,
    textAlign: 'center',
  },
  message: {
    fontFamily: 'Inter',
    fontSize: 15,
    fontWeight: '400',
    color: colors.neutral[500],
    textAlign: 'center',
    lineHeight: 22,
    marginBottom: 32,
    maxWidth: 300,
  },

  // ── Buttons ──
  primaryButton: {
    backgroundColor: colors.primary[600],
    borderRadius: 14,
    paddingVertical: 16,
    paddingHorizontal: 40,
    minWidth: 160,
    alignItems: 'center',
  },
  primaryButtonPressed: {
    backgroundColor: colors.primary[700],
  },
  primaryButtonText: {
    fontFamily: 'Inter',
    fontSize: 16,
    fontWeight: '700',
    color: colors.white,
  },
  secondaryButton: {
    backgroundColor: colors.neutral[100],
    borderRadius: 14,
    paddingVertical: 16,
    paddingHorizontal: 32,
    minWidth: 120,
    alignItems: 'center',
  },
  secondaryButtonPressed: {
    backgroundColor: colors.neutral[200],
  },
  secondaryButtonText: {
    fontFamily: 'Inter',
    fontSize: 16,
    fontWeight: '600',
    color: colors.neutral[700],
  },

  // ── Soft update overlay ──
  overlay: {
    flex: 1,
    backgroundColor: 'rgba(0,0,0,0.5)',
    justifyContent: 'center',
    alignItems: 'center',
    paddingHorizontal: 24,
  },
  promptCard: {
    backgroundColor: colors.white,
    borderRadius: 24,
    padding: 28,
    width: '100%',
    maxWidth: 360,
    alignItems: 'center',
  },
  promptTitle: {
    fontFamily: 'Inter',
    fontSize: 20,
    fontWeight: '700',
    color: colors.neutral[900],
    marginBottom: 8,
  },
  promptMessage: {
    fontFamily: 'Inter',
    fontSize: 14,
    fontWeight: '400',
    color: colors.neutral[500],
    textAlign: 'center',
    lineHeight: 20,
    marginBottom: 24,
  },
  promptButtons: {
    flexDirection: 'row',
    gap: 12,
  },
});
```

- [ ] **Step 2: Commit**

```bash
git add src/components/ui/app-update-gate.tsx
git commit -m "feat(mobile): add AppUpdateGate with force/soft/maintenance modes"
```

---

## Task 9: Mobile — Integrate Gate into Root Layout

**Files:**
- Modify: `mobile-app/src/app/_layout.tsx`

- [ ] **Step 1: Wrap the app with AppUpdateGate**

In `mobile-app/src/app/_layout.tsx`, add the import at the top:

```typescript
import { AppUpdateGate } from '@/components/ui/app-update-gate';
```

Then wrap the `<Stack>` inside the `RootLayout` function with `<AppUpdateGate>`:

Replace the return in `RootLayout` (around line 45-56):

```typescript
  return (
    <Providers>
      <AppUpdateGate>
        <Stack screenOptions={{ animation: 'fade' }}>
          <Stack.Screen name="(app)" options={{ headerShown: false }} />
          <Stack.Screen name="onboarding" options={{ headerShown: false }} />
          <Stack.Screen name="login" options={{ headerShown: false }} />
          <Stack.Screen name="forgot-password" options={{ headerShown: false }} />
          <Stack.Screen name="mfa-setup-voluntary" options={{ headerShown: false }} />
          <Stack.Screen name="change-password" options={{ headerShown: false }} />
        </Stack>
      </AppUpdateGate>
    </Providers>
  );
```

The gate renders BEFORE any navigation, so it blocks even the login screen when a force update or maintenance is active.

- [ ] **Step 2: Verify app starts**

Run:
```bash
cd mobile-app && pnpm start
```
Expected: App launches. In dev mode, OTA check is skipped (the `__DEV__` guard), version check runs against the backend. If no `AppVersionConfig` exists in the DB, the check returns `updateRequired: "none"` and the app loads normally.

- [ ] **Step 3: Commit**

```bash
git add src/app/_layout.tsx
git commit -m "feat(mobile): integrate AppUpdateGate in root layout"
```

---

## Task 10: Seed Initial Config + End-to-End Verification

- [ ] **Step 1: Insert test config via API**

Start the backend and use curl to create an Android config:

```bash
# Get a super admin token first (adjust login creds as needed)
TOKEN="<your-super-admin-jwt>"

# Create ANDROID config — allows current version through
curl -X POST http://localhost:3000/api/v1/platform/app-versions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "platform": "ANDROID",
    "latestVersion": "1.0.5",
    "minimumVersion": "1.0.0",
    "recommendedVersion": "1.0.5",
    "updateUrl": "https://play.google.com/store/apps/details?id=com.avyren.erp",
    "maintenanceMode": false,
    "isActive": true
  }'
```

- [ ] **Step 2: Test public version check**

```bash
# Should return updateRequired: "none" (1.0.5 >= 1.0.0 minimum)
curl "http://localhost:3000/api/v1/app-version/check?platform=ANDROID&version=1.0.5"

# Should return updateRequired: "force" (0.9.0 < 1.0.0 minimum)
curl "http://localhost:3000/api/v1/app-version/check?platform=ANDROID&version=0.9.0"

# Should return updateRequired: "soft" (1.0.2 < 1.0.5 recommended, >= 1.0.0 minimum)
curl "http://localhost:3000/api/v1/app-version/check?platform=ANDROID&version=1.0.2"
```

- [ ] **Step 3: Test maintenance mode**

```bash
# Update config to enable maintenance mode
curl -X PATCH "http://localhost:3000/api/v1/platform/app-versions/<config-id>" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{ "maintenanceMode": true, "maintenanceMessage": "We are upgrading our servers. Back in 30 minutes." }'

# Should return maintenanceMode: true for ANY version
curl "http://localhost:3000/api/v1/app-version/check?platform=ANDROID&version=99.99.99"
```

- [ ] **Step 4: Commit any fixes**

```bash
git add -A
git commit -m "feat(app-version): complete version control + force update system"
```

---

## Summary: How to Use in Production

### Pushing a Play Store update:

1. Bump version in `mobile-app/package.json` (e.g., `1.0.5` → `1.1.0`)
2. Build: `eas build --profile production --platform android`
3. Upload to Play Store → wait 24-48hr for approval
4. **After approval**: Update backend config via super admin panel or API:
   - Set `latestVersion: "1.1.0"`
   - Set `recommendedVersion: "1.1.0"` (soft prompt for older versions)
   - Optionally set `minimumVersion: "1.1.0"` (force update, blocks all older versions)
5. Users on old versions will see the force/soft update screen on next app launch

### Pushing an OTA update (instant):

```bash
cd mobile-app && eas update --branch production --message "hotfix: ..."
```
No backend config change needed. OTA updates are checked and applied automatically on app launch.

### Maintenance mode (emergency):

Update backend config: `{ "maintenanceMode": true, "maintenanceMessage": "..." }`
All app users see the maintenance screen on next launch. Toggle off when done.
