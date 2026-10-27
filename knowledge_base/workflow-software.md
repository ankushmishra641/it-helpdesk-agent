# Demo application fulfillment procedure
Category: Software
Owner: Northstar Software Asset Management
Version: 1.0
Reviewed: 2026-10-27
Audience: service-desk

## Scope
Fictional managed device only. No installers are downloaded or executed. The demo catalog approves VS Code; all other requests require specialist review.
## Resolution
Ask whether the employee requests approved VS Code or unapproved software. Inspect catalog approval and installed state. For unapproved software, escalate to Software Asset Management without installing. For approved VS Code that is absent, propose install_software and request confirmation. Update the fictional device's installation record. Verify catalog approval, package presence and simulated launch. Ask the employee to confirm success before resolving the ticket. Escalate if the employee reports a remaining problem.
## Tools
install_software sets installed=true only when approved=true. Verification checks both fields. Never claim software was installed on the visitor's real computer.
