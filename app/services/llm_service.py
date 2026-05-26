"""
LLM Service - Supports DeepSeek API and Doubao proxy gateway
"""
import logging
import httpx
from openai import AsyncOpenAI
from app.config import settings

logger = logging.getLogger(__name__)


class LLMService:
    def __init__(self):
        self.provider = settings.LLM_PROVIDER
        self.system_prompt = (
            "你是「小景」，一位专业、热情、知识渊博的景区智能导游。"
            "你的职责是为游客提供准确、生动的景区讲解服务。\n"
            "回答要求：\n"
            "1. 基于提供的景区知识资料回答问题，不要编造事实\n"
            "2. 语言亲切自然，像朋友聊天一样\n"
            "3. 适当加入历史典故和文化背景，让讲解更生动\n"
            "4. 如果游客问到非景区相关问题，礼貌地引导回景区话题\n"
            "5. 如果知识库中没有相关信息，诚实告知并建议游客咨询景区服务台\n"
            "6. 回答简洁明了，一般不超过200字"
        )

        if self.provider == "doubao":
            logger.info(f"LLM provider: Doubao Proxy (model={settings.DOUBAO_MODEL})")
        else:
            self.client = AsyncOpenAI(
                api_key=settings.DEEPSEEK_API_KEY,
                base_url=settings.DEEPSEEK_BASE_URL,
            )
            self.model = settings.DEEPSEEK_MODEL
            logger.info(f"LLM provider: DeepSeek (model={self.model})")

    async def _call_doubao(self, messages: list[dict]) -> str:
        """Call Doubao proxy via httpx with query-param auth"""
        headers = {
            "Content-Type": "application/json",
            "Open-ID": settings.DOUBAO_OPEN_ID,
            "Developer-Secret": settings.DOUBAO_DEVELOPER_SECRET,
            "Service-Code": "ai_proxy",
            "S-Open-Id": settings.DOUBAO_OPEN_ID,
        }
        params = {
            "serviceCode": "ai_proxy",
            "sOpenId": settings.DOUBAO_OPEN_ID,
        }
        payload = {
            "model": settings.DOUBAO_MODEL,
            "messages": messages,
            "max_tokens": 512,
            "temperature": 0.7,
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(
                settings.DOUBAO_ENDPOINT,
                json=payload,
                headers=headers,
                params=params,
            )
            resp.raise_for_status()
            data = resp.json()

        if "choices" not in data:
            logger.error(f"Doubao unexpected response: {data}")
            return "抱歉，大模型返回了异常响应。"

        content = data["choices"][0]["message"]["content"]
        return content.strip()

    async def _call_deepseek(self, messages: list[dict]) -> str:
        """Call DeepSeek via OpenAI SDK"""
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=512,
                temperature=0.7,
                top_p=0.9,
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            logger.error(f"DeepSeek call failed: {e}")
            return "抱歉，我暂时无法回答您的问题，请稍后再试。"

    async def _call_llm(self, messages: list[dict]) -> str:
        """Unified LLM call"""
        try:
            if self.provider == "doubao":
                return await self._call_doubao(messages)
            else:
                return await self._call_deepseek(messages)
        except Exception as e:
            logger.error(f"LLM call failed ({self.provider}): {e}")
            return "抱歉，我暂时无法回答您的问题，请稍后再试。"

    async def chat(self, user_message: str, context: str = "") -> str:
        messages = [{"role": "system", "content": self.system_prompt}]
        if context:
            messages.append({
                "role": "system",
                "content": f"以下是景区知识库中的相关资料，请据此回答游客问题：\n\n{context}"
            })
        messages.append({"role": "user", "content": user_message})
        return await self._call_llm(messages)

    async def chat_with_history(self, messages_history: list, context: str = "") -> str:
        full_messages = [{"role": "system", "content": self.system_prompt}]
        if context:
            full_messages.append({
                "role": "system",
                "content": f"以下是景区知识库中的相关资料，请据此回答游客问题：\n\n{context}"
            })
        full_messages.extend(messages_history)
        return await self._call_llm(full_messages)

    async def analyze_sentiment(self, text: str) -> str:
        try:
            messages = [
                {"role": "system", "content": "你是一个情感分析助手。只回复一个词：positive、neutral 或 negative。"},
                {"role": "user", "content": f"分析以下文本的情感倾向：\n{text}"}
            ]
            result = await self._call_llm(messages)
            result = result.strip().lower()
            if result in ("positive", "neutral", "negative"):
                return result
            return "neutral"
        except Exception:
            return "neutral"

    async def recommend_route(self, interest: str, knowledge_context: str = "") -> str:
        context_msg = ""
        if knowledge_context:
            context_msg = f"\n景区参考资料：\n{knowledge_context}"

        messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": f"游客表示对「{interest}」感兴趣，请为其推荐一条游览路线，包含景点名称、推荐游览时间和简要说明。{context_msg}"}
        ]
        return await self._call_llm(messages)


llm_service = LLMService()
