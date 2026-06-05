"""
Admin API - 管理端接口
提供知识库管理、数据大屏、情感趋势等管理端专用接口
"""
import uuid
import logging
from datetime import datetime, timedelta
from collections import Counter
from typing import Optional

from fastapi import APIRouter, Depends, Query, Header, HTTPException
from sqlalchemy import select, func, desc, distinct
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import (
    KnowledgeEntry, KnowledgeDocument, ChatRecord,
    VisitorFeedback, AvatarConfig, VisitorProfile,
)
from app.schemas import (
    AdminLoginRequest, AdminLoginResponse,
    KnowledgeEntryCreate, KnowledgeEntryUpdate,
    MessageResponse,
)
from app.config import settings
from app.services.analytics_service import analytics_service

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/admin", tags=["Admin"])

# ---- 简易 Token 存储（内存） ----
_active_tokens: dict[str, str] = {}  # token -> username


def _ok(data=None, message="success"):
    """统一响应格式"""
    return {"code": 0, "data": data, "message": message}


def _fail(message: str, code: int = -1):
    """统一错误响应"""
    return {"code": code, "data": None, "message": message}


async def _check_token(authorization: Optional[str] = Header(None)):
    """简易鉴权中间件"""
    if not authorization:
        raise HTTPException(401, "未登录")
    token = authorization.replace("Bearer ", "") if authorization.startswith("Bearer ") else authorization
    if token not in _active_tokens:
        raise HTTPException(401, "Token 无效，请重新登录")
    return token


# ============================================================
# 1. 认证模块
# ============================================================

@router.post("/login")
async def admin_login(data: AdminLoginRequest):
    """管理员登录"""
    if data.username != settings.ADMIN_USERNAME or data.password != settings.ADMIN_PASSWORD:
        return _fail("用户名或密码错误", code=1001)

    token = str(uuid.uuid4())
    _active_tokens[token] = data.username
    return _ok({"token": token, "username": data.username})


@router.post("/register")
async def admin_register(data: AdminLoginRequest):
    """管理员注册（预留）"""
    return _ok(message="注册功能暂未开放")


@router.post("/logout")
async def admin_logout(token: str = Depends(_check_token)):
    """管理员登出"""
    _active_tokens.pop(token, None)
    return _ok(message="已登出")


# ============================================================
# 2. 知识库管理
# ============================================================

@router.get("/knowledge/list")
async def knowledge_list(
    keyword: str = "",
    category: str = "",
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    token: str = Depends(_check_token),
    db: AsyncSession = Depends(get_db),
):
    """知识库列表（分页 + 搜索）"""
    query = select(KnowledgeEntry)

    # 筛选条件
    if keyword:
        query = query.where(
            KnowledgeEntry.title.contains(keyword) |
            KnowledgeEntry.content.contains(keyword)
        )
    if category:
        query = query.where(KnowledgeEntry.category == category)

    # 总数
    count_query = select(func.count()).select_from(KnowledgeEntry)
    if keyword:
        count_query = count_query.where(
            KnowledgeEntry.title.contains(keyword) |
            KnowledgeEntry.content.contains(keyword)
        )
    if category:
        count_query = count_query.where(KnowledgeEntry.category == category)
    total = await db.scalar(count_query) or 0

    # 分页
    query = query.order_by(KnowledgeEntry.updated_at.desc())
    query = query.offset((page - 1) * page_size).limit(page_size)

    result = await db.execute(query)
    entries = result.scalars().all()

    return _ok({
        "list": [
            {
                "id": e.id,
                "title": e.title,
                "category": e.category,
                "keywords": e.keywords or [],
                "content": e.content,
                "status": e.status,
                "hit_count": e.hit_count,
                "created_at": e.created_at.isoformat() if e.created_at else None,
                "updated_at": e.updated_at.isoformat() if e.updated_at else None,
            }
            for e in entries
        ],
        "total": total,
        "page": page,
        "page_size": page_size,
    })


@router.post("/knowledge/add")
async def knowledge_add(
    data: KnowledgeEntryCreate,
    token: str = Depends(_check_token),
    db: AsyncSession = Depends(get_db),
):
    """新增知识条目"""
    entry = KnowledgeEntry(
        title=data.title,
        category=data.category,
        keywords=data.keywords,
        content=data.content,
        status=data.status,
    )
    db.add(entry)
    await db.commit()
    await db.refresh(entry)

    return _ok({
        "id": entry.id,
        "title": entry.title,
    }, message="添加成功")


@router.post("/knowledge/update")
async def knowledge_update(
    data: KnowledgeEntryUpdate,
    token: str = Depends(_check_token),
    db: AsyncSession = Depends(get_db),
):
    """编辑知识条目"""
    entry = await db.get(KnowledgeEntry, data.id)
    if not entry:
        return _fail("条目不存在", code=2001)

    if data.title is not None:
        entry.title = data.title
    if data.category is not None:
        entry.category = data.category
    if data.keywords is not None:
        entry.keywords = data.keywords
    if data.content is not None:
        entry.content = data.content
    if data.status is not None:
        entry.status = data.status

    await db.commit()
    return _ok(message="更新成功")


@router.post("/knowledge/delete")
async def knowledge_delete(
    id: int,
    token: str = Depends(_check_token),
    db: AsyncSession = Depends(get_db),
):
    """删除知识条目"""
    entry = await db.get(KnowledgeEntry, id)
    if not entry:
        return _fail("条目不存在", code=2001)

    await db.delete(entry)
    await db.commit()
    return _ok(message="删除成功")


@router.post("/knowledge/updateStatus")
async def knowledge_update_status(
    id: int,
    status: str,
    token: str = Depends(_check_token),
    db: AsyncSession = Depends(get_db),
):
    """切换知识条目状态"""
    entry = await db.get(KnowledgeEntry, id)
    if not entry:
        return _fail("条目不存在", code=2001)

    entry.status = status
    await db.commit()
    return _ok(message="状态更新成功")


@router.get("/knowledge/categories")
async def knowledge_categories(
    token: str = Depends(_check_token),
    db: AsyncSession = Depends(get_db),
):
    """获取知识库分类列表"""
    result = await db.execute(
        select(KnowledgeEntry.category).distinct()
    )
    categories = [row[0] for row in result if row[0]]

    # 如果没有自定义分类，提供默认分类
    if not categories:
        categories = ["景区信息", "票务信息", "交通指南", "美食推荐", "住宿信息", "其他"]

    return _ok({"categories": categories})


# ============================================================
# 3. 数据大屏
# ============================================================

@router.get("/dashboard/stats")
async def dashboard_stats(
    token: str = Depends(_check_token),
    db: AsyncSession = Depends(get_db),
):
    """数据大屏 - 统计卡片"""
    # 复用已有 analytics service 获取核心数据
    stats = await analytics_service.get_dashboard_stats(db)

    # 知识库条目总数
    knowledge_count = await db.scalar(
        select(func.count(KnowledgeEntry.id))
    ) or 0

    return _ok({
        "today_chats": stats["today_chats"],
        "today_users": stats["today_users"],
        "week_chats": stats["week_chats"],
        "week_users": stats["week_users"],
        "knowledge_count": knowledge_count,
        "avg_rating": stats["avg_rating"],
        "positive_rate": stats["positive_rate"],
    })


@router.get("/dashboard/trend")
async def dashboard_trend(
    period: str = "week",
    token: str = Depends(_check_token),
    db: AsyncSession = Depends(get_db),
):
    """数据大屏 - 交互趋势"""
    days = 30 if period == "month" else 7
    since = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")

    result = await db.execute(
        select(
            func.strftime("%Y-%m-%d", ChatRecord.created_at).label("date"),
            func.count(ChatRecord.id).label("count"),
        )
        .where(func.strftime("%Y-%m-%d", ChatRecord.created_at) >= since)
        .group_by("date")
        .order_by("date")
    )

    trend = [{"date": row[0], "count": row[1]} for row in result]
    return _ok({"trend": trend, "period": period})


@router.get("/dashboard/hotQuestions")
async def dashboard_hot_questions(
    days: int = Query(7, ge=1, le=30),
    token: str = Depends(_check_token),
    db: AsyncSession = Depends(get_db),
):
    """数据大屏 - 热门问题 TOP10"""
    since = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")

    result = await db.execute(
        select(ChatRecord.user_message, func.count(ChatRecord.id).label("count"))
        .where(func.strftime("%Y-%m-%d", ChatRecord.created_at) >= since)
        .group_by(ChatRecord.user_message)
        .order_by(desc("count"))
        .limit(10)
    )

    questions = [
        {"question": row[0], "count": row[1]}
        for row in result
    ]
    return _ok({"list": questions})


@router.get("/dashboard/recentRecords")
async def dashboard_recent_records(
    limit: int = Query(10, ge=1, le=50),
    token: str = Depends(_check_token),
    db: AsyncSession = Depends(get_db),
):
    """数据大屏 - 最近交互记录"""
    result = await db.execute(
        select(ChatRecord)
        .order_by(ChatRecord.created_at.desc())
        .limit(limit)
    )
    records = result.scalars().all()

    return _ok({
        "list": [
            {
                "id": r.id,
                "session_id": r.session_id,
                "visitor": f"游客{r.session_id[:6]}",
                "question": r.user_message,
                "reply": r.bot_reply[:100] + "..." if len(r.bot_reply) > 100 else r.bot_reply,
                "reply_source": r.reply_source,
                "response_time": r.response_time,
                "created_at": r.created_at.isoformat() if r.created_at else None,
            }
            for r in records
        ]
    })


@router.get("/dashboard/satisfaction")
async def dashboard_satisfaction(
    token: str = Depends(_check_token),
    db: AsyncSession = Depends(get_db),
):
    """数据大屏 - 满意度分布"""
    # 按评分统计
    result = await db.execute(
        select(VisitorFeedback.rating, func.count(VisitorFeedback.id).label("count"))
        .where(VisitorFeedback.rating.isnot(None))
        .group_by(VisitorFeedback.rating)
    )
    rating_dist = {str(row[0]): row[1] for row in result}

    # 按情感统计
    sentiment_result = await db.execute(
        select(VisitorFeedback.sentiment, func.count(VisitorFeedback.id).label("count"))
        .group_by(VisitorFeedback.sentiment)
    )
    sentiment_dist = {row[0]: row[1] for row in sentiment_result}

    return _ok({
        "rating_distribution": rating_dist,
        "sentiment_distribution": sentiment_dist,
    })


# ============================================================
# 4. 情感/游客报告
# ============================================================

@router.get("/visitor/report")
async def visitor_report(
    days: int = Query(7, ge=1, le=30),
    token: str = Depends(_check_token),
    db: AsyncSession = Depends(get_db),
):
    """游客感受度报告"""
    report = await analytics_service.get_sentiment_report(db, days)

    # 额外统计
    since = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")

    # 平均评分
    avg_rating = await db.scalar(
        select(func.avg(VisitorFeedback.rating)).where(
            func.strftime("%Y-%m-%d", VisitorFeedback.created_at) >= since,
            VisitorFeedback.rating.isnot(None),
        )
    ) or 0.0

    # 总交互数
    total_chats = await db.scalar(
        select(func.count(ChatRecord.id)).where(
            func.strftime("%Y-%m-%d", ChatRecord.created_at) >= since,
        )
    ) or 0

    # 平均响应时间
    avg_response = await db.scalar(
        select(func.avg(ChatRecord.response_time)).where(
            func.strftime("%Y-%m-%d", ChatRecord.created_at) >= since,
        )
    ) or 0.0

    return _ok({
        "summary": {
            "avg_rating": round(float(avg_rating), 1),
            "total_chats": total_chats,
            "positive_rate": report["positive_rate"],
            "avg_response_time": round(float(avg_response), 2),
            "total_feedbacks": report["total_feedbacks"],
        },
        "sentiment": {
            "positive": report["positive"],
            "neutral": report["neutral"],
            "negative": report["negative"],
        },
        "feedbacks": report["recent_feedbacks"],
    })


@router.get("/visitor/satisfactionStats")
async def visitor_satisfaction_stats(
    token: str = Depends(_check_token),
    db: AsyncSession = Depends(get_db),
):
    """满意度统计卡片"""
    avg_rating = await db.scalar(
        select(func.avg(VisitorFeedback.rating)).where(VisitorFeedback.rating.isnot(None))
    ) or 0.0

    total_chats = await db.scalar(
        select(func.count(ChatRecord.id))
    ) or 0

    positive_count = await db.scalar(
        select(func.count(VisitorFeedback.id)).where(VisitorFeedback.sentiment == "positive")
    ) or 0
    total_feedbacks = await db.scalar(
        select(func.count(VisitorFeedback.id))
    ) or 1
    positive_rate = round(positive_count / total_feedbacks * 100, 1) if total_feedbacks > 0 else 0.0

    avg_response = await db.scalar(
        select(func.avg(ChatRecord.response_time))
    ) or 0.0

    return _ok({
        "avg_rating": round(float(avg_rating), 1),
        "total_interactions": total_chats,
        "positive_rate": positive_rate,
        "avg_response_time": round(float(avg_response), 2),
    })


@router.get("/visitor/satisfactionTrend")
async def visitor_satisfaction_trend(
    days: int = Query(7, ge=1, le=30),
    token: str = Depends(_check_token),
    db: AsyncSession = Depends(get_db),
):
    """满意度趋势"""
    trend = []
    for i in range(days - 1, -1, -1):
        date = (datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d")

        day_avg = await db.scalar(
            select(func.avg(VisitorFeedback.rating)).where(
                func.strftime("%Y-%m-%d", VisitorFeedback.created_at) == date,
                VisitorFeedback.rating.isnot(None),
            )
        ) or 0.0

        day_count = await db.scalar(
            select(func.count(VisitorFeedback.id)).where(
                func.strftime("%Y-%m-%d", VisitorFeedback.created_at) == date,
            )
        ) or 0

        trend.append({
            "date": date,
            "avg_rating": round(float(day_avg), 1),
            "feedback_count": day_count,
        })

    return _ok({"trend": trend})
