# Validation record

Date: 27 October 2026. Release branch: release/public-helpdesk-demo.

## Completed

- Clean Python 3.12 installation of the application requirements.
- 22 regression tests passed locally against SQLite.
- The same 22 tests passed in GitHub CI against PostgreSQL 16.
- GitHub CI also passed the SQLite suite, JavaScript syntax validation and dependency audit.
- 48 resolved dependencies audited locally: no known vulnerabilities reported; no skipped packages.
- Dependency consistency check: no broken requirements.
- Credential-pattern scan of application, documentation, tests and synthetic data: no provider/token patterns found.
- Browser flow: confirmed ticket creation, ticket list persistence after reload, VPN answer and cited guide, knowledge filtering, article details and historical ticket filtering.
- Browser developer log check: no captured errors/warnings during the tested portal flows.
- Narrow initial browser layout and wide desktop layout inspected. Exact mobile viewport emulation was not reliable in this browser host; a broader physical-device/accessibility audit remains outstanding.
- Four-page project brief rendered and visually inspected.

CI evidence: https://github.com/ankushmishra641/it-helpdesk-agent/actions/runs/40486786324

## Scope of the tests

Authentication, visitor isolation, expiry, deletion, persistent records, idempotency (including simultaneous retries), rate limits, daily budgets, schema/input caps, server-owned history, password-reset denial, injection attempts against account actions, provider-failure fallback, retrieval scenarios and synthetic referential integrity.

## Remaining target-environment checks

The Supabase-specific pooler, dedicated role and schema grants; Render deployment and wake behavior; public HTTPS end-to-end tests; backup restoration; live Groq model availability and answer quality. PostgreSQL CI success does not establish Supabase configuration correctness or a production SLA.

The audit is a point-in-time dependency check, not proof that the application has no vulnerabilities.

## Guided workflow extension — 27 October 2026

33 regression tests passed locally against SQLite, including all three resolution paths, prerequisite escalation, employee-reported failure, wrong-session access, missing policy, malformed/unsafe model proposals, persistence, deletion cascades and concurrent approvals. Provider JSON success and failure are mocked in the suite. A browser walkthrough confirmed account recovery through Resolved with no captured console warnings/errors. A real Groq call is not established by these mock tests.

### Hosted release verification

Implementation commit: 032c400. CI run 40494627664 passed both 33-test suites (SQLite and PostgreSQL 16), JavaScript syntax and dependency audit.

On 27 October 2026, the Render/Supabase deployment completed VPN repair, fictional account recovery and approved software fulfillment through verification and Resolved status in isolated test sessions. All three also passed with the provider disabled. After private Groq configuration, an actual chat response reported groq mode and all four case planning steps returned accepted Groq proposals: repair_vpn, verify_identity, recover_account and install_software. Test sessions were removed afterward. Evidence contains no API key, database credential or session token.

The live app runs openai/gpt-oss-20b through Groq. Provider latency and available quota can still cause fallback on later requests. This verifies the stated demo scenarios, not general autonomous problem resolution or real account/device administration.
