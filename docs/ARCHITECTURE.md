# Architecture and data model

## Design decisions

The public application has one origin and one Python worker. FastAPI serves both the static portal and JSON endpoints. Same-origin requests require no permissive CORS policy. Static assets contain no provider credentials.

A two-node LangGraph workflow retrieves evidence and then prepares an answer. Local BM25 retrieval is the default: the 60-document corpus is small, predictable and version-controlled. Token normalization, title weighting, relevance thresholds and paired-guide deduplication improve topic matching. The index is rebuilt into a new list when source file signatures change; no persistent collection accumulates duplicates. Retrieval is lexical rather than semantic, and relevance thresholds are heuristics.

Groq is an optional explanation provider. Only retrieved documentation, the current question and up to four prior messages are sent. A model response has no write capability. Account-recovery requests are blocked deterministically; ticket intent produces a draft action for the frontend form. Ticket lookup is constrained by the server session.

## Trust boundaries

1. Browser input is untrusted. Extra schema fields, supplied history and invalid enumerations are rejected.
2. A random token creates an anonymous demo workspace, not an employee identity.
3. Database reads and writes filter by the server-resolved session digest.
4. Model output is rendered as escaped text, never HTML.
5. Historical company data is immutable synthetic JSON. Visitor writes cannot modify it.
6. PostgreSQL objects live in the private `helpdesk` schema, not Supabase's default exposed `public` schema. Do not add `helpdesk` to exposed API schemas.

## Relational schema, version 1

| Table | Key | Purpose |
| --- | --- | --- |
| demo_sessions | token digest | Expiry, message and ticket counters |
| tickets | random INC ID | Session-owned request, priority, status, category, idempotency key |
| messages | random UUID | Server-owned conversation history |
| audit_events | random UUID | Minimal ticket-created audit event; no raw prompt or secrets |
| llm_daily_budget | UTC date | Atomic global provider call reservation |
| session_daily_budget | UTC date | Atomic global session reservation |
| schema_version | integer | Initial schema version marker |

Tickets, messages and audit events reference sessions with cascade deletion. Ticket creation, counter reservation and audit insertion are one transaction. A unique `(session_id, request_key)` constraint makes duplicate submissions safe; reuse with a different payload returns a conflict.

Initial installation creates schema version 1 using SQLAlchemy metadata. This is bootstrap, not an upgrade migration system. Before making incompatible schema changes, add a reviewed migration and backup/restore test. Do not assume `create_all` alters existing columns.

## Deployment topology

Render web service -> Supabase PostgreSQL Session pooler over TLS.

Use one Uvicorn worker because short-term rate limits and provider concurrency are in-process. Durable daily quotas and records are database-backed. Horizontal scaling requires a shared rate limiter and distributed concurrency control.

## Known limits

No authenticated enterprise users, email notifications, ticket assignment engine, comments/update API, live monitoring, SSO, real ITSM connector or password reset exists. The demo demonstrates creation and inspection; historical ticket timelines are seeded. Chat responses are delivered as a complete response, not token streaming. Provider availability is configuration state, not a continuous health probe.
