"""
ai_engine/lone_woman_detector.py
─────────────────────────────────
Detects the "Lone Woman" threat scenario:
  A woman is flagged when she is physically isolated from other people
  AND the scene matches a contextual risk condition (night-time, dark area,
  or a restricted zone).

Algorithm:
  1. Receive the list of PersonDetection objects for the current frame.
  2. For each woman, compute the minimum pixel distance to any other person.
  3. If distance > ISOLATION_THRESHOLD for N consecutive frames,
     raise a LoneWomanAlert.

Risk Context:
  - Time-based: 22:00 – 06:00 treated as "high risk hours"
  - (Optional) Camera zone flag: camera can be tagged as "isolated_zone"
"""

from __future__ import annotations

import math
import time
from dataclasses import dataclass, field
from datetime import datetime

from loguru import logger
from .gender_classifier import PersonDetection


# ── Config ────────────────────────────────────────────────────────────────────

ISOLATION_PIXEL_THRESHOLD = 200   # Min distance (px) to be "alone"
HIGH_RISK_HOURS = range(22, 24)    # 22:00–23:59 (add range(0,6) for midnight+)
CONSECUTIVE_FRAMES_TO_ALERT = 10  # ~0.33 sec at 30 FPS


# ── Data Containers ───────────────────────────────────────────────────────────

@dataclass
class LoneWomanAlert:
    track_id: int
    bbox: tuple[int, int, int, int]
    camera_id: str
    timestamp: str
    nearest_person_distance: float
    is_high_risk_time: bool
    is_isolated_zone: bool


# ── Detector ──────────────────────────────────────────────────────────────────

class LoneWomanDetector:
    """
    Maintains per-track isolation frame counters.
    Emits a LoneWomanAlert when a woman is isolated for enough frames.
    """

    def __init__(
        self,
        camera_id: str = "cam-01",
        is_isolated_zone: bool = False,
        pixel_threshold: int = ISOLATION_PIXEL_THRESHOLD,
        frame_threshold: int = CONSECUTIVE_FRAMES_TO_ALERT,
    ):
        self.camera_id = camera_id
        self.is_isolated_zone = is_isolated_zone
        self.pixel_threshold = pixel_threshold
        self.frame_threshold = frame_threshold
        # track_id → consecutive isolation frame count
        self._isolation_counters: dict[int, int] = {}

    @staticmethod
    def _bbox_center(bbox: tuple[int, int, int, int]) -> tuple[float, float]:
        x1, y1, x2, y2 = bbox
        return ((x1 + x2) / 2, (y1 + y2) / 2)

    @staticmethod
    def _distance(a: tuple[float, float], b: tuple[float, float]) -> float:
        return math.hypot(a[0] - b[0], a[1] - b[1])

    def _is_high_risk_time(self) -> bool:
        hour = datetime.now().hour
        return hour in HIGH_RISK_HOURS or hour < 6

    def process_frame(
        self, detections: list[PersonDetection]
    ) -> list[LoneWomanAlert]:
        """
        Called every frame. Returns a list of active LoneWomanAlerts.
        """
        women = [d for d in detections if d.gender == "woman"]
        others = [d for d in detections if d.gender != "woman"]
        alerts: list[LoneWomanAlert] = []
        active_ids = set()

        for woman in women:
            tid = woman.track_id
            active_ids.add(tid)
            wc = self._bbox_center(woman.bbox)

            # Min distance to any other person in the frame
            if others:
                min_dist = min(
                    self._distance(wc, self._bbox_center(o.bbox)) for o in others
                )
            else:
                min_dist = float("inf")

            is_isolated = min_dist > self.pixel_threshold
            is_risky_time = self._is_high_risk_time()
            is_risky = is_isolated and (is_risky_time or self.is_isolated_zone)

            if is_risky:
                self._isolation_counters[tid] = self._isolation_counters.get(tid, 0) + 1
            else:
                self._isolation_counters[tid] = 0

            if self._isolation_counters.get(tid, 0) >= self.frame_threshold:
                logger.warning(
                    f"[LoneWoman] Track #{tid} isolated for "
                    f"{self._isolation_counters[tid]} frames | "
                    f"dist={min_dist:.0f}px | risk_time={is_risky_time}"
                )
                alerts.append(LoneWomanAlert(
                    track_id=tid,
                    bbox=woman.bbox,
                    camera_id=self.camera_id,
                    timestamp=datetime.utcnow().isoformat(),
                    nearest_person_distance=round(min_dist, 2),
                    is_high_risk_time=is_risky_time,
                    is_isolated_zone=self.is_isolated_zone,
                ))

        # Prune counters for tracks no longer in frame
        stale = set(self._isolation_counters) - active_ids
        for sid in stale:
            del self._isolation_counters[sid]

        return alerts
