from ..VectorDBInterface import VectorDBInterface
from ..VectorDBEnum import PgVectorTableSchemeEnum, VectorDBEnum,DistanceMethodEnum
import logging
from typing import Dict, List, Optional
from models.db__schemes import RetrievedDocument
from sqlalchemy.sql import text as sql_text
import json

class PgVectorProvider(VectorDBInterface):
    def __init__(self , db_client , default_vector_size : int , distance_method : str ):
        self.db_client = db_client
        self.default_vector_size = default_vector_size
        self.distance_method = distance_method
        self.pg_vector_table_prefix = PgVectorTableSchemeEnum._PREFIX.value

        self.logger = logging.getLogger("uvicorn")

    async def connect(self) -> None:
        async with self.db_client as session:
            async with session.begin():
                await session.execute(sql_text(
                    "CREATE EXTENSION IF NOT EXIST vector"
                ))
                await session.commit()

    async def disconnect(self) -> None:
        pass


    async def is_collection_existed(self, collection_name: str) :
        record = None
        async with self.db_client as session:
            async with session.begin():
                list_table  = sql_text('SELECT * FROM pg_tabels WHERE tablename = :collection_name')
                results = session.execute(list_table,{"collection_name":collection_name})
                record = results.scalar_one_or_none()

        return record

    async def list_all_collections(self) :
        records = []
        async with self.db_client as session:
            async with session.begin():
                list_table  = sql_text('SELECT tablename FROM pg_tabels WHERE tablename LIKE :prefix')
                results =await session.execute(list_table,{"prfix":self.pg_vector_table_prefix})
                records = results.scalars().all()
        return records
    
    async def get_collection_info(self, collection_name: str) :
        async with self.db_client as session:
            async with session.begin():
                table_info_sql  = sql_text('SELECT * FROM pg_tabels WHERE tablename = :collection_name')
                count_sql = sql_text('SELECT COUNT(*) FROM :collection_name')
                table_info = session.execute(table_info_sql,{"collection_name":collection_name})
                count = session.execute(count_sql,{"collection_name":collection_name})

                data_info = table_info.fetchone()
                if data_info is None:
                    return None
                return {
                    "table":dict(data_info),
                    "count":count
                }
    
    async def delete_collection(self, collection_name: str) -> None:
        async with self.db_client as session:
            async with session.begin():
                self.logger.info(f"resetting collection {collection_name}")
                await session.execute(sql_text(
                    "DROP TABLE IF EXISTS :collection_name"
                ))
                await session.commit()
        return None
    async def create_collection(self,
                                collection_name: str,
                                embedding_size: int,
                                do_reset: bool = False
                            ) :
        if do_reset:
            _ = await self.delete_collection(collection_name=collection_name)
        is_collection_existed = await self.is_collection_existed(collection_name=collection_name)
        if not is_collection_existed:
            self.logger.info(f"creating collection {collection_name}")
            async with self.db_client as session:
                async with session.begin():
                    create_sql = sql_text(f'CREATE TABLE {collection_name}('f'{PgVectorTableSchemeEnum.ID.value} bigserial PRYMARY KEY'
                                        f'{PgVectorTableSchemeEnum.ID.value} bigserial PRYMARY KEY'
                                        f'{PgVectorTableSchemeEnum.TEXT.value} text'
                                        f'{PgVectorTableSchemeEnum.VECTOR.value} vector {embedding_size}'
                                        f'{PgVectorTableSchemeEnum.METADATA.value} jsonb  DEFAULT \'{{}}\''
                                        f'{PgVectorTableSchemeEnum.CHUNK_ID.value} integer' ')' \
                                        f'FOREIGN KEY ({PgVectorTableSchemeEnum.ID.value}) REFERENCES chunks(chunk_id)'
                                            ')'
                                            )
                    await session.execute(create_sql)
                    await session.commit()
            return True
        
        return False
    async def insert_one(self,collection_name: str,
                        text: str,
                        vector: list,
                        metadata: Optional[Dict] = None,
                        record_id: Optional[str] = None
                    ) :
        is_collection_existed = await self.is_collection_existed(collection_name=collection_name)
        if not is_collection_existed:
            self.logger.error(f"can not insert new record to non-existed collection {collection_name}")
            return False
        if not record_id:
            self.logger.error(f"Can not insert new record with out chunk_id: {collection_name}")
            return False
        
        async with self.db_client as session:
            async with session.begin():
                insert_sql = sql_text(f'INSERT INTO {collection_name}('f'{PgVectorTableSchemeEnum.ID.value} bigserial PRYMARY KEY'
                                        f'({PgVectorTableSchemeEnum.TEXT.value},{PgVectorTableSchemeEnum.VECTOR.value},{PgVectorTableSchemeEnum.METADATA.value},{PgVectorTableSchemeEnum.CHUNK_ID.value}'

                                        'VALUES(:text , :vector , :metadate , :chunk_id)'
                                            )
                await session.execute(insert_sql , {
                    "text":text , "vector": "["+ ",".join([ str(v) for v in vector])+ "]" , "metadate": metadata, "chunk_id":record_id
                })
                await session.commit()
        return True


    async def insert_many(
        self,
        collection_name: str,
        text: List[str],
        vector: List[List[float]],
        metadata: Optional[List[Optional[Dict]]] = None,
        record_id: Optional[List[str]] = None,
        batch_size: int = 50
    ) -> bool:
       
        # 1- validation input
        if not text or not vector:
            self.logger.warning("vectors is null !!")
            return True 
        
        n = len(text)
        if len(vector) != n:
            self.logger.error(f"text({n}) != vector({len(vector)})")
            return False
        
        if record_id is None or len(record_id) != n:
            self.logger.error(f"record_id ={n} ! {len(record_id) if record_id else 'None'})")
            return False
        
        if any(rid is None or rid.strip() == "" for rid in record_id):
            self.logger.error("None  record_id - chunk_id")
            return False
        
        if metadata is None:
            self.logger.error("None  metadata")

            return False
        elif len(metadata) != n:
            self.logger.error(f"   metadata:  {n}، != {len(metadata)}")
            return False

        # 2.   Validation collection 
        if not await self.is_collection_existed(collection_name=collection_name):
            self.logger.error(f"can not insert new records to non-existed collection {collection_name}")
            return False

        # 3.  (transaction)
        try:
            async with self.db_client as session:
                async with session.begin():
                    for start_idx in range(0, n, batch_size):
                        end_idx = min(start_idx + batch_size, n)
                        batch_size_actual = end_idx - start_idx
                        
                        placeholders = []
                        params = {}
                        
                        for i in range(batch_size_actual):
                            global_idx = start_idx + i
                            p_text = f"text_{i}"
                            p_vec = f"vector_{i}"
                            p_meta = f"metadata_{i}"
                            p_id = f"chunk_id_{i}"
                            
                            placeholders.append(
                                f"(:{p_text}, :{p_vec}::vector, :{p_meta}, :{p_id})"
                            )
                            
                            params[p_text] = text[global_idx]
                            params[p_vec] = vector[global_idx]  
                            params[p_meta] = metadata[global_idx]
                            params[p_id] = record_id[global_idx]
                        
                        values_clause = ", ".join(placeholders)
                        insert_sql = sql_text(
                            f'INSERT INTO {collection_name} ('
                            f'{PgVectorTableSchemeEnum.TEXT.value}, '
                            f'{PgVectorTableSchemeEnum.VECTOR.value}, '
                            f'{PgVectorTableSchemeEnum.METADATA.value}, '
                            f'{PgVectorTableSchemeEnum.CHUNK_ID.value}'
                            f') VALUES {values_clause}'
                        )
                        
                        await session.execute(insert_sql, params)
            
            self.logger.info(f"has successfuly inserted {n}  '{collection_name}' in {((n-1)//batch_size)+1} bacth")
            return True
            
        except Exception as e:
            self.logger.exception(f"faild inserted in  '{collection_name}': {str(e)}")
            return False
        
    async def serch_by_vector(self , collection_name : str , vector:list , limit: int):

        is_collection_existed = await self.is_collection_existed(collection_name=collection_name)
        if not is_collection_existed:
            self.logger.error(f"can not serch for records to non-existed collection {collection_name}")
            return False
        vector_str = "["+ ",".join([ str(v) for v in vector])+ "]" 
        async with self.db_client as session:
            async with session.begin():
                search_sql = sql_text(f'SELECT {PgVectorTableSchemeEnum.TEXT.value} as text,1-({PgVectorTableSchemeEnum.VECTOR.value}<=>:vector) as score'
                                      f'FROM {collection_name}'
                                      'ORDER BY score DESC'
                                      f'LIMIT {limit}'
                                            ) 
                results = await session.execute(search_sql , {
                    "vector": vector_str
                })
                records = results.fetchall()

                return [ RetrievedDocument(**{
                
                "score": record.score,
                "text":record.payload["text"], 

            })
            for record in records
            ]
