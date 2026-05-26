"""
Chat API - Core conversational endpoint
"""
import time
import logging
from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import AvatarConfig
from app.schemas import ChatRequest, ChatResponse
from app.services.llm_service import llm_service
from app.services.rag_service import rag_service
from app.services.analytics_service import analytics_service

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api", tags=["Chat"])


async def _get_current_mode(db: AsyncSession) -> str:
    """Get mode from active avatar config"""
    result = await db.execute(
        select(AvatarConfig).where(AvatarConfig.is_active == True)
    )
    avatar = result.scalar_one_or_none()
    if avatar and hasattr(avatar, "mode"):
        return avatar.mode or "normal"
    return "normal"


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest, db: AsyncSession = Depends(get_db)):
    """Main chat endpoint - RAG augmented Q&A with mode support"""
    start_time = time.time()

    mode = await _get_current_mode(db)

    # 1. Retrieve relevant context from knowledge base
    context = await rag_service.get_context(request.message, top_k=5)

    # 2. Generate reply using LLM with RAG context
    if context:
        reply = await llm_service.chat(request.message, context=context, mode=mode)
        source = "rag"
    else:
        reply = await llm_service.chat(request.message, mode=mode)
        source = "llm"

    response_time = time.time() - start_time

    # 3. Record the interaction
    await analytics_service.record_chat(
        db=db,
        session_id=request.session_id,
        user_message=request.message,
        bot_reply=reply,
        input_type=request.input_type,
        reply_source=source,
        response_time=round(response_time, 3),
    )

    return ChatResponse(
        reply=reply,
        session_id=request.session_id,
        source=source,
        response_time=round(response_time, 3),
    )


@router.post("/chat/route")
async def recommend_route(
    interest: str,
    session_id: str = "default",
    db: AsyncSession = Depends(get_db),
):
    """Get personalized route recommendation based on interest"""
    start_time = time.time()

    context = await rag_service.get_context(f"{interest} 路线推荐", top_k=5)
    reply = await llm_service.recommend_route(interest, context)

    response_time = time.time() - start_time

    await analytics_service.record_chat(
        db=db,
        session_id=session_id,
        user_message=f"[路线推荐] 兴趣：{interest}",
        bot_reply=reply,
        reply_source="rag",
        response_time=round(response_time, 3),
    )

    return {"reply": reply, "interest": interest, "response_time": round(response_time, 3)}
