from abc import ABC, abstractmethod
from typing import List, Dict, Optional

class VectorDBInterface(ABC):

    @abstractmethod
    def connect(self) -> None:
        pass

    @abstractmethod
    def disconnect(self) -> None:
        pass

    @abstractmethod
    def is_collection_existed(self, collection_name: str) -> bool:
        pass

    @abstractmethod
    def list_all_collections(self) -> List[str]:
        pass

    @abstractmethod
    def get_collection_info(self, collection_name: str) -> Dict:
        pass

    @abstractmethod
    def delete_collection(self, collection_name: str) -> None:
        pass

    @abstractmethod
    def create_collection(
        self,
        collection_name: str,
        embedding_size: int,
        do_reset: bool = False
    ) -> None:
        pass

    @abstractmethod
    def insert_one(
        self,
        collection_name: str,
        text: str,
        vector: list,
        metadata: Optional[Dict] = None,
        record_id: Optional[str] = None
    ) -> None:
        pass
    @abstractmethod
    def insert_many(
        self,
        collection_name: str,
        text: list,
        vector: list,
        metadata: Optional[list] = None,
        record_id: Optional[list] = None,
        batch_size : int = 50
    ) -> None:
        pass
    @abstractmethod
    def serch_by_vector(self , collection_name : str , vector:list , limit: int):
        pass
