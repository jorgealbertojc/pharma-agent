"""
Tests de integración para InventoryCache.

Requiere:
- Variables de entorno GOOGLE_APPLICATION_CREDENTIALS y SPREADSHEET_ID definidas.
- Redis en ejecución (host/port de settings).
- La hoja 'INV-TI.RE' debe existir y contener inventario.
"""

import pytest
import redis

from typing import Iterator

from app.core.config import settings
from app.inventory.cache import InventoryCache
from app.inventory.client import InventoryClient
from app.inventory.schema import Inventario


@pytest.fixture(scope="function")
def redis_client() -> redis.Redis:
    """Cliente Redis configurado desde settings."""
    return redis.Redis(
        host=settings.REDIS_HOST,
        port=settings.REDIS_PORT,
        db=settings.REDIS_DB_INDEX,
        decode_responses=True,
    )


@pytest.fixture(scope="function")
def cache_key() -> str:
    """Clave única para cada test."""
    import uuid
    return f"test_inventory_cache:{uuid.uuid4().hex[:8]}"


@pytest.fixture(scope="function")
def inventory_cache(redis_client: redis.Redis, cache_key: str) -> Iterator[InventoryCache]:
    """Crea una caché con clave única y sin TTL."""
    cache = InventoryCache(redis_client=redis_client, key=cache_key, ttl=None)
    yield cache
    # Limpieza al finalizar el test
    cache.clear()


class TestInventoryCache:
    """Pruebas de integración para InventoryCache."""

    def test_cache_miss_returns_none(
        self,
        inventory_cache: InventoryCache,
    ) -> None:
        """
        Given: Una caché vacía (sin clave en Redis).
        When: Se llama a get().
        Then: Retorna None.
        """
        # Given
        cache = inventory_cache

        # When
        result = cache.get()

        # Then
        assert result is None
        assert cache.is_fresh() is False

    def test_set_and_get_works(
        self,
        inventory_cache: InventoryCache,
    ) -> None:
        """
        Given: Un inventario obtenido desde Google Sheets.
        When: Se guarda en caché y luego se recupera.
        Then: El objeto recuperado es una instancia de Inventario con datos.
        """
        # Given
        cache = inventory_cache
        client = InventoryClient(sheet_name="INV-TI.RE")
        inventario = client.fetch_inventory()

        # When
        success = cache.set(inventario)
        retrieved = cache.get()

        # Then
        assert success is True
        assert retrieved is not None
        assert isinstance(retrieved, Inventario)
        assert len(retrieved.medicamentos) > 0
        assert retrieved.ultima_actualizacion is not None
        assert cache.is_fresh() is True

    def test_clear_removes_cache(
        self,
        inventory_cache: InventoryCache,
    ) -> None:
        """
        Given: Una caché con datos guardados.
        When: Se llama a clear().
        Then: get() retorna None y is_fresh() es False.
        """
        # Given
        cache = inventory_cache
        client = InventoryClient(sheet_name="INV-TI.RE")
        inventario = client.fetch_inventory()
        cache.set(inventario)

        # When
        deleted = cache.clear()
        retrieved = cache.get()

        # Then
        assert deleted is True
        assert retrieved is None
        assert cache.is_fresh() is False

    def test_cache_ttl_expiration(
        self,
        redis_client: redis.Redis,
        cache_key: str,
    ) -> None:
        """
        Given: Una caché con TTL=1 segundo.
        When: Se guarda y se espera más de 1 segundo.
        Then: get() retorna None (caché expirada).
        """
        # Given
        import time
        cache = InventoryCache(
            redis_client=redis_client,
            key=cache_key,
            ttl=1,
        )
        client = InventoryClient(sheet_name="INV-TI.RE")
        inventario = client.fetch_inventory()
        cache.set(inventario)

        # When
        time.sleep(1.5)
        retrieved = cache.get()

        # Then
        assert retrieved is None
        # Limpieza manual (aunque el TTL ya borró la clave)
        cache.clear()
