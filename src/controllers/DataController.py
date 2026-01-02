from .BaseController import BaseController
from .ProjectController import ProjectController
from fastapi import UploadFile
from models import ResponseSignal
import re
import os
class DataController(BaseController):
    def __init__(self):
        super().__init__()

    def validate_upload_file(self,file:UploadFile):
        self.size_scale = 1024*1024 # MB to Bytes
        if file.content_type not in self.app_settings.FILE_ALLOWED_TYPES:

            return False,ResponseSignal.FILE_TYPE_NOT_SUPPORTED.value
        
        file.file.seek(0, 2) 
        size = file.file.tell()
        file.file.seek(0)    

        if size > self.app_settings.FILE_MAX_SIZE * self.size_scale:
            return False,ResponseSignal.FILE_SIZE_EXCEEDED.value
        return True,ResponseSignal.FILL_VALIDATED_SUCCESS.value
    

    def generate_file_name(self,orgin_file_name:str,project_id:str):
        random_key = self.generate_random_string()

        project_path = ProjectController().get_project_path(project_id=project_id)
        
        cleaned_file_name = self.clean_file_name(original_file_name=orgin_file_name)

        new_file_path=os.path.join(project_path,random_key+"_"+ cleaned_file_name)
        while os.path.exists(new_file_path):
            random_key = self.generate_random_string()
            new_file_path =os.path.join(project_path,random_key+"_"+ cleaned_file_name)


        return new_file_path,random_key+"_"+ cleaned_file_name


    def clean_file_name(self,original_file_name:str):
        # remove any special character  except . and underscore
        cleaned_file_name =re.sub(r'[^\w.]', '',original_file_name.strip())

        cleaned_file_name = cleaned_file_name.replace(" ","_")

        return cleaned_file_name