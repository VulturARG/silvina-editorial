from dataclasses import dataclass

from src.domain.dtos.base_dto import BaseDTO


@dataclass(frozen=True)
class ClassificationTextSamplingSettingsDTO(BaseDTO):
    """Configuration limits for article classification text sampling."""

    introduction_character_limit: int
    conclusion_character_limit: int
    fallback_character_limit: int
    bibliography_header_max_length: int
