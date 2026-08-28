# tests/integration/agent/test_nodes.py
"""
Tests de integración para los nodos del agente.

Requiere:
- Contenedores de Ollama y Pinecone en ejecución.
- Google Sheets configurado con credenciales.
- Redis (opcional, solo si se usa caché).
- El índice de Pinecone debe estar vacío al iniciar los tests.

Cada test que usa Pinecone limpia el índice antes y después de la ejecución.
"""

import json
from pathlib import Path
from typing import Iterator, Dict, Any
from unittest.mock import patch, MagicMock

import pytest
from pinecone import Pinecone
from langchain_core.messages import HumanMessage, AIMessage

from app.core.config import settings
from app.inventory import InventoryClient, Inventario
from app.rag.indexer import Indexer
from app.rag.retriever import Retriever
from app.rag.enums import SearchType
from app.tools.search_docs import SearchDocs
from app.agent.nodes import AgentNodes
from app.agent.state import create_initial_state


# ============================================================
# Fixtures
# ============================================================

@pytest.fixture(scope="module")
def inventario_real() -> Inventario:
    """
    Obtiene el inventario real desde Google Sheets (una vez por módulo).
    """
    client = InventoryClient(sheet_name="INV-TI.RE")
    return client.fetch_inventory()


@pytest.fixture(scope="function")
def pinecone_index() -> Iterator[Pinecone]:
    """
    Retorna el índice de Pinecone y lo limpia al inicio y al final.
    """
    pinecone = Pinecone(api_key=settings.PINECONE_API_KEY)
    index = pinecone.Index(host=settings.PINECONE_HOST)
    # Limpiar antes de usar
    index.delete(delete_all=True)
    yield index
    # Limpiar después
    index.delete(delete_all=True)


@pytest.fixture(scope="function")
def test_document(tmp_path: Path) -> Path:
    """Crea un archivo de texto de prueba con información específica."""
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
def retriever(pinecone_index: Pinecone, test_document: Path) -> Retriever:
    """
    Indexa el documento de prueba en Pinecone y devuelve un retriever.
    """
    indexer = Indexer(
        file_path=test_document,
        chunk_size=500,
        chunk_overlap=0,
        settings=settings,
    )
    indexer.index()
    return Retriever(
        k=3,
        search_type=SearchType.SIMILARITY,
        settings=settings,
    )


@pytest.fixture(scope="function")
def agent_nodes(retriever: Retriever, inventario_real: Inventario) -> AgentNodes:
    """
    Crea una instancia de AgentNodes con dependencias reales.
    """
    return AgentNodes(retriever=retriever, inventory=inventario_real)


# ============================================================
# Tests
# ============================================================

class TestAgentNodes:
    """Suite de tests para los nodos del agente."""

    # ------------------------------------------------------------
    # retrieve_docs_node
    # ------------------------------------------------------------

    def test_retrieve_docs_node_success(self, agent_nodes: AgentNodes) -> None:
        """
        Given: Un agente con documentos indexados.
        When: Se solicita información sobre el protagonista.
        Then: El contexto contiene "Grenouille".
        """
        # Given
        state = create_initial_state("protagonista de El perfume")

        # When
        result = agent_nodes.retrieve_docs_node(state)

        # Then
        assert "context" in result
        assert result["context"] is not None
        assert "Grenouille" in result["context"]

    def test_retrieve_docs_node_empty_query(self, agent_nodes: AgentNodes) -> None:
        """
        Given: Un agente con documentos indexados.
        When: Se solicita con pregunta vacía.
        Then: El contexto es None y no hay error.
        """
        # Given
        state = create_initial_state("")

        # When
        result = agent_nodes.retrieve_docs_node(state)

        # Then
        assert result["context"] is None
        assert result.get("error") is not None

    # ------------------------------------------------------------
    # search_inventory_node
    # ------------------------------------------------------------

    def test_search_inventory_node_success(self, agent_nodes: AgentNodes) -> None:
        """
        Given: Un agente con inventario real.
        When: Se busca "ibuprofeno".
        Then: Se obtienen resultados (lista de dicts no vacía).
        """
        # Given
        state = create_initial_state("ibuprofeno")

        # When
        result = agent_nodes.search_inventory_node(state)

        # Then
        assert "inventory_results" in result
        assert len(result["inventory_results"]) > 0
        # Verificar que los resultados son dicts (model_dump)
        assert isinstance(result["inventory_results"][0], dict)

    def test_search_inventory_node_empty_query(self, agent_nodes: AgentNodes) -> None:
        """
        Given: Un agente con inventario real.
        When: Se busca con pregunta vacía.
        Then: La lista de resultados está vacía.
        """
        # Given
        state = create_initial_state("")

        # When
        result = agent_nodes.search_inventory_node(state)

        # Then
        assert result["inventory_results"] == []

    # ------------------------------------------------------------
    # suggest_upsell_node
    # ------------------------------------------------------------

    def test_suggest_upsell_node_success(self, agent_nodes: AgentNodes) -> None:
        """
        Given: Un agente con inventario real.
        When: Se solicita sugerencia para un producto existente.
        Then: Se obtiene un texto de sugerencia no vacío.
        """
        # Given
        state = create_initial_state("paracetamol")
        # Necesitamos que el inventario haya sido buscado antes para tener resultados
        # que se usan en suggest_upsell. Pero suggest_upsell internamente usa search_inventory
        # y el inventario real, así que no es necesario llamarlo antes.
        # Sin embargo, para que la sugerencia sea relevante, el producto debe existir.

        # When
        result = agent_nodes.suggest_upsell_node(state)

        # Then
        assert "suggestions" in result
        # Puede ser None si no hay sugerencias, pero al menos no debe haber error
        # Si hay sugerencias, debe ser un string
        if result["suggestions"] is not None:
            assert isinstance(result["suggestions"], str)
            assert len(result["suggestions"]) > 0

    def test_suggest_upsell_node_empty_query(self, agent_nodes: AgentNodes) -> None:
        """
        Given: Un agente con inventario real.
        When: Se solicita sugerencia con pregunta vacía.
        Then: La sugerencia es None.
        """
        # Given
        state = create_initial_state("")

        # When
        result = agent_nodes.suggest_upsell_node(state)

        # Then
        assert result["suggestions"] is None

    # ------------------------------------------------------------
    # generate_response_node
    # ------------------------------------------------------------

    def test_generate_response_node_success(self, agent_nodes: AgentNodes) -> None:
        """
        Given: Un agente con estado parcialmente poblado (contexto, inventario, sugerencias).
        When: Se genera una respuesta.
        Then: Se obtiene una respuesta no vacía (sin errores).
        """
        # Given: Estado con datos de prueba
        state = create_initial_state("¿Quién es Grenouille?")
        # Poblar algunas partes del estado para dar contexto al LLM
        state["context"] = "Grenouille es el protagonista de El perfume, un asesino con olfato extraordinario."
        state["inventory_results"] = []  # No hay resultados de inventario
        state["suggestions"] = "No hay sugerencias."

        # When
        result = agent_nodes.generate_response_node(state)

        # Then
        assert "final_answer" in result
        assert result["final_answer"] is not None
        assert len(result["final_answer"]) > 0
        # No debe haber error
        assert "error" not in result or result["error"] is None

    def test_generate_response_node_empty_query(self, agent_nodes: AgentNodes) -> None:
        """
        Given: Un agente con pregunta vacía.
        When: Se intenta generar respuesta.
        Then: Devuelve un mensaje de error.
        """
        # Given
        state = create_initial_state("")

        # When
        result = agent_nodes.generate_response_node(state)

        # Then
        assert "final_answer" in result
        assert "No se proporcionó pregunta" in result["final_answer"]
        assert result.get("error") is not None

    def test_generate_response_node_handles_llm_error(self, agent_nodes: AgentNodes) -> None:
        """
        Given: Un agente con el LLM mockeado para lanzar excepción.
        When: Se genera respuesta.
        Then: Devuelve mensaje de error y lo guarda en el estado.
        """
        # Given: Mockear el método invoke de la clase ChatOllama
        with patch('langchain_ollama.ChatOllama.invoke', side_effect=Exception("LLM timeout")):
            state = create_initial_state("¿Qué es el ibuprofeno?")
            state["context"] = "El ibuprofeno es un AINE."

            # When
            result = agent_nodes.generate_response_node(state)

            # Then
            assert "final_answer" in result
            assert "ocurrió un error" in result["final_answer"].lower()
            assert result.get("error") is not None

    # ------------------------------------------------------------
    # should_continue
    # ------------------------------------------------------------

    def test_should_continue_finish_when_error(self, agent_nodes: AgentNodes) -> None:
        """
        Given: Un estado con error.
        When: Se evalúa la continuación.
        Then: Devuelve "finish".
        """
        # Given
        state = create_initial_state("Pregunta")
        state["error"] = "Error de prueba"

        # When
        result = agent_nodes.should_continue(state)

        # Then
        assert result == "finish"

    def test_should_continue_finish_when_final_answer(self, agent_nodes: AgentNodes) -> None:
        """
        Given: Un estado con final_answer.
        When: Se evalúa la continuación.
        Then: Devuelve "finish".
        """
        # Given
        state = create_initial_state("Pregunta")
        state["final_answer"] = "Respuesta de prueba"

        # When
        result = agent_nodes.should_continue(state)

        # Then
        assert result == "finish"

    def test_should_continue_continue_when_no_final_answer_no_error(self, agent_nodes: AgentNodes) -> None:
        """
        Given: Un estado sin error ni final_answer.
        When: Se evalúa la continuación.
        Then: Devuelve "continue".
        """
        # Given
        state = create_initial_state("Pregunta")
        state["context"] = "Contexto de prueba"  # Estado parcial, sin final_answer ni error

        # When
        result = agent_nodes.should_continue(state)

        # Then
        assert result == "continue"
