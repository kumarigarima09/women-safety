#!/usr/bin/env bash
# =============================================================================
# setup_mac.sh — One-shot environment setup for SIH1605 on macOS
# Run: chmod +x setup_mac.sh && ./setup_mac.sh
# =============================================================================
set -e

echo "======================================"
echo "  SIH1605 Women Safety Analytics"
echo "  macOS Environment Setup Script"
echo "======================================"

# --- 1. Check for Homebrew ---
if ! command -v brew &>/dev/null; then
  echo "[+] Installing Homebrew..."
  /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
else
  echo "[✓] Homebrew found"
fi

# --- 2. System dependencies ---
echo "[+] Installing system dependencies via Homebrew..."
brew install ffmpeg postgresql@16 python@3.11 || true

# --- 3. Start PostgreSQL ---
echo "[+] Starting PostgreSQL service..."
brew services start postgresql@16

# --- 4. Create virtual environment ---
echo "[+] Creating Python virtual environment..."
python3.11 -m venv myenv
source myenv/bin/activate

# --- 5. Upgrade pip and install requirements ---
echo "[+] Installing Python packages..."
pip install --upgrade pip
pip install -r requirements.txt

# --- 6. Detect Apple Silicon & verify MPS (Metal) GPU support ---
echo ""
echo "[+] Verifying PyTorch hardware acceleration..."
python3 - <<'EOF'
import torch
print(f"  PyTorch version : {torch.__version__}")
if torch.backends.mps.is_available():
    print("  MPS (Apple Silicon GPU) : AVAILABLE ✓")
elif torch.cuda.is_available():
    print(f"  CUDA : AVAILABLE ✓ ({torch.cuda.get_device_name(0)})")
else:
    print("  Hardware acceleration : Not available, will use CPU")
EOF

# --- 7. Setup PostgreSQL database ---
echo ""
echo "[+] Setting up PostgreSQL database..."
createdb sih1605 2>/dev/null || echo "  Database 'sih1605' already exists, skipping."


# --- 8. Run DB schema ---
echo "[+] Applying database schema..."
psql sih1605 -f backend/database/schema.sql

# --- 9. Frontend setup ---
echo "[+] Setting up frontend..."
cd frontend && npm install && cd ..

echo ""
echo "======================================"
echo "  Setup Complete!"
echo "  Activate your env: source myenv/bin/activate"
echo "  Start backend:     uvicorn backend.main:app --reload --port 8000"
echo "  Start frontend:    cd frontend && npm run dev"
echo "======================================"
