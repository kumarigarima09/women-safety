"""
tests/test_sos_gesture.py
──────────────────────────
Unit tests for SOS gesture heuristics (without requiring a live camera).
Tests the mathematical rules directly on mocked landmark data.
"""

import pytest
import types
import numpy as np

from ai_engine.sos_gesture import LM
def _make_landmark(x: float, y: float, z: float = 0.0):
    lm = types.SimpleNamespace(x=x, y=y, z=z, visibility=1.0)
    return lm


def _make_landmarks(overrides: dict = None):
    """
    Build a 33-landmark MediaPipe Pose pose_landmarks.landmark mock.
    Overrides is a dict of {landmark_idx: (x, y)}.
    Default = all landmarks at (0.5, 0.5).
    """
    lms = types.SimpleNamespace()
    landmark_list = [_make_landmark(0.5, 0.5) for _ in range(33)]
    if overrides:
        for idx, (x, y) in overrides.items():
            landmark_list[idx] = _make_landmark(x, y)
    lms.landmark = landmark_list
    return lms


class TestArmsRaised:
    """Tests for the _both_arms_raised heuristic."""

    def _call(self, lms):
        from ai_engine.sos_gesture import SosGestureDetector, LM
        det = SosGestureDetector.__new__(SosGestureDetector)
        return det._both_arms_raised(lms)

    def test_arms_above_nose(self):
        """Both wrists clearly above nose → high confidence."""
        lms = _make_landmarks({
            LM.NOSE: (0.5, 0.6),          # nose lower on screen (higher y)
            LM.LEFT_WRIST:  (0.3, 0.3),   # wrist higher on screen (lower y)
            LM.RIGHT_WRIST: (0.7, 0.3),
        })
        
        conf = self._call(lms)
        assert conf > 0.5, f"Expected >0.5, got {conf}"

    def test_arms_at_side(self):
        """Wrists lower than nose → 0 confidence."""
        
        lms = _make_landmarks({
            LM.NOSE: (0.5, 0.2),
            LM.LEFT_WRIST:  (0.3, 0.7),
            LM.RIGHT_WRIST: (0.7, 0.7),
        })
        conf = self._call(lms)
        assert conf == 0.0


class TestDefensivePosture:
    """Tests for the _defensive_posture heuristic."""

    def _call(self, lms):
        from ai_engine.sos_gesture import SosGestureDetector, LM
        det = SosGestureDetector.__new__(SosGestureDetector)
        return det._defensive_posture(lms)

    def test_arms_crossed(self):
        """Left wrist on right side, right wrist on left side → crossed."""
        
        lms = _make_landmarks({
            LM.LEFT_SHOULDER:  (0.3, 0.4),
            LM.RIGHT_SHOULDER: (0.7, 0.4),
            LM.LEFT_WRIST:  (0.6, 0.5),   # left wrist on right side
            LM.RIGHT_WRIST: (0.5, 0.5),   # right wrist left of left wrist
        })
        conf = self._call(lms)
        assert conf > 0.5

    def test_arms_normal(self):
        """Normal arm position → 0 confidence."""
        
        lms = _make_landmarks({
            LM.LEFT_SHOULDER:  (0.3, 0.4),
            LM.RIGHT_SHOULDER: (0.7, 0.4),
            LM.LEFT_WRIST:  (0.2, 0.5),
            LM.RIGHT_WRIST: (0.8, 0.5),
        })
        conf = self._call(lms)
        assert conf == 0.0
