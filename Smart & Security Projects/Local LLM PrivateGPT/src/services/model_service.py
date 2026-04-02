"""Ollama model management — list, pull, switch."""

import os
import ollama


class ModelService:
    """Interact with the Ollama API for model lifecycle operations."""

    def __init__(self):
        self.host = os.getenv("OLLAMA_HOST", "http://localhost:11434")
        self._client = ollama.Client(host=self.host)

    def list_models(self) -> list:
        """Return a list of locally available models."""
        try:
            response = self._client.list()
            return response.get("models", [])
        except Exception:
            return []

    def pull_model(self, name: str):
        """Download a model from the Ollama registry. Yields progress dicts."""
        try:
            for progress in self._client.pull(name, stream=True):
                yield progress
        except Exception as exc:
            yield {"error": str(exc)}

    def model_info(self, name: str) -> dict:
        """Return metadata about a specific model."""
        try:
            return self._client.show(name)
        except Exception:
            return {}

    @staticmethod
    def get_active_model() -> str:
        return os.getenv("OLLAMA_MODEL", "llama3:8b-q4_0")

    @staticmethod
    def switch_model(name: str) -> None:
        """Update the active model in the environment (runtime only)."""
        os.environ["OLLAMA_MODEL"] = name
