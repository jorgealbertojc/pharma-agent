"""
Memoria conversacional tipo buffer en RAM.

Esta clase almacena el historial de mensajes en una lista en memoria.
Soporta límites opcionales de número de mensajes y de tokens estimados.
Cuando se supera un límite, se descartan los mensajes más antiguos.
"""

from typing import List, Dict, Optional

from .base import BaseMemory


class BufferMemory(BaseMemory):
    """
    Memoria conversacional en RAM con límites configurables.

    Args:
        max_messages: Número máximo de mensajes a retener. None = sin límite.
        max_tokens: Máximo de tokens estimados. None = sin límite.
    """

    def __init__(
        self,
        max_messages: Optional[int] = None,
        max_tokens: Optional[int] = None,
    ):
        self._messages: List[Dict[str, str]] = []
        self.max_messages = max_messages
        self.max_tokens = max_tokens

    def add_message(self, role: str, content: str) -> None:
        """
        Añade un mensaje al historial y aplica los límites configurados.

        Args:
            role: 'user' o 'assistant'.
            content: Texto del mensaje.

        Raises:
            ValueError: Si el rol no es 'user' ni 'assistant'.
        """
        if role not in ("user", "assistant"):
            raise ValueError(f"Rol inválido: {role}. Debe ser 'user' o 'assistant'.")

        self._messages.append({"role": role, "content": content})
        self._truncate()

    def get_messages(self) -> List[Dict[str, str]]:
        """Retorna una copia de la lista de mensajes."""
        return self._messages.copy()

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
        if not self._messages:
            return ""

        lines = []
        for msg in self._messages:
            role = "Usuario" if msg["role"] == "user" else "Asistente"
            lines.append(f"{role}: {msg['content']}")
        return "\n".join(lines)

    def clear(self) -> None:
        """Elimina todos los mensajes del historial."""
        self._messages = []

    def get_token_count(self) -> int:
        """
        Retorna una estimación del total de tokens en el historial.

        La heurística usada es 4 caracteres ≈ 1 token.
        Es una aproximación válida para modelos como Llama o GPT.

        Returns:
            Número estimado de tokens.
        """
        return sum(len(msg["content"]) // 4 for msg in self._messages)

    def _truncate(self) -> None:
        """
        Aplica los límites de mensajes y tokens.

        Si se excede max_messages, elimina los mensajes más antiguos.
        Si se excede max_tokens, elimina mensajes antiguos hasta que
        el total estimado de tokens sea menor o igual al límite.
        """
        # 1. Límite por número de mensajes
        if self.max_messages is not None and len(self._messages) > self.max_messages:
            self._messages = self._messages[-self.max_messages:]

        # 2. Límite por tokens estimados
        if self.max_tokens is not None:
            while self._messages and self.get_token_count() > self.max_tokens:
                # Eliminar el mensaje más antiguo (principio de la lista)
                self._messages.pop(0)
