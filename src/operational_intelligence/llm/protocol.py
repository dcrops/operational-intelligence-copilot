from typing import Protocol


class LLMClient(Protocol):
    """Vendor-neutral interface for text completion."""

    def complete(
        self,
        messages: list[dict[str, str]],
        temperature: float = 0.0,
    ) -> str:
        """Return the assistant's text response for the given chat messages."""
        ...
