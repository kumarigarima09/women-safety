"""
ai_engine/pipeline.py
──────────────────────
Master AI pipeline that chains all detectors together for a single camera.

Flow per frame:
  VideoReader → GenderDetector → LoneWomanDetector
                               → SosGestureDetector
                               → WeaponDetector
                               → emit combined AlertFrame via callback
"""

from __future__ import annotations

import asyncio
import threading
import time
from dataclasses import dataclass, field
from typing import Callable, Awaitable

import cv2
import numpy as np
from loguru import logger

from .gender_classifier import GenderDetector, PersonDetection
from .lone_woman_detector import LoneWomanDetector, LoneWomanAlert
from .sos_gesture import SosGestureDetector, SosGestureAlert
from .weapon_detector import WeaponDetector, WeaponAlert
from .video_reader import VideoReader


# ── Unified alert container ───────────────────────────────────────────────────

@dataclass
class AlertFrame:
    camera_id: str
    timestamp: str
    annotated_frame: np.ndarray
    persons: list[PersonDetection]
    lone_woman_alerts: list[LoneWomanAlert] = field(default_factory=list)
    sos_alerts: list[SosGestureAlert] = field(default_factory=list)
    weapon_alerts: list[WeaponAlert] = field(default_factory=list)

    @property
    def has_alert(self) -> bool:
        return bool(
            self.lone_woman_alerts or self.sos_alerts or self.weapon_alerts
        )

    @property
    def severity(self) -> str:
        if self.weapon_alerts or self.sos_alerts:
            return "HIGH"
        if self.lone_woman_alerts:
            return "MEDIUM"
        return "NORMAL"


# ── Pipeline ──────────────────────────────────────────────────────────────────

class CameraPipeline:
    """
    Runs all AI modules on a continuous video feed.
    on_alert_frame is called with an AlertFrame every time a frame is processed.
    """

    def __init__(
        self,
        source,
        camera_id: str = "cam-01",
        is_isolated_zone: bool = False,
        on_alert_frame: Callable[[AlertFrame], None] | None = None,
        target_fps: int = 10,          # process N frames per second (save CPU)
        privacy_blur: bool = True,     # blur non-threat persons' faces
    ):
        self.camera_id = camera_id
        self.on_alert_frame = on_alert_frame
        self.target_fps = target_fps
        self.privacy_blur = privacy_blur
        self._stopped = False

        self.reader = VideoReader(source=source, fps_limit=30)
        self.gender_det = GenderDetector()
        self.lone_det = LoneWomanDetector(
            camera_id=camera_id, is_isolated_zone=is_isolated_zone
        )
        self.sos_det = SosGestureDetector(camera_id=camera_id)
        self.weapon_det = WeaponDetector(camera_id=camera_id)

        self._thread = threading.Thread(target=self._run_loop, daemon=True)
        logger.info(f"CameraPipeline ready for {camera_id} (source={source})")

    def start(self):
        self._thread.start()
        logger.info(f"Pipeline started: {self.camera_id}")

    def stop(self):
        self._stopped = True
        self.reader.release()
        logger.info(f"Pipeline stopped: {self.camera_id}")

    def _run_loop(self):
        from datetime import datetime, timezone
        frame_interval = 1.0 / self.target_fps

        while not self._stopped:
            t0 = time.time()
            frame = self.reader.read()
            if frame is None:
                time.sleep(0.1)
                continue

            # --- Run AI detectors ---
            persons      = self.gender_det.process_frame(frame)
            lone_alerts  = self.lone_det.process_frame(persons)
            sos_alerts   = self.sos_det.process_frame(frame)
            weapon_alerts = self.weapon_det.process_frame(frame)

            # --- Annotate frame ---
            annotated = self.gender_det.annotate_frame(frame, persons)
            annotated = self.sos_det.annotate_frame(annotated, sos_alerts)
            annotated = self.weapon_det.annotate_frame(annotated, weapon_alerts)

            if self.privacy_blur:
                annotated = self._apply_privacy_blur(annotated, persons, lone_alerts)

            ts = datetime.now(timezone.utc).isoformat()
            alert_frame = AlertFrame(
                camera_id=self.camera_id,
                timestamp=ts,
                annotated_frame=annotated,
                persons=persons,
                lone_woman_alerts=lone_alerts,
                sos_alerts=sos_alerts,
                weapon_alerts=weapon_alerts,
            )

            if self.on_alert_frame:
                self.on_alert_frame(alert_frame)

            elapsed = time.time() - t0
            sleep_time = max(0, frame_interval - elapsed)
            time.sleep(sleep_time)

    def _apply_privacy_blur(
        self,
        frame: np.ndarray,
        persons: list[PersonDetection],
        lone_alerts: list[LoneWomanAlert],
    ) -> np.ndarray:
        """
        Blur faces of persons who are NOT in any active alert (privacy protection).
        """
        alert_track_ids = {a.track_id for a in lone_alerts}
        blurred = frame.copy()

        for person in persons:
            if person.track_id in alert_track_ids:
                continue   # keep threat subjects un-blurred for review
            x1, y1, x2, y2 = person.bbox
            face_y2 = y1 + max(1, (y2 - y1) // 4)
            roi = blurred[y1:face_y2, x1:x2]
            if roi.size > 0:
                roi = cv2.GaussianBlur(roi, (51, 51), 0)
                blurred[y1:face_y2, x1:x2] = roi

        return blurred
