"""RAG ingestion + retrieval — FastEmbed + in-memory cosine search.

Designed for reliable Streamlit Cloud deploys (no Chroma/FAISS native deps).
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np
from langchain_community.document_loaders import DirectoryLoader, TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter

from src.config import EMBEDDING_MODEL, KB_DIR, TOP_K

_embeddings = None
_chunks: list[Any] = []
_matrix: np.ndarray | None = None
_ready = False


def get_embeddings():
    global _embeddings
    if _embeddings is not None:
        return _embeddings

    try:
        from langchain_community.embeddings.fastembed import FastEmbedEmbeddings

        _embeddings = FastEmbedEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
        return _embeddings
    except Exception:
        from langchain_community.embeddings import HuggingFaceEmbeddings

        _embeddings = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL)
        return _embeddings


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


def _normalize(vectors: np.ndarray) -> np.ndarray:
    norms = np.linalg.norm(vectors, axis=1, keepdims=True)
    norms = np.clip(norms, 1e-12, None)
    return vectors / norms


def build_or_load_store(force_rebuild: bool = False):
    """Build an in-memory embedding index from the knowledge base."""
    global _chunks, _matrix, _ready

    if _ready and not force_rebuild:
        return True

    embeddings = get_embeddings()
    chunks = _load_chunks()
    texts = [c.page_content for c in chunks]
    vectors = np.array(embeddings.embed_documents(texts), dtype=np.float32)
    _matrix = _normalize(vectors)
    _chunks = chunks
    _ready = True
    return True


def search_knowledge_base(query: str, k: int = TOP_K) -> list[dict[str, Any]]:
    build_or_load_store()
    assert _matrix is not None

    embeddings = get_embeddings()
    q = np.array(embeddings.embed_query(query), dtype=np.float32)
    q = q / max(float(np.linalg.norm(q)), 1e-12)
    scores = _matrix @ q
    top_idx = np.argsort(scores)[::-1][:k]

    out: list[dict[str, Any]] = []
    for i in top_idx:
        doc = _chunks[int(i)]
        out.append(
            {
                "content": doc.page_content,
                "source": doc.metadata.get("source", "unknown"),
                "score": float(scores[int(i)]),
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
