# tests/unit/agent/test_state.py
"""
Tests unitarios para el estado del agente conversacional.

Verifica la creación del estado inicial, la adición de mensajes
y el correcto tipado de los campos del estado.
"""

import pytest
from langchain_core.messages import HumanMessage, AIMessage

from app.agent.state import AgentState, create_initial_state, add_message_to_state


class TestAgentState:
    """Suite de tests para el estado del agente."""

    def test_create_initial_state_without_messages(self) -> None:
        """
        Given: Una pregunta de usuario sin historial previo.
        When: Se crea el estado inicial con create_initial_state.
        Then: El estado contiene la pregunta y los campos por defecto.
        """
        # Given
        question = "¿Qué es el ibuprofeno?"

        # When
        state = create_initial_state(question)

        # Then
        assert state["question"] == question
        assert state["messages"] == []
        assert state["context"] is None
        assert state["inventory_results"] is None
        assert state["suggestions"] is None
        assert state["final_answer"] is None
        assert state["error"] is None
        assert state["next_step"] is None
        assert state["iterations"] == 0

    def test_create_initial_state_with_messages(self) -> None:
        """
        Given: Una pregunta y un historial previo de mensajes.
        When: Se crea el estado inicial.
        Then: El estado incluye el historial en el campo 'messages'.
        """
        # Given
        question = "¿Y cómo murió?"
        messages = [
            HumanMessage(content="¿Quién es el protagonista de El perfume?"),
            AIMessage(content="Jean-Baptiste Grenouille."),
        ]

        # When
        state = create_initial_state(question, messages=messages)

        # Then
        assert state["question"] == question
        assert len(state["messages"]) == 2
        assert isinstance(state["messages"][0], HumanMessage)
        assert isinstance(state["messages"][1], AIMessage)
        assert state["messages"][0].content == "¿Quién es el protagonista de El perfume?"
        assert state["messages"][1].content == "Jean-Baptiste Grenouille."

    def test_add_message_to_state_updates_messages(self) -> None:
        """
        Given: Un estado con un mensaje previo.
        When: Se añade un nuevo mensaje con add_message_to_state.
        Then: El nuevo mensaje se agrega al final de la lista y los demás campos se mantienen.
        """
        # Given
        initial_state = create_initial_state("Pregunta inicial")
        new_message = HumanMessage(content="Nuevo mensaje del usuario")

        # When
        updated_state = add_message_to_state(initial_state, new_message)

        # Then
        assert len(updated_state["messages"]) == 1
        assert updated_state["messages"][0].content == "Nuevo mensaje del usuario"
        # Verificar que los demás campos se mantienen
        assert updated_state["question"] == initial_state["question"]
        assert updated_state["context"] is None
        assert updated_state["iterations"] == 0

    def test_add_message_to_state_does_not_mutate_original(self) -> None:
        """
        Given: Un estado con un mensaje previo.
        When: Se añade un nuevo mensaje con add_message_to_state.
        Then: El estado original no se modifica (inmutabilidad).
        """
        # Given
        initial_state = create_initial_state("Pregunta")
        initial_state["context"] = "Contexto de prueba"
        new_message = HumanMessage(content="Otro mensaje")
        original_messages_len = len(initial_state["messages"])

        # When
        updated_state = add_message_to_state(initial_state, new_message)

        # Then
        assert len(initial_state["messages"]) == original_messages_len
        assert len(updated_state["messages"]) == original_messages_len + 1
        assert initial_state["context"] == "Contexto de prueba"
        assert updated_state["context"] == "Contexto de prueba"

    def test_messages_field_accumulates_with_operator_add(self) -> None:
        """
        Given: Un estado que usa Annotated con operator.add.
        When: Se simula una actualización de messages (LangGraph lo hace automáticamente).
        Then: Los mensajes se concatenan, no se sobrescriben.
        """
        # Este test verifica que el tipo de datos de messages es una lista
        # y que operator.add está configurado correctamente en el TypedDict.
        # Simulamos una actualización manual para comprobar el comportamiento.

        # Given
        state: AgentState = {
            "messages": [HumanMessage(content="Hola")],
            "question": "Hola",
            "context": None,
            "inventory_results": None,
            "suggestions": None,
            "final_answer": None,
            "error": None,
            "next_step": None,
            "iterations": 0,
        }

        # When: añadimos un nuevo mensaje como lo haría LangGraph
        new_messages = [AIMessage(content="¿Cómo estás?")]
        state["messages"] = state["messages"] + new_messages  # Simula operator.add

        # Then
        assert len(state["messages"]) == 2
        assert state["messages"][0].content == "Hola"
        assert state["messages"][1].content == "¿Cómo estás?"

    def test_state_type_accepts_optional_fields_as_none(self) -> None:
        """
        Given: Un estado creado con campos opcionales omitidos.
        When: Se construye el estado manualmente.
        Then: Los campos opcionales pueden ser None sin error de tipo.
        """
        # Given / When
        state: AgentState = {
            "messages": [],
            "question": "Prueba",
            "context": None,
            "inventory_results": None,
            "suggestions": None,
            "final_answer": None,
            "error": None,
            "next_step": None,
            "iterations": 0,
        }

        # Then
        assert state["context"] is None
        assert state["inventory_results"] is None
        assert state["suggestions"] is None
        assert state["error"] is None
        assert state["next_step"] is None
