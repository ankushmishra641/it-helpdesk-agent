"""Agent tools — the actions the helpdesk agent can take."""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from src.rag import format_citations, search_knowledge_base

# In-memory stores for local / prototype use
SYSTEM_STATUS: dict[str, dict[str, str]] = {
    "vpn": {"status": "operational", "note": "All gateways healthy"},
    "email": {"status": "operational", "note": "Exchange Online healthy"},
    "wifi": {"status": "degraded", "note": "Floor 3 AP intermittent"},
    "intranet": {"status": "operational", "note": "Portal responding normally"},
}

TICKETS: dict[str, dict[str, Any]] = {}
VERIFIED_EMPLOYEES = {"E1001", "E1002", "E2045"}  # demo verified IDs


def tool_search_knowledge_base(query: str) -> str:
    hits = search_knowledge_base(query)
    return format_citations(hits)


def tool_check_system_status(service: str) -> str:
    key = service.strip().lower().replace(" ", "")
    aliases = {
        "vpn": "vpn",
        "email": "email",
        "outlook": "email",
        "wifi": "wifi",
        "wi-fi": "wifi",
        "network": "wifi",
        "intranet": "intranet",
        "portal": "intranet",
    }
    mapped = aliases.get(key, key)
    info = SYSTEM_STATUS.get(mapped)
    if not info:
        known = ", ".join(SYSTEM_STATUS.keys())
        return f"Unknown service '{service}'. Known services: {known}"
    return (
        f"Service: {mapped}\n"
        f"Status: {info['status']}\n"
        f"Note: {info['note']}\n"
        f"Checked_at: {datetime.now(timezone.utc).isoformat()}"
    )


def tool_create_ticket(summary: str, priority: str = "Medium", category: str = "General") -> str:
    ticket_id = f"INC{uuid.uuid4().hex[:6].upper()}"
    ticket = {
        "id": ticket_id,
        "summary": summary,
        "priority": priority.title(),
        "category": category.title(),
        "status": "Open",
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    TICKETS[ticket_id] = ticket
    return (
        f"Ticket created successfully.\n"
        f"ID: {ticket_id}\n"
        f"Priority: {ticket['priority']}\n"
        f"Category: {ticket['category']}\n"
        f"Summary: {summary}"
    )


def tool_lookup_ticket(ticket_id: str) -> str:
    ticket = TICKETS.get(ticket_id.strip().upper())
    if not ticket:
        return f"No ticket found for ID '{ticket_id}'. Create one if needed."
    return (
        f"Ticket {ticket['id']}\n"
        f"Status: {ticket['status']}\n"
        f"Priority: {ticket['priority']}\n"
        f"Category: {ticket['category']}\n"
        f"Summary: {ticket['summary']}\n"
        f"Created: {ticket['created_at']}"
    )


def tool_reset_password(employee_id: str, verified: bool = False) -> str:
    """Guarded action: refuses unless identity is verified."""
    emp = employee_id.strip().upper()
    if not verified and emp not in VERIFIED_EMPLOYEES:
        return (
            "GUARDRAIL BLOCKED: password reset requires identity verification. "
            "Ask the employee for a verified Employee ID (demo IDs: E1001, E1002, E2045) "
            "or escalate with create_ticket."
        )
    if emp not in VERIFIED_EMPLOYEES and not verified:
        return "GUARDRAIL BLOCKED: employee identity could not be verified."

    temp = f"Temp-{uuid.uuid4().hex[:8]}"
    return (
        f"Password reset completed for {emp}.\n"
        f"Temporary password: {temp}\n"
        f"Must be changed at next login. Expires in 24 hours.\n"
        f"Advise employee to update VPN/email clients after 2–3 minutes."
    )


TOOL_SPECS = [
    {
        "name": "search_knowledge_base",
        "description": "Search internal IT documentation and return cited passages.",
        "parameters": {"query": "string — the user issue or topic"},
    },
    {
        "name": "check_system_status",
        "description": "Check live status of VPN, Email, Wi-Fi, or Intranet.",
        "parameters": {"service": "string — vpn|email|wifi|intranet"},
    },
    {
        "name": "create_ticket",
        "description": "Create an IT support ticket for human escalation.",
        "parameters": {
            "summary": "string",
            "priority": "Low|Medium|High",
            "category": "Network|Identity|Software|Hardware|General",
        },
    },
    {
        "name": "lookup_ticket",
        "description": "Look up an existing ticket by ID.",
        "parameters": {"ticket_id": "string like INCAB12CD"},
    },
    {
        "name": "reset_password",
        "description": "Reset password ONLY after identity verification.",
        "parameters": {
            "employee_id": "string",
            "verified": "bool — true only if identity confirmed",
        },
    },
]
