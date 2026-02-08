from bson import ObjectId
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

    async def get_chunk(self, chunk_id: int): # غيرت النوع لـ int لأنه Primary Key في تعريفك
        async with self.db_client() as session: # type: ignore
            # تم تصحيح اسم العمود إلى chunk_id
            stmt = select(DataChunk).where(DataChunk.chunk_id == chunk_id)
            result = await session.execute(stmt)
            return result.scalar_one_or_none()

    async def insert_many_chunks(self, chunks: list, batch_size: int = 100):
        async with self.db_client() as session: # type: ignore
            async with session.begin():
                for i in range(0, len(chunks), batch_size):
                    batch = chunks[i:i + batch_size]
                    session.add_all(batch)
                    # الـ flush هنا كافٍ، والـ commit سيحدث تلقائياً في نهاية الـ with
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
            
    async def get_total_chunk_count(self, project_id: int):
        async with self.db_client() as session: # type: ignore
            # تصحيح الـ count بتحديد العمود
            count_sql = select(func.count(DataChunk.chunk_id)).where(DataChunk.chunk_project_id == project_id)
            count_result = await session.execute(count_sql)
            return count_result.scalar() or 0