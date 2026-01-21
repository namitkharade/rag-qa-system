from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    openai_api_key: str = ""
    backend_host: str = "0.0.0.0"
    backend_port: int = 8000
    chroma_host: str = "localhost"
    chroma_port: int = 8001
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_db: int = 0
    agent_host: str = "localhost"
    agent_port: int = 8002
    
    class Config:
        env_file = ".env"


settings = Settings()
