"""One conversation, one selected case. Consent is never inferred by an LLM."""
import copy
import hashlib
import json
import re
import threading
import uuid
from sqlalchemy import select, insert, delete
from src import database as db, workflows as wf
from src.agent import run_agent
from src.rag import search_knowledge_base

# Deployment uses one worker. Durable revisions also guard tool execution.
locks = [threading.RLock() for _ in range(64)]
def lock(sid):
    return locks[int(sid[:8], 16) % len(locks)]

def select_case(sid, ticket_id):
    if not db.get_ticket(sid, ticket_id):
        raise LookupError('Ticket not found.')
    with db.engine.begin() as c:
        c.execute(delete(db.active_cases).where(db.active_cases.c.session_id == sid))
        c.execute(insert(db.active_cases).values(session_id=sid, ticket_id=ticket_id))

def active(sid):
    with db.engine.connect() as c:
        ticket_id = c.scalar(select(db.active_cases.c.ticket_id).where(db.active_cases.c.session_id == sid))
    return wf.get(sid, ticket_id) if ticket_id else None

def public(state):
    if not state:
        return None
    data = wf.public(state) if state['kind'] != 'guidance' else {**state, 'actions': []}
    if state['stage'] == 'intake':
        data['actions'] = ([{'id': 'internet_yes', 'label': 'Yes, internet works'},
                            {'id': 'internet_no', 'label': 'No, internet also fails'}]
                           if state.get('missing') == 'internet' else [])
    elif state['stage'] == 'guidance':
        data['actions'] = [{'id': 'helped', 'label': 'That solved it'}, {'id': 'not_helped', 'label': 'Still not working'}]
    elif state['stage'] == 'needs_detail':
        data['actions'] = [{'id': 'escalate', 'label': 'Escalate for specialist review'}]
    return data

def response(sid, state, prefix=''):
    ticket = db.get_ticket(sid, state['ticket_id'])
    explanation = state['explanation']
    if state['stage'] == 'proposed':
        if state['proposal'] == 'verify_identity':
            explanation += '\nMay I complete the simulated identity-verification step? No real credentials are needed.'
        elif state['proposal'] != 'escalate':
            explanation += '\nDo you approve this action on the demo resource?'
    return {'answer': prefix + explanation, 'mode': state['mode'], 'sources': state['sources'],
            'tool_trace': [e['event'] + ': ' + e['note'] for e in state['events'][-3:]],
            'action': None, 'case': public(state), 'ticket': ticket}

def guidance(sid, ticket, existing=None, detail=''):
    text = ticket['summary'] + '\n' + ticket['description'] + '\n' + detail
    result = run_agent(text[:1500], session_id=sid)
    state = copy.deepcopy(existing) if existing else dict(ticket_id=ticket['id'], kind='guidance', revision=0,
              summary=ticket['summary'], description=ticket['description'], events=[], resource={}, proposal=None, verification=None)
    state.update(stage='guidance' if result['sources'] else 'needs_detail', mode=result['mode'],
                 explanation=(result['answer'] + '\nDid these steps solve the issue?') if result['sources'] else
                 'I could not find an approved procedure for that issue. Which application or device is affected, and what exact error do you see?',
                 sources=result['sources'])
    wf.event(state, 'Guidance prepared', 'Retrieved approved documentation.' if result['sources'] else 'No matching procedure; clarification requested.')
    if existing:
        return wf.save(sid, existing, state, 'Waiting', 'guidance')
    with db.engine.begin() as c:
        c.execute(insert(db.workflows).values(ticket_id=ticket['id'], session_id=sid, revision=0, state=json.dumps(state)))
        c.execute(db.tickets.update().where(db.tickets.c.id == ticket['id'], db.tickets.c.session_id == sid).values(status='Waiting'))
    return state

def investigate_ticket(sid, ticket_id):
    ticket = db.get_ticket(sid, ticket_id)
    if not ticket:
        raise LookupError('Ticket not found.')
    state = wf.get(sid, ticket_id)
    if not state:
        kind = wf.suggest(ticket['summary'] + ' ' + ticket['description'])
        state = wf.start(sid, ticket_id, kind) if kind else guidance(sid, ticket)
    if state['stage'] == 'intake':
        state = wf.investigate(sid, ticket_id)
    select_case(sid, ticket_id)
    return state

def normalized(text):
    return re.sub(r'[^a-z0-9 ]', '', text.lower().replace('’', "'")).strip()

def consent(state, text):
    value = normalized(text)
    # Deliberately narrow: questions, quoted instructions and qualifications are not consent.
    yes = value in {'yes', 'yes please', 'approve', 'i approve', 'go ahead', 'yes go ahead',
                    'please proceed', 'proceed', 'yes repair it', 'yes install it', 'yes recover it', 'confirm',
                    'yes please go ahead', 'yes please proceed', 'yes do it', 'sure go ahead', 'yes reset it',
                    'yes complete verification', 'okay', 'ok'}
    if state['stage'] == 'proposed' and yes:
        return 'approve'
    if state['stage'] == 'awaiting_confirmation':
        if value in {'yes', 'yes it works', 'it works', 'it works now', 'working now', 'resolved', 'yes resolved', 'fixed', 'that fixed it', 'yes its working now', 'yes now it is working'}:
            return 'resolved'
        if value in {'no', 'still not working', 'not working', 'still failing', 'it still fails', 'no still not working'}:
            return 'still_failing'
    if state['stage'] == 'guidance':
        if value in {'yes', 'it works', 'it works now', 'that solved it', 'resolved', 'fixed'}:
            return 'helped'
        if value in {'no', 'still not working', 'still failing', 'did not help'}:
            return 'not_helped'
    if value in {'escalate', 'please escalate', 'escalate instead'}:
        return 'escalate'
    return None

def step(sid, state, revision, action):
    if revision is None or revision != state['revision']:
        raise ValueError('This case changed. Review the latest message before approving an action.')
    if action not in {a['id'] for a in public(state)['actions']}:
        raise ValueError('That action is not available at this stage.')
    if action in {'internet_yes', 'internet_no'}:
        return wf.investigate(sid, state['ticket_id'], 'internet works' if action == 'internet_yes' else 'internet is down', revision)
    if state['kind'] != 'guidance':
        return wf.advance(sid, state['ticket_id'], revision, action)
    after = copy.deepcopy(state)
    if action == 'helped':
        after.update(stage='resolved', explanation='You confirmed that the documented steps solved the issue. I have resolved your ticket.',
                     verification={'passed': True, 'check': 'Employee-reported resolution; no device tool was run', 'at': db.now()})
        status = 'Resolved'
    else:
        after.update(stage='escalated', explanation='I have escalated this demo ticket for specialist review, with your description and the guidance already tried. No real service team is notified.')
        status = 'Escalated'
    wf.event(after, status, after['explanation'])
    return wf.save(sid, state, after, status, action)

def handle(sid, message, request_key, case_id=None, revision=None, action=None):
    with lock(sid):
        fingerprint = hashlib.sha256(json.dumps([message, case_id, revision, action]).encode()).hexdigest()
        with db.engine.connect() as c:
            old = c.execute(select(db.assistant_requests).where(db.assistant_requests.c.session_id == sid,
                            db.assistant_requests.c.request_key == request_key)).mappings().first()
        if old:
            if old['fingerprint'] != fingerprint:
                raise ValueError('This message key was already used for a different message.')
            return json.loads(old['response'])
        result = turn(sid, message, request_key, case_id, revision, action)
        db.save_turn(sid, message, result['answer'])
        with db.engine.begin() as c:
            c.execute(insert(db.assistant_requests).values(session_id=sid, request_key=request_key,
                      fingerprint=fingerprint, response=json.dumps(result)))
        return result

def turn(sid, message, request_key, case_id, revision, action):
    state = wf.get(sid, case_id) if case_id else active(sid)
    if case_id and not state:
        raise LookupError('Case not found.')
    if action:
        if not case_id:
            raise ValueError('Select the case before approving an action.')
        state = step(sid, state, revision, action)
        select_case(sid, state['ticket_id'])
        return response(sid, state)
    ticket_match = re.search(r'\bINC-[A-F0-9]{16}\b', message.upper())
    if ticket_match:
        ticket = db.get_ticket(sid, ticket_match.group())
        if not ticket:
            raise LookupError('That ticket is not available in your session.')
        state = investigate_ticket(sid, ticket['id'])
        return response(sid, state, 'Ticket ' + ticket['id'] + '. ')
    kind = wf.suggest(message)
    if state and state['stage'] not in {'resolved', 'escalated'} and (not kind or kind == state['kind']):
        chosen = consent(state, message)
        if chosen:
            # An old message or a naked yes without matching context cannot approve a new tool.
            if case_id != state['ticket_id']:
                return response(sid, state, 'Please use the current approval button below. ')
            state = step(sid, state, revision, chosen)
        elif state['stage'] == 'intake':
            state = wf.investigate(sid, state['ticket_id'], message, revision)
        elif state['stage'] == 'needs_detail':
            ticket = db.get_ticket(sid, state['ticket_id'])
            state = guidance(sid, ticket, state, message)
        elif normalized(message) in {'no', 'no thanks', 'cancel', 'do not proceed', 'dont proceed'}:
            return response(sid, state, 'No action was taken. You can approve later or choose escalation.\n')
        else:
            return response(sid, state, 'Here is the current finding and next step for your case:\n')
        return response(sid, state)
    if normalized(message) in {'hi', 'hello', 'thanks', 'thank you', 'yes', 'no', 'go ahead'}:
        return {'answer': 'Describe the IT issue and what you have already tried. I can investigate demo VPN, account-access and software cases, or guide you using company documentation.',
                'mode': 'knowledge', 'sources': [], 'tool_trace': [], 'action': None, 'case': public(state)}
    hits = search_knowledge_base(message)
    if not kind and not hits:
        return {'answer': 'I do not have an approved procedure for that yet. Which application or device is affected, and what error do you see? I can help with IT support; I cannot promise to fix every issue automatically.',
                'mode': 'knowledge', 'sources': [], 'tool_trace': [], 'action': None, 'case': None}
    ticket = db.create_ticket(sid, dict(summary=message[:160] if len(message)>=5 else 'IT support request', description=message,
                              category=wf.SPECS[kind]['category'] if kind else 'General', priority='Medium'), request_key)
    state = investigate_ticket(sid, ticket['id'])
    return response(sid, state, 'I opened ' + ticket['id'] + ' and used your description to investigate.\n\n')
