# tests/integration/memory/test_persistent.py
"""
Integration tests for PersistentMemory (DynamoDB version).

Each test creates a temporary DynamoDB table, uses it, and cleans up afterwards.
"""

import time
import uuid
from typing import Iterator

import boto3
import pytest
from botocore.exceptions import ClientError

from app.core.config import settings
from app.memory.persistent import PersistentMemory


def _table_name() -> str:
    """Generate a unique table name with timestamp."""
    return f"test_persistent_memory_{int(time.time() * 1000)}"


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
def temp_table(dynamodb_client):
    """Create a temporary DynamoDB table and delete it after the test."""
    table_name = _table_name()
    try:
        dynamodb_client.create_table(
            TableName=table_name,
            AttributeDefinitions=[
                {"AttributeName": "session_id", "AttributeType": "S"},
            ],
            KeySchema=[
                {"AttributeName": "session_id", "KeyType": "HASH"},
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
def session_id() -> str:
    """Generate a unique session_id for each test."""
    return f"test_{uuid.uuid4().hex[:8]}"


@pytest.fixture(scope="function")
def persistent_memory(temp_table, session_id) -> Iterator[PersistentMemory]:
    """Create a PersistentMemory instance using a temporary table."""
    memory = PersistentMemory(
        session_id=session_id,
        ttl=None,
        max_messages=None,
        max_tokens=None,
        table_name=temp_table,
    )
    yield memory
    memory.clear()


class TestPersistentMemory:
    """Integration tests for PersistentMemory."""

    def test_add_and_get_messages(self, persistent_memory: PersistentMemory) -> None:
        memory = persistent_memory
        memory.add_message("user", "Hola")
        memory.add_message("assistant", "¿Cómo estás?")
        memory.add_message("user", "Bien, ¿y tú?")
        messages = memory.get_messages()
        assert len(messages) == 3
        assert messages[0] == {"role": "user", "content": "Hola"}
        assert messages[1] == {"role": "assistant", "content": "¿Cómo estás?"}
        assert messages[2] == {"role": "user", "content": "Bien, ¿y tú?"}

    def test_get_context_formats_correctly(self, persistent_memory: PersistentMemory) -> None:
        memory = persistent_memory
        memory.add_message("user", "Hola")
        memory.add_message("assistant", "¿Cómo estás?")
        context = memory.get_context()
        expected = "Usuario: Hola\nAsistente: ¿Cómo estás?"
        assert context == expected

    def test_clear_removes_all_messages(self, persistent_memory: PersistentMemory) -> None:
        memory = persistent_memory
        memory.add_message("user", "Mensaje 1")
        memory.add_message("assistant", "Mensaje 2")
        memory.clear()
        assert memory.get_messages() == []
        assert memory.get_context() == ""
        assert memory.get_token_count() == 0

    def test_invalid_role_raises_error(self, persistent_memory: PersistentMemory) -> None:
        with pytest.raises(ValueError, match="Rol inválido: invalid"):
            persistent_memory.add_message("invalid", "contenido")

    def test_get_token_count(self, persistent_memory: PersistentMemory) -> None:
        memory = persistent_memory
        memory.add_message("user", "abc")        # 0 tokens
        memory.add_message("assistant", "abcd")  # 1 token
        memory.add_message("user", "abcdefgh")   # 2 tokens
        assert memory.get_token_count() == 3

    def test_persistence_across_instances(self, temp_table, session_id) -> None:
        memory1 = PersistentMemory(session_id=session_id, table_name=temp_table)
        memory1.add_message("user", "Hola")
        memory1.add_message("assistant", "¿Cómo estás?")

        memory2 = PersistentMemory(session_id=session_id, table_name=temp_table)
        messages = memory2.get_messages()
        assert len(messages) == 2
        assert messages[0]["content"] == "Hola"
        assert messages[1]["content"] == "¿Cómo estás?"
        memory1.clear()

    def test_ttl_is_set(self, temp_table, session_id, dynamodb_client) -> None:
        memory = PersistentMemory(
            session_id=session_id,
            ttl=60,
            table_name=temp_table,
        )
        memory.add_message("user", "Mensaje con TTL")
        time.sleep(1)

        response = dynamodb_client.get_item(
            TableName=temp_table,
            Key={"session_id": {"S": session_id}},
        )
        item = response.get("Item", {})
        assert "expireAt" in item
        expire_at = int(item["expireAt"]["N"])
        current_time = int(time.time())
        assert expire_at >= current_time + 60 - 5
        memory.clear()
