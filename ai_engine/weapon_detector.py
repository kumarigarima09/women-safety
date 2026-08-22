"""
ai_engine/weapon_detector.py
──────────────────────────────
Detects dangerous objects (knives, bats, guns etc.) in video frames
using YOLOv8 trained on a custom/open dataset.

Can be swapped for a custom fine-tuned YOLO model by providing
`model_path` to the constructor.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

import cv2
import numpy as np
from ultralytics import YOLO
from loguru import logger


# ── Classes treated as weapons (adjust per your YOLO model) ──────────────────
WEAPON_CLASSES = {"knife", "gun", "pistol", "bat", "scissors", "sword"}


# ── Data Container ────────────────────────────────────────────────────────────

@dataclass
class WeaponAlert:
    weapon_type: str
    confidence: float
    bbox: tuple[int, int, int, int]
    camera_id: str
    timestamp: str


# ── Detector ──────────────────────────────────────────────────────────────────

class WeaponDetector:
    """
    Wraps a YOLO model and filters detections to weapon class names only.
    Default model: yolov8n.pt (COCO). Replace with a weapon-specific model
    for better accuracy.
    """

    def __init__(
        self,
        model_path: str = "yolov8n.pt",
        camera_id: str = "cam-01",
        conf_threshold: float = 0.50,
    ):
        self.camera_id = camera_id
        self.conf_threshold = conf_threshold
        self.yolo = YOLO(model_path)
        logger.info(f"WeaponDetector loaded model: {model_path}")

    def process_frame(self, frame: np.ndarray) -> list[WeaponAlert]:
        results = self.yolo(frame, conf=self.conf_threshold, verbose=False)
        alerts: list[WeaponAlert] = []

        for r in results:
            if r.boxes is None:
                continue
            for box in r.boxes:
                class_id = int(box.cls[0])
                class_name = self.yolo.names.get(class_id, "").lower()
                if class_name in WEAPON_CLASSES:
                    x1, y1, x2, y2 = map(int, box.xyxy[0].tolist())
                    conf = float(box.conf[0])
                    logger.critical(
                        f"[WEAPON] '{class_name}' detected (conf={conf:.0%}) "
                        f"on {self.camera_id}"
                    )
                    alerts.append(WeaponAlert(
                        weapon_type=class_name,
                        confidence=round(conf, 3),
                        bbox=(x1, y1, x2, y2),
                        camera_id=self.camera_id,
                        timestamp=datetime.utcnow().isoformat(),
                    ))

        return alerts

    def annotate_frame(
        self, frame: np.ndarray, alerts: list[WeaponAlert]
    ) -> np.ndarray:
        annotated = frame.copy()
        for alert in alerts:
            x1, y1, x2, y2 = alert.bbox
            cv2.rectangle(annotated, (x1, y1), (x2, y2), (0, 0, 255), 3)
            cv2.putText(
                annotated,
                f"WEAPON: {alert.weapon_type} ({alert.confidence:.0%})",
                (x1, y1 - 10),
                cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2,
            )
        return annotated
