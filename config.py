from pydantic_settings import BaseSettings
from typing import Optional
from pathlib import Path


class Settings(BaseSettings):
    openai_api_key: str
    google_maps_api_key: str
    modulate_api_key: str
    modulate_base_url: str = "https://modulate-developer-apis.com"
    neo4j_uri: str = "bolt://localhost:7687"
    neo4j_user: str = "neo4j"
    neo4j_password: str
    port: int = 8000
    log_level: str = "INFO"
    use_mock_data: bool = True
    
    class Config:
        env_file = str(Path(__file__).resolve().parent / ".env")
        case_sensitive = False
        extra = "ignore"


settings = Settings()
