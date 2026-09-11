# app/core/config.py
"""
Application configuration.

Loads environment variables from .env and exposes a global settings instance.
All values are validated by Pydantic and immutable at runtime.
"""

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

from app.core.enums import Environments, LogLevels


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        # Absolute path to .env at the project root (two levels up from app/core)
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        frozen=True,
    )

    # ------------------------------------------------------------
    # Environment and logs
    # ------------------------------------------------------------
    AGENT_ENVIRONMENT: Environments = Environments.DEVELOPMENT
    AGENT_LOG_LEVEL: LogLevels = LogLevels.INFO
    AGENT_NAME: str = "pharma-assistant"

    # ------------------------------------------------------------
    # LLM (generic, applies to any provider)
    # ------------------------------------------------------------
    IA_MODEL_TEMPERATURE: float = 0.0

    # ------------------------------------------------------------
    # DynamoDB (chat history and inventory cache)
    # ------------------------------------------------------------
    # Required table for chat history
    DYNAMODB_CHAT_HISTORY_TABLE: str

    # Required table for inventory cache
    DYNAMODB_INVENTORY_CACHE_TABLE: str

    # Endpoint (default: Floci)
    DYNAMODB_ENDPOINT_URL: str = "http://localhost:4566"

    # AWS region
    DYNAMODB_REGION: str = "us-east-1"

    # Credentials (dummy values for Floci)
    DYNAMODB_ACCESS_KEY_ID: str = "test"
    DYNAMODB_SECRET_ACCESS_KEY: str = "test"

    # ------------------------------------------------------------
    # OpenSearch (vector store for RAG)
    # ------------------------------------------------------------
    OPENSEARCH_HOST: str = "localhost"
    OPENSEARCH_PORT: int = 9400

    # Required index name
    OPENSEARCH_INDEX_NAME: str

    # Required vector dimensions
    OPENSEARCH_INDEX_DIMENSIONS: int

    # Similarity metric (optional)
    OPENSEARCH_INDEX_METRIC: str = "cosine"

    # Credentials (dummy values for Floci)
    OPENSEARCH_ACCESS_KEY_ID: str = "test"
    OPENSEARCH_SECRET_ACCESS_KEY: str = "test"
    OPENSEARCH_REGION: str = "us-east-1"

    # ------------------------------------------------------------
    # Bedrock (LLM and embeddings)
    # ------------------------------------------------------------
    # Required AWS region
    BEDROCK_REGION: str

    # Required model IDs
    BEDROCK_EMBEDDINGS_MODEL: str
    BEDROCK_LLM_MODEL: str

    # Endpoint (default: Floci)
    BEDROCK_ENDPOINT_URL: str = "http://localhost:4566"

    # Credentials (dummy values for Floci)
    BEDROCK_ACCESS_KEY_ID: str = "test"
    BEDROCK_SECRET_ACCESS_KEY: str = "test"

    # ------------------------------------------------------------
    # Google Sheets (inventory source)
    # ------------------------------------------------------------
    GOOGLE_APPLICATION_CREDENTIALS: str = ""
    SPREADSHEET_ID: str = ""

    @classmethod
    def from_env_file(cls, env_file: Path | None = None) -> "Settings":
        """
        Create a Settings instance loading variables from a specific .env file.

        Args:
            env_file: Path to the .env file. If None, uses the default
                      location at the project root.

        Returns:
            Settings instance with variables loaded from the given file.
        """
        if env_file is None:
            env_file = Path(__file__).parent.parent.parent / ".env"
        return cls(_env_file=env_file)


# Global settings instance (loads .env from the project root)
settings = Settings()
