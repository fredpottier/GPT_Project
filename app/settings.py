from pydantic_settings import BaseSettings
from pydantic import Field

class Settings(BaseSettings):
    # LLM
    openai_api_key: str = Field(..., env="OPENAI_API_KEY")

    # App
    app_port: int = Field(5173, env="APP_PORT")
    app_api_key: str = Field(..., env="APP_API_KEY")

    # Zep
    zep_api_url: str = Field("http://zep:8000", env="ZEP_API_URL")
    zep_api_key: str = Field("dev", env="ZEP_API_KEY")

    # Qdrant
    qdrant_url: str = Field("http://qdrant:6333", env="QDRANT_URL")
    qdrant_collection: str = Field("project_docs", env="QDRANT_COLLECTION")

    # Projects registry (JSON)
    projects_file: str = Field("/data/projects.json", env="PROJECTS_FILE")

settings = Settings()
