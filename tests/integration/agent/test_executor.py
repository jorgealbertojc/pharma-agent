"""
Tests de integración para el ejecutor del agente.

Requiere:
- Contenedores de Docker levantados (Ollama, Pinecone, Redis).
- Pinecone poblado con el libro de farmacia (documentos indexados).
- Google Sheets configurado con credenciales (para inventario).
- Estos tests realizan llamadas reales a servicios externos, consumiendo tokens y cuotas de API.
"""

import pytest
from unittest.mock import patch
from io import StringIO
import sys

from src.agent.executor import AgentExecutor


@pytest.fixture(scope="class", autouse=True)
def executor_setup(request):
    """Fixture de clase que inicializa el executor una sola vez."""
    request.cls.executor = AgentExecutor()


@pytest.mark.usefixtures("executor_setup")
class TestAgentExecutor:
    """Suite de tests para AgentExecutor (sin mocks de servicios externos)."""

    def test_executor_initialization(self):
        """
        Given: La clase AgentExecutor.
        When: Se crea una instancia.
        Then: Se inicializan correctamente las dependencias (retriever, inventory, graph).
        """
        executor = self.executor
        assert executor.graph is not None
        assert executor.nodes is not None
        assert executor.formatter is not None
        # El estado debe ser None inicialmente, pero _process_question lo inicializará
        assert executor.state is None

    def test_process_question_returns_response(self):
        """
        Given: Un executor con servicios reales y estado None.
        When: Se procesa una pregunta válida.
        Then: Se genera una respuesta (final_answer) y se actualiza el estado.
        """
        executor = self.executor
        question = "¿Qué es el ibuprofeno?"

        # When
        executor._process_question(question)

        # Then
        assert executor.state is not None
        assert executor.state.get("final_answer") is not None
        assert len(executor.state.get("final_answer", "")) > 0
        assert len(executor.state.get("messages", [])) >= 2

    def test_process_question_empty_input(self):
        """
        Given: Un executor con estado inicializado.
        When: Se procesa una pregunta vacía.
        Then: El método maneja la entrada vacía sin error y no genera respuesta.
        """
        executor = self.executor
        # Inicializar estado manualmente
        from src.agent.state import create_initial_state
        executor.state = create_initial_state("")
        initial_messages_count = len(executor.state.get("messages", []))

        # When
        executor._process_question("")

        # Then
        # El estado no debería cambiar (no se añade mensaje, no se genera respuesta)
        assert len(executor.state.get("messages", [])) == initial_messages_count
        # No debería haber final_answer
        assert executor.state.get("final_answer") is None

    def test_run_loop_exit_command(self):
        """
        Given: Un executor listo para ejecutar.
        When: Se ejecuta el bucle y se ingresa el comando "salir".
        Then: El bucle termina sin errores.
        """
        executor = self.executor
        with patch('builtins.input', return_value='salir'):
            captured_output = StringIO()
            sys.stdout = captured_output
            try:
                executor.run()
            finally:
                sys.stdout = sys.__stdout__

            assert "👋 ¡Hasta luego!" in captured_output.getvalue()

    def test_run_loop_empty_input_is_ignored(self):
        """
        Given: Un executor listo para ejecutar.
        When: Se ingresa una línea vacía y luego "salir".
        Then: La línea vacía se ignora y el bucle continúa.
        """
        executor = self.executor
        inputs = iter(['', 'salir'])
        with patch('builtins.input', side_effect=lambda _: next(inputs)):
            captured_output = StringIO()
            sys.stdout = captured_output
            try:
                executor.run()
            finally:
                sys.stdout = sys.__stdout__

            assert "👋 ¡Hasta luego!" in captured_output.getvalue()

    def test_run_loop_keyboard_interrupt_exits(self):
        """
        Given: Un executor listo para ejecutar.
        When: Se produce un KeyboardInterrupt durante el bucle.
        Then: El bucle termina mostrando el mensaje de interrupción.
        """
        executor = self.executor
        with patch('builtins.input', side_effect=KeyboardInterrupt):
            captured_output = StringIO()
            sys.stdout = captured_output
            try:
                executor.run()
            finally:
                sys.stdout = sys.__stdout__

            assert "Interrupción detectada" in captured_output.getvalue()

    def test_run_loop_error_handling(self):
        """
        Given: Un executor con un error simulado en el procesamiento.
        When: Se ingresa una pregunta que causa un error en el grafo.
        Then: El error se captura y se muestra un mensaje, y el bucle continúa.
        """
        executor = self.executor
        with patch.object(executor, '_process_question', side_effect=Exception("Error simulado")):
            inputs = iter(['pregunta', 'salir'])
            with patch('builtins.input', side_effect=lambda _: next(inputs)):
                captured_output = StringIO()
                sys.stdout = captured_output
                try:
                    executor.run()
                finally:
                    sys.stdout = sys.__stdout__

                assert "❌ Ocurrió un error" in captured_output.getvalue()
                assert "Error simulado" in captured_output.getvalue()
                assert "👋 ¡Hasta luego!" in captured_output.getvalue()
