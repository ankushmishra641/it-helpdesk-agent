# Free-tier deployment: Render + Supabase

## Scope

Deploy a public synthetic demo under one Render HTTPS URL. No custom domain purchase is required. Free-tier limits can change; verify the current provider dashboard before choosing a plan. Avoid enabling paid add-ons.

Official references:
- https://render.com/docs/free
- https://render.com/docs/deploy-fastapi
- https://supabase.com/docs/guides/database/connecting-to-postgres
- https://supabase.com/docs/guides/platform/free-project-pausing
- https://console.groq.com/docs/rate-limits

## 1. Prepare PostgreSQL

Create or select a free Supabase project. Keep database credentials in the provider secret settings, not chat, source files, screenshots or GitHub issues.

For a dedicated server role, an administrator can run the following in Supabase SQL Editor. Replace the password in the provider interface itself. Do not commit the resulting credential.

```sql
CREATE ROLE helpdesk_app LOGIN PASSWORD '<set a strong unique password privately>';
CREATE SCHEMA helpdesk AUTHORIZATION helpdesk_app;
REVOKE ALL ON SCHEMA helpdesk FROM PUBLIC;
GRANT CONNECT ON DATABASE postgres TO helpdesk_app;
```

If the role/schema already exists, inspect its owner and grants rather than rerunning CREATE statements. The app creates its tables within this schema. Do not add helpdesk to Supabase's exposed API schemas.

Copy the **Session pooler** connection URI from Connect. Use the dedicated role in the pooler username according to Supabase's connection instructions, preserve the project reference, URL-encode password characters, and require TLS. Session pooler is preferred for compatibility with a long-running Python service. Test the role through the pooler before launch.

```text
postgresql+psycopg://ROLE.PROJECT_REF:PASSWORD@POOLER_HOST:5432/postgres?sslmode=require
```

Use the actual dashboard URI and host; the example is not a connection string.

## 2. Deploy the repository

Repository: https://github.com/ankushmishra641/it-helpdesk-agent

Choose Render New > Blueprint and select the tested release branch containing render.yaml. Review that the service plan is Free. Alternatively create a Python web service with:

| Setting | Value |
| --- | --- |
| Python | 3.12.10 |
| Build | pip install -r requirements.txt |
| Start | uvicorn api:app --host 0.0.0.0 --port $PORT --workers 1 --limit-concurrency 40 --timeout-keep-alive 5 |
| Health check | /health |
| DATABASE_URL | Private Supabase connection URI |
| LLM_PROVIDER | none initially |
| DAILY_LLM_LIMIT | 100 |
| MAX_DAILY_SESSIONS | 50 |

Leave GROQ_API_KEY absent initially. The blueprint does not provision a database or create a paid service. Do not use Render's expiring free Postgres for a long-lived showcase. The app refuses local SQLite on Render.

The first startup creates schema version 1. If readiness fails, inspect credential validity, pooler host, schema ownership and TLS configuration. Do not paste complete logs containing credentials into public issues.

## 3. Optional AI mode

Set GROQ_API_KEY privately in Render and change LLM_PROVIDER to groq. Redeploy. Groq calls are bounded to 100/day by default, 2 concurrent calls, 1500-character questions and 1,800 completion tokens. Exceeding the allowance or encountering a provider failure falls back to local knowledge. Confirm the model is available in your account.

The AI key never appears in client JavaScript. The application remains functional without it.

## 4. Launch verification

1. Open the HTTPS URL in two independent browser sessions.
2. Ask a VPN question and inspect the cited article.
3. Create a ticket in session A and verify session B cannot retrieve it.
4. Refresh the browser and verify session A's records remain.
5. Redeploy the service and confirm ticket persistence.
6. Check the health endpoint and the incident snapshot label.
7. Confirm no browser console errors and test mobile ticket creation.
8. Run the PostgreSQL smoke test below against a dedicated staging database.
9. Verify a backup restoration before storing anything you need to retain.

## PostgreSQL staging test

Use a new empty staging database/schema, never an existing production schema. Set DATABASE_URL securely in the terminal environment; do not include credentials in shell history. Run `python scripts/check_database.py`. The script creates a temporary session and ticket, verifies it, then deletes only that session. It prints no credentials.

## Free-tier behavior

Render can sleep after 15 minutes without requests and may take about a minute to wake. Supabase can pause low-activity free projects. Local files on Render are ephemeral. The source-controlled knowledge and sample JSON are rebuilt from Git; visitor records belong in PostgreSQL.

A public URL is a deployment result, not proof of production readiness. Do not claim successful hosting until the provider reports success and the deployed workflows pass.
