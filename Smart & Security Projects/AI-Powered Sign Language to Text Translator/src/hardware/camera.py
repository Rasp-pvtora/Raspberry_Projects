"""Camera capture module — OpenCV VideoCapture with configurable source and resolution."""

import os
import base64

import cv2
import numpy as np


class Camera:
    """Capture frames from Pi Camera, USB webcam, or fall back to mock."""

    def __init__(self):
        source = os.getenv("CAMERA_SOURCE", "0")
        self._source = int(source) if source.isdigit() else source
        resolution = os.getenv("CAMERA_RESOLUTION", "640x480")
        self._width, self._height = (int(x) for x in resolution.split("x"))

        self._cap = None
        self._mock = None
        self._open()

    def _open(self):
        try:
            self._cap = cv2.VideoCapture(self._source)
            if not self._cap.isOpened():
                raise RuntimeError("Camera not available")
            self._cap.set(cv2.CAP_PROP_FRAME_WIDTH, self._width)
            self._cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self._height)
        except Exception:
            from src.hardware.mock_hardware import MockCamera
            self._mock = MockCamera(self._width, self._height)
            self._cap = None

    def get_frame(self) -> np.ndarray | None:
        if self._mock:
            return self._mock.get_frame()
        if self._cap and self._cap.isOpened():
            ret, frame = self._cap.read()
            return frame if ret else None
        return None

    def encode_frame(self, frame: np.ndarray) -> str:
        if frame is None:
            return ""
        _, buffer = cv2.imencode(".jpg", frame)
        return base64.b64encode(buffer).decode("utf-8")

    def release(self):
        if self._cap:
            self._cap.release()
