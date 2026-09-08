from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict
from app.core.enums import Environments, IndexMetric, LogLevels


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        # Ruta absoluta al .env en la raíz del proyecto (dos niveles arriba de src/core)
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        frozen=True,
    )

    # ------------------------------------------------------------
    # Entorno y logs
    # ------------------------------------------------------------
    AGENT_ENVIRONMENT: Environments = Environments.DEVELOPMENT
    AGENT_LOG_LEVEL: LogLevels = LogLevels.INFO
    AGENT_NAME: str = "pharma-assistant"

    # ------------------------------------------------------------
    # Ollama / Modelos
    # ------------------------------------------------------------
    IA_MODEL_HOST: str = "localhost"
    IA_MODEL_EMBEDDED_NAME: str = "gpt4o-mini"
    IA_MODEL_AGENT_NAME: str = "gpt4o-mini"
    IA_MODEL_API_KEY: str = ""              # Ollama no requiere, pero se deja por compatibilidad
    IA_MODEL_TEMPERATURE: float = 0.0

    # ------------------------------------------------------------
    # Pinecone
    # ------------------------------------------------------------
    PINECONE_HOST: str = "localhost"
    PINECONE_INDEX_NAME: str = "lab"
    PINECONE_INDEX_DIMENSIONS: int = 768
    PINECONE_INDEX_METRIC: IndexMetric = IndexMetric.COSINE
    PINECONE_API_KEY: str = "pclocal"

    # ------------------------------------------------------------
    # Redis
    # ------------------------------------------------------------
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB_INDEX: int = 0
    REDIS_TTL_SECONDS: int | None = None    # None = sin expiración

    # ------------------------------------------------------------
    # DynamoDB (reemplazo de Redis)
    # ------------------------------------------------------------
    # Tabla para historial de conversaciones (obligatoria)
    DYNAMODB_CHAT_HISTORY_TABLE: str

    # Tabla para caché de inventario (obligatoria)
    DYNAMODB_INVENTORY_CACHE_TABLE: str

    # Endpoint de DynamoDB (con valor por defecto para Floci)
    DYNAMODB_ENDPOINT_URL: str = "http://localhost:4566"

    # Región de AWS (con valor por defecto para Floci)
    DYNAMODB_REGION: str = "us-east-1"

    # Credenciales dummy para Floci (con valor por defecto)
    DYNAMODB_ACCESS_KEY_ID: str = "test"
    DYNAMODB_SECRET_ACCESS_KEY: str = "test"

    # ------------------------------------------------------------
    # OpenSearch (reemplazo de Pinecone)
    # ------------------------------------------------------------
    # Host y puerto de OpenSearch
    OPENSEARCH_HOST: str = "localhost"
    OPENSEARCH_PORT: int = 4566

    # Índice de vectores (obligatorio)
    OPENSEARCH_INDEX_NAME: str

    # Dimensión de los vectores (obligatorio)
    OPENSEARCH_INDEX_DIMENSIONS: int

    # Métrica de similitud (opcional, con valor por defecto)
    OPENSEARCH_INDEX_METRIC: str = "cosine"

    # Credenciales para OpenSearch (opcional, para Floci)
    OPENSEARCH_ACCESS_KEY_ID: str = "test"
    OPENSEARCH_SECRET_ACCESS_KEY: str = "test"
    OPENSEARCH_REGION: str = "us-east-1"

    # ------------------------------------------------------------
    # Google Sheets (Inventario)
    # ------------------------------------------------------------
    GOOGLE_APPLICATION_CREDENTIALS: str = ""  # Ruta al archivo JSON de la cuenta de servicio
    SPREADSHEET_ID: str = ""                  # ID del documento de Google Sheets

    @classmethod
    def from_env_file(cls, env_file: Path | None = None) -> "Settings":
        """
        Crea una instancia de Settings cargando variables desde un archivo .env específico.

        Args:
            env_file: Ruta al archivo .env. Si es None, se usa la ruta por defecto (raíz del proyecto).

        Returns:
            Instancia de Settings con las variables del archivo indicado.

        Uso:
            # Para tests con archivo vacío o temporal
            settings = Settings.from_env_file(Path("/dev/null"))

            # Para usar un .env alternativo
            settings = Settings.from_env_file(Path("config/test.env"))
        """
        if env_file is None:
            env_file = Path(__file__).parent.parent.parent / ".env"
        return cls(_env_file=env_file)


# Instancia global por defecto (carga el .env de la raíz del proyecto)
settings = Settings()
