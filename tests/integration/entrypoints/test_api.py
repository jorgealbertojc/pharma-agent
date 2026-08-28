# tests/integration/entrypoints/test_api.py
"""
Tests de integración para la API REST del agente farmacéutico.

Requiere:
- Contenedores de Docker levantados (Ollama, Pinecone, Redis).
- Pinecone poblado con el libro de farmacia (documentos indexados).
- Google Sheets configurado con credenciales (para inventario).
- Estos tests realizan llamadas reales a servicios externos, consumiendo tokens y cuotas de API.
"""

import pytest
from fastapi.testclient import TestClient
from app.entrypoints.api import app, get_executor


@pytest.fixture(scope="function")
def client() -> TestClient:
    """
    Crea un cliente de prueba para la API.

    Reinicia el estado del executor antes de cada test para evitar interferencias.
    """
    # Obtener el executor y reiniciar su estado
    executor = get_executor()
    executor.state = None  # Reiniciar estado para cada test
    return TestClient(app)


class TestAPI:
    """Suite de tests de integración para la API."""

    def test_health_check(self, client: TestClient) -> None:
        """
        Given: La API en funcionamiento.
        When: Se hace GET a /health.
        Then: Retorna 200 con status ok y agent_ready true.
        """
        # When
        response = client.get("/health")

        # Then
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert data["agent_ready"] is True
        assert data["version"] == "0.0.4"

    def test_query_success(self, client: TestClient) -> None:
        """
        Given: Una pregunta válida.
        When: Se hace POST a /query.
        Then: Retorna 200 con una respuesta no vacía.
        """
        # Given
        payload = {"question": "¿Qué es el ibuprofeno?"}

        # When
        response = client.post("/query", json=payload)

        # Then
        assert response.status_code == 200
        data = response.json()
        assert "answer" in data
        assert len(data["answer"]) > 0
        # Puede tener sources, suggestions, inventory_results, error
        assert "error" not in data or data["error"] is None

    def test_query_with_session_id(self, client: TestClient) -> None:
        """
        Given: Una pregunta y un session_id.
        When: Se hace POST a /query.
        Then: Retorna 200 y la respuesta contiene la información esperada.
        """
        # Given
        payload = {
            "question": "¿Cuál es la dosis de paracetamol?",
            "session_id": "test-session-123",
        }

        # When
        response = client.post("/query", json=payload)

        # Then
        assert response.status_code == 200
        data = response.json()
        assert "answer" in data
        assert len(data["answer"]) > 0

    def test_query_empty_question_returns_400(self, client: TestClient) -> None:
        """
        Given: Una pregunta vacía.
        When: Se hace POST a /query.
        Then: Retorna 400 con error de validación.
        """
        # Given
        payload = {"question": ""}

        # When
        response = client.post("/query", json=payload)

        # Then
        assert response.status_code == 400
        data = response.json()
        # El mensaje puede ser "Error de validación" o el detalle del validador
        assert "detail" in data
        assert "validación" in data["detail"].lower() or "question" in data["detail"].lower()

    def test_query_whitespace_question_returns_400(self, client: TestClient) -> None:
        """
        Given: Una pregunta con solo espacios en blanco.
        When: Se hace POST a /query.
        Then: Retorna 400 con error de validación.
        """
        # Given
        payload = {"question": "   "}

        # When
        response = client.post("/query", json=payload)

        # Then
        assert response.status_code == 400
        data = response.json()
        assert "detail" in data

    def test_query_missing_question_returns_400(self, client: TestClient) -> None:
        """
        Given: Un payload sin el campo 'question'.
        When: Se hace POST a /query.
        Then: Retorna 422 (validación de Pydantic).
        """
        # Given
        payload = {}

        # When
        response = client.post("/query", json=payload)

        # Then
        assert response.status_code == 400  # FastAPI/Pydantic validation error
        data = response.json()
        assert "detail" in data
        # Verificar que el error menciona 'question'
        assert "validación" in data["detail"].lower() or "question" in data["detail"].lower()

    def test_query_handles_long_conversation(self, client: TestClient) -> None:
        """
        Given: Una conversación de múltiples preguntas.
        When: Se envían varias preguntas en secuencia.
        Then: El agente mantiene el contexto (historial) y responde coherentemente.
        """
        # Primera pregunta
        payload1 = {"question": "¿Qué es el ibuprofeno?"}
        response1 = client.post("/query", json=payload1)
        assert response1.status_code == 200
        answer1 = response1.json()["answer"]
        assert "ibuprofeno" in answer1.lower()

        # Segunda pregunta (referencia a la anterior)
        payload2 = {"question": "¿Cuáles son sus efectos secundarios?"}
        response2 = client.post("/query", json=payload2)
        assert response2.status_code == 200
        answer2 = response2.json()["answer"]
        # El agente debería haber entendido que "sus" se refiere a ibuprofeno
        # No podemos garantizar que mencione ibuprofeno, pero al menos debe responder
        assert len(answer2) > 0

        # Tercera pregunta (cambio de tema)
        payload3 = {"question": "¿Qué es el paracetamol?"}
        response3 = client.post("/query", json=payload3)
        assert response3.status_code == 200
        answer3 = response3.json()["answer"]
        assert "paracetamol" in answer3.lower()
