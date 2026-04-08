I will give you the files that I have last updated from last 2 days please give me a complete chanelog based on that:
Backend changes:
```
root@a:/home/a/Documents/Avyren-Technologies/Avy-ERP-Backend# git pull origin main
From https://github.com/Avyren-Technologies/Avy-ERP-Backend
 * branch            main       -> FETCH_HEAD
Updating 3a2fee1..385b7fc
Fast-forward
 package.json                                                   |    1 +
 pnpm-lock.yaml                                                 |  911 ++++++++++++++++++++++++++++++++++++++++
 prisma/migrations/20260406150732_training_module/migration.sql |  661 +++++++++++++++++++++++++++++
 prisma/migrations/20260407044830_geo_fencing/migration.sql     |   42 ++
 prisma/modules/company-admin/geofence.prisma                   |   33 ++
 prisma/modules/company-admin/locations.prisma                  |    3 +
 prisma/modules/company-admin/settings.prisma                   |    4 +-
 prisma/modules/hrms/employee.prisma                            |    9 +-
 prisma/modules/hrms/org-structure.prisma                       |    3 +
 prisma/modules/hrms/recruitment.prisma                         |  172 ++++++++
 prisma/modules/hrms/training.prisma                            |  266 +++++++++++-
 prisma/modules/platform/analytics.prisma                       |   18 +
 prisma/modules/platform/audit.prisma                           |   27 +-
 prisma/modules/platform/auth.prisma                            |    4 +
 prisma/modules/platform/notifications.prisma                   |   40 ++
 prisma/modules/platform/tenant.prisma                          |   33 +-
 prisma/schema.prisma                                           |  623 ++++++++++++++++++++++++++--
 src/app/routes.ts                                              |    4 +
 src/app/server.ts                                              |    8 +
 src/core/audit/__tests__/audit.service.test.ts                 |   22 +-
 src/core/audit/audit.controller.ts                             |    6 +-
 src/core/audit/audit.service.ts                                |   24 +-
 src/core/auth/auth.service.ts                                  |    1 +
 src/core/company-admin/company-admin.controller.ts             |   12 +-
 src/core/company-admin/company-admin.routes.ts                 |    9 +-
 src/core/company-admin/company-admin.service.ts                |   17 +-
 src/core/company-admin/geofence.controller.ts                  |   58 +++
 src/core/company-admin/geofence.service.ts                     |  204 +++++++++
 src/core/company-admin/geofence.validators.ts                  |   12 +
 src/core/dashboard/dashboard.service.ts                        |   16 +-
 src/core/notifications/notification.controller.ts              |   88 ++++
 src/core/notifications/notification.routes.ts                  |   16 +
 src/core/notifications/notification.service.ts                 |  185 +++++++++
 src/core/rbac/rbac.service.ts                                  |   12 +
 src/core/tenant/bulk-onboard.constants.ts                      |  193 +++++++++
 src/core/tenant/bulk-onboard.controller.ts                     |   56 +++
 src/core/tenant/bulk-onboard.service.ts                        | 1152 +++++++++++++++++++++++++++++++++++++++++++++++++++
 src/core/tenant/bulk-onboard.validators.ts                     |  260 ++++++++++++
 src/core/tenant/tenant.routes.ts                               |    6 +
 src/core/tenant/tenant.service.ts                              |   22 +-
 src/modules/hr/advanced/advanced.controller.ts                 |   74 +++-
 src/modules/hr/advanced/advanced.routes.ts                     |  125 ++++--
 src/modules/hr/advanced/advanced.service.ts                    |  683 +++++++++++++++++++++++++++---
 src/modules/hr/advanced/advanced.validators.ts                 |   20 +-
 src/modules/hr/advanced/candidate-profile.controller.ts        |  131 ++++++
 src/modules/hr/advanced/candidate-profile.routes.ts            |   30 ++
 src/modules/hr/advanced/candidate-profile.service.ts           |  181 ++++++++
 src/modules/hr/advanced/candidate-profile.validators.ts        |   43 ++
 src/modules/hr/advanced/evaluation.controller.ts               |   42 ++
 src/modules/hr/advanced/evaluation.routes.ts                   |   13 +
 src/modules/hr/advanced/evaluation.service.ts                  |   72 ++++
 src/modules/hr/advanced/evaluation.validators.ts               |   10 +
 src/modules/hr/advanced/offer.controller.ts                    |   79 ++++
 src/modules/hr/advanced/offer.routes.ts                        |   14 +
 src/modules/hr/advanced/offer.service.ts                       |  302 ++++++++++++++
 src/modules/hr/advanced/offer.validators.ts                    |   26 ++
 src/modules/hr/advanced/trainer.controller.ts                  |   65 +++
 src/modules/hr/advanced/trainer.routes.ts                      |   13 +
 src/modules/hr/advanced/trainer.service.ts                     |  177 ++++++++
 src/modules/hr/advanced/trainer.validators.ts                  |   26 ++
 src/modules/hr/advanced/training-attendance.controller.ts      |   76 ++++
 src/modules/hr/advanced/training-attendance.routes.ts          |   15 +
 src/modules/hr/advanced/training-attendance.service.ts         |  221 ++++++++++
 src/modules/hr/advanced/training-attendance.validators.ts      |   23 +
 src/modules/hr/advanced/training-budget.controller.ts          |   67 +++
 src/modules/hr/advanced/training-budget.routes.ts              |   15 +
 src/modules/hr/advanced/training-budget.service.ts             |  203 +++++++++
 src/modules/hr/advanced/training-budget.validators.ts          |   11 +
 src/modules/hr/advanced/training-evaluation.controller.ts      |   88 ++++
 src/modules/hr/advanced/training-evaluation.routes.ts          |   13 +
 src/modules/hr/advanced/training-evaluation.service.ts         |  288 +++++++++++++
 src/modules/hr/advanced/training-evaluation.validators.ts      |   32 ++
 src/modules/hr/advanced/training-material.controller.ts        |   48 +++
 src/modules/hr/advanced/training-material.routes.ts            |   15 +
 src/modules/hr/advanced/training-material.service.ts           |   81 ++++
 src/modules/hr/advanced/training-material.validators.ts        |   12 +
 src/modules/hr/advanced/training-program.controller.ts         |  143 +++++++
 src/modules/hr/advanced/training-program.routes.ts             |   17 +
 src/modules/hr/advanced/training-program.service.ts            |  422 +++++++++++++++++++
 src/modules/hr/advanced/training-program.validators.ts         |   23 +
 src/modules/hr/advanced/training-session.controller.ts         |   79 ++++
 src/modules/hr/advanced/training-session.routes.ts             |   14 +
 src/modules/hr/advanced/training-session.service.ts            |  348 ++++++++++++++++
 src/modules/hr/advanced/training-session.validators.ts         |   31 ++
 src/modules/hr/analytics/analytics.controller.ts               |   64 ++-
 src/modules/hr/analytics/analytics.routes.ts                   |   20 +-
 src/modules/hr/analytics/analytics.types.ts                    |    2 +-
 src/modules/hr/analytics/insights/insights-engine.service.ts   |    1 +
 src/modules/hr/analytics/services/analytics.service.ts         |   52 ++-
 src/modules/hr/attendance/attendance.service.ts                |    6 +-
 src/modules/hr/attendance/attendance.validators.ts             |   29 +-
 src/modules/hr/employee/bulk-import.controller.ts              |   63 +++
 src/modules/hr/employee/bulk-import.service.ts                 |  772 ++++++++++++++++++++++++++++++++++
 src/modules/hr/employee/bulk-import.validators.ts              |  186 +++++++++
 src/modules/hr/employee/employee.routes.ts                     |    6 +
 src/modules/hr/employee/employee.service.ts                    |   41 +-
 src/modules/hr/employee/employee.validators.ts                 |    1 +
 src/modules/hr/ess/ess.controller.ts                           |  178 ++++++--
 src/modules/hr/ess/ess.routes.ts                               |    4 +
 src/modules/hr/ess/ess.service.ts                              |  323 +++++++++------
 src/modules/hr/leave/leave.service.ts                          |    6 +-
 src/modules/hr/offboarding/offboarding.service.ts              |    6 +-
 src/modules/hr/org-structure/org-structure.service.ts          |    6 +-
 src/modules/hr/payroll-run/payroll-run.service.ts              |    6 +-
 src/modules/hr/payroll/payroll.service.ts                      |    6 +-
 src/modules/hr/performance/performance.service.ts              |    8 +-
 src/modules/hr/transfer/transfer.service.ts                    |    6 +-
 src/shared/constants/linked-screens.ts                         |   29 +-
 src/shared/constants/navigation-manifest.ts                    |   50 ++-
 src/shared/constants/permissions.ts                            |   28 +-
 src/shared/constants/system-defaults.ts                        |    4 +-
 src/shared/events/event-bus.ts                                 |   27 ++
 src/shared/events/hr-events.ts                                 |   26 ++
 src/shared/events/listeners/hr-listeners.ts                    |   91 ++++
 src/shared/utils/audit.ts                                      |  109 +++++
 src/shared/utils/index.ts                                      |    3 +
 src/shared/utils/prisma-helpers.ts                             |   10 +
 src/shared/utils/state-machine.ts                              |   93 +++++
 118 files changed, 11391 insertions(+), 515 deletions(-)
 create mode 100644 prisma/migrations/20260406150732_training_module/migration.sql
 create mode 100644 prisma/migrations/20260407044830_geo_fencing/migration.sql
 create mode 100644 prisma/modules/company-admin/geofence.prisma
 create mode 100644 prisma/modules/platform/analytics.prisma
 create mode 100644 prisma/modules/platform/notifications.prisma
 create mode 100644 src/core/company-admin/geofence.controller.ts
 create mode 100644 src/core/company-admin/geofence.service.ts
 create mode 100644 src/core/company-admin/geofence.validators.ts
 create mode 100644 src/core/notifications/notification.controller.ts
 create mode 100644 src/core/notifications/notification.routes.ts
 create mode 100644 src/core/notifications/notification.service.ts
 create mode 100644 src/core/tenant/bulk-onboard.constants.ts
 create mode 100644 src/core/tenant/bulk-onboard.controller.ts
 create mode 100644 src/core/tenant/bulk-onboard.service.ts
 create mode 100644 src/core/tenant/bulk-onboard.validators.ts
 create mode 100644 src/modules/hr/advanced/candidate-profile.controller.ts
 create mode 100644 src/modules/hr/advanced/candidate-profile.routes.ts
 create mode 100644 src/modules/hr/advanced/candidate-profile.service.ts
 create mode 100644 src/modules/hr/advanced/candidate-profile.validators.ts
 create mode 100644 src/modules/hr/advanced/evaluation.controller.ts
 create mode 100644 src/modules/hr/advanced/evaluation.routes.ts
 create mode 100644 src/modules/hr/advanced/evaluation.service.ts
 create mode 100644 src/modules/hr/advanced/evaluation.validators.ts
 create mode 100644 src/modules/hr/advanced/offer.controller.ts
 create mode 100644 src/modules/hr/advanced/offer.routes.ts
 create mode 100644 src/modules/hr/advanced/offer.service.ts
 create mode 100644 src/modules/hr/advanced/offer.validators.ts
 create mode 100644 src/modules/hr/advanced/trainer.controller.ts
 create mode 100644 src/modules/hr/advanced/trainer.routes.ts
 create mode 100644 src/modules/hr/advanced/trainer.service.ts
 create mode 100644 src/modules/hr/advanced/trainer.validators.ts
 create mode 100644 src/modules/hr/advanced/training-attendance.controller.ts
 create mode 100644 src/modules/hr/advanced/training-attendance.routes.ts
 create mode 100644 src/modules/hr/advanced/training-attendance.service.ts
 create mode 100644 src/modules/hr/advanced/training-attendance.validators.ts
 create mode 100644 src/modules/hr/advanced/training-budget.controller.ts
 create mode 100644 src/modules/hr/advanced/training-budget.routes.ts
 create mode 100644 src/modules/hr/advanced/training-budget.service.ts
 create mode 100644 src/modules/hr/advanced/training-budget.validators.ts
 create mode 100644 src/modules/hr/advanced/training-evaluation.controller.ts
 create mode 100644 src/modules/hr/advanced/training-evaluation.routes.ts
 create mode 100644 src/modules/hr/advanced/training-evaluation.service.ts
 create mode 100644 src/modules/hr/advanced/training-evaluation.validators.ts
 create mode 100644 src/modules/hr/advanced/training-material.controller.ts
 create mode 100644 src/modules/hr/advanced/training-material.routes.ts
 create mode 100644 src/modules/hr/advanced/training-material.service.ts
 create mode 100644 src/modules/hr/advanced/training-material.validators.ts
 create mode 100644 src/modules/hr/advanced/training-program.controller.ts
 create mode 100644 src/modules/hr/advanced/training-program.routes.ts
 create mode 100644 src/modules/hr/advanced/training-program.service.ts
 create mode 100644 src/modules/hr/advanced/training-program.validators.ts
 create mode 100644 src/modules/hr/advanced/training-session.controller.ts
 create mode 100644 src/modules/hr/advanced/training-session.routes.ts
 create mode 100644 src/modules/hr/advanced/training-session.service.ts
 create mode 100644 src/modules/hr/advanced/training-session.validators.ts
 create mode 100644 src/modules/hr/employee/bulk-import.controller.ts
 create mode 100644 src/modules/hr/employee/bulk-import.service.ts
 create mode 100644 src/modules/hr/employee/bulk-import.validators.ts
 create mode 100644 src/shared/events/event-bus.ts
 create mode 100644 src/shared/events/hr-events.ts
 create mode 100644 src/shared/events/listeners/hr-listeners.ts
 create mode 100644 src/shared/utils/audit.ts
 create mode 100644 src/shared/utils/prisma-helpers.ts
 create mode 100644 src/shared/utils/state-machine.ts
root@a:/home/a/Documents/Avyren-Technologies/Avy-ERP-Backend# 
root@a:/home/a/Documents/Avyren-Technologies/Avy-ERP-Backend# git pull origin main
remote: Enumerating objects: 72, done.
remote: Counting objects: 100% (72/72), done.
remote: Compressing objects: 100% (13/13), done.
remote: Total 54 (delta 41), reused 54 (delta 41), pack-reused 0 (from 0)
Unpacking objects: 100% (54/54), 11.74 KiB | 279.00 KiB/s, done.
From https://github.com/Avyren-Technologies/Avy-ERP-Backend
 * branch            main       -> FETCH_HEAD
   385b7fc..6c32fb4  main       -> origin/main
Updating 385b7fc..6c32fb4
Fast-forward
 src/modules/hr/attendance/admin-attendance.controller.ts |  78 +++++++++
 src/modules/hr/attendance/admin-attendance.routes.ts     |  12 ++
 src/modules/hr/attendance/admin-attendance.service.ts    | 547 ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
 src/modules/hr/attendance/admin-attendance.validators.ts |  27 +++
 src/modules/hr/attendance/attendance.routes.ts           |   4 +
 src/shared/constants/navigation-manifest.ts              |   1 +
 src/shared/constants/permissions.ts                      |   8 +
 7 files changed, 677 insertions(+)
 create mode 100644 src/modules/hr/attendance/admin-attendance.controller.ts
 create mode 100644 src/modules/hr/attendance/admin-attendance.routes.ts
 create mode 100644 src/modules/hr/attendance/admin-attendance.service.ts
 create mode 100644 src/modules/hr/attendance/admin-attendance.validators.ts
root@a:/home/a/Documents/Avyren-Technologies/Avy-ERP-Backend# 
```

Web Changes:
```
root@a:/home/a/Documents/Avyren-Technologies/Avy-ERP-Electron-Web# git pull origin main
remote: Enumerating objects: 952, done.
remote: Counting objects: 100% (952/952), done.
remote: Compressing objects: 100% (338/338), done.
remote: Total 823 (delta 668), reused 626 (delta 479), pack-reused 0 (from 0)
Receiving objects: 100% (823/823), 1.66 MiB | 2.28 MiB/s, done.
Resolving deltas: 100% (668/668), completed with 97 local objects.
From https://github.com/Avyren-Technologies/Avy-ERP-Electron-Web
 * branch            main       -> FETCH_HEAD
   987609e..539bc06  main       -> origin/main
Updating 987609e..539bc06
Fast-forward
 .gitignore                                                                    |     3 +
 index.html                                                                    |     1 -
 package-lock.json                                                             | 12685 +++++++++++++++++++++++++++++++++++
 package.json                                                                  |     5 +-
 pnpm-lock.yaml                                                                |   839 ++-
 pnpm-workspace.yaml                                                           |     3 +
 public/firebase-messaging-sw.js                                               |    25 +
 src/App.tsx                                                                   |   456 +-
 src/assets/logo/Avy-ERP-Logo.png                                              |   Bin 389567 -> 0 bytes
 src/assets/logo/Company-Logo-WithBG.png                                       |   Bin 817962 -> 0 bytes
 src/assets/logo/Company-Logo.png                                              |   Bin 155938 -> 23184 bytes
 src/assets/logo/app-logo.png                                                  |   Bin 0 -> 7340 bytes
 src/components/ui/ImageViewer.tsx                                             |   156 +
 src/components/ui/SearchableSelect.tsx                                        |     8 +-
 src/features/auth/LandingScreen.tsx                                           |   248 +-
 src/features/auth/LoginScreen.tsx                                             |   324 +-
 src/features/auth/MfaSetupScreen.tsx                                          |   206 +
 src/features/auth/MfaVerifyScreen.tsx                                         |   188 +
 src/features/auth/ProductShowcaseScreen.tsx                                   |  1587 +++++
 src/features/auth/RegisterCompanyScreen.tsx                                   |   200 +
 src/features/auth/TenantNotFoundScreen.tsx                                    |    90 +
 src/features/company-admin/BillingDashboardScreen.tsx                         |     8 +-
 src/features/company-admin/CompanyProfileScreen.tsx                           |    12 +-
 src/features/company-admin/LocationManagementScreen.tsx                       |    13 +-
 src/features/company-admin/MfaSetupDialog.tsx                                 |   304 +
 src/features/company-admin/MyInvoicesScreen.tsx                               |    10 +-
 src/features/company-admin/MyPaymentsScreen.tsx                               |     8 +-
 src/features/company-admin/RoleManagementScreen.tsx                           |   157 +-
 src/features/company-admin/ShiftManagementScreen.tsx                          |    31 +-
 src/features/company-admin/SystemControlsScreen.tsx                           |     2 +
 src/features/company-admin/UserManagementScreen.tsx                           |    11 +-
 src/features/company-admin/api/index.ts                                       |     4 +-
 src/features/company-admin/api/use-company-admin-queries.ts                   |     2 +
 src/features/company-admin/api/use-ess-mutations.ts                           |    18 +
 src/features/company-admin/api/use-ess-queries.ts                             |    35 +
 src/features/company-admin/api/use-geofence-queries.ts                        |    77 +
 src/features/company-admin/api/use-hr-mutations.ts                            |    24 +-
 src/features/company-admin/api/use-hr-queries.ts                              |    14 +
 src/features/company-admin/api/use-payroll-run-queries.ts                     |     2 +-
 src/features/company-admin/api/use-recruitment-mutations.ts                   |   497 +-
 src/features/company-admin/api/use-recruitment-queries.ts                     |   359 +-
 src/features/company-admin/hr/AdminAttendanceScreen.tsx                       |  1009 +++
 src/features/company-admin/hr/ApprovalRequestScreen.tsx                       |    65 +-
 src/features/company-admin/hr/ApprovalWorkflowScreen.tsx                      |    91 +-
 src/features/company-admin/hr/AssetManagementScreen.tsx                       |    10 +-
 src/features/company-admin/hr/AttendanceDashboardScreen.tsx                   |   329 +-
 src/features/company-admin/hr/AttendanceOverrideScreen.tsx                    |   303 +-
 src/features/company-admin/hr/BiometricDeviceScreen.tsx                       |     6 +-
 src/features/company-admin/hr/BonusBatchScreen.tsx                            |    46 +-
 src/features/company-admin/hr/BulkEmployeeImportModal.tsx                     |   614 ++
 src/features/company-admin/hr/CandidateDetailScreen.tsx                       |  1270 ++++
 src/features/company-admin/hr/ChatbotScreen.tsx                               |   171 +-
 src/features/company-admin/hr/ClearanceDashboardScreen.tsx                    |     2 +-
 src/features/company-admin/hr/CostCentreScreen.tsx                            |     2 +-
 src/features/company-admin/hr/DataRetentionScreen.tsx                         |     8 +-
 src/features/company-admin/hr/DelegateScreen.tsx                              |    25 +-
 src/features/company-admin/hr/DisciplinaryScreen.tsx                          |    57 +-
 src/features/company-admin/hr/ESignScreen.tsx                                 |    13 +-
 src/features/company-admin/hr/EmployeeDirectoryScreen.tsx                     |   101 +-
 src/features/company-admin/hr/EmployeeProfileScreen.tsx                       |   397 +-
 src/features/company-admin/hr/EmployeeSalaryScreen.tsx                        |    73 +-
 src/features/company-admin/hr/ExitRequestScreen.tsx                           |    12 +-
 src/features/company-admin/hr/ExpenseClaimScreen.tsx                          |   128 +-
 src/features/company-admin/hr/Feedback360Screen.tsx                           |    16 +-
 src/features/company-admin/hr/FnFSettlementScreen.tsx                         |    13 +-
 src/features/company-admin/hr/Form16Screen.tsx                                |    65 +-
 src/features/company-admin/hr/GradeScreen.tsx                                 |     4 +-
 src/features/company-admin/hr/GrievanceScreen.tsx                             |    24 +-
 src/features/company-admin/hr/HRLetterScreen.tsx                              |     8 +-
 src/features/company-admin/hr/HolidayScreen.tsx                               |     4 +-
 src/features/company-admin/hr/ITDeclarationScreen.tsx                         |   141 +-
 src/features/company-admin/hr/LeaveBalanceScreen.tsx                          |    19 +-
 src/features/company-admin/hr/LeaveRequestScreen.tsx                          |     8 +-
 src/features/company-admin/hr/LoanScreen.tsx                                  |   216 +-
 src/features/company-admin/hr/MyAttendanceScreen.tsx                          |    60 +-
 src/features/company-admin/hr/MyLeaveScreen.tsx                               |     8 +-
 src/features/company-admin/hr/MyPayslipsScreen.tsx                            |    45 +-
 src/features/company-admin/hr/MyProfileScreen.tsx                             |   259 +-
 src/features/company-admin/hr/NotificationRuleScreen.tsx                      |     8 +-
 src/features/company-admin/hr/NotificationTemplateScreen.tsx                  |    10 +-
 src/features/company-admin/hr/OnboardingScreen.tsx                            |     4 +-
 src/features/company-admin/hr/OrgChartScreen.tsx                              |     8 +-
 src/features/company-admin/hr/PayrollReportScreen.tsx                         |   106 +-
 src/features/company-admin/hr/PayrollRunScreen.tsx                            |    14 +-
 src/features/company-admin/hr/PayslipScreen.tsx                               |   378 +-
 src/features/company-admin/hr/ProbationReviewScreen.tsx                       |    41 +-
 src/features/company-admin/hr/ProductionIncentiveScreen.tsx                   |    47 +-
 src/features/company-admin/hr/PromotionScreen.tsx                             |    61 +-
 src/features/company-admin/hr/RequisitionScreen.tsx                           |   647 +-
 src/features/company-admin/hr/RosterScreen.tsx                                |     4 +-
 src/features/company-admin/hr/SalaryComponentScreen.tsx                       |     4 +-
 src/features/company-admin/hr/SalaryHoldScreen.tsx                            |    36 +-
 src/features/company-admin/hr/SalaryRevisionScreen.tsx                        |    34 +-
 src/features/company-admin/hr/ShiftCheckInScreen.tsx                          |    87 +-
 src/features/company-admin/hr/ShiftRotationScreen.tsx                         |     6 +-
 src/features/company-admin/hr/StatutoryFilingScreen.tsx                       |    52 +-
 src/features/company-admin/hr/SuccessionScreen.tsx                            |    16 +-
 src/features/company-admin/hr/TeamViewScreen.tsx                              |    59 +-
 src/features/company-admin/hr/TrainingCatalogueScreen.tsx                     |  1597 ++++-
 src/features/company-admin/hr/TransferScreen.tsx                              |    55 +-
 src/features/company-admin/hr/TravelAdvanceScreen.tsx                         |    18 +-
 .../company-admin/hr/analytics/AttendanceAnalyticsDashboardScreen.tsx         |     9 +-
 src/features/company-admin/hr/analytics/AttritionDashboardScreen.tsx          |     9 +-
 src/features/company-admin/hr/analytics/ComplianceDashboardScreen.tsx         |     9 +-
 src/features/company-admin/hr/analytics/ExecutiveDashboardScreen.tsx          |     9 +-
 src/features/company-admin/hr/analytics/LeaveAnalyticsDashboardScreen.tsx     |     9 +-
 src/features/company-admin/hr/analytics/PayrollAnalyticsDashboardScreen.tsx   |     9 +-
 .../company-admin/hr/analytics/PerformanceAnalyticsDashboardScreen.tsx        |     9 +-
 src/features/company-admin/hr/analytics/RecruitmentDashboardScreen.tsx        |     9 +-
 src/features/company-admin/hr/analytics/ReportsHubScreen.tsx                  |    15 +-
 src/features/company-admin/hr/analytics/TrainingDashboardScreen.tsx           |   115 +
 src/features/company-admin/hr/analytics/WorkforceDashboardScreen.tsx          |     9 +-
 src/features/company-admin/settings/GeofenceManager.tsx                       |   887 +++
 src/features/employee/AnnouncementsScreen.tsx                                 |    11 +-
 src/features/employee/DynamicDashboardScreen.tsx                              |   136 +-
 src/features/employee/EmployeeDashboard.tsx                                   |    13 +-
 src/features/ess/MyAppraisalScreen.tsx                                        |   361 +
 src/features/ess/MyAssetsScreen.tsx                                           |     4 +-
 src/features/ess/MyDocumentsScreen.tsx                                        |     4 +-
 src/features/ess/MyExpenseClaimsScreen.tsx                                    |   110 +-
 src/features/ess/MyForm16Screen.tsx                                           |   419 +-
 src/features/ess/MyGrievancesScreen.tsx                                       |     4 +-
 src/features/ess/MyHolidaysScreen.tsx                                         |     4 +-
 src/features/ess/MyLoanScreen.tsx                                             |     8 +-
 src/features/ess/MyTrainingScreen.tsx                                         |   153 +-
 src/features/ess/PolicyDocumentsScreen.tsx                                    |     4 +-
 src/features/ess/ShiftSwapScreen.tsx                                          |   581 +-
 src/features/ess/WfhRequestScreen.tsx                                         |   464 +-
 src/features/help/HelpSupportScreen.tsx                                       |     9 +-
 src/features/notifications/NotificationListScreen.tsx                         |   189 +
 src/features/super-admin/AuditLogScreen.tsx                                   |    17 +-
 src/features/super-admin/BillingOverviewScreen.tsx                            |    19 +-
 src/features/super-admin/CompanyDetailEditModal.tsx                           |  1420 +++-
 src/features/super-admin/CompanyDetailScreen.tsx                              |    59 +-
 src/features/super-admin/CompanyListScreen.tsx                                |    44 +-
 src/features/super-admin/InvoiceDetailScreen.tsx                              |    12 +-
 src/features/super-admin/InvoiceListScreen.tsx                                |    12 +-
 src/features/super-admin/ModuleCatalogueScreen.tsx                            |     6 +-
 src/features/super-admin/PaymentHistoryScreen.tsx                             |    16 +-
 src/features/super-admin/RegistrationDetailScreen.tsx                         |   298 +
 src/features/super-admin/RegistrationListScreen.tsx                           |   415 ++
 src/features/super-admin/SubscriptionDetailScreen.tsx                         |    24 +-
 src/features/super-admin/api/use-tenant-queries.ts                            |    33 +
 src/features/super-admin/bulk-upload/BulkUploadModal.tsx                      |   568 ++
 src/features/super-admin/bulk-upload/bulk-upload-utils.ts                     |    38 +
 src/features/super-admin/support/SupportDashboardScreen.tsx                   |     8 +-
 src/features/super-admin/support/SupportTicketDetailScreen.tsx                |    21 +-
 src/features/super-admin/tenant-onboarding/TenantOnboardingWizard.tsx         |     3 +-
 src/features/super-admin/tenant-onboarding/steps/Step01Identity.tsx           |    71 +-
 src/features/super-admin/tenant-onboarding/store.ts                           |     2 +-
 src/features/super-admin/tenant-onboarding/types.ts                           |     1 +
 src/features/support/TicketChatScreen.tsx                                     |    16 +-
 src/hooks/useCompanyFormatter.ts                                              |    22 +
 src/hooks/useSessionTimeout.ts                                                |    67 +
 src/index.css                                                                 |   191 +-
 src/layouts/DashboardLayout.tsx                                               |    12 +-
 src/layouts/Sidebar.tsx                                                       |   241 +-
 src/layouts/TopBar.tsx                                                        |   184 +-
 src/lib/api/admin-attendance.ts                                               |    30 +
 src/lib/api/attendance.ts                                                     |     5 +-
 src/lib/api/auth.ts                                                           |    73 +-
 src/lib/api/client.ts                                                         |    18 +-
 src/lib/api/company-admin.ts                                                  |    27 +
 src/lib/api/ess.ts                                                            |    24 +
 src/lib/api/hr.ts                                                             |    50 +-
 src/lib/api/notifications.ts                                                  |    23 +
 src/lib/api/payroll-run.ts                                                    |     4 +-
 src/lib/api/platform-registrations.ts                                         |    65 +
 src/lib/api/recruitment.ts                                                    |   556 +-
 src/lib/api/registration.ts                                                   |    27 +
 src/lib/api/tenant.ts                                                         |    22 +
 src/lib/api/use-auth-mutations.ts                                             |    31 +-
 src/lib/employee-org-defaults.ts                                              |    22 +
 src/lib/format/company-formatter.ts                                           |   105 +
 src/lib/notifications/index.ts                                                |     1 +
 src/lib/notifications/setup.ts                                                |    99 +
 src/lib/probation-end-date.ts                                                 |    59 +
 src/lib/tenant.ts                                                             |    81 +
 src/main.tsx                                                                  |    34 +-
 src/modules/visitor/VisitorBoard.tsx                                          |     4 +-
 src/store/useAuthStore.ts                                                     |    60 +-
 vite.config.ts                                                                |    20 +
 wrangler.jsonc                                                                |     9 +
 183 files changed, 34206 insertions(+), 2161 deletions(-)
 create mode 100644 package-lock.json
 create mode 100644 public/firebase-messaging-sw.js
 delete mode 100644 src/assets/logo/Avy-ERP-Logo.png
 delete mode 100644 src/assets/logo/Company-Logo-WithBG.png
 create mode 100644 src/assets/logo/app-logo.png
 create mode 100644 src/components/ui/ImageViewer.tsx
 create mode 100644 src/features/auth/MfaSetupScreen.tsx
 create mode 100644 src/features/auth/MfaVerifyScreen.tsx
 create mode 100644 src/features/auth/ProductShowcaseScreen.tsx
 create mode 100644 src/features/auth/RegisterCompanyScreen.tsx
 create mode 100644 src/features/auth/TenantNotFoundScreen.tsx
 create mode 100644 src/features/company-admin/MfaSetupDialog.tsx
 create mode 100644 src/features/company-admin/api/use-geofence-queries.ts
 create mode 100644 src/features/company-admin/hr/AdminAttendanceScreen.tsx
 create mode 100644 src/features/company-admin/hr/BulkEmployeeImportModal.tsx
 create mode 100644 src/features/company-admin/hr/CandidateDetailScreen.tsx
 create mode 100644 src/features/company-admin/hr/analytics/TrainingDashboardScreen.tsx
 create mode 100644 src/features/company-admin/settings/GeofenceManager.tsx
 create mode 100644 src/features/ess/MyAppraisalScreen.tsx
 create mode 100644 src/features/notifications/NotificationListScreen.tsx
 create mode 100644 src/features/super-admin/RegistrationDetailScreen.tsx
 create mode 100644 src/features/super-admin/RegistrationListScreen.tsx
 create mode 100644 src/features/super-admin/bulk-upload/BulkUploadModal.tsx
 create mode 100644 src/features/super-admin/bulk-upload/bulk-upload-utils.ts
 create mode 100644 src/hooks/useCompanyFormatter.ts
 create mode 100644 src/hooks/useSessionTimeout.ts
 create mode 100644 src/lib/api/admin-attendance.ts
 create mode 100644 src/lib/api/notifications.ts
 create mode 100644 src/lib/api/platform-registrations.ts
 create mode 100644 src/lib/api/registration.ts
 create mode 100644 src/lib/employee-org-defaults.ts
 create mode 100644 src/lib/format/company-formatter.ts
 create mode 100644 src/lib/notifications/index.ts
 create mode 100644 src/lib/notifications/setup.ts
 create mode 100644 src/lib/probation-end-date.ts
 create mode 100644 src/lib/tenant.ts
 create mode 100644 wrangler.jsonc
root@a:/home/a/Documents/Avyren-Technologies/Avy-ERP-Electron-Web# 
```


