"""
IT Helpdesk Agent — internal support assistant
"""
from __future__ import annotations

import html
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

st.info('Legacy local interface. The public portal runs with: uvicorn api:app --port 8000. All IT services are fictional; real password resets are disabled.')

st.markdown(
    """
    <style>
      @import url('https://fonts.googleapis.com/css2?family=DM+Sans:ital,opsz,wght@0,9..40,400;0,9..40,500;0,9..40,600;0,9..40,700;1,9..40,400&family=IBM+Plex+Mono:wght@400;500;600&display=swap');

      .stApp {
        background:
          radial-gradient(1200px 500px at 10% -10%, #dbeafe 0%, transparent 55%),
          radial-gradient(900px 420px at 100% 0%, #ccfbf1 0%, transparent 50%),
          linear-gradient(180deg, #eef2f7 0%, #f7f9fc 40%, #f3f5f8 100%);
        color: #0f172a;
      }

      html, body, [class*="css"] {
        font-family: 'DM Sans', system-ui, sans-serif;
      }

      .stApp > header { background: transparent; }
      #MainMenu, footer { visibility: hidden; }

      /* Sidebar */
      [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0b1220 0%, #111827 55%, #0f172a 100%);
        border-right: 1px solid #1e293b;
      }
      [data-testid="stSidebar"] * { color: #e2e8f0 !important; }
      [data-testid="stSidebar"] .stCaption,
      [data-testid="stSidebar"] [data-testid="stCaption"] {
        color: #94a3b8 !important;
      }
      [data-testid="stSidebar"] .stButton > button {
        background: #1e293b !important;
        border: 1px solid #334155 !important;
        color: #f8fafc !important;
        border-radius: 10px !important;
        font-weight: 600 !important;
        transition: background 0.15s ease, border-color 0.15s ease, transform 0.12s ease;
      }
      [data-testid="stSidebar"] .stButton > button:hover {
        background: #243447 !important;
        border-color: #475569 !important;
        transform: translateY(-1px);
      }

      /* Top bar */
      .topbar {
        background: rgba(255,255,255,0.86);
        backdrop-filter: blur(10px);
        border: 1px solid #e2e8f0;
        border-radius: 16px;
        padding: 20px 24px;
        margin-bottom: 14px;
        display: flex;
        justify-content: space-between;
        align-items: center;
        gap: 16px;
        box-shadow: 0 10px 30px rgba(15, 23, 42, 0.04);
      }
      .brand-mark {
        display: inline-flex;
        align-items: center;
        gap: 10px;
        margin-bottom: 6px;
      }
      .brand-mark .logo {
        width: 34px;
        height: 34px;
        border-radius: 10px;
        background: linear-gradient(145deg, #0f766e, #0ea5e9);
        color: #fff !important;
        display: inline-flex;
        align-items: center;
        justify-content: center;
        font-weight: 700;
        font-size: 0.85rem;
        letter-spacing: 0.02em;
      }
      .brand-mark .name {
        font-size: 0.78rem;
        font-weight: 700;
        letter-spacing: 0.08em;
        text-transform: uppercase;
        color: #64748b !important;
      }
      .topbar-left h1 {
        margin: 0 !important;
        font-size: 1.55rem !important;
        font-weight: 700 !important;
        color: #0f172a !important;
        letter-spacing: -0.03em;
        line-height: 1.15 !important;
      }
      .topbar-left p {
        margin: 6px 0 0 0 !important;
        color: #64748b !important;
        font-size: 0.95rem !important;
      }
      .status-dot {
        display: inline-flex;
        align-items: center;
        gap: 8px;
        background: #ecfdf5;
        color: #065f46 !important;
        border: 1px solid #a7f3d0;
        border-radius: 999px;
        padding: 8px 14px;
        font-size: 0.82rem;
        font-weight: 700;
        white-space: nowrap;
      }
      .status-dot::before {
        content: "";
        width: 8px;
        height: 8px;
        border-radius: 50%;
        background: #10b981;
        box-shadow: 0 0 0 4px rgba(16,185,129,0.18);
      }

      .meta {
        display: grid;
        grid-template-columns: repeat(3, 1fr);
        gap: 10px;
        margin-bottom: 16px;
      }
      .meta-card {
        background: rgba(255,255,255,0.9);
        border: 1px solid #e2e8f0;
        border-radius: 12px;
        padding: 14px 16px;
        box-shadow: 0 6px 18px rgba(15, 23, 42, 0.03);
      }
      .meta-card span {
        display: block;
        font-size: 0.72rem;
        color: #64748b !important;
        text-transform: uppercase;
        letter-spacing: 0.06em;
        font-weight: 700;
        margin-bottom: 5px;
      }
      .meta-card strong {
        color: #0f172a !important;
        font-size: 0.98rem;
        font-weight: 700;
      }

      .panel {
        background: rgba(255,255,255,0.92);
        border: 1px solid #e2e8f0;
        border-radius: 14px;
        padding: 18px 18px;
        margin-bottom: 12px;
        box-shadow: 0 8px 22px rgba(15, 23, 42, 0.035);
      }
      .panel h3 {
        margin: 0 0 10px 0 !important;
        font-size: 0.92rem !important;
        color: #0f172a !important;
        font-weight: 700 !important;
      }
      .panel p, .panel li {
        color: #475569 !important;
        font-size: 0.9rem !important;
        line-height: 1.55 !important;
      }

      /* Chat messages */
      div[data-testid="stChatMessage"] {
        background: rgba(255,255,255,0.95);
        border: 1px solid #e2e8f0;
        border-radius: 16px;
        padding: 4px 2px;
        box-shadow: 0 8px 24px rgba(15, 23, 42, 0.04);
        margin-bottom: 10px;
      }
      div[data-testid="stChatMessage"] p,
      div[data-testid="stChatMessage"] li,
      div[data-testid="stChatMessage"] strong {
        color: #0f172a !important;
      }

      /* Expander */
      [data-testid="stExpander"] {
        background: #f8fafc;
        border: 1px solid #e2e8f0 !important;
        border-radius: 12px !important;
        overflow: hidden;
      }
      [data-testid="stExpander"] details {
        border: none !important;
      }
      [data-testid="stExpander"] summary,
      [data-testid="stExpander"] summary span,
      [data-testid="stExpander"] summary p {
        color: #0f172a !important;
        font-weight: 700 !important;
      }

      /* Activity log shell */
      .activity-shell {
        background: #0b1220;
        border: 1px solid #1e293b;
        border-radius: 12px;
        padding: 12px;
        margin-top: 4px;
      }
      .activity-shell .activity-title {
        color: #94a3b8 !important;
        font-size: 0.72rem;
        font-weight: 700;
        letter-spacing: 0.08em;
        text-transform: uppercase;
        margin: 0 0 10px 0 !important;
        font-family: 'DM Sans', sans-serif !important;
      }

      /* Chat composer */
      [data-testid="stBottomBlockContainer"],
      [data-testid="stChatInput"] {
        background: transparent !important;
      }
      div[data-testid="stChatInput"] > div {
        background: #0f172a !important;
        border: 1px solid #1e293b !important;
        border-radius: 18px !important;
        padding: 10px 12px !important;
        box-shadow: 0 16px 40px rgba(15, 23, 42, 0.18) !important;
      }
      div[data-testid="stChatInput"] textarea,
      div[data-testid="stChatInput"] textarea:focus,
      div[data-testid="stChatInput"] textarea:focus-visible {
        color: #0f172a !important;
        caret-color: #0f172a !important;
        background: #ffffff !important;
        border: 1px solid #cbd5e1 !important;
        border-radius: 12px !important;
        font-size: 0.98rem !important;
        font-family: 'DM Sans', sans-serif !important;
        box-shadow: none !important;
        outline: none !important;
        resize: none !important;
      }
      div[data-testid="stChatInput"] textarea::placeholder {
        color: #64748b !important;
        opacity: 1 !important;
      }
      div[data-testid="stChatInput"] button {
        background: linear-gradient(145deg, #0f766e, #0284c7) !important;
        border: none !important;
        border-radius: 12px !important;
        color: #ffffff !important;
        width: 42px !important;
        height: 42px !important;
      }
      div[data-testid="stChatInput"] button:hover {
        filter: brightness(1.08);
      }
      div[data-testid="stChatInput"] button svg {
        fill: #ffffff !important;
        color: #ffffff !important;
      }

      .stButton > button {
        border-radius: 10px !important;
        border: 1px solid #334155 !important;
        background: #1e293b !important;
        color: #f8fafc !important;
        font-weight: 600 !important;
      }

      @media (max-width: 900px) {
        .meta { grid-template-columns: 1fr; }
        .topbar { flex-direction: column; align-items: flex-start; }
      }
    </style>
    """,
    unsafe_allow_html=True,
)


def render_activity_log(trace: list[str]) -> None:
    """High-contrast terminal-style tool trace (inline styles = reliable in Streamlit)."""
    rows: list[str] = []
    for line in trace:
        text = html.escape(str(line))
        is_result = str(line).startswith("->")
        if is_result:
            color = "#86efac" if "GUARDRAIL" not in str(line).upper() else "#fbbf24"
            label = "RESULT"
            label_color = "#4ade80" if "GUARDRAIL" not in str(line).upper() else "#fbbf24"
        else:
            color = "#e2e8f0"
            label = "TOOL"
            label_color = "#38bdf8"
        rows.append(
            f"""
            <div style="
              display:flex; gap:10px; align-items:flex-start;
              background:#111827; border:1px solid #1f2937; border-radius:10px;
              padding:10px 12px; margin:0 0 8px 0;">
              <span style="
                flex:0 0 auto; font-family:'IBM Plex Mono',monospace; font-size:0.68rem;
                font-weight:600; letter-spacing:0.06em; color:{label_color};
                background:#0b1220; border:1px solid #1e293b; border-radius:6px;
                padding:3px 7px; margin-top:1px;">{label}</span>
              <pre style="
                margin:0; padding:0; background:transparent; border:none;
                color:{color}; font-family:'IBM Plex Mono',ui-monospace,monospace;
                font-size:0.8rem; line-height:1.5; white-space:pre-wrap;
                word-break:break-word; overflow-wrap:anywhere;">{text}</pre>
            </div>
            """
        )
    st.markdown(
        f"""
        <div class="activity-shell">
          <p class="activity-title">Agent tool activity</p>
          {''.join(rows)}
        </div>
        """,
        unsafe_allow_html=True,
    )


with st.sidebar:
    st.markdown("## IT Helpdesk")
    st.caption("Internal IT Support Console")
    st.divider()
    st.markdown("**Quick actions**")

    demos = {
        "VPN connectivity": "I can't connect to VPN — is the service down?",
        "Password reset": "Please reset my password",
        "Account access guide": "How can I recover access to my account?",
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
    st.caption("Monitored · VPN · Email · Wi‑Fi · Intranet")

engine = LLM_PROVIDER.upper() if has_llm() else "LOCAL"
st.markdown(
    f"""
    <div class="topbar">
      <div class="topbar-left">
        <div class="brand-mark">
          <span class="logo">IT</span>
          <span class="name">Helpdesk Agent</span>
        </div>
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

main, side = st.columns([1.75, 1], gap="medium")

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
            Real password resets are disabled in this public demonstration.
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
                with st.expander("Activity log", expanded=False):
                    render_activity_log(msg["trace"])

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
                with st.expander("Activity log", expanded=True):
                    render_activity_log(result["tool_trace"])

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
