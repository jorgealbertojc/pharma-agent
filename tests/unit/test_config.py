# tests/unit/test_config.py
"""
Tests unitarios para la configuración de la aplicación.

Verifica que:
- Los valores por defecto se usan cuando no hay variables de entorno.
- Las variables válidas se cargan correctamente.
- Las variables inválidas lanzan ValidationError.
"""

import pytest
import time
from pathlib import Path

from pydantic import ValidationError

from src.core.config import Settings
from src.core.enums import Environments, LogLevels, IndexMetric


class TestConfig:
    """Suite de tests para la configuración."""

    def test_default_values_when_env_empty(self, monkeypatch):
        """1. Archivo .env vacío: deben usarse los valores por defecto."""
        # Eliminar todas las variables de entorno relevantes
        env_vars = [
            "AGENT_ENVIRONMENT",
            "AGENT_LOG_LEVEL",
            "AGENT_NAME",
            "IA_MODEL_HOST",
            "IA_MODEL_EMBEDDED_NAME",
            "IA_MODEL_AGENT_NAME",
            "IA_MODEL_API_KEY",
            "IA_MODEL_TEMPERATURE",
            "PINECONE_HOST",
            "PINECONE_INDEX_NAME",
            "PINECONE_INDEX_DIMENSIONS",
            "PINECONE_INDEX_METRIC",
            "REDIS_HOST",
            "REDIS_PORT",
            "REDIS_DB_INDEX",
            "REDIS_TTL_SECONDS",
        ]
        for var in env_vars:
            monkeypatch.delenv(var, raising=False)

        # crea archivo temporal vacío
        empty_env = create_empty_env_file()

        # Instanciar Settings (no debe leer .env, solo el entorno vacío)
        settings = Settings().from_env_file(env_file = empty_env)

        # Verificar valores por defecto
        assert settings.AGENT_ENVIRONMENT == Environments.DEVELOPMENT
        assert settings.AGENT_LOG_LEVEL == LogLevels.INFO
        assert settings.AGENT_NAME == "pharma-assistant"
        assert settings.IA_MODEL_HOST == "localhost"
        assert settings.IA_MODEL_EMBEDDED_NAME == "gpt4o-mini"
        assert settings.IA_MODEL_AGENT_NAME == "gpt4o-mini"
        assert settings.IA_MODEL_API_KEY == ""
        assert settings.IA_MODEL_TEMPERATURE == 0.0
        assert settings.PINECONE_HOST == "localhost"
        assert settings.PINECONE_INDEX_NAME == "lab"
        assert settings.PINECONE_INDEX_DIMENSIONS == 768
        assert settings.PINECONE_INDEX_METRIC == IndexMetric.COSINE
        assert settings.REDIS_HOST == "localhost"
        assert settings.REDIS_PORT == 6379
        assert settings.REDIS_DB_INDEX == 0
        assert settings.REDIS_TTL_SECONDS is None

    def test_valid_values_from_env(self, monkeypatch):
        """2. Todas las variables de entorno son válidas."""
        monkeypatch.setenv("AGENT_ENVIRONMENT", "production")
        monkeypatch.setenv("AGENT_LOG_LEVEL", "ERROR")
        monkeypatch.setenv("AGENT_NAME", "custom-agent")
        monkeypatch.setenv("IA_MODEL_HOST", "http://ollama:11434")
        monkeypatch.setenv("IA_MODEL_EMBEDDED_NAME", "custom-embed")
        monkeypatch.setenv("IA_MODEL_AGENT_NAME", "custom-model")
        monkeypatch.setenv("IA_MODEL_API_KEY", "sk-test")
        monkeypatch.setenv("IA_MODEL_TEMPERATURE", "0.7")
        monkeypatch.setenv("PINECONE_HOST", "http://pinecone:5081")
        monkeypatch.setenv("PINECONE_INDEX_NAME", "production-index")
        monkeypatch.setenv("PINECONE_INDEX_DIMENSIONS", "1024")
        monkeypatch.setenv("PINECONE_INDEX_METRIC", "euclidean")
        monkeypatch.setenv("REDIS_HOST", "redis-prod")
        monkeypatch.setenv("REDIS_PORT", "6380")
        monkeypatch.setenv("REDIS_DB_INDEX", "2")
        monkeypatch.setenv("REDIS_TTL_SECONDS", "3600")

        settings = Settings()

        assert settings.AGENT_ENVIRONMENT == Environments.PRODUCTION
        assert settings.AGENT_LOG_LEVEL == LogLevels.ERROR
        assert settings.AGENT_NAME == "custom-agent"
        assert settings.IA_MODEL_HOST == "http://ollama:11434"
        assert settings.IA_MODEL_EMBEDDED_NAME == "custom-embed"
        assert settings.IA_MODEL_AGENT_NAME == "custom-model"
        assert settings.IA_MODEL_API_KEY == "sk-test"
        assert settings.IA_MODEL_TEMPERATURE == 0.7
        assert settings.PINECONE_HOST == "http://pinecone:5081"
        assert settings.PINECONE_INDEX_NAME == "production-index"
        assert settings.PINECONE_INDEX_DIMENSIONS == 1024
        assert settings.PINECONE_INDEX_METRIC == IndexMetric.EUCLIDEAN
        assert settings.REDIS_HOST == "redis-prod"
        assert settings.REDIS_PORT == 6380
        assert settings.REDIS_DB_INDEX == 2
        assert settings.REDIS_TTL_SECONDS == 3600

    def test_invalid_environment_raises_error(self, monkeypatch):
        """3.1. AGENT_ENVIRONMENT inválido -> ValidationError."""
        monkeypatch.setenv("AGENT_ENVIRONMENT", "invalid_env")
        with pytest.raises(ValidationError) as exc_info:
            Settings()
        # Verificar que el error menciona el campo
        assert "AGENT_ENVIRONMENT" in str(exc_info.value)

    def test_invalid_log_level_raises_error(self, monkeypatch):
        """3.2. AGENT_LOG_LEVEL inválido -> ValidationError."""
        monkeypatch.setenv("AGENT_LOG_LEVEL", "TRACE")  # no válido
        with pytest.raises(ValidationError) as exc_info:
            Settings()
        assert "AGENT_LOG_LEVEL" in str(exc_info.value)

    def test_invalid_index_metric_raises_error(self, monkeypatch):
        """3.3. PINECONE_INDEX_METRIC inválido -> ValidationError."""
        monkeypatch.setenv("PINECONE_INDEX_METRIC", "manhattan")
        with pytest.raises(ValidationError) as exc_info:
            Settings()
        assert "PINECONE_INDEX_METRIC" in str(exc_info.value)

    def test_invalid_temperature_raises_error(self, monkeypatch):
        """3.4. IA_MODEL_TEMPERATURE inválido (no numérico) -> ValidationError."""
        monkeypatch.setenv("IA_MODEL_TEMPERATURE", "very-hot")
        with pytest.raises(ValidationError) as exc_info:
            Settings()
        assert "IA_MODEL_TEMPERATURE" in str(exc_info.value)

    def test_temperature_out_of_range(self, monkeypatch):
        """Opcional: temperatura fuera de rango (aunque no está validado en el modelo, podrías añadirlo)."""
        # Como no hemos definido un validador de rango, esto debería pasar.
        # Si en el futuro añadimos validación, este test se actualizará.
        monkeypatch.setenv("IA_MODEL_TEMPERATURE", "2.5")
        settings = Settings()
        assert settings.IA_MODEL_TEMPERATURE == 2.5
        # Nota: si quieres que falle, debes agregar un field_validator en config.py.

def create_empty_env_file() -> Path:
    """Crea un archivo .env vacío en /tmp con nombre basado en timestamp."""
    timestamp = time.time()
    # Formato: /tmp/.<segundos>.<milisegundos>.env  (ej. /tmp/.1734567890.123.env)
    filename = f"/tmp/.{timestamp:.3f}.env"
    env_file = Path(filename)
    env_file.touch()  # Crea archivo vacío
    return env_file
