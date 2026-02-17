from fastapi import FastAPI,APIRouter,Depends,status,Request
from fastapi.responses import JSONResponse
import logging

from routes.schemes.nlp import PushRequest, SerachRequest 
from models.ProjectModel import ProjectModel
from models.DataChunkModel import DataChunkModel
from models.enums.ResponesEnums import ResponseSignal
from controllers import NLPController
from tqdm.auto import tqdm

logger = logging.getLogger("uvicorn.error")

nlp_router = APIRouter(
    prefix="/apiv1/nlp",
    tags= [ "api_v1","nlp"]
)

@nlp_router.post("/index/push/{project_id}")
async def index_project(request : Request,project_id : int , push_requset : PushRequest):

    project_model =await ProjectModel.create_instance(db_client=request.app.db_client)
    project =await project_model.get_project_or_create_one(project_id=project_id)


    data_chunk_model =await DataChunkModel.create_instance(
        db_client = request.app.db_client
    )

    if not project:
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST,content={"signal":ResponseSignal.PROJECT_NOT_FOUND.value })

    nlp_controller = NLPController(
                    embedding_client=request.app.embedding_client,
                    generation_client = request.app.generation_client,
                    vector_db_client= request.app.vectordb_client,
                    template_parser = request.app.template_parser) 
    
    has_record = True
    page_number = 1
    inserted_items_count = 0 

    collection_name = nlp_controller.create_collection_name(project_id=project_id)
    _ = await request.app.vectordb_client.create_collection(collection_name = collection_name ,
                                                             embedding_size =request.app.embedding_client.emmbeding_size,
                                                              do_reset = push_requset.do_reset )
    
    total_chunk = await data_chunk_model.get_total_chunk_count(project_id=project_id)
    pbar = tqdm(total=total_chunk ,desc="vector_indexing",position=0,)
    
    while has_record:
        page_chunks ,_  = await data_chunk_model.get_project_chunks(
            project_id=project.project_id, # type: ignore
            page=page_number
        )

        if not page_chunks:
            has_record = False
            break

        is_inserted =await nlp_controller.index_into_vector_db(
            chunks=page_chunks,
            project=project,
        )

        if not is_inserted:
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={"signal": ResponseSignal.INSERT_INTO_VECTOR_DB_ERROR.value}
            )
        pbar.update(len(page_chunks))
        inserted_items_count += len(page_chunks)
        page_number += 1

        if not is_inserted:
            return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST,content={"signal":ResponseSignal.INSERT_INTO_VECTOR_DB_ERROR.value })
    return JSONResponse(
        content={"signal":ResponseSignal.INSERT_INTO_VECTOR_DB_SUCCESS.value,
                 "no_chunks":inserted_items_count}
    )
@nlp_router.get("/collection/{project_id}")
async def get_collection_info(request : Request,project_id : int):

    project_model =await ProjectModel.create_instance(db_client=request.app.db_client)
    project =await project_model.get_project_or_create_one(project_id=project_id)
    if not project:
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST,content={"signal":ResponseSignal.PROJECT_NOT_FOUND.value })

    nlp_controller = NLPController(
                    embedding_client=request.app.embedding_client,
                    generation_client = request.app.generation_client,
                    vector_db_client= request.app.vectordb_client,
                    template_parser = request.app.template_parser) 
    collection_info =await nlp_controller.get_vector_collection_info(project=project) # type: ignore
    return JSONResponse(
        content={"signal":ResponseSignal.INSERT_INTO_VECTOR_DB_SUCCESS.value,
                 "collection_info":collection_info}
    )

@nlp_router.get("/list/collection/{project_id}")
async def get_list_collection_info(request : Request,project_id : int):

    project_model =await ProjectModel.create_instance(db_client=request.app.db_client)
    project =await project_model.get_project_or_create_one(project_id=project_id)
    if not project:
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST,content={"signal":ResponseSignal.PROJECT_NOT_FOUND.value })
    nlp_controller = NLPController(
                    embedding_client=request.app.embedding_client,
                    generation_client = request.app.generation_client,
                    vector_db_client= request.app.vectordb_client,
                    template_parser = request.app.template_parser) 
    list_collection_info =await nlp_controller.get_list_vector_info() 
    return JSONResponse(
        content={"signal":ResponseSignal.INSERT_INTO_VECTOR_DB_SUCCESS.value,
                 "list_collection_size":(list_collection_info)}
    )
@nlp_router.post("/index/search/{project_id}")
async def index_search(request : Request,project_id : int , search_requset : SerachRequest):

    project_model =await ProjectModel.create_instance(db_client=request.app.db_client)
    project =await project_model.get_project_or_create_one(project_id=project_id)

    if not project:
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST,content={"signal":ResponseSignal.PROJECT_NOT_FOUND.value })

    nlp_controller = NLPController(
                    embedding_client=request.app.embedding_client,
                    generation_client = request.app.generation_client,
                    vector_db_client= request.app.vectordb_client,
                    template_parser = request.app.template_parser) 
    results =await nlp_controller.search_by_vector(project=project,text=search_requset.text,limit=search_requset.limit) # type: ignore
    if not results:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"signal":ResponseSignal.VECTOR_SEARCH_ERROR.value })
    return JSONResponse(
        content={"signal":ResponseSignal.VECTOR_SEARCH_SUCCESS.value,
                 "result":[result.dict() for result in results ]}
    )

@nlp_router.post("/index/answer/{project_id}")
async def answer_rag(request : Request,project_id : int , search_requset : SerachRequest):
    project_model =await ProjectModel.create_instance(db_client=request.app.db_client)
    project =await project_model.get_project_or_create_one(project_id=project_id)

    if not project:
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST,content={"signal":ResponseSignal.PROJECT_NOT_FOUND.value })

    nlp_controller = NLPController(
                    embedding_client=request.app.embedding_client,
                    generation_client = request.app.generation_client,
                    vector_db_client= request.app.vectordb_client,
                    template_parser = request.app.template_parser) 
    
    answer,full_prompt , chat_history =await nlp_controller.answer_rag_question(project=project,query=search_requset.text,limit=search_requset.limit) # type: ignore
    if not answer:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"signal":ResponseSignal.ANSWER_RESPONSE_ERROR.value })
    return JSONResponse(
        content= {
            "signal":ResponseSignal.ANSWER_RESPONSE_SUCCESS.value,
            "answer":answer,
            "full_prompt": full_prompt,
            "chat_history":chat_history

        }
    )