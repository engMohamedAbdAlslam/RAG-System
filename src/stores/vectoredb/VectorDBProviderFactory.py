from helpers import config
from stores.vectoredb.VectorDBInterface import VectorDBInterface
from .providers import QdrantDB,PgVectorProvider
from typing import Optional
from .VectorDBEnum import VectorDBEnum
from controllers.BaseController import BaseController
from sqlalchemy.orm import sessionmaker
class VectorDBProviderFactory:
    def __init__(self, config,db_client : sessionmaker|None):
        self.config = config
        self.db_client= db_client
        self.base_controller = BaseController()

    def create(self, provider: str) -> Optional[VectorDBInterface]:
        if provider == VectorDBEnum.QDRANT.value:
            qdrant_db_client = self.base_controller.get_database_path(database_name=self.config.VECTOR_DB_PATH)
            if provider == VectorDBEnum.QDRANT.value:
                return QdrantDB(db_client=qdrant_db_client,
                                distance_method=self.config.VECTOR_DB_DISTANCE_METHOD,
                                default_vector_size=self.config.EMBEDDING_MODEL_SIZE)
        
        if provider == VectorDBEnum.PGVECTOR.value:
                return PgVectorProvider(db_client=self.db_client,
                                        distance_method=self.config.VECTOR_DB_DISTANCE_METHOD,
                                        default_vector_size=self.config.EMBEDDING_MODEL_SIZE,
                                        index_threshold=self.config.VECTOR_DB_INDEX_THRESHOLD)
       
        return None