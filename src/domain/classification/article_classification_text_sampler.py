from src.domain.dtos.classification_text_sampling_settings_dto import (
    ClassificationTextSamplingSettingsDTO,
)
from src.domain.dtos.document_content_dto import DocumentContentDTO


class ArticleClassificationTextSampler:
    """Builds a strategic text excerpt for LLM-based article-classification signals."""

    _BIBLIOGRAPHY_MARKERS = (
        "referencias",
        "bibliografía",
        "bibliography",
        "fuentes bibliográficas",
    )

    def __init__(
        self,
        classification_text_sampling_settings: ClassificationTextSamplingSettingsDTO,
    ) -> None:
        self._classification_text_sampling_settings = classification_text_sampling_settings

    def build_sample(self, document_content: DocumentContentDTO) -> str:
        """Return a strategic excerpt combining introduction and ending, skipping the bibliography."""
        full_text = " ".join(document_content.paragraphs)
        clean_text = self._strip_bibliography(document_content.paragraphs, full_text)

        introduction = clean_text[
            : self._classification_text_sampling_settings.introduction_character_limit
        ]
        ending = (
            clean_text[-self._classification_text_sampling_settings.conclusion_character_limit :]
            if len(clean_text)
            > self._classification_text_sampling_settings.introduction_character_limit
            else ""
        )
        sample = (introduction + " " + ending).strip()
        return (
            sample
            or full_text[: self._classification_text_sampling_settings.fallback_character_limit]
        )

    def _strip_bibliography(self, paragraphs: list[str], full_text: str) -> str:
        bibliography_position = len(full_text)
        character_position = 0
        for paragraph in paragraphs:
            paragraph_lower = paragraph.strip().lower()
            is_bibliography_header = len(
                paragraph_lower
            ) <= self._classification_text_sampling_settings.bibliography_header_max_length and any(
                marker in paragraph_lower for marker in self._BIBLIOGRAPHY_MARKERS
            )
            if is_bibliography_header:
                bibliography_position = character_position
                break
            character_position += len(paragraph) + 1

        return full_text[:bibliography_position] if bibliography_position > 0 else full_text
