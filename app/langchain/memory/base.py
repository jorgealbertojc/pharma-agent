# app/langchain/memory/base.py
"""
Definición de la interfaz base para sistemas de memoria conversacional.

Este archivo establece el contrato que deben cumplir todas las implementaciones
de memoria. Una memoria conversacional es responsable de:
- Almacenar el historial de mensajes (usuario y asistente).
- Recuperar el historial formateado para inyectarlo en el prompt.
- Gestionar el límite de tokens (truncar, resumir, o eliminar mensajes antiguos).

Cualquier clase que herede de BaseMemory debe implementar los métodos abstractos.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional


class BaseMemory(ABC):
    """
    Interfaz abstracta para sistemas de memoria conversacional.

    La memoria almacena el historial de la conversación y lo formatea para
    ser inyectado en el prompt del modelo en cada turno.
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
    def get_context(self) -> str:
        """
        Retorna el historial formateado como texto para inyectar en el prompt.

        Returns:
            El historial completo (o truncado) en formato legible.
        """
        pass

    @abstractmethod
    def get_messages(self) -> List[Dict[str, str]]:
        """
        Retorna el historial como lista de diccionarios.

        Returns:
            Lista de mensajes con formato [{"role": "...", "content": "..."}].
        """
        pass

    @abstractmethod
    def clear(self) -> None:
        """Limpia todo el historial de la memoria."""
        pass

    @abstractmethod
    def get_token_count(self) -> int:
        """
        Retorna la cantidad aproximada de tokens que ocupa el historial actual.

        Returns:
            Número estimado de tokens (base en 4 caracteres ≈ 1 token).
        """
        pass

    def format_for_prompt(self, include_system: bool = True) -> str:
        """
        Formatea el historial como un bloque de texto para el prompt.

        Este método NO es abstracto porque proporciona una implementación
        por defecto que puede ser sobrescrita si se necesita un formato
        específico.

        Args:
            include_system: Si se debe incluir un encabezado de sistema.

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
