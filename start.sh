#!/bin/bash
echo "=========================================="
echo "  景区导览AI数字人 - 启动后端服务"
echo "=========================================="

# Check .env
if [ ! -f .env ]; then
    echo "[WARN] .env not found, copying from .env.example"
    cp .env.example .env
    echo "[INFO] Please edit .env with your API key"
fi

# Check venv
if [ ! -d "venv" ]; then
    echo "[INFO] Creating virtual environment..."
    python3 -m venv venv
    source venv/bin/activate
    echo "[INFO] Installing dependencies..."
    pip install -r requirements.txt
else
    source venv/bin/activate
fi

echo "[INFO] Starting server at http://localhost:8000"
echo "[INFO] API docs: http://localhost:8000/docs"

uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
