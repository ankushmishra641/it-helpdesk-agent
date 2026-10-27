# Demo connectivity recovery procedure
Category: Network
Owner: Northstar Network Operations
Version: 1.0
Reviewed: 2026-10-27
Audience: service-desk

## Scope
Session-isolated simulated resources only. Never execute commands on a real device.
## Resolution
Ask whether internet works independently of VPN. Inspect internet availability, service health and the local profile. If internet is unavailable or the VPN service is degraded, escalate to Network Operations without changing the profile. When internet and service are healthy and the profile is stale, propose repair_vpn. Ask for confirmation, repair the fictional profile and reconnect once. Verify that the simulated internal portal is reachable. Wait for employee confirmation before resolving the ticket. If they report failure, escalate with the checks and attempted action.
## Tools
repair_vpn changes this case's fictional vpn_profile from stale to healthy. Its verification requires internet=true, service=Operational and vpn_profile=healthy. No real network settings change.
