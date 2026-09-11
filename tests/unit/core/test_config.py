# tests/unit/core/test_config.py
"""
Unit tests for the application configuration.

Verifies default values, required fields, and validation errors.
"""

import time
from pathlib import Path
from typing import Dict

import pytest
from pydantic import ValidationError

from app.core.config import Settings
from app.core.enums import Environments, LogLevels


def create_env_file_with_values(values: Dict[str, str]) -> Path:
    """Create a temporary .env file with the given key-value pairs."""
    filename = f"/tmp/.{time.time():.3f}.env"
    env_file = Path(filename)
    with open(env_file, "w") as f:
        for key, value in values.items():
            f.write(f"{key}={value}\n")
    return env_file


# Minimal valid environment (required fields only)
def minimal_env(**overrides) -> Dict[str, str]:
    """Return a dictionary with the minimum required environment variables."""
    base = {
        "DYNAMODB_CHAT_HISTORY_TABLE": "test_chat_history",
        "DYNAMODB_INVENTORY_CACHE_TABLE": "test_inventory_cache",
        "OPENSEARCH_INDEX_NAME": "test_index",
        "OPENSEARCH_INDEX_DIMENSIONS": "768",
        "BEDROCK_REGION": "us-east-1",
        "BEDROCK_EMBEDDINGS_MODEL": "amazon.titan-embed-text-v1",
        "BEDROCK_LLM_MODEL": "anthropic.claude-3-haiku-20240307-v1:0",
    }
    base.update(overrides)
    return base


class TestConfig:
    """Test suite for Settings."""

    def test_default_values_for_optional_fields(self) -> None:
        """
        Given: A .env file with only the required fields.
        When: Settings is loaded.
        Then: Optional fields take their default values.
        """
        # Given
        env_file = create_env_file_with_values(minimal_env())

        try:
            # When
            settings = Settings.from_env_file(env_file)

            # Then
            assert settings.AGENT_ENVIRONMENT == Environments.DEVELOPMENT
            assert settings.AGENT_LOG_LEVEL == LogLevels.INFO
            assert settings.AGENT_NAME == "pharma-assistant"
            assert settings.IA_MODEL_TEMPERATURE == 0.0

            assert settings.DYNAMODB_ENDPOINT_URL == "http://localhost:4566"
            assert settings.DYNAMODB_REGION == "us-east-1"
            assert settings.DYNAMODB_ACCESS_KEY_ID == "test"
            assert settings.DYNAMODB_SECRET_ACCESS_KEY == "test"

            assert settings.OPENSEARCH_HOST == "localhost"
            assert settings.OPENSEARCH_PORT == 9400
            assert settings.OPENSEARCH_INDEX_METRIC == "cosine"
            assert settings.OPENSEARCH_ACCESS_KEY_ID == "test"
            assert settings.OPENSEARCH_SECRET_ACCESS_KEY == "test"
            assert settings.OPENSEARCH_REGION == "us-east-1"

            assert settings.BEDROCK_ENDPOINT_URL == "http://localhost:4566"
            assert settings.BEDROCK_ACCESS_KEY_ID == "test"
            assert settings.BEDROCK_SECRET_ACCESS_KEY == "test"

            assert settings.GOOGLE_APPLICATION_CREDENTIALS == ""
            assert settings.SPREADSHEET_ID == ""
        finally:
            env_file.unlink(missing_ok=True)

    def test_valid_values_from_env(self) -> None:
        """
        Given: A .env file with all values set to non-default values.
        When: Settings is loaded.
        Then: All fields reflect the provided values.
        """
        # Given
        env_vars = minimal_env(
            AGENT_ENVIRONMENT="production",
            AGENT_LOG_LEVEL="ERROR",
            AGENT_NAME="custom-agent",
            IA_MODEL_TEMPERATURE="0.7",
            DYNAMODB_ENDPOINT_URL="http://dynamo:4566",
            DYNAMODB_REGION="us-west-2",
            DYNAMODB_ACCESS_KEY_ID="real_key",
            DYNAMODB_SECRET_ACCESS_KEY="real_secret",
            OPENSEARCH_HOST="opensearch",
            OPENSEARCH_PORT="9200",
            OPENSEARCH_INDEX_METRIC="euclidean",
            OPENSEARCH_ACCESS_KEY_ID="opensearch_key",
            OPENSEARCH_SECRET_ACCESS_KEY="opensearch_secret",
            OPENSEARCH_REGION="eu-west-1",
            BEDROCK_ENDPOINT_URL="http://bedrock:4566",
            BEDROCK_ACCESS_KEY_ID="bedrock_key",
            BEDROCK_SECRET_ACCESS_KEY="bedrock_secret",
            GOOGLE_APPLICATION_CREDENTIALS="/path/to/creds.json",
            SPREADSHEET_ID="spreadsheet123",
        )
        env_file = create_env_file_with_values(env_vars)

        try:
            # When
            settings = Settings.from_env_file(env_file)

            # Then
            assert settings.AGENT_ENVIRONMENT == Environments.PRODUCTION
            assert settings.AGENT_LOG_LEVEL == LogLevels.ERROR
            assert settings.AGENT_NAME == "custom-agent"
            assert settings.IA_MODEL_TEMPERATURE == 0.7

            assert settings.DYNAMODB_CHAT_HISTORY_TABLE == "test_chat_history"
            assert settings.DYNAMODB_INVENTORY_CACHE_TABLE == "test_inventory_cache"
            assert settings.DYNAMODB_ENDPOINT_URL == "http://dynamo:4566"
            assert settings.DYNAMODB_REGION == "us-west-2"
            assert settings.DYNAMODB_ACCESS_KEY_ID == "real_key"
            assert settings.DYNAMODB_SECRET_ACCESS_KEY == "real_secret"

            assert settings.OPENSEARCH_HOST == "opensearch"
            assert settings.OPENSEARCH_PORT == 9200
            assert settings.OPENSEARCH_INDEX_NAME == "test_index"
            assert settings.OPENSEARCH_INDEX_DIMENSIONS == 768
            assert settings.OPENSEARCH_INDEX_METRIC == "euclidean"
            assert settings.OPENSEARCH_ACCESS_KEY_ID == "opensearch_key"
            assert settings.OPENSEARCH_SECRET_ACCESS_KEY == "opensearch_secret"
            assert settings.OPENSEARCH_REGION == "eu-west-1"

            assert settings.BEDROCK_REGION == "us-east-1"
            assert settings.BEDROCK_EMBEDDINGS_MODEL == "amazon.titan-embed-text-v1"
            assert settings.BEDROCK_LLM_MODEL == "anthropic.claude-3-haiku-20240307-v1:0"
            assert settings.BEDROCK_ENDPOINT_URL == "http://bedrock:4566"
            assert settings.BEDROCK_ACCESS_KEY_ID == "bedrock_key"
            assert settings.BEDROCK_SECRET_ACCESS_KEY == "bedrock_secret"

            assert settings.GOOGLE_APPLICATION_CREDENTIALS == "/path/to/creds.json"
            assert settings.SPREADSHEET_ID == "spreadsheet123"
        finally:
            env_file.unlink(missing_ok=True)

    def test_missing_dynamodb_chat_history_table_raises_error(self) -> None:
        """
        Given: A .env file without DYNAMODB_CHAT_HISTORY_TABLE.
        When: Settings is loaded.
        Then: ValidationError is raised.
        """
        # Given
        env = minimal_env()
        del env["DYNAMODB_CHAT_HISTORY_TABLE"]
        env_file = create_env_file_with_values(env)

        try:
            # When / Then
            with pytest.raises(ValidationError) as exc_info:
                Settings.from_env_file(env_file)
            assert "DYNAMODB_CHAT_HISTORY_TABLE" in str(exc_info.value)
        finally:
            env_file.unlink(missing_ok=True)

    def test_missing_opensearch_index_name_raises_error(self) -> None:
        """
        Given: A .env file without OPENSEARCH_INDEX_NAME.
        When: Settings is loaded.
        Then: ValidationError is raised.
        """
        # Given
        env = minimal_env()
        del env["OPENSEARCH_INDEX_NAME"]
        env_file = create_env_file_with_values(env)

        try:
            # When / Then
            with pytest.raises(ValidationError) as exc_info:
                Settings.from_env_file(env_file)
            assert "OPENSEARCH_INDEX_NAME" in str(exc_info.value)
        finally:
            env_file.unlink(missing_ok=True)

    def test_missing_bedrock_region_raises_error(self) -> None:
        """
        Given: A .env file without BEDROCK_REGION.
        When: Settings is loaded.
        Then: ValidationError is raised.
        """
        # Given
        env = minimal_env()
        del env["BEDROCK_REGION"]
        env_file = create_env_file_with_values(env)

        try:
            # When / Then
            with pytest.raises(ValidationError) as exc_info:
                Settings.from_env_file(env_file)
            assert "BEDROCK_REGION" in str(exc_info.value)
        finally:
            env_file.unlink(missing_ok=True)

    def test_missing_bedrock_llm_model_raises_error(self) -> None:
        """
        Given: A .env file without BEDROCK_LLM_MODEL.
        When: Settings is loaded.
        Then: ValidationError is raised.
        """
        # Given
        env = minimal_env()
        del env["BEDROCK_LLM_MODEL"]
        env_file = create_env_file_with_values(env)

        try:
            # When / Then
            with pytest.raises(ValidationError) as exc_info:
                Settings.from_env_file(env_file)
            assert "BEDROCK_LLM_MODEL" in str(exc_info.value)
        finally:
            env_file.unlink(missing_ok=True)

    def test_invalid_environment_raises_error(self) -> None:
        """
        Given: AGENT_ENVIRONMENT set to an invalid value.
        When: Settings is loaded.
        Then: ValidationError is raised.
        """
        # Given
        env_file = create_env_file_with_values(minimal_env(AGENT_ENVIRONMENT="invalid_env"))

        try:
            # When / Then
            with pytest.raises(ValidationError) as exc_info:
                Settings.from_env_file(env_file)
            assert "AGENT_ENVIRONMENT" in str(exc_info.value)
        finally:
            env_file.unlink(missing_ok=True)

    def test_invalid_log_level_raises_error(self) -> None:
        """
        Given: AGENT_LOG_LEVEL set to an invalid value.
        When: Settings is loaded.
        Then: ValidationError is raised.
        """
        # Given
        env_file = create_env_file_with_values(minimal_env(AGENT_LOG_LEVEL="TRACE"))

        try:
            # When / Then
            with pytest.raises(ValidationError) as exc_info:
                Settings.from_env_file(env_file)
            assert "AGENT_LOG_LEVEL" in str(exc_info.value)
        finally:
            env_file.unlink(missing_ok=True)

    def test_invalid_temperature_raises_error(self) -> None:
        """
        Given: IA_MODEL_TEMPERATURE set to a non-numeric value.
        When: Settings is loaded.
        Then: ValidationError is raised.
        """
        # Given
        env_file = create_env_file_with_values(minimal_env(IA_MODEL_TEMPERATURE="very-hot"))

        try:
            # When / Then
            with pytest.raises(ValidationError) as exc_info:
                Settings.from_env_file(env_file)
            assert "IA_MODEL_TEMPERATURE" in str(exc_info.value)
        finally:
            env_file.unlink(missing_ok=True)
