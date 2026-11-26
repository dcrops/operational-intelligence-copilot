import os

from openai import OpenAI

from src.operational_intelligence.llm.narrative_config import (
    DEFAULT_OPENAI_MODEL,
    LUNA_CHAT_MODEL,
)
from src.operational_intelligence.llm.protocol import LLMClient

import truststore

truststore.inject_into_ssl()


class OpenAIClient:
    """OpenAI-backed implementation of LLMClient."""

    def __init__(
        self,
        model_name: str = DEFAULT_OPENAI_MODEL,
        timeout_seconds: int = 30,
        max_retries: int = 2,
    ) -> None:
        api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key:
            raise RuntimeError("OPENAI_API_KEY environment variable is not set")

        self._model_name = model_name
        self._client = OpenAI(api_key=api_key)
        self._max_retries = max_retries
        self._timeout_seconds = timeout_seconds

    def _request_params(
        self,
        messages: list[dict[str, str]],
        temperature: float,
    ) -> dict:
        """Build Chat Completions parameters for the configured model.

        gpt-4.1-mini keeps the historical model, messages, temperature, and
        timeout arguments and does not send reasoning_effort. The exact model
        id gpt-6-luna sends reasoning_effort none, keeps the timeout, and omits
        temperature. Neither profile adds a token limit.
        """
        params: dict = {
            "model": self._model_name,
            "messages": messages,
            "timeout": getattr(self, "_timeout_seconds", 30),
        }
        if self._model_name == LUNA_CHAT_MODEL:
            params["reasoning_effort"] = "none"
            return params
        params["temperature"] = temperature
        return params

    def complete(
        self,
        messages: list[dict[str, str]],
        temperature: float = 0.0,
    ) -> str:
        import time

        attempts = 0
        last_exc = None

        while attempts <= getattr(self, '_max_retries', 2):
            try:
                response = self._client.chat.completions.create(
                    **self._request_params(messages, temperature),
                )
                content = response.choices[0].message.content
                if not content:
                    raise RuntimeError("OpenAI API returned an empty response")
                return content.strip()
            except Exception as exc:
                last_exc = exc
                attempts += 1
                if attempts > getattr(self, '_max_retries', 2):
                    break
                time.sleep(1)  # brief pause before retry

        raise RuntimeError(f"OpenAI API request failed after {getattr(self, '_max_retries', 2)+1} attempts: {last_exc}") from last_exc
