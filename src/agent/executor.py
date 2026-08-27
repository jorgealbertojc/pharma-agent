# src/agent/executor.py
"""
Ejecutor del agente conversacional.

Maneja el bucle de interacción con el usuario, procesando cada pregunta
a través del grafo de LangGraph y mostrando las respuestas formateadas.
"""

import logging
from langgraph.graph import StateGraph, END
from langchain_core.messages import HumanMessage, AIMessage

from src.core.config import settings
from src.rag.retriever import Retriever
from src.rag.enums import SearchType
from src.inventory.client import InventoryClient
from src.agent.state import AgentState, create_initial_state, add_message_to_state
from src.agent.nodes import AgentNodes
from src.tools import ResponseFormatter

logger = logging.getLogger(__name__)


class AgentExecutor:
    """
    Ejecutor del agente que maneja la interacción con el usuario.
    """

    def __init__(self):
        # 1. Inicializar dependencias
        logger.info("Inicializando Retriever...")
        retriever = Retriever(k=3, search_type=SearchType.SIMILARITY, settings=settings)

        logger.info("Obteniendo inventario desde Google Sheets...")
        client = InventoryClient(sheet_name="INV-TI.RE")
        inventory = client.fetch_inventory()

        # 2. Crear instancia de AgentNodes
        self.nodes = AgentNodes(retriever=retriever, inventory=inventory)
        self.formatter = ResponseFormatter()

        # 3. Construir el grafo manualmente
        workflow = StateGraph(AgentState)
        workflow.add_node("retrieve_docs", self.nodes.retrieve_docs_node)
        workflow.add_node("search_inventory", self.nodes.search_inventory_node)
        workflow.add_node("suggest_upsell", self.nodes.suggest_upsell_node)
        workflow.add_node("generate_response", self.nodes.generate_response_node)

        workflow.set_entry_point("retrieve_docs")
        workflow.add_edge("retrieve_docs", "search_inventory")
        workflow.add_edge("search_inventory", "suggest_upsell")
        workflow.add_edge("suggest_upsell", "generate_response")
        workflow.add_conditional_edges(
            "generate_response",
            self.nodes.should_continue,
            {
                "continue": "retrieve_docs",
                "finish": END,
            }
        )

        self.graph = workflow.compile()
        self.state = None

    def run(self) -> None:
        """Inicia el bucle de interacción con el usuario."""
        print("🤖 Agente farmacéutico iniciado. Escribe 'salir' para terminar.\n")
        self.state = create_initial_state("")

        while True:
            try:
                user_input = input("🧑‍⚕️ Tú: ").strip()
                if not user_input:
                    continue
                if user_input.lower() in ("salir", "exit", "quit"):
                    print("👋 ¡Hasta luego!")
                    break

                self._process_question(user_input)

            except KeyboardInterrupt:
                print("\n👋 Interrupción detectada. Saliendo...")
                break
            except Exception as e:
                logger.error(f"Error inesperado: {e}")
                print(f"❌ Ocurrió un error: {e}")

    def _process_question(self, question: str) -> None:
        """Procesa una pregunta del usuario a través del grafo."""

        if not question or not question.strip():
            return

        if self.state is None:
            self.state = create_initial_state("")

        self.state = add_message_to_state(self.state, HumanMessage(content=question))
        self.state["question"] = question
        self.state["final_answer"] = None
        self.state["error"] = None
        self.state["context"] = None
        self.state["inventory_results"] = None
        self.state["suggestions"] = None
        self.state["next_step"] = None
        self.state["iterations"] = 0

        result_state = self.graph.invoke(self.state)
        self.state = result_state

        final_answer = result_state.get("final_answer")
        if final_answer:
            print("\n🤖 Asistente:")
            print(final_answer)
            print()
            self.state = add_message_to_state(self.state, AIMessage(content=final_answer))
        else:
            error = result_state.get("error")
            print(f"\n❌ Error: {error}" if error else "\n⚠️ No se pudo generar una respuesta.")


if __name__ == "__main__":
    executor = AgentExecutor()
    executor.run()
