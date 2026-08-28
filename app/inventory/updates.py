# src/inventory/updates.py
"""
Orquestador de actualizaciones del inventario.

Este módulo coordina la obtención del inventario, decidiendo si usar
la caché (Redis) o consultar directamente a Google Sheets cuando
la caché está vacía o se fuerza una actualización.
"""

import logging
from typing import Optional

from .client import InventoryClient
from .cache import InventoryCache
from .schema import Inventario

logger = logging.getLogger(__name__)


class InventoryUpdater:
    """
    Coordina la obtención del inventario, usando caché cuando esté disponible.

    Args:
        client: Cliente para obtener datos desde Google Sheets.
        cache: Gestor de caché en Redis.
    """

    def __init__(self, client: InventoryClient, cache: InventoryCache):
        self.client = client
        self.cache = cache

    def get_inventory(self, force: bool = False) -> Inventario:
        """
        Obtiene el inventario actual.

        Si force=True, ignora la caché y consulta siempre a Google Sheets.
        Si force=False, intenta obtener de caché; si no existe, consulta y guarda.

        Returns:
            Inventario con los datos más recientes.
        """
        if force:
            logger.info("Forzando actualización desde Google Sheets.")
            return self._fetch_and_cache()

        cached = self.cache.get()
        if cached is not None:
            logger.info("Inventario obtenido desde caché.")
            return cached

        logger.info("Caché vacía o expirada. Consultando Google Sheets.")
        return self._fetch_and_cache()

    def force_refresh(self) -> Inventario:
        """
        Fuerza una actualización completa desde Google Sheets
        y actualiza la caché.

        Returns:
            Inventario con datos frescos.
        """
        return self._fetch_and_cache()

    def _fetch_and_cache(self) -> Inventario:
        """
        Obtiene el inventario desde Google Sheets, lo guarda en caché
        y lo retorna.

        Returns:
            Inventario con los datos recién obtenidos.
        """
        inventario = self.client.fetch_inventory()
        self.cache.set(inventario)
        logger.info(f"Inventario actualizado con {len(inventario.medicamentos)} medicamentos.")
        return inventario
