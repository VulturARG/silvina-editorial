from dataclasses import dataclass

from src.domain.dtos.base_dto import BaseDTO


@dataclass(frozen=True)
class QualityTextSamplingSettingsDTO(BaseDTO):
    """Configuration limits for quality text sampling."""

    min_sample_word_count: int
    text_sample_character_limit: int
    reference_line_prefix_length: int
    introduction_paragraph_count: int
    middle_paragraph_count: int
    conclusion_paragraph_limit: int
    fallback_tail_paragraph_count: int
    conclusion_header_marker: str
