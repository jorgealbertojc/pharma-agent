"""
Módulo del agente conversacional.

Proporciona las clases y utilidades principales para interactuar
con el agente farmacéutico.
"""

# Importaciones ligeras (solo tipos y utilidades sin dependencias pesadas)
from .state import AgentState, create_initial_state, add_message_to_state

# Exportar en __all__ para que la interfaz pública siga siendo clara
__all__ = [
    "AgentExecutor",          # Interfaz principal para ejecutar el agente
    "AgentNodes",             # Nodos del grafo (para personalización o pruebas)
    "AgentState",             # Tipo del estado compartido
    "create_initial_state",   # Crea el estado inicial
    "add_message_to_state",   # Añade un mensaje al estado de forma segura
    "build_agent_graph",      # Construye el grafo (si se necesita customizar)
    "agent_graph",            # Instancia global del grafo compilado (desaconsejado)
]

# Importaciones perezosas (solo se cargan cuando se accede al atributo)
def __getattr__(name):
    if name == "AgentExecutor":
        from .executor import AgentExecutor
        return AgentExecutor
    if name == "AgentNodes":
        from .nodes import AgentNodes
        return AgentNodes
    if name == "build_agent_graph":
        from .graph import build_agent_graph
        return build_agent_graph
    if name == "agent_graph":
        from .graph import agent_graph
        return agent_graph
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
