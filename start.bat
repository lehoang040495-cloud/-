@echo off
chcp 65001 >nul
echo ==========================================
echo   景区导览AI数字人 - 启动后端服务
echo ==========================================
echo.

REM Check .env file
if not exist .env (
    echo [WARN] .env file not found, copying from .env.example
    copy .env.example .env
    echo [INFO] Please edit .env with your API key before starting
    echo.
)

REM Check virtual environment
if not exist venv (
    echo [INFO] Creating virtual environment...
    python -m venv venv
    call venv\Scripts\activate.bat
    echo [INFO] Installing dependencies...
    pip install -r requirements.txt
) else (
    call venv\Scripts\activate.bat
)

echo.
echo [INFO] Starting server at http://localhost:8000
echo [INFO] API docs: http://localhost:8000/docs
echo.

uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
