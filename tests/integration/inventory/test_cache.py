# tests/integration/inventory/test_cache.py
"""
Integration tests for InventoryCache using DynamoDB.

Requires:
- GOOGLE_APPLICATION_CREDENTIALS and SPREADSHEET_ID environment variables.
- A running Floci instance (DynamoDB emulation).
- The 'INV-TI.RE' sheet must exist and contain inventory data.

Each test creates a temporary DynamoDB table, uses it, and deletes it afterwards.
"""

import time
import uuid
from typing import Iterator

import boto3
import pytest
from botocore.exceptions import ClientError

from app.core.config import settings
from app.inventory.cache import InventoryCache
from app.inventory.client import InventoryClient
from app.inventory.schema import Inventario


def _table_name() -> str:
    """Generate a unique table name with timestamp."""
    return f"test_inventory_cache_{int(time.time() * 1000)}"


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
    """
    Create a temporary DynamoDB table with 'cache_key' as the primary key.
    Delete it after the test.
    """
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
def cache_key() -> str:
    """Generate a unique cache key for each test."""
    return f"test_cache_{uuid.uuid4().hex[:8]}"


@pytest.fixture(scope="function")
def inventory_cache(temp_table: str, cache_key: str) -> Iterator[InventoryCache]:
    """
    Create an InventoryCache instance using a temporary DynamoDB table.
    Clean up the item after the test.
    """
    cache = InventoryCache(
        cache_key=cache_key,
        ttl=None,
        table_name=temp_table,
    )
    yield cache
    cache.clear()


class TestInventoryCache:
    """Integration tests for InventoryCache."""

    def test_cache_miss_returns_none(self, inventory_cache: InventoryCache) -> None:
        """
        Given: An empty cache (no item in DynamoDB).
        When: Calling get().
        Then: Returns None and is_fresh() is False.
        """
        # Given
        cache = inventory_cache

        # When
        result = cache.get()

        # Then
        assert result is None
        assert cache.is_fresh() is False

    def test_set_and_get_works(self, inventory_cache: InventoryCache) -> None:
        """
        Given: An inventory fetched from Google Sheets.
        When: Storing it in cache and retrieving it.
        Then: The retrieved object is an Inventario instance with data.
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

    def test_clear_removes_cache(self, inventory_cache: InventoryCache) -> None:
        """
        Given: A cache with stored data.
        When: Calling clear().
        Then: get() returns None and is_fresh() is False.
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

    def test_cache_ttl_expiration(self, temp_table: str, cache_key: str) -> None:
        """
        Given: A cache with TTL=2 seconds.
        When: Storing the inventory and waiting for TTL expiration.
        Then: get() returns None (cache expired).
        """
        # Given
        cache = InventoryCache(
            cache_key=cache_key,
            ttl=2,
            table_name=temp_table,
        )
        client = InventoryClient(sheet_name="INV-TI.RE")
        inventario = client.fetch_inventory()
        cache.set(inventario)

        # When
        time.sleep(3)
        retrieved = cache.get()

        # Then
        assert retrieved is None
        # Cleanup (though TTL would have already removed it)
        cache.clear()
