.
├── avy-erp-backend
│   ├── Dockerfile
│   ├── README.md
│   ├── deploy.sh
│   ├── deployment-guide.md
│   ├── docker-compose.yml
│   ├── jest.config.ts
│   ├── logs
│   │   ├── app-error.log
│   │   └── app.log
│   ├── package-lock.json
│   ├── package.json
│   ├── prisma
│   │   ├── migrations
│   │   │   ├── 20260321084920_init
│   │   │   │   └── migration.sql
│   │   │   ├── 20260323043711_shift_addition
│   │   │   │   └── migration.sql
│   │   │   ├── 20260327144902_rbac_fix
│   │   │   │   └── migration.sql
│   │   │   ├── 20260328012812_hrms_fix
│   │   │   │   └── migration.sql
│   │   │   ├── 20260328025108_hrms_phase1_audit_remediation
│   │   │   │   └── migration.sql
│   │   │   ├── 20260328034622_hrms_phase2_full_implementation
│   │   │   │   └── migration.sql
│   │   │   └── migration_lock.toml
│   │   ├── schema.prisma
│   │   ├── seed-rbac-fix.ts
│   │   └── seed.ts
│   ├── project-structure.md
│   ├── src
│   │   ├── __tests__
│   │   │   └── setup.ts
│   │   ├── app
│   │   │   ├── __tests__
│   │   │   │   └── openapi.integration.test.ts
│   │   │   ├── app.ts
│   │   │   ├── openapi.ts
│   │   │   ├── routes.ts
│   │   │   └── server.ts
│   │   ├── config
│   │   │   ├── database.ts
│   │   │   ├── env.ts
│   │   │   ├── logger.ts
│   │   │   └── redis.ts
│   │   ├── core
│   │   │   ├── audit
│   │   │   │   ├── __tests__
│   │   │   │   │   └── audit.service.test.ts
│   │   │   │   ├── audit.controller.ts
│   │   │   │   ├── audit.routes.ts
│   │   │   │   └── audit.service.ts
│   │   │   ├── auth
│   │   │   │   ├── __tests__
│   │   │   │   │   ├── auth.integration.test.ts
│   │   │   │   │   └── auth.service.test.ts
│   │   │   │   ├── auth.controller.ts
│   │   │   │   ├── auth.routes.ts
│   │   │   │   ├── auth.service.ts
│   │   │   │   └── auth.types.ts
│   │   │   ├── billing
│   │   │   │   ├── __tests__
│   │   │   │   │   ├── billing.service.test.ts
│   │   │   │   │   ├── invoice.service.test.ts
│   │   │   │   │   ├── payment.service.test.ts
│   │   │   │   │   ├── pricing.service.test.ts
│   │   │   │   │   └── subscription.service.test.ts
│   │   │   │   ├── billing-config.controller.ts
│   │   │   │   ├── billing-config.routes.ts
│   │   │   │   ├── billing-config.service.ts
│   │   │   │   ├── billing.controller.ts
│   │   │   │   ├── billing.routes.ts
│   │   │   │   ├── billing.service.ts
│   │   │   │   ├── billing.validators.ts
│   │   │   │   ├── invoice.controller.ts
│   │   │   │   ├── invoice.routes.ts
│   │   │   │   ├── invoice.service.ts
│   │   │   │   ├── payment.controller.ts
│   │   │   │   ├── payment.routes.ts
│   │   │   │   ├── payment.service.ts
│   │   │   │   ├── pdf.service.ts
│   │   │   │   ├── pricing.service.ts
│   │   │   │   ├── subscription.controller.ts
│   │   │   │   ├── subscription.routes.ts
│   │   │   │   └── subscription.service.ts
│   │   │   ├── company
│   │   │   │   ├── __tests__
│   │   │   │   │   └── company.service.test.ts
│   │   │   │   ├── company.controller.ts
│   │   │   │   ├── company.routes.ts
│   │   │   │   └── company.service.ts
│   │   │   ├── company-admin
│   │   │   │   ├── company-admin.controller.ts
│   │   │   │   ├── company-admin.routes.ts
│   │   │   │   ├── company-admin.service.ts
│   │   │   │   └── company-admin.validators.ts
│   │   │   ├── dashboard
│   │   │   │   ├── __tests__
│   │   │   │   │   └── dashboard.service.test.ts
│   │   │   │   ├── dashboard.controller.ts
│   │   │   │   ├── dashboard.routes.ts
│   │   │   │   └── dashboard.service.ts
│   │   │   ├── feature-toggle
│   │   │   │   ├── feature-toggle.controller.ts
│   │   │   │   ├── feature-toggle.routes.ts
│   │   │   │   └── feature-toggle.service.ts
│   │   │   ├── rbac
│   │   │   │   ├── __tests__
│   │   │   │   │   └── rbac.service.test.ts
│   │   │   │   ├── rbac.controller.ts
│   │   │   │   ├── rbac.routes.ts
│   │   │   │   ├── rbac.service.ts
│   │   │   │   └── rbac.types.ts
│   │   │   ├── support
│   │   │   │   ├── support.controller.ts
│   │   │   │   ├── support.routes.ts
│   │   │   │   ├── support.service.ts
│   │   │   │   └── support.validators.ts
│   │   │   └── tenant
│   │   │       ├── __tests__
│   │   │       │   └── tenant-onboarding.test.ts
│   │   │       ├── tenant.controller.ts
│   │   │       ├── tenant.routes.ts
│   │   │       ├── tenant.service.ts
│   │   │       ├── tenant.types.ts
│   │   │       └── tenant.validators.ts
│   │   ├── infrastructure
│   │   │   ├── cache
│   │   │   │   └── cache.service.ts
│   │   │   ├── database
│   │   │   │   └── connection.ts
│   │   │   ├── email
│   │   │   │   ├── __tests__
│   │   │   │   │   └── email.service.test.ts
│   │   │   │   └── email.service.ts
│   │   │   ├── queue
│   │   │   │   └── report.queue.ts
│   │   │   └── storage
│   │   │       └── storage.service.ts
│   │   ├── lib
│   │   │   └── socket.ts
│   │   ├── middleware
│   │   │   ├── __tests__
│   │   │   │   └── auth.middleware.test.ts
│   │   │   ├── auth.middleware.ts
│   │   │   ├── error.middleware.ts
│   │   │   ├── logging.middleware.ts
│   │   │   └── tenant.middleware.ts
│   │   ├── modules
│   │   │   ├── hr
│   │   │   │   ├── advanced
│   │   │   │   │   ├── advanced.controller.ts
│   │   │   │   │   ├── advanced.routes.ts
│   │   │   │   │   ├── advanced.service.ts
│   │   │   │   │   └── advanced.validators.ts
│   │   │   │   ├── attendance
│   │   │   │   │   ├── attendance.controller.ts
│   │   │   │   │   ├── attendance.routes.ts
│   │   │   │   │   ├── attendance.service.ts
│   │   │   │   │   └── attendance.validators.ts
│   │   │   │   ├── chatbot
│   │   │   │   │   ├── chatbot.controller.ts
│   │   │   │   │   ├── chatbot.routes.ts
│   │   │   │   │   ├── chatbot.service.ts
│   │   │   │   │   └── chatbot.validators.ts
│   │   │   │   ├── employee
│   │   │   │   │   ├── employee.controller.ts
│   │   │   │   │   ├── employee.routes.ts
│   │   │   │   │   ├── employee.service.ts
│   │   │   │   │   └── employee.validators.ts
│   │   │   │   ├── ess
│   │   │   │   │   ├── ess.controller.ts
│   │   │   │   │   ├── ess.routes.ts
│   │   │   │   │   ├── ess.service.ts
│   │   │   │   │   └── ess.validators.ts
│   │   │   │   ├── leave
│   │   │   │   │   ├── leave.controller.ts
│   │   │   │   │   ├── leave.routes.ts
│   │   │   │   │   ├── leave.service.ts
│   │   │   │   │   └── leave.validators.ts
│   │   │   │   ├── offboarding
│   │   │   │   │   ├── offboarding.controller.ts
│   │   │   │   │   ├── offboarding.routes.ts
│   │   │   │   │   ├── offboarding.service.ts
│   │   │   │   │   └── offboarding.validators.ts
│   │   │   │   ├── onboarding
│   │   │   │   │   ├── onboarding.controller.ts
│   │   │   │   │   ├── onboarding.routes.ts
│   │   │   │   │   ├── onboarding.service.ts
│   │   │   │   │   └── onboarding.validators.ts
│   │   │   │   ├── org-structure
│   │   │   │   │   ├── org-structure.controller.ts
│   │   │   │   │   ├── org-structure.routes.ts
│   │   │   │   │   ├── org-structure.service.ts
│   │   │   │   │   └── org-structure.validators.ts
│   │   │   │   ├── payroll
│   │   │   │   │   ├── payroll.controller.ts
│   │   │   │   │   ├── payroll.routes.ts
│   │   │   │   │   ├── payroll.service.ts
│   │   │   │   │   └── payroll.validators.ts
│   │   │   │   ├── payroll-run
│   │   │   │   │   ├── payroll-run.controller.ts
│   │   │   │   │   ├── payroll-run.routes.ts
│   │   │   │   │   ├── payroll-run.service.ts
│   │   │   │   │   └── payroll-run.validators.ts
│   │   │   │   ├── performance
│   │   │   │   │   ├── performance.controller.ts
│   │   │   │   │   ├── performance.routes.ts
│   │   │   │   │   ├── performance.service.ts
│   │   │   │   │   └── performance.validators.ts
│   │   │   │   ├── retention
│   │   │   │   │   ├── retention.controller.ts
│   │   │   │   │   ├── retention.routes.ts
│   │   │   │   │   ├── retention.service.ts
│   │   │   │   │   └── retention.validators.ts
│   │   │   │   ├── routes.ts
│   │   │   │   └── transfer
│   │   │   │       ├── transfer.controller.ts
│   │   │   │       ├── transfer.routes.ts
│   │   │   │       ├── transfer.service.ts
│   │   │   │       └── transfer.validators.ts
│   │   │   ├── inventory
│   │   │   │   └── routes.ts
│   │   │   ├── machines
│   │   │   │   └── routes.ts
│   │   │   ├── maintenance
│   │   │   │   └── routes.ts
│   │   │   ├── production
│   │   │   │   └── routes.ts
│   │   │   ├── reports
│   │   │   │   └── routes.ts
│   │   │   └── visitors
│   │   │       └── routes.ts
│   │   ├── shared
│   │   │   ├── constants
│   │   │   │   ├── __tests__
│   │   │   │   │   └── permissions.test.ts
│   │   │   │   ├── feature-toggles.ts
│   │   │   │   ├── index.ts
│   │   │   │   └── permissions.ts
│   │   │   ├── errors
│   │   │   │   ├── api-error.ts
│   │   │   │   ├── auth-error.ts
│   │   │   │   ├── index.ts
│   │   │   │   └── validation-error.ts
│   │   │   ├── types
│   │   │   │   └── index.ts
│   │   │   ├── utils
│   │   │   │   └── index.ts
│   │   │   └── validators
│   │   │       └── index.ts
│   │   └── workers
│   │       ├── analytics.worker.ts
│   │       ├── approval-sla.worker.ts
│   │       ├── billing.worker.ts
│   │       ├── notification.worker.ts
│   │       ├── report.worker.ts
│   │       └── sla-cron.ts
│   └── tsconfig.json
├── docs
│   ├── 01_Avy_ERP_Tenant_Onboarding_SuperAdmin.md
│   ├── 02_Avy_ERP_HRMS_Module_Configuration.md
│   ├── 03_Avy_ERP_Super_Admin_Panel_Reference.md
│   ├── 04_Super_Admin_Development_Checklist.md
│   ├── 05_Multi_Tenancy_Architecture_Guide.md
│   ├── AVY_ERP_HRMS_FINALISED.md
│   ├── Archive
│   │   ├── 2-PRD-hrms-configeration information Doc.html
│   │   ├── 3-Company Settup UI.html
│   │   ├── 4-PRD -hrms-transactions-redesign (1).html
│   │   ├── 5-hrms-employee-hub (2).html
│   │   ├── 6-hr-operations-v4.html
│   │   ├── 7-hrms-performance-unified (1).html
│   │   └── JSON-Response.md
│   ├── Company Profile.html
│   ├── HRMS_AUDIT_REPORT.md
│   ├── HRMS_CODE_AUDIT_FINAL_SIGN_OFF.md
│   ├── HRMS_FINAL_AUDIT_REPORT.md
│   ├── HRMS_NEW_FEATURES_TESTING_GUIDE.md
│   ├── HRMS_PHASE2_ROADMAP.md
│   ├── Mobile_ERP_PRD_Three_Modules.html
│   ├── api-endpoints-part1.md
│   ├── api-endpoints-part2.md
│   ├── avy-erp-complete-user-guide.md
│   ├── avy-erp-prd.md
│   ├── company-master.html
│   ├── duplicates
│   │   └── tenant-onboarding-screen.tsx
│   ├── final_avy_erp_web_defect_report.md
│   └── superpowers
│       ├── plans
│       │   ├── 2026-03-19-billing-invoicing.md
│       │   ├── 2026-03-19-company-admin-and-hrms-master-plan.md
│       │   ├── 2026-03-19-full-stack-integration.md
│       │   ├── 2026-03-19-phase1-company-admin-core.md
│       │   ├── 2026-03-19-super-admin-sprint1-3.md
│       │   ├── 2026-03-20-hrms-feature-scope-register.md
│       │   ├── 2026-03-20-implementation-checklist.md
│       │   ├── 2026-03-20-manual-testing-guide.md
│       │   ├── 2026-03-27-module-crud-support-system.md
│       │   ├── 2026-03-27-sidebar-rbac-module-separation.md
│       │   ├── 2026-03-28-hrms-audit-remediation.md
│       │   ├── 2026-03-28-hrms-phase2-implementation.md
│       │   └── HRMS
│       │       └── Key-matrix.md
│       └── specs
│           ├── 2026-03-19-billing-invoicing-design.md
│           └── 2026-03-27-module-crud-support-system-design.md
├── mobile-app
│   ├── LICENSE
│   ├── README-project.md
│   ├── README.md
│   ├── __mocks__
│   │   ├── @gorhom
│   │   │   └── bottom-sheet.ts
│   │   ├── expo-localization.ts
│   │   ├── moti.ts
│   │   ├── react-native-gesture-handler.ts
│   │   └── react-native-keyboard-controller.ts
│   ├── app.config.ts
│   ├── assets
│   │   ├── Company-Logo-WithBG.png
│   │   ├── Company-Logo.png
│   │   ├── adaptive-icon.png
│   │   ├── favicon.png
│   │   ├── icon.png
│   │   ├── illustrations
│   │   │   ├── Login-Screen.png
│   │   │   ├── Onboarding-1-Light.png
│   │   │   ├── Onboarding-1.png
│   │   │   ├── Onboarding-2-Light.png
│   │   │   ├── Onboarding-2.png
│   │   │   ├── Onboarding-3-Light.png
│   │   │   ├── Onboarding-3.png
│   │   │   ├── illustration-2.jpeg
│   │   │   ├── illustrations-1.jpeg
│   │   │   └── illustrations-3.jpeg
│   │   └── splash-icon.png
│   ├── babel.config.js
│   ├── claude.md
│   ├── cli
│   │   ├── README.md
│   │   ├── clone-repo.js
│   │   ├── index.js
│   │   ├── package.json
│   │   ├── pnpm-lock.yaml
│   │   ├── setup-project.js
│   │   └── utils.js
│   ├── commitlint.config.js
│   ├── coverage
│   │   └── jest-junit.xml
│   ├── cspell.json
│   ├── docs
│   │   ├── README.md
│   │   ├── astro.config.mjs
│   │   ├── package.json
│   │   ├── pnpm-lock.yaml
│   │   ├── public
│   │   │   ├── _redirects
│   │   │   ├── favicon.svg
│   │   │   ├── og.jpg
│   │   │   └── reviews
│   │   │       ├── aman.jpg
│   │   │       ├── brandon.png
│   │   │       ├── kawtar.jpg
│   │   │       ├── simon.jpg
│   │   │       └── yuri.jpeg
│   │   ├── src
│   │   │   ├── assets
│   │   │   │   ├── logo-titled.svg
│   │   │   │   └── logo.webp
│   │   │   ├── components
│   │   │   │   ├── Comments.astro
│   │   │   │   ├── GithubStar.astro
│   │   │   │   ├── LastUpdated.astro
│   │   │   │   ├── about.astro
│   │   │   │   ├── code.astro
│   │   │   │   └── reviews.astro
│   │   │   ├── content
│   │   │   │   └── docs
│   │   │   │       ├── changelog.md
│   │   │   │       ├── ci-cd
│   │   │   │       │   ├── app-releasing-process.mdx
│   │   │   │       │   ├── overview.mdx
│   │   │   │       │   └── workflows-references.mdx
│   │   │   │       ├── faq.md
│   │   │   │       ├── getting-started
│   │   │   │       │   ├── create-new-app.md
│   │   │   │       │   ├── customize-app.mdx
│   │   │   │       │   ├── environment-vars-config.mdx
│   │   │   │       │   ├── project-structure.mdx
│   │   │   │       │   └── rules-and-conventions.mdx
│   │   │   │       ├── guides
│   │   │   │       │   ├── authentication.mdx
│   │   │   │       │   ├── data-fetching.mdx
│   │   │   │       │   ├── internationalization.mdx
│   │   │   │       │   ├── navigation.mdx
│   │   │   │       │   ├── storage.mdx
│   │   │   │       │   └── upgrading-deps.mdx
│   │   │   │       ├── how-to-contribute.md
│   │   │   │       ├── index.mdx
│   │   │   │       ├── libraries-recommendation.md
│   │   │   │       ├── overview.md
│   │   │   │       ├── recipes
│   │   │   │       │   └── sentry-setup.mdx
│   │   │   │       ├── reviews.md
│   │   │   │       ├── stay-updated.md
│   │   │   │       ├── testing
│   │   │   │       │   ├── end-to-end-testing.mdx
│   │   │   │       │   ├── overview.mdx
│   │   │   │       │   └── unit-testing.mdx
│   │   │   │       └── ui-and-theme
│   │   │   │           ├── Forms.mdx
│   │   │   │           ├── components.mdx
│   │   │   │           ├── fonts.mdx
│   │   │   │           └── ui-theming.mdx
│   │   │   ├── content.config.ts
│   │   │   ├── env.d.ts
│   │   │   └── styles
│   │   │       └── custom.css
│   │   └── tsconfig.json
│   ├── eas.json
│   ├── env.ts
│   ├── eslint.config.mjs
│   ├── expo-env.d.ts
│   ├── husky
│   │   ├── _
│   │   │   ├── applypatch-msg
│   │   │   ├── commit-msg
│   │   │   ├── h
│   │   │   ├── husky.sh
│   │   │   ├── post-applypatch
│   │   │   ├── post-checkout
│   │   │   ├── post-commit
│   │   │   ├── post-merge
│   │   │   ├── post-rewrite
│   │   │   ├── pre-applypatch
│   │   │   ├── pre-auto-gc
│   │   │   ├── pre-commit
│   │   │   ├── pre-merge-commit
│   │   │   ├── pre-push
│   │   │   ├── pre-rebase
│   │   │   └── prepare-commit-msg
│   │   ├── commit-msg
│   │   ├── common.sh
│   │   ├── post-merge
│   │   └── pre-commit
│   ├── jest-setup.ts
│   ├── jest.config.js
│   ├── lint-staged.config.js
│   ├── metro.config.js
│   ├── nativewind-env.d.ts
│   ├── package.json
│   ├── pnpm-lock.yaml
│   ├── scripts
│   │   ├── genrate-apk-and-install
│   │   ├── i18next-syntax-validation.js
│   │   └── verify-setup.js
│   ├── src
│   │   ├── app
│   │   │   ├── (app)
│   │   │   │   ├── _layout.tsx
│   │   │   │   ├── admin-support.tsx
│   │   │   │   ├── billing
│   │   │   │   │   ├── _layout.tsx
│   │   │   │   │   ├── index.tsx
│   │   │   │   │   ├── invoice
│   │   │   │   │   │   └── [id].tsx
│   │   │   │   │   ├── invoices.tsx
│   │   │   │   │   ├── payments.tsx
│   │   │   │   │   └── subscriptions
│   │   │   │   │       └── [companyId].tsx
│   │   │   │   ├── companies.tsx
│   │   │   │   ├── company
│   │   │   │   │   ├── _layout.tsx
│   │   │   │   │   ├── billing-invoices.tsx
│   │   │   │   │   ├── billing-payments.tsx
│   │   │   │   │   ├── billing.tsx
│   │   │   │   │   ├── contacts.tsx
│   │   │   │   │   ├── controls.tsx
│   │   │   │   │   ├── feature-toggles.tsx
│   │   │   │   │   ├── hr
│   │   │   │   │   │   ├── _layout.tsx
│   │   │   │   │   │   ├── appraisal-cycles.tsx
│   │   │   │   │   │   ├── approval-requests.tsx
│   │   │   │   │   │   ├── approval-workflows.tsx
│   │   │   │   │   │   ├── assets.tsx
│   │   │   │   │   │   ├── attendance-overrides.tsx
│   │   │   │   │   │   ├── attendance-rules.tsx
│   │   │   │   │   │   ├── attendance.tsx
│   │   │   │   │   │   ├── bank-config.tsx
│   │   │   │   │   │   ├── biometric-devices.tsx
│   │   │   │   │   │   ├── bonus-batches.tsx
│   │   │   │   │   │   ├── candidates.tsx
│   │   │   │   │   │   ├── chatbot.tsx
│   │   │   │   │   │   ├── clearance-dashboard.tsx
│   │   │   │   │   │   ├── cost-centres.tsx
│   │   │   │   │   │   ├── data-retention.tsx
│   │   │   │   │   │   ├── delegates.tsx
│   │   │   │   │   │   ├── departments.tsx
│   │   │   │   │   │   ├── designations.tsx
│   │   │   │   │   │   ├── disciplinary.tsx
│   │   │   │   │   │   ├── employee-detail.tsx
│   │   │   │   │   │   ├── employee-salary.tsx
│   │   │   │   │   │   ├── employee-types.tsx
│   │   │   │   │   │   ├── employees.tsx
│   │   │   │   │   │   ├── esign.tsx
│   │   │   │   │   │   ├── ess-config.tsx
│   │   │   │   │   │   ├── exit-requests.tsx
│   │   │   │   │   │   ├── expenses.tsx
│   │   │   │   │   │   ├── feedback-360.tsx
│   │   │   │   │   │   ├── fnf-settlement.tsx
│   │   │   │   │   │   ├── form-16.tsx
│   │   │   │   │   │   ├── goals.tsx
│   │   │   │   │   │   ├── grades.tsx
│   │   │   │   │   │   ├── grievances.tsx
│   │   │   │   │   │   ├── holidays.tsx
│   │   │   │   │   │   ├── hr-letters.tsx
│   │   │   │   │   │   ├── it-declarations.tsx
│   │   │   │   │   │   ├── leave-balances.tsx
│   │   │   │   │   │   ├── leave-policies.tsx
│   │   │   │   │   │   ├── leave-requests.tsx
│   │   │   │   │   │   ├── leave-types.tsx
│   │   │   │   │   │   ├── loan-policies.tsx
│   │   │   │   │   │   ├── loans.tsx
│   │   │   │   │   │   ├── my-attendance.tsx
│   │   │   │   │   │   ├── my-leave.tsx
│   │   │   │   │   │   ├── my-payslips.tsx
│   │   │   │   │   │   ├── my-profile.tsx
│   │   │   │   │   │   ├── notification-rules.tsx
│   │   │   │   │   │   ├── notification-templates.tsx
│   │   │   │   │   │   ├── onboarding.tsx
│   │   │   │   │   │   ├── org-chart.tsx
│   │   │   │   │   │   ├── overtime-rules.tsx
│   │   │   │   │   │   ├── payroll-reports.tsx
│   │   │   │   │   │   ├── payroll-runs.tsx
│   │   │   │   │   │   ├── payslips.tsx
│   │   │   │   │   │   ├── performance-dashboard.tsx
│   │   │   │   │   │   ├── probation-reviews.tsx
│   │   │   │   │   │   ├── production-incentives.tsx
│   │   │   │   │   │   ├── promotions.tsx
│   │   │   │   │   │   ├── ratings.tsx
│   │   │   │   │   │   ├── requisitions.tsx
│   │   │   │   │   │   ├── rosters.tsx
│   │   │   │   │   │   ├── salary-components.tsx
│   │   │   │   │   │   ├── salary-holds.tsx
│   │   │   │   │   │   ├── salary-revisions.tsx
│   │   │   │   │   │   ├── salary-structures.tsx
│   │   │   │   │   │   ├── shift-check-in.tsx
│   │   │   │   │   │   ├── shift-rotations.tsx
│   │   │   │   │   │   ├── skills.tsx
│   │   │   │   │   │   ├── statutory-config.tsx
│   │   │   │   │   │   ├── statutory-filings.tsx
│   │   │   │   │   │   ├── succession.tsx
│   │   │   │   │   │   ├── tax-config.tsx
│   │   │   │   │   │   ├── team-view.tsx
│   │   │   │   │   │   ├── training-nominations.tsx
│   │   │   │   │   │   ├── training.tsx
│   │   │   │   │   │   ├── transfers.tsx
│   │   │   │   │   │   └── travel-advances.tsx
│   │   │   │   │   ├── inventory.tsx
│   │   │   │   │   ├── iot-reasons.tsx
│   │   │   │   │   ├── locations.tsx
│   │   │   │   │   ├── maintenance.tsx
│   │   │   │   │   ├── module-catalogue.tsx
│   │   │   │   │   ├── no-series.tsx
│   │   │   │   │   ├── production.tsx
│   │   │   │   │   ├── profile.tsx
│   │   │   │   │   ├── roles.tsx
│   │   │   │   │   ├── settings.tsx
│   │   │   │   │   ├── shifts.tsx
│   │   │   │   │   └── users.tsx
│   │   │   │   ├── index.tsx
│   │   │   │   ├── more.tsx
│   │   │   │   ├── reports
│   │   │   │   │   ├── _layout.tsx
│   │   │   │   │   └── audit.tsx
│   │   │   │   ├── settings.tsx
│   │   │   │   ├── support
│   │   │   │   │   ├── _layout.tsx
│   │   │   │   │   ├── index.tsx
│   │   │   │   │   └── ticket
│   │   │   │   │       └── [id].tsx
│   │   │   │   └── tenant
│   │   │   │       ├── [id].tsx
│   │   │   │       ├── add-company.tsx
│   │   │   │       └── module-assignment.tsx
│   │   │   ├── +html.tsx
│   │   │   ├── [...messing].tsx
│   │   │   ├── _layout.tsx
│   │   │   ├── forgot-password.tsx
│   │   │   ├── login.tsx
│   │   │   └── onboarding.tsx
│   │   ├── components
│   │   │   └── ui
│   │   │       ├── SKELETON_README.md
│   │   │       ├── button.test.tsx
│   │   │       ├── button.tsx
│   │   │       ├── checkbox.test.tsx
│   │   │       ├── checkbox.tsx
│   │   │       ├── colors.js
│   │   │       ├── confirm-modal.tsx
│   │   │       ├── empty-state.tsx
│   │   │       ├── fab.tsx
│   │   │       ├── focus-aware-status-bar.tsx
│   │   │       ├── form-utils.ts
│   │   │       ├── icons
│   │   │       │   ├── arrow-right.tsx
│   │   │       │   ├── caret-down.tsx
│   │   │       │   ├── github.tsx
│   │   │       │   ├── home.tsx
│   │   │       │   ├── index.tsx
│   │   │       │   ├── language.tsx
│   │   │       │   ├── rate.tsx
│   │   │       │   ├── settings.tsx
│   │   │       │   ├── share.tsx
│   │   │       │   ├── style.tsx
│   │   │       │   ├── support.tsx
│   │   │       │   └── website.tsx
│   │   │       ├── image.tsx
│   │   │       ├── index.tsx
│   │   │       ├── input.test.tsx
│   │   │       ├── input.tsx
│   │   │       ├── list.tsx
│   │   │       ├── modal-keyboard-aware-scroll-view.tsx
│   │   │       ├── modal.tsx
│   │   │       ├── no-permission-screen.tsx
│   │   │       ├── progress-bar.tsx
│   │   │       ├── search-bar.tsx
│   │   │       ├── select.test.tsx
│   │   │       ├── select.tsx
│   │   │       ├── sidebar.tsx
│   │   │       ├── skeleton-examples.tsx
│   │   │       ├── skeleton.tsx
│   │   │       ├── status-badge.tsx
│   │   │       ├── text.tsx
│   │   │       ├── use-theme-config.tsx
│   │   │       └── utils.tsx
│   │   ├── features
│   │   │   ├── auth
│   │   │   │   ├── __tests__
│   │   │   │   │   ├── use-auth-mutations.test.ts
│   │   │   │   │   └── use-auth-store.test.ts
│   │   │   │   ├── forgot-password-screen.tsx
│   │   │   │   ├── login-screen.tsx
│   │   │   │   ├── use-auth-mutations.ts
│   │   │   │   └── use-auth-store.ts
│   │   │   ├── company-admin
│   │   │   │   ├── api
│   │   │   │   │   ├── index.ts
│   │   │   │   │   ├── use-attendance-mutations.ts
│   │   │   │   │   ├── use-attendance-queries.ts
│   │   │   │   │   ├── use-biometric-mutations.ts
│   │   │   │   │   ├── use-biometric-queries.ts
│   │   │   │   │   ├── use-bonus-batch-mutations.ts
│   │   │   │   │   ├── use-bonus-batch-queries.ts
│   │   │   │   │   ├── use-chatbot-mutations.ts
│   │   │   │   │   ├── use-chatbot-queries.ts
│   │   │   │   │   ├── use-company-admin-mutations.ts
│   │   │   │   │   ├── use-company-admin-queries.ts
│   │   │   │   │   ├── use-ess-mutations.ts
│   │   │   │   │   ├── use-ess-queries.ts
│   │   │   │   │   ├── use-hr-mutations.ts
│   │   │   │   │   ├── use-hr-queries.ts
│   │   │   │   │   ├── use-leave-mutations.ts
│   │   │   │   │   ├── use-leave-queries.ts
│   │   │   │   │   ├── use-offboarding-mutations.ts
│   │   │   │   │   ├── use-offboarding-queries.ts
│   │   │   │   │   ├── use-onboarding-mutations.ts
│   │   │   │   │   ├── use-onboarding-queries.ts
│   │   │   │   │   ├── use-payroll-mutations.ts
│   │   │   │   │   ├── use-payroll-queries.ts
│   │   │   │   │   ├── use-payroll-run-mutations.ts
│   │   │   │   │   ├── use-payroll-run-queries.ts
│   │   │   │   │   ├── use-performance-mutations.ts
│   │   │   │   │   ├── use-performance-queries.ts
│   │   │   │   │   ├── use-production-incentive-mutations.ts
│   │   │   │   │   ├── use-production-incentive-queries.ts
│   │   │   │   │   ├── use-recruitment-mutations.ts
│   │   │   │   │   ├── use-recruitment-queries.ts
│   │   │   │   │   ├── use-retention-mutations.ts
│   │   │   │   │   ├── use-retention-queries.ts
│   │   │   │   │   ├── use-shift-rotation-mutations.ts
│   │   │   │   │   ├── use-shift-rotation-queries.ts
│   │   │   │   │   ├── use-transfer-mutations.ts
│   │   │   │   │   └── use-transfer-queries.ts
│   │   │   │   ├── billing-dashboard-screen.tsx
│   │   │   │   ├── company-profile-screen.tsx
│   │   │   │   ├── company-settings-screen.tsx
│   │   │   │   ├── contact-management-screen.tsx
│   │   │   │   ├── dashboard-screen.tsx
│   │   │   │   ├── feature-toggle-screen.tsx
│   │   │   │   ├── hr
│   │   │   │   │   ├── appraisal-cycles-screen.tsx
│   │   │   │   │   ├── approval-request-screen.tsx
│   │   │   │   │   ├── approval-workflow-screen.tsx
│   │   │   │   │   ├── assets-screen.tsx
│   │   │   │   │   ├── attendance-dashboard-screen.tsx
│   │   │   │   │   ├── attendance-override-screen.tsx
│   │   │   │   │   ├── attendance-rules-screen.tsx
│   │   │   │   │   ├── bank-config-screen.tsx
│   │   │   │   │   ├── biometric-device-screen.tsx
│   │   │   │   │   ├── bonus-batch-screen.tsx
│   │   │   │   │   ├── candidates-screen.tsx
│   │   │   │   │   ├── chatbot-screen.tsx
│   │   │   │   │   ├── clearance-dashboard-screen.tsx
│   │   │   │   │   ├── cost-centre-screen.tsx
│   │   │   │   │   ├── data-retention-screen.tsx
│   │   │   │   │   ├── delegate-screen.tsx
│   │   │   │   │   ├── department-screen.tsx
│   │   │   │   │   ├── designation-screen.tsx
│   │   │   │   │   ├── disciplinary-screen.tsx
│   │   │   │   │   ├── employee-detail-screen.tsx
│   │   │   │   │   ├── employee-directory-screen.tsx
│   │   │   │   │   ├── employee-salary-screen.tsx
│   │   │   │   │   ├── employee-type-screen.tsx
│   │   │   │   │   ├── esign-screen.tsx
│   │   │   │   │   ├── ess-config-screen.tsx
│   │   │   │   │   ├── exit-request-screen.tsx
│   │   │   │   │   ├── expenses-screen.tsx
│   │   │   │   │   ├── feedback-360-screen.tsx
│   │   │   │   │   ├── fnf-settlement-screen.tsx
│   │   │   │   │   ├── form16-screen.tsx
│   │   │   │   │   ├── goals-screen.tsx
│   │   │   │   │   ├── grade-screen.tsx
│   │   │   │   │   ├── grievances-screen.tsx
│   │   │   │   │   ├── holiday-screen.tsx
│   │   │   │   │   ├── hr-letters-screen.tsx
│   │   │   │   │   ├── it-declaration-screen.tsx
│   │   │   │   │   ├── leave-balance-screen.tsx
│   │   │   │   │   ├── leave-policy-screen.tsx
│   │   │   │   │   ├── leave-request-screen.tsx
│   │   │   │   │   ├── leave-type-screen.tsx
│   │   │   │   │   ├── loan-policy-screen.tsx
│   │   │   │   │   ├── loan-screen.tsx
│   │   │   │   │   ├── my-attendance-screen.tsx
│   │   │   │   │   ├── my-leave-screen.tsx
│   │   │   │   │   ├── my-payslips-screen.tsx
│   │   │   │   │   ├── my-profile-screen.tsx
│   │   │   │   │   ├── notification-rule-screen.tsx
│   │   │   │   │   ├── notification-template-screen.tsx
│   │   │   │   │   ├── onboarding-screen.tsx
│   │   │   │   │   ├── org-chart-screen.tsx
│   │   │   │   │   ├── overtime-rules-screen.tsx
│   │   │   │   │   ├── payroll-report-screen.tsx
│   │   │   │   │   ├── payroll-run-screen.tsx
│   │   │   │   │   ├── payslip-screen.tsx
│   │   │   │   │   ├── performance-dashboard-screen.tsx
│   │   │   │   │   ├── placeholder-screen.tsx
│   │   │   │   │   ├── probation-review-screen.tsx
│   │   │   │   │   ├── production-incentive-screen.tsx
│   │   │   │   │   ├── promotion-screen.tsx
│   │   │   │   │   ├── ratings-screen.tsx
│   │   │   │   │   ├── requisitions-screen.tsx
│   │   │   │   │   ├── roster-screen.tsx
│   │   │   │   │   ├── salary-component-screen.tsx
│   │   │   │   │   ├── salary-hold-screen.tsx
│   │   │   │   │   ├── salary-revision-screen.tsx
│   │   │   │   │   ├── salary-structure-screen.tsx
│   │   │   │   │   ├── shift-check-in-screen.tsx
│   │   │   │   │   ├── shift-rotation-screen.tsx
│   │   │   │   │   ├── skills-screen.tsx
│   │   │   │   │   ├── statutory-config-screen.tsx
│   │   │   │   │   ├── statutory-filing-screen.tsx
│   │   │   │   │   ├── succession-screen.tsx
│   │   │   │   │   ├── tax-config-screen.tsx
│   │   │   │   │   ├── team-view-screen.tsx
│   │   │   │   │   ├── training-nominations-screen.tsx
│   │   │   │   │   ├── training-screen.tsx
│   │   │   │   │   ├── transfer-screen.tsx
│   │   │   │   │   └── travel-advance-screen.tsx
│   │   │   │   ├── inventory-screen.tsx
│   │   │   │   ├── iot-reason-management-screen.tsx
│   │   │   │   ├── location-management-screen.tsx
│   │   │   │   ├── maintenance-screen.tsx
│   │   │   │   ├── module-catalogue-screen.tsx
│   │   │   │   ├── my-invoices-screen.tsx
│   │   │   │   ├── my-payments-screen.tsx
│   │   │   │   ├── no-series-management-screen.tsx
│   │   │   │   ├── production-screen.tsx
│   │   │   │   ├── role-management-screen.tsx
│   │   │   │   ├── shift-management-screen.tsx
│   │   │   │   ├── system-controls-screen.tsx
│   │   │   │   └── user-management-screen.tsx
│   │   │   ├── onboarding
│   │   │   │   └── onboarding-screen.tsx
│   │   │   ├── settings
│   │   │   │   ├── components
│   │   │   │   │   ├── language-item.tsx
│   │   │   │   │   ├── settings-container.tsx
│   │   │   │   │   ├── settings-item.tsx
│   │   │   │   │   └── theme-item.tsx
│   │   │   │   └── settings-screen.tsx
│   │   │   ├── super-admin
│   │   │   │   ├── add-company-screen.tsx
│   │   │   │   ├── api
│   │   │   │   │   ├── __tests__
│   │   │   │   │   │   ├── use-dashboard-queries.test.ts
│   │   │   │   │   │   └── use-tenant-queries.test.ts
│   │   │   │   │   ├── use-audit-queries.ts
│   │   │   │   │   ├── use-dashboard-queries.ts
│   │   │   │   │   ├── use-invoice-queries.ts
│   │   │   │   │   ├── use-payment-queries.ts
│   │   │   │   │   ├── use-subscription-queries.ts
│   │   │   │   │   ├── use-support-mutations.ts
│   │   │   │   │   ├── use-support-queries.ts
│   │   │   │   │   └── use-tenant-queries.ts
│   │   │   │   ├── audit-log-screen.tsx
│   │   │   │   ├── billing-overview-screen.tsx
│   │   │   │   ├── company-detail-edit-modal.tsx
│   │   │   │   ├── company-detail-screen.tsx
│   │   │   │   ├── company-list-screen.tsx
│   │   │   │   ├── dashboard-screen.tsx
│   │   │   │   ├── invoice-detail-screen.tsx
│   │   │   │   ├── invoice-list-screen.tsx
│   │   │   │   ├── module-assignment-screen.tsx
│   │   │   │   ├── more-menu-screen.tsx
│   │   │   │   ├── payment-history-screen.tsx
│   │   │   │   ├── subscription-detail-screen.tsx
│   │   │   │   ├── support
│   │   │   │   │   ├── support-dashboard-screen.tsx
│   │   │   │   │   └── support-ticket-detail-screen.tsx
│   │   │   │   └── tenant-onboarding
│   │   │   │       ├── atoms.tsx
│   │   │   │       ├── constants.ts
│   │   │   │       ├── form-date-picker.tsx
│   │   │   │       ├── index.tsx
│   │   │   │       ├── schemas.ts
│   │   │   │       ├── shared-styles.ts
│   │   │   │       ├── step-indicator.tsx
│   │   │   │       ├── steps
│   │   │   │       │   ├── step01-identity.tsx
│   │   │   │       │   ├── step02-statutory.tsx
│   │   │   │       │   ├── step03-address.tsx
│   │   │   │       │   ├── step04-fiscal.tsx
│   │   │   │       │   ├── step05-preferences.tsx
│   │   │   │       │   ├── step06-endpoint.tsx
│   │   │   │       │   ├── step07-strategy.tsx
│   │   │   │       │   ├── step08-locations.tsx
│   │   │   │       │   ├── step09-per-location-modules.tsx
│   │   │   │       │   ├── step10-per-location-tier.tsx
│   │   │   │       │   ├── step11-contacts.tsx
│   │   │   │       │   ├── step12-shifts.tsx
│   │   │   │       │   ├── step13-no-series.tsx
│   │   │   │       │   ├── step14-iot-reasons.tsx
│   │   │   │       │   ├── step15-controls.tsx
│   │   │   │       │   ├── step16-users.tsx
│   │   │   │       │   └── step17-activation.tsx
│   │   │   │       └── types.ts
│   │   │   └── support
│   │   │       ├── help-support-screen.tsx
│   │   │       └── ticket-chat-screen.tsx
│   │   ├── global.css
│   │   ├── hooks
│   │   │   └── use-ticket-socket.ts
│   │   ├── lib
│   │   │   ├── api
│   │   │   │   ├── __tests__
│   │   │   │   │   ├── auth.test.ts
│   │   │   │   │   ├── client.test.ts
│   │   │   │   │   ├── dashboard.test.ts
│   │   │   │   │   └── tenant.test.ts
│   │   │   │   ├── attendance.ts
│   │   │   │   ├── audit.ts
│   │   │   │   ├── auth.ts
│   │   │   │   ├── biometric.ts
│   │   │   │   ├── bonus-batch.ts
│   │   │   │   ├── chatbot.ts
│   │   │   │   ├── client.tsx
│   │   │   │   ├── company-admin.ts
│   │   │   │   ├── dashboard.ts
│   │   │   │   ├── ess.ts
│   │   │   │   ├── hr.ts
│   │   │   │   ├── index.ts
│   │   │   │   ├── invoice.ts
│   │   │   │   ├── leave.ts
│   │   │   │   ├── offboarding.ts
│   │   │   │   ├── onboarding.ts
│   │   │   │   ├── payment.ts
│   │   │   │   ├── payroll-run.ts
│   │   │   │   ├── payroll.ts
│   │   │   │   ├── performance.ts
│   │   │   │   ├── production-incentive.ts
│   │   │   │   ├── provider.tsx
│   │   │   │   ├── recruitment.ts
│   │   │   │   ├── retention.ts
│   │   │   │   ├── shift-rotation.ts
│   │   │   │   ├── subscription.ts
│   │   │   │   ├── support.ts
│   │   │   │   ├── tenant.ts
│   │   │   │   ├── transfer.ts
│   │   │   │   └── utils.tsx
│   │   │   ├── auth
│   │   │   │   └── utils.tsx
│   │   │   ├── hooks
│   │   │   │   ├── index.tsx
│   │   │   │   ├── use-is-first-time.tsx
│   │   │   │   └── use-selected-theme.tsx
│   │   │   ├── i18n
│   │   │   │   ├── index.tsx
│   │   │   │   ├── react-i18next.d.ts
│   │   │   │   ├── resources.ts
│   │   │   │   ├── types.ts
│   │   │   │   └── utils.tsx
│   │   │   ├── logger.ts
│   │   │   ├── socket.ts
│   │   │   ├── storage.tsx
│   │   │   ├── test-utils.tsx
│   │   │   └── utils.ts
│   │   └── translations
│   │       ├── ar.json
│   │       └── en.json
│   ├── tsconfig.json
│   └── uniwind-types.d.ts
├── project-structure.md
└── web-system-app
    ├── README.md
    ├── cspell.json
    ├── deploy
    │   └── nginx-spa.conf
    ├── dist-electron
    │   ├── main.js
    │   └── preload.mjs
    ├── docs
    │   ├── Mobile_ERP_PRD_Three_Modules.html
    │   ├── Mobile_ERP_PRD_v2.html
    │   └── mobile-erp-v2.html
    ├── electron
    │   ├── main.ts
    │   └── preload.ts
    ├── eslint.config.js
    ├── index.html
    ├── package.json
    ├── pnpm-lock.yaml
    ├── pnpm-workspace.yaml
    ├── postcss.config.js
    ├── public
    │   ├── Logo-Small-Old.png
    │   ├── _redirects
    │   └── vite.svg
    ├── src
    │   ├── App.css
    │   ├── App.tsx
    │   ├── assets
    │   │   ├── logo
    │   │   │   ├── Avy-ERP-Logo.png
    │   │   │   ├── Company-Logo-WithBG.png
    │   │   │   └── Company-Logo.png
    │   │   └── react.svg
    │   ├── components
    │   │   └── ui
    │   │       ├── CustomLoader.tsx
    │   │       ├── DataTable.tsx
    │   │       ├── EmptyState.tsx
    │   │       ├── GlassButton.tsx
    │   │       ├── KpiCard.tsx
    │   │       ├── Modal.tsx
    │   │       ├── PhoneInput.tsx
    │   │       ├── SearchableSelect.tsx
    │   │       └── Skeleton.tsx
    │   ├── features
    │   │   ├── auth
    │   │   │   ├── AuthFlowAside.tsx
    │   │   │   ├── ForgotPasswordScreen.tsx
    │   │   │   ├── LandingScreen.tsx
    │   │   │   ├── LoginScreen.tsx
    │   │   │   ├── ResetPasswordScreen.tsx
    │   │   │   └── VerifyResetCodeScreen.tsx
    │   │   ├── company-admin
    │   │   │   ├── BillingDashboardScreen.tsx
    │   │   │   ├── CompanyAdminDashboard.tsx
    │   │   │   ├── CompanyProfileScreen.tsx
    │   │   │   ├── CompanySettingsScreen.tsx
    │   │   │   ├── ContactManagementScreen.tsx
    │   │   │   ├── FeatureToggleScreen.tsx
    │   │   │   ├── IOTReasonManagementScreen.tsx
    │   │   │   ├── LocationManagementScreen.tsx
    │   │   │   ├── MyInvoicesScreen.tsx
    │   │   │   ├── MyPaymentsScreen.tsx
    │   │   │   ├── NoSeriesManagementScreen.tsx
    │   │   │   ├── RoleManagementScreen.tsx
    │   │   │   ├── ShiftManagementScreen.tsx
    │   │   │   ├── SystemControlsScreen.tsx
    │   │   │   ├── UserManagementScreen.tsx
    │   │   │   ├── api
    │   │   │   │   ├── index.ts
    │   │   │   │   ├── use-attendance-mutations.ts
    │   │   │   │   ├── use-attendance-queries.ts
    │   │   │   │   ├── use-biometric-mutations.ts
    │   │   │   │   ├── use-biometric-queries.ts
    │   │   │   │   ├── use-bonus-batch-mutations.ts
    │   │   │   │   ├── use-bonus-batch-queries.ts
    │   │   │   │   ├── use-chatbot-mutations.ts
    │   │   │   │   ├── use-chatbot-queries.ts
    │   │   │   │   ├── use-company-admin-mutations.ts
    │   │   │   │   ├── use-company-admin-queries.ts
    │   │   │   │   ├── use-ess-mutations.ts
    │   │   │   │   ├── use-ess-queries.ts
    │   │   │   │   ├── use-hr-mutations.ts
    │   │   │   │   ├── use-hr-queries.ts
    │   │   │   │   ├── use-leave-mutations.ts
    │   │   │   │   ├── use-leave-queries.ts
    │   │   │   │   ├── use-offboarding-mutations.ts
    │   │   │   │   ├── use-offboarding-queries.ts
    │   │   │   │   ├── use-onboarding-mutations.ts
    │   │   │   │   ├── use-onboarding-queries.ts
    │   │   │   │   ├── use-payroll-mutations.ts
    │   │   │   │   ├── use-payroll-queries.ts
    │   │   │   │   ├── use-payroll-run-mutations.ts
    │   │   │   │   ├── use-payroll-run-queries.ts
    │   │   │   │   ├── use-performance-mutations.ts
    │   │   │   │   ├── use-performance-queries.ts
    │   │   │   │   ├── use-production-incentive-mutations.ts
    │   │   │   │   ├── use-production-incentive-queries.ts
    │   │   │   │   ├── use-recruitment-mutations.ts
    │   │   │   │   ├── use-recruitment-queries.ts
    │   │   │   │   ├── use-retention-mutations.ts
    │   │   │   │   ├── use-retention-queries.ts
    │   │   │   │   ├── use-shift-rotation-mutations.ts
    │   │   │   │   ├── use-shift-rotation-queries.ts
    │   │   │   │   ├── use-transfer-mutations.ts
    │   │   │   │   └── use-transfer-queries.ts
    │   │   │   └── hr
    │   │   │       ├── AppraisalCycleScreen.tsx
    │   │   │       ├── ApprovalRequestScreen.tsx
    │   │   │       ├── ApprovalWorkflowScreen.tsx
    │   │   │       ├── AssetManagementScreen.tsx
    │   │   │       ├── AttendanceDashboardScreen.tsx
    │   │   │       ├── AttendanceOverrideScreen.tsx
    │   │   │       ├── AttendanceRulesScreen.tsx
    │   │   │       ├── BankConfigScreen.tsx
    │   │   │       ├── BiometricDeviceScreen.tsx
    │   │   │       ├── BonusBatchScreen.tsx
    │   │   │       ├── CandidateScreen.tsx
    │   │   │       ├── ChatbotScreen.tsx
    │   │   │       ├── ClearanceDashboardScreen.tsx
    │   │   │       ├── CostCentreScreen.tsx
    │   │   │       ├── DataRetentionScreen.tsx
    │   │   │       ├── DelegateScreen.tsx
    │   │   │       ├── DepartmentScreen.tsx
    │   │   │       ├── DesignationScreen.tsx
    │   │   │       ├── DisciplinaryScreen.tsx
    │   │   │       ├── ESignScreen.tsx
    │   │   │       ├── EmployeeDirectoryScreen.tsx
    │   │   │       ├── EmployeeProfileScreen.tsx
    │   │   │       ├── EmployeeSalaryScreen.tsx
    │   │   │       ├── EmployeeTypeScreen.tsx
    │   │   │       ├── EssConfigScreen.tsx
    │   │   │       ├── ExitRequestScreen.tsx
    │   │   │       ├── ExpenseClaimScreen.tsx
    │   │   │       ├── Feedback360Screen.tsx
    │   │   │       ├── FnFSettlementScreen.tsx
    │   │   │       ├── Form16Screen.tsx
    │   │   │       ├── GoalScreen.tsx
    │   │   │       ├── GradeScreen.tsx
    │   │   │       ├── GrievanceScreen.tsx
    │   │   │       ├── HRLetterScreen.tsx
    │   │   │       ├── HolidayScreen.tsx
    │   │   │       ├── ITDeclarationScreen.tsx
    │   │   │       ├── LeaveBalanceScreen.tsx
    │   │   │       ├── LeavePolicyScreen.tsx
    │   │   │       ├── LeaveRequestScreen.tsx
    │   │   │       ├── LeaveTypeScreen.tsx
    │   │   │       ├── LoanPolicyScreen.tsx
    │   │   │       ├── LoanScreen.tsx
    │   │   │       ├── MyAttendanceScreen.tsx
    │   │   │       ├── MyLeaveScreen.tsx
    │   │   │       ├── MyPayslipsScreen.tsx
    │   │   │       ├── MyProfileScreen.tsx
    │   │   │       ├── NotificationRuleScreen.tsx
    │   │   │       ├── NotificationTemplateScreen.tsx
    │   │   │       ├── OnboardingScreen.tsx
    │   │   │       ├── OrgChartScreen.tsx
    │   │   │       ├── OvertimeRulesScreen.tsx
    │   │   │       ├── PayrollReportScreen.tsx
    │   │   │       ├── PayrollRunScreen.tsx
    │   │   │       ├── PayslipScreen.tsx
    │   │   │       ├── PerformanceDashboardScreen.tsx
    │   │   │       ├── ProbationReviewScreen.tsx
    │   │   │       ├── ProductionIncentiveScreen.tsx
    │   │   │       ├── PromotionScreen.tsx
    │   │   │       ├── RatingsScreen.tsx
    │   │   │       ├── RequisitionScreen.tsx
    │   │   │       ├── RosterScreen.tsx
    │   │   │       ├── SalaryComponentScreen.tsx
    │   │   │       ├── SalaryHoldScreen.tsx
    │   │   │       ├── SalaryRevisionScreen.tsx
    │   │   │       ├── SalaryStructureScreen.tsx
    │   │   │       ├── ShiftCheckInScreen.tsx
    │   │   │       ├── ShiftRotationScreen.tsx
    │   │   │       ├── SkillScreen.tsx
    │   │   │       ├── StatutoryConfigScreen.tsx
    │   │   │       ├── StatutoryFilingScreen.tsx
    │   │   │       ├── SuccessionScreen.tsx
    │   │   │       ├── TaxConfigScreen.tsx
    │   │   │       ├── TeamViewScreen.tsx
    │   │   │       ├── TrainingCatalogueScreen.tsx
    │   │   │       ├── TrainingNominationScreen.tsx
    │   │   │       ├── TransferScreen.tsx
    │   │   │       └── TravelAdvanceScreen.tsx
    │   │   ├── help
    │   │   │   └── HelpSupportScreen.tsx
    │   │   ├── inventory
    │   │   │   └── InventoryScreen.tsx
    │   │   ├── maintenance
    │   │   │   ├── MachineRegistryScreen.tsx
    │   │   │   ├── MaintenanceScreen.tsx
    │   │   │   └── WorkOrdersScreen.tsx
    │   │   ├── production
    │   │   │   └── ProductionScreen.tsx
    │   │   ├── shared
    │   │   │   └── NoPermissionScreen.tsx
    │   │   ├── super-admin
    │   │   │   ├── AddCompanyWizard.tsx
    │   │   │   ├── AuditLogScreen.tsx
    │   │   │   ├── BillingOverviewScreen.tsx
    │   │   │   ├── CompanyDetailEditModal.tsx
    │   │   │   ├── CompanyDetailScreen.tsx
    │   │   │   ├── CompanyListScreen.tsx
    │   │   │   ├── DashboardScreen.tsx
    │   │   │   ├── InvoiceDetailScreen.tsx
    │   │   │   ├── InvoiceListScreen.tsx
    │   │   │   ├── ModuleAssignmentScreen.tsx
    │   │   │   ├── ModuleCatalogueScreen.tsx
    │   │   │   ├── PaymentHistoryScreen.tsx
    │   │   │   ├── PlatformMonitorScreen.tsx
    │   │   │   ├── SubscriptionDetailScreen.tsx
    │   │   │   ├── api
    │   │   │   │   ├── __tests__
    │   │   │   │   │   ├── use-dashboard-queries.test.ts
    │   │   │   │   │   └── use-tenant-queries.test.ts
    │   │   │   │   ├── use-audit-queries.ts
    │   │   │   │   ├── use-dashboard-queries.ts
    │   │   │   │   ├── use-invoice-queries.ts
    │   │   │   │   ├── use-payment-queries.ts
    │   │   │   │   ├── use-subscription-queries.ts
    │   │   │   │   ├── use-support-mutations.ts
    │   │   │   │   ├── use-support-queries.ts
    │   │   │   │   └── use-tenant-queries.ts
    │   │   │   ├── support
    │   │   │   │   ├── SupportDashboardScreen.tsx
    │   │   │   │   └── SupportTicketDetailScreen.tsx
    │   │   │   └── tenant-onboarding
    │   │   │       ├── TenantOnboardingWizard.tsx
    │   │   │       ├── atoms.tsx
    │   │   │       ├── change_required.md
    │   │   │       ├── constants.ts
    │   │   │       ├── index.ts
    │   │   │       ├── steps
    │   │   │       │   ├── Step01Identity.tsx
    │   │   │       │   ├── Step02Statutory.tsx
    │   │   │       │   ├── Step03Address.tsx
    │   │   │       │   ├── Step04Fiscal.tsx
    │   │   │       │   ├── Step05Preferences.tsx
    │   │   │       │   ├── Step06Endpoint.tsx
    │   │   │       │   ├── Step07Strategy.tsx
    │   │   │       │   ├── Step08Locations.tsx
    │   │   │       │   ├── Step09PerLocationModules.tsx
    │   │   │       │   ├── Step10PerLocationTier.tsx
    │   │   │       │   ├── Step11Contacts.tsx
    │   │   │       │   ├── Step12Shifts.tsx
    │   │   │       │   ├── Step13NoSeries.tsx
    │   │   │       │   ├── Step14IOTReasons.tsx
    │   │   │       │   ├── Step15Controls.tsx
    │   │   │       │   ├── Step16Users.tsx
    │   │   │       │   └── Step17Activation.tsx
    │   │   │       ├── store.ts
    │   │   │       └── types.ts
    │   │   └── support
    │   │       └── TicketChatScreen.tsx
    │   ├── hooks
    │   │   └── useTicketSocket.ts
    │   ├── index.css
    │   ├── layouts
    │   │   ├── AuthLayout.tsx
    │   │   ├── DashboardLayout.tsx
    │   │   ├── Sidebar.tsx
    │   │   └── TopBar.tsx
    │   ├── lib
    │   │   ├── api
    │   │   │   ├── __tests__
    │   │   │   │   ├── auth.test.ts
    │   │   │   │   ├── client.proactive-refresh.test.ts
    │   │   │   │   ├── client.test.ts
    │   │   │   │   ├── dashboard.test.ts
    │   │   │   │   ├── tenant.test.ts
    │   │   │   │   └── use-auth-mutations.test.ts
    │   │   │   ├── attendance.ts
    │   │   │   ├── audit.ts
    │   │   │   ├── auth.ts
    │   │   │   ├── biometric.ts
    │   │   │   ├── bonus-batch.ts
    │   │   │   ├── chatbot.ts
    │   │   │   ├── client.ts
    │   │   │   ├── company-admin.ts
    │   │   │   ├── dashboard.ts
    │   │   │   ├── ess.ts
    │   │   │   ├── hr.ts
    │   │   │   ├── invoice.ts
    │   │   │   ├── leave.ts
    │   │   │   ├── offboarding.ts
    │   │   │   ├── onboarding.ts
    │   │   │   ├── payment.ts
    │   │   │   ├── payroll-run.ts
    │   │   │   ├── payroll.ts
    │   │   │   ├── performance.ts
    │   │   │   ├── production-incentive.ts
    │   │   │   ├── provider.tsx
    │   │   │   ├── recruitment.ts
    │   │   │   ├── retention.ts
    │   │   │   ├── shift-rotation.ts
    │   │   │   ├── subscription.ts
    │   │   │   ├── support.ts
    │   │   │   ├── tenant.ts
    │   │   │   ├── transfer.ts
    │   │   │   └── use-auth-mutations.ts
    │   │   ├── socket.ts
    │   │   ├── toast.tsx
    │   │   └── utils.ts
    │   ├── main.tsx
    │   ├── modules
    │   │   ├── dashboard
    │   │   │   └── Dashboard.tsx
    │   │   ├── hr
    │   │   │   ├── AttendanceTrack.tsx
    │   │   │   ├── EmployeeDirectory.tsx
    │   │   │   ├── HRModule.tsx
    │   │   │   └── PayrollConfig.tsx
    │   │   ├── machine
    │   │   │   ├── MachineModule.tsx
    │   │   │   └── MachineRegistry.tsx
    │   │   └── visitor
    │   │       ├── VisitorBoard.tsx
    │   │       └── VisitorModule.tsx
    │   ├── store
    │   │   ├── __tests__
    │   │   │   ├── useAuthStore.crossTabSync.test.ts
    │   │   │   └── useAuthStore.test.ts
    │   │   ├── hrStore.ts
    │   │   ├── machineStore.ts
    │   │   ├── useAuthStore.ts
    │   │   ├── useThemeStore.ts
    │   │   └── visitorStore.ts
    │   └── test
    │       └── setup.ts
    ├── tailwind.config.js
    ├── tsconfig.app.json
    ├── tsconfig.json
    ├── tsconfig.node.json
    ├── vercel.json
    ├── vite.config.ts
    └── vitest.config.ts

186 directories, 1068 files
