# Module CRUD & Support Ticket System — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Enable Company Admins to manage modules on their locations (billing-gated), raise support tickets for one-time billing tenants, and give Super Admins a support dashboard with module approval workflow.

**Architecture:** Three-layer build: (1) Prisma schema + backend support module + module CRUD endpoints, (2) Web frontend — module management UI, help & support screen, super-admin support dashboard, (3) Mobile frontend — same screens mirrored. Backend follows existing Express + Prisma + Zod patterns. Frontend uses React Query hooks with cache invalidation.

**Tech Stack:** Express, Prisma, Zod, Bull queue (backend); React, React Query, Tailwind, Lucide (web); React Native, Expo Router, NativeWind, Zustand (mobile)

**Spec:** `docs/superpowers/specs/2026-03-27-module-crud-support-system-design.md`

---

## Phase 1: Database & Backend

### Task 1: Prisma Schema — Support Ticket Models

**Files:**
- Modify: `avy-erp-backend/prisma/schema.prisma`

- [ ] **Step 1: Add enums and models to schema.prisma**

Add after existing enums (around line 2868):

```prisma
// ── Support Ticket System ──

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
  id               String         @id @default(cuid())
  tenantId         String
  companyId        String
  companyName      String
  createdByUserId  String
  createdByName    String
  subject          String
  category         TicketCategory @default(GENERAL)
  priority         TicketPriority @default(NORMAL)
  status           TicketStatus   @default(OPEN)
  assignedToUserId String?
  metadata         Json?
  resolvedAt       DateTime?
  closedAt         DateTime?
  createdAt        DateTime       @default(now())
  updatedAt        DateTime       @updatedAt

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
  senderUserId    String?
  senderName      String
  senderRole      SenderRole @default(COMPANY_ADMIN)
  body            String
  isSystemMessage Boolean    @default(false)
  createdAt       DateTime   @default(now())

  ticket SupportTicket @relation(fields: [ticketId], references: [id], onDelete: Cascade)

  @@index([ticketId])
  @@map("support_messages")
}
```

- [ ] **Step 2: Add back-relation to Company model**

Find the Company model's relations block and add:

```prisma
  supportTickets SupportTicket[]
```

Add after the existing `notificationRules NotificationRule[]` line.

- [ ] **Step 3: Generate Prisma client and create migration**

Run:
```bash
cd avy-erp-backend
npx prisma generate
npx prisma migrate dev --name add-support-ticket-system
```

Expected: Migration created successfully, Prisma client regenerated.

- [ ] **Step 4: Commit**

```bash
git add prisma/
git commit -m "feat(schema): add SupportTicket and SupportMessage models with enums"
```

---

### Task 2: Backend — Support Module (Validators + Service)

**Files:**
- Create: `avy-erp-backend/src/core/support/support.validators.ts`
- Create: `avy-erp-backend/src/core/support/support.service.ts`

- [ ] **Step 1: Create support validators**

Create `avy-erp-backend/src/core/support/support.validators.ts`:

```typescript
import { z } from 'zod';

export const moduleChangeMetadataSchema = z.object({
    type: z.enum(['add', 'remove']),
    locationId: z.string().min(1),
    locationName: z.string().min(1),
    moduleId: z.string().min(1),
    moduleName: z.string().min(1),
});

export const createTicketSchema = z
    .object({
        subject: z.string().min(3).max(200),
        category: z.enum(['MODULE_CHANGE', 'BILLING', 'TECHNICAL', 'GENERAL']).default('GENERAL'),
        priority: z.enum(['LOW', 'NORMAL', 'HIGH', 'URGENT']).optional(),
        message: z.string().min(1).max(5000),
        metadata: z.record(z.unknown()).optional(),
    })
    .refine(
        (data) => {
            if (data.category === 'MODULE_CHANGE') {
                return moduleChangeMetadataSchema.safeParse(data.metadata).success;
            }
            return true;
        },
        {
            message:
                'MODULE_CHANGE tickets require valid metadata (type, locationId, locationName, moduleId, moduleName)',
        },
    );

export const sendMessageSchema = z.object({
    body: z.string().min(1).max(5000),
});

export const updateStatusSchema = z.object({
    status: z.enum(['OPEN', 'IN_PROGRESS', 'WAITING_ON_CUSTOMER', 'RESOLVED', 'CLOSED']),
});

export const rejectModuleSchema = z.object({
    reason: z.string().min(1).max(1000),
});

export type CreateTicketInput = z.infer<typeof createTicketSchema>;
export type SendMessageInput = z.infer<typeof sendMessageSchema>;
export type UpdateStatusInput = z.infer<typeof updateStatusSchema>;
export type RejectModuleInput = z.infer<typeof rejectModuleSchema>;
```

- [ ] **Step 2: Create support service**

Create `avy-erp-backend/src/core/support/support.service.ts`:

```typescript
import { PrismaClient, TicketStatus, SenderRole } from '@prisma/client';
import { ApiError } from '../../shared/errors/api-error';

const prisma = new PrismaClient();

// Status transition rules
const ALLOWED_TRANSITIONS: Record<string, string[]> = {
    OPEN: ['IN_PROGRESS', 'WAITING_ON_CUSTOMER', 'RESOLVED', 'CLOSED'],
    IN_PROGRESS: ['WAITING_ON_CUSTOMER', 'RESOLVED', 'CLOSED'],
    WAITING_ON_CUSTOMER: ['OPEN', 'IN_PROGRESS', 'RESOLVED', 'CLOSED'],
    RESOLVED: ['CLOSED'],
    CLOSED: [],
};

export const supportService = {
    async createTicket(params: {
        tenantId: string;
        companyId: string;
        companyName: string;
        userId: string;
        userName: string;
        data: {
            subject: string;
            category?: string;
            priority?: string;
            message: string;
            metadata?: Record<string, unknown>;
        };
    }) {
        const { tenantId, companyId, companyName, userId, userName, data } = params;

        // Duplicate check for MODULE_CHANGE
        if (data.category === 'MODULE_CHANGE' && data.metadata) {
            const meta = data.metadata as { locationId: string; moduleId: string; type: string };
            const existing = await prisma.supportTicket.findFirst({
                where: {
                    companyId,
                    category: 'MODULE_CHANGE',
                    status: { notIn: ['RESOLVED', 'CLOSED'] },
                },
            });
            if (existing) {
                // Check metadata match
                const existingMeta = existing.metadata as any;
                if (
                    existingMeta?.locationId === meta.locationId &&
                    existingMeta?.moduleId === meta.moduleId &&
                    existingMeta?.type === meta.type
                ) {
                    throw ApiError.conflict(
                        `A ${meta.type} request for this module at this location is already open (ticket #${existing.id})`,
                    );
                }
            }
        }

        return prisma.$transaction(async (tx) => {
            const ticket = await tx.supportTicket.create({
                data: {
                    tenantId,
                    companyId,
                    companyName,
                    createdByUserId: userId,
                    createdByName: userName,
                    subject: data.subject,
                    category: (data.category as any) ?? 'GENERAL',
                    priority: (data.priority as any) ?? 'NORMAL',
                    metadata: data.metadata ?? undefined,
                },
            });

            // User's initial message
            await tx.supportMessage.create({
                data: {
                    ticketId: ticket.id,
                    senderUserId: userId,
                    senderName: userName,
                    senderRole: 'COMPANY_ADMIN',
                    body: data.message,
                },
            });

            // System message for MODULE_CHANGE
            if (data.category === 'MODULE_CHANGE' && data.metadata) {
                const meta = data.metadata as { type: string; moduleName: string; locationName: string };
                await tx.supportMessage.create({
                    data: {
                        ticketId: ticket.id,
                        senderName: 'System',
                        senderRole: 'SYSTEM',
                        body: `Module change requested: ${meta.type === 'add' ? 'Add' : 'Remove'} "${meta.moduleName}" ${meta.type === 'add' ? 'to' : 'from'} ${meta.locationName}`,
                        isSystemMessage: true,
                    },
                });
            }

            return tx.supportTicket.findUnique({
                where: { id: ticket.id },
                include: { messages: { orderBy: { createdAt: 'asc' } } },
            });
        });
    },

    async listTickets(filters: {
        companyId?: string;
        tenantId?: string;
        status?: string;
        category?: string;
        search?: string;
        page?: number;
        limit?: number;
    }) {
        const { companyId, tenantId, status, category, search, page = 1, limit = 20 } = filters;
        const where: any = {};
        if (companyId) where.companyId = companyId;
        if (tenantId) where.tenantId = tenantId;
        if (status) where.status = status;
        if (category) where.category = category;
        if (search) {
            where.OR = [
                { subject: { contains: search, mode: 'insensitive' } },
                { companyName: { contains: search, mode: 'insensitive' } },
            ];
        }

        const [tickets, total] = await Promise.all([
            prisma.supportTicket.findMany({
                where,
                include: {
                    messages: { orderBy: { createdAt: 'desc' }, take: 1 },
                },
                orderBy: { updatedAt: 'desc' },
                skip: (page - 1) * limit,
                take: limit,
            }),
            prisma.supportTicket.count({ where }),
        ]);

        return { tickets, total, page, limit, totalPages: Math.ceil(total / limit) };
    },

    async getTicket(ticketId: string, companyId?: string) {
        const where: any = { id: ticketId };
        if (companyId) where.companyId = companyId;

        const ticket = await prisma.supportTicket.findFirst({
            where,
            include: {
                messages: { orderBy: { createdAt: 'asc' } },
                company: {
                    select: {
                        id: true,
                        name: true,
                        displayName: true,
                        billingType: true,
                        userTier: true,
                        locationConfig: true,
                        wizardStatus: true,
                    },
                },
            },
        });

        if (!ticket) throw ApiError.notFound('Ticket not found');
        return ticket;
    },

    async sendMessage(params: {
        ticketId: string;
        companyId?: string;
        userId: string;
        userName: string;
        role: SenderRole;
        body: string;
    }) {
        const { ticketId, companyId, userId, userName, role, body } = params;

        const ticket = await this.getTicket(ticketId, companyId);
        if (ticket.status === 'CLOSED') {
            throw ApiError.badRequest('Cannot send messages to a closed ticket');
        }

        const message = await prisma.supportMessage.create({
            data: {
                ticketId,
                senderUserId: userId,
                senderName: userName,
                senderRole: role,
                body,
            },
        });

        await prisma.supportTicket.update({
            where: { id: ticketId },
            data: { updatedAt: new Date() },
        });

        return message;
    },

    async updateStatus(ticketId: string, newStatus: string) {
        const ticket = await prisma.supportTicket.findUnique({ where: { id: ticketId } });
        if (!ticket) throw ApiError.notFound('Ticket not found');

        const allowed = ALLOWED_TRANSITIONS[ticket.status] ?? [];
        if (!allowed.includes(newStatus)) {
            throw ApiError.badRequest(
                `Cannot transition from ${ticket.status} to ${newStatus}. Allowed: ${allowed.join(', ') || 'none'}`,
            );
        }

        const updateData: any = { status: newStatus };
        if (newStatus === 'RESOLVED') updateData.resolvedAt = new Date();
        if (newStatus === 'CLOSED') updateData.closedAt = new Date();

        return prisma.supportTicket.update({
            where: { id: ticketId },
            data: updateData,
        });
    },

    async approveModuleChange(ticketId: string, approverUserId: string, approverName: string) {
        const ticket = await prisma.supportTicket.findUnique({ where: { id: ticketId } });
        if (!ticket) throw ApiError.notFound('Ticket not found');
        if (ticket.category !== 'MODULE_CHANGE') {
            throw ApiError.badRequest('This ticket is not a module change request');
        }
        if (['RESOLVED', 'CLOSED'].includes(ticket.status)) {
            throw ApiError.conflict('This ticket has already been resolved');
        }

        const meta = ticket.metadata as any;
        if (!meta?.locationId || !meta?.moduleId) {
            throw ApiError.badRequest('Invalid ticket metadata');
        }

        return prisma.$transaction(async (tx) => {
            const location = await tx.location.findFirst({
                where: { id: meta.locationId, companyId: ticket.companyId },
            });
            if (!location) throw ApiError.notFound('Location not found');

            const currentModules = (location.moduleIds as string[] | null) ?? [];

            if (meta.type === 'add') {
                // Add module + resolve deps (simplified — full dep resolution uses MODULE_CATALOGUE)
                const newModules = Array.from(new Set([...currentModules, meta.moduleId]));
                await tx.location.update({
                    where: { id: meta.locationId },
                    data: { moduleIds: newModules },
                });
            } else if (meta.type === 'remove') {
                const newModules = currentModules.filter((m: string) => m !== meta.moduleId);
                await tx.location.update({
                    where: { id: meta.locationId },
                    data: { moduleIds: newModules },
                });
            }

            // Re-aggregate company selectedModuleIds
            const allLocations = await tx.location.findMany({
                where: { companyId: ticket.companyId },
                select: { moduleIds: true },
            });
            const aggregated = Array.from(
                new Set(allLocations.flatMap((l) => (l.moduleIds as string[] | null) ?? [])),
            );
            await tx.company.update({
                where: { id: ticket.companyId },
                data: { selectedModuleIds: aggregated },
            });

            // System message
            await tx.supportMessage.create({
                data: {
                    ticketId,
                    senderName: 'System',
                    senderRole: 'SYSTEM',
                    body: `✅ Module change approved by ${approverName}: ${meta.type === 'add' ? 'Added' : 'Removed'} "${meta.moduleName}" ${meta.type === 'add' ? 'to' : 'from'} ${meta.locationName}`,
                    isSystemMessage: true,
                },
            });

            // Resolve ticket
            return tx.supportTicket.update({
                where: { id: ticketId },
                data: { status: 'RESOLVED', resolvedAt: new Date() },
                include: { messages: { orderBy: { createdAt: 'asc' } } },
            });
        });
    },

    async rejectModuleChange(ticketId: string, approverName: string, reason: string) {
        const ticket = await prisma.supportTicket.findUnique({ where: { id: ticketId } });
        if (!ticket) throw ApiError.notFound('Ticket not found');
        if (ticket.category !== 'MODULE_CHANGE') {
            throw ApiError.badRequest('This ticket is not a module change request');
        }
        if (['RESOLVED', 'CLOSED'].includes(ticket.status)) {
            throw ApiError.conflict('This ticket has already been resolved');
        }

        return prisma.$transaction(async (tx) => {
            await tx.supportMessage.create({
                data: {
                    ticketId,
                    senderName: 'System',
                    senderRole: 'SYSTEM',
                    body: `❌ Module change rejected by ${approverName}: ${reason}`,
                    isSystemMessage: true,
                },
            });

            return tx.supportTicket.update({
                where: { id: ticketId },
                data: { status: 'RESOLVED', resolvedAt: new Date() },
                include: { messages: { orderBy: { createdAt: 'asc' } } },
            });
        });
    },

    async getStats() {
        const [open, inProgress, waiting, resolvedToday] = await Promise.all([
            prisma.supportTicket.count({ where: { status: 'OPEN' } }),
            prisma.supportTicket.count({ where: { status: 'IN_PROGRESS' } }),
            prisma.supportTicket.count({ where: { status: 'WAITING_ON_CUSTOMER' } }),
            prisma.supportTicket.count({
                where: {
                    status: 'RESOLVED',
                    resolvedAt: { gte: new Date(new Date().setHours(0, 0, 0, 0)) },
                },
            }),
        ]);
        return { open, inProgress, waiting, resolvedToday };
    },
};
```

- [ ] **Step 3: Commit**

```bash
git add src/core/support/
git commit -m "feat(support): add validators and service for support ticket system"
```

---

### Task 3: Backend — Support Controller + Routes

**Files:**
- Create: `avy-erp-backend/src/core/support/support.controller.ts`
- Create: `avy-erp-backend/src/core/support/support.routes.ts`
- Modify: `avy-erp-backend/src/app/routes.ts`

- [ ] **Step 1: Create support controller**

Create `avy-erp-backend/src/core/support/support.controller.ts`:

```typescript
import { Request, Response } from 'express';
import { supportService } from './support.service';
import {
    createTicketSchema,
    sendMessageSchema,
    updateStatusSchema,
    rejectModuleSchema,
} from './support.validators';
import { ApiError } from '../../shared/errors/api-error';
import { createSuccessResponse, createPaginatedResponse } from '../../shared/utils';
import { asyncHandler } from '../../middleware/error.middleware';

// ── Company Admin Handlers ──

export const createTicket = asyncHandler(async (req: Request, res: Response) => {
    const user = req.user as any;
    if (!user?.companyId) throw ApiError.badRequest('Company ID required');

    const parsed = createTicketSchema.safeParse(req.body);
    if (!parsed.success) {
        throw ApiError.badRequest(parsed.error.errors.map((e) => e.message).join(', '));
    }

    const company = await (req as any).prisma?.company?.findUnique?.({ where: { id: user.companyId } });
    const companyName = company?.displayName || company?.name || 'Unknown';

    const ticket = await supportService.createTicket({
        tenantId: user.tenantId || '',
        companyId: user.companyId,
        companyName,
        userId: user.id,
        userName: `${user.firstName} ${user.lastName}`,
        data: parsed.data,
    });

    res.status(201).json(createSuccessResponse(ticket, 'Ticket created'));
});

export const listMyTickets = asyncHandler(async (req: Request, res: Response) => {
    const user = req.user as any;
    if (!user?.companyId) throw ApiError.badRequest('Company ID required');

    const { status, category, search, page, limit } = req.query;
    const result = await supportService.listTickets({
        companyId: user.companyId,
        status: status as string,
        category: category as string,
        search: search as string,
        page: page ? parseInt(page as string) : undefined,
        limit: limit ? parseInt(limit as string) : undefined,
    });

    res.json(
        createPaginatedResponse(result.tickets, result.page, result.limit, result.total, 'Tickets retrieved'),
    );
});

export const getMyTicket = asyncHandler(async (req: Request, res: Response) => {
    const user = req.user as any;
    if (!user?.companyId) throw ApiError.badRequest('Company ID required');

    const ticket = await supportService.getTicket(req.params.id, user.companyId);
    res.json(createSuccessResponse(ticket));
});

export const sendMyMessage = asyncHandler(async (req: Request, res: Response) => {
    const user = req.user as any;
    if (!user?.companyId) throw ApiError.badRequest('Company ID required');

    const parsed = sendMessageSchema.safeParse(req.body);
    if (!parsed.success) {
        throw ApiError.badRequest(parsed.error.errors.map((e) => e.message).join(', '));
    }

    const message = await supportService.sendMessage({
        ticketId: req.params.id,
        companyId: user.companyId,
        userId: user.id,
        userName: `${user.firstName} ${user.lastName}`,
        role: 'COMPANY_ADMIN',
        body: parsed.data.body,
    });

    res.status(201).json(createSuccessResponse(message, 'Message sent'));
});

export const closeMyTicket = asyncHandler(async (req: Request, res: Response) => {
    const user = req.user as any;
    if (!user?.companyId) throw ApiError.badRequest('Company ID required');

    // Verify ticket belongs to this company
    await supportService.getTicket(req.params.id, user.companyId);
    const ticket = await supportService.updateStatus(req.params.id, 'CLOSED');
    res.json(createSuccessResponse(ticket, 'Ticket closed'));
});

// ── Super Admin Handlers ──

export const listAllTickets = asyncHandler(async (req: Request, res: Response) => {
    const { status, category, search, page, limit } = req.query;
    const result = await supportService.listTickets({
        status: status as string,
        category: category as string,
        search: search as string,
        page: page ? parseInt(page as string) : undefined,
        limit: limit ? parseInt(limit as string) : undefined,
    });

    res.json(
        createPaginatedResponse(result.tickets, result.page, result.limit, result.total, 'Tickets retrieved'),
    );
});

export const getTicketAdmin = asyncHandler(async (req: Request, res: Response) => {
    const ticket = await supportService.getTicket(req.params.id);
    res.json(createSuccessResponse(ticket));
});

export const replyToTicket = asyncHandler(async (req: Request, res: Response) => {
    const user = req.user as any;
    const parsed = sendMessageSchema.safeParse(req.body);
    if (!parsed.success) {
        throw ApiError.badRequest(parsed.error.errors.map((e) => e.message).join(', '));
    }

    const message = await supportService.sendMessage({
        ticketId: req.params.id,
        userId: user.id,
        userName: `${user.firstName} ${user.lastName}`,
        role: 'SUPER_ADMIN',
        body: parsed.data.body,
    });

    res.status(201).json(createSuccessResponse(message, 'Reply sent'));
});

export const updateTicketStatus = asyncHandler(async (req: Request, res: Response) => {
    const parsed = updateStatusSchema.safeParse(req.body);
    if (!parsed.success) {
        throw ApiError.badRequest(parsed.error.errors.map((e) => e.message).join(', '));
    }

    const ticket = await supportService.updateStatus(req.params.id, parsed.data.status);
    res.json(createSuccessResponse(ticket, 'Status updated'));
});

export const approveModuleChange = asyncHandler(async (req: Request, res: Response) => {
    const user = req.user as any;
    const ticket = await supportService.approveModuleChange(
        req.params.id,
        user.id,
        `${user.firstName} ${user.lastName}`,
    );
    res.json(createSuccessResponse(ticket, 'Module change approved'));
});

export const rejectModuleChange = asyncHandler(async (req: Request, res: Response) => {
    const user = req.user as any;
    const parsed = rejectModuleSchema.safeParse(req.body);
    if (!parsed.success) {
        throw ApiError.badRequest(parsed.error.errors.map((e) => e.message).join(', '));
    }

    const ticket = await supportService.rejectModuleChange(
        req.params.id,
        `${user.firstName} ${user.lastName}`,
        parsed.data.reason,
    );
    res.json(createSuccessResponse(ticket, 'Module change rejected'));
});

export const getTicketStats = asyncHandler(async (_req: Request, res: Response) => {
    const stats = await supportService.getStats();
    res.json(createSuccessResponse(stats));
});
```

- [ ] **Step 2: Create support routes**

Create `avy-erp-backend/src/core/support/support.routes.ts`:

```typescript
import { Router } from 'express';
import * as ctrl from './support.controller';

// Company-admin routes (mounted at /company/support)
export const supportCompanyRoutes = Router();
supportCompanyRoutes.post('/tickets', ctrl.createTicket);
supportCompanyRoutes.get('/tickets', ctrl.listMyTickets);
supportCompanyRoutes.get('/tickets/:id', ctrl.getMyTicket);
supportCompanyRoutes.post('/tickets/:id/messages', ctrl.sendMyMessage);
supportCompanyRoutes.patch('/tickets/:id/close', ctrl.closeMyTicket);

// Super-admin routes (mounted at /platform/support)
export const supportPlatformRoutes = Router();
supportPlatformRoutes.get('/tickets', ctrl.listAllTickets);
supportPlatformRoutes.get('/tickets/:id', ctrl.getTicketAdmin);
supportPlatformRoutes.post('/tickets/:id/messages', ctrl.replyToTicket);
supportPlatformRoutes.patch('/tickets/:id/status', ctrl.updateTicketStatus);
supportPlatformRoutes.post('/tickets/:id/approve-module', ctrl.approveModuleChange);
supportPlatformRoutes.post('/tickets/:id/reject-module', ctrl.rejectModuleChange);
supportPlatformRoutes.get('/stats', ctrl.getTicketStats);
```

- [ ] **Step 3: Mount routes in main router**

Modify `avy-erp-backend/src/app/routes.ts`. Add import at top:

```typescript
import { supportCompanyRoutes, supportPlatformRoutes } from '../core/support/support.routes';
```

Mount company support routes after existing `/company` routes:

```typescript
router.use('/company/support', supportCompanyRoutes);
```

Mount platform support routes after existing `/platform` routes:

```typescript
router.use('/platform/support', supportPlatformRoutes);
```

- [ ] **Step 4: Verify backend compiles**

Run:
```bash
cd avy-erp-backend && npx tsc --noEmit
```

Expected: No errors.

- [ ] **Step 5: Commit**

```bash
git add src/core/support/ src/app/routes.ts
git commit -m "feat(support): add controller and routes for support ticket system"
```

---

### Task 4: Backend — Module CRUD Endpoints

**Files:**
- Modify: `avy-erp-backend/src/core/company-admin/company-admin.validators.ts`
- Modify: `avy-erp-backend/src/core/company-admin/company-admin.service.ts`
- Modify: `avy-erp-backend/src/core/company-admin/company-admin.controller.ts`
- Modify: `avy-erp-backend/src/core/company-admin/company-admin.routes.ts`

- [ ] **Step 1: Add module CRUD validator**

Append to `company-admin.validators.ts`:

```typescript
export const addModulesSchema = z.object({
    moduleIds: z.array(z.string().min(1)).min(1).max(10),
});
```

- [ ] **Step 2: Add module CRUD service methods**

Append to `company-admin.service.ts`. These require the MODULE_CATALOGUE dependency map. Add at top of file:

```typescript
const MODULE_DEPS: Record<string, string[]> = {
    masters: [],
    security: ['masters'],
    hr: ['security'],
    production: ['machine-maintenance', 'masters'],
    'machine-maintenance': ['masters'],
    inventory: ['masters'],
    vendor: ['inventory', 'masters'],
    sales: ['finance', 'masters'],
    finance: ['masters'],
    visitor: ['security'],
};

const MODULE_NAMES: Record<string, string> = {
    masters: 'Masters', security: 'Security', hr: 'HR Management',
    production: 'Production', 'machine-maintenance': 'Machine Maintenance',
    inventory: 'Inventory', vendor: 'Vendor Management',
    sales: 'Sales & Invoicing', finance: 'Finance', visitor: 'Visitor Management',
};

const MODULE_PRICES: Record<string, number> = {
    masters: 0, security: 1499, hr: 2999, production: 2499,
    'machine-maintenance': 1999, inventory: 1999, vendor: 1499,
    sales: 1999, finance: 2499, visitor: 999,
};

function resolveDeps(moduleIds: string[]): string[] {
    const resolved = new Set(moduleIds);
    const queue = [...moduleIds];
    while (queue.length) {
        const id = queue.shift()!;
        for (const dep of MODULE_DEPS[id] ?? []) {
            if (!resolved.has(dep)) {
                resolved.add(dep);
                queue.push(dep);
            }
        }
    }
    return Array.from(resolved);
}

function getDependents(moduleId: string): string[] {
    return Object.entries(MODULE_DEPS)
        .filter(([, deps]) => deps.includes(moduleId))
        .map(([id]) => id);
}
```

Add service methods (append to the existing service object / export):

```typescript
async addModulesToLocation(companyId: string, locationId: string, moduleIds: string[]) {
    // Validate location ownership
    const location = await prisma.location.findFirst({
        where: { id: locationId, companyId },
    });
    if (!location) throw ApiError.notFound('Location not found');

    // Check billing type
    const company = await prisma.company.findUnique({ where: { id: companyId } });
    const billingType = (company?.locationConfig === 'common'
        ? company?.billingType
        : location.billingType) ?? 'monthly';

    if (billingType !== 'monthly' && billingType !== 'annual') {
        if ((location as any).oneTimeLicenseFee > 0 || billingType === 'one_time') {
            throw ApiError.forbidden(
                'One-time billing tenants must request module changes via support tickets',
            );
        }
    }

    // Validate module IDs
    for (const id of moduleIds) {
        if (!MODULE_DEPS[id] && MODULE_DEPS[id] === undefined) {
            throw ApiError.badRequest(`Unknown module: ${id}`);
        }
    }

    // Resolve deps
    const currentModules = (location.moduleIds as string[] | null) ?? [];
    const allToAdd = resolveDeps(moduleIds);
    const newModules = Array.from(new Set([...currentModules, ...allToAdd]));
    const autoAdded = allToAdd.filter((m) => !moduleIds.includes(m) && !currentModules.includes(m));

    return prisma.$transaction(async (tx) => {
        if (company?.locationConfig === 'common') {
            // Update ALL locations
            await tx.location.updateMany({
                where: { companyId },
                data: { moduleIds: newModules },
            });
            await tx.company.update({
                where: { id: companyId },
                data: { selectedModuleIds: newModules },
            });
        } else {
            await tx.location.update({
                where: { id: locationId },
                data: { moduleIds: newModules },
            });
            // Re-aggregate company
            const allLocs = await tx.location.findMany({
                where: { companyId },
                select: { moduleIds: true },
            });
            const aggregated = Array.from(
                new Set(allLocs.flatMap((l) => (l.moduleIds as string[] | null) ?? [])),
            );
            await tx.company.update({
                where: { id: companyId },
                data: { selectedModuleIds: aggregated },
            });
        }

        const updated = await tx.location.findUnique({ where: { id: locationId } });

        return {
            location: updated,
            autoAddedDeps: autoAdded,
            billingImpact: {
                addedModules: allToAdd
                    .filter((m) => !currentModules.includes(m))
                    .map((m) => ({ id: m, name: MODULE_NAMES[m] ?? m, price: MODULE_PRICES[m] ?? 0 })),
                monthlyDelta: allToAdd
                    .filter((m) => !currentModules.includes(m))
                    .reduce((sum, m) => sum + (MODULE_PRICES[m] ?? 0), 0),
            },
        };
    });
},

async removeModuleFromLocation(companyId: string, locationId: string, moduleId: string) {
    if (moduleId === 'masters') {
        throw ApiError.badRequest('Cannot remove the Masters module');
    }

    const location = await prisma.location.findFirst({
        where: { id: locationId, companyId },
    });
    if (!location) throw ApiError.notFound('Location not found');

    const currentModules = (location.moduleIds as string[] | null) ?? [];
    if (!currentModules.includes(moduleId)) {
        throw ApiError.notFound(`Module "${moduleId}" is not active on this location`);
    }

    // Check billing type
    const company = await prisma.company.findUnique({ where: { id: companyId } });
    const billingType = (company?.locationConfig === 'common'
        ? company?.billingType
        : location.billingType) ?? 'monthly';

    if (billingType !== 'monthly' && billingType !== 'annual') {
        if ((location as any).oneTimeLicenseFee > 0 || billingType === 'one_time') {
            throw ApiError.forbidden(
                'One-time billing tenants must request module changes via support tickets',
            );
        }
    }

    // Check dependents
    const dependents = getDependents(moduleId).filter((d) => currentModules.includes(d));
    if (dependents.length > 0) {
        throw ApiError.conflict(
            `Cannot remove "${MODULE_NAMES[moduleId]}": required by ${dependents.map((d) => MODULE_NAMES[d]).join(', ')}`,
        );
    }

    const newModules = currentModules.filter((m) => m !== moduleId);

    return prisma.$transaction(async (tx) => {
        if (company?.locationConfig === 'common') {
            await tx.location.updateMany({
                where: { companyId },
                data: { moduleIds: newModules },
            });
            await tx.company.update({
                where: { id: companyId },
                data: { selectedModuleIds: newModules },
            });
        } else {
            await tx.location.update({
                where: { id: locationId },
                data: { moduleIds: newModules },
            });
            const allLocs = await tx.location.findMany({
                where: { companyId },
                select: { moduleIds: true },
            });
            const aggregated = Array.from(
                new Set(allLocs.flatMap((l) => (l.moduleIds as string[] | null) ?? [])),
            );
            await tx.company.update({
                where: { id: companyId },
                data: { selectedModuleIds: aggregated },
            });
        }

        return tx.location.findUnique({ where: { id: locationId } });
    });
},
```

- [ ] **Step 3: Add controller handlers for module CRUD**

Append to `company-admin.controller.ts`:

```typescript
export const addModulesToLocation = asyncHandler(async (req: Request, res: Response) => {
    const companyId = (req.user as any)?.companyId;
    if (!companyId) throw ApiError.badRequest('Company ID required');

    const parsed = addModulesSchema.safeParse(req.body);
    if (!parsed.success) {
        throw ApiError.badRequest(parsed.error.errors.map((e) => e.message).join(', '));
    }

    const result = await companyAdminService.addModulesToLocation(
        companyId,
        req.params.locationId,
        parsed.data.moduleIds,
    );

    res.json(createSuccessResponse(result, 'Modules added successfully'));
});

export const removeModuleFromLocation = asyncHandler(async (req: Request, res: Response) => {
    const companyId = (req.user as any)?.companyId;
    if (!companyId) throw ApiError.badRequest('Company ID required');

    const location = await companyAdminService.removeModuleFromLocation(
        companyId,
        req.params.locationId,
        req.params.moduleId,
    );

    res.json(createSuccessResponse(location, 'Module removed successfully'));
});
```

- [ ] **Step 4: Add routes for module CRUD**

Append to `company-admin.routes.ts`:

```typescript
// Module CRUD (location-based)
router.post('/locations/:locationId/modules', ctrl.addModulesToLocation);
router.delete('/locations/:locationId/modules/:moduleId', ctrl.removeModuleFromLocation);
```

- [ ] **Step 5: Verify backend compiles**

Run:
```bash
cd avy-erp-backend && npx tsc --noEmit
```

Expected: No errors.

- [ ] **Step 6: Commit**

```bash
git add src/core/company-admin/
git commit -m "feat(modules): add module CRUD endpoints with billing gate and dependency resolution"
```

---

## Phase 2: Web Frontend

### Task 5: Web — API Layer (Support + Module CRUD)

**Files:**
- Modify: `web-system-app/src/lib/api/company-admin.ts`
- Create: `web-system-app/src/lib/api/support.ts`
- Modify: `web-system-app/src/features/company-admin/api/use-company-admin-queries.ts`
- Modify: `web-system-app/src/features/company-admin/api/use-company-admin-mutations.ts`
- Create: `web-system-app/src/features/support/api/use-support-queries.ts`
- Create: `web-system-app/src/features/support/api/use-support-mutations.ts`
- Create: `web-system-app/src/features/super-admin/api/use-support-queries.ts`
- Create: `web-system-app/src/features/super-admin/api/use-support-mutations.ts`
- Modify: `web-system-app/src/features/company-admin/api/index.ts`

- [ ] **Step 1: Add support API functions to company-admin.ts**

Append to `web-system-app/src/lib/api/company-admin.ts`:

```typescript
// ── Support Tickets ──
createSupportTicket: (data: { subject: string; category?: string; priority?: string; message: string; metadata?: Record<string, unknown> }) =>
    client.post('/company/support/tickets', data),
listSupportTickets: (params?: { status?: string; category?: string; search?: string; page?: number; limit?: number }) =>
    client.get('/company/support/tickets', { params }),
getSupportTicket: (id: string) =>
    client.get(`/company/support/tickets/${id}`),
sendSupportMessage: (id: string, data: { body: string }) =>
    client.post(`/company/support/tickets/${id}/messages`, data),
closeSupportTicket: (id: string) =>
    client.patch(`/company/support/tickets/${id}/close`),

// ── Module CRUD ──
addLocationModules: (locationId: string, data: { moduleIds: string[] }) =>
    client.post(`/company/locations/${locationId}/modules`, data),
removeLocationModule: (locationId: string, moduleId: string) =>
    client.delete(`/company/locations/${locationId}/modules/${moduleId}`),
```

- [ ] **Step 2: Create platform support API file**

Create `web-system-app/src/lib/api/support.ts`:

```typescript
import { client } from './client';

export const supportApi = {
    listTickets: (params?: { status?: string; category?: string; search?: string; page?: number; limit?: number }) =>
        client.get('/platform/support/tickets', { params }),
    getTicket: (id: string) =>
        client.get(`/platform/support/tickets/${id}`),
    replyToTicket: (id: string, data: { body: string }) =>
        client.post(`/platform/support/tickets/${id}/messages`, data),
    updateTicketStatus: (id: string, data: { status: string }) =>
        client.patch(`/platform/support/tickets/${id}/status`, data),
    approveModuleChange: (id: string) =>
        client.post(`/platform/support/tickets/${id}/approve-module`),
    rejectModuleChange: (id: string, data: { reason: string }) =>
        client.post(`/platform/support/tickets/${id}/reject-module`, data),
    getStats: () =>
        client.get('/platform/support/stats'),
};
```

- [ ] **Step 3: Add module CRUD query keys + mutations to company-admin hooks**

Append to `use-company-admin-queries.ts` query keys:

```typescript
supportTickets: (params?: Record<string, unknown>) => [...companyAdminKeys.all, 'support-tickets', params] as const,
supportTicket: (id: string) => [...companyAdminKeys.all, 'support-ticket', id] as const,
```

Add query hooks:

```typescript
export function useSupportTickets(params?: { status?: string; category?: string; search?: string; page?: number }) {
    return useQuery({
        queryKey: companyAdminKeys.supportTickets(params),
        queryFn: () => companyAdminApi.listSupportTickets(params),
    });
}

export function useSupportTicket(id: string) {
    return useQuery({
        queryKey: companyAdminKeys.supportTicket(id),
        queryFn: () => companyAdminApi.getSupportTicket(id),
        enabled: !!id,
        refetchInterval: 10000,
    });
}
```

Append to `use-company-admin-mutations.ts`:

```typescript
export function useCreateSupportTicket() {
    const qc = useQueryClient();
    return useMutation({
        mutationFn: (data: { subject: string; category?: string; priority?: string; message: string; metadata?: Record<string, unknown> }) =>
            companyAdminApi.createSupportTicket(data),
        onSuccess: () => {
            qc.invalidateQueries({ queryKey: companyAdminKeys.supportTickets() });
        },
    });
}

export function useSendSupportMessage() {
    const qc = useQueryClient();
    return useMutation({
        mutationFn: ({ id, body }: { id: string; body: string }) =>
            companyAdminApi.sendSupportMessage(id, { body }),
        onSuccess: (_, vars) => {
            qc.invalidateQueries({ queryKey: companyAdminKeys.supportTicket(vars.id) });
        },
    });
}

export function useCloseSupportTicket() {
    const qc = useQueryClient();
    return useMutation({
        mutationFn: (id: string) => companyAdminApi.closeSupportTicket(id),
        onSuccess: () => {
            qc.invalidateQueries({ queryKey: companyAdminKeys.supportTickets() });
        },
    });
}

export function useAddLocationModules() {
    const qc = useQueryClient();
    return useMutation({
        mutationFn: ({ locationId, moduleIds }: { locationId: string; moduleIds: string[] }) =>
            companyAdminApi.addLocationModules(locationId, { moduleIds }),
        onSuccess: () => {
            qc.invalidateQueries({ queryKey: companyAdminKeys.locations() });
            qc.invalidateQueries({ queryKey: companyAdminKeys.profile() });
            qc.invalidateQueries({ queryKey: companyAdminKeys.moduleCatalogue() });
        },
    });
}

export function useRemoveLocationModule() {
    const qc = useQueryClient();
    return useMutation({
        mutationFn: ({ locationId, moduleId }: { locationId: string; moduleId: string }) =>
            companyAdminApi.removeLocationModule(locationId, moduleId),
        onSuccess: () => {
            qc.invalidateQueries({ queryKey: companyAdminKeys.locations() });
            qc.invalidateQueries({ queryKey: companyAdminKeys.profile() });
            qc.invalidateQueries({ queryKey: companyAdminKeys.moduleCatalogue() });
        },
    });
}
```

- [ ] **Step 4: Create super-admin support hooks**

Create `web-system-app/src/features/super-admin/api/use-support-queries.ts`:

```typescript
import { useQuery } from '@tanstack/react-query';
import { supportApi } from '@/lib/api/support';

export const platformSupportKeys = {
    all: ['platform-support'] as const,
    tickets: (params?: Record<string, unknown>) => [...platformSupportKeys.all, 'tickets', params] as const,
    ticket: (id: string) => [...platformSupportKeys.all, 'ticket', id] as const,
    stats: () => [...platformSupportKeys.all, 'stats'] as const,
};

export function usePlatformSupportTickets(params?: { status?: string; category?: string; search?: string; page?: number }) {
    return useQuery({
        queryKey: platformSupportKeys.tickets(params),
        queryFn: () => supportApi.listTickets(params),
    });
}

export function usePlatformSupportTicket(id: string) {
    return useQuery({
        queryKey: platformSupportKeys.ticket(id),
        queryFn: () => supportApi.getTicket(id),
        enabled: !!id,
        refetchInterval: 10000,
    });
}

export function usePlatformSupportStats() {
    return useQuery({
        queryKey: platformSupportKeys.stats(),
        queryFn: () => supportApi.getStats(),
        refetchInterval: 30000,
    });
}
```

Create `web-system-app/src/features/super-admin/api/use-support-mutations.ts`:

```typescript
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { supportApi } from '@/lib/api/support';
import { platformSupportKeys } from './use-support-queries';

export function useReplySupportTicket() {
    const qc = useQueryClient();
    return useMutation({
        mutationFn: ({ id, body }: { id: string; body: string }) =>
            supportApi.replyToTicket(id, { body }),
        onSuccess: (_, vars) => {
            qc.invalidateQueries({ queryKey: platformSupportKeys.ticket(vars.id) });
        },
    });
}

export function useUpdateTicketStatus() {
    const qc = useQueryClient();
    return useMutation({
        mutationFn: ({ id, status }: { id: string; status: string }) =>
            supportApi.updateTicketStatus(id, { status }),
        onSuccess: () => {
            qc.invalidateQueries({ queryKey: platformSupportKeys.tickets() });
        },
    });
}

export function useApproveModuleChange() {
    const qc = useQueryClient();
    return useMutation({
        mutationFn: (id: string) => supportApi.approveModuleChange(id),
        onSuccess: () => {
            qc.invalidateQueries({ queryKey: platformSupportKeys.tickets() });
            qc.invalidateQueries({ queryKey: platformSupportKeys.stats() });
        },
    });
}

export function useRejectModuleChange() {
    const qc = useQueryClient();
    return useMutation({
        mutationFn: ({ id, reason }: { id: string; reason: string }) =>
            supportApi.rejectModuleChange(id, { reason }),
        onSuccess: () => {
            qc.invalidateQueries({ queryKey: platformSupportKeys.tickets() });
            qc.invalidateQueries({ queryKey: platformSupportKeys.stats() });
        },
    });
}
```

- [ ] **Step 5: Update index.ts re-exports**

Append to `web-system-app/src/features/company-admin/api/index.ts`:

```typescript
// Support
export { useSupportTickets, useSupportTicket } from './use-company-admin-queries';
export { useCreateSupportTicket, useSendSupportMessage, useCloseSupportTicket, useAddLocationModules, useRemoveLocationModule } from './use-company-admin-mutations';
```

- [ ] **Step 6: Verify web compiles**

Run:
```bash
cd web-system-app && npx tsc --noEmit
```

- [ ] **Step 7: Commit**

```bash
git add src/lib/api/ src/features/company-admin/api/ src/features/super-admin/api/
git commit -m "feat(web): add API hooks for support tickets and module CRUD"
```

---

### Task 6: Web — Company Admin Help & Support Screen

**Files:**
- Modify: `web-system-app/src/features/help/HelpSupportScreen.tsx` (full rewrite)
- Create: `web-system-app/src/features/support/TicketChatScreen.tsx`
- Modify: `web-system-app/src/App.tsx` (add route)

This is a large UI task. The Help & Support screen gets two tabs: My Tickets (new) + Help Center (existing FAQ content preserved). The Ticket Chat is a separate screen at `/app/help/ticket/:id`.

- [ ] **Step 1: Rewrite HelpSupportScreen with tickets tab + help center tab**

Rewrite `web-system-app/src/features/help/HelpSupportScreen.tsx`. Keep the existing FAQ/Quick Start content but wrap it in a tabbed layout. Tab 1 = My Tickets (uses `useSupportTickets`), Tab 2 = Help Center (existing content). Include a "New Ticket" modal with subject, category, message fields.

- [ ] **Step 2: Create TicketChatScreen**

Create `web-system-app/src/features/support/TicketChatScreen.tsx`. Chat bubble UI: right-aligned (primary) for own messages, left-aligned (neutral) for admin, centered (muted) for system. Module request summary card at top for MODULE_CHANGE tickets. Input bar at bottom. Uses `useSupportTicket(id)` with 10s polling.

- [ ] **Step 3: Add routes in App.tsx**

Add import and route:
```typescript
import { TicketChatScreen } from "./features/support/TicketChatScreen";
// ...
<Route path="help/ticket/:id" element={<TicketChatScreen />} />
```

- [ ] **Step 4: Verify web compiles and renders**

```bash
cd web-system-app && npx tsc --noEmit
```

- [ ] **Step 5: Commit**

```bash
git add src/features/help/ src/features/support/ src/App.tsx
git commit -m "feat(web): add Help & Support screen with ticket list and chat view"
```

---

### Task 7: Web — Company Admin Module Management UI

**Files:**
- Modify: `web-system-app/src/features/company-admin/CompanyProfileScreen.tsx`

- [ ] **Step 1: Transform Active Modules section to interactive**

Replace the current read-only "Active Modules" section (around line 775-804) in `CompanyProfileScreen.tsx` with an interactive module management UI:

- Per-location expandable sections
- Each location shows all MODULE_CATALOGUE items as toggle cards
- Active modules: green toggle, can click to remove
- Inactive modules: muted toggle, can click to add
- Dependency badges on each card
- For one-time billing: show "Request Add/Remove" buttons instead of toggles
- On add: show confirmation dialog with billing impact before calling `useAddLocationModules`
- On remove: show confirmation with dependent module warning from API 409 response

Uses `useAddLocationModules()` and `useRemoveLocationModule()` mutations. For one-time billing detection, check `location.billingType !== 'monthly' && location.billingType !== 'annual'` or `location.oneTimeLicenseFee > 0`.

- [ ] **Step 2: Verify compiles**

```bash
cd web-system-app && npx tsc --noEmit
```

- [ ] **Step 3: Commit**

```bash
git add src/features/company-admin/CompanyProfileScreen.tsx
git commit -m "feat(web): add interactive module management with billing gate on company profile"
```

---

### Task 8: Web — Super Admin Support Dashboard

**Files:**
- Create: `web-system-app/src/features/super-admin/support/SupportDashboardScreen.tsx`
- Modify: `web-system-app/src/App.tsx`
- Modify: `web-system-app/src/layouts/Sidebar.tsx`

- [ ] **Step 1: Create SupportDashboardScreen**

Create `web-system-app/src/features/super-admin/support/SupportDashboardScreen.tsx`:

- Stats bar: 4 cards (Open, In Progress, Waiting, Resolved Today) using `usePlatformSupportStats()`
- Ticket list table with filters (status, category, search)
- Module change tickets highlighted with special badge
- Click ticket → navigate to `/app/support/ticket/:id`
- Uses `usePlatformSupportTickets(params)`

- [ ] **Step 2: Create Super Admin ticket detail view**

This reuses the chat view pattern from Task 6 but adds:
- Status dropdown to change ticket status
- For MODULE_CHANGE: Approve/Reject buttons
- Company context card showing tenant info

Route: `/app/support/ticket/:id`

- [ ] **Step 3: Add routes in App.tsx**

```typescript
import { SupportDashboardScreen } from "./features/super-admin/support/SupportDashboardScreen";
// ...
<Route path="support" element={<RequireRole roles={['super-admin']}><SupportDashboardScreen /></RequireRole>} />
<Route path="support/ticket/:id" element={<RequireRole roles={['super-admin']}><SupportTicketDetailScreen /></RequireRole>} />
```

- [ ] **Step 4: Add Support to sidebar**

Modify `web-system-app/src/layouts/Sidebar.tsx`:

Add to super-admin management section:
```typescript
{ icon: MessageSquare, label: 'Support', path: '/app/support', badge: supportStats?.open + supportStats?.inProgress }
```

Import `MessageSquare` from lucide-react. The badge count comes from `usePlatformSupportStats()` called in the sidebar component.

- [ ] **Step 5: Verify compiles**

```bash
cd web-system-app && npx tsc --noEmit
```

- [ ] **Step 6: Commit**

```bash
git add src/features/super-admin/support/ src/App.tsx src/layouts/Sidebar.tsx
git commit -m "feat(web): add super-admin support dashboard with module approval workflow"
```

---

## Phase 3: Mobile Frontend

### Task 9: Mobile — API Layer (Support + Module CRUD)

**Files:**
- Modify: `mobile-app/src/lib/api/company-admin.ts`
- Create: `mobile-app/src/lib/api/support.ts`
- Modify: `mobile-app/src/features/company-admin/api/use-company-admin-queries.ts`
- Modify: `mobile-app/src/features/company-admin/api/use-company-admin-mutations.ts`
- Create: `mobile-app/src/features/super-admin/api/use-support-queries.ts`
- Create: `mobile-app/src/features/super-admin/api/use-support-mutations.ts`
- Modify: `mobile-app/src/features/company-admin/api/index.ts`

Mirror the exact same API functions and hooks from Task 5, adapted for mobile patterns (uses `showError` in onError, lazy imports for client).

- [ ] **Step 1: Add support + module CRUD API functions to mobile company-admin.ts**

Same endpoints as web Step 1.

- [ ] **Step 2: Create mobile platform support API file**

Same as web `support.ts`, using mobile client import.

- [ ] **Step 3: Add query keys + hooks to mobile company-admin hooks**

Same pattern as web, with `showError` on mutations.

- [ ] **Step 4: Create mobile super-admin support hooks**

Same as web Task 5 Step 4.

- [ ] **Step 5: Update mobile index.ts re-exports**

- [ ] **Step 6: Verify mobile compiles**

```bash
cd mobile-app && npx tsc --noEmit
```

- [ ] **Step 7: Commit**

```bash
git add src/lib/api/ src/features/company-admin/api/ src/features/super-admin/api/
git commit -m "feat(mobile): add API hooks for support tickets and module CRUD"
```

---

### Task 10: Mobile — Help & Support Screen + Chat View

**Files:**
- Create: `mobile-app/src/features/support/help-support-screen.tsx`
- Create: `mobile-app/src/features/support/ticket-chat-screen.tsx`
- Create: `mobile-app/src/app/(app)/support.tsx`
- Create: `mobile-app/src/app/(app)/support/ticket/[id].tsx`
- Modify: `mobile-app/src/app/(app)/_layout.tsx`

- [ ] **Step 1: Create help-support-screen.tsx**

Two tabs (using ScrollView + tab buttons): My Tickets + Help Center.
My Tickets: FlatList of ticket cards with status badges, category chips.
FAB for "New Ticket" → bottom sheet form.
Help Center: FAQ content ported from web.

- [ ] **Step 2: Create ticket-chat-screen.tsx**

Chat bubble UI (FlatList, inverted). Right = own (primary bg), Left = admin (neutral bg), Center = system (muted).
Module request card at top for MODULE_CHANGE tickets.
KeyboardAvoidingView + text input at bottom.
Uses `useSupportTicket(id)` with 10s refetch.

- [ ] **Step 3: Create route files**

`src/app/(app)/support.tsx`:
```typescript
export { HelpSupportScreen as default } from '@/features/support/help-support-screen';
```

Create `src/app/(app)/support/` directory with `_layout.tsx` (Stack navigator) and `ticket/[id].tsx`:
```typescript
export { TicketChatScreen as default } from '@/features/support/ticket-chat-screen';
```

- [ ] **Step 4: Wire sidebar navigation**

In `_layout.tsx`, find the company-admin sidebar sections and add "Help & Support" item:
```typescript
{ label: 'Help & Support', icon: 'help', onPress: () => router.push('/support') }
```

Wire the super-admin "Support" item (currently empty handler):
```typescript
{ label: 'Support', icon: 'support', onPress: () => router.push('/support') }
```

- [ ] **Step 5: Verify compiles**

```bash
cd mobile-app && npx tsc --noEmit
```

- [ ] **Step 6: Commit**

```bash
git add src/features/support/ src/app/ src/app/\(app\)/_layout.tsx
git commit -m "feat(mobile): add Help & Support screen with ticket chat view"
```

---

### Task 11: Mobile — Company Admin Module Management UI

**Files:**
- Modify: `mobile-app/src/features/company-admin/company-profile-screen.tsx`

- [ ] **Step 1: Transform Active Modules section to interactive**

Same logic as web Task 7: replace read-only module display with interactive toggles per location. Use `useAddLocationModules()` and `useRemoveLocationModule()`. One-time billing shows "Request" buttons. Uses `ConfirmModal` for confirmations (not Alert).

- [ ] **Step 2: Verify compiles**

```bash
cd mobile-app && npx tsc --noEmit
```

- [ ] **Step 3: Commit**

```bash
git add src/features/company-admin/company-profile-screen.tsx
git commit -m "feat(mobile): add interactive module management on company profile"
```

---

### Task 12: Mobile — Super Admin Support Dashboard

**Files:**
- Create: `mobile-app/src/features/super-admin/support/support-dashboard-screen.tsx`
- Create: `mobile-app/src/app/(app)/admin-support.tsx` (separate route to avoid conflict with company-admin support)

- [ ] **Step 1: Create support-dashboard-screen.tsx**

Stats bar (4 cards), ticket FlatList with filters, MODULE_CHANGE highlighted.
Tap ticket → navigate to chat view at `/support/ticket/[id]` (shared chat screen detects role and shows admin controls).

- [ ] **Step 2: Add admin controls to shared chat screen**

In `ticket-chat-screen.tsx`, detect if user is SUPER_ADMIN and show:
- Status change picker
- Approve/Reject buttons for MODULE_CHANGE tickets
- Company context card

- [ ] **Step 3: Create route file + wire sidebar**

`src/app/(app)/admin-support.tsx`:
```typescript
export { SupportDashboardScreen as default } from '@/features/super-admin/support/support-dashboard-screen';
```

Wire super-admin sidebar "Support" → `/admin-support`.

- [ ] **Step 4: Verify compiles**

```bash
cd mobile-app && npx tsc --noEmit
```

- [ ] **Step 5: Commit**

```bash
git add src/features/super-admin/support/ src/app/
git commit -m "feat(mobile): add super-admin support dashboard with module approval"
```

---

## Phase 4: Final Integration

### Task 13: Final Verification & Cleanup

- [ ] **Step 1: Run full type checks on all three codebases**

```bash
cd avy-erp-backend && npx tsc --noEmit
cd ../web-system-app && npx tsc --noEmit
cd ../mobile-app && npx tsc --noEmit
```

- [ ] **Step 2: Test the complete flow manually**

Verify:
1. Monthly tenant → can add/remove modules directly
2. One-time tenant → gets 403 on direct CRUD, can raise support ticket
3. Super admin → sees ticket, can approve/reject
4. Module dependencies resolve correctly
5. Chat messages flow in real-time (10s polling)
6. Sidebar badges show correct counts

- [ ] **Step 3: Final commit**

```bash
git add -A
git commit -m "feat: complete module CRUD & support ticket system implementation"
```
