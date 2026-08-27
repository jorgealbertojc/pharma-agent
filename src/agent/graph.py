# src/agent/graph.py
"""
Grafo del agente conversacional construido con LangGraph.

Define el flujo de ejecución del agente, conectando nodos de procesamiento
(recuperación de documentos, búsqueda en inventario, sugerencias, generación de respuesta)
y transiciones condicionales basadas en el estado.
"""

from langgraph.graph import StateGraph, END
from langgraph.checkpoint import MemorySaver

from .state import AgentState
from .nodes import (
    retrieve_docs,
    search_inventory,
    suggest_upsell,
    generate_response,
    should_continue,
)


def build_agent_graph() -> StateGraph:
    """
    Construye y retorna el grafo del agente.

    El flujo:
    1. Nodo 'retrieve_docs' → obtiene contexto de documentos (RAG).
    2. Nodo 'search_inventory' → busca medicamentos en el inventario.
    3. Nodo 'suggest_upsell' → genera sugerencias de productos complementarios.
    4. Nodo 'generate_response' → produce la respuesta final con el modelo.
    5. Transición condicional 'should_continue' → decide si continuar o finalizar.

    Returns:
        StateGraph compilado y listo para ejecución.
    """
    # 1. Inicializar el grafo con el estado definido
    workflow = StateGraph(AgentState)

    # 2. Añadir nodos al grafo
    workflow.add_node("retrieve_docs", retrieve_docs)
    workflow.add_node("search_inventory", search_inventory)
    workflow.add_node("suggest_upsell", suggest_upsell)
    workflow.add_node("generate_response", generate_response)

    # 3. Definir las transiciones (aristas)
    # Inicio: después de retrieve_docs, ir a search_inventory (siempre)
    workflow.set_entry_point("retrieve_docs")
    workflow.add_edge("retrieve_docs", "search_inventory")
    workflow.add_edge("search_inventory", "suggest_upsell")
    workflow.add_edge("suggest_upsell", "generate_response")

    # 4. Transición condicional después de generate_response
    workflow.add_conditional_edges(
        "generate_response",
        should_continue,
        {
            "continue": "retrieve_docs",   # bucle si se necesita más información
            "finish": END,                 # finalizar
        },
    )

    # 5. Compilar el grafo con memoria (para persistencia opcional)
    memory = MemorySaver()
    compiled_graph = workflow.compile(checkpointer=memory)

    return compiled_graph


# Instancia global del grafo (para reutilización)
agent_graph = build_agent_graph()
