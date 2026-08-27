"""
Grafo del agente conversacional construido con LangGraph.
"""

from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

from .state import AgentState
from .nodes import AgentNodes


def build_agent_graph(nodes: AgentNodes) -> StateGraph:
    """
    Construye el grafo del agente usando los nodos de la instancia.

    Args:
        nodes: Instancia de AgentNodes (con dependencias inyectadas).

    Returns:
        StateGraph compilado.
    """
    workflow = StateGraph(AgentState)

    # Añadir nodos usando los métodos de la instancia
    workflow.add_node("retrieve_docs", nodes.retrieve_docs_node)
    workflow.add_node("search_inventory", nodes.search_inventory_node)
    workflow.add_node("suggest_upsell", nodes.suggest_upsell_node)
    workflow.add_node("generate_response", nodes.generate_response_node)

    workflow.set_entry_point("retrieve_docs")
    workflow.add_edge("retrieve_docs", "search_inventory")
    workflow.add_edge("search_inventory", "suggest_upsell")
    workflow.add_edge("suggest_upsell", "generate_response")

    workflow.add_conditional_edges(
        "generate_response",
        nodes.should_continue,
        {
            "continue": "retrieve_docs",
            "finish": END,
        },
    )

    memory = MemorySaver()
    return workflow.compile(checkpointer=memory)
