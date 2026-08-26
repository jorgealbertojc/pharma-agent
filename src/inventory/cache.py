"""
Caché para el inventario usando Redis.

Permite almacenar el inventario completo en Redis para reducir
las llamadas a la API de Google Sheets. La caché se invalida
mediante TTL (time-to-live) o manualmente.
"""

import json
import logging
from typing import Optional

import redis

from .schema import Inventario

logger = logging.getLogger(__name__)


class InventoryCache:
    """
    Gestor de caché del inventario en Redis.

    Args:
        redis_client: Cliente Redis ya conectado.
        key: Clave de Redis donde se almacenará el inventario.
        ttl: Tiempo de vida en segundos (None = sin expiración).
    """

    def __init__(
        self,
        redis_client: redis.Redis,
        key: str = "inventory:cache",
        ttl: Optional[int] = None,
    ):
        self.redis_client = redis_client
        self.key = key
        self.ttl = ttl

    def get(self) -> Optional[Inventario]:
        """
        Recupera el inventario desde Redis.

        Returns:
            Instancia de Inventario si existe y es válida, o None si no hay caché.
        """
        try:
            raw = self.redis_client.get(self.key)
            if raw is None:
                logger.debug("Caché de inventario vacío o expirado.")
                return None
            data = json.loads(raw)
            return Inventario(**data)
        except (json.JSONDecodeError, TypeError, redis.RedisError) as e:
            logger.error(f"Error al recuperar caché de inventario: {e}")
            return None

    def set(self, inventario: Inventario) -> bool:
        """
        Almacena el inventario en Redis.

        Args:
            inventario: Objeto Inventario a cachear.

        Returns:
            True si se guardó correctamente, False en caso de error.
        """
        try:
            raw = inventario.model_dump_json()
            self.redis_client.set(self.key, raw)
            if self.ttl is not None:
                self.redis_client.expire(self.key, self.ttl)
            logger.info(f"Inventario cacheado correctamente (TTL={self.ttl}s)")
            return True
        except (TypeError, redis.RedisError) as e:
            logger.error(f"Error al cachear inventario: {e}")
            return False

    def clear(self) -> bool:
        """
        Elimina la caché del inventario.

        Returns:
            True si se eliminó, False si no existía o hubo error.
        """
        try:
            deleted = self.redis_client.delete(self.key)
            if deleted:
                logger.info("Caché de inventario eliminada.")
            else:
                logger.debug("Caché de inventario ya no existía.")
            return bool(deleted)
        except redis.RedisError as e:
            logger.error(f"Error al limpiar caché de inventario: {e}")
            return False

    def is_fresh(self) -> bool:
        """
        Verifica si la caché existe y no ha expirado.

        Returns:
            True si la clave existe y tiene TTL > 0 (o no tiene TTL).
        """
        try:
            exists = self.redis_client.exists(self.key)
            if not exists:
                return False
            ttl = self.redis_client.ttl(self.key)
            # TTL = -1 significa que la clave existe sin expiración
            # TTL > 0 significa que aún no ha expirado
            return ttl != -2
        except redis.RedisError:
            return False
