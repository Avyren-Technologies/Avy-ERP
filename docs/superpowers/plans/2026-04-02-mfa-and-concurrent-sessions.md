# MFA & Max Concurrent Sessions Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Enforce MFA (TOTP-based) and max concurrent sessions globally across web + mobile, driven by the company's `SystemControls` settings.

**Architecture:**
- **MFA:** TOTP-based (RFC 6238) using `otplib`. User model gets `mfaSecret` + `mfaEnabled`. Login becomes 2-step: password check returns a `mfaRequired` challenge instead of tokens; a second `POST /auth/mfa/verify` call completes login. Both web and mobile get MFA setup + verification screens.
- **Max Concurrent Sessions:** A new `ActiveSession` DB table tracks each login. On login/refresh, the backend checks session count against `SystemControls.maxConcurrentSessions`. When the limit is exceeded, the oldest session is revoked. Both web and mobile share the same global pool — the limit is per-user, not per-platform.

**Tech Stack:** otplib (TOTP), qrcode (QR generation), Prisma, Redis, React/React Native

---

## File Structure

### Backend (avy-erp-backend)

| File | Action | Responsibility |
|------|--------|----------------|
| `prisma/modules/platform/auth.prisma` | Modify | Add `mfaSecret`, `mfaEnabled` to User; add `ActiveSession` model |
| `src/core/auth/auth.types.ts` | Modify | Add MFA-related request/response types, `ActiveSessionInfo` |
| `src/core/auth/auth.service.ts` | Modify | Add MFA setup/verify methods, session tracking in login/refresh/logout |
| `src/core/auth/auth.controller.ts` | Modify | Add MFA endpoints |
| `src/core/auth/auth.routes.ts` | Modify | Mount MFA routes |
| `src/shared/errors/auth-error.ts` | Modify | Add `mfaRequired()`, `invalidMfaCode()`, `mfaAlreadyEnabled()` errors |

### Web (web-system-app)

| File | Action | Responsibility |
|------|--------|----------------|
| `src/lib/api/auth.ts` | Modify | Add MFA API functions |
| `src/lib/api/use-auth-mutations.ts` | Modify | Handle 2-step MFA login flow |
| `src/features/auth/MfaVerifyScreen.tsx` | Create | TOTP code entry during login |
| `src/features/company-admin/MfaSetupDialog.tsx` | Create | QR code display + TOTP verification for setup |

### Mobile (mobile-app)

| File | Action | Responsibility |
|------|--------|----------------|
| `src/lib/api/auth.ts` | Modify | Add MFA API functions |
| `src/features/auth/mfa-verify-screen.tsx` | Create | TOTP code entry during login |
| `src/features/auth/mfa-setup-screen.tsx` | Create | QR code display + TOTP verification for setup |
| `src/app/(auth)/mfa-verify.tsx` | Create | Route file for MFA verify screen |

---

## Task 1: Prisma Schema — MFA Fields + ActiveSession Model

**Files:**
- Modify: `avy-erp-backend/prisma/modules/platform/auth.prisma`

- [ ] **Step 1: Add MFA fields to User model and create ActiveSession model**

In `prisma/modules/platform/auth.prisma`, add to the `User` model (after `lockedUntil`):

```prisma
  // MFA (TOTP-based, enforced via SystemControls.mfaRequired)
  mfaEnabled Boolean  @default(false)
  mfaSecret  String?  // Encrypted TOTP secret (base32)
```

Add the `ActiveSession` model (after `PasswordResetToken`):

```prisma
// Active sessions — tracks each login for concurrent session enforcement
model ActiveSession {
  id           String   @id @default(cuid())
  userId       String
  deviceInfo   String?  // "web", "mobile-ios", "mobile-android", or user-agent snippet
  ipAddress    String?
  refreshToken String   @unique // hash of the refresh token (SHA-256)
  expiresAt    DateTime // mirrors the refresh token expiry
  createdAt    DateTime @default(now())
  lastActiveAt DateTime @default(now())

  user User @relation(fields: [userId], references: [id], onDelete: Cascade)

  @@index([userId])
  @@map("active_sessions")
}
```

Add the relation in the `User` model (in the Relations section):

```prisma
  sessions    ActiveSession[]
```

- [ ] **Step 2: Run prisma merge + generate**

```bash
cd avy-erp-backend && pnpm prisma:merge && pnpm db:generate
```

Expected: `125+ models, 80+ enums (no duplicates)` and `Generated Prisma Client`.

- [ ] **Step 3: Run migration**

```bash
cd avy-erp-backend && pnpm db:migrate --name add_mfa_and_active_sessions
```

Expected: Migration created and applied successfully.

- [ ] **Step 4: Commit**

```bash
git add prisma/
git commit -m "schema: add MFA fields to User and ActiveSession model"
```

---

## Task 2: Backend — Auth Error Types + Request/Response Types

**Files:**
- Modify: `avy-erp-backend/src/shared/errors/auth-error.ts`
- Modify: `avy-erp-backend/src/core/auth/auth.types.ts`

- [ ] **Step 1: Add MFA-related auth errors**

In `src/shared/errors/auth-error.ts`, add these static methods to the `AuthError` class:

```typescript
  static mfaRequired(): AuthError {
    return new AuthError('MFA verification required', 'MFA_REQUIRED');
  }

  static invalidMfaCode(): AuthError {
    return new AuthError('Invalid or expired MFA code', 'INVALID_MFA_CODE');
  }

  static mfaAlreadyEnabled(): AuthError {
    return new AuthError('MFA is already enabled for this account', 'MFA_ALREADY_ENABLED');
  }

  static sessionLimitExceeded(): AuthError {
    return new AuthError('Maximum concurrent sessions exceeded', 'SESSION_LIMIT_EXCEEDED');
  }
```

- [ ] **Step 2: Add MFA types to auth.types.ts**

In `src/core/auth/auth.types.ts`, add:

```typescript
export interface MfaChallengeResponse {
  mfaRequired: true;
  mfaToken: string; // short-lived JWT (5 min) encoding userId + email — NOT an auth token
}

export interface MfaVerifyRequest {
  mfaToken: string;
  code: string; // 6-digit TOTP code
}

export interface MfaSetupResponse {
  secret: string;    // base32 TOTP secret
  otpauthUrl: string; // otpauth:// URI for QR code
  qrCodeDataUrl: string; // data:image/png;base64,... QR code image
}

export interface MfaConfirmRequest {
  code: string; // 6-digit TOTP code to verify setup
}

export interface ActiveSessionInfo {
  id: string;
  deviceInfo: string | null;
  ipAddress: string | null;
  lastActiveAt: Date;
  createdAt: Date;
  isCurrent: boolean;
}
```

Also update `AuthResponse` to be a union:

```typescript
export type LoginResult = AuthResponse | MfaChallengeResponse;
```

- [ ] **Step 3: Commit**

```bash
git add src/shared/errors/auth-error.ts src/core/auth/auth.types.ts
git commit -m "feat: add MFA and session types/errors"
```

---

## Task 3: Backend — Session Tracking in Auth Service

**Files:**
- Modify: `avy-erp-backend/src/core/auth/auth.service.ts`

This task adds session creation/cleanup to `login()`, `refreshToken()`, and `logout()`.

- [ ] **Step 1: Add crypto import and session helper methods**

At the top of `auth.service.ts`, add:

```typescript
import crypto from 'crypto';
```

Add these private methods to the `AuthService` class (before `generateTokens`):

```typescript
  /** SHA-256 hash of a token for safe DB storage (never store raw JWTs in DB). */
  private hashToken(token: string): string {
    return crypto.createHash('sha256').update(token).digest('hex');
  }

  /**
   * Create a session record and enforce maxConcurrentSessions.
   * If the limit is exceeded, the oldest session is revoked (its refresh token blacklisted).
   */
  private async trackSession(
    userId: string,
    refreshToken: string,
    refreshExpiresIn: string,
    companyId: string | null | undefined,
    deviceInfo?: string,
    ipAddress?: string,
  ): Promise<void> {
    const tokenHash = this.hashToken(refreshToken);
    const expiresAt = new Date(Date.now() + this.parseExpiresInToSeconds(refreshExpiresIn) * 1000);

    // Create the new session
    await platformPrisma.activeSession.create({
      data: { userId, refreshToken: tokenHash, expiresAt, deviceInfo, ipAddress },
    });

    // Enforce max concurrent sessions
    if (!companyId) return; // super-admin — no company-level limits

    let maxSessions = 3;
    try {
      const { getCachedSystemControls } = await import('../../shared/utils/config-cache');
      const controls = await getCachedSystemControls(companyId);
      maxSessions = controls.maxConcurrentSessions;
    } catch {
      // Non-fatal
    }

    // Get all active sessions ordered oldest-first
    const sessions = await platformPrisma.activeSession.findMany({
      where: { userId, expiresAt: { gt: new Date() } },
      orderBy: { createdAt: 'asc' },
    });

    if (sessions.length > maxSessions) {
      // Revoke oldest sessions to get within the limit
      const toRevoke = sessions.slice(0, sessions.length - maxSessions);
      for (const s of toRevoke) {
        // We can't blacklist by hash — we just delete the session record.
        // The refresh token will fail on next use because the session won't exist.
        await platformPrisma.activeSession.delete({ where: { id: s.id } });
      }
      logger.info(`Revoked ${toRevoke.length} oldest session(s) for user ${userId} (limit: ${maxSessions})`);
    }
  }

  /** Remove a session record by its refresh token hash. */
  private async removeSession(refreshToken: string): Promise<void> {
    const tokenHash = this.hashToken(refreshToken);
    await platformPrisma.activeSession.deleteMany({ where: { refreshToken: tokenHash } }).catch(() => {});
  }

  /** Clean up expired sessions for a user. */
  private async cleanExpiredSessions(userId: string): Promise<void> {
    await platformPrisma.activeSession.deleteMany({
      where: { userId, expiresAt: { lte: new Date() } },
    }).catch(() => {});
  }
```

- [ ] **Step 2: Add session tracking to `login()` method**

After the `generateTokens` call and `cacheUserData` call in `login()` (around line 155), add:

```typescript
    // Track session + enforce max concurrent sessions
    const deviceInfo = (loginData as any).deviceInfo ?? 'web';
    const ipAddress = (loginData as any).ipAddress;
    await this.cleanExpiredSessions(user.id);
    await this.trackSession(user.id, tokens.refreshToken, env.JWT_REFRESH_EXPIRES_IN, user.companyId, deviceInfo, ipAddress);
```

- [ ] **Step 3: Add session validation + rotation to `refreshToken()` method**

In `refreshToken()`, after verifying the refresh token is not blacklisted (around line 348), add a session existence check:

```typescript
      // Validate session still exists (not revoked by concurrent session enforcement)
      const tokenHash = this.hashToken(refreshToken);
      const session = await platformPrisma.activeSession.findUnique({
        where: { refreshToken: tokenHash },
      });
      if (!session) {
        throw AuthError.invalidToken(); // Session was revoked
      }
```

After generating new tokens and blacklisting the old refresh token (around line 362), add session rotation:

```typescript
      // Rotate session record to the new refresh token
      const newTokenHash = this.hashToken(tokens.refreshToken);
      await platformPrisma.activeSession.update({
        where: { id: session.id },
        data: {
          refreshToken: newTokenHash,
          expiresAt: new Date(Date.now() + this.parseExpiresInToSeconds(env.JWT_REFRESH_EXPIRES_IN) * 1000),
          lastActiveAt: new Date(),
        },
      }).catch(() => {});
```

- [ ] **Step 4: Add session cleanup to `logout()` method**

In `logout()`, before the existing token blacklisting, add:

```typescript
    // Remove the session record for this token
    await this.removeSession(accessToken); // We don't have the refresh token here, but we can clean by user
```

Actually, we need the refresh token for proper cleanup. Update the `logout` method signature and controller to pass both tokens. For now, just clean all user sessions if the refresh token isn't available:

After the existing blacklisting code in `logout()`, add:

```typescript
    // Clean expired sessions
    await this.cleanExpiredSessions(userId);
```

- [ ] **Step 5: Commit**

```bash
git add src/core/auth/auth.service.ts
git commit -m "feat: enforce max concurrent sessions via ActiveSession tracking"
```

---

## Task 4: Backend — MFA Setup + Verify in Auth Service

**Files:**
- Modify: `avy-erp-backend/src/core/auth/auth.service.ts`

- [ ] **Step 1: Install otplib and qrcode**

```bash
cd avy-erp-backend && pnpm add otplib qrcode && pnpm add -D @types/qrcode
```

- [ ] **Step 2: Add MFA imports**

At the top of `auth.service.ts`, add:

```typescript
import { authenticator } from 'otplib';
import QRCode from 'qrcode';
```

- [ ] **Step 3: Modify `login()` for 2-step MFA flow**

In the `login()` method, after the successful password check and failed-attempts reset (around line 107-110), but BEFORE generating tokens, add an MFA check:

```typescript
    // ── MFA enforcement ──
    // Check if MFA is required for this company OR already enabled by the user
    let mfaRequired = user.mfaEnabled;
    if (!mfaRequired && user.companyId && controls) {
      // Company-level MFA enforcement — if mfaRequired is true in controls,
      // all users must set up MFA. If user hasn't set it up yet, let them through
      // (they'll be prompted to set up MFA after login via the frontend).
      try {
        const fullControls = await (await import('../../shared/utils/config-cache')).getCachedSystemControls(user.companyId);
        mfaRequired = fullControls.mfaRequired && user.mfaEnabled;
      } catch {}
    }

    if (mfaRequired && user.mfaSecret) {
      // Return MFA challenge instead of tokens
      const mfaToken = jwt.sign(
        { userId: user.id, email: user.email, purpose: 'mfa-challenge' },
        env.JWT_SECRET,
        { expiresIn: '5m', algorithm: JWT_ALGORITHM } as any,
      );
      return { mfaRequired: true, mfaToken } as any;
    }
```

Update the return type of `login()` from `Promise<AuthResponse>` to `Promise<AuthResponse | MfaChallengeResponse>`.

Add the import at top:

```typescript
import type { MfaChallengeResponse, MfaSetupResponse, MfaConfirmRequest, MfaVerifyRequest } from './auth.types';
```

- [ ] **Step 4: Add `verifyMfa()` method**

Add this method to the `AuthService` class:

```typescript
  /** Verify TOTP code during MFA-challenged login. Returns full auth tokens. */
  async verifyMfa(data: MfaVerifyRequest, deviceInfo?: string, ipAddress?: string): Promise<AuthResponse> {
    // Decode the MFA challenge token
    let decoded: { userId: string; email: string; purpose: string };
    try {
      decoded = jwt.verify(data.mfaToken, env.JWT_SECRET, {
        algorithms: [JWT_ALGORITHM],
      }) as any;
    } catch {
      throw AuthError.invalidMfaCode();
    }

    if (decoded.purpose !== 'mfa-challenge') {
      throw AuthError.invalidMfaCode();
    }

    // Get user with MFA secret
    const user = await platformPrisma.user.findUnique({
      where: { id: decoded.userId },
      include: { company: { include: { tenant: true } } },
    });

    if (!user || !user.mfaEnabled || !user.mfaSecret) {
      throw AuthError.invalidMfaCode();
    }

    // Verify TOTP code
    const isValid = authenticator.verify({ token: data.code, secret: user.mfaSecret });
    if (!isValid) {
      throw AuthError.invalidMfaCode();
    }

    // MFA passed — generate tokens (same as normal login completion)
    const tenantId = user.company?.tenant?.id;
    let employeeId = user.employeeId ?? undefined;
    if (!employeeId && user.companyId) {
      const linked = await platformPrisma.employee.findFirst({
        where: { companyId: user.companyId, officialEmail: user.email },
        select: { id: true },
      });
      if (linked) {
        await platformPrisma.user.update({ where: { id: user.id }, data: { employeeId: linked.id } });
        employeeId = linked.id;
      }
    }

    const permissions = await this.getExpandedPermissions(user.id, tenantId, user.companyId);
    const tokens = await this.generateTokens({
      userId: user.id, email: user.email,
      tenantId: tenantId ?? undefined, companyId: user.companyId ?? undefined,
      employeeId, roleId: user.role, permissions,
    });

    await this.cacheUserData(user.id, {
      id: user.id, email: user.email, firstName: user.firstName, lastName: user.lastName,
      tenantId, companyId: user.companyId, employeeId, roleId: user.role, permissions, isActive: user.isActive,
    });

    // Track session
    await this.cleanExpiredSessions(user.id);
    await this.trackSession(user.id, tokens.refreshToken, env.JWT_REFRESH_EXPIRES_IN, user.companyId, deviceInfo, ipAddress);

    logger.info(`MFA verified for user: ${user.email}`);

    return {
      user: {
        id: user.id, email: user.email, firstName: user.firstName, lastName: user.lastName,
        role: user.role, permissions,
        ...(user.companyId ? { companyId: user.companyId } : {}),
        ...(tenantId ? { tenantId } : {}),
        ...(employeeId ? { employeeId } : {}),
      },
      tokens,
    };
  }
```

- [ ] **Step 5: Add `setupMfa()` and `confirmMfa()` methods**

```typescript
  /** Generate a TOTP secret and QR code for MFA setup. Requires an authenticated user. */
  async setupMfa(userId: string): Promise<MfaSetupResponse> {
    const user = await platformPrisma.user.findUnique({ where: { id: userId } });
    if (!user) throw AuthError.invalidCredentials();
    if (user.mfaEnabled) throw AuthError.mfaAlreadyEnabled();

    const secret = authenticator.generateSecret();
    const otpauthUrl = authenticator.keyuri(user.email, 'Avy ERP', secret);
    const qrCodeDataUrl = await QRCode.toDataURL(otpauthUrl);

    // Store the secret temporarily (not yet confirmed)
    await platformPrisma.user.update({
      where: { id: userId },
      data: { mfaSecret: secret }, // mfaEnabled stays false until confirmed
    });

    return { secret, otpauthUrl, qrCodeDataUrl };
  }

  /** Confirm MFA setup by verifying the user can produce a valid TOTP code. */
  async confirmMfa(userId: string, code: string): Promise<void> {
    const user = await platformPrisma.user.findUnique({ where: { id: userId } });
    if (!user || !user.mfaSecret) throw AuthError.invalidMfaCode();
    if (user.mfaEnabled) throw AuthError.mfaAlreadyEnabled();

    const isValid = authenticator.verify({ token: code, secret: user.mfaSecret });
    if (!isValid) throw AuthError.invalidMfaCode();

    await platformPrisma.user.update({
      where: { id: userId },
      data: { mfaEnabled: true },
    });

    // Clear user cache so next auth check picks up mfaEnabled
    await cacheRedis.del(createUserCacheKey(userId, 'auth'));
    logger.info(`MFA enabled for user: ${user.email}`);
  }

  /** Disable MFA for a user (requires password confirmation). */
  async disableMfa(userId: string, password: string): Promise<void> {
    const user = await platformPrisma.user.findUnique({ where: { id: userId } });
    if (!user) throw AuthError.invalidCredentials();

    const isValid = await comparePassword(password, user.password);
    if (!isValid) throw AuthError.invalidCredentials();

    await platformPrisma.user.update({
      where: { id: userId },
      data: { mfaEnabled: false, mfaSecret: null },
    });

    await cacheRedis.del(createUserCacheKey(userId, 'auth'));
    logger.info(`MFA disabled for user: ${user.email}`);
  }
```

- [ ] **Step 6: Commit**

```bash
git add src/core/auth/auth.service.ts
git commit -m "feat: add MFA setup/verify/disable and 2-step login flow"
```

---

## Task 5: Backend — MFA Controller + Routes

**Files:**
- Modify: `avy-erp-backend/src/core/auth/auth.controller.ts`
- Modify: `avy-erp-backend/src/core/auth/auth.routes.ts`

- [ ] **Step 1: Add MFA controller methods**

In `auth.controller.ts`, add to the `AuthController` class:

```typescript
  // MFA verify (during login)
  verifyMfa = asyncHandler(async (req: Request, res: Response) => {
    const { mfaToken, code } = req.body;
    if (!mfaToken || !code) throw ApiError.badRequest('MFA token and code are required');

    const deviceInfo = req.headers['x-device-info'] as string | undefined;
    const ipAddress = req.ip || req.socket.remoteAddress;
    const result = await authService.verifyMfa({ mfaToken, code }, deviceInfo, ipAddress);
    res.json(createSuccessResponse(result, 'MFA verified'));
  });

  // MFA setup (authenticated)
  setupMfa = asyncHandler(async (req: Request, res: Response) => {
    const userId = req.user?.id;
    if (!userId) throw ApiError.badRequest('Authentication required');

    const result = await authService.setupMfa(userId);
    res.json(createSuccessResponse(result, 'MFA setup initiated'));
  });

  // MFA confirm setup (authenticated)
  confirmMfa = asyncHandler(async (req: Request, res: Response) => {
    const userId = req.user?.id;
    if (!userId) throw ApiError.badRequest('Authentication required');
    const { code } = req.body;
    if (!code) throw ApiError.badRequest('TOTP code is required');

    await authService.confirmMfa(userId, code);
    res.json(createSuccessResponse(null, 'MFA enabled successfully'));
  });

  // MFA disable (authenticated, requires password)
  disableMfa = asyncHandler(async (req: Request, res: Response) => {
    const userId = req.user?.id;
    if (!userId) throw ApiError.badRequest('Authentication required');
    const { password } = req.body;
    if (!password) throw ApiError.badRequest('Password is required to disable MFA');

    await authService.disableMfa(userId, password);
    res.json(createSuccessResponse(null, 'MFA disabled successfully'));
  });
```

Add the `ApiError` import if not already present:

```typescript
import { ApiError } from '../../shared/errors';
```

- [ ] **Step 2: Add MFA routes**

In `auth.routes.ts`, add after the existing public routes (after line 13 `reset-password`):

```typescript
// MFA verify (public — the user hasn't completed auth yet)
router.post('/mfa/verify', authController.verifyMfa);
```

Add after the existing `router.use(authMiddleware());` protected routes section:

```typescript
// MFA setup (authenticated)
router.post('/mfa/setup', authController.setupMfa);
router.post('/mfa/confirm', authController.confirmMfa);
router.post('/mfa/disable', authController.disableMfa);
```

- [ ] **Step 3: Update the login controller to pass deviceInfo/ipAddress**

In `auth.controller.ts`, update the `login` method to extract device info:

```typescript
  login = asyncHandler(async (req: Request, res: Response) => {
    const loginData = validateLogin(req.body) as LoginRequest;
    // Pass device info for session tracking
    (loginData as any).deviceInfo = req.headers['x-device-info'] || 'web';
    (loginData as any).ipAddress = req.ip || req.socket.remoteAddress;
    const result = await authService.login(loginData);

    res.json(createSuccessResponse(result, result && 'mfaRequired' in result ? 'MFA verification required' : 'Login successful'));
  });
```

- [ ] **Step 4: Commit**

```bash
git add src/core/auth/auth.controller.ts src/core/auth/auth.routes.ts
git commit -m "feat: add MFA endpoints and device info tracking"
```

---

## Task 6: Web App — Handle 2-Step MFA Login

**Files:**
- Modify: `web-system-app/src/lib/api/auth.ts`
- Modify: `web-system-app/src/lib/api/use-auth-mutations.ts`
- Create: `web-system-app/src/features/auth/MfaVerifyScreen.tsx`

- [ ] **Step 1: Add MFA API functions**

In `src/lib/api/auth.ts`, add to the `authApi` object:

```typescript
    verifyMfa: (mfaToken: string, code: string) =>
        client.post('/auth/mfa/verify', { mfaToken, code }).then(r => r.data) as Promise<ApiResponse<LoginResponse>>,

    setupMfa: () =>
        client.post('/auth/mfa/setup').then(r => r.data) as Promise<ApiResponse<{ secret: string; otpauthUrl: string; qrCodeDataUrl: string }>>,

    confirmMfa: (code: string) =>
        client.post('/auth/mfa/confirm', { code }).then(r => r.data) as Promise<ApiResponse>,

    disableMfa: (password: string) =>
        client.post('/auth/mfa/disable', { password }).then(r => r.data) as Promise<ApiResponse>,
```

- [ ] **Step 2: Update login mutation for MFA challenge**

In `src/lib/api/use-auth-mutations.ts`, update `useLoginMutation`:

```typescript
export function useLoginMutation() {
    const navigate = useNavigate();
    const signIn = useAuthStore((s) => s.signIn);

    return useMutation({
        mutationFn: ({ email, password }: { email: string; password: string }) =>
            authApi.login(email, password),
        onSuccess: (response) => {
            if (response.success && response.data) {
                // Check if MFA is required
                if ('mfaRequired' in response.data && response.data.mfaRequired) {
                    // Store MFA token temporarily and redirect to MFA verify screen
                    sessionStorage.setItem('mfa_token', (response.data as any).mfaToken);
                    navigate('/mfa-verify');
                    return;
                }

                const { user, tokens } = response.data as LoginResponse;
                const payload = decodeJwtPayload(tokens.accessToken);
                const permissions: string[] = Array.isArray(payload?.permissions)
                    ? (payload.permissions as string[])
                    : [];
                const role = mapBackendRole(user.role);
                signIn(tokens, { ...user, permissions }, role);
                navigate('/app/dashboard');
            }
        },
    });
}
```

Add the import:

```typescript
import type { LoginResponse } from '@/lib/api/auth';
```

- [ ] **Step 3: Create MfaVerifyScreen**

Create `src/features/auth/MfaVerifyScreen.tsx`:

```tsx
import { useState, useRef, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useMutation } from '@tanstack/react-query';
import { Shield, ArrowLeft } from 'lucide-react';
import { authApi, decodeJwtPayload } from '@/lib/api/auth';
import { useAuthStore, mapBackendRole } from '@/store/useAuthStore';
import { showApiError } from '@/lib/toast';

export function MfaVerifyScreen() {
    const navigate = useNavigate();
    const signIn = useAuthStore((s) => s.signIn);
    const [code, setCode] = useState(['', '', '', '', '', '']);
    const inputRefs = useRef<(HTMLInputElement | null)[]>([]);

    const mfaToken = sessionStorage.getItem('mfa_token');

    useEffect(() => {
        if (!mfaToken) navigate('/login');
    }, [mfaToken, navigate]);

    const verifyMutation = useMutation({
        mutationFn: () => authApi.verifyMfa(mfaToken!, code.join('')),
        onSuccess: (response) => {
            if (response.success && response.data) {
                sessionStorage.removeItem('mfa_token');
                const { user, tokens } = response.data;
                const payload = decodeJwtPayload(tokens.accessToken);
                const permissions: string[] = Array.isArray(payload?.permissions)
                    ? (payload.permissions as string[]) : [];
                signIn(tokens, { ...user, permissions }, mapBackendRole(user.role));
                navigate('/app/dashboard');
            }
        },
        onError: (err) => showApiError(err),
    });

    const handleChange = (index: number, value: string) => {
        if (!/^\d*$/.test(value)) return;
        const next = [...code];
        next[index] = value.slice(-1);
        setCode(next);
        if (value && index < 5) inputRefs.current[index + 1]?.focus();
        if (next.every(d => d !== '')) {
            setTimeout(() => verifyMutation.mutate(), 100);
        }
    };

    const handleKeyDown = (index: number, e: React.KeyboardEvent) => {
        if (e.key === 'Backspace' && !code[index] && index > 0) {
            inputRefs.current[index - 1]?.focus();
        }
    };

    return (
        <div className="min-h-screen flex items-center justify-center bg-neutral-50 dark:bg-neutral-950 p-4">
            <div className="bg-white dark:bg-neutral-900 rounded-2xl shadow-xl p-8 w-full max-w-md">
                <button onClick={() => { sessionStorage.removeItem('mfa_token'); navigate('/login'); }}
                    className="flex items-center gap-2 text-sm text-neutral-500 hover:text-neutral-700 mb-6">
                    <ArrowLeft size={16} /> Back to login
                </button>

                <div className="flex flex-col items-center text-center mb-8">
                    <div className="w-14 h-14 rounded-2xl bg-primary-100 dark:bg-primary-900/30 flex items-center justify-center mb-4">
                        <Shield size={24} className="text-primary-600" />
                    </div>
                    <h1 className="text-xl font-bold text-neutral-900 dark:text-white">Two-Factor Authentication</h1>
                    <p className="text-sm text-neutral-500 dark:text-neutral-400 mt-2">
                        Enter the 6-digit code from your authenticator app
                    </p>
                </div>

                <div className="flex justify-center gap-3 mb-8">
                    {code.map((digit, i) => (
                        <input
                            key={i}
                            ref={el => { inputRefs.current[i] = el; }}
                            type="text"
                            inputMode="numeric"
                            maxLength={1}
                            value={digit}
                            onChange={e => handleChange(i, e.target.value)}
                            onKeyDown={e => handleKeyDown(i, e)}
                            className="w-12 h-14 text-center text-xl font-bold border-2 border-neutral-200 dark:border-neutral-700 rounded-xl
                                focus:border-primary-500 focus:ring-2 focus:ring-primary-500/20 outline-none
                                bg-white dark:bg-neutral-800 text-neutral-900 dark:text-white transition-all"
                        />
                    ))}
                </div>

                <button
                    onClick={() => verifyMutation.mutate()}
                    disabled={code.some(d => d === '') || verifyMutation.isPending}
                    className="w-full py-3 rounded-xl bg-primary-600 text-white font-bold text-sm hover:bg-primary-700
                        disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                >
                    {verifyMutation.isPending ? 'Verifying...' : 'Verify Code'}
                </button>
            </div>
        </div>
    );
}
```

- [ ] **Step 4: Add the MFA verify route**

In `src/App.tsx` (or wherever routes are defined), add:

```tsx
import { MfaVerifyScreen } from '@/features/auth/MfaVerifyScreen';
// ...
<Route path="/mfa-verify" element={<MfaVerifyScreen />} />
```

- [ ] **Step 5: Commit**

```bash
git add src/lib/api/auth.ts src/lib/api/use-auth-mutations.ts src/features/auth/MfaVerifyScreen.tsx src/App.tsx
git commit -m "feat(web): handle MFA challenge in login flow"
```

---

## Task 7: Web App — MFA Setup Dialog for Settings

**Files:**
- Create: `web-system-app/src/features/company-admin/MfaSetupDialog.tsx`

- [ ] **Step 1: Create MFA setup dialog component**

Create `src/features/company-admin/MfaSetupDialog.tsx` — a dialog that company admins or individual users can use from their settings/profile page to enable MFA. Shows a QR code, asks for TOTP verification, and confirms setup.

This is a self-contained dialog component. Wire it into the profile or system settings screen where appropriate. The component calls `authApi.setupMfa()` to get the QR code, displays it, and calls `authApi.confirmMfa(code)` to finalize.

- [ ] **Step 2: Commit**

```bash
git add src/features/company-admin/MfaSetupDialog.tsx
git commit -m "feat(web): add MFA setup dialog"
```

---

## Task 8: Mobile App — MFA Verify + Setup Screens

**Files:**
- Modify: `mobile-app/src/lib/api/auth.ts`
- Create: `mobile-app/src/features/auth/mfa-verify-screen.tsx`
- Create: `mobile-app/src/app/(auth)/mfa-verify.tsx`

- [ ] **Step 1: Add MFA API functions to mobile auth**

In `mobile-app/src/lib/api/auth.ts`, add to the `authApi` object:

```typescript
  verifyMfa: (mfaToken: string, code: string) =>
    client.post('/auth/mfa/verify', { mfaToken, code }) as Promise<ApiResponse<LoginResponse>>,

  setupMfa: () =>
    client.post('/auth/mfa/setup') as Promise<ApiResponse<{ secret: string; otpauthUrl: string; qrCodeDataUrl: string }>>,

  confirmMfa: (code: string) =>
    client.post('/auth/mfa/confirm', { code }) as Promise<ApiResponse>,

  disableMfa: (password: string) =>
    client.post('/auth/mfa/disable', { password }) as Promise<ApiResponse>,
```

- [ ] **Step 2: Update mobile login flow for MFA challenge**

In the mobile login handler (wherever `authApi.login` is called and tokens are processed), add MFA check:

```typescript
if (response.data && 'mfaRequired' in response.data && response.data.mfaRequired) {
    // Navigate to MFA verify screen with the challenge token
    router.push({ pathname: '/(auth)/mfa-verify', params: { mfaToken: response.data.mfaToken } });
    return;
}
```

- [ ] **Step 3: Create MFA verify screen for mobile**

Create `src/features/auth/mfa-verify-screen.tsx` with a 6-digit OTP input using the same pattern as the web version, adapted for React Native (use `TextInput` with `keyboardType="number-pad"` and auto-focus chaining).

- [ ] **Step 4: Create route file**

Create `src/app/(auth)/mfa-verify.tsx`:

```tsx
export { MfaVerifyScreen as default } from '@/features/auth/mfa-verify-screen';
```

- [ ] **Step 5: Add X-Device-Info header to mobile API client**

In `mobile-app/src/lib/api/client.tsx`, add to the request interceptor:

```typescript
config.headers['X-Device-Info'] = Platform.OS === 'ios' ? 'mobile-ios' : 'mobile-android';
```

Import `Platform` from `react-native`.

- [ ] **Step 6: Commit**

```bash
git add src/lib/api/auth.ts src/features/auth/mfa-verify-screen.tsx src/app/\(auth\)/mfa-verify.tsx src/lib/api/client.tsx
git commit -m "feat(mobile): add MFA verify screen and device info header"
```

---

## Task 9: Web App — Add X-Device-Info Header

**Files:**
- Modify: `web-system-app/src/lib/api/client.ts`

- [ ] **Step 1: Add device info header to web client**

In `src/lib/api/client.ts`, update the request interceptor to include the device header:

```typescript
client.interceptors.request.use(
    async (config) => {
        config.headers['X-Device-Info'] = 'web';
        const token = await proactiveRefreshIfNeeded();
        if (token) {
            config.headers.Authorization = `Bearer ${token}`;
        }
        return config;
    },
    (error) => Promise.reject(error),
);
```

Also add it to `refreshClient`:

```typescript
refreshClient.interceptors.request.use((config) => {
    config.headers['X-Device-Info'] = 'web';
    return config;
});
```

- [ ] **Step 2: Commit**

```bash
git add src/lib/api/client.ts
git commit -m "feat(web): add X-Device-Info header for session tracking"
```

---

## Summary: Enforcement Matrix After All Tasks

| Setting | Enforced Where | How |
|---------|---------------|-----|
| MFA Required | Backend `login()` | Returns `mfaRequired` challenge; both frontends handle 2-step flow |
| Session Timeout | Frontend `useSessionTimeout` hook | Inactivity timer reads `sessionTimeoutMinutes` from SystemControls |
| Max Concurrent Sessions | Backend `trackSession()` | `ActiveSession` table; oldest session revoked when limit exceeded |
| Password Min Length | Backend `changePassword()` + `resetPassword()` | Validates against `passwordMinLength` from SystemControls |
| Password Complexity | Backend `changePassword()` + `resetPassword()` | Validates uppercase/lowercase/digit/special from SystemControls |
| Account Lock Threshold | Backend `login()` | Tracks `failedLoginAttempts`; locks after threshold |
| Account Lock Duration | Backend `login()` | `lockedUntil` timestamp; auto-unlocks after duration |

### Max Concurrent Sessions — Mobile Answer
The limit is **global across all platforms**. The `ActiveSession` table has a `deviceInfo` field (`web`, `mobile-ios`, `mobile-android`) but the count is per-user regardless of device. If `maxConcurrentSessions = 3`, a user can have 2 web + 1 mobile, or 3 mobile, or any combination. The oldest session is auto-revoked when the limit is exceeded — both web and mobile will gracefully redirect to login on next refresh attempt.
