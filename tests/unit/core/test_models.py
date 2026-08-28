# tests/unit/core/test_models.py
"""
Tests unitarios para los modelos de datos centrales.

Verifica la creación y validación de QueryRequest, AgentResponse y ErrorResponse.
"""

import pytest
from pydantic import ValidationError

from src.core.models import QueryRequest, AgentResponse, ErrorResponse


class TestQueryRequest:
    """Pruebas para el modelo QueryRequest."""

    def test_valid_question_only(self) -> None:
        """
        Given: Una pregunta válida sin session_id.
        When: Se crea un QueryRequest.
        Then: El objeto se crea correctamente y session_id es None.
        """
        # Given
        question = "¿Qué es el ibuprofeno?"

        # When
        req = QueryRequest(question=question)

        # Then
        assert req.question == question
        assert req.session_id is None

    def test_valid_with_session_id(self) -> None:
        """
        Given: Una pregunta y un session_id.
        When: Se crea un QueryRequest.
        Then: Ambos campos se asignan correctamente.
        """
        # Given
        question = "¿Cuál es la dosis?"
        session_id = "session-123"

        # When
        req = QueryRequest(question=question, session_id=session_id)

        # Then
        assert req.question == question
        assert req.session_id == session_id

    def test_empty_question_raises_validation_error(self) -> None:
        """
        Given: Una pregunta vacía.
        When: Se crea un QueryRequest.
        Then: Se lanza ValidationError porque question tiene min_length=1.
        """
        # Given
        question = ""

        # When / Then
        with pytest.raises(ValidationError) as exc_info:
            QueryRequest(question=question)

        # Verificar que el error menciona "question"
        assert "question" in str(exc_info.value).lower()

    def test_whitespace_question_raises_validation_error(self) -> None:
        """
        Given: Una pregunta con solo espacios en blanco.
        When: Se crea un QueryRequest.
        Then: Se lanza ValidationError (min_length=1).
        """
        # Given
        question = "   "

        # When / Then
        with pytest.raises(ValidationError):
            QueryRequest(question=question)


class TestAgentResponse:
    """Pruebas para el modelo AgentResponse."""

    def test_minimal_response(self) -> None:
        """
        Given: Solo el campo obligatorio 'answer'.
        When: Se crea un AgentResponse.
        Then: El objeto se crea correctamente, los demás campos son None.
        """
        # Given
        answer = "El ibuprofeno es un AINE."

        # When
        resp = AgentResponse(answer=answer)

        # Then
        assert resp.answer == answer
        assert resp.sources is None
        assert resp.suggestions is None
        assert resp.inventory_results is None
        assert resp.error is None

    def test_full_response(self) -> None:
        """
        Given: Todos los campos.
        When: Se crea un AgentResponse.
        Then: Todos los campos se asignan correctamente.
        """
        # Given
        answer = "Respuesta completa."
        sources = ["Fuente 1", "Fuente 2"]
        suggestions = "Sugerencia: tomar con agua."
        inventory_results = [{"producto": "Ibuprofeno", "stock": 10}]
        error = None

        # When
        resp = AgentResponse(
            answer=answer,
            sources=sources,
            suggestions=suggestions,
            inventory_results=inventory_results,
            error=error,
        )

        # Then
        assert resp.answer == answer
        assert resp.sources == sources
        assert resp.suggestions == suggestions
        assert resp.inventory_results == inventory_results
        assert resp.error is None

    def test_error_message_handled(self) -> None:
        """
        Given: Una respuesta con error.
        When: Se crea un AgentResponse.
        Then: El error se guarda en el campo correspondiente.
        """
        # Given
        answer = "No se pudo procesar la consulta."
        error = "Timeout al consultar Pinecone."

        # When
        resp = AgentResponse(answer=answer, error=error)

        # Then
        assert resp.answer == answer
        assert resp.error == error


class TestErrorResponse:
    """Pruebas para el modelo ErrorResponse."""

    def test_minimal_error_response(self) -> None:
        """
        Given: Solo el campo obligatorio 'error'.
        When: Se crea un ErrorResponse.
        Then: El objeto se crea correctamente y details es None.
        """
        # Given
        error = "Not Found"

        # When
        err = ErrorResponse(error=error)

        # Then
        assert err.error == error
        assert err.details is None

    def test_error_response_with_details(self) -> None:
        """
        Given: 'error' y 'details'.
        When: Se crea un ErrorResponse.
        Then: Ambos campos se asignan correctamente.
        """
        # Given
        error = "Validation failed"
        details = "El campo 'question' no puede estar vacío."

        # When
        err = ErrorResponse(error=error, details=details)

        # Then
        assert err.error == error
        assert err.details == details
