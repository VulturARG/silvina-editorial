from src.domain.dtos.document_content_dto import DocumentContentDTO
from src.domain.dtos.laya_text_sample_settings_dto import LayaTextSampleSettingsDTO
from src.domain.enums.reference_line_marker import ReferenceLineMarker


class LayaTextSampler:
    """Builds the Laya state excerpt with the legacy quality-analysis sampling strategy."""

    def __init__(self, text_sample_settings: LayaTextSampleSettingsDTO) -> None:
        self._text_sample_settings = text_sample_settings
        self._conclusion_header_marker = text_sample_settings.conclusion_header_marker.lower()

    def build_sample(self, document_content: DocumentContentDTO) -> str:
        """Return a strategic excerpt of the document, or its full text if too short."""
        parts = [document_content.title or ""]
        parts.extend(
            document_content.paragraphs[: self._text_sample_settings.introduction_paragraph_count]
        )
        middle_index = len(document_content.paragraphs) // 2
        parts.extend(
            document_content.paragraphs[
                middle_index : middle_index + self._text_sample_settings.middle_paragraph_count
            ]
        )
        parts.extend(self._collect_conclusion_or_tail_paragraphs(document_content.paragraphs))

        text_sample = self._join_to_paragraph_boundary(parts)
        if len(text_sample.split()) < self._text_sample_settings.min_sample_word_count:
            return self._join_to_paragraph_boundary(document_content.paragraphs)
        return text_sample

    def _join_to_paragraph_boundary(self, paragraphs: list[str]) -> str:
        included: list[str] = []
        for paragraph in paragraphs:
            included.append(paragraph)
            if len(" ".join(included)) >= self._text_sample_settings.text_sample_character_limit:
                break
        return " ".join(included)

    def _collect_conclusion_or_tail_paragraphs(self, paragraphs: list[str]) -> list[str]:
        conclusion_paragraphs = []
        in_conclusion = False
        for paragraph in paragraphs:
            if self._conclusion_header_marker in paragraph.lower():
                in_conclusion = True
            if in_conclusion and not self._is_reference_like(paragraph):
                conclusion_paragraphs.append(paragraph)

        if conclusion_paragraphs:
            return conclusion_paragraphs[: self._text_sample_settings.conclusion_paragraph_limit]

        non_reference_paragraphs = [
            paragraph for paragraph in paragraphs if not self._is_reference_like(paragraph)
        ]
        return non_reference_paragraphs[-self._text_sample_settings.fallback_tail_paragraph_count :]

    def _is_reference_like(self, paragraph: str) -> bool:
        prefix = paragraph[: self._text_sample_settings.reference_line_prefix_length]
        return any(marker.value in prefix for marker in ReferenceLineMarker)
