# API reference

All private demo routes require `X-Demo-Token: <opaque token>`. Obtain it from `POST /api/session`. Never place tokens in URLs or logs. The browser stores the token in sessionStorage. There are no cookies or cross-origin allowances.

| Method | Route | Behavior |
| --- | --- | --- |
| GET | / | Portal |
| GET | /health | Database readiness and active knowledge count |
| POST | /api/session | Issue a 7-day anonymous demo token |
| DELETE | /api/session | Delete current session and dependent private records |
| GET | /api/bootstrap | Fictional company summary, service snapshot and own tickets |
| GET | /api/history | Last 12 server-stored messages |
| POST | /api/chat | Retrieve and explain; never create tickets or reset passwords |
| GET | /api/tickets | List own tickets |
| GET | /api/tickets/{id} | Read own ticket; absent/other-session IDs return 404 |
| POST | /api/tickets | Confirm a new ticket, with an idempotency UUID |
| GET | /api/knowledge?q= | List or search active articles |
| GET | /api/knowledge/{id} | Read an indexed article; no arbitrary file access |
| GET | /api/demo-records?q=&page= | Read-only synthetic history, 20 records/page |

## Chat request

```json
{"message": "I cannot connect to VPN"}
```

The response includes `answer`, `mode`, `sources`, `tool_trace` and an optional `action`. Trace entries are curated descriptions, not raw tool arguments or passwords. Supplied client history is rejected.

## Ticket request

```json
{
  "summary": "External monitor not detected",
  "description": "The assigned dock is powered, but the display remains blank.",
  "category": "Hardware",
  "priority": "Medium",
  "request_key": "bdcf5ed2-b128-456e-ae82-937320687b37"
}
```

Reuse the same request_key only to retry exactly the same submission. Responses omit ownership digests and request fingerprints. Categories: General, Network, Identity, Software, Hardware. Priorities: Low, Medium, High.

## Limits and errors

Bodies are limited to 16 KiB including streamed bodies. Chat messages: 2-1500 characters. Ticket summaries: 5-160; descriptions: 10-3000. Validation strips leading/trailing whitespace and rejects unexpected fields.

401: missing/expired session. 404: inaccessible or missing record. 409: conflicting idempotency payload or ticket allowance reached. 413: body too large. 422: schema validation. 429: session, IP or daily quota. 503: internal dependency unavailable.

Readiness does not verify a live Groq response. No OpenAPI browser or legacy /chat or /mcp/call_tool endpoint is exposed on this public demo.
