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
from typing import Dict
import tempfile

from pydantic import ValidationError

from src.core.config import Settings
from src.core.enums import Environments, LogLevels, IndexMetric


class TestConfig:
    """Suite de tests para la configuración."""

    def test_default_values_when_env_empty(self):
        """1. Archivo .env vacío: deben usarse los valores por defecto."""
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

    def test_valid_values_from_env(self):
        """2. Todas las variables de entorno son válidas."""
        # 1. Definir variables de prueba
        env_vars = {
            "AGENT_ENVIRONMENT": "production",
            "AGENT_LOG_LEVEL": "ERROR",
            "AGENT_NAME": "custom-agent",
            "IA_MODEL_HOST": "http://ollama:11434",
            "IA_MODEL_EMBEDDED_NAME": "custom-embed",
            "IA_MODEL_AGENT_NAME": "custom-model",
            "IA_MODEL_API_KEY": "sk-test",
            "IA_MODEL_TEMPERATURE": "0.7",
            "PINECONE_HOST": "http://pinecone:5081",
            "PINECONE_INDEX_NAME": "production-index",
            "PINECONE_INDEX_DIMENSIONS": "1024",
            "PINECONE_INDEX_METRIC": "euclidean",
            "REDIS_HOST": "redis-prod",
            "REDIS_PORT": "6380",
            "REDIS_DB_INDEX": "2",
            "REDIS_TTL_SECONDS": "3600",
        }

        # 2. Crear archivo .env con esos valores
        env_file = create_env_file_with_values(env_vars)

        try:
            # 3. Cargar Settings desde ese archivo
            settings = Settings.from_env_file(env_file)

            # 4. Validar que los valores coinciden
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
        finally:
            # Limpiar archivo temporal
            env_file.unlink(missing_ok=True)

    def test_invalid_environment_raises_error(self):
        """3.1. AGENT_ENVIRONMENT inválido -> ValidationError."""
        env_file = create_env_file_with_values({"AGENT_ENVIRONMENT": "invalid_env"})
        try:
            with pytest.raises(ValidationError) as exc_info:
                Settings.from_env_file(env_file)
            assert "AGENT_ENVIRONMENT" in str(exc_info.value)
        finally:
            env_file.unlink(missing_ok=True)

    def test_invalid_log_level_raises_error(self):
        """3.2. AGENT_LOG_LEVEL inválido -> ValidationError."""
        env_file = create_env_file_with_values({"AGENT_LOG_LEVEL": "TRACE"})
        try:
            with pytest.raises(ValidationError) as exc_info:
                Settings.from_env_file(env_file)
            assert "AGENT_LOG_LEVEL" in str(exc_info.value)
        finally:
            env_file.unlink(missing_ok=True)

    def test_invalid_index_metric_raises_error(self):
        """3.3. PINECONE_INDEX_METRIC inválido -> ValidationError."""
        env_file = create_env_file_with_values({"PINECONE_INDEX_METRIC": "manhattan"})
        try:
            with pytest.raises(ValidationError) as exc_info:
                Settings.from_env_file(env_file)
            assert "PINECONE_INDEX_METRIC" in str(exc_info.value)
        finally:
            env_file.unlink(missing_ok=True)

    def test_invalid_temperature_raises_error(self):
        """3.4. IA_MODEL_TEMPERATURE inválido (no numérico) -> ValidationError."""
        env_file = create_env_file_with_values({"IA_MODEL_TEMPERATURE": "very-hot"})
        try:
            with pytest.raises(ValidationError) as exc_info:
                Settings.from_env_file(env_file)
            assert "IA_MODEL_TEMPERATURE" in str(exc_info.value)
        finally:
            env_file.unlink(missing_ok=True)

    def test_temperature_out_of_range(self):
        """Opcional: temperatura fuera de rango (sin validación de rango)."""
        env_file = create_env_file_with_values({"IA_MODEL_TEMPERATURE": "2.5"})
        try:
            settings = Settings.from_env_file(env_file)
            assert settings.IA_MODEL_TEMPERATURE == 2.5
        finally:
            env_file.unlink(missing_ok=True)

def create_empty_env_file() -> Path:
    """Crea un archivo .env vacío en /tmp con nombre basado en timestamp."""
    timestamp = time.time()
    # Formato: /tmp/.<segundos>.<milisegundos>.env  (ej. /tmp/.1734567890.123.env)
    filename = f"/tmp/.{timestamp:.3f}.env"
    env_file = Path(filename)
    env_file.touch()  # Crea archivo vacío
    return env_file

def create_env_file_with_values(values: Dict[str, str]) -> Path:
    """
    Crea un archivo .env temporal con las variables dadas.

    Args:
        values: Diccionario con variables de entorno (clave -> valor).

    Returns:
        Path al archivo temporal.
    """
    # Crear un archivo temporal en /tmp con nombre único
    import time
    filename = f"/tmp/.{time.time():.3f}.env"
    env_file = Path(filename)

    with open(env_file, "w") as f:
        for key, value in values.items():
            f.write(f"{key}={value}\n")

    return env_file
