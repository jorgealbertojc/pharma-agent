"""
Tests de integración para SearchDocs.

Cada test limpia el índice de Pinecone antes de indexar el documento de prueba,
asegurando que solo se usen los datos de prueba.
"""

import json
from pathlib import Path

import pytest
from pinecone import Pinecone

from src.core.config import settings
from src.rag.indexer import Indexer
from src.rag.retriever import Retriever
from src.rag.enums import SearchType
from src.tools.search_docs import SearchDocs


@pytest.fixture(scope="function")
def test_document(tmp_path: Path) -> Path:
    """Crea un archivo de texto de prueba con información completa."""
    content = (
        "El perfume es una novela de Patrick Süskind. "
        "El protagonista es Jean-Baptiste Grenouille, un asesino con olfato extraordinario. "
        "Nace en París en 1738 y muere devorado por una multitud en 1767. "
        "Grenouille puede distinguir todos los olores del mundo."
    )
    file_path = tmp_path / "test_doc.txt"
    file_path.write_text(content, encoding="utf-8")
    return file_path


@pytest.fixture(scope="function")
def retriever(test_document: Path) -> Retriever:
    """
    Limpia el índice de Pinecone, indexa el documento de prueba y devuelve un retriever.
    """
    # 1. Limpiar el índice existente
    pinecone = Pinecone(api_key=settings.PINECONE_API_KEY)
    index = pinecone.Index(host=settings.PINECONE_HOST)
    index.delete(delete_all=True)  # Elimina todos los vectores

    # 2. Indexar el documento de prueba
    indexer = Indexer(
        file_path=test_document,
        chunk_size=500,      # Todo el contenido en un solo fragmento
        chunk_overlap=0,
        settings=settings,
    )
    indexer.index()

    # 3. Retornar el retriever
    return Retriever(
        k=3,
        search_type=SearchType.SIMILARITY,
        settings=settings,
    )


@pytest.fixture(scope="function")
def search_docs(retriever: Retriever) -> SearchDocs:
    """Crea una instancia de SearchDocs con el retriever recién indexado."""
    return SearchDocs(retriever=retriever)


class TestSearchDocs:
    """Suite de tests de integración para SearchDocs."""

    def test_search_returns_fragments(self, search_docs: SearchDocs) -> None:
        """
        Given: Un buscador con el documento de prueba indexado.
        When: Se consulta por el protagonista.
        Then: Se obtiene al menos un fragmento que mencione "Grenouille".
        """
        searcher = search_docs
        fragments = searcher.search("protagonista de El perfume")
        assert len(fragments) > 0
        assert any("Grenouille" in f for f in fragments)

    def test_search_as_context(self, search_docs: SearchDocs) -> None:
        """
        Given: Un buscador con el documento de prueba indexado.
        When: Se consulta por la muerte del protagonista.
        Then: El contexto contiene "muere" o "devorado".
        """
        searcher = search_docs
        context = searcher.search_as_context("¿Cómo muere Grenouille?")
        assert isinstance(context, str)
        assert len(context) > 0
        assert "muere" in context.lower() or "devorado" in context.lower()

    def test_search_and_format_markdown(self, search_docs: SearchDocs) -> None:
        """
        Given: Un buscador con el documento de prueba indexado.
        When: Se consulta y se solicita formato Markdown.
        Then: El resultado es un string con viñetas o mensaje informativo.
        """
        searcher = search_docs
        result = searcher.search_and_format("olfato", format_type="markdown", title="Resultados")
        assert isinstance(result, str)
        assert "## Resultados" in result or "No se encontró" in result
        if "No se encontró" not in result:
            assert "- " in result
            assert "fragmentos relevantes" in result

    def test_search_and_format_json(self, search_docs: SearchDocs) -> None:
        """
        Given: Un buscador con el documento de prueba indexado.
        When: Se consulta y se solicita formato JSON.
        Then: El resultado es un JSON válido con la consulta y los resultados.
        """
        searcher = search_docs
        result = searcher.search_and_format("París", format_type="json")
        data = json.loads(result)
        assert "query" in data
        assert "results" in data
        assert data["query"] == "París"
        assert isinstance(data["results"], list)

    def test_search_empty_query(self, search_docs: SearchDocs) -> None:
        """
        Given: Un buscador con el documento de prueba indexado.
        When: Se busca con una cadena vacía.
        Then: Se obtiene lista vacía y contexto informativo.
        """
        searcher = search_docs
        assert searcher.search("") == []
        assert searcher.search("   ") == []
        assert searcher.search_as_context("") == "No se encontró información relevante."

    def test_search_and_format_max_items(self, search_docs: SearchDocs) -> None:
        """
        Given: Un buscador con el documento de prueba indexado.
        When: Se consulta con max_items=1.
        Then: Solo se muestra un fragmento y se indica el total.
        """
        searcher = search_docs
        result = searcher.search_and_format("Grenouille", format_type="markdown", max_items=1, title="Prueba")
        if "No se encontró" not in result:
            assert result.count("- ") <= 1
            assert "Se encontraron" in result
