"""
ai_engine/gender_classifier.py
──────────────────────────────
Two-stage pipeline:
  Stage 1: YOLOv8n detects all persons in the frame → bounding boxes
  Stage 2: A lightweight MobileNet classifier predicts gender (M/F)
            on each cropped bounding box

The PyTorch inference device is auto-selected:
  - Apple Silicon Mac → "mps"
  - NVIDIA GPU       → "cuda"
  - Fallback         → "cpu"
"""

from __future__ import annotations

import cv2
import numpy as np
import torch
import torch.nn as nn
import torchvision.models as models
import torchvision.transforms as T
from dataclasses import dataclass, field
from ultralytics import YOLO
from loguru import logger


# ── Device selection (macOS MPS aware) ──────────────────────────────────────

def _select_device() -> torch.device:
    if torch.backends.mps.is_available():
        logger.info("Hardware: Apple Silicon MPS GPU")
        return torch.device("mps")
    if torch.cuda.is_available():
        logger.info(f"Hardware: CUDA GPU ({torch.cuda.get_device_name(0)})")
        return torch.device("cuda")
    logger.info("Hardware: CPU (no GPU detected)")
    return torch.device("cpu")


DEVICE = _select_device()


# ── Data containers ──────────────────────────────────────────────────────────

@dataclass
class PersonDetection:
    bbox: tuple[int, int, int, int]      # (x1, y1, x2, y2)
    gender: str                           # "woman" | "man" | "unknown"
    gender_conf: float = 0.0
    track_id: int = -1


# ── Gender Classifier (MobileNetV3-Small fine-tuned on face data) ────────────

class GenderClassifier(nn.Module):
    """
    Lightweight binary classifier: man vs woman.
    Uses MobileNetV3-Small for fast inference on Mac CPU/MPS.
    """

    def __init__(self, model_path: str | None = None):
        super().__init__()
        backbone = models.mobilenet_v3_small(
            weights=models.MobileNet_V3_Small_Weights.DEFAULT
        )
        # Replace the classifier head for binary output
        in_features = backbone.classifier[-1].in_features
        backbone.classifier[-1] = nn.Linear(in_features, 2)
        self.model = backbone

        if model_path:
            state = torch.load(model_path, map_location=DEVICE)
            self.model.load_state_dict(state)
            logger.info(f"Loaded gender model weights from: {model_path}")
        else:
            logger.warning(
                "No model_path provided — using untrained weights."
                " Train via scripts/train_gender_model.py"
            )

        self.model.to(DEVICE).eval()
        self._transform = T.Compose([
            T.ToPILImage(),
            T.Resize((64, 64)),
            T.ToTensor(),
            T.Normalize(mean=[0.485, 0.456, 0.406],
                        std=[0.229, 0.224, 0.225]),
        ])

    @torch.inference_mode()
    def predict(self, crop_bgr: np.ndarray) -> tuple[str, float]:
        """
        Returns (label, confidence) for one person crop.
        crop_bgr: numpy BGR image (from cv2)
        """
        if crop_bgr.size == 0:
            return "unknown", 0.0
        rgb = cv2.cvtColor(crop_bgr, cv2.COLOR_BGR2RGB)
        tensor = self._transform(rgb).unsqueeze(0).to(DEVICE)
        logits = self.model(tensor)
        probs = torch.softmax(logits, dim=1)[0]
        idx = probs.argmax().item()
        label = "man" if idx == 0 else "woman"
        return label, round(probs[idx].item(), 3)


# ── Combined Detector ────────────────────────────────────────────────────────

class GenderDetector:
    """
    Runs YOLOv8 person detection + per-crop gender classification.
    Supports optional YOLO tracking (ByteTrack) for persistent IDs.
    """

    PERSON_CLASS_ID = 0   # COCO class index for "person"

    def __init__(
        self,
        yolo_model: str = "yolov8n.pt",
        gender_model_path: str | None = "data/models/gender_detection_model.pth",
        conf_threshold: float = 0.45,
        use_tracker: bool = True,
    ):
        self.conf_threshold = conf_threshold
        self.use_tracker = use_tracker

        logger.info(f"Loading YOLO model: {yolo_model}")
        self.yolo = YOLO(yolo_model)
        self.gender_clf = GenderClassifier(model_path=gender_model_path)

    def process_frame(self, frame: np.ndarray) -> list[PersonDetection]:
        """
        Process one video frame and return a list of PersonDetection objects.
        """
        if self.use_tracker:
            results = self.yolo.track(
                frame, persist=True, classes=[self.PERSON_CLASS_ID],
                conf=self.conf_threshold, verbose=False
            )
        else:
            results = self.yolo(
                frame, classes=[self.PERSON_CLASS_ID],
                conf=self.conf_threshold, verbose=False
            )

        detections: list[PersonDetection] = []
        for r in results:
            boxes = r.boxes
            if boxes is None:
                continue
            for box in boxes:
                x1, y1, x2, y2 = map(int, box.xyxy[0].tolist())
                track_id = int(box.id[0]) if (box.id is not None) else -1

                # Crop the person bounding box and classify gender
                crop = frame[max(0, y1):y2, max(0, x1):x2]
                gender, conf = self.gender_clf.predict(crop)

                detections.append(PersonDetection(
                    bbox=(x1, y1, x2, y2),
                    gender=gender,
                    gender_conf=conf,
                    track_id=track_id,
                ))

        return detections

    def annotate_frame(
        self, frame: np.ndarray, detections: list[PersonDetection]
    ) -> np.ndarray:
        """Draw bounding boxes and gender labels on the frame."""
        annotated = frame.copy()
        for det in detections:
            x1, y1, x2, y2 = det.bbox
            color = (255, 100, 200) if det.gender == "woman" else (100, 150, 255)
            label = f"{det.gender} ({det.gender_conf:.0%})"
            if det.track_id != -1:
                label = f"#{det.track_id} {label}"
            cv2.rectangle(annotated, (x1, y1), (x2, y2), color, 2)
            cv2.putText(
                annotated, label, (x1, y1 - 8),
                cv2.FONT_HERSHEY_SIMPLEX, 0.55, color, 2
            )
        return annotated
