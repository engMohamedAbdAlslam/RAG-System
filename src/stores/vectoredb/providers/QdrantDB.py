from qdrant_client import models ,QdrantClient
from ..VectorDBInterface import VectorDBInterface
from ..VectorDBEnum import VectorDBEnum,DistanceMethodEnum
import logging
from models.db__schemes.minirag.schemes import RetrievedDocument

class QdrantDB(VectorDBInterface):
    def __init__(self,db_path : str ,distance_method  : str):
        self.client = None
        self.db_path = db_path
        if distance_method == DistanceMethodEnum.COSINE:
            self.distance_method = models.Distance.COSINE
        elif distance_method == DistanceMethodEnum.DOT:
            self.distance_method = models.Distance.DOT
        else:
            raise ValueError(f"Unsupported distance method: {distance_method}")


        self.logger = logging.getLogger(__name__)

    def connect(self):
        self.client = QdrantClient(path=self.db_path)
    
    def disconnect(self):
        self.client=None
    def is_collection_existed(self, collection_name: str) -> bool:
        if self.client:
            return self.client.collection_exists(collection_name=collection_name)
        return False
    
    def list_all_collections(self):
        if self.client:
            return self.client.get_collections()
        return []
    def get_collection_info(self, collection_name: str) :
        if self.client:
            return self.client.get_collection(collection_name=collection_name)
        return {}
    def delete_collection(self, collection_name: str) :
        if self.is_collection_existed(collection_name=collection_name) and self.client:
            self.client.delete_collection(collection_name=collection_name)
        return None
    def create_collection(self, collection_name: str, embedding_size: int, do_reset: bool = False) :
        if self.client:
            if do_reset:
                _ = self.delete_collection(collection_name=collection_name)
            if not self.is_collection_existed(collection_name=collection_name):
                _ = self.client.create_collection(collection_name=collection_name , vectors_config=models.VectorParams(size=embedding_size,distance=self.distance_method))
            return True
        return False
    
    def insert_one(self, collection_name: str, text: str, vector: list, metadata: models.Dict = None, record_id: str= None) : # type: ignore
        if self.client:
            if not self.is_collection_existed(collection_name=collection_name):
                self.logger.error("collection is not found so you can not insert")
                return False
            try:
                _ = self.client.upload_records(collection_name=collection_name,records=[
                        models.Record(vector=vector,
                                        payload={"text":text,"metadata":metadata},id = record_id
                                        )
                                        ]
                                        )
            except Exception as e:
                self.logger.error("error while inserting  {e}")     
                return False       
            return True
        return False
    
    def insert_many(self, collection_name: str, texts: list, vectors: list, metadata: list = None, record_ids: list  = None, batch_size: int = 50) : # type: ignore
        if self.client:
            if metadata is None:
                metadata = [None]*len(texts)
            if record_ids is None : 
                record_ids = [None]*len(texts)
            for i in range(0,len(texts),batch_size):
                batch_end = i + batch_size
                batch_texts = texts[i:batch_end]
                batch_vectors = vectors[i:batch_end]
                batch_metadata = metadata[i:batch_end]
                batch_records_ids =record_ids[i:batch_end] 

                batch_records = [
                        models.Record(vector=batch_vectors[x],
                                        payload={"text":batch_texts[x],"metadata":batch_metadata[x]},id = batch_records_ids[x]
                                        )
                    for x in range(len(batch_texts))
                ] 
                try:
                    _ = self.client.upload_records(collection_name=collection_name,records=batch_records)
                except Exception as e:
                    self.logger.error(f"error while inserting batch {e}")
                    return False
            return True
        return False
    
    def serch_by_vector(self, collection_name: str, vector: list, limit: int=5):
        if self.client:
            results = self.client.search(collection_name=collection_name,query_vector=vector,limit=limit)
            if not results or len(results) == 0:
                return None
            return [ RetrievedDocument(**{
                
                "score": result.score,
                "text":result.payload["text"], # type: ignore

            })
            for result in results
            ]
        