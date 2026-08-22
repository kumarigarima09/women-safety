"""
ai_engine/video_reader.py
─────────────────────────
Provides a thread-safe VideoReader that pulls frames from either:
  - A local webcam  (default index 0  – Mac FaceTime HD camera)
  - An RTSP stream  (e.g. "rtsp://user:pass@192.168.1.100:554/stream")
  - A local video file path

Usage:
    reader = VideoReader(source=0)          # Mac webcam
    reader = VideoReader(source="rtsp://…") # IP camera
    for frame in reader:
        # frame is a BGR numpy array
        process(frame)
    reader.release()
"""

import threading
import time
from typing import Union

import cv2
import numpy as np
from loguru import logger


class VideoReader:
    """
    Thread-safe video reader with a background capture thread.
    Always returns the latest frame, dropping stale ones to keep real-time.
    """

    def __init__(
        self,
        source: Union[int, str] = 0,
        width: int = 1280,
        height: int = 720,
        fps_limit: int = 30,
    ):
        self.source = source
        self.width = width
        self.height = height
        self.fps_limit = fps_limit
        self._frame: np.ndarray | None = None
        self._lock = threading.Lock()
        self._stopped = False

        self.cap = cv2.VideoCapture(source)
        if not self.cap.isOpened():
            raise RuntimeError(f"Cannot open video source: {source}")

        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
        self.cap.set(cv2.CAP_PROP_FPS, fps_limit)
        # For RTSP: lower buffer to reduce latency
        self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)

        logger.info(f"VideoReader initialised — source: {source}")
        self._thread = threading.Thread(target=self._capture_loop, daemon=True)
        self._thread.start()

    def _capture_loop(self):
        delay = 1.0 / self.fps_limit
        while not self._stopped:
            ret, frame = self.cap.read()
            if not ret:
                logger.warning("Frame grab failed — reconnecting in 2s…")
                time.sleep(2)
                self.cap.open(self.source)
                continue
            with self._lock:
                self._frame = frame
            time.sleep(delay)

    def read(self) -> np.ndarray | None:
        """Return the most recent frame (or None if not yet available)."""
        with self._lock:
            return self._frame.copy() if self._frame is not None else None

    def __iter__(self):
        return self

    def __next__(self) -> np.ndarray:
        frame = self.read()
        if frame is None or self._stopped:
            raise StopIteration
        return frame

    def release(self):
        self._stopped = True
        self._thread.join(timeout=2)
        self.cap.release()
        logger.info("VideoReader released.")
