"""Small-corpus BM25 retrieval without downloads or a writable vector index."""
import math
import re
import threading
from collections import Counter
from src.config import KB_DIR, TOP_K
STOP = set('a an the is are i my me it to for of and or on in with how do does can please help not cannot have has this that what'.split())
ALIASES = {'connect': 'connection', 'connecting': 'connection', 'wireless': 'wifi', 'outlook': 'email', 'teams': 'meeting', 'locked': 'lockout', 'slow': 'performance', 'slowly': 'performance', 'laptop': 'device', 'resetting': 'reset'}
_lock = threading.RLock()
_signature = None
_documents = []
def tokens(text):
    text = text.lower().replace('wi-fi', 'wifi')
    return [ALIASES.get(t, t) for t in re.findall(r'[a-z0-9]+', text) if t not in STOP and len(t) > 1]
def build_or_load_store(force_rebuild=False):
    global _signature, _documents
    with _lock:
        paths = sorted(KB_DIR.glob('*.md'))
        signature = tuple((p.name, p.stat().st_mtime_ns, p.stat().st_size) for p in paths)
        if signature != _signature or force_rebuild:
            documents = []
            for p in paths:
                content = p.read_text(encoding='utf-8')
                title = content.splitlines()[0].lstrip('# ')
                category = next((s.split(':', 1)[1].strip() for s in content.splitlines() if s.startswith('Category:')), 'General')
                documents.append({'id': p.stem, 'title': title, 'source': p.name, 'category': category,
                                  'content': content, '_terms': Counter(tokens(title + ' ' + title + ' ' + content))})
            _documents, _signature = documents, signature
        return list(_documents)
def list_articles():
    return [{k: v for k, v in d.items() if k != '_terms'} for d in build_or_load_store()]
def search_knowledge_base(query, k=TOP_K):
    docs = build_or_load_store()
    terms = set(tokens(query))
    if not terms or not docs:
        return []
    average = sum(sum(d['_terms'].values()) for d in docs) / len(docs)
    ranked = []
    for d in docs:
        score = 0.0
        matched = terms.intersection(d['_terms'])
        for term in matched:
            df = sum(term in x['_terms'] for x in docs)
            idf = math.log(1 + (len(docs) - df + .5) / (df + .5))
            frequency = d['_terms'][term]
            score += idf * frequency * 2.2 / (frequency + 1.2 * (.25 + .75 * sum(d['_terms'].values()) / average))
            if term in tokens(d['title']):
                score += 2 * idf
        if score >= 1.2 and len(matched) / len(terms) >= .25:
            ranked.append({**{k: v for k, v in d.items() if k != '_terms'}, 'score': round(score, 3)})
    # Employee guide and matching desk runbook describe the same topic.
    # Avoid spending the context window on both copies of one procedure.
    unique, seen = [], set()
    for hit in sorted(ranked, key=lambda d: d['score'], reverse=True):
        topic = hit['id'].rsplit('-', 1)[0] if hit['id'].startswith('ns-') else hit['id']
        if topic not in seen:
            unique.append(hit)
            seen.add(topic)
        if len(unique) >= k:
            break
    return unique
def format_citations(hits):
    return '\n\n'.join(f"[{i}] ({h['source']})\n{h['content']}" for i, h in enumerate(hits, 1)) or 'No relevant documents found in the knowledge base.'
