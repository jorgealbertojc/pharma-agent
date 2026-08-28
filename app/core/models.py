# src/core/models.py
"""
Modelos de datos centrales para la aplicación.

Define los contratos de entrada/salida para la API y el CLI,
independientes de la implementación interna del agente.
"""

from typing import Optional, List, Any, Dict
from pydantic import BaseModel, Field, field_validator


class QueryRequest(BaseModel):
    """
    Solicitud de consulta al agente.

    Attributes:
        question: Pregunta del usuario (texto libre).
        session_id: Identificador de sesión para memoria persistente (opcional).
                    Si no se proporciona, se genera uno nuevo.
    """
    question: str = Field(..., description="Pregunta del usuario", min_length=1)
    session_id: Optional[str] = Field(None, description="Identificador de sesión (opcional)")

    @field_validator('question')
    def validate_question(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError('La pregunta no puede estar vacía')
        return v


class AgentResponse(BaseModel):
    """
    Respuesta generada por el agente.

    Attributes:
        answer: Respuesta final en texto plano o Markdown.
        sources: Lista de fuentes o referencias (opcional).
        suggestions: Sugerencias de productos complementarios (opcional).
        inventory_results: Resultados de búsqueda en inventario (opcional).
        error: Mensaje de error si ocurrió (opcional).
    """
    answer: str = Field(..., description="Respuesta del agente")
    sources: Optional[List[str]] = Field(None, description="Fuentes de información")
    suggestions: Optional[str] = Field(None, description="Sugerencias de productos")
    inventory_results: Optional[List[Dict[str, Any]]] = Field(None, description="Resultados de inventario")
    error: Optional[str] = Field(None, description="Mensaje de error si ocurrió")


class ErrorResponse(BaseModel):
    """
    Respuesta de error estandarizada.

    Attributes:
        error: Código o mensaje de error.
        details: Detalles adicionales (opcional).
    """
    error: str = Field(..., description="Código o mensaje de error")
    details: Optional[str] = Field(None, description="Detalles adicionales")
