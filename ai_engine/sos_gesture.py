"""
ai_engine/sos_gesture.py
─────────────────────────
Detects SOS / distress gestures using MediaPipe Pose keypoints.

Supported gestures:
  1. BOTH_ARMS_RAISED   — Both wrists above the nose landmark
  2. RAPID_ARM_WAVE     — Wrist velocity spike over consecutive frames
  3. DEFENSIVE_POSTURE  — Arms crossed in front of body

Each detected gesture triggers a SosGestureAlert.
"""

from __future__ import annotations

import math
import time
from dataclasses import dataclass
from datetime import datetime
from typing import NamedTuple

import cv2
import numpy as np
from loguru import logger

try:
    import mediapipe as mp
    _mp_pose = mp.solutions.pose
    _mp_drawing = mp.solutions.drawing_utils
    HAS_MEDIAPIPE_SOLUTIONS = True
except (ImportError, AttributeError):
    logger.warning("mediapipe.solutions is not available (common on Apple Silicon). SOS gesture detection will be disabled.")
    HAS_MEDIAPIPE_SOLUTIONS = False
    _mp_pose = None
    _mp_drawing = None

# ── MediaPipe landmark indices ────────────────────────────────────────────────
class LM:
    NOSE = 0
    LEFT_WRIST  = 15
    RIGHT_WRIST = 16
    LEFT_ELBOW  = 13
    RIGHT_ELBOW = 14
    LEFT_SHOULDER  = 11
    RIGHT_SHOULDER = 12
    LEFT_HIP   = 23
    RIGHT_HIP  = 24


# ── Config ────────────────────────────────────────────────────────────────────
WAVE_VELOCITY_THRESHOLD = 0.05    # normalised units per frame
WAVE_HISTORY_LEN = 8              # frames to track velocity history


# ── Data Containers ───────────────────────────────────────────────────────────

@dataclass
class SosGestureAlert:
    gesture_type: str              # e.g. "BOTH_ARMS_RAISED"
    confidence: float
    camera_id: str
    timestamp: str
    frame_snapshot: np.ndarray     # frame at time of alert (for review)


# ── Detector ──────────────────────────────────────────────────────────────────

class SosGestureDetector:
    """
    Uses MediaPipe Pose to extract keypoints and applies rule-based
    heuristics to identify distress gestures.
    """

    def __init__(self, camera_id: str = "cam-01", min_detection_confidence: float = 0.6):
        self.camera_id = camera_id
        if HAS_MEDIAPIPE_SOLUTIONS:
            self.pose = _mp_pose.Pose(
                static_image_mode=False,
                model_complexity=1,           # 0=lite, 1=full, 2=heavy
                enable_segmentation=False,
                min_detection_confidence=min_detection_confidence,
                min_tracking_confidence=0.5,
            )
        else:
            self.pose = None

        # Per-person wrist position history for wave detection
        self._left_wrist_history: list[float] = []
        self._right_wrist_history: list[float] = []

    def _get_landmark(self, landmarks, idx: int) -> tuple[float, float]:
        lm = landmarks.landmark[idx]
        return (lm.x, lm.y)   # normalised [0, 1]

    def _both_arms_raised(self, lms) -> float:
        """Returns confidence (0–1) that both wrists are above the nose."""
        nose_y   = lms.landmark[LM.NOSE].y
        left_y   = lms.landmark[LM.LEFT_WRIST].y
        right_y  = lms.landmark[LM.RIGHT_WRIST].y
        # In MediaPipe, smaller y = higher on screen
        left_up  = nose_y - left_y
        right_up = nose_y - right_y
        if left_up > 0.05 and right_up > 0.05:
            return min(1.0, (left_up + right_up) / 0.4)
        return 0.0

    def _rapid_wave(self, lms) -> float:
        """Returns confidence that wrist velocity spike indicates waving."""
        left_x = lms.landmark[LM.LEFT_WRIST].x
        right_x = lms.landmark[LM.RIGHT_WRIST].x

        self._left_wrist_history.append(left_x)
        self._right_wrist_history.append(right_x)

        if len(self._left_wrist_history) > WAVE_HISTORY_LEN:
            self._left_wrist_history.pop(0)
            self._right_wrist_history.pop(0)

        if len(self._left_wrist_history) < 4:
            return 0.0

        # Check max velocity (absolute difference between successive positions)
        left_vel  = max(abs(self._left_wrist_history[i] - self._left_wrist_history[i-1])
                        for i in range(1, len(self._left_wrist_history)))
        right_vel = max(abs(self._right_wrist_history[i] - self._right_wrist_history[i-1])
                        for i in range(1, len(self._right_wrist_history)))

        avg_vel = (left_vel + right_vel) / 2
        if avg_vel > WAVE_VELOCITY_THRESHOLD:
            return min(1.0, avg_vel / 0.15)
        return 0.0

    def _defensive_posture(self, lms) -> float:
        """
        Detect arms crossed in front: left wrist is on the right side of body
        and right wrist is on the left side (swapped x positions).
        """
        left_wrist_x  = lms.landmark[LM.LEFT_WRIST].x
        right_wrist_x = lms.landmark[LM.RIGHT_WRIST].x
        left_shoulder_x  = lms.landmark[LM.LEFT_SHOULDER].x
        right_shoulder_x = lms.landmark[LM.RIGHT_SHOULDER].x

        # Wrists should be close to each other and near body centre
        crossed = left_wrist_x > right_wrist_x  # hands swapped
        close   = abs(left_wrist_x - right_wrist_x) < 0.15
        if crossed and close:
            return 0.75
        return 0.0

    def process_frame(
        self, frame: np.ndarray
    ) -> list[SosGestureAlert]:
        """Process one frame and return any detected SOS alerts."""
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = self.pose.process(rgb)
        alerts: list[SosGestureAlert] = []

        if not results.pose_landmarks:
            return alerts

        lms = results.pose_landmarks
        checks = {
            "BOTH_ARMS_RAISED": self._both_arms_raised(lms),
            "RAPID_ARM_WAVE":   self._rapid_wave(lms),
            "DEFENSIVE_POSTURE": self._defensive_posture(lms),
        }

        for gesture, conf in checks.items():
            if conf > 0.6:
                logger.warning(f"[SOS] Gesture detected: {gesture} (conf={conf:.2f})")
                alerts.append(SosGestureAlert(
                    gesture_type=gesture,
                    confidence=round(conf, 3),
                    camera_id=self.camera_id,
                    timestamp=datetime.utcnow().isoformat(),
                    frame_snapshot=frame.copy(),
                ))

        return alerts

    def annotate_frame(
        self, frame: np.ndarray, alerts: list[SosGestureAlert]
    ) -> np.ndarray:
        """Overlay skeleton and alert label on the frame."""
        annotated = frame.copy()
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = self.pose.process(rgb)
        if results.pose_landmarks:
            mp.solutions.drawing_utils.draw_landmarks(
                annotated,
                results.pose_landmarks,
                _mp_pose.POSE_CONNECTIONS,
            )
        for alert in alerts:
            cv2.putText(
                annotated,
                f"SOS: {alert.gesture_type}",
                (20, 50), cv2.FONT_HERSHEY_SIMPLEX, 1.2,
                (0, 0, 255), 3,
            )
        return annotated
