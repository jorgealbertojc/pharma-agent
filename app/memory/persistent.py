# app/memory/persistent.py
"""
Memoria conversacional persistente usando DynamoDB (reemplazo de Redis).

Esta clase almacena el historial de mensajes en DynamoDB, permitiendo
que la conversación sobreviva a reinicios del proceso.
"""

from typing import Optional, List, Dict

from app.aws.dynamodb import create_dynamodb_memory
from .base import BaseMemory


class PersistentMemory(BaseMemory):
    """
    Memoria conversacional persistente con DynamoDB.

    Args:
        session_id: Identificador único de la sesión (ej. "user_123").
        ttl: Tiempo de vida en segundos (None = sin expiración).
        max_messages: (Ignorado actualmente, DynamoDB no lo soporta).
        max_tokens: (Ignorado actualmente, DynamoDB no lo soporta).
        table_name: Nombre de la tabla DynamoDB (opcional, por defecto usa settings).
    """

    def __init__(
        self,
        session_id: str,
        ttl: Optional[int] = None,
        max_messages: Optional[int] = None,
        max_tokens: Optional[int] = None,
        table_name: Optional[str] = None,
    ):
        self.session_id = session_id
        self.ttl = ttl
        self.max_messages = max_messages
        self.max_tokens = max_tokens

        # Crear la instancia de DynamoDBMemory usando la fábrica
        self._history = create_dynamodb_memory(
            session_id=session_id,
            table_name=table_name,
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
        self._history.add_message(role, content)

    def get_messages(self) -> List[Dict[str, str]]:
        """
        Recupera todos los mensajes del historial en orden cronológico.

        Returns:
            Lista de diccionarios [{"role": "...", "content": "..."}, ...].
        """
        return self._history.get_messages()

    def get_context(self) -> str:
        """
        Retorna el historial formateado para inyectar en el prompt.

        El formato es:
            Usuario: <mensaje>
            Asistente: <mensaje>
            ...

        Returns:
            Cadena con los mensajes formateados.
        """
        return self._history.get_context()

    def clear(self) -> None:
        """Elimina todo el historial de la sesión."""
        self._history.clear()

    def get_token_count(self) -> int:
        """
        Retorna una estimación del total de tokens en el historial.

        Returns:
            Número estimado de tokens.
        """
        return self._history.get_token_count()
