# src/agent/nodes.py
"""
Nodos del grafo del agente.

Cada nodo implementa una funcionalidad específica:
- retrieve_docs: Consulta documentos externos (RAG).
- search_inventory: Busca medicamentos en el inventario.
- suggest_upsell: Sugiere productos complementarios.
- generate_response: Genera la respuesta final con el LLM.
- should_continue: Función de enrutamiento para decidir si continuar o finalizar.

Las dependencias se inyectan a través de la clase AgentNodes para facilitar
el testing y el desacoplamiento.
"""

import logging
from typing import Dict, Any, Literal, List

from langchain_core.messages import HumanMessage, AIMessage, BaseMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_ollama import ChatOllama

from app.core.config import settings
from app.inventory.schema import Inventario, Medicamento
from app.rag.retriever import Retriever
from app.tools import SearchDocs, SearchInventory, SuggestUpsell, ResponseFormatter

from .state import AgentState

logger = logging.getLogger(__name__)


class AgentNodes:
    """
    Encapsula los nodos del agente, inyectando las dependencias necesarias.

    Args:
        retriever: Instancia del retriever de RAG.
        inventory: Objeto Inventario con todos los medicamentos.
    """

    def __init__(self, retriever: Retriever, inventory: Inventario):
        self.retriever = retriever
        self.inventory = inventory

        # Inicializar herramientas
        self.search_docs = SearchDocs(retriever)
        self.search_inventory = SearchInventory(inventory)
        self.suggest_upsell = SuggestUpsell(
            inventory,
            search_docs=self.search_docs,
        )
        self.formatter = ResponseFormatter()

        # Inicializar modelo de lenguaje (ChatOllama)
        self.llm = ChatOllama(
            model=settings.IA_MODEL_AGENT_NAME,
            base_url=settings.IA_MODEL_HOST,
            temperature=settings.IA_MODEL_TEMPERATURE,
        )

        # Prompt template para la generación de respuestas
        self.prompt_template = ChatPromptTemplate.from_messages([
            ("system", """Eres un asistente farmacéutico profesional y útil.
Debes responder las preguntas del usuario basándote en el contexto proporcionado (documentos, inventario y sugerencias).
Si no tienes suficiente información, dilo claramente.
Formatea tu respuesta en Markdown (usar títulos, negritas, listas, etc.).

**Historial de la conversación:**
{history}

**Contexto de documentos:**
{context}

**Resultados del inventario:**
{inventory_results}

**Sugerencias de venta adicional:**
{suggestions}
"""),
            ("human", "{question}")
        ])

    # ------------------------------------------------------------
    # Nodos del grafo
    # ------------------------------------------------------------

    def retrieve_docs_node(self, state: AgentState) -> Dict[str, Any]:
        """
        Nodo para recuperar contexto de los documentos (RAG).

        Args:
            state: Estado actual del agente.

        Returns:
            Diccionario con el contexto recuperado o error.
        """
        question = state.get("question", "")
        if not question:
            return {"context": None, "error": "No se proporcionó pregunta."}

        try:
            context = self.search_docs.search_as_context(question)
            return {"context": context}
        except Exception as e:
            logger.error(f"Error en retrieve_docs: {e}")
            return {"context": None, "error": str(e)}

    def search_inventory_node(self, state: AgentState) -> Dict[str, Any]:
        """
        Nodo para buscar en el inventario.

        Args:
            state: Estado actual del agente.

        Returns:
            Diccionario con los resultados de la búsqueda (lista de dicts) o error.
        """
        question = state.get("question", "")
        if not question:
            return {"inventory_results": []}

        try:
            results = self.search_inventory.search(question)
            # Convertir a dict para serialización segura en el estado
            results_dicts = [med.model_dump() for med in results]
            return {"inventory_results": results_dicts}
        except Exception as e:
            logger.error(f"Error en search_inventory: {e}")
            return {"inventory_results": [], "error": str(e)}

    def suggest_upsell_node(self, state: AgentState) -> Dict[str, Any]:
        """
        Nodo para generar sugerencias de venta adicional.

        Args:
            state: Estado actual del agente.

        Returns:
            Diccionario con las sugerencias formateadas o error.
        """
        question = state.get("question", "")
        if not question:
            return {"suggestions": None}

        try:
            # Si hay resultados de inventario, pasamos el primero como referencia
            suggestion_text = self.suggest_upsell.suggest(question)
            return {"suggestions": suggestion_text}
        except Exception as e:
            logger.error(f"Error en suggest_upsell: {e}")
            return {"suggestions": None, "error": str(e)}

    def generate_response_node(self, state: AgentState) -> Dict[str, Any]:
        """
        Nodo para generar la respuesta final con el LLM.

        Args:
            state: Estado actual del agente.

        Returns:
            Diccionario con la respuesta final o error.
        """
        question = state.get("question", "")
        if not question:
            return {"final_answer": "No se proporcionó pregunta.", "error": "Pregunta vacía"}

        # Preparar los datos del estado para el prompt
        history = state.get("messages", [])
        history_str = self._format_history(history)

        context = state.get("context", "No hay contexto de documentos.")

        inventory_results = state.get("inventory_results", [])
        inventory_str = self._format_inventory_results(inventory_results)

        suggestions = state.get("suggestions", "No hay sugerencias.")

        # Construir y ejecutar el prompt
        try:
            prompt = self.prompt_template.format(
                history=history_str,
                context=context,
                inventory_results=inventory_str,
                suggestions=suggestions,
                question=question
            )

            response = self.llm.invoke(prompt)
            return {"final_answer": response.content}
        except Exception as e:
            logger.error(f"Error en generate_response: {e}")
            return {
                "final_answer": f"Lo siento, ocurrió un error al generar la respuesta: {e}",
                "error": str(e)
            }

    # ------------------------------------------------------------
    # Funciones auxiliares
    # ------------------------------------------------------------

    def _format_history(self, messages: List[BaseMessage]) -> str:
        """Formatea el historial de mensajes para el prompt."""
        if not messages:
            return "No hay historial previo."
        lines = []
        for msg in messages:
            role = "Usuario" if isinstance(msg, HumanMessage) else "Asistente"
            lines.append(f"{role}: {msg.content}")
        return "\n".join(lines)

    def _format_inventory_results(self, results: List[Dict[str, Any]]) -> str:
        """Formatea los resultados del inventario para el prompt."""
        if not results:
            return "No hay resultados en inventario."
        # Reconstruir objetos Medicamento desde dicts
        medicamentos = [Medicamento(**med) for med in results]
        return self.formatter.format_medicamentos(
            medicamentos,
            format_type="table",
            max_items=5
        )

    # ------------------------------------------------------------
    # Función de enrutamiento
    # ------------------------------------------------------------

    def should_continue(self, state: AgentState) -> Literal["finish", "continue"]:
        """
        Decide si el grafo debe continuar o finalizar.

        Args:
            state: Estado actual del agente.

        Returns:
            "finish" si hay respuesta o error, "continue" en caso contrario.
        """
        if state.get("error") or state.get("final_answer"):
            return "finish"
        return "continue"
