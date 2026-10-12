from dataclasses import dataclass

from src.domain.dtos.base_dto import BaseDTO


@dataclass(frozen=True)
class AbstractNormsDTO(BaseDTO):
    """Editorial norms for document abstract sections and length."""

    section_keywords: tuple[str, ...]
    min_word_count: int
    max_word_count: int
