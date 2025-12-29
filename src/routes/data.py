from fastapi import FastAPI,APIRouter,UploadFile,Depends,status
from fastapi.responses import JSONResponse
import aiofiles
import os
from models import ResponseSignal
from helpers.config import get_settings,Settings
from controllers import DataController,ProjectController,ProcessController
import logging
from .schemes.data import ProcessRequest
logger = logging.getLogger('uvicorn.error')

data_router = APIRouter(
    prefix="/api/v1/data",
    tags=["api_v1","data"]

)
@data_router.post("/upload/{project_id}")
async def upload_data(project_id: str,file:UploadFile,app_settings:Settings = Depends(get_settings)):


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
                        "file_id":file_id})

@data_router.post("/process/{project_id}")
async def process_end_point(project_id : str, process_request : ProcessRequest):
    file_id = process_request.file_id
    chunck_size=process_request.chunck_size
    overlap_size =process_request.overlap_size
    do_reset= process_request.do_reset
    process_controller = ProcessController(project_id=project_id)
    file_content = process_controller.get_file_content(file_id=file_id)
    file_chunks = process_controller.process_file_content(chunk_size=chunck_size,file_content=file_content,file_id=file_id,overlap_size=overlap_size)

    if file_chunks is None or len(file_chunks)==0:
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST,content={
            "signal":ResponseSignal.PROCESSING_FAILD.value
        })
    return file_chunks