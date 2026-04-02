"""Tests for hand landmark extraction."""

import numpy as np

from src.recognition.hand_tracker import HandTracker


class TestHandTracker:
    def test_normalize_landmarks(self):
        """Normalizing landmarks should translate to wrist origin and scale."""
        tracker = HandTracker.__new__(HandTracker)

        # 21 landmarks × 3 coords = 63 values
        raw = np.random.rand(63).astype(np.float32)
        normalized = tracker._normalize(raw)

        reshaped = normalized.reshape(-1, 3)
        # Wrist (index 0) should be at origin
        np.testing.assert_allclose(reshaped[0], [0.0, 0.0, 0.0], atol=1e-6)
        # Max distance from origin should be ≤ 1
        distances = np.linalg.norm(reshaped, axis=1)
        assert np.max(distances) <= 1.0 + 1e-6

    def test_normalize_preserves_shape(self):
        """Output should have same shape as input."""
        tracker = HandTracker.__new__(HandTracker)
        raw = np.random.rand(63).astype(np.float32)
        normalized = tracker._normalize(raw)
        assert normalized.shape == (63,)

    def test_extract_landmarks_length(self):
        """Extracted landmarks should have 63 values (21 × 3)."""
        tracker = HandTracker.__new__(HandTracker)

        # Create a mock hand_landmarks object
        class MockLandmark:
            def __init__(self, x, y, z):
                self.x = x
                self.y = y
                self.z = z

        class MockHandLandmarks:
            def __init__(self):
                self.landmark = [MockLandmark(i * 0.01, i * 0.02, i * 0.001) for i in range(21)]

        landmarks = tracker._extract_landmarks(MockHandLandmarks())
        assert landmarks.shape == (63,)
        assert landmarks.dtype == np.float32
