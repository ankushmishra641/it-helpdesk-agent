# Operations runbook

## Readiness and diagnostics

GET /health checks database access and reports active article count. It does not call the model. Frontend AI availability indicates configuration, not provider health. On provider failure the assistant uses local guides.

Logs intentionally exclude prompts, bearer tokens and provider exception bodies. Investigate error class, provider dashboards and database connectivity. Never expose raw configuration in diagnostics.

## Common incidents

| Symptom | First action |
| --- | --- |
| First visit loads slowly | Check whether the free Render instance is waking |
| 503 / failed readiness | Check Supabase pause state, pooler URI, TLS and role grants |
| 429 chat | Wait for the minute window; inspect session allowance |
| No new sessions | Check UTC daily quota; do not disable caps during abuse |
| AI explanation absent | Check provider quota/key/model; local search should still work |
| Irrelevant answer | Add a regression query and improve source text/ranking |
| Duplicate ticket report | Compare request_key and payload; same-key retries must return one record |

## Knowledge changes

Edit active Markdown files at the knowledge_base root. The archive subdirectory is excluded. Each article needs an owner, version, review dates, symptoms, resolution, validation and escalation. Restart or the next retrieval detects file changes. Run retrieval tests after changing content. Never insert secrets or real employee information.

The deterministic seed script overwrites generated guides and the sample JSON. Update its topic definitions before regeneration if you want changes to persist.

## Retention and backup

Sessions expire after seven days; cleanup runs during startup and new-session issuance. For a strict cleanup schedule, run a trusted maintenance job that deletes expired session rows, allowing foreign-key cascades.

Do not rely on free-tier automated backups. For PostgreSQL, an authorized operator can use pg_dump with credentials supplied through a secure environment/pgpass file:

```text
pg_dump --format=custom --schema=helpdesk --file=helpdesk-backup.dump
```

Supply connection parameters securely (PGHOST, PGPORT, PGUSER, PGDATABASE, TLS settings). Encrypt backups, restrict access and choose a retention period. Restore into an isolated staging database with pg_restore, run readiness and the staging smoke test, and verify representative records. Restore has not been verified until this procedure succeeds in the selected environment.

SQLite is a local-only convenience. Stop the app before copying a local database for a development backup.

## Rollback

Keep the prior tested Git commit. Redeploy that commit from Render if an application change fails. Version 1 has only schema bootstrap; no destructive migration is run at startup. For future schema changes, provide explicit forward/backward-compatible migrations and a restore plan before rollout. Do not deploy older code across an incompatible schema.

## Scaling and enterprise work

Before adding workers or replicas, replace in-memory rate/concurrency limits with shared infrastructure. Before connecting real IT systems, add authenticated users, RBAC, verified identity-provider flows, permission-scoped connectors, secret management, robust auditing, data retention governance and independent security testing.
