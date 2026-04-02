"""LLM generator — build prompt, call Ollama, stream answer."""

import os
import time
import json
from typing import Generator as GenType, List

import ollama


class Generator:
    """Construct RAG prompt and call Ollama for answer generation."""

    SYSTEM_PROMPT = (
        "You are a helpful document assistant. Answer the user's question based ONLY on "
        "the provided context. If the context does not contain enough information to answer, "
        "say so clearly. Always cite which document and page your information comes from."
    )

    def __init__(self):
        self.host = os.getenv("OLLAMA_HOST", "http://localhost:11434")
        self.model = os.getenv("OLLAMA_MODEL", "llama3:8b-q4_0")
        self.temperature = float(os.getenv("OLLAMA_TEMPERATURE", 0.3))
        self.max_tokens = int(os.getenv("OLLAMA_MAX_TOKENS", 512))
        self._client = ollama.Client(host=self.host)

    # ------------------------------------------------------------------
    # Prompt construction
    # ------------------------------------------------------------------
    @staticmethod
    def _build_context_block(chunks) -> str:
        """Format retrieved chunks into a numbered context block."""
        blocks: List[str] = []
        for i, chunk in enumerate(chunks, 1):
            meta = chunk.metadata or {}
            doc_name = meta.get("filename", "Unknown")
            page = meta.get("page_number", "?")
            blocks.append(f"[Source {i}: {doc_name}, page {page}]\n{chunk.text}")
        return "\n\n---\n\n".join(blocks)

    def _build_messages(self, query: str, context_chunks, conversation_history=None):
        messages = [{"role": "system", "content": self.SYSTEM_PROMPT}]

        if conversation_history:
            for entry in conversation_history:
                messages.append({"role": entry["role"], "content": entry["content"]})

        if context_chunks:
            context = self._build_context_block(context_chunks)
            user_content = f"Context:\n{context}\n\nQuestion: {query}"
        else:
            user_content = query

        messages.append({"role": "user", "content": user_content})
        return messages

    # ------------------------------------------------------------------
    # Generation (streaming)
    # ------------------------------------------------------------------
    def generate(
        self,
        query: str,
        context_chunks=None,
        conversation_history=None,
        model: str | None = None,
    ) -> GenType[str, None, None]:
        """Yield answer tokens one by one. Catches connection errors gracefully."""
        model = model or self.model
        messages = self._build_messages(query, context_chunks, conversation_history)

        try:
            stream = self._client.chat(
                model=model,
                messages=messages,
                stream=True,
                options={
                    "temperature": self.temperature,
                    "num_predict": self.max_tokens,
                },
            )
            for chunk in stream:
                token = chunk.get("message", {}).get("content", "")
                if token:
                    yield token
        except Exception as exc:
            yield f"\n\n[Error communicating with Ollama: {exc}]"

    def generate_full(
        self,
        query: str,
        context_chunks=None,
        conversation_history=None,
        model: str | None = None,
    ) -> dict:
        """Return the complete answer as a dict with metadata."""
        start = time.time()
        tokens: List[str] = []
        for token in self.generate(query, context_chunks, conversation_history, model):
            tokens.append(token)
        answer = "".join(tokens)
        elapsed = time.time() - start

        citations = []
        if context_chunks:
            for chunk in context_chunks:
                meta = chunk.metadata or {}
                citations.append({
                    "document": meta.get("filename", "Unknown"),
                    "page": meta.get("page_number", 0),
                    "passage": chunk.text[:300],
                    "chunk_id": meta.get("chroma_id", ""),
                })

        return {
            "answer": answer,
            "citations": citations,
            "model": model or self.model,
            "generation_time": round(elapsed, 2),
        }
