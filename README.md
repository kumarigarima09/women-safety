# 🛡️ SIH1605 – Women Safety Analytics

> **Smart India Hackathon 2024 | Problem Statement SIH1605**  
> Issued by: **Bharat Electronics Limited (BEL)**  
> Category: Miscellaneous / Smart Automation Software

A real-time, AI-powered CCTV surveillance system that proactively detects threats to women's safety. The system processes live video feeds from cameras, runs multiple computer vision models, and instantly alerts law enforcement via a web dashboard — shifting surveillance from **reactive recording** to **proactive threat detection**.

---

## ✨ Features

| Module | Description |
|---|---|
| 👤 **Gender Detection** | YOLOv8 person detection + MobileNetV3 gender classification |
| 🚨 **Lone Woman Alert** | Detects isolated women in high-risk zones or night hours |
| 🆘 **SOS Gesture Recognition** | MediaPipe Pose detects raised arms, waves, defensive posture |
| 🔪 **Weapon Detection** | YOLOv8 detects knives, guns, and other threats |
| 🗺️ **Hotspot Mapping** | DBSCAN clustering maps high-risk zones on a live map |
| 🔒 **Privacy Blur** | Non-threat bystanders' faces are automatically blurred |
| 📡 **Live Dashboard** | React web dashboard with real-time WebSocket streaming |

---

## 🗂️ Project Structure

```
sih1605-women-safety/
├── ai_engine/                    # Core AI/CV modules
│   ├── video_reader.py           # Thread-safe RTSP/webcam reader
│   ├── gender_classifier.py      # YOLOv8 + MobileNetV3 gender detector
│   ├── lone_woman_detector.py    # Isolation + risk-time logic
│   ├── sos_gesture.py            # MediaPipe Pose SOS recognition
│   ├── weapon_detector.py        # YOLOv8 weapon detection
│   └── pipeline.py               # Master pipeline orchestrator
├── backend/                      # FastAPI backend
│   ├── main.py                   # App entry point
│   ├── routes/
│   │   ├── stream.py             # WebSocket live stream endpoint
│   │   ├── alerts.py             # REST: alert history CRUD
│   │   └── hotspots.py           # REST: hotspot data + recompute
│   └── database/
│       ├── connection.py         # SQLAlchemy + .env config
│       ├── models.py             # ORM models (Camera, Alert, Hotspot)
│       └── schema.sql            # PostgreSQL + PostGIS schema
├── frontend/                     # React + Vite dashboard
│   └── src/components/
│       ├── LiveFeed.jsx           # Multi-camera video grid
│       ├── AlertPanel.jsx         # Real-time alert notifications
│       └── HotspotMap.jsx         # Leaflet geospatial hotspot map
├── tests/                        # Pytest unit tests
│   ├── test_lone_woman.py
│   └── test_sos_gesture.py
├── data/
│   └── models/                   # Place trained .pth model files here
├── scripts/                      # Training/utility scripts
├── pitorch.py                    # Hardware (MPS/CUDA) verification
├── requirements.txt
├── setup_mac.sh                  # One-shot macOS setup script
└── .gitignore
```

---

## 🚀 Quick Start (macOS)

### Prerequisites
- macOS 12+ (Apple Silicon M1/M2/M3 **recommended** for MPS acceleration)
- Python 3.11
- [Homebrew](https://brew.sh)
- Node.js 20+

### 1. Clone the repository
```bash
git clone https://github.com/YOUR_USERNAME/sih1605-women-safety.git
cd sih1605-women-safety
```

### 2. Run the one-shot setup script
```bash
chmod +x setup_mac.sh
./setup_mac.sh
```
This will:
- Install `ffmpeg`, `postgresql`, and `postgis` via Homebrew
- Create a Python virtualenv and install all dependencies
- Verify PyTorch MPS (Apple GPU) support
- Create and seed the `sih1605` PostgreSQL database

### 3. Verify GPU support
```bash
source myenv/bin/activate
python pitorch.py
```
Expected output on Apple Silicon:
```
MPS (Apple Silicon GPU) : AVAILABLE ✓
```

### 4. Start the backend
```bash
source myenv/bin/activate
uvicorn backend.main:app --reload --port 8000
```

### 5. Start the frontend dashboard
```bash
cd frontend
npm install
npm run dev
# Opens at http://localhost:5173
```

---

## ⚙️ Configuration

Create a `.env` file in the project root (copy from `.env.example`):

```env
DATABASE_URL=postgresql://localhost/sih1605
```

---

## 🎥 Camera Configuration

The system supports multiple camera sources configured via the database:

| Source | `stream_url` value |
|---|---|
| Mac built-in webcam | `"0"` |
| IP Camera (RTSP) | `"rtsp://user:pass@192.168.1.100:554/stream"` |
| Local video file | `"path/to/video.mp4"` |

---

## 🧪 Running Tests

```bash
source myenv/bin/activate
pytest tests/ -v
```

---

## 🏗️ Architecture Diagram

```
CCTV / Webcam Feed
        │
        ▼
  VideoReader (OpenCV)
        │
        ▼
  ┌─────────────────────────────┐
  │       AI Pipeline           │
  │  ┌──────────────────────┐   │
  │  │  Gender Detector     │   │
  │  │  (YOLOv8 + MobileNet)│   │
  │  └──────────┬───────────┘   │
  │             │               │
  │  ┌──────────▼───────────┐   │
  │  │  Lone Woman Detector │   │
  │  │  (Distance + Time)   │   │
  │  └──────────────────────┘   │
  │  ┌──────────────────────┐   │
  │  │  SOS Gesture Detect  │   │
  │  │  (MediaPipe Pose)    │   │
  │  └──────────────────────┘   │
  │  ┌──────────────────────┐   │
  │  │  Weapon Detector     │   │
  │  │  (YOLOv8)            │   │
  │  └──────────────────────┘   │
  └─────────────┬───────────────┘
                │  AlertFrame
                ▼
      FastAPI Backend (port 8000)
      ├── WebSocket /ws/stream/{cam}
      ├── REST /api/alerts
      └── REST /api/hotspots
                │
                ▼
   React Dashboard (port 5173)
   ├── Live Feed Grid
   ├── Alert Panel (WebSocket)
   └── Hotspot Map (Leaflet)
```

---

## 🔒 Privacy & Compliance

- Faces of **non-threatening individuals** are automatically blurred via Gaussian blur before streaming
- Only **active threat subjects** remain un-blurred for law enforcement review
- No personal data is permanently stored; only alert metadata and coordinates

---

## 🛠️ Suggested Improvements

- [ ] Fine-tune gender model on Indian demographics dataset
- [ ] Add thermal/IR camera support for low-light environments (Zero-DCE)
- [ ] Implement stalking detection (group following a lone individual)
- [ ] Add SMS alerting via Twilio for offline notification
- [ ] Dockerise the entire stack for deployment independence
- [ ] Add TensorRT optimisation for NVIDIA Jetson edge deployment

---

## 📄 License

This project was developed for SIH 2024 (Non-commercial, academic use).

---

## 🤝 Team

Developed for **Smart India Hackathon 2024** — Problem Statement SIH1605  
Issued by **Bharat Electronics Limited (BEL)**
