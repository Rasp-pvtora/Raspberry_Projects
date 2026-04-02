"""ChromaDB vector store — collection management, add, delete, search."""

import os
import uuid
from typing import List, Tuple

import chromadb


class VectorStore:
    """Manage a ChromaDB collection for document chunk embeddings."""

    COLLECTION_NAME = "privategpt_docs"

    def __init__(self, persist_dir: str | None = None):
        self.persist_dir = persist_dir or os.getenv("CHROMA_PERSIST_DIR", "./data/chroma")
        os.makedirs(self.persist_dir, exist_ok=True)
        self._client = chromadb.PersistentClient(path=self.persist_dir)
        self._collection = self._client.get_or_create_collection(
            name=self.COLLECTION_NAME,
            metadata={"hnsw:space": "cosine"},
        )

    # ------------------------------------------------------------------
    # Write
    # ------------------------------------------------------------------
    def add(self, texts: List[str], embeddings: List[List[float]], metadatas: List[dict]) -> List[str]:
        """Insert chunks into ChromaDB. Returns the generated IDs."""
        ids = [str(uuid.uuid4()) for _ in texts]
        self._collection.add(
            ids=ids,
            embeddings=embeddings,
            documents=texts,
            metadatas=metadatas,
        )
        return ids

    def delete(self, document_id: int) -> None:
        """Remove all entries belonging to *document_id*."""
        self._collection.delete(where={"document_id": document_id})

    # ------------------------------------------------------------------
    # Read
    # ------------------------------------------------------------------
    def search(
        self,
        query_embedding: List[float],
        top_k: int = 5,
    ) -> List[Tuple[str, dict, float]]:
        """Return (text, metadata, distance) tuples ranked by similarity."""
        results = self._collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
            include=["documents", "metadatas", "distances"],
        )
        items: List[Tuple[str, dict, float]] = []
        documents = results.get("documents", [[]])[0]
        metadatas = results.get("metadatas", [[]])[0]
        distances = results.get("distances", [[]])[0]
        for doc, meta, dist in zip(documents, metadatas, distances):
            items.append((doc, meta, dist))
        return items

    def count(self) -> int:
        return self._collection.count()
