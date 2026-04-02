"""RAG retriever — embed query, search ChromaDB, optional re-ranking."""

import os
from dataclasses import dataclass
from typing import List

from src.ingestion.embedder import Embedder
from src.services.vector_store import VectorStore


@dataclass
class RetrievedChunk:
    """A chunk returned by similarity search."""
    text: str
    document_id: int = 0
    page_number: int = 0
    chunk_index: int = 0
    score: float = 0.0
    metadata: dict | None = None


class Retriever:
    """Embed a user query and retrieve the most relevant chunks."""

    def __init__(
        self,
        embedder: Embedder | None = None,
        vector_store: VectorStore | None = None,
    ):
        self.embedder = embedder or Embedder()
        self.vector_store = vector_store or VectorStore()
        self.top_k = int(os.getenv("RETRIEVAL_TOP_K", 5))
        self.reranking_enabled = os.getenv("RERANKING_ENABLED", "true").lower() == "true"

    def retrieve(self, query: str, top_k: int | None = None) -> List[RetrievedChunk]:
        """Return the *top_k* most relevant chunks for *query*."""
        rag_enabled = os.getenv("RAG_ENABLED", "true").lower() == "true"
        if not rag_enabled:
            return []

        k = top_k or self.top_k
        query_embedding = self.embedder.embed_query(query)

        results = self.vector_store.search(query_embedding.tolist(), top_k=k)

        chunks: List[RetrievedChunk] = []
        for doc_text, meta, distance in results:
            chunks.append(
                RetrievedChunk(
                    text=doc_text,
                    document_id=meta.get("document_id", 0),
                    page_number=meta.get("page_number", 0),
                    chunk_index=meta.get("chunk_index", 0),
                    score=1.0 - distance if distance is not None else 0.0,
                    metadata=meta,
                )
            )

        if self.reranking_enabled:
            chunks = self._rerank(query, chunks)

        return chunks

    @staticmethod
    def _rerank(query: str, chunks: List[RetrievedChunk]) -> List[RetrievedChunk]:
        """Simple keyword-overlap re-rank (lightweight, no extra model)."""
        query_tokens = set(query.lower().split())
        for chunk in chunks:
            chunk_tokens = set(chunk.text.lower().split())
            overlap = len(query_tokens & chunk_tokens)
            chunk.score += overlap * 0.01  # small boost
        chunks.sort(key=lambda c: c.score, reverse=True)
        return chunks
