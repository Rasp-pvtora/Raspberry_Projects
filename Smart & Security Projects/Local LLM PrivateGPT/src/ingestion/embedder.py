"""Sentence-transformer embedding generation."""

import os
from typing import List

import numpy as np
from sentence_transformers import SentenceTransformer


class Embedder:
    """Compute dense vector embeddings for text chunks."""

    def __init__(self, model_name: str | None = None):
        self.model_name = model_name or os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")
        self._model: SentenceTransformer | None = None

    # Lazy-load so the model is only loaded when first needed.
    @property
    def model(self) -> SentenceTransformer:
        if self._model is None:
            self._model = SentenceTransformer(self.model_name)
        return self._model

    def embed(self, texts: List[str]) -> np.ndarray:
        """Return an (N, dim) array of embeddings for *texts*."""
        if not texts:
            return np.empty((0, 384), dtype=np.float32)
        embeddings = self.model.encode(texts, show_progress_bar=False, convert_to_numpy=True)
        return embeddings

    def embed_query(self, query: str) -> np.ndarray:
        """Embed a single query string and return a 1-d vector."""
        return self.model.encode(query, show_progress_bar=False, convert_to_numpy=True)
