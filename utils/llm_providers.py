"""
LLM Provider Abstraction Layer
Supports both Anthropic direct API and AWS Bedrock
"""

import json
import logging
import os
from abc import ABC, abstractmethod
from typing import Optional

_log = logging.getLogger(__name__)

try:
    import anthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False

try:
    import boto3
    BOTO3_AVAILABLE = True
except ImportError:
    BOTO3_AVAILABLE = False


class LLMProvider(ABC):
    """Abstract base class for LLM providers."""

    @abstractmethod
    def call_model(self, system_prompt: str, user_message: str, max_tokens: int = 2000) -> str:
        """
        Call the LLM with a system prompt and user message.

        Args:
            system_prompt: System-level instructions for the model
            user_message: User's input message
            max_tokens: Maximum tokens in response

        Returns:
            Model's text response
        """
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """Check if the provider is properly configured and available."""
        pass

    @abstractmethod
    def get_model_name(self) -> str:
        """Get the model identifier/name."""
        pass


class AnthropicProvider(LLMProvider):
    """Provider for direct Anthropic Claude API."""

    def __init__(self, api_key: Optional[str] = None, model: str = "claude-sonnet-4-6"):
        self.api_key = api_key
        self.client = None
        self.model = model

        if ANTHROPIC_AVAILABLE and self.api_key:
            try:
                self.client = anthropic.Anthropic(api_key=self.api_key)
            except Exception as e:
                _log.warning("Failed to initialize Anthropic client: %s", type(e).__name__)
                self.client = None

    def call_model(self, system_prompt: str, user_message: str, max_tokens: int = 2000) -> str:
        """Call Anthropic Claude API."""
        if not self.client:
            raise RuntimeError("Anthropic client not initialized")

        message = self.client.messages.create(
            model=self.model,
            max_tokens=max_tokens,
            system=system_prompt,
            messages=[
                {"role": "user", "content": user_message}
            ]
        )

        return message.content[0].text

    def is_available(self) -> bool:
        """Check if Anthropic is available."""
        return ANTHROPIC_AVAILABLE and self.client is not None

    def get_model_name(self) -> str:
        """Get model name."""
        return f"Anthropic Claude ({self.model})"

    def test_connection(self) -> bool:
        """Test connection by making a minimal API call."""
        try:
            response = self.call_model(
                system_prompt="You are a helpful assistant.",
                user_message="Say 'OK' if you can hear me.",
                max_tokens=10
            )
            return len(response) > 0
        except Exception:
            return False


class BedrockProvider(LLMProvider):
    """Provider for AWS Bedrock Claude API."""

    def __init__(
        self,
        region: str = "us-east-1",
        model_id: str = "us.anthropic.claude-sonnet-4-6",
        aws_access_key_id: Optional[str] = None,
        aws_secret_access_key: Optional[str] = None
    ):
        """
        Initialize AWS Bedrock provider.

        Args:
            region: AWS region
            model_id: Bedrock model ID
            aws_access_key_id: AWS access key (optional, uses default credentials if None)
            aws_secret_access_key: AWS secret key (optional)
        """
        self.region = region
        self.model_id = model_id
        self.client = None

        if not BOTO3_AVAILABLE:
            _log.warning("boto3 not available — install with: pip install boto3")
            return

        try:
            # Build client kwargs
            kwargs = {"region_name": region}
            if aws_access_key_id and aws_secret_access_key:
                kwargs["aws_access_key_id"] = aws_access_key_id
                kwargs["aws_secret_access_key"] = aws_secret_access_key

            self.client = boto3.client("bedrock-runtime", **kwargs)
        except Exception as e:
            _log.warning("Failed to initialize Bedrock client: %s", type(e).__name__)
            self.client = None

    def call_model(self, system_prompt: str, user_message: str, max_tokens: int = 2000) -> str:
        """Call AWS Bedrock Claude API."""
        if not self.client:
            raise RuntimeError("Bedrock client not initialized")

        # Bedrock request format for Claude
        body = json.dumps({
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": max_tokens,
            "system": system_prompt,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": user_message
                        }
                    ]
                }
            ]
        })

        try:
            response = self.client.invoke_model(
                modelId=self.model_id,
                body=body
            )

            # Parse response
            response_body = json.loads(response['body'].read())
            return response_body['content'][0]['text']

        except Exception as e:
            raise RuntimeError(f"Bedrock API call failed: {e}")

    def is_available(self) -> bool:
        """Check if Bedrock is available."""
        return BOTO3_AVAILABLE and self.client is not None

    def get_model_name(self) -> str:
        """Get model name."""
        return f"AWS Bedrock ({self.model_id})"

    def test_connection(self) -> bool:
        """Test connection by making a minimal API call."""
        try:
            response = self.call_model(
                system_prompt="You are a helpful assistant.",
                user_message="Say 'OK' if you can hear me.",
                max_tokens=10
            )
            return len(response) > 0
        except Exception:
            return False


class DummyProvider(LLMProvider):
    """Dummy provider that returns no-op responses (for testing without API)."""

    def call_model(self, system_prompt: str, user_message: str, max_tokens: int = 2000) -> str:
        """Return empty response."""
        return ""  # Will trigger fallback to dummy data in query generation

    def is_available(self) -> bool:
        """Always available."""
        return True

    def get_model_name(self) -> str:
        """Get model name."""
        return "Dummy Provider (No API)"


def create_llm_provider(provider_type: str, config: dict) -> LLMProvider:
    """
    Factory function to create LLM providers.

    Args:
        provider_type: "anthropic", "bedrock", or "dummy"
        config: Configuration dictionary with provider-specific keys

    Returns:
        LLMProvider instance

    Raises:
        ValueError: If provider_type is unknown
    """
    if provider_type == "anthropic":
        return AnthropicProvider(
            api_key=config.get("api_key"),
            model=config.get("model", "claude-sonnet-4-6")
        )

    elif provider_type == "bedrock":
        return BedrockProvider(
            region=config.get("region", "us-east-1"),
            model_id=config.get("model_id", "us.anthropic.claude-3-5-sonnet-20241022-v2:0"),
            aws_access_key_id=config.get("aws_access_key_id"),
            aws_secret_access_key=config.get("aws_secret_access_key")
        )

    elif provider_type == "dummy":
        return DummyProvider()

    else:
        raise ValueError(f"Unknown provider type: {provider_type}")


# Test the providers
if __name__ == "__main__":
    print("Testing LLM Providers...\n")

    # Test Anthropic
    print("1. Anthropic Provider:")
    anthropic_provider = AnthropicProvider()
    print(f"   Available: {anthropic_provider.is_available()}")
    print(f"   Model: {anthropic_provider.get_model_name()}\n")

    # Test Bedrock
    print("2. Bedrock Provider:")
    bedrock_provider = BedrockProvider()
    print(f"   Available: {bedrock_provider.is_available()}")
    print(f"   Model: {bedrock_provider.get_model_name()}\n")

    # Test Dummy
    print("3. Dummy Provider:")
    dummy_provider = DummyProvider()
    print(f"   Available: {dummy_provider.is_available()}")
    print(f"   Model: {dummy_provider.get_model_name()}\n")

    # Test factory
    print("4. Factory Function:")
    provider = create_llm_provider("dummy", {})
    print(f"   Created: {provider.get_model_name()}")
