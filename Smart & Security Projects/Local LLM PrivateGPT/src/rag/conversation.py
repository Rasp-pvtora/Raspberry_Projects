"""Session-based conversation memory for multi-turn Q&A."""

import os
from typing import List


class ConversationMemory:
    """Maintain a rolling window of previous Q&A exchanges for context."""

    def __init__(self, max_turns: int = 5):
        self.enabled = os.getenv("CONVERSATION_MEMORY_ENABLED", "true").lower() == "true"
        self.max_turns = max_turns
        # In-memory store keyed by session / conversation id
        self._memory: dict[str, List[dict]] = {}

    def add(self, conversation_id: str, role: str, content: str) -> None:
        if not self.enabled:
            return
        if conversation_id not in self._memory:
            self._memory[conversation_id] = []
        self._memory[conversation_id].append({"role": role, "content": content})
        # Trim to max_turns * 2 messages (each turn = user + assistant)
        max_messages = self.max_turns * 2
        if len(self._memory[conversation_id]) > max_messages:
            self._memory[conversation_id] = self._memory[conversation_id][-max_messages:]

    def get_context(self, conversation_id: str) -> List[dict]:
        """Return previous exchanges for inclusion in the LLM prompt."""
        if not self.enabled:
            return []
        return list(self._memory.get(conversation_id, []))

    def clear(self, conversation_id: str) -> None:
        self._memory.pop(conversation_id, None)
