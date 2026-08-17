# app/langchain/memory/__init__.py
"""
Módulo de memoria conversacional.

Proporciona implementaciones de memoria para mantener el historial
de conversaciones en sistemas RAG o chatbots.

Clases disponibles:
    - BaseMemory: Interfaz abstracta para sistemas de memoria.
    - BufferMemory: Memoria tipo buffer con límite de mensajes y tokens.
"""

from .base import BaseMemory
from .buffer import BufferMemory

__all__ = [
    "BaseMemory",
    "BufferMemory",
]
