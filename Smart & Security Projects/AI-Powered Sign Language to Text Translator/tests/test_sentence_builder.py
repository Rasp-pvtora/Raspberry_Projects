"""Tests for sentence builder."""

import time
import os

# Set pause to short value for testing
os.environ["SENTENCE_PAUSE_SEC"] = "0.1"

from src.recognition.sentence_builder import SentenceBuilder


class TestSentenceBuilder:
    def test_add_signs(self):
        builder = SentenceBuilder()
        builder._pause_sec = 0.1
        builder.add_sign("HELLO", 0.9)
        builder.add_sign("WORLD", 0.85)
        assert builder.get_current_sentence() == "HELLO WORLD"

    def test_duplicate_suppression(self):
        """Consecutive duplicate signs should not be added twice."""
        builder = SentenceBuilder()
        builder._pause_sec = 0.1
        builder.add_sign("HELLO", 0.9)
        builder.add_sign("HELLO", 0.9)
        assert builder.get_current_sentence() == "HELLO"

    def test_pause_finalization(self):
        """After a pause, the sentence should be finalized."""
        builder = SentenceBuilder()
        builder._pause_sec = 0.1
        builder.add_sign("HELLO", 0.9)
        time.sleep(0.15)
        result = builder.check_pause()
        assert result == "HELLO"
        assert builder.get_current_sentence() == ""

    def test_no_premature_finalization(self):
        """Sentence should not finalize before pause duration."""
        builder = SentenceBuilder()
        builder._pause_sec = 10.0
        builder.add_sign("HELLO", 0.9)
        result = builder.check_pause()
        assert result is None

    def test_reset(self):
        builder = SentenceBuilder()
        builder.add_sign("HELLO", 0.9)
        builder.reset()
        assert builder.get_current_sentence() == ""
