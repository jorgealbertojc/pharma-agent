# tests/unit/core/test_exceptions.py
"""
Tests unitarios para las excepciones personalizadas.

Verifica la jerarquía de herencia, el constructor con mensaje y detalles,
y la representación en string de las excepciones.
"""

import pytest

from app.core.exceptions import (
    AppException,
    ConfigurationError,
    ServiceConnectionError,
    PineconeError,
    RedisError,
    GoogleSheetsError,
    OllamaError,
    DataValidationError,
    RAGError,
    DocumentNotFoundError,
    IndexingError,
    InventoryError,
    ProductNotFoundError,
    AgentError,
    ResponseGenerationError,
    MemoryError,
    NotFoundError,
)


class TestAppException:
    """Pruebas para la excepción base AppException."""

    def test_exception_with_message_only(self) -> None:
        """
        Given: Un mensaje de error.
        When: Se lanza AppException con solo el mensaje.
        Then: El mensaje se guarda y __str__ devuelve solo el mensaje.
        """
        # Given
        msg = "Error general"

        # When
        with pytest.raises(AppException) as exc_info:
            raise AppException(msg)

        # Then
        assert exc_info.value.message == msg
        assert exc_info.value.details is None
        assert str(exc_info.value) == msg

    def test_exception_with_details(self) -> None:
        """
        Given: Un mensaje y detalles.
        When: Se lanza AppException con ambos.
        Then: El mensaje y detalles se guardan, y __str__ los incluye.
        """
        # Given
        msg = "Error crítico"
        details = "Detalles adicionales del error"

        # When
        with pytest.raises(AppException) as exc_info:
            raise AppException(msg, details)

        # Then
        assert exc_info.value.message == msg
        assert exc_info.value.details == details
        assert str(exc_info.value) == f"{msg} (detalles: {details})"


class TestSpecificExceptions:
    """Pruebas para las excepciones específicas (herencia y captura)."""

    def test_configuration_error_inheritance(self) -> None:
        """
        Given: ConfigurationError.
        When: Se lanza y se captura como AppException.
        Then: La captura funciona por herencia.
        """
        # Given
        msg = "Configuración inválida"

        # When / Then
        with pytest.raises(AppException) as exc_info:
            raise ConfigurationError(msg)
        assert exc_info.value.message == msg
        assert isinstance(exc_info.value, ConfigurationError)
        assert isinstance(exc_info.value, AppException)

    def test_pinecone_error_inheritance(self) -> None:
        """
        Given: PineconeError.
        When: Se lanza y se captura como ServiceConnectionError y AppException.
        Then: La jerarquía de herencia funciona.
        """
        msg = "Error de conexión a Pinecone"
        with pytest.raises(ServiceConnectionError) as exc_info:
            raise PineconeError(msg)
        assert isinstance(exc_info.value, PineconeError)
        assert isinstance(exc_info.value, ServiceConnectionError)
        assert isinstance(exc_info.value, AppException)

    def test_redis_error_inheritance(self) -> None:
        """Verifica que RedisError herede correctamente."""
        msg = "Error de Redis"
        with pytest.raises(ServiceConnectionError):
            raise RedisError(msg)

    def test_google_sheets_error_inheritance(self) -> None:
        """Verifica que GoogleSheetsError herede correctamente."""
        msg = "Error de Google Sheets"
        with pytest.raises(ServiceConnectionError):
            raise GoogleSheetsError(msg)

    def test_ollama_error_inheritance(self) -> None:
        """Verifica que OllamaError herede correctamente."""
        msg = "Error de Ollama"
        with pytest.raises(ServiceConnectionError):
            raise OllamaError(msg)

    def test_data_validation_error_inheritance(self) -> None:
        """Verifica que DataValidationError herede de AppException."""
        msg = "Datos inválidos"
        with pytest.raises(AppException):
            raise DataValidationError(msg)

    def test_rag_error_inheritance(self) -> None:
        """Verifica que RAGError y sus subclases hereden correctamente."""
        msg = "Error de RAG"
        with pytest.raises(RAGError):
            raise DocumentNotFoundError(msg)
        with pytest.raises(RAGError):
            raise IndexingError(msg)

    def test_inventory_error_inheritance(self) -> None:
        """Verifica que InventoryError y ProductNotFoundError hereden correctamente."""
        msg = "Error de inventario"
        with pytest.raises(InventoryError):
            raise ProductNotFoundError(msg)

    def test_agent_error_inheritance(self) -> None:
        """Verifica que AgentError y sus subclases hereden correctamente."""
        msg = "Error del agente"
        with pytest.raises(AgentError):
            raise ResponseGenerationError(msg)
        with pytest.raises(AgentError):
            raise MemoryError(msg)

    def test_not_found_error_inheritance(self) -> None:
        """Verifica que NotFoundError herede de AppException."""
        msg = "Recurso no encontrado"
        with pytest.raises(AppException):
            raise NotFoundError(msg)
