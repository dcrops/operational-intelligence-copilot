"""Parse labelled narrative sections from OpenAI text responses."""

from __future__ import annotations

from dataclasses import dataclass

from src.operational_intelligence.llm.narrative_errors import NarrativeGenerationError
from src.operational_intelligence.llm.narrative_governance import (
    ADVISOR_SECTION_LABELS,
    ADVISOR_SECTION_LABEL_LIMITATIONS,
    ADVISOR_SECTION_LABEL_TO_TITLE,
    ADVISOR_SECTION_TITLES,
)
from src.operational_intelligence.llm.narrative_models import NarrativeSection


@dataclass(frozen=True)
class ParsedNarrativeSections:
    """Parsed narrative content extracted from provider text."""

    sections: tuple[NarrativeSection, ...]
    limitations: str


class OpenAINarrativeResponseParser:
    """Parse fixed labelled advisor sections from LLM text."""

    def parse(self, text: str) -> ParsedNarrativeSections:
        """Extract advisor sections or raise NarrativeGenerationError."""
        normalized = text.strip()
        if not normalized:
            raise NarrativeGenerationError("OpenAI response was empty")

        advisor_labels = ADVISOR_SECTION_LABELS[:-1]
        sections: list[NarrativeSection] = []

        for index, label in enumerate(advisor_labels):
            next_labels = advisor_labels[index + 1 :] + (ADVISOR_SECTION_LABEL_LIMITATIONS,)
            content = self._extract_section(
                normalized,
                label,
                next_labels=next_labels,
            )
            if not content:
                raise NarrativeGenerationError(
                    f"OpenAI response missing required section: {label.rstrip(':')}"
                )
            sections.append(
                NarrativeSection(
                    title=ADVISOR_SECTION_LABEL_TO_TITLE[label],
                    content=content,
                )
            )

        limitations = self._extract_section(
            normalized,
            ADVISOR_SECTION_LABEL_LIMITATIONS,
            next_labels=(),
        )

        if len(sections) != len(ADVISOR_SECTION_TITLES):
            raise NarrativeGenerationError("OpenAI response missing required advisor sections")

        return ParsedNarrativeSections(
            sections=tuple(sections),
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
