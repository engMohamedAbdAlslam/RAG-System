from datetime import datetime, timedelta
from typing import Optional, List, Any
import uuid
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from .BaseDataModel import BaseDataModel
from models.db__schemes.minirag.schemes.chat_message import ChatMessage
from models.db__schemes.minirag.schemes.session import ChatSession

class ChatRepositoryModel(BaseDataModel):
    def __init__(self, db_session_factory: Any):
        # نمرر المصنع للكلاس الأب إذا كان يحتاجه، ونحتفظ به هنا
        super().__init__(db_client=db_session_factory) 
        self.db_session_factory = db_session_factory

    async def create_chat_session(self, project_id: int, session_name: Optional[str] = None):
        async with self.db_session_factory() as db: # تصحيح: فتح جلسة هنا
            new_uuid = (uuid.uuid4())
            expiration_date = datetime.now() + timedelta(hours=1)

            new_session = ChatSession(
                session_uuid=new_uuid,
                project_id=project_id,
                session_name=session_name or f"Chat {datetime.now().strftime('%Y-%m-%d %H:%M')}",
                expires_at=expiration_date,
                is_active=True
            )

            db.add(new_session)
            await db.commit()
            await db.refresh(new_session)
            return new_session

    async def get_or_create_session(self, session_uuid: Optional[uuid.UUID], project_id: int):
        async with self.db_session_factory() as db:
            if session_uuid and session_uuid: 
                stmt = select(ChatSession).filter(
                    ChatSession.session_uuid == session_uuid,
                    ChatSession.project_id == project_id
                )
                result = await db.execute(stmt)
                session = result.scalar_one_or_none()
                if session:
                    return session

            # إنشاء جلسة جديدة إذا لم توجد
            new_uuid = (uuid.uuid4())
            new_session = ChatSession(
                session_uuid=new_uuid, 
                project_id=project_id,
                is_active=True
            )
            
            db.add(new_session)
            await db.commit()
            await db.refresh(new_session)
            return new_session
        
    async def get_session_history(self, session_uuid: uuid.UUID) -> List[ChatMessage]:
        async with self.db_session_factory() as db:
            result = await db.execute(
                select(ChatMessage)
                .join(ChatSession)
                .filter(ChatSession.session_uuid == session_uuid)
                .order_by(ChatMessage.created_at.asc())
            )
            return list(result.scalars().all())

    async def save_chat_message(self, session_uuid: uuid.UUID, role: str, text: str):
        async with self.db_session_factory() as db:
            result = await db.execute(
                select(ChatSession).filter(ChatSession.session_uuid == session_uuid)
            )
            session = result.scalar_one_or_none()
            
            if session:
                new_msg = ChatMessage(
                    session_id=session.session_id, 
                    role=role, 
                    message_text=text
                )
                db.add(new_msg)
                session.updated_at = func.now() 
                await db.commit()
                await db.refresh(new_msg)
                return new_msg