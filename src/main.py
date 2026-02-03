from fastapi import FastAPI
from sqlalchemy import URL
from routes import base, data, nlp
# from motor.motor_asyncio import AsyncIOMotorClient # type: ignore
from helpers.config import get_settings
from stores.llm.LLMProviderFactory import LLMProviderFactory
from stores.vectoredb.VectorDBProviderFactory import VectorDBProviderFactory
from stores.llm.tamplates.template_parser import TemplateParser
from sqlalchemy.ext.asyncio import create_async_engine,AsyncSession
from sqlalchemy.orm import sessionmaker

app = FastAPI()


@app.on_event("startup")
async def startup_span():
    settings = get_settings()
    # ===== MongoDB =====
    # app.mongo_conn = AsyncIOMotorClient(settings.MONGODB_URL)  # type: ignore
    # app.db_client = app.mongo_conn[settings.MONGODB_DATABASE]  # type: ignore

    
    # ===== Postgres =====

    database_url = URL.create(
        drivername="postgresql+asyncpg",
        username=settings.POSTGRES_USERNAME,
        password=settings.POSTGRES_PASSWORD,  
        host=settings.POSTGRES_HOST,
        port=settings.POSTGRES_PORT,
        database=settings.POSTGRES_MAIN_DATABASE,
    )
    app.db_engine = create_async_engine( # type: ignore
        database_url,
        echo=True,  # غيّر إلى False في الإنتاج
        pool_pre_ping=True,
        pool_size=10,
        max_overflow=20
    )  

    app.db_client = sessionmaker( # type: ignore
        bind=app.db_engine,   # type: ignore
        class_=AsyncSession,
        expire_on_commit=False
    )


    # ===== Factories =====
    llm_provider_factory = LLMProviderFactory(settings)
    vectordb_provider_factory = VectorDBProviderFactory(config=settings)

    # ===== Generation Client =====
    app.generation_client = llm_provider_factory.create(provider=settings.GENERATION_BACKEND)  # type: ignore

    if app.generation_client is None: # type: ignore
        raise RuntimeError("Generation client was not created")

    app.generation_client.set_generation_model(model_id=settings.GENERATION_MODEL_ID)  # type: ignore

    # ===== Embedding Client =====
    app.embedding_client = llm_provider_factory.create(provider=settings.EMBEDDING_BACKEND)  # type: ignore

    if app.embedding_client is None: # type: ignore
        raise RuntimeError("Embedding client was not created")

    app.embedding_client.set_embedding_model(model_id=settings.EMBEDDING_MODEL_ID, emmbeding_size=settings.EMBEDDING_MODEL_SIZE,)  # type: ignore

    # ===== Vector DB =====
    app.vectordb_client = vectordb_provider_factory.create(provider=settings.VECTOR_DB_BACKEND)  # type: ignore

    if app.vectordb_client is None: # type: ignore
        raise RuntimeError("VectorDB client was not created")

    app.vectordb_client.connect()  # type: ignore

    # ====== Template Parser =====
    app.template_parser = TemplateParser(languge=settings.ORGINAL_LANGUGE,default_languge=settings.DEFAULT_LANGUGE) # type: ignore


@app.on_event("shutdown")
async def shutdown_span():
    # if hasattr(app, "mongo_conn"):
    #     app.mongo_conn.close()  # type: ignore
    app.db_engine.dispose() # type: ignore
    if hasattr(app, "vectordb_client"):
        app.vectordb_client.disconnect()  # type: ignore


# ===== Routers =====
app.include_router(base.base_router)
app.include_router(data.data_router)
app.include_router(nlp.nlp_router)
