# src/core/exceptions.py
"""
Excepciones personalizadas para la aplicación.

Define una jerarquía de excepciones que permite manejar errores de forma granular
y consistente en todos los módulos (RAG, Inventory, Agent, API, etc.).
"""

from typing import Optional


class AppException(Exception):
    """
    Excepción base para toda la aplicación.

    Todas las excepciones personalizadas deben heredar de esta clase
    para permitir capturas genéricas en puntos de entrada (CLI, API).
    """

    def __init__(self, message: str, details: Optional[str] = None):
        self.message = message
        self.details = details
        super().__init__(message)

    def __str__(self) -> str:
        if self.details:
            return f"{self.message} (detalles: {self.details})"
        return self.message


# ------------------------------------------------------------
# Excepciones de configuración
# ------------------------------------------------------------

class ConfigurationError(AppException):
    """
    Error relacionado con la configuración de la aplicación.
    Ej: variable de entorno faltante, archivo de credenciales no encontrado.
    """
    pass


# ------------------------------------------------------------
# Excepciones de conexión a servicios externos
# ------------------------------------------------------------

class ServiceConnectionError(AppException):
    """
    Error al conectar con un servicio externo.
    Ej: Pinecone, Redis, Google Sheets, Ollama.
    """
    pass


class PineconeError(ServiceConnectionError):
    """Error específico de Pinecone."""
    pass


class RedisError(ServiceConnectionError):
    """Error específico de Redis."""
    pass


class GoogleSheetsError(ServiceConnectionError):
    """Error específico de Google Sheets."""
    pass


class OllamaError(ServiceConnectionError):
    """Error específico de Ollama (modelos de lenguaje)."""
    pass


# ------------------------------------------------------------
# Excepciones de validación de datos
# ------------------------------------------------------------

class DataValidationError(AppException):
    """
    Error de validación de datos (Pydantic o lógica de negocio).
    Ej: campos inválidos, datos corruptos, etc.
    """
    pass


# ------------------------------------------------------------
# Excepciones del módulo RAG
# ------------------------------------------------------------

class RAGError(AppException):
    """
    Error durante la recuperación o indexación de documentos (RAG).
    """
    pass


class DocumentNotFoundError(RAGError):
    """El documento solicitado no existe en el índice."""
    pass


class IndexingError(RAGError):
    """Error al indexar un documento en Pinecone."""
    pass


# ------------------------------------------------------------
# Excepciones del módulo Inventory
# ------------------------------------------------------------

class InventoryError(AppException):
    """
    Error al interactuar con el inventario (Google Sheets o caché).
    """
    pass


class ProductNotFoundError(InventoryError):
    """El medicamento buscado no existe en el inventario."""
    pass


# ------------------------------------------------------------
# Excepciones del módulo Agent
# ------------------------------------------------------------

class AgentError(AppException):
    """
    Error durante la ejecución del agente (LangGraph, nodos).
    """
    pass


class ResponseGenerationError(AgentError):
    """Error al generar la respuesta con el LLM."""
    pass


class MemoryError(AgentError):
    """Error al leer o escribir en la memoria conversacional."""
    pass


# ------------------------------------------------------------
# Excepciones de recursos no encontrados (genéricas)
# ------------------------------------------------------------

class NotFoundError(AppException):
    """
    Recurso no encontrado (genérico).
    Ej: sesión no encontrada, ítem no encontrado.
    """
    pass
