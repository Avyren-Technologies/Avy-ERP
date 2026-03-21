.
├── avy-erp-backend
│   ├── package-lock.json
│   ├── package.json
│   ├── prisma
│   │   └── schema.prisma
│   ├── src
│   │   ├── app
│   │   │   ├── app.ts
│   │   │   ├── routes.ts
│   │   │   └── server.ts
│   │   ├── config
│   │   │   ├── database.ts
│   │   │   ├── env.ts
│   │   │   ├── logger.ts
│   │   │   └── redis.ts
│   │   ├── core
│   │   │   ├── auth
│   │   │   │   ├── auth.controller.ts
│   │   │   │   ├── auth.routes.ts
│   │   │   │   ├── auth.service.ts
│   │   │   │   └── auth.types.ts
│   │   │   ├── billing
│   │   │   │   └── billing.routes.ts
│   │   │   ├── company
│   │   │   │   └── company.routes.ts
│   │   │   ├── feature-toggle
│   │   │   │   └── feature-toggle.routes.ts
│   │   │   ├── rbac
│   │   │   │   └── rbac.routes.ts
│   │   │   └── tenant
│   │   │       ├── tenant.controller.ts
│   │   │       ├── tenant.routes.ts
│   │   │       └── tenant.service.ts
│   │   ├── infrastructure
│   │   │   ├── cache
│   │   │   │   └── cache.service.ts
│   │   │   ├── database
│   │   │   │   └── connection.ts
│   │   │   ├── queue
│   │   │   │   └── report.queue.ts
│   │   │   └── storage
│   │   │       └── storage.service.ts
│   │   ├── middleware
│   │   │   ├── auth.middleware.ts
│   │   │   ├── error.middleware.ts
│   │   │   ├── logging.middleware.ts
│   │   │   └── tenant.middleware.ts
│   │   ├── modules
│   │   │   ├── hr
│   │   │   │   └── routes.ts
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
│   │   │   │   └── index.ts
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
│   │       ├── notification.worker.ts
│   │       └── report.worker.ts
│   └── tsconfig.json
├── docs
│   ├── Company Profile.html
│   ├── Mobile_ERP_PRD_Three_Modules.html
│   ├── company-master.html
│   └── duplicates
│       └── tenant-onboarding-screen.tsx
├── mobile-app
│   ├── LICENSE
│   ├── __mocks__
│   │   ├── @gorhom
│   │   │   └── bottom-sheet.ts
│   │   ├── expo-localization.ts
│   │   ├── moti.ts
│   │   ├── react-native-gesture-handler.ts
│   │   └── react-native-keyboard-controller.ts
│   ├── app.config.ts
│   ├── assets
│   ├── babel.config.js
│   ├── cli
│   │   ├── clone-repo.js
│   │   ├── index.js
│   │   ├── package.json
│   │   ├── pnpm-lock.yaml
│   │   ├── setup-project.js
│   │   └── utils.js
│   ├── commitlint.config.js
│   ├── docs
│   │   ├── astro.config.mjs
│   │   ├── package.json
│   │   ├── pnpm-lock.yaml
│   │   ├── public
│   │   │   ├── _redirects
│   │   │   └── reviews
│   │   ├── src
│   │   │   ├── assets
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
│   │   │   │       ├── ci-cd
│   │   │   │       │   ├── app-releasing-process.mdx
│   │   │   │       │   ├── overview.mdx
│   │   │   │       │   └── workflows-references.mdx
│   │   │   │       ├── getting-started
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
│   │   │   │       ├── index.mdx
│   │   │   │       ├── recipes
│   │   │   │       │   └── sentry-setup.mdx
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
│   │   │   │   ├── billing.tsx
│   │   │   │   ├── companies.tsx
│   │   │   │   ├── index.tsx
│   │   │   │   ├── more.tsx
│   │   │   │   ├── settings.tsx
│   │   │   │   └── tenant
│   │   │   │       ├── [id].tsx
│   │   │   │       ├── add-company.tsx
│   │   │   │       └── module-assignment.tsx
│   │   │   ├── +html.tsx
│   │   │   ├── [...messing].tsx
│   │   │   ├── _layout.tsx
│   │   │   ├── login.tsx
│   │   │   └── onboarding.tsx
│   │   ├── components
│   │   │   └── ui
│   │   │       ├── button.test.tsx
│   │   │       ├── button.tsx
│   │   │       ├── checkbox.test.tsx
│   │   │       ├── checkbox.tsx
│   │   │       ├── colors.js
│   │   │       ├── confirm-modal.tsx
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
│   │   ├── constants
│   │   ├── features
│   │   │   ├── auth
│   │   │   │   ├── login-screen.tsx
│   │   │   │   └── use-auth-store.ts
│   │   │   ├── onboarding
│   │   │   │   └── onboarding-screen.tsx
│   │   │   ├── settings
│   │   │   │   ├── components
│   │   │   │   │   ├── language-item.tsx
│   │   │   │   │   ├── settings-container.tsx
│   │   │   │   │   ├── settings-item.tsx
│   │   │   │   │   └── theme-item.tsx
│   │   │   │   └── settings-screen.tsx
│   │   │   └── super-admin
│   │   │       ├── add-company-screen.tsx
│   │   │       ├── billing-overview-screen.tsx
│   │   │       ├── company-detail-screen.tsx
│   │   │       ├── company-list-screen.tsx
│   │   │       ├── dashboard-screen.tsx
│   │   │       ├── module-assignment-screen.tsx
│   │   │       ├── more-menu-screen.tsx
│   │   │       └── tenant-onboarding
│   │   │           ├── atoms.tsx
│   │   │           ├── constants.ts
│   │   │           ├── index.tsx
│   │   │           ├── schemas.ts
│   │   │           ├── shared-styles.ts
│   │   │           ├── step-indicator.tsx
│   │   │           ├── steps
│   │   │           │   ├── step01-identity.tsx
│   │   │           │   ├── step02-statutory.tsx
│   │   │           │   ├── step03-address.tsx
│   │   │           │   ├── step04-fiscal.tsx
│   │   │           │   ├── step05-preferences.tsx
│   │   │           │   ├── step06-contacts.tsx
│   │   │           │   ├── step06-endpoint.tsx
│   │   │           │   ├── step07-modules.tsx
│   │   │           │   ├── step07-plants-branches.tsx
│   │   │           │   ├── step08-shifts.tsx
│   │   │           │   ├── step08-user-tier.tsx
│   │   │           │   ├── step09-no-series.tsx
│   │   │           │   ├── step10-iot-reasons.tsx
│   │   │           │   ├── step11-controls.tsx
│   │   │           │   ├── step12-users.tsx
│   │   │           │   └── step13-activation.tsx
│   │   │           └── types.ts
│   │   ├── global.css
│   │   ├── lib
│   │   │   ├── api
│   │   │   │   ├── client.tsx
│   │   │   │   ├── index.ts
│   │   │   │   ├── provider.tsx
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
│   │   │   ├── storage.tsx
│   │   │   ├── test-utils.tsx
│   │   │   └── utils.ts
│   │   └── translations
│   │       ├── ar.json
│   │       └── en.json
│   ├── tsconfig.json
│   └── uniwind-types.d.ts
└── web-system-app
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
    ├── package-lock.json
    ├── package.json
    ├── postcss.config.js
    ├── public
    ├── src
    │   ├── App.css
    │   ├── App.tsx
    │   ├── assets
    │   ├── components
    │   │   └── ui
    │   │       ├── CustomLoader.tsx
    │   │       ├── DataTable.tsx
    │   │       ├── GlassButton.tsx
    │   │       ├── KpiCard.tsx
    │   │       └── Modal.tsx
    │   ├── features
    │   │   ├── auth
    │   │   │   ├── LandingScreen.tsx
    │   │   │   └── LoginScreen.tsx
    │   │   └── super-admin
    │   │       ├── AddCompanyWizard.tsx
    │   │       ├── BillingOverviewScreen.tsx
    │   │       ├── CompanyDetailScreen.tsx
    │   │       ├── CompanyListScreen.tsx
    │   │       ├── DashboardScreen.tsx
    │   │       ├── ModuleAssignmentScreen.tsx
    │   │       ├── ModuleCatalogueScreen.tsx
    │   │       ├── PlatformMonitorScreen.tsx
    │   │       └── tenant-onboarding
    │   │           ├── TenantOnboardingWizard.tsx
    │   │           ├── atoms.tsx
    │   │           ├── constants.ts
    │   │           ├── index.ts
    │   │           ├── steps
    │   │           │   ├── Step01Identity.tsx
    │   │           │   ├── Step02Statutory.tsx
    │   │           │   ├── Step03Address.tsx
    │   │           │   ├── Step04Fiscal.tsx
    │   │           │   ├── Step05Preferences.tsx
    │   │           │   ├── Step06Endpoint.tsx
    │   │           │   ├── Step07Modules.tsx
    │   │           │   ├── Step08UserTier.tsx
    │   │           │   ├── Step09Contacts.tsx
    │   │           │   ├── Step10Plants.tsx
    │   │           │   ├── Step11Shifts.tsx
    │   │           │   ├── Step12NoSeries.tsx
    │   │           │   ├── Step13IOTReasons.tsx
    │   │           │   ├── Step14Controls.tsx
    │   │           │   └── Step15Activation.tsx
    │   │           ├── store.ts
    │   │           └── types.ts
    │   ├── index.css
    │   ├── layouts
    │   │   ├── AuthLayout.tsx
    │   │   ├── DashboardLayout.tsx
    │   │   ├── Sidebar.tsx
    │   │   └── TopBar.tsx
    │   ├── lib
    │   │   ├── api
    │   │   │   └── client.ts
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
    │   └── store
    │       ├── hrStore.ts
    │       ├── machineStore.ts
    │       ├── useAuthStore.ts
    │       ├── useThemeStore.ts
    │       └── visitorStore.ts
    ├── tailwind.config.js
    ├── tsconfig.app.json
    ├── tsconfig.json
    ├── tsconfig.node.json
    └── vite.config.ts

104 directories, 327 files
