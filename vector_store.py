"""Vector-store boundary for the Learning Lab.

This module owns ChromaDB initialization and index-level operations so the UI
does not need to know storage details.
"""

import chromadb

from config import CHROMA_DATA_DIR

client = chromadb.PersistentClient(path=CHROMA_DATA_DIR)
collection = client.get_or_create_collection(name="rag_collection")


def get_collection():
    """Return the shared persistent collection."""
    return collection


def get_stats():
    """Return basic document/chunk counts from the collection."""
    total_chunks = collection.count()
    rows = collection.get(include=["metadatas"]) if total_chunks else {}
    metadatas = rows.get("metadatas", []) if rows else []
    document_ids = {
        metadata.get("document_id")
        for metadata in metadatas
        if metadata and metadata.get("document_id")
    }
    sources = sorted(
        {
            metadata.get("source")
            for metadata in metadatas
            if metadata and metadata.get("source")
        }
    )
    return {
        "total_chunks": total_chunks,
        "unique_documents": len(document_ids),
        "sources": sources,
    }
