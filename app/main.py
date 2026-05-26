"""
Scenic Guide AI Digital Human - Backend
FastAPI application entry point
"""
import os
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.config import settings
from app.database import init_db
from app.api import chat, knowledge, avatar, speech, analytics

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown"""
    logger.info("Starting Scenic Guide Backend...")
    await init_db()
    logger.info("Database initialized")
    os.makedirs("./data/audio", exist_ok=True)
    yield
    logger.info("Shutting down...")


app = FastAPI(
    title="景区导览AI数字人 - 后端服务",
    description="基于FastAPI + DeepSeek + RAG的智能景区导览后端系统",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS - allow frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Production should restrict origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static files for audio output
app.mount("/audio", StaticFiles(directory="./data/audio"), name="audio")

# Register API routers
app.include_router(chat.router)
app.include_router(knowledge.router)
app.include_router(avatar.router)
app.include_router(speech.router)
app.include_router(analytics.router)


@app.get("/")
async def root():
    return {
        "service": "景区导览AI数字人",
        "version": "1.0.0",
        "docs": "/docs",
    }


@app.get("/health")
async def health():
    return {"status": "ok"}
