#!/bin/bash
set -e

echo "============================================"
echo "  景区导览后端 - 一键初始化脚本"
echo "============================================"
echo ""

# 1. Create venv
if [ ! -d "venv" ]; then
    echo "[1/4] Creating virtual environment..."
    python3 -m venv venv
else
    echo "[1/4] Virtual environment already exists"
fi

# 2. Install dependencies
echo "[2/4] Installing dependencies..."
source venv/bin/activate
pip install -r requirements.txt -q

# 3. Download embedding model (if missing)
if [ ! -f "data/embedding_model/model.safetensors" ]; then
    echo "[3/4] Downloading embedding model (391MB)..."
    mkdir -p data/embedding_model
    echo "Downloading from HuggingFace..."
    echo "If download fails, try: https://hf-mirror.com/shibing624/text2vec-base-chinese/resolve/main/model.safetensors"
    curl -L -o data/embedding_model/model.safetensors https://huggingface.co/shibing624/text2vec-base-chinese/resolve/main/model.safetensors || {
        echo ""
        echo "[WARNING] Download failed! Trying mirror..."
        curl -L -o data/embedding_model/model.safetensors https://hf-mirror.com/shibing624/text2vec-base-chinese/resolve/main/model.safetensors || {
            echo ""
            echo "[ERROR] Both downloads failed. Please manually download:"
            echo "  URL: https://huggingface.co/shibing624/text2vec-base-chinese/resolve/main/model.safetensors"
            echo "  Save to: data/embedding_model/model.safetensors"
            exit 1
        }
    }
else
    echo "[3/4] Embedding model already exists"
fi

# 4. Init data
echo "[4/4] Initializing database..."
python init_data.py

echo ""
echo "============================================"
echo "  Setup complete!"
echo "  Run: ./start.sh"
echo "  Then visit: http://localhost:8000/docs"
echo "============================================"
