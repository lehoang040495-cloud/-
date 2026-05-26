"""
LLM Service - Supports DeepSeek API and Doubao proxy gateway
"""
import logging
import base64
import httpx
from openai import AsyncOpenAI
from app.config import settings

logger = logging.getLogger(__name__)

MODE_PROMPTS = {
    "normal": (
        "你是「小景」，一位专业、热情、知识渊博的景区智能导游。"
        "你的职责是为游客提供准确、生动的景区讲解服务。\n"
        "回答要求：\n"
        "1. 基于提供的景区知识资料回答问题，不要编造事实\n"
        "2. 语言亲切自然，像朋友聊天一样\n"
        "3. 适当加入历史典故和文化背景，让讲解更生动\n"
        "4. 如果游客问到非景区相关问题，礼貌地引导回景区话题\n"
        "5. 如果知识库中没有相关信息，诚实告知并建议游客咨询景区服务台\n"
        "6. 回答简洁明了，一般不超过200字"
    ),
    "elderly": (
        "你是「小景」，一位耐心、温暖的景区导游，专门为老年游客服务。\n"
        "回答要求：\n"
        "1. 语言简单易懂，语速适中，避免复杂术语\n"
        "2. 特别关注老年人的安全和体力，提醒休息和补水\n"
        "3. 推荐平缓、舒适的游览路线，提醒台阶和坡道\n"
        "4. 讲解以故事为主，温暖贴心，像对家人一样\n"
        "5. 主动提醒天气变化、随身物品保管等\n"
        "6. 回答详细但口语化，不用长句，重要信息重复强调"
    ),
    "children": (
        "你是「小景」，一位活泼、有趣的景区导游，专门为小朋友服务。\n"
        "回答要求：\n"
        "1. 用简单有趣的语言，就像讲故事一样\n"
        "2. 多用比喻和拟人手法，让景点生动有趣\n"
        "3. 加入趣味问答和互动环节，激发好奇心\n"
        "4. 提醒注意安全，不要乱跑，牵好大人的手\n"
        "5. 适当介绍自然科学知识，寓教于乐\n"
        "6. 回答活泼可爱，多用感叹号和语气词"
    ),
}


class LLMService:
    def __init__(self):
        self.provider = settings.LLM_PROVIDER
        self.current_mode = "normal"

        if self.provider == "doubao":
            logger.info(f"LLM provider: Doubao Proxy (model={settings.DOUBAO_MODEL})")
        else:
            self.client = AsyncOpenAI(
                api_key=settings.DEEPSEEK_API_KEY,
                base_url=settings.DEEPSEEK_BASE_URL,
            )
            self.model = settings.DEEPSEEK_MODEL
            logger.info(f"LLM provider: DeepSeek (model={self.model})")

    def get_system_prompt(self, mode: str = None) -> str:
        mode = mode or self.current_mode
        return MODE_PROMPTS.get(mode, MODE_PROMPTS["normal"])

    def set_mode(self, mode: str):
        if mode in MODE_PROMPTS:
            self.current_mode = mode

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

    async def _call_doubao_vision(self, messages: list[dict]) -> str:
        """Call Doubao with image content for vision tasks"""
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
            "max_tokens": 800,
            "temperature": 0.5,
        }

        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.post(
                settings.DOUBAO_ENDPOINT,
                json=payload,
                headers=headers,
                params=params,
            )
            resp.raise_for_status()
            data = resp.json()

        if "choices" not in data:
            logger.error(f"Doubao vision unexpected response: {data}")
            return "抱歉，图片识别失败。"

        return data["choices"][0]["message"]["content"].strip()

    async def chat(self, user_message: str, context: str = "", mode: str = None) -> str:
        system_prompt = self.get_system_prompt(mode)
        messages = [{"role": "system", "content": system_prompt}]
        if context:
            messages.append({
                "role": "system",
                "content": f"以下是景区知识库中的相关资料，请据此回答游客问题：\n\n{context}"
            })
        messages.append({"role": "user", "content": user_message})
        return await self._call_llm(messages)

    async def chat_with_history(self, messages_history: list, context: str = "", mode: str = None) -> str:
        system_prompt = self.get_system_prompt(mode)
        full_messages = [{"role": "system", "content": system_prompt}]
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
            {"role": "system", "content": self.get_system_prompt()},
            {"role": "user", "content": f"游客表示对「{interest}」感兴趣，请为其推荐一条游览路线，包含景点名称、推荐游览时间和简要说明。{context_msg}"}
        ]
        return await self._call_llm(messages)

    async def companion_answer(self, query: str, query_type: str, context: str = "") -> str:
        type_prompts = {
            "emergency": "游客遇到了紧急情况！请提供紧急联系信息和安全建议。",
            "service": "游客在寻找附近的服务设施（如洗手间、餐厅、售票处等）。",
            "reminder": "请为游客提供游览注意事项和温馨提示。",
            "pitfall": "游客想了解景区的避坑指南，包括常见的注意事项和消费提醒。",
            "general": "",
        }
        type_hint = type_prompts.get(query_type, "")
        system_content = (
            "你是景区导游助手，专门回答游客的实用问题。\n"
            "请提供具体、实用、准确的建议。如果涉及价格或时间，请说明可能有变动。"
        )
        messages = [{"role": "system", "content": system_content}]
        if type_hint:
            messages.append({"role": "system", "content": type_hint})
        if context:
            messages.append({"role": "system", "content": f"参考资料：\n{context}"})
        messages.append({"role": "user", "content": query})
        return await self._call_llm(messages)

    async def analyze_visitor_profile(self, chat_history: list[str]) -> dict:
        if not chat_history:
            return {"interests": [], "travel_style": "general", "summary": "新游客"}

        history_text = "\n".join(f"- {msg}" for msg in chat_history[-20:])
        messages = [
            {
                "role": "system",
                "content": (
                    "你是游客画像分析助手。根据游客的对话记录，分析游客的兴趣和偏好。\n"
                    "请用JSON格式回复，包含以下字段：\n"
                    "- interests: 兴趣标签列表（如历史、自然、美食、文化、亲子等）\n"
                    "- travel_style: 旅行风格（culture/nature/family/adventure/relaxation）\n"
                    "- preferred_duration: 偏好游览时长\n"
                    "- summary: 一句话总结游客画像\n"
                    "只返回JSON，不要其他内容。"
                )
            },
            {"role": "user", "content": f"游客对话记录：\n{history_text}"}
        ]
        try:
            result = await self._call_llm(messages)
            import json
            result = result.strip()
            if result.startswith("```"):
                result = result.split("\n", 1)[-1].rsplit("```", 1)[0].strip()
            return json.loads(result)
        except Exception as e:
            logger.error(f"Profile analysis failed: {e}")
            return {"interests": [], "travel_style": "general", "summary": "分析失败"}

    async def generate_commemorative_text(self, spots: list[str]) -> str:
        spots_text = "、".join(spots)
        messages = [
            {
                "role": "system",
                "content": "你是一位有文采的景区导游，请为游客生成一段温馨的旅行纪念文字。"
            },
            {
                "role": "user",
                "content": (
                    f"游客游览了以下景点：{spots_text}\n"
                    "请生成一段50-100字的旅行纪念文字，回顾这段旅程的美好时光。"
                    "语言温暖有诗意，适合放在纪念卡片上。"
                )
            }
        ]
        return await self._call_llm(messages)

    async def recognize_spot_from_image(self, image_base64: str, context: str = "") -> str:
        messages = [
            {
                "role": "system",
                "content": (
                    "你是一个景区景点识别助手。请根据游客拍摄的图片，识别这是哪个景点。\n"
                    "请用以下JSON格式回复：\n"
                    '{"spot_name": "景点名称", "description": "景点描述", '
                    '"history": "历史背景", "tips": "游览建议"}\n'
                    "如果无法确定具体景点，请根据图片内容给出合理的描述和建议。只返回JSON。"
                )
            },
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": "请识别这张图片中的景点。" + (f"\n参考知识：{context}" if context else "")
                    },
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:image/jpeg;base64,{image_base64}"}
                    }
                ]
            }
        ]
        try:
            result = await self._call_doubao_vision(messages)
            return result
        except Exception as e:
            logger.error(f"Vision recognition failed: {e}")
            return '{"spot_name": "未知景点", "description": "抱歉，图片识别失败，请重新拍摄", "history": "", "tips": ""}'

    async def generate_care_message(self, weather_info: str = "", visitor_sentiment: str = "neutral") -> str:
        context_parts = []
        if weather_info:
            context_parts.append(f"当前天气：{weather_info}")
        context_parts.append(f"游客情绪倾向：{visitor_sentiment}")

        messages = [
            {
                "role": "system",
                "content": (
                    "你是景区关怀助手。请根据游客的情绪和天气情况，生成一条贴心的关怀消息。\n"
                    "要求：简短温暖（30字以内），像朋友发的微信消息一样自然。"
                )
            },
            {
                "role": "user",
                "content": "\n".join(context_parts)
            }
        ]
        return await self._call_llm(messages)


llm_service = LLMService()
