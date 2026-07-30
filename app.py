"""
IT Helpdesk Agent — internal support assistant
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import streamlit as st

from src.agent import run_agent
from src.config import LLM_PROVIDER, has_llm
from src.rag import build_or_load_store

st.set_page_config(
    page_title="IT Helpdesk Agent",
    page_icon="🛠️",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
      @import url('https://fonts.googleapis.com/css2?family=Source+Sans+3:wght@400;500;600;700&family=IBM+Plex+Sans:wght@400;500;600&display=swap');

      .stApp {
        background: #f4f6f9;
        color: #1a2332;
      }

      html, body, [class*="css"] {
        font-family: 'Source Sans 3', 'IBM Plex Sans', sans-serif;
      }

      [data-testid="stSidebar"] {
        background: #111827;
        border-right: 1px solid #1f2937;
      }

      [data-testid="stSidebar"] * {
        color: #e5e7eb !important;
      }

      [data-testid="stSidebar"] .stCaption, [data-testid="stSidebar"] p {
        color: #9ca3af !important;
      }

      .topbar {
        background: #ffffff;
        border: 1px solid #e5e7eb;
        border-radius: 12px;
        padding: 18px 22px;
        margin-bottom: 16px;
        display: flex;
        justify-content: space-between;
        align-items: center;
        gap: 16px;
      }

      .topbar-left h1 {
        margin: 0 !important;
        font-size: 1.35rem !important;
        font-weight: 700 !important;
        color: #111827 !important;
        letter-spacing: -0.02em;
      }

      .topbar-left p {
        margin: 4px 0 0 0 !important;
        color: #6b7280 !important;
        font-size: 0.92rem !important;
      }

      .status-dot {
        display: inline-flex;
        align-items: center;
        gap: 8px;
        background: #ecfdf5;
        color: #065f46 !important;
        border: 1px solid #a7f3d0;
        border-radius: 999px;
        padding: 6px 12px;
        font-size: 0.82rem;
        font-weight: 600;
        white-space: nowrap;
      }

      .status-dot::before {
        content: "";
        width: 8px;
        height: 8px;
        border-radius: 50%;
        background: #10b981;
      }

      .panel {
        background: #ffffff;
        border: 1px solid #e5e7eb;
        border-radius: 12px;
        padding: 16px 18px;
        margin-bottom: 14px;
      }

      .panel h3 {
        margin: 0 0 10px 0 !important;
        font-size: 0.95rem !important;
        color: #111827 !important;
        font-weight: 700 !important;
      }

      .panel p, .panel li {
        color: #4b5563 !important;
        font-size: 0.9rem !important;
        line-height: 1.5 !important;
      }

      .meta {
        display: grid;
        grid-template-columns: repeat(3, 1fr);
        gap: 10px;
        margin-bottom: 14px;
      }

      .meta-card {
        background: #ffffff;
        border: 1px solid #e5e7eb;
        border-radius: 10px;
        padding: 12px 14px;
      }

      .meta-card span {
        display: block;
        font-size: 0.75rem;
        color: #6b7280 !important;
        text-transform: uppercase;
        letter-spacing: 0.04em;
        font-weight: 600;
        margin-bottom: 4px;
      }

      .meta-card strong {
        color: #111827 !important;
        font-size: 0.95rem;
      }

      div[data-testid="stChatMessage"] {
        background: #ffffff;
        border: 1px solid #e5e7eb;
        border-radius: 12px;
      }

      .stButton > button {
        border-radius: 8px !important;
        border: 1px solid #374151 !important;
        background: #1f2937 !important;
        color: #f9fafb !important;
        font-weight: 600 !important;
      }

      .stButton > button:hover {
        background: #374151 !important;
        border-color: #4b5563 !important;
      }

      [data-testid="stChatInput"] {
        background: #ffffff;
      }

      h1, h2, h3, h4, p, label, span, div {
        color: #1a2332;
      }

      /* Keep main area readable; don't force white text globally */
      .stApp > header { background: transparent; }

      @media (max-width: 900px) {
        .meta { grid-template-columns: 1fr; }
        .topbar { flex-direction: column; align-items: flex-start; }
      }
    </style>
    """,
    unsafe_allow_html=True,
)

with st.sidebar:
    st.markdown("## IT Helpdesk")
    st.caption("Internal IT Support")
    st.divider()
    st.markdown("**Quick actions**")

    demos = {
        "VPN connectivity": "I can't connect to VPN — is the service down?",
        "Password reset": "Please reset my password",
        "Verified password reset": "Reset password for employee E1001",
        "Software access": "How do I request new software?",
        "Open a ticket": "Create a ticket for my slow laptop",
    }
    for label, text in demos.items():
        if st.button(label, use_container_width=True):
            st.session_state.pending_prompt = text

    st.divider()
    if st.button("Clear conversation", use_container_width=True):
        st.session_state.messages = []
        st.session_state.history = []
        st.rerun()

    if st.button("Refresh knowledge base", use_container_width=True):
        with st.spinner("Updating index..."):
            build_or_load_store(force_rebuild=True)
        st.success("Knowledge base updated.")

    st.divider()
    st.caption("Services monitored: VPN · Email · Wi‑Fi · Intranet")

# Header
engine = LLM_PROVIDER.upper() if has_llm() else "LOCAL"
st.markdown(
    f"""
    <div class="topbar">
      <div class="topbar-left">
        <h1>IT Helpdesk Support</h1>
        <p>Ask IT questions or request actions. Answers are grounded in internal documentation.</p>
      </div>
      <div class="status-dot">System online · {engine}</div>
    </div>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    """
    <div class="meta">
      <div class="meta-card"><span>Capability</span><strong>Knowledge answers</strong></div>
      <div class="meta-card"><span>Capability</span><strong>Status checks</strong></div>
      <div class="meta-card"><span>Capability</span><strong>Tickets & resets</strong></div>
    </div>
    """,
    unsafe_allow_html=True,
)

main, side = st.columns([1.7, 1], gap="medium")

with side:
    st.markdown(
        """
        <div class="panel">
          <h3>Available actions</h3>
          <p>
            • Search IT knowledge base<br/>
            • Check service status<br/>
            • Create support tickets<br/>
            • Lookup existing tickets<br/>
            • Password reset (identity required)
          </p>
        </div>
        <div class="panel">
          <h3>Security note</h3>
          <p>
            Sensitive actions require verification.
            Password resets are blocked unless a valid employee ID is confirmed.
          </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

with main:
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "history" not in st.session_state:
        st.session_state.history = []
    if "indexed" not in st.session_state:
        with st.spinner("Loading knowledge base..."):
            build_or_load_store()
        st.session_state.indexed = True

    if not st.session_state.messages:
        st.markdown(
            """
            <div class="panel">
              <h3>How can we help?</h3>
              <p>
                Describe your issue below, or use a quick action from the left menu.
                Examples: VPN not connecting, password expired, software install request.
              </p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
            if msg.get("trace"):
                with st.expander("Activity log"):
                    for line in msg["trace"]:
                        st.code(line, language="text")

    pending = st.session_state.pop("pending_prompt", None)
    prompt = st.chat_input("Describe your IT issue...")
    user_text = pending or prompt

    if user_text:
        st.session_state.messages.append({"role": "user", "content": user_text})
        with st.chat_message("user"):
            st.markdown(user_text)

        with st.chat_message("assistant"):
            with st.spinner("Working on your request..."):
                result = run_agent(user_text, st.session_state.history)
            st.markdown(result["answer"])
            if result.get("tool_trace"):
                with st.expander("Activity log", expanded=False):
                    for line in result["tool_trace"]:
                        st.code(line, language="text")

        st.session_state.messages.append(
            {
                "role": "assistant",
                "content": result["answer"],
                "trace": result.get("tool_trace", []),
            }
        )
        st.session_state.history.append({"role": "user", "content": user_text})
        st.session_state.history.append({"role": "assistant", "content": result["answer"]})
        st.rerun()
