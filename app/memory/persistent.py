# src/memory/persistent.py
"""
Memoria conversacional persistente usando Redis.

Esta clase almacena el historial de mensajes en Redis, lo que permite
que la conversación sobreviva a reinicios del proceso. El cliente
Redis se inyecta desde fuera para mantener el desacoplamiento.
"""

import json
from typing import List, Dict, Optional

import redis

from .base import BaseMemory


class PersistentMemory(BaseMemory):
    """
    Memoria conversacional persistente con Redis.

    Almacena el historial como una lista de Redis (RPUSH para añadir,
    LRANGE para recuperar, LPOP para truncar). Cada mensaje se guarda
    como un string JSON con los campos "role" y "content".

    Args:
        session_id: Identificador único de la sesión (ej. "user_123").
        redis_client: Cliente Redis ya conectado.
        ttl: Tiempo de vida en segundos (None = sin expiración).
        max_messages: Número máximo de mensajes a retener. None = sin límite.
        max_tokens: Máximo de tokens estimados. None = sin límite.
    """

    def __init__(
        self,
        session_id: str,
        redis_client: redis.Redis,
        ttl: Optional[int] = None,
        max_messages: Optional[int] = None,
        max_tokens: Optional[int] = None,
    ):
        self.session_id = session_id
        self.redis_client = redis_client
        self.ttl = ttl
        self.max_messages = max_messages
        self.max_tokens = max_tokens
        self._key = f"chat_history:{session_id}"

    def add_message(self, role: str, content: str) -> None:
        """
        Añade un mensaje al historial persistente.

        Args:
            role: 'user' o 'assistant'.
            content: Texto del mensaje.

        Raises:
            ValueError: Si el rol no es válido.
            redis.RedisError: Si hay un problema de conexión.
        """
        if role not in ("user", "assistant"):
            raise ValueError(f"Rol inválido: {role}. Debe ser 'user' o 'assistant'.")

        # Serializar el mensaje a JSON
        message = json.dumps({"role": role, "content": content})

        # Añadir al final de la lista
        self.redis_client.rpush(self._key, message)

        # Aplicar TTL si está configurado
        if self.ttl is not None:
            self.redis_client.expire(self._key, self.ttl)

        # Truncar según límites
        self._truncate()

    def get_messages(self) -> List[Dict[str, str]]:
        """
        Recupera todos los mensajes del historial en orden cronológico.

        Returns:
            Lista de diccionarios [{"role": "...", "content": "..."}, ...].

        Raises:
            redis.RedisError: Si hay un problema de conexión.
        """
        # Obtener todos los elementos de la lista (0 = primero, -1 = último)
        items = self.redis_client.lrange(self._key, 0, -1)

        messages = []
        for item in items:
            try:
                data = json.loads(item)
                # Validar que tenga los campos esperados
                if "role" in data and "content" in data:
                    messages.append(data)
                # Si el formato es inválido, lo saltamos silenciosamente
                # (podríamos loguearlo, pero para un laboratorio es aceptable)
            except json.JSONDecodeError:
                # Si el string no es JSON, lo saltamos
                continue

        return messages

    def get_context(self) -> str:
        """
        Retorna el historial formateado para inyectar en el prompt.

        El formato es:
            Usuario: <mensaje>
            Asistente: <mensaje>
            ...

        Returns:
            Cadena con los mensajes formateados.
            Si no hay mensajes, retorna una cadena vacía.
        """
        messages = self.get_messages()
        if not messages:
            return ""

        lines = []
        for msg in messages:
            role = "Usuario" if msg["role"] == "user" else "Asistente"
            lines.append(f"{role}: {msg['content']}")
        return "\n".join(lines)

    def clear(self) -> None:
        """Elimina todo el historial de la sesión en Redis."""
        self.redis_client.delete(self._key)

    def get_token_count(self) -> int:
        """
        Retorna una estimación del total de tokens en el historial.

        La heurística usada es 4 caracteres ≈ 1 token.
        Para obtener el conteo, recupera todos los mensajes y calcula
        la longitud total de los contenidos.

        Returns:
            Número estimado de tokens.
        """
        messages = self.get_messages()
        total_chars = sum(len(msg["content"]) for msg in messages)
        return total_chars // 4

    def _truncate(self) -> None:
        """
        Aplica los límites de mensajes y tokens usando operaciones atómicas de Redis.

        Elimina mensajes del principio de la lista (los más antiguos)
        hasta que se cumplan todos los límites.
        """
        # 1. Límite por número de mensajes
        if self.max_messages is not None:
            current_len = self.redis_client.llen(self._key)
            if current_len > self.max_messages:
                # Mantener solo los últimos max_messages elementos
                self.redis_client.ltrim(self._key, -self.max_messages, -1)

        # 2. Límite por tokens estimados
        if self.max_tokens is not None:
            # Mientras haya mensajes y el total estimado supere el límite,
            # eliminar el mensaje más antiguo (el primero de la lista)
            while self.get_token_count() > self.max_tokens:
                # Si la lista está vacía, salir
                if self.redis_client.llen(self._key) == 0:
                    break
                self.redis_client.lpop(self._key)
                # Actualizar TTL si es necesario (lo mantenemos en cada operación)
                if self.ttl is not None:
                    self.redis_client.expire(self._key, self.ttl)
