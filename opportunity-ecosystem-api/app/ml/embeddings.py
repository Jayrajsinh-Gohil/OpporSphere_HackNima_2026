"""
Embedding model — local SentenceTransformer (all-MiniLM-L6-v2).

Produces 384-dimensional vectors matching the vector(384) columns in PostgreSQL.
The model is downloaded once and cached locally.  Encoding runs in a thread pool
to keep the async event loop non-blocking.

No API key required — completely free and offline.

Usage:
    from app.ml.embeddings import get_embedder
    embedder = get_embedder()
    vector = await embedder.embed("Some text to embed")
    vectors = await embedder.embed_batch(["text a", "text b"])
"""

from __future__ import annotations

import asyncio
from functools import lru_cache
from typing import List

import numpy as np
from loguru import logger

# ── Typing alias ──────────────────────────────────────────────────────────────
Vector = List[float]


class SentenceTransformerEmbedder:
    """
    Local embedder using sentence-transformers (all-MiniLM-L6-v2).

    Produces 384-dimensional normalised vectors.
    Loaded once at application startup via the lifespan hook.
    Encoding runs in a thread pool to keep the async event loop non-blocking.
    """

    def __init__(self, model_name: str = "all-MiniLM-L6-v2") -> None:
        self.model_name = model_name
        self._model = None

    def load_model(self) -> None:
        """Synchronously load the model if not already loaded."""
        if self._model is None:
            logger.info(f"Loading SentenceTransformer model '{self.model_name}'...")
            from sentence_transformers import SentenceTransformer
            self._model = SentenceTransformer(self.model_name)
            logger.info(
                f"SentenceTransformer '{self.model_name}' loaded successfully (dim=384)."
            )

    async def embed(self, text: str) -> Vector:
        """Compute a 384-dim normalised embedding vector for a single text."""
        if self._model is None:
            await asyncio.to_thread(self.load_model)
        cleaned = text.replace("\n", " ").strip()
        vector = await asyncio.to_thread(
            self._model.encode,
            cleaned,
            normalize_embeddings=True,
        )
        return vector.tolist()

    async def embed_batch(self, texts: List[str]) -> List[Vector]:
        """Compute embeddings for a batch of strings."""
        if self._model is None:
            await asyncio.to_thread(self.load_model)
        cleaned = [t.replace("\n", " ").strip() for t in texts]
        vectors = await asyncio.to_thread(
            self._model.encode,
            cleaned,
            normalize_embeddings=True,
        )
        return [v.tolist() for v in vectors]

    @staticmethod
    def cosine_similarity(a: Any, b: Any) -> float:
        """Quick cosine similarity between two 384-dim vectors."""
        import json
        if isinstance(a, str):
            try:
                a = json.loads(a)
            except Exception:
                return 0.0
        if isinstance(b, str):
            try:
                b = json.loads(b)
            except Exception:
                return 0.0
        if a is None or b is None:
            return 0.0
        na = np.array(a, dtype=float)
        nb = np.array(b, dtype=float)
        denom = np.linalg.norm(na) * np.linalg.norm(nb)
        return float(np.dot(na, nb) / denom) if denom else 0.0


@lru_cache
def get_embedder() -> SentenceTransformerEmbedder:
    """Return the cached local SentenceTransformer embedder singleton."""
    return SentenceTransformerEmbedder()


# Alias — kept for backwards compatibility with any code that imported get_local_embedder
get_local_embedder = get_embedder
