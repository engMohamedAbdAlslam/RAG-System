from typing import Optional, List
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    APP_NAME: str
    APP_VERSION: str

    FILE_ALLOWED_TYPES: List[str] = []
    FILE_MAX_SIZE: int
    FILE_CHUNK_SIZE: int

    # MONGODB_URL: str
    # MONGODB_DATABASE: str

    POSTGRES_USERNAME:str
    POSTGRES_PASSWORD:str
    POSTGRES_HOST:str
    POSTGRES_PORT:int
    POSTGRES_MAIN_DATABASE:str
    
    
    GENERATION_BACKEND: str
    EMBEDDING_BACKEND: str

    OPENAI_API_KEY: Optional[str] = None
    OPENAI_API_URL: Optional[str] = None
    COHERE_API_KEY: Optional[str] = None

    GENERATION_MODEL_ID: Optional[str] = None
    EMBEDDING_MODEL_ID: Optional[str] = None
    EMBEDDING_MODEL_SIZE: Optional[int] = None
    INPUT_DAFAULT_MAX_CHARACTERS: Optional[int] = None
    GENERATION_DAFAULT_MAX_TOKENS: Optional[int] = None
    GENERATION_DAFAULT_TEMPERATURE: Optional[float] = None


    VECTOR_DB_BACKEND_LITERAL : List[str] = None
    VECTOR_DB_BACKEND : Optional[str] = None
    VECTOR_DB_PATH : Optional[str] = None
    VECTOR_DB_DISTANCE_METHOD : Optional[str] = None

    ORGINAL_LANGUGE :str = "en"
    DEFAULT_LANGUGE :str = "en"


    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8"
    )

def get_settings():
    return Settings() # type: ignore
