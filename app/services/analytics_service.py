"""
Analytics Service - Dashboard stats, sentiment analysis, reports
"""
import logging
from datetime import datetime, timedelta
from typing import Optional
from collections import Counter

from sqlalchemy import select, func, desc, and_, distinct
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import ChatRecord, VisitorFeedback, DailyStatistics
from app.services.llm_service import llm_service

logger = logging.getLogger(__name__)


class AnalyticsService:
    async def record_chat(
        self,
        db: AsyncSession,
        session_id: str,
        user_message: str,
        bot_reply: str,
        input_type: str = "text",
        reply_source: str = "rag",
        response_time: float = 0.0,
    ):
        """Record a chat interaction"""
        record = ChatRecord(
            session_id=session_id,
            user_message=user_message,
            bot_reply=bot_reply,
            input_type=input_type,
            reply_source=reply_source,
            response_time=response_time,
        )
        db.add(record)
        await db.commit()

    async def record_feedback(
        self,
        db: AsyncSession,
        session_id: str,
        rating: Optional[int] = None,
        feedback_text: Optional[str] = None,
    ) -> VisitorFeedback:
        """Record visitor feedback with sentiment analysis"""
        sentiment = "neutral"
        if feedback_text:
            sentiment = await llm_service.analyze_sentiment(feedback_text)

        feedback = VisitorFeedback(
            session_id=session_id,
            rating=rating,
            feedback_text=feedback_text,
            sentiment=sentiment,
        )
        db.add(feedback)
        await db.commit()
        await db.refresh(feedback)
        return feedback

    async def get_dashboard_stats(self, db: AsyncSession) -> dict:
        """Get dashboard statistics"""
        today = datetime.now().strftime("%Y-%m-%d")
        week_ago = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")

        # Today stats
        today_chats = await db.scalar(
            select(func.count(ChatRecord.id)).where(
                func.strftime("%Y-%m-%d", ChatRecord.created_at) == today
            )
        ) or 0

        today_users = await db.scalar(
            select(func.count(distinct(ChatRecord.session_id))).where(
                func.strftime("%Y-%m-%d", ChatRecord.created_at) == today
            )
        ) or 0

        # Week stats
        week_chats = await db.scalar(
            select(func.count(ChatRecord.id)).where(
                func.strftime("%Y-%m-%d", ChatRecord.created_at) >= week_ago
            )
        ) or 0

        week_users = await db.scalar(
            select(func.count(distinct(ChatRecord.session_id))).where(
                func.strftime("%Y-%m-%d", ChatRecord.created_at) >= week_ago
            )
        ) or 0

        # Average rating
        avg_rating = await db.scalar(
            select(func.avg(VisitorFeedback.rating)).where(
                VisitorFeedback.rating.isnot(None)
            )
        ) or 0.0

        # Positive rate
        total_feedbacks = await db.scalar(
            select(func.count(VisitorFeedback.id))
        ) or 1
        positive_count = await db.scalar(
            select(func.count(VisitorFeedback.id)).where(
                VisitorFeedback.sentiment == "positive"
            )
        ) or 0
        positive_rate = round(positive_count / total_feedbacks * 100, 1) if total_feedbacks > 0 else 0.0

        # Top questions (last 7 days)
        top_q_rows = await db.execute(
            select(ChatRecord.user_message, func.count(ChatRecord.id).label("cnt"))
            .where(func.strftime("%Y-%m-%d", ChatRecord.created_at) >= week_ago)
            .group_by(ChatRecord.user_message)
            .order_by(desc("cnt"))
            .limit(10)
        )
        top_questions = [
            {"question": row[0], "count": row[1]}
            for row in top_q_rows
        ]

        # Satisfaction trend (last 7 days)
        satisfaction_trend = []
        for i in range(6, -1, -1):
            date = (datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d")
            day_avg = await db.scalar(
                select(func.avg(VisitorFeedback.rating)).where(
                    and_(
                        func.strftime("%Y-%m-%d", VisitorFeedback.created_at) == date,
                        VisitorFeedback.rating.isnot(None),
                    )
                )
            ) or 0.0
            satisfaction_trend.append({"date": date, "avg_rating": round(float(day_avg), 1)})

        # Daily chat trend (last 7 days)
        daily_chat_trend = []
        for i in range(6, -1, -1):
            date = (datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d")
            day_count = await db.scalar(
                select(func.count(ChatRecord.id)).where(
                    func.strftime("%Y-%m-%d", ChatRecord.created_at) == date
                )
            ) or 0
            daily_chat_trend.append({"date": date, "count": day_count})

        return {
            "today_chats": today_chats,
            "today_users": today_users,
            "week_chats": week_chats,
            "week_users": week_users,
            "avg_rating": round(float(avg_rating), 1),
            "positive_rate": positive_rate,
            "top_questions": top_questions,
            "satisfaction_trend": satisfaction_trend,
            "daily_chat_trend": daily_chat_trend,
        }

    async def get_sentiment_report(self, db: AsyncSession, days: int = 7) -> dict:
        """Get sentiment analysis report for the past N days"""
        since = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")

        feedbacks = await db.execute(
            select(VisitorFeedback).where(
                func.strftime("%Y-%m-%d", VisitorFeedback.created_at) >= since
            ).order_by(VisitorFeedback.created_at.desc())
        )
        feedback_list = feedbacks.scalars().all()

        sentiment_counts = Counter(f.sentiment for f in feedback_list)
        total = len(feedback_list)

        return {
            "total_feedbacks": total,
            "positive": sentiment_counts.get("positive", 0),
            "neutral": sentiment_counts.get("neutral", 0),
            "negative": sentiment_counts.get("negative", 0),
            "positive_rate": round(sentiment_counts.get("positive", 0) / total * 100, 1) if total > 0 else 0.0,
            "recent_feedbacks": [
                {
                    "id": f.id,
                    "rating": f.rating,
                    "text": f.feedback_text,
                    "sentiment": f.sentiment,
                    "created_at": f.created_at.isoformat() if f.created_at else None,
                }
                for f in feedback_list[:20]
            ],
        }


analytics_service = AnalyticsService()
