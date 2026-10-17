"""
embeddings.py — Vector embedding generator for MentoAI's graph nodes.

Uses local fastembed ONNX runtime if available, with a normalized 384-dimensional
fallback embedding to guarantee zero-cost local execution without GPU requirements.
"""
import math
import hashlib
from typing import List, Optional

EMBEDDING_MODEL_NAME = "bge-small-en-v1.5"
EMBEDDING_DIM = 384

import importlib.util

_fastembed_model = None
_has_fastembed = False

try:
    if importlib.util.find_spec("fastembed") is not None:
        from fastembed import TextEmbedding  # type: ignore
        _fastembed_model = TextEmbedding(model_name="BAAI/bge-small-en-v1.5")
        _has_fastembed = True
except Exception:
    _has_fastembed = False
    _fastembed_model = None


def _fallback_deterministic_embed(text: str, dim: int = EMBEDDING_DIM) -> List[float]:
    """
    Deterministic normalized pseudo-embedding based on character n-grams and hashing.
    Provides consistent vector dimensions and dot-product properties for offline testing.
    """
    clean_text = text.lower().strip()
    words = clean_text.split()
    vec = [0.0] * dim

    # Combine unigram and bigram hash buckets
    tokens = words + [f"{words[i]}_{words[i+1]}" for i in range(len(words) - 1)] if len(words) > 1 else words
    if not tokens:
        tokens = [clean_text]

    for tok in tokens:
        h = int(hashlib.sha256(tok.encode("utf-8")).hexdigest(), 16)
        idx = h % dim
        sign = 1.0 if (h >> 8) % 2 == 0 else -1.0
        vec[idx] += sign

    # L2 normalize
    norm = math.sqrt(sum(x * x for x in vec))
    if norm > 1e-9:
        vec = [x / norm for x in vec]
    else:
        vec[0] = 1.0

    return vec


def get_embedding(text: str) -> List[float]:
    """Generate normalized 384-dimensional vector embedding for text."""
    if not text:
        return [0.0] * EMBEDDING_DIM

    if _has_fastembed and _fastembed_model is not None:
        try:
            embeddings = list(_fastembed_model.embed([text]))
            return embeddings[0].tolist()
        except Exception:
            pass

    return _fallback_deterministic_embed(text, EMBEDDING_DIM)


def cosine_similarity(v1: List[float], v2: List[float]) -> float:
    """Compute cosine similarity between two unit vectors."""
    if not v1 or not v2 or len(v1) != len(v2):
        return 0.0
    return sum(a * b for a, b in zip(v1, v2))
