"""
Módulo de memoria conversacional.

Proporciona implementaciones de memoria para mantener el historial
de conversaciones en sistemas RAG o chatbots.

Clases disponibles:
    - BaseMemory: Interfaz abstracta para sistemas de memoria.
    - BufferMemory: Memoria tipo buffer con límite de mensajes y tokens.
    - PersistentMemory: Memoria persistente con DynamoDB (reemplazo de Redis).
"""

from .base import BaseMemory
from .buffer import BufferMemory

__all__ = [
    "BaseMemory",
    "BufferMemory",
    "PersistentMemory",
]


def __getattr__(name):
    """Lazy import for PersistentMemory to avoid circular imports."""
    if name == "PersistentMemory":
        from .persistent import PersistentMemory
        return PersistentMemory
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
