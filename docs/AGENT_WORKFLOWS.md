# Guided resolution workflows

## What is implemented

The public app has an optional LLM-backed RAG planner, controlled demo tools, persistent case state and a deterministic fallback. It is a bounded human-in-the-loop agent, not an unrestricted autonomous administrator. LangGraph orchestrates retrieval, resource inspection and planning. BM25 retrieves related guides; the chosen workflow's authoritative procedure is included explicitly. Groq returns a JSON tool recommendation and explanation. Model output never directly changes resources.

Each case owns a fictional resource independent of other tickets and sessions. This provides repeatable scenarios, not an enterprise inventory integration. Identity verification is a simulated fixture transition; no real credential is requested or changed. Software installation changes a database record, not the visitor's device. Verification checks that record and its preconditions. Escalation records a fictional queue and history; it sends no notification.

## Demonstrate all three cases

1. Ask the assistant about VPN, password recovery or software. Select **Start guided demo case**, review the form and create it. Existing tickets also have workflow buttons in their details.
2. Answer the scenario question. The graph retrieves policy, inspects the resource and proposes the next tool. Sources, mode and diagnostics are visible.
3. Approve the proposed action. Account recovery requires a separate simulated identity-verification step before recovery can be approved.
4. The tool updates the fictional resource and checks the result. The ticket becomes **Waiting**, not Resolved.
5. Select **It works — resolve this ticket** to close it, or **Still not working — escalate** to retain the investigation in a specialist queue.

VPN repair requires working internet and an operational VPN service. Internet failure or a simulated outage routes to review. Software fulfillment permits approved VS Code only; an unapproved application routes to Software Asset Management. Unsupported issues can still use ordinary knowledge search and tickets.

## Privately enable Groq on Render

Open the northstar-it-helpdesk service → Environment → Edit. Set:

| Key | Value |
| --- | --- |
| GROQ_API_KEY | Paste your private key in Render only |
| LLM_PROVIDER | groq |
| GROQ_MODEL | openai/gpt-oss-20b |
| DAILY_LLM_LIMIT | 100, or a smaller positive limit |

Save, rebuild, and deploy. Never put the key in chat, screenshots, source files, frontend JavaScript or GitHub. A key alone does not enable model calls. Both chat and case planning share the daily allowance and two-call concurrency limit. Calls time out after 15 seconds and cap completion tokens at 1,800. Groq account limits and billing are separate; the application limit is not a currency cap. Availability depends on the account's model permissions.

The default model was checked against Groq's supported models on 27 October 2026: https://console.groq.com/docs/models . Override GROQ_MODEL if account availability changes. No model tools for browsing, shell execution or remote MCP are enabled.

## Fallback and evidence

Disabled AI, exhausted quota, busy slots, network/provider errors, malformed JSON and invalid proposed tools use the documented fallback. The case displays **LLM + RAG plan** only when a valid provider response was accepted; otherwise it displays **Documented workflow fallback**. A configuration badge alone is not proof a live model call succeeded.

The event timeline distinguishes observations, proposed tools, confirmed tool execution, verification and employee confirmation. The UI labels generated explanations as proposals. Successful simulation is not proof that a real employee problem has been solved.

## Concurrency and recovery

Workflow creation is idempotent per ticket. Each action supplies the displayed revision. Only one compare-and-swap can commit a revision, so duplicate approvals cannot recover an account or apply a remedy twice. A lost HTTP response can be recovered by reopening the ticket. Model planning happens before the database transaction; a concurrent stale plan is discarded. No external action happens before commit.

## Before real enterprise use

Replace anonymous sessions with authenticated employees, integrate scoped identity/device/ITSM tools, implement real identity verification and approval policies, enforce organizational permissions, and test backup restoration and monitoring. Keep the policy gates, confirmation boundaries, verification checks and audit trail. Do not reuse the simulated verification flag as authentication.
