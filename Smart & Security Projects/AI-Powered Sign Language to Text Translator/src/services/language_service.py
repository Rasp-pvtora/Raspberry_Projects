"""Language service — manage multi-sign-language model swapping."""

import os

SUPPORTED_LANGUAGES = {
    "asl": {"name": "American Sign Language", "model": "asl_lstm.h5"},
    "bsl": {"name": "British Sign Language", "model": "bsl_lstm.h5"},
    "dgs": {"name": "German Sign Language (DGS)", "model": "dgs_lstm.h5"},
    "lsf": {"name": "French Sign Language (LSF)", "model": "lsf_lstm.h5"},
}


class LanguageService:
    """Manage sign language model selection and swapping."""

    def __init__(self):
        self._current = os.getenv("SIGN_LANGUAGE", "asl")
        self._models_dir = os.path.join(os.path.dirname(__file__), "..", "..", "models")

    @property
    def current_language(self) -> str:
        return self._current

    @property
    def current_model_path(self) -> str:
        info = SUPPORTED_LANGUAGES.get(self._current, SUPPORTED_LANGUAGES["asl"])
        return os.path.join(self._models_dir, info["model"])

    def switch_language(self, language_code: str) -> str:
        """Switch to a different sign language. Returns new model path."""
        if language_code not in SUPPORTED_LANGUAGES:
            raise ValueError(f"Unsupported language: {language_code}")
        self._current = language_code
        return self.current_model_path

    def list_languages(self) -> list[dict]:
        """Return list of supported languages with availability info."""
        result = []
        for code, info in SUPPORTED_LANGUAGES.items():
            model_path = os.path.join(self._models_dir, info["model"])
            result.append({
                "code": code,
                "name": info["name"],
                "model": info["model"],
                "available": os.path.exists(model_path),
                "active": code == self._current,
            })
        return result
