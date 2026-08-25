# src/memory/base.py
"""
Definición de la interfaz base para sistemas de memoria conversacional.

Esta clase abstracta establece el contrato que deben cumplir todas las
implementaciones de memoria. La memoria es responsable de almacenar y
recuperar el historial de mensajes (usuario y asistente) en una conversación.
"""

from abc import ABC, abstractmethod
from typing import List, Dict


class BaseMemory(ABC):
    """
    Interfaz abstracta para sistemas de memoria conversacional.

    Cualquier implementación de memoria (en RAM, persistente con Redis, etc.)
    debe heredar de esta clase e implementar todos sus métodos.

    La memoria almacena mensajes en orden cronológico y proporciona métodos
    para añadir, recuperar y gestionar el historial.
    """

    @abstractmethod
    def add_message(self, role: str, content: str) -> None:
        """
        Añade un mensaje al historial.

        Args:
            role: El rol del emisor ('user' o 'assistant').
            content: El contenido del mensaje.

        Raises:
            ValueError: Si el rol no es válido.
        """
        pass

    @abstractmethod
    def get_messages(self) -> List[Dict[str, str]]:
        """
        Retorna el historial completo como una lista de diccionarios.

        Returns:
            Lista de mensajes con formato [{"role": "user", "content": "..."}, ...]
        """
        pass

    @abstractmethod
    def get_context(self) -> str:
        """
        Retorna el historial formateado como un único bloque de texto,
        adecuado para inyectar en el prompt del modelo.

        Returns:
            Cadena de texto con los mensajes precedidos por "Usuario:" y "Asistente:".
        """
        pass

    @abstractmethod
    def clear(self) -> None:
        """Elimina todos los mensajes del historial."""
        pass

    @abstractmethod
    def get_token_count(self) -> int:
        """
        Retorna una estimación del número de tokens que ocupa el historial actual.

        Returns:
            Número estimado de tokens (basado en una heurística simple).
        """
        pass

    def format_for_prompt(self, include_system: bool = True) -> str:
        """
        Formatea el historial como un bloque de texto estructurado para el prompt.

        Este método no es abstracto porque proporciona una implementación
        por defecto que puede ser sobrescrita si se necesita un formato específico.

        Args:
            include_system: Si se debe incluir un encabezado descriptivo.

        Returns:
            El historial formateado como texto.
        """
        messages = self.get_messages()
        if not messages:
            return "No hay historial previo."

        lines = []
        if include_system:
            lines.append("## Historial de la conversación")
        for msg in messages:
            role = "Usuario" if msg["role"] == "user" else "Asistente"
            lines.append(f"{role}: {msg['content']}")

        return "\n".join(lines)
