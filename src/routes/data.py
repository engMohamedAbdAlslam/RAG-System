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
from models.db__schemes import DataChunk
from bson.objectid import ObjectId


data_router = APIRouter(
    prefix="/api/v1/data",
    tags=["api_v1","data"]

)
 
@data_router.post("/upload/{project_id}")
async def upload_data(request:Request,project_id: str,file:UploadFile,app_settings:Settings = Depends(get_settings)):

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
    file_path,file_id = data_controller.generate_file_name(project_id=project_id,orgin_file_name=file.filename)
    try:
        async with aiofiles.open(file_path,"wb") as f:
            while chunk := await file.read(app_settings.FILE_CHUNK_SIZE):
                await f.write(chunk)
    except Exception as e:
        logger.error(f"error while uploading file: {e} ")
        logging
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                "signal":ResponseSignal.FILE_SIZE_EXCEEDED.value})
    return JSONResponse(content={
                        "signal":ResponseSignal.FILE_UPLOAD_SUCCESS.value,
                        "file_id":file_id
                        })

@data_router.post("/process/{project_id}")
async def process_end_point(request:Request,project_id : str, process_request : ProcessRequest):
    file_id = process_request.file_id
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



    process_controller = ProcessController(project_id=project_id)
    file_content = process_controller.get_file_content(file_id=file_id)
    file_chunks = process_controller.process_file_content(chunk_size=chunck_size,file_content=file_content,file_id=file_id,overlap_size=overlap_size)

    if file_chunks is None or len(file_chunks)==0:
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST,content={
            "signal":ResponseSignal.PROCESSING_FAILD.value
        })

    file_chunks_recoreds=[
        DataChunk(
            chunk_text=chunk.page_content,
            chunk_matadata=chunk.metadata,
            chunk_order=i+1,
            chunk_project_id=ObjectId(project.id)
            )
        for i , chunk in enumerate(file_chunks)
    ]

    if do_reset == 1:
        _ = await chunk_model.delet_chunks_by_project_id(
            project_id=project.id
            )
    else:
        no_recored =await chunk_model.insert_many_chunks(chunks = file_chunks_recoreds)
    return JSONResponse(content = {
        "signal":ResponseSignal.PROCESSING_SUCCESS.value,
        "chunks_add":no_recored
    }
    )