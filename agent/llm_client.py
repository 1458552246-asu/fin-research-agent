"""
Unified LLM Client - single module for all LLM API calls.

Uses OpenAI-compatible API (supports any OpenAI-compatible endpoint).
"""

import httpx
import openai
from typing import Optional, List, Dict

from .config import Config


class LLMClient:
    """
    Unified LLM client for all agents.

    Supports OpenAI-compatible endpoints (including proxied Claude models).
    """

    def __init__(self, temperature: float = 0.3, max_tokens: int = 4000):
        self.api_key = Config.LLM_API_KEY
        self.base_url = Config.LLM_BASE_URL
        self.model = Config.LLM_MODEL
        self.temperature = temperature
        self.max_tokens = max_tokens
        self._client: Optional[openai.OpenAI] = None

    @property
    def client(self) -> openai.OpenAI:
        """Lazy-initialize OpenAI client."""
        if self._client is None:
            http_client = httpx.Client(timeout=120.0)
            self._client = openai.OpenAI(
                api_key=self.api_key,
                base_url=self.base_url,
                http_client=http_client,
            )
        return self._client

    @property
    def is_configured(self) -> bool:
        """Check if API credentials are available."""
        return bool(self.api_key)

    def chat(
        self,
        prompt: str,
        system: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> str:
        """
        Send a chat completion request.

        Args:
            prompt: User message content
            system: Optional system prompt
            temperature: Override default temperature
            max_tokens: Override default max_tokens

        Returns:
            Response text content

        Raises:
            LLMError if API call fails and no fallback available.
        """
        if not self.is_configured:
            raise LLMError("LLM API key not configured. Set LLM_API_KEY in .env")

        messages: List[Dict[str, str]] = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temperature if temperature is not None else self.temperature,
                max_tokens=max_tokens or self.max_tokens,
            )
            return response.choices[0].message.content
        except Exception as e:
            raise LLMError(f"LLM API call failed: {e}") from e


class LLMError(Exception):
    """Raised when LLM API call fails."""
    pass
