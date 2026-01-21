from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    openai_api_key: str
    langchain_api_key: str = ""
    langchain_tracing_v2: bool = False
    langchain_project: str = "hybrid-rag"
    chroma_host: str = "localhost"
    chroma_port: int = 8001
    chroma_collection_name: str = "regulatory_documents"
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_db: int = 0
    
    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()
