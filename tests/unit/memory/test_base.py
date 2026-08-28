"""
Tests unitarios para la clase abstracta BaseMemory.

Verifican:
- La correcta instanciación de subclases concretas.
- El formato del historial con y sin encabezado.
- El manejo del historial vacío.
"""

import pytest

from app.memory import BaseMemory


# ------------------------------------------------------------
# Helper: Subclase concreta para testear el método concreto
# ------------------------------------------------------------

class ConcreteMemory(BaseMemory):
    """Implementación mínima de BaseMemory para pruebas unitarias."""

    def __init__(self, messages: list[dict[str, str]] | None = None):
        self._messages = messages or []

    def add_message(self, role: str, content: str) -> None:
        self._messages.append({"role": role, "content": content})

    def get_messages(self) -> list[dict[str, str]]:
        return self._messages

    def get_context(self) -> str:
        # No usada en estos tests, pero requerida por la interfaz
        return ""

    def clear(self) -> None:
        self._messages = []

    def get_token_count(self) -> int:
        # No usada en estos tests, pero requerida por la interfaz
        return 0


# ------------------------------------------------------------
# Tests
# ------------------------------------------------------------

def test_cannot_instantiate_abstract_class() -> None:
    """
    Given: Una clase abstracta BaseMemory.
    When: Se intenta instanciar directamente.
    Then: Se lanza TypeError (por los métodos abstractos no implementados).
    """
    with pytest.raises(TypeError, match="Can't instantiate abstract class BaseMemory"):
        BaseMemory()  # type: ignore[abstract]


def test_format_for_prompt_with_messages() -> None:
    """
    Given: Una instancia con mensajes en el historial.
    When: Se llama a format_for_prompt().
    Then: Devuelve el texto formateado con encabezado y roles.
    """
    # Given
    history = ConcreteMemory([
        {"role": "user", "content": "Hola, ¿quién eres?"},
        {"role": "assistant", "content": "Soy un asistente farmacéutico."},
        {"role": "user", "content": "¿Qué es el ibuprofeno?"},
    ])

    # When
    result = history.format_for_prompt()

    # Then
    assert "## Historial de la conversación" in result
    assert "Usuario: Hola, ¿quién eres?" in result
    assert "Asistente: Soy un asistente farmacéutico." in result
    assert "Usuario: ¿Qué es el ibuprofeno?" in result


def test_format_for_prompt_without_system_header() -> None:
    """
    Given: Una instancia con mensajes en el historial.
    When: Se llama a format_for_prompt(include_system=False).
    Then: El encabezado "## Historial" no aparece.
    """
    # Given
    history = ConcreteMemory([
        {"role": "user", "content": "Hola"},
        {"role": "assistant", "content": "Adiós"},
    ])

    # When
    result = history.format_for_prompt(include_system=False)

    # Then
    assert "## Historial de la conversación" not in result
    assert "Usuario: Hola" in result
    assert "Asistente: Adiós" in result


def test_format_for_prompt_empty_history() -> None:
    """
    Given: Una instancia sin mensajes.
    When: Se llama a format_for_prompt().
    Then: Devuelve el mensaje "No hay historial previo."
    """
    # Given
    history = ConcreteMemory()

    # When
    result = history.format_for_prompt()

    # Then
    assert result == "No hay historial previo."
