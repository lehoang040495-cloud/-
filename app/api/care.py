"""
Care API - Proactive emotion-based care messages
"""
import logging
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import CareMessage, ChatRecord
from app.schemas import CareMessageResponse
from app.services.llm_service import llm_service
from app.services.weather_service import weather_service

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/care", tags=["Care"])


@router.get("/messages/{session_id}", response_model=list[CareMessageResponse])
async def get_care_messages(session_id: str, db: AsyncSession = Depends(get_db)):
    """Get unread care messages for a visitor"""
    result = await db.execute(
        select(CareMessage)
        .where(CareMessage.session_id == session_id)
        .order_by(CareMessage.created_at.desc())
        .limit(20)
    )
    return result.scalars().all()


@router.post("/messages/{message_id}/read")
async def mark_message_read(message_id: int, db: AsyncSession = Depends(get_db)):
    """Mark a care message as read"""
    result = await db.execute(
        select(CareMessage).where(CareMessage.id == message_id)
    )
    msg = result.scalar_one_or_none()
    if not msg:
        raise HTTPException(status_code=404, detail="消息不存在")
    msg.is_read = True
    await db.commit()
    return {"message": "已标记为已读", "success": True}


@router.post("/generate/{session_id}")
async def generate_care_message(session_id: str, db: AsyncSession = Depends(get_db)):
    """Generate a proactive care message based on visitor's emotion and weather"""
    # Analyze recent sentiment from chat history
    result = await db.execute(
        select(ChatRecord.user_message)
        .where(ChatRecord.session_id == session_id)
        .order_by(ChatRecord.created_at.desc())
        .limit(5)
    )
    recent_messages = [row[0] for row in result.all()]

    sentiment = "neutral"
    if recent_messages:
        sentiment = await llm_service.analyze_sentiment("。".join(recent_messages))

    # Get weather info
    weather = await weather_service.get_weather()
    weather_info = f"{weather['description']}，{weather['temperature']}"

    # Generate care message
    care_text = await llm_service.generate_care_message(weather_info, sentiment)

    # Save to DB
    msg_type = "emotion"
    if sentiment == "negative":
        msg_type = "emotion"
    elif "雨" in weather_info or "雪" in weather_info:
        msg_type = "weather"
    else:
        msg_type = "reminder"

    msg = CareMessage(
        session_id=session_id,
        message_type=msg_type,
        content=care_text,
    )
    db.add(msg)
    await db.commit()
    await db.refresh(msg)

    return {
        "id": msg.id,
        "content": care_text,
        "message_type": msg_type,
        "sentiment_detected": sentiment,
        "success": True,
    }


@router.get("/check/{session_id}")
async def check_and_notify(session_id: str, db: AsyncSession = Depends(get_db)):
    """Check if visitor needs proactive care (based on chat pattern and time)"""
    result = await db.execute(
        select(CareMessage)
        .where(
            CareMessage.session_id == session_id,
            CareMessage.is_read == False,
        )
    )
    unread = result.scalars().all()

    return {
        "has_unread": len(unread) > 0,
        "unread_count": len(unread),
        "messages": [
            {
                "id": m.id,
                "type": m.message_type,
                "content": m.content,
                "created_at": m.created_at.isoformat(),
            }
            for m in unread
        ],
    }
