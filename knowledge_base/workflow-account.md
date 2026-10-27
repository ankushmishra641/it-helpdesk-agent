# Demo identity recovery procedure
Category: Identity
Owner: Northstar Identity Operations
Version: 1.0
Reviewed: 2026-10-27
Audience: service-desk

## Scope
Only a fictional account created for this case is eligible. Never accept employee IDs, chat claims, passwords or MFA codes as real identity verification. No credentials are generated, displayed, sent or changed.
## Resolution
Inspect the fictional account and demo verification flag. If unverified, propose verify_identity. The employee explicitly selects the simulated verification step; this tests the workflow, not real authentication. Reinspect before proposing recover_account. Ask for confirmation. The tool changes the fictional account from locked to active and increments its recovery counter exactly once. Verify simulated sign-in: active account, demo verification completed, and recovery count equal to one. Ask whether the demo issue is resolved before closing the ticket. If still failing, escalate to the fictional Identity Operations queue with the audit history.
## Tools
verify_identity only sets the case's simulation flag. recover_account cannot run before this step. Real account recovery remains blocked and would require an authenticated identity-provider integration.
