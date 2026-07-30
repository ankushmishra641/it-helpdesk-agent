"""RAG retrieval with pure NumPy TF-IDF (Streamlit Cloud friendly).

No Chroma, FAISS, fastembed, torch, or Pillow — avoids native build failures on Python 3.14.
"""
from __future__ import annotations

import math
import re
from collections import Counter
from pathlib import Path
from typing import Any

from langchain_community.document_loaders import DirectoryLoader, TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter

from src.config import KB_DIR, TOP_K

_chunks: list[Any] = []
_tfidf: list[dict[str, float]] = []
_idf: dict[str, float] = {}
_ready = False

_TOKEN = re.compile(r"[a-z0-9_]+")


def _tokenize(text: str) -> list[str]:
    return _TOKEN.findall(text.lower())


def _load_chunks():
    loader = DirectoryLoader(
        str(KB_DIR),
        glob="**/*.md",
        loader_cls=TextLoader,
        loader_kwargs={"encoding": "utf-8"},
    )
    docs = loader.load()
    for d in docs:
        d.metadata["source"] = Path(d.metadata.get("source", "")).name

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=700,
        chunk_overlap=120,
        separators=["\n## ", "\n### ", "\n\n", "\n", " "],
    )
    return splitter.split_documents(docs)


def build_or_load_store(force_rebuild: bool = False):
    """Build an in-memory TF-IDF index over the knowledge base."""
    global _chunks, _tfidf, _idf, _ready

    if _ready and not force_rebuild:
        return True

    chunks = _load_chunks()
    docs_tokens = [_tokenize(c.page_content) for c in chunks]
    df: Counter[str] = Counter()
    for tokens in docs_tokens:
        df.update(set(tokens))

    n = max(len(docs_tokens), 1)
    idf = {term: math.log((n + 1) / (freq + 1)) + 1.0 for term, freq in df.items()}

    vectors: list[dict[str, float]] = []
    for tokens in docs_tokens:
        tf = Counter(tokens)
        length = max(len(tokens), 1)
        vec = {t: (cnt / length) * idf.get(t, 0.0) for t, cnt in tf.items()}
        vectors.append(vec)

    _chunks = chunks
    _tfidf = vectors
    _idf = idf
    _ready = True
    return True


def _cosine(a: dict[str, float], b: dict[str, float]) -> float:
    if not a or not b:
        return 0.0
    dot = 0.0
    for k, v in a.items():
        if k in b:
            dot += v * b[k]
    na = math.sqrt(sum(v * v for v in a.values())) or 1e-12
    nb = math.sqrt(sum(v * v for v in b.values())) or 1e-12
    return dot / (na * nb)


def search_knowledge_base(query: str, k: int = TOP_K) -> list[dict[str, Any]]:
    build_or_load_store()
    q_tokens = _tokenize(query)
    tf = Counter(q_tokens)
    length = max(len(q_tokens), 1)
    q_vec = {t: (cnt / length) * _idf.get(t, 0.0) for t, cnt in tf.items()}

    scored = [(_cosine(q_vec, doc_vec), idx) for idx, doc_vec in enumerate(_tfidf)]
    scored.sort(reverse=True)

    out: list[dict[str, Any]] = []
    for score, idx in scored[:k]:
        doc = _chunks[idx]
        out.append(
            {
                "content": doc.page_content,
                "source": doc.metadata.get("source", "unknown"),
                "score": float(score),
            }
        )
    return out


def format_citations(hits: list[dict[str, Any]]) -> str:
    if not hits:
        return "No relevant documents found in the knowledge base."
    parts = []
    for i, h in enumerate(hits, 1):
        parts.append(f"[{i}] ({h['source']})\n{h['content']}")
    return "\n\n---\n\n".join(parts)
