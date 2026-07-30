"""LangGraph IT Helpdesk agent — reason → tool → observe → answer."""
from __future__ import annotations

import json
import re
from typing import Annotated, Any, Literal, TypedDict

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, ToolMessage
from langchain_core.tools import StructuredTool
from langgraph.graph import END, StateGraph
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode
from pydantic import BaseModel, Field

from src.config import GROQ_API_KEY, GROQ_MODEL, OPENAI_API_KEY, OPENAI_MODEL, LLM_PROVIDER, has_llm
from src.tools import (
    tool_check_system_status,
    tool_create_ticket,
    tool_lookup_ticket,
    tool_reset_password,
    tool_search_knowledge_base,
)

SYSTEM_PROMPT = """You are an internal IT Helpdesk AI Agent for employees.

Rules:
1. Prefer grounded answers from search_knowledge_base and always mention source file names.
2. For outages/connectivity, call check_system_status before concluding.
3. Never reset a password unless the employee provided a verified employee ID — pass verified=true only then.
   Demo verified IDs: E1001, E1002, E2045.
4. If you cannot safely resolve, create_ticket with a clear summary.
5. Be concise, step-by-step, and professional. Do not invent company policies.
6. If retrieval returns nothing relevant, say you don't have that in the knowledge base and offer to raise a ticket.
"""


class SearchArgs(BaseModel):
    query: str = Field(..., description="Search query for IT docs")


class StatusArgs(BaseModel):
    service: str = Field(..., description="vpn, email, wifi, or intranet")


class TicketArgs(BaseModel):
    summary: str
    priority: str = "Medium"
    category: str = "General"


class LookupArgs(BaseModel):
    ticket_id: str


class ResetArgs(BaseModel):
    employee_id: str
    verified: bool = False


def _build_tools() -> list[StructuredTool]:
    return [
        StructuredTool.from_function(
            func=tool_search_knowledge_base,
            name="search_knowledge_base",
            description="Search internal IT documentation with citations.",
            args_schema=SearchArgs,
        ),
        StructuredTool.from_function(
            func=tool_check_system_status,
            name="check_system_status",
            description="Check live status of VPN/Email/Wi-Fi/Intranet.",
            args_schema=StatusArgs,
        ),
        StructuredTool.from_function(
            func=tool_create_ticket,
            name="create_ticket",
            description="Create an IT ticket for escalation.",
            args_schema=TicketArgs,
        ),
        StructuredTool.from_function(
            func=tool_lookup_ticket,
            name="lookup_ticket",
            description="Lookup ticket status by ID.",
            args_schema=LookupArgs,
        ),
        StructuredTool.from_function(
            func=tool_reset_password,
            name="reset_password",
            description="Reset password only after identity verification.",
            args_schema=ResetArgs,
        ),
    ]


def get_llm():
    if LLM_PROVIDER == "groq":
        from langchain_groq import ChatGroq

        return ChatGroq(api_key=GROQ_API_KEY, model=GROQ_MODEL, temperature=0.2)
    if LLM_PROVIDER == "openai":
        from langchain_openai import ChatOpenAI

        return ChatOpenAI(api_key=OPENAI_API_KEY, model=OPENAI_MODEL, temperature=0.2)
    raise RuntimeError("No LLM configured. Set GROQ_API_KEY or OPENAI_API_KEY in .env")


class AgentState(TypedDict):
    messages: Annotated[list, add_messages]


def build_agent():
    tools = _build_tools()
    llm = get_llm().bind_tools(tools)

    def assistant(state: AgentState):
        msgs = [SystemMessage(content=SYSTEM_PROMPT)] + state["messages"]
        response = llm.invoke(msgs)
        return {"messages": [response]}

    def should_continue(state: AgentState) -> Literal["tools", "end"]:
        last = state["messages"][-1]
        if isinstance(last, AIMessage) and last.tool_calls:
            return "tools"
        return "end"

    graph = StateGraph(AgentState)
    graph.add_node("assistant", assistant)
    graph.add_node("tools", ToolNode(tools))
    graph.set_entry_point("assistant")
    graph.add_conditional_edges("assistant", should_continue, {"tools": "tools", "end": END})
    graph.add_edge("tools", "assistant")
    return graph.compile()


_agent = None


def get_agent():
    global _agent
    if _agent is None:
        _agent = build_agent()
    return _agent


def _offline_fallback(user_text: str) -> dict[str, Any]:
    steps: list[str] = []
    lower = user_text.lower()

    status_snip = ""
    if any(w in lower for w in ["vpn", "email", "wifi", "wi-fi", "down", "outage"]):
        service = "vpn" if "vpn" in lower else "email" if "email" in lower else "wifi"
        status_snip = tool_check_system_status(service)
        steps.append(f"check_system_status({service})")

    hits = tool_search_knowledge_base(user_text)
    steps.append("search_knowledge_base")

    reset_snip = ""
    m = re.search(r"\b(E\d{4})\b", user_text.upper())
    if "password" in lower and ("reset" in lower or "expired" in lower):
        emp = m.group(1) if m else "UNKNOWN"
        reset_snip = tool_reset_password(emp, verified=bool(m))
        steps.append(f"reset_password({emp})")

    ticket_snip = ""
    if "ticket" in lower or "escalate" in lower or "GUARDRAIL BLOCKED" in reset_snip:
        ticket_snip = tool_create_ticket(summary=user_text[:160], priority="Medium", category="General")
        steps.append("create_ticket")

    answer = [
        "**Offline demo mode** (no LLM key). Showing RAG + tools pipeline:\n",
        "### Retrieved context\n",
        hits[:1200] + ("..." if len(hits) > 1200 else ""),
    ]
    if status_snip:
        answer += ["\n### System status\n", status_snip]
    if reset_snip:
        answer += ["\n### Password action\n", reset_snip]
    if ticket_snip:
        answer += ["\n### Ticket\n", ticket_snip]
    answer += [
        "\n### Suggested next steps\n",
        "1. Follow the cited IT guide steps above.\n",
        "2. If still blocked, keep the ticket ID and share it with IT.\n",
        "3. Add GROQ_API_KEY for full agent reasoning.",
    ]
    return {"answer": "\n".join(answer), "tool_trace": steps, "mode": "offline"}


def run_agent(user_text: str, history: list[dict[str, str]] | None = None) -> dict[str, Any]:
    history = history or []
    if not has_llm():
        return _offline_fallback(user_text)

    agent = get_agent()
    messages: list[Any] = []
    for turn in history[-6:]:
        if turn["role"] == "user":
            messages.append(HumanMessage(content=turn["content"]))
        else:
            messages.append(AIMessage(content=turn["content"]))
    messages.append(HumanMessage(content=user_text))

    result = agent.invoke({"messages": messages})
    final_messages = result["messages"]

    tool_trace: list[str] = []
    for msg in final_messages:
        if isinstance(msg, AIMessage) and msg.tool_calls:
            for tc in msg.tool_calls:
                tool_trace.append(f"{tc['name']}({json.dumps(tc.get('args', {}))})")
        if isinstance(msg, ToolMessage):
            tool_trace.append(f"-> {msg.name}: {str(msg.content)[:180]}")

    answer = ""
    for msg in reversed(final_messages):
        if isinstance(msg, AIMessage) and msg.content and not msg.tool_calls:
            answer = msg.content if isinstance(msg.content, str) else str(msg.content)
            break

    return {"answer": answer or "I could not generate a response.", "tool_trace": tool_trace, "mode": LLM_PROVIDER}
