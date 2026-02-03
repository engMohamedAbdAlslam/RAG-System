from helpers import config
from stores.vectoredb.VectorDBInterface import VectorDBInterface
from .providers.QdrantDB import QdrantDB
from typing import Optional
from .VectorDBEnum import VectorDBEnum
from controllers.BaseController import BaseController

class VectorDBProviderFactory:
    def __init__(self, config):
        self.config = config
        self.base_controller = BaseController()

    def create(self, provider: str) -> Optional[VectorDBInterface]:
        db_path = self.base_controller.get_database_path(database_name=self.config.VECTOR_DB_PATH)
        if provider == VectorDBEnum.QDRANT.value:
            return QdrantDB(db_path=db_path,distance_method=self.config.VECTOR_DB_DISTANCE_METHOD)
        return None