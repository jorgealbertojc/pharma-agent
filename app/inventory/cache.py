# app/inventory/cache.py
"""
Caché para el inventario usando DynamoDB (reemplazo de Redis).

Permite almacenar el inventario completo en DynamoDB para reducir
las llamadas a la API de Google Sheets. La caché se invalida
mediante TTL (time-to-live) o manualmente.
"""

import logging
from typing import Optional

from app.aws.dynamodb import create_dynamodb_cache, DynamoDBCache
from .schema import Inventario

logger = logging.getLogger(__name__)


class InventoryCache:
    """
    Gestor de caché del inventario en DynamoDB.

    Args:
        cache_key: Clave de DynamoDB donde se almacenará el inventario.
        ttl: Tiempo de vida en segundos (None = sin expiración).
        table_name: Nombre de la tabla DynamoDB (opcional, por defecto usa settings).
    """

    def __init__(
        self,
        cache_key: str = "inventory",
        ttl: Optional[int] = None,
        table_name: Optional[str] = None,
    ):
        self.cache_key = cache_key
        self.ttl = ttl

        # Crear la instancia de DynamoDBCache usando la fábrica
        self._cache: DynamoDBCache = create_dynamodb_cache(
            table_name=table_name,
            cache_key=cache_key,
            ttl=ttl,
        )

    def get(self) -> Optional[Inventario]:
        """
        Recupera el inventario desde DynamoDB.

        Returns:
            Instancia de Inventario si existe y es válida, o None si no hay caché.
        """
        return self._cache.get()

    def set(self, inventario: Inventario) -> bool:
        """
        Almacena el inventario en DynamoDB.

        Args:
            inventario: Objeto Inventario a cachear.

        Returns:
            True si se guardó correctamente, False en caso de error.
        """
        return self._cache.set(inventario)

    def clear(self) -> bool:
        """
        Elimina la caché del inventario.

        Returns:
            True si se eliminó, False si no existía o hubo error.
        """
        return self._cache.clear()

    def is_fresh(self) -> bool:
        """
        Verifica si la caché existe y no ha expirado.

        Returns:
            True si el ítem existe y no ha expirado.
        """
        return self._cache.is_fresh()
