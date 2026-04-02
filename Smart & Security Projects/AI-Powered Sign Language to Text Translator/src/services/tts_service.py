"""Piper TTS service — text-to-speech output for finalized sentences."""

import os
import subprocess
import shutil


class TTSService:
    """Speak text using Piper TTS."""

    def __init__(self):
        self._enabled = os.getenv("TTS_ENABLED", "false").lower() == "true"
        self._voice = os.getenv("TTS_VOICE", "en_US-lessac-medium")
        self._piper_path = shutil.which("piper")

    # Language → TTS voice mapping
    LANGUAGE_VOICES = {
        "asl": "en_US-lessac-medium",
        "bsl": "en_GB-alan-medium",
        "dgs": "de_DE-thorsten-medium",
        "lsf": "fr_FR-upmc-medium",
    }

    def speak(self, text: str):
        """Synthesize and play text via Piper TTS."""
        if not self._enabled or not text.strip():
            return

        if not self._piper_path:
            return

        try:
            process = subprocess.Popen(
                [self._piper_path, "--model", self._voice, "--output-raw"],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL,
            )
            audio_data, _ = process.communicate(input=text.encode("utf-8"), timeout=10)

            # Play via aplay (Linux/Pi)
            if audio_data and shutil.which("aplay"):
                play = subprocess.Popen(
                    ["aplay", "-r", "22050", "-f", "S16_LE", "-t", "raw", "-"],
                    stdin=subprocess.PIPE,
                    stderr=subprocess.DEVNULL,
                )
                play.communicate(input=audio_data, timeout=15)
        except Exception:
            pass

    def set_voice(self, voice: str):
        self._voice = voice

    def set_language(self, language: str):
        voice = self.LANGUAGE_VOICES.get(language, self._voice)
        self._voice = voice
