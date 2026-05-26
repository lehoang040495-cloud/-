"""
Initialize default data: create default avatar config and sample route recommendations
"""
import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.database import async_session, init_db
from app.models import AvatarConfig, RouteRecommendation


async def seed():
    await init_db()

    async with async_session() as db:
        # Default avatar
        from sqlalchemy import select
        existing = await db.execute(select(AvatarConfig))
        if not existing.scalars().first():
            avatar = AvatarConfig(
                name="小景（默认）",
                model_url="https://cdn.jsdelivr.net/gh/guansss/pixi-live2d-display/test/assets/shizuku/shizuku.model.json",
                voice_name="zh-CN-XiaoxiaoNeural",
                voice_rate="+0%",
                greeting="您好！我是您的智能导游小景，很高兴为您服务！请问有什么可以帮您的？",
                outfit="default",
                is_active=True,
            )
            db.add(avatar)

        # Sample routes
        existing_routes = await db.execute(select(RouteRecommendation))
        if not existing_routes.scalars().first():
            routes = [
                RouteRecommendation(
                    name="历史文化之旅",
                    description="深度探索景区的历史文化遗迹，感受千年传承",
                    interest_tag="history",
                    spots=["古城门", "文庙", "历史博物馆", "古街道"],
                    duration="3-4小时",
                    difficulty="easy",
                ),
                RouteRecommendation(
                    name="自然风光路线",
                    description="欣赏景区最美的自然风光，感受山水之美",
                    interest_tag="nature",
                    spots=["观景台", "瀑布群", "植物园", "湖心亭"],
                    duration="4-5小时",
                    difficulty="medium",
                ),
                RouteRecommendation(
                    name="亲子欢乐游",
                    description="适合全家出行的轻松路线，趣味十足",
                    interest_tag="family",
                    spots=["互动体验馆", "儿童乐园", "美食街", "纪念品商店"],
                    duration="2-3小时",
                    difficulty="easy",
                ),
            ]
            for route in routes:
                db.add(route)

        await db.commit()
        print("Default data initialized successfully!")


if __name__ == "__main__":
    asyncio.run(seed())
