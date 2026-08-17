# app/langchain/redis/history.py
"""
Implementación de historial de chat persistente con Redis.

Esta clase proporciona un almacenamiento duradero para el historial
de conversaciones usando Redis como backend. Los mensajes se guardan
como una lista de strings JSON en una clave única por sesión.

Cumple con la interfaz BaseChatMessageHistory de LangChain.
"""

import json
from typing import List, Optional

from langchain_core.chat_history import BaseChatMessageHistory
from langchain_core.messages import BaseMessage
from redis import Redis

from .utils import serialize_message, deserialize_message, get_redis_key


class RedisChatHistory(BaseChatMessageHistory):
    """
    Historial de chat persistente en Redis.

    Cada sesión se identifica con un session_id. Los mensajes se almacenan
    en una lista de Redis (clave: chat_history:<session_id>).

    Args:
        session_id: Identificador único de la sesión (ej. 'user_123').
        redis_client: Instancia de Redis ya conectada.
        ttl: Tiempo de vida en segundos (None = sin expiración).
    """

    def __init__(
        self,
        session_id: str,
        redis_client: Redis,
        ttl: Optional[int] = None,
    ):
        self.session_id = session_id
        self.redis_client = redis_client
        self.ttl = ttl
        self.key = get_redis_key(session_id)

    def add_message(self, message: BaseMessage) -> None:
        """
        Añade un mensaje al historial.

        Args:
            message: HumanMessage o AIMessage.
        """
        serialized = serialize_message(message)
        self.redis_client.rpush(self.key, json.dumps(serialized))
        if self.ttl:
            self.redis_client.expire(self.key, self.ttl)

    def get_messages(self) -> List[BaseMessage]:
        """
        Recupera todos los mensajes del historial en orden cronológico.

        Returns:
            Lista de mensajes (HumanMessage/AIMessage).
        """
        items = self.redis_client.lrange(self.key, 0, -1)
        messages = []
        for item in items:
            try:
                data = json.loads(item)
                messages.append(deserialize_message(data))
            except (json.JSONDecodeError, KeyError):
                # Si el formato es inválido, saltamos el mensaje
                continue
        return messages

    def clear(self) -> None:
        """Elimina todo el historial de la sesión."""
        self.redis_client.delete(self.key)

    def __len__(self) -> int:
        """Retorna la cantidad de mensajes en el historial."""
        return self.redis_client.llen(self.key)

    @property
    def messages(self) -> List[BaseMessage]:
        """
        Propiedad requerida por BaseChatMessageHistory (alias de get_messages).
        """
        return self.get_messages()
