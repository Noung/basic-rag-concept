"""Central configuration for the Basic RAG Learning Lab."""

import os

MODEL = os.getenv("RAG_MODEL", "gemma3:1b")
INSUFFICIENT_CONTEXT_TEXT = "ไม่พบข้อมูลเพียงพอในเอกสารที่อัปโหลด"
EMBEDDING_MODEL = os.getenv("RAG_EMBEDDING_MODEL", "nomic-embed-text")
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434/api/embeddings")
RETRIEVAL_TOP_K = int(os.getenv("RAG_RETRIEVAL_TOP_K", "8"))
SEMANTIC_WEIGHT = float(os.getenv("RAG_SEMANTIC_WEIGHT", "0.75"))
LEXICAL_WEIGHT = float(os.getenv("RAG_LEXICAL_WEIGHT", "0.25"))
MIN_FINAL_SCORE = float(os.getenv("RAG_MIN_FINAL_SCORE", "0.22"))
FALLBACK_FINAL_SCORE = float(os.getenv("RAG_FALLBACK_FINAL_SCORE", "0.16"))
MAX_CONTEXT_CHUNKS = int(os.getenv("RAG_MAX_CONTEXT_CHUNKS", "4"))
CHUNK_SIZE = int(os.getenv("RAG_CHUNK_SIZE", "700"))
CHUNK_OVERLAP = int(os.getenv("RAG_CHUNK_OVERLAP", "120"))
CHROMA_DATA_DIR = os.getenv(
    "RAG_CHROMA_DATA_DIR",
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "chroma"),
)
