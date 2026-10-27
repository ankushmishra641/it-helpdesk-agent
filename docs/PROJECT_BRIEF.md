# Northstar IT Service Desk
## Product and engineering brief | 27 October 2026

### Purpose
Demonstrate a realistic employee support experience: explain IT procedures with sources, inspect service health and submit a request with clear ownership. The fictional company context makes the application useful for portfolio reviews and product demonstrations without importing private company data.

### Product experience
Six connected views cover overview, assistant, personal tickets, knowledge, service status and sample historical requests. The portal uses a restrained indigo/neutral design, responsive navigation, keyboard focus states, native dialogs and escaped text rendering.

### Dataset
60 active articles across Network, Identity, Software, Hardware and General support. Thirty employee procedures each have a corresponding service-desk runbook. A deterministic seed creates 150 fictional employees, 250 assigned assets, 600 linked requests, 20 services and 40 incident/maintenance records. Historical records have timelines and linked articles. The source snapshot is dated 20 October 2026.

### Architecture
FastAPI serves a buildless browser frontend. A bounded LangGraph workflow combines BM25 retrieval with optional Groq explanations. SQLAlchemy supports SQLite for development and PostgreSQL for deployment. Historical records are immutable JSON; new visitor records live in session-owned database rows.

### Safe action design
The model never receives mutation tools. Ticket creation requires a reviewed form and validated API request, with session ownership and idempotency. Real password resets are unavailable regardless of employee ID or a claimed verification flag. Service health is explicitly a simulation.

### Release verification
Automated tests exercise authentication, cross-session isolation, expiry, deletion, persistence, parallel duplicate submission, provider failure, request quotas, untrusted history, unsafe account instructions, retrieval matching and dataset references. Browser verification covers the actual interface. Target hosting, PostgreSQL and real-provider behavior require separate deployed verification.

### Hosting
Target: Render Free application plus Supabase Free PostgreSQL, accessed through one public HTTPS link. Groq is optional. Usage allowances and idle suspension mean this is a limited public demo, not an always-on enterprise service.

### Enterprise roadmap
SSO and role-based access, identity-provider verification, real ITSM integrations, distributed rate limiting, explicit database migrations, backup restore exercises, live monitoring, accessibility audit, broader retrieval evaluation and load/security testing.
