"""
backend/database/models.py
───────────────────────────
SQLAlchemy ORM models for cameras, alerts, and hotspots.
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, Float, JSON, DateTime, ForeignKey
from .connection import Base


class Camera(Base):
    __tablename__ = "cameras"

    id           = Column(String, primary_key=True)
    name         = Column(String, nullable=False)
    stream_url   = Column(String, nullable=False)
    latitude     = Column(Float)
    longitude    = Column(Float)
    is_isolated  = Column(Boolean, default=False)
    active       = Column(Boolean, default=True)
    created_at   = Column(DateTime, default=datetime.utcnow)


class Alert(Base):
    __tablename__ = "alerts"

    id          = Column(Integer, primary_key=True, autoincrement=True)
    camera_id   = Column(String, ForeignKey("cameras.id", ondelete="SET NULL"))
    alert_type  = Column(String, nullable=False)   # LONE_WOMAN | SOS_GESTURE | WEAPON
    severity    = Column(String, nullable=False)   # HIGH | MEDIUM
    details     = Column(JSON)
    reviewed    = Column(Boolean, default=False)
    created_at  = Column(DateTime, default=datetime.utcnow)


class Hotspot(Base):
    __tablename__ = "hotspots"

    id          = Column(Integer, primary_key=True, autoincrement=True)
    latitude    = Column(Float, nullable=False)
    longitude   = Column(Float, nullable=False)
    risk_score  = Column(Float, nullable=False)
    alert_count = Column(Integer, nullable=False)
    last_seen   = Column(DateTime, default=datetime.utcnow)
