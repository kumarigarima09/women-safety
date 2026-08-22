"""
backend/routes/hotspots.py
───────────────────────────
Endpoints to retrieve hotspot geographic data and trigger re-aggregation.

Hotspot computation uses DBSCAN clustering on historical alert coordinates.
"""

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session
from loguru import logger

from backend.database.connection import get_db
from backend.database.models import Alert, Hotspot, Camera

router = APIRouter(prefix="/api/hotspots", tags=["hotspots"])


@router.get("/")
def get_hotspots(db: Session = Depends(get_db)):
    """Return all computed hotspots."""
    return db.query(Hotspot).order_by(Hotspot.risk_score.desc()).all()


@router.post("/recompute")
def recompute_hotspots(db: Session = Depends(get_db)):
    """
    Recompute hotspots from historical alerts using DBSCAN clustering.
    Called on demand (or via a cron job).
    """
    from sklearn.cluster import DBSCAN
    import numpy as np

    # Fetch all alert coordinates via camera locations
    rows = (
        db.query(Camera.latitude, Camera.longitude, Alert.alert_type)
        .join(Alert, Camera.id == Alert.camera_id)
        .filter(Camera.latitude.isnot(None))
        .all()
    )

    if len(rows) < 3:
        return {"message": "Not enough data to compute hotspots", "clusters": 0}

    coords = np.array([[r.latitude, r.longitude] for r in rows])
    # DBSCAN: eps=0.001 ≈ ~100m radius; min_samples=3 events
    labels = DBSCAN(eps=0.001, min_samples=3).fit_predict(coords)

    # Clear old hotspots
    db.query(Hotspot).delete()

    unique_labels = set(labels) - {-1}
    for label in unique_labels:
        mask = labels == label
        cluster_coords = coords[mask]
        centre_lat = float(cluster_coords[:, 0].mean())
        centre_lon = float(cluster_coords[:, 1].mean())
        count = int(mask.sum())
        risk_score = round(count / len(rows), 4)

        db.add(Hotspot(
            latitude=centre_lat,
            longitude=centre_lon,
            risk_score=risk_score,
            alert_count=count,
        ))

    db.commit()
    logger.info(f"Hotspot recompute: {len(unique_labels)} clusters found")
    return {"clusters": len(unique_labels)}
