"""RAG ingestion + retrieval over the IT knowledge base (ChromaDB)."""
from __future__ import annotations

from pathlib import Path
from typing import Any

from langchain_community.document_loaders import DirectoryLoader, TextLoader
from langchain_community.vectorstores import Chroma
from langchain_text_splitters import RecursiveCharacterTextSplitter

from src.config import CHROMA_DIR, EMBEDDING_MODEL, KB_DIR, TOP_K

_embeddings = None
_store: Chroma | None = None


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


def build_or_load_store(force_rebuild: bool = False) -> Chroma:
    """Build or load a local ChromaDB index (for localhost demos)."""
    global _store
    if _store is not None and not force_rebuild:
        return _store

    CHROMA_DIR.mkdir(parents=True, exist_ok=True)
    embeddings = get_embeddings()

    if CHROMA_DIR.exists() and any(CHROMA_DIR.iterdir()) and not force_rebuild:
        try:
            _store = Chroma(
                persist_directory=str(CHROMA_DIR),
                embedding_function=embeddings,
                collection_name="it_helpdesk",
            )
            if _store._collection.count() > 0:
                return _store
        except Exception:
            pass

    chunks = _load_chunks()
    _store = Chroma.from_documents(
        documents=chunks,
        embedding=embeddings,
        persist_directory=str(CHROMA_DIR),
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
