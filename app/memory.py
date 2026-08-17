# app/memory.py
"""
Script de prueba para el módulo de memoria conversacional.
Ejecutar con: python -m app.memory
"""

from app.langchain.memory import BufferMemory

def test_memory():
    print("🧪 Probando memoria conversacional BufferMemory...\n")

    # 1. Crear memoria con límite de 4 mensajes
    memory = BufferMemory(max_messages=4)

    # 2. Añadir mensajes de ejemplo
    memory.add_message("user", "Hola, ¿quién es el protagonista de El perfume?")
    memory.add_message("assistant", "El protagonista es Jean-Baptiste Grenouille.")
    memory.add_message("user", "¿Y cómo nace?")
    memory.add_message("assistant", "Nace en un mercado de París en 1738, abandonado por su madre.")
    memory.add_message("user", "¿Qué habilidades especiales tiene?")

    # 3. Mostrar el historial
    print("📜 HISTORIAL COMPLETO (últimos 3 mensajes):")
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
    print(f"Contexto después de limpiar: '{memory.get_context()}' (debe estar vacío)")

if __name__ == "__main__":
    test_memory()
