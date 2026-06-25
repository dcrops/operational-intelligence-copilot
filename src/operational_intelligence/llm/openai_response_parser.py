"""Parse labelled narrative sections from OpenAI text responses."""

from __future__ import annotations

from dataclasses import dataclass

from src.operational_intelligence.llm.narrative_errors import NarrativeGenerationError

_SECTION_KEY_MESSAGE = "KEY MESSAGE:"
_SECTION_EXECUTIVE_NARRATIVE = "EXECUTIVE NARRATIVE:"
_SECTION_LIMITATIONS = "LIMITATIONS:"


@dataclass(frozen=True)
class ParsedNarrativeSections:
    """Parsed narrative content extracted from provider text."""

    key_message: str
    executive_narrative: str
    limitations: str


class OpenAINarrativeResponseParser:
    """Parse fixed labelled sections from LLM text."""

    def parse(self, text: str) -> ParsedNarrativeSections:
        """Extract narrative sections or raise NarrativeGenerationError."""
        normalized = text.strip()
        if not normalized:
            raise NarrativeGenerationError("OpenAI response was empty")

        key_message = self._extract_section(
            normalized,
            _SECTION_KEY_MESSAGE,
            next_labels=(_SECTION_EXECUTIVE_NARRATIVE,),
        )
        executive_narrative = self._extract_section(
            normalized,
            _SECTION_EXECUTIVE_NARRATIVE,
            next_labels=(_SECTION_LIMITATIONS,),
        )
        limitations = self._extract_section(
            normalized,
            _SECTION_LIMITATIONS,
            next_labels=(),
        )

        if not key_message or not executive_narrative:
            raise NarrativeGenerationError(
                "OpenAI response missing required KEY MESSAGE or EXECUTIVE NARRATIVE sections"
            )

        return ParsedNarrativeSections(
            key_message=key_message,
            executive_narrative=executive_narrative,
            limitations=limitations or "None stated.",
        )

    def _extract_section(
        self,
        text: str,
        label: str,
        *,
        next_labels: tuple[str, ...],
    ) -> str:
        start = text.find(label)
        if start == -1:
            return ""

        content_start = start + len(label)
        end = len(text)
        for next_label in next_labels:
            next_index = text.find(next_label, content_start)
            if next_index != -1:
                end = min(end, next_index)

        return text[content_start:end].strip()
