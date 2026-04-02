"""Text-to-sign display — reverse lookup: text input → sign images/GIFs."""

import os
import json


class TextToSign:
    """Convert text input into a sequence of sign language images."""

    def __init__(self):
        self._enabled = os.getenv("TEXT_TO_SIGN_ENABLED", "true").lower() == "true"
        self._dictionary_path = os.path.join(
            os.path.dirname(__file__), "..", "..", "models", "sign_dictionary"
        )
        self._dictionary: dict[str, str] = {}
        self._load_dictionary()

    def _load_dictionary(self):
        """Load sign dictionary mapping words/letters to image paths."""
        index_path = os.path.join(self._dictionary_path, "index.json")
        if os.path.exists(index_path):
            with open(index_path, "r") as f:
                self._dictionary = json.load(f)
        else:
            # Default: map A-Z to expected image filenames
            for letter in "ABCDEFGHIJKLMNOPQRSTUVWXYZ":
                self._dictionary[letter] = f"{letter.lower()}.png"

    def translate(self, text: str) -> list[dict]:
        """Convert text to a list of sign entries.

        Returns list of {"char": "A", "image": "a.png", "found": True/False}
        """
        if not self._enabled:
            return []

        results = []
        for char in text.upper():
            if char == " ":
                results.append({"char": " ", "image": None, "found": True})
                continue

            image = self._dictionary.get(char)
            results.append({
                "char": char,
                "image": image,
                "found": image is not None,
            })
        return results

    @property
    def dictionary_path(self) -> str:
        return self._dictionary_path
