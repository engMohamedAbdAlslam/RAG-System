from venv import create
from .minirag_base import SQLAlchemyBase
from sqlalchemy import Column,Integer , DateTime, func
from sqlalchemy.dialects.postgresql import UUID
import uuid
from sqlalchemy.orm import relationship


class Project(SQLAlchemyBase):
    __tablename__ = "projects"

    project_id = Column(Integer,primary_key = True,autoincrement = True)
    poject_uuid = Column(UUID(as_uuid=True),default=uuid.uuid4,unique=True,nullable=False)

    create_at = Column(DateTime(timezone=True),server_default=func.now(),nullable=False)
    update_at = Column(  # ✅ إضافة القيمة الافتراضية للـ insert الأولي
        DateTime(timezone=True),
        default=func.now(),          # ← مهم جدًا للـ insert الأولي
        onupdate=func.now(),         # للتحديثات اللاحقة
        server_default=func.now(),   # احتياطي على مستوى قاعدة البيانات
        nullable=False
    )

    chunks = relationship("DataChunk",back_populates="project")
    assets = relationship("Asset",back_populates="project")