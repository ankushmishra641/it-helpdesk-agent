"""
MCP-style tool server for the IT Helpdesk Agent.

Exposes helpdesk tools over a simple JSON HTTP interface so other
clients can call them through a shared tool protocol.

Run: python mcp_server.py
"""
from __future__ import annotations

import sys
from pathlib import Path

from fastapi import FastAPI
from pydantic import BaseModel
import uvicorn

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from src.tools import (
    TOOL_SPECS,
    tool_check_system_status,
    tool_create_ticket,
    tool_lookup_ticket,
    tool_reset_password,
    tool_search_knowledge_base,
)

app = FastAPI(title="IT Helpdesk MCP-style Tool Server", version="0.1.0")


class CallRequest(BaseModel):
    name: str
    arguments: dict = {}


@app.get("/mcp/list_tools")
def list_tools():
    return {"protocol": "mcp-style-demo", "tools": TOOL_SPECS}


@app.post("/mcp/call_tool")
def call_tool(req: CallRequest):
    name = req.name
    args = req.arguments or {}
    if name == "search_knowledge_base":
        return {"content": tool_search_knowledge_base(args.get("query", ""))}
    if name == "check_system_status":
        return {"content": tool_check_system_status(args.get("service", "vpn"))}
    if name == "create_ticket":
        return {
            "content": tool_create_ticket(
                args.get("summary", "No summary"),
                args.get("priority", "Medium"),
                args.get("category", "General"),
            )
        }
    if name == "lookup_ticket":
        return {"content": tool_lookup_ticket(args.get("ticket_id", ""))}
    if name == "reset_password":
        return {
            "content": tool_reset_password(
                args.get("employee_id", ""),
                bool(args.get("verified", False)),
            )
        }
    return {"error": f"Unknown tool: {name}"}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8100)
