"""
Integration tests for DynamoDB chat history.

These tests use a real DynamoDB table (via Floci) and create/destroy a temporary
table for each test to ensure isolation.
"""

import time
import boto3
import pytest
from botocore.exceptions import ClientError

from app.aws.dynamodb.chat_history import DynamoDBMemory, create_dynamodb_memory
from app.core.config import settings
from app.core.exceptions import MemoryError


# Helper to create a unique table name with timestamp
def _table_name() -> str:
    return f"test_chat_history_{int(time.time() * 1000)}"


@pytest.fixture
def dynamodb_client():
    """Return a boto3 DynamoDB client configured for Floci."""
    return boto3.client(
        "dynamodb",
        endpoint_url=settings.DYNAMODB_ENDPOINT_URL,
        region_name=settings.DYNAMODB_REGION,
        aws_access_key_id=settings.DYNAMODB_ACCESS_KEY_ID,
        aws_secret_access_key=settings.DYNAMODB_SECRET_ACCESS_KEY,
    )


@pytest.fixture
def temp_table(dynamodb_client):
    """
    Create a temporary DynamoDB table with a single primary key (session_id).
    Delete it after the test.
    """
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

    # Cleanup
    try:
        dynamodb_client.delete_table(TableName=table_name)
        waiter = dynamodb_client.get_waiter("table_not_exists")
        waiter.wait(TableName=table_name, WaiterConfig={"Delay": 1, "MaxAttempts": 10})
    except ClientError:
        pass  # Ignore cleanup errors


@pytest.fixture
def chat_history(temp_table):
    """
    Return a DynamoDBMemory instance using the temporary table.
    """
    return create_dynamodb_memory(
        session_id="test_session",
        table_name=temp_table,
        ttl=None,
        primary_key_name="session_id",
    )


class TestDynamoDBMemory:
    """Integration tests for DynamoDBMemory."""

    def test_add_and_get_messages(self, chat_history):
        """
        Given: A new chat history session.
        When: Adding user and assistant messages.
        Then: They are retrieved in the correct order.
        """
        # Given
        history = chat_history

        # When
        history.add_message("user", "Hola, ¿qué es el ibuprofeno?")
        history.add_message("assistant", "Es un antiinflamatorio.")
        history.add_message("user", "¿Tiene efectos secundarios?")

        # Then
        messages = history.get_messages()
        assert len(messages) == 3
        assert messages[0] == {"role": "user", "content": "Hola, ¿qué es el ibuprofeno?"}
        assert messages[1] == {"role": "assistant", "content": "Es un antiinflamatorio."}
        assert messages[2] == {"role": "user", "content": "¿Tiene efectos secundarios?"}

    def test_get_context(self, chat_history):
        """
        Given: A history with messages.
        When: Calling get_context().
        Then: It returns formatted text with "Usuario:" and "Asistente:".
        """
        # Given
        history = chat_history
        history.add_message("user", "Hola")
        history.add_message("assistant", "¿Cómo estás?")

        # When
        context = history.get_context()

        # Then
        expected = "Usuario: Hola\nAsistente: ¿Cómo estás?"
        assert context == expected

    def test_get_context_empty(self, chat_history):
        """
        Given: An empty history.
        When: Calling get_context().
        Then: It returns an empty string.
        """
        # Given
        history = chat_history

        # When
        context = history.get_context()

        # Then
        assert context == ""

    def test_clear(self, chat_history):
        """
        Given: A history with messages.
        When: Calling clear().
        Then: All messages are removed.
        """
        # Given
        history = chat_history
        history.add_message("user", "Mensaje 1")
        history.add_message("assistant", "Mensaje 2")

        # When
        history.clear()

        # Then
        messages = history.get_messages()
        assert len(messages) == 0
        assert history.get_context() == ""

    def test_invalid_role_raises_error(self, chat_history):
        """
        Given: A history instance.
        When: Adding a message with an invalid role.
        Then: ValueError is raised.
        """
        # Given
        history = chat_history

        # When / Then
        with pytest.raises(ValueError, match="Rol inválido: invalid"):
            history.add_message("invalid", "contenido")

    def test_ttl_is_applied(self, dynamodb_client, temp_table):
        """
        Given: A history with TTL enabled.
        When: Adding a message.
        Then: The item has the TTL attribute set.
        """
        # Given
        ttl_seconds = 60
        history = create_dynamodb_memory(
            session_id="test_ttl",
            table_name=temp_table,
            ttl=ttl_seconds,
            primary_key_name="session_id",
        )

        # When
        history.add_message("user", "Mensaje con TTL")
        time.sleep(1)  # Allow write to propagate

        # Then
        response = dynamodb_client.get_item(
            TableName=temp_table,
            Key={"session_id": {"S": "test_ttl"}},
        )
        item = response.get("Item", {})
        # LangChain uses "expireAt" as the TTL attribute name
        assert "expireAt" in item, "Item should have expireAt attribute"
        expire_at = int(item["expireAt"]["N"])
        current_time = int(time.time())
        # TTL should be roughly ttl_seconds ahead
        assert expire_at >= current_time + ttl_seconds - 5

    def test_get_token_count(self, chat_history):
        """
        Given: A history with messages of varying lengths.
        When: Calling get_token_count().
        Then: It returns the sum of len(content)//4.
        """
        # Given
        history = chat_history
        history.add_message("user", "abc")        # 0 tokens
        history.add_message("assistant", "abcd")  # 1 token
        history.add_message("user", "abcdefgh")   # 2 tokens

        # When
        count = history.get_token_count()

        # Then
        assert count == 3  # 0 + 1 + 2

    def test_persistence_across_instances(self, temp_table):
        """
        Given: A session with messages stored.
        When: A new DynamoDBMemory instance is created with the same session_id.
        Then: The messages are retrieved correctly.
        """
        # Given
        session_id = "persist_session"
        memory1 = create_dynamodb_memory(
            session_id=session_id,
            table_name=temp_table,
            primary_key_name="session_id",
        )
        memory1.add_message("user", "Hola")
        memory1.add_message("assistant", "¿Cómo estás?")

        # When
        memory2 = create_dynamodb_memory(
            session_id=session_id,
            table_name=temp_table,
            primary_key_name="session_id",
        )

        # Then
        messages = memory2.get_messages()
        assert len(messages) == 2
        assert messages[0]["content"] == "Hola"
        assert messages[1]["content"] == "¿Cómo estás?"
