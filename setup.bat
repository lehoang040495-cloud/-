@echo off
chcp 65001 >nul
echo ============================================
echo   景区导览后端 - 一键初始化脚本
echo ============================================
echo.

:: 1. Create venv
if not exist venv (
    echo [1/4] Creating virtual environment...
    python -m venv venv
) else (
    echo [1/4] Virtual environment already exists
)

:: 2. Install dependencies
echo [2/4] Installing dependencies...
call venv\Scripts\activate.bat
pip install -r requirements.txt -q

:: 3. Download embedding model (if missing)
if not exist data\embedding_model\model.safetensors (
    echo [3/4] Downloading embedding model (391MB)...
    if not exist data\embedding_model mkdir data\embedding_model
    echo Downloading from HuggingFace...
    echo If download fails, please manually download from:
    echo https://huggingface.co/shibing624/text2vec-base-chinese/resolve/main/model.safetensors
    echo Save to: data\embedding_model\model.safetensors
    echo.
    curl -L -o data\embedding_model\model.safetensors https://huggingface.co/shibing624/text2vec-base-chinese/resolve/main/model.safetensors
    if errorlevel 1 (
        echo.
        echo [WARNING] Download failed! Please download manually:
        echo   URL: https://huggingface.co/shibing624/text2vec-base-chinese/resolve/main/model.safetensors
        echo   Save to: data\embedding_model\model.safetensors
        echo.
        echo Or try the mirror:
        echo   curl -L -o data\embedding_model\model.safetensors https://hf-mirror.com/shibing624/text2vec-base-chinese/resolve/main/model.safetensors
        pause
        exit /b 1
    )
) else (
    echo [3/4] Embedding model already exists
)

:: 4. Init data
echo [4/4] Initializing database...
python init_data.py

echo.
echo ============================================
echo   Setup complete!
echo   Run: start.bat
echo   Then visit: http://localhost:8000/docs
echo ============================================
pause
