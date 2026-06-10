"""
Chat API - Core conversational endpoint
"""
import asyncio
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

CHAT_TIMEOUT_SECONDS = 10
RAG_TIMEOUT_SECONDS = 3
RAG_TOP_K = 2
FALLBACK_REPLY = "抱歉，当前网络有点慢，请稍后再试一次。"

QUICK_REPLIES = {
    "continue": "我可以继续为你介绍景点、路线、拍照点和服务设施，你想先了解哪一类？",
    "identity": "我是景区智能导游小景，可以为你讲解景点、推荐路线、提醒服务设施和拍照打卡点。",
    "lingshan_buddha": "灵山大佛是灵山胜境的标志景观，通高88米，庄严壮观。适合在广场正面拍照，也可以登台近距离参观。",
    "fan_gong": "梵宫是灵山胜境的文化建筑亮点，内部装饰精美，适合参观佛教艺术、拍摄建筑细节。",
    "route": "推荐先看灵山大佛，再游九龙灌浴、梵宫和五印坛城。全程约3到4小时，适合慢慢参观。",
}

SCENIC_KEYWORDS = (
    "灵山",
    "大佛",
    "梵宫",
    "九龙",
    "五印",
    "祥符",
    "景区",
    "景点",
    "门票",
    "路线",
    "游览",
    "拍照",
    "打卡",
    "服务",
    "设施",
    "天气",
    "停车",
    "卫生间",
    "讲解",
)


def _get_quick_reply(message: str) -> str:
    """Return deterministic mobile-friendly replies for common questions."""
    text = (message or "").strip().lower()
    if not text:
        return ""

    if text in ("继续", "接着说", "继续说", "再说"):
        return QUICK_REPLIES["continue"]

    if "灵山大佛" in text or "大佛" in text:
        return QUICK_REPLIES["lingshan_buddha"]
    if "梵宫" in text:
        return QUICK_REPLIES["fan_gong"]
    if "路线" in text or "怎么逛" in text or "游览" in text:
        return QUICK_REPLIES["route"]

    identity_keywords = (
        "你好",
        "您好",
        "hello",
        "hi",
        "你是谁",
        "你是什么",
        "什么模型",
        "能做什么",
        "可以干什么",
        "可以做什么",
        "有什么功能",
        "介绍你自己",
    )
    if any(keyword in text for keyword in identity_keywords):
        return QUICK_REPLIES["identity"]

    return ""


def _should_use_rag(message: str) -> bool:
    """Only use knowledge retrieval for scenic-guide questions."""
    text = (message or "").strip()
    return any(keyword in text for keyword in SCENIC_KEYWORDS)


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

    context = ""
    source = "llm"
    quick_reply = _get_quick_reply(request.message)

    if quick_reply:
        response_time = time.time() - start_time
        await analytics_service.record_chat(
            db=db,
            session_id=request.session_id,
            user_message=request.message,
            bot_reply=quick_reply,
            input_type=request.input_type,
            reply_source="template",
            response_time=round(response_time, 3),
        )
        return ChatResponse(
            reply=quick_reply,
            session_id=request.session_id,
            source="template",
            response_time=round(response_time, 3),
        )

    if _should_use_rag(request.message):
        try:
            context = await asyncio.wait_for(
                rag_service.get_context(request.message, top_k=RAG_TOP_K),
                timeout=RAG_TIMEOUT_SECONDS,
            )
            logger.info(f"Context length: {len(context)} chars, mode: {mode}")
        except asyncio.TimeoutError:
            logger.warning("RAG context retrieval timed out; falling back to LLM only")
        except Exception as e:
            logger.error(f"RAG context retrieval failed: {e}")

    try:
        reply = await asyncio.wait_for(
            llm_service.chat(request.message, context=context, mode=mode),
            timeout=CHAT_TIMEOUT_SECONDS,
        )
        source = "rag" if context else "llm"
    except asyncio.TimeoutError:
        logger.warning("Chat generation timed out")
        reply = FALLBACK_REPLY
        source = "fallback"
    except Exception as e:
        logger.error(f"Chat generation failed: {e}")
        reply = FALLBACK_REPLY
        source = "fallback"

    if not reply:
        reply = FALLBACK_REPLY
        source = "fallback"

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
