# app/langchain/redis/__init__.py
"""
Paquete Redis para almacenamiento persistente de historial conversacional.

Proporciona una implementación de BaseChatMessageHistory de LangChain
usando Redis como backend, ideal para sistemas RAG con memoria persistente.

Uso básico:
    from app.langchain.redis import RedisChatHistory, redis_client

    history = RedisChatHistory(session_id="user_123", redis_client=redis_client)
    history.add_message(HumanMessage(content="Hola"))
    history.add_message(AIMessage(content="Hola, ¿cómo estás?"))
    messages = history.get_messages()
"""

from redis import Redis

from .config import REDIS_HOST, REDIS_PORT, REDIS_DB, REDIS_TTL
from .history import RedisChatHistory
from .utils import (
    serialize_message,
    deserialize_message,
    get_redis_key,
    format_messages_for_context,
)

# Cliente Redis compartido (creado con la configuración del .env)
redis_client = Redis(host=REDIS_HOST, port=REDIS_PORT, db=REDIS_DB)

__all__ = [
    "RedisChatHistory",
    "redis_client",
    "serialize_message",
    "deserialize_message",
    "get_redis_key",
    "format_messages_for_context",
    "REDIS_HOST",
    "REDIS_PORT",
    "REDIS_DB",
    "REDIS_TTL",
]
