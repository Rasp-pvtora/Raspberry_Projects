"""Token-based text chunking with configurable size and overlap."""

import os
from dataclasses import dataclass, field
from typing import List


@dataclass
class Chunk:
    """A single chunk of text with provenance metadata."""
    text: str
    document_id: int = 0
    chunk_index: int = 0
    page_number: int = 0
    char_offset: int = 0
    token_count: int = 0
    metadata: dict = field(default_factory=dict)


class Chunker:
    """Split document text into overlapping token-based chunks."""

    def __init__(
        self,
        chunk_size: int | None = None,
        chunk_overlap: int | None = None,
    ):
        self.chunk_size = chunk_size or int(os.getenv("CHUNK_SIZE", 1000))
        self.chunk_overlap = chunk_overlap or int(os.getenv("CHUNK_OVERLAP", 200))

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    @staticmethod
    def _tokenize(text: str) -> List[str]:
        """Whitespace tokenizer (simple, fast, deterministic)."""
        return text.split()

    @staticmethod
    def _detokenize(tokens: List[str]) -> str:
        return " ".join(tokens)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def chunk(
        self,
        text: str,
        document_id: int = 0,
        page_number: int = 0,
    ) -> List[Chunk]:
        """Split *text* into chunks.  Returns an empty list for blank input."""
        tokens = self._tokenize(text)
        if not tokens:
            return []

        # If the whole text fits in one chunk, return it directly
        if len(tokens) <= self.chunk_size:
            return [
                Chunk(
                    text=self._detokenize(tokens),
                    document_id=document_id,
                    chunk_index=0,
                    page_number=page_number,
                    char_offset=0,
                    token_count=len(tokens),
                )
            ]

        chunks: List[Chunk] = []
        step = self.chunk_size - self.chunk_overlap
        if step < 1:
            step = 1  # safety guard

        char_offset = 0
        for idx, start in enumerate(range(0, len(tokens), step)):
            window = tokens[start : start + self.chunk_size]
            chunk_text = self._detokenize(window)
            chunks.append(
                Chunk(
                    text=chunk_text,
                    document_id=document_id,
                    chunk_index=idx,
                    page_number=page_number,
                    char_offset=char_offset,
                    token_count=len(window),
                )
            )
            char_offset += len(chunk_text) + 1  # approximate

            # Stop when we've consumed all tokens
            if start + self.chunk_size >= len(tokens):
                break

        return chunks
