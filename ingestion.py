import hashlib
from datetime import datetime, timezone


def normalize_newlines(text):
    """Normalize mixed newlines to \n for consistent chunking."""
    return text.replace("\r\n", "\n").replace("\r", "\n")


def chunk_text(text, chunk_size=700, chunk_overlap=120):
    """Split text into fixed-size overlapping chunks."""
    if chunk_size <= 0:
        raise ValueError("chunk_size must be greater than 0")
    if chunk_overlap < 0:
        raise ValueError("chunk_overlap must be >= 0")
    if chunk_overlap >= chunk_size:
        raise ValueError("chunk_overlap must be smaller than chunk_size")

    normalized = normalize_newlines(text).strip()
    if not normalized:
        return []

    chunks = []
    step = chunk_size - chunk_overlap
    start = 0

    while start < len(normalized):
        end = min(start + chunk_size, len(normalized))
        chunk = normalized[start:end].strip()
        if chunk:
            chunks.append(chunk)
        if end == len(normalized):
            break
        start += step

    return chunks


def chunk_content_hash(chunk):
    """Create stable hash for one chunk content."""
    normalized = normalize_newlines(chunk).strip()
    return hashlib.sha1(normalized.encode("utf-8")).hexdigest()


def prepare_unique_chunks(chunks):
    """Return unique chunks with stable content hashes while preserving order."""
    unique = []
    seen = set()

    for chunk in chunks:
        content_hash = chunk_content_hash(chunk)
        if content_hash in seen:
            continue
        seen.add(content_hash)
        unique.append((chunk, content_hash))

    return unique


def document_id_from_path(file_path):
    """Build stable document id from file path."""
    digest = hashlib.sha1(file_path.encode("utf-8")).hexdigest()
    return f"doc_{digest}"


def timestamp_utc():
    """Return RFC3339 UTC timestamp for metadata."""
    return datetime.now(timezone.utc).isoformat()
