"""Pure retrieval scoring helpers for the Learning Lab."""

import re


def tokenize(text):
    """Tokenize Thai/English text for lightweight lexical matching."""
    cleaned = re.sub(r"[^0-9a-zA-Zก-๙\s]", " ", (text or "").lower())
    return [token for token in cleaned.split() if token]


def lexical_overlap_score(query, text):
    """Return query-token overlap in the candidate text (0..1)."""
    query_tokens = set(tokenize(query))
    text_tokens = set(tokenize(text))
    if not query_tokens or not text_tokens:
        return 0.0
    return len(query_tokens.intersection(text_tokens)) / len(query_tokens)


def distance_to_relevance(distance):
    """Convert a non-negative vector distance to a bounded score."""
    if distance is None:
        return 0.0
    return 1.0 / (1.0 + max(float(distance), 0.0))


def hybrid_score(
    semantic_score,
    lexical_score,
    semantic_weight=0.75,
    lexical_weight=0.25,
):
    """Combine semantic and lexical scores after weight normalization."""
    if semantic_weight < 0 or lexical_weight < 0:
        raise ValueError("weights must be >= 0")
    total = semantic_weight + lexical_weight
    if total == 0:
        raise ValueError("at least one weight must be greater than zero")
    return (
        semantic_weight * semantic_score + lexical_weight * lexical_score
    ) / total
