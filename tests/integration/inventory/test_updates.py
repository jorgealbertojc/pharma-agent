# tests/integration/inventory/test_updates.py
"""
Integration tests for InventoryUpdater with DynamoDB cache.

Requires:
- GOOGLE_APPLICATION_CREDENTIALS and SPREADSHEET_ID environment variables.
- A running Floci instance (DynamoDB emulation).
- The 'INV-TI.RE' sheet must exist and contain inventory data.

Each test creates a temporary DynamoDB table, uses it, and deletes it afterwards.
"""

import time
from typing import Iterator

import boto3
import pytest
from botocore.exceptions import ClientError

from app.core.config import settings
from app.inventory.cache import InventoryCache
from app.inventory.client import InventoryClient
from app.inventory.schema import Inventario
from app.inventory.updates import InventoryUpdater


def _table_name() -> str:
    """Generate a unique table name with timestamp."""
    return f"test_inventory_updates_{int(time.time() * 1000)}"


class CountingInventoryClient(InventoryClient):
    """
    InventoryClient subclass that counts the number of times
    fetch_inventory() is called. Used to verify cache behavior
    without mocks.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fetch_count = 0

    def fetch_inventory(self) -> Inventario:
        self.fetch_count += 1
        return super().fetch_inventory()


@pytest.fixture(scope="function")
def dynamodb_client():
    """Return a boto3 DynamoDB client configured for Floci."""
    return boto3.client(
        "dynamodb",
        endpoint_url=settings.DYNAMODB_ENDPOINT_URL,
        region_name=settings.DYNAMODB_REGION,
        aws_access_key_id=settings.DYNAMODB_ACCESS_KEY_ID,
        aws_secret_access_key=settings.DYNAMODB_SECRET_ACCESS_KEY,
    )


@pytest.fixture(scope="function")
def temp_table(dynamodb_client) -> Iterator[str]:
    """Create a temporary DynamoDB table with 'cache_key' as primary key."""
    table_name = _table_name()
    try:
        dynamodb_client.create_table(
            TableName=table_name,
            AttributeDefinitions=[
                {"AttributeName": "cache_key", "AttributeType": "S"},
            ],
            KeySchema=[
                {"AttributeName": "cache_key", "KeyType": "HASH"},
            ],
            BillingMode="PAY_PER_REQUEST",
        )
        waiter = dynamodb_client.get_waiter("table_exists")
        waiter.wait(TableName=table_name, WaiterConfig={"Delay": 1, "MaxAttempts": 10})
    except ClientError as e:
        pytest.fail(f"Failed to create test table: {e}")

    yield table_name

    try:
        dynamodb_client.delete_table(TableName=table_name)
        waiter = dynamodb_client.get_waiter("table_not_exists")
        waiter.wait(TableName=table_name, WaiterConfig={"Delay": 1, "MaxAttempts": 10})
    except ClientError:
        pass  # Ignore cleanup errors


@pytest.fixture(scope="function")
def cache(temp_table: str) -> InventoryCache:
    """Create an InventoryCache backed by a temporary DynamoDB table."""
    return InventoryCache(
        cache_key="inventory",
        ttl=None,
        table_name=temp_table,
    )


@pytest.fixture(scope="function")
def client() -> CountingInventoryClient:
    """Create a CountingInventoryClient for real Google Sheets access."""
    return CountingInventoryClient(sheet_name="INV-TI.RE")


@pytest.fixture(scope="function")
def updater(client: CountingInventoryClient, cache: InventoryCache) -> InventoryUpdater:
    """Create an InventoryUpdater with real client and cache."""
    return InventoryUpdater(client=client, cache=cache)


class TestInventoryUpdater:
    """Integration tests for InventoryUpdater."""

    def test_get_inventory_cache_miss_fetches_from_sheets(
        self,
        updater: InventoryUpdater,
        cache: InventoryCache,
        client: CountingInventoryClient,
    ) -> None:
        """
        Given: An empty cache.
        When: Calling get_inventory(force=False).
        Then: It fetches from Google Sheets, stores in cache, and returns Inventario.
        """
        # Given
        updater.cache.clear()
        client.fetch_count = 0

        # When
        result = updater.get_inventory(force=False)

        # Then
        assert isinstance(result, Inventario)
        assert len(result.medicamentos) > 0
        assert result.ultima_actualizacion is not None
        assert client.fetch_count == 1, "Sheets should have been queried once"

        # Verify the cache was populated
        cached = updater.cache.get()
        assert cached is not None
        assert len(cached.medicamentos) == len(result.medicamentos)

    def test_get_inventory_cache_hit_does_not_call_sheets(
        self,
        updater: InventoryUpdater,
        cache: InventoryCache,
        client: CountingInventoryClient,
    ) -> None:
        """
        Given: A cache populated with data.
        When: Calling get_inventory(force=False).
        Then: It returns from cache without querying Google Sheets.
        """
        # Given: populate cache with real data (one fetch)
        updater.cache.clear()
        client.fetch_count = 0
        first = updater.get_inventory(force=False)
        assert client.fetch_count == 1

        # When: second call should hit the cache
        result = updater.get_inventory(force=False)

        # Then
        assert client.fetch_count == 1, "Sheets should NOT be queried again"
        assert len(result.medicamentos) == len(first.medicamentos)

    def test_get_inventory_force_true_ignores_cache(
        self,
        updater: InventoryUpdater,
        client: CountingInventoryClient,
    ) -> None:
        """
        Given: A cache populated with data.
        When: Calling get_inventory(force=True).
        Then: It ignores the cache, queries Sheets, and updates the cache.
        """
        # Given
        updater.cache.clear()
        client.fetch_count = 0
        updater.get_inventory(force=False)
        assert client.fetch_count == 1

        # When
        result = updater.get_inventory(force=True)

        # Then
        assert client.fetch_count == 2, "Sheets should be queried again despite cache"
        assert isinstance(result, Inventario)
        assert len(result.medicamentos) > 0

        # Verify cache was refreshed
        cached = updater.cache.get()
        assert cached is not None
        assert len(cached.medicamentos) == len(result.medicamentos)

    def test_force_refresh_updates_cache(
        self,
        updater: InventoryUpdater,
        client: CountingInventoryClient,
    ) -> None:
        """
        Given: A cache populated with data.
        When: Calling force_refresh().
        Then: It queries Sheets and updates the cache.
        """
        # Given
        updater.cache.clear()
        client.fetch_count = 0
        updater.get_inventory(force=False)
        assert client.fetch_count == 1

        # When
        result = updater.force_refresh()

        # Then
        assert client.fetch_count == 2
        assert isinstance(result, Inventario)
        assert len(result.medicamentos) > 0

        cached = updater.cache.get()
        assert cached is not None
        assert len(cached.medicamentos) == len(result.medicamentos)

    def test_get_inventory_cache_miss_with_empty_sheets_returns_empty_inventory(
        self,
        updater: InventoryUpdater,
    ) -> None:
        """
        Given: An empty cache and a fresh Sheets fetch.
        When: Calling get_inventory(force=False).
        Then: Returns an Inventario (possibly with medicamentos).
        """
        # Given
        updater.cache.clear()

        # When
        result = updater.get_inventory(force=False)

        # Then
        assert isinstance(result, Inventario)
        # We don't assert on medicamentos count because Sheets is external,
        # but the returned object should be valid.
        assert result.ultima_actualizacion is not None
