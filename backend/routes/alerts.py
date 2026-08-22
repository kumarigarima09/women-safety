"""
backend/routes/alerts.py
─────────────────────────
REST endpoints for retrieving and reviewing alert history.
"""

from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from loguru import logger

from backend.database.connection import get_db
from backend.database.models import Alert

router = APIRouter(prefix="/api/alerts", tags=["alerts"])


@router.get("/")
def list_alerts(
    limit: int = Query(50, ge=1, le=500),
    camera_id: Optional[str] = None,
    alert_type: Optional[str] = None,
    reviewed: Optional[bool] = None,
    db: Session = Depends(get_db),
):
    """Return paginated, filtered alert history."""
    query = db.query(Alert).order_by(Alert.created_at.desc())
    if camera_id:
        query = query.filter(Alert.camera_id == camera_id)
    if alert_type:
        query = query.filter(Alert.alert_type == alert_type)
    if reviewed is not None:
        query = query.filter(Alert.reviewed == reviewed)
    return query.limit(limit).all()


@router.post("/")
def create_alert(
    camera_id: str,
    alert_type: str,
    severity: str,
    details: Optional[dict] = None,
    db: Session = Depends(get_db),
):
    """Called internally by the pipeline to persist a new alert."""
    alert = Alert(
        camera_id=camera_id,
        alert_type=alert_type,
        severity=severity,
        details=details or {},
        created_at=datetime.utcnow(),
    )
    db.add(alert)
    db.commit()
    db.refresh(alert)
    logger.info(f"Alert logged: {alert_type} on {camera_id} (id={alert.id})")
    return alert


@router.patch("/{alert_id}/review")
def mark_reviewed(alert_id: int, db: Session = Depends(get_db)):
    """Mark an alert as reviewed by the operator."""
    alert = db.query(Alert).filter(Alert.id == alert_id).first()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    alert.reviewed = True
    db.commit()
    return {"status": "ok", "alert_id": alert_id}
