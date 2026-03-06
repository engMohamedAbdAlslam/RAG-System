from .minirag_base import SQLAlchemyBase
from sqlalchemy import Boolean, Column, ForeignKey, Integer, DateTime, func, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid

class ChatSession(SQLAlchemyBase):
    __tablename__ = "chat_sessions"

    session_id = Column(Integer, primary_key=True, autoincrement=True)
    session_uuid = Column(UUID(as_uuid=True), default=uuid.uuid4, unique=True, nullable=False)
    
    # ربط الجلسة بالمشروع
    project_id = Column(Integer, ForeignKey("projects.project_id"), nullable=False)
    
    # اسم اختياري للجلسة (مثل: "مناقشة السيرة الذاتية")
    session_name = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(
        DateTime(timezone=True), 
        server_default=func.now(), 
        onupdate=func.now(), # يتحدث تلقائياً عند أي تعديل في السطر
        nullable=False
    )
    expires_at = Column(DateTime(timezone=True), nullable=True) # سنقوم بحسابه برمجياً
    
    # التحكم اليدوي
    is_active = Column(Boolean, default=True, nullable=False)

    messages = relationship("ChatMessage", back_populates="session", cascade="all, delete-orphan")
    project = relationship("Project", back_populates="sessions")