from dataclasses import dataclass

from src.domain.dtos.base_dto import BaseDTO


@dataclass(frozen=True)
class BibliographyNormsDTO(BaseDTO):
    """Editorial norms for detecting the bibliography header that closes the article body."""

    header_markers: tuple[str, ...]
    header_max_length: int
