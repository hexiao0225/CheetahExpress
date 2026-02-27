from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # OpenAI
    openai_api_key: str

    # Yutori
    yutori_api_key: str
    yutori_base_url: str = "https://api.yutori.io/v1"

    # Google Maps
    google_maps_api_key: str

    # Modulate
    modulate_api_key: str
    modulate_base_url: str = "https://api.modulate.ai/v1"
    modulate_caller_number: str

    # App
    webhook_base_url: str
    port: int = 8000
    log_level: str = "INFO"

    # Neo4j
    neo4j_uri: str
    neo4j_username: str = "neo4j"
    neo4j_password: str
    neo4j_database: str = "neo4j"

    model_config = {"env_file": ".env", "case_sensitive": False}


settings = Settings()
