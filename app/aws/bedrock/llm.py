"""
Bedrock LLM using LangChain.

This module provides a wrapper around ChatBedrock from LangChain,
replacing ChatOllama as the LLM provider for the agent.
"""

from typing import Optional, Any, List, Dict, Generator

from langchain_aws import ChatBedrock
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from langchain_core.language_models import BaseChatModel

from app.core.config import settings


class BedrockLLM:
    """
    Wrapper for Bedrock LLM with dependency injection.

    Args:
        model_id: The model ID to use for chat (e.g., "anthropic.claude-3-haiku-20240307-v1:0").
        endpoint_url: Bedrock endpoint URL (for Floci or AWS).
        region_name: AWS region.
        aws_access_key_id: AWS access key (optional, for local/dev).
        aws_secret_access_key: AWS secret key (optional, for local/dev).
        temperature: Temperature for generation (0.0 to 1.0).
        max_tokens: Maximum tokens to generate.
        stop: Optional stop sequences.
        model_kwargs: Additional model-specific parameters.
    """

    def __init__(
        self,
        model_id: Optional[str] = None,
        endpoint_url: Optional[str] = None,
        region_name: Optional[str] = None,
        aws_access_key_id: Optional[str] = None,
        aws_secret_access_key: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        stop: Optional[List[str]] = None,
        model_kwargs: Optional[Dict[str, Any]] = None,
    ):
        self.model_id = model_id or settings.BEDROCK_LLM_MODEL
        self.endpoint_url = endpoint_url or settings.BEDROCK_ENDPOINT_URL
        self.region_name = region_name or settings.BEDROCK_REGION
        self.aws_access_key_id = aws_access_key_id or settings.BEDROCK_ACCESS_KEY_ID
        self.aws_secret_access_key = aws_secret_access_key or settings.BEDROCK_SECRET_ACCESS_KEY
        self.temperature = temperature if temperature is not None else settings.IA_MODEL_TEMPERATURE
        self.max_tokens = max_tokens or 4096
        self.stop = stop
        self.model_kwargs = model_kwargs or {}

        # Initialize the LangChain Bedrock client
        self._client = ChatBedrock(
            model_id=self.model_id,
            endpoint_url=self.endpoint_url,
            region_name=self.region_name,
            aws_access_key_id=self.aws_access_key_id,
            aws_secret_access_key=self.aws_secret_access_key,
            temperature=self.temperature,
            max_tokens=self.max_tokens,
            stop=self.stop,
            model_kwargs=self.model_kwargs,
        )

    def invoke(self, prompt: str) -> str:
        """
        Generate a response for a single prompt.

        Args:
            prompt: The input text.

        Returns:
            The generated response string.
        """
        messages = [HumanMessage(content=prompt)]
        response = self._client.invoke(messages)
        return response.content

    def generate(self, messages: List[BaseMessage]) -> str:
        """
        Generate a response for a list of messages (conversation).

        Args:
            messages: List of messages (HumanMessage, AIMessage, etc.).

        Returns:
            The generated response string.
        """
        response = self._client.invoke(messages)
        return response.content

    def stream(self, prompt: str) -> Generator[str, None, None]:
        """
        Stream a response for a single prompt.

        Note: Since Floci does not support streaming (InvokeModelWithResponseStream),
        this returns the full response as a single chunk.
        """
        messages = [HumanMessage(content=prompt)]
        # Use invoke (non-streaming) to get the full response
        response = self._client.invoke(messages)
        yield response.content

    def get_chat_model(self) -> BaseChatModel:
        """
        Return the underlying ChatBedrock instance.

        This is useful for cases where you need the full LangChain interface.
        """
        return self._client


def create_bedrock_llm(
    model_id: Optional[str] = None,
    endpoint_url: Optional[str] = None,
    region_name: Optional[str] = None,
    aws_access_key_id: Optional[str] = None,
    aws_secret_access_key: Optional[str] = None,
    temperature: Optional[float] = None,
    max_tokens: Optional[int] = None,
    stop: Optional[List[str]] = None,
    model_kwargs: Optional[Dict[str, Any]] = None,
) -> BedrockLLM:
    """
    Factory function to create a BedrockLLM instance with global settings.

    Returns:
        Configured BedrockLLM instance.
    """
    return BedrockLLM(
        model_id=model_id,
        endpoint_url=endpoint_url,
        region_name=region_name,
        aws_access_key_id=aws_access_key_id,
        aws_secret_access_key=aws_secret_access_key,
        temperature=temperature,
        max_tokens=max_tokens,
        stop=stop,
        model_kwargs=model_kwargs,
    )
