# tests/integration/memory/test_persistent.py
"""
Tests de integración para PersistentMemory (Redis).

Cada test crea su propia sesión (session_id único) y limpia los datos al finalizar,
evitando colisiones entre tests. Se usa inyección de dependencias: el cliente Redis
se obtiene desde la configuración global y se pasa al constructor.
"""

import json
import uuid

import pytest
import redis

from typing import Iterator

from app.core.config import settings
from app.memory.persistent import PersistentMemory


# ------------------------------------------------------------
# Fixtures
# ------------------------------------------------------------

@pytest.fixture(scope="function")
def redis_client() -> redis.Redis:
    """
    Retorna un cliente Redis conectado usando la configuración global.
    """
    return redis.Redis(
        host=settings.REDIS_HOST,
        port=settings.REDIS_PORT,
        db=settings.REDIS_DB_INDEX,
        decode_responses=True,  # Para obtener strings directamente
    )


@pytest.fixture(scope="function")
def session_id() -> str:
    """
    Genera un session_id único para cada test.
    """
    return f"test_{uuid.uuid4().hex[:8]}"


@pytest.fixture(scope="function")
def persistent_memory(redis_client: redis.Redis, session_id: str) -> Iterator[PersistentMemory]:
    """
    Crea una instancia de PersistentMemory sin límites de mensajes/tokens.
    La limpieza se realiza al final del test (clear automático).
    """
    memory = PersistentMemory(
        session_id=session_id,
        redis_client=redis_client,
        ttl=None,
        max_messages=None,
        max_tokens=None,
    )
    yield memory
    # Limpieza: borrar la clave de Redis
    redis_client.delete(memory._key)


# ------------------------------------------------------------
# Tests
# ------------------------------------------------------------

class TestPersistentMemory:
    """Suite de tests para PersistentMemory."""

    def test_add_and_get_messages(
        self,
        persistent_memory: PersistentMemory,
    ) -> None:
        """
        Given: Una memoria persistente vacía.
        When: Se añaden mensajes.
        Then: Se recuperan en el orden correcto.
        """
        # Given
        memory = persistent_memory

        # When
        memory.add_message("user", "Hola")
        memory.add_message("assistant", "¿Cómo estás?")
        memory.add_message("user", "Bien, ¿y tú?")

        # Then
        messages = memory.get_messages()
        assert len(messages) == 3
        assert messages[0] == {"role": "user", "content": "Hola"}
        assert messages[1] == {"role": "assistant", "content": "¿Cómo estás?"}
        assert messages[2] == {"role": "user", "content": "Bien, ¿y tú?"}

    def test_get_context_formats_correctly(
        self,
        persistent_memory: PersistentMemory,
    ) -> None:
        """
        Given: Una memoria con mensajes.
        When: Se llama a get_context().
        Then: Devuelve el formato esperado.
        """
        # Given
        memory = persistent_memory
        memory.add_message("user", "Hola")
        memory.add_message("assistant", "¿Cómo estás?")

        # When
        context = memory.get_context()

        # Then
        expected = "Usuario: Hola\nAsistente: ¿Cómo estás?"
        assert context == expected

    def test_max_messages_truncates(
        self,
        redis_client: redis.Redis,
        session_id: str,
    ) -> None:
        """
        Given: PersistentMemory con max_messages=2.
        When: Se añaden 3 mensajes.
        Then: Solo se retienen los últimos 2.
        """
        # Given
        memory = PersistentMemory(
            session_id=session_id,
            redis_client=redis_client,
            max_messages=2,
        )

        # When
        memory.add_message("user", "Primero")
        memory.add_message("assistant", "Segundo")
        memory.add_message("user", "Tercero")

        # Then
        messages = memory.get_messages()
        assert len(messages) == 2
        assert messages[0]["content"] == "Segundo"
        assert messages[1]["content"] == "Tercero"

        # Cleanup
        redis_client.delete(memory._key)

    def test_max_tokens_truncates(
        self,
        redis_client: redis.Redis,
        session_id: str,
    ) -> None:
        """
        Given: PersistentMemory con max_tokens=10 (≈40 caracteres).
        When: Se añaden mensajes que superan el límite.
        Then: Se eliminan los más antiguos hasta cumplir el límite.
        """
        # Given
        memory = PersistentMemory(
            session_id=session_id,
            redis_client=redis_client,
            max_tokens=10,
        )

        # When
        memory.add_message("user", "Mensaje1")          # 8 chars → 2 tokens
        memory.add_message("assistant", "Mensaje2 con más texto")  # 22 chars → 5 tokens
        memory.add_message("user", "Otro mensaje")      # 14 chars → 3 tokens
        # Total ≈ 10 tokens (2+5+3 = 10). Está justo en el límite, no debe truncar.
        messages = memory.get_messages()
        assert len(messages) == 3

        # Ahora añadimos uno más que desborda
        memory.add_message("assistant", "Este es un mensaje largo que excede el límite")  # 50 chars → 12 tokens
        # Ahora debe truncar hasta que el total sea ≤ 10 tokens.
        # Se espera que solo quede el último mensaje (12 tokens es >10, pero con solo
        # el último ya supera el límite, lo que significa que quedará vacío o solo
        # parcialmente. Como la heurística es len//4, el último tiene 50//4=12.5 -> 12 tokens,
        # que es >10, así que se eliminará y quedará vacío.
        # Pero en realidad, la lógica de truncamiento elimina hasta que el total sea <= max_tokens.
        # Si ningún mensaje cumple, se vacía la lista.
        messages_after = memory.get_messages()
        # El comportamiento esperado: como el último mensaje supera el límite, la lista queda vacía.
        assert len(messages_after) == 0

        # Cleanup
        redis_client.delete(memory._key)

    def test_ttl_is_set(
        self,
        redis_client: redis.Redis,
        session_id: str,
    ) -> None:
        """
        Given: PersistentMemory con ttl=60 segundos.
        When: Se añade un mensaje.
        Then: La clave de Redis tiene TTL configurado.
        """
        # Given
        memory = PersistentMemory(
            session_id=session_id,
            redis_client=redis_client,
            ttl=60,
        )

        # When
        memory.add_message("user", "Mensaje con TTL")

        # Then
        ttl = redis_client.ttl(memory._key)
        # El TTL debe ser un valor positivo (puede ser ligeramente menor por el tiempo transcurrido)
        assert 1 <= ttl <= 60

        # Cleanup
        redis_client.delete(memory._key)

    def test_clear_removes_all_messages(
        self,
        persistent_memory: PersistentMemory,
    ) -> None:
        """
        Given: Una memoria con mensajes.
        When: Se llama a clear().
        Then: El historial queda vacío.
        """
        # Given
        memory = persistent_memory
        memory.add_message("user", "Hola")
        memory.add_message("assistant", "Adiós")

        # When
        memory.clear()

        # Then
        assert memory.get_messages() == []
        assert memory.get_context() == ""
        assert memory.get_token_count() == 0

    def test_invalid_role_raises_error(
        self,
        persistent_memory: PersistentMemory,
    ) -> None:
        """
        Given: Una memoria persistente.
        When: Se intenta añadir un mensaje con rol inválido.
        Then: Se lanza ValueError.
        """
        memory = persistent_memory
        with pytest.raises(ValueError, match="Rol inválido: invalid"):
            memory.add_message("invalid", "contenido")

    def test_get_token_count(
        self,
        persistent_memory: PersistentMemory,
    ) -> None:
        """
        Given: Una memoria con mensajes de diferente longitud.
        When: Se calcula el token count.
        Then: El resultado es la suma de len(content)//4.
        """
        # Given
        memory = persistent_memory
        memory.add_message("user", "abc")        # 3//4 = 0
        memory.add_message("assistant", "abcd")  # 4//4 = 1
        memory.add_message("user", "abcdefgh")   # 8//4 = 2

        # When
        count = memory.get_token_count()

        # Then
        assert count == 3

    def test_persistence_across_instances(
        self,
        redis_client: redis.Redis,
        session_id: str,
    ) -> None:
        """
        Given: Una sesión con mensajes guardados en Redis.
        When: Se crea una nueva instancia de PersistentMemory con el mismo session_id.
        Then: Los mensajes se recuperan correctamente.
        """
        # Given
        memory1 = PersistentMemory(
            session_id=session_id,
            redis_client=redis_client,
        )
        memory1.add_message("user", "Hola")
        memory1.add_message("assistant", "¿Cómo estás?")

        # When
        memory2 = PersistentMemory(
            session_id=session_id,
            redis_client=redis_client,
        )

        # Then
        messages = memory2.get_messages()
        assert len(messages) == 2
        assert messages[0]["content"] == "Hola"
        assert messages[1]["content"] == "¿Cómo estás?"

        # Cleanup
        redis_client.delete(memory1._key)
        redis_client.delete(memory2._key)  # misma clave
