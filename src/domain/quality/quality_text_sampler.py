from src.domain.dtos.document_content_dto import DocumentContentDTO
from src.domain.dtos.quality_text_sampling_settings_dto import (
    QualityTextSamplingSettingsDTO,
)
from src.domain.enums.reference_line_marker import ReferenceLineMarker


class QualityTextSampler:
    """Builds a strategic text excerpt for LLM-based quality analysis."""

    def __init__(self, quality_text_sampling_settings: QualityTextSamplingSettingsDTO) -> None:
        self._quality_text_sampling_settings = quality_text_sampling_settings

    def build_sample(self, document_content: DocumentContentDTO) -> str:
        """Return a strategic excerpt of the document, or its full text if too short."""
        parts = [document_content.title or ""]
        parts.extend(
            document_content.paragraphs[
                : self._quality_text_sampling_settings.introduction_paragraph_count
            ]
        )
        middle_index = len(document_content.paragraphs) // 2
        parts.extend(
            document_content.paragraphs[
                middle_index : middle_index
                + self._quality_text_sampling_settings.middle_paragraph_count
            ]
        )
        parts.extend(self._collect_conclusion_or_tail_paragraphs(document_content.paragraphs))

        text_sample = self._join_to_paragraph_boundary(parts)
        if len(text_sample.split()) < self._quality_text_sampling_settings.min_sample_word_count:
            return self._join_to_paragraph_boundary(document_content.paragraphs)
        return text_sample

    def _join_to_paragraph_boundary(self, paragraphs: list[str]) -> str:
        """Join paragraphs, completing in full the one that first reaches the character limit."""
        included: list[str] = []
        for paragraph in paragraphs:
            included.append(paragraph)
            if (
                len(" ".join(included))
                >= self._quality_text_sampling_settings.text_sample_character_limit
            ):
                break
        return " ".join(included)

    def _collect_conclusion_or_tail_paragraphs(self, paragraphs: list[str]) -> list[str]:
        conclusion_paragraphs = []
        in_conclusion = False
        marker = self._quality_text_sampling_settings.conclusion_header_marker.lower()
        for paragraph in paragraphs:
            if marker in paragraph.lower():
                in_conclusion = True
            if in_conclusion and not self._is_reference_like(paragraph):
                conclusion_paragraphs.append(paragraph)

        if conclusion_paragraphs:
            return conclusion_paragraphs[
                : self._quality_text_sampling_settings.conclusion_paragraph_limit
            ]

        non_reference_paragraphs = [
            paragraph for paragraph in paragraphs if not self._is_reference_like(paragraph)
        ]
        return non_reference_paragraphs[
            -self._quality_text_sampling_settings.fallback_tail_paragraph_count :
        ]

    def _is_reference_like(self, paragraph: str) -> bool:
        prefix = paragraph[: self._quality_text_sampling_settings.reference_line_prefix_length]
        return any(marker.value in prefix for marker in ReferenceLineMarker)
