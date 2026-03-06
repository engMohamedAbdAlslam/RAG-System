import logging
from models.ChatRepositoryModel import ChatRepositoryModel
from models.db__schemes import Project
from .BaseController import BaseController
from models.db__schemes import Project,DataChunk
from typing import List, Optional
from stores.llm.LLMEnum import DocumentTypeEnum
import json
import uuid
from stores.llm.tamplates.template_parser import TemplateParser


class NLPController(BaseController):
    def __init__(self, db_session, vector_db_client, embedding_client, generation_client, template_parser: TemplateParser):
        super().__init__()
        self.vector_db_client = vector_db_client
        self.embedding_client = embedding_client
        self.generation_client = generation_client
        self.template_parser = template_parser
        self.db_session_factory = db_session
        self.chat_repo = ChatRepositoryModel(db_session)
        self.logger = logging.getLogger(__name__)


    def create_collection_name(self,project_id :int):
        return f"collection_{self.vector_db_client.default_vector_size}_{project_id}".strip()
    
    async def reset_vectordb_collection(self,project :Project ):
        collection_name = self.create_collection_name(project_id=project.project_id) # type: ignore
        return await self.vector_db_client.delete_collection(collection_name = collection_name)
    
    async def search_by_vector(self,text : str ,project :Project, limit:int=5 ):

        # text embbeding
        embbeding_text = self.embedding_client.emmbed_text(text = text , document_type =DocumentTypeEnum.QUERY.value )
        if len(embbeding_text) == 0:
            return False
        query_embbeding = None

        if isinstance(embbeding_text,list) and len(embbeding_text)>0:
            query_embbeding = embbeding_text[0]

        if not query_embbeding:
            return False
        # get collection name
        collection_name = self.create_collection_name(project_id=project.project_id) # type: ignore
        # search by vector
        results  = await self.vector_db_client.serch_by_vector(collection_name=collection_name,limit=limit,vector=query_embbeding)
        if not results:
            return False
        return results
    
    async def get_vector_collection_info(self,project :Project):
        collection_name = self.create_collection_name(project_id=project.project_id) # type: ignore
        print("GET COLLECTION:", collection_name)

        collection_info = await self.vector_db_client.get_collection_info(collection_name=collection_name)
        return json.loads(
            json.dumps(collection_info,default =lambda x : x.__dict__)
        )
    
    async def get_list_vector_info(self,):
        list_collection = await self.vector_db_client.list_all_collections()
        return json.loads(
            json.dumps(list_collection,default =lambda x : x.__dict__)
        )


    async def index_into_vector_db(self , project :Project , chunks : List[DataChunk],do_reset :bool =False,):
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
            chunk_id = chunk.chunk_id
            generated_id = chunk_id
            record_ids.append(generated_id)

        batch_size= 50
        vectors =  self.embedding_client.emmbed_text(text=texts , document_type= DocumentTypeEnum.DOCUMENT.value )
        

        ## step 3 create collection 
        await self.vector_db_client.create_collection(collection_name=collection_name,embedding_size=self.embedding_client.emmbeding_size,do_reset=do_reset)

        ## step 4 insert into vector DB 
        success =await self.vector_db_client.insert_many(batch_size=batch_size,collection_name=collection_name,metadata=metadata,vector=vectors,text=texts,record_id=record_ids)


        return success


    async def answer_rag_question_rewrite_query(self, project: Project, query: str, session_uuid: uuid.UUID, limit: int = 5,context_window: int = 5):
        # 1. جلب التاريخ الخام والـ System Prompt
        db_messages  = await self.chat_repo.get_session_history(session_uuid)
        system_prompt = self.template_parser.get(group="rag", key="system_prompt")
        
        # 2. تحويل التاريخ لتنسيق الموديل (Dynamic Format)
        chat_history = self.generation_client.format_history(db_messages, system_prompt)

        # 3. خطوة إعادة صياغة السؤال (Query Re-writing)
        # نطلب من الموديل صياغة سؤال مستقل بناءً على المحادثة
         
        rephrase_history = chat_history[-context_window:] if len(chat_history) > context_window else chat_history
        rephrase_vars = {"query": query}
        rephrase_instruction = self.template_parser.get(group="rag", key="rephrase_prompt", vars=rephrase_vars)
        
        # نرسل التاريخ مع الطلب الجديد للحصول على سؤال "نظيف" للبحث
        try:
            search_query = self.generation_client.generate_text(prompt=rephrase_instruction, chat_history=rephrase_history)
        except Exception as e:
            search_query = query
            self.logger.error(f"Generation failed: {e}")
        search_query = search_query if search_query else query #  في حال فشل التوليد
        self.logger.info(f"search query = : {search_query}")

        retrived_doc = await self.search_by_vector(project=project, text=search_query, limit=limit)
        
        if not retrived_doc:
            return "Sorry, I couldn't find relevant information.", None, chat_history,session_uuid

        document_prompt = "\n".join([
            self.template_parser.get(group="rag", key="document_prompt", 
                vars={"doc_num": idx + 1, "chunk_text": doc.text}) or ""
            for idx, doc in enumerate(retrived_doc)
        ])
        
        footer_prompt = self.template_parser.get(group="rag", key="footer_prompt", vars={"query": query})
        full_prompt = "\n\n".join([document_prompt, footer_prompt or ""])

        # 6. توليد الإجابة النهائية
        answer = self.generation_client.generate_text(prompt=full_prompt, chat_history=chat_history)

        await self.chat_repo.save_chat_message(session_uuid, "user", query)
        await self.chat_repo.save_chat_message(session_uuid, "assistant", answer)

        chat_history.append(self.generation_client.construct_prompt(prompt=query, role="user"))
        chat_history.append(self.generation_client.construct_prompt(prompt=answer, role="assistant"))

        return answer, full_prompt, chat_history , session_uuid