# app/inventory/updates.py
"""
Inventory update orchestrator.

This module coordinates inventory retrieval, deciding whether to use
the cache (DynamoDB) or query Google Sheets directly when the cache
is empty or a forced refresh is requested.
"""

import logging

from .client import InventoryClient
from .cache import InventoryCache
from .schema import Inventario

logger = logging.getLogger(__name__)


class InventoryUpdater:
    """
    Coordinates inventory retrieval, using cache when available.

    Args:
        client: Client to fetch data from Google Sheets.
        cache: Cache manager backed by DynamoDB.
    """

    def __init__(self, client: InventoryClient, cache: InventoryCache):
        self.client = client
        self.cache = cache

    def get_inventory(self, force: bool = False) -> Inventario:
        """
        Retrieve the current inventory.

        If force=True, ignores the cache and always queries Google Sheets.
        If force=False, attempts to read from cache; if missing or expired,
        queries Google Sheets and stores the result in cache.

        Args:
            force: If True, bypass the cache and fetch fresh data.

        Returns:
            Inventario with the most recent data.
        """
        if force:
            logger.info("Forcing refresh from Google Sheets.")
            return self._fetch_and_cache()

        cached = self.cache.get()
        if cached is not None:
            logger.info("Inventory retrieved from cache.")
            return cached

        logger.info("Cache empty or expired. Fetching from Google Sheets.")
        return self._fetch_and_cache()

    def force_refresh(self) -> Inventario:
        """
        Force a full refresh from Google Sheets and update the cache.

        Returns:
            Inventario with fresh data.
        """
        return self._fetch_and_cache()

    def _fetch_and_cache(self) -> Inventario:
        """
        Fetch inventory from Google Sheets, store it in cache, and return it.

        Returns:
            Inventario with newly fetched data.
        """
        inventario = self.client.fetch_inventory()
        self.cache.set(inventario)
        logger.info(f"Inventory updated with {len(inventario.medicamentos)} medicamentos.")
        return inventario
