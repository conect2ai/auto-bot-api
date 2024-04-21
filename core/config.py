import os

from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    """
        Settings class for the API.    
    """

    API_NAME:    str = "Auto Guide API"
    API_VERSION: str = "v0.0.0"

    DB_MILVUS_HOST:       str = os.getenv("DB_MILVUS_HOST")
    DB_MILVUS_PORT:       str = os.getenv("DB_MILVUS_PORT")
    DB_MILVUS_COLLECTION: str = os.getenv("DB_MILVUS_COLLECTION")

    # DB_MILVUS_HOST: str = "localhost"
    # DB_MILVUS_PORT: str = "19530"
    # DB_MILVUS_COLLECTION: str = "api"

    class ConfigDict:
        case_sensitive = True


api_settings = Settings()