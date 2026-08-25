# app/memory.py
"""
Script de prueba para el módulo de memoria conversacional.
Ejecutar con: python -m app.memory
"""

from app.langchain.memory import BufferMemory, PersistentMemory
from app.langchain.redis import redis_client


def test_buffer_memory():
    print("🧪 Probando memoria conversacional BufferMemory (en RAM)...\n")

    # 1. Crear memoria con límite de 4 mensajes
    memory = BufferMemory(max_messages=4)

    # 2. Añadir mensajes de ejemplo
    memory.add_message("user", "Hola, ¿quién es el protagonista de El perfume?")
    memory.add_message("assistant", "El protagonista es Jean-Baptiste Grenouille.")
    memory.add_message("user", "¿Y cómo nace?")
    memory.add_message("assistant", "Nace en un mercado de París en 1738, abandonado por su madre.")
    memory.add_message("user", "¿Qué habilidades especiales tiene?")

    # 3. Mostrar el historial
    print("📜 HISTORIAL COMPLETO (últimos 4 mensajes):")
    print(memory.get_context())
    print()

    # 4. Mostrar mensajes en bruto
    print("📦 MENSAJES (estructura interna):")
    for msg in memory.get_messages():
        print(f"  {msg}")
    print()

    # 5. Mostrar conteo de tokens
    print(f"🔢 Tokens estimados: {memory.get_token_count()}")
    print()

    # 6. Probar clear()
    memory.clear()
    print("🧹 Memoria limpiada.")
    print(f"Contexto después de limpiar: '{memory.get_context()}' (debe estar vacío)\n")


def test_persistent_memory():
    print("🧪 Probando memoria persistente (Redis)...\n")

    # 1. Crear memoria persistente (sin TTL, sin límite de tokens)
    session_id = "test_persistent_session"
    memory = PersistentMemory(
        session_id=session_id,
        redis_client=redis_client,
        ttl=None,
        max_tokens=None,
    )

    # 2. Insertar mensajes (cada ejecución añade nuevos)
    import time
    timestamp = time.strftime("%H:%M:%S")
    memory.add_message("user", f"Consulta desde script a las {timestamp}")
    memory.add_message("assistant", f"Respuesta generada a las {timestamp}")
    memory.add_message("user", "¿Qué mensajes hay en el historial?")

    # 3. Recuperar todo el historial
    messages = memory.get_messages()
    print(f"📖 Historial completo (sesión: {session_id}):")
    for i, msg in enumerate(messages, 1):
        print(f"  {i}. {msg['role']}: {msg['content']}")
    print()

    # 4. Mostrar contexto formateado
    print("📋 Contexto formateado:")
    print(memory.get_context())
    print()

    # 5. Mostrar conteo de tokens
    print(f"🔢 Tokens estimados: {memory.get_token_count()}")
    print()

    # 6. NO se limpia la memoria (los datos persisten en Redis)
    print("💾 Los datos permanecen en Redis. Ejecuta de nuevo para añadir más mensajes.")


if __name__ == "__main__":
    # Probar memoria en RAM
    test_buffer_memory()

    # Probar memoria persistente
    test_persistent_memory()
