# app/langchain/memory/buffer.py
"""
Implementación de memoria conversacional tipo buffer.

Esta memoria almacena todos los mensajes en una lista y permite limitar
el número de mensajes o el total de tokens. Al superar los límites,
se descartan los mensajes más antiguos (principio de la lista).

Es la implementación más simple y directa para mantener el contexto
de una conversación, similar a la memoria de ChatGPT o DeepSeek.
"""

from typing import List, Dict, Optional

from .base import BaseMemory
from .utils import count_tokens_approx, truncate_by_tokens, format_messages


class BufferMemory(BaseMemory):
    """
    Memoria tipo buffer con límite de mensajes y/o tokens.

    Atributos:
        messages (List[Dict]): Lista de mensajes en orden cronológico.
        max_messages (int, optional): Número máximo de mensajes a retener.
        max_tokens (int, optional): Máximo de tokens estimados a retener.

    El límite de mensajes se aplica primero, luego el de tokens.
    """

    def __init__(
        self,
        max_messages: Optional[int] = None,
        max_tokens: Optional[int] = None,
    ):
        """
        Inicializa la memoria buffer.

        Args:
            max_messages: Número máximo de mensajes (None = sin límite).
            max_tokens: Máximo de tokens estimados (None = sin límite).
        """
        self.messages: List[Dict[str, str]] = []
        self.max_messages = max_messages
        self.max_tokens = max_tokens

    def add_message(self, role: str, content: str) -> None:
        """
        Añade un mensaje y aplica los límites configurados.

        Args:
            role: 'user' o 'assistant'.
            content: Texto del mensaje.

        Raises:
            ValueError: Si el rol no es válido.
        """
        if role not in ("user", "assistant"):
            raise ValueError(f"Rol inválido: {role}. Debe ser 'user' o 'assistant'.")
        self.messages.append({"role": role, "content": content})
        self._truncate()

    def get_messages(self) -> List[Dict[str, str]]:
        """Retorna una copia de la lista de mensajes."""
        return self.messages.copy()

    def get_context(self) -> str:
        """
        Retorna el historial formateado como texto plano.

        Returns:
            Texto con cada mensaje precedido por "Usuario:" o "Asistente:".
            Si no hay mensajes, retorna una cadena vacía.
        """
        return format_messages(self.messages, include_roles=True)

    def clear(self) -> None:
        """Elimina todos los mensajes del historial."""
        self.messages = []

    def get_token_count(self) -> int:
        """
        Retorna el total aproximado de tokens en el historial actual.

        Uses:
            count_tokens_approx (estimación 4 caracteres ≈ 1 token).
        """
        return sum(count_tokens_approx(msg["content"]) for msg in self.messages)

    def _truncate(self) -> None:
        """
        Aplica los límites de mensajes y tokens.

        Primero limita por número de mensajes, luego por tokens.
        En ambos casos, elimina los mensajes más antiguos.
        """
        # Límite por mensajes
        if self.max_messages is not None and len(self.messages) > self.max_messages:
            self.messages = self.messages[-self.max_messages:]

        # Límite por tokens
        if self.max_tokens is not None:
            self.messages = truncate_by_tokens(self.messages, self.max_tokens)
