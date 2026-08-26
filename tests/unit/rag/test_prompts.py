"""
Tests unitarios para el gestor de prompts (RAGPrompt).

Estos tests son autónomos y no requieren conexión a Pinecone ni a Ollama,
ya que solo verifican la construcción y formateo de prompts.
"""

import pytest
from langchain_core.prompts import ChatPromptTemplate

from src.rag.prompts import RAGPrompt


class TestRAGPrompt:
    """Suite de tests para la clase RAGPrompt."""

    def test_default_prompt(self) -> None:
        """
        Given: Un RAGPrompt con configuración por defecto.
        When: Se construye un prompt con contexto y pregunta.
        Then: El prompt contiene todos los elementos esperados.
        """
        # Given
        prompt_manager = RAGPrompt()
        context = "El ibuprofeno es un antiinflamatorio no esteroideo (AINE)."
        question = "¿Qué es el ibuprofeno?"

        # When
        result = prompt_manager.build_prompt(context, question)

        # Then
        assert "Eres un asistente farmacéutico profesional" in result
        assert "Contexto:\nEl ibuprofeno es un antiinflamatorio no esteroideo (AINE)." in result
        assert "Pregunta: ¿Qué es el ibuprofeno?" in result
        assert "Proporciona respuestas claras y concisas" in result

    def test_custom_prompt(self) -> None:
        """
        Given: Un RAGPrompt con valores personalizados.
        When: Se construye un prompt.
        Then: Se utilizan los valores personalizados en lugar de los predeterminados.
        """
        # Given
        custom_system = "Eres un asistente muy estricto."
        custom_context = "--- CONTEXTO ---\n{context}\n"
        custom_question = ">>> {question}\n"
        custom_format = "Responde en formato de viñetas."

        prompt_manager = RAGPrompt(
            system_prompt=custom_system,
            context_template=custom_context,
            question_template=custom_question,
            format_instructions=custom_format,
        )
        context = "El paracetamol es un analgésico."
        question = "Dosis máxima."

        # When
        result = prompt_manager.build_prompt(context, question)

        # Then
        assert custom_system in result
        assert "--- CONTEXTO ---\nEl paracetamol es un analgésico." in result
        assert ">>> Dosis máxima." in result
        assert custom_format in result

    def test_empty_context(self) -> None:
        """
        Given: Un RAGPrompt con contexto vacío.
        When: Se construye el prompt.
        Then: El bloque de contexto no aparece en el prompt final.
        """
        # Given
        prompt_manager = RAGPrompt()
        question = "Pregunta sin contexto"

        # When
        result = prompt_manager.build_prompt("", question)

        # Then
        assert "Contexto:" not in result
        assert "Pregunta: Pregunta sin contexto" in result
        # Asegurar que el sistema y formato siguen presentes
        assert "Eres un asistente farmacéutico profesional" in result
        assert "Proporciona respuestas claras" in result

    def test_to_langchain_template(self) -> None:
        """
        Given: Un RAGPrompt con configuración por defecto.
        When: Se convierte a ChatPromptTemplate de LangChain.
        Then: El objeto resultante es un ChatPromptTemplate válido
              y contiene los placeholders esperados.
        """
        # Given
        prompt_manager = RAGPrompt()

        # When
        template = prompt_manager.to_langchain_template()

        # Then
        assert isinstance(template, ChatPromptTemplate)
        # Los placeholders deben ser 'context' y 'question'
        input_vars = template.input_variables
        assert "context" in input_vars
        assert "question" in input_vars

        # Opcional: verificar que los mensajes contienen los placeholders
        messages = template.messages
        # El sistema no debe tener placeholders
        assert "{context}" not in messages[0].prompt.template
        assert "{question}" not in messages[0].prompt.template
        # El mensaje humano sí debe tenerlos
        assert "{context}" in messages[1].prompt.template
        assert "{question}" in messages[1].prompt.template
