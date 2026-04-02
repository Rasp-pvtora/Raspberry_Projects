"""LSTM sign classifier — buffers frames and classifies sign sequences."""

import os
from collections import deque

import numpy as np


class SignClassifier:
    """Buffer landmark frames and classify using a TFLite LSTM model."""

    BUFFER_SIZE = 30  # ~2 seconds at 15 FPS

    def __init__(self):
        self._confidence_threshold = float(os.getenv("CONFIDENCE_THRESHOLD", "0.7"))
        self._model_path = os.getenv("MODEL_PATH", "./models/asl_lstm.h5")
        self._buffer: deque[np.ndarray] = deque(maxlen=self.BUFFER_SIZE)
        self._interpreter = None
        self._labels: list[str] = []
        self._input_details = None
        self._output_details = None
        self._load_model()

    def _load_model(self):
        """Load TFLite model if available."""
        tflite_path = self._model_path.replace(".h5", ".tflite")
        try:
            import tflite_runtime.interpreter as tflite
            self._interpreter = tflite.Interpreter(model_path=tflite_path)
        except ImportError:
            try:
                import tensorflow as tf
                self._interpreter = tf.lite.Interpreter(model_path=tflite_path)
            except Exception:
                self._interpreter = None
                return

        if self._interpreter:
            try:
                self._interpreter.allocate_tensors()
                self._input_details = self._interpreter.get_input_details()
                self._output_details = self._interpreter.get_output_details()
            except Exception:
                self._interpreter = None

        self._load_labels()

    def _load_labels(self):
        """Load sign labels from a text file next to the model."""
        labels_path = os.path.splitext(self._model_path)[0] + "_labels.txt"
        if os.path.exists(labels_path):
            with open(labels_path, "r") as f:
                self._labels = [line.strip() for line in f if line.strip()]
        else:
            # Default ASL alphabet
            self._labels = list("ABCDEFGHIJKLMNOPQRSTUVWXYZ")

    def classify(self, landmarks: np.ndarray) -> tuple[str, float] | None:
        """Add landmarks to buffer. When full, classify the sequence.

        Returns (label, confidence) or None.
        """
        self._buffer.append(landmarks)

        if len(self._buffer) < self.BUFFER_SIZE:
            return None

        if self._interpreter is None:
            return self._mock_classify()

        return self._run_inference()

    def _run_inference(self) -> tuple[str, float] | None:
        """Run TFLite inference on the buffered sequence."""
        sequence = np.array(list(self._buffer), dtype=np.float32)
        input_shape = self._input_details[0]["shape"]
        # Reshape to match model input: (1, BUFFER_SIZE, features)
        sequence = sequence.reshape(input_shape)

        self._interpreter.set_tensor(self._input_details[0]["index"], sequence)
        self._interpreter.invoke()
        output = self._interpreter.get_tensor(self._output_details[0]["index"])

        prediction = output[0]
        idx = int(np.argmax(prediction))
        confidence = float(prediction[idx])

        if confidence < self._confidence_threshold:
            return None

        label = self._labels[idx] if idx < len(self._labels) else f"SIGN_{idx}"
        self._buffer.clear()
        return label, confidence

    def _mock_classify(self) -> tuple[str, float] | None:
        """Mock classification when no model is loaded — for development."""
        self._buffer.clear()
        return None

    def set_model(self, model_path: str):
        """Hot-swap the model file."""
        self._model_path = model_path
        self._buffer.clear()
        self._load_model()
