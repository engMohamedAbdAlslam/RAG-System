from .minirag_base import SQLAlchemyBase
from sqlalchemy import Column, ForeignKey, Integer, DateTime, func, String, Text
from sqlalchemy.orm import relationship

class ChatMessage(SQLAlchemyBase):
    __tablename__ = "chat_messages"

    message_id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(Integer, ForeignKey("chat_sessions.session_id"), nullable=False)
    
    role = Column(String, nullable=False) 
    
    message_text = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    session = relationship("ChatSession", back_populates="messages")