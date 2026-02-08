from fastapi import FastAPI,APIRouter,UploadFile,Depends,status,Request
from fastapi.responses import JSONResponse
import aiofiles
import os
from models import ResponseSignal
from helpers.config import get_settings,Settings
from controllers import DataController,ProjectController,ProcessController
import logging
from .schemes.data import ProcessRequest
logger = logging.getLogger('uvicorn.error')
from models.ProjectModel import ProjectModel
from models.DataChunkModel import DataChunkModel
from models.AssetModel import AssetModel
from models.db__schemes import DataChunk,Asset
from models.enums.AssetEnum import AssetEnum
from controllers import NLPController

data_router = APIRouter(
    prefix="/api/v1/data",
    tags=["api_v1","data"]

)
 
@data_router.post("/upload/{project_id}")
async def upload_data(request:Request,project_id: int ,file:UploadFile,app_settings:Settings = Depends(get_settings)):

    project_model=await ProjectModel.create_instance(db_client=
                               request.app.db_client)
    project =await project_model.get_project_or_create_one(project_id=project_id)
    # validate file
    data_controller = DataController()
    is_valid,signal = data_controller.validate_upload_file(file=file)

    if not is_valid:
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST
                            ,content={"signal":signal})
    
    project_controller = ProjectController()
    project_dir_path = project_controller.get_project_path(project_id=project_id)
    file_path,file_id = data_controller.generate_file_name(project_id=project_id,orgin_file_name=file.filename) # type: ignore
    try:
        async with aiofiles.open(file_path,"wb") as f:
            while chunk := await file.read(app_settings.FILE_CHUNK_SIZE):
                await f.write(chunk)
    except Exception as e:
        logger.error(f"error while uploading file: {e} ")
        logging # type: ignore

        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                "signal":ResponseSignal.FILE_SIZE_EXCEEDED.value})

    asset_model =await AssetModel.create_instance(db_client=request.app.db_client)
    asset_resource = Asset(
        asset_name = file_id,
        asset_type = AssetEnum.FILE.value ,
        asset_size = os.path.getsize(file_path),
        asset_project_id = project.project_id
 
    ) # type: ignore
    asset_recored = await asset_model.create_asset(asset=asset_resource)

    return JSONResponse(content={
                        "signal":ResponseSignal.FILE_UPLOAD_SUCCESS.value,
                        "file_id":str(asset_recored.asset_id)
                        })

@data_router.post("/process/{project_id}")
async def process_end_point(request:Request,project_id : int , process_request : ProcessRequest):
    # file_id = process_request.file_id
    chunck_size=process_request.chunck_size
    overlap_size =process_request.overlap_size
    do_reset= process_request.do_reset
    no_recored=0

    project_model =await ProjectModel.create_instance(
    db_client=request.app.db_client)
    
    project = await project_model.get_project_or_create_one(project_id=project_id)

    chunk_model =await DataChunkModel.create_instance(
        db_client = request.app.db_client
    )


    asset_model =await AssetModel.create_instance(
            db_client=request.app.db_client)
    
    nlp_controller = NLPController(embedding_client=request.app.vectordb_client,
                                   generation_client=request.app.generation_client,
                                   template_parser=request.app.template_parser,
                                   vector_db_client=request.app.vectordb_client)
    project_file_ids = {}
    
    if process_request.file_id:
        asset_record =await asset_model.get_asset_record(asset_project_id=project.project_id,asset_name=process_request.file_id) # type: ignore

        if asset_record is None:
            return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST,
            content={
                "signal":ResponseSignal.FILE_NO_FOUND_ID.value
            })

        project_file_ids={asset_record.asset_id:asset_record.asset_name}

    else:

 
        project_files = await asset_model.get_all_project_assets(
            asset_project_id=project.project_id,asset_type=AssetEnum.FILE.value) # type: ignore

        project_file_ids={
            record.asset_id:record.asset_name
            for record in project_files
        }

        if len(project_file_ids)==0:
            return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST,content={
                "signal":ResponseSignal.NO_FILE_ERROES.value
            })
    process_controller = ProcessController(project_id=project_id)

    if do_reset == 1:
        collection_name = nlp_controller.create_collection_name(project_id=project_id)
        _ = await request.app.vectordb_client.delete_collection(collection_name)
        _ = await chunk_model.delete_chunks_by_project_id(
        project_id=project.project_id # type: ignore
        )
    no_recored =0
    no_files = 0
    for asset_id,file_id in project_file_ids.items():
        file_content = process_controller.get_file_content(file_id=file_id)
        if file_content is None:
            logger.error(f"error while processing {file_id}")
            continue
        file_chunks = process_controller.process_file_content(chunk_size=chunck_size,file_content=file_content,file_id=file_id,overlap_size=overlap_size) # type: ignore

        if file_chunks is None or len(file_chunks)==0:
            return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST,content={
                "signal":ResponseSignal.PROCESSING_FAILD.value
            })

        file_chunks_recoreds=[
            DataChunk(
                chunk_text=chunk.page_content,
                chunk_metadata=chunk.metadata,
                chunk_order=i+1,
                chunk_project_id=project.project_id,
                chunk_asset_id = asset_id
                ) # type: ignore
            for i , chunk in enumerate(file_chunks)
        ]

        no_recored +=await chunk_model.insert_many_chunks(chunks = file_chunks_recoreds)
        no_files += 1
    return JSONResponse(content = {
        "signal":ResponseSignal.PROCESSING_SUCCESS.value,
        "chunks_add":no_recored,
        "processed_files_number":no_files
    }
    )