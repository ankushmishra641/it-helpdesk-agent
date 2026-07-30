# IT Helpdesk Agent

### Agentic RAG assistant for internal IT support

An AI helpdesk that answers employee IT questions from company documentation and can take safe actions — check service status, create tickets, and reset passwords after identity verification.

Built with LangGraph agent orchestration, RAG over a vector store, a Streamlit UI, and a FastAPI backend.

---

## Problem

IT teams handle many repetitive Level-1 requests:

- VPN not connecting
- Password expired / account locked
- Wi-Fi issues
- Software install requests

This agent reduces that load by answering from internal docs and performing common support actions safely.

---

## Features

- RAG answers from internal IT docs (VPN, password, Wi-Fi, software, onboarding, FAQ)
- LangGraph agent loop (reason → tool call → observe → answer)
- Service status checks (VPN / Email / Wi-Fi / Intranet)
- Ticket create + lookup
- Guarded password reset (verified employee ID required)
- Streamlit chat UI
- REST API for integrations
- MCP-style tool server for reusable tools
- Offline fallback when no LLM key is set

---

## Architecture

```text
User (Streamlit / API)
        │
        ▼
 LangGraph Agent
        │
        ├── search_knowledge_base  → embeddings + vector search
        ├── check_system_status
        ├── create_ticket
        ├── lookup_ticket
        └── reset_password (guarded)
        │
        ▼
 Grounded response to user
```

---

## Tech Stack

| Layer | Technology |
|---|---|
| Language | Python 3.12 |
| UI | Streamlit |
| API | FastAPI + Uvicorn |
| Agent | LangGraph + LangChain |
| LLM | Groq (`llama-3.3-70b-versatile`) / OpenAI optional |
| Embeddings | FastEmbed (`all-MiniLM-L6-v2`) |
| Vector retrieval | In-memory cosine similarity index |
| Validation | Pydantic |
| Config | python-dotenv / Streamlit secrets |

---

## Project structure

```text
it-helpdesk-agent/
├── app.py                 # Streamlit UI
├── api.py                 # REST API
├── mcp_server.py          # MCP-style tool server
├── requirements.txt
├── .env.example
├── knowledge_base/        # Internal IT documents
└── src/
    ├── agent.py           # LangGraph agent
    ├── rag.py             # Ingestion + retrieval
    ├── tools.py           # Tools
    └── config.py          # Settings
```

---

## Quick start

```bash
git clone https://github.com/ankushmishra641/it-helpdesk-agent.git
cd it-helpdesk-agent

python -m venv .venv

# Windows
.venv\Scripts\activate

# macOS / Linux
source .venv/bin/activate

pip install -r requirements.txt
cp .env.example .env
```

Add your key in `.env`:

```env
GROQ_API_KEY=your_groq_api_key
LLM_PROVIDER=groq
```

Run UI:

```bash
streamlit run app.py
```

Open http://localhost:8501

Run API:

```bash
uvicorn api:app --reload --port 8000
```

Run MCP-style tools:

```bash
python mcp_server.py
```

---

## Example prompts

- `I can't connect to VPN — is the service down?`
- `How do I request new software?`
- `Please reset my password` → blocked by guardrail
- `Reset password for employee E1001` → allowed
- `Create a ticket for my slow laptop`

Verified demo employee IDs: `E1001`, `E1002`, `E2045`

---

## Deploy (Streamlit Cloud)

1. Open https://share.streamlit.io
2. Deploy repo `ankushmishra641/it-helpdesk-agent`
3. Branch: `master`
4. Main file: `app.py`
5. Add secret:

```toml
GROQ_API_KEY = "your_groq_api_key"
```

---

## Security notes

- Never commit `.env` or API keys
- Password reset requires verified identity
- For production, connect real ITSM / identity systems

---

## License

MIT
