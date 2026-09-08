"""
Bedrock module for LLM and embeddings.

Exports:
    - BedrockEmbeddingsWrapper: Wrapper for Bedrock embeddings.
    - create_bedrock_embeddings: Factory function for embeddings.
    - BedrockLLM: Wrapper for Bedrock chat models.
    - create_bedrock_llm: Factory function for LLM.
"""

from .embeddings import BedrockEmbeddingsWrapper, create_bedrock_embeddings
from .llm import BedrockLLM, create_bedrock_llm

__all__ = [
    "BedrockEmbeddingsWrapper",
    "create_bedrock_embeddings",
    "BedrockLLM",
    "create_bedrock_llm",
]
