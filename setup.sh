#!/usr/bin/env bash
set -e

echo "=========================================================="
echo " Adverse Media Screening Copilot — Setup Script"
echo "=========================================================="
echo ""

# 1. Backend Setup
echo "[1/3] Setting up Python backend..."
cd backend
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip

# Note: The requirements.txt assumes a standard torch install,
# but for AMD ROCm we specifically want the ROCm wheel:
echo "Installing PyTorch for ROCm 6.2..."
pip install --pre torch torchvision torchaudio --index-url https://download.pytorch.org/whl/nightly/rocm6.2

echo "Installing backend dependencies..."
pip install -r requirements.txt

# Generate the synthetic dataset
echo "Generating synthetic dataset..."
python -m app.data.generate_dataset

deactivate
cd ..

# 2. Frontend Setup
echo "[2/3] Setting up React frontend..."
cd frontend
npm install
cd ..

echo "[3/3] Setup complete!"
echo ""
echo "To run the application:"
echo "Terminal 1 (Backend):  cd backend && source venv/bin/activate && uvicorn app.main:app --reload --host 0.0.0.0 --port 8000"
echo "Terminal 2 (Frontend): cd frontend && npm run dev"
echo ""
echo "The UI will be available at http://localhost:8501"
echo "=========================================================="
