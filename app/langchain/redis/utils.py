# app/langchain/redis/utils.py
"""
Utilidades para el paquete Redis: serialización, formateo y gestión de claves.
"""

import json
from typing import List, Dict, Any

from langchain_core.messages import BaseMessage, HumanMessage, AIMessage


def serialize_message(message: BaseMessage) -> Dict[str, Any]:
    """
    Convierte un mensaje de LangChain a diccionario serializable.

    Args:
        message: Instancia de HumanMessage o AIMessage.

    Returns:
        Diccionario con 'type' y 'content'.
    """
    return {
        "type": message.type,  # "human" o "ai"
        "content": message.content,
    }


def deserialize_message(data: Dict[str, Any]) -> BaseMessage:
    """
    Reconstruye un mensaje de LangChain desde un diccionario.

    Args:
        data: Diccionario con 'type' y 'content'.

    Returns:
        HumanMessage o AIMessage.
    """
    if data["type"] == "human":
        return HumanMessage(content=data["content"])
    elif data["type"] == "ai":
        return AIMessage(content=data["content"])
    else:
        raise ValueError(f"Tipo de mensaje desconocido: {data['type']}")


def get_redis_key(session_id: str, prefix: str = "chat_history") -> str:
    """
    Genera la clave de Redis para una sesión determinada.

    Args:
        session_id: Identificador único de la sesión.
        prefix: Prefijo para agrupar claves (por defecto "chat_history").

    Returns:
        Clave formateada, ej: "chat_history:session_123"
    """
    return f"{prefix}:{session_id}"


def format_messages_for_context(messages: List[BaseMessage]) -> str:
    """
    Formatea una lista de mensajes de LangChain para inyectar en el prompt.

    Args:
        messages: Lista de mensajes (HumanMessage o AIMessage).

    Returns:
        Texto con formato "Usuario: ...\nAsistente: ..."
    """
    lines = []
    for msg in messages:
        if isinstance(msg, HumanMessage):
            lines.append(f"Usuario: {msg.content}")
        elif isinstance(msg, AIMessage):
            lines.append(f"Asistente: {msg.content}")
    return "\n".join(lines) if lines else ""
