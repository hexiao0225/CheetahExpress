from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    openai_api_key: str
    yutori_api_key: str
    yutori_base_url: str = "https://api.yutori.com/v1"
    google_maps_api_key: str
    modulate_api_key: str
    modulate_base_url: str = "https://api.modulate.ai/v1"
    neo4j_uri: str = "bolt://localhost:7687"
    neo4j_user: str = "neo4j"
    neo4j_password: str
    port: int = 8000
    log_level: str = "INFO"
    
    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()
