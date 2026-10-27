"""Single-origin demo application: API + static portal."""
import asyncio
import logging
import threading
import time
from collections import defaultdict, deque
from contextlib import asynccontextmanager
from typing import Literal
from uuid import UUID
from fastapi import FastAPI, Request, HTTPException, Depends, Query
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field, ConfigDict, field_validator
from sqlalchemy import select
from src import database as db
from src import workflows
from src import conversation as support
from src.agent import run_agent
from src.catalog import catalog
from src.config import ROOT_DIR, has_llm
from src.rag import list_articles, search_knowledge_base, build_or_load_store
logger = logging.getLogger('helpdesk')
_rate_lock = threading.Lock()
_rates = {}
def throttle(key, limit, window=60):
    now = time.monotonic()
    with _rate_lock:
        if len(_rates) > 5000:
            for old in list(_rates):
                if not _rates[old] or now - _rates[old][-1] > 3600:
                    del _rates[old]
            if len(_rates) > 5000 and key not in _rates:
                raise HTTPException(429, 'Demo is busy. Please try again later.')
        queue = _rates.setdefault(key, deque())
        while queue and queue[0] <= now - window:
            queue.popleft()
        if len(queue) >= limit:
            raise HTTPException(429, 'Too many requests. Please wait before trying again.', headers={'Retry-After': str(window)})
        queue.append(now)
@asynccontextmanager
async def lifespan(app):
    db.init_db()
    build_or_load_store()
    catalog()
    yield
app = FastAPI(title='Northstar IT • Public demo', version='2.0.0', lifespan=lifespan, docs_url=None, redoc_url=None, openapi_url=None)
class StrictModel(BaseModel):
    model_config = ConfigDict(extra='forbid', str_strip_whitespace=True)
class ChatRequest(StrictModel):
    message: str = Field(min_length=2, max_length=1500)
class AssistantRequest(ChatRequest):
    request_key: UUID
    case_id: str | None = Field(default=None, max_length=40)
    revision: int | None = Field(default=None, ge=0, le=100)
    action: Literal['internet_yes', 'internet_no', 'approve', 'escalate', 'resolved', 'still_failing', 'helped', 'not_helped'] | None = None
class TicketRequest(StrictModel):
    summary: str = Field(min_length=5, max_length=160)
    description: str = Field(min_length=10, max_length=3000)
    category: Literal['Network', 'Identity', 'Software', 'Hardware', 'General'] = 'General'
    priority: Literal['Low', 'Medium', 'High'] = 'Medium'
    request_key: UUID
    investigate: bool = True
class WorkflowStart(StrictModel):
    kind: Literal['vpn', 'account', 'software']
class WorkflowAction(StrictModel):
    revision: int = Field(ge=0, le=30)
    action: Literal['diagnose', 'internet_down', 'outage', 'unapproved', 'approve', 'escalate', 'resolved', 'still_failing']
def session(request: Request):
    token = request.headers.get('X-Demo-Token', '')
    sid = db.identify(token)
    if not sid:
        raise HTTPException(401, 'Your demo session has expired. Start a new demo session.')
    return sid
@app.middleware('http')
async def protections(request, call_next):
    # Bound actual body bytes, including requests without Content-Length.
    if request.method in {'POST', 'PUT', 'PATCH'}:
        parts = []
        size = 0
        async for part in request.stream():
            size += len(part)
            if size > 16384:
                return JSONResponse({'detail': 'Request is too large.'}, status_code=413)
            parts.append(part)
        request._body = b''.join(parts)
    try:
        if request.url.path.startswith('/api/'):
            throttle('ip:' + (request.client.host if request.client else 'unknown'), 120)
        response = await call_next(request)
    except HTTPException as error:
        response = JSONResponse({'detail': error.detail}, status_code=error.status_code, headers=error.headers)
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['Referrer-Policy'] = 'same-origin'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['Content-Security-Policy'] = "default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; connect-src 'self'; frame-ancestors 'none'; base-uri 'self'; form-action 'self'"
    response.headers['Permissions-Policy'] = 'camera=(), microphone=(), geolocation=()'
    if request.url.path.startswith('/api/'):
        response.headers['Cache-Control'] = 'no-store'
    return response
@app.exception_handler(Exception)
async def unexpected(request, exc):
    # Do not log request bodies, tokens, SQL parameters, or provider exceptions.
    logger.error('Request failed: %s', type(exc).__name__)
    return JSONResponse({'detail': 'The service is temporarily unavailable. Please try again.'}, status_code=503)
@app.get('/health')
def health():
    try:
        with db.engine.connect() as c:
            c.execute(select(db.versions.c.version)).first()
        return {'status': 'ok', 'mode': 'public-demo', 'knowledge_articles': len(list_articles())}
    except Exception:
        raise HTTPException(503, 'Database is unavailable.')
@app.post('/api/session')
def start_session(request: Request):
    throttle('session:' + (request.client.host if request.client else 'unknown'), 10, 3600)
    try:
        return {'token': db.new_session(), 'expires_in_days': 7}
    except ValueError as error:
        raise HTTPException(429, str(error))
@app.delete('/api/session')
def delete_session(sid=Depends(session)):
    db.clear_session(sid)
    return {'deleted': True}
@app.get('/api/bootstrap')
def bootstrap(sid=Depends(session)):
    data = catalog()
    return {'company': data['company'], 'services': data['services'], 'incidents': data['incidents'],
            'counts': {key: len(data[key]) for key in ['employees', 'assets', 'tickets', 'services']},
            'articles': len(list_articles()), 'ai_available': has_llm(), 'tickets': db.list_tickets(sid),
            'active_case': support.public(support.active(sid))}
@app.get('/api/history')
def chat_history(sid=Depends(session)):
    return {'messages': db.history(sid)}
@app.post('/api/chat')
def chat(req: ChatRequest, sid=Depends(session)):
    throttle('chat:' + sid, 8)
    if not db.consume_chat(sid):
        raise HTTPException(429, 'Your demo session has reached its 80-message allowance.')
    result = run_agent(req.message, db.history(sid), session_id=sid)
    db.save_turn(sid, req.message, result['answer'])
    return result
@app.post('/api/assist')
def assist(req: AssistantRequest, sid=Depends(session)):
    throttle('assist:' + sid, 20)
    if not db.consume_chat(sid):
        raise HTTPException(429, 'Your demo session has reached its 80-message allowance.')
    try:
        return support.handle(sid, req.message, str(req.request_key), req.case_id, req.revision, req.action)
    except LookupError as error:
        raise HTTPException(404, str(error))
    except ValueError as error:
        raise HTTPException(409, str(error))
@app.post('/api/tickets/{ticket_id}/continue')
def continue_case(ticket_id: str, sid=Depends(session)):
    throttle('workflow:' + sid, 20)
    try:
        with support.lock(sid):
            return support.response(sid, support.investigate_ticket(sid, ticket_id))
    except LookupError as error:
        raise HTTPException(404, str(error))
    except ValueError as error:
        raise HTTPException(409, str(error))
@app.get('/api/tickets')
def ticket_list(sid=Depends(session)):
    return {'tickets': db.list_tickets(sid)}
@app.get('/api/tickets/{ticket_id}')
def ticket_detail(ticket_id: str, sid=Depends(session)):
    ticket = db.get_ticket(sid, ticket_id)
    if not ticket:
        raise HTTPException(404, 'Ticket not found.')
    return {**ticket, 'workflow': support.public(w) if (w := workflows.get(sid, ticket_id)) else None,
            'suggested_workflow': workflows.suggest(ticket['summary'] + ' ' + ticket['description'])}
@app.post('/api/tickets/{ticket_id}/workflow')
def start_workflow(ticket_id: str, req: WorkflowStart, sid=Depends(session)):
    throttle('workflow:' + sid, 20)
    try:
        return workflows.public(workflows.start(sid, ticket_id, req.kind))
    except LookupError as error:
        raise HTTPException(404, str(error))
    except ValueError as error:
        raise HTTPException(409, str(error))
@app.post('/api/tickets/{ticket_id}/workflow/action')
def workflow_action(ticket_id: str, req: WorkflowAction, sid=Depends(session)):
    throttle('workflow:' + sid, 20)
    try:
        return workflows.public(workflows.advance(sid, ticket_id, req.revision, req.action))
    except LookupError as error:
        raise HTTPException(404, str(error))
    except ValueError as error:
        raise HTTPException(409, str(error))
@app.post('/api/tickets', status_code=201)
def new_ticket(req: TicketRequest, sid=Depends(session)):
    throttle('ticket:' + sid, 10)
    try:
        with support.lock(sid):
            ticket = db.create_ticket(sid, req.model_dump(exclude={'request_key', 'investigate'}), str(req.request_key))
            if req.investigate:
                state = support.investigate_ticket(sid, ticket['id'])
                return {**db.get_ticket(sid, ticket['id']), 'assistant': support.response(sid, state)}
            return ticket
    except ValueError as error:
        raise HTTPException(409, str(error))
@app.get('/api/knowledge')
def knowledge(q: str = Query('', max_length=200), sid=Depends(session)):
    docs = search_knowledge_base(q, k=20) if q.strip() else list_articles()
    return {'articles': [{k: v for k, v in d.items() if k != 'content'} for d in docs]}
@app.get('/api/knowledge/{article_id}')
def article(article_id: str, sid=Depends(session)):
    result = next((a for a in list_articles() if a['id'] == article_id), None)
    if not result:
        raise HTTPException(404, 'Article not found.')
    return result
@app.get('/api/demo-records')
def records(q: str = Query('', max_length=120), page: int = Query(1, ge=1, le=100), sid=Depends(session)):
    data = catalog()['tickets']
    if q:
        data = [t for t in data if q.lower() in (t['summary'] + ' ' + t['id'] + ' ' + t['category'] + ' ' + t['status']).lower()]
    return {'records': data[(page-1)*20:page*20], 'total': len(data), 'page': page}
app.mount('/assets', StaticFiles(directory=ROOT_DIR / 'web'), name='assets')
@app.get('/')
def home():
    return FileResponse(ROOT_DIR / 'web' / 'index.html')
