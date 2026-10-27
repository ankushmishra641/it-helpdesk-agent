# Security review and public-demo boundary

Reviewed implementation scope: synthetic demonstration. This document is not a penetration-test certificate.

## Original findings and treatment

| Finding | Treatment |
| --- | --- |
| Caller-controlled verified flag permitted resets | All real resets blocked, including direct tool calls |
| Offline pattern treated any employee ID as verified | No identity inference from text |
| Unauthenticated global ticket tools | Removed public tool server; session-owned validated API |
| Shared in-memory tickets | SQL transactions and ownership filters |
| Temporary passwords in output/traces | No credential generation; curated non-sensitive trace descriptions |
| Duplicate/outdated knowledge entries | Immutable in-memory rebuild; old corpus archived |
| Ticket lookup created a ticket | Separate lookup, drafting and confirmed creation paths |
| Arbitrary client conversation history | Server-owned history; extra request fields rejected |
| No request/provider limits | Body caps, session/IP throttling, DB-backed daily quotas, bounded provider concurrency |
| Unsafe rendered output risk | Escape dynamic text; strict Content Security Policy; no external frontend scripts |
| Public refresh action | Not exposed in the new portal |
| Wildcard CORS | Removed; one origin |

## Authorization model

Tokens have 256 bits of random entropy and are stored as digests in the database. They confer access only to one anonymous demo session. Possession of a copied token grants that demo session; there is no claim of strong employee authentication. All ticket routes resolve the token server-side and apply ownership checks. A database credential is held only by the server.

Use the private helpdesk schema on PostgreSQL. Do not expose that schema through Supabase REST/GraphQL. Use a dedicated database role scoped to that schema for deployment; see the deployment SQL. No Supabase service-role key is sent to the browser.

## Model boundary

The model has no database credential and no mutation tools. Prompt injection can still affect the quality of an AI explanation; a prompt is not a complete defense. Safe action boundaries do not depend on model obedience. Retrieved source cards are selected by the server. AI explanations are not independently fact-checked; users should inspect the cited guide.

## Privacy and retention

Use synthetic details only. Requests and answers are stored in the session database, and optional AI mode sends recent context to Groq. Hosting/database operators can access stored data. No request body or token is intentionally logged. Provider errors are reduced to a fallback status.

Expiry checks happen on every authenticated route. Expired sessions are deleted at startup or new-session creation. This is opportunistic cleanup, not a guaranteed deletion-time SLA. Operators should run scheduled cleanup if they require a precise retention deadline.

## Residual risks and launch gates

- In-process IP/rate counters reset on restart and do not support multiple workers.
- Anonymous quotas can be abused; the global daily session cap limits growth but can also deny access to legitimate visitors.
- IP accounting depends on correct trusted-proxy configuration. Do not enable trust for arbitrary forwarded headers.
- No SSO, RBAC, enterprise tenant model, managed secrets rotation, or live identity verification.
- Do not connect real employee data until a separate security/privacy review and enterprise authorization design is complete.
- Free tiers provide no always-on or backup SLA.
- Database restore, live PostgreSQL integration, real provider quality and deployed smoke tests must be verified in the target environment.
