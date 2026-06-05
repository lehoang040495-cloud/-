from sqlalchemy import Column, Integer, String, Text, DateTime, Float, JSON, Boolean
from sqlalchemy.sql import func
from app.database import Base


class KnowledgeDocument(Base):
    """知识库文档"""
    __tablename__ = "knowledge_documents"

    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(255), nullable=False)
    file_name = Column(String(255), nullable=False)
    file_path = Column(String(512), nullable=False)
    file_type = Column(String(20), nullable=False)  # pdf, docx, txt, xlsx
    category = Column(String(100), default="通用")
    chunk_count = Column(Integer, default=0)
    status = Column(String(20), default="active")  # active, disabled
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())


class ChatRecord(Base):
    """对话记录"""
    __tablename__ = "chat_records"

    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(String(100), nullable=False, index=True)
    user_message = Column(Text, nullable=False)
    bot_reply = Column(Text, nullable=False)
    input_type = Column(String(20), default="text")  # text, voice
    reply_source = Column(String(20), default="rag")  # rag, llm
    response_time = Column(Float, default=0.0)
    created_at = Column(DateTime, server_default=func.now())


class VisitorFeedback(Base):
    """游客反馈"""
    __tablename__ = "visitor_feedback"

    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(String(100), nullable=False, index=True)
    rating = Column(Integer)  # 1-5
    feedback_text = Column(Text)
    sentiment = Column(String(20))  # positive, neutral, negative
    created_at = Column(DateTime, server_default=func.now())


class AvatarConfig(Base):
    """数字人形象配置"""
    __tablename__ = "avatar_configs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    model_url = Column(String(512), nullable=False)
    voice_name = Column(String(100), default="zh-CN-XiaoxiaoNeural")
    voice_rate = Column(String(20), default="+0%")
    greeting = Column(Text, default="您好！我是您的智能导游小景，很高兴为您服务！")
    outfit = Column(String(100), default="default")
    mode = Column(String(20), default="normal")  # normal, elderly, children
    is_active = Column(Boolean, default=False)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())


class RouteRecommendation(Base):
    """推荐路线"""
    __tablename__ = "route_recommendations"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(200), nullable=False)
    description = Column(Text)
    interest_tag = Column(String(100))  # history, nature, culture, family
    spots = Column(JSON)  # 景点列表
    duration = Column(String(50))
    difficulty = Column(String(20), default="easy")
    created_at = Column(DateTime, server_default=func.now())


class DailyStatistics(Base):
    """每日统计"""
    __tablename__ = "daily_statistics"

    id = Column(Integer, primary_key=True, autoincrement=True)
    date = Column(String(10), nullable=False, unique=True)  # YYYY-MM-DD
    total_chats = Column(Integer, default=0)
    total_users = Column(Integer, default=0)
    avg_rating = Column(Float, default=0.0)
    positive_rate = Column(Float, default=0.0)
    top_questions = Column(JSON)
    created_at = Column(DateTime, server_default=func.now())


class TravelTrajectory(Base):
    """游客游览轨迹"""
    __tablename__ = "travel_trajectories"

    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(String(100), nullable=False, index=True)
    spot_name = Column(String(200), nullable=False)
    spot_description = Column(Text)
    longitude = Column(Float)
    latitude = Column(Float)
    visit_order = Column(Integer, default=0)
    photo_url = Column(String(512))
    note = Column(Text)
    visited_at = Column(DateTime, server_default=func.now())


class VisitorProfile(Base):
    """游客画像"""
    __tablename__ = "visitor_profiles"

    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(String(100), nullable=False, unique=True, index=True)
    interests = Column(JSON)  # 兴趣标签列表
    travel_style = Column(String(50))  # culture, nature, family, adventure
    preferred_duration = Column(String(50))
    sentiment_summary = Column(String(20), default="neutral")
    chat_count = Column(Integer, default=0)
    profile_data = Column(JSON)  # 详细画像数据
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())


class KnowledgeEntry(Base):
    """知识库条目（管理端直接编辑的文本知识）"""
    __tablename__ = "knowledge_entries"

    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(255), nullable=False)
    category = Column(String(100), default="通用")
    keywords = Column(JSON)  # 关键词标签列表
    content = Column(Text, nullable=False)
    status = Column(String(20), default="active")  # active, disabled
    hit_count = Column(Integer, default=0)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())


class CareMessage(Base):
    """关怀消息记录"""
    __tablename__ = "care_messages"

    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(String(100), nullable=False, index=True)
    message_type = Column(String(50))  # weather, emotion, reminder, safety
    content = Column(Text, nullable=False)
    is_read = Column(Boolean, default=False)
    created_at = Column(DateTime, server_default=func.now())
