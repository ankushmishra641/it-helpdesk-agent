"""Explicit configuration: no UI imports and no secret output."""
import os
from pathlib import Path
from dotenv import load_dotenv
ROOT_DIR = Path(__file__).resolve().parent.parent
load_dotenv(ROOT_DIR / '.env')
KB_DIR = ROOT_DIR / 'knowledge_base'
DATABASE_URL = os.getenv('DATABASE_URL', f'sqlite:///{ROOT_DIR / "helpdesk.db"}')
if DATABASE_URL.startswith(('postgres://', 'postgresql://')):
    DATABASE_URL = 'postgresql+psycopg://' + DATABASE_URL.split('://', 1)[1]
GROQ_API_KEY = os.getenv('GROQ_API_KEY', '').strip()
GROQ_MODEL = os.getenv('GROQ_MODEL', 'openai/gpt-oss-20b')
# A key alone must never silently enable spending.
LLM_PROVIDER = os.getenv('LLM_PROVIDER', 'none').lower()
TOP_K = 3
DAILY_LLM_LIMIT = int(os.getenv('DAILY_LLM_LIMIT', '100'))
SESSION_DAYS = 7
MAX_DAILY_SESSIONS = int(os.getenv('MAX_DAILY_SESSIONS', '50'))
if os.getenv('RENDER') and DATABASE_URL.startswith('sqlite'):
    raise RuntimeError('Render requires a persistent PostgreSQL DATABASE_URL. Local SQLite is for development only.')
def has_llm():
    return LLM_PROVIDER == 'groq' and bool(GROQ_API_KEY) and DAILY_LLM_LIMIT > 0
