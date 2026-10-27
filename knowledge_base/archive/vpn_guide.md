# VPN Setup & Troubleshooting Guide

## Overview
Company VPN provides secure remote access to internal systems. Use the official GlobalProtect client.

## Setup (Windows)
1. Download GlobalProtect from the IT portal.
2. Install and open the app.
3. Enter gateway: `vpn.company.internal`
4. Sign in with your corporate email and password / MFA.
5. Confirm status shows **Connected**.

## Common Issues
### Cannot connect / connection times out
- Confirm internet works in a browser.
- Disable personal VPN or proxy temporarily.
- Try switching network (office Wi-Fi vs home vs mobile hotspot).
- Check that MFA push was approved on your phone.
- If gateway DNS fails, set DNS to corporate DNS or try `vpn-backup.company.internal`.

### Connected but cannot reach internal apps
- Disconnect and reconnect VPN.
- Confirm you are on the correct gateway region.
- Clear browser cache for internal portals.
- Raise a ticket if only one app fails while others work.

### Password expired while on VPN
- Password expiry blocks VPN auth.
- Use the password reset self-service portal or ask IT Helpdesk Agent to start a verified reset.
- After reset, wait 2–3 minutes before reconnecting.

## Escalation
If VPN is down for multiple users, check System Status first. If service is degraded, create a Priority High ticket under Network.
