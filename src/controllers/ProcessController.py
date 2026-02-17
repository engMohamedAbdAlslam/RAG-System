from .BaseController import BaseController
import os
from .ProjectController import ProjectController
from langchain_community.document_loaders import TextLoader
from langchain_community.document_loaders import PyMuPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from models import ProcessEnum
import re

class ProcessController(BaseController):
    def __init__(self,project_id:int):
        super().__init__()

        self.project_id = project_id
        self.project_path=ProjectController().get_project_path(project_id=project_id)

        
    def normalize_text(self, text: str) -> str: # type: ignore
        # إزالة الأسطر الزائدة
        text = re.sub(r"\n{2,}", " ", text)

        # دمج الأسطر المكسورة
        text = re.sub(r"(?<![.!؟])\n", " ", text)

        # إزالة الفراغات الزائدة
        text = re.sub(r"\s{2,}", " ", text)

        return text.strip()

    def get_file_extension(self,file_id:str):
        return os.path.splitext(file_id)[-1].lower()
    
    def get_file_loader(self, file_id:str):
        file_extension = self.get_file_extension(file_id=file_id)
        file_path=os.path.join(
            self.project_path,
            file_id
        )
        if not os.path.exists (file_path):
            return None 
        if file_extension == ProcessEnum.TXT.value:
            return TextLoader(file_path,encoding = "utf-8")
        if file_extension == ProcessEnum.PDF.value:
            return PyMuPDFLoader(file_path)
        return None
    
    def get_file_content(self, file_id: str):
        loader = self.get_file_loader(file_id=file_id)

        if loader is None:
            raise ValueError(f"Unsupported file type or loader not found for: {file_id}")

        return loader.load()
    
    def process_file_content(
    self,
    file_content: list,
    file_id: str,
    chunk_size: int = 100,
    overlap_size: int = 20
):
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=overlap_size,
            separators=["\n\n", "\n", " ", ""],
            length_function=len
        )

        cleaned_texts = [
            self.normalize_text(rec.page_content)
            for rec in file_content
        ]

        metadatas = [
            rec.metadata
            for rec in file_content
        ]

        chunks = text_splitter.create_documents(
            cleaned_texts,
            metadatas=metadatas
        )

        for chunk in chunks:
            chunk.metadata["file_id"] = file_id

        return chunks
