"""Persistent session-scoped demo records, for SQLite and PostgreSQL."""
import hashlib
import json
import secrets
import time
import uuid
from datetime import datetime, timezone
from sqlalchemy import create_engine, MetaData, Table, Column, String, Integer, Text, ForeignKey, UniqueConstraint, select, update, delete, insert, event
from sqlalchemy.exc import IntegrityError
from src.config import DATABASE_URL, SESSION_DAYS, DAILY_LLM_LIMIT, MAX_DAILY_SESSIONS
engine = create_engine(DATABASE_URL, pool_pre_ping=True,
    connect_args={'check_same_thread': False, 'timeout': 20} if DATABASE_URL.startswith('sqlite') else {'connect_timeout': 10})
if DATABASE_URL.startswith('sqlite'):
    @event.listens_for(engine, 'connect')
    def configure_sqlite(connection, record):
        connection.execute('PRAGMA foreign_keys=ON')
metadata = MetaData(schema='helpdesk' if DATABASE_URL.startswith('postgresql') else None)
sessions = Table('demo_sessions', metadata,
    Column('id', String(64), primary_key=True), Column('expires', Integer, nullable=False),
    Column('chat_count', Integer, nullable=False, default=0), Column('ticket_count', Integer, nullable=False, default=0))
tickets = Table('tickets', metadata,
    Column('id', String(40), primary_key=True),
    Column('session_id', String(64), ForeignKey('demo_sessions.id', ondelete='CASCADE'), nullable=False, index=True),
    Column('summary', String(160), nullable=False), Column('description', Text, nullable=False),
    Column('category', String(30), nullable=False), Column('priority', String(10), nullable=False),
    Column('status', String(20), nullable=False), Column('created_at', String(40), nullable=False),
    Column('request_key', String(36), nullable=False), Column('fingerprint', String(64), nullable=False),
    UniqueConstraint('session_id', 'request_key'))
messages = Table('messages', metadata,
    Column('id', String(40), primary_key=True),
    Column('session_id', String(64), ForeignKey('demo_sessions.id', ondelete='CASCADE'), nullable=False, index=True),
    Column('role', String(20), nullable=False), Column('content', Text, nullable=False),
    Column('created_at', String(40), nullable=False))
audit = Table('audit_events', metadata,
    Column('id', String(40), primary_key=True),
    Column('session_id', String(64), ForeignKey('demo_sessions.id', ondelete='CASCADE'), nullable=False),
    Column('action', String(50), nullable=False), Column('resource', String(40), nullable=False),
    Column('created_at', String(40), nullable=False))
budgets = Table('llm_daily_budget', metadata, Column('day', String(10), primary_key=True), Column('used', Integer, nullable=False))
versions = Table('schema_version', metadata, Column('version', Integer, primary_key=True))
session_budget = Table('session_daily_budget', metadata, Column('day', String(10), primary_key=True), Column('used', Integer, nullable=False))
workflows = Table('case_workflows', metadata,
    Column('ticket_id', String(40), ForeignKey('tickets.id', ondelete='CASCADE'), primary_key=True),
    Column('session_id', String(64), ForeignKey('demo_sessions.id', ondelete='CASCADE'), nullable=False),
    Column('revision', Integer, nullable=False), Column('state', Text, nullable=False))
active_cases = Table('active_cases', metadata,
    Column('session_id', String(64), ForeignKey('demo_sessions.id', ondelete='CASCADE'), primary_key=True),
    Column('ticket_id', String(40), ForeignKey('tickets.id', ondelete='CASCADE'), nullable=False))
assistant_requests = Table('assistant_requests', metadata,
    Column('session_id', String(64), ForeignKey('demo_sessions.id', ondelete='CASCADE'), primary_key=True),
    Column('request_key', String(36), primary_key=True), Column('fingerprint', String(64), nullable=False),
    Column('response', Text, nullable=False))
def now():
    return datetime.now(timezone.utc).isoformat()
def init_db():
    if metadata.schema:
        from sqlalchemy.schema import CreateSchema
        with engine.begin() as c:
            c.execute(CreateSchema(metadata.schema, if_not_exists=True))
    metadata.create_all(engine)
    with engine.begin() as c:
        if c.scalar(select(versions.c.version)) is None:
            c.execute(insert(versions).values(version=1))
        c.execute(delete(sessions).where(sessions.c.expires < int(time.time())))
def new_session():
    if not reserve_daily(session_budget, MAX_DAILY_SESSIONS):
        raise ValueError('The daily demo-session allowance is full. Please return tomorrow (UTC).')
    token = secrets.token_urlsafe(32)
    sid = hashlib.sha256(token.encode()).hexdigest()
    with engine.begin() as c:
        c.execute(delete(sessions).where(sessions.c.expires < int(time.time())))
        c.execute(insert(sessions).values(id=sid, expires=int(time.time()) + SESSION_DAYS * 86400, chat_count=0, ticket_count=0))
    return token
def identify(token):
    if not token or len(token) > 100:
        return None
    sid = hashlib.sha256(token.encode()).hexdigest()
    with engine.connect() as c:
        return c.scalar(select(sessions.c.id).where(sessions.c.id == sid, sessions.c.expires > int(time.time())))
def consume_chat(sid):
    with engine.begin() as c:
        return c.execute(update(sessions).where(sessions.c.id == sid, sessions.c.chat_count < 80)
                         .values(chat_count=sessions.c.chat_count + 1)).rowcount == 1
def reserve_llm():
    return reserve_daily(budgets, DAILY_LLM_LIMIT)
def reserve_daily(table, limit):
    day = now()[:10]
    try:
        with engine.begin() as c:
            c.execute(insert(table).values(day=day, used=0))
    except IntegrityError:
        pass
    with engine.begin() as c:
        c.execute(delete(table).where(table.c.day < day))
        return c.execute(update(table).where(table.c.day == day, table.c.used < limit)
                         .values(used=table.c.used + 1)).rowcount == 1
def public_ticket(row):
    return {k: v for k, v in dict(row).items() if k not in {'session_id', 'request_key', 'fingerprint'}}
def list_tickets(sid):
    with engine.connect() as c:
        rows = c.execute(select(tickets).where(tickets.c.session_id == sid).order_by(tickets.c.created_at.desc())).mappings()
        return [public_ticket(r) for r in rows]
def get_ticket(sid, ticket_id):
    with engine.connect() as c:
        row = c.execute(select(tickets).where(tickets.c.session_id == sid, tickets.c.id == ticket_id)).mappings().first()
        return public_ticket(row) if row else None
def create_ticket(sid, data, request_key):
    fingerprint = hashlib.sha256(json.dumps(data, sort_keys=True).encode()).hexdigest()
    def existing(c):
        row = c.execute(select(tickets).where(tickets.c.session_id == sid, tickets.c.request_key == request_key)).mappings().first()
        if row and row['fingerprint'] != fingerprint:
            raise ValueError('This request key was already used for a different ticket.')
        return public_ticket(row) if row else None
    try:
        with engine.begin() as c:
            previous = existing(c)
            if previous:
                return previous
            if c.execute(update(sessions).where(sessions.c.id == sid, sessions.c.ticket_count < 20)
                         .values(ticket_count=sessions.c.ticket_count + 1)).rowcount != 1:
                raise ValueError('This demo session has reached its 20-ticket limit.')
            row = dict(id='INC-' + uuid.uuid4().hex[:16].upper(), session_id=sid, **data,
                       status='Open', created_at=now(), request_key=request_key, fingerprint=fingerprint)
            c.execute(insert(tickets).values(**row))
            c.execute(insert(audit).values(id=uuid.uuid4().hex, session_id=sid, action='ticket.created', resource=row['id'], created_at=now()))
            return public_ticket(row)
    except IntegrityError:
        with engine.connect() as c:
            previous = existing(c)
            if previous:
                return previous
        raise
def save_turn(sid, question, answer):
    with engine.begin() as c:
        for role, content in [('user', question), ('assistant', answer)]:
            c.execute(insert(messages).values(id=uuid.uuid4().hex, session_id=sid, role=role, content=content[:12000], created_at=now()))
def history(sid):
    with engine.connect() as c:
        rows = c.execute(select(messages.c.role, messages.c.content).where(messages.c.session_id == sid)
                         .order_by(messages.c.created_at.desc()).limit(12)).mappings().all()
        return [dict(r) for r in reversed(rows)]
def clear_session(sid):
    with engine.begin() as c:
        c.execute(delete(sessions).where(sessions.c.id == sid))
