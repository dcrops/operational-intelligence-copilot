"""Test doubles for narrative provider tests."""

from __future__ import annotations


class FakeLLMClient:
    """Minimal LLMClient test double."""

    def __init__(
        self,
        *,
        response: str | None = None,
        exc: Exception | None = None,
        calls: list[dict] | None = None,
    ) -> None:
        self._response = response
        self._exc = exc
        self.calls = calls if calls is not None else []

    def complete(self, messages: list[dict[str, str]], temperature: float = 0.0) -> str:
        self.calls.append({"messages": messages, "temperature": temperature})
        if self._exc is not None:
            raise self._exc
        if self._response is None:
            raise RuntimeError("FakeLLMClient has no configured response")
        return self._response
