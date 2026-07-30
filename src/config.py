"""App configuration — env vars + Streamlit Cloud secrets."""
from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

ROOT_DIR = Path(__file__).resolve().parent.parent
KB_DIR = ROOT_DIR / "knowledge_base"
CHROMA_DIR = ROOT_DIR / ".chroma"


def _secret(name: str, default: str = "") -> str:
    value = os.getenv(name, "").strip()
    if value:
        return value
    try:
        import streamlit as st

        if hasattr(st, "secrets") and name in st.secrets:
            return str(st.secrets[name]).strip()
    except Exception:
        pass
    return default


GROQ_API_KEY = _secret("GROQ_API_KEY")
OPENAI_API_KEY = _secret("OPENAI_API_KEY")

LLM_PROVIDER = _secret("LLM_PROVIDER").lower()
if not LLM_PROVIDER:
    if GROQ_API_KEY:
        LLM_PROVIDER = "groq"
    elif OPENAI_API_KEY:
        LLM_PROVIDER = "openai"
    else:
        LLM_PROVIDER = "none"

GROQ_MODEL = _secret("GROQ_MODEL", "llama-3.3-70b-versatile")
OPENAI_MODEL = _secret("OPENAI_MODEL", "gpt-4o-mini")
# FastEmbed is lighter than PyTorch sentence-transformers (better for free cloud hosts)
EMBEDDING_MODEL = _secret("EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2")
TOP_K = int(_secret("TOP_K", "4") or "4")


def has_llm() -> bool:
    return LLM_PROVIDER in {"groq", "openai"} and (
        (LLM_PROVIDER == "groq" and bool(GROQ_API_KEY))
        or (LLM_PROVIDER == "openai" and bool(OPENAI_API_KEY))
    )
