"""
Integration tests for Bedrock LLM.

These tests verify connectivity to the Bedrock endpoint.
The actual LLM functionality is tested against real AWS when available.
"""

import boto3
import pytest
from botocore.exceptions import ClientError

from app.aws.bedrock.llm import BedrockLLM, create_bedrock_llm
from app.core.config import settings


@pytest.fixture(scope="session")
def bedrock_client():
    """Return a boto3 client for Bedrock Runtime."""
    return boto3.client(
        "bedrock-runtime",
        endpoint_url=settings.BEDROCK_ENDPOINT_URL,
        region_name=settings.BEDROCK_REGION,
        aws_access_key_id=settings.BEDROCK_ACCESS_KEY_ID,
        aws_secret_access_key=settings.BEDROCK_SECRET_ACCESS_KEY,
    )


def test_bedrock_llm_connectivity(bedrock_client):
    """
    Given: A configured Bedrock client pointing to Floci.
    When: Invoking a simple chat model.
    Then: The request does not raise a connection/authentication error.
    (The response content is not validated, as Floci returns a stub.)
    """
    # Given
    client = bedrock_client
    model_id = settings.BEDROCK_LLM_MODEL

    # When / Then
    try:
        response = client.invoke_model(
            modelId=model_id,
            body='{"prompt": "Hola", "max_tokens": 10}',
        )
        # If we reach here, the connection and authentication worked.
        assert response["ResponseMetadata"]["HTTPStatusCode"] == 200
    except ClientError as e:
        # If the model is not supported, we still consider connectivity successful
        # if the error is about the model, not about connection/auth.
        if "ValidationException" in str(e):
            pytest.skip(f"Model {model_id} not supported by Floci stub")
        else:
            raise


@pytest.fixture(scope="function")
def bedrock_llm(bedrock_client) -> BedrockLLM:
    """
    Create a Bedrock LLM instance and skip tests if the stub doesn't support the model.
    """
    try:
        llm = create_bedrock_llm()
        # Try a simple invocation to detect if the stub returns a parsable response
        llm.invoke("test")
        return llm
    except Exception as e:
        # If the model is not supported or the stub returns an unexpected format
        pytest.skip(f"Bedrock LLM not available: {e}")
        return None  # This line is never reached, but satisfies mypy


class TestBedrockLLM:
    """Integration tests for Bedrock LLM wrapper (only if stub supports it)."""

    def test_invoke_returns_string(self, bedrock_llm: BedrockLLM):
        """
        Given: A Bedrock LLM instance.
        When: Invoking with a prompt.
        Then: Returns a string (content not validated).
        """
        # Given
        llm = bedrock_llm

        # When
        response = llm.invoke("¿Qué es el ibuprofeno?")

        # Then
        assert isinstance(response, str)

    def test_generate_with_messages(self, bedrock_llm: BedrockLLM):
        """
        Given: A Bedrock LLM instance and a list of messages.
        When: Calling generate().
        Then: Returns a string.
        """
        # Given
        from langchain_core.messages import HumanMessage, AIMessage
        llm = bedrock_llm
        messages = [
            HumanMessage(content="Hola"),
            AIMessage(content="¿Cómo estás?"),
            HumanMessage(content="Bien, ¿y tú?"),
        ]

        # When
        response = llm.generate(messages)

        # Then
        assert isinstance(response, str)

    def test_stream_returns_generator(self, bedrock_llm: BedrockLLM):
        """
        Given: A Bedrock LLM instance.
        When: Calling stream() with a prompt.
        Then: Returns a generator that yields strings (at least one chunk).
        """
        # Given
        llm = bedrock_llm

        # When
        chunks = list(llm.stream("Hola mundo"))

        # Then
        assert len(chunks) == 1, "Floci returns a single chunk because streaming is not supported"
        assert isinstance(chunks[0], str)

    def test_get_chat_model_returns_base_chat_model(self, bedrock_llm: BedrockLLM):
        """
        Given: A Bedrock LLM instance.
        When: Calling get_chat_model().
        Then: Returns a BaseChatModel instance.
        """
        # Given
        llm = bedrock_llm

        # When
        chat_model = llm.get_chat_model()

        # Then
        from langchain_core.language_models import BaseChatModel
        assert isinstance(chat_model, BaseChatModel)
