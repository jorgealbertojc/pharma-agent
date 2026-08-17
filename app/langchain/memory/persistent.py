# app/langchain/memory/persistent.py
"""
Implementación de memoria persistente usando Redis como backend.

Esta clase implementa la interfaz BaseMemory almacenando los mensajes
en Redis de forma duradera. La sesión se identifica por un session_id,
lo que permite múltiples conversaciones simultáneas.

El cliente Redis se inyecta desde fuera para mantener el desacoplamiento.
"""

from typing import List, Dict, Optional

from redis import Redis

from .base import BaseMemory
from .utils import format_messages, count_tokens_approx
from app.langchain.redis import RedisChatHistory
from langchain_core.messages import HumanMessage, AIMessage, BaseMessage


class PersistentMemory(BaseMemory):
    """
    Memoria persistente con Redis.

    Attributes:
        session_id: Identificador único de la sesión.
        history: Instancia de RedisChatHistory (LangChain).
        max_tokens: Límite de tokens opcional (trunca mensajes antiguos).
    """

    def __init__(
        self,
        session_id: str,
        redis_client: Redis,
        ttl: Optional[int] = None,
        max_tokens: Optional[int] = None,
    ):
        """
        Inicializa la memoria persistente.

        Args:
            session_id: Identificador único de la sesión.
            redis_client: Cliente Redis ya conectado.
            ttl: Tiempo de vida en segundos (None = sin expiración).
            max_tokens: Máximo de tokens a retener (None = sin límite).
        """
        self.session_id = session_id
        self.redis_client = redis_client
        self.ttl = ttl
        self.max_tokens = max_tokens
        self.history = RedisChatHistory(
            session_id=session_id,
            redis_client=redis_client,
            ttl=ttl,
        )

    def add_message(self, role: str, content: str) -> None:
        """
        Añade un mensaje al historial persistente.

        Args:
            role: 'user' o 'assistant'.
            content: Texto del mensaje.

        Raises:
            ValueError: Si el rol no es válido.
        """
        if role not in ("user", "assistant"):
            raise ValueError(f"Rol inválido: {role}. Debe ser 'user' o 'assistant'.")

        msg: BaseMessage
        if role == "user":
            msg = HumanMessage(content=content)
        else:
            msg = AIMessage(content=content)

        self.history.add_message(msg)

        # Aplicar límite de tokens si está configurado
        if self.max_tokens is not None:
            self._truncate_by_tokens()

    def get_messages(self) -> List[Dict[str, str]]:
        """
        Recupera todos los mensajes del historial.

        Returns:
            Lista de diccionarios con 'role' y 'content'.
        """
        messages = self.history.get_messages()
        return [
            {"role": "user" if isinstance(m, HumanMessage) else "assistant", "content": m.content}
            for m in messages
        ]

    def get_context(self) -> str:
        """
        Retorna el historial formateado como texto para inyectar en el prompt.

        Returns:
            Texto con formato "Usuario: ...\nAsistente: ..."
        """
        messages = self.get_messages()
        return format_messages(messages, include_roles=True)

    def clear(self) -> None:
        """Elimina todo el historial de la sesión en Redis."""
        self.history.clear()

    def get_token_count(self) -> int:
        """
        Retorna el total aproximado de tokens en el historial actual.

        Uses:
            count_tokens_approx (estimación 4 caracteres ≈ 1 token).
        """
        messages = self.get_messages()
        return sum(count_tokens_approx(msg["content"]) for msg in messages)

    def _truncate_by_tokens(self) -> None:
        """
        Elimina mensajes antiguos hasta que el total de tokens esté dentro del límite.
        """
        if self.max_tokens is None:
            return

        messages = self.history.get_messages()
        while messages and self.get_token_count() > self.max_tokens:
            # Eliminar el mensaje más antiguo (índice 0)
            self.redis_client.lpop(self.history.key)
            # Actualizar TTL si estaba configurado
            if self.ttl:
                self.redis_client.expire(self.history.key, self.ttl)
            # Recargar mensajes
            messages = self.history.get_messages()
