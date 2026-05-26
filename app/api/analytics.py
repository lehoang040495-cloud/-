"""
Analytics API - Dashboard, feedback, and reports
"""
import logging
from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, func, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import ChatRecord, VisitorFeedback
from app.schemas import (
    FeedbackCreate, FeedbackResponse, DashboardStats, MessageResponse,
)
from app.services.analytics_service import analytics_service

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/analytics", tags=["Analytics"])


@router.get("/dashboard")
async def get_dashboard(db: AsyncSession = Depends(get_db)):
    """Get dashboard overview statistics"""
    stats = await analytics_service.get_dashboard_stats(db)
    return stats


@router.post("/feedback", response_model=FeedbackResponse)
async def submit_feedback(data: FeedbackCreate, db: AsyncSession = Depends(get_db)):
    """Submit visitor feedback"""
    feedback = await analytics_service.record_feedback(
        db=db,
        session_id=data.session_id,
        rating=data.rating,
        feedback_text=data.feedback_text,
    )
    return feedback


@router.get("/feedback")
async def list_feedback(
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    """List recent feedback"""
    result = await db.execute(
        select(VisitorFeedback)
        .order_by(VisitorFeedback.created_at.desc())
        .limit(limit)
    )
    return result.scalars().all()


@router.get("/sentiment-report")
async def sentiment_report(days: int = Query(7, ge=1, le=30), db: AsyncSession = Depends(get_db)):
    """Get sentiment analysis report"""
    return await analytics_service.get_sentiment_report(db, days)


@router.get("/chat-history")
async def chat_history(
    session_id: str = None,
    limit: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
):
    """Get chat history"""
    query = select(ChatRecord).order_by(ChatRecord.created_at.desc())
    if session_id:
        query = query.where(ChatRecord.session_id == session_id)
    query = query.limit(limit)

    result = await db.execute(query)
    records = result.scalars().all()

    return [
        {
            "id": r.id,
            "session_id": r.session_id,
            "user_message": r.user_message,
            "bot_reply": r.bot_reply,
            "input_type": r.input_type,
            "response_time": r.response_time,
            "created_at": r.created_at.isoformat() if r.created_at else None,
        }
        for r in records
    ]


@router.get("/hot-topics")
async def hot_topics(days: int = Query(7, ge=1, le=30), db: AsyncSession = Depends(get_db)):
    """Get trending topics/questions"""
    from datetime import datetime, timedelta
    since = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")

    result = await db.execute(
        select(ChatRecord.user_message, func.count(ChatRecord.id).label("count"))
        .where(func.strftime("%Y-%m-%d", ChatRecord.created_at) >= since)
        .group_by(ChatRecord.user_message)
        .order_by(desc("count"))
        .limit(20)
    )

    return {
        "topics": [
            {"question": row[0], "count": row[1]}
            for row in result
        ]
    }
