from pydantic import BaseModel
from typing import Optional
from datetime import datetime


# === Chat ===
class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = "default"
    input_type: Optional[str] = "text"  # text, voice

class ChatResponse(BaseModel):
    reply: str
    session_id: str
    source: str = "rag"  # rag, llm
    response_time: float = 0.0


# === Knowledge ===
class KnowledgeCreate(BaseModel):
    title: str
    category: Optional[str] = "通用"

class KnowledgeResponse(BaseModel):
    id: int
    title: str
    file_name: str
    file_type: str
    category: str
    chunk_count: int
    status: str
    created_at: datetime

    class Config:
        from_attributes = True

class KnowledgeUpdate(BaseModel):
    title: Optional[str] = None
    category: Optional[str] = None
    status: Optional[str] = None


# === Avatar ===
class AvatarCreate(BaseModel):
    name: str
    model_url: str
    voice_name: Optional[str] = "zh-CN-XiaoxiaoNeural"
    voice_rate: Optional[str] = "+0%"
    greeting: Optional[str] = "您好！我是您的智能导游小景，很高兴为您服务！"
    outfit: Optional[str] = "default"

class AvatarResponse(BaseModel):
    id: int
    name: str
    model_url: str
    voice_name: str
    voice_rate: str
    greeting: str
    outfit: str
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True

class AvatarUpdate(BaseModel):
    name: Optional[str] = None
    model_url: Optional[str] = None
    voice_name: Optional[str] = None
    voice_rate: Optional[str] = None
    greeting: Optional[str] = None
    outfit: Optional[str] = None
    is_active: Optional[bool] = None


# === Speech ===
class TTSRequest(BaseModel):
    text: str
    voice: Optional[str] = None
    rate: Optional[str] = None

class STTResponse(BaseModel):
    text: str
    confidence: float = 0.0


# === Analytics ===
class DashboardStats(BaseModel):
    today_chats: int
    today_users: int
    week_chats: int
    week_users: int
    avg_rating: float
    positive_rate: float
    top_questions: list
    satisfaction_trend: list
    daily_chat_trend: list

class FeedbackCreate(BaseModel):
    session_id: str
    rating: Optional[int] = None
    feedback_text: Optional[str] = None

class FeedbackResponse(BaseModel):
    id: int
    session_id: str
    rating: Optional[int]
    feedback_text: Optional[str]
    sentiment: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


# === Route ===
class RouteCreate(BaseModel):
    name: str
    description: Optional[str] = None
    interest_tag: Optional[str] = None
    spots: Optional[list] = None
    duration: Optional[str] = None
    difficulty: Optional[str] = "easy"

class RouteResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]
    interest_tag: Optional[str]
    spots: Optional[list]
    duration: Optional[str]
    difficulty: str
    created_at: datetime

    class Config:
        from_attributes = True


# === Generic ===
class MessageResponse(BaseModel):
    message: str
    success: bool = True
