import os
from helpers.config import get_settings,Settings
from fastapi import FastAPI,APIRouter,Depends
base_router = APIRouter(
    prefix="/api/v1",
    tags=["api_v1"]
)

@base_router.get("/")
async def welcom(app_settings : Settings = Depends(get_settings)):
    # app_settings = get_settings()
    app_name = app_settings.APP_NAME
    app_version = app_settings.APP_VERSION
    return{
        "app_name":app_name,
        "app_version":app_version
                }