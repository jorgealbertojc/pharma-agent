"""
DynamoDB-backed chat history using LangChain.

This module provides a persistent memory implementation that stores
conversation history in DynamoDB using LangChain's DynamoDBChatMessageHistory.
"""

from typing import Optional, List, Dict

import boto3
from langchain_community.chat_message_histories import DynamoDBChatMessageHistory
from langchain_core.messages import HumanMessage, AIMessage

from app.core.config import settings
from app.memory.base import BaseMemory


class DynamoDBMemory(BaseMemory):
    """
    Persistent chat memory using DynamoDB (LangChain adapter).

    Stores all messages of a session as a single item with a list of messages.
    Uses a simple primary key (session_id).

    Args:
        session_id: Unique identifier for the chat session.
        table_name: Name of the DynamoDB table.
        endpoint_url: DynamoDB endpoint URL (for local emulation).
        region_name: AWS region name.
        aws_access_key_id: AWS access key (optional, for local/dev).
        aws_secret_access_key: AWS secret key (optional, for local/dev).
        ttl: Time-to-live in seconds for the item (None = no expiration).
        primary_key_name: Name of the primary key attribute (default: "session_id").
    """

    def __init__(
        self,
        session_id: str,
        table_name: str,
        endpoint_url: Optional[str] = None,
        region_name: Optional[str] = None,
        aws_access_key_id: Optional[str] = None,
        aws_secret_access_key: Optional[str] = None,
        ttl: Optional[int] = None,
        primary_key_name: str = "session_id",
    ):
        self.session_id = session_id
        self.table_name = table_name
        self.ttl = ttl
        self.primary_key_name = primary_key_name

        # Create boto3 session with the provided credentials
        session = boto3.Session(
            aws_access_key_id=aws_access_key_id,
            aws_secret_access_key=aws_secret_access_key,
            region_name=region_name,
        )

        # Initialize LangChain's DynamoDB chat history adapter
        self._history = DynamoDBChatMessageHistory(
            table_name=table_name,
            session_id=session_id,
            ttl=ttl,
            boto3_session=session,
            endpoint_url=endpoint_url,
            primary_key_name=primary_key_name,
        )

    def add_message(self, role: str, content: str) -> None:
        """
        Add a message to the chat history.

        Args:
            role: 'user' or 'assistant'.
            content: Message content.

        Raises:
            ValueError: If role is invalid.
        """
        if role not in ("user", "assistant"):
            raise ValueError(f"Rol inválido: {role}. Debe ser 'user' o 'assistant'.")

        if role == "user":
            self._history.add_user_message(content)
        else:
            self._history.add_ai_message(content)

    def get_messages(self) -> List[Dict[str, str]]:
        """
        Retrieve all messages in chronological order.

        Returns:
            List of dicts with 'role' and 'content' keys.
        """
        messages = self._history.messages
        return [
            {
                "role": "user" if isinstance(m, HumanMessage) else "assistant",
                "content": m.content,
            }
            for m in messages
        ]

    def get_context(self) -> str:
        """
        Format the history as a single string for prompt injection.

        Returns:
            Formatted string with "Usuario:" and "Asistente:" prefixes.
            Empty string if no messages.
        """
        messages = self.get_messages()
        if not messages:
            return ""

        lines = []
        for msg in messages:
            role = "Usuario" if msg["role"] == "user" else "Asistente"
            lines.append(f"{role}: {msg['content']}")
        return "\n".join(lines)

    def clear(self) -> None:
        """Delete all messages for this session."""
        self._history.clear()

    def get_token_count(self) -> int:
        """
        Estimate token count using a heuristic (4 chars ≈ 1 token).

        Returns:
            Estimated number of tokens.
        """
        messages = self.get_messages()
        total_chars = sum(len(msg["content"]) for msg in messages)
        return total_chars // 4


def create_dynamodb_memory(
    session_id: str,
    table_name: Optional[str] = None,
    ttl: Optional[int] = None,
    primary_key_name: str = "session_id",
) -> DynamoDBMemory:
    """
    Factory function to create a DynamoDBMemory instance with global settings.

    Args:
        session_id: Unique session identifier.
        table_name: Optional override for table name.
        ttl: Optional override for TTL (seconds).
        primary_key_name: Primary key attribute name.

    Returns:
        Configured DynamoDBMemory instance.
    """
    if table_name is None:
        table_name = settings.DYNAMODB_CHAT_HISTORY_TABLE

    if ttl is None:
        ttl = getattr(settings, "DYNAMODB_CHAT_HISTORY_TTL", None)

    return DynamoDBMemory(
        session_id=session_id,
        table_name=table_name,
        endpoint_url=settings.DYNAMODB_ENDPOINT_URL,
        region_name=settings.DYNAMODB_REGION,
        aws_access_key_id=settings.DYNAMODB_ACCESS_KEY_ID,
        aws_secret_access_key=settings.DYNAMODB_SECRET_ACCESS_KEY,
        ttl=ttl,
        primary_key_name=primary_key_name,
    )
