"""
Bedrock embeddings using LangChain.

This module provides a wrapper around BedrockEmbeddings from LangChain,
replacing OllamaEmbeddings as the embedding provider for RAG.
"""

from typing import Optional, Any

from langchain_aws import BedrockEmbeddings
from langchain_core.embeddings import Embeddings

from app.core.config import settings


class BedrockEmbeddingsWrapper(Embeddings):
    """
    Wrapper for Bedrock embeddings with dependency injection.

    Args:
        model_id: The model ID to use for embeddings (e.g., "amazon.titan-embed-text-v2:0").
        endpoint_url: Bedrock endpoint URL (for Floci or AWS).
        region_name: AWS region.
        aws_access_key_id: AWS access key (optional, for local/dev).
        aws_secret_access_key: AWS secret key (optional, for local/dev).
    """

    def __init__(
        self,
        model_id: Optional[str] = None,
        endpoint_url: Optional[str] = None,
        region_name: Optional[str] = None,
        aws_access_key_id: Optional[str] = None,
        aws_secret_access_key: Optional[str] = None,
    ):
        self.model_id = model_id or settings.BEDROCK_EMBEDDINGS_MODEL
        self.endpoint_url = endpoint_url or settings.BEDROCK_ENDPOINT_URL
        self.region_name = region_name or settings.BEDROCK_REGION
        self.aws_access_key_id = aws_access_key_id or settings.BEDROCK_ACCESS_KEY_ID
        self.aws_secret_access_key = aws_secret_access_key or settings.BEDROCK_SECRET_ACCESS_KEY

        # Initialize the LangChain Bedrock client
        self._client = BedrockEmbeddings(
            model_id=self.model_id,
            endpoint_url=self.endpoint_url,
            region_name=self.region_name,
            aws_access_key_id=self.aws_access_key_id,
            aws_secret_access_key=self.aws_secret_access_key,
        )

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        """Embed a list of documents."""
        return self._client.embed_documents(texts)

    def embed_query(self, text: str) -> list[float]:
        """Embed a single query."""
        return self._client.embed_query(text)

    def __call__(self, text: str) -> list[float]:
        """Allow the instance to be called directly as a function."""
        return self.embed_query(text)


def create_bedrock_embeddings(
    model_id: Optional[str] = None,
    endpoint_url: Optional[str] = None,
    region_name: Optional[str] = None,
    aws_access_key_id: Optional[str] = None,
    aws_secret_access_key: Optional[str] = None,
) -> BedrockEmbeddingsWrapper:
    """
    Factory function to create a BedrockEmbeddingsWrapper with global settings.

    Returns:
        Configured BedrockEmbeddingsWrapper instance.
    """
    return BedrockEmbeddingsWrapper(
        model_id=model_id,
        endpoint_url=endpoint_url,
        region_name=region_name,
        aws_access_key_id=aws_access_key_id,
        aws_secret_access_key=aws_secret_access_key,
    )
