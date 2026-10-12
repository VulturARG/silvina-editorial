from dataclasses import dataclass

from src.domain.dtos.base_dto import BaseDTO


@dataclass(frozen=True)
class KeywordNormsDTO(BaseDTO):
    """Editorial norms for document keyword sections and counts."""

    section_markers: tuple[str, ...]
    min_count: int
    max_count: int
