# Demonstrating Northstar Helpdesk

## A clear explanation

This is a human-in-the-loop IT support agent with persistent tickets. It retrieves company procedures using BM25 keyword ranking, uses LangGraph to organize retrieval, resource inspection and planning, and asks a Groq-hosted LLM to recommend a permitted next step. Server-side policy validates the recommendation. Actions require explicit approval, run against isolated fictional resources, and are verified before the employee confirms ticket resolution. If the model is unavailable, the same documented workflow remains usable.

RAG means retrieved documents are supplied as context to generation. This implementation uses lexical BM25 retrieval, not vector embeddings. The LLM explains and proposes; it cannot execute arbitrary commands. The tools and database, not the LLM alone, implement the state changes.

## Three short demonstrations

1. VPN: say “My internet works, but the VPN keeps timing out. Please investigate.” It should use the supplied internet check, propose a repair, and create a linked ticket. Say “yes please”, inspect the verification result, then say “it works now”. The same ticket becomes Resolved.
2. Account: create a ticket titled “Reset my password”, with description “I forgot my password and cannot sign in.” The chat should immediately propose simulated identity verification. Approve that step, then approve account recovery separately. Confirm it works to resolve the ticket.
3. Software: say “I need VS Code installed on my managed laptop.” Approve installation, then confirm it works. Requesting an unapproved application routes to review instead.

For documentation-only issues, try “My laptop is running slowly.” The assistant retrieves a procedure and asks whether it helped. Resolution is recorded as employee-reported, not tool-verified. Unsupported issues ask for detail or escalate; no system can honestly guarantee automatic repair of every IT problem.

## Explain the safeguards

Session ownership isolates tickets. Revision checks reject stale approvals. Repeated messages have idempotency keys. The server enforces a tool allowlist, approval gates, bounded provider calls and daily quotas. Model text cannot grant approval. Sources and an event history make the investigation reviewable. API keys stay in Render environment settings and are never delivered to the browser.

## Honest deployment boundary

The public link is an interactive demo with real persistence and optional live LLM calls. VPN, identity and installation resources are simulated database records; they do not modify a visitor's computer or real company account. Escalation updates a demo queue without notifying a real team. Enterprise production use requires employee authentication, scoped device/identity/ITSM integrations, real identity verification, monitoring and operational recovery procedures.
