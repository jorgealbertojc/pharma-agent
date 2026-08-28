"""
Tests de integración para el grafo del agente.

Verifica que el grafo compilado con nodos reales (Retriever, InventoryClient, etc.)
ejecute correctamente el flujo completo.
"""

from pathlib import Path

import pytest

from app.core.config import settings
from app.rag.retriever import Retriever
from app.rag.indexer import Indexer
from app.rag.enums import SearchType
from app.inventory.client import InventoryClient
from app.agent.graph import build_agent_graph
from app.agent.nodes import AgentNodes
from app.agent.state import create_initial_state


@pytest.fixture(scope="module")
def inventario_real():
    """Obtiene el inventario real desde Google Sheets una sola vez por módulo."""
    client = InventoryClient(sheet_name="INV-TI.RE")
    return client.fetch_inventory()


@pytest.fixture(scope="function")
def test_document(tmp_path: Path) -> Path:
    """Crea un documento de prueba con contenido farmacéutico."""
    content = (
        "El ibuprofeno es un antiinflamatorio no esteroideo (AINE). "
        "Se utiliza para aliviar el dolor, la fiebre y la inflamación. "
        "La dosis habitual en adultos es de 400-600 mg cada 6-8 horas. "
        "Contraindicaciones: úlcera péptica activa, insuficiencia renal grave."
    )
    file_path = tmp_path / "test_doc.txt"
    file_path.write_text(content, encoding="utf-8")
    return file_path


@pytest.fixture(scope="function")
def nodes(inventario_real, test_document: Path) -> AgentNodes:
    """
    Limpia Pinecone, indexa el documento de prueba y retorna una instancia de AgentNodes.
    """
    from pinecone import Pinecone
    pc = Pinecone(api_key=settings.PINECONE_API_KEY)
    idx = pc.Index(host=settings.PINECONE_HOST)
    idx.delete(delete_all=True)

    indexer = Indexer(
        file_path=test_document,
        chunk_size=500,
        chunk_overlap=0,
        settings=settings,
    )
    indexer.index()

    retriever = Retriever(
        k=3,
        search_type=SearchType.SIMILARITY,
        settings=settings,
    )

    return AgentNodes(retriever=retriever, inventory=inventario_real)


@pytest.fixture(scope="function")
def run_config() -> dict:
    """Configuración mínima de LangGraph con thread_id."""
    return {"configurable": {"thread_id": "test-thread"}}


class TestAgentGraph:
    """Suite de tests de integración para el grafo del agente."""

    def test_graph_compiles_without_errors(self, nodes):
        graph = build_agent_graph(nodes)
        assert graph is not None
        assert hasattr(graph, "invoke")
        assert hasattr(graph, "stream")

    def test_graph_executes_full_flow_and_returns_final_answer(self, nodes, run_config):
        graph = build_agent_graph(nodes)
        state = create_initial_state("¿Qué es el ibuprofeno?")
        result = graph.invoke(state, config=run_config)
        assert result is not None
        assert result.get("final_answer") is not None
        assert len(result["final_answer"]) > 0
        assert result.get("error") is None

    def test_graph_handles_empty_question_gracefully(self, nodes, run_config):
        graph = build_agent_graph(nodes)
        state = create_initial_state("")
        result = graph.invoke(state, config=run_config)
        assert result is not None
        if result.get("error"):
            assert "pregunta" in result["error"].lower()
        else:
            assert result.get("final_answer") is not None
            assert "pregunta" in result["final_answer"].lower()

    def test_graph_handles_inventory_integration(self, nodes, run_config):
        graph = build_agent_graph(nodes)
        state = create_initial_state("paracetamol")
        result = graph.invoke(state, config=run_config)
        inventory_results = result.get("inventory_results")
        if inventory_results:
            assert len(inventory_results) > 0
            assert isinstance(inventory_results[0], dict)
        assert result.get("error") is None
