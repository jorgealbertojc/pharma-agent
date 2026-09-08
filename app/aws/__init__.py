"""
AWS module for local AWS services emulation with Floci.

This package provides adapters for:
- Bedrock: LLM and embeddings (stub for local development).
- DynamoDB: Chat history and inventory cache.
- OpenSearch: Vector store for RAG (real mode with Floci).

All modules are designed to work with Floci endpoints and credentials
from the global settings.
"""

from .bedrock import (
    BedrockEmbeddingsWrapper,
    create_bedrock_embeddings,
    BedrockLLM,
    create_bedrock_llm,
)
from .dynamodb import (
    DynamoDBMemory,
    create_dynamodb_memory,
    DynamoDBCache,
    create_dynamodb_cache,
)
from .opensearch import OpenSearchVectorStore

__all__ = [
    # Bedrock
    "BedrockEmbeddingsWrapper",
    "create_bedrock_embeddings",
    "BedrockLLM",
    "create_bedrock_llm",
    # DynamoDB
    "DynamoDBMemory",
    "create_dynamodb_memory",
    "DynamoDBCache",
    "create_dynamodb_cache",
    # OpenSearch
    "OpenSearchVectorStore",
]
