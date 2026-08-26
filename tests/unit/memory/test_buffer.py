# tests/unit/memory/test_buffer.py
"""
Tests unitarios para la memoria BufferMemory.

Verifica:
- Inicialización con y sin límites.
- Adición de mensajes (roles válidos e inválidos).
- Recuperación de mensajes y contexto.
- Truncamiento por número de mensajes y tokens.
- Cálculo de tokens estimados.
- Limpieza del historial.
"""

import pytest

from src.memory.buffer import BufferMemory


class TestBufferMemory:
    """Suite de tests para BufferMemory."""

    def test_init_without_limits(self) -> None:
        """
        Given: Una instancia de BufferMemory sin límites.
        When: Se añaden mensajes.
        Then: Todos los mensajes se retienen indefinidamente.
        """
        # Given
        memory = BufferMemory()

        # When
        memory.add_message("user", "Hola")
        memory.add_message("assistant", "¿Cómo estás?")
        memory.add_message("user", "Bien, gracias")

        # Then
        messages = memory.get_messages()
        assert len(messages) == 3
        assert messages[0] == {"role": "user", "content": "Hola"}
        assert messages[1] == {"role": "assistant", "content": "¿Cómo estás?"}
        assert messages[2] == {"role": "user", "content": "Bien, gracias"}

    def test_init_with_max_messages(self) -> None:
        """
        Given: BufferMemory con max_messages=2.
        When: Se añaden 3 mensajes.
        Then: Solo se retienen los últimos 2.
        """
        # Given
        memory = BufferMemory(max_messages=2)

        # When
        memory.add_message("user", "Primero")
        memory.add_message("assistant", "Segundo")
        memory.add_message("user", "Tercero")

        # Then
        messages = memory.get_messages()
        assert len(messages) == 2
        assert messages[0] == {"role": "assistant", "content": "Segundo"}
        assert messages[1] == {"role": "user", "content": "Tercero"}

    def test_init_with_max_tokens(self) -> None:
        """
        Given: BufferMemory con max_tokens=10 (aprox 40 caracteres).
        When: Se añaden mensajes que superan el límite.
        Then: Se eliminan los mensajes más antiguos hasta cumplir el límite.
        """
        # Given
        memory = BufferMemory(max_tokens=10)

        # Cuando el token estimado es len//4, 10 tokens ≈ 40 caracteres.
        # Mensaje 1: 20 chars → 5 tokens
        # Mensaje 2: 30 chars → 7 tokens → total 12 > 10, se elimina el más antiguo.
        memory.add_message("user", "Mensaje de 20 chars.")  # 21 chars
        memory.add_message("assistant", "Este mensaje tiene 30 chars.")  # 31 chars

        # Then
        messages = memory.get_messages()
        assert len(messages) == 1
        assert messages[0]["content"] == "Este mensaje tiene 30 chars."

    def test_init_with_both_limits(self) -> None:
        """
        Given: BufferMemory con max_messages=3 y max_tokens=10.
        When: Se añaden mensajes que exceden ambos límites.
        Then: Se aplica primero max_messages y luego max_tokens.
        """
        # Given
        memory = BufferMemory(max_messages=3, max_tokens=10)

        # Añadir 4 mensajes con tamaños crecientes
        memory.add_message("user", "a" * 5)   # 1 token aprox
        memory.add_message("assistant", "b" * 20) # 5 tokens
        memory.add_message("user", "c" * 30)  # 7 tokens
        memory.add_message("assistant", "d" * 40) # 10 tokens

        # Primero se queda con los últimos 3 (mensajes 2,3,4)
        # Luego se aplica límite de tokens: total ≈ (5+7+10)=22 > 10 → elimina antiguos
        # Debería quedarse solo con el último (10 tokens, justo en el límite)
        messages = memory.get_messages()
        assert len(messages) == 1
        assert messages[0]["content"] == "d" * 40

    def test_add_message_invalid_role(self) -> None:
        """
        Given: Una instancia de BufferMemory.
        When: Se intenta añadir un mensaje con rol inválido.
        Then: Se lanza ValueError.
        """
        memory = BufferMemory()
        with pytest.raises(ValueError, match="Rol inválido: invalid"):
            memory.add_message("invalid", "contenido")

    def test_get_messages_returns_copy(self) -> None:
        """
        Given: BufferMemory con un mensaje.
        When: Se obtienen mensajes y se modifica la lista devuelta.
        Then: El historial interno no se modifica.
        """
        # Given
        memory = BufferMemory()
        memory.add_message("user", "mensaje")

        # When
        messages = memory.get_messages()
        messages.append({"role": "assistant", "content": "añadido"})

        # Then
        internal = memory.get_messages()
        assert len(internal) == 1
        assert internal[0]["content"] == "mensaje"

    def test_get_context(self) -> None:
        """
        Given: BufferMemory con varios mensajes.
        When: Se llama a get_context().
        Then: Devuelve el formato esperado con "Usuario:" y "Asistente:".
        """
        # Given
        memory = BufferMemory()
        memory.add_message("user", "Hola")
        memory.add_message("assistant", "¿Cómo estás?")
        memory.add_message("user", "Bien")

        # When
        context = memory.get_context()

        # Then
        expected = "Usuario: Hola\nAsistente: ¿Cómo estás?\nUsuario: Bien"
        assert context == expected

    def test_get_context_empty(self) -> None:
        """
        Given: BufferMemory sin mensajes.
        When: Se llama a get_context().
        Then: Devuelve cadena vacía.
        """
        memory = BufferMemory()
        assert memory.get_context() == ""

    def test_clear(self) -> None:
        """
        Given: BufferMemory con mensajes.
        When: Se llama a clear().
        Then: El historial queda vacío.
        """
        # Given
        memory = BufferMemory()
        memory.add_message("user", "Mensaje")
        memory.add_message("assistant", "Otro")

        # When
        memory.clear()

        # Then
        assert memory.get_messages() == []
        assert memory.get_context() == ""
        assert memory.get_token_count() == 0

    def test_get_token_count(self) -> None:
        """
        Given: BufferMemory con mensajes de diferentes longitudes.
        When: Se calcula el token count.
        Then: El resultado es la suma de len(content)//4 para cada mensaje.
        """
        # Given
        memory = BufferMemory()
        memory.add_message("user", "abc")       # 3//4 = 0
        memory.add_message("assistant", "abcd") # 4//4 = 1
        memory.add_message("user", "abcdefgh")  # 8//4 = 2

        # When
        count = memory.get_token_count()

        # Then
        assert count == 3  # 0 + 1 + 2
