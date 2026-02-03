from .BaseDataModel import BaseDataModel
from .db__schemes import DataChunk
from sqlalchemy import delete, func, select
from sqlalchemy.exc import NoResultFound

class DataChunkModel(BaseDataModel):
    def __init__(self, db_client: object):
        super().__init__(db_client=db_client)
        self.db_client = db_client

    @classmethod
    async def create_instance(cls, db_client: object):
        instance = cls(db_client)
        return instance

    async def create_chunk(self, chunk: DataChunk):
        async with self.db_client() as session: # type: ignore
            async with session.begin():
                session.add(chunk)
            await session.commit()
            await session.refresh(chunk)
        return chunk

    async def get_chunk(self, chunk_id: str):
        async with self.db_client() as session: # type: ignore
            async with session.begin():
                stmt = select(DataChunk).where(DataChunk.id == chunk_id)
                result = await session.execute(stmt)
                return result.scalar_one_or_none()

    async def insert_many_chunks(self, chunks: list, batch_size: int = 100):
        """إدخال دفعات من الـ chunks مع تحسين الأداء"""
        async with self.db_client() as session: # type: ignore
            async with session.begin():
                for i in range(0, len(chunks), batch_size):
                    batch = chunks[i:i + batch_size]
                    session.add_all(batch)
                    # flush دوري لتجنب استهلاك الذاكرة مع الحفاظ على الأداء
                    if (i // batch_size) % 10 == 0:  # flush كل 10 دفعات
                        await session.flush()
        return len(chunks)

    async def delete_chunks_by_project_id(self, project_id: str):  # تم الحفاظ على الاسم الأصلي مع التنويه
        async with self.db_client() as session: # type: ignore
            async with session.begin():
                stmt = delete(DataChunk).where(DataChunk.chunk_project_id == project_id)
                result = await session.execute(stmt)
                return result.rowcount  # عدد السجلات المحذوفة

    async def get_project_chunks(self, project_id: str, page: int = 1, page_size: int = 50):
        async with self.db_client() as session: # type: ignore
            async with session.begin():
                count_stmt = select(func.count(DataChunk.chunk_id)).where(
                    DataChunk.chunk_project_id == project_id
                )
                total_result = await session.execute(count_stmt)
                total_documents = total_result.scalar_one()
                
                total_pages = (total_documents + page_size - 1) // page_size  
                
                stmt = (
                    select(DataChunk)
                    .where(DataChunk.chunk_project_id == project_id)
                    .offset((page - 1) * page_size)
                    .limit(page_size)
                )
                result = await session.execute(stmt)
                chunks = result.scalars().all()
                
                return chunks, total_pages