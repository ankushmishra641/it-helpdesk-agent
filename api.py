"""
REST API for the IT Helpdesk Agent.
Run: uvicorn api:app --reload --port 8000
"""
from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.agent import run_agent
from src.config import LLM_PROVIDER, has_llm
from src.rag import build_or_load_store, search_knowledge_base
from src.tools import TOOL_SPECS

app = FastAPI(
    title="IT Helpdesk AI Agent API",
    description="RAG + LangGraph agentic IT support API",
    version="1.0.0",
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1)
    history: list[dict[str, str]] = Field(default_factory=list)


class ChatResponse(BaseModel):
    answer: str
    tool_trace: list[str]
    mode: str


@app.on_event("startup")
def startup() -> None:
    build_or_load_store()


@app.get("/health")
def health() -> dict[str, Any]:
    return {"status": "ok", "llm": LLM_PROVIDER if has_llm() else "offline", "rag": True}


@app.get("/tools")
def list_tools() -> dict[str, Any]:
    return {"tools": TOOL_SPECS}


@app.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest) -> ChatResponse:
    result = run_agent(req.message, req.history)
    return ChatResponse(**result)


@app.get("/search")
def search(q: str) -> dict[str, Any]:
    return {"query": q, "results": search_knowledge_base(q)}
