"""
Companion API - Travel companion assistant
Emergency help, nearby services, care reminders, pitfall guide
"""
import logging
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas import CompanionRequest, CompanionResponse
from app.services.llm_service import llm_service
from app.services.rag_service import rag_service

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api", tags=["Companion"])


@router.post("/companion", response_model=CompanionResponse)
async def companion_query(request: CompanionRequest, db: AsyncSession = Depends(get_db)):
    """Travel companion assistant - emergency, services, reminders, pitfall guide"""
    context = await rag_service.get_context(request.query, top_k=3)
    reply = await llm_service.companion_answer(request.query, request.query_type, context)
    return CompanionResponse(
        reply=reply,
        query_type=request.query_type,
        source="rag" if context else "llm",
    )


@router.post("/companion/emergency")
async def emergency_help(
    description: str = "游客需要帮助",
    db: AsyncSession = Depends(get_db),
):
    """Emergency assistance endpoint"""
    context = await rag_service.get_context("紧急情况 救援 安全", top_k=3)
    reply = await llm_service.companion_answer(
        f"紧急情况：{description}",
        query_type="emergency",
        context=context,
    )
    return {
        "reply": reply,
        "emergency_contacts": {
            "scenic_service": "景区服务热线：请拨打景区公告电话",
            "police": "110",
            "medical": "120",
            "fire": "119",
        },
    }


@router.get("/companion/services")
async def get_nearby_services(
    spot: str = "",
    db: AsyncSession = Depends(get_db),
):
    """Get nearby service facilities"""
    query = f"{spot}附近服务设施 洗手间 餐厅 售票处 停车场"
    context = await rag_service.get_context(query, top_k=3)
    reply = await llm_service.companion_answer(
        f"游客在「{spot}」附近，请介绍附近的服务设施",
        query_type="service",
        context=context,
    )
    return {"reply": reply, "spot": spot}


@router.get("/companion/reminders")
async def get_reminders(db: AsyncSession = Depends(get_db)):
    """Get travel reminders and tips"""
    context = await rag_service.get_context("游览注意 安全提示 温馨提醒", top_k=3)
    reply = await llm_service.companion_answer(
        "请为游客提供游览注意事项和温馨提示",
        query_type="reminder",
        context=context,
    )
    return {"reminders": reply}


@router.get("/companion/pitfall-guide")
async def get_pitfall_guide(db: AsyncSession = Depends(get_db)):
    """Get pitfall avoidance guide"""
    context = await rag_service.get_context("避坑指南 消费注意 门票 陷阱", top_k=3)
    reply = await llm_service.companion_answer(
        "请为游客提供景区避坑指南，包括消费注意事项",
        query_type="pitfall",
        context=context,
    )
    return {"guide": reply}
