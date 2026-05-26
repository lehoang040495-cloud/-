"""
Profile API - Visitor profile/portrait analysis
"""
import logging
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import ChatRecord, VisitorProfile
from app.schemas import VisitorProfileResponse
from app.services.llm_service import llm_service

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/analytics", tags=["Profile"])


@router.get("/profile/{session_id}", response_model=VisitorProfileResponse)
async def get_visitor_profile(session_id: str, db: AsyncSession = Depends(get_db)):
    """Get or generate visitor profile based on chat history"""
    # Check existing profile
    result = await db.execute(
        select(VisitorProfile).where(VisitorProfile.session_id == session_id)
    )
    profile = result.scalar_one_or_none()

    # Get chat history
    chat_result = await db.execute(
        select(ChatRecord.user_message)
        .where(ChatRecord.session_id == session_id)
        .order_by(ChatRecord.created_at)
    )
    chat_messages = [row[0] for row in chat_result.all()]

    if not chat_messages:
        return VisitorProfileResponse(
            session_id=session_id,
            interests=[],
            travel_style="general",
            preferred_duration=None,
            sentiment_summary="neutral",
            chat_count=0,
            profile_data={"summary": "新游客，暂无对话记录"},
        )

    # Always re-analyze if chat count changed or no profile exists
    if profile is None or profile.chat_count != len(chat_messages):
        analysis = await llm_service.analyze_visitor_profile(chat_messages)

        # Get overall sentiment
        sentiment = await llm_service.analyze_sentiment(chat_messages[-1])

        if profile is None:
            profile = VisitorProfile(
                session_id=session_id,
                interests=analysis.get("interests", []),
                travel_style=analysis.get("travel_style", "general"),
                preferred_duration=analysis.get("preferred_duration"),
                sentiment_summary=sentiment,
                chat_count=len(chat_messages),
                profile_data=analysis,
            )
            db.add(profile)
        else:
            profile.interests = analysis.get("interests", [])
            profile.travel_style = analysis.get("travel_style", "general")
            profile.preferred_duration = analysis.get("preferred_duration")
            profile.sentiment_summary = sentiment
            profile.chat_count = len(chat_messages)
            profile.profile_data = analysis

        await db.commit()
        await db.refresh(profile)

    return VisitorProfileResponse(
        session_id=profile.session_id,
        interests=profile.interests or [],
        travel_style=profile.travel_style or "general",
        preferred_duration=profile.preferred_duration,
        sentiment_summary=profile.sentiment_summary or "neutral",
        chat_count=profile.chat_count,
        profile_data=profile.profile_data,
    )


@router.get("/profiles")
async def list_profiles(db: AsyncSession = Depends(get_db)):
    """List all visitor profiles"""
    result = await db.execute(
        select(VisitorProfile).order_by(VisitorProfile.updated_at.desc()).limit(50)
    )
    profiles = result.scalars().all()
    return {
        "total": len(profiles),
        "profiles": [
            {
                "session_id": p.session_id,
                "interests": p.interests,
                "travel_style": p.travel_style,
                "chat_count": p.chat_count,
                "sentiment_summary": p.sentiment_summary,
                "updated_at": p.updated_at.isoformat() if p.updated_at else None,
            }
            for p in profiles
        ],
    }
