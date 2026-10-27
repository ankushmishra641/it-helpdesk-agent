"""Bounded Groq JSON planner. Untrusted output is validated by the caller."""
import json
import threading
import httpx
from src.config import has_llm, GROQ_API_KEY, GROQ_MODEL
from src import database as db

slots = threading.BoundedSemaphore(2)

def plan(system, context):
    if not has_llm():
        return None, 'LLM disabled; using the documented workflow.'
    if not slots.acquire(blocking=False):
        return None, 'AI busy; using the documented workflow.'
    try:
        if not db.reserve_llm():
            return None, 'Daily AI allowance reached; using the documented workflow.'
        payload = dict(model=GROQ_MODEL, temperature=0.1, max_completion_tokens=1800,
                       response_format={'type': 'json_object'},
                       messages=[{'role': 'system', 'content': system},
                                 {'role': 'user', 'content': json.dumps(context)}])
        if GROQ_MODEL.startswith('openai/gpt-oss'):
            payload.update(reasoning_effort='low', include_reasoning=False)
        with httpx.Client(timeout=httpx.Timeout(15, connect=4)) as client:
            response = client.post('https://api.groq.com/openai/v1/chat/completions',
                                   headers={'Authorization': 'Bearer ' + GROQ_API_KEY}, json=payload)
        response.raise_for_status()
        result = json.loads(response.json()['choices'][0]['message']['content'])
        if not isinstance(result, dict):
            raise ValueError('Invalid planner response')
        return result, 'Groq generated a plan from retrieved procedures and tool observations.'
    except (httpx.HTTPError, KeyError, IndexError, TypeError, ValueError):
        return None, 'AI provider unavailable or invalid response; using the documented workflow.'
    finally:
        slots.release()
