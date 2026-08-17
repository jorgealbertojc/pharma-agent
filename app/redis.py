# app/redis.py
"""
Script de prueba para el paquete Redis.

Ejecutar con: python -m app.redis
"""

import json
from app.langchain.redis import redis_client
from app.langchain.redis.utils import get_redis_key, format_messages_for_context
from langchain_core.messages import HumanMessage, AIMessage
from app.langchain.redis import RedisChatHistory

def test_redis_operations():
    print("🧪 Probando operaciones básicas en Redis...\n")

    # 1. Insertar mensajes con RPUSH (usando RedisChatHistory)
    session_id = "test_session_001"
    history = RedisChatHistory(session_id=session_id, redis_client=redis_client, ttl=None)

    # Limpiar por si existía algo previo
    history.clear()

    print("📝 Insertando mensajes...")
    history.add_message(HumanMessage(content="Hola, ¿qué es El perfume?"))
    history.add_message(AIMessage(content="Es una novela de Patrick Süskind sobre un asesino con olfato extraordinario."))
    history.add_message(HumanMessage(content="¿Dónde transcurre?"))
    history.add_message(AIMessage(content="Principalmente en París, Francia, en el siglo XVIII."))

    # 2. Recuperar con LRANGE (get_messages)
    print("\n📖 Recuperando historial completo (LRANGE):")
    messages = history.get_messages()
    for i, msg in enumerate(messages, 1):
        print(f"  {i}. {msg.type}: {msg.content}")

    # 3. Mostrar contexto formateado
    print("\n📋 Contexto formateado para prompt:")
    print(format_messages_for_context(messages))

    # 4. Ver la clave en Redis y su TTL
    key = get_redis_key(session_id)
    ttl = redis_client.ttl(key)
    print(f"\n🔑 Clave Redis: {key} (TTL: {ttl} segundos)")

    # 5. Probar DEL (clear)
    print("\n🧹 Eliminando historial (DEL)...")
    history.clear()
    after_delete = history.get_messages()
    print(f"Historial después de limpiar: {len(after_delete)} mensajes (debe ser 0)")

    # 6. Verificar que la clave ya no existe
    exists = redis_client.exists(key)
    print(f"¿La clave existe todavía? {exists} (debe ser 0)")

if __name__ == "__main__":
    test_redis_operations()
