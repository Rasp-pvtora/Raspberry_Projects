"""Tests for sign classifier."""

import numpy as np

from src.recognition.sign_classifier import SignClassifier


class TestSignClassifier:
    def test_buffer_accumulation(self):
        """Classifier should accumulate frames before classifying."""
        classifier = SignClassifier.__new__(SignClassifier)
        classifier._confidence_threshold = 0.7
        classifier._interpreter = None
        classifier._labels = list("ABCDEFGHIJKLMNOPQRSTUVWXYZ")
        classifier._buffer = __import__("collections").deque(maxlen=30)

        landmarks = np.random.rand(63).astype(np.float32)

        # Adding fewer than BUFFER_SIZE frames should return None
        for _ in range(29):
            result = classifier.classify(landmarks)
            assert result is None

    def test_mock_classify_returns_none(self):
        """Mock classification (no model) should return None."""
        classifier = SignClassifier.__new__(SignClassifier)
        classifier._interpreter = None
        classifier._buffer = __import__("collections").deque(maxlen=30)
        result = classifier._mock_classify()
        assert result is None

    def test_set_model_clears_buffer(self):
        """Swapping model should clear the landmark buffer."""
        classifier = SignClassifier.__new__(SignClassifier)
        classifier._confidence_threshold = 0.7
        classifier._interpreter = None
        classifier._labels = []
        classifier._buffer = __import__("collections").deque(maxlen=30)
        classifier._input_details = None
        classifier._output_details = None

        # Add some frames
        for _ in range(10):
            classifier._buffer.append(np.zeros(63))
        assert len(classifier._buffer) == 10

        classifier.set_model("./models/test.h5")
        assert len(classifier._buffer) == 0
