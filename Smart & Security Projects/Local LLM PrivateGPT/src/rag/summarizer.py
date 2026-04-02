"""Document summarization pipeline — iterative chunk-based summarization."""

import os
from typing import List

from src.rag.generator import Generator


class Summarizer:
    """Summarise an entire document by iteratively compressing its chunks."""

    def __init__(self, generator: Generator | None = None):
        self.enabled = os.getenv("SUMMARIZATION_ENABLED", "true").lower() == "true"
        self.generator = generator or Generator()

    def summarize(self, chunks: List[str], filename: str = "document") -> str:
        """Return a coherent summary of all *chunks*."""
        if not self.enabled:
            return "Summarization is disabled."
        if not chunks:
            return "No content to summarize."

        # Stage 1 — summarise each chunk individually
        chunk_summaries: List[str] = []
        for i, chunk_text in enumerate(chunks):
            prompt = (
                f"Summarize the following excerpt from '{filename}' "
                f"(part {i + 1}/{len(chunks)}) in 2-3 sentences:\n\n{chunk_text}"
            )
            result = self.generator.generate_full(prompt)
            chunk_summaries.append(result["answer"])

        # Stage 2 — combine chunk summaries into a final summary
        combined = "\n\n".join(chunk_summaries)
        final_prompt = (
            f"Below are section-by-section summaries of '{filename}'. "
            f"Write a coherent overall summary (one paragraph):\n\n{combined}"
        )
        result = self.generator.generate_full(final_prompt)
        return result["answer"]
