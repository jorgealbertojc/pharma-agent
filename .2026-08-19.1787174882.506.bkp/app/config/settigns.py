from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):

    model_config = SettingsConfigDict(
        env_file = ".env",
        env_file_encoding = "utf-8",
        extra = "ignore"
    )

    ia_model_host: str = "localhost"
    ia_model_embedded_name: str = "gpt40-mini"
    ia_model_agent_name: str = "gpt40-mini"
    ia_model_api_key: str = ""
    ia_model_temperature: float = 0.0

    pinecone_host: str = "localhost"
    pinecone_index_name: str = "lab"
    pinecone_index_dimensions: int = 768
    pinecone_index_metric: str = "cosine"

    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_db_index: int = 0

settings = Settings()
