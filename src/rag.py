"""RAG ingestion + retrieval over the IT knowledge base (ChromaDB)."""
from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import chromadb
from chromadb.config import Settings
from langchain_chroma import Chroma
from langchain_community.document_loaders import DirectoryLoader, TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter

from src.config import EMBEDDING_MODEL, KB_DIR, TOP_K

# Helps avoid some Chroma telemetry / client init issues on cloud hosts
os.environ.setdefault("ANONYMIZED_TELEMETRY", "False")

_embeddings = None
_store: Chroma | None = None
_client = None


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


def _get_client():
    """Ephemeral client is more reliable on Streamlit Cloud than PersistentClient."""
    global _client
    if _client is None:
        _client = chromadb.EphemeralClient(
            settings=Settings(anonymized_telemetry=False, allow_reset=True)
        )
    return _client


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


def build_or_load_store(force_rebuild: bool = False) -> Chroma:
    global _store
    if _store is not None and not force_rebuild:
        return _store

    embeddings = get_embeddings()
    client = _get_client()

    if force_rebuild:
        try:
            client.delete_collection("it_helpdesk")
        except Exception:
            pass
        _store = None

    chunks = _load_chunks()
    _store = Chroma.from_documents(
        documents=chunks,
        embedding=embeddings,
        client=client,
        collection_name="it_helpdesk",
    )
    return _store


def search_knowledge_base(query: str, k: int = TOP_K) -> list[dict[str, Any]]:
    store = build_or_load_store()
    results = store.similarity_search_with_score(query, k=k)
    out: list[dict[str, Any]] = []
    for doc, score in results:
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
