# app/langchain/redis/config.py
"""
Configuración del paquete Redis.

Todas las variables se cargan desde el archivo .env o usan valores por defecto.
"""

import os
from dotenv import load_dotenv

load_dotenv()

# Configuración de conexión
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
REDIS_DB = int(os.getenv("REDIS_DB", "0"))
REDIS_TTL = os.getenv("REDIS_TTL")

# Convertir TTL a int o None
if REDIS_TTL is not None:
    try:
        REDIS_TTL = int(REDIS_TTL)
    except ValueError:
        REDIS_TTL = None
