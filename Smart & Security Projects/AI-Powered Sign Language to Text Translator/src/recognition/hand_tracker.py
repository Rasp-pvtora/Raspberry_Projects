"""MediaPipe hand landmark extraction — 21 landmarks per hand, normalized."""

import os

import cv2
import numpy as np
import mediapipe as mp


class HandTracker:
    """Extract and normalize hand landmarks using MediaPipe Hands."""

    def __init__(self):
        self._mp_hands = mp.solutions.hands
        self._mp_draw = mp.solutions.drawing_utils
        two_hand = os.getenv("TWO_HAND_ENABLED", "true").lower() == "true"
        max_hands = 2 if two_hand else 1

        self._hands = self._mp_hands.Hands(
            static_image_mode=False,
            max_num_hands=max_hands,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5,
        )

    def process_frame(self, frame: np.ndarray) -> tuple[np.ndarray | None, np.ndarray]:
        """Process a BGR frame. Returns (landmarks_array, annotated_frame).

        landmarks_array: shape (63,) for one hand or (126,) for two hands, or None.
        annotated_frame: original frame with hand skeleton drawn.
        """
        annotated = frame.copy()
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = self._hands.process(rgb)

        if not results.multi_hand_landmarks:
            return None, annotated

        all_landmarks = []
        for hand_landmarks in results.multi_hand_landmarks:
            self._mp_draw.draw_landmarks(
                annotated, hand_landmarks, self._mp_hands.HAND_CONNECTIONS,
            )
            raw = self._extract_landmarks(hand_landmarks)
            normalized = self._normalize(raw)
            all_landmarks.append(normalized)

        if len(all_landmarks) == 1:
            return all_landmarks[0], annotated
        # Two hands — concatenate to 126 features
        return np.concatenate(all_landmarks[:2]), annotated

    def _extract_landmarks(self, hand_landmarks) -> np.ndarray:
        """Extract 21 landmarks as flat array of 63 values (x, y, z)."""
        coords = []
        for lm in hand_landmarks.landmark:
            coords.extend([lm.x, lm.y, lm.z])
        return np.array(coords, dtype=np.float32)

    def _normalize(self, landmarks: np.ndarray) -> np.ndarray:
        """Translate to wrist origin and scale to unit size."""
        reshaped = landmarks.reshape(-1, 3)
        wrist = reshaped[0].copy()
        reshaped -= wrist  # translate to wrist origin
        max_dist = np.max(np.linalg.norm(reshaped, axis=1))
        if max_dist > 0:
            reshaped /= max_dist
        return reshaped.flatten()
