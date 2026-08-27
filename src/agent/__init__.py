# src/agent/__init__.py
"""
Módulo del agente conversacional.

Proporciona las clases y utilidades principales para interactuar
con el agente farmacéutico.

Uso básico:
    from src.agent import AgentExecutor

    executor = AgentExecutor()
    executor.run()
"""

from .executor import AgentExecutor
from .nodes import AgentNodes
from .state import AgentState, create_initial_state, add_message_to_state
from .graph import build_agent_graph

__all__ = [
    "AgentExecutor",
    "AgentNodes",
    "AgentState",
    "create_initial_state",
    "add_message_to_state",
    "build_agent_graph",
]
