# app/aws/dynamodb/cache.py
"""
DynamoDB-based cache for inventory data.

This module provides a persistent cache implementation that stores
the entire inventory as a single item in DynamoDB, replacing the Redis cache.
"""

import json
import time
from typing import Optional, Any

import boto3
from botocore.exceptions import ClientError

from app.core.config import settings
from app.inventory.schema import Inventario
from app.core.exceptions import CacheError


class DynamoDBCache:
    """
    Inventory cache using DynamoDB.

    Stores the inventory as a single item with a fixed key.
    Supports TTL via the 'expireAt' attribute.

    Args:
        table_name: DynamoDB table name.
        cache_key: Fixed key for the inventory item (default: "inventory").
        dynamodb_client: Optional boto3 DynamoDB client (if not provided, one is created).
        ttl: Time-to-live in seconds (None = no expiration).
    """

    def __init__(
        self,
        table_name: str,
        cache_key: str = "inventory",
        dynamodb_client: Optional[Any] = None,
        ttl: Optional[int] = None,
    ):
        self.table_name = table_name
        self.cache_key = cache_key
        self.ttl = ttl

        if dynamodb_client is None:
            # Create a DynamoDB client using global settings
            dynamodb_client = boto3.client(
                "dynamodb",
                endpoint_url=settings.DYNAMODB_ENDPOINT_URL,
                region_name=settings.DYNAMODB_REGION,
                aws_access_key_id=settings.DYNAMODB_ACCESS_KEY_ID,
                aws_secret_access_key=settings.DYNAMODB_SECRET_ACCESS_KEY,
            )
        self._client = dynamodb_client

    def get(self) -> Optional[Inventario]:
        """
        Retrieve the inventory from the cache.

        Returns:
            Inventario instance if found and not expired, None otherwise.
        """
        try:
            response = self._client.get_item(
                TableName=self.table_name,
                Key={"cache_key": {"S": self.cache_key}},
            )
            item = response.get("Item")
            if not item:
                return None

            # Check if expired (DynamoDB may not have deleted it yet)
            if "expireAt" in item:
                expire_at = int(item["expireAt"]["N"])
                if int(time.time()) > expire_at:
                    # Item expired, treat as cache miss
                    return None

            # Deserialize the inventory from JSON
            inventory_data = json.loads(item["inventory"]["S"])
            return Inventario.model_validate(inventory_data)

        except ClientError as e:
            raise CacheError(f"Failed to get inventory from DynamoDB: {e}") from e

    def set(self, inventory: Inventario) -> bool:
        """
        Store the inventory in the cache.

        Args:
            inventory: Inventario object to cache.

        Returns:
            True if successful, False otherwise.
        """
        try:
            # Serialize the inventory to JSON
            inventory_json = inventory.model_dump_json()

            item = {
                "cache_key": {"S": self.cache_key},
                "inventory": {"S": inventory_json},
                "last_updated": {"S": inventory.ultima_actualizacion or ""},
            }

            # Add TTL if configured
            if self.ttl is not None:
                expire_at = int(time.time()) + self.ttl
                item["expireAt"] = {"N": str(expire_at)}

            self._client.put_item(
                TableName=self.table_name,
                Item=item,
            )
            return True

        except ClientError as e:
            raise CacheError(f"Failed to set inventory in DynamoDB: {e}") from e

    def clear(self) -> bool:
        """
        Remove the inventory from the cache.

        Returns:
            True if item was deleted, False if it didn't exist.
        """
        try:
            response = self._client.delete_item(
                TableName=self.table_name,
                Key={"cache_key": {"S": self.cache_key}},
                ReturnValues="ALL_OLD",
            )
            # Return True if something was deleted
            return "Attributes" in response

        except ClientError as e:
            raise CacheError(f"Failed to clear inventory from DynamoDB: {e}") from e

    def is_fresh(self) -> bool:
        """
        Check if the cache exists and is not expired.

        Returns:
            True if cache is present and valid, False otherwise.
        """
        try:
            response = self._client.get_item(
                TableName=self.table_name,
                Key={"cache_key": {"S": self.cache_key}},
                # Eliminamos ProjectionExpression para obtener el ítem completo
                # y así poder verificar su existencia aunque no tenga expireAt.
            )
            item = response.get("Item")
            if not item:
                return False

            if "expireAt" in item:
                expire_at = int(item["expireAt"]["N"])
                return int(time.time()) <= expire_at

            return True

        except ClientError:
            return False


def create_dynamodb_cache(
    table_name: Optional[str] = None,
    cache_key: str = "inventory",
    ttl: Optional[int] = None,
) -> DynamoDBCache:
    """
    Factory function to create a DynamoDBCache instance with global settings.

    Args:
        table_name: Optional override for table name.
        cache_key: Fixed key for the inventory item (default: "inventory").
        ttl: Optional override for TTL (seconds).

    Returns:
        Configured DynamoDBCache instance.
    """
    if table_name is None:
        table_name = settings.DYNAMODB_INVENTORY_CACHE_TABLE

    if ttl is None:
        ttl = getattr(settings, "DYNAMODB_INVENTORY_CACHE_TTL", None)

    return DynamoDBCache(
        table_name=table_name,
        cache_key=cache_key,
        ttl=ttl,
    )
