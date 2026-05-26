import os
from pydantic_settings import BaseSettings
from pathlib import Path


class Settings(BaseSettings):
    # LLM Provider: deepseek / doubao
    LLM_PROVIDER: str = "doubao"

    # DeepSeek API
    DEEPSEEK_API_KEY: str = "your_api_key_here"
    DEEPSEEK_BASE_URL: str = "https://api.deepseek.com"
    DEEPSEEK_MODEL: str = "deepseek-chat"

    # Doubao Proxy
    DOUBAO_ENDPOINT: str = "https://fosp-gateway.vemic.com/ai_proxy/v2/volces/chat/completions"
    DOUBAO_MODEL: str = "doubao-seed-2-0-pro-260215"
    DOUBAO_OPEN_ID: str = ""
    DOUBAO_DEVELOPER_SECRET: str = ""

    # Database
    DATABASE_URL: str = "sqlite+aiosqlite:///./data/scenic_guide.db"

    # Server
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    # RAG
    EMBEDDING_MODEL: str = "shibing624/text2vec-base-chinese"
    VECTOR_STORE_PATH: str = "./data/vectors"
    KNOWLEDGE_PATH: str = "./data/knowledge"
    CHUNK_SIZE: int = 500
    CHUNK_OVERLAP: int = 50

    # TTS
    TTS_VOICE: str = "zh-CN-XiaoxiaoNeural"
    TTS_RATE: str = "+0%"

    # STT
    WHISPER_MODEL: str = "base"
    WHISPER_DEVICE: str = "cpu"

    # Weather
    WEATHER_LATITUDE: float = 30.57
    WEATHER_LONGITUDE: float = 104.07
    WEATHER_LOCATION_NAME: str = "景区"

    # Admin
    ADMIN_USERNAME: str = "admin"
    ADMIN_PASSWORD: str = "admin123"

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
    }


settings = Settings()

# Ensure data directories exist
for d in [settings.VECTOR_STORE_PATH, settings.KNOWLEDGE_PATH, "./data/audio"]:
    Path(d).mkdir(parents=True, exist_ok=True)
