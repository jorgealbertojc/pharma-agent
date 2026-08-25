# app/langchain/memory/__init__.py
"""
Módulo de memoria conversacional.

Proporciona implementaciones de memoria para mantener el historial
de conversaciones en sistemas RAG o chatbots.

Clases disponibles:
    - BaseMemory: Interfaz abstracta para sistemas de memoria.
    - BufferMemory: Memoria tipo buffer con límite de mensajes y tokens.
    - PersistentMemory: Memoria persistente con Redis (almacenamiento duradero).
"""

from .base import BaseMemory
from .buffer import BufferMemory
from .persistent import PersistentMemory

__all__ = [
    "BaseMemory",
    "BufferMemory",
    "PersistentMemory"
]
