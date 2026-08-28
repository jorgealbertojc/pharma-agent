# tests/integration/test_indexer.py
"""
Tests de integración para el indexador de Pinecone.

Estos tests requieren que los contenedores lab-ollama y lab-pinecone
estén en ejecución y accesibles desde la configuración por defecto.
"""

import os
from pathlib import Path
from typing import Iterator

import pytest
from _pytest.tmpdir import TempPathFactory

from app.core import config
from app.core.config import Settings
from app.rag.indexer import Indexer


# ------------------------------------------------------------
# Fixtures para archivos temporales y configuración
# ------------------------------------------------------------

@pytest.fixture
def temp_env_file(tmp_path: Path) -> Path:
    """Crea un archivo .env temporal con valores por defecto para Pinecone y Redis."""
    env_content = """
PINECONE_HOST=http://localhost:5081
PINECONE_INDEX_NAME=test-index
IA_MODEL_HOST=http://localhost:11434
IA_MODEL_EMBEDDED_NAME=nomic-embed-text
REDIS_HOST=localhost
REDIS_PORT=6379
"""
    env_file = tmp_path / ".env"
    env_file.write_text(env_content, encoding="utf-8")
    return env_file


@pytest.fixture
def settings_from_env(temp_env_file: Path) -> Settings:
    """Carga una instancia de Settings desde el archivo .env temporal."""
    return Settings.from_env_file(temp_env_file)


@pytest.fixture
def override_settings(settings_from_env: Settings) -> Iterator[None]:
    """
    Sustituye el objeto `settings` global por el cargado desde el .env temporal.
    """
    original_settings = config.settings
    config.settings = settings_from_env
    yield
    config.settings = original_settings


@pytest.fixture
def sample_text_file(tmp_path: Path) -> Path:
    """Crea un archivo de texto de ejemplo con contenido válido."""
    content = """
Ibuprofeno es un antiinflamatorio no esteroideo (AINE).
Se utiliza para aliviar el dolor, la inflamación y la fiebre.
La dosis habitual en adultos es de 400-600 mg cada 6-8 horas.
No debe administrarse a pacientes con úlcera péptica activa.
"""
    file_path = tmp_path / "sample.txt"
    file_path.write_text(content, encoding="utf-8")
    return file_path


@pytest.fixture
def empty_text_file(tmp_path: Path) -> Path:
    """Crea un archivo de texto vacío."""
    file_path = tmp_path / "empty.txt"
    file_path.touch()
    return file_path


# ------------------------------------------------------------
# Tests de validaciones (errores esperados)
# ------------------------------------------------------------

def test_indexer_raises_if_file_not_found(override_settings: None) -> None:
    """1. El archivo no existe → FileNotFoundError."""
    non_existent = Path("/nonexistent/file.txt")
    indexer = Indexer(file_path=non_existent)
    with pytest.raises(FileNotFoundError, match="El archivo .* no existe."):
        indexer.index()


def test_indexer_raises_if_pinecone_host_missing(override_settings: None, tmp_path: Path) -> None:
    """2. PINECONE_HOST no está definido → ValueError."""
    base = Settings()
    test_settings = base.model_copy(update={"PINECONE_HOST": ""})

    # Creamos un archivo dummy
    dummy_file = tmp_path / "dummy.txt"
    dummy_file.write_text("test", encoding="utf-8")

    indexer = Indexer(file_path=dummy_file, settings=test_settings)
    with pytest.raises(ValueError, match="PINECONE_HOST no está definido"):
        indexer.index()


def test_indexer_raises_if_pinecone_index_name_missing(override_settings: None, tmp_path: Path) -> None:
    """3. PINECONE_INDEX_NAME no está definido → ValueError."""
    base = Settings()
    test_settings = base.model_copy(update={"PINECONE_INDEX_NAME": ""})

    dummy_file = tmp_path / "dummy.txt"
    dummy_file.write_text("test", encoding="utf-8")

    indexer = Indexer(file_path=dummy_file, settings=test_settings)
    with pytest.raises(ValueError, match="PINECONE_INDEX_NAME no está definido"):
        indexer.index()


# ------------------------------------------------------------
# Tests de funcionalidad
# ------------------------------------------------------------

def test_indexer_raises_if_no_chunks(override_settings: None, empty_text_file: Path) -> None:
    """4. El documento no generó ningún fragmento → ValueError."""
    indexer = Indexer(file_path=empty_text_file, chunk_size=100, chunk_overlap=0)
    with pytest.raises(ValueError, match="El documento no generó ningún fragmento"):
        indexer.index()


def test_indexer_returns_number_of_chunks(
    override_settings: None,
    sample_text_file: Path,
) -> None:
    """5. Indexación exitosa → retorna el número de fragmentos > 0."""
    # Usamos chunk_size pequeño para asegurar varios chunks
    indexer = Indexer(
        file_path=sample_text_file,
        chunk_size=50,
        chunk_overlap=10,
    )
    num_chunks = indexer.index()
    assert num_chunks > 0
    # Podríamos verificar que realmente se escribió en Pinecone,
    # pero eso implicaría usar el retriever. No es necesario para este test.
    # La ausencia de excepción ya indica éxito parcial.
