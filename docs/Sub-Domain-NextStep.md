Here’s your content rewritten into a clean, professional, production-ready document format 👇

⸻

🚀 Avy ERP — Production Readiness Checklist

📌 Next Steps for Completeness

This document outlines the required steps to move the system from the current state to production deployment, including infrastructure setup, database configuration, backend environment setup, deferred features, and final testing.

⸻

🏗️ 1. Infrastructure Setup (Pre Go-Live)

1.1 Cloudflare DNS Configuration
	•	Add wildcard subdomain:
	•	*.avyerp.avyren.in → CNAME → Cloudflare Pages project
	•	Add root subdomain:
	•	avyerp.avyren.in → CNAME → Cloudflare Pages project
	•	SSL:
	•	Enabled automatically via Cloudflare Universal SSL

⸻

1.2 Cloudflare Pages Deployment
	•	Create a project pointing to:
	•	web-system-app/ (build output directory)
	•	Add custom domains:
	•	avyerp.avyren.in
	•	*.avyerp.avyren.in
	•	Build configuration:

pnpm build



⸻

1.3 PgBouncer Setup (Connection Pooling)
	•	Start PgBouncer on server:

docker-compose up -d pgbouncer


	•	Update backend environment:
	•	Replace:

@postgres:5432


	•	With:

@pgbouncer:6432


	•	Verify connection:

pg_isready -h localhost -p 6432



⸻

🗄️ 2. Database & Data Setup

2.1 Run Database Migrations

cd avy-erp-backend

pnpm db:migrate            # Platform schema
pnpm db:migrate-tenants   # Tenant schemas


⸻

2.2 Create Demo Tenant
	•	Onboard a demo company via Super Admin Wizard
	•	Slug: demo
	•	Create demo credentials:
	•	Email: demo-admin@avyerp.com
	•	Password: demo123
	•	Seed sample data:
	•	Departments
	•	Employees
	•	Attendance
	•	Payroll data

⸻

2.3 Backfill Tenant Slugs
	•	Ensure all existing tenants have a unique slug
	•	Required since slug is now mandatory
	•	Options:
	•	Write a one-time migration script
	•	Or manually assign before migration

⸻

⚙️ 3. Backend Configuration

3.1 Production Environment Variables

MAIN_DOMAIN=avyerp.avyren.in
SUPER_ADMIN_EMAIL=admin@avyren.in
CORS_ALLOWED_ORIGINS=https://avyerp.avyren.in
SMTP_HOST=...  # For registration emails


⸻

3.2 Web Application Environment

VITE_MAIN_DOMAIN=avyerp.avyren.in
VITE_API_URL=https://avy-erp-api.avyren.in/api/v1/


⸻

🧩 4. Features Deferred (Post Go-Live Enhancements)

4.1 Demo Tenant Isolation
	•	Daily cron job to reset demo data
	•	Disable:
	•	Email
	•	SMS
	•	External integrations (via feature flags)

⸻

4.2 Super Admin Registration Dashboard
	•	UI for:
	•	/platform/registrations
	•	List view
	•	Detail view
	•	Approve / Reject actions
	•	✅ Backend APIs already implemented

⸻

4.3 Registration → Onboarding Flow
	•	Connect approval action to:
	•	Auto-fill tenant onboarding wizard
	•	Use registration data to pre-populate setup

⸻

4.4 Custom Domain Support
	•	customDomain field exists in Tenant model
	•	Implement:
	•	Domain resolution
	•	SSL provisioning (Cloudflare / custom)

⸻

4.5 Database-per-Tenant Strategy
	•	dbStrategy abstraction already exists
	•	Future implementation:
	•	Separate DB provisioning per tenant
	•	Dynamic connection routing

⸻

✅ 5. Pre-Production Testing Checklist

5.1 Domain & Routing Validation
	•	avyerp.avyren.in
	•	Landing page
	•	Demo login
	•	Registration link
	•	admin.avyerp.avyren.in
	•	Super admin login only
	•	<slug>.avyerp.avyren.in
	•	Company-specific branded login
	•	Invalid slug:
	•	invalid-slug.avyerp.avyren.in
	•	Expected: 404 — Company Not Found

⸻

5.2 Authentication & Security
	•	Registration flow:
	•	Submit → Super admin receives email
	•	Cross-tenant login:
	•	Must be blocked with proper error
	•	Mobile login:
	•	Works correctly
	•	No registration option exposed

⸻

5.3 Functional Validation
	•	Demo tenant works end-to-end
	•	Tenant isolation verified
	•	API responses mapped correctly
	•	Role-based access enforced

⸻

🎯 Final Summary

Phase	Scope
1–3	Core deployment & infrastructure
4	Future-ready enhancements
5	Final validation before production


⸻

🧠 Conclusion
	•	Steps 1–8 → Mandatory for production deployment
	•	Steps 9–13 → Planned features (architecture already supports them)
	•	Step 14 → Final validation before go-live

✔ Completing this checklist ensures your system is:
	•	Deployment-ready
	•	Scalable
	•	Multi-tenant safe
	•	Production-grade

⸻

If you want, I can next:
👉 Convert this into a DevOps checklist (CI/CD + monitoring + rollback plan)
👉 Or create a production architecture diagram (like system design doc)