"""
tests/test_lone_woman.py
─────────────────────────
Unit tests for the LoneWomanDetector module.
"""

import pytest
from ai_engine.gender_classifier import PersonDetection
from ai_engine.lone_woman_detector import LoneWomanDetector


def make_person(x1, y1, x2, y2, gender="woman", tid=1):
    return PersonDetection(bbox=(x1, y1, x2, y2), gender=gender, track_id=tid)


class TestLoneWomanDetector:
    def setup_method(self):
        self.det = LoneWomanDetector(
            camera_id="test-cam",
            is_isolated_zone=True,   # always treat as isolated zone → no time dep
            pixel_threshold=200,
            frame_threshold=1,       # alert on 1st frame for test speed
        )

    def test_no_alert_when_not_alone(self):
        """Woman with a person nearby should NOT trigger alert."""
        woman = make_person(100, 100, 200, 300, "woman", tid=1)
        other = make_person(150, 100, 250, 300, "man",   tid=2)
        alerts = self.det.process_frame([woman, other])
        assert len(alerts) == 0

    def test_alert_when_isolated(self):
        """Woman far from everyone in an isolated zone should trigger alert."""
        woman = make_person(100, 100, 200, 300, "woman", tid=1)
        other = make_person(700, 100, 800, 300, "man",   tid=2)
        alerts = self.det.process_frame([woman, other])
        assert len(alerts) == 1
        assert alerts[0].track_id == 1

    def test_no_alert_when_no_women(self):
        """Frame with only men should never produce an alert."""
        man1 = make_person(100, 100, 200, 300, "man", tid=1)
        man2 = make_person(700, 100, 800, 300, "man", tid=2)
        alerts = self.det.process_frame([man1, man2])
        assert len(alerts) == 0

    def test_counter_resets_when_rejoined(self):
        """Alert counter should reset once another person comes close."""
        woman = make_person(100, 100, 200, 300, "woman", tid=1)
        far_man = make_person(700, 100, 800, 300, "man", tid=2)
        # First frame — isolated
        self.det.process_frame([woman, far_man])
        # Second frame — person comes close
        close_man = make_person(120, 100, 220, 300, "man", tid=2)
        alerts = self.det.process_frame([woman, close_man])
        assert len(alerts) == 0
        assert self.det._isolation_counters.get(1, 0) == 0
