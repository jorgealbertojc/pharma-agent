# src/agent/state.py
"""
Estado del agente conversacional para el grafo de LangGraph.

Define la estructura de datos que se comparte entre todos los nodos del grafo.
Cada nodo recibe y modifica este estado para construir la respuesta final.
"""

from typing import Annotated, Any, List, Dict, Optional, Sequence
from typing_extensions import TypedDict
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
import operator


class AgentState(TypedDict):
    """
    Estado del agente para el grafo de LangGraph.

    Atributos:
        messages: Lista de mensajes del historial conversacional (acumulativa).
        question: Pregunta actual del usuario (texto sin procesar).
        context: Contexto recuperado desde documentos (RAG) como texto concatenado.
        inventory_results: Resultados de búsqueda en inventario (lista de medicamentos o vacío).
        suggestions: Sugerencias de productos complementarios (texto formateado).
        final_answer: Respuesta final generada por el modelo (antes de formatear).
        error: Mensaje de error si ocurrió un fallo en algún nodo (opcional).
        next_step: Control de flujo para decidir el siguiente nodo ('finish' o nombre de nodo).
        iterations: Contador de iteraciones para evitar bucles infinitos.
    """
    messages: Annotated[List[BaseMessage], operator.add]
    question: str
    context: Optional[str]
    inventory_results: Optional[List[Dict[str, Any]]]
    suggestions: Optional[str]
    final_answer: Optional[str]
    error: Optional[str]
    next_step: Optional[str]
    iterations: int


def create_initial_state(
    question: str,
    messages: Optional[List[BaseMessage]] = None,
) -> AgentState:
    """
    Crea el estado inicial del agente para una nueva consulta.

    Args:
        question: Pregunta del usuario.
        messages: Historial previo (opcional, para conversaciones).

    Returns:
        Estado inicial configurado.
    """
    return AgentState(
        messages=messages or [],
        question=question,
        context=None,
        inventory_results=None,
        suggestions=None,
        final_answer=None,
        error=None,
        next_step=None,
        iterations=0,
    )


def add_message_to_state(state: AgentState, message: BaseMessage) -> AgentState:
    """
    Añade un mensaje al estado (útil para actualizaciones seguras).

    Args:
        state: Estado actual.
        message: Mensaje a añadir (HumanMessage o AIMessage).

    Returns:
        Nuevo estado con el mensaje añadido.
    """
    return {
        **state,
        "messages": list(state["messages"]) + [message],
    }
