from openai import chat
from models.db__schemes import Project
from stores.vectoredb.providers.QdrantDB import QdrantDB
from .BaseController import BaseController
from models.db__schemes import Project,DataChunk
from typing import List, Optional
from stores.llm.LLMEnum import DocumentTypeEnum
import json
import uuid
from stores.llm.tamplates.template_parser import TemplateParser



class NLPController(BaseController):
    def __init__(self,vectordb_client: QdrantDB,embedding_client,generation_client,template_parser:TemplateParser):
        super().__init__()

        self.vectordb_client = vectordb_client
        self.embedding_client = embedding_client
        self.generation_client = generation_client
        self.template_parser = template_parser

    def create_collection_name(self,project_id :int):
        return f"collection_{project_id}".strip()
    
    def reset_vectordb_collection(self,project :Project ):
        collection_name = self.create_collection_name(project_id=project.project_id) # type: ignore
        return self.vectordb_client.delete_collection(collection_name = collection_name)
    
    def search_by_vector(self,text : str ,project :Project, limit:int=5 ):

        # text embbeding
        embbeding_text = self.embedding_client.emmbed_text(text = text , document_type =DocumentTypeEnum.QUERY.value )
        if len(embbeding_text) == 0:
            return False
        # get collection name
        collection_name = self.create_collection_name(project_id=project.project_id) # type: ignore
        # search by vector
        result  = self.vectordb_client.serch_by_vector(collection_name=collection_name,limit=limit,vector=embbeding_text)
        if not result:
            return False
        return result
    
    def get_vector_collection_info(self,project :Project):
        collection_name = self.create_collection_name(project_id=project.project_id) # type: ignore
        print("GET COLLECTION:", collection_name)

        collection_info = self.vectordb_client.get_collection_info(collection_name=collection_name)
        return json.loads(
            json.dumps(collection_info,default =lambda x : x.__dict__)
        )
    
    def get_list_vector_info(self,):
        list_collection = self.vectordb_client.list_all_collections()
        return json.loads(
            json.dumps(list_collection,default =lambda x : x.__dict__)
        )


    def index_into_vector_db(self , project :Project , chunks : List[DataChunk],do_reset :bool =False,):
        ## step 1 get collection name
        collection_name = self.create_collection_name(project_id=project.project_id) # type: ignore
        print("CREATE COLLECTION:", collection_name)


        ## step 2 mange item
        texts = [

           chunk.chunk_text for chunk in chunks
        ]
        metadata=[

           chunk.chunk_metadata for chunk in chunks
        ]
        record_ids = []
        for chunk in chunks:
            mongo_id = str(chunk.chunk_id)
            generated_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, mongo_id))
            record_ids.append(generated_id)

        batch_size= 50
        vecrtors = [
            self.embedding_client.emmbed_text(text=text , document_type= DocumentTypeEnum.DOCUMENT.value )
            for text in texts
        ]

        ## step 3 create collection 
        self.vectordb_client.create_collection(collection_name=collection_name,embedding_size=self.embedding_client.emmbeding_size,do_reset=do_reset)

        ## step 4 insert into vector DB 
        success = self.vectordb_client.insert_many(batch_size=batch_size,collection_name=collection_name,metadata=metadata,vectors=vecrtors,texts=texts,record_ids=record_ids)


        return success
    
    def answer_rag_question(self, project :Project , query:str , limit: int = 5):
        retrived_doc = self.search_by_vector(project=project,text=query,limit=limit)
        if not retrived_doc or len(retrived_doc)==0:
            return None

        system_prompt = self.template_parser.get(group="rag" , key= "system_prompt",vars={})

        document_prompt = "\n".join(
            self.template_parser.get(
                group="rag",
                key="document_prompt",
                vars={
                    "doc_num": idx + 1,
                    "chunk_text": self.generation_client.process_text(doc.text)
                }
            ) or ""
            for idx, doc in enumerate(retrived_doc)
        )
        footer_prompt = self.template_parser.get(group="rag" , key= "footer_prompt",vars={"query":query})
        chat_history= [
            self.generation_client.construct_prompt( prompt = system_prompt , role  = self.generation_client.enums.SYSTEM.value)

        ]
        full_prompt = "\n\n".join([document_prompt , footer_prompt or ""])

        answer = self.generation_client.generate_text(prompt= full_prompt, chat_history = chat_history )
        return answer , full_prompt , chat_history
