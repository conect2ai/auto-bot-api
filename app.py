import uvicorn
from fastapi import FastAPI
from core.config import api_settings

from routers.application import chat

from pymilvus import connections
from contextlib import asynccontextmanager

from utils.logger import setup_logger

# Setup logger
logger = setup_logger("api.log")

@asynccontextmanager
async def connect_to_milvus(app: FastAPI):

    logger.info("Connecting to Milvus")
    con = connections.connect(
        host=api_settings.DB_MILVUS_HOST,
        port=api_settings.DB_MILVUS_PORT
    )

    logger.info("Milvus connected!")

    try:
        logger.info("Persising connection to Milvus")
        yield con
    finally:
        logger.info("Disconnecting from Milvus")
        connections.disconnect()


app = FastAPI(
    title=api_settings.API_NAME,
    version=api_settings.API_VERSION,
    description="""
    This FastAPI application serves as a versatile backend for an interactive chatbot, capable of transcribing user-submitted audio messages into text for dynamic query processing. Leveraging state-of-the-art machine learning models, it interprets and extracts content from uploaded audio files, facilitating a natural and accessible user experience. Furthermore, the application can access and consult a knowledge base of automotive manuals, allowing for precise, context-aware responses to user inquiries. It supports comprehensive search capabilities across indexed documents in the knowledge base, enriching the conversational interface with reliable and detailed automotive data. Additional features include the generation of PDF exports of chat histories, image processing for enriched visual context in conversations, and robust management endpoints for maintaining the underlying knowledge base.
    """,
    lifespan=connect_to_milvus,
)

app.include_router(chat.router)


if __name__ == "__main__":
    uvicorn.run(
        app="app:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
