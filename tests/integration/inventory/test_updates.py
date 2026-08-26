# tests/integration/inventory/test_updates.py
"""
Tests de integración para InventoryUpdater.

Verifica el comportamiento del orquestador de inventario:
- Obtener desde caché cuando está disponible.
- Consultar a Google Sheets cuando la caché está vacía.
- Forzar actualización ignorando la caché.
"""

from typing import Iterator
from unittest.mock import MagicMock

import pytest
import redis

from src.core.config import settings
from src.inventory.cache import InventoryCache
from src.inventory.client import InventoryClient
from src.inventory.updates import InventoryUpdater
from src.inventory.schema import Inventario, Medicamento


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
    return f"test_inventory_updates:{uuid.uuid4().hex[:8]}"


@pytest.fixture(scope="function")
def inventory_cache(redis_client: redis.Redis, cache_key: str) -> Iterator[InventoryCache]:
    """Crea una caché con clave única y sin TTL."""
    cache = InventoryCache(redis_client=redis_client, key=cache_key, ttl=None)
    yield cache
    cache.clear()


@pytest.fixture(scope="function")
def inventory_client() -> InventoryClient:
    """Cliente real de Google Sheets."""
    return InventoryClient(sheet_name="INV-TI.RE")


@pytest.fixture(scope="function")
def updater(
    inventory_client: InventoryClient,
    inventory_cache: InventoryCache,
) -> InventoryUpdater:
    """Orquestador de inventario con cliente y caché reales."""
    return InventoryUpdater(client=inventory_client, cache=inventory_cache)


class TestInventoryUpdater:
    """Pruebas de integración para InventoryUpdater."""

    def test_get_inventory_cache_miss_fetches_from_sheets(
        self,
        updater: InventoryUpdater,
        inventory_cache: InventoryCache,
    ) -> None:
        """
        Given: Una caché vacía.
        When: Se llama a get_inventory().
        Then: Se consulta Google Sheets, se guarda en caché y se retorna Inventario.
        """
        # Given
        updater.cache.clear()  # Asegurar que la caché esté vacía

        # When
        result = updater.get_inventory(force=False)

        # Then
        assert isinstance(result, Inventario)
        assert len(result.medicamentos) > 0
        assert result.ultima_actualizacion is not None

        # Verificar que la caché se haya guardado
        cached = updater.cache.get()
        assert cached is not None
        assert len(cached.medicamentos) == len(result.medicamentos)

    def test_get_inventory_cache_hit_does_not_call_api(
        self,
        updater: InventoryUpdater,
        inventory_cache: InventoryCache,
        inventory_client: InventoryClient,
    ) -> None:
        """
        Given: Una caché poblada con datos reales.
        When: Se llama a get_inventory().
        Then: Se retorna Inventario desde caché y NO se consulta la API.
        """
        # Given: poblar caché con datos reales desde Sheets
        fresh_inventory = inventory_client.fetch_inventory()
        updater.cache.set(fresh_inventory)

        # Espiar el método fetch_inventory del cliente
        original_fetch = inventory_client.fetch_inventory
        inventory_client.fetch_inventory = MagicMock(side_effect=original_fetch)

        # When
        result = updater.get_inventory(force=False)

        # Then
        # No debe haber llamado al método fetch_inventory (solo a caché)
        inventory_client.fetch_inventory.assert_not_called()
        assert isinstance(result, Inventario)
        assert len(result.medicamentos) == len(fresh_inventory.medicamentos)

        # Restaurar (opcional)
        inventory_client.fetch_inventory = original_fetch

    def test_force_refresh_ignores_cache_and_updates(
        self,
        updater: InventoryUpdater,
        inventory_cache: InventoryCache,
    ) -> None:
        """
        Given: Una caché con datos antiguos (simulados).
        When: Se llama a force_refresh().
        Then: Se consulta Google Sheets, se actualiza la caché y se retorna Inventario fresco.
        """
        # Given: poblar caché con datos viejos (simulados)
        old_inventory = Inventario(
            medicamentos=[Medicamento(
                codigo="999",
                producto="Producto viejo",
                tipo_venta="LIBRE VENTA",
                marca="Marca vieja",
                stock=0,
                stock_real=0,
                precio_compra=0.0,
                precio_publico=0.0,
                vendidos_piezas=0,
            )]
        )
        updater.cache.set(old_inventory)

        # Espiar fetch_inventory para verificar que se llama
        original_fetch = updater.client.fetch_inventory
        updater.client.fetch_inventory = MagicMock(side_effect=original_fetch)

        # When
        result = updater.force_refresh()

        # Then
        updater.client.fetch_inventory.assert_called_once()
        assert isinstance(result, Inventario)
        assert len(result.medicamentos) > 0
        # Verificar que la caché se actualizó con datos frescos
        cached = updater.cache.get()
        assert cached is not None
        assert len(cached.medicamentos) == len(result.medicamentos)
        # Asegurar que los datos viejos se sobrescribieron (el codigo "999" ya no debería estar)
        assert not any(m.codigo == "999" for m in cached.medicamentos)

        # Restaurar
        updater.client.fetch_inventory = original_fetch

    def test_get_inventory_force_true_ignores_cache(
        self,
        updater: InventoryUpdater,
        inventory_cache: InventoryCache,
    ) -> None:
        """
        Given: Una caché con datos antiguos.
        When: Se llama a get_inventory(force=True).
        Then: Se ignora la caché, se consulta Google Sheets y se actualiza la caché.
        """
        # Given: poblar caché con datos viejos
        from src.inventory.schema import Medicamento
        old_inventory = Inventario(
            medicamentos=[Medicamento(
                codigo="888",
                producto="Producto antiguo",
                tipo_venta="LIBRE VENTA",
                marca="Marca antigua",
                stock=0,
                stock_real=0,
                precio_compra=0.0,
                precio_publico=0.0,
                vendidos_piezas=0,
            )]
        )
        updater.cache.set(old_inventory)

        # Espiar fetch_inventory
        original_fetch = updater.client.fetch_inventory
        updater.client.fetch_inventory = MagicMock(side_effect=original_fetch)

        # When
        result = updater.get_inventory(force=True)

        # Then
        updater.client.fetch_inventory.assert_called_once()
        assert isinstance(result, Inventario)
        assert len(result.medicamentos) > 0
        # Verificar que la caché se actualizó
        cached = updater.cache.get()
        assert cached is not None
        assert len(cached.medicamentos) == len(result.medicamentos)
        assert not any(m.codigo == "888" for m in cached.medicamentos)

        # Restaurar
        updater.client.fetch_inventory = original_fetch
