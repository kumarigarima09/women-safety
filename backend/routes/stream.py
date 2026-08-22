"""
backend/routes/stream.py
─────────────────────────
WebSocket endpoint: streams JPEG frames from a running CameraPipeline
to a connected browser client in real-time.

Also broadcasts alert JSON to all connected dashboard clients via
a shared alert queue.
"""

import asyncio
import base64
import json
import queue
import threading
from typing import Any

import cv2
import numpy as np
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from loguru import logger

from ai_engine import CameraPipeline, AlertFrame

router = APIRouter(prefix="/ws", tags=["stream"])

# ── Global state ──────────────────────────────────────────────────────────────
_pipelines: dict[str, CameraPipeline] = {}
_alert_queues: dict[str, queue.Queue] = {}   # camera_id → alert queue
_connections: dict[str, list[WebSocket]] = {}  # camera_id → list of sockets


def _get_or_start_pipeline(camera_id: str, stream_url: str, is_isolated: bool) -> CameraPipeline:
    if camera_id in _pipelines:
        return _pipelines[camera_id]

    q: queue.Queue = queue.Queue(maxsize=5)
    _alert_queues[camera_id] = q
    _connections[camera_id] = []

    def on_frame(af: AlertFrame):
        try:
            q.put_nowait(af)
        except queue.Full:
            pass   # drop oldest frame to maintain real-time streaming

    pipeline = CameraPipeline(
        source=stream_url,
        camera_id=camera_id,
        is_isolated_zone=is_isolated,
        on_alert_frame=on_frame,
        target_fps=10,
    )
    pipeline.start()
    _pipelines[camera_id] = pipeline
    logger.info(f"Started pipeline for {camera_id}")
    return pipeline


def _encode_frame_to_b64(frame: np.ndarray) -> str:
    _, buf = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 70])
    return base64.b64encode(buf).decode("utf-8")


@router.websocket("/stream/{camera_id}")
async def stream_feed(websocket: WebSocket, camera_id: str):
    """
    WebSocket endpoint.
    Send a JSON message after connecting:
      {"stream_url": "0", "is_isolated": false}
    Receives continuous JPEG frames + alert data.
    """
    await websocket.accept()
    logger.info(f"WS client connected to {camera_id}")

    try:
        # First message configures the stream
        config = await websocket.receive_json()
        stream_url = config.get("stream_url", "0")
        # "0" = Mac webcam, or an RTSP URL string
        try:
            stream_url = int(stream_url)
        except (ValueError, TypeError):
            pass
        is_isolated = config.get("is_isolated", False)

        _get_or_start_pipeline(camera_id, stream_url, is_isolated)
        q = _alert_queues[camera_id]

        while True:
            await asyncio.sleep(0.05)   # ~20 pushes/sec max
            try:
                alert_frame: AlertFrame = q.get_nowait()
            except queue.Empty:
                continue

            payload: dict[str, Any] = {
                "camera_id":   alert_frame.camera_id,
                "timestamp":   alert_frame.timestamp,
                "severity":    alert_frame.severity,
                "has_alert":   alert_frame.has_alert,
                "frame":       _encode_frame_to_b64(alert_frame.annotated_frame),
                "alerts": {
                    "lone_woman": [
                        {"track_id": a.track_id,
                         "is_high_risk_time": a.is_high_risk_time,
                         "distance": a.nearest_person_distance}
                        for a in alert_frame.lone_woman_alerts
                    ],
                    "sos_gesture": [
                        {"gesture": a.gesture_type, "confidence": a.confidence}
                        for a in alert_frame.sos_alerts
                    ],
                    "weapon": [
                        {"type": a.weapon_type, "confidence": a.confidence}
                        for a in alert_frame.weapon_alerts
                    ],
                },
            }
            await websocket.send_text(json.dumps(payload))

    except WebSocketDisconnect:
        logger.info(f"WS client disconnected from {camera_id}")
    except Exception as e:
        logger.error(f"WS error on {camera_id}: {e}")
        await websocket.close()
