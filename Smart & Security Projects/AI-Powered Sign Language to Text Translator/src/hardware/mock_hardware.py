"""Mock hardware — returns pre-recorded or blank frames for development."""

import os
import glob

import cv2
import numpy as np


class MockCamera:
    """Return pre-saved frames from data/ or a blank frame with text overlay."""

    def __init__(self, width: int = 640, height: int = 480):
        self._width = width
        self._height = height
        self._frames: list[np.ndarray] = []
        self._index = 0
        self._load_frames()

    def _load_frames(self):
        data_dir = os.path.join(os.path.dirname(__file__), "..", "..", "data", "mock_frames")
        if os.path.isdir(data_dir):
            paths = sorted(glob.glob(os.path.join(data_dir, "*.jpg")))
            for p in paths:
                frame = cv2.imread(p)
                if frame is not None:
                    frame = cv2.resize(frame, (self._width, self._height))
                    self._frames.append(frame)

    def get_frame(self) -> np.ndarray:
        if self._frames:
            frame = self._frames[self._index % len(self._frames)]
            self._index += 1
            return frame.copy()

        # Return blank frame with info text
        frame = np.zeros((self._height, self._width, 3), dtype=np.uint8)
        cv2.putText(
            frame, "MOCK CAMERA - No real camera detected",
            (30, self._height // 2), cv2.FONT_HERSHEY_SIMPLEX,
            0.6, (0, 255, 0), 1,
        )
        return frame
