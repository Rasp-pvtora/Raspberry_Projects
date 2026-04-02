"""Sentence builder — accumulates sign labels into sentences with pause detection."""

import os
import time


class SentenceBuilder:
    """Buffer recognized signs and finalize sentences on pause."""

    def __init__(self):
        self._enabled = os.getenv("SENTENCE_ENABLED", "true").lower() == "true"
        self._pause_sec = float(os.getenv("SENTENCE_PAUSE_SEC", "2.0"))
        self._signs: list[str] = []
        self._last_sign_time: float = 0.0

    def add_sign(self, label: str, confidence: float):
        """Add a recognized sign to the buffer."""
        if not self._enabled:
            return

        # Avoid duplicate consecutive signs
        if self._signs and self._signs[-1] == label:
            self._last_sign_time = time.time()
            return

        self._signs.append(label)
        self._last_sign_time = time.time()

    def get_current_sentence(self) -> str:
        """Return the sentence currently being built."""
        return " ".join(self._signs)

    def check_pause(self) -> str | None:
        """Check if a pause has occurred. Returns finalized sentence or None."""
        if not self._signs:
            return None
        if not self._last_sign_time:
            return None

        elapsed = time.time() - self._last_sign_time
        if elapsed >= self._pause_sec:
            sentence = " ".join(self._signs)
            self._signs.clear()
            self._last_sign_time = 0.0
            return sentence

        return None

    def reset(self):
        """Clear the sentence buffer."""
        self._signs.clear()
        self._last_sign_time = 0.0
