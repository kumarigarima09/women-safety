-- backend/database/schema.sql
-- Run: psql sih1605 -f backend/database/schema.sql

CREATE EXTENSION IF NOT EXISTS postgis;

-- ── Camera registry ──────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS cameras (
    id            TEXT PRIMARY KEY,
    name          TEXT NOT NULL,
    stream_url    TEXT NOT NULL,
    latitude      DOUBLE PRECISION,
    longitude     DOUBLE PRECISION,
    is_isolated   BOOLEAN DEFAULT FALSE,
    active        BOOLEAN DEFAULT TRUE,
    created_at    TIMESTAMPTZ DEFAULT NOW()
);

-- ── Alert log ─────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS alerts (
    id            SERIAL PRIMARY KEY,
    camera_id     TEXT REFERENCES cameras(id) ON DELETE SET NULL,
    alert_type    TEXT NOT NULL,       -- 'LONE_WOMAN' | 'SOS_GESTURE' | 'WEAPON'
    severity      TEXT NOT NULL,       -- 'HIGH' | 'MEDIUM'
    details       JSONB,
    location      GEOGRAPHY(POINT, 4326),
    reviewed      BOOLEAN DEFAULT FALSE,
    created_at    TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_alerts_created ON alerts (created_at DESC);
CREATE INDEX IF NOT EXISTS idx_alerts_type    ON alerts (alert_type);
CREATE INDEX IF NOT EXISTS idx_alerts_camera  ON alerts (camera_id);

-- ── Hotspot aggregation (materialised view refreshed by cron) ─────────────────
CREATE TABLE IF NOT EXISTS hotspots (
    id            SERIAL PRIMARY KEY,
    latitude      DOUBLE PRECISION NOT NULL,
    longitude     DOUBLE PRECISION NOT NULL,
    risk_score    FLOAT NOT NULL,
    alert_count   INT NOT NULL,
    last_seen     TIMESTAMPTZ,
    location      GEOGRAPHY(POINT, 4326)
);

-- ── Seed default cameras (update stream_url for real CCTV or Mac webcam) ──────
INSERT INTO cameras (id, name, stream_url, latitude, longitude, is_isolated)
VALUES
  ('cam-01', 'Main Gate',        '0',               28.6139, 77.2090, FALSE),
  ('cam-02', 'Parking Lot',      'rtsp://localhost', 28.6140, 77.2091, TRUE),
  ('cam-03', 'Back Alley',       'rtsp://localhost', 28.6138, 77.2089, TRUE)
ON CONFLICT (id) DO NOTHING;
